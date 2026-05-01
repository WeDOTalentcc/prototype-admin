"""
TechnicalTestsRepository — session-in-constructor pattern.
Covers all DB operations needed by app/api/v1/technical_tests.py.
"""
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.technical_tests import (
    ClientTestConfig,
    TechnicalTest,
    TestResult,
)

logger = logging.getLogger(__name__)


class TechnicalTestsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── TechnicalTest CRUD ────────────────────────────────────────────────

    async def list_tests(
        self,
        category: str | None = None,
        subcategory: str | None = None,
        difficulty: str | None = None,
        is_global: bool | None = None,
        is_active: bool | None = True,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TechnicalTest]:
        conditions = []

        if is_active is not None:
            conditions.append(TechnicalTest.is_active == is_active)

        if category:
            conditions.append(TechnicalTest.category == category)

        if subcategory:
            conditions.append(TechnicalTest.subcategory == subcategory)

        if difficulty:
            conditions.append(TechnicalTest.difficulty == difficulty)

        if is_global is not None:
            conditions.append(TechnicalTest.is_global == is_global)

        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    TechnicalTest.name.ilike(search_term),
                    TechnicalTest.description.ilike(search_term),
                )
            )

        query = select(TechnicalTest)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(TechnicalTest.category, TechnicalTest.name)
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_tests(
        self,
        category: str | None = None,
        subcategory: str | None = None,
        difficulty: str | None = None,
        is_global: bool | None = None,
        is_active: bool | None = True,
        search: str | None = None,
    ) -> int:
        conditions = []

        if is_active is not None:
            conditions.append(TechnicalTest.is_active == is_active)

        if category:
            conditions.append(TechnicalTest.category == category)

        if subcategory:
            conditions.append(TechnicalTest.subcategory == subcategory)

        if difficulty:
            conditions.append(TechnicalTest.difficulty == difficulty)

        if is_global is not None:
            conditions.append(TechnicalTest.is_global == is_global)

        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    TechnicalTest.name.ilike(search_term),
                    TechnicalTest.description.ilike(search_term),
                )
            )

        query = select(func.count(TechnicalTest.id))
        if conditions:
            query = query.where(and_(*conditions))

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_by_id(self, test_id: UUID) -> TechnicalTest | None:
        result = await self.db.execute(
            select(TechnicalTest).where(TechnicalTest.id == test_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> TechnicalTest | None:
        result = await self.db.execute(
            select(TechnicalTest).where(TechnicalTest.name == name)
        )
        return result.scalar_one_or_none()

    async def create_test(self, test: TechnicalTest) -> TechnicalTest:
        self.db.add(test)
        await self.db.commit()
        await self.db.refresh(test)
        return test

    async def update_test(self, test: TechnicalTest) -> TechnicalTest:
        await self.db.commit()
        await self.db.refresh(test)
        return test

    async def deactivate_test(self, test: TechnicalTest) -> None:
        test.is_active = False
        test.updated_at = datetime.utcnow()
        await self.db.commit()

    async def rollback(self) -> None:
        await self.db.rollback()

    # ── ClientTestConfig ──────────────────────────────────────────────────

    async def list_client_tests(
        self,
        client_id: UUID,
        is_enabled: bool | None = None,
        category: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[tuple[ClientTestConfig, TechnicalTest]]:
        conditions = [ClientTestConfig.client_id == client_id]

        if is_enabled is not None:
            conditions.append(ClientTestConfig.is_enabled == is_enabled)

        query = select(ClientTestConfig, TechnicalTest).join(
            TechnicalTest, ClientTestConfig.test_id == TechnicalTest.id
        ).where(and_(*conditions))

        if category:
            query = query.where(TechnicalTest.category == category)

        query = query.order_by(ClientTestConfig.priority.desc(), TechnicalTest.name)
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.all())

    async def count_client_tests(
        self,
        client_id: UUID,
        is_enabled: bool | None = None,
    ) -> int:
        conditions = [ClientTestConfig.client_id == client_id]

        if is_enabled is not None:
            conditions.append(ClientTestConfig.is_enabled == is_enabled)

        query = select(func.count(ClientTestConfig.id)).where(and_(*conditions))
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_client_test_config(
        self, client_id: UUID, test_id: UUID
    ) -> ClientTestConfig | None:
        result = await self.db.execute(
            select(ClientTestConfig).where(
                and_(
                    ClientTestConfig.client_id == client_id,
                    ClientTestConfig.test_id == test_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def upsert_client_test_config(
        self, config: ClientTestConfig, is_new: bool
    ) -> ClientTestConfig:
        if is_new:
            self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        return config

    async def delete_client_test_config(self, config: ClientTestConfig) -> None:
        await self.db.delete(config)
        await self.db.commit()

    # ── Stats ──────────────────────────────────────────────────────────────

    async def count_enabled_client_tests(self, client_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count(ClientTestConfig.id)).where(
                and_(
                    ClientTestConfig.client_id == client_id,
                    ClientTestConfig.is_enabled,
                )
            )
        )
        return result.scalar() or 0

    async def get_test_results_stats(self, client_id: UUID) -> list[Any]:
        query = select(
            TestResult.test_id,
            func.count(TestResult.id).label("total_taken"),
            func.count(case((TestResult.completed_at.isnot(None), 1))).label("total_completed"),
            func.avg(TestResult.score).label("avg_score"),
            func.avg(TestResult.time_taken_seconds).label("avg_time"),
            func.sum(case((TestResult.passed, 1), else_=0)).label("passed_count"),
        ).where(
            TestResult.client_id == client_id
        ).group_by(TestResult.test_id)

        result = await self.db.execute(query)
        return list(result.all())

    async def get_category_stats(self, client_id: UUID) -> list[Any]:
        query = select(
            TechnicalTest.category,
            func.count(TestResult.id).label("count"),
            func.avg(TestResult.score).label("avg_score"),
        ).join(
            TestResult, TechnicalTest.id == TestResult.test_id
        ).where(
            TestResult.client_id == client_id
        ).group_by(TechnicalTest.category)

        result = await self.db.execute(query)
        return list(result.all())
