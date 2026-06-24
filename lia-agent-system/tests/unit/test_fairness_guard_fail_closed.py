"""
Mutation gap: FairnessGuard fail-closed para "boa aparência" (Task #364).

"boa aparência" foi promovida de Layer-2 (aviso implícito) para Layer-1 (hard block)
em DISCRIMINATORY_CATEGORIES["aparencia_fisica"]. Nenhum teste existente exercita
este path diretamente — mutant que removesse o padrão passaria sem detecção.

Cobertura:
- check("boa aparência") → is_blocked=True, category="aparencia_fisica"
- check("boa aparencia") → idem sem acento (regex [eê])
- _COMPILED_PATTERNS não está vazio — guard estrutural anti-fail-open
"""
import pytest

from app.shared.compliance.fairness_guard import FairnessGuard, FairnessCheckResult


@pytest.fixture(scope="module")
def guard() -> FairnessGuard:
    return FairnessGuard()


class TestFairnessGuardFailClosed:
    def test_blocks_boa_aparencia_com_acento(self, guard):
        """
        Regra Task #364: "boa aparência" é Layer-1 hard block, não aviso implícito.
        Falha indica fail-open: candidatos discriminados por aparência passariam.
        """
        result = guard.check("candidatos com boa aparência")

        assert isinstance(result, FairnessCheckResult)
        assert result.is_blocked, (
            "FairnessGuard FAIL-OPEN: 'boa aparência' não foi bloqueada. "
            "Verifique DISCRIMINATORY_CATEGORIES['aparencia_fisica'] → pattern "
            r"r'\bboa\s+apar[eê]ncia\b'."
        )
        assert result.category == "aparencia_fisica", (
            f"Category esperada 'aparencia_fisica', got {result.category!r}"
        )
        assert result.confidence >= 0.7
        assert result.educational_message is not None
        assert len(result.blocked_terms) > 0

    def test_blocks_boa_aparencia_sem_acento(self, guard):
        """Variante sem acento: regex [eê] deve casar 'aparencia' também."""
        result = guard.check("boa aparencia obrigatória para a função")

        assert result.is_blocked, "'boa aparencia' (sem acento) deve ser BLOCK Layer-1"
        assert result.category == "aparencia_fisica"

    def test_blocks_boa_aparencia_em_contexto_de_vaga(self, guard):
        """Frase em contexto realista de JD discriminatória."""
        result = guard.check("Requisito: boa aparência e boa apresentação pessoal")

        assert result.is_blocked
        assert result.category == "aparencia_fisica"
        assert result.is_biased  # alias de is_blocked

    def test_allows_criterio_objetivo_de_apresentacao(self, guard):
        """Não deve bloquear critérios objetivos de dress code sem citar aparência."""
        result = guard.check("uso de uniforme e crachá de identificação obrigatórios")

        assert not result.is_blocked, (
            "Critério objetivo de apresentação (uniforme/crachá) não deve ser bloqueado"
        )

    def test_compiled_patterns_not_empty(self):
        """
        Guard estrutural anti-fail-open: se _COMPILED_PATTERNS estiver vazio,
        NENHUMA frase discriminatória seria detectada.
        """
        from app.shared.compliance import fairness_guard as fg_module

        assert len(fg_module._COMPILED_PATTERNS) > 0, (
            "FAIL-OPEN: _COMPILED_PATTERNS está vazio — _ensure_compiled() não rodou "
            "ou DISCRIMINATORY_CATEGORIES está vazio. FairnessGuard cego."
        )
        assert "aparencia_fisica" in fg_module._COMPILED_PATTERNS, (
            "Categoria 'aparencia_fisica' ausente de _COMPILED_PATTERNS — "
            "padrão 'boa aparência' (Task #364) não seria detectado."
        )
        assert len(fg_module._COMPILED_PATTERNS["aparencia_fisica"]) > 0

    def test_original_query_preserved_in_blocked_result(self, guard):
        """Metadata: original_query deve ser preservada para auditoria LGPD."""
        phrase = "Exigimos boa aparência dos candidatos"
        result = guard.check(phrase)

        assert result.original_query == phrase
        assert result.is_blocked
