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

PER-TENANT THRESHOLDS (Wave 2 P0.A1+A2 fix, 2026-05-22):
========================================================
Cada detector le `AlertPreference` (canonical decidido em ADR-WT-2025) por
company_id+alert_type ANTES de calcular threshold. Fallback: usa default
hardcoded MAS loga `logger.info("No tenant template for X, using default")` +
incrementa Prometheus counter
`alert_threshold_source_total{alert_type, source}`.

- AlertPreference.is_enabled=False -> detector skip silencioso.
- AlertPreference.threshold -> overrides class constant (interpretacao
  per-detector documentada em _DETECTOR_ALERT_TYPE_MAP).
- AlertPreference.cooldown_hours -> aplica em _persist_hints dedup
  (sobrepoe expires_in_hours hint-side).
- AlertPreference channels (email/bell/teams/whatsapp) -> passado no
  hint payload para downstream notification dispatcher.

ADR canonical: ~/Documents/wedotalent_audit_2026-05-21/ADR-WT-2025-alert-canonical-table.md
Mapping detector.name -> AlertPreference.alert_type: vide
_DETECTOR_ALERT_TYPE_MAP abaixo.

PATTERN:
- Cada detector implementa BaseDetector.detect(db, company_id, override) -> list[hint]
- Service agrega + escreve em proactive_actions com action_type "suggestion"
- Deduplica: nao insere segundo hint do mesmo detector enquanto o anterior
  esta PENDING para a mesma company (cooldown_hours canonical).

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
from dataclasses import dataclass, field
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
# Per-tenant threshold canonical (ADR-WT-2025)
# ---------------------------------------------------------------------------
# Mapeia detector.name -> AlertPreference.alert_type (canonical table per
# ADR-WT-2025). Quando um detector roda, carregamos AlertPreference por
# (company_id, alert_type) e aplicamos o override. AlertPreference.threshold
# interpretation eh per-detector (vide docstring de cada classe).
#
# Para detector novo: registre aqui + adicione default em _DEFAULT_TENANT_OVERRIDE.

_DETECTOR_ALERT_TYPE_MAP: dict[str, str] = {
    "company_profile_completion": "company_profile_incomplete",
    "dsr_overdue": "dsr_overdue",
    "candidate_stale": "candidate_no_interaction",
    "workforce_plan_stale": "workforce_plan_stale",
    "ai_credits_low": "credits_low",
    "pipeline_stuck": "candidates_stagnant",
}


@dataclass(frozen=True)
class TenantThresholdOverride:
    """Per-tenant override carregado de AlertPreference.

    is_enabled=False sinaliza skip explicito do tenant.
    threshold interpretation: vide docstring do detector.
    cooldown_hours: aplicado em _persist_hints dedup (sobrepoe expires_in_hours).
    channels: passado pro hint payload (downstream dispatcher).
    source: "tenant" quando lido de AlertPreference; "default" quando fallback.
    """

    is_enabled: bool = True
    threshold: int | None = None
    cooldown_hours: int | None = None
    channels: dict[str, bool] = field(default_factory=dict)
    source: str = "default"


# Per-detector default override quando tenant nao tem AlertPreference row.
# Threshold semantica deve bater com classe constant correspondente.
_DEFAULT_TENANT_OVERRIDE: dict[str, TenantThresholdOverride] = {
    "company_profile_completion": TenantThresholdOverride(
        is_enabled=True, threshold=80, cooldown_hours=24 * 7
    ),
    "dsr_overdue": TenantThresholdOverride(
        is_enabled=True, threshold=24, cooldown_hours=12
    ),
    "candidate_stale": TenantThresholdOverride(
        is_enabled=True, threshold=7, cooldown_hours=24
    ),
    "workforce_plan_stale": TenantThresholdOverride(
        is_enabled=True, threshold=30, cooldown_hours=24 * 14
    ),
    "ai_credits_low": TenantThresholdOverride(
        is_enabled=True, threshold=20, cooldown_hours=12
    ),
    "pipeline_stuck": TenantThresholdOverride(
        is_enabled=True, threshold=14, cooldown_hours=24 * 3
    ),
}


def _emit_threshold_source_metric(alert_type: str, source: str) -> None:
    """Best-effort emit Prometheus counter alert_threshold_source_total.

    Counter label set: {alert_type, source=tenant|default}.
    NUNCA quebra detector se prometheus_client nao esta disponivel.
    """
    try:
        from prometheus_client import Counter

        # Module-level cache (idempotent registration).
        global _ALERT_THRESHOLD_SOURCE_COUNTER  # noqa: PLW0603
        if "_ALERT_THRESHOLD_SOURCE_COUNTER" not in globals():
            _ALERT_THRESHOLD_SOURCE_COUNTER = Counter(  # type: ignore[name-defined]
                "alert_threshold_source_total",
                "Source of alert threshold per detector run (tenant vs default)",
                labelnames=["alert_type", "source"],
            )
        _ALERT_THRESHOLD_SOURCE_COUNTER.labels(  # type: ignore[name-defined]
            alert_type=alert_type, source=source
        ).inc()
    except Exception as exc:  # noqa: BLE001
        logger.debug(
            "Prometheus counter emit failed (best-effort): %s", exc
        )


# ---------------------------------------------------------------------------
# Base detector contract
# ---------------------------------------------------------------------------


class BaseDetector(ABC):
    """Base class para todos os proactive detectors.

    Cada subclass DEVE definir:
    - name: identificador estavel (usado para deduplicar hints + AST sensor)
    - severity: low | medium | high | critical
    - detect(db, company_id, override=None) -> list[dict]

    `override`: TenantThresholdOverride canonical lido pelo orchestrator de
    AlertPreference. Quando None (compat retro), subclass deve usar
    _DEFAULT_TENANT_OVERRIDE[self.name] como fallback.
    """

    name: str = ""
    severity: str = "medium"

    @abstractmethod
    async def detect(
        self,
        db: "AsyncSession",
        company_id: str,
        override: TenantThresholdOverride | None = None,
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
            "channels": dict | None,      # canais escolhidos pelo tenant
        }
        """
        ...

    def _resolve_override(
        self,
        override: TenantThresholdOverride | None,
    ) -> TenantThresholdOverride:
        """Helper canonical: aplica fallback + emit metric source.

        Quando override is None ou source='default': loga + incrementa metric
        com source='default'. Quando override.source='tenant': metric com
        source='tenant'. Retorna SEMPRE TenantThresholdOverride (nunca None).
        """
        alert_type = _DETECTOR_ALERT_TYPE_MAP.get(self.name, self.name)
        if override is None or override.source == "default":
            logger.info(
                "No tenant template for %s, using default", self.name
            )
            _emit_threshold_source_metric(alert_type, "default")
            return _DEFAULT_TENANT_OVERRIDE.get(
                self.name, TenantThresholdOverride()
            )
        _emit_threshold_source_metric(alert_type, "tenant")
        return override


# ---------------------------------------------------------------------------
# Detector implementations
# ---------------------------------------------------------------------------


class CompanyProfileCompletionDetector(BaseDetector):
    """Trigger quando profile da empresa esta < threshold% completo.

    Per-tenant override (AlertPreference.alert_type='company_profile_incomplete'):
    - threshold: percentage minimo (default 80)
    - cooldown_hours: dedup gate (default 24*7=168)
    """

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

    async def detect(self, db, company_id, override=None):
        cfg = self._resolve_override(override)
        if not cfg.is_enabled:
            return []

        try:
            from sqlalchemy import select

            from lia_models.company import CompanyProfile
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
        threshold_pct = cfg.threshold if cfg.threshold is not None else 80

        if percentage >= threshold_pct:
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
                "expires_in_hours": cfg.cooldown_hours or 24 * 7,
                "related_job_id": None,
                "related_candidate_id": None,
                "channels": cfg.channels or {},
            }
        ]


class DSROverdueDetector(BaseDetector):
    """Trigger quando DSR (LGPD Art.18) chegando perto do SLA legal (15 dias).

    Per-tenant override (AlertPreference.alert_type='dsr_overdue'):
    - threshold: margem de aviso em horas antes do deadline (default 24)
    - cooldown_hours: dedup gate (default 12)
    """

    name = "dsr_overdue"
    severity = "high"

    # Default margem de aviso: alertar quando faltam < 24h para deadline.
    # Pode ser sobrescrito por AlertPreference.threshold.
    WARN_MARGIN_HOURS = 24

    async def detect(self, db, company_id, override=None):
        cfg = self._resolve_override(override)
        if not cfg.is_enabled:
            return []

        try:
            from sqlalchemy import and_, or_, select

            from lia_models.observability import (
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
        warn_hours = (
            cfg.threshold if cfg.threshold is not None else self.WARN_MARGIN_HOURS
        )
        cutoff = now + timedelta(hours=warn_hours)
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
                    else f"{len(overdue)} DSR(s) vencendo em {warn_hours}h"
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
                "expires_in_hours": cfg.cooldown_hours or 12,
                "related_job_id": None,
                "related_candidate_id": None,
                "channels": cfg.channels or {},
            }
        ]


class CandidateStaleDetector(BaseDetector):
    """Trigger quando candidato esta N+ dias sem feedback / mudanca de estagio.

    Per-tenant override (AlertPreference.alert_type='candidate_no_interaction'):
    - threshold: dias sem update para considerar stale (default 7)
    - cooldown_hours: dedup gate (default 24)
    """

    name = "candidate_stale"
    severity = "medium"

    STALE_DAYS = 7
    BATCH_SIZE = 50

    async def detect(self, db, company_id, override=None):
        """Detecta candidatos em estagios interview/screening sem update >= N dias.

        Query canonical: JOIN VacancyCandidate x JobVacancy filtrando por
        company_id (multi-tenancy fail-closed) + status canonical pos-triagem
        + updated_at < cutoff. Agrupa por vaga para gerar 1 hint por vaga
        (evita flood na bell quando ha varias vagas com candidatos parados).
        """
        cfg = self._resolve_override(override)
        if not cfg.is_enabled:
            return []

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

        stale_days = cfg.threshold if cfg.threshold is not None else self.STALE_DAYS
        cutoff = datetime.utcnow() - timedelta(days=stale_days)
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
                    "title": f"Candidatos sem feedback ha {stale_days}+ dias",
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
                    "expires_in_hours": cfg.cooldown_hours or 24,
                    "related_job_id": str(row.id),
                    "related_candidate_id": None,
                    "channels": cfg.channels or {},
                }
            )
        return hints


class WorkforcePlanStaleDetector(BaseDetector):
    """Trigger quando workforce_plan da company tem > N dias sem update.

    Per-tenant override (AlertPreference.alert_type='workforce_plan_stale'):
    - threshold: dias sem update para considerar stale (default 30)
    - cooldown_hours: dedup gate (default 24*14=336)
    """

    name = "workforce_plan_stale"
    severity = "low"

    STALE_DAYS = 30

    async def detect(self, db, company_id, override=None):
        cfg = self._resolve_override(override)
        if not cfg.is_enabled:
            return []

        try:
            from sqlalchemy import text as sa_text

            # Workforce table pode variar de schema por tenant; usamos query
            # defensiva via raw SQL gateado pelo company_id.
            company_uuid = UUID(company_id)
        except (ValueError, Exception):
            return []

        stale_days = cfg.threshold if cfg.threshold is not None else self.STALE_DAYS

        try:
            # ADR-001-EXEMPT: leitura cross-domain workforce_plans. Repo
            # dedicado pendente em follow-up sprint.
            cutoff = datetime.utcnow() - timedelta(days=stale_days)
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
                "expires_in_hours": cfg.cooldown_hours or 24 * 14,
                "related_job_id": None,
                "related_candidate_id": None,
                "channels": cfg.channels or {},
            }
        ]


class AICreditsLowDetector(BaseDetector):
    """Trigger quando balance de AI credits < N% do plano contratado.

    Per-tenant override (AlertPreference.alert_type='credits_low'):
    - threshold: pct remaining minimo para nao alertar (default 20 = alerta
      quando saldo < 20%)
    - cooldown_hours: dedup gate (default 12)
    """

    name = "ai_credits_low"
    severity = "high"

    LOW_THRESHOLD = 0.20

    async def detect(self, db, company_id, override=None):
        """Detecta company com >=(100-threshold)% do monthly_limit consumido.

        Le `ai_credits_balance` local (tabela Python-owned, vide
        libs/models/lia_models/ai_consumption.py:AiCreditsBalance). Severity
        escala: 80-94% -> medium override, >=95% -> high. Sem row = noop
        (company nao tem plano contratado / nao configurada).
        """
        cfg = self._resolve_override(override)
        if not cfg.is_enabled:
            return []

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
        # threshold=20 (default) -> alerta quando remaining < 20% (usage >= 80%).
        low_threshold_pct = (
            cfg.threshold if cfg.threshold is not None else 20
        )
        alert_at_usage_pct = 100 - low_threshold_pct
        if usage_pct < alert_at_usage_pct:
            return []

        remaining_pct = max(0.0, 100 - usage_pct)
        # Escalation: >=95% saldo critico -> high; >=alert_at -> medium.
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
                "expires_in_hours": cfg.cooldown_hours or 12,
                "related_job_id": None,
                "related_candidate_id": None,
                "channels": cfg.channels or {},
            }
        ]


class PipelineStuckDetector(BaseDetector):
    """Trigger quando vagas estao paradas em screening > N dias.

    Per-tenant override (AlertPreference.alert_type='candidates_stagnant'):
    - threshold: dias parados para considerar stuck (default 14)
    - cooldown_hours: dedup gate (default 24*3=72)
    """

    name = "pipeline_stuck"
    severity = "medium"

    STUCK_DAYS = 14

    async def detect(self, db, company_id, override=None):
        cfg = self._resolve_override(override)
        if not cfg.is_enabled:
            return []

        try:
            from sqlalchemy import select

            from lia_models.job_vacancy import JobVacancy
        except Exception as exc:
            logger.warning("PipelineStuckDetector import failed: %s", exc)
            return []

        try:
            company_uuid = UUID(company_id)
        except ValueError:
            return []

        stuck_days = cfg.threshold if cfg.threshold is not None else self.STUCK_DAYS
        cutoff = datetime.utcnow() - timedelta(days=stuck_days)

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
                "title": f"{len(stuck)} vaga(s) parada(s) em triagem ha {stuck_days}+ dias",
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
                "expires_in_hours": cfg.cooldown_hours or 24 * 3,
                "related_job_id": str(stuck[0].id) if stuck else None,
                "related_candidate_id": None,
                "channels": cfg.channels or {},
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

    async def _load_tenant_overrides(
        self, db: "AsyncSession", company_id: str
    ) -> dict[str, TenantThresholdOverride]:
        """Carrega AlertPreference rows do tenant + monta dict por detector.name.

        Canonical table: AlertPreference (ADR-WT-2025). Quando o tenant nao
        tem row para um alert_type, NAO entra no dict (orchestrator vai cair
        em _resolve_override default + log).

        Multi-tenancy: query filtra por company_id explicitamente.
        ADR-001-EXEMPT: leitura cross-user (todos os AlertPreference da
        company, agregado por alert_type usando o mais recente). Repo
        dedicado pendente em follow-up.
        """
        overrides: dict[str, TenantThresholdOverride] = {}
        if not company_id:
            return overrides

        try:
            from sqlalchemy import select

            from app.models.alert import AlertPreference
        except Exception as exc:
            self.logger.warning(
                "AlertPreference import failed (using all defaults): %s", exc
            )
            return overrides

        try:
            result = await db.execute(
                select(AlertPreference).where(
                    AlertPreference.company_id == company_id,
                )
            )
            rows = list(result.scalars().all())
        except Exception as exc:
            # Table may not exist yet em alguns ambientes; fall back para defaults.
            self.logger.debug(
                "AlertPreference query failed for company=%s: %s",
                company_id,
                exc,
            )
            return overrides

        # Inverte _DETECTOR_ALERT_TYPE_MAP: alert_type -> detector.name.
        # Multiplos users podem ter preferences para o mesmo alert_type; pegamos
        # a mais recente (assumindo que admin/team config eh single source).
        alert_type_to_detector = {
            v: k for k, v in _DETECTOR_ALERT_TYPE_MAP.items()
        }

        # Agrega: por alert_type, pega a row com updated_at mais recente.
        latest_by_type: dict[str, Any] = {}
        for row in rows:
            atype = str(getattr(row, "alert_type", ""))
            if atype not in alert_type_to_detector:
                continue  # alert_type que nao mapeia pra detector conhecido
            existing = latest_by_type.get(atype)
            if (
                existing is None
                or getattr(row, "updated_at", None)
                and getattr(row, "updated_at") > getattr(existing, "updated_at", datetime.min)
            ):
                latest_by_type[atype] = row

        for atype, row in latest_by_type.items():
            detector_name = alert_type_to_detector[atype]
            channels = {
                "email": bool(getattr(row, "channel_email", False)),
                "bell": bool(getattr(row, "channel_bell", False)),
                "teams": bool(getattr(row, "channel_teams", False)),
                "whatsapp": bool(getattr(row, "channel_whatsapp", False)),
            }
            overrides[detector_name] = TenantThresholdOverride(
                is_enabled=bool(getattr(row, "is_enabled", True)),
                threshold=(
                    int(getattr(row, "threshold"))
                    if getattr(row, "threshold", None) is not None
                    else None
                ),
                cooldown_hours=(
                    int(getattr(row, "cooldown_hours"))
                    if getattr(row, "cooldown_hours", None) is not None
                    else None
                ),
                channels=channels,
                source="tenant",
            )
        return overrides

    async def run_for_company(
        self, db: "AsyncSession", company_id: str
    ) -> dict[str, Any]:
        """Roda todos detectors para uma company. Persist + retorna sumario.

        Per-tenant thresholds: chama _load_tenant_overrides antes de rodar e
        passa override apropriado a cada detector. Fail-closed se load
        levantar exception: detectors caem em default (com log).
        """
        all_hints: list[dict[str, Any]] = []
        per_detector_count: dict[str, int] = {}

        try:
            tenant_overrides = await self._load_tenant_overrides(db, company_id)
        except Exception as exc:
            self.logger.warning(
                "Failed to load tenant overrides for company=%s, "
                "falling back to defaults: %s",
                company_id,
                exc,
            )
            tenant_overrides = {}

        # WT-2022 Wave 2 P0.ALR-1+2 (2026-05-22): wire de
        # communication_settings.alerts[].enabled — antes esses 5 toggles UI
        # gravavam no DB mas o detector NAO consultava (ghost setting).
        try:
            from app.shared.services.communication_settings_consumer import (
                get_company_communication_settings,
                is_alert_enabled,
                get_alert_channel,
                inc_communication_skip,
            )
            comm_settings = await get_company_communication_settings(db, company_id)
        except Exception as exc:
            self.logger.warning(
                "ProactiveDetector: failed to load tenant comm_settings for %s, "
                "all detectors run with default-enabled (fail-safe): %s",
                company_id, exc,
            )
            comm_settings = {}

            def is_alert_enabled(_s, _id):  # type: ignore[no-redef]
                return True

            def get_alert_channel(_s, _id, default="email"):  # type: ignore[no-redef]
                return default

            def inc_communication_skip(_r):  # type: ignore[no-redef]
                return None

        for detector in self.detectors:
            # WT-2022 Wave 2 P0.ALR-1: gate per tenant — toggle off pula detector.
            if not is_alert_enabled(comm_settings, detector.name):
                self.logger.info(
                    "Detector %s disabled by tenant settings company=%s — skipping",
                    detector.name, company_id,
                )
                inc_communication_skip("alert_disabled")
                per_detector_count[detector.name] = -2  # skip sentinel (vs -1 error)
                continue

            # G9 fix (2026-06-04): a deteccao e read-only. Um detector anterior
            # (ou o load de overrides/comm_settings) pode ter batido numa query
            # que falhou e foi engolida, deixando a transacao asyncpg abortada
            # (InFailedSQLTransactionError). Rollback aqui limpa esse estado SEM
            # descartar nada que importe (nenhum write aconteceu ainda) e impede
            # a falha de cascatear para este detector e para o persist abaixo.
            try:
                await db.rollback()
            except Exception:
                pass

            try:
                override = tenant_overrides.get(detector.name)
                hints = await detector.detect(db, company_id, override=override)
                for hint in hints:
                    hint["detector"] = detector.name
                    hint["company_id"] = company_id
                    # WT-2022 Wave 2 P0.ALR-2: anexa channel preferido tenant.
                    hint["channel"] = get_alert_channel(comm_settings, detector.name)
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

        # Transacao limpa para a fase de escrita, independente do ultimo detector
        # (ver comentario G9 acima). Sem isto, o SELECT de dedup do persist morria
        # com InFailedSQLTransactionError — a causa real da lampada sempre vazia.
        try:
            await db.rollback()
        except Exception:
            pass

        persisted = await self._persist_hints(db, all_hints)

        return {
            "hints_count": len(all_hints),
            "hints_persisted": persisted,
            "detectors_run": len(self.detectors),
            "per_detector": per_detector_count,
            "tenant_overrides_loaded": len(tenant_overrides),
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

            from lia_models.background_jobs import (
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

            # WT-2022: WebSocket broadcast canonical (best-effort).
            # Polling 60s no hook frontend continua sendo fallback —
            # falha aqui NUNCA quebra o persist.
            try:
                from app.api.websockets.proactive_hints_ws import proactive_pool

                hint_company_id = hint.get("company_id")
                if hint_company_id:
                    await proactive_pool.broadcast_to_company(
                        str(hint_company_id), hint
                    )
            except Exception as exc:
                self.logger.debug(
                    "ProactiveWS broadcast failed (polling fallback active): %s",
                    exc,
                )

        # G9 fix (2026-06-04): commit aqui (fail-loud). Antes o contrato era
        # "caller commits" — mas o piggyback do MonitoringLoop roda numa sessao
        # fresca e saia do `async with` SEM commit, descartando os INSERTs. O
        # celery batch (proactive.detect_hints_hourly) ainda commita no fim; com
        # persist commitando por company, aquele commit vira no-op idempotente
        # e cada company fica duravel antes do proximo run.
        try:
            await db.commit()
        except Exception as exc:
            self.logger.error(
                "ProactiveDetector persist commit failed (%d hints lost): %s",
                persisted,
                exc,
            )
            await db.rollback()
            raise
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
    "TenantThresholdOverride",
    "proactive_detector_service",
    "_DETECTOR_ALERT_TYPE_MAP",
    "_DEFAULT_TENANT_OVERRIDE",
]
