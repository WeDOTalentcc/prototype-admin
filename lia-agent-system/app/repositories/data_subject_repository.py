"""
Data Subject domain repository — all SQLAlchemy operations for data_subject_requests.py.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.observability import DataSubjectRequest

import logging
logger = logging.getLogger(__name__)


class DsrExecutorFailedError(Exception):
    """Raised when critical DSR executor fails — prevents silent compliance theater
    where status=completed but PII still live (WT-2022 P2.1 fix)."""
    pass


class DataSubjectRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    async def create_request(self, data: dict) -> DataSubjectRequest:
        """Create a new DataSubjectRequest and persist it."""
        request = DataSubjectRequest(
            company_id=data["company_id"],
            request_type=data["request_type"],
            status=data["status"],
            subject_name=data.get("subject_name"),
            subject_email=data.get("subject_email"),
            subject_phone=data.get("subject_phone"),
            subject_identifier=data.get("subject_identifier"),
            description=data.get("description"),
            source_channel=data["source_channel"],
            data_categories=data.get("data_categories", []),
            sla_deadline=data.get("sla_deadline"),
            audit_trail=data.get("audit_trail", []),
        )
        self.db.add(request)
        await self.db.commit()
        await self.db.refresh(request)
        return request

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get_by_id(self, request_id: uuid.UUID) -> DataSubjectRequest | None:
        """Fetch a request by primary key (no company filter — public tracking)."""
        result = await self.db.execute(
            select(DataSubjectRequest).where(DataSubjectRequest.id == request_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_and_company(
        self, request_id: uuid.UUID, company_id: uuid.UUID
    ) -> DataSubjectRequest | None:
        """Fetch a request by id scoped to a company (authenticated endpoints)."""
        result = await self.db.execute(
            select(DataSubjectRequest).where(
                and_(
                    DataSubjectRequest.id == request_id,
                    DataSubjectRequest.company_id == company_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_requests(
        self,
        company_id: uuid.UUID,
        status_filter: str | None,
        request_type: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
        subject_email: str | None,
        skip: int,
        limit: int,
    ) -> tuple[list[DataSubjectRequest], int]:
        """List requests with optional filters; returns (rows, total_count)."""
        conditions = [DataSubjectRequest.company_id == company_id]

        if status_filter:
            conditions.append(DataSubjectRequest.status == status_filter)
        if request_type:
            conditions.append(DataSubjectRequest.request_type == request_type)
        if date_from:
            conditions.append(DataSubjectRequest.created_at >= date_from)
        if date_to:
            conditions.append(DataSubjectRequest.created_at <= date_to)
        if subject_email:
            conditions.append(DataSubjectRequest.subject_email.ilike(f"%{subject_email}%"))

        query = (
            select(DataSubjectRequest)
            .where(and_(*conditions))
            .order_by(desc(DataSubjectRequest.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        requests = list(result.scalars().all())

        count_result = await self.db.execute(
            select(func.count(DataSubjectRequest.id)).where(and_(*conditions))
        )
        total = count_result.scalar() or 0

        return requests, total

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    async def get_stats(self, company_id: uuid.UUID) -> dict:
        """Return aggregated statistics for all DSR endpoints."""
        total_result = await self.db.execute(
            select(func.count(DataSubjectRequest.id)).where(
                DataSubjectRequest.company_id == company_id
            )
        )
        total = total_result.scalar() or 0

        status_counts: dict[str, int] = {}
        for status_val in ["pending", "in_review", "processing", "completed", "rejected", "cancelled"]:
            count_result = await self.db.execute(
                select(func.count(DataSubjectRequest.id)).where(
                    and_(
                        DataSubjectRequest.company_id == company_id,
                        DataSubjectRequest.status == status_val,
                    )
                )
            )
            status_counts[status_val] = count_result.scalar() or 0

        overdue_result = await self.db.execute(
            select(func.count(DataSubjectRequest.id)).where(
                and_(
                    DataSubjectRequest.company_id == company_id,
                    DataSubjectRequest.status.in_(["pending", "in_review", "processing"]),
                    DataSubjectRequest.sla_deadline < datetime.utcnow(),
                )
            )
        )
        overdue = overdue_result.scalar() or 0

        sla_met_result = await self.db.execute(
            select(func.count(DataSubjectRequest.id)).where(
                and_(
                    DataSubjectRequest.company_id == company_id,
                    DataSubjectRequest.sla_met,
                )
            )
        )
        sla_met = sla_met_result.scalar() or 0

        type_counts: dict[str, int] = {}
        for type_val in ["access", "correction", "deletion", "portability", "objection", "restriction", "explanation"]:
            type_result = await self.db.execute(
                select(func.count(DataSubjectRequest.id)).where(
                    and_(
                        DataSubjectRequest.company_id == company_id,
                        DataSubjectRequest.request_type == type_val,
                    )
                )
            )
            type_counts[type_val] = type_result.scalar() or 0

        channel_counts: dict[str, int] = {}
        for channel_val in ["portal", "email", "whatsapp", "phone", "in_person", "api"]:
            channel_result = await self.db.execute(
                select(func.count(DataSubjectRequest.id)).where(
                    and_(
                        DataSubjectRequest.company_id == company_id,
                        DataSubjectRequest.source_channel == channel_val,
                    )
                )
            )
            channel_counts[channel_val] = channel_result.scalar() or 0

        return {
            "total": total,
            "status_counts": status_counts,
            "overdue": overdue,
            "sla_met": sla_met,
            "type_counts": type_counts,
            "channel_counts": channel_counts,
        }

    # ------------------------------------------------------------------
    # Mutations (assign, verify, process, complete, reject)
    # ------------------------------------------------------------------

    async def assign_request(
        self,
        request: DataSubjectRequest,
        assigned_to: uuid.UUID,
        audit_entry: dict,
    ) -> DataSubjectRequest:
        """Assign request to a user; advances status from pending to in_review."""
        request.assigned_to = assigned_to
        if request.status == "pending":
            request.status = "in_review"
        request.audit_trail = (request.audit_trail or []) + [audit_entry]
        await self.db.commit()
        await self.db.refresh(request)
        return request

    async def verify_identity(
        self,
        request: DataSubjectRequest,
        verified: bool,
        method: str,
        audit_entry: dict,
    ) -> DataSubjectRequest:
        """Record identity verification result."""
        request.identity_verified = verified
        request.identity_verification_method = method
        request.identity_verified_at = datetime.utcnow() if verified else None
        request.audit_trail = (request.audit_trail or []) + [audit_entry]
        await self.db.commit()
        await self.db.refresh(request)
        return request

    async def start_processing(
        self,
        request: DataSubjectRequest,
        audit_entry: dict,
    ) -> DataSubjectRequest:
        """Transition request to processing state."""
        request.status = "processing"
        request.audit_trail = (request.audit_trail or []) + [audit_entry]
        await self.db.commit()
        await self.db.refresh(request)
        return request

    async def _execute_dsr_side_effect(self, request: DataSubjectRequest) -> dict:
        """WT-2022 P2.1: Execute real side-effects per DSR request_type.

        Fixes compliance theater bug: complete_request previously only set
        status='completed' without invoking any executor. ANPD audit would
        see status=completed with PII still live, violating LGPD Art. 18 VI
        (deletion), Art. 18 V (portability), Art. 18 IV (restriction).

        Returns audit-friendly dict with execution status. Raises
        DsrExecutorFailedError if CRITICAL executor (deletion) fails - to
        prevent silent completion of deletion requests when no candidate
        is found (which would mask ANPD non-compliance).

        For request_types without automated executor (correction, restriction,
        objection, explanation), records 'requires_admin_followup' flag in
        audit_trail - admin must apply manually but audit trail is faithful.
        """
        import hashlib

        side_effect: dict = {
            "executor_run_at": datetime.utcnow().isoformat(),
            "request_type": request.request_type,
        }

        # Find candidate by email_hash (Candidate.email_hash is SHA-256 indexed)
        candidate = None
        try:
            from app.models.candidate import Candidate
            email_hash = hashlib.sha256(
                request.subject_email.lower().encode()
            ).hexdigest()
            result = await self.db.execute(
                select(Candidate).where(
                    and_(
                        Candidate.email_hash == email_hash,
                        Candidate.company_id == request.company_id,
                    )
                )
            )
            candidate = result.scalar_one_or_none()
        except Exception as exc:
            side_effect["candidate_lookup_error"] = str(exc)[:200]
            logger.warning(
                "DSR candidate lookup failed for request %s: %s",
                request.id, exc, exc_info=True,
            )

        side_effect["candidate_found"] = candidate is not None
        side_effect["candidate_id"] = str(candidate.id) if candidate else None

        rt = request.request_type

        if rt == "deletion":
            # CRITICAL: LGPD Art. 18 VI fail-loud
            if not candidate:
                raise DsrExecutorFailedError(
                    f"DSR deletion request {request.id}: no candidate found "
                    f"matching subject_email - manual investigation required "
                    f"before marking completed (LGPD Art. 18 VI)"
                )
            try:
                from app.domains.lgpd.services.lgpd_cleanup_service import (
                    schedule_deletion_for_candidate,
                )
                deletion_at = await schedule_deletion_for_candidate(
                    self.db, str(candidate.id), reason="lgpd_dsr_deletion"
                )
                side_effect["action"] = "deletion_scheduled"
                side_effect["scheduled_deletion_at"] = deletion_at.isoformat()

                # Fase 4 — LGPD Art. 18 VI: cascade erasure de perfis Pearch descobertos
                # ExternalCandidateProfile não tem FK para Candidate; link é por email.
                # Deletar imediatamente (não agendar): usuário pediu erasure explicitamente.
                try:
                    import sqlalchemy as sa
                    from lia_models.candidate import ExternalCandidateProfile
                    subject_email = (request.subject_email or "").strip().lower()
                    if subject_email:
                        await self.db.execute(
                            sa.delete(ExternalCandidateProfile).where(
                                sa.and_(
                                    sa.func.lower(ExternalCandidateProfile.email) == subject_email,
                                    ExternalCandidateProfile.company_id == str(request.company_id),
                                )
                            )
                        )
                        await self.db.commit()
                        side_effect["pearch_profiles_erased"] = True
                except Exception as _erase_exc:
                    side_effect["pearch_profiles_erased"] = False
                    side_effect["pearch_erase_warning"] = str(_erase_exc)[:200]
                    logger.warning(
                        "Erasure cascade: ExternalCandidateProfile delete failed (non-fatal): %s",
                        _erase_exc,
                    )

            except Exception as exc:
                raise DsrExecutorFailedError(
                    f"DSR deletion executor failed for {request.id}: {exc}"
                ) from exc

        elif rt in ("access", "portability"):
            if not candidate:
                side_effect["action"] = "no_data_to_export"
                side_effect["warning"] = "candidate_not_found_matching_subject_email"
            else:
                try:
                    from app.domains.lgpd.services.dsr_export_service import (
                        DsrExportService,
                    )
                    export_svc = DsrExportService()
                    data = await export_svc.export_candidate_data(
                        self.db,
                        str(candidate.id),
                        str(request.company_id),
                        request.subject_email,
                    )
                    side_effect["action"] = f"data_{rt}_exported"
                    side_effect["payload_size_bytes"] = len(str(data))
                except Exception as exc:
                    side_effect["action"] = f"{rt}_export_failed"
                    side_effect["error"] = str(exc)[:200]
                    logger.error(
                        "DSR export failed for request %s: %s",
                        request.id, exc, exc_info=True,
                    )

        elif rt in ("correction", "restriction", "objection", "explanation"):
            # No automated executor - admin must apply manually
            side_effect["action"] = f"{rt}_pending_manual_apply"
            side_effect["requires_admin_followup"] = True
            side_effect["warning"] = (
                f"DSR request_type '{rt}' has no automated executor. "
                "Audit trail shows status=completed but processing change "
                "requires manual admin application (LGPD compliance gap)."
            )
            # P1-W4-12: Log urgente para rastreabilidade admin.
            # Dado pode persistir incorreto/irrestrito ate intervencao manual
            # (LGPD Art. 18 III correcao / Art. 18 IV bloqueio / Art. 18 V portabilidade).
            try:
                from app.shared.compliance.audit_service import AuditService
                _dsr_audit_svc = AuditService()
                _sla_str = str(request.sla_deadline) if request.sla_deadline else "nao definido"
                await _dsr_audit_svc.log_decision(
                    company_id=str(request.company_id),
                    agent_name="data_subject_repository",
                    decision_type="dsr_manual_followup_required",
                    action=f"dsr_{rt}_completed_needs_admin",
                    decision="admin_followup_required",
                    reasoning=[
                        f"DSR type={rt} marcado completed sem executor automatico.",
                        "Dado pode persistir incorreto/irrestrito ate acao manual do admin.",
                        "LGPD Art. 18 III/IV/V: intervencao humana obrigatoria.",
                        f"SLA deadline: {_sla_str}",
                    ],
                    criteria_used=["lgpd_art_18_iii_iv", "dsr_manual_followup", "admin_required"],
                    human_review_required=True,
                )
                logger.info(
                    "[DSR] P1-W4-12 audit log criado: request_id=%s type=%s company=%s",
                    request.id, rt, request.company_id,
                )
            except Exception as _dsr_audit_err:
                logger.warning(
                    "[DSR] P1-W4-12 audit log falhou (non-blocking): %s",
                    _dsr_audit_err,
                )

        else:
            side_effect["action"] = "unknown_request_type"
            side_effect["error"] = f"Unknown request_type: {rt}"

        return side_effect

    async def complete_request(
        self,
        request: DataSubjectRequest,
        response: str,
        evidence_files: list,
        audit_entry: dict,
    ) -> DataSubjectRequest:
        """Mark request as completed with response.

        WT-2022 P2.1 fix: invokes _execute_dsr_side_effect FIRST to ensure
        side-effect (deletion, export, etc.) is actually executed.
        Raises DsrExecutorFailedError if deletion can't be executed.
        Endpoint catches and returns 500 - prevents silent compliance theater.
        """
        # WT-2022 P2.1: Execute side-effect BEFORE marking completed
        side_effect_result = await self._execute_dsr_side_effect(request)
        audit_entry["side_effect"] = side_effect_result

        now = datetime.utcnow()
        request.status = "completed"
        request.response = response
        request.completed_at = now
        request.evidence_files = evidence_files
        request.sla_met = now <= request.sla_deadline if request.sla_deadline else True
        request.audit_trail = (request.audit_trail or []) + [audit_entry]
        await self.db.commit()
        await self.db.refresh(request)
        return request

    async def reject_request(
        self,
        request: DataSubjectRequest,
        rejection_reason: str,
        audit_entry: dict,
    ) -> DataSubjectRequest:
        """Reject request with a stated reason."""
        now = datetime.utcnow()
        request.status = "rejected"
        request.rejection_reason = rejection_reason
        request.completed_at = now
        request.sla_met = now <= request.sla_deadline if request.sla_deadline else True
        request.audit_trail = (request.audit_trail or []) + [audit_entry]
        await self.db.commit()
        await self.db.refresh(request)
        return request

    # ------------------------------------------------------------------
    # Rollback helper (used by controller exception handlers)
    # ------------------------------------------------------------------

    async def rollback(self) -> None:
        await self.db.rollback()
