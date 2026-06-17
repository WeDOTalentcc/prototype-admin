"""
Sensor anti-regressão: o parecer NÃO pode voltar a ter fallback degradado
silencioso (score=50 / "CONSIDERAR" retornado como se fosse avaliação real).

Histórico: `_generate_parecer_sections` capturava qualquer exceção do LLM e
retornava `_generate_fallback_sections` (HTTP 200 com conteúdo genérico),
mascarando a falha — viola CLAUDE.md REGRA 4. Fix: fail-loud via
ParecerGenerationError. Estes testes pinam o contrato.
"""
import importlib
import inspect

# O __init__ do pacote `services` faz `from .candidate_report_service import *`,
# o que importa a INSTÂNCIA singleton `candidate_report_service` para o namespace
# do pacote e sobrescreve o atributo do submódulo. Por isso `import ... as mod`
# resolveria a instância. `importlib.import_module` retorna o MÓDULO real.
mod = importlib.import_module(
    "app.domains.analytics.services.candidate_report_service"
)


def test_fallback_method_removed():
    assert not hasattr(mod.CandidateReportService, "_generate_fallback_sections"), (
        "_generate_fallback_sections voltou — fallback degradado silencioso é proibido (REGRA 4)"
    )


def test_parecer_generation_error_exists():
    assert hasattr(mod, "ParecerGenerationError")
    assert issubclass(mod.ParecerGenerationError, Exception)


def test_source_has_no_degraded_fallback_markers():
    src = inspect.getsource(mod)
    # marcadores do fallback antigo não devem reaparecer
    assert "Avaliação baseada em dados limitados" not in src
    assert '"acao_sugerida": "CONSIDERAR"' not in src


def test_sections_generator_raises_on_llm_failure():
    """O except do gerador de seções deve LEVANTAR, não retornar fallback."""
    src = inspect.getsource(mod.CandidateReportService._generate_parecer_sections)
    assert "raise ParecerGenerationError" in src
    assert "_generate_fallback_sections" not in src
