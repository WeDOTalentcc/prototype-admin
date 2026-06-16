"""
Communication service enums and constants.

Centralizes magic strings used across communication services and orchestrators.
"""
from enum import StrEnum


class MessageType(StrEnum):
    """Types of messages that can be sent."""
    INITIAL_CONTACT = "initial_contact"
    SCREENING_INVITATION = "screening_invitation"
    SCREENING_REMINDER = "screening_reminder"
    SCREENING_PASSED = "screening_passed"
    SCREENING_FAILED = "screening_failed"
    INTERVIEW_INVITE = "interview_invite"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_REMINDER = "interview_reminder"
    INTERVIEW_CONFIRMATION = "interview_confirmation"
    INTERVIEW_CONFIRMED = "interview_confirmed"
    REJECTION_FEEDBACK = "rejection_feedback"
    PROCESS_CLOSED = "process_closed"
    OFFER = "offer"
    GENERAL = "general"


class MessageChannel(StrEnum):
    """Communication channels."""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    SMS = "sms"


class ApprovalStatus(StrEnum):
    """Status of approval requests."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    AUTO_APPROVED = "auto_approved"


class CommunicationStatus(StrEnum):
    """Status of sent communications."""
    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    BOUNCED = "bounced"
    BLOCKED = "blocked"


class TemplateSituation(StrEnum):
    """
    Template situation identifiers stored in EmailTemplate.situation.

    These map from MessageType (via MESSAGE_TYPE_TO_SITUATION) to the DB field
    used to look up active email templates.
    """
    INITIAL_CONTACT = "initial_contact"
    TRIAGEM = "triagem"
    SCREENING_REMINDER = "screening_reminder"
    SCREENING_PASSED = "screening_passed"
    SCREENING_FAILED = "screening_failed"
    INTERVIEW_INVITE = "interview_invite"
    INTERVIEW_REMINDER = "interview_reminder"
    INTERVIEW_CONFIRMED = "interview_confirmed"
    REJEICAO = "rejeicao"
    PROCESS_CLOSED = "process_closed"
    PROPOSTA = "proposta"


class ABTestName(StrEnum):
    """A/B test identifiers used by ABTestingService."""
    SCREENING_INVITE = "email_screening_invite"
    FOLLOW_UP_REMINDER = "email_follow_up_reminder"
    FEEDBACK_REJECTION = "email_feedback_rejection"


MESSAGE_TYPE_TO_SITUATION: dict[MessageType, TemplateSituation | None] = {
    MessageType.INTERVIEW_INVITE: TemplateSituation.INTERVIEW_INVITE,
    MessageType.INTERVIEW_CONFIRMED: TemplateSituation.INTERVIEW_CONFIRMED,
    MessageType.INTERVIEW_SCHEDULED: TemplateSituation.INTERVIEW_INVITE,
    MessageType.INTERVIEW_REMINDER: TemplateSituation.INTERVIEW_REMINDER,
    MessageType.INTERVIEW_CONFIRMATION: TemplateSituation.INTERVIEW_CONFIRMED,
    MessageType.INITIAL_CONTACT: TemplateSituation.INITIAL_CONTACT,
    MessageType.SCREENING_INVITATION: TemplateSituation.TRIAGEM,
    MessageType.SCREENING_REMINDER: TemplateSituation.SCREENING_REMINDER,
    MessageType.SCREENING_PASSED: TemplateSituation.SCREENING_PASSED,
    MessageType.SCREENING_FAILED: TemplateSituation.SCREENING_FAILED,
    MessageType.REJECTION_FEEDBACK: TemplateSituation.REJEICAO,
    MessageType.PROCESS_CLOSED: TemplateSituation.PROCESS_CLOSED,
    MessageType.OFFER: TemplateSituation.PROPOSTA,
    MessageType.GENERAL: None,
}
