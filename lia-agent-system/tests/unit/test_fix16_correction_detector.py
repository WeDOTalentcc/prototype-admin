"""
FIX 16 — Correction detector.

Bug observed in chat audit (screenshot 3):
  Turn 5: user says "estamos falando de buscar candidatos e nao perfil cultura"
  LIA response: "Nenhum candidato encontrado para 'e nao perfil cultura'"

User was CORRECTING LIA (turn 4 jumped to cultural profile, user clarifies
they are talking about candidate search). But keyword matcher saw "candidatos"
+ "buscar" and routed to search_candidates with the full phrase as raw_query.

FIX: deterministic regex detector that identifies user corrections BEFORE
cascade router runs. If correction detected, short-circuit with a
clarification response instead of executing a garbage query.

Canonical structure: mirrors meta_question_detector.py (Task #726).
"""
import pytest


class TestFix16CorrectionDetector:
    def test_module_exists(self):
        from app.orchestrator.correction_detector import detect_user_correction
        assert callable(detect_user_correction)

    def test_screenshot_3_exact_phrase_detected(self):
        """The exact phrase from the audit screenshot must be detected."""
        from app.orchestrator.correction_detector import detect_user_correction
        result = detect_user_correction(
            "estamos falando de buscar candidatos e nao perfil cultura"
        )
        assert result is not None
        assert result.is_correction is True

    def test_nao_quis_dizer_detected(self):
        from app.orchestrator.correction_detector import detect_user_correction
        result = detect_user_correction("não, quis dizer outra coisa")
        assert result is not None

    def test_na_verdade_detected(self):
        from app.orchestrator.correction_detector import detect_user_correction
        result = detect_user_correction("na verdade eu queria ver vagas abertas")
        assert result is not None

    def test_nao_e_isso_detected(self):
        from app.orchestrator.correction_detector import detect_user_correction
        result = detect_user_correction("não é isso que eu pedi")
        assert result is not None

    def test_normal_search_not_detected(self):
        """Regression: buscas normais não devem ser classificadas como correção."""
        from app.orchestrator.correction_detector import detect_user_correction
        for phrase in (
            "busque candidatos React em SP",
            "quero ver vagas abertas",
            "mostra candidatos python senior",
            "cria uma nova vaga",
        ):
            assert detect_user_correction(phrase) is None, (
                f"'{phrase}' é busca normal, não correção"
            )

    def test_affirmation_not_detected(self):
        """Regression: affirmations (FIX 15) não são correções."""
        from app.orchestrator.correction_detector import detect_user_correction
        for phrase in ("pode sim", "ok", "beleza", "manda ver"):
            assert detect_user_correction(phrase) is None

    def test_capability_question_not_detected(self):
        """Regression: capability questions (FIX Task #726) não são correções."""
        from app.orchestrator.correction_detector import detect_user_correction
        for phrase in (
            "consegue buscar candidatos?",
            "você sabe agendar entrevistas?",
        ):
            assert detect_user_correction(phrase) is None

    def test_result_has_reply_message(self):
        """Correction result deve incluir mensagem de clarification."""
        from app.orchestrator.correction_detector import detect_user_correction
        result = detect_user_correction("não, quis dizer outra coisa")
        assert result is not None
        assert hasattr(result, "reply")
        assert result.reply  # não vazio
        assert isinstance(result.reply, str)

    def test_fail_open_on_empty(self):
        """Mensagem vazia retorna None, não explode."""
        from app.orchestrator.correction_detector import detect_user_correction
        assert detect_user_correction("") is None
        assert detect_user_correction(None) is None


class TestFix16OrchestratorIntegration:
    def test_main_orchestrator_imports_correction_detector(self):
        """main_orchestrator.py deve invocar correction_detector ANTES de meta_question."""
        from pathlib import Path
        import app.orchestrator.main_orchestrator as mo
        src = Path(mo.__file__).read_text()
        assert "detect_user_correction" in src, (
            "main_orchestrator must import detect_user_correction"
        )
        # Correção detector deve ser chamado ANTES de meta_question_detector
        idx_corr = src.find("detect_user_correction")
        idx_meta = src.find("detect_meta_capability_question")
        assert idx_corr > 0 and idx_meta > 0
        assert idx_corr < idx_meta, (
            "correction_detector deve ser chamado ANTES de meta_question_detector — "
            "correções têm prioridade sobre perguntas de capability"
        )
