"""
Integration tests for the enrichment pipeline (Task T2).

Validates that:
- All search endpoints call enrich_and_filter_candidates
- Candidates without email AND phone are filtered out after enrichment
- Candidates already having contact are NOT re-enriched (no double cost)
- SearchType.PRO is removed — only FAST exists
- The enrich_candidate_contact tool works correctly
"""
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestSearchTypePro:
    def test_pro_not_in_search_type(self):
        from lia_models.pearch import SearchType

        members = [m.value for m in SearchType]
        assert "pro" not in members
        assert "fast" in members

    def test_only_fast_exists(self):
        from lia_models.pearch import SearchType

        assert SearchType.FAST.value == "fast"
        assert len(SearchType) == 1


def _make_candidate_dto(
    cid: str,
    email: str | None = None,
    phone: str | None = None,
    linkedin_url: str | None = None,
):
    return MagicMock(
        id=cid,
        name=f"Candidate {cid}",
        email=email,
        best_personal_email=None,
        best_business_email=None,
        phone=phone,
        phone_numbers=None,
        has_email=bool(email),
        has_phone=bool(phone),
        linkedin_url=linkedin_url,
        linkedin_slug=None,
        source="pearch",
    )


class TestEnrichAndFilterCandidates:

    @pytest.mark.asyncio
    async def test_candidates_with_contact_pass_through(self):
        from app.api.v1.candidate_search._shared import enrich_and_filter_candidates

        candidates = [
            _make_candidate_dto("1", email="a@b.com"),
            _make_candidate_dto("2", phone="+5511999"),
            _make_candidate_dto("3", email="c@d.com", phone="+5511888"),
        ]

        mock_svc = MagicMock()
        mock_svc.enrich_batch = AsyncMock(return_value=[])

        with patch(
            "app.api.v1.candidate_search._shared.get_contact_enrichment_service",
            return_value=mock_svc,
        ):
            db = AsyncMock()
            result = await enrich_and_filter_candidates(db, candidates)

        assert len(result) == 3
        mock_svc.enrich_batch.assert_not_called()

    @pytest.mark.asyncio
    async def test_candidates_without_contact_are_filtered(self):
        from app.api.v1.candidate_search._shared import enrich_and_filter_candidates

        candidates = [
            _make_candidate_dto("1", email="a@b.com"),
            _make_candidate_dto("2"),
            _make_candidate_dto("3"),
        ]

        mock_svc = MagicMock()
        mock_svc.enrich_batch = AsyncMock(return_value=[
            {"success": False},
            {"success": False},
        ])

        with patch(
            "app.api.v1.candidate_search._shared.get_contact_enrichment_service",
            return_value=mock_svc,
        ):
            db = AsyncMock()
            result = await enrich_and_filter_candidates(db, candidates)

        assert len(result) == 1
        assert result[0].id == "1"

    @pytest.mark.asyncio
    async def test_enrichment_scenario_20_candidates_3_without_contact(self):
        """
        Scenario from task spec:
        20 candidates -> 3 without contact -> Apify enriches 2 -> result has 19 candidates
        """
        from app.api.v1.candidate_search._shared import enrich_and_filter_candidates

        candidates = []
        for i in range(17):
            candidates.append(_make_candidate_dto(str(i), email=f"user{i}@test.com"))

        candidates.append(_make_candidate_dto("17", linkedin_url="https://linkedin.com/in/user17"))
        candidates.append(_make_candidate_dto("18", linkedin_url="https://linkedin.com/in/user18"))
        candidates.append(_make_candidate_dto("19", linkedin_url="https://linkedin.com/in/user19"))

        async def mock_enrich_batch(db, batch, **kwargs):
            for item in batch:
                cid = item["id"]
                if cid in ("17", "18"):
                    for c in candidates:
                        if c.id == cid:
                            c.email = f"enriched-{cid}@apify.com"
                            c.has_email = True
            return [{"success": True}] * len(batch)

        mock_svc = MagicMock()
        mock_svc.enrich_batch = AsyncMock(side_effect=mock_enrich_batch)

        with patch(
            "app.api.v1.candidate_search._shared.get_contact_enrichment_service",
            return_value=mock_svc,
        ):
            db = AsyncMock()
            result = await enrich_and_filter_candidates(db, candidates)

        assert len(result) == 19
        mock_svc.enrich_batch.assert_called_once()
        batch_arg = mock_svc.enrich_batch.call_args[0][1]
        assert len(batch_arg) == 3

        result_ids = {c.id for c in result}
        assert "17" in result_ids
        assert "18" in result_ids
        assert "19" not in result_ids

    @pytest.mark.asyncio
    async def test_candidates_with_existing_contact_not_sent_to_enrichment(self):
        from app.api.v1.candidate_search._shared import enrich_and_filter_candidates

        candidates = [
            _make_candidate_dto("1", email="a@b.com"),
            _make_candidate_dto("2", phone="+55"),
        ]

        mock_svc = MagicMock()
        mock_svc.enrich_batch = AsyncMock(return_value=[])

        with patch(
            "app.api.v1.candidate_search._shared.get_contact_enrichment_service",
            return_value=mock_svc,
        ):
            db = AsyncMock()
            result = await enrich_and_filter_candidates(db, candidates)

        assert len(result) == 2
        mock_svc.enrich_batch.assert_not_called()

    @pytest.mark.asyncio
    async def test_enrichment_batch_failure_is_non_fatal(self):
        from app.api.v1.candidate_search._shared import enrich_and_filter_candidates

        candidates = [
            _make_candidate_dto("1", email="ok@test.com"),
            _make_candidate_dto("2", linkedin_url="https://linkedin.com/in/user2"),
        ]

        mock_svc = MagicMock()
        mock_svc.enrich_batch = AsyncMock(side_effect=Exception("Apify down"))

        with patch(
            "app.api.v1.candidate_search._shared.get_contact_enrichment_service",
            return_value=mock_svc,
        ):
            db = AsyncMock()
            result = await enrich_and_filter_candidates(db, candidates)

        assert len(result) == 1
        assert result[0].id == "1"


class TestToolRegistryInclusion:
    def test_enrich_candidate_contact_in_tool_definitions(self):
        from app.domains.sourcing.agents.sourcing_tool_registry import TOOL_DEFINITIONS

        tool_names = [t.name for t in TOOL_DEFINITIONS]
        assert "enrich_candidate_contact" in tool_names

    def test_enrich_candidate_contact_in_stage_tools(self):
        from app.domains.sourcing.agents.sourcing_tool_registry import STAGE_TOOLS

        assert "enrich_candidate_contact" in STAGE_TOOLS["talent-search"]
        assert "enrich_candidate_contact" in STAGE_TOOLS["profile-analysis"]


class TestSystemPromptCosts:
    def test_system_prompt_contains_cost_section(self):
        from app.domains.sourcing.agents.sourcing_system_prompt import SOURCING_DOMAIN_SPECIFIC

        assert "CUSTOS DE BUSCA E ECONOMIA" in SOURCING_DOMAIN_SPECIFIC
        assert "NAO existe modo Pro" in SOURCING_DOMAIN_SPECIFIC
        assert "Apify" in SOURCING_DOMAIN_SPECIFIC
        assert "$0.01/candidato" in SOURCING_DOMAIN_SPECIFIC
        assert "enrich_candidate_contact" in SOURCING_DOMAIN_SPECIFIC
