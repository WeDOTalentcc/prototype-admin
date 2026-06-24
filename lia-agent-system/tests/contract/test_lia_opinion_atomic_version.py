"""Contract tests — OpinionsRepository.create_wsi_opinion_with_atomic_version.

Closes the TODO at app/api/v1/wsi/evaluation.py:49 (Phase 2 ADR-001).
The endpoint previously inlined two raw SQL writes against ``lia_opinions``:

  (1) SELECT MAX(version)+1
  (2) INSERT (... version=:next_version)

Between (1) and (2) two concurrent completions could pick the same MAX,
violating the implicit "monotonically increasing version" invariant.
The new repository method collapses both into a single atomic statement.

These tests pin:
  * the method exists and exposes the canonical kwargs
  * multi-tenancy fail-closed via ``_require_company_id``
  * the archive step issues an UPDATE scoped to (candidate, vacancy, company)
  * the insert step issues a single statement containing both
    ``INSERT INTO lia_opinions`` and ``SELECT MAX(version)`` — proving the
    race window is closed at the SQL level
  * back-compat: returned id is a stringified UUID, no commit happens
    inside the repo (caller-owned transaction)
"""
from __future__ import annotations

import asyncio
import inspect
import re
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest


# ── Method existence & signature ────────────────────────────────────────────


def test_repo_exposes_atomic_version_method():
    """OpinionsRepository must expose create_wsi_opinion_with_atomic_version."""
    from app.repositories.opinions_repository import (
        OpinionsRepository,
    )

    assert hasattr(OpinionsRepository, "create_wsi_opinion_with_atomic_version"), (
        "OpinionsRepository missing create_wsi_opinion_with_atomic_version. "
        "Add the atomic INSERT ... SELECT MAX(version)+1 method so the WSI "
        "endpoint stops doing read-then-write on the version column."
    )


def test_atomic_version_method_signature():
    """Pin the kwargs surface so endpoint callers and tests cannot drift."""
    from app.repositories.opinions_repository import (
        OpinionsRepository,
    )

    sig = inspect.signature(
        OpinionsRepository.create_wsi_opinion_with_atomic_version
    )
    required = {
        "candidate_id",
        "job_vacancy_id",
        "company_id",
        "score",
        "wsi_score",
        "archetype",
        "recommendation",
        "summary",
        "score_breakdown",
        "strengths",
        "concerns",
        "gaps",
        "matched_skills",
        "missing_skills",
        "next_steps",
    }
    missing = required - set(sig.parameters)
    assert not missing, (
        f"create_wsi_opinion_with_atomic_version missing kwargs: {missing}. "
        "These are the canonical fields persisted on a WSI LiaOpinion — "
        "any divergence breaks the back-compat contract with the endpoint."
    )


def test_repo_exposes_company_id_for_vacancy_helper():
    """get_company_id_for_vacancy is the repo-side tenant lookup so the
    endpoint never trusts the request payload for company_id."""
    from app.repositories.opinions_repository import (
        OpinionsRepository,
    )

    assert hasattr(OpinionsRepository, "get_company_id_for_vacancy"), (
        "OpinionsRepository missing get_company_id_for_vacancy(job_vacancy_id). "
        "This is the canonical multi-tenancy lookup used by the WSI endpoint."
    )


# ── Multi-tenancy fail-closed ───────────────────────────────────────────────


def test_create_wsi_opinion_rejects_empty_company_id():
    """ADR-001 anatomy: every public repo write must call _require_company_id.
    Empty company_id must raise ValueError before any DB call."""
    from app.repositories.opinions_repository import (
        OpinionsRepository,
    )

    mock_db = AsyncMock()
    repo = OpinionsRepository(mock_db)

    async def _run():
        return await repo.create_wsi_opinion_with_atomic_version(
            candidate_id=str(uuid.uuid4()),
            job_vacancy_id=str(uuid.uuid4()),
            company_id="",  # ← fail-closed
            score=4.0,
            wsi_score=4.0,
            archetype="Executor Confiável",
            recommendation="approved",
            summary="ok",
            score_breakdown={},
            strengths=[],
            concerns=[],
            gaps=[],
            matched_skills=[],
            missing_skills=[],
            next_steps=[],
        )

    with pytest.raises(ValueError, match="company_id"):
        asyncio.run(_run())

    assert not mock_db.execute.called, (
        "DB.execute was called despite empty company_id — fail-closed "
        "guard must run BEFORE any DB I/O."
    )


def test_create_wsi_opinion_rejects_missing_candidate_id():
    """candidate_id is structurally required — without it the archive
    UPDATE would have no scope and could clobber other candidates."""
    from app.repositories.opinions_repository import (
        OpinionsRepository,
    )

    mock_db = AsyncMock()
    repo = OpinionsRepository(mock_db)

    async def _run():
        await repo.create_wsi_opinion_with_atomic_version(
            candidate_id="",
            job_vacancy_id=None,
            company_id=str(uuid.uuid4()),
            score=4.0,
            wsi_score=4.0,
            archetype="x",
            recommendation="approved",
            summary="ok",
            score_breakdown={},
            strengths=[],
            concerns=[],
            gaps=[],
            matched_skills=[],
            missing_skills=[],
            next_steps=[],
        )

    with pytest.raises(ValueError, match="candidate_id"):
        asyncio.run(_run())


# ── Atomic SQL shape (race condition closed at the SQL layer) ───────────────


def test_create_wsi_opinion_issues_exactly_two_statements():
    """One UPDATE (archive previous current) + one INSERT (atomic write).
    Anything more would re-open a multi-statement race window."""
    from app.repositories.opinions_repository import (
        OpinionsRepository,
    )

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=MagicMock())
    repo = OpinionsRepository(mock_db)

    candidate_id = str(uuid.uuid4())
    vacancy_id = str(uuid.uuid4())
    company_id = str(uuid.uuid4())

    async def _run():
        return await repo.create_wsi_opinion_with_atomic_version(
            candidate_id=candidate_id,
            job_vacancy_id=vacancy_id,
            company_id=company_id,
            score=4.0,
            wsi_score=4.0,
            archetype="Executor Confiável",
            recommendation="approved",
            summary="ok",
            score_breakdown={"bloom_level": 4},
            strengths=["a"],
            concerns=["b"],
            gaps=["c"],
            matched_skills=["py"],
            missing_skills=["k8s"],
            next_steps=["s1"],
        )

    opinion_id = asyncio.run(_run())

    # Returned id must be a valid UUID string (back-compat with the
    # previous inline str(uuid.uuid4()) generator).
    uuid.UUID(opinion_id)

    # Exactly 2 DB statements: archive + atomic insert.
    assert mock_db.execute.await_count == 2, (
        f"Expected 2 DB statements (UPDATE archive + atomic INSERT), got "
        f"{mock_db.execute.await_count}. Any extra statement (e.g. a "
        f"separate SELECT MAX(version)) re-opens the race window the "
        f"atomic SQL is supposed to close."
    )


def test_create_wsi_opinion_atomic_sql_contains_select_max_inside_insert():
    """This is the load-bearing assertion: the SECOND statement must contain
    BOTH ``INSERT INTO lia_opinions`` AND ``SELECT MAX(version)`` — proving
    that the next-version computation lives inside the same statement that
    inserts, eliminating the read-then-write race condition."""
    from app.repositories.opinions_repository import (
        OpinionsRepository,
    )

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=MagicMock())
    repo = OpinionsRepository(mock_db)

    async def _run():
        await repo.create_wsi_opinion_with_atomic_version(
            candidate_id=str(uuid.uuid4()),
            job_vacancy_id=str(uuid.uuid4()),
            company_id=str(uuid.uuid4()),
            score=4.0,
            wsi_score=4.0,
            archetype="x",
            recommendation="approved",
            summary="ok",
            score_breakdown={},
            strengths=[],
            concerns=[],
            gaps=[],
            matched_skills=[],
            missing_skills=[],
            next_steps=[],
        )

    asyncio.run(_run())

    # Inspect each statement issued.
    statements = []
    for call_args in mock_db.execute.await_args_list:
        clause = call_args.args[0]
        sql_text = str(getattr(clause, "text", clause))
        statements.append(sql_text)

    assert any("UPDATE lia_opinions" in s and "is_current = false" in s for s in statements), (
        "Missing archive UPDATE statement — previous current WSI opinion "
        "must be marked is_current=false before insert."
    )

    insert_stmts = [s for s in statements if "INSERT INTO lia_opinions" in s]
    assert len(insert_stmts) == 1, (
        f"Expected exactly one INSERT statement, got {len(insert_stmts)}. "
        "If there are zero, the atomic write was skipped. If more than one, "
        "something is splitting the write — race window may be re-opened."
    )

    insert_sql = insert_stmts[0]
    assert re.search(r"SELECT\s+MAX\(version\)", insert_sql, re.IGNORECASE), (
        "The INSERT statement does not contain ``SELECT MAX(version)`` — "
        "this means the version is being computed by a separate statement, "
        "which re-introduces the race condition that this refactor exists to fix.\n\n"
        f"Actual SQL:\n{insert_sql}"
    )
    assert re.search(r"COALESCE\(", insert_sql, re.IGNORECASE), (
        "The MAX(version) must be wrapped in COALESCE(..., 0) so the very "
        "first WSI opinion for a candidate/vacancy gets version=1."
    )


def test_create_wsi_opinion_archive_scope_includes_company_id():
    """The archive UPDATE must filter by company_id — without it a writer
    could deactivate is_current=true rows belonging to another tenant."""
    from app.repositories.opinions_repository import (
        OpinionsRepository,
    )

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=MagicMock())
    repo = OpinionsRepository(mock_db)

    async def _run():
        await repo.create_wsi_opinion_with_atomic_version(
            candidate_id=str(uuid.uuid4()),
            job_vacancy_id=str(uuid.uuid4()),
            company_id=str(uuid.uuid4()),
            score=4.0,
            wsi_score=4.0,
            archetype="x",
            recommendation="approved",
            summary="ok",
            score_breakdown={},
            strengths=[],
            concerns=[],
            gaps=[],
            matched_skills=[],
            missing_skills=[],
            next_steps=[],
        )

    asyncio.run(_run())

    archive_calls = [
        c for c in mock_db.execute.await_args_list
        if "UPDATE lia_opinions" in str(getattr(c.args[0], "text", c.args[0]))
    ]
    assert archive_calls, "Archive UPDATE never issued."
    archive_sql = str(getattr(archive_calls[0].args[0], "text", archive_calls[0].args[0]))
    assert "company_id" in archive_sql and ":company_id" in archive_sql, (
        "Archive UPDATE must filter by :company_id to keep multi-tenancy "
        "fail-closed. Without it, two tenants sharing a candidate row "
        "(e.g. in a test seed) could deactivate each other's opinions."
    )


def test_create_wsi_opinion_does_not_commit_inside_repo():
    """Transaction ownership belongs to the request scope (FastAPI Depends).
    Committing inside the repo would break atomicity with wsi_results +
    wsi_sessions writes that the endpoint performs in the same request."""
    from app.repositories.opinions_repository import (
        OpinionsRepository,
    )

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=MagicMock())
    repo = OpinionsRepository(mock_db)

    async def _run():
        await repo.create_wsi_opinion_with_atomic_version(
            candidate_id=str(uuid.uuid4()),
            job_vacancy_id=None,  # exercise the NULL-vacancy path too
            company_id=str(uuid.uuid4()),
            score=4.0,
            wsi_score=4.0,
            archetype="x",
            recommendation="approved",
            summary="ok",
            score_breakdown={},
            strengths=[],
            concerns=[],
            gaps=[],
            matched_skills=[],
            missing_skills=[],
            next_steps=[],
        )

    asyncio.run(_run())

    assert not mock_db.commit.called, (
        "Repo committed the session — transaction must stay caller-owned "
        "so the endpoint can group LiaOpinion + wsi_results + wsi_sessions "
        "writes into a single atomic request transaction."
    )


# ── Endpoint refactor pin — inline SQL no longer in the API surface ─────────


def test_evaluation_endpoint_no_more_inline_lia_opinions_sql():
    """Once the refactor lands, app/api/v1/wsi/evaluation.py must not contain
    the previous inline ``INSERT INTO lia_opinions`` / ``SELECT COALESCE(MAX(version), 0)``
    blocks. The TODO at line 49 is closed by delegating to the repository."""
    import importlib
    import inspect as _inspect

    mod = importlib.import_module("app.api.v1.wsi.evaluation")
    src = _inspect.getsource(mod)

    # The big inline SQL strings that used to live in the endpoint.
    forbidden = [
        "INSERT INTO lia_opinions",
        "UPDATE lia_opinions",
        "SELECT COALESCE(MAX(version), 0) + 1 as next_version",
        "FROM lia_opinions",
    ]
    leaks = [needle for needle in forbidden if needle in src]
    assert not leaks, (
        f"evaluation.py still contains inline lia_opinions SQL: {leaks}. "
        "All lia_opinions writes must go through "
        "OpinionsRepository.create_wsi_opinion_with_atomic_version."
    )

    # Positive: the endpoint must actually USE the new repo method.
    assert "create_wsi_opinion_with_atomic_version" in src, (
        "evaluation.py never calls the new atomic-version repo method. "
        "The refactor was applied to the repo but the endpoint still "
        "imports nothing — wire OpinionsRepository(db).create_wsi_opinion_with_atomic_version(...)."
    )
