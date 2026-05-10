"""TDD red-phase — handle_job_published wires record_jd (Sprint B Phase 1, gap W2).

Harness taxonomy: Sensor (computacional, feedback) — verifies the event
handler invokes JdSimilarService.record_jd when the company toggle
`learning_loops.jd_similar_suggestion` is enabled.

Why this exists: `record_jd` endpoint and service exist (and the helper
`record_jd_fire_and_forget`), but no caller wires them on publish events.
The JD History thus stays empty in production, and the learning loop never
activates. CLAUDE.md "Wiring de features Phase X precisa ser end-to-end"
applies — wiring belongs INSIDE the handler, not just on a separate hook.

If a test fails: check that handle_job_published gained a call to
JdSimilarService.record_jd (or a helper that calls it), gated by the
hiring policy toggle, and that exceptions don't propagate (fail-soft).
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_event(
    company_id: str = "co-1",
    job_id: str = "job-abc",
    title: str = "Backend Engineer",
    jd_enriched: dict | None = None,
    department: str | None = "Engineering",
    seniority_level: str | None = "Senior",
):
    from app.shared.messaging.platform_events import PlatformEvent

    return PlatformEvent(
        event_type="vagas.job.published",
        company_id=company_id,
        source_api="api-vagas",
        payload={
            "job_id": job_id,
            "title": title,
            "jd_enriched": jd_enriched or {
                "responsibilities": ["Build APIs", "Mentor juniors"],
                "requirements": ["Python", "PostgreSQL"],
            },
            "department": department,
            "seniority_level": seniority_level,
            "recruiter_ids": [],
        },
    )


def _make_policy(jd_similar_enabled: bool):
    """Mock CompanyHiringPolicy with learning_loops.jd_similar_suggestion toggle."""
    policy = MagicMock()
    policy.automation_rules = {
        "learning_loops": {
            "enabled": True,
            "jd_similar_suggestion": jd_similar_enabled,
        },
    }
    return policy


class TestRecordJdWiring:
    def test_calls_record_jd_when_toggle_on(self):
        """Toggle ON → JdSimilarService.record_jd MUST be called."""
        from app.api.v1 import platform_event_handlers

        event = _make_event()
        record_jd_mock = AsyncMock()

        async def _run():
            # Patch where the names are *bound* in the handler module
            # (Python from-imports rebind locally; patching origin won't intercept).
            with patch.object(
                platform_event_handlers, "_get_db", new=AsyncMock(return_value=AsyncMock())
            ), patch(
                "app.domains.hiring_policy.repositories.hiring_policy_repository.HiringPolicyRepository.get_by_company",
                new=AsyncMock(return_value=_make_policy(jd_similar_enabled=True)),
            ), patch.object(
                platform_event_handlers, "get_pipeline_stage_service"
            ) as ps, patch.object(
                platform_event_handlers, "get_activity_service"
            ) as act, patch(
                "app.domains.job_creation.services.jd_similar_service.JdSimilarService.record_jd",
                new=record_jd_mock,
            ):
                ps.return_value.initialize_company_stages = AsyncMock()
                act.return_value.create_activity = AsyncMock()
                await platform_event_handlers.handle_job_published(event)

        asyncio.run(_run())
        assert record_jd_mock.called, (
            "JdSimilarService.record_jd was not called. "
            "Wire it inside handle_job_published, gated by "
            "hiring_policy.automation_rules.learning_loops.jd_similar_suggestion."
        )
        kwargs = record_jd_mock.call_args.kwargs
        assert kwargs.get("company_id") == "co-1"
        assert kwargs.get("job_id") == "job-abc"
        assert kwargs.get("title") == "Backend Engineer"

    def test_skips_record_when_toggle_off(self):
        """Toggle OFF → record_jd MUST NOT be called."""
        from app.api.v1 import platform_event_handlers

        event = _make_event()
        record_jd_mock = AsyncMock()

        async def _run():
            with patch.object(
                platform_event_handlers, "_get_db", new=AsyncMock(return_value=AsyncMock())
            ), patch(
                "app.domains.hiring_policy.repositories.hiring_policy_repository.HiringPolicyRepository.get_by_company",
                new=AsyncMock(return_value=_make_policy(jd_similar_enabled=False)),
            ), patch.object(
                platform_event_handlers, "get_pipeline_stage_service"
            ) as ps, patch.object(
                platform_event_handlers, "get_activity_service"
            ) as act, patch(
                "app.domains.job_creation.services.jd_similar_service.JdSimilarService.record_jd",
                new=record_jd_mock,
            ):
                ps.return_value.initialize_company_stages = AsyncMock()
                act.return_value.create_activity = AsyncMock()
                await platform_event_handlers.handle_job_published(event)

        asyncio.run(_run())
        assert not record_jd_mock.called, (
            "record_jd was called despite toggle being OFF. "
            "Add an early-return when learning_loops.jd_similar_suggestion is False."
        )

    def test_skips_record_when_no_policy_exists(self):
        """No CompanyHiringPolicy row → use AUTOMATION_RULES_DEFAULTS (jd_similar=True default).

        Default behavior per AUTOMATION_RULES_DEFAULTS: jd_similar_suggestion=True.
        So when policy is None, we still call record_jd (default ON).
        """
        from app.api.v1 import platform_event_handlers

        event = _make_event()
        record_jd_mock = AsyncMock()

        async def _run():
            with patch.object(
                platform_event_handlers, "_get_db", new=AsyncMock(return_value=AsyncMock())
            ), patch(
                "app.domains.hiring_policy.repositories.hiring_policy_repository.HiringPolicyRepository.get_by_company",
                new=AsyncMock(return_value=None),
            ), patch.object(
                platform_event_handlers, "get_pipeline_stage_service"
            ) as ps, patch.object(
                platform_event_handlers, "get_activity_service"
            ) as act, patch(
                "app.domains.job_creation.services.jd_similar_service.JdSimilarService.record_jd",
                new=record_jd_mock,
            ):
                ps.return_value.initialize_company_stages = AsyncMock()
                act.return_value.create_activity = AsyncMock()
                await platform_event_handlers.handle_job_published(event)

        asyncio.run(_run())
        assert record_jd_mock.called, (
            "record_jd should be called when no policy exists "
            "(AUTOMATION_RULES_DEFAULTS sets jd_similar_suggestion=True)."
        )

    def test_swallows_record_jd_errors_fail_soft(self):
        """record_jd raising must NOT propagate — pipeline init still completes."""
        from app.api.v1 import platform_event_handlers

        event = _make_event()
        init_stages_mock = AsyncMock()
        record_jd_mock = AsyncMock(side_effect=RuntimeError("embedding service down"))

        async def _run():
            with patch.object(
                platform_event_handlers, "_get_db", new=AsyncMock(return_value=AsyncMock())
            ), patch(
                "app.domains.hiring_policy.repositories.hiring_policy_repository.HiringPolicyRepository.get_by_company",
                new=AsyncMock(return_value=_make_policy(jd_similar_enabled=True)),
            ), patch.object(
                platform_event_handlers, "get_pipeline_stage_service"
            ) as ps, patch.object(
                platform_event_handlers, "get_activity_service"
            ) as act, patch(
                "app.domains.job_creation.services.jd_similar_service.JdSimilarService.record_jd",
                new=record_jd_mock,
            ):
                ps.return_value.initialize_company_stages = init_stages_mock
                act.return_value.create_activity = AsyncMock()
                # Should NOT raise
                await platform_event_handlers.handle_job_published(event)

        asyncio.run(_run())
        assert init_stages_mock.called, (
            "initialize_company_stages was NOT called even though record_jd "
            "failed. Wrap record_jd in try/except so failures don't break "
            "the rest of the publish handler."
        )
