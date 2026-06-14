"""Campaign Repository — data access layer for RecruitmentCampaign.

ADR-001 compliant: services must not issue SQL directly; all queries live here.
Every public method requires company_id (multi-tenancy fail-closed).
"""
import logging
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.recruitment_campaign import RecruitmentCampaign

logger = logging.getLogger(__name__)


class CampaignRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _require_company_id(self, company_id: str) -> None:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy fail-closed)")

    async def list_by_company(
        self,
        company_id: str,
        status: str | None = None,
        job_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[RecruitmentCampaign], int]:
        self._require_company_id(company_id)
        q = select(RecruitmentCampaign).where(RecruitmentCampaign.company_id == company_id)
        if status:
            q = q.where(RecruitmentCampaign.status == status)
        if job_id:
            q = q.where(RecruitmentCampaign.job_id == job_id)

        count_q = select(func.count()).select_from(q.subquery())
        total = (await self.db.execute(count_q)).scalar_one()

        q = q.order_by(RecruitmentCampaign.created_at.desc()).limit(limit).offset(offset)
        rows = list((await self.db.execute(q)).scalars().all())
        return rows, total

    async def get_by_id(self, campaign_id: UUID, company_id: str) -> RecruitmentCampaign | None:
        self._require_company_id(company_id)
        result = await self.db.execute(
            select(RecruitmentCampaign).where(
                RecruitmentCampaign.id == campaign_id,
                RecruitmentCampaign.company_id == company_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> RecruitmentCampaign:
        self._require_company_id(data.get("company_id", ""))
        campaign = RecruitmentCampaign(**data)
        self.db.add(campaign)
        await self.db.flush()
        await self.db.refresh(campaign)
        return campaign

    async def update(
        self,
        campaign_id: UUID,
        company_id: str,
        updates: dict,
    ) -> RecruitmentCampaign | None:
        self._require_company_id(company_id)
        campaign = await self.get_by_id(campaign_id, company_id)
        if campaign is None:
            return None
        for key, value in updates.items():
            if hasattr(campaign, key) and key not in ("id", "company_id", "created_by", "created_at"):
                setattr(campaign, key, value)
        campaign.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(campaign)
        return campaign

    async def advance_stage(
        self,
        campaign_id: UUID,
        company_id: str,
    ) -> RecruitmentCampaign | None:
        self._require_company_id(company_id)
        campaign = await self.get_by_id(campaign_id, company_id)
        if campaign is None:
            return None
        if campaign.stages and campaign.current_stage_index < len(campaign.stages) - 1:
            campaign.current_stage_index += 1
        elif campaign.stages and campaign.current_stage_index >= len(campaign.stages) - 1:
            campaign.status = "completed"
        campaign.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(campaign)
        return campaign
