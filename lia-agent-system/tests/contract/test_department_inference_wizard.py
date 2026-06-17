"""T11 — Inferencia de departamento pelo titulo no wizard (SERVICE_TOOL).

Testa o handler ``_handle_infer_department`` que faz fuzzy match do titulo
contra os departamentos REAIS da empresa via DepartmentRepository.

5 cenarios:
  1. Match bem-sucedido (Diretor Juridico -> Juridico)
  2. Sem match (titulo generico -> lista departamentos)
  3. Departamento ja definido -> skip
  4. Titulo nao definido -> erro
  5. Empresa sem departamentos -> orientacao
"""
from __future__ import annotations

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.job_creation.orchestrator.wizard_tools import ToolContext, ToolResult


# ── Helpers ──────────────────────────────────────────────────────────────

def _make_ctx(company_id: str = "11111111-1111-1111-1111-111111111111") -> ToolContext:
    return ToolContext(company_id=company_id, user_id="u1")


def _make_dept(name: str) -> MagicMock:
    d = MagicMock()
    d.name = name
    return d


def _import_handler():
    from app.domains.job_creation.orchestrator.wizard_service_tools import (
        _handle_infer_department,
    )
    return _handle_infer_department


def _run_handler_with_depts(state, ctx, depts):
    """Run handler with mocked DB that returns given department list."""
    handler = _import_handler()

    # The handler does lazy imports inside a try block:
    #   from async_audit import run_coro_in_threadpool
    #   from app.core.database import AsyncSessionLocal
    #   from department_repository import DepartmentRepository
    # Then calls run_coro_in_threadpool(lambda: _fetch_departments(), timeout=5)
    # where _fetch_departments is an async fn that uses AsyncSessionLocal + repo.
    #
    # We patch run_coro_in_threadpool to return depts directly, bypassing DB.
    with patch(
        "app.domains.job_creation.helpers.async_audit.run_coro_in_threadpool",
        side_effect=lambda fn, **kw: depts,
    ):
        return handler(state, {}, ctx)


# ── Tests ────────────────────────────────────────────────────────────────

def test_successful_match():
    """Diretor Juridico against departments including Juridico -> matches."""
    state = {"parsed_title": "Diretor Juridico"}
    ctx = _make_ctx()
    depts = [_make_dept("Comercial"), _make_dept("Juridico"), _make_dept("RH")]

    result = _run_handler_with_depts(state, ctx, depts)

    assert isinstance(result, ToolResult)
    assert not result.error
    assert result.state_updates
    assert result.state_updates.get("parsed_department") == "Juridico"
    assert "Juridico" in result.llm_message


def test_no_match_lists_departments():
    """Title that does not match any department -> returns department list."""
    state = {"parsed_title": "Astronauta Espacial"}
    ctx = _make_ctx()
    depts = [_make_dept("Comercial"), _make_dept("Juridico"), _make_dept("RH")]

    result = _run_handler_with_depts(state, ctx, depts)

    assert isinstance(result, ToolResult)
    assert not result.error
    assert result.state_updates is None or "parsed_department" not in (result.state_updates or {})
    assert "Comercial" in result.llm_message
    assert "Pergunte" in result.llm_message


def test_department_already_set_skips():
    """If department is already set, handler skips inference."""
    handler = _import_handler()
    state = {"parsed_title": "Diretor Juridico", "parsed_department": "Financeiro"}
    ctx = _make_ctx()

    # No DB mock needed — handler returns early
    result = handler(state, {}, ctx)

    assert isinstance(result, ToolResult)
    assert not result.error
    assert "Financeiro" in result.llm_message
    assert result.state_updates is None or "parsed_department" not in (result.state_updates or {})


def test_no_title_returns_error():
    """No title set -> error telling to define title first."""
    handler = _import_handler()
    state = {}
    ctx = _make_ctx()

    result = handler(state, {}, ctx)

    assert isinstance(result, ToolResult)
    assert result.error
    assert "titulo" in result.llm_message.lower()


def test_empty_departments_list():
    """Company has no departments -> orientation message."""
    state = {"parsed_title": "Analista Financeiro"}
    ctx = _make_ctx()

    result = _run_handler_with_depts(state, ctx, [])

    assert isinstance(result, ToolResult)
    assert not result.error
    assert "departamentos" in result.llm_message.lower()
