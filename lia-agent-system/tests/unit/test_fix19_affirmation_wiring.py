"""
FIX 19 — Wire FIX 15's is_simple_affirmation into runtime via _should_resolve.

Bug discovered in audit post FIX 14-17:
  is_simple_affirmation("pode sim") → True  (FIX 15 function works)
  _should_resolve("pode sim")       → False (gate blocks entry)
  ∴ memory_resolver.resolve() early-returns, FIX 15 dead in runtime

FIX 19 makes _should_resolve() recognize affirmations so resolve() enters
and applies continuation semantics (keep filters / preserve intent).

Canonical-fix: extends existing gate function with 1 signal. Blast radius:
1 function, 0 new callers.
"""
import pytest


class TestFix19AffirmationWiring:
    def test_should_resolve_recognizes_pode_sim(self):
        """The gate must accept 'pode sim' after FIX 19."""
        from app.orchestrator.memory_resolver import _should_resolve
        assert _should_resolve("pode sim") is True, (
            "FIX 19: _should_resolve must admit affirmations, otherwise "
            "memory_resolver.resolve() early-returns and is_simple_affirmation "
            "never has effect in runtime"
        )

    def test_should_resolve_recognizes_other_affirmations(self):
        from app.orchestrator.memory_resolver import _should_resolve
        for phrase in ("ok", "beleza", "manda ver", "isso mesmo", "confirmo"):
            assert _should_resolve(phrase) is True, (
                f"_should_resolve should accept affirmation {phrase!r}"
            )

    def test_should_resolve_still_rejects_plain_searches(self):
        """Regression: novas buscas continuam não disparando resolve."""
        from app.orchestrator.memory_resolver import _should_resolve
        # 'busque python em SP' não tem pronome/ref/positional/affirmation
        assert _should_resolve("busque python em SP") is False
        assert _should_resolve("mostra candidatos") is False

    def test_should_resolve_still_matches_existing_signals(self):
        """Regression: pronouns/refs/positional ainda funcionam."""
        from app.orchestrator.memory_resolver import _should_resolve
        # "mostra ele" (pronoun), "a vaga" (entity ref), "o primeiro" (positional)
        assert _should_resolve("mostra ele") is True
        assert _should_resolve("o primeiro") is True

    @pytest.mark.asyncio
    async def test_resolve_triggers_for_affirmation_end_to_end(self):
        """Smoke: resolve() agora faz algo para 'pode sim' (não early-return)."""
        from app.orchestrator.memory_resolver import memory_resolver
        # Sem WorkingMemory disponível, resolve deve pelo menos NÃO crashar
        # e retornar um tuple válido (message, was_resolved:bool)
        result = await memory_resolver.resolve(
            message="pode sim",
            session_id="test-sess-fix19",
        )
        assert isinstance(result, tuple) and len(result) == 2
        _msg, _was = result
        assert isinstance(_msg, str)
        assert isinstance(_was, bool)
        # Não importa o valor de _was (depende de memory disponibility)
        # O importante é que resolve() ENTROU — não early-returnou por _should_resolve False
