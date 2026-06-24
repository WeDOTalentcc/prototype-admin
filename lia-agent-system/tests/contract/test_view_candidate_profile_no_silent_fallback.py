"""Contract test — _wrap_view_candidate_profile NÃO pode mascarar falha (REGRA 4).

Descoberto 2026-06-05: quando get_full_profile lançava SQL error, o wrapper
engolia via `try/except: logger.warning(...)` e retornava
`{success: True, data: {profile_loaded: False}}` — perfil VAZIO reportado como
sucesso. Viola REGRA 4 (silent fallback em path crítico mascara falha).

Fix canonical (Opção A/B da REGRA 4): em erro de carregamento, retornar
`success: False` + `needs_manual_review: True` + `error` explícito.

Estes testes são unit (mock) e complementam o teste de DB real em
tests/integration/test_candidate_full_profile_db.py. Mock pega o contrato do
consumidor; DB real pega o defeito de SQL do produtor.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


def _patches(mock_repo):
    mock_db = AsyncMock()
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=None)
    return (
        patch(
            "app.domains.recruiter_assistant.agents.talent_tool_registry.AsyncSessionLocal",
            return_value=mock_db,
        ),
        patch(
            "app.domains.recruiter_assistant.agents.talent_tool_registry.CandidateRepository",
            return_value=mock_repo,
        ),
    )


async def test_db_error_is_not_masked_as_success():
    """Erro no produtor NÃO pode virar success=True com perfil vazio."""
    mock_repo = AsyncMock()
    mock_repo.get_full_profile = AsyncMock(
        side_effect=Exception('column "start_year" does not exist')
    )
    p_db, p_repo = _patches(mock_repo)
    with p_db, p_repo:
        from app.domains.recruiter_assistant.agents.talent_tool_registry import (
            _wrap_view_candidate_profile,
        )

        result = await _wrap_view_candidate_profile(
            company_id="company-abc",
            candidate_id="cand-123",
        )

    # REGRA 4: falha explícita, não success silencioso.
    assert result["success"] is False
    assert result["data"].get("profile_loaded") is not True
    assert result["data"].get("needs_manual_review") is True
    assert result["data"].get("error"), "erro deve ser propagado explicitamente"


async def test_valid_profile_still_returns_success():
    """Caminho feliz preservado: perfil carregado → success=True."""
    mock_repo = AsyncMock()
    mock_repo.get_full_profile = AsyncMock(
        return_value={
            "candidate_id": "cand-123",
            "name": "Larissa Nascimento",
            "education": [{"institution": "UFSC", "period": "1997-02 - 2001-12"}],
            "work_history": [],
            "profile_loaded": True,
        }
    )
    p_db, p_repo = _patches(mock_repo)
    with p_db, p_repo:
        from app.domains.recruiter_assistant.agents.talent_tool_registry import (
            _wrap_view_candidate_profile,
        )

        result = await _wrap_view_candidate_profile(
            company_id="company-abc",
            candidate_id="cand-123",
        )

    assert result["success"] is True
    assert result["data"]["profile_loaded"] is True
    assert result["data"]["name"] == "Larissa Nascimento"


async def test_not_found_still_returns_explicit_not_found():
    """Candidato inexistente → success=False com mensagem 'nao encontrado'."""
    mock_repo = AsyncMock()
    mock_repo.get_full_profile = AsyncMock(return_value=None)
    p_db, p_repo = _patches(mock_repo)
    with p_db, p_repo:
        from app.domains.recruiter_assistant.agents.talent_tool_registry import (
            _wrap_view_candidate_profile,
        )

        result = await _wrap_view_candidate_profile(
            company_id="company-abc",
            candidate_id="nonexistent-id",
        )

    assert result["success"] is False
    assert "nao encontrado" in result["message"]


def test_producer_sql_uses_real_education_columns():
    """Sensor estático barato: o produtor não pode reintroduzir colunas legadas.

    Roda sem DB — pega regressão de copy-paste em qualquer ambiente.
    """
    import inspect

    from app.domains.candidates.repositories.candidate_repository import (
        CandidateRepository,
    )

    src = inspect.getsource(CandidateRepository.get_full_profile)
    # Colunas reais de candidate_education (information_schema 2026-06-05).
    assert "start_date" in src
    assert "end_date" in src
    assert "is_completed" in src
    # Colunas que NÃO existem no schema — não podem voltar.
    assert "start_year" not in src, "coluna inexistente reintroduzida"
    assert "end_year" not in src, "coluna inexistente reintroduzida"
    assert "is_current" not in src, "coluna inexistente reintroduzida"
