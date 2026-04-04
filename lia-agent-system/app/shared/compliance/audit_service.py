"""
Audit Service for AI Governance.

This service provides comprehensive audit logging for all AI decisions
made by LIA agents, ensuring transparency, accountability, and LGPD compliance.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.audit_log import AuditLog, DecisionType
import uuid

logger = logging.getLogger(__name__)

DECISION_TYPE_MAPPING = {
    "cv_screening": DecisionType.SCORE_CANDIDATE,
    "screen_candidate": DecisionType.SCORE_CANDIDATE,
    "wsi_evaluation": DecisionType.SCORE_CANDIDATE,
    "calculate_wsi": DecisionType.SCORE_CANDIDATE,
    "quick_screening": DecisionType.SCORE_CANDIDATE,
    "complete_interview": DecisionType.SCORE_CANDIDATE,
    "screening_evaluation": DecisionType.SCORE_CANDIDATE,
    "search_candidates": DecisionType.SCORE_CANDIDATE,
    "proceed_to_next_stage": DecisionType.MOVE_STAGE,
    "proceed_to_wsi": DecisionType.MOVE_STAGE,
    "reject": DecisionType.REJECT_CANDIDATE,
    "rejected": DecisionType.REJECT_CANDIDATE,
    "approve": DecisionType.APPROVE_CANDIDATE,
    "approved": DecisionType.APPROVE_CANDIDATE,
    "generate_jd": DecisionType.GENERATE_FEEDBACK,
    "generate_wsi_questions": DecisionType.GENERATE_FEEDBACK,
}

PROTECTED_CRITERIA = [
    "age",
    "gender",
    "ethnicity",
    "marital_status",
    "photo",
    "institution",
    "address",
    "religion",
    "disability",
    "cv_gaps",
]


class AuditService:
    """Service for logging AI decisions with full explainability."""
    
    RETENTION_PERIODS = {
        "score_candidate": 730,
        "approve_candidate": 730,
        "reject_candidate": 730,
        "move_stage": 730,
        "send_message": 1825,
        "schedule_interview": 365,
        "generate_feedback": 730,
    }
    
    async def log_decision(
        self,
        company_id: str,
        agent_name: str,
        decision_type: str,
        action: str,
        decision: str,
        reasoning: List[str],
        criteria_used: List[str],
        candidate_id: Optional[str] = None,
        job_vacancy_id: Optional[str] = None,
        score: Optional[float] = None,
        confidence: Optional[float] = None,
        human_review_required: bool = False,
        criteria_ignored: Optional[List[str]] = None
    ) -> AuditLog:
        """
        Log an AI decision with full context for auditability.
        
        Args:
            company_id: The company/tenant ID
            agent_name: Name of the agent making the decision (e.g., "triagem_curricular")
            decision_type: Type of decision (see DecisionType enum)
            action: Specific action taken
            decision: Result of the decision ("approved", "rejected", "pending_review")
            reasoning: List of reasons for the decision
            criteria_used: List of criteria that were evaluated
            candidate_id: Optional candidate ID if decision relates to a candidate
            job_vacancy_id: Optional job vacancy ID if decision relates to a job
            score: Optional score assigned
            confidence: Optional confidence level (0-1)
            human_review_required: Whether this decision requires human review
            criteria_ignored: List of criteria explicitly ignored (for anti-bias)
            
        Returns:
            Created AuditLog instance
        """
        canonical_type = DECISION_TYPE_MAPPING.get(decision_type.lower())
        if canonical_type is None:
            try:
                canonical_type = DecisionType(decision_type)
            except ValueError:
                logger.warning(f"Unknown decision_type '{decision_type}', defaulting to SCORE_CANDIDATE")
                canonical_type = DecisionType.SCORE_CANDIDATE
        
        final_ignored = set(PROTECTED_CRITERIA)
        if criteria_ignored:
            final_ignored.update(criteria_ignored)
        
        retention_days = self.RETENTION_PERIODS.get(canonical_type.value, 730)
        retention_until = datetime.utcnow() + timedelta(days=retention_days)
        
        async with AsyncSessionLocal() as session:
            audit_log = AuditLog(
                id=str(uuid.uuid4()),
                company_id=company_id,
                agent_name=agent_name,
                decision_type=canonical_type.value,
                action=action,
                decision=decision,
                reasoning=reasoning,
                criteria_used=criteria_used,
                criteria_ignored=list(final_ignored),
                candidate_id=candidate_id,
                job_vacancy_id=job_vacancy_id,
                score=score,
                confidence=confidence,
                human_review_required=human_review_required,
                retention_until=retention_until
            )
            
            session.add(audit_log)
            await session.commit()
            await session.refresh(audit_log)
            
            logger.info(
                f"✅ Audit log created: {agent_name} - {decision_type} -> {decision} "
                f"(candidate: {candidate_id}, job: {job_vacancy_id})"
            )
            return audit_log
    
    async def get_candidate_decisions(
        self,
        company_id: str,
        candidate_id: str,
        job_vacancy_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get all decisions made about a candidate (for explainability).
        
        Args:
            company_id: The company/tenant ID
            candidate_id: The candidate ID
            job_vacancy_id: Optional job vacancy ID to filter by
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            Dictionary with audit logs and pagination info
        """
        from sqlalchemy import func
        
        async with AsyncSessionLocal() as session:
            where_conditions = [
                AuditLog.company_id == company_id,
                AuditLog.candidate_id == candidate_id
            ]
            
            if job_vacancy_id:
                where_conditions.append(AuditLog.job_vacancy_id == job_vacancy_id)
            
            count_query = select(func.count()).select_from(AuditLog).where(and_(*where_conditions))
            count_result = await session.execute(count_query)
            total = count_result.scalar() or 0
            
            data_query = (
                select(AuditLog)
                .where(and_(*where_conditions))
                .order_by(desc(AuditLog.created_at))
                .limit(limit)
                .offset(offset)
            )
            
            result = await session.execute(data_query)
            audit_logs = result.scalars().all()
            
            logger.info(f"📋 Retrieved {len(audit_logs)} audit logs for candidate {candidate_id}")
            
            return {
                "audit_logs": [log.to_dict() for log in audit_logs],
                "total": total,
                "limit": limit,
                "offset": offset,
            }
    
    async def get_decisions_by_agent(
        self,
        company_id: str,
        agent_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get decisions made by a specific agent.
        
        Args:
            company_id: The company/tenant ID
            agent_name: Name of the agent
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum number of results
            
        Returns:
            List of AuditLog instances
        """
        async with AsyncSessionLocal() as session:
            where_conditions = [
                AuditLog.company_id == company_id,
                AuditLog.agent_name == agent_name
            ]
            
            if start_date:
                where_conditions.append(AuditLog.created_at >= start_date)
            if end_date:
                where_conditions.append(AuditLog.created_at <= end_date)
            
            query = (
                select(AuditLog)
                .where(and_(*where_conditions))
                .order_by(desc(AuditLog.created_at))
                .limit(limit)
            )
            
            result = await session.execute(query)
            audit_logs = result.scalars().all()
            
            logger.info(f"📋 Retrieved {len(audit_logs)} audit logs for agent {agent_name}")
            return list(audit_logs)
    
    async def log_output(
        self,
        *,
        company_id: str,
        session_id: str,
        agent_used: str,
        input_text: str,
        output_text: str,
        action_executed: str = None,
        candidate_id: str = None,
        job_vacancy_id: str = None,
        fairness_flags: list = None,
    ) -> None:
        """
        Registra a saida conversacional da LIA para auditoria completa.

        Chamado pelo MainOrchestrator apos cada resposta que envolva
        candidate_id ou job_vacancy_id (acoes de alto impacto).

        Compliance: EU AI Act Art. 13, LGPD Art. 18, CLT Art. 373-A.
        """
        retention_until = datetime.utcnow() + timedelta(days=1825)  # 5 anos

        async with AsyncSessionLocal() as session:
            audit_log = AuditLog(
                id=str(uuid.uuid4()),
                company_id=company_id,
                session_id=session_id,
                agent_name=agent_used,
                agent_used=agent_used,
                decision_type="conversational_output",
                action=action_executed or "lia_response",
                decision="responded",
                candidate_id=candidate_id,
                job_vacancy_id=job_vacancy_id,
                input_text=input_text[:4000] if input_text else None,
                output_text=output_text[:8000] if output_text else None,
                fairness_flags=fairness_flags or [],
                reasoning=[],
                criteria_used=[],
                criteria_ignored=list(PROTECTED_CRITERIA),
                human_review_required=False,
                retention_until=retention_until,
            )
            session.add(audit_log)
            await session.commit()

            logger.info(
                "Output audit logged: agent=%s session=%s candidate=%s",
                agent_used, session_id, candidate_id
            )

        async def record_human_review(
        self,
        audit_log_id: str,
        reviewed_by: str,
        override: Optional[str] = None
    ) -> Optional[AuditLog]:
        """
        Record when a human reviews/overrides an AI decision.
        
        Args:
            audit_log_id: ID of the audit log to update
            reviewed_by: User ID of the reviewer
            override: Optional new decision if human overrides AI
            
        Returns:
            Updated AuditLog instance or None if not found
        """
        async with AsyncSessionLocal() as session:
            query = select(AuditLog).where(AuditLog.id == audit_log_id)
            result = await session.execute(query)
            audit_log = result.scalar_one_or_none()
            
            if audit_log:
                audit_log.human_reviewed_by = reviewed_by
                audit_log.human_reviewed_at = datetime.utcnow()
                audit_log.human_override = override
                
                await session.commit()
                await session.refresh(audit_log)
                
                logger.info(
                    f"✅ Human review recorded for audit log {audit_log_id} "
                    f"by {reviewed_by}" + (f" (override: {override})" if override else "")
                )
                return audit_log
            else:
                logger.warning(f"⚠️  Audit log not found: {audit_log_id}")
                return None
    
    async def get_pending_reviews(
        self,
        company_id: str,
        limit: int = 50
    ) -> List[AuditLog]:
        """
        Get decisions that require human review but haven't been reviewed yet.
        
        Args:
            company_id: The company/tenant ID
            limit: Maximum number of results
            
        Returns:
            List of AuditLog instances pending review
        """
        async with AsyncSessionLocal() as session:
            query = (
                select(AuditLog)
                .where(
                    and_(
                        AuditLog.company_id == company_id,
                        AuditLog.human_review_required == True,
                        AuditLog.human_reviewed_at.is_(None)
                    )
                )
                .order_by(desc(AuditLog.created_at))
                .limit(limit)
            )
            
            result = await session.execute(query)
            audit_logs = result.scalars().all()
            
            logger.info(f"📋 Found {len(audit_logs)} pending reviews for company {company_id}")
            return list(audit_logs)
    
    async def get_decision_statistics(
        self,
        company_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about AI decisions for governance reporting.
        
        Args:
            company_id: The company/tenant ID
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dictionary with decision statistics
        """
        from sqlalchemy import func
        
        async with AsyncSessionLocal() as session:
            where_conditions = [AuditLog.company_id == company_id]
            
            if start_date:
                where_conditions.append(AuditLog.created_at >= start_date)
            if end_date:
                where_conditions.append(AuditLog.created_at <= end_date)
            
            total_query = select(func.count()).select_from(AuditLog).where(and_(*where_conditions))
            total_result = await session.execute(total_query)
            total_decisions = total_result.scalar() or 0
            
            by_type_query = (
                select(AuditLog.decision_type, func.count(AuditLog.id))
                .where(and_(*where_conditions))
                .group_by(AuditLog.decision_type)
            )
            by_type_result = await session.execute(by_type_query)
            by_type = dict(by_type_result.fetchall())
            
            by_decision_query = (
                select(AuditLog.decision, func.count(AuditLog.id))
                .where(and_(*where_conditions))
                .group_by(AuditLog.decision)
            )
            by_decision_result = await session.execute(by_decision_query)
            by_decision = dict(by_decision_result.fetchall())
            
            reviewed_query = (
                select(func.count())
                .select_from(AuditLog)
                .where(
                    and_(
                        *where_conditions,
                        AuditLog.human_reviewed_at.isnot(None)
                    )
                )
            )
            reviewed_result = await session.execute(reviewed_query)
            human_reviewed = reviewed_result.scalar() or 0
            
            overridden_query = (
                select(func.count())
                .select_from(AuditLog)
                .where(
                    and_(
                        *where_conditions,
                        AuditLog.human_override.isnot(None)
                    )
                )
            )
            overridden_result = await session.execute(overridden_query)
            human_overridden = overridden_result.scalar() or 0
            
            return {
                "total_decisions": total_decisions,
                "by_type": by_type,
                "by_decision": by_decision,
                "human_reviewed": human_reviewed,
                "human_overridden": human_overridden,
                "override_rate": (human_overridden / human_reviewed * 100) if human_reviewed > 0 else 0,
            }


audit_service = AuditService()
