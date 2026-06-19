"""
R5 — SEV2-C3-05: _batch_move_candidates deve ser fail-closed quando company_id ausente.

TDD RED — prova do defeito (antes do fix):
  T-R5-a: com company_id=None a função chama db.execute() SEM filtro de tenant
           (db.execute.call_count > 0 → cross-tenant latente).
  T-R5-b: com company_id válido db.execute é chamado (não-regressão baseline).

TDD GREEN (após fix):
  T-R5-a: com company_id=None a função retorna ActionResult(error) SEM chamar db.execute
           (fail-closed antes do banco).
  T-R5-b: com company_id válido db.execute continua sendo chamado (P-DETERMINISM).

Princípio: P-TENANT — company_id obrigatório, silent-skip proibido.
Raiz: R5 · SEV2-C3-05 · candidate_actions.py::_batch_move_candidates.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# IDs válidos (UUIDs) para evitar erros de formato mascarando o bug de tenant
_VALID_CAND = str(uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"))
_VALID_CO   = "co-ffff-0001-0002-0003-000000000004"
_VALID_STAGE = "entrevista"


# ─── Mock helpers ─────────────────────────────────────────────────────────────

def _make_db(rowcount: int = 1):
    db = MagicMock()
    result_mock = MagicMock()
    result_mock.rowcount = rowcount
    db.execute = AsyncMock(return_value=result_mock)
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


def _make_session_cm(db):
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=db)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


# ─── T-R5-a: RED — fail-closed com company_id ausente ────────────────────────

@pytest.mark.asyncio
async def test_none_company_id_does_not_call_execute():
    """
    RED: com company_id=None a função chama db.execute() SEM filtro de tenant
         (db.execute.call_count > 0 — cross-tenant latente).
         Prova: assert call_count == 0 FALHA → RED.

    GREEN: função retorna ActionResult(error) ANTES do db.execute
           (db.execute.call_count == 0 — fail-closed).
    """
    from app.orchestrator.action_handlers.candidate_actions import _batch_move_candidates

    db = _make_db()
    cm = _make_session_cm(db)

    with patch("app.core.database.AsyncSessionLocal", return_value=cm),          patch("app.orchestrator.action_handlers._handler_hooks.log_action_audit",
               new_callable=AsyncMock):
        result = await _batch_move_candidates(
            params={"candidate_ids": [_VALID_CAND], "to_stage": _VALID_STAGE},
            context={"company_id": None},
        )

    # ── RED assertion: db.execute NÃO deve ter sido chamado (fail-closed) ──
    assert db.execute.call_count == 0, (
        f"[RED] db.execute foi chamado {db.execute.call_count}× com company_id=None "
        f"— cross-tenant latente (SEV2-C3-05). "
        "Após fix, a função deve recusar ANTES do banco (fail-closed P-TENANT)."
    )
    # ── E resultado deve ser ActionResult(error) ──
    assert result is not None, "[RED] retornou None em vez de ActionResult(error)"
    assert result.status == "error"
    assert "company_id" in (result.error_detail or "").lower() or            "tenant" in (result.error_detail or "").lower(), (
        f"error_detail deve mencionar company_id/tenant, got: {result.error_detail!r}"
    )


@pytest.mark.asyncio
async def test_empty_string_company_id_does_not_call_execute():
    """
    Variante: company_id="" é falsy → mesmo bug → fail-closed esperado.
    """
    from app.orchestrator.action_handlers.candidate_actions import _batch_move_candidates

    db = _make_db()
    cm = _make_session_cm(db)

    with patch("app.core.database.AsyncSessionLocal", return_value=cm),          patch("app.orchestrator.action_handlers._handler_hooks.log_action_audit",
               new_callable=AsyncMock):
        result = await _batch_move_candidates(
            params={"candidate_ids": [_VALID_CAND], "to_stage": _VALID_STAGE},
            context={"company_id": ""},
        )

    assert db.execute.call_count == 0, (
        f"[RED] db.execute chamado {db.execute.call_count}× com company_id= — "
        "string vazia deve ser tratada como ausente (fail-closed)."
    )
    assert result is not None and result.status == "error"


@pytest.mark.asyncio
async def test_none_context_does_not_call_execute():
    """
    Variante: context=None → company_id indisponível → fail-closed.
    """
    from app.orchestrator.action_handlers.candidate_actions import _batch_move_candidates

    db = _make_db()
    cm = _make_session_cm(db)

    with patch("app.core.database.AsyncSessionLocal", return_value=cm),          patch("app.orchestrator.action_handlers._handler_hooks.log_action_audit",
               new_callable=AsyncMock):
        result = await _batch_move_candidates(
            params={"candidate_ids": [_VALID_CAND], "to_stage": _VALID_STAGE},
            context=None,
        )

    assert db.execute.call_count == 0, (
        f"[RED] db.execute chamado {db.execute.call_count}× com context=None — "
        "deve recusar antes do banco."
    )
    assert result is not None and result.status == "error"


# ─── T-R5-b: non-regression com company_id válido ────────────────────────────

@pytest.mark.asyncio
async def test_valid_company_id_calls_execute():
    """
    Non-regression (GREEN from start): com company_id válido db.execute é chamado.
    Valida P-DETERMINISM: comportamento normal não é afetado pelo fail-closed guard.
    """
    from app.orchestrator.action_handlers.candidate_actions import _batch_move_candidates

    db = _make_db(rowcount=1)
    cm = _make_session_cm(db)

    with patch("app.core.database.AsyncSessionLocal", return_value=cm),          patch("app.orchestrator.action_handlers._handler_hooks.log_action_audit",
               new_callable=AsyncMock):
        result = await _batch_move_candidates(
            params={"candidate_ids": [_VALID_CAND], "to_stage": _VALID_STAGE},
            context={"company_id": _VALID_CO},
        )

    assert db.execute.call_count >= 1, (
        "Com company_id válido, db.execute deve ser chamado (transição executa normalmente)."
    )
