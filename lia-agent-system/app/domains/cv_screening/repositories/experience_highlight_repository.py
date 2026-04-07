"""ExperienceHighlightRepository — raw SQL operations for candidate experience highlights cache.

Extracted from app/api/v1/experience_highlights.py as part of Phase 2 refactor.
Uses raw SQL via sqlalchemy text() because the table is dynamically created (no ORM model).
"""
import logging
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ExperienceHighlightRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def ensure_table(self) -> None:
        """Ensure the candidate_experience_highlights cache table exists."""
        await self.db.execute(text("""
            CREATE TABLE IF NOT EXISTS candidate_experience_highlights (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                candidate_id VARCHAR(255) NOT NULL,
                company_id VARCHAR(255) NOT NULL,
                highlight_text TEXT NOT NULL,
                model_used VARCHAR(100) NOT NULL DEFAULT 'claude-sonnet-4-6',
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_candidate_highlight UNIQUE (candidate_id, company_id)
            )
        """))
        await self.db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_exp_highlights_candidate
            ON candidate_experience_highlights(candidate_id)
        """))
        await self.db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_exp_highlights_expires
            ON candidate_experience_highlights(expires_at)
        """))

    async def get_valid_highlight(
        self, candidate_id: str, company_id: str
    ) -> tuple | None:
        """Return (id, candidate_id, highlight_text, model_used, generated_at, expires_at) or None."""
        result = await self.db.execute(
            text("""
                SELECT id, candidate_id, highlight_text, model_used, generated_at, expires_at
                FROM candidate_experience_highlights
                WHERE candidate_id = :candidate_id
                AND company_id = :company_id
                AND expires_at > CURRENT_TIMESTAMP
                ORDER BY generated_at DESC
                LIMIT 1
            """),
            {"candidate_id": candidate_id, "company_id": company_id},
        )
        return result.fetchone()

    async def upsert_highlight(
        self,
        highlight_id: str,
        candidate_id: str,
        company_id: str,
        highlight_text: str,
        model_used: str,
        generated_at: datetime,
        expires_at: datetime,
    ) -> tuple:
        """Insert or update a highlight. Returns the stored row."""
        result = await self.db.execute(
            text("""
                INSERT INTO candidate_experience_highlights
                (id, candidate_id, company_id, highlight_text, model_used, generated_at, expires_at)
                VALUES (:id, :candidate_id, :company_id, :highlight_text, :model_used, :generated_at, :expires_at)
                ON CONFLICT (candidate_id, company_id)
                DO UPDATE SET
                    highlight_text = EXCLUDED.highlight_text,
                    model_used = EXCLUDED.model_used,
                    generated_at = EXCLUDED.generated_at,
                    expires_at = EXCLUDED.expires_at,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id, candidate_id, highlight_text, model_used, generated_at, expires_at
            """),
            {
                "id": highlight_id,
                "candidate_id": candidate_id,
                "company_id": company_id,
                "highlight_text": highlight_text,
                "model_used": model_used,
                "generated_at": generated_at,
                "expires_at": expires_at,
            },
        )
        return result.fetchone()

    async def delete_highlight(self, candidate_id: str, company_id: str) -> int:
        """Delete highlight for a candidate. Returns rowcount."""
        result = await self.db.execute(
            text("""
                DELETE FROM candidate_experience_highlights
                WHERE candidate_id = :candidate_id AND company_id = :company_id
            """),
            {"candidate_id": candidate_id, "company_id": company_id},
        )
        return result.rowcount
