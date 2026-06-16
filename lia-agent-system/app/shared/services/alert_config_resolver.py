"""Canonical alert-config resolver (Task #1295 — fonte-única-da-verdade).

PROBLEMA RESOLVIDO
==================
Antes desta camada, CADA gerador de alerta proativo decidia sozinho se uma
regra estava ligada, qual o threshold e quais canais usar:

- ``ProactiveDetectorService`` lia ``AlertPreference`` (correto) MAS sobrepunha
  um gate quebrado de ``communication_settings.alerts[]`` (sempre True) e um
  ``channel`` que caia sempre em "email".
- ``MonitoringLoop`` usava constantes HARDCODED (dias + canais ``["bell","chat"]``)
  e NUNCA consultava a config do tenant — o toggle da tela
  "Configurações → Comunicação & Alertas" era um ghost setting.
- Os defaults de código (``_DEFAULT_TENANT_OVERRIDE``) divergiam do catálogo
  exibido na UI (``DEFAULT_ALERT_PREFERENCES``): candidate=7 vs 5, stagnant=14 vs 10.

CANONICAL (ADR-WT-2025)
=======================
``AlertPreference`` (tabela ``alert_preferences``) é a ÚNICA fonte de verdade
para config de alerta — escrita pela tela de Configurações via
``POST /alerts/preferences`` (``is_enabled`` / ``threshold`` / ``cooldown_hours`` /
4 bool de canal). ``communication_settings`` mantém SÓ o seu papel real (janela
de envio / assinatura / cooldown LGPD), NUNCA o enable/canal dos alertas.

Este módulo expõe o leitor canônico que TODOS os geradores usam:

- :func:`resolve_alert_config` — resolve (company_id, alert_type) -> resolução
  efetiva (tenant override OU default), com source rastreável.
- :data:`ALERT_CONFIG_DEFAULTS` — registro ÚNICO de defaults, espelhando 1-1 os
  valores do catálogo da UI (``DEFAULT_ALERT_PREFERENCES``). Tanto o detector
  (``_DEFAULT_TENANT_OVERRIDE``) quanto o MonitoringLoop derivam daqui, e um
  sentinel (``test_alert_config_single_source``) trava qualquer divergência
  futura entre código e UI.
- :func:`channels_to_list` — converte o dict de canais canônico em lista para
  os dispatchers downstream.

FAIL-LOUD (canonical-fix)
=========================
``resolve_alert_config`` distingue ausência de config (default, logado +
metric ``source=default``) de ERRO de DB (logado em WARNING/ERROR + metric
``source=error``). NUNCA mascara silenciosamente uma config existente do tenant.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Ordem canônica dos canais (espelha as colunas channel_* de AlertPreference
# e as chaves do catálogo DEFAULT_ALERT_PREFERENCES).
CHANNEL_KEYS: tuple[str, ...] = ("email", "bell", "teams", "whatsapp")


@dataclass(frozen=True)
class AlertConfigDefault:
    """Default canônico de um alert_type. Espelha 1-1 o catálogo da UI."""

    is_enabled: bool
    threshold: int
    cooldown_hours: int
    channels: dict[str, bool]


@dataclass(frozen=True)
class AlertConfigResolution:
    """Resultado da resolução para (company_id, alert_type).

    source:
      - "tenant"  -> lido de AlertPreference (tenant configurou na tela).
      - "default" -> nenhum row; caímos no default canônico (espelha UI).
      - "error"   -> erro de DB; default aplicado MAS sinalizado (fail-loud).
    """

    alert_type: str
    is_enabled: bool
    threshold: int
    cooldown_hours: int
    channels: dict[str, bool]
    source: str


# ---------------------------------------------------------------------------
# Registro ÚNICO de defaults — DEVE espelhar app/api/v1/alerts.py:
# DEFAULT_ALERT_PREFERENCES (catálogo exibido na UI). O sentinel
# test_alert_config_single_source trava qualquer drift.
#
# Cobertura: TODOS os 15 alert_types do catálogo da UI têm gerador (Task #1296
# fechou as 9 regras órfãs — vide proactive_detector_service.py + a matriz 15/15
# em docs/runbooks/alert-config-single-source.md). Cada alert_type aqui é
# honrado por um detector canônico (ou pelo MonitoringLoop, no caso do
# sla_near_expiration legado por-dias).
# ---------------------------------------------------------------------------
ALERT_CONFIG_DEFAULTS: dict[str, AlertConfigDefault] = {
    "company_profile_incomplete": AlertConfigDefault(
        is_enabled=True, threshold=80, cooldown_hours=168,
        channels={"email": False, "bell": True, "teams": False, "whatsapp": False},
    ),
    "dsr_overdue": AlertConfigDefault(
        is_enabled=True, threshold=24, cooldown_hours=12,
        channels={"email": True, "bell": True, "teams": False, "whatsapp": False},
    ),
    "candidate_no_interaction": AlertConfigDefault(
        is_enabled=True, threshold=5, cooldown_hours=24,
        channels={"email": True, "bell": True, "teams": False, "whatsapp": False},
    ),
    "workforce_plan_stale": AlertConfigDefault(
        is_enabled=True, threshold=30, cooldown_hours=336,
        channels={"email": False, "bell": True, "teams": False, "whatsapp": False},
    ),
    "credits_low": AlertConfigDefault(
        is_enabled=True, threshold=20, cooldown_hours=12,
        channels={"email": True, "bell": True, "teams": True, "whatsapp": False},
    ),
    "candidates_stagnant": AlertConfigDefault(
        is_enabled=True, threshold=10, cooldown_hours=48,
        channels={"email": True, "bell": True, "teams": False, "whatsapp": False},
    ),
    "sla_near_expiration": AlertConfigDefault(
        is_enabled=True, threshold=80, cooldown_hours=12,
        channels={"email": True, "bell": True, "teams": True, "whatsapp": False},
    ),
    # Task #1296 — 8 regras órfãs ganharam detector canônico (sla_near_expiration
    # já existia acima). Valores espelham 1-1 DEFAULT_ALERT_PREFERENCES.
    "conversion_rate_low": AlertConfigDefault(
        is_enabled=True, threshold=2, cooldown_hours=48,
        channels={"email": True, "bell": True, "teams": False, "whatsapp": False},
    ),
    "interview_not_confirmed": AlertConfigDefault(
        is_enabled=True, threshold=24, cooldown_hours=12,
        channels={"email": True, "bell": True, "teams": True, "whatsapp": True},
    ),
    "feedback_pending": AlertConfigDefault(
        is_enabled=False, threshold=48, cooldown_hours=24,
        channels={"email": True, "bell": True, "teams": False, "whatsapp": False},
    ),
    "offers_pending_long": AlertConfigDefault(
        is_enabled=True, threshold=72, cooldown_hours=24,
        channels={"email": True, "bell": True, "teams": True, "whatsapp": True},
    ),
    "tasks_overdue": AlertConfigDefault(
        is_enabled=True, threshold=5, cooldown_hours=8,
        channels={"email": True, "bell": True, "teams": True, "whatsapp": False},
    ),
    "email_delivery_low": AlertConfigDefault(
        is_enabled=True, threshold=80, cooldown_hours=24,
        channels={"email": False, "bell": True, "teams": False, "whatsapp": False},
    ),
    "ideal_candidate_found": AlertConfigDefault(
        is_enabled=True, threshold=90, cooldown_hours=0,
        channels={"email": True, "bell": True, "teams": True, "whatsapp": True},
    ),
    "ats_sync_failed": AlertConfigDefault(
        is_enabled=True, threshold=3, cooldown_hours=2,
        channels={"email": True, "bell": True, "teams": True, "whatsapp": False},
    ),
}


def channels_to_list(channels: dict[str, bool] | None) -> list[str]:
    """Converte o dict canônico {email,bell,teams,whatsapp} em lista ordenada.

    Retorna só os canais ativos, na ordem de CHANNEL_KEYS. Dispatchers
    downstream iteram sobre essa lista.
    """
    if not channels:
        return []
    return [k for k in CHANNEL_KEYS if bool(channels.get(k, False))]


def _channels_from_row(row: object) -> dict[str, bool]:
    """Extrai o dict de canais de uma row AlertPreference (channel_* bools)."""
    return {
        "email": bool(getattr(row, "channel_email", False)),
        "bell": bool(getattr(row, "channel_bell", False)),
        "teams": bool(getattr(row, "channel_teams", False)),
        "whatsapp": bool(getattr(row, "channel_whatsapp", False)),
    }


def _emit_source_metric(alert_type: str, source: str) -> None:
    """Best-effort: reusa o counter alert_threshold_source_total do detector."""
    try:
        from app.shared.services.proactive_detector_service import (
            _emit_threshold_source_metric,
        )

        _emit_threshold_source_metric(alert_type, source)
    except Exception:  # noqa: BLE001 — métrica nunca quebra o caller
        pass


def _default_resolution(alert_type: str, source: str) -> AlertConfigResolution:
    d = ALERT_CONFIG_DEFAULTS.get(alert_type)
    if d is None:
        # alert_type desconhecido: fail-safe enabled, sem threshold útil.
        logger.warning(
            "resolve_alert_config: alert_type '%s' sem default canônico — "
            "fail-safe enabled. Registre em ALERT_CONFIG_DEFAULTS.",
            alert_type,
        )
        return AlertConfigResolution(
            alert_type=alert_type, is_enabled=True, threshold=0,
            cooldown_hours=0,
            channels={"email": False, "bell": True, "teams": False, "whatsapp": False},
            source=source,
        )
    return AlertConfigResolution(
        alert_type=alert_type,
        is_enabled=d.is_enabled,
        threshold=d.threshold,
        cooldown_hours=d.cooldown_hours,
        channels=dict(d.channels),
        source=source,
    )


async def resolve_alert_config(
    db: "AsyncSession",
    company_id: str,
    alert_type: str,
) -> AlertConfigResolution:
    """Resolve a config canônica de um alert_type para um tenant.

    Lê ``AlertPreference`` (canonical). Quando o tenant tem row(s) para o
    alert_type, usa a mais recente (``updated_at``). Quando não tem, cai no
    default canônico (que espelha a UI). Em erro de DB, loga alto e aplica
    default com ``source="error"`` (fail-loud, sem mascarar config existente).

    Multi-tenancy: filtra por ``company_id`` explicitamente.
    """
    if not company_id:
        return _default_resolution(alert_type, "default")

    try:
        from sqlalchemy import select

        from app.models.alert import AlertPreference
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "resolve_alert_config: AlertPreference import falhou (%s) — default",
            exc,
        )
        _emit_source_metric(alert_type, "error")
        return _default_resolution(alert_type, "error")

    try:
        result = await db.execute(
            select(AlertPreference).where(
                AlertPreference.company_id == company_id,
                AlertPreference.alert_type == alert_type,
            )
        )
        rows = list(result.scalars().all())
    except Exception as exc:  # noqa: BLE001
        # Fail-loud: NÃO mascarar config existente como "ausente".
        logger.warning(
            "resolve_alert_config: query AlertPreference falhou para "
            "company=%s alert_type=%s: %s — aplicando default (source=error)",
            company_id, alert_type, exc,
        )
        _emit_source_metric(alert_type, "error")
        return _default_resolution(alert_type, "error")

    if not rows:
        logger.info(
            "resolve_alert_config: sem AlertPreference para company=%s "
            "alert_type=%s — usando default canônico", company_id, alert_type,
        )
        _emit_source_metric(alert_type, "default")
        return _default_resolution(alert_type, "default")

    # Múltiplos users podem ter preference pro mesmo alert_type; pega a mais
    # recente (admin/team config = single source assumida).
    latest = rows[0]
    for row in rows[1:]:
        if getattr(row, "updated_at", None) and (
            getattr(latest, "updated_at", None) is None
            or getattr(row, "updated_at") > getattr(latest, "updated_at", datetime.min)
        ):
            latest = row

    d = ALERT_CONFIG_DEFAULTS.get(alert_type)
    fallback_threshold = d.threshold if d else 0
    fallback_cooldown = d.cooldown_hours if d else 0

    threshold_val = getattr(latest, "threshold", None)
    cooldown_val = getattr(latest, "cooldown_hours", None)

    _emit_source_metric(alert_type, "tenant")
    return AlertConfigResolution(
        alert_type=alert_type,
        is_enabled=bool(getattr(latest, "is_enabled", True)),
        threshold=int(threshold_val) if threshold_val is not None else fallback_threshold,
        cooldown_hours=(
            int(cooldown_val) if cooldown_val is not None else fallback_cooldown
        ),
        channels=_channels_from_row(latest),
        source="tenant",
    )
