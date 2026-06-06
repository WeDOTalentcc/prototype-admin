"""P1-3: aprendizado por feedback no funil — boost stateless cross-tenant-safe.

(a) apply_feedback_boost: helper puro que ajusta o Match score (+/- pts) com
    proveniencia honesta, clamp 0-100, ignora sem-score/sem-feedback.
(b) load_search_feedback: loader STATELESS escopado por company_id (mata o leak
    do singleton compartilhado) + fail-closed sem company_id.
"""
import contextlib
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock


def test_apply_feedback_boost_like_dislike_clamp_provenance():
    from app.api.v1.candidate_search._shared import apply_feedback_boost

    cands = [
        SimpleNamespace(id="a", score=80.0, match_summary=None),   # like -> 90
        SimpleNamespace(id="b", score=95.0, match_summary="x"),    # like -> 100 (clamp)
        SimpleNamespace(id="c", score=5.0, match_summary=None),    # dislike -> 0 (clamp)
        SimpleNamespace(id="d", score=50.0, match_summary=None),   # sem feedback -> intacto
        SimpleNamespace(id="e", score=None, match_summary=None),   # sem score -> skip
    ]
    apply_feedback_boost(cands, {"a": "like", "b": "like", "c": "dislike"}, 10.0)

    assert cands[0].score == 90.0
    assert cands[1].score == 100.0
    assert cands[2].score == 0.0
    assert cands[3].score == 50.0
    assert cands[4].score is None
    # proveniencia honesta (REGRA 4)
    assert "feedback do recrutador" in (cands[0].match_summary or "")
    assert "+10" in (cands[0].match_summary or "")
    assert "-10" in (cands[2].match_summary or "")
    # sem feedback nao anota nada
    assert "feedback" not in (cands[3].match_summary or "")


async def test_load_search_feedback_stateless_and_scoped(monkeypatch):
    from app.domains.cv_screening.services.lia_score_service import lia_score_service

    @contextlib.asynccontextmanager
    async def fake_ts(company_id):
        db = MagicMock()
        res = MagicMock()
        res.all.return_value = [("cand-A", "like"), ("cand-B", "dislike")]
        db.execute = AsyncMock(return_value=res)
        yield db

    monkeypatch.setattr("app.core.database.tenant_session", fake_ts)
    fb = await lia_score_service.load_search_feedback(["cand-A", "cand-B"], company_id="co-1")
    assert fb == {"cand-A": "like", "cand-B": "dislike"}
    # leak fix: NENHUM estado de instancia compartilhado criado (singleton)
    assert not hasattr(lia_score_service, "_search_feedback_cache")


async def test_load_search_feedback_fail_closed():
    from app.domains.cv_screening.services.lia_score_service import lia_score_service

    # company_id vazio -> {} (fail-closed multi-tenancy)
    assert await lia_score_service.load_search_feedback(["a"], company_id="") == {}
    # sem ids -> {}
    assert await lia_score_service.load_search_feedback([], company_id="co-1") == {}
