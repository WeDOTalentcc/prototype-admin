"""
Calibration Service - Service for managing the calibration loop.

This service handles:
- Recording implicit feedback (stage changes, overrides)
- Recording explicit feedback (thumbs up/down)
- Analyzing divergences between LIA and recruiter decisions
- Generating calibration suggestions
- Applying approved weight adjustments
"""
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import desc

from app.models.calibration import (
    CalibrationEvent,
    CalibrationSuggestion,
    CalibrationWeight,
    FeedbackType,
)


class CalibrationService:
    """Service for managing calibration loop operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def record_explicit_feedback(
        self,
        candidate_id: str,
        job_id: str | None,
        user_id: str,
        agrees_with_lia: bool,
        lia_score: float | None = None,
        lia_recommendation: str | None = None,
        feedback_reason: str | None = None,
        context: dict[str, Any] | None = None
    ) -> CalibrationEvent:
        """Record explicit feedback (thumbs up/down) from recruiter."""
        event = CalibrationEvent(
            id=str(uuid.uuid4()),
            feedback_type=FeedbackType.EXPLICIT_AGREE if agrees_with_lia else FeedbackType.EXPLICIT_DISAGREE,
            candidate_id=candidate_id,
            job_id=job_id,
            user_id=user_id,
            lia_score=lia_score,
            lia_recommendation=lia_recommendation,
            feedback_reason=feedback_reason,
            score_delta=0 if agrees_with_lia else (-10 if lia_score and lia_score > 70 else 10),
            context=context or {},
            created_at=datetime.utcnow()
        )
        
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        
        return event
    
    async def record_implicit_feedback(
        self,
        candidate_id: str,
        job_id: str,
        user_id: str,
        action: str,
        stage_from: str | None = None,
        stage_to: str | None = None,
        lia_score: float | None = None,
        lia_ranking: int | None = None,
        context: dict[str, Any] | None = None
    ) -> CalibrationEvent:
        """Record implicit feedback from recruiter actions."""
        if action == "advance":
            feedback_type = FeedbackType.IMPLICIT_ADVANCE
            score_delta = 5 if lia_score and lia_score < 60 else 0
        elif action == "reject":
            feedback_type = FeedbackType.IMPLICIT_REJECT
            score_delta = -5 if lia_score and lia_score > 70 else 0
        else:
            feedback_type = FeedbackType.IMPLICIT_OVERRIDE
            score_delta = 0
        
        event = CalibrationEvent(
            id=str(uuid.uuid4()),
            feedback_type=feedback_type,
            candidate_id=candidate_id,
            job_id=job_id,
            user_id=user_id,
            lia_score=lia_score,
            lia_ranking=lia_ranking,
            recruiter_action=action,
            recruiter_stage_from=stage_from,
            recruiter_stage_to=stage_to,
            score_delta=score_delta,
            context=context or {},
            created_at=datetime.utcnow()
        )
        
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        
        return event
    
    async def record_post_hire_feedback(
        self,
        candidate_id: str,
        job_id: str,
        user_id: str,
        success: bool,
        lia_score: float | None = None,
        feedback_reason: str | None = None,
        context: dict[str, Any] | None = None
    ) -> CalibrationEvent:
        """Record post-hire outcome feedback."""
        event = CalibrationEvent(
            id=str(uuid.uuid4()),
            feedback_type=FeedbackType.POST_HIRE_SUCCESS if success else FeedbackType.POST_HIRE_FAILURE,
            candidate_id=candidate_id,
            job_id=job_id,
            user_id=user_id,
            lia_score=lia_score,
            feedback_reason=feedback_reason,
            score_delta=15 if success else -15,
            context=context or {},
            created_at=datetime.utcnow()
        )
        
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        
        return event
    
    async def get_divergences(
        self,
        days: int = 30,
        min_score_delta: float = 5.0,
        limit: int = 20
    ) -> list[dict[str, Any]]:
        """Get recent divergences between LIA and recruiter decisions."""
        since = datetime.utcnow() - timedelta(days=days)
        
        stmt = select(CalibrationEvent).where(
            and_(
                CalibrationEvent.created_at >= since,
                or_(
                    CalibrationEvent.feedback_type == FeedbackType.EXPLICIT_DISAGREE,
                    and_(
                        CalibrationEvent.feedback_type == FeedbackType.IMPLICIT_REJECT,
                        CalibrationEvent.lia_score > 70
                    ),
                    and_(
                        CalibrationEvent.feedback_type == FeedbackType.IMPLICIT_ADVANCE,
                        CalibrationEvent.lia_score < 60
                    )
                )
            )
        ).order_by(desc(CalibrationEvent.created_at)).limit(limit)
        
        result = await self.db.execute(stmt)
        events = result.scalars().all()
        
        divergences = []
        for event in events:
            divergences.append({
                "id": event.id,
                "type": event.feedback_type.value,
                "candidate_id": event.candidate_id,
                "job_id": event.job_id,
                "lia_score": event.lia_score,
                "recruiter_action": event.recruiter_action,
                "stage_from": event.recruiter_stage_from,
                "stage_to": event.recruiter_stage_to,
                "feedback_reason": event.feedback_reason,
                "score_delta": event.score_delta,
                "created_at": event.created_at.isoformat() if event.created_at else None
            })
        
        return divergences
    
    async def get_calibration_stats(self, days: int = 30) -> dict[str, Any]:
        """Get calibration statistics for the dashboard."""
        since = datetime.utcnow() - timedelta(days=days)
        
        total_stmt = select(func.count(CalibrationEvent.id)).where(
            CalibrationEvent.created_at >= since
        )
        total_result = await self.db.execute(total_stmt)
        total_events = total_result.scalar() or 0
        
        agree_stmt = select(func.count(CalibrationEvent.id)).where(
            and_(
                CalibrationEvent.created_at >= since,
                CalibrationEvent.feedback_type == FeedbackType.EXPLICIT_AGREE
            )
        )
        agree_result = await self.db.execute(agree_stmt)
        explicit_agree = agree_result.scalar() or 0
        
        disagree_stmt = select(func.count(CalibrationEvent.id)).where(
            and_(
                CalibrationEvent.created_at >= since,
                CalibrationEvent.feedback_type == FeedbackType.EXPLICIT_DISAGREE
            )
        )
        disagree_result = await self.db.execute(disagree_stmt)
        explicit_disagree = disagree_result.scalar() or 0
        
        advances_stmt = select(func.count(CalibrationEvent.id)).where(
            and_(
                CalibrationEvent.created_at >= since,
                CalibrationEvent.feedback_type == FeedbackType.IMPLICIT_ADVANCE
            )
        )
        advances_result = await self.db.execute(advances_stmt)
        implicit_advances = advances_result.scalar() or 0
        
        rejects_stmt = select(func.count(CalibrationEvent.id)).where(
            and_(
                CalibrationEvent.created_at >= since,
                CalibrationEvent.feedback_type == FeedbackType.IMPLICIT_REJECT
            )
        )
        rejects_result = await self.db.execute(rejects_stmt)
        implicit_rejects = rejects_result.scalar() or 0
        
        high_score_rejects_stmt = select(func.count(CalibrationEvent.id)).where(
            and_(
                CalibrationEvent.created_at >= since,
                CalibrationEvent.feedback_type == FeedbackType.IMPLICIT_REJECT,
                CalibrationEvent.lia_score > 70
            )
        )
        high_score_result = await self.db.execute(high_score_rejects_stmt)
        high_score_rejects = high_score_result.scalar() or 0
        
        low_score_advances_stmt = select(func.count(CalibrationEvent.id)).where(
            and_(
                CalibrationEvent.created_at >= since,
                CalibrationEvent.feedback_type == FeedbackType.IMPLICIT_ADVANCE,
                CalibrationEvent.lia_score < 60
            )
        )
        low_score_result = await self.db.execute(low_score_advances_stmt)
        low_score_advances = low_score_result.scalar() or 0
        
        total_explicit = explicit_agree + explicit_disagree
        agreement_rate = (explicit_agree / total_explicit * 100) if total_explicit > 0 else 100
        
        divergence_count = high_score_rejects + low_score_advances + explicit_disagree
        
        return {
            "period_days": days,
            "total_events": total_events,
            "explicit_feedback": {
                "total": total_explicit,
                "agree": explicit_agree,
                "disagree": explicit_disagree,
                "agreement_rate": round(agreement_rate, 1)
            },
            "implicit_feedback": {
                "advances": implicit_advances,
                "rejects": implicit_rejects
            },
            "divergences": {
                "total": divergence_count,
                "high_score_rejects": high_score_rejects,
                "low_score_advances": low_score_advances,
                "explicit_disagree": explicit_disagree
            },
            "accuracy_indicator": round(100 - (divergence_count / max(total_events, 1) * 100), 1)
        }
    
    async def generate_suggestions(self) -> list[CalibrationSuggestion]:
        """Analyze divergences and generate calibration suggestions."""
        stats = await self.get_calibration_stats(days=30)
        suggestions = []
        
        if stats["divergences"]["high_score_rejects"] >= 3:
            suggestion = CalibrationSuggestion(
                id=str(uuid.uuid4()),
                suggestion_type="weight_adjustment",
                dimension="technical_skills",
                current_weight=0.7,
                suggested_weight=0.6,
                title="Reduzir peso de habilidades técnicas",
                description=f"Você rejeitou {stats['divergences']['high_score_rejects']} candidatos com nota LIA > 70 nos últimos 30 dias.",
                rationale="Os candidatos podem estar sendo supervalorizados tecnicamente. Considere aumentar o peso de soft skills ou fit cultural.",
                supporting_evidence=[
                    {"metric": "high_score_rejects", "value": stats["divergences"]["high_score_rejects"]},
                    {"metric": "period", "value": "30 dias"}
                ],
                impact_score=0.7,
                confidence=min(stats["divergences"]["high_score_rejects"] / 10, 0.9),
                status="pending",
                created_at=datetime.utcnow()
            )
            suggestions.append(suggestion)
            self.db.add(suggestion)
        
        if stats["divergences"]["low_score_advances"] >= 3:
            suggestion = CalibrationSuggestion(
                id=str(uuid.uuid4()),
                suggestion_type="weight_adjustment",
                dimension="experience_years",
                current_weight=0.3,
                suggested_weight=0.4,
                title="Aumentar peso de experiência prática",
                description=f"Você avançou {stats['divergences']['low_score_advances']} candidatos com nota LIA < 60 nos últimos 30 dias.",
                rationale="Candidatos com menos pontuação técnica estão sendo promovidos. Talvez a experiência prática seja mais importante para estas vagas.",
                supporting_evidence=[
                    {"metric": "low_score_advances", "value": stats["divergences"]["low_score_advances"]},
                    {"metric": "period", "value": "30 dias"}
                ],
                impact_score=0.6,
                confidence=min(stats["divergences"]["low_score_advances"] / 10, 0.9),
                status="pending",
                created_at=datetime.utcnow()
            )
            suggestions.append(suggestion)
            self.db.add(suggestion)
        
        if suggestions:
            await self.db.commit()
        
        return suggestions
    
    async def get_pending_suggestions(self) -> list[dict[str, Any]]:
        """Get all pending calibration suggestions."""
        stmt = select(CalibrationSuggestion).where(
            CalibrationSuggestion.status == "pending"
        ).order_by(desc(CalibrationSuggestion.created_at))
        
        result = await self.db.execute(stmt)
        suggestions = result.scalars().all()
        
        return [s.to_dict() for s in suggestions]
    
    async def approve_suggestion(
        self,
        suggestion_id: str,
        user_id: str
    ) -> CalibrationSuggestion | None:
        """Approve a calibration suggestion."""
        stmt = select(CalibrationSuggestion).where(
            CalibrationSuggestion.id == suggestion_id
        )
        result = await self.db.execute(stmt)
        suggestion = result.scalar_one_or_none()
        
        if not suggestion:
            return None
        
        suggestion.status = "approved"
        suggestion.approved_by = user_id
        suggestion.approved_at = datetime.utcnow()
        
        if suggestion.dimension:
            weight_stmt = select(CalibrationWeight).where(
                and_(
                    CalibrationWeight.dimension == suggestion.dimension,
                    CalibrationWeight.is_active
                )
            )
            weight_result = await self.db.execute(weight_stmt)
            weight = weight_result.scalar_one_or_none()
            
            if weight:
                old_weight = weight.adjusted_weight
                weight.adjusted_weight = suggestion.suggested_weight
                weight.sample_size += 1
                weight.last_adjustment_reason = suggestion.rationale
                weight.adjustment_history = weight.adjustment_history or []
                weight.adjustment_history.append({
                    "from": old_weight,
                    "to": suggestion.suggested_weight,
                    "reason": suggestion.rationale,
                    "approved_by": user_id,
                    "approved_at": datetime.utcnow().isoformat()
                })
            else:
                weight = CalibrationWeight(
                    id=str(uuid.uuid4()),
                    dimension=suggestion.dimension,
                    base_weight=suggestion.current_weight or 1.0,
                    adjusted_weight=suggestion.suggested_weight or 1.0,
                    sample_size=1,
                    last_adjustment_reason=suggestion.rationale,
                    adjustment_history=[{
                        "from": suggestion.current_weight,
                        "to": suggestion.suggested_weight,
                        "reason": suggestion.rationale,
                        "approved_by": user_id,
                        "approved_at": datetime.utcnow().isoformat()
                    }],
                    created_at=datetime.utcnow()
                )
                self.db.add(weight)
        
        await self.db.commit()
        await self.db.refresh(suggestion)
        
        return suggestion
    
    async def reject_suggestion(
        self,
        suggestion_id: str,
        user_id: str,
        reason: str | None = None
    ) -> CalibrationSuggestion | None:
        """Reject a calibration suggestion."""
        stmt = select(CalibrationSuggestion).where(
            CalibrationSuggestion.id == suggestion_id
        )
        result = await self.db.execute(stmt)
        suggestion = result.scalar_one_or_none()
        
        if not suggestion:
            return None
        
        suggestion.status = "rejected"
        suggestion.rejected_by = user_id
        suggestion.rejected_at = datetime.utcnow()
        suggestion.rejection_reason = reason
        
        await self.db.commit()
        await self.db.refresh(suggestion)
        
        return suggestion
    
    async def get_recent_events(
        self,
        limit: int = 50,
        feedback_types: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Get recent calibration events."""
        stmt = select(CalibrationEvent).order_by(
            desc(CalibrationEvent.created_at)
        ).limit(limit)
        
        if feedback_types:
            type_enums = [FeedbackType(t) for t in feedback_types if t in [e.value for e in FeedbackType]]
            if type_enums:
                stmt = stmt.where(CalibrationEvent.feedback_type.in_(type_enums))
        
        result = await self.db.execute(stmt)
        events = result.scalars().all()
        
        return [e.to_dict() for e in events]
    
    async def get_weights(self, job_id: str | None = None) -> list[dict[str, Any]]:
        """Get current calibration weights."""
        stmt = select(CalibrationWeight).where(
            CalibrationWeight.is_active
        )
        
        if job_id:
            stmt = stmt.where(
                or_(
                    CalibrationWeight.job_id == job_id,
                    CalibrationWeight.job_id.is_(None)
                )
            )
        
        result = await self.db.execute(stmt)
        weights = result.scalars().all()
        
        return [w.to_dict() for w in weights]
