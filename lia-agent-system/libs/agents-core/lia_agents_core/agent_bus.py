"""Backwards-compatibility shim — canonical implementation in app.shared.agents.agent_bus."""
from app.shared.agents.agent_bus import *  # noqa: F401, F403
from app.shared.agents.agent_bus import AgentEvent, AgentBus, CHANNEL_PREFIX  # noqa: F401
