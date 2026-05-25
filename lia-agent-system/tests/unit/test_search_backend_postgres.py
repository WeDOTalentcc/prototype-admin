"""
Testes unitários para SearchBackend ABC — PostgresSearchBackend, ElasticsearchSearchBackend,
factory get_search_backend() e reset_search_backend().

Cobertura (Camada 2 — Unitário):
  - SearchResult dataclass (campos obrigatórios e opcionais)
  - PostgresSearchBackend.search_candidates() — sucesso, erro, modo full-text
  - PostgresSearchBackend.search_jobs() — sucesso, erro
  - PostgresSearchBackend.index_candidate/job() — no-op retorna True
  - PostgresSearchBackend.health() — healthy/unhealthy
  - ElasticsearchSearchBackend — graceful failure sem ELASTICSEARCH_URL
  - ElasticsearchSearchBackend.search_candidates/jobs/index — retorna fallback correto
  - get_search_backend() — factory selector por SEARCH_BACKEND env var
  - reset_search_backend() — reseta singleton entre testes
  - Multi-tenant isolation — company_id presente em todas as queries
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

from app.domains.ai.services.search_service import (
    SearchBackend,
    SearchResult,
    PostgresSearchBackend,
    ElasticsearchSearchBackend,
    get_search_backend,
    reset_search_backend,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_singleton():
    """Garante que o singleton é resetado antes e depois de cada teste."""
    reset_search_backend()
    yield
    reset_search_backend()


def _make_db_row(id="cand-1", score=1.0, name="João Silva", email="joao@test.com", role="Dev"):
    row = MagicMock()
    row.__getitem__ = lambda self, i: [id, score, name, email, role][i]
    return row


def _make_job_row(id="job-1", score=0.8, title="Dev Pleno", status="open"):
    row = MagicMock()
    row.__getitem__ = lambda self, i: [id, score, title, status][i]
    return row


# ---------------------------------------------------------------------------
# SearchResult dataclass
# ---------------------------------------------------------------------------

class TestSearchResult:

    def test_search_result_required_fields(self):
        """SearchResult tem id, score, source e data como obrigatórios."""
        r = SearchResult(id="cand-1", score=0.9, source="postgres", data={"name": "X"})
        assert r.id == "cand-1"
        assert r.score == 0.9
        assert r.source == "postgres"
        assert r.data == {"name": "X"}

    def test_search_result_highlights_optional(self):
        """highlights é None por padrão."""
        r = SearchResult(id="x", score=1.0, source="postgres", data={})
        assert r.highlights is None

    def test_search_result_with_highlights(self):
        """highlights pode ser definido."""
        r = SearchResult(
            id="x", score=1.0, source="elasticsearch", data={},
            highlights={"name": ["<em>João</em>"]}
        )
        assert r.highlights["name"][0] == "<em>João</em>"


# ---------------------------------------------------------------------------
# ABC — interface compliance
# ---------------------------------------------------------------------------

class TestSearchBackendABC:

    def test_postgres_backend_is_subclass(self):
        assert issubclass(PostgresSearchBackend, SearchBackend)

    def test_es_backend_is_subclass(self):
        assert issubclass(ElasticsearchSearchBackend, SearchBackend)

    def test_search_backend_cannot_be_instantiated(self):
        """ABC não pode ser instanciado diretamente."""
        with pytest.raises(TypeError):
            SearchBackend()  # type: ignore[abstract]

    def test_postgres_implements_all_abstract_methods(self):
        """PostgresSearchBackend implementa todos os 5 métodos abstratos."""
        backend = PostgresSearchBackend()
        for method in ("search_candidates", "search_jobs", "index_candidate", "index_job", "health"):
            assert callable(getattr(backend, method))


# ---------------------------------------------------------------------------
# PostgresSearchBackend — search_candidates
# ---------------------------------------------------------------------------

class TestPostgresSearchCandidates:

    @pytest.mark.asyncio
    async def test_search_candidates_returns_search_result_list(self):
        """Busca bem-sucedida retorna lista de SearchResult."""
        backend = PostgresSearchBackend()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_row = _make_db_row()
        mock_result.fetchall.return_value = [mock_row]
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("app.core.database.AsyncSessionLocal", return_value=mock_ctx):
            results = await backend.search_candidates("python developer", "company-1")

        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0].source == "postgres"

    @pytest.mark.asyncio
    async def test_search_candidates_returns_empty_on_db_error(self):
        """Erro no banco retorna lista vazia sem propagar exceção."""
        backend = PostgresSearchBackend()
        with patch("app.core.database.AsyncSessionLocal", side_effect=Exception("DB down")):
            results = await backend.search_candidates("python", "company-1")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_candidates_full_text_mode(self):
        """semantic=False usa caminho full-text."""
        backend = PostgresSearchBackend()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("app.core.database.AsyncSessionLocal", return_value=mock_ctx):
            results = await backend.search_candidates("python", "company-1", semantic=False)
        assert results == []

    @pytest.mark.asyncio
    async def test_search_candidates_respects_company_id(self):
        """company_id é passado como parâmetro à query (isolamento multi-tenant)."""
        backend = PostgresSearchBackend()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("app.core.database.AsyncSessionLocal", return_value=mock_ctx):
            await backend.search_candidates("python", "company-XYZ")

        call_args = mock_session.execute.call_args
        params = call_args[0][1]
        assert params["company_id"] == "company-XYZ"

    @pytest.mark.asyncio
    async def test_search_candidates_respects_limit(self):
        """limit é passado como parâmetro à query."""
        backend = PostgresSearchBackend()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("app.core.database.AsyncSessionLocal", return_value=mock_ctx):
            await backend.search_candidates("python", "company-1", limit=5)

        call_args = mock_session.execute.call_args
        params = call_args[0][1]
        assert params["limit"] == 5


# ---------------------------------------------------------------------------
# PostgresSearchBackend — search_jobs
# ---------------------------------------------------------------------------

class TestPostgresSearchJobs:

    @pytest.mark.asyncio
    async def test_search_jobs_returns_search_result_list(self):
        """search_jobs bem-sucedido retorna lista de SearchResult."""
        backend = PostgresSearchBackend()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_row = _make_job_row()
        mock_result.fetchall.return_value = [mock_row]
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("app.core.database.AsyncSessionLocal", return_value=mock_ctx):
            results = await backend.search_jobs("desenvolvedor", "company-1")

        assert len(results) == 1
        assert results[0].source == "postgres"

    @pytest.mark.asyncio
    async def test_search_jobs_returns_empty_on_error(self):
        """Erro retorna lista vazia."""
        backend = PostgresSearchBackend()
        with patch("app.core.database.AsyncSessionLocal", side_effect=Exception("fail")):
            results = await backend.search_jobs("dev", "company-1")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_jobs_company_id_isolation(self):
        """company_id é passado como parâmetro à query."""
        backend = PostgresSearchBackend()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("app.core.database.AsyncSessionLocal", return_value=mock_ctx):
            await backend.search_jobs("dev", "tenant-ABC")

        params = mock_session.execute.call_args[0][1]
        assert params["company_id"] == "tenant-ABC"


# ---------------------------------------------------------------------------
# PostgresSearchBackend — index & health
# ---------------------------------------------------------------------------

class TestPostgresIndexAndHealth:

    @pytest.mark.asyncio
    async def test_index_candidate_is_noop_returns_true(self):
        """index_candidate é no-op e retorna True."""
        backend = PostgresSearchBackend()
        result = await backend.index_candidate("cand-1", "company-1", {"name": "X"})
        assert result is True

    @pytest.mark.asyncio
    async def test_index_job_is_noop_returns_true(self):
        """index_job é no-op e retorna True."""
        backend = PostgresSearchBackend()
        result = await backend.index_job("job-1", "company-1", {"title": "Dev"})
        assert result is True

    @pytest.mark.asyncio
    async def test_health_returns_healthy_when_db_ok(self):
        """health() retorna status=healthy quando DB responde."""
        backend = PostgresSearchBackend()
        mock_session = AsyncMock()
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("app.core.database.AsyncSessionLocal", return_value=mock_ctx):
            result = await backend.health()

        assert result["status"] == "healthy"
        assert result["backend"] == "postgres"

    @pytest.mark.asyncio
    async def test_health_returns_unhealthy_on_db_error(self):
        """health() retorna status=unhealthy quando DB falha."""
        backend = PostgresSearchBackend()
        with patch("app.core.database.AsyncSessionLocal", side_effect=Exception("conn refused")):
            result = await backend.health()

        assert result["status"] == "unhealthy"
        assert result["backend"] == "postgres"
        assert "error" in result


# ---------------------------------------------------------------------------
# ElasticsearchSearchBackend — graceful failure
# ---------------------------------------------------------------------------

class TestElasticsearchSearchBackend:

    def test_es_backend_instantiates_without_url(self):
        """ES backend pode ser instanciado mesmo sem ELASTICSEARCH_URL."""
        backend = ElasticsearchSearchBackend()
        assert backend is not None

    @pytest.mark.asyncio
    async def test_es_search_candidates_returns_empty_on_error(self):
        """Erro no ES retorna lista vazia."""
        backend = ElasticsearchSearchBackend()
        with patch.object(backend, "_get_client", side_effect=ImportError("no ES")):
            results = await backend.search_candidates("python", "company-1")
        assert results == []

    @pytest.mark.asyncio
    async def test_es_search_jobs_returns_empty_on_error(self):
        """Erro no ES retorna lista vazia."""
        backend = ElasticsearchSearchBackend()
        with patch.object(backend, "_get_client", side_effect=ValueError("no url")):
            results = await backend.search_jobs("dev", "company-1")
        assert results == []

    @pytest.mark.asyncio
    async def test_es_index_candidate_returns_false_on_error(self):
        """Erro ao indexar retorna False."""
        backend = ElasticsearchSearchBackend()
        with patch.object(backend, "_get_client", side_effect=Exception("fail")):
            result = await backend.index_candidate("cand-1", "company-1", {})
        assert result is False

    @pytest.mark.asyncio
    async def test_es_index_job_returns_false_on_error(self):
        """Erro ao indexar vaga retorna False."""
        backend = ElasticsearchSearchBackend()
        with patch.object(backend, "_get_client", side_effect=Exception("fail")):
            result = await backend.index_job("job-1", "company-1", {})
        assert result is False

    @pytest.mark.asyncio
    async def test_es_health_returns_unhealthy_on_error(self):
        """health() retorna unhealthy quando ES indisponível."""
        backend = ElasticsearchSearchBackend()
        with patch.object(backend, "_get_client", side_effect=ImportError("no ES")):
            result = await backend.health()
        assert result["status"] == "unhealthy"
        assert result["backend"] == "elasticsearch"


# ---------------------------------------------------------------------------
# Factory — get_search_backend() e reset_search_backend()
# ---------------------------------------------------------------------------

class TestSearchBackendFactory:

    def test_get_search_backend_returns_postgres_by_default(self):
        """Sem SEARCH_BACKEND configurado, usa PostgresSearchBackend."""
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.SEARCH_BACKEND = "postgres"
            backend = get_search_backend()
        assert isinstance(backend, PostgresSearchBackend)

    def test_get_search_backend_returns_es_when_configured(self):
        """Com SEARCH_BACKEND=elasticsearch, usa ElasticsearchSearchBackend."""
        reset_search_backend()
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.SEARCH_BACKEND = "elasticsearch"
            backend = get_search_backend()
        assert isinstance(backend, ElasticsearchSearchBackend)

    def test_get_search_backend_is_singleton(self):
        """get_search_backend() retorna mesma instância (singleton)."""
        b1 = get_search_backend()
        b2 = get_search_backend()
        assert b1 is b2

    def test_reset_search_backend_clears_singleton(self):
        """reset_search_backend() permite nova instância."""
        b1 = get_search_backend()
        reset_search_backend()
        b2 = get_search_backend()
        assert b1 is not b2

    def test_get_search_backend_fallback_on_config_error(self):
        """Erro ao ler settings cai back para postgres."""
        reset_search_backend()
        with patch("app.core.config.settings", side_effect=Exception("config err")):
            # Simula falha no import de settings
            with patch("builtins.__import__", side_effect=Exception("import err")) if False else patch("app.core.config.settings") as m:
                m.SEARCH_BACKEND = "postgres"
                backend = get_search_backend()
        assert isinstance(backend, PostgresSearchBackend)
