"""
Canonical-fix regression tests for chat action `duplicate_job`.

GUIDE: chat `duplicar_vaga` MUST route through
`JobCloneService.clone_from_template` (status 'Rascunho' + canonical
FIELDS_TO_CLONE incl. responsibilities). It MUST NOT reimplement cloning with
raw inline SQL nor publish the copy as 'Ativa'.

These tests pin the producer (canonical service is the one invoked) and the
contract (no `INSERT INTO job_vacancies` / no `'Ativa'` literal left behind).
"""
import sys
sys.path.insert(0, '/home/runner/workspace/lia-agent-system')
import asyncio
import inspect
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


SOURCE_UUID = "11111111-1111-1111-1111-111111111111"
NEW_UUID = "22222222-2222-2222-2222-222222222222"


def _fake_clone_result(status="Rascunho"):
    return {
        "success": True,
        "source_job": {"id": SOURCE_UUID, "job_id": "WDT-X", "title": "Dev Sênior"},
        "created_job": {
            "id": NEW_UUID,
            "job_id": "WDT-Y",
            "title": "Dev Sênior (Cópia)",
            "status": status,
            "department": "Engenharia",
            "location": "Remoto",
            "seniority_level": "Sênior",
            "manager": "Paulo",
            "screening_questions_count": 3,
            "benefits_count": 2,
        },
        "data_copied": {
            "description": True,
            "technical_requirements": 4,
            "behavioral_competencies": 5,
            "screening_questions": 3,
            "benefits": 2,
            "salary_range": True,
            "interview_stages": 2,
        },
    }


class TestDuplicateJobUsesCanonicalService:
    def test_duplicate_job_invokes_clone_from_template(self):
        """Producer pin: _duplicate_job MUST call JobCloneService.clone_from_template."""
        from app.orchestrator.action_handlers import job_actions

        source = MagicMock()
        source.id = SOURCE_UUID
        source.title = "Dev Sênior"

        with patch.object(job_actions, "job_clone_service") as svc, \
             patch.object(job_actions, "AsyncSessionLocal") as session_cls, \
             patch.object(job_actions, "log_action_audit", new=AsyncMock()), \
             patch.object(job_actions, "sync_to_rails", new=AsyncMock()):
            session = AsyncMock()
            session_cls.return_value.__aenter__.return_value = session
            svc.get_job_by_id_or_title = AsyncMock(return_value=source)
            svc.clone_from_template = AsyncMock(return_value=_fake_clone_result())

            result = asyncio.run(
                job_actions._duplicate_job(
                    {"job_id": SOURCE_UUID, "job_title": "Dev Sênior"},
                    {"company_id": "comp-1", "user_id": "user-9"},
                )
            )

        assert svc.clone_from_template.await_count == 1, (
            "_duplicate_job did not call the canonical JobCloneService.clone_from_template. "
            "It must route cloning through the producer, not raw SQL."
        )
        call = svc.clone_from_template.await_args
        assert call.kwargs.get("company_id") == "comp-1", "company_id must come from context (multi-tenancy)."
        assert call.kwargs.get("source_job_id") == SOURCE_UUID
        assert result.status == "executed"
        assert result.action_type == "duplicate_job"
        # Maps canonical result into data: new job id + draft status preserved.
        assert result.data.get("new_job_id") == NEW_UUID
        assert result.data.get("status") == "Rascunho"

    def test_duplicate_job_source_not_found_is_error(self):
        from app.orchestrator.action_handlers import job_actions

        with patch.object(job_actions, "job_clone_service") as svc, \
             patch.object(job_actions, "AsyncSessionLocal") as session_cls:
            session = AsyncMock()
            session_cls.return_value.__aenter__.return_value = session
            svc.get_job_by_id_or_title = AsyncMock(return_value=None)
            svc.clone_from_template = AsyncMock()

            result = asyncio.run(
                job_actions._duplicate_job(
                    {"job_id": "nope", "job_title": "x"},
                    {"company_id": "comp-1"},
                )
            )

        assert result.status == "error", "Source-not-found must fail loud, not fabricate a copy."
        svc.clone_from_template.assert_not_awaited()

    def test_duplicate_job_clone_failure_is_error(self):
        from app.orchestrator.action_handlers import job_actions

        source = MagicMock()
        source.id = SOURCE_UUID
        source.title = "Dev Sênior"

        with patch.object(job_actions, "job_clone_service") as svc, \
             patch.object(job_actions, "AsyncSessionLocal") as session_cls:
            session = AsyncMock()
            session_cls.return_value.__aenter__.return_value = session
            svc.get_job_by_id_or_title = AsyncMock(return_value=source)
            svc.clone_from_template = AsyncMock(
                return_value={"success": False, "error": "boom"}
            )

            result = asyncio.run(
                job_actions._duplicate_job(
                    {"job_id": SOURCE_UUID, "job_title": "x"},
                    {"company_id": "comp-1"},
                )
            )

        assert result.status == "error", "clone failure must be surfaced, not silently swallowed."


class TestNoRawSqlSensor:
    """SENSOR: _duplicate_job source must contain no raw INSERT / 'Ativa' literal."""

    def test_no_inline_insert_or_ativa_literal(self):
        from app.orchestrator.action_handlers import job_actions

        src = inspect.getsource(job_actions._duplicate_job)
        assert "INSERT INTO job_vacancies" not in src, (
            "REGRESSION: _duplicate_job reintroduced raw `INSERT INTO job_vacancies` SQL. "
            "Cloning MUST go through JobCloneService.clone_from_template (ADR-001: no inline SQL "
            "in handlers). Remove the raw INSERT and call the canonical service."
        )
        assert "'Ativa'" not in src, (
            "REGRESSION: _duplicate_job sets status 'Ativa' — a duplicate must be a DRAFT "
            "('Rascunho'), set by JobCloneService.clone_from_template. Do not publish the copy."
        )
