"""
Event Dispatcher Service
Listens for database events and triggers corresponding automation handlers.

This service provides a centralized way to dispatch events to automation handlers
when important database events occur (stage changes, screening completed, etc.).

Usage:
    from app.shared.services.event_dispatcher import event_dispatcher
    
    await event_dispatcher.on_screening_completed(
        candidate_id="...",
        vacancy_id="...",
        company_id="...",
        wsi_scores={"adaptabilidade": 0.85, ...}
    )
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class EventDispatcher:
    """
    Dispatches events to automation handlers.
    Can be called from services when important events occur.
    
    Events are dispatched asynchronously via HTTP to the automation API endpoints.
    This decouples the event source from the automation logic.
    """
    
    def __init__(self):
        # P2-W1-10: FastAPI roda na porta 8001 no Replit. Default 8000 é fallback local.
        # Configurar INTERNAL_API_URL=http://127.0.0.1:8001 em .env se evento-dispatcher
        # falhar silenciosamente em dev. Front-end proxies ja usam 8001 (process.env.BACKEND_URL).
        internal_api_url = os.getenv("INTERNAL_API_URL", "http://127.0.0.1:8001")
        self.base_url = f"{internal_api_url}/api/v1/automation"
        self._client: httpx.AsyncClient | None = None
        self._enabled = True
    
    async def get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client for dispatching events."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
    
    def enable(self):
        """Enable event dispatching."""
        self._enabled = True
        logger.info("[EVENT_DISPATCHER] Enabled")
    
    def disable(self):
        """Disable event dispatching (useful for testing/migrations)."""
        self._enabled = False
        logger.info("[EVENT_DISPATCHER] Disabled")
    
    async def dispatch(
        self,
        trigger: str,
        payload: dict[str, Any],
        fire_and_forget: bool = True,
        use_engine: bool = True
    ) -> dict[str, Any]:
        """
        Dispatch an event to the appropriate automation handler.
        
        Args:
            trigger: The trigger type (e.g., "screening-completed", "ats-sync")
            payload: The event payload to send
            fire_and_forget: If True, don't wait for response (default)
            use_engine: If True, use StageAutomationEngine for routing (default)
            
        Returns:
            Dict with dispatch result
        """
        if not self._enabled:
            logger.debug(f"[EVENT_DISPATCHER] Skipping {trigger} - dispatcher disabled")
            return {"success": True, "skipped": True, "reason": "dispatcher_disabled"}
        
        if use_engine:
            from app.core.database import AsyncSessionLocal
            from app.domains.automation.services.stage_automation_engine import (
                AutomationEvent,
                TriggerType,
                stage_automation_engine,
            )
            
            try:
                trigger_type = TriggerType(trigger.replace("-", "_"))
            except ValueError:
                logger.warning(f"[EVENT_DISPATCHER] Unknown trigger type: {trigger}, falling back to HTTP")
                use_engine = False
            
            if use_engine:
                async def _do_engine_dispatch():
                    try:
                        async with AsyncSessionLocal() as db:
                            event = AutomationEvent(
                                trigger_type=trigger_type,
                                candidate_id=payload.get("candidate_id", ""),
                                vacancy_id=payload.get("vacancy_id", ""),
                                company_id=payload.get("company_id", ""),
                                payload=payload,
                                source="event_dispatcher"
                            )
                            result = await stage_automation_engine.process_event(event, db)
                            await db.commit()
                            logger.info(
                                f"[EVENT_DISPATCHER] {trigger} processed via engine: "
                                f"success={result.get('success')}"
                            )
                            return result
                    except Exception as e:
                        try:
                            await db.rollback()
                        except Exception:
                            pass
                        logger.error(f"[EVENT_DISPATCHER] Engine error for {trigger}: {e}")
                        return {"success": False, "error": str(e), "engine_error": True}
                
                if fire_and_forget:
                    asyncio.create_task(_do_engine_dispatch())
                    return {"success": True, "dispatched": True, "fire_and_forget": True, "via_engine": True}
                else:
                    return await _do_engine_dispatch()
        
        client = await self.get_client()
        endpoint = f"{self.base_url}/handle-trigger/{trigger}"
        
        async def _do_dispatch():
            try:
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                result = response.json()
                logger.info(
                    f"[EVENT_DISPATCHER] {trigger} dispatched successfully: "
                    f"success={result.get('success')}"
                )
                return result
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"[EVENT_DISPATCHER] HTTP error dispatching {trigger}: "
                    f"{e.response.status_code} - {e.response.text}"
                )
                return {"success": False, "error": str(e), "status_code": e.response.status_code}
            except httpx.RequestError as e:
                logger.error(f"[EVENT_DISPATCHER] Request error dispatching {trigger}: {e}")
                return {"success": False, "error": str(e)}
            except Exception as e:
                logger.error(f"[EVENT_DISPATCHER] Unexpected error dispatching {trigger}: {e}")
                return {"success": False, "error": str(e)}
        
        if fire_and_forget:
            asyncio.create_task(_do_dispatch())
            return {"success": True, "dispatched": True, "fire_and_forget": True}
        else:
            return await _do_dispatch()
    
    async def dispatch_multiple(
        self,
        events: list[dict[str, Any]],
        fire_and_forget: bool = True
    ) -> list[dict[str, Any]]:
        """
        Dispatch multiple events in parallel.
        
        Args:
            events: List of dicts with "trigger" and "payload" keys
            fire_and_forget: If True, don't wait for responses
            
        Returns:
            List of dispatch results
        """
        tasks = [
            self.dispatch(
                event["trigger"],
                event["payload"],
                fire_and_forget=fire_and_forget
            )
            for event in events
        ]
        return await asyncio.gather(*tasks)
    
    async def on_screening_completed(
        self,
        candidate_id: str,
        vacancy_id: str,
        company_id: str,
        wsi_scores: dict[str, float] | None = None,
        screening_type: str = "wsi",
        passed: bool = True,
        **kwargs
    ) -> dict[str, Any]:
        """
        Dispatch event when a candidate completes screening.
        
        Args:
            candidate_id: ID of the candidate
            vacancy_id: ID of the vacancy
            company_id: ID of the company
            wsi_scores: WSI dimension scores
            screening_type: Type of screening (wsi, cv, technical)
            passed: Whether candidate passed screening
            **kwargs: Additional context
            
        Returns:
            Dispatch result
        """
        payload = {
            "candidate_id": candidate_id,
            "vacancy_id": vacancy_id,
            "company_id": company_id,
            "wsi_scores": wsi_scores or {},
            "screening_type": screening_type,
            "passed": passed,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        
        logger.info(
            f"[EVENT_DISPATCHER] Dispatching screening-completed for "
            f"candidate={candidate_id}, vacancy={vacancy_id}"
        )
        
        return await self.dispatch("screening-completed", payload)
    
    async def on_stage_changed(
        self,
        candidate_id: str,
        vacancy_id: str,
        company_id: str,
        new_stage: str,
        previous_stage: str | None = None,
        triggered_by: str = "system",
        source_agent: str | None = None,
        sync_to_ats: bool = True,
        **kwargs
    ) -> dict[str, Any]:
        """
        Dispatch event when a candidate's stage changes.
        
        This triggers ATS synchronization if enabled.
        
        Args:
            candidate_id: ID of the candidate
            vacancy_id: ID of the vacancy
            company_id: ID of the company
            new_stage: The new stage name
            previous_stage: The previous stage name
            triggered_by: Who triggered the change
            source_agent: Agent that triggered (if applicable)
            sync_to_ats: Whether to sync to ATS
            **kwargs: Additional context
            
        Returns:
            Dispatch result
        """
        payload = {
            "candidate_id": candidate_id,
            "vacancy_id": vacancy_id,
            "company_id": company_id,
            "new_stage": new_stage,
            "previous_stage": previous_stage,
            "triggered_by": triggered_by,
            "source_agent": source_agent,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        
        logger.info(
            f"[EVENT_DISPATCHER] Dispatching stage change: "
            f"{previous_stage} → {new_stage} for candidate={candidate_id}"
        )
        
        if sync_to_ats:
            return await self.dispatch("ats-sync", payload)
        
        return {"success": True, "skipped": True, "reason": "ats_sync_disabled"}
    
    async def on_interview_scheduled(
        self,
        candidate_id: str,
        vacancy_id: str,
        company_id: str,
        interview_id: str,
        interview_datetime: str,
        interview_type: str = "video",
        interviewer_name: str | None = None,
        interviewer_email: str | None = None,
        **kwargs
    ) -> dict[str, Any]:
        """
        Dispatch event when an interview is scheduled.
        
        Args:
            candidate_id: ID of the candidate
            vacancy_id: ID of the vacancy
            company_id: ID of the company
            interview_id: ID of the created interview
            interview_datetime: ISO format datetime of the interview
            interview_type: Type of interview
            interviewer_name: Name of the interviewer
            interviewer_email: Email of the interviewer
            **kwargs: Additional context
            
        Returns:
            Dispatch result
        """
        payload = {
            "candidate_id": candidate_id,
            "vacancy_id": vacancy_id,
            "company_id": company_id,
            "interview_id": interview_id,
            "interview_datetime": interview_datetime,
            "interview_type": interview_type,
            "interviewer_name": interviewer_name,
            "interviewer_email": interviewer_email,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        
        logger.info(
            f"[EVENT_DISPATCHER] Dispatching interview-scheduled for "
            f"candidate={candidate_id}, interview={interview_id}"
        )
        
        return await self.dispatch("interview-scheduled", payload)
    
    async def on_interview_completed(
        self,
        candidate_id: str,
        vacancy_id: str,
        company_id: str,
        interview_id: str,
        outcome: str | None = None,
        feedback: dict[str, Any] | None = None,
        **kwargs
    ) -> dict[str, Any]:
        """
        Dispatch event when an interview is completed.
        
        Args:
            candidate_id: ID of the candidate
            vacancy_id: ID of the vacancy
            company_id: ID of the company
            interview_id: ID of the completed interview
            outcome: Interview outcome (passed, failed, pending_review)
            feedback: Interview feedback data
            **kwargs: Additional context
            
        Returns:
            Dispatch result
        """
        payload = {
            "candidate_id": candidate_id,
            "vacancy_id": vacancy_id,
            "company_id": company_id,
            "interview_id": interview_id,
            "outcome": outcome,
            "feedback": feedback or {},
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        
        logger.info(
            f"[EVENT_DISPATCHER] Dispatching interview-completed for "
            f"candidate={candidate_id}, interview={interview_id}"
        )
        
        return await self.dispatch("interview-completed", payload)
    
    async def on_candidate_inactive(
        self,
        candidate_id: str,
        vacancy_id: str,
        company_id: str,
        days_inactive: int,
        last_activity: str | None = None,
        **kwargs
    ) -> dict[str, Any]:
        """
        Dispatch event when a candidate becomes inactive.
        
        Args:
            candidate_id: ID of the candidate
            vacancy_id: ID of the vacancy
            company_id: ID of the company
            days_inactive: Number of days since last activity
            last_activity: Description of last activity
            **kwargs: Additional context
            
        Returns:
            Dispatch result
        """
        payload = {
            "candidate_id": candidate_id,
            "vacancy_id": vacancy_id,
            "company_id": company_id,
            "days_inactive": days_inactive,
            "last_activity": last_activity,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        
        logger.info(
            f"[EVENT_DISPATCHER] Dispatching candidate-inactive for "
            f"candidate={candidate_id}, days_inactive={days_inactive}"
        )
        
        return await self.dispatch("candidate-inactive", payload)
    
    async def on_candidate_no_show(
        self,
        candidate_id: str,
        vacancy_id: str,
        company_id: str,
        interview_id: str,
        scheduled_datetime: str,
        **kwargs
    ) -> dict[str, Any]:
        """
        Dispatch event when a candidate doesn't show up for an interview.
        
        Args:
            candidate_id: ID of the candidate
            vacancy_id: ID of the vacancy
            company_id: ID of the company
            interview_id: ID of the missed interview
            scheduled_datetime: When the interview was scheduled
            **kwargs: Additional context
            
        Returns:
            Dispatch result
        """
        payload = {
            "candidate_id": candidate_id,
            "vacancy_id": vacancy_id,
            "company_id": company_id,
            "interview_id": interview_id,
            "scheduled_datetime": scheduled_datetime,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        
        logger.info(
            f"[EVENT_DISPATCHER] Dispatching candidate-no-show for "
            f"candidate={candidate_id}, interview={interview_id}"
        )
        
        return await self.dispatch("candidate-no-show", payload)
    
    async def on_offer_sent(
        self,
        candidate_id: str,
        vacancy_id: str,
        company_id: str,
        salary_offered: float | None = None,
        start_date: str | None = None,
        response_deadline: str | None = None,
        offer_details: dict[str, Any] | None = None,
        **kwargs
    ) -> dict[str, Any]:
        """
        Dispatch event when an offer is sent to a candidate.
        
        Args:
            candidate_id: ID of the candidate
            vacancy_id: ID of the vacancy
            company_id: ID of the company
            salary_offered: Salary amount offered
            start_date: Proposed start date
            response_deadline: Date by which candidate should respond
            offer_details: Additional offer details
            **kwargs: Additional context
            
        Returns:
            Dispatch result
        """
        payload = {
            "candidate_id": candidate_id,
            "vacancy_id": vacancy_id,
            "company_id": company_id,
            "salary_offered": salary_offered,
            "start_date": start_date,
            "response_deadline": response_deadline,
            "offer_details": offer_details or {},
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        
        logger.info(
            f"[EVENT_DISPATCHER] Dispatching offer-sent for "
            f"candidate={candidate_id}, vacancy={vacancy_id}"
        )
        
        return await self.dispatch("offer-sent", payload)
    
    async def on_candidate_hired(
        self,
        candidate_id: str,
        vacancy_id: str,
        company_id: str,
        hire_date: str | None = None,
        final_salary: float | None = None,
        department: str | None = None,
        manager_id: str | None = None,
        **kwargs
    ) -> dict[str, Any]:
        """
        Dispatch event when a candidate is hired.
        
        Args:
            candidate_id: ID of the candidate
            vacancy_id: ID of the vacancy
            company_id: ID of the company
            hire_date: Official hire date
            final_salary: Final agreed salary
            department: Department the candidate will join
            manager_id: ID of the direct manager
            **kwargs: Additional context
            
        Returns:
            Dispatch result
        """
        payload = {
            "candidate_id": candidate_id,
            "vacancy_id": vacancy_id,
            "company_id": company_id,
            "hire_date": hire_date,
            "final_salary": final_salary,
            "department": department,
            "manager_id": manager_id,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        
        logger.info(
            f"[EVENT_DISPATCHER] Dispatching candidate-hired for "
            f"candidate={candidate_id}, vacancy={vacancy_id}"
        )
        
        return await self.dispatch("candidate-hired", payload)
    
    async def on_candidate_rejected(
        self,
        candidate_id: str,
        vacancy_id: str,
        company_id: str,
        rejection_reason: str | None = None,
        rejection_stage: str | None = None,
        add_to_talent_pool: bool = True,
        send_feedback: bool = True,
        **kwargs
    ) -> dict[str, Any]:
        """
        Dispatch event when a candidate is rejected.
        
        Args:
            candidate_id: ID of the candidate
            vacancy_id: ID of the vacancy
            company_id: ID of the company
            rejection_reason: Reason for rejection
            rejection_stage: Stage at which rejected
            add_to_talent_pool: Whether to add to talent pool
            send_feedback: Whether to send feedback email
            **kwargs: Additional context
            
        Returns:
            Dispatch result
        """
        payload = {
            "candidate_id": candidate_id,
            "vacancy_id": vacancy_id,
            "company_id": company_id,
            "rejection_reason": rejection_reason,
            "rejection_stage": rejection_stage,
            "add_to_talent_pool": add_to_talent_pool,
            "send_feedback": send_feedback,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        
        logger.info(
            f"[EVENT_DISPATCHER] Dispatching candidate-rejected for "
            f"candidate={candidate_id}, vacancy={vacancy_id}, stage={rejection_stage}"
        )
        
        return await self.dispatch("candidate-rejected", payload)

    async def on_job_status_changed(
        self,
        job_id: str,
        company_id: str,
        new_status: str,
        previous_status: str | None = None,
        changed_by: str = "system",
        job_title: str | None = None,
        **kwargs
    ) -> dict[str, Any]:
        payload = {
            "job_id": job_id,
            "company_id": company_id,
            "new_status": new_status,
            "previous_status": previous_status,
            "changed_by": changed_by,
            "job_title": job_title,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }

        logger.info(
            f"[EVENT_DISPATCHER] Dispatching job-status-changed: "
            f"{previous_status} → {new_status} for job={job_id}"
        )

        return await self.dispatch("job-status-changed", payload)

    async def on_candidates_sourced(
        self,
        job_id: str,
        company_id: str,
        candidates_found: int,
        candidates_added: int,
        source: str = "local",
        expanded_to_global: bool = False,
        job_title: str | None = None,
        **kwargs
    ) -> dict[str, Any]:
        payload = {
            "job_id": job_id,
            "company_id": company_id,
            "candidates_found": candidates_found,
            "candidates_added": candidates_added,
            "source": source,
            "expanded_to_global": expanded_to_global,
            "job_title": job_title,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }

        logger.info(
            f"[EVENT_DISPATCHER] Dispatching candidates-sourced: "
            f"found={candidates_found}, added={candidates_added} for job={job_id}"
        )

        return await self.dispatch("candidates-sourced", payload)

    async def on_message_sent(
        self,
        company_id: str,
        candidate_id: str,
        message_type: str,
        channel: str,
        job_id: str | None = None,
        success: bool = True,
        log_id: str | None = None,
        **kwargs
    ) -> dict[str, Any]:
        payload = {
            "company_id": company_id,
            "candidate_id": candidate_id,
            "message_type": message_type,
            "channel": channel,
            "job_id": job_id,
            "success": success,
            "log_id": log_id,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }

        logger.info(
            f"[EVENT_DISPATCHER] Dispatching message-sent: "
            f"type={message_type}, channel={channel}, candidate={candidate_id}"
        )

        return await self.dispatch("message-sent", payload)

    async def on_ats_sync_completed(
        self,
        company_id: str,
        ats_type: str,
        trigger: str,
        candidate_id: str | None = None,
        job_id: str | None = None,
        fields_synced: int = 0,
        success: bool = True,
        **kwargs
    ) -> dict[str, Any]:
        payload = {
            "company_id": company_id,
            "ats_type": ats_type,
            "trigger": trigger,
            "candidate_id": candidate_id,
            "job_id": job_id,
            "fields_synced": fields_synced,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }

        logger.info(
            f"[EVENT_DISPATCHER] Dispatching ats-sync-completed: "
            f"ats={ats_type}, trigger={trigger}, fields={fields_synced}"
        )

        return await self.dispatch("ats-sync-completed", payload)

    async def on_report_generated(
        self,
        company_id: str,
        report_type: str,
        user_id: str | None = None,
        email_sent: bool = False,
        recipients_count: int = 0,
        **kwargs
    ) -> dict[str, Any]:
        payload = {
            "company_id": company_id,
            "report_type": report_type,
            "user_id": user_id,
            "email_sent": email_sent,
            "recipients_count": recipients_count,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }

        logger.info(
            f"[EVENT_DISPATCHER] Dispatching report-generated: "
            f"type={report_type}, sent={email_sent}"
        )

        return await self.dispatch("report-generated", payload)


event_dispatcher = EventDispatcher()
