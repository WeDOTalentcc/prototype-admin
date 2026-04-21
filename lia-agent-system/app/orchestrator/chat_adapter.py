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

from app.orchestrator.context_adapter import ContextAdapter, UniversalContext
from app.orchestrator.main_orchestrator import MainOrchestrator
from app.shared.pii_masking import redact_response_with_audit

logger = logging.getLogger(__name__)


# Onda 2.1 G5 light (2026-04-21) — PII redaction helper for response boundary.
def _apply_pii_redaction(response_dict: dict) -> dict:
    """Apply PII redaction to the 'response' field of a chat response dict.

    LGPD Art. 12 + 13 compliance: redact candidate CPF/CNPJ/email/phone from
    LIA responses before frontend exposes them. Audit trail logged to
    compliance audit log (via logger with PIIMaskingFilter installed).

    Returns a new dict with:
      - response: redacted text
      - pii_redacted: bool (True if any PII was detected + redacted)
      - pii_audit_count: int (number of PII instances found)
    """
    text = response_dict.get("response", "")
    if not isinstance(text, str) or not text:
        return response_dict

    redacted, audit = redact_response_with_audit(text)
    if not audit:
        # Nothing redacted — add explicit pii_redacted=False for traceability
        response_dict = dict(response_dict)
        response_dict["pii_redacted"] = False
        response_dict["pii_audit_count"] = 0
        return response_dict

    # PII detected + redacted; log audit for LGPD compliance trail.
    types_found = sorted({a["type"] for a in audit})
    logger.info(
        "[G5-PII] redaction applied count=%d types=%s",
        len(audit), types_found,
    )

    response_dict = dict(response_dict)
    response_dict["response"] = redacted
    response_dict["pii_redacted"] = True
    response_dict["pii_audit_count"] = len(audit)
    return response_dict



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

        # Load conversation state for entity memory
        try:
            from app.shared.memory.conversation_state import conversation_state_store, ConversationState
            _cstate = conversation_state_store.get(conversation_id or "") or ConversationState()
            _cstate.company_id = company_id  # Ensure tenant isolation
            ctx.conversation_state = _cstate
        except Exception:
            pass  # Fail-safe

        # ── Step 2: Call MainOrchestrator ──
        try:
            orch_response = await self._orch.process(ctx, db)
        except Exception as exc:
            logger.error(f"[ChatAdapter] MainOrchestrator failed: {exc}", exc_info=True)
            return self._error_response(str(exc))

        # Save updated conversation state back to store
        try:
            if ctx.conversation_state and conversation_id:
                from app.shared.memory.conversation_state import conversation_state_store
                conversation_state_store.set(conversation_id, ctx.conversation_state)
        except Exception:
            pass

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
        entity_id = pc.get("entity_id") or pc.get("job_vacancy_id") or pc.get("job_id")
        entity_type = "job" if entity_id else None

        context_page = pc.get("page_type") or pc.get("domain") or "general"

        ctx = ContextAdapter.from_rest(
            message=user_message,
            user_id=user_id,
            company_id=str(company_id) if company_id else "",
            conversation_id=conversation_id,
            context_page=context_page,
            entity_id=str(entity_id) if entity_id else None,
            entity_type=entity_type,
            selected_candidate_ids=pc.get("candidate_ids"),
            job_context=pc.get("job_context"),
            actor_user_id=user_id,
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
        - agent_used: str  (Task #552 — routed specialist identifier)
        - agents_consulted: list[str]  (Task #552)
        - action_result: dict | None (new)
        - pending_action: dict | None (new)
        - fairness_warnings: list[str] (new)
        - from_cache: bool (new)
        """
        _agent_used = getattr(orch_response, "agent_used", "") or "main_orchestrator"
        result: dict[str, Any] = {
            "response": getattr(orch_response, "content", "") or "",
            "intent": getattr(orch_response, "intent_detected", "general"),
            "entities": {},
            "workflow_data": {},
            # Task #552: expose the routed specialist explicitly so chat.py can
            # echo it on the response payload (instead of overloading
            # prompt_version, which is meant for the prompt-registry hash).
            "agent_used": _agent_used,
            "agents_consulted": list(getattr(orch_response, "agents_consulted", []) or []),
            "prompt_version": _agent_used,
            "fairness_warnings": getattr(orch_response, "fairness_warnings", []),
            "from_cache": getattr(orch_response, "from_cache", False),
            # LIA-LCF-01 (Task #620): expose tool calls observed by the ReAct agent
            # so chat.py can surface them on the response body for eval/judge.
            "actions": list(getattr(orch_response, "actions", []) or []),
        }

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

        return _apply_pii_redaction(result)

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
            "agent_used": "chat_adapter_error",
            "agents_consulted": [],
            "prompt_version": "chat_adapter_error",
            "error": error_msg,
        }
