from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import Any


class ChannelType(StrEnum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    IN_APP = "in_app"
    MS_TEAMS = "ms_teams"
    VOICE = "voice"  # Sprint 3.4 W4-1 V2: Twilio PSTN/VoIP + Gemini Live, unified


class DeliveryStatus(StrEnum):
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    BOUNCED = "bounced"


@dataclass
class ChannelMessage:
    recipient_id: str
    recipient_name: str
    recipient_contact: str
    subject: str | None = None
    body_text: str = ""
    body_html: str | None = None
    template_id: str | None = None
    template_vars: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    company_id: str = ""
    vacancy_id: str | None = None


@dataclass
class DeliveryResult:
    success: bool
    channel: ChannelType
    message_id: str
    status: DeliveryStatus
    provider_id: str | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = field(default_factory=dict)


class ChannelAdapter(ABC):
    channel_type: ChannelType

    @abstractmethod
    async def send(self, message: ChannelMessage) -> DeliveryResult:
        ...

    @abstractmethod
    async def check_status(self, message_id: str) -> DeliveryStatus:
        ...

    @abstractmethod
    async def is_available(
        self,
        company_id: str | None = None,
        db: "Any | None" = None,
    ) -> bool:
        ...

    @abstractmethod
    def validate_contact(self, contact: str) -> bool:
        ...
