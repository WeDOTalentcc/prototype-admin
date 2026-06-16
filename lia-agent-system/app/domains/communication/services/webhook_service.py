"""
Webhook Service - External webhook management.

This service handles:
- Registering external webhooks for event notifications
- Triggering webhooks when events occur
- Managing webhook configurations
- Logging webhook delivery attempts
"""
import hashlib
from app.shared.constants.webhook_constants import (
    WEBHOOK_SIGNATURE_HEADER,
    WEBHOOK_SIGNATURE_HEADER_LEGACY,
)  # P1-W3-13
import hmac
import json
import logging
import secrets
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.communication.repositories.webhook_repository import WebhookRepository

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from lia_models.webhook import WEBHOOK_EVENTS, Webhook, WebhookLog, WebhookStatus

logger = logging.getLogger(__name__)


class WebhookService:
    """
    Service for managing outbound webhooks.
    
    Webhooks allow external systems to be notified when events occur in the LIA system.
    Each webhook can subscribe to multiple events and will receive HTTP POST requests
    with event data when those events occur.
    """
    
    def __init__(self):
        """Initialize WebhookService."""
        self.is_development = settings.APP_ENV == "development"
    
    async def register_webhook(
        self,
        company_id: str,
        name: str,
        url: str,
        events: list[str],
        description: str | None = None,
        secret_key: str | None = None,
        headers: dict[str, str] | None = None,
        retry_count: int = 3,
        timeout_seconds: int = 30,
        created_by: str | None = None,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Register a new webhook.
        
        Args:
            company_id: Company ID
            name: Webhook name for identification
            url: Webhook endpoint URL
            events: List of events to subscribe to
            description: Optional description
            secret_key: Secret for signing payloads (auto-generated if not provided)
            headers: Custom headers to include in webhook requests
            retry_count: Number of retry attempts on failure
            timeout_seconds: Request timeout in seconds
            created_by: User who created the webhook
            db: Database session
            
        Returns:
            Created webhook data
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            valid_events = list(WEBHOOK_EVENTS)  # P1-W3-12: WEBHOOK_EVENTS is list[str] from enum, not list[dict]
            for event in events:
                if event not in valid_events:
                    return {
                        "success": False,
                        "error": f"Invalid event: {event}. Valid events: {valid_events}"
                    }
            
            if not secret_key:
                secret_key = secrets.token_urlsafe(32)
            
            webhook = Webhook(
                company_id=company_id,
                name=name,
                description=description,
                url=url,
                events=events,
                secret_key=secret_key,
                headers=headers or {},
                retry_count=retry_count,
                timeout_seconds=timeout_seconds,
                created_by=created_by,
                is_active=True
            )
            
            db.add(webhook)
            await db.commit()
            await db.refresh(webhook)
            
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"Webhook registered: {name} for events {events}")
            
            return {
                "success": True,
                "webhook": webhook.to_dict_full(),
                "message": "Webhook registered successfully"
            }
            
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error(f"Error registering webhook: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            if should_close:
                await db.close()
    
    async def update_webhook(
        self,
        webhook_id: str,
        company_id: str,
        updates: dict[str, Any],
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Update an existing webhook.
        
        Args:
            webhook_id: Webhook ID to update
            company_id: Company ID for authorization
            updates: Fields to update
            db: Database session
            
        Returns:
            Updated webhook data
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            webhook = await WebhookRepository(db).get_by_id_and_company(
                webhook_id=webhook_id, company_id=company_id
            )
            
            if not webhook:
                return {
                    "success": False,
                    "error": "Webhook not found"
                }
            
            allowed_updates = ["name", "description", "url", "events", "headers", 
                             "is_active", "retry_count", "timeout_seconds"]
            
            for key, value in updates.items():
                if key in allowed_updates:
                    setattr(webhook, key, value)
            
            webhook.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(webhook)
            
            logger.info(f"Webhook updated: {webhook_id}")
            
            return {
                "success": True,
                "webhook": webhook.to_dict()
            }
            
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error(f"Error updating webhook: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            if should_close:
                await db.close()
    
    async def delete_webhook(
        self,
        webhook_id: str,
        company_id: str,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Delete a webhook.
        
        Args:
            webhook_id: Webhook ID to delete
            company_id: Company ID for authorization
            db: Database session
            
        Returns:
            Success status
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            webhook = await WebhookRepository(db).get_by_id_and_company(
                webhook_id=webhook_id, company_id=company_id
            )
            
            if not webhook:
                return {
                    "success": False,
                    "error": "Webhook not found"
                }
            
            await db.delete(webhook)
            await db.commit()
            
            logger.info(f"Webhook deleted: {webhook_id}")
            
            return {
                "success": True,
                "message": "Webhook deleted successfully"
            }
            
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error(f"Error deleting webhook: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            if should_close:
                await db.close()
    
    async def list_webhooks(
        self,
        company_id: str,
        is_active: bool | None = None,
        event_filter: str | None = None,
        limit: int = 50,
        offset: int = 0,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        List webhooks for a company.
        
        Args:
            company_id: Company ID
            is_active: Filter by active status
            event_filter: Filter by subscribed event
            limit: Maximum results
            offset: Pagination offset
            db: Database session
            
        Returns:
            List of webhooks
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            webhooks = await WebhookRepository(db).list_for_company(
                company_id=company_id, is_active=is_active, limit=limit, offset=offset
            )
            
            if event_filter:
                webhooks = [w for w in webhooks if event_filter in (w.events or [])]
            
            return {
                "success": True,
                "webhooks": [w.to_dict() for w in webhooks],
                "total": len(webhooks),
                "has_more": len(webhooks) == limit
            }
            
        except Exception as e:
            logger.error(f"Error listing webhooks: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            if should_close:
                await db.close()
    
    async def get_webhook(
        self,
        webhook_id: str,
        company_id: str,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Get a single webhook by ID.
        
        Args:
            webhook_id: Webhook ID
            company_id: Company ID for authorization
            db: Database session
            
        Returns:
            Webhook data
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            webhook = await WebhookRepository(db).get_by_id_and_company(
                webhook_id=webhook_id, company_id=company_id
            )
            
            if not webhook:
                return {
                    "success": False,
                    "error": "Webhook not found"
                }
            
            return {
                "success": True,
                "webhook": webhook.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error getting webhook: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            if should_close:
                await db.close()
    
    async def trigger_webhook(
        self,
        event: str,
        payload: dict[str, Any],
        company_id: str,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Trigger all webhooks subscribed to an event.
        
        Args:
            event: Event type that occurred
            payload: Event data payload
            company_id: Company ID
            db: Database session
            
        Returns:
            Results of webhook deliveries
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            all_webhooks = await WebhookRepository(db).list_active_for_company(company_id=company_id)
            
            webhooks = [w for w in all_webhooks if event in (w.events or [])]
            
            if not webhooks:
                return {
                    "success": True,
                    "triggered": 0,
                    "message": "No webhooks subscribed to this event"
                }
            
            full_payload = {
                "event": event,
                "timestamp": datetime.utcnow().isoformat(),
                "data": payload
            }
            
            results = []
            for webhook in webhooks:
                delivery_result = await self._deliver_webhook(webhook, full_payload, db)
                results.append({
                    "webhook_id": webhook.id,
                    "webhook_name": webhook.name,
                    **delivery_result
                })
            
            success_count = sum(1 for r in results if r.get("success"))
            
            return {
                "success": True,
                "triggered": len(webhooks),
                "successful": success_count,
                "failed": len(webhooks) - success_count,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error triggering webhooks: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            if should_close:
                await db.close()
    
    async def _deliver_webhook(
        self,
        webhook: Webhook,
        payload: dict[str, Any],
        db: AsyncSession
    ) -> dict[str, Any]:
        """
        Deliver a webhook to its endpoint.
        
        Args:
            webhook: Webhook configuration
            payload: Data to send
            db: Database session
            
        Returns:
            Delivery result
        """
        start_time = datetime.utcnow()
        
        log = WebhookLog(
            webhook_id=webhook.id,
            company_id=webhook.company_id,
            event=payload.get("event", "unknown"),
            payload=payload,
            status=WebhookStatus.PENDING.value,
            attempt_number=1
        )
        db.add(log)
        
        if self.is_development and not webhook.url.startswith("http"):
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"[WEBHOOK DEV] {webhook.name}: {payload}")
            log.status = WebhookStatus.SUCCESS.value
            log.completed_at = datetime.utcnow()
            log.duration_ms = 0
            await db.commit()
            return {
                "success": True,
                "mode": "development",
                "message": "Webhook logged (development mode)"
            }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "LIA-Agent-System/1.0",
            "X-Webhook-Event": payload.get("event", "unknown"),
            "X-Webhook-Timestamp": payload.get("timestamp", datetime.utcnow().isoformat()),
        }
        
        if webhook.headers:
            headers.update(webhook.headers)
        
        if webhook.secret_key:
            payload_json = json.dumps(payload, separators=(',', ':'))
            signature = hmac.new(
                webhook.secret_key.encode(),
                payload_json.encode(),
                hashlib.sha256
            ).hexdigest()
            headers[WEBHOOK_SIGNATURE_HEADER] = f"sha256={signature}"  # canonical
            headers[WEBHOOK_SIGNATURE_HEADER_LEGACY] = f"sha256={signature}"  # backward compat (P1-W3-13)
        
        try:
            async with httpx.AsyncClient(timeout=webhook.timeout_seconds) as client:
                response = await client.post(
                    webhook.url,
                    json=payload,
                    headers=headers
                )
                
                end_time = datetime.utcnow()
                duration_ms = int((end_time - start_time).total_seconds() * 1000)
                
                if 200 <= response.status_code < 300:
                    log.status = WebhookStatus.SUCCESS.value
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
                    log.status = WebhookStatus.FAILED.value
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
                    
                    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                    logger.warning(f"Webhook failed: {webhook.name} ({response.status_code})")
                    
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "error": f"HTTP {response.status_code}",
                        "duration_ms": duration_ms
                    }
                    
        except httpx.TimeoutException:
            try:
                await db.rollback()
            except Exception:
                pass
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            log.status = WebhookStatus.FAILED.value
            log.error_message = "Request timeout"
            log.completed_at = end_time
            log.duration_ms = duration_ms
            
            webhook.last_triggered_at = datetime.utcnow()
            webhook.last_failure_at = datetime.utcnow()
            webhook.last_failure_reason = "Request timeout"
            webhook.total_triggers += 1
            webhook.total_failures += 1
            
            await db.commit()
            
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.error(f"Webhook timeout: {webhook.name}")
            
            return {
                "success": False,
                "error": "Request timeout",
                "duration_ms": duration_ms
            }
            
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            log.status = WebhookStatus.FAILED.value
            log.error_message = str(e)
            log.completed_at = end_time
            log.duration_ms = duration_ms
            
            webhook.last_triggered_at = datetime.utcnow()
            webhook.last_failure_at = datetime.utcnow()
            webhook.last_failure_reason = str(e)
            webhook.total_triggers += 1
            webhook.total_failures += 1
            
            await db.commit()
            
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.error(f"Webhook error: {webhook.name} - {e}")
            
            return {
                "success": False,
                "error": str(e),
                "duration_ms": duration_ms
            }
    
    async def test_webhook(
        self,
        webhook_id: str,
        company_id: str,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Send a test event to a webhook.
        
        Args:
            webhook_id: Webhook ID to test
            company_id: Company ID for authorization
            db: Database session
            
        Returns:
            Test result
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            webhook = await WebhookRepository(db).get_by_id_and_company(
                webhook_id=webhook_id, company_id=company_id
            )
            
            if not webhook:
                return {
                    "success": False,
                    "error": "Webhook not found"
                }
            
            test_payload = {
                "event": "webhook.test",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "message": "This is a test webhook from LIA Agent System",
                    "webhook_id": webhook_id,
                    "webhook_name": webhook.name,
                    "test": True
                }
            }
            
            return await self._deliver_webhook(webhook, test_payload, db)
            
        except Exception as e:
            logger.error(f"Error testing webhook: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            if should_close:
                await db.close()
    
    async def get_webhook_logs(
        self,
        webhook_id: str,
        company_id: str,
        status_filter: str | None = None,
        limit: int = 50,
        offset: int = 0,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Get delivery logs for a webhook.
        
        Args:
            webhook_id: Webhook ID
            company_id: Company ID for authorization
            status_filter: Filter by status
            limit: Maximum results
            offset: Pagination offset
            db: Database session
            
        Returns:
            List of webhook logs
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            logs = await WebhookRepository(db).list_logs_for_webhook(
                webhook_id=webhook_id, company_id=company_id, status_filter=status_filter,
                limit=limit, offset=offset
            )
            
            return {
                "success": True,
                "logs": [log.to_dict() for log in logs],
                "total": len(logs),
                "has_more": len(logs) == limit
            }
            
        except Exception as e:
            logger.error(f"Error getting webhook logs: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            if should_close:
                await db.close()
    
    def get_available_events(self) -> list[dict[str, Any]]:
        """
        Get list of available webhook events.
        
        Returns:
            List of available events with descriptions and payload examples
        """
        return WEBHOOK_EVENTS


webhook_service = WebhookService()
