"""Planned Task Service - Business logic for task planning and DAG execution.

This service handles:
- Creating and managing planned tasks
- Building DAG from task dependencies
- Topological sorting for execution order
- Cycle detection
- Priority calculation
- Execution plan generation

Refactored per ADR-001: SQL access delegated to PlannedTaskRepository.
"""
import logging
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.automation.repositories.planned_task_repository import (
    PlannedTaskRepository,
)
from lia_models.planned_task import (
    ExecutionPlan,
    PlannedTask,
    PlannedTaskPriority,
    PlannedTaskStatus,
)

logger = logging.getLogger(__name__)


class CycleDetectedError(Exception):
    """Raised when a cycle is detected in the task DAG."""
    pass


class PlannedTaskService:
    """Service for managing planned tasks with DAG support."""

    PRIORITY_WEIGHTS = {
        "deadline_urgency": 0.30,
        "dependents_impact": 0.25,
        "goal_criticality": 0.25,
        "effort_efficiency": 0.20,
    }

    async def create_planned_task(
        self,
        db: AsyncSession,
        title: str,
        description: str | None = None,
        agent_type: str | None = None,
        priority: PlannedTaskPriority = PlannedTaskPriority.MEDIUM,
        parent_task_id: str | None = None,
        dependencies: list[str] | None = None,
        estimated_duration: int | None = None,
        deadline: datetime | None = None,
        goal_id: str | None = None,
        goal_criticality: float = 0.5,
        related_job_id: str | None = None,
        related_candidate_id: str | None = None,
        company_id: str | None = None,
        context: dict[str, Any] | None = None,
        created_by: str | None = None,
        chain_of_thought: list[str] | None = None
    ) -> PlannedTask:
        """Create a new planned task."""
        # R-019 P0: company_id must come from JWT — validated by the API layer.
        # Belt-and-suspenders runtime guard here too.
        if not company_id:
            raise ValueError(
                "company_id is required (R-019 P0: must come from JWT, never from request body)"
            )
        task = PlannedTask(
            title=title,
            description=description,
            agent_type=agent_type,
            priority=priority,
            parent_task_id=parent_task_id,
            dependencies=dependencies or [],
            estimated_duration=estimated_duration,
            deadline=deadline,
            goal_id=goal_id,
            goal_criticality=goal_criticality,
            related_job_id=related_job_id,
            related_candidate_id=related_candidate_id,
            company_id=company_id,
            context=context or {},
            created_by=created_by,
            chain_of_thought=chain_of_thought or []
        )

        repo = PlannedTaskRepository(db)
        await repo.add(task)

        logger.info(f"Created planned task: {task.id} - {title}")

        return task

    async def create_subtasks(
        self,
        db: AsyncSession,
        parent_task_id: str,
        subtasks_data: list[dict[str, Any]],
        company_id: str | None = None,
        created_by: str | None = None
    ) -> list[PlannedTask]:
        """Create multiple subtasks for a parent task."""
        created_tasks = []

        for subtask_data in subtasks_data:
            task = await self.create_planned_task(
                db=db,
                title=subtask_data.get("title"),
                description=subtask_data.get("description"),
                agent_type=subtask_data.get("agent_type"),
                priority=PlannedTaskPriority(subtask_data.get("priority", "medium")),
                parent_task_id=parent_task_id,
                dependencies=subtask_data.get("dependencies", []),
                estimated_duration=subtask_data.get("estimated_duration"),
                deadline=subtask_data.get("deadline"),
                goal_id=subtask_data.get("goal_id"),
                goal_criticality=subtask_data.get("goal_criticality", 0.5),
                company_id=company_id,
                context=subtask_data.get("context", {}),
                created_by=created_by
            )
            created_tasks.append(task)

        return created_tasks

    async def get_task(self, db: AsyncSession, task_id: str) -> PlannedTask | None:
        """Get a planned task by ID."""
        repo = PlannedTaskRepository(db)
        return await repo.get_by_id(task_id)

    async def get_tasks_by_goal(
        self,
        db: AsyncSession,
        goal_id: str,
        include_completed: bool = False
    ) -> list[PlannedTask]:
        """Get all tasks for a specific goal."""
        repo = PlannedTaskRepository(db)
        return await repo.list_by_goal(goal_id, include_completed=include_completed)

    async def get_subtasks(
        self,
        db: AsyncSession,
        parent_task_id: str
    ) -> list[PlannedTask]:
        """Get all subtasks of a parent task."""
        repo = PlannedTaskRepository(db)
        return await repo.list_subtasks(parent_task_id)

    async def update_task_status(
        self,
        db: AsyncSession,
        task_id: str,
        status: PlannedTaskStatus,
        result: dict[str, Any] | None = None,
        error_message: str | None = None
    ) -> PlannedTask | None:
        """Update task status."""
        repo = PlannedTaskRepository(db)
        task = await repo.get_by_id(task_id)
        if not task:
            return None

        task.status = status
        task.updated_at = datetime.utcnow()

        if status == PlannedTaskStatus.IN_PROGRESS:
            task.started_at = datetime.utcnow()
        elif status == PlannedTaskStatus.COMPLETED:
            task.completed_at = datetime.utcnow()
            if task.started_at:
                task.actual_duration = int(
                    (task.completed_at - task.started_at).total_seconds() / 60
                )
            task.result = result
        elif status == PlannedTaskStatus.FAILED:
            task.error_message = error_message

        await repo.commit_refresh(task)

        logger.info(f"Updated task {task_id} status to {status.value}")

        return task

    def _detect_cycle(
        self,
        tasks: list[PlannedTask]
    ) -> tuple[bool, list[str] | None]:
        """Detect cycles in the task dependency graph using DFS."""
        task_map = {task.id: task for task in tasks}

        WHITE, GRAY, BLACK = 0, 1, 2
        color = {task.id: WHITE for task in tasks}
        parent = {}

        def dfs(task_id: str) -> list[str] | None:
            color[task_id] = GRAY

            task = task_map.get(task_id)
            if task and task.dependencies:
                for dep_id in task.dependencies:
                    if dep_id not in task_map:
                        continue

                    if color.get(dep_id) == GRAY:
                        cycle = [dep_id, task_id]
                        current = task_id
                        while parent.get(current) and parent[current] != dep_id:
                            current = parent[current]
                            cycle.append(current)
                        return cycle

                    if color.get(dep_id) == WHITE:
                        parent[dep_id] = task_id
                        result = dfs(dep_id)
                        if result:
                            return result

            color[task_id] = BLACK
            return None

        for task in tasks:
            if color[task.id] == WHITE:
                cycle = dfs(task.id)
                if cycle:
                    return True, cycle

        return False, None

    def _topological_sort(
        self,
        tasks: list[PlannedTask]
    ) -> list[list[PlannedTask]]:
        """Perform topological sort and group tasks by execution level."""
        task_map = {task.id: task for task in tasks}

        in_degree = {task.id: 0 for task in tasks}
        for task in tasks:
            if task.dependencies:
                for dep_id in task.dependencies:
                    if dep_id in task_map:
                        in_degree[task.id] += 1

        levels = []
        remaining = set(task.id for task in tasks)

        while remaining:
            current_level = []
            for task_id in list(remaining):
                if in_degree[task_id] == 0:
                    current_level.append(task_map[task_id])

            if not current_level:
                logger.error("Topological sort failed - remaining tasks with dependencies")
                break

            for task in current_level:
                remaining.remove(task.id)
                for other_task in tasks:
                    if other_task.dependencies and task.id in other_task.dependencies:
                        in_degree[other_task.id] -= 1

            levels.append(current_level)

        return levels

    async def build_task_dag(
        self,
        db: AsyncSession,
        task_ids: list[str]
    ) -> dict[str, Any]:
        """Build a DAG from task dependencies."""
        repo = PlannedTaskRepository(db)
        tasks = await repo.list_by_ids(task_ids)

        has_cycle, cycle_path = self._detect_cycle(tasks)

        if has_cycle:
            return {
                "has_cycle": True,
                "cycle_path": cycle_path,
                "execution_levels": [],
                "total_tasks": len(tasks),
                "error": "Ciclo detectado no grafo de dependencias"
            }

        execution_levels = self._topological_sort(tasks)

        for level_idx, level_tasks in enumerate(execution_levels):
            for task in level_tasks:
                task.execution_level = level_idx

        await repo.commit()

        return {
            "has_cycle": False,
            "cycle_path": None,
            "execution_levels": [
                [task.to_dict() for task in level]
                for level in execution_levels
            ],
            "total_tasks": len(tasks),
            "level_count": len(execution_levels)
        }

    def _calculate_deadline_urgency(
        self,
        deadline: datetime | None,
        now: datetime | None = None
    ) -> float:
        """Calculate urgency score based on deadline proximity."""
        if not deadline:
            return 0.3

        now = now or datetime.utcnow()

        if deadline < now:
            return 1.0

        hours_until_deadline = (deadline - now).total_seconds() / 3600

        if hours_until_deadline <= 4:
            return 1.0
        elif hours_until_deadline <= 24:
            return 0.9
        elif hours_until_deadline <= 48:
            return 0.7
        elif hours_until_deadline <= 72:
            return 0.5
        elif hours_until_deadline <= 168:
            return 0.3
        else:
            return 0.1

    def _calculate_dependents_impact(
        self,
        task: PlannedTask,
        all_tasks: list[PlannedTask]
    ) -> float:
        """Calculate impact score based on number of dependent tasks."""
        dependents_count = task.get_dependents_count(all_tasks)

        if dependents_count == 0:
            return 0.1
        elif dependents_count == 1:
            return 0.3
        elif dependents_count <= 3:
            return 0.6
        elif dependents_count <= 5:
            return 0.8
        else:
            return 1.0

    def _calculate_effort_efficiency(
        self,
        estimated_duration: int | None
    ) -> float:
        """Calculate efficiency score based on effort."""
        if not estimated_duration:
            return 0.5

        if estimated_duration <= 15:
            return 1.0
        elif estimated_duration <= 30:
            return 0.8
        elif estimated_duration <= 60:
            return 0.6
        elif estimated_duration <= 120:
            return 0.4
        else:
            return 0.2

    async def calculate_priority_score(
        self,
        db: AsyncSession,
        task: PlannedTask,
        all_tasks: list[PlannedTask] | None = None
    ) -> float:
        """Calculate weighted priority score for a task."""
        if all_tasks is None:
            repo = PlannedTaskRepository(db)
            all_tasks = await repo.list_for_priority_context(
                goal_id=task.goal_id,
                parent_task_id=task.parent_task_id,
            )

        deadline_urgency = self._calculate_deadline_urgency(task.deadline)
        dependents_impact = self._calculate_dependents_impact(task, all_tasks)
        goal_criticality = task.goal_criticality or 0.5
        effort_efficiency = self._calculate_effort_efficiency(task.estimated_duration)

        score = (
            deadline_urgency * self.PRIORITY_WEIGHTS["deadline_urgency"] +
            dependents_impact * self.PRIORITY_WEIGHTS["dependents_impact"] +
            goal_criticality * self.PRIORITY_WEIGHTS["goal_criticality"] +
            effort_efficiency * self.PRIORITY_WEIGHTS["effort_efficiency"]
        )

        return round(score, 4)

    async def reprioritize_tasks(
        self,
        db: AsyncSession,
        task_ids: list[str]
    ) -> list[PlannedTask]:
        """Recalculate priority scores for a set of tasks."""
        repo = PlannedTaskRepository(db)
        tasks = await repo.list_by_ids(task_ids)

        for task in tasks:
            task.priority_score = await self.calculate_priority_score(db, task, tasks)

        await repo.commit()

        for task in tasks:
            await repo.refresh(task)

        logger.info(f"Reprioritized {len(tasks)} tasks")

        return sorted(tasks, key=lambda t: t.priority_score, reverse=True)

    async def get_next_tasks(
        self,
        db: AsyncSession,
        goal_id: str | None = None,
        parent_task_id: str | None = None,
        company_id: str | None = None,
        agent_type: str | None = None,
        limit: int = 5
    ) -> list[PlannedTask]:
        """Get the next tasks that are ready to execute."""
        repo = PlannedTaskRepository(db)
        all_candidates = await repo.list_ready_candidates(
            goal_id=goal_id,
            parent_task_id=parent_task_id,
            company_id=company_id,
            agent_type=agent_type,
        )

        completed_ids = await repo.list_completed_ids()

        ready_tasks = [
            task for task in all_candidates
            if task.is_ready_to_execute(completed_ids)
        ]

        for task in ready_tasks:
            if task.status == PlannedTaskStatus.PENDING:
                task.status = PlannedTaskStatus.READY

        await repo.commit()

        sorted_tasks = sorted(
            ready_tasks,
            key=lambda t: (t.priority_score or 0),
            reverse=True
        )

        return sorted_tasks[:limit]

    async def create_execution_plan(
        self,
        db: AsyncSession,
        name: str,
        task_ids: list[str],
        description: str | None = None,
        goal_id: str | None = None,
        company_id: str | None = None,
        created_by: str | None = None
    ) -> ExecutionPlan:
        """Create an execution plan from a set of tasks."""
        # R-019 P0: company_id must come from JWT — validated by API layer.
        if not company_id:
            raise ValueError(
                "company_id is required (R-019 P0: must come from JWT, never from request body)"
            )
        dag_result = await self.build_task_dag(db, task_ids)

        if dag_result["has_cycle"]:
            raise CycleDetectedError(
                f"Ciclo detectado: {' -> '.join(dag_result['cycle_path'])}"
            )

        repo = PlannedTaskRepository(db)
        tasks = await repo.list_by_ids(task_ids)

        total_duration = sum(t.estimated_duration or 0 for t in tasks)

        max_level_duration = 0
        for level_tasks in dag_result["execution_levels"]:
            level_duration = max(
                (t.get("estimated_duration") or 0) for t in level_tasks
            ) if level_tasks else 0
            max_level_duration += level_duration

        plan = ExecutionPlan(
            name=name,
            description=description,
            goal_id=goal_id,
            task_ids=task_ids,
            execution_levels=dag_result["execution_levels"],
            total_estimated_duration=total_duration,
            parallel_execution_time=max_level_duration,
            company_id=company_id,
            created_by=created_by,
            plan_metadata={
                "level_count": dag_result["level_count"],
                "total_tasks": dag_result["total_tasks"]
            }
        )

        await repo.add(plan)

        logger.info(f"Created execution plan: {plan.id} with {len(task_ids)} tasks")

        return plan

    async def get_execution_plan(
        self,
        db: AsyncSession,
        plan_id: str
    ) -> ExecutionPlan | None:
        """Get an execution plan by ID."""
        repo = PlannedTaskRepository(db)
        return await repo.get_execution_plan(plan_id)

    async def check_dependencies(
        self,
        db: AsyncSession,
        task_id: str
    ) -> dict[str, Any]:
        """Check the dependency status for a task."""
        repo = PlannedTaskRepository(db)
        task = await repo.get_by_id(task_id)
        if not task:
            return {"error": "Task not found", "task_id": task_id}

        if not task.dependencies:
            return {
                "task_id": task_id,
                "all_satisfied": True,
                "dependencies": [],
                "blocking_count": 0
            }

        dep_tasks = await repo.list_by_ids(task.dependencies)

        dep_statuses = []
        blocking_count = 0

        for dep_id in task.dependencies:
            dep_task = next((t for t in dep_tasks if t.id == dep_id), None)

            if dep_task:
                is_satisfied = dep_task.status == PlannedTaskStatus.COMPLETED
                if not is_satisfied:
                    blocking_count += 1

                dep_statuses.append({
                    "task_id": dep_id,
                    "title": dep_task.title,
                    "status": dep_task.status.value,
                    "is_satisfied": is_satisfied
                })
            else:
                dep_statuses.append({
                    "task_id": dep_id,
                    "title": "Unknown",
                    "status": "not_found",
                    "is_satisfied": False
                })
                blocking_count += 1

        return {
            "task_id": task_id,
            "all_satisfied": blocking_count == 0,
            "dependencies": dep_statuses,
            "blocking_count": blocking_count
        }

    async def add_chain_of_thought(
        self,
        db: AsyncSession,
        task_id: str,
        thought: str,
        thought_type: str = "reasoning"
    ) -> PlannedTask | None:
        """Add a chain-of-thought entry to a task."""
        repo = PlannedTaskRepository(db)
        task = await repo.get_by_id(task_id)
        if not task:
            return None

        cot_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": thought_type,
            "thought": thought
        }

        if task.chain_of_thought is None:
            task.chain_of_thought = []

        task.chain_of_thought = task.chain_of_thought + [cot_entry]
        task.updated_at = datetime.utcnow()

        await repo.commit_refresh(task)

        return task


planned_task_service = PlannedTaskService()
