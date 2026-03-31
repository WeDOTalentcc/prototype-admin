"""
Apify Service for enriching company and candidate profiles with LinkedIn and Glassdoor data.
Uses Apify actors to scrape information from external sources.

Supports:
- Company profile enrichment (LinkedIn, Glassdoor)
- Candidate profile enrichment (LinkedIn person profiles, email discovery)
- Salary benchmarking data
"""
import os
import logging
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

APIFY_API_KEY = os.environ.get("APIFY_API_KEY", "")
APIFY_BASE_URL = "https://api.apify.com/v2"

LINKEDIN_ACTOR_ID = "voyager/linkedin-company-profile-scraper"
LINKEDIN_PERSON_ACTOR_ID = "anchor/linkedin-profile-scraper"
EMAIL_FINDER_ACTOR_ID = "curious_coder/email-finder"
GLASSDOOR_ACTOR_ID = "bebity/glassdoor-scraper"


class ApifyService:
    """
    Service for interacting with Apify actors to enrich company data.
    """
    
    def __init__(self):
        self.api_key = APIFY_API_KEY
        self.base_url = APIFY_BASE_URL
        self.timeout = httpx.Timeout(120.0, connect=30.0)
    
    async def run_apify_actor(self, actor_id: str, input_data: dict) -> dict:
        """
        Run an Apify actor and wait for results.
        
        Args:
            actor_id: The Apify actor ID (e.g., "voyager/linkedin-company-profile-scraper")
            input_data: Input parameters for the actor
            
        Returns:
            Dict with actor results or empty dict on failure
        """
        if not self.api_key:
            logger.error("APIFY_API_KEY not configured")
            return {}
        
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
                            return await self._get_dataset_items(client, dataset_id)
                        return {}
                    elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                        logger.error(f"Actor run failed with status: {status}")
                        return {}
                
                logger.error(f"Actor run timed out after {max_wait_seconds} seconds")
                return {}
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error running Apify actor {actor_id}: {e.response.status_code} - {e.response.text}")
            return {}
        except Exception as e:
            logger.error(f"Error running Apify actor {actor_id}: {type(e).__name__}: {e}")
            return {}
    
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
    
    async def scrape_linkedin_company(self, linkedin_url: str) -> dict:
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
        
        result = await self.run_apify_actor(LINKEDIN_ACTOR_ID, input_data)
        
        if result:
            return self._extract_linkedin_culture_data(result)
        
        return {}
    
    async def scrape_glassdoor_company(self, company_name: str) -> dict:
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
        
        result = await self.run_apify_actor(GLASSDOOR_ACTOR_ID, input_data)
        
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
        linkedin_url: Optional[str] = None,
        candidate_name: Optional[str] = None,
        candidate_email: Optional[str] = None,
    ) -> Dict:
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
        enriched: Dict = {"source": "apify"}

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

    async def _scrape_linkedin_person(self, linkedin_url: str) -> Dict:
        """Scrape a LinkedIn person profile via Apify actor."""
        if not linkedin_url:
            return {}

        logger.info("[Apify] Scraping LinkedIn person: %s", linkedin_url)

        input_data = {
            "startUrls": [{"url": linkedin_url}],
            "proxy": {"useApifyProxy": True},
        }

        result = await self.run_apify_actor(LINKEDIN_PERSON_ACTOR_ID, input_data)
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
        }
        for src_key, dst_key in field_map.items():
            if result.get(src_key):
                extracted[dst_key] = result[src_key]

        if result.get("experience"):
            experiences = result["experience"]
            if isinstance(experiences, list):
                extracted["experience"] = [
                    {
                        "title": exp.get("title", ""),
                        "company": exp.get("companyName", ""),
                        "duration": exp.get("timePeriod", ""),
                        "location": exp.get("locationName", ""),
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

        if result.get("education"):
            education = result["education"]
            if isinstance(education, list):
                extracted["education"] = [
                    {
                        "school": edu.get("schoolName", ""),
                        "degree": edu.get("degreeName", ""),
                        "field": edu.get("fieldOfStudy", ""),
                    }
                    for edu in education[:5]
                ]

        if result.get("certifications"):
            certs = result["certifications"]
            if isinstance(certs, list):
                extracted["certifications"] = [
                    c.get("name", c) if isinstance(c, dict) else str(c)
                    for c in certs[:10]
                ]

        extracted["source"] = "linkedin"
        return extracted

    async def _discover_email(
        self, candidate_name: str, linkedin_url: Optional[str] = None
    ) -> List[str]:
        """Attempt to discover candidate emails via Apify email finder."""
        if not candidate_name:
            return []

        logger.info("[Apify] Discovering email for: %s", candidate_name)

        input_data: Dict = {"name": candidate_name}
        if linkedin_url:
            input_data["linkedinUrl"] = linkedin_url

        result = await self.run_apify_actor(EMAIL_FINDER_ACTOR_ID, input_data)
        if not result:
            return []

        emails: List[str] = []
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
        Scrapes salary data from Glassdoor/LinkedIn via Apify.
        Returns dict with 'salaries' list (BRL values).
        Fail-open: returns empty dict on error.
        """
        try:
            actor_id = "bebity/glassdoor-salary-scraper"
            run_input = {
                "jobTitle": job_title,
                "location": location,
                "maxItems": 50,
            }
            result = await self.run_apify_actor(actor_id, run_input)
            if not result or not isinstance(result, (list, dict)):
                return {}
            items = result if isinstance(result, list) else result.get("items", [])
            salaries = []
            for item in items:
                salary = item.get("salary") or item.get("basePayAmount")
                if salary and isinstance(salary, (int, float)) and salary > 0:
                    salaries.append(float(salary))
            return {"salaries": salaries} if salaries else {}
        except Exception as exc:
            logger.warning("[Apify] scrape_salary_data failed: %s", exc)
            return {}


apify_service = ApifyService()
