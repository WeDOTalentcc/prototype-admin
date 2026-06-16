"""ProfileAnalysisRepository — DB access layer for LIA profile analyses.

Extracted from app/api/v1/lia_profile_analysis.py as part of Phase 2 refactor.
"""
import logging

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lia_profile_analysis import LiaProfileAnalysis

logger = logging.getLogger(__name__)


class ProfileAnalysisRepository:
    """Repository for LIA profile analysis data access."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_by_candidate_type_company(
        self,
        candidate_id: str,
        analysis_type: str,
        company_id: str,
    ) -> LiaProfileAnalysis | None:
        """Fetch an active analysis for a candidate/type/company combination."""
        query = select(LiaProfileAnalysis).where(
            and_(
                LiaProfileAnalysis.candidate_id == candidate_id,
                LiaProfileAnalysis.analysis_type == analysis_type,
                LiaProfileAnalysis.company_id == company_id,
                LiaProfileAnalysis.is_active,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_content(
        self,
        analysis: LiaProfileAnalysis,
        content: str,
        candidate_name: str | None,
    ) -> LiaProfileAnalysis:
        """Update content and candidate_name on an existing analysis."""
        analysis.content = content
        if candidate_name is not None:
            analysis.candidate_name = candidate_name
        await self.db.flush()
        await self.db.refresh(analysis)
        return analysis

    async def create(
        self,
        candidate_id: str,
        analysis_type: str,
        content: str,
        candidate_name: str | None,
        created_by: str | None,
        company_id: str,
    ) -> LiaProfileAnalysis:
        """Insert a new profile analysis record."""
        new_analysis = LiaProfileAnalysis(
            candidate_id=candidate_id,
            analysis_type=analysis_type,
            content=content,
            candidate_name=candidate_name,
            created_by=created_by,
            company_id=company_id,
        )
        self.db.add(new_analysis)
        await self.db.flush()
        await self.db.refresh(new_analysis)
        return new_analysis

    async def get_all_active_for_candidate(
        self,
        candidate_id: str,
        company_id: str,
    ) -> list[LiaProfileAnalysis]:
        """Fetch all active analyses for a candidate within a company."""
        query = (
            select(LiaProfileAnalysis)
            .where(
                and_(
                    LiaProfileAnalysis.candidate_id == candidate_id,
                    LiaProfileAnalysis.company_id == company_id,
                    LiaProfileAnalysis.is_active,
                )
            )
            .order_by(desc(LiaProfileAnalysis.created_at))
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def soft_delete(
        self,
        candidate_id: str,
        analysis_type: str,
        company_id: str,
    ) -> LiaProfileAnalysis | None:
        """Soft-delete (is_active=False) a specific analysis. Returns None if not found."""
        query = select(LiaProfileAnalysis).where(
            and_(
                LiaProfileAnalysis.candidate_id == candidate_id,
                LiaProfileAnalysis.analysis_type == analysis_type,
                LiaProfileAnalysis.company_id == company_id,
                LiaProfileAnalysis.is_active,
            )
        )
        result = await self.db.execute(query)
        analysis = result.scalar_one_or_none()
        if not analysis:
            return None
        analysis.is_active = False
        return analysis
