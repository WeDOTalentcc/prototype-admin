"""
Repository for Trust Center domain.

Encapsulates all database access for:
- TrustCenterSettings
- TrustCenterResource
- TrustCenterUpdate
- Subprocessor
- ComplianceControl (read-only, aggregations)
- BiasAuditReport (read-only)
"""
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.observability import BiasAuditReport, ComplianceControl
from app.models.trust_center import (
    Subprocessor,
    TrustCenterResource,
    TrustCenterSettings,
    TrustCenterUpdate,
)


class TrustCenterRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------ #
    # Settings                                                             #
    # ------------------------------------------------------------------ #

    async def get_settings_by_slug(self, company_slug: str) -> TrustCenterSettings:
        """Fetch settings by company_slug; raises 404 if not found."""
        # TENANT-EXEMPT: trust_center settings/resources are global (no tenant scoping by design) or per-company via dynamic conditions builder; LGPD-safe; T-RATCHET tenant_filter
        query = select(TrustCenterSettings).where(
            TrustCenterSettings.company_slug == company_slug
        )
        result = await self.db.execute(query)
        settings = result.scalar_one_or_none()
        if not settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trust center not found for slug: {company_slug}",
            )
        return settings

    async def get_settings_by_company_id(self, company_uuid: UUID):
        query = select(TrustCenterSettings).where(
            TrustCenterSettings.company_id == company_uuid
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def settings_slug_taken(self, company_slug: str, exclude_id=None) -> bool:
        conditions = [TrustCenterSettings.company_slug == company_slug]
        if exclude_id is not None:
            conditions.append(TrustCenterSettings.id != exclude_id)
        # TENANT-EXEMPT: trust_center settings/resources are global (no tenant scoping by design) or per-company via dynamic conditions builder; LGPD-safe; T-RATCHET tenant_filter
        query = select(TrustCenterSettings).where(and_(*conditions))
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def create_settings(self, company_uuid: UUID, data: dict) -> TrustCenterSettings:
        settings = TrustCenterSettings(company_id=company_uuid, **data)
        self.db.add(settings)
        await self.db.flush()
        await self.db.refresh(settings)
        return settings

    async def update_settings(self, settings: TrustCenterSettings, update_data: dict) -> TrustCenterSettings:
        for key, value in update_data.items():
            if value is not None:
                setattr(settings, key, value)
        await self.db.flush()
        await self.db.refresh(settings)
        return settings

    # ------------------------------------------------------------------ #
    # Resources                                                            #
    # ------------------------------------------------------------------ #

    async def list_resources(self, company_uuid: UUID, category=None):
        conditions = [
            TrustCenterResource.company_id == company_uuid,
            TrustCenterResource.is_public,
        ]
        if category:
            conditions.append(TrustCenterResource.category == category)
        query = (
            # TENANT-EXEMPT: trust_center settings/resources are global (no tenant scoping by design) or per-company via dynamic conditions builder; LGPD-safe; T-RATCHET tenant_filter
            select(TrustCenterResource)
            .where(and_(*conditions))
            .order_by(TrustCenterResource.title)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_resource(self, company_uuid: UUID, data: dict) -> TrustCenterResource:
        resource = TrustCenterResource(company_id=company_uuid, **data)
        self.db.add(resource)
        await self.db.flush()
        await self.db.refresh(resource)
        return resource

    # ------------------------------------------------------------------ #
    # Updates                                                              #
    # ------------------------------------------------------------------ #

    async def list_updates(self, company_uuid: UUID, category=None, limit=10):
        conditions = [
            TrustCenterUpdate.company_id == company_uuid,
            TrustCenterUpdate.is_published,
        ]
        if category:
            conditions.append(TrustCenterUpdate.category == category)
        query = (
            # TENANT-EXEMPT: trust_center settings/resources are global (no tenant scoping by design) or per-company via dynamic conditions builder; LGPD-safe; T-RATCHET tenant_filter
            select(TrustCenterUpdate)
            .where(and_(*conditions))
            .order_by(desc(TrustCenterUpdate.published_at))
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def count_updates(self, company_uuid: UUID, category=None) -> int:
        conditions = [
            TrustCenterUpdate.company_id == company_uuid,
            TrustCenterUpdate.is_published,
        ]
        if category:
            conditions.append(TrustCenterUpdate.category == category)
        query = select(func.count(TrustCenterUpdate.id)).where(and_(*conditions))
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def create_update(self, company_uuid: UUID, data: dict, is_published: bool) -> TrustCenterUpdate:
        published_at = datetime.utcnow() if is_published else None
        update = TrustCenterUpdate(
            company_id=company_uuid,
            published_at=published_at,
            **data,
        )
        self.db.add(update)
        await self.db.flush()
        await self.db.refresh(update)
        return update

    # ------------------------------------------------------------------ #
    # Subprocessors                                                        #
    # ------------------------------------------------------------------ #

    async def list_subprocessors(self, company_uuid: UUID, category=None):
        conditions = [
            Subprocessor.company_id == company_uuid,
            Subprocessor.is_public,
        ]
        if category:
            conditions.append(Subprocessor.category == category)
        query = (
            # TENANT-EXEMPT: trust_center settings/resources are global (no tenant scoping by design) or per-company via dynamic conditions builder; LGPD-safe; T-RATCHET tenant_filter
            select(Subprocessor)
            .where(and_(*conditions))
            .order_by(Subprocessor.name)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_subprocessor(self, company_uuid: UUID, data: dict) -> Subprocessor:
        subprocessor = Subprocessor(company_id=company_uuid, **data)
        self.db.add(subprocessor)
        await self.db.flush()
        await self.db.refresh(subprocessor)
        return subprocessor

    # ------------------------------------------------------------------ #
    # ComplianceControl aggregations (read-only)                          #
    # ------------------------------------------------------------------ #

    async def get_controls_framework_stats(self, company_uuid: UUID):
        """Return rows of (framework, status, count) for a company."""
        query = (
            select(
                ComplianceControl.framework,
                ComplianceControl.status,
                func.count(ComplianceControl.id).label("count"),
            )
            .where(ComplianceControl.company_id == company_uuid)
            .group_by(ComplianceControl.framework, ComplianceControl.status)
        )
        result = await self.db.execute(query)
        return result.all()

    async def count_implemented_controls(self, company_uuid: UUID) -> int:
        query = select(func.count(ComplianceControl.id)).where(
            and_(
                ComplianceControl.company_id == company_uuid,
                ComplianceControl.status == "implemented",
            )
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def list_implemented_controls_by_framework(self, company_uuid: UUID):
        """Return all implemented controls ordered by framework (for certifications view)."""
        query = (
            select(ComplianceControl)
            .where(
                and_(
                    ComplianceControl.company_id == company_uuid,
                    ComplianceControl.status == "implemented",
                )
            )
            .order_by(ComplianceControl.framework)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    # ------------------------------------------------------------------ #
    # BiasAuditReport (read-only)                                         #
    # ------------------------------------------------------------------ #

    async def list_public_bias_audits(self, company_uuid: UUID):
        query = (
            select(BiasAuditReport)
            .where(
                and_(
                    BiasAuditReport.company_id == company_uuid,
                    BiasAuditReport.is_public,
                )
            )
            .order_by(desc(BiasAuditReport.published_at))
        )
        result = await self.db.execute(query)
        return result.scalars().all()
