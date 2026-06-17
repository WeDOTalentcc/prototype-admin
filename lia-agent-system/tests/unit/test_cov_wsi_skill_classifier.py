"""Coverage tests for wsi_skill_classifier.py — heuristic path (llm=None)."""
import pytest

from app.domains.job_creation.services.wsi_skill_classifier import (
    DEFAULT_FALLBACK_SKILL,
    WsiSkillClassifier,
)


@pytest.fixture
def clf():
    return WsiSkillClassifier(llm=None)


class TestHeuristicFallback:
    def test_prazo_keyword_maps_delivery(self, clf):
        assert clf._heuristic_fallback("como voce lida com prazo apertado?") == "delivery_under_deadline_pressure"

    def test_deadline_keyword(self, clf):
        assert clf._heuristic_fallback("deadline urgente") == "delivery_under_deadline_pressure"

    def test_priorizar_keyword(self, clf):
        assert clf._heuristic_fallback("como priorizar tarefas") == "prioritization_with_competing_demands"

    def test_feedback_keyword(self, clf):
        assert clf._heuristic_fallback("lidar com feedback") == "feedback_acceptance"

    def test_conflito_keyword(self, clf):
        assert clf._heuristic_fallback("conflito com colega") == "conflict_resolution"

    def test_dado_keyword(self, clf):
        assert clf._heuristic_fallback("tomar decisao com dado e metrica") == "data_driven_decision_making"

    def test_cliente_keyword(self, clf):
        assert clf._heuristic_fallback("gerenciar stakeholder") == "stakeholder_management"

    def test_ambig_keyword(self, clf):
        assert clf._heuristic_fallback("situacao de ambig e incerteza") == "ambiguity_tolerance"

    def test_causa_raiz_keyword(self, clf):
        assert clf._heuristic_fallback("investigar causa raiz") == "root_cause_analysis"

    def test_equipe_keyword(self, clf):
        assert clf._heuristic_fallback("alinhar com equipe e time") == "cross_team_alignment"

    def test_no_match_returns_default(self, clf):
        result = clf._heuristic_fallback("completamente irrelevante xyz")
        assert result == DEFAULT_FALLBACK_SKILL

    def test_case_insensitive(self, clf):
        r1 = clf._heuristic_fallback("PRAZO urgente")
        r2 = clf._heuristic_fallback("prazo urgente")
        assert r1 == r2


class TestNormalizeLlmResponse:
    def test_valid_skill_id_direct(self, clf):
        from app.domains.job_creation.services.wsi_skill_taxonomy import all_skill_ids
        sid = all_skill_ids()[0]
        assert clf._normalize_llm_response(sid) == sid

    def test_skill_with_double_quotes(self, clf):
        from app.domains.job_creation.services.wsi_skill_taxonomy import all_skill_ids
        sid = all_skill_ids()[0]
        quoted = '"' + sid + '"'
        assert clf._normalize_llm_response(quoted) == sid

    def test_skill_with_backticks(self, clf):
        from app.domains.job_creation.services.wsi_skill_taxonomy import all_skill_ids
        sid = all_skill_ids()[0]
        ticked = '`' + sid + '`'
        assert clf._normalize_llm_response(ticked) == sid

    def test_skill_embedded_in_text(self, clf):
        from app.domains.job_creation.services.wsi_skill_taxonomy import all_skill_ids
        sid = all_skill_ids()[0]
        text = "The answer is " + sid + " done"
        assert clf._normalize_llm_response(text) == sid

    def test_invalid_returns_none(self, clf):
        assert clf._normalize_llm_response("not_a_real_skill_xyz") is None

    def test_empty_returns_none(self, clf):
        assert clf._normalize_llm_response("   ") is None


class TestClassify:
    def test_empty_returns_default(self, clf):
        r = clf.classify("")
        assert r["skill_id"] == DEFAULT_FALLBACK_SKILL
        assert r["source"] == "default"

    def test_whitespace_returns_default(self, clf):
        r = clf.classify("   ")
        assert r["skill_id"] == DEFAULT_FALLBACK_SKILL
        assert r["source"] == "default"

    def test_prazo_question(self, clf):
        r = clf.classify("Como voce lida com prazo apertado?")
        assert r["skill_id"] == "delivery_under_deadline_pressure"
        assert r["source"] == "heuristic"

    def test_unknown_returns_default(self, clf):
        r = clf.classify("xzyzqp blbkldk nada relevante")
        assert r["skill_id"] == DEFAULT_FALLBACK_SKILL
        assert r["source"] == "heuristic"

    def test_result_has_required_keys(self, clf):
        r = clf.classify("qualquer pergunta")
        assert "skill_id" in r
        assert "source" in r

    def test_llm_failure_falls_back_to_heuristic(self):
        from unittest.mock import MagicMock
        mock = MagicMock()
        mock.invoke.side_effect = RuntimeError("LLM down")
        c = WsiSkillClassifier(llm=mock)
        r = c.classify("Como voce lida com prazo?")
        assert r["source"] == "heuristic"

    def test_llm_bad_response_falls_back(self):
        from unittest.mock import MagicMock
        mock_llm = MagicMock()
        resp = MagicMock()
        resp.content = "not_a_valid_skill_at_all"
        mock_llm.invoke.return_value = resp
        c = WsiSkillClassifier(llm=mock_llm)
        r = c.classify("qualquer pergunta")
        assert r["source"] == "heuristic"

    def test_llm_valid_response_uses_llm_source(self):
        from unittest.mock import MagicMock
        from app.domains.job_creation.services.wsi_skill_taxonomy import all_skill_ids
        sid = all_skill_ids()[0]
        mock_llm = MagicMock()
        resp = MagicMock()
        resp.content = sid
        mock_llm.invoke.return_value = resp
        c = WsiSkillClassifier(llm=mock_llm)
        r = c.classify("Alguma pergunta de entrevista")
        assert r["skill_id"] == sid
        assert r["source"] == "llm"
