"""
Pydantic schemas for Risk Register API.

Includes schemas for:
- Risk management (SOX, ISO 27001, BCB 498 compliance)
- Risk treatments
- Risk matrix and statistics
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class RiskCategoryEnum(str, Enum):
    """Categories of risks."""
    OPERATIONAL = "operational"
    FINANCIAL = "financial"
    STRATEGIC = "strategic"
    COMPLIANCE = "compliance"
    TECHNOLOGY = "technology"
    SECURITY = "security"
    REPUTATIONAL = "reputational"
    LEGAL = "legal"


class RiskStatusEnum(str, Enum):
    """Status of risks."""
    IDENTIFIED = "identified"
    ASSESSED = "assessed"
    TREATED = "treated"
    MONITORED = "monitored"
    CLOSED = "closed"


class RiskLevelEnum(str, Enum):
    """Risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TreatmentStatusEnum(str, Enum):
    """Status of risk treatments."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TreatmentTypeEnum(str, Enum):
    """Types of risk treatment."""
    MITIGATE = "mitigate"
    ACCEPT = "accept"
    TRANSFER = "transfer"
    AVOID = "avoid"


class RiskTreatmentResponse(BaseModel):
    """Response schema for risk treatment."""
    id: str
    risk_id: str
    treatment_type: str
    description: str
    responsible: Optional[str] = None
    due_date: Optional[date] = None
    status: str
    effectiveness: Optional[int] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RiskTreatmentCreate(BaseModel):
    """Schema for creating a risk treatment."""
    treatment_type: TreatmentTypeEnum = Field(..., description="Type of treatment")
    description: str = Field(..., min_length=10, description="Treatment description")
    responsible: Optional[str] = Field(None, description="Person responsible")
    due_date: Optional[date] = Field(None, description="Due date for treatment")
    notes: Optional[str] = Field(None, description="Additional notes")

    class Config:
        json_schema_extra = {
            "example": {
                "treatment_type": "mitigate",
                "description": "Implement additional access controls and monitoring",
                "responsible": "João Silva",
                "due_date": "2024-03-15",
                "notes": "Priority action for Q1"
            }
        }


class RiskTreatmentUpdate(BaseModel):
    """Schema for updating a risk treatment."""
    treatment_type: Optional[TreatmentTypeEnum] = None
    description: Optional[str] = Field(None, min_length=10)
    responsible: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[TreatmentStatusEnum] = None
    effectiveness: Optional[int] = Field(None, ge=0, le=100)
    notes: Optional[str] = None


class RiskResponse(BaseModel):
    """Response schema for risk."""
    id: str
    company_id: str
    title: str
    description: str
    category: str
    status: str
    likelihood: int
    impact: int
    risk_level: str
    risk_score: int
    owner: Optional[str] = None
    owner_email: Optional[str] = None
    identified_at: Optional[datetime] = None
    last_assessed_at: Optional[datetime] = None
    next_review_at: Optional[date] = None
    controls: List[str] = []
    affected_processes: List[str] = []
    compliance_frameworks: List[str] = []
    treatments: List[RiskTreatmentResponse] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RiskListResponse(BaseModel):
    """Paginated list of risks."""
    risks: List[RiskResponse]
    total: int
    limit: int
    offset: int


class RiskCreate(BaseModel):
    """Schema for creating a risk."""
    title: str = Field(..., min_length=5, max_length=255, description="Risk title")
    description: str = Field(..., min_length=10, description="Risk description")
    category: RiskCategoryEnum = Field(..., description="Risk category")
    likelihood: int = Field(..., ge=1, le=5, description="Likelihood (1-5)")
    impact: int = Field(..., ge=1, le=5, description="Impact (1-5)")
    owner: Optional[str] = Field(None, description="Risk owner name")
    owner_email: Optional[str] = Field(None, description="Risk owner email")
    controls: List[str] = Field(default=[], description="Existing controls")
    affected_processes: List[str] = Field(default=[], description="Affected business processes")
    compliance_frameworks: List[str] = Field(default=[], description="Related compliance frameworks")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Unauthorized Access to Sensitive Data",
                "description": "Risk of unauthorized access to candidate PII due to insufficient access controls",
                "category": "security",
                "likelihood": 3,
                "impact": 4,
                "owner": "Maria Silva",
                "owner_email": "maria.silva@empresa.com.br",
                "controls": ["Access control policy", "MFA enabled"],
                "affected_processes": ["Recruitment", "Data Processing"],
                "compliance_frameworks": ["LGPD", "ISO27001", "SOC2"]
            }
        }


class RiskUpdate(BaseModel):
    """Schema for updating a risk."""
    title: Optional[str] = Field(None, min_length=5, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    category: Optional[RiskCategoryEnum] = None
    status: Optional[RiskStatusEnum] = None
    likelihood: Optional[int] = Field(None, ge=1, le=5)
    impact: Optional[int] = Field(None, ge=1, le=5)
    owner: Optional[str] = None
    owner_email: Optional[str] = None
    controls: Optional[List[str]] = None
    affected_processes: Optional[List[str]] = None
    compliance_frameworks: Optional[List[str]] = None
    next_review_at: Optional[date] = None


class RiskMatrixCell(BaseModel):
    """Cell in risk matrix."""
    likelihood: int
    impact: int
    count: int
    risk_level: str
    risk_ids: List[str] = []


class RiskMatrixResponse(BaseModel):
    """Risk matrix response."""
    matrix: List[RiskMatrixCell]
    total_risks: int
    by_level: Dict[str, int]


class RiskStats(BaseModel):
    """Risk statistics."""
    total_risks: int = 0
    by_category: Dict[str, int] = {}
    by_status: Dict[str, int] = {}
    by_level: Dict[str, int] = {}
    overdue_treatments: int = 0
    pending_reviews: int = 0
    average_risk_score: float = 0.0
