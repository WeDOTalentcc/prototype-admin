"""
Testa que publish_node chama save_question_set após gravar screening_config
quando as perguntas foram aprovadas pelo recrutador (HITL #2).

Sem este fix: wizard grava screening_config JSONB mas triagem lê
screening_question_sets (tabela versionada) → regenera do zero, descartando
as 12 perguntas aprovadas + calibração Bloom/Dreyfus/Big Five.
"""
import pytest
from unittest.mock import MagicMock, patch, call


def _make_state(questions_approved=True, mode="full"):
    return {
        "job_id": "job-uuid-001",
        "company_id": "company-uuid-001",
        "screening_mode": mode,
        "wsi_questions": [
            {
                "id": f"q{i}",
                "question": f"Pergunta técnica {i}",
                "block": "technical" if i < 7 else "behavioral",
                "framework": "CBI",
                "competency": "Python",
                "skill": "python",
                "bloom_level": 4,
                "dreyfus_level": 3,
                "trait_ocean": None,
                "weight": 0.8,
                "ideal_answer": "resposta ideal",
                "scoring_rubric": {
                    "score_5": "Excelente",
                    "score_3": "Adequado",
                    "score_1": "Insuficiente",
                },
                "needs_manual_review": False,
                "fallback_used": False,
            }
            for i in range(12)
        ],
        "questions_approved": questions_approved,
        "jd_enriched": {
            "skills_obrigatorias": ["Python"],
            "competencias_comportamentais": [],
            "responsabilidades": [],
        },
        "jd_approved": True,
        "eligibility_questions": [],
        "seniority_resolved": "senior",
        "publish_platforms": ["website"],
        "sourcing_mode": "local",
    }


class TestWizardPublishCreatesQuestionSet:
    def test_publish_calls_save_question_set_when_approved(self):
        """Quando questions_approved=True, publish_node DEVE chamar save_question_set."""
        from app.domains.job_creation.nodes.publish import publish_node

        state = _make_state(questions_approved=True)
        mock_api = MagicMock()
        mock_api.save_screening_config.return_value = MagicMock(success=True, data={"saved": 12})
        mock_api.save_question_set.return_value = MagicMock(success=True, data={"saved": 12})
        mock_api.create_job.return_value = MagicMock(
            success=True,
            data={"data": {"id": "job-uuid-001", "uid": "uid-001", "attributes": {"id": "job-uuid-001", "uid": "uid-001"}}},
        )
        mock_api.publish_job.return_value = MagicMock(success=True, data={"share_link": "http://example.com"})
        mock_api.get_share_link.return_value = MagicMock(success=True, data={"share_link": "http://example.com"})

        with patch(
            "app.domains.job_creation.graph._get_api_client",
            return_value=mock_api,
        ):
            publish_node(state)

        mock_api.save_question_set.assert_called_once()
        call_kwargs = mock_api.save_question_set.call_args
        # primeiro argumento posicional = job_id
        args, kwargs = call_kwargs
        job_id_arg = args[0] if args else kwargs.get("job_id")
        assert job_id_arg == "job-uuid-001"

    def test_publish_includes_metadata_in_question_set(self):
        """save_question_set deve receber questions com bloom_level, dreyfus_level e weight."""
        from app.domains.job_creation.nodes.publish import publish_node

        state = _make_state(questions_approved=True)
        mock_api = MagicMock()
        mock_api.save_screening_config.return_value = MagicMock(success=True, data={"saved": 12})
        mock_api.save_question_set.return_value = MagicMock(success=True, data={"saved": 12})
        mock_api.create_job.return_value = MagicMock(
            success=True,
            data={"data": {"id": "job-uuid-001", "uid": "uid-001", "attributes": {"id": "job-uuid-001", "uid": "uid-001"}}},
        )
        mock_api.publish_job.return_value = MagicMock(success=True, data={"share_link": "http://example.com"})
        mock_api.get_share_link.return_value = MagicMock(success=True, data={"share_link": "http://example.com"})

        with patch(
            "app.domains.job_creation.graph._get_api_client",
            return_value=mock_api,
        ):
            publish_node(state)

        args, kwargs = mock_api.save_question_set.call_args
        # questions pode ser posicional (arg[1]) ou keyword
        questions = args[1] if len(args) > 1 else kwargs.get("questions")
        assert questions is not None, "save_question_set deve receber as questions"
        assert len(questions) == 12
        first_q = questions[0]
        assert "bloom_level" in first_q, "bloom_level deve ser preservado"
        assert "dreyfus_level" in first_q, "dreyfus_level deve ser preservado"
        assert "weight" in first_q, "weight deve ser preservado"

    def test_publish_skips_question_set_when_not_approved(self):
        """Quando questions_approved=False/None, save_question_set NAO deve ser chamado."""
        from app.domains.job_creation.nodes.publish import publish_node

        state = _make_state(questions_approved=False)
        mock_api = MagicMock()
        mock_api.save_screening_config.return_value = MagicMock(success=True, data={"saved": 12})
        mock_api.save_question_set.return_value = MagicMock(success=True, data={"saved": 12})
        mock_api.create_job.return_value = MagicMock(
            success=True,
            data={"data": {"id": "job-uuid-001", "uid": "uid-001", "attributes": {"id": "job-uuid-001", "uid": "uid-001"}}},
        )
        mock_api.publish_job.return_value = MagicMock(success=True, data={"share_link": "http://example.com"})
        mock_api.get_share_link.return_value = MagicMock(success=True, data={"share_link": "http://example.com"})

        with patch(
            "app.domains.job_creation.graph._get_api_client",
            return_value=mock_api,
        ):
            publish_node(state)

        mock_api.save_question_set.assert_not_called()
