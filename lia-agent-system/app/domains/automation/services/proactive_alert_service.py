"""

# ADR-001-EXEMPT: Cross-tenant proactive trigger scanner. Scans aggregate
# operational health across companies (no_contact, deadlines, interview metrics)
# for ops dashboards and alert dispatch. Tenant isolation reapplied when alerts
# fan out to per-company handlers downstream.
# TODO Sprint 6: extract scanning queries to dedicated cross-tenant repos with  # R-048: needs owner + ticket
# explicit company_id filtering audit logs.

Proactive Alert Service - Intelligent alert system for recruiters.

This service monitors KPIs and indicators to proactively alert recruiters
when conditions require their attention. It integrates with all other services
to detect issues and opportunities.

Alert Categories:
- Pipeline Health: conversion rates, stagnant candidates, pending offers
- Productivity: overdue tasks, daily goals, scorecard completion
- Communication: delivery rates, response rates, opt-outs
- Predictive: dropout risk, time-to-fill, ideal candidate detection
- System: ATS sync, agent health, credits, AI errors

PER-TENANT THRESHOLDS (ADR-WT-2025 Sprint A, 2026-05-22):
=========================================================
Cada AlertCondition consulta `AlertPreference` (canonical decidido em ADR-WT-2025)
por (company_id, alert_type) ANTES de aplicar threshold/cooldown/channel. Fallback:
usa default hardcoded em `ThresholdConfig.DEFAULT_THRESHOLDS` MAS loga
`logger.info("No tenant template for X, using default")` + incrementa Prometheus
counter `alert_threshold_source_total{alert_type, source}`.

- AlertPreference.is_enabled=False -> condition skip silencioso (log INFO + metric).
- AlertPreference.threshold -> overrides class constant (semantica per-condition,
  documentada em `ThresholdConfig.DEFAULT_THRESHOLDS`).
- AlertPreference.cooldown_hours -> aplica em `_can_send_alert` dedup.
- AlertPreference channels (email/bell/teams/whatsapp) -> passa pro `_send_alert`
  e mapeia para NotificationChannel.

Reuse: `TenantThresholdOverride` + `_emit_threshold_source_metric` vem de
`app.shared.services.proactive_detector_service` (DRY com 6 detectors).

ADR canonical: ~/Documents/wedotalent_audit_2026-05-21/ADR-WT-2025-alert-canonical-table.md
"""
import logging
from datetime import datetime, timedelta
from enum import Enum, StrEnum
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from lia_models.candidate import Candidate
from lia_models.interview import Interview
from lia_models.task import Task, TaskStatus
from app.services.notification_service import (
    NotificationChannel,
    NotificationService,
    NotificationType,
    ProactiveNotificationType,
)
from app.shared.services.proactive_detector_service import (
    TenantThresholdOverride,
    _emit_threshold_source_metric,
)

logger = logging.getLogger(__name__)


class AlertCategory(StrEnum):
    """Categories of proactive alerts."""
    PIPELINE = "pipeline"
    PRODUCTIVITY = "productivity"
    COMMUNICATION = "communication"
    PREDICTIVE = "predictive"
    SYSTEM = "system"


class AlertCondition(StrEnum):
    """Specific alert conditions that can be triggered."""
    CONVERSION_RATE_LOW = "conversion_rate_low"
    CANDIDATES_STAGNANT = "candidates_stagnant"
    OFFERS_PENDING_LONG = "offers_pending_long"
    PIPELINE_EMPTY = "pipeline_empty"
    TASKS_OVERDUE = "tasks_overdue"
    NO_ACTIVITY = "no_activity"
    DAILY_GOAL_RISK = "daily_goal_risk"
    SCORECARDS_PENDING = "scorecards_pending"
    EMAIL_DELIVERY_LOW = "email_delivery_low"
    CANDIDATES_NO_RESPONSE = "candidates_no_response"
    HIGH_OPT_OUT = "high_opt_out"
    DROPOUT_RISK_HIGH = "dropout_risk_high"
    TIME_TO_FILL_RISK = "time_to_fill_risk"
    IDEAL_CANDIDATE_FOUND = "ideal_candidate_found"
    REJECTION_PATTERN = "rejection_pattern"
    ATS_SYNC_FAILED = "ats_sync_failed"
    AGENT_HEALTH_LOW = "agent_health_low"
    CREDITS_LOW = "credits_low"
    AI_DECISION_ERROR = "ai_decision_error"


# ---------------------------------------------------------------------------
# Per-tenant threshold canonical (ADR-WT-2025 Sprint A)
# ---------------------------------------------------------------------------
# Mapeia AlertCondition.value -> AlertPreference.alert_type. Quando ProactiveAlertService
# roda um check, carregamos AlertPreference por (company_id, alert_type) e aplicamos
# o override. AlertPreference.threshold interpretation eh per-condition (vide
# ThresholdConfig.DEFAULT_THRESHOLDS abaixo).
#
# Para condition nova: registre aqui + adicione default em ThresholdConfig.DEFAULT_THRESHOLDS.

_CONDITION_ALERT_TYPE_MAP: dict[str, str] = {
    AlertCondition.CONVERSION_RATE_LOW.value: "conversion_rate_low",
    AlertCondition.CANDIDATES_STAGNANT.value: "candidates_stagnant",
    AlertCondition.OFFERS_PENDING_LONG.value: "offers_pending_long",
    AlertCondition.PIPELINE_EMPTY.value: "pipeline_empty",
    AlertCondition.TASKS_OVERDUE.value: "tasks_overdue",
    AlertCondition.NO_ACTIVITY.value: "no_activity",
    AlertCondition.DAILY_GOAL_RISK.value: "daily_goal_risk",
    AlertCondition.SCORECARDS_PENDING.value: "scorecards_pending",
    AlertCondition.EMAIL_DELIVERY_LOW.value: "email_delivery_low",
    AlertCondition.CANDIDATES_NO_RESPONSE.value: "candidates_no_response",
    AlertCondition.HIGH_OPT_OUT.value: "high_opt_out",
    AlertCondition.DROPOUT_RISK_HIGH.value: "dropout_risk_high",
    AlertCondition.TIME_TO_FILL_RISK.value: "time_to_fill_risk",
    AlertCondition.IDEAL_CANDIDATE_FOUND.value: "ideal_candidate_found",
    AlertCondition.REJECTION_PATTERN.value: "rejection_pattern",
    AlertCondition.ATS_SYNC_FAILED.value: "ats_sync_failed",
    AlertCondition.AGENT_HEALTH_LOW.value: "agent_health_low",
    AlertCondition.CREDITS_LOW.value: "credits_low",
    AlertCondition.AI_DECISION_ERROR.value: "ai_decision_error",
}


class ThresholdConfig:
    """Configuration for alert thresholds."""

    DEFAULT_THRESHOLDS = {
        AlertCondition.CONVERSION_RATE_LOW: {
            "threshold": 5.0,
            "operator": "lt",
            "severity": NotificationType.WARNING,
            "cooldown_hours": 24
        },
        AlertCondition.CANDIDATES_STAGNANT: {
            "threshold_days": 10,
            "min_count": 5,
            "severity": NotificationType.WARNING,
            "cooldown_hours": 48
        },
        AlertCondition.OFFERS_PENDING_LONG: {
            "threshold_hours": 72,
            "severity": NotificationType.URGENT,
            "cooldown_hours": 24
        },
        AlertCondition.PIPELINE_EMPTY: {
            "threshold_count": 3,
            "severity": NotificationType.URGENT,
            "cooldown_hours": 12
        },
        AlertCondition.TASKS_OVERDUE: {
            "threshold_count": 5,
            "severity": NotificationType.URGENT,
            "cooldown_hours": 8
        },
        AlertCondition.NO_ACTIVITY: {
            "threshold_hours": 2,
            "severity": NotificationType.INFO,
            "cooldown_hours": 4
        },
        AlertCondition.DAILY_GOAL_RISK: {
            "threshold_percent": 50,
            "check_hour": 16,
            "severity": NotificationType.WARNING,
            "cooldown_hours": 24
        },
        AlertCondition.SCORECARDS_PENDING: {
            "threshold_hours": 24,
            "min_count": 3,
            "severity": NotificationType.URGENT,
            "cooldown_hours": 12
        },
        AlertCondition.EMAIL_DELIVERY_LOW: {
            "threshold_percent": 80,
            "severity": NotificationType.WARNING,
            "cooldown_hours": 24
        },
        AlertCondition.CANDIDATES_NO_RESPONSE: {
            "threshold_hours": 48,
            "min_count": 5,
            "severity": NotificationType.ACTION_REQUIRED,
            "cooldown_hours": 24
        },
        AlertCondition.HIGH_OPT_OUT: {
            "threshold_count": 10,
            "period_days": 7,
            "severity": NotificationType.WARNING,
            "cooldown_hours": 72
        },
        AlertCondition.DROPOUT_RISK_HIGH: {
            "threshold_percent": 70,
            "severity": NotificationType.URGENT,
            "cooldown_hours": 24
        },
        AlertCondition.TIME_TO_FILL_RISK: {
            "threshold_percent": 120,
            "severity": NotificationType.WARNING,
            "cooldown_hours": 48
        },
        AlertCondition.IDEAL_CANDIDATE_FOUND: {
            "threshold_match": 90,
            "severity": NotificationType.SUCCESS,
            "cooldown_hours": 0
        },
        AlertCondition.REJECTION_PATTERN: {
            "threshold_percent": 60,
            "min_rejections": 10,
            "severity": NotificationType.INFO,
            "cooldown_hours": 168
        },
        AlertCondition.ATS_SYNC_FAILED: {
            "failure_count": 3,
            "severity": NotificationType.URGENT,
            "cooldown_hours": 2
        },
        AlertCondition.AGENT_HEALTH_LOW: {
            "threshold_percent": 70,
            "severity": NotificationType.WARNING,
            "cooldown_hours": 24
        },
        AlertCondition.CREDITS_LOW: {
            "threshold_percent": 20,
            "severity": NotificationType.WARNING,
            "cooldown_hours": 48
        },
        AlertCondition.AI_DECISION_ERROR: {
            "threshold_count": 1,
            "period_hours": 24,
            "severity": NotificationType.INFO,
            "cooldown_hours": 24
        }
    }

    @classmethod
    def get_threshold(cls, condition: AlertCondition) -> dict[str, Any]:
        """Get threshold configuration for a condition."""
        return cls.DEFAULT_THRESHOLDS.get(condition, {})


# Primary threshold field per AlertCondition. When AlertPreference.threshold
# is set, it overrides this specific field in the default config dict.
# Used by `_apply_tenant_override` to splice override.threshold into the
# correct slot. None means "no primary threshold field" (skip overrides).
_CONDITION_PRIMARY_THRESHOLD_FIELD: dict[AlertCondition, str | None] = {
    AlertCondition.CONVERSION_RATE_LOW: "threshold",
    AlertCondition.CANDIDATES_STAGNANT: "threshold_days",
    AlertCondition.OFFERS_PENDING_LONG: "threshold_hours",
    AlertCondition.PIPELINE_EMPTY: "threshold_count",
    AlertCondition.TASKS_OVERDUE: "threshold_count",
    AlertCondition.NO_ACTIVITY: "threshold_hours",
    AlertCondition.DAILY_GOAL_RISK: "threshold_percent",
    AlertCondition.SCORECARDS_PENDING: "threshold_hours",
    AlertCondition.EMAIL_DELIVERY_LOW: "threshold_percent",
    AlertCondition.CANDIDATES_NO_RESPONSE: "threshold_hours",
    AlertCondition.HIGH_OPT_OUT: "threshold_count",
    AlertCondition.DROPOUT_RISK_HIGH: "threshold_percent",
    AlertCondition.TIME_TO_FILL_RISK: "threshold_percent",
    AlertCondition.IDEAL_CANDIDATE_FOUND: "threshold_match",
    AlertCondition.REJECTION_PATTERN: "threshold_percent",
    AlertCondition.ATS_SYNC_FAILED: "failure_count",
    AlertCondition.AGENT_HEALTH_LOW: "threshold_percent",
    AlertCondition.CREDITS_LOW: "threshold_percent",
    AlertCondition.AI_DECISION_ERROR: "threshold_count",
}


class ProactiveAlertService:
    """
    Service for generating proactive alerts based on KPIs and conditions.

    This service runs periodic checks and sends notifications when
    conditions warrant recruiter attention.

    Per-tenant thresholds (ADR-WT-2025 Sprint A):
    --------------------------------------------
    Cada chamada de `check_all_conditions` carrega AlertPreference rows do
    tenant via `_load_overrides_for_company` e injeta os overrides em
    `_can_send_alert` + `_get_effective_threshold`. Fallback fail-closed:
    se nao houver default NEM tenant pra um alert_type, `_can_send_alert`
    retorna False (skip silencioso com log WARNING).
    """

    def __init__(self):
        self.notification_service = NotificationService()
        self.alert_history: dict[str, datetime] = {}
        self.thresholds: dict[AlertCondition, dict[str, Any]] = {
            k: v.copy() for k, v in ThresholdConfig.DEFAULT_THRESHOLDS.items()
        }
        # Per-run cache: {(company_id, alert_type): TenantThresholdOverride}.
        # Populated by `_load_overrides_for_company`, consumed by `_can_send_alert`
        # and `_get_effective_threshold`. Cleared at end of `check_all_conditions`.
        self._tenant_overrides_cache: dict[
            tuple[str, str], TenantThresholdOverride
        ] = {}

    def get_threshold(self, condition: AlertCondition) -> dict[str, Any]:
        """Get threshold configuration for a condition from instance thresholds.

        Note: returns DEFAULT (class-level) thresholds. For per-tenant effective
        values, use `_get_effective_threshold(condition, company_id)`.
        """
        return self.thresholds.get(condition, {})

    async def _load_overrides_for_company(
        self,
        company_id: str,
        db: AsyncSession,
    ) -> dict[str, TenantThresholdOverride]:
        """Carrega AlertPreference rows do tenant + monta dict por alert_type.

        Canonical table: AlertPreference (ADR-WT-2025). Quando o tenant nao
        tem row para um alert_type, NAO entra no dict (caller cai em default
        + log via `_get_override_for_condition`).

        Multi-tenancy: query filtra por company_id explicitamente.
        ADR-001-EXEMPT: leitura cross-user (todos os AlertPreference da
        company, agregado por alert_type usando o mais recente). Pattern
        compartilhado com ProactiveDetectorService._load_tenant_overrides.
        """
        overrides: dict[str, TenantThresholdOverride] = {}
        if not company_id:
            return overrides

        try:
            from app.models.alert import AlertPreference
        except Exception as exc:
            logger.warning(
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
            # Table may not exist in some envs; fall back to defaults.
            logger.debug(
                "AlertPreference query failed for company=%s: %s",
                company_id,
                exc,
            )
            return overrides

        # Agrega: por alert_type, pega a row com updated_at mais recente.
        latest_by_type: dict[str, Any] = {}
        for row in rows:
            atype = str(getattr(row, "alert_type", ""))
            if not atype:
                continue
            existing = latest_by_type.get(atype)
            if (
                existing is None
                or (
                    getattr(row, "updated_at", None) is not None
                    and getattr(row, "updated_at")
                    > getattr(existing, "updated_at", datetime.min)
                )
            ):
                latest_by_type[atype] = row

        for atype, row in latest_by_type.items():
            channels = {
                "email": bool(getattr(row, "channel_email", False)),
                "bell": bool(getattr(row, "channel_bell", False)),
                "teams": bool(getattr(row, "channel_teams", False)),
                "whatsapp": bool(getattr(row, "channel_whatsapp", False)),
            }
            overrides[atype] = TenantThresholdOverride(
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

    def _get_override_for_condition(
        self,
        condition: AlertCondition,
        company_id: str | None,
    ) -> TenantThresholdOverride | None:
        """Lookup override no cache populado por `_load_overrides_for_company`.

        Returns None quando company_id eh None ou nao ha row no cache
        para esse alert_type. Caller eh responsavel por fallback em default.
        """
        if not company_id:
            return None
        alert_type = _CONDITION_ALERT_TYPE_MAP.get(condition.value, condition.value)
        return self._tenant_overrides_cache.get((company_id, alert_type))

    def _get_effective_threshold(
        self,
        condition: AlertCondition,
        company_id: str | None = None,
    ) -> dict[str, Any]:
        """Retorna threshold dict com tenant override aplicado quando disponivel.

        Quando `AlertPreference.threshold` esta setado:
          - Splica em `_CONDITION_PRIMARY_THRESHOLD_FIELD[condition]` (slot canonical)
          - Emite Prometheus counter `alert_threshold_source_total{source=tenant}`
          - Log INFO eh emitido na 1a vez por (company, alert_type) via `_can_send_alert`

        Quando nao tem override OU threshold=None:
          - Retorna class-level default
          - Emite counter `source=default`
        """
        defaults = self.thresholds.get(condition, {}).copy()
        override = self._get_override_for_condition(condition, company_id)
        alert_type = _CONDITION_ALERT_TYPE_MAP.get(
            condition.value, condition.value
        )

        if override is None or override.threshold is None:
            _emit_threshold_source_metric(alert_type, "default")
            return defaults

        primary_field = _CONDITION_PRIMARY_THRESHOLD_FIELD.get(condition)
        if primary_field is not None:
            defaults[primary_field] = override.threshold
        _emit_threshold_source_metric(alert_type, "tenant")
        return defaults

    def _can_send_alert(
        self,
        condition: AlertCondition,
        user_id: str,
        *,
        company_id: str | None = None,
    ) -> bool:
        """Check if alert is within cooldown period + respect tenant toggle.

        Per-tenant gates (ADR-WT-2025 Sprint A):
        1. `AlertPreference.is_enabled=False` -> skip silencioso (log INFO +
           Prometheus counter `tenant_disabled`).
        2. `AlertPreference.cooldown_hours` -> overrides class-level cooldown.
        3. Fail-closed: se nao ha default NEM tenant override pro alert_type,
           retorna False (skip + log WARNING).
        """
        alert_type = _CONDITION_ALERT_TYPE_MAP.get(
            condition.value, condition.value
        )
        override = self._get_override_for_condition(condition, company_id)

        # Tenant explicitly disabled this alert.
        if override is not None and not override.is_enabled:
            logger.info(
                "Alert %s disabled for company %s (per AlertPreference)",
                condition.value,
                company_id,
            )
            _emit_threshold_source_metric(alert_type, "tenant_disabled")
            return False

        # Cooldown gate: tenant cooldown_hours overrides class default.
        default_threshold = self.thresholds.get(condition, {})
        if not default_threshold and (
            override is None or override.cooldown_hours is None
        ):
            # Fail-closed: no default for this alert_type AND no tenant override.
            logger.warning(
                "No threshold for alert_type=%s (tenant nor default); skipping",
                condition.value,
            )
            return False

        tenant_cooldown = (
            override.cooldown_hours
            if override is not None and override.cooldown_hours is not None
            else None
        )
        cooldown_hours = (
            tenant_cooldown
            if tenant_cooldown is not None
            else default_threshold.get("cooldown_hours", 24)
        )

        key = f"{user_id}:{condition.value}"
        last_sent = self.alert_history.get(key)
        if not last_sent:
            return True

        return datetime.utcnow() - last_sent > timedelta(hours=cooldown_hours)

    def _get_channels_for_condition(
        self,
        condition: AlertCondition,
        company_id: str | None = None,
    ) -> dict[str, bool] | None:
        """Retorna channels per-tenant ou None (caller usa defaults).

        AlertPreference.channel_{email,bell,teams,whatsapp} -> dict.
        """
        override = self._get_override_for_condition(condition, company_id)
        if override is None or not override.channels:
            return None
        return dict(override.channels)

    def _record_alert_sent(self, condition: AlertCondition, user_id: str):
        """Record that an alert was sent."""
        key = f"{user_id}:{condition.value}"
        self.alert_history[key] = datetime.utcnow()

    async def check_all_conditions(
        self,
        user_id: str,
        company_id: str,
        db: AsyncSession | None = None
    ) -> list[dict[str, Any]]:
        """
        Check all alert conditions and return triggered alerts.

        This is the main entry point for the periodic alert check.

        Per-tenant: carrega AlertPreference rows do company_id ANTES de rodar
        os checks; injeta cache que `_can_send_alert` e `_get_effective_threshold`
        consultam. Cache eh limpo no finally.
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True

        try:
            # Pre-load AlertPreference rows do tenant (Sprint A canonical).
            try:
                overrides = await self._load_overrides_for_company(company_id, db)
                self._tenant_overrides_cache = {
                    (company_id, atype): ov for atype, ov in overrides.items()
                }
                logger.debug(
                    "Loaded %d AlertPreference overrides for company=%s",
                    len(overrides),
                    company_id,
                )
            except Exception as exc:
                logger.warning(
                    "Failed to load tenant overrides for company=%s, "
                    "falling back to defaults: %s",
                    company_id,
                    exc,
                )
                self._tenant_overrides_cache = {}

            triggered_alerts = []

            pipeline_alerts = await self.check_pipeline_health(user_id, company_id, db)
            triggered_alerts.extend(pipeline_alerts)

            productivity_alerts = await self.check_productivity(user_id, company_id, db)
            triggered_alerts.extend(productivity_alerts)

            communication_alerts = await self.check_communication_health(user_id, company_id, db)
            triggered_alerts.extend(communication_alerts)

            predictive_alerts = await self.check_predictive_indicators(user_id, company_id, db)
            triggered_alerts.extend(predictive_alerts)

            system_alerts = await self.check_system_health(user_id, company_id, db)
            triggered_alerts.extend(system_alerts)

            for alert in triggered_alerts:
                await self._send_alert(alert, user_id, company_id=company_id)

            logger.info(f"🔔 Proactive check completed: {len(triggered_alerts)} alerts triggered for user {user_id}")
            return triggered_alerts

        finally:
            # Always clear cache to avoid leaking overrides between runs/tenants.
            self._tenant_overrides_cache = {}
            if should_close:
                await db.close()

    async def check_pipeline_health(
        self,
        user_id: str,
        company_id: str,
        db: AsyncSession
    ) -> list[dict[str, Any]]:
        """Check pipeline-related alert conditions."""
        alerts = []

        try:
            result = await db.execute(
                select(Candidate.status, func.count(Candidate.id))
                .where(Candidate.is_active)
                .group_by(Candidate.status)
            )
            stage_counts = {row[0]: row[1] for row in result.all()}
            total = sum(stage_counts.values())

            if total > 0:
                hired = stage_counts.get("hired", 0) + stage_counts.get("contratado", 0)
                conversion_rate = (hired / total) * 100

                threshold = self._get_effective_threshold(
                    AlertCondition.CONVERSION_RATE_LOW, company_id=company_id
                )
                if conversion_rate < threshold.get("threshold", 5):
                    if self._can_send_alert(
                        AlertCondition.CONVERSION_RATE_LOW,
                        user_id,
                        company_id=company_id,
                    ):
                        alerts.append({
                            "condition": AlertCondition.CONVERSION_RATE_LOW,
                            "category": AlertCategory.PIPELINE,
                            "title": "📉 Taxa de Conversão Baixa",
                            "message": f"Sua taxa de conversão está em {conversion_rate:.1f}%. Posso analisar os gargalos do funil para você?",
                            "severity": threshold.get("severity"),
                            "data": {"conversion_rate": conversion_rate, "total_candidates": total},
                            "suggested_action": "analyze_funnel",
                            "action_label": "Analisar Funil"
                        })

            threshold = self._get_effective_threshold(
                AlertCondition.CANDIDATES_STAGNANT, company_id=company_id
            )
            cutoff_date = datetime.utcnow() - timedelta(days=threshold.get("threshold_days", 10))

            result = await db.execute(
                select(func.count(Candidate.id)).where(
                    and_(
                        Candidate.status.in_(["screening", "triagem", "Triagem"]),
                        Candidate.updated_at < cutoff_date,
                        Candidate.is_active
                    )
                )
            )
            stagnant_count = result.scalar() or 0

            if stagnant_count >= threshold.get("min_count", 5):
                if self._can_send_alert(
                    AlertCondition.CANDIDATES_STAGNANT,
                    user_id,
                    company_id=company_id,
                ):
                    alerts.append({
                        "condition": AlertCondition.CANDIDATES_STAGNANT,
                        "category": AlertCategory.PIPELINE,
                        "title": "⏳ Candidatos Parados na Triagem",
                        "message": f"{stagnant_count} candidatos estão na triagem há mais de {threshold.get('threshold_days', 10)} dias. Quer que eu priorize a avaliação?",
                        "severity": threshold.get("severity"),
                        "data": {"stagnant_count": stagnant_count},
                        "suggested_action": "batch_screening",
                        "action_label": "Triagem em Massa"
                    })

            threshold = self._get_effective_threshold(
                AlertCondition.OFFERS_PENDING_LONG, company_id=company_id
            )
            cutoff_time = datetime.utcnow() - timedelta(hours=threshold.get("threshold_hours", 72))

            result = await db.execute(
                select(func.count(Candidate.id)).where(
                    and_(
                        Candidate.status.in_(["offer", "oferta", "Proposta"]),
                        Candidate.updated_at < cutoff_time,
                        Candidate.is_active
                    )
                )
            )
            pending_offers = result.scalar() or 0

            if pending_offers > 0:
                if self._can_send_alert(
                    AlertCondition.OFFERS_PENDING_LONG,
                    user_id,
                    company_id=company_id,
                ):
                    alerts.append({
                        "condition": AlertCondition.OFFERS_PENDING_LONG,
                        "category": AlertCategory.PIPELINE,
                        "title": "🚨 Ofertas Pendentes Há Muito Tempo",
                        "message": f"{pending_offers} oferta(s) aguardam resposta há mais de 72h. Risco de perda de candidato! Quer que eu envie um follow-up?",
                        "severity": threshold.get("severity"),
                        "data": {"pending_offers": pending_offers},
                        "suggested_action": "send_offer_followup",
                        "action_label": "Enviar Follow-up"
                    })

        except Exception as e:
            logger.error(f"Error checking pipeline health: {e}")

        return alerts

    async def check_productivity(
        self,
        user_id: str,
        company_id: str,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        """Check productivity-related alert conditions."""
        alerts = []

        try:
            threshold = self._get_effective_threshold(
                AlertCondition.TASKS_OVERDUE, company_id=company_id
            )

            result = await db.execute(
                select(func.count(Task.id)).where(
                    and_(
                        Task.assigned_to_user_id == user_id,
                        Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
                        Task.due_date < datetime.utcnow()
                    )
                )
            )
            overdue_count = result.scalar() or 0

            if overdue_count >= threshold.get("threshold_count", 5):
                if self._can_send_alert(
                    AlertCondition.TASKS_OVERDUE,
                    user_id,
                    company_id=company_id,
                ):
                    alerts.append({
                        "condition": AlertCondition.TASKS_OVERDUE,
                        "category": AlertCategory.PRODUCTIVITY,
                        "title": "⏰ Tarefas Atrasadas",
                        "message": f"Você tem {overdue_count} tarefas atrasadas. Posso priorizar e reorganizar sua lista?",
                        "severity": threshold.get("severity"),
                        "data": {"overdue_count": overdue_count},
                        "suggested_action": "prioritize_tasks",
                        "action_label": "Priorizar Tarefas"
                    })

            threshold = self._get_effective_threshold(
                AlertCondition.SCORECARDS_PENDING, company_id=company_id
            )
            cutoff_time = datetime.utcnow() - timedelta(hours=threshold.get("threshold_hours", 24))

            result = await db.execute(
                select(func.count(Interview.id)).where(
                    and_(
                        Interview.scheduled_at < cutoff_time,
                        Interview.status == "completed",
                        Interview.scorecard.is_(None)
                    )
                )
            )
            pending_scorecards = result.scalar() or 0

            if pending_scorecards >= threshold.get("min_count", 3):
                if self._can_send_alert(
                    AlertCondition.SCORECARDS_PENDING,
                    user_id,
                    company_id=company_id,
                ):
                    alerts.append({
                        "condition": AlertCondition.SCORECARDS_PENDING,
                        "category": AlertCategory.PRODUCTIVITY,
                        "title": "📝 Scorecards Pendentes",
                        "message": f"{pending_scorecards} entrevistas sem feedback há mais de 24h. Quer que eu envie lembretes aos gestores?",
                        "severity": threshold.get("severity"),
                        "data": {"pending_scorecards": pending_scorecards},
                        "suggested_action": "send_scorecard_reminder",
                        "action_label": "Enviar Lembretes"
                    })

            now = datetime.utcnow()
            threshold = self._get_effective_threshold(
                AlertCondition.DAILY_GOAL_RISK, company_id=company_id
            )

            if now.hour >= threshold.get("check_hour", 16):
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

                result = await db.execute(
                    select(func.count(Task.id)).where(
                        and_(
                            Task.assigned_to_user_id == user_id,
                            Task.status == TaskStatus.COMPLETED,
                            Task.updated_at >= today_start
                        )
                    )
                )
                completed_today = result.scalar() or 0

                daily_goal = 10
                progress = (completed_today / daily_goal) * 100 if daily_goal > 0 else 0

                if progress < threshold.get("threshold_percent", 50):
                    if self._can_send_alert(
                        AlertCondition.DAILY_GOAL_RISK,
                        user_id,
                        company_id=company_id,
                    ):
                        alerts.append({
                            "condition": AlertCondition.DAILY_GOAL_RISK,
                            "category": AlertCategory.PRODUCTIVITY,
                            "title": "📊 Meta do Dia em Risco",
                            "message": f"Atingiu {progress:.0f}% da meta diária. Posso acelerar alguns processos automaticamente?",
                            "severity": threshold.get("severity"),
                            "data": {"progress": progress, "completed": completed_today, "goal": daily_goal},
                            "suggested_action": "accelerate_processes",
                            "action_label": "Acelerar Processos"
                        })

        except Exception as e:
            logger.error(f"Error checking productivity: {e}")

        return alerts

    async def check_communication_health(
        self,
        user_id: str,
        company_id: str,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        """Check communication-related alert conditions."""
        alerts = []

        try:
            from lia_models.communication import CommunicationLog

            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            week_ago = today - timedelta(days=7)

            result = await db.execute(
                select(func.count(CommunicationLog.id)).where(
                    and_(
                        CommunicationLog.company_id == company_id,
                        CommunicationLog.created_at >= today,
                        CommunicationLog.channel == "email"
                    )
                )
            )
            total_emails = result.scalar() or 0

            result = await db.execute(
                select(func.count(CommunicationLog.id)).where(
                    and_(
                        CommunicationLog.company_id == company_id,
                        CommunicationLog.created_at >= today,
                        CommunicationLog.channel == "email",
                        CommunicationLog.status.in_(["sent", "delivered"])
                    )
                )
            )
            delivered_emails = result.scalar() or 0

            if total_emails > 10:
                delivery_rate = (delivered_emails / total_emails) * 100
                threshold = self._get_effective_threshold(
                    AlertCondition.EMAIL_DELIVERY_LOW, company_id=company_id
                )

                if delivery_rate < threshold.get("threshold_percent", 80):
                    if self._can_send_alert(
                        AlertCondition.EMAIL_DELIVERY_LOW,
                        user_id,
                        company_id=company_id,
                    ):
                        alerts.append({
                            "condition": AlertCondition.EMAIL_DELIVERY_LOW,
                            "category": AlertCategory.COMMUNICATION,
                            "title": "📧 Taxa de Entrega de Email Baixa",
                            "message": f"Taxa de entrega de emails caiu para {delivery_rate:.0f}%. Pode haver problema com domínio ou reputação.",
                            "severity": threshold.get("severity"),
                            "data": {"delivery_rate": delivery_rate, "total": total_emails, "delivered": delivered_emails},
                            "suggested_action": "check_email_settings",
                            "action_label": "Verificar Configurações"
                        })

            threshold = self._get_effective_threshold(
                AlertCondition.CANDIDATES_NO_RESPONSE, company_id=company_id
            )
            cutoff = datetime.utcnow() - timedelta(hours=threshold.get("threshold_hours", 48))

            result = await db.execute(
                select(func.count(CommunicationLog.id)).where(
                    and_(
                        CommunicationLog.company_id == company_id,
                        CommunicationLog.created_at < cutoff,
                        CommunicationLog.created_at >= week_ago,
                        CommunicationLog.status == "sent",
                        not CommunicationLog.response_received
                    )
                )
            )
            no_response_count = result.scalar() or 0

            if no_response_count >= threshold.get("min_count", 5):
                if self._can_send_alert(
                    AlertCondition.CANDIDATES_NO_RESPONSE,
                    user_id,
                    company_id=company_id,
                ):
                    alerts.append({
                        "condition": AlertCondition.CANDIDATES_NO_RESPONSE,
                        "category": AlertCategory.COMMUNICATION,
                        "title": "📭 Candidatos Sem Resposta",
                        "message": f"{no_response_count} candidatos não responderam em 48h. Quer que eu envie um follow-up automático?",
                        "severity": threshold.get("severity"),
                        "data": {"no_response_count": no_response_count},
                        "suggested_action": "send_followup",
                        "action_label": "Enviar Follow-up"
                    })

            threshold = self._get_effective_threshold(
                AlertCondition.HIGH_OPT_OUT, company_id=company_id
            )
            period_start = datetime.utcnow() - timedelta(days=threshold.get("period_days", 7))

            result = await db.execute(
                select(func.count(CommunicationLog.id)).where(
                    and_(
                        CommunicationLog.company_id == company_id,
                        CommunicationLog.created_at >= period_start,
                        CommunicationLog.status == "opt_out"
                    )
                )
            )
            opt_out_count = result.scalar() or 0

            if opt_out_count >= threshold.get("threshold_count", 10):
                if self._can_send_alert(
                    AlertCondition.HIGH_OPT_OUT,
                    user_id,
                    company_id=company_id,
                ):
                    alerts.append({
                        "condition": AlertCondition.HIGH_OPT_OUT,
                        "category": AlertCategory.COMMUNICATION,
                        "title": "⚠️ Alto Volume de Opt-outs",
                        "message": f"{opt_out_count} candidatos solicitaram opt-out essa semana. Recomendo revisar templates e frequência de envio.",
                        "severity": threshold.get("severity"),
                        "data": {"opt_out_count": opt_out_count},
                        "suggested_action": "review_templates",
                        "action_label": "Revisar Templates"
                    })

        except ImportError:
            logger.debug("CommunicationLog model not available, skipping communication health checks")
        except Exception as e:
            logger.error(f"Error checking communication health: {e}")

        return alerts

    async def check_predictive_indicators(
        self,
        user_id: str,
        company_id: str,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        """Check predictive alert conditions using AI."""
        alerts = []

        try:
            threshold = self._get_effective_threshold(
                AlertCondition.IDEAL_CANDIDATE_FOUND, company_id=company_id
            )

            # Multi-tenancy fail-closed: filter by company_id (P0 LGPD fix 2026-05-22)
            result = await db.execute(
                select(Candidate).where(
                    and_(
                        Candidate.company_id == company_id,
                        Candidate.is_active,
                        Candidate.lia_score >= threshold.get("threshold_match", 90)
                    )
                ).order_by(Candidate.created_at.desc()).limit(5)
            )
            ideal_candidates = result.scalars().all()

            for candidate in ideal_candidates:
                if not self._can_send_alert(
                    AlertCondition.IDEAL_CANDIDATE_FOUND,
                    user_id,
                    company_id=company_id,
                ):
                    # Skip ALL remaining ideal candidates this cycle (single
                    # cooldown gate per alert_type). Mirrors original behavior
                    # except adds explicit tenant respect.
                    break
                alerts.append({
                    "condition": AlertCondition.IDEAL_CANDIDATE_FOUND,
                    "category": AlertCategory.PREDICTIVE,
                    "title": "✨ Candidato Ideal Encontrado!",
                    "message": f"{candidate.name} tem {candidate.lia_score}% de compatibilidade! Quer agendar uma entrevista agora?",
                    "severity": threshold.get("severity"),
                    "data": {"candidate_id": candidate.id, "name": candidate.name, "score": candidate.lia_score},
                    "suggested_action": "schedule_interview",
                    "action_label": "Agendar Entrevista"
                })

        except Exception as e:
            logger.error(f"Error checking predictive indicators: {e}")

        return alerts

    async def check_system_health(
        self,
        user_id: str,
        company_id: str,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        """Check system health alert conditions."""
        alerts = []

        try:
            from app.domains.ats_integration.services.ats_sync_service import ats_sync_service

            sync_stats = ats_sync_service.get_sync_stats()
            threshold = self._get_effective_threshold(
                AlertCondition.ATS_SYNC_FAILED, company_id=company_id
            )

            if sync_stats.get("errors", 0) >= threshold.get("failure_count", 3):
                if self._can_send_alert(
                    AlertCondition.ATS_SYNC_FAILED,
                    user_id,
                    company_id=company_id,
                ):
                    alerts.append({
                        "condition": AlertCondition.ATS_SYNC_FAILED,
                        "category": AlertCategory.SYSTEM,
                        "title": "🔴 Falha na Sincronização ATS",
                        "message": f"A integração com o ATS falhou {sync_stats.get('errors')} vezes. Verificar credenciais e configurações.",
                        "severity": threshold.get("severity"),
                        "data": sync_stats,
                        "suggested_action": "check_ats_settings",
                        "action_label": "Verificar Integração"
                    })
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Error checking ATS sync: {e}")

        try:
            from app.domains.analytics.services.agent_monitoring_service import AgentMonitoringService

            agent_monitor = AgentMonitoringService(db)
            global_metrics = await agent_monitor.get_global_metrics()
            threshold = self._get_effective_threshold(
                AlertCondition.AGENT_HEALTH_LOW, company_id=company_id
            )

            if global_metrics.get("success_rate", 100) < threshold.get("threshold_percent", 70):
                if self._can_send_alert(
                    AlertCondition.AGENT_HEALTH_LOW,
                    user_id,
                    company_id=company_id,
                ):
                    alerts.append({
                        "condition": AlertCondition.AGENT_HEALTH_LOW,
                        "category": AlertCategory.SYSTEM,
                        "title": "⚠️ Saúde dos Agentes Baixa",
                        "message": f"Taxa de sucesso dos agentes está em {global_metrics.get('success_rate'):.0f}%. Pode haver problemas de performance.",
                        "severity": threshold.get("severity"),
                        "data": global_metrics,
                        "suggested_action": "check_agent_health",
                        "action_label": "Ver Diagnóstico"
                    })
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Error checking agent health: {e}")

        try:
            from app.services.credits_service import CreditsService

            credits_service = CreditsService()
            credits_info = await credits_service.get_credits_balance(company_id, db)
            threshold = self._get_effective_threshold(
                AlertCondition.CREDITS_LOW, company_id=company_id
            )

            if credits_info:
                remaining_percent = (credits_info.get("remaining", 0) / max(credits_info.get("total", 1), 1)) * 100
                if remaining_percent < threshold.get("threshold_percent", 20):
                    if self._can_send_alert(
                        AlertCondition.CREDITS_LOW,
                        user_id,
                        company_id=company_id,
                    ):
                        alerts.append({
                            "condition": AlertCondition.CREDITS_LOW,
                            "category": AlertCategory.SYSTEM,
                            "title": "💳 Créditos de Pesquisa Baixos",
                            "message": f"Restam apenas {remaining_percent:.0f}% dos créditos de busca. Considere adquirir mais créditos.",
                            "severity": threshold.get("severity"),
                            "data": credits_info,
                            "suggested_action": "buy_credits",
                            "action_label": "Comprar Créditos"
                        })
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Error checking credits: {e}")

        try:
            from app.shared.services.audit_service import AuditService

            audit_service = AuditService()
            threshold = self._get_effective_threshold(
                AlertCondition.AI_DECISION_ERROR, company_id=company_id
            )
            period_hours = threshold.get("period_hours", 24)
            start_date = datetime.utcnow() - timedelta(hours=period_hours)

            stats = await audit_service.get_decision_statistics(
                company_id=company_id,
                start_date=start_date
            )

            override_count = stats.get("human_overridden", 0)
            if override_count >= threshold.get("threshold_count", 1):
                if self._can_send_alert(
                    AlertCondition.AI_DECISION_ERROR,
                    user_id,
                    company_id=company_id,
                ):
                    alerts.append({
                        "condition": AlertCondition.AI_DECISION_ERROR,
                        "category": AlertCategory.SYSTEM,
                        "title": "🤖 Decisões IA Ajustadas",
                        "message": f"{override_count} decisão(ões) da IA precisaram de ajuste manual nas últimas {period_hours}h. Posso mostrar detalhes.",
                        "severity": threshold.get("severity"),
                        "data": stats,
                        "suggested_action": "view_ai_decisions",
                        "action_label": "Ver Decisões"
                    })
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Error checking AI decisions: {e}")

        return alerts

    async def _send_alert(
        self,
        alert: dict[str, Any],
        user_id: str,
        *,
        company_id: str | None = None,
    ):
        """Send an alert through the notification service.

        Per-tenant channels: AlertPreference.channel_{email,bell,teams,whatsapp}
        override defaults quando setado pra esse alert_type. Quando nao ha
        override, usa baseline (BELL + CHAT, com TEAMS pra URGENT).
        """
        try:
            condition = alert.get("condition")
            tenant_channels = (
                self._get_channels_for_condition(condition, company_id=company_id)
                if isinstance(condition, AlertCondition)
                else None
            )

            if tenant_channels is not None:
                # Map AlertPreference channel flags -> NotificationChannel enum.
                channels: list[NotificationChannel] = []
                if tenant_channels.get("bell"):
                    channels.append(NotificationChannel.BELL)
                if tenant_channels.get("email"):
                    channels.append(NotificationChannel.EMAIL)
                if tenant_channels.get("teams"):
                    channels.append(NotificationChannel.TEAMS)
                if tenant_channels.get("whatsapp"):
                    channels.append(NotificationChannel.WHATSAPP)
                # CHAT canal nao tem flag dedicada em AlertPreference; eh sempre
                # incluido como UX padrao do chat inferior (parte do widget LIA).
                channels.append(NotificationChannel.CHAT)
                if not channels:
                    # Tenant disabled tudo -> fail-closed sem enviar.
                    logger.info(
                        "All channels disabled for alert=%s company=%s, skipping send",
                        alert.get("condition"),
                        company_id,
                    )
                    if isinstance(condition, AlertCondition):
                        self._record_alert_sent(condition, user_id)
                    return
            else:
                channels = [NotificationChannel.BELL, NotificationChannel.CHAT]
                if alert.get("severity") == NotificationType.URGENT:
                    channels.append(NotificationChannel.TEAMS)

            # E1 (entrega multi-canal 2026-06-09): fan-out REAL via
            # send_multi_channel_notification. Antes chamava
            # create_proactive_notification (metodo inexistente) -> AttributeError
            # engolido -> zero entrega em canal nenhum. data["actions"]/company_id
            # alimentam os handlers de Teams (per-tenant) e Email.
            _action_url = f"/chat?action={alert.get('suggested_action', 'help')}"
            _action_label = alert.get("action_label", "Ver Mais")
            await self.notification_service.send_multi_channel_notification(
                user_id=user_id,
                title=alert["title"],
                message=alert["message"],
                channels=channels,
                notification_type=alert.get("severity", NotificationType.INFO),
                proactive_type=ProactiveNotificationType.APPROVAL_REQUEST,
                data={
                    "condition": alert["condition"].value if isinstance(alert["condition"], AlertCondition) else alert["condition"],
                    "category": alert["category"].value if isinstance(alert["category"], AlertCategory) else alert["category"],
                    "data": alert.get("data", {}),
                    "suggested_action": alert.get("suggested_action"),
                    "action_url": _action_url,
                    "action_label": _action_label,
                    "actions": [{"label": _action_label, "url": _action_url}],
                    "company_id": company_id,
                },
            )

            if isinstance(alert["condition"], AlertCondition):
                self._record_alert_sent(alert["condition"], user_id)

            logger.info(f"🔔 Alert sent: {alert['title']} to user {user_id}")

        except Exception as e:
            logger.error(f"Error sending alert: {e}")

    async def get_alert_history(self, user_id: str) -> dict[str, Any]:
        """Get history of alerts sent to a user."""
        user_alerts = {
            k.split(":")[1]: v.isoformat()
            for k, v in self.alert_history.items()
            if k.startswith(f"{user_id}:")
        }
        return user_alerts

    def update_threshold(
        self,
        condition: AlertCondition,
        new_threshold: dict[str, Any]
    ):
        """Update threshold configuration for a condition."""
        if condition in self.thresholds:
            self.thresholds[condition].update(new_threshold)
        else:
            self.thresholds[condition] = new_threshold

        logger.info(f"⚙️ Threshold updated for {condition.value}: {new_threshold}")


proactive_alert_service = ProactiveAlertService()
