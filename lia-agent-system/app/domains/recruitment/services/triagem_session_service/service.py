"""
TriagemSessionService facade: delegates to lifecycle, messaging, voice sub-modules.
"""
import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.triagem import TriagemMessage, TriagemSession

from app.domains.recruitment.repositories.triagem_session_repository import (
    TriagemSessionRepository,
)

from ._shared import _build_progress, _get_session_blocks
from .lifecycle import (
    complete_session,
    create_session,
    get_history,
    get_session_config,
    start_session,
    validate_token,
)
from .messaging import process_message
from .voice import generate_tts_for_message, request_phone_call

logger = logging.getLogger(__name__)


class TriagemSessionService:
    """
    Facade that exposes all triagem session operations.
    Each method delegates to the appropriate sub-module function.
    """

    async def validate_token(self, db: AsyncSession, token: str) -> dict[str, Any]:
        return await validate_token(db, token)

    async def get_session_config(self, db: AsyncSession, token: str) -> dict[str, Any] | None:
        return await get_session_config(db, token)

    async def create_session(
        self,
        db: AsyncSession,
        candidate_id: str,
        job_id: str,
        company_id: str,
        candidate_name: str | None = None,
        candidate_email: str | None = None,
        job_title: str | None = None,
        company_name: str | None = None,
        company_logo_url: str | None = None,
        invite_channel: str = "email",
        created_by: str | None = None,
        expires_days: int = 7,
        voice_mode: bool = False,
    ) -> TriagemSession:
        return await create_session(
            db=db,
            candidate_id=candidate_id,
            job_id=job_id,
            company_id=company_id,
            candidate_name=candidate_name,
            candidate_email=candidate_email,
            job_title=job_title,
            company_name=company_name,
            company_logo_url=company_logo_url,
            invite_channel=invite_channel,
            created_by=created_by,
            expires_days=expires_days,
            voice_mode=voice_mode,
        )

    async def start_session(
        self, db: AsyncSession, token: str, voice_mode: bool | None = None
    ) -> dict[str, Any]:
        return await start_session(db, token, voice_mode)

    async def process_message(
        self,
        db: AsyncSession,
        token: str,
        content: str,
        message_type: str = "text",
        voice_mode: bool | None = None,
    ) -> dict[str, Any]:
        return await process_message(db, token, content, message_type, voice_mode)

    async def get_history(self, db: AsyncSession, token: str) -> dict[str, Any]:
        return await get_history(db, token)

    async def complete_session(self, db: AsyncSession, token: str) -> dict[str, Any]:
        return await complete_session(db, token)

    async def generate_tts_for_message(
        self, db: AsyncSession, token: str, message_id: str
    ) -> dict[str, Any]:
        repo = TriagemSessionRepository(db)
        session = await repo.get_session_by_token(token)
        if not session:
            return {"error": "not_found"}
        return await generate_tts_for_message(db, session, message_id)

    async def request_phone_call(
        self, db: AsyncSession, token: str, candidate_phone: str
    ) -> dict[str, Any]:
        repo = TriagemSessionRepository(db)
        session = await repo.get_session_by_token(token)
        if not session:
            return {"error": "not_found"}
        if session.status == "completed":
            return {"error": "already_completed"}
        return await request_phone_call(db, session, candidate_phone)


triagem_service = TriagemSessionService()


def get_triagem_service() -> "TriagemSessionService":
    """Return the module-level TriagemSessionService singleton."""
    return triagem_service
