"""Automation ReAct Agent — Tool Registry.

Wraps PlannedTaskService + LLMService operations into ToolDefinition format
so the ReActLoop can autonomously decide which tools to call.
"""
import json
import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from lia_agents_core.react_loop import ToolDefinition

from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool wrappers
# ---------------------------------------------------------------------------

TASK_DECOMPOSITION_PROMPT = """Você é um especialista em planejamento e decomposição de tarefas para recrutamento.

## Tarefa Principal:
{task_description}

## Contexto Adicional:
{context}

## Instruções:
Decomponha esta tarefa em subtarefas menores e executáveis. Para cada subtarefa:
1. **Identificar subtarefas**: Liste todas as ações necessárias
2. **Estimar duração**: Em minutos (5min a 120min)
3. **Definir dependências**: Quais subtarefas dependem de outras?
4. **Atribuir agente**: job_planner | sourcing | cv_screening | interviewer | wsi_evaluator | scheduling | analyst_feedback
5. **Prioridade**: critical, high, medium, low

## Formato de Resposta (JSON):
{{
    "main_task_summary": "Resumo",
    "subtasks": [
        {{
            "id": "temp_1",
            "title": "Título",
            "description": "Descrição",
            "agent_type": "job_planner",
            "priority": "high",
            "estimated_duration": 30,
            "dependencies": [],
            "goal_criticality": 0.8
        }}
    ],
    "execution_notes": "Observações",
    "estimated_total_duration": 90,
    "parallel_opportunities": ["temp_3 e temp_4 podem executar em paralelo"]
}}

Responda APENAS com o JSON válido."""

PRIORITY_ANALYSIS_PROMPT = """Você é um especialista em priorização de tarefas de recrutamento.

## Tarefas para Priorizar:
{tasks_json}

## Contexto:
{context}

## Critérios (pesos): Urgência 30% | Impacto 25% | Criticidade 25% | Eficiência 20%

## Responda com JSON:
{{
    "prioritized_tasks": [
        {{
            "task_id": "id",
            "priority_score": 0.85,
            "reasoning": "Justificativa",
            "recommended_priority": "high"
        }}
    ],
    "execution_recommendation": "Sugestão de ordem",
    "quick_wins": ["IDs de tarefas rápidas que desbloqueiam outras"]
}}

Responda APENAS com JSON válido."""


@tool_handler("automation")
async def _wrap_decompose_task(**kwargs: Any) -> dict[str, Any]:
    """Decompose a complex recruitment or workflow task into executable subtasks via LLM.

    Uses a structured planning prompt to assign agent types, priorities, estimated
    durations, and dependency chains. Persists results to PlannedTaskService by default.
    Side effects: db_write, credits_consumed
    Governance: multi_tenant, audit_trail
    Use before: prioritize_tasks, get_execution_plan
    """
    from app.core.database import AsyncSessionLocal
    from app.domains.automation.services.planned_task_service import PlannedTaskService
    from lia_models.planned_task import PlannedTaskPriority
    from app.domains.ai.services.llm import LLMService

    task_description = kwargs.get("task_description") or kwargs.get("description", "")
    company_id = kwargs.get("company_id")
    created_by = kwargs.get("user_id")
    goal_id = kwargs.get("goal_id")
    parent_task_id = kwargs.get("parent_task_id")
    deadline = kwargs.get("deadline")
    persist = kwargs.get("persist", True)

    if not task_description:
        return {"success": False, "message": "task_description é obrigatório"}

    context_str = json.dumps(
        {"goal_id": goal_id, "company_id": company_id, "deadline": str(deadline) if deadline else None},
        ensure_ascii=False,
    )

    try:
        llm = LLMService()
        llm_response = await llm.generate_json(
            prompt=TASK_DECOMPOSITION_PROMPT.format(
                task_description=task_description, context=context_str
            ),
            system_message="Você é um especialista em planejamento. Responda APENAS com JSON válido.",
        )
        if isinstance(llm_response, str):
            llm_response = json.loads(llm_response)

        subtasks_data = llm_response.get("subtasks", [])
        if not subtasks_data:
            return {"success": False, "message": "LLM não retornou subtarefas"}

        if not persist:
            return {
                "success": True,
                "subtasks": subtasks_data,
                "execution_notes": llm_response.get("execution_notes"),
                "estimated_total_duration": llm_response.get("estimated_total_duration"),
                "parallel_opportunities": llm_response.get("parallel_opportunities", []),
                "persisted": False,
            }

        svc = PlannedTaskService()
        temp_id_map: dict[str, str] = {}
        created_tasks = []

        async with AsyncSessionLocal() as db:
            for subtask in subtasks_data:
                temp_id = subtask.get("id", f"temp_{uuid4().hex[:8]}")
                real_deps = [
                    temp_id_map[dep]
                    for dep in subtask.get("dependencies", [])
                    if dep in temp_id_map
                ]
                task = await svc.create_planned_task(
                    db=db,
                    title=subtask.get("title"),
                    description=subtask.get("description"),
                    agent_type=subtask.get("agent_type"),
                    priority=PlannedTaskPriority(subtask.get("priority", "medium")),
                    parent_task_id=parent_task_id,
                    dependencies=real_deps,
                    estimated_duration=subtask.get("estimated_duration"),
                    deadline=deadline if isinstance(deadline, datetime) else None,
                    goal_id=goal_id,
                    goal_criticality=subtask.get("goal_criticality", 0.5),
                    company_id=company_id,
                    created_by=created_by,
                )
                temp_id_map[temp_id] = task.id
                created_tasks.append(task)

            task_ids = [t.id for t in created_tasks]
            await svc.reprioritize_tasks(db, task_ids)
            dag_result = await svc.build_task_dag(db, task_ids)
            await db.commit()

        return {
            "success": True,
            "subtasks_created": len(created_tasks),
            "subtasks": [t.to_dict() for t in created_tasks],
            "dag": dag_result,
            "execution_notes": llm_response.get("execution_notes"),
            "estimated_total_duration": llm_response.get("estimated_total_duration"),
            "parallel_opportunities": llm_response.get("parallel_opportunities", []),
        }

    except json.JSONDecodeError as e:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.error(f"[automation_tools] LLM JSON parse error: {e}")
        return {"success": False, "message": f"Erro ao parsear resposta da IA: {e}"}
    except Exception as e:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.error(f"[automation_tools] decompose_task error: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


@tool_handler("automation")
async def _wrap_prioritize_tasks(**kwargs: Any) -> dict[str, Any]:
    """Recalculate and update priority scores for planned tasks using multi-criteria scoring.

    Criteria weights: urgency 30%, impact 25%, criticality 25%, efficiency 20%.
    Writes updated priority values back to planned_tasks table.
    Side effects: db_write
    Governance: multi_tenant, audit_trail
    Use after: decompose_task; use before: get_execution_plan
    """
    from app.core.database import AsyncSessionLocal
    from app.domains.automation.services.planned_task_service import PlannedTaskService

    task_ids = kwargs.get("task_ids", [])
    goal_id = kwargs.get("goal_id")

    svc = PlannedTaskService()
    async with AsyncSessionLocal() as db:
        if goal_id and not task_ids:
            tasks = await svc.get_tasks_by_goal(db, goal_id)
            task_ids = [t.id for t in tasks]

        if not task_ids:
            return {"success": False, "message": "Forneça task_ids ou goal_id"}

        prioritized = await svc.reprioritize_tasks(db, task_ids)

    return {
        "success": True,
        "prioritized_count": len(prioritized),
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "priority": t.priority.value,
                "priority_score": t.priority_score,
                "status": t.status.value,
            }
            for t in prioritized
        ],
    }
@tool_handler("automation")
async def _wrap_get_execution_plan(**kwargs: Any) -> dict[str, Any]:
    """Generate a structured execution plan with parallel levels from a set of planned tasks.

    Validates the dependency DAG for cycles and persists the plan to the database.
    Returns the plan with its parallel execution levels and any cycle warnings.
    Side effects: db_write
    Governance: multi_tenant, audit_trail
    Use after: decompose_task, prioritize_tasks; use before: dispatching specialist agents
    """
    from app.core.database import AsyncSessionLocal
    from app.domains.automation.services.planned_task_service import CycleDetectedError, PlannedTaskService

    task_ids = kwargs.get("task_ids", [])
    goal_id = kwargs.get("goal_id")
    plan_name = kwargs.get("name", f"Plano - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    company_id = kwargs.get("company_id")
    created_by = kwargs.get("user_id")

    try:
        svc = PlannedTaskService()
        async with AsyncSessionLocal() as db:
            if goal_id and not task_ids:
                tasks = await svc.get_tasks_by_goal(db, goal_id)
                task_ids = [t.id for t in tasks]

            if not task_ids:
                return {"success": False, "message": "Forneça task_ids ou goal_id"}

            dag = await svc.build_task_dag(db, task_ids)
            if dag.get("has_cycle"):
                return {
                    "success": False,
                    "has_cycle": True,
                    "cycle_path": dag.get("cycle_path", []),
                    "message": "Ciclo detectado nas dependências",
                }

            plan = await svc.create_execution_plan(
                db=db,
                name=plan_name,
                task_ids=task_ids,
                goal_id=goal_id,
                company_id=company_id,
                created_by=created_by,
            )
            return {"success": True, "plan": plan.to_dict(), "dag": dag}

    except CycleDetectedError as e:
        return {"success": False, "has_cycle": True, "message": str(e)}
@tool_handler("automation")
async def _wrap_build_dag(**kwargs: Any) -> dict[str, Any]:
    """Build and validate a Directed Acyclic Graph (DAG) from a list of task dependencies.

    Detects cycles and computes topological execution levels. Read-only — does not persist.
    Side effects: none
    Governance: multi_tenant
    Use before: get_execution_plan (for cycle-free validation)
    """
    from app.core.database import AsyncSessionLocal
    from app.domains.automation.services.planned_task_service import PlannedTaskService

    task_ids = kwargs.get("task_ids", [])
    if not task_ids:
        return {"success": False, "message": "Forneça task_ids"}

    svc = PlannedTaskService()
    async with AsyncSessionLocal() as db:
        result = await svc.build_task_dag(db, task_ids)
    return {"success": True, **result}
@tool_handler("automation")
async def _wrap_check_dependencies(**kwargs: Any) -> dict[str, Any]:
    """Check the dependency completion status for a specific planned task.

    Returns which prerequisite tasks are done, pending, or blocked.
    Use to determine if a task is ready to start before dispatching it.
    Side effects: none (read-only)
    Governance: multi_tenant
    Use before: dispatching any specialist agent; see also: get_next_tasks
    """
    from app.core.database import AsyncSessionLocal
    from app.domains.automation.services.planned_task_service import PlannedTaskService

    task_id = kwargs.get("task_id")
    if not task_id:
        return {"success": False, "message": "Forneça task_id"}

    svc = PlannedTaskService()
    async with AsyncSessionLocal() as db:
        result = await svc.check_dependencies(db, task_id)
    return {"success": True, **result}
@tool_handler("automation")
async def _wrap_get_next_tasks(**kwargs: Any) -> dict[str, Any]:
    """Return planned tasks that are ready for execution (all dependencies completed).

    Filtered by goal, agent type, and company. Drive the autonomous execution loop —
    call repeatedly to pick up tasks as dependencies complete.
    Side effects: none (read-only)
    Governance: multi_tenant
    Poll pattern: call after each completed task to discover newly unblocked tasks.
    """
    from app.core.database import AsyncSessionLocal
    from app.domains.automation.services.planned_task_service import PlannedTaskService

    svc = PlannedTaskService()
    async with AsyncSessionLocal() as db:
        tasks = await svc.get_next_tasks(
            db=db,
            goal_id=kwargs.get("goal_id"),
            parent_task_id=kwargs.get("parent_task_id"),
            company_id=kwargs.get("company_id"),
            agent_type=kwargs.get("agent_type"),
            limit=kwargs.get("limit", 5),
        )
    return {"success": True, "tasks": [t.to_dict() for t in tasks], "count": len(tasks)}
# ---------------------------------------------------------------------------
# Public registry
# ---------------------------------------------------------------------------

def get_automation_tools() -> list[ToolDefinition]:
    return [
        ToolDefinition(
            name="decompose_task",
            description=(
                "Decomposes a complex recruitment or workflow task into executable subtasks using an LLM "
                "with a structured planning prompt. Automatically assigns agent types, priorities, estimated "
                "durations, and dependency chains. Optionally persists the subtasks to the database via "
                "PlannedTaskService. Use for any multi-step workflow that requires orchestration across "
                "multiple agents. "
                "Params: task_description (str, required), goal_id (str), company_id (str), persist (bool, default True). "
                "Side effects: db_write, credits_consumed. Governance: multi_tenant, audit_trail."
            ),
            function=_wrap_decompose_task,
        ),
        ToolDefinition(
            name="prioritize_tasks",
            description=(
                "Recalculates and updates priority scores for a list of planned tasks using multi-criteria "
                "scoring (urgency 30%, impact 25%, criticality 25%, efficiency 20%). Writes updated priority "
                "values back to the planned_tasks table. Run after decomposing tasks or when context changes "
                "(budget cut, new deadline, blocked dependency). "
                "Params: task_ids (list[str]) or goal_id (str). "
                "Side effects: db_write. Governance: multi_tenant, audit_trail."
            ),
            function=_wrap_prioritize_tasks,
        ),
        ToolDefinition(
            name="get_execution_plan",
            description=(
                "Generates a structured execution plan with parallel levels from a set of planned tasks, "
                "validates the dependency DAG for cycles, and persists the plan to the database. Returns "
                "the plan with its parallel execution levels and any cycle warnings. Use to prepare the "
                "final, validated execution schedule before starting an autonomous pipeline. "
                "Params: task_ids (list[str]) or goal_id (str), name (str, optional). "
                "Side effects: db_write. Governance: multi_tenant, audit_trail."
            ),
            function=_wrap_get_execution_plan,
        ),
        ToolDefinition(
            name="build_dag",
            description=(
                "Builds and validates a Directed Acyclic Graph (DAG) from a list of task dependencies, "
                "detecting cycles and computing topological execution levels. Read-only — does not persist "
                "anything. Use to validate a dependency graph before committing to an execution plan. "
                "Params: task_ids (list[str], required). "
                "Side effects: none. Governance: multi_tenant."
            ),
            function=_wrap_build_dag,
        ),
        ToolDefinition(
            name="check_dependencies",
            description=(
                "Checks the dependency completion status for a specific planned task, returning which "
                "prerequisite tasks are done, pending, or blocked. Use to determine if a task is ready "
                "to start before dispatching it to the appropriate specialist agent. "
                "Params: task_id (str, required). "
                "Side effects: none (read-only). Governance: multi_tenant."
            ),
            function=_wrap_check_dependencies,
        ),
        ToolDefinition(
            name="get_next_tasks",
            description=(
                "Returns the list of planned tasks ready for execution (all dependencies completed, not yet "
                "started), filtered by goal, agent type, and company. Use to drive the autonomous execution "
                "loop — call repeatedly to pick up tasks as they become available. "
                "Params: goal_id (str), parent_task_id (str), agent_type (str), limit (int, default 5). "
                "Side effects: none (read-only). Governance: multi_tenant."
            ),
            function=_wrap_get_next_tasks,
        ),
    ]


def get_stage_tools(stage: str) -> list[ToolDefinition]:
    """Return tools available for a given stage."""
    from app.domains.automation.agents.automation_stage_context import get_stage_tools as _stage_tools
    stage_tool_names = set(_stage_tools(stage))
    return [t for t in get_automation_tools() if t.name in stage_tool_names]
