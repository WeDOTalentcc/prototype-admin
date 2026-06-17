"""
Tests — Z6-01, Z6-02, Z6-03, Z7-01.

Z6-01 — Consolidação ATS clients:
  1.  domain __init__ re-exporta do path canônico
  2.  GupyClient acessível via path de domínio
  3.  app.services.ats_clients é a fonte de verdade

Z6-02 — OpenTelemetry:
  4.  settings tem OTEL_SERVICE_NAME, OTEL_EXPORTER_OTLP_ENDPOINT, OTEL_TRACES_ENABLED
  5.  trace_span funciona quando TRACES_ENABLED=True (LightweightTracer)
  6.  trace_span é noop quando TRACES_ENABLED=False
  7.  get_trace_stats inclui otlp_active e traces_enabled
  8.  _try_init_otlp retorna False quando OTLP_ENDPOINT vazio
  9.  trace_span aplicado no CascadedRouter.route (decorador presente)
  10. trace_span aplicado no DLQService.push_failure
  11. trace_span aplicado no LearningLoopService.process_unprocessed_feedback
  12. GET /api/v1/traces endpoint registrado no main.py

Z6-03 — Presidio NER Layer 4:
  13. strip_pii_for_llm_prompt sem Presidio funciona normalmente
  14. _presidio_layer4_strip retorna texto original quando Presidio não instalado
  15. _presidio_layer4_strip com Presidio mockado remove PERSON entity
  16. _presidio_layer4_strip é fail-safe em exceção do analyzer
  17. LLM_PROMPT_PRESIDIO_ENABLED=false → layer4 não chamada

Z7-01 — Recruiter Behavior:
  18. RecruiterBehaviorProfile.to_dict() / from_dict() round-trip
  19. get_or_compute retorna perfil de cache quando disponível
  20. get_or_compute computa sem DB (sinais Redis vazios)
  21. record_action armazena sinal no Redis
  22. invalidate remove cache
  23. endpoint registrado no main.py
  24. _enrich_active_hours agrega horas corretamente
  25. communication_style derivado de volume de canais
"""
import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── Z6-01: ATS clients consolidation ─────────────────────────────────────────

def test_ats_domain_init_exports_from_canonical():
    from app.domains.ats_integration.services.ats_clients import GupyClient, ATSClient
    assert GupyClient is not None
    assert ATSClient is not None


def test_ats_domain_gupy_is_same_class_as_canonical():
    from app.domains.ats_integration.services.ats_clients import GupyClient as DomainGupy
    from app.domains.ats_integration.services.ats_clients.gupy import GupyClient as ServiceGupy
    assert DomainGupy is ServiceGupy


def test_ats_services_is_canonical():
    from app.domains.ats_integration.services.ats_clients.base import ATSClient
    from app.domains.ats_integration.services.ats_clients.gupy import GupyClient
    assert ATSClient is not None
    assert GupyClient is not None


# ── Z6-02: OpenTelemetry ──────────────────────────────────────────────────────

def test_settings_has_otel_fields():
    from app.core.config import settings
    assert hasattr(settings, "OTEL_SERVICE_NAME")
    assert hasattr(settings, "OTEL_EXPORTER_OTLP_ENDPOINT")
    assert hasattr(settings, "OTEL_TRACES_ENABLED")
    assert settings.OTEL_TRACES_ENABLED is True
    assert settings.OTEL_SERVICE_NAME == "lia-agent-system"


@pytest.mark.asyncio
async def test_trace_span_decorator_works():
    from app.shared.tracing import trace_span

    calls = []

    @trace_span("test.operation", attributes={"unit": "test"})
    async def my_func(x):
        calls.append(x)
        return x * 2

    result = await my_func(5)
    assert result == 10
    assert calls == [5]


@pytest.mark.asyncio
async def test_trace_span_noop_when_disabled():
    with patch.dict(os.environ, {"OTEL_TRACES_ENABLED": "false"}):
        # Reimport to pick up env var
        import importlib
        import app.shared.tracing as tracing_mod
        old = tracing_mod._TRACES_ENABLED
        tracing_mod._TRACES_ENABLED = False

        calls = []

        @tracing_mod.trace_span("noop.op")
        async def noop_func():
            calls.append(1)
            return "ok"

        result = await noop_func()
        assert result == "ok"
        assert calls == [1]  # still runs, just no tracing overhead
        tracing_mod._TRACES_ENABLED = old


def test_trace_stats_has_otlp_fields():
    from app.shared.tracing import get_trace_stats
    stats = get_trace_stats()
    assert "otlp_active" in stats
    assert "traces_enabled" in stats


def test_try_init_otlp_returns_false_when_no_endpoint():
    with patch.dict(os.environ, {"OTEL_EXPORTER_OTLP_ENDPOINT": ""}):
        from app.shared.tracing import _try_init_otlp
        result = _try_init_otlp()
        # Must be False when no endpoint configured
        assert result is False


def test_cascaded_router_has_trace_span():
    import inspect
    from app.orchestrator.routing.cascaded_router import CascadedRouter
    src = inspect.getsource(CascadedRouter.route)
    # The decorator is applied, so the original function should be wrapped
    assert "router.route" in inspect.getsource(
        sys.modules["app.orchestrator.routing.cascaded_router"]
    )


def test_dlq_service_has_trace_span():
    import inspect
    import app.shared.resilience.dlq_service as dlq_mod
    src = inspect.getsource(dlq_mod)
    assert "dlq.push_failure" in src


def test_learning_loop_has_trace_span():
    import inspect
    import app.shared.learning.learning_loop_service as ll_mod
    src = inspect.getsource(ll_mod)
    assert "learning.process_feedback" in src


def test_traces_router_registered():
    # routers registered in routes.py, not main.py (Phase 4B migration)
    # Read source directly to avoid triggering full module import which can fail in isolation
    import inspect, pathlib
    routes_src = pathlib.Path(inspect.getfile(__import__("app.api.routes", fromlist=["routes"])
                                             )).read_text() if "app.api.routes" in __import__("sys").modules else                  (pathlib.Path(__file__).parent.parent.parent / "app/api/routes.py").read_text()
    assert "traces_router" in routes_src


# ── Z6-03: Presidio NER Layer 4 ──────────────────────────────────────────────

def test_strip_pii_without_presidio_works_normally():
    from app.shared.pii_masking import strip_pii_for_llm_prompt
    text = "Email: user@example.com CPF: 123.456.789-09"
    result = strip_pii_for_llm_prompt(text)
    assert "user@example.com" not in result
    assert "123.456.789-09" not in result


def test_presidio_layer4_returns_text_when_not_installed():
    from app.shared.pii_masking import _presidio_layer4_strip
    # presidio not installed, should return text unchanged (fail-safe)
    text = "João Silva mora em São Paulo"
    result = _presidio_layer4_strip(text)
    assert result == text


@pytest.mark.asyncio
async def test_presidio_layer4_with_mocked_analyzer():
    """Simula Presidio instalado e verificando que entities são removidas."""
    import app.shared.pii_masking as pii_mod

    # Simula resultado do presidio
    mock_result = MagicMock()
    mock_result.start = 0
    mock_result.end = 10
    mock_result.entity_type = "PERSON"

    mock_analyzer = MagicMock()
    mock_analyzer.analyze.return_value = [mock_result]

    original_enabled = pii_mod._PRESIDIO_ENABLED
    pii_mod._PRESIDIO_ENABLED = True
    pii_mod._presidio_analyzer_instance = mock_analyzer

    try:
        result = pii_mod._presidio_layer4_strip("João Silva é candidato")
        assert "[PERSON REMOVIDO]" in result
    finally:
        pii_mod._PRESIDIO_ENABLED = original_enabled
        pii_mod._presidio_analyzer_instance = None


def test_presidio_layer4_failsafe_on_exception():
    import app.shared.pii_masking as pii_mod

    mock_analyzer = MagicMock()
    mock_analyzer.analyze.side_effect = RuntimeError("Presidio crashed")

    original_enabled = pii_mod._PRESIDIO_ENABLED
    pii_mod._PRESIDIO_ENABLED = True
    pii_mod._presidio_analyzer_instance = mock_analyzer

    try:
        text = "João Silva"
        result = pii_mod._presidio_layer4_strip(text)
        assert result == text  # fail-safe: retorna original
    finally:
        pii_mod._PRESIDIO_ENABLED = original_enabled
        pii_mod._presidio_analyzer_instance = None


def test_presidio_disabled_layer4_not_called():
    import app.shared.pii_masking as pii_mod
    original_enabled = pii_mod._PRESIDIO_ENABLED
    pii_mod._PRESIDIO_ENABLED = False
    try:
        with patch.object(pii_mod, "_get_presidio_analyzer") as mock_get:
            pii_mod._presidio_layer4_strip("João Silva")
        mock_get.assert_not_called()
    finally:
        pii_mod._PRESIDIO_ENABLED = original_enabled


# ── Z7-01: Recruiter Behavior ─────────────────────────────────────────────────

def test_behavior_profile_round_trip():
    from app.shared.services.recruiter_behavior_service import RecruiterBehaviorProfile
    profile = RecruiterBehaviorProfile(
        recruiter_id="user-1",
        company_id="co-1",
        active_hours_distribution={"9": 5, "14": 3},
        preferred_sourcing_channels={"linkedin": 10},
        communication_style="high_volume",
    )
    data = profile.to_dict()
    restored = RecruiterBehaviorProfile.from_dict(data)
    assert restored.recruiter_id == "user-1"
    assert restored.active_hours_distribution == {"9": 5, "14": 3}
    assert restored.communication_style == "high_volume"


@pytest.mark.asyncio
async def test_get_or_compute_uses_cache():
    from app.shared.services.recruiter_behavior_service import (
        RecruiterBehaviorService, RecruiterBehaviorProfile
    )
    svc = RecruiterBehaviorService()
    cached = RecruiterBehaviorProfile(
        recruiter_id="user-1", company_id="co-1", computed_at="2026-03-19T10:00:00+00:00"
    )
    svc._get_cached = AsyncMock(return_value=cached)
    svc._compute_and_cache = AsyncMock()

    result = await svc.get_or_compute("user-1", "co-1")
    assert result.recruiter_id == "user-1"
    svc._compute_and_cache.assert_not_called()


@pytest.mark.asyncio
async def test_get_or_compute_computes_when_no_cache():
    from app.shared.services.recruiter_behavior_service import (
        RecruiterBehaviorService, RecruiterBehaviorProfile
    )
    svc = RecruiterBehaviorService()
    computed = RecruiterBehaviorProfile(recruiter_id="user-2", company_id="co-1")
    svc._get_cached = AsyncMock(return_value=None)
    svc._compute_and_cache = AsyncMock(return_value=computed)

    result = await svc.get_or_compute("user-2", "co-1")
    assert result.recruiter_id == "user-2"
    svc._compute_and_cache.assert_called_once()


@pytest.mark.asyncio
async def test_record_action_stores_in_redis():
    from app.shared.services.recruiter_behavior_service import RecruiterBehaviorService
    svc = RecruiterBehaviorService()

    redis_mock = AsyncMock()
    redis_mock.lpush = AsyncMock(return_value=1)
    redis_mock.ltrim = AsyncMock()
    redis_mock.expire = AsyncMock()
    redis_mock.__aenter__ = AsyncMock(return_value=redis_mock)
    redis_mock.__aexit__ = AsyncMock(return_value=False)

    svc._get_redis = AsyncMock(return_value=redis_mock)
    await svc.record_action("user-1", "co-1", "sourcing_channel_used", {"channel": "linkedin"})

    redis_mock.lpush.assert_called_once()


@pytest.mark.asyncio
async def test_invalidate_removes_cache():
    from app.shared.services.recruiter_behavior_service import RecruiterBehaviorService, _behavior_key
    svc = RecruiterBehaviorService()

    redis_mock = AsyncMock()
    redis_mock.delete = AsyncMock()
    redis_mock.__aenter__ = AsyncMock(return_value=redis_mock)
    redis_mock.__aexit__ = AsyncMock(return_value=False)

    svc._get_redis = AsyncMock(return_value=redis_mock)
    await svc.invalidate("user-1", "co-1")

    redis_mock.delete.assert_called_once_with(_behavior_key("user-1", "co-1"))


def test_recruiter_behavior_router_registered():
    # routers registered in routes.py, not main.py (Phase 4B migration)
    # Read source directly to avoid triggering full module import which can fail in isolation
    import pathlib
    routes_path = pathlib.Path(__file__).parent.parent.parent / "app/api/routes.py"
    routes_src = routes_path.read_text()
    assert "recruiter_behavior_router" in routes_src


@pytest.mark.asyncio
async def test_enrich_active_hours():
    from app.shared.services.recruiter_behavior_service import (
        RecruiterBehaviorService, RecruiterBehaviorProfile
    )
    import json
    from datetime import datetime, timezone

    svc = RecruiterBehaviorService()
    profile = RecruiterBehaviorProfile(recruiter_id="u1", company_id="c1")

    signals = [
        json.dumps({"action_type": "batch_review", "ts": "2026-03-19T09:00:00+00:00", "metadata": {}}),
        json.dumps({"action_type": "batch_review", "ts": "2026-03-19T09:30:00+00:00", "metadata": {}}),
        json.dumps({"action_type": "batch_review", "ts": "2026-03-19T14:00:00+00:00", "metadata": {}}),
    ]

    redis_mock = AsyncMock()
    redis_mock.lrange = AsyncMock(return_value=signals)
    redis_mock.__aenter__ = AsyncMock(return_value=redis_mock)
    redis_mock.__aexit__ = AsyncMock(return_value=False)

    svc._get_redis = AsyncMock(return_value=redis_mock)
    await svc._enrich_active_hours(profile)

    assert profile.active_hours_distribution.get("9") == 2
    assert profile.active_hours_distribution.get("14") == 1


@pytest.mark.asyncio
async def test_communication_style_high_volume():
    from app.shared.services.recruiter_behavior_service import (
        RecruiterBehaviorService, RecruiterBehaviorProfile
    )
    import json

    svc = RecruiterBehaviorService()
    profile = RecruiterBehaviorProfile(recruiter_id="u1", company_id="c1")

    # 25 sinais de canal
    signals = [
        json.dumps({"action_type": "sourcing_channel_used", "ts": "2026-03-19T09:00:00+00:00",
                    "metadata": {"channel": "linkedin"}})
        for _ in range(25)
    ]

    redis_mock = AsyncMock()
    redis_mock.lrange = AsyncMock(return_value=signals)
    redis_mock.__aenter__ = AsyncMock(return_value=redis_mock)
    redis_mock.__aexit__ = AsyncMock(return_value=False)

    svc._get_redis = AsyncMock(return_value=redis_mock)
    await svc._enrich_sourcing_channels(profile)

    assert profile.communication_style == "high_volume"
    assert profile.preferred_sourcing_channels.get("linkedin") == 25
