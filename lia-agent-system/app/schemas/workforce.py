"""
Pydantic schemas for Workforce Planning module.
"""
from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from app.shared.types import WeDoBaseModel


class HiringPlanBase(BaseModel):
    fiscal_year: int
    name: str
    description: str | None = None
    status: str | None = "draft"
    owner_name: str | None = None
    owner_email: str | None = None
    total_headcount: int | None = 0
    total_budget: float | None = None
    currency: str | None = "BRL"
    ai_source_metadata: dict[str, Any] | None = {}


class HiringPlanCreate(HiringPlanBase):
    company_id: UUID  # Required - must specify which company this plan belongs to


class HiringPlanUpdate(WeDoBaseModel):
    fiscal_year: int | None = None
    name: str | None = None
    description: str | None = None
    status: str | None = None
    owner_name: str | None = None
    owner_email: str | None = None
    total_headcount: int | None = None
    total_budget: float | None = None
    currency: str | None = None
    ai_source_metadata: dict[str, Any] | None = None
    is_active: bool | None = None


class HiringPlanResponse(HiringPlanBase):
    id: UUID
    company_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    
    class Config:
        from_attributes = True


class PlannedHeadcountBase(BaseModel):
    target_month: int
    target_year: int
    title: str
    level: str | None = None
    contract_type: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = "BRL"
    headcount: int | None = 1
    justification: str | None = None
    hiring_manager_name: str | None = None
    hiring_manager_email: str | None = None
    technical_profile: dict[str, Any] | None = {}
    behavioral_profile: dict[str, Any] | None = {}
    job_description: str | None = None
    priority: str | None = "medium"
    hiring_window_start: date | None = None
    hiring_window_end: date | None = None
    status: str | None = "planned"
    notes: str | None = None


class PlannedHeadcountCreate(PlannedHeadcountBase):
    hiring_plan_id: UUID
    department_id: UUID | None = None
    ideal_profile_id: UUID | None = None


class PlannedHeadcountUpdate(WeDoBaseModel):
    target_month: int | None = None
    target_year: int | None = None
    title: str | None = None
    level: str | None = None
    contract_type: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
    headcount: int | None = None
    justification: str | None = None
    hiring_manager_name: str | None = None
    hiring_manager_email: str | None = None
    technical_profile: dict[str, Any] | None = None
    behavioral_profile: dict[str, Any] | None = None
    job_description: str | None = None
    priority: str | None = None
    hiring_window_start: date | None = None
    hiring_window_end: date | None = None
    status: str | None = None
    notes: str | None = None
    department_id: UUID | None = None
    ideal_profile_id: UUID | None = None
    linked_vacancy_id: UUID | None = None
    is_active: bool | None = None


class PlannedHeadcountResponse(PlannedHeadcountBase):
    id: UUID
    hiring_plan_id: UUID
    department_id: UUID | None
    ideal_profile_id: UUID | None
    linked_vacancy_id: UUID | None
    ai_generated: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ImportJobBase(BaseModel):
    file_name: str
    file_type: str
    status: str | None = "pending"
    total_rows: int | None = 0
    imported_rows: int | None = 0
    error_rows: int | None = 0
    errors: list[dict[str, Any]] | None = []
    column_mapping: dict[str, str] | None = {}
    ai_suggestions: dict[str, Any] | None = {}


class ImportJobCreate(WeDoBaseModel):
    hiring_plan_id: UUID
    file_name: str
    file_type: str
    column_mapping: dict[str, str] | None = {}


class ImportJobResponse(ImportJobBase):
    id: UUID
    hiring_plan_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    
    class Config:
        from_attributes = True


class HiringPlanWithDetails(HiringPlanResponse):
    planned_headcounts: list[PlannedHeadcountResponse] = []
    import_jobs: list[ImportJobResponse] = []


class ImportRowValidation(BaseModel):
    row_number: int
    data: dict[str, Any]
    is_valid: bool
    errors: list[str] = []
    warnings: list[str] = []
    suggested_corrections: dict[str, Any] | None = None


class ImportPreview(BaseModel):
    file_name: str
    file_type: str
    total_rows: int
    valid_rows: int
    error_rows: int
    detected_columns: list[str]
    column_mapping: dict[str, str]
    ai_suggested_mapping: dict[str, str] | None = None
    sample_data: list[dict[str, Any]] = []
    row_validations: list[ImportRowValidation] = []
    can_proceed: bool
    validation_summary: dict[str, Any] = {}


class ImportConfirm(BaseModel):
    import_job_id: UUID
    column_mapping: dict[str, str]
    skip_invalid_rows: bool | None = False
    apply_ai_corrections: bool | None = True
    rows_to_import: list[int] | None = None


class ImportResult(BaseModel):
    success: bool
    import_job_id: UUID
    total_rows: int
    imported_rows: int
    error_rows: int
    errors: list[dict[str, Any]] = []
    created_headcount_ids: list[UUID] = []


class MonthlyHeadcountStats(BaseModel):
    month: int
    year: int
    total_headcount: int
    by_status: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    by_department: dict[str, int] = {}


class WorkforcePlanningStats(BaseModel):
    hiring_plan_id: UUID
    fiscal_year: int
    total_planned_headcount: int
    total_filled: int
    total_in_progress: int
    total_pending: int
    total_cancelled: int
    fill_rate: float
    total_budget: float | None = None
    budget_utilized: float | None = None
    monthly_breakdown: list[MonthlyHeadcountStats] = []
    by_department: dict[str, int] = {}
    by_level: dict[str, int] = {}
    by_contract_type: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    avg_time_to_fill: float | None = None
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
    department_summary: list[DepartmentHeadcountSummary] = []
