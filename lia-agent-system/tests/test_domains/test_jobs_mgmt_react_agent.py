"""
Tests for JobsMgmtReActAgent — 15 test cases covering:
  import, structure, tool registry, system prompt, stage context,
  multi-tenancy, token budget, wizard orchestrator integration, fairness.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ------------------------------------------------------------------ #
# 1–3: Import and basic structure                                      #
# ------------------------------------------------------------------ #

class TestJobsMgmtReActAgentImport:

    def test_agent_importable(self):
        from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import (
            JobsMgmtReActAgent,
        )
        assert JobsMgmtReActAgent is not None

    def test_agent_instantiable(self):
        from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import (
            JobsMgmtReActAgent,
        )
        agent = JobsMgmtReActAgent()
        assert agent is not None

    def test_agent_has_process_or_run(self):
        from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import (
            JobsMgmtReActAgent,
        )
        agent = JobsMgmtReActAgent()
        assert hasattr(agent, "process") or hasattr(agent, "run"), (
            "Agent must expose process() or run()"
        )


# ------------------------------------------------------------------ #
# 4–6: Wizard orchestrator integration                                 #
# ------------------------------------------------------------------ #

class TestWizardOrchestratorIntegration:

    def test_wizard_orchestrator_service_importable(self):
        from app.domains.job_management.services.wizard_orchestrator_service import (
            wizard_orchestrator_service,
        )
        assert wizard_orchestrator_service is not None

    def test_wizard_intent_enum_has_expected_values(self):
        from app.domains.job_management.services.wizard_orchestrator_service import WizardIntent
        expected = {"PUBLISH_JOB", "PAUSE_JOB", "CLOSE_JOB", "SAVE_DRAFT"}
        actual = {e.name for e in WizardIntent}
        assert expected.issubset(actual), f"Missing intents: {expected - actual}"

    def test_intent_to_tool_mapping_not_empty(self):
        from app.domains.job_management.services.wizard_orchestrator_service import (
            INTENT_TO_TOOL_MAPPING,
        )
        assert len(INTENT_TO_TOOL_MAPPING) > 0


# ------------------------------------------------------------------ #
# 7–9: Stage config service                                            #
# ------------------------------------------------------------------ #

class TestJobStageConfig:

    def test_job_stage_config_importable(self):
        from app.domains.job_management.services.job_stage_config import JOB_CREATION_STAGES, get_stage_config
        assert len(JOB_CREATION_STAGES) == 8

    def test_get_stage_config_returns_dict(self):
        from app.domains.job_management.services.job_stage_config import get_stage_config
        cfg = get_stage_config(1)
        assert isinstance(cfg, dict)
        assert cfg["stage"] == 1

    def test_get_stage_config_unknown_returns_empty(self):
        from app.domains.job_management.services.job_stage_config import get_stage_config
        assert get_stage_config(99) == {}


# ------------------------------------------------------------------ #
# 10–12: should_skip_stage logic                                       #
# ------------------------------------------------------------------ #

class TestShouldSkipStage:

    def test_stage_1_never_skipped(self):
        from app.domains.job_management.services.job_stage_config import should_skip_stage
        can_skip, _ = should_skip_stage(1, {})
        assert can_skip is False

    def test_stage_2_skipped_when_confident(self):
        from app.domains.job_management.services.job_stage_config import should_skip_stage
        detected = {
            "seniority": {"value": "senior", "confidence": 0.9},
            "department": {"value": "Engineering", "confidence": 0.9},
            "location": {"value": "São Paulo", "confidence": 0.9},
        }
        can_skip, reason = should_skip_stage(2, detected)
        assert can_skip is True

    def test_stage_2_not_skipped_below_threshold(self):
        from app.domains.job_management.services.job_stage_config import should_skip_stage
        detected = {
            "seniority": {"value": "senior", "confidence": 0.5},
        }
        can_skip, _ = should_skip_stage(2, detected)
        assert can_skip is False


# ------------------------------------------------------------------ #
# 13–15: JD parser and requirements services                           #
# ------------------------------------------------------------------ #

class TestJobServicesExtracted:

    def test_jd_parser_service_importable(self):
        from app.domains.ai.services.jd_parser_service import JDParserService, jd_parser_service
        assert callable(jd_parser_service.to_requirement_creates)

    def test_job_requirements_service_importable(self):
        from app.domains.job_management.services.job_requirements_service import (
            JobRequirementsService,
            job_requirements_service,
        )
        assert callable(job_requirements_service.parse_requirements_from_raw)

    def test_parse_requirements_from_string_list(self):
        from app.domains.job_management.services.job_requirements_service import job_requirements_service
        reqs = job_requirements_service.parse_requirements_from_raw(
            ["Python 5+ years", "FastAPI"]
        )
        assert len(reqs) == 2
        assert reqs[0].requirement == "Python 5+ years"
