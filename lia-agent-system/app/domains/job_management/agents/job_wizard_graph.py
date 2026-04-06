"""
Job Wizard Graph - LangGraph-style State Machine.

Implements a directed graph where nodes are processing steps and
edges define the flow between them. Supports conditional routing,
streaming execution, and state persistence.
"""
import asyncio
import logging
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, Final, Optional
from uuid import uuid4

try:
    from langsmith import traceable as _traceable
except ImportError:
    def _traceable(**kwargs):  # type: ignore[misc]
        def decorator(fn):
            return fn
        return decorator

from lia_agents_core.state_machine import (
    GraphExecutionLog,
    JobWizardState,
    ReasoningStep,
    WizardIntent,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.nodes import JobWizardNodes, job_wizard_nodes
from app.services.checkpoint_service import delete_checkpoint, restore_checkpoint, save_checkpoint
from app.tools import initialize_tools

logger = logging.getLogger(__name__)

# B2 — campos efêmeros excluídos do merge de checkpoint (estado da sessão atual)
EPHEMERAL_FIELDS: frozenset = frozenset({"user_message", "session_id", "execution_id"})

_tools_initialized = False


@dataclass
class EdgeCondition:
    """Condition for a graph edge."""
    target_node: str
    condition: Callable[[JobWizardState], bool] | None = None
    priority: int = 0


class JobWizardGraph:
    """
    LangGraph-style state machine for job wizard.
    
    The graph consists of:
    - Nodes: Async functions that process and update state
    - Edges: Connections between nodes with optional conditions
    - Entry point: Starting node for execution
    - End conditions: When to stop graph execution
    """
    
    MAX_ITERATIONS = 10
    START_NODE = "intent_classifier"
    END_NODE = "END"
    
    def __init__(self, nodes: JobWizardNodes | None = None):
        global _tools_initialized
        if not _tools_initialized:
            initialize_tools()
            _tools_initialized = True
            logger.info("Tools initialized for JobWizardGraph")
        
        self.nodes = nodes or job_wizard_nodes
        self.edges = self._build_edges()
        self.conditional_edges = self._build_conditional_edges()
        self.logger = logging.getLogger(self.__class__.__name__)
        self._execution_logs: dict[str, GraphExecutionLog] = {}
        self._compiled_lg: Any | None = None  # LangGraph compiled graph (lazy init)
    
    def _build_edges(self) -> dict[str, list[str]]:
        """
        Define static graph edges (transitions).
        
        Each key is a node name, and the value is a list of possible
        next nodes. For conditional routing, use _build_conditional_edges.
        """
        return {
            "intent_classifier": ["field_extractor"],
            "field_extractor": ["tool_router"],
            "tool_router": ["tool_executor", "response_generator"],
            "tool_executor": ["response_generator"],
            "response_generator": ["stage_transition"],
            "stage_transition": ["END"]
        }
    
    def _build_conditional_edges(self) -> dict[str, list[EdgeCondition]]:
        """
        Define conditional edges based on state.
        
        Returns edges with conditions that are evaluated at runtime.
        Higher priority conditions are checked first.
        """
        return {
            "intent_classifier": [
                EdgeCondition(
                    target_node="response_generator",
                    condition=lambda s: s.get("intent") in [
                        WizardIntent.START_FROM_SCRATCH.value,
                        WizardIntent.USE_EXISTING.value,
                        WizardIntent.USE_TEMPLATE.value
                    ],
                    priority=3
                ),
                EdgeCondition(
                    target_node="response_generator",
                    condition=lambda s: s.get("intent") in [
                        WizardIntent.HELP.value,
                        WizardIntent.ASK_QUESTION.value
                    ],
                    priority=2
                ),
                EdgeCondition(
                    target_node="field_extractor",
                    condition=lambda s: s.get("intent") in [
                        WizardIntent.PROVIDE_INFO.value,
                        WizardIntent.MODIFY.value
                    ],
                    priority=1
                ),
                EdgeCondition(
                    target_node="stage_transition",
                    condition=lambda s: s.get("intent") in [
                        WizardIntent.SKIP.value,
                        WizardIntent.GO_BACK.value,
                        WizardIntent.CONFIRM.value
                    ],
                    priority=1
                ),
                EdgeCondition(
                    target_node="field_extractor",
                    priority=0
                ),
            ],
            "tool_router": [
                EdgeCondition(
                    target_node="tool_executor",
                    condition=lambda s: len(s.get("tool_calls", [])) > 0,
                    priority=1
                ),
                EdgeCondition(
                    target_node="response_generator",
                    priority=0
                ),
            ],
            "stage_transition": [
                EdgeCondition(
                    target_node="END",
                    condition=lambda s: not s.get("should_continue", True),
                    priority=1
                ),
                EdgeCondition(
                    target_node="intent_classifier",
                    condition=lambda s: s.get("should_continue", False),
                    priority=0
                ),
            ]
        }
    
    # ------------------------------------------------------------------
    # LangGraph nativo — StateGraph
    # ------------------------------------------------------------------

    def _build_langgraph(self):
        """Constrói StateGraph nativo substituindo checkpoint_service por PostgresSaver."""
        from langgraph.graph import END as LEND
        from langgraph.graph import StateGraph
        from lia_agents_core.checkpointer import get_checkpointer

        nodes_ref = self.nodes

        def _wrap(name: str):
            """Cria wrapper que chama nodes_ref.get_node(name) com o estado."""
            async def _node_fn(state):
                fn = nodes_ref.get_node(name)
                if fn is None:
                    state["error"] = f"Node not found: {name}"
                    state["should_continue"] = False
                    return state
                return await fn(state)
            _node_fn.__name__ = name
            return _node_fn

        # ---- Routing functions ----

        def route_intent_classifier(state) -> str:
            intent = state.get("intent", "")
            if intent in [
                WizardIntent.START_FROM_SCRATCH.value,
                WizardIntent.USE_EXISTING.value,
                WizardIntent.USE_TEMPLATE.value,
                WizardIntent.HELP.value,
                WizardIntent.ASK_QUESTION.value,
            ]:
                return "response_generator"
            if intent in [
                WizardIntent.SKIP.value,
                WizardIntent.GO_BACK.value,
                WizardIntent.CONFIRM.value,
            ]:
                return "stage_transition"
            return "field_extractor"  # PROVIDE_INFO, MODIFY, default

        def route_tool_router(state) -> str:
            return "tool_executor" if len(state.get("tool_calls", [])) > 0 else "response_generator"

        def route_stage_transition(state) -> str:
            return "end" if not state.get("should_continue", True) else "continue"

        # ---- Build graph ----

        builder = StateGraph(JobWizardState)

        for node_name in [
            "intent_classifier", "field_extractor", "tool_router",
            "tool_executor", "response_generator", "stage_transition",
        ]:
            builder.add_node(node_name, _wrap(node_name))

        builder.set_entry_point("intent_classifier")
        builder.add_conditional_edges("intent_classifier", route_intent_classifier, {
            "response_generator": "response_generator",
            "stage_transition": "stage_transition",
            "field_extractor": "field_extractor",
        })
        builder.add_edge("field_extractor", "tool_router")
        builder.add_conditional_edges("tool_router", route_tool_router, {
            "tool_executor": "tool_executor",
            "response_generator": "response_generator",
        })
        builder.add_edge("tool_executor", "response_generator")
        builder.add_edge("response_generator", "stage_transition")
        builder.add_conditional_edges("stage_transition", route_stage_transition, {
            "end": LEND,
            "continue": "intent_classifier",
        })

        # interrupt_before stage_transition: permite HITL antes de criar vaga (CONFIRM intent)
        return builder.compile(
            checkpointer=get_checkpointer(),
            interrupt_before=["stage_transition"],
        )

    async def _invoke_langgraph(
        self, state: JobWizardState, audit_callback=None
    ) -> JobWizardState:
        """Executa via StateGraph nativo com PostgresSaver (substitui checkpoint_service)."""
        if self._compiled_lg is None:
            self._compiled_lg = self._build_langgraph()

        session_id = state.get("session_id", f"system:{uuid4()}")
        if audit_callback:
            audit_callback.on_chain_start_manual()

        self.logger.info(
            "[JobWizardGraph] iniciando execução (LangGraph nativo)",
            extra={"session_id": session_id, "graph": "JobWizardGraph"},
        )

        config = {"configurable": {"thread_id": session_id}}

        try:
            result = await self._compiled_lg.ainvoke(state, config=config)
        except Exception as exc:
            self.logger.error(f"[JobWizardGraph] StateGraph ainvoke error: {exc}", exc_info=True)
            result = dict(state)
            result["error"] = str(exc)

        # ── HITL: detectar interrupt_before stage_transition ──────────────────
        # LangGraph retorna {"__interrupt__": [...]} quando pausa num nó
        if isinstance(result, dict) and result.get("__interrupt__"):
            intent = state.get("intent", "")
            from lia_agents_core.state_machine import WizardIntent
            if intent == WizardIntent.CONFIRM.value and not state.get("hitl_approved"):
                # Solicitar aprovação humana antes de criar a vaga
                try:
                    from app.services.hitl_service import hitl_service
                    ws_session_id = str(session_id)
                    pending_id = await hitl_service.request_approval(
                        thread_id=ws_session_id,
                        action="create_job",
                        description=f"Confirmar criação da vaga: {state.get('job_title', 'sem título')}",
                        data={
                            "job_title": state.get("job_title", ""),
                            "company_id": state.get("company_id", ""),
                            "fields": state.get("fields", {}),
                        },
                        ws_session_id=ws_session_id,
                        domain="wizard",
                        company_id=state.get("company_id", ""),
                    )
                    # Armazenar contexto de resume para quando aprovação chegar
                    await hitl_service.store_resume_info(
                        thread_id=ws_session_id,
                        domain="wizard",
                        session_id=ws_session_id,
                        agent_input_dict={
                            "message": state.get("user_message", ""),
                            "context": {
                                "company_id": state.get("company_id", ""),
                                "hitl_approved": True,
                                "hitl_pending_id": pending_id,
                            },
                            "session_id": ws_session_id,
                            "company_id": state.get("company_id", ""),
                            "user_id": state.get("user_id", ""),
                        },
                        hitl_context="wizard_confirm_job",
                    )
                    result = dict(state)
                    result["hitl_pending"] = True
                    result["hitl_pending_id"] = pending_id
                    self.logger.info("[JobWizardGraph] HITL aprovação solicitada session=%s", session_id)
                except Exception as _hitl_exc:
                    self.logger.warning("[JobWizardGraph] HITL request_approval falhou: %s", _hitl_exc)
            else:
                # Não é CONFIRM ou já aprovado → resume imediatamente
                try:
                    result = await self._compiled_lg.ainvoke(None, config=config)
                except Exception as exc:
                    self.logger.warning("[JobWizardGraph] Resume automático falhou: %s", exc)

        if audit_callback:
            error = result.get("error") if isinstance(result, dict) else None
            try:
                await audit_callback.on_chain_end_manual(
                    confidence=0.9 if not error else 0.3,
                    success=not bool(error),
                    error=error,
                )
            except Exception:
                pass

        self.logger.info(
            "[JobWizardGraph] execução concluída (LangGraph nativo)",
            extra={"session_id": session_id, "graph": "JobWizardGraph"},
        )
        return result

    # ------------------------------------------------------------------
    # Execução
    # ------------------------------------------------------------------

    async def invoke(
        self,
        state: JobWizardState,
        start_node: str | None = None,
        db: AsyncSession | None = None,
        audit_callback=None,
    ) -> JobWizardState:
        """Invoca o grafo via LangGraph nativo (PostgresSaver gerencia checkpoints).

        Os parâmetros `start_node` e `db` são mantidos por compatibilidade de assinatura
        mas não são utilizados — o LangGraph StateGraph gerencia o fluxo e checkpoints.
        """
        return await self._invoke_langgraph(state, audit_callback)

    @_traceable(name="JobWizardGraph._invoke_legacy", run_type="chain")
    async def _invoke_legacy(
        self,
        state: JobWizardState,
        start_node: str | None = None,
        db: AsyncSession | None = None,
        audit_callback=None,
    ) -> JobWizardState:
        """
        Run the graph to completion.

        Restores persisted state from the database at the start of each call
        (A3 — checkpoint recovery). Saves the final state at the end so the
        next call can resume from where it left off even after a process restart.

        Args:
            state: Incoming state slice (typically contains the new user_message)
            start_node: Optional starting node (defaults to START_NODE)
            db: AsyncSession for checkpoint persistence (optional — skips if None)

        Returns:
            Final state after graph execution
        """
        session_id = state.get("session_id", f"system:{uuid4()}")
        company_id = state.get("company_id")

        # A3 — restore prior state so accumulated job data survives restarts
        if db is not None:
            prior = await restore_checkpoint(db, session_id, "job_wizard")
            if prior:
                self.logger.info(f"Checkpoint restored for session {session_id}")
                # Merge: incoming state is the base; prior preserved fields fill in gaps
                # Ephemeral fields (user_message, session_id) come from incoming state
                merged = {**state, **{k: v for k, v in prior.items() if k not in EPHEMERAL_FIELDS}}
                state = merged  # type: ignore[assignment]

        execution_id = str(uuid4())
        start_time = datetime.utcnow()

        execution_log = GraphExecutionLog(
            session_id=session_id,
            execution_id=execution_id,
            start_time=start_time,
            nodes_visited=[],
            reasoning_steps=[],
        )

        current_node = start_node or self.START_NODE
        iteration = 0

        if audit_callback:
            audit_callback.on_chain_start_manual()

        self.logger.info(f"[JobWizardGraph] Starting graph execution (legado): {execution_id}")

        try:
            async with asyncio.timeout(120):
                while current_node != self.END_NODE and iteration < self.MAX_ITERATIONS:
                    iteration += 1

                    state, duration = await self._execute_node(current_node, state, audit_callback=audit_callback)

                    execution_log.nodes_visited.append(current_node)
                    execution_log.reasoning_steps.append(ReasoningStep(
                        step_number=iteration,
                        node_name=current_node,
                        action=f"Executed {current_node}",
                        duration_ms=duration,
                    ))

                    if state.get("error"):
                        self.logger.error(f"Graph error at node {current_node}: {state['error']}")
                        break

                    current_node = self._get_next_node(current_node, state)
                    self.logger.debug(f"Next node: {current_node}")

        except TimeoutError:
            self.logger.error("JobWizardGraph timeout após 120s", extra={"execution_id": execution_id})
            state["error"] = "Timeout: graph execution exceeded 120s"

        if iteration >= self.MAX_ITERATIONS:
            self.logger.warning(f"Graph reached max iterations ({self.MAX_ITERATIONS})")
            state["error"] = f"Max iterations reached ({self.MAX_ITERATIONS})"

        end_time = datetime.utcnow()
        execution_log.end_time = end_time
        execution_log.total_duration_ms = (end_time - start_time).total_seconds() * 1000
        execution_log.final_state = dict(state)
        execution_log.success = state.get("error") is None

        self._execution_logs[execution_id] = execution_log

        # A3 — persist state; delete checkpoint if wizard is complete (vaga publicada)
        if db is not None:
            wizard_done = state.get("current_stage") in ("published", "completed", "cancelled")
            if wizard_done:
                await delete_checkpoint(db, session_id, "job_wizard")
            else:
                await save_checkpoint(db, session_id, "job_wizard", dict(state), company_id)

        # E12: Event store — JobCreated event (dual write, immutable audit trail)
        try:
            _job_id = state.get("job_id") or state.get("fields", {}).get("job_id")
            _company_id_es = state.get("company_id", "")
            _user_id_es = state.get("user_id")
            _intent_es = state.get("intent", "")
            _is_confirm = _intent_es in ("confirm", "CONFIRM")
            if db is not None and _job_id and _company_id_es and _is_confirm:
                import asyncio as _asyncio

                from app.services.event_store_service import event_store_service as _es
                _asyncio.create_task(_es.append(
                    aggregate_type="job",
                    aggregate_id=str(_job_id),
                    event_type="JobCreated",
                    data={"source": "wizard"},
                    company_id=str(_company_id_es),
                    db=db,
                    created_by=str(_user_id_es) if _user_id_es else "wizard_agent",
                ))
        except Exception:
            pass

        if audit_callback:
            error = state.get("error")
            try:
                await audit_callback.on_chain_end_manual(
                    confidence=0.9 if not error else 0.3,
                    success=not bool(error),
                    error=error,
                )
            except Exception:
                pass

        self.logger.info(
            f"Graph execution complete: {execution_id} "
            f"(nodes: {len(execution_log.nodes_visited)}, "
            f"duration: {execution_log.total_duration_ms:.1f}ms)"
        )

        # E10: emit job_creation_ready to jobs_management agent when wizard completes
        try:
            _wizard_done = state.get("current_stage") in ("published", "completed")
            _company_id_val = state.get("company_id", "")
            if _wizard_done and _company_id_val:
                from lia_agents_core.agent_bus import agent_bus
                _job_id_val = state.get("job_id", "")
                asyncio.create_task(agent_bus.publish(
                    from_agent="wizard",
                    to_agent="jobs_management",
                    event_type="job_creation_ready",
                    payload={"job_id": _job_id_val, "source": "wizard_briefing"},
                    company_id=_company_id_val,
                ))
        except Exception:
            pass

        return state
    
    async def stream(
        self,
        state: JobWizardState,
        start_node: str | None = None
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Stream execution for real-time updates.
        
        Yields state updates after each node execution,
        allowing clients to receive progress updates.
        
        Args:
            state: Initial state for the graph
            start_node: Optional starting node
            
        Yields:
            Dict with node name, state update, and execution info
        """
        execution_id = str(uuid4())
        start_time = datetime.utcnow()
        
        current_node = start_node or self.START_NODE
        iteration = 0
        
        yield {
            "type": "start",
            "execution_id": execution_id,
            "start_node": current_node,
            "timestamp": start_time.isoformat()
        }
        
        while current_node != self.END_NODE and iteration < self.MAX_ITERATIONS:
            iteration += 1
            
            yield {
                "type": "node_start",
                "node": current_node,
                "iteration": iteration,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            state, duration = await self._execute_node(current_node, state)
            
            yield {
                "type": "node_complete",
                "node": current_node,
                "iteration": iteration,
                "duration_ms": duration,
                "state_update": {
                    "current_stage": state.get("current_stage"),
                    "intent": state.get("intent"),
                    "extracted_fields": state.get("extracted_fields"),
                    "response_text": state.get("response_text"),
                    "error": state.get("error")
                },
                "reasoning_steps": state.get("reasoning_steps", [])[-3:],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if state.get("error"):
                yield {
                    "type": "error",
                    "node": current_node,
                    "error": state["error"],
                    "timestamp": datetime.utcnow().isoformat()
                }
                break
            
            current_node = self._get_next_node(current_node, state)
        
        end_time = datetime.utcnow()
        total_duration = (end_time - start_time).total_seconds() * 1000
        
        yield {
            "type": "complete",
            "execution_id": execution_id,
            "total_iterations": iteration,
            "total_duration_ms": total_duration,
            "final_state": {
                "current_stage": state.get("current_stage"),
                "job_draft": state.get("job_draft"),
                "response_text": state.get("response_text"),
                "reasoning_steps": state.get("reasoning_steps"),
                "error": state.get("error")
            },
            "timestamp": end_time.isoformat()
        }
    
    def get_execution_log(self, execution_id: str) -> GraphExecutionLog | None:
        """Get the execution log for a specific run."""
        return self._execution_logs.get(execution_id)

    def get_graph_structure(self) -> dict[str, Any]:
        """Get a description of the graph structure for visualization."""
        return {
            "nodes": list(self.edges.keys()) + [self.END_NODE],
            "edges": self.edges,
            "conditional_edges": {
                node: [
                    {
                        "target": edge.target_node,
                        "has_condition": edge.condition is not None,
                        "priority": edge.priority
                    }
                    for edge in edges
                ]
                for node, edges in self.conditional_edges.items()
            },
            "start_node": self.START_NODE,
            "end_node": self.END_NODE,
            "max_iterations": self.MAX_ITERATIONS
        }


job_wizard_graph = JobWizardGraph()
