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


def run_audit_with_claude(card_key, summary, description_text, react_files, vue_files):
    try:
        import anthropic
        client = anthropic.Anthropic()
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
  "vuetify_ts_code": "createVuetify({{\\n  defaults: {{\\n    VIcon: {{ size: '16' }},\\n    VBtn: {{ variant: 'flat', size: 'small' }},\\n    VCard: {{ elevation: 0 }},\\n  }}\\n}})"
}}

REGRAS:
- Mínimo 5 issues, máximo 15
- Números com zero à esquerda: "01", "02", etc.
- Código ANTES/DEPOIS deve ser real e específico (não genérico)
- Se não tiver código Vue, gere o DEPOIS correto baseado nas regras DS LIA e no React
- vuetify_defaults: inclua apenas os que aparecem nesta tela especificamente
- Responda APENAS o JSON, sem markdown, sem explicação"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=10000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


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

    def code_block(code, language=""):
        return {"type": "codeBlock", "attrs": {"language": language}, "content": [{"type": "text", "text": code}]}

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

    nodes.append(rule())

    nodes.append(heading(2, "🔍 Issues de Auditoria — React vs Vue (gerados por IA)"))
    nodes.append(paragraph(
        "Metodologia: React/Replit = fonte da verdade absoluta.\n"
        "Cada Issue abaixo é um bug confirmado — Vue diverge do React.\n"
        "Sem '[VER NO PROD]'. Sem 'verificar'. Cada Issue tem Antes/Depois concreto."
    ))

    nodes.append(heading(1, f"Auditoria DS LIA v4.2.1 — {tela}"))
    nodes.append(paragraph(f"Card Jira: {card_key}"))
    nodes.append(paragraph(f"Tela: {tela}"))
    if arquivo_vue:
        nodes.append(paragraph(f"Arquivos auditados: {arquivo_vue}"))
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
        "Qualquer componente Vue que diverge do React = bug a corrigir."
    ))

    return {"version": 1, "type": "doc", "content": nodes}


def update_card(token, issue_key, adf_description):
    url = f"{BASE_URL}/issue/{issue_key}"
    resp = requests.put(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"},
        json={"fields": {"description": adf_description}},
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

    print("\n[1/5] Buscando credenciais Jira...")
    token = get_jira_token()
    print("✓ Token obtido")

    print(f"\n[2/5] Buscando card {issue_key}...")
    card = fetch_card(token, issue_key)
    summary = card["fields"].get("summary", "")
    description_text = adf_to_text(card["fields"].get("description") or {}).strip()
    print(f"✓ Card: {summary}")
    print(f"  Transcrição: {len(description_text)} caracteres")

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

    print(f"\n[3/5] Coletando código React (Replit — fonte da verdade)...")
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

    print(f"\n[4/5] Coletando código Vue (GitHub WeDOTalent/{GITHUB_VUE_REPO})...")
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

    print(f"\n[5/5] Auditando com Claude (DS LIA v4.2.1)...")
    audit_data = run_audit_with_claude(issue_key, summary, description_text, react_files, vue_files)
    issues = audit_data.get("issues", [])
    defaults = audit_data.get("vuetify_defaults", [])
    print(f"✓ Auditoria gerada")
    print(f"  {len(issues)} issues identificadas")
    print(f"  {len(defaults)} Vuetify defaults a corrigir")
    for iss in issues:
        print(f"  → Issue {iss.get('numero', '?')}: {iss.get('titulo', '')}")

    adf = build_audit_adf(audit_data, issue_key, summary)

    if args.dry_run:
        print("\n[DRY RUN] Preview das issues (não enviado ao Jira):")
        for iss in issues:
            print(f"\n  Issue {iss.get('numero')}: {iss.get('titulo')}")
            print(f"    Arquivo: {iss.get('arquivo_vue', '-')}")
            print(f"    Regra: {iss.get('regra_ds', '-')[:80]}")
        print(f"\n✅ DRY RUN concluído. Remova --dry-run para publicar no Jira.")
        return

    print(f"\nPublicando auditoria no Jira...")
    status_code, text = update_card(token, issue_key, adf)
    if status_code in (200, 204):
        print(f"\n✅ Card {issue_key} atualizado com auditoria de design!")
        print(f"   URL: https://wedotalent.atlassian.net/browse/{issue_key}")
    else:
        print(f"\n❌ Erro {status_code}: {text[:400]}")


if __name__ == "__main__":
    main()
