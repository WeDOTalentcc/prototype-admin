from fastapi import APIRouter, Request
from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
from lia_agents_core.agent_interface import AgentInput
import logging
import os

logger = logging.getLogger("lia.sourcing_orchestrator")
router = APIRouter(prefix="/sourcing", tags=["Sourcing Agent"])


@router.post("/react-orchestrate")
async def sourcing_react_orchestrate(request: Request):
    """Sourcing agent endpoint - ReAct based autonomous talent sourcing."""
    if not os.getenv("USE_REACT_AGENTS", "false").lower() == "true":
        return {"error": "ReAct agents not enabled", "detail": "Set USE_REACT_AGENTS=true"}

    try:
        body = await request.json()
        agent_input = AgentInput(
            message=body.get("message", ""),
            session_id=body.get("session_id", "default"),
            company_id=body.get("company_id", "demo"),
            user_id=body.get("user_id", "demo-user"),
            context=body.get("context", {}),
        )

        agent = SourcingReActAgent()
        output = await agent.process(agent_input)

        return {
            "message": output.message,
            "confidence": output.confidence,
            "navigation": {"target_stage": output.navigation.target_stage, "auto_navigate": output.navigation.auto_navigate} if output.navigation else None,
            "actions": [{"type": a.action_type, "data": a.params} for a in output.actions] if output.actions else [],
            "metadata": output.metadata or {},
        }
    except Exception as e:
        logger.error(f"Sourcing ReAct error: {e}", exc_info=True)
        return {"message": "Desculpe, ocorreu um erro ao processar sua solicitação. Tente novamente.", "confidence": 0, "error": str(e)}
