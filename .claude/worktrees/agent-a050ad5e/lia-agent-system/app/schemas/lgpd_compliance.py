"""
Pydantic schemas for LGPD Compliance API.

Includes schemas for:
- DPO Registry (Data Protection Officer management)
- Breach Notifications (48h LGPD requirement)
- Automated Decision Explanations (Article 20 compliance)
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class BreachSeverityEnum(str, Enum):
    """Severity levels for data breaches."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BreachStatusEnum(str, Enum):
    """Status of breach notification workflow."""
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    NOTIFIED = "notified"
    RESOLVED = "resolved"


class DecisionTypeEnum(str, Enum):
    """Types of automated decisions for LGPD Article 20."""
    SCREENING = "screening"
    RANKING = "ranking"
    REJECTION = "rejection"


class DPORegistryResponse(BaseModel):
    """Response schema for DPO registry entry."""
    id: str
    company_id: str
    dpo_name: str
    dpo_email: str
    dpo_phone: Optional[str] = None
    appointment_date: Optional[date] = None
    is_active: bool = True
    public_contact_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DPORegistryListResponse(BaseModel):
    """Paginated list of DPO registry entries."""
    dpos: List[DPORegistryResponse]
    total: int
    limit: int
    offset: int


class DPORegistryCreate(BaseModel):
    """Schema for creating/updating a DPO registry entry."""
    dpo_name: str = Field(..., min_length=2, max_length=255, description="Full name of the DPO")
    dpo_email: str = Field(..., description="DPO contact email")
    dpo_phone: Optional[str] = Field(None, max_length=50, description="DPO contact phone")
    appointment_date: date = Field(..., description="Date of DPO appointment")
    public_contact_url: Optional[str] = Field(None, max_length=500, description="Public URL for data subject contact")

    class Config:
        json_schema_extra = {
            "example": {
                "dpo_name": "Maria Silva",
                "dpo_email": "dpo@empresa.com.br",
                "dpo_phone": "+55 11 99999-9999",
                "appointment_date": "2024-01-15",
                "public_contact_url": "https://empresa.com.br/privacidade/contato"
            }
        }


class DPORegistryUpdate(BaseModel):
    """Schema for updating a DPO registry entry."""
    dpo_name: Optional[str] = Field(None, min_length=2, max_length=255)
    dpo_email: Optional[str] = None
    dpo_phone: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    public_contact_url: Optional[str] = Field(None, max_length=500)


class BreachNotificationResponse(BaseModel):
    """Response schema for breach notification."""
    id: str
    company_id: str
    breach_detected_at: Optional[datetime] = None
    breach_description: str
    affected_data_types: List[str] = []
    affected_count: Optional[int] = None
    severity: str
    notification_sent_to_anpd: bool = False
    anpd_notification_at: Optional[datetime] = None
    notification_sent_to_subjects: bool = False
    subjects_notification_at: Optional[datetime] = None
    remediation_actions: List[str] = []
    status: str
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    hours_since_detection: Optional[float] = None
    anpd_deadline_exceeded: Optional[bool] = None

    class Config:
        from_attributes = True


class BreachNotificationListResponse(BaseModel):
    """Paginated list of breach notifications."""
    breaches: List[BreachNotificationResponse]
    total: int
    limit: int
    offset: int


class BreachNotificationCreate(BaseModel):
    """Schema for creating a breach notification."""
    breach_detected_at: datetime = Field(..., description="When the breach was detected")
    breach_description: str = Field(..., min_length=10, description="Description of the breach")
    affected_data_types: List[str] = Field(default=[], description="Types of data affected (e.g., 'personal_info', 'cv', 'contact_info')")
    affected_count: Optional[int] = Field(None, ge=0, description="Number of data subjects affected")
    severity: BreachSeverityEnum = Field(default=BreachSeverityEnum.MEDIUM, description="Severity level")

    class Config:
        json_schema_extra = {
            "example": {
                "breach_detected_at": "2024-01-15T10:30:00Z",
                "breach_description": "Unauthorized access to candidate database detected from unknown IP",
                "affected_data_types": ["personal_info", "cv", "contact_info"],
                "affected_count": 150,
                "severity": "high"
            }
        }


class BreachNotificationUpdate(BaseModel):
    """Schema for updating a breach notification."""
    breach_description: Optional[str] = Field(None, min_length=10)
    affected_data_types: Optional[List[str]] = None
    affected_count: Optional[int] = Field(None, ge=0)
    severity: Optional[BreachSeverityEnum] = None
    remediation_actions: Optional[List[str]] = None
    status: Optional[BreachStatusEnum] = None


class ANPDNotification(BaseModel):
    """Schema for marking ANPD notification."""
    notification_details: Optional[str] = Field(None, description="Details about the ANPD notification")
    protocol_number: Optional[str] = Field(None, description="ANPD protocol number if available")

    class Config:
        json_schema_extra = {
            "example": {
                "notification_details": "Notified via ANPD portal",
                "protocol_number": "ANPD-2024-001234"
            }
        }


class SubjectsNotification(BaseModel):
    """Schema for marking data subjects notification."""
    notification_method: Optional[str] = Field(None, description="Method used to notify subjects")
    subjects_notified_count: Optional[int] = Field(None, ge=0, description="Number of subjects notified")

    class Config:
        json_schema_extra = {
            "example": {
                "notification_method": "email",
                "subjects_notified_count": 150
            }
        }


class BreachResolution(BaseModel):
    """Schema for resolving a breach notification."""
    resolution_notes: Optional[str] = Field(None, description="Notes about the resolution")
    remediation_actions: Optional[List[str]] = Field(None, description="Final remediation actions taken")

    class Config:
        json_schema_extra = {
            "example": {
                "resolution_notes": "Access revoked, security patches applied, all affected users notified",
                "remediation_actions": [
                    "Revoked compromised credentials",
                    "Applied security patches",
                    "Implemented additional monitoring",
                    "Completed security audit"
                ]
            }
        }


class AutomatedDecisionResponse(BaseModel):
    """Response schema for automated decision explanation."""
    id: str
    company_id: str
    decision_type: str
    candidate_id: Optional[str] = None
    vacancy_id: Optional[str] = None
    ai_model_used: Optional[str] = None
    input_criteria: Dict[str, Any] = {}
    decision_criteria: Dict[str, Any] = {}
    explanation_text: Optional[str] = None
    explanation_requested_at: Optional[datetime] = None
    explanation_provided_at: Optional[datetime] = None
    human_review_requested: bool = False
    human_review_completed_at: Optional[datetime] = None
    human_review_decision: Optional[str] = None
    human_reviewer_id: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AutomatedDecisionListResponse(BaseModel):
    """Paginated list of automated decision explanations."""
    decisions: List[AutomatedDecisionResponse]
    total: int
    limit: int
    offset: int


class AutomatedDecisionCreate(BaseModel):
    """Schema for creating an automated decision record."""
    decision_type: DecisionTypeEnum = Field(..., description="Type of decision")
    candidate_id: Optional[str] = Field(None, description="Candidate ID")
    vacancy_id: Optional[str] = Field(None, description="Vacancy ID")
    ai_model_used: Optional[str] = Field(None, description="AI model version used")
    input_criteria: Dict[str, Any] = Field(default={}, description="Input data criteria used")
    decision_criteria: Dict[str, Any] = Field(default={}, description="Decision criteria and weights")
    explanation_text: Optional[str] = Field(None, description="Human-readable explanation")

    class Config:
        json_schema_extra = {
            "example": {
                "decision_type": "screening",
                "candidate_id": "550e8400-e29b-41d4-a716-446655440000",
                "vacancy_id": "660e8400-e29b-41d4-a716-446655440001",
                "ai_model_used": "scoring-model-v2.1",
                "input_criteria": {
                    "experience_years": 5,
                    "skills_match": ["Python", "FastAPI"],
                    "education_level": "bachelor"
                },
                "decision_criteria": {
                    "minimum_experience": 3,
                    "required_skills": ["Python"],
                    "education_weight": 0.2
                },
                "explanation_text": "Candidate approved for screening based on 5 years experience matching minimum requirement of 3 years, and possession of required Python skill."
            }
        }


class HumanReviewRequest(BaseModel):
    """Schema for requesting human review of an automated decision."""
    reason: Optional[str] = Field(None, description="Reason for requesting human review")
    requested_by: Optional[str] = Field(None, description="ID of the data subject requesting review")

    class Config:
        json_schema_extra = {
            "example": {
                "reason": "Candidate believes the automated decision did not consider relevant experience",
                "requested_by": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class HumanReviewComplete(BaseModel):
    """Schema for completing a human review."""
    decision: str = Field(..., description="Human review decision")
    reviewer_id: str = Field(..., description="ID of the human reviewer")
    notes: Optional[str] = Field(None, description="Additional notes")

    class Config:
        json_schema_extra = {
            "example": {
                "decision": "Automated decision upheld - candidate experience was correctly evaluated",
                "reviewer_id": "770e8400-e29b-41d4-a716-446655440002",
                "notes": "Reviewed candidate CV and confirmed 5 years of relevant experience"
            }
        }


class LGPDComplianceStats(BaseModel):
    """Statistics for LGPD compliance dashboard."""
    dpo_registered: bool = False
    dpo_active: bool = False
    total_breaches: int = 0
    open_breaches: int = 0
    breaches_pending_anpd: int = 0
    breaches_deadline_exceeded: int = 0
    total_automated_decisions: int = 0
    pending_human_reviews: int = 0
    completed_human_reviews: int = 0
