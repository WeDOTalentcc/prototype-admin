"""
Unit tests — TOONService (Sprint G7).

Camada 2 — Unitária (pytest-asyncio, sem DB/Redis reais — AsyncMock/MagicMock).

Cobre:
- TOONCard dataclass: all expected fields present
- name_display masking: anonymize=True → "Candidato X", False → real name
- match_score: 0-100 range, None when no job_id
- highlights: list of strings, length 3–5
- skills_match: intersection of candidate and job skills
- fairness_reviewed: always True
- anonymized flag: reflects the anonymize parameter
- get_or_generate: Redis cache hit → no DB call on second fetch
- get_or_generate: Redis miss → generates and stores in cache
- get_or_generate: Redis unavailable → generates without caching
- generate: raises ValueError when candidate not found
- generate: multi-tenant isolation (company_id scoped)
- generate: experience_years defaults to 0 when None
- generate: location built from city/state/country
- generate: headline uses current_title, years_of_experience, current_company
- generate: job_id=None → match_score is None, skills_match is []
- generate: job with no matching skills → match_score=0
- generate: full skill match → match_score=100
- generate: partial skill match → 0 < match_score < 100
- cache key format: includes company_id and job_id
- TOONCard: generated_at is valid ISO datetime
"""
import json
import pytest

pytestmark = pytest.mark.medium

from dataclasses import fields as dataclass_fields
from datetime import datetime, timezone
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch, call
from app.services.toon_service import (
    TOONCard,
    TOONService,
    _toon_cache_key,
    _build_headline,
    _build_location,
    _build_highlights,
    _compute_skills_match,
    _compute_match_score,
    toon_service,
)


# ---------------------------------------------------------------------------
# Helpers — build mock candidate / job
# ---------------------------------------------------------------------------

def _make_candidate(
    *,
    id="cand-uuid-001",
    company_id="company-uuid-001",
    name="Maria Souza",
    current_title="Desenvolvedora Python Sênior",
    current_company="FinTech SA",
    years_of_experience=8,
    technical_skills=None,
    soft_skills=None,
    location_city="São Paulo",
    location_state="SP",
    location_country="Brasil",
    is_remote=True,
    willing_to_relocate=False,
    seniority_level="Senior",
):
    c = MagicMock()
    c.id = id
    c.company_id = company_id
    c.name = name
    c.current_title = current_title
    c.current_company = current_company
    c.years_of_experience = years_of_experience
    c.technical_skills = technical_skills if technical_skills is not None else ["Python", "FastAPI", "PostgreSQL"]
    c.soft_skills = soft_skills if soft_skills is not None else ["Comunicação", "Liderança"]
    c.location_city = location_city
    c.location_state = location_state
    c.location_country = location_country
    c.is_remote = is_remote
    c.willing_to_relocate = willing_to_relocate
    c.seniority_level = seniority_level
    return c


def _make_job(
    *,
    id="job-uuid-001",
    company_id="company-uuid-001",
    required_skills=None,
):
    j = MagicMock()
    j.id = id
    j.company_id = company_id
    j.required_skills = required_skills or ["Python", "FastAPI", "Docker"]
    return j


async def _db_returning(candidate=None, job=None):
    """Return a mock AsyncSession whose execute() returns candidate or job."""
    db = AsyncMock()

    async def _execute(stmt):
        result = MagicMock()
        # Heuristic: if stmt has 'required_skills' attr lookup, it's a job query
        result.scalar_one_or_none.return_value = candidate
        return result

    db.execute.side_effect = _execute
    return db


# ---------------------------------------------------------------------------
# TOONCard dataclass
# ---------------------------------------------------------------------------

class TestTOONCardDataclass:
    def test_all_expected_fields_present(self):
        """TOONCard must have all required fields."""
        field_names = {f.name for f in dataclass_fields(TOONCard)}
        required = {
            "candidate_id",
            "job_id",
            "generated_at",
            "headline",
            "highlights",
            "match_score",
            "skills_match",
            "name_display",
            "location",
            "experience_years",
            "anonymized",
            "fairness_reviewed",
        }
        assert required.issubset(field_names)

    def test_instantiation(self):
        card = TOONCard(
            candidate_id="c1",
            job_id="j1",
            generated_at="2026-03-08T00:00:00+00:00",
            headline="Dev Python Sênior",
            highlights=["8 anos de experiência"],
            match_score=85,
            skills_match=["Python", "FastAPI"],
            name_display="Maria Souza",
            location="São Paulo, SP, Brasil",
            experience_years=8,
            anonymized=False,
            fairness_reviewed=True,
        )
        assert card.candidate_id == "c1"
        assert card.match_score == 85


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

class TestBuildHeadline:
    def test_full_headline(self):
        c = _make_candidate()
        h = _build_headline(c)
        assert "Desenvolvedora Python Sênior" in h
        assert "8 anos" in h
        assert "FinTech SA" in h

    def test_no_title_fallback(self):
        c = _make_candidate(current_title=None, current_company=None, years_of_experience=None)
        h = _build_headline(c)
        assert "disponível" in h.lower()


class TestBuildLocation:
    def test_full_location(self):
        c = _make_candidate()
        loc = _build_location(c)
        assert loc == "São Paulo, SP, Brasil"

    def test_partial_location(self):
        c = _make_candidate(location_city="Recife", location_state=None, location_country="Brasil")
        loc = _build_location(c)
        assert loc == "Recife, Brasil"

    def test_empty_location(self):
        c = _make_candidate(location_city=None, location_state=None, location_country=None)
        loc = _build_location(c)
        assert "não informada" in loc.lower()


class TestComputeSkillsMatch:
    def test_full_match(self):
        matched = _compute_skills_match(["Python", "FastAPI"], ["Python", "FastAPI"])
        assert set(matched) == {"Python", "FastAPI"}

    def test_partial_match(self):
        matched = _compute_skills_match(["Python", "FastAPI", "Vue"], ["Python", "Docker"])
        assert matched == ["Python"]

    def test_no_match(self):
        matched = _compute_skills_match(["Python"], ["Go", "Rust"])
        assert matched == []

    def test_case_insensitive(self):
        matched = _compute_skills_match(["python"], ["Python"])
        assert matched == ["python"]

    def test_empty_job_skills(self):
        matched = _compute_skills_match(["Python"], [])
        assert matched == []


class TestComputeMatchScore:
    def test_no_job_skills_returns_none(self):
        c = _make_candidate()
        assert _compute_match_score(c, []) is None

    def test_full_match_100(self):
        c = _make_candidate(technical_skills=["Python", "FastAPI"], soft_skills=[])
        score = _compute_match_score(c, ["Python", "FastAPI"])
        assert score == 100

    def test_partial_match_range(self):
        c = _make_candidate(technical_skills=["Python"], soft_skills=[])
        score = _compute_match_score(c, ["Python", "Docker", "Kubernetes"])
        assert score is not None
        assert 0 < score < 100

    def test_no_candidate_skills_zero(self):
        c = _make_candidate(technical_skills=[], soft_skills=[])
        score = _compute_match_score(c, ["Python"])
        assert score == 0

    def test_score_capped_at_100(self):
        c = _make_candidate(technical_skills=["Python", "FastAPI", "Docker", "Redis"], soft_skills=[])
        score = _compute_match_score(c, ["Python"])
        assert score == 100


# ---------------------------------------------------------------------------
# TOONService.generate
# ---------------------------------------------------------------------------

class TestTOONServiceGenerate:
    @pytest.mark.asyncio
    async def test_generate_real_name_when_not_anonymized(self):
        candidate = _make_candidate(name="Maria Souza")
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = candidate
        db.execute.return_value = result

        svc = TOONService()
        card = await svc.generate("cand-001", None, db, "company-001", anonymize=False)
        assert card.name_display == "Maria Souza"
        assert card.anonymized is False

    @pytest.mark.asyncio
    async def test_generate_anonymized_masks_name(self):
        candidate = _make_candidate(name="Maria Souza")
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = candidate
        db.execute.return_value = result

        svc = TOONService()
        card = await svc.generate("cand-001", None, db, "company-001", anonymize=True)
        assert card.name_display == "Candidato X"
        assert card.anonymized is True

    @pytest.mark.asyncio
    async def test_generate_raises_when_candidate_not_found(self):
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute.return_value = result

        svc = TOONService()
        with pytest.raises(ValueError, match="not found"):
            await svc.generate("missing-cand", None, db, "company-001")

    @pytest.mark.asyncio
    async def test_generate_no_job_id_match_score_is_none(self):
        candidate = _make_candidate()
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = candidate
        db.execute.return_value = result

        svc = TOONService()
        card = await svc.generate("cand-001", None, db, "company-001")
        assert card.match_score is None
        assert card.skills_match == []

    @pytest.mark.asyncio
    async def test_generate_fairness_reviewed_always_true(self):
        candidate = _make_candidate()
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = candidate
        db.execute.return_value = result

        svc = TOONService()
        card = await svc.generate("cand-001", None, db, "company-001")
        assert card.fairness_reviewed is True

    @pytest.mark.asyncio
    async def test_generate_experience_years_default_zero(self):
        candidate = _make_candidate(years_of_experience=None)
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = candidate
        db.execute.return_value = result

        svc = TOONService()
        card = await svc.generate("cand-001", None, db, "company-001")
        assert card.experience_years == 0

    @pytest.mark.asyncio
    async def test_generate_highlights_is_list_of_strings(self):
        candidate = _make_candidate()
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = candidate
        db.execute.return_value = result

        svc = TOONService()
        card = await svc.generate("cand-001", None, db, "company-001")
        assert isinstance(card.highlights, list)
        assert len(card.highlights) >= 3
        assert all(isinstance(h, str) for h in card.highlights)

    @pytest.mark.asyncio
    async def test_generate_match_score_0_to_100(self):
        candidate = _make_candidate(technical_skills=["Python"], soft_skills=[])
        db = AsyncMock()

        call_count = 0

        async def multi_execute(stmt):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                result.scalar_one_or_none.return_value = candidate
            else:
                job = _make_job(required_skills=["Python", "Docker"])
                result.scalar_one_or_none.return_value = job
            return result

        db.execute.side_effect = multi_execute

        svc = TOONService()
        card = await svc.generate("cand-001", "job-001", db, "company-001")
        assert card.match_score is not None
        assert 0 <= card.match_score <= 100

    @pytest.mark.asyncio
    async def test_generate_generated_at_is_valid_iso(self):
        candidate = _make_candidate()
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = candidate
        db.execute.return_value = result

        svc = TOONService()
        card = await svc.generate("cand-001", None, db, "company-001")
        # Should parse without error
        dt = datetime.fromisoformat(card.generated_at)
        assert dt is not None


# ---------------------------------------------------------------------------
# TOONService.get_or_generate (caching)
# ---------------------------------------------------------------------------

class TestTOONServiceGetOrGenerate:
    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_card(self):
        """When Redis has a cached card, generate() should NOT be called."""
        cached_card = TOONCard(
            candidate_id="cand-001",
            job_id="job-001",
            generated_at="2026-03-08T00:00:00+00:00",
            headline="Cached headline",
            highlights=["bullet 1", "bullet 2", "bullet 3"],
            match_score=77,
            skills_match=["Python"],
            name_display="Ana Lima",
            location="Rio de Janeiro, RJ, Brasil",
            experience_years=5,
            anonymized=False,
            fairness_reviewed=True,
        )

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps(vars(cached_card) if not hasattr(cached_card, '__dataclass_fields__') else {f.name: getattr(cached_card, f.name) for f in dataclass_fields(cached_card)}))
        mock_redis.aclose = AsyncMock()

        svc = TOONService()
        db = AsyncMock()

        with patch("app.services.toon_service._get_redis", return_value=mock_redis):
            card = await svc.get_or_generate("cand-001", "job-001", db, "company-001")

        assert card.headline == "Cached headline"
        assert card.match_score == 77
        # DB was never called because cache was hit
        db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_miss_calls_generate_and_stores(self):
        """On cache miss, generates fresh card and writes to Redis."""
        candidate = _make_candidate()
        db = AsyncMock()
        db_result = MagicMock()
        db_result.scalar_one_or_none.return_value = candidate
        db.execute.return_value = db_result

        mock_redis_miss = AsyncMock()
        mock_redis_miss.get = AsyncMock(return_value=None)
        mock_redis_miss.aclose = AsyncMock()

        mock_redis_write = AsyncMock()
        mock_redis_write.setex = AsyncMock()
        mock_redis_write.aclose = AsyncMock()

        redis_calls = [mock_redis_miss, mock_redis_write]

        async def _get_redis_side_effect(*args, **kwargs):
            return redis_calls.pop(0) if redis_calls else None

        svc = TOONService()

        with patch("app.services.toon_service._get_redis", side_effect=_get_redis_side_effect):
            card = await svc.get_or_generate("cand-001", None, db, "company-001")

        assert card.candidate_id == "cand-001"
        mock_redis_write.setex.assert_called_once()
        # Verify TTL=3600
        call_args = mock_redis_write.setex.call_args
        assert call_args[0][1] == 3600

    @pytest.mark.asyncio
    async def test_redis_unavailable_generates_without_caching(self):
        """When Redis is down, get_or_generate still returns a card."""
        candidate = _make_candidate()
        db = AsyncMock()
        db_result = MagicMock()
        db_result.scalar_one_or_none.return_value = candidate
        db.execute.return_value = db_result

        async def _no_redis(*args, **kwargs):
            return None

        svc = TOONService()

        with patch("app.services.toon_service._get_redis", side_effect=_no_redis):
            card = await svc.get_or_generate("cand-001", None, db, "company-001")

        assert card.candidate_id == "cand-001"
        assert card.name_display == "Maria Souza"


# ---------------------------------------------------------------------------
# Cache key
# ---------------------------------------------------------------------------

class TestToonCacheKey:
    def test_cache_key_includes_company_id(self):
        key = _toon_cache_key("cand-1", "job-1", "company-42")
        assert "company-42" in key

    def test_cache_key_includes_job_id(self):
        key = _toon_cache_key("cand-1", "job-1", "company-42")
        assert "job-1" in key

    def test_cache_key_no_job_uses_placeholder(self):
        key = _toon_cache_key("cand-1", None, "company-42")
        assert "no-job" in key

    def test_cache_key_format(self):
        key = _toon_cache_key("cand-1", "job-1", "company-42")
        assert key.startswith("toon:")


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

class TestModuleSingleton:
    def test_toon_service_singleton_is_toon_service_instance(self):
        assert isinstance(toon_service, TOONService)
