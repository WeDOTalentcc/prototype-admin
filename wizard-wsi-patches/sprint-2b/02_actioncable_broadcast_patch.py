"""
Sprint 2B.13 + 2B.14 — ActionCable broadcast + StageAutomationEngine trigger.

ONDE APLICAR: Adicionar ao publish_node.py APÓS criar o job e campaign.
AÇÃO: POST ao Rails para broadcast campaign update e disparar automações.
"""

import httpx
import logging
import os

logger = logging.getLogger(__name__)

RAILS_BACKEND_URL = os.getenv("RAILS_BACKEND_URL", "http://localhost:3000")


async def broadcast_campaign_update(
    campaign_id: int,
    company_id: int,
    auth_token: str,
) -> None:
    """
    Trigger Rails ActionCable broadcast for WorkflowRail real-time update.

    Rails RecruitmentCampaign#broadcast_update! sends to:
    WorkflowChannel (workflow_user_#{user_id})

    This call advances the campaign stage which triggers the broadcast.
    """
    if not campaign_id:
        return

    try:
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
            "X-Company-ID": str(company_id),
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Advance campaign to "sourcing" stage (triggers broadcast_update!)
            resp = await client.post(
                f"{RAILS_BACKEND_URL}/v1/users/recruitment_campaigns/{campaign_id}/advance_stage",
                headers=headers,
            )
            if resp.status_code < 300:
                logger.info(f"Campaign {campaign_id} advanced + broadcast sent")
            else:
                logger.warning(f"Campaign advance returned {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.warning(f"ActionCable broadcast failed (non-blocking): {e}")


async def trigger_stage_automation(
    job_id: int,
    company_id: int,
    auth_token: str,
    trigger_event: str = "job_published",
) -> None:
    """
    Trigger Rails StageAutomationEngine for post-publish automations.

    Rails RecruitmentAutomation model checks trigger_event == "job_published"
    and executes configured actions (send_message, advance_stage, etc.)
    """
    try:
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
            "X-Company-ID": str(company_id),
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Call Rails automation trigger endpoint
            # This endpoint checks recruitment_automations table
            # for active automations with trigger_event == "job_published"
            resp = await client.post(
                f"{RAILS_BACKEND_URL}/v1/users/jobs/{job_id}/trigger_automation",
                json={"trigger_event": trigger_event},
                headers=headers,
            )
            if resp.status_code < 300:
                logger.info(f"Automation triggered for job {job_id}: {trigger_event}")
            else:
                # Non-blocking: automation endpoint may not exist yet
                logger.info(f"Automation trigger returned {resp.status_code} (may not be implemented)")
    except Exception as e:
        logger.warning(f"Stage automation trigger failed (non-blocking): {e}")


# --- INTEGRAÇÃO NO publish_node.py ---
# Após criar job e campaign (steps 2 e 4):
#
# await broadcast_campaign_update(campaign_id, company_id, auth_token)
# await trigger_stage_automation(job_id, company_id, auth_token)
