import contextvars
import functools
import logging
import time
from typing import Any, Literal, Optional

from lia_agents_core.agent_interface import AgentInput, AgentOutput, AgentAction
from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
from lia_agents_core.langgraph_react_base import LangGraphReActBase
from app.shared.agents.tenant_aware_agent import TenantAwareAgentMixin

logger = logging.getLogger(__name__)

# ADR-029 §3 / Audit H 2026-05-06: use canonical ContextVar from auth_enforcement
# instead of a sibling ContextVar. Previously this module defined its own
# `_CURRENT_COMPANY_ID` which bypassed the R-008 setter lockdown and the
# Sprint 1B `tool_handler` decorator's ContextVar resolution path.
# The local alias name is kept for backward compat in this file's call sites.
from app.middleware.auth_enforcement import _current_company_id as _CURRENT_COMPANY_ID  # noqa: F401
from app.shared.observability.tracing import trace_span

# Platform tools registry loaded from config/platform_tools.yaml (single source of truth).
# Migrated from inline Python dict to declarative YAML — see platform_tools_loader.py.
from app.domains.agent_studio.platform_tools_loader import (
    get_platform_tools_registry as _load_registry,
    get_hitl_required_tools as _load_hitl,
    get_domain_tool_loaders as _load_domain_loaders,
    get_available_tool_names,
)

PLATFORM_TOOLS_REGISTRY: dict[str, str] = _load_registry()


HITL_REQUIRED_TOOLS: frozenset[str] = _load_hitl()


# ── P0-2 Onda 0 (2026-06-12): review gate constants ──────────────────────────
# Marketplace-installed agents stay in pending_review until a wedotalent_admin
# explicitly approves them. These constants are the source of truth for the
# review gate in _handle_execute_custom_agent (domain.py) and for contract tests.
REVIEW_STATUS_PENDING: str = "pending_review"
REVIEW_STATUS_ACTIVE: str = "active"


# ── Q4.1 Sandbox dry-run (2026-05-29) ─────────────────────────────────────────
# ContextVars (canonical pattern espelhando _CURRENT_COMPANY_ID em
# auth_enforcement): o runtime e cacheado por agent_id (get_or_create_runtime),
# logo as tool wrappers sao construidas UMA vez no _get_compiled_graph e
# reusadas. Nao da pra fechar o flag dry_run no closure — precisa ser lido
# dinamicamente em cada tool call. ContextVar e fail-closed por request e
# reset em finally de execute() (sem leak entre requests).
#
# Semantica:
#   _DRY_RUN=True  → write tools (PLATFORM_TOOLS_REGISTRY[name]=="write") sao
#                    INTERCEPTADAS: NAO executam side-effect real (sem
#                    WhatsApp/email/move), retornam mock success e registram
#                    "WOULD execute: <tool>(<args>)" em _DRY_RUN_WOULD_DO.
#                    Read tools rodam normal (o recruiter quer ver o raciocinio
#                    real sobre dados reais). LLM/BYOK roda de verdade.
#   _DRY_RUN_WOULD_DO → lista por-request das acoes que o agente FARIA. Lida em
#                    _state_to_output e exposta em AgentOutput.metadata pro
#                    frontend renderizar "Enviaria WhatsApp para X", etc.
_DRY_RUN: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "studio_dry_run", default=False
)
_DRY_RUN_WOULD_DO: contextvars.ContextVar[Optional[list]] = contextvars.ContextVar(
    "studio_dry_run_would_do", default=None
)


def _summarize_tool_args(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Resumo legivel dos args de uma write tool pro painel de simulacao.

    Remove ruido interno (confirm, company_id injetado pelo wrapper) e trunca
    valores longos. NAO faz PII redaction profunda — o consumer (frontend)
    exibe so pro proprio recruiter do tenant; multi-tenancy ja garante escopo.
    """
    out: dict[str, Any] = {}
    for k, v in (kwargs or {}).items():
        if k in ("confirm", "company_id"):
            continue
        if isinstance(v, str) and len(v) > 200:
            out[k] = v[:200] + "…"
        else:
            out[k] = v
    return out


class CustomAgentRuntime(TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin):
    # Gap G (2026-06-08): TenantAwareAgentMixin PRIMEIRO no MRO. execute()
    # chama self._process_langgraph (linha ~829) → o override do mixin
    # pré-resolve o snippet de tenant + aplica strict-mode gate
    # (MissingTenantContextError) e o filtro de snippet degradado
    # ("sua empresa"). Antes, agentes do Studio escapavam desses controles.
    # _get_system_prompt próprio do runtime (sync) ainda vence no MRO e lê
    # ctx['tenant_context_snippet'] que o mixin injeta.

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
        initial_greeting: str | None = None,
        description: str | None = None,
        persona: dict[str, Any] | None = None,
        pricing_tier: str = "pro",
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
        # Sprint 3.6 W4-1 V2: voice plugin config canonical (F-01 pattern).
        # These were ghost attrs accessed by future code paths; making them
        # explicit __init__ params so callers (custom_agents API, tests) can
        # populate per-agent without monkey-patching.
        self._initial_greeting = initial_greeting
        self._description = description
        self._persona = persona or {}
        self._pricing_tier = pricing_tier
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

    # HITL_REQUIRED_TOOLS loaded from config/platform_tools.yaml (module-level)

    def _get_tools(self) -> list:
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool

        # GAP 5: Load tools from domain-specific registries
        all_tools = []

        # Pool 2: Domain-specific tools based on agent domain
        domain = self._domain.split(":")[0] if ":" in self._domain else self._domain
        domain_tool_loaders = _load_domain_loaders()
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

                    # ── Q4.1 Sandbox dry-run interception (2026-05-29) ──
                    # Em modo simulacao, write tools NAO executam side-effect real.
                    # Registramos "WOULD execute" e retornamos mock success pro LLM
                    # continuar o raciocinio. Read tools caem fora deste branch e
                    # rodam normal (dados reais alimentam o raciocinio real).
                    # lia-compliance: garante que nenhuma mensagem/movimentacao
                    # real sai sem o recruiter ter ativado o agente.
                    if _write and _DRY_RUN.get(False):
                        _safe_args = _summarize_tool_args(kwargs)
                        _would = _DRY_RUN_WOULD_DO.get(None)
                        if _would is not None:
                            _would.append({"tool": _fn.__name__, "args": _safe_args})
                        logger.info(
                            "[Studio][DRY-RUN] WOULD execute tool=%s tenant=%s args=%s",
                            _fn.__name__, request_company_id or "unknown", _safe_args,
                        )
                        return {
                            "success": True,
                            "dry_run": True,
                            "message": (
                                f"[SIMULAÇÃO] O agente executaria a ação "
                                f"'{_fn.__name__}' — nenhuma ação real foi realizada."
                            ),
                            "would_execute": {"tool": _fn.__name__, "args": _safe_args},
                        }

                    # ── P0-1 HITL gate for sensitive tools (Onda 0, 2026-06-12) ──────────
                    # HITL_REQUIRED_TOOLS are tools with irreversible/high-impact effects.
                    # They return hitl_pending regardless of confirm flag — the LLM cannot
                    # self-approve these. Only the human via the approval UI can unblock.
                    # This gate runs BEFORE the AUD-4 generic confirm check.
                    if _fn.__name__ in HITL_REQUIRED_TOOLS:
                        logger.info(
                            "[Studio][P0-1] HITL_REQUIRED gate held tool=%s tenant=%s — requer aprovacao humana",
                            _fn.__name__, request_company_id or "unknown",
                        )
                        return {
                            "status": "hitl_pending",
                            "requires_approval": True,
                            "tool": _fn.__name__,
                            "message": (
                                f"A acao '{_fn.__name__}' requer aprovacao humana. "
                                "Use o painel de aprovacao para autorizar ou rejeitar."
                            ),
                            "hitl_gate": "P0-1",
                        }

                    # ── AUD-4 HITL gate (canonical, registrado Wave C2.6 2026-05-27) ──
                    # `confirm=True` em write tools E O gate Human-in-the-Loop canonical
                    # do Agent Studio. LLM custom NAO pode bypass — runtime intercepta
                    # antes da execucao. AUD-4 audit trail logged abaixo.
                    if _write and not kwargs.get("confirm"):
                        logger.info(
                            "[Studio][AUD-4] HITL gate held tool=%s tenant=%s",
                            _fn.__name__, request_company_id or "unknown",
                        )
                        return {
                            "success": False,
                            "message": "Operação de escrita bloqueada: confirm=True necessário.",
                            "hitl_gate": "AUD-4",
                        }
                    if _write:
                        # AUD-4 audit: write tool com confirm=True foi aprovado pelo recruiter
                        logger.info(
                            "[Studio][AUD-4] HITL gate passed tool=%s tenant=%s",
                            _fn.__name__, request_company_id or "unknown",
                        )
                    _tool_result = await _fn(*args, **kwargs)

                    # === 2.3: FairnessGuard on tool output (bias detection) ===
                    # Wave 2 audit 2026-05-21: ANTES log-only, output bias passava direto pro LLM.
                    # AGORA bloqueia o output e retorna sanitized placeholder. LLM recebe sinal
                    # de bias e raciocina sobre alternativa. Audit trail via logger.warning.
                    try:
                        from app.shared.compliance.fairness_guard import FairnessGuard
                        _fg_out = FairnessGuard()
                        _out_text = str(_tool_result) if not isinstance(_tool_result, str) else _tool_result
                        if len(_out_text) > 20:
                            _fg_check = _fg_out.check(_out_text)
                            if _fg_check.is_blocked:
                                logger.warning(
                                    "[Studio] FairnessGuard BLOCKED tool output: tool=%s category=%s",
                                    _fn.__name__, _fg_check.category,
                                )
                                # Sanitize: replace tool_result com mensagem explicativa pro LLM.
                                # LLM vê o bloqueio e ajusta raciocínio em vez de propagar bias.
                                return (
                                    f"[FairnessGuard bloqueou output do tool {_fn.__name__}: "
                                    f"categoria={_fg_check.category or 'bias_detectado'}. "
                                    f"Reformule a consulta sem critérios discriminatórios.]"
                                )
                    except Exception as _fg_exc:
                        logger.warning("[Studio] FairnessGuard check failed: %s", _fg_exc)

                    return _tool_result

                try:
                    wrapped_td = td.model_copy(update={"function": _tenant_safe_wrapper})
                except AttributeError:
                    wrapped_td = td
                filtered.append(wrapped_td)

        return [tool_definition_to_langchain_tool(td) for td in filtered]

    @trace_span("agent_studio.run_graph")
    async def _run_graph(
        self,
        initial_state: dict,
        session_id: str,
        audit_callback: Any = None,
        streaming_callback: Any = None,
        conversation_id: Any = None,
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
                ai_persona=ctx.get("ai_persona"),  # P0-9 E2.3 per-tenant persona
                extra_instructions=(
                    f"{intelligence_floor}\n\n"
                    f"{ctx.get('lia_filtered_prompt', '')}\n\n"  # P0-8 lia_field_toggles canonical
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
                ai_persona=ctx.get("ai_persona"),  # P0-9 E2.3 per-tenant persona
                extra_instructions=(
                    f"{intelligence_floor}\n\n"
                    f"{ctx.get('lia_filtered_prompt', '')}\n\n"  # P0-8 lia_field_toggles canonical
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
            ai_persona=ctx.get("ai_persona"),  # P0-9 E2.3 per-tenant persona
            extra_instructions=(
                f"{intelligence_floor}\n\n"
                f"{ctx.get('lia_filtered_prompt', '')}\n\n"  # P0-8 lia_field_toggles canonical
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

        # Wave D1.3 (2026-05-27): aggregate token usage from langgraph AIMessages.
        # LangChain populates ``usage_metadata`` on each AIMessage when the
        # provider returns it (Anthropic, OpenAI, Gemini via langchain-google-genai).
        # Sum across messages and derive cost via canonical pricing helper.
        tokens_input = 0
        tokens_output = 0
        model_used = ""
        for m in messages:
            usage = getattr(m, "usage_metadata", None) or (
                m.get("usage_metadata") if isinstance(m, dict) else None
            )
            if usage:
                tokens_input += int(usage.get("input_tokens", 0) or 0)
                tokens_output += int(usage.get("output_tokens", 0) or 0)
            if not model_used:
                resp_meta = getattr(m, "response_metadata", None) or (
                    m.get("response_metadata") if isinstance(m, dict) else None
                )
                if resp_meta:
                    model_used = (
                        resp_meta.get("model_name")
                        or resp_meta.get("model")
                        or ""
                    )

        cost_usd = 0.0
        try:
            if tokens_input or tokens_output:
                from libs.audit.lia_audit.audit_callback import _estimate_cost
                cost_usd = _estimate_cost(model_used or None, tokens_input, tokens_output)
        except Exception as _cost_exc:  # REGRA-4-EXEMPT: cost helper, not AI decision path
            logger.warning("[CustomAgentRuntime] cost estimation failed: %s", _cost_exc)
            cost_usd = 0.0

        # Onda 1 B2 (2026-05-27): construir reasoning_trace canonical pra
        # Studio Control Room (DecisionTreeDrawer). Helper extracted pra ser
        # testable em isolamento + manter _state_to_output legivel.
        # reasoning_trace e um artefato de observabilidade best-effort
        # (DecisionTreeDrawer UI), NAO uma decisao/parecer de IA. Fora do escopo
        # do anti-silent-fallback de path critico de decisao IA.
        try:
            from app.domains.agent_studio.reasoning_trace_builder import (
                build_reasoning_trace,
            )
            reasoning_trace = build_reasoning_trace(messages, max_steps=20)
        except Exception as _trace_exc:
            # REGRA-4-EXEMPT (P1-6, 2026-05-29): fail-open LOUD. O except ja loga
            # com exc_info e degrada pra None, que o consumer trata como "sem
            # trace". Nao ha envelope de sucesso falso nem parecer fabricado.
            logger.error(
                "[CustomAgentRuntime] build_reasoning_trace falhou — trace=None",
                exc_info=True,
                extra={"agent_id": self._agent_id, "err": str(_trace_exc)},
            )
            reasoning_trace = None

        # Onda 5+1 (2026-05-29) — extrair candidate_ids tocados pra popular
        # pool_agent_runs.results.candidate_ids[] (endpoint /agent-monitoring/
        # candidate/{id}/touches da Onda 2 B3). Fail-open + LOUD log.
        touched_candidate_ids: list[str] = []
        candidate_ids_truncated = False
        try:
            from app.domains.agent_studio.reasoning_trace_builder import (
                extract_touched_candidate_ids,
            )
            touched_candidate_ids, candidate_ids_truncated = (
                extract_touched_candidate_ids(messages)
            )
        except Exception as _cid_exc:
            logger.error(
                "[CustomAgentRuntime] extract_touched_candidate_ids falhou",
                exc_info=True,
                extra={"agent_id": self._agent_id, "err": str(_cid_exc)},
            )

        # Q4.1 Sandbox: surface dry-run flag + would-do actions pro frontend.
        # ContextVar ainda esta ativo aqui (execute() so reseta no finally, que
        # roda depois de _process_langgraph → _state_to_output retornar).
        _is_dry_run = _DRY_RUN.get(False)
        _would_do = _DRY_RUN_WOULD_DO.get(None) or []

        return AgentOutput(
            message=response,
            actions=actions,
            confidence=0.8,
            reasoning_trace=reasoning_trace,
            metadata={
                "source": "custom_agent_runtime",
                "agent_id": self._agent_id,
                "agent_name": self._agent_name,
                "domain": self._domain,
                "tool_calls": len(actions),
                # Q4.1 Sandbox dry-run (2026-05-29)
                "dry_run": _is_dry_run,
                "would_do_actions": list(_would_do),
                # Wave D1.3 — token tracking canonical (consumido por pool_agents
                # task ao persistir runtime_metrics).
                "tokens_input": tokens_input,
                "tokens_output": tokens_output,
                "input_tokens": tokens_input,  # alias canonical
                "output_tokens": tokens_output,
                "model_used": model_used,
                "cost_usd": cost_usd,
                # Onda 5+1 — candidate IDs tocados (LGPD audit trail + UI badge).
                "touched_candidate_ids": touched_candidate_ids,
                "candidate_ids_truncated": candidate_ids_truncated,
            },
        )

    @trace_span("agent_studio.execute")
    async def execute(
        self,
        message: str = "",
        user_id: str = "system",
        company_id: str = "",
        session_id: str = "",
        context: Optional[dict[str, Any]] = None,
        *,
        channel: Literal["text", "voice", "voip", "whatsapp"] = "text",
        audio_chunk: bytes | None = None,
        voice_session_id: str | None = None,
        sender_phone: str | None = None,
        conversation_history: list[dict[str, Any]] | None = None,
        db: Any = None,
        dry_run: bool = False,
    ) -> AgentOutput:
        """Execute custom agent against a single user message.

        Q4.1 Sandbox (2026-05-29) — ``dry_run=True`` roda o raciocinio REAL
        (LLM/BYOK + tools de leitura) mas INTERCEPTA write tools (send_*/move_*/
        update_*): nenhum side-effect real acontece. O resultado expoe em
        ``metadata["dry_run"]=True`` e ``metadata["would_do_actions"]`` a lista
        de acoes que o agente FARIA, pro recruiter validar antes de ativar.

        Sprint 3.5 W4-1 V2 — channel routing (revisão 2026-05-23):
        - channel="text" (default): text-only langgraph conversation.
          Aliases legacy "chat" e "in_app" são aceitos via DeprecationWarning
          (audit AUDIT_CANDIDATE_CHAT_PUBLIC_2026-05-23.md — "in_app" era gap
          conceitual; chat candidato público vive em /api/v1/triagem/).
        - channel="voice": delegates to _invoke_voice, gated by feature flag
          voice_screening_v2_enabled (per-tenant). Audio in/out via VoiceCoreOrchestrator.
        - channel="whatsapp": T5a UX Transformação 5 — delegates to
          _invoke_whatsapp (message-driven sync), gated by per-agent
          ``whatsapp_enabled`` flag (checked at the REST endpoint layer).

        Keyword-only after context= to preserve backward compat with positional callers
        from Sprint <=3.4. process() callers route through here unchanged.
        """
        # Revert in_app_enabled (2026-05-23): aliases legacy "chat" e "in_app" são
        # mapeados pra "text" (langgraph default) com DeprecationWarning. "in_app"
        # como 4o canal canonical foi gap conceitual (audit
        # AUDIT_CANDIDATE_CHAT_PUBLIC_2026-05-23.md). Chat candidato público canonical
        # vive em /api/v1/triagem/ (handler dedicado, fora deste runtime).
        if channel in ("chat", "in_app"):
            import warnings
            warnings.warn(
                f"channel={channel!r} is deprecated; use channel='text' "
                "(revert 2026-05-23). Candidate-facing chat lives at "
                "/api/v1/triagem/ (separate handler).",
                DeprecationWarning,
                stacklevel=2,
            )
            channel = "text"

        # W-Channels-A: voice agora significa PSTN. voip = VoIP browser/Gemini Live.
        # Ambos resolvem para o mesmo _invoke_voice handler que faz routing interno
        # (PSTN vs VoIP) baseado em context["candidate_phone"]. A separação de flag
        # acontece dentro de _invoke_voice respeitando voice_enabled vs voip_enabled.

        # Sprint 3.5 W4-1 V2: channel-aware routing dispatch.
        if channel in ("voice", "voip"):
            # Pass intended mode forward so _invoke_voice can validate the right
            # per-agent flag (voice_enabled for PSTN, voip_enabled for VoIP).
            _voice_ctx = dict(context) if context else {}
            _voice_ctx.setdefault("voice_mode", "voip" if channel == "voip" else "pstn")
            return await self._invoke_voice(
                message=message,
                user_id=user_id,
                company_id=company_id,
                session_id=session_id,
                audio_chunk=audio_chunk,
                voice_session_id=voice_session_id,
                context=_voice_ctx,
            )
        if channel == "whatsapp":
            return await self._invoke_whatsapp(
                user_message=message,
                user_id=user_id,
                company_id=company_id,
                session_id=session_id,
                sender_phone=sender_phone or (context or {}).get("candidate_phone"),
                conversation_history=conversation_history,
                context=context,
                db=db,
            )

        effective_company_id = company_id or self._company_id
        # ADR-029-EXEMPT (audit Wave 2 2026-05-21): runtime-scope ContextVar re-set.
        # Justification: HTTP middleware (auth_enforcement) já setou via JWT verificado
        # upstream. Runtime re-set garante que self._company_id (do construtor, vinculado
        # ao agent_id no cache de runtimes) prevalece em casos onde execute() é chamado
        # de contexto não-HTTP (ex: background job, agent-to-agent invoke). Scope é
        # mandatoriamente reset em finally (linha ~541) para evitar ContextVar leak.
        # Sensor scripts/check_no_direct_contextvar_set.py reconhece este marker.
        _token = _CURRENT_COMPANY_ID.set(effective_company_id)

        # Q4.1 Sandbox: ativa interceptacao de write tools + buffer de would-do.
        # Reset garantido no finally (junto com _CURRENT_COMPANY_ID) — sem leak.
        _dry_token = _DRY_RUN.set(bool(dry_run))
        _would_do_buffer: list = []
        _would_token = _DRY_RUN_WOULD_DO.set(_would_do_buffer if dry_run else None)

        # === P0-8 + P0-9 audit 2026-05-21: pre-load AI persona + lia_field_toggles canonical ===
        # Antes: agent custom ignorava persona name/tone customizado pelo cliente E
        # ignorava os 34 toggles "Instruções LIA por Campo" (ghost settings).
        # Agora: helpers canônicos (get_ai_persona, build_company_agent_context) populam
        # context para _get_system_prompt aplicar via SystemPromptBuilder. Best-effort:
        # falhas logam warning e seguem com fallback (não bloqueia execução do agent).
        try:
            from app.core.database import AsyncSessionLocal
            from app.domains.persona.services.ai_persona_service import get_ai_persona
            from app.shared.services.lia_agent_context_builder import build_company_agent_context

            _ctx_local = dict(context) if context else {}
            async with AsyncSessionLocal() as _persona_db:
                try:
                    _persona = await get_ai_persona(effective_company_id, _persona_db)
                    if _persona:
                        _ctx_local["ai_persona"] = _persona
                except Exception as _persona_exc:
                    logger.warning(
                        "[CustomAgentRuntime:%s] get_ai_persona failed: %s",
                        self._agent_name, _persona_exc,
                    )
                try:
                    _lia_filtered = await build_company_agent_context(
                        effective_company_id, _persona_db,
                        job_context=_ctx_local.get("job_context"),
                    )
                    if _lia_filtered:
                        _ctx_local["lia_filtered_prompt"] = _lia_filtered
                except Exception as _ctx_exc:
                    logger.warning(
                        "[CustomAgentRuntime:%s] build_company_agent_context failed: %s",
                        self._agent_name, _ctx_exc,
                    )
            context = _ctx_local
        except Exception as _preload_exc:
            logger.warning(
                "[CustomAgentRuntime:%s] persona/toggles preload skipped: %s",
                self._agent_name, _preload_exc,
            )

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
            _DRY_RUN.reset(_dry_token)
            _DRY_RUN_WOULD_DO.reset(_would_token)



    @trace_span("agent_studio.invoke_voice")
    async def _invoke_voice(
        self,
        message: str,
        user_id: str,
        company_id: str,
        session_id: str,
        audio_chunk: bytes | None,
        voice_session_id: str | None,
        context: Optional[dict[str, Any]],
    ) -> AgentOutput:
        """Voice channel handler (Sprint 3.6 W4-1 V2 — full StudioVoicePlugin wiring).

        Gated by feature flag ``voice_screening_v2_enabled`` (per-tenant, OFF by default).
        Builds a ``StudioVoicePlugin`` from the agent config (system_prompt + allowed_tools
        + initial_greeting + persona + description) and passes it to
        ``VoiceCoreOrchestrator`` so the canonical core conversation loop runs with
        the agent's identity.

        Routing
        ───────
        - ``voice_session_id`` present + ``audio_chunk`` present → resume an existing
          session: process the audio chunk + generate next LIA response.
        - ``voice_session_id`` present + no audio → continuation handshake (returns
          session metadata; caller will stream audio in subsequent calls).
        - No ``voice_session_id`` + ``context["candidate_phone"]`` present → initiate
          PSTN call via ``orchestrator.initiate_call``.
        - No ``voice_session_id`` + no phone → initiate VoIP/browser session via
          ``orchestrator.initiate_voip_session``.

        Multi-tenancy: requires ``company_id`` (effective from arg or self._company_id).
        Rejects calls with neither ``audio_chunk`` nor ``voice_session_id`` — at least
        one must be provided so the orchestrator knows whether to bootstrap a new
        session or continue an existing one.
        """
        effective_company_id = company_id or self._company_id

        if not effective_company_id:
            return AgentOutput(
                message="Voice channel requires authenticated company_id.",
                confidence=0.0,
                metadata={"error": "voice_missing_company_id", "channel": "voice"},
            )

        # Sprint 3.5 feature flag gate (per-tenant rollout).
        try:
            from app.core.feature_flags import is_enabled as _ff_is_enabled
            if not _ff_is_enabled("voice_screening_v2_enabled", company_id=effective_company_id):
                return AgentOutput(
                    message="Voice channel disabled for this tenant.",
                    confidence=0.0,
                    metadata={
                        "status": "feature_not_enabled",
                        "channel": "voice",
                        "flag": "voice_screening_v2_enabled",
                    },
                )
        except Exception as _ff_exc:
            logger.warning(
                "[CustomAgentRuntime:%s] voice feature-flag check failed: %s — failing closed",
                self._agent_name, _ff_exc,
            )
            return AgentOutput(
                message="Voice channel unavailable (flag service error).",
                confidence=0.0,
                metadata={"status": "feature_check_failed", "channel": "voice"},
            )

        # Sprint 3.5: require either an audio_chunk (streaming) or a voice_session_id
        # (continuing session). Without either, caller has nothing for the orchestrator.
        if not audio_chunk and not voice_session_id:
            return AgentOutput(
                message="Voice channel requires audio_chunk or voice_session_id.",
                confidence=0.0,
                metadata={"error": "voice_no_payload", "channel": "voice"},
            )

        try:
            from app.domains.voice.services.voice_screening_orchestrator import (
                VoiceCoreOrchestrator,
            )
            from app.domains.voice.plugins.studio_voice_plugin import (
                StudioVoicePlugin,
            )

            # Sprint 3.6 W4-1 V2: build canonical Studio voice plugin from
            # agent config. The plugin owns initial_greeting + summary +
            # billing + audit hooks. Core orchestrator continues to own the
            # transport (Twilio / Gemini Live) and LLM conversational loop.
            ctx = context or {}
            agent_config: dict[str, Any] = {
                "system_prompt": self._system_prompt_template,
                "allowed_tools": list(self._allowed_tools),
                "initial_greeting": self._initial_greeting,
                "persona": self._persona,
                "description": self._description,
                "pricing_tier": self._pricing_tier,
            }
            plugin = StudioVoicePlugin(
                agent_id=self._agent_id,
                agent_config=agent_config,
                company_id=effective_company_id,
            )
            orchestrator = VoiceCoreOrchestrator(plugins=[plugin])

            # Routing 1: resume existing voice session.
            if voice_session_id:
                response_text: str | None = None
                transcribed: str | None = None
                if audio_chunk:
                    try:
                        transcribed = await orchestrator.process_audio_chunk(
                            session_id=voice_session_id,
                            audio_data=audio_chunk,
                        )
                    except Exception as _audio_exc:
                        logger.warning(
                            "[CustomAgentRuntime:%s] process_audio_chunk failed: %s",
                            self._agent_name, _audio_exc,
                        )
                    if transcribed:
                        try:
                            response_text = await orchestrator.generate_lia_response(
                                session_id=voice_session_id,
                                candidate_utterance=transcribed,
                            )
                        except Exception as _resp_exc:
                            logger.warning(
                                "[CustomAgentRuntime:%s] generate_lia_response failed: %s",
                                self._agent_name, _resp_exc,
                            )

                return AgentOutput(
                    message=response_text or "Voice session bootstrap acknowledged.",
                    confidence=1.0,
                    metadata={
                        "channel": "voice",
                        "status": "session_resumed",
                        "company_id": effective_company_id,
                        "agent_id": self._agent_id,
                        "agent_name": self._agent_name,
                        "voice_session_id": voice_session_id,
                        "session_id": voice_session_id,
                        "has_audio_chunk": bool(audio_chunk),
                        "audio_chunk_bytes": len(audio_chunk) if audio_chunk else 0,
                        "orchestrator_ready": True,
                        "plugin_name": plugin.plugin_name,
                        "user_id": user_id,
                        "transcribed": transcribed,
                        "lia_response": response_text,
                    },
                )

            # Routing 2 + 3: new session — PSTN vs VoIP.
            candidate_id = ctx.get("candidate_id") or user_id or "anonymous"
            candidate_name = ctx.get("candidate_name") or "Candidato"
            candidate_phone = ctx.get("candidate_phone")
            job_id = ctx.get("job_id")
            job_title = ctx.get("job_title") or self._description or "Vaga"
            language = ctx.get("language") or "pt-BR"

            if candidate_phone:
                session = await orchestrator.initiate_call(
                    candidate_id=candidate_id,
                    candidate_name=candidate_name,
                    phone_number=candidate_phone,
                    job_title=job_title,
                    company_id=effective_company_id,
                    job_id=job_id,
                    language=language,
                )
                is_voip = False
            else:
                session = await orchestrator.initiate_voip_session(
                    candidate_id=candidate_id,
                    candidate_name=candidate_name,
                    job_title=job_title,
                    company_id=effective_company_id,
                    job_id=job_id,
                    language=language,
                )
                is_voip = True

            return AgentOutput(
                message="Voice session bootstrap acknowledged.",
                confidence=1.0,
                metadata={
                    "channel": "voice",
                    "status": "session_initiated",
                    "company_id": effective_company_id,
                    "agent_id": self._agent_id,
                    "agent_name": self._agent_name,
                    "voice_session_id": getattr(session, "session_id", None),
                    "session_id": getattr(session, "session_id", session_id),
                    "call_sid": getattr(session, "call_sid", None),
                    "session_status": getattr(session, "status", None),
                    "voice_provider": getattr(session, "voice_provider", None),
                    "is_voip": is_voip,
                    # W-Channels-A (2026-05-23): expose canonical voice_mode for downstream
                    # observers (audit, billing, frontend status). Sourced from context (set
                    # in execute() dispatch) with fallback to is_voip flag.
                    "voice_mode": (ctx.get("voice_mode") if isinstance(ctx, dict) else None) or ("voip" if is_voip else "pstn"),
                    "has_audio_chunk": bool(audio_chunk),
                    "audio_chunk_bytes": len(audio_chunk) if audio_chunk else 0,
                    "orchestrator_ready": True,
                    "plugin_name": plugin.plugin_name,
                    "user_id": user_id,
                    # C.3 ticket (2026-05-23): surface the bootstrap greeting
                    # cached in session.metadata by VoiceCoreOrchestrator
                    # _on_session_initiated so frontend can render "agent
                    # talks first" UX without an extra round-trip.
                    "initial_greeting": (
                        (getattr(session, "metadata", None) or {}).get(
                            "initial_greeting"
                        )
                        if session is not None
                        else None
                    ),
                },
            )
        except Exception as exc:
            logger.error(
                "[CustomAgentRuntime:%s] voice invocation failed: %s",
                self._agent_name, exc, exc_info=True,
            )
            return AgentOutput(
                message="Voice channel error.",
                confidence=0.0,
                metadata={"error": str(exc), "channel": "voice"},
            )

    @trace_span("agent_studio.invoke_whatsapp")
    async def _invoke_whatsapp(
        self,
        *,
        user_message: str,
        user_id: str,
        company_id: str,
        session_id: str,
        sender_phone: str | None,
        conversation_history: list[dict[str, Any]] | None,
        context: Optional[dict[str, Any]],
        db: Any = None,
    ) -> AgentOutput:
        """WhatsApp channel handler (T5a UX Transformação 5).

        Diferentemente de ``_invoke_voice`` (async + bidirectional streaming
        via VoiceCoreOrchestrator), WhatsApp é message-driven sync. Não há
        orchestrator pesado — apenas:

            1. WhatsAppAgentPlugin.on_message_received(...) — audit canonical.
            2. WhatsAppAgentPlugin.generate_response(...) — LLM text-only.
            3. WhatsAppChannelAdapter.send(...) — canonical send via factory.
            4. WhatsAppAgentPlugin.on_message_sent(...) — billing + audit.

        Routing
        ───────
        - Sem ``sender_phone`` → erro estruturado (sem destino, sem envio).
        - Sem ``company_id`` → fail-closed (tenant guard).

        Multi-tenancy: ``company_id`` SEMPRE vem do caller (REST endpoint
        canonical via Depends(require_company_id) → JWT). NÃO é trusted
        do payload; o caller é responsável por garantir a origem.

        Compatibilidade com voice path: plugin import lazy + try/except em
        todos side effects → audit/billing nunca bloqueiam delivery.
        """
        effective_company_id = company_id or self._company_id

        if not effective_company_id:
            return AgentOutput(
                message="WhatsApp channel requires authenticated company_id.",
                confidence=0.0,
                metadata={"error": "whatsapp_missing_company_id", "channel": "whatsapp"},
            )

        if not sender_phone:
            return AgentOutput(
                message="WhatsApp channel requires sender_phone.",
                confidence=0.0,
                metadata={"error": "whatsapp_missing_sender_phone", "channel": "whatsapp"},
            )

        if not user_message or not user_message.strip():
            return AgentOutput(
                message="WhatsApp channel requires non-empty user_message.",
                confidence=0.0,
                metadata={"error": "whatsapp_empty_message", "channel": "whatsapp"},
            )

        try:
            from app.domains.agent_studio.whatsapp_agent_plugin import (
                WhatsAppAgentPlugin,
            )

            plugin = WhatsAppAgentPlugin(
                agent_id=self._agent_id,
                agent_config={
                    "system_prompt": self._system_prompt_template,
                    "allowed_tools": list(self._allowed_tools),
                    "description": self._description,
                    "persona": self._persona,
                    "pricing_tier": self._pricing_tier,
                },
                company_id=effective_company_id,
            )

            # 1. Audit message received (best-effort).
            await plugin.on_message_received(
                user_message=user_message,
                sender_phone=sender_phone,
                session_id=session_id,
                db=db,
            )

            # 2. Generate response via canonical LLM.
            response_text = await plugin.generate_response(
                conversation_history=conversation_history or [],
                user_message=user_message,
                sender_phone=sender_phone,
            )

            # 3. Send via canonical WhatsAppChannelAdapter.
            from app.shared.channels.adapters.whatsapp_adapter import (
                WhatsAppChannelAdapter,
            )
            from app.shared.channels.channel_adapter import ChannelMessage

            adapter = WhatsAppChannelAdapter()
            ctx = context or {}
            candidate_name = (
                ctx.get("candidate_name")
                or ctx.get("recipient_name")
                or "Candidato"
            )
            recipient_id = ctx.get("candidate_id") or sender_phone

            send_msg = ChannelMessage(
                recipient_id=str(recipient_id),
                recipient_name=str(candidate_name),
                recipient_contact=sender_phone,
                body_text=response_text,
                company_id=effective_company_id,
                metadata={
                    "agent_id": self._agent_id,
                    "agent_name": self._agent_name,
                    "plugin": plugin.plugin_name,
                    "session_id": session_id,
                },
            )

            delivery = await adapter.send(send_msg)
            delivery_success = bool(delivery.success)
            delivery_status = str(getattr(delivery.status, "value", delivery.status))

            # 4. Audit completion + billing (best-effort).
            await plugin.on_message_sent(
                delivery_success=delivery_success,
                response_text=response_text,
                delivery_status=delivery_status,
                db=db,
            )

            return AgentOutput(
                message=response_text,
                confidence=1.0 if delivery_success else 0.5,
                metadata={
                    "channel": "whatsapp",
                    "status": "message_sent" if delivery_success else "send_failed",
                    "company_id": effective_company_id,
                    "agent_id": self._agent_id,
                    "agent_name": self._agent_name,
                    "plugin_name": plugin.plugin_name,
                    "delivery_status": delivery_status,
                    "delivery_message_id": delivery.message_id,
                    "delivery_provider_id": delivery.provider_id,
                    "delivery_error": delivery.error,
                    "response_text": response_text,
                    "response_len": len(response_text),
                    "sender_phone": sender_phone,
                    "session_id": session_id,
                    "user_id": user_id,
                },
            )
        except Exception as exc:
            logger.error(
                "[CustomAgentRuntime:%s] whatsapp invocation failed: %s",
                self._agent_name, exc, exc_info=True,
            )
            return AgentOutput(
                message="WhatsApp channel error.",
                confidence=0.0,
                metadata={"error": str(exc), "channel": "whatsapp"},
            )


_runtime_cache: dict[str, CustomAgentRuntime] = {}
_RUNTIME_CACHE_MAX_SIZE = 500
_RUNTIME_CACHE_WARN_SIZE = 200


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
    initial_greeting: str | None = None,
    description: str | None = None,
    persona: dict[str, Any] | None = None,
    pricing_tier: str = "pro",
) -> CustomAgentRuntime:
    cache_key = f"{agent_id}:{company_id}"
    # ── GAP-5 fix: evict oldest entry when cache exceeds max size ──
    # ADR-004: cache sem maxsize permite memory leak silencioso.
    # LRU simples: evicta a primeira chave (oldest insertion) quando cheio.
    _cache_size = len(_runtime_cache)
    if _cache_size >= _RUNTIME_CACHE_WARN_SIZE and _cache_size % 50 == 0:
        logger.warning(
            "[CustomAgentRuntime][cache] size=%d (warn=%d, max=%d)",
            _cache_size, _RUNTIME_CACHE_WARN_SIZE, _RUNTIME_CACHE_MAX_SIZE,
        )
    if _cache_size >= _RUNTIME_CACHE_MAX_SIZE and cache_key not in _runtime_cache:
        _evict_key = next(iter(_runtime_cache))
        del _runtime_cache[_evict_key]
        logger.info("[CustomAgentRuntime][cache] evicted oldest entry: %s", _evict_key)
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
            initial_greeting=initial_greeting,
            description=description,
            persona=persona,
            pricing_tier=pricing_tier,
        )
    return _runtime_cache[cache_key]
