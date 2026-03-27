"""
Sourcing & Engagement State schema for workflow steps 14-27.
Tracks candidate pipeline, outreach, screening, and feedback workflow.
"""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


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


class CandidateStatus(str, Enum):
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
    email: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    linkedin_url: Optional[str] = None
    current_role: Optional[str] = None
    current_company: Optional[str] = None
    source: Literal["local", "pearch", "referral", "application"] = "local"
    match_score: Optional[CandidateMatchScore] = None
    status: CandidateStatus = CandidateStatus.IDENTIFIED
    calibration_result: Optional[Literal["approved", "rejected"]] = None
    calibration_feedback: Optional[str] = None
    outreach_attempts: int = 0
    last_outreach_at: Optional[datetime] = None
    outreach_channel: Optional[Literal["email", "whatsapp", "linkedin"]] = None
    screening_started_at: Optional[datetime] = None
    screening_completed_at: Optional[datetime] = None
    screening_deadline: Optional[datetime] = None
    wsi_score: Optional[float] = None
    wsi_report: Optional[Dict[str, Any]] = None
    feedback_sent: bool = False
    feedback_content: Optional[str] = None
    feedback_sent_at: Optional[datetime] = None
    interview_scheduled_at: Optional[datetime] = None
    interview_link: Optional[str] = None
    notes: List[str] = Field(default_factory=list)
    added_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CalibrationSession(BaseModel):
    """Calibration session with recruiter."""
    session_id: str
    candidates_presented: List[str] = Field(default_factory=list)
    approvals: List[str] = Field(default_factory=list)
    rejections: List[str] = Field(default_factory=list)
    feedback_notes: Dict[str, str] = Field(default_factory=dict)
    learned_preferences: Dict[str, Any] = Field(default_factory=dict)
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
    recommendation: Optional[str] = None
    suggested_action: Literal["proceed", "expand_local", "expand_global", "adjust_criteria"] = "proceed"


class GlobalSearchRequest(BaseModel):
    """Request for global (Pearch) search."""
    requested: bool = False
    approved: bool = False
    estimated_credits: float = 0
    estimated_candidates: int = 0
    actual_credits_used: float = 0
    actual_candidates_found: int = 0
    search_params: Dict[str, Any] = Field(default_factory=dict)
    thread_id: Optional[str] = None
    requested_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class OutreachCampaign(BaseModel):
    """Email/WhatsApp outreach campaign."""
    campaign_id: str
    candidates_targeted: List[str] = Field(default_factory=list)
    candidates_contacted: List[str] = Field(default_factory=list)
    candidates_responded: List[str] = Field(default_factory=list)
    template_used: str = "default"
    channel: Literal["email", "whatsapp"] = "email"
    status: Literal["pending", "in_progress", "completed", "paused"] = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ScreeningSession(BaseModel):
    """WSI Screening session with candidate."""
    session_id: str
    candidate_id: str
    channel: Literal["web_chat", "whatsapp", "voice"] = "web_chat"
    status: Literal["invited", "in_progress", "completed", "expired", "cancelled"] = "invited"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    deadline: datetime
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    transcript: Optional[str] = None
    wsi_evaluation: Optional[Dict[str, Any]] = None
    strengths: List[str] = Field(default_factory=list)
    development_areas: List[str] = Field(default_factory=list)
    overall_score: Optional[float] = None
    passed: Optional[bool] = None
    reminder_sent: bool = False
    reminder_sent_at: Optional[datetime] = None


class CandidateFeedback(BaseModel):
    """Feedback sent to candidate."""
    feedback_id: str
    candidate_id: str
    type: Literal["screening_passed", "screening_failed", "rejected", "process_closed"] = "screening_passed"
    strengths: List[str] = Field(default_factory=list)
    development_areas: List[str] = Field(default_factory=list)
    message: str
    channel: Literal["email", "whatsapp"] = "email"
    sent: bool = False
    sent_at: Optional[datetime] = None
    customized_by_recruiter: bool = False


class RecruiterNotification(BaseModel):
    """Notification sent to recruiter via Teams/Chat."""
    notification_id: str
    type: Literal["screening_completed", "approval_needed", "interview_reminder", "daily_briefing", "end_of_day", "alert"]
    title: str
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    action_required: bool = False
    action_type: Optional[Literal["approve", "reject", "schedule", "confirm", "review"]] = None
    candidate_ids: List[str] = Field(default_factory=list)
    sent: bool = False
    sent_at: Optional[datetime] = None
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    response: Optional[str] = None


class SourcingEngagementState(BaseModel):
    """
    Complete state for sourcing and engagement workflow (steps 14-27).
    """
    job_id: str
    job_title: str
    company_name: Optional[str] = None
    is_confidential: bool = False
    current_phase: Literal["sourcing", "calibration", "engagement", "screening", "decision", "closing"] = "sourcing"
    current_step: int = 14
    candidates: List[PipelineCandidate] = Field(default_factory=list)
    calibration_sessions: List[CalibrationSession] = Field(default_factory=list)
    volume_assessment: Optional[VolumeAssessment] = None
    global_search: Optional[GlobalSearchRequest] = None
    outreach_campaigns: List[OutreachCampaign] = Field(default_factory=list)
    screening_sessions: List[ScreeningSession] = Field(default_factory=list)
    candidate_feedbacks: List[CandidateFeedback] = Field(default_factory=list)
    recruiter_notifications: List[RecruiterNotification] = Field(default_factory=list)
    governance_auto_schedule: bool = False
    governance_auto_feedback: bool = False
    governance_requires_approval: bool = True
    score_threshold_high: float = 80.0
    score_threshold_medium: float = 60.0
    screening_window_hours: int = 24
    hired_candidate_id: Optional[str] = None
    closed_at: Optional[datetime] = None
    close_reason: Optional[Literal["hired", "cancelled", "on_hold"]] = None
    mass_feedback_sent: bool = False
    mass_feedback_sent_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def get_candidates_by_status(self, status: CandidateStatus) -> List[PipelineCandidate]:
        """Get all candidates with a specific status."""
        return [c for c in self.candidates if c.status == status]

    def get_high_match_candidates(self) -> List[PipelineCandidate]:
        """Get candidates with high match score (>=80%)."""
        return [c for c in self.candidates if c.match_score and c.match_score.overall_score >= self.score_threshold_high]

    def get_pending_approval_candidates(self) -> List[PipelineCandidate]:
        """Get candidates pending recruiter decision."""
        return [c for c in self.candidates if c.status == CandidateStatus.PENDING_RECRUITER_DECISION]

    def get_pending_feedback_candidates(self) -> List[PipelineCandidate]:
        """Get candidates who haven't received feedback yet."""
        return [c for c in self.candidates if not c.feedback_sent and c.status in [
            CandidateStatus.REJECTED,
            CandidateStatus.REJECTED_CALIBRATION,
            CandidateStatus.SCREENING_EXPIRED
        ]]

    def get_expired_screenings(self) -> List[ScreeningSession]:
        """Get screening sessions that have expired."""
        now = datetime.utcnow()
        return [s for s in self.screening_sessions if s.status == "in_progress" and s.deadline < now]

    def calculate_pipeline_stats(self) -> Dict[str, int]:
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
        match_score: Optional[CandidateMatchScore] = None,
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
        data: Optional[Dict[str, Any]] = None,
        action_required: bool = False,
        action_type: Optional[Literal["approve", "reject", "schedule", "confirm", "review"]] = None,
        candidate_ids: Optional[List[str]] = None
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
    subject: Optional[str] = None
    body: str
    variables: List[str] = Field(default_factory=list)
    is_default: bool = False


class EmailOutreachTemplate(BaseModel):
    """Template for email outreach to candidates."""
    template_id: str
    name: str
    type: Literal["initial_contact", "follow_up", "screening_invite"]
    subject: str
    body: str
    variables: List[str] = Field(default_factory=list)
    is_confidential_version: bool = False


class WhatsAppTemplate(BaseModel):
    """Template for WhatsApp messages."""
    template_id: str
    name: str
    type: Literal["initial_contact", "screening_invite", "reminder", "feedback", "scheduling"]
    body: str
    variables: List[str] = Field(default_factory=list)
    is_confidential_version: bool = False
