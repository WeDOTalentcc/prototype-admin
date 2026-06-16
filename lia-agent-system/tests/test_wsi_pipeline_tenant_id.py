"""Task #334 — WSI screening pipeline must forward the recruiter's tenant id.

When the WSI interview graph hits the on-the-fly question-generation fallback,
it instantiates ``WSIScreeningPipeline().build_pipeline(req, [])``. The request
carries ``company_id``, but the pipeline must:

1. Set the ``_current_company_id`` contextvar before any LLM call so providers
   resolved by Choose Your AI use the tenant's key, not the global fallback.
2. Forward the tenant id to ``WSIService.generate_from_simple_inputs`` via
   ``tracking_context`` so usage tracking is attributed to the right tenant.
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.domains.cv_screening.services.wsi_screening_pipeline import (
    WSIScreeningPipeline,
)
from app.middleware.auth_enforcement import _current_company_id
from app.schemas.screening import WSIScreeningPipelineRequest


TENANT_ID = "11111111-1111-1111-1111-111111111111"


@pytest.mark.asyncio
async def test_build_pipeline_forwards_tenant_id_to_wsi_service():
    """The pipeline must pass company_id through tracking_context and set the
    LLM tenant contextvar while LLM calls happen."""

    seen_company_ids: list[str | None] = []
    seen_contextvar: list[str] = []

    async def _fake_generate(*args, **kwargs):
        ctx = kwargs.get("tracking_context") or {}
        seen_company_ids.append(ctx.get("company_id"))
        seen_contextvar.append(_current_company_id.get(""))
        return []

    with patch(
        "app.domains.cv_screening.services.wsi_service.WSIService.generate_from_simple_inputs",
        new=AsyncMock(side_effect=_fake_generate),
    ):
        request = WSIScreeningPipelineRequest(
            job_title="Engenheiro Backend",
            seniority="pleno",
            technical_skills=["Python", "FastAPI"],
            behavioral_competencies=["Comunicação"],
            company_id=TENANT_ID,
            include_company_questions=False,
        )
        pipeline = WSIScreeningPipeline()
        # Reset contextvar so we are sure the pipeline itself sets it.
        token = _current_company_id.set("")
        try:
            await pipeline.build_pipeline(request, [])
        finally:
            _current_company_id.reset(token)

    assert seen_company_ids, "WSIService was never called by the pipeline"
    assert all(cid == TENANT_ID for cid in seen_company_ids), (
        f"Expected every WSIService call to receive tenant {TENANT_ID} via "
        f"tracking_context, got {seen_company_ids!r}"
    )
    assert all(cid == TENANT_ID for cid in seen_contextvar), (
        f"Expected _current_company_id contextvar to be set to {TENANT_ID} "
        f"during LLM dispatch, got {seen_contextvar!r}"
    )


@pytest.mark.asyncio
async def test_load_context_fallback_passes_tenant_id_to_pipeline():
    """End-to-end: when no saved questions exist, the WSI interview graph's
    `load_context` fallback must call the pipeline with `state.company_id`."""

    from app.domains.cv_screening.agents.wsi_interview_graph import (
        WSIInterviewNodes,
        WSIInterviewState,
    )

    captured: dict = {}

    async def _fake_build(self, request, company_questions_raw):  # noqa: ANN001
        captured["company_id"] = request.company_id
        captured["job_title"] = request.job_title

        class _Result:
            questions = []

        return _Result()

    state = WSIInterviewState(
        session_id="sess-1",
        company_id=TENANT_ID,
        candidate_id="cand-1",
        job_id="job-1",
        job_requirements={
            "title": "Engenheiro Backend",
            "description": "Python/FastAPI",
            "seniority": "pleno",
        },
        candidate_profile={"name": "Alice"},
    )

    with patch(
        "app.domains.cv_screening.services.wsi_screening_pipeline.WSIScreeningPipeline.build_pipeline",
        new=_fake_build,
    ):
        await WSIInterviewNodes().load_context(state)

    assert captured.get("company_id") == TENANT_ID, (
        f"Pipeline fallback should receive tenant {TENANT_ID} via request.company_id, "
        f"got {captured!r}"
    )


@pytest.mark.asyncio
async def test_build_pipeline_without_company_id_is_noop_for_tenant_scope():
    """When no company_id is provided the pipeline must not invent one — it
    leaves the contextvar untouched and passes no tracking_context."""

    seen: list[dict | None] = []

    async def _fake_generate(*args, **kwargs):
        seen.append(kwargs.get("tracking_context"))
        return []

    with patch(
        "app.domains.cv_screening.services.wsi_service.WSIService.generate_from_simple_inputs",
        new=AsyncMock(side_effect=_fake_generate),
    ):
        request = WSIScreeningPipelineRequest(
            job_title="Engenheiro Backend",
            seniority="pleno",
            technical_skills=["Python"],
            behavioral_competencies=["Comunicação"],
            company_id=None,
            include_company_questions=False,
        )
        token = _current_company_id.set("")
        try:
            await WSIScreeningPipeline().build_pipeline(request, [])
            assert _current_company_id.get("") == "", (
                "Pipeline must not set the tenant contextvar when company_id is missing"
            )
        finally:
            _current_company_id.reset(token)

    assert seen, "WSIService was never called by the pipeline"
    assert all(ctx is None for ctx in seen), (
        f"Expected no tracking_context when company_id missing, got {seen!r}"
    )
