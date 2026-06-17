"""Contract tests -- Wave 4 Gap 1 (2026-05-22).

Validates that ``install_llm_guards()`` is invoked at EVERY process entry
point (FastAPI, Celery worker, RabbitMQ consumer if/when enabled) and is
idempotent + observable via the ``llm_guards_installed`` Prometheus gauge.

Background
==========

Wave 3 (commit b9db634e3) wired ``install_llm_guards()`` into ``app/main.py``
which covers the FastAPI process. But Celery workers run in a separate
process tree -- the prefork model spawns child processes that do NOT
inherit the monkey-patches applied in the API process. Without an
explicit hook on ``signals.worker_process_init``, every LLM call from a
background task would bypass the universal ai_credit_gate.

These tests are the harness sensor for that gap: they pin the wiring
(import-time presence) + idempotency + telemetry contract so future
refactors can't silently break it.
"""
from __future__ import annotations

import importlib
import logging
from unittest.mock import patch, MagicMock

import pytest


@pytest.fixture(autouse=True)
def _reset_llm_bootstrap_state():
    """Reset module-level ``_installed`` so each test starts clean."""
    import app.shared.llm_bootstrap as m
    saved = (m._installed, dict(m._LAST_INSTALL_STATUS))
    m._installed = False
    m._LAST_INSTALL_STATUS = {"anthropic": False, "openai": False, "gemini": False}
    yield
    m._installed, m._LAST_INSTALL_STATUS = saved


# ----------------------------------------------------------------------
# (1) FastAPI startup wires install_llm_guards in app/main.py
# ----------------------------------------------------------------------

def test_fastapi_startup_installs_guards():
    """``app/main.py`` MUST call install_llm_guards(entrypoint="fastapi")
    as one of the very first import-time side effects."""
    import pathlib
    main_path = pathlib.Path("app/main.py")
    src = main_path.read_text()

    # Must import the function.
    assert "from app.shared.llm_bootstrap import install_llm_guards" in src, (
        "app/main.py must import install_llm_guards (Wave 3 contract)"
    )
    # Must invoke it with the entrypoint label.
    assert 'install_llm_guards(entrypoint="fastapi")' in src, (
        "app/main.py must call install_llm_guards(entrypoint='fastapi') "
        "for the gauge to be tagged with the right entrypoint"
    )


# ----------------------------------------------------------------------
# (2) Celery worker startup wires install_llm_guards
# ----------------------------------------------------------------------

def test_celery_worker_startup_installs_guards():
    """``libs/config/lia_config/celery_app.py`` MUST register a
    ``worker_process_init`` signal handler that calls install_llm_guards
    with entrypoint='celery'."""
    import pathlib
    celery_path = pathlib.Path("libs/config/lia_config/celery_app.py")
    src = celery_path.read_text()

    assert "worker_process_init" in src, (
        "celery_app.py must use signals.worker_process_init.connect"
    )
    assert "install_llm_guards(entrypoint='celery')" in src or \
           'install_llm_guards(entrypoint="celery")' in src, (
        "celery_app.py must invoke install_llm_guards(entrypoint='celery') "
        "in its worker_process_init handler (Wave 4 Gap 1)"
    )


# ----------------------------------------------------------------------
# (3) Idempotent: multiple calls do not error or re-patch.
# ----------------------------------------------------------------------

def test_install_idempotent_no_error_on_second_call():
    """Calling install_llm_guards multiple times must be safe."""
    from app.shared.llm_bootstrap import install_llm_guards

    status1 = install_llm_guards(entrypoint="test-1")
    status2 = install_llm_guards(entrypoint="test-2")
    status3 = install_llm_guards(entrypoint="test-3")

    # Each call returns the same provider-status dict.
    assert status1 == status2 == status3
    # At least anthropic/openai must be present in this venv.
    assert status1["anthropic"] is True
    assert status1["openai"] is True


# ----------------------------------------------------------------------
# (4) Log message on install identifies entrypoint + providers.
# ----------------------------------------------------------------------

def test_log_message_on_install(caplog):
    """Install must emit an INFO log identifying the entrypoint and which
    providers were patched."""
    from app.shared.llm_bootstrap import install_llm_guards

    with caplog.at_level(logging.INFO, logger="app.shared.llm_bootstrap"):
        install_llm_guards(entrypoint="contract-test")

    messages = [r.getMessage() for r in caplog.records]
    combined = " ".join(messages)
    assert "LLM guards installed" in combined, (
        "Expected install message in INFO log"
    )
    assert "entrypoint=contract-test" in combined, (
        "Log message must include the entrypoint label"
    )
    assert "anthropic" in combined and "openai" in combined and "gemini" in combined, (
        "Log message must enumerate all 3 providers"
    )


# ----------------------------------------------------------------------
# (5) Prometheus gauge set after install (best-effort, observability).
# ----------------------------------------------------------------------

def test_prometheus_gauge_set_after_install():
    """``llm_guards_installed{provider, entrypoint}`` must be set to 1 for
    each successfully-patched provider after install_llm_guards()."""
    from app.shared.llm_bootstrap import install_llm_guards
    from app.shared.observability.canary_metrics import llm_guards_installed

    if llm_guards_installed is None:
        pytest.skip("prometheus_client not available in this env")

    install_llm_guards(entrypoint="contract-gauge-test")

    # Read back the gauge value -- prometheus_client's Gauge exposes
    # _value via the internal sample collector.
    samples = list(llm_guards_installed.collect())[0].samples
    # At least one sample with entrypoint=contract-gauge-test and value=1.
    matching = [
        s for s in samples
        if s.labels.get("entrypoint") == "contract-gauge-test" and s.value == 1.0
    ]
    assert matching, (
        f"Expected llm_guards_installed{{entrypoint='contract-gauge-test'}}=1 "
        f"sample; got samples={[(s.labels, s.value) for s in samples]}"
    )
