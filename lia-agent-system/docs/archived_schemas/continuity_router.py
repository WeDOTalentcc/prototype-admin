"""
Business Continuity API Endpoints.

Provides endpoints for:
- Critical processes (BIA - Business Impact Analysis)
- DR Plans (Disaster Recovery)
- Continuity tests
- Dashboard and statistics
"""
from fastapi import APIRouter, HTTPException, Query, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from typing import Optional, List
from datetime import datetime, date
import logging
from uuid import UUID

from app.core.database import get_db
from app.models.observability import BusinessProcess, DisasterRecoveryPlan, ContinuityTest
from app.shared.tenant_guard import get_verified_company_id
from app.schemas.continuity import (
    CriticalProcessResponse, CriticalProcessListResponse, CriticalProcessCreate, CriticalProcessUpdate,
    DRPlanResponse, DRPlanListResponse, DRPlanCreate, DRPlanUpdate, DRPlanApproval,
    ContinuityTestResponse, ContinuityTestListResponse, ContinuityTestCreate, ContinuityTestUpdate,
    ContinuityDashboard, ContinuityStats
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/continuity", tags=["continuity"])


def process_to_response(process: BusinessProcess) -> dict:
    """Convert BusinessProcess model to response dict format."""
    return {
        "id": str(process.id),
        "company_id": str(process.company_id),
        "name": process.process_name,
        "description": process.backup_procedures,
        "criticality": process.criticality,
        "status": "active",
        "owner": process.responsible_team,
        "owner_email": None,
        "department": process.department,
        "rto_hours": process.rto_hours,
        "rpo_hours": process.rpo_hours,
        "mtpd_hours": process.mtpd_hours,
        "dependencies": [str(d) for d in process.dependencies] if process.dependencies else [],
        "recovery_procedures": process.backup_procedures,
        "last_bia_date": None,
        "next_review_date": process.next_test_due.isoformat() if process.next_test_due else None,
        "created_at": process.created_at.isoformat() if process.created_at else None,
        "updated_at": process.updated_at.isoformat() if process.updated_at else None
    }


def plan_to_response(plan: DisasterRecoveryPlan) -> dict:
    """Convert DisasterRecoveryPlan model to response dict format."""
    return {
        "id": str(plan.id),
        "company_id": str(plan.company_id),
        "name": plan.plan_name,
        "description": plan.scope,
        "plan_type": "disaster_recovery",
        "status": plan.status,
        "version": plan.version,
        "processes_covered": [],
        "recovery_strategies": plan.recovery_steps or [],
        "communication_plan": plan.contact_list or [],
        "escalation_matrix": [],
        "approved_by": str(plan.approved_by) if plan.approved_by else None,
        "approved_at": plan.approved_at.isoformat() if plan.approved_at else None,
        "last_tested_at": plan.last_tested_at.isoformat() if plan.last_tested_at else None,
        "next_test_date": None,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
        "updated_at": plan.updated_at.isoformat() if plan.updated_at else None
    }


def test_to_response(test: ContinuityTest, plan_name: str = None) -> dict:
    """Convert ContinuityTest model to response dict format."""
    return {
        "id": str(test.id),
        "company_id": str(test.company_id),
        "plan_id": str(test.plan_id) if test.plan_id else None,
        "plan_name": plan_name,
        "test_type": test.test_type,
        "name": test.test_name,
        "description": test.findings,
        "scheduled_date": test.scheduled_date.isoformat() if test.scheduled_date else None,
        "status": test.status,
        "result": "passed" if test.status == "completed" else None,
        "actual_rto_achieved": None,
        "actual_rpo_achieved": None,
        "participants": test.participants or [],
        "findings": test.findings,
        "recommendations": test.improvements_identified or [],
        "conducted_by": None,
        "completed_at": test.executed_date.isoformat() if test.executed_date else None,
        "created_at": test.created_at.isoformat() if test.created_at else None,
        "updated_at": test.created_at.isoformat() if test.created_at else None
    }


@router.get("/stats", response_model=ContinuityStats, summary="Get continuity statistics")
async def get_continuity_stats(
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get aggregated continuity statistics for the company."""
    try:
        company_uuid = UUID(company_id)
        
        processes_query = select(BusinessProcess).where(BusinessProcess.company_id == company_uuid)
        processes_result = await db.execute(processes_query)
        processes = processes_result.scalars().all()
        
        plans_query = select(DisasterRecoveryPlan).where(DisasterRecoveryPlan.company_id == company_uuid)
        plans_result = await db.execute(plans_query)
        plans = plans_result.scalars().all()
        
        tests_query = select(ContinuityTest).where(ContinuityTest.company_id == company_uuid)
        tests_result = await db.execute(tests_query)
        tests = tests_result.scalars().all()
        
        by_criticality = {}
        for process in processes:
            crit = process.criticality or "unknown"
            by_criticality[crit] = by_criticality.get(crit, 0) + 1
        
        by_plan_status = {}
        by_plan_type = {}
        for plan in plans:
            stat = plan.status or "unknown"
            by_plan_status[stat] = by_plan_status.get(stat, 0) + 1
            by_plan_type["disaster_recovery"] = by_plan_type.get("disaster_recovery", 0) + 1
        
        by_test_status = {}
        by_test_result = {}
        for test in tests:
            stat = test.status or "unknown"
            by_test_status[stat] = by_test_status.get(stat, 0) + 1
            if test.status == "completed":
                by_test_result["passed"] = by_test_result.get("passed", 0) + 1
        
        return ContinuityStats(
            total_processes=len(processes),
            by_criticality=by_criticality,
            total_plans=len(plans),
            by_plan_status=by_plan_status,
            by_plan_type=by_plan_type,
            total_tests=len(tests),
            by_test_status=by_test_status,
            by_test_result=by_test_result,
            average_rto_gap_percent=0.0,
            average_rpo_gap_percent=0.0
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error getting continuity stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard", response_model=ContinuityDashboard, summary="Get continuity dashboard")
async def get_continuity_dashboard(
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard data for business continuity."""
    try:
        company_uuid = UUID(company_id)
        
        processes_query = select(BusinessProcess).where(BusinessProcess.company_id == company_uuid)
        processes_result = await db.execute(processes_query)
        processes = processes_result.scalars().all()
        
        plans_query = select(DisasterRecoveryPlan).where(DisasterRecoveryPlan.company_id == company_uuid)
        plans_result = await db.execute(plans_query)
        plans = plans_result.scalars().all()
        
        tests_query = select(ContinuityTest).where(ContinuityTest.company_id == company_uuid)
        tests_result = await db.execute(tests_query)
        tests = tests_result.scalars().all()
        
        by_criticality = {}
        for process in processes:
            crit = process.criticality or "unknown"
            by_criticality[crit] = by_criticality.get(crit, 0) + 1
        
        approved_plans = len([p for p in plans if p.status in ["approved", "active"]])
        outdated_plans = len([p for p in plans if p.status == "retired"])
        
        pending_tests = [t for t in tests if t.status == "scheduled"]
        upcoming = []
        today = date.today()
        for test in pending_tests:
            if test.scheduled_date and test.scheduled_date >= today:
                upcoming.append({
                    "id": str(test.id),
                    "name": test.test_name,
                    "scheduled_date": test.scheduled_date.isoformat(),
                    "plan_id": str(test.plan_id) if test.plan_id else None
                })
        
        last_test_results = {}
        for test in tests:
            if test.status == "completed":
                last_test_results["passed"] = last_test_results.get("passed", 0) + 1
        
        return ContinuityDashboard(
            total_processes=len(processes),
            by_criticality=by_criticality,
            total_plans=len(plans),
            approved_plans=approved_plans,
            outdated_plans=outdated_plans,
            pending_tests=len(pending_tests),
            upcoming_tests=upcoming[:5],
            rto_gaps=[],
            rpo_gaps=[],
            last_test_results=last_test_results
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error getting continuity dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/processes", response_model=CriticalProcessListResponse, summary="List processes")
async def list_processes(
    criticality: Optional[str] = Query(None, description="Filter by criticality"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """List critical processes with optional filters."""
    try:
        company_uuid = UUID(company_id)
        conditions = [BusinessProcess.company_id == company_uuid]
        
        if criticality:
            conditions.append(BusinessProcess.criticality == criticality)
        
        query = select(BusinessProcess).where(and_(*conditions))
        query = query.order_by(desc(BusinessProcess.created_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        processes = result.scalars().all()
        
        count_query = select(func.count(BusinessProcess.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        return CriticalProcessListResponse(
            processes=[CriticalProcessResponse(**process_to_response(p)) for p in processes],
            total=total,
            limit=limit,
            offset=offset
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error listing processes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/processes", response_model=CriticalProcessResponse, status_code=status.HTTP_201_CREATED, summary="Create process")
async def create_process(
    data: CriticalProcessCreate,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a new critical process."""
    try:
        company_uuid = UUID(company_id)
        
        process = BusinessProcess(
            company_id=company_uuid,
            process_code=f"PROC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            process_name=data.name,
            department=data.department,
            criticality=data.criticality.value,
            rto_hours=data.rto_hours,
            rpo_hours=data.rpo_hours,
            mtpd_hours=data.mtpd_hours,
            dependencies=[],
            responsible_team=data.owner,
            backup_procedures=data.recovery_procedures
        )
        
        db.add(process)
        await db.commit()
        await db.refresh(process)
        
        logger.info(f"Created process {process.id} for company {company_id}")
        return CriticalProcessResponse(**process_to_response(process))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating process: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/processes/{process_id}", response_model=CriticalProcessResponse, summary="Update process")
async def update_process(
    process_id: str,
    data: CriticalProcessUpdate,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing critical process."""
    try:
        company_uuid = UUID(company_id)
        process_uuid = UUID(process_id)
        
        query = select(BusinessProcess).where(
            and_(
                BusinessProcess.id == process_uuid,
                BusinessProcess.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        process = result.scalar_one_or_none()
        
        if not process:
            raise HTTPException(status_code=404, detail="Process not found")
        
        if data.name is not None:
            process.process_name = data.name
        if data.department is not None:
            process.department = data.department
        if data.criticality is not None:
            process.criticality = data.criticality.value
        if data.owner is not None:
            process.responsible_team = data.owner
        if data.rto_hours is not None:
            process.rto_hours = data.rto_hours
        if data.rpo_hours is not None:
            process.rpo_hours = data.rpo_hours
        if data.mtpd_hours is not None:
            process.mtpd_hours = data.mtpd_hours
        if data.recovery_procedures is not None:
            process.backup_procedures = data.recovery_procedures
        if data.next_review_date is not None:
            process.next_test_due = data.next_review_date
        
        await db.commit()
        await db.refresh(process)
        
        logger.info(f"Updated process {process_id}")
        return CriticalProcessResponse(**process_to_response(process))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid process ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating process: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plans", response_model=DRPlanListResponse, summary="List plans")
async def list_plans(
    plan_type: Optional[str] = Query(None, description="Filter by plan type"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """List DR plans with optional filters."""
    try:
        company_uuid = UUID(company_id)
        conditions = [DisasterRecoveryPlan.company_id == company_uuid]
        
        if status_filter:
            conditions.append(DisasterRecoveryPlan.status == status_filter)
        
        query = select(DisasterRecoveryPlan).where(and_(*conditions))
        query = query.order_by(desc(DisasterRecoveryPlan.created_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        plans = result.scalars().all()
        
        count_query = select(func.count(DisasterRecoveryPlan.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        return DRPlanListResponse(
            plans=[DRPlanResponse(**plan_to_response(p)) for p in plans],
            total=total,
            limit=limit,
            offset=offset
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error listing plans: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plans", response_model=DRPlanResponse, status_code=status.HTTP_201_CREATED, summary="Create plan")
async def create_plan(
    data: DRPlanCreate,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a new DR plan."""
    try:
        company_uuid = UUID(company_id)
        
        plan = DisasterRecoveryPlan(
            company_id=company_uuid,
            plan_name=data.name,
            version="1.0",
            status="draft",
            scope=data.description,
            recovery_steps=data.recovery_strategies or [],
            contact_list=data.communication_plan or []
        )
        
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        
        logger.info(f"Created plan {plan.id} for company {company_id}")
        return DRPlanResponse(**plan_to_response(plan))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating plan: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/plans/{plan_id}", response_model=DRPlanResponse, summary="Update plan")
async def update_plan(
    plan_id: str,
    data: DRPlanUpdate,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing DR plan."""
    try:
        company_uuid = UUID(company_id)
        plan_uuid = UUID(plan_id)
        
        query = select(DisasterRecoveryPlan).where(
            and_(
                DisasterRecoveryPlan.id == plan_uuid,
                DisasterRecoveryPlan.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        plan = result.scalar_one_or_none()
        
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        if data.name is not None:
            plan.plan_name = data.name
        if data.description is not None:
            plan.scope = data.description
        if data.status is not None:
            plan.status = data.status.value
        if data.recovery_strategies is not None:
            plan.recovery_steps = data.recovery_strategies
        if data.communication_plan is not None:
            plan.contact_list = data.communication_plan
        
        await db.commit()
        await db.refresh(plan)
        
        logger.info(f"Updated plan {plan_id}")
        return DRPlanResponse(**plan_to_response(plan))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid plan ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating plan: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/plans/{plan_id}/approve", response_model=DRPlanResponse, summary="Approve plan")
async def approve_plan(
    plan_id: str,
    data: DRPlanApproval,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Approve a DR plan."""
    try:
        company_uuid = UUID(company_id)
        plan_uuid = UUID(plan_id)
        
        query = select(DisasterRecoveryPlan).where(
            and_(
                DisasterRecoveryPlan.id == plan_uuid,
                DisasterRecoveryPlan.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        plan = result.scalar_one_or_none()
        
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        plan.status = "approved"
        plan.approved_at = datetime.utcnow()
        if data.version:
            plan.version = data.version
        
        await db.commit()
        await db.refresh(plan)
        
        logger.info(f"Approved plan {plan_id}")
        return DRPlanResponse(**plan_to_response(plan))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid plan ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error approving plan: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tests", response_model=ContinuityTestListResponse, summary="List tests")
async def list_tests(
    test_type: Optional[str] = Query(None, description="Filter by test type"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """List continuity tests with optional filters."""
    try:
        company_uuid = UUID(company_id)
        conditions = [ContinuityTest.company_id == company_uuid]
        
        if test_type:
            conditions.append(ContinuityTest.test_type == test_type)
        if status_filter:
            conditions.append(ContinuityTest.status == status_filter)
        
        query = select(ContinuityTest).where(and_(*conditions))
        query = query.order_by(desc(ContinuityTest.scheduled_date)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        tests = result.scalars().all()
        
        count_query = select(func.count(ContinuityTest.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        plan_ids = set(t.plan_id for t in tests if t.plan_id)
        plan_names = {}
        if plan_ids:
            plans_query = select(DisasterRecoveryPlan).where(DisasterRecoveryPlan.id.in_(plan_ids))
            plans_result = await db.execute(plans_query)
            for plan in plans_result.scalars().all():
                plan_names[str(plan.id)] = plan.plan_name
        
        test_responses = []
        for test in tests:
            plan_name = plan_names.get(str(test.plan_id)) if test.plan_id else None
            test_responses.append(ContinuityTestResponse(**test_to_response(test, plan_name)))
        
        return ContinuityTestListResponse(
            tests=test_responses,
            total=total,
            limit=limit,
            offset=offset
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error listing tests: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tests", response_model=ContinuityTestResponse, status_code=status.HTTP_201_CREATED, summary="Schedule test")
async def create_test(
    data: ContinuityTestCreate,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Schedule a new continuity test."""
    try:
        company_uuid = UUID(company_id)
        plan_uuid = UUID(data.plan_id)
        
        plan_query = select(DisasterRecoveryPlan).where(
            and_(
                DisasterRecoveryPlan.id == plan_uuid,
                DisasterRecoveryPlan.company_id == company_uuid
            )
        )
        plan_result = await db.execute(plan_query)
        plan = plan_result.scalar_one_or_none()
        
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        test = ContinuityTest(
            company_id=company_uuid,
            plan_id=plan_uuid,
            test_type=data.test_type.value,
            test_name=data.name,
            scheduled_date=data.scheduled_date,
            status="scheduled",
            participants=data.participants or [],
            findings=data.description,
            improvements_identified=[]
        )
        
        db.add(test)
        await db.commit()
        await db.refresh(test)
        
        logger.info(f"Scheduled test {test.id} for company {company_id}")
        return ContinuityTestResponse(**test_to_response(test, plan.plan_name))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating test: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/tests/{test_id}", response_model=ContinuityTestResponse, summary="Update test")
async def update_test(
    test_id: str,
    data: ContinuityTestUpdate,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Update a continuity test (including results)."""
    try:
        company_uuid = UUID(company_id)
        test_uuid = UUID(test_id)
        
        query = select(ContinuityTest).where(
            and_(
                ContinuityTest.id == test_uuid,
                ContinuityTest.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        test = result.scalar_one_or_none()
        
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        
        if data.test_type is not None:
            test.test_type = data.test_type.value
        if data.name is not None:
            test.test_name = data.name
        if data.description is not None:
            test.findings = data.description
        if data.scheduled_date is not None:
            test.scheduled_date = data.scheduled_date
        if data.status is not None:
            test.status = data.status.value
            if data.status.value == "completed":
                test.executed_date = date.today()
        if data.participants is not None:
            test.participants = data.participants
        if data.findings is not None:
            test.findings = data.findings
        if data.recommendations is not None:
            test.improvements_identified = data.recommendations
        
        await db.commit()
        await db.refresh(test)
        
        plan_name = None
        if test.plan_id:
            plan_query = select(DisasterRecoveryPlan).where(DisasterRecoveryPlan.id == test.plan_id)
            plan_result = await db.execute(plan_query)
            plan = plan_result.scalar_one_or_none()
            if plan:
                plan_name = plan.plan_name
                plan.last_tested_at = datetime.utcnow()
                await db.commit()
        
        logger.info(f"Updated test {test_id}")
        return ContinuityTestResponse(**test_to_response(test, plan_name))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid test ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating test: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
