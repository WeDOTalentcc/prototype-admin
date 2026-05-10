"""
Sector Templates API — endpoints for listing and applying sector templates.

Extends the existing agent_templates_api.py (Stage 8) with sector-specific routes.
Does NOT duplicate CRUD endpoints — those are in agent_templates_api.py.

Apply to: lia-agent-system/app/api/v1/sector_templates.py
Register: app.include_router(sector_templates_router)
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import get_current_user
from app.core.database import get_db
from pydantic import BaseModel
from typing import Optional

router = APIRouter(tags=["Agent Studio — Sector Templates"])


class SectorTemplateSummary(BaseModel):
    id: str
    display_name: str
    description: str
    icon: str


class ApplySectorRequest(BaseModel):
    agent_name: Optional[str] = None  # override name; defaults to template display_name
    company_context: Optional[str] = None  # e.g. "Empresa de logística com foco em CLT"


class ApplySectorResponse(BaseModel):
    template_id: str
    name: str
    domain: str
    status: str
    screening_questions: list
    message: str


@router.get("/agent-templates/sectors", response_model=list[SectorTemplateSummary])
async def list_sector_templates():
    """List available sector templates for the Agent Studio gallery."""
    from app.shared.agent_templates.sector_templates import list_templates
    return list_templates()


@router.post("/agent-templates/sectors/{sector}/apply", response_model=ApplySectorResponse)
async def apply_sector_template(
    sector: str,
    body: ApplySectorRequest = ApplySectorRequest(),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Instantiate a sector template as an AgentTemplate for the current tenant.

    Creates a DRAFT AgentTemplate with the sector's system_prompt_yaml,
    screening questions, and default config. Recruiter can edit before publishing.
    """
    from app.shared.agent_templates.sector_templates import get_template

    try:
        template = get_template(sector)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Sector '{sector}' não encontrado")

    # Build the AgentTemplate record using the Stage 8 model
    from lia_models.agent_template import AgentTemplate

    template_id = str(uuid.uuid4())
    name = body.agent_name or f"Agente {template['display_name']}"

    # Append company context to the YAML if provided
    yaml_content = template["system_prompt_yaml"]
    if body.company_context:
        yaml_content = yaml_content.rstrip() + f"\n  Contexto da empresa: {body.company_context}\n"

    agent_template = AgentTemplate(
        id=template_id,
        company_id=current_user.get("company_id", "unknown"),
        name=name,
        domain=template["domain"],
        system_prompt_yaml=yaml_content,
        version=1,
        status="draft",
        created_by=current_user.get("user_id", "system"),
        created_at=datetime.utcnow(),
    )

    db.add(agent_template)
    await db.commit()

    return ApplySectorResponse(
        template_id=template_id,
        name=name,
        domain=template["domain"],
        status="draft",
        screening_questions=template.get("screening_questions", []),
        message=f"Template '{template['display_name']}' aplicado. Edite e publique quando pronto.",
    )
