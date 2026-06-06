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


def _modal_capabilities() -> dict[str, Any]:
    """Capabilities que têm modal_id (abríveis via open_ui). DRY com o yaml."""
    return {
        intent: cap
        for intent, cap in CapabilityMapService.load().items()
        if cap.modal_id
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
    if cap is None or not cap.modal_id:
        # Falha ALTO honesta (REGRA 4) — não inventar modal. Oferece fallback.
        known = sorted(_modal_capabilities().keys())
        return {
            "success": False,
            "message": (
                f"Não conheço um modal para '{capability}'. "
                f"Capabilities com modal disponíveis: {', '.join(known)}."
            ),
            "data": {"navigate_fallback": cap.navigate_fallback if cap else None},
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
    caps = _modal_capabilities()
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


def get_ui_tools() -> list[ToolDefinition]:
    """ToolDefinitions de UI (open_ui). Federadas no recruiter_copilot."""
    return [_build_open_ui_definition()]
