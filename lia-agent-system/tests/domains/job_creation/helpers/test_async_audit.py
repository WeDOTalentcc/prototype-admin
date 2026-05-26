"""Tests do helper async_audit (PR-4 foundation Onda 2).

Cobre:
- emit_audit_fire_and_forget: running loop, no loop, factory exception, inner coro exception
- run_coro_in_threadpool: running loop, no loop, exception propagation
"""
from __future__ import annotations

import asyncio
import logging

import pytest

from app.domains.job_creation.helpers.async_audit import (
    emit_audit_fire_and_forget,
    run_coro_in_threadpool,
)


# --- emit_audit_fire_and_forget --------------------------------------------


@pytest.mark.asyncio
async def test_emit_audit_fire_and_forget_running_loop_schedules_task():
    """Running loop: coro é agendada e executa sem bloquear."""
    called: list[str] = []

    async def audit_coro():
        called.append("audited")

    emit_audit_fire_and_forget(lambda: audit_coro())
    # Yield para a task rodar
    for _ in range(3):
        await asyncio.sleep(0)
    assert called == ["audited"]


def test_emit_audit_no_loop_skipped(caplog):
    """Sem loop ativo, skip silencioso com warning log."""

    async def audit_coro():
        raise AssertionError("should not run without loop")

    with caplog.at_level(logging.WARNING):
        emit_audit_fire_and_forget(lambda: audit_coro())
    assert any("no running loop" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_emit_audit_factory_exception_swallowed(caplog):
    """Factory que raise não quebra o node — log warning."""

    def factory():
        raise ValueError("factory broken")

    with caplog.at_level(logging.WARNING):
        emit_audit_fire_and_forget(factory)
    assert any("factory raised" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_emit_audit_inner_coro_exception_swallowed(caplog):
    """Exception dentro da coro é log-warned mas não propaga."""

    async def failing_coro():
        raise RuntimeError("audit DB down")

    with caplog.at_level(logging.WARNING):
        emit_audit_fire_and_forget(lambda: failing_coro())
        # Yield para a task rodar e a exception ser logada
        for _ in range(5):
            await asyncio.sleep(0)
    assert any("failed silently" in r.message for r in caplog.records)


# --- run_coro_in_threadpool ------------------------------------------------


@pytest.mark.asyncio
async def test_run_coro_in_threadpool_with_running_loop():
    """Running loop: usa ThreadPoolExecutor (não raise RuntimeError Py 3.12+)."""

    async def get_value():
        return 42

    result = run_coro_in_threadpool(lambda: get_value())
    assert result == 42


def test_run_coro_in_threadpool_no_loop():
    """Sem loop ativo, usa asyncio.run direto."""

    async def get_value():
        return "ok"

    result = run_coro_in_threadpool(lambda: get_value())
    assert result == "ok"


@pytest.mark.asyncio
async def test_run_coro_in_threadpool_propagates_coro_exception():
    """Exception dentro da coro propaga para o caller (não silent)."""

    async def failing():
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        run_coro_in_threadpool(lambda: failing())


@pytest.mark.asyncio
async def test_run_coro_in_threadpool_with_real_value():
    """Smoke test com dict typical (mimicking _apply_pipeline_template payload)."""

    async def fake_template_payload():
        return {"interview_stages": ["screening"], "template_name": "Default"}

    result = run_coro_in_threadpool(lambda: fake_template_payload())
    assert result == {"interview_stages": ["screening"], "template_name": "Default"}
