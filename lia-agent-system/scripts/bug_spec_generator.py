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
# GitHub — leitura do código Vue real (WeDOTalent/ats_front)
# Fonte da verdade: branch develop do repositório de produção Vue/Vuetify
# ─────────────────────────────────────────────────────────────────────────────

GITHUB_REPO   = "WeDOTalent/ats_front"
GITHUB_BRANCH = "develop"
_GH_API       = "https://api.github.com"
_gh_tree_cache_bug: list | None = None


def _github_token() -> str:
    """Retorna o PAT do GitHub configurado como secret no Replit."""
    return os.getenv("GITHUB_PAT_WEDOTALENT", "")


def _github_file(path: str, ref: str = GITHUB_BRANCH) -> str:
    """Lê um arquivo do repositório Vue via GitHub API. Retorna '' se não encontrado."""
    token = _github_token()
    if not token:
        return ""
    try:
        import base64 as _b64
        resp = requests.get(
            f"{_GH_API}/repos/{GITHUB_REPO}/contents/{path}",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"},
            params={"ref": ref},
            timeout=15,
        )
        if resp.ok:
            data = resp.json()
            if isinstance(data, dict) and data.get("content"):
                return _b64.b64decode(data["content"]).decode("utf-8", errors="replace")
    except Exception:
        pass
    return ""


def _github_tree(ref: str = GITHUB_BRANCH) -> list[str]:
    """Lista todos os arquivos Vue + TS do repositório (com cache)."""
    global _gh_tree_cache_bug
    if _gh_tree_cache_bug is not None:
        return _gh_tree_cache_bug
    token = _github_token()
    if not token:
        return []
    try:
        resp = requests.get(
            f"{_GH_API}/repos/{GITHUB_REPO}/git/trees/{ref}",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"},
            params={"recursive": "1"},
            timeout=20,
        )
        if resp.ok:
            files = [
                f["path"] for f in resp.json().get("tree", [])
                if f.get("type") == "blob"
                and (f["path"].endswith(".vue") or f["path"].endswith(".ts"))
            ]
            _gh_tree_cache_bug = files
            return files
    except Exception:
        pass
    _gh_tree_cache_bug = []
    return []


def _find_vue_files_for_url(page_url: str, keywords: list[str], max_results: int = 4) -> list[str]:
    """Encontra arquivos Vue relevantes dado uma URL e keywords do card."""
    all_files = _github_tree()
    if not all_files:
        return []
    # Extrai path segments da URL para usar como keywords adicionais
    url_parts = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", page_url or "")
    search_kw = [k.lower() for k in (keywords + url_parts)]
    scored: list[tuple[int, str]] = []
    for path in all_files:
        score = sum(1 for kw in search_kw if kw in path.lower())
        if score > 0:
            scored.append((score, path))
    scored.sort(key=lambda x: -x[0])
    return [p for _, p in scored[:max_results]]


def _vue_code_preview(vue_files: list[str], max_lines_per_file: int = 40) -> str:
    """Lê arquivos Vue e retorna preview do código prod atual para o template."""
    if not vue_files or not _github_token():
        return "[GITHUB_PAT_WEDOTALENT nao configurado — adicionar manualmente]"
    parts: list[str] = []
    for path in vue_files[:3]:
        content = _github_file(path)
        if not content:
            continue
        lines = content.splitlines()
        # Pega primeiras linhas do <template> block — mais revelador do UI
        template_start = next((i for i, l in enumerate(lines) if "<template>" in l), 0)
        snippet = lines[template_start: template_start + max_lines_per_file]
        parts.append(f"// {GITHUB_REPO}/{path}\n" + "\n".join(snippet))
    return "\n\n".join(parts) if parts else "[arquivo nao encontrado no GitHub]"


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
            except Exception as exc:
                print(f"⚠️  Conector Replit Jira falhou ({exc}), tentando fallback de auth...", file=sys.stderr)

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
    # PUT /issue retorna 204 No Content — corpo vazio é esperado
    if resp.status_code == 204 or not resp.content:
        return {}
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


# ─────────────────────────────────────────────────────────────────────────────
# BetterBugs — extração de mídia e links embutidos no ADF do card Jira
# ─────────────────────────────────────────────────────────────────────────────

def _extract_adf_media_and_links(node: dict, _acc: dict | None = None) -> dict:
    """Percorre o ADF recursivamente e coleta:
    - screenshots embedadas como `mediaSingle` / `media` external (CDN BetterBugs)
    - links de texto (marks do tipo "link") — classifica sessão, console, rede, source
    - inlineCards (smart links Jira)
    Retorna dict com chaves: screenshots, links, betterbugs_session,
    source_url, console_logs_url, network_logs_url, inline_cards.
    """
    if _acc is None:
        _acc = {
            "screenshots":        [],
            "links":              [],
            "inline_cards":       [],
            "betterbugs_session": None,
            "source_url":         None,
            "console_logs_url":   None,
            "network_logs_url":   None,
        }
    if not node:
        return _acc

    ntype = node.get("type", "")

    # Screenshot embarcada como nó media external (CDN BetterBugs / Jira)
    if ntype == "media":
        attrs = node.get("attrs", {})
        if attrs.get("type") == "external":
            url = attrs.get("url", "")
            if url and url not in _acc["screenshots"]:
                _acc["screenshots"].append(url)

    # Smart link / inline card
    if ntype == "inlineCard":
        url = node.get("attrs", {}).get("url", "")
        if url and url not in _acc["inline_cards"]:
            _acc["inline_cards"].append(url)

    # Links em marks de texto — classifica por padrão de URL
    for mark in node.get("marks", []):
        if mark.get("type") == "link":
            href = mark.get("attrs", {}).get("href", "")
            text = node.get("text", "")
            if href and not href.startswith("mailto:"):
                entry = {"text": text, "href": href}
                if entry not in _acc["links"]:
                    _acc["links"].append(entry)
                if re.search(r"betterbugs\.io/session/[^?]+$", href):
                    _acc["betterbugs_session"] = href
                elif "openedDevTab=console" in href:
                    _acc["console_logs_url"] = href
                elif "openedDevTab=network" in href:
                    _acc["network_logs_url"] = href
                elif ("wedotalent" in href or "replit" in href) and not _acc["source_url"]:
                    _acc["source_url"] = href

    for child in node.get("content", []):
        _extract_adf_media_and_links(child, _acc)

    return _acc


def _download_betterbugs_screenshots(adf: dict, card_key: str = "") -> list[str]:
    """Baixa as screenshots BetterBugs embedadas no ADF para /tmp.
    Retorna lista de caminhos locais salvos."""
    extracted = _extract_adf_media_and_links(adf)
    local_paths: list[str] = []
    for i, url in enumerate(extracted["screenshots"]):
        try:
            r = requests.get(url, timeout=15)
            if r.ok:
                ext = url.split(".")[-1].split("?")[0] or "png"
                ext = ext[:4]
                slug = f"_{card_key}" if card_key else ""
                path = f"/tmp/bb_screenshot{slug}_{i+1}.{ext}"
                Path(path).write_bytes(r.content)
                local_paths.append(path)
        except Exception:
            pass
    return local_paths


# ─────────────────────────────────────────────────────────────────────────────
# BetterBugs REST API — busca dados completos da sessão (vídeo, prints, logs)
# Requer: BETTERBUGS_API_KEY no ambiente
# API base: https://butterfly-api.betterbugs.io
# ─────────────────────────────────────────────────────────────────────────────

_BB_API_BASE = "https://butterfly-api.betterbugs.io"
_BB_CDN_BASE = "https://cdn-butterfly-new.betterbugs.io"


def _betterbugs_api_token() -> str:
    return os.getenv("BETTERBUGS_API_KEY", "")


def _betterbugs_fetch_session(session_url: str) -> dict:
    """Busca dados completos da sessão BetterBugs via REST API.

    Extrai o sessionId da URL (https://app.betterbugs.io/session/<id>),
    tenta os endpoints conhecidos com autenticação via BETTERBUGS_API_KEY.

    Retorna dict com:
        video_url       — URL do vídeo de gravação (mp4/webm)
        screenshots     — lista de URLs de screenshots da sessão
        console_logs    — lista de entradas do console
        network_logs    — lista de requests de rede
        session_id      — id da sessão
        raw             — payload bruto da API
    Se a chave não está configurada ou a API falha, retorna dict vazio.
    """
    token = _betterbugs_api_token()
    result: dict = {
        "video_url":    None,
        "screenshots":  [],
        "console_logs": [],
        "network_logs": [],
        "session_id":   None,
        "raw":          {},
    }

    # Extrai sessionId da URL
    sid_match = re.search(r"/session/([a-f0-9]{24,})", session_url or "")
    if not sid_match:
        return result
    session_id = sid_match.group(1)
    result["session_id"] = session_id

    if not token:
        return result

    # Cabeçalhos de auth — BetterBugs aceita x-api-key e/ou Authorization Bearer
    headers = {
        "x-api-key":     token,
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }

    # Endpoints a tentar (em ordem de probabilidade)
    endpoints = [
        f"{_BB_API_BASE}/recording-link/{session_id}",
        f"{_BB_API_BASE}/sessions/{session_id}",
        f"{_BB_API_BASE}/bugs/{session_id}",
        f"{_BB_API_BASE}/v1/recording-link/{session_id}",
        f"{_BB_API_BASE}/v1/sessions/{session_id}",
    ]

    data: dict = {}
    for url in endpoints:
        try:
            resp = requests.get(url, headers=headers, timeout=12)
            if resp.ok:
                data = resp.json()
                result["raw"] = data
                break
            elif resp.status_code == 401:
                print("    ⚠️  BetterBugs API: autenticação falhou (401) — verifique BETTERBUGS_API_KEY")
                return result
        except Exception:
            continue

    if not data:
        return result

    # Extrai vídeo — campo screenRecording.url (caminho relativo no CDN)
    screen_rec = data.get("screenRecording") or data.get("screen_recording") or {}
    if isinstance(screen_rec, dict):
        vid_path = screen_rec.get("url", "")
        if vid_path:
            result["video_url"] = vid_path

    # Extrai screenshots adicionais
    for field in ("screenshots", "images", "attachments"):
        items = data.get(field, [])
        if isinstance(items, list):
            for item in items:
                url = item.get("url") or item.get("src") or (item if isinstance(item, str) else "")
                if url and url not in result["screenshots"]:
                    result["screenshots"].append(url)

    # Extrai console logs
    for field in ("consoleLogs", "console_logs", "devLogs"):
        logs = data.get(field, [])
        if isinstance(logs, list):
            result["console_logs"] = logs[:50]
            break

    # Extrai network logs
    for field in ("networkLogs", "network_logs", "networkRequests"):
        logs = data.get(field, [])
        if isinstance(logs, list):
            result["network_logs"] = logs[:30]
            break

    return result


def _betterbugs_download_video(video_url: str, card_key: str = "") -> str | None:
    """Baixa o vídeo BetterBugs para /tmp. Retorna o caminho local ou None."""
    if not video_url:
        return None
    try:
        r = requests.get(video_url, timeout=30, stream=True)
        if r.ok:
            ext = "mp4" if "mp4" in video_url else "webm"
            slug = f"_{card_key}" if card_key else ""
            path = f"/tmp/bb_video{slug}.{ext}"
            with open(path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            return path
    except Exception:
        pass
    return None


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
Complemento — Revisão de Produto ({date})

**Metadados do Card**
- Tipo: [PREENCHER: Bug | Melhoria UX | Task | Spike]
- Área: [PREENCHER: Frontend | Backend | Full-Stack | Infra | DS]
- Pontos de Esforço: [PREENCHER: 1-2-3-5-8-13]
- Prioridade: {priority}
- Sprint: A definir
- Tags: [PREENCHER: lista separada por vírgula — ex: bug, ux, ds, vuetify, betterbugs]

**Referência ({source})**
- Link: {ref_link}
- Tipo de Registro: {record_type}
- Criado por: {reporter} em {created}
- Título Original: "{summary}"

**Descrição do Problema (Estruturada)**
[PREENCHER — numerado, objetivo, baseado na descrição original]

**Comportamento Esperado (Proposto)**
[PREENCHER — o que deve acontecer após a correção]

**Regras de Negócio Impactadas**
[PREENCHER — ex: Design System LIA v4.2.1, nomenclatura LIA, fluxo do candidato]

**Informações Técnicas**
- Console Logs: {console_logs}
- Network Requests: {network_requests}
- Page URL: {page_url}
- Metadados: {device_info}

---
**Spec Técnica — LIA Design System v4.2.1**

**Arquivos a Localizar**
- Produto React (referência): `{react_file_hint}`
- Produto Vue (branch develop): `{vue_file_hint}`

**Código Vue Atual — Prod (WeDOTalent/ats_front / branch develop)**

```vue
{vue_code_preview}
```

**Tabela de Tokens — Referência Completa**

| Propriedade | Atual (ERRADO) | Correto | Hex | Tailwind | Vuetify |
|---|---|---|---|---|---|
| [PREENCHER] | [ERRADO] | [CORRETO] | `#` | `class=""` | `class=""` |

**Componentes Afetados — Antes / Depois**

[Para CADA componente envolvido no fix (título, botão, ícone, badge, modal, input, lista...),
 especificar o bloco de código antes e depois nas duas stacks:]

**[COMPONENTE 1 — ex: Título da Página]**

Antes (ERRADO):

```vue
<!-- Vue/Vuetify — estado atual -->
[PREENCHER com trecho do codigo Vue real acima]
```

```tsx
<!-- React/Tailwind — referencia -->
[PREENCHER]
```

Depois (CORRETO):

```vue
<!-- Vue/Vuetify — corrigido -->
[PREENCHER]
```

**Regra 90/10 — Checklist Obrigatório**
- [ ] Cyan (#60BED1) SOMENTE em ícones/ações LIA/IA
- [ ] 90% elementos: escala gray-50 a gray-950 (monocromático)
- [ ] Todos os botões: rounded-md (8px), font-medium (500)
- [ ] Source Serif eliminado — buscar "serif" e "Source Serif" no arquivo
- [ ] mdi-brain = ícone exclusivo LIA — não usar sparkles, stars, wand
- [ ] Botão primário: bg-gray-900 (#111827) / variant="primary" no BaseButton
- [ ] Componente Button (DEPRECADO) migrado para BaseButton

**Definition of Done**
- [ ] [PREENCHER]
- [ ] Screenshot comparativo antes/depois
- [ ] Revisão de acessibilidade (contraste WCAG AA, foco, aria-label)
- [ ] PR aprovado e merge na branch develop

**Critérios de Aceitação**
- [PREENCHER]
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

    # ── BetterBugs — extrai mídia e links do ADF ──────────────────────────────
    bb = _extract_adf_media_and_links(adf_desc)
    bb_session_data: dict = {}
    bb_screenshots: list[str] = []

    if source == "BetterBugs" or any([bb["screenshots"], bb["betterbugs_session"]]):
        print("🐛  BetterBugs detectado no card:")
        if bb["betterbugs_session"]:
            print(f"    🔗 Sessão:        {bb['betterbugs_session']}")
        if bb["source_url"]:
            print(f"    🌐 Source URL:    {bb['source_url']}")
        if bb["console_logs_url"]:
            print(f"    📋 Console logs:  {bb['console_logs_url']}")
        if bb["network_logs_url"]:
            print(f"    🌐 Network logs:  {bb['network_logs_url']}")

        # API BetterBugs (vídeo + dados completos)
        if bb["betterbugs_session"] and _betterbugs_api_token():
            print("    🎬 Buscando dados completos via API BetterBugs...")
            bb_session_data = _betterbugs_fetch_session(bb["betterbugs_session"])
            if bb_session_data.get("video_url"):
                print(f"       ✅ Vídeo: {bb_session_data['video_url']}")
            if bb_session_data.get("console_logs"):
                print(f"       ✅ {len(bb_session_data['console_logs'])} entradas de console log")
            if bb_session_data.get("network_logs"):
                print(f"       ✅ {len(bb_session_data['network_logs'])} requests de rede")
            if not any([bb_session_data.get("video_url"), bb_session_data.get("screenshots")]):
                print("       ⚠️  API respondeu mas sem dados de mídia — verifique os endpoints")
        elif bb["betterbugs_session"] and not _betterbugs_api_token():
            print("    💡 Configure BETTERBUGS_API_KEY para acessar vídeo e dados completos")

        # Screenshots do CDN (embedadas no ADF)
        if bb["screenshots"]:
            print(f"    📸 Baixando {len(bb['screenshots'])} screenshot(s) do CDN...")
            bb_screenshots = _download_betterbugs_screenshots(adf_desc, card_key)
            for i, path in enumerate(bb_screenshots, 1):
                size = Path(path).stat().st_size
                print(f"       ✅ Screenshot {i}: {path} ({size:,} bytes)")
            if not bb_screenshots:
                print("       ⚠️  Nenhuma screenshot baixada (CDN inacessível?)")

    screenshot_path = ""
    image_attachments = [a for a in attachments if (a.get("mimeType") or "").startswith("image/")]
    if bb_screenshots:
        screenshot_path = bb_screenshots[0]
    elif image_attachments:
        att = image_attachments[0]
        screenshot_path = f"/tmp/jam_screenshot_{card_key}.png"
        dl_resp = requests.get(
            att["content"], headers=_build_headers(), timeout=30, stream=True
        )
        if dl_resp.ok:
            Path(screenshot_path).write_bytes(dl_resp.content)

    record_type = "Screenshot" if (bb_screenshots or image_attachments) else "Bug Report (sem imagem)"
    if bb_session_data.get("video_url"):
        record_type = "Vídeo de Sessão + Screenshots"

    ref_link = (
        bb["betterbugs_session"]
        or bug_info.get("ref_link")
        or (
            "[PREENCHER: URL do registro no Jam.dev]" if source == "Jam.dev"
            else f"[PREENCHER: link da sessão {source}]"
        )
    )

    # ── Busca arquivos Vue relevantes via GitHub ────────────────────────────
    page_url_val = bug_info["page_url"] or ""
    # Extrai keywords do sumário + URL para localizar arquivos Vue
    kw_from_summary = re.findall(r"[a-zA-ZÀ-ÿ]{4,}", summary)
    vue_files_found = _find_vue_files_for_url(page_url_val, kw_from_summary, max_results=3)
    vue_code_preview = _vue_code_preview(vue_files_found)

    react_file_hint = "[PREENCHER: ex: src/app/funil-de-talentos/page.tsx]"
    vue_file_hint   = (
        ", ".join(f"`{f}`" for f in vue_files_found)
        if vue_files_found
        else "[PREENCHER: ex: features/lia/candidates/index.vue]"
    )
    if vue_files_found:
        print(f"🔗  Arquivos Vue encontrados: {vue_files_found}")

    # Merge console/network logs: API BetterBugs tem prioridade sobre texto parseado
    _console_logs = bug_info["console_logs"]
    _network_requests = bug_info["network_requests"]
    if bb_session_data.get("console_logs"):
        _console_logs = "\n".join(
            str(e) for e in bb_session_data["console_logs"]
        )
    if bb_session_data.get("network_logs"):
        _network_requests = "\n".join(
            str(e) for e in bb_session_data["network_logs"]
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
        page_url=page_url_val or "[não registrado]",
        device_info=bug_info["device_info"] or "[não registrado]",
        console_logs=_console_logs,
        network_requests=_network_requests,
        react_file_hint=react_file_hint,
        vue_file_hint=vue_file_hint,
        vue_code_preview=vue_code_preview,
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

    if bb_session_data.get("video_url"):
        header += f"🎬 Vídeo BetterBugs: {bb_session_data['video_url']}\n"
    if bb["betterbugs_session"]:
        header += f"🐛 Sessão BetterBugs: {bb['betterbugs_session']}\n"

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

        # ── Horizontal rule ────────────────────────────────────────────────────
        if stripped == "---" or stripped == "-------------------------------------":
            content.append({"type": "rule"})
            i += 1
            continue

        # ── Code blocks (``` lang ... ```) ─────────────────────────────────────
        if stripped.startswith("```"):
            lang = stripped[3:].strip() or "plain"
            # Normalise language identifiers Jira understands
            _lang_map = {
                "tsx": "javascript", "jsx": "javascript",
                "ts": "javascript",  "vue": "xml",
                "css": "css",        "python": "python",
                "py": "python",      "sh": "bash",
                "shell": "bash",
            }
            lang = _lang_map.get(lang, lang)
            i += 1
            code_lines: list[str] = []
            while i < len(lines):
                if lines[i].strip() == "```":
                    i += 1
                    break
                code_lines.append(lines[i])
                i += 1
            code_text = "\n".join(code_lines)
            content.append({
                "type": "codeBlock",
                "attrs": {"language": lang},
                "content": [{"type": "text", "text": code_text}],
            })
            continue

        # ── Markdown tables (| col | col |) ────────────────────────────────────
        if stripped.startswith("|") and stripped.endswith("|"):
            table_rows: list[dict] = []
            is_header_row = True
            while i < len(lines):
                s = lines[i].strip()
                if not (s.startswith("|") and s.endswith("|")):
                    break
                # Skip separator rows (|---|---|)
                if re.match(r"^\|[\s\-|:]+\|$", s):
                    i += 1
                    is_header_row = False
                    continue
                cells = [c.strip() for c in s[1:-1].split("|")]
                cell_type = "tableHeader" if is_header_row else "tableCell"
                row_cells = [
                    {
                        "type": cell_type,
                        "attrs": {},
                        "content": [{"type": "paragraph", "content": _parse_inline(c)}],
                    }
                    for c in cells
                ]
                table_rows.append({"type": "tableRow", "content": row_cells})
                i += 1
                if is_header_row:
                    is_header_row = False
            if table_rows:
                content.append({
                    "type": "table",
                    "attrs": {"isNumberColumnEnabled": False, "layout": "default"},
                    "content": table_rows,
                })
            continue

        # ── Headings ───────────────────────────────────────────────────────────
        if stripped.startswith("### "):
            content.append({
                "type": "heading",
                "attrs": {"level": 3},
                "content": _parse_inline(stripped[4:]),
            })
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

        # ── Task lists (- [ ] / - [x] ) ────────────────────────────────────────
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
                    "content": _parse_inline(item_text),
                })
                i += 1
            content.append({
                "type": "taskList",
                "attrs": {"localId": str(uuid.uuid4())},
                "content": task_nodes,
            })
            continue

        # ── Bullet lists ───────────────────────────────────────────────────────
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

        # ── Ordered lists ──────────────────────────────────────────────────────
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

        # ── Empty line ─────────────────────────────────────────────────────────
        if stripped == "":
            content.append({"type": "paragraph", "content": []})
            i += 1
            continue

        # ── Default paragraph ──────────────────────────────────────────────────
        content.append({"type": "paragraph", "content": _parse_inline(stripped)})
        i += 1

    return {"type": "doc", "version": 1, "content": content}


# ─────────────────────────────────────────────────────────────────────────────
# Tags extractor
# ─────────────────────────────────────────────────────────────────────────────

def _extract_tags(text: str) -> list[str]:
    # Aceita "- Tags:" (template) ou "Tags:" (sem traço)
    m = re.search(r"^-?\s*Tags:\s*(.+)", text, re.MULTILINE | re.IGNORECASE)
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

    # ── Busca descrição atual e faz append ──────────────────────────────────
    print(f"\n🔍  Buscando descrição atual de {card_key}...")
    current_data = _get(f"/issue/{card_key}", {"fields": "description"})
    current_desc = current_data["fields"].get("description") or {}
    existing_nodes: list[dict] = []
    if current_desc.get("type") == "doc":
        existing_nodes = current_desc.get("content", [])

    # Separator + new spec nodes
    separator = {"type": "rule"}
    new_nodes  = adf_body.get("content", [])
    merged_doc = {
        "type": "doc",
        "version": 1,
        "content": existing_nodes + ([separator] if existing_nodes else []) + new_nodes,
    }

    if args.dry_run:
        print(f"\n{'━' * 60}")
        print(f"DRY RUN — {card_key}")
        print(f"{'━' * 60}")
        print(f"\nTags a aplicar: {tags or '(nenhuma)'}")
        print(f"Nós existentes na descrição: {len(existing_nodes)}")
        print(f"Nós a adicionar: {len(new_nodes)}")
        print("\nPrimeiros 2000 chars do doc final:")
        print(json.dumps(merged_doc, ensure_ascii=False, indent=2)[:2000])
        print(f"\n{'─' * 60}")
        print("✅  Dry run concluído. Rode sem --dry-run para atualizar.")
        return

    print(f"📝  Atualizando descrição de {card_key} (append abaixo do conteúdo existente)...")
    _put_json(f"/issue/{card_key}", {"fields": {"description": merged_doc}})
    print(f"✅  Descrição atualizada: https://wedotalent.atlassian.net/browse/{card_key}")

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
