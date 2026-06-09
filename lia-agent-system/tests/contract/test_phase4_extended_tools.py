"""
WT-2022 Fase 4 Extended — contract tests pras 5 tools high-impact.

Cobre por tool:
- Happy path (valid input → success True + ui_action correto)
- Invalid action/enum → success False
- Missing company_id → success False (multi-tenancy fail-closed)
- Cross-tenant: existing row pertence a outra company → bloqueado

Sensors: harness engineering / regression guard pro pattern Fase 4 Extended.
Pattern espelha tests/contract/test_offer_approval_gate.py (mock repos + AsyncMock).
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.domains.company_settings.agents import company_settings_tools_extended as ext


# Fixtures canonical — ContextVar tenant + mock DB
@pytest.fixture
def company_id() -> str:
    return "11111111-1111-1111-1111-111111111111"


@pytest.fixture
def other_company_id() -> str:
    return "99999999-9999-9999-9999-999999999999"


@pytest.fixture
def mock_db() -> AsyncMock:
    db = AsyncMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def set_tenant_ctxvar(company_id: str):
    """Set _current_company_id ContextVar (used by tool_handler decorator)."""
    from app.middleware import auth_enforcement as ae

    token = ae._current_company_id.set(company_id)
    yield
    ae._current_company_id.reset(token)


# ════════════════════════════════════════════════════════════════════════════
# Tool 1: toggle_communication_alert
# ════════════════════════════════════════════════════════════════════════════
class TestToggleCommunicationAlert:
    @pytest.mark.asyncio
    async def test_invalid_alert_id(self, set_tenant_ctxvar, mock_db):
        result = await ext._wrap_toggle_communication_alert(
            alert_id="not_a_real_alert", enabled=True, db=mock_db
        )
        assert result["success"] is False
        assert "alert_id invalido" in result["error"]

    @pytest.mark.asyncio
    async def test_missing_enabled_and_channel(self, set_tenant_ctxvar, mock_db):
        result = await ext._wrap_toggle_communication_alert(
            alert_id="sla_warning", db=mock_db
        )
        assert result["success"] is False
        assert "enabled" in result["error"] or "channel" in result["error"]

    @pytest.mark.asyncio
    async def test_invalid_channel(self, set_tenant_ctxvar, mock_db):
        result = await ext._wrap_toggle_communication_alert(
            alert_id="sla_warning", channel="carrier_pigeon", db=mock_db
        )
        assert result["success"] is False
        assert "channel invalido" in result["error"]

    @pytest.mark.asyncio
    async def test_happy_path_creates_config(
        self, set_tenant_ctxvar, mock_db, company_id
    ):
        repo_mock = MagicMock()
        repo_mock.get_active_config_for_company = AsyncMock(return_value=None)
        repo_mock.create_config = AsyncMock(return_value=MagicMock())
        with patch(
            "app.repositories.alert_repository.AlertRepository",
            return_value=repo_mock,
        ):
            result = await ext._wrap_toggle_communication_alert(
                alert_id="sla_warning", enabled=False, db=mock_db
            )
        assert result["success"] is True
        assert result["alert_id"] == "sla_warning"
        assert result["ui_action"] == "settings_open_tab"
        assert result["ui_action_params"]["section"] == "comunicacao-alertas"
        repo_mock.create_config.assert_awaited_once()


# ════════════════════════════════════════════════════════════════════════════
# Tool 2: update_email_signature
# ════════════════════════════════════════════════════════════════════════════
class TestUpdateEmailSignature:
    @pytest.mark.asyncio
    async def test_neither_text_nor_html(self, set_tenant_ctxvar, mock_db):
        result = await ext._wrap_update_email_signature(db=mock_db)
        assert result["success"] is False
        assert "text ou html" in result["error"]

    @pytest.mark.asyncio
    async def test_text_too_long(self, set_tenant_ctxvar, mock_db):
        result = await ext._wrap_update_email_signature(
            text="a" * 4001, db=mock_db
        )
        assert result["success"] is False
        assert "4000" in result["error"]

    @pytest.mark.asyncio
    async def test_happy_path_text_only(
        self, set_tenant_ctxvar, mock_db, company_id
    ):
        repo_mock = MagicMock()
        repo_mock.upsert = AsyncMock(return_value=MagicMock())
        with patch(
            "app.domains.communication.repositories.communication_settings_repository.CommunicationSettingsRepository",
            return_value=repo_mock,
        ):
            result = await ext._wrap_update_email_signature(
                text="Att,\nLIA", db=mock_db
            )
        assert result["success"] is True
        assert result["text_updated"] is True
        assert result["html_updated"] is False
        repo_mock.upsert.assert_awaited_once()
        called_data = repo_mock.upsert.call_args[0][1]
        assert "signature" in called_data
        assert "signature_html" not in called_data


# ════════════════════════════════════════════════════════════════════════════
# Tool 3: configure_pipeline_stage
# ════════════════════════════════════════════════════════════════════════════
class TestConfigurePipelineStage:
    @pytest.mark.asyncio
    async def test_invalid_action(self, set_tenant_ctxvar, mock_db):
        result = await ext._wrap_configure_pipeline_stage(
            action="purge", stage_data={"id": str(uuid4())}, db=mock_db
        )
        assert result["success"] is False
        assert "action invalida" in result["error"]

    @pytest.mark.asyncio
    async def test_create_missing_name(self, set_tenant_ctxvar, mock_db):
        result = await ext._wrap_configure_pipeline_stage(
            action="create", stage_data={}, db=mock_db
        )
        assert result["success"] is False
        assert "name" in result["error"]

    @pytest.mark.asyncio
    async def test_create_happy_path(
        self, set_tenant_ctxvar, mock_db, company_id
    ):
        stage_mock = MagicMock()
        stage_mock.id = uuid4()
        stage_mock.name = "Triagem Inicial"
        repo_mock = MagicMock()
        repo_mock.create = AsyncMock(return_value=stage_mock)
        with patch(
            "app.domains.recruitment.repositories.recruitment_stage_repository.RecruitmentStageRepository",
            return_value=repo_mock,
        ):
            result = await ext._wrap_configure_pipeline_stage(
                action="create",
                stage_data={
                    "name": "Triagem Inicial",
                    "display_name": "Triagem Inicial",
                    "stage_order": 1,
                },
                db=mock_db,
            )
        assert result["success"] is True
        assert result["action"] == "create"
        assert result["ui_action_params"]["section"] == "pipeline"

    @pytest.mark.asyncio
    async def test_cross_tenant_blocked(
        self, set_tenant_ctxvar, mock_db, company_id, other_company_id
    ):
        stage_uuid = uuid4()
        existing = MagicMock()
        existing.id = stage_uuid
        existing.company_id = other_company_id  # outro tenant
        existing.is_system = False
        repo_mock = MagicMock()
        repo_mock.get_by_id = AsyncMock(return_value=existing)
        with patch(
            "app.domains.recruitment.repositories.recruitment_stage_repository.RecruitmentStageRepository",
            return_value=repo_mock,
        ):
            result = await ext._wrap_configure_pipeline_stage(
                action="delete",
                stage_data={"id": str(stage_uuid)},
                db=mock_db,
            )
        assert result["success"] is False
        assert "cross-tenant" in result["error"].lower() or "outro tenant" in result["error"]


# ════════════════════════════════════════════════════════════════════════════
# Tool 4: configure_screening_questions
# ════════════════════════════════════════════════════════════════════════════
class TestConfigureScreeningQuestions:
    @pytest.mark.asyncio
    async def test_invalid_action(self, set_tenant_ctxvar, mock_db):
        result = await ext._wrap_configure_screening_questions(
            action="purge", question_data={"id": str(uuid4())}, db=mock_db
        )
        assert result["success"] is False
        assert "action invalida" in result["error"]

    @pytest.mark.asyncio
    async def test_add_missing_text(self, set_tenant_ctxvar, mock_db):
        result = await ext._wrap_configure_screening_questions(
            action="add", question_data={}, db=mock_db
        )
        assert result["success"] is False
        assert "question_text" in result["error"]

    @pytest.mark.asyncio
    async def test_add_invalid_type(self, set_tenant_ctxvar, mock_db):
        result = await ext._wrap_configure_screening_questions(
            action="add",
            question_data={
                "question_text": "Voce tem CNH?",
                "question_type": "morse_code",
            },
            db=mock_db,
        )
        assert result["success"] is False
        assert "question_type invalido" in result["error"]

    @pytest.mark.asyncio
    async def test_add_happy_path(self, set_tenant_ctxvar, mock_db, company_id):
        q_mock = MagicMock()
        q_mock.id = uuid4()
        q_mock.question_text = "Voce tem CNH categoria B?"
        repo_mock = MagicMock()
        repo_mock.get_last_order = AsyncMock(return_value=2)
        repo_mock.create = AsyncMock(return_value=q_mock)
        with patch(
            "app.domains.recruitment.repositories.screening_question_repository.ScreeningQuestionRepository",
            return_value=repo_mock,
        ):
            result = await ext._wrap_configure_screening_questions(
                action="add",
                question_data={
                    "question_text": "Voce tem CNH categoria B?",
                    "question_type": "yes_no",
                    "is_eliminatory": True,
                    "expected_answer": "Sim",
                    "category": "logistics",
                },
                db=mock_db,
            )
        assert result["success"] is True
        assert result["action"] == "add"
        assert result["ui_action_params"]["section"] == "screening"

    @pytest.mark.asyncio
    async def test_cross_tenant_blocked(
        self, set_tenant_ctxvar, mock_db, company_id, other_company_id
    ):
        q_uuid = uuid4()
        existing = MagicMock()
        existing.id = q_uuid
        existing.company_id = other_company_id
        repo_mock = MagicMock()
        repo_mock.get_by_id = AsyncMock(return_value=existing)
        with patch(
            "app.domains.recruitment.repositories.screening_question_repository.ScreeningQuestionRepository",
            return_value=repo_mock,
        ):
            result = await ext._wrap_configure_screening_questions(
                action="remove",
                question_data={"id": str(q_uuid)},
                db=mock_db,
            )
        assert result["success"] is False
        assert "tenant" in result["error"].lower()


# ════════════════════════════════════════════════════════════════════════════
# Tool 5: set_communication_schedule
# ════════════════════════════════════════════════════════════════════════════
class TestSetCommunicationSchedule:
    @pytest.mark.asyncio
    async def test_no_fields_provided(self, set_tenant_ctxvar, mock_db):
        result = await ext._wrap_set_communication_schedule(db=mock_db)
        assert result["success"] is False
        assert "informe ao menos um campo" in result["error"]

    @pytest.mark.asyncio
    async def test_start_out_of_range(self, set_tenant_ctxvar, mock_db):
        result = await ext._wrap_set_communication_schedule(
            sending_hours_start=3, db=mock_db
        )
        assert result["success"] is False
        assert "6" in result["error"] and "12" in result["error"]

    @pytest.mark.asyncio
    async def test_end_out_of_range(self, set_tenant_ctxvar, mock_db):
        result = await ext._wrap_set_communication_schedule(
            sending_hours_end=23, db=mock_db
        )
        assert result["success"] is False
        assert "18" in result["error"] and "22" in result["error"]

    @pytest.mark.asyncio
    async def test_start_and_end_boundaries_ok(
        self, set_tenant_ctxvar, mock_db, company_id
    ):
        # Boundaries 12 (max start) and 18 (min end) — should succeed since
        # 12 < 18. Validates the start >= end check is correctly OFF here.
        repo_mock = MagicMock()
        repo_mock.upsert = AsyncMock(return_value=MagicMock())
        with patch(
            "app.domains.communication.repositories.communication_settings_repository.CommunicationSettingsRepository",
            return_value=repo_mock,
        ):
            result = await ext._wrap_set_communication_schedule(
                sending_hours_start=12, sending_hours_end=18, db=mock_db
            )
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_max_messages_out_of_range(self, set_tenant_ctxvar, mock_db):
        result = await ext._wrap_set_communication_schedule(
            max_messages_per_day=100, db=mock_db
        )
        assert result["success"] is False
        assert "50" in result["error"]

    @pytest.mark.asyncio
    async def test_happy_path(self, set_tenant_ctxvar, mock_db, company_id):
        repo_mock = MagicMock()
        repo_mock.upsert = AsyncMock(return_value=MagicMock())
        with patch(
            "app.domains.communication.repositories.communication_settings_repository.CommunicationSettingsRepository",
            return_value=repo_mock,
        ):
            result = await ext._wrap_set_communication_schedule(
                sending_hours_start=9,
                sending_hours_end=19,
                respect_weekends=True,
                max_messages_per_day=3,
                db=mock_db,
            )
        assert result["success"] is True
        assert result["schedule_updated"] is True
        assert "sending_hours_start" in result["updated_fields"]
        assert "sending_hours_end" in result["updated_fields"]
        assert "respect_weekends" in result["updated_fields"]
        assert "max_messages_per_day" in result["updated_fields"]
        assert result["ui_action_params"]["section"] == "comunicacao-alertas"


# ════════════════════════════════════════════════════════════════════════════
# Multi-tenancy fail-closed: company_id missing from ContextVar
# ════════════════════════════════════════════════════════════════════════════
class TestMultiTenancyFailClosed:
    @pytest.mark.asyncio
    async def test_no_ctxvar_blocks_tool(self, mock_db):
        # No set_tenant_ctxvar fixture → ContextVar empty → tool_handler returns
        # _TENANT_REQUIRED_RESPONSE (success=False).
        result = await ext._wrap_toggle_communication_alert(
            alert_id="sla_warning", enabled=True, db=mock_db
        )
        assert result.get("success") is False


# ════════════════════════════════════════════════════════════════════════════
# Registry contract: 5 new tools wired in TOOL_DEFINITIONS + STAGE_TOOLS
# ════════════════════════════════════════════════════════════════════════════
class TestRegistryWiring:
    def test_all_5_tools_in_registry(self):
        from app.domains.company_settings.agents.company_tool_registry import (
            get_company_settings_tools,
        )

        names = {t.name for t in get_company_settings_tools()}
        expected = {
            "toggle_communication_alert",
            "update_email_signature",
            "configure_pipeline_stage",
            "configure_screening_questions",
            "set_communication_schedule",
        }
        assert expected.issubset(names), f"missing: {expected - names}"

    def test_stage_tools_allowlist_extended(self):
        from app.domains.company_settings.agents.company_tool_registry import (
            STAGE_TOOLS,
        )

        assert "toggle_communication_alert" in STAGE_TOOLS["comunicacao-alertas"]
        assert "set_communication_schedule" in STAGE_TOOLS["comunicacao-alertas"]
        assert "update_email_signature" in STAGE_TOOLS["templates-assinatura"]
        assert "configure_pipeline_stage" in STAGE_TOOLS["pipeline"]
        assert "configure_screening_questions" in STAGE_TOOLS["screening"]
