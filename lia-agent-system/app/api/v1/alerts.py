"""
Alerts API - Endpoints for alert management.
"""
import logging
from datetime import datetime
from typing import Any, cast

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.notifications.repositories.alert_repository import AlertRepository
from app.domains.job_management.services.job_alert_service import job_alert_service
from app.models.alert import AlertConfig, AlertPreference, AlertSeverity
from app.shared.tenant_guard import get_verified_company_id
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alerts", tags=["alerts"])


def get_alert_repo(db: AsyncSession = Depends(get_db)) -> AlertRepository:
    return AlertRepository(db)


def _emit_legacy_alerts_config_endpoint_counter(
    *, method: str, company_id: str | None
) -> None:
    """Canary counter for ADR-WT-2025 Sprint D+1 partial.

    Tracks calls to deprecated GET/PUT /alerts/config to drive removal
    timing decision pre-sunset (2026-08-22). Spike = clients still on
    legacy API; sustained zero = safe to remove endpoint early.

    Fail-open: never raises (prometheus_client may be absent in dev).
    """
    try:
        import hashlib

        from app.shared.observability.canary_metrics import (
            legacy_alerts_config_endpoint_calls_total,
        )

        if legacy_alerts_config_endpoint_calls_total is None:
            return
        company_id_hash = (
            hashlib.sha256(company_id.encode("utf-8")).hexdigest()[:16]
            if company_id
            else "unknown"
        )
        legacy_alerts_config_endpoint_calls_total.labels(
            method=method, company_id_hash=company_id_hash
        ).inc()
    except Exception:  # pragma: no cover -- canary must never break endpoint
        pass


class AlertResponse(WeDoBaseModel):
    """Response model for an alert."""
    id: str
    alert_type: str | None
    severity: str | None
    status: str | None
    title: str
    message: str
    user_id: str | None
    job_id: str | None
    candidate_id: str | None
    context: dict | None
    suggested_actions: list | None
    acknowledged_at: datetime | None
    resolved_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertSummaryResponse(BaseModel):
    """Response model for alert summary."""
    critical: int
    high: int
    medium: int
    low: int
    info: int
    total: int


@router.get("/", response_model=list[AlertResponse])
async def list_alerts(
    severity: AlertSeverity | None = None,
    user_id: str | None = None,
    limit: int = Query(default=50, le=100),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List active alerts with optional filters."""
    alerts = await job_alert_service.get_active_alerts(
        db=db,
        user_id=user_id,
        severity=severity,
        limit=limit
    )
    return [alert.to_dict() for alert in alerts]


@router.get("/summary", response_model=AlertSummaryResponse)
async def get_alert_summary(
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get summary of active alerts by severity."""
    summary = await job_alert_service.get_alert_summary(db=db)
    return summary


@router.post("/check", response_model=None)
async def run_alert_checks(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Manually trigger alert checks."""
    # P0-W1-06: pass company_id so check_all_alerts respects alerts_enabled toggle
    alerts = await job_alert_service.check_all_alerts(db=db, company_id=company_id)
    return {
        "status": "completed",
        "alerts_created": len(alerts),
        "alerts": [alert.to_dict() for alert in alerts]
    }


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: str,
    user_id: str = "system",
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Acknowledge an alert."""
    alert = await job_alert_service.acknowledge_alert(
        db=db,
        alert_id=alert_id,
        user_id=user_id
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert.to_dict()


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: str,
    user_id: str = "system",
    resolution_note: str | None = None,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Resolve an alert."""
    alert = await job_alert_service.resolve_alert(
        db=db,
        alert_id=alert_id,
        user_id=user_id,
        resolution_note=resolution_note
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert.to_dict()


class AlertConfigItem(BaseModel):
    """Model for individual alert configuration."""
    id: str
    name: str
    description: str
    enabled: bool = True
    channel: str = "email"


class AlertConfigRequest(WeDoBaseModel):
    """Request model for alert configuration."""
    alerts: list[AlertConfigItem]
    briefing_frequency: str = "daily"


class AlertConfigResponse(BaseModel):
    """Response model for alert configuration."""
    alerts: list[dict]
    briefing_frequency: str


DEFAULT_ALERTS = [
    {"id": "1", "name": "SLA Próximo do Vencimento", "description": "Alerta quando um candidato está há 80% do SLA na mesma etapa", "enabled": True, "channel": "both"},
    {"id": "2", "name": "Meta Mensal em Risco", "description": "Notifica quando a meta de contratações do mês pode não ser atingida", "enabled": True, "channel": "email"},
    {"id": "3", "name": "Candidato Sem Interação", "description": "Alerta para candidatos sem contato há mais de 5 dias", "enabled": True, "channel": "teams"},
    {"id": "4", "name": "Entrevista Não Confirmada", "description": "Lembrete 24h antes de entrevistas sem confirmação", "enabled": True, "channel": "both"},
    {"id": "5", "name": "Feedback Pendente", "description": "Solicita feedback após 48h de entrevista realizada", "enabled": False, "channel": "email"}
]


@router.get("/config", response_model=AlertConfigResponse, deprecated=True)
async def get_alert_config(
    response: Response,
    company_id: str = Depends(get_verified_company_id),
    repo: AlertRepository = Depends(get_alert_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get current alert configuration. DEPRECATED 2026-05-22 — use /alerts/preferences instead.

    Sunset date: 2026-08-22 (RFC 8594). Continues working but emits Deprecation header.
    ADR-WT-2025 Sprint D cutover: canonical UI agora le AlertPreference, nao AlertConfig.
    """
    # ADR-WT-2025 Sprint D: deprecation headers (RFC 8594 + IETF draft).
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "Sat, 22 Aug 2026 00:00:00 GMT"
    response.headers["Link"] = '</api/v1/alerts/preferences>; rel="successor-version"'
    logger.warning(
        "legacy_alert_config_endpoint_read",
        extra={
            "company_id": company_id,
            "deprecated_since": "2026-05-22",
            "sunset_date": "2026-08-22",
            "successor": "/api/v1/alerts/preferences",
            "adr": "ADR-WT-2025",
        },
    )
    # ADR-WT-2025 Sprint D+1 partial: canary counter (drives sunset decision).
    _emit_legacy_alerts_config_endpoint_counter(method="GET", company_id=company_id)
    try:
        config = await repo.get_active_config_for_company(company_id)

        if config:
            alerts_value = cast(list[dict[Any, Any]], config.alerts) if config.alerts else DEFAULT_ALERTS
            freq_value = cast(str, config.briefing_frequency) if config.briefing_frequency else "daily"
            return AlertConfigResponse(
                alerts=alerts_value,
                briefing_frequency=freq_value
            )

        return AlertConfigResponse(
            alerts=DEFAULT_ALERTS,
            briefing_frequency="daily"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching alert config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch alert config: {str(e)}")


@router.put("/config", response_model=AlertConfigResponse, deprecated=True)
async def update_alert_config(
    data: AlertConfigRequest,
    response: Response,
    company_id: str = Depends(get_verified_company_id),
    repo: AlertRepository = Depends(get_alert_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update alert configuration. DEPRECATED 2026-05-22 — use /alerts/preferences instead.

    Sunset date: 2026-08-22 (RFC 8594). Backend continua gravando em AlertConfig
    (legacy) ate sunset; clientes devem migrar para /alerts/preferences (canonical
    per ADR-WT-2025). Sprint D+1 removera o handler.

    REGRA 4 (anti silent-fallback): mesmo deprecated, NAO mascarar erro — write
    legacy precisa continuar fail-loud se falhar.
    """
    # ADR-WT-2025 Sprint D: deprecation headers (RFC 8594).
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "Sat, 22 Aug 2026 00:00:00 GMT"
    response.headers["Link"] = '</api/v1/alerts/preferences>; rel="successor-version"'
    logger.warning(
        "legacy_alert_config_write",
        extra={
            "company_id": company_id,
            "deprecated_since": "2026-05-22",
            "sunset_date": "2026-08-22",
            "successor": "/api/v1/alerts/preferences",
            "adr": "ADR-WT-2025",
            "alert_count": len(data.alerts) if data.alerts else 0,
        },
    )
    # ADR-WT-2025 Sprint D+1 partial: canary counter (drives sunset decision).
    _emit_legacy_alerts_config_endpoint_counter(method="PUT", company_id=company_id)
    try:
        config = await repo.get_active_config_for_company(company_id)

        alerts_data = [a.model_dump() for a in data.alerts]

        if config:
            updated = await repo.update_config(config, {
                "alerts": alerts_data,
                "briefing_frequency": data.briefing_frequency,
                "updated_at": datetime.utcnow(),
            })
        else:
            updated = await repo.create_config({
                "company_id": company_id,
                "alerts": alerts_data,
                "briefing_frequency": data.briefing_frequency,
                "is_active": True,
            })

        logger.info(f"Alert config updated successfully for company {company_id}")

        return AlertConfigResponse(
            alerts=cast(list[dict[Any, Any]], updated.alerts),
            briefing_frequency=cast(str, updated.briefing_frequency)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating alert config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class AlertPreferenceChannels(BaseModel):
    """Channels configuration for alert preference."""
    email: bool = True
    bell: bool = True
    teams: bool = False
    whatsapp: bool = False


class AlertPreferenceItem(BaseModel):
    """Model for individual alert preference."""
    id: str | None = None
    user_id: str
    alert_type: str
    is_enabled: bool = True
    threshold: int | None = None
    channels: AlertPreferenceChannels = AlertPreferenceChannels()
    cooldown_hours: int = 24


class AlertPreferenceRequest(WeDoBaseModel):
    """Request model for creating/updating preferences."""
    preferences: list[AlertPreferenceItem]


class AlertPreferenceResponse(BaseModel):
    """Response model for alert preferences."""
    preferences: list[dict]
    user_id: str


DEFAULT_ALERT_PREFERENCES = [
    {"alert_type": "time_to_hire_critical", "name": "Time to Hire Crítico", "description": "Alerta quando time to hire ultrapassa limite", "is_enabled": True, "threshold": 45, "channels": {"email": True, "bell": True, "teams": False, "whatsapp": False}, "cooldown_hours": 24},
    {"alert_type": "conversion_rate_low", "name": "Taxa de Conversão Baixa", "description": "Alerta quando taxa de conversão está abaixo do limite", "is_enabled": True, "threshold": 2, "channels": {"email": True, "bell": True, "teams": False, "whatsapp": False}, "cooldown_hours": 48},
    {"alert_type": "nps_declining", "name": "NPS em Declínio", "description": "Alerta quando NPS cai abaixo do limite", "is_enabled": True, "threshold": 75, "channels": {"email": False, "bell": True, "teams": False, "whatsapp": False}, "cooldown_hours": 24},
    {"alert_type": "no_hires", "name": "Sem Contratações", "description": "Alerta quando não há contratações no período", "is_enabled": True, "threshold": 0, "channels": {"email": True, "bell": True, "teams": True, "whatsapp": False}, "cooldown_hours": 168},
    {"alert_type": "quality_score_low", "name": "Score de Qualidade Baixo", "description": "Alerta quando score de qualidade está baixo", "is_enabled": True, "threshold": 4, "channels": {"email": True, "bell": True, "teams": False, "whatsapp": False}, "cooldown_hours": 48},
    {"alert_type": "sla_near_expiration", "name": "SLA Próximo do Vencimento", "description": "Alerta quando candidato está há 80% do SLA na mesma etapa", "is_enabled": True, "threshold": 80, "channels": {"email": True, "bell": True, "teams": True, "whatsapp": False}, "cooldown_hours": 12},
    {"alert_type": "monthly_goal_at_risk", "name": "Meta Mensal em Risco", "description": "Notifica quando a meta de contratações pode não ser atingida", "is_enabled": True, "threshold": 50, "channels": {"email": True, "bell": True, "teams": False, "whatsapp": False}, "cooldown_hours": 24},
    {"alert_type": "candidate_no_interaction", "name": "Candidato Sem Interação", "description": "Alerta para candidatos sem contato há mais de 5 dias", "is_enabled": True, "threshold": 5, "channels": {"email": True, "bell": True, "teams": False, "whatsapp": False}, "cooldown_hours": 24},
    {"alert_type": "interview_not_confirmed", "name": "Entrevista Não Confirmada", "description": "Lembrete 24h antes de entrevistas sem confirmação", "is_enabled": True, "threshold": 24, "channels": {"email": True, "bell": True, "teams": True, "whatsapp": True}, "cooldown_hours": 12},
    {"alert_type": "feedback_pending", "name": "Feedback Pendente", "description": "Solicita feedback após 48h de entrevista realizada", "is_enabled": False, "threshold": 48, "channels": {"email": True, "bell": True, "teams": False, "whatsapp": False}, "cooldown_hours": 24},
    {"alert_type": "candidates_stagnant", "name": "Candidatos Estagnados", "description": "Candidatos parados na mesma etapa por muito tempo", "is_enabled": True, "threshold": 10, "channels": {"email": True, "bell": True, "teams": False, "whatsapp": False}, "cooldown_hours": 48},
    {"alert_type": "offers_pending_long", "name": "Propostas Pendentes", "description": "Propostas aguardando resposta por muito tempo", "is_enabled": True, "threshold": 72, "channels": {"email": True, "bell": True, "teams": True, "whatsapp": True}, "cooldown_hours": 24},
    {"alert_type": "pipeline_empty", "name": "Pipeline Vazio", "description": "Vaga com poucos candidatos ativos", "is_enabled": True, "threshold": 3, "channels": {"email": True, "bell": True, "teams": False, "whatsapp": False}, "cooldown_hours": 12},
    {"alert_type": "tasks_overdue", "name": "Tarefas Atrasadas", "description": "Tarefas pendentes além do prazo", "is_enabled": True, "threshold": 5, "channels": {"email": True, "bell": True, "teams": True, "whatsapp": False}, "cooldown_hours": 8},
    {"alert_type": "email_delivery_low", "name": "Entrega de Email Baixa", "description": "Taxa de entrega de emails abaixo do esperado", "is_enabled": True, "threshold": 80, "channels": {"email": False, "bell": True, "teams": False, "whatsapp": False}, "cooldown_hours": 24},
    {"alert_type": "dropout_risk_high", "name": "Risco de Desistência Alto", "description": "Candidato com alto risco de desistência", "is_enabled": True, "threshold": 70, "channels": {"email": True, "bell": True, "teams": True, "whatsapp": True}, "cooldown_hours": 24},
    {"alert_type": "ideal_candidate_found", "name": "Candidato Ideal Encontrado", "description": "Candidato com match acima de 90%", "is_enabled": True, "threshold": 90, "channels": {"email": True, "bell": True, "teams": True, "whatsapp": True}, "cooldown_hours": 0},
    {"alert_type": "ats_sync_failed", "name": "Falha na Sincronização ATS", "description": "Erro na sincronização com sistema ATS", "is_enabled": True, "threshold": 3, "channels": {"email": True, "bell": True, "teams": True, "whatsapp": False}, "cooldown_hours": 2},
    # ADR-WT-2025 (2026-05-22): catalogo extendido com 4 detector types
    # declarados em _DETECTOR_ALERT_TYPE_MAP (proactive_detector_service.py).
    # Cada um tem default em _DEFAULT_TENANT_OVERRIDE. Schema-sync sensor
    # scripts/check_alert_preferences_schema_sync.py garante 1-1 com TS canonical.
    {"alert_type": "company_profile_incomplete", "name": "Perfil da Empresa Incompleto", "description": "Alerta quando completeness do perfil da empresa esta abaixo do limite (%)", "is_enabled": True, "threshold": 80, "channels": {"email": False, "bell": True, "teams": False, "whatsapp": False}, "cooldown_hours": 168},
    {"alert_type": "dsr_overdue", "name": "Solicitacao LGPD Vencendo", "description": "Alerta quando DSR (Data Subject Request) esta proxima do deadline LGPD (horas)", "is_enabled": True, "threshold": 24, "channels": {"email": True, "bell": True, "teams": False, "whatsapp": False}, "cooldown_hours": 12},
    {"alert_type": "workforce_plan_stale", "name": "Plano de Workforce Desatualizado", "description": "Alerta quando workforce plan nao eh atualizado ha mais de X dias", "is_enabled": True, "threshold": 30, "channels": {"email": False, "bell": True, "teams": False, "whatsapp": False}, "cooldown_hours": 336},
    {"alert_type": "credits_low", "name": "Creditos IA Baixos", "description": "Alerta quando AI credits remaining cai abaixo do percentual configurado", "is_enabled": True, "threshold": 20, "channels": {"email": True, "bell": True, "teams": True, "whatsapp": False}, "cooldown_hours": 12},
]


@router.get("/preferences", response_model=None)
async def get_alert_preferences(
    user_id: str = Query(..., description="User ID (required)"),
    company_id: str = Depends(get_verified_company_id),
    repo: AlertRepository = Depends(get_alert_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get users alert preferences. Requires X-Company-ID header for multi-tenant isolation."""
    try:
        preferences = await repo.list_preferences_for_company_user(
            company_id=company_id,
            user_id=user_id,
        )

        if preferences:
            return {
                "preferences": [pref.to_dict() for pref in preferences],
                "user_id": user_id,
                "company_id": company_id
            }

        default_prefs = []
        for pref in DEFAULT_ALERT_PREFERENCES:
            default_prefs.append({
                "id": None,
                "company_id": company_id,
                "user_id": user_id,
                **pref
            })

        return {
            "preferences": default_prefs,
            "user_id": user_id,
            "company_id": company_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching alert preferences: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch alert preferences: {str(e)}")


@router.post("/preferences", response_model=None)
async def create_alert_preferences(
    data: AlertPreferenceRequest,
    company_id: str = Depends(get_verified_company_id),
    repo: AlertRepository = Depends(get_alert_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Create or update users alert preferences. Requires X-Company-ID header for multi-tenant isolation."""
    try:
        if not data.preferences:
            raise HTTPException(status_code=400, detail="Preferences list cannot be empty")

        user_id = data.preferences[0].user_id
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required in preferences")

        created_preferences = []
        for pref_data in data.preferences:
            pref = await repo.upsert_preference_by_type(
                company_id=company_id,
                user_id=pref_data.user_id,
                alert_type=pref_data.alert_type,
                data={
                    "is_enabled": pref_data.is_enabled,
                    "threshold": pref_data.threshold,
                    "channel_email": pref_data.channels.email,
                    "channel_bell": pref_data.channels.bell,
                    "channel_teams": pref_data.channels.teams,
                    "channel_whatsapp": pref_data.channels.whatsapp,
                    "cooldown_hours": pref_data.cooldown_hours,
                },
            )
            created_preferences.append(pref)

        logger.info(f"Alert preferences created/updated for user {user_id} in company {company_id}")

        return {
            "preferences": [pref.to_dict() for pref in created_preferences],
            "user_id": user_id,
            "company_id": company_id,
            "message": "Preferências salvas com sucesso"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating alert preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/preferences", response_model=None)
async def update_alert_preferences(
    data: AlertPreferenceRequest,
    company_id: str = Depends(get_verified_company_id),
    repo: AlertRepository = Depends(get_alert_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update users alert preferences. Requires X-Company-ID header for multi-tenant isolation."""
    return await create_alert_preferences(data, company_id, repo)
