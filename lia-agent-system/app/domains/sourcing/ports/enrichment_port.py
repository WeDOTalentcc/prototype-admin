"""Port interface for candidate enrichment (UC-P3-15).

Decouples contact_enrichment (sourcing domain) from candidate_enrichment domain.
The ContactEnrichmentService now depends on this abstraction instead of importing
CandidateEnrichmentService directly.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from uuid import UUID


class IEnrichmentPort(ABC):
    """Port for enriching a contact/candidate with additional data."""

    @abstractmethod
    async def enrich_candidate(
        self,
        db: "AsyncSession",
        candidate_id: "UUID",
        linkedin_url: str | None = None,
        include_experiences: bool = True,
        include_education: bool = True,
        include_email_discovery: bool = True,
    ) -> dict[str, Any]:
        """Enrich a candidate record via LinkedIn/Apify.

        Returns a dict with enriched fields (same contract as
        CandidateEnrichmentService.enrich_candidate).
        """
        ...

    @abstractmethod
    async def scrape_profile(
        self,
        linkedin_url: str,
        actor: str = "dev_fusion/Linkedin-Profile-Scraper",
    ) -> dict[str, Any] | None:
        """Scrape raw LinkedIn profile data.

        Used by enrich_contact_from_url (URL-only enrichment without a DB candidate).
        Returns raw profile dict or None on failure.
        """
        ...


class CandidateEnrichmentAdapter(IEnrichmentPort):
    """Adapter: wraps CandidateEnrichmentService behind IEnrichmentPort.

    This is the default production implementation injected by ContactEnrichmentService.
    Tests can substitute a lightweight mock without touching the real Apify calls.
    """

    async def enrich_candidate(
        self,
        db: "AsyncSession",
        candidate_id: "UUID",
        linkedin_url: str | None = None,
        include_experiences: bool = True,
        include_education: bool = True,
        include_email_discovery: bool = True,
    ) -> dict[str, Any]:
        from app.domains.candidates.services.candidate_enrichment_service import (
            candidate_enrichment_service,
        )

        return await candidate_enrichment_service.enrich_candidate(
            db=db,
            candidate_id=candidate_id,
            linkedin_url=linkedin_url,
            include_experiences=include_experiences,
            include_education=include_education,
            include_email_discovery=include_email_discovery,
        )

    async def scrape_profile(
        self,
        linkedin_url: str,
        actor: str = "dev_fusion/Linkedin-Profile-Scraper",
    ) -> dict[str, Any] | None:
        from app.domains.candidates.services.candidate_enrichment_service import (
            candidate_enrichment_service,
        )

        return await candidate_enrichment_service._scrape_linkedin_profile(
            linkedin_url, actor
        )
