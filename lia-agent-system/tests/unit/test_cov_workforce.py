"""Coverage tests for app/schemas/workforce.py — Pydantic models."""
import pytest
from datetime import date, datetime
from uuid import UUID
from app.schemas.workforce import (
    HiringPlanBase,
    HiringPlanCreate,
    HiringPlanUpdate,
    HiringPlanResponse,
    HiringPlanWithDetails,
    HiringPlanSummary,
    PlannedHeadcountBase,
    PlannedHeadcountCreate,
    PlannedHeadcountUpdate,
    PlannedHeadcountResponse,
    ImportJobBase,
    ImportJobCreate,
    ImportJobResponse,
    ImportRowValidation,
    ImportPreview,
    ImportConfirm,
    ImportResult,
    MonthlyHeadcountStats,
    WorkforcePlanningStats,
    DepartmentHeadcountSummary,
)

_UUID1 = UUID("550e8400-e29b-41d4-a716-446655440001")
_UUID2 = UUID("550e8400-e29b-41d4-a716-446655440002")
_UUID3 = UUID("550e8400-e29b-41d4-a716-446655440003")
_DT = datetime(2024, 1, 15, 10, 30)


class TestHiringPlanBase:
    def test_basic(self):
        m = HiringPlanBase(fiscal_year=2025, name="Plan A")
        assert m.fiscal_year == 2025
        assert m.name == "Plan A"

    def test_defaults(self):
        m = HiringPlanBase(fiscal_year=2024, name="Plan B")
        assert m.status == "draft"
        assert m.total_headcount == 0
        assert m.currency == "BRL"
        assert m.description is None

    def test_full(self):
        m = HiringPlanBase(
            fiscal_year=2025,
            name="Full Plan",
            description="Full description",
            status="active",
            owner_name="Ana",
            owner_email="ana@co.com",
            total_headcount=10,
            total_budget=500000.0,
            currency="USD",
        )
        assert m.total_budget == 500000.0
        assert m.owner_name == "Ana"


class TestHiringPlanCreate:
    def test_basic(self):
        m = HiringPlanCreate(fiscal_year=2025, name="Plan C", company_id=_UUID1)
        assert m.company_id == _UUID1
        assert m.fiscal_year == 2025

    def test_inherits_defaults(self):
        m = HiringPlanCreate(fiscal_year=2025, name="Plan D", company_id=_UUID1)
        assert m.status == "draft"
        assert m.currency == "BRL"


class TestHiringPlanUpdate:
    def test_all_optional(self):
        m = HiringPlanUpdate()
        assert m.fiscal_year is None
        assert m.name is None
        assert m.status is None

    def test_partial_update(self):
        m = HiringPlanUpdate(status="active", total_headcount=5)
        assert m.status == "active"
        assert m.total_headcount == 5


class TestHiringPlanResponse:
    def test_basic(self):
        m = HiringPlanResponse(
            fiscal_year=2025,
            name="Plan R",
            id=_UUID1,
            company_id=_UUID2,
            is_active=True,
            created_at=_DT,
            updated_at=_DT,
            created_by="user@co.com",
        )
        assert m.id == _UUID1
        assert m.is_active is True
        assert m.created_by == "user@co.com"

    def test_created_by_none(self):
        m = HiringPlanResponse(
            fiscal_year=2025, name="Plan R2",
            id=_UUID1, company_id=_UUID2,
            is_active=False, created_at=_DT, updated_at=_DT,
            created_by=None,
        )
        assert m.created_by is None


class TestHiringPlanWithDetails:
    def test_empty_lists(self):
        m = HiringPlanWithDetails(
            fiscal_year=2025, name="Detailed",
            id=_UUID1, company_id=_UUID2,
            is_active=True, created_at=_DT, updated_at=_DT,
            created_by=None,
        )
        assert m.planned_headcounts == []
        assert m.import_jobs == []


class TestHiringPlanSummary:
    def test_basic(self):
        m = HiringPlanSummary(
            id=_UUID1,
            fiscal_year=2025,
            name="Summary Plan",
            status="active",
            total_headcount=20,
            filled_count=10,
            in_progress_count=5,
            pending_count=5,
            fill_rate=0.5,
        )
        assert m.fill_rate == pytest.approx(0.5)
        assert m.department_summary == []

    def test_with_departments(self):
        dept = DepartmentHeadcountSummary(
            department_id=_UUID1,
            department_name="Engineering",
            total_headcount=10,
            filled=5,
            in_progress=2,
            pending=3,
        )
        m = HiringPlanSummary(
            id=_UUID2, fiscal_year=2024, name="With Depts",
            status="draft", total_headcount=10,
            filled_count=5, in_progress_count=2,
            pending_count=3, fill_rate=0.5,
            department_summary=[dept],
        )
        assert len(m.department_summary) == 1


class TestPlannedHeadcountBase:
    def test_basic(self):
        m = PlannedHeadcountBase(target_month=3, target_year=2025, title="Backend Dev")
        assert m.target_month == 3
        assert m.target_year == 2025
        assert m.title == "Backend Dev"

    def test_defaults(self):
        m = PlannedHeadcountBase(target_month=1, target_year=2025, title="Dev")
        assert m.headcount == 1
        assert m.priority == "medium"
        assert m.status == "planned"
        assert m.salary_currency == "BRL"

    def test_full(self):
        m = PlannedHeadcountBase(
            target_month=6, target_year=2025, title="Senior Dev",
            level="senior", contract_type="CLT",
            salary_min=10000.0, salary_max=15000.0,
            headcount=2, justification="Growth",
        )
        assert m.salary_min == pytest.approx(10000.0)
        assert m.headcount == 2


class TestPlannedHeadcountCreate:
    def test_basic(self):
        m = PlannedHeadcountCreate(
            target_month=3, target_year=2025, title="Dev",
            hiring_plan_id=_UUID1,
        )
        assert m.hiring_plan_id == _UUID1
        assert m.department_id is None

    def test_with_department(self):
        m = PlannedHeadcountCreate(
            target_month=3, target_year=2025, title="PM",
            hiring_plan_id=_UUID1,
            department_id=_UUID2,
            ideal_profile_id=_UUID3,
        )
        assert m.department_id == _UUID2
        assert m.ideal_profile_id == _UUID3


class TestPlannedHeadcountUpdate:
    def test_all_optional(self):
        m = PlannedHeadcountUpdate()
        assert m.title is None
        assert m.headcount is None
        assert m.status is None


class TestPlannedHeadcountResponse:
    def test_basic(self):
        m = PlannedHeadcountResponse(
            target_month=3, target_year=2025, title="Dev",
            id=_UUID1, hiring_plan_id=_UUID2,
            department_id=None, ideal_profile_id=None,
            linked_vacancy_id=None,
            ai_generated=False, is_active=True,
            created_at=_DT, updated_at=_DT,
        )
        assert m.id == _UUID1
        assert m.ai_generated is False
        assert m.linked_vacancy_id is None


class TestImportJobBase:
    def test_basic(self):
        m = ImportJobBase(file_name="headcount.xlsx", file_type="xlsx")
        assert m.file_name == "headcount.xlsx"
        assert m.file_type == "xlsx"

    def test_defaults(self):
        m = ImportJobBase(file_name="data.csv", file_type="csv")
        assert m.status == "pending"
        assert m.total_rows == 0
        assert m.imported_rows == 0
        assert m.error_rows == 0


class TestImportJobCreate:
    def test_basic(self):
        m = ImportJobCreate(
            hiring_plan_id=_UUID1,
            file_name="upload.csv",
            file_type="csv",
        )
        assert m.hiring_plan_id == _UUID1
        assert m.column_mapping == {}


class TestImportJobResponse:
    def test_basic(self):
        m = ImportJobResponse(
            file_name="file.csv",
            file_type="csv",
            id=_UUID1,
            hiring_plan_id=_UUID2,
            created_at=_DT,
            updated_at=_DT,
            created_by="admin",
        )
        assert m.id == _UUID1
        assert m.created_by == "admin"


class TestImportRowValidation:
    def test_valid(self):
        m = ImportRowValidation(
            row_number=1,
            data={"title": "Dev", "month": 3},
            is_valid=True,
        )
        assert m.row_number == 1
        assert m.is_valid is True
        assert m.errors == []

    def test_invalid(self):
        m = ImportRowValidation(
            row_number=5,
            data={"title": ""},
            is_valid=False,
            errors=["Title cannot be empty"],
        )
        assert m.is_valid is False
        assert len(m.errors) == 1


class TestImportPreview:
    def test_basic(self):
        m = ImportPreview(
            file_name="data.csv",
            file_type="csv",
            total_rows=100,
            valid_rows=95,
            error_rows=5,
            detected_columns=["title", "month", "year"],
            column_mapping={"title": "title"},
            can_proceed=True,
        )
        assert m.total_rows == 100
        assert m.can_proceed is True
        assert m.sample_data == []
        assert m.ai_suggested_mapping is None


class TestImportConfirm:
    def test_basic(self):
        m = ImportConfirm(
            import_job_id=_UUID1,
            column_mapping={"title": "title"},
        )
        assert m.import_job_id == _UUID1
        assert m.skip_invalid_rows is False
        assert m.apply_ai_corrections is True

    def test_with_rows(self):
        m = ImportConfirm(
            import_job_id=_UUID1,
            column_mapping={},
            skip_invalid_rows=True,
            rows_to_import=[1, 2, 3],
        )
        assert m.rows_to_import == [1, 2, 3]


class TestImportResult:
    def test_success(self):
        m = ImportResult(
            success=True,
            import_job_id=_UUID1,
            total_rows=10,
            imported_rows=10,
            error_rows=0,
        )
        assert m.success is True
        assert m.errors == []
        assert m.created_headcount_ids == []

    def test_partial_failure(self):
        m = ImportResult(
            success=False,
            import_job_id=_UUID1,
            total_rows=10,
            imported_rows=8,
            error_rows=2,
            errors=[{"row": 3, "msg": "bad data"}],
        )
        assert m.error_rows == 2
        assert len(m.errors) == 1


class TestMonthlyHeadcountStats:
    def test_basic(self):
        m = MonthlyHeadcountStats(month=3, year=2025, total_headcount=15)
        assert m.month == 3
        assert m.year == 2025
        assert m.total_headcount == 15
        assert m.by_status == {}

    def test_with_breakdowns(self):
        m = MonthlyHeadcountStats(
            month=6, year=2025, total_headcount=20,
            by_status={"planned": 15, "filled": 5},
            by_priority={"high": 8, "medium": 12},
        )
        assert m.by_status["planned"] == 15


class TestWorkforcePlanningStats:
    def test_basic(self):
        m = WorkforcePlanningStats(
            hiring_plan_id=_UUID1,
            fiscal_year=2025,
            total_planned_headcount=50,
            total_filled=20,
            total_in_progress=10,
            total_pending=15,
            total_cancelled=5,
            fill_rate=0.4,
        )
        assert m.total_planned_headcount == 50
        assert m.fill_rate == pytest.approx(0.4)
        assert m.monthly_breakdown == []
        assert m.positions_at_risk == 0

    def test_with_budget(self):
        m = WorkforcePlanningStats(
            hiring_plan_id=_UUID1,
            fiscal_year=2025,
            total_planned_headcount=10,
            total_filled=5,
            total_in_progress=2,
            total_pending=2,
            total_cancelled=1,
            fill_rate=0.5,
            total_budget=1000000.0,
            budget_utilized=500000.0,
        )
        assert m.total_budget == pytest.approx(1000000.0)


class TestDepartmentHeadcountSummary:
    def test_basic(self):
        m = DepartmentHeadcountSummary(
            department_id=_UUID1,
            department_name="Engineering",
            total_headcount=15,
            filled=8,
            in_progress=4,
            pending=3,
        )
        assert m.department_name == "Engineering"
        assert m.filled == 8
        assert m.in_progress == 4
