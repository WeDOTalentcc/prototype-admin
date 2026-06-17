"""F4: bug fix send_daily_digest TeamsProactivityEngine.

Bug: send_daily_digest chamava _find_stalled_pipelines(db, company_id)
     mas a assinatura correta é _find_stalled_pipelines(company_id, stalled_days=5).
     O db session era passado como company_id, descartando o company_id real.

Fix: corrigido para _find_stalled_pipelines(company_id).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db_mock():
    """Cria mock de AsyncSession com execute retornando scalar 0."""
    scalar_result = MagicMock()
    scalar_result.scalar.return_value = 0
    db = AsyncMock()
    db.execute = AsyncMock(return_value=scalar_result)
    return db


def _make_session_ctx(db_mock):
    """Cria context manager mock que retorna db_mock."""
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=db_mock)
    ctx.__aexit__ = AsyncMock(return_value=None)
    return ctx


# ---------------------------------------------------------------------------
# Test 1: assinatura de _find_stalled_pipelines não aceita db
# ---------------------------------------------------------------------------

def test_find_stalled_pipelines_signature_no_db_arg():
    """Confirmar que _find_stalled_pipelines aceita (company_id, stalled_days) sem db."""
    import inspect
    from app.domains.communication.services.teams_proactivity_engine import (
        TeamsProactivityEngine,
    )

    sig = inspect.signature(TeamsProactivityEngine._find_stalled_pipelines)
    params = list(sig.parameters.keys())

    assert "self" in params
    assert "company_id" in params
    assert "stalled_days" in params
    assert "db" not in params, (
        f"_find_stalled_pipelines NAO deve aceitar 'db'. Parametros: {params}"
    )


# ---------------------------------------------------------------------------
# Test 2: send_daily_digest chama _find_stalled_pipelines com company_id correto
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_daily_digest_passes_company_id_not_db():
    """O primeiro arg de _find_stalled_pipelines deve ser str, nao db session."""
    from app.domains.communication.services.teams_proactivity_engine import (
        TeamsProactivityEngine,
    )

    engine = TeamsProactivityEngine()
    captured_args = {}

    async def fake_find_stalled(company_id, stalled_days=5):
        captured_args["company_id"] = company_id
        captured_args["stalled_days"] = stalled_days
        return []

    db_mock = _make_db_mock()
    session_ctx = _make_session_ctx(db_mock)

    with patch.object(engine, "_find_stalled_pipelines", side_effect=fake_find_stalled), \
         patch.object(engine, "_get_recruiter_refs_for_vacancy", new_callable=AsyncMock, return_value=[]), \
         patch.object(engine, "_broadcast_card", new_callable=AsyncMock, return_value=False), \
         patch("app.core.database.AsyncSessionLocal", return_value=session_ctx):

        await engine.send_daily_digest("company-abc-123")

    assert "company_id" in captured_args, "_find_stalled_pipelines nao foi chamado"
    assert captured_args["company_id"] == "company-abc-123", (
        f"company_id errado: esperado 'company-abc-123', got {repr(captured_args['company_id'])}"
    )
    # Garantir que nao e um objeto db session
    assert isinstance(captured_args["company_id"], str), (
        f"company_id deveria ser str, got {type(captured_args['company_id'])}"
    )


# ---------------------------------------------------------------------------
# Test 3: send_daily_digest com company_id=None nao levanta excecao
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_daily_digest_with_none_company_id():
    """send_daily_digest(None) deve retornar int sem lancar excecao."""
    from app.domains.communication.services.teams_proactivity_engine import (
        TeamsProactivityEngine,
    )

    engine = TeamsProactivityEngine()

    db_mock = _make_db_mock()
    session_ctx = _make_session_ctx(db_mock)

    with patch.object(engine, "_find_stalled_pipelines", new_callable=AsyncMock, return_value=[]), \
         patch.object(engine, "_get_recruiter_refs_for_vacancy", new_callable=AsyncMock, return_value=[]), \
         patch.object(engine, "_broadcast_card", new_callable=AsyncMock, return_value=False), \
         patch("app.core.database.AsyncSessionLocal", return_value=session_ctx):

        result = await engine.send_daily_digest(None)

    assert isinstance(result, int), f"Deve retornar int, got {type(result)}"
