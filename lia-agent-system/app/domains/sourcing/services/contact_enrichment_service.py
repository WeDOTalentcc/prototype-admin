import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.candidates.repositories.candidate_repository import CandidateRepository

from app.domains.sourcing.ports.enrichment_port import (
    IEnrichmentPort,
    CandidateEnrichmentAdapter,
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
    def __init__(self, enrichment_svc: IEnrichmentPort | None = None):
        self._enrichment_svc: IEnrichmentPort = enrichment_svc or CandidateEnrichmentAdapter()

    async def _track_apify_consumption(
        self,
        db: AsyncSession,
        company_id: str | None,
        user_id: str | None,
        candidate_id: str | None,
        linkedin_url: str | None,
        operation: str,
        cost_usd: float,
        success: bool,
        result_status: str = "success",
        response_time_ms: int = 0,
        error_message: str | None = None,
    ) -> None:
        resolved_company_id = company_id or "unattributed"
        try:
            from app.domains.billing.services.consumption_tracking_service import ConsumptionTrackingService
            await ConsumptionTrackingService.record_apify_call(
                db=db,
                company_id=resolved_company_id,
                user_id=user_id,
                candidate_id=str(candidate_id) if candidate_id else None,
                linkedin_url=linkedin_url,
                operation=operation,
                cost_usd=cost_usd,
                success=success,
                result_status=result_status,
                response_time_ms=response_time_ms,
                error_message=error_message,
            )
        except Exception as e:
            logger.error("[ContactEnrichment] Failed to track consumption: %s", e)

    async def enrich_candidate_contact(
        self,
        db: AsyncSession,
        candidate_id: UUID,
        linkedin_url: str | None = None,
        force: bool = False,
        company_id: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        candidate_repo = CandidateRepository(db)
        candidate = await candidate_repo.get_by_id(candidate_id)
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

            await APIFY_CIRCUIT.record_success()

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

            result_status = "success" if has_contact else "no_contact"
            await self._track_apify_consumption(
                db=db,
                company_id=company_id,
                user_id=user_id,
                candidate_id=str(candidate_id),
                linkedin_url=profile_url,
                operation="enrich",
                cost_usd=APIFY_COST_USD,
                success=enrichment_result.get("success", False),
                result_status=result_status,
                response_time_ms=int(elapsed * 1000),
            )

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
            await APIFY_CIRCUIT.record_failure()
            logger.error("[ContactEnrichment] Apify enrichment failed for %s: %s", candidate_id, e)

            await self._track_apify_consumption(
                db=db,
                company_id=company_id,
                user_id=user_id,
                candidate_id=str(candidate_id),
                linkedin_url=profile_url,
                operation="enrich",
                cost_usd=APIFY_COST_USD,
                success=False,
                result_status="fail",
                error_message=str(e)[:500],
            )

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
        company_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Enrich contact data from a LinkedIn URL without requiring a local DB candidate.
        Uses dev_fusion/Linkedin-Profile-Scraper directly and extracts email/phone.
        Returns dict with success, email, phone fields.
        """
        import time as _time
        _start = _time.monotonic()
        try:
            profile_data = await self._enrichment_svc._scrape_linkedin_profile(
                linkedin_url
            )
            _elapsed_ms = int((_time.monotonic() - _start) * 1000)
            error_msg = None
            if not profile_data:
                error_msg = "No data"
            elif isinstance(profile_data, dict) and profile_data.get("error"):
                error_msg = profile_data["error"]
            if error_msg:
                await self._track_apify_consumption_fire_and_forget(
                    company_id=company_id,
                    linkedin_url=linkedin_url,
                    operation="enrich_url",
                    cost_usd=APIFY_COST_USD,
                    success=False,
                    result_status="no_contact",
                    response_time_ms=_elapsed_ms,
                )
                return {"success": False, "error": error_msg}

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

            has_contact = bool(email or phone)
            result_status = "success" if has_contact else "no_contact"
            await self._track_apify_consumption_fire_and_forget(
                company_id=company_id,
                linkedin_url=linkedin_url,
                operation="enrich_url",
                cost_usd=APIFY_COST_USD,
                success=True,
                result_status=result_status,
                response_time_ms=_elapsed_ms,
            )

            return {
                "success": True,
                "email": email,
                "phone": phone,
                "has_contact": has_contact,
                "source": "apify",
                "cost_usd": APIFY_COST_USD,
            }
        except Exception as e:
            _elapsed_ms = int((_time.monotonic() - _start) * 1000)
            logger.error("[ContactEnrichment] URL-only enrichment failed for %s: %s", linkedin_url, e)
            await self._track_apify_consumption_fire_and_forget(
                company_id=company_id,
                linkedin_url=linkedin_url,
                operation="enrich_url",
                cost_usd=APIFY_COST_USD,
                success=False,
                result_status="fail",
                response_time_ms=_elapsed_ms,
                error_message=str(e)[:500],
            )
            return {"success": False, "error": str(e)}

    async def _track_apify_consumption_fire_and_forget(
        self,
        company_id: str | None,
        linkedin_url: str | None,
        operation: str,
        cost_usd: float,
        success: bool,
        result_status: str = "success",
        response_time_ms: int = 0,
        error_message: str | None = None,
    ) -> None:
        resolved_company_id = company_id or "unattributed"
        try:
            from app.core.database import AsyncSessionLocal
            from app.domains.billing.services.consumption_tracking_service import ConsumptionTrackingService
            async with AsyncSessionLocal() as db:
                await ConsumptionTrackingService.record_apify_call(
                    db=db,
                    company_id=resolved_company_id,
                    user_id=None,
                    candidate_id=None,
                    linkedin_url=linkedin_url,
                    operation=operation,
                    cost_usd=cost_usd,
                    success=success,
                    result_status=result_status,
                    response_time_ms=response_time_ms,
                    error_message=error_message,
                )
                await db.commit()
        except Exception as e:
            logger.error("[ContactEnrichment] Fire-and-forget tracking failed: %s", e)

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
        candidate_repo = CandidateRepository(db)
        candidates = await candidate_repo.search_by_linkedin_substring(
            normalized.split("/in/")[-1]
        )
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
