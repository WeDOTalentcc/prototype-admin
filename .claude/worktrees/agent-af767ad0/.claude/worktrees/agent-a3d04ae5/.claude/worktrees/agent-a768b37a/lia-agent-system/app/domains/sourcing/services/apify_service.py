"""
Apify Service for enriching company profiles with LinkedIn and Glassdoor data.
Uses Apify actors to scrape company information from external sources.
"""
import os
import logging
from typing import Dict, Optional

import httpx

logger = logging.getLogger(__name__)

APIFY_API_KEY = os.environ.get("APIFY_API_KEY", "")
APIFY_BASE_URL = "https://api.apify.com/v2"

LINKEDIN_ACTOR_ID = "voyager/linkedin-company-profile-scraper"
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


apify_service = ApifyService()
