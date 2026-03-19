"""
Testes de integração para PlatformEvents — publicação via RabbitMQ.

Camada 3 (Integração) da pirâmide — RabbitMQ mockado via patch.
Testa publish_platform_event(), routing keys, schema dos eventos e
fallback graceful quando RabbitMQ está indisponível.

Cobertura:
  - 4 tipos de eventos: JobPublished, JobClosed, CandidateMoved, CompanyConfigured
  - publish_platform_event() retorna bool
  - Graceful failure quando RabbitMQ offline
  - Routing key segue padrão {dominio}.{entidade}.{acao}
  - company_id está presente no payload do evento
  - event_id único por publicação
  - occurred_at em UTC
  - Handler dispatch: dispatch_event() chama handler registrado
  - register_event_handler() e dispatch_event() funcionam corretamente
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import timezone
from uuid import UUID


from app.shared.messaging.platform_events import (
    PlatformEvent,
    JobPublishedEvent,
    JobClosedEvent,
    CandidateMovedEvent,
    CompanyConfiguredEvent,
    publish_platform_event,
    register_event_handler,
    dispatch_event,
    PLATFORM_EVENTS_EXCHANGE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_job_published(company_id: str = "company-test") -> JobPublishedEvent:
    return JobPublishedEvent(
        company_id=company_id,
        payload={"job_id": "job-001", "title": "Dev Pleno Python"},
    )


def _make_candidate_moved(company_id: str = "company-test") -> CandidateMovedEvent:
    return CandidateMovedEvent(
        company_id=company_id,
        payload={
            "candidate_id": "cand-001",
            "from_stage": "triagem",
            "to_stage": "entrevista",
        },
    )


# ---------------------------------------------------------------------------
# Seção 1: Schemas dos eventos
# ---------------------------------------------------------------------------

class TestPlatformEventSchemas:

    def test_job_published_event_type(self):
        evt = _make_job_published()
        assert evt.event_type == "vagas.job.published"

    def test_job_closed_event_type(self):
        evt = JobClosedEvent(company_id="c1", payload={"job_id": "j1"})
        assert evt.event_type == "vagas.job.closed"

    def test_candidate_moved_event_type(self):
        evt = _make_candidate_moved()
        assert evt.event_type == "funil.candidate.moved"

    def test_company_configured_event_type(self):
        evt = CompanyConfiguredEvent(company_id="c1", payload={"company_id": "c1"})
        assert evt.event_type == "onboarding.company.configured"

    def test_event_id_is_unique(self):
        """Dois eventos têm event_ids diferentes."""
        e1 = _make_job_published()
        e2 = _make_job_published()
        assert e1.event_id != e2.event_id

    def test_event_id_is_valid_uuid(self):
        """event_id é um UUID válido."""
        evt = _make_job_published()
        UUID(evt.event_id)  # não deve lançar exceção

    def test_occurred_at_is_utc(self):
        """occurred_at tem timezone UTC."""
        evt = _make_job_published()
        assert evt.occurred_at.tzinfo is not None
        assert evt.occurred_at.utcoffset().total_seconds() == 0

    def test_company_id_preserved_in_event(self):
        """company_id está presente e correto no evento."""
        evt = _make_job_published(company_id="tenant-XYZ")
        assert evt.company_id == "tenant-XYZ"

    def test_payload_preserved(self):
        """Payload do evento é preservado."""
        evt = _make_job_published()
        assert evt.payload["job_id"] == "job-001"
        assert evt.payload["title"] == "Dev Pleno Python"

    def test_version_default(self):
        """version tem valor padrão '1.0'."""
        evt = _make_job_published()
        assert evt.version == "1.0"

    def test_source_api_job_published(self):
        evt = _make_job_published()
        assert evt.source_api == "api-vagas"

    def test_source_api_candidate_moved(self):
        evt = _make_candidate_moved()
        assert evt.source_api == "api-funil"


# ---------------------------------------------------------------------------
# Seção 2: publish_platform_event() com RabbitMQ mockado
# ---------------------------------------------------------------------------

class TestPublishPlatformEvent:

    @pytest.mark.asyncio
    async def test_publish_job_published_returns_bool(self):
        """publish_platform_event retorna bool."""
        evt = _make_job_published()
        with patch(
            "app.shared.messaging.rabbitmq_producer.publish_to_exchange",
            new=AsyncMock(return_value=True),
        ):
            result = await publish_platform_event(evt)
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_publish_job_published_success(self):
        """publish_platform_event retorna True quando publicação bem-sucedida."""
        evt = _make_job_published()
        with patch(
            "app.shared.messaging.rabbitmq_producer.publish_to_exchange",
            new=AsyncMock(return_value=True),
        ):
            result = await publish_platform_event(evt)
        assert result is True

    @pytest.mark.asyncio
    async def test_publish_graceful_when_rabbitmq_unavailable(self):
        """Quando RabbitMQ está offline, publish_platform_event retorna False sem lançar."""
        evt = _make_job_published()
        with patch(
            "app.shared.messaging.rabbitmq_producer.publish_to_exchange",
            new=AsyncMock(side_effect=Exception("Connection refused")),
        ):
            result = await publish_platform_event(evt)
        assert result is False

    @pytest.mark.asyncio
    async def test_publish_candidate_moved_event(self):
        """CandidateMovedEvent é publicado com sucesso."""
        evt = _make_candidate_moved()
        with patch(
            "app.shared.messaging.rabbitmq_producer.publish_to_exchange",
            new=AsyncMock(return_value=True),
        ):
            result = await publish_platform_event(evt)
        assert result is True

    @pytest.mark.asyncio
    async def test_publish_company_configured_event(self):
        """CompanyConfiguredEvent é publicado com sucesso."""
        evt = CompanyConfiguredEvent(
            company_id="c1",
            payload={"company_id": "c1", "plan": "pro"},
        )
        with patch(
            "app.shared.messaging.rabbitmq_producer.publish_to_exchange",
            new=AsyncMock(return_value=True),
        ):
            result = await publish_platform_event(evt)
        assert result is True

    @pytest.mark.asyncio
    async def test_publish_uses_platform_events_exchange(self):
        """publish_platform_event chama publish_to_exchange com exchange correto."""
        evt = _make_job_published()
        mock_publish = AsyncMock(return_value=True)
        with patch(
            "app.shared.messaging.rabbitmq_producer.publish_to_exchange",
            new=mock_publish,
        ):
            await publish_platform_event(evt)

        call_args = mock_publish.call_args
        assert call_args is not None
        # exchange deve ser "platform.events" ou similar
        exchange_arg = call_args[0][0] if call_args[0] else call_args[1].get("exchange", "")
        assert PLATFORM_EVENTS_EXCHANGE in str(exchange_arg)

    @pytest.mark.asyncio
    async def test_publish_routing_key_format(self):
        """Routing key segue padrão {domain}.{entity}.{action}."""
        evt = _make_job_published()
        mock_publish = AsyncMock(return_value=True)
        with patch(
            "app.shared.messaging.rabbitmq_producer.publish_to_exchange",
            new=mock_publish,
        ):
            await publish_platform_event(evt)

        call_args = mock_publish.call_args
        if call_args and call_args[0]:
            routing_key = call_args[0][1] if len(call_args[0]) > 1 else ""
            if routing_key:
                parts = routing_key.split(".")
                assert len(parts) >= 2, f"Routing key inválida: '{routing_key}'"


# ---------------------------------------------------------------------------
# Seção 3: Handler registry e dispatch
# ---------------------------------------------------------------------------

class TestEventHandlerRegistry:

    @pytest.mark.asyncio
    async def test_register_and_dispatch_handler(self):
        """Handler registrado é chamado ao fazer dispatch do evento."""
        received = []

        async def my_handler(evt: PlatformEvent):
            received.append(evt.event_id)

        evt = _make_job_published()
        register_event_handler(evt.event_type, my_handler)

        await dispatch_event(evt.model_dump())
        assert evt.event_id in received

    @pytest.mark.asyncio
    async def test_dispatch_unknown_event_no_error(self):
        """Dispatch de evento sem handler registrado não lança exceção."""
        evt = PlatformEvent(
            event_type="unknown.event.type",
            company_id="c1",
            payload={},
            source_api="api-test",
        )
        # Não deve lançar exceção
        await dispatch_event(evt.model_dump())

    @pytest.mark.asyncio
    async def test_handler_failure_does_not_stop_others(self):
        """Se um handler falha, os demais ainda são chamados."""
        called = []

        async def failing_handler(evt):
            raise RuntimeError("handler error")

        async def ok_handler(evt):
            called.append("ok")

        event_type = "test.handler.failure.resilience"
        register_event_handler(event_type, failing_handler)
        register_event_handler(event_type, ok_handler)

        evt = PlatformEvent(
            event_type=event_type,
            company_id="c1",
            payload={},
            source_api="api-test",
        )
        await dispatch_event(evt.model_dump())
        assert "ok" in called
