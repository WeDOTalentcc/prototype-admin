"""
Credits API endpoints.
Manages company credit balance for paid features (global search, AI analysis, etc.).
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from app.domains.credits.dependencies import get_credits_repo
from app.domains.credits.repositories.credits_repository import CreditsRepository
from app.domains.credits.services.credit_service import ACTION_CREDIT_COSTS
from lia_models.billing import CreditTransactionType
from app.shared.security.require_company_id import require_company_id
from app.shared.errors import LIAError
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/credits", tags=["credits"])


def _get_company_id(request: Request) -> str:
    company_id = getattr(request.state, "company_id", None)
    if not company_id:
        raise HTTPException(status_code=401, detail="Company context required")
    return company_id


class CreditBalanceResponse(BaseModel):
    balance: int
    plan_type: str = "free"
    lifetime_purchased: int
    lifetime_consumed: int
    lifetime_bonus: int
    low_balance_warning: bool = False
    low_balance_threshold: int = 20
    reset_date: str | None = None
    updated_at: str | None = None


class AddCreditsRequest(WeDoBaseModel):
    amount: int = Field(..., gt=0, le=100000)
    transaction_type: str = Field(
        default="purchase",
        description="One of: purchase, bonus, refund, subscription_grant, adjustment",
    )
    description: str = Field(default="Manual credit addition")
    reference_type: str | None = None
    reference_id: str | None = None


class ConsumeCreditsRequest(WeDoBaseModel):
    amount: int = Field(..., gt=0, le=10000)
    description: str
    action_type: str | None = None
    reference_type: str | None = None
    reference_id: str | None = None


class ConsumeActionRequest(WeDoBaseModel):
    action_type: str = Field(..., description="Action type (search, analysis, screening, report, etc.)")
    reference_type: str | None = None
    reference_id: str | None = None


class CreditTransactionResponse(BaseModel):
    id: str
    company_id: str
    transaction_type: str
    action_type: str | None = None
    amount: int
    balance_after: int
    description: str | None
    reference_type: str | None
    reference_id: str | None
    performed_by: str | None
    created_at: str | None


@router.get("/balance", response_model=CreditBalanceResponse)
async def get_credit_balance(
    request: Request,
    repo: CreditsRepository = Depends(get_credits_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    company_id = _get_company_id(request)
    try:
        data = await repo.get_balance(company_id)
        return CreditBalanceResponse(**data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[Credits] Error fetching balance for %s: %s", company_id, e)
        raise LIAError(message="Error fetching credit balance")


@router.post("/add", response_model=CreditBalanceResponse)
async def add_credits(
    request: Request,
    body: AddCreditsRequest,
    repo: CreditsRepository = Depends(get_credits_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    user_role = getattr(request.state, "user_role", None)
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    company_id = _get_company_id(request)
    user_id = getattr(request.state, "user_id", "system")

    valid_types = {t.value for t in CreditTransactionType} - {
        CreditTransactionType.CONSUMPTION.value,
        CreditTransactionType.EXPIRATION.value,
    }
    if body.transaction_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transaction type. Must be one of: {sorted(valid_types)}",
        )

    try:
        tx_type = CreditTransactionType(body.transaction_type)
        data = await repo.add_credits(
            company_id,
            body.amount,
            tx_type,
            body.description,
            reference_type=body.reference_type,
            reference_id=body.reference_id,
            performed_by=user_id,
        )
        return CreditBalanceResponse(**data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[Credits] Error adding credits for %s: %s", company_id, e)
        raise LIAError(message="Error adding credits")


@router.post("/consume")
async def consume_credits(
    request: Request,
    body: ConsumeCreditsRequest,
    repo: CreditsRepository = Depends(get_credits_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    company_id = _get_company_id(request)
    user_id = getattr(request.state, "user_id", "system")

    try:
        success, remaining = await repo.consume(
            company_id,
            body.amount,
            body.description,
            action_type=body.action_type,
            reference_type=body.reference_type,
            reference_id=body.reference_id,
            performed_by=user_id,
        )
        if not success:
            raise HTTPException(
                status_code=402,
                detail=f"Insufficient credits. Current balance: {remaining}",
            )
        return {"success": True, "remaining_balance": remaining}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("[Credits] Error consuming credits for %s: %s", company_id, e)
        raise LIAError(message="Error consuming credits")


@router.post("/consume-action")
async def consume_action_credits(
    request: Request,
    body: ConsumeActionRequest,
    repo: CreditsRepository = Depends(get_credits_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    company_id = _get_company_id(request)
    user_id = getattr(request.state, "user_id", "system")

    if body.action_type not in ACTION_CREDIT_COSTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown action type {body.action_type}. Valid: {sorted(ACTION_CREDIT_COSTS.keys())}",
        )

    try:
        success, remaining = await repo.consume_action(
            company_id,
            body.action_type,
            reference_type=body.reference_type,
            reference_id=body.reference_id,
            performed_by=user_id,
        )
        if not success:
            raise HTTPException(
                status_code=402,
                detail=f"Insufficient credits. Current balance: {remaining}",
            )
        return {
            "success": True,
            "action_type": body.action_type,
            "cost": ACTION_CREDIT_COSTS[body.action_type],
            "remaining_balance": remaining,
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("[Credits] Error consuming action credits for %s: %s", company_id, e)
        raise LIAError(message="Error consuming credits")


@router.get("/costs")
async def get_action_costs(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    return {
        "costs": ACTION_CREDIT_COSTS,
    }


@router.get("/transactions", response_model=list[CreditTransactionResponse])
async def get_credit_transactions(
    request: Request,
    repo: CreditsRepository = Depends(get_credits_repo),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    company_id = _get_company_id(request)
    try:
        txs = await repo.get_transactions(company_id, limit, offset)
        return txs
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[Credits] Error fetching transactions for %s: %s", company_id, e)
        raise LIAError(message="Error fetching transactions")
