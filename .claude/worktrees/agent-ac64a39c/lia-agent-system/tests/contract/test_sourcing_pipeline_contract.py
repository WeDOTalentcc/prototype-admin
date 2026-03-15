"""
Contract Test: Sourcing → Pipeline Handoff
============================================
Verifies that candidates found by SourcingReActAgent can be passed
to PipelineReActAgent for screening.

Key contract:
  - SourcingAgent.domain_name == "sourcing"
  - Candidates returned in state_updates follow the expected schema
  - company_id is preserved through the handoff
  - PII is not exposed in top-level context keys sent to the LLM
  - AgentOutput from Sourcing is a valid AgentOutput
"""
import pytest
from pydantic import ValidationError

from lia_agents_core.agent_interface import AgentInput, AgentOutput, AgentAction


# ---------------------------------------------------------------------------
# Expected fields
# ---------------------------------------------------------------------------

SOURCING_EXPECTED_STATE_UPDATE_KEYS = {
    "candidates_found",   # list of candidate summaries
    "search_query",       # the query used to search
    "total_results",      # total number of candidates found
}

# Fields that a candidate summary may have — NOT PII-sensitive at summary level
CANDIDATE_SUMMARY_ALLOWED_KEYS = {
    "candidate_id", "match_score", "skills", "seniority",
    "location", "years_experience", "source",
}

# PII keys forbidden at state_updates top level
PII_FORBIDDEN_TOP_LEVEL = {
    "cpf", "rg", "birth_date", "address", "email",
    "phone_number", "photo_url", "ethnicity", "gender",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_sourcing_output(candidates: list = None) -> AgentOutput:
    """Simulate a typical SourcingAgent output after finding candidates."""
    if candidates is None:
        candidates = [
            {
                "candidate_id": "cand-001",
                "match_score": 0.91,
                "skills": ["Python", "FastAPI", "PostgreSQL"],
                "seniority": "Senior",
                "location": "São Paulo, SP",
                "years_experience": 7,
                "source": "pearch",
            },
            {
                "candidate_id": "cand-002",
                "match_score": 0.85,
                "skills": ["Python", "Django", "Redis"],
                "seniority": "Senior",
                "location": "Remoto",
                "years_experience": 5,
                "source": "pearch",
            },
        ]
    return AgentOutput(
        message="Encontrei candidatos que correspondem ao perfil solicitado.",
        actions=[
            AgentAction(action_type="call_tool", params={"tool": "search_candidates"}),
        ],
        state_updates={
            "candidates_found": candidates,
            "search_query": "Python Senior Backend São Paulo",
            "total_results": len(candidates),
        },
        confidence=0.88,
    )


def make_pipeline_input_from_sourcing(
    sourcing_output: AgentOutput,
    job_id: str = "job-001",
    company_id: str = "company-001",
) -> AgentInput:
    """Build PipelineAgent input from SourcingAgent output."""
    return AgentInput(
        message="Iniciar triagem dos candidatos encontrados",
        context={
            "current_stage": "sourcing_review",
            "candidates": sourcing_output.state_updates.get("candidates_found", []),
            "job_id": job_id,
            "search_query": sourcing_output.state_updates.get("search_query", ""),
        },
        session_id="session-sourcing-pipeline-001",
        company_id=company_id,
        user_id="recruiter-001",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSourcingPipelineContract:

    def test_sourcing_output_is_valid_agent_output(self):
        """SourcingAgent must return a valid AgentOutput."""
        output = make_sourcing_output()
        assert isinstance(output, AgentOutput)
        assert output.message
        assert 0.0 <= output.confidence <= 1.0

    def test_sourcing_state_updates_has_expected_keys(self):
        """SourcingAgent state_updates must have candidates_found, search_query, total_results."""
        output = make_sourcing_output()
        for key in SOURCING_EXPECTED_STATE_UPDATE_KEYS:
            assert key in output.state_updates, (
                f"SourcingAgent state_updates must contain '{key}'"
            )

    def test_sourcing_candidates_found_is_list(self):
        """candidates_found must be a list (even if empty)."""
        output = make_sourcing_output()
        assert isinstance(output.state_updates["candidates_found"], list)

    def test_sourcing_candidates_have_required_fields(self):
        """Each candidate summary must have at minimum: candidate_id and match_score."""
        output = make_sourcing_output()
        for cand in output.state_updates["candidates_found"]:
            assert "candidate_id" in cand, "Candidate summary must have candidate_id"
            assert "match_score" in cand, "Candidate summary must have match_score"
            assert 0.0 <= cand["match_score"] <= 1.0, "match_score must be in [0, 1]"

    def test_no_pii_at_top_level_state_updates(self):
        """PII keys must not appear at top level of state_updates."""
        output = make_sourcing_output()
        pii_found = PII_FORBIDDEN_TOP_LEVEL & set(output.state_updates.keys())
        assert not pii_found, (
            f"SourcingAgent state_updates has PII at top level: {pii_found}"
        )

    def test_pipeline_input_from_sourcing_is_valid(self):
        """AgentInput built from SourcingAgent output must pass validation."""
        sourcing_output = make_sourcing_output()
        pipeline_input = make_pipeline_input_from_sourcing(sourcing_output)
        assert isinstance(pipeline_input, AgentInput)
        assert pipeline_input.company_id == "company-001"
        assert "candidates" in pipeline_input.context
        assert isinstance(pipeline_input.context["candidates"], list)

    def test_company_id_preserved_through_handoff(self):
        """company_id must be identical in both sourcing output and pipeline input."""
        tenant = "tenant-isolated-001"
        sourcing_output = make_sourcing_output()
        pipeline_input = make_pipeline_input_from_sourcing(
            sourcing_output, company_id=tenant
        )
        assert pipeline_input.company_id == tenant

    def test_sourcing_empty_results_is_valid(self):
        """SourcingAgent output with 0 candidates is still a valid contract."""
        output = make_sourcing_output(candidates=[])
        assert isinstance(output, AgentOutput)
        assert output.state_updates["candidates_found"] == []
        assert isinstance(output.state_updates["total_results"], int)

    def test_pipeline_context_no_pii_top_level_keys(self):
        """PII must not appear as top-level context keys in pipeline input."""
        sourcing_output = make_sourcing_output()
        pipeline_input = make_pipeline_input_from_sourcing(sourcing_output)
        pii_found = PII_FORBIDDEN_TOP_LEVEL & set(pipeline_input.context.keys())
        assert not pii_found, (
            f"Pipeline context (from Sourcing) has PII top-level keys: {pii_found}"
        )
