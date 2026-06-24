"""
GoalsRepository — persistence layer for goals and goal templates.
"""
import logging
import uuid
from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.goal import Goal, GoalTemplate

logger = logging.getLogger(__name__)


class GoalsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Goal queries
    # ------------------------------------------------------------------

    async def list_goals(
        self,
        user_id: str | None = None,
        company_id: uuid.UUID | None = None,
        period: str | None = None,
        category: str | None = None,
        status: str | None = None,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Goal]:
        """List goals.

        Sprint B.1 tail (2026-05-22): company_id RECOMENDADO (defense-in-depth).
        Quando passado, filtra por tenant. Caller (api/v1/goals.py) eh tenant-gated.
        """
        # TENANT-EXEMPT: dynamic builder — Goal.company_id == company_id aplicado abaixo quando company_id is not None; caller api/v1 eh tenant-gated via require_company_id
        query = select(Goal)

        if user_id:
            query = query.where(Goal.user_id == user_id)
        if company_id:
            query = query.where(Goal.company_id == company_id)
        if period:
            query = query.where(Goal.period == period)
        if category:
            query = query.where(Goal.category == category)
        if status:
            query = query.where(Goal.status == status)
        if not include_inactive:
            query = query.where(Goal.is_active)

        query = query.order_by(Goal.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(
        self,
        goal_id: uuid.UUID,
        company_id: uuid.UUID | None = None,
    ) -> Goal | None:
        """Lookup Goal por id.

        Sprint B.1 tail (2026-05-22): company_id RECOMENDADO (defense-in-depth).
        Quando passado, filtra por tenant.
        """
        # TENANT-EXEMPT: defense-in-depth — caller eh tenant-gated; company_id param desde Sprint B.1 tail
        if company_id is not None:
            result = await self.db.execute(
                select(Goal).where(
                    Goal.id == goal_id,
                    Goal.company_id == company_id,
                )
            )
        else:
            # TENANT-EXEMPT: backwards-compat — caller validates goal.company_id post-fetch
            result = await self.db.execute(
                select(Goal).where(Goal.id == goal_id)
            )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Goal mutations
    # ------------------------------------------------------------------

    async def create(self, data: dict) -> Goal:
        goal = Goal(**data)
        goal.calculate_progress()
        goal.update_status()
        self.db.add(goal)
        await self.db.commit()
        await self.db.refresh(goal)
        return goal

    async def update(self, goal_id: uuid.UUID, data: dict) -> Goal | None:
        goal = await self.get_by_id(goal_id)
        if not goal:
            return None
        for field, value in data.items():
            setattr(goal, field, value)
        goal.calculate_progress()
        goal.update_status()
        goal.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(goal)
        return goal

    async def soft_delete(self, goal_id: uuid.UUID) -> Goal | None:
        goal = await self.get_by_id(goal_id)
        if not goal:
            return None
        goal.is_active = False
        goal.updated_at = datetime.utcnow()
        await self.db.commit()
        return goal

    async def create_bulk(self, goals_data: list[dict]) -> list[Goal]:
        created: list[Goal] = []
        for data in goals_data:
            goal = Goal(**data)
            goal.calculate_progress()
            goal.update_status()
            self.db.add(goal)
            created.append(goal)
        await self.db.commit()
        for goal in created:
            await self.db.refresh(goal)
        return created

    async def add_and_flush(self, goal: Goal) -> None:
        """Add a single Goal instance and flush (used during import)."""
        self.db.add(goal)
        await self.db.flush()

    async def commit(self) -> None:
        await self.db.commit()

    async def rollback(self) -> None:
        await self.db.rollback()

    # ------------------------------------------------------------------
    # GoalTemplate queries
    # ------------------------------------------------------------------

    async def list_templates(
        self,
        company_id: uuid.UUID | None = None,
        category: str | None = None,
        include_inactive: bool = False,
    ) -> list[GoalTemplate]:
        # TENANT-EXEMPT: marketplace pattern — global templates (is_system=True) compartilhados;
        # filter aplicado via or_(company_id, is_system) abaixo quando company_id is not None.
        # company_id=None reservado pra admin-only — caller responsavel pelo gate.
        query = select(GoalTemplate)

        if company_id:
            query = query.where(
                or_(
                    GoalTemplate.company_id == company_id,
                    GoalTemplate.is_system,
                )
            )
        if category:
            query = query.where(GoalTemplate.category == category)
        if not include_inactive:
            query = query.where(GoalTemplate.is_active)

        query = query.order_by(GoalTemplate.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def find_system_template_by_name(self, name: str) -> GoalTemplate | None:
        """Lookup global system template por nome.

        TENANT-EXEMPT: system templates por definicao tem company_id=NULL (compartilhados);
        is_system=True garante so retornar templates marketplace globais.
        """
        result = await self.db.execute(
            select(GoalTemplate).where(
                and_(
                    GoalTemplate.name == name,
                    GoalTemplate.is_system,
                )
            )
        )
        return result.scalar_one_or_none()

    async def create_template(self, data: dict) -> GoalTemplate:
        template = GoalTemplate(**data)
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template
