#!/usr/bin/env python3
"""
jira-fetch-analyze.py — Análise completa de card Jira: funcionalidade + design.

Lê a transcrição do card (erros reportados, comportamentos incorretos, pontos levantados),
visita o código em TODOS os layers (frontend React/Replit, frontend Vue/GitHub, backend Python,
agentes IA, integrações) e gera um card estruturado com:
  - Issues de funcionalidade (incompleta, mal funcionando, erros)
  - Issues de design das funcionalidades mencionadas
  - Sugestões de código por layer (front, back, IA, integrações)
  - Action items e critérios de aceite

Script 1 de 2: Escopo COMPLETO (funcionalidade + design).
Script 2 (jira-audit-design.py): Escopo DESIGN ONLY, mais profundo e detalhado.

Uso:
    python3 scripts/jira-fetch-analyze.py WT-1234
    python3 scripts/jira-fetch-analyze.py WT-1234 --dry-run
    python3 scripts/jira-fetch-analyze.py WT-1234 --react-file plataforma-lia/src/components/sidebar.tsx
    python3 scripts/jira-fetch-analyze.py WT-1234 --vue-file components/ui/menu/sidebar.vue
    python3 scripts/jira-fetch-analyze.py WT-1234 --backend-file lia-agent-system/app/api/v1/jobs.py
"""

import os
import sys
import json
import re
import base64
import requests
import argparse
from datetime import date

CLOUD_ID = "8cf762f8-6a44-47de-8915-6b3dc0cd2715"
BASE_URL = f"https://api.atlassian.com/ex/jira/{CLOUD_ID}/rest/api/3"
WORKSPACE_ROOT = "/home/runner/workspace"
GITHUB_ORG = "WeDOTalent"
GITHUB_VUE_REPO = "wedo-nuxt"
GITHUB_BRANCH = "main"

# Layers a pesquisar no Replit
SEARCH_LAYERS = {
    "frontend_react": {
        "dirs": ["plataforma-lia/src"],
        "extensions": (".tsx", ".ts", ".css"),
        "label": "Frontend React (Replit)",
    },
    "backend": {
        "dirs": ["lia-agent-system/app/api", "lia-agent-system/app/domains", "lia-agent-system/app/services"],
        "extensions": (".py",),
        "label": "Backend Python",
    },
    "ai_agents": {
        "dirs": ["lia-agent-system/app/domains"],
        "extensions": (".py",),
        "label": "Agentes IA",
    },
    "integrations": {
        "dirs": ["plataforma-lia/src/lib", "plataforma-lia/src/app/api", "lia-agent-system/app/integrations"],
        "extensions": (".ts", ".py"),
        "label": "Integrações",
    },
}


# ── Jira Auth ───────────────────────────────────────────────────────────────

def get_jira_token():
    hostname = os.environ.get("REPLIT_CONNECTORS_HOSTNAME")
    repl_identity = os.environ.get("REPL_IDENTITY")
    web_repl_renewal = os.environ.get("WEB_REPL_RENEWAL")

    if repl_identity:
        x_token = f"repl {repl_identity}"
    elif web_repl_renewal:
        x_token = f"depl {web_repl_renewal}"
    else:
        raise ValueError("Token Replit não encontrado (REPL_IDENTITY / WEB_REPL_RENEWAL)")

    resp = requests.get(
        f"https://{hostname}/api/v2/connection?include_secrets=true&connector_names=jira",
        headers={"Accept": "application/json", "X_REPLIT_TOKEN": x_token},
    )
    settings = resp.json()["items"][0]["settings"]
    token = settings.get("access_token") or settings.get("oauth", {}).get("credentials", {}).get("access_token")
    if not token:
        raise ValueError("access_token Jira não encontrado")
    return token


def fetch_card(token, issue_key):
    url = f"{BASE_URL}/issue/{issue_key}?fields=summary,description,status,labels"
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
    if resp.status_code != 200:
        raise ValueError(f"Erro ao buscar {issue_key}: {resp.status_code} {resp.text[:300]}")
    return resp.json()


def update_card(token, issue_key, adf_description):
    url = f"{BASE_URL}/issue/{issue_key}"
    resp = requests.put(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"},
        json={"fields": {"description": adf_description}},
    )
    return resp.status_code, resp.text


# ── Text helpers ─────────────────────────────────────────────────────────────

def adf_to_text(node):
    if not node:
        return ""
    if isinstance(node, str):
        return node
    text = ""
    if node.get("type") == "text":
        text += node.get("text", "")
    for child in node.get("content", []):
        text += adf_to_text(child)
    if node.get("type") in ("paragraph", "heading", "listItem"):
        text += "\n"
    return text


def extract_keywords(text, max_kw=10):
    stopwords = {
        "that", "this", "with", "from", "have", "para", "como", "deve", "pelo", "pela",
        "está", "menu", "logo", "card", "jira", "side", "left", "right", "when", "only",
        "mais", "item", "list", "show", "hide", "view", "open", "issue", "only", "appears",
        "button", "pass", "mouse", "also", "common", "which", "there", "missing", "parts",
        "look", "product", "correct", "these", "relation", "dynamic", "expansion", "incorrect",
        "correction", "corrections", "error", "errors", "click", "hover", "tela", "arquivo",
        "codigo", "code", "file", "func", "page", "route", "data", "user", "type", "name",
    }
    words = re.findall(r"\b[a-z][a-z0-9]{3,}\b", text.lower())
    return list(dict.fromkeys([w for w in words if w not in stopwords]))[:max_kw]


def extract_file_mentions(text):
    paths = set()
    for match in re.finditer(
        r"(?:plataforma-lia/|src/|app/|components/|hooks/|pages/|lia-agent-system/)[\w./\-]+\.(?:tsx|ts|css|py|vue)",
        text
    ):
        paths.add(match.group(0))
    return list(paths)


def extract_vue_mentions(text):
    return list(set(re.findall(r"[\w./\-]+\.vue", text)))


# ── Local file reading ────────────────────────────────────────────────────────

def read_local_file(rel_path, max_lines=250):
    full_path = os.path.join(WORKSPACE_ROOT, rel_path)
    if not os.path.exists(full_path):
        return None, f"Não encontrado: {rel_path}"
    try:
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        content = "".join(lines[:max_lines])
        if len(lines) > max_lines:
            content += f"\n... [{len(lines) - max_lines} linhas omitidas]"
        return content, None
    except Exception as e:
        return None, str(e)


def find_files_in_layer(layer_key, keywords, max_files=3):
    """Busca arquivos por keywords em um layer específico."""
    layer = SEARCH_LAYERS.get(layer_key, {})
    dirs = layer.get("dirs", [])
    exts = layer.get("extensions", ())
    found = []

    for rel_dir in dirs:
        full_dir = os.path.join(WORKSPACE_ROOT, rel_dir)
        if not os.path.exists(full_dir):
            continue
        for root, subdirs, files in os.walk(full_dir):
            subdirs[:] = [d for d in subdirs if d not in ("node_modules", ".next", "__pycache__", ".git")]
            for fname in files:
                if not fname.endswith(exts):
                    continue
                fname_lower = fname.lower()
                for kw in keywords:
                    if kw.lower() in fname_lower:
                        full_path = os.path.join(root, fname)
                        rel = os.path.relpath(full_path, WORKSPACE_ROOT)
                        if rel not in found:
                            found.append(rel)
                        break
            if len(found) >= max_files:
                break
        if len(found) >= max_files:
            break

    return found[:max_files]


# ── GitHub ────────────────────────────────────────────────────────────────────

def fetch_github_file(file_path, repo=None, branch=GITHUB_BRANCH):
    token = os.environ.get("GITHUB_PAT_WEDOTALENT")
    if not token:
        return None, "GITHUB_PAT_WEDOTALENT não configurado"
    if not repo:
        repo = f"{GITHUB_ORG}/{GITHUB_VUE_REPO}"
    url = f"https://api.github.com/repos/{repo}/contents/{file_path}?ref={branch}"
    resp = requests.get(url, headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    })
    if resp.status_code == 404:
        return None, f"Não encontrado no GitHub: {file_path}"
    if resp.status_code != 200:
        return None, f"GitHub {resp.status_code}: {resp.text[:200]}"
    content = base64.b64decode(resp.json().get("content", "")).decode("utf-8", errors="replace")
    return content, None


def search_github_file(query, repo=None):
    token = os.environ.get("GITHUB_PAT_WEDOTALENT")
    if not token:
        return []
    if not repo:
        repo = f"{GITHUB_ORG}/{GITHUB_VUE_REPO}"
    url = f"https://api.github.com/search/code?q={query}+repo:{repo}&per_page=5"
    resp = requests.get(url, headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    })
    if resp.status_code != 200:
        return []
    return [item["path"] for item in resp.json().get("items", [])]


# ── Claude Analysis ───────────────────────────────────────────────────────────

DS_LIA_DESIGN_RULES = """
## DS LIA v4.2.1 — Regras de Design (React = Fonte da Verdade)

### Paleta (Regra 90/10)
- 90% monocromático: gray-900 primary, gray-100 backgrounds, gray-400 textos secundários
- 10% acento: #60BED1 (wedo-cyan) — APENAS ícone brain LIA, badges LIA, links hover
- Cyan NUNCA em botões de ação primária, backgrounds de seção ou textos de corpo

### Tipografia
- Open Sans 85%: corpo, labels, navegação, dados
- Inter 10%: dados numéricos, métricas, tabelas
- JetBrains Mono 5%: código, IDs técnicos
- Menu items: 13px, line-height 1.25

### Bordas e Formas
- Border radius SEMPRE 8px (rounded-md / rounded-lg)
- NUNCA rounded-12px, rounded-full em botões de ação, ou valores custom
- Inputs: rounded-xl (12px) — única exceção aprovada

### Ícones
- Tamanho padrão: SEMPRE 16px (w-4 h-4)
- Lucide icons como padrão
- NUNCA 14px, 18px, 24px (default Vuetify) sem override

### Botões
- Primary: bg-gray-900 text-white, variant="flat" no Vuetify
- Secondary: border border-gray-200, variant="outlined"
- NUNCA variant="elevated" (sombra indevida)
- Altura: 40px ação principal, 32px secundário

### Sidebar/Menu
- Largura expandido: 240px — NUNCA 256px (default Vuetify)
- Largura colapsado: 64px
- Comportamento: SEMPRE permanent — NUNCA expand-on-hover
- Toggle: botão chevron explícito, não hover automático
- Estado ativo: bg-gray-100 (light) / bg-gray-800 (dark) + font-semibold
- Itens: min-height 40px

### Cards e Superfícies
- elevation="0" (flat) — NUNCA elevation padrão Vuetify (sombra)
- Borda: border border-gray-200 (light) / border-gray-700 (dark)

### Defaults Vuetify a Corrigir (vuetify.ts)
- VIcon: { size: '16' }
- VBtn: { variant: 'flat', size: 'small' }
- VCard: { elevation: 0 }
- VTextField: { density: 'compact', variant: 'outlined' }
- VNavigationDrawer: { width: 240 }
"""


def analyze_with_claude(card_key, summary, description_text, code_by_layer, vue_files):
    try:
        import anthropic
        client = anthropic.Anthropic()
    except Exception as e:
        raise ValueError(f"Erro ao inicializar Anthropic: {e}")

    code_sections = ""
    for layer_label, files in code_by_layer.items():
        for path, content in files.items():
            code_sections += f"\n{'='*60}\n[{layer_label}] {path}\n{'='*60}\n{content}\n"

    vue_section = ""
    for path, content in vue_files.items():
        vue_section += f"\n{'='*60}\n[Vue/GitHub] {path}\n{'='*60}\n{content}\n"

    prompt = f"""Você é um engenheiro senior full-stack + design system expert da Plataforma LIA (WeDOTalent).

Analise o card Jira abaixo. Mapeie TODOS os pontos levantados na transcrição:
funcionalidades incompletas, erros, comportamentos incorretos, problemas de design,
UX ruim, integrações quebradas, lógica de IA incorreta, problemas visuais, etc.
Não deixe NENHUM ponto da transcrição de fora.

## CARD JIRA
Chave: {card_key}
Título: {summary}
Data: {date.today().strftime('%d/%m/%Y')}

## TRANSCRIÇÃO / DESCRIÇÃO DO CARD (fonte primária — extraia TUDO):
{description_text}

## CÓDIGO DOS LAYERS (React Replit + Backend Python + IA + Integrações):
{code_sections if code_sections else "(arquivos não encontrados automaticamente — analise pela transcrição)"}

## CÓDIGO VUE (GitHub WeDOTalent — a ser auditado):
{vue_section if vue_section else "(não fornecido — gere código Vue correto baseado nas regras DS LIA)"}

## REGRAS DS LIA v4.2.1:
{DS_LIA_DESIGN_RULES}

## INSTRUÇÕES
Gere um JSON com a estrutura EXATA abaixo. Seja específico e concreto — nunca genérico.
Código ANTES/DEPOIS deve ser real, extraído do código fornecido. Nunca use placeholders.

{{
  "titulo_auditoria": "Título descritivo do que foi analisado",
  "resumo": "2-3 parágrafos descrevendo o problema, o que foi analisado e o que precisa ser feito",
  "betterbugs_link": "URL do BetterBugs se encontrada na transcrição, senão null",
  "arquivos_de_referencia": [
    {{"path": "caminho/real/do/arquivo", "layer": "Frontend React|Backend|Agente IA|Integração|Vue|Banco de Dados", "descricao": "O que este arquivo faz"}}
  ],
  "issues_funcionalidade": [
    {{
      "numero": "F01",
      "titulo": "Título do problema funcional",
      "tipo": "bug|incompleto|ux|integracao|ia|banco",
      "descricao": "O que está errado e por quê — detalhado e específico",
      "layers_afetados": ["Frontend React", "Vue", "Backend Python", "Agente IA", "Integração", "Banco de Dados"],
      "blocos_de_codigo": [
        {{
          "layer": "Backend Python",
          "arquivo": "lia-agent-system/app/domains/screening/service.py",
          "linguagem": "python",
          "antes_label": "Código atual — INCORRETO",
          "antes": "trecho python atual com o bug",
          "depois_label": "deve ficar assim",
          "depois": "trecho python corrigido"
        }},
        {{
          "layer": "Agente IA",
          "arquivo": "lia-agent-system/app/domains/cv_screening/agents/wsi_graph.py",
          "linguagem": "python",
          "antes_label": "Lógica de IA atual — INCORRETA",
          "antes": "trecho do agente com o problema",
          "depois_label": "lógica corrigida",
          "depois": "trecho corrigido do agente"
        }},
        {{
          "layer": "Banco de Dados",
          "arquivo": "migrations/schema.sql ou model",
          "linguagem": "sql",
          "antes_label": "Schema/query atual",
          "antes": "CREATE TABLE ou SELECT atual",
          "depois_label": "schema/query corrigido",
          "depois": "CREATE TABLE ou SELECT corrigido"
        }},
        {{
          "layer": "Integração",
          "arquivo": "plataforma-lia/src/lib/api/jobs.ts",
          "linguagem": "typescript",
          "antes_label": "Chamada de API atual — INCORRETA",
          "antes": "fetch ou axios atual com o problema",
          "depois_label": "chamada corrigida",
          "depois": "fetch ou axios corrigido"
        }},
        {{
          "layer": "Frontend React",
          "arquivo": "plataforma-lia/src/components/jobs/job-card.tsx",
          "linguagem": "tsx",
          "antes_label": "React atual — INCORRETO",
          "antes": "trecho tsx atual",
          "depois_label": "React corrigido",
          "depois": "trecho tsx corrigido"
        }},
        {{
          "layer": "Vue",
          "arquivo": "components/jobs/job-card.vue",
          "linguagem": "vue",
          "antes_label": "Vue atual — INCORRETO",
          "antes": "trecho vue atual com o problema equivalente",
          "depois_label": "Vue corrigido",
          "depois": "trecho vue corrigido conforme DS LIA"
        }}
      ]
    }}
  ],
  "issues_design": [
    {{
      "numero": "D01",
      "titulo": "Título do problema de design",
      "descricao": "O que está visualmente errado — referência à regra DS LIA violada",
      "arquivo_react": "caminho/do/arquivo.tsx",
      "arquivo_vue": "components/caminho/do/arquivo.vue",
      "antes_label": "Vue atual — INCORRETO",
      "antes_codigo": "código vue atual com o problema",
      "depois_label": "deve ficar assim — React/DS LIA",
      "depois_codigo": "código vue corrigido",
      "linguagem": "vue",
      "warning": "⚠️ Impacto visual deste bug"
    }}
  ],
  "vuetify_defaults": [
    {{
      "componente": "v-icon",
      "titulo": "v-icon — size ausente",
      "default_vuetify": "24px (Material Design default)",
      "react_correto": "w-4 h-4 = 16px",
      "impacto": "Impacto visual concreto",
      "fix_local": "<v-icon size=\\"16\\">mdi-*</v-icon>",
      "fix_global": "VIcon: {{ size: '16' }}"
    }}
  ],
  "vuetify_ts_code": "createVuetify({{\\n  defaults: {{\\n    VIcon: {{ size: '16' }},\\n  }}\\n}})",
  "action_items": [
    "[ ] [Layer] Ação concreta e verificável"
  ],
  "criterios_de_aceite": [
    "[Área] Critério verificável e concreto"
  ],
  "arquivos_para_modificar": [
    {{"path": "caminho/arquivo", "layer": "Frontend React|Vue|Backend|Agente IA|Integração|Banco de Dados", "motivo": "Por que precisa ser modificado"}}
  ]
}}

REGRAS OBRIGATÓRIAS:
- Extraia ABSOLUTAMENTE TODOS os elementos da transcrição — nenhum ponto pode ficar de fora
- issues_funcionalidade.blocos_de_codigo: inclua APENAS os layers REALMENTE afetados por aquela issue
  • Issue de backend: blocos Backend + (Integração se há chamada) + (Vue se afeta a exibição)
  • Issue de IA: blocos Agente IA + (Backend se há endpoint) + (Frontend React + Vue se afeta resultado exibido)
  • Issue de banco: blocos Banco de Dados + Backend que usa a query
  • Issue puramente de frontend: blocos Frontend React + Vue
  • NÃO crie blocos vazios ou genéricos — só o que foi realmente encontrado no código
- issues_design: SEMPRE com ANTES (Vue incorreto) e DEPOIS (Vue corrigido conforme DS LIA)
- vuetify_defaults: inclua TODOS os defaults Vuetify relevantes para esta tela
- vuetify_ts_code: bloco completo e pronto para colar no vuetify.ts
- Mínimo 3 issues_funcionalidade e 5 issues_design se mencionados na transcrição
- Mínimo 10 critérios de aceite
- Responda APENAS o JSON puro, sem markdown, sem explicação fora do JSON"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=10000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


# ── ADF Builder ───────────────────────────────────────────────────────────────

def build_adf(data, card_key, summary):
    nodes = []

    def h(level, text):
        return {"type": "heading", "attrs": {"level": level}, "content": [{"type": "text", "text": text}]}

    def p(text, bold=False):
        if bold:
            return {"type": "paragraph", "content": [{"type": "text", "text": text, "marks": [{"type": "strong"}]}]}
        return {"type": "paragraph", "content": [{"type": "text", "text": text}]}

    def p_mixed(*parts):
        content = []
        for text, bold, code in parts:
            node = {"type": "text", "text": text}
            marks = []
            if bold:
                marks.append({"type": "strong"})
            if code:
                marks.append({"type": "code"})
            if marks:
                node["marks"] = marks
            content.append(node)
        return {"type": "paragraph", "content": content}

    def blist(items):
        return {
            "type": "bulletList",
            "content": [
                {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": str(i)}]}]}
                for i in items
            ],
        }

    def code_block(code, lang=""):
        return {"type": "codeBlock", "attrs": {"language": lang}, "content": [{"type": "text", "text": str(code)}]}

    def rule():
        return {"type": "rule"}

    today = date.today().strftime("%d/%m/%Y")

    # ── Header ──
    nodes.append(h(1, data.get("titulo_auditoria", summary)))
    nodes.append(p(f"Card: {card_key}  |  Gerado em: {today}"))

    resumo = data.get("resumo", "")
    if resumo:
        for para in resumo.split("\n"):
            if para.strip():
                nodes.append(p(para.strip()))

    betterbugs = data.get("betterbugs_link")
    if betterbugs:
        nodes.append(p_mixed(("🐛 BetterBugs: ", True, False), (betterbugs, False, False)))

    nodes.append(rule())

    # ── Arquivos de Referência ──
    arquivos = data.get("arquivos_de_referencia", [])
    if arquivos:
        nodes.append(h(2, "📁 Arquivos de Referência"))
        items = []
        for a in arquivos:
            if isinstance(a, dict):
                layer = a.get("layer", "")
                prefix = f"[{layer}] " if layer else ""
                items.append(f"{prefix}{a.get('path', '')} — {a.get('descricao', '')}")
            else:
                items.append(str(a))
        nodes.append(blist(items))
        nodes.append(rule())

    # ── Issues de Funcionalidade ──
    issues_func = data.get("issues_funcionalidade", [])
    if issues_func:
        nodes.append(h(2, "⚙️ Issues de Funcionalidade"))
        nodes.append(p(
            "Problemas funcionais identificados na transcrição: erros, comportamentos incorretos, "
            "features incompletas, integrações, lógica de IA e banco de dados. "
            "Cada issue detalha TODOS os layers afetados (Backend Python 🐍, Agente IA 🤖, "
            "Integração 🔌, Banco de Dados 🗄️, Frontend React ⚛️, Vue 🟢) "
            "com código ANTES/DEPOIS específico por layer."
        ))

        # Layer badges for the heading
        LAYER_EMOJI = {
            "backend python": "🐍",
            "backend": "🐍",
            "agente ia": "🤖",
            "ia": "🤖",
            "integração": "🔌",
            "integracao": "🔌",
            "banco de dados": "🗄️",
            "banco": "🗄️",
            "frontend react": "⚛️",
            "react": "⚛️",
            "vue": "🟢",
        }

        for issue in issues_func:
            num = issue.get("numero", "F?")
            titulo = issue.get("titulo", "")
            tipo = issue.get("tipo", "")
            descricao = issue.get("descricao", "")
            layers = issue.get("layers_afetados", [issue.get("layer", "")])
            blocos = issue.get("blocos_de_codigo", [])

            # Fallback: se vier no formato antigo (sem blocos_de_codigo)
            if not blocos:
                arq_react = issue.get("arquivo_react", issue.get("arquivo", ""))
                arq_vue = issue.get("arquivo_vue", "")
                if issue.get("codigo_atual_react") or issue.get("codigo_atual"):
                    blocos.append({
                        "layer": "Frontend React",
                        "arquivo": arq_react,
                        "linguagem": issue.get("linguagem_react", "tsx"),
                        "antes_label": "React atual — INCORRETO",
                        "antes": issue.get("codigo_atual_react", issue.get("codigo_atual", "")),
                        "depois_label": "React corrigido",
                        "depois": issue.get("codigo_sugerido_react", issue.get("codigo_sugerido", "")),
                    })
                if issue.get("codigo_atual_vue"):
                    blocos.append({
                        "layer": "Vue",
                        "arquivo": arq_vue,
                        "linguagem": "vue",
                        "antes_label": "Vue — ANTES (incorreto)",
                        "antes": issue.get("codigo_atual_vue", ""),
                        "depois_label": "Vue — DEPOIS (corrigido)",
                        "depois": issue.get("codigo_sugerido_vue", ""),
                    })

            tipo_badge = f" [{tipo.upper()}]" if tipo else ""
            layers_str = ", ".join(layers) if isinstance(layers, list) else str(layers)
            nodes.append(h(3, f"Issue {num} — {titulo}{tipo_badge}"))

            if layers_str:
                nodes.append(p_mixed(
                    ("Layers afetados: ", False, False),
                    (layers_str, True, False),
                ))

            if descricao:
                nodes.append(p(descricao))

            # Renderiza cada bloco de código por layer
            for bloco in blocos:
                bloco_layer = bloco.get("layer", "")
                bloco_arquivo = bloco.get("arquivo", "")
                bloco_lang = bloco.get("linguagem", "")
                bloco_antes_label = bloco.get("antes_label", "Código atual — INCORRETO")
                bloco_antes = bloco.get("antes", "")
                bloco_depois_label = bloco.get("depois_label", "deve ficar assim")
                bloco_depois = bloco.get("depois", "")

                emoji = LAYER_EMOJI.get(bloco_layer.lower(), "")
                layer_title = f"{emoji} {bloco_layer}".strip()

                nodes.append(h(4, layer_title))
                if bloco_arquivo:
                    nodes.append(p_mixed(
                        ("Arquivo: ", False, False),
                        (bloco_arquivo, False, True),
                    ))

                if bloco_antes and bloco_antes.strip():
                    nodes.append(p(f"{bloco_antes_label}:", bold=True))
                    nodes.append(code_block(bloco_antes, bloco_lang))

                if bloco_depois and bloco_depois.strip():
                    nodes.append(p(f"{bloco_depois_label}:", bold=True))
                    nodes.append(code_block(bloco_depois, bloco_lang))

            nodes.append(rule())

    # ── Issues de Design ──
    issues_design = data.get("issues_design", [])
    if issues_design:
        nodes.append(h(2, "🎨 Issues de Design (DS LIA v4.2.1)"))
        nodes.append(p(
            "Problemas visuais identificados nos elementos mencionados na transcrição. "
            "Cada issue mapeia ANTES (Vue atual incorreto) → DEPOIS (Vue corrigido conforme DS LIA). "
            "React/Replit = fonte da verdade absoluta. "
            "Para auditoria de design ainda mais aprofundada, usar jira-audit-design.py."
        ))

        for issue in issues_design:
            num = issue.get("numero", "D?")
            titulo = issue.get("titulo", "")
            descricao = issue.get("descricao", "")
            arq_react = issue.get("arquivo_react", "")
            arq_vue = issue.get("arquivo_vue", issue.get("arquivo", ""))
            antes_label = issue.get("antes_label", "Vue atual — INCORRETO")
            antes_cod = issue.get("antes_codigo", issue.get("codigo_atual", ""))
            depois_label = issue.get("depois_label", "deve ficar assim — React/DS LIA")
            depois_cod = issue.get("depois_codigo", issue.get("codigo_sugerido", ""))
            lang = issue.get("linguagem", "vue")
            warning = issue.get("warning", "")

            nodes.append(h(3, f"Issue {num} — {titulo}"))
            if descricao:
                nodes.append(p(descricao))
            if arq_react:
                nodes.append(p_mixed(("Ref React: ", False, False), (arq_react, False, True)))
            if arq_vue:
                nodes.append(p_mixed(("Arquivo Vue: ", False, False), (arq_vue, False, True)))

            if antes_cod and antes_cod.strip():
                nodes.append(p(f"{antes_label}:", bold=True))
                nodes.append(code_block(antes_cod, lang))
            if depois_cod and depois_cod.strip():
                nodes.append(p(f"{depois_label}:", bold=True))
                nodes.append(code_block(depois_cod, lang))
            if warning:
                nodes.append(p(warning))

            nodes.append(rule())

    # ── Vuetify Defaults ──
    vuetify_defaults = data.get("vuetify_defaults", [])
    vuetify_ts = data.get("vuetify_ts_code", "")
    if vuetify_defaults or vuetify_ts:
        nodes.append(h(2, "⚠️ ALERTA VUETIFY DEFAULTS — Para dev / ClaudeCode / Cursor"))
        nodes.append(p(
            "Causa raiz sistêmica: os problemas abaixo não são erros isolados — são causados por "
            "defaults implícitos do Vuetify que divergem do DS LIA (React/Replit = fonte da verdade). "
            "Corrija localmente E atualize o vuetify.ts (global defaults) para evitar reincidência."
        ))

        for d in vuetify_defaults:
            titulo_d = d.get("titulo", d.get("componente", ""))
            nodes.append(h(3, titulo_d))
            items_d = []
            if d.get("default_vuetify"):
                items_d.append(f"Vuetify default implícito: {d['default_vuetify']}")
            if d.get("react_correto"):
                items_d.append(f"React/Replit (correto): {d['react_correto']}")
            if d.get("impacto"):
                items_d.append(f"Impacto visual: {d['impacto']}")
            if d.get("fix_local"):
                items_d.append(f"Fix local: {d['fix_local']}")
            if d.get("fix_global"):
                items_d.append(f"Fix global (vuetify.ts): {d['fix_global']}")
            if items_d:
                nodes.append(blist(items_d))

        if vuetify_ts:
            nodes.append(h(3, "Como atualizar o vuetify.ts"))
            nodes.append(code_block(vuetify_ts, "typescript"))

        nodes.append(rule())

    # ── Arquivos a modificar ──
    mod_files = data.get("arquivos_para_modificar", [])
    if mod_files:
        nodes.append(h(2, "🗂️ Arquivos a Modificar"))
        items_mod = []
        for f in mod_files:
            if isinstance(f, dict):
                layer = f.get("layer", "")
                prefix = f"[{layer}] " if layer else ""
                items_mod.append(f"{prefix}{f.get('path', '')} — {f.get('motivo', '')}")
            else:
                items_mod.append(str(f))
        nodes.append(blist(items_mod))
        nodes.append(rule())

    # ── Action Items ──
    action_items = data.get("action_items", [])
    if action_items:
        nodes.append(h(2, "📋 Action Items"))
        nodes.append(blist(action_items))
        nodes.append(rule())

    # ── Critérios de Aceite ──
    criterios = data.get("criterios_de_aceite", [])
    if criterios:
        nodes.append(h(2, "✅ Critérios de Aceite"))
        nodes.append(blist(criterios))

    nodes.append(rule())
    nodes.append(p(
        "Referência: React/Replit é sempre a fonte da verdade de design e funcionalidade. "
        "Para auditoria de design exclusiva e mais completa, usar jira-audit-design.py."
    ))

    return {"version": 1, "type": "doc", "content": nodes}


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Análise completa de card Jira (funcionalidade + design)")
    parser.add_argument("issue_key", help="Chave do card (ex: WT-1637)")
    parser.add_argument("--dry-run", action="store_true", help="Mostra resultado sem atualizar o Jira")
    parser.add_argument("--react-file", action="append", default=[], metavar="PATH",
                        help="Arquivo React específico (path relativo ao workspace)")
    parser.add_argument("--vue-file", action="append", default=[], metavar="PATH",
                        help="Arquivo Vue no GitHub (ex: components/ui/menu/sidebar.vue)")
    parser.add_argument("--backend-file", action="append", default=[], metavar="PATH",
                        help="Arquivo backend Python específico")
    args = parser.parse_args()

    issue_key = args.issue_key.upper()

    print("=" * 70)
    print(f"JIRA FETCH ANALYZE — {issue_key}")
    print("Escopo: Funcionalidade + Design (todos os layers)")
    print("=" * 70)

    print("\n[1/6] Buscando credenciais Jira...")
    token = get_jira_token()
    print("✓ Token obtido")

    print(f"\n[2/6] Buscando card {issue_key}...")
    card = fetch_card(token, issue_key)
    summary = card["fields"].get("summary", "")
    description_text = adf_to_text(card["fields"].get("description") or {}).strip()
    print(f"✓ Card: {summary}")
    print(f"  Transcrição: {len(description_text)} caracteres")

    mentioned_files = extract_file_mentions(description_text)
    mentioned_vue = extract_vue_mentions(description_text)
    keywords = extract_keywords(summary + " " + description_text)
    print(f"  Keywords: {', '.join(keywords[:6])}")

    print(f"\n[3/6] Coletando código React (Replit frontend)...")
    react_files = {}
    for rf in args.react_file:
        content, err = read_local_file(rf)
        if content:
            react_files[rf] = content
            print(f"  ✓ {rf}")
        else:
            print(f"  ✗ {rf}: {err}")

    if not react_files:
        for rf in [f for f in mentioned_files if f.endswith((".tsx", ".ts"))]:
            content, err = read_local_file(rf)
            if content:
                react_files[rf] = content
                print(f"  ✓ {rf} (mencionado no card)")

    if not react_files:
        for rf in find_files_in_layer("frontend_react", keywords, max_files=3):
            content, err = read_local_file(rf)
            if content:
                react_files[rf] = content
                print(f"  ✓ {rf} (auto-detectado)")

    print(f"  Total React: {len(react_files)} arquivo(s)")

    print(f"\n[4/6] Coletando código Backend + IA + Integrações (Replit)...")
    backend_files = {}
    ai_files = {}
    integration_files = {}

    for bf in args.backend_file:
        content, err = read_local_file(bf)
        if content:
            backend_files[bf] = content
            print(f"  ✓ [backend] {bf}")

    if not backend_files:
        for bf in [f for f in mentioned_files if f.endswith(".py")]:
            content, err = read_local_file(bf)
            if content:
                backend_files[bf] = content
                print(f"  ✓ [backend] {bf} (mencionado)")

    if not backend_files:
        for bf in find_files_in_layer("backend", keywords, max_files=2):
            content, err = read_local_file(bf)
            if content:
                backend_files[bf] = content
                print(f"  ✓ [backend] {bf} (auto)")

    for af in find_files_in_layer("ai_agents", keywords, max_files=2):
        if af not in backend_files:
            content, err = read_local_file(af)
            if content:
                ai_files[af] = content
                print(f"  ✓ [IA] {af} (auto)")

    for inf in find_files_in_layer("integrations", keywords, max_files=2):
        if inf not in backend_files and inf not in react_files:
            content, err = read_local_file(inf)
            if content:
                integration_files[inf] = content
                print(f"  ✓ [integração] {inf} (auto)")

    total_local = len(react_files) + len(backend_files) + len(ai_files) + len(integration_files)
    print(f"  Total local: {total_local} arquivo(s)")

    print(f"\n[5/6] Coletando código Vue (GitHub WeDOTalent/{GITHUB_VUE_REPO})...")
    vue_files = {}

    specific_vue = list(args.vue_file) or mentioned_vue[:2]
    for vf in specific_vue:
        content, err = fetch_github_file(vf)
        if content:
            vue_files[vf] = content
            print(f"  ✓ {vf} ({len(content)} chars)")
        else:
            print(f"  ✗ {vf}: {err}")

    if not vue_files:
        for kw in keywords[:3]:
            for path in search_github_file(kw):
                if path.endswith(".vue") and path not in vue_files:
                    content, err = fetch_github_file(path)
                    if content:
                        vue_files[path] = content
                        print(f"  ✓ {path} (auto)")
                    break
            if vue_files:
                break

    print(f"  Total Vue: {len(vue_files)} arquivo(s)")

    code_by_layer = {}
    if react_files:
        code_by_layer["Frontend React"] = react_files
    if backend_files:
        code_by_layer["Backend Python"] = backend_files
    if ai_files:
        code_by_layer["Agentes IA"] = ai_files
    if integration_files:
        code_by_layer["Integrações"] = integration_files

    print(f"\n[6/6] Analisando com Claude (funcionalidade + design)...")
    analysis = analyze_with_claude(issue_key, summary, description_text, code_by_layer, vue_files)
    print(f"✓ Análise gerada")
    print(f"  {len(analysis.get('issues_funcionalidade', []))} issues de funcionalidade")
    print(f"  {len(analysis.get('issues_design', []))} issues de design")
    print(f"  {len(analysis.get('criterios_de_aceite', []))} critérios de aceite")

    adf = build_adf(analysis, issue_key, summary)

    if args.dry_run:
        print("\n[DRY RUN] Preview (não enviado ao Jira):")
        print(json.dumps(analysis, indent=2, ensure_ascii=False)[:3000])
        print(f"\n✅ DRY RUN concluído. Remova --dry-run para publicar.")
        return

    print(f"\nPublicando no Jira...")
    status_code, text = update_card(token, issue_key, adf)
    if status_code in (200, 204):
        print(f"\n✅ Card {issue_key} atualizado com sucesso!")
        print(f"   URL: https://wedotalent.atlassian.net/browse/{issue_key}")
    else:
        print(f"\n❌ Erro {status_code}: {text[:400]}")


if __name__ == "__main__":
    main()
