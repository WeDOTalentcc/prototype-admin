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

# Task #1227 — buscar/pontuar/adicionar reuses these canonical primitives (each
# already embeds tenant scoping + FairnessGuard + audit). Imported at module
# level so tests can patch them via ``patch.object(discrete_actions, ...)``.
from app.domains.cv_screening.services.cv_scoring_service import CVScoringService
from app.domains.cv_screening.tools.candidate_tools import add_candidate_to_vacancy
from app.domains.cv_screening.tools.cv_upload_tool import (
    parse_and_create_candidate as _parse_and_create_candidate_primitive,
)
from app.domains.job_management.services.jd_enrichment_service import JdEnrichmentService
from app.domains.sourcing.services.pearch_service import PearchService

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


@dataclass
class _DiscreteToolContext:
    """Minimal `_context` object for tools that require company_id + user_id.

    Tenant identity comes ONLY from the resolved :class:`ActionContext` (server
    side), never from client-provided params.
    """

    company_id: str | None
    user_id: str


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


# ─────────────────────────────────────────────────────────────────────────────
# Task #1227 — Buscar, pontuar e adicionar (item 1)
# ─────────────────────────────────────────────────────────────────────────────


def _attr(obj: Any, key: str, default: Any = None) -> Any:
    """Read ``key`` from a dict OR an attribute object (Pearch CandidateProfile)."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


async def _get_vacancy_jd(company_id: str, vacancy_id: str) -> dict[str, Any] | None:
    """Tenant-scoped fetch of a vacancy's enriched JD (title/description/location).

    Returns ``None`` when the vacancy does not exist for this tenant — the caller
    surfaces an honest "vaga não encontrada" instead of guessing.
    """
    if not company_id or not vacancy_id:
        return None
    try:
        from sqlalchemy import text

        from lia_config.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(
                    """
                    SELECT title, description, location
                    FROM job_vacancies
                    WHERE id = :vid AND company_id = :cid
                    LIMIT 1
                    """
                ),
                {"vid": str(vacancy_id), "cid": str(company_id)},
            )
            row = result.fetchone()
            if not row:
                return None
            return {"title": row[0], "description": row[1], "location": row[2]}
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Vacancy JD lookup failed: %s", exc, exc_info=True)
        return None


def _profile_to_candidate(p: Any) -> dict[str, Any]:
    """Normalise a Pearch ``CandidateProfile`` (or dict) into candidate_data for
    standalone scoring. ``id`` = ``docid`` (DB PK for local/discovered; Pearch id
    for externals — the latter honestly fail at add-time, never faked)."""
    name = (
        _attr(p, "name")
        or " ".join(x for x in [_attr(p, "first_name"), _attr(p, "last_name")] if x)
        or "Candidato"
    )
    emails = _attr(p, "emails") or []
    email = (
        _attr(p, "best_personal_email")
        or _attr(p, "best_business_email")
        or (emails[0] if emails else None)
    )
    score = _attr(p, "match_score")
    if score is None:
        raw = _attr(p, "score")
        score = (raw / 4) * 100 if isinstance(raw, (int, float)) else None
    return {
        "id": _attr(p, "docid"),
        "name": name,
        "title": _attr(p, "current_title") or _attr(p, "title"),
        "skills": list(_attr(p, "skills") or []),
        "experiences": list(_attr(p, "experiences") or []),
        "education": list(_attr(p, "education") or []),
        "total_experience_years": _attr(p, "total_experience_years"),
        "summary": _attr(p, "summary"),
        "email": email,
        "location": _attr(p, "location"),
        "match_score": score,
        "is_discovered": bool(_attr(p, "is_discovered", False)),
    }


@register_discrete_handler("sourcing", "search_candidates")
async def handle_search_candidates(
    params: dict[str, Any], actx: ActionContext
) -> DomainResponse:
    """Search candidates for a vacancy via the canonical, tenant-scoped Pearch
    service. Dual-mode: with a ``vacancy_id`` it searches by the enriched JD;
    otherwise it falls back to a free-text query (keeps buscar_e_comparar /
    buscar_e_triar working). Emits BOTH ``candidates`` (for scoring) and
    ``candidate_ids`` (for the legacy compare/screen chains). HONEST: no vacancy
    and no query → clarification; no results → empty success (never faked)."""
    company_id = actx.company_id or actx.tenant_id
    if not company_id:
        return DomainResponse.error_response(
            error="missing_tenant_context",
            message="Não consegui identificar a empresa para a busca.",
            domain_id="sourcing",
            action_id="search_candidates",
        )

    vacancy_id = _pick(params, actx, "vacancy_id", "job_id")
    location = _pick(params, actx, "location")
    limit = _pick(params, actx, "limit") or 20
    job_title = None
    job_description = None
    if vacancy_id:
        jd = await _get_vacancy_jd(str(company_id), str(vacancy_id))
        if not jd:
            return DomainResponse.error_response(
                error="job_not_found",
                message="Não encontrei essa vaga na sua empresa. Pode confirmar qual vaga?",
                domain_id="sourcing",
                action_id="search_candidates",
            )
        job_title = jd.get("title")
        job_description = jd.get("description") or jd.get("title")
        location = location or jd.get("location")

    query = job_description or _pick(params, actx, "query", "raw_query") or (actx.raw_query or "")
    if not query or not str(query).strip():
        return DomainResponse.clarification_response(
            question=(
                "Para buscar candidatos eu preciso de uma vaga ou de uma descrição/termo "
                "de busca. Qual vaga ou perfil você quer buscar?"
            ),
            domain_id="sourcing",
            action_id="search_candidates",
        )

    try:
        service = PearchService()
        resp = await service.search_by_job_description(
            job_description=str(query),
            location=str(location) if location else None,
            limit=int(limit),
            company_id=str(company_id),
        )
    except Exception as exc:
        logger.error("P&E search_candidates Pearch call failed: %s", exc, exc_info=True)
        return DomainResponse.error_response(
            error="search_failed",
            message="Não consegui concluir a busca de candidatos agora. Tente novamente em instantes.",
            domain_id="sourcing",
            action_id="search_candidates",
        )

    profiles: list[Any] = []
    if resp is not None:
        getter = getattr(resp, "get_candidates", None)
        profiles = getter() if callable(getter) else (getattr(resp, "candidates", None) or [])
    candidates = [_profile_to_candidate(p) for p in profiles]
    candidate_ids = [c["id"] for c in candidates if c.get("id")]
    data = {
        "candidates": candidates,
        "candidate_ids": candidate_ids,
        "vacancy_id": vacancy_id,
        "job_id": vacancy_id,
        "job_title": job_title,
    }
    if not candidates:
        return DomainResponse.success_response(
            message="Não encontrei candidatos para essa busca. Quer ajustar os critérios ou a vaga?",
            data=data,
            domain_id="sourcing",
            action_id="search_candidates",
        )
    return DomainResponse.success_response(
        message=f"Encontrei {len(candidates)} candidato(s) para a busca.",
        data=data,
        domain_id="sourcing",
        action_id="search_candidates",
    )


def _build_ranking_message(ranked: list[dict[str, Any]], job_title: str | None = None) -> str:
    """Single chat message with the score ranking (ranking_plus_card UX)."""
    header = "🏅 **Ranking dos candidatos**"
    if job_title:
        header += f" — vaga *{job_title}*"
    lines = [header, ""]
    rank = 0
    for r in ranked:
        if not r.get("success"):
            continue
        rank += 1
        score = r.get("rubric_score")
        score_txt = f"{int(round(score))}%" if isinstance(score, (int, float)) else "—"
        fit = r.get("cv_fit") or "—"
        reco = r.get("recommendation") or "—"
        mark = " ✅" if r.get("approved") else ""
        lines.append(
            f"{rank}. **{r.get('candidate_name') or 'Candidato'}** — "
            f"{score_txt} · Fit: {fit} · {reco}{mark}"
        )
    failed_n = sum(1 for r in ranked if not r.get("success"))
    if failed_n:
        lines.append("")
        lines.append(f"_{failed_n} candidato(s) não puderam ser pontuados._")
    return "\n".join(lines)


@register_discrete_handler("cv_screening", "score_candidates")
async def handle_score_candidates(
    params: dict[str, Any], actx: ActionContext
) -> DomainResponse:
    """Score each searched candidate via the canonical ``score_candidate_standalone``
    (BARS dry-run + FairnessGuard C1 + tenant fail-closed + audit are already
    embedded). Ranks by ``rubric_score`` and marks approved by REUSING the
    service's classification (``sub_status == "cv_approved"``) — never
    re-implements a threshold. HONEST: no candidates → error."""
    company_id = actx.company_id or actx.tenant_id
    if not company_id:
        return DomainResponse.error_response(
            error="missing_tenant_context",
            message="Não consegui identificar a empresa para pontuar os candidatos.",
            domain_id="cv_screening",
            action_id="score_candidates",
        )

    vacancy_id = _pick(params, actx, "vacancy_id", "job_id")
    if not vacancy_id:
        return DomainResponse.clarification_response(
            question="Para qual vaga devo pontuar os candidatos?",
            domain_id="cv_screening",
            action_id="score_candidates",
        )

    raw = _pick(params, actx, "candidates")
    candidates = raw if isinstance(raw, list) else []
    if not candidates:
        return DomainResponse.error_response(
            error="no_candidates",
            message="Não há candidatos para pontuar — faça uma busca primeiro.",
            domain_id="cv_screening",
            action_id="score_candidates",
        )

    service = CVScoringService()
    scored: list[dict[str, Any]] = []
    for cand in candidates:
        cand_id = _attr(cand, "id") or _attr(cand, "candidate_id")
        cand_name = _attr(cand, "name") or "Candidato"
        try:
            result = await service.score_candidate_standalone(
                candidate_data=cand if isinstance(cand, dict) else dict(cand),
                vacancy_id=str(vacancy_id),
                company_id=str(company_id),
                db=None,
            )
        except Exception as exc:
            logger.error("P&E score_candidate_standalone failed: %s", exc, exc_info=True)
            result = None
        if not result or not result.get("success"):
            scored.append(
                {
                    "candidate_id": cand_id,
                    "candidate_name": cand_name,
                    "success": False,
                    "error": (result or {}).get("error", "scoring_failed"),
                }
            )
            continue
        scored.append(
            {
                "candidate_id": result.get("candidate_id") or cand_id,
                "candidate_name": result.get("candidate_name") or cand_name,
                "rubric_score": result.get("rubric_score"),
                "cv_fit": result.get("cv_fit"),
                "recommendation": result.get("recommendation"),
                "sub_status": result.get("sub_status"),
                "approved": result.get("sub_status") == "cv_approved",
                "success": True,
                "evaluation": result,
            }
        )

    ranked = sorted(
        scored,
        key=lambda r: (r.get("rubric_score") if isinstance(r.get("rubric_score"), (int, float)) else -1),
        reverse=True,
    )
    if not any(r.get("success") for r in ranked):
        return DomainResponse.error_response(
            error="scoring_failed",
            message="Não consegui pontuar os candidatos agora.",
            data={"ranking": ranked},
            domain_id="cv_screening",
            action_id="score_candidates",
        )

    approved_ids = [
        r["candidate_id"] for r in ranked if r.get("approved") and r.get("candidate_id")
    ]
    message = _build_ranking_message(ranked, job_title=_pick(params, actx, "job_title"))
    if approved_ids:
        message += f"\n\n{len(approved_ids)} aprovado(s) na triagem por currículo."
    return DomainResponse.success_response(
        message=message,
        data={
            "ranking": ranked,
            "approved_candidate_ids": approved_ids,
            "vacancy_id": vacancy_id,
            "job_id": vacancy_id,
        },
        domain_id="cv_screening",
        action_id="score_candidates",
    )


@register_discrete_handler("cv_screening", "add_approved_to_vacancy")
async def handle_add_approved_to_vacancy(
    params: dict[str, Any], actx: ActionContext
) -> DomainResponse:
    """Add the approved candidates to the vacancy via the canonical
    ``add_candidate_to_vacancy`` (email validation + FairnessGuard C1 on notes +
    tenant scoping + candidate_movement audit are already embedded). HONEST: no
    ids → clarification; reports added/failures per candidate, NEVER faked.

    Gated: only dispatched after a natural PT-BR confirmation (see
    ``pe_add_to_vacancy_continuation``). INVIOLÁVEL (#1211): never creates a job."""
    company_id = actx.company_id or actx.tenant_id
    if not company_id:
        return DomainResponse.error_response(
            error="missing_tenant_context",
            message="Não consegui identificar a empresa para adicionar os candidatos à vaga.",
            domain_id="cv_screening",
            action_id="add_approved_to_vacancy",
        )

    job_id = _pick(params, actx, "job_id", "vacancy_id")
    raw_ids = _pick(params, actx, "approved_candidate_ids", "candidate_ids")
    if isinstance(raw_ids, str):
        approved_ids = [raw_ids]
    elif isinstance(raw_ids, (list, tuple)):
        approved_ids = [str(x) for x in raw_ids if x]
    else:
        approved_ids = []

    if not job_id or not approved_ids:
        return DomainResponse.clarification_response(
            question=(
                "Para adicionar à vaga eu preciso da vaga e de quais candidatos aprovados "
                "adicionar. Quais candidatos e em qual vaga?"
            ),
            domain_id="cv_screening",
            action_id="add_approved_to_vacancy",
        )

    ctx_obj = _DiscreteToolContext(company_id=str(company_id), user_id=actx.user_id)
    added: list[str] = []
    failures: list[dict[str, Any]] = []
    for cid in approved_ids:
        try:
            res = await add_candidate_to_vacancy(
                candidate_id=str(cid),
                job_id=str(job_id),
                initial_stage="Triagem",
                source="sourcing",
                _context=ctx_obj,
            )
        except Exception as exc:
            logger.error("P&E add_candidate_to_vacancy failed: %s", exc, exc_info=True)
            res = {"success": False, "error": "add_failed"}
        if res and res.get("success"):
            added.append(str(cid))
        else:
            failures.append(
                {"candidate_id": str(cid), "error": (res or {}).get("error", "unknown")}
            )

    data = {"added": added, "failures": failures, "job_id": job_id}
    if not added:
        return DomainResponse.error_response(
            error="add_failed",
            message="Não consegui adicionar os candidatos aprovados à vaga.",
            data=data,
            domain_id="cv_screening",
            action_id="add_approved_to_vacancy",
        )
    msg = f"Adicionei {len(added)} candidato(s) aprovado(s) à vaga (etapa Triagem)."
    if failures:
        msg += f" {len(failures)} não pôde(puderam) ser adicionado(s)."
    return DomainResponse.success_response(
        message=msg,
        data=data,
        domain_id="cv_screening",
        action_id="add_approved_to_vacancy",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Task #1229 — Upload, cadastrar e handoff de triagem (item 5)
# ─────────────────────────────────────────────────────────────────────────────


@register_discrete_handler("cv_screening", "parse_and_create_candidate")
async def handle_parse_and_create_candidate(
    params: dict[str, Any], actx: ActionContext
) -> DomainResponse:
    """Parse an uploaded/pasted CV and create the Candidate by REUSING the
    canonical primitive ``cv_upload_tool.parse_and_create_candidate`` (which
    AI-parses the CV and persists the Candidate tenant-scoped via the injected
    ``_context.company_id``). HONEST: no CV text → clarification; no tenant →
    error; primitive failure → error (NEVER faked). Emits ``candidate_id`` /
    ``candidate_name`` so the next step (``add_to_vacancy``) can chain.
    INVIOLÁVEL (#1211): never creates a job."""
    company_id = actx.company_id or actx.tenant_id
    if not company_id:
        return DomainResponse.error_response(
            error="missing_tenant_context",
            message="Não consegui identificar a empresa para cadastrar o candidato.",
            domain_id="cv_screening",
            action_id="parse_and_create_candidate",
        )

    cv_text = _pick(params, actx, "cv_text", "resume_text", "cv", "raw_text", "text")
    if not cv_text or not str(cv_text).strip():
        return DomainResponse.clarification_response(
            question=(
                "Para cadastrar o candidato eu preciso do CV. Envie o arquivo ou "
                "cole o texto do currículo aqui no chat."
            ),
            domain_id="cv_screening",
            action_id="parse_and_create_candidate",
        )

    vacancy_id = _pick(params, actx, "vacancy_id", "job_id")
    vacancy_title = _pick(params, actx, "vacancy_title", "job_title")

    ctx_obj = _DiscreteToolContext(company_id=str(company_id), user_id=actx.user_id)
    try:
        result = await _parse_and_create_candidate_primitive(
            cv_text=str(cv_text),
            vacancy_title=str(vacancy_title) if vacancy_title else None,
            vacancy_id=str(vacancy_id) if vacancy_id else None,
            source="cv_upload",
            _context=ctx_obj,
        )
    except Exception as exc:
        logger.error("P&E parse_and_create_candidate failed: %s", exc, exc_info=True)
        result = {"success": False, "error": "parse_create_failed"}

    if not result or not result.get("success"):
        return DomainResponse.error_response(
            error=(result or {}).get("error", "parse_create_failed"),
            message=(result or {}).get("message")
            or "Não consegui cadastrar o candidato a partir do CV.",
            domain_id="cv_screening",
            action_id="parse_and_create_candidate",
        )

    data = {
        "candidate_id": result.get("candidate_id"),
        "candidate_name": result.get("candidate_name"),
        "vacancy_id": vacancy_id,
        "job_id": vacancy_id,
        "duplicate": result.get("duplicate", False),
    }
    return DomainResponse.success_response(
        message=result.get("message") or "Candidato cadastrado a partir do CV.",
        data=data,
        domain_id="cv_screening",
        action_id="parse_and_create_candidate",
    )


@register_discrete_handler("cv_screening", "add_to_vacancy")
async def handle_add_to_vacancy(
    params: dict[str, Any], actx: ActionContext
) -> DomainResponse:
    """Add the just-created candidate to the vacancy by REUSING the HARDENED
    ``add_candidate_to_vacancy`` (email validation + FairnessGuard C1 on notes +
    tenant scoping + cross_tenant guard + candidate_movement audit are already
    embedded). Chains ``candidate_id`` from ``parse_and_create_candidate``.
    HONEST: missing candidate/vacancy → clarification; missing/invalid email or
    cross-tenant → surfaces the tool's EXPLICIT error (NEVER faked). The
    candidate enters at the classification stage ("Triagem"). INVIOLÁVEL
    (#1211): never creates a job."""
    company_id = actx.company_id or actx.tenant_id
    if not company_id:
        return DomainResponse.error_response(
            error="missing_tenant_context",
            message="Não consegui identificar a empresa para adicionar o candidato à vaga.",
            domain_id="cv_screening",
            action_id="add_to_vacancy",
        )

    candidate_id = _pick(params, actx, "candidate_id")
    job_id = _pick(params, actx, "job_id", "vacancy_id")
    if not candidate_id or not job_id:
        return DomainResponse.clarification_response(
            question=(
                "Para adicionar à vaga eu preciso do candidato e da vaga. "
                "Qual candidato e em qual vaga?"
            ),
            domain_id="cv_screening",
            action_id="add_to_vacancy",
        )

    ctx_obj = _DiscreteToolContext(company_id=str(company_id), user_id=actx.user_id)
    try:
        res = await add_candidate_to_vacancy(
            candidate_id=str(candidate_id),
            job_id=str(job_id),
            initial_stage="Triagem",
            source="cv_upload",
            _context=ctx_obj,
        )
    except Exception as exc:
        logger.error("P&E add_to_vacancy failed: %s", exc, exc_info=True)
        res = {"success": False, "error": "add_failed"}

    if not res or not res.get("success"):
        return DomainResponse.error_response(
            error=(res or {}).get("error", "add_failed"),
            message=(res or {}).get("message")
            or "Não consegui adicionar o candidato à vaga.",
            domain_id="cv_screening",
            action_id="add_to_vacancy",
        )

    inner = res.get("data") or {}
    data = {
        "candidate_id": candidate_id,
        "candidate_name": inner.get("candidate_name"),
        "job_id": job_id,
        "vacancy_id": job_id,
        "stage": inner.get("stage", "Triagem"),
    }
    return DomainResponse.success_response(
        message=res.get("message")
        or "Candidato adicionado à vaga na etapa Triagem.",
        data=data,
        domain_id="cv_screening",
        action_id="add_to_vacancy",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Task #1228 — Gerar/enriquecer JD e avaliar (item 2)
# ─────────────────────────────────────────────────────────────────────────────


async def _enrich_and_persist_jd(company_id: str, vacancy_id: str) -> Any:
    """Open a tenant-scoped session and REUSE the canonical WSI primitive
    ``JdEnrichmentService.enrich_and_persist_vacancy``.

    The primitive embeds the WSI minimums gate (9 técnicas + 5 comportamentais)
    and fail-alto on a missing/invalid vacancy — this wrapper never re-implements
    those rules, it only owns the session lifecycle so the handler stays thin.
    """
    from lia_config.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        return await JdEnrichmentService().enrich_and_persist_vacancy(
            job_vacancy_id=str(vacancy_id),
            company_id=str(company_id),
            db=session,
        )


async def _get_candidate_for_scoring(company_id: str, candidate_id: str) -> dict[str, Any] | None:
    """Tenant-scoped fetch of a candidate's data for standalone BARS scoring.

    Returns ``None`` when the candidate does not exist FOR THIS TENANT so the
    caller surfaces an honest clarification instead of scoring a cross-tenant id.
    SECURITY: ``candidate_id`` is untrusted (LLM/client) — the ``company_id``
    filter is what blocks cross-tenant evaluation.
    """
    if not company_id or not candidate_id:
        return None
    try:
        from sqlalchemy import text

        from lia_config.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(
                    """
                    SELECT id, name, current_title, summary, resume_text,
                           technical_skills, soft_skills, total_experience_years,
                           location_city, location_state, self_introduction
                    FROM candidates
                    WHERE id = :cid AND company_id = :company_id
                    LIMIT 1
                    """
                ),
                {"cid": str(candidate_id), "company_id": str(company_id)},
            )
            row = result.fetchone()
            if not row:
                return None
            return {
                "id": str(row[0]),
                "name": row[1] or "Candidato",
                "title": row[2],
                "summary": row[3],
                "resume_text": row[4],
                "skills": list(row[5] or []),
                "soft_skills": list(row[6] or []),
                "total_experience_years": row[7],
                "location": " ".join(x for x in [row[8], row[9]] if x) or None,
                "self_introduction": row[10],
            }
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Candidate lookup for scoring failed: %s", exc, exc_info=True)
        return None


@register_discrete_handler("job_management", "generate_jd")
async def handle_generate_jd(params: dict[str, Any], actx: ActionContext) -> DomainResponse:
    """Generate→enrich→PERSIST a real vacancy's JD via the canonical WSI primitive.

    INVIOLÁVEL (#1211): este handler NUNCA cria vaga — ele só enriquece uma vaga
    EXISTENTE (exige ``vacancy_id``). HONESTO: sem vaga → clarification; mínimos
    WSI não atingidos → clarification explicando o que falta (``persisted=False``,
    o serviço NÃO grava "no vácuo"); persistido → success + emite ``jd_data`` (com
    ``vacancy_id``) para encadear no ``evaluate_against_jd``.
    """
    company_id = actx.company_id or actx.tenant_id
    if not company_id:
        return DomainResponse.error_response(
            error="missing_tenant_context",
            message="Não consegui identificar a empresa para enriquecer a JD.",
            domain_id="job_management",
            action_id="generate_jd",
        )

    vacancy_id = _pick(params, actx, "vacancy_id", "job_id")
    if not vacancy_id:
        return DomainResponse.clarification_response(
            question=(
                "Para gerar e enriquecer a descrição (JD) eu preciso saber QUAL vaga. "
                "Qual vaga você quer enriquecer?"
            ),
            domain_id="job_management",
            action_id="generate_jd",
        )

    try:
        result = await _enrich_and_persist_jd(company_id=str(company_id), vacancy_id=str(vacancy_id))
    except ValueError as exc:
        # fail-alto do primitivo (id inválido / vaga inexistente) — honesto
        return DomainResponse.error_response(
            error="jd_enrichment_invalid",
            message="Não encontrei essa vaga na sua empresa para enriquecer. Pode confirmar qual vaga?",
            domain_id="job_management",
            action_id="generate_jd",
            metadata={"detail": str(exc)},
        )
    except Exception as exc:
        logger.error("P&E generate_jd enrich_and_persist failed: %s", exc, exc_info=True)
        return DomainResponse.error_response(
            error="jd_enrichment_failed",
            message="Não consegui enriquecer a JD agora. Tente novamente em instantes.",
            domain_id="job_management",
            action_id="generate_jd",
        )

    jd_data = {
        "vacancy_id": result.job_vacancy_id or str(vacancy_id),
        "persisted": result.persisted,
        "meets_wsi_minimums": result.meets_wsi_minimums,
        "wsi_quality_score": result.wsi_quality_score,
        "technical_count": result.technical_count,
        "behavioral_count": result.behavioral_count,
        "responsibilities_count": result.responsibilities_count,
    }

    if not result.success:
        return DomainResponse.error_response(
            error=result.error or "jd_enrichment_failed",
            message=result.message or "Não foi possível enriquecer a JD desta vaga.",
            data={"jd_data": jd_data},
            domain_id="job_management",
            action_id="generate_jd",
        )

    if not result.persisted:
        # mínimos WSI não atingidos: honesto, pede mais info (não finge sucesso)
        return DomainResponse.clarification_response(
            question=(
                result.message
                or "A descrição ainda não atingiu os mínimos WSI (9 competências técnicas "
                "e 5 comportamentais). Pode me dar mais detalhes da vaga?"
            ),
            data={"jd_data": jd_data},
            domain_id="job_management",
            action_id="generate_jd",
        )

    return DomainResponse.success_response(
        message=result.message or "JD enriquecida e salva na vaga.",
        data={"jd_data": jd_data},
        metadata={"wsi_quality_score": result.wsi_quality_score},
        domain_id="job_management",
        action_id="generate_jd",
    )


@register_discrete_handler("cv_screening", "evaluate_against_jd")
async def handle_evaluate_against_jd(
    params: dict[str, Any], actx: ActionContext
) -> DomainResponse:
    """Evaluate candidate(s) against the (enriched) vacancy JD via the canonical
    ``score_candidate_standalone`` — the MESMO primitivo do item 1 (BARS dry-run +
    FairnessGuard C1 + tenant fail-closed + audit já embutidos). Resolve a vaga do
    ``jd_data`` encadeado ou dos params; pega candidatos do contexto (dicts) OU
    carrega por id tenant-scoped. Retorna o payload BARS no padrão do modal de CV
    (``evaluations``) + ranking. HONESTO: sem vaga/candidato → clarification;
    nenhum candidato pontuado → erro (nunca finge sucesso)."""
    company_id = actx.company_id or actx.tenant_id
    if not company_id:
        return DomainResponse.error_response(
            error="missing_tenant_context",
            message="Não consegui identificar a empresa para avaliar o candidato.",
            domain_id="cv_screening",
            action_id="evaluate_against_jd",
        )

    jd_data = params.get("jd_data") if isinstance(params.get("jd_data"), dict) else {}
    vacancy_id = jd_data.get("vacancy_id") or _pick(params, actx, "vacancy_id", "job_id")
    if not vacancy_id:
        return DomainResponse.clarification_response(
            question="Contra qual vaga devo avaliar o(s) candidato(s)?",
            domain_id="cv_screening",
            action_id="evaluate_against_jd",
        )

    raw = _pick(params, actx, "candidates")
    candidates: list[Any] = list(raw) if isinstance(raw, list) else []
    if not candidates:
        raw_ids = _pick(params, actx, "candidate_ids", "candidate_id")
        if isinstance(raw_ids, str):
            ids = [raw_ids]
        elif isinstance(raw_ids, (list, tuple)):
            ids = [str(x) for x in raw_ids if x]
        elif raw_ids is not None:
            ids = [str(raw_ids)]
        else:
            ids = []
        for cid in ids:
            cand = await _get_candidate_for_scoring(str(company_id), str(cid))
            if cand:
                candidates.append(cand)

    if not candidates:
        return DomainResponse.clarification_response(
            question="Qual candidato você quer avaliar contra essa vaga?",
            domain_id="cv_screening",
            action_id="evaluate_against_jd",
        )

    service = CVScoringService()
    scored: list[dict[str, Any]] = []
    evaluations: list[dict[str, Any]] = []
    for cand in candidates:
        cand_id = _attr(cand, "id") or _attr(cand, "candidate_id")
        cand_name = _attr(cand, "name") or "Candidato"
        try:
            result = await service.score_candidate_standalone(
                candidate_data=cand if isinstance(cand, dict) else dict(cand),
                vacancy_id=str(vacancy_id),
                company_id=str(company_id),
                db=None,
            )
        except Exception as exc:
            logger.error("P&E evaluate score_candidate_standalone failed: %s", exc, exc_info=True)
            result = None
        if not result or not result.get("success"):
            scored.append(
                {
                    "candidate_id": cand_id,
                    "candidate_name": cand_name,
                    "success": False,
                    "error": (result or {}).get("error", "scoring_failed"),
                }
            )
            continue
        evaluations.append(result)
        scored.append(
            {
                "candidate_id": result.get("candidate_id") or cand_id,
                "candidate_name": result.get("candidate_name") or cand_name,
                "rubric_score": result.get("rubric_score"),
                "cv_fit": result.get("cv_fit"),
                "recommendation": result.get("recommendation"),
                "sub_status": result.get("sub_status"),
                "approved": result.get("sub_status") == "cv_approved",
                "success": True,
                "evaluation": result,
            }
        )

    ranked = sorted(
        scored,
        key=lambda r: (r.get("rubric_score") if isinstance(r.get("rubric_score"), (int, float)) else -1),
        reverse=True,
    )
    if not any(r.get("success") for r in ranked):
        return DomainResponse.error_response(
            error="evaluation_failed",
            message="Não consegui avaliar o(s) candidato(s) contra essa vaga agora.",
            data={"ranking": ranked, "vacancy_id": vacancy_id},
            domain_id="cv_screening",
            action_id="evaluate_against_jd",
        )

    message = _build_ranking_message(ranked, job_title=_pick(params, actx, "job_title"))
    return DomainResponse.success_response(
        message=message,
        data={
            "ranking": ranked,
            "evaluations": evaluations,
            "vacancy_id": vacancy_id,
            "job_id": vacancy_id,
        },
        domain_id="cv_screening",
        action_id="evaluate_against_jd",
    )
