"""Coverage tests for teams_card_renderer.py — TeamsCardRenderer pure methods."""
import pytest
from app.domains.communication.services.teams_card_renderer import TeamsCardRenderer


@pytest.fixture
def renderer():
    return TeamsCardRenderer()


class TestScoreBar:
    def test_zero_returns_empty(self, renderer):
        assert renderer._score_bar(0) == ""

    def test_none_returns_empty(self, renderer):
        assert renderer._score_bar(None) == ""

    def test_100_returns_full_bar(self, renderer):
        result = renderer._score_bar(100)
        assert "█" in result  # filled block

    def test_50_returns_half_bar(self, renderer):
        result = renderer._score_bar(50)
        assert "█" in result and "░" in result

    def test_length_always_10(self, renderer):
        for score in [10, 50, 80, 100]:
            result = renderer._score_bar(score)
            total = result.count("█") + result.count("░")
            assert total == 10


class TestActionLabel:
    def test_known_action(self, renderer):
        assert renderer._action_label("search_candidates") == "Buscar candidatos"

    def test_unknown_action_titlecased(self, renderer):
        result = renderer._action_label("custom_action_xyz")
        assert "Custom" in result or "custom" in result.lower()

    def test_compare_candidates(self, renderer):
        assert "ompar" in renderer._action_label("compare_candidates")

    def test_schedule_interview(self, renderer):
        assert "ntrevista" in renderer._action_label("schedule_interview")


class TestRenderTextCard:
    def test_message_included(self, renderer):
        result = renderer.render({"message": "Olá mundo"})
        assert result is not None
        assert result.get("type") == "AdaptiveCard"

    def test_returns_none_on_empty(self, renderer):
        result = renderer.render({})
        assert result is None

    def test_with_suggested_prompts(self, renderer):
        result = renderer.render({
            "message": "Resultado aqui",
            "suggested_prompts": ["Mais detalhes", "Ver candidatos"]
        })
        assert result is not None

    def test_with_next_actions(self, renderer):
        result = renderer.render({
            "message": "Resultado",
            "next_actions": ["Buscar candidatos"]
        })
        assert result is not None


class TestRenderCandidatesCard:
    def test_candidates_in_structured_data(self, renderer):
        result = renderer.render({
            "structured_data": {
                "candidates": [
                    {"name": "Ana Silva", "score": 85}
                ]
            },
            "message": "Encontrei candidatos"
        })
        assert result is not None

    def test_candidates_in_data_key(self, renderer):
        result = renderer.render({
            "data": {
                "candidates": [
                    {"name": "Bruno Costa", "score": 70}
                ]
            }
        })
        assert result is not None


class TestRenderPlanCard:
    def test_execution_plan_triggers_plan_card(self, renderer):
        result = renderer.render({
            "execution_plan": {
                "steps": [
                    {"action": "search_candidates", "description": "Buscar"}
                ]
            },
            "message": "Plano criado"
        })
        assert result is not None
        assert result.get("type") == "AdaptiveCard"


class TestRenderCvScreeningCard:
    def test_cv_screening_agent_type(self, renderer):
        result = renderer.render({
            "agent_type": "cv_screening",
            "message": "Triagem concluída",
            "candidate_name": "Pedro Lima"
        })
        assert result is not None

    def test_candidate_id_triggers_cv_card(self, renderer):
        result = renderer.render({
            "candidate_id": "cand_123",
            "message": "Resultado"
        })
        assert result is not None


class TestRenderConfirmationCard:
    def test_requires_user_input(self, renderer):
        result = renderer.render({
            "requires_user_input": True,
            "message": "Confirmar ação?"
        })
        assert result is not None

    def test_needs_confirmation(self, renderer):
        result = renderer.render({
            "needs_confirmation": True,
            "message": "Você confirma?"
        })
        assert result is not None


class TestRenderNotificationCard:
    def test_basic_notification(self, renderer):
        result = renderer.render_notification_card(
            title="Teste",
            body_text="Mensagem de teste"
        )
        assert result.get("type") == "AdaptiveCard"
        assert result.get("version") == "1.4"

    def test_with_actions(self, renderer):
        actions = [{"type": "Action.Submit", "title": "OK", "data": {}}]
        result = renderer.render_notification_card(
            title="Titulo",
            body_text="Corpo",
            actions=actions
        )
        assert "actions" in result

    def test_without_actions_no_actions_key(self, renderer):
        result = renderer.render_notification_card(
            title="Titulo",
            body_text="Corpo"
        )
        assert "actions" not in result


class TestRenderNewCandidateCard:
    def test_basic_candidate_card(self, renderer):
        result = renderer.render_new_candidate_card(
            candidate_name="Ana Lima",
            job_title="Desenvolvedor",
            candidate_id="cand_1",
            vacancy_id="vac_1"
        )
        assert result.get("type") == "AdaptiveCard"
        assert "actions" in result

    def test_with_score(self, renderer):
        result = renderer.render_new_candidate_card(
            candidate_name="Carlos",
            job_title="Designer",
            candidate_id="cand_2",
            vacancy_id="vac_2",
            estimated_score=85.0
        )
        assert result is not None


class TestRenderStalledPipelineCard:
    def test_stalled_card_created(self, renderer):
        result = renderer.render_stalled_pipeline_card(
            vacancy_title="Backend Engineer",
            candidates_count=5,
            days_stalled=7,
            vacancy_id="vac_3"
        )
        assert result.get("type") == "AdaptiveCard"
        assert "actions" in result


class TestRenderDeadlineCard:
    def test_deadline_urgent(self, renderer):
        result = renderer.render_deadline_card(
            vacancy_title="Sales Manager",
            days_remaining=2,
            candidates_in_pipeline=3,
            vacancy_id="vac_4"
        )
        assert result is not None

    def test_deadline_warning(self, renderer):
        result = renderer.render_deadline_card(
            vacancy_title="Engineer",
            days_remaining=5,
            candidates_in_pipeline=8,
            vacancy_id="vac_5"
        )
        assert result is not None


class TestRenderContextGreetingCard:
    def test_home_page(self, renderer):
        result = renderer.render_context_greeting_card(page="home")
        assert result is not None
        assert result.get("type") == "AdaptiveCard"

    def test_vaga_page(self, renderer):
        result = renderer.render_context_greeting_card(page="vaga")
        assert result is not None

    def test_candidato_page(self, renderer):
        result = renderer.render_context_greeting_card(page="candidato")
        assert result is not None

    def test_unknown_page_fallback(self, renderer):
        result = renderer.render_context_greeting_card(page="unknown_page")
        assert result is not None


class TestExtractCandidates:
    def test_from_structured_data(self, renderer):
        result = {"structured_data": {"candidates": [{"name": "Ana"}]}}
        candidates = renderer._extract_candidates(result)
        assert len(candidates) == 1

    def test_from_data_key(self, renderer):
        result = {"data": {"candidates": [{"name": "Bruno"}, {"name": "Carlos"}]}}
        candidates = renderer._extract_candidates(result)
        assert len(candidates) == 2

    def test_empty_returns_empty_list(self, renderer):
        assert renderer._extract_candidates({}) == []

    def test_from_top_level_candidates(self, renderer):
        result = {"candidates": [{"name": "Diana"}]}
        candidates = renderer._extract_candidates(result)
        assert len(candidates) >= 1
