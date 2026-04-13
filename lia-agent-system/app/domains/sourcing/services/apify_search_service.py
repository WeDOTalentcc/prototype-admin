import asyncio
import logging
import os
import time
import uuid
from dataclasses import dataclass

import httpx

from app.domains.sourcing.services.apify_service import (
    APIFY_API_KEY,
    APIFY_BASE_URL,
    EMAIL_FINDER_ACTOR_ID,
    LINKEDIN_PERSON_ACTOR_ID,
    ApifyService,
)

logger = logging.getLogger(__name__)

LINKEDIN_SEARCH_ACTOR_ID = os.environ.get(
    "APIFY_LINKEDIN_SEARCH_ACTOR",
    "curious_coder/linkedin-search",
)

APIFY_SEARCH_COST_USD = float(os.environ.get("APIFY_SEARCH_COST_USD", "0.02"))
APIFY_PROFILE_SCRAPE_COST_USD = float(os.environ.get("APIFY_PROFILE_SCRAPE_COST_USD", "0.01"))
APIFY_EMAIL_FINDER_COST_USD = float(os.environ.get("APIFY_EMAIL_FINDER_COST_USD", "0.01"))

APIFY_SEARCH_TIMEOUT = int(os.environ.get("APIFY_SEARCH_TIMEOUT_SECONDS", "120"))
APIFY_PROFILE_TIMEOUT = int(os.environ.get("APIFY_PROFILE_TIMEOUT_SECONDS", "30"))
APIFY_EMAIL_TIMEOUT = int(os.environ.get("APIFY_EMAIL_TIMEOUT_SECONDS", "15"))
APIFY_SEARCH_MAX_CONCURRENT = int(os.environ.get("APIFY_SEARCH_MAX_CONCURRENT", "5"))

APIFY_SEARCH_FALLBACK_ENABLED = os.environ.get(
    "APIFY_SEARCH_FALLBACK_ENABLED", "false"
).lower() in ("true", "1", "yes")


@dataclass
class SearchPipelineResult:
    candidates: list[dict]
    search_time_seconds: float
    profiles_scraped: int
    emails_found: int
    total_cost_usd: float
    pipeline_id: str
    errors: list[str]


class ApifySearchService:
    def __init__(self):
        self._apify = ApifyService()
        self._semaphore = asyncio.Semaphore(APIFY_SEARCH_MAX_CONCURRENT)

    async def search_candidates(
        self,
        query: str,
        location: str | None = None,
        limit: int = 15,
        company_id: str | None = None,
        user_id: str | None = None,
    ) -> SearchPipelineResult:
        pipeline_id = str(uuid.uuid4())
        start = time.time()
        errors: list[str] = []

        logger.info(
            "[ApifySearch] Starting pipeline %s: query=%r location=%r limit=%d",
            pipeline_id, query, location, limit,
        )

        linkedin_urls = await self._step1_search(query, location, limit, errors)

        if not linkedin_urls:
            logger.warning("[ApifySearch] Pipeline %s: no URLs from search step", pipeline_id)
            return SearchPipelineResult(
                candidates=[],
                search_time_seconds=round(time.time() - start, 2),
                profiles_scraped=0,
                emails_found=0,
                total_cost_usd=APIFY_SEARCH_COST_USD,
                pipeline_id=pipeline_id,
                errors=errors,
            )

        profiles = await self._step2_scrape_profiles(linkedin_urls, errors)

        emails_found = await self._step3_find_emails(profiles, errors)

        elapsed = round(time.time() - start, 2)
        total_cost = (
            APIFY_SEARCH_COST_USD
            + len(profiles) * APIFY_PROFILE_SCRAPE_COST_USD
            + emails_found * APIFY_EMAIL_FINDER_COST_USD
        )

        logger.info(
            "[ApifySearch] Pipeline %s complete: %d profiles, %d emails, $%.4f, %.1fs",
            pipeline_id, len(profiles), emails_found, total_cost, elapsed,
        )

        return SearchPipelineResult(
            candidates=profiles,
            search_time_seconds=elapsed,
            profiles_scraped=len(profiles),
            emails_found=emails_found,
            total_cost_usd=round(total_cost, 4),
            pipeline_id=pipeline_id,
            errors=errors,
        )

    async def _step1_search(
        self,
        query: str,
        location: str | None,
        limit: int,
        errors: list[str],
    ) -> list[str]:
        input_data: dict = {
            "searchTerms": [query],
            "maxResults": min(limit, 50),
            "proxy": {"useApifyProxy": True},
        }
        if location:
            input_data["location"] = location

        try:
            result = await asyncio.wait_for(
                self._apify.run_apify_actor(LINKEDIN_SEARCH_ACTOR_ID, input_data),
                timeout=APIFY_SEARCH_TIMEOUT,
            )
        except asyncio.TimeoutError:
            errors.append(f"Search actor timed out after {APIFY_SEARCH_TIMEOUT}s")
            logger.error("[ApifySearch] Step 1 timeout")
            raise
        except Exception as e:
            errors.append(f"Search actor error: {e}")
            logger.error("[ApifySearch] Step 1 error: %s", e)
            raise

        if not result:
            errors.append("Search actor returned empty result")
            return []

        items = result.get("items", [result] if isinstance(result, dict) else result)
        if not isinstance(items, list):
            items = [items]

        urls: list[str] = []
        for item in items:
            url = (
                item.get("linkedinUrl")
                or item.get("profileUrl")
                or item.get("url")
                or item.get("linkedin_url")
            )
            if url and "linkedin.com/in/" in url and url not in urls:
                urls.append(url)

        logger.info("[ApifySearch] Step 1: found %d LinkedIn URLs", len(urls))
        return urls[:limit]

    async def _step2_scrape_profiles(
        self,
        urls: list[str],
        errors: list[str],
    ) -> list[dict]:
        async def _scrape_one(url: str) -> dict | None:
            async with self._semaphore:
                try:
                    result = await asyncio.wait_for(
                        self._apify._scrape_linkedin_person(url),
                        timeout=APIFY_PROFILE_TIMEOUT,
                    )
                    if result:
                        result["linkedin_url"] = url
                        return result
                except asyncio.TimeoutError:
                    errors.append(f"Profile scrape timeout: {url}")
                except Exception as e:
                    errors.append(f"Profile scrape error ({url}): {e}")
            return None

        tasks = [_scrape_one(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        profiles = []
        for r in results:
            if isinstance(r, dict):
                profiles.append(r)
            elif isinstance(r, Exception):
                errors.append(f"Profile scrape exception: {r}")

        logger.info("[ApifySearch] Step 2: scraped %d/%d profiles", len(profiles), len(urls))
        return profiles

    async def _step3_find_emails(
        self,
        profiles: list[dict],
        errors: list[str],
    ) -> int:
        candidates_needing_email = [
            p for p in profiles
            if not p.get("emails") and p.get("first_name")
        ]

        if not candidates_needing_email:
            return 0

        found = 0

        async def _find_one(profile: dict) -> bool:
            async with self._semaphore:
                name = f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip()
                if not name:
                    return False
                try:
                    emails = await asyncio.wait_for(
                        self._apify._discover_email(name, profile.get("linkedin_url")),
                        timeout=APIFY_EMAIL_TIMEOUT,
                    )
                    if emails:
                        profile["emails"] = emails
                        return True
                except asyncio.TimeoutError:
                    errors.append(f"Email finder timeout: {name}")
                except Exception as e:
                    errors.append(f"Email finder error ({name}): {e}")
                return False

        tasks = [_find_one(p) for p in candidates_needing_email]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if r is True:
                found += 1

        logger.info(
            "[ApifySearch] Step 3: found emails for %d/%d candidates",
            found, len(candidates_needing_email),
        )
        return found

    def map_to_search_dto(self, profile: dict) -> dict:
        first = profile.get("first_name", "")
        last = profile.get("last_name", "")
        name = f"{first} {last}".strip() or profile.get("headline", "Unknown")

        emails = profile.get("emails", [])
        phones = profile.get("phones", [])

        experiences = profile.get("experience", [])
        current_title = None
        current_company = None
        if experiences:
            latest = experiences[0] if isinstance(experiences, list) else None
            if latest and isinstance(latest, dict):
                current_title = latest.get("title")
                current_company = latest.get("companyName") or latest.get("company")

        return {
            "id": str(uuid.uuid4()),
            "name": name,
            "first_name": first,
            "last_name": last,
            "headline": profile.get("headline"),
            "current_title": current_title or profile.get("headline"),
            "current_company": current_company,
            "location": profile.get("location") or profile.get("geo_location"),
            "skills": profile.get("skills", [])[:15],
            "linkedin_url": profile.get("linkedin_url"),
            "email": emails[0] if emails else None,
            "has_email": bool(emails),
            "phone": phones[0] if phones else None,
            "has_phone": bool(phones),
            "source": "apify_search",
            "summary": profile.get("summary"),
            "picture_url": profile.get("picture_url"),
            "score": None,
        }


apify_search_service = ApifySearchService()


def get_apify_search_service() -> ApifySearchService:
    return apify_search_service
