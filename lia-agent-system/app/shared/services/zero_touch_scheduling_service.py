"""
Zero-Touch Scheduling Service - Sprint 1C.

Connects the existing SelfSchedulingLink model (app/models/self_scheduling.py)
with the communication layer so recruiters can send a scheduling link to a
candidate with a single call. The candidate picks a slot, and the service
automatically creates the interview via SchedulingService.

Flow:
  1. Recruiter (or agent) calls send_scheduling_link()
     → Creates SelfSchedulingLink record
     → Sends link via WhatsApp (preferred) or email
  2. Candidate accesses the public link and selects a slot
     → Frontend calls confirm_slot() (handled by API endpoint)
     → Service creates Interview via SchedulingService
     → Updates SelfSchedulingLink status to "used"
"""

from __future__ import annotations

# RAILS-DEPRECATED: This service performs CRUD for Rails-owned entities.
# Will be deleted after ats-api-rails handoff is complete.
# Do NOT migrate to a domain -- route through integrations_hub/rails_adapter instead.

import warnings
warnings.warn(
    "zero_touch_scheduling_service is deprecated and will be removed once Rails adapter routes are complete. "
    "Migrate callers to rails_adapter equivalents. "
    "See UC-P1-22 in the remediation plan (CROSS_CUTTING_AUDIT_AND_REMEDIATION_PLAN.md).",
    DeprecationWarning,
    stacklevel=2,
)


import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from lia_models.self_scheduling import SelfSchedulingLink

logger = logging.getLogger(__name__)

_communication_service = None
_scheduling_service = None


def _get_communication_service():
    global _communication_service
    if _communication_service is None:
        from app.domains.communication.services.communication_service import communication_service
        _communication_service = communication_service
    return _communication_service


def _get_scheduling_service():
    global _scheduling_service
    if _scheduling_service is None:
        from app.domains.interview_scheduling.services.scheduling_service import SchedulingService
        _scheduling_service = SchedulingService()
    return _scheduling_service


class ZeroTouchSchedulingService:
    """
    Orchestrates candidate self-scheduling without recruiter involvement.

    Usage by agents or API:
    ```python
    result = await zero_touch_scheduling_service.send_scheduling_link(
        company_id="...",
        candidate_id="...",
        candidate_name="Maria Silva",
        candidate_email="maria@email.com",
        candidate_phone="+5511999999999",
        job_vacancy_id="...",
        job_title="Analista de RH",
        available_slots=[
            {"start": "2026-03-10T10:00:00", "end": "2026-03-10T11:00:00"},
            {"start": "2026-03-11T14:00:00", "end": "2026-03-11T15:00:00"},
        ],
        interviewer_emails=["recruiter@empresa.com"],
        interview_type="hr",
        preferred_channel="whatsapp",
        created_by="pipeline_agent",
    )
    ```
    """

    async def send_scheduling_link(
        self,
        company_id: str,
        candidate_id: str,
        candidate_name: str,
        candidate_email: str,
        job_vacancy_id: str,
        job_title: str,
        available_slots: list[dict[str, str]],
        interviewer_emails: list[str],
        candidate_phone: str | None = None,
        interview_type: str = "hr",
        interview_mode: str = "video",
        duration_minutes: int = 60,
        preferred_channel: str = "whatsapp",
        expires_hours: int = 72,
        created_by: str = "system",
        db: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """
        Create a SelfSchedulingLink and send it to the candidate.

        Returns dict with link token, scheduling URL, and send status.
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True

        try:
            token = SelfSchedulingLink.generate_token()
            expires_at = datetime.utcnow() + timedelta(hours=expires_hours)

            link = SelfSchedulingLink(
                token=token,
                candidate_id=uuid.UUID(candidate_id) if candidate_id else None,
                candidate_name=candidate_name,
                candidate_email=candidate_email,
                job_vacancy_id=uuid.UUID(job_vacancy_id) if job_vacancy_id else None,
                job_title=job_title,
                interviewer_emails=interviewer_emails,
                interview_type=interview_type,
                interview_mode=interview_mode,
                duration_minutes=duration_minutes,
                available_slots=available_slots,
                status="pending",
                expires_at=expires_at,
                created_by=created_by,
            )
            db.add(link)
            await db.commit()
            await db.refresh(link)

            logger.info(
                f"SelfSchedulingLink created: token={token[:8]}... "
                f"candidate={candidate_name} vacancy={job_title}"
            )

            scheduling_url = f"/agendar/{token}"
            send_result = await self._send_link_to_candidate(
                company_id=company_id,
                candidate_id=candidate_id,
                candidate_name=candidate_name,
                candidate_email=candidate_email,
                candidate_phone=candidate_phone,
                job_title=job_title,
                scheduling_url=scheduling_url,
                expires_hours=expires_hours,
                preferred_channel=preferred_channel,
                db=db,
            )

            return {
                "success": True,
                "link_id": str(link.id),
                "token": token,
                "scheduling_url": scheduling_url,
                "expires_at": expires_at.isoformat(),
                "slots_offered": len(available_slots),
                "send_result": send_result,
            }

        except Exception as e:
            logger.error(f"ZeroTouchSchedulingService.send_scheduling_link error: {e}")
            await db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if should_close:
                await db.close()

    async def confirm_slot(
        self,
        token: str,
        selected_slot: dict[str, str],
        db: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """
        Called when candidate selects a slot from the scheduling page.

        Creates the Interview record and marks the SelfSchedulingLink as used.
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True

        try:
            result = await db.execute(
                select(SelfSchedulingLink).where(SelfSchedulingLink.token == token)
            )
            link = result.scalar_one_or_none()

            if not link:
                return {"success": False, "error": "Link não encontrado"}

            if not link.is_valid():
                return {"success": False, "error": "Link expirado ou já utilizado"}

            link.selected_slot = selected_slot
            link.status = "used"
            link.use_count = (link.use_count or 0) + 1
            link.updated_at = datetime.utcnow()

            scheduling_svc = _get_scheduling_service()
            try:
                start_dt = datetime.fromisoformat(selected_slot["start"])
                interview_result = await scheduling_svc.create_interview(
                    db=db,
                    job_vacancy_id=str(link.job_vacancy_id) if link.job_vacancy_id else None,
                    candidate_id=str(link.candidate_id) if link.candidate_id else None,
                    candidate_name=link.candidate_name,
                    candidate_email=link.candidate_email,
                    interviewer_emails=link.interviewer_emails or [],
                    start_time=start_dt,
                    duration_minutes=link.duration_minutes,
                    interview_type=link.interview_type,
                    interview_mode=link.interview_mode,
                    notes="Agendado pelo candidato via link de auto-agendamento.",
                )
                if interview_result.get("interview_id"):
                    link.interview_id = uuid.UUID(interview_result["interview_id"])
            except Exception as e:
                logger.warning(f"Could not auto-create interview from slot selection: {e}")
                interview_result = {"error": str(e)}

            await db.commit()

            logger.info(
                f"Slot confirmed: token={token[:8]}... "
                f"candidate={link.candidate_name} slot={selected_slot}"
            )

            return {
                "success": True,
                "link_id": str(link.id),
                "candidate_name": link.candidate_name,
                "job_title": link.job_title,
                "selected_slot": selected_slot,
                "interview_result": interview_result,
            }

        except Exception as e:
            logger.error(f"ZeroTouchSchedulingService.confirm_slot error: {e}")
            await db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if should_close:
                await db.close()

    async def get_link_by_token(
        self,
        token: str,
        db: AsyncSession | None = None,
    ) -> dict[str, Any] | None:
        """Return public-safe link data for the scheduling page."""
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True

        try:
            result = await db.execute(
                select(SelfSchedulingLink).where(SelfSchedulingLink.token == token)
            )
            link = result.scalar_one_or_none()
            if not link:
                return None
            return link.to_dict()
        except Exception as e:
            logger.warning(f"get_link_by_token error: {e}")
            return None
        finally:
            if should_close:
                await db.close()

    async def _send_link_to_candidate(
        self,
        company_id: str,
        candidate_id: str,
        candidate_name: str,
        candidate_email: str,
        candidate_phone: str | None,
        job_title: str,
        scheduling_url: str,
        expires_hours: int,
        preferred_channel: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Send scheduling link via WhatsApp (preferred) or email fallback."""
        from app.domains.communication.services.communication_service import (
            MessageChannel,
            MessageType,
        )

        first_name = candidate_name.split()[0] if candidate_name else "candidato(a)"
        message_body = (
            f"Olá, {first_name}! Temos uma vaga de {job_title} para você. "
            f"Por favor, escolha o melhor horário para sua entrevista acessando o link abaixo. "
            f"O link expira em {expires_hours} horas.\n\n"
            f"Agendar: {scheduling_url}"
        )

        channel = MessageChannel.WHATSAPP if (
            preferred_channel == "whatsapp" and candidate_phone
        ) else MessageChannel.EMAIL

        try:
            comm_svc = _get_communication_service()
            result = await comm_svc.send_message(
                company_id=company_id,
                candidate_id=candidate_id,
                candidate_email=candidate_email,
                candidate_phone=candidate_phone,
                message_type=MessageType.INTERVIEW_INVITE,
                channel=channel,
                subject=f"Agende sua entrevista — {job_title}",
                body=message_body,
                job_id=None,
                db=db,
            )
            logger.info(
                f"Scheduling link sent via {channel.value} to {candidate_name}: "
                f"success={result.get('success')}"
            )
            return result
        except Exception as e:
            logger.warning(f"Failed to send scheduling link via {channel.value}: {e}")
            # Email fallback if WhatsApp failed
            if channel == MessageChannel.WHATSAPP:
                try:
                    comm_svc = _get_communication_service()
                    return await comm_svc.send_message(
                        company_id=company_id,
                        candidate_id=candidate_id,
                        candidate_email=candidate_email,
                        candidate_phone=None,
                        message_type=MessageType.INTERVIEW_INVITE,
                        channel=MessageChannel.EMAIL,
                        subject=f"Agende sua entrevista — {job_title}",
                        body=message_body,
                        job_id=None,
                        db=db,
                    )
                except Exception as e2:
                    logger.error(f"Email fallback also failed: {e2}")
            return {"success": False, "error": str(e)}


zero_touch_scheduling_service = ZeroTouchSchedulingService()
