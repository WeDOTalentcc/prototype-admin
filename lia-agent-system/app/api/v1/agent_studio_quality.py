"""
Agent Studio Quality Floor — templates, quality gate, quality score.

Endpoints:
  GET  /agent-studio/templates — list available templates
  POST /agent-studio/{agent_id}/evaluate — run quality gate
  GET  /agent-studio/{agent_id}/quality-score — compute quality score

Item: PX08 — Sprint 12, item 12.6
"""
import logging
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.shared.security.require_company_id import require_company_id
from typing import Annotated
from fastapi import Path as FastAPIPath
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-studio", tags=["Agent Studio Quality"])

_TEMPLATES_PATH = Path(__file__).resolve().parent.parent.parent / "app" / "config" / "agent_templates" / "templates.yaml"


# ── Schemas ──────────────────────────────────────────────────────

class TemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    icon: str
    system_prompt: str
    recommended_tools: list[str]
    config: dict[str, Any]


class QualityScoreResponse(BaseModel):
    agent_id: str
    overall_score: float
    quality_level: str
    passed: bool
    dimensions: list[dict[str, Any]]
    suggestions: list[str]


# ── Templates endpoint ───────────────────────────────────────────

@router.get("/templates", response_model=list[TemplateResponse])
async def list_templates(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List available agent templates. Recruiter picks one as starting point."""
    try:
        # Try multiple paths (dev vs production)
        paths = [
            _TEMPLATES_PATH,
            Path(__file__).resolve().parent.parent / "config" / "agent_templates" / "templates.yaml",
        ]
        data = None
        for p in paths:
            if p.exists():
                with open(p) as f:
                    data = yaml.safe_load(f)
                break

        if not data:
            return []

        return [
            TemplateResponse(
                id=t["id"],
                name=t["name"],
                description=t["description"],
                category=t["category"],
                icon=t.get("icon", "🤖"),
                system_prompt=t["system_prompt"],
                recommended_tools=t.get("recommended_tools", []),
                config=t.get("config", {}),
            )
            for t in data.get("templates", [])
        ]
    except Exception as exc:
        logger.error("[AgentStudioQuality] Failed to load templates: %s", exc)
        return []


# ── Quality Score endpoint ───────────────────────────────────────

@router.get("/{agent_id}/quality-score", response_model=QualityScoreResponse)
async def get_quality_score(
    agent_id: Annotated[str, FastAPIPath(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Compute quality score for a custom agent."""
    from uuid import UUID
    from lia_models.custom_agent import CustomAgent
    from app.services.agent_quality_gate import compute_quality_score

    company_id = str(current_user.company_id)

    result = await db.execute(
        select(CustomAgent).where(
            CustomAgent.id == UUID(agent_id),
            CustomAgent.company_id == company_id,
        )
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agente nao encontrado")

    gate_result = compute_quality_score(
        system_prompt=agent.system_prompt or "",
        allowed_tools=agent.allowed_tools or [],
        domain=agent.domain or "general",
        max_steps=agent.max_steps or 8,
        temperature=agent.temperature or 0.7,
        enable_memory=agent.enable_memory if agent.enable_memory is not None else True,
    )
    gate_result.agent_id = agent_id

    return QualityScoreResponse(
        agent_id=agent_id,
        overall_score=gate_result.overall_score,
        quality_level=gate_result.quality_level,
        passed=gate_result.passed,
        dimensions=[
            {"name": d.name, "score": round(d.score, 2), "feedback": d.feedback}
            for d in gate_result.dimensions
        ],
        suggestions=gate_result.suggestions,
    )

reorder_collection_before_item(router)
