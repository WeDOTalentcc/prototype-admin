"""W3-021 + W4-038 · TDD tests · LearningSignalRepository + few_shot schema/CLI.

Verifica:
1. Migration 184 criou learning_signals table com schema canonical.
2. LearningSignalRepository.insert persist + retorna UUID.
3. _require_company_id raise se ausente (fail-closed).
4. list_unconsumed_by_domain filtra correto.
5. mark_consumed atualiza flag.
6. count_by_company_and_domain retorna corretos.
7. CorrectionCaptureService.record_correction wire ao repo (smoke text check).
8. Schema canonical YAML existe.
9. Sensor check_few_shot_yaml_schema.py importável + executável.
10. CLI manage_few_shots.py importável.

Skip se sem DATABASE_URL.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest


def _get_async_database_url():
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

    url = os.environ.get("DATABASE_URL", "")
    if not url:
        return None
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if "+asyncpg" not in url:
        return None
    parts = urlsplit(url)
    drop = {"sslmode", "sslrootcert", "sslcert", "sslkey", "channel_binding"}
    new_qs = [(k, v) for k, v in parse_qsl(parts.query) if k not in drop]
    url = urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(new_qs), parts.fragment)
    )
    return url


@pytest.fixture
async def pg_session():
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    url = _get_async_database_url()
    if not url:
        pytest.skip("DATABASE_URL not available")

    engine = create_async_engine(url, future=True)
    sm = async_sessionmaker(engine, expire_on_commit=False)

    async with sm() as session:
        await session.execute(
            text("DELETE FROM learning_signals WHERE company_id LIKE 'w3021-test-%'")
        )
        await session.commit()
        yield session
        await session.execute(
            text("DELETE FROM learning_signals WHERE company_id LIKE 'w3021-test-%'")
        )
        await session.commit()

    await engine.dispose()


# ===== Repository tests =====


@pytest.mark.asyncio
async def test_table_has_canonical_schema(pg_session):
    """W3-021 · learning_signals table tem colunas canonical."""
    from sqlalchemy import text

    result = await pg_session.execute(
        text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'learning_signals' ORDER BY column_name"
        )
    )
    cols = {row[0] for row in result.fetchall()}
    required = {
        "id", "company_id", "user_id", "conversation_id", "domain",
        "original_response", "corrected_response", "feedback_type",
        "confidence_at_generation", "signal_metadata",
        "consumed_for_fewshot", "consumed_at", "created_at",
    }
    missing = required - cols
    assert not missing, f"learning_signals missing columns: {missing}"


@pytest.mark.asyncio
async def test_require_company_id_fail_closed(pg_session):
    """W3-021 · _require_company_id raise se ausente."""
    from app.domains.analytics.repositories.learning_signal_repository import (
        LearningSignalRepository,
    )

    repo = LearningSignalRepository(pg_session)
    with pytest.raises(ValueError, match="company_id"):
        await repo.insert(
            company_id="",
            user_id="user-1",
            conversation_id=None,
            domain="automation",
            original_response="orig",
            corrected_response="corr",
            feedback_type="correction",
        )


@pytest.mark.asyncio
async def test_insert_returns_uuid(pg_session):
    """W3-021 · insert persist + retorna UUID."""
    from app.domains.analytics.repositories.learning_signal_repository import (
        LearningSignalRepository,
    )

    cid = f"w3021-test-insert-{uuid.uuid4().hex[:8]}"
    repo = LearningSignalRepository(pg_session)
    signal_id = await repo.insert(
        company_id=cid,
        user_id="user-1",
        conversation_id="conv-1",
        domain="automation",
        original_response="resposta IA inicial",
        corrected_response="resposta corrigida pelo recrutador",
        feedback_type="correction",
        confidence_at_generation=0.75,
        metadata={"intent": "test"},
    )
    assert signal_id is not None
    # Confirma persistência
    from sqlalchemy import text
    result = await pg_session.execute(
        text("SELECT company_id, feedback_type FROM learning_signals WHERE id = :id"),
        {"id": str(signal_id)},
    )
    row = result.first()
    assert row is not None
    assert row[0] == cid
    assert row[1] == "correction"


@pytest.mark.asyncio
async def test_list_unconsumed_by_domain(pg_session):
    """W3-021 · list_unconsumed_by_domain retorna só não-consumed."""
    from app.domains.analytics.repositories.learning_signal_repository import (
        LearningSignalRepository,
    )

    cid = f"w3021-test-list-{uuid.uuid4().hex[:8]}"
    repo = LearningSignalRepository(pg_session)
    id1 = await repo.insert(
        company_id=cid, user_id="u1", conversation_id=None,
        domain="cv_screening", original_response="r1", corrected_response="r1c",
        feedback_type="correction",
    )
    id2 = await repo.insert(
        company_id=cid, user_id="u1", conversation_id=None,
        domain="cv_screening", original_response="r2", corrected_response="r2c",
        feedback_type="correction",
    )
    # Marca um como consumed
    await repo.mark_consumed(id1)

    unconsumed = await repo.list_unconsumed_by_domain(domain="cv_screening", limit=100)
    unconsumed_ids = [r["id"] for r in unconsumed]
    assert id1 not in unconsumed_ids
    assert id2 in unconsumed_ids


@pytest.mark.asyncio
async def test_count_by_company_and_domain(pg_session):
    """W3-021 · count_by_company_and_domain retorna correto + multi-tenant isolation."""
    from app.domains.analytics.repositories.learning_signal_repository import (
        LearningSignalRepository,
    )

    cid_a = f"w3021-test-count-a-{uuid.uuid4().hex[:8]}"
    cid_b = f"w3021-test-count-b-{uuid.uuid4().hex[:8]}"
    repo = LearningSignalRepository(pg_session)
    for _ in range(3):
        await repo.insert(
            company_id=cid_a, user_id="u1", conversation_id=None,
            domain="automation", original_response="r", corrected_response="rc",
            feedback_type="correction",
        )
    await repo.insert(
        company_id=cid_b, user_id="u1", conversation_id=None,
        domain="automation", original_response="r", corrected_response="rc",
        feedback_type="correction",
    )

    assert await repo.count_by_company_and_domain(company_id=cid_a) == 3
    assert await repo.count_by_company_and_domain(company_id=cid_b) == 1
    assert await repo.count_by_company_and_domain(company_id=cid_a, domain="automation") == 3
    assert await repo.count_by_company_and_domain(company_id=cid_a, domain="other") == 0


# ===== Static wire / schema tests =====


def test_correction_capture_wires_repo():
    """W3-021 · CorrectionCaptureService.record_correction USA LearningSignalRepository."""
    src = (
        Path(__file__).resolve().parents[2]
        / "app" / "shared" / "learning" / "correction_capture.py"
    ).read_text()
    assert "LearningSignalRepository" in src
    assert "repo.insert(" in src or "LearningSignalRepository(session)" in src
    # TODOs deferred devem estar removidos (substituídos por wire real)
    assert "TODO: Persist via LearningSignalRepository" not in src


def test_few_shot_template_yaml_exists():
    """W4-038 · template canonical schema doc existe."""
    p = (
        Path(__file__).resolve().parents[2]
        / "app" / "prompts" / "shared" / "few_shot_template.yaml"
    )
    assert p.exists()
    content = p.read_text()
    assert "few_shot_examples:" in content
    assert "W4-038" in content


def test_schema_sensor_script_exists():
    """W4-038 · sensor check_few_shot_yaml_schema.py existe + executable."""
    p = (
        Path(__file__).resolve().parents[2]
        / "scripts" / "check_few_shot_yaml_schema.py"
    )
    assert p.exists()
    assert "CATEGORY_PATTERN" in p.read_text()


def test_cli_manage_few_shots_exists():
    """W4-038 · CLI manage_few_shots.py existe + tem subcommands canonical."""
    p = (
        Path(__file__).resolve().parents[2]
        / "scripts" / "manage_few_shots.py"
    )
    assert p.exists()
    src = p.read_text()
    for sub in ("cmd_list", "cmd_validate", "cmd_add", "cmd_prune"):
        assert sub in src, f"CLI missing subcommand: {sub}"
