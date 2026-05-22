"""
Repository for Compliance Controls domain.

Encapsulates all database access for:
- ComplianceControlLibrary
- CompanyComplianceControl
- ComplianceAudit
- SOXControl
"""
from datetime import date, datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.observability import (
    CompanyComplianceControl,
    ComplianceAudit,
    ComplianceControlLibrary,
    SOXControl,
)


class ComplianceControlsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------ #
    # Control Library                                                      #
    # ------------------------------------------------------------------ #

    async def list_control_library(
        self,
        framework=None,
        category=None,
        search=None,
        limit=100,
        offset=0,
    ):
        conditions = []
        if framework:
            conditions.append(ComplianceControlLibrary.framework == framework)
        if category:
            conditions.append(ComplianceControlLibrary.control_category == category)
        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    ComplianceControlLibrary.control_name.ilike(search_term),
                    ComplianceControlLibrary.control_description.ilike(search_term),
                )
            )

        query = select(ComplianceControlLibrary)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(
            ComplianceControlLibrary.framework, ComplianceControlLibrary.control_id
        )
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        controls = result.scalars().all()

        count_query = select(func.count(ComplianceControlLibrary.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        return controls, total

    async def get_controls_by_framework(self, framework: str, limit=200, offset=0):
        query = (
            select(ComplianceControlLibrary)
            .where(ComplianceControlLibrary.framework == framework)
            .order_by(ComplianceControlLibrary.control_id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        controls = result.scalars().all()

        count_query = select(func.count(ComplianceControlLibrary.id)).where(
            ComplianceControlLibrary.framework == framework
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        return controls, total

    async def get_control_library_item(self, control_id: UUID):
        query = select(ComplianceControlLibrary).where(
            ComplianceControlLibrary.id == control_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_control_library(
        self,
        framework: str,
        control_id: str,
        control_name: str,
        control_description=None,
        control_category=None,
        domain=None,
        is_mandatory: bool = False,
        implementation_guidance=None,
        evidence_requirements=None,
        related_controls=None,
    ):
        control = ComplianceControlLibrary(
            framework=framework,
            control_id=control_id,
            control_name=control_name,
            control_description=control_description,
            control_category=control_category,
            domain=domain,
            is_mandatory=is_mandatory,
            implementation_guidance=implementation_guidance,
            evidence_requirements=evidence_requirements or [],
            related_controls=related_controls or [],
        )
        self.db.add(control)
        await self.db.commit()
        await self.db.refresh(control)
        return control

    async def check_control_library_exists(self, framework: str, control_id_val: str):
        """Return True if a library entry already exists for the given framework + control_id."""
        result = await self.db.execute(
            select(ComplianceControlLibrary).where(
                and_(
                    ComplianceControlLibrary.framework == framework,
                    ComplianceControlLibrary.control_id == control_id_val,
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def add_library_entry_no_commit(self, entry: ComplianceControlLibrary):
        """Add a library entry without committing (for batch operations)."""
        self.db.add(entry)

    async def commit(self):
        await self.db.commit()

    async def rollback(self):
        await self.db.rollback()

    # ------------------------------------------------------------------ #
    # Company Compliance Controls                                          #
    # ------------------------------------------------------------------ #

    async def list_company_controls(
        self,
        company_uuid: UUID,
        status_filter=None,
        limit=100,
        offset=0,
    ):
        conditions = [CompanyComplianceControl.company_id == company_uuid]
        if status_filter:
            conditions.append(CompanyComplianceControl.status == status_filter)

        query = (
            # TENANT-EXEMPT: compliance controls catalog (SOX/LGPD) is system-wide reference data, not per-tenant; T-RATCHET tenant_filter
            select(CompanyComplianceControl)
            .where(and_(*conditions))
            .order_by(desc(CompanyComplianceControl.updated_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        controls = result.scalars().all()

        count_query = select(func.count(CompanyComplianceControl.id)).where(
            and_(*conditions)
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        return controls, total

    async def get_company_control(self, control_uuid: UUID, company_uuid: UUID):
        query = select(CompanyComplianceControl).where(
            and_(
                CompanyComplianceControl.id == control_uuid,
                CompanyComplianceControl.company_id == company_uuid,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_company_control(
        self,
        company_uuid: UUID,
        control_library_id: UUID,
        status: str = "not_started",
        owner_name=None,
        owner_email=None,
        notes=None,
    ):
        control = CompanyComplianceControl(
            company_id=company_uuid,
            control_library_id=control_library_id,
            status=status,
            owner_name=owner_name,
            owner_email=owner_email,
            notes=notes,
        )
        self.db.add(control)
        await self.db.commit()
        await self.db.refresh(control)
        return control

    async def update_company_control(self, control: CompanyComplianceControl, update_data: dict):
        for key, value in update_data.items():
            setattr(control, key, value)
        await self.db.commit()
        await self.db.refresh(control)
        return control

    async def update_company_control_evidence(
        self, control: CompanyComplianceControl, evidence_files: list
    ):
        control.evidence_files = evidence_files
        await self.db.commit()
        await self.db.refresh(control)
        return control

    async def delete_company_control(self, control: CompanyComplianceControl):
        await self.db.delete(control)
        await self.db.commit()

    # ------------------------------------------------------------------ #
    # Compliance Audits                                                    #
    # ------------------------------------------------------------------ #

    async def list_audits(
        self,
        company_uuid: UUID,
        framework=None,
        audit_type=None,
        limit=50,
        offset=0,
    ):
        conditions = [ComplianceAudit.company_id == company_uuid]
        if framework:
            conditions.append(ComplianceAudit.framework == framework)
        if audit_type:
            conditions.append(ComplianceAudit.audit_type == audit_type)

        query = (
            # TENANT-EXEMPT: compliance controls catalog (SOX/LGPD) is system-wide reference data, not per-tenant; T-RATCHET tenant_filter
            select(ComplianceAudit)
            .where(and_(*conditions))
            .order_by(desc(ComplianceAudit.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        audits = result.scalars().all()

        count_query = select(func.count(ComplianceAudit.id)).where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        return audits, total

    async def get_audit(self, audit_id: UUID, company_uuid: UUID):
        query = select(ComplianceAudit).where(
            and_(
                ComplianceAudit.id == audit_id,
                ComplianceAudit.company_id == company_uuid,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_audit(
        self,
        company_uuid: UUID,
        framework: str,
        audit_type: str,
        auditor_organization=None,
        auditor_name=None,
        audit_start_date=None,
        audit_end_date=None,
        scope_description=None,
    ):
        audit = ComplianceAudit(
            company_id=company_uuid,
            framework=framework,
            audit_type=audit_type,
            auditor_organization=auditor_organization,
            auditor_name=auditor_name,
            audit_start_date=audit_start_date,
            audit_end_date=audit_end_date,
            scope_description=scope_description,
        )
        self.db.add(audit)
        await self.db.commit()
        await self.db.refresh(audit)
        return audit

    async def update_audit(self, audit: ComplianceAudit, update_data: dict):
        for key, value in update_data.items():
            setattr(audit, key, value)
        await self.db.commit()
        await self.db.refresh(audit)
        return audit

    # ------------------------------------------------------------------ #
    # SOX Controls                                                         #
    # ------------------------------------------------------------------ #

    async def list_sox_controls(
        self,
        company_uuid: UUID,
        section=None,
        test_result=None,
        limit=100,
        offset=0,
    ):
        conditions = [SOXControl.company_id == company_uuid]
        if section:
            conditions.append(SOXControl.section == section)
        if test_result:
            conditions.append(SOXControl.test_result == test_result)

        query = (
            # TENANT-EXEMPT: compliance controls catalog (SOX/LGPD) is system-wide reference data, not per-tenant; T-RATCHET tenant_filter
            select(SOXControl)
            .where(and_(*conditions))
            .order_by(SOXControl.section, SOXControl.control_id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        controls = result.scalars().all()

        count_query = select(func.count(SOXControl.id)).where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        return controls, total

    async def get_sox_control(self, control_uuid: UUID, company_uuid: UUID):
        query = select(SOXControl).where(
            and_(
                SOXControl.id == control_uuid,
                SOXControl.company_id == company_uuid,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_sox_control(
        self,
        company_uuid: UUID,
        section: str,
        control_id: str,
        control_name: str,
        control_objective=None,
        key_control: bool = False,
        frequency=None,
        control_owner=None,
    ):
        control = SOXControl(
            company_id=company_uuid,
            section=section,
            control_id=control_id,
            control_name=control_name,
            control_objective=control_objective,
            key_control=key_control,
            frequency=frequency,
            control_owner=control_owner,
        )
        self.db.add(control)
        await self.db.commit()
        await self.db.refresh(control)
        return control

    async def update_sox_control(self, control: SOXControl, update_data: dict):
        for key, value in update_data.items():
            setattr(control, key, value)
        await self.db.commit()
        await self.db.refresh(control)
        return control

    # ------------------------------------------------------------------ #
    # Dashboard aggregations                                               #
    # ------------------------------------------------------------------ #

    async def get_compliance_dashboard_stats(self, company_uuid: UUID):
        """Return all data needed for the compliance dashboard in one place."""
        # Join company controls with library to get framework info
        ctrl_query = select(
            CompanyComplianceControl, ComplianceControlLibrary
        ).join(
            ComplianceControlLibrary,
            CompanyComplianceControl.control_library_id == ComplianceControlLibrary.id,
        ).where(CompanyComplianceControl.company_id == company_uuid)

        result = await self.db.execute(ctrl_query)
        controls = result.all()

        today = date.today()
        next_30_days = today + timedelta(days=30)

        upcoming_query = select(func.count(CompanyComplianceControl.id)).where(
            and_(
                CompanyComplianceControl.company_id == company_uuid,
                CompanyComplianceControl.next_review_date.isnot(None),
                CompanyComplianceControl.next_review_date <= next_30_days,
                CompanyComplianceControl.next_review_date >= today,
            )
        )
        upcoming_result = await self.db.execute(upcoming_query)
        upcoming_reviews = upcoming_result.scalar() or 0

        overdue_query = select(func.count(CompanyComplianceControl.id)).where(
            and_(
                CompanyComplianceControl.company_id == company_uuid,
                CompanyComplianceControl.next_review_date.isnot(None),
                CompanyComplianceControl.next_review_date < today,
            )
        )
        overdue_result = await self.db.execute(overdue_query)
        overdue_reviews = overdue_result.scalar() or 0

        audit_query = (
            select(ComplianceAudit)
            .where(ComplianceAudit.company_id == company_uuid)
            .order_by(desc(ComplianceAudit.created_at))
            .limit(5)
        )
        audit_result = await self.db.execute(audit_query)
        recent_audits = audit_result.scalars().all()

        sox_query = (
            select(SOXControl.test_result, func.count(SOXControl.id).label("count"))
            .where(SOXControl.company_id == company_uuid)
            .group_by(SOXControl.test_result)
        )
        sox_result = await self.db.execute(sox_query)
        sox_summary = {row.test_result: row.count for row in sox_result}

        return controls, upcoming_reviews, overdue_reviews, recent_audits, sox_summary
