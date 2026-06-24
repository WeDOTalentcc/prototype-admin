"""ObservabilityRepository - manages observability and governance models."""
import logging
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.observability import (
    AIInferenceLog,
    BiasAuditReport,
    ComplianceControl,
    ConsentRecord,
    DataAccessLog,
    IncidentReport,
    ModelEvaluation,
)

logger = logging.getLogger(__name__)


class ObservabilityRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── AIInferenceLog ────────────────────────────────────────────────────────

    async def get_ai_inference_stats(
        self,
        company_uuid: UUID,
        agent_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict:
        conditions = [AIInferenceLog.company_id == company_uuid]
        if agent_type:
            conditions.append(AIInferenceLog.agent_type == agent_type)
        if start_date:
            conditions.append(AIInferenceLog.created_at >= start_date)
        if end_date:
            conditions.append(AIInferenceLog.created_at <= end_date)

        total_result = await self.db.execute(
            select(func.count(AIInferenceLog.id)).where(and_(*conditions))
        )
        total = total_result.scalar() or 0

        agent_type_result = await self.db.execute(
            select(AIInferenceLog.agent_type, func.count(AIInferenceLog.id).label('count'))
            .where(and_(*conditions))
            .group_by(AIInferenceLog.agent_type)
        )
        by_agent_type = {row.agent_type: row.count for row in agent_type_result}

        decision_type_result = await self.db.execute(
            select(AIInferenceLog.decision_type, func.count(AIInferenceLog.id).label('count'))
            .where(and_(*conditions))
            .group_by(AIInferenceLog.decision_type)
        )
        by_decision_type = {row.decision_type or "unknown": row.count for row in decision_type_result}

        avg_result = await self.db.execute(
            select(
                func.avg(AIInferenceLog.latency_ms).label('avg_latency'),
                func.avg(AIInferenceLog.confidence_score).label('avg_confidence'),
                func.sum(AIInferenceLog.tokens_used).label('total_tokens'),
            ).where(and_(*conditions))
        )
        avg_row = avg_result.one()

        override_result = await self.db.execute(
            select(func.count(AIInferenceLog.id)).where(
                and_(*conditions, AIInferenceLog.human_override == True)  # noqa: E712
            )
        )
        override_count = override_result.scalar() or 0

        return {
            "total": total,
            "by_agent_type": by_agent_type,
            "by_decision_type": by_decision_type,
            "avg_latency": avg_row.avg_latency,
            "avg_confidence": avg_row.avg_confidence,
            "total_tokens": avg_row.total_tokens,
            "override_count": override_count,
        }

    async def list_ai_inference_logs(
        self,
        company_uuid: UUID,
        agent_type: str | None = None,
        candidate_id: UUID | None = None,
        vacancy_id: UUID | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AIInferenceLog], int]:
        conditions = [AIInferenceLog.company_id == company_uuid]
        if agent_type:
            conditions.append(AIInferenceLog.agent_type == agent_type)
        if candidate_id:
            conditions.append(AIInferenceLog.candidate_id == candidate_id)
        if vacancy_id:
            conditions.append(AIInferenceLog.vacancy_id == vacancy_id)
        if start_date:
            conditions.append(AIInferenceLog.created_at >= start_date)
        if end_date:
            conditions.append(AIInferenceLog.created_at <= end_date)

        query = (
            # TENANT-EXEMPT: observability per-company log query uses conditions=[Model.company_id==X] + and_(*conditions); AST sensor cannot trace dynamic builder; T-RATCHET tenant_filter
            select(AIInferenceLog)
            .where(and_(*conditions))
            .order_by(desc(AIInferenceLog.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        logs = list(result.scalars().all())

        count_result = await self.db.execute(
            select(func.count(AIInferenceLog.id)).where(and_(*conditions))
        )
        total = count_result.scalar() or 0

        return logs, total

    async def get_ai_inference_log(self, log_uuid: UUID, company_uuid: UUID) -> AIInferenceLog | None:
        result = await self.db.execute(
            select(AIInferenceLog).where(
                and_(AIInferenceLog.id == log_uuid, AIInferenceLog.company_id == company_uuid)
            )
        )
        return result.scalar_one_or_none()

    # ── DataAccessLog ─────────────────────────────────────────────────────────

    async def get_data_access_stats(
        self,
        company_uuid: UUID,
        data_type: str | None = None,
        operation: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict:
        conditions = [DataAccessLog.company_id == company_uuid]
        if data_type:
            conditions.append(DataAccessLog.data_type == data_type)
        if operation:
            conditions.append(DataAccessLog.operation == operation)
        if start_date:
            conditions.append(DataAccessLog.created_at >= start_date)
        if end_date:
            conditions.append(DataAccessLog.created_at <= end_date)

        total_result = await self.db.execute(
            select(func.count(DataAccessLog.id)).where(and_(*conditions))
        )
        total = total_result.scalar() or 0

        data_type_result = await self.db.execute(
            select(DataAccessLog.data_type, func.count(DataAccessLog.id).label('count'))
            .where(and_(*conditions))
            .group_by(DataAccessLog.data_type)
        )
        by_data_type = {row.data_type: row.count for row in data_type_result}

        operation_result = await self.db.execute(
            select(DataAccessLog.operation, func.count(DataAccessLog.id).label('count'))
            .where(and_(*conditions))
            .group_by(DataAccessLog.operation)
        )
        by_operation = {row.operation: row.count for row in operation_result}

        legal_basis_result = await self.db.execute(
            select(DataAccessLog.legal_basis, func.count(DataAccessLog.id).label('count'))
            .where(and_(*conditions))
            .group_by(DataAccessLog.legal_basis)
        )
        by_legal_basis = {row.legal_basis or "unknown": row.count for row in legal_basis_result}

        unique_users_result = await self.db.execute(
            select(func.count(func.distinct(DataAccessLog.user_id))).where(and_(*conditions))
        )
        unique_users = unique_users_result.scalar() or 0

        unique_subjects_result = await self.db.execute(
            select(func.count(func.distinct(DataAccessLog.data_subject_id))).where(and_(*conditions))
        )
        unique_subjects = unique_subjects_result.scalar() or 0

        return {
            "total": total,
            "by_data_type": by_data_type,
            "by_operation": by_operation,
            "by_legal_basis": by_legal_basis,
            "unique_users": unique_users,
            "unique_subjects": unique_subjects,
        }

    async def list_data_access_logs(
        self,
        company_uuid: UUID,
        data_type: str | None = None,
        operation: str | None = None,
        user_id: UUID | None = None,
        data_subject_id: UUID | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[DataAccessLog], int]:
        conditions = [DataAccessLog.company_id == company_uuid]
        if data_type:
            conditions.append(DataAccessLog.data_type == data_type)
        if operation:
            conditions.append(DataAccessLog.operation == operation)
        if user_id:
            conditions.append(DataAccessLog.user_id == user_id)
        if data_subject_id:
            conditions.append(DataAccessLog.data_subject_id == data_subject_id)
        if start_date:
            conditions.append(DataAccessLog.created_at >= start_date)
        if end_date:
            conditions.append(DataAccessLog.created_at <= end_date)

        query = (
            # TENANT-EXEMPT: observability per-company log query uses conditions=[Model.company_id==X] + and_(*conditions); AST sensor cannot trace dynamic builder; T-RATCHET tenant_filter
            select(DataAccessLog)
            .where(and_(*conditions))
            .order_by(desc(DataAccessLog.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        logs = list(result.scalars().all())

        count_result = await self.db.execute(
            select(func.count(DataAccessLog.id)).where(and_(*conditions))
        )
        total = count_result.scalar() or 0

        return logs, total

    async def list_data_access_logs_by_data_subject(
        self,
        company_uuid: UUID,
        data_subject_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[DataAccessLog], int]:
        return await self.list_data_access_logs(
            company_uuid=company_uuid,
            data_subject_id=data_subject_id,
            limit=limit,
            offset=offset,
        )

    # ── ConsentRecord ─────────────────────────────────────────────────────────

    async def list_consent_records(
        self,
        company_uuid: UUID,
        consent_type: str | None = None,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ConsentRecord], int]:
        conditions = [ConsentRecord.company_id == company_uuid]
        if consent_type:
            conditions.append(ConsentRecord.consent_type == consent_type)
        if is_active is not None:
            conditions.append(ConsentRecord.is_active == is_active)

        query = (
            # TENANT-EXEMPT: observability per-company log query uses conditions=[Model.company_id==X] + and_(*conditions); AST sensor cannot trace dynamic builder; T-RATCHET tenant_filter
            select(ConsentRecord)
            .where(and_(*conditions))
            .order_by(desc(ConsentRecord.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        consents = list(result.scalars().all())

        count_result = await self.db.execute(
            select(func.count(ConsentRecord.id)).where(and_(*conditions))
        )
        total = count_result.scalar() or 0

        return consents, total

    async def list_consents_by_candidate(
        self,
        company_uuid: UUID,
        candidate_uuid: UUID,
        is_active: bool | None = None,
    ) -> list[ConsentRecord]:
        conditions = [
            ConsentRecord.company_id == company_uuid,
            ConsentRecord.candidate_id == candidate_uuid,
        ]
        if is_active is not None:
            conditions.append(ConsentRecord.is_active == is_active)

        query = (
            # TENANT-EXEMPT: observability per-company log query uses conditions=[Model.company_id==X] + and_(*conditions); AST sensor cannot trace dynamic builder; T-RATCHET tenant_filter
            select(ConsentRecord)
            .where(and_(*conditions))
            .order_by(desc(ConsentRecord.created_at))
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_consent(self, data: dict) -> ConsentRecord:
        consent = ConsentRecord(**data)
        self.db.add(consent)
        await self.db.commit()
        await self.db.refresh(consent)
        return consent

    async def get_consent(self, consent_uuid: UUID, company_uuid: UUID) -> ConsentRecord | None:
        result = await self.db.execute(
            select(ConsentRecord).where(
                and_(
                    ConsentRecord.id == consent_uuid,
                    ConsentRecord.company_id == company_uuid,
                )
            )
        )
        return result.scalar_one_or_none()

    async def revoke_consent(self, consent: ConsentRecord) -> ConsentRecord:
        """Append-only revocation: INSERTs a new revocation record instead of mutating the original.

        Required for compatibility with RN-06 immutability trigger in migration 261
        (BEFORE UPDATE/DELETE raises exception on consent_records).
        Returns the newly inserted revocation record.
        """
        import uuid as _uuid
        revocation = ConsentRecord(
            id=_uuid.uuid4(),
            company_id=consent.company_id,
            candidate_id=consent.candidate_id,
            consent_type=consent.consent_type,
            version=consent.version,
            granted_at=consent.granted_at,
            revoked_at=datetime.utcnow(),
            is_active=False,
            source=consent.source,
            legal_basis=consent.legal_basis,
            consent_text=consent.consent_text,
            ip_address=consent.ip_address,
            canal=consent.canal,
            user_agent=consent.user_agent,
            processo_id=consent.processo_id,
            vaga_id=consent.vaga_id,
            versao_disclaimer=consent.versao_disclaimer,
        )
        self.db.add(revocation)
        await self.db.commit()
        await self.db.refresh(revocation)
        return revocation

    # ── IncidentReport ────────────────────────────────────────────────────────

    async def list_incidents(
        self,
        company_uuid: UUID,
        incident_type: str | None = None,
        severity: str | None = None,
        status_filter: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[IncidentReport], int]:
        conditions = [IncidentReport.company_id == company_uuid]
        if incident_type:
            conditions.append(IncidentReport.incident_type == incident_type)
        if severity:
            conditions.append(IncidentReport.severity == severity)
        if status_filter:
            conditions.append(IncidentReport.status == status_filter)
        if start_date:
            conditions.append(IncidentReport.detected_at >= start_date)
        if end_date:
            conditions.append(IncidentReport.detected_at <= end_date)

        query = (
            # TENANT-EXEMPT: observability per-company log query uses conditions=[Model.company_id==X] + and_(*conditions); AST sensor cannot trace dynamic builder; T-RATCHET tenant_filter
            select(IncidentReport)
            .where(and_(*conditions))
            .order_by(desc(IncidentReport.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        incidents = list(result.scalars().all())

        count_result = await self.db.execute(
            select(func.count(IncidentReport.id)).where(and_(*conditions))
        )
        total = count_result.scalar() or 0

        return incidents, total

    async def create_incident(self, data: dict) -> IncidentReport:
        incident = IncidentReport(**data)
        self.db.add(incident)
        await self.db.commit()
        await self.db.refresh(incident)
        return incident

    async def get_incident(self, incident_uuid: UUID, company_uuid: UUID) -> IncidentReport | None:
        result = await self.db.execute(
            select(IncidentReport).where(
                and_(
                    IncidentReport.id == incident_uuid,
                    IncidentReport.company_id == company_uuid,
                )
            )
        )
        return result.scalar_one_or_none()

    async def update_incident(self, incident: IncidentReport, data: dict) -> IncidentReport:
        for key, value in data.items():
            if hasattr(incident, key):
                setattr(incident, key, value)
        await self.db.commit()
        await self.db.refresh(incident)
        return incident

    # ── ModelEvaluation ───────────────────────────────────────────────────────

    async def get_evaluation_summary(
        self,
        company_uuid: UUID,
        model_version: str | None = None,
    ) -> dict:
        conditions = [ModelEvaluation.company_id == company_uuid]
        if model_version:
            conditions.append(ModelEvaluation.model_version == model_version)

        total_result = await self.db.execute(
            select(func.count(ModelEvaluation.id)).where(and_(*conditions))
        )
        total = total_result.scalar() or 0

        dimension_result = await self.db.execute(
            select(ModelEvaluation.dimension, func.count(ModelEvaluation.id).label('count'))
            .where(and_(*conditions))
            .group_by(ModelEvaluation.dimension)
        )
        by_dimension = {}
        for row in dimension_result:
            by_dimension[row.dimension or "general"] = {"count": row.count}

        type_result = await self.db.execute(
            select(ModelEvaluation.evaluation_type, func.count(ModelEvaluation.id).label('count'))
            .where(and_(*conditions))
            .group_by(ModelEvaluation.evaluation_type)
        )
        by_type = {row.evaluation_type: row.count for row in type_result}

        passed_result = await self.db.execute(
            select(func.count(ModelEvaluation.id)).where(
                and_(*conditions, ModelEvaluation.passed == True)  # noqa: E712
            )
        )
        passed_count = passed_result.scalar() or 0

        latest_result = await self.db.execute(
            select(func.max(ModelEvaluation.evaluation_date)).where(and_(*conditions))
        )
        latest_date = latest_result.scalar()

        return {
            "total": total,
            "by_dimension": by_dimension,
            "by_type": by_type,
            "passed_count": passed_count,
            "latest_date": latest_date,
        }

    async def list_model_evaluations(
        self,
        company_uuid: UUID,
        model_version: str | None = None,
        evaluation_type: str | None = None,
        dimension: str | None = None,
        passed: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ModelEvaluation], int]:
        conditions = [ModelEvaluation.company_id == company_uuid]
        if model_version:
            conditions.append(ModelEvaluation.model_version == model_version)
        if evaluation_type:
            conditions.append(ModelEvaluation.evaluation_type == evaluation_type)
        if dimension:
            conditions.append(ModelEvaluation.dimension == dimension)
        if passed is not None:
            conditions.append(ModelEvaluation.passed == passed)

        query = (
            # TENANT-EXEMPT: observability per-company log query uses conditions=[Model.company_id==X] + and_(*conditions); AST sensor cannot trace dynamic builder; T-RATCHET tenant_filter
            select(ModelEvaluation)
            .where(and_(*conditions))
            .order_by(desc(ModelEvaluation.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        evaluations = list(result.scalars().all())

        count_result = await self.db.execute(
            select(func.count(ModelEvaluation.id)).where(and_(*conditions))
        )
        total = count_result.scalar() or 0

        return evaluations, total

    # ── ComplianceControl ─────────────────────────────────────────────────────

    async def get_compliance_summary(
        self,
        company_uuid: UUID,
        framework: str | None = None,
    ) -> dict:
        conditions = [ComplianceControl.company_id == company_uuid]
        if framework:
            conditions.append(ComplianceControl.framework == framework)

        total_result = await self.db.execute(
            select(func.count(ComplianceControl.id)).where(and_(*conditions))
        )
        total = total_result.scalar() or 0

        framework_result = await self.db.execute(
            select(
                ComplianceControl.framework,
                ComplianceControl.status,
                func.count(ComplianceControl.id).label('count'),
            )
            .where(and_(*conditions))
            .group_by(ComplianceControl.framework, ComplianceControl.status)
        )
        by_framework: dict = {}
        for row in framework_result:
            if row.framework not in by_framework:
                by_framework[row.framework] = {}
            by_framework[row.framework][row.status] = row.count

        status_result = await self.db.execute(
            select(ComplianceControl.status, func.count(ComplianceControl.id).label('count'))
            .where(and_(*conditions))
            .group_by(ComplianceControl.status)
        )
        by_status = {row.status: row.count for row in status_result}

        now = datetime.utcnow()
        overdue_result = await self.db.execute(
            select(func.count(ComplianceControl.id)).where(
                and_(*conditions, ComplianceControl.next_review_at < now)
            )
        )
        overdue = overdue_result.scalar() or 0

        upcoming_date = now + timedelta(days=30)
        upcoming_result = await self.db.execute(
            select(func.count(ComplianceControl.id)).where(
                and_(
                    *conditions,
                    ComplianceControl.next_review_at >= now,
                    ComplianceControl.next_review_at <= upcoming_date,
                )
            )
        )
        upcoming = upcoming_result.scalar() or 0

        return {
            "total": total,
            "by_framework": by_framework,
            "by_status": by_status,
            "overdue": overdue,
            "upcoming": upcoming,
        }

    async def list_compliance_controls(
        self,
        company_uuid: UUID,
        framework: str | None = None,
        status_filter: str | None = None,
        risk_level: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ComplianceControl], int]:
        conditions = [ComplianceControl.company_id == company_uuid]
        if framework:
            conditions.append(ComplianceControl.framework == framework)
        if status_filter:
            conditions.append(ComplianceControl.status == status_filter)
        if risk_level:
            conditions.append(ComplianceControl.risk_level == risk_level)

        query = (
            # TENANT-EXEMPT: observability per-company log query uses conditions=[Model.company_id==X] + and_(*conditions); AST sensor cannot trace dynamic builder; T-RATCHET tenant_filter
            select(ComplianceControl)
            .where(and_(*conditions))
            .order_by(ComplianceControl.framework, ComplianceControl.control_id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        controls = list(result.scalars().all())

        count_result = await self.db.execute(
            select(func.count(ComplianceControl.id)).where(and_(*conditions))
        )
        total = count_result.scalar() or 0

        return controls, total

    async def get_compliance_control(
        self, control_uuid: UUID, company_uuid: UUID
    ) -> ComplianceControl | None:
        result = await self.db.execute(
            select(ComplianceControl).where(
                and_(
                    ComplianceControl.id == control_uuid,
                    ComplianceControl.company_id == company_uuid,
                )
            )
        )
        return result.scalar_one_or_none()

    async def update_compliance_control(
        self, control: ComplianceControl, data: dict
    ) -> ComplianceControl:
        for key, value in data.items():
            if hasattr(control, key):
                setattr(control, key, value)
        control.last_reviewed_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(control)
        return control

    # ── Dashboard aggregates ──────────────────────────────────────────────────

    async def get_dashboard_data(self, company_uuid: UUID, start_date: datetime) -> dict:
        ai_total_result = await self.db.execute(
            select(func.count(AIInferenceLog.id)).where(
                and_(
                    AIInferenceLog.company_id == company_uuid,
                    AIInferenceLog.created_at >= start_date,
                )
            )
        )
        ai_total = ai_total_result.scalar() or 0

        data_access_total_result = await self.db.execute(
            select(func.count(DataAccessLog.id)).where(
                and_(
                    DataAccessLog.company_id == company_uuid,
                    DataAccessLog.created_at >= start_date,
                )
            )
        )
        data_access_total = data_access_total_result.scalar() or 0

        active_consents_result = await self.db.execute(
            select(func.count(ConsentRecord.id)).where(
                and_(
                    ConsentRecord.company_id == company_uuid,
                    ConsentRecord.is_active == True,  # noqa: E712
                )
            )
        )
        active_consents = active_consents_result.scalar() or 0

        open_incidents_result = await self.db.execute(
            select(func.count(IncidentReport.id)).where(
                and_(
                    IncidentReport.company_id == company_uuid,
                    IncidentReport.status == "open",
                )
            )
        )
        open_incidents = open_incidents_result.scalar() or 0

        critical_incidents_result = await self.db.execute(
            select(func.count(IncidentReport.id)).where(
                and_(
                    IncidentReport.company_id == company_uuid,
                    IncidentReport.status == "open",
                    IncidentReport.severity == "critical",
                )
            )
        )
        critical_incidents = critical_incidents_result.scalar() or 0

        eval_count_result = await self.db.execute(
            select(func.count(ModelEvaluation.id)).where(
                ModelEvaluation.company_id == company_uuid
            )
        )
        eval_count = eval_count_result.scalar() or 0

        passed_count_result = await self.db.execute(
            select(func.count(ModelEvaluation.id)).where(
                and_(
                    ModelEvaluation.company_id == company_uuid,
                    ModelEvaluation.passed == True,  # noqa: E712
                )
            )
        )
        passed_count = passed_count_result.scalar() or 0

        compliance_total_result = await self.db.execute(
            select(func.count(ComplianceControl.id)).where(
                ComplianceControl.company_id == company_uuid
            )
        )
        compliance_total = compliance_total_result.scalar() or 0

        implemented_result = await self.db.execute(
            select(func.count(ComplianceControl.id)).where(
                and_(
                    ComplianceControl.company_id == company_uuid,
                    ComplianceControl.status == "implemented",
                )
            )
        )
        implemented = implemented_result.scalar() or 0

        return {
            "ai_total": ai_total,
            "data_access_total": data_access_total,
            "active_consents": active_consents,
            "open_incidents": open_incidents,
            "critical_incidents": critical_incidents,
            "eval_count": eval_count,
            "passed_count": passed_count,
            "compliance_total": compliance_total,
            "implemented": implemented,
        }

    # ── BiasAuditReport ───────────────────────────────────────────────────────

    async def get_latest_bias_audit(self, company_uuid: UUID) -> BiasAuditReport | None:
        result = await self.db.execute(
            select(BiasAuditReport)
            .where(BiasAuditReport.company_id == company_uuid)
            .order_by(desc(BiasAuditReport.audit_date))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_bias_audit_summary(self, company_uuid: UUID) -> dict:
        total_result = await self.db.execute(
            select(func.count(BiasAuditReport.id)).where(
                BiasAuditReport.company_id == company_uuid
            )
        )
        total = total_result.scalar() or 0

        audit_type_result = await self.db.execute(
            select(BiasAuditReport.audit_type, func.count(BiasAuditReport.id).label('count'))
            .where(BiasAuditReport.company_id == company_uuid)
            .group_by(BiasAuditReport.audit_type)
        )
        by_audit_type = {row.audit_type: row.count for row in audit_type_result}

        public_result = await self.db.execute(
            select(func.count(BiasAuditReport.id)).where(
                and_(
                    BiasAuditReport.company_id == company_uuid,
                    BiasAuditReport.is_public == True,  # noqa: E712
                )
            )
        )
        public_count = public_result.scalar() or 0

        latest_result = await self.db.execute(
            select(BiasAuditReport)
            .where(BiasAuditReport.company_id == company_uuid)
            .order_by(desc(BiasAuditReport.audit_date))
            .limit(1)
        )
        latest_audit = latest_result.scalar_one_or_none()

        frameworks_result = await self.db.execute(
            select(BiasAuditReport.compliance_frameworks).where(
                BiasAuditReport.company_id == company_uuid
            )
        )
        all_frameworks: set = set()
        for row in frameworks_result:
            if row.compliance_frameworks:
                all_frameworks.update(row.compliance_frameworks)

        return {
            "total": total,
            "by_audit_type": by_audit_type,
            "public_count": public_count,
            "latest_audit": latest_audit,
            "all_frameworks": all_frameworks,
        }

    async def list_bias_audits(
        self,
        company_uuid: UUID,
        audit_type: str | None = None,
        is_public: bool | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[BiasAuditReport], int]:
        conditions = [BiasAuditReport.company_id == company_uuid]
        if audit_type:
            conditions.append(BiasAuditReport.audit_type == audit_type)
        if is_public is not None:
            conditions.append(BiasAuditReport.is_public == is_public)
        if start_date:
            conditions.append(BiasAuditReport.audit_date >= start_date.date())
        if end_date:
            conditions.append(BiasAuditReport.audit_date <= end_date.date())

        query = (
            # TENANT-EXEMPT: observability per-company log query uses conditions=[Model.company_id==X] + and_(*conditions); AST sensor cannot trace dynamic builder; T-RATCHET tenant_filter
            select(BiasAuditReport)
            .where(and_(*conditions))
            .order_by(desc(BiasAuditReport.audit_date))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        audits = list(result.scalars().all())

        count_result = await self.db.execute(
            select(func.count(BiasAuditReport.id)).where(and_(*conditions))
        )
        total = count_result.scalar() or 0

        return audits, total

    async def get_bias_audit(self, audit_uuid: UUID, company_uuid: UUID) -> BiasAuditReport | None:
        result = await self.db.execute(
            select(BiasAuditReport).where(
                and_(
                    BiasAuditReport.id == audit_uuid,
                    BiasAuditReport.company_id == company_uuid,
                )
            )
        )
        return result.scalar_one_or_none()

    async def create_bias_audit(self, data: dict) -> BiasAuditReport:
        audit = BiasAuditReport(**data)
        self.db.add(audit)
        await self.db.commit()
        await self.db.refresh(audit)
        return audit

    async def update_bias_audit(self, audit: BiasAuditReport, data: dict) -> BiasAuditReport:
        for key, value in data.items():
            if hasattr(audit, key):
                setattr(audit, key, value)
        await self.db.commit()
        await self.db.refresh(audit)
        return audit
