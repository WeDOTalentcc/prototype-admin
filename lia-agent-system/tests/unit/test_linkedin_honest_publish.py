"""
Onda 2E — proveniência honesta na publicação LinkedIn.

Antes: com credenciais configuradas, publish_to_linkedin FABRICAVA um post_id falso
(li_<uuid>), marcava a vaga como published_linkedin=True e retornava success=True com
uma URL inventada — SEM nenhuma chamada real à API do LinkedIn. Isso viola a regra de
proveniência honesta (CLAUDE.md). A LinkedIn Job Posting API exige aprovação de partner
e não está implementada → deve retornar not_implemented, sem fabricar publicação.
(Indeed NÃO é mock: alimenta um feed XML real — não alterado.)
"""
from types import SimpleNamespace

from app.domains.job_management.services.job_board_service import JobBoardService


class _FakeDB:
    async def commit(self):  # pragma: no cover
        pass

    async def rollback(self):  # pragma: no cover
        pass


def _job():
    return SimpleNamespace(
        id="job-1", title="Dev", published_linkedin=False,
        linkedin_post_id=None, last_published_at=None,
    )


class TestLinkedInHonesty:
    async def test_not_configured_without_credentials(self):
        svc = JobBoardService()
        svc.linkedin_client_id = None
        svc.linkedin_client_secret = None
        job = _job()
        r = await svc.publish_to_linkedin(job, _FakeDB())
        assert r["success"] is False
        assert r["error"] == "not_configured"
        assert job.published_linkedin is False

    async def test_does_not_fabricate_publish_when_credentials_set(self):
        svc = JobBoardService()
        svc.linkedin_client_id = "id"
        svc.linkedin_client_secret = "secret"
        job = _job()
        r = await svc.publish_to_linkedin(job, _FakeDB())
        assert r["success"] is False
        assert r.get("status") == "not_implemented"
        # NÃO fabrica post_id, NÃO marca como publicada, NÃO inventa URL.
        assert job.published_linkedin is False
        assert job.linkedin_post_id is None
        assert "post_id" not in r
        assert "job_url" not in r
