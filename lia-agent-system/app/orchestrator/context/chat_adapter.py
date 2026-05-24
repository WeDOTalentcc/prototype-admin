"""
ChatAdapter — Bridge between chat.py (REST) and MainOrchestrator.

Path A migration: converts chat.py raw params <-> MainOrchestrator
UniversalContext/ChatResponse, preserving the exact API contract
the frontend expects.

Passo 2 of Path A: skip_memory_persist=True (ChatRepository remains owner).
Passo 3 (M2): flip to skip_memory_persist=False.
"""
from __future__ import annotations

import logging
from typing import Any

from app.orchestrator.context.context_adapter import ContextAdapter, UniversalContext
from app.orchestrator.execution.main_orchestrator import MainOrchestrator

logger = logging.getLogger(__name__)


class ChatAdapter:
    """
    Adapter between chat.py REST endpoint and MainOrchestrator.

    Input:  exactly what chat.py passes today (raw strings + page_context dict)
    Output: exactly what _invoke_orchestrator() returned (dict with response/intent/entities/workflow_data)
    """

    def __init__(self, main_orchestrator: MainOrchestrator):
        self._orch = main_orchestrator

    async def process_message(
        self,
        *,
        user_message: str,
        user_id: str,
        company_id: str,
        conversation_id: str | None = None,
        page_context: dict[str, Any] | None = None,
        db: Any = None,
    ) -> dict[str, Any]:
        """
        Process a user message through MainOrchestrator and return
        a dict compatible with what chat.py expects from _invoke_orchestrator().
        """
        # ── Step 1: Build UniversalContext from raw params ──
        ctx = self._build_context(
            user_message=user_message,
            user_id=user_id,
            company_id=company_id,
            conversation_id=conversation_id,
            page_context=page_context,
        )

        # ── Step 2: Call MainOrchestrator ──
        try:
            orch_response = await self._orch.process(ctx, db)
        except Exception as exc:
            logger.error(f"[ChatAdapter] MainOrchestrator failed: {exc}", exc_info=True)
            return self._error_response(str(exc))

        # ── Step 3: Convert ChatResponse → dict ──
        return self._convert_response(orch_response)

    # ──────────────────────────────────────────────────────────────────
    # Input conversion: raw params → UniversalContext
    # ──────────────────────────────────────────────────────────────────

    def _build_context(
        self,
        *,
        user_message: str,
        user_id: str,
        company_id: str,
        conversation_id: str | None,
        page_context: dict[str, Any] | None,
    ) -> UniversalContext:
        """Build UniversalContext from chat.py raw parameters."""
        pc = page_context or {}

        # Extract entity_id from page_context (job_vacancy_id or job_id)
        entity_id = pc.get("job_vacancy_id") or pc.get("job_id")
        entity_type = "job" if entity_id else None

        # G1 canonical fix (2026-05-24): normalize incoming page_type via
        # canonical_pages so legacy frontend vocabularies (kanban,
        # candidates, settings_config) and missing-page (None) all map to
        # a known CanonicalPage value.
        from app.shared.canonical_pages import normalize_page

        ctx = ContextAdapter.from_rest(
            message=user_message,
            user_id=user_id,
            company_id=str(company_id) if company_id else "",
            conversation_id=conversation_id,
            context_page=normalize_page(pc.get("page_type")).value,
            entity_id=str(entity_id) if entity_id else None,
            entity_type=entity_type,
            selected_candidate_ids=pc.get("candidate_ids"),
            job_context=pc.get("job_context"),
        )

        # Passo 2: ChatRepository remains memory owner until M2
        ctx.skip_memory_persist = False  # M2: MainOrchestrator owns persistence

        return ctx

    # ──────────────────────────────────────────────────────────────────
    # Output conversion: MainOrchestrator ChatResponse → dict
    # ──────────────────────────────────────────────────────────────────

    def _convert_response(self, orch_response: Any) -> dict[str, Any]:
        """
        Convert MainOrchestrator ChatResponse to the dict format
        that chat.py expects from _invoke_orchestrator().

        Keys expected by chat.py:
        - response: str (LIA response text)
        - intent: str
        - entities: dict
        - workflow_data: dict
        - prompt_version: str
        - action_result: dict | None (new)
        - pending_action: dict | None (new)
        - fairness_warnings: list[str] (new)
        - from_cache: bool (new)
        """
        result: dict[str, Any] = {
            "response": getattr(orch_response, "content", "") or "",
            "intent": getattr(orch_response, "intent_detected", "general"),
            "entities": {},
            "workflow_data": {},
            "prompt_version": getattr(orch_response, "agent_used", "main_orchestrator"),
            "fairness_warnings": getattr(orch_response, "fairness_warnings", []),
            "from_cache": getattr(orch_response, "from_cache", False),
        }

        # G3 canonical fix (2026-05-24): extract [NAVIGATE:<page>] marker
        # from LLM raw output and promote to ui_action shape (same contract
        # ACTIONABLE_INTENTS / Rail A use). Strips marker from response text
        # so user only sees natural-language content.
        _extracted = _extract_navigate_marker(result["response"])
        if _extracted is not None:
            _clean_text, _canonical_page = _extracted
            result["response"] = _clean_text
            # Only emit ui_action when canonical_page is a known page.
            # Unknown pages resolve to general — strip the marker but
            # do not trigger frontend navigation.
            if _canonical_page != "general":
                result["ui_action"] = "navigate_to"
                result["ui_action_params"] = {"page": _canonical_page}

        # ── Structured data → workflow_data ──
        structured = getattr(orch_response, "structured_data", None)
        if structured:
            result["workflow_data"] = structured

        # ── Action result (from MainOrchestrator Phase 0+1) ──
        action_result = getattr(orch_response, "action_result", None)
        if action_result:
            result["action_result"] = action_result

        # ── Pending action (reconstruct dict format chat.py uses) ──
        pending_id = getattr(orch_response, "pending_action_id", None)
        if pending_id:
            result["pending_action"] = {
                "pending_id": pending_id,
                "intent": getattr(orch_response, "intent_detected", ""),
                "awaiting_confirmation": getattr(orch_response, "needs_confirmation", False),
                "missing_params": getattr(orch_response, "needs_params", False),
            }

        # ── Success check — blocked responses ──
        success = getattr(orch_response, "success", True)
        if not success:
            intent = getattr(orch_response, "intent_detected", "")
            if "blocked_bias" in intent or "blocked_security" in intent:
                # FairnessGuard or SecurityPatterns blocked — return as
                # normal response (educational message), not HTTP error
                result["blocked"] = True
                result["block_reason"] = intent

        return result

    # ──────────────────────────────────────────────────────────────────
    # Error fallback
    # ──────────────────────────────────────────────────────────────────

    def _error_response(self, error_msg: str) -> dict[str, Any]:
        """Return error dict compatible with chat.py expectations."""
        return {
            "response": "Desculpe, ocorreu um erro interno. Tente novamente em alguns instantes.",
            "intent": "error",
            "entities": {},
            "workflow_data": {},
            "prompt_version": "chat_adapter_error",
            "error": error_msg,
        }


# ───────────────────────────────────────────────────────────────────────
# G3 canonical fix (2026-05-24) — navigation marker post-processor
# ───────────────────────────────────────────────────────────────────────

def _extract_navigate_marker(text: str):
    """Extract [NAVIGATE:<page>] marker from LLM raw response.

    Returns:
        (clean_text, canonical_page_id) when marker present (canonical_page_id
        is always a valid CanonicalPage value string — unknown pages
        resolve to 'general').
        None when no marker is found in text.

    Single marker per response (first match wins). Marker stripped from
    returned text. canonical_page_id is normalized via canonical_pages
    so legacy aliases (kanban → pipeline_kanban, candidates →
    candidato_detalhe, settings_config → configuracoes) resolve correctly.

    Contract documented in system_prompt_builder.py Navegação section.
    """
    import re
    from app.shared.canonical_pages import normalize_page

    match = re.search(r"\[NAVIGATE:\s*([a-z][a-z0-9_-]*)\s*\]", text, re.IGNORECASE)
    if not match:
        return None
    canonical = normalize_page(match.group(1))
    clean = (text[: match.start()] + text[match.end():]).strip()
    return clean, canonical.value
