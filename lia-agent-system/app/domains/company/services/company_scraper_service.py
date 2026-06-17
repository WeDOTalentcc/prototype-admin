"""
Company Web Scraper Service.
Extracts culture-related content from company websites using Apify.
Supports multi-source extraction: Website + LinkedIn.
Now with MCP (Model Context Protocol) support for simplified actor calls.
"""
import asyncio
import logging
import os
import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

APIFY_API_TOKEN = os.getenv("APIFY_API_KEY", "")
APIFY_ACTOR_ID = "apify~website-content-crawler"
LINKEDIN_ACTOR_ID = "bebity~linkedin-premium-actor"

USE_MCP = os.getenv("USE_APIFY_MCP", "false").lower() == "true"

CULTURE_PAGE_PATTERNS = [
    r'/about',
    r'/sobre',
    r'/quem-somos',
    r'/who-we-are',
    r'/careers',
    r'/carreiras',
    r'/trabalhe-conosco',
    r'/jobs',
    r'/vagas',
    r'/culture',
    r'/cultura',
    r'/our-culture',
    r'/nossa-cultura',
    r'/values',
    r'/valores',
    r'/mission',
    r'/missao',
    r'/company',
    r'/empresa',
    r'/team',
    r'/time',
    r'/equipe',
    r'/life-at',
    r'/vida-na',
]

CULTURE_KEYWORDS = [
    'about', 'sobre', 'quem somos', 'careers', 'carreiras',
    'trabalhe', 'culture', 'cultura', 'values', 'valores',
    'team', 'equipe', 'time', 'company', 'empresa', 'mission',
    'missao', 'vision', 'visao'
]


class CompanyScraperService:
    """
    Service for scraping company websites to extract culture-related content.
    Uses Apify Website Content Crawler for reliable extraction.
    Supports LinkedIn company page scraping for structured data.
    Now with MCP (Model Context Protocol) support for simplified actor calls.
    """
    
    def __init__(self):
        self.apify_token = APIFY_API_TOKEN
        self.timeout = httpx.Timeout(120.0, connect=30.0)
        self.use_mcp = USE_MCP
        self._mcp_client = None
    
    def _get_mcp_client(self):
        """Lazy load MCP client."""
        if self._mcp_client is None:
            from app.domains.sourcing.services.apify_mcp_client import ApifyMCPClient
            self._mcp_client = ApifyMCPClient()
        return self._mcp_client
    
    async def scrape_website(self, url: str, linkedin_url: str | None = None) -> dict:
        """
        Main entry point: scrapes a company website for culture content using Apify.
        Optionally also scrapes LinkedIn for structured company data.
        Supports MCP mode when USE_APIFY_MCP=true environment variable is set.
        
        Args:
            url: The company website URL
            linkedin_url: Optional LinkedIn company page URL
            
        Returns:
            Dict with scraped content, discovered pages, LinkedIn URL, and structured LinkedIn data
        """
        logger.info(f"Starting website scrape for: {url}")
        
        if self.use_mcp:
            logger.info("Using MCP mode for Apify calls")
            return await self._scrape_with_mcp(url, linkedin_url)
        
        return await self._scrape_website_http(url, linkedin_url)
    
    async def _scrape_with_mcp(self, url: str, linkedin_url: str | None = None) -> dict:
        """
        Scrape website using MCP client instead of direct HTTP API calls.
        
        Args:
            url: Website URL to scrape
            linkedin_url: Optional LinkedIn company page URL
            
        Returns:
            Dict with scraped content matching the existing return schema
        """
        base_url = self._normalize_url(url)
        mcp = self._get_mcp_client()
        
        try:
            website_result = await mcp.scrape_website(base_url)
            
            if isinstance(website_result, dict) and website_result.get("error"):
                logger.warning(f"MCP website scrape failed: {website_result.get('error')}")
                return await self._scrape_with_httpx(base_url)
            
            all_content = []
            scraped_pages = []
            discovered_linkedin = None
            
            if isinstance(website_result, list):
                for item in website_result:
                    page_url = item.get("url", "")
                    text = item.get("text", "") or item.get("markdown", "") or ""
                    if text:
                        page_type = self._categorize_page(page_url)
                        all_content.append(f"[{page_type.upper()}]\nURL: {page_url}\n{text}\n")
                        scraped_pages.append(page_url)
            elif isinstance(website_result, dict):
                if "text" in website_result or "markdown" in website_result:
                    text = website_result.get("text", "") or website_result.get("markdown", "")
                    all_content.append(f"[CONTENT]\n{text}\n")
            
            combined_content = "\n---\n".join(all_content)
            if len(combined_content) > 50000:
                combined_content = combined_content[:50000] + "\n[CONTENT TRUNCATED]"
            
            result = {
                "success": bool(combined_content),
                "content": combined_content,
                "pages": scraped_pages,
                "linkedin_url": linkedin_url or discovered_linkedin,
                "pages_scraped": len(scraped_pages),
                "source": "mcp",
                "linkedin_data": {}
            }
            
            if linkedin_url:
                linkedin_data = await mcp.scrape_linkedin_company(linkedin_url)
                if isinstance(linkedin_data, dict) and not linkedin_data.get("error"):
                    result["linkedin_data"] = self._parse_linkedin_data(linkedin_data)
            
            return result
            
        except Exception as e:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.error(f"MCP scrape error: {type(e).__name__}: {e}")
            return await self._scrape_with_httpx(base_url)
    
    async def _scrape_website_http(self, url: str, linkedin_url: str | None = None) -> dict:
        """Original HTTP-based scraping method."""
        base_url = self._normalize_url(url)
        
        website_result = None
        linkedin_result = None
        
        if self.apify_token:
            logger.info("Using Apify Website Content Crawler")
            website_result = await self._scrape_with_apify(base_url)
            if not website_result["success"]:
                logger.warning(f"Apify scrape failed: {website_result.get('error')}, trying fallback")
                website_result = await self._scrape_with_httpx(base_url)
            
            if linkedin_url:
                logger.info(f"Scraping LinkedIn company page: {linkedin_url}")
                linkedin_result = await self._scrape_linkedin_with_apify(linkedin_url)
            elif website_result.get("linkedin_url"):
                discovered_linkedin = website_result.get("linkedin_url")
                if discovered_linkedin:
                    logger.info(f"Discovered LinkedIn URL, scraping: {discovered_linkedin}")
                    linkedin_result = await self._scrape_linkedin_with_apify(discovered_linkedin)
        else:
            logger.info("Using fallback httpx scraper")
            website_result = await self._scrape_with_httpx(base_url)
        
        if linkedin_result and linkedin_result.get("success"):
            website_result["linkedin_data"] = linkedin_result.get("data", {})
            if not website_result.get("linkedin_url"):
                website_result["linkedin_url"] = linkedin_url or website_result.get("linkedin_url")
        else:
            website_result["linkedin_data"] = {}
        
        return website_result
    
    async def _scrape_linkedin_with_apify(self, linkedin_url: str) -> dict:
        """
        Scrape LinkedIn company page using Apify bebity/linkedin-premium-actor.
        
        Args:
            linkedin_url: LinkedIn company page URL
            
        Returns:
            Dict with structured company data
        """
        if not self.apify_token:
            return {
                "success": False,
                "error": "Apify token not configured",
                "data": {}
            }
        
        try:
            linkedin_url = linkedin_url.split('?')[0].rstrip('/')
            
            run_input = {
                "action": "get-companies",
                "keywords": [linkedin_url],
                "isUrl": True,
                "limit": 1
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                run_url = f"https://api.apify.com/v2/acts/{LINKEDIN_ACTOR_ID}/runs"
                headers = {
                    "Authorization": f"Bearer {self.apify_token}",
                    "Content-Type": "application/json"
                }
                
                logger.info(f"Starting LinkedIn Apify actor run for {linkedin_url}")
                response = await client.post(run_url, json=run_input, headers=headers)
                
                if response.status_code != 201:
                    error_text = response.text
                    logger.error(f"Failed to start LinkedIn Apify run: {response.status_code} - {error_text}")
                    return {
                        "success": False,
                        "error": f"LinkedIn Apify API error: {response.status_code}",
                        "data": {}
                    }
                
                run_data = response.json()
                run_id = run_data["data"]["id"]
                dataset_id = run_data["data"]["defaultDatasetId"]
                
                logger.info(f"LinkedIn Apify run started: {run_id}, waiting for completion...")
                
                max_wait = 90
                poll_interval = 3
                elapsed = 0
                
                while elapsed < max_wait:
                    await asyncio.sleep(poll_interval)
                    elapsed += poll_interval
                    
                    status_url = f"https://api.apify.com/v2/actor-runs/{run_id}"
                    status_response = await client.get(status_url, headers=headers)
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        run_status = status_data["data"]["status"]
                        
                        logger.info(f"LinkedIn Apify run status: {run_status} (elapsed: {elapsed}s)")
                        
                        if run_status == "SUCCEEDED":
                            break
                        elif run_status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                            return {
                                "success": False,
                                "error": f"LinkedIn Apify run {run_status}",
                                "data": {}
                            }
                
                if elapsed >= max_wait:
                    logger.warning("LinkedIn Apify run timed out")
                    return {
                        "success": False,
                        "error": "LinkedIn scraping timed out",
                        "data": {}
                    }
                
                dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?format=json"
                dataset_response = await client.get(dataset_url, headers=headers)
                
                if dataset_response.status_code != 200:
                    return {
                        "success": False,
                        "error": "Failed to fetch LinkedIn Apify results",
                        "data": {}
                    }
                
                items = dataset_response.json()
                
                if not items:
                    return {
                        "success": False,
                        "error": "No LinkedIn data extracted",
                        "data": {}
                    }
                
                company_data = items[0] if items else {}
                
                structured_data = self._parse_linkedin_data(company_data)
                
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.info(f"LinkedIn scrape completed: extracted data for {structured_data.get('name', 'unknown')}")
                
                return {
                    "success": True,
                    "data": structured_data,
                    "raw_data": company_data
                }
                
        except Exception as e:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.error(f"Error in LinkedIn Apify scrape: {type(e).__name__}: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": {}
            }
    
    def _parse_linkedin_data(self, raw_data: dict) -> dict:
        """
        Parse raw LinkedIn data into structured format.
        
        Args:
            raw_data: Raw data from LinkedIn scraper
            
        Returns:
            Structured company data
        """
        employee_count = None
        company_size = None
        
        employee_range = raw_data.get("employeeCount") or raw_data.get("staffCount") or raw_data.get("employeeCountRange")
        if employee_range:
            if isinstance(employee_range, int):
                employee_count = employee_range
            elif isinstance(employee_range, str):
                numbers = re.findall(r'\d+', employee_range.replace(',', ''))
                if numbers:
                    employee_count = int(numbers[-1])
        
        if employee_count:
            if employee_count <= 50:
                company_size = "Startup"
            elif employee_count <= 500:
                company_size = "PME"
            elif employee_count <= 5000:
                company_size = "Média-Grande"
            else:
                company_size = "Enterprise"
        
        founded_year = None
        founded = raw_data.get("foundedYear") or raw_data.get("founded")
        if founded:
            try:
                founded_year = int(str(founded)[:4])
            except (ValueError, TypeError):
                pass
        
        locations = []
        if raw_data.get("locations"):
            for loc in raw_data.get("locations", []):
                if isinstance(loc, dict):
                    loc_str = loc.get("city", "") or loc.get("address", "")
                    if loc_str:
                        locations.append(loc_str)
                elif isinstance(loc, str):
                    locations.append(loc)
        
        headquarters = raw_data.get("headquarters") or raw_data.get("headquarter")
        if isinstance(headquarters, dict):
            headquarters = headquarters.get("city") or headquarters.get("address") or ""
        
        specialties = raw_data.get("specialties") or raw_data.get("specialities") or []
        if isinstance(specialties, str):
            specialties = [s.strip() for s in specialties.split(',')]
        
        return {
            "name": raw_data.get("name") or raw_data.get("companyName"),
            "industry": raw_data.get("industry") or raw_data.get("industries", [None])[0] if isinstance(raw_data.get("industries"), list) else raw_data.get("industries"),
            "employee_count": employee_count,
            "company_size": company_size,
            "headquarters": headquarters,
            "locations": locations,
            "founded_year": founded_year,
            "description": raw_data.get("description") or raw_data.get("tagline"),
            "website": raw_data.get("website") or raw_data.get("companyUrl"),
            "specialties": specialties,
            "logo_url": raw_data.get("logo") or raw_data.get("logoUrl"),
            "follower_count": raw_data.get("followerCount") or raw_data.get("followersCount"),
        }
    
    async def _scrape_with_apify(self, base_url: str) -> dict:
        """
        Scrape website using Apify Website Content Crawler.
        """
        try:
            run_input = {
                "startUrls": [{"url": base_url}],
                "maxCrawlPages": 15,
                "maxCrawlDepth": 2,
                "crawlerType": "playwright:adaptive",
                "includeUrlGlobs": [
                    f"{base_url}*about*",
                    f"{base_url}*sobre*",
                    f"{base_url}*quem-somos*",
                    f"{base_url}*careers*",
                    f"{base_url}*carreiras*",
                    f"{base_url}*culture*",
                    f"{base_url}*cultura*",
                    f"{base_url}*values*",
                    f"{base_url}*valores*",
                    f"{base_url}*mission*",
                    f"{base_url}*company*",
                    f"{base_url}*empresa*",
                    f"{base_url}*team*",
                    f"{base_url}*equipe*",
                    f"{base_url}*trabalhe*",
                ],
                "excludeUrlGlobs": [
                    "*login*", "*signin*", "*cart*", "*checkout*",
                    "*blog/*", "*news/*", "*produto*", "*product*",
                    "*.pdf", "*.doc*", "*.xls*"
                ],
                "removeElementsCssSelector": "nav, footer, header, aside, .cookie, .popup, .modal, .banner, .advertisement, script, style, noscript",
                "maxResults": 15,
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                run_url = f"https://api.apify.com/v2/acts/{APIFY_ACTOR_ID}/runs"
                headers = {
                    "Authorization": f"Bearer {self.apify_token}",
                    "Content-Type": "application/json"
                }
                
                logger.info(f"Starting Apify actor run for {base_url}")
                response = await client.post(run_url, json=run_input, headers=headers)
                
                if response.status_code != 201:
                    error_text = response.text
                    logger.error(f"Failed to start Apify run: {response.status_code} - {error_text}")
                    return {
                        "success": False,
                        "error": f"Apify API error: {response.status_code}",
                        "content": "",
                        "pages": [],
                        "linkedin_url": None
                    }
                
                run_data = response.json()
                run_id = run_data["data"]["id"]
                dataset_id = run_data["data"]["defaultDatasetId"]
                
                logger.info(f"Apify run started: {run_id}, waiting for completion...")
                
                max_wait = 120
                poll_interval = 3
                elapsed = 0
                
                while elapsed < max_wait:
                    await asyncio.sleep(poll_interval)
                    elapsed += poll_interval
                    
                    status_url = f"https://api.apify.com/v2/actor-runs/{run_id}"
                    status_response = await client.get(status_url, headers=headers)
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        run_status = status_data["data"]["status"]
                        
                        logger.info(f"Apify run status: {run_status} (elapsed: {elapsed}s)")
                        
                        if run_status == "SUCCEEDED":
                            break
                        elif run_status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                            return {
                                "success": False,
                                "error": f"Apify run {run_status}",
                                "content": "",
                                "pages": [],
                                "linkedin_url": None
                            }
                
                if elapsed >= max_wait:
                    logger.warning("Apify run timed out, fetching partial results")
                
                dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?format=json"
                dataset_response = await client.get(dataset_url, headers=headers)
                
                if dataset_response.status_code != 200:
                    return {
                        "success": False,
                        "error": "Failed to fetch Apify results",
                        "content": "",
                        "pages": [],
                        "linkedin_url": None
                    }
                
                items = dataset_response.json()
                
                if not items:
                    return {
                        "success": False,
                        "error": "No content extracted by Apify",
                        "content": "",
                        "pages": [],
                        "linkedin_url": None
                    }
                
                all_content = []
                scraped_pages = []
                linkedin_url = None
                
                for item in items:
                    page_url = item.get("url", "")
                    text = item.get("text", "") or item.get("markdown", "") or ""
                    
                    if text:
                        page_type = self._categorize_page(page_url)
                        all_content.append(f"[{page_type.upper()}]\nURL: {page_url}\n{text}\n")
                        scraped_pages.append(page_url)
                        
                        if not linkedin_url:
                            html = item.get("html", "")
                            if html:
                                linkedin_url = self._find_linkedin_url(html, base_url)
                
                combined_content = "\n---\n".join(all_content)
                
                if len(combined_content) > 50000:
                    combined_content = combined_content[:50000] + "\n[CONTENT TRUNCATED]"
                
                logger.info(f"Apify scrape completed: {len(scraped_pages)} pages extracted")
                
                return {
                    "success": True,
                    "content": combined_content,
                    "pages": scraped_pages,
                    "linkedin_url": linkedin_url,
                    "pages_discovered": len(items),
                    "pages_scraped": len(scraped_pages),
                    "source": "apify"
                }
                
        except Exception as e:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.error(f"Error in Apify scrape: {type(e).__name__}: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": "",
                "pages": [],
                "linkedin_url": None
            }
    
    async def _scrape_with_httpx(self, base_url: str) -> dict:
        """
        Fallback scraper using httpx for simple websites.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=15.0),
                headers=headers,
                follow_redirects=True
            ) as client:
                homepage_html = await self._fetch_page(client, base_url)
                if not homepage_html:
                    return {
                        "success": False,
                        "error": "Failed to fetch homepage",
                        "content": "",
                        "pages": [],
                        "linkedin_url": None
                    }
                
                linkedin_url = self._find_linkedin_url(homepage_html, base_url)
                discovered_pages = self._discover_pages(base_url, homepage_html)
                
                all_content = []
                scraped_pages = []
                
                homepage_content = self._extract_text_content(homepage_html)
                all_content.append(f"[HOMEPAGE]\n{homepage_content}\n")
                scraped_pages.append(base_url)
                
                for page_url, page_type in discovered_pages[:8]:
                    if page_url == base_url:
                        continue
                    
                    await asyncio.sleep(0.5)
                    
                    page_html = await self._fetch_page(client, page_url)
                    if page_html:
                        page_content = self._extract_text_content(page_html)
                        all_content.append(f"[{page_type.upper()}]\nURL: {page_url}\n{page_content}\n")
                        scraped_pages.append(page_url)
                        
                        if not linkedin_url:
                            linkedin_url = self._find_linkedin_url(page_html, base_url)
                
                combined_content = "\n---\n".join(all_content)
                
                if len(combined_content) > 50000:
                    combined_content = combined_content[:50000] + "\n[CONTENT TRUNCATED]"
                
                return {
                    "success": True,
                    "content": combined_content,
                    "pages": scraped_pages,
                    "linkedin_url": linkedin_url,
                    "pages_discovered": len(discovered_pages),
                    "pages_scraped": len(scraped_pages),
                    "source": "httpx"
                }
                
        except Exception as e:
            logger.error(f"Error in httpx scrape: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": "",
                "pages": [],
                "linkedin_url": None
            }
    
    async def _fetch_page(self, client: httpx.AsyncClient, url: str, retries: int = 2) -> str | None:
        """Fetch a single page and return its HTML content."""
        for attempt in range(retries + 1):
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
            except httpx.TimeoutException:
                logger.warning(f"Timeout fetching {url} (attempt {attempt + 1}/{retries + 1})")
                if attempt < retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None
            except httpx.HTTPStatusError as e:
                logger.warning(f"HTTP error fetching {url}: {e.response.status_code}")
                return None
            except Exception as e:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.warning(f"Failed to fetch {url}: {type(e).__name__}: {e}")
                if attempt < retries:
                    await asyncio.sleep(1)
                    continue
                return None
        return None
    
    def _discover_pages(self, base_url: str, homepage_html: str) -> list[tuple[str, str]]:
        """Discover culture-related pages from the homepage."""
        discovered = []
        soup = BeautifulSoup(homepage_html, 'lxml')
        parsed_base = urlparse(base_url)
        
        for link in soup.find_all('a', href=True):
            href_attr = link.get('href', '')
            href = str(href_attr) if href_attr else ''
            
            if href.startswith('javascript:') or href.startswith('#') or href.startswith('mailto:'):
                continue
            
            full_url = urljoin(base_url, href)
            parsed_link = urlparse(full_url)
            
            if parsed_base.netloc != parsed_link.netloc:
                continue
            
            for pattern in CULTURE_PAGE_PATTERNS:
                if re.search(pattern, full_url.lower()):
                    page_type = self._categorize_page(full_url)
                    if (full_url, page_type) not in discovered:
                        discovered.append((full_url, page_type))
                    break
            
            link_text = link.get_text(strip=True).lower()
            if any(kw in link_text for kw in CULTURE_KEYWORDS):
                page_type = self._categorize_page(full_url, link_text)
                if (full_url, page_type) not in discovered:
                    discovered.append((full_url, page_type))
        
        return discovered
    
    def _categorize_page(self, url: str, link_text: str = "") -> str:
        """Categorize a page based on its URL or link text."""
        url_lower = url.lower()
        text_lower = link_text.lower()
        
        if any(kw in url_lower or kw in text_lower for kw in ['career', 'carreira', 'job', 'vaga', 'trabalhe']):
            return "careers"
        elif any(kw in url_lower or kw in text_lower for kw in ['culture', 'cultura']):
            return "culture"
        elif any(kw in url_lower or kw in text_lower for kw in ['value', 'valor']):
            return "values"
        elif any(kw in url_lower or kw in text_lower for kw in ['about', 'sobre', 'quem-somos', 'who-we-are', 'company', 'empresa']):
            return "about"
        elif any(kw in url_lower or kw in text_lower for kw in ['team', 'time', 'equipe']):
            return "team"
        elif any(kw in url_lower or kw in text_lower for kw in ['mission', 'missao']):
            return "mission"
        else:
            return "general"
    
    def _extract_text_content(self, html: str) -> str:
        """Extract clean text content from HTML."""
        soup = BeautifulSoup(html, 'lxml')
        
        for element in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript']):
            element.decompose()
        
        for element in soup.find_all(class_=re.compile(r'(cookie|popup|modal|banner|ad-|advertisement)', re.I)):
            element.decompose()
        
        main_content = soup.find('main') or soup.find('article') or soup.find(id=re.compile(r'content|main', re.I))
        
        if main_content:
            text = main_content.get_text(separator='\n', strip=True)
        else:
            text = soup.get_text(separator='\n', strip=True)
        
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = '\n'.join(lines)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text
    
    def _find_linkedin_url(self, html: str, base_url: str) -> str | None:
        """Find LinkedIn company page URL from HTML content."""
        soup = BeautifulSoup(html, 'lxml')
        
        for link in soup.find_all('a', href=True):
            href_attr = link.get('href', '')
            href = str(href_attr) if href_attr else ''
            if 'linkedin.com/company/' in href:
                return href
        
        og_url = soup.find('meta', property='og:see_also')
        if og_url:
            content = og_url.get('content', '')
            content_str = str(content) if content else ''
            if 'linkedin.com' in content_str:
                return content_str
        
        for link in soup.find_all('a', href=True):
            href_attr = link.get('href', '')
            href = str(href_attr) if href_attr else ''
            if 'linkedin.com' in href and '/company' in href:
                return href
        
        return None
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL to ensure it has a scheme."""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        parsed = urlparse(url)
        if not parsed.path or parsed.path == '/':
            url = url.rstrip('/') + '/'
        
        return url


company_scraper_service = CompanyScraperService()
