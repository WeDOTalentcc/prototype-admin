"""TDD — WSI close_panel after approval (registrado 2026-06-12).

Pina o invariante: após approve_wsi_questions bem-sucedido, o handler emite
``ui_action: close_panel`` via SSE sink para fechar o painel lateral WSI.

Invariantes:
  1. Aprovação bem-sucedida emite ui_action=close_panel via SSE sink.
  2. Rejeição (gate de mínimo) NÃO emite close_panel.
  3. Sem questions NÃO emite close_panel.
  4. SSE sink ausente (ContextVar default=None) não levanta exceção — best-effort.

Listener FE: useUIAction.ts case "close_panel" -> dispatchEvent("lia:close_panel")
-> lia-float-context.tsx handleClosePanel -> closeDynamicPanel().
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

import pytest

from app.domains.job_creation.orchestrator.wizard_service_tools import (
    _handle_approve_wsi_questions,
)
from app.domains.job_creation.orchestrator.wizard_tools import ToolContext
from lia_agents_core.streaming_callback import (
    reset_sse_frame_sink,
    set_sse_frame_sink,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _q(block: str) -> Dict[str, Any]:
    return {"id": None, "question": "Q?", "block": block}


def _state(n_tech: int, n_behav: int) -> Dict[str, Any]:
    qs = [_q("technical") for _ in range(n_tech)] + [
        _q("behavioral") for _ in range(n_behav)
    ]
    return {
        "wsi_questions": qs,
        "screening_mode": "compact",
        "seniority_resolved": "pleno",
    }


_CTX = ToolContext(company_id="11111111-1111-1111-1111-111111111111")


# ---------------------------------------------------------------------------
# 1. Aprovação bem-sucedida emite ui_action=close_panel via SSE sink
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_approve_emits_close_panel_via_sse_sink():
    """Após approve bem-sucedido, SSE sink recebe frame com ui_action=close_panel."""
    received_frames: List[Dict[str, Any]] = []

    async def _sink(frame: dict) -> None:
        received_frames.append(frame)

    # Registrar o sink no ContextVar (padrão canonical)
    tok = set_sse_frame_sink(_sink)
    try:
        res = _handle_approve_wsi_questions(_state(5, 2), {}, _CTX)
        # O handler usa run_coroutine_threadsafe (loop running) -> aguardar a coro
        await asyncio.sleep(0.05)
    finally:
        reset_sse_frame_sink(tok)

    # Gate passou -> resultado OK
    assert res.error is False
    assert res.state_updates.get("questions_approved") is True

    # SSE sink recebeu frame com ui_action=close_panel
    assert len(received_frames) >= 1, "SSE sink nao recebeu nenhum frame"
    close_frames = [f for f in received_frames if f.get("ui_action") == "close_panel"]
    assert len(close_frames) >= 1, (
        f"Nenhum frame com ui_action=close_panel. Frames recebidos: {received_frames}"
    )


# ---------------------------------------------------------------------------
# 2. Rejeição (gate mínimo) NÃO emite close_panel
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_reject_does_not_emit_close_panel():
    """Quando o gate de mínimo bloqueia a aprovação, SSE sink NAO emite close_panel."""
    received_frames: List[Dict[str, Any]] = []

    async def _sink(frame: dict) -> None:
        received_frames.append(frame)

    tok = set_sse_frame_sink(_sink)
    try:
        res = _handle_approve_wsi_questions(_state(3, 0), {}, _CTX)
        await asyncio.sleep(0.05)
    finally:
        reset_sse_frame_sink(tok)

    assert res.error is True
    close_frames = [f for f in received_frames if f.get("ui_action") == "close_panel"]
    assert len(close_frames) == 0, (
        "close_panel nao deve ser emitido em caso de rejeicao"
    )


# ---------------------------------------------------------------------------
# 3. Sem questions NÃO emite close_panel
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_no_questions_does_not_emit_close_panel():
    """Quando nao ha perguntas, SSE sink NAO emite close_panel."""
    received_frames: List[Dict[str, Any]] = []

    async def _sink(frame: dict) -> None:
        received_frames.append(frame)

    tok = set_sse_frame_sink(_sink)
    try:
        res = _handle_approve_wsi_questions({"wsi_questions": []}, {}, _CTX)
        await asyncio.sleep(0.05)
    finally:
        reset_sse_frame_sink(tok)

    assert res.error is True
    close_frames = [f for f in received_frames if f.get("ui_action") == "close_panel"]
    assert len(close_frames) == 0


# ---------------------------------------------------------------------------
# 4. SSE sink ausente (ContextVar default=None) não levanta exceção
# ---------------------------------------------------------------------------
def test_approve_no_sink_does_not_raise():
    """SSE sink ausente: best-effort — nao bloqueia a aprovacao."""
    # Nao registrar nenhum sink; ContextVar permanece None (default)
    res = _handle_approve_wsi_questions(_state(5, 2), {}, _CTX)
    assert res.error is False
    assert res.state_updates.get("questions_approved") is True


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
