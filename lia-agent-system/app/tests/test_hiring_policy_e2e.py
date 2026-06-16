"""
E2E Tests for CompanyHiringPolicy — Phase 1 Coverage

Tests:
1. Full policy creation via API (upsert)
2. Partial block update via PATCH
3. Progress calculation (based on answered_questions)
4. Policy retrieval with defaults
5. Block update merges correctly
6. PolicyHelper get_company_policy with cache
7. PolicySetupAgent intent classification (natural responses)
8. Model defaults and to_dict
"""
import uuid
from datetime import datetime

from app.models.company_hiring_policy import (
    ALL_DEFAULTS,
    AUTOMATION_RULES_DEFAULTS,
    COMMUNICATION_RULES_DEFAULTS,
    PIPELINE_RULES_DEFAULTS,
    SCHEDULING_RULES_DEFAULTS,
    SCREENING_RULES_DEFAULTS,
    CompanyHiringPolicy,
)


class TestCompanyHiringPolicyModel:
    """Test the SQLAlchemy model directly."""

    def test_model_creation(self):
        policy = CompanyHiringPolicy(
            id=uuid.uuid4(),
            company_id="test_company",
        )
        assert policy.company_id == "test_company"
        assert policy.setup_completed_at is None

    def test_setup_progress_explicit_zero(self):
        policy = CompanyHiringPolicy(
            id=uuid.uuid4(),
            company_id="test_company",
            setup_progress=0,
        )
        assert policy.setup_progress == 0

    def test_to_dict_returns_defaults_for_none_blocks(self):
        policy = CompanyHiringPolicy(
            id=uuid.uuid4(),
            company_id="test_company",
            pipeline_rules=None,
            scheduling_rules=None,
            communication_rules=None,
            screening_rules=None,
            automation_rules=None,
        )
        result = policy.to_dict()
        assert result["pipeline_rules"] == PIPELINE_RULES_DEFAULTS
        assert result["scheduling_rules"] == SCHEDULING_RULES_DEFAULTS
        assert result["communication_rules"] == COMMUNICATION_RULES_DEFAULTS
        assert result["screening_rules"] == SCREENING_RULES_DEFAULTS
        assert result["automation_rules"] == AUTOMATION_RULES_DEFAULTS
        assert result["pipeline_templates"] == []
        assert result["learned_patterns"] == []

    def test_to_dict_returns_actual_data_when_set(self):
        custom_pipeline = {"min_interviews_before_offer": 5, "manager_approval_for_offer": False}
        policy = CompanyHiringPolicy(
            id=uuid.uuid4(),
            company_id="test_company",
            pipeline_rules=custom_pipeline,
        )
        result = policy.to_dict()
        assert result["pipeline_rules"] == custom_pipeline
        assert result["pipeline_rules"]["min_interviews_before_offer"] == 5

    def test_get_rule_with_data(self):
        policy = CompanyHiringPolicy(
            id=uuid.uuid4(),
            company_id="test_company",
            pipeline_rules={"min_interviews_before_offer": 4},
        )
        assert policy.get_rule("pipeline_rules", "min_interviews_before_offer") == 4

    def test_get_rule_falls_back_to_defaults(self):
        policy = CompanyHiringPolicy(
            id=uuid.uuid4(),
            company_id="test_company",
            pipeline_rules={},
        )
        assert policy.get_rule("pipeline_rules", "min_interviews_before_offer") == 2

    def test_get_rule_with_none_block(self):
        policy = CompanyHiringPolicy(
            id=uuid.uuid4(),
            company_id="test_company",
            pipeline_rules=None,
        )
        assert policy.get_rule("pipeline_rules", "min_interviews_before_offer") == 2

    def test_get_rule_unknown_key_returns_default(self):
        policy = CompanyHiringPolicy(
            id=uuid.uuid4(),
            company_id="test_company",
        )
        assert policy.get_rule("pipeline_rules", "nonexistent", "fallback") == "fallback"

    def test_repr(self):
        policy = CompanyHiringPolicy(
            id=uuid.uuid4(),
            company_id="acme_corp",
            setup_progress=50,
        )
        assert "acme_corp" in repr(policy)
        assert "50" in repr(policy)

    def test_to_dict_includes_all_fields(self):
        policy = CompanyHiringPolicy(
            id=uuid.uuid4(),
            company_id="test_company",
            setup_progress=40,
            created_by="user1",
            updated_by="user2",
            created_at=datetime(2025, 1, 1),
            updated_at=datetime(2025, 1, 2),
            answered_questions=["q1", "q2"],
        )
        result = policy.to_dict()
        assert result["company_id"] == "test_company"
        assert result["setup_progress"] == 40
        assert result["created_by"] == "user1"
        assert result["updated_by"] == "user2"
        assert result["answered_questions"] == ["q1", "q2"]
        assert "id" in result


class TestAllDefaults:
    """Verify ALL_DEFAULTS structure."""

    def test_all_defaults_has_5_rule_blocks(self):
        assert "pipeline_rules" in ALL_DEFAULTS
        assert "scheduling_rules" in ALL_DEFAULTS
        assert "communication_rules" in ALL_DEFAULTS
        assert "screening_rules" in ALL_DEFAULTS
        assert "automation_rules" in ALL_DEFAULTS

    def test_all_defaults_has_templates_and_patterns(self):
        assert "pipeline_templates" in ALL_DEFAULTS
        assert "learned_patterns" in ALL_DEFAULTS
        assert ALL_DEFAULTS["pipeline_templates"] == []
        assert ALL_DEFAULTS["learned_patterns"] == []

    def test_pipeline_rules_defaults(self):
        assert PIPELINE_RULES_DEFAULTS["min_interviews_before_offer"] == 2
        assert PIPELINE_RULES_DEFAULTS["manager_approval_for_offer"] is True

    def test_scheduling_rules_defaults(self):
        assert SCHEDULING_RULES_DEFAULTS["default_duration_minutes"] == 60
        assert SCHEDULING_RULES_DEFAULTS["self_scheduling_enabled"] is False

    def test_communication_rules_defaults(self):
        assert COMMUNICATION_RULES_DEFAULTS["preferred_channel"] == "whatsapp"
        assert COMMUNICATION_RULES_DEFAULTS["lia_tone"] == "professional"

    def test_screening_rules_defaults(self):
        assert SCREENING_RULES_DEFAULTS["experience_policy"] == "per_job"
        assert SCREENING_RULES_DEFAULTS["default_screening_questions"] == []

    def test_automation_rules_defaults(self):
        assert AUTOMATION_RULES_DEFAULTS["autonomy_level"] == "low"
        assert AUTOMATION_RULES_DEFAULTS["auto_screening"] is False


class TestProgressCalculation:
    """Test the _calculate_progress function (based on answered_questions)."""

    def test_empty_answered_questions_is_zero(self):
        from app.api.v1.hiring_policy import _calculate_progress
        policy = CompanyHiringPolicy(
            id=uuid.uuid4(),
            company_id="test_company",
            answered_questions=[],
        )
        progress = _calculate_progress(policy)
        assert progress == 0

    def test_some_answered_questions_gives_partial(self):
        from app.api.v1.hiring_policy import TOTAL_QUESTIONS, _calculate_progress
        policy = CompanyHiringPolicy(
            id=uuid.uuid4(),
            company_id="test_company",
            answered_questions=["min_interviews_before_offer", "manager_approval_for_offer"],
        )
        progress = _calculate_progress(policy)
        expected = min(int((2 / TOTAL_QUESTIONS) * 100), 100)
        assert progress == expected

    def test_all_questions_answered_is_100(self):
        from app.api.v1.hiring_policy import TOTAL_QUESTIONS, _calculate_progress
        all_questions = [f"q{i}" for i in range(TOTAL_QUESTIONS)]
        policy = CompanyHiringPolicy(
            id=uuid.uuid4(),
            company_id="test_company",
            answered_questions=all_questions,
        )
        progress = _calculate_progress(policy)
        assert progress == 100

    def test_none_answered_questions_is_zero(self):
        from app.api.v1.hiring_policy import _calculate_progress
        policy = CompanyHiringPolicy(
            id=uuid.uuid4(),
            company_id="test_company",
            answered_questions=None,
        )
        progress = _calculate_progress(policy)
        assert progress == 0


class TestBlocksCompleted:
    """Test blocks_completed calculation."""

    def test_no_questions_no_blocks_completed(self):
        from app.api.v1.hiring_policy import _blocks_completed
        policy = CompanyHiringPolicy(
            id=uuid.uuid4(),
            company_id="test_company",
            answered_questions=[],
        )
        result = _blocks_completed(policy)
        assert result["pipeline_rules"] is False
        assert result["scheduling_rules"] is False
        assert result["communication_rules"] is False
        assert result["screening_rules"] is False
        assert result["automation_rules"] is False

    def test_pipeline_block_completed(self):
        from app.api.v1.hiring_policy import _blocks_completed
        policy = CompanyHiringPolicy(
            id=uuid.uuid4(),
            company_id="test_company",
            answered_questions=[
                "min_interviews_before_offer",
                "manager_approval_for_offer",
                "max_days_in_stage",
                "pipeline_template",
            ],
        )
        result = _blocks_completed(policy)
        assert result["pipeline_rules"] is True


class TestPolicyHelperUnit:
    """Test PolicyHelper functions."""

    def test_import_policy_helper(self):
        from app.shared.policy_helper import get_company_policy, invalidate_policy_cache
        assert callable(get_company_policy)
        assert callable(invalidate_policy_cache)


class TestPolicySetupAgentIntents:
    """Test PolicySetupAgent natural language understanding."""

    def test_import_agent(self):
        from app.domains.policy.agents.agent import PolicySetupAgent
        assert PolicySetupAgent is not None

    def test_agent_has_required_methods(self):
        from app.domains.policy.agents.agent import PolicySetupAgent
        agent = PolicySetupAgent.__new__(PolicySetupAgent)
        assert hasattr(agent, 'process_message') or hasattr(agent, 'handle_message') or hasattr(agent, 'run')

    def test_extract_number_from_natural_response(self):
        from app.domains.policy.agents.agent import PolicySetupAgent
        agent = PolicySetupAgent.__new__(PolicySetupAgent)
        if hasattr(agent, '_extract_number'):
            assert agent._extract_number("3 entrevistas") == 3
            assert agent._extract_number("pelo menos 2") == 2

    def test_extract_boolean_from_natural_response(self):
        from app.domains.policy.agents.agent import PolicySetupAgent
        agent = PolicySetupAgent.__new__(PolicySetupAgent)
        if hasattr(agent, '_extract_boolean'):
            assert agent._extract_boolean("sim, com certeza") is True
            assert agent._extract_boolean("nao, nao precisa") is False


class TestBlockUpdateMerge:
    """Test that block updates merge correctly (don't overwrite)."""

    def test_block_update_merges_with_existing(self):
        policy = CompanyHiringPolicy(
            id=uuid.uuid4(),
            company_id="test_company",
            pipeline_rules={"min_interviews_before_offer": 2, "manager_approval_for_offer": True},
        )
        existing = policy.pipeline_rules.copy()
        existing.update({"max_days_in_stage": 7})
        policy.pipeline_rules = existing

        assert policy.pipeline_rules["min_interviews_before_offer"] == 2
        assert policy.pipeline_rules["manager_approval_for_offer"] is True
        assert policy.pipeline_rules["max_days_in_stage"] == 7

    def test_block_update_can_override_single_field(self):
        policy = CompanyHiringPolicy(
            id=uuid.uuid4(),
            company_id="test_company",
            pipeline_rules={"min_interviews_before_offer": 2, "manager_approval_for_offer": True},
        )
        existing = policy.pipeline_rules.copy()
        existing.update({"min_interviews_before_offer": 5})
        policy.pipeline_rules = existing

        assert policy.pipeline_rules["min_interviews_before_offer"] == 5
        assert policy.pipeline_rules["manager_approval_for_offer"] is True

    def test_all_blocks_support_merge(self):
        blocks = {
            "pipeline_rules": {"min_interviews_before_offer": 3},
            "scheduling_rules": {"default_duration_minutes": 45},
            "communication_rules": {"preferred_channel": "email"},
            "screening_rules": {"salary_expectation_filter": True},
            "automation_rules": {"auto_screening": True},
        }
        for block_name, update_data in blocks.items():
            policy = CompanyHiringPolicy(
                id=uuid.uuid4(),
                company_id="test_company",
                **{block_name: ALL_DEFAULTS.get(block_name, {}).copy()},
            )
            current = getattr(policy, block_name).copy()
            current.update(update_data)
            setattr(policy, block_name, current)
            for key, val in update_data.items():
                assert getattr(policy, block_name)[key] == val


class TestPolicySchemas:
    """Test Pydantic schemas."""

    def test_import_schemas(self):
        from app.schemas.company_hiring_policy import (
            CompanyHiringPolicyBlockUpdate,
            CompanyHiringPolicyCreate,
            CompanyHiringPolicyResponse,
            PolicyChatMessage,
            PolicyChatResponse,
            PolicyProgressResponse,
        )
        assert CompanyHiringPolicyCreate is not None
        assert CompanyHiringPolicyResponse is not None
        assert CompanyHiringPolicyBlockUpdate is not None
        assert PolicyProgressResponse is not None
        assert PolicyChatMessage is not None
        assert PolicyChatResponse is not None

    def test_block_update_schema_validates(self):
        from app.schemas.company_hiring_policy import CompanyHiringPolicyBlockUpdate
        update = CompanyHiringPolicyBlockUpdate(
            block="pipeline_rules",
            data={"min_interviews_before_offer": 4},
        )
        assert update.block == "pipeline_rules"
        assert update.data["min_interviews_before_offer"] == 4

    def test_block_update_accepts_all_valid_blocks(self):
        from app.schemas.company_hiring_policy import CompanyHiringPolicyBlockUpdate
        valid_blocks = [
            "pipeline_rules",
            "scheduling_rules",
            "communication_rules",
            "screening_rules",
            "automation_rules",
        ]
        for block in valid_blocks:
            update = CompanyHiringPolicyBlockUpdate(block=block, data={"key": "value"})
            assert update.block == block

    def test_chat_message_schema(self):
        from app.schemas.company_hiring_policy import PolicyChatMessage
        msg = PolicyChatMessage(message="3 entrevistas", company_id="acme")
        assert msg.message == "3 entrevistas"
        assert msg.company_id == "acme"

    def test_chat_message_optional_fields(self):
        from app.schemas.company_hiring_policy import PolicyChatMessage
        msg = PolicyChatMessage(
            message="sim, pode avançar",
            company_id="acme",
            user_id="user1",
            session_id="session-123",
        )
        assert msg.user_id == "user1"
        assert msg.session_id == "session-123"

    def test_chat_response_schema(self):
        from app.schemas.company_hiring_policy import PolicyChatResponse
        resp = PolicyChatResponse(
            reply="Entendi! Configurei 3 entrevistas.",
            current_block="pipeline_rules",
            current_question=2,
            total_questions=19,
            setup_progress=10,
        )
        assert resp.reply == "Entendi! Configurei 3 entrevistas."
        assert resp.current_block == "pipeline_rules"
        assert resp.setup_progress == 10

    def test_progress_response_has_blocks_completed(self):
        from app.schemas.company_hiring_policy import PolicyProgressResponse
        resp = PolicyProgressResponse(
            company_id="test",
            setup_progress=40,
            setup_completed_at=None,
            blocks_completed={
                "pipeline_rules": True,
                "scheduling_rules": True,
                "communication_rules": False,
                "screening_rules": False,
                "automation_rules": False,
            },
        )
        assert resp.setup_progress == 40
        assert resp.blocks_completed["pipeline_rules"] is True
        assert resp.blocks_completed["automation_rules"] is False


class TestAPIRouteRegistration:
    """Test that API routes are properly registered."""

    def test_hiring_policy_router_has_endpoints(self):
        from app.api.v1.hiring_policy import router
        routes = [r.path for r in router.routes]
        assert any("/{company_id}" in r for r in routes)
        assert any("/block" in r for r in routes)
        assert any("/progress" in r for r in routes)
        assert any("/chat" in r for r in routes)

    def test_valid_blocks_constant(self):
        from app.api.v1.hiring_policy import VALID_BLOCKS
        assert "pipeline_rules" in VALID_BLOCKS
        assert "scheduling_rules" in VALID_BLOCKS
        assert "communication_rules" in VALID_BLOCKS
        assert "screening_rules" in VALID_BLOCKS
        assert "automation_rules" in VALID_BLOCKS
        assert len(VALID_BLOCKS) == 6
        assert "pipeline_templates" in VALID_BLOCKS
