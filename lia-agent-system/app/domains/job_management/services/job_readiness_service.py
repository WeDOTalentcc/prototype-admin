"""
Job Readiness Service (Task #429)

Classifier + orchestrator for the Job Readiness Hub. Given a JobVacancy row,
decides which of the 7 canonical readiness stages it belongs to and which
next action LIA should take to move it forward.

This service is intentionally side-effect free for classification — pure
function over the row's current shape — so it can be safely used both at
read-time (Hub overview/board) and as the source-of-truth for write-time
state transitions.

Stages (canonical order):
    importada            → ATS row, nothing decided yet
    sem_jd               → no description / no enriched_jd
    jd_rascunho          → description present, no AI enrichment
    jd_enriquecido       → AI-enriched JD waiting for human OK
    perguntas_triagem    → screening_questions generated, waiting OK
    pronta_disparo       → questions approved, awaiting audience policy
    em_triagem           → screening live (sessions in progress)
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Iterable, Optional
from uuid import UUID

from lia_models.job_vacancy import JobVacancy

logger = logging.getLogger(__name__)


# ── Stage constants ─────────────────────────────────────────────────────────
STAGE_IMPORTADA = "importada"
STAGE_SEM_JD = "sem_jd"
STAGE_JD_RASCUNHO = "jd_rascunho"
STAGE_JD_ENRIQUECIDO = "jd_enriquecido"
STAGE_PERGUNTAS_TRIAGEM = "perguntas_triagem"
STAGE_PRONTA_DISPARO = "pronta_disparo"
STAGE_EM_TRIAGEM = "em_triagem"

CANONICAL_STAGES: tuple[str, ...] = (
    STAGE_IMPORTADA,
    STAGE_SEM_JD,
    STAGE_JD_RASCUNHO,
    STAGE_JD_ENRIQUECIDO,
    STAGE_PERGUNTAS_TRIAGEM,
    STAGE_PRONTA_DISPARO,
    STAGE_EM_TRIAGEM,
)

STAGE_LABELS_PT: dict[str, str] = {
    STAGE_IMPORTADA: "Importada",
    STAGE_SEM_JD: "Sem Job Description",
    STAGE_JD_RASCUNHO: "JD Rascunho",
    STAGE_JD_ENRIQUECIDO: "JD Enriquecido",
    STAGE_PERGUNTAS_TRIAGEM: "Perguntas de Triagem",
    STAGE_PRONTA_DISPARO: "Pronta para Disparo",
    STAGE_EM_TRIAGEM: "Em Triagem",
}

# Stages that require human approval before LIA can advance.
HITL_STAGES: frozenset[str] = frozenset({
    STAGE_JD_ENRIQUECIDO,
    STAGE_PERGUNTAS_TRIAGEM,
    STAGE_PRONTA_DISPARO,
})

# Allowed audience policies for screening dispatch.
AUDIENCE_POLICIES: frozenset[str] = frozenset({
    "new_only",
    "imported_untriaged",
    "manual_selection",
})


# ── Action codes (used by orchestrator + audit log) ─────────────────────────
ACTION_GENERATE_JD = "generate_jd"
ACTION_ENRICH_JD = "enrich_jd"
ACTION_GENERATE_QUESTIONS = "generate_questions"
ACTION_APPROVE_STAGE = "approve_stage"
ACTION_REJECT_STAGE = "reject_stage"
ACTION_DISPATCH_SCREENING = "dispatch_screening"

# Map current stage → next LIA action (None means "waiting on human").
NEXT_ACTION_BY_STAGE: dict[str, Optional[str]] = {
    STAGE_IMPORTADA: ACTION_GENERATE_JD,
    STAGE_SEM_JD: ACTION_GENERATE_JD,
    STAGE_JD_RASCUNHO: ACTION_ENRICH_JD,
    STAGE_JD_ENRIQUECIDO: None,           # human approval gate
    STAGE_PERGUNTAS_TRIAGEM: None,        # human approval gate
    STAGE_PRONTA_DISPARO: None,           # human dispatch gate
    STAGE_EM_TRIAGEM: None,
}


# ── Pure classifier ─────────────────────────────────────────────────────────

def _has_questions(job: JobVacancy) -> bool:
    qs = job.screening_questions or []
    return bool(qs) and len(qs) > 0


def _questions_approved(job: JobVacancy) -> bool:
    """True when every screening question carries an explicit ``approved`` flag.

    A freshly generated question package is considered *not* approved until the
    recruiter signs off via ``approve_stage`` — that is the HITL gate for the
    ``perguntas_triagem`` stage. We require *all* questions to be flagged so a
    partial-approval state cannot accidentally promote the job to
    ``pronta_disparo``.
    """
    qs = job.screening_questions or []
    if not qs:
        return False
    for q in qs:
        if not isinstance(q, dict):
            # Legacy shape (plain strings) — treat as unapproved so the
            # recruiter has to review it explicitly. Backfill is responsible
            # for stamping approved=True on jobs already screening live.
            return False
        if not q.get("approved"):
            return False
    return True


def _has_enriched(job: JobVacancy) -> bool:
    enriched = job.enriched_jd or None
    if not enriched:
        return False
    if isinstance(enriched, dict) and not enriched:
        return False
    return True


def _has_description(job: JobVacancy) -> bool:
    return bool((job.description or "").strip())


def _is_screening_live(job: JobVacancy) -> bool:
    cfg = job.screening_config or {}
    status = (cfg.get("status") or {}).get("screening_status", "").lower()
    return status in ("active", "paused", "completed")


def _from_ats(job: JobVacancy) -> bool:
    """A vacancy is considered ATS-imported if it has a non-LIA source_system."""
    src = (job.source_system or "").lower()
    if not src:
        # Fall back to legacy heuristic for backfill safety.
        ad = job.additional_data or {}
        return bool(
            ad.get("imported_from_ats") in (True, "true", "True")
            or ad.get("external_system_id")
            or ad.get("ats_external_id")
        )
    return not src.startswith("lia")


def classify(job: JobVacancy) -> str:
    """Return the canonical readiness stage for ``job``.

    Pure function — does not mutate or persist. Order matters: the most
    advanced applicable stage wins.
    """
    if _is_screening_live(job):
        return STAGE_EM_TRIAGEM
    if _has_questions(job):
        # Questions exist but the recruiter still has to approve them.
        # Only an explicit approve_stage() call (which stamps approved=True
        # on every question) promotes the row to pronta_disparo.
        if _questions_approved(job):
            return STAGE_PRONTA_DISPARO
        return STAGE_PERGUNTAS_TRIAGEM
    if _has_enriched(job):
        return STAGE_JD_ENRIQUECIDO
    if _has_description(job):
        return STAGE_JD_RASCUNHO
    if _from_ats(job):
        return STAGE_SEM_JD
    return STAGE_IMPORTADA


def compute_blockers(job: JobVacancy) -> list[str]:
    """Return a list of human-actionable blocker codes for the row."""
    blockers: list[str] = []
    if not _has_description(job) and not _has_enriched(job):
        blockers.append("missing_jd")
    if not _has_enriched(job):
        blockers.append("missing_enrichment")
    if not (job.behavioral_competencies or []):
        blockers.append("missing_competencies")
    if not _has_questions(job):
        blockers.append("missing_questions")
    return blockers


def next_action(job: JobVacancy) -> Optional[str]:
    """Next LIA action that can be auto-executed without a human, or None."""
    stage = classify(job)
    return NEXT_ACTION_BY_STAGE.get(stage)


def requires_human(job: JobVacancy) -> bool:
    """True if the current stage is gated on a human decision."""
    return classify(job) in HITL_STAGES


# ── Orchestrator ────────────────────────────────────────────────────────────

class JobReadinessService:
    """Orchestrates classification, HITL transitions and async enqueueing."""

    def __init__(self, db, audit_service: Any | None = None, task_manager: Any | None = None):
        self.db = db
        self._audit = audit_service
        self._tasks = task_manager

    # ── State sync ──────────────────────────────────────────────────────
    async def reclassify_and_persist(
        self,
        job: JobVacancy,
        *,
        actor: str = "lia",
    ) -> JobVacancy:
        """Recompute stage + blockers and persist if changed."""
        new_stage = classify(job)
        new_blockers = compute_blockers(job)
        old_stage = job.readiness_stage

        changed = (
            new_stage != old_stage
            or list(new_blockers) != list(job.readiness_blockers or [])
        )
        if not changed:
            return job

        job.readiness_stage = new_stage
        job.readiness_blockers = new_blockers
        job.last_readiness_event_at = datetime.utcnow()
        await self.db.flush()

        if old_stage and old_stage != new_stage:
            await self._audit_transition(job, old_stage, new_stage, actor=actor)
        return job

    # ── HITL transitions ────────────────────────────────────────────────
    async def approve_stage(self, job: JobVacancy, *, actor: str) -> JobVacancy:
        """Move a HITL-gated row to the next stage when the human signs off."""
        stage = classify(job)
        if stage == STAGE_JD_ENRIQUECIDO:
            # Mark enrichment as approved by stamping a flag in enriched_jd.
            enriched = dict(job.enriched_jd or {})
            enriched["approved_by"] = actor
            enriched["approved_at"] = datetime.utcnow().isoformat()
            job.enriched_jd = enriched
            # Next action: generate questions. We'll *enqueue*, classifier
            # will move the row to perguntas_triagem after questions land.
            await self._enqueue(job, ACTION_GENERATE_QUESTIONS, actor=actor)
        elif stage == STAGE_PERGUNTAS_TRIAGEM:
            # Approving the questions package transitions to pronta_disparo
            # (classifier handles it via _has_questions).
            qs = list(job.screening_questions or [])
            for q in qs:
                if isinstance(q, dict):
                    q["approved"] = True
            job.screening_questions = qs
        elif stage == STAGE_PRONTA_DISPARO:
            raise ValueError("dispatch_screening must be used to leave 'pronta_disparo'")
        else:
            raise ValueError(f"stage {stage!r} is not a HITL gate")

        return await self.reclassify_and_persist(job, actor=actor)

    async def reject_stage(self, job: JobVacancy, *, actor: str, reason: str = "") -> JobVacancy:
        """Recruiter rejects the current AI artifact — drop it and step back."""
        stage = classify(job)
        if stage == STAGE_JD_ENRIQUECIDO:
            job.enriched_jd = None
        elif stage == STAGE_PERGUNTAS_TRIAGEM:
            job.screening_questions = []
        else:
            raise ValueError(f"stage {stage!r} cannot be rejected")
        # Audit trail captures the reason.
        await self._audit_transition(
            job, stage, classify(job), actor=actor, reason=reason or "rejected"
        )
        return await self.reclassify_and_persist(job, actor=actor)

    async def dispatch_screening(
        self,
        job: JobVacancy,
        *,
        actor: str,
        audience_policy: str,
    ) -> JobVacancy:
        """Recruiter chose the audience policy and is firing the screening.

        We mark the row as ``em_triagem`` by flipping screening_config.status
        to ``active``; the actual session creation is delegated to the
        existing TriagemSessionService via the async task manager (best-effort
        — falls back to the in-process flag flip if the queue is unavailable).
        """
        if audience_policy not in AUDIENCE_POLICIES:
            raise ValueError(
                f"invalid audience_policy {audience_policy!r}. "
                f"Allowed: {sorted(AUDIENCE_POLICIES)}"
            )
        if classify(job) != STAGE_PRONTA_DISPARO:
            raise ValueError("job is not in 'pronta_disparo' stage")

        cfg = dict(job.screening_config or {})
        status = dict(cfg.get("status") or {})
        status["screening_status"] = "active"
        status["enabled"] = True
        status["dispatched_by"] = actor
        status["dispatched_at"] = datetime.utcnow().isoformat()
        status["audience_policy"] = audience_policy
        cfg["status"] = status
        job.screening_config = cfg
        job.assigned_audience_policy = audience_policy

        await self._enqueue(
            job,
            ACTION_DISPATCH_SCREENING,
            actor=actor,
            extra={"audience_policy": audience_policy},
        )
        return await self.reclassify_and_persist(job, actor=actor)

    # ── Batch ───────────────────────────────────────────────────────────
    async def run_batch(
        self,
        jobs: Iterable[JobVacancy],
        *,
        actor: str = "lia",
    ) -> dict[str, Any]:
        """Enqueue the next-action for every job that has one.

        Returns a summary of what was enqueued / skipped, never raises so a
        single bad row cannot poison the batch.
        """
        enqueued: list[str] = []
        skipped_human: list[str] = []
        errors: list[dict[str, str]] = []
        for job in jobs:
            try:
                action = next_action(job)
                if action is None:
                    skipped_human.append(str(job.id))
                    continue
                await self._enqueue(job, action, actor=actor)
                enqueued.append(str(job.id))
            except Exception as exc:  # noqa: BLE001 — defensive, batch-level
                logger.warning(
                    "[JobReadinessService] enqueue failed job_id=%s err=%s",
                    getattr(job, "id", "?"), exc,
                )
                errors.append({"job_id": str(getattr(job, "id", "?")), "error": str(exc)})
        return {
            "enqueued": enqueued,
            "skipped_human_required": skipped_human,
            "errors": errors,
            "total": len(enqueued) + len(skipped_human) + len(errors),
        }

    # ── Internals ───────────────────────────────────────────────────────
    # Window during which the same readiness action will not be
    # re-enqueued for the same job (idempotency guard for HITL approvals
    # and run-all/run-batch). Async handlers (#449) will clear this stamp
    # explicitly when they finish or fail; until then this prevents a
    # recruiter from accidentally enqueuing the same task many times.
    _ENQUEUE_DEDUPE_SECONDS = 300

    async def _enqueue(
        self,
        job: JobVacancy,
        action: str,
        *,
        actor: str,
        extra: dict | None = None,
    ) -> Optional[str]:
        """Submit a task to the DomainTaskManager. Best-effort + idempotent.

        Stores a ``{action, at}`` stamp under
        ``screening_config["readiness"]["pending_action"]`` and refuses to
        enqueue the same action again until the stamp is older than
        ``_ENQUEUE_DEDUPE_SECONDS`` seconds.
        """
        cfg = dict(job.screening_config or {})
        readiness_meta = dict(cfg.get("readiness") or {})
        pending = readiness_meta.get("pending_action") or {}
        if pending.get("action") == action and pending.get("at"):
            try:
                last = datetime.fromisoformat(pending["at"])
                if (datetime.utcnow() - last).total_seconds() < self._ENQUEUE_DEDUPE_SECONDS:
                    logger.info(
                        "[JobReadinessService] dedupe: action=%s job_id=%s already pending",
                        action, job.id,
                    )
                    return pending.get("task_id")
            except (TypeError, ValueError):
                pass

        if self._tasks is None:
            logger.info(
                "[JobReadinessService] task_manager unavailable, action=%s job_id=%s",
                action, job.id,
            )
            readiness_meta["pending_action"] = {
                "action": action,
                "at": datetime.utcnow().isoformat(),
                "actor": actor,
                "task_id": None,
            }
            cfg["readiness"] = readiness_meta
            job.screening_config = cfg
            return None
        try:
            params = {
                "job_id": str(job.id),
                "company_id": job.company_id,
                "action": action,
                "actor": actor,
            }
            if extra:
                params.update(extra)
            task_id = await self._tasks.submit_task(
                domain_id="job_management",
                action_id=f"readiness_{action}",
                params=params,
                user_id=actor,
            )
            readiness_meta["pending_action"] = {
                "action": action,
                "at": datetime.utcnow().isoformat(),
                "actor": actor,
                "task_id": task_id,
            }
            cfg["readiness"] = readiness_meta
            job.screening_config = cfg
            return task_id
        except Exception as exc:  # noqa: BLE001 — observability path
            logger.warning(
                "[JobReadinessService] task submission failed action=%s job_id=%s err=%s",
                action, job.id, exc,
            )
            return None

    async def _audit_transition(
        self,
        job: JobVacancy,
        old_stage: str,
        new_stage: str,
        *,
        actor: str,
        reason: str = "",
    ) -> None:
        if self._audit is None:
            return
        try:
            # Reuse the generic update logger if available.
            logger_method = getattr(self._audit, "log_update", None)
            if logger_method is None:
                return
            await logger_method(
                job_id=str(job.id),
                changed_by=actor,
                company_id=job.company_id,
                db=self.db,
                changes={
                    "readiness_stage": {
                        "old": old_stage,
                        "new": new_stage,
                        "reason": reason,
                    }
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug(
                "[JobReadinessService] audit log skipped: %s", exc
            )


__all__ = [
    "JobReadinessService",
    "classify",
    "compute_blockers",
    "next_action",
    "requires_human",
    "CANONICAL_STAGES",
    "STAGE_LABELS_PT",
    "AUDIENCE_POLICIES",
    "HITL_STAGES",
    "STAGE_IMPORTADA",
    "STAGE_SEM_JD",
    "STAGE_JD_RASCUNHO",
    "STAGE_JD_ENRIQUECIDO",
    "STAGE_PERGUNTAS_TRIAGEM",
    "STAGE_PRONTA_DISPARO",
    "STAGE_EM_TRIAGEM",
    "ACTION_GENERATE_JD",
    "ACTION_ENRICH_JD",
    "ACTION_GENERATE_QUESTIONS",
    "ACTION_DISPATCH_SCREENING",
]
