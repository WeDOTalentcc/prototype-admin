"""UC-P1-13: ConsentManager unified facade orchestrates all consent artifacts."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_check_ai_consent_delegates_to_granular():
    """check_ai_consent routes to GranularConsentService.check_purpose."""
    from app.domains.consent.services.consent_manager import ConsentManager
    mock_db = MagicMock()
    manager = ConsentManager.__new__(ConsentManager)
    manager._granular = MagicMock()
    manager._gate = MagicMock()
    manager._repo = MagicMock()
    manager._granular.check_purpose = AsyncMock(return_value=True)
    result = await manager.check_ai_consent("cand_1", "company_1", "AI_SCORING")
    manager._granular.check_purpose.assert_called_once_with("cand_1", "company_1", "AI_SCORING")
    assert result is True


@pytest.mark.asyncio
async def test_check_ai_consent_fail_closed_on_error():
    """check_ai_consent returns False (fail-closed) on upstream exception."""
    from app.domains.consent.services.consent_manager import ConsentManager
    manager = ConsentManager.__new__(ConsentManager)
    manager._granular = MagicMock()
    manager._gate = MagicMock()
    manager._repo = MagicMock()
    manager._granular.check_purpose = AsyncMock(side_effect=RuntimeError("db down"))
    result = await manager.check_ai_consent("cand_1", "company_1", "AI_SCORING")
    assert result is False


@pytest.mark.asyncio
async def test_check_communication_consent_delegates_to_gate():
    """check_communication_consent routes to CommunicationConsentGate.check."""
    from app.domains.consent.services.consent_manager import ConsentManager

    class MockResult:
        allowed = False

    mock_gate = MagicMock()
    mock_gate.check = AsyncMock(return_value=MockResult())

    manager = ConsentManager.__new__(ConsentManager)
    manager._granular = MagicMock()
    manager._gate = mock_gate
    manager._repo = MagicMock()
    result = await manager.check_communication_consent("cand_1", "company_1", "email")
    mock_gate.check.assert_called_once()
    assert result is False


@pytest.mark.asyncio
async def test_check_communication_consent_fail_closed_on_error():
    """check_communication_consent returns False on upstream exception."""
    from app.domains.consent.services.consent_manager import ConsentManager
    manager = ConsentManager.__new__(ConsentManager)
    manager._granular = MagicMock()
    manager._gate = MagicMock()
    manager._repo = MagicMock()
    manager._gate.check = AsyncMock(side_effect=RuntimeError("timeout"))
    result = await manager.check_communication_consent("cand_1", "company_1", "sms")
    assert result is False


@pytest.mark.asyncio
async def test_revoke_consent_updates_repository():
    """revoke_consent writes to consent repository via record_revocation."""
    from app.domains.consent.services.consent_manager import ConsentManager
    manager = ConsentManager.__new__(ConsentManager)
    manager._granular = MagicMock()
    manager._gate = MagicMock()
    manager._repo = MagicMock()
    manager._repo.record_revocation = AsyncMock()
    await manager.revoke_consent("cand_1", "company_1", "AI_SCORING")
    manager._repo.record_revocation.assert_called_once_with("cand_1", "company_1", "AI_SCORING")


@pytest.mark.asyncio
async def test_record_consent_updates_repository():
    """record_consent writes to consent repository."""
    from app.domains.consent.services.consent_manager import ConsentManager
    manager = ConsentManager.__new__(ConsentManager)
    manager._granular = MagicMock()
    manager._gate = MagicMock()
    manager._repo = MagicMock()
    manager._repo.record_consent = AsyncMock()
    await manager.record_consent("cand_1", "company_1", "AI_SCORING", True)
    manager._repo.record_consent.assert_called_once_with("cand_1", "company_1", "AI_SCORING", True)


def test_consent_manager_exposes_unified_interface():
    """ConsentManager has the 4 required public methods."""
    from app.domains.consent.services.consent_manager import ConsentManager
    for method in ['check_ai_consent', 'check_communication_consent',
                   'record_consent', 'revoke_consent']:
        assert hasattr(ConsentManager, method), f"Missing method: {method}"
