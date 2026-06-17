"""
E2E Tests for AI/LLM Pipeline Integration
Tests all 6 phases of the LLM-powered pipeline system.
Each test validates functionality AND fallback behavior.
"""
import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock

# Phase 2: InterpretContextLLMService
class TestInterpretContextLLM:
    """Tests for LLM-powered context interpretation."""
    
    @pytest.mark.asyncio
    async def test_interpret_with_llm_success(self):
        """LLM should extract preferences from mini-prompt."""
        from app.domains.communication.services.interpret_context_llm_service import interpret_with_llm
        
        mock_response = json.dumps({
            "extracted_preferences": {
                "date": "terça",
                "time": "14h",
                "format": "remoto"
            },
            "suggested_sub_status": "agendado",
            "suggested_action": "lia_auto",
            "urgency": "normal",
            "lia_message": "Vou agendar a entrevista para terça às 14h, remoto.",
            "confidence": 0.92,
            "reasoning": "Recrutador pediu agendamento com data e hora específicas"
        })
        
        with patch("app.domains.communication.services.interpret_context_llm_service.is_llm_available", return_value=True), \
             patch("app.domains.communication.services.interpret_context_llm_service.llm_complete", new_callable=AsyncMock, return_value=mock_response), \
             patch("app.domains.communication.services.interpret_context_llm_service.settings") as mock_settings:
            mock_settings.ENABLE_LLM_INTERPRET_CONTEXT = True
            
            result = await interpret_with_llm(
                prompt="agendar entrevista terça 14h remoto",
                candidate_name="Maria Silva",
                job_title="Dev Senior",
                from_stage="screening",
                to_stage="interview",
                action_behavior="scheduling",
            )
        
        assert result is not None
        assert result["suggested_action"] == "lia_auto"
        assert result["confidence"] == 0.92
        assert result["method"] == "llm"
        assert result["extracted_preferences"]["date"] == "terça"
        assert result["extracted_preferences"]["time"] == "14h"
    
    @pytest.mark.asyncio
    async def test_interpret_fallback_when_llm_unavailable(self):
        """Should return None when LLM is unavailable."""
        from app.domains.communication.services.interpret_context_llm_service import interpret_with_llm
        
        with patch("app.domains.communication.services.interpret_context_llm_service.is_llm_available", return_value=False), \
             patch("app.domains.communication.services.interpret_context_llm_service.settings") as mock_settings:
            mock_settings.ENABLE_LLM_INTERPRET_CONTEXT = True
            
            result = await interpret_with_llm(prompt="agendar terça")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_interpret_fallback_when_feature_disabled(self):
        """Should return None when feature flag is disabled."""
        from app.domains.communication.services.interpret_context_llm_service import interpret_with_llm
        
        with patch("app.domains.communication.services.interpret_context_llm_service.settings") as mock_settings:
            mock_settings.ENABLE_LLM_INTERPRET_CONTEXT = False
            
            result = await interpret_with_llm(prompt="agendar terça")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_interpret_handles_invalid_json(self):
        """Should return None when LLM returns invalid JSON."""
        from app.domains.communication.services.interpret_context_llm_service import interpret_with_llm
        
        with patch("app.domains.communication.services.interpret_context_llm_service.is_llm_available", return_value=True), \
             patch("app.domains.communication.services.interpret_context_llm_service.llm_complete", new_callable=AsyncMock, return_value="not valid json"), \
             patch("app.domains.communication.services.interpret_context_llm_service.settings") as mock_settings:
            mock_settings.ENABLE_LLM_INTERPRET_CONTEXT = True
            
            result = await interpret_with_llm(prompt="agendar terça")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_interpret_empty_prompt(self):
        """Should return None for empty prompt."""
        from app.domains.communication.services.interpret_context_llm_service import interpret_with_llm
        
        with patch("app.domains.communication.services.interpret_context_llm_service.settings") as mock_settings:
            mock_settings.ENABLE_LLM_INTERPRET_CONTEXT = True
            
            result = await interpret_with_llm(prompt="")
            assert result is None
            
            result = await interpret_with_llm(prompt="   ")
            assert result is None


# Phase 3: CandidateContextAggregator
class TestCandidateContextAggregator:
    """Tests for candidate context aggregation."""
    
    @pytest.mark.asyncio
    async def test_aggregate_returns_default_on_missing_candidate(self):
        """Should return default context when candidate not found."""
        from app.domains.automation.services.candidate_context_aggregator import CandidateContextAggregator
        
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        aggregator = CandidateContextAggregator(mock_db)
        context = await aggregator.aggregate("nonexistent-id")
        
        assert context["vacancy_candidate_id"] == "nonexistent-id"
        assert context["name"] == ""
        assert context["wsi_score"] == {}
        assert context["interview_notes"] == []


# Phase 5: InferBehavior with LLM
class TestInferBehaviorLLM:
    """Tests for LLM-powered behavior inference."""
    
    @pytest.mark.asyncio
    async def test_infer_behavior_llm_success(self):
        """LLM should classify custom stage names."""
        from app.domains.communication.services.infer_behavior_service import infer_behavior_llm
        
        mock_response = json.dumps({
            "suggested_behavior": "evaluation",
            "confidence": 0.88,
            "reasoning": "A etapa 'Teste Prático' indica uma avaliação técnica",
            "alternatives": [{"behavior": "screening", "confidence": 0.4}]
        })
        
        with patch("app.domains.communication.services.infer_behavior_service.is_llm_available", return_value=True), \
             patch("app.domains.communication.services.infer_behavior_service.llm_complete", new_callable=AsyncMock, return_value=mock_response), \
             patch("app.domains.communication.services.infer_behavior_service.settings") as mock_settings:
            mock_settings.ENABLE_LLM_INFER_BEHAVIOR = True
            
            result = await infer_behavior_llm("Teste Prático de Código")
        
        assert result["suggested_behavior"] == "evaluation"
        assert result["confidence"] == 0.88
        assert result["method"] == "llm"
    
    @pytest.mark.asyncio
    async def test_infer_behavior_auto_keyword_sufficient(self):
        """Auto mode should use keywords when confidence is high."""
        from app.domains.communication.services.infer_behavior_service import infer_behavior_auto
        
        result = await infer_behavior_auto("Entrevista Técnica")
        assert result["suggested_behavior"] == "scheduling"
        assert result["confidence"] >= 0.7
    
    @pytest.mark.asyncio
    async def test_infer_behavior_auto_escalates_to_llm(self):
        """Auto mode should escalate to LLM when keyword confidence is low."""
        from app.domains.communication.services.infer_behavior_service import infer_behavior_auto, infer_behavior
        
        keyword_result = infer_behavior("Etapa Customizada XYZ")
        
        if keyword_result["confidence"] < 0.7:
            mock_response = json.dumps({
                "suggested_behavior": "passive",
                "confidence": 0.75,
                "reasoning": "Nome genérico sem indicação clara de ação",
                "alternatives": []
            })
            
            with patch("app.domains.communication.services.infer_behavior_service.is_llm_available", return_value=True), \
                 patch("app.domains.communication.services.infer_behavior_service.llm_complete", new_callable=AsyncMock, return_value=mock_response), \
                 patch("app.domains.communication.services.infer_behavior_service.settings") as mock_settings:
                mock_settings.ENABLE_LLM_INFER_BEHAVIOR = True
                
                result = await infer_behavior_auto("Etapa Customizada XYZ")
            
            assert result["method"] == "llm"
    
    @pytest.mark.asyncio
    async def test_infer_behavior_llm_validates_behavior(self):
        """LLM result with invalid behavior should fallback to keywords."""
        from app.domains.communication.services.infer_behavior_service import infer_behavior_llm
        
        mock_response = json.dumps({
            "suggested_behavior": "invalid_behavior_xyz",
            "confidence": 0.9,
            "reasoning": "test",
            "alternatives": []
        })
        
        with patch("app.domains.communication.services.infer_behavior_service.is_llm_available", return_value=True), \
             patch("app.domains.communication.services.infer_behavior_service.llm_complete", new_callable=AsyncMock, return_value=mock_response), \
             patch("app.domains.communication.services.infer_behavior_service.settings") as mock_settings:
            mock_settings.ENABLE_LLM_INFER_BEHAVIOR = True
            
            result = await infer_behavior_llm("Triagem Inicial")
        
        assert result["method"] == "keyword_fallback"


# Phase 6: PipelineTransitionDomain
class TestPipelineTransitionDomain:
    """Tests for the pipeline transition domain."""
    
    def test_domain_config(self):
        """Domain should expose correct config."""
        from app.domains.pipeline.domain import get_domain_config
        
        config = get_domain_config()
        assert config["name"] == "pipeline_transition"
        assert len(config["tools"]) >= 4
        assert "handler" in config
    
    @pytest.mark.asyncio
    async def test_handle_unknown_tool(self):
        """Should return error for unknown tools."""
        from app.domains.pipeline.domain import handle_tool_call
        
        result = await handle_tool_call("unknown_tool", {})
        assert result["success"] is False
        assert "Unknown tool" in result["error"]
    
    @pytest.mark.asyncio
    async def test_handle_list_stages(self):
        """Should return pipeline stages."""
        from app.domains.pipeline.domain import handle_tool_call
        
        result = await handle_tool_call("list_pipeline_stages", {"company_id": "test"})
        assert result["success"] is True
        assert "stages" in result
        assert len(result["stages"]) > 0


# Phase 6.3: KanbanAssistantService
class TestKanbanAssistantService:
    """Tests for Kanban assistant suggestions."""
    
    @pytest.mark.asyncio
    async def test_stale_candidate_suggestion(self):
        """Should suggest action for stale candidates."""
        from app.domains.pipeline.kanban_assistant_service import KanbanAssistantService
        
        candidates = [
            {"id": "1", "name": "João Silva", "days_in_stage": 10, "wsi_score": 70},
        ]
        
        suggestions = await KanbanAssistantService.get_suggestions(
            candidates_in_stage=candidates,
            stage_name="Triagem",
            action_behavior="screening",
        )
        
        assert len(suggestions) >= 1
        stale = [s for s in suggestions if s["type"] == "stale_candidate"]
        assert len(stale) == 1
        assert stale[0]["candidate_name"] == "João Silva"
    
    @pytest.mark.asyncio
    async def test_high_score_suggestion(self):
        """Should suggest advancing high-score candidates."""
        from app.domains.pipeline.kanban_assistant_service import KanbanAssistantService
        
        candidates = [
            {"id": "2", "name": "Ana Costa", "days_in_stage": 2, "wsi_score": 85},
        ]
        
        suggestions = await KanbanAssistantService.get_suggestions(
            candidates_in_stage=candidates,
            stage_name="Triagem",
            action_behavior="screening",
        )
        
        high_score = [s for s in suggestions if s["type"] == "high_score"]
        assert len(high_score) == 1
    
    @pytest.mark.asyncio
    async def test_empty_candidates(self):
        """Should handle empty candidate list."""
        from app.domains.pipeline.kanban_assistant_service import KanbanAssistantService
        
        suggestions = await KanbanAssistantService.get_suggestions(
            candidates_in_stage=[],
            stage_name="Triagem",
            action_behavior="screening",
        )
        
        assert suggestions == []


# Feature Flags
class TestFeatureFlags:
    """Tests for AI feature flags."""
    
    def test_all_flags_exist(self):
        """All AI feature flags should exist in settings."""
        from app.core.config import settings
        
        assert hasattr(settings, "ENABLE_LLM_INTERPRET_CONTEXT")
        assert hasattr(settings, "ENABLE_LLM_DISPATCH_PERSONALIZATION")
        assert hasattr(settings, "ENABLE_LLM_INFER_BEHAVIOR")
        assert hasattr(settings, "ENABLE_LLM_SUBSTATUS_PREDICTION")
    
    def test_flags_default_true(self):
        """All AI feature flags should default to True."""
        from app.core.config import settings
        
        assert settings.ENABLE_LLM_INTERPRET_CONTEXT is True
        assert settings.ENABLE_LLM_DISPATCH_PERSONALIZATION is True
        assert settings.ENABLE_LLM_INFER_BEHAVIOR is True
        assert settings.ENABLE_LLM_SUBSTATUS_PREDICTION is True


# LLM Client
class TestLLMClient:
    """Tests for unified LLM client."""
    
    def test_is_llm_available(self):
        """LLM availability check should not crash."""
        from app.shared.providers.llm_client import is_llm_available
        result = is_llm_available()
        assert isinstance(result, bool)
