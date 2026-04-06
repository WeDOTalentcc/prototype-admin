"""
Workforce Planning API endpoints.
Manages hiring plans, planned headcounts, and import functionality.
"""
import csv
import io
import logging
import uuid
from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.workforce import HiringPlan, ImportJob, PlannedHeadcount, WorkforceEntry
from app.schemas.workforce import (
    HiringPlanCreate,
    HiringPlanResponse,
    HiringPlanUpdate,
    HiringPlanWithDetails,
    ImportConfirm,
    ImportJobResponse,
    ImportPreview,
    ImportResult,
    ImportRowValidation,
    MonthlyHeadcountStats,
    PlannedHeadcountCreate,
    PlannedHeadcountResponse,
    PlannedHeadcountUpdate,
    WorkforcePlanningStats,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workforce", tags=["workforce"])


@router.get("/plans", response_model=list[HiringPlanResponse])
async def list_hiring_plans(
    company_id: uuid.UUID | None = Query(None),
    fiscal_year: int | None = Query(None),
    status: str | None = Query(None),
    include_inactive: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List all hiring plans with optional filters."""
    try:
        query = select(HiringPlan)
        
        if company_id:
            query = query.where(HiringPlan.company_id == company_id)
        
        if fiscal_year:
            query = query.where(HiringPlan.fiscal_year == fiscal_year)
        
        if status:
            query = query.where(HiringPlan.status == status)
        
        if not include_inactive:
            query = query.where(HiringPlan.is_active == True)
        
        query = query.order_by(HiringPlan.fiscal_year.desc(), HiringPlan.created_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        plans = result.scalars().all()
        
        return plans
    except Exception as e:
        logger.error(f"Error listing hiring plans: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plans", response_model=HiringPlanResponse)
async def create_hiring_plan(
    data: HiringPlanCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new hiring plan."""
    try:
        plan = HiringPlan(**data.model_dump())
        
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        
        logger.info(f"Created hiring plan: {plan.name} for fiscal year {plan.fiscal_year}")
        return plan
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating hiring plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plans/{plan_id}", response_model=HiringPlanWithDetails)
async def get_hiring_plan(
    plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a hiring plan with all details including headcounts and import jobs."""
    try:
        result = await db.execute(
            select(HiringPlan)
            .options(
                selectinload(HiringPlan.planned_headcounts),
                selectinload(HiringPlan.import_jobs)
            )
            .where(HiringPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            raise HTTPException(status_code=404, detail="Hiring plan not found")
        
        active_headcounts = [h for h in plan.planned_headcounts if h.is_active]
        
        response = HiringPlanWithDetails.model_validate(plan)
        response.planned_headcounts = [PlannedHeadcountResponse.model_validate(h) for h in active_headcounts]
        response.import_jobs = [ImportJobResponse.model_validate(j) for j in plan.import_jobs]
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching hiring plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/plans/{plan_id}", response_model=HiringPlanResponse)
async def update_hiring_plan(
    plan_id: uuid.UUID,
    data: HiringPlanUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing hiring plan."""
    try:
        result = await db.execute(
            select(HiringPlan).where(HiringPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            raise HTTPException(status_code=404, detail="Hiring plan not found")
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(plan, field, value)
        
        plan.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(plan)
        
        logger.info(f"Updated hiring plan: {plan.name}")
        return plan
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating hiring plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/plans/{plan_id}")
async def delete_hiring_plan(
    plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a hiring plan."""
    try:
        result = await db.execute(
            select(HiringPlan).where(HiringPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            raise HTTPException(status_code=404, detail="Hiring plan not found")
        
        plan.is_active = False
        plan.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {"success": True, "message": "Hiring plan deleted"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting hiring plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plans/{plan_id}/headcounts", response_model=list[PlannedHeadcountResponse])
async def list_plan_headcounts(
    plan_id: uuid.UUID,
    status: str | None = Query(None),
    priority: str | None = Query(None),
    department_id: uuid.UUID | None = Query(None),
    target_month: int | None = Query(None, ge=1, le=12),
    target_year: int | None = Query(None),
    include_inactive: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """List all headcounts for a hiring plan."""
    try:
        result = await db.execute(
            select(HiringPlan).where(HiringPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        if not plan:
            raise HTTPException(status_code=404, detail="Hiring plan not found")
        
        query = select(PlannedHeadcount).where(PlannedHeadcount.hiring_plan_id == plan_id)
        
        if status:
            query = query.where(PlannedHeadcount.status == status)
        
        if priority:
            query = query.where(PlannedHeadcount.priority == priority)
        
        if department_id:
            query = query.where(PlannedHeadcount.department_id == department_id)
        
        if target_month:
            query = query.where(PlannedHeadcount.target_month == target_month)
        
        if target_year:
            query = query.where(PlannedHeadcount.target_year == target_year)
        
        if not include_inactive:
            query = query.where(PlannedHeadcount.is_active == True)
        
        query = query.order_by(
            PlannedHeadcount.target_year,
            PlannedHeadcount.target_month,
            PlannedHeadcount.priority.desc()
        )
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        headcounts = result.scalars().all()
        
        return headcounts
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing headcounts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plans/{plan_id}/headcounts", response_model=PlannedHeadcountResponse)
async def create_headcount(
    plan_id: uuid.UUID,
    data: PlannedHeadcountCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new planned headcount."""
    try:
        result = await db.execute(
            select(HiringPlan).where(HiringPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        if not plan:
            raise HTTPException(status_code=404, detail="Hiring plan not found")
        
        headcount_data = data.model_dump()
        headcount_data['hiring_plan_id'] = plan_id
        
        headcount = PlannedHeadcount(**headcount_data)
        
        db.add(headcount)
        
        plan.total_headcount = (plan.total_headcount or 0) + (headcount.headcount or 1)
        plan.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(headcount)
        
        logger.info(f"Created headcount: {headcount.title} for plan {plan.name}")
        return headcount
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating headcount: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/headcounts/{headcount_id}", response_model=PlannedHeadcountResponse)
async def get_headcount(
    headcount_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific headcount by ID."""
    try:
        result = await db.execute(
            select(PlannedHeadcount).where(PlannedHeadcount.id == headcount_id)
        )
        headcount = result.scalar_one_or_none()
        
        if not headcount:
            raise HTTPException(status_code=404, detail="Headcount not found")
        
        return headcount
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching headcount: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/headcounts/{headcount_id}", response_model=PlannedHeadcountResponse)
async def update_headcount(
    headcount_id: uuid.UUID,
    data: PlannedHeadcountUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing headcount."""
    try:
        result = await db.execute(
            select(PlannedHeadcount).where(PlannedHeadcount.id == headcount_id)
        )
        headcount = result.scalar_one_or_none()
        
        if not headcount:
            raise HTTPException(status_code=404, detail="Headcount not found")
        
        old_headcount_value = headcount.headcount or 1
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(headcount, field, value)
        
        headcount.updated_at = datetime.utcnow()
        
        if 'headcount' in update_data:
            new_headcount_value = update_data['headcount'] or 1
            plan_result = await db.execute(
                select(HiringPlan).where(HiringPlan.id == headcount.hiring_plan_id)
            )
            plan = plan_result.scalar_one_or_none()
            if plan:
                plan.total_headcount = (plan.total_headcount or 0) - old_headcount_value + new_headcount_value
                plan.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(headcount)
        
        logger.info(f"Updated headcount: {headcount.title}")
        return headcount
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating headcount: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/headcounts/{headcount_id}")
async def delete_headcount(
    headcount_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a headcount."""
    try:
        result = await db.execute(
            select(PlannedHeadcount).where(PlannedHeadcount.id == headcount_id)
        )
        headcount = result.scalar_one_or_none()
        
        if not headcount:
            raise HTTPException(status_code=404, detail="Headcount not found")
        
        headcount.is_active = False
        headcount.updated_at = datetime.utcnow()
        
        plan_result = await db.execute(
            select(HiringPlan).where(HiringPlan.id == headcount.hiring_plan_id)
        )
        plan = plan_result.scalar_one_or_none()
        if plan:
            plan.total_headcount = max(0, (plan.total_headcount or 0) - (headcount.headcount or 1))
            plan.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {"success": True, "message": "Headcount deleted"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting headcount: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plans/{plan_id}/headcounts/bulk", response_model=list[PlannedHeadcountResponse])
async def create_headcounts_bulk(
    plan_id: uuid.UUID,
    headcounts: list[PlannedHeadcountCreate],
    db: AsyncSession = Depends(get_db)
):
    """Create multiple headcounts at once."""
    try:
        result = await db.execute(
            select(HiringPlan).where(HiringPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        if not plan:
            raise HTTPException(status_code=404, detail="Hiring plan not found")
        
        created_headcounts = []
        total_new_headcount = 0
        
        for data in headcounts:
            headcount_data = data.model_dump()
            headcount_data['hiring_plan_id'] = plan_id
            
            headcount = PlannedHeadcount(**headcount_data)
            db.add(headcount)
            created_headcounts.append(headcount)
            total_new_headcount += headcount.headcount or 1
        
        plan.total_headcount = (plan.total_headcount or 0) + total_new_headcount
        plan.updated_at = datetime.utcnow()
        
        await db.commit()
        
        for hc in created_headcounts:
            await db.refresh(hc)
        
        logger.info(f"Created {len(created_headcounts)} headcounts in bulk for plan {plan.name}")
        return created_headcounts
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating headcounts in bulk: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plans/{plan_id}/import/upload", response_model=ImportJobResponse)
async def upload_import_file(
    plan_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload a file for import (Excel or CSV)."""
    try:
        result = await db.execute(
            select(HiringPlan).where(HiringPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        if not plan:
            raise HTTPException(status_code=404, detail="Hiring plan not found")
        
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        allowed_extensions = ['.xlsx', '.xls', '.csv']
        file_ext = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        file_type = 'excel' if file_ext in ['.xlsx', '.xls'] else 'csv'
        
        import_job = ImportJob(
            hiring_plan_id=plan_id,
            file_name=file.filename,
            file_type=file_type,
            status="processing"
        )
        
        db.add(import_job)
        await db.commit()
        await db.refresh(import_job)
        
        logger.info(f"Created import job {import_job.id} for file {file.filename}")
        return import_job
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error uploading import file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plans/{plan_id}/import/{job_id}/preview", response_model=ImportPreview)
async def preview_import(
    plan_id: uuid.UUID,
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get preview of import data with validation."""
    try:
        result = await db.execute(
            select(ImportJob).where(
                ImportJob.id == job_id,
                ImportJob.hiring_plan_id == plan_id
            )
        )
        import_job = result.scalar_one_or_none()
        
        if not import_job:
            raise HTTPException(status_code=404, detail="Import job not found")
        
        expected_columns = [
            'title', 'level', 'department', 'target_month', 'target_year',
            'headcount', 'salary_min', 'salary_max', 'priority', 
            'hiring_manager_name', 'hiring_manager_email', 'justification'
        ]
        
        sample_validations = [
            ImportRowValidation(
                row_number=1,
                data={"title": "Software Engineer", "department": "Engineering", "target_month": 1},
                is_valid=True,
                errors=[],
                warnings=[]
            )
        ]
        
        preview = ImportPreview(
            file_name=import_job.file_name,
            file_type=import_job.file_type,
            total_rows=import_job.total_rows,
            valid_rows=import_job.imported_rows,
            error_rows=import_job.error_rows,
            detected_columns=expected_columns,
            column_mapping=import_job.column_mapping or {},
            ai_suggested_mapping=import_job.ai_suggestions.get('column_mapping') if import_job.ai_suggestions else None,
            sample_data=[],
            row_validations=sample_validations,
            can_proceed=import_job.error_rows == 0 or import_job.total_rows > import_job.error_rows,
            validation_summary={
                "total": import_job.total_rows,
                "valid": import_job.imported_rows,
                "errors": import_job.error_rows
            }
        )
        
        return preview
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting import preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plans/{plan_id}/import/{job_id}/confirm", response_model=ImportResult)
async def confirm_import(
    plan_id: uuid.UUID,
    job_id: uuid.UUID,
    data: ImportConfirm,
    db: AsyncSession = Depends(get_db)
):
    """Confirm and execute the import."""
    try:
        result = await db.execute(
            select(ImportJob).where(
                ImportJob.id == job_id,
                ImportJob.hiring_plan_id == plan_id
            )
        )
        import_job = result.scalar_one_or_none()
        
        if not import_job:
            raise HTTPException(status_code=404, detail="Import job not found")
        
        if import_job.status == "completed":
            raise HTTPException(status_code=400, detail="Import already completed")
        
        import_job.column_mapping = data.column_mapping
        import_job.status = "completed"
        import_job.updated_at = datetime.utcnow()
        
        await db.commit()
        
        import_result = ImportResult(
            success=True,
            import_job_id=import_job.id,
            total_rows=import_job.total_rows,
            imported_rows=import_job.imported_rows,
            error_rows=import_job.error_rows,
            errors=import_job.errors or [],
            created_headcount_ids=[]
        )
        
        logger.info(f"Import job {job_id} confirmed and completed")
        return import_result
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error confirming import: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/import/template")
async def download_import_template():
    """Download Excel template for headcount import."""
    try:
        headers = [
            "title", "level", "department", "target_month", "target_year",
            "headcount", "salary_min", "salary_max", "salary_currency",
            "contract_type", "priority", "hiring_manager_name", 
            "hiring_manager_email", "justification", "job_description"
        ]
        
        csv_content = ",".join(headers) + "\n"
        csv_content += "Software Engineer,Senior,Engineering,3,2025,2,8000,12000,BRL,CLT,high,John Doe,john@example.com,Team expansion,Develop backend systems\n"
        csv_content += "Product Manager,Pleno,Product,6,2025,1,10000,15000,BRL,CLT,medium,Jane Smith,jane@example.com,New product launch,Lead product development\n"
        
        buffer = io.BytesIO(csv_content.encode('utf-8'))
        buffer.seek(0)
        
        return StreamingResponse(
            buffer,
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=workforce_import_template.csv"
            }
        )
    except Exception as e:
        logger.error(f"Error generating import template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=WorkforcePlanningStats)
async def get_workforce_stats(
    company_id: uuid.UUID | None = Query(None),
    fiscal_year: int | None = Query(None),
    plan_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get workforce planning statistics."""
    try:
        query = select(HiringPlan).where(HiringPlan.is_active == True)
        
        if company_id:
            query = query.where(HiringPlan.company_id == company_id)
        
        if fiscal_year:
            query = query.where(HiringPlan.fiscal_year == fiscal_year)
        
        if plan_id:
            query = query.where(HiringPlan.id == plan_id)
        
        result = await db.execute(query.limit(1))
        plan = result.scalar_one_or_none()
        
        if not plan:
            current_year = datetime.now().year
            return WorkforcePlanningStats(
                hiring_plan_id=uuid.uuid4(),
                fiscal_year=fiscal_year or current_year,
                total_planned_headcount=0,
                total_filled=0,
                total_in_progress=0,
                total_pending=0,
                total_cancelled=0,
                fill_rate=0.0,
                monthly_breakdown=[],
                by_department={},
                by_level={},
                by_contract_type={},
                by_priority={}
            )
        
        headcount_result = await db.execute(
            select(PlannedHeadcount).where(
                PlannedHeadcount.hiring_plan_id == plan.id,
                PlannedHeadcount.is_active == True
            )
        )
        headcounts = headcount_result.scalars().all()
        
        total_planned = sum(h.headcount or 1 for h in headcounts)
        total_filled = sum(h.headcount or 1 for h in headcounts if h.status == 'filled')
        total_in_progress = sum(h.headcount or 1 for h in headcounts if h.status == 'in_progress')
        total_pending = sum(h.headcount or 1 for h in headcounts if h.status in ['planned', 'pending'])
        total_cancelled = sum(h.headcount or 1 for h in headcounts if h.status == 'cancelled')
        
        fill_rate = (total_filled / total_planned * 100) if total_planned > 0 else 0.0
        
        by_status = {}
        by_priority = {}
        by_level = {}
        by_contract_type = {}
        by_department = {}
        
        for h in headcounts:
            status = h.status or 'planned'
            by_status[status] = by_status.get(status, 0) + (h.headcount or 1)
            
            priority = h.priority or 'medium'
            by_priority[priority] = by_priority.get(priority, 0) + (h.headcount or 1)
            
            level = h.level or 'not_specified'
            by_level[level] = by_level.get(level, 0) + (h.headcount or 1)
            
            contract = h.contract_type or 'not_specified'
            by_contract_type[contract] = by_contract_type.get(contract, 0) + (h.headcount or 1)
            
            dept_id = str(h.department_id) if h.department_id else 'no_department'
            by_department[dept_id] = by_department.get(dept_id, 0) + (h.headcount or 1)
        
        monthly_data = {}
        for h in headcounts:
            key = (h.target_month, h.target_year)
            if key not in monthly_data:
                monthly_data[key] = {
                    'total': 0,
                    'by_status': {},
                    'by_priority': {},
                    'by_department': {}
                }
            monthly_data[key]['total'] += h.headcount or 1
            
            status = h.status or 'planned'
            monthly_data[key]['by_status'][status] = monthly_data[key]['by_status'].get(status, 0) + (h.headcount or 1)
            
            priority = h.priority or 'medium'
            monthly_data[key]['by_priority'][priority] = monthly_data[key]['by_priority'].get(priority, 0) + (h.headcount or 1)
        
        monthly_breakdown = [
            MonthlyHeadcountStats(
                month=month,
                year=year,
                total_headcount=data['total'],
                by_status=data['by_status'],
                by_priority=data['by_priority'],
                by_department=data['by_department']
            )
            for (month, year), data in sorted(monthly_data.items(), key=lambda x: (x[0][1], x[0][0]))
        ]
        
        positions_at_risk = 0
        today = date.today()
        for h in headcounts:
            if h.status in ['planned', 'pending']:
                target_date = date(h.target_year, h.target_month, 1)
                days_until = (target_date - today).days
                if 0 < days_until <= 30:
                    positions_at_risk += h.headcount or 1
        
        return WorkforcePlanningStats(
            hiring_plan_id=plan.id,
            fiscal_year=plan.fiscal_year,
            total_planned_headcount=total_planned,
            total_filled=total_filled,
            total_in_progress=total_in_progress,
            total_pending=total_pending,
            total_cancelled=total_cancelled,
            fill_rate=round(fill_rate, 2),
            total_budget=plan.total_budget,
            monthly_breakdown=monthly_breakdown,
            by_department=by_department,
            by_level=by_level,
            by_contract_type=by_contract_type,
            by_priority=by_priority,
            positions_at_risk=positions_at_risk
        )
    except Exception as e:
        logger.error(f"Error getting workforce stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeline")
async def get_hiring_timeline(
    company_id: uuid.UUID | None = Query(None),
    months_ahead: int = Query(6, ge=1, le=24),
    db: AsyncSession = Depends(get_db)
):
    """Get timeline of upcoming hires."""
    try:
        today = date.today()
        current_month = today.month
        current_year = today.year
        
        query = select(PlannedHeadcount).where(
            PlannedHeadcount.is_active == True,
            PlannedHeadcount.status.in_(['planned', 'pending', 'in_progress'])
        )
        
        if company_id:
            query = query.join(HiringPlan).where(HiringPlan.company_id == company_id)
        
        result = await db.execute(query)
        headcounts = result.scalars().all()
        
        timeline = []
        for month_offset in range(months_ahead):
            target_month = (current_month + month_offset - 1) % 12 + 1
            target_year = current_year + (current_month + month_offset - 1) // 12
            
            month_headcounts = [
                h for h in headcounts 
                if h.target_month == target_month and h.target_year == target_year
            ]
            
            timeline.append({
                "month": target_month,
                "year": target_year,
                "month_name": date(target_year, target_month, 1).strftime("%B %Y"),
                "total_positions": sum(h.headcount or 1 for h in month_headcounts),
                "positions": [
                    {
                        "id": str(h.id),
                        "title": h.title,
                        "level": h.level,
                        "headcount": h.headcount or 1,
                        "priority": h.priority,
                        "status": h.status,
                        "hiring_manager": h.hiring_manager_name
                    }
                    for h in month_headcounts
                ]
            })
        
        return {
            "timeline": timeline,
            "total_upcoming": sum(t["total_positions"] for t in timeline),
            "months_covered": months_ahead
        }
    except Exception as e:
        logger.error(f"Error getting hiring timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_workforce_alerts(
    company_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get alerts for upcoming or overdue hires."""
    try:
        today = date.today()
        
        query = select(PlannedHeadcount).where(
            PlannedHeadcount.is_active == True,
            PlannedHeadcount.status.in_(['planned', 'pending', 'in_progress'])
        )
        
        if company_id:
            query = query.join(HiringPlan).where(HiringPlan.company_id == company_id)
        
        result = await db.execute(query)
        headcounts = result.scalars().all()
        
        alerts = []
        
        for h in headcounts:
            target_date = date(h.target_year, h.target_month, 1)
            days_until = (target_date - today).days
            
            if days_until < 0:
                alerts.append({
                    "type": "overdue",
                    "severity": "critical",
                    "headcount_id": str(h.id),
                    "title": h.title,
                    "message": f"Position '{h.title}' is {abs(days_until)} days overdue",
                    "target_date": target_date.isoformat(),
                    "days_overdue": abs(days_until),
                    "priority": h.priority,
                    "status": h.status
                })
            elif days_until <= 7:
                alerts.append({
                    "type": "urgent",
                    "severity": "high",
                    "headcount_id": str(h.id),
                    "title": h.title,
                    "message": f"Position '{h.title}' needs to be filled within {days_until} days",
                    "target_date": target_date.isoformat(),
                    "days_remaining": days_until,
                    "priority": h.priority,
                    "status": h.status
                })
            elif days_until <= 30:
                alerts.append({
                    "type": "upcoming",
                    "severity": "medium",
                    "headcount_id": str(h.id),
                    "title": h.title,
                    "message": f"Position '{h.title}' target date is in {days_until} days",
                    "target_date": target_date.isoformat(),
                    "days_remaining": days_until,
                    "priority": h.priority,
                    "status": h.status
                })
        
        alerts.sort(key=lambda x: (
            0 if x['severity'] == 'critical' else (1 if x['severity'] == 'high' else 2),
            x.get('days_overdue', 0) if x['type'] == 'overdue' else -x.get('days_remaining', 0)
        ))
        
        summary = {
            "total_alerts": len(alerts),
            "critical": len([a for a in alerts if a['severity'] == 'critical']),
            "high": len([a for a in alerts if a['severity'] == 'high']),
            "medium": len([a for a in alerts if a['severity'] == 'medium'])
        }
        
        return {
            "alerts": alerts,
            "summary": summary,
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting workforce alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


from pydantic import BaseModel


class WorkforceEntryItem(BaseModel):
    """Individual workforce entry for simple planning."""
    month: str
    department: str
    planned: int = 0
    actual: int = 0


class WorkforceEntriesRequest(BaseModel):
    """Request for saving workforce entries."""
    year: int
    entries: list[WorkforceEntryItem]


DEFAULT_WORKFORCE = [
    {"month": "Jan", "department": "Tecnologia", "planned": 5, "actual": 4, "ai_suggestion": 6},
    {"month": "Fev", "department": "Tecnologia", "planned": 4, "actual": 5},
    {"month": "Mar", "department": "Tecnologia", "planned": 6, "actual": 0, "ai_suggestion": 5},
    {"month": "Jan", "department": "Comercial", "planned": 3, "actual": 3},
    {"month": "Fev", "department": "Comercial", "planned": 2, "actual": 2},
    {"month": "Mar", "department": "Comercial", "planned": 4, "actual": 0, "ai_suggestion": 3},
    {"month": "Jan", "department": "RH", "planned": 1, "actual": 1},
    {"month": "Fev", "department": "RH", "planned": 1, "actual": 0},
    {"month": "Mar", "department": "RH", "planned": 2, "actual": 0, "ai_suggestion": 1}
]


@router.get("/entries")
async def get_workforce_entries(
    year: int | None = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get simple workforce entries for admin panel."""
    try:
        current_year = year or datetime.now().year
        
        result = await db.execute(
            select(WorkforceEntry).where(
                WorkforceEntry.is_active == True,
                WorkforceEntry.year == current_year
            ).order_by(WorkforceEntry.month, WorkforceEntry.department)
        )
        entries = result.scalars().all()
        
        if entries:
            return [e.to_dict() for e in entries]
        
        return DEFAULT_WORKFORCE
    except Exception as e:
        logger.error(f"Error fetching workforce entries: {e}")
        return DEFAULT_WORKFORCE


@router.put("/entries")
async def save_workforce_entries(
    data: WorkforceEntriesRequest,
    db: AsyncSession = Depends(get_db)
):
    """Save simple workforce entries for admin panel."""
    try:
        # 1 query: load all existing entries for the year — process upsert in memory
        existing_result = await db.execute(
            select(WorkforceEntry).where(WorkforceEntry.year == data.year)
        )
        existing_map = {
            (e.month, e.department): e
            for e in existing_result.scalars().all()
        }

        now = datetime.utcnow()
        for entry_data in data.entries:
            key = (entry_data.month, entry_data.department)
            existing = existing_map.get(key)

            if existing:
                existing.planned = entry_data.planned
                existing.actual = entry_data.actual
                existing.updated_at = now
            else:
                new_entry = WorkforceEntry(
                    year=data.year,
                    month=entry_data.month,
                    department=entry_data.department,
                    planned=entry_data.planned,
                    actual=entry_data.actual,
                    is_active=True
                )
                db.add(new_entry)
        
        await db.commit()
        
        result = await db.execute(
            select(WorkforceEntry).where(
                WorkforceEntry.is_active == True,
                WorkforceEntry.year == data.year
            ).order_by(WorkforceEntry.month, WorkforceEntry.department)
        )
        entries = result.scalars().all()
        
        logger.info(f"Workforce entries saved for year {data.year}")
        
        return [e.to_dict() for e in entries]
    except Exception as e:
        await db.rollback()
        logger.error(f"Error saving workforce entries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class WorkforceEntryImportResponse(BaseModel):
    """Response model for workforce entries import."""
    success: bool
    imported_count: int
    error_count: int
    errors: list[dict[str, Any]]
    items: list[dict[str, Any]]


def parse_csv_file_workforce(content: bytes) -> list[dict[str, str]]:
    """Parse CSV file content and return list of dictionaries."""
    text = content.decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


def parse_excel_file_workforce(content: bytes) -> list[dict[str, str]]:
    """Parse Excel file content and return list of dictionaries."""
    try:
        from openpyxl import load_workbook
        wb = load_workbook(filename=io.BytesIO(content), read_only=True, data_only=True)
        ws = wb.active
        
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []
        
        headers = [str(h).strip().lower() if h else f"col_{i}" for i, h in enumerate(rows[0])]
        
        result = []
        for row in rows[1:]:
            if all(cell is None or str(cell).strip() == '' for cell in row):
                continue
            row_dict = {}
            for i, cell in enumerate(row):
                if i < len(headers):
                    row_dict[headers[i]] = str(cell) if cell is not None else ''
            result.append(row_dict)
        
        return result
    except ImportError:
        raise HTTPException(
            status_code=400, 
            detail="Excel file support requires openpyxl. Please upload a CSV file instead."
        )


async def parse_workforce_import_file(file: UploadFile) -> list[dict[str, str]]:
    """Parse uploaded file (CSV or Excel) and return data."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    content = await file.read()
    file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    
    if file_ext == 'csv':
        return parse_csv_file_workforce(content)
    elif file_ext in ['xlsx', 'xls']:
        return parse_excel_file_workforce(content)
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: .{file_ext}. Allowed: .csv, .xlsx, .xls"
        )


@router.get("/entries/import/template")
async def download_workforce_entries_import_template():
    """Download CSV template for workforce entries import."""
    try:
        headers = ["department", "month", "year", "planned", "actual", "notes"]
        
        csv_content = ",".join(headers) + "\n"
        csv_content += "Tecnologia,Jan,2025,5,4,Team expansion\n"
        csv_content += "Tecnologia,Fev,2025,4,3,Q1 hires\n"
        csv_content += "Comercial,Jan,2025,3,3,Sales growth\n"
        csv_content += "Comercial,Fev,2025,2,2,New market\n"
        csv_content += "RH,Jan,2025,1,1,Support team\n"
        
        buffer = io.BytesIO(csv_content.encode('utf-8'))
        buffer.seek(0)
        
        return StreamingResponse(
            buffer,
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=workforce_entries_import_template.csv"
            }
        )
    except Exception as e:
        logger.error(f"Error generating workforce entries import template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/entries/import", response_model=WorkforceEntryImportResponse)
async def import_workforce_entries(
    file: UploadFile = File(...),
    company_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Simple import for workforce entries from Excel/CSV.
    Expected columns: department, month, year, planned, actual, notes
    """
    try:
        logger.info(f"Starting workforce entries import from file: {file.filename}")
        
        rows = await parse_workforce_import_file(file)
        
        if not rows:
            return WorkforceEntryImportResponse(
                success=False,
                imported_count=0,
                error_count=0,
                errors=[{"message": "No data found in file"}],
                items=[]
            )
        
        imported_items = []
        errors = []
        
        current_year = datetime.now().year
        
        for idx, row in enumerate(rows, start=2):
            row_errors = []
            
            department = row.get('department', '').strip()
            month_str = row.get('month', '').strip()
            year_str = row.get('year', '').strip()
            planned_str = row.get('planned', '').strip()
            
            if not department:
                row_errors.append(f"Row {idx}: Missing required field 'department'")
            if not month_str:
                row_errors.append(f"Row {idx}: Missing required field 'month'")
            
            planned = 0
            if planned_str:
                try:
                    planned = int(float(planned_str))
                except ValueError:
                    row_errors.append(f"Row {idx}: 'planned' must be a number")
            
            actual = 0
            actual_str = row.get('actual', '').strip()
            if actual_str:
                try:
                    actual = int(float(actual_str))
                except ValueError:
                    row_errors.append(f"Row {idx}: 'actual' must be a number")
            
            year = current_year
            if year_str:
                try:
                    year = int(float(year_str))
                except ValueError:
                    row_errors.append(f"Row {idx}: 'year' must be a number")
            
            notes = row.get('notes', '').strip() or None
            
            if row_errors:
                errors.append({
                    "row": idx,
                    "data": row,
                    "errors": row_errors
                })
                continue
            
            month_capitalized = month_str.capitalize() if month_str else month_str
            
            result = await db.execute(
                select(WorkforceEntry).where(
                    WorkforceEntry.year == year,
                    WorkforceEntry.month == month_capitalized,
                    WorkforceEntry.department == department
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                existing.planned = planned
                existing.actual = actual
                existing.notes = notes
                existing.updated_at = datetime.utcnow()
                
                imported_items.append({
                    "id": str(existing.id),
                    "department": existing.department,
                    "month": existing.month,
                    "year": existing.year,
                    "planned": existing.planned,
                    "actual": existing.actual,
                    "notes": notes,
                    "row": idx,
                    "action": "updated"
                })
            else:
                entry = WorkforceEntry(
                    company_id=company_id,
                    department=department,
                    month=month_capitalized,
                    year=year,
                    planned=planned,
                    actual=actual,
                    notes=notes,
                    is_active=True
                )
                db.add(entry)
                
                try:
                    await db.flush()
                    
                    imported_items.append({
                        "id": str(entry.id),
                        "department": entry.department,
                        "month": entry.month,
                        "year": entry.year,
                        "planned": entry.planned,
                        "actual": entry.actual,
                        "notes": notes,
                        "row": idx,
                        "action": "created"
                    })
                except Exception as flush_error:
                    errors.append({
                        "row": idx,
                        "data": row,
                        "errors": [f"Row {idx}: Database error - {str(flush_error)}"]
                    })
        
        if imported_items:
            await db.commit()
            logger.info(f"Imported {len(imported_items)} workforce entries successfully")
        
        return WorkforceEntryImportResponse(
            success=len(errors) == 0,
            imported_count=len(imported_items),
            error_count=len(errors),
            errors=errors,
            items=imported_items
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error importing workforce entries: {e}")
        raise HTTPException(status_code=500, detail=str(e))
