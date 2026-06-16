"""
Sprint 1A.2-1.7 — publish_node Rails integration.

ONDE APLICAR: app/domains/job_creation/nodes/publish_node.py
AÇÃO: Substituir o publish_node atual por esta versão que integra com Rails.

Este é o nó mais crítico — sem ele, o job nunca é criado no banco real.
"""

import os
import httpx
import logging
from typing import Any

logger = logging.getLogger(__name__)

RAILS_BACKEND_URL = os.getenv("RAILS_BACKEND_URL", "http://localhost:3000")


async def _call_rails(
    method: str,
    path: str,
    company_id: int,
    auth_token: str,
    json_data: dict | None = None,
) -> dict:
    """Call Rails API with tenant context (Apartment gem)."""
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
        "X-Company-ID": str(company_id),  # Multi-tenancy: Apartment gem
    }
    url = f"{RAILS_BACKEND_URL}{path}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        if method == "POST":
            resp = await client.post(url, json=json_data, headers=headers)
        elif method == "PATCH":
            resp = await client.patch(url, json=json_data, headers=headers)
        else:
            resp = await client.get(url, headers=headers)

        resp.raise_for_status()
        return resp.json()


async def publish_node(state: dict, config: dict) -> dict:
    """
    Publish node — creates job in Rails, creates campaign,
    triggers screening pipeline and automations.

    Flow:
    1. Create job in Rails (POST /v1/users/jobs)
    2. Create RecruitmentCampaign (POST /v1/users/recruitment_campaigns)
    3. Trigger WSIScreeningPipeline
    4. Trigger RecruitmentAutomation (job_published)
    5. Broadcast via ActionCable
    6. Send wizard_stage "publish" with job_id + share_link
    """
    # Extract context
    company_id = state.get("company_id")
    auth_token = state.get("auth_token", "")
    ws_send = state.get("ws_send")  # WebSocket sender function

    # Extract wizard data
    enriched_jd = state.get("jd_enriched", {})
    questions = state.get("approved_questions", [])
    eligibility = state.get("eligibility_questions", [])
    seniority = state.get("seniority", "pleno")
    screening_mode = state.get("screening_mode", "compact")
    platforms = state.get("platforms", ["website"])
    auto_screen = state.get("auto_screen", True)
    salary_min = state.get("salary_min")
    salary_max = state.get("salary_max")

    # --- Step 1: Send progress WS ---
    if ws_send:
        await ws_send({
            "type": "wizard_stage",
            "stage": "publish",
            "data": {"progress": "Criando vaga..."},
            "completeness": 0.85,
            "requires_approval": False,
        })

    # --- Step 2: Create job in Rails ---
    job_payload = {
        "job": {
            "title": enriched_jd.get("titulo_padronizado", "Nova Vaga"),
            "description": enriched_jd.get("about_role", ""),
            "seniority_level": seniority,
            "technical_requirements": [s.get("skill", "") for s in enriched_jd.get("skills_obrigatorias", [])],
            "behavioral_competencies": [c.get("competencia", "") for c in enriched_jd.get("competencias_comportamentais", [])],
            "screening_questions": [q.get("question", "") for q in questions],
            "published_linkedin": "linkedin" in platforms,
            "published_indeed": "indeed" in platforms,
            "published_website": "website" in platforms,
            "status": "published",
        }
    }
    if salary_min:
        job_payload["job"]["budget"] = salary_max or salary_min

    try:
        rails_job = await _call_rails("POST", "/v1/users/jobs", company_id, auth_token, job_payload)
        job_id = rails_job.get("data", {}).get("id") or rails_job.get("id")
        logger.info(f"Job created in Rails: {job_id}")
    except Exception as e:
        logger.error(f"Failed to create job in Rails: {e}")
        state["error"] = f"Erro ao criar vaga no sistema: {e}"
        return state

    # --- Step 3: Progress WS ---
    if ws_send:
        await ws_send({
            "type": "wizard_stage",
            "stage": "publish",
            "data": {"progress": "Criando campanha de recrutamento..."},
            "completeness": 0.88,
            "requires_approval": False,
        })

    # --- Step 4: Create RecruitmentCampaign in Rails ---
    campaign_payload = {
        "recruitment_campaign": {
            "name": f"Campanha - {enriched_jd.get('titulo_padronizado', 'Vaga')}",
            "job_id": job_id,
            "current_stage": "definition",
            "automation_level": "semi",
            "status": "active",
            "stages_config": {
                "screening_mode": screening_mode,
                "auto_screen": auto_screen,
                "question_count": len(questions),
            },
        }
    }

    campaign_id = None
    try:
        rails_campaign = await _call_rails("POST", "/v1/users/recruitment_campaigns", company_id, auth_token, campaign_payload)
        campaign_id = rails_campaign.get("data", {}).get("id") or rails_campaign.get("id")
        logger.info(f"Campaign created in Rails: {campaign_id}")
    except Exception as e:
        logger.warning(f"Failed to create campaign in Rails: {e}")

    # --- Step 5: Progress WS ---
    if ws_send:
        await ws_send({
            "type": "wizard_stage",
            "stage": "publish",
            "data": {"progress": "Ativando screening automatico..."},
            "completeness": 0.92,
            "requires_approval": False,
        })

    # --- Step 6: Trigger WSIScreeningPipeline ---
    if auto_screen and questions:
        try:
            from app.domains.cv_screening.services.wsi_screening_pipeline import WSIScreeningPipeline
            pipeline = WSIScreeningPipeline.build_pipeline(
                job_id=job_id,
                questions=questions,
                eligibility_questions=eligibility,
                screening_mode=screening_mode,
                seniority=seniority,
            )
            logger.info(f"WSI Screening Pipeline activated for job {job_id}")
        except ImportError:
            logger.warning("WSIScreeningPipeline not found — screening not activated")
        except Exception as e:
            logger.warning(f"Failed to activate screening pipeline: {e}")

    # --- Step 7: Trigger RecruitmentAutomation (job_published) ---
    try:
        await _call_rails(
            "POST",
            f"/v1/users/recruitment_campaigns/{campaign_id}/add_checkpoint",
            company_id,
            auth_token,
            {
                "message": "Vaga publicada via Wizard WSI",
                "candidates_count": 0,
            },
        )
    except Exception as e:
        logger.warning(f"Failed to add campaign checkpoint: {e}")

    # --- Step 7b: ActionCable broadcast + StageAutomation ---
    try:
        from wizard_wsi_patches.sprint_2b.actioncable_broadcast_patch import (
            broadcast_campaign_update,
            trigger_stage_automation,
        )
        if campaign_id:
            await broadcast_campaign_update(campaign_id, company_id, auth_token)
        await trigger_stage_automation(job_id, company_id, auth_token)
    except ImportError:
        # Fallback: call Rails directly if patch module not available
        if campaign_id:
            try:
                await _call_rails("POST", f"/v1/users/recruitment_campaigns/{campaign_id}/advance_stage", company_id, auth_token)
            except Exception:
                pass
    except Exception as e:
        logger.warning(f"Broadcast/automation failed (non-blocking): {e}")

    # --- Step 7c: SLA tracking ---
    try:
        from wizard_wsi_patches.sprint_4.backend_integrations import create_recruitment_sla
        if campaign_id:
            await create_recruitment_sla(campaign_id, company_id, auth_token)
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"SLA creation failed (non-blocking): {e}")

    # --- Step 8: Generate share link ---
    public_slug = enriched_jd.get("titulo_padronizado", "vaga").lower().replace(" ", "-")
    share_link = f"{os.getenv('FRONTEND_URL', '')}/vagas/{job_id}/{public_slug}"

    # --- Step 9: Progress WS ---
    if ws_send:
        await ws_send({
            "type": "wizard_stage",
            "stage": "publish",
            "data": {"progress": "Gerando link de compartilhamento..."},
            "completeness": 0.95,
            "requires_approval": False,
        })

    # --- Step 10: Audit log ---
    try:
        from app.shared.compliance.audit_service import AuditService
        audit = AuditService()
        await audit.log_output(
            company_id=company_id,
            session_id=state.get("session_id"),
            agent_used="job_creation",
            input_text=f"Publicar vaga: {enriched_jd.get('titulo_padronizado', '')}",
            output_text=f"Job {job_id} criado. Campaign {campaign_id}. Platforms: {platforms}.",
            action_executed="publish_job",
            candidate_id=None,
            job_vacancy_id=job_id,
            fairness_flags=state.get("fairness_flags", []),
        )
    except Exception as e:
        logger.warning(f"Audit log failed (non-blocking): {e}")

    # --- Step 11: Update state ---
    state["job_id"] = job_id
    state["campaign_id"] = campaign_id
    state["share_link"] = share_link
    state["published"] = True

    # --- Step 12: Final wizard_stage payload ---
    state["ws_stage_payload"] = {
        "type": "wizard_stage",
        "stage": "publish",
        "data": {
            "job_id": job_id,
            "platforms": platforms,
            "sourcing_mode": state.get("sourcing_mode", "local"),
            "contact_channels": state.get("contact_channels", []),
            "share_link": share_link,
            "auto_screen": auto_screen,
        },
        "completeness": 0.95,
        "requires_approval": False,
    }

    return state
