"""
Tests for Task #442: persist ATS-pulled jobs into job_vacancies.

Covers:
- pull_jobs upserts JobVacancy rows with source_system + external_system_id
- Re-imports are idempotent on (company_id, source_system, external_system_id)
- Webhook handler `process_ats_job_event` upserts via the same path
- Gupy and Pandapé-shaped payloads
"""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.domains.ats_integration.services.ats_clients.base import ATSJob
from app.domains.ats_integration.services.ats_sync_service import ATSSyncService
from lia_models.job_vacancy import JobVacancy


class _FakeClient:
    """Minimal ATS client returning canned ATSJob objects."""

    def __init__(self, jobs: list[ATSJob]):
        self._jobs = jobs

    async def sync_jobs_from_ats(self, status: str | None = None, limit: int = 100):
        return list(self._jobs)


class _FakeSession:
    """In-memory replacement for ``AsyncSession`` used by ``upsert_job_vacancy``.

    We only need ``execute(stmt)`` to return scalars().all() over our store and
    ``add()`` / ``flush()`` to track inserts. The Service does not rely on any
    other Session features.
    """

    def __init__(self) -> None:
        self.store: list[JobVacancy] = []
        self._added: list[JobVacancy] = []

    async def execute(self, stmt):  # noqa: ARG002 — we ignore the SQL stmt and return everything
        store = self.store

        class _Result:
            def scalars(self_inner):
                class _Scalars:
                    def all(self_inner2):
                        return list(store)

                    def first(self_inner2):
                        return store[0] if store else None
                return _Scalars()

        return _Result()

    def add(self, obj: JobVacancy) -> None:
        self._added.append(obj)
        self.store.append(obj)

    async def flush(self) -> None:
        return None


def _gupy_job() -> ATSJob:
    raw: dict[str, Any] = {
        "id": "GP-1001",
        "name": "Engenheiro(a) de Software Sênior",
        "department": "Tecnologia",
        "location": "São Paulo, SP",
        "status": "published",
        "type": "CLT",
    }
    return ATSJob(
        ats_id="GP-1001",
        title="Engenheiro(a) de Software Sênior",
        description="Vaga vinda do Gupy",
        department="Tecnologia",
        location="São Paulo, SP",
        status="Ativa",
        employment_type="CLT",
        raw_data=raw,
    )


def _pandape_job() -> ATSJob:
    raw: dict[str, Any] = {
        "IdVacancy": 88231,
        "Title": "Analista de RH Pleno",
        "Department": "Recursos Humanos",
        "City": "Rio de Janeiro",
        "State": "RJ",
        "Status": "Open",
    }
    return ATSJob(
        ats_id="88231",
        title="Analista de RH Pleno",
        description="Vaga vinda do Pandapé",
        department="Recursos Humanos",
        location="Rio de Janeiro, RJ",
        status="Ativa",
        employment_type=None,
        raw_data=raw,
    )


@pytest.mark.asyncio
async def test_pull_jobs_persists_gupy_job_with_source_system():
    company_id = f"test-company-{uuid4().hex[:8]}"
    service = ATSSyncService()
    service.register_client("gupy", _FakeClient([_gupy_job()]))
    db = _FakeSession()

    result = await service.pull_jobs(
        ats_type="gupy",
        db=db,
        company_id=company_id,
    )

    assert result["success"] is True
    assert result["persisted"] is True
    assert result["created"] == 1
    assert result["updated"] == 0
    assert len(db.store) == 1
    row = db.store[0]
    assert row.company_id == company_id
    assert row.source_system == "gupy"
    assert (row.additional_data or {}).get("external_system_id") == "GP-1001"
    assert row.title == "Engenheiro(a) de Software Sênior"


@pytest.mark.asyncio
async def test_pull_jobs_is_idempotent_on_reimport_pandape():
    company_id = f"test-company-{uuid4().hex[:8]}"
    service = ATSSyncService()
    service.register_client("pandape", _FakeClient([_pandape_job()]))
    db = _FakeSession()

    first = await service.pull_jobs(
        ats_type="pandape", db=db, company_id=company_id
    )
    assert first["created"] == 1
    assert first["updated"] == 0
    assert len(db.store) == 1

    second = await service.pull_jobs(
        ats_type="pandape", db=db, company_id=company_id
    )
    assert second["created"] == 0
    assert second["updated"] == 1
    assert len(db.store) == 1, "re-import must not create a duplicate row"

    row = db.store[0]
    assert row.source_system == "pandape"
    assert (row.additional_data or {}).get("external_system_id") == "88231"


@pytest.mark.asyncio
async def test_pull_jobs_isolates_per_company():
    company_a = f"company-a-{uuid4().hex[:8]}"
    company_b = f"company-b-{uuid4().hex[:8]}"
    service = ATSSyncService()
    service.register_client("gupy", _FakeClient([_gupy_job()]))

    db_a = _FakeSession()
    db_b = _FakeSession()
    res_a = await service.pull_jobs(ats_type="gupy", db=db_a, company_id=company_a)
    res_b = await service.pull_jobs(ats_type="gupy", db=db_b, company_id=company_b)

    assert res_a["created"] == 1 and res_b["created"] == 1
    assert db_a.store[0].company_id == company_a
    assert db_b.store[0].company_id == company_b


@pytest.mark.asyncio
async def test_upsert_job_vacancy_updates_mutable_fields():
    company_id = f"test-company-{uuid4().hex[:8]}"
    service = ATSSyncService()
    db = _FakeSession()

    job = _gupy_job()
    action = await service.upsert_job_vacancy(
        db=db, company_id=company_id, ats_type="gupy", job=job
    )
    assert action == "created"

    job.title = "Engenheiro(a) de Software Staff"
    job.location = "Remoto - Brasil"
    action = await service.upsert_job_vacancy(
        db=db, company_id=company_id, ats_type="gupy", job=job
    )
    assert action == "updated"
    assert len(db.store) == 1

    row = db.store[0]
    assert row.title == "Engenheiro(a) de Software Staff"
    assert row.location == "Remoto - Brasil"
    assert (row.additional_data or {}).get("external_system_id") == "GP-1001"


@pytest.mark.asyncio
async def test_upsert_skips_when_external_id_missing():
    service = ATSSyncService()
    db = _FakeSession()
    job = ATSJob(ats_id="", title="Sem ID")
    action = await service.upsert_job_vacancy(
        db=db, company_id="any", ats_type="gupy", job=job
    )
    assert action == "skipped"
    assert db.store == []


@pytest.mark.asyncio
async def test_pull_jobs_without_db_does_not_persist():
    """When no db/company_id is passed, pull_jobs must not include persistence info."""
    service = ATSSyncService()
    service.register_client("gupy", _FakeClient([_gupy_job()]))

    result = await service.pull_jobs(ats_type="gupy")
    assert result["success"] is True
    assert "persisted" not in result
    assert result["count"] == 1


@pytest.mark.asyncio
async def test_webhook_job_event_upserts_for_gupy_payload():
    """`process_ats_job_event` should map a Gupy webhook payload and upsert."""
    from app.api.v1 import external_webhooks as wh

    captured: dict[str, Any] = {}

    fake_db = _FakeSession()

    class _AsyncCM:
        async def __aenter__(self_inner):
            return fake_db

        async def __aexit__(self_inner, *exc):
            return False

    sync_service = ATSSyncService()

    async def _spy_upsert(db, company_id, ats_type, job):
        captured["company_id"] = company_id
        captured["ats_type"] = ats_type
        captured["external_id"] = job.ats_id
        captured["title"] = job.title
        return "created"

    with patch.object(sync_service, "upsert_job_vacancy", side_effect=_spy_upsert), \
         patch.object(wh, "get_ats_sync_service", return_value=sync_service), \
         patch("lia_config.database.get_tenant_aware_session", return_value=_AsyncCM()):
        await wh.process_ats_job_event(
            "gupy",
            "job.created",
            {
                "event": "job.created",
                "company_id": "company-xyz",
                "job": {
                    "id": "GP-9001",
                    "name": "Vaga Gupy",
                    "department": "Eng",
                    "location": "SP",
                    "status": "published",
                },
            },
        )

    assert captured["company_id"] == "company-xyz"
    assert captured["ats_type"] == "gupy"
    assert captured["external_id"] == "GP-9001"
    assert captured["title"] == "Vaga Gupy"


@pytest.mark.asyncio
async def test_webhook_job_event_upserts_for_pandape_payload():
    """`process_ats_job_event` should map a Pandapé webhook payload and upsert."""
    from app.api.v1 import external_webhooks as wh

    captured: dict[str, Any] = {}

    fake_db = _FakeSession()

    class _AsyncCM:
        async def __aenter__(self_inner):
            return fake_db

        async def __aexit__(self_inner, *exc):
            return False

    sync_service = ATSSyncService()

    async def _spy_upsert(db, company_id, ats_type, job):
        captured["company_id"] = company_id
        captured["ats_type"] = ats_type
        captured["external_id"] = job.ats_id
        captured["title"] = job.title
        return "updated"

    with patch.object(sync_service, "upsert_job_vacancy", side_effect=_spy_upsert), \
         patch.object(wh, "get_ats_sync_service", return_value=sync_service), \
         patch("lia_config.database.get_tenant_aware_session", return_value=_AsyncCM()):
        await wh.process_ats_job_event(
            "pandape",
            "job.updated",
            {
                "event": "job.updated",
                "tenant_id": "company-abc",
                "vacancy": {
                    "IdVacancy": 12345,
                    "Title": "Vaga Pandapé",
                    "City": "RJ",
                    "Status": "Open",
                },
            },
        )

    assert captured["company_id"] == "company-abc"
    assert captured["ats_type"] == "pandape"
    assert captured["external_id"] == "12345"
    assert captured["title"] == "Vaga Pandapé"


@pytest.mark.asyncio
async def test_upsert_lookup_filters_by_external_id_in_sql_returning_single_row():
    """Task #446: ``upsert_job_vacancy`` must push the
    ``external_system_id`` filter down to SQL (not iterate every row of the
    ``(company_id, source_system)`` window in Python) and only fetch a single
    matching row per lookup.
    """
    from sqlalchemy.sql import Select

    company_id = f"test-company-{uuid4().hex[:8]}"
    service = ATSSyncService()

    captured: list[Any] = []

    class _CaptureSession(_FakeSession):
        async def execute(self_inner, stmt):
            captured.append(stmt)
            return await _FakeSession.execute(self_inner, stmt)

    db = _CaptureSession()
    await service.upsert_job_vacancy(
        db=db, company_id=company_id, ats_type="gupy", job=_gupy_job()
    )

    assert len(captured) == 1, "expected exactly one SELECT per upsert"
    stmt = captured[0]
    assert isinstance(stmt, Select)

    # The SELECT must be limited to a single row — no more loading the whole
    # (company_id, source_system) window into memory.
    assert stmt._limit == 1, "lookup must request at most one row"

    # And it must filter on additional_data->>'external_system_id' at the SQL
    # layer so the new functional index can serve it in O(1).
    from sqlalchemy.dialects import postgresql
    compiled = str(stmt.compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": True},
    ))
    assert "additional_data ->> 'external_system_id'" in compiled
    assert "GP-1001" in compiled
    assert "company_id" in compiled
    assert "source_system" in compiled
    assert "LIMIT 1" in compiled


@pytest.mark.asyncio
async def test_upsert_returns_only_matching_row_when_window_has_many():
    """Task #446: even when the (company_id, source_system) window already
    contains many imported rows, the lookup must return only the row whose
    ``external_system_id`` matches — proving the filter happens at the SQL
    layer (not by iterating every row in Python).
    """
    company_id = f"test-company-{uuid4().hex[:8]}"
    service = ATSSyncService()

    # A FakeSession that actually evaluates the SELECT's WHERE clause against
    # its in-memory store, so a regression to "load everything and filter in
    # Python" would surface as multiple matched rows / wrong row updated.
    class _FilteringSession:
        def __init__(self_inner) -> None:
            self_inner.store: list[JobVacancy] = []
            self_inner.executed_count = 0

        async def execute(self_inner, stmt):
            self_inner.executed_count += 1
            # Pull literal-bound predicates from the compiled SQL so we don't
            # have to walk SQLAlchemy's expression tree.
            from sqlalchemy.dialects import postgresql
            sql = str(stmt.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True},
            ))

            def _matches(row: JobVacancy) -> bool:
                if f"company_id = '{row.company_id}'" not in sql:
                    return False
                if f"source_system = '{row.source_system}'" not in sql:
                    return False
                ext = (row.additional_data or {}).get("external_system_id", "")
                if f"= '{ext}'" not in sql:
                    return False
                return True

            matched = [r for r in self_inner.store if _matches(r)]
            limited = matched[:1]  # honour the LIMIT 1

            class _Result:
                def scalars(self_inner2):
                    class _Scalars:
                        def all(self_inner3):
                            return list(limited)

                        def first(self_inner3):
                            return limited[0] if limited else None
                    return _Scalars()

            return _Result()

        def add(self_inner, obj: JobVacancy) -> None:
            self_inner.store.append(obj)

        async def flush(self_inner) -> None:
            return None

    db = _FilteringSession()

    # Pre-populate the window with several other gupy imports for the same
    # tenant so a Python-side scan of the (company, source_system) bucket
    # would have to iterate all of them.
    for ext_id in ("GP-2000", "GP-2001", "GP-2002", "GP-2003"):
        db.store.append(JobVacancy(
            company_id=company_id,
            source_system="gupy",
            title=f"Other vaga {ext_id}",
            additional_data={"external_system_id": ext_id},
        ))

    # Upsert the target row (GP-1001) — should create it, not match any of the
    # pre-existing siblings.
    action = await service.upsert_job_vacancy(
        db=db, company_id=company_id, ats_type="gupy", job=_gupy_job()
    )
    assert action == "created"
    assert db.executed_count == 1, "exactly one SELECT per upsert"
    assert len(db.store) == 5

    # Re-upsert the same job — must update the just-created row, not any of
    # the unrelated GP-2000..GP-2003 siblings.
    action = await service.upsert_job_vacancy(
        db=db, company_id=company_id, ats_type="gupy", job=_gupy_job()
    )
    assert action == "updated"
    assert len(db.store) == 5, "no duplicate row created on re-upsert"

    # Sanity: the unrelated siblings are untouched.
    siblings = [r for r in db.store if (r.additional_data or {}).get(
        "external_system_id") in {"GP-2000", "GP-2001", "GP-2002", "GP-2003"}]
    assert len(siblings) == 4
    for s in siblings:
        assert s.title.startswith("Other vaga ")


@pytest.mark.asyncio
async def test_webhook_job_event_without_company_id_is_noop():
    """No company_id ⇒ handler logs and returns; no upsert call."""
    from app.api.v1 import external_webhooks as wh

    sync_service = ATSSyncService()
    upsert_mock = AsyncMock()
    with patch.object(sync_service, "upsert_job_vacancy", upsert_mock), \
         patch.object(wh, "get_ats_sync_service", return_value=sync_service):
        await wh.process_ats_job_event(
            "gupy",
            "job.created",
            {"job": {"id": "GP-1", "name": "Foo"}},
        )
    upsert_mock.assert_not_awaited()
