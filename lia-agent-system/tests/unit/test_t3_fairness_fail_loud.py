"""
T3 — FairnessGuard Layer3: warning→error (fail-loud).

check_semantic é o método onde a LIA-FG-01 ERROR é logada quando
app.services.llm_service não existe (ImportError sempre disparado).
"""
import logging
import pytest


def test_fairness_guard_layer3_code_uses_error_not_warning():
    """Inspeção estática: logger.error para [LIA-FG-01], sem logger.warning."""
    path = "/home/runner/workspace/lia-agent-system/app/shared/compliance/fairness_guard.py"
    with open(path) as f:
        source = f.read()

    assert 'logger.error(' in source and 'LIA-FG-01' in source, (
        "FairnessGuard deve usar logger.error para [LIA-FG-01] quando Layer3 falha"
    )
    lines_with_fg01_warning = [
        (i + 1, line.strip())
        for i, line in enumerate(source.splitlines())
        if "LIA-FG-01" in line and "logger.warning" in line
    ]
    assert len(lines_with_fg01_warning) == 0, (
        f"Ainda há logger.warning para [LIA-FG-01]: {lines_with_fg01_warning}"
    )


def test_fairness_guard_layer3_sentry_capture_present():
    """Inspeção estática: sentry_sdk.capture_exception presente após o logger.error."""
    path = "/home/runner/workspace/lia-agent-system/app/shared/compliance/fairness_guard.py"
    with open(path) as f:
        source = f.read()

    assert "sentry_sdk.capture_exception(e)" in source, (
        "FairnessGuard deve incluir sentry_sdk.capture_exception após o logger.error da Layer3"
    )


@pytest.mark.asyncio
async def test_check_semantic_importerror_logs_error_and_does_not_block(caplog):
    """check_semantic tenta importar app.services.llm_service → ImportError sempre.
    Deve logar ERROR [LIA-FG-01] (não WARNING) e retornar resultado não bloqueado."""
    from app.shared.compliance.fairness_guard import FairnessGuard

    guard = FairnessGuard()

    # check_semantic é onde o ImportError de app.services.llm_service é capturado
    with caplog.at_level(logging.DEBUG, logger="app.shared.compliance.fairness_guard"):
        result = await guard.check_semantic("texto neutro sem bias")

    fg01_errors = [
        r for r in caplog.records
        if "LIA-FG-01" in r.getMessage() and r.levelno >= logging.ERROR
    ]
    fg01_warnings = [
        r for r in caplog.records
        if "LIA-FG-01" in r.getMessage() and r.levelno == logging.WARNING
    ]

    assert len(fg01_errors) > 0, (
        f"check_semantic deve logar ERROR [LIA-FG-01] quando ImportError. "
        f"Logs capturados: {[(r.levelname, r.getMessage()) for r in caplog.records]}"
    )
    assert len(fg01_warnings) == 0, (
        f"Não deve haver WARNING [LIA-FG-01] após o fix: {[r.getMessage() for r in fg01_warnings]}"
    )
    assert not result.is_blocked, "Texto neutro não deve ser bloqueado após ImportError"
