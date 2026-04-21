"""
FIX 15 — Affirmation detection in MemoryResolver.

Bug observed in chat audit (screenshot 3):
  Turn 3: user asks "busque candidatos desenvolvedor python com ingles..."
  Turn 4: LIA says "Não consigo filtrar por localização..."
  Turn 5: user says "pode sim" → LIA jumps to cultural profile onboarding

FIX 14 removed the agent_type hijack. But a residual risk remains: if the
cascade router picks the wrong domain for a short affirmation, FIX 14 alone
doesn't help. This fix adds affirmation pattern detection to MemoryResolver
so that "pode sim" / "ok" / "beleza" are flagged as CONTINUATION of the
previous turn, preserving session intent.

Canonical-fix: extends existing _CONTINUITY_PATTERNS / _NEW_SEARCH_PATTERNS
structure in memory_resolver.py. No duplicate logic. Blast: 1 call site.
"""
import pytest


class TestFix15AffirmationDetection:
    def test_is_simple_affirmation_function_exists(self):
        from app.orchestrator.memory_resolver import is_simple_affirmation
        assert callable(is_simple_affirmation)

    def test_pode_sim_is_affirmation(self):
        from app.orchestrator.memory_resolver import is_simple_affirmation
        assert is_simple_affirmation("pode sim") is True

    def test_ok_is_affirmation(self):
        from app.orchestrator.memory_resolver import is_simple_affirmation
        assert is_simple_affirmation("ok") is True
        assert is_simple_affirmation("OK, manda ver") is True

    def test_common_affirmations_are_detected(self):
        from app.orchestrator.memory_resolver import is_simple_affirmation
        for phrase in ("sim", "pode", "beleza", "bora", "vai", "manda ver",
                       "continua", "pode continuar", "isso", "exato"):
            assert is_simple_affirmation(phrase) is True, (
                f"'{phrase}' deveria ser detectada como affirmation"
            )

    def test_search_queries_are_not_affirmations(self):
        from app.orchestrator.memory_resolver import is_simple_affirmation
        # Mensagens que são clearly novas intents, não affirmations
        for phrase in (
            "busque candidatos python",
            "quero ver candidatos",
            "mostra minhas vagas",
            "estamos falando de candidatos e nao perfil cultura",
            "não, quis dizer outra coisa",
        ):
            assert is_simple_affirmation(phrase) is False, (
                f"'{phrase}' NÃO deveria ser affirmation — tem intent concreto"
            )

    def test_affirmation_triggers_should_keep_filters(self):
        """Affirmations devem ser tratadas como continuation."""
        from app.orchestrator.memory_resolver import should_keep_filters
        # should_keep_filters deve retornar True para affirmations
        # (preserva contexto/filtros do turn anterior)
        assert should_keep_filters("pode sim") is True
        assert should_keep_filters("ok continua") is True

    def test_new_search_still_returns_false(self):
        """Regression: mensagens de nova busca continuam False."""
        from app.orchestrator.memory_resolver import should_keep_filters
        assert should_keep_filters("busque python em SP") is False
        assert should_keep_filters("nova busca") is False
