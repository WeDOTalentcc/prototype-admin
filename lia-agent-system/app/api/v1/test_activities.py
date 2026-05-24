"""
Test endpoint to populate activity feed with sample data.
Only for development/testing purposes.
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_tenant_db
from app.models.activity_feed import ActivityFeed
from app.domains.analytics.services.activity_service import ActivityService, get_activity_service
from app.shared.security.require_company_id import require_company_id

router = APIRouter(prefix="/test", tags=["Testing"])


@router.post("/populate-activities", response_model=None)
# TODO(phase2): extract to repository — test activity logging
async def populate_activities(
    db: AsyncSession = Depends(get_tenant_db),
    activity_svc: ActivityService = Depends(get_activity_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Create sample activities for all types to test the Activity Feed UI.
    """
    created_activities = []
    
    # 1. Interview Scheduled (entrevista - verde)
    interview_activity = await activity_svc.create_interview_scheduled(
        candidate_id="test-candidate-001",
        candidate_name="Ana Costa",
        job_title="Backend Sênior Node.js",
        interviewer_name="Carlos Silva",
        interview_date=datetime.utcnow() + timedelta(days=2),
        interview_type="technical",
        scheduled_by="recruiter-123",
    )
    created_activities.append(interview_activity)
    
    # 2. Email Sent (email - azul-acinzentado)
    email_activity = await activity_svc.create_email_sent(
        recipient_id="test-candidate-002",
        recipient_name="João Pedro Santos",
        recipient_type="candidate",
        email_subject="Próximos passos - Backend Sênior Node.js",
        email_type="follow-up",
        sent_by="recruiter-456",
    )
    created_activities.append(email_activity)
    
    # 3. Offer Sent (oferta - lilás)
    offer_activity = await activity_svc.create_offer_sent(
        candidate_id="test-candidate-003",
        candidate_name="Mariana Oliveira",
        job_title="Frontend Pleno React",
        salary_range="R$ 8.000 - R$ 12.000",
        sent_by="recruiter-789",
    )
    created_activities.append(offer_activity)
    
    # 4. Approval Pending (minha - cinza)
    approval_activity = await activity_svc.create_approval_pending(
        item_type="candidate",
        item_id="test-candidate-004",
        item_name="Lucas Mendes - DevOps Engineer",
        approval_type="hiring_manager",
        requested_by="recruiter-101",
    )
    created_activities.append(approval_activity)
    
    # 5. Candidate Moved by LIA (ia - rosa/bege)
    lia_move_activity = await activity_svc.create_candidate_moved(
        candidate_id="test-candidate-005",
        candidate_name="Fernanda Lima",
        from_stage="Triagem Inicial",
        to_stage="Entrevista Técnica",
        job_title="Fullstack Sênior",
        moved_by="lia",
    )
    created_activities.append(lia_move_activity)
    
    # 6. Candidate Moved by Recruiter (minha - cinza)
    recruiter_move_activity = await activity_svc.create_candidate_moved(
        candidate_id="test-candidate-006",
        candidate_name="Rafael Souza",
        from_stage="Entrevista RH",
        to_stage="Entrevista Técnica",
        job_title="Mobile Flutter Pleno",
        moved_by="recruiter-202",
    )
    created_activities.append(recruiter_move_activity)
    
    # 7. LIA Suggestion (ia - rosa/bege)
    lia_suggestion_activity = await activity_svc.create_lia_suggestion(
        suggestion_type="candidate_match",
        target_id="test-job-001",
        target_name="Tech Lead - Python/AWS",
        target_type="job",
        suggestion_text="3 candidatos altamente compatíveis encontrados no Pearch",
        priority="high",
    )
    created_activities.append(lia_suggestion_activity)
    
    return {
        "success": True,
        "message": f"Created {len(created_activities)} sample activities",
        "activities": [
            {
                "id": activity.id,
                "type": activity.activity_type,
                "title": activity.title,
                "created_at": activity.created_at.isoformat(),
            }
            for activity in created_activities
        ],
    }


@router.delete("/clear-test-activities", response_model=None)
async def clear_test_activities(db: AsyncSession = Depends(get_db), company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Delete all test activities (those with test- prefixed IDs).
    """
    # Multi-tenancy fail-closed: explicit company_id filter (REGRA ZERO + B.1).
    stmt = delete(ActivityFeed).where(
        ActivityFeed.target_id.like("test-%"),
        ActivityFeed.company_id == company_id,
    )

    await db.execute(stmt)
    
    return {
        "success": True,
        "message": "Test activities cleared successfully",
    }
