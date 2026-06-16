"""
LIA Chat Feedback — canonical HTTP endpoints for thumbs/rating/correction.

Closes the gap identified in Audit #569 (docs/audits/chat-message-actions-and-feedback-loop-audit.md):
the frontend posted to /api/v1/lia/feedback/* but the router did not exist,
so every thumbs click 404'd silently and the learning loop was dead in production.

Originalmente implementado em Task #570 (commit 0120f8d7e, 2026-04-19).
Recuperado em 2026-05-23 após descoberta da regressão silenciosa pelo merge
commit 02361f41c ("docs cherry-pick" que apagou 403 linhas).

Boy Scout upgrades aplicados durante recovery (vs. Task #570 original):
1. ``require_company_id`` canonical do `app.shared.security` substitui helper
   local — habilita Prometheus counter `lia_endpoint_require_company_id_total`
   pra observabilidade.
2. Pydantic schemas herdam ``WeDoBaseModel`` (`extra='forbid'`) — rejeita
   payload com fields fantasma (audit canonical R1 from CLAUDE.md).
3. ``AuditService.log_decision`` registrado em cada submit/regenerate —
   trail SOX-equivalent pra ações de feedback (CLAUDE.md "AuditService em
   ações sensíveis").
4. Sensor anti-regressão em `tests/contract/test_lia_feedback_contract.py`
   garante que os 6 paths permanecem registrados na OpenAPI runtime.

Contract canonical:
- company_id and user_id são derivados do authenticated user — NUNCA do body
  (IDOR-safe — see lia-compliance, multi-tenant isolation).
- Endpoints retornam 4xx/5xx explicitos (sem silent try/except).
- Persistência + pattern update delegados ao ``feedback_service`` canonical
  (app.domains.analytics.services.feedback_service.FeedbackService).
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ConfigDict, Field
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.core.database import get_db
from app.domains.analytics.services.feedback_service import FeedbackService
from app.shared.compliance.audit_service import AuditService
from app.shared.security.require_company_id import require_company_id
from app.shared.errors import LIAError
from app.shared.types import WeDoBaseModel
from lia_models.feedback import InteractionFeedback
from lia_models.memory import ConversationMemory

logger = logging.getLogger(__name__)

# Router prefix `/feedback` — composto a `/lia` (lia_assistant.router) e `/api/v1`
# (app.include_router em app/api/routes.py:492). Path final: `/api/v1/lia/feedback/*`.
# Nota: prefix curto aqui (sem `/lia/`) porque o parent já carrega `/lia`. Task #570
# original tinha `/lia/feedback` e provavelmente gerava duplicação; corrigido no
# recovery pra bater com o pattern dos outros sub-routers (suggestions etc).
feedback_router = APIRouter(prefix="/feedback", tags=["lia-feedback"])

# Module-level singletons. Stateless services, safe to share across requests.
_feedback_service = FeedbackService()
_audit_service = AuditService()


# ─── Schemas ──────────────────────────────────────────────────────────────


class MessageContextPayload(WeDoBaseModel):
    """Optional context about the LIA response being rated. All fields optional."""
    user_message: str | None = None
    lia_response: str | None = None
    intent: str | None = None
    stage: str | None = None
    response_time_ms: int | None = None
    tools_used: list[str] | None = None
    confidence_score: float | None = None


class ThumbsRequest(WeDoBaseModel):
    session_id: str = Field(..., min_length=1)
    message_id: str = Field(..., min_length=1)
    thumbs: str = Field(..., pattern="^(up|down)$")
    feedback_text: str | None = Field(default=None, max_length=2000)
    category: str | None = Field(default=None, max_length=50)
    message_context: MessageContextPayload | None = None


class RatingRequest(WeDoBaseModel):
    session_id: str = Field(..., min_length=1)
    message_id: str = Field(..., min_length=1)
    rating: int = Field(..., ge=1, le=5)
    feedback_text: str | None = Field(default=None, max_length=2000)
    category: str | None = Field(default=None, max_length=50)
    message_context: MessageContextPayload | None = None


class CorrectionRequest(WeDoBaseModel):
    session_id: str = Field(..., min_length=1)
    message_id: str = Field(..., min_length=1)
    original_response: str = Field(..., max_length=20000)
    correction: str = Field(..., min_length=1, max_length=20000)
    message_context: MessageContextPayload | None = None


class FeedbackAck(WeDoBaseModel):
    # Response schemas opt-out de validate_assignment porque podem ser
    # populados via from_attributes nos handlers (mas mantemos extra='forbid'
    # pra contract consistency).
    model_config = ConfigDict(extra="forbid")
    feedback_id: str
    status: str = "recorded"


class MessageFeedbackEntry(WeDoBaseModel):
    model_config = ConfigDict(extra="forbid")
    message_id: str
    thumbs: str | None = None
    rating: int | None = None
    feedback_text: str | None = None
    correction: str | None = None


class RegenerateRequest(WeDoBaseModel):
    session_id: str = Field(..., min_length=1)
    message_id: str = Field(..., min_length=1, description="Assistant message_id to regenerate")


class RegenerateResponse(WeDoBaseModel):
    model_config = ConfigDict(extra="forbid")
    user_message: str = Field(..., description="Prior user message text to re-process")
    prior_message_id: str | None = None
    regenerate_of: str
    status: str = "ready"


class ConversationFeedbackResponse(WeDoBaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[MessageFeedbackEntry]


class ImplicitSignalRequest(WeDoBaseModel):
    """Task #1299 — frontend-detected implicit signal.

    Only ``correction_delta`` and ``abandonment`` arrive here; ``regeneration``
    is captured server-side in ``/regenerate``. The backend is the gatekeeper:
    it re-applies the FairnessGuard gate and (for abandonment) the conservative
    criterion + engagement check before anything is persisted.
    """
    session_id: str = Field(..., min_length=1)
    message_id: str = Field(..., min_length=1, description="LIA message the signal is about")
    signal_type: str = Field(..., pattern="^(correction_delta|abandonment)$")
    # correction_delta payload
    original_response: str | None = Field(default=None, max_length=20000)
    used_text: str | None = Field(default=None, max_length=20000)
    # abandonment payload
    abandoned_response: str | None = Field(default=None, max_length=20000)
    next_user_message: str | None = Field(default=None, max_length=20000)
    message_context: MessageContextPayload | None = None


class ImplicitSignalAck(WeDoBaseModel):
    model_config = ConfigDict(extra="forbid")
    persisted: bool
    signal_type: str
    signal_id: str | None = None
    skipped_reason: str | None = None


# ─── Helpers ──────────────────────────────────────────────────────────────


def _build_context(
    message_id: str,
    payload: MessageContextPayload | None,
) -> dict[str, Any]:
    ctx: dict[str, Any] = {"message_id": message_id}
    if payload is not None:
        ctx.update({k: v for k, v in payload.model_dump().items() if v is not None})
    return ctx


async def _audit_feedback_action(
    company_id: str,
    user_id: str,
    action: str,
    decision: str,
    session_id: str,
    message_id: str,
    extra_reasoning: list[str] | None = None,
) -> None:
    """Best-effort audit trail. Failure to audit must NOT block the user action."""
    try:
        await _audit_service.log_decision(
            company_id=company_id,
            agent_name="lia_feedback_endpoint",
            decision_type="user_feedback",
            action=action,
            decision=decision,
            reasoning=[
                f"session_id={session_id}",
                f"message_id={message_id}",
                *(extra_reasoning or []),
            ],
            criteria_used=["user_explicit_input"],
            actor_user_id=user_id,
        )
    except Exception:
        logger.exception("audit_service.log_decision failed for feedback action=%s", action)


# ─── Endpoints ────────────────────────────────────────────────────────────


@feedback_router.post("/thumbs", response_model=FeedbackAck, status_code=201)
async def submit_thumbs(
    body: ThumbsRequest,
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
) -> FeedbackAck:
    """Record a thumbs up/down. Optionally attaches a free-text comment."""
    try:
        feedback = await _feedback_service.record_feedback(
            session_id=body.session_id,
            company_id=company_id,
            user_id=str(current_user.id),
            feedback_type="thumbs",
            feedback_value=body.thumbs,
            message_context=_build_context(body.message_id, body.message_context),
            db=db,
        )
        # Audit #570 review fix: when the user attaches a free-text reason to a
        # thumbs-down, persist it to `InteractionFeedback.correction` (NOT
        # `feedback_text`) so it lights up the qualitative-signal branch in
        # `_update_patterns_from_feedback` (feedback_service.py L152). The UI
        # category ("inaccurate" / "wrong_tone" / "hallucinated") still goes
        # to `feedback_category` for analytics buckets.
        if body.feedback_text or body.category:
            if body.feedback_text:
                feedback.correction = body.feedback_text
            feedback.feedback_category = body.category
            await db.commit()
            await db.refresh(feedback)
            # Re-trigger the pattern update now that `correction` is set —
            # the first record_feedback call ran before we wrote the field.
            try:
                await _feedback_service._update_patterns_from_feedback(feedback, db)
            except Exception:
                logger.exception("pattern update after thumbs-down comment failed")

        # Boy Scout upgrade #3: audit trail SOX-equivalent (CLAUDE.md
        # "AuditService.log_decision em ações sensíveis").
        await _audit_feedback_action(
            company_id=company_id,
            user_id=str(current_user.id),
            action=f"thumbs_{body.thumbs}",
            decision="recorded",
            session_id=body.session_id,
            message_id=body.message_id,
            extra_reasoning=(
                [f"category={body.category}"] if body.category else None
            ),
        )
        return FeedbackAck(feedback_id=str(feedback.id))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to record thumbs feedback")
        raise LIAError(message="Erro interno do servidor")


@feedback_router.post("/rating", response_model=FeedbackAck, status_code=201)
async def submit_rating(
    body: RatingRequest,
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
) -> FeedbackAck:
    """Record a 1-5 star rating for an assistant response."""
    try:
        feedback = await _feedback_service.record_feedback(
            session_id=body.session_id,
            company_id=company_id,
            user_id=str(current_user.id),
            feedback_type="rating",
            feedback_value={
                "rating": body.rating,
                "feedback_text": body.feedback_text,
                "category": body.category,
            },
            message_context=_build_context(body.message_id, body.message_context),
            db=db,
        )
        await _audit_feedback_action(
            company_id=company_id,
            user_id=str(current_user.id),
            action="rating",
            decision=f"stars={body.rating}",
            session_id=body.session_id,
            message_id=body.message_id,
        )
        return FeedbackAck(feedback_id=str(feedback.id))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to record rating feedback")
        raise LIAError(message="Erro interno do servidor")


@feedback_router.post("/correction", response_model=FeedbackAck, status_code=201)
async def submit_correction(
    body: CorrectionRequest,
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
) -> FeedbackAck:
    """Record a user-proposed correction to an assistant response."""
    ctx = _build_context(body.message_id, body.message_context)
    # Preserve the original response in context if not explicitly provided.
    ctx.setdefault("lia_response", body.original_response)
    try:
        feedback = await _feedback_service.record_feedback(
            session_id=body.session_id,
            company_id=company_id,
            user_id=str(current_user.id),
            feedback_type="correction",
            feedback_value=body.correction,
            message_context=ctx,
            db=db,
        )
        await _audit_feedback_action(
            company_id=company_id,
            user_id=str(current_user.id),
            action="correction",
            decision="recorded",
            session_id=body.session_id,
            message_id=body.message_id,
            extra_reasoning=[f"correction_length={len(body.correction)}"],
        )
        return FeedbackAck(feedback_id=str(feedback.id))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to record correction feedback")
        raise LIAError(message="Erro interno do servidor")


@feedback_router.get("/metrics")
async def get_metrics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Aggregated feedback metrics scoped to caller's company."""
    try:
        return await _feedback_service.get_feedback_metrics(
            company_id=company_id, days=days, db=db
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to load feedback metrics")
        raise LIAError(message="Erro interno do servidor")


@feedback_router.get(
    "/by-conversation/{session_id}",
    response_model=ConversationFeedbackResponse,
)
async def get_feedback_by_conversation(
    session_id: str,
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
) -> ConversationFeedbackResponse:
    """
    Hydrate per-message feedback state for a conversation.

    Returns the LATEST feedback row per message_id, scoped to the current
    user's company (multi-tenant isolation). Used by the chat UI to restore
    thumbs state after a refresh — closes UX gap F3 from the audit.
    """
    try:
        from uuid import UUID as _UUID
        try:
            company_uuid = _UUID(company_id)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid company_id: {company_id}"
            )

        result = await db.execute(
            select(InteractionFeedback)
            .where(
                and_(
                    InteractionFeedback.session_id == session_id,
                    InteractionFeedback.company_id == company_uuid,
                    InteractionFeedback.message_id.isnot(None),
                )
            )
            .order_by(InteractionFeedback.created_at.asc())
        )
        rows = result.scalars().all()

        # Last-write-wins per message_id.
        latest: dict[str, InteractionFeedback] = {}
        for row in rows:
            if row.message_id:
                latest[row.message_id] = row

        items = [
            MessageFeedbackEntry(
                message_id=mid,
                thumbs=fb.thumbs,
                rating=fb.rating,
                feedback_text=fb.feedback_text,
                correction=fb.correction,
            )
            for mid, fb in latest.items()
        ]
        return ConversationFeedbackResponse(items=items)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to load conversation feedback")
        raise LIAError(message="Erro interno do servidor")


@feedback_router.post(
    "/regenerate", response_model=RegenerateResponse, status_code=200
)
async def regenerate_response(
    body: RegenerateRequest,
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
) -> RegenerateResponse:
    """
    Audit #570 P1: backend-side regeneration handshake.

    The client requests regeneration of an assistant message. We:
      1. Verify the assistant message belongs to the caller's company
         (multi-tenant isolation, IDOR-safe).
      2. Locate the immediately prior `user` message in the same session.
      3. Mark the original assistant row as `regenerated=true` in metadata
         so analytics + UI can hide/version-stamp the superseded bubble.
      4. Return the user message text + a `regenerate_of` correlation id
         the client uses when re-invoking the chat pipeline; the new
         assistant response will carry `regenerated_from=<old_id>`.

    Why this is a separate endpoint instead of just resending: it gives
    us a single auditable spot for the supersede-mark + ownership check,
    avoids inflating the conversation thread with duplicate bubbles, and
    lets the learning loop distinguish organic turns from regenerations.
    """
    from uuid import UUID as _UUID
    try:
        company_uuid = _UUID(company_id)
        assistant_uuid = _UUID(body.message_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid company_id or message_id (expected UUIDs).",
        )

    assistant_row = (
        await db.execute(
            select(ConversationMemory).where(
                and_(
                    ConversationMemory.id == assistant_uuid,
                    ConversationMemory.company_id == company_uuid,
                    ConversationMemory.session_id == body.session_id,
                    ConversationMemory.role == "assistant",
                )
            )
        )
    ).scalar_one_or_none()

    if assistant_row is None:
        raise HTTPException(
            status_code=404,
            detail="Assistant message not found in this conversation.",
        )

    prior = (
        await db.execute(
            select(ConversationMemory)
            .where(
                and_(
                    ConversationMemory.session_id == body.session_id,
                    ConversationMemory.company_id == company_uuid,
                    ConversationMemory.role == "user",
                    ConversationMemory.created_at < assistant_row.created_at,
                )
            )
            .order_by(ConversationMemory.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    if prior is None:
        raise HTTPException(
            status_code=409,
            detail="No prior user message found to regenerate from.",
        )

    # Stamp the superseded assistant message so the UI/analytics can hide it.
    md = dict(assistant_row.extra_data or {})
    md["regenerated"] = True
    md["regenerated_at"] = datetime.utcnow().isoformat()
    assistant_row.extra_data = md
    try:
        await db.commit()
    except HTTPException:
        raise
    except Exception:
        await db.rollback()
        logger.exception("Failed to stamp regenerated metadata")
        raise LIAError(message="Could not mark message regenerated")

    await _audit_feedback_action(
        company_id=company_id,
        user_id=str(current_user.id),
        action="regenerate_requested",
        decision="superseded",
        session_id=body.session_id,
        message_id=str(assistant_row.id),
        extra_reasoning=[f"prior_user_message_id={prior.id}"],
    )

    # Task #1299: regeneration is a strong IMPLICIT NEGATIVE signal. Capture it
    # server-side (the most reliable hook) into the same learning store as
    # explicit feedback. Defensive — a learning-loop hiccup must NEVER break the
    # regenerate handshake the recruiter is waiting on.
    try:
        from app.shared.learning.implicit_feedback_service import (
            implicit_feedback_service,
        )

        _md = assistant_row.extra_data or {}
        await implicit_feedback_service.capture_regeneration(
            db=db,
            company_id=company_id,
            user_id=str(current_user.id),
            session_id=body.session_id,
            superseded_message_id=str(assistant_row.id),
            superseded_response=assistant_row.content or "",
            prior_user_message=prior.content or "",
            intent=_md.get("intent"),
            stage=_md.get("stage"),
            trace_id=_md.get("trace_id"),
            confidence_at_generation=_md.get("confidence_score"),
        )
    except Exception:
        logger.exception(
            "Task #1299: implicit regeneration signal capture failed (non-fatal)"
        )

    return RegenerateResponse(
        user_message=prior.content,
        prior_message_id=str(prior.id),
        regenerate_of=str(assistant_row.id),
    )


@feedback_router.post(
    "/implicit", response_model=ImplicitSignalAck, status_code=200
)
async def submit_implicit_signal(
    body: ImplicitSignalRequest,
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
) -> ImplicitSignalAck:
    """Task #1299: frontend-detected implicit signal (correction_delta /
    abandonment).

    ``company_id`` / ``user_id`` are derived from the authenticated user (never
    the body — IDOR-safe). The service is the gatekeeper: FairnessGuard gate for
    both, plus the conservative criterion + explicit-engagement check for
    abandonment. ``persisted=False`` with a ``skipped_reason`` is a normal,
    non-error outcome (e.g. criterion not met).
    """
    from app.shared.learning.implicit_feedback_service import (
        implicit_feedback_service,
    )

    ctx = body.message_context.model_dump() if body.message_context else {}
    intent = ctx.get("intent")
    stage = ctx.get("stage")
    trace_id = ctx.get("trace_id") if isinstance(ctx, dict) else None
    confidence = ctx.get("confidence_score") if isinstance(ctx, dict) else None

    try:
        if body.signal_type == "correction_delta":
            result = await implicit_feedback_service.capture_correction_delta(
                db=db,
                company_id=company_id,
                user_id=str(current_user.id),
                session_id=body.session_id,
                source_message_id=body.message_id,
                original_response=body.original_response or "",
                used_text=body.used_text or "",
                intent=intent,
                stage=stage,
                trace_id=trace_id,
                confidence_at_generation=confidence,
            )
        else:  # abandonment (schema-validated to one of the two)
            result = await implicit_feedback_service.capture_abandonment(
                db=db,
                company_id=company_id,
                user_id=str(current_user.id),
                session_id=body.session_id,
                abandoned_message_id=body.message_id,
                abandoned_response=body.abandoned_response or "",
                next_user_message=body.next_user_message or "",
                intent=intent,
                stage=stage,
                trace_id=trace_id,
                confidence_at_generation=confidence,
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to record implicit signal")
        raise HTTPException(
            status_code=500, detail="Internal server error"
        )

    if result.persisted:
        await _audit_feedback_action(
            company_id=company_id,
            user_id=str(current_user.id),
            action=f"implicit_{result.signal_type}",
            decision="recorded",
            session_id=body.session_id,
            message_id=body.message_id,
        )

    return ImplicitSignalAck(
        persisted=result.persisted,
        signal_type=result.signal_type,
        signal_id=result.signal_id,
        skipped_reason=result.skipped_reason,
    )
