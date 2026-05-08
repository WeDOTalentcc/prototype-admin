"""DataRequestRepository — DB access for DataRequest, DataRequestConfig,
DataRequestTemplate, DataRequestField, VacancyDataRequestConfig.

Extracted from app/domains/communication/services/data_request_service.py per ADR-001.
Multi-row queries scoped by company_id (multi-tenancy invariant).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.data_request import (
    DataRequest,
    DataRequestConfig,
    DataRequestField,
    DataRequestStatus,
    DataRequestTemplate,
    TriggerType,
    VacancyDataRequestConfig,
)


class DataRequestRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ---- DataRequest ----
    async def list_for_candidate(
        self,
        *,
        candidate_id: UUID,
        status: DataRequestStatus | None = None,
        include_expired: bool = False,
    ) -> list[DataRequest]:
        query = select(DataRequest).where(DataRequest.candidate_id == candidate_id)
        if status:
            query = query.where(DataRequest.status == status)
        if not include_expired:
            query = query.where(
                or_(
                    DataRequest.status != DataRequestStatus.EXPIRED,
                    DataRequest.expires_at > datetime.utcnow(),
                )
            )
        query = query.order_by(DataRequest.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_for_vacancy(
        self,
        *,
        vacancy_id: UUID,
        status: DataRequestStatus | None = None,
    ) -> list[DataRequest]:
        query = select(DataRequest).where(DataRequest.vacancy_id == vacancy_id)
        if status:
            query = query.where(DataRequest.status == status)
        query = query.order_by(DataRequest.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_token(self, token: str) -> DataRequest | None:
        result = await self.db.execute(
            select(DataRequest).where(DataRequest.token == token)
        )
        return result.scalar_one_or_none()

    async def find_pending_for_stage(
        self,
        *,
        candidate_id: UUID,
        stage: str,
        statuses: list,
    ) -> DataRequest | None:
        query = select(DataRequest).where(
            and_(
                DataRequest.candidate_id == candidate_id,
                DataRequest.trigger_stage == stage,
                DataRequest.status.in_(statuses),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ---- DataRequestConfig ----
    async def get_config_for_company(
        self,
        *,
        company_id: UUID,
    ) -> DataRequestConfig | None:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        result = await self.db.execute(
            select(DataRequestConfig).where(DataRequestConfig.company_id == company_id)
        )
        return result.scalar_one_or_none()

    def add_config(self, config: DataRequestConfig) -> None:
        self.db.add(config)

    # ---- DataRequestTemplate ----
    async def list_templates_for_company(
        self,
        *,
        company_id: UUID,
        active_only: bool = True,
    ) -> list[DataRequestTemplate]:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        query = select(DataRequestTemplate).where(
            DataRequestTemplate.company_id == company_id
        )
        if active_only:
            query = query.where(DataRequestTemplate.is_active)
        query = query.order_by(DataRequestTemplate.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def find_active_template_for_stage(
        self,
        *,
        company_id: UUID,
        stage: str,
    ) -> DataRequestTemplate | None:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        result = await self.db.execute(
            select(DataRequestTemplate)
            .where(
                and_(
                    DataRequestTemplate.company_id == company_id,
                    DataRequestTemplate.trigger_stage == stage,
                    DataRequestTemplate.is_active,
                    DataRequestTemplate.trigger_type.in_([
                        TriggerType.STAGE_ENTRY,
                        TriggerType.AUTOMATIC,
                    ]),
                )
            )
            .order_by(DataRequestTemplate.is_default.desc())
        )
        return result.scalar_one_or_none()

    # ---- DataRequestField ----
    async def list_active_fields_for_company(
        self,
        *,
        company_id: UUID,
    ) -> list[DataRequestField]:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        result = await self.db.execute(
            select(DataRequestField)
            .where(
                DataRequestField.company_id == company_id,
                DataRequestField.is_active,
            )
            .order_by(DataRequestField.order)
        )
        return list(result.scalars().all())

    # ---- VacancyDataRequestConfig ----
    async def get_vacancy_config(
        self,
        *,
        vacancy_id: UUID,
    ) -> VacancyDataRequestConfig | None:
        result = await self.db.execute(
            select(VacancyDataRequestConfig).where(
                VacancyDataRequestConfig.vacancy_id == vacancy_id
            )
        )
        return result.scalar_one_or_none()
