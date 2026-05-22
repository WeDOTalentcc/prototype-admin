"""
Tests for Agent Robustness Module.

Tests cover:
- Intent schemas and confidence scoring
- Error handling and user-friendly messages
- Input validation and sanitization
- Context management and cancellation
- Enhanced routing with fallback chains
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.shared.agents.agent_types import AgentType
from app.shared.robustness.intent_schemas import (
    IntentSchema,
    EntityRequirement,
    EntityImportance,
    EntityType,
    get_agent_intents,
    get_intent_schema,
    ALL_INTENT_SCHEMAS
)
from app.shared.robustness.error_handling import (
    AgentError,
    AgentErrorCode,
    AgentErrorResponse,
    create_user_friendly_error,
    raise_missing_entity,
    raise_not_found
)
from app.shared.robustness.input_validation import (
    sanitize_text,
    sanitize_sql_input,
    detect_language,
    SupportedLanguage,
    is_empty_or_whitespace,
    normalize_text,
    BaseAgentInput,
    JobInput,
    CandidateInput
)
from app.shared.robustness.context_management import (
    ContextManager,
    CancellationHandler,
    HandoffContract,
    ContextStatus
)
from app.shared.robustness.defensive_prompts import (
    get_clarification_message,
    get_out_of_scope_response,
    format_confirmation_message,
    CLARIFICATION_TRIGGERS,
    OUT_OF_SCOPE_RESPONSES
)


class TestIntentSchemas:
    """Test intent schema definitions and confidence scoring."""
    
    def test_all_agents_have_intents(self):
        """Test that all main agent types have intent schemas."""
        required_agents = [
            AgentType.JOB_PLANNER,
            AgentType.SOURCING,
            AgentType.CV_SCREENING,
            AgentType.INTERVIEWER,
            AgentType.WSI_EVALUATOR,
            AgentType.SCHEDULING,
            AgentType.ANALYST_FEEDBACK,
            AgentType.ATS_INTEGRATOR,
            AgentType.TASK_PLANNER
        ]
        for agent_type in required_agents:
            intents = get_agent_intents(agent_type)
            assert len(intents) > 0, f"No intents for {agent_type.value}"
    
    def test_intent_schema_confidence_full_entities(self):
        """Test confidence is high when all entities are present."""
        schema = IntentSchema(
            intent="test_intent",
            agent_type=AgentType.JOB_PLANNER,
            description="Test",
            entity_requirements=[
                EntityRequirement(EntityType.JOB_ID, EntityImportance.REQUIRED),
                EntityRequirement(EntityType.CANDIDATE_ID, EntityImportance.RECOMMENDED),
            ],
            keywords=["test", "testing"]
        )
        
        entities = {"job_id": "123", "candidate_id": "456"}
        confidence = schema.calculate_confidence(entities, {}, "test this")
        
        assert confidence >= 0.7
    
    def test_intent_schema_confidence_missing_required(self):
        """Test confidence is lower when required entity is missing."""
        schema = IntentSchema(
            intent="test_intent",
            agent_type=AgentType.JOB_PLANNER,
            description="Test",
            entity_requirements=[
                EntityRequirement(EntityType.JOB_ID, EntityImportance.REQUIRED),
            ]
        )
        
        entities = {}
        confidence = schema.calculate_confidence(entities, {}, "")
        
        assert confidence < 0.5
    
    def test_get_intent_schema(self):
        """Test retrieving a specific intent schema."""
        schema = get_intent_schema("create_job_vacancy")
        
        assert schema is not None
        assert schema.intent == "create_job_vacancy"
        assert schema.agent_type == AgentType.JOB_PLANNER
    
    def test_schema_validation(self):
        """Test schema validation of entities."""
        schema = IntentSchema(
            intent="test",
            agent_type=AgentType.JOB_PLANNER,
            description="Test",
            entity_requirements=[
                EntityRequirement(EntityType.JOB_ID, EntityImportance.REQUIRED),
            ]
        )
        
        assert not schema.is_valid({})
        assert schema.is_valid({"job_id": "123"})


class TestErrorHandling:
    """Test error handling utilities."""
    
    def test_agent_error_creation(self):
        """Test creating an AgentError."""
        error = AgentError(
            code=AgentErrorCode.MISSING_REQUIRED_ENTITY,
            user_message="Falta informação",
            missing_entities=["job_id"]
        )
        
        assert error.code == AgentErrorCode.MISSING_REQUIRED_ENTITY
        assert "job_id" in error.missing_entities
    
    def test_agent_error_response(self):
        """Test AgentErrorResponse conversion."""
        response = AgentErrorResponse(
            code=AgentErrorCode.NOT_FOUND,
            user_message="Não encontrado",
            technical_message="Resource not found",
            retryable=False
        )
        
        data = response.to_dict()
        assert data["error"] is True
        assert data["code"] == "NOT_FOUND"
        assert data["retryable"] is False
    
    def test_user_friendly_error(self):
        """Test user-friendly error creation."""
        error = create_user_friendly_error(
            AgentErrorCode.RATE_LIMITED,
            technical_message="Too many requests"
        )
        
        assert error.retryable is True
        assert "aguarde" in error.user_message.lower()
    
    def test_raise_missing_entity(self):
        """Test raise_missing_entity helper."""
        with pytest.raises(AgentError) as exc_info:
            raise_missing_entity("job_id", "ID da vaga")
        
        assert exc_info.value.code == AgentErrorCode.MISSING_REQUIRED_ENTITY
        assert "job_id" in exc_info.value.missing_entities
    
    def test_raise_not_found(self):
        """Test raise_not_found helper."""
        with pytest.raises(AgentError) as exc_info:
            raise_not_found("Candidato", "abc123")
        
        assert exc_info.value.code == AgentErrorCode.NOT_FOUND


class TestInputValidation:
    """Test input validation and sanitization."""
    
    def test_sanitize_text_xss(self):
        """Test XSS sanitization."""
        malicious = '<script>alert("xss")</script>Hello'
        sanitized = sanitize_text(malicious)
        
        assert "<script>" not in sanitized
        assert "Hello" in sanitized
    
    def test_sanitize_text_html_entities(self):
        """Test HTML entity escaping."""
        text = '<div class="test">Content</div>'
        sanitized = sanitize_text(text)
        
        assert "<div" not in sanitized
        assert "&lt;" in sanitized or "Content" in sanitized
    
    def test_sanitize_sql_input(self):
        """Test SQL injection prevention."""
        malicious = "'; DROP TABLE users; --"
        sanitized = sanitize_sql_input(malicious)
        
        assert "DROP TABLE" not in sanitized
    
    def test_detect_language_portuguese(self):
        """Test Portuguese language detection."""
        text = "Preciso criar uma vaga para desenvolvedor"
        lang = detect_language(text)
        
        assert lang == SupportedLanguage.PT_BR
    
    def test_detect_language_english(self):
        """Test English language detection."""
        text = "I need to find candidates for this job"
        lang = detect_language(text)
        
        assert lang == SupportedLanguage.EN_US
    
    def test_is_empty_or_whitespace(self):
        """Test empty/whitespace detection."""
        assert is_empty_or_whitespace(None)
        assert is_empty_or_whitespace("")
        assert is_empty_or_whitespace("   ")
        assert not is_empty_or_whitespace("text")
    
    def test_normalize_text(self):
        """Test text normalization."""
        text = "  Olá   MUNDO  "
        normalized = normalize_text(text)
        
        assert normalized == "ola mundo"
    
    def test_job_input_validation(self):
        """Test JobInput validation."""
        valid_input = JobInput(
            intent="create_job",
            job_title="Developer",
            salary_min=5000,
            salary_max=10000
        )
        assert valid_input.job_title == "Developer"
    
    def test_job_input_salary_validation(self):
        """Test JobInput salary range validation."""
        with pytest.raises(ValueError):
            JobInput(
                intent="create_job",
                salary_min=10000,
                salary_max=5000
            )
    
    def test_candidate_email_validation(self):
        """Test CandidateInput email validation."""
        with pytest.raises(ValueError):
            CandidateInput(
                intent="add_candidate",
                candidate_email="invalid-email"
            )


class TestContextManagement:
    """Test context management and cancellation handling."""
    
    def test_context_manager_creation(self):
        """Test ContextManager initialization."""
        ctx = ContextManager(session_id="sess123", user_id="user456")
        
        assert ctx.session_id == "sess123"
        assert ctx.user_id == "user456"
        assert ctx.status == ContextStatus.ACTIVE
    
    def test_context_update_and_versioning(self):
        """Test context updates create versions."""
        ctx = ContextManager(session_id="sess", user_id="user")
        
        ctx.update("job_id", "123", agent_type="job_planner")
        ctx.update("candidate_id", "456", agent_type="sourcing")
        
        assert ctx.version == 2
        assert ctx.get("job_id") == "123"
        assert len(ctx.snapshots) == 2
    
    def test_context_rollback(self):
        """Test context rollback to previous version."""
        ctx = ContextManager(session_id="sess", user_id="user")
        
        ctx.update("key1", "value1")
        ctx.update("key2", "value2")
        ctx.update("key1", "modified")
        
        success = ctx.rollback_to_version(2)
        
        assert success
        assert ctx.version == 2
    
    def test_context_cancellation(self):
        """Test context cancellation."""
        ctx = ContextManager(session_id="sess", user_id="user")
        ctx.cancel(reason="User requested")
        
        assert ctx.status == ContextStatus.CANCELLED
    
    def test_idempotency_key(self):
        """Test idempotency key generation and checking."""
        ctx = ContextManager(session_id="sess", user_id="user")
        
        key = ctx.generate_idempotency_key("create_job", {"title": "Dev"})
        
        assert ctx.check_idempotency(key) is True
        assert ctx.check_idempotency(key) is False
    
    def test_handoff_contract(self):
        """Test handoff contract creation."""
        ctx = ContextManager(session_id="sess", user_id="user")
        ctx.update("job_id", "123")
        ctx.update("candidate_id", "456")
        ctx.current_agent = "sourcing"
        
        handoff = ctx.create_handoff(
            target_agent="cv_screening",
            shared_keys=["job_id", "candidate_id"],
            reason="Proceeding to screening"
        )
        
        assert handoff.source_agent == "sourcing"
        assert handoff.target_agent == "cv_screening"
        assert handoff.is_valid()
    
    def test_cancellation_detection(self):
        """Test cancellation keyword detection."""
        assert CancellationHandler.is_cancellation_request("quero cancelar isso")
        assert CancellationHandler.is_cancellation_request("pare com isso")
        assert CancellationHandler.is_cancellation_request("stop")
        assert not CancellationHandler.is_cancellation_request("continuar")
    
    def test_restart_detection(self):
        """Test restart keyword detection."""
        assert CancellationHandler.is_restart_request("vamos recomeçar")
        assert CancellationHandler.is_restart_request("restart")
        assert not CancellationHandler.is_restart_request("continuar")
    
    def test_confirmation_detection(self):
        """Test confirmation/denial detection."""
        assert CancellationHandler.is_confirmation("sim, pode fazer")
        assert CancellationHandler.is_confirmation("ok")
        assert CancellationHandler.is_denial("não quero")
        assert CancellationHandler.is_denial("errado")


class TestDefensivePrompts:
    """Test defensive prompt utilities."""
    
    def test_clarification_message(self):
        """Test clarification message generation."""
        message = get_clarification_message(["job_id", "candidate_id"])
        
        assert "vaga" in message.lower()
        assert "candidato" in message.lower()
    
    def test_out_of_scope_response(self):
        """Test out-of-scope responses."""
        response = get_out_of_scope_response("medical")
        
        assert "médic" in response.lower() or "saúde" in response.lower()
    
    def test_out_of_scope_general(self):
        """Test general out-of-scope response includes capabilities."""
        response = get_out_of_scope_response("general")
        
        assert "posso" in response.lower() or "fazer" in response.lower()
    
    def test_confirmation_message(self):
        """Test confirmation message formatting."""
        message = format_confirmation_message(
            action="Criar nova vaga",
            details={"Título": "Developer", "Localização": "São Paulo"}
        )
        
        assert "Criar nova vaga" in message
        assert "Developer" in message
        assert "sim" in message.lower()
    
    def test_clarification_triggers_exist(self):
        """Test that clarification triggers are defined."""
        assert "missing_job" in CLARIFICATION_TRIGGERS
        assert "missing_candidate" in CLARIFICATION_TRIGGERS
        assert "ambiguous_action" in CLARIFICATION_TRIGGERS
    
    def test_out_of_scope_categories(self):
        """Test all out-of-scope categories are defined."""
        categories = ["general", "medical", "legal", "financial", "personal"]
        for cat in categories:
            assert cat in OUT_OF_SCOPE_RESPONSES


class TestRoutingAndFallback:
    """Test enhanced routing with fallback chains."""
    
    def test_entity_requirement_satisfaction(self):
        """Test entity requirement satisfaction check."""
        req = EntityRequirement(
            EntityType.JOB_ID,
            EntityImportance.REQUIRED,
            "ID da vaga"
        )
        
        assert not req.is_satisfied({})
        assert req.is_satisfied({"job_id": "123"})
    
    def test_entity_confidence_contribution(self):
        """Test entity confidence contribution."""
        required = EntityRequirement(EntityType.JOB_ID, EntityImportance.REQUIRED)
        optional = EntityRequirement(EntityType.LOCATION, EntityImportance.OPTIONAL)
        
        assert required.get_confidence_contribution({"job_id": "123"}) > 0.3
        assert required.get_confidence_contribution({}) == 0.0
        assert optional.get_confidence_contribution({}) > 0
    
    def test_schema_missing_entities(self):
        """Test getting missing entities from schema."""
        schema = IntentSchema(
            intent="test",
            agent_type=AgentType.JOB_PLANNER,
            description="Test",
            entity_requirements=[
                EntityRequirement(EntityType.JOB_ID, EntityImportance.REQUIRED),
                EntityRequirement(EntityType.CANDIDATE_ID, EntityImportance.REQUIRED),
                EntityRequirement(EntityType.LOCATION, EntityImportance.OPTIONAL),
            ]
        )
        
        missing = schema.get_missing_entities({"location": "SP"})
        
        assert len(missing) == 2
        missing_types = [m.entity_type for m in missing]
        assert EntityType.JOB_ID in missing_types
        assert EntityType.CANDIDATE_ID in missing_types


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_message_handling(self):
        """Test handling of empty messages."""
        assert is_empty_or_whitespace("")
        assert detect_language("") == SupportedLanguage.PT_BR
    
    def test_very_long_text_sanitization(self):
        """Test sanitization of very long text."""
        long_text = "x" * 100000
        sanitized = sanitize_text(long_text, max_length=1000)
        
        assert len(sanitized) <= 1000
    
    def test_unicode_handling(self):
        """Test Unicode character handling."""
        text = "Olá, você está bem? 🎉 日本語"
        sanitized = sanitize_text(text)
        
        assert "Olá" in sanitized or "Ol" in sanitized
    
    def test_mixed_language_detection(self):
        """Test detection with mixed languages."""
        text = "I need to criar uma vaga for developer"
        lang = detect_language(text)
        
        assert lang in [SupportedLanguage.PT_BR, SupportedLanguage.EN_US]
    
    def test_context_with_no_snapshots(self):
        """Test context manager with no snapshots."""
        ctx = ContextManager(session_id="sess", user_id="user")
        
        assert ctx.version == 0
        assert len(ctx.snapshots) == 0
        assert ctx.to_dict() is not None
    
    def test_handoff_expired(self):
        """Test expired handoff contract."""
        from datetime import datetime, timedelta
        
        handoff = HandoffContract(
            source_agent="a",
            target_agent="b",
            ttl_seconds=0
        )
        handoff.created_at = datetime.utcnow() - timedelta(seconds=10)
        
        assert handoff.is_expired()
