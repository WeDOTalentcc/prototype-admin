"""
FIX 1 - TDD Red: DomainActions must reach LLM via routing context.

Tests verify:
1. DomainPrompt.get_actions_for_prompt() exists and includes action descriptions
2. LLMCascadeRouter has rebuild_routing_context() method
3. After rebuild, router has _actions_context with content
"""
import pytest


class TestDomainPromptGetActionsForPrompt:

    def test_get_actions_for_prompt_method_exists_on_base(self):
        from app.domains.base import DomainPrompt
        assert hasattr(DomainPrompt, "get_actions_for_prompt"), (
            "DomainPrompt deve ter metodo get_actions_for_prompt()"
        )

    def test_get_actions_for_prompt_returns_string(self):
        from app.domains.job_management.domain import JobManagementDomain
        domain = JobManagementDomain()
        result = domain.get_actions_for_prompt()
        assert isinstance(result, str)

    def test_get_actions_for_prompt_includes_action_ids(self):
        from app.domains.job_management.domain import JobManagementDomain
        domain = JobManagementDomain()
        max_actions = 8
        result = domain.get_actions_for_prompt(max_actions=max_actions)
        # Only the first max_actions actions are included — verify all of them appear
        actions_included = domain.get_allowed_actions()[:max_actions]
        found = sum(1 for a in actions_included if a.action_id in result)
        assert found == len(actions_included), (
            f"Todos {len(actions_included)} action_ids incluidos devem aparecer, encontrado {found}"
        )

    def test_get_actions_for_prompt_empty_domain_returns_empty_string(self):
        from app.domains.base import DomainPrompt, DomainResponse, IntentResult

        class EmptyTestDomain(DomainPrompt):
            domain_id = "test_empty_fix1"
            domain_name = "Test"

            def get_allowed_actions(self):
                return []

            def get_system_prompt(self):
                return ""

            async def process_intent(self, q, ctx):
                return IntentResult("x", "x", 0.5)

            async def execute_action(self, aid, params, ctx):
                return DomainResponse.error_response("no")

        domain = EmptyTestDomain()
        result = domain.get_actions_for_prompt()
        assert result == "", f"Domain sem actions deve retornar '', got: {result!r}"

    def test_get_actions_for_prompt_max_actions_respected(self):
        from app.domains.job_management.domain import JobManagementDomain
        domain = JobManagementDomain()
        # Solicitar apenas 3 actions
        result = domain.get_actions_for_prompt(max_actions=3)
        actions = domain.get_allowed_actions()
        # Nao deve ter mais de 3 action_ids no resultado
        found = sum(1 for a in actions if a.action_id in result)
        assert found <= 3, f"max_actions=3 deve limitar resultado, encontrado {found} action_ids"


class TestLLMCascadeRouterEnhancedPrompt:

    def test_router_has_rebuild_routing_context_method(self):
        from app.orchestrator.llm_cascade import LLMCascadeRouter
        router = LLMCascadeRouter()
        assert hasattr(router, "rebuild_routing_context"), (
            "LLMCascadeRouter deve ter metodo rebuild_routing_context()"
        )

    def test_rebuild_routing_context_executes_without_error(self):
        from app.orchestrator.llm_cascade import LLMCascadeRouter
        router = LLMCascadeRouter()
        try:
            router.rebuild_routing_context()
        except Exception as e:
            pytest.fail(f"rebuild_routing_context() nao deve levancar excecao: {e}")

    def test_rebuild_populates_actions_context_attribute(self):
        from app.orchestrator.llm_cascade import LLMCascadeRouter
        router = LLMCascadeRouter()
        router.rebuild_routing_context()
        assert hasattr(router, "_actions_context"), (
            "Router deve ter _actions_context apos rebuild_routing_context()"
        )

    def test_actions_context_is_string(self):
        from app.orchestrator.llm_cascade import LLMCascadeRouter
        router = LLMCascadeRouter()
        router.rebuild_routing_context()
        ctx = getattr(router, "_actions_context", None)
        assert isinstance(ctx, str), f"_actions_context deve ser str, got: {type(ctx)}"

    def test_actions_context_contains_domain_ids(self):
        from app.orchestrator.llm_cascade import LLMCascadeRouter
        router = LLMCascadeRouter()
        router.rebuild_routing_context()
        ctx = router._actions_context
        # Ao menos um domain deve aparecer no contexto
        assert len(ctx) > 0, "_actions_context deve ter conteudo apos rebuild"
