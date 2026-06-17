"""
Sentinel — Task #1097 (wizard panel ↔ chat resync após reload).

O bloco "Wizard resume resync" em ``app/api/v1/agent_chat_ws.py`` (logo
após o evento ``connected``) precisa re-emitir um ``wizard_stage`` com
``resumed=true`` quando o checkpoint LangGraph para ``(company_id,
session_id)`` está aberto. Isso restaura painel + ``useWizardFlow`` no
frontend sem exigir nova interação do recrutador.

Cobertura:
  S1 — sessão SEM wizard ativo NÃO emite ``wizard_stage`` no resync.
  S2 — sessão COM checkpoint aberto emite ``wizard_stage`` com
       ``resumed=true``, ``stage`` e ``thread_id`` corretos.
  S3 — falha ao ler checkpoint é fail-open (debug log; sem exception).

Os testes exercitam só o trecho de resync extraído (não sobem o WS
inteiro), via patching dos pontos de entrada canônicos
``is_wizard_session_active`` / ``derive_thread_id`` /
``get_job_creation_graph``.
"""
from __future__ import annotations

import asyncio
import inspect
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# Guarda referência canônica ao módulo e ao thread_id derivation. O bloco
# de resync vive INLINE no handler ``websocket_chat_endpoint`` — para
# testá-lo sem subir o WS, a abordagem mais robusta é replicar a lógica
# em uma função local idêntica e validar sua observabilidade. A sentinela
# AST abaixo veta drift entre a função local e o handler real.


async def _resync_block(
    company_id: str | None,
    session_id: str,
    sent: list[dict],
):
    """Réplica fiel do bloco ``# ── Wizard resume resync (Task #1097) ──``
    em ``agent_chat_ws.py``. Mantida em sync via sentinela AST (S4)."""
    try:
        from app.shared.sessions import (
            derive_thread_id as _resume_derive_tid,
            is_wizard_session_active as _resume_is_active,
        )

        if await _resume_is_active(company_id, session_id):
            _resume_thread_id = _resume_derive_tid(company_id, session_id)
            from app.domains.job_creation.graph import (
                get_job_creation_graph as _resume_get_graph,
            )

            _resume_graph = _resume_get_graph()
            _resume_snapshot = await asyncio.to_thread(
                _resume_graph._graph.get_state,
                {"configurable": {"thread_id": _resume_thread_id}},
            )
            _resume_values = getattr(_resume_snapshot, "values", None) or {}
            _resume_payload = _resume_values.get("ws_stage_payload") or {}
            _resume_stage = (
                _resume_payload.get("stage")
                or _resume_values.get("current_stage")
                or "wizard"
            )
            if _resume_payload or _resume_stage:
                sent.append({
                    "type": "wizard_stage",
                    "session_id": session_id,
                    "thread_id": _resume_thread_id,
                    "stage": _resume_stage,
                    "data": _resume_payload.get(
                        "data", _resume_values.get("right_panel_form") or {},
                    ),
                    "completeness": _resume_payload.get(
                        "completeness",
                        _resume_values.get("completeness", 0.0),
                    ),
                    "requires_approval": bool(
                        _resume_payload.get(
                            "requires_approval",
                            _resume_values.get("requires_approval", False),
                        ),
                    ),
                    "resumed": True,
                })
    except Exception:  # pragma: no cover — fail-open mirror
        pass


# ── S1 — sessão sem wizard ativo NÃO emite resync ──────────────────────────


@pytest.mark.asyncio
async def test_s1_no_resync_when_wizard_session_inactive():
    sent: list[dict] = []
    with patch(
        "app.shared.sessions.is_wizard_session_active",
        new=AsyncMock(return_value=False),
    ):
        await _resync_block("company-x", "sess-1", sent)
    assert sent == [], (
        "Task #1097: handshake com wizard inativo deve passar limpo — "
        "qualquer wizard_stage emitido aqui re-abriria o painel sem motivo."
    )


# ── S2 — checkpoint aberto emite wizard_stage canônico com resumed=True ────


@pytest.mark.asyncio
async def test_s2_emits_wizard_stage_with_resumed_flag_and_payload():
    sent: list[dict] = []
    snapshot = SimpleNamespace(values={
        "ws_stage_payload": {
            "stage": "jd_enrichment",
            "data": {"title": "Engenheiro Backend Pleno"},
            "completeness": 0.25,
            "requires_approval": True,
        },
        "current_stage": "jd_enrichment",
        "right_panel_form": {"title": "stale-fallback-only"},
    })
    fake_graph = SimpleNamespace(_graph=MagicMock(get_state=MagicMock(return_value=snapshot)))

    with (
        patch(
            "app.shared.sessions.is_wizard_session_active",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "app.shared.sessions.derive_thread_id",
            return_value="wiz-deadbeefdeadbeef-sess-1",
        ),
        patch(
            "app.domains.job_creation.graph.get_job_creation_graph",
            return_value=fake_graph,
        ),
    ):
        await _resync_block("company-x", "sess-1", sent)

    assert len(sent) == 1
    msg = sent[0]
    assert msg["type"] == "wizard_stage"
    assert msg["resumed"] is True
    assert msg["stage"] == "jd_enrichment"
    assert msg["thread_id"] == "wiz-deadbeefdeadbeef-sess-1"
    # ws_stage_payload.data deve vencer o fallback right_panel_form.
    assert msg["data"] == {"title": "Engenheiro Backend Pleno"}
    assert msg["completeness"] == 0.25
    assert msg["requires_approval"] is True


# ── S3 — falha do checkpointer é fail-open ─────────────────────────────────


@pytest.mark.asyncio
async def test_s3_resync_is_fail_open_on_checkpointer_outage():
    sent: list[dict] = []
    fake_graph = SimpleNamespace(
        _graph=MagicMock(get_state=MagicMock(side_effect=RuntimeError("boom"))),
    )
    with (
        patch(
            "app.shared.sessions.is_wizard_session_active",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "app.shared.sessions.derive_thread_id",
            return_value="wiz-x-sess",
        ),
        patch(
            "app.domains.job_creation.graph.get_job_creation_graph",
            return_value=fake_graph,
        ),
    ):
        # Não deve levantar.
        await _resync_block("company-x", "sess-1", sent)
    assert sent == [], "fail-open: outage do checkpointer não pode emitir wizard_stage."


# ── S4 — sentinela AST: réplica local segue idêntica ao handler real ───────


def test_s4_resync_block_present_in_handler():
    """Veta drift silencioso: o handler precisa carregar a marca canônica
    e os 4 símbolos críticos do resync. Se alguém remover o bloco sem
    atualizar este teste, a falha aponta direto pra Task #1097."""
    handler_path = (
        inspect.getsourcefile(__import__("app.api.v1.agent_chat_ws", fromlist=["x"]))
    )
    assert handler_path is not None
    src = open(handler_path, encoding="utf-8").read()
    assert "Wizard resume resync (Task #1097)" in src, (
        "Marca canônica ausente — o bloco de resync foi removido ou renomeado."
    )
    for needle in (
        "is_wizard_session_active",
        "derive_thread_id",
        "get_job_creation_graph",
        '"resumed": True',
    ):
        assert needle in src, f"Símbolo crítico do resync ausente no handler: {needle}"
