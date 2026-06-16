"""
Sourcing & Engagement State schema for workflow steps 14-27.
Tracks candidate pipeline, outreach, screening, and feedback workflow.
"""
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel


class CandidateMatchScore(BaseModel):
    """Match score breakdown for a candidate."""
    overall_score: float = Field(..., ge=0, le=100)
    technical_score: float = Field(default=0, ge=0, le=100)
    behavioral_score: float = Field(default=0, ge=0, le=100)
    experience_score: float = Field(default=0, ge=0, le=100)
    cultural_score: float = Field(default=0, ge=0, le=100)
    score_tier: Literal["high", "medium", "low"] = "medium"
    auto_added: bool = False
    needs_review: bool = False


class CandidateStatus(StrEnum):
    """Candidate status in the pipeline."""
    IDENTIFIED = "identified"
    CALIBRATION = "calibration"
    APPROVED = "approved"
    REJECTED_CALIBRATION = "rejected_calibration"
    PENDING_CONTACT = "pending_contact"
    CONTACTED = "contacted"
    SCREENING_INVITED = "screening_invited"
    SCREENING_IN_PROGRESS = "screening_in_progress"
    SCREENING_COMPLETED = "screening_completed"
    SCREENING_EXPIRED = "screening_expired"
    PENDING_RECRUITER_DECISION = "pending_recruiter_decision"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_COMPLETED = "interview_completed"
    REJECTED = "rejected"
    HIRED = "hired"
    FEEDBACK_SENT = "feedback_sent"


class PipelineCandidate(BaseModel):
    """Candidate in the sourcing/engagement pipeline."""
    candidate_id: str
    name: str
    email: str | None = None
    phone: str | None = None
    whatsapp: str | None = None
    linkedin_url: str | None = None
    current_role: str | None = None
    current_company: str | None = None
    source: Literal["local", "pearch", "referral", "application"] = "local"
    match_score: CandidateMatchScore | None = None
    status: CandidateStatus = CandidateStatus.IDENTIFIED
    calibration_result: Literal["approved", "rejected"] | None = None
    calibration_feedback: str | None = None
    outreach_attempts: int = 0
    last_outreach_at: datetime | None = None
    outreach_channel: Literal["email", "whatsapp", "linkedin"] | None = None
    screening_started_at: datetime | None = None
    screening_completed_at: datetime | None = None
    screening_deadline: datetime | None = None
    wsi_score: float | None = None
    wsi_report: dict[str, Any] | None = None
    feedback_sent: bool = False
    feedback_content: str | None = None
    feedback_sent_at: datetime | None = None
    interview_scheduled_at: datetime | None = None
    interview_link: str | None = None
    notes: list[str] = Field(default_factory=list)
    added_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CalibrationSession(BaseModel):
    """Calibration session with recruiter."""
    session_id: str
    candidates_presented: list[str] = Field(default_factory=list)
    approvals: list[str] = Field(default_factory=list)
    rejections: list[str] = Field(default_factory=list)
    feedback_notes: dict[str, str] = Field(default_factory=dict)
    learned_preferences: dict[str, Any] = Field(default_factory=dict)
    completed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VolumeAssessment(BaseModel):
    """Assessment of candidate volume for the job."""
    total_local: int = 0
    total_global_estimated: int = 0
    total_in_pipeline: int = 0
    high_match_count: int = 0
    medium_match_count: int = 0
    low_match_count: int = 0
    is_satisfactory: bool = False
    recommendation: str | None = None
    suggested_action: Literal["proceed", "expand_local", "expand_global", "adjust_criteria"] = "proceed"


class GlobalSearchRequest(WeDoBaseModel):
    """Request for global (Pearch) search."""
    requested: bool = False
    approved: bool = False
    estimated_credits: float = 0
    estimated_candidates: int = 0
    actual_credits_used: float = 0
    actual_candidates_found: int = 0
    search_params: dict[str, Any] = Field(default_factory=dict)
    thread_id: str | None = None
    requested_at: datetime | None = None
    approved_at: datetime | None = None
    completed_at: datetime | None = None


class OutreachCampaign(BaseModel):
    """Email/WhatsApp outreach campaign."""
    campaign_id: str
    candidates_targeted: list[str] = Field(default_factory=list)
    candidates_contacted: list[str] = Field(default_factory=list)
    candidates_responded: list[str] = Field(default_factory=list)
    template_used: str = "default"
    channel: Literal["email", "whatsapp"] = "email"
    status: Literal["pending", "in_progress", "completed", "paused"] = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None


class ScreeningSession(BaseModel):
    """WSI Screening session with candidate."""
    session_id: str
    candidate_id: str
    channel: Literal["web_chat", "whatsapp", "voice"] = "web_chat"
    status: Literal["invited", "in_progress", "completed", "expired", "cancelled"] = "invited"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    deadline: datetime
    messages: list[dict[str, Any]] = Field(default_factory=list)
    transcript: str | None = None
    wsi_evaluation: dict[str, Any] | None = None
    strengths: list[str] = Field(default_factory=list)
    development_areas: list[str] = Field(default_factory=list)
    overall_score: float | None = None
    passed: bool | None = None
    reminder_sent: bool = False
    reminder_sent_at: datetime | None = None


class CandidateFeedback(BaseModel):
    """Feedback sent to candidate."""
    feedback_id: str
    candidate_id: str
    type: Literal["screening_passed", "screening_failed", "rejected", "process_closed"] = "screening_passed"
    strengths: list[str] = Field(default_factory=list)
    development_areas: list[str] = Field(default_factory=list)
    message: str
    channel: Literal["email", "whatsapp"] = "email"
    sent: bool = False
    sent_at: datetime | None = None
    customized_by_recruiter: bool = False


class RecruiterNotification(BaseModel):
    """Notification sent to recruiter via Teams/Chat."""
    notification_id: str
    type: Literal["screening_completed", "approval_needed", "interview_reminder", "daily_briefing", "end_of_day", "alert"]
    title: str
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    action_required: bool = False
    action_type: Literal["approve", "reject", "schedule", "confirm", "review"] | None = None
    candidate_ids: list[str] = Field(default_factory=list)
    sent: bool = False
    sent_at: datetime | None = None
    acknowledged: bool = False
    acknowledged_at: datetime | None = None
    response: str | None = None


class SourcingEngagementState(BaseModel):
    """
    Complete state for sourcing and engagement workflow (steps 14-27).
    """
    job_id: str
    job_title: str
    company_name: str | None = None
    is_confidential: bool = False
    current_phase: Literal["sourcing", "calibration", "engagement", "screening", "decision", "closing"] = "sourcing"
    current_step: int = 14
    candidates: list[PipelineCandidate] = Field(default_factory=list)
    calibration_sessions: list[CalibrationSession] = Field(default_factory=list)
    volume_assessment: VolumeAssessment | None = None
    global_search: GlobalSearchRequest | None = None
    outreach_campaigns: list[OutreachCampaign] = Field(default_factory=list)
    screening_sessions: list[ScreeningSession] = Field(default_factory=list)
    candidate_feedbacks: list[CandidateFeedback] = Field(default_factory=list)
    recruiter_notifications: list[RecruiterNotification] = Field(default_factory=list)
    governance_auto_schedule: bool = False
    governance_auto_feedback: bool = False
    governance_requires_approval: bool = True
    score_threshold_high: float = 80.0
    score_threshold_medium: float = 60.0
    screening_window_hours: int = 24
    hired_candidate_id: str | None = None
    closed_at: datetime | None = None
    close_reason: Literal["hired", "cancelled", "on_hold"] | None = None
    mass_feedback_sent: bool = False
    mass_feedback_sent_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def get_candidates_by_status(self, status: CandidateStatus) -> list[PipelineCandidate]:
        """Get all candidates with a specific status."""
        return [c for c in self.candidates if c.status == status]

    def get_high_match_candidates(self) -> list[PipelineCandidate]:
        """Get candidates with high match score (>=80%)."""
        return [c for c in self.candidates if c.match_score and c.match_score.overall_score >= self.score_threshold_high]

    def get_pending_approval_candidates(self) -> list[PipelineCandidate]:
        """Get candidates pending recruiter decision."""
        return [c for c in self.candidates if c.status == CandidateStatus.PENDING_RECRUITER_DECISION]

    def get_pending_feedback_candidates(self) -> list[PipelineCandidate]:
        """Get candidates who haven't received feedback yet."""
        return [c for c in self.candidates if not c.feedback_sent and c.status in [
            CandidateStatus.REJECTED,
            CandidateStatus.REJECTED_CALIBRATION,
            CandidateStatus.SCREENING_EXPIRED
        ]]

    def get_expired_screenings(self) -> list[ScreeningSession]:
        """Get screening sessions that have expired."""
        now = datetime.utcnow()
        return [s for s in self.screening_sessions if s.status == "in_progress" and s.deadline < now]

    def calculate_pipeline_stats(self) -> dict[str, int]:
        """Calculate pipeline statistics."""
        stats = {
            "total": len(self.candidates),
            "identified": 0,
            "in_calibration": 0,
            "approved": 0,
            "contacted": 0,
            "screening_in_progress": 0,
            "screening_completed": 0,
            "pending_decision": 0,
            "interview_scheduled": 0,
            "rejected": 0,
            "hired": 0
        }
        for candidate in self.candidates:
            if candidate.status == CandidateStatus.IDENTIFIED:
                stats["identified"] += 1
            elif candidate.status == CandidateStatus.CALIBRATION:
                stats["in_calibration"] += 1
            elif candidate.status == CandidateStatus.APPROVED:
                stats["approved"] += 1
            elif candidate.status in [CandidateStatus.CONTACTED, CandidateStatus.SCREENING_INVITED]:
                stats["contacted"] += 1
            elif candidate.status == CandidateStatus.SCREENING_IN_PROGRESS:
                stats["screening_in_progress"] += 1
            elif candidate.status == CandidateStatus.SCREENING_COMPLETED:
                stats["screening_completed"] += 1
            elif candidate.status == CandidateStatus.PENDING_RECRUITER_DECISION:
                stats["pending_decision"] += 1
            elif candidate.status in [CandidateStatus.INTERVIEW_SCHEDULED, CandidateStatus.INTERVIEW_COMPLETED]:
                stats["interview_scheduled"] += 1
            elif candidate.status in [CandidateStatus.REJECTED, CandidateStatus.REJECTED_CALIBRATION]:
                stats["rejected"] += 1
            elif candidate.status == CandidateStatus.HIRED:
                stats["hired"] += 1
        return stats

    def add_candidate(
        self,
        candidate_id: str,
        name: str,
        source: Literal["local", "pearch", "referral", "application"],
        match_score: CandidateMatchScore | None = None,
        **kwargs
    ) -> PipelineCandidate:
        """Add a candidate to the pipeline."""
        if match_score:
            if match_score.overall_score >= self.score_threshold_high:
                match_score.score_tier = "high"
                match_score.auto_added = True
            elif match_score.overall_score >= self.score_threshold_medium:
                match_score.score_tier = "medium"
                match_score.needs_review = True
            else:
                match_score.score_tier = "low"
        
        candidate = PipelineCandidate(
            candidate_id=candidate_id,
            name=name,
            source=source,
            match_score=match_score,
            **kwargs
        )
        self.candidates.append(candidate)
        self.updated_at = datetime.utcnow()
        return candidate

    def update_candidate_status(self, candidate_id: str, new_status: CandidateStatus) -> bool:
        """Update a candidate's status."""
        for candidate in self.candidates:
            if candidate.candidate_id == candidate_id:
                candidate.status = new_status
                candidate.updated_at = datetime.utcnow()
                self.updated_at = datetime.utcnow()
                return True
        return False

    def create_screening_session(
        self,
        candidate_id: str,
        channel: Literal["web_chat", "whatsapp", "voice"] = "web_chat"
    ) -> ScreeningSession:
        """Create a new screening session for a candidate."""
        import uuid
        from datetime import timedelta
        session = ScreeningSession(
            session_id=str(uuid.uuid4()),
            candidate_id=candidate_id,
            channel=channel,
            deadline=datetime.utcnow() + timedelta(hours=self.screening_window_hours)
        )
        self.screening_sessions.append(session)
        self.update_candidate_status(candidate_id, CandidateStatus.SCREENING_INVITED)
        return session

    def send_notification_to_recruiter(
        self,
        notification_type: Literal["screening_completed", "approval_needed", "interview_reminder", "daily_briefing", "end_of_day", "alert"],
        title: str,
        message: str,
        data: dict[str, Any] | None = None,
        action_required: bool = False,
        action_type: Literal["approve", "reject", "schedule", "confirm", "review"] | None = None,
        candidate_ids: list[str] | None = None
    ) -> RecruiterNotification:
        """Create a notification for the recruiter."""
        import uuid
        notification = RecruiterNotification(
            notification_id=str(uuid.uuid4()),
            type=notification_type,
            title=title,
            message=message,
            data=data or {},
            action_required=action_required,
            action_type=action_type,
            candidate_ids=candidate_ids or []
        )
        self.recruiter_notifications.append(notification)
        return notification


class FeedbackTemplate(BaseModel):
    """Template for candidate feedback messages."""
    template_id: str
    name: str
    type: Literal["screening_passed", "screening_failed", "rejected", "process_closed"]
    channel: Literal["email", "whatsapp"]
    subject: str | None = None
    body: str
    variables: list[str] = Field(default_factory=list)
    is_default: bool = False


class EmailOutreachTemplate(BaseModel):
    """Template for email outreach to candidates."""
    template_id: str
    name: str
    type: Literal["initial_contact", "follow_up", "screening_invite"]
    subject: str
    body: str
    variables: list[str] = Field(default_factory=list)
    is_confidential_version: bool = False


class WhatsAppTemplate(BaseModel):
    """Template for WhatsApp messages."""
    template_id: str
    name: str
    type: Literal["initial_contact", "screening_invite", "reminder", "feedback", "scheduling"]
    body: str
    variables: list[str] = Field(default_factory=list)
    is_confidential_version: bool = False
