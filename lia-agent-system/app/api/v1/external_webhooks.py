"""
External Webhooks API.

Receives events from:
- ATS platforms (Gupy, Pandapé, Merge)
- Other external integrations
"""
import hashlib
import hmac
import logging
import os
import secrets
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, ValidationError

from app.domains.automation.services.webhook_adapters import (
    DocumentWebhookAdapter,
    InterviewWebhookAdapter,
    TestWebhookAdapter,
    WebhookAdapter,
)

from app.domains.ats_integration.services.ats_sync_service import ATSSyncService, get_ats_sync_service
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/external-webhooks", tags=["external-webhooks"])

# P1-W3-02: Bearer token estático para webhooks interview/test/document.
# Configurar EXTERNAL_WEBHOOK_SECRET_TOKEN com valor opaco ≥ 32 chars.
# TODO Task #1147: migrar pra verify_webhook_owner canonical com per-tenant HMAC
# quando os provedores (calendly, testgorilla, etc.) tiverem webhook secrets configuráveis.
# TODO Task #1148: IP allowlist (cloudflare / provider CIDR) seria a defesa ideal
# para providers com IP fixo, mas não está implementada — bearer token é o gate atual.
_EXTERNAL_WEBHOOK_SECRET_TOKEN = os.getenv("EXTERNAL_WEBHOOK_SECRET_TOKEN", "")


def _verify_external_webhook_bearer(authorization: str | None, provider: str) -> None:
    """Verify EXTERNAL_WEBHOOK_SECRET_TOKEN bearer token.

    P1-W3-02: gate obrigatório para interview/test/document webhooks enquanto
    a migração para verify_webhook_owner canonical (Task #1147) não é concluída.
    Fail-loud: 401 se token ausente/inválido. Fail-loud: 500 se env var não configurada
    (impede deploy silencioso sem proteção).
    """
    if not _EXTERNAL_WEBHOOK_SECRET_TOKEN:
        logger.error(
            "[WEBHOOK] P1-W3-02: EXTERNAL_WEBHOOK_SECRET_TOKEN não configurado — "
            "provider=%s rejeitado. Configure a env var para habilitar este endpoint.",
            provider,
        )
        raise HTTPException(
            status_code=503,
            detail=(
                "Webhook endpoint temporariamente indisponível: "
                "EXTERNAL_WEBHOOK_SECRET_TOKEN não configurado no servidor. "
                "Contate o administrador."
            ),
        )
    token = (authorization or "").removeprefix("Bearer ").strip()
    if not token or not secrets.compare_digest(token, _EXTERNAL_WEBHOOK_SECRET_TOKEN):
        logger.warning(
            "[WEBHOOK] P1-W3-02: bearer token inválido ou ausente — provider=%s 401",
            provider,
        )
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Authorization: Bearer <token> inválido ou ausente",
        )


def is_webhook_adapter_enabled(provider: str) -> bool:
    flag = os.getenv(f"ENABLE_WEBHOOK_{provider.upper()}", "true")
    return flag.lower() == "true"


class ATSWebhookEvent(BaseModel):
    """ATS webhook event payload."""
    event_type: str
    ats_candidate_id: str
    ats_vacancy_id: str | None = None
    new_stage: str | None = None
    previous_stage: str | None = None
    candidate_data: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


def verify_webhook_signature(payload: bytes, signature: str, secret: str, platform: str = "unknown") -> bool:
    """
    Verify webhook signature using HMAC-SHA256.
    
    Args:
        payload: Raw request body bytes
        signature: Signature from header
        secret: Webhook secret
        platform: Platform name for logging
        
    Returns:
        True if signature is valid
    """
    if not secret:
        logger.warning(f"[WEBHOOK] No secret configured for {platform}, rejecting request for security")
        return False
    
    try:
        expected = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature.replace("sha256=", ""))
    except Exception as e:
        logger.error(f"❌ Signature verification error: {e}")
        return False


@router.post("/ats/{platform}", response_model=None)
async def handle_ats_webhook(
    platform: str,
    request: Request,
    background_tasks: BackgroundTasks,
    x_webhook_signature: str | None = Header(None, alias="X-Webhook-Signature"),
    x_gupy_signature: str | None = Header(None, alias="X-Gupy-Signature"),
    x_pandape_signature: str | None = Header(None, alias="X-Pandape-Signature"),
    x_merge_signature: str | None = Header(None, alias="X-Merge-Signature"),
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Receive webhook from ATS platforms (Gupy, Pandapé, Merge).
    Used for inbound sync when changes happen in external ATS.
    
    Supported platforms:
    - gupy: Gupy ATS
    - pandape: Pandapé ATS
    - merge: Merge.dev unified ATS API
    
    Events:
    - candidate_created: New candidate in ATS
    - candidate_updated: Candidate data changed
    - stage_changed: Candidate moved to new stage
    - candidate_hired: Candidate was hired
    - candidate_rejected: Candidate was rejected
    """
    platform_lower = platform.lower()
    
    if platform_lower not in ["gupy", "pandape", "merge"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported ATS platform: {platform}"
        )
    
    raw_body = await request.body()
    
    signature = (
        x_gupy_signature if platform_lower == "gupy"
        else x_pandape_signature if platform_lower == "pandape"
        else x_merge_signature if platform_lower == "merge"
        else x_webhook_signature
    )
    
    secret_env_key = f"{platform.upper()}_WEBHOOK_SECRET"
    secret = os.getenv(secret_env_key)
    
    if not verify_webhook_signature(raw_body, signature or "", secret or "", platform_lower):
        logger.error(f"❌ Invalid or missing webhook signature for {platform}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature or secret not configured"
        )
    
    try:
        raw_payload = await request.json()
    except Exception as e:
        logger.error("Failed to parse webhook payload: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )

    # Validate against typed model where fields match; fall back to raw dict for flexible ATS schemas
    try:
        ats_event = ATSWebhookEvent.model_validate(raw_payload)
        event_type = ats_event.event_type
        candidate_id = ats_event.ats_candidate_id
        payload = raw_payload  # keep raw dict for background tasks that access extra fields
    except ValidationError:
        # ATS payloads often have platform-specific field names — fall back gracefully
        payload = raw_payload
        event_type = payload.get("event_type") or payload.get("event") or payload.get("type", "unknown")
        candidate_id = (
            payload.get("ats_candidate_id") or
            payload.get("candidate_id") or
            payload.get("candidateId") or
            payload.get("data", {}).get("candidate_id")
        )
    
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[WEBHOOK] ATS {platform} event: {event_type} for candidate {candidate_id}")
    
    if event_type in ["candidate_updated", "candidate.updated"]:
        background_tasks.add_task(
            process_ats_candidate_updated,
            platform_lower,
            payload
        )
    elif event_type in ["stage_changed", "stage.changed", "candidate_moved"]:
        background_tasks.add_task(
            process_ats_stage_changed,
            platform_lower,
            payload
        )
    elif event_type in ["candidate_created", "candidate.created"]:
        background_tasks.add_task(
            process_ats_candidate_created,
            platform_lower,
            payload
        )
    elif event_type in ["candidate_hired", "candidate.hired"]:
        background_tasks.add_task(
            process_ats_candidate_hired,
            platform_lower,
            payload
        )
    elif event_type in ["candidate_rejected", "candidate.rejected"]:
        background_tasks.add_task(
            process_ats_candidate_rejected,
            platform_lower,
            payload
        )
    else:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.warning(f"[WEBHOOK] Unknown ATS event type: {event_type}")
    
    return {
        "status": "received",
        "platform": platform_lower,
        "event_type": event_type,
        "candidate_id": candidate_id
    }


async def process_ats_candidate_updated(platform: str, payload: dict[str, Any]):
    """Sync candidate data from ATS to LIA."""
    try:
        sync_service = get_ats_sync_service()
        
        candidate_id = (
            payload.get("ats_candidate_id") or 
            payload.get("candidate_id") or 
            payload.get("candidateId")
        )
        
        logger.info(f"[ATS SYNC] Processing candidate update from {platform}: {candidate_id}")
        
        result = await sync_service.pull_candidate(
            ats_type=platform,
            ats_candidate_id=candidate_id,
            source_agent="external_webhook"
        )
        
        logger.info(f"[ATS SYNC] Candidate update processed: {result}")
    except Exception as e:
        logger.error(f"❌ Error processing ATS candidate update: {e}", exc_info=True)


async def process_ats_stage_changed(platform: str, payload: dict[str, Any]):
    """Sync stage change from ATS to LIA (inbound sync)."""
    try:
        candidate_id = (
            payload.get("ats_candidate_id") or 
            payload.get("candidate_id") or
            payload.get("candidateId")
        )
        new_stage = payload.get("new_stage") or payload.get("stage") or payload.get("data", {}).get("stage")
        previous_stage = payload.get("previous_stage") or payload.get("old_stage")
        
        logger.info(f"[ATS SYNC] Stage change from {platform}: {candidate_id} -> {new_stage}")
        
        sync_service = get_ats_sync_service()
        result = await sync_service.sync_stage_from_ats(
            ats_type=platform,
            ats_candidate_id=candidate_id,
            new_stage=new_stage,
            previous_stage=previous_stage
        )
        
        logger.info(f"[ATS SYNC] Stage change processed: {result}")
    except Exception as e:
        logger.error(f"❌ Error processing ATS stage change: {e}", exc_info=True)


async def process_ats_candidate_created(platform: str, payload: dict[str, Any]):
    """Handle new candidate created in ATS.

    P2-W3-INT-1: esta funcao era dead code — linha payload.get() sem efeito + apenas log.
    TODO: implementar importacao real de candidato via ATS sync service (veja process_ats_stage_changed
    como modelo). Ate la, o evento e recebido mas descartado com log estruturado.
    Ticket: WT-backlog ATS candidate sync.
    """
    try:
        candidate_data = payload.get("candidate_data") or payload.get("data", {})
        logger.info(
            "[ATS SYNC] candidate_created recebido de %s — importacao pendente (P2-W3-INT-1 TODO)",
            platform,
            extra={"platform": platform, "candidate_keys": list(candidate_data.keys()) if candidate_data else []},
        )
    except Exception as e:
        logger.error(f"❌ Error processing ATS candidate created: {e}", exc_info=True)


async def process_ats_candidate_hired(platform: str, payload: dict[str, Any]):
    """Handle candidate hired in ATS.

    T-10 Fase 5: wire HIRED_EXTERNAL outcome canonical (ADR-032).
    Pipeline canonical pós-Fase 5: 6/6 outcomes wired (100% coverage).
    """
    try:
        from app.domains.analytics.services.activity_service import activity_service

        candidate_id = (
            payload.get("ats_candidate_id") or
            payload.get("candidate_id")
        )

        logger.info(f"[ATS SYNC] Candidate hired in {platform}: {candidate_id}")

        await activity_service.log_activity(
            action="candidate_hired_ats",
            entity_type="candidate",
            entity_id=candidate_id,
            details={
                "source": f"{platform}_webhook",
                "ats_platform": platform
            }
        )

        # T-10 Fase 5 WIRE canonical (ADR-032): HIRED_EXTERNAL outcome learning loop.
        # Fail-soft via helper canonical (wire_feedback_outcome nunca raises).
        # Resolves company_id + job_id best-effort from payload — skip se ausentes.
        # Onda 4.2e-P0-12 (2026-05-23): payload company_id documentado como
        # untrusted (vem do webhook ATS externo). Idealmente derivar via
        # mapeamento secret→tenant (Task #1146 verify_webhook_owner pattern).
        # Por enquanto mantido como best-effort fail-soft (skip se ausente
        # OU se inconsistente com config local — TODO sensor).
        _company_id = payload.get("company_id") or payload.get("tenant_id")
        _job_id = (
            payload.get("vacancy_id")
            or payload.get("job_id")
            or payload.get("position_id")
        )
        if _company_id and _job_id:
            try:
                from app.shared.learning.feedback_writer import wire_feedback_outcome
                from lia_config.database import AsyncSessionLocal

                async with AsyncSessionLocal() as _db:
                    await wire_feedback_outcome(
                        db=_db,
                        domain="ats_integration",
                        outcome_type="HIRED_EXTERNAL",
                        company_id=str(_company_id),
                        job_id=str(_job_id),
                        context={
                            "ats_platform": platform,
                            "ats_candidate_id": candidate_id,
                            "wire_source": "external_webhooks.process_ats_candidate_hired",
                        },
                    )
            except Exception as _wire_exc:
                logger.warning(
                    "[ATS SYNC T-10 Fase 5] wire_feedback_outcome failed (non-blocking): %s",
                    str(_wire_exc)[:200],
                )
        else:
            logger.debug(
                "[ATS SYNC T-10 Fase 5] skip wire — missing company_id (%s) or job_id (%s)",
                _company_id, _job_id,
            )
    except Exception as e:
        logger.error(f"❌ Error processing ATS candidate hired: {e}", exc_info=True)


async def process_ats_candidate_rejected(platform: str, payload: dict[str, Any]):
    """Handle candidate rejected in ATS.

    T-10 Fase 5 WIRE canonical (ADR-032): REJECTED outcome learning loop.
    Pattern alinhado com process_ats_candidate_hired wire (same fail-soft logic).
    """
    try:
        candidate_id = (
            payload.get("ats_candidate_id") or
            payload.get("candidate_id")
        )
        rejection_reason = payload.get("rejection_reason") or payload.get("reason")

        logger.info(f"[ATS SYNC] Candidate rejected in {platform}: {candidate_id}")

        # T-10 Fase 5 WIRE canonical: REJECTED outcome via ats_integration domain.
        # Onda 4.2e-P0-12 (2026-05-23): payload company_id documentado como
        # untrusted (vem do webhook ATS externo). Idealmente derivar via
        # mapeamento secret→tenant (Task #1146 verify_webhook_owner pattern).
        # Por enquanto mantido como best-effort fail-soft (skip se ausente
        # OU se inconsistente com config local — TODO sensor).
        _company_id = payload.get("company_id") or payload.get("tenant_id")
        _job_id = (
            payload.get("vacancy_id")
            or payload.get("job_id")
            or payload.get("position_id")
        )
        if _company_id and _job_id:
            try:
                from app.shared.learning.feedback_writer import wire_feedback_outcome
                from lia_config.database import AsyncSessionLocal

                async with AsyncSessionLocal() as _db:
                    await wire_feedback_outcome(
                        db=_db,
                        domain="ats_integration",
                        outcome_type="REJECTED",
                        company_id=str(_company_id),
                        job_id=str(_job_id),
                        context={
                            "ats_platform": platform,
                            "ats_candidate_id": candidate_id,
                            "rejection_reason": rejection_reason,
                            "wire_source": "external_webhooks.process_ats_candidate_rejected",
                        },
                    )
            except Exception as _wire_exc:
                logger.warning(
                    "[ATS SYNC T-10 Fase 5] wire_feedback_outcome failed (non-blocking): %s",
                    str(_wire_exc)[:200],
                )
    except Exception as e:
        logger.error(f"❌ Error processing ATS candidate rejected: {e}", exc_info=True)


@router.post("/interview/{provider}", response_model=None)
async def handle_interview_webhook(
    provider: str,
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str | None = Header(None, alias="Authorization"),
    company_id: str = Depends(require_company_id),
):
    """Receive webhook from interview scheduling tools (calendly, custom).

    Onda 4.2e-P0-9 (2026-05-23): adicionado require_company_id.
    P1-W3-02 (2026-05-24): adicionado bearer token gate via
    EXTERNAL_WEBHOOK_SECRET_TOKEN. Antes era endpoint com apenas JWT
    (qualquer usuário autenticado podia spoofar eventos de entrevista).
    TODO Task #1147: migrar pra verify_webhook_owner canonical (per-tenant HMAC).
    TODO Task #1148: IP allowlist para providers com IP fixo (defesa ideal).
    """
    _verify_external_webhook_bearer(authorization, provider=f"interview/{provider}")

    if not is_webhook_adapter_enabled(f"interview_{provider}"):
        return {"status": "disabled", "provider": provider}

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_id = payload.get("event_id") or payload.get("id") or str(uuid.uuid4())
    event_type = payload.get("event_type") or payload.get("type") or "interview_confirmed"

    result = await InterviewWebhookAdapter.process(event_id, event_type, payload)
    return result


@router.post("/test/{provider}", response_model=None)
async def handle_test_webhook(
    provider: str,
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str | None = Header(None, alias="Authorization"),
    company_id: str = Depends(require_company_id),
):
    """Receive webhook from assessment/test platforms (testgorilla, codility, custom).

    Onda 4.2e-P0-10 (2026-05-23): adicionado require_company_id.
    P1-W3-02 (2026-05-24): adicionado bearer token gate via
    EXTERNAL_WEBHOOK_SECRET_TOKEN. Antes era endpoint com apenas JWT
    (atacante com JWT válido injetava resultados de teste falsos).
    TODO Task #1147: migrar pra verify_webhook_owner canonical.
    TODO Task #1148: IP allowlist para providers com IP fixo.
    """
    _verify_external_webhook_bearer(authorization, provider=f"test/{provider}")

    if not is_webhook_adapter_enabled(f"test_{provider}"):
        return {"status": "disabled", "provider": provider}

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_id = payload.get("event_id") or payload.get("id") or str(uuid.uuid4())
    event_type = payload.get("event_type") or payload.get("type") or "test_completed"

    result = await TestWebhookAdapter.process(event_id, event_type, payload)
    return result


@router.post("/document/{provider}", response_model=None)
async def handle_document_webhook(
    provider: str,
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str | None = Header(None, alias="Authorization"),
    company_id: str = Depends(require_company_id),
):
    """Receive webhook from document collection services.

    Onda 4.2e-P0-11 (2026-05-23): adicionado require_company_id.
    P1-W3-02 (2026-05-24): adicionado bearer token gate via
    EXTERNAL_WEBHOOK_SECRET_TOKEN. LGPD Art. 38 (uso indevido de
    declaracao de documentacao).
    TODO Task #1147: migrar pra verify_webhook_owner canonical.
    TODO Task #1148: IP allowlist para providers com IP fixo.
    """
    _verify_external_webhook_bearer(authorization, provider=f"document/{provider}")

    if not is_webhook_adapter_enabled(f"document_{provider}"):
        return {"status": "disabled", "provider": provider}

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_id = payload.get("event_id") or payload.get("id") or str(uuid.uuid4())
    event_type = payload.get("event_type") or payload.get("type") or "document_submitted"

    result = await DocumentWebhookAdapter.process(event_id, event_type, payload)
    return result


@router.get("/event-log", response_model=None)
async def get_webhook_event_log(limit: int = 50, ):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get recent webhook event processing log."""
    return {
        "events": WebhookAdapter.get_event_log(limit),
        "total_processed": len(WebhookAdapter._processed_events),
    }


@router.get("/health", response_model=None)
async def external_webhooks_health():
    # multi-tenancy: public endpoint (health) — no tenant data
    """Check external webhook endpoints health and configuration."""
    return {
        "status": "healthy",
        "endpoints": {
            "ats": "/external-webhooks/ats/{platform}",
            "interview": "/external-webhooks/interview/{provider}",
            "test": "/external-webhooks/test/{provider}",
            "document": "/external-webhooks/document/{provider}",
            "event_log": "/external-webhooks/event-log",
        },
        "supported_ats_platforms": ["gupy", "pandape", "merge"],
        "secrets_configured": {
            "gupy": bool(os.getenv("GUPY_WEBHOOK_SECRET")),
            "pandape": bool(os.getenv("PANDAPE_WEBHOOK_SECRET")),
            "merge": bool(os.getenv("MERGE_WEBHOOK_SECRET")),
        },
        "feature_flags": {
            "interview_calendly": is_webhook_adapter_enabled("interview_calendly"),
            "test_testgorilla": is_webhook_adapter_enabled("test_testgorilla"),
            "test_codility": is_webhook_adapter_enabled("test_codility"),
            "document_custom": is_webhook_adapter_enabled("document_custom"),
        }
    }
