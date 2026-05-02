"""
TimedToolNode — ToolNode com métricas de latência e timeout.

Subclasse de ToolNode do LangGraph que:
- Aplica asyncio.wait_for(timeout) em cada invocação (André R6/P4)
  - default: 15s por tool call
  - por tool: tool_timeouts={"search_candidates": 30}
  - em TimeoutError: injeta ToolMessage de erro + retorna gracefully
- Mede latência e emite métricas Prometheus (opcional)
- Compatível com create_react_agent (aceita ToolNode diretamente)
- LIA-C03: Intercepta tool call args para verificar filtros discriminatórios
  via FairnessGuard antes de executar a tool.

Compatível com LangGraph 0.2.x.
"""
import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from langgraph.prebuilt import ToolNode
    _HAS_LANGGRAPH = True
except ImportError:
    _HAS_LANGGRAPH = False
    ToolNode = object  # type: ignore[assignment,misc]

_METRICS_AVAILABLE = False

# ---------------------------------------------------------------------------
# LIA-C03: Feature flag — desative via env FAIRNESS_TOOL_CHECK_ENABLED=false
# ---------------------------------------------------------------------------
_FAIRNESS_TOOL_CHECK_ENABLED_DEFAULT = (
    os.environ.get("FAIRNESS_TOOL_CHECK_ENABLED", "true").lower() == "true"
)


if _HAS_LANGGRAPH:
    class TimedToolNode(ToolNode):  # type: ignore[valid-type,misc]
        """
        ToolNode com timeout e instrumentação de latência para LangGraph.

        Uso direto com create_react_agent:
            timed_node = TimedToolNode(
                tools=[my_tool_1, my_tool_2],
                domain="pipeline",
                default_timeout_seconds=15,
                tool_timeouts={"search_candidates": 30},
            )
            graph = create_react_agent(model, tools=timed_node)
        """

        def __init__(
            self,
            tools: List[Any],
            domain: str = "unknown",
            handle_tool_errors: bool = True,
            default_timeout_seconds: int = 15,
            tool_timeouts: Optional[Dict[str, int]] = None,
            fairness_tool_check_enabled: Optional[bool] = None,
            **kwargs: Any,
        ):
            super().__init__(
                tools=tools,
                handle_tool_errors=handle_tool_errors,
                **kwargs,
            )
            self.domain = domain
            self.default_timeout_seconds = default_timeout_seconds
            self.tool_timeouts: Dict[str, int] = tool_timeouts or {}
            self._tools_list = tools
            # LIA-C03: flag de instância (sobrescreve env se fornecido explicitamente)
            if fairness_tool_check_enabled is not None:
                self._fairness_tool_check_enabled = fairness_tool_check_enabled
            else:
                self._fairness_tool_check_enabled = _FAIRNESS_TOOL_CHECK_ENABLED_DEFAULT

        # ------------------------------------------------------------------
        # LIA-C03: Fairness check nos argumentos da tool call
        # ------------------------------------------------------------------

        async def _check_tool_args_fairness(
            self, tool_name: str, tool_args: dict
        ) -> Optional[str]:
            """
            Verifica se os argumentos de uma tool call contêm filtros discriminatórios.

            Retorna mensagem educacional de bloqueio se detectado, None se limpo.
            Falha silenciosamente (retorna None) em caso de erro para não
            interromper o pipeline principal.

            LIA-C03 — EU AI Act Art. 14: supervisão humana em sistemas de alto risco.
            """
            if not self._fairness_tool_check_enabled:
                return None

            args_str = json.dumps(tool_args, ensure_ascii=False)

            try:
                from app.shared.compliance.fairness_guard import FairnessGuard
                guard = FairnessGuard()
                result = guard.check(args_str)
                if result.is_blocked:
                    logger.warning(
                        "[LIA-C03][TimedToolNode] FairnessGuard BLOQUEOU tool domain=%s "
                        "tool=%s category=%s terms=%s args_preview=%s",
                        self.domain,
                        tool_name,
                        result.category,
                        result.blocked_terms,
                        args_str[:200],
                    )
                    return result.educational_message
            except Exception as exc:
                logger.warning(
                    "[LIA-C03][TimedToolNode] FairnessGuard tool check falhou (fail-safe): "
                    "domain=%s tool=%s error=%s",
                    self.domain, tool_name, exc,
                )
            return None

        def _build_fairness_block_response(
            self,
            input: Any,
            tool_calls: List[Any],
            blocked_tool_name: str,
            educational_message: str,
        ) -> Any:
            """Injeta ToolMessage de bloqueio de fairness para a tool_call bloqueada."""
            try:
                from langchain_core.messages import ToolMessage

                block_messages = []
                for tc in tool_calls:
                    tool_call_id = (
                        tc.get("id", "unknown") if isinstance(tc, dict)
                        else getattr(tc, "id", "unknown")
                    )
                    tool_name = (
                        tc.get("name", "unknown") if isinstance(tc, dict)
                        else getattr(tc, "name", "unknown")
                    )
                    block_messages.append(
                        ToolMessage(
                            content=(
                                f"[COMPLIANCE LIA-C03] A ferramenta '{tool_name}' foi bloqueada "
                                f"por conter filtros que podem configurar discriminação. "
                                f"{educational_message}"
                            ),
                            tool_call_id=tool_call_id,
                            name=tool_name,
                        )
                    )

                if hasattr(input, "messages"):
                    existing = list(input.messages) + block_messages
                    if hasattr(input, "model_copy"):
                        return input.model_copy(update={"messages": existing})
                    return {**input, "messages": existing}
                elif isinstance(input, dict):
                    existing = list(input.get("messages", [])) + block_messages
                    return {**input, "messages": existing}
            except Exception as exc:
                logger.error(
                    "[LIA-C03][TimedToolNode] Erro ao construir fairness block response: %s", exc
                )
            return input

        # ------------------------------------------------------------------
        # Core: ainvoke com timeout + fairness check (LIA-C03)
        # ------------------------------------------------------------------

        async def ainvoke(self, input: Any, config: Any = None, **kwargs: Any) -> Any:
            """Override de ainvoke com timeout, fairness check e métricas."""
            start = time.time()
            tool_calls = self._extract_tool_calls(input)

            # LIA-C03: Verificar fairness nos args de cada tool call ANTES de executar
            for tc in tool_calls:
                tool_name = (
                    tc.get("name", "unknown") if isinstance(tc, dict)
                    else getattr(tc, "name", "unknown")
                )
                tool_args = (
                    tc.get("args", {}) if isinstance(tc, dict)
                    else getattr(tc, "args", {})
                ) or {}

                block_msg = await self._check_tool_args_fairness(tool_name, tool_args)
                if block_msg is not None:
                    return self._build_fairness_block_response(
                        input, tool_calls, tool_name, block_msg
                    )

            # Timeout conservador: menor entre default e overrides das tools chamadas
            timeout = self.default_timeout_seconds
            for tc in tool_calls:
                name = tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
                if name in self.tool_timeouts:
                    timeout = min(timeout, self.tool_timeouts[name])

            try:
                result = await asyncio.wait_for(
                    super().ainvoke(input, config, **kwargs),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                duration_ms = (time.time() - start) * 1000
                names = [
                    (tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", "?"))
                    for tc in tool_calls
                ]
                logger.warning(
                    "[TimedToolNode] TIMEOUT domain=%s timeout=%ds duration=%.0fms tools=%s",
                    self.domain, timeout, duration_ms, names,
                )
                return self._build_timeout_response(input, tool_calls, timeout)

            duration_ms = (time.time() - start) * 1000
            for tc in tool_calls:
                name = tc.get("name", "unknown") if isinstance(tc, dict) else getattr(tc, "name", "unknown")
                if _METRICS_AVAILABLE:
                    try:
                        agent_iterations_total.labels(
                            domain=self.domain, action_type=f"tool:{name}"
                        ).inc()
                    except Exception:
                        pass
                logger.debug(
                    "[TimedToolNode] domain=%s tool=%s duration=%.1fms",
                    self.domain, name, duration_ms,
                )
            return result

        def _extract_tool_calls(self, input: Any) -> List[Any]:
            """Extrai tool_calls do último message do estado."""
            messages = (
                getattr(input, "messages", [])
                if hasattr(input, "messages")
                else input.get("messages", []) if isinstance(input, dict) else []
            )
            if messages:
                last = messages[-1]
                return getattr(last, "tool_calls", []) or []
            return []

        def _build_timeout_response(
            self,
            input: Any,
            tool_calls: List[Any],
            timeout: int,
        ) -> Any:
            """Injeta ToolMessage de erro para cada tool_call pendente."""
            try:
                from langchain_core.messages import ToolMessage

                timeout_messages = []
                for tc in tool_calls:
                    tool_call_id = tc.get("id", "unknown") if isinstance(tc, dict) else getattr(tc, "id", "unknown")
                    tool_name = tc.get("name", "unknown") if isinstance(tc, dict) else getattr(tc, "name", "unknown")
                    timeout_messages.append(
                        ToolMessage(
                            content=(
                                f"Tool timeout after {timeout}s. A ferramenta '{tool_name}' "
                                "demorou mais que o esperado. Tente novamente ou use uma abordagem alternativa."
                            ),
                            tool_call_id=tool_call_id,
                            name=tool_name,
                        )
                    )

                if hasattr(input, "messages"):
                    existing = list(input.messages) + timeout_messages
                    if hasattr(input, "model_copy"):
                        return input.model_copy(update={"messages": existing})
                    return {**input, "messages": existing}
                elif isinstance(input, dict):
                    existing = list(input.get("messages", [])) + timeout_messages
                    return {**input, "messages": existing}
            except Exception as exc:
                logger.error("[TimedToolNode] Erro ao construir timeout response: %s", exc)
            return input

        def get_tools(self) -> List[Any]:
            return self._tools_list

else:
    # Fallback quando LangGraph não instalado (testes sem deps)
    class TimedToolNode:  # type: ignore[no-redef]
        """Stub quando LangGraph não disponível."""

        def __init__(
            self,
            tools: List[Any],
            domain: str = "unknown",
            handle_tool_errors: bool = True,
            default_timeout_seconds: int = 15,
            tool_timeouts: Optional[Dict[str, int]] = None,
            fairness_tool_check_enabled: Optional[bool] = None,
            **kwargs: Any,
        ):
            self.domain = domain
            self.default_timeout_seconds = default_timeout_seconds
            self.tool_timeouts: Dict[str, int] = tool_timeouts or {}
            self._tools_list = tools
            self._node = None
            if fairness_tool_check_enabled is not None:
                self._fairness_tool_check_enabled = fairness_tool_check_enabled
            else:
                self._fairness_tool_check_enabled = _FAIRNESS_TOOL_CHECK_ENABLED_DEFAULT

        async def _check_tool_args_fairness(
            self, tool_name: str, tool_args: dict
        ) -> Optional[str]:
            if not self._fairness_tool_check_enabled:
                return None
            args_str = json.dumps(tool_args, ensure_ascii=False)
            try:
                from app.shared.compliance.fairness_guard import FairnessGuard
                guard = FairnessGuard()
                result = guard.check(args_str)
                if result.is_blocked:
                    logger.warning(
                        "[LIA-C03][TimedToolNode] FairnessGuard BLOQUEOU tool domain=%s "
                        "tool=%s category=%s terms=%s args_preview=%s",
                        self.domain,
                        tool_name,
                        result.category,
                        result.blocked_terms,
                        args_str[:200],
                    )
                    return result.educational_message
            except Exception as exc:
                logger.warning(
                    "[LIA-C03][TimedToolNode] FairnessGuard tool check falhou (fail-safe): "
                    "domain=%s tool=%s error=%s",
                    self.domain, tool_name, exc,
                )
            return None

        async def ainvoke(self, input: Any, config: Any = None, **kwargs: Any) -> Any:
            logger.error("[TimedToolNode] LangGraph não disponível")
            return input

        async def __call__(self, state: Any, config: Any = None) -> Any:
            return await self.ainvoke(state, config)

        def _build_timeout_response(self, input: Any, tool_calls: List[Any], timeout: int) -> Any:
            return input

        def get_tools(self) -> List[Any]:
            return self._tools_list



# ---------------------------------------------------------------------------
# GovernanceToolNode — pós-execução: PII masking + audit + fail-safe
# ---------------------------------------------------------------------------
# Estende TimedToolNode (que já aplica FairnessGuard PRÉ-execução, LIA-C03).
# Esta classe adiciona camada PÓS-execução:
#   1. PII masking em campos declarados em ToolContract.pii_output_fields
#   2. Audit log não-bloqueante via AuditService (asyncio.create_task)
#   3. Fail-safe: exceções em governança NUNCA quebram o pipeline principal
#
# Harness Engineering: tipo SENSOR computacional (feedback pós-execução).
# Referência: ToolContract.touches_pii / pii_output_fields / affects_candidate_decision
# ---------------------------------------------------------------------------

if _HAS_LANGGRAPH:
    class GovernanceToolNode(TimedToolNode):
        """
        ToolNode com governança pós-execução sobre ToolMessage.content.

        Uso:
            contracts = [ToolContract(name="search", touches_pii=True, pii_output_fields=["email"])]
            node = GovernanceToolNode(tools=[...], tool_contracts=contracts, domain="pipeline")
            graph = create_react_agent(model, tools=node)
        """

        def __init__(
            self,
            tools: List[Any],
            tool_contracts: Optional[List[Any]] = None,
            **kwargs: Any,
        ) -> None:
            super().__init__(tools=tools, **kwargs)
            self._contract_map: Dict[str, Any] = {}
            for contract in (tool_contracts or []):
                name = getattr(contract, "name", None)
                if name:
                    self._contract_map[name] = contract

        async def ainvoke(self, input: Any, config: Any = None, **kwargs: Any) -> Any:
            result = await super().ainvoke(input, config, **kwargs)
            return await self._apply_governance(result, config)

        async def _apply_governance(self, state: Any, config: Any) -> Any:
            """Aplica PII masking e audit a ToolMessages do resultado. Fail-safe."""
            try:
                from langchain_core.messages import ToolMessage

                messages: List[Any] = (
                    list(state.get("messages", [])) if isinstance(state, dict)
                    else list(getattr(state, "messages", []))
                )
                new_messages = list(messages)

                configurable: Dict[str, Any] = (
                    (config or {}).get("configurable", {})
                    if isinstance(config, dict) else {}
                )
                company_id: Optional[str] = configurable.get("company_id")
                user_id: Optional[str] = configurable.get("user_id")

                for i, msg in enumerate(new_messages):
                    if not isinstance(msg, ToolMessage):
                        continue

                    tool_name: str = getattr(msg, "name", None) or ""
                    contract = self._contract_map.get(tool_name)
                    if contract is None:
                        continue  # unknown tool — passthrough, no governance

                    content: str = msg.content
                    modified = False

                    # PII masking: field-level over parsed JSON output
                    if (
                        getattr(contract, "touches_pii", False)
                        and getattr(contract, "pii_output_fields", None)
                    ):
                        try:
                            content_dict = json.loads(content)
                            if isinstance(content_dict, dict):
                                content_dict = self._mask_pii_fields(
                                    content_dict, contract.pii_output_fields
                                )
                                content = json.dumps(content_dict, ensure_ascii=False)
                                modified = True
                        except Exception:
                            pass  # fail-safe: invalid JSON → keep original content

                    if modified:
                        new_messages[i] = ToolMessage(
                            content=content,
                            tool_call_id=getattr(msg, "tool_call_id", "unknown"),
                            name=tool_name,
                        )

                    # Audit: non-blocking background task (always for known tools)
                    asyncio.create_task(
                        self._audit(
                            tool_name=tool_name,
                            company_id=company_id,
                            user_id=user_id,
                            success=True,
                            output_snippet=content[:200],
                        )
                    )

                if isinstance(state, dict):
                    return {**state, "messages": new_messages}
                try:
                    return state.model_copy(update={"messages": new_messages})
                except Exception:
                    return state

            except Exception as exc:
                logger.warning("[GovernanceToolNode] _apply_governance fail-safe: %s", exc)
                return state

        def _mask_pii_fields(self, data: Any, fields: List[str]) -> Any:
            """Recursivamente mascara campos PII declarados em pii_output_fields."""
            if isinstance(data, dict):
                result_dict: Dict[str, Any] = {}
                for key, value in data.items():
                    if key in fields:
                        try:
                            import app.shared.pii_masking as _pm
                            result_dict[key] = _pm.mask_pii(value)
                        except Exception:
                            result_dict[key] = "[REDACTED]"
                    else:
                        result_dict[key] = self._mask_pii_fields(value, fields)
                return result_dict
            elif isinstance(data, list):
                return [self._mask_pii_fields(item, fields) for item in data]
            return data

        async def _audit(
            self,
            *,
            tool_name: str,
            company_id: Optional[str],
            user_id: Optional[str],
            success: bool,
            output_snippet: str,
        ) -> None:
            """Audit log assíncrono. Fail-safe: nunca propaga exceção."""
            try:
                from app.shared.compliance.audit_service import get_audit_service
                audit = get_audit_service()
                await audit.log_action(
                    action_type="tool_execution",
                    tool_name=tool_name,
                    company_id=company_id,
                    user_id=user_id,
                    success=success,
                    output_snippet=output_snippet,
                )
            except Exception as exc:
                logger.debug(
                    "[GovernanceToolNode] audit fail-safe: tool=%s error=%s",
                    tool_name,
                    exc,
                )

else:
    class GovernanceToolNode(TimedToolNode):  # type: ignore[no-redef]
        """Stub quando LangGraph não disponível."""

        def __init__(
            self,
            tools: List[Any],
            tool_contracts: Optional[List[Any]] = None,
            **kwargs: Any,
        ) -> None:
            super().__init__(tools=tools, **kwargs)
            self._contract_map: Dict[str, Any] = {}
            for contract in (tool_contracts or []):
                name = getattr(contract, "name", None)
                if name:
                    self._contract_map[name] = contract

        async def ainvoke(self, input: Any, config: Any = None, **kwargs: Any) -> Any:
            logger.error("[GovernanceToolNode] LangGraph não disponível")
            return input

        async def _apply_governance(self, state: Any, config: Any) -> Any:
            return state
