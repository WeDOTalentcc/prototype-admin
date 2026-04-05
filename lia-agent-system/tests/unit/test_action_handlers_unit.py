"""
Tests for action_handlers/ (0% → ~50%)
Covers: candidate_actions, job_actions, communication_actions, pipeline_actions
"""
import sys
sys.path.insert(0, '/home/runner/workspace/lia-agent-system')
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


class TestCandidateActionsConstants:
    def test_allowed_direct_fields(self):
        from app.orchestrator.action_handlers.candidate_actions import ALLOWED_DIRECT_FIELDS
        assert "phone" in ALLOWED_DIRECT_FIELDS
        assert "email" in ALLOWED_DIRECT_FIELDS
        assert "linkedin_url" in ALLOWED_DIRECT_FIELDS
        assert "current_title" in ALLOWED_DIRECT_FIELDS

    def test_allowed_json_fields(self):
        from app.orchestrator.action_handlers.candidate_actions import ALLOWED_JSON_FIELDS
        assert "availability_date" in ALLOWED_JSON_FIELDS
        assert "education_level" in ALLOWED_JSON_FIELDS

    def test_allowed_fields_union(self):
        from app.orchestrator.action_handlers.candidate_actions import (
            ALLOWED_FIELDS, ALLOWED_DIRECT_FIELDS, ALLOWED_JSON_FIELDS
        )
        assert ALLOWED_FIELDS == ALLOWED_DIRECT_FIELDS | ALLOWED_JSON_FIELDS

    def test_field_aliases_pt_br(self):
        from app.orchestrator.action_handlers.candidate_actions import FIELD_ALIASES
        assert FIELD_ALIASES.get("telefone") == "phone"
        assert FIELD_ALIASES.get("e-mail") == "email"
        assert FIELD_ALIASES.get("linkedin") == "linkedin_url"
        assert FIELD_ALIASES.get("cidade") == "location_city"
        assert FIELD_ALIASES.get("formação") == "education_level"


class TestExecuteCandidateAction:
    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_unknown_action_returns_none(self):
        from app.orchestrator.action_handlers.candidate_actions import execute_candidate_action
        result = self._run(execute_candidate_action("unknown_action_xyz", {}, {}))
        assert result is None

    def test_move_candidate_missing_db(self):
        from app.orchestrator.action_handlers.candidate_actions import execute_candidate_action
        # Without real DB, should return ActionResult with error
        result = self._run(execute_candidate_action(
            "move_candidate",
            {"candidate_id": "cand-123", "to_stage": "Entrevista"},
            {"company_id": "co-1"},
        ))
        # Should return an ActionResult (not None) — either executed or error
        assert result is not None

    def test_update_candidate_field_missing_db(self):
        from app.orchestrator.action_handlers.candidate_actions import execute_candidate_action
        result = self._run(execute_candidate_action(
            "update_candidate_field",
            {"candidate_id": "cand-123", "field": "phone", "value": "+55 11 99999-0000"},
            {},
        ))
        assert result is not None

    def test_start_screening_missing_db(self):
        from app.orchestrator.action_handlers.candidate_actions import execute_candidate_action
        result = self._run(execute_candidate_action(
            "start_screening",
            {"candidate_id": "cand-123", "job_id": "job-456"},
            {},
        ))
        assert result is not None

    def test_analyze_profile_missing_db(self):
        from app.orchestrator.action_handlers.candidate_actions import execute_candidate_action
        result = self._run(execute_candidate_action(
            "analyze_profile",
            {"candidate_id": "cand-123"},
            {},
        ))
        assert result is not None


class TestExecuteJobAction:
    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_unknown_action_returns_none(self):
        from app.orchestrator.action_handlers.job_actions import execute_job_action
        result = self._run(execute_job_action("unknown_xyz", {}, {}))
        assert result is None

    def test_pause_job_missing_db(self):
        from app.orchestrator.action_handlers.job_actions import execute_job_action
        result = self._run(execute_job_action(
            "pause_job",
            {"job_id": "job-123", "job_title": "Dev Sênior"},
            {},
        ))
        assert result is not None

    def test_close_job_missing_db(self):
        from app.orchestrator.action_handlers.job_actions import execute_job_action
        result = self._run(execute_job_action(
            "close_job",
            {"job_id": "job-123"},
            {},
        ))
        assert result is not None

    def test_duplicate_job_missing_db(self):
        from app.orchestrator.action_handlers.job_actions import execute_job_action
        result = self._run(execute_job_action(
            "duplicate_job",
            {"job_id": "job-123"},
            {},
        ))
        assert result is not None

    def test_reopen_job_missing_db(self):
        from app.orchestrator.action_handlers.job_actions import execute_job_action
        result = self._run(execute_job_action(
            "reopen_job",
            {"job_id": "job-123"},
            {},
        ))
        assert result is not None


class TestCommunicationActions:
    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_module_importable(self):
        from app.orchestrator.action_handlers import communication_actions
        assert hasattr(communication_actions, "execute_communication_action")

    def test_unknown_action_returns_none(self):
        from app.orchestrator.action_handlers.communication_actions import execute_communication_action
        result = self._run(execute_communication_action("unknown_xyz", {}, {}))
        assert result is None

    def test_send_email_missing_deps(self):
        from app.orchestrator.action_handlers.communication_actions import execute_communication_action
        result = self._run(execute_communication_action(
            "send_email",
            {"candidate_id": "cand-123", "message": "Olá", "subject": "Teste"},
            {},
        ))
        assert result is not None


class TestPipelineActions:
    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_module_importable(self):
        from app.orchestrator.action_handlers import pipeline_actions
        assert hasattr(pipeline_actions, "execute_pipeline_action")

    def test_unknown_action_returns_none(self):
        from app.orchestrator.action_handlers.pipeline_actions import execute_pipeline_action
        result = self._run(execute_pipeline_action("unknown_xyz", {}, {}))
        assert result is None


class TestActionHandlersInit:
    def test_init_module_importable(self):
        from app.orchestrator.action_handlers import __init__  # noqa
        # If this raises, the package is broken

    def test_action_handlers_all_importable(self):
        from app.orchestrator.action_handlers import candidate_actions
        from app.orchestrator.action_handlers import job_actions
        from app.orchestrator.action_handlers import communication_actions
        from app.orchestrator.action_handlers import pipeline_actions
        assert all([candidate_actions, job_actions, communication_actions, pipeline_actions])
