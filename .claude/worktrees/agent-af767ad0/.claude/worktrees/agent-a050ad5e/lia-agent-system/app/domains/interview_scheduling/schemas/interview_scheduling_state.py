"""
Interview Scheduling State Schema for conversational workflow.
"""
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field


class InterviewParticipant(BaseModel):
    """Single interview participant."""
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None  # "interviewer", "additional_interviewer", "candidate"


class InterviewSchedulingState(BaseModel):
    """
    Complete state for interview scheduling workflow.
    Tracks all fields, collection status, and workflow metadata.
    """
    
    # =============================================
    # CANDIDATE INFORMATION
    # =============================================
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    candidate_phone: Optional[str] = None
    
    # =============================================
    # JOB & POSITION
    # =============================================
    job_title: Optional[str] = None
    job_id: Optional[str] = None  # Reference to job_vacancies table
    
    # =============================================
    # INTERVIEW DETAILS
    # =============================================
    interview_type: Optional[Literal["tecnica", "comportamental", "cultural", "rh", "gerencial"]] = None
    interview_mode: Optional[Literal["presencial", "remoto", "hibrido"]] = None
    
    # =============================================
    # SCHEDULING
    # =============================================
    preferred_date: Optional[date] = None
    preferred_time: Optional[str] = None  # "14:00", "manhã", "tarde"
    start_time: Optional[datetime] = None  # Final computed datetime
    duration_minutes: Optional[int] = 60  # Default 1 hour
    
    # =============================================
    # LOCATION & MEETING
    # =============================================
    location: Optional[str] = None  # Physical address or "Online"
    as_teams_meeting: bool = True  # Default to Teams meeting
    meeting_url: Optional[str] = None  # Generated after creation
    
    # =============================================
    # PARTICIPANTS
    # =============================================
    interviewer_name: Optional[str] = None
    interviewer_email: Optional[str] = None
    additional_interviewers: List[InterviewParticipant] = Field(default_factory=list)
    
    # =============================================
    # NOTES & CONTEXT
    # =============================================
    notes: Optional[str] = None
    preparation_materials: List[str] = Field(default_factory=list)
    
    # =============================================
    # WORKFLOW METADATA
    # =============================================
    collected_fields: List[str] = Field(default_factory=list)
    pending_fields: List[str] = Field(default_factory=list)
    conversation_id: Optional[str] = None
    created_interview_id: Optional[str] = None  # Set after scheduling
    
    # =============================================
    # VALIDATION STATE
    # =============================================
    is_complete: bool = False
    validation_errors: List[str] = Field(default_factory=list)
    
    def mark_field_collected(self, field_name: str):
        """Mark a field as collected."""
        if field_name not in self.collected_fields:
            self.collected_fields.append(field_name)
        if field_name in self.pending_fields:
            self.pending_fields.remove(field_name)
    
    def get_next_pending_field(self) -> Optional[str]:
        """
        Get next field that needs to be collected.
        Priority order for interview scheduling.
        """
        required_fields = [
            "candidate_name",
            "candidate_email",
            "job_title",
            "interview_type",
            "interviewer_email",
            "preferred_date",
            "preferred_time",
        ]
        
        for field in required_fields:
            value = getattr(self, field, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                return field
        
        return None
    
    def validate_completeness(self) -> bool:
        """
        Validate if all required fields are collected.
        """
        self.validation_errors = []
        
        # Required fields check
        if not self.candidate_name:
            self.validation_errors.append("Nome do candidato não informado")
        if not self.candidate_email:
            self.validation_errors.append("Email do candidato não informado")
        if not self.job_title:
            self.validation_errors.append("Cargo/vaga não informado")
        if not self.interview_type:
            self.validation_errors.append("Tipo de entrevista não informado")
        if not self.interviewer_email:
            self.validation_errors.append("Email do entrevistador não informado")
        if not self.start_time:
            self.validation_errors.append("Data/hora da entrevista não definida")
        
        self.is_complete = len(self.validation_errors) == 0
        return self.is_complete
    
    def get_collection_progress(self) -> Dict[str, Any]:
        """
        Get progress of field collection for UI display.
        """
        total_required = 7  # candidate_name, email, job_title, type, interviewer, date, time
        collected = len([f for f in [
            "candidate_name", "candidate_email", "job_title", 
            "interview_type", "interviewer_email", "preferred_date", "preferred_time"
        ] if getattr(self, f, None)])
        
        return {
            "total_required": total_required,
            "collected": collected,
            "percentage": int((collected / total_required) * 100),
            "next_field": self.get_next_pending_field(),
            "is_complete": self.is_complete
        }
    
    def to_interview_request(self) -> Dict[str, Any]:
        """
        Convert state to API request format for /api/v1/interviews/schedule.
        """
        if not self.start_time:
            raise ValueError("start_time must be computed before creating interview")
        
        return {
            "candidate_name": self.candidate_name,
            "candidate_email": self.candidate_email,
            "job_title": self.job_title,
            "interview_type": self.interview_type,
            "interview_mode": self.interview_mode or "remoto",
            "interviewer_name": self.interviewer_name or "Equipe WedoTalent",
            "interviewer_email": self.interviewer_email,
            "additional_interviewers": [
                {
                    "name": p.name,
                    "email": p.email,
                    "role": p.role
                }
                for p in self.additional_interviewers
            ],
            "start_time": self.start_time.isoformat(),
            "duration_minutes": self.duration_minutes,
            "location": self.location or "Microsoft Teams",
            "as_teams_meeting": self.as_teams_meeting,
            "notes": self.notes
        }
