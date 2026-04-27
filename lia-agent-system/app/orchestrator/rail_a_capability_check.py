"""
rail_a_capability_check — PR-J Phase 0.5 gate.

harness-engineering guide computacional:
When a Rail A message carries intent_hint, check capability_map.yaml BEFORE
routing to any agent. Non-chat-executable intents return ui_action immediately
(no LLM call, no keyword guessing). Chat-executable intents with entity_required
resolve the entity via SQL and enrich context in-place.

Multi-tenant: all DB queries pass company_id. Max 2 disambiguation steps
before suggesting navigation fallback.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_UI_ACTION_NAVIGATE = "navigate_to"
_UI_ACTION_OPEN_MODAL = "open_modal"


async def check_rail_a_capability(
    context: dict[str, Any],
    message: str,
    company_id: str,
    db: Any,
) -> dict[str, Any] | None:
    """Check Rail A intent_hint against capability_map and short-circuit if needed.

    Returns:
        dict  — WS response payload to send directly (caller must `continue`)
        None  — normal processing should proceed
    """
    # PR-A sends metadata nested: context = { metadata: { intent_hint, source, ... } }
    _meta: dict = context.get("metadata") or {}
    intent_hint: str | None = _meta.get("intent_hint") or context.get("intent_hint")
    source: str = _meta.get("source") or context.get("source", "")

    if not intent_hint or source != "rail_a":
        return None

    try:
        from app.shared.services.capability_map_service import CapabilityMapService
        cap = CapabilityMapService.get(intent_hint)
    except Exception as _load_exc:
        logger.warning("[PR-J] CapabilityMapService load failed: %s", _load_exc)
        return None

    if cap is None:
        logger.debug("[PR-J] intent_hint=%r not in capability_map — fallthrough", intent_hint)
        return None

    logger.info(
        "[PR-J] Rail A intent_hint=%r chat_executable=%s source=%s",
        intent_hint, cap.chat_executable, source,
    )

    # ── Non-chat-executable: return ui_action immediately (no agent call) ──
    if not cap.chat_executable:
        if cap.modal_id:
            return {
                "type": "message",
                "content": _build_modal_message(intent_hint, cap.modal_id),
                "ui_action": _UI_ACTION_OPEN_MODAL,
                "ui_action_params": {"modal_id": cap.modal_id},
                "confidence": 1.0,
                "domain": "capability_map",
                "source": "rail_a_gate",
            }
        if cap.navigate_fallback:
            return {
                "type": "message",
                "content": f"Abrindo a tela correspondente...",
                "ui_action": _UI_ACTION_NAVIGATE,
                "ui_action_params": {"page": cap.navigate_fallback},
                "confidence": 1.0,
                "domain": "capability_map",
                "source": "rail_a_gate",
            }

    # ── Chat-executable with entity_required: resolve entity and enrich context ──
    if cap.entity_required and db is not None:
        try:
            enriched = await _resolve_required_entities(
                entity_requirements=cap.entity_required,
                message=message,
                context=context,
                company_id=company_id,
                db=db,
            )
            if enriched is not None:
                return enriched
        except Exception as _ent_exc:
            logger.warning("[PR-J] Entity resolution failed (non-blocking): %s", _ent_exc)

    return None


async def _resolve_required_entities(
    entity_requirements: list,
    message: str,
    context: dict[str, Any],
    company_id: str,
    db: Any,
) -> dict[str, Any] | None:
    """Try to resolve required entities from the message.

    Returns response dict if disambiguation/navigation needed, None if resolved.
    Enriches context in-place with resolved entity data when found.
    """
    from app.shared.services.entity_resolver_service import EntityResolverService

    for req in entity_requirements:
        entity_type: str = req.type
        param_key: str = req.param

        # Skip if already provided in context
        if context.get(param_key) or context.get("entity_id"):
            continue

        resolution = await EntityResolverService.resolve(
            entity_type=entity_type,
            hint=message,
            company_id=company_id,
            db=db,
        )

        if resolution.resolved:
            # Enrich context with resolved entity — next agent call will have it
            context[param_key] = resolution.entity_id
            context["entity_id"] = resolution.entity_id
            context["entity_type"] = entity_type
            if resolution.preview:
                context[f"{entity_type}_preview"] = resolution.preview
            logger.info(
                "[PR-J] Entity resolved: type=%s id=%s",
                entity_type, resolution.entity_id,
            )
            continue

        if resolution.ambiguous:
            # Build disambiguation message showing up to 3 options
            options_text = "\n".join(
                f"- **{c['name']}** (etapa: {c.get('stage', '?')})"
                for c in resolution.candidates_preview
            )
            return {
                "type": "message",
                "content": (
                    f"Encontrei {len(resolution.candidates_preview)} candidatos com esse nome. "
                    f"Qual você quer?\n\n{options_text}"
                ),
                "confidence": 0.6,
                "domain": "entity_resolver",
                "source": "disambiguation",
            }

        # Not found — suggest navigation
        navigate = resolution.navigate_to or "/funil-de-talentos"
        return {
            "type": "message",
            "content": (
                "Não encontrei esse candidato. "
                "Tente buscar pelo nome completo ou abrir a tela de candidatos."
            ),
            "ui_action": _UI_ACTION_NAVIGATE,
            "ui_action_params": {"page": navigate},
            "confidence": 0.5,
            "domain": "entity_resolver",
            "source": "not_found",
        }

    return None


def _build_modal_message(intent_hint: str, modal_id: str) -> str:
    _labels: dict[str, str] = {
        "add_candidate": "Abrindo o formulário para adicionar candidato...",
        "stage_transition": "Abrindo o painel de transição de etapa...",
        "interview_scheduling": "Abrindo o agendador de entrevistas...",
        "candidate_compare": "Abrindo a tela de comparação de candidatos...",
    }
    return _labels.get(modal_id, f"Abrindo {modal_id.replace('_', ' ')}...")
