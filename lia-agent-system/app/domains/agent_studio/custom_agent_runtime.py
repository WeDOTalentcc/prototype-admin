import contextvars
import functools
import logging
import time
from typing import Any, Optional

from lia_agents_core.agent_interface import AgentInput, AgentOutput, AgentAction
from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
from lia_agents_core.langgraph_react_base import LangGraphReActBase

logger = logging.getLogger(__name__)

# ADR-029 §3 / Audit H 2026-05-06: use canonical ContextVar from auth_enforcement
# instead of a sibling ContextVar. Previously this module defined its own
# `_CURRENT_COMPANY_ID` which bypassed the R-008 setter lockdown and the
# Sprint 1B `tool_handler` decorator's ContextVar resolution path.
# The local alias name is kept for backward compat in this file's call sites.
from app.middleware.auth_enforcement import _current_company_id as _CURRENT_COMPANY_ID  # noqa: F401

PLATFORM_TOOLS_REGISTRY: dict[str, str] = {
    "search_candidates": "read",
    "list_jobs": "read",
    "get_job_details": "read",
    "get_candidate_details": "read",
    "get_pipeline_summary": "read",
    "search_talent_pool": "read",
    "get_analytics_summary": "read",
    "get_company_culture": "read",
    "get_evaluation_criteria": "read",
    "summarize_context": "read",
    "clarify_request": "read",
    "move_candidate": "write",
    "send_email": "write",
    "update_candidate_field": "write",
    "schedule_interview": "write",
    "create_note": "write",
}


def get_available_tool_names() -> list[str]:
    return list(PLATFORM_TOOLS_REGISTRY.keys())


class CustomAgentRuntime(LangGraphReActBase, EnhancedAgentMixin):

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        system_prompt: str,
        allowed_tools: list[str],
        domain: str = "custom",
        max_steps: int = 8,
        temperature: float = 0.7,
        model_override: Optional[str] = None,
        company_id: str = "",
        enable_memory: bool = True,
        excluded_tools: list[str] | None = None,
        context_level: str = "full",
    ) -> None:
        super().__init__()
        self._agent_id = agent_id
        self._agent_name = agent_name
        self._system_prompt_template = system_prompt
        self._allowed_tools = allowed_tools
        self._domain = domain
        self._max_steps = max_steps
        self._temperature = temperature
        self._model_override = model_override
        self._company_id = company_id
        self._enable_memory = enable_memory
        self._excluded_tools = set(excluded_tools or [])
        self._context_level = context_level if context_level in ("full", "standard", "minimal") else "full"
        self._setup_enhanced(domain=f"custom:{agent_name}")
        logger.info(
            "[CustomAgentRuntime] Initialized agent=%s tools=%d max_steps=%d",
            agent_name,
            len(allowed_tools),
            max_steps,
        )

    @property
    def domain_name(self) -> str:
        return f"custom:{self._agent_name}"

    async def process(self, input) -> "AgentOutput":
        """Implement abstract method from AgentInterface — delegates to execute()."""
        return await self.execute(
            message=input.message,
            user_id=input.user_id,
            company_id=input.company_id,
            session_id=input.session_id,
            context=input.context,
        )

    @property
    def available_tools(self) -> list[str]:
        return list(self._allowed_tools)

    # Tools NOT available to Studio agents (admin/destructive operations)
    _RESTRICTED_TOOLS = frozenset({
        "delete_candidate", "delete_job", "delete_company",
        "bulk_delete", "reset_pipeline", "drop_tenant",
        "modify_permissions", "change_plan", "admin_override",
        # Etapa 2: batch/destructive operations blocked from Studio
        "bulk_sync_candidates", "finalize_hiring",
        "batch_move", "batch_move_candidates",
        # Etapa 3: additional dangerous tools (OWASP LLM06 audit)
        "reject_autonomous_action", "calibrate_sourcing_agent",
        "advance_campaign_stage", "move_pool_to_job",
    })

    def _get_tools(self) -> list:
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool

        # GAP 5: Load tools from autonomous pool + domain-specific registries
        all_tools = []

        # Pool 1: Autonomous tools (40 curated cross-domain tools)
        try:
            from app.domains.autonomous.agents.autonomous_tool_registry import get_autonomous_tools  # DEPRECATED-IMPORT-EXEMPT: Pool 1 cross-domain canonical (46 tools curadas) — Studio agents usam autonomous como baseline cross-domain + Pool 2 domain-specific (sem equivalente em agent_studio)
            all_tools.extend(get_autonomous_tools())
        except Exception:
            pass

        # Pool 2: Domain-specific tools based on agent domain
        domain = self._domain.split(":")[0] if ":" in self._domain else self._domain
        domain_tool_loaders = {
            "sourcing": "app.domains.sourcing.agents.sourcing_tool_registry.get_sourcing_tools",
            "pipeline": "app.domains.pipeline.agents.pipeline_tool_registry.get_pipeline_tools",
            "screening": "app.domains.cv_screening.agents.pipeline_tool_registry.get_pipeline_tools",
            "communication": "app.domains.communication.agents.communication_tool_registry.get_communication_tools",
            "analytics": "app.domains.analytics.agents.analytics_tool_registry.get_analytics_tools",
            "job_management": "app.domains.job_management.agents.wizard_tool_registry.get_wizard_tools",
            "automation": "app.domains.automation.agents.automation_tool_registry.get_automation_tools",
        }
        loader_path = domain_tool_loaders.get(domain)
        if loader_path:
            try:
                module_path, func_name = loader_path.rsplit(".", 1)
                import importlib
                mod = importlib.import_module(module_path)
                domain_tools = getattr(mod, func_name)()
                all_tools.extend(domain_tools)
            except Exception as _e:
                logger.debug("[CustomAgentRuntime] Domain tools load failed for %s: %s", domain, _e)

        enhanced_tools = self._get_all_enhanced_tools()
        # Deduplicate by name, filter out restricted
        all_available = {}
        for td in all_tools + enhanced_tools:
            if td.name not in self._RESTRICTED_TOOLS and td.name not in self._excluded_tools:
                all_available[td.name] = td

        filtered = []
        # If allowed_tools is empty, allow ALL available tools (minus restricted/excluded)
        tool_names_to_use = self._allowed_tools if self._allowed_tools else list(all_available.keys())
        for tool_name in tool_names_to_use:
            if tool_name in all_available:
                td = all_available[tool_name]
                original_fn = td.function
                _is_write = PLATFORM_TOOLS_REGISTRY.get(tool_name, "read") == "write"

                @functools.wraps(original_fn)
                async def _tenant_safe_wrapper(
                    *args: Any,
                    _fn=original_fn,
                    _write=_is_write,
                    **kwargs: Any,
                ) -> Any:
                    request_company_id = _CURRENT_COMPANY_ID.get("")
                    if request_company_id:
                        kwargs["company_id"] = request_company_id
                    else:
                        kwargs.pop("company_id", None)

                    if _write and not kwargs.get("confirm"):
                        return {
                            "success": False,
                            "message": "Operação de escrita bloqueada: confirm=True necessário.",
                        }
                    _tool_result = await _fn(*args, **kwargs)

                    # === 2.3: FairnessGuard on tool output (bias detection) ===
                    try:
                        from app.shared.compliance.fairness_guard import FairnessGuard
                        _fg_out = FairnessGuard()
                        _out_text = str(_tool_result) if not isinstance(_tool_result, str) else _tool_result
                        if len(_out_text) > 20:
                            _fg_check = _fg_out.check(_out_text)
                            if _fg_check.is_blocked:
                                logger.warning(
                                    "[Studio] FairnessGuard flagged tool output: tool=%s",
                                    _fn.__name__,
                                )
                    except Exception:
                        pass

                    return _tool_result

                try:
                    wrapped_td = td.model_copy(update={"function": _tenant_safe_wrapper})
                except AttributeError:
                    wrapped_td = td
                filtered.append(wrapped_td)

        return [tool_definition_to_langchain_tool(td) for td in filtered]

    async def _run_graph(
        self,
        initial_state: dict,
        session_id: str,
        audit_callback: Any = None,
        streaming_callback: Any = None,
    ) -> dict:
        compiled = self._get_compiled_graph()
        if compiled is None:
            raise RuntimeError(f"[CustomAgentRuntime:{self._agent_name}] Grafo LangGraph não disponível")

        # GAP 4+8: Thread_id based on enable_memory setting
        if self._enable_memory:
            effective_thread = session_id or f"{self._agent_id}:{initial_state.get('user_id', 'anon')}:{self._company_id}"
        else:
            import uuid as _uuid
            effective_thread = f"stateless:{self._agent_id}:{_uuid.uuid4().hex[:8]}"
        config: dict[str, Any] = {
            "configurable": {"thread_id": effective_thread},
            "recursion_limit": self._max_steps * 2 + 1,
        }
        # === 2.4 + 2.5: Auto-inject PII strip + Audit callbacks ===
        try:
            from app.shared.llm.callbacks import AuditLogCallback, PIIStripCallback
            auto_callbacks = [
                PIIStripCallback(),
                AuditLogCallback(
                    tenant_id=self._company_id,
                    caller=f"studio:{self._agent_name}",
                ),
            ]
        except Exception:
            auto_callbacks = []
        callbacks = auto_callbacks + [
            cb for cb in [audit_callback, streaming_callback] if cb is not None
        ]
        if callbacks:
            config["callbacks"] = callbacks

        return await compiled.ainvoke(initial_state, config=config)

    def _get_system_prompt(self, input: AgentInput) -> str:
        """Compose system prompt respecting context_level:

        - full: persona + domain + tenant + user + history + few-shot + intelligence_floor + custom (default)
        - standard: persona + tenant + user + intelligence_floor + custom (no history, no few-shot)
        - minimal: persona + intelligence_floor + custom instructions only

        Intelligence floor (item 12.6) is ALWAYS injected to guarantee minimum
        quality regardless of client prompt configuration.
        """
        from app.shared.prompts.system_prompt_builder import SystemPromptBuilder

        ctx = input.context or {}

        # Load intelligence floor (item 12.6 — quality floor for custom agents)
        intelligence_floor = self._load_intelligence_floor()

        # Map domain to agent_type for SystemPromptBuilder
        agent_type = self._domain if self._domain != "custom" else "general"
        if ":" in agent_type:
            agent_type = agent_type.split(":")[0]
        domain_map = {
            "sourcing": "sourcing",
            "screening": "cv_screening",
            "pipeline": "pipeline",
            "analytics": "analytics",
            "communication": "communication",
            "job_management": "job_planner",
            "general": "recruiter_assistant",
            "custom": "recruiter_assistant",
        }
        builder_agent_type = domain_map.get(agent_type, "recruiter_assistant")

        # === context_level routing ===
        if self._context_level == "minimal":
            base = SystemPromptBuilder.build(
                agent_type=builder_agent_type,
                extra_instructions=(
                    f"{intelligence_floor}\n\n"
                    f"INSTRUCOES ADICIONAIS DO OPERADOR:\n{self._system_prompt_template}"
                ),
            )
            return base

        if self._context_level == "standard":
            base = SystemPromptBuilder.build(
                agent_type=builder_agent_type,
                tenant_context_snippet=ctx.get("tenant_context_snippet", ""),
                user_name=ctx.get("user_name", ""),
                user_role=ctx.get("user_role", ""),
                context_page=ctx.get("context_page", "general"),
                extra_instructions=(
                    f"{intelligence_floor}\n\n"
                    f"INSTRUCOES ADICIONAIS DO OPERADOR:\n{self._system_prompt_template}"
                ),
            )
            return base

        # Full: everything (default)
        base = SystemPromptBuilder.build(
            agent_type=builder_agent_type,
            tenant_context_snippet=ctx.get("tenant_context_snippet", ""),
            user_name=ctx.get("user_name", ""),
            user_role=ctx.get("user_role", ""),
            recruiter_context=ctx.get("recruiter_context", ""),
            conversation_summary=ctx.get("conversation_summary", ""),
            conversation_history=ctx.get("conversation_history"),
            context_page=ctx.get("context_page", "general"),
            extra_instructions=(
                f"{intelligence_floor}\n\n"
                f"INSTRUCOES ADICIONAIS DO OPERADOR:\n{self._system_prompt_template}"
            ),
        )

        # Inject domain-specific few-shot examples + reasoning
        domain_instructions = self._load_domain_instructions()
        if domain_instructions:
            return f"{base}\n\n---\n\n{domain_instructions}"
        return base

    @staticmethod
    def _load_intelligence_floor() -> str:
        """Load intelligence floor YAML (item 12.6 — quality floor for custom agents)."""
        try:
            from pathlib import Path
            import yaml
            floor_path = Path(__file__).resolve().parent.parent.parent / "config" / "agent_studio" / "intelligence_floor.yaml"
            if floor_path.exists():
                with open(floor_path) as f:
                    data = yaml.safe_load(f)
                return data.get("floor_instructions", "")
        except Exception as exc:
            logger.debug("[CustomAgentRuntime] Intelligence floor load failed: %s", exc)
        return ""

    def _load_domain_instructions(self) -> str:
        """Load DOMAIN_INSTRUCTIONS for the agent's domain (same as product agents)."""
        domain = self._domain.split(":")[0] if ":" in self._domain else self._domain
        _domain_loaders = {
            "sourcing": lambda: self._safe_import("app.domains.sourcing.agents.sourcing_system_prompt", "SOURCING_DOMAIN_SPECIFIC"),
            "screening": lambda: self._safe_import("app.domains.cv_screening.agents.pipeline_system_prompt", "PIPELINE_DOMAIN_SPECIFIC"),
            "pipeline": lambda: self._safe_import("app.domains.cv_screening.agents.pipeline_system_prompt", "PIPELINE_DOMAIN_SPECIFIC"),
            "analytics": lambda: self._safe_import("app.domains.analytics.agents.analytics_system_prompt", "ANALYTICS_DOMAIN_SPECIFIC"),
            "communication": lambda: self._safe_import("app.domains.communication.agents.communication_system_prompt", "COMMUNICATION_DOMAIN_SPECIFIC"),
            "job_management": lambda: self._safe_import("app.domains.job_management.agents.wizard_system_prompt", "WIZARD_DOMAIN_SPECIFIC"),
            "automation": lambda: self._safe_import("app.domains.automation.agents.automation_system_prompt", "AUTOMATION_DOMAIN_SPECIFIC"),
        }
        loader = _domain_loaders.get(domain)
        return loader() if loader else ""

    @staticmethod
    def _safe_import(module_path: str, attr_name: str) -> str:
        """Safely import a domain-specific constant."""
        try:
            import importlib
            mod = importlib.import_module(module_path)
            return getattr(mod, attr_name, "")
        except Exception:
            return ""

    def _state_to_output(self, state: dict, input: AgentInput) -> AgentOutput:
        messages = state.get("messages", [])
        response = ""

        for m in reversed(messages):
            content = getattr(m, "content", None) or (
                m.get("content", "") if isinstance(m, dict) else ""
            )
            if content and not getattr(m, "tool_call_id", None) and not (
                isinstance(m, dict) and m.get("tool_call_id")
            ):
                response = self._extract_text_content(content)
                break

        if not response:
            response = "Não consegui processar sua solicitação. Por favor, tente reformular."

        actions = []
        for m in messages:
            for tc in (getattr(m, "tool_calls", None) or []):
                name = tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
                actions.append(AgentAction(action_type="call_tool", params={"tool": name}))

        return AgentOutput(
            message=response,
            actions=actions,
            confidence=0.8,
            metadata={
                "source": "custom_agent_runtime",
                "agent_id": self._agent_id,
                "agent_name": self._agent_name,
                "domain": self._domain,
                "tool_calls": len(actions),
            },
        )

    async def execute(
        self,
        message: str,
        user_id: str = "system",
        company_id: str = "",
        session_id: str = "",
        context: Optional[dict[str, Any]] = None,
    ) -> AgentOutput:
        effective_company_id = company_id or self._company_id
        _token = _CURRENT_COMPANY_ID.set(effective_company_id)

        # === 2.1: SecurityPatterns — block SQL injection, XSS, path traversal ===
        try:
            from app.shared.robustness.security_patterns import check_input_security
            _sec = check_input_security(message)
            if _sec.is_blocked:
                logger.warning(
                    "[Studio:%s] SecurityPatterns blocked input: threats=%s",
                    self._agent_name, _sec.threat_categories,
                )
                return AgentOutput(
                    message="Solicitação bloqueada: padrão de segurança detectado.",
                    confidence=1.0,
                    metadata={
                        "blocked": True,
                        "reason": "security_patterns",
                        "threats": _sec.threat_categories,
                    },
                )
        except Exception:
            pass

        # === 2.2: PromptInjectionGuard — block jailbreak attempts ===
        try:
            from app.shared.prompt_injection import PromptInjectionGuard
            _pig = PromptInjectionGuard()
            _pig_result = _pig.check(message)
            if _pig_result.is_blocked:
                logger.warning(
                    "[Studio:%s] PromptInjection blocked: patterns=%s",
                    self._agent_name, _pig_result.matched_patterns,
                )
                return AgentOutput(
                    message="Solicitação bloqueada: possível tentativa de injeção detectada.",
                    confidence=1.0,
                    metadata={
                        "blocked": True,
                        "reason": "prompt_injection",
                        "patterns": _pig_result.matched_patterns,
                    },
                )
        except Exception:
            pass

        # === Existing FairnessGuard ===
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard
            _fg = FairnessGuard()
            _fg_result = _fg.check(message)
            if _fg_result.is_blocked:
                return AgentOutput(
                    message=_fg_result.educational_message or "Solicitação bloqueada por critérios de equidade.",
                    confidence=1.0,
                    metadata={"blocked": True, "reason": "fairness_guard"},
                )
        except Exception:
            pass

        try:
            agent_input = AgentInput(
                message=message,
                user_id=user_id,
                company_id=effective_company_id,
                session_id=session_id,
                context=context or {},
            )
            output = await self._process_langgraph(agent_input)
            return output
        except Exception as exc:
            _is_recursion = "recursion" in str(exc).lower()
            if _is_recursion:
                return AgentOutput(
                    message="O agente atingiu o limite máximo de passos. Tente reformular.",
                    confidence=0.0,
                    metadata={"budget_exhausted": True},
                )
            logger.error("[CustomAgentRuntime:%s] Error: %s", self._agent_name, exc, exc_info=True)
            return AgentOutput(
                message="Ocorreu um erro ao processar sua solicitação.",
                confidence=0.0,
                metadata={"error": str(exc)},
            )
        finally:
            _CURRENT_COMPANY_ID.reset(_token)


_runtime_cache: dict[str, CustomAgentRuntime] = {}


def get_or_create_runtime(
    agent_id: str,
    agent_name: str,
    system_prompt: str,
    allowed_tools: list[str],
    domain: str = "custom",
    max_steps: int = 8,
    temperature: float = 0.7,
    model_override: Optional[str] = None,
    company_id: str = "",
    force_new: bool = False,
    enable_memory: bool = True,
    excluded_tools: list[str] | None = None,
    context_level: str = "full",
) -> CustomAgentRuntime:
    cache_key = f"{agent_id}:{company_id}"
    if cache_key not in _runtime_cache or force_new:
        _runtime_cache[cache_key] = CustomAgentRuntime(
            agent_id=agent_id,
            agent_name=agent_name,
            system_prompt=system_prompt,
            allowed_tools=allowed_tools,
            domain=domain,
            max_steps=max_steps,
            temperature=temperature,
            model_override=model_override,
            enable_memory=enable_memory,
            excluded_tools=excluded_tools,
            context_level=context_level,
            company_id=company_id,
        )
    return _runtime_cache[cache_key]
