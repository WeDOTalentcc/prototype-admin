"""
Pydantic schemas for Offer Proposals API.

Sprint F.4 #42 canonical-remap (2026-05-20):
- Fields aligned 1:1 with canonical OfferProposal model
  (libs/models/lia_models/offer_proposal.py).
- BREAKING WIRE CHANGE: requests and responses now use canonical field names
  (``salary``, ``currency``, ``bonus_pct``, ``benefits``, ``start_date``,
  ``response_deadline``, ``custom_clauses``, ``created_by``, ``job_vacancy_id``).
- Legacy wire names (``offered_salary``, ``validity_days``, ``recruiter_notes``,
  ``expires_at``, ``send_mode``, ``email_log_id``, ``sent_by_user_id``,
  ``job_id``, ``template_id``) are kept as **input aliases** so the FE can
  migrate at its own pace; on output the canonical names are emitted.
- ``validity_days``, ``email_log_id``, ``send_mode``, ``sent_by_user_id``,
  ``template_id`` have NO direct canonical column — they are translated at
  the service boundary (see ``OfferService``).
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from app.shared.types import WeDoBaseModel


class OfferBonusVariable(BaseModel):
    type: str = Field(..., description="commission | profit_sharing | project_bonus | other")
    value: Decimal
    frequency: str = Field(default="annual", description="monthly | quarterly | annual | one_time")
    conditions: str | None = None


class OfferDraftCreate(WeDoBaseModel):
    candidate_id: str
    # Accept both canonical ``job_vacancy_id`` and legacy wire ``job_id``.
    # Internal attribute is ``job_id`` (back-compat for existing service
    # callers); they pass it to repo / model as ``job_vacancy_id``.
    job_id: UUID = Field(
        ..., validation_alias=AliasChoices("job_id", "job_vacancy_id")
    )
    # TODO Sprint F.4 #42: canonical-remap — template_id was UUID FK in the
    # old model; canonical model uses ``template_version`` VARCHAR(32).
    # Service translates UUID -> str when persisting.
    template_id: UUID | None = None


class OfferDraftUpdate(WeDoBaseModel):
    """Update payload — accepts both canonical and legacy field names.

    Python attribute names match canonical OfferProposal columns. Legacy
    names (``offered_salary``, ``offered_start_date``, etc.) are accepted as
    validation aliases for FE back-compat.
    """
    salary: Decimal | None = Field(
        default=None, validation_alias=AliasChoices("salary", "offered_salary")
    )
    currency: str | None = Field(
        default=None,
        validation_alias=AliasChoices("currency", "offered_salary_currency"),
    )
    bonus_pct: Decimal | None = Field(
        default=None,
        validation_alias=AliasChoices("bonus_pct", "offered_bonus_admission"),
    )
    # TODO Sprint F.4 #42: bonus_target semantics differ from
    # ``offered_bonus_variable`` (canonical uses Numeric; old used JSONB
    # structure). Service extracts ``value`` if a dict is supplied.
    bonus_target: OfferBonusVariable | Decimal | None = Field(
        default=None,
        validation_alias=AliasChoices("bonus_target", "offered_bonus_variable"),
    )
    benefits: list[dict[str, Any]] | None = Field(
        default=None,
        validation_alias=AliasChoices("benefits", "offered_benefits"),
    )
    start_date: date | None = Field(
        default=None,
        validation_alias=AliasChoices("start_date", "offered_start_date"),
    )
    # TODO Sprint F.4 #42: validity_days has no direct canonical column.
    # Service translates to ``response_deadline = utcnow() + timedelta(days=N)``.
    validity_days: int | None = Field(default=None, ge=1, le=90)
    # TODO Sprint F.4 #42: recruiter_notes was free-form Text in old model.
    # Canonical model uses ``custom_clauses`` JSONB. Service wraps as
    # ``[{"clause_type": "recruiter_notes", "content": "..."}]``.
    recruiter_notes: str | None = None
    template_id: UUID | None = None

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class OfferDraftResponse(BaseModel):
    """Response — emits canonical field names; accepts legacy wire names on input.

    NOTE: FE migration to canonical names is required. Pydantic
    ``populate_by_name`` is enabled so the ORM (which already has canonical
    attributes) is read natively. Output uses canonical names exclusively.
    Legacy wire names (``job_id``, ``offered_salary``, ``created_by_user_id``,
    etc.) are accepted as ``validation_alias`` for back-compat with existing
    callers/tests.
    """
    id: UUID
    company_id: str
    candidate_id: str
    job_vacancy_id: UUID = Field(
        ..., validation_alias=AliasChoices("job_vacancy_id", "job_id")
    )
    # TODO Sprint F.4 #42: template_id has no canonical column; this is
    # synthesised from ``template_version`` (if it parses as UUID) for FE compat.
    template_id: UUID | None = None
    job_data_snapshot: dict[str, Any]
    candidate_data_snapshot: dict[str, Any]
    salary: Decimal | None = Field(
        default=None, validation_alias=AliasChoices("salary", "offered_salary")
    )
    currency: str = Field(
        default="BRL",
        validation_alias=AliasChoices("currency", "offered_salary_currency"),
    )
    bonus_pct: Decimal | None = Field(
        default=None,
        validation_alias=AliasChoices("bonus_pct", "offered_bonus_admission"),
    )
    bonus_target: Decimal | None = Field(
        default=None,
        validation_alias=AliasChoices("bonus_target", "offered_bonus_variable"),
    )
    benefits: list[dict[str, Any]] | None = Field(
        default=None, validation_alias=AliasChoices("benefits", "offered_benefits")
    )
    start_date: date | None = Field(
        default=None,
        validation_alias=AliasChoices("start_date", "offered_start_date"),
    )
    # TODO Sprint F.4 #42: validity_days is derived from response_deadline
    # at the service boundary.
    validity_days: int = 7
    response_deadline: datetime | None = Field(
        default=None,
        validation_alias=AliasChoices("response_deadline", "expires_at"),
    )
    # TODO Sprint F.4 #42: recruiter_notes is derived from custom_clauses
    # JSONB on read (service flattens for wire).
    recruiter_notes: str | None = None
    custom_clauses: list[dict[str, Any]] | None = None
    status: str
    # TODO Sprint F.4 #42: send_mode has no canonical column; service may
    # extract from sent_via JSONB first item's metadata.
    send_mode: str | None = None
    # TODO Sprint F.4 #42: email_log_id has no canonical column; service
    # extracts from sent_via JSONB ``[{"channel": "email", "log_id": ...}]``.
    email_log_id: UUID | None = None
    sent_via: list[dict[str, Any]] | None = None
    created_by: str | None = Field(
        default=None,
        validation_alias=AliasChoices("created_by", "created_by_user_id"),
    )
    # TODO Sprint F.4 #42: sent_by_user_id has no canonical column.
    # Canonical model has only ``created_by``. Extracted from sent_via.
    sent_by_user_id: str | None = None
    sent_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class OfferDraftListResponse(BaseModel):
    """Paginated list of offer drafts for a job vacancy."""
    offers: list[OfferDraftResponse]
    total: int | None = None

    model_config = ConfigDict(from_attributes=True)


class OfferSendAutoRequest(WeDoBaseModel):
    pass  # draft data already in DB; no extra params needed


class OfferSendAutoResponse(BaseModel):
    offer_id: UUID
    status: str  # sent
    email_log_id: UUID | None
    sent_at: datetime
    message: str
    offer_link: str | None = None


class OfferPrepareManualResponse(BaseModel):
    offer_id: UUID
    template_id: UUID | None
    subject_pre_filled: str
    body_pre_filled: str
    variables: dict[str, str]
    message: str


class OfferCancelRequest(WeDoBaseModel):
    reason: str | None = None
