"""Unit tests do wrapper resolve_field_default_for_state (FASE 1).

Estaveis (sem DB/loop): monkeypatcham get_field_config + AsyncSessionLocal pra
testar a logica do wrapper — extracao do valor escalar + fail-open. A cadeia de
heranca real (departamento > empresa) ja e coberta, com DB real, por
tests/integration/test_department_defaults_inheritance.py.
"""
from __future__ import annotations

import contextlib
import uuid

import pytest

from app.domains.job_creation.helpers.vaga_field_inheritance import (
    resolve_field_default_for_state,
)

pytestmark = pytest.mark.asyncio

_CID = str(uuid.uuid4())


@contextlib.asynccontextmanager
async def _fake_session():
    yield object()


class _Ctx:
    def __init__(self, value):
        self.value = value


def _fake_service_factory(field_contexts):
    class _Result:
        pass

    class _Svc:
        def __init__(self, db):
            pass

        async def get_field_config(self, company_id, job_context):
            r = _Result()
            r.field_contexts = field_contexts
            return r

    return _Svc


def _patch(monkeypatch, field_contexts=None, raises=False):
    monkeypatch.setattr("app.core.database.AsyncSessionLocal", _fake_session)
    if raises:
        class _Boom:
            def __init__(self, db):
                pass

            async def get_field_config(self, *a, **k):
                raise RuntimeError("boom")
        svc = _Boom
    else:
        svc = _fake_service_factory(field_contexts or {})
    monkeypatch.setattr(
        "app.domains.cv_screening.services.lia_field_config_service.LiaFieldConfigService",
        svc,
    )


async def test_extracts_scalar_value(monkeypatch):
    _patch(monkeypatch, {"work_model": _Ctx("REMOTE-X")})
    assert await resolve_field_default_for_state({"company_id": _CID}, "work_model") == "REMOTE-X"


async def test_non_scalar_value_returns_none(monkeypatch):
    # valor lista (campo nao-escalar) -> None (nao aplicavel a um campo unico)
    _patch(monkeypatch, {"tech_stack": _Ctx(["Python", "Go"])})
    assert await resolve_field_default_for_state({"company_id": _CID}, "tech_stack") is None


async def test_missing_field_returns_none(monkeypatch):
    _patch(monkeypatch, {})
    assert await resolve_field_default_for_state({"company_id": _CID}, "work_model") is None


async def test_fail_open_on_service_error(monkeypatch):
    _patch(monkeypatch, raises=True)
    assert await resolve_field_default_for_state({"company_id": _CID}, "work_model") is None


async def test_fail_open_bad_company_id():
    assert await resolve_field_default_for_state({"company_id": "not-a-uuid"}, "work_model") is None


async def test_fail_open_no_company_id():
    assert await resolve_field_default_for_state({}, "work_model") is None
