"""Task #1219 — loop de completude "Híbrida com email" (require_emails=True).

Garante que a busca acumula o ALVO de candidatos COM email percorrendo páginas
adicionais da Pearch, NUNCA devolve candidato sem email, e respeita os
guardrails (max_pages, deadline, parada em erro/esgotamento) — sem loop
infinito e sem fake success.
"""
import time

import pytest

from lia_models.pearch import (
    CandidateProfile,
    PearchSearchRequest,
    PearchSearchResponse,
)
from app.domains.sourcing.services.pearch_service import (
    PearchService,
    _profile_has_email,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _profile(docid: str, *, has_email: bool) -> CandidateProfile:
    return CandidateProfile(
        docid=docid,
        full_name=f"cand-{docid}",
        has_emails=has_email,
    )


def _response(profiles: list[CandidateProfile], *, thread_id="t1", credits=99) -> PearchSearchResponse:
    return PearchSearchResponse(
        uuid="u",
        thread_id=thread_id,
        query="dev",
        status="completed",
        total_estimate=len(profiles),
        credits_remaining=credits,
        candidates=profiles,  # get_candidates() faz fallback p/ candidates
    )


def _service() -> PearchService:
    # Sem API key — não importa, vamos mockar search_candidates direto.
    return PearchService(timeout=5.0)


# ---------------------------------------------------------------------------
# _profile_has_email
# ---------------------------------------------------------------------------

class TestProfileHasEmail:
    def test_has_emails_flag_true(self):
        assert _profile_has_email(_profile("a", has_email=True)) is True

    def test_no_email_is_false(self):
        assert _profile_has_email(_profile("a", has_email=False)) is False

    def test_email_strings_count_even_without_flag(self):
        p = CandidateProfile(docid="x", emails=["a@b.com"])
        assert _profile_has_email(p) is True

    def test_best_personal_email_counts(self):
        p = CandidateProfile(docid="x", best_personal_email="a@b.com")
        assert _profile_has_email(p) is True


# ---------------------------------------------------------------------------
# _accumulate_pearch_with_emails
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestAccumulateLoop:

    async def _run(self, svc, pages, target, monkeypatch):
        """pages: lista de listas de CandidateProfile (uma por chamada)."""
        calls = {"n": 0, "blacklists": []}

        async def fake_search(request, timeout=None, company_id=None):
            calls["blacklists"].append(list(request.docid_blacklist or []))
            i = calls["n"]
            calls["n"] += 1
            page = pages[i] if i < len(pages) else []
            return _response(page)

        monkeypatch.setattr(svc, "search_candidates", fake_search)
        base = PearchSearchRequest(query="dev", require_emails=True)
        accumulated, diag = await svc._accumulate_pearch_with_emails(
            base_request=base, target=target, loop_start_monotonic=time.monotonic()
        )
        return accumulated, diag, calls

    async def test_single_page_reaches_target(self, monkeypatch):
        svc = _service()
        pages = [[_profile(str(i), has_email=True) for i in range(5)]]
        acc, diag, calls = await self._run(svc, pages, target=5, monkeypatch=monkeypatch)
        assert len(acc) == 5
        assert all(_profile_has_email(c) for c in acc)
        assert diag["stop_reason"] == "target_reached"
        assert calls["n"] == 1

    async def test_paginates_until_target_filtering_no_email(self, monkeypatch):
        svc = _service()
        # Página 1: 2 com email + 2 sem. Página 2: 3 com email.
        pages = [
            [_profile("1", has_email=True), _profile("2", has_email=False),
             _profile("3", has_email=True), _profile("4", has_email=False)],
            [_profile("5", has_email=True), _profile("6", has_email=True),
             _profile("7", has_email=True)],
        ]
        acc, diag, calls = await self._run(svc, pages, target=5, monkeypatch=monkeypatch)
        assert len(acc) == 5
        assert all(_profile_has_email(c) for c in acc)
        assert diag["filtered_no_email"] == 2
        assert calls["n"] == 2
        # docids da página 1 entram no blacklist da página 2 (paginação)
        assert set(calls["blacklists"][1]) >= {"1", "2", "3", "4"}

    async def test_never_returns_no_email_candidate(self, monkeypatch):
        svc = _service()
        pages = [[_profile(str(i), has_email=(i % 2 == 0)) for i in range(10)]]
        acc, diag, _ = await self._run(svc, pages, target=10, monkeypatch=monkeypatch)
        assert all(_profile_has_email(c) for c in acc)

    async def test_exhaustion_stops_no_infinite_loop(self, monkeypatch):
        svc = _service()
        # Só 2 com email disponíveis; alvo 10. Página 2 repete (nada novo).
        pages = [
            [_profile("1", has_email=True), _profile("2", has_email=True)],
            [_profile("1", has_email=True), _profile("2", has_email=True)],
        ]
        acc, diag, calls = await self._run(svc, pages, target=10, monkeypatch=monkeypatch)
        assert len(acc) == 2
        assert diag["sources_exhausted"] is True
        assert diag["stop_reason"] == "exhausted"
        assert calls["n"] == 2  # parou ao detectar página sem docids novos

    async def test_max_pages_guardrail(self, monkeypatch):
        svc = _service()
        from lia_config.config import settings
        monkeypatch.setattr(settings, "SEARCH_HYBRID_EMAIL_MAX_PAGES", 2)
        # Cada página traz 1 novo com email, nunca atinge alvo 100.
        pages = [[_profile(f"p{p}-{0}", has_email=True)] for p in range(10)]
        acc, diag, calls = await self._run(svc, pages, target=100, monkeypatch=monkeypatch)
        assert diag["stop_reason"] == "max_pages"
        assert calls["n"] == 2

    async def test_error_stops_gracefully_partial(self, monkeypatch):
        svc = _service()

        async def boom(request, timeout=None, company_id=None):
            raise RuntimeError("pearch down")

        monkeypatch.setattr(svc, "search_candidates", boom)
        base = PearchSearchRequest(query="dev", require_emails=True)
        acc, diag = await svc._accumulate_pearch_with_emails(
            base_request=base, target=10, loop_start_monotonic=time.monotonic()
        )
        assert acc == []
        assert diag["stop_reason"] == "error"
        assert diag["error_message"] is not None

    async def test_target_zero_returns_immediately(self, monkeypatch):
        svc = _service()
        called = {"n": 0}

        async def fake(request, timeout=None, company_id=None):
            called["n"] += 1
            return _response([])

        monkeypatch.setattr(svc, "search_candidates", fake)
        base = PearchSearchRequest(query="dev", require_emails=True)
        acc, diag = await svc._accumulate_pearch_with_emails(
            base_request=base, target=0, loop_start_monotonic=time.monotonic()
        )
        assert acc == []
        assert diag["stop_reason"] == "target_reached"
        assert called["n"] == 0  # não chama Pearch quando alvo já satisfeito


# ---------------------------------------------------------------------------
# refine_search (load-more do modo "Híbrida com email")
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestRefineSearchEmailLoop:

    async def test_refine_require_emails_completes_increment_email_only(self, monkeypatch):
        svc = _service()
        # 2 páginas; só candidatos com email devem retornar e completar o alvo.
        pages = [
            [_profile("a", has_email=True), _profile("b", has_email=False),
             _profile("c", has_email=True)],
            [_profile("d", has_email=True), _profile("e", has_email=True)],
        ]
        calls = {"n": 0, "require_emails": [], "blacklists": []}

        async def fake_search(request, timeout=None, company_id=None):
            calls["require_emails"].append(request.require_emails)
            calls["blacklists"].append(list(request.docid_blacklist or []))
            i = calls["n"]
            calls["n"] += 1
            return _response(pages[i] if i < len(pages) else [])

        monkeypatch.setattr(svc, "search_candidates", fake_search)
        resp = await svc.refine_search(
            thread_id="t-prev",
            additional_query="dev senior",
            limit=4,
            require_emails=True,
            docid_blacklist=["seed1"],
        )
        cands = resp.get_candidates()
        assert len(cands) == 4
        assert all(_profile_has_email(c) for c in cands)
        # require_emails propagado a cada chamada Pearch
        assert all(calls["require_emails"])
        # seed blacklist é respeitada na 1ª página
        assert "seed1" in calls["blacklists"][0]

    async def test_refine_without_require_emails_uses_plain_search(self, monkeypatch):
        svc = _service()
        called = {"n": 0}

        async def fake_search(request, timeout=None, company_id=None):
            called["n"] += 1
            # devolve mix; sem require_emails NÃO filtramos por email aqui
            return _response([_profile("x", has_email=False), _profile("y", has_email=True)])

        monkeypatch.setattr(svc, "search_candidates", fake_search)
        resp = await svc.refine_search(
            thread_id="t", additional_query="dev", limit=10,
        )
        # caminho plano: uma única chamada, sem loop de completude
        assert called["n"] == 1
        assert len(resp.get_candidates()) == 2


# ---------------------------------------------------------------------------
# Guardrail: loop deadline < route deadline (config sanity)
# ---------------------------------------------------------------------------

def test_loop_deadline_below_route_deadline():
    """O deadline interno do loop DEVE ser menor que o da rota, senão o
    asyncio.wait_for da rota cancela o loop e devolve resposta degradada
    vazia (perdendo o parcial honesto)."""
    from lia_config.config import settings
    assert (
        settings.SEARCH_HYBRID_EMAIL_LOOP_DEADLINE_SECONDS
        < settings.SEARCH_CANDIDATES_DEADLINE_SECONDS
    )
