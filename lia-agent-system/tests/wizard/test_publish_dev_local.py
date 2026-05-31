"""TDD — dev-local publish fallbacks no JobCreationAPIClient.

FastAPI canonical, Rails fora (Paulo 2026-05-31). Quando base_url vazio,
publish_job/save_screening_config/get_share_link gravam direto no Postgres
via psycopg2 (sync — evita o bug 'Future attached to a different loop' do
engine async global reusado entre asyncio.run sequenciais). Testa roteamento
+ SQL emitido + wrapping APIResponse com uma conexão psycopg2 fake.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.domains.job_creation.api_client import JobCreationAPIClient, APIResponse


def _client_devlocal() -> JobCreationAPIClient:
    c = JobCreationAPIClient()
    c.base_url = ""  # força dev-local
    return c


class _FakeCursor:
    def __init__(self, fetchone_result):
        self._fetchone = fetchone_result
        self.executed: list[tuple] = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchone(self):
        return self._fetchone


class _FakeConn:
    def __init__(self, fetchone_result):
        self.cursor_obj = _FakeCursor(fetchone_result)
        self.committed = False
        self.closed = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True


@pytest.mark.medium
def test_publish_job_local_sets_status_ativa_and_flags():
    c = _client_devlocal()
    fake = _FakeConn(fetchone_result=("uid-1",))
    with patch.object(c, "_devlocal_conn", return_value=fake):
        res = c.publish_job("uid-1", ["linkedin", "website"], "local")
    assert res.success
    assert res.data["status"] == "Ativa"
    assert fake.committed and fake.closed
    sql, params = fake.cursor_obj.executed[0]
    assert "status = 'Ativa'" in sql
    # flags: linkedin True, website True, indeed False
    assert params[0] is True and params[1] is True and params[2] is False


@pytest.mark.medium
def test_publish_job_local_not_found_fail_loud():
    c = _client_devlocal()
    fake = _FakeConn(fetchone_result=None)
    with patch.object(c, "_devlocal_conn", return_value=fake):
        res = c.publish_job("missing", [], "local")
    assert not res.success
    assert "não encontrada" in res.error


@pytest.mark.medium
def test_publish_job_uses_rails_when_base_url_set():
    c = JobCreationAPIClient()
    c.base_url = "http://rails.example"
    with patch.object(c, "_request", return_value=APIResponse(success=True, data={})) as m, \
         patch.object(c, "_publish_job_local") as local:
        c.publish_job(1, ["website"], "local")
    assert m.called and not local.called


@pytest.mark.medium
def test_save_screening_config_local_merges_jsonb():
    c = _client_devlocal()
    fake = _FakeConn(fetchone_result=("uid-1",))
    with patch.object(c, "_devlocal_conn", return_value=fake):
        res = c.save_screening_config("uid-1", [{"q": 1}] * 3, "compact", [])
    assert res.success and res.data["saved"] == 3
    sql, params = fake.cursor_obj.executed[0]
    assert "screening_config" in sql and "||" in sql  # merge jsonb


@pytest.mark.medium
def test_get_share_link_local_generates_slug_when_missing():
    c = _client_devlocal()
    # SELECT retorna (public_slug=None, title) → gera slug + UPDATE
    fake = _FakeConn(fetchone_result=(None, "Engenheiro de Software"))
    with patch.object(c, "_devlocal_conn", return_value=fake):
        res = c.get_share_link("uid-1")
    assert res.success
    assert res.data["share_link"].startswith("https://app.wedotalent.com/jobs/")
    assert "engenheiro" in res.data["slug"].lower()
    # houve um UPDATE do slug (2ª execução)
    assert any("UPDATE job_vacancies SET public_slug" in e[0] for e in fake.cursor_obj.executed)


@pytest.mark.medium
def test_get_share_link_local_reuses_existing_slug():
    c = _client_devlocal()
    fake = _FakeConn(fetchone_result=("ja-existe-abc", "Cargo"))
    with patch.object(c, "_devlocal_conn", return_value=fake):
        res = c.get_share_link("uid-1")
    assert res.success
    assert res.data["slug"] == "ja-existe-abc"
    # não deve emitir UPDATE quando slug já existe
    assert all("UPDATE" not in e[0] for e in fake.cursor_obj.executed)


@pytest.mark.medium
def test_get_share_link_local_not_found():
    c = _client_devlocal()
    fake = _FakeConn(fetchone_result=None)
    with patch.object(c, "_devlocal_conn", return_value=fake):
        res = c.get_share_link("missing")
    assert not res.success
    assert "não encontrada" in res.error


@pytest.mark.medium
def test_screening_config_persists_mode_with_empty_questions():
    """Gap 2026-05-31: screening_config deve gravar o modo mesmo SEM perguntas WSI."""
    c = _client_devlocal()
    fake = _FakeConn(fetchone_result=("uid-1",))
    with patch.object(c, "_devlocal_conn", return_value=fake):
        res = c.save_screening_config("uid-1", [], "full", [])
    assert res.success
    # o jsonb merge inclui screening_mode mesmo com questions=[]
    sql, params = fake.cursor_obj.executed[0]
    assert "screening_config" in sql
    import json as _j
    payload = _j.loads(params[0])
    assert payload["screening_mode"] == "full"
    assert payload["screening_questions"] == []
