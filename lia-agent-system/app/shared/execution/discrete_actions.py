"""Discrete action handlers for the Plan & Execute (P&E) executor.

Some P&E pipeline steps map to *discrete, one-shot* actions (move a candidate,
notify the team) that must run through the platform's compliant code paths
instead of the lossy keyword-matching `DomainWorkflow.process` re-derivation.

This module is the canonical registry for those handlers. Each handler:

  * receives the already-resolved ``params`` (task params + chained context) and
    an :class:`ActionContext` carrying tenant/user/session identity;
  * reuses the existing compliant services (FairnessGuard, PipelineStageService,
    AuditService, notification_service) — it never re-implements thresholds;
  * is HONEST: missing required inputs return a clarification, missing
    recipients return an error. It NEVER fakes success.

INVIOLÁVEL (#1211): nenhuma ação discreta cria vaga — criação de vaga é SEMPRE
e SÓ o wizard canônico.

Handlers are registered by ``(domain_id, action_id)``. The PlanExecutor consults
:func:`get_discrete_handler` before falling back to the DomainWorkflow path.
"""
from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from app.domains.base import DomainResponse

# Module-level bindings so handlers reuse the compliant services. Imported here
# (not lazily) so tests can patch them via ``patch.object(discrete_actions, ...)``
# and so the registry wiring is explicit/auditable.
from app.domains.recruiter_assistant.services.pipeline_stage_service import PipelineStageService
from app.services.notification_service import notification_service
from app.shared.compliance.audit_service import AuditService
from app.shared.compliance.fairness_guard import FairnessGuard

logger = logging.getLogger(__name__)


@dataclass
class ActionContext:
    """Identity/context passed to a discrete handler (never client-trusted)."""

    company_id: str | None
    user_id: str
    session_id: str
    tenant_id: str | None
    raw_query: str = ""
    base_context: dict[str, Any] = field(default_factory=dict)


DiscreteHandler = Callable[[dict[str, Any], ActionContext], Awaitable[DomainResponse]]

_HANDLERS: dict[tuple[str, str], DiscreteHandler] = {}


def register_discrete_handler(domain_id: str, action_id: str) -> Callable[[DiscreteHandler], DiscreteHandler]:
    """Decorator registering a discrete handler for ``(domain_id, action_id)``."""

    def _decorator(func: DiscreteHandler) -> DiscreteHandler:
        _HANDLERS[(domain_id, action_id)] = func
        return func

    return _decorator


def get_discrete_handler(domain_id: str, action_id: str) -> DiscreteHandler | None:
    """Return the registered handler for ``(domain_id, action_id)`` or ``None``."""
    return _HANDLERS.get((domain_id, action_id))


def _pick(params: dict[str, Any], actx: ActionContext, *keys: str) -> Any:
    """First non-None value for ``keys``, preferring params then base_context.

    P&E pattern tasks start with empty params; recruiter/extracted entities are
    carried in ``base_context``. This lets a handler accept either source.
    """
    for key in keys:
        if params.get(key) is not None:
            return params.get(key)
    bc = actx.base_context or {}
    for key in keys:
        if bc.get(key) is not None:
            return bc.get(key)
    return None


async def _resolve_team_recipients(company_id: str | None) -> list[tuple[str, str | None]]:
    """Return ``(user_id, email)`` for the tenant's notifiable team members.

    Scoped strictly by ``company_id`` (manager/admin/hiring_manager). Returns an
    empty list on any failure so the caller can surface an honest error.
    """
    if not company_id:
        return []
    try:
        from sqlalchemy import text

        from lia_config.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(
                    """
                    SELECT DISTINCT u.id, u.email
                    FROM users u
                    WHERE u.company_id = :company_id
                      AND u.role IN ('manager', 'admin', 'hiring_manager')
                    LIMIT 25
                    """
                ),
                {"company_id": company_id},
            )
            return [(str(r[0]), r[1]) for r in result.fetchall() if r[0]]
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Team recipient lookup failed: %s", exc, exc_info=True)
        return []


async def _resolve_recipients_by_ids(
    company_id: str | None, user_ids: list[Any]
) -> list[tuple[str, str | None]]:
    """Validate client-supplied recipient IDs against the current tenant.

    SECURITY: explicit ``recipient_user_ids`` are untrusted (LLM/client input).
    They MUST be resolved to users that actually belong to ``company_id`` so a
    spoofed/hallucinated ID cannot write a notification into another tenant.
    IDs outside the tenant are silently dropped; an empty result lets the caller
    surface an honest error.
    """
    if not company_id or not user_ids:
        return []
    ids = [str(u) for u in user_ids if u]
    if not ids:
        return []
    try:
        from sqlalchemy import bindparam, text

        from lia_config.database import AsyncSessionLocal

        stmt = text(
            """
            SELECT DISTINCT u.id, u.email
            FROM users u
            WHERE u.company_id = :company_id
              AND u.id IN :ids
            LIMIT 50
            """
        ).bindparams(bindparam("ids", expanding=True))
        async with AsyncSessionLocal() as session:
            result = await session.execute(stmt, {"company_id": company_id, "ids": ids})
            return [(str(r[0]), r[1]) for r in result.fetchall() if r[0]]
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Explicit recipient lookup failed: %s", exc, exc_info=True)
        return []


@register_discrete_handler("automation", "move_candidate_stage")
async def handle_move_candidate_stage(params: dict[str, Any], actx: ActionContext) -> DomainResponse:
    """Move one or more candidates to a stage via the compliant pipeline path.

    FairnessGuard L3 (pipeline_move) is BLOCKING; PipelineStageService enforces
    transition rules and tenant scoping; AuditService records each move
    (decision_type=move_stage). Emits ``movement_data`` for downstream chaining.
    """
    company_id = actx.company_id or actx.tenant_id
    if not company_id:
        return DomainResponse.error_response(
            error="missing_tenant_context",
            message="Contexto de empresa ausente — movimentação não executada.",
            domain_id="automation",
            action_id="move_candidate_stage",
        )
    to_stage = _pick(params, actx, "to_stage", "stage")
    raw_ids = _pick(
        params,
        actx,
        "vacancy_candidate_ids",
        "vacancy_candidate_id",
        "candidate_ids",
        "candidate_id",
    )
    if isinstance(raw_ids, str):
        ids = [raw_ids]
    elif isinstance(raw_ids, (list, tuple)):
        ids = [str(x) for x in raw_ids if x]
    elif raw_ids is not None:
        ids = [str(raw_ids)]
    else:
        ids = []

    if not ids or not to_stage:
        return DomainResponse.clarification_response(
            question=(
                "Para mover o(s) candidato(s) preciso saber QUAL candidato "
                "(vacancy_candidate_id) e para QUAL etapa mover."
            ),
            domain_id="automation",
            action_id="move_candidate_stage",
        )

    # ── Fairness L3 BLOQUEANTE ────────────────────────────────────────────
    guard = FairnessGuard()
    fairness = await guard.check_with_layer3(
        actx.raw_query or f"mover para {to_stage}", action_type="pipeline_move"
    )
    try:
        await guard.log_check(fairness, context="pe_pipeline_move", company_id=company_id)
    except Exception as exc:  # pragma: no cover - audit must not crash flow
        logger.warning("FairnessGuard log_check failed (move): %s", exc)
    if getattr(fairness, "is_blocked", False):
        return DomainResponse.error_response(
            error="fairness_blocked",
            message=(
                getattr(fairness, "educational_message", None)
                or "Movimentação bloqueada: possível critério discriminatório."
            ),
            domain_id="automation",
            action_id="move_candidate_stage",
            metadata={
                "fairness_blocked": True,
                "category": getattr(fairness, "category", None),
            },
        )

    # ── Transição compliant ───────────────────────────────────────────────
    service = PipelineStageService()
    moved: list[str] = []
    errors: list[dict[str, Any]] = []
    for vcid in ids:
        try:
            await service.transition_candidate(
                vacancy_candidate_id=vcid,
                to_stage=str(to_stage),
                to_sub_status=params.get("to_sub_status"),
                triggered_by="plan_execute",
                triggered_by_user_id=actx.user_id,
                source_agent="plan_execute",
                reason=params.get("reason") or "P&E: mover_e_notificar",
                context={"company_id": company_id},
                db=None,
            )
            moved.append(vcid)
        except PermissionError:
            errors.append({"vacancy_candidate_id": vcid, "error": "permission_denied"})
        except Exception as exc:
            errors.append({"vacancy_candidate_id": vcid, "error": str(exc)})

    if not moved:
        return DomainResponse.error_response(
            error="move_failed",
            message="Não foi possível mover o(s) candidato(s) para a etapa solicitada.",
            domain_id="automation",
            action_id="move_candidate_stage",
            metadata={"errors": errors},
        )

    # ── Auditoria (move_stage) ────────────────────────────────────────────
    audit = AuditService()
    for vcid in moved:
        try:
            await audit.log_decision(
                company_id=company_id,
                agent_name="plan_execute",
                decision_type="move_stage",
                action=f"move_to:{to_stage}",
                decision="moved",
                reasoning=[f"P&E mover_e_notificar → etapa '{to_stage}'"],
                criteria_used=["stage_transition"],
                candidate_id=vcid,
                human_review_required=False,
                actor_user_id=actx.user_id,
            )
        except Exception as exc:  # pragma: no cover - audit must not crash flow
            logger.warning("AuditService log_decision failed (move): %s", exc)

    movement_data = {
        "to_stage": to_stage,
        "moved_count": len(moved),
        "vacancy_candidate_ids": moved,
        "candidate_id": moved[0] if len(moved) == 1 else None,
        "errors": errors,
    }
    message = f"Movido(s) {len(moved)} candidato(s) para a etapa '{to_stage}'."
    if errors:
        message += f" {len(errors)} falha(s) registrada(s)."

    return DomainResponse.success_response(
        message=message,
        data={"movement_data": movement_data, "moved_count": len(moved), "to_stage": to_stage},
        domain_id="automation",
        action_id="move_candidate_stage",
    )


@register_discrete_handler("communication", "send_notification")
async def handle_send_notification(params: dict[str, Any], actx: ActionContext) -> DomainResponse:
    """Notify the tenant team in-app about a pipeline event.

    Fairness here is LIGHT (Layer 1/2 only) and NON-blocking on the happy path —
    soft warnings are attached to metadata, never used to drop a team notice.
    Auditing (decision_type=send_message) is mandatory. No recipients → honest
    error (never a fake success).
    """
    company_id = actx.company_id or actx.tenant_id
    if not company_id:
        return DomainResponse.error_response(
            error="missing_tenant_context",
            message="Contexto de empresa ausente — notificação não enviada.",
            domain_id="communication",
            action_id="send_notification",
        )
    movement_data = params.get("movement_data") or {}
    if not isinstance(movement_data, dict):
        movement_data = {}

    to_stage = movement_data.get("to_stage")
    related_job_id = params.get("job_id") or movement_data.get("job_id")
    related_candidate_id = params.get("candidate_id") or movement_data.get("candidate_id")

    title = params.get("title") or "Atualização do pipeline"
    message = params.get("message")
    if not message:
        message = (
            f"Candidato movido para a etapa '{to_stage}'."
            if to_stage
            else "Atualização no pipeline de recrutamento."
        )

    # ── Fairness LEVE (não bloqueante) no conteúdo ────────────────────────
    guard = FairnessGuard()
    fairness = guard.check(f"{title}\n{message}")
    soft_warnings = list(getattr(fairness, "soft_warnings", []) or [])
    try:
        await guard.log_check(fairness, context="pe_notification", company_id=company_id)
    except Exception as exc:  # pragma: no cover - audit must not crash flow
        logger.warning("FairnessGuard log_check failed (notify): %s", exc)

    # ── Destinatários ─────────────────────────────────────────────────────
    explicit = params.get("recipient_user_ids")
    recipients: list[tuple[str, str | None]]
    if explicit:
        # SECURITY: explicit IDs are untrusted — validate against the tenant.
        recipients = await _resolve_recipients_by_ids(company_id, list(explicit))
    else:
        recipients = await _resolve_team_recipients(company_id)

    if not recipients:
        return DomainResponse.error_response(
            error="no_recipients",
            message=(
                "Nenhum membro do time (manager/admin/hiring_manager) encontrado "
                "para notificar. Indique os destinatários."
            ),
            domain_id="communication",
            action_id="send_notification",
        )

    created = 0
    for user_id, _email in recipients:
        if not user_id:
            continue
        try:
            await notification_service.create_notification(
                user_id=str(user_id),
                title=title,
                message=message,
                category="pipeline_update",
                source_agent="plan_execute",
                related_job_id=str(related_job_id) if related_job_id else None,
                related_candidate_id=str(related_candidate_id) if related_candidate_id else None,
            )
            created += 1
        except Exception as exc:
            logger.warning("notification_service.create_notification failed: %s", exc)

    if created == 0:
        return DomainResponse.error_response(
            error="notification_failed",
            message="Não foi possível criar notificações in-app para o time.",
            domain_id="communication",
            action_id="send_notification",
        )

    # ── Auditoria (send_message) ──────────────────────────────────────────
    try:
        await AuditService().log_decision(
            company_id=company_id,
            agent_name="plan_execute",
            decision_type="send_message",
            action="notify_team",
            decision="sent",
            reasoning=["P&E mover_e_notificar → notificar time"],
            criteria_used=["team_notification"],
            job_vacancy_id=str(related_job_id) if related_job_id else None,
            human_review_required=False,
            actor_user_id=actx.user_id,
        )
    except Exception as exc:  # pragma: no cover - audit must not crash flow
        logger.warning("AuditService log_decision failed (notify): %s", exc)

    metadata: dict[str, Any] = {"recipients": created}
    if soft_warnings:
        metadata["fairness_soft_warnings"] = soft_warnings

    return DomainResponse.success_response(
        message=f"Time notificado: {created} notificação(ões) in-app criada(s).",
        data={
            "notifications_created": created,
            "recipients": created,
            "notification_data": {"title": title, "message": message},
        },
        metadata=metadata,
        domain_id="communication",
        action_id="send_notification",
    )
