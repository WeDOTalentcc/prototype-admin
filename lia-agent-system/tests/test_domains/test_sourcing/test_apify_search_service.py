import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.sourcing.services.apify_search_service import (
    APIFY_EMAIL_FINDER_COST_USD,
    APIFY_PROFILE_SCRAPE_COST_USD,
    APIFY_SEARCH_COST_USD,
    ApifySearchService,
    SearchPipelineResult,
    StageRecord,
)


@pytest.fixture
def service():
    return ApifySearchService()


@pytest.fixture
def mock_search_results():
    return {
        "items": [
            {"linkedinUrl": "https://linkedin.com/in/john-doe"},
            {"linkedinUrl": "https://linkedin.com/in/jane-smith"},
            {"linkedinUrl": "https://linkedin.com/in/bob-jones"},
        ]
    }


@pytest.fixture
def mock_profile_data():
    return {
        "first_name": "John",
        "last_name": "Doe",
        "headline": "Senior Engineer",
        "location": "São Paulo, BR",
        "summary": "Experienced engineer",
        "skills": ["Python", "FastAPI"],
        "experience": [
            {"title": "Senior Engineer", "companyName": "TechCo"},
        ],
        "source": "linkedin",
    }


class TestApifySearchService:

    @pytest.mark.asyncio
    async def test_search_candidates_full_pipeline(self, service, mock_search_results, mock_profile_data):
        with patch.object(
            service._apify, "run_apify_actor", new_callable=AsyncMock, return_value=mock_search_results
        ) as mock_actor, patch.object(
            service._apify, "_scrape_linkedin_person", new_callable=AsyncMock, return_value=mock_profile_data
        ) as mock_scrape, patch.object(
            service._apify, "_discover_email", new_callable=AsyncMock, return_value=["john@example.com"]
        ) as mock_email:
            result = await service.search_candidates("python developer", location="São Paulo", limit=3)

            assert isinstance(result, SearchPipelineResult)
            assert len(result.candidates) == 3
            assert result.profiles_scraped == 3
            assert result.pipeline_id
            assert result.search_time_seconds >= 0
            assert result.total_cost_usd > 0
            assert len(result.stage_records) > 0
            ops = [sr.operation for sr in result.stage_records]
            assert "apify_search" in ops
            assert "profile_scrape" in ops

            mock_actor.assert_called_once()
            assert mock_scrape.call_count == 3

    @pytest.mark.asyncio
    async def test_search_candidates_empty_results(self, service):
        with patch.object(
            service._apify, "run_apify_actor", new_callable=AsyncMock, return_value={}
        ):
            result = await service.search_candidates("nonexistent query")

            assert isinstance(result, SearchPipelineResult)
            assert len(result.candidates) == 0
            assert result.profiles_scraped == 0
            assert result.total_cost_usd == APIFY_SEARCH_COST_USD

    @pytest.mark.asyncio
    async def test_search_candidates_search_error(self, service):
        with patch.object(
            service._apify, "run_apify_actor",
            new_callable=AsyncMock,
            side_effect=Exception("Connection refused"),
        ):
            with pytest.raises(Exception, match="Connection refused"):
                await service.search_candidates("test query")

    @pytest.mark.asyncio
    async def test_search_candidates_partial_profile_failures(self, service, mock_search_results):
        call_count = 0

        async def _scrape_with_failures(url):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("Scrape failed")
            return {
                "first_name": "Test",
                "last_name": f"User{call_count}",
                "headline": "Dev",
                "source": "linkedin",
            }

        with patch.object(
            service._apify, "run_apify_actor", new_callable=AsyncMock, return_value=mock_search_results
        ), patch.object(
            service._apify, "_scrape_linkedin_person", side_effect=_scrape_with_failures
        ), patch.object(
            service._apify, "_discover_email", new_callable=AsyncMock, return_value=[]
        ):
            result = await service.search_candidates("test", limit=3)

            assert result.profiles_scraped == 2
            assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_step1_extracts_urls(self, service):
        actor_result = {
            "items": [
                {"linkedinUrl": "https://linkedin.com/in/user1"},
                {"profileUrl": "https://linkedin.com/in/user2"},
                {"url": "https://linkedin.com/in/user3"},
                {"url": "https://example.com/not-linkedin"},
                {"linkedinUrl": "https://linkedin.com/in/user1"},
            ]
        }
        with patch.object(
            service._apify, "run_apify_actor", new_callable=AsyncMock, return_value=actor_result
        ):
            urls = await service._step1_search("test", None, 10, [])
            assert len(urls) == 3
            assert all("linkedin.com/in/" in u for u in urls)

    @pytest.mark.asyncio
    async def test_step3_only_for_missing_emails(self, service):
        profiles = [
            {"first_name": "Has", "last_name": "Email", "emails": ["has@email.com"]},
            {"first_name": "No", "last_name": "Email"},
            {"first_name": "Also", "last_name": "NoEmail"},
        ]

        with patch.object(
            service._apify, "_discover_email", new_callable=AsyncMock, return_value=["found@email.com"]
        ) as mock_email:
            found, records = await service._step3_find_emails(profiles, [])
            assert mock_email.call_count == 2
            assert found == 2
            assert len(records) == 2
            assert all(r.operation == "email_finder" for r in records)

    def test_map_to_search_dto(self, service):
        profile = {
            "first_name": "Maria",
            "last_name": "Silva",
            "headline": "Product Manager",
            "location": "São Paulo",
            "skills": ["Strategy", "Analytics"],
            "linkedin_url": "https://linkedin.com/in/maria-silva",
            "emails": ["maria@company.com"],
            "phones": ["+5511999999999"],
            "experience": [
                {"title": "PM Lead", "companyName": "BigCorp"},
            ],
        }
        dto = service.map_to_search_dto(profile)
        assert dto["name"] == "Maria Silva"
        assert dto["source"] == "apify_search"
        assert dto["has_email"] is True
        assert dto["has_phone"] is True
        assert dto["email"] == "maria@company.com"
        assert dto["current_title"] == "PM Lead"
        assert dto["current_company"] == "BigCorp"

    @pytest.mark.asyncio
    async def test_cost_calculation(self, service, mock_search_results, mock_profile_data):
        with patch.object(
            service._apify, "run_apify_actor", new_callable=AsyncMock, return_value=mock_search_results
        ), patch.object(
            service._apify, "_scrape_linkedin_person", new_callable=AsyncMock, return_value=mock_profile_data
        ), patch.object(
            service._apify, "_discover_email", new_callable=AsyncMock, return_value=["email@test.com"]
        ):
            result = await service.search_candidates("test", limit=3)

            expected_cost = (
                APIFY_SEARCH_COST_USD
                + 3 * APIFY_PROFILE_SCRAPE_COST_USD
                + result.emails_found * APIFY_EMAIL_FINDER_COST_USD
            )
            assert abs(result.total_cost_usd - expected_cost) < 0.001
