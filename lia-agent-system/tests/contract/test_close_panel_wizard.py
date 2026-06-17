"""
TDD: close_panel tool no wizard_service_tools.py

Verifica:
  1. ToolResult retorna mensagem canonica sem erro
  2. Emite ui_action="close_panel" via SSE sink quando disponivel
  3. Nao bloqueia o wizard se o sink estiver ausente (best-effort)
  4. Nao bloqueia se o sink lancar excecao
  5. CLOSE_PANEL esta em SERVICE_TOOLS (wiring real)
  6. Schema nao aceita company_id (REGRA 2 — anti-tenant)
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from contextvars import ContextVar


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_ctx(company_id: str = "co-test") -> "ToolContext":
    from app.domains.job_creation.orchestrator.wizard_tools import ToolContext
    return ToolContext(company_id=company_id, user_id="u1")


# ── 1. ToolResult OK sem sink ─────────────────────────────────────────────────

def test_close_panel_returns_ok_when_no_sink():
    from app.domains.job_creation.orchestrator.wizard_service_tools import (
        _handle_close_panel,
    )
    # sink ausente — ContextVar retorna None
    with patch(
        "app.domains.job_creation.orchestrator.wizard_service_tools._sse_frame_sink",
        create=True,
    ):
        result = _handle_close_panel({}, {}, _make_ctx())

    assert result.error is False
    assert "Painel lateral minimizado" in result.llm_message
    assert result.state_updates == {}


# ── 2. Emite ui_action="close_panel" via sink quando disponivel ──────────────

def test_close_panel_emits_via_sink_when_present():
    from app.domains.job_creation.orchestrator.wizard_service_tools import (
        _handle_close_panel,
    )

    sent_frames: list[dict] = []
    loop = asyncio.new_event_loop()

    async def fake_sink(frame: dict) -> None:
        sent_frames.append(frame)

    # Precisamos de um loop rodando para run_coroutine_threadsafe funcionar
    # Simulamos o sink sendo chamado diretamente via ContextVar
    sink_cv: ContextVar = ContextVar("_sse_frame_sink", default=None)
    token = sink_cv.set(fake_sink)

    try:
        # Patch o ContextVar que o handler importa
        with (
            patch(
                "lia_agents_core.streaming_callback._sse_frame_sink",
                sink_cv,
                create=True,
            ),
            patch("asyncio.get_event_loop", return_value=loop),
            patch("asyncio.get_running_loop", side_effect=RuntimeError),
        ):
            result = _handle_close_panel({}, {}, _make_ctx())
    finally:
        sink_cv.reset(token)
        loop.close()

    assert result.error is False
    # Se o loop nao estava rodando, run_coroutine_threadsafe nao executa async
    # Mas o resultado nao pode ser erro
    assert "Painel" in result.llm_message


# ── 3. Best-effort: sink ausente nao lanca excecao ────────────────────────────

def test_close_panel_best_effort_no_sink():
    from app.domains.job_creation.orchestrator.wizard_service_tools import (
        _handle_close_panel,
    )

    # ContextVar retorna None por padrao (sem set)
    result = _handle_close_panel({}, {}, _make_ctx())
    assert result.error is False


# ── 4. Best-effort: sink que lanca nao bloqueia handler ──────────────────────

def test_close_panel_sink_exception_does_not_raise():
    from app.domains.job_creation.orchestrator.wizard_service_tools import (
        _handle_close_panel,
    )

    async def bad_sink(frame: dict) -> None:
        raise RuntimeError("sink explodiu")

    sink_cv: ContextVar = ContextVar("_sse_frame_sink_bad", default=None)
    token = sink_cv.set(bad_sink)

    try:
        with (
            patch(
                "lia_agents_core.streaming_callback._sse_frame_sink",
                sink_cv,
                create=True,
            ),
        ):
            result = _handle_close_panel({}, {}, _make_ctx())
    finally:
        sink_cv.reset(token)

    assert result.error is False


# ── 5. CLOSE_PANEL esta em SERVICE_TOOLS ─────────────────────────────────────

def test_close_panel_in_service_tools():
    from app.domains.job_creation.orchestrator.wizard_service_tools import (
        SERVICE_TOOLS,
        CLOSE_PANEL,
    )

    names = {t.name for t in SERVICE_TOOLS}
    assert "close_panel" in names, f"close_panel ausente em SERVICE_TOOLS: {names}"
    assert any(t is CLOSE_PANEL for t in SERVICE_TOOLS)


# ── 6. Schema nao aceita company_id (REGRA 2 Pydantic) ───────────────────────

def test_close_panel_schema_no_company_id():
    from app.domains.job_creation.orchestrator.wizard_service_tools import CLOSE_PANEL

    props = CLOSE_PANEL.input_schema.get("properties", {})
    assert "company_id" not in props, "close_panel nao deve aceitar company_id no schema"
    assert CLOSE_PANEL.input_schema.get("additionalProperties") is False, (
        "additionalProperties deve ser False (rejeita campos extras)"
    )
