"""
P1-7 regression sensor (2026-05-24): PUT /company/profile/{profile_id}
MUST reject cross-tenant writes with HTTP 403 BEFORE any update.

Context: update_company_profile fetched the profile by ID but never
validated that profile.client_account_id matched the JWT company_id.
Any authenticated user could overwrite another tenant's company profile
by guessing/knowing a profile_id -- classic IDOR (Insecure Direct Object
Reference), OWASP A01 Broken Access Control.

Pattern: CompanyProfile uses client_account_id (FK -> client_accounts)
as its tenant anchor, NOT company_id (which is a field on child models
like Department/Benefit). Same check used in upload_company_logo.

Strategy: unit test -- mock CompanyProfileRepository, inject mismatched
company_id via require_company_id dependency. Verifies 403 is raised
BEFORE profile_repo.update is ever called (no side-effect escape).
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException


COMPANY_A = str(uuid.uuid4())
COMPANY_B = str(uuid.uuid4())
PROFILE_ID = uuid.uuid4()


def _make_profile(*, client_account_id):
    """Return a minimal CompanyProfile mock."""
    p = MagicMock()
    p.id = PROFILE_ID
    p.name = "Acme Corp"
    p.client_account_id = client_account_id
    return p


@pytest.mark.asyncio
async def test_update_profile_idor_blocked_when_tenant_mismatch():
    """
    GIVEN a profile owned by tenant A,
    WHEN an authenticated user from tenant B attempts PUT /profile/{id},
    THEN HTTP 403 is raised before any update is written.
    """
    from app.api.v1.company import update_company_profile

    profile_mock = _make_profile(client_account_id=COMPANY_A)
    repo_mock = AsyncMock()
    repo_mock.get_by_id = AsyncMock(return_value=profile_mock)
    repo_mock.update = AsyncMock()  # should NOT be called

    data_mock = MagicMock()
    data_mock.model_dump = MagicMock(return_value={"name": "Hacked Corp"})

    current_user_mock = MagicMock()
    current_user_mock.company_id = COMPANY_B

    with pytest.raises(HTTPException) as exc_info:
        await update_company_profile(
            profile_id=PROFILE_ID,
            data=data_mock,
            profile_repo=repo_mock,
            current_user=current_user_mock,
            company_id=COMPANY_B,
        )

    assert exc_info.value.status_code == 403
    repo_mock.update.assert_not_called()


@pytest.mark.asyncio
async def test_update_profile_allowed_when_tenant_matches():
    """
    GIVEN a profile owned by tenant A,
    WHEN an authenticated user from tenant A attempts PUT /profile/{id},
    THEN the update proceeds without 403.
    """
    from app.api.v1.company import update_company_profile

    profile_mock = _make_profile(client_account_id=COMPANY_A)
    profile_mock.name = "Acme Corp"

    updated_mock = MagicMock()
    updated_mock.name = "Acme Corp Updated"

    repo_mock = AsyncMock()
    repo_mock.get_by_id = AsyncMock(return_value=profile_mock)
    repo_mock.update = AsyncMock(return_value=updated_mock)

    data_mock = MagicMock()
    data_mock.model_dump = MagicMock(return_value={"name": "Acme Corp Updated"})

    current_user_mock = MagicMock()
    current_user_mock.company_id = COMPANY_A

    result = await update_company_profile(
        profile_id=PROFILE_ID,
        data=data_mock,
        profile_repo=repo_mock,
        current_user=current_user_mock,
        company_id=COMPANY_A,
    )

    repo_mock.update.assert_called_once()
    assert result is not None


@pytest.mark.asyncio
async def test_update_profile_allowed_when_no_client_account_id():
    """
    GIVEN a profile with null client_account_id (unclaimed/demo profile),
    WHEN any authenticated user attempts PUT /profile/{id},
    THEN the update is allowed (guard skips for null, sets client_account_id).
    """
    from app.api.v1.company import update_company_profile

    profile_mock = _make_profile(client_account_id=None)
    profile_mock.name = "Demo Corp"

    updated_mock = MagicMock()
    updated_mock.name = "Demo Corp"

    repo_mock = AsyncMock()
    repo_mock.get_by_id = AsyncMock(return_value=profile_mock)
    repo_mock.update = AsyncMock(return_value=updated_mock)

    data_mock = MagicMock()
    data_mock.model_dump = MagicMock(return_value={"name": "Demo Corp"})

    current_user_mock = MagicMock()
    current_user_mock.company_id = COMPANY_A

    result = await update_company_profile(
        profile_id=PROFILE_ID,
        data=data_mock,
        profile_repo=repo_mock,
        current_user=current_user_mock,
        company_id=COMPANY_A,
    )

    repo_mock.update.assert_called_once()


@pytest.mark.asyncio
async def test_update_profile_returns_404_when_not_found():
    """Profile not found -> 404, never reaches IDOR check."""
    from app.api.v1.company import update_company_profile

    repo_mock = AsyncMock()
    repo_mock.get_by_id = AsyncMock(return_value=None)

    data_mock = MagicMock()
    data_mock.model_dump = MagicMock(return_value={})

    with pytest.raises(HTTPException) as exc_info:
        await update_company_profile(
            profile_id=PROFILE_ID,
            data=data_mock,
            profile_repo=repo_mock,
            current_user=MagicMock(),
            company_id=COMPANY_A,
        )

    assert exc_info.value.status_code == 404
