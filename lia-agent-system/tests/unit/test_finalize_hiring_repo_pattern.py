"""
TDD tests for G3: _wrap_finalize_hiring ADR-001 compliance.
Verifica que a função usa VacancyCandidateRepository em vez de SQL inline.
"""
import ast
import inspect
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


CANDIDATE_ID = str(uuid.uuid4())
COMPANY_ID = str(uuid.uuid4())


def _make_mock_vc(stage="Triagem", status="em_triagem"):
    vc = MagicMock()
    vc.stage = stage
    vc.status = status
    return vc


def _make_mock_candidate(name="João Silva"):
    c = MagicMock()
    c.name = name
    return c


@pytest.mark.asyncio
async def test_finalize_hiring_success():
    """Candidato encontrado → stage='Contratado', status='hired', response success."""
    from app.domains.cv_screening.agents.pipeline_tool_registry import _wrap_finalize_hiring

    mock_vc = _make_mock_vc()
    mock_candidate = _make_mock_candidate("Maria Oliveira")

    mock_repo = AsyncMock()
    mock_repo.get_most_recent_for_candidate = AsyncMock(return_value=mock_vc)
    mock_repo.update = AsyncMock(return_value=mock_vc)

    mock_candidate_repo = AsyncMock()
    mock_candidate_repo.get_by_id_str = AsyncMock(return_value=mock_candidate)

    mock_db = AsyncMock()
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "app.domains.cv_screening.agents.pipeline_tool_registry.AsyncSessionLocal",
        return_value=mock_db,
    ), patch(
        "app.domains.cv_screening.agents.pipeline_tool_registry.VacancyCandidateRepository",
        return_value=mock_repo,
    ), patch(
        "app.domains.cv_screening.agents.pipeline_tool_registry.CandidateRepository",
        return_value=mock_candidate_repo,
    ):
        result = await _wrap_finalize_hiring(
            candidate_id=CANDIDATE_ID,
            company_id=COMPANY_ID,
        )

    assert result["success"] is True
    assert result["data"]["new_status"] == "hired"
    assert result["data"]["new_stage"] == "Contratado"
    assert result["data"]["candidate_name"] == "Maria Oliveira"
    assert mock_vc.stage == "Contratado"
    assert mock_vc.status == "hired"
    mock_repo.update.assert_called_once_with(mock_vc)


@pytest.mark.asyncio
async def test_finalize_hiring_not_found():
    """get_most_recent_for_candidate retorna None → response success=False."""
    from app.domains.cv_screening.agents.pipeline_tool_registry import _wrap_finalize_hiring

    mock_repo = AsyncMock()
    mock_repo.get_most_recent_for_candidate = AsyncMock(return_value=None)

    mock_candidate_repo = AsyncMock()

    mock_db = AsyncMock()
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "app.domains.cv_screening.agents.pipeline_tool_registry.AsyncSessionLocal",
        return_value=mock_db,
    ), patch(
        "app.domains.cv_screening.agents.pipeline_tool_registry.VacancyCandidateRepository",
        return_value=mock_repo,
    ), patch(
        "app.domains.cv_screening.agents.pipeline_tool_registry.CandidateRepository",
        return_value=mock_candidate_repo,
    ):
        result = await _wrap_finalize_hiring(
            candidate_id=CANDIDATE_ID,
            company_id=COMPANY_ID,
        )

    assert result["success"] is False
    assert "não encontrado" in result["message"]


def test_finalize_hiring_no_sql_inline():
    """AST check: _wrap_finalize_hiring não contém SQL inline (UPDATE/SELECT vacancy_candidates)."""
    import app.domains.cv_screening.agents.pipeline_tool_registry as mod

    func = getattr(mod, "_wrap_finalize_hiring", None)
    assert func is not None

    # Use AST to check — get the source file and parse the function
    import inspect
    source = inspect.getsource(mod)

    # Parse AST to find string constants used in text() calls inside _wrap_finalize_hiring
    tree = ast.parse(source)

    sql_strings_in_func = []
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "_wrap_finalize_hiring":
            for inner in ast.walk(node):
                if isinstance(inner, ast.Constant) and isinstance(inner.s, str):
                    val = inner.s
                    if "UPDATE vacancy_candidates" in val or "SELECT vc.stage" in val:
                        sql_strings_in_func.append(val[:80])

    assert sql_strings_in_func == [], (
        f"_wrap_finalize_hiring ainda contém SQL inline — violação ADR-001: {sql_strings_in_func}"
    )

    # Verify VacancyCandidateRepository is referenced
    func_source = inspect.getsource(mod._wrap_finalize_hiring.__wrapped__ if hasattr(mod._wrap_finalize_hiring, "__wrapped__") else mod._wrap_finalize_hiring)
    assert "VacancyCandidateRepository" in func_source, (
        "_wrap_finalize_hiring deve usar VacancyCandidateRepository (ADR-001)"
    )

    # Verify new_status is 'hired' not 'contratado' — check via AST constants in function
    hired_found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "_wrap_finalize_hiring":
            for inner in ast.walk(node):
                if isinstance(inner, ast.Constant) and inner.s == "hired":
                    hired_found = True
                    break
    assert hired_found, "status 'hired' deve estar presente no return dict (VALID_STATUSES fix)"
