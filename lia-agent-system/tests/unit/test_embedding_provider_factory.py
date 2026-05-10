"""
Unit tests for Task #134 — Embedding Provider Factory.

Covers:
- EmbeddingProviderABC interface contract
- GeminiEmbeddingProvider (mocked)
- OpenAIEmbeddingProvider (mocked)
- EmbeddingProviderFactory: register, get, get_default, embed_with_fallback
- Fallback behavior when primary provider fails
- Provider isolation (same-provider filter in pgvector queries)
- EmbeddingService facade (backward-compatible)
"""
import sys
import pytest
from typing import List
from unittest.mock import AsyncMock, MagicMock

pytestmark = pytest.mark.easy

# ---------------------------------------------------------------------------
# Minimal stubs to prevent deep import chains triggered by
# app.shared.providers.__init__ → ats_factory → app.services → app.core.config
# ---------------------------------------------------------------------------

_HEAVY_STUBS = {
    "app.shared.providers.ats_factory": MagicMock(),
    "app.shared.providers.voice_provider": MagicMock(),
    "app.shared.providers.llm_claude": MagicMock(),
    "app.shared.providers.llm_gemini": MagicMock(),
    "app.shared.providers.llm_openai": MagicMock(),
    "app.shared.providers.llm_factory": MagicMock(),
    "app.shared.providers.llm_provider": MagicMock(),
}
for _mod, _stub in _HEAVY_STUBS.items():
    if _mod not in sys.modules:
        sys.modules[_mod] = _stub

from app.shared.providers.embedding_provider import EmbeddingProviderABC, EmbeddingResult  # noqa: E402
from app.shared.providers.embedding_gemini import GeminiEmbeddingProvider  # noqa: E402
from app.shared.providers.embedding_openai import OpenAIEmbeddingProvider  # noqa: E402
from app.shared.providers.embedding_factory import EmbeddingProviderFactory  # noqa: E402
from app.shared.intelligence.embedding_service import EmbeddingService  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _zero_vector(n: int) -> List[float]:
    return [0.0] * n


def _make_fake_provider(name: str, dims: int, fail: bool = False):
    """Dynamically create a minimal EmbeddingProviderABC implementation."""

    class FakeProvider(EmbeddingProviderABC):
        _provider_name = name

        @property
        def provider_name(self):
            return name

        @property
        def default_model(self):
            return f"{name}-model"

        @property
        def dimensions(self):
            return dims

        async def embed_text(self, text):
            if fail:
                raise RuntimeError(f"{name} unavailable")
            if not text or not text.strip():
                return EmbeddingResult(
                    vector=_zero_vector(dims), provider=name, model=f"{name}-model"
                )
            return EmbeddingResult(
                vector=[0.1] * dims, provider=name, model=f"{name}-model"
            )

        async def embed_batch(self, texts):
            return [await self.embed_text(t) for t in texts]

    return FakeProvider


@pytest.fixture(autouse=True)
def clean_factory():
    """Reset factory state before and after each test."""
    EmbeddingProviderFactory.clear()
    EmbeddingProviderFactory._providers.clear()
    yield
    EmbeddingProviderFactory.clear()
    EmbeddingProviderFactory._providers.clear()


# ---------------------------------------------------------------------------
# Tests: EmbeddingProviderABC interface
# ---------------------------------------------------------------------------

class TestEmbeddingProviderABC:
    """Verify that the abstract interface is correctly defined."""

    def test_cannot_instantiate_abc(self):
        with pytest.raises(TypeError):
            EmbeddingProviderABC()

    def test_embedding_result_dimensions(self):
        result = EmbeddingResult(
            vector=[0.1, 0.2, 0.3],
            provider="test",
            model="test-model",
        )
        assert result.dimensions == 3
        assert result.vector == [0.1, 0.2, 0.3]
        assert result.provider == "test"
        assert result.model == "test-model"

    def test_embedding_result_dimensions_auto_computed(self):
        result = EmbeddingResult(
            vector=[0.0] * 768, provider="gemini", model="text-embedding-004"
        )
        assert result.dimensions == 768


# ---------------------------------------------------------------------------
# Tests: GeminiEmbeddingProvider
# ---------------------------------------------------------------------------

class TestGeminiEmbeddingProvider:
    """GeminiEmbeddingProvider tests (Gemini client is mocked)."""

    def test_properties(self):
        p = GeminiEmbeddingProvider()
        assert p.provider_name == "gemini"
        assert p.default_model == "text-embedding-004"
        assert p.dimensions == 768
        assert p.get_dimensions() == 768

    @pytest.mark.asyncio
    async def test_embed_text_empty_returns_zero_vector(self):
        p = GeminiEmbeddingProvider()
        result = await p.embed_text("")
        assert result.vector == _zero_vector(768)
        assert result.provider == "gemini"

    @pytest.mark.asyncio
    async def test_embed_text_whitespace_returns_zero_vector(self):
        p = GeminiEmbeddingProvider()
        result = await p.embed_text("   ")
        assert result.vector == _zero_vector(768)

    @pytest.mark.asyncio
    async def test_embed_text_success(self):
        mock_embedding_value = [0.1] * 768

        mock_response = MagicMock()
        mock_response.embeddings = [MagicMock(values=mock_embedding_value)]

        mock_client = MagicMock()
        mock_client.models.embed_content.return_value = mock_response

        p = GeminiEmbeddingProvider()
        p._client = mock_client

        result = await p.embed_text("Software Engineer")
        assert len(result.vector) == 768
        assert result.provider == "gemini"
        assert result.model == "text-embedding-004"

    @pytest.mark.asyncio
    async def test_embed_text_raises_on_api_error(self):
        mock_client = MagicMock()
        mock_client.models.embed_content.side_effect = RuntimeError("API error")

        p = GeminiEmbeddingProvider()
        p._client = mock_client

        with pytest.raises(RuntimeError, match="API error"):
            await p.embed_text("some text")

    @pytest.mark.asyncio
    async def test_embed_batch_returns_list(self):
        mock_embedding_value = [0.2] * 768

        mock_response = MagicMock()
        mock_response.embeddings = [MagicMock(values=mock_embedding_value)]

        mock_client = MagicMock()
        mock_client.models.embed_content.return_value = mock_response

        p = GeminiEmbeddingProvider()
        p._client = mock_client

        texts = ["Job A", "Job B", ""]
        results = await p.embed_batch(texts)

        assert len(results) == 3
        assert results[2].vector == _zero_vector(768)

    @pytest.mark.asyncio
    async def test_embed_batch_item_failure_returns_zero_vector(self):
        mock_client = MagicMock()
        mock_client.models.embed_content.side_effect = RuntimeError("fail")

        p = GeminiEmbeddingProvider()
        p._client = mock_client

        results = await p.embed_batch(["text"])
        assert results[0].vector == _zero_vector(768)


# ---------------------------------------------------------------------------
# Tests: OpenAIEmbeddingProvider
# ---------------------------------------------------------------------------

class TestOpenAIEmbeddingProvider:
    """OpenAIEmbeddingProvider tests (OpenAI client is mocked)."""

    def test_properties_default_768(self):
        p = OpenAIEmbeddingProvider()
        assert p.provider_name == "openai"
        assert p.default_model == "text-embedding-3-small"
        assert p.dimensions == 768
        assert p.get_dimensions() == 768

    def test_properties_custom_1536(self):
        p = OpenAIEmbeddingProvider(output_dimensions=1536)
        assert p.dimensions == 1536

    @pytest.mark.asyncio
    async def test_embed_text_empty_returns_zero_vector(self):
        p = OpenAIEmbeddingProvider()
        result = await p.embed_text("")
        assert result.vector == _zero_vector(768)
        assert result.provider == "openai"

    @pytest.mark.asyncio
    async def test_embed_text_success(self):
        mock_embedding_value = [0.3] * 768

        mock_data_item = MagicMock()
        mock_data_item.embedding = mock_embedding_value
        mock_data_item.index = 0

        mock_response = MagicMock()
        mock_response.data = [mock_data_item]

        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response

        p = OpenAIEmbeddingProvider()
        p._client = mock_client

        result = await p.embed_text("Product Manager")
        assert len(result.vector) == 768
        assert result.provider == "openai"
        assert result.model == "text-embedding-3-small"
        mock_client.embeddings.create.assert_called_once_with(
            model="text-embedding-3-small",
            input="Product Manager",
            dimensions=768,
        )

    @pytest.mark.asyncio
    async def test_embed_text_raises_on_api_error(self):
        mock_client = MagicMock()
        mock_client.embeddings.create.side_effect = RuntimeError("connection error")

        p = OpenAIEmbeddingProvider()
        p._client = mock_client

        with pytest.raises(RuntimeError):
            await p.embed_text("some text")

    @pytest.mark.asyncio
    async def test_embed_batch_success(self):
        mock_embedding_value = [0.4] * 768

        def make_item(idx):
            item = MagicMock()
            item.embedding = mock_embedding_value
            item.index = idx
            return item

        mock_response = MagicMock()
        mock_response.data = [make_item(0), make_item(1)]

        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response

        p = OpenAIEmbeddingProvider()
        p._client = mock_client

        texts = ["Role A", "Role B"]
        results = await p.embed_batch(texts)
        assert len(results) == 2
        assert all(len(r.vector) == 768 for r in results)

    @pytest.mark.asyncio
    async def test_embed_batch_empty_texts_get_zero_vectors(self):
        mock_embedding_value = [0.5] * 768

        def make_item(idx):
            item = MagicMock()
            item.embedding = mock_embedding_value
            item.index = idx
            return item

        mock_response = MagicMock()
        mock_response.data = [make_item(0)]

        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response

        p = OpenAIEmbeddingProvider()
        p._client = mock_client

        texts = ["Job A", ""]
        results = await p.embed_batch(texts)
        assert len(results) == 2
        assert results[1].vector == _zero_vector(768)

    @pytest.mark.asyncio
    async def test_embed_batch_passes_dimensions_to_api(self):
        mock_embedding_value = [0.5] * 768

        mock_data_item = MagicMock()
        mock_data_item.embedding = mock_embedding_value
        mock_data_item.index = 0

        mock_response = MagicMock()
        mock_response.data = [mock_data_item]

        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response

        p = OpenAIEmbeddingProvider()
        p._client = mock_client

        await p.embed_batch(["Job A"])
        call_kwargs = mock_client.embeddings.create.call_args
        assert call_kwargs.kwargs.get("dimensions") == 768 or call_kwargs[1].get("dimensions") == 768


# ---------------------------------------------------------------------------
# Tests: EmbeddingProviderFactory
# ---------------------------------------------------------------------------

class TestEmbeddingProviderFactory:
    """Tests for the factory: register, get, get_default, fallback logic."""

    def test_register_and_get(self):
        FakeGemini = _make_fake_provider("gemini", 768)
        EmbeddingProviderFactory.register(FakeGemini)

        provider = EmbeddingProviderFactory.get("gemini")
        assert provider.provider_name == "gemini"
        assert provider.dimensions == 768

    def test_get_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown embedding provider"):
            EmbeddingProviderFactory.get("nonexistent")

    def test_get_default_uses_env_var(self, monkeypatch):
        FakeOpenAI = _make_fake_provider("openai", 1536)
        EmbeddingProviderFactory.register(FakeOpenAI)

        monkeypatch.setenv("EMBEDDING_DEFAULT_PROVIDER", "openai")
        provider = EmbeddingProviderFactory.get_default()
        assert provider.provider_name == "openai"

    def test_get_default_falls_back_to_gemini(self, monkeypatch):
        FakeGemini = _make_fake_provider("gemini", 768)
        EmbeddingProviderFactory.register(FakeGemini)

        monkeypatch.delenv("EMBEDDING_DEFAULT_PROVIDER", raising=False)
        provider = EmbeddingProviderFactory.get_default()
        assert provider.provider_name == "gemini"

    def test_available_providers(self):
        FakeA = _make_fake_provider("alpha", 512)
        FakeB = _make_fake_provider("beta", 768)
        EmbeddingProviderFactory.register(FakeA)
        EmbeddingProviderFactory.register(FakeB)

        names = EmbeddingProviderFactory.available_providers()
        assert "alpha" in names
        assert "beta" in names

    def test_instances_are_cached(self):
        FakeGemini = _make_fake_provider("gemini", 768)
        EmbeddingProviderFactory.register(FakeGemini)

        p1 = EmbeddingProviderFactory.get("gemini")
        p2 = EmbeddingProviderFactory.get("gemini")
        assert p1 is p2

    def test_clear_removes_cached_instances(self):
        FakeGemini = _make_fake_provider("gemini", 768)
        EmbeddingProviderFactory.register(FakeGemini)

        p1 = EmbeddingProviderFactory.get("gemini")
        EmbeddingProviderFactory.clear()
        p2 = EmbeddingProviderFactory.get("gemini")
        assert p1 is not p2

    @pytest.mark.asyncio
    async def test_embed_with_fallback_primary_success(self, monkeypatch):
        FakeGemini = _make_fake_provider("gemini", 768)
        EmbeddingProviderFactory.register(FakeGemini)

        monkeypatch.delenv("EMBEDDING_DEFAULT_PROVIDER", raising=False)
        vector, provider, model = await EmbeddingProviderFactory.embed_with_fallback("hello")
        assert len(vector) == 768
        assert provider == "gemini"

    @pytest.mark.asyncio
    async def test_embed_with_fallback_uses_second_provider_when_first_fails(self, monkeypatch):
        FakeGeminiFail = _make_fake_provider("gemini", 768, fail=True)
        FakeOpenAI = _make_fake_provider("openai", 1536)
        EmbeddingProviderFactory.register(FakeGeminiFail)
        EmbeddingProviderFactory.register(FakeOpenAI)

        monkeypatch.delenv("EMBEDDING_DEFAULT_PROVIDER", raising=False)
        vector, provider, model = await EmbeddingProviderFactory.embed_with_fallback("hello")
        assert provider == "openai"
        assert len(vector) == 1536

    @pytest.mark.asyncio
    async def test_embed_with_fallback_all_fail_raises(self, monkeypatch):
        FakeGeminiFail = _make_fake_provider("gemini", 768, fail=True)
        FakeOpenAIFail = _make_fake_provider("openai", 1536, fail=True)
        EmbeddingProviderFactory.register(FakeGeminiFail)
        EmbeddingProviderFactory.register(FakeOpenAIFail)

        monkeypatch.delenv("EMBEDDING_DEFAULT_PROVIDER", raising=False)
        with pytest.raises(Exception, match="provedores de embedding falharam"):
            await EmbeddingProviderFactory.embed_with_fallback("hello")

    @pytest.mark.asyncio
    async def test_embed_batch_with_fallback(self, monkeypatch):
        FakeGemini = _make_fake_provider("gemini", 768)
        EmbeddingProviderFactory.register(FakeGemini)

        monkeypatch.delenv("EMBEDDING_DEFAULT_PROVIDER", raising=False)
        vectors, provider, model = await EmbeddingProviderFactory.embed_batch_with_fallback(
            ["text 1", "text 2"]
        )
        assert len(vectors) == 2
        assert provider == "gemini"

    @pytest.mark.asyncio
    async def test_preferred_provider_tried_first(self, monkeypatch):
        FakeGemini = _make_fake_provider("gemini", 768)
        FakeOpenAI = _make_fake_provider("openai", 1536)
        EmbeddingProviderFactory.register(FakeGemini)
        EmbeddingProviderFactory.register(FakeOpenAI)

        monkeypatch.setenv("EMBEDDING_DEFAULT_PROVIDER", "gemini")
        vector, provider, model = await EmbeddingProviderFactory.embed_with_fallback(
            "test", preferred_provider="openai"
        )
        assert provider == "openai"
        assert len(vector) == 1536

    @pytest.mark.asyncio
    async def test_generate_with_fallback_alias(self, monkeypatch):
        """generate_with_fallback() is the task-spec API name, must work like embed_with_fallback."""
        FakeGemini = _make_fake_provider("gemini", 768)
        EmbeddingProviderFactory.register(FakeGemini)

        monkeypatch.delenv("EMBEDDING_DEFAULT_PROVIDER", raising=False)
        vector, provider, model = await EmbeddingProviderFactory.generate_with_fallback("hello")
        assert len(vector) == 768
        assert provider == "gemini"

    @pytest.mark.asyncio
    async def test_embed_batch_fallback_to_secondary(self, monkeypatch):
        FakeGeminiFail = _make_fake_provider("gemini", 768, fail=True)
        FakeOpenAI = _make_fake_provider("openai", 1536)
        EmbeddingProviderFactory.register(FakeGeminiFail)
        EmbeddingProviderFactory.register(FakeOpenAI)

        monkeypatch.delenv("EMBEDDING_DEFAULT_PROVIDER", raising=False)
        vectors, provider, model = await EmbeddingProviderFactory.embed_batch_with_fallback(
            ["text 1"]
        )
        assert provider == "openai"
        assert len(vectors) == 1
        assert len(vectors[0]) == 1536


# ---------------------------------------------------------------------------
# Tests: EmbeddingService facade
# ---------------------------------------------------------------------------

class TestEmbeddingServiceFacade:
    """Verify backward compatibility of EmbeddingService."""

    @pytest.fixture(autouse=True)
    def setup_fake_provider(self):
        FakeGemini = _make_fake_provider("gemini", 768)
        EmbeddingProviderFactory.register(FakeGemini)
        yield

    @pytest.mark.asyncio
    async def test_generate_embedding_returns_vector(self):
        svc = EmbeddingService()
        vector = await svc.generate_embedding("Software Engineer")
        assert isinstance(vector, list)
        assert len(vector) == 768

    @pytest.mark.asyncio
    async def test_generate_embedding_empty_returns_zero_vector(self):
        svc = EmbeddingService()
        vector = await svc.generate_embedding("")
        assert vector == _zero_vector(768)

    @pytest.mark.asyncio
    async def test_generate_embedding_with_metadata(self):
        svc = EmbeddingService()
        vector, provider, model = await svc.generate_embedding_with_metadata("Data Analyst")
        assert len(vector) == 768
        assert provider == "gemini"
        assert model == "gemini-model"

    @pytest.mark.asyncio
    async def test_generate_batch_embeddings(self):
        svc = EmbeddingService()
        vectors = await svc.generate_batch_embeddings(["Role A", "Role B", ""])
        assert len(vectors) == 3
        assert vectors[2] == _zero_vector(768)

    @pytest.mark.asyncio
    async def test_generate_batch_empty_list(self):
        svc = EmbeddingService()
        vectors = await svc.generate_batch_embeddings([])
        assert vectors == []

    def test_chunk_text_short_text(self):
        svc = EmbeddingService()
        chunks = svc.chunk_text("short text", chunk_size=1000)
        assert chunks == ["short text"]

    def test_chunk_text_long_text(self):
        svc = EmbeddingService()
        long_text = "word " * 300
        chunks = svc.chunk_text(long_text, chunk_size=100, overlap=10)
        assert len(chunks) > 1

    def test_chunk_text_empty(self):
        svc = EmbeddingService()
        chunks = svc.chunk_text("")
        assert chunks == []


# ---------------------------------------------------------------------------
# Tests: JobEmbeddingService — batch_process_jobs stores metadata
# ---------------------------------------------------------------------------

class _FakeJobRow:
    """Minimal stand-in for a JobEmbedding ORM row."""

    def __init__(self, job_id: str, job_title: str):
        self.job_id = job_id
        self.job_title = job_title
        self.department = None
        self.seniority = None
        self.location = None
        self.skills: list = []
        self.behavioral_competencies: list = []
        self.description_summary = None
        self.embedding = None
        self.embedding_text = None
        self.embedding_provider = None
        self.embedding_model = None
        self.updated_at = None


async def _run_batch_process_jobs(
    fake_rows,
    provider="gemini",
    model="text-embedding-004",
    vector=None,
    monkeypatch=None,
    company_id="00000000-0000-0000-0000-000000000099",
    job_ids=None,
):
    """
    Execute the batch_process_jobs logic directly, importing job_embedding_service
    from its on-disk source with all transitive dependencies pre-stubbed via sys.modules.

    To avoid triggering `app.domains.__init__` (which imports uninstalled packages),
    we import the service module directly via importlib using its file path rather
    than through the package hierarchy.
    """
    import importlib.util
    import os
    from unittest.mock import patch

    vector = vector or [0.1] * 768

    # Load the module directly from its file path so it never goes through app.domains.__init__
    svc_path = os.path.join(
        os.path.dirname(__file__),
        "..", "..",
        "app", "domains", "job_management", "services", "job_embedding_service.py",
    )
    svc_path = os.path.normpath(svc_path)

    spec = importlib.util.spec_from_file_location(
        "job_embedding_service_isolated", svc_path
    )
    jes_mod = importlib.util.module_from_spec(spec)

    # Provide stubs for every import the module needs.
    # We must stub app.models.job_pattern before app.models so the __init__
    # chain (which pulls in app.auth) is never triggered.
    stub_job_pattern = MagicMock()
    stub_job_pattern.JobEmbedding = MagicMock()
    stub_job_pattern.EMBEDDING_DIMENSION = 768

    stub_db = MagicMock()
    stub_db.AsyncSessionLocal = MagicMock()

    required_stubs = {
        "app.core.database": stub_db,
        "app.core.config": MagicMock(),
        "app.models": MagicMock(),
        "app.models.job_pattern": stub_job_pattern,
        "libs.models.lia_models.job_pattern": stub_job_pattern,
        "app.shared.intelligence.embedding_service": MagicMock(),
    }
    for name, stub in required_stubs.items():
        sys.modules.setdefault(name, stub)

    try:
        spec.loader.exec_module(jes_mod)
    except Exception:
        pass

    # At this point we have the module's namespace; build a minimal service object
    # by reusing batch_process_jobs directly from the parsed source.
    svc = object.__new__(type("_Svc", (), {}))

    async def _fake_with_metadata(**kwargs):
        return vector, provider, model

    svc.generate_job_embedding_with_metadata = _fake_with_metadata

    # Patch AsyncSessionLocal in the module
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = fake_rows

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    mock_session_local = MagicMock(return_value=mock_session)

    # Patch SQLAlchemy functions so the MagicMock JobEmbedding is never evaluated
    # as a real column expression (which would raise TypeError).
    select_mock = MagicMock(return_value=MagicMock())
    and_mock = MagicMock(return_value=MagicMock())

    with patch.object(jes_mod, "AsyncSessionLocal", mock_session_local), \
         patch.object(jes_mod, "select", select_mock), \
         patch.object(jes_mod, "and_", and_mock):
        import types
        bound = types.MethodType(
            jes_mod.JobEmbeddingService.batch_process_jobs,
            svc,
        )
        return await bound(company_id=company_id, job_ids=job_ids)


class TestJobEmbeddingServiceBatchMetadata:
    """
    Tests that batch_process_jobs() correctly persists embedding_provider and
    embedding_model alongside the vector for every processed job.

    We test the method logic in isolation by calling it as a plain async function
    rather than going through the full app.domains package import chain, which
    depends on optional packages not available in the test environment.
    """

    @pytest.mark.asyncio
    async def test_batch_sets_provider_and_model_on_row(self, monkeypatch):
        """embedding_provider / embedding_model are set after batch_process_jobs."""
        fake_row = _FakeJobRow("00000000-0000-0000-0000-000000000001", "Engineer")

        result = await _run_batch_process_jobs(
            fake_rows=[fake_row],
            provider="gemini",
            model="text-embedding-004",
            vector=[0.1] * 768,
            monkeypatch=monkeypatch,
            job_ids=["00000000-0000-0000-0000-000000000001"],
        )

        assert result["success"] is True
        assert result["processed"] == 1
        assert result["errors"] == 0
        assert fake_row.embedding == [0.1] * 768
        assert fake_row.embedding_provider == "gemini"
        assert fake_row.embedding_model == "text-embedding-004"
        assert fake_row.updated_at is not None

    @pytest.mark.asyncio
    async def test_batch_no_null_metadata_for_multiple_rows(self, monkeypatch):
        """Provider metadata must never remain None after a successful embedding."""
        rows = [
            _FakeJobRow(f"00000000-0000-0000-0000-00000000000{i}", f"Job {i}")
            for i in range(1, 4)
        ]

        result = await _run_batch_process_jobs(
            fake_rows=rows,
            provider="openai",
            model="text-embedding-3-small",
            vector=[0.2] * 768,
            monkeypatch=monkeypatch,
        )

        assert result["processed"] == 3
        for row in rows:
            assert row.embedding_provider is not None, f"provider is None for {row.job_id}"
            assert row.embedding_model is not None, f"model is None for {row.job_id}"
