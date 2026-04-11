"""
Shared Chat Event Serializer — unified event format for WS and SSE transports.

Both WebSocket and SSE endpoints use this module to serialize events,
ensuring the same message structure reaches the frontend regardless of transport.

Event types:
  - thinking: agent started processing
  - token: streaming token chunk
  - token_done: streaming complete
  - message: final response
  - panel_update: UI panel command
  - background_task_update: async task progress
  - error: error notification
  - connected: connection established
  - pong: keep-alive response
  - approval_required: HITL approval request
  - approval_confirmed: HITL approval ack
  - clarification: domain routing needs input
  - plan_progress: multi-step plan progress
"""
import json
import time
from typing import Any


_EVENT_COUNTER = 0


def _next_event_id() -> str:
    global _EVENT_COUNTER
    _EVENT_COUNTER += 1
    return f"{int(time.time() * 1000)}-{_EVENT_COUNTER}"


def serialize_event(event_type: str, **kwargs: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"type": event_type}
    payload.update({k: v for k, v in kwargs.items() if v is not None})
    return payload


def serialize_thinking(content: str = "", step: int = 0) -> dict[str, Any]:
    return serialize_event("thinking", content=content, step=step)


def serialize_token(content: str) -> dict[str, Any]:
    return serialize_event("token", content=content)


def serialize_token_done(tokens_sent: int = 0) -> dict[str, Any]:
    return serialize_event("token_done", tokens_sent=tokens_sent)


def serialize_message(
    content: str,
    confidence: float = 0.0,
    domain: str = "",
    source: str = "direct",
    actions: list | None = None,
    navigation: dict | None = None,
    state_updates: dict | None = None,
    fairness_warnings: list | None = None,
    execution_plan: dict | None = None,
    conversation_id: str | None = None,
) -> dict[str, Any]:
    payload = serialize_event(
        "message",
        content=content,
        confidence=confidence,
        domain=domain,
        source=source,
    )
    if actions:
        payload["actions"] = actions
    if navigation:
        payload["navigation"] = navigation
    if state_updates:
        payload["state_updates"] = state_updates
    if fairness_warnings:
        payload["fairness_warnings"] = fairness_warnings
    if execution_plan:
        payload["execution_plan"] = execution_plan
    if conversation_id:
        payload["conversation_id"] = conversation_id
    return payload


def serialize_error(message: str, error_code: str = "") -> dict[str, Any]:
    payload = serialize_event("error", message=message)
    if error_code:
        payload["error_code"] = error_code
    return payload


def serialize_panel_update(
    panel_type: str,
    panel_data: dict[str, Any],
    panel_title: str = "",
    action: str = "open",
) -> dict[str, Any]:
    return serialize_event(
        "panel_update",
        panel_type=panel_type,
        panel_data=panel_data,
        panel_title=panel_title,
        action=action,
    )


def serialize_background_task_update(
    task_id: str,
    task_type: str,
    label: str,
    status: str,
    progress: int | None = None,
    message: str = "",
    result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return serialize_event(
        "background_task_update",
        task_id=task_id,
        task_type=task_type,
        label=label,
        status=status,
        progress=progress,
        message=message or None,
        result=result,
    )


def serialize_connected(session_id: str, domain: str = "") -> dict[str, Any]:
    return serialize_event("connected", session_id=session_id, domain=domain)


def format_sse_event(data: dict[str, Any], event_id: str | None = None) -> str:
    eid = event_id or _next_event_id()
    json_str = json.dumps(data, ensure_ascii=False)
    return f"id: {eid}\ndata: {json_str}\n\n"


def format_sse_keepalive() -> str:
    return ": keepalive\n\n"
