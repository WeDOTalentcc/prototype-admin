"""
WebSocket manager shim -- actual implementation moved to app/shared/websocket/ws_manager.py
to avoid circular imports (domain->api).
Re-exported here for backwards compatibility.
"""
from app.shared.websocket.ws_manager import WSManager, ws_manager, get_ws_manager  # noqa: F401
