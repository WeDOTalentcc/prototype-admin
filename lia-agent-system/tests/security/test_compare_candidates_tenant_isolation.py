"""[#591/security] compare_candidates: cross-tenant IDOR defense.

Garante que a tool `compare_candidates`:
1. Recusa execucao quando nao ha company_id no contexto (fail-fast).
2. Nunca retorna registros de outro tenant, mesmo quando o caller tenta
   passar IDs de candidatos que pertencem a outra empresa.
3. Ignora company_id passado como parametro quando ha _context (caller
   nao consegue subir privilegio sobrescrevendo o tenant).
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.sourcing.tools.query_tools import compare_candidates


def _ctx(company_id: str | None) -> SimpleNamespace:
    return SimpleNamespace(company_id=company_id)


def test_compare_candidates_refuses_without_tenant_context() -> None:
    """Sem _context (ou com company_id vazio), a tool falha-fast."""
    res = asyncio.run(
        compare_candidates(
            candidate_ids=["11111111-1111-1111-1111-111111111111",
                           "22222222-2222-2222-2222-222222222222"],
        )
    )
    assert res["success"] is False
    assert res.get("error") == "missing_tenant_context"
    assert res["candidates"] == []


def test_compare_candidates_ignores_caller_supplied_company_id() -> None:
    """Mesmo com company_id explicito, prevalece o do _context."""
    captured: dict = {}

    class _StubResult:
        def mappings(self):
            class _M:
                def all(self_inner):
                    return []
            return _M()

    class _StubSession:
        async def __aenter__(self_inner):
            return self_inner
        async def __aexit__(self_inner, *a):
            return False
        async def execute(self_inner, sql, params):
            captured["sql"] = str(sql)
            captured["params"] = dict(params)
            return _StubResult()

    with patch(
        "app.core.database.AsyncSessionLocal",
        return_value=_StubSession(),
    ):
        res = asyncio.run(
            compare_candidates(
                candidate_ids=["aaaa", "bbbb"],
                company_id="ATTACKER_COMPANY",  # tenta sobrescrever
                _context=_ctx("REAL_TENANT"),
            )
        )

    assert "company_id = :_company_id" in captured["sql"], (
        "SQL nao filtra por company_id — IDOR cross-tenant possivel"
    )
    assert captured["params"]["_company_id"] == "REAL_TENANT", (
        f"Esperado company_id do contexto; obtido: {captured['params'].get('_company_id')!r}"
    )
    # mesmo que SQL retorne vazio (mock), a resposta deve ser estruturada.
    assert isinstance(res, dict)


def test_compare_candidates_other_tenant_ids_return_empty() -> None:
    """Passar IDs de outro tenant nao retorna nenhuma linha (WHERE company_id filtra)."""
    captured_params: dict = {}

    class _StubResult:
        def mappings(self):
            class _M:
                def all(self_inner):
                    # Simula DB real: WHERE id IN (...) AND company_id=:_company_id
                    # como o tenant nao bate, vem vazio.
                    return []
            return _M()

    class _StubSession:
        async def __aenter__(self_inner):
            return self_inner
        async def __aexit__(self_inner, *a):
            return False
        async def execute(self_inner, sql, params):
            captured_params.update(params)
            return _StubResult()

    with patch(
        "app.core.database.AsyncSessionLocal",
        return_value=_StubSession(),
    ):
        res = asyncio.run(
            compare_candidates(
                candidate_ids=[
                    "00000000-0000-0000-0000-000000000001",
                    "00000000-0000-0000-0000-000000000002",
                ],
                _context=_ctx("TENANT_A"),
            )
        )

    assert captured_params.get("_company_id") == "TENANT_A"
    assert res["success"] is False  # "Candidatos nao encontrados."
    assert res["candidates"] == []
