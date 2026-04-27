"""
Pydantic schemas for Offer Proposals API.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class OfferBonusVariable(BaseModel):
    type: str = Field(..., description="commission | profit_sharing | project_bonus | other")
    value: Decimal
    frequency: str = Field(default="annual", description="monthly | quarterly | annual | one_time")
    conditions: str | None = None


class OfferDraftCreate(BaseModel):
    candidate_id: str
    job_id: UUID
    template_id: UUID | None = None


class OfferDraftUpdate(BaseModel):
    offered_salary: Decimal | None = None
    offered_salary_currency: str | None = None
    offered_bonus_admission: Decimal | None = None
    offered_bonus_variable: OfferBonusVariable | None = None
    offered_benefits: list[dict[str, Any]] | None = None
    offered_start_date: date | None = None
    validity_days: int | None = Field(None, ge=1, le=90)
    recruiter_notes: str | None = None
    template_id: UUID | None = None


class OfferDraftResponse(BaseModel):
    id: UUID
    company_id: str
    candidate_id: str
    job_id: UUID
    template_id: UUID | None = None
    job_data_snapshot: dict[str, Any]
    candidate_data_snapshot: dict[str, Any]
    offered_salary: Decimal | None = None
    offered_salary_currency: str = "BRL"
    offered_bonus_admission: Decimal | None = None
    offered_bonus_variable: dict[str, Any] | None = None
    offered_benefits: list[dict[str, Any]] | None = None
    offered_start_date: date | None = None
    validity_days: int = 7
    expires_at: datetime | None = None
    recruiter_notes: str | None = None
    status: str
    send_mode: str | None = None
    email_log_id: UUID | None = None
    created_by_user_id: str
    sent_by_user_id: str | None = None
    sent_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OfferSendAutoRequest(BaseModel):
    pass  # draft data already in DB; no extra params needed


class OfferSendAutoResponse(BaseModel):
    offer_id: UUID
    status: str  # "sent"
    email_log_id: UUID
    sent_at: datetime
    message: str


class OfferPrepareManualResponse(BaseModel):
    offer_id: UUID
    template_id: UUID | None
    subject_pre_filled: str
    body_pre_filled: str
    variables: dict[str, str]
    message: str


class OfferCancelRequest(BaseModel):
    reason: str | None = None
