"""Contract tests — Task #1295 fonte-única-da-verdade de config de alerta.

Garante que TODOS os geradores de alerta proativo (ProactiveDetectorService +
MonitoringLoop) leem a MESMA config canônica (``AlertPreference`` via
``alert_config_resolver``) e que os defaults de código nunca divergem do
catálogo exibido na tela "Configurações → Comunicação & Alertas".

Sentinelas (canonical-fix):
1. ALERT_CONFIG_DEFAULTS espelha 1-1 o catálogo da UI (DEFAULT_ALERT_PREFERENCES)
   para todos os alert_types cobertos por gerador.
2. Os defaults do detector (_DEFAULT_TENANT_OVERRIDE) DERIVAM de
   ALERT_CONFIG_DEFAULTS — nenhum literal divergente.
3. resolve_alert_config honra ausência de config (default) e fail-loud em erro.
4. communication_settings_consumer importa CommunicationSettings do módulo
   canônico (não do shim observability quebrado).
5. Canais canônicos são persistidos: detector grava channels em suggested_action;
   MonitoringLoop persiste alert.channels (não hardcoded).
6. MonitoringLoop respeita o toggle: regra desabilitada => nenhum alerta.
"""
from __future__ import annotations

import ast
import asyncio
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _literal_assignment(path: Path, name: str):
    """Extrai e avalia (literal_eval) uma atribuição de módulo top-level."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise AssertionError(f"{name} não encontrado em {path}")


# =============================================================================
# 1. Defaults de código espelham o catálogo da UI
# =============================================================================
def test_alert_config_defaults_mirror_ui_catalog():
    from app.shared.services.alert_config_resolver import ALERT_CONFIG_DEFAULTS

    catalog_list = _literal_assignment(
        REPO_ROOT / "app" / "api" / "v1" / "alerts.py",
        "DEFAULT_ALERT_PREFERENCES",
    )
    catalog = {row["alert_type"]: row for row in catalog_list}

    for alert_type, default in ALERT_CONFIG_DEFAULTS.items():
        assert alert_type in catalog, (
            f"alert_type '{alert_type}' está em ALERT_CONFIG_DEFAULTS mas não no "
            f"catálogo da UI (DEFAULT_ALERT_PREFERENCES) — drift código↔UI."
        )
        ui = catalog[alert_type]
        assert default.is_enabled == ui["is_enabled"], alert_type
        assert default.threshold == ui["threshold"], alert_type
        assert default.cooldown_hours == ui["cooldown_hours"], alert_type
        assert default.channels == ui["channels"], alert_type


# =============================================================================
# 2. Defaults do detector derivam da fonte-única-da-verdade
# =============================================================================
def test_detector_defaults_derive_from_resolver():
    from app.shared.services.alert_config_resolver import ALERT_CONFIG_DEFAULTS
    from app.shared.services.proactive_detector_service import (
        _DEFAULT_TENANT_OVERRIDE,
        _DETECTOR_ALERT_TYPE_MAP,
    )

    for detector_name, alert_type in _DETECTOR_ALERT_TYPE_MAP.items():
        override = _DEFAULT_TENANT_OVERRIDE[detector_name]
        canonical = ALERT_CONFIG_DEFAULTS[alert_type]
        assert override.threshold == canonical.threshold, detector_name
        assert override.cooldown_hours == canonical.cooldown_hours, detector_name
        assert override.is_enabled == canonical.is_enabled, detector_name
        assert override.channels == canonical.channels, detector_name
        assert override.source == "default", detector_name


# =============================================================================
# 3. Resolver: fallback default + fail-loud
# =============================================================================
def test_resolver_returns_default_without_company():
    from app.shared.services.alert_config_resolver import resolve_alert_config

    res = asyncio.run(resolve_alert_config(None, "", "candidate_no_interaction"))
    assert res.source == "default"
    assert res.threshold == 5
    assert res.is_enabled is True


def test_resolver_unknown_alert_type_failsafe():
    from app.shared.services.alert_config_resolver import resolve_alert_config

    res = asyncio.run(resolve_alert_config(None, "", "tipo_inexistente_xyz"))
    # fail-safe enabled, mas sem threshold útil — nunca silenciosamente desliga.
    assert res.is_enabled is True
    assert res.source == "default"


def test_channels_to_list_ordering():
    from app.shared.services.alert_config_resolver import channels_to_list

    out = channels_to_list(
        {"whatsapp": True, "email": True, "bell": False, "teams": True}
    )
    assert out == ["email", "teams", "whatsapp"]
    assert channels_to_list(None) == []
    assert channels_to_list({}) == []


# =============================================================================
# 4. Consumer importa do módulo canônico
# =============================================================================
def test_consumer_imports_canonical_communication_settings():
    src = (
        REPO_ROOT
        / "app" / "shared" / "services" / "communication_settings_consumer.py"
    ).read_text(encoding="utf-8")
    assert "from app.models.observability import CommunicationSettings" not in src, (
        "communication_settings_consumer ainda importa CommunicationSettings do "
        "shim observability quebrado (Task #1295)."
    )
    assert (
        "from app.models.communication_settings import CommunicationSettings" in src
    )


# =============================================================================
# 5. Canais canônicos persistidos pelos geradores
# =============================================================================
def test_detector_persists_channels_in_suggested_action():
    src = (
        REPO_ROOT
        / "app" / "shared" / "services" / "proactive_detector_service.py"
    ).read_text(encoding="utf-8")
    assert '"channels": channels_to_list(hint.get("channels"))' in src


def test_monitoring_loop_persists_per_alert_channels():
    src = (
        REPO_ROOT / "app" / "domains" / "recruiter_assistant" / "services"
        / "monitoring_loop.py"
    ).read_text(encoding="utf-8")
    # NÃO mais hardcoded em create_notification.
    assert "channels=alert.channels" in src
    assert 'channels=["bell", "chat"],\n                    metadata' not in src


# =============================================================================
# 6. MonitoringLoop respeita o toggle (regra desabilitada => 0 alertas)
# =============================================================================
def test_monitoring_loop_skips_when_alert_disabled(monkeypatch):
    from app.domains.recruiter_assistant.services import monitoring_loop as ml
    from app.shared.services.alert_config_resolver import AlertConfigResolution

    async def _fake_resolve(db, company_id, alert_type):
        return AlertConfigResolution(
            alert_type=alert_type, is_enabled=False, threshold=5,
            cooldown_hours=24,
            channels={"email": False, "bell": True, "teams": False, "whatsapp": False},
            source="tenant",
        )

    class _FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def execute(self, *a, **k):  # pragma: no cover - não deve rodar
            raise AssertionError(
                "execute() não deveria ser chamado: alerta desabilitado deve "
                "retornar ANTES de qualquer query."
            )

    monkeypatch.setattr(
        "app.shared.services.alert_config_resolver.resolve_alert_config",
        _fake_resolve,
    )
    monkeypatch.setattr(
        "lia_config.database.AsyncSessionLocal", lambda: _FakeSession()
    )

    loop = ml.MonitoringLoop()
    stale = asyncio.run(loop._check_stale_candidates("company-xyz"))
    sla = asyncio.run(loop._check_sla_risks("company-xyz"))
    assert stale == []
    assert sla == []


def test_detector_load_overrides_fails_loud_on_db_error():
    """O erro de query em _load_tenant_overrides deve ser RASTREÁVEL (warning +
    metric source=error), nunca silencioso (logger.debug) que mascara
    indisponibilidade como 'tenant sem config'."""
    src = (
        REPO_ROOT
        / "app" / "shared" / "services" / "proactive_detector_service.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(src)

    func = None
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "_load_tenant_overrides":
            func = node
            break
    assert func is not None, "_load_tenant_overrides não encontrado"

    func_src = ast.get_source_segment(src, func) or ""
    # NÃO pode usar debug para o erro de query (silencioso).
    assert "self.logger.debug(" not in func_src, (
        "_load_tenant_overrides ainda usa logger.debug (silencioso) no path de "
        "erro — viola fail-loud (Task #1295)."
    )
    # DEVE emitir metric source=error para distinguir erro de ausência.
    assert '_emit_threshold_source_metric("__load_overrides__", "error")' in func_src


def test_resolve_alert_channels_preserves_in_app_surfaces():
    from app.domains.recruiter_assistant.services.monitoring_loop import (
        _resolve_alert_channels,
    )

    # bell ativo => também surface no chat (briefing).
    out = _resolve_alert_channels(
        {"email": True, "bell": True, "teams": False, "whatsapp": False}
    )
    assert "email" in out and "bell" in out and "chat" in out
    # nada marcado => fail-safe (não perde o alerta; regra ainda enabled aqui).
    assert _resolve_alert_channels({}) == ["bell", "chat"]
