"""
Job Status Webhook Service - Dispatch webhooks for job vacancy status changes.

This service handles:
- Dispatching webhooks when job status changes
- Retry with exponential backoff
- HMAC signature generation
- Audit logging of all webhook calls
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.domains.job_management.repositories.webhook_repository import WebhookRepository
from lia_models.audit_log import AuditLog, DecisionType
from lia_models.webhook_registration import JOB_STATUS_WEBHOOK_EVENTS, WebhookDeliveryLog, WebhookRegistration

logger = logging.getLogger(__name__)


class JobStatusWebhookService:
    """
    Service for dispatching webhooks on job vacancy status changes.
    
    Implements:
    - Webhook lookup by company and event type
    - HTTP POST with signed payload
    - Retry with exponential backoff (3 attempts)
    - Audit trail logging
    """
    
    def __init__(self):
        """Initialize JobStatusWebhookService."""
        self.is_development = getattr(settings, 'APP_ENV', 'development') == 'development'
        self.max_retries = 3
        self.base_delay = 1.0
    
    async def dispatch_status_change(
        self,
        job_id: str,
        old_status: str,
        new_status: str,
        company_id: str,
        db: AsyncSession,
        changed_by: str | None = None,
        job_title: str | None = None
    ) -> dict[str, Any]:
        """
        Dispatch webhook notifications for job status change.
        
        Args:
            job_id: Job vacancy ID
            old_status: Previous status
            new_status: New status
            company_id: Company ID
            db: Database session
            changed_by: User who made the change
            job_title: Job title for context
            
        Returns:
            Result of webhook dispatch
        """
        # T-10 Fase 4 WIRE canonical (ADR-032): CANCELED outcome learning loop.
        # Centralizado AQUI (1 site) vs N call sites em bulk_archive/cancel/lifecycle.
        # Status PT-BR canonical: "Arquivada"/"Cancelada"/"Encerrada" → CANCELED.
        # "Concluída" → FILLED já wire em mark_filled (Phase 1) — não duplicar.
        # Fail-soft: helper canonical wire_feedback_outcome nunca raises.
        _CANCELED_STATUSES = {"arquivada", "cancelada", "encerrada"}
        if new_status and new_status.lower() in _CANCELED_STATUSES:
            try:
                from app.shared.learning.feedback_writer import wire_feedback_outcome
                await wire_feedback_outcome(
                    db=db,
                    domain="job_management",
                    outcome_type="CANCELED",
                    company_id=company_id,
                    job_id=job_id,
                    context={
                        "old_status": old_status,
                        "new_status": new_status,
                        "changed_by": changed_by,
                        "wire_source": "job_status_webhook_service.dispatch_status_change",
                    },
                )
            except Exception as _wire_exc:
                logger.warning(
                    "[dispatch_status_change] T-10 Fase 4 wire failed (non-blocking): %s",
                    str(_wire_exc)[:200],
                )

        try:
            webhooks = await self._get_active_webhooks(
                company_id=company_id,
                event_type="job.status_changed",
                db=db
            )
            
            if not webhooks:
                logger.debug(f"No webhooks registered for company {company_id} for job.status_changed")
                return {
                    "success": True,
                    "triggered": 0,
                    "message": "No webhooks registered for this event"
                }
            
            payload = {
                "event": "job.status_changed",
                "job_id": job_id,
                "old_status": old_status,
                "new_status": new_status,
                "changed_at": datetime.utcnow().isoformat() + "Z",
                "changed_by": changed_by,
                "job_title": job_title
            }
            
            # P1-W3-15: enqueue via Celery (non-blocking) — mirrors Studio webhook_tasks pattern.
            # _deliver_with_retry (blocking async with asyncio.sleep) is kept for test-webhook path.
            queued = 0
            for webhook in webhooks:
                try:
                    from app.jobs.webhook_tasks import deliver_webhook_task
                    deliver_webhook_task.delay(
                        webhook_id=str(webhook.id),
                        url=webhook.url,
                        secret=webhook.secret_key or "",
                        event="job.status_changed",
                        payload=payload,
                    )
                    queued += 1
                    await self._log_to_audit_trail(
                        company_id=company_id,
                        job_id=job_id,
                        webhook_id=str(webhook.id),
                        event_type="job.status_changed",
                        success=True,  # enqueued — actual delivery result logged by Celery
                        error=None,
                        db=db
                    )
                except Exception as _enq_err:
                    logger.warning("[JobWebhook] Celery enqueue failed for webhook %s: %s", webhook.id, _enq_err)
            results = [{"queued": queued, "total": len(webhooks)}]
            
            logger.info("[WEBHOOK] Enqueued job.status_changed for job %s: %d/%d via Celery", job_id, queued, len(webhooks))

            return {
                "success": True,
                "triggered": len(webhooks),
                "queued": queued,
                "failed": len(webhooks) - queued,
                "delivery": "async_celery"
            }
            
        except Exception as e:
            logger.error(f"Error dispatching status change webhooks: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_active_webhooks(
        self,
        company_id: str,
        event_type: str,
        db: AsyncSession
    ) -> list[WebhookRegistration]:
        """Get active webhooks for a company subscribed to an event type."""
        all_webhooks = await WebhookRepository(db).list_active_for_company(company_id)
        
        matching_webhooks = [
            w for w in all_webhooks 
            if event_type in (w.event_types or []) or "*" in (w.event_types or [])
        ]
        
        return matching_webhooks
    
    async def _deliver_with_retry(
        self,
        webhook: WebhookRegistration,
        payload: dict[str, Any],
        event_type: str,
        db: AsyncSession
    ) -> dict[str, Any]:
        """
        Deliver webhook with exponential backoff retry.
        
        Args:
            webhook: Webhook configuration
            payload: Payload to send
            event_type: Event type for logging
            db: Database session
            
        Returns:
            Delivery result
        """
        last_error = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                result = await self._deliver_webhook(
                    webhook=webhook,
                    payload=payload,
                    event_type=event_type,
                    attempt=attempt,
                    db=db
                )
                
                if result.get("success"):
                    return result
                
                last_error = result.get("error", "Unknown error")
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Webhook delivery attempt {attempt} failed: {e}")
            
            if attempt < self.max_retries:
                delay = self.base_delay * (2 ** (attempt - 1))
                logger.info(f"Retrying webhook in {delay}s (attempt {attempt + 1}/{self.max_retries})")
                await asyncio.sleep(delay)
        
        logger.error(f"Webhook delivery failed after {self.max_retries} attempts: {last_error}")
        return {
            "success": False,
            "error": last_error,
            "attempts": self.max_retries
        }
    
    async def _deliver_webhook(
        self,
        webhook: WebhookRegistration,
        payload: dict[str, Any],
        event_type: str,
        attempt: int,
        db: AsyncSession
    ) -> dict[str, Any]:
        """
        Deliver a single webhook request.
        
        Args:
            webhook: Webhook configuration
            payload: Payload to send
            event_type: Event type
            attempt: Attempt number
            db: Database session
            
        Returns:
            Delivery result
        """
        start_time = datetime.utcnow()
        
        log = WebhookDeliveryLog(
            webhook_id=webhook.id,
            company_id=webhook.company_id,
            event_type=event_type,
            payload=payload,
            status="pending",
            attempt_number=attempt
        )
        db.add(log)
        
        if self.is_development and not webhook.url.startswith("http"):
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"[WEBHOOK DEV] {webhook.name}: {payload}")
            log.status = "success"
            log.completed_at = datetime.utcnow()
            log.duration_ms = 0
            await db.commit()
            return {
                "success": True,
                "mode": "development",
                "message": "Webhook logged (development mode)"
            }
        
        payload_json = json.dumps(payload, separators=(',', ':'), default=str)
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "LIA-Agent-System/1.0",
            "X-Webhook-Event": event_type,
            "X-Webhook-Timestamp": datetime.utcnow().isoformat(),
            "X-Webhook-Delivery": str(log.id),
        }
        
        if webhook.headers:
            headers.update(webhook.headers)
        
        if webhook.secret_key:
            signature = WebhookRegistration.generate_signature(payload_json, webhook.secret_key)
            headers[WEBHOOK_SIGNATURE_HEADER] = signature  # canonical
            headers[WEBHOOK_SIGNATURE_HEADER_LEGACY] = signature  # backward compat (P1-W3-13)
        
        try:
            async with httpx.AsyncClient(timeout=webhook.timeout_seconds) as client:
                response = await client.post(
                    webhook.url,
                    content=payload_json,
                    headers=headers
                )
                
                end_time = datetime.utcnow()
                duration_ms = int((end_time - start_time).total_seconds() * 1000)
                
                if 200 <= response.status_code < 300:
                    log.status = "success"
                    log.status_code = response.status_code
                    log.response_body = response.text[:1000] if response.text else None
                    log.completed_at = end_time
                    log.duration_ms = duration_ms
                    
                    webhook.last_triggered_at = datetime.utcnow()
                    webhook.last_success_at = datetime.utcnow()
                    webhook.total_triggers += 1
                    webhook.total_successes += 1
                    
                    await db.commit()
                    
                    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                    logger.info(f"Webhook delivered: {webhook.name} ({response.status_code})")
                    
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "duration_ms": duration_ms
                    }
                else:
                    log.status = "failed"
                    log.status_code = response.status_code
                    log.response_body = response.text[:1000] if response.text else None
                    log.error_message = f"HTTP {response.status_code}"
                    log.completed_at = end_time
                    log.duration_ms = duration_ms
                    
                    webhook.last_triggered_at = datetime.utcnow()
                    webhook.last_failure_at = datetime.utcnow()
                    webhook.last_failure_reason = f"HTTP {response.status_code}"
                    webhook.total_triggers += 1
                    webhook.total_failures += 1
                    
                    await db.commit()
                    
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "error": f"HTTP {response.status_code}"
                    }
                    
        except httpx.TimeoutException:
            try:
                await db.rollback()
            except Exception:
                pass
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            log.status = "failed"
            log.error_message = "Request timeout"
            log.completed_at = end_time
            log.duration_ms = duration_ms
            
            webhook.last_triggered_at = datetime.utcnow()
            webhook.last_failure_at = datetime.utcnow()
            webhook.last_failure_reason = "Request timeout"
            webhook.total_triggers += 1
            webhook.total_failures += 1
            
            await db.commit()
            
            return {
                "success": False,
                "error": "Request timeout"
            }
            
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            log.status = "failed"
            log.error_message = str(e)
            log.completed_at = end_time
            log.duration_ms = duration_ms
            
            webhook.last_triggered_at = datetime.utcnow()
            webhook.last_failure_at = datetime.utcnow()
            webhook.last_failure_reason = str(e)
            webhook.total_triggers += 1
            webhook.total_failures += 1
            
            await db.commit()
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _log_to_audit_trail(
        self,
        company_id: str,
        job_id: str,
        webhook_id: str,
        event_type: str,
        success: bool,
        error: str | None,
        db: AsyncSession
    ):
        """Log webhook dispatch to audit trail."""
        try:
            audit_log = AuditLog(
                company_id=company_id,
                candidate_id=None,
                vacancy_id=job_id,
                agent_name="job_status_webhook_service",
                decision_type=DecisionType.ACTION,
                action="webhook_dispatch",
                outcome="success" if success else "failure",
                reason=f"Dispatched {event_type} webhook to {webhook_id}" if success else f"Failed: {error}",
                confidence_score=1.0 if success else 0.0,
                input_data={"event_type": event_type, "job_id": job_id},
                output_data={"webhook_id": webhook_id, "success": success, "error": error}
            )
            db.add(audit_log)
            await db.commit()
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.warning(f"Failed to log to audit trail: {e}")
    
    async def send_test_webhook(
        self,
        webhook_id: str,
        company_id: str,
        db: AsyncSession
    ) -> dict[str, Any]:
        """
        Send a test webhook to verify configuration.
        
        Args:
            webhook_id: Webhook ID to test
            company_id: Company ID for authorization
            db: Database session
            
        Returns:
            Test result
        """
        try:
            webhook = await WebhookRepository(db).get_by_id(webhook_id, company_id)
            
            if not webhook:
                return {
                    "success": False,
                    "error": "Webhook not found"
                }
            
            test_payload = {
                "event": "webhook.test",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "data": {
                    "message": "This is a test webhook from LIA Agent System",
                    "webhook_id": str(webhook_id),
                    "webhook_name": webhook.name,
                    "test": True
                }
            }
            
            return await self._deliver_with_retry(
                webhook=webhook,
                payload=test_payload,
                event_type="webhook.test",
                db=db
            )
            
        except Exception as e:
            logger.error(f"Error sending test webhook: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_available_events(self) -> list[dict[str, Any]]:
        """Get list of available webhook events."""
        return JOB_STATUS_WEBHOOK_EVENTS


job_status_webhook_service = JobStatusWebhookService()
