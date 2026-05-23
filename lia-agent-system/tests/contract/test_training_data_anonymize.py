"""BUG-C4-A regression sensor: TrainingDataService._anonymize_feedback_batch
MUST exist and produce LGPD-anonymized samples ready for cross-border training
data upload (ADR-LGPD-002).

Context (audit 2026-05-23): Sensor F-26 (expanded in C.4) detected that
`TrainingDataService._anonymize_feedback_batch` was called in 3 sites
(`export_openai_format`, `export_anthropic_format`, `export_dpo_pairs`)
but the method was MISSING from the class. Production code raised
AttributeError at runtime, blocking T-21b LGPD anonymization wiring.

Strategy: write unit tests covering shape, PII stripping, candidate_id
hashing, and idempotency. Delegates to canonical TrainingDataAnonymizer
(`app/domains/analytics/services/training_data_anonymizer.py`) — single
source of truth for LGPD Art. 12 §1.
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest


def _make_feedback(
    *,
    user_message: str = "Olá, sou Maria Silva, email maria@acme.com",
    lia_response: str = "Oi! Vou te ajudar a encontrar candidatos.",
    correction: str | None = None,
    candidate_id=None,
    rating: int = 5,
):
    """Build a SimpleNamespace mimicking the ORM InteractionFeedback shape
    consumed by `_anonymize_feedback_batch`. The method should NOT depend
    on SQLAlchemy session state — only on attribute access."""
    return SimpleNamespace(
        id=uuid4(),
        user_message=user_message,
        lia_response=lia_response,
        correction=correction,
        candidate_id=candidate_id,
        rating=rating,
        thumbs="up",
        confidence_score=0.9,
        intent="job_creation",
        stage="active",
    )


@pytest.fixture
def service():
    from app.domains.analytics.services.training_data_service import (
        TrainingDataService,
    )
    return TrainingDataService(db=MagicMock())


@pytest.mark.asyncio
async def test_method_exists_on_class():
    """RED guard: method must exist (was MISSING per F-26 C.4)."""
    from app.domains.analytics.services.training_data_service import (
        TrainingDataService,
    )
    assert hasattr(TrainingDataService, "_anonymize_feedback_batch"), (
        "BUG-C4-A regression: _anonymize_feedback_batch method removed. "
        "It is called by 3 sites (export_openai_format, export_anthropic_format, "
        "export_dpo_pairs) — removing it re-introduces production AttributeError."
    )


@pytest.mark.asyncio
async def test_anonymize_returns_list_of_dicts(service):
    """Output must be list[dict] with required keys for downstream packers."""
    feedback = [_make_feedback()]
    result = await service._anonymize_feedback_batch(
        feedback, company_id=str(uuid4())
    )
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], dict)
    # Required keys consumed by callers
    assert "user_message" in result[0]
    assert "lia_response" in result[0]


@pytest.mark.asyncio
async def test_anonymize_strips_email_in_user_message(service):
    """LGPD: email-like PII in free text must be stripped."""
    feedback = [_make_feedback(
        user_message="Contato é maria@acme.com.br pelo número (11) 99999-8888"
    )]
    result = await service._anonymize_feedback_batch(
        feedback, company_id=str(uuid4())
    )
    msg = result[0]["user_message"]
    assert "maria@acme.com.br" not in msg, f"Email leak in: {msg!r}"


@pytest.mark.asyncio
async def test_anonymize_hashes_candidate_id_when_present(service):
    """LGPD Art. 12 §1: candidate_id must be SHA-256 hashed irreversibly."""
    cand_id = uuid4()
    feedback = [_make_feedback(candidate_id=cand_id)]
    result = await service._anonymize_feedback_batch(
        feedback, company_id=str(uuid4())
    )
    # Raw candidate_id must be removed
    assert "candidate_id" not in result[0], (
        "Raw candidate_id leaked through anonymization"
    )
    # Hashed version must be present
    assert "candidate_id_hash" in result[0]
    assert len(result[0]["candidate_id_hash"]) == 64  # SHA-256 hex


@pytest.mark.asyncio
async def test_anonymize_adds_version_metadata(service):
    """Every sample must carry _anonymization_version for audit trail."""
    feedback = [_make_feedback()]
    result = await service._anonymize_feedback_batch(
        feedback, company_id=str(uuid4())
    )
    assert "_anonymization_version" in result[0]
    assert result[0]["_anonymization_version"]  # truthy


@pytest.mark.asyncio
async def test_anonymize_preserves_correction_field_for_dpo(service):
    """DPO export needs correction field anonymized but not dropped."""
    feedback = [_make_feedback(
        correction="Resposta melhor sem PII",
    )]
    result = await service._anonymize_feedback_batch(
        feedback, company_id=str(uuid4())
    )
    assert "correction" in result[0]
    assert result[0]["correction"] == "Resposta melhor sem PII"


@pytest.mark.asyncio
async def test_anonymize_preserves_batch_count(service):
    """N feedback rows in => N samples out (no silent dropping)."""
    feedback = [_make_feedback() for _ in range(5)]
    result = await service._anonymize_feedback_batch(
        feedback, company_id=str(uuid4())
    )
    assert len(result) == 5


@pytest.mark.asyncio
async def test_anonymize_empty_input_returns_empty_list(service):
    """Defensive: empty input must not raise."""
    result = await service._anonymize_feedback_batch(
        [], company_id=str(uuid4())
    )
    assert result == []
