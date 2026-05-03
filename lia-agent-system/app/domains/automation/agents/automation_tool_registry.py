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
from lia_agents_core.tool_adapter import ToolOutput

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
    """Decompose a complex task into subtasks using LLM + PlannedTaskService."""
    from app.core.database import AsyncSessionLocal
    from app.domains.automation.services.planned_task_service import PlannedTaskService
    from app.models.planned_task import PlannedTaskPriority
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
    """Recalculate priority scores for tasks."""
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
    """Generate an execution plan with parallel levels."""
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
    """Build and validate a DAG from task dependencies."""
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
    """Check dependency status for a task."""
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
    """Get tasks ready for execution."""
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
            description="Decompor uma tarefa complexa em subtarefas usando IA. Parâmetros: task_description (str, obrigatório), goal_id (str, opcional), company_id (str, opcional), persist (bool, padrão True).",
            output_schema=ToolOutput,
            function=_wrap_decompose_task,
        ),
        ToolDefinition(
            name="prioritize_tasks",
            description="Calcular e atualizar prioridades de tarefas. Parâmetros: task_ids (list[str]) ou goal_id (str).",
            output_schema=ToolOutput,
            function=_wrap_prioritize_tasks,
        ),
        ToolDefinition(
            name="get_execution_plan",
            description="Gerar plano de execução com níveis paralelos. Parâmetros: task_ids (list[str]) ou goal_id (str), name (str, opcional).",
            output_schema=ToolOutput,
            function=_wrap_get_execution_plan,
        ),
        ToolDefinition(
            name="build_dag",
            description="Construir e validar DAG de dependências. Parâmetros: task_ids (list[str]).",
            output_schema=ToolOutput,
            function=_wrap_build_dag,
        ),
        ToolDefinition(
            name="check_dependencies",
            description="Verificar status das dependências de uma tarefa. Parâmetros: task_id (str).",
            output_schema=ToolOutput,
            function=_wrap_check_dependencies,
        ),
        ToolDefinition(
            name="get_next_tasks",
            description="Obter próximas tarefas prontas para execução. Parâmetros: goal_id (str, opcional), agent_type (str, opcional), limit (int, padrão 5).",
            output_schema=ToolOutput,
            function=_wrap_get_next_tasks,
        ),
    ]


def get_stage_tools(stage: str) -> list[ToolDefinition]:
    """Return tools available for a given stage."""
    from app.domains.automation.agents.automation_stage_context import get_stage_tools as _stage_tools
    stage_tool_names = set(_stage_tools(stage))
    return [t for t in get_automation_tools() if t.name in stage_tool_names]
