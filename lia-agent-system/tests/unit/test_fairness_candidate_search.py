"""
TDD: FairnessGuard wired to candidate search endpoints.

Covers:
1. POST /candidates — discriminatory query → HTTP 400 fairness_blocked
2. POST /candidates — clean query → no fairness block (passes through)
3. POST /archetypes/from-description — discriminatory description → HTTP 400 fairness_blocked
4. POST /archetypes/from-description — clean description → no fairness block
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock


class _FairnessBlocked:
    is_blocked = True
    category = "gender"
    blocked_terms = ["homens"]
    educational_message = (
        "Filtrar candidatos por genero viola a CLT Art. 373-A e LGPD Art. 20."
    )
    soft_warnings: list = []


class _FairnessOK:
    is_blocked = False
    category = None
    blocked_terms = []
    educational_message = None
    soft_warnings: list = []


class TestSearchCandidatesFairnessGuard:

    def _make_search_request(self, query: str):
        from app.api.v1.candidate_search._shared import SearchRequestDTO
        return SearchRequestDTO(query=query)

    @pytest.mark.asyncio
    async def test_discriminatory_query_returns_400(self):
        from fastapi import HTTPException
        from app.api.v1.candidate_search.search import search_candidates

        request = self._make_search_request("apenas homens abaixo de 30 anos")
        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_pearch = AsyncMock()
        mock_rubric = AsyncMock()
        mock_credit = AsyncMock()

        with patch("app.api.v1.candidate_search.search._fairness_guard") as mock_guard:
            mock_guard.check.return_value = _FairnessBlocked()
            with pytest.raises(HTTPException) as exc_info:
                await search_candidates(
                    request=request,
                    db=mock_db,
                    current_user=mock_user,
                    pearch_svc=mock_pearch,
                    rubric_svc=mock_rubric,
                    _cs=mock_credit,
                    company_id="company-uuid-123",
                )
        assert exc_info.value.status_code == 400
        detail = exc_info.value.detail
        assert detail["fairness_blocked"] is True
        assert "educational_message" in detail

    @pytest.mark.asyncio
    async def test_clean_query_passes_fairness_check(self):
        from app.api.v1.candidate_search.search import search_candidates

        request = self._make_search_request("engenheiro python senior")
        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_pearch = AsyncMock()
        mock_rubric = AsyncMock()
        mock_credit = AsyncMock()

        hybrid_result = MagicMock()
        hybrid_result.local_candidates = []
        hybrid_result.pearch_candidates = []
        hybrid_result.local_count = 0
        hybrid_result.pearch_count = 0
        hybrid_result.thread_id = "t1"
        hybrid_result.query = "engenheiro python senior"
        hybrid_result.pearch_credits_remaining = None
        hybrid_result.local_search_time = 0.0
        hybrid_result.pearch_search_time = 0.0
        hybrid_result.warning_message = None
        hybrid_result.filtered_no_contact = 0
        hybrid_result.sources_exhausted = False
        hybrid_result.enrichment_attempted = 0
        mock_pearch.hybrid_search = AsyncMock(return_value=hybrid_result)
        mock_credit.consume_action = AsyncMock(return_value=(True, 100))
        mock_credit.get_balance = AsyncMock(return_value={"low_balance_warning": False})

        with patch("app.api.v1.candidate_search.search._fairness_guard") as mock_guard:
            mock_guard.check.return_value = _FairnessOK()
            with patch(
                "app.api.v1.candidate_search.search.enrich_and_filter_candidates",
                new_callable=AsyncMock,
                return_value=[],
            ):
                result = await search_candidates(
                    request=request,
                    db=mock_db,
                    current_user=mock_user,
                    pearch_svc=mock_pearch,
                    rubric_svc=mock_rubric,
                    _cs=mock_credit,
                    company_id="company-uuid-123",
                )
        mock_guard.check.assert_called_once()
        assert result is not None


class TestArchetypesFromDescriptionFairnessGuard:

    def _make_description_request(self, description: str):
        from app.api.v1.candidate_search.archetypes import ArchetypeFromDescriptionRequest
        return ArchetypeFromDescriptionRequest(description=description)

    @pytest.mark.asyncio
    async def test_discriminatory_description_returns_400(self):
        from fastapi import HTTPException
        from app.api.v1.candidate_search.archetypes import generate_archetype_from_description

        request = self._make_description_request(
            "Quero candidato do sexo masculino, maximo 35 anos, sem filhos preferivel"
        )
        mock_db = AsyncMock()

        with patch("app.api.v1.candidate_search.archetypes._fairness_guard") as mock_guard:
            mock_guard.check.return_value = _FairnessBlocked()
            with pytest.raises(HTTPException) as exc_info:
                await generate_archetype_from_description(
                    request=request,
                    db=mock_db,
                    company_id="company-uuid-123",
                )
        assert exc_info.value.status_code == 400
        detail = exc_info.value.detail
        assert detail["fairness_blocked"] is True

    @pytest.mark.asyncio
    async def test_clean_description_passes_guard(self):
        import json
        from app.api.v1.candidate_search.archetypes import generate_archetype_from_description

        request = self._make_description_request(
            "Analista de dados com experiencia em Python, SQL e machine learning, nivel pleno"
        )
        mock_db = AsyncMock()

        with patch("app.api.v1.candidate_search.archetypes._fairness_guard") as mock_guard:
            mock_guard.check.return_value = _FairnessOK()
            mock_provider = MagicMock()
            mock_provider.generate_with_fallback = AsyncMock(
                return_value=json.dumps({
                    "name": "Analista de Dados",
                    "description": "Analista com Python e ML",
                    "query": "analista de dados python machine learning",
                    "filters": {"seniority": "pleno", "experience_years_min": 2, "skills": ["python", "sql"]},
                    "tags": ["dados", "python"],
                    "industry": "tecnologia",
                    "seniority": "pleno",
                })
            )
            with patch(
                "app.shared.providers.llm_factory.get_provider_for_tenant",
                return_value=mock_provider,
            ):
                mock_db.execute = AsyncMock(return_value=MagicMock())
                mock_db.commit = AsyncMock()
                mock_db.add = MagicMock()

                result = await generate_archetype_from_description(
                    request=request,
                    db=mock_db,
                    company_id="company-uuid-123",
                )

        mock_guard.check.assert_called_once()
        assert result is not None
