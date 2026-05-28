"""
Public Shared Searches API endpoints.

Public endpoints for hiring managers/guests to access shared candidate searches.
NO JWT authentication required - uses unique token + OTP verification.

Security:
- Unique access token validation per recipient
- OTP verification (6 digits, 10 min expiry)
- Session token for authenticated access (24 hour expiry)
"""
import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta
from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_tenant_db
from app.domains.shared_searches.repositories.shared_search_repository import SharedSearchRepository
from app.middleware.rate_limiter import rate_limiter as _otp_rate_limiter
from app.models.shared_search import (
    FeedbackDecision,
    SharedSearch,
    SharedSearchAccess,
    SharedSearchFeedback,
    SharedSearchStatus,
)
from app.schemas.shared_search import (
    CandidateSnapshot,
    FeedbackResponse,
    OTPResponse,
    PublicSharedSearchResponse,
    RequestOTPRequest,
    SessionResponse,
    SubmitFeedbackRequest,
    VerifyOTPRequest,
)
from app.schemas.shared_search import FeedbackDecision as SchemaFeedbackDecision
from app.services.notification_service import NotificationType, notification_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public/shared", tags=["Public Shared Searches"])


def get_shared_search_repo(db: AsyncSession = Depends(get_db)) -> SharedSearchRepository:
    return SharedSearchRepository(db)

OTP_EXPIRY_MINUTES = 10
SESSION_EXPIRY_HOURS = 24
MAX_OTP_VERIFY_ATTEMPTS = 10  # DB-backed hard cap per OTP issuance
MAX_OTP_REQUEST_PER_WINDOW = 5  # Redis sliding-window cap (900 s)

def get_jwt_secret() -> str:
    """Get JWT secret with production safety check."""
    secret = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY") or os.getenv("SESSION_SECRET")
    if secret:
        return secret
    env = os.getenv("ENV", "development").lower()
    if env in ("production", "prod"):
        raise RuntimeError("JWT_SECRET, SECRET_KEY, or SESSION_SECRET must be set in production")
    return "shared-search-dev-only-secret-key"

JWT_SECRET = get_jwt_secret()
JWT_ALGORITHM = "HS256"


def generate_otp() -> str:
    """Generate a 6-digit OTP."""
    return f"{secrets.randbelow(1000000):06d}"


def hash_otp(otp: str) -> str:
    """Hash OTP for storage."""
    return hashlib.sha256(otp.encode()).hexdigest()


def verify_otp_hash(otp: str, otp_hash: str) -> bool:
    """Verify OTP against stored hash."""
    return secrets.compare_digest(hash_otp(otp), otp_hash)


def create_session_token(email: str, shared_search_id: str, access_id: str) -> tuple[str, datetime]:
    """Create a session token (JWT) for authenticated access."""
    expires_at = datetime.utcnow() + timedelta(hours=SESSION_EXPIRY_HOURS)
    payload = {
        "email": email,
        "shared_search_id": shared_search_id,
        "access_id": access_id,
        "exp": expires_at,
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, expires_at


def decode_session_token(token: str) -> dict | None:
    """Decode and validate a session token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


async def get_shared_search_by_token(
    token: str,
    db: AsyncSession
) -> tuple[SharedSearch, SharedSearchAccess]:
    """Get shared search and access record by access token."""
    repo = SharedSearchRepository(db)
    access = await repo.get_access_by_token(token)
    
    if not access:
        raise HTTPException(status_code=404, detail="Link de compartilhamento não encontrado")
    
    search = await repo.get_shared_search_by_id(access.shared_search_id)
    
    if not search:
        raise HTTPException(status_code=404, detail="Busca compartilhada não encontrada")
    
    if search.status == SharedSearchStatus.revoked:
        raise HTTPException(status_code=410, detail="Este link foi revogado")
    
    if search.expires_at and search.expires_at < datetime.utcnow():
        if search.status != SharedSearchStatus.expired:
            search.status = SharedSearchStatus.expired
        raise HTTPException(status_code=410, detail="Este link expirou")
    
    return search, access


async def get_session_from_header(
    authorization: str | None = Header(None, alias="X-Session-Token"),
    db: AsyncSession = Depends(get_db)
) -> dict | None:
    """Extract and validate session from header."""
    if not authorization:
        return None
    
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    payload = decode_session_token(token)
    
    if not payload:
        return None
    
    return payload


async def require_session(
    authorization: str | None = Header(None, alias="X-Session-Token"),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Require valid session token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Token de sessão necessário")
    
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    payload = decode_session_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada")
    
    return payload


def build_candidate_snapshots(
    snapshot_data: list[dict],
    limit: int | None = None,
    include_sensitive: bool = True,
) -> list[CandidateSnapshot]:
    """Build candidate snapshot objects from raw data.

    Args:
        snapshot_data: Raw candidate dicts from the snapshot payload.
        limit: If set, only the first *limit* candidates are returned.
        include_sensitive: When False, ``linkedin_url`` and ``resume_url`` are
            stripped.  Pass False for unauthenticated (pre-OTP) previews so
            that candidate artifact URLs are not disclosed before the reviewer
            has proven control of the recipient e-mail address.
    """
    candidates = snapshot_data[:limit] if limit else snapshot_data
    result = []

    for c in candidates:
        result.append(CandidateSnapshot(
            id=UUID(c.get("id")) if c.get("id") else None,
            name=c.get("name", ""),
            title=c.get("title"),
            company=c.get("company"),
            location=c.get("location"),
            experience_years=c.get("experience_years"),
            skills=c.get("skills", []),
            wsi_score=c.get("wsi_score"),
            linkedin_url=c.get("linkedin_url") if include_sensitive else None,
            resume_url=c.get("resume_url") if include_sensitive else None,
            feedback=None
        ))

    return result


@router.get("/{token}", response_model=None)
async def get_public_shared_search(
    token: str,
    db: AsyncSession = Depends(get_db),
    session: dict | None = Depends(get_session_from_header)
) -> PublicSharedSearchResponse:
    """
    Get public shared search preview.
    
    - Without valid session: Returns limited preview (first 5 candidates)
    - With valid session: Returns full candidate data
    """
    search, access = await get_shared_search_by_token(token, db)
    
    snapshot_payload = search.snapshot_payload or {}
    all_candidates = snapshot_payload.get("candidates", [])
    
    is_authenticated = session is not None and session.get("shared_search_id") == str(search.id)
    
    if is_authenticated:
        candidates = build_candidate_snapshots(all_candidates, include_sensitive=True)

        repo = SharedSearchRepository(db)
        feedbacks = await repo.get_feedbacks_by_search_and_reviewer(
            search.id, session.get("email")
        )
        feedback_map = {str(f.candidate_id): f for f in feedbacks}

        for candidate in candidates:
            if str(candidate.id) in feedback_map:
                f = feedback_map[str(candidate.id)]
                candidate.feedback = FeedbackResponse(
                    id=f.id,
                    candidate_id=f.candidate_id,
                    reviewer_email=f.reviewer_email,
                    decision=SchemaFeedbackDecision(f.decision.value),
                    rating=f.rating,
                    comment=f.comment,
                    created_at=f.created_at
                )
    else:
        # Strip sensitive artifact URLs (linkedin_url, resume_url) from the
        # unauthenticated preview — the OTP gate must be passed before those
        # fields are disclosed.
        candidates = build_candidate_snapshots(all_candidates, limit=5, include_sensitive=False)
    
    return PublicSharedSearchResponse(
        title=search.title,
        description=search.description,
        expires_at=search.expires_at,
        shared_by_name=None,
        shared_by_email=None,
        company_name=None,
        company_logo_url=None,
        candidate_count=len(all_candidates),
        candidates=candidates,
        can_comment=getattr(search, 'can_comment', True),
        can_rate=getattr(search, 'can_rate', True)
    )


@router.post("/{token}/request-otp", response_model=None)
async def request_otp(
    token: str,
    request_data: RequestOTPRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> OTPResponse:
    """
    Request OTP for a specific email.

    - Verify email is in SharedSearchAccess for this token
    - Generate 6-digit OTP, hash and store it
    - OTP expires in 10 minutes
    - Rate limited: 5 requests per 15 minutes per token (anti-brute-force)
    - Fails CLOSED when Redis is unavailable to prevent unlimited OTP generation
    """
    # Rate limit: 5 OTP requests per 15 minutes per token.
    # Fail CLOSED: if Redis is unavailable we cannot enforce the sliding-window,
    # so we return 503 rather than silently allow unlimited OTP generation.
    rl_key = f"otp_rl:req:{token}"
    try:
        r = await _otp_rate_limiter._get_redis()
        if r is None:
            logger.warning("Redis unavailable; refusing OTP request to prevent rate-limit bypass")
            raise HTTPException(
                status_code=503,
                detail="Serviço temporariamente indisponível. Tente novamente em instantes.",
            )
        allowed, _count = await _otp_rate_limiter._redis_sliding_window(rl_key, MAX_OTP_REQUEST_PER_WINDOW, 900)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Muitas tentativas. Aguarde 15 minutos antes de solicitar um novo código.",
                headers={"Retry-After": "900"},
            )
    except HTTPException:
        raise
    except Exception:
        logger.warning("Rate-limiter error on OTP request; failing closed", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Serviço temporariamente indisponível. Tente novamente em instantes.",
        )

    search, access = await get_shared_search_by_token(token, db)

    if access.email.lower() != request_data.email.lower():
        repo = SharedSearchRepository(db)
        access = await repo.get_access_by_email(search.id, request_data.email)

        if not access:
            raise HTTPException(
                status_code=403,
                detail="Este e-mail não tem permissão para acessar esta busca"
            )

    otp = generate_otp()
    access.otp_hash = hash_otp(otp)
    access.otp_expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)
    # Reset the DB-backed attempt counter whenever a fresh OTP is issued so the
    # new code starts with a clean slate.
    access.otp_attempts = 0

    _email_hash = hashlib.sha256(request_data.email.lower().encode()).hexdigest()[:8]
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"OTP generated for email_hash={_email_hash} on shared_search={search.id}")

    return OTPResponse(
        success=True,
        message=f"Código de verificação enviado para {request_data.email}"
    )


@router.post("/{token}/verify-otp", response_model=None)
async def verify_otp(
    token: str,
    request_data: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db)
) -> SessionResponse:
    """
    Verify OTP and generate session token.

    - Verify OTP matches and not expired
    - Generate session token (JWT)
    - Update access timestamps and view count
    - Rate limited: Redis sliding-window (primary) + DB-backed attempt counter
      (always-on fallback so Redis outages cannot be used to bypass brute-force
      protection)
    """
    # Resolve the access record early so we can apply the DB-backed counter
    # before touching any Redis-dependent logic.
    search, access = await get_shared_search_by_token(token, db)

    if access.email.lower() != request_data.email.lower():
        repo = SharedSearchRepository(db)
        access = await repo.get_access_by_email(search.id, request_data.email)

        if not access:
            raise HTTPException(
                status_code=403,
                detail="Este e-mail não tem permissão para acessar esta busca"
            )

    # DB-backed hard cap — enforced regardless of Redis availability.
    # otp_attempts is reset to 0 whenever a fresh OTP is issued via request_otp,
    # so the counter tracks guesses against the current OTP only.
    current_attempts = access.otp_attempts or 0
    if current_attempts >= MAX_OTP_VERIFY_ATTEMPTS:
        logger.warning(
            f"OTP attempt cap reached (db_attempts={current_attempts}) "
            f"for shared_search={search.id}"
        )
        raise HTTPException(
            status_code=429,
            detail="Muitas tentativas de verificação. Solicite um novo código.",
            headers={"Retry-After": "900"},
        )

    # Redis sliding-window (primary limiter — best-effort; the DB cap above
    # guarantees enforcement even when Redis is down).
    rl_key = f"otp_rl:verify:{token}"
    try:
        r = await _otp_rate_limiter._get_redis()
        if r is not None:
            allowed, _count = await _otp_rate_limiter._redis_sliding_window(rl_key, MAX_OTP_VERIFY_ATTEMPTS, 900)
            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail="Muitas tentativas de verificação. Aguarde 15 minutos.",
                    headers={"Retry-After": "900"},
                )
    except HTTPException:
        raise
    except Exception:
        # Redis error: the DB cap above already guards against brute-force, so
        # we log and continue rather than serving a 503 to the legitimate user.
        logger.warning("Rate-limiter error on OTP verify; DB cap still active", exc_info=True)

    # Increment the DB counter and commit it BEFORE running checks that can
    # raise HTTPException.  FastAPI/SQLAlchemy roll back any uncommitted
    # changes when an HTTPException propagates, so the increment must be
    # durable before we validate the code.  This guarantees that failed
    # guesses are counted even during Redis outages.
    access.otp_attempts = current_attempts + 1
    try:
        await db.commit()
        # Refresh is required: SQLAlchemy expires all attributes after commit,
        # and subsequent attribute access on an async session raises
        # MissingGreenlet if lazy-loading is attempted.
        await db.refresh(access)
    except Exception:
        logger.exception("Failed to persist otp_attempts increment; aborting verify to fail closed")
        raise HTTPException(
            status_code=503,
            detail="Serviço temporariamente indisponível. Tente novamente em instantes.",
        )

    if not access.otp_hash:
        raise HTTPException(
            status_code=400,
            detail="Nenhum código OTP foi solicitado. Solicite um novo código."
        )

    if not access.otp_expires_at or access.otp_expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="Código OTP expirado. Solicite um novo código."
        )

    if not verify_otp_hash(request_data.otp, access.otp_hash):
        raise HTTPException(
            status_code=400,
            detail="Código OTP incorreto"
        )

    # Successful verification: clear the OTP and reset the attempt counter.
    access.otp_hash = None
    access.otp_expires_at = None
    access.otp_attempts = 0

    now = datetime.utcnow()
    if not access.first_accessed_at:
        access.first_accessed_at = now
    access.last_accessed_at = now
    access.total_views = (access.total_views or 0) + 1

    session_token, expires_at = create_session_token(
        email=access.email,
        shared_search_id=str(search.id),
        access_id=str(access.id)
    )

    _email_hash = hashlib.sha256(request_data.email.lower().encode()).hexdigest()[:8]
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"OTP verified for email_hash={_email_hash} on shared_search={search.id}")

    return SessionResponse(
        access_token=session_token,
        expires_at=expires_at
    )


@router.post("/{token}/feedback", response_model=None)
async def submit_feedback(
    token: str,
    request_data: SubmitFeedbackRequest,
    db: AsyncSession = Depends(get_tenant_db),
    session: dict = Depends(require_session)
) -> FeedbackResponse:
    """
    Submit feedback on a candidate.
    
    - Requires valid session token
    - Create or update SharedSearchFeedback record
    """
    search, access = await get_shared_search_by_token(token, db)
    
    if session.get("shared_search_id") != str(search.id):
        raise HTTPException(status_code=403, detail="Sessão inválida para esta busca")
    
    if not getattr(search, 'can_rate', True):
        raise HTTPException(
            status_code=403,
            detail="O recrutador desativou avaliações para este compartilhamento"
        )
    
    if request_data.comment and not getattr(search, 'can_comment', True):
        raise HTTPException(
            status_code=403,
            detail="O recrutador desativou comentários para este compartilhamento"
        )
    
    reviewer_email = session.get("email")
    
    snapshot_payload = search.snapshot_payload or {}
    all_candidates = snapshot_payload.get("candidates", [])
    candidate_ids = [c.get("id") for c in all_candidates]
    
    if str(request_data.candidate_id) not in candidate_ids:
        raise HTTPException(status_code=404, detail="Candidato não encontrado nesta busca")
    
    repo = SharedSearchRepository(db)
    existing = await repo.get_feedback_by_candidate_and_reviewer(
        search.id, request_data.candidate_id, reviewer_email
    )
    
    now = datetime.utcnow()
    
    if existing:
        existing.decision = FeedbackDecision(request_data.decision.value)
        existing.rating = request_data.rating
        existing.comment = request_data.comment
        existing.updated_at = now
        feedback = existing
        await db.flush()
        await db.refresh(feedback)
    else:
        import uuid
        feedback = await repo.create_feedback(SharedSearchFeedback(
            id=uuid.uuid4(),
            shared_search_id=search.id,
            candidate_id=request_data.candidate_id,
            reviewer_email=reviewer_email,
            decision=FeedbackDecision(request_data.decision.value),
            rating=request_data.rating,
            comment=request_data.comment,
            created_at=now,
            updated_at=now,
        ))

    _reviewer_hash = hashlib.sha256(reviewer_email.lower().encode()).hexdigest()[:8] if reviewer_email else "unknown"
    logger.info(f"Feedback submitted by email_hash={_reviewer_hash} for candidate={request_data.candidate_id} on shared_search={search.id}")

    # Notificar recrutor que criou o compartilhamento (H.3c)
    if search.created_by_user_id:
        try:
            await notification_service.create_notification(
                user_id=str(search.created_by_user_id),
                title="Avaliação recebida",
                message=(
                    f"Gestor {reviewer_email} avaliou candidatos da shortlist "
                    f"'{search.title}'"
                ),
                notification_type=NotificationType.INFO,
                category="shortlist_feedback",
                action_url="/funil-de-talentos",
                channels=["bell"],
                db=db,
            )
        except Exception as notify_err:
            logger.warning(
                f"Failed to send feedback notification for shared_search {search.id}: {notify_err}"
            )

    return FeedbackResponse(
        id=feedback.id,
        candidate_id=feedback.candidate_id,
        reviewer_email=feedback.reviewer_email,
        decision=SchemaFeedbackDecision(feedback.decision.value),
        rating=feedback.rating,
        comment=feedback.comment,
        created_at=feedback.created_at
    )


@router.get("/{token}/my-feedbacks", response_model=None)
async def get_my_feedbacks(
    token: str,
    db: AsyncSession = Depends(get_db),
    session: dict = Depends(require_session)
) -> list[FeedbackResponse]:
    """
    Get all feedbacks submitted by the current user.
    
    - Requires valid session token
    """
    search, access = await get_shared_search_by_token(token, db)
    
    if session.get("shared_search_id") != str(search.id):
        raise HTTPException(status_code=403, detail="Sessão inválida para esta busca")
    
    reviewer_email = session.get("email")
    
    repo = SharedSearchRepository(db)
    feedbacks = await repo.get_feedbacks_by_reviewer(search.id, reviewer_email)
    
    return [
        FeedbackResponse(
            id=f.id,
            candidate_id=f.candidate_id,
            reviewer_email=f.reviewer_email,
            decision=SchemaFeedbackDecision(f.decision.value),
            rating=f.rating,
            comment=f.comment,
            created_at=f.created_at
        )
        for f in feedbacks
    ]
