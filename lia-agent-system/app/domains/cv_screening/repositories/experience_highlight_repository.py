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
        """Best-effort: table is canonical-managed by alembic migration 138.

        SMOKE-#4+#5 fix (audit 2026-05-20): under role ``lia_app`` (no CREATE on
        schema public — by design), CREATE TABLE IF NOT EXISTS raises
        InsufficientPrivilegeError. The table already exists from prior runs +
        canonical migration; swallow permission denied with debug log instead
        of HTTP 500.
        """
        import logging
        _logger = logging.getLogger(__name__)
        try:
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

        except Exception as exc:
            # Permission denied for schema public under lia_app is expected:
            # table is alembic-managed (migration 138). Other errors should still
            # bubble up since they indicate real DDL failure.
            if "permission denied" in str(exc).lower() or "insufficientprivilege" in type(exc).__name__.lower():
                # SMOKE-#4+#5 v2 fix: asyncpg poisons the transaction on permission denied.
                # We MUST rollback to recover, otherwise subsequent SELECT/DELETE on the
                # same session lança InFailedSQLTransactionError.
                try:
                    await self.db.rollback()
                except Exception:
                    pass  # rollback errors are non-fatal here
                _logger.debug(
                    "ExperienceHighlightRepository.ensure_table skipped (lia_app no CREATE on public — table is alembic-managed): %s",
                    exc,
                )
                return
            raise

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
