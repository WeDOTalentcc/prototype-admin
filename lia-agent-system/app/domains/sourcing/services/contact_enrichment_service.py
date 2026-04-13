import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.candidates.services.candidate_enrichment_service import (
    CandidateEnrichmentService,
    candidate_enrichment_service,
)
from app.shared.resilience.circuit_breaker import APIFY_CIRCUIT
from lia_models.candidate import Candidate

logger = logging.getLogger(__name__)

from app.domains.sourcing.services.apify_service import (
    APIFY_COST_PER_ENRICHMENT_USD,
    APIFY_MAX_CONCURRENT,
)

APIFY_COST_USD = APIFY_COST_PER_ENRICHMENT_USD
DEDUP_WINDOW_HOURS = 24
BATCH_CONCURRENCY = APIFY_MAX_CONCURRENT


class ContactEnrichmentService:
    def __init__(self, enrichment_svc: CandidateEnrichmentService | None = None):
        self._enrichment_svc = enrichment_svc or candidate_enrichment_service

    async def enrich_candidate_contact(
        self,
        db: AsyncSession,
        candidate_id: UUID,
        linkedin_url: str | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        result = await db.execute(
            select(Candidate).where(Candidate.id == candidate_id)
        )
        candidate = result.scalar_one_or_none()
        if not candidate:
            return {"success": False, "error": "Candidate not found", "source": None}

        if self._has_contact(candidate) and not force:
            return {
                "success": True,
                "already_has_contact": True,
                "email": candidate.email,
                "phone": getattr(candidate, "phone", None),
                "source": "existing",
            }

        profile_url = linkedin_url or candidate.linkedin_url
        if not profile_url:
            return {"success": False, "error": "No LinkedIn URL available", "source": None}

        if not force and self._recently_enriched(candidate):
            return {
                "success": False,
                "error": "Recently enriched without results",
                "source": "dedup_skip",
            }

        if not force and await self._linkedin_url_recently_enriched(db, profile_url):
            return {
                "success": False,
                "error": "Another candidate with this LinkedIn URL was recently enriched",
                "source": "dedup_linkedin_skip",
            }

        if APIFY_CIRCUIT.is_open:
            logger.warning("[ContactEnrichment] Apify circuit breaker is OPEN, skipping")
            return {"success": False, "error": "Apify circuit breaker open", "source": None}

        try:
            start = time.monotonic()
            enrichment_result = await self._enrichment_svc.enrich_candidate(
                db=db,
                candidate_id=candidate_id,
                linkedin_url=profile_url,
                include_experiences=True,
                include_education=True,
                include_email_discovery=True,
            )
            elapsed = time.monotonic() - start

            APIFY_CIRCUIT.record_success()

            await db.refresh(candidate)

            has_contact = self._has_contact(candidate)

            logger.info(
                "[ContactEnrichment] candidate=%s has_contact=%s elapsed=%.1fs fields=%s",
                candidate_id,
                has_contact,
                elapsed,
                enrichment_result.get("fields_updated", []),
            )

            await self._sync_to_rails(candidate, enrichment_result.get("fields_updated", []))

            return {
                "success": enrichment_result.get("success", False),
                "has_contact": has_contact,
                "email": candidate.email,
                "phone": getattr(candidate, "phone", None),
                "fields_updated": enrichment_result.get("fields_updated", []),
                "source": "apify",
                "cost_usd": APIFY_COST_USD,
                "elapsed_seconds": round(elapsed, 2),
            }

        except Exception as e:
            APIFY_CIRCUIT.record_failure()
            logger.error("[ContactEnrichment] Apify enrichment failed for %s: %s", candidate_id, e)
            return {"success": False, "error": str(e), "source": "apify_error"}

    async def enrich_batch(
        self,
        db: AsyncSession,
        candidates: list[dict[str, Any]],
        force: bool = False,
    ) -> list[dict[str, Any]]:
        semaphore = asyncio.Semaphore(BATCH_CONCURRENCY)

        async def _enrich_one(cand: dict) -> dict[str, Any]:
            async with semaphore:
                cand_id = cand.get("id") or cand.get("candidate_id")
                linkedin = cand.get("linkedin_url") or cand.get("linkedin_slug")
                if linkedin and not linkedin.startswith("http"):
                    linkedin = f"https://www.linkedin.com/in/{linkedin}"

                if not cand_id:
                    return {"success": False, "error": "No candidate ID"}

                return await self.enrich_candidate_contact(
                    db=db,
                    candidate_id=UUID(str(cand_id)),
                    linkedin_url=linkedin,
                    force=force,
                )

        results = await asyncio.gather(
            *[_enrich_one(c) for c in candidates],
            return_exceptions=True,
        )

        processed = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                processed.append({"success": False, "error": str(r), "source": "exception"})
            else:
                processed.append(r)
        return processed

    async def enrich_by_linkedin_url(
        self,
        linkedin_url: str,
    ) -> dict[str, Any]:
        """
        Enrich contact data from a LinkedIn URL without requiring a local DB candidate.
        Uses dev_fusion/Linkedin-Profile-Scraper directly and extracts email/phone.
        Returns dict with success, email, phone fields.
        """
        try:
            profile_data = await self._enrichment_svc._scrape_linkedin_profile(
                linkedin_url, "dev_fusion/Linkedin-Profile-Scraper"
            )
            if not profile_data or profile_data.get("error"):
                return {"success": False, "error": profile_data.get("error", "No data")}

            email = (
                profile_data.get("email")
                or profile_data.get("emailAddress")
                or profile_data.get("personalEmail")
                or profile_data.get("bestPersonalEmail")
                or profile_data.get("businessEmail")
                or profile_data.get("bestBusinessEmail")
            )
            personal_emails = profile_data.get("personalEmails") or []
            if not email and personal_emails:
                email = personal_emails[0]

            phone = (
                profile_data.get("phone")
                or profile_data.get("phoneNumber")
                or profile_data.get("mobilePhone")
            )
            phone_numbers = profile_data.get("phoneNumbers") or profile_data.get("phones") or []
            if not phone and phone_numbers:
                phone = phone_numbers[0] if isinstance(phone_numbers[0], str) else str(phone_numbers[0])

            return {
                "success": True,
                "email": email,
                "phone": phone,
                "has_contact": bool(email or phone),
                "source": "apify",
                "cost_usd": APIFY_COST_USD,
            }
        except Exception as e:
            logger.error("[ContactEnrichment] URL-only enrichment failed for %s: %s", linkedin_url, e)
            return {"success": False, "error": str(e)}

    async def enrich_search_results_and_filter(
        self,
        db: AsyncSession,
        candidates: list[Any],
        source_field: str = "source",
    ) -> list[Any]:
        needs_enrichment = []
        for cand in candidates:
            email = getattr(cand, "email", None) or getattr(cand, "best_personal_email", None)
            phone = getattr(cand, "phone", None)
            phones = getattr(cand, "phone_numbers", None)
            if not email and not phone and not phones:
                linkedin = getattr(cand, "linkedin_url", None) or getattr(cand, "linkedin_slug", None)
                cand_id = getattr(cand, "id", None)
                if linkedin and cand_id:
                    needs_enrichment.append({
                        "id": str(cand_id),
                        "linkedin_url": linkedin if linkedin.startswith("http") else f"https://www.linkedin.com/in/{linkedin}",
                    })

        if needs_enrichment:
            logger.info(
                "[ContactEnrichment] Enriching %d/%d candidates missing contact",
                len(needs_enrichment),
                len(candidates),
            )
            await self.enrich_batch(db, needs_enrichment)

        enriched = []
        for cand in candidates:
            email = getattr(cand, "email", None) or getattr(cand, "best_personal_email", None)
            phone = getattr(cand, "phone", None)
            phones = getattr(cand, "phone_numbers", None)
            if email or phone or phones:
                enriched.append(cand)
            else:
                cand_id = getattr(cand, "id", "?")
                logger.debug("[ContactEnrichment] Filtering out candidate %s — no contact after enrichment", cand_id)

        filtered_count = len(candidates) - len(enriched)
        if filtered_count > 0:
            logger.info(
                "[ContactEnrichment] Filtered %d candidates without contact. Returning %d/%d",
                filtered_count,
                len(enriched),
                len(candidates),
            )

        return enriched

    def _has_contact(self, candidate: Candidate) -> bool:
        if candidate.email:
            return True
        if getattr(candidate, "best_personal_email", None):
            return True
        if getattr(candidate, "best_business_email", None):
            return True
        if getattr(candidate, "phone", None):
            return True
        return False

    def _recently_enriched(self, candidate: Candidate) -> bool:
        enrichment_data = (candidate.additional_data or {}).get("enrichment", {})
        last_enriched = enrichment_data.get("last_enriched_at")
        if not last_enriched:
            return False
        try:
            last_dt = datetime.fromisoformat(last_enriched)
            return datetime.utcnow() - last_dt < timedelta(hours=DEDUP_WINDOW_HOURS)
        except (ValueError, TypeError):
            return False

    async def _linkedin_url_recently_enriched(self, db: AsyncSession, linkedin_url: str) -> bool:
        normalized = linkedin_url.strip().rstrip("/").split("?")[0]
        result = await db.execute(
            select(Candidate).where(
                Candidate.linkedin_url.ilike(f"%{normalized.split('/in/')[-1]}%")
            )
        )
        candidates = result.scalars().all()
        for cand in candidates:
            enrichment_data = (cand.additional_data or {}).get("enrichment", {})
            last_enriched = enrichment_data.get("last_enriched_at")
            if not last_enriched:
                continue
            try:
                last_dt = datetime.fromisoformat(last_enriched)
                if datetime.utcnow() - last_dt < timedelta(hours=DEDUP_WINDOW_HOURS):
                    logger.debug(
                        "[ContactEnrichment] LinkedIn URL %s already enriched via candidate %s",
                        linkedin_url, cand.id,
                    )
                    return True
            except (ValueError, TypeError):
                continue
        return False

    async def _sync_to_rails(self, candidate: Candidate, fields_updated: list[str]) -> None:
        if not fields_updated:
            return
        try:
            from app.domains.integrations_hub.services.rails_adapter import (
                CANDIDATE_FORK_TO_RAILS,
                RailsAdapter,
                RAILS_ENABLED,
            )
            if not RAILS_ENABLED:
                return

            sync_data: dict[str, Any] = {}
            for fork_field in fields_updated:
                rails_field = CANDIDATE_FORK_TO_RAILS.get(fork_field)
                if rails_field:
                    value = getattr(candidate, fork_field, None)
                    if value is not None:
                        sync_data[rails_field] = value

            if not sync_data:
                return

            adapter = RailsAdapter()
            await adapter.publish_event(
                event_type="candidate.enriched",
                entity_type="candidate",
                entity_id=str(candidate.id),
                data={
                    "enriched_fields": sync_data,
                    "source": "apify_linkedin",
                },
            )
            logger.info(
                "[ContactEnrichment] Rails sync event published for candidate %s (%d fields)",
                candidate.id, len(sync_data),
            )
        except ImportError:
            logger.debug("[ContactEnrichment] Rails adapter not available, skipping sync")
        except Exception as e:
            logger.warning("[ContactEnrichment] Rails sync failed for %s: %s", candidate.id, e)


contact_enrichment_service = ContactEnrichmentService()


def get_contact_enrichment_service() -> ContactEnrichmentService:
    return contact_enrichment_service
