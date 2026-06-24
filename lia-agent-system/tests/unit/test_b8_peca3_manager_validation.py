"""B8 Peça 3 — TDD: validate_manager_email + ClientUser inference source."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_validate_existing_active_user():
    """Email matches active ClientUser → valid=True + user_name returned."""
    from app.domains.job_management.services.job_vacancy_service import validate_manager_email

    mock_user = MagicMock()
    mock_user.status = "active"
    mock_user.name = "Maria Souza"

    mock_repo = MagicMock()
    mock_repo.get_by_email = AsyncMock(return_value=mock_user)

    with patch(
        "app.repositories.client_user_repository.ClientUserRepository",
        return_value=mock_repo,
    ):
        result = await validate_manager_email(
            "maria@empresa.com", "00000000-0000-0000-0000-000000000001", MagicMock()
        )

    assert result["valid"] is True
    assert result["user_name"] == "Maria Souza"
    assert result["source"] == "client_user"


@pytest.mark.asyncio
async def test_validate_unknown_email():
    """Email not in client_users → valid=False, source=not_found."""
    from app.domains.job_management.services.job_vacancy_service import validate_manager_email

    mock_repo = MagicMock()
    mock_repo.get_by_email = AsyncMock(return_value=None)

    with patch(
        "app.repositories.client_user_repository.ClientUserRepository",
        return_value=mock_repo,
    ):
        result = await validate_manager_email(
            "ghost@nowhere.com", "00000000-0000-0000-0000-000000000001", MagicMock()
        )

    assert result["valid"] is False
    assert result["source"] == "not_found"


@pytest.mark.asyncio
async def test_validate_inactive_user():
    """Email matches inactive ClientUser → valid=False, source=inactive_user."""
    from app.domains.job_management.services.job_vacancy_service import validate_manager_email

    mock_user = MagicMock()
    mock_user.status = "inactive"

    mock_repo = MagicMock()
    mock_repo.get_by_email = AsyncMock(return_value=mock_user)

    with patch(
        "app.repositories.client_user_repository.ClientUserRepository",
        return_value=mock_repo,
    ):
        result = await validate_manager_email(
            "old@empresa.com", "00000000-0000-0000-0000-000000000001", MagicMock()
        )

    assert result["valid"] is False
    assert result["source"] == "inactive_user"


@pytest.mark.asyncio
async def test_validate_no_email():
    """No email → valid=False, source=no_email — no DB query."""
    from app.domains.job_management.services.job_vacancy_service import validate_manager_email

    result = await validate_manager_email(None, "company-id", MagicMock())
    assert result["valid"] is False
    assert result["source"] == "no_email"
