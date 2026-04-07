"""
DataRequestRepository — data access for direct DB calls in data_request.py
that bypass the data_request_service layer.
Extracted from app/api/v1/data_request.py as part of Phase 2 refactor.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class DataRequestRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_all_for_company(
        self,
        company_id: str,
        status_enum=None,
        limit: int = 100,
    ) -> list:
        """
        Return DataRequest rows for a company (no vacancy/candidate filter).
        Used as fallback in list_data_requests when neither candidate_id
        nor vacancy_id is supplied.
        """
        from app.models.data_request import DataRequest

        query = select(DataRequest).where(DataRequest.company_id == company_id)
        if status_enum is not None:
            query = query.where(DataRequest.status == status_enum)
        query = query.order_by(DataRequest.created_at.desc()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_vacancy_trigger_config(self, vacancy_id: UUID):
        """Return VacancyDataRequestConfig for a vacancy, or None."""
        from app.models.data_request import VacancyDataRequestConfig

        result = await self.db.execute(
            select(VacancyDataRequestConfig).where(
                VacancyDataRequestConfig.vacancy_id == vacancy_id
            )
        )
        return result.scalar_one_or_none()

    async def upsert_vacancy_trigger_config(
        self,
        vacancy_id: UUID,
        use_company_defaults: bool,
        custom_template_id,
        stage_configs: dict,
    ):
        """Create or update VacancyDataRequestConfig; flush and refresh; return instance."""
        from app.models.data_request import VacancyDataRequestConfig

        config = await self.get_vacancy_trigger_config(vacancy_id)
        if not config:
            config = VacancyDataRequestConfig(
                vacancy_id=vacancy_id,
                use_company_defaults=use_company_defaults,
                custom_template_id=custom_template_id,
                stage_configs=stage_configs,
            )
            self.db.add(config)
        else:
            config.use_company_defaults = use_company_defaults
            config.custom_template_id = custom_template_id
            if stage_configs:
                config.stage_configs = stage_configs

        await self.db.flush()
        await self.db.refresh(config)
        return config
