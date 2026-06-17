"""Sensores do endpoint de feedback de busca (like/dislike) — anti-ghost-endpoint.

Bug: frontend chamava POST /search/feedback e GET /search/feedback/by-search, que
nao existiam (404) -> SearchFeedbackButtons revertia o estado -> "nada acontece".
Estes testes pinam: rota existe, insere novo, faz upsert, e by-search re-hidrata.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.api.v1.candidate_search.feedback import (
    SearchFeedbackRequest,
    submit_search_feedback,
    get_search_feedback_by_fingerprint,
)
from lia_models.search_feedback import SearchFeedback


def _db_with_existing(existing):
    db = MagicMock()
    result = MagicMock()
    result.scalars.return_value.first.return_value = existing
    db.execute = AsyncMock(return_value=result)
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


def _db_with_rows(rows):
    db = MagicMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows
    db.execute = AsyncMock(return_value=result)
    return db


class _User:
    id = "user-1"


@pytest.mark.asyncio
async def test_routes_registered():
    from app.api.v1.candidate_search import router
    paths = {getattr(r, "path", "") for r in router.routes}
    assert "/search/feedback" in paths
    assert "/search/feedback/by-search" in paths


@pytest.mark.asyncio
async def test_insert_new_feedback():
    db = _db_with_existing(None)
    req = SearchFeedbackRequest(
        candidate_id="cand-1", feedback_type="like",
        search_fingerprint="fp-abc", candidate_name="Ana",
    )
    resp = await submit_search_feedback(req, db=db, current_user=_User(), company_id="comp-A")
    assert resp.success is True
    assert resp.feedback_type == "like"
    db.add.assert_called_once()
    added = db.add.call_args.args[0]
    assert isinstance(added, SearchFeedback)
    assert added.company_id == "comp-A"
    assert added.candidate_id == "cand-1"
    assert added.feedback_type == "like"
    assert added.user_id == "user-1"
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_upsert_existing_feedback():
    existing = SearchFeedback(
        id="x", company_id="comp-A", candidate_id="cand-1",
        user_id="user-1", search_fingerprint="fp-abc", feedback_type="like",
    )
    db = _db_with_existing(existing)
    req = SearchFeedbackRequest(
        candidate_id="cand-1", feedback_type="dislike", search_fingerprint="fp-abc",
    )
    resp = await submit_search_feedback(req, db=db, current_user=_User(), company_id="comp-A")
    assert resp.success is True
    assert existing.feedback_type == "dislike"  # atualizado in-place
    db.add.assert_not_called()  # upsert, nao insere
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_by_search_rehydrates_map():
    rows = [
        SearchFeedback(id="1", company_id="comp-A", candidate_id="c1", user_id="u", feedback_type="like"),
        SearchFeedback(id="2", company_id="comp-A", candidate_id="c2", user_id="u", feedback_type="dislike"),
    ]
    db = _db_with_rows(rows)
    out = await get_search_feedback_by_fingerprint(fingerprint="fp-abc", db=db, company_id="comp-A")
    assert out == {"feedbacks": {"c1": "like", "c2": "dislike"}}


def test_request_forbids_company_id():
    # REGRA 2: company_id nunca no payload
    import pydantic
    with pytest.raises(pydantic.ValidationError):
        SearchFeedbackRequest(candidate_id="c", feedback_type="like", company_id="x")
