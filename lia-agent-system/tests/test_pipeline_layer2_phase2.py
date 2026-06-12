"""
Tests for Pipeline Layer 2 Phase 2 - Batch Rejection, Real Data, Webhooks
Tests cover: Bulk prediction, webhook adapters, context aggregation, message generation.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock


class TestBulkSubStatusPrediction:
    """Tests for bulk-predict-substatus endpoint."""

    def test_bulk_predict_multiple_candidates_rejected(self):
        """Test predicting substatus for multiple candidates being rejected."""
        from app.domains.automation.services.stage_transition_automation import SubStatusPredictor

        candidates = [
            {
                "name": "Candidate A",
                "wsi_score": {"overall": 30, "technical": 25, "behavioral": 50, "cultural": 40},
                "interview_notes": [],
                "lia_parecer": {},
                "job": {"has_hired_candidate": False}
            },
            {
                "name": "Candidate B",
                "wsi_score": {"overall": 85, "technical": 90, "behavioral": 80, "cultural": 85},
                "interview_notes": [],
                "lia_parecer": {},
                "job": {"has_hired_candidate": True}
            },
            {
                "name": "Candidate C",
                "wsi_score": {"overall": 60, "technical": 70, "behavioral": 65, "cultural": 30},
                "interview_notes": [],
                "lia_parecer": {},
                "job": {"has_hired_candidate": False}
            }
        ]

        results = []
        for candidate in candidates:
            result = SubStatusPredictor.predict(candidate, "interview_technical", "rejected")
            results.append(result)

        assert results[0]["predicted_substatus"] == "lacking_technical_skills"  # low tech score
        assert results[1]["predicted_substatus"] == "another_candidate_selected"  # job has hire
        assert results[2]["predicted_substatus"] == "cultural_mismatch"  # low cultural score

        for r in results:
            assert "confidence" in r
            assert "reasoning" in r
            assert 0 <= r["confidence"] <= 1

    def test_bulk_predict_non_rejection_default_substatus(self):
        """Test non-rejection transitions get default substatus."""
        from app.domains.automation.services.stage_transition_automation import SubStatusPredictor

        result = SubStatusPredictor.predict({}, "sourcing", "screening")
        assert result["predicted_substatus"] == "cv_received"
        assert result["confidence"] >= 0.85

    def test_bulk_predict_feature_flag_off_uses_deterministic(self):
        """Test that disabling feature flag uses deterministic prediction."""
        from app.domains.automation.services.stage_transition_automation import SubStatusPredictor

        result = SubStatusPredictor.predict(
            {"wsi_score": {"overall": 20}, "job": {}},
            "screening",
            "rejected"
        )
        assert result["predicted_substatus"] in [
            "under_qualified", "another_candidate_selected", "lacking_technical_skills"
        ]

    def test_bulk_predict_manager_rejection(self):
        """Test rejection from manager stage."""
        from app.domains.automation.services.stage_transition_automation import SubStatusPredictor

        result = SubStatusPredictor.predict(
            {"wsi_score": {}, "job": {}},
            "interview_manager",
            "rejected"
        )
        assert result["predicted_substatus"] == "another_candidate_selected"

    def test_bulk_predict_with_interview_gaps(self):
        """Test rejection with technical interview gaps."""
        from app.domains.automation.services.stage_transition_automation import SubStatusPredictor

        context = {
            "wsi_score": {"overall": 55, "technical": 55},
            "interview_notes": [
                {
                    "stage": "interview_technical",
                    "gaps": ["SQL", "System Design", "API Architecture"],
                    "strengths": ["Communication"]
                }
            ],
            "job": {}
        }

        result = SubStatusPredictor.predict(context, "interview_technical", "rejected")
        assert result["predicted_substatus"] == "lacking_technical_skills"


class TestWebhookAdapters:
    """Tests for webhook adapters with idempotency."""

    @pytest.fixture(autouse=True)
    def reset_adapters(self):
        from app.domains.automation.services.webhook_adapters import (
            InterviewWebhookAdapter, TestWebhookAdapter, DocumentWebhookAdapter, WebhookAdapter
        )
        WebhookAdapter._processed_events = set()
        WebhookAdapter._event_log = []
        yield

    @pytest.mark.asyncio
    async def test_interview_webhook_confirmed(self):
        from app.domains.automation.services.webhook_adapters import InterviewWebhookAdapter

        result = await InterviewWebhookAdapter.process(
            "evt-001", "interview_confirmed",
            {"candidate_id": "c1", "vacancy_id": "v1", "interview_date": "2025-03-01T14:00:00"}
        )

        assert result["status"] == "processed"
        assert result["mapped_sub_status"] == "interview_confirmed"
        assert result["candidate_id"] == "c1"

    @pytest.mark.asyncio
    async def test_interview_webhook_idempotency(self):
        from app.domains.automation.services.webhook_adapters import InterviewWebhookAdapter

        result1 = await InterviewWebhookAdapter.process("evt-dup", "interview_confirmed", {"candidate_id": "c1"})
        result2 = await InterviewWebhookAdapter.process("evt-dup", "interview_confirmed", {"candidate_id": "c1"})

        assert result1["status"] == "processed"
        assert result2["status"] == "duplicate"

    @pytest.mark.asyncio
    async def test_test_webhook_completed(self):
        from app.domains.automation.services.webhook_adapters import TestWebhookAdapter

        result = await TestWebhookAdapter.process(
            "evt-002", "test_completed",
            {"candidate_id": "c2", "score": 85, "test_type": "technical", "duration_minutes": 45}
        )

        assert result["status"] == "processed"
        assert result["mapped_sub_status"] == "test_completed"
        assert result["test_data"]["score"] == 85

    @pytest.mark.asyncio
    async def test_document_webhook(self):
        from app.domains.automation.services.webhook_adapters import DocumentWebhookAdapter

        result = await DocumentWebhookAdapter.process(
            "evt-003", "document_submitted",
            {"candidate_id": "c3", "document_type": "diploma", "file_url": "https://storage.example.com/doc.pdf"}
        )

        assert result["status"] == "processed"
        assert result["mapped_sub_status"] == "documents_received"
        assert result["document_data"]["document_type"] == "diploma"

    @pytest.mark.asyncio
    async def test_event_log_tracking(self):
        from app.domains.automation.services.webhook_adapters import InterviewWebhookAdapter, WebhookAdapter

        await InterviewWebhookAdapter.process("evt-log1", "interview_confirmed", {"candidate_id": "c1"})
        await InterviewWebhookAdapter.process("evt-log2", "interview_completed", {"candidate_id": "c2"})

        log = WebhookAdapter.get_event_log()
        assert len(log) == 2
        assert log[0]["event_id"] == "evt-log1"
        assert log[1]["event_id"] == "evt-log2"

    @pytest.mark.asyncio
    async def test_cross_adapter_idempotency(self):
        """Idempotency is shared across adapters (same base class state)."""
        from app.domains.automation.services.webhook_adapters import InterviewWebhookAdapter, TestWebhookAdapter

        result1 = await InterviewWebhookAdapter.process("shared-evt", "interview_confirmed", {})
        result2 = await TestWebhookAdapter.process("shared-evt", "test_completed", {})

        assert result1["status"] == "processed"
        assert result2["status"] == "duplicate"


class TestCandidateContextAggregator:
    """Tests for CandidateContextAggregator with real data extraction."""

    def test_extract_wsi_score_from_metadata(self):
        from app.domains.automation.services.candidate_context_aggregator import CandidateContextAggregator

        mock_vc = MagicMock()
        mock_vc.metadata = {"wsi_score": {"overall": 75, "technical": 80}}
        mock_vc.screening_data = None

        aggregator = CandidateContextAggregator(db=MagicMock())
        result = aggregator._extract_wsi_score(mock_vc)

        assert result["overall"] == 75
        assert result["technical"] == 80

    def test_extract_wsi_score_from_screening_data(self):
        from app.domains.automation.services.candidate_context_aggregator import CandidateContextAggregator

        mock_vc = MagicMock()
        mock_vc.metadata = {}
        mock_vc.screening_data = {"wsi_score": {"overall": 60}}

        aggregator = CandidateContextAggregator(db=MagicMock())
        result = aggregator._extract_wsi_score(mock_vc)

        assert result["overall"] == 60

    def test_extract_wsi_score_from_attribute(self):
        from app.domains.automation.services.candidate_context_aggregator import CandidateContextAggregator

        mock_vc = MagicMock()
        mock_vc.metadata = {}
        mock_vc.screening_data = {}
        mock_vc.wsi_score = 72

        aggregator = CandidateContextAggregator(db=MagicMock())
        result = aggregator._extract_wsi_score(mock_vc)

        assert result == {"overall": 72}

    def test_extract_interview_notes_from_metadata(self):
        from app.domains.automation.services.candidate_context_aggregator import CandidateContextAggregator

        notes = [{"stage": "interview_hr", "rating": 4, "strengths": ["comunicação"], "gaps": []}]
        mock_vc = MagicMock()
        mock_vc.metadata = {"interview_notes": notes}

        aggregator = CandidateContextAggregator(db=MagicMock())
        result = aggregator._extract_interview_notes(mock_vc)

        assert len(result) == 1
        assert result[0]["stage"] == "interview_hr"

    def test_extract_lia_parecer(self):
        from app.domains.automation.services.candidate_context_aggregator import CandidateContextAggregator

        parecer = {"summary": "Bom candidato", "strengths": ["liderança"], "development_areas": ["SQL"]}
        mock_vc = MagicMock()
        mock_vc.metadata = {"lia_parecer": parecer}

        aggregator = CandidateContextAggregator(db=MagicMock())
        result = aggregator._extract_lia_parecer(mock_vc)

        assert result["summary"] == "Bom candidato"
        assert "liderança" in result["strengths"]

    def test_extract_stage_history_from_metadata(self):
        from app.domains.automation.services.candidate_context_aggregator import CandidateContextAggregator

        history = [
            {"stage": "sourcing", "timestamp": "2025-01-01T00:00:00"},
            {"stage": "screening", "timestamp": "2025-01-05T00:00:00"}
        ]
        mock_vc = MagicMock()
        mock_vc.metadata = {"stage_history": history}

        aggregator = CandidateContextAggregator(db=MagicMock())
        result = aggregator._extract_stage_history(mock_vc)

        assert len(result) == 2
        assert result[0]["stage"] == "sourcing"

    def test_extract_empty_context_gracefully(self):
        from app.domains.automation.services.candidate_context_aggregator import CandidateContextAggregator

        mock_vc = MagicMock()
        mock_vc.metadata = None
        mock_vc.screening_data = None
        mock_vc.wsi_score = None

        aggregator = CandidateContextAggregator(db=MagicMock())

        assert aggregator._extract_wsi_score(mock_vc) == {}
        assert aggregator._extract_interview_notes(mock_vc) == []
        assert aggregator._extract_lia_parecer(mock_vc) == {}


class TestMessageGeneration:
    """Tests for message generation with personalization."""

    @pytest.mark.asyncio
    async def test_fallback_message_rejected(self):
        from app.domains.automation.services.stage_transition_automation import MessageGenerator

        result = MessageGenerator._generate_fallback(
            {"name": "João Silva", "current_title": "Dev Python"},
            "rejected",
            "profile_not_aligned",
            {"title": "Engenheiro Senior"},
            "email"
        )

        assert "João" in result["body"]
        assert "Engenheiro Senior" in result["body"]
        assert result["subject"] is not None
        assert result["metadata"]["generated_by"] == "fallback_template"

    @pytest.mark.asyncio
    async def test_fallback_message_non_rejected(self):
        from app.domains.automation.services.stage_transition_automation import MessageGenerator

        result = MessageGenerator._generate_fallback(
            {"name": "Maria Costa"},
            "screening",
            "cv_received",
            {"title": "Analista de Dados"},
            "whatsapp"
        )

        assert "Maria" in result["body"]
        assert result["subject"] is None  # WhatsApp has no subject

    def test_personalization_data_building(self):
        from app.domains.automation.services.stage_transition_automation import MessageGenerator

        context = {
            "wsi_score": {"overall": 72, "technical": 80, "behavioral": 65},
            "lia_parecer": {"strengths": ["liderança", "comunicação"], "development_areas": ["SQL"]},
            "interview_notes": [
                {"stage": "interview_hr", "strengths": ["proatividade"], "gaps": ["inglês"]}
            ]
        }

        result = MessageGenerator._build_personalization_data(context)

        # Contrato seguro (auditoria 2026-06-10): scores/gaps/notas internas NAO
        # entram no prompt do LLM. So pontos fortes curados (positivos).
        assert "72" not in result and "80" not in result and "65" not in result
        assert "SQL" not in result          # gaps/development_areas fora
        assert "inglês" not in result        # gap de entrevista fora
        assert "proatividade" not in result  # nota verbatim de entrevistador fora
        assert "liderança" in result and "comunicação" in result  # strengths mantidos

    def test_personalization_data_empty_context(self):
        from app.domains.automation.services.stage_transition_automation import MessageGenerator

        result = MessageGenerator._build_personalization_data({})
        assert "não disponíveis" in result.lower() or "Dados" in result


class TestPredictSubstatusFromDb:
    """Tests for predict_substatus_from_db and predict_substatus_bulk_from_db."""
    
    @pytest.mark.asyncio
    async def test_predict_from_db_with_session(self):
        """Test prediction with a mock DB session providing real data."""
        from app.domains.automation.services.stage_transition_automation import StageTransitionAutomationService
        
        service = StageTransitionAutomationService()
        
        with patch('app.domains.automation.services.candidate_context_aggregator.CandidateContextAggregator') as MockAgg:
            mock_aggregator = AsyncMock()
            mock_aggregator.aggregate.return_value = {
                "wsi_score": {"overall": 35, "technical": 25},
                "interview_notes": [],
                "lia_parecer": {},
                "job": {"has_hired_candidate": False},
                "stage_history": [{"stage": "screening"}],
                "email": "test@example.com",
            }
            MockAgg.return_value = mock_aggregator
            
            result = await service.predict_substatus_from_db(
                vacancy_candidate_id="vc-001",
                from_stage="screening",
                to_stage="rejected",
                db=MagicMock(),
            )
            
            assert result["predicted_substatus"] in [
                "under_qualified", "lacking_technical_skills", "another_candidate_selected"
            ]
            assert "confidence" in result
            assert "reasoning" in result
            mock_aggregator.aggregate.assert_called_once_with("vc-001")
    
    @pytest.mark.asyncio
    async def test_predict_from_db_without_session(self):
        """Test fallback when no DB session provided."""
        from app.domains.automation.services.stage_transition_automation import StageTransitionAutomationService
        
        service = StageTransitionAutomationService()
        result = await service.predict_substatus_from_db(
            vacancy_candidate_id="vc-001",
            from_stage="screening",
            to_stage="rejected",
            db=None,
        )
        
        assert result["predicted_substatus"] is not None
        assert "confidence" in result
    
    @pytest.mark.asyncio
    async def test_predict_bulk_from_db(self):
        """Test bulk prediction with mock DB session."""
        from app.domains.automation.services.stage_transition_automation import StageTransitionAutomationService
        
        service = StageTransitionAutomationService()
        
        with patch('app.domains.automation.services.candidate_context_aggregator.CandidateContextAggregator') as MockAgg:
            mock_aggregator = AsyncMock()
            mock_aggregator.aggregate_bulk.return_value = {
                "vc-001": {
                    "wsi_score": {"overall": 30},
                    "interview_notes": [],
                    "lia_parecer": {},
                    "job": {},
                },
                "vc-002": {
                    "wsi_score": {"overall": 90},
                    "interview_notes": [],
                    "lia_parecer": {},
                    "job": {"has_hired_candidate": True},
                },
            }
            MockAgg.return_value = mock_aggregator
            
            results = await service.predict_substatus_bulk_from_db(
                vacancy_candidate_ids=["vc-001", "vc-002"],
                from_stage="interview_technical",
                to_stage="rejected",
                db=MagicMock(),
            )
            
            assert len(results) == 2
            assert results[0]["vacancy_candidate_id"] == "vc-001"
            assert results[1]["vacancy_candidate_id"] == "vc-002"
            assert results[1]["predicted_substatus"] == "another_candidate_selected"
            mock_aggregator.aggregate_bulk.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_predict_bulk_from_db_no_session(self):
        """Test bulk prediction without DB session uses fallback."""
        from app.domains.automation.services.stage_transition_automation import StageTransitionAutomationService
        
        service = StageTransitionAutomationService()
        results = await service.predict_substatus_bulk_from_db(
            vacancy_candidate_ids=["vc-001", "vc-002"],
            from_stage="screening",
            to_stage="rejected",
            db=None,
        )
        
        assert len(results) == 2
        for r in results:
            assert "predicted_substatus" in r
            assert "vacancy_candidate_id" in r
    
    @pytest.mark.asyncio
    async def test_predict_from_db_aggregator_error_graceful(self):
        """Test that aggregator errors propagate correctly."""
        from app.domains.automation.services.stage_transition_automation import StageTransitionAutomationService
        
        service = StageTransitionAutomationService()
        
        with patch('app.domains.automation.services.candidate_context_aggregator.CandidateContextAggregator') as MockAgg:
            mock_aggregator = AsyncMock()
            mock_aggregator.aggregate.side_effect = Exception("DB connection lost")
            MockAgg.return_value = mock_aggregator
            
            with pytest.raises(Exception, match="DB connection lost"):
                await service.predict_substatus_from_db(
                    vacancy_candidate_id="vc-001",
                    from_stage="screening",
                    to_stage="rejected",
                    db=MagicMock(),
                )
