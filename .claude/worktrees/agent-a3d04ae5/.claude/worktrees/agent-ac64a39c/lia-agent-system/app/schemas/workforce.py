"""
Pydantic schemas for Workforce Planning module.
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID


class HiringPlanBase(BaseModel):
    fiscal_year: int
    name: str
    description: Optional[str] = None
    status: Optional[str] = "draft"
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    total_headcount: Optional[int] = 0
    total_budget: Optional[float] = None
    currency: Optional[str] = "BRL"
    ai_source_metadata: Optional[Dict[str, Any]] = {}


class HiringPlanCreate(HiringPlanBase):
    company_id: UUID  # Required - must specify which company this plan belongs to


class HiringPlanUpdate(BaseModel):
    fiscal_year: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    total_headcount: Optional[int] = None
    total_budget: Optional[float] = None
    currency: Optional[str] = None
    ai_source_metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class HiringPlanResponse(HiringPlanBase):
    id: UUID
    company_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    
    class Config:
        from_attributes = True


class PlannedHeadcountBase(BaseModel):
    target_month: int
    target_year: int
    title: str
    level: Optional[str] = None
    contract_type: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = "BRL"
    headcount: Optional[int] = 1
    justification: Optional[str] = None
    hiring_manager_name: Optional[str] = None
    hiring_manager_email: Optional[str] = None
    technical_profile: Optional[Dict[str, Any]] = {}
    behavioral_profile: Optional[Dict[str, Any]] = {}
    job_description: Optional[str] = None
    priority: Optional[str] = "medium"
    hiring_window_start: Optional[date] = None
    hiring_window_end: Optional[date] = None
    status: Optional[str] = "planned"
    notes: Optional[str] = None


class PlannedHeadcountCreate(PlannedHeadcountBase):
    hiring_plan_id: UUID
    department_id: Optional[UUID] = None
    ideal_profile_id: Optional[UUID] = None


class PlannedHeadcountUpdate(BaseModel):
    target_month: Optional[int] = None
    target_year: Optional[int] = None
    title: Optional[str] = None
    level: Optional[str] = None
    contract_type: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    headcount: Optional[int] = None
    justification: Optional[str] = None
    hiring_manager_name: Optional[str] = None
    hiring_manager_email: Optional[str] = None
    technical_profile: Optional[Dict[str, Any]] = None
    behavioral_profile: Optional[Dict[str, Any]] = None
    job_description: Optional[str] = None
    priority: Optional[str] = None
    hiring_window_start: Optional[date] = None
    hiring_window_end: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    department_id: Optional[UUID] = None
    ideal_profile_id: Optional[UUID] = None
    linked_vacancy_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class PlannedHeadcountResponse(PlannedHeadcountBase):
    id: UUID
    hiring_plan_id: UUID
    department_id: Optional[UUID]
    ideal_profile_id: Optional[UUID]
    linked_vacancy_id: Optional[UUID]
    ai_generated: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ImportJobBase(BaseModel):
    file_name: str
    file_type: str
    status: Optional[str] = "pending"
    total_rows: Optional[int] = 0
    imported_rows: Optional[int] = 0
    error_rows: Optional[int] = 0
    errors: Optional[List[Dict[str, Any]]] = []
    column_mapping: Optional[Dict[str, str]] = {}
    ai_suggestions: Optional[Dict[str, Any]] = {}


class ImportJobCreate(BaseModel):
    hiring_plan_id: UUID
    file_name: str
    file_type: str
    column_mapping: Optional[Dict[str, str]] = {}


class ImportJobResponse(ImportJobBase):
    id: UUID
    hiring_plan_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    
    class Config:
        from_attributes = True


class HiringPlanWithDetails(HiringPlanResponse):
    planned_headcounts: List[PlannedHeadcountResponse] = []
    import_jobs: List[ImportJobResponse] = []


class ImportRowValidation(BaseModel):
    row_number: int
    data: Dict[str, Any]
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    suggested_corrections: Optional[Dict[str, Any]] = None


class ImportPreview(BaseModel):
    file_name: str
    file_type: str
    total_rows: int
    valid_rows: int
    error_rows: int
    detected_columns: List[str]
    column_mapping: Dict[str, str]
    ai_suggested_mapping: Optional[Dict[str, str]] = None
    sample_data: List[Dict[str, Any]] = []
    row_validations: List[ImportRowValidation] = []
    can_proceed: bool
    validation_summary: Dict[str, Any] = {}


class ImportConfirm(BaseModel):
    import_job_id: UUID
    column_mapping: Dict[str, str]
    skip_invalid_rows: Optional[bool] = False
    apply_ai_corrections: Optional[bool] = True
    rows_to_import: Optional[List[int]] = None


class ImportResult(BaseModel):
    success: bool
    import_job_id: UUID
    total_rows: int
    imported_rows: int
    error_rows: int
    errors: List[Dict[str, Any]] = []
    created_headcount_ids: List[UUID] = []


class MonthlyHeadcountStats(BaseModel):
    month: int
    year: int
    total_headcount: int
    by_status: Dict[str, int] = {}
    by_priority: Dict[str, int] = {}
    by_department: Dict[str, int] = {}


class WorkforcePlanningStats(BaseModel):
    hiring_plan_id: UUID
    fiscal_year: int
    total_planned_headcount: int
    total_filled: int
    total_in_progress: int
    total_pending: int
    total_cancelled: int
    fill_rate: float
    total_budget: Optional[float] = None
    budget_utilized: Optional[float] = None
    monthly_breakdown: List[MonthlyHeadcountStats] = []
    by_department: Dict[str, int] = {}
    by_level: Dict[str, int] = {}
    by_contract_type: Dict[str, int] = {}
    by_priority: Dict[str, int] = {}
    avg_time_to_fill: Optional[float] = None
    positions_at_risk: int = 0


class DepartmentHeadcountSummary(BaseModel):
    department_id: UUID
    department_name: str
    total_headcount: int
    filled: int
    in_progress: int
    pending: int


class HiringPlanSummary(BaseModel):
    id: UUID
    fiscal_year: int
    name: str
    status: str
    total_headcount: int
    filled_count: int
    in_progress_count: int
    pending_count: int
    fill_rate: float
    department_summary: List[DepartmentHeadcountSummary] = []
