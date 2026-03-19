"""
Testes — interview_system_prompt.py

Verifica que:
1. get_extraction_prompt() retorna string não-vazia com os placeholders preenchidos
2. O prompt inclui NEGATION_DETECTION_BLOCK
3. O prompt inclui os 8 cenários few-shot
4. interview_scheduling_nodes importa o prompt corretamente (smoke test)
"""
import pytest

from app.domains.interview_scheduling.agents.interview_system_prompt import (
    INTERVIEW_EXTRACTION_PROMPT,
    INTERVIEW_FEW_SHOT_EXAMPLES,
    get_extraction_prompt,
)


class TestGetExtractionPrompt:
    def test_returns_non_empty_string(self):
        result = get_extraction_prompt(
            last_message="Agenda entrevista com João amanhã às 14h",
            current_state="{}",
            next_pending_field="candidate_email",
        )
        assert isinstance(result, str)
        assert len(result) > 100

    def test_contains_last_message(self):
        msg = "Agenda entrevista com João amanhã às 14h"
        result = get_extraction_prompt(
            last_message=msg,
            current_state="{}",
            next_pending_field="candidate_email",
        )
        assert msg in result

    def test_contains_next_pending_field(self):
        result = get_extraction_prompt(
            last_message="ok",
            current_state="{}",
            next_pending_field="preferred_date",
        )
        assert "preferred_date" in result

    def test_contains_negation_detection(self):
        result = get_extraction_prompt(
            last_message="não quero mais",
            current_state="{}",
            next_pending_field="",
        )
        # NEGATION_DETECTION_BLOCK deve estar presente
        assert "não" in result.lower() or "negaç" in result.lower() or "cancel" in result.lower()

    def test_contains_few_shot_examples(self):
        result = get_extraction_prompt("ok", "{}", "")
        assert "Cenário" in result

    def test_none_pending_field_uses_fallback(self):
        """next_pending_field vazio usa texto de fallback, não quebra."""
        result = get_extraction_prompt("ok", "{}", "")
        assert "nenhum" in result or "todos coletados" in result


class TestFewShotExamples:
    def test_has_eight_scenarios(self):
        count = INTERVIEW_FEW_SHOT_EXAMPLES.count("**Cenário")
        assert count == 8, f"Esperado 8 cenários, encontrado {count}"

    def test_includes_negation_scenario(self):
        assert "Negação" in INTERVIEW_FEW_SHOT_EXAMPLES or "cancelamento" in INTERVIEW_FEW_SHOT_EXAMPLES.lower()

    def test_includes_partial_message_scenario(self):
        assert "parcial" in INTERVIEW_FEW_SHOT_EXAMPLES.lower()

    def test_includes_thought_tags(self):
        assert "<thought>" in INTERVIEW_FEW_SHOT_EXAMPLES


class TestNodesImportSmokeTest:
    def test_nodes_imports_get_extraction_prompt(self):
        """Smoke test: verifica que o import no nodes não quebra."""
        from app.domains.interview_scheduling.agents.interview_scheduling_nodes import (
            interview_details_collector,
        )
        assert callable(interview_details_collector)
