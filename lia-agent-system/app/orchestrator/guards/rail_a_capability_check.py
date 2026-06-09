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
            # B3b fix (2026-06-09): enrich ui_action_params.data with entity_ids
            # so LiaEntityModalHost can fetch the entity before opening the modal.
            modal_data = await _collect_entity_ids_for_modal(
                entity_requirements=cap.entity_required,
                meta=_meta,
                context=context,
                message=message,
                company_id=company_id,
                db=db,
            )
            if isinstance(modal_data, dict) and "_redirect" in modal_data:
                return modal_data["_redirect"]
            # If entity_required and core params still missing → honest navigate fallback
            if cap.entity_required:
                _missing = [r.param for r in cap.entity_required if not (modal_data or {}).get(r.param)]
                if _missing and cap.navigate_fallback:
                    logger.info(
                        "[PR-J] entity_required params missing %s for %r — navigate fallback",
                        _missing, intent_hint,
                    )
                    return {
                        "type": "message",
                        "content": (
                            "Para abrir esse painel preciso saber qual vaga ou candidato. "
                            "Me diga o nome ou abra primeiro."
                        ),
                        "ui_action": _UI_ACTION_NAVIGATE,
                        "ui_action_params": {"page": cap.navigate_fallback},
                        "confidence": 0.7,
                        "domain": "capability_map",
                        "source": "rail_a_gate",
                    }
            return {
                "type": "message",
                "content": _build_modal_message(intent_hint, cap.modal_id),
                "ui_action": _UI_ACTION_OPEN_MODAL,
                "ui_action_params": {
                    "modal_id": cap.modal_id,
                    "data": {**(modal_data or {}), "company_id": company_id},
                },
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


async def _collect_entity_ids_for_modal(
    entity_requirements: list,
    meta: dict,
    context: dict,
    message: str,
    company_id: str,
    db: Any,
) -> dict:
    """Collect entity_ids for a non-chat-executable modal.

    Precedence: FE metadata.entity_ids > individual params in meta/context
    > entity resolver (message text) > empty dict (caller decides fallback).

    Returns:
        dict  — entity param keys mapped to ids, possibly empty
        {"_redirect": response_dict}  — when resolution needs user input
    """
    if not entity_requirements:
        return {}

    entity_ids: dict = {}

    # 1. FE-provided entity_ids dict (injected by lia-float-context entityContext)
    meta_entity_ids = meta.get("entity_ids") or {}
    if isinstance(meta_entity_ids, dict):
        entity_ids.update({k: str(v) for k, v in meta_entity_ids.items() if v})

    # 2. Individual param names in meta or context
    for req in entity_requirements:
        if entity_ids.get(req.param):
            continue
        typed_match = (
            meta.get("entity_id")
            if str(meta.get("entity_type", "")) == req.type
            else (
                context.get("entity_id")
                if str(context.get("entity_type", "")) == req.type
                else None
            )
        )
        val = meta.get(req.param) or context.get(req.param) or typed_match
        if val:
            entity_ids[req.param] = str(val)

    # 3. Entity resolver from message text if still missing
    missing = [r.param for r in entity_requirements if not entity_ids.get(r.param)]
    if missing and db is not None:
        try:
            _resolve_ctx: dict = {**context}
            _missing_reqs = [r for r in entity_requirements if r.param in missing]
            resolve_response = await _resolve_required_entities(
                entity_requirements=_missing_reqs,
                message=message,
                context=_resolve_ctx,
                company_id=company_id,
                db=db,
            )
            if resolve_response is not None:
                return {"_redirect": resolve_response}
            for req in _missing_reqs:
                if _resolve_ctx.get(req.param):
                    entity_ids[req.param] = str(_resolve_ctx[req.param])
        except Exception as _exc:
            logger.warning("[PR-J] _collect_entity_ids_for_modal resolver: %s", _exc)

    return entity_ids


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

        # Not found — suggest navigation if a valid route is available.
        # Post-mortem 2026-04-29 Bug 4: previous fallback was
        # "/funil-de-talentos" — a dead route in the App Router migration
        # (404). Route now through safe_navigate_route so producers can
        # never emit dead URLs. Default fallback is "/teams-tab/candidatos"
        # (the canonical candidate list page); if even that is invalid the
        # ui_action is omitted entirely so the user just sees the message.
        from app.shared.navigation_routes import (
            safe_navigate_route,
            validate_navigate_route,
        )
        candidate_path = resolution.navigate_to or "/teams-tab/candidatos"
        navigate = safe_navigate_route(candidate_path)
        response: dict[str, Any] = {
            "type": "message",
            "content": (
                "Não encontrei esse candidato. "
                "Tente buscar pelo nome completo ou abrir a tela de candidatos."
            ),
            "confidence": 0.5,
            "domain": "entity_resolver",
            "source": "not_found",
        }
        if validate_navigate_route(navigate):
            response["ui_action"] = _UI_ACTION_NAVIGATE
            response["ui_action_params"] = {"page": navigate}
        return response

    return None


def _build_modal_message(intent_hint: str, modal_id: str) -> str:
    _labels: dict[str, str] = {
        "add_candidate": "Abrindo o formulário para adicionar candidato...",
        "stage_transition": "Abrindo o painel de transição de etapa...",
        "interview_scheduling": "Abrindo o agendador de entrevistas...",
        "candidate_compare": "Abrindo a tela de comparação de candidatos...",
    }
    return _labels.get(modal_id, f"Abrindo {modal_id.replace('_', ' ')}...")
