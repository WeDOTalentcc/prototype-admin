"""
Credits API endpoints.
Manages company credit balance for paid features (global search, AI analysis, etc.).
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.credit_service import CreditService
from lia_models.billing import CreditTransactionType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/credits", tags=["credits"])

_credit_service = CreditService()


def _get_company_id(request: Request) -> str:
    company_id = getattr(request.state, "company_id", None)
    if not company_id:
        raise HTTPException(status_code=401, detail="Company context required")
    return company_id


class CreditBalanceResponse(BaseModel):
    balance: int
    lifetime_purchased: int
    lifetime_consumed: int
    lifetime_bonus: int
    updated_at: str | None = None


class AddCreditsRequest(BaseModel):
    amount: int = Field(..., gt=0, le=100000)
    transaction_type: str = Field(
        default="purchase",
        description="One of: purchase, bonus, refund, subscription_grant, adjustment",
    )
    description: str = Field(default="Manual credit addition")
    reference_type: str | None = None
    reference_id: str | None = None


class ConsumeCreditsRequest(BaseModel):
    amount: int = Field(..., gt=0, le=10000)
    description: str
    reference_type: str | None = None
    reference_id: str | None = None


class CreditTransactionResponse(BaseModel):
    id: str
    company_id: str
    transaction_type: str
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
    db: AsyncSession = Depends(get_db),
):
    company_id = _get_company_id(request)
    try:
        data = await _credit_service.get_balance(db, company_id)
        await db.commit()
        return CreditBalanceResponse(**data)
    except Exception as e:
        logger.error("[Credits] Error fetching balance for %s: %s", company_id, e)
        raise HTTPException(status_code=500, detail="Error fetching credit balance")


@router.post("/add", response_model=CreditBalanceResponse)
async def add_credits(
    request: Request,
    body: AddCreditsRequest,
    db: AsyncSession = Depends(get_db),
):
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
        new_balance = await _credit_service.add_credits(
            db,
            company_id,
            body.amount,
            tx_type,
            body.description,
            reference_type=body.reference_type,
            reference_id=body.reference_id,
            performed_by=user_id,
        )
        await db.commit()
        data = await _credit_service.get_balance(db, company_id)
        return CreditBalanceResponse(**data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("[Credits] Error adding credits for %s: %s", company_id, e)
        raise HTTPException(status_code=500, detail="Error adding credits")


@router.post("/consume")
async def consume_credits(
    request: Request,
    body: ConsumeCreditsRequest,
    db: AsyncSession = Depends(get_db),
):
    company_id = _get_company_id(request)
    user_id = getattr(request.state, "user_id", "system")

    try:
        success, remaining = await _credit_service.consume(
            db,
            company_id,
            body.amount,
            body.description,
            reference_type=body.reference_type,
            reference_id=body.reference_id,
            performed_by=user_id,
        )
        if not success:
            raise HTTPException(
                status_code=402,
                detail=f"Insufficient credits. Current balance: {remaining}",
            )
        await db.commit()
        return {"success": True, "remaining_balance": remaining}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("[Credits] Error consuming credits for %s: %s", company_id, e)
        raise HTTPException(status_code=500, detail="Error consuming credits")


@router.get("/transactions", response_model=list[CreditTransactionResponse])
async def get_credit_transactions(
    request: Request,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
):
    company_id = _get_company_id(request)
    try:
        txs = await _credit_service.get_transactions(db, company_id, limit, offset)
        return txs
    except Exception as e:
        logger.error("[Credits] Error fetching transactions for %s: %s", company_id, e)
        raise HTTPException(status_code=500, detail="Error fetching transactions")
