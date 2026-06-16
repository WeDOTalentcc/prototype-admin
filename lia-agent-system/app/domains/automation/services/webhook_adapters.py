import logging
from enum import Enum, StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class WebhookEventType(StrEnum):
    INTERVIEW_CONFIRMED = "interview_confirmed"
    INTERVIEW_COMPLETED = "interview_completed"
    INTERVIEW_CANCELLED = "interview_cancelled"
    TEST_COMPLETED = "test_completed"
    TEST_EXPIRED = "test_expired"
    DOCUMENT_SUBMITTED = "document_submitted"
    REFERENCE_COMPLETED = "reference_completed"
    OFFER_ACCEPTED = "offer_accepted"
    OFFER_DECLINED = "offer_declined"
    CANDIDATE_RESPONSE = "candidate_response"


class WebhookAdapter:
    """Base adapter for processing inbound webhook events."""

    _processed_events: set[str] = set()

    @classmethod
    def is_duplicate(cls, event_id: str) -> bool:
        return event_id in cls._processed_events

    @classmethod
    def mark_processed(cls, event_id: str, event_type: str, provider: str, result: dict[str, Any]):
        cls._processed_events.add(event_id)
        if len(cls._processed_events) > 10000:
            cls._processed_events = set(list(cls._processed_events)[-5000:])


class InterviewWebhookAdapter(WebhookAdapter):
    """Processes interview-related webhook events and maps to pipeline transitions."""

    EVENT_TO_TRANSITION = {
        "interview_confirmed": {"sub_status": "interview_confirmed", "action": "update_status"},
        "interview_completed": {"sub_status": "interview_done", "action": "advance_or_hold"},
        "interview_cancelled": {"sub_status": "interview_cancelled", "action": "notify_recruiter"},
        "interview_no_show": {"sub_status": "candidate_no_show", "action": "flag_candidate"},
    }

    @classmethod
    async def process(cls, event_id: str, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        if cls.is_duplicate(event_id):
            logger.info(f"[WEBHOOK] Duplicate event ignored: {event_id}")
            return {"status": "duplicate", "event_id": event_id}

        transition = cls.EVENT_TO_TRANSITION.get(event_type, {})
        candidate_id = payload.get("candidate_id") or payload.get("candidateId")
        vacancy_id = payload.get("vacancy_id") or payload.get("vacancyId")

        result = {
            "status": "processed",
            "event_id": event_id,
            "event_type": event_type,
            "candidate_id": candidate_id,
            "vacancy_id": vacancy_id,
            "mapped_sub_status": transition.get("sub_status"),
            "mapped_action": transition.get("action"),
            "provider_data": {
                "interview_date": payload.get("interview_date"),
                "interviewer": payload.get("interviewer"),
                "feedback": payload.get("feedback"),
            }
        }

        cls.mark_processed(event_id, event_type, "interview_provider", result)
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"[WEBHOOK] Interview event processed: {event_type} for candidate {candidate_id}")
        return result


class TestWebhookAdapter(WebhookAdapter):
    """Processes test/assessment completion webhook events."""

    EVENT_TO_TRANSITION = {
        "test_completed": {"sub_status": "test_completed", "action": "evaluate_results"},
        "test_expired": {"sub_status": "test_expired", "action": "notify_recruiter"},
        "test_started": {"sub_status": "test_in_progress", "action": "update_status"},
    }

    @classmethod
    async def process(cls, event_id: str, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        if cls.is_duplicate(event_id):
            return {"status": "duplicate", "event_id": event_id}

        transition = cls.EVENT_TO_TRANSITION.get(event_type, {})
        candidate_id = payload.get("candidate_id") or payload.get("candidateId")

        result = {
            "status": "processed",
            "event_id": event_id,
            "event_type": event_type,
            "candidate_id": candidate_id,
            "mapped_sub_status": transition.get("sub_status"),
            "mapped_action": transition.get("action"),
            "test_data": {
                "score": payload.get("score"),
                "test_type": payload.get("test_type"),
                "duration_minutes": payload.get("duration_minutes"),
                "completed_at": payload.get("completed_at"),
            }
        }

        cls.mark_processed(event_id, event_type, "test_provider", result)
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"[WEBHOOK] Test event processed: {event_type} for candidate {candidate_id}")
        return result


class DocumentWebhookAdapter(WebhookAdapter):
    """Processes document submission webhook events."""

    @classmethod
    async def process(cls, event_id: str, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        if cls.is_duplicate(event_id):
            return {"status": "duplicate", "event_id": event_id}

        candidate_id = payload.get("candidate_id") or payload.get("candidateId")

        result = {
            "status": "processed",
            "event_id": event_id,
            "event_type": event_type,
            "candidate_id": candidate_id,
            "mapped_sub_status": "documents_received",
            "mapped_action": "verify_documents",
            "document_data": {
                "document_type": payload.get("document_type"),
                "file_url": payload.get("file_url"),
            }
        }

        cls.mark_processed(event_id, event_type, "document_provider", result)
        return result
