"""Phase 4: Agentic Loop — patch script for main_orchestrator.py and workflow.py"""
import sys
import os

BASE = os.path.expanduser("~/workspace/lia-agent-system")

# ============================================================
# CHANGE 1: main_orchestrator.py — LLM interpretation of action results
# ============================================================

orch_path = os.path.join(BASE, "app/orchestrator/main_orchestrator.py")
with open(orch_path, "r") as f:
    orch = f.read()

# 1a. Replace the "executed" block in _try_action_executor
old_executed = '''        if action_result.status == "executed":
            return ChatResponse.from_action_result(
                action_result,
                intent=action_result.action_type or "action",
                conv_id=conv_id,
                suggested_prompts=_get_suggested_prompts(
                    action_result.action_type or "", len(candidates), 0
                ),
            )

        return None'''

new_executed = '''        if action_result.status == "executed":
            # LIA-A01: LLM interpretation of action results
            # Instead of returning raw action result, ask the LLM to generate a natural response
            try:
                _interpreted = await self._interpret_action_result(ctx, action_result, {})
                if _interpreted:
                    action_result = ActionResult(
                        status=action_result.status,
                        action_type=action_result.action_type,
                        message=_interpreted,
                        data=action_result.data,
                        candidates=action_result.candidates,
                    )
            except Exception as e:
                logger.debug("[LIA-A01] LLM interpretation skipped (fail-open): %s", e)

            return ChatResponse.from_action_result(
                action_result,
                intent=action_result.action_type or "action",
                conv_id=conv_id,
                suggested_prompts=_get_suggested_prompts(
                    action_result.action_type or "", len(candidates), 0
                ),
            )

        return None'''

if old_executed not in orch:
    print("ERROR: Could not find executed block in main_orchestrator.py")
    sys.exit(1)

orch = orch.replace(old_executed, new_executed)
print("OK: Replaced executed block in _try_action_executor")

# 1b. Add _interpret_action_result method after _try_action_executor (before Phase 2 section)
phase2_marker = '''    # ------------------------------------------------------------------
    # Phase 2 — Pipeline consolidado (sem delegação intermediária)
    # ------------------------------------------------------------------'''

interpret_method = '''    # ------------------------------------------------------------------
    # LIA-A01 — LLM interpretation of action results
    # ------------------------------------------------------------------

    async def _interpret_action_result(
        self, ctx: UniversalContext, action_result: ActionResult, orchestrator_context: dict
    ) -> str | None:
        """LIA-A01: Use LLM to generate natural response from action result."""
        import os as _os
        if _os.getenv("LIA_AGENTIC_INTERPRET", "true").lower() not in ("true", "1"):
            return None

        try:
            from app.shared.prompts.system_prompt_builder import SystemPromptBuilder

            # Build a focused interpretation prompt
            system_prompt = SystemPromptBuilder.build(
                agent_type="orchestrator",
                tenant_context=orchestrator_context.get("tenant_context"),
                user_context=orchestrator_context.get("user_context"),
            )

            interpretation_prompt = (
                f"{system_prompt}\\n\\n"
                f"O usuario pediu: {ctx.message}\\n\\n"
                f"A acao '{action_result.action_type}' foi executada com sucesso.\\n"
                f"Resultado: {action_result.message}\\n"
            )

            if action_result.data:
                import json
                try:
                    data_str = json.dumps(action_result.data, ensure_ascii=False, default=str)[:2000]
                    interpretation_prompt += f"Dados retornados: {data_str}\\n"
                except Exception:
                    pass

            interpretation_prompt += (
                "\\nGere uma resposta natural e contextualizada para o usuario. "
                "Seja conciso. Nao repita o que o usuario disse. "
                "Se houver dados, apresente-os de forma organizada."
            )

            # Use the LLM service for interpretation
            from app.domains.ai.services.llm import LLMService
            llm_svc = LLMService()

            response = await llm_svc.generate(
                prompt=interpretation_prompt,
                provider="gemini",  # Use cheapest model for interpretation
                max_tokens=500,
            )

            if response and response.strip():
                return response.strip()
        except Exception as e:
            logger.debug("[LIA-A01] Interpretation failed: %s", e)

        return None

    ''' + phase2_marker

if phase2_marker not in orch:
    print("ERROR: Could not find Phase 2 marker in main_orchestrator.py")
    sys.exit(1)

orch = orch.replace(phase2_marker, interpret_method)
print("OK: Added _interpret_action_result method")

# 1c. CHANGE 3: Add LIA-A03 feature flag comment in process() method
process_marker = '''        Phase 0: PendingAction — se há ação pendente aguardando confirmação/params
        Phase 1: ActionExecutor — ações fechadas detectáveis por padrão
        Phase 2: Orchestrator completo — CascadedRouter → DomainWorkflow → ReAct Agent
        """'''

process_replacement = '''        Phase 0: PendingAction — se há ação pendente aguardando confirmação/params
        Phase 1: ActionExecutor — ações fechadas detectáveis por padrão
        Phase 2: Orchestrator completo — CascadedRouter → DomainWorkflow → ReAct Agent

        LIA-A03: Agentic interpretation is controlled by LIA_AGENTIC_INTERPRET env var.
        Set to "false" to disable LLM interpretation of action results (falls back to raw).
        Default: "true" — LLM interprets all action results for natural responses.
        """'''

if process_marker not in orch:
    print("WARNING: Could not find process() docstring marker for LIA-A03")
else:
    orch = orch.replace(process_marker, process_replacement)
    print("OK: Added LIA-A03 feature flag docs in process()")

with open(orch_path, "w") as f:
    f.write(orch)
print("OK: main_orchestrator.py saved")

# ============================================================
# CHANGE 2: workflow.py — LLM interpretation for domain responses
# ============================================================

wf_path = os.path.join(BASE, "app/domains/workflow.py")
with open(wf_path, "r") as f:
    wf = f.read()

# 2a. Add _interpret_if_technical method to DomainWorkflow class
# Insert it right before _build_error_response
error_response_marker = '''    def _build_error_response(self, state: WorkflowState) -> DomainResponse:'''

interpret_technical_method = '''    # ------------------------------------------------------------------
    # LIA-A02 — LLM interpretation for domain execution results
    # ------------------------------------------------------------------

    async def _interpret_if_technical(self, response_text: str, question: str, context: dict) -> str:
        """LIA-A02: Interpret technical/template responses into natural language."""
        # Skip if response is already natural (> 200 chars, has multiple sentences)
        if len(response_text) > 200 or response_text.count('.') > 2:
            return response_text

        # Skip known natural patterns
        _technical_patterns = [
            "encaminhada", "executada", "realizada", "cancelada",
            "Acao ", "Operacao ", "Lista ", "Resultado:",
        ]
        is_technical = any(p in response_text for p in _technical_patterns)
        if not is_technical:
            return response_text

        import os as _os
        if _os.getenv("LIA_AGENTIC_INTERPRET", "true").lower() not in ("true", "1"):
            return response_text

        try:
            from app.domains.ai.services.llm import LLMService
            llm_svc = LLMService()

            prompt = (
                f"O usuario perguntou: {question}\\n"
                f"O sistema respondeu: {response_text}\\n\\n"
                f"Reescreva essa resposta de forma natural, amigavel e informativa. "
                f"Mantenha o conteudo. Seja conciso."
            )

            result = await llm_svc.generate(prompt=prompt, provider="gemini", max_tokens=300)
            return result.strip() if result else response_text
        except Exception:
            return response_text

    ''' + error_response_marker

if error_response_marker not in wf:
    print("ERROR: Could not find _build_error_response marker in workflow.py")
    sys.exit(1)

wf = wf.replace(error_response_marker, interpret_technical_method)
print("OK: Added _interpret_if_technical method to DomainWorkflow")

# 2b. Wire _interpret_if_technical after _format step in process()
# Insert after state = await self._format(state) and before post-process compliance
format_call = '''            state = await self._format(state)

            # LIA-C02: Post-process compliance (FactCheck via ComplianceDomainPrompt)'''

format_call_with_interpret = '''            state = await self._format(state)

            # LIA-A02: LLM interpretation for domain execution results
            # If the formatted response looks like a raw template, interpret it
            if state.formatted_response and state.formatted_response.message:
                try:
                    _interpreted_msg = await self._interpret_if_technical(
                        state.formatted_response.message,
                        query,
                        {},
                    )
                    if _interpreted_msg != state.formatted_response.message:
                        state.formatted_response.message = _interpreted_msg
                        state.log_step("agentic_interpret", {"status": "rewritten"})
                except Exception as _interp_exc:
                    logger.debug("[LIA-A02] Interpretation skipped (fail-open): %s", _interp_exc)

            # LIA-C02: Post-process compliance (FactCheck via ComplianceDomainPrompt)'''

if format_call not in wf:
    print("ERROR: Could not find _format call marker in workflow.py")
    sys.exit(1)

wf = wf.replace(format_call, format_call_with_interpret)
print("OK: Wired _interpret_if_technical in process() pipeline")

with open(wf_path, "w") as f:
    f.write(wf)
print("OK: workflow.py saved")

print("\n=== All patches applied successfully ===")
