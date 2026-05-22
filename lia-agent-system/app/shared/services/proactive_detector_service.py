"""
WT-2022 Camada IA Proativa - Service canonical de detection de hints.

CONTEXTO HISTORICO (registrado 2026-05-21):
=============================================
Camada IA reativa (chat turn) ja existe via `proactive_actions` endpoints +
`ProactiveActionsBell`. Faltava o LADO SCHEDULER-DRIVEN: 1x/hora um detector
varre o estado da empresa e identifica HINTS de UX (profile incompleto, DSR
estourando SLA, candidatos sem feedback, plano de workforce stale, etc).

Esses hints sao PROACTIVE_ACTION rows com action_type="suggestion" persistidas
em proactive_actions. UI consome via GET /api/v1/proactive-hints (separado dos
endpoints /proactive-actions/pending/{company_id} que cuidam de actions
candidato-especificas).

DETECTORS:
- CompanyProfileCompletionDetector - profile_completion_percentage < 80
- DSROverdueDetector              - sla_deadline em < 24h e status pending
- CandidateStaleDetector          - 7+ dias sem feedback no candidato
- WorkforcePlanStaleDetector      - last_updated > 30 dias atras
- AICreditsLowDetector            - balance < 20% do plano contratado
- PipelineStuckDetector           - vagas em screening > 14 dias

PATTERN:
- Cada detector implementa BaseDetector.detect(db, company_id) -> list[hint]
- Service agrega + escreve em proactive_actions com action_type "suggestion"
- Deduplica: nao insere segundo hint do mesmo detector enquanto o anterior
  esta PENDING para a mesma company.

CONSUMER:
- app/jobs/tasks/proactive.py (Celery beat task hourly)
- app/api/v1/proactive_hints.py (REST GET + DISMISS)

MULTI-TENANCY:
- Cada detector recebe company_id e SO opera dentro daquela company.
- Persist usa ProactiveAction.company_id = company_uuid. Cross-tenant impossivel
  por design.

SENSOR ANTI-REGRESSAO:
- scripts/check_proactive_detectors_registered.py garante que toda classe
  XxxDetector(BaseDetector) declarada neste arquivo esta no
  ProactiveDetectorService.detectors list (evita drift silencioso).

PRODUCTION-QUALITY:
- Cada detector wrapeia logica em try/except (um detector quebrado nao derruba
  os outros 5).
- _persist_hints idempotente: usa unique constraint logica (detector + company
  + status=pending) para evitar duplicates.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Severity normalization
# ---------------------------------------------------------------------------
# Hints sao mapeados para ActionPriority no momento do persist. Manter alinhado
# com libs/models/lia_models/background_jobs.py:ActionPriority.

_SEVERITY_TO_PRIORITY = {
    "low": "low",
    "medium": "normal",
    "high": "high",
    "critical": "urgent",
}


def _normalize_priority(severity: str) -> str:
    """Map detector severity -> ActionPriority value."""
    return _SEVERITY_TO_PRIORITY.get(severity, "normal")


# ---------------------------------------------------------------------------
# Base detector contract
# ---------------------------------------------------------------------------


class BaseDetector(ABC):
    """Base class para todos os proactive detectors.

    Cada subclass DEVE definir:
    - name: identificador estavel (usado para deduplicar hints + AST sensor)
    - severity: low | medium | high | critical
    - detect(db, company_id) -> list[dict]
    """

    name: str = ""
    severity: str = "medium"

    @abstractmethod
    async def detect(
        self, db: "AsyncSession", company_id: str
    ) -> list[dict[str, Any]]:
        """Returns list of hints. Each hint:
        {
            "title": str,                 # 255 chars max
            "message": str,               # detail / description
            "action": str,                # frontend ui_action key
            "action_params": dict,
            "severity": str,              # low | medium | high | critical
            "expires_in_hours": int | None,
            "related_job_id": str | None,
            "related_candidate_id": str | None,
        }
        """
        ...


# ---------------------------------------------------------------------------
# Detector implementations
# ---------------------------------------------------------------------------


class CompanyProfileCompletionDetector(BaseDetector):
    """Trigger quando profile da empresa esta < 80% completo."""

    name = "company_profile_completion"
    severity = "low"

    REQUIRED_FIELDS = [
        "name",
        "industry",
        "company_size",
        "description",
        "headquarters_city",
        "main_email",
        "linkedin_url",
        "employee_count",
        "founded_year",
        "website",
    ]

    async def detect(self, db, company_id):
        try:
            from sqlalchemy import select

            from libs.models.lia_models.company import CompanyProfile
        except Exception as exc:
            logger.warning("CompanyProfileCompletionDetector import failed: %s", exc)
            return []

        try:
            company_uuid = UUID(company_id)
        except ValueError:
            return []

        result = await db.execute(
            select(CompanyProfile).where(
                CompanyProfile.client_account_id == company_uuid,
                CompanyProfile.is_active.is_(True),
            ).limit(1)
        )
        profile = result.scalars().first()
        if profile is None:
            return []

        filled = sum(
            1
            for field in self.REQUIRED_FIELDS
            if getattr(profile, field, None) not in (None, "", 0)
        )
        percentage = (filled / len(self.REQUIRED_FIELDS)) * 100

        if percentage >= 80:
            return []

        missing = [
            field
            for field in self.REQUIRED_FIELDS
            if getattr(profile, field, None) in (None, "", 0)
        ]

        return [
            {
                "title": f"Perfil da empresa esta {percentage:.0f}% completo",
                "message": (
                    "Completar o perfil ajuda a LIA a calibrar tom, JD e "
                    f"matching. Faltam: {', '.join(missing[:5])}."
                ),
                "action": "navigate_to_company_data",
                "action_params": {"missing_fields": missing},
                "severity": self.severity,
                "expires_in_hours": 24 * 7,
                "related_job_id": None,
                "related_candidate_id": None,
            }
        ]


class DSROverdueDetector(BaseDetector):
    """Trigger quando DSR (LGPD Art.18) chegando perto do SLA legal (15 dias)."""

    name = "dsr_overdue"
    severity = "high"

    # Margem de aviso: alertar quando faltam < 24h para deadline
    WARN_MARGIN_HOURS = 24

    async def detect(self, db, company_id):
        try:
            from sqlalchemy import and_, or_, select

            from libs.models.lia_models.observability import (
                DataSubjectRequest,
                DataSubjectRequestStatusEnum,
            )
        except Exception as exc:
            logger.warning("DSROverdueDetector import failed: %s", exc)
            return []

        try:
            company_uuid = UUID(company_id)
        except ValueError:
            return []

        now = datetime.utcnow()
        cutoff = now + timedelta(hours=self.WARN_MARGIN_HOURS)
        active_statuses = [
            DataSubjectRequestStatusEnum.PENDING.value,
            DataSubjectRequestStatusEnum.IN_REVIEW.value,
            DataSubjectRequestStatusEnum.PROCESSING.value,
        ]

        result = await db.execute(
            select(DataSubjectRequest).where(
                and_(
                    DataSubjectRequest.company_id == company_uuid,
                    DataSubjectRequest.status.in_(active_statuses),
                    DataSubjectRequest.sla_deadline.is_not(None),
                    or_(
                        DataSubjectRequest.sla_deadline <= cutoff,
                        DataSubjectRequest.sla_deadline <= now,
                    ),
                )
            ).limit(10)
        )
        overdue = list(result.scalars().all())
        if not overdue:
            return []

        critical = [dsr for dsr in overdue if dsr.sla_deadline <= now]
        severity = "critical" if critical else self.severity

        return [
            {
                "title": (
                    f"{len(critical)} DSR(s) vencido(s)"
                    if critical
                    else f"{len(overdue)} DSR(s) vencendo em 24h"
                ),
                "message": (
                    "LGPD Art. 18 obriga responder em 15 dias corridos. "
                    f"Total ativos com risco: {len(overdue)}."
                ),
                "action": "navigate_to_compliance_dsr",
                "action_params": {
                    "ids": [str(dsr.id) for dsr in overdue[:5]],
                    "critical_count": len(critical),
                },
                "severity": severity,
                "expires_in_hours": 12,
                "related_job_id": None,
                "related_candidate_id": None,
            }
        ]


class CandidateStaleDetector(BaseDetector):
    """Trigger quando candidato esta 7+ dias sem feedback / mudanca de estagio."""

    name = "candidate_stale"
    severity = "medium"

    STALE_DAYS = 7
    BATCH_SIZE = 50

    async def detect(self, db, company_id):
        """Detecta candidatos em estagios interview/screening sem update >= 7 dias.

        Query canonical: JOIN VacancyCandidate x JobVacancy filtrando por
        company_id (multi-tenancy fail-closed) + status canonical pos-triagem
        + updated_at < cutoff. Agrupa por vaga para gerar 1 hint por vaga
        (evita flood na bell quando ha varias vagas com candidatos parados).
        """
        try:
            from sqlalchemy import func, select

            from app.models.candidate import VacancyCandidate
            from app.models.job_vacancy import JobVacancy
        except Exception as exc:
            logger.warning("CandidateStaleDetector import failed: %s", exc)
            return []

        # Valida UUID format (graceful para input invalido).
        try:
            UUID(company_id)
        except (ValueError, TypeError, AttributeError):
            return []

        cutoff = datetime.utcnow() - timedelta(days=self.STALE_DAYS)
        stale_statuses = ["interview", "screening", "final_evaluation"]

        try:
            result = await db.execute(
                select(
                    JobVacancy.id,
                    JobVacancy.title,
                    func.count(VacancyCandidate.id).label("stale_count"),
                )
                .join(
                    VacancyCandidate,
                    VacancyCandidate.vacancy_id == JobVacancy.id,
                )
                .where(
                    JobVacancy.company_id == company_id,
                    VacancyCandidate.company_id == company_id,
                    VacancyCandidate.updated_at < cutoff,
                    VacancyCandidate.status.in_(stale_statuses),
                )
                .group_by(JobVacancy.id, JobVacancy.title)
                .having(func.count(VacancyCandidate.id) > 0)
                .limit(self.BATCH_SIZE)
            )
            rows = result.all()
        except Exception as exc:
            logger.debug(
                "CandidateStaleDetector query failed (table may not exist): %s",
                exc,
            )
            return []

        hints = []
        for row in rows:
            hints.append(
                {
                    "title": f"Candidatos sem feedback ha {self.STALE_DAYS}+ dias",
                    "message": (
                        f"{row.stale_count} candidato(s) na vaga "
                        f"'{row.title}' precisam de feedback. "
                        "Considere avancar estagio, descartar, ou agendar entrevista."
                    ),
                    "action": "navigate_to_vacancy",
                    "action_params": {
                        "vacancy_id": str(row.id),
                        "stale_count": int(row.stale_count),
                    },
                    "severity": self.severity,
                    "expires_in_hours": 24,
                    "related_job_id": str(row.id),
                    "related_candidate_id": None,
                }
            )
        return hints


class WorkforcePlanStaleDetector(BaseDetector):
    """Trigger quando workforce_plan da company tem > 30 dias sem update."""

    name = "workforce_plan_stale"
    severity = "low"

    STALE_DAYS = 30

    async def detect(self, db, company_id):
        try:
            from sqlalchemy import select, text as sa_text

            # Workforce table pode variar de schema por tenant; usamos query
            # defensiva via raw SQL gateado pelo company_id.
            company_uuid = UUID(company_id)
        except (ValueError, Exception):
            return []

        try:
            # ADR-001-EXEMPT: leitura cross-domain workforce_plans. Repo
            # dedicado pendente em follow-up sprint.
            cutoff = datetime.utcnow() - timedelta(days=self.STALE_DAYS)
            result = await db.execute(
                sa_text(
                    "SELECT id, last_updated_at FROM workforce_plans "
                    "WHERE company_id = :company_id "
                    "ORDER BY last_updated_at DESC LIMIT 1"
                ),
                {"company_id": str(company_uuid)},
            )
            row = result.first()
            if row is None:
                return []
            last_updated = row[1]
            if last_updated is None or last_updated >= cutoff:
                return []
        except Exception as exc:
            logger.debug(
                "WorkforcePlanStaleDetector query failed (table may not exist): %s",
                exc,
            )
            return []

        days = (datetime.utcnow() - last_updated).days
        return [
            {
                "title": f"Plano de workforce parado ha {days} dias",
                "message": (
                    "Recomendamos revisar o plano de headcount mensalmente. "
                    "A LIA pode sugerir ajustes com base nas vagas abertas."
                ),
                "action": "navigate_to_workforce",
                "action_params": {"days_stale": days},
                "severity": self.severity,
                "expires_in_hours": 24 * 14,
                "related_job_id": None,
                "related_candidate_id": None,
            }
        ]


class AICreditsLowDetector(BaseDetector):
    """Trigger quando balance de AI credits < 20% do plano contratado."""

    name = "ai_credits_low"
    severity = "high"

    LOW_THRESHOLD = 0.20

    async def detect(self, db, company_id):
        """Detecta company com >=80% do monthly_limit consumido.

        Le `ai_credits_balance` local (tabela Python-owned, vide
        libs/models/lia_models/ai_consumption.py:AiCreditsBalance). Severity
        escala: 80-94% -> medium override, >=95% -> high. Sem row = noop
        (company nao tem plano contratado / nao configurada).
        """
        try:
            from sqlalchemy import select

            from app.models.ai_consumption import AiCreditsBalance
        except Exception as exc:
            logger.warning("AICreditsLowDetector import failed: %s", exc)
            return []

        try:
            company_uuid = UUID(company_id)
        except (ValueError, TypeError, AttributeError):
            return []

        try:
            result = await db.execute(
                select(AiCreditsBalance).where(
                    AiCreditsBalance.company_id == company_uuid
                )
            )
            balance = result.scalar_one_or_none()
        except Exception as exc:
            logger.debug(
                "AICreditsLowDetector query failed (table may not exist): %s",
                exc,
            )
            return []

        if balance is None:
            return []

        monthly_limit = int(getattr(balance, "monthly_limit", 0) or 0)
        current_usage = int(getattr(balance, "current_usage", 0) or 0)
        if monthly_limit <= 0:
            return []

        usage_pct = (current_usage / monthly_limit) * 100
        threshold_pct = (1 - self.LOW_THRESHOLD) * 100  # 80% por default
        if usage_pct < threshold_pct:
            return []

        remaining_pct = max(0.0, 100 - usage_pct)
        # Escalation: >=95% saldo critico -> high; 80-94% -> medium.
        effective_severity = "high" if usage_pct >= 95 else "medium"
        return [
            {
                "title": "AI Credits baixo",
                "message": (
                    f"Saldo de IA em {remaining_pct:.0f}% "
                    f"({current_usage}/{monthly_limit} tokens). "
                    "Considere upgrade do plano antes do saldo zerar."
                ),
                "action": "navigate_to",
                "action_params": {
                    "path": "/configuracoes/ai-credits",
                    "usage_pct": round(usage_pct, 1),
                },
                "severity": effective_severity,
                "expires_in_hours": 12,
                "related_job_id": None,
                "related_candidate_id": None,
            }
        ]


class PipelineStuckDetector(BaseDetector):
    """Trigger quando vagas estao paradas em screening > 14 dias."""

    name = "pipeline_stuck"
    severity = "medium"

    STUCK_DAYS = 14

    async def detect(self, db, company_id):
        try:
            from sqlalchemy import select

            from libs.models.lia_models.job_vacancy import JobVacancy
        except Exception as exc:
            logger.warning("PipelineStuckDetector import failed: %s", exc)
            return []

        try:
            company_uuid = UUID(company_id)
        except ValueError:
            return []

        cutoff = datetime.utcnow() - timedelta(days=self.STUCK_DAYS)

        try:
            result = await db.execute(
                select(JobVacancy).where(
                    JobVacancy.company_id == company_uuid,
                    JobVacancy.status.in_(["screening", "triagem", "in_progress"]),
                    JobVacancy.updated_at <= cutoff,
                ).limit(10)
            )
            stuck = list(result.scalars().all())
        except Exception as exc:
            logger.debug("PipelineStuckDetector query failed: %s", exc)
            return []

        if not stuck:
            return []

        return [
            {
                "title": f"{len(stuck)} vaga(s) parada(s) em triagem ha 14+ dias",
                "message": (
                    "Vagas estagnadas perdem candidatos qualificados. A LIA "
                    "pode sugerir aceleracao ou reabertura de pool."
                ),
                "action": "navigate_to_jobs_filtered",
                "action_params": {
                    "ids": [str(job.id) for job in stuck[:5]],
                    "stage": "triagem",
                },
                "severity": self.severity,
                "expires_in_hours": 24 * 3,
                "related_job_id": str(stuck[0].id) if stuck else None,
                "related_candidate_id": None,
            }
        ]


# ---------------------------------------------------------------------------
# Service orchestrator
# ---------------------------------------------------------------------------


class ProactiveDetectorService:
    """Canonical service. Runs all detectors + writes hints to proactive_actions.

    Singleton via `proactive_detector_service` no fim do modulo.
    """

    def __init__(self) -> None:
        self.detectors: list[BaseDetector] = [
            CompanyProfileCompletionDetector(),
            DSROverdueDetector(),
            CandidateStaleDetector(),
            WorkforcePlanStaleDetector(),
            AICreditsLowDetector(),
            PipelineStuckDetector(),
        ]
        self.logger = logging.getLogger(self.__class__.__name__)

    async def run_for_company(
        self, db: "AsyncSession", company_id: str
    ) -> dict[str, Any]:
        """Roda todos detectors para uma company. Persist + retorna sumario."""
        all_hints: list[dict[str, Any]] = []
        per_detector_count: dict[str, int] = {}

        for detector in self.detectors:
            try:
                hints = await detector.detect(db, company_id)
                for hint in hints:
                    hint["detector"] = detector.name
                    hint["company_id"] = company_id
                all_hints.extend(hints)
                per_detector_count[detector.name] = len(hints)
            except Exception as exc:
                # Defense-in-depth: detector quebrado NAO derruba os outros.
                self.logger.warning(
                    "Detector %s failed for company=%s: %s",
                    detector.name,
                    company_id,
                    exc,
                )
                per_detector_count[detector.name] = -1

        persisted = await self._persist_hints(db, all_hints)

        return {
            "hints_count": len(all_hints),
            "hints_persisted": persisted,
            "detectors_run": len(self.detectors),
            "per_detector": per_detector_count,
        }

    async def _persist_hints(
        self, db: "AsyncSession", hints: list[dict[str, Any]]
    ) -> int:
        """Persist hints in proactive_actions table. Deduplicate by (detector + company)
        enquanto status=PENDING.
        """
        if not hints:
            return 0

        try:
            from sqlalchemy import and_, select

            from libs.models.lia_models.background_jobs import (
                ActionStatus,
                ActionType,
                ProactiveAction,
            )
        except Exception as exc:
            self.logger.error("ProactiveAction model import failed: %s", exc)
            return 0

        persisted = 0
        for hint in hints:
            try:
                company_uuid = UUID(hint["company_id"])
            except (KeyError, ValueError):
                continue

            detector_name = hint.get("detector", "")
            # Deduplicate: existe ja um hint pendente do mesmo detector?
            existing = await db.execute(
                select(ProactiveAction).where(
                    and_(
                        ProactiveAction.company_id == company_uuid,
                        ProactiveAction.trigger_reason == detector_name,
                        ProactiveAction.status == ActionStatus.PENDING.value,
                    )
                ).limit(1)
            )
            if existing.scalars().first() is not None:
                continue  # ja tem hint ativo desse detector

            related_job = hint.get("related_job_id")
            related_candidate = hint.get("related_candidate_id")
            expires_h = hint.get("expires_in_hours")

            action = ProactiveAction(
                id=uuid4(),
                company_id=company_uuid,
                action_type=ActionType.SUGGESTION.value,
                title=str(hint.get("title", ""))[:255],
                description=str(hint.get("message", "")),
                priority=_normalize_priority(hint.get("severity", "medium")),
                suggested_action={
                    "action": hint.get("action"),
                    "action_params": hint.get("action_params") or {},
                    "source": "proactive_detector_scheduler",
                    "detector": detector_name,
                },
                auto_executable=False,
                trigger_reason=detector_name,
                status=ActionStatus.PENDING.value,
                created_at=datetime.utcnow(),
                expires_at=(
                    datetime.utcnow() + timedelta(hours=int(expires_h))
                    if expires_h
                    else None
                ),
            )
            try:
                if related_job:
                    action.related_job_id = UUID(str(related_job))
            except ValueError:
                pass
            try:
                if related_candidate:
                    action.related_candidate_id = UUID(str(related_candidate))
            except ValueError:
                pass

            db.add(action)
            persisted += 1

        # Commit responsabilidade do caller (task / endpoint). Mantemos a
        # transacao aberta para que o caller controle isolation.
        return persisted


# Singleton canonical
proactive_detector_service = ProactiveDetectorService()


__all__ = [
    "BaseDetector",
    "CompanyProfileCompletionDetector",
    "DSROverdueDetector",
    "CandidateStaleDetector",
    "WorkforcePlanStaleDetector",
    "AICreditsLowDetector",
    "PipelineStuckDetector",
    "ProactiveDetectorService",
    "proactive_detector_service",
]
