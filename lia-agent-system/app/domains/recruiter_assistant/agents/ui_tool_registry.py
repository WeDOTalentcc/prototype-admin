"""UI tool registry — `open_ui` tool da superfície FEDERADA do chat da LIA.

Fase B (2026-06-06, decisão Paulo): mecanismo DETERMINÍSTICO (não marker
inferencial) para a LIA abrir modais/painéis. A tool valida a capability
contra o `capability_map.yaml` (single source of truth) e EMITE a diretiva
canônica `ui_action="open_modal"` com `modal_id` + `data`. O FE
(LIAGlobalModals) escuta `lia:open_modal` e monta o modal.

Multi-tenancy: company_id vem do ContextVar JWT (@tool_handler), NUNCA do
payload da LLM. Os entity_ids (candidate_id/job_id) vêm da LLM, mas a carga
de dados do modal é company-scoped no FE (proxy + JWT) — defense-in-depth.

HITL (decisão Paulo): capabilities com `requires_confirmation=true` (fechar
vaga, ação em massa, enviar comunicação, etc.) abrem o modal MAS a ação
dentro confirma. A flag viaja no payload p/ o FE/prompt sinalizar.

Sensor: tests/contract/test_open_ui_tool.py
"""
from __future__ import annotations

import logging
from typing import Any

from lia_agents_core.tool_adapter import ToolDefinition, ToolOutput

from app.shared.services.capability_map_service import CapabilityMapService
from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)

# Papéis privilegiados (staff WeDOTalent) sempre passam pelo role-gate.
_PRIVILEGED_ROLES = {"admin", "wedotalent_admin", "superadmin"}


def _role_allows(required_role: str, user_role: str | None) -> bool:
    """Role-gate fail-closed: cap restrita a um papel só passa se o user
    tem esse papel (ou é privilegiado). Sem role conhecido → nega (a cap
    restrita não vaza p/ quem não tem permissão)."""
    role = (user_role or "").strip().lower()
    if not role:
        return False
    if role in _PRIVILEGED_ROLES:
        return True
    return role == required_role.strip().lower()


def _ui_capabilities() -> dict[str, Any]:
    """Capabilities acionáveis via open_ui: têm modal_id (abre modal) OU
    navigate_page (navega pro surface onde a ação/seleção vive). DRY c/ yaml."""
    return {
        intent: cap
        for intent, cap in CapabilityMapService.load().items()
        if cap.modal_id or cap.navigate_page or cap.settings_section
    }


@tool_handler("ui")
async def _wrap_open_ui(**kwargs: Any) -> dict[str, Any]:
    """Abre um modal/painel da plataforma validando a capability canônica.

    Args (kwargs):
        capability: nome da capability (deve existir no capability_map e ter modal_id).
        entity_ids: dict com os ids exigidos (ex: {"candidate_id": "...", "job_id": "..."}).
        company_id: injetado pelo @tool_handler (ContextVar JWT).

    Returns dict no contrato de diretiva consumido por
    agentic_loop._extract_tool_directive → main_orchestrator:
        {"success", "data": {"ui_action": "open_modal", "ui_action_params": {...}}, "message"}
    """
    company_id = kwargs.get("company_id")
    if not company_id:
        return {
            "success": False,
            "needs_manual_review": True,
            "message": "company_id ausente do contexto JWT — operação bloqueada.",
        }

    capability = (kwargs.get("capability") or "").strip()
    entity_ids = kwargs.get("entity_ids") or {}
    if not isinstance(entity_ids, dict):
        entity_ids = {}

    cap = CapabilityMapService.get(capability)
    if cap is None:
        known = sorted(_ui_capabilities().keys())
        return {
            "success": False,
            "message": (
                f"Não conheço a capability '{capability}'. "
                f"Disponíveis: {', '.join(known)}."
            ),
            "data": {"navigate_fallback": None},
        }
    # Role-gate (decisão Paulo): cap restrita exige papel. Fail-closed.
    # Dormant até uma cap staff declarar required_role + tool_handler
    # injetar user_role no contexto. user_role NÃO vem da LLM.
    if cap.required_role and not _role_allows(cap.required_role, kwargs.get("user_role")):
        return {
            "success": False,
            "message": (
                "Essa tela é restrita à equipe WeDOTalent — seu perfil não "
                "tem permissão de acesso."
            ),
        }
    if cap.settings_section:
        # settings_open_tab: navega pra /configuracoes?section=X&subsection=Y
        # e dispara lia:settings-action para abrir a aba correta mesmo se
        # a página já estiver montada. FE (useUIAction) cuida disso.
        return {
            "success": True,
            "data": {
                "ui_action": "settings_open_tab",
                "ui_action_params": {
                    "section": cap.settings_section,
                    "subsection": cap.settings_subsection or "",
                },
            },
            "message": "Abrindo a seção de configurações...",
        }

    if not cap.modal_id:
        # Sem modal → navega pro surface (a ação/seleção vive na página, com
        # seu handler + confirmação = HITL preservado). Não duplica a lógica
        # de mutação da página no chat (CLAUDE.md single-source).
        if cap.navigate_page:
            nav_id = None
            for req in cap.entity_required:
                v = entity_ids.get(req.param)
                if v:
                    nav_id = v
                    break
            params: dict[str, Any] = {"page": cap.navigate_page}
            if nav_id:
                params["id"] = nav_id
            if cap.navigate_query:
                params["query"] = cap.navigate_query
            return {
                "success": True,
                "data": {"ui_action": "navigate_to", "ui_action_params": params},
                "message": "Te levando pra lá — você conclui a ação na tela.",
            }
        return {
            "success": False,
            "message": f"'{capability}' não tem modal nem destino de navegação.",
            "data": {"navigate_fallback": cap.navigate_fallback},
        }

    # Valida entidades exigidas (presença) — entity company-scoped no fetch do FE.
    missing = [
        req.param
        for req in cap.entity_required
        if not entity_ids.get(req.param)
    ]
    if missing:
        return {
            "success": False,
            "needs_params": True,
            "message": (
                f"Para abrir esse modal preciso de: {', '.join(missing)}. "
                "Me diga qual candidato/vaga (ou abra a partir do contexto)."
            ),
            "data": {
                "navigate_fallback": cap.navigate_fallback,
                "missing_params": missing,
            },
        }

    # Payload do modal: ids da LLM + company_id autoritativo do JWT (tenant).
    modal_data: dict[str, Any] = {
        k: v for k, v in entity_ids.items() if v is not None
    }
    modal_data["company_id"] = company_id
    if cap.requires_confirmation:
        # HITL: o FE/modal confirma a ação destrutiva antes de efetivá-la.
        modal_data["requires_confirmation"] = True

    return {
        "success": True,
        "data": {
            "ui_action": "open_modal",
            "ui_action_params": {
                "modal_id": cap.modal_id,
                "data": modal_data,
                "requires_confirmation": cap.requires_confirmation,
            },
        },
        "message": (
            "Abrindo para você."
            if not cap.requires_confirmation
            else "Vou abrir — você confirma a ação na tela (é uma ação que precisa de confirmação)."
        ),
    }


def _build_open_ui_definition() -> ToolDefinition:
    caps = _ui_capabilities()
    enum_caps = sorted(caps.keys())
    desc_lines = [
        "Abre um modal/painel da plataforma para o recrutador. Use quando o "
        "usuário pedir explicitamente para abrir/ver algo que é um modal "
        "(perfil, comparar, insights, score, fechar vaga, enviar comunicação, "
        "etc.). Passe a `capability` exata e os `entity_ids` necessários "
        "(candidate_id/job_id) do contexto — NUNCA invente ids. Capabilities "
        "com confirmação humana (fechar vaga, ação em massa, enviar mensagem) "
        "abrem o modal e a ação é confirmada na tela.",
        "Capabilities disponíveis: " + ", ".join(enum_caps) + ".",
    ]
    return ToolDefinition(
        name="open_ui",
        description="\n".join(desc_lines),
        parameters={
            "type": "object",
            "properties": {
                "capability": {
                    "type": "string",
                    "enum": enum_caps,
                    "description": "Capability canônica do modal a abrir.",
                },
                "entity_ids": {
                    "type": "object",
                    "description": (
                        "Ids exigidos pela capability (ex: {'candidate_id': '...'} "
                        "ou {'job_id': '...'}). Vazio quando a capability não exige."
                    ),
                },
            },
            "required": ["capability"],
        },
        output_schema=ToolOutput,
        function=_wrap_open_ui,
    )




# ---------------------------------------------------------------------------
# Fase 2 slice 1 — ponte in-page `apply_table_state`
# ---------------------------------------------------------------------------
# Tool DETERMINISTICA (irmã do open_ui) que NAO abre modal nem navega: filtra/
# busca/ordena a tabela de candidatos JA ABERTA na tela. Emite a diretiva
# canonica ui_action="apply_table_state" consumida por
# agentic_loop._extract_tool_directive; o FE escuta `lia:apply_table_state` e
# aplica o patch no useCandidatesStore.
#
# NAO passa pelo capability_map.yaml (apply_table_state nao e modal nem
# navigate). Read-only UI: nenhuma mutacao, nenhum HITL, nenhum DB read
# company-scoped. company_id vem do ContextVar (consistencia) mas NAO e usado
# e NUNCA contamina o patch.
#
# Slice 1 = surface "candidates" apenas. patch keys sao camelCase (FE contract):
# search, sortBy, sortOrder, quickFilters. Args sao snake_case (sort_by,
# sort_order, quick_filters) — mapeamos snake->camel e dropamos None/vazio.

_APPLY_TABLE_STATE_SURFACES = ("candidates", "jobs", "kanban", "talent_pool", "recrutar")
# Vocabulario VALIDO da lista de Vagas (surface jobs) — espelha o consumidor
# useJobsFilters.ts (activeFilter no filteredJobs). Emitir fora = no-op silencioso.
_VALID_JOB_FILTERS = (
    "todas",
    "ativas",
    "urgentes",
    "ats",
    "paralisadas",
    "concluidas",
    "canceladas",
)
# Vocabulario VALIDO do board Kanban (surface kanban) — espelha
# KanbanColumnRenderer.filteredCandidates (status/origin/workModel/score).
_VALID_KANBAN_STATUS = (
    "novo",
    "em_analise",
    "aguardando_aprovacao",
    "triado_aprovado",
    "negociacao",
)
_VALID_KANBAN_ORIGIN = ("web", "whatsapp", "sourcing", "ats")
_VALID_KANBAN_WORK_MODEL = ("remoto", "hibrido", "presencial")
_VALID_POOL_STAGES = (
    "discovered",
    "contacted",
    "screening",
    "screened",
    "ready",
)
_VALID_POOL_TABS = ("candidates", "sourcing", "agents", "config")

# Vocabulario VALIDO do funil (surface candidates) — espelha o consumidor
# useCandidatesFilterSort.ts. Emitir fora disso = patch dormente: o funil
# ignora silenciosamente (default return true / acesso a campo undefined).
# Falhar alto (msg ao usuario), nunca emitir um no-op com "success".
_VALID_SORT_BY = (
    "score",
    "name",
    "location",
    "current_company",
    "current_title",
    "years_of_experience",
    "activity",
)
_VALID_QUICK_FILTERS = ("frontend", "backend", "design", "senior", "remoto")
# Abas do Funil (surface candidates) — espelha o tipo ActiveTab do consumidor
# candidates-store.ts. Emitir fora disso = patch dormente (setActiveTab ignora).
_VALID_TABS = (
    "search",
    "favorites",
    "lists",
    "history",
    "saved-searches",
    "agents",
)


def _candidates_patch(kwargs: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    """Patch da surface 'candidates' (Funil). Retorna (patch, erro)."""
    patch: dict[str, Any] = {}
    search = kwargs.get("search")
    if search:
        patch["search"] = search
    sort_by = kwargs.get("sort_by")
    if sort_by:
        if sort_by not in _VALID_SORT_BY:
            return {}, (
                f"Não sei ordenar candidatos por '{sort_by}'. "
                f"Opções: {', '.join(_VALID_SORT_BY)}."
            )
        patch["sortBy"] = sort_by
    sort_order = kwargs.get("sort_order")
    if sort_order:
        patch["sortOrder"] = sort_order
    quick_filters = kwargs.get("quick_filters")
    if quick_filters:
        valid = [q for q in quick_filters if q in _VALID_QUICK_FILTERS]
        invalid = [q for q in quick_filters if q not in _VALID_QUICK_FILTERS]
        if invalid and not valid:
            return {}, (
                f"Filtro(s) rápido(s) desconhecido(s): {', '.join(invalid)}. "
                f"Disponíveis: {', '.join(_VALID_QUICK_FILTERS)}."
            )
        if valid:
            patch["quickFilters"] = valid
    tab = kwargs.get("tab")
    if tab:
        if tab not in _VALID_TABS:
            return {}, (
                f"Não conheço a aba '{tab}' do Funil. "
                f"Opções: {', '.join(_VALID_TABS)}."
            )
        patch["tab"] = tab
    return patch, None


def _jobs_patch(kwargs: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    """Patch da surface 'jobs' (lista de Vagas). Retorna (patch, erro).
    patch.search -> setSearchTerm; patch.filter -> setActiveFilter."""
    patch: dict[str, Any] = {}
    search = kwargs.get("search")
    if search:
        patch["search"] = search
    status_filter = kwargs.get("status_filter")
    if status_filter:
        if status_filter not in _VALID_JOB_FILTERS:
            return {}, (
                f"Não sei filtrar vagas por '{status_filter}'. "
                f"Opções: {', '.join(_VALID_JOB_FILTERS)}."
            )
        patch["filter"] = status_filter
    return patch, None


def _validate_multi(values: Any, vocab: tuple[str, ...], label: str) -> tuple[list[str] | None, str | None]:
    """Valida lista multi-select contra vocab. (validos, erro). Todos invalidos -> erro."""
    if not values:
        return None, None
    if not isinstance(values, list):
        values = [values]
    valid = [v for v in values if v in vocab]
    invalid = [v for v in values if v not in vocab]
    if invalid and not valid:
        return None, (
            f"{label} desconhecido(s): {', '.join(map(str, invalid))}. "
            f"Disponiveis: {', '.join(vocab)}."
        )
    return (valid or None), None


def _kanban_patch(kwargs: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    """Patch da surface 'kanban' (board da vaga aberta). Retorna (patch, erro).
    patch keys camelCase: search/scoreMin/statusFilter/originFilter/workModelFilter."""
    patch: dict[str, Any] = {}
    search = kwargs.get("search")
    if search:
        patch["search"] = search
    score_min = kwargs.get("score_min")
    if score_min is not None:
        try:
            sm = int(score_min)
        except (TypeError, ValueError):
            return {}, "score_min deve ser um numero de 0 a 100."
        if not 0 <= sm <= 100:
            return {}, "score_min deve estar entre 0 e 100."
        patch["scoreMin"] = sm
    status, err = _validate_multi(kwargs.get("status"), _VALID_KANBAN_STATUS, "Status")
    if err:
        return {}, err
    if status:
        patch["statusFilter"] = status
    origin, err = _validate_multi(kwargs.get("origin"), _VALID_KANBAN_ORIGIN, "Origem")
    if err:
        return {}, err
    if origin:
        patch["originFilter"] = origin
    wm, err = _validate_multi(kwargs.get("work_model"), _VALID_KANBAN_WORK_MODEL, "Modelo de trabalho")
    if err:
        return {}, err
    if wm:
        patch["workModelFilter"] = wm
    return patch, None




def _pool_patch(kwargs):
    patch = {}
    stage = kwargs.get("stage")
    if stage is not None:
        if stage not in _VALID_POOL_STAGES and stage not in ("all", ""):
            stages_str = ", ".join(_VALID_POOL_STAGES)
            return {}, (
                "Etapa " + repr(stage) + " invalida. Valores: " + stages_str +
                " ou null/all para mostrar todos."
            )
        patch["stage"] = None if stage in ("all", "") else stage
    tab = kwargs.get("pool_tab")
    if tab is not None:
        if tab not in _VALID_POOL_TABS:
            return {}, "Aba " + repr(tab) + " invalida. Valores: " + ", ".join(_VALID_POOL_TABS) + "."
        patch["tab"] = tab
    return patch, None


def _recrutar_patch(kwargs):
    patch = {}
    if "stage" in kwargs:
        stage = kwargs["stage"]
        if stage is not None and (not isinstance(stage, str) or len(stage) > 120):
            return {}, "O nome da etapa deve ser uma string curta."
        patch["stage"] = stage.strip() if isinstance(stage, str) else None
    return patch, None


@tool_handler("ui")
async def _wrap_apply_table_state(**kwargs: Any) -> dict[str, Any]:
    """Filtra/busca/ordena a tabela in-page (Fase 2 slice 1).

    Args (kwargs):
        surface: "candidates" (unico suportado no slice 1).
        search: termo de busca livre (opcional).
        sort_by: campo de ordenacao (opcional).
        sort_order: "asc" | "desc" (opcional).
        quick_filters: list[str] de filtros rapidos (opcional).
        tab: aba do Funil (opcional, SO candidates): search/favorites/
            lists/history/saved-searches/agents.
        company_id: injetado pelo @tool_handler (ContextVar JWT) — NAO usado.

    Returns dict no contrato de diretiva consumido por
    agentic_loop._extract_tool_directive:
        {"success", "data": {"ui_action": "apply_table_state",
         "ui_action_params": {"surface", "patch"}}, "message"}
    """
    surface = (kwargs.get("surface") or "candidates").strip()
    if surface not in _APPLY_TABLE_STATE_SURFACES:
        return {
            "success": False,
            "message": (
                f"Surface '{surface}' não suportada. Disponíveis: "
                f"{', '.join(_APPLY_TABLE_STATE_SURFACES)}."
            ),
        }

    if surface == "jobs":
        patch, err = _jobs_patch(kwargs)
        label = "vagas"
    elif surface == "kanban":
        patch, err = _kanban_patch(kwargs)
        label = "candidatos no board"
    elif surface == "talent_pool":
        patch, err = _pool_patch(kwargs)
        label = "candidatos no banco"
    elif surface == "recrutar":
        patch, err = _recrutar_patch(kwargs)
        label = "pipeline de recrutamento"
    else:
        patch, err = _candidates_patch(kwargs)
        label = "candidatos"
    if err:
        return {"success": False, "message": err}
    if not patch:
        return {
            "success": False,
            "message": (
                "Me diga o que aplicar na tabela: um termo de busca, um "
                "filtro ou uma ordenação."
            ),
        }

    return {
        "success": True,
        "data": {
            "ui_action": "apply_table_state",
            "ui_action_params": {"surface": surface, "patch": patch},
        },
        "message": f"Aplicando na tabela de {label}.",
    }


def _build_apply_table_state_definition() -> ToolDefinition:
    return ToolDefinition(
        name="apply_table_state",
        description=(
            "Filtra/busca/ordena a tabela de candidatos JÁ ABERTA na tela "
            "(não navega, não abre modal, não muta dados). Use quando o "
            "usuário, estando na tela do funil/candidatos, pedir para buscar, "
            "ordenar ou filtrar a lista visível. Funciona em DUAS telas "
            "(surface): 'candidates' (Funil — busca/ordena/filtros rápidos e troca de aba) e "
            "'jobs' (lista de Vagas — busca + status) e 'kanban' (board da vaga — busca/score/status/origem/modelo). Ex: 'ordene "
            "por score', 'mostre só os seniores', 'busca por João', 'abre os Favoritos', 'vai pra Buscas Salvas' (candidates); "
            "'mostre as vagas ativas', 'busca vaga de backend' (jobs). NÃO use "
            "para abrir perfil/modal (use open_ui) nem para navegar."
        ),
        parameters={
            "type": "object",
            "properties": {
                "surface": {
                    "type": "string",
                    "enum": list(_APPLY_TABLE_STATE_SURFACES),
                    "description": "Tela alvo: 'candidates' (Funil) ou 'jobs' (lista de Vagas).",
                },
                "search": {
                    "type": "string",
                    "description": "Termo de busca livre (opcional).",
                },
                "sort_by": {
                    "type": "string",
                    "enum": list(_VALID_SORT_BY),
                    "description": (
                        "Campo de ordenação (opcional). Apenas estes valores "
                        "são reconhecidos pelo funil."
                    ),
                },
                "sort_order": {
                    "type": "string",
                    "enum": ["asc", "desc"],
                    "description": "Direção da ordenação (opcional).",
                },
                "quick_filters": {
                    "type": "array",
                    "items": {"type": "string", "enum": list(_VALID_QUICK_FILTERS)},
                    "description": (
                        "Filtros rápidos a aplicar (opcional, SÓ candidates). "
                        "Valores: frontend, backend, design, senior, remoto."
                    ),
                },
                "tab": {
                    "type": "string",
                    "enum": list(_VALID_TABS),
                    "description": (
                        "Aba do Funil: search=Buscar, favorites=Favoritos, "
                        "lists=Listas, history=Histórico, saved-searches=Buscas "
                        "Salvas, agents=Agentes (opcional, SÓ candidates)."
                    ),
                },
                "status_filter": {
                    "type": "string",
                    "enum": list(_VALID_JOB_FILTERS),
                    "description": (
                        "Filtro de status da lista de Vagas (opcional, SÓ jobs): "
                        "todas/ativas/urgentes/ats/paralisadas/concluidas/canceladas."
                    ),
                },
                "score_min": {
                    "type": "integer",
                    "description": "Score LIA minimo 0-100 (opcional, SÓ kanban).",
                },
                "status": {
                    "type": "array",
                    "items": {"type": "string", "enum": list(_VALID_KANBAN_STATUS)},
                    "description": (
                        "Status do candidato no board (opcional, SÓ kanban): "
                        "novo/em_analise/aguardando_aprovacao/triado_aprovado/negociacao."
                    ),
                },
                "origin": {
                    "type": "array",
                    "items": {"type": "string", "enum": list(_VALID_KANBAN_ORIGIN)},
                    "description": "Origem do candidato (opcional, SÓ kanban): web/whatsapp/sourcing/ats.",
                },
                "work_model": {
                    "type": "array",
                    "items": {"type": "string", "enum": list(_VALID_KANBAN_WORK_MODEL)},
                    "description": "Modelo de trabalho (opcional, SÓ kanban): remoto/hibrido/presencial.",
                },
                "stage": {
                    "type": ["string", "null"],
                    "description": (
                        "Etapa a selecionar/filtrar (opcional). "
                        "talent_pool: discovered/contacted/screening/screened/ready ou null=todos. "
                        "recrutar: nome exato da etapa do pipeline (ex: 'triagem_whatsapp') ou null=deseleciona."
                    ),
                },
                "pool_tab": {
                    "type": "string",
                    "enum": list(_VALID_POOL_TABS),
                    "description": "Aba do banco de talentos (opcional, SÓ talent_pool): candidates/sourcing/agents/config.",
                },
            },
            "required": ["surface"],
        },
        output_schema=ToolOutput,
        function=_wrap_apply_table_state,
    )


# ---------------------------------------------------------------------------
# Fase 2 surface close --- select_rows
# ---------------------------------------------------------------------------
_VALID_SELECT_MODES = ("set", "add", "clear")
_MAX_SELECTION_IDS = 200


@tool_handler("ui")
async def _wrap_select_rows(**kwargs):
    """Seleciona candidatos na tabela (pre-marca para bulk action).
    mode=set: substitui selecao pelos IDs fornecidos.
    mode=add: adiciona IDs a selecao existente.
    mode=clear: limpa toda a selecao.
    Nao muta dados - apenas estado UI in-page. Sem HITL gate.
    """
    surface = kwargs.get("surface")
    if surface != "candidates":
        msg = f"surface={surface!r} nao suportada. Use candidates."
        return {"success": False, "error": msg, "message": msg}

    mode = kwargs.get("mode")
    if mode not in _VALID_SELECT_MODES:
        modes_str = ", ".join(_VALID_SELECT_MODES)
        msg = f"mode={mode!r} invalido. Valores: {modes_str}."
        return {"success": False, "error": msg, "message": msg}

    ids = kwargs.get("candidate_ids")
    if mode in ("set", "add"):
        if not ids or not isinstance(ids, list):
            msg = f"candidate_ids obrigatorio e nao-vazio para mode={mode!r}."
            return {"success": False, "error": msg, "message": msg}
        if len(ids) > _MAX_SELECTION_IDS:
            msg = (
                f"Maximo de {_MAX_SELECTION_IDS} IDs por vez "
                f"(recebido: {len(ids)})."
            )
            return {"success": False, "error": msg, "message": msg}

    params = {"surface": surface, "mode": mode}
    if mode != "clear":
        params["ids"] = ids

    count = len(ids) if ids else 0
    message = (
        f"{count} candidato(s) selecionado(s)." if mode == "set"
        else f"{count} candidato(s) adicionado(s) a selecao." if mode == "add"
        else "Selecao limpa."
    )

    return {
        "success": True,
        "data": {
            "ui_action": "select_rows",
            "ui_action_params": params,
        },
        "message": message,
    }


def _build_select_rows_definition():
    return ToolDefinition(
        name="select_rows",
        description=(
            "Seleciona candidatos especificos na tabela do Funil (in-page, sem mutacao de dados). "
            "Use para pre-marcar candidatos antes de propor uma acao em lote (bulk). "
            "mode=set: define selecao exata. mode=add: acrescenta a selecao existente. "
            "mode=clear: limpa toda a selecao."
        ),
        parameters={
            "type": "object",
            "properties": {
                "surface": {
                    "type": "string",
                    "enum": ["candidates"],
                    "description": "Superficie a selecionar (somente candidates nesta versao).",
                },
                "mode": {
                    "type": "string",
                    "enum": list(_VALID_SELECT_MODES),
                    "description": "Modo de selecao: set=substitui, add=acrescenta, clear=limpa.",
                },
                "candidate_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Lista de UUIDs dos candidatos a selecionar. "
                        "Obrigatorio para mode=set e mode=add. Max: 200 IDs."
                    ),
                },
            },
            "required": ["surface", "mode"],
        },
        output_schema=ToolOutput,
        function=_wrap_select_rows,
    )


def get_ui_tools() -> list[ToolDefinition]:
    """ToolDefinitions de UI (open_ui + apply_table_state + select_rows). Federadas no recruiter_copilot."""
    return [_build_open_ui_definition(), _build_apply_table_state_definition(), _build_select_rows_definition()]


def get_open_ui_tools() -> list[ToolDefinition]:
    """So open_ui (abre modal / navega). capability_map-gated + HITL nas acoes
    sensiveis -> seguro p/ conceder a qualquer agente CONVERSACIONAL via grant
    explicito no _get_tools do agente (least-privilege, removivel)."""
    return [_build_open_ui_definition()]


def get_table_state_tools() -> list[ToolDefinition]:
    """So apply_table_state (filtra/ordena/busca tabela in-page). Conceder APENAS
    a agentes cuja surface TEM ponte FE (anti-ghost): hoje a surface 'candidates'
    (Funil). jobs/kanban/pools entram quando a ponte da surface deles existir."""
    return [_build_apply_table_state_definition(), _build_select_rows_definition()]


def register_ui_tools_global() -> int:
    """Registra ui tools no tool_registry GLOBAL (consumido pelo agentic_loop —
    caminho supervisor Phase 1.5). O caminho federado usa get_ui_tools() via
    federacao e NAO depende disto.

    Registra open_ui + apply_table_state (simetria: o supervisor Phase 1.5
    agentic_loop alcanca os mesmos ui tools que o federado). Adapter: lia_agents_core.ToolDefinition -> a ToolDefinition
    do app.tools.registry (campos distintos: parameters->parameters_schema,
    function->handler). Idempotente (o registry sobrescreve por nome)."""
    from app.tools.registry import ToolDefinition as _GlobalToolDef
    from app.tools.registry import tool_registry as _global_registry

    n = 0
    for td in get_ui_tools():
        _global_registry.register(
            _GlobalToolDef(
                name=td.name,
                description=td.description,
                parameters_schema=td.parameters,
                handler=td.function,
                allowed_agents=[
                    "recruiter_assistant",
                    "recruiter_copilot",
                    "orchestrator",
                ],
                requires_confirmation=False,
            )
        )
        n += 1
    return n
