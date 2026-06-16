"""
Unit tests — BrokerInterface & Factory (Task #67).

Cobertura:
- get_broker() retorna instância correta por backend
- RedisBroker, RabbitMQBroker, PubSubBroker: types corretos
- PubSubBroker.health_check() retorna dict com status="stub"
- PubSubBroker.publish() levanta NotImplementedError
- PubSubBroker.consume() levanta NotImplementedError
- _get_celery_broker_url() mapeia BROKER_BACKEND para URL correta
- _get_celery_broker_url() CELERY_BROKER_URL tem precedência
- /health broker component shape (broker key presente)
"""
import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

pytestmark = pytest.mark.easy


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_broker_singleton():
    """Reseta o singleton entre testes para isolamento."""
    import app.shared.messaging.broker_interface as mod
    original = mod._broker_instance
    yield
    mod._broker_instance = original


# ---------------------------------------------------------------------------
# get_broker() factory
# ---------------------------------------------------------------------------

class TestGetBrokerFactory:
    def test_redis_backend_returns_redis_broker(self):
        from app.shared.messaging.broker_interface import get_broker, RedisBroker
        broker = get_broker("redis")
        assert isinstance(broker, RedisBroker)

    def test_rabbitmq_backend_returns_rabbitmq_broker(self):
        from app.shared.messaging.broker_interface import get_broker, RabbitMQBroker
        broker = get_broker("rabbitmq")
        assert isinstance(broker, RabbitMQBroker)

    def test_pubsub_backend_returns_pubsub_broker(self):
        from app.shared.messaging.broker_interface import get_broker, PubSubBroker
        broker = get_broker("pubsub")
        assert isinstance(broker, PubSubBroker)

    def test_unknown_backend_falls_back_to_redis(self):
        from app.shared.messaging.broker_interface import get_broker, RedisBroker
        broker = get_broker("unknown_backend_xyz")
        assert isinstance(broker, RedisBroker)

    def test_env_var_broker_backend_redis(self, monkeypatch):
        monkeypatch.setenv("BROKER_BACKEND", "redis")
        from app.shared.messaging.broker_interface import get_broker, RedisBroker
        broker = get_broker()
        assert isinstance(broker, RedisBroker)

    def test_env_var_broker_backend_rabbitmq(self, monkeypatch):
        monkeypatch.setenv("BROKER_BACKEND", "rabbitmq")
        from app.shared.messaging.broker_interface import get_broker, RabbitMQBroker
        broker = get_broker()
        assert isinstance(broker, RabbitMQBroker)

    def test_env_var_broker_backend_pubsub(self, monkeypatch):
        monkeypatch.setenv("BROKER_BACKEND", "pubsub")
        from app.shared.messaging.broker_interface import get_broker, PubSubBroker
        broker = get_broker()
        assert isinstance(broker, PubSubBroker)

    def test_default_is_redis(self, monkeypatch):
        monkeypatch.delenv("BROKER_BACKEND", raising=False)
        from app.shared.messaging.broker_interface import get_broker, RedisBroker
        broker = get_broker()
        assert isinstance(broker, RedisBroker)

    def test_case_insensitive_backend(self):
        from app.shared.messaging.broker_interface import get_broker, RedisBroker
        broker = get_broker("REDIS")
        assert isinstance(broker, RedisBroker)


# ---------------------------------------------------------------------------
# BrokerInterface ABC enforcement
# ---------------------------------------------------------------------------

class TestBrokerInterfaceABC:
    def test_cannot_instantiate_abstract_interface(self):
        from app.shared.messaging.broker_interface import BrokerInterface
        with pytest.raises(TypeError):
            BrokerInterface()

    def test_abstract_methods_defined(self):
        from app.shared.messaging.broker_interface import BrokerInterface
        assert "publish" in BrokerInterface.__abstractmethods__
        assert "consume" in BrokerInterface.__abstractmethods__
        assert "health_check" in BrokerInterface.__abstractmethods__


# ---------------------------------------------------------------------------
# PubSubBroker stub behavior
# ---------------------------------------------------------------------------

class TestPubSubBrokerStub:
    @pytest.fixture
    def pubsub_broker(self):
        from app.shared.messaging.broker_interface import PubSubBroker
        return PubSubBroker(project_id="test-project")

    @pytest.mark.asyncio
    async def test_health_check_returns_stub_status(self, pubsub_broker):
        result = await pubsub_broker.health_check()
        assert result["status"] == "stub"
        assert result["backend"] == "pubsub"
        assert "project_id" in result
        assert "note" in result

    @pytest.mark.asyncio
    async def test_publish_raises_not_implemented(self, pubsub_broker):
        with pytest.raises(NotImplementedError) as exc_info:
            await pubsub_broker.publish("topic", {"key": "value"})
        assert "gcp-migration-guide" in str(exc_info.value).lower() or "stub" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_consume_raises_not_implemented(self, pubsub_broker):
        with pytest.raises(NotImplementedError):
            await pubsub_broker.consume("topic")

    def test_pubsub_project_id_from_arg(self):
        from app.shared.messaging.broker_interface import PubSubBroker
        broker = PubSubBroker(project_id="my-project")
        assert broker._project_id == "my-project"

    def test_pubsub_project_id_from_env(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "env-project")
        from app.shared.messaging.broker_interface import PubSubBroker
        broker = PubSubBroker()
        assert broker._project_id == "env-project"


# ---------------------------------------------------------------------------
# RedisBroker — client init correctness
# ---------------------------------------------------------------------------

class TestRedisBrokerInit:
    def test_init_stores_redis_url(self, monkeypatch):
        monkeypatch.setenv("REDIS_URL", "redis://testhost:6379/0")
        from app.shared.messaging.broker_interface import RedisBroker
        broker = RedisBroker()
        assert broker._redis_url == "redis://testhost:6379/0"

    def test_init_accepts_explicit_url(self):
        from app.shared.messaging.broker_interface import RedisBroker
        broker = RedisBroker(redis_url="redis://custom:6380/1")
        assert broker._redis_url == "redis://custom:6380/1"

    @pytest.mark.asyncio
    async def test_get_client_not_awaitable_from_url(self):
        """Garante que from_url() não é awaited (redis.asyncio retorna client sync)."""
        from app.shared.messaging.broker_interface import RedisBroker

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)

        with patch("redis.asyncio.from_url", return_value=mock_client) as mock_from_url:
            broker = RedisBroker(redis_url="redis://localhost:6379/0")
            client = await broker._get_client()

        # from_url deve ter sido chamado SEM await (não é coroutine)
        mock_from_url.assert_called_once()
        assert client is mock_client

    @pytest.mark.asyncio
    async def test_health_check_unhealthy_when_redis_down(self):
        from app.shared.messaging.broker_interface import RedisBroker

        with patch("redis.asyncio.from_url", side_effect=ConnectionError("refused")):
            broker = RedisBroker(redis_url="redis://nonexistent:9999/0")
            broker._client = None
            result = await broker.health_check()

        assert result["status"] == "unhealthy"
        assert result["backend"] == "redis"
        assert "error" in result


# ---------------------------------------------------------------------------
# Celery broker URL factory
# ---------------------------------------------------------------------------

class TestCeleryBrokerFactory:
    def _import_factory(self):
        """Import factory function fresh (avoids module-level caching)."""
        import importlib
        import sys
        if "lia_config.celery_app" in sys.modules:
            mod = sys.modules["lia_config.celery_app"]
            return mod._get_celery_broker_url, mod._get_celery_result_backend
        else:
            sys.path.insert(0, "libs/config")
            from lia_config.celery_app import _get_celery_broker_url, _get_celery_result_backend
            return _get_celery_broker_url, _get_celery_result_backend

    def test_broker_backend_redis_maps_to_redis_url(self, monkeypatch):
        monkeypatch.setenv("BROKER_BACKEND", "redis")
        monkeypatch.delenv("CELERY_BROKER_URL", raising=False)
        get_url, _ = self._import_factory()
        url = get_url()
        assert url.startswith("redis://")

    def test_broker_backend_rabbitmq_maps_to_amqp_url(self, monkeypatch):
        monkeypatch.setenv("BROKER_BACKEND", "rabbitmq")
        monkeypatch.delenv("CELERY_BROKER_URL", raising=False)
        get_url, _ = self._import_factory()
        url = get_url()
        assert url.startswith("amqp://")

    def test_celery_broker_url_env_takes_precedence(self, monkeypatch):
        monkeypatch.setenv("BROKER_BACKEND", "rabbitmq")
        monkeypatch.setenv("CELERY_BROKER_URL", "redis://override:6379/1")
        get_url, _ = self._import_factory()
        url = get_url()
        assert url == "redis://override:6379/1"

    def test_default_is_redis_url(self, monkeypatch):
        monkeypatch.delenv("BROKER_BACKEND", raising=False)
        monkeypatch.delenv("CELERY_BROKER_URL", raising=False)
        get_url, _ = self._import_factory()
        url = get_url()
        assert url.startswith("redis://")


# ---------------------------------------------------------------------------
# /health broker component shape
# ---------------------------------------------------------------------------

class TestHealthBrokerComponent:
    @pytest.mark.asyncio
    async def test_check_broker_returns_dict_with_status(self):
        """_check_broker() deve retornar dict com chave 'status'."""
        from app.api.v1.system_health import _check_broker

        mock_broker = AsyncMock()
        mock_broker.health_check = AsyncMock(return_value={
            "status": "healthy",
            "backend": "redis",
            "latency_ms": 1.2,
        })

        with patch("app.shared.messaging.broker_interface.get_default_broker", return_value=mock_broker):
            result = await _check_broker()

        assert "status" in result

    @pytest.mark.asyncio
    async def test_check_broker_handles_exception(self):
        """_check_broker() deve retornar unhealthy quando broker falha."""
        from app.api.v1.system_health import _check_broker

        with patch(
            "app.shared.messaging.broker_interface.get_default_broker",
            side_effect=RuntimeError("broker down"),
        ):
            result = await _check_broker()

        assert result["status"] == "unhealthy"
        assert "error" in result
