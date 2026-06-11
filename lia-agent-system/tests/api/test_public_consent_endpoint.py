"""
Tests for the public consent lookup endpoint (Phase 4 LGPD Portal).

GET /api/v1/public/consents?cpf=...&email=...
"""
import hashlib
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


def _email_hash(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()


def _cpf_hash(cpf: str) -> str:
    digits = "".join(c for c in cpf if c.isdigit())
    return hashlib.sha256(digits.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_consent_dict(candidate_id: str, consent_type: str = "comunicacao") -> dict:
    return {
        "id": str(uuid.uuid4()),
        "company_id": str(uuid.uuid4()),
        "candidate_id": candidate_id,
        "consent_type": consent_type,
        "version": "1.0",
        "granted_at": "2026-01-15T10:00:00",
        "expires_at": None,
        "revoked_at": None,
        "is_active": True,
        "source": "portal",
        "legal_basis": "consent",
        "canal": "chat_web",
        "user_agent": None,
        "processo_id": None,
        "vaga_id": None,
        "versao_disclaimer": "1.0",
        "created_at": "2026-01-15T10:00:00",
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_public_consents_by_email_returns_candidate_consents():
    """Endpoint returns consents when a matching candidate is found by email."""
    candidate_id = uuid.uuid4()
    email = "candidato@exemplo.com"
    mock_consent = MagicMock()
    mock_consent.to_dict.return_value = _make_consent_dict(str(candidate_id))

    mock_db = AsyncMock()

    # First query: find candidate IDs
    candidate_row = MagicMock()
    candidate_row.__getitem__ = lambda self, i: candidate_id
    candidate_result_mock = MagicMock()
    candidate_result_mock.fetchall.return_value = [(candidate_id,)]

    # Second query: find consents
    consent_result_mock = MagicMock()
    consent_result_mock.scalars.return_value.all.return_value = [mock_consent]

    mock_db.execute = AsyncMock(side_effect=[candidate_result_mock, consent_result_mock])

    from app.api.v1.public_consent import list_public_consents

    result = await list_public_consents(cpf=None, email=email, db=mock_db)

    assert result["total"] == 1
    assert len(result["consents"]) == 1
    assert result["consents"][0]["candidate_id"] == str(candidate_id)


@pytest.mark.asyncio
async def test_public_consents_cpf_not_found_returns_empty():
    """Returns empty list when no candidate matches the CPF."""
    mock_db = AsyncMock()

    candidate_result_mock = MagicMock()
    candidate_result_mock.fetchall.return_value = []  # no matching candidate

    mock_db.execute = AsyncMock(return_value=candidate_result_mock)

    from app.api.v1.public_consent import list_public_consents

    result = await list_public_consents(cpf="123.456.789-00", email=None, db=mock_db)

    assert result["total"] == 0
    assert result["consents"] == []
    # Only one DB query was made (no second query needed)
    assert mock_db.execute.call_count == 1


@pytest.mark.asyncio
async def test_public_consents_missing_both_params_returns_422():
    """Raises HTTPException(422) when neither cpf nor email is provided."""
    from fastapi import HTTPException

    from app.api.v1.public_consent import list_public_consents

    with pytest.raises(HTTPException) as exc_info:
        await list_public_consents(cpf=None, email=None, db=AsyncMock())

    assert exc_info.value.status_code == 422
    assert "obrigatório" in exc_info.value.detail.lower()
