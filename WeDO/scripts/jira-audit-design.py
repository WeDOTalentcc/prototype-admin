#!/usr/bin/env python3
"""
jira-audit-design.py — Audita design de card Jira contra DS LIA v4.2.1.

Lê a transcrição do card, mapeia todos os elementos de design mencionados
(botões, bordas, ícones, tipografia, espaçamento, comportamento visual),
visita o código React (Replit) e Vue (GitHub WeDOTalent), e gera issues
numeradas com ANTES/DEPOIS concretos + seção de Vuetify defaults.

Uso:
    python3 scripts/jira-audit-design.py WT-1637
    python3 scripts/jira-audit-design.py WT-1637 --dry-run
    python3 scripts/jira-audit-design.py WT-1637 --vue-file components/ui/menu/sidebar.vue
    python3 scripts/jira-audit-design.py WT-1637 --react-file plataforma-lia/src/components/ui/sidebar.tsx

Fluxo:
    1. Busca card no Jira (transcrição + lista de pontos + BetterBugs link)
    2. Extrai todos os elementos de design da transcrição
    3. Lê código React no Replit (fonte da verdade)
    4. Lê código Vue no GitHub (WeDOTalent/wedo-nuxt) — o que será auditado
    5. Claude audita Vue vs React e gera issues numeradas com ANTES/DEPOIS
    6. Atualiza card com relatório de auditoria completo em ADF
"""

import os
import sys
import json
import re
import base64
import requests
import argparse
from pathlib import Path

CLOUD_ID = "8cf762f8-6a44-47de-8915-6b3dc0cd2715"
BASE_URL = f"https://api.atlassian.com/ex/jira/{CLOUD_ID}/rest/api/3"
WORKSPACE_ROOT = "/home/runner/workspace"
GITHUB_ORG = "WeDOTalent"
GITHUB_VUE_REPO = "wedo-nuxt"
GITHUB_BRANCH = "main"

DS_LIA_RULES = """
# Design System LIA v4.2.1 — Regras Canônicas (React = Fonte da Verdade)

## Paleta (Regra 90/10)
- 90% monocromático: gray-900 para primary, gray-100 para backgrounds, gray-400 para textos secundários
- 10% acento: #60BED1 (wedo-cyan) — APENAS para elementos LIA (ícone brain, badges LIA, links hover)
- Cyan NUNCA em botões de ação primária, backgrounds de seção ou textos de corpo

## Tipografia
- Open Sans 85%: texto de corpo, labels, navegação, dados
- Inter 10%: dados numéricos, métricas, tabelas
- JetBrains Mono 5%: código, IDs técnicos
- Tamanho menu items: 13px, line-height 1.25
- Nenhum outro font-family permitido (Source Serif 4 apenas em branding excepcionalmente)

## Bordas e Formas
- Border radius SEMPRE 8px (rounded-md / rounded-lg do Vuetify)
- NUNCA rounded-12px, rounded-full em botões de ação, ou valores custom
- Inputs: rounded-xl (12px) — exceção aprovada apenas para inputs

## Ícones
- Tamanho padrão: SEMPRE 16px (w-4 h-4)
- Lucide icons como padrão
- NUNCA 14px, 18px, 24px (default Vuetify) sem override explícito

## Botões
- Primary: bg-gray-900 text-white, variant="flat" no Vuetify
- Secondary/outline: border border-gray-200, variant="outlined"
- NUNCA variant="elevated" (sombra indevida)
- Tamanho: height 40px para ação principal, 32px para ações secundárias

## Sidebar/Menu
- Largura expandido: 240px (w-60) — NUNCA 256px (default Vuetify)
- Largura colapsado: 64px (rail-width)
- Comportamento: SEMPRE permanente (permanent) — NUNCA expand-on-hover
- Toggle: botão chevron explícito, não hover automático
- Estado ativo: bg-gray-100 (light) / bg-gray-800 (dark) + font-semibold
- Logo: controlado por isRail (não por hover/isHovered)
- Altura mínima itens: 40px

## Cards e Superfícies
- elevation="0" (flat) — NUNCA elevation padrão Vuetify (sombra)
- Borda: border border-gray-200 (light) / border-gray-700 (dark)

## Dark Mode
- Backgrounds: gray-900 para página, gray-800 para cards/surface, gray-700 para inputs
- Textos: gray-50 para primário, gray-400 para secundário

## Defaults Vuetify a Corrigir (vuetify.ts)
- VIcon: { size: '16' } — default é 24px
- VBtn: { variant: 'flat', size: 'small' } — default é elevated
- VCard: { elevation: 0 } — default tem sombra
- VTextField: { density: 'compact', variant: 'outlined' }
- VNavigationDrawer: não usar expand-on-hover

## Metodologia
- React/Replit = fonte da verdade absoluta
- Cada divergência Vue vs React = bug a corrigir
- Sem '[VER NO PROD]'. Sem 'verificar'. Cada issue com Antes/Depois concreto.
"""


def get_jira_token():
    hostname = os.environ.get("REPLIT_CONNECTORS_HOSTNAME")
    repl_identity = os.environ.get("REPL_IDENTITY")
    web_repl_renewal = os.environ.get("WEB_REPL_RENEWAL")

    if repl_identity:
        x_token = f"repl {repl_identity}"
    elif web_repl_renewal:
        x_token = f"depl {web_repl_renewal}"
    else:
        raise ValueError("Token Replit não encontrado")

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


def extract_description_text(card):
    desc = card.get("fields", {}).get("description")
    if not desc:
        return ""
    return adf_to_text(desc).strip()


def extract_vue_mentions(text):
    matches = re.findall(r"[\w./\-]+\.vue", text)
    return list(set(matches))


# ── BetterBugs ────────────────────────────────────────────────────────────────

def extract_betterbugs_url(text):
    """Extrai URL pública do BetterBugs da transcrição do card."""
    for pattern in [
        r'https?://(?:app\.)?betterbugs\.io/[^\s\'"<>\)]+',
        r'https?://betterbugs\.io/[^\s\'"<>\)]+',
    ]:
        m = re.search(pattern, text)
        if m:
            return m.group(0).rstrip(".,;)")
    return None


def fetch_betterbugs_content(url, timeout=20):
    """Busca e extrai conteúdo público de um link BetterBugs.

    Tenta extrair: título, descrição, logs de console, logs de rede,
    info do browser, device info e qualquer JSON de estado inicial.
    Retorna string formatada para ser injetada no prompt do Claude.
    """
    if not url or not url.startswith("http"):
        return None

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            return f"[BetterBugs] Erro HTTP {resp.status_code} ao acessar {url}"

        html = resp.text
        extracted = []

        # ── Tenta JSON embarcado (Next.js __NEXT_DATA__) ──
        next_match = re.search(
            r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
            html, re.DOTALL
        )
        if next_match:
            try:
                nd = json.loads(next_match.group(1))
                page_props = nd.get("props", {}).get("pageProps", nd)
                extracted.append(("📋 Dados da sessão BetterBugs (Next.js)",
                                   json.dumps(page_props, ensure_ascii=False, indent=2)[:6000]))
            except Exception:
                pass

        # ── Tenta JSON em script tags (React hydration, Nuxt, etc.) ──
        for var_pat in [
            r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});',
            r'window\.__data__\s*=\s*(\{.*?\});',
            r'window\.session\s*=\s*(\{.*?\});',
        ]:
            m = re.search(var_pat, html, re.DOTALL)
            if m:
                try:
                    d = json.loads(m.group(1))
                    extracted.append(("📋 Dados de sessão (variável window)",
                                       json.dumps(d, ensure_ascii=False, indent=2)[:4000]))
                    break
                except Exception:
                    pass

        # ── Tenta API JSON direta ──
        session_id_match = re.search(r'/(?:session|report|bug|s)/([a-zA-Z0-9_\-]{8,})', url)
        if session_id_match:
            session_id = session_id_match.group(1)
            for api_url in [
                f"https://app.betterbugs.io/api/session/{session_id}",
                f"https://api.betterbugs.io/session/{session_id}",
                f"https://app.betterbugs.io/api/sessions/{session_id}",
            ]:
                try:
                    api_resp = requests.get(api_url, headers={**headers, "Accept": "application/json"}, timeout=10)
                    if api_resp.status_code == 200 and "json" in api_resp.headers.get("content-type", ""):
                        extracted.append(("📡 API BetterBugs (JSON)",
                                           json.dumps(api_resp.json(), ensure_ascii=False, indent=2)[:6000]))
                        break
                except Exception:
                    pass

        # ── Extrai meta tags (Open Graph, Twitter Card) ──
        meta_parts = []
        for label, pat in [
            ("Título", r'<title[^>]*>(.*?)</title>'),
            ("OG Title", r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']'),
            ("OG Desc",  r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']'),
            ("OG Image", r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']'),
        ]:
            m = re.search(pat, html, re.DOTALL | re.IGNORECASE)
            if m:
                meta_parts.append(f"{label}: {m.group(1).strip()}")
        if meta_parts:
            extracted.append(("🔗 Meta informações da página", "\n".join(meta_parts)))

        # ── Extrai texto visível da página ──
        clean = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.DOTALL)
        clean = re.sub(r'<[^>]+>', ' ', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        if clean and len(clean) > 200:
            extracted.append(("📄 Texto visível da página", clean[:4000]))

        if not extracted:
            return (
                f"[BetterBugs] Página acessível mas sem conteúdo extraível (SPA pura). "
                f"URL: {url}\n"
                "NOTA: screenshots e vídeo disponíveis no link — analise a transcrição descrevendo o visível."
            )

        result = f"[BetterBugs] Conteúdo extraído de: {url}\n\n"
        for label, content in extracted:
            result += f"### {label}\n{content}\n\n"
        return result.strip()

    except requests.exceptions.Timeout:
        return f"[BetterBugs] Timeout ({timeout}s) ao acessar {url}"
    except requests.exceptions.ConnectionError as e:
        return f"[BetterBugs] Erro de conexão ao acessar {url}: {e}"
    except Exception as e:
        return f"[BetterBugs] Erro inesperado ao buscar conteúdo: {e}"


def find_react_files_by_keyword(keywords, max_files=5):
    found = []
    search_dirs = [
        os.path.join(WORKSPACE_ROOT, "plataforma-lia/src"),
    ]
    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            continue
        for root, dirs, files in os.walk(search_dir):
            dirs[:] = [d for d in dirs if d not in ("node_modules", ".next", "__pycache__", ".git")]
            for fname in files:
                if not fname.endswith((".tsx", ".ts")):
                    continue
                fname_lower = fname.lower()
                for kw in keywords:
                    if kw.lower() in fname_lower:
                        full_path = os.path.join(root, fname)
                        rel_path = os.path.relpath(full_path, WORKSPACE_ROOT)
                        if rel_path not in found:
                            found.append(rel_path)
                        break
            if len(found) >= max_files:
                break
        if len(found) >= max_files:
            break
    return found[:max_files]


def read_local_file(rel_path, max_lines=300):
    full_path = os.path.join(WORKSPACE_ROOT, rel_path)
    if not os.path.exists(full_path):
        return None, f"Arquivo não encontrado: {rel_path}"
    try:
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        if len(lines) > max_lines:
            content = "".join(lines[:max_lines]) + f"\n... [{len(lines) - max_lines} linhas omitidas]"
        else:
            content = "".join(lines)
        return content, None
    except Exception as e:
        return None, str(e)


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
        return None, f"Não encontrado: {file_path}"
    if resp.status_code != 200:
        return None, f"Erro {resp.status_code}: {resp.text[:200]}"
    data = resp.json()
    content = base64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")
    return content, None


def search_github_file(query, repo=None):
    token = os.environ.get("GITHUB_PAT_WEDOTALENT")
    if not token:
        return []
    if not repo:
        repo = f"{GITHUB_ORG}/{GITHUB_VUE_REPO}"
    url = f"https://api.github.com/search/code?q={query}+repo:{repo}+extension:vue&per_page=5"
    resp = requests.get(url, headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    })
    if resp.status_code != 200:
        return []
    return [item["path"] for item in resp.json().get("items", [])]


def run_audit_with_claude(card_key, summary, description_text, react_files, vue_files, betterbugs_content=None):
    try:
        import anthropic
        api_key = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
        base_url = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        client = anthropic.Anthropic(**kwargs)
    except Exception as e:
        raise ValueError(f"Erro ao inicializar Anthropic: {e}")

    react_section = "\n".join(
        f"--- REACT: {path} ---\n{content}"
        for path, content in react_files.items()
    ) or "(nenhum arquivo React encontrado — analise pela transcrição)"

    vue_section = "\n".join(
        f"--- VUE: {path} ---\n{content}"
        for path, content in vue_files.items()
    ) or "(nenhum arquivo Vue encontrado — gere issues baseadas na transcrição e nas regras DS)"

    from datetime import date
    today = date.today().strftime("%d/%m/%Y")

    prompt = f"""Você é um auditor de Design System especializado no DS LIA v4.2.1.
Metodologia: React/Replit = fonte da verdade absoluta. Cada divergência Vue vs React = bug confirmado.
Sem '[VER NO PROD]'. Sem 'verificar'. Cada issue com Antes/Depois concreto.

## CARD JIRA
Chave: {card_key}
Título: {summary}
Data: {today}

## TRANSCRIÇÃO / DESCRIÇÃO (lista de problemas reportados):
{description_text}

## EVIDÊNCIAS BETTERBUGS (screenshots, vídeo, console logs — contexto visual real do bug):
{betterbugs_content if betterbugs_content else "(link BetterBugs não encontrado na transcrição — analise apenas pelo texto)"}

## REGRAS DS LIA v4.2.1:
{DS_LIA_RULES}

## CÓDIGO REACT (Replit — fonte da verdade — CORRETO):
{react_section}

## CÓDIGO VUE (GitHub WeDOTalent — A AUDITAR):
{vue_section}

## TAREFA
1. Leia a transcrição e mapeie TODOS os elementos de design mencionados:
   botões, bordas, ícones, tipografia, cores, espaçamentos, comportamentos visuais, estados, animações, logos, etc.

2. Para cada elemento: compare React vs Vue e identifique divergências.

3. Identifique TAMBÉM divergências de Vuetify defaults (tamanhos, variants, elevation, etc.)

Gere um JSON com a estrutura exata abaixo:

{{
  "tela": "Nome da tela/componente auditado",
  "rota": "/rota/da/tela",
  "arquivo_vue_principal": "components/ui/menu/sidebar.vue",
  "issues": [
    {{
      "numero": "01",
      "titulo": "Descrição curta do bug (ex: Comportamento de visibilidade incorreto)",
      "arquivo_vue": "components/ui/menu/sidebar.vue",
      "regra_ds": "Regra DS LIA violada (ex: O menu deve estar sempre visível, não aparecer só no hover)",
      "antes_label": "Vue atual — INCORRETO",
      "antes_codigo": "código vue incorreto exato",
      "antes_lang": "vue",
      "depois_label": "deve ficar assim — React/DS LIA",
      "depois_codigo": "código vue corrigido exato",
      "depois_lang": "vue",
      "warning": "⚠️ Explicação do impacto visual/funcional deste bug"
    }}
  ],
  "vuetify_defaults": [
    {{
      "componente": "v-icon",
      "titulo": "v-icon — size ausente",
      "default_vuetify": "24px (padrão Material Design)",
      "react_correto": "w-4 h-4 = 16px (padrão DS LIA)",
      "impacto": "8px a mais no produto — ícones visivelmente grandes",
      "fix_local": "<v-icon size=\\"16\\">mdi-*</v-icon>",
      "fix_global": "VIcon: {{ size: '16' }}"
    }}
  ],
  "vuetify_ts_code": "createVuetify({{\\n  defaults: {{\\n    VIcon: {{ size: '16' }},\\n    VBtn: {{ variant: 'flat', size: 'small' }},\\n    VCard: {{ elevation: 0 }},\\n  }}\\n}})",
  "comportamento_esperado": [
    {{
      "dado": "que o designer ou dev está implementando este componente Vue",
      "quando": "renderiza o componente na tela",
      "entao": "o resultado visual é idêntico ao equivalente React no Replit",
      "e": "todas as medidas (px), cores, bordas e comportamentos coincidem"
    }}
  ],
  "fora_de_escopo": [
    "O que NÃO será corrigido nesta auditoria (apenas design — lógica de negócio fora do escopo)"
  ],
  "impacto_outros_sistemas": [
    {{
      "sistema": "Nome do componente/tela impactado",
      "descricao": "Como a correção do design pode afetar outros componentes que usam este"
    }}
  ],
  "definition_of_done": [
    "[ ] Todas as issues desta auditoria corrigidas e verificadas visualmente",
    "[ ] vuetify.ts atualizado com defaults DS LIA (se aplicável)",
    "[ ] Componente revisado por outro dev ou designer",
    "[ ] Sem regressão visual em telas que usam os componentes corrigidos",
    "[ ] PR linkado a este card com checklist preenchido"
  ]
}}

REGRAS:
- Mínimo 5 issues, máximo 15
- Números com zero à esquerda: "01", "02", etc.
- Código ANTES/DEPOIS deve ser real e específico (não genérico)
- Se não tiver código Vue, gere o DEPOIS correto baseado nas regras DS LIA e no React
- vuetify_defaults: inclua apenas os que aparecem nesta tela especificamente
- comportamento_esperado: um cenário DADO/QUANDO/ENTÃO por comportamento visual que o card menciona
- fora_de_escopo: liste explicitamente o que não será corrigido (lógica de negócio, APIs, etc.)
- impacto_outros_sistemas: componentes que herdam ou reutilizam o que está sendo corrigido
- definition_of_done: adapte com itens específicos desta auditoria
- Responda APENAS o JSON, sem markdown, sem explicação"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        lines = raw.splitlines()
        for _ in range(min(30, len(lines))):
            lines.pop()
            try:
                candidate = "\n".join(lines) + "\n}"
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
        raise ValueError(f"Resposta do Claude não é JSON válido mesmo após recovery:\n{raw[:500]}")


def build_audit_adf(data, card_key, summary):
    """Constrói ADF de auditoria de design com issues numeradas e Vuetify defaults."""
    nodes = []
    from datetime import date
    today = date.today().strftime("%d/%m/%Y")

    def heading(level, text):
        return {"type": "heading", "attrs": {"level": level}, "content": [{"type": "text", "text": text}]}

    def paragraph(text, bold=False):
        if bold:
            return {"type": "paragraph", "content": [{"type": "text", "text": text, "marks": [{"type": "strong"}]}]}
        return {"type": "paragraph", "content": [{"type": "text", "text": text}]}

    def paragraph_mixed(*parts):
        content = []
        for text, is_bold, is_code in parts:
            node = {"type": "text", "text": text}
            marks = []
            if is_bold:
                marks.append({"type": "strong"})
            if is_code:
                marks.append({"type": "code"})
            if marks:
                node["marks"] = marks
            content.append(node)
        return {"type": "paragraph", "content": content}

    def bullet_list_mixed(items):
        list_items = []
        for item in items:
            if isinstance(item, str):
                content_node = [{"type": "paragraph", "content": [{"type": "text", "text": item}]}]
            elif isinstance(item, dict):
                content_node = [item]
            else:
                content_node = [item]
            list_items.append({"type": "listItem", "content": content_node})
        return {"type": "bulletList", "content": list_items}

    def code_block(code, language="", max_chars=600):
        text = str(code)
        if len(text) > max_chars:
            text = text[:max_chars] + f"\n... [truncado — {len(str(code)) - max_chars} chars omitidos]"
        return {"type": "codeBlock", "attrs": {"language": language}, "content": [{"type": "text", "text": text}]}

    def rule():
        return {"type": "rule"}

    tela = data.get("tela", summary)
    rota = data.get("rota", "/")
    arquivo_vue = data.get("arquivo_vue_principal", "")

    nodes.append(heading(1, f"AUDITORIA DE DESIGN — LIA Design System v4.2.1"))

    meta_items = [
        f"Card Jira: {card_key}",
        f"Tela: {tela}",
        f"Rota: {rota}",
        f"Gerado em: {today}",
    ]
    for item in meta_items:
        nodes.append(paragraph(item))

    if arquivo_vue:
        nodes.append(paragraph(f"Arquivos auditados: {arquivo_vue}"))

    nodes.append(rule())

    nodes.append(heading(2, "🔍 Issues de Auditoria — React vs Vue"))
    nodes.append(paragraph(
        "Metodologia: React/Replit = fonte da verdade absoluta.\n"
        "Cada Issue abaixo é um bug confirmado — Vue diverge do React.\n"
        "Sem '[VER NO PROD]'. Sem 'verificar'. Cada Issue tem Antes/Depois concreto.\n"
        "Comportamento Esperado, Fora de Escopo, DoD e Impactos: veja o comentário abaixo."
    ))

    nodes.append(rule())

    nodes.append(heading(2, "Issues Identificadas"))

    for issue in data.get("issues", []):
        num = issue.get("numero", "?")
        titulo = issue.get("titulo", "")
        arquivo = issue.get("arquivo_vue", "")
        regra = issue.get("regra_ds", "")
        antes_label = issue.get("antes_label", "ANTES (Vue atual — INCORRETO)")
        antes_cod = issue.get("antes_codigo", "")
        antes_lang = issue.get("antes_lang", "vue")
        depois_label = issue.get("depois_label", "DEPOIS (deve ficar assim — React/DS LIA)")
        depois_cod = issue.get("depois_codigo", "")
        depois_lang = issue.get("depois_lang", "vue")
        warning = issue.get("warning", "")

        nodes.append(heading(3, f"Issue {num} — {titulo}"))

        if arquivo:
            nodes.append(paragraph_mixed(
                ("Arquivo Vue: ", False, False),
                (arquivo, False, True),
            ))
        if regra:
            nodes.append(paragraph_mixed(
                ("Regra DS LIA: ", False, False),
                (regra, False, False),
            ))
        nodes.append(paragraph(""))

        nodes.append(paragraph(f"{antes_label}:", bold=True))
        if antes_cod:
            nodes.append(code_block(antes_cod, antes_lang))

        nodes.append(paragraph(f"{depois_label}:", bold=True))
        if depois_cod:
            nodes.append(code_block(depois_cod, depois_lang))

        if warning:
            nodes.append(paragraph(warning))

        nodes.append(rule())

    nodes.append(heading(2, "⚠️ ALERTA VUETIFY DEFAULTS — Para dev / ClaudeCode / Cursor"))
    nodes.append(paragraph(
        "Causa raiz sistêmica: Os Issues abaixo não são erros isolados — são causados por\n"
        "defaults implícitos do Vuetify que divergem do DS LIA (React/Replit = fonte da verdade).\n"
        "Corrija localmente E atualize o arquivo vuetify.ts (global defaults) para\n"
        "evitar que os mesmos erros apareçam em features futuras."
    ))
    nodes.append(heading(3, "Defaults identificados nesta auditoria"))

    for default in data.get("vuetify_defaults", []):
        titulo_d = default.get("titulo", default.get("componente", ""))
        nodes.append(heading(4, titulo_d))

        items_d = []
        if default.get("default_vuetify"):
            items_d.append(f"Vuetify default implícito: {default['default_vuetify']}")
        if default.get("react_correto"):
            items_d.append(f"React/Replit (correto): {default['react_correto']}")
        if default.get("impacto"):
            items_d.append(f"Impacto visual: {default['impacto']}")
        if default.get("fix_local"):
            items_d.append(f"Fix local: {default['fix_local']}")
        if default.get("fix_global"):
            items_d.append(f"Fix global (vuetify.ts): {default['fix_global']}")

        if items_d:
            nodes.append(bullet_list_mixed(items_d))

    vuetify_ts = data.get("vuetify_ts_code", "")
    if vuetify_ts:
        nodes.append(heading(3, "Como atualizar o vuetify.ts"))
        nodes.append(code_block(vuetify_ts, "typescript"))

    nodes.append(rule())

    nodes.append(paragraph(
        "Referência: React/Replit é sempre a fonte da verdade de design.\n"
        "Qualquer componente Vue que diverge do React = bug a corrigir.\n"
        "Comportamento Esperado, Fora de Escopo, DoD e Impactos estão no comentário abaixo."
    ))

    return {"version": 1, "type": "doc", "content": nodes}


def build_audit_comment_adf(data, card_key, summary):
    """Constrói ADF do comentário: comportamento esperado, fora de escopo, impacto e DoD."""
    nodes = []
    from datetime import date
    today = date.today().strftime("%d/%m/%Y")

    def heading(level, text):
        return {"type": "heading", "attrs": {"level": level}, "content": [{"type": "text", "text": text}]}

    def paragraph(text, bold=False):
        if bold:
            return {"type": "paragraph", "content": [{"type": "text", "text": text, "marks": [{"type": "strong"}]}]}
        return {"type": "paragraph", "content": [{"type": "text", "text": text}]}

    def bullet_list_mixed(items):
        list_items = []
        for item in items:
            if isinstance(item, str):
                content_node = [{"type": "paragraph", "content": [{"type": "text", "text": item}]}]
            elif isinstance(item, dict):
                content_node = [item]
            else:
                content_node = [item]
            list_items.append({"type": "listItem", "content": content_node})
        return {"type": "bulletList", "content": list_items}

    def code_block(code, language=""):
        text = str(code)[:600]
        return {"type": "codeBlock", "attrs": {"language": language}, "content": [{"type": "text", "text": text}]}

    def rule():
        return {"type": "rule"}

    nodes.append(heading(1, f"Análise Complementar — {summary}"))
    nodes.append(paragraph(f"Card: {card_key} | Gerado em: {today}"))
    nodes.append(rule())

    comportamentos = data.get("comportamento_esperado", [])
    if comportamentos:
        nodes.append(heading(2, "🎯 Comportamento Esperado (Spec Driven)"))
        nodes.append(paragraph(
            "Spec formal do comportamento visual correto — usada como contexto para Cursor/Claude Code."
        ))
        for c in comportamentos:
            dado = c.get("dado", "")
            quando = c.get("quando", "")
            entao = c.get("entao", "")
            e_extra = c.get("e", "")
            bloco = f"DADO {dado}\nQUANDO {quando}\nENTÃO {entao}"
            if e_extra:
                bloco += f"\nE {e_extra}"
            nodes.append(code_block(bloco, "gherkin"))
        nodes.append(rule())

    fora = data.get("fora_de_escopo", [])
    if fora:
        nodes.append(heading(2, "🚫 Fora de Escopo"))
        nodes.append(paragraph("O que NÃO será corrigido nesta auditoria."))
        nodes.append(bullet_list_mixed(fora))
        nodes.append(rule())

    impactos = data.get("impacto_outros_sistemas", [])
    if impactos:
        nodes.append(heading(2, "💥 Impacto em Outros Sistemas"))
        nodes.append(paragraph("Componentes ou telas que podem ser afetados pelas correções."))
        items_imp = []
        for imp in impactos:
            if isinstance(imp, dict):
                sistema = imp.get("sistema", "")
                desc = imp.get("descricao", "")
                items_imp.append(f"{sistema} — {desc}" if sistema else desc)
            else:
                items_imp.append(str(imp))
        nodes.append(bullet_list_mixed(items_imp))
        nodes.append(rule())

    dod = data.get("definition_of_done", [])
    if dod:
        nodes.append(heading(2, "🏁 Definition of Done"))
        nodes.append(paragraph(
            "Checklist obrigatório antes do PR de design ser aprovado. "
            "Sem todos esses itens marcados, o card não fecha."
        ))
        nodes.append(bullet_list_mixed(dod))
        nodes.append(rule())

    criterios = data.get("criterios_aceite", [])
    if criterios:
        nodes.append(heading(2, "✅ Critérios de Aceite"))
        nodes.append(paragraph("Condições que devem ser verdadeiras para o card ser aceito."))
        nodes.append(bullet_list_mixed(criterios))
        nodes.append(rule())

    return {"version": 1, "type": "doc", "content": nodes}


def update_card(token, issue_key, adf_description):
    url = f"{BASE_URL}/issue/{issue_key}"
    resp = requests.put(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"},
        json={"fields": {"description": adf_description}},
    )
    return resp.status_code, resp.text


def add_comment(token, issue_key, adf_body):
    """Adiciona um comentário ADF ao card Jira."""
    url = f"{BASE_URL}/issue/{issue_key}/comment"
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"},
        json={"body": adf_body},
    )
    return resp.status_code, resp.text


def main():
    parser = argparse.ArgumentParser(description="Auditoria de Design DS LIA v4.2.1 para card Jira")
    parser.add_argument("issue_key", help="Chave do card Jira (ex: WT-1637)")
    parser.add_argument("--dry-run", action="store_true", help="Mostra resultado mas não atualiza o Jira")
    parser.add_argument("--react-file", action="append", default=[], help="Arquivo React (path relativo ao workspace)")
    parser.add_argument("--vue-file", action="append", default=[], help="Arquivo Vue no GitHub (ex: components/ui/menu/sidebar.vue)")
    args = parser.parse_args()

    issue_key = args.issue_key.upper()

    print("=" * 70)
    print(f"JIRA AUDIT DESIGN — DS LIA v4.2.1 — {issue_key}")
    print("=" * 70)

    print("\n[1/6] Buscando credenciais Jira...")
    token = get_jira_token()
    print("✓ Token obtido")

    print(f"\n[2/6] Buscando card {issue_key}...")
    card = fetch_card(token, issue_key)
    summary = card["fields"].get("summary", "")
    existing_desc_adf = card["fields"].get("description") or {}
    description_text = adf_to_text(existing_desc_adf).strip()
    print(f"✓ Card: {summary}")
    print(f"  Transcrição: {len(description_text)} caracteres")
    print(f"  Descrição original: NÃO será modificada — auditoria vai como comentários")

    mentioned_vue = extract_vue_mentions(description_text)

    words_raw = re.findall(r"\b[a-z][a-z]{3,}\b", summary.lower() + " " + description_text.lower())
    stopwords = {"that", "this", "with", "from", "have", "para", "como", "deve", "pelo", "pela", "está", "menu",
                 "logo", "card", "jira", "side", "left", "right", "when", "only", "mais", "item", "list", "show",
                 "hide", "view", "open", "issue", "issues", "only", "appears", "button", "pass", "mouse", "also",
                 "common", "which", "there", "missing", "parts", "look", "product", "correct", "these", "relation",
                 "dynamic", "expansion", "incorrect", "correction", "corrections"}
    keywords = list(set([w for w in words_raw if w not in stopwords]))[:8]

    print(f"  Keywords extraídas: {', '.join(keywords[:5])}")
    if mentioned_vue:
        print(f"  Arquivos Vue mencionados: {', '.join(mentioned_vue)}")

    print(f"\n[3/6] Coletando código React (Replit — fonte da verdade)...")
    react_files = {}

    for rf in args.react_file:
        content, err = read_local_file(rf)
        if content:
            react_files[rf] = content
            print(f"  ✓ {rf}")
        else:
            print(f"  ✗ {rf}: {err}")

    if not react_files:
        found = find_react_files_by_keyword(keywords[:6])
        for f in found[:4]:
            content, err = read_local_file(f)
            if content:
                react_files[f] = content
                print(f"  ✓ {f} (auto, {len(content)} chars)")

    if not react_files:
        print("  ⚠ Nenhum arquivo React encontrado — auditoria baseada na transcrição + regras DS")

    print(f"\n[4/6] Coletando código Vue (GitHub WeDOTalent/{GITHUB_VUE_REPO})...")
    vue_files = {}

    specific_vue = list(args.vue_file)
    if not specific_vue:
        specific_vue = mentioned_vue[:2]

    for vf in specific_vue:
        content, err = fetch_github_file(vf)
        if content:
            vue_files[vf] = content
            print(f"  ✓ {vf} ({len(content)} chars)")
        else:
            print(f"  ✗ {vf}: {err}")

    if not vue_files:
        for kw in keywords[:4]:
            results = search_github_file(kw)
            for path in results:
                if path not in vue_files:
                    content, err = fetch_github_file(path)
                    if content:
                        vue_files[path] = content
                        print(f"  ✓ {path} (auto, {len(content)} chars)")
                        break
            if vue_files:
                break

    if not vue_files:
        print("  ⚠ Nenhum arquivo Vue encontrado — auditoria baseada na transcrição + regras DS")

    print(f"\n[5/6] Auditando com Claude (DS LIA v4.2.1)...")
    print(f"  Buscando conteúdo BetterBugs...")
    betterbugs_url = extract_betterbugs_url(description_text)
    betterbugs_content = None
    if betterbugs_url:
        print(f"  ✓ BetterBugs URL encontrado: {betterbugs_url[:80]}...")
        betterbugs_content = fetch_betterbugs_content(betterbugs_url)
        if betterbugs_content and not betterbugs_content.startswith("[BetterBugs] Erro"):
            print(f"  ✓ Conteúdo BetterBugs extraído ({len(betterbugs_content)} chars)")
        else:
            print(f"  ⚠ BetterBugs: {betterbugs_content[:100] if betterbugs_content else 'sem conteúdo'}")
    else:
        print(f"  — BetterBugs URL não encontrado na transcrição")
    audit_data = run_audit_with_claude(issue_key, summary, description_text, react_files, vue_files, betterbugs_content)
    issues = audit_data.get("issues", [])
    defaults = audit_data.get("vuetify_defaults", [])
    print(f"✓ Auditoria gerada")
    print(f"  {len(issues)} issues identificadas")
    print(f"  {len(defaults)} Vuetify defaults a corrigir")
    for iss in issues:
        print(f"  → Issue {iss.get('numero', '?')}: {iss.get('titulo', '')}")

    audit_comment_adf = build_audit_adf(audit_data, issue_key, summary)
    supplement_adf = build_audit_comment_adf(audit_data, issue_key, summary)

    has_supplement = any([
        audit_data.get("comportamento_esperado"),
        audit_data.get("fora_de_escopo"),
        audit_data.get("impacto_outros_sistemas"),
        audit_data.get("definition_of_done"),
        audit_data.get("criterios_aceite"),
    ])

    if args.dry_run:
        print("\n[DRY RUN] Preview das issues (não enviado ao Jira):")
        for iss in issues:
            print(f"\n  Issue {iss.get('numero')}: {iss.get('titulo')}")
            print(f"    Arquivo: {iss.get('arquivo_vue', '-')}")
            print(f"    Regra: {iss.get('regra_ds', '-')[:80]}")
        dod = audit_data.get("definition_of_done", [])
        if dod:
            print(f"\n  DoD ({len(dod)} itens) — iria para comentário 2")
        print(f"\n✅ DRY RUN concluído. Remova --dry-run para publicar no Jira.")
        return

    print(f"\n[6/6] Publicando no Jira...")
    print(f"  NOTA: A descrição original do card NÃO será modificada.")
    print(f"  Toda a auditoria vai para comentários (mais estável que o PUT /description).")

    print(f"  [Comentário 1/2] Postando issues de design ({len(issues)} issues + {len(defaults)} Vuetify defaults)...")
    c1_status, c1_text = add_comment(token, issue_key, audit_comment_adf)
    if c1_status in (200, 201):
        print(f"  ✓ Comentário 1 adicionado ({len(issues)} issues de design + Vuetify defaults)")
    else:
        print(f"  ❌ Erro no comentário 1 — {c1_status}: {c1_text[:400]}")

    if has_supplement:
        print(f"  [Comentário 2/2] Postando comportamento esperado + DoD + critérios...")
        c2_status, c2_text = add_comment(token, issue_key, supplement_adf)
        if c2_status in (200, 201):
            dod_count = len(audit_data.get("definition_of_done", []))
            comport_count = len(audit_data.get("comportamento_esperado", []))
            print(f"  ✓ Comentário 2 adicionado ({comport_count} comportamentos + {dod_count} DoD)")
        else:
            print(f"  ❌ Erro no comentário 2 — {c2_status}: {c2_text[:300]}")
        c_ok = c1_status in (200, 201) and c2_status in (200, 201)
    else:
        c_ok = c1_status in (200, 201)

    if c_ok:
        print(f"\n✅ Card {issue_key} atualizado com auditoria de design!")
        print(f"   URL: https://wedotalent.atlassian.net/browse/{issue_key}")
    else:
        print(f"\n❌ Erro ao publicar auditoria no Jira")


if __name__ == "__main__":
    main()
