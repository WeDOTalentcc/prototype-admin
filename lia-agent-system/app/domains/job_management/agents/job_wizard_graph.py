"""
Job Wizard Graph - LangGraph-style State Machine.

Implements a directed graph where nodes are processing steps and
edges define the flow between them. Supports conditional routing,
streaming execution, and state persistence.
"""
import logging
import asyncio
import time
from typing import Dict, List, Any, Optional, Callable, AsyncIterator, Tuple
from datetime import datetime
from uuid import uuid4
from dataclasses import dataclass

try:
    from langsmith import traceable as _traceable
except ImportError:
    def _traceable(**kwargs):  # type: ignore[misc]
        def decorator(fn):
            return fn
        return decorator

from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.agents.state_machine import (
    JobWizardState,
    WizardStage,
    WizardIntent,
    GraphExecutionLog,
    ReasoningStep,
    create_initial_state,
)
from app.agents.nodes import JobWizardNodes, job_wizard_nodes
from app.tools import initialize_tools
from app.services.checkpoint_service import save_checkpoint, restore_checkpoint, delete_checkpoint

logger = logging.getLogger(__name__)

# B2 — campos efêmeros excluídos do merge de checkpoint (estado da sessão atual)
EPHEMERAL_FIELDS: frozenset = frozenset({"user_message", "session_id", "execution_id"})

_tools_initialized = False


@dataclass
class EdgeCondition:
    """Condition for a graph edge."""
    target_node: str
    condition: Optional[Callable[[JobWizardState], bool]] = None
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
    
    def __init__(self, nodes: Optional[JobWizardNodes] = None):
        global _tools_initialized
        if not _tools_initialized:
            initialize_tools()
            _tools_initialized = True
            logger.info("Tools initialized for JobWizardGraph")
        
        self.nodes = nodes or job_wizard_nodes
        self.edges = self._build_edges()
        self.conditional_edges = self._build_conditional_edges()
        self.logger = logging.getLogger(self.__class__.__name__)
        self._execution_logs: Dict[str, GraphExecutionLog] = {}
        self._compiled_lg: Optional[Any] = None  # LangGraph compiled graph (lazy init)
    
    def _build_edges(self) -> Dict[str, List[str]]:
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
    
    def _build_conditional_edges(self) -> Dict[str, List[EdgeCondition]]:
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
        from langgraph.graph import StateGraph, END as LEND
        from app.shared.agents.checkpointer import get_checkpointer

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

        session_id = state.get("session_id", str(uuid4()))
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
            from app.shared.agents.state_machine import WizardIntent
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
        start_node: Optional[str] = None,
        db: Optional[AsyncSession] = None,
        audit_callback=None,
    ) -> JobWizardState:
        """Invoca o grafo via LangGraph nativo (PostgresSaver gerencia checkpoints).

        Os parâmetros `start_node` e `db` são mantidos por compatibilidade de assinatura
        mas não são utilizados — o LangGraph StateGraph gerencia o fluxo e checkpoints.
        """
        return await self._invoke_langgraph(state, audit_callback)

    def get_execution_log(self, execution_id: str) -> Optional[GraphExecutionLog]:
        """Get the execution log for a specific run."""
        return self._execution_logs.get(execution_id)

    def get_graph_structure(self) -> Dict[str, Any]:
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
