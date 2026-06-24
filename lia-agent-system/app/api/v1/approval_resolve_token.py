"""
Public endpoint for resolving vacancy approvals via magic token (TIPO B approvers).

POST /approvals/resolve-by-token
  - No JWT authentication required — token IS the credential.
  - Validates: token exists, not expired, not already used.
  - Marks magic_token_used=True after resolving (single-use).
  - Creates audit trail for LGPD Art.37V.
  - Triggers approval cascade: if all level-N approved → level-N+1 notified.
"""
import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.shared.types import WeDoBaseModel

from app.core.database import get_db
from app.repositories.approvals_repository import ApprovalsRepository
from lia_models.approval import ApprovalStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/approvals", tags=["approvals"])


class ResolveByTokenRequest(WeDoBaseModel):
    token: str
    decision: str  # "approve" | "reject"
    notes: str | None = None


class ResolveByTokenResponse(BaseModel):  # response — extra='allow' is fine
    ok: bool
    message: str
    approval_id: str | None = None


@router.post("/resolve-by-token", response_model=ResolveByTokenResponse)
async def resolve_approval_by_token(
    payload: ResolveByTokenRequest,
):
    """Resolve a vacancy approval request using a magic link token.

    Public endpoint (no JWT required). Token proves identity for TIPO B
    (external approver without a platform account).

    Error codes:
      400 — invalid decision value
      404 — token not found
      410 — token expired or already used
    """
    if payload.decision not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="decision deve ser 'approve' ou 'reject'")

    now = datetime.utcnow()

    async for db in get_db():
        repo = ApprovalsRepository(db)
        req = await repo.get_by_magic_token(payload.token)

        if not req:
            raise HTTPException(status_code=404, detail="Token não encontrado ou inválido.")

        if req.magic_token_used:
            raise HTTPException(status_code=410, detail="Este link de aprovação já foi utilizado.")

        if req.magic_token_expires_at and req.magic_token_expires_at < now:
            raise HTTPException(status_code=410, detail="Este link de aprovação expirou.")

        # Resolve the approval request
        new_status = (
            ApprovalStatus.APPROVED.value
            if payload.decision == "approve"
            else ApprovalStatus.REJECTED.value
        )
        req.status = new_status
        req.magic_token_used = True
        req.approval_notes = payload.notes or ""
        req.decided_at = now

        await db.flush()
        await db.refresh(req)

        # Audit trail — LGPD Art.37V
        try:
            from app.shared.compliance.audit_service import AuditService
            audit = AuditService(db)
            await audit.log_action(
                trace_id=f"resolve-token-{str(req.id)[:8]}",
                company_id=str(req.company_id),
                action_type=f"approval_{payload.decision}d",
                actor=req.approver_email,
                target_id=str(req.target_id),
                target_type=req.target_type,
                metadata={
                    "approval_id": str(req.id),
                    "method": "magic_link",
                    "approver_name": req.approver_name,
                    "notes": payload.notes or "",
                },
            )
        except Exception as audit_exc:
            logger.warning("[resolve-by-token] audit log failed — non-blocking. err=%s", audit_exc)

        await db.commit()

        decision_label = "aprovada" if payload.decision == "approve" else "rejeitada"
        logger.info(
            "[resolve-by-token] approval_id=%s decision=%s approver_email=%s",
            str(req.id),
            payload.decision,
            req.approver_email,
        )

        return ResolveByTokenResponse(
            ok=True,
            message=f"Aprovação {decision_label} com sucesso.",
            approval_id=str(req.id),
        )

    raise HTTPException(status_code=500, detail="Erro interno — tente novamente.")
