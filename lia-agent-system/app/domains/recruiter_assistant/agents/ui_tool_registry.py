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
        if cap.modal_id or cap.navigate_page
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

_APPLY_TABLE_STATE_SURFACES = ("candidates",)

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


@tool_handler("ui")
async def _wrap_apply_table_state(**kwargs: Any) -> dict[str, Any]:
    """Filtra/busca/ordena a tabela in-page (Fase 2 slice 1).

    Args (kwargs):
        surface: "candidates" (unico suportado no slice 1).
        search: termo de busca livre (opcional).
        sort_by: campo de ordenacao (opcional).
        sort_order: "asc" | "desc" (opcional).
        quick_filters: list[str] de filtros rapidos (opcional).
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
                "Por enquanto só sei filtrar/ordenar a tabela de candidatos "
                f"(surface 'candidates') — '{surface}' ainda não é suportado."
            ),
        }

    # snake_case (arg) -> camelCase (patch FE). Dropa None/vazio.
    patch: dict[str, Any] = {}
    search = kwargs.get("search")
    if search:
        patch["search"] = search
    sort_by = kwargs.get("sort_by")
    if sort_by:
        if sort_by not in _VALID_SORT_BY:
            # Falha alto: nao emitir um sort que o funil ignora em silencio.
            return {
                "success": False,
                "message": (
                    f"Não sei ordenar candidatos por '{sort_by}'. "
                    f"Opções: {', '.join(_VALID_SORT_BY)}."
                ),
            }
        patch["sortBy"] = sort_by
    sort_order = kwargs.get("sort_order")
    if sort_order:
        patch["sortOrder"] = sort_order
    quick_filters = kwargs.get("quick_filters")
    if quick_filters:
        valid = [q for q in quick_filters if q in _VALID_QUICK_FILTERS]
        invalid = [q for q in quick_filters if q not in _VALID_QUICK_FILTERS]
        if invalid and not valid:
            # Todos invalidos: nao fingir sucesso com filtro que nao filtra.
            return {
                "success": False,
                "message": (
                    f"Filtro(s) rápido(s) desconhecido(s): {', '.join(invalid)}. "
                    f"Disponíveis: {', '.join(_VALID_QUICK_FILTERS)}."
                ),
            }
        if valid:
            patch["quickFilters"] = valid

    if not patch:
        return {
            "success": False,
            "message": (
                "Me diga o que aplicar na tabela: um termo de busca, uma "
                "ordenação (ex: por score) ou um filtro rápido."
            ),
        }

    return {
        "success": True,
        "data": {
            "ui_action": "apply_table_state",
            "ui_action_params": {"surface": surface, "patch": patch},
        },
        "message": "Aplicando na tabela de candidatos.",
    }


def _build_apply_table_state_definition() -> ToolDefinition:
    return ToolDefinition(
        name="apply_table_state",
        description=(
            "Filtra/busca/ordena a tabela de candidatos JÁ ABERTA na tela "
            "(não navega, não abre modal, não muta dados). Use quando o "
            "usuário, estando na tela do funil/candidatos, pedir para buscar, "
            "ordenar ou filtrar a lista visível (ex: 'ordene por score', "
            "'mostre só os seniores', 'busca por João'). NÃO use para abrir "
            "perfil/modal (use open_ui) nem para navegar."
        ),
        parameters={
            "type": "object",
            "properties": {
                "surface": {
                    "type": "string",
                    "enum": list(_APPLY_TABLE_STATE_SURFACES),
                    "description": "Superfície da tabela. Slice 1: 'candidates'.",
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
                        "Filtros rápidos a aplicar (opcional). Valores válidos: "
                        "frontend, backend, design, senior, remoto."
                    ),
                },
            },
            "required": ["surface"],
        },
        output_schema=ToolOutput,
        function=_wrap_apply_table_state,
    )


def get_ui_tools() -> list[ToolDefinition]:
    """ToolDefinitions de UI (open_ui + apply_table_state). Federadas no recruiter_copilot."""
    return [_build_open_ui_definition(), _build_apply_table_state_definition()]


def get_open_ui_tools() -> list[ToolDefinition]:
    """So open_ui (abre modal / navega). capability_map-gated + HITL nas acoes
    sensiveis -> seguro p/ conceder a qualquer agente CONVERSACIONAL via grant
    explicito no _get_tools do agente (least-privilege, removivel)."""
    return [_build_open_ui_definition()]


def get_table_state_tools() -> list[ToolDefinition]:
    """So apply_table_state (filtra/ordena/busca tabela in-page). Conceder APENAS
    a agentes cuja surface TEM ponte FE (anti-ghost): hoje a surface 'candidates'
    (Funil). jobs/kanban/pools entram quando a ponte da surface deles existir."""
    return [_build_apply_table_state_definition()]


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
