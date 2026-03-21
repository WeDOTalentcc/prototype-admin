"""
Design Audit Generator — Jira I/O para Auditoria de Design completa de tela.

Fluxo:
  1. Usuário grava vídeo comparando telas (produto Vue vs. protótipo React/Replit)
     e cria card Jira mencionando tela + elementos a auditar.
  2. `fetch` lê a descrição do card, identifica a tela e os elementos solicitados,
     lê os arquivos React correspondentes, e gera um template de auditoria pré-preenchido.
  3. Agente ou dev preenche a coluna "Vue/Prod (VER)" e os blocos Antes/Depois.
  4. `post` faz append do template preenchido na descrição do card.

Configuração (mesma do bug_spec_generator):
    JIRA_EMAIL       = email da conta Atlassian
    JIRA_API_TOKEN   = token em https://id.atlassian.com/manage-api-tokens
    JIRA_CLOUD_ID    = 8cf762f8-6a44-47de-8915-6b3dc0cd2715  (já preenchido)

Uso:
    python scripts/design_audit_generator.py fetch WT-1640
    python scripts/design_audit_generator.py fetch WT-1640 --output-file /tmp/audit-WT-1640.md
    python scripts/design_audit_generator.py post  WT-1640 --from-file /tmp/audit-WT-1640.md
    python scripts/design_audit_generator.py post  WT-1640 --from-file /tmp/audit.md --dry-run
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


CLOUD_ID       = os.getenv("JIRA_CLOUD_ID", "8cf762f8-6a44-47de-8915-6b3dc0cd2715")
_JIRA_BASE     = f"https://api.atlassian.com/ex/jira/{CLOUD_ID}/rest/api/3"
TODAY          = datetime.now(timezone.utc).strftime("%d/%m/%Y")
REPLIT_ROOT    = Path(__file__).parent.parent.parent / "plataforma-lia"

# ─────────────────────────────────────────────────────────────────────────────
# GitHub — leitura do código Vue real (WeDOTalent/ats_front)
# ─────────────────────────────────────────────────────────────────────────────

GITHUB_REPO   = "WeDOTalent/ats_front"
GITHUB_BRANCH = "develop"
_GH_API       = "https://api.github.com"
_gh_tree_cache: dict | None = None


def _github_token() -> str:
    return os.getenv("GITHUB_PAT_WEDOTALENT", "")


def _github_file(path: str, ref: str = GITHUB_BRANCH) -> str:
    """Lê um arquivo do repositório Vue via GitHub API. Retorna string vazia se não encontrado."""
    token = _github_token()
    if not token:
        return ""
    try:
        resp = requests.get(
            f"{_GH_API}/repos/{GITHUB_REPO}/contents/{path}",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"},
            params={"ref": ref},
            timeout=15,
        )
        if not resp.ok:
            return ""
        data = resp.json()
        if isinstance(data, dict) and data.get("content"):
            import base64 as _b64
            return _b64.b64decode(data["content"]).decode("utf-8", errors="replace")
    except Exception:
        pass
    return ""


def _github_tree(ref: str = GITHUB_BRANCH) -> list[str]:
    """Retorna a lista de todos os arquivos .vue do repositório (com cache)."""
    global _gh_tree_cache
    if _gh_tree_cache is not None:
        return _gh_tree_cache
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
                if f.get("type") == "blob" and f["path"].endswith(".vue")
            ]
            _gh_tree_cache = files
            return files
    except Exception:
        pass
    _gh_tree_cache = []
    return []


def _find_vue_files(keywords: list[str], max_results: int = 8) -> list[str]:
    """Encontra arquivos Vue no repositório que correspondem às keywords."""
    all_files = _github_tree()
    low_kw = [k.lower() for k in keywords]
    scored: list[tuple[int, str]] = []
    for path in all_files:
        score = sum(1 for kw in low_kw if kw in path.lower())
        if score > 0:
            scored.append((score, path))
    scored.sort(key=lambda x: -x[0])
    return [p for _, p in scored[:max_results]]


def _github_snippets(vue_files: list[str], keywords: list[str], max_lines: int = 60) -> str:
    """Lê arquivos Vue do GitHub e retorna trechos relevantes."""
    if not vue_files or not _github_token():
        return ""
    parts: list[str] = []
    low_kw = [k.lower() for k in keywords]
    for path in vue_files[:4]:
        content = _github_file(path)
        if not content:
            continue
        lines = content.splitlines()
        # Coleta linhas relevantes por keyword
        relevant: list[tuple[int, str]] = []
        for i, line in enumerate(lines):
            if any(kw in line.lower() for kw in low_kw + ["class=", "color=", "variant=", "v-icon", "Icon ", "BaseButton", "Button "]):
                relevant.append((i, line))
        # Pega até max_lines das linhas mais relevantes
        snippet_lines = [l for _, l in relevant[:max_lines]]
        if snippet_lines:
            parts.append(f"// {path}\n" + "\n".join(snippet_lines))
    return "\n\n".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# DS LIA v4.2.1 — Tokens de referência
# ─────────────────────────────────────────────────────────────────────────────

DS_TOKENS = {
    "tipografia": {
        "fonte_ui":          ("Open Sans", "100% UI — Source Serif eliminado v4.1"),
        "titulo_h1":         ("text-xl font-semibold text-gray-900", "20px / 600 / #111827"),
        "titulo_h2":         ("text-lg font-semibold text-gray-900", "18px / 600 / #111827"),
        "caption":           ("text-xs text-gray-500 mt-0.5", "12px / 400 / #6B7280"),
        "body":              ("text-sm text-gray-700", "14px / 400 / #374151"),
        "body_small":        ("text-xs text-gray-600", "12px / 400 / #4B5563"),
        "label_botao":       ("text-xs font-medium", "12px / 500 — nunca 600 ou 700"),
    },
    "cores": {
        "cyan_lia":          ("#60BED1", "wedo-cyan — exclusivo LIA; NUNCA substituir por blue"),
        "cinza_primario":    ("#111827", "gray-900 — botão primário, títulos"),
        "cinza_texto":       ("#374151", "gray-700 — texto body"),
        "cinza_secundario":  ("#6B7280", "gray-500 — captions, labels secundários"),
        "cinza_borda":       ("#E5E7EB", "gray-200 — borders, dividers"),
        "bg_pagina":         ("#F9FAFB", "gray-50 — fundo geral"),
        "bg_card":           ("#FFFFFF", "white — cards, modais, painéis"),
        "bg_card_dark":      ("#111827", "gray-900 dark mode"),
    },
    "botoes": {
        "primario":          ("bg-gray-900 text-white hover:bg-gray-800", "Vuetify: color='grey-darken-4' variant='flat'"),
        "outline":           ("variant='outline' border-gray-300", "Vuetify: variant='outlined' color='grey-darken-4'"),
        "ghost":             ("variant='ghost' text-gray-600", "Vuetify: variant='text'"),
        "tamanho_sm":        ("h-8 px-3 text-xs", "Vuetify: size='small'"),
        "tamanho_icon":      ("h-7 w-7 p-0 rounded-md", "Vuetify: icon size='small'"),
        "font":              ("font-medium text-xs", "NUNCA font-semibold ou bold em botões"),
    },
    "bordas": {
        "radius":            ("rounded-md", "8px — padrão DS v4.2.1; NUNCA rounded-lg ou rounded-full em cards"),
        "borda_padrao":      ("border border-gray-200", "Vuetify: border variant"),
        "borda_escura":      ("dark:border-gray-800", "dark mode"),
    },
    "icones": {
        "brain_lia":         ("Brain w-4 h-4 text-wedo-cyan", "mdi-brain color='#60BED1' — ícone LIA exclusivo"),
        "tamanho_padrao":    ("w-4 h-4", "16x16px — tamanho padrão de ícones"),
        "tamanho_grande":    ("w-5 h-5", "20x20px — ícones de header"),
        "cor_padrao":        ("text-gray-600 dark:text-gray-400", "ícones neutros"),
    },
    "componentes": {
        "badge_contagem":    ("ml-1.5 h-4 px-1.5 text-[10px] bg-gray-900 text-white", "Vuetify: bg-color='grey-darken-4' rounded='pill'"),
        "badge_outline":     ("variant='outline' border-gray-300 text-gray-600", "Vuetify: variant='outlined'"),
        "input_busca":       ("pl-9 text-xs rounded-md border-gray-200 bg-transparent", "Vuetify: variant='outlined' density='compact'"),
        "chip_ativo":        ("bg-gray-900 text-white border-gray-900", "filtro selecionado"),
        "chip_inativo":      ("bg-white text-gray-600 border-gray-200 hover:bg-gray-50", "filtro não selecionado"),
        "tabs_lista":        ("bg-white border border-gray-200 rounded-md", "Vuetify: VTabs — sem elevação"),
        "tabs_trigger":      ("rounded-md text-xs", "Vuetify: VTab text-style='caption'"),
        "dialog_header":     ("px-6 pt-5 pb-3 border-b border-gray-100", "Vuetify: VCardTitle + VDivider"),
        "dialog_footer":     ("px-6 py-4 border-t border-gray-100 flex justify-end gap-2", "Vuetify: VCardActions"),
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN MAP — mapeamento tela → arquivos React + hint Vue
# Opção A (tabela fixa) com fallback B (grep no código)
# ─────────────────────────────────────────────────────────────────────────────

SCREEN_MAP: dict[str, dict] = {
    "funil-de-talentos": {
        "nome":         "Funil de Talentos",
        "rota":         "/funil-de-talentos",
        "keywords":     ["funil de talentos", "funil-de-talentos", "talent funnel",
                         "busca de candidatos", "candidatos", "smart search",
                         "linguagem natural", "compartilhar busca", "filtros de candidatos"],
        "react_files":  [
            "src/app/funil-de-talentos/page.tsx",
            "src/components/pages/candidates/CandidatesHeader.tsx",
            "src/components/pages/candidates/CandidateSearchBar.tsx",
            "src/components/pages/candidates/CandidateTabs.tsx",
            "src/components/pages/candidates/CandidatesTable.tsx",
            "src/components/search/smart-search-input.tsx",
            "src/components/modals/share-search-modal.tsx",
        ],
        "vue_files":    [
            "features/lia/candidates/index.vue",
            "features/lia/candidates/SearchSourceButtons.vue",
            "features/lia/candidates/search/similar.vue",
            "features/lia/candidates/search/description.vue",
            "features/lia/candidates/search/archetypes.vue",
            "features/lia/candidates/search/boolean.vue",
            "features/lia/search/side-panel.vue",
        ],
        "vue_hint":     "features/lia/candidates/index.vue + SearchSourceButtons.vue",
        "regioes":      [
            "Header (título, caption, botão compartilhar)",
            "Tabs (Todos / Favoritos / Listas / Buscas Salvas)",
            "Área de Busca (input, modos, filtros de status, filtros de senioridade)",
            "Modos de Busca LIA (Linguagem Natural, Similar, JD, Boolean, Arquétipos)",
            "Tabela de Candidatos (colunas, badges de score, ações)",
            "Paginação",
            "Modal Compartilhar Busca",
            "Estado Vazio / Erro de busca",
        ],
    },
    "funil-kanban": {
        "nome":         "Funil (Kanban / Pipeline)",
        "rota":         "/funil",
        "keywords":     ["funil kanban", "funil pipeline", "pipeline", "kanban",
                         "etapas", "mover candidato", "arrastar", "drag"],
        "react_files":  [
            "src/app/funil/page.tsx",
            "src/components/pages/job-kanban/KanbanCard.tsx",
            "src/components/pages/job-kanban/MoveConfirmationModal.tsx",
        ],
        "vue_files":    [
            "features/applies/kanban_filters.vue",
            "components/ui/table/actions/candidates.vue",
        ],
        "vue_hint":     "features/applies/kanban_filters.vue",
        "regioes":      [
            "Header (seletor de vaga, ações)",
            "Colunas Kanban (títulos de etapa, contagem)",
            "Card de Candidato (nome, score, senioridade, avatar, ações)",
            "Modal de Confirmação de Mover",
            "Estado Vazio de coluna",
        ],
    },
    "jobs": {
        "nome":         "Jobs / Vagas",
        "rota":         "/jobs",
        "keywords":     ["jobs", "vagas", "requisições", "vaga", "job listing",
                         "criar vaga", "criar job", "lista de vagas"],
        "react_files":  [
            "src/app/jobs/page.tsx",
            "src/components/modals/create-job-modal.tsx",
            "src/components/modals/edit-job-modal.tsx",
        ],
        "vue_files":    [
            "features/lia/jobs/search.vue",
            "composables/useCreateJobModal.ts",
        ],
        "vue_hint":     "features/lia/jobs/search.vue",
        "regioes":      [
            "Header (título, botão criar vaga)",
            "Tabela/Lista de Vagas (colunas, status badge, ações)",
            "Modal Criar Vaga",
            "Modal Editar Vaga",
            "Estado Vazio",
        ],
    },
    "chat": {
        "nome":         "Chat LIA",
        "rota":         "/chat",
        "keywords":     ["chat", "chat lia", "conversa", "mensagem", "chatbot",
                         "assistente", "lia chat", "histórico de conversa"],
        "react_files":  [
            "src/app/chat/page.tsx",
        ],
        "vue_files":    [
            "features/lia/ConversationList.vue",
            "pages/user/lia/index.vue",
            "pages/user/sourcing/[id]/chat.vue",
        ],
        "vue_hint":     "features/lia/ConversationList.vue + pages/user/lia/index.vue",
        "regioes":      [
            "Área de conversa (mensagens, timestamps)",
            "Input de mensagem (textarea, botão enviar, ícone LIA)",
            "Sidebar de histórico",
            "Estado vazio (primeira conversa)",
        ],
    },
    "configuracoes": {
        "nome":         "Configurações",
        "rota":         "/configuracoes",
        "keywords":     ["configurações", "configuracoes", "settings", "integrações",
                         "ai credits", "créditos", "perfil", "conta", "preferências"],
        "react_files":  [
            "src/app/configuracoes/page.tsx",
            "src/app/configuracoes/integracoes/page.tsx",
            "src/app/configuracoes/ai-credits/page.tsx",
        ],
        "vue_files":    [],
        "vue_hint":     "Buscar: settings, configuracoes nas pages/",
        "regioes":      [
            "Sidebar de navegação de configurações",
            "Seção de Perfil",
            "Seção de Integrações (cards de integração, status badge)",
            "Seção AI Credits (uso, plano, histórico)",
        ],
    },
    "login": {
        "nome":         "Login / Autenticação",
        "rota":         "/login",
        "keywords":     ["login", "autenticação", "autenticacao", "signin", "sign in",
                         "acesso", "senha", "email e senha", "welcome"],
        "react_files":  [
            "src/app/login/page.tsx",
            "src/app/login/welcome/page.tsx",
            "src/app/register/page.tsx",
            "src/app/forgot-password/page.tsx",
        ],
        "vue_files":    [],
        "vue_hint":     "Buscar: pages/login, auth nas pages/",
        "regioes":      [
            "Logo / Marca",
            "Card de login (container, sombra, padding)",
            "Input Email",
            "Input Senha (com toggle show/hide)",
            "Botão Entrar (primário)",
            "Link 'Esqueci minha senha'",
            "Mensagem de erro",
        ],
    },
    "modal-candidato": {
        "nome":         "Modal Cadastro de Candidato",
        "rota":         "/funil-de-talentos",
        "keywords":     ["cadastro de candidato", "novo candidato", "modal candidato",
                         "cadastrar candidato", "new candidate", "add candidate",
                         "cv tab", "linkedin tab", "manual tab", "upload cv",
                         "cadastrar com cv", "cadastrar via linkedin"],
        "react_files":  [
            "src/components/modals/new-candidate-unified-modal.tsx",
            "src/components/modals/add-candidate-modal.tsx",
        ],
        "vue_files":    [
            "features/candidates/new_candidate_dialog.vue",
            "components/ui/base/BaseButton.vue",
            "components/ui/button/button.vue",
            "config/vuetify.config.ts",
        ],
        "vue_hint":     "features/candidates/new_candidate_dialog.vue",
        "regioes":      [
            "Header do Modal (título, subtítulo, dimensões)",
            "Tabs de Navegação (CV / LinkedIn / Manual)",
            "Tab CV (drop zone, botão Cadastrar com CV)",
            "Tab LinkedIn (ícone header, hint LIA, botão LinkedIn)",
            "Tab Manual (campos, botão Cadastrar Candidato)",
            "Estado de Processamento (Brain animate-pulse)",
        ],
    },
}

# Palavras-chave de elementos UI para extração do card Jira
ELEMENT_KEYWORDS = {
    "tipografia":  ["fonte", "tipografia", "typography", "texto", "title", "título", "caption",
                    "font", "size", "tamanho", "weight", "bold", "semibold"],
    "botões":      ["botão", "botoes", "button", "btn", "cta", "ação", "ações", "action"],
    "cores":       ["cor", "cores", "color", "background", "bg", "fundo", "hex", "paleta"],
    "ícones":      ["ícone", "icone", "icon", "brain", "mdi", "lucide"],
    "inputs":      ["input", "campo", "field", "busca", "search", "textarea", "formulário"],
    "chips":       ["chip", "chips", "filtro", "filtros", "tag", "badge", "pill"],
    "modal":       ["modal", "dialog", "popup", "overlay", "drawer"],
    "tabs":        ["tab", "tabs", "aba", "abas", "navegação", "navegar"],
    "tabela":      ["tabela", "table", "coluna", "colunas", "linha", "linha", "grid", "lista"],
    "paginação":   ["paginação", "paginacao", "paginar", "próxima", "anterior", "pagination"],
    "kanban":      ["kanban", "coluna", "card", "arrastar", "drag", "etapa", "stage"],
    "comportamento": ["comportamento", "hover", "estado", "state", "animação", "transition",
                      "loading", "vazio", "empty", "erro", "error"],
}


# ─────────────────────────────────────────────────────────────────────────────
# Auth — idêntico ao bug_spec_generator (mesma ordem de prioridade)
# ─────────────────────────────────────────────────────────────────────────────

def _get_auth() -> tuple[dict[str, str], str]:
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
                        return {
                            "Authorization": f"Bearer {token}",
                            "Accept":        "application/json",
                            "Content-Type":  "application/json",
                        }, _JIRA_BASE
            except Exception as exc:
                print(f"⚠️  Conector Replit falhou ({exc}), tentando fallback...", file=sys.stderr)

    token = os.getenv("JIRA_TOKEN", "")
    if token:
        return {"Authorization": f"Bearer {token}", "Accept": "application/json",
                "Content-Type": "application/json"}, _JIRA_BASE

    email     = os.getenv("JIRA_EMAIL", "")
    api_token = os.getenv("JIRA_API_TOKEN", "")
    if email and api_token:
        creds = base64.b64encode(f"{email}:{api_token}".encode()).decode()
        return {"Authorization": f"Basic {creds}", "Accept": "application/json",
                "Content-Type": "application/json"}, _JIRA_BASE

    sys.exit("❌  Credenciais Jira não encontradas. Configure JIRA_EMAIL + JIRA_API_TOKEN.")


def _get(path: str, params: dict | None = None) -> dict:
    headers, base = _get_auth()
    resp = requests.get(f"{base}{path}", headers=headers, params=params, timeout=15)
    if not resp.ok:
        sys.exit(f"❌  Jira API {resp.status_code}: {resp.text[:300]}")
    return resp.json()


def _put_json(path: str, body: dict) -> dict:
    headers, base = _get_auth()
    resp = requests.put(f"{base}{path}", headers=headers, json=body, timeout=15)
    if not resp.ok:
        sys.exit(f"❌  Jira API {resp.status_code}: {resp.text[:400]}")
    return {} if resp.status_code == 204 or not resp.content else resp.json()


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
            "screenshots":       [],
            "links":             [],
            "inline_cards":      [],
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
                # Classifica o link
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
                ext = ext[:4]  # segurança
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
            # BetterBugs serve .webm mas converte para .mp4 via CDN
            if vid_path.startswith("http"):
                result["video_url"] = vid_path
            else:
                # Monta a URL do CDN (workspace_id vem dos IDs embutidos no CDN URL da screenshot)
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
            result["console_logs"] = logs[:50]  # máximo 50 entradas
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


# ─────────────────────────────────────────────────────────────────────────────
# Screen detection — identifica a tela a partir da descrição do card
# ─────────────────────────────────────────────────────────────────────────────

def _detect_screen(description_text: str) -> tuple[str, dict] | tuple[None, None]:
    """Retorna (screen_key, screen_info) ou (None, None)."""
    lower = description_text.lower()
    # Opção A: tabela fixa
    best_key  = None
    best_score = 0
    for key, info in SCREEN_MAP.items():
        score = sum(1 for kw in info["keywords"] if kw in lower)
        if score > best_score:
            best_score = score
            best_key   = key
    if best_key and best_score >= 1:
        return best_key, SCREEN_MAP[best_key]

    # Opção B: fallback grep no codebase (tenta nomes de rotas)
    for key, info in SCREEN_MAP.items():
        rota = info["rota"].strip("/").replace("-", " ")
        if rota in lower or info["rota"] in lower:
            return key, info

    return None, None


def _detect_elements(description_text: str) -> list[str]:
    """Detecta categorias de elementos UI mencionados na descrição."""
    lower     = description_text.lower()
    found: list[str] = []
    for category, keywords in ELEMENT_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            found.append(category)
    return found if found else ["todos os elementos"]


# ─────────────────────────────────────────────────────────────────────────────
# React file reader — lê arquivos e extrai dados de componentes
# ─────────────────────────────────────────────────────────────────────────────

def _read_react_file(rel_path: str) -> str:
    """Lê o arquivo React do protótipo Replit."""
    full = REPLIT_ROOT / rel_path
    if not full.exists():
        return ""
    try:
        return full.read_text(encoding="utf-8")
    except Exception:
        return ""


def _extract_class_for_pattern(content: str, pattern: str) -> str:
    """Extrai className de um padrão JSX (ex: '<h1 className=')."""
    m = re.search(rf'{re.escape(pattern)}\s+className=["\{{]([^"}}]+)', content)
    if m:
        return m.group(1).strip()
    m2 = re.search(rf'{re.escape(pattern)}[^>]*className=["\{{]cn\(([^)]+)\)', content)
    if m2:
        return m2.group(1).strip()
    return "[extrair manualmente]"


def _extract_icon_usages(content: str) -> list[str]:
    """Extrai ícones usados no componente."""
    icons = re.findall(r'<([A-Z][a-zA-Z]+)\s+className=["\{][^"]*(?:w-\d|h-\d)[^"]*["\}]', content)
    icons += re.findall(r'import\s*\{([^}]+)\}\s*from\s*["\']lucide-react["\']', content)
    flat: list[str] = []
    for match in icons:
        flat.extend([x.strip() for x in match.split(",") if x.strip()])
    return list(dict.fromkeys(flat))


def _extract_brain_usages(content: str) -> list[str]:
    """Extrai usos do ícone Brain (LIA)."""
    return re.findall(r'<Brain\s+className=["\{]([^"}\]]+)["\}]', content)


def _extract_buttons(content: str) -> list[dict[str, str]]:
    """Extrai botões com variant e className."""
    results: list[dict[str, str]] = []
    for m in re.finditer(
        r'<Button\s[^>]*variant=["\{]([^"}\]]+)["\}][^>]*(?:className=["\{]([^"}\]]+)["\}])?',
        content,
    ):
        results.append({"variant": m.group(1), "className": (m.group(2) or "").strip()})
    return results[:8]


def _extract_search_modes(content: str) -> list[dict[str, str]]:
    """Extrai modos de busca do SmartSearchInput."""
    modes: list[dict[str, str]] = []
    m = re.search(r"const modes[^=]*=\s*\[([^\]]+)\]", content, re.DOTALL)
    if m:
        for entry in re.finditer(
            r'key:\s*["\']([^"\']+)["\'][^}]*label:\s*["\']([^"\']+)["\'][^}]*icon:\s*([A-Za-z]+)',
            m.group(1),
        ):
            modes.append({"key": entry.group(1), "label": entry.group(2), "icon": entry.group(3)})
    return modes


# ─────────────────────────────────────────────────────────────────────────────
# Template builder — gera o markdown de auditoria pré-preenchido
# ─────────────────────────────────────────────────────────────────────────────

def _build_audit_template(
    card_key: str,
    card_title: str,
    description_text: str,
    screen_key: str,
    screen: dict,
    elements_detected: list[str],
    bb_data: dict | None = None,
    bb_screenshots: list[str] | None = None,
) -> str:
    lines: list[str] = []
    bb_data = bb_data or {}
    bb_screenshots = bb_screenshots or []

    # ── Leitura antecipada do código Vue real (GitHub) ─────────────────────
    vue_files = screen.get("vue_files", [])
    vue_contents: dict[str, str] = {}
    has_github = bool(_github_token())
    if has_github and vue_files:
        print(f"🔗  Lendo {len(vue_files)} arquivo(s) Vue do GitHub ({GITHUB_REPO}/{GITHUB_BRANCH})...")
        for vf in vue_files:
            content = _github_file(vf)
            if content:
                vue_contents[vf] = content
                print(f"    ✅ {vf} ({len(content.splitlines())} linhas)")
            else:
                print(f"    ⚠️  {vf} — não encontrado")

    # ── Cabeçalho ─────────────────────────────────────────────────────────
    lines += [
        "---",
        "",
        f"## AUDITORIA DE DESIGN — LIA Design System v4.2.1",
        "",
        f"**Card:** {card_key}  ",
        f"**Tela:** {screen['nome']}  ",
        f"**Rota:** `{screen['rota']}`  ",
        f"**Gerado em:** {TODAY}  ",
        f"**Elementos solicitados:** {', '.join(elements_detected)}  ",
        "",
    ]

    # ── BetterBugs context (se houver) ────────────────────────────────────
    bb_lines: list[str] = []
    if bb_data.get("betterbugs_session"):
        bb_lines.append(f"**Sessão BetterBugs:** {bb_data['betterbugs_session']}  ")
    if bb_data.get("source_url"):
        bb_lines.append(f"**URL reportada:** {bb_data['source_url']}  ")
    if bb_data.get("console_logs_url"):
        bb_lines.append(f"**Console logs:** {bb_data['console_logs_url']}  ")
    if bb_data.get("network_logs_url"):
        bb_lines.append(f"**Network logs:** {bb_data['network_logs_url']}  ")
    if bb_screenshots:
        bb_lines.append(
            f"**Screenshots BetterBugs ({len(bb_screenshots)}):** "
            + " · ".join(bb_screenshots)
            + "  "
        )
    if bb_lines:
        lines += ["### Contexto BetterBugs", ""] + bb_lines + [""]

    # ── Arquivos de Referência ─────────────────────────────────────────────
    react_files_exist = [f for f in screen["react_files"] if (REPLIT_ROOT / f).exists()]
    react_files_missing = [f for f in screen["react_files"] if not (REPLIT_ROOT / f).exists()]

    lines += [
        "### Arquivos de Referência",
        "",
        "**React/Next.js — CORRETO (referência de spec):**",
    ]
    for f in react_files_exist:
        lines.append(f"- `plataforma-lia/{f}`")
    for f in react_files_missing:
        lines.append(f"- `plataforma-lia/{f}` — verificar nome")

    lines += ["", "**Vue/Vuetify — Prod atual (branch: develop):**"]
    if vue_contents:
        for vf in vue_files:
            status = "lido" if vf in vue_contents else "nao encontrado"
            lines.append(f"- `{GITHUB_REPO}/{vf}` ({status})")
    else:
        lines.append(f"- {screen['vue_hint']}")
    lines.append("")

    # ── Leitura dos arquivos React ─────────────────────────────────────────
    all_content = "\n".join(_read_react_file(f) for f in screen["react_files"])

    # ── Mapa de Componentes ────────────────────────────────────────────────
    lines += [
        "---",
        "",
        "### 📊 Mapa de Componentes Auditados",
        "",
        f"Regiões da tela **{screen['nome']}**:",
        "",
    ]
    for regiao in screen["regioes"]:
        lines.append(f"- {regiao}")
    lines.append("")

    # ── Extração automática dos dados React ───────────────────────────────
    icons_used    = _extract_icon_usages(all_content)
    brain_usages  = _extract_brain_usages(all_content)
    buttons       = _extract_buttons(all_content)
    search_modes  = _extract_search_modes(all_content)

    lines += [
        "#### Ícones detectados no protótipo React",
        "",
    ]
    for ic in icons_used[:12]:
        lines.append(f"- `{ic}`")
    lines.append("")

    if brain_usages:
        lines += [
            "#### Ícone LIA (Brain) — usos detectados",
            "",
        ]
        for usage in brain_usages:
            lines.append(f"- `<Brain className=\"{usage}\" />` → Vuetify: `<v-icon color=\"#60BED1\">mdi-brain</v-icon>`")
        lines.append("")

    if search_modes:
        lines += [
            "#### Modos de Busca SmartSearchInput",
            "",
            "| Modo | Label | Ícone React | Ícone Vuetify |",
            "| --- | --- | --- | --- |",
        ]
        icon_map = {
            "Brain":    "mdi-brain",
            "Users":    "mdi-account-group",
            "FileText": "mdi-file-document",
            "Binary":   "mdi-code-braces",
            "Target":   "mdi-target",
        }
        for m in search_modes:
            vuetify_icon = icon_map.get(m["icon"], f"mdi-{m['icon'].lower()}")
            lines.append(f"| `{m['key']}` | {m['label']} | `{m['icon']}` | `{vuetify_icon}` |")
        lines.append("")

    # ── Tabela de Tokens ───────────────────────────────────────────────────
    lines += [
        "---",
        "",
        "### 📋 Tabela de Tokens — Auditoria Completa",
        "",
        "| Componente | Propriedade | React/CORRETO | Vue/Prod (VER) | CSS Var | Hex | Tailwind | Vuetify |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    # Header / Tipografia
    titulo_cls = _extract_class_for_pattern(all_content, "<h1")
    if titulo_cls == "[extrair manualmente]":
        titulo_cls = "textStyles.title + text-xl font-semibold"
    lines += [
        f"| Header — Título h1 | font, size, weight, color | `{titulo_cls}` | [VER NO PROD] | `--color-gray-900` | #111827 | `text-xl font-semibold text-gray-900` | `class=\"text-h6 font-weight-semibold\"` |",
        "| Header — Caption | font, size, color | `textStyles.secondary text-xs mt-0.5` | [VER NO PROD] | `--color-gray-500` | #6B7280 | `text-xs text-gray-500` | `class=\"text-caption text-grey-lighten-1\"` |",
        "| Botão Compartilhar | variant, border, font | `variant='outline' rounded-md border-gray-300` | [VER NO PROD] | — | — | `rounded-md border-gray-300` | `variant='outlined' color='grey-darken-4'` |",
        "| Botão Primário | bg, text, hover | `bg-gray-900 text-white hover:bg-gray-800` | [VER NO PROD] | — | #111827 | `bg-gray-900` | `color='grey-darken-4' variant='flat'` |",
        "| Tabs — Lista | bg, border, radius | `bg-white border border-gray-200 rounded-md` | [VER NO PROD] | `--color-gray-200` | #E5E7EB | `border-gray-200 rounded-md` | `VTabs elevation='0'` |",
        "| Tabs — Trigger | font, size, radius | `rounded-md text-xs font-medium` | [VER NO PROD] | — | — | `text-xs rounded-md` | `text-style='caption'` |",
        "| Badge Contagem | bg, text, size | `bg-gray-900 text-white h-4 px-1.5 text-[10px]` | [VER NO PROD] | — | #111827 | `bg-gray-900 text-[10px]` | `bg-color='grey-darken-4' rounded='pill'` |",
        "| Input Busca | pl, font, border, radius | `pl-9 text-xs rounded-md border-gray-200 bg-transparent` | [VER NO PROD] | `--color-gray-200` | #E5E7EB | `pl-9 text-xs rounded-md` | `variant='outlined' density='compact'` |",
        "| Search Ícone | icon, size, color | `Search h-4 w-4 text-gray-400` | [VER NO PROD] | `--color-gray-400` | #9CA3AF | — | `mdi-magnify color='grey-lighten-1'` |",
        "| Chip Status — Ativo | bg, text, border | `bg-gray-900 text-white border-gray-900` | [VER NO PROD] | — | #111827 | `bg-gray-900` | `color='grey-darken-4' variant='flat'` |",
        "| Chip Status — Inativo | bg, text, border | `bg-white text-gray-600 border-gray-200` | [VER NO PROD] | — | #4B5563 | `text-gray-600 border-gray-200` | `color='grey-darken-2' variant='outlined'` |",
        "| Ícone Brain LIA | icon, size, color | `Brain w-4 h-4 text-wedo-cyan` | [VER NO PROD] | `--color-wedo-cyan` | #60BED1 | — | `mdi-brain color='#60BED1'` |",
        "| Modal — Header | padding, border-b | `px-6 pt-5 pb-3 border-b border-gray-100` | [VER NO PROD] | `--color-gray-100` | #F3F4F6 | `border-gray-100` | `VCardTitle + VDivider` |",
        "| Modal — Título | font, size, weight | `textStyles.title flex items-center gap-2` | [VER NO PROD] | — | — | `text-gray-900 font-semibold` | `class=\"text-h6\"` |",
        "| Fundo Página | bg | `bg-gray-50 dark:bg-gray-950` | [VER NO PROD] | `--color-gray-50` | #F9FAFB | `bg-gray-50` | `bg-color='grey-lighten-5'` |",
        "| Fundo Card/Painel | bg, border, radius | `bg-white border border-gray-200 rounded-md` | [VER NO PROD] | — | #FFFFFF | `bg-white` | `VCard elevation='0'` |",
    ]
    lines.append("")

    # ── Specs Antes / Depois ───────────────────────────────────────────────
    lines += [
        "---",
        "",
        "### 🔄 Specs Antes / Depois — por Componente",
        "",
        "> **Instruções para o dev:** Para cada bloco abaixo, copie o código React como referência visual e ajuste o código Vue conforme as especificações da tabela acima.",
        "",
    ]

    # Gera seções por região da tela
    # Prepara snippets Vue por arquivo para uso nos blocos Antes/Depois
    def _vue_snippet_for_region(regiao: str) -> str:
        """Extrai trecho do código Vue relacionado à região."""
        # Keywords para buscar no código Vue
        region_lower = regiao.lower()
        kw_map = {
            "header":       ["header", "title", "h2", "caption", "breadcrumb", "pa-6", "v-card-title"],
            "tab":          ["v-tab", "v-tabs", "tab-btn", "searchType", "search-tab"],
            "busca":        ["search", "input", "v-text-field", "FormInput", "placeholder"],
            "modo":         ["searchType", "searchMode", "natural", "similar", "description", "archetype", "boolean"],
            "botão":        ["BaseButton", "v-btn", "Button", "custom_color", "@click"],
            "ícone":        ["v-icon", "Icon ", "mdi-", "lucide-", "brain", "linkedin"],
            "cv":           ["cv", "upload", "file", "drag", "drop", "mdi-file"],
            "linkedin":     ["linkedin", "0A66C2", "mdi-linkedin"],
            "manual":       ["manual", "manualForm", "mdi-account"],
            "processament": ["isEnriching", "loading", "animate-pulse", "mdi-brain", "progress"],
            "modal":        ["v-dialog", "v-card", "v-card-title", "max-width"],
            "chip":         ["v-chip", "FilterChip", "chip", "filter"],
            "tabela":       ["v-data-table", "v-table", "table", "column"],
        }
        relevant_kw: list[str] = []
        for key, kws in kw_map.items():
            if key in region_lower or any(k in region_lower for k in kws[:2]):
                relevant_kw.extend(kws)

        if not relevant_kw or not vue_contents:
            return f"<!-- Buscar em: {screen['vue_hint']} -->"

        best_lines: list[str] = []
        for vf, content in list(vue_contents.items())[:2]:
            lines_list = content.splitlines()
            matched: list[str] = []
            for i, line in enumerate(lines_list):
                if any(kw.lower() in line.lower() for kw in relevant_kw):
                    # Include context: 1 line before + matched + 1 after
                    start = max(0, i - 1)
                    end = min(len(lines_list), i + 3)
                    matched.extend(lines_list[start:end])
                    matched.append("")
                if len(matched) >= 30:
                    break
            if matched:
                best_lines.append(f"// {vf}")
                best_lines.extend(matched[:30])

        return "\n".join(best_lines) if best_lines else f"<!-- Buscar em: {screen['vue_hint']} -->"

    for regiao in screen["regioes"]:
        vue_snippet = _vue_snippet_for_region(regiao)
        react_file_hint = screen["react_files"][0] if screen["react_files"] else "page.tsx"
        region_tag = regiao.split("(")[0].strip().replace(" ", "")

        lines += [
            f"#### {regiao}",
            "",
            "**Referência React (CORRETO):**",
            "```tsx",
            f"// {react_file_hint}",
            f"// Buscar por: <{region_tag}",
            "```",
            "",
            "**Vue/Vuetify — ANTES (estado atual no prod):**",
            "```vue",
            vue_snippet,
            "```",
            "",
            "**Vue/Vuetify — DEPOIS (corrigido conforme DS v4.2.1):**",
            "```vue",
            "<!-- Preencher com o codigo corrigido conforme tokens da tabela acima -->",
            "```",
            "",
        ]

    # ── Regra 90/10 ───────────────────────────────────────────────────────
    lines += [
        "---",
        "",
        "### ⚠️ Regra 90/10 — Checklist",
        "",
        "- [ ] 90% da tela usa escala de cinza (#111827, #374151, #6B7280, #9CA3AF, #E5E7EB, #F9FAFB, #FFFFFF)",
        "- [ ] Cyan #60BED1 usado **apenas** em: ícone Brain LIA, loading states, destaque de IA",
        "- [ ] Zero uso de cores brand (blue, purple, indigo) em elementos UI genéricos",
        "- [ ] Todos os botões com `font-medium` (500) — nunca `font-semibold` ou `font-bold`",
        "- [ ] `border-radius: 8px` (`rounded-md`) em todos os cards, inputs, botões, modais",
        "- [ ] Open Sans em toda a UI — nenhuma fonte diferente",
        "- [ ] Ícones LIA: `Brain` com `color='#60BED1'` — sem variações de cor",
        "- [ ] Badges de contagem: `bg-gray-900 text-white` (modo claro) / `bg-gray-100 text-gray-900` (dark)",
        "",
    ]

    # ── Definition of Done ─────────────────────────────────────────────────
    lines += [
        "---",
        "",
        "### ✅ Definition of Done — Auditoria",
        "",
        f"- [ ] Todos os componentes da tela `{screen['nome']}` auditados",
        "- [ ] Tabela de tokens preenchida (coluna Vue/Prod)",
        "- [ ] Blocos Antes/Depois escritos para cada região",
        "- [ ] Checklist 90/10 aprovado",
        "- [ ] PR criado com referência a este card",
        f"- [ ] QA visual realizado comparando produto vs. protótipo Replit (`{screen['rota']}`)",
        "",
        f"> **Referência visual:** `https://plataforma-lia.replit.dev{screen['rota']}`  ",
        f"> **DS v4.2.1:** `plataforma-lia/docs/design-system/00-design-system-v4.md`  ",
        "",
    ]

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# ADF Converter — Markdown → Atlassian Document Format
# (adaptado do bug_spec_generator com suporte a tabelas, code blocks, h3/h4)
# ─────────────────────────────────────────────────────────────────────────────

def _md_to_adf(text: str) -> dict:
    nodes: list[dict] = []

    def _inline(line: str) -> list[dict]:
        """Converte linha com **bold**, `code`, e texto normal para inline nodes."""
        parts: list[dict] = []
        while line:
            m_code = re.search(r"`([^`]+)`", line)
            m_bold = re.search(r"\*\*([^*]+)\*\*", line)
            if not m_code and not m_bold:
                if line:
                    parts.append({"type": "text", "text": line})
                break
            first = None
            if m_code and m_bold:
                first = m_code if m_code.start() < m_bold.start() else m_bold
            else:
                first = m_code or m_bold
            before = line[: first.start()]
            if before:
                parts.append({"type": "text", "text": before})
            if first is m_code:
                parts.append({"type": "text", "text": first.group(1),
                               "marks": [{"type": "code"}]})
            else:
                parts.append({"type": "text", "text": first.group(1),
                               "marks": [{"type": "strong"}]})
            line = line[first.end():]
        return parts or [{"type": "text", "text": ""}]

    def _para(content: list[dict]) -> dict:
        return {"type": "paragraph", "content": content}

    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]

        # Horizontal rule
        if re.match(r"^-{3,}$", line.strip()):
            nodes.append({"type": "rule"})
            i += 1
            continue

        # Headings h2, h3, h4
        m_h = re.match(r"^(#{2,4})\s+(.+)$", line)
        if m_h:
            level = len(m_h.group(1))
            nodes.append({
                "type": "heading",
                "attrs": {"level": level},
                "content": _inline(m_h.group(2)),
            })
            i += 1
            continue

        # Code blocks
        m_cb = re.match(r"^```(\w*)$", line.strip())
        if m_cb:
            lang = m_cb.group(1) or "plain"
            code_lines: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            nodes.append({
                "type": "codeBlock",
                "attrs": {"language": lang},
                "content": [{"type": "text", "text": "\n".join(code_lines)}],
            })
            i += 1
            continue

        # Tables
        if line.strip().startswith("|"):
            table_rows: list[list[str]] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                row = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.match(r"^[-: ]+$", c) for c in row):
                    table_rows.append(row)
                i += 1
            if table_rows:
                adf_rows: list[dict] = []
                for ri, row in enumerate(table_rows):
                    cell_type = "tableHeader" if ri == 0 else "tableCell"
                    cells = []
                    for cell in row:
                        cells.append({
                            "type": cell_type,
                            "attrs": {},
                            "content": [_para(_inline(cell))],
                        })
                    adf_rows.append({"type": "tableRow", "content": cells})
                nodes.append({
                    "type": "table",
                    "attrs": {"isNumberColumnEnabled": False, "layout": "full-width"},
                    "content": adf_rows,
                })
            continue

        # Task list items
        m_task = re.match(r"^- \[([ xX])\] (.+)$", line)
        if m_task:
            checked = m_task.group(1).lower() == "x"
            if not nodes or nodes[-1].get("type") != "taskList":
                nodes.append({
                    "type":    "taskList",
                    "attrs":   {"localId": str(uuid.uuid4())},
                    "content": [],
                })
            task_node = {
                "type":    "taskItem",
                "attrs":   {"localId": str(uuid.uuid4()), "state": "DONE" if checked else "TODO"},
                "content": _inline(m_task.group(2)),
            }
            nodes[-1]["content"].append(task_node)
            i += 1
            continue

        # Bullet list items
        m_bullet = re.match(r"^[-*]\s+(.+)$", line)
        if m_bullet:
            if not nodes or nodes[-1].get("type") != "bulletList":
                nodes.append({"type": "bulletList", "content": []})
            nodes[-1]["content"].append({
                "type":    "listItem",
                "content": [_para(_inline(m_bullet.group(1)))],
            })
            i += 1
            continue

        # Block quote (> ...)
        m_bq = re.match(r"^>\s*(.*)$", line)
        if m_bq:
            nodes.append({
                "type":    "blockquote",
                "content": [_para(_inline(m_bq.group(1)))],
            })
            i += 1
            continue

        # Empty line — close list
        if line.strip() == "":
            i += 1
            continue

        # Paragraph
        nodes.append(_para(_inline(line)))
        i += 1

    return {"version": 1, "type": "doc", "content": nodes}


# ─────────────────────────────────────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────────────────────────────────────

def cmd_fetch(args: argparse.Namespace) -> None:
    key = args.key.upper()
    print(f"🔍  Buscando card {key}...")

    data        = _get(f"/issue/{key}", {"fields": "summary,description,labels,attachment"})
    fields      = data.get("fields", {})
    title       = fields.get("summary", "")
    adf         = fields.get("description") or {}
    desc_text   = _adf_to_text(adf).strip()

    print(f"📋  Título: {title}")

    # ── BetterBugs — extrai mídia e links do ADF ──────────────────────────────
    bb = _extract_adf_media_and_links(adf)
    bb_screenshots: list[str] = []

    bb_session_data: dict = {}
    if any([bb["screenshots"], bb["betterbugs_session"], bb["source_url"]]):
        print("🐛  BetterBugs detectado no card:")
        if bb["betterbugs_session"]:
            print(f"    🔗 Sessão:        {bb['betterbugs_session']}")
        if bb["source_url"]:
            print(f"    🌐 Source URL:    {bb['source_url']}")
        if bb["console_logs_url"]:
            print(f"    📋 Console logs:  {bb['console_logs_url']}")
        if bb["network_logs_url"]:
            print(f"    🌐 Network logs:  {bb['network_logs_url']}")

        # ── API BetterBugs (vídeo + dados completos) ──────────────────────
        if bb["betterbugs_session"] and _betterbugs_api_token():
            print("    🎬 Buscando dados completos via API BetterBugs...")
            bb_session_data = _betterbugs_fetch_session(bb["betterbugs_session"])
            if bb_session_data.get("video_url"):
                print(f"       ✅ Vídeo: {bb_session_data['video_url']}")
            if bb_session_data.get("screenshots"):
                print(f"       ✅ {len(bb_session_data['screenshots'])} screenshot(s) adicionais")
            if bb_session_data.get("console_logs"):
                print(f"       ✅ {len(bb_session_data['console_logs'])} entradas de console log")
            if not any([bb_session_data.get("video_url"), bb_session_data.get("screenshots")]):
                print("       ⚠️  API respondeu mas sem dados de mídia — verifique os endpoints")
        elif bb["betterbugs_session"] and not _betterbugs_api_token():
            print("    💡 Configure BETTERBUGS_API_KEY para acessar vídeo e dados completos")

        # ── Screenshots do CDN (embedadas no ADF) ─────────────────────────
        if bb["screenshots"]:
            print(f"    📸 Baixando {len(bb['screenshots'])} screenshot(s) do CDN...")
            bb_screenshots = _download_betterbugs_screenshots(adf, key)
            for i, path in enumerate(bb_screenshots, 1):
                size = Path(path).stat().st_size
                print(f"       ✅ Screenshot {i}: {path} ({size:,} bytes)")
            if not bb_screenshots:
                print("       ⚠️  Nenhuma screenshot baixada (CDN inacessível?)")
    else:
        # Verifica anexos Jira convencionais
        attachments = fields.get("attachment", []) or []
        imgs = [a for a in attachments if a.get("mimeType", "").startswith("image/")]
        if imgs:
            print(f"📎  {len(imgs)} imagem(ns) anexada(s) ao card (sem BetterBugs inline):")
            for img in imgs:
                print(f"    → {img.get('filename')} — {img.get('content')}")

    # Detecta tela e elementos solicitados
    combined_text = f"{title} {desc_text}".lower()
    screen_key, screen = _detect_screen(combined_text)
    elements = _detect_elements(combined_text)

    if screen is None:
        print("\n⚠️  Não foi possível identificar a tela automaticamente.")
        print("    Telas disponíveis:")
        for k, v in SCREEN_MAP.items():
            print(f"      • {k} — {v['nome']}")
        print("\n    Adicione o nome da tela na descrição do card e tente novamente.")
        print("    Ou use --screen para forçar: --screen funil-de-talentos")
        if hasattr(args, "screen") and args.screen:
            screen_key = args.screen
            screen = SCREEN_MAP.get(screen_key)
        if screen is None:
            return

    print(f"🖥️   Tela identificada: {screen['nome']} ({screen_key})")
    print(f"🔎  Elementos detectados: {', '.join(elements)}")
    print(f"📂  Lendo {len(screen['react_files'])} arquivo(s) React...")

    found = sum(1 for f in screen["react_files"] if (REPLIT_ROOT / f).exists())
    print(f"    ✅ {found}/{len(screen['react_files'])} arquivo(s) encontrado(s)")

    template = _build_audit_template(key, title, desc_text, screen_key, screen, elements,
                                     bb_data=bb, bb_screenshots=bb_screenshots)

    output_file = getattr(args, "output_file", None)
    if output_file:
        Path(output_file).write_text(template, encoding="utf-8")
        print(f"\n✅  Template salvo em: {output_file}")
    else:
        print("\n" + "═" * 70)
        print(template)
        print("═" * 70)
        print(f"\n💡  Salve com: python scripts/design_audit_generator.py fetch {key} --output-file /tmp/audit-{key}.md")
        print(f"📤  Poste com: python scripts/design_audit_generator.py post  {key} --from-file /tmp/audit-{key}.md")

    print(f"\n🔗  Card: https://wedotalent.atlassian.net/browse/{key}")


def cmd_post(args: argparse.Namespace) -> None:
    key = args.key.upper()

    # Lê conteúdo da auditoria
    if getattr(args, "from_file", None):
        content = Path(args.from_file).read_text(encoding="utf-8")
    else:
        print("Paste o conteúdo da auditoria e pressione Ctrl+D:")
        content = sys.stdin.read()

    content = content.strip()
    if not content:
        sys.exit("❌  Conteúdo vazio.")

    # Converte para ADF
    new_nodes = _md_to_adf(content).get("content", [])
    print(f"📝  {len(new_nodes)} nó(s) ADF gerados a partir do conteúdo da auditoria.")

    if getattr(args, "dry_run", False):
        print(f"\n[DRY-RUN] Nós a adicionar: {len(new_nodes)}")
        print(json.dumps(new_nodes[:3], ensure_ascii=False, indent=2))
        print("  ... (dry-run — nada enviado)")
        return

    # Busca descrição atual
    print(f"🔍  Buscando descrição atual de {key}...")
    data   = _get(f"/issue/{key}", {"fields": "description"})
    fields = data.get("fields", {})
    adf    = fields.get("description") or {"version": 1, "type": "doc", "content": []}
    existing = adf.get("content", [])
    print(f"    → {len(existing)} nó(s) existentes na descrição.")

    # Append: separador + novos nós
    separator = {"type": "rule"}
    merged = existing + [separator] + new_nodes
    new_adf = {"version": 1, "type": "doc", "content": merged}

    print(f"📤  Atualizando descrição de {key} (append de auditoria)...")

    # ── Tenta PUT na descrição; fallback p/ comentário se CONTENT_LIMIT_EXCEEDED ──
    headers, jira_base = _get_auth()
    resp = requests.put(
        f"{jira_base}/issue/{key}",
        headers=headers,
        json={"fields": {"description": new_adf}},
        timeout=30,
    )
    if resp.ok or resp.status_code == 204:
        print(f"✅  Auditoria adicionada à descrição: https://wedotalent.atlassian.net/browse/{key}")
    elif resp.status_code == 400 and "CONTENT_LIMIT_EXCEEDED" in resp.text:
        print("⚠️  CONTENT_LIMIT_EXCEEDED — a descrição já está cheia.")
        print("📝  Tentando SUBSTITUIR a descrição com apenas a auditoria nova...")
        # Tenta substituir (sem os nós antigos) — mantém apenas separador + auditoria
        replace_adf = {"version": 1, "type": "doc", "content": new_nodes}
        resp2 = requests.put(
            f"{jira_base}/issue/{key}",
            headers=headers,
            json={"fields": {"description": replace_adf}},
            timeout=30,
        )
        if resp2.ok or resp2.status_code == 204:
            print(f"✅  Descrição substituída com auditoria: https://wedotalent.atlassian.net/browse/{key}")
        elif resp2.status_code == 400 and "CONTENT_LIMIT_EXCEEDED" in resp2.text:
            print("⚠️  Auditoria completa ainda é muito grande. Postando em comentário...")
            comment_adf = {"version": 1, "type": "doc", "content": new_nodes}
            resp3 = requests.post(
                f"{jira_base}/issue/{key}/comment",
                headers=headers,
                json={"body": comment_adf},
                timeout=30,
            )
            if resp3.ok:
                print(f"✅  Auditoria postada como COMENTÁRIO: https://wedotalent.atlassian.net/browse/{key}")
            else:
                print(f"❌  Falha ao postar comentário ({resp3.status_code}): {resp3.text[:300]}")
        else:
            print(f"❌  Falha ao substituir descrição ({resp2.status_code}): {resp2.text[:300]}")
    else:
        sys.exit(f"❌  Jira API {resp.status_code}: {resp.text[:300]}")

    # Labels
    labels_to_add = {"design-audit", "ds", "vuetify", "lia-v4"}
    cur_data   = _get(f"/issue/{key}", {"fields": "labels"})
    cur_labels = set(cur_data.get("fields", {}).get("labels") or [])
    new_labels = sorted(cur_labels | labels_to_add)
    _put_json(f"/issue/{key}", {"fields": {"labels": new_labels}})
    print(f"🏷️   Labels: {new_labels}")
    print(f"\n🔗  Card: https://wedotalent.atlassian.net/browse/{key}")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Design Audit Generator — auditoria completa de tela para Jira",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python scripts/design_audit_generator.py fetch WT-1640
  python scripts/design_audit_generator.py fetch WT-1640 --output-file /tmp/audit-WT-1640.md
  python scripts/design_audit_generator.py fetch WT-1640 --screen funil-de-talentos
  python scripts/design_audit_generator.py post  WT-1640 --from-file /tmp/audit-WT-1640.md
  python scripts/design_audit_generator.py post  WT-1640 --from-file /tmp/audit.md --dry-run

Telas disponíveis:
""" + "\n".join(f"  • {k}" for k in SCREEN_MAP),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_fetch = sub.add_parser("fetch", help="Gera template de auditoria a partir do card Jira")
    p_fetch.add_argument("key", help="Chave do card (ex: WT-1640)")
    p_fetch.add_argument("--output-file", "-o", help="Salva template em arquivo")
    p_fetch.add_argument("--screen", help="Força tela específica (ex: funil-de-talentos)")

    p_post = sub.add_parser("post", help="Posta auditoria preenchida na descrição do card")
    p_post.add_argument("key", help="Chave do card (ex: WT-1640)")
    p_post.add_argument("--from-file", "-f", help="Arquivo markdown com auditoria preenchida")
    p_post.add_argument("--dry-run", action="store_true", help="Pré-visualiza sem enviar")

    args = parser.parse_args()

    if args.cmd == "fetch":
        cmd_fetch(args)
    elif args.cmd == "post":
        cmd_post(args)


if __name__ == "__main__":
    main()
