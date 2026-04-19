"""
Apify Service for enriching company and candidate profiles with LinkedIn and Glassdoor data.
Uses Apify actors to scrape information from external sources.

Supports:
- Company profile enrichment (LinkedIn, Glassdoor)
- Candidate profile enrichment (LinkedIn person profiles, email discovery)
- Salary benchmarking data
"""
import logging
import os
import time

import httpx

logger = logging.getLogger(__name__)

APIFY_API_KEY = os.environ.get("APIFY_API_KEY", "")
APIFY_BASE_URL = "https://api.apify.com/v2"

LINKEDIN_ACTOR_ID = "voyager/linkedin-company-profile-scraper"
LINKEDIN_PERSON_ACTOR_ID = "dev_fusion/Linkedin-Profile-Scraper"
LINKEDIN_LEGACY_ACTOR_ID = os.environ.get("APIFY_LEGACY_ACTOR", "anchor/linkedin-person-scraper")
EMAIL_FINDER_ACTOR_ID = "curious_coder/email-finder"
GLASSDOOR_ACTOR_ID = "bebity/glassdoor-scraper"

APIFY_COST_PER_ENRICHMENT_USD = float(os.environ.get("APIFY_COST_PER_ENRICHMENT_USD", "0.01"))
APIFY_ENRICHMENT_TIMEOUT = int(os.environ.get("APIFY_ENRICHMENT_TIMEOUT_SECONDS", "30"))
APIFY_MAX_CONCURRENT = int(os.environ.get("APIFY_MAX_CONCURRENT_ENRICHMENTS", "5"))


class ApifyService:
    """
    Service for interacting with Apify actors to enrich company data.
    """
    
    def __init__(self):
        self.api_key = APIFY_API_KEY
        self.base_url = APIFY_BASE_URL
        self.timeout = httpx.Timeout(120.0, connect=30.0)
    
    async def run_apify_actor(
        self,
        actor_id: str,
        input_data: dict,
        *,
        company_id: str | None = None,
        operation: str | None = None,
        user_id: str | None = None,
        candidate_id: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """
        Run an Apify actor and wait for results.

        Gateway-style: enforces consumption tracking + budget check per tenant.

        Args:
            actor_id: Apify actor ID (e.g., "voyager/linkedin-company-profile-scraper")
            input_data: Input parameters for the actor
            company_id: Tenant isolation — REQUIRED for production calls.
            operation: Operation name for pricing. Derived from actor_id if omitted.
            user_id: User who initiated (audit trail)
            candidate_id: Related candidate (audit trail)
            metadata: Extra fields for consumption record

        Returns:
            Dict with actor results or empty dict on failure.
        """
        if not self.api_key:
            logger.error("APIFY_API_KEY not configured")
            return {}

        # Derive operation from actor_id when not provided
        if not operation:
            low = actor_id.lower()
            if "email" in low:
                operation = "email_finder"
            elif "glassdoor" in low:
                operation = "glassdoor_scrape"
            elif "company" in low:
                operation = "company_scrape"
            elif "profile" in low or "person" in low:
                operation = "profile_scrape"
            elif "salary" in low:
                operation = "salary_benchmark"
            else:
                operation = "apify_call"

        # Budget check (fail-open)
        if company_id:
            try:
                from app.core.database import AsyncSessionLocal
                from app.domains.billing.services.consumption_tracking_service import (
                    ConsumptionTrackingService,
                )
                async with AsyncSessionLocal() as _db:
                    current = await ConsumptionTrackingService.get_monthly_apify_spend(_db, company_id)
                    limit = ConsumptionTrackingService.get_tenant_budget(company_id, "apify")
                    if current >= limit:
                        logger.warning(
                            "[ApifyGateway] BUDGET EXCEEDED tenant=%s actor=%s current=$%.2f limit=$%.2f",
                            company_id, actor_id, current, limit,
                        )
                        return {"_error": "budget_exceeded", "current_usd": current, "limit_usd": limit}
            except Exception as _budget_exc:
                logger.debug("[ApifyGateway] budget check skipped: %s", _budget_exc)
        else:
            logger.warning(
                "[ApifyGateway] call WITHOUT company_id — tenant isolation compromised. actor=%s op=%s",
                actor_id, operation,
            )

        _start_time = time.monotonic()
        _success = False
        _error_msg: str | None = None

        run_url = f"{self.base_url}/acts/{actor_id}/runs?token={self.api_key}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Starting Apify actor: {actor_id}")
                
                run_response = await client.post(
                    run_url,
                    json=input_data,
                    headers={"Content-Type": "application/json"}
                )
                run_response.raise_for_status()
                run_data = run_response.json()
                
                run_id = run_data.get("data", {}).get("id")
                if not run_id:
                    logger.error(f"No run ID returned from actor {actor_id}")
                    return {}
                
                logger.info(f"Actor {actor_id} started with run ID: {run_id}")
                
                status_url = f"{self.base_url}/actor-runs/{run_id}?token={self.api_key}"
                max_wait_seconds = 300
                poll_interval = 5
                elapsed = 0
                
                while elapsed < max_wait_seconds:
                    await self._sleep(poll_interval)
                    elapsed += poll_interval
                    
                    status_response = await client.get(status_url)
                    status_response.raise_for_status()
                    status_data = status_response.json()
                    
                    status = status_data.get("data", {}).get("status")
                    logger.debug(f"Actor run status: {status}")
                    
                    if status == "SUCCEEDED":
                        dataset_id = status_data.get("data", {}).get("defaultDatasetId")
                        if dataset_id:
                            _result = await self._get_dataset_items(client, dataset_id)
                            _success = True
                            return _result
                        _success = True
                        return {}
                    elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                        _error_msg = f"Actor run failed with status: {status}"
                        logger.error(_error_msg)
                        return {}

                _error_msg = f"Actor run timed out after {max_wait_seconds} seconds"
                logger.error(_error_msg)
                return {}

        except httpx.HTTPStatusError as e:
            _error_msg = f"HTTP error running Apify actor {actor_id}: {e.response.status_code} - {e.response.text}"
            logger.error(_error_msg)
            return {}
        except Exception as e:
            _error_msg = f"Error running Apify actor {actor_id}: {type(e).__name__}: {e}"
            logger.error(_error_msg)
            return {}
        finally:
            # Mandatory consumption tracking (success or failure)
            if company_id:
                try:
                    from app.core.database import AsyncSessionLocal
                    from app.domains.billing.services.consumption_tracking_service import (
                        ConsumptionTrackingService,
                    )
                    _duration_ms = int((time.monotonic() - _start_time) * 1000)
                    _cost = ConsumptionTrackingService.get_operation_price("apify", operation) or APIFY_COST_PER_ENRICHMENT_USD
                    async with AsyncSessionLocal() as _track_db:
                        await ConsumptionTrackingService.record_apify_call(
                            db=_track_db,
                            company_id=company_id,
                            user_id=user_id,
                            candidate_id=candidate_id,
                            linkedin_url=(metadata or {}).get("linkedin_url"),
                            operation=operation,
                            cost_usd=_cost,
                            success=_success,
                            result_status="success" if _success else "fail",
                            response_time_ms=_duration_ms,
                            error_message=_error_msg,
                            actor_id=actor_id,
                            pipeline_id=(metadata or {}).get("pipeline_id"),
                            search_session_id=(metadata or {}).get("search_session_id"),
                        )
                        await _track_db.commit()
                except Exception as _track_exc:
                    logger.error("[ApifyGateway] tracking failed: %s", _track_exc)
    
    async def _get_dataset_items(self, client: httpx.AsyncClient, dataset_id: str) -> dict:
        """Fetch items from an Apify dataset."""
        try:
            items_url = f"{self.base_url}/datasets/{dataset_id}/items?token={self.api_key}"
            response = await client.get(items_url)
            response.raise_for_status()
            items = response.json()
            
            if isinstance(items, list) and len(items) > 0:
                return items[0] if len(items) == 1 else {"items": items}
            return {}
        except Exception as e:
            logger.error(f"Error fetching dataset items: {e}")
            return {}
    
    async def _sleep(self, seconds: int):
        """Async sleep helper."""
        import asyncio
        await asyncio.sleep(seconds)
    
    async def scrape_linkedin_company(
        self,
        linkedin_url: str,
        *,
        company_id: str | None = None,
        user_id: str | None = None,
    ) -> dict:
        """
        Scrape LinkedIn company profile data.
        
        Args:
            linkedin_url: URL of the LinkedIn company page
            
        Returns:
            Dict with company data including mission, culture, values if found
        """
        if not linkedin_url:
            logger.warning("No LinkedIn URL provided")
            return {}
        
        logger.info(f"Scraping LinkedIn company: {linkedin_url}")
        
        input_data = {
            "startUrls": [{"url": linkedin_url}],
            "proxy": {
                "useApifyProxy": True
            }
        }
        
        result = await self.run_apify_actor(
            LINKEDIN_ACTOR_ID, input_data,
            company_id=company_id, user_id=user_id,
            operation="company_scrape",
            metadata={"linkedin_url": linkedin_url},
        )
        
        if result:
            return self._extract_linkedin_culture_data(result)
        
        return {}
    
    async def scrape_glassdoor_company(
        self,
        company_name: str,
        *,
        company_id: str | None = None,
        user_id: str | None = None,
    ) -> dict:
        """
        Scrape Glassdoor company data including reviews and culture.
        
        Args:
            company_name: Name of the company to search on Glassdoor
            
        Returns:
            Dict with company culture data from Glassdoor
        """
        if not company_name:
            logger.warning("No company name provided for Glassdoor scraping")
            return {}
        
        logger.info(f"Scraping Glassdoor for company: {company_name}")
        
        input_data = {
            "searchQueries": [company_name],
            "maxResults": 1,
            "includeReviews": True,
            "maxReviews": 10,
            "proxy": {
                "useApifyProxy": True
            }
        }
        
        result = await self.run_apify_actor(
            GLASSDOOR_ACTOR_ID, input_data,
            company_id=company_id, user_id=user_id,
            operation="glassdoor_scrape",
            metadata={"company_name": company_name},
        )
        
        if result:
            return self._extract_glassdoor_culture_data(result)
        
        return {}
    
    def _extract_linkedin_culture_data(self, data: dict) -> dict:
        """Extract relevant culture data from LinkedIn scrape results."""
        extracted = {}
        
        if "items" in data:
            data = data["items"][0] if data["items"] else {}
        
        if data.get("description"):
            extracted["description"] = data["description"]
        
        if data.get("tagline"):
            extracted["tagline"] = data["tagline"]
        
        if data.get("specialties"):
            extracted["specialties"] = data["specialties"]
        
        if data.get("industries"):
            extracted["industries"] = data["industries"]
        
        if data.get("companySize"):
            extracted["company_size"] = data["companySize"]
        
        if data.get("headquarters"):
            extracted["headquarters"] = data["headquarters"]
        
        if data.get("foundedOn"):
            extracted["founded"] = data["foundedOn"]
        
        if data.get("website"):
            extracted["website"] = data["website"]
        
        culture_keywords = ["culture", "values", "mission", "vision", "about"]
        for key, value in data.items():
            if any(kw in key.lower() for kw in culture_keywords):
                extracted[key] = value
        
        extracted["source"] = "linkedin"
        
        return extracted
    
    def _extract_glassdoor_culture_data(self, data: dict) -> dict:
        """Extract relevant culture data from Glassdoor scrape results."""
        extracted = {}
        
        if "items" in data:
            data = data["items"][0] if data["items"] else {}
        
        if data.get("rating"):
            extracted["overall_rating"] = data["rating"]
        
        if data.get("reviews"):
            reviews = data["reviews"]
            if isinstance(reviews, list):
                pros = []
                cons = []
                for review in reviews[:10]:
                    if review.get("pros"):
                        pros.append(review["pros"])
                    if review.get("cons"):
                        cons.append(review["cons"])
                
                if pros:
                    extracted["employee_pros"] = pros
                if cons:
                    extracted["employee_cons"] = cons
        
        if data.get("cultureAndValues"):
            extracted["culture_rating"] = data["cultureAndValues"]
        
        if data.get("workLifeBalance"):
            extracted["work_life_balance"] = data["workLifeBalance"]
        
        if data.get("seniorManagement"):
            extracted["management_rating"] = data["seniorManagement"]
        
        if data.get("careerOpportunities"):
            extracted["career_opportunities"] = data["careerOpportunities"]
        
        if data.get("compensationAndBenefits"):
            extracted["compensation_rating"] = data["compensationAndBenefits"]
        
        if data.get("mission"):
            extracted["mission"] = data["mission"]
        
        if data.get("overview"):
            extracted["overview"] = data["overview"]
        
        extracted["source"] = "glassdoor"
        
        return extracted


    async def enrich_candidate_profile(
        self,
        linkedin_url: str | None = None,
        candidate_name: str | None = None,
        candidate_email: str | None = None,
        *,
        company_id: str | None = None,
        user_id: str | None = None,
        candidate_id: str | None = None,
    ) -> dict:
        """
        Enrich a candidate profile with data from LinkedIn and email discovery.

        Used by SourcingReActAgent (E4) to gather complementary data for
        candidates found during talent search.

        Args:
            linkedin_url: LinkedIn profile URL of the candidate
            candidate_name: Full name of the candidate (for fallback search)
            candidate_email: Known email for reverse lookup

        Returns:
            Dict with enriched profile data:
            {
                "linkedin": {...},   # LinkedIn profile data
                "emails": [...],     # Discovered email addresses
                "social_profiles": [...],
                "source": "apify",
            }
        """
        # Propagate tenant context for downstream run_apify_actor calls
        self._current_company_id = company_id
        self._current_user_id = user_id
        self._current_candidate_id = candidate_id
        enriched: dict = {"source": "apify"}

        if linkedin_url:
            try:
                linkedin_data = await self._scrape_linkedin_person(linkedin_url)
                if linkedin_data:
                    enriched["linkedin"] = linkedin_data
            except Exception as e:
                logger.warning("[Apify] LinkedIn person scrape failed: %s", e)

        if candidate_name and not candidate_email:
            try:
                email_data = await self._discover_email(candidate_name, linkedin_url)
                if email_data:
                    enriched["emails"] = email_data
            except Exception as e:
                logger.warning("[Apify] Email discovery failed: %s", e)

        if not enriched.get("linkedin") and not enriched.get("emails"):
            logger.info("[Apify] No enrichment data found for candidate")

        return enriched

    async def _scrape_linkedin_person(self, linkedin_url: str) -> dict:
        """Scrape a LinkedIn person profile via Apify actor."""
        if not linkedin_url:
            return {}

        logger.info("[Apify] Scraping LinkedIn person: %s", linkedin_url)

        input_data = {
            "startUrls": [{"url": linkedin_url}],
            "proxy": {"useApifyProxy": True},
        }

        result = await self.run_apify_actor(
            LINKEDIN_PERSON_ACTOR_ID, input_data,
            company_id=getattr(self, "_current_company_id", None),
            user_id=getattr(self, "_current_user_id", None),
            candidate_id=getattr(self, "_current_candidate_id", None),
            operation="profile_scrape",
        )
        if not result:
            return {}

        if "items" in result:
            result = result["items"][0] if result["items"] else {}

        extracted = {}
        field_map = {
            "firstName": "first_name",
            "lastName": "last_name",
            "headline": "headline",
            "summary": "summary",
            "location": "location",
            "industryName": "industry",
            "connectionCount": "connections",
            "profilePicture": "picture_url",
            "geoCountryName": "country",
            "geoLocationName": "geo_location",
            "followerCount": "follower_count",
            "publicIdentifier": "public_identifier",
        }
        for src_key, dst_key in field_map.items():
            if result.get(src_key):
                extracted[dst_key] = result[src_key]

        emails = []
        if result.get("email"):
            emails.append(result["email"])
        if result.get("emails") and isinstance(result["emails"], list):
            emails.extend(result["emails"])
        if result.get("emailAddress"):
            emails.append(result["emailAddress"])
        if emails:
            extracted["emails"] = list(set(emails))

        phones = []
        if result.get("phone"):
            phones.append(result["phone"])
        if result.get("phones") and isinstance(result["phones"], list):
            phones.extend(result["phones"])
        if result.get("phoneNumbers") and isinstance(result["phoneNumbers"], list):
            for pn in result["phoneNumbers"]:
                if isinstance(pn, dict):
                    num = pn.get("number") or pn.get("value") or pn.get("phone")
                    if num:
                        phones.append(str(num))
                elif isinstance(pn, str):
                    phones.append(pn)
        if result.get("mobilePhone"):
            phones.append(result["mobilePhone"])
        if phones:
            extracted["phones"] = list(set(phones))

        if result.get("experience"):
            experiences = result["experience"]
            if isinstance(experiences, list):
                extracted["experience"] = [
                    {
                        "title": exp.get("title", ""),
                        "companyName": exp.get("companyName", exp.get("company", "")),
                        "company": exp.get("companyName", exp.get("company", "")),
                        "duration": exp.get("timePeriod", exp.get("duration", "")),
                        "location": exp.get("locationName", exp.get("location", "")),
                        "description": exp.get("description", ""),
                        "startDate": exp.get("startDate", exp.get("start", "")),
                        "endDate": exp.get("endDate", exp.get("end", "")),
                        "companyUrl": exp.get("companyUrl", exp.get("companyLinkedinUrl", "")),
                    }
                    for exp in experiences[:10]
                ]

        if result.get("skills"):
            skills = result["skills"]
            if isinstance(skills, list):
                extracted["skills"] = [
                    s.get("name", s) if isinstance(s, dict) else str(s)
                    for s in skills[:30]
                ]

        if result.get("education") or result.get("educations"):
            education = result.get("education") or result.get("educations")
            if isinstance(education, list):
                extracted["education"] = [
                    {
                        "schoolName": edu.get("schoolName", edu.get("school", "")),
                        "school": edu.get("schoolName", edu.get("school", "")),
                        "degree": edu.get("degreeName", edu.get("degree", "")),
                        "degreeName": edu.get("degreeName", edu.get("degree", "")),
                        "fieldOfStudy": edu.get("fieldOfStudy", edu.get("field", "")),
                        "startDate": edu.get("startDate", edu.get("start", "")),
                        "endDate": edu.get("endDate", edu.get("end", "")),
                        "description": edu.get("description", edu.get("activities", "")),
                    }
                    for edu in education[:10]
                ]

        if result.get("certifications"):
            certs = result["certifications"]
            if isinstance(certs, list):
                extracted["certifications"] = [
                    c.get("name", c) if isinstance(c, dict) else str(c)
                    for c in certs[:10]
                ]

        if result.get("languages"):
            langs = result["languages"]
            if isinstance(langs, list):
                extracted["languages"] = [
                    {
                        "name": lang.get("name", lang) if isinstance(lang, dict) else str(lang),
                        "proficiency": lang.get("proficiency", "") if isinstance(lang, dict) else "",
                    }
                    for lang in langs[:10]
                ]

        if result.get("volunteerExperiences"):
            extracted["volunteer"] = result["volunteerExperiences"][:5]

        if result.get("projects"):
            extracted["projects"] = result["projects"][:5]

        if result.get("honors") or result.get("honorsAndAwards"):
            extracted["honors"] = (result.get("honors") or result.get("honorsAndAwards", []))[:5]

        extracted["source"] = "linkedin"
        return extracted

    async def _discover_email(
        self, candidate_name: str, linkedin_url: str | None = None
    ) -> list[str]:
        """Attempt to discover candidate emails via Apify email finder."""
        if not candidate_name:
            return []

        logger.info("[Apify] Discovering email for: %s", candidate_name)

        input_data: dict = {"name": candidate_name}
        if linkedin_url:
            input_data["linkedinUrl"] = linkedin_url

        result = await self.run_apify_actor(
            EMAIL_FINDER_ACTOR_ID, input_data,
            company_id=getattr(self, "_current_company_id", None),
            user_id=getattr(self, "_current_user_id", None),
            candidate_id=getattr(self, "_current_candidate_id", None),
            operation="email_finder",
        )
        if not result:
            return []

        emails: list[str] = []
        if isinstance(result, dict):
            if result.get("email"):
                emails.append(result["email"])
            if result.get("emails") and isinstance(result["emails"], list):
                emails.extend(result["emails"])
            if result.get("items") and isinstance(result["items"], list):
                for item in result["items"]:
                    if isinstance(item, dict) and item.get("email"):
                        emails.append(item["email"])

        return list(set(emails))

    async def scrape_salary_data(
        self,
        job_title: str,
        location: str,
    ) -> dict:
        """
        Scrapes salary data via Apify actors.
        Strategy: Google Jobs -> Indeed -> fallback empty.
        Returns dict with salaries list (BRL values).
        """
        import re as _re

        actors = [
            {
                "id": "hMvNSpz3JnHgl5jkh",
                "input": {"queries": [f"{job_title} {location}"], "maxPagesPerQuery": 3},
            },
            {
                "id": "misceres/indeed-scraper",
                "input": {"position": job_title, "location": location, "maxItems": 30},
            },
        ]

        for actor_cfg in actors:
            try:
                result = await self.run_apify_actor(
                    actor_cfg["id"], actor_cfg["input"],
                    company_id=getattr(self, "_current_company_id", None),
                    user_id=getattr(self, "_current_user_id", None),
                    operation="salary_benchmark",
                )
                if not result:
                    continue
                items = result if isinstance(result, list) else result.get("items", [])
                salaries = self._extract_salaries(items)
                if salaries:
                    logger.info("[Apify] Salary data from %s: %d values", actor_cfg["id"], len(salaries))
                    return {"salaries": salaries}
            except Exception as exc:
                logger.warning("[Apify] Actor %s failed: %s", actor_cfg["id"], exc)
        return {}

    @staticmethod
    def _extract_salaries(items: list) -> list[float]:
        """Extract salary values from job listing results."""
        import re as _re
        salaries = []
        for item in items:
            for key in ("salary", "salaryRange", "estimatedSalary", "compensation", "salaryText"):
                val = item.get(key)
                if val is None:
                    continue
                if isinstance(val, (int, float)) and 1000 < val < 200000:
                    salaries.append(float(val))
                    break
                elif isinstance(val, str):
                    cleaned = val.replace(".", "").replace(",", ".")
                    nums = _re.findall(r"[0-9]+\.?[0-9]*", cleaned)
                    for n in nums:
                        try:
                            v = float(n)
                            if 1000 < v < 200000:
                                salaries.append(v)
                        except ValueError:
                            pass
                    if salaries:
                        break
                elif isinstance(val, dict):
                    for sub in ("min", "max", "median", "value"):
                        sv = val.get(sub)
                        if isinstance(sv, (int, float)) and 1000 < sv < 200000:
                            salaries.append(float(sv))
                    if salaries:
                        break
        return salaries


apify_service = ApifyService()
