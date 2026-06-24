import pytest
from unittest.mock import AsyncMock, MagicMock

# Re-export mock HTTP fixtures so they are available globally (GAP-08-006)
from tests.fixtures.mock_http import MockResponse, mock_http_client  # noqa: F401

try:
    from lia_agents_core.react_loop import ReActConfig, ReActLoop, ToolDefinition
    from lia_agents_core.observability import ReActObserver
    _LIA_CORE_AVAILABLE = True
except ImportError:
    _LIA_CORE_AVAILABLE = False
    ReActConfig = None
    ReActLoop = None
    ToolDefinition = None
    ReActObserver = None


@pytest.fixture
def mock_tool():
    if not _LIA_CORE_AVAILABLE:
        pytest.skip("lia_agents_core not installed — skipping ToolDefinition fixture")
    fn = AsyncMock(return_value={"result": "ok", "success": True})
    return ToolDefinition(
        name="mock_tool",
        description="A mock tool for testing",
        parameters={"input": {"type": "string"}},
        function=fn,
    )


@pytest.fixture
def mock_memory_service():
    svc = MagicMock()
    svc.increment_iteration = AsyncMock()
    svc.get_or_create = AsyncMock()
    svc.update_memory = AsyncMock()
    svc.get_context_summary = AsyncMock(return_value="Test memory summary")
    return svc


@pytest.fixture
def base_react_config(mock_tool):
    if not _LIA_CORE_AVAILABLE:
        pytest.skip("lia_agents_core not installed — skipping ReActConfig fixture")
    return ReActConfig(
        system_prompt="You are a test agent.",
        available_tools=[mock_tool],
        max_iterations=3,
        domain="test",
        model_provider="claude",
    )


@pytest.fixture
def observer():
    if not _LIA_CORE_AVAILABLE:
        pytest.skip("lia_agents_core not installed — skipping ReActObserver fixture")
    return ReActObserver(
        session_id="test-session",
        domain="test",
        agent_class="TestAgent",
    )


# ─── LLM Bootstrap test fixtures (R-009) ────────────────────────────────────

@pytest.fixture()
def reset_company_contextvar():
    """Reset _current_company_id ContextVar before and after each test."""
    try:
        from app.middleware.auth_enforcement import _current_company_id
        token = _current_company_id.set("")
        yield _current_company_id
        _current_company_id.reset(token)
    except ImportError:
        # Graceful skip if middleware not importable in test context
        from contextvars import ContextVar
        yield ContextVar("_current_company_id", default="")


@pytest.fixture()
def mock_anthropic_client():
    """Return a MagicMock mimicking anthropic.Anthropic client."""
    client = MagicMock()
    client.messages = MagicMock()
    client.messages.create = MagicMock()
    client.messages.stream = MagicMock()
    return client


@pytest.fixture()
def mock_openai_client():
    """Return a MagicMock mimicking openai.OpenAI client."""
    client = MagicMock()
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    client.chat.completions.create = MagicMock()
    return client


@pytest.fixture()
def mock_genai_client():
    """Return a MagicMock mimicking google.genai.Client."""
    client = MagicMock()
    client.models = MagicMock()
    client.models.generate_content = MagicMock()
    return client


@pytest.fixture()
def patched_llm_audit_log():
    """Patch _audit_log in llm_bootstrap and return the MagicMock for assertions."""
    from unittest.mock import patch as _patch
    with _patch("app.shared.llm_bootstrap._audit_log") as mock_audit:
        yield mock_audit


@pytest.fixture(autouse=True)
def _f15_force_voice_session_repo_inmemory(request):
    """
    F-15 P0 (audit 2026-05-22): force VoiceSessionRedisRepository to use the
    in-memory fallback in tests. Prevents pollution from the canonical Redis
    singleton (shared client → "Event loop is closed" + cross-test state leak).

    Per-test isolation: clears the in-memory dict before each test starts. New
    orchestrator instances created inside the test still use the patched
    `_get_redis` (the patch hooks at the class method level).

    Opt-out: tests that need real Redis can mark with
    `@pytest.mark.no_voice_redis_isolation`.
    """
    # Honor opt-out marker.
    if request.node.get_closest_marker("no_voice_redis_isolation"):
        yield
        return

    try:
        from app.domains.voice.repositories import voice_session_redis_repository as vsrr
    except ImportError:
        yield
        return

    # Async stub: always returns None → repo uses in-memory fallback paths.
    async def _no_redis(_self):
        return None

    original_get_redis = vsrr.VoiceSessionRedisRepository._get_redis
    vsrr.VoiceSessionRedisRepository._get_redis = _no_redis  # type: ignore[method-assign]

    # Also reset the canonical singleton's in-memory state if it exists,
    # so cross-test isolation holds for shared instances.
    if vsrr._voice_session_repository is not None:
        vsrr._voice_session_repository._memory_fallback.clear()
        vsrr._voice_session_repository._memory_active_index.clear()
        vsrr._voice_session_repository._memory_reverse_index.clear()
        vsrr._voice_session_repository._redis = None
        vsrr._voice_session_repository._redis_available = False

    yield

    # Restore on test teardown.
    vsrr.VoiceSessionRedisRepository._get_redis = original_get_redis  # type: ignore[method-assign]
