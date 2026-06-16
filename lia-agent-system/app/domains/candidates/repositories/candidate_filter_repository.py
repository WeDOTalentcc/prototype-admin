"""CandidateFilterRepository — DB access layer for filter suggestion queries.

Extracted from app/api/v1/candidate_search/contact.py as part of Phase 2 refactor.
Provides autocomplete/facet counts over the candidates table for:
  titles, companies, skills, locations, countries, universities, languages.
"""
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class CandidateFilterRepository:
    """Repository for candidate filter-suggestion (autocomplete + counts) queries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_titles(self, query_lower: str, limit: int) -> list:
        """Return (current_title, count) rows matching query fragment."""
        result = await self.db.execute(
            text("""
                SELECT current_title, COUNT(*) as count
                FROM candidates
                WHERE current_title IS NOT NULL
                AND current_title != ''
                AND is_active = true
                AND LOWER(current_title) LIKE :query
                GROUP BY current_title
                ORDER BY count DESC
                LIMIT :limit
            """),
            {"query": f"%{query_lower}%", "limit": limit * 2},
        )
        return result.fetchall()

    async def get_companies(self, query_lower: str, limit: int) -> list:
        """Return (current_company, count) rows matching query fragment."""
        result = await self.db.execute(
            text("""
                SELECT current_company, COUNT(*) as count
                FROM candidates
                WHERE current_company IS NOT NULL
                AND current_company != ''
                AND is_active = true
                AND LOWER(current_company) LIKE :query
                GROUP BY current_company
                ORDER BY count DESC
                LIMIT :limit
            """),
            {"query": f"%{query_lower}%", "limit": limit},
        )
        return result.fetchall()

    async def get_skills(self, query_lower: str, limit: int) -> list:
        """Return (skill, count) rows from unnested technical_skills array."""
        result = await self.db.execute(
            text("""
                SELECT skill, COUNT(*) as count
                FROM (
                    SELECT UNNEST(technical_skills) as skill
                    FROM candidates
                    WHERE is_active = true
                    AND technical_skills IS NOT NULL
                ) skills_expanded
                WHERE LOWER(skill) LIKE :query
                GROUP BY skill
                ORDER BY count DESC
                LIMIT :limit
            """),
            {"query": f"%{query_lower}%", "limit": limit},
        )
        return result.fetchall()

    async def get_locations(self, query_lower: str, limit: int) -> list:
        """Return (location_label, count) rows combining city+state."""
        result = await self.db.execute(
            text("""
                SELECT
                    CASE
                        WHEN location_state IS NOT NULL AND location_state != ''
                        THEN CONCAT(location_city, ', ', location_state)
                        ELSE location_city
                    END as location,
                    COUNT(*) as count
                FROM candidates
                WHERE location_city IS NOT NULL
                AND location_city != ''
                AND is_active = true
                AND (
                    LOWER(location_city) LIKE :query
                    OR LOWER(location_state) LIKE :query
                )
                GROUP BY location_city, location_state
                ORDER BY count DESC
                LIMIT :limit
            """),
            {"query": f"%{query_lower}%", "limit": limit},
        )
        return result.fetchall()

    async def get_countries(self, query_lower: str, limit: int) -> list:
        """Return (location_country, count) rows matching query fragment."""
        result = await self.db.execute(
            text("""
                SELECT location_country, COUNT(*) as count
                FROM candidates
                WHERE location_country IS NOT NULL
                AND location_country != ''
                AND is_active = true
                AND LOWER(location_country) LIKE :query
                GROUP BY location_country
                ORDER BY count DESC
                LIMIT :limit
            """),
            {"query": f"%{query_lower}%", "limit": limit},
        )
        return result.fetchall()

    async def get_universities(self, query_lower: str, limit: int) -> list:
        """Return (university, count) rows from additional_data JSONB field."""
        result = await self.db.execute(
            text("""
                SELECT
                    COALESCE(additional_data->>'university', 'Não especificado') as university,
                    COUNT(*) as count
                FROM candidates
                WHERE is_active = true
                AND additional_data->>'university' IS NOT NULL
                AND LOWER(additional_data->>'university') LIKE :query
                GROUP BY additional_data->>'university'
                ORDER BY count DESC
                LIMIT :limit
            """),
            {"query": f"%{query_lower}%", "limit": limit},
        )
        return result.fetchall()

    async def get_languages(self, query_lower: str, limit: int) -> list:
        """Return (language_key, count) rows from languages JSONB object keys."""
        result = await self.db.execute(
            text("""
                SELECT key as language, COUNT(*) as count
                FROM candidates, jsonb_object_keys(COALESCE(languages, '{}'::jsonb)) as key
                WHERE is_active = true
                AND LOWER(key) LIKE :query
                GROUP BY key
                ORDER BY count DESC
                LIMIT :limit
            """),
            {"query": f"%{query_lower}%", "limit": limit},
        )
        return result.fetchall()
