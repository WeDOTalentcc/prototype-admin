"""Endpoint de validacao de contato (Peca C) — consumido pelos badges da tabela (Peca B).

POST /search/validate-contacts: recebe lista de candidatos com email/telefone e
devolve veredito de validade por candidato (email com MX, telefone E.164). Permite
ao recrutador ver quem realmente vai receber email/WhatsApp antes de disparar.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from app.shared.security.require_company_id import require_company_id
from app.shared.services.contact_validation_service import get_contact_validation_service

router = APIRouter()

_MAX_BATCH = 100


class ContactToValidate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate_id: str
    email: str | None = None
    phone: str | None = None


class ValidateContactsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    contacts: list[ContactToValidate] = Field(default_factory=list)


class ContactValidity(BaseModel):
    candidate_id: str
    email_valid: bool | None = None
    email_reason: str | None = None
    phone_valid: bool | None = None
    phone_e164: str | None = None


class ValidateContactsResponse(BaseModel):
    results: list[ContactValidity]


@router.post("/validate-contacts", response_model=ValidateContactsResponse)
async def validate_contacts(
    request: ValidateContactsRequest,
    company_id: str = Depends(require_company_id),
):
    svc = get_contact_validation_service()
    results: list[ContactValidity] = []
    for c in request.contacts[:_MAX_BATCH]:
        item = ContactValidity(candidate_id=c.candidate_id)
        if c.email:
            ev = svc.validate_email(c.email)
            item.email_valid = ev["valid"]
            item.email_reason = ev["reason"] or None
        if c.phone:
            pv = svc.validate_phone(c.phone)
            item.phone_valid = pv["valid"]
            item.phone_e164 = pv["e164"]
        results.append(item)
    return ValidateContactsResponse(results=results)
