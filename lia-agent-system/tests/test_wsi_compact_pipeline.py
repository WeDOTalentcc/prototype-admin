"""Tests for WSICompactPipeline question generation (Task #541).

Regression: previously the pipeline tried to call a non-existent
``get_llm(tier="fast")`` helper, breaking question generation in runtime.
This test pins the pipeline to the supported entry point
``get_provider_for_tenant_from_db`` + ``generate_with_fallback``.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.services.wsi_compact_pipeline import (
    COMPACT_MODE_MAX_QUESTIONS,
    WSICompactPipeline,
)


@pytest.mark.asyncio
async def test_generate_from_archetype_happy_path():
    pipeline = WSICompactPipeline()

    fake_llm_payload = {
        "questions": [
            {
                "question": "Qual sua disponibilidade para inicio?",
                "ideal_answer": "Imediata",
                "weight": 0.25,
                "competency": "logistical",
            },
            {
                "question": "Descreva sua experiencia com Python.",
                "ideal_answer": "3+ anos",
                "weight": 0.5,
                "competency": "technical",
            },
            {
                "question": "Como voce lida com prazos curtos?",
                "ideal_answer": "Prioriza e comunica",
                "weight": 0.25,
                "competency": "behavioral",
            },
        ]
    }

    fake_container = AsyncMock()
    fake_container.generate_with_fallback = AsyncMock(
        return_value=json.dumps(fake_llm_payload)
    )

    with patch(
        "app.shared.providers.llm_factory.get_provider_for_tenant_from_db",
        AsyncMock(return_value=fake_container),
    ) as mock_get_provider:
        config = await pipeline.generate_from_archetype(
            archetype_data={
                "id": "arch-1",
                "name": "Backend Engineer",
                "description": "Python/FastAPI",
                "seniority_level": "senior",
                "mandatory_skills": ["python", "fastapi"],
            },
            company_id="company-123",
            language="pt-BR",
        )

    mock_get_provider.assert_awaited_once_with("company-123")
    fake_container.generate_with_fallback.assert_awaited_once()
    assert len(config.questions) == 3
    assert len(config.questions) <= COMPACT_MODE_MAX_QUESTIONS
    assert all(q.source == "wsi_compact" for q in config.questions)
    # Weights are normalized to ~1.0
    assert abs(sum(q.weight for q in config.questions) - 1.0) < 0.05


@pytest.mark.asyncio
async def test_generate_from_archetype_handles_markdown_fenced_json():
    pipeline = WSICompactPipeline()

    fake_llm_payload = {
        "questions": [
            {
                "question": "Q1?",
                "ideal_answer": "A1",
                "weight": 1.0,
                "competency": "technical",
            }
        ]
    }
    fenced = f"```json\n{json.dumps(fake_llm_payload)}\n```"

    fake_container = AsyncMock()
    fake_container.generate_with_fallback = AsyncMock(return_value=fenced)

    with patch(
        "app.shared.providers.llm_factory.get_provider_for_tenant_from_db",
        AsyncMock(return_value=fake_container),
    ):
        config = await pipeline.generate_from_archetype(
            archetype_data={"name": "X"}, company_id="company-xyz"
        )

    assert len(config.questions) == 1
    assert config.questions[0].question == "Q1?"
