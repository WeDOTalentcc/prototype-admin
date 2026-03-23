#!/usr/bin/env python3
"""
jira-fetch-analyze.py — Lê card Jira, analisa transcrição + código (React/Replit + Vue/GitHub)
e gera documentação técnica estruturada de volta no card.

Uso:
    python3 scripts/jira-fetch-analyze.py WT-1234
    python3 scripts/jira-fetch-analyze.py WT-1234 --dry-run
    python3 scripts/jira-fetch-analyze.py WT-1234 --react-file src/components/sidebar.tsx
    python3 scripts/jira-fetch-analyze.py WT-1234 --vue-file components/ui/menu/sidebar.vue

Fluxo:
    1. Busca card no Jira (transcrição + pontos + BetterBugs link)
    2. Extrai menções de componentes, funcionalidades, arquivos
    3. Lê código React no Replit (local)
    4. Lê código Vue no GitHub (WeDOTalent)
    5. Envia para Claude → gera documentação estruturada
    6. Atualiza card no Jira com ADF formatado
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
    url = f"{BASE_URL}/issue/{issue_key}?fields=summary,description,status,labels,comment"
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
    if resp.status_code != 200:
        raise ValueError(f"Erro ao buscar card {issue_key}: {resp.status_code} {resp.text[:300]}")
    return resp.json()


def adf_to_text(node):
    """Converte ADF (Atlassian Document Format) para texto plano."""
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
    """Extrai texto da descrição do card (ADF → texto plano)."""
    fields = card.get("fields", {})
    desc = fields.get("description")
    if not desc:
        return ""
    return adf_to_text(desc).strip()


def extract_file_mentions(text):
    """Extrai caminhos de arquivo mencionados no texto do card."""
    patterns = [
        r"plataforma-lia/[^\s\n,]+\.(tsx|ts|css|py)",
        r"src/[^\s\n,]+\.(tsx|ts|css)",
        r"app/[^\s\n,]+\.(tsx|ts|py)",
        r"components/[^\s\n,]+\.(tsx|ts|vue)",
        r"pages/[^\s\n,]+\.(tsx|ts|vue)",
        r"hooks/[^\s\n,]+\.(tsx|ts)",
    ]
    files = set()
    for pattern in patterns:
        for match in re.findall(pattern, text):
            pass
        for match in re.finditer(r"(?:plataforma-lia/|src/|app/|components/|hooks/|pages/)[\w./\-]+\.(?:tsx|ts|css|py|vue)", text):
            files.add(match.group(0))
    return list(files)


def extract_vue_mentions(text):
    """Extrai menções de arquivos Vue no texto."""
    matches = re.findall(r"components/[\w./\-]+\.vue", text)
    return list(set(matches))


def find_local_files_by_keyword(keywords, base_dir=WORKSPACE_ROOT, max_files=6):
    """Busca arquivos locais por palavras-chave no nome."""
    found = []
    search_dirs = [
        os.path.join(base_dir, "plataforma-lia/src"),
        os.path.join(base_dir, "lia-agent-system/app"),
    ]
    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            continue
        for root, dirs, files in os.walk(search_dir):
            dirs[:] = [d for d in dirs if d not in ("node_modules", ".next", "__pycache__", ".git")]
            for fname in files:
                if not fname.endswith((".tsx", ".ts", ".py", ".css")):
                    continue
                fname_lower = fname.lower()
                for kw in keywords:
                    if kw.lower() in fname_lower:
                        full_path = os.path.join(root, fname)
                        rel_path = os.path.relpath(full_path, base_dir)
                        found.append(rel_path)
                        break
            if len(found) >= max_files:
                break
        if len(found) >= max_files:
            break
    return found[:max_files]


def read_local_file(rel_path, max_lines=200):
    """Lê arquivo local do workspace."""
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
    """Busca arquivo do GitHub (WeDOTalent)."""
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
        return None, f"Arquivo não encontrado no GitHub: {file_path}"
    if resp.status_code != 200:
        return None, f"Erro GitHub {resp.status_code}: {resp.text[:200]}"
    data = resp.json()
    content_b64 = data.get("content", "")
    content = base64.b64decode(content_b64).decode("utf-8", errors="replace")
    return content, None


def search_github_file(filename_pattern, repo=None):
    """Busca arquivo por padrão de nome no GitHub."""
    token = os.environ.get("GITHUB_PAT_WEDOTALENT")
    if not token:
        return []
    if not repo:
        repo = f"{GITHUB_ORG}/{GITHUB_VUE_REPO}"
    url = f"https://api.github.com/search/code?q={filename_pattern}+repo:{repo}&per_page=5"
    resp = requests.get(url, headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    })
    if resp.status_code != 200:
        return []
    items = resp.json().get("items", [])
    return [item["path"] for item in items]


def analyze_with_claude(card_key, summary, description_text, react_files_content, vue_files_content):
    """Envia dados para Claude e recebe documentação estruturada."""
    try:
        import anthropic
        client = anthropic.Anthropic()
    except Exception as e:
        raise ValueError(f"Erro ao inicializar Anthropic: {e}")

    react_section = ""
    for path, content in react_files_content.items():
        react_section += f"\n--- ARQUIVO: {path} ---\n{content}\n"

    vue_section = ""
    for path, content in vue_files_content.items():
        vue_section += f"\n--- ARQUIVO VUE: {path} ---\n{content}\n"

    prompt = f"""Você é um engenheiro senior da Plataforma LIA (WeDOTalent).

Analise o card Jira abaixo e o código relacionado. Gere documentação técnica estruturada completa.

## CARD JIRA
Chave: {card_key}
Título: {summary}

## TRANSCRIÇÃO / DESCRIÇÃO DO CARD:
{description_text}

## CÓDIGO REACT (Replit — fonte da verdade):
{react_section if react_section else "(nenhum arquivo React encontrado)"}

## CÓDIGO VUE (GitHub WeDOTalent):
{vue_section if vue_section else "(nenhum arquivo Vue encontrado)"}

## INSTRUÇÕES
A partir da transcrição e do código, gere um JSON com a estrutura exata abaixo:

{{
  "titulo_auditoria": "Título descritivo da auditoria/feature",
  "resumo": "Parágrafo descrevendo o que a feature/bug envolve e o que foi implementado/analisado",
  "arquivos_de_referencia": [
    {{"path": "caminho/do/arquivo.tsx", "descricao": "O que este arquivo faz"}}
  ],
  "secoes_tecnicas": [
    {{
      "titulo": "🔧 Nome da Seção (ex: Layout Geral, Comportamento, Integração)",
      "items": ["item 1 com detalhe técnico", "item 2", "..."]
    }}
  ],
  "action_items": [
    "[ ] Ação concreta a ser feita",
    "[ ] Outra ação"
  ],
  "criterios_de_aceite": [
    "[Area] Critério verificável e concreto",
    "[Area] Outro critério"
  ]
}}

REGRAS:
- Extraia TODOS os elementos mencionados na transcrição: botões, bordas, ícones, comportamentos, estados, tipografia
- Os arquivos de referência devem ser os arquivos REAIS encontrados no código
- Critérios de aceite: mínimo 10, concretos e verificáveis
- Seções técnicas: mínimo 3, baseadas no que a transcrição descreve
- Responda APENAS o JSON, sem markdown, sem explicação adicional"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


def build_adf(data, card_key, summary):
    """Constrói ADF (Atlassian Document Format) a partir dos dados da análise."""
    nodes = []

    def heading(level, text):
        return {"type": "heading", "attrs": {"level": level}, "content": [{"type": "text", "text": text}]}

    def paragraph(text, bold=False):
        if bold:
            return {"type": "paragraph", "content": [{"type": "text", "text": text, "marks": [{"type": "strong"}]}]}
        return {"type": "paragraph", "content": [{"type": "text", "text": text}]}

    def bullet_list(items):
        list_items = []
        for item in items:
            if isinstance(item, str):
                content = [{"type": "paragraph", "content": [{"type": "text", "text": item}]}]
            else:
                content = [item]
            list_items.append({"type": "listItem", "content": content})
        return {"type": "bulletList", "content": list_items}

    def rule():
        return {"type": "rule"}

    def code_block(code, language=""):
        return {"type": "codeBlock", "attrs": {"language": language}, "content": [{"type": "text", "text": code}]}

    titulo = data.get("titulo_auditoria", summary)
    nodes.append(heading(1, titulo))
    nodes.append(paragraph(data.get("resumo", "")))
    nodes.append(rule())

    arquivos = data.get("arquivos_de_referencia", [])
    if arquivos:
        nodes.append(heading(2, "📁 Arquivos de Referência (Protótipo Replit)"))
        items = []
        for arq in arquivos:
            if isinstance(arq, dict):
                items.append(f"{arq['path']}: {arq.get('descricao', '')}")
            else:
                items.append(str(arq))
        nodes.append(bullet_list(items))
        nodes.append(rule())

    for secao in data.get("secoes_tecnicas", []):
        nodes.append(heading(2, secao.get("titulo", "Seção")))
        items = secao.get("items", [])
        if items:
            nodes.append(bullet_list(items))
        nodes.append(rule())

    action_items = data.get("action_items", [])
    if action_items:
        nodes.append(heading(2, "📋 Action Items"))
        nodes.append(bullet_list(action_items))
        nodes.append(rule())

    criterios = data.get("criterios_de_aceite", [])
    if criterios:
        nodes.append(heading(2, "✅ Critérios de Aceite"))
        nodes.append(bullet_list(criterios))

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
    parser = argparse.ArgumentParser(description="Analisa card Jira e gera documentação técnica")
    parser.add_argument("issue_key", help="Chave do card Jira (ex: WT-1637)")
    parser.add_argument("--dry-run", action="store_true", help="Mostra resultado mas não atualiza o Jira")
    parser.add_argument("--react-file", action="append", default=[], help="Arquivo React específico (path relativo ao workspace)")
    parser.add_argument("--vue-file", action="append", default=[], help="Arquivo Vue específico no GitHub (ex: components/ui/menu/sidebar.vue)")
    args = parser.parse_args()

    issue_key = args.issue_key.upper()

    print("=" * 70)
    print(f"JIRA FETCH ANALYZE — {issue_key}")
    print("=" * 70)

    print("\n[1/5] Buscando credenciais Jira...")
    token = get_jira_token()
    print("✓ Token obtido")

    print(f"\n[2/5] Buscando card {issue_key}...")
    card = fetch_card(token, issue_key)
    summary = card["fields"].get("summary", "")
    description_text = extract_description_text(card)
    print(f"✓ Card: {summary}")
    print(f"  Descrição: {len(description_text)} caracteres")

    mentioned_files = extract_file_mentions(description_text)
    mentioned_vue = extract_vue_mentions(description_text)

    words = re.findall(r"\b[a-z][a-z0-9\-]{3,}\b", summary.lower() + " " + description_text.lower())
    keywords = list(set([w for w in words if w not in ("that", "this", "with", "from", "have", "para", "como", "deve", "pelo", "pela", "está", "menu", "logo", "card", "jira", "side", "left", "right", "when", "only", "mais", "item", "list", "show", "hide", "view", "open")]))[:8]

    print(f"\n[3/5] Coletando código React (Replit)...")
    react_files_content = {}

    specific_react = list(args.react_file)
    if not specific_react:
        specific_react = [f for f in mentioned_files if f.endswith((".tsx", ".ts", ".py")) and not f.endswith(".vue")]

    if specific_react:
        for f in specific_react[:4]:
            content, err = read_local_file(f)
            if content:
                react_files_content[f] = content
                print(f"  ✓ {f} ({len(content)} chars)")
            else:
                print(f"  ✗ {f}: {err}")

    if not react_files_content:
        found = find_local_files_by_keyword(keywords[:5])
        for f in found[:4]:
            content, err = read_local_file(f)
            if content:
                react_files_content[f] = content
                print(f"  ✓ {f} (auto-detectado, {len(content)} chars)")

    if not react_files_content:
        print("  ⚠ Nenhum arquivo React encontrado automaticamente")

    print(f"\n[4/5] Coletando código Vue (GitHub WeDOTalent)...")
    vue_files_content = {}

    specific_vue = list(args.vue_file)
    if not specific_vue and mentioned_vue:
        specific_vue = mentioned_vue[:2]

    if specific_vue:
        for vf in specific_vue:
            content, err = fetch_github_file(vf)
            if content:
                vue_files_content[vf] = content
                print(f"  ✓ {vf} ({len(content)} chars)")
            else:
                print(f"  ✗ {vf}: {err}")

    if not vue_files_content:
        for kw in keywords[:3]:
            results = search_github_file(kw)
            for path in results:
                if path.endswith(".vue") and path not in vue_files_content:
                    content, err = fetch_github_file(path)
                    if content:
                        vue_files_content[path] = content
                        print(f"  ✓ {path} (auto-detectado, {len(content)} chars)")
                        break
            if vue_files_content:
                break

    if not vue_files_content:
        print("  ⚠ Nenhum arquivo Vue encontrado automaticamente")

    print(f"\n[5/5] Analisando com Claude...")
    analysis = analyze_with_claude(issue_key, summary, description_text, react_files_content, vue_files_content)
    print(f"✓ Análise gerada")
    print(f"  {len(analysis.get('secoes_tecnicas', []))} seções técnicas")
    print(f"  {len(analysis.get('criterios_de_aceite', []))} critérios de aceite")
    print(f"  {len(analysis.get('action_items', []))} action items")

    adf = build_adf(analysis, issue_key, summary)

    if args.dry_run:
        print("\n[DRY RUN] Descrição gerada (não enviada ao Jira):")
        print(json.dumps(analysis, indent=2, ensure_ascii=False)[:2000])
        print(f"\n✅ DRY RUN concluído. Remova --dry-run para publicar no Jira.")
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
