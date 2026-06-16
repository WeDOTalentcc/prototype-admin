"""
Coverage tests for app/domains/recruiter_assistant/services/conversation_manager.py
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import datetime, timedelta
from uuid import uuid4


# ── ConversationMessages — pure static methods, no I/O ───────────────────────

class TestConversationMessages:
    @pytest.fixture(autouse=True)
    def _import(self):
        from app.domains.recruiter_assistant.services.conversation_manager import ConversationMessages
        self.msgs = ConversationMessages

    @pytest.mark.easy
    def test_lgpd_request_default(self):
        result = self.msgs.lgpd_request()
        assert "LIA" in result
        assert "ACEITO" in result
        assert "a empresa" in result

    @pytest.mark.easy
    def test_lgpd_request_custom_company(self):
        result = self.msgs.lgpd_request("WeDo")
        assert "WeDo" in result

    @pytest.mark.easy
    def test_lgpd_accepted(self):
        result = self.msgs.lgpd_accepted()
        assert "currículo" in result.lower() or "curriculo" in result.lower()

    @pytest.mark.easy
    def test_lgpd_not_accepted(self):
        result = self.msgs.lgpd_not_accepted()
        assert "ACEITO" in result

    @pytest.mark.easy
    def test_cv_received_parsing(self):
        result = self.msgs.cv_received_parsing()
        assert len(result) > 0

    @pytest.mark.easy
    def test_cv_parsed(self):
        result = self.msgs.cv_parsed("João", "Dev Python 5 anos")
        assert "João" in result
        assert "Dev Python" in result

    @pytest.mark.easy
    def test_cv_parse_error(self):
        result = self.msgs.cv_parse_error()
        assert "PDF" in result

    @pytest.mark.easy
    def test_screening_question(self):
        result = self.msgs.screening_question(1, "Qual sua experiência?")
        assert "Qual sua experiência?" in result

    @pytest.mark.easy
    def test_screening_complete(self):
        result = self.msgs.screening_complete()
        assert len(result) > 0

    @pytest.mark.easy
    def test_additional_info_request(self):
        result = self.msgs.additional_info_request()
        assert "email" in result.lower()

    @pytest.mark.easy
    def test_confirm_email(self):
        result = self.msgs.confirm_email("joao@test.com")
        assert "joao@test.com" in result
        assert "SIM" in result

    @pytest.mark.easy
    def test_ask_email(self):
        result = self.msgs.ask_email()
        assert "email" in result.lower()

    @pytest.mark.easy
    def test_rubric_rejection(self):
        result = self.msgs.rubric_rejection("Dev Python", 45.0)
        assert "Dev Python" in result

    @pytest.mark.easy
    def test_awaiting_screening_message(self):
        result = self.msgs.awaiting_screening_message("Dev Python")
        assert "Dev Python" in result
        assert "triagem" in result.lower()

    @pytest.mark.easy
    def test_awaiting_screening_already(self):
        result = self.msgs.awaiting_screening_already()
        assert len(result) > 0

    @pytest.mark.easy
    def test_completion_message(self):
        result = self.msgs.completion_message("Dev Python", 7)
        assert "Dev Python" in result
        assert "7" in result

    @pytest.mark.easy
    def test_completion_message_default_days(self):
        result = self.msgs.completion_message("QA")
        assert "5" in result

    @pytest.mark.easy
    def test_feedback_approved(self):
        result = self.msgs.feedback_approved("Dev Python", "Ana")
        assert "Dev Python" in result
        assert "Ana" in result

    @pytest.mark.easy
    def test_feedback_approved_default_recruiter(self):
        result = self.msgs.feedback_approved("Dev")
        assert "recrutador" in result.lower()

    @pytest.mark.easy
    def test_feedback_rejected(self):
        result = self.msgs.feedback_rejected("Dev Python")
        assert "Dev Python" in result

    @pytest.mark.easy
    def test_expired_conversation(self):
        result = self.msgs.expired_conversation()
        assert "inativa" in result.lower() or "nova" in result.lower()

    @pytest.mark.easy
    def test_error_message(self):
        result = self.msgs.error_message()
        assert "problema" in result.lower() or "técnico" in result.lower()


# ── ConversationManager — mock DB and providers ──────────────────────────────

class TestConversationManager:
    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.add = MagicMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def mock_provider(self):
        return AsyncMock()

    @pytest.fixture
    def manager(self, mock_db, mock_provider):
        from app.domains.recruiter_assistant.services.conversation_manager import ConversationManager
        return ConversationManager(db=mock_db, provider=mock_provider)

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_get_provider_uses_injected(self, manager, mock_provider):
        result = await manager.get_provider("comp-1")
        assert result is mock_provider

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_get_or_create_conversation_new(self, manager, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await manager.get_or_create_conversation(
            phone_number="+5511999999999",
            company_id="comp-1",
            job_vacancy_id=uuid4(),
        )
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_get_or_create_conversation_existing(self, manager, mock_db):
        existing = MagicMock()
        existing.created_at = datetime.utcnow()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_db.execute.return_value = mock_result

        result = await manager.get_or_create_conversation(
            phone_number="+5511999999999",
            company_id="comp-1",
        )
        assert result is existing

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_get_or_create_expired(self, manager, mock_db):
        expired = MagicMock()
        expired.created_at = datetime.utcnow() - timedelta(hours=100)
        expired.state = "initial"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expired
        mock_db.execute.return_value = mock_result

        result = await manager.get_or_create_conversation(
            phone_number="+5511999999999",
            company_id="comp-1",
        )
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_process_incoming_message_error(self, manager, mock_db):
        mock_db.execute.side_effect = Exception("DB down")
        result = await manager.process_incoming_message(
            phone_number="+5511999999999",
            message_content="Olá",
            company_id="comp-1",
        )
        assert "problema" in result.lower() or "técnico" in result.lower()

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_process_incoming_message_with_ref(self, manager, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch.object(manager, "_get_job_by_slug", new_callable=AsyncMock, return_value=None), \
             patch.object(manager, "_handle_state", new_callable=AsyncMock, return_value="OK"), \
             patch.object(manager, "_log_message", new_callable=AsyncMock):
            result = await manager.process_incoming_message(
                phone_number="+5511999999999",
                message_content="Ref: my-job-slug Olá",
                company_id="comp-1",
            )

    @pytest.mark.easy
    def test_conversation_timeout_hours(self, manager):
        assert manager.CONVERSATION_TIMEOUT_HOURS == 72
