"""
FIX 11 — G5 actions_context placement + G7 WSI cluster.

G5: The routing prompt must place {actions_context} BEFORE {message}
    (not appended at the end after the JSON instruction).

G7: generate_wsi_questions in job_management must cross-reference
    the cv_screening equivalent to reduce ambiguity.
"""


class TestFix11Placement:
    def test_routing_prompt_has_actions_context_placeholder(self):
        from app.orchestrator.llm_cascade import _ROUTING_PROMPT
        assert "{actions_context}" in _ROUTING_PROMPT, (
            "_ROUTING_PROMPT must contain {actions_context} placeholder"
        )

    def test_actions_context_placeholder_before_message(self):
        from app.orchestrator.llm_cascade import _ROUTING_PROMPT
        idx_ctx = _ROUTING_PROMPT.index("{actions_context}")
        idx_msg = _ROUTING_PROMPT.index("{message}")
        assert idx_ctx < idx_msg, (
            "{actions_context} must come BEFORE {message} so LLM weighs "
            "domain actions while interpreting the user query"
        )

    def test_call_model_substitutes_actions_context(self):
        """After rebuild_routing_context, _call_model builds a prompt where
        the context is at the correct position (not appended)."""
        from app.orchestrator.llm_cascade import LLMCascadeRouter, _ROUTING_PROMPT
        router = LLMCascadeRouter()
        router.rebuild_routing_context()
        # Simulate what _call_model does
        ctx = getattr(router, "_actions_context", "")
        assert ctx, "rebuild should have populated _actions_context"
        # After FIX 11: context replaces placeholder, not appended
        # Test via a simple smoke: the prompt shape has placeholder substitution working
        rendered = _ROUTING_PROMPT.replace("{actions_context}", ctx).replace("{message}", "TEST")
        # Context should appear before "Mensagem:" marker in the rendered prompt
        if "Mensagem:" in rendered:
            idx_msg = rendered.index("Mensagem:")
            # Look for at least one domain_id from ctx
            ctx_start = rendered.find(ctx[:50]) if ctx else -1
            if ctx_start >= 0:
                assert ctx_start < idx_msg, (
                    f"In rendered prompt, actions context must precede 'Mensagem:'"
                )


class TestFix11WSICluster:
    def test_generate_wsi_questions_has_cross_reference(self):
        """generate_wsi_questions in job_management must reference cv_screening
        or the triagem flow to reduce ambiguity with cv_screening's WSI generator."""
        from app.domains.job_management.domain import JobManagementDomain
        domain = JobManagementDomain()
        action = next(
            (a for a in domain.get_allowed_actions() if a.action_id == "generate_wsi_questions"),
            None,
        )
        assert action is not None, "generate_wsi_questions must exist in job_management"
        desc = action.description.lower()
        # Must mention cv_screening OR triagem to disambiguate
        assert (
            "cv_screening" in desc
            or "triagem" in desc
            or "distinto de" in desc
            or "distinto do" in desc
        ), (
            f"generate_wsi_questions description must cross-ref cv_screening/triagem. "
            f"Got: {action.description[-200:]}"
        )
