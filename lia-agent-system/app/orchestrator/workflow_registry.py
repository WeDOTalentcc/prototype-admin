"""Onda 2.5 Init II.D (2026-04-21) — Workflow Registry.

Formalizes multi-turn flows (cancelamento de vaga, sourcing com filtros,
wizard de criação) so LIA knows "user is in workflow X step Y" across turns.

Complements PendingActionState (single-param collection) with broader
multi-step semantics.

Canonical-fix: registry is the single producer for workflow definitions.
Orchestrator + SystemPromptBuilder consume read-only.

v1 ships with 3 canonical workflows — extensible via register_workflow().
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

_WORKFLOW_CONTEXT_ENABLED = os.environ.get(
    "LIA_WORKFLOW_CONTEXT_ENABLED", "true"
).lower() == "true"


@dataclass
class WorkflowDefinition:
    """Static definition of a multi-turn workflow."""
    id: str
    title: str
    description: str
    steps: list[str]  # ordered step names
    terminal_steps: set[str] = field(default_factory=set)  # workflow ends here
    domain: str = "general"  # routing hint

    def next_step(self, current: str) -> str | None:
        """Return next step name after `current`, or None if at end."""
        if current not in self.steps:
            return self.steps[0] if self.steps else None
        idx = self.steps.index(current)
        if idx + 1 < len(self.steps):
            return self.steps[idx + 1]
        return None

    def is_terminal(self, step: str) -> bool:
        return step in self.terminal_steps


# ─── Registry ────────────────────────────────────────────────────────────────

_REGISTRY: dict[str, WorkflowDefinition] = {}


def register_workflow(workflow: WorkflowDefinition) -> None:
    """Register a workflow definition (idempotent — overwrites)."""
    _REGISTRY[workflow.id] = workflow


def get_workflow(workflow_id: str) -> WorkflowDefinition | None:
    return _REGISTRY.get(workflow_id)


def list_workflows() -> list[str]:
    return sorted(_REGISTRY.keys())


# ─── v1 canonical workflows ──────────────────────────────────────────────────

register_workflow(WorkflowDefinition(
    id="close_job",
    title="Encerrar ou cancelar vaga",
    description="Fluxo multi-turn para encerrar vaga com motivo canônico + "
                "confirmação (+ notificação opcional de candidatos).",
    steps=["ask_reason", "confirm", "execute", "notified"],
    terminal_steps={"notified"},
    domain="job_management",
))

register_workflow(WorkflowDefinition(
    id="sourcing_with_filters",
    title="Sourcing de candidatos com filtros",
    description="Busca multi-turn onde usuário refina filtros entre queries "
                "(skill, seniority, location) e pagina resultados.",
    steps=["initial_search", "apply_filter", "resume", "paginate", "complete"],
    terminal_steps={"complete"},
    domain="sourcing",
))

register_workflow(WorkflowDefinition(
    id="job_creation_wizard",
    title="Wizard de criação de vaga",
    description="Coleta estruturada de campos da vaga (role, skills, JD) "
                "com validação + publicação final.",
    steps=["collect_role", "collect_skills", "validate_jd", "publish", "published"],
    terminal_steps={"published"},
    domain="job_management",
))


# ─── Context helpers (ConversationState.workflow_context manipulation) ───────

def start_workflow(
    workflow_id: str,
    initial_data: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Create a workflow_context dict for ConversationState.

    Returns None if feature flag off or workflow unknown.
    """
    if not _WORKFLOW_CONTEXT_ENABLED:
        return None

    wf = get_workflow(workflow_id)
    if wf is None:
        logger.warning("Init II.D: workflow %s not registered", workflow_id)
        return None

    return {
        "workflow_id": workflow_id,
        "step": wf.steps[0] if wf.steps else "unknown",
        "data": initial_data or {},
        "started_at": datetime.utcnow().isoformat(),
    }


def advance_step(
    context: dict[str, Any],
    new_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Advance workflow_context to next step. Mutates + returns."""
    wf = get_workflow(context.get("workflow_id", ""))
    if wf is None:
        return context
    nxt = wf.next_step(context.get("step", ""))
    if nxt:
        context["step"] = nxt
    if new_data:
        context.setdefault("data", {}).update(new_data)
    return context


def is_complete(context: dict[str, Any] | None) -> bool:
    """True when workflow reached a terminal step."""
    if not context:
        return True
    wf = get_workflow(context.get("workflow_id", ""))
    if wf is None:
        return True
    return wf.is_terminal(context.get("step", ""))


def render_prompt_context(context: dict[str, Any] | None) -> str:
    """Format workflow_context as a system prompt section.

    Used by SystemPromptBuilder.build() to inject `## Fluxo em Andamento`
    block when a workflow is active.
    """
    if not context or not _WORKFLOW_CONTEXT_ENABLED:
        return ""
    wf = get_workflow(context.get("workflow_id", ""))
    if wf is None:
        return ""

    step = context.get("step", "?")
    data_keys = list((context.get("data") or {}).keys())

    lines = [
        "## Fluxo em Andamento (Init II.D)",
        f"Fluxo: **{wf.title}**",
        f"Etapa atual: `{step}` de {wf.steps}",
        f"Dados coletados: {data_keys or '(nenhum ainda)'}",
        "",
        "Continue o fluxo na etapa atual. Se o usuário desviar claramente "
        "do tópico, ofereça confirmar se quer sair do fluxo.",
    ]
    return "\n".join(lines)
