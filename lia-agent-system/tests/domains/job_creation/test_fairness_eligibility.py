"""
Fase 7 Lote 2 — Testes fairness para perguntas de elegibilidade.

Sites cobertos:
  Site 1: wizard_orchestrator.process_turn — fail-open → fail-loud (exception do guard)
  Site 2+3: _check_question_fairness helper — wired em create_custom + apply template

Convenção xfail:
  strict=True em lacunas documentadas do guard. Quando o guard for corrigido,
  o teste vira XPASS → CI sinaliza que o xfail deve ser removido.

Run:
  python3 -m pytest tests/domains/job_creation/test_fairness_eligibility.py \\
      -v --tb=short --no-cov
"""
import pytest
from unittest.mock import patch, MagicMock


# ─── Fixtures compartilhadas ─────────────────────────────────────────────────

@pytest.fixture()
def fairness_check():
    """Importa o helper após o patch ser aplicado."""
    from app.domains.job_creation.orchestrator.wizard_service_tools import (
        _check_question_fairness,
    )
    return _check_question_fairness


# ─── Bloco 1: helper _check_question_fairness — categorias bloqueadas ─────────

class TestCheckQuestionFairnessBlocked:
    """Guard bloqueia texto discriminatório → helper retorna ToolResult(error=True)."""

    def test_genero_bloqueado(self, fairness_check):
        result = fairness_check("Precisa ser do sexo feminino")
        assert result is not None, "genero discriminatório deve ser bloqueado"
        assert result.error is True
        assert "genero" in result.llm_message.lower() or "discriminatório" in result.llm_message

    def test_deficiencia_bloqueada(self, fairness_check):
        result = fairness_check("Precisamos de candidatos sem deficiência física")
        assert result is not None, "deficiencia discriminatória deve ser bloqueada"
        assert result.error is True

    def test_religiao_bloqueada(self, fairness_check):
        result = fairness_check("Candidatos de religião cristã preferencial")
        assert result is not None, "religiao discriminatória deve ser bloqueada"
        assert result.error is True

    def test_raca_etnia_bloqueada(self, fairness_check):
        result = fairness_check("Candidatos brancos com perfil europeu")
        assert result is not None, "raca_etnia discriminatória deve ser bloqueada"
        assert result.error is True

    def test_maternidade_bloqueada(self, fairness_check):
        result = fairness_check("Candidatos solteiros sem filhos")
        assert result is not None, "maternidade/estado_civil deve ser bloqueado"
        assert result.error is True


# ─── Bloco 2: helper — categorias benignas passam ─────────────────────────────

class TestCheckQuestionFairnessBenign:
    """Textos técnicos/operacionais passam (guard retorna None)."""

    def test_cnh_passa(self, fairness_check):
        assert fairness_check("Você possui CNH categoria B ou superior?") is None

    def test_presencial_passa(self, fairness_check):
        assert fairness_check("Disponibilidade para trabalho presencial em São Paulo?") is None

    def test_idioma_passa(self, fairness_check):
        assert fairness_check("Inglês avançado ou fluente é requisito da vaga?") is None

    def test_experiencia_tecnica_passa(self, fairness_check):
        assert fairness_check("Você tem experiência com Python e APIs REST?") is None


# ─── Bloco 3: lacunas documentadas do guard (RED xfail, strict=True) ─────────
#
# strict=True: se o guard for corrigido e o teste passar → XPASS → CI
# sinaliza para remover o xfail. Isso documenta o gap sem esconder o verde.

class TestCheckQuestionFairnessGuardGaps:
    """
    Lacunas de calibração do guard: categorias discriminatórias que o
    FairnessGuard NÃO detecta ainda com as frases testadas.

    Estes testes são documentação viva — falham como esperado (xfail)
    até que fairness_guard.py receba termos adicionais.
    """

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "guard gap: categoria 'idade' não detecta 'Ter menos de 30 anos de idade' — "
            "fix pending: adicionar termos em fairness_guard.py DISCRIMINATORY_CATEGORIES['idade']"
        ),
    )
    def test_guard_catches_idade_gap(self, fairness_check):
        """RED: guard não pega forma 'menos de X anos'. Fix = adicionar termos ao guard."""
        result = fairness_check("Ter menos de 30 anos de idade")
        assert result is not None  # xfail aqui: result é None → assertion falha como esperado

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "guard gap: categoria 'nacionalidade' não detecta 'brasileiros natos somente' — "
            "fix pending: adicionar termos em fairness_guard.py DISCRIMINATORY_CATEGORIES['nacionalidade']"
        ),
    )
    def test_guard_catches_nacionalidade_gap(self, fairness_check):
        """RED: guard não pega forma 'natos'. Fix = adicionar termos ao guard."""
        result = fairness_check("Candidatos brasileiros natos somente")
        assert result is not None

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "guard gap: categoria 'antecedentes_criminais' não detecta 'sem ficha criminal' — "
            "fix pending: adicionar termos em fairness_guard.py DISCRIMINATORY_CATEGORIES['antecedentes_criminais']"
        ),
    )
    def test_guard_catches_antecedentes_gap(self, fairness_check):
        """RED: guard não pega forma 'ficha criminal'. Fix = adicionar termos ao guard."""
        result = fairness_check("Sem ficha criminal, apenas pessoas idôneas")
        assert result is not None


# ─── Bloco 4: fail-closed no helper (guard exception → ToolResult(error=True)) ─

class TestCheckQuestionFairnessFailClosed:
    """Se o guard lançar exceção → fail-closed: helper retorna ToolResult(error=True)."""

    def test_guard_exception_retorna_tool_result_error(self, fairness_check):
        """
        Mocka FairnessGuard para levantar RuntimeError.
        Espera: helper não propaga a exceção nem retorna None.
        Retorna: ToolResult com error=True e mensagem de indisponibilidade.

        Patch no módulo canonical (não no local import): quando a função faz
        'from app.shared.compliance.fairness_guard import FairnessGuard',
        Python busca o atributo no módulo já cacheado em sys.modules. O patch
        no atributo do módulo intercepta esse lookup.
        """
        with patch(
            "app.shared.compliance.fairness_guard.FairnessGuard",
            side_effect=RuntimeError("guard crashed in test"),
        ):
            result = fairness_check("Qualquer texto que normalmente passaria")

        assert result is not None, (
            "fail-closed: guard exception deve retornar ToolResult, nunca None. "
            "None aqui significaria que a exceção foi silenciada e o texto passou."
        )
        assert result.error is True
        assert "indisponível" in result.llm_message or "compliance" in result.llm_message.lower(), (
            f"Mensagem de indisponibilidade esperada, got: {result.llm_message!r}"
        )


# ─── Bloco 5: Site 1 — wizard_orchestrator fail-loud ─────────────────────────

class TestOrchestratorFairnessFailLoud:
    """
    Testa que exception no FairnessGuard dentro de process_turn:
      - NÃO continua silenciosamente (fail-open antigo)
      - Retorna OrchestratorResult(error=True) com reply de diagnóstico
      - NÃO seta fairness_blocked=True (distinguível de detecção real)

    process_turn é sync — chamável diretamente sem asyncio.
    FairnessGuard é importado localmente na função (local import pattern);
    patch no módulo canonical interceta o lookup.
    """

    def _minimal_orchestrator(self):
        """Instância mínima de WizardOrchestrator sem __init__ completo."""
        from app.domains.job_creation.orchestrator.wizard_orchestrator import WizardOrchestrator
        return WizardOrchestrator.__new__(WizardOrchestrator)

    def test_guard_exception_retorna_error_result(self):
        """
        Guard exception → OrchestratorResult(error=True, reply=diagnóstico).
        O turn para antes de chamar o LLM (process_turn retorna na linha do except).
        """
        from app.domains.job_creation.orchestrator.wizard_orchestrator import OrchestratorResult
        orch = self._minimal_orchestrator()
        ctx = MagicMock()
        ctx.company_id = "co-test-123"

        with patch(
            "app.shared.compliance.fairness_guard.FairnessGuard",
            side_effect=RuntimeError("guard crashed"),
        ):
            # process_turn é sync, chamável direto
            result = orch.process_turn(
                state={},
                user_message="Candidatos do sexo feminino apenas",
                ctx=ctx,
            )

        assert isinstance(result, OrchestratorResult)
        assert result.error is True, (
            "fail-loud: OrchestratorResult.error deve ser True quando guard falha"
        )
        assert not result.fairness_blocked, (
            "fairness_blocked=False distingue 'guard caiu' de 'discriminação detectada'"
        )
        assert "indisponível" in result.reply or "compliance" in result.reply.lower(), (
            f"Reply deve indicar indisponibilidade de compliance, got: {result.reply!r}"
        )

    def test_guard_detection_sets_fairness_blocked(self):
        """
        Detecção real → OrchestratorResult(fairness_blocked=True).
        Não seta error=True (distinguível de crash do guard).
        """
        from app.shared.compliance.fairness_guard import FairnessCheckResult
        from app.domains.job_creation.orchestrator.wizard_orchestrator import OrchestratorResult
        orch = self._minimal_orchestrator()
        ctx = MagicMock()
        ctx.company_id = "co-test-123"

        blocked = FairnessCheckResult(
            is_blocked=True,
            blocked_terms=["sexo feminino"],
            category="genero",
            educational_message="Critério de gênero é discriminatório.",
            confidence=1.0,
            soft_warnings=[],
        )

        with patch(
            "app.shared.compliance.fairness_guard.FairnessGuard"
        ) as MockGuard:
            MockGuard.return_value.check.return_value = blocked
            result = orch.process_turn(
                state={},
                user_message="Precisa ser do sexo feminino",
                ctx=ctx,
            )

        assert isinstance(result, OrchestratorResult)
        assert result.fairness_blocked is True
        assert result.error is False, (
            "error=False quando é detecção real (não crash do guard)"
        )
        assert "discriminatório" in result.reply.lower() or "gênero" in result.reply.lower() \
            or "critério" in result.reply.lower(), (
            f"Reply deve conter mensagem educacional, got: {result.reply!r}"
        )
