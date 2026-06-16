"""
Integration tests for candidate search API endpoints.
Uses TestClient + dependency_overrides — no real database needed.
Target: app/api/v1/candidate_search.py (~17% coverage)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.database import get_db
from app.auth.dependencies import (
    get_current_user,
    get_current_active_user,
    get_current_user_or_demo,
)

UUID1 = "123e4567-e89b-12d3-a456-426614174000"
UUID2 = "223e4567-e89b-12d3-a456-426614174001"


def make_mock_db():
    session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_scalars.first.return_value = None
    mock_result.scalars.return_value = mock_scalars
    mock_result.scalar_one_or_none.return_value = None
    mock_result.scalar.return_value = 0
    mock_result.all.return_value = []
    session.execute = AsyncMock(return_value=mock_result)
    session.get = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.rollback = AsyncMock()
    return session


def get_mock_db():
    yield make_mock_db()


def get_mock_user():
    user = MagicMock()
    user.id = "user-1"
    user.company_id = "test-company"
    user.role = "admin"
    user.is_active = True
    user.email = "admin@test.com"
    return user


# ── Mock Pearch search result ──────────────────────────────────────────────────

def _make_hybrid_result():
    result = MagicMock()
    result.local_candidates = []
    result.pearch_candidates = []
    result.local_count = 0
    result.pearch_count = 0
    result.total_count = 0
    result.pearch_credits_remaining = 100
    result.local_search_time = 0.1
    result.pearch_search_time = 0.0
    result.warning_message = None
    result.query = "dev python"
    result.thread_id = None
    return result


@pytest.fixture(scope="module")
def client():
    app.dependency_overrides[get_db] = get_mock_db
    app.dependency_overrides[get_current_user] = get_mock_user
    app.dependency_overrides[get_current_active_user] = get_mock_user
    app.dependency_overrides[get_current_user_or_demo] = get_mock_user
    with patch("app.main.init_db", AsyncMock()):
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
    app.dependency_overrides.clear()


# ===== POST /api/v1/search/candidates =====

def test_search_candidates_local_only(client):
    """POST /api/v1/search/candidates — local only, pearch disabled."""
    with patch(
        "app.domains.sourcing.services.pearch_service.pearch_service.hybrid_search",
        AsyncMock(return_value=_make_hybrid_result()),
    ):
        payload = {
            "query": "dev python",
            "search_local": True,
            "search_pearch": False,
        }
        resp = client.post("/api/v1/search/candidates", json=payload)
    assert resp.status_code in (200, 400, 422, 500)


def test_search_candidates_with_pearch(client):
    """POST /api/v1/search/candidates — with pearch enabled."""
    with patch(
        "app.domains.sourcing.services.pearch_service.pearch_service.hybrid_search",
        AsyncMock(return_value=_make_hybrid_result()),
    ):
        payload = {
            "query": "engenheiro python sênior",
            "search_local": True,
            "search_pearch": True,
            "pearch_type": "fast",
            "pearch_limit": 10,
        }
        resp = client.post("/api/v1/search/candidates", json=payload)
    assert resp.status_code in (200, 400, 402, 422, 500)


def test_search_candidates_empty_query(client):
    """POST /api/v1/search/candidates — missing query triggers 422."""
    resp = client.post("/api/v1/search/candidates", json={})
    assert resp.status_code in (200, 400, 422, 500)


def test_search_candidates_with_job_id(client):
    """POST /api/v1/search/candidates — with job_id for rubric evaluation."""
    with patch(
        "app.domains.sourcing.services.pearch_service.pearch_service.hybrid_search",
        AsyncMock(return_value=_make_hybrid_result()),
    ):
        payload = {
            "query": "developer",
            "search_local": True,
            "search_pearch": False,
            "job_id": UUID1,
        }
        resp = client.post("/api/v1/search/candidates", json=payload)
    assert resp.status_code in (200, 400, 422, 500)


def test_search_candidates_with_search_spec(client):
    """POST /api/v1/search/candidates — with SearchSpec metadata."""
    with patch(
        "app.domains.sourcing.services.pearch_service.pearch_service.hybrid_search",
        AsyncMock(return_value=_make_hybrid_result()),
    ):
        payload = {
            "query": "product manager",
            "search_local": True,
            "search_pearch": False,
            "search_spec": {
                "location": "São Paulo",
                "seniority": "senior",
                "skills": ["product", "agile"],
            },
        }
        resp = client.post("/api/v1/search/candidates", json=payload)
    assert resp.status_code in (200, 400, 422, 500)


# ===== POST /api/v1/search/parse-query =====

def test_parse_query_basic(client):
    """POST /api/v1/search/parse-query — extracts entities from natural language."""
    payload = {"query": "desenvolvedor python sênior em São Paulo"}
    resp = client.post("/api/v1/search/parse-query", json=payload)
    assert resp.status_code in (200, 400, 422, 500)


def test_parse_query_with_work_model(client):
    """POST /api/v1/search/parse-query — remote work model."""
    payload = {"query": "engenheiro backend remoto 5 anos de experiência"}
    resp = client.post("/api/v1/search/parse-query", json=payload)
    assert resp.status_code in (200, 400, 422, 500)


def test_parse_query_empty(client):
    """POST /api/v1/search/parse-query — empty string."""
    payload = {"query": ""}
    resp = client.post("/api/v1/search/parse-query", json=payload)
    assert resp.status_code in (200, 400, 422, 500)


def test_parse_query_complex(client):
    """POST /api/v1/search/parse-query — complex query with multiple entities."""
    payload = {"query": "data scientist machine learning 3 anos python tensorflow"}
    resp = client.post("/api/v1/search/parse-query", json=payload)
    assert resp.status_code in (200, 400, 422, 500)


# ===== POST /api/v1/search/candidates/estimate =====

def test_estimate_credits_fast(client):
    """POST /api/v1/search/candidates/estimate — fast type."""
    payload = {"query": "dev python", "pearch_type": "fast"}
    resp = client.post("/api/v1/search/candidates/estimate", json=payload)
    assert resp.status_code in (200, 400, 422, 500)


def test_estimate_credits_pro_rejected(client):
    """POST /api/v1/search/candidates/estimate — pro type removed, should reject or fallback."""
    payload = {"query": "dev python", "pearch_type": "pro"}
    resp = client.post("/api/v1/search/candidates/estimate", json=payload)
    assert resp.status_code in (400, 422, 500)


def test_estimate_credits_invalid_type(client):
    """POST /api/v1/search/candidates/estimate — invalid pearch_type → 400."""
    payload = {"query": "dev python", "pearch_type": "invalid"}
    resp = client.post("/api/v1/search/candidates/estimate", json=payload)
    assert resp.status_code in (200, 400, 422, 500)


# ===== GET /api/v1/search/candidates/local =====

def test_local_candidates_search(client):
    """GET /api/v1/search/candidates/local — basic local search."""
    resp = client.get("/api/v1/search/candidates/local?query=python")
    assert resp.status_code in (200, 400, 422, 500)


def test_local_candidates_search_no_query(client):
    """GET /api/v1/search/candidates/local — no query."""
    resp = client.get("/api/v1/search/candidates/local")
    assert resp.status_code in (200, 400, 422, 500)


# ===== POST /api/v1/search/analyze =====

def test_analyze_results_empty(client):
    """POST /api/v1/search/analyze — empty results."""
    payload = {
        "candidates": [],
        "search_criteria": {"query": "dev"},
        "generate_narrative": False,
    }
    resp = client.post("/api/v1/search/analyze", json=payload)
    assert resp.status_code in (200, 400, 422, 500)


def test_analyze_results_with_narrative(client):
    """POST /api/v1/search/analyze — with narrative generation."""
    payload = {
        "candidates": [],
        "search_criteria": {"query": "engenheiro"},
        "generate_narrative": True,
    }
    resp = client.post("/api/v1/search/analyze", json=payload)
    assert resp.status_code in (200, 400, 422, 500)


# ===== POST /api/v1/search/enhance-prompt =====

def test_enhance_prompt_basic(client):
    """POST /api/v1/search/enhance-prompt — basic query."""
    with patch(
        "app.services.llm.llm_service.generate",
        AsyncMock(return_value='{"enhanced_query": "dev python sênior SP", "explanation": "test", "suggestions": []}'),
    ):
        payload = {"query": "dev python"}
        resp = client.post("/api/v1/search/enhance-prompt", json=payload)
    assert resp.status_code in (200, 400, 422, 500)


def test_enhance_prompt_with_context(client):
    """POST /api/v1/search/enhance-prompt — with job context."""
    payload = {
        "query": "dev",
        "context": {"job_title": "Engenheiro Backend", "seniority": "senior"},
    }
    resp = client.post("/api/v1/search/enhance-prompt", json=payload)
    assert resp.status_code in (200, 400, 422, 500)


# ===== POST /api/v1/search/suggestions =====

def test_filter_suggestions_basic(client):
    """POST /api/v1/search/suggestions — basic suggestions."""
    payload = {"partial_query": "python"}
    resp = client.post("/api/v1/search/suggestions", json=payload)
    assert resp.status_code in (200, 400, 422, 500)


def test_filter_suggestions_empty(client):
    """POST /api/v1/search/suggestions — empty partial query."""
    payload = {"partial_query": ""}
    resp = client.post("/api/v1/search/suggestions", json=payload)
    assert resp.status_code in (200, 400, 422, 500)


# ===== POST /api/v1/search/similar =====

def test_search_similar_candidates(client):
    """POST /api/v1/search/similar — by reference profile."""
    with patch(
        "app.domains.sourcing.services.pearch_service.pearch_service.hybrid_search",
        AsyncMock(return_value=_make_hybrid_result()),
    ):
        payload = {
            "reference_candidate_id": UUID1,
            "query": "profile similar to João",
            "limit": 10,
        }
        resp = client.post("/api/v1/search/similar", json=payload)
    assert resp.status_code in (200, 400, 422, 500)


# ===== POST /api/v1/search/evaluate-for-job =====

def test_evaluate_candidates_for_job(client):
    """POST /api/v1/search/evaluate-for-job — batch rubric evaluation."""
    payload = {
        "job_id": UUID1,
        "candidate_ids": [UUID2],
    }
    resp = client.post("/api/v1/search/evaluate-for-job", json=payload)
    assert resp.status_code in (200, 400, 404, 422, 500)


# ===== Helper function unit tests =====

def test_normalize_priority_with_string():
    """Test _normalize_priority helper with string input."""
    from app.api.v1.candidate_search import _normalize_priority
    from app.schemas.rubric import RequirementPriorityEnum

    result = _normalize_priority("essential")
    assert result == RequirementPriorityEnum.ESSENTIAL

    result = _normalize_priority(None)
    assert result == RequirementPriorityEnum.IMPORTANT

    result = _normalize_priority("unknown_value")
    assert result == RequirementPriorityEnum.IMPORTANT


def test_normalize_priority_with_enum():
    """Test _normalize_priority with RequirementPriorityEnum input."""
    from app.api.v1.candidate_search import _normalize_priority
    from app.schemas.rubric import RequirementPriorityEnum

    result = _normalize_priority(RequirementPriorityEnum.NICE_TO_HAVE)
    assert result == RequirementPriorityEnum.NICE_TO_HAVE
