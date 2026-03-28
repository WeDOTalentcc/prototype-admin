from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class ChannelType(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    IN_APP = "in_app"
    MS_TEAMS = "ms_teams"


class DeliveryStatus(str, Enum):
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
    subject: Optional[str] = None
    body_text: str = ""
    body_html: Optional[str] = None
    template_id: Optional[str] = None
    template_vars: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    company_id: str = ""
    vacancy_id: Optional[str] = None


@dataclass
class DeliveryResult:
    success: bool
    channel: ChannelType
    message_id: str
    status: DeliveryStatus
    provider_id: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)


class ChannelAdapter(ABC):
    channel_type: ChannelType

    @abstractmethod
    async def send(self, message: ChannelMessage) -> DeliveryResult:
        ...

    @abstractmethod
    async def check_status(self, message_id: str) -> DeliveryStatus:
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        ...

    @abstractmethod
    def validate_contact(self, contact: str) -> bool:
        ...
