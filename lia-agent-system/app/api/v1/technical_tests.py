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

from app.domains.technical_tests.dependencies import get_technical_tests_repo
from app.domains.technical_tests.repositories.technical_tests_repository import (
    TechnicalTestsRepository,
)
from app.models.technical_tests import (
    DEFAULT_TESTS,
    TEST_CATEGORY_OPTIONS,
    TEST_DIFFICULTY_OPTIONS,
    ClientTestConfig,
    TechnicalTest,
    TestSubcategory,
)
from app.schemas.technical_tests import (
    ClientTestConfigCreate,
    TechnicalTestCreate,
    TechnicalTestUpdate,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.tenant_guard import get_verified_company_id
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(tags=["technical-tests"])


def get_user_from_headers(
    company_id: str = Depends(get_verified_company_id),
    x_user_id: str | None = Header(None, alias="X-User-ID"),
    x_user_role: str | None = Header(None, alias="X-User-Role")
) -> dict[str, Any]:
    """Get user context from request.

    Multi-tenancy canonical (R4): ``company_id`` comes from JWT via
    ``get_verified_company_id`` (which validates header matches JWT and
    rejects cross-tenant spoof attempts). NEVER trust X-Company-ID header
    blindly — that was the SMOKE-#2 LGPD anti-pattern.
    """
    return {
        "company_id": company_id,
        "user_id": x_user_id or "system",
        "role": x_user_role or "user",
        "is_admin": x_user_role == "admin"
    }


@router.get("/technical-tests/options", summary="Get test options", response_model=None)
async def get_test_options(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
    repo: TechnicalTestsRepository = Depends(get_technical_tests_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List all available tests from the global library."""
    try:
        tests = await repo.list_tests(
            category=category,
            subcategory=subcategory,
            difficulty=difficulty,
            is_global=is_global,
            is_active=is_active,
            search=search,
            limit=limit,
            offset=offset,
        )

        total = await repo.count_tests(
            category=category,
            subcategory=subcategory,
            difficulty=difficulty,
            is_global=is_global,
            is_active=is_active,
            search=search,
        )

        logger.info(f"Listed {len(tests)} technical tests (total: {total})")

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
        logger.error(f"Error listing technical tests: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list technical tests: {str(e)}"
        )


@router.get("/technical-tests/{test_id}", summary="Get test details", response_model=None)
async def get_technical_test(
    test_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: TechnicalTestsRepository = Depends(get_technical_tests_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get details of a specific test."""
    try:
        try:
            test_uuid = UUID(test_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid test ID format"
            )

        test = await repo.get_by_id(test_uuid)

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
        logger.error(f"Error getting technical test: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get technical test: {str(e)}"
        )


@router.post("/technical-tests", status_code=status.HTTP_201_CREATED, summary="Create new test", response_model=None)
async def create_technical_test(
    data: TechnicalTestCreate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: TechnicalTestsRepository = Depends(get_technical_tests_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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

        test = await repo.create_test(test)

        logger.info(f"Created technical test: {test.name} (ID: {test.id})")

        return {
            "success": True,
            "message": "Technical test created successfully",
            "data": test.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Error creating technical test: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create technical test: {str(e)}"
        )


@router.put("/technical-tests/{test_id}", summary="Update test", response_model=None)
async def update_technical_test(
    test_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: TechnicalTestUpdate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: TechnicalTestsRepository = Depends(get_technical_tests_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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

        test = await repo.get_by_id(test_uuid)

        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test not found: {test_id}"
            )

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(value, "value"):
                value = value.value
            setattr(test, field, value)

        test.updated_at = datetime.utcnow()

        test = await repo.update_test(test)

        logger.info(f"Updated technical test: {test.name} (ID: {test.id})")

        return {
            "success": True,
            "message": "Technical test updated successfully",
            "data": test.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Error updating technical test: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update technical test: {str(e)}"
        )


@router.delete("/technical-tests/{test_id}", summary="Delete test", response_model=None)
async def delete_technical_test(
    test_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: TechnicalTestsRepository = Depends(get_technical_tests_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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

        test = await repo.get_by_id(test_uuid)

        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test not found: {test_id}"
            )

        await repo.deactivate_test(test)

        logger.info(f"Deactivated technical test: {test.name} (ID: {test.id})")

        return {
            "success": True,
            "message": f"Technical test '{test.name}' has been deactivated"
        }

    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Error deleting technical test: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete technical test: {str(e)}"
        )


@router.get("/clients/{client_id}/tests", summary="Get tests configured for a client", response_model=None)
async def get_client_tests(
    client_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    is_enabled: bool | None = Query(None, description="Filter by enabled status"),
    category: str | None = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: TechnicalTestsRepository = Depends(get_technical_tests_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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

        rows = await repo.list_client_tests(
            client_id=client_uuid,
            is_enabled=is_enabled,
            category=category,
            limit=limit,
            offset=offset,
        )

        configs = []
        for config, test in rows:
            config_dict = config.to_dict()
            config_dict["test"] = test.to_dict()
            configs.append(config_dict)

        total = await repo.count_client_tests(
            client_id=client_uuid,
            is_enabled=is_enabled,
        )

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
        logger.error(f"Error getting client tests: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client tests: {str(e)}"
        )


@router.put("/clients/{client_id}/tests/{test_id}", summary="Configure test for client", response_model=None)
async def configure_client_test(
    client_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    test_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: ClientTestConfigCreate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: TechnicalTestsRepository = Depends(get_technical_tests_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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

        test = await repo.get_by_id(test_uuid)

        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test not found: {test_id}"
            )

        config = await repo.get_client_test_config(client_uuid, test_uuid)

        is_new = config is None
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
            message = "Test configuration created successfully"

        config = await repo.upsert_client_test_config(config, is_new=is_new)

        config_dict = config.to_dict()
        config_dict["test"] = test.to_dict()

        logger.info(f"Configured test {test.name} for client {client_id}")

        return {
            "success": True,
            "message": message,
            "data": config_dict
        }

    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Error configuring client test: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to configure client test: {str(e)}"
        )


@router.delete("/clients/{client_id}/tests/{test_id}", summary="Remove test from client", response_model=None)
async def remove_client_test(
    client_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    test_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: TechnicalTestsRepository = Depends(get_technical_tests_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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

        config = await repo.get_client_test_config(client_uuid, test_uuid)

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test configuration not found"
            )

        await repo.delete_client_test_config(config)

        logger.info(f"Removed test {test_id} from client {client_id}")

        return {
            "success": True,
            "message": "Test configuration removed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Error removing client test: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove client test: {str(e)}"
        )


@router.get("/clients/{client_id}/tests/stats", summary="Get test statistics for client", response_model=None)
async def get_client_test_stats(
    client_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: TechnicalTestsRepository = Depends(get_technical_tests_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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

        total_tests_enabled = await repo.count_enabled_client_tests(client_uuid)
        test_stats_rows = await repo.get_test_results_stats(client_uuid)

        total_results = 0
        total_passed = 0
        total_score_sum = 0
        stats_by_test = []

        for row in test_stats_rows:
            test = await repo.get_by_id(row.test_id)

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

        category_rows = await repo.get_category_stats(client_uuid)

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
        logger.error(f"Error getting client test stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client test stats: {str(e)}"
        )


@router.post("/technical-tests/seed", summary="Seed default tests", response_model=None)
async def seed_default_tests(
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    repo: TechnicalTestsRepository = Depends(get_technical_tests_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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
            existing = await repo.get_by_name(test_data["name"])

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
            await repo.create_test(test)
            created_count += 1

        logger.info(f"Seeded {created_count} default tests (skipped {skipped_count} existing)")

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
        await repo.rollback()
        logger.error(f"Error seeding default tests: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to seed default tests: {str(e)}"
        )

reorder_collection_before_item(router)
