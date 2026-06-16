"""
Shared Searches API endpoints - manage shared candidate searches with external stakeholders.
"""
import hashlib
import logging
import secrets
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr

from app.auth.dependencies import get_current_user_or_demo, get_user_company_id
from lia_models.candidate import VacancyCandidate
from app.auth.models import User
from app.domains.communication.services.email_providers import get_email_provider
from app.repositories.dependencies import get_shared_search_repo
from app.repositories.shared_search_repository import (
    SharedSearchRepository,
)
from app.models.shared_search import (
    SharedSearch,
    SharedSearchAccess,
    SharedSearchStatus,
    ShareType,
)
from app.schemas.shared_search import (
    CreateSharedSearchRequest,
    FeedbackSummary,
    RecipientSummary,
    ShareChannel,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter()


class UpdateSharedSearchRequest(WeDoBaseModel):
    status: str | None = None
    expires_at: datetime | None = None
    description: str | None = None


class ResendInviteRequest(WeDoBaseModel):
    email: EmailStr


class AddToJobRequest(WeDoBaseModel):
    job_id: str
    candidate_ids: list[str] | None = None
    all_approved: bool = False
    include_notes: bool = False


def parse_company_uuid(company_id: str):
    """Parse company_id, returning UUID if valid, otherwise None."""
    try:
        if company_id and len(company_id) >= 32:
            return uuid.UUID(company_id)
    except (ValueError, TypeError):
        pass
    return None


def generate_access_token() -> str:
    return secrets.token_urlsafe(32)


def generate_otp() -> str:
    return secrets.token_hex(3).upper()


def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()


def send_shared_search_invite_email(
    to_email: str,
    to_name: str | None,
    otp_code: str,
    access_token: str,
    search_title: str,
    candidate_count: int,
    recruiter_name: str,
    company_name: str,
    message: str | None = None,
    expires_at: datetime | None = None,
    subject_override: str | None = None,
) -> bool:
    """Send invitation email to share recipient."""
    try:
        import os
        base_url = (
            os.environ.get("APP_BASE_URL")
            or os.environ.get("PUBLIC_URL")
            or (f"https://{d}" if (d := os.environ.get("REPLIT_DEV_DOMAIN")) else None)
            or "http://localhost:5000"
        ).rstrip("/")

        access_url = f"{base_url}/shared/{access_token}"
        recipient_greeting = to_name or "Gestor(a)"
        expiry_text = (
            f"<p style='color: #666; font-size: 14px;'>Este link expira em "
            f"{expires_at.strftime('%d/%m/%Y às %H:%M') if expires_at else 'breve'}.</p>"
            if expires_at
            else ""
        )
        message_html = (
            f"<p style='color: #333; font-size: 14px; background: #f5f5f5; padding: 12px; "
            f"border-radius: 6px; margin: 16px 0;'><em>\"{message}\"</em></p>"
            if message
            else ""
        )

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: 'Open Sans', Arial, sans-serif; background: #f9fafb; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                <div style="background: linear-gradient(135deg, #1a1a1a 0%, #333 100%); padding: 32px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 24px; font-weight: 600;">LIA</h1>
                    <p style="color: #60BED1; margin: 8px 0 0; font-size: 14px;">Learning Intelligence Assistant</p>
                </div>

                <div style="padding: 32px;">
                    <h2 style="color: #1a1a1a; font-size: 20px; margin: 0 0 16px;">Olá, {recipient_greeting}!</h2>

                    <p style="color: #333; font-size: 14px; line-height: 1.6; margin: 0 0 16px;">
                        <strong>{recruiter_name}</strong> da <strong>{company_name}</strong> compartilhou uma seleção de candidatos com você para avaliação.
                    </p>

                    {message_html}

                    <div style="background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; margin: 24px 0;">
                        <p style="color: #666; font-size: 12px; margin: 0 0 4px; text-transform: uppercase; letter-spacing: 0.5px;">Busca compartilhada</p>
                        <p style="color: #1a1a1a; font-size: 16px; font-weight: 600; margin: 0 0 8px;">{search_title}</p>
                        <p style="color: #60BED1; font-size: 14px; margin: 0;">
                            <strong>{candidate_count}</strong> candidato{"s" if candidate_count != 1 else ""} para avaliar
                        </p>
                    </div>

                    <div style="background: #60BED1; border-radius: 8px; padding: 20px; text-align: center; margin: 24px 0;">
                        <p style="color: white; font-size: 12px; margin: 0 0 8px; text-transform: uppercase; letter-spacing: 0.5px;">Seu código de acesso</p>
                        <p style="color: white; font-size: 32px; font-weight: 700; margin: 0; letter-spacing: 4px; font-family: monospace;">{otp_code}</p>
                    </div>

                    <a href="{access_url}" style="display: block; background: #1a1a1a; color: white; text-decoration: none; padding: 14px 24px; border-radius: 8px; text-align: center; font-size: 14px; font-weight: 600; margin: 24px 0;">
                        Avaliar Candidatos
                    </a>

                    {expiry_text}

                    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">

                    <p style="color: #999; font-size: 12px; line-height: 1.5; margin: 0;">
                        Se você não esperava este email, pode ignorá-lo com segurança.<br>
                        Este é um email automático, por favor não responda.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        provider = get_email_provider()
        result = provider.send(
            to=to_email,
            subject=subject_override or f"🔍 {recruiter_name} compartilhou candidatos para sua avaliação",
            html=html,
            from_name="LIA - WeDoTalent"
        )

        if result.success:
            # pii-logs ok: PII mascarado em runtime via PIIMaskingFilter (LGPD Art.46 — defesa em profundidade)
            logger.info(f"Invite email sent to {to_email}")
        else:
            # pii-logs ok: PII mascarado em runtime via PIIMaskingFilter (LGPD Art.46 — defesa em profundidade)
            logger.warning(f"Failed to send invite email to {to_email}: {result.error}")

        return result.success
    except Exception as e:
        logger.error(f"Error sending invite email: {e}")
        return False


def render_template_variables(template_str: str, variables: dict) -> str:
    """Replace {{variable}} placeholders in template string."""
    result = template_str
    for key, value in variables.items():
        result = result.replace(f"{{{{{key}}}}}", str(value) if value else "")
    return result


def send_whatsapp_simulated(
    to_phone: str,
    to_name: str | None,
    message_body: str,
    recruiter_name: str,
    search_title: str,
    candidate_count: int,
) -> bool:
    """Log a simulated WhatsApp message (not actually sent)."""
    logger.info(
        f"[WhatsApp SIMULATED] To: {to_phone} ({to_name or 'N/A'}) | "
        f"From: {recruiter_name} | Search: {search_title} | "
        f"Candidates: {candidate_count} | Message length: {len(message_body)} chars"
    )
    logger.info(f"[WhatsApp SIMULATED] Body: {message_body[:500]}")
    return True


async def build_candidate_snapshot(
    repo: SharedSearchRepository, candidate_ids: list[uuid.UUID]
) -> list[dict]:
    if not candidate_ids:
        return []

    candidates = await repo.get_candidates_by_ids(candidate_ids)

    snapshots = []
    for c in candidates:
        location_parts = [c.location_city, c.location_state, c.location_country]
        location = ", ".join([p for p in location_parts if p])

        snapshots.append({
            "id": str(c.id),
            "name": c.name,
            "title": c.current_title,
            "company": c.current_company,
            "location": location or None,
            "experience_years": c.years_of_experience,
            "skills": c.technical_skills or [],
            "wsi_score": c.lia_score,
            "avatar_url": c.avatar_url,
            "linkedin_url": c.linkedin_url,
            "resume_url": c.resume_url
        })

    return snapshots


def build_feedback_summary(feedbacks, total_candidates: int) -> FeedbackSummary:
    counts = {"approved": 0, "maybe": 0, "rejected": 0}
    for f in feedbacks:
        if f.decision.value in counts:
            counts[f.decision.value] += 1

    reviewed = sum(counts.values())
    return FeedbackSummary(
        approved=counts["approved"],
        maybe=counts["maybe"],
        rejected=counts["rejected"],
        pending=max(0, total_candidates - reviewed)
    )


@router.post("", response_model=None)
async def create_shared_search(
    data: CreateSharedSearchRequest,
    repo: SharedSearchRepository = Depends(get_shared_search_repo),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)):
    """
    Create a new shared search with candidate snapshots and recipient access tokens.
    """
    try:
        logger.info(f"Creating shared search - data: {data}")
        company_id = get_user_company_id(current_user)
        logger.info(f"Company ID: {company_id}")
        company_uuid = parse_company_uuid(company_id)

        if not company_uuid:
            company_uuid = await repo.get_default_company_id()
            if company_uuid:
                logger.info(f"Using default company UUID: {company_uuid}")

        logger.info(f"Company UUID: {company_uuid}")

        if not company_uuid:
            logger.error(f"Invalid company ID: {company_id}")
            raise HTTPException(status_code=400, detail="Company ID inválido para criar compartilhamento")

        candidate_uuids = [uuid.UUID(str(cid)) for cid in data.candidate_ids]

        # G6 LGPD consent gate — sharing PII with third parties requires explicit consent (Art. 7)
        # ADR-LGPD-002: this is NOT recruiter viewing own data (Art. 7 II legítimo interesse);
        # this is sharing with EXTERNAL recipients (hiring managers) via link+OTP = third-party disclosure
        candidates_for_consent = await repo.get_candidates_by_ids(candidate_uuids)
        candidates_without_consent = [
            str(c.id) for c in candidates_for_consent
            if not getattr(c, "communication_consent", False)
        ]
        if candidates_without_consent:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "lgpd_consent_missing",
                    "message": (
                        f"{len(candidates_without_consent)} candidato(s) não consentiram com "
                        f"compartilhamento de dados. Obtenha o consentimento antes de compartilhar."
                    ),
                    "candidate_ids_without_consent": candidates_without_consent,
                },
            )

        snapshot_data = await build_candidate_snapshot(repo, candidate_uuids)

        if not snapshot_data:
            raise HTTPException(status_code=400, detail="Nenhum candidato válido encontrado")

        shared_search = SharedSearch(
            id=uuid.uuid4(),
            company_id=company_uuid,
            created_by_user_id=current_user.id,
            share_type=ShareType(data.share_type.value),
            source_query=data.source_query,
            source_list_id=data.source_list_id,
            title=data.title,
            description=data.description,
            expires_at=data.expires_at,
            status=SharedSearchStatus.active,
            snapshot_payload={"candidates": snapshot_data},
            can_comment=data.can_comment,
            can_rate=data.can_rate,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        await repo.create_shared_search(shared_search)

        access_records = []
        for recipient in data.recipients:
            access_token = generate_access_token()
            otp = generate_otp()

            access_record = SharedSearchAccess(
                id=uuid.uuid4(),
                shared_search_id=shared_search.id,
                email=recipient.email,
                name=recipient.name,
                role=recipient.role,
                access_token=access_token,
                otp_hash=hash_otp(otp),
                otp_expires_at=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            await repo.create_access_record(access_record)
            access_records.append({
                "email": recipient.email,
                "name": recipient.name,
                "phone": recipient.phone,
                "role": recipient.role,
                "access_token": access_token,
                "otp": otp
            })

        await repo.commit()
        await repo.refresh(shared_search)

        recruiter_name = current_user.name or current_user.email or "Recrutador"
        company_name = "WeDoTalent"
        channel = data.channel
        send_email = channel in (ShareChannel.email, ShareChannel.both)
        send_whatsapp = channel in (ShareChannel.whatsapp, ShareChannel.both)

        email_template = None
        whatsapp_template = None
        if send_email:
            email_template = await repo.get_share_template("email", company_id)
        if send_whatsapp:
            whatsapp_template = await repo.get_share_template("whatsapp", company_id)

        import os
        base_url = (
            os.environ.get("APP_BASE_URL")
            or os.environ.get("PUBLIC_URL")
            or (f"https://{d}" if (d := os.environ.get("REPLIT_DEV_DOMAIN")) else None)
            or "http://localhost:5000"
        ).rstrip("/")

        for record in access_records:
            access_url = f"{base_url}/shared/{record['access_token']}"
            template_vars = {
                "recruiter_name": recruiter_name,
                "job_title": data.title,
                "candidate_count": str(len(snapshot_data)),
                "share_link": access_url,
                "otp_code": record["otp"],
                "expiry_date": data.expires_at.strftime("%d/%m/%Y às %H:%M") if data.expires_at else "",
                "message": data.message or "",
                "company_name": company_name,
            }

            if send_email:
                if email_template:
                    subject_source = data.subject if data.subject else (email_template.subject or "")
                    rendered_subject = render_template_variables(subject_source, template_vars)
                    rendered_html = render_template_variables(email_template.body_html, template_vars)
                    try:
                        provider = get_email_provider()
                        result = provider.send(
                            to=record["email"],
                            subject=rendered_subject,
                            html=rendered_html,
                            from_name="LIA - WeDoTalent"
                        )
                        if result.success:
                            # pii-logs ok: PII mascarado em runtime via PIIMaskingFilter (LGPD Art.46 — defesa em profundidade)
                            logger.info(f"Invite email (from template) sent to {record['email']}")
                        else:
                            # pii-logs ok: PII mascarado em runtime via PIIMaskingFilter (LGPD Art.46 — defesa em profundidade)
                            logger.warning(f"Failed to send invite email to {record['email']}: {result.error}")
                    except Exception as e:
                        logger.error(f"Error sending templated invite email: {e}")
                else:
                    send_shared_search_invite_email(
                        to_email=record["email"],
                        to_name=record["name"],
                        otp_code=record["otp"],
                        access_token=record["access_token"],
                        search_title=data.title,
                        candidate_count=len(snapshot_data),
                        recruiter_name=recruiter_name,
                        company_name=company_name,
                        message=data.message,
                        expires_at=data.expires_at,
                        subject_override=data.subject,
                    )

            if send_whatsapp:
                phone = record.get("phone")
                if phone:
                    if whatsapp_template:
                        wa_body = render_template_variables(
                            whatsapp_template.body_text or whatsapp_template.body_html,
                            template_vars
                        )
                    else:
                        wa_body = (
                            f"Olá! {recruiter_name} da {company_name} compartilhou "
                            f"{len(snapshot_data)} candidato(s) para a vaga \"{data.title}\" "
                            f"com você. Acesse: {access_url} | Código: {record['otp']}"
                        )
                    send_whatsapp_simulated(
                        to_phone=phone,
                        to_name=record["name"],
                        message_body=wa_body,
                        recruiter_name=recruiter_name,
                        search_title=data.title,
                        candidate_count=len(snapshot_data),
                    )
                else:
                    logger.warning(
                        f"WhatsApp channel requested but no phone for recipient {record['email']}"
                    )

        logger.info(f"Shared search created id={shared_search.id} channel={channel.value}")

        recipients_summary = [
            RecipientSummary(
                email=r["email"],
                name=r["name"],
                role=r["role"],
                first_accessed_at=None,
                last_accessed_at=None,
                total_views=0,
                feedback_count=0
            )
            for r in access_records
        ]

        return {
            "id": str(shared_search.id),
            "company_id": str(shared_search.company_id),
            "share_type": shared_search.share_type.value,
            "title": shared_search.title,
            "description": shared_search.description,
            "status": shared_search.status.value,
            "expires_at": shared_search.expires_at.isoformat() if shared_search.expires_at else None,
            "created_at": shared_search.created_at.isoformat() if shared_search.created_at else None,
            "candidate_count": len(snapshot_data),
            "channel": channel.value,
            "feedback_summary": FeedbackSummary(pending=len(snapshot_data)).model_dump(),
            "recipients": [r.model_dump() for r in recipients_summary],
            "access_links": access_records
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating shared search: {e}", exc_info=True)
        await repo.rollback()
        raise LIAError(message="Erro interno do servidor")


@router.get("", response_model=None)
async def list_shared_searches(
    status: str | None = Query(None, description="Filter by status: active, expired, revoked"),
    share_type: str | None = Query(None, description="Filter by type: search, list"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    repo: SharedSearchRepository = Depends(get_shared_search_repo),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)):
    """
    List shared searches for the current company with feedback summaries.
    """
    try:
        company_id = get_user_company_id(current_user)
        company_uuid = parse_company_uuid(company_id)

        if not company_uuid:
            return {"total": 0, "offset": offset, "limit": limit, "items": []}

        total, searches = await repo.list_shared_searches(
            company_uuid=company_uuid,
            status=status,
            share_type=share_type,
            offset=offset,
            limit=limit,
        )

        items = []
        for search in searches:
            access_records = await repo.get_access_by_search(search.id)
            feedbacks = await repo.get_feedbacks_by_search(search.id)

            candidates_in_snapshot = search.snapshot_payload.get("candidates", []) if search.snapshot_payload else []
            feedback_summary = build_feedback_summary(feedbacks, len(candidates_in_snapshot))

            feedback_counts_by_email = {}
            for f in feedbacks:
                feedback_counts_by_email[f.reviewer_email] = feedback_counts_by_email.get(f.reviewer_email, 0) + 1

            recipients = [
                RecipientSummary(
                    email=acc.email,
                    name=acc.name,
                    role=acc.role,
                    first_accessed_at=acc.first_accessed_at,
                    last_accessed_at=acc.last_accessed_at,
                    total_views=acc.total_views,
                    feedback_count=feedback_counts_by_email.get(acc.email, 0)
                )
                for acc in access_records
            ]

            first_recipient = access_records[0] if access_records else None
            share_url = f"/shared/{first_recipient.access_token}" if first_recipient else None

            items.append({
                "id": str(search.id),
                "company_id": str(search.company_id),
                "share_type": search.share_type.value,
                "title": search.title,
                "description": search.description,
                "status": search.status.value,
                "expires_at": search.expires_at.isoformat() if search.expires_at else None,
                "created_at": search.created_at.isoformat() if search.created_at else None,
                "candidate_count": len(candidates_in_snapshot),
                "feedback_summary": feedback_summary.model_dump(),
                "feedback_counts": {
                    "approved": feedback_summary.approved,
                    "rejected": feedback_summary.rejected,
                    "maybe": feedback_summary.maybe,
                    "pending": feedback_summary.pending,
                    "new_count": 0
                },
                "share_url": share_url,
                "recipient_email": first_recipient.email if first_recipient else None,
                "recipient_name": first_recipient.name if first_recipient else None,
                "first_accessed_at": first_recipient.first_accessed_at.isoformat() if first_recipient and first_recipient.first_accessed_at else None,
                "recipients": [r.model_dump() for r in recipients]
            })

        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "items": items
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing shared searches: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/{search_id}", response_model=None)
async def get_shared_search(
    search_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    repo: SharedSearchRepository = Depends(get_shared_search_repo),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)):
    """
    Get shared search details including all candidates and feedbacks.
    """
    try:
        company_id = get_user_company_id(current_user)
        company_uuid = parse_company_uuid(company_id)

        if not company_uuid:
            raise HTTPException(status_code=404, detail="Compartilhamento não encontrado")

        search = await repo.get_by_id_and_company(uuid.UUID(search_id), company_uuid)

        if not search:
            raise HTTPException(status_code=404, detail="Compartilhamento não encontrado")

        access_records = await repo.get_access_by_search(search.id)
        feedbacks = await repo.get_feedbacks_by_search(search.id)

        candidates_data = search.snapshot_payload.get("candidates", []) if search.snapshot_payload else []

        feedback_by_candidate = {}
        for f in feedbacks:
            cid = str(f.candidate_id)
            if cid not in feedback_by_candidate:
                feedback_by_candidate[cid] = []
            feedback_by_candidate[cid].append({
                "id": str(f.id),
                "candidate_id": str(f.candidate_id),
                "reviewer_email": f.reviewer_email,
                "decision": f.decision.value,
                "rating": f.rating,
                "comment": f.comment,
                "created_at": f.created_at.isoformat() if f.created_at else None
            })

        candidates_with_feedback = []
        for c in candidates_data:
            cid = c.get("id", "")
            c_feedback = feedback_by_candidate.get(cid, [])
            candidates_with_feedback.append({
                **c,
                "feedbacks": c_feedback
            })

        feedback_summary = build_feedback_summary(feedbacks, len(candidates_data))

        feedback_counts_by_email = {}
        for f in feedbacks:
            feedback_counts_by_email[f.reviewer_email] = feedback_counts_by_email.get(f.reviewer_email, 0) + 1

        recipients = [
            {
                "email": acc.email,
                "name": acc.name,
                "role": acc.role,
                "first_accessed_at": acc.first_accessed_at.isoformat() if acc.first_accessed_at else None,
                "last_accessed_at": acc.last_accessed_at.isoformat() if acc.last_accessed_at else None,
                "total_views": acc.total_views,
                "feedback_count": feedback_counts_by_email.get(acc.email, 0),
                "access_token": acc.access_token
            }
            for acc in access_records
        ]

        all_feedbacks = [
            {
                "id": str(f.id),
                "candidate_id": str(f.candidate_id),
                "reviewer_email": f.reviewer_email,
                "decision": f.decision.value,
                "rating": f.rating,
                "comment": f.comment,
                "created_at": f.created_at.isoformat() if f.created_at else None
            }
            for f in feedbacks
        ]

        return {
            "id": str(search.id),
            "company_id": str(search.company_id),
            "share_type": search.share_type.value,
            "title": search.title,
            "description": search.description,
            "status": search.status.value,
            "expires_at": search.expires_at.isoformat() if search.expires_at else None,
            "created_at": search.created_at.isoformat() if search.created_at else None,
            "candidate_count": len(candidates_data),
            "feedback_summary": feedback_summary.model_dump(),
            "recipients": recipients,
            "candidates": candidates_with_feedback,
            "feedbacks": all_feedbacks
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting shared search: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.post("/{search_id}/resend", response_model=None)
async def resend_invite(
    search_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: ResendInviteRequest,
    repo: SharedSearchRepository = Depends(get_shared_search_repo),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)):
    """
    Resend invite email with a new OTP.
    """
    try:
        company_id = get_user_company_id(current_user)
        company_uuid = parse_company_uuid(company_id)

        if not company_uuid:
            raise HTTPException(status_code=404, detail="Compartilhamento não encontrado")

        search = await repo.get_by_id_and_company(uuid.UUID(search_id), company_uuid)

        if not search:
            raise HTTPException(status_code=404, detail="Compartilhamento não encontrado")

        if search.status != SharedSearchStatus.active:
            raise HTTPException(status_code=400, detail="Compartilhamento não está ativo")

        access_record = await repo.get_access_by_email(search.id, data.email)

        if not access_record:
            raise HTTPException(status_code=404, detail="Destinatário não encontrado")

        new_otp = generate_otp()
        await repo.update_access_otp(
            access_record,
            otp_hash=hash_otp(new_otp),
            otp_expires_at=datetime.utcnow(),
        )

        return {
            "success": True,
            "message": "Convite reenviado com sucesso",
            "email": data.email,
            "otp": new_otp
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resending invite: {e}", exc_info=True)
        await repo.rollback()
        raise LIAError(message="Erro interno do servidor")


@router.patch("/{search_id}", response_model=None)
async def update_shared_search(
    search_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: UpdateSharedSearchRequest,
    repo: SharedSearchRepository = Depends(get_shared_search_repo),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)):
    """
    Update shared search (status, expires_at, description).
    """
    try:
        company_id = get_user_company_id(current_user)
        company_uuid = parse_company_uuid(company_id)

        if not company_uuid:
            raise HTTPException(status_code=404, detail="Compartilhamento não encontrado")

        search = await repo.get_by_id_and_company(uuid.UUID(search_id), company_uuid)

        if not search:
            raise HTTPException(status_code=404, detail="Compartilhamento não encontrado")

        search = await repo.update_shared_search(
            search,
            status=data.status,
            expires_at=data.expires_at,
            description=data.description,
        )

        candidates_data = search.snapshot_payload.get("candidates", []) if search.snapshot_payload else []

        return {
            "id": str(search.id),
            "company_id": str(search.company_id),
            "share_type": search.share_type.value,
            "title": search.title,
            "description": search.description,
            "status": search.status.value,
            "expires_at": search.expires_at.isoformat() if search.expires_at else None,
            "created_at": search.created_at.isoformat() if search.created_at else None,
            "updated_at": search.updated_at.isoformat() if search.updated_at else None,
            "candidate_count": len(candidates_data)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating shared search: {e}", exc_info=True)
        await repo.rollback()
        raise LIAError(message="Erro interno do servidor")


@router.delete("/{search_id}", response_model=None)
async def delete_shared_search(
    search_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    repo: SharedSearchRepository = Depends(get_shared_search_repo),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)):
    """
    Delete/revoke a shared search.
    """
    try:
        company_id = get_user_company_id(current_user)
        company_uuid = parse_company_uuid(company_id)

        if not company_uuid:
            raise HTTPException(status_code=404, detail="Compartilhamento não encontrado")

        search = await repo.get_by_id_and_company(uuid.UUID(search_id), company_uuid)

        if not search:
            raise HTTPException(status_code=404, detail="Compartilhamento não encontrado")

        await repo.revoke_shared_search(search)

        return {"success": True, "message": "Compartilhamento revogado com sucesso"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting shared search: {e}", exc_info=True)
        await repo.rollback()
        raise LIAError(message="Erro interno do servidor")


@router.post("/{search_id}/add-to-job", response_model=None)
async def add_approved_to_job(
    search_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: AddToJobRequest,
    repo: SharedSearchRepository = Depends(get_shared_search_repo),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)):
    """
    Add approved candidates from shared search to a job vacancy.
    """
    try:
        company_id = get_user_company_id(current_user)
        company_uuid = parse_company_uuid(company_id)

        if not company_uuid:
            raise HTTPException(status_code=404, detail="Compartilhamento não encontrado")

        search = await repo.get_by_id_and_company(uuid.UUID(search_id), company_uuid)

        if not search:
            raise HTTPException(status_code=404, detail="Compartilhamento não encontrado")

        approved_feedbacks = await repo.get_approved_feedbacks(search.id)

        if data.all_approved:
            candidate_ids_to_add = [f.candidate_id for f in approved_feedbacks]
        elif data.candidate_ids:
            requested_ids = set(uuid.UUID(cid) for cid in data.candidate_ids)
            approved_ids = set(f.candidate_id for f in approved_feedbacks)
            candidate_ids_to_add = list(requested_ids & approved_ids)
        else:
            raise HTTPException(status_code=400, detail="Especifique candidate_ids ou all_approved=true")

        if not candidate_ids_to_add:
            return {
                "success": True,
                "added": 0,
                "already_in_job": 0,
                "message": "Nenhum candidato aprovado para adicionar"
            }

        job_uuid = uuid.UUID(data.job_id)
        added_count = 0
        already_in_job = 0

        feedback_comments = {}
        if data.include_notes:
            for f in approved_feedbacks:
                if f.comment:
                    feedback_comments[f.candidate_id] = f.comment

        for candidate_id in candidate_ids_to_add:
            existing = await repo.get_vacancy_candidate(job_uuid, candidate_id)

            if existing:
                already_in_job += 1
                continue

            notes = feedback_comments.get(candidate_id) if data.include_notes else None

            # Task #1306: record the structural stage link so SLA detection can
            # join by id instead of fragile name matching.
            from app.shared.services.stage_id_resolver import (
from app.shared.errors import LIAError
                resolve_recruitment_stage_id,
            )

            recruitment_stage_id = await resolve_recruitment_stage_id(
                repo.db, str(company_uuid), "sourcing"
            )

            new_vacancy_candidate = VacancyCandidate(
                id=uuid.uuid4(),
                company_id=company_uuid,
                vacancy_id=job_uuid,
                candidate_id=candidate_id,
                stage="sourcing",
                recruitment_stage_id=recruitment_stage_id,
                status="sourced",
                source="shared_search",
                notes=notes,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            await repo.create_vacancy_candidate(new_vacancy_candidate)
            added_count += 1

        await repo.commit()

        return {
            "success": True,
            "added": added_count,
            "already_in_job": already_in_job,
            "job_id": data.job_id,
            "total_approved": len(candidate_ids_to_add)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding candidates to job: {e}", exc_info=True)
        await repo.rollback()
        raise LIAError(message="Erro interno do servidor")

reorder_collection_before_item(router)
