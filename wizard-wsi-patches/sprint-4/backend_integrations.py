"""
Sprint 4B — Backend integration patches.

4.9:  Campaign orchestration (SourcingAgentOrchestrator)
4.10: Voice screening toggle
4.11: WorkflowRail integration
4.12: Calibration hard enforcement
4.13: OCR for images
4.14: Wizard antigo session migration
4.15: SLA tracking
4.16: Email/WhatsApp notification
"""

import os
import logging
import httpx

logger = logging.getLogger(__name__)

RAILS_BACKEND_URL = os.getenv("RAILS_BACKEND_URL", "http://localhost:3000")


# === 4.9: Campaign Orchestration ===
# ONDE: Chamar no publish_node APÓS criar campaign

async def start_sourcing_campaign(
    job_id: int,
    campaign_id: int,
    company_id: int,
    sourcing_mode: str = "local",
) -> None:
    """Start active sourcing via SourcingAgentOrchestrator after publish."""
    try:
        from app.services.sourcing_agent_orchestrator import SourcingAgentOrchestrator
        orchestrator = SourcingAgentOrchestrator(company_id=company_id)
        await orchestrator.create_agent(
            job_id=job_id,
            campaign_id=campaign_id,
            sourcing_mode=sourcing_mode,
            enabled=True,
        )
        logger.info(f"Sourcing campaign started for job {job_id}")
    except ImportError:
        logger.info("SourcingAgentOrchestrator not available — skipping sourcing")
    except Exception as e:
        logger.warning(f"Sourcing campaign start failed (non-blocking): {e}")


# === 4.10: Voice Screening Toggle ===
# ONDE: Adicionar ao wizard state + publish_node

VOICE_SCREENING_CONFIG = {
    "enabled": False,  # Default off, user toggles in wizard
    "channels": ["web", "whatsapp", "phone"],
    "default_channel": "web",
}

# No publish_node, se voice_screening_enabled:
# from app.api.v1.voice_screening import create_voice_session
# await create_voice_session(job_id=job_id, channel=voice_channel)


# === 4.12: Calibration Hard Enforcement ===
# ONDE: app/domains/job_creation/nodes/calibration_node.py

async def calibration_node(state: dict, config: dict) -> dict:
    """
    Calibration node with HARD enforcement.
    Blocks handoff if approved_count < threshold.
    """
    candidates = state.get("calibration_candidates", [])
    threshold = state.get("calibration_threshold", 3)
    approved = [c for c in candidates if c.get("decision") == "approved"]
    approved_count = len(approved)

    # HARD enforcement: cannot proceed without minimum calibrations
    can_proceed = approved_count >= threshold

    state["calibration_complete"] = can_proceed
    state["calibration_approved_count"] = approved_count

    state["ws_stage_payload"] = {
        "type": "wizard_stage",
        "stage": "calibration",
        "data": {
            "candidates": candidates,
            "threshold": threshold,
            "approved_count": approved_count,
            "complete": can_proceed,
        },
        "completeness": 0.90 if can_proceed else 0.88,
        "requires_approval": not can_proceed,
    }

    if not can_proceed:
        logger.info(f"Calibration blocked: {approved_count}/{threshold} (need {threshold - approved_count} more)")

    return state


# === 4.15: SLA Tracking ===
# ONDE: Chamar no publish_node após criar campaign

async def create_recruitment_sla(
    campaign_id: int,
    company_id: int,
    auth_token: str,
) -> None:
    """Create SLA records in Rails for each campaign stage."""
    DEFAULT_SLAS = {
        "sourcing": {"max_days": 14, "escalation_after_days": 10},
        "screening": {"max_days": 7, "escalation_after_days": 5},
        "wsi": {"max_days": 5, "escalation_after_days": 3},
        "interview": {"max_days": 14, "escalation_after_days": 10},
        "offer": {"max_days": 7, "escalation_after_days": 5},
    }

    try:
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
            "X-Company-ID": str(company_id),
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            for stage, config in DEFAULT_SLAS.items():
                await client.post(
                    f"{RAILS_BACKEND_URL}/v1/users/recruitment_slas",
                    json={
                        "recruitment_sla": {
                            "campaign_id": campaign_id,
                            "stage": stage,
                            **config,
                        }
                    },
                    headers=headers,
                )
        logger.info(f"SLAs created for campaign {campaign_id}")
    except Exception as e:
        logger.warning(f"SLA creation failed (non-blocking): {e}")


# === 4.16: Email/WhatsApp Notification ===
# ONDE: Chamar no publish_node após publicar

async def send_publish_notification(
    job_id: int,
    job_title: str,
    company_id: int,
    notify_channels: list[str] | None = None,
) -> None:
    """Send notification to configured channels after job publish."""
    channels = notify_channels or ["email"]

    try:
        # Use existing Communication service
        from app.services.communication_service import CommunicationService
        comm = CommunicationService(company_id=company_id)

        for channel in channels:
            if channel == "email":
                await comm.send_email(
                    template="job_published",
                    context={"job_id": job_id, "job_title": job_title},
                )
            elif channel == "whatsapp":
                await comm.send_whatsapp(
                    template="job_published",
                    context={"job_id": job_id, "job_title": job_title},
                )
        logger.info(f"Publish notification sent for job {job_id} via {channels}")
    except ImportError:
        logger.info("CommunicationService not available — skipping notification")
    except Exception as e:
        logger.warning(f"Notification failed (non-blocking): {e}")


# === 4.13: OCR for Images ===
# ONDE: app/domains/job_creation/services/ocr_service.py (NOVO)

async def extract_text_from_image(file_bytes: bytes, filename: str) -> str:
    """
    Extract text from image file using OCR.
    Falls back to empty string if OCR not available.

    Supports: .png, .jpg, .jpeg
    Uses: pytesseract or Google Vision API
    """
    try:
        import pytesseract
        from PIL import Image
        import io

        image = Image.open(io.BytesIO(file_bytes))
        text = pytesseract.image_to_string(image, lang="por+eng")
        logger.info(f"OCR extracted {len(text)} chars from {filename}")
        return text.strip()
    except ImportError:
        logger.warning("pytesseract not installed — OCR not available")
        return ""
    except Exception as e:
        logger.warning(f"OCR failed for {filename}: {e}")
        return ""
