"""
Testes de integração para o sistema de Platform Events.

Cobre:
- Validação de schema dos eventos
- Registro e despacho de handlers
- Comportamento graceful quando RabbitMQ está indisponível
- Propagação correta de company_id
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.shared.messaging.platform_events import (
    CandidateMovedEvent,
    CompanyConfiguredEvent,
    JobClosedEvent,
    JobPublishedEvent,
    PlatformEvent,
    clear_event_handlers,
    dispatch_event,
    get_registered_handlers,
    publish_platform_event,
    register_event_handler,
)


@pytest.fixture(autouse=True)
def reset_handlers():
    """Limpa handlers registrados antes de cada teste para isolamento."""
    clear_event_handlers()
    yield
    clear_event_handlers()


class TestPlatformEventSchema:
    def test_platform_event_schema_valid(self):
        """PlatformEvent com campos obrigatórios é válido."""
        event = PlatformEvent(
            event_type="vagas.job.published",
            company_id="company-123",
            payload={"job_id": "job-001", "title": "Engenheiro Python"},
            source_api="api-vagas",
        )
        assert event.event_type == "vagas.job.published"
        assert event.company_id == "company-123"
        assert event.payload["job_id"] == "job-001"
        assert event.source_api == "api-vagas"
        assert event.version == "1.0"
        assert event.event_id  # gerado automaticamente
        assert isinstance(event.occurred_at, datetime)

    def test_job_published_event_type(self):
        """JobPublishedEvent tem event_type e source_api corretos."""
        event = JobPublishedEvent(
            company_id="company-abc",
            payload={"job_id": "job-999"},
        )
        assert event.event_type == "vagas.job.published"
        assert event.source_api == "api-vagas"

    def test_job_closed_event_type(self):
        """JobClosedEvent tem event_type e source_api corretos."""
        event = JobClosedEvent(
            company_id="company-abc",
            payload={"job_id": "job-998"},
        )
        assert event.event_type == "vagas.job.closed"
        assert event.source_api == "api-vagas"

    def test_candidate_moved_event_type(self):
        """CandidateMovedEvent tem event_type e source_api corretos."""
        event = CandidateMovedEvent(
            company_id="company-xyz",
            payload={
                "candidate_id": "cand-001",
                "from_stage": "triage",
                "to_stage": "interview",
            },
        )
        assert event.event_type == "funil.candidate.moved"
        assert event.source_api == "api-funil"

    def test_company_configured_event_type(self):
        """CompanyConfiguredEvent tem event_type e source_api corretos."""
        event = CompanyConfiguredEvent(
            company_id="company-new",
            payload={"onboarding_step": "completed"},
        )
        assert event.event_type == "onboarding.company.configured"
        assert event.source_api == "api-onboarding"

    def test_event_preserves_company_id(self):
        """company_id é propagado corretamente no evento."""
        company_id = "my-tenant-uuid-1234"
        event = JobPublishedEvent(
            company_id=company_id,
            payload={"job_id": "j1"},
        )
        assert event.company_id == company_id

        # Verificar que serialização preserva company_id
        dumped = event.model_dump(mode="json")
        assert dumped["company_id"] == company_id

    def test_event_id_is_unique(self):
        """Cada evento gerado tem event_id único."""
        e1 = JobPublishedEvent(company_id="c1", payload={})
        e2 = JobPublishedEvent(company_id="c1", payload={})
        assert e1.event_id != e2.event_id

    def test_occurred_at_is_utc(self):
        """occurred_at é gerado em UTC."""
        event = PlatformEvent(
            event_type="test.event",
            company_id="c1",
            payload={},
            source_api="test",
        )
        assert event.occurred_at.tzinfo is not None


class TestEventHandlerRegistry:
    @pytest.mark.asyncio
    async def test_register_and_dispatch_handler(self):
        """Registrar handler + dispatch → handler é chamado com o evento."""
        received_events = []

        async def my_handler(event: PlatformEvent) -> None:
            received_events.append(event)

        register_event_handler("test.event.dispatched", my_handler)

        raw = {
            "event_type": "test.event.dispatched",
            "company_id": "company-dispatch-test",
            "payload": {"key": "value"},
            "source_api": "api-test",
        }
        await dispatch_event(raw)

        assert len(received_events) == 1
        assert received_events[0].company_id == "company-dispatch-test"
        assert received_events[0].event_type == "test.event.dispatched"

    @pytest.mark.asyncio
    async def test_dispatch_unknown_event_no_error(self):
        """Evento sem handler registrado não lança exceção."""
        raw = {
            "event_type": "unknown.event.type",
            "company_id": "company-x",
            "payload": {},
            "source_api": "api-x",
        }
        # Não deve lançar exceção
        await dispatch_event(raw)

    @pytest.mark.asyncio
    async def test_multiple_handlers_all_called(self):
        """Múltiplos handlers para o mesmo event_type são todos chamados."""
        call_count = {"n": 0}

        async def handler_a(event: PlatformEvent) -> None:
            call_count["n"] += 1

        async def handler_b(event: PlatformEvent) -> None:
            call_count["n"] += 1

        register_event_handler("multi.test", handler_a)
        register_event_handler("multi.test", handler_b)

        await dispatch_event({
            "event_type": "multi.test",
            "company_id": "c",
            "payload": {},
            "source_api": "test",
        })
        assert call_count["n"] == 2

    @pytest.mark.asyncio
    async def test_handler_failure_does_not_stop_others(self):
        """Falha em um handler não impede execução dos demais."""
        results = []

        async def failing_handler(event: PlatformEvent) -> None:
            raise RuntimeError("Handler intencional com erro")

        async def ok_handler(event: PlatformEvent) -> None:
            results.append("ok")

        register_event_handler("fault.test", failing_handler)
        register_event_handler("fault.test", ok_handler)

        # Não deve propagar exceção
        await dispatch_event({
            "event_type": "fault.test",
            "company_id": "c",
            "payload": {},
            "source_api": "test",
        })
        assert results == ["ok"]

    def test_get_registered_handlers_returns_copy(self):
        """get_registered_handlers retorna cópia do registry."""
        async def h(event): pass
        register_event_handler("inspect.test", h)

        registry = get_registered_handlers()
        assert "inspect.test" in registry
        assert len(registry["inspect.test"]) == 1

        # Modificar o retorno não afeta o registry interno
        registry["inspect.test"].clear()
        assert len(get_registered_handlers()["inspect.test"]) == 1


class TestPublishPlatformEvent:
    @pytest.mark.asyncio
    async def test_publish_event_graceful_on_rabbitmq_unavailable(self):
        """RabbitMQ indisponível → retorna False sem lançar exceção."""
        event = JobPublishedEvent(
            company_id="company-rmq-down",
            payload={"job_id": "job-001"},
        )

        # publish_to_exchange é importado localmente dentro de publish_platform_event,
        # então patchamos no módulo origem (rabbitmq_producer).
        with patch(
            "app.shared.messaging.rabbitmq_producer.publish_to_exchange",
            side_effect=ConnectionError("RabbitMQ connection refused"),
        ):
            result = await publish_platform_event(event)

        assert result is False, "Deve retornar False quando RabbitMQ está indisponível"

    @pytest.mark.asyncio
    async def test_publish_event_returns_true_on_success(self):
        """Publicação bem-sucedida retorna True."""
        event = JobPublishedEvent(
            company_id="company-ok",
            payload={"job_id": "job-002"},
        )

        mock_publish = AsyncMock()
        with patch(
            "app.shared.messaging.rabbitmq_producer.publish_to_exchange",
            mock_publish,
        ):
            result = await publish_platform_event(event)

        assert result is True
        mock_publish.assert_called_once_with(
            exchange="platform.events",
            routing_key="vagas.job.published",
            message=event.model_dump(mode="json"),
        )

    @pytest.mark.asyncio
    async def test_publish_event_company_id_in_payload(self):
        """company_id está presente no payload publicado."""
        company_id = "tenant-abc-123"
        event = CandidateMovedEvent(
            company_id=company_id,
            payload={"candidate_id": "cand-x", "from_stage": "a", "to_stage": "b"},
        )

        captured = {}

        async def capture_publish(exchange, routing_key, message):
            captured["message"] = message

        with patch(
            "app.shared.messaging.rabbitmq_producer.publish_to_exchange",
            side_effect=capture_publish,
        ):
            await publish_platform_event(event)

        assert captured["message"]["company_id"] == company_id
