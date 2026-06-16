import logging
import os

from fastapi import APIRouter, HTTPException, Request
from lia_agents_core.agent_interface import AgentInput

from app.domains.cv_screening.agents.pipeline_react_agent import PipelineReActAgent
from fastapi import Depends
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger("lia.pipeline_orchestrator")
router = APIRouter(prefix="/pipeline", tags=["Pipeline Agent"])


@router.post("/react-orchestrate", response_model=None)
async def pipeline_react_orchestrate(request: Request, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Pipeline agent endpoint - ReAct based autonomous candidate management."""
    if not os.getenv("USE_REACT_AGENTS", "false").lower() == "true":
        return {"error": "ReAct agents not enabled", "detail": "Set USE_REACT_AGENTS=true"}

    user_id = getattr(request.state, "user_id", None)
    company_id = getattr(request.state, "company_id", None)
    if not user_id or not company_id:
        raise HTTPException(status_code=401, detail="Authentication required: missing user or company context")

    try:
        body = await request.json()
        agent_input = AgentInput(
            message=body.get("message", ""),
            session_id=body.get("session_id", "default"),
            company_id=company_id,
            user_id=user_id,
            context=body.get("context", {}),
        )

        # FairnessGuard: bloquear inputs discriminatórios antes do agente
        from app.shared.compliance.fairness_guard import FairnessGuard
        _fg_po = FairnessGuard()
        _fr_po = _fg_po.check(body.get("message", ""))
        if _fr_po and _fr_po.is_blocked:
            import asyncio as _asyncio
            try:
                _asyncio.get_event_loop().create_task(
                    _fg_po.log_check(
                        result=_fr_po,
                        context="pipeline_orchestrator",
                        company_id=company_id or None,
                        recruiter_id=user_id or None,
                    )
                )
            except Exception:
                pass
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "fairness_blocked",
                    "fairness_blocked": True,
                    "educational_message": _fr_po.educational_message,
                    "category": _fr_po.category,
                },
            )

        agent = PipelineReActAgent()
        output = await agent.process(agent_input)

        return {
            "message": output.message,
            "confidence": output.confidence,
            "navigation": {"target_stage": output.navigation.target_stage, "auto_navigate": output.navigation.auto_navigate} if output.navigation else None,
            "actions": [{"type": a.action_type, "data": a.params} for a in output.actions] if output.actions else [],
            "metadata": output.metadata or {},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pipeline ReAct error: {e}", exc_info=True)
        return {"message": "Desculpe, ocorreu um erro ao processar sua solicitação. Tente novamente.", "confidence": 0, "error": str(e)}
