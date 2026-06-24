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
- CandidateStaleDetector          - 5+ dias sem feedback no candidato
- WorkforcePlanStaleDetector      - last_updated > 30 dias atras
- AICreditsLowDetector            - balance < 20% (+ forecast de esgotamento)
- PipelineStuckDetector           - vagas em screening > 10 dias
- ConversionRateLowDetector       - taxa contratados/total abaixo do threshold
- SlaNearExpirationDetector       - >= threshold% do SLA (RecruitmentStage.sla_hours)
- InterviewNotConfirmedDetector   - entrevista proxima com confirmation pending
- FeedbackPendingDetector         - entrevista realizada sem feedback
- OffersPendingLongDetector       - proposta enviada sem resposta ha N horas
- TasksOverdueDetector            - N+ tarefas pendentes alem do prazo
- EmailDeliveryLowDetector        - taxa de entrega de email < threshold (MessageQueue)
- IdealCandidateFoundDetector     - candidato com match >= threshold recente
- AtsSyncFailedDetector           - N+ jobs de sync ATS FAILED recentes

Task #1296 fechou as 9 regras orfas do catalogo (matriz 15/15 em
docs/runbooks/alert-config-single-source.md).

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

# Fonte-única-da-verdade de defaults + helper de canais (Task #1295). Tanto os
# defaults do detector quanto o MonitoringLoop derivam deste registro, que
# espelha 1-1 o catálogo da UI (DEFAULT_ALERT_PREFERENCES).
from app.shared.services.alert_config_resolver import (  # noqa: E402
    ALERT_CONFIG_DEFAULTS,
    channels_to_list,
)


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
    # Task #1296 — 9 regras órfãs do catálogo ganharam detector canônico.
    "conversion_rate_low": "conversion_rate_low",
    "sla_near_expiration": "sla_near_expiration",
    "interview_not_confirmed": "interview_not_confirmed",
    "feedback_pending": "feedback_pending",
    "offers_pending_long": "offers_pending_long",
    "tasks_overdue": "tasks_overdue",
    "email_delivery_low": "email_delivery_low",
    "ideal_candidate_found": "ideal_candidate_found",
    "ats_sync_failed": "ats_sync_failed",
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
#
# Task #1295: derivado da fonte-única-da-verdade ALERT_CONFIG_DEFAULTS (que
# espelha o catálogo da UI) via _DETECTOR_ALERT_TYPE_MAP. Antes os valores eram
# literais e divergiam da UI (candidate_stale=7 vs 5, pipeline_stuck=14 vs 10).
# O sentinel test_alert_config_single_source trava qualquer drift futuro.
def _build_default_tenant_overrides() -> dict[str, TenantThresholdOverride]:
    out: dict[str, TenantThresholdOverride] = {}
    for detector_name, alert_type in _DETECTOR_ALERT_TYPE_MAP.items():
        d = ALERT_CONFIG_DEFAULTS.get(alert_type)
        if d is None:
            out[detector_name] = TenantThresholdOverride()
            continue
        out[detector_name] = TenantThresholdOverride(
            is_enabled=d.is_enabled,
            threshold=d.threshold,
            cooldown_hours=d.cooldown_hours,
            channels=dict(d.channels),
            source="default",
        )
    return out


_DEFAULT_TENANT_OVERRIDE: dict[str, TenantThresholdOverride] = (
    _build_default_tenant_overrides()
)


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
    - threshold: dias sem update para considerar stale (default 5, espelha UI)
    - cooldown_hours: dedup gate (default 24)
    """

    name = "candidate_stale"
    severity = "medium"

    STALE_DAYS = 5
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

        # AiCreditsBalance.company_id é String(64) (Python-owned table) — filtrar
        # como string canônica. Converter p/ UUID quebrava o operador varchar=uuid
        # no Postgres, caía no except e o detector NUNCA disparava (matava também
        # o forecast preditivo). Ver libs/models/lia_models/ai_consumption.py.
        if not isinstance(company_id, str) or not company_id:
            return []

        try:
            result = await db.execute(
                select(AiCreditsBalance).where(
                    AiCreditsBalance.company_id == company_id
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

        # Vinculacao preditiva (Task #1296): projeta a data de esgotamento a
        # partir do consumo historico (AiConsumption). Fail-defensive: sem
        # historico suficiente, o hint segue SEM forecast (nunca inventa data).
        forecast = await self._forecast_exhaustion(
            db, company_id, monthly_limit, current_usage
        )
        forecast_msg = ""
        action_params: dict[str, Any] = {
            "path": "/configuracoes/ai-credits",
            "usage_pct": round(usage_pct, 1),
        }
        if forecast:
            action_params["projected_exhaustion_date"] = forecast[
                "projected_exhaustion_date"
            ]
            action_params["days_left"] = forecast["days_left"]
            forecast_msg = (
                f" No ritmo atual, o saldo deve zerar em "
                f"~{forecast['days_left']:.0f} dia(s) "
                f"({forecast['projected_exhaustion_date']})."
            )

        return [
            {
                "title": "AI Credits baixo",
                "message": (
                    f"Saldo de IA em {remaining_pct:.0f}% "
                    f"({current_usage}/{monthly_limit} tokens). "
                    "Considere upgrade do plano antes do saldo zerar."
                    + forecast_msg
                ),
                "action": "navigate_to",
                "action_params": action_params,
                "severity": effective_severity,
                "expires_in_hours": cfg.cooldown_hours or 12,
                "related_job_id": None,
                "related_candidate_id": None,
                "channels": cfg.channels or {},
            }
        ]

    async def _forecast_exhaustion(
        self, db, company_id, monthly_limit, current_usage
    ):
        """Projeta a data de esgotamento do saldo a partir do consumo historico.

        Le AiConsumption.total_tokens dos ultimos FORECAST_WINDOW_DAYS, calcula
        o burn rate diario medio e projeta quantos dias ate current_usage
        atingir monthly_limit. Fail-defensive: retorna None se nao houver
        historico (canonical-fix: NUNCA inventa uma data de esgotamento).
        """
        forecast_window_days = 14
        try:
            from sqlalchemy import func, select

            from app.models.ai_consumption import AiConsumption
        except Exception as exc:
            logger.debug("AICredits forecast import failed: %s", exc)
            return None

        cutoff = datetime.utcnow() - timedelta(days=forecast_window_days)
        try:
            consumed = await db.scalar(
                select(
                    func.coalesce(func.sum(AiConsumption.total_tokens), 0)
                ).where(
                    AiConsumption.company_id == company_id,
                    AiConsumption.created_at >= cutoff,
                )
            )
        except Exception as exc:
            logger.debug("AICredits forecast query failed: %s", exc)
            return None

        consumed = int(consumed or 0)
        if consumed <= 0:
            return None
        daily_burn = consumed / forecast_window_days
        if daily_burn <= 0:
            return None

        remaining = max(0, int(monthly_limit) - int(current_usage))
        days_left = remaining / daily_burn
        exhaustion = datetime.utcnow() + timedelta(days=days_left)
        return {
            "days_left": round(days_left, 1),
            "projected_exhaustion_date": exhaustion.date().isoformat(),
            "daily_burn_tokens": int(daily_burn),
        }


class PipelineStuckDetector(BaseDetector):
    """Trigger quando vagas estao paradas em screening > N dias.

    Per-tenant override (AlertPreference.alert_type='candidates_stagnant'):
    - threshold: dias parados para considerar stuck (default 10, espelha UI)
    - cooldown_hours: dedup gate (default 24*3=72)
    """

    name = "pipeline_stuck"
    severity = "medium"

    STUCK_DAYS = 10

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

        # JobVacancy.company_id é String(255) (Python-owned table) — filtrar como
        # string canônica. Converter p/ UUID quebrava o operador varchar=uuid no
        # Postgres, caía no except e o detector NUNCA disparava (mesmo bug do
        # AICreditsLowDetector, Task #1296/#1302). Ver lia_models/job_vacancy.py.
        if not isinstance(company_id, str) or not company_id:
            return []

        stuck_days = cfg.threshold if cfg.threshold is not None else self.STUCK_DAYS
        cutoff = datetime.utcnow() - timedelta(days=stuck_days)

        try:
            result = await db.execute(
                select(JobVacancy).where(
                    JobVacancy.company_id == company_id,
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


class ConversionRateLowDetector(BaseDetector):
    """Trigger quando a taxa de conversao do funil cai abaixo do threshold (%).

    Per-tenant override (AlertPreference.alert_type='conversion_rate_low'):
    - threshold: taxa minima de conversao (%) aceitavel (default 2). Conversao =
      contratados / total de candidatos adicionados na janela.
    - cooldown_hours: dedup gate (default 48).

    Janela: candidatos com created_at nos ultimos WINDOW_DAYS. Exige amostra
    minima (MIN_SAMPLE) para evitar ruido em funil pequeno (sem fake alert).
    """

    name = "conversion_rate_low"
    severity = "medium"

    WINDOW_DAYS = 90
    MIN_SAMPLE = 20

    async def detect(self, db, company_id, override=None):
        cfg = self._resolve_override(override)
        if not cfg.is_enabled:
            return []
        if not company_id:
            return []

        try:
            from sqlalchemy import func, select

            from lia_models.candidate import VacancyCandidate
        except Exception as exc:
            logger.warning("ConversionRateLowDetector import failed: %s", exc)
            return []

        cutoff = datetime.utcnow() - timedelta(days=self.WINDOW_DAYS)
        try:
            total = await db.scalar(
                select(func.count(VacancyCandidate.id)).where(
                    VacancyCandidate.company_id == company_id,
                    VacancyCandidate.created_at >= cutoff,
                )
            )
            hired = await db.scalar(
                select(func.count(VacancyCandidate.id)).where(
                    VacancyCandidate.company_id == company_id,
                    VacancyCandidate.created_at >= cutoff,
                    VacancyCandidate.status == "hired",
                )
            )
        except Exception as exc:
            logger.debug("ConversionRateLowDetector query failed: %s", exc)
            return []

        total = int(total or 0)
        hired = int(hired or 0)
        if total < self.MIN_SAMPLE:
            return []

        rate = (hired / total) * 100
        threshold = cfg.threshold if cfg.threshold is not None else 2
        if rate >= threshold:
            return []

        return [
            {
                "title": f"Taxa de conversao baixa ({rate:.1f}%)",
                "message": (
                    f"Apenas {hired} de {total} candidatos dos ultimos "
                    f"{self.WINDOW_DAYS} dias foram contratados "
                    f"({rate:.1f}%, abaixo de {threshold}%). A LIA pode revisar "
                    "gargalos do funil e sugerir ajustes de triagem."
                ),
                "action": "navigate_to_candidates",
                "action_params": {
                    "conversion_rate": round(rate, 1),
                    "window_days": self.WINDOW_DAYS,
                    "hired": hired,
                    "total": total,
                },
                "severity": self.severity,
                "expires_in_hours": cfg.cooldown_hours or 48,
                "related_job_id": None,
                "related_candidate_id": None,
                "channels": cfg.channels or {},
            }
        ]


class SlaNearExpirationDetector(BaseDetector):
    """Trigger quando candidatos atingem >= threshold% do SLA na etapa atual.

    Vinculacao preditiva (Task #1296): o SLA vem de RecruitmentStage.sla_hours
    (config real por etapa/tenant), NAO de constante hardcoded. Para cada
    VacancyCandidate ativo, calcula elapsed = now - stage_entered_at e compara
    com o sla_hours da etapa. Conta quem esta entre threshold% e 100% (perto de
    estourar, ainda dentro do prazo).

    Vinculacao robusta por id (Task #1303): a etapa do candidato e resolvida por
    VacancyCandidate.recruitment_stage_id (join estavel por identificador) quando
    presente; o match por NOME so e usado como fallback para registros legados
    sem o vinculo. Isso evita que divergencias de nomenclatura (acentuacao,
    maiusculas, renomeacao) silenciosamente desliguem o alerta.

    Per-tenant override (AlertPreference.alert_type='sla_near_expiration'):
    - threshold: % do SLA decorrido para alertar (default 80).
    - cooldown_hours: dedup gate (default 12).
    """

    name = "sla_near_expiration"
    severity = "high"

    TERMINAL_STATUSES = ("hired", "rejected", "not_selected", "cancelled")
    MAX_CANDIDATES = 500

    async def detect(self, db, company_id, override=None):
        cfg = self._resolve_override(override)
        if not cfg.is_enabled:
            return []
        if not company_id:
            return []

        try:
            from sqlalchemy import select

            from lia_models.candidate import VacancyCandidate
            from lia_models.recruitment_stages import RecruitmentStage
        except Exception as exc:
            logger.warning("SlaNearExpirationDetector import failed: %s", exc)
            return []

        threshold = cfg.threshold if cfg.threshold is not None else 80
        try:
            stage_rows = await db.execute(
                select(
                    RecruitmentStage.id,
                    RecruitmentStage.name,
                    RecruitmentStage.sla_hours,
                ).where(
                    RecruitmentStage.company_id == company_id,
                    RecruitmentStage.sla_hours.isnot(None),
                )
            )
            # Task #1303: index the SLA both by stage id (robust, preferred) and
            # by name (legacy fallback for rows without recruitment_stage_id).
            sla_by_stage_id: dict[str, int] = {}
            sla_by_stage: dict[str, int] = {}
            for stage_id, name, sla in stage_rows.all():
                if not sla or int(sla) <= 0:
                    continue
                hours = int(sla)
                if stage_id is not None:
                    sla_by_stage_id[str(stage_id)] = hours
                if name:
                    sla_by_stage[name] = hours
        except Exception as exc:
            logger.debug("SlaNearExpirationDetector stage query failed: %s", exc)
            return []

        if not sla_by_stage_id and not sla_by_stage:
            # Tenant nao configurou SLA por etapa: nada a checar (sem fake).
            return []

        try:
            cand_rows = await db.execute(
                select(VacancyCandidate)
                .where(
                    VacancyCandidate.company_id == company_id,
                    VacancyCandidate.stage_entered_at.isnot(None),
                    ~VacancyCandidate.status.in_(self.TERMINAL_STATUSES),
                )
                .limit(self.MAX_CANDIDATES)
            )
            candidates = list(cand_rows.scalars().all())
        except Exception as exc:
            logger.debug(
                "SlaNearExpirationDetector candidate query failed: %s", exc
            )
            return []

        now = datetime.utcnow()
        near = []
        for cand in candidates:
            # Prefer the structural stage link (Task #1303); fall back to the
            # textual stage name only for legacy rows without the id binding.
            sla_hours = None
            stage_id = getattr(cand, "recruitment_stage_id", None)
            if stage_id is not None:
                sla_hours = sla_by_stage_id.get(str(stage_id))
            if not sla_hours:
                sla_hours = sla_by_stage.get(getattr(cand, "stage", None))
            if not sla_hours:
                continue
            entered = getattr(cand, "stage_entered_at", None)
            if entered is None:
                continue
            elapsed_h = (now - entered).total_seconds() / 3600
            pct = (elapsed_h / sla_hours) * 100
            if threshold <= pct < 100:
                near.append(cand)

        if not near:
            return []

        return [
            {
                "title": f"{len(near)} candidato(s) perto do limite de SLA",
                "message": (
                    f"{len(near)} candidato(s) ja consumiram {threshold}%+ do "
                    "prazo (SLA) na etapa atual. Aja antes do vencimento para "
                    "nao perder talentos qualificados."
                ),
                "action": "navigate_to_candidates_filtered",
                "action_params": {
                    "ids": [str(c.candidate_id) for c in near[:5]],
                    "reason": "sla_near_expiration",
                },
                "severity": self.severity,
                "expires_in_hours": cfg.cooldown_hours or 12,
                "related_job_id": None,
                "related_candidate_id": (
                    str(near[0].candidate_id) if near else None
                ),
                "channels": cfg.channels or {},
            }
        ]


class InterviewNotConfirmedDetector(BaseDetector):
    """Trigger para entrevistas proximas sem confirmacao do candidato.

    Per-tenant override (AlertPreference.alert_type='interview_not_confirmed'):
    - threshold: janela (horas) antes do start_time para lembrar (default 24).
    - cooldown_hours: dedup gate (default 12).

    Considera Interview.confirmation_status=='pending', status ativo, e
    start_time entre agora e agora+threshold horas.
    """

    name = "interview_not_confirmed"
    severity = "high"

    INACTIVE_STATUSES = ("cancelled", "completed", "no_show")

    async def detect(self, db, company_id, override=None):
        cfg = self._resolve_override(override)
        if not cfg.is_enabled:
            return []
        if not company_id:
            return []

        try:
            from sqlalchemy import select

            from lia_models.interview import Interview
        except Exception as exc:
            logger.warning("InterviewNotConfirmedDetector import failed: %s", exc)
            return []

        threshold = cfg.threshold if cfg.threshold is not None else 24
        now = datetime.utcnow()
        window_end = now + timedelta(hours=threshold)
        try:
            rows = await db.execute(
                select(Interview)
                .where(
                    Interview.company_id == company_id,
                    Interview.confirmation_status == "pending",
                    ~Interview.status.in_(self.INACTIVE_STATUSES),
                    Interview.start_time >= now,
                    Interview.start_time <= window_end,
                )
                .limit(50)
            )
            pending = list(rows.scalars().all())
        except Exception as exc:
            logger.debug("InterviewNotConfirmedDetector query failed: %s", exc)
            return []

        if not pending:
            return []

        first = pending[0]
        return [
            {
                "title": f"{len(pending)} entrevista(s) sem confirmacao",
                "message": (
                    f"{len(pending)} entrevista(s) nas proximas {threshold}h ainda "
                    "nao foram confirmadas pelo candidato. Reforce o lembrete "
                    "para evitar no-show."
                ),
                "action": "navigate_to_interviews",
                "action_params": {
                    "ids": [str(i.id) for i in pending[:5]],
                    "reason": "not_confirmed",
                },
                "severity": self.severity,
                "expires_in_hours": cfg.cooldown_hours or 12,
                "related_job_id": (
                    str(first.job_vacancy_id)
                    if getattr(first, "job_vacancy_id", None)
                    else None
                ),
                "related_candidate_id": (
                    str(first.candidate_id)
                    if getattr(first, "candidate_id", None)
                    else None
                ),
                "channels": cfg.channels or {},
            }
        ]


class FeedbackPendingDetector(BaseDetector):
    """Trigger para entrevistas realizadas ha threshold+ horas sem feedback.

    Per-tenant override (AlertPreference.alert_type='feedback_pending'):
    - threshold: horas apos a entrevista para cobrar feedback (default 48).
    - cooldown_hours: dedup gate (default 24).

    Default is_enabled=False (espelha a UI). Detecta Interview com end_time <
    now-threshold, status nao cancelado, SEM InterviewFeedback e com feedback
    JSON vazio.
    """

    name = "feedback_pending"
    severity = "medium"

    MAX_INTERVIEWS = 200

    async def detect(self, db, company_id, override=None):
        cfg = self._resolve_override(override)
        if not cfg.is_enabled:
            return []
        if not company_id:
            return []

        try:
            from sqlalchemy import select

            from lia_models.interview import Interview, InterviewFeedback
        except Exception as exc:
            logger.warning("FeedbackPendingDetector import failed: %s", exc)
            return []

        threshold = cfg.threshold if cfg.threshold is not None else 48
        cutoff = datetime.utcnow() - timedelta(hours=threshold)
        try:
            rows = await db.execute(
                select(Interview)
                .where(
                    Interview.company_id == company_id,
                    Interview.end_time < cutoff,
                    ~Interview.status.in_(("cancelled",)),
                )
                .limit(self.MAX_INTERVIEWS)
            )
            past = list(rows.scalars().all())
        except Exception as exc:
            logger.debug("FeedbackPendingDetector query failed: %s", exc)
            return []

        if not past:
            return []

        interview_ids = [i.id for i in past]
        try:
            fb_rows = await db.execute(
                select(InterviewFeedback.interview_id).where(
                    InterviewFeedback.interview_id.in_(interview_ids)
                )
            )
            with_feedback = {r for (r,) in fb_rows.all()}
        except Exception as exc:
            logger.debug(
                "FeedbackPendingDetector feedback query failed: %s", exc
            )
            return []

        pending = [
            i
            for i in past
            if i.id not in with_feedback
            and not (getattr(i, "feedback", None) or {})
        ]
        if not pending:
            return []

        first = pending[0]
        return [
            {
                "title": f"{len(pending)} entrevista(s) sem feedback",
                "message": (
                    f"{len(pending)} entrevista(s) realizadas ha mais de "
                    f"{threshold}h ainda nao tem feedback registrado. Colete a "
                    "avaliacao enquanto a impressao esta fresca."
                ),
                "action": "navigate_to_interviews",
                "action_params": {
                    "ids": [str(i.id) for i in pending[:5]],
                    "reason": "feedback_pending",
                },
                "severity": self.severity,
                "expires_in_hours": cfg.cooldown_hours or 24,
                "related_job_id": (
                    str(first.job_vacancy_id)
                    if getattr(first, "job_vacancy_id", None)
                    else None
                ),
                "related_candidate_id": (
                    str(first.candidate_id)
                    if getattr(first, "candidate_id", None)
                    else None
                ),
                "channels": cfg.channels or {},
            }
        ]


class OffersPendingLongDetector(BaseDetector):
    """Trigger para propostas enviadas ha threshold+ horas sem resposta.

    Per-tenant override (AlertPreference.alert_type='offers_pending_long'):
    - threshold: horas desde o envio sem resposta (default 72).
    - cooldown_hours: dedup gate (default 24).

    Detecta OfferProposal com sent_at < now-threshold, sem accepted_at/
    declined_at e nao cancelada/expirada.
    """

    name = "offers_pending_long"
    severity = "high"

    async def detect(self, db, company_id, override=None):
        cfg = self._resolve_override(override)
        if not cfg.is_enabled:
            return []
        if not company_id:
            return []

        try:
            from sqlalchemy import select

            from lia_models.offer_proposal import OfferProposal
        except Exception as exc:
            logger.warning("OffersPendingLongDetector import failed: %s", exc)
            return []

        threshold = cfg.threshold if cfg.threshold is not None else 72
        cutoff = datetime.utcnow() - timedelta(hours=threshold)
        try:
            rows = await db.execute(
                select(OfferProposal)
                .where(
                    OfferProposal.company_id == company_id,
                    OfferProposal.sent_at.isnot(None),
                    OfferProposal.sent_at < cutoff,
                    OfferProposal.accepted_at.is_(None),
                    OfferProposal.declined_at.is_(None),
                    ~OfferProposal.status.in_(
                        ("accepted", "declined", "cancelled", "expired")
                    ),
                )
                .limit(50)
            )
            pending = list(rows.scalars().all())
        except Exception as exc:
            logger.debug("OffersPendingLongDetector query failed: %s", exc)
            return []

        if not pending:
            return []

        first = pending[0]
        return [
            {
                "title": f"{len(pending)} proposta(s) aguardando resposta",
                "message": (
                    f"{len(pending)} proposta(s) enviada(s) ha mais de "
                    f"{threshold}h sem resposta do candidato. Faca follow-up "
                    "antes que o candidato aceite outra oferta."
                ),
                "action": "navigate_to_offers",
                "action_params": {
                    "ids": [str(o.id) for o in pending[:5]],
                    "reason": "pending_long",
                },
                "severity": self.severity,
                "expires_in_hours": cfg.cooldown_hours or 24,
                "related_job_id": (
                    str(first.job_vacancy_id)
                    if getattr(first, "job_vacancy_id", None)
                    else None
                ),
                "related_candidate_id": (
                    str(first.candidate_id)
                    if getattr(first, "candidate_id", None)
                    else None
                ),
                "channels": cfg.channels or {},
            }
        ]


class TasksOverdueDetector(BaseDetector):
    """Trigger quando ha threshold+ tarefas pendentes alem do prazo.

    Per-tenant override (AlertPreference.alert_type='tasks_overdue'):
    - threshold: numero MINIMO de tarefas atrasadas para alertar (default 5).
      Interpretacao por-contagem (nao por-dias) para evitar 1 alerta por tarefa;
      o tenant pode baixar para 1 se quiser sensibilidade maxima.
    - cooldown_hours: dedup gate (default 8).

    Atrasada = due_date < now e status == PENDING (nao completed/failed).
    """

    name = "tasks_overdue"
    severity = "medium"

    async def detect(self, db, company_id, override=None):
        cfg = self._resolve_override(override)
        if not cfg.is_enabled:
            return []
        if not company_id:
            return []

        try:
            from sqlalchemy import func, select

            from lia_models.task import Task, TaskStatus
        except Exception as exc:
            logger.warning("TasksOverdueDetector import failed: %s", exc)
            return []

        now = datetime.utcnow()
        try:
            overdue = await db.scalar(
                select(func.count(Task.id)).where(
                    Task.company_id == company_id,
                    Task.due_date.isnot(None),
                    Task.due_date < now,
                    Task.status == TaskStatus.PENDING,
                )
            )
        except Exception as exc:
            logger.debug("TasksOverdueDetector query failed: %s", exc)
            return []

        overdue = int(overdue or 0)
        threshold = cfg.threshold if cfg.threshold is not None else 5
        if overdue < max(1, threshold):
            return []

        return [
            {
                "title": f"{overdue} tarefa(s) atrasada(s)",
                "message": (
                    f"{overdue} tarefa(s) pendente(s) ja passaram do prazo. "
                    "Revise as pendencias para nao travar o pipeline."
                ),
                "action": "navigate_to_tasks",
                "action_params": {"overdue_count": overdue, "filter": "overdue"},
                "severity": self.severity,
                "expires_in_hours": cfg.cooldown_hours or 8,
                "related_job_id": None,
                "related_candidate_id": None,
                "channels": cfg.channels or {},
            }
        ]


class EmailDeliveryLowDetector(BaseDetector):
    """Trigger quando a taxa de entrega de email cai abaixo do threshold (%).

    Per-tenant override (AlertPreference.alert_type='email_delivery_low'):
    - threshold: taxa minima de entrega (%) aceitavel (default 80).
    - cooldown_hours: dedup gate (default 24).

    Fonte real: MessageQueue (channel='email') nos ultimos WINDOW_DAYS dias.
    Taxa = (sent + delivered) / processados, onde processados exclui
    pending/processing/cancelled. Exige amostra minima (MIN_SAMPLE) — sem
    amostra suficiente, NAO alerta (canonical-fix: nada de metrica inventada).
    """

    name = "email_delivery_low"
    severity = "medium"

    WINDOW_DAYS = 7
    MIN_SAMPLE = 10
    DELIVERED_STATUSES = ("sent", "delivered")
    FAILED_STATUSES = ("failed", "bounced", "blocked")

    async def detect(self, db, company_id, override=None):
        cfg = self._resolve_override(override)
        if not cfg.is_enabled:
            return []
        if not company_id:
            return []

        try:
            from sqlalchemy import func, select

            from lia_models.message_queue import MessageQueue
        except Exception as exc:
            logger.warning("EmailDeliveryLowDetector import failed: %s", exc)
            return []

        cutoff = datetime.utcnow() - timedelta(days=self.WINDOW_DAYS)
        processed_statuses = self.DELIVERED_STATUSES + self.FAILED_STATUSES
        try:
            processed = await db.scalar(
                select(func.count(MessageQueue.id)).where(
                    MessageQueue.company_id == company_id,
                    MessageQueue.channel == "email",
                    MessageQueue.created_at >= cutoff,
                    MessageQueue.status.in_(processed_statuses),
                )
            )
            delivered = await db.scalar(
                select(func.count(MessageQueue.id)).where(
                    MessageQueue.company_id == company_id,
                    MessageQueue.channel == "email",
                    MessageQueue.created_at >= cutoff,
                    MessageQueue.status.in_(self.DELIVERED_STATUSES),
                )
            )
        except Exception as exc:
            logger.debug("EmailDeliveryLowDetector query failed: %s", exc)
            return []

        processed = int(processed or 0)
        delivered = int(delivered or 0)
        if processed < self.MIN_SAMPLE:
            return []

        rate = (delivered / processed) * 100
        threshold = cfg.threshold if cfg.threshold is not None else 80
        if rate >= threshold:
            return []

        return [
            {
                "title": f"Entrega de email baixa ({rate:.0f}%)",
                "message": (
                    f"Apenas {delivered} de {processed} emails dos ultimos "
                    f"{self.WINDOW_DAYS} dias foram entregues ({rate:.0f}%, "
                    f"abaixo de {threshold}%). Verifique reputacao de dominio e "
                    "taxa de bounce."
                ),
                "action": "navigate_to_communications",
                "action_params": {
                    "delivery_rate": round(rate, 1),
                    "window_days": self.WINDOW_DAYS,
                    "delivered": delivered,
                    "processed": processed,
                },
                "severity": self.severity,
                "expires_in_hours": cfg.cooldown_hours or 24,
                "related_job_id": None,
                "related_candidate_id": None,
                "channels": cfg.channels or {},
            }
        ]


class IdealCandidateFoundDetector(BaseDetector):
    """Trigger quando surge candidato com match >= threshold% recentemente.

    Per-tenant override (AlertPreference.alert_type='ideal_candidate_found'):
    - threshold: match minimo (%) para considerar ideal (default 90).
    - cooldown_hours: dedup gate (default 0 = sem janela; usamos fallback de
      expiracao para o hint nao ficar eterno).

    Fonte: VacancyCandidate.match_percentage em candidatos ativos atualizados
    nos ultimos WINDOW_DAYS (recem-encontrados/recem-pontuados).
    """

    name = "ideal_candidate_found"
    severity = "medium"

    WINDOW_DAYS = 7
    ACTIVE_STATUSES = (
        "sourced",
        "screening",
        "shortlisted",
        "interview",
        "approved",
        "pending",
    )

    async def detect(self, db, company_id, override=None):
        cfg = self._resolve_override(override)
        if not cfg.is_enabled:
            return []
        if not company_id:
            return []

        try:
            from sqlalchemy import select

            from lia_models.candidate import VacancyCandidate
        except Exception as exc:
            logger.warning("IdealCandidateFoundDetector import failed: %s", exc)
            return []

        threshold = cfg.threshold if cfg.threshold is not None else 90
        cutoff = datetime.utcnow() - timedelta(days=self.WINDOW_DAYS)
        try:
            rows = await db.execute(
                select(VacancyCandidate)
                .where(
                    VacancyCandidate.company_id == company_id,
                    VacancyCandidate.match_percentage.isnot(None),
                    VacancyCandidate.match_percentage >= threshold,
                    VacancyCandidate.status.in_(self.ACTIVE_STATUSES),
                    VacancyCandidate.updated_at >= cutoff,
                )
                .limit(20)
            )
            ideal = list(rows.scalars().all())
        except Exception as exc:
            logger.debug("IdealCandidateFoundDetector query failed: %s", exc)
            return []

        if not ideal:
            return []

        first = ideal[0]
        best = max((getattr(c, "match_percentage", 0) or 0) for c in ideal)
        return [
            {
                "title": f"{len(ideal)} candidato(s) ideal(is) encontrado(s)",
                "message": (
                    f"{len(ideal)} candidato(s) com match >= {threshold}% "
                    f"(melhor: {best:.0f}%) entraram no funil recentemente. "
                    "Priorize o contato antes da concorrencia."
                ),
                "action": "navigate_to_candidates_filtered",
                "action_params": {
                    "ids": [str(c.candidate_id) for c in ideal[:5]],
                    "reason": "ideal_match",
                    "min_match": threshold,
                },
                "severity": self.severity,
                "expires_in_hours": cfg.cooldown_hours or 24,
                "related_job_id": (
                    str(first.vacancy_id)
                    if getattr(first, "vacancy_id", None)
                    else None
                ),
                "related_candidate_id": (
                    str(first.candidate_id)
                    if getattr(first, "candidate_id", None)
                    else None
                ),
                "channels": cfg.channels or {},
            }
        ]


class AtsSyncFailedDetector(BaseDetector):
    """Trigger quando ha threshold+ falhas de sync ATS recentes.

    Per-tenant override (AlertPreference.alert_type='ats_sync_failed'):
    - threshold: numero minimo de jobs de sync FAILED na janela (default 3).
    - cooldown_hours: dedup gate (default 2).

    ATSSyncJob nao tem company_id direto — escopo via ATSConnection
    (connection_id -> ATSConnection.company_id). Janela: ultimas WINDOW_HOURS.
    """

    name = "ats_sync_failed"
    severity = "high"

    WINDOW_HOURS = 24

    async def detect(self, db, company_id, override=None):
        cfg = self._resolve_override(override)
        if not cfg.is_enabled:
            return []
        if not company_id:
            return []

        try:
            from sqlalchemy import func, select

            from lia_models.ats_integration import (
                ATSConnection,
                ATSSyncJob,
                SyncStatus,
            )
        except Exception as exc:
            logger.warning("AtsSyncFailedDetector import failed: %s", exc)
            return []

        cutoff = datetime.utcnow() - timedelta(hours=self.WINDOW_HOURS)
        try:
            failed = await db.scalar(
                select(func.count(ATSSyncJob.id))
                .select_from(ATSSyncJob)
                .join(
                    ATSConnection,
                    ATSConnection.id == ATSSyncJob.connection_id,
                )
                .where(
                    ATSConnection.company_id == company_id,
                    ATSSyncJob.status == SyncStatus.FAILED,
                    ATSSyncJob.created_at >= cutoff,
                )
            )
        except Exception as exc:
            logger.debug("AtsSyncFailedDetector query failed: %s", exc)
            return []

        failed = int(failed or 0)
        threshold = cfg.threshold if cfg.threshold is not None else 3
        if failed < max(1, threshold):
            return []

        return [
            {
                "title": f"{failed} falha(s) de sincronizacao ATS",
                "message": (
                    f"{failed} job(s) de sincronizacao com o ATS falharam nas "
                    f"ultimas {self.WINDOW_HOURS}h. Verifique credenciais e "
                    "conectividade da integracao."
                ),
                "action": "navigate_to_integrations",
                "action_params": {
                    "failed_count": failed,
                    "window_hours": self.WINDOW_HOURS,
                },
                "severity": self.severity,
                "expires_in_hours": cfg.cooldown_hours or 2,
                "related_job_id": None,
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
            # Task #1296 — 9 regras orfas do catalogo agora cobertas.
            ConversionRateLowDetector(),
            SlaNearExpirationDetector(),
            InterviewNotConfirmedDetector(),
            FeedbackPendingDetector(),
            OffersPendingLongDetector(),
            TasksOverdueDetector(),
            EmailDeliveryLowDetector(),
            IdealCandidateFoundDetector(),
            AtsSyncFailedDetector(),
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
            # Task #1295 (fail-loud): import quebrado NÃO pode passar silencioso.
            # Emite metric source="error" p/ distinguir de "tenant sem config".
            self.logger.warning(
                "AlertPreference import failed (using all defaults): %s", exc
            )
            _emit_threshold_source_metric("__load_overrides__", "error")
            return overrides

        try:
            result = await db.execute(
                select(AlertPreference).where(
                    AlertPreference.company_id == company_id,
                )
            )
            rows = list(result.scalars().all())
        except Exception as exc:
            # Task #1295 (fail-loud, canonical-fix): um erro de DB ao carregar a
            # config NÃO é o mesmo que "tenant sem config". Antes isto caía em
            # logger.debug (silencioso) e mascarava indisponibilidade como
            # "sem override". Eleva para WARNING + metric source="error" para
            # ficar observável. O batch ainda roda com defaults (fail-open
            # deliberado — ver test_orchestrator_fallback_when_load_fails), mas
            # de forma RASTREÁVEL, nunca silenciosa.
            self.logger.warning(
                "AlertPreference query failed for company=%s: %s — "
                "rodando detectors com defaults (source=error, fail-open)",
                company_id,
                exc,
            )
            _emit_threshold_source_metric("__load_overrides__", "error")
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

        # Task #1295: o gate de enable/canal é canônico via AlertPreference
        # (carregado em tenant_overrides acima). O wire antigo de
        # communication_settings.alerts[] era um ghost setting (alert_id nunca
        # batia com detector.name -> sempre True) e o channel caía sempre em
        # "email". REMOVIDO: enable vem de cfg.is_enabled (dentro de detect()),
        # canais vêm de cfg.channels (AlertPreference). communication_settings
        # mantém SÓ seu papel real (janela de envio / assinatura / LGPD),
        # consumido pelos dispatchers, não pelo gate de detecção.
        for detector in self.detectors:
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
                # Task #1295: override efetivo (tenant OU default canônico) — a
                # fonte dos canais que vão no hint. Espelha o que detect() resolve
                # internamente via _resolve_override.
                effective = (
                    override
                    if (override is not None and override.source == "tenant")
                    else _DEFAULT_TENANT_OVERRIDE.get(
                        detector.name, TenantThresholdOverride()
                    )
                )
                hints = await detector.detect(db, company_id, override=override)
                for hint in hints:
                    hint["detector"] = detector.name
                    hint["company_id"] = company_id
                    # Canais canônicos de AlertPreference (dict). Detector pode ter
                    # setado explicitamente; senão herda do override efetivo.
                    hint.setdefault("channels", dict(effective.channels))
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
            from sqlalchemy import and_, select, text as sa_text

            from lia_models.background_jobs import (
                ActionStatus,
                ActionType,
                ProactiveAction,
            )
        except Exception as exc:
            self.logger.error("ProactiveAction model import failed: %s", exc)
            return 0

        # Scheduler runs without an HTTP request context, so app.company_id is
        # not set → app_current_company_id() returns NULL → RLS policy
        # (company_id::text = app_current_company_id(), migration 124) denies
        # both SELECTs (dedup) and INSERTs.  Set it per-company via
        # set_config(is_local=true) — transaction-scoped, clears on commit.
        _rls_company_set: str | None = None

        persisted = 0
        for hint in hints:
            try:
                company_uuid = UUID(hint["company_id"])
            except (KeyError, ValueError):
                continue

            if str(company_uuid) != _rls_company_set:
                await db.execute(
                    sa_text("SELECT set_config('app.company_id', :cid, true)"),
                    {"cid": str(company_uuid)},
                )
                _rls_company_set = str(company_uuid)

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
                    # Task #1295: canais canônicos (AlertPreference) persistidos
                    # como lista para os dispatchers downstream (email/teams/...).
                    "channels": channels_to_list(hint.get("channels")),
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
    "ConversionRateLowDetector",
    "SlaNearExpirationDetector",
    "InterviewNotConfirmedDetector",
    "FeedbackPendingDetector",
    "OffersPendingLongDetector",
    "TasksOverdueDetector",
    "EmailDeliveryLowDetector",
    "IdealCandidateFoundDetector",
    "AtsSyncFailedDetector",
    "ProactiveDetectorService",
    "TenantThresholdOverride",
    "proactive_detector_service",
    "_DETECTOR_ALERT_TYPE_MAP",
    "_DEFAULT_TENANT_OVERRIDE",
]
