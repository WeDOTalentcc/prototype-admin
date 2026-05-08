"""
Task Planner API - Endpoints for task decomposition and planning.

Provides REST endpoints for:
- Task decomposition via LLM
- DAG building and validation
- Priority calculation
- Execution plan management
- Next tasks retrieval
"""
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from app.auth.dependencies import get_current_user_or_demo, get_user_company_id
from app.auth.models import User
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.automation.agents.automation_react_agent import AutomationReActAgent
from app.domains.automation.services.planned_task_service import CycleDetectedError, planned_task_service
from app.models.planned_task import PlannedTaskPriority, PlannedTaskStatus

router = APIRouter(prefix="/task-planner", tags=["Task Planner"])


class DecomposeTaskRequest(BaseModel):
    """Request body for task decomposition."""
    task_description: str = Field(..., description="Description of the task to decompose")
    parent_task_id: str | None = None
    goal_id: str | None = None
    deadline: datetime | None = None
    persist: bool = True
    additional_context: dict[str, Any] | None = None


class CreatePlannedTaskRequest(BaseModel):
    """Request body for creating a planned task."""
    title: str
    description: str | None = None
    agent_type: str | None = None
    priority: str = "medium"
    parent_task_id: str | None = None
    dependencies: list[str] | None = None
    estimated_duration: int | None = None
    deadline: datetime | None = None
    goal_id: str | None = None
    goal_criticality: float = 0.5
    related_job_id: str | None = None
    related_candidate_id: str | None = None
    context: dict[str, Any] | None = None


class CreateExecutionPlanRequest(BaseModel):
    """Request body for creating an execution plan."""
    name: str
    task_ids: list[str]
    description: str | None = None
    goal_id: str | None = None


class PrioritizeTasksRequest(BaseModel):
    """Request body for prioritizing tasks."""
    task_ids: list[str] | None = None
    goal_id: str | None = None
    use_llm: bool = False


class UpdateTaskStatusRequest(BaseModel):
    """Request body for updating task status."""
    status: str
    result: dict[str, Any] | None = None
    error_message: str | None = None


@router.post("/decompose", response_model=None)
async def decompose_task(
    request: DecomposeTaskRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
):
    """
    Decompose a complex task into subtasks using AI.
    
    The LLM will analyze the task description and:
    - Break it into smaller, actionable subtasks
    - Identify dependencies between subtasks
    - Estimate duration for each subtask
    - Assign appropriate agent types
    """
    company_id = get_user_company_id(current_user)
    agent = AutomationReActAgent()
    response = await agent.decompose_task(
        task_description=request.task_description,
        company_id=company_id,
        goal_id=request.goal_id,
        parent_task_id=request.parent_task_id,
        deadline=request.deadline,
        persist=request.persist,
        additional_context=request.additional_context,
    )

    if not response.get("success"):
        raise HTTPException(status_code=400, detail=response.get("message", "Erro ao decompor tarefa"))
    
    return {
        "success": True,
        "message": f"Tarefa decomposta em {response.get('subtasks_created', 0)} subtarefas.",
        "data": response,
    }


@router.post("/tasks", response_model=None)
async def create_planned_task(
    request: CreatePlannedTaskRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
):
    """Create a new planned task."""
    company_id = get_user_company_id(current_user)
    try:
        task = await planned_task_service.create_planned_task(
            db=db,
            title=request.title,
            description=request.description,
            agent_type=request.agent_type,
            priority=PlannedTaskPriority(request.priority),
            parent_task_id=request.parent_task_id,
            dependencies=request.dependencies,
            estimated_duration=request.estimated_duration,
            deadline=request.deadline,
            goal_id=request.goal_id,
            goal_criticality=request.goal_criticality,
            related_job_id=request.related_job_id,
            related_candidate_id=request.related_candidate_id,
            company_id=company_id,
            context=request.context
        )
        
        return {
            "success": True,
            "task": task.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks/{task_id}", response_model=None)
async def get_planned_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a planned task by ID."""
    task = await planned_task_service.get_task(db, task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task.to_dict()


@router.patch("/tasks/{task_id}/status", response_model=None)
async def update_task_status(
    task_id: str,
    request: UpdateTaskStatusRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update the status of a planned task."""
    try:
        status = PlannedTaskStatus(request.status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {request.status}"
        )
    
    task = await planned_task_service.update_task_status(
        db=db,
        task_id=task_id,
        status=status,
        result=request.result,
        error_message=request.error_message
    )
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task.to_dict()


@router.get("/tasks/{task_id}/subtasks", response_model=None)
async def get_subtasks(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all subtasks of a parent task."""
    subtasks = await planned_task_service.get_subtasks(db, task_id)
    
    return {
        "parent_task_id": task_id,
        "subtasks": [t.to_dict() for t in subtasks],
        "count": len(subtasks)
    }


@router.get("/tasks/{task_id}/dependencies", response_model=None)
async def check_task_dependencies(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Check the dependency status for a task."""
    result = await planned_task_service.check_dependencies(db, task_id)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.get("/goal/{goal_id}/tasks", response_model=None)
async def get_tasks_by_goal(
    goal_id: str,
    include_completed: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """Get all tasks for a specific goal."""
    tasks = await planned_task_service.get_tasks_by_goal(
        db, goal_id, include_completed
    )
    
    return {
        "goal_id": goal_id,
        "tasks": [t.to_dict() for t in tasks],
        "count": len(tasks)
    }


@router.post("/prioritize", response_model=None)
async def prioritize_tasks(
    request: PrioritizeTasksRequest,
    db: AsyncSession = Depends(get_db)
):
    """Recalculate priority scores for tasks."""
    agent = AutomationReActAgent()
    response = await agent.prioritize_tasks(
        task_ids=request.task_ids,
        goal_id=request.goal_id,
    )

    if not response.get("success"):
        raise HTTPException(status_code=400, detail=response.get("message", "Erro ao priorizar tarefas"))

    return {
        "success": True,
        "message": f"{response.get('prioritized_count', 0)} tarefas priorizadas.",
        "data": response,
    }


@router.post("/dag/build", response_model=None)
async def build_task_dag(
    task_ids: list[str] = Body(..., embed=True),
    db: AsyncSession = Depends(get_db)
):
    """
    Build and validate a DAG from task dependencies.
    
    Returns:
    - Cycle detection results
    - Execution levels (tasks grouped by parallel execution)
    - Topological order
    """
    result = await planned_task_service.build_task_dag(db, task_ids)
    
    if result.get("has_cycle"):
        return {
            "success": False,
            "has_cycle": True,
            "cycle_path": result["cycle_path"],
            "error": "Cycle detected in task dependencies"
        }
    
    return {
        "success": True,
        "has_cycle": False,
        "execution_levels": result["execution_levels"],
        "level_count": result["level_count"],
        "total_tasks": result["total_tasks"]
    }


@router.post("/execution-plans", response_model=None)
async def create_execution_plan(
    request: CreateExecutionPlanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
):
    """
    Create an execution plan from a set of tasks.
    
    The plan includes:
    - DAG validation
    - Execution levels for parallel processing
    - Duration estimates
    """
    company_id = get_user_company_id(current_user)
    try:
        plan = await planned_task_service.create_execution_plan(
            db=db,
            name=request.name,
            task_ids=request.task_ids,
            description=request.description,
            goal_id=request.goal_id,
            company_id=company_id
        )
        
        return {
            "success": True,
            "plan": plan.to_dict()
        }
    except CycleDetectedError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/execution-plans/{plan_id}", response_model=None)
async def get_execution_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get an execution plan by ID."""
    plan = await planned_task_service.get_execution_plan(db, plan_id)
    
    if not plan:
        raise HTTPException(status_code=404, detail="Execution plan not found")
    
    return plan.to_dict()


@router.get("/next-tasks", response_model=None)
async def get_next_tasks(
    goal_id: str | None = Query(None),
    parent_task_id: str | None = Query(None),
    agent_type: str | None = Query(None),
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
):
    """
    Get the next tasks that are ready for execution.
    
    Returns tasks that:
    1. Have all dependencies completed
    2. Are in READY or PENDING status
    3. Sorted by priority score
    """
    company_id = get_user_company_id(current_user)
    tasks = await planned_task_service.get_next_tasks(
        db=db,
        goal_id=goal_id,
        parent_task_id=parent_task_id,
        company_id=company_id,
        agent_type=agent_type,
        limit=limit
    )
    
    return {
        "tasks": [t.to_dict() for t in tasks],
        "count": len(tasks),
        "filters": {
            "goal_id": goal_id,
            "parent_task_id": parent_task_id,
            "agent_type": agent_type,
            "company_id": company_id
        }
    }


@router.post("/tasks/{task_id}/chain-of-thought", response_model=None)
async def add_chain_of_thought(
    task_id: str,
    thought: str = Body(..., embed=True),
    thought_type: str = Body("reasoning", embed=True),
    db: AsyncSession = Depends(get_db)
):
    """Add a chain-of-thought entry to a task for logging decisions."""
    task = await planned_task_service.add_chain_of_thought(
        db=db,
        task_id=task_id,
        thought=thought,
        thought_type=thought_type
    )
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "success": True,
        "task_id": task_id,
        "chain_of_thought": task.chain_of_thought
    }
