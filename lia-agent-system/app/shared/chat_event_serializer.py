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
from typing import Any, Literal, NotRequired, TypedDict


# ---------------------------------------------------------------------------
# TypedDicts — typed event envelopes (R-042)
# ---------------------------------------------------------------------------

class ThinkingEvent(TypedDict):
    type: Literal["thinking"]
    content: str
    step: int


class TokenEvent(TypedDict):
    type: Literal["token"]
    content: str


class TokenDoneEvent(TypedDict):
    type: Literal["token_done"]
    tokens_sent: int


class MessageEvent(TypedDict):
    type: Literal["message"]
    content: str
    confidence: float
    domain: str
    source: str
    actions: NotRequired[list]
    navigation: NotRequired[dict]
    state_updates: NotRequired[dict]
    fairness_warnings: NotRequired[list]
    execution_plan: NotRequired[dict]
    conversation_id: NotRequired[str]
    ws_stage_payload: NotRequired[dict]


class ErrorEvent(TypedDict):
    type: Literal["error"]
    message: str
    error_code: NotRequired[str]


class PanelUpdateEvent(TypedDict):
    type: Literal["panel_update"]
    panel_type: str
    panel_data: dict[str, Any]
    panel_title: str
    action: str


class BackgroundTaskUpdateEvent(TypedDict):
    type: Literal["background_task_update"]
    task_id: str
    task_type: str
    label: str
    status: str
    progress: NotRequired[int]
    message: NotRequired[str]
    result: NotRequired[dict[str, Any]]


class ConnectedEvent(TypedDict):
    type: Literal["connected"]
    session_id: str
    domain: str


# Union of all known event types
ChatEvent = (
    ThinkingEvent
    | TokenEvent
    | TokenDoneEvent
    | MessageEvent
    | ErrorEvent
    | PanelUpdateEvent
    | BackgroundTaskUpdateEvent
    | ConnectedEvent
)


_EVENT_COUNTER = 0


def _next_event_id() -> str:
    global _EVENT_COUNTER
    _EVENT_COUNTER += 1
    return f"{int(time.time() * 1000)}-{_EVENT_COUNTER}"


def serialize_event(event_type: str, **kwargs: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"type": event_type}
    payload.update({k: v for k, v in kwargs.items() if v is not None})
    return payload


def serialize_thinking(content: str = "", step: int = 0) -> ThinkingEvent:
    return serialize_event("thinking", content=content, step=step)  # type: ignore[return-value]


def serialize_token(content: str) -> TokenEvent:
    return serialize_event("token", content=content)  # type: ignore[return-value]


def serialize_token_done(tokens_sent: int = 0) -> TokenDoneEvent:
    return serialize_event("token_done", tokens_sent=tokens_sent)  # type: ignore[return-value]


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
    tool_results: list | None = None,
    response_blocks: list | None = None,
    ui_action: str | None = None,
    ui_action_params: dict | None = None,
    ws_stage_payload: dict | None = None,
) -> MessageEvent:
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
    # PR6 (Task #1006) — Bridge IA→UI: surface tool execution metadata
    # (tool_name, success, section?) so the frontend WS consumer can dispatch
    # `lia:settings-updated` CustomEvent for canonical save tools without
    # introducing a new frame type. Additive field; existing consumers ignore.
    if tool_results:
        payload["tool_results"] = tool_results
    if response_blocks:
        payload["response_blocks"] = response_blocks
    # FIX-NAVIGATE-LEAK (Fase 0): contrato de navegacao do FE = ui_action/
    # ui_action_params (useChatSocket/useChatMessages PR-D). Paridade c/ orquestrador.
    if ui_action:
        payload["ui_action"] = ui_action
    if ui_action_params:
        payload["ui_action_params"] = ui_action_params
    # Task #1090 — wizard side-panel signal (canonical-fix: produtor unico).
    # O orchestrator empacota ws_stage_payload (type=wizard_stage, thread_id,
    # stage, **payload) em structured_data. Anexa-lo aqui garante paridade de
    # transporte: WS, REST (message_metadata) e SSE carregam o MESMO sinal e o
    # FE abre o painel. Aditivo; consumidores antigos ignoram o campo extra.
    if ws_stage_payload:
        payload["ws_stage_payload"] = ws_stage_payload
    return payload  # type: ignore[return-value]


def serialize_error(message: str, error_code: str = "") -> ErrorEvent:
    payload = serialize_event("error", message=message)
    if error_code:
        payload["error_code"] = error_code
    return payload  # type: ignore[return-value]


def serialize_panel_update(
    panel_type: str,
    panel_data: dict[str, Any],
    panel_title: str = "",
    action: str = "open",
    thread_id: str | None = None,
    completeness: float | None = None,
) -> PanelUpdateEvent:
    # thread_id + completeness sao opcionais e so aparecem no frame quando
    # fornecidos (serialize_event descarta None). Necessarios para o wizard:
    # o FE deduplica panel_update(wizard_stage) por chave
    # thread_id:stage:completeness; sem eles, dois turnos do MESMO stage
    # colapsam na mesma chave e a ponte que injeta o stage e suprimida no 2o
    # turno -> painel do wizard fecha. Ver fix 2026-06-05.
    return serialize_event(
        "panel_update",
        panel_type=panel_type,
        panel_data=panel_data,
        panel_title=panel_title,
        action=action,
        thread_id=thread_id,
        completeness=completeness,
    )


def serialize_background_task_update(
    task_id: str,
    task_type: str,
    label: str,
    status: str,
    progress: int | None = None,
    message: str = "",
    result: dict[str, Any] | None = None,
) -> BackgroundTaskUpdateEvent:
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


def serialize_tool_started(
    name: str, args: str = "", tool_id: str = ""
) -> dict[str, Any]:
    return serialize_event(
        "tool_started", name=name, args=args or None, tool_id=tool_id or None
    )


def serialize_tool_finished(
    name: str,
    status: str = "ok",
    duration_ms: int | None = None,
    result: str = "",
    tool_id: str = "",
) -> dict[str, Any]:
    return serialize_event(
        "tool_finished",
        name=name,
        status=status,
        duration_ms=duration_ms,
        result=result or None,
        tool_id=tool_id or None,
    )


def serialize_reasoning_step(label: str, detail: str = "") -> dict[str, Any]:
    return serialize_event("reasoning_step", label=label, detail=detail or None)


def serialize_connected(session_id: str, domain: str = "") -> ConnectedEvent:
    return serialize_event("connected", session_id=session_id, domain=domain)


def format_sse_event(data: dict[str, Any], event_id: str | None = None) -> str:
    eid = event_id or _next_event_id()
    json_str = json.dumps(data, ensure_ascii=False)
    return f"id: {eid}\ndata: {json_str}\n\n"


def format_sse_keepalive() -> str:
    return ": keepalive\n\n"


def serialize_keepalive() -> str:
    """Emite evento SSE data: de keepalive com JSON.

    Retorna um evento JSON data: {"type": "keepalive", "ts": <timestamp>}
    para compatibilidade com clientes que filtram apenas eventos data:.
    Retrocompat: format_sse_keepalive() continua retornando SSE comment.
    """
    payload = json.dumps({"type": "keepalive", "ts": int(time.time())})
    return f"data: {payload}\n\n"
