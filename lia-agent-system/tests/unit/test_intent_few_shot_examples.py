"""
Testes para intent few-shot examples — Sprint J2.

Verifica que os exemplos:
- Cobrem exatamente 10 claros + 10 ambíguos
- Cobrem todos os domínios obrigatórios
- Casos claros têm confiança >= 0.85
- Casos ambíguos têm confiança <= 0.55
- Todos têm campos obrigatórios (message, intent, confidence)
- intent 'clarification_needed' APENAS nos ambíguos
- Mensagens não são vazias e têm contexto mínimo
"""
import pytest


def _get_examples():
    from app.shared.prompts.intent_few_shot_examples import (
        CLEAR_EXAMPLES, AMBIGUOUS_EXAMPLES, FEW_SHOT_EXAMPLES,
        REQUIRED_DOMAINS, COVERED_DOMAINS,
    )
    return CLEAR_EXAMPLES, AMBIGUOUS_EXAMPLES, FEW_SHOT_EXAMPLES, REQUIRED_DOMAINS, COVERED_DOMAINS


class TestExampleCounts:

    def test_total_20_examples(self):
        _, _, all_ex, _, _ = _get_examples()
        assert len(all_ex) == 20

    def test_exactly_10_clear(self):
        clear, _, _, _, _ = _get_examples()
        assert len(clear) == 10

    def test_exactly_10_ambiguous(self):
        _, ambig, _, _, _ = _get_examples()
        assert len(ambig) == 10


class TestClearExamples:

    def test_clear_confidence_above_085(self):
        clear, _, _, _, _ = _get_examples()
        for ex in clear:
            assert ex.confidence >= 0.85, (
                f"Exemplo claro com confiança baixa: '{ex.message}' = {ex.confidence}"
            )

    def test_clear_examples_have_domain(self):
        clear, _, _, _, _ = _get_examples()
        for ex in clear:
            assert ex.domain is not None, f"Exemplo claro sem domain: '{ex.message}'"

    def test_clear_intent_not_clarification(self):
        clear, _, _, _, _ = _get_examples()
        for ex in clear:
            assert ex.intent != "clarification_needed", (
                f"Exemplo claro não deve ter intent=clarification_needed: '{ex.message}'"
            )


class TestAmbiguousExamples:

    def test_ambiguous_confidence_below_055(self):
        _, ambig, _, _, _ = _get_examples()
        for ex in ambig:
            assert ex.confidence <= 0.55, (
                f"Exemplo ambíguo com confiança alta: '{ex.message}' = {ex.confidence}"
            )

    def test_ambiguous_intent_is_clarification(self):
        _, ambig, _, _, _ = _get_examples()
        for ex in ambig:
            assert ex.intent == "clarification_needed", (
                f"Exemplo ambíguo deve ter intent=clarification_needed: '{ex.message}'"
            )


class TestDomainCoverage:

    def test_all_required_domains_covered(self):
        _, _, _, required, covered = _get_examples()
        missing = required - covered
        assert not missing, f"Domínios não cobertos pelos exemplos: {missing}"

    def test_covered_domains_include_job_management(self):
        _, _, _, _, covered = _get_examples()
        assert "job_management" in covered

    def test_covered_domains_include_cv_screening(self):
        _, _, _, _, covered = _get_examples()
        assert "cv_screening" in covered

    def test_covered_domains_include_sourcing(self):
        _, _, _, _, covered = _get_examples()
        assert "sourcing" in covered

    def test_covered_domains_include_pipeline(self):
        _, _, _, _, covered = _get_examples()
        assert "pipeline" in covered

    def test_covered_domains_include_communication(self):
        _, _, _, _, covered = _get_examples()
        assert "communication" in covered

    def test_covered_domains_include_policy(self):
        _, _, _, _, covered = _get_examples()
        assert "policy" in covered


class TestExampleStructure:

    def test_all_have_message(self):
        _, _, all_ex, _, _ = _get_examples()
        for ex in all_ex:
            assert ex.message and len(ex.message) > 5, f"Mensagem inválida: '{ex.message}'"

    def test_all_have_confidence(self):
        _, _, all_ex, _, _ = _get_examples()
        for ex in all_ex:
            assert 0.0 <= ex.confidence <= 1.0, (
                f"Confiança fora do range [0,1]: {ex.confidence}"
            )

    def test_all_have_intent(self):
        _, _, all_ex, _, _ = _get_examples()
        for ex in all_ex:
            assert ex.intent and len(ex.intent) > 0

    def test_no_duplicate_messages(self):
        _, _, all_ex, _, _ = _get_examples()
        messages = [ex.message for ex in all_ex]
        assert len(messages) == len(set(messages)), "Exemplos com mensagens duplicadas"
