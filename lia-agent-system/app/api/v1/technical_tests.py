"""
Technical Tests API Endpoints.

Provides CRUD operations for technical tests management,
client-specific configurations, and test statistics.
"""
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.technical_tests import (
    DEFAULT_TESTS,
    TEST_CATEGORY_OPTIONS,
    TEST_DIFFICULTY_OPTIONS,
    ClientTestConfig,
    TechnicalTest,
    TestResult,
    TestSubcategory,
)
from app.schemas.technical_tests import (
    ClientTestConfigCreate,
    TechnicalTestCreate,
    TechnicalTestUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["technical-tests"])


def get_user_from_headers(
    x_company_id: str | None = Header(None, alias="X-Company-ID"),
    x_user_id: str | None = Header(None, alias="X-User-ID"),
    x_user_role: str | None = Header(None, alias="X-User-Role")
) -> dict[str, Any]:
    """Get user context from request headers."""
    if not x_company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Company ID required. Please provide X-Company-ID header."
        )
    
    return {
        "company_id": x_company_id,
        "user_id": x_user_id or "system",
        "role": x_user_role or "user",
        "is_admin": x_user_role == "admin"
    }


@router.get("/technical-tests/options", summary="Get test options", response_model=None)
async def get_test_options():
    """Get available test categories, subcategories, and difficulties."""
    subcategory_options = [
        {"value": s.value, "label": s.value.replace("_", " ").title()}
        for s in TestSubcategory
    ]
    
    return {
        "success": True,
        "data": {
            "categories": TEST_CATEGORY_OPTIONS,
            "subcategories": subcategory_options,
            "difficulties": TEST_DIFFICULTY_OPTIONS
        }
    }


@router.get("/technical-tests", summary="List all available tests", response_model=None)
async def list_technical_tests(
    category: str | None = Query(None, description="Filter by category"),
    subcategory: str | None = Query(None, description="Filter by subcategory"),
    difficulty: str | None = Query(None, description="Filter by difficulty"),
    is_global: bool | None = Query(None, description="Filter by global status"),
    is_active: bool | None = Query(True, description="Filter by active status"),
    search: str | None = Query(None, description="Search by name or description"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """List all available tests from the global library."""
    try:
        conditions = []
        
        if is_active is not None:
            conditions.append(TechnicalTest.is_active == is_active)
        
        if category:
            conditions.append(TechnicalTest.category == category)
        
        if subcategory:
            conditions.append(TechnicalTest.subcategory == subcategory)
        
        if difficulty:
            conditions.append(TechnicalTest.difficulty == difficulty)
        
        if is_global is not None:
            conditions.append(TechnicalTest.is_global == is_global)
        
        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    TechnicalTest.name.ilike(search_term),
                    TechnicalTest.description.ilike(search_term)
                )
            )
        
        query = select(TechnicalTest)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(TechnicalTest.category, TechnicalTest.name)
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        tests = result.scalars().all()
        
        count_query = select(func.count(TechnicalTest.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        logger.info(f"📋 Listed {len(tests)} technical tests (total: {total})")
        
        return {
            "success": True,
            "data": {
                "tests": [t.to_dict() for t in tests],
                "total": total,
                "limit": limit,
                "offset": offset
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error listing technical tests: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list technical tests: {str(e)}"
        )


@router.get("/technical-tests/{test_id}", summary="Get test details", response_model=None)
async def get_technical_test(
    test_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """Get details of a specific test."""
    try:
        try:
            test_uuid = UUID(test_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid test ID format"
            )
        
        query = select(TechnicalTest).where(TechnicalTest.id == test_uuid)
        result = await db.execute(query)
        test = result.scalar_one_or_none()
        
        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test not found: {test_id}"
            )
        
        return {
            "success": True,
            "data": test.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting technical test: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get technical test: {str(e)}"
        )


@router.post("/technical-tests", status_code=status.HTTP_201_CREATED, summary="Create new test", response_model=None)
async def create_technical_test(
    data: TechnicalTestCreate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """Create a new technical test (admin only)."""
    try:
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can create technical tests"
            )
        
        test = TechnicalTest(
            name=data.name,
            category=data.category.value,
            subcategory=data.subcategory.value if data.subcategory else None,
            description=data.description,
            duration_minutes=data.duration_minutes,
            difficulty=data.difficulty.value,
            passing_score=data.passing_score,
            max_attempts=data.max_attempts,
            instructions=data.instructions,
            questions_config=data.questions_config or {},
            is_global=data.is_global,
            is_active=True,
            created_by=current_user.get("user_id"),
        )
        
        db.add(test)
        await db.commit()
        await db.refresh(test)
        
        logger.info(f"✅ Created technical test: {test.name} (ID: {test.id})")
        
        return {
            "success": True,
            "message": "Technical test created successfully",
            "data": test.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error creating technical test: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create technical test: {str(e)}"
        )


@router.put("/technical-tests/{test_id}", summary="Update test", response_model=None)
async def update_technical_test(
    test_id: str,
    data: TechnicalTestUpdate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing technical test."""
    try:
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can update technical tests"
            )
        
        try:
            test_uuid = UUID(test_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid test ID format"
            )
        
        query = select(TechnicalTest).where(TechnicalTest.id == test_uuid)
        result = await db.execute(query)
        test = result.scalar_one_or_none()
        
        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test not found: {test_id}"
            )
        
        update_data = data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(value, 'value'):
                value = value.value
            setattr(test, field, value)
        
        test.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(test)
        
        logger.info(f"✅ Updated technical test: {test.name} (ID: {test.id})")
        
        return {
            "success": True,
            "message": "Technical test updated successfully",
            "data": test.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error updating technical test: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update technical test: {str(e)}"
        )


@router.delete("/technical-tests/{test_id}", summary="Delete test", response_model=None)
async def delete_technical_test(
    test_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """Delete a technical test (soft delete by deactivating)."""
    try:
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can delete technical tests"
            )
        
        try:
            test_uuid = UUID(test_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid test ID format"
            )
        
        query = select(TechnicalTest).where(TechnicalTest.id == test_uuid)
        result = await db.execute(query)
        test = result.scalar_one_or_none()
        
        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test not found: {test_id}"
            )
        
        test.is_active = False
        test.updated_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"✅ Deactivated technical test: {test.name} (ID: {test.id})")
        
        return {
            "success": True,
            "message": f"Technical test '{test.name}' has been deactivated"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error deleting technical test: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete technical test: {str(e)}"
        )


@router.get("/clients/{client_id}/tests", summary="Get tests configured for a client", response_model=None)
async def get_client_tests(
    client_id: str,
    is_enabled: bool | None = Query(None, description="Filter by enabled status"),
    category: str | None = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """Get tests configured for a specific client."""
    try:
        try:
            client_uuid = UUID(client_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid client ID format"
            )
        
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        user_company_id = current_user.get("company_id")
        
        if not is_admin and str(client_uuid) != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this client's tests"
            )
        
        conditions = [ClientTestConfig.client_id == client_uuid]
        
        if is_enabled is not None:
            conditions.append(ClientTestConfig.is_enabled == is_enabled)
        
        query = select(ClientTestConfig, TechnicalTest).join(
            TechnicalTest, ClientTestConfig.test_id == TechnicalTest.id
        ).where(and_(*conditions))
        
        if category:
            query = query.where(TechnicalTest.category == category)
        
        query = query.order_by(ClientTestConfig.priority.desc(), TechnicalTest.name)
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        rows = result.all()
        
        configs = []
        for config, test in rows:
            config_dict = config.to_dict()
            config_dict["test"] = test.to_dict()
            configs.append(config_dict)
        
        count_query = select(func.count(ClientTestConfig.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        return {
            "success": True,
            "data": {
                "configs": configs,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting client tests: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client tests: {str(e)}"
        )


@router.put("/clients/{client_id}/tests/{test_id}", summary="Configure test for client", response_model=None)
async def configure_client_test(
    client_id: str,
    test_id: str,
    data: ClientTestConfigCreate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """Configure a test for a specific client (enable/disable, custom settings)."""
    try:
        try:
            client_uuid = UUID(client_id)
            test_uuid = UUID(test_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid client or test ID format"
            )
        
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        user_company_id = current_user.get("company_id")
        
        if not is_admin and str(client_uuid) != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to configure this client's tests"
            )
        
        test_query = select(TechnicalTest).where(TechnicalTest.id == test_uuid)
        test_result = await db.execute(test_query)
        test = test_result.scalar_one_or_none()
        
        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test not found: {test_id}"
            )
        
        config_query = select(ClientTestConfig).where(
            and_(
                ClientTestConfig.client_id == client_uuid,
                ClientTestConfig.test_id == test_uuid
            )
        )
        config_result = await db.execute(config_query)
        config = config_result.scalar_one_or_none()
        
        if config:
            config.is_enabled = data.is_enabled
            config.custom_time_limit = data.custom_time_limit
            config.custom_passing_score = data.custom_passing_score
            config.custom_instructions = data.custom_instructions
            config.custom_max_attempts = data.custom_max_attempts
            config.priority = data.priority
            config.required_for_roles = data.required_for_roles or []
            config.updated_at = datetime.utcnow()
            message = "Test configuration updated successfully"
        else:
            config = ClientTestConfig(
                client_id=client_uuid,
                test_id=test_uuid,
                is_enabled=data.is_enabled,
                custom_time_limit=data.custom_time_limit,
                custom_passing_score=data.custom_passing_score,
                custom_instructions=data.custom_instructions,
                custom_max_attempts=data.custom_max_attempts,
                priority=data.priority,
                required_for_roles=data.required_for_roles or [],
            )
            db.add(config)
            message = "Test configuration created successfully"
        
        await db.commit()
        await db.refresh(config)
        
        config_dict = config.to_dict()
        config_dict["test"] = test.to_dict()
        
        logger.info(f"✅ Configured test {test.name} for client {client_id}")
        
        return {
            "success": True,
            "message": message,
            "data": config_dict
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error configuring client test: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to configure client test: {str(e)}"
        )


@router.delete("/clients/{client_id}/tests/{test_id}", summary="Remove test from client", response_model=None)
async def remove_client_test(
    client_id: str,
    test_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """Remove a test configuration from a client."""
    try:
        try:
            client_uuid = UUID(client_id)
            test_uuid = UUID(test_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid client or test ID format"
            )
        
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        user_company_id = current_user.get("company_id")
        
        if not is_admin and str(client_uuid) != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to remove this client's tests"
            )
        
        config_query = select(ClientTestConfig).where(
            and_(
                ClientTestConfig.client_id == client_uuid,
                ClientTestConfig.test_id == test_uuid
            )
        )
        config_result = await db.execute(config_query)
        config = config_result.scalar_one_or_none()
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test configuration not found"
            )
        
        await db.delete(config)
        await db.commit()
        
        logger.info(f"✅ Removed test {test_id} from client {client_id}")
        
        return {
            "success": True,
            "message": "Test configuration removed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error removing client test: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove client test: {str(e)}"
        )


@router.get("/clients/{client_id}/tests/stats", summary="Get test statistics for client", response_model=None)
async def get_client_test_stats(
    client_id: str,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """Get test statistics for a specific client."""
    try:
        try:
            client_uuid = UUID(client_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid client ID format"
            )
        
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        user_company_id = current_user.get("company_id")
        
        if not is_admin and str(client_uuid) != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this client's stats"
            )
        
        enabled_count_query = select(func.count(ClientTestConfig.id)).where(
            and_(
                ClientTestConfig.client_id == client_uuid,
                ClientTestConfig.is_enabled
            )
        )
        enabled_result = await db.execute(enabled_count_query)
        total_tests_enabled = enabled_result.scalar() or 0
        
        results_query = select(
            TestResult.test_id,
            func.count(TestResult.id).label('total_taken'),
            func.count(case((TestResult.completed_at.isnot(None), 1))).label('total_completed'),
            func.avg(TestResult.score).label('avg_score'),
            func.avg(TestResult.time_taken_seconds).label('avg_time'),
            func.sum(case((TestResult.passed, 1), else_=0)).label('passed_count')
        ).where(
            TestResult.client_id == client_uuid
        ).group_by(TestResult.test_id)
        
        results_result = await db.execute(results_query)
        test_stats_rows = results_result.all()
        
        total_results = 0
        total_passed = 0
        total_score_sum = 0
        stats_by_test = []
        
        for row in test_stats_rows:
            test_query = select(TechnicalTest).where(TechnicalTest.id == row.test_id)
            test_result = await db.execute(test_query)
            test = test_result.scalar_one_or_none()
            
            total_taken = row.total_taken or 0
            total_completed = row.total_completed or 0
            avg_score = float(row.avg_score or 0)
            passed_count = row.passed_count or 0
            
            completion_rate = (total_completed / total_taken * 100) if total_taken > 0 else 0
            pass_rate = (passed_count / total_completed * 100) if total_completed > 0 else 0
            
            total_results += total_taken
            total_passed += passed_count
            total_score_sum += avg_score * total_completed
            
            stats_by_test.append({
                "test_id": str(row.test_id),
                "test_name": test.name if test else "Unknown",
                "total_taken": total_taken,
                "total_completed": total_completed,
                "avg_score": round(avg_score, 2),
                "completion_rate": round(completion_rate, 2),
                "pass_rate": round(pass_rate, 2),
                "avg_time_seconds": float(row.avg_time) if row.avg_time else None
            })
        
        overall_pass_rate = (total_passed / total_results * 100) if total_results > 0 else 0
        completed_count = sum(s["total_completed"] for s in stats_by_test)
        overall_avg_score = (total_score_sum / completed_count) if completed_count > 0 else 0
        
        category_query = select(
            TechnicalTest.category,
            func.count(TestResult.id).label('count'),
            func.avg(TestResult.score).label('avg_score')
        ).join(
            TestResult, TechnicalTest.id == TestResult.test_id
        ).where(
            TestResult.client_id == client_uuid
        ).group_by(TechnicalTest.category)
        
        category_result = await db.execute(category_query)
        category_rows = category_result.all()
        
        stats_by_category = {
            row.category: {
                "count": row.count,
                "avg_score": round(float(row.avg_score or 0), 2)
            }
            for row in category_rows
        }
        
        return {
            "success": True,
            "data": {
                "client_id": str(client_uuid),
                "total_tests_enabled": total_tests_enabled,
                "total_results": total_results,
                "overall_pass_rate": round(overall_pass_rate, 2),
                "overall_avg_score": round(overall_avg_score, 2),
                "stats_by_test": stats_by_test,
                "stats_by_category": stats_by_category
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting client test stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client test stats: {str(e)}"
        )


@router.post("/technical-tests/seed", summary="Seed default tests", response_model=None)
async def seed_default_tests(
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """Seed the database with default tests (admin only)."""
    try:
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can seed tests"
            )
        
        created_count = 0
        skipped_count = 0
        
        for test_data in DEFAULT_TESTS:
            existing_query = select(TechnicalTest).where(
                TechnicalTest.name == test_data["name"]
            )
            existing_result = await db.execute(existing_query)
            existing = existing_result.scalar_one_or_none()
            
            if existing:
                skipped_count += 1
                continue
            
            test = TechnicalTest(
                name=test_data["name"],
                category=test_data["category"],
                subcategory=test_data["subcategory"],
                description=test_data["description"],
                duration_minutes=test_data["duration_minutes"],
                difficulty=test_data["difficulty"],
                passing_score=test_data["passing_score"],
                max_attempts=test_data["max_attempts"],
                instructions=test_data["instructions"],
                is_global=test_data["is_global"],
                is_active=True,
                created_by=current_user.get("user_id"),
            )
            db.add(test)
            created_count += 1
        
        await db.commit()
        
        logger.info(f"✅ Seeded {created_count} default tests (skipped {skipped_count} existing)")
        
        return {
            "success": True,
            "message": f"Seeded {created_count} tests ({skipped_count} already existed)",
            "data": {
                "created": created_count,
                "skipped": skipped_count
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error seeding default tests: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to seed default tests: {str(e)}"
        )
