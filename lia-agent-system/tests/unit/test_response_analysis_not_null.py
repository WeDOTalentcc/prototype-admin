"""Sensor — insert_response_analysis_full preenche as colunas NOT NULL.

Pina o fix do bug stale: candidate_id, job_vacancy_id e response_hash são
NOT NULL em wsi_response_analyses e antes eram OMITIDOS pelo método do repo
(insert falhava silenciosamente em produção — candidato real ficava sem
respostas por-competência no modal de triagem).

Captura os params executados via db mockado (sem DB real) e garante que as 3
colunas chegam preenchidas. response_hash é derivado de response_text quando
não informado.
"""
import hashlib

import pytest

from app.domains.voice.repositories.wsi_repository import WsiRepository


class _FakeResult:
    pass


class _CapturingDB:
    """AsyncSession mínima que captura (statement, params) do execute."""

    def __init__(self):
        self.calls = []

    async def execute(self, statement, params=None):
        self.calls.append((str(statement), params))
        return _FakeResult()


@pytest.mark.asyncio
async def test_insert_response_analysis_full_includes_not_null_cols():
    db = _CapturingDB()
    repo = WsiRepository(db)

    await repo.insert_response_analysis_full(
        analysis_id="11111111-1111-4111-8111-111111111111",
        session_id="22222222-2222-4222-8222-222222222222",
        question_id="33333333-3333-4333-8333-333333333333",
        candidate_id="44444444-4444-4444-8444-444444444444",
        job_vacancy_id="55555555-5555-4555-8555-555555555555",
        competency="comunicacao",
        response_text="resposta do candidato",
        autodeclaration_score=8.0,
        context_score=8.0,
        bloom_level=3,
        dreyfus_level=3,
        evidences_json="[]",
        red_flags_json="[]",
        consistency_penalty=0.0,
        final_score=8.0,
        justification="ok",
    )

    assert len(db.calls) == 1
    sql, params = db.calls[0]

    # NOT NULL: as 3 colunas que antes eram omitidas precisam estar no INSERT
    for col in ("candidate_id", "job_vacancy_id", "response_hash"):
        assert col in sql, f"coluna NOT NULL ausente do INSERT: {col}"
        assert params.get(col), f"param NOT NULL vazio/None: {col}"

    # response_hash derivado de response_text quando não informado
    assert params["response_hash"] == hashlib.md5(
        "resposta do candidato".encode("utf-8")
    ).hexdigest()

    # casts jsonb não usam o padrão quebrado :param::cast
    assert ":evidences::jsonb" not in sql
    assert "CAST(:evidences AS jsonb)" in sql


@pytest.mark.asyncio
async def test_insert_response_analysis_full_respects_explicit_hash():
    db = _CapturingDB()
    repo = WsiRepository(db)
    await repo.insert_response_analysis_full(
        analysis_id="11111111-1111-4111-8111-111111111111",
        session_id="22222222-2222-4222-8222-222222222222",
        question_id="33333333-3333-4333-8333-333333333333",
        candidate_id="44444444-4444-4444-8444-444444444444",
        job_vacancy_id="55555555-5555-4555-8555-555555555555",
        competency="comunicacao",
        response_text="x",
        autodeclaration_score=8.0,
        context_score=8.0,
        bloom_level=3,
        dreyfus_level=3,
        evidences_json="[]",
        red_flags_json="[]",
        consistency_penalty=0.0,
        final_score=8.0,
        justification="ok",
        response_hash="hash-explicito",
    )
    _, params = db.calls[0]
    assert params["response_hash"] == "hash-explicito"
