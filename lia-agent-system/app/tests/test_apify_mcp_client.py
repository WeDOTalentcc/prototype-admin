"""
Tests for ApifyMCPClient - MCP protocol client for Apify.

Tests cover:
- MCPSession validation and lifecycle
- SSE response parsing
- HTTP error handling
- Session management with retry logic
- Tool calls (mocked)
"""
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.domains.sourcing.services.apify_mcp_client import ApifyMCPClient, MCPSession


class TestMCPSession:
    """Tests for MCPSession dataclass."""
    
    def test_session_creation(self):
        """Test MCPSession can be created with required fields."""
        session = MCPSession(
            session_id="test-123",
            created_at=datetime.utcnow()
        )
        
        assert session.session_id == "test-123"
        assert session.initialized is False
        assert session.protocol_version == "2024-11-05"
        assert session.server_capabilities == {}
    
    def test_session_is_valid_when_initialized_and_fresh(self):
        """Test session is valid when initialized and within age limit."""
        session = MCPSession(
            session_id="test-123",
            created_at=datetime.utcnow(),
            initialized=True
        )
        
        assert session.is_valid(max_age_minutes=30) is True
    
    def test_session_is_invalid_when_not_initialized(self):
        """Test session is invalid when not initialized."""
        session = MCPSession(
            session_id="test-123",
            created_at=datetime.utcnow(),
            initialized=False
        )
        
        assert session.is_valid(max_age_minutes=30) is False
    
    def test_session_is_invalid_when_expired(self):
        """Test session is invalid when older than max age."""
        old_time = datetime.utcnow() - timedelta(minutes=45)
        session = MCPSession(
            session_id="test-123",
            created_at=old_time,
            initialized=True
        )
        
        assert session.is_valid(max_age_minutes=30) is False
    
    def test_session_edge_case_just_expired(self):
        """Test session that just expired."""
        old_time = datetime.utcnow() - timedelta(minutes=31)
        session = MCPSession(
            session_id="test-123",
            created_at=old_time,
            initialized=True
        )
        
        assert session.is_valid(max_age_minutes=30) is False


class TestSSEParsing:
    """Tests for SSE response parsing."""
    
    def test_parse_simple_sse_response(self):
        """Test parsing a simple SSE response."""
        client = ApifyMCPClient(api_key="test-key")
        
        sse_text = """event: message
data: {"jsonrpc": "2.0", "id": "req-123", "result": {"status": "ok"}}

:done"""
        
        result = client._parse_sse_response(sse_text, request_id="req-123")
        
        assert result.get("jsonrpc") == "2.0"
        assert result.get("id") == "req-123"
        assert result.get("result") == {"status": "ok"}
    
    def test_parse_multi_event_sse(self):
        """Test parsing SSE with multiple events."""
        client = ApifyMCPClient(api_key="test-key")
        
        sse_text = """event: message
data: {"jsonrpc": "2.0", "id": "req-1", "result": {"step": 1}}

event: message
data: {"jsonrpc": "2.0", "id": "req-2", "result": {"step": 2}}

event: message
data: {"jsonrpc": "2.0", "id": "req-123", "result": {"final": true}}

:done"""
        
        result = client._parse_sse_response(sse_text, request_id="req-123")
        
        assert result.get("id") == "req-123"
        assert result.get("result") == {"final": True}
    
    def test_parse_sse_with_error(self):
        """Test parsing SSE response with error."""
        client = ApifyMCPClient(api_key="test-key")
        
        sse_text = """event: message
data: {"jsonrpc": "2.0", "id": "req-123", "error": {"code": -32600, "message": "Invalid Request"}}

:done"""
        
        result = client._parse_sse_response(sse_text, request_id="req-123")
        
        assert "error" in result
        assert result["error"]["code"] == -32600
    
    def test_parse_sse_multiline_data(self):
        """Test parsing SSE with data split across lines."""
        client = ApifyMCPClient(api_key="test-key")
        
        sse_text = """event: message
data: {"jsonrpc": "2.0", "id": "req-123",
data:  "result": {"content": "test"}}

:done"""
        
        result = client._parse_sse_response(sse_text, request_id="req-123")
        
        assert result.get("id") == "req-123"
    
    def test_parse_sse_no_matching_request_id(self):
        """Test parsing SSE when request_id doesn't match returns last result."""
        client = ApifyMCPClient(api_key="test-key")
        
        sse_text = """event: message
data: {"jsonrpc": "2.0", "id": "other-id", "result": {"data": "found"}}

:done"""
        
        result = client._parse_sse_response(sse_text, request_id="req-123")
        
        assert result.get("result") == {"data": "found"}
    
    def test_parse_empty_sse(self):
        """Test parsing empty SSE response."""
        client = ApifyMCPClient(api_key="test-key")
        
        sse_text = """:done"""
        
        result = client._parse_sse_response(sse_text)
        
        assert "error" in result
    
    def test_parse_sse_invalid_json(self):
        """Test parsing SSE with invalid JSON."""
        client = ApifyMCPClient(api_key="test-key")
        
        sse_text = """event: message
data: not valid json

event: message
data: {"jsonrpc": "2.0", "result": {"valid": true}}

:done"""
        
        result = client._parse_sse_response(sse_text)
        
        assert result.get("result") == {"valid": True}


class TestApifyMCPClientHeaders:
    """Tests for header generation."""
    
    def test_headers_without_session(self):
        """Test headers are correct without session ID."""
        client = ApifyMCPClient(api_key="test-api-key")
        
        headers = client._get_headers()
        
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json, text/event-stream"
        assert headers["Authorization"] == "Bearer test-api-key"
        assert "Mcp-Session-Id" not in headers
    
    def test_headers_with_session(self):
        """Test headers include session ID when provided."""
        client = ApifyMCPClient(api_key="test-api-key")
        
        headers = client._get_headers(session_id="session-456")
        
        assert headers["Mcp-Session-Id"] == "session-456"
    
    def test_headers_without_api_key(self):
        """Test headers when no API key is set."""
        client = ApifyMCPClient(api_key="")
        client.api_key = ""
        
        headers = client._get_headers()
        
        assert headers.get("Authorization", "") == "" or "Authorization" not in headers


class TestApifyMCPClientToolResultExtraction:
    """Tests for tool result extraction."""
    
    def test_extract_json_from_content(self):
        """Test extracting JSON from content array."""
        client = ApifyMCPClient(api_key="test-key")
        
        result = {
            "content": [
                {"type": "text", "text": '{"name": "John", "age": 30}'}
            ]
        }
        
        extracted = client._extract_tool_result(result)
        
        assert extracted == {"name": "John", "age": 30}
    
    def test_extract_plain_text_from_content(self):
        """Test extracting plain text when JSON parsing fails."""
        client = ApifyMCPClient(api_key="test-key")
        
        result = {
            "content": [
                {"type": "text", "text": "Plain text result"}
            ]
        }
        
        extracted = client._extract_tool_result(result)
        
        assert extracted == "Plain text result"
    
    def test_extract_returns_original_when_no_content(self):
        """Test returns original result when no content field."""
        client = ApifyMCPClient(api_key="test-key")
        
        result = {"data": "direct"}
        
        extracted = client._extract_tool_result(result)
        
        assert extracted == {"data": "direct"}


class TestApifyMCPClientIntegration:
    """Integration tests with mocked HTTP responses."""
    
    @pytest.fixture
    def mock_http_response(self):
        """Create a mock HTTP response factory."""
        def create_response(
            status_code: int = 200,
            json_data: dict | None = None,
            content_type: str = "application/json",
            text: str | None = None
        ):
            response = MagicMock(spec=httpx.Response)
            response.status_code = status_code
            response.headers = {"content-type": content_type}
            
            if json_data:
                response.json.return_value = json_data
            if text:
                response.text = text
            
            response.raise_for_status = MagicMock()
            if status_code >= 400:
                response.raise_for_status.side_effect = httpx.HTTPStatusError(
                    message=f"HTTP {status_code}",
                    request=MagicMock(),
                    response=response
                )
            
            return response
        
        return create_response
    
    @pytest.mark.asyncio
    async def test_initialize_session_success(self, mock_http_response):
        """Test successful session initialization."""
        ApifyMCPClient._shared_session = None
        ApifyMCPClient._session_lock = None
        
        client = ApifyMCPClient(api_key="test-key")
        
        mock_response = mock_http_response(
            json_data={
                "jsonrpc": "2.0",
                "id": "test",
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}}
                }
            }
        )
        
        mock_http_client = AsyncMock()
        mock_http_client.post.return_value = mock_response
        mock_http_client.is_closed = False
        
        client._http_client = mock_http_client
        
        result = await client.initialize()
        
        assert result is True
        assert ApifyMCPClient._shared_session is not None
        assert ApifyMCPClient._shared_session.initialized is True
        
        ApifyMCPClient._shared_session = None
        await client.close()
    
    @pytest.mark.asyncio
    async def test_list_tools(self, mock_http_response):
        """Test listing available tools."""
        ApifyMCPClient._shared_session = MCPSession(
            session_id="test-session",
            created_at=datetime.utcnow(),
            initialized=True
        )
        ApifyMCPClient._session_lock = None
        
        client = ApifyMCPClient(api_key="test-key")
        
        mock_response = mock_http_response(
            json_data={
                "jsonrpc": "2.0",
                "id": "test",
                "result": {
                    "tools": [
                        {"name": "search-actors", "description": "Search for actors"},
                        {"name": "call-actor", "description": "Call an actor"}
                    ]
                }
            }
        )
        
        mock_http_client = AsyncMock()
        mock_http_client.post.return_value = mock_response
        mock_http_client.is_closed = False
        
        client._http_client = mock_http_client
        
        tools = await client.list_tools()
        
        assert len(tools) == 2
        assert tools[0]["name"] == "search-actors"
        
        ApifyMCPClient._shared_session = None
        await client.close()
    
    @pytest.mark.asyncio
    async def test_call_tool_success(self, mock_http_response):
        """Test successful tool call."""
        ApifyMCPClient._shared_session = MCPSession(
            session_id="test-session",
            created_at=datetime.utcnow(),
            initialized=True
        )
        ApifyMCPClient._session_lock = None
        
        client = ApifyMCPClient(api_key="test-key")
        
        mock_response = mock_http_response(
            json_data={
                "jsonrpc": "2.0",
                "id": "test",
                "result": {
                    "content": [
                        {"type": "text", "text": '{"actors": [{"name": "test-actor"}]}'}
                    ]
                }
            }
        )
        
        mock_http_client = AsyncMock()
        mock_http_client.post.return_value = mock_response
        mock_http_client.is_closed = False
        
        client._http_client = mock_http_client
        
        result = await client.call_tool("search-actors", {"query": "linkedin"})
        
        assert "content" in result
        
        ApifyMCPClient._shared_session = None
        await client.close()
    
    @pytest.mark.asyncio
    async def test_authentication_failure(self, mock_http_response):
        """Test handling of 401 authentication error."""
        ApifyMCPClient._shared_session = None
        ApifyMCPClient._session_lock = None
        
        client = ApifyMCPClient(api_key="invalid-key")
        
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 401
        mock_response.headers = {"content-type": "application/json"}
        
        mock_http_client = AsyncMock()
        mock_http_client.post.return_value = mock_response
        mock_http_client.is_closed = False
        
        client._http_client = mock_http_client
        
        result = await client.initialize()
        
        assert result is False
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_session_refresh_on_403(self, mock_http_response):
        """Test session refresh when receiving 403 forbidden."""
        old_session = MCPSession(
            session_id="old-session",
            created_at=datetime.utcnow() - timedelta(minutes=40),
            initialized=True
        )
        ApifyMCPClient._shared_session = old_session
        ApifyMCPClient._session_lock = None
        
        client = ApifyMCPClient(api_key="test-key")
        
        mock_403_response = MagicMock(spec=httpx.Response)
        mock_403_response.status_code = 403
        mock_403_response.headers = {"content-type": "application/json"}
        
        mock_success_response = mock_http_response(
            json_data={
                "jsonrpc": "2.0",
                "id": "test",
                "result": {"data": "success"}
            }
        )
        
        mock_init_response = mock_http_response(
            json_data={
                "jsonrpc": "2.0",
                "id": "test",
                "result": {"protocolVersion": "2024-11-05", "capabilities": {}}
            }
        )
        
        mock_http_client = AsyncMock()
        mock_http_client.post.side_effect = [
            mock_403_response,
            mock_init_response,
            mock_success_response
        ]
        mock_http_client.is_closed = False
        
        client._http_client = mock_http_client
        
        await client._send_mcp_request("tools/list")
        
        assert ApifyMCPClient._shared_session is not old_session
        
        ApifyMCPClient._shared_session = None
        await client.close()
    
    @pytest.mark.asyncio
    async def test_sse_response_handling(self, mock_http_response):
        """Test handling of SSE response format."""
        ApifyMCPClient._shared_session = MCPSession(
            session_id="test-session",
            created_at=datetime.utcnow(),
            initialized=True
        )
        ApifyMCPClient._session_lock = None
        
        client = ApifyMCPClient(api_key="test-key")
        
        sse_text = """event: message
data: {"jsonrpc": "2.0", "id": "test-id", "result": {"actors": []}}

:done"""
        
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/event-stream"}
        mock_response.text = sse_text
        mock_response.raise_for_status = MagicMock()
        
        mock_http_client = AsyncMock()
        mock_http_client.post.return_value = mock_response
        mock_http_client.is_closed = False
        
        client._http_client = mock_http_client
        
        result = await client._send_mcp_request("search-actors")
        
        assert "result" in result or "actors" in result.get("result", {})
        
        ApifyMCPClient._shared_session = None
        await client.close()
    
    @pytest.mark.asyncio
    async def test_search_actors(self, mock_http_response):
        """Test search_actors method."""
        ApifyMCPClient._shared_session = MCPSession(
            session_id="test-session",
            created_at=datetime.utcnow(),
            initialized=True
        )
        ApifyMCPClient._session_lock = None
        
        client = ApifyMCPClient(api_key="test-key")
        
        actors_list = [
            {"id": "actor1", "name": "LinkedIn Scraper"},
            {"id": "actor2", "name": "Profile Extractor"}
        ]
        
        mock_response = mock_http_response(
            json_data={
                "jsonrpc": "2.0",
                "id": "test",
                "result": {
                    "content": [
                        {"type": "text", "text": json.dumps(actors_list)}
                    ]
                }
            }
        )
        
        mock_http_client = AsyncMock()
        mock_http_client.post.return_value = mock_response
        mock_http_client.is_closed = False
        
        client._http_client = mock_http_client
        
        result = await client.search_actors("linkedin", limit=5)
        
        assert len(result) == 2
        assert result[0]["name"] == "LinkedIn Scraper"
        
        ApifyMCPClient._shared_session = None
        await client.close()
    
    @pytest.mark.asyncio
    async def test_call_actor(self, mock_http_response):
        """Test call_actor method."""
        ApifyMCPClient._shared_session = MCPSession(
            session_id="test-session",
            created_at=datetime.utcnow(),
            initialized=True
        )
        ApifyMCPClient._session_lock = None
        
        client = ApifyMCPClient(api_key="test-key")
        
        actor_result = [
            {"firstName": "John", "lastName": "Doe", "headline": "Developer"}
        ]
        
        mock_response = mock_http_response(
            json_data={
                "jsonrpc": "2.0",
                "id": "test",
                "result": {
                    "content": [
                        {"type": "text", "text": json.dumps(actor_result)}
                    ]
                }
            }
        )
        
        mock_http_client = AsyncMock()
        mock_http_client.post.return_value = mock_response
        mock_http_client.is_closed = False
        
        client._http_client = mock_http_client
        
        result = await client.call_actor(
            "dev_fusion/Linkedin-Profile-Scraper",
            {"urls": ["https://linkedin.com/in/johndoe"]},
            wait_for_finish=True,
            timeout_secs=180
        )
        
        assert isinstance(result, list)
        assert result[0]["firstName"] == "John"
        
        ApifyMCPClient._shared_session = None
        await client.close()


class TestApifyMCPClientHTTPClient:
    """Tests for HTTP client management."""
    
    @pytest.mark.asyncio
    async def test_http_client_creation(self):
        """Test HTTP client is created on demand."""
        client = ApifyMCPClient(api_key="test-key")
        
        assert client._http_client is None
        
        http_client = await client._get_http_client()
        
        assert http_client is not None
        assert client._http_client is http_client
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_http_client_reuse(self):
        """Test HTTP client is reused across calls."""
        client = ApifyMCPClient(api_key="test-key")
        
        http_client_1 = await client._get_http_client()
        http_client_2 = await client._get_http_client()
        
        assert http_client_1 is http_client_2
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_close_client(self):
        """Test closing HTTP client."""
        client = ApifyMCPClient(api_key="test-key")
        
        await client._get_http_client()
        assert client._http_client is not None
        
        await client.close()
        assert client._http_client is None
