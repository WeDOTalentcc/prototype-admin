"""PR4 (Task #1004) — `audit_company_change`: fail-CLOSED audit wrapper
for company_settings save/read tools (Inegociável #6 — SOX, ISO 27001,
EU AI Act).

Design: outbox intent (separate committed row) + atomic outcome
(outcome row written in the SAME session as the body's business
writes, committed together). Audit failure on outcome rolls back the
business writes and raises. Intent failure aborts before the body
runs.

Body uses ``audit.session`` for all writes and MUST NOT commit. Body
populates ``set_before/set_after/set_target_id`` (canonical SOX
payload). ``LIA_DISABLE_COMPANY_AUDIT=1`` bypasses both phases (R-007
emergency rollback only).
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Any, Optional

logger = logging.getLogger(__name__)

_DISABLE_FLAG = "LIA_DISABLE_COMPANY_AUDIT"


def is_company_audit_disabled() -> bool:
    return os.getenv(_DISABLE_FLAG, "0") == "1"


def _derive_outcome(result: Any, *, read_only: bool) -> str:
    if read_only:
        return "read"
    if not isinstance(result, dict):
        return "completed"
    if result.get("success") is True:
        return "completed"
    reason = result.get("reason") or result.get("error")
    if reason == "fairness_violation":
        return "blocked_fairness"
    if reason:
        return f"failed:{reason}"[:64]
    return "failed"


def _truncate_str(value: Any, limit: int = 200) -> str:
    s = str(value)
    return s if len(s) <= limit else f"{s[:limit]}…"


def _serialize_payload(value: Any, limit: int = 1000) -> str:
    try:
        s = json.dumps(value, default=str, ensure_ascii=False, sort_keys=True)
    except Exception:
        s = str(value)
    return s if len(s) <= limit else f"{s[:limit]}…"


def _sentry_capture(exc: BaseException) -> None:
    try:
        import sentry_sdk

        sentry_sdk.capture_exception(exc)
    except Exception:
        # T-04 Tipo C: Sentry capture is best-effort observability;
        # never propagate failure here (we are already in audit error path).
        logger.debug(
            "[audit_decorators] sentry capture failed (best-effort)",
            exc_info=True,
        )


class _AuditCtx:
    """Async CM with outbox intent + atomic outcome. See module docstring."""

    def __init__(
        self,
        *,
        action: str,
        company_id: str,
        actor: Optional[str],
        target_table: Optional[str],
        target_id: Optional[str],
        metadata: Optional[dict[str, Any]],
        agent_name: str,
        read_only: bool,
        human_review_required: bool = False,
    ) -> None:
        self.action = action
        self.company_id = str(company_id) if company_id else ""
        self.actor = actor or "anonymous"
        self.target_table = target_table or "company_settings"
        self.target_id = target_id
        self.metadata = dict(metadata or {})
        self.agent_name = agent_name
        self.read_only = read_only
        # B1 (PR8 / Task #1008) — EU AI Act Art. 14 (human oversight): quando
        # uma sugestão da IA altera config corporativa que afeta múltiplos
        # candidatos (ex.: import_benefits_from_data), o audit log precisa
        # marcar `human_review_required=true`. Default permanece False
        # (compatibilidade com saves field-by-field já confirmados em UI).
        self.human_review_required = bool(human_review_required)
        self.trace_id = str(uuid.uuid4())
        self._result: Any = None
        self._before: Any = None
        self._before_set = False
        self._after: Any = None
        self._after_set = False
        # Shared session for the body's business writes + atomic outcome row.
        self.session = None  # type: ignore[assignment]
        self._session_cm = None

    # ── Setters (called by body) ─────────────────────────────────────
    def set_result(self, result: Any) -> None:
        self._result = result

    def set_before(self, before: Any) -> None:
        self._before = before
        self._before_set = True

    def set_after(self, after: Any) -> None:
        self._after = after
        self._after_set = True

    def set_target_id(self, target_id: Optional[str]) -> None:
        self.target_id = str(target_id) if target_id else None

    # ── Internal payload builders ────────────────────────────────────
    def _build_reasoning(self, decision: str, exc: Optional[BaseException]) -> list[str]:
        r = [
            f"trace_id={self.trace_id}",
            f"actor={self.actor}",
            f"target_id={self.target_id or '∅'}",
            f"outcome={decision}",
        ]
        if self._before_set:
            r.append(f"before={_serialize_payload(self._before)}")
        if self._after_set:
            r.append(f"after={_serialize_payload(self._after)}")
        for k, v in self.metadata.items():
            r.append(f"{k}={_truncate_str(v)}")
        if exc is not None:
            r.append(f"exception={type(exc).__name__}: {_truncate_str(exc)}")
        return r

    def _build_criteria(self) -> list[str]:
        return [
            "company_scoped",
            f"target_table:{self.target_table}",
            f"target_id:{self.target_id or '∅'}",
            f"action:{self.action}",
            f"read_only:{self.read_only}",
            f"trace_id:{self.trace_id}",
        ]

    async def _emit_independent(self, decision: str, exc: Optional[BaseException]) -> None:
        """Emit an audit row in its OWN session (commits independently).
        Used for intent (must be durable before body runs) and for
        exception/disabled outcomes where the body session is unusable."""
        from app.shared.compliance.audit_service import AuditService

        await AuditService().log_decision(
            company_id=self.company_id,
            agent_name=self.agent_name,
            decision_type="company_settings_change",
            action=self.action,
            decision=decision,
            reasoning=self._build_reasoning(decision, exc),
            criteria_used=self._build_criteria(),
            confidence=1.0,
            human_review_required=self.human_review_required,
        )

    async def _emit_in_session(self, decision: str, exc: Optional[BaseException]) -> None:
        """Emit an audit row in the SHARED body session (no commit).
        Caller commits to make business + outcome atomic."""
        from app.shared.compliance.audit_service import AuditService

        await AuditService().log_decision_in_session(
            self.session,
            company_id=self.company_id,
            agent_name=self.agent_name,
            decision_type="company_settings_change",
            action=self.action,
            decision=decision,
            reasoning=self._build_reasoning(decision, exc),
            criteria_used=self._build_criteria(),
            confidence=1.0,
            human_review_required=self.human_review_required,
        )

    async def _open_session(self) -> None:
        from app.shared.compliance.audit_service import AsyncSessionLocal, _bind_tenant

        self._session_cm = AsyncSessionLocal()
        self.session = await self._session_cm.__aenter__()
        if self.company_id:
            try:
                await _bind_tenant(self.session, self.company_id)
            except Exception as e:
                logger.warning(
                    "[audit_company_change] _bind_tenant failed (continuing): %s", e
                )

    async def _close_session(self, exc_type) -> None:
        if self._session_cm is not None:
            try:
                await self._session_cm.__aexit__(exc_type, None, None)
            except Exception:
                # T-04 Tipo C: session-cm teardown is best-effort;
                # connection may already be poisoned by the outer body exception.
                logger.debug(
                    "[audit_decorators] session __aexit__ failed (best-effort)",
                    exc_info=True,
                )
            self._session_cm = None
            self.session = None

    # ── CM protocol ──────────────────────────────────────────────────
    async def __aenter__(self) -> "_AuditCtx":
        if is_company_audit_disabled():
            await self._open_session()
            return self

        if self.read_only:
            await self._open_session()
            return self

        if not self.company_id:
            logger.error(
                "[audit_company_change] missing company_id for action=%s — "
                "intent skipped (RLS would block)",
                self.action,
            )
            await self._open_session()
            return self

        # Outbox phase 1: intent in independent session.
        try:
            await self._emit_independent("initiated", None)
        except Exception as audit_exc:
            logger.critical(
                "[audit_company_change] FAIL-CLOSED (intent) action=%s "
                "company=%s: %s",
                self.action, self.company_id, audit_exc, exc_info=True,
            )
            _sentry_capture(audit_exc)
            raise RuntimeError(
                f"audit_company_change: audit storage unavailable (intent emit "
                f"failed) for action={self.action}; business mutation aborted "
                f"to preserve Inegociável #6"
            ) from audit_exc

        await self._open_session()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        # Body raised: rollback business writes, emit "exception" outcome
        # in independent session (body session is poisoned).
        if exc_type is not None:
            if self.session is not None:
                try:
                    await self.session.rollback()
                except Exception:
                    # T-04 Tipo C: rollback is best-effort cleanup on poisoned session;
                    # the body exception is the real signal and will re-raise.
                    logger.debug(
                        "[audit_decorators] session rollback failed (best-effort)",
                        exc_info=True,
                    )
            await self._close_session(exc_type)
            if not is_company_audit_disabled() and self.company_id and not self.read_only:
                try:
                    await self._emit_independent("exception", exc)
                except Exception as audit_exc:
                    logger.critical(
                        "[audit_company_change] outcome 'exception' emit failed "
                        "for action=%s trace_id=%s: %s",
                        self.action, self.trace_id, audit_exc, exc_info=True,
                    )
                    _sentry_capture(audit_exc)
            return False  # never suppress

        outcome = _derive_outcome(self._result, read_only=self.read_only)

        # Bypass / no-tenant / read-only paths: no audit, just commit body
        # session (if any business writes happened) and exit.
        if is_company_audit_disabled():
            logger.warning(
                "[audit_company_change] BYPASSED action=%s company=%s outcome=%s",
                self.action, self.company_id, outcome,
            )
            if self.session is not None and not self.read_only:
                try:
                    await self.session.commit()
                except Exception:
                    await self.session.rollback()
                    raise
            await self._close_session(None)
            return False

        if not self.company_id:
            if self.session is not None and not self.read_only:
                try:
                    await self.session.commit()
                except Exception:
                    await self.session.rollback()
                    raise
            await self._close_session(None)
            return False

        if self.read_only:
            # Read-only: emit outcome in independent session. Fail-CLOSED
            # consistente com writes (LGPD Art. 37 / ISO 27001 A.12.4
            # exigem trilha de acesso a config corporativa).
            try:
                await self._emit_independent(outcome, None)
            except Exception as audit_exc:
                logger.critical(
                    "[audit_company_change] FAIL-CLOSED (read outcome) "
                    "action=%s company=%s trace_id=%s: %s",
                    self.action, self.company_id, self.trace_id,
                    audit_exc, exc_info=True,
                )
                _sentry_capture(audit_exc)
                await self._close_session(None)
                raise RuntimeError(
                    f"audit_company_change: read outcome audit failed for "
                    f"action={self.action} trace_id={self.trace_id} "
                    f"(fail-CLOSED)"
                ) from audit_exc
            await self._close_session(None)
            return False

        # ── ATOMIC PATH: outcome row + business writes in one commit ─
        try:
            await self._emit_in_session(outcome, None)
            await self.session.commit()
        except Exception as audit_exc:
            try:
                await self.session.rollback()
            # REGRA-4-EXEMPT: rollback-of-rollback defensivo; o logger.critical abaixo ja reporta com exc_info=True
            except Exception:
                pass
            logger.critical(
                "[audit_company_change] FAIL-CLOSED (outcome) action=%s "
                "company=%s outcome=%s trace_id=%s — business writes ROLLED "
                "BACK: %s",
                self.action, self.company_id, outcome, self.trace_id,
                audit_exc, exc_info=True,
            )
            _sentry_capture(audit_exc)
            await self._close_session(None)
            raise RuntimeError(
                f"audit_company_change: outcome audit failed for action="
                f"{self.action} trace_id={self.trace_id}; business writes "
                f"rolled back (fail-CLOSED)"
            ) from audit_exc
        await self._close_session(None)
        return False


def audit_company_change(
    *,
    action: str,
    company_id: str,
    actor: Optional[str] = None,
    target_table: Optional[str] = None,
    target_id: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
    agent_name: str = "company_settings_tools",
    read_only: bool = False,
    human_review_required: bool = False,
) -> _AuditCtx:
    """See module docstring. Body MUST use ``audit.session`` for writes
    and MUST NOT commit; CM commits atomically with the outcome row.

    ``human_review_required`` (B1 / PR8): set ``True`` when an AI suggestion
    mutates company-wide config that affects future candidates (EU AI Act
    Art. 14 — human oversight). Default ``False`` for field-level saves
    already confirmed by the recruiter via UI.
    """
    return _AuditCtx(
        action=action,
        company_id=company_id,
        actor=actor,
        target_table=target_table,
        target_id=target_id,
        metadata=metadata,
        agent_name=agent_name,
        read_only=read_only,
        human_review_required=human_review_required,
    )


__all__ = ["audit_company_change", "is_company_audit_disabled"]
