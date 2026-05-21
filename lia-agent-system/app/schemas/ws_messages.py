"""
LIA-E05: Standard WebSocket Message Envelope

Provides a consistent envelope for WebSocket messages across chat, notifications,
and voice channels. Endpoints can opt-in gradually — existing raw dict messages
continue to work.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class WSMessageType(str, Enum):
    # User-initiated
    USER_MESSAGE = "user.message"
    USER_TYPING = "user.typing"
    USER_READ = "user.read"

    # Assistant-initiated
    ASSISTANT_MESSAGE = "assistant.message"
    ASSISTANT_TYPING = "assistant.typing"
    ASSISTANT_ACTION = "assistant.action"

    # System
    SYSTEM_STATUS = "system.status"
    SYSTEM_ERROR = "system.error"
    SYSTEM_NOTIFICATION = "system.notification"

    # Streaming
    STREAM_START = "stream.start"
    STREAM_CHUNK = "stream.chunk"
    STREAM_END = "stream.end"


class WSMessage(BaseModel):
    model_config = ConfigDict(extra='forbid')

    """Standard WebSocket message envelope.

    All WS messages SHOULD conform to this shape:
        {"type": "user.message", "timestamp": "...", "payload": {...}, "metadata": {...}}
    """
    type: Union[WSMessageType, str]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)
    session_id: Optional[str] = None
    request_id: Optional[str] = None

    @classmethod
    def user_message(cls, content: str, **kwargs) -> "WSMessage":
        return cls(type=WSMessageType.USER_MESSAGE, payload={"content": content}, **kwargs)

    @classmethod
    def assistant_message(cls, content: str, **kwargs) -> "WSMessage":
        return cls(type=WSMessageType.ASSISTANT_MESSAGE, payload={"content": content}, **kwargs)

    @classmethod
    def error(cls, message: str, code: str = "error", **kwargs) -> "WSMessage":
        return cls(type=WSMessageType.SYSTEM_ERROR, payload={"message": message, "code": code}, **kwargs)
