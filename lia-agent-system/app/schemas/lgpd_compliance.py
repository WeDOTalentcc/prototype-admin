"""
Pydantic schemas for LGPD Compliance API.

Includes schemas for:
- DPO Registry (Data Protection Officer management)
- Breach Notifications (48h LGPD requirement)
- Automated Decision Explanations (Article 20 compliance)
"""

from datetime import date, datetime
from enum import Enum, StrEnum
from typing import Any

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel


class BreachSeverityEnum(StrEnum):
    """Severity levels for data breaches."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BreachStatusEnum(StrEnum):
    """Status of breach notification workflow."""
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    NOTIFIED = "notified"
    RESOLVED = "resolved"


class DecisionTypeEnum(StrEnum):
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
    dpo_phone: str | None = None
    appointment_date: date | None = None
    is_active: bool = True
    public_contact_url: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class DPORegistryListResponse(BaseModel):
    """Paginated list of DPO registry entries."""
    dpos: list[DPORegistryResponse]
    total: int
    limit: int
    offset: int


class DPORegistryCreate(WeDoBaseModel):
    """Schema for creating/updating a DPO registry entry."""
    dpo_name: str = Field(..., min_length=2, max_length=255, description="Full name of the DPO")
    dpo_email: str = Field(..., description="DPO contact email")
    dpo_phone: str | None = Field(None, max_length=50, description="DPO contact phone")
    appointment_date: date = Field(..., description="Date of DPO appointment")
    public_contact_url: str | None = Field(None, max_length=500, description="Public URL for data subject contact")

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


class DPORegistryUpdate(WeDoBaseModel):
    """Schema for updating a DPO registry entry."""
    dpo_name: str | None = Field(None, min_length=2, max_length=255)
    dpo_email: str | None = None
    dpo_phone: str | None = Field(None, max_length=50)
    is_active: bool | None = None
    public_contact_url: str | None = Field(None, max_length=500)


class BreachNotificationResponse(BaseModel):
    """Response schema for breach notification."""
    id: str
    company_id: str
    breach_detected_at: datetime | None = None
    breach_description: str
    affected_data_types: list[str] = []
    affected_count: int | None = None
    severity: str
    notification_sent_to_anpd: bool = False
    anpd_notification_at: datetime | None = None
    notification_sent_to_subjects: bool = False
    subjects_notification_at: datetime | None = None
    remediation_actions: list[str] = []
    status: str
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    resolved_at: datetime | None = None
    hours_since_detection: float | None = None
    anpd_deadline_exceeded: bool | None = None

    class Config:
        from_attributes = True


class BreachNotificationListResponse(BaseModel):
    """Paginated list of breach notifications."""
    breaches: list[BreachNotificationResponse]
    total: int
    limit: int
    offset: int


class BreachNotificationCreate(WeDoBaseModel):
    """Schema for creating a breach notification."""
    breach_detected_at: datetime = Field(..., description="When the breach was detected")
    breach_description: str = Field(..., min_length=10, description="Description of the breach")
    affected_data_types: list[str] = Field(default=[], description="Types of data affected (e.g., 'personal_info', 'cv', 'contact_info')")
    affected_count: int | None = Field(None, ge=0, description="Number of data subjects affected")
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


class BreachNotificationUpdate(WeDoBaseModel):
    """Schema for updating a breach notification."""
    breach_description: str | None = Field(None, min_length=10)
    affected_data_types: list[str] | None = None
    affected_count: int | None = Field(None, ge=0)
    severity: BreachSeverityEnum | None = None
    remediation_actions: list[str] | None = None
    status: BreachStatusEnum | None = None


class ANPDNotification(BaseModel):
    """Schema for marking ANPD notification."""
    notification_details: str | None = Field(None, description="Details about the ANPD notification")
    protocol_number: str | None = Field(None, description="ANPD protocol number if available")

    class Config:
        json_schema_extra = {
            "example": {
                "notification_details": "Notified via ANPD portal",
                "protocol_number": "ANPD-2024-001234"
            }
        }


class SubjectsNotification(BaseModel):
    """Schema for marking data subjects notification."""
    notification_method: str | None = Field(None, description="Method used to notify subjects")
    subjects_notified_count: int | None = Field(None, ge=0, description="Number of subjects notified")

    class Config:
        json_schema_extra = {
            "example": {
                "notification_method": "email",
                "subjects_notified_count": 150
            }
        }


class BreachResolution(BaseModel):
    """Schema for resolving a breach notification."""
    resolution_notes: str | None = Field(None, description="Notes about the resolution")
    remediation_actions: list[str] | None = Field(None, description="Final remediation actions taken")

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
    candidate_id: str | None = None
    vacancy_id: str | None = None
    ai_model_used: str | None = None
    input_criteria: dict[str, Any] = {}
    decision_criteria: dict[str, Any] = {}
    explanation_text: str | None = None
    explanation_requested_at: datetime | None = None
    explanation_provided_at: datetime | None = None
    human_review_requested: bool = False
    human_review_completed_at: datetime | None = None
    human_review_decision: str | None = None
    human_reviewer_id: str | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class AutomatedDecisionListResponse(BaseModel):
    """Paginated list of automated decision explanations."""
    decisions: list[AutomatedDecisionResponse]
    total: int
    limit: int
    offset: int


class AutomatedDecisionCreate(WeDoBaseModel):
    """Schema for creating an automated decision record."""
    decision_type: DecisionTypeEnum = Field(..., description="Type of decision")
    candidate_id: str | None = Field(None, description="Candidate ID")
    vacancy_id: str | None = Field(None, description="Vacancy ID")
    ai_model_used: str | None = Field(None, description="AI model version used")
    input_criteria: dict[str, Any] = Field(default={}, description="Input data criteria used")
    decision_criteria: dict[str, Any] = Field(default={}, description="Decision criteria and weights")
    explanation_text: str | None = Field(None, description="Human-readable explanation")

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


class HumanReviewRequest(WeDoBaseModel):
    """Schema for requesting human review of an automated decision."""
    reason: str | None = Field(None, description="Reason for requesting human review")
    requested_by: str | None = Field(None, description="ID of the data subject requesting review")

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
    notes: str | None = Field(None, description="Additional notes")

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
