"""Contract/regression test — CandidateRepository.get_full_profile (real DB).

Pega a classe de bug descoberta 2026-06-05: a subquery de `candidate_education`
referenciava colunas inexistentes (`start_year`, `end_year`, `is_current`) em vez
das colunas reais (`start_date`, `end_date`, `is_completed`). O erro era ENGOLIDO
por um `try/except` silencioso no consumidor (`_wrap_view_candidate_profile`), que
retornava perfil VAZIO com success=True (REGRA 4 — silent fallback proibido).

Mocks NUNCA pegam esse defeito (não executam SQL) — ver memória
[[harness_sqlalchemy_text_jsonb_cast_asyncpg]]. Por isso este teste roda contra
DB real (skip se DATABASE_URL ausente), espelhando tests/integration/test_parecer_roundtrip_db.py.
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not available",
)

# Company de seed conhecida do ambiente dev (mesma usada na auditoria).
_SEED_COMPANY = "00000000-0000-4000-a000-000000000001"


async def _find_candidate_with_education(db):
    """Descobre (read-only) um candidato real com >= 1 registro de education."""
    from sqlalchemy import text as sa_text

    row = await db.execute(
        sa_text(
            """
            SELECT c.id, c.company_id
            FROM candidates c
            WHERE EXISTS (
                SELECT 1 FROM candidate_education e WHERE e.candidate_id = c.id
            )
            LIMIT 1
            """
        )
    )
    return row.mappings().first()


async def test_get_full_profile_loads_education_without_sql_error():
    """RED→GREEN: get_full_profile NÃO pode lançar SQL error e DEVE carregar education.

    Antes do fix: ProgrammingError 'column "start_year" does not exist'.
    """
    from app.core.database import AsyncSessionLocal
    from app.domains.candidates.repositories.candidate_repository import (
        CandidateRepository,
    )

    async with AsyncSessionLocal() as db:
        seed = await _find_candidate_with_education(db)
        if not seed:
            pytest.skip("Nenhum candidato com education no banco de dev")

        repo = CandidateRepository(db)
        # Não deve levantar — antes do fix levantava ProgrammingError.
        data = await repo.get_full_profile(
            candidate_id=str(seed["id"]),
            company_id=str(seed["company_id"]),
        )

    assert data is not None, "perfil não carregou (candidato existe)"
    assert data["profile_loaded"] is True
    # O candidato tem registros de education no banco → a lista não pode vir vazia.
    assert isinstance(data["education"], list)
    assert len(data["education"]) >= 1, (
        "education veio vazio apesar de existir registro — "
        "subquery candidate_education provavelmente quebrou de novo"
    )
    edu = data["education"][0]
    assert "institution" in edu and "period" in edu
    # period deriva de start_date/end_date/is_completed (colunas reais).
    assert " - " in edu["period"]
