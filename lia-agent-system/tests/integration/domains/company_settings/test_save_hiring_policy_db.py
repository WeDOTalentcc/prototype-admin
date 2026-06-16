"""Integration test (Task #1009) — `save_hiring_policy` persiste corretamente
em `company_hiring_policies` via Postgres real (INSERT inicial + UPDATE com
merge JSON superficial).

Cobre o gap deixado pelo PR2 / Task #1002:
  * Unit (`tests/unit/domains/company_settings/test_save_hiring_policy.py`)
    valida apenas input/whitelist/mapeamento/FairnessGuard — não toca DB.
  * Golden eval + Playwright (PR7) cobrem o caminho LLM → tool no nível de
    prompt e UI, mas também não inspecionam o estado final no banco.

Este teste usa a fixture canônica do projeto (`AsyncSessionLocal` em
`lia_config.database`, apontada pelo `DATABASE_URL`) e exercita o caminho
SQL real (`:bind::json` cast + `NOW()`) — qualquer regressão na query
crua quebra aqui antes do merge.

Skip-graceful: se `DATABASE_URL` não estiver disponível ou a conexão
falhar (gate offline puro), pulamos com mensagem clara em vez de quebrar.
A tabela `company_hiring_policies` é criada via o helper canônico
`create_company_hiring_policies_table` e cada teste isola o tenant via
UUID v4 fresco + cleanup no teardown.
"""
from __future__ import annotations

import json
import os
import uuid
from types import SimpleNamespace

import pytest
from sqlalchemy import text


def _has_postgres() -> bool:
    url = os.environ.get("DATABASE_URL", "")
    return bool(url and "postgres" in url)


pytestmark = pytest.mark.skipif(
    not _has_postgres(),
    reason=(
        "Requer DATABASE_URL apontando pra Postgres (mesma fixture de "
        "tests/integration/agents/test_company_settings_no_regression.py)."
    ),
)


_DDL_READY = False


@pytest.fixture
async def pg_db():
    """Conecta no Postgres via AsyncSessionLocal canônico do projeto.

    - Garante a existência da tabela `company_hiring_policies` (DDL canônica)
      uma única vez por processo de teste — o engine async em
      `lia_config.database` é bindado ao primeiro event loop que o tocar,
      e pytest-asyncio cria loops por teste; rodar a DDL múltiplas vezes
      provoca "Future attached to a different loop" no segundo teste.
    - Se a DDL inicial falhar (PG indisponível em gate offline puro),
      pula o teste com mensagem clara.
    - Yield: `AsyncSessionLocal`. Cleanup feito por teste (DELETE WHERE
      company_id = ...) usando UUID isolado por teste.
    """
    global _DDL_READY
    try:
        from lia_config.database import AsyncSessionLocal
        from app.core.database import create_company_hiring_policies_table
    except Exception as exc:  # pragma: no cover — só dispara se libs quebrarem
        pytest.skip(f"Não consegui importar fixture de DB do projeto: {exc}")

    if not _DDL_READY:
        try:
            await create_company_hiring_policies_table()
        except Exception as exc:
            pytest.skip(f"Postgres indisponível para integração: {exc}")
        _DDL_READY = True

    yield AsyncSessionLocal


def _ctx(company_id: str, user_id: str = "user-task1009"):
    return SimpleNamespace(company_id=company_id, user_id=user_id)


async def _bind_and_load(SessionMaker, company_id: str) -> dict:
    """Lê a linha persistida em `company_hiring_policies` deserializando
    os 5 blocos. Vincula `app.company_id` (RLS) na MESMA transação do SELECT.
    """
    async with SessionMaker() as session:
        await session.execute(
            text("SELECT set_config('app.company_id', :cid, true)"),
            {"cid": company_id},
        )
        result = await session.execute(
            text(
                "SELECT company_id, pipeline_rules, scheduling_rules, "
                "communication_rules, screening_rules, automation_rules "
                "FROM company_hiring_policies WHERE company_id = :cid"
            ),
            {"cid": company_id},
        )
        row = result.mappings().first()
        await session.commit()

    assert row is not None, f"linha ausente em company_hiring_policies para {company_id}"

    parsed: dict = {"company_id": row["company_id"]}
    for block in (
        "pipeline_rules",
        "scheduling_rules",
        "communication_rules",
        "screening_rules",
        "automation_rules",
    ):
        raw = row[block]
        if isinstance(raw, str):
            parsed[block] = json.loads(raw)
        elif raw is None:
            parsed[block] = {}
        else:
            parsed[block] = raw  # asyncpg já desserializa json → dict
    return parsed


async def _cleanup(SessionMaker, company_id: str) -> None:
    """Apaga linhas residuais (policies + audit_logs) do tenant de teste."""
    async with SessionMaker() as session:
        await session.execute(
            text("SELECT set_config('app.company_id', :cid, true)"),
            {"cid": company_id},
        )
        await session.execute(
            text("DELETE FROM company_hiring_policies WHERE company_id = :cid"),
            {"cid": company_id},
        )
        # audit_logs também é tenant-scoped via RLS; best-effort cleanup
        try:
            await session.execute(
                text("DELETE FROM audit_logs WHERE company_id = :cid"),
                {"cid": company_id},
            )
        except Exception:
            pass
        await session.commit()


@pytest.mark.asyncio
async def test_save_hiring_policy_insert_then_update_merges_blocks(pg_db):
    """INSERT inicial + UPDATE em outro bloco → merge superficial preserva
    estado anterior. Exercita SQL bruto Postgres com cast `::json` em dicts
    vazios."""
    SessionMaker = pg_db
    from app.domains.company_settings.tools.import_tools import save_hiring_policy

    company_id = f"test-1009-{uuid.uuid4()}"
    try:
        # (a) INSERT inicial: 1 campo de screening_rules + 1 de communication_rules.
        first = await save_hiring_policy(
            rules={"min_interviews_before_offer": 2, "lia_tone": "amigável"},
            _context=_ctx(company_id),
        )
        assert first.get("success") is True, first
        assert sorted(first["data"]["blocks_touched"]) == [
            "communication_rules",
            "screening_rules",
        ]
        assert sorted(first["data"]["fields_saved"]) == [
            "lia_tone",
            "min_interviews_before_offer",
        ]

        after_insert = await _bind_and_load(SessionMaker, company_id)
        # 5 blocos JSONB inicializados — confirma que `::json` aceita `{}`
        # nos blocos não tocados sem erro de cast (requirement (c) da task).
        assert after_insert["pipeline_rules"] == {}
        assert after_insert["scheduling_rules"] == {}
        assert after_insert["automation_rules"] == {}
        assert after_insert["screening_rules"] == {"min_interviews_before_offer": 2}
        assert after_insert["communication_rules"] == {"lia_tone": "amigável"}

        # (b) UPDATE: campo em scheduling_rules → não pode apagar nada do INSERT.
        second = await save_hiring_policy(
            rules={"allowed_days": ["mon", "tue"]},
            _context=_ctx(company_id),
        )
        assert second.get("success") is True, second
        assert second["data"]["blocks_touched"] == ["scheduling_rules"]
        assert second["data"]["fields_saved"] == ["allowed_days"]

        after_update = await _bind_and_load(SessionMaker, company_id)
        assert after_update["scheduling_rules"] == {"allowed_days": ["mon", "tue"]}
        # PRESERVADO (regressão alvo): campos da chamada anterior intactos.
        assert after_update["screening_rules"] == {"min_interviews_before_offer": 2}
        assert after_update["communication_rules"] == {"lia_tone": "amigável"}
        assert after_update["pipeline_rules"] == {}
        assert after_update["automation_rules"] == {}

        # (c) Sentinela de unicidade do tenant: exatamente 1 linha.
        async with SessionMaker() as session:
            await session.execute(
                text("SELECT set_config('app.company_id', :cid, true)"),
                {"cid": company_id},
            )
            count = await session.execute(
                text(
                    "SELECT COUNT(*) FROM company_hiring_policies "
                    "WHERE company_id = :cid"
                ),
                {"cid": company_id},
            )
            assert count.scalar_one() == 1
            await session.commit()
    finally:
        await _cleanup(SessionMaker, company_id)


@pytest.mark.asyncio
async def test_save_hiring_policy_update_within_same_block_merges_atomic_fields(
    pg_db,
):
    """Merge superficial DENTRO do mesmo bloco JSONB: dois saves consecutivos
    em `screening_rules` devem coexistir (não substituição total do bloco).
    """
    SessionMaker = pg_db
    from app.domains.company_settings.tools.import_tools import save_hiring_policy

    company_id = f"test-1009-{uuid.uuid4()}"
    try:
        r1 = await save_hiring_policy(
            rules={"min_interviews_before_offer": 3},
            _context=_ctx(company_id),
        )
        assert r1.get("success") is True, r1

        r2 = await save_hiring_policy(
            rules={"manager_approval_for_offer": True},
            _context=_ctx(company_id),
        )
        assert r2.get("success") is True, r2

        final = await _bind_and_load(SessionMaker, company_id)
        assert final["screening_rules"] == {
            "min_interviews_before_offer": 3,
            "manager_approval_for_offer": True,
        }
    finally:
        await _cleanup(SessionMaker, company_id)
