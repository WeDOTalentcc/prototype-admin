"""
Bug Spec Generator — Jira I/O (Jam · Userback · BetterBugs · manual)

Dois comandos simples para enriquecer cards do Jira com spec técnica.
A geração de conteúdo (complemento + spec técnica) acontece no chat com
o agente LIA — este script faz apenas o I/O com o Jira.

Detecta automaticamente a origem do card:
  • Jam.dev       — separador "---..." + link jam.dev
  • Userback      — bloco "--- Metadata ---" + Session Link
  • BetterBugs    — link betterbugs.io na descrição
  • Manual        — sem padrão reconhecível

Configuração (adicione ao .env ou exporte no shell):
    JIRA_EMAIL       = email da conta Atlassian (ex: admin@wedotalent.com)
    JIRA_API_TOKEN   = token gerado em https://id.atlassian.com/manage-api-tokens
    JIRA_CLOUD_ID    = 8cf762f8-6a44-47de-8915-6b3dc0cd2715  (já preenchido)
    JIRA_PROJECT     = WT  (já preenchido)

Uso:
    # 1. Busca o card e imprime template pré-preenchido
    python scripts/bug_spec_generator.py fetch WT-1631

    # 2. Posta o complemento gerado (de arquivo ou stdin)
    python scripts/bug_spec_generator.py post WT-1631 --from-file /tmp/spec-WT-1631.md
    python scripts/bug_spec_generator.py post WT-1631               # lê do stdin

    # Pré-visualiza sem postar
    python scripts/bug_spec_generator.py post WT-1631 --dry-run --from-file spec.md

    # Salva saída do fetch em arquivo
    python scripts/bug_spec_generator.py fetch WT-1631 --output-file /tmp/card.md
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError:
    sys.exit("❌  Instale o pacote requests: pip install requests")


CLOUD_ID   = os.getenv("JIRA_CLOUD_ID", "8cf762f8-6a44-47de-8915-6b3dc0cd2715")
_JIRA_BASE_DEFAULT = f"https://api.atlassian.com/ex/jira/{CLOUD_ID}/rest/api/3"
TODAY = datetime.now(timezone.utc).strftime("%d/%m/%Y")

# Separadores por ferramenta
JAM_SEPARATOR        = "-------------------------------------"
USERBACK_SEPARATOR   = "--- Metadata ---"


# ─────────────────────────────────────────────────────────────────────────────
# Auth — ordem de prioridade:
#   1. Replit connector OAuth2 (REPLIT_CONNECTORS_HOSTNAME + REPL_IDENTITY)
#   2. Bearer token manual   (JIRA_TOKEN)
#   3. Basic auth            (JIRA_EMAIL + JIRA_API_TOKEN)
# ─────────────────────────────────────────────────────────────────────────────

def _get_auth() -> tuple[dict[str, str], str]:
    """Retorna (headers, jira_base_url) resolvendo credenciais pela ordem de prioridade."""

    # ── 1. Replit connector OAuth2 ───────────────────────────────────────────
    connector_host = os.getenv("REPLIT_CONNECTORS_HOSTNAME", "")
    repl_identity  = os.getenv("REPL_IDENTITY", "")
    web_renewal    = os.getenv("WEB_REPL_RENEWAL", "")

    if connector_host:
        x_replit_token = (
            f"repl {repl_identity}" if repl_identity
            else f"depl {web_renewal}" if web_renewal
            else ""
        )
        if x_replit_token:
            try:
                resp = requests.get(
                    f"https://{connector_host}/api/v2/connection",
                    params={"include_secrets": "true", "connector_names": "jira"},
                    headers={"Accept": "application/json", "X-Replit-Token": x_replit_token},
                    timeout=10,
                )
                if resp.ok:
                    item     = (resp.json().get("items") or [{}])[0]
                    settings = item.get("settings", {})
                    token    = (
                        settings.get("access_token")
                        or (settings.get("oauth") or {}).get("credentials", {}).get("access_token")
                    )
                    if token:
                        # O token OAuth do conector funciona via api.atlassian.com (não via site_url direto)
                        headers = {
                            "Authorization": f"Bearer {token}",
                            "Accept":        "application/json",
                            "Content-Type":  "application/json",
                        }
                        return headers, _JIRA_BASE_DEFAULT
            except Exception:
                pass  # cai para o próximo método

    # ── 2. Bearer token manual ───────────────────────────────────────────────
    token = os.getenv("JIRA_TOKEN", "")
    if token:
        return (
            {
                "Authorization": f"Bearer {token}",
                "Accept":        "application/json",
                "Content-Type":  "application/json",
            },
            _JIRA_BASE_DEFAULT,
        )

    # ── 3. Basic auth ────────────────────────────────────────────────────────
    email     = os.getenv("JIRA_EMAIL", "")
    api_token = os.getenv("JIRA_API_TOKEN", "")
    if email and api_token:
        creds = base64.b64encode(f"{email}:{api_token}".encode()).decode()
        return (
            {
                "Authorization": f"Basic {creds}",
                "Accept":        "application/json",
                "Content-Type":  "application/json",
            },
            _JIRA_BASE_DEFAULT,
        )

    sys.exit(
        "❌  Credenciais Jira não encontradas.\n"
        "    Opções (em ordem de prioridade):\n"
        "      1. Conector Replit OAuth2 — configure REPLIT_CONNECTORS_HOSTNAME no ambiente\n"
        "      2. JIRA_TOKEN=<oauth_bearer_token>\n"
        "      3. JIRA_EMAIL=seu@email.com + JIRA_API_TOKEN=<api_token>\n"
        "         (token em https://id.atlassian.com/manage-api-tokens)"
    )


def _get(path: str, params: dict | None = None) -> dict:
    headers, jira_base = _get_auth()
    resp = requests.get(f"{jira_base}{path}", headers=headers, params=params, timeout=15)
    if not resp.ok:
        sys.exit(f"❌  Jira API erro {resp.status_code}: {resp.text[:300]}")
    return resp.json()


def _post_json(path: str, body: dict) -> dict:
    headers, jira_base = _get_auth()
    resp = requests.post(f"{jira_base}{path}", headers=headers, json=body, timeout=15)
    if not resp.ok:
        sys.exit(f"❌  Jira API erro {resp.status_code}: {resp.text[:400]}")
    return resp.json()


def _put_json(path: str, body: dict) -> dict:
    headers, jira_base = _get_auth()
    resp = requests.put(f"{jira_base}{path}", headers=headers, json=body, timeout=15)
    if not resp.ok:
        sys.exit(f"❌  Jira API erro {resp.status_code}: {resp.text[:400]}")
    return resp.json()


def _build_headers() -> dict[str, str]:
    """Retrocompatibilidade — retorna apenas os headers (sem base_url)."""
    headers, _ = _get_auth()
    return headers


# ─────────────────────────────────────────────────────────────────────────────
# Description parser — multi-tool (Jam · Userback · BetterBugs · manual)
# ─────────────────────────────────────────────────────────────────────────────

def _adf_to_text(node: dict) -> str:
    if not node:
        return ""
    parts: list[str] = []
    if node.get("type") == "text":
        parts.append(node.get("text", ""))
    if node.get("type") == "hardBreak":
        parts.append("\n")
    for child in node.get("content", []):
        parts.append(_adf_to_text(child))
    if node.get("type") in ("paragraph", "heading", "listItem"):
        parts.append("\n")
    return "".join(parts)


def _extract_after(label: str, text: str) -> str:
    m = re.search(
        rf"{re.escape(label)}\s*[:\-]?\s*\n?\s*(.+?)(?=\n[A-Za-z\-]|\n\n|\Z)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    return m.group(1).strip() if m else ""


def _detect_source(raw: str) -> str:
    """Identifica a ferramenta que criou o card com base no conteúdo da descrição."""
    if JAM_SEPARATOR in raw and re.search(r"jam\.dev", raw, re.IGNORECASE):
        return "Jam.dev"
    if USERBACK_SEPARATOR in raw or re.search(r"userback\.io", raw, re.IGNORECASE):
        return "Userback"
    if re.search(r"betterbugs\.io", raw, re.IGNORECASE):
        return "BetterBugs"
    return "Manual"


def _parse_bug_description(adf: dict) -> dict[str, str]:
    """Parseia a descrição do card e extrai metadados independentemente da ferramenta."""
    raw = _adf_to_text(adf).strip()

    result: dict[str, str] = {
        "source": "Manual",
        "user_notes": raw,
        "page_url": "",
        "device_info": "",
        "date_reported": "",
        "console_logs": "Não registrado",
        "network_requests": "Não registrado",
        "ref_link": "",
    }

    source = _detect_source(raw)
    result["source"] = source

    # ── Jam.dev ──────────────────────────────────────────────────────────────
    if source == "Jam.dev":
        parts = raw.split(JAM_SEPARATOR, 1)
        result["user_notes"] = parts[0].strip()
        meta = parts[1]

        result["page_url"]      = _extract_after("Website URL", meta)
        result["device_info"]   = _extract_after("Device and browser info", meta)
        result["date_reported"] = _extract_after("Date and time", meta)

        dev_link_m = re.search(
            r"developer information.*?\n(jam\.dev/\S+|https://jam\.dev/\S+)", meta
        )
        if dev_link_m:
            link = dev_link_m.group(1).strip()
            if not link.startswith("http"):
                link = "https://" + link
            result["ref_link"]           = link
            result["console_logs"]       = f"Ver {link}"
            result["network_requests"]   = f"Ver {link}"

    # ── Userback ─────────────────────────────────────────────────────────────
    elif source == "Userback":
        if USERBACK_SEPARATOR in raw:
            parts = raw.split(USERBACK_SEPARATOR, 1)
            result["user_notes"] = parts[0].strip()
            meta = parts[1]
        else:
            meta = raw

        result["device_info"]   = _extract_after("Browser", meta)
        result["page_url"]      = _extract_after("URL", meta)

        screen_m = re.search(r"Screen[:\s]+(\d+x\d+)", meta, re.IGNORECASE)
        if screen_m:
            result["device_info"] += f" | Resolução: {screen_m.group(1)}"

        session_m = re.search(
            r"Session Link[:\s]+(https://\S+userback\S*)", meta, re.IGNORECASE
        )
        if session_m:
            result["ref_link"] = session_m.group(1)

        feedback_m = re.search(r"Feedback ID[:\s]+(\S+)", meta, re.IGNORECASE)
        if feedback_m:
            result["date_reported"] = f"ID {feedback_m.group(1)}"

        console_m = re.search(
            r"Console Logs[:\s]+(https://\S+)", meta, re.IGNORECASE
        )
        if console_m:
            result["console_logs"] = f"Ver {console_m.group(1)}"

    # ── BetterBugs ────────────────────────────────────────────────────────────
    elif source == "BetterBugs":
        bb_m = re.search(r"(https://app\.betterbugs\.io/\S+)", raw, re.IGNORECASE)
        if bb_m:
            result["ref_link"] = bb_m.group(1)
            result["console_logs"]     = f"Ver {bb_m.group(1)}"
            result["network_requests"] = f"Ver {bb_m.group(1)}"

        device_m = re.search(r"(Browser|Device)[:\s]+([^\n]+)", raw, re.IGNORECASE)
        if device_m:
            result["device_info"] = device_m.group(2).strip()

    return result


# Manter compatibilidade retroativa com código legado
def _parse_jam_description(adf: dict) -> dict[str, str]:
    parsed = _parse_bug_description(adf)
    parsed["jam_dev_link"] = parsed.get("ref_link", "")
    parsed["date_jam"]     = parsed.get("date_reported", "")
    return parsed


def _format_date(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y às %H:%M UTC")
    except Exception:
        return iso


# ─────────────────────────────────────────────────────────────────────────────
# FETCH command
# ─────────────────────────────────────────────────────────────────────────────

_TEMPLATE = """\
-------------------------------------
📋 Complemento — Revisão de Produto ({date})

**Metadados do Card**
- Tipo: [PREENCHER: Bug | Melhoria UX | Task | Spike]
- Área: [PREENCHER: Frontend | Backend | Full-Stack | Infra | DS]
- Pontos de Esforço: [PREENCHER: 1-2-3-5-8-13]
- Prioridade: {priority}
- Sprint: A definir
- Tags: [PREENCHER: lista separada por vírgula — ex: bug, ux, email, ds, jam]

**🔗 Referência ({source})**
- Link: {ref_link}
- Tipo de Registro: {record_type}
- Criado por: {reporter} em {created}
- Título Original: "{summary}"

**Descrição do Problema (Estruturada)**
[PREENCHER — baseado nos pontos acima, numerados e objetivos]

**Comportamento Esperado (Proposto)**
[PREENCHER — o que deveria acontecer após a correção]

**Regras de Negócio Impactadas**
[PREENCHER — ex: nomenclatura LIA, design system, legalidade, fluxo do candidato]

**Informações Técnicas**
- Console Logs: {console_logs}
- Network Requests: {network_requests}
- Page URL: {page_url}
- Metadados: {device_info}

**Definition of Done (DoD)**
- [ ] [PREENCHER]
- [ ] Testes visuais aprovados no Figma/produto
- [ ] Revisão de acessibilidade (contraste, foco, aria-label)
- [ ] PR aprovado e merge na branch de desenvolvimento

**Critérios de Aceitação**
- [PREENCHER]

---
🔧 **Spec Técnica — LIA Design System v4.2.1**
[PREENCHER — após análise da screenshot e do DS:
  • Tokens incorretos vs tokens corretos (cores, tipografia, espaçamento)
  • Equivalência Vue + Vuetify (v-btn, v-card, etc.)
  • Componente(s) afetado(s) no produto real
  • Regra 90/10 monocromático aplicada?
  • Cyan = uso exclusivo LIA — aplicado corretamente?]
-------------------------------------"""


def cmd_fetch(args: argparse.Namespace) -> None:
    card_key = args.card.upper()
    print(f"\n🔍 Buscando {card_key} no Jira...\n")

    fields = "summary,description,labels,priority,status,reporter,assignee,attachment,created"
    data = _get(f"/issue/{card_key}", {"fields": fields})
    f = data["fields"]

    summary     = f.get("summary", "")
    priority    = f.get("priority", {}).get("name", "Não definida")
    reporter    = (f.get("reporter") or {}).get("displayName", "Não informado")
    created     = _format_date(f.get("created", ""))
    labels      = f.get("labels", [])
    attachments = f.get("attachment", [])
    status      = (f.get("status") or {}).get("name", "")
    adf_desc    = f.get("description") or {}

    bug_info = _parse_bug_description(adf_desc)
    source   = bug_info["source"]

    screenshot_path = ""
    image_attachments = [a for a in attachments if (a.get("mimeType") or "").startswith("image/")]
    if image_attachments:
        att = image_attachments[0]
        screenshot_path = f"/tmp/jam_screenshot_{card_key}.png"
        dl_resp = requests.get(
            att["content"], headers=_build_headers(), timeout=30, stream=True
        )
        if dl_resp.ok:
            Path(screenshot_path).write_bytes(dl_resp.content)

    record_type = "Screenshot" if image_attachments else "Bug Report (sem imagem)"

    ref_link = bug_info.get("ref_link") or (
        "[PREENCHER: URL do registro no Jam.dev]" if source == "Jam.dev"
        else f"[PREENCHER: link da sessão {source}]"
    )

    template = _TEMPLATE.format(
        date=TODAY,
        priority=priority,
        reporter=reporter,
        created=created,
        summary=summary,
        source=source,
        record_type=record_type,
        ref_link=ref_link,
        page_url=bug_info["page_url"] or "[não registrado]",
        device_info=bug_info["device_info"] or "[não registrado]",
        console_logs=bug_info["console_logs"],
        network_requests=bug_info["network_requests"],
    )

    header = (
        f"{'━' * 60}\n"
        f"📋  {card_key} — {summary}\n"
        f"{'━' * 60}\n"
        f"Origem    : {source}\n"
        f"Reporter  : {reporter}\n"
        f"Criado em : {created}\n"
        f"Status    : {status}  |  Prioridade: {priority}\n"
        f"Labels    : {', '.join(labels) if labels else '(nenhuma)'}\n"
    )

    if screenshot_path and Path(screenshot_path).exists():
        header += f"📸 Screenshot: {screenshot_path}\n"
    else:
        header += "📸 Screenshot: não encontrada nos anexos do card\n"

    header += (
        f"\n{'─' * 60}\n"
        f"DESCRIÇÃO BRUTA\n"
        f"{'─' * 60}\n"
        f"{_adf_to_text(adf_desc).strip()}\n"
    )

    if bug_info["page_url"] or bug_info["ref_link"] or bug_info["device_info"]:
        header += (
            f"\n{'─' * 60}\n"
            f"METADADOS EXTRAÍDOS ({source})\n"
            f"{'─' * 60}\n"
            f"Page URL    : {bug_info['page_url'] or '—'}\n"
            f"Device      : {bug_info['device_info'] or '—'}\n"
            f"Data/ID     : {bug_info['date_reported'] or '—'}\n"
            f"Link Ref    : {bug_info['ref_link'] or '—'}\n"
        )

    header += (
        f"\n{'━' * 60}\n"
        f"TEMPLATE DO COMPLEMENTO — copie, preencha e envie no chat\n"
        f"{'━' * 60}\n\n"
    )

    output = header + template + (
        f"\n\n{'─' * 60}\n"
        f"💡 Próximos passos:\n"
        f"   1. Compartilhe este output + a screenshot no chat com o agente\n"
        f"   2. O agente vai preencher o template completo\n"
        f"   3. Cole a resposta num arquivo: spec-{card_key}.md\n"
        f"   4. Rode: python scripts/bug_spec_generator.py post {card_key} --from-file spec-{card_key}.md\n"
        f"{'─' * 60}\n"
    )

    if args.output_file:
        Path(args.output_file).write_text(output, encoding="utf-8")
        print(output)
        print(f"\n✅  Output salvo em: {args.output_file}")
    else:
        print(output)


# ─────────────────────────────────────────────────────────────────────────────
# Markdown → ADF converter
# ─────────────────────────────────────────────────────────────────────────────

def _text_node(text: str, bold: bool = False) -> dict:
    node: dict[str, Any] = {"type": "text", "text": text}
    if bold:
        node["marks"] = [{"type": "strong"}]
    return node


def _parse_inline(line: str) -> list[dict]:
    nodes: list[dict] = []
    pattern = r"\*\*(.+?)\*\*"
    last = 0
    for m in re.finditer(pattern, line):
        if m.start() > last:
            nodes.append(_text_node(line[last:m.start()]))
        nodes.append(_text_node(m.group(1), bold=True))
        last = m.end()
    if last < len(line):
        nodes.append(_text_node(line[last:]))
    return nodes or [_text_node(line)]


def _md_to_adf(text: str) -> dict:
    content: list[dict] = []
    lines = text.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped == "---" or stripped == "-------------------------------------":
            content.append({"type": "rule"})
            i += 1
            continue

        if stripped.startswith("## "):
            content.append({
                "type": "heading",
                "attrs": {"level": 2},
                "content": _parse_inline(stripped[3:]),
            })
            i += 1
            continue

        if stripped.startswith("# "):
            content.append({
                "type": "heading",
                "attrs": {"level": 1},
                "content": _parse_inline(stripped[2:]),
            })
            i += 1
            continue

        if stripped.startswith("- [ ] ") or stripped.startswith("- [x] "):
            task_nodes: list[dict] = []
            while i < len(lines):
                s = lines[i].strip()
                if not (s.startswith("- [ ] ") or s.startswith("- [x] ")):
                    break
                done = s.startswith("- [x] ")
                item_text = s[6:]
                task_nodes.append({
                    "type": "taskItem",
                    "attrs": {
                        "localId": str(uuid.uuid4()),
                        "state": "DONE" if done else "TODO",
                    },
                    "content": [{"type": "paragraph", "content": _parse_inline(item_text)}],
                })
                i += 1
            content.append({
                "type": "taskList",
                "attrs": {"localId": str(uuid.uuid4())},
                "content": task_nodes,
            })
            continue

        if stripped.startswith("- "):
            bullet_nodes: list[dict] = []
            while i < len(lines):
                s = lines[i].strip()
                if not s.startswith("- "):
                    break
                item_text = s[2:]
                bullet_nodes.append({
                    "type": "listItem",
                    "content": [{"type": "paragraph", "content": _parse_inline(item_text)}],
                })
                i += 1
            content.append({"type": "bulletList", "content": bullet_nodes})
            continue

        if re.match(r"^\d+\.\s", stripped):
            ordered_nodes: list[dict] = []
            while i < len(lines):
                s = lines[i].strip()
                if not re.match(r"^\d+\.\s", s):
                    break
                item_text = re.sub(r"^\d+\.\s+", "", s)
                ordered_nodes.append({
                    "type": "listItem",
                    "content": [{"type": "paragraph", "content": _parse_inline(item_text)}],
                })
                i += 1
            content.append({"type": "orderedList", "content": ordered_nodes})
            continue

        if stripped == "":
            content.append({"type": "paragraph", "content": []})
            i += 1
            continue

        content.append({"type": "paragraph", "content": _parse_inline(stripped)})
        i += 1

    return {"type": "doc", "version": 1, "content": content}


# ─────────────────────────────────────────────────────────────────────────────
# Tags extractor
# ─────────────────────────────────────────────────────────────────────────────

def _extract_tags(text: str) -> list[str]:
    m = re.search(r"- Tags:\s*(.+)", text)
    if not m:
        return []
    raw = m.group(1)
    if "[PREENCHER" in raw:
        return []
    tags = [t.strip().lower().replace(" ", "-") for t in raw.split(",") if t.strip()]
    return [t for t in tags if t and "[" not in t]


# ─────────────────────────────────────────────────────────────────────────────
# POST command
# ─────────────────────────────────────────────────────────────────────────────

def cmd_post(args: argparse.Namespace) -> None:
    card_key = args.card.upper()

    if args.from_file:
        content_path = Path(args.from_file)
        if not content_path.exists():
            sys.exit(f"❌  Arquivo não encontrado: {args.from_file}")
        spec_text = content_path.read_text(encoding="utf-8")
    else:
        print("📋  Cole o conteúdo gerado e pressione Ctrl+D para finalizar:")
        spec_text = sys.stdin.read()

    if not spec_text.strip():
        sys.exit("❌  Conteúdo vazio — nada para postar.")

    tags = _extract_tags(spec_text)
    adf_body = _md_to_adf(spec_text)

    if args.dry_run:
        print(f"\n{'━' * 60}")
        print(f"DRY RUN — {card_key}")
        print(f"{'━' * 60}")
        print(f"\nTags a aplicar: {tags or '(nenhuma)'}\n")
        print("Corpo ADF (resumo):")
        print(json.dumps(adf_body, ensure_ascii=False, indent=2)[:2000])
        print(f"\n{'─' * 60}")
        print("✅  Dry run concluído. Rode sem --dry-run para postar.")
        return

    print(f"\n📤  Postando comentário em {card_key}...")
    comment_payload = {"body": adf_body}
    result = _post_json(f"/issue/{card_key}/comment", comment_payload)
    comment_url = (
        f"https://wedotalent.atlassian.net/browse/{card_key}"
        f"?focusedCommentId={result.get('id', '')}"
    )
    print(f"✅  Comentário postado: {comment_url}")

    if tags:
        print(f"\n🏷️   Aplicando tags: {tags}")
        current = _get(f"/issue/{card_key}", {"fields": "labels"})
        current_labels = current["fields"].get("labels", [])
        merged = sorted(set(current_labels) | set(tags))
        _put_json(f"/issue/{card_key}", {"fields": {"labels": merged}})
        print(f"✅  Labels atualizadas: {merged}")

    print(f"\n🔗  Card: https://wedotalent.atlassian.net/browse/{card_key}\n")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="bug_spec_generator",
        description=(
            "Bug Spec Generator — Jira I/O para enriquecimento de cards Jam → Jira.\n"
            "A geração de conteúdo acontece no chat com o agente LIA."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_fetch = sub.add_parser(
        "fetch",
        help="Busca o card Jira e imprime template pré-preenchido.",
    )
    p_fetch.add_argument("card", metavar="CARD_KEY", help="Ex: WT-1631")
    p_fetch.add_argument(
        "--output-file",
        metavar="PATH",
        help="Salva o output em arquivo (além de imprimir no terminal).",
    )

    p_post = sub.add_parser(
        "post",
        help="Posta o complemento gerado no Jira e aplica as tags.",
    )
    p_post.add_argument("card", metavar="CARD_KEY", help="Ex: WT-1631")
    p_post.add_argument(
        "--from-file",
        metavar="PATH",
        help="Lê o conteúdo de um arquivo .md (padrão: stdin).",
    )
    p_post.add_argument(
        "--dry-run",
        action="store_true",
        help="Imprime o que seria postado sem enviar ao Jira.",
    )

    args = parser.parse_args()

    if args.command == "fetch":
        cmd_fetch(args)
    elif args.command == "post":
        cmd_post(args)


if __name__ == "__main__":
    main()
