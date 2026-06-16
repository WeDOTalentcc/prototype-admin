"""
Pydantic schemas for Business Continuity API.

Includes schemas for:
- Critical processes (BIA - Business Impact Analysis)
- DR Plans (Disaster Recovery)
- Continuity tests
- Dashboard and statistics
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class ProcessCriticalityEnum(str, Enum):
    """Criticality levels for processes."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProcessStatusEnum(str, Enum):
    """Status of processes."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNDER_REVIEW = "under_review"


class PlanStatusEnum(str, Enum):
    """Status of DR plans."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    OUTDATED = "outdated"
    ARCHIVED = "archived"


class PlanTypeEnum(str, Enum):
    """Types of continuity plans."""
    DISASTER_RECOVERY = "disaster_recovery"
    BUSINESS_CONTINUITY = "business_continuity"
    INCIDENT_RESPONSE = "incident_response"
    CRISIS_MANAGEMENT = "crisis_management"


class TestStatusEnum(str, Enum):
    """Status of continuity tests."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TestTypeEnum(str, Enum):
    """Types of continuity tests."""
    TABLETOP = "tabletop"
    WALKTHROUGH = "walkthrough"
    SIMULATION = "simulation"
    FULL_TEST = "full_test"


class TestResultEnum(str, Enum):
    """Results of continuity tests."""
    PASSED = "passed"
    PARTIAL = "partial"
    FAILED = "failed"
    NOT_APPLICABLE = "not_applicable"


class CriticalProcessResponse(BaseModel):
    """Response schema for critical process."""
    id: str
    company_id: str
    name: str
    description: Optional[str] = None
    criticality: str
    status: str
    owner: Optional[str] = None
    owner_email: Optional[str] = None
    department: Optional[str] = None
    rto_hours: Optional[int] = None
    rpo_hours: Optional[int] = None
    mtpd_hours: Optional[int] = None
    dependencies: List[str] = []
    recovery_procedures: Optional[str] = None
    last_bia_date: Optional[date] = None
    next_review_date: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CriticalProcessListResponse(BaseModel):
    """Paginated list of critical processes."""
    processes: List[CriticalProcessResponse]
    total: int
    limit: int
    offset: int


class CriticalProcessCreate(BaseModel):
    """Schema for creating a critical process."""
    name: str = Field(..., min_length=3, max_length=255, description="Process name")
    description: Optional[str] = Field(None, description="Process description")
    criticality: ProcessCriticalityEnum = Field(..., description="Process criticality")
    owner: Optional[str] = Field(None, description="Process owner name")
    owner_email: Optional[str] = Field(None, description="Process owner email")
    department: Optional[str] = Field(None, description="Department")
    rto_hours: Optional[int] = Field(None, ge=0, description="Recovery Time Objective in hours")
    rpo_hours: Optional[int] = Field(None, ge=0, description="Recovery Point Objective in hours")
    mtpd_hours: Optional[int] = Field(None, ge=0, description="Maximum Tolerable Period of Disruption in hours")
    dependencies: List[str] = Field(default=[], description="Process dependencies")
    recovery_procedures: Optional[str] = Field(None, description="Recovery procedures")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Candidate Screening System",
                "description": "AI-powered candidate screening and scoring system",
                "criticality": "critical",
                "owner": "João Silva",
                "owner_email": "joao.silva@empresa.com.br",
                "department": "Technology",
                "rto_hours": 4,
                "rpo_hours": 1,
                "mtpd_hours": 24,
                "dependencies": ["Database", "AI Models", "Email Service"],
                "recovery_procedures": "1. Restore from backup\n2. Validate data integrity\n3. Resume processing"
            }
        }


class CriticalProcessUpdate(BaseModel):
    """Schema for updating a critical process."""
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    criticality: Optional[ProcessCriticalityEnum] = None
    status: Optional[ProcessStatusEnum] = None
    owner: Optional[str] = None
    owner_email: Optional[str] = None
    department: Optional[str] = None
    rto_hours: Optional[int] = Field(None, ge=0)
    rpo_hours: Optional[int] = Field(None, ge=0)
    mtpd_hours: Optional[int] = Field(None, ge=0)
    dependencies: Optional[List[str]] = None
    recovery_procedures: Optional[str] = None
    next_review_date: Optional[date] = None


class DRPlanResponse(BaseModel):
    """Response schema for DR plan."""
    id: str
    company_id: str
    name: str
    description: Optional[str] = None
    plan_type: str
    status: str
    version: str
    processes_covered: List[str] = []
    recovery_strategies: Optional[str] = None
    communication_plan: Optional[str] = None
    escalation_matrix: Optional[Dict[str, Any]] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    last_tested_at: Optional[datetime] = None
    next_test_date: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DRPlanListResponse(BaseModel):
    """Paginated list of DR plans."""
    plans: List[DRPlanResponse]
    total: int
    limit: int
    offset: int


class DRPlanCreate(BaseModel):
    """Schema for creating a DR plan."""
    name: str = Field(..., min_length=5, max_length=255, description="Plan name")
    description: Optional[str] = Field(None, description="Plan description")
    plan_type: PlanTypeEnum = Field(default=PlanTypeEnum.DISASTER_RECOVERY, description="Plan type")
    processes_covered: List[str] = Field(default=[], description="Covered process IDs")
    recovery_strategies: Optional[str] = Field(None, description="Recovery strategies")
    communication_plan: Optional[str] = Field(None, description="Communication plan")
    escalation_matrix: Optional[Dict[str, Any]] = Field(None, description="Escalation matrix")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "IT Infrastructure DR Plan",
                "description": "Disaster recovery plan for core IT infrastructure",
                "plan_type": "disaster_recovery",
                "processes_covered": ["550e8400-e29b-41d4-a716-446655440000"],
                "recovery_strategies": "1. Failover to secondary site\n2. Restore from backups",
                "communication_plan": "Notify stakeholders within 30 minutes",
                "escalation_matrix": {
                    "level_1": {"contact": "IT Manager", "time_minutes": 15},
                    "level_2": {"contact": "CTO", "time_minutes": 30}
                }
            }
        }


class DRPlanUpdate(BaseModel):
    """Schema for updating a DR plan."""
    name: Optional[str] = Field(None, min_length=5, max_length=255)
    description: Optional[str] = None
    plan_type: Optional[PlanTypeEnum] = None
    status: Optional[PlanStatusEnum] = None
    processes_covered: Optional[List[str]] = None
    recovery_strategies: Optional[str] = None
    communication_plan: Optional[str] = None
    escalation_matrix: Optional[Dict[str, Any]] = None
    next_test_date: Optional[date] = None


class DRPlanApproval(BaseModel):
    """Schema for approving a DR plan."""
    approved_by: str = Field(..., description="Approver ID")
    version: Optional[str] = Field(None, description="Version number")
    notes: Optional[str] = Field(None, description="Approval notes")

    class Config:
        json_schema_extra = {
            "example": {
                "approved_by": "770e8400-e29b-41d4-a716-446655440002",
                "version": "2.0",
                "notes": "Approved after annual review and updates"
            }
        }


class ContinuityTestResponse(BaseModel):
    """Response schema for continuity test."""
    id: str
    company_id: str
    plan_id: str
    plan_name: Optional[str] = None
    test_type: str
    name: str
    description: Optional[str] = None
    scheduled_date: date
    status: str
    result: Optional[str] = None
    actual_rto_achieved: Optional[int] = None
    actual_rpo_achieved: Optional[int] = None
    participants: List[str] = []
    findings: Optional[str] = None
    recommendations: List[str] = []
    conducted_by: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ContinuityTestListResponse(BaseModel):
    """Paginated list of continuity tests."""
    tests: List[ContinuityTestResponse]
    total: int
    limit: int
    offset: int


class ContinuityTestCreate(BaseModel):
    """Schema for creating a continuity test."""
    plan_id: str = Field(..., description="DR plan ID")
    test_type: TestTypeEnum = Field(..., description="Test type")
    name: str = Field(..., min_length=5, max_length=255, description="Test name")
    description: Optional[str] = Field(None, description="Test description")
    scheduled_date: date = Field(..., description="Scheduled date")
    participants: List[str] = Field(default=[], description="Participant names")

    class Config:
        json_schema_extra = {
            "example": {
                "plan_id": "550e8400-e29b-41d4-a716-446655440000",
                "test_type": "simulation",
                "name": "Q1 2024 DR Simulation",
                "description": "Quarterly disaster recovery simulation test",
                "scheduled_date": "2024-03-15",
                "participants": ["João Silva", "Maria Santos", "Pedro Costa"]
            }
        }


class ContinuityTestUpdate(BaseModel):
    """Schema for updating a continuity test."""
    test_type: Optional[TestTypeEnum] = None
    name: Optional[str] = Field(None, min_length=5, max_length=255)
    description: Optional[str] = None
    scheduled_date: Optional[date] = None
    status: Optional[TestStatusEnum] = None
    result: Optional[TestResultEnum] = None
    actual_rto_achieved: Optional[int] = Field(None, ge=0)
    actual_rpo_achieved: Optional[int] = Field(None, ge=0)
    participants: Optional[List[str]] = None
    findings: Optional[str] = None
    recommendations: Optional[List[str]] = None
    conducted_by: Optional[str] = None


class ContinuityDashboard(BaseModel):
    """Dashboard data for business continuity."""
    total_processes: int = 0
    by_criticality: Dict[str, int] = {}
    total_plans: int = 0
    approved_plans: int = 0
    outdated_plans: int = 0
    pending_tests: int = 0
    upcoming_tests: List[Dict[str, Any]] = []
    rto_gaps: List[Dict[str, Any]] = []
    rpo_gaps: List[Dict[str, Any]] = []
    last_test_results: Dict[str, int] = {}


class ContinuityStats(BaseModel):
    """Continuity statistics."""
    total_processes: int = 0
    by_criticality: Dict[str, int] = {}
    total_plans: int = 0
    by_plan_status: Dict[str, int] = {}
    by_plan_type: Dict[str, int] = {}
    total_tests: int = 0
    by_test_status: Dict[str, int] = {}
    by_test_result: Dict[str, int] = {}
    average_rto_gap_percent: float = 0.0
    average_rpo_gap_percent: float = 0.0
