"""
Apify MCP Client - Model Context Protocol client for Apify.
Connects to mcp.apify.com using Streamable HTTP transport.
Replaces direct HTTP API calls with MCP protocol.

Improvements:
- Session persistence across requests
- Enhanced SSE parsing with multi-event support
- Better error handling and retry logic
"""
import asyncio
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import httpx
from lia_config.config import settings

logger = logging.getLogger(__name__)

APIFY_MCP_URL = "https://mcp.apify.com"
APIFY_API_KEY = os.environ.get("APIFY_API_KEY", "")


@dataclass
class MCPSession:
    """Tracks MCP session state."""
    session_id: str
    created_at: datetime
    initialized: bool = False
    protocol_version: str = "2024-11-05"
    server_capabilities: dict = field(default_factory=dict)
    
    def is_valid(self, max_age_minutes: int = 30) -> bool:
        """Check if session is still valid based on age."""
        return (
            self.initialized and 
            (datetime.utcnow() - self.created_at) < timedelta(minutes=max_age_minutes)
        )


class ApifyMCPClient:
    """
    MCP Client for Apify platform.
    Uses Streamable HTTP transport to communicate with mcp.apify.com.
    
    Features:
    - Session persistence with automatic refresh
    - Enhanced SSE parsing for streamed responses
    - Retry logic for transient failures
    """
    
    _shared_session: MCPSession | None = None
    _session_lock: asyncio.Lock | None = None
    
    def __init__(self, api_key: str | None = None, session_max_age_minutes: int = 30):
        self.api_key = api_key or APIFY_API_KEY
        self.mcp_url = APIFY_MCP_URL
        self.timeout = httpx.Timeout(settings.HTTP_TIMEOUT_APIFY_SECONDS, connect=settings.HTTP_TIMEOUT_APIFY_CONNECT_SECONDS)  # UC-P2-12
        self.session_max_age = session_max_age_minutes
        self._http_client: httpx.AsyncClient | None = None
        self._max_retries = 3
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create persistent HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=self.timeout)
        return self._http_client
    
    async def close(self):
        """Close the HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None
    
    def _get_headers(self, session_id: str | None = None) -> dict[str, str]:
        """Get headers for MCP requests."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if session_id:
            headers["Mcp-Session-Id"] = session_id
        return headers
    
    async def _ensure_session(self) -> MCPSession:
        """Ensure a valid MCP session exists, creating one if needed."""
        if ApifyMCPClient._session_lock is None:
            ApifyMCPClient._session_lock = asyncio.Lock()
            
        async with ApifyMCPClient._session_lock:
            if ApifyMCPClient._shared_session and ApifyMCPClient._shared_session.is_valid(self.session_max_age):
                return ApifyMCPClient._shared_session
            
            session = MCPSession(
                session_id=f"system:{uuid.uuid4()}",
                created_at=datetime.utcnow()
            )
            
            response = await self._send_raw_request("initialize", {
                "protocolVersion": session.protocol_version,
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "lia-agent-system",
                    "version": "1.0.0"
                }
            }, session_id=session.session_id)
            
            if "error" not in response:
                session.initialized = True
                if "result" in response:
                    session.server_capabilities = response["result"].get("capabilities", {})
                ApifyMCPClient._shared_session = session
                logger.info(f"MCP session initialized: {session.session_id[:8]}...")
            else:
                logger.error(f"MCP session initialization failed: {response}")
            
            return session
    
    async def _send_raw_request(
        self, 
        method: str, 
        params: dict[str, Any] | None = None,
        session_id: str | None = None
    ) -> dict[str, Any]:
        """Send a raw JSON-RPC request without session management."""
        request_id = str(uuid.uuid4())
        
        payload: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params:
            payload["params"] = params
        
        try:
            client = await self._get_http_client()
            response = await client.post(
                self.mcp_url,
                json=payload,
                headers=self._get_headers(session_id)
            )
            
            if response.status_code == 401:
                logger.error("MCP authentication failed - check APIFY_API_KEY")
                return {"error": "Authentication failed"}
            
            if response.status_code == 403:
                logger.error("MCP forbidden - session may have expired")
                ApifyMCPClient._shared_session = None
                return {"error": "Session expired or forbidden"}
            
            response.raise_for_status()
            
            content_type = response.headers.get("content-type", "")
            if "text/event-stream" in content_type:
                return self._parse_sse_response(response.text, request_id)
            else:
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"MCP HTTP error: {e.response.status_code} - {e.response.text}")
            return {"error": f"HTTP {e.response.status_code}"}
        except Exception as e:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.error(f"MCP request error: {type(e).__name__}: {e}")
            return {"error": str(e)}
    
    async def _send_mcp_request(
        self, 
        method: str, 
        params: dict[str, Any] | None = None,
        retry_count: int = 0
    ) -> dict[str, Any]:
        """
        Send a JSON-RPC request to the MCP server with session management and retry.
        
        Args:
            method: MCP method name (e.g., "tools/call", "tools/list")
            params: Parameters for the method
            retry_count: Current retry attempt
            
        Returns:
            Response from MCP server
        """
        session = await self._ensure_session()
        
        if not session.initialized:
            return {"error": "Failed to initialize MCP session"}
        
        response = await self._send_raw_request(method, params, session.session_id)
        
        if response.get("error") == "Session expired or forbidden" and retry_count < self._max_retries:
            logger.info(f"Session expired, reinitializing (attempt {retry_count + 1})")
            ApifyMCPClient._shared_session = None
            return await self._send_mcp_request(method, params, retry_count + 1)
        
        return response
    
    def _parse_sse_response(self, sse_text: str, request_id: str | None = None) -> dict:
        """
        Parse Server-Sent Events response with multi-event support.
        
        SSE Format:
        event: message
        data: {"jsonrpc": "2.0", "id": "...", "result": {...}}
        
        :done
        """
        events = []
        current_event = {"event": None, "data": ""}
        final_result = {}
        
        for line in sse_text.split("\n"):
            line = line.strip()
            
            if line.startswith("event:"):
                if current_event["data"]:
                    events.append(current_event.copy())
                current_event = {"event": line[6:].strip(), "data": ""}
            elif line.startswith("data:"):
                data_content = line[5:].strip()
                if current_event["data"]:
                    current_event["data"] += "\n" + data_content
                else:
                    current_event["data"] = data_content
            elif line == "" and current_event["data"]:
                events.append(current_event.copy())
                current_event = {"event": None, "data": ""}
            elif line == ":done":
                if current_event["data"]:
                    events.append(current_event.copy())
                break
        
        if current_event["data"]:
            events.append(current_event)
        
        for event in reversed(events):
            data_str = event["data"]
            if not data_str:
                continue
            
            try:
                parsed = json.loads(data_str)
                
                if isinstance(parsed, dict):
                    if "error" in parsed:
                        return parsed
                    
                    if request_id and parsed.get("id") == request_id:
                        return parsed
                    
                    if "result" in parsed:
                        final_result = parsed
                    elif not final_result:
                        final_result = parsed
                        
            except json.JSONDecodeError as e:
                logger.debug(f"SSE data parse error: {e}, data: {data_str[:100]}...")
                continue
        
        return final_result if final_result else {"error": "No valid JSON in SSE response"}
    
    async def initialize(self) -> bool:
        """Initialize MCP session (uses shared session internally)."""
        session = await self._ensure_session()
        return session.initialized
    
    async def list_tools(self) -> list[dict]:
        """List available MCP tools."""
        response = await self._send_mcp_request("tools/list")
        
        if "result" in response:
            return response["result"].get("tools", [])
        return []
    
    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """
        Call an MCP tool.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        response = await self._send_mcp_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
        
        if "result" in response:
            return response["result"]
        return response
    
    async def search_actors(self, query: str, limit: int = 10) -> list[dict]:
        """
        Search for Apify actors.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching actors
        """
        result = await self.call_tool("search-actors", {
            "query": query,
            "limit": limit
        })
        
        if "content" in result:
            for item in result["content"]:
                if item.get("type") == "text":
                    try:
                        return json.loads(item["text"])
                    except (json.JSONDecodeError, KeyError):
                        pass
        return []
    
    async def call_actor(
        self,
        actor_id: str,
        input_data: dict,
        wait_for_finish: bool = True,
        timeout_secs: int = 300
    ) -> dict:
        """
        Run an Apify actor via MCP.
        
        Args:
            actor_id: Actor ID (e.g., "apify/website-content-crawler")
            input_data: Actor input parameters
            wait_for_finish: Wait for actor to complete
            timeout_secs: Timeout in seconds
            
        Returns:
            Actor run results
        """
        result = await self.call_tool("call-actor", {
            "actorId": actor_id,
            "input": input_data,
            "waitForFinish": wait_for_finish,
            "timeout": timeout_secs
        })
        
        return self._extract_tool_result(result)
    
    async def get_dataset_items(
        self,
        dataset_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> list[dict]:
        """
        Get items from an Apify dataset.
        
        Args:
            dataset_id: Dataset ID
            limit: Maximum items to retrieve
            offset: Starting offset
            
        Returns:
            List of dataset items
        """
        result = await self.call_tool("get-dataset-items", {
            "datasetId": dataset_id,
            "limit": limit,
            "offset": offset
        })
        
        return self._extract_tool_result(result)
    
    def _extract_tool_result(self, result: dict) -> Any:
        """Extract actual data from MCP tool result."""
        if "content" in result:
            for item in result["content"]:
                if item.get("type") == "text":
                    try:
                        return json.loads(item["text"])
                    except json.JSONDecodeError:
                        return item["text"]
        return result
    
    async def scrape_website(self, url: str, max_pages: int = 15) -> dict:
        """
        Scrape a website using apify/website-content-crawler.
        
        Args:
            url: Website URL to scrape
            max_pages: Maximum pages to crawl
            
        Returns:
            Scraped content
        """
        return await self.call_actor(
            "apify/website-content-crawler",
            {
                "startUrls": [{"url": url}],
                "maxCrawlPages": max_pages,
                "maxCrawlDepth": 2,
                "crawlerType": "playwright:adaptive",
            }
        )
    
    async def scrape_linkedin_company(self, linkedin_url: str) -> dict:
        """
        Scrape LinkedIn company profile.
        
        Args:
            linkedin_url: LinkedIn company page URL
            
        Returns:
            Company profile data
        """
        return await self.call_actor(
            "curious_coder/linkedin-company-scraper",
            {
                "urls": [linkedin_url],
                "minDelay": 2,
                "maxDelay": 5
            }
        )
    
    async def scrape_glassdoor(self, company_name: str) -> dict:
        """
        Scrape Glassdoor company data.
        
        Args:
            company_name: Company name to search
            
        Returns:
            Glassdoor company data
        """
        return await self.call_actor(
            "bebity/glassdoor-scraper",
            {
                "searchQueries": [company_name],
                "maxResults": 1,
                "includeReviews": True,
                "maxReviews": 10
            }
        )
    
    async def browse_web(self, query: str, max_results: int = 5) -> dict:
        """
        Browse the web using RAG Web Browser actor.
        
        Args:
            query: Search query
            max_results: Maximum results
            
        Returns:
            Web browsing results
        """
        return await self.call_actor(
            "apify/rag-web-browser",
            {
                "query": query,
                "maxResults": max_results
            }
        )


apify_mcp_client = ApifyMCPClient()
