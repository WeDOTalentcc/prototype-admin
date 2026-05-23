"""
Contract sensor — wsi_fallback_total Prometheus counter (Onda 2.3).

WHY THIS SENSOR EXISTS
======================
Audit E2E 2026-05-20 F6.B3: ``safe_json_parse`` NameError caia silentemente
em template fallback ("Conte sobre experiência com X"). API retornava HTTP
200 OK com perguntas falsa-positivas. Telemetria de status code reportava
100% saúde, feature broken por dias/semanas.

REGRA 4 anti-silent-fallback (CLAUDE.md) exige observability sensor.
``inc_wsi_fallback(framework, reason)`` foi implementado em
``app/shared/observability/fallback_metrics.py`` + wired em 3 call sites
no question_generator. Grafana alarm em rate > 5% detecta reincidência.

Esse sensor garante:
1. ``inc_wsi_fallback`` function existe + invocável
2. ``_WSI_FALLBACK_TEMPLATE`` Counter exposto via Prometheus REGISTRY
3. question_generator.py CHAMA inc_wsi_fallback em pelo menos 3 call sites
   (validation_fail x2 + llm_error)

Pattern: BLOCKING. Anti-regression — protege que counter continue wired.
"""
from __future__ import annotations

import inspect
from pathlib import Path


def _question_generator_source() -> str:
    repo_root = Path(__file__).resolve().parents[2]
    src = repo_root / "app" / "domains" / "cv_screening" / "services" / "wsi_service" / "question_generator.py"
    return src.read_text()


def test_inc_wsi_fallback_exists_and_callable():
    """``inc_wsi_fallback(framework, reason)`` deve estar publicamente importável."""
    from app.shared.observability.fallback_metrics import inc_wsi_fallback
    sig = inspect.signature(inc_wsi_fallback)
    params = list(sig.parameters.keys())
    assert params == ["framework", "reason"], (
        f"inc_wsi_fallback signature mudou: params={params} (esperado ['framework', 'reason'])"
    )


def test_wsi_fallback_counter_exists_in_prometheus_registry():
    """``wsi_fallback_total`` Counter deve estar registrado em Prometheus."""
    # Trigger lazy init importando o módulo
    import app.shared.observability.fallback_metrics  # noqa: F401
    from app.shared.observability.fallback_metrics import _get_counters

    wsi_counter, _ = _get_counters()
    assert wsi_counter is not None, (
        "wsi_fallback_total Counter não está inicializado. "
        "prometheus_client pode não estar instalado OU lazy init falhou."
    )


def test_question_generator_calls_inc_wsi_fallback_in_validation_fail():
    """question_generator.py CHAMA inc_wsi_fallback(_, 'validation_fail') >= 2x."""
    src = _question_generator_source()
    count = src.count('inc_wsi_fallback(_framework_label, "validation_fail")')
    assert count >= 2, (
        f"question_generator.py chama inc_wsi_fallback(_, 'validation_fail') "
        f"apenas {count}x (esperado >= 2). Hardening C.1 + retry sites devem "
        f"ambos chamar — observability gap se regredir."
    )


def test_question_generator_calls_inc_wsi_fallback_for_llm_error():
    """question_generator.py CHAMA inc_wsi_fallback(_, 'llm_error') em LLM failure path."""
    src = _question_generator_source()
    assert 'inc_wsi_fallback(framework_label, "llm_error")' in src, (
        "question_generator.py NÃO chama inc_wsi_fallback no LLM error path. "
        "Audit F6.B3 root cause: silent fallback sem counter = bug invisível."
    )


def test_question_generator_imports_inc_wsi_fallback():
    """question_generator.py importa inc_wsi_fallback do shared canonical."""
    src = _question_generator_source()
    expected_import = "from app.shared.observability.fallback_metrics import inc_wsi_fallback"
    assert expected_import in src, (
        f"question_generator.py não importa inc_wsi_fallback canonical.\n"
        f"Esperado: {expected_import}"
    )
