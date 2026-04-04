"""
Testes E2E — Dead Letter Queue (DLQ) retry e requeue.

Valida o comportamento do DLQService para tasks Celery com falha:

Cenários cobertos:
1. push_failure → persiste entrada na DLQ com metadados corretos
2. list_entries → retorna entradas da DLQ para uma fila
3. queue_size → retorna tamanho correto da fila
4. requeue → re-enfileira task da DLQ na fila original
5. clear → limpa todas as entradas de uma fila
6. PII masking em kwargs antes de persistir
7. summary → retorna resumo de todas as filas com entradas
8. DLQ fail-safe: Redis indisponível não quebra o sistema
9. _notify_if_critical: notificação para tasks críticas

Camada: E2E com mocks Redis (sem Redis real).
"""
import pytest
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_dlq_service_with_mock_redis(
    lpush_response=1,
    lrange_response=None,
    llen_response=0,
    smembers_response=None,
    redis_available=True,
):
    """Cria DLQService com Redis mockado."""
    from app.shared.resilience.dlq_service import DLQService

    service = DLQService()

    if not redis_available:
        async def _get_none():
            return None

        with patch("app.shared.resilience.dlq_service._get_redis", return_value=None):
            return service, None

    mock_pipe = MagicMock()
    mock_pipe.execute = AsyncMock(return_value=[None, None, None, None])

    mock_redis = MagicMock()
    mock_redis.__aenter__ = AsyncMock(return_value=mock_redis)
    mock_redis.__aexit__ = AsyncMock(return_value=False)
    mock_redis.lpush = AsyncMock(return_value=lpush_response)
    mock_redis.ltrim = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)
    mock_redis.sadd = AsyncMock(return_value=None)
    mock_redis.srem = AsyncMock(return_value=None)
    mock_redis.llen = AsyncMock(return_value=llen_response)
    mock_redis.lrange = AsyncMock(return_value=lrange_response or [])
    mock_redis.smembers = AsyncMock(return_value=smembers_response or set())
    mock_redis.delete = AsyncMock(return_value=None)
    mock_redis.lrem = AsyncMock(return_value=None)

    return service, mock_redis


def _make_sample_exception() -> RuntimeError:
    return RuntimeError("Simulated task failure")


def _make_sample_entry(
    task_name: str = "drift.run_batch",
    queue: str = "onboarding_low",
    company_id: str = "company-test-001",
) -> dict:
    return {
        "entry_id": str(uuid.uuid4()),
        "task_name": task_name,
        "queue": queue,
        "args": [],
        "kwargs": {"company_id": company_id, "batch_size": 100},
        "exception_type": "RuntimeError",
        "exception_msg": "Simulated task failure",
        "traceback": "",
        "retries": 3,
        "company_id": company_id,
        "failed_at": "2026-04-04T12:00:00+00:00",
    }


# ---------------------------------------------------------------------------
# Seção 1 — push_failure
# ---------------------------------------------------------------------------

class TestDLQPushFailure:

    @pytest.mark.asyncio
    async def test_push_failure_returns_entry_id(self):
        """push_failure deve retornar um entry_id UUID quando Redis está disponível."""
        service, mock_redis = _make_dlq_service_with_mock_redis()

        with patch("app.shared.resilience.dlq_service._get_redis", AsyncMock(return_value=mock_redis)):
            entry_id = await service.push_failure(
                task_name="drift.run_batch",
                queue="onboarding_low",
                args=[],
                kwargs={"company_id": "company-001"},
                exc=_make_sample_exception(),
                retries=3,
                company_id="company-001",
            )

        assert entry_id is not None
        assert isinstance(entry_id, str)
        try:
            uuid.UUID(entry_id)
        except ValueError:
            pytest.fail(f"entry_id não é um UUID válido: {entry_id}")

    @pytest.mark.asyncio
    async def test_push_failure_calls_lpush(self):
        """push_failure deve chamar lpush no Redis para persistir a entrada."""
        service, mock_redis = _make_dlq_service_with_mock_redis()

        with patch("app.shared.resilience.dlq_service._get_redis", AsyncMock(return_value=mock_redis)):
            await service.push_failure(
                task_name="evaluation.score",
                queue="evaluation_normal",
                args=[],
                kwargs={"company_id": "company-001"},
                exc=_make_sample_exception(),
            )

        mock_redis.lpush.assert_called_once()

    @pytest.mark.asyncio
    async def test_push_failure_returns_none_when_redis_unavailable(self):
        """push_failure retorna None quando Redis não está disponível (fail-safe)."""
        service, _ = _make_dlq_service_with_mock_redis()

        with patch("app.shared.resilience.dlq_service._get_redis", AsyncMock(return_value=None)):
            entry_id = await service.push_failure(
                task_name="drift.run_batch",
                queue="onboarding_low",
                args=[],
                kwargs={},
                exc=_make_sample_exception(),
            )

        assert entry_id is None

    @pytest.mark.asyncio
    async def test_push_failure_masks_pii_in_kwargs(self):
        """push_failure deve mascarar campos PII antes de persistir no Redis."""
        service, mock_redis = _make_dlq_service_with_mock_redis()
        captured_data = []

        async def _capture_lpush(key, value):
            captured_data.append(json.loads(value))
            return 1

        mock_redis.lpush = AsyncMock(side_effect=_capture_lpush)

        with patch("app.shared.resilience.dlq_service._get_redis", AsyncMock(return_value=mock_redis)):
            await service.push_failure(
                task_name="candidate.process",
                queue="evaluation_normal",
                args=[],
                kwargs={
                    "company_id": "company-001",
                    "email": "candidato@empresa.com",
                    "password": "senha_secreta_123",
                    "cpf": "123.456.789-00",
                    "resume_text": "Currículo do candidato",
                },
                exc=_make_sample_exception(),
            )

        assert len(captured_data) == 1
        entry = captured_data[0]
        assert entry["kwargs"].get("email") == "***"
        assert entry["kwargs"].get("password") == "***"
        assert entry["kwargs"].get("cpf") == "***"
        assert entry["kwargs"].get("resume_text") == "Currículo do candidato"
        assert entry["kwargs"].get("company_id") == "company-001"

    @pytest.mark.asyncio
    async def test_push_failure_sets_ttl_on_key(self):
        """push_failure deve definir TTL nas chaves Redis (fila + index)."""
        service, mock_redis = _make_dlq_service_with_mock_redis()
        expire_calls = []

        async def _capture_expire(key, ttl):
            expire_calls.append((key, ttl))

        mock_redis.expire = AsyncMock(side_effect=_capture_expire)

        with patch("app.shared.resilience.dlq_service._get_redis", AsyncMock(return_value=mock_redis)):
            await service.push_failure(
                task_name="drift.run_batch",
                queue="onboarding_low",
                args=[],
                kwargs={},
                exc=_make_sample_exception(),
            )

        from app.shared.resilience.dlq_service import DLQ_TTL_SECONDS
        expire_keys = [k for k, _ in expire_calls]
        expire_ttls = [t for _, t in expire_calls]

        assert "dlq:onboarding_low" in expire_keys, (
            f"TTL não definido na chave da fila. Chamadas: {expire_calls}"
        )
        assert all(t == DLQ_TTL_SECONDS for t in expire_ttls), (
            f"TTL incorreto. Esperado {DLQ_TTL_SECONDS}s. Chamadas: {expire_calls}"
        )


# ---------------------------------------------------------------------------
# Seção 2 — list_entries
# ---------------------------------------------------------------------------

class TestDLQListEntries:

    @pytest.mark.asyncio
    async def test_list_entries_returns_parsed_entries(self):
        """list_entries deve retornar entradas parseadas do Redis."""
        sample_entry = _make_sample_entry()
        service, mock_redis = _make_dlq_service_with_mock_redis(
            lrange_response=[json.dumps(sample_entry)]
        )

        with patch("app.shared.resilience.dlq_service._get_redis", AsyncMock(return_value=mock_redis)):
            entries = await service.list_entries("onboarding_low", limit=10)

        assert len(entries) == 1
        assert entries[0]["task_name"] == "drift.run_batch"
        assert entries[0]["queue"] == "onboarding_low"

    @pytest.mark.asyncio
    async def test_list_entries_returns_empty_when_redis_unavailable(self):
        """list_entries retorna lista vazia quando Redis não está disponível."""
        service, _ = _make_dlq_service_with_mock_redis()

        with patch("app.shared.resilience.dlq_service._get_redis", AsyncMock(return_value=None)):
            entries = await service.list_entries("onboarding_low")

        assert entries == []

    @pytest.mark.asyncio
    async def test_list_entries_respects_limit(self):
        """list_entries respeita o parâmetro limit."""
        service, mock_redis = _make_dlq_service_with_mock_redis(lrange_response=[])

        with patch("app.shared.resilience.dlq_service._get_redis", AsyncMock(return_value=mock_redis)):
            await service.list_entries("evaluation_normal", limit=25)

        mock_redis.lrange.assert_called_with("dlq:evaluation_normal", 0, 24)

    @pytest.mark.asyncio
    async def test_list_entries_returns_multiple_entries(self):
        """list_entries retorna múltiplas entradas corretamente."""
        entries = [
            _make_sample_entry(task_name=f"task.{i}")
            for i in range(3)
        ]
        service, mock_redis = _make_dlq_service_with_mock_redis(
            lrange_response=[json.dumps(e) for e in entries]
        )

        with patch("app.shared.resilience.dlq_service._get_redis", AsyncMock(return_value=mock_redis)):
            result = await service.list_entries("onboarding_low", limit=10)

        assert len(result) == 3
        assert result[0]["task_name"] == "task.0"
        assert result[2]["task_name"] == "task.2"


# ---------------------------------------------------------------------------
# Seção 3 — queue_size
# ---------------------------------------------------------------------------

class TestDLQQueueSize:

    @pytest.mark.asyncio
    async def test_queue_size_returns_correct_count(self):
        """queue_size retorna o número correto de entradas."""
        service, mock_redis = _make_dlq_service_with_mock_redis(llen_response=42)

        with patch("app.shared.resilience.dlq_service._get_redis", AsyncMock(return_value=mock_redis)):
            size = await service.queue_size("sourcing_high")

        assert size == 42

    @pytest.mark.asyncio
    async def test_queue_size_returns_zero_when_redis_unavailable(self):
        """queue_size retorna 0 quando Redis não está disponível."""
        service, _ = _make_dlq_service_with_mock_redis()

        with patch("app.shared.resilience.dlq_service._get_redis", AsyncMock(return_value=None)):
            size = await service.queue_size("sourcing_high")

        assert size == 0

    @pytest.mark.asyncio
    async def test_queue_size_zero_for_empty_queue(self):
        """queue_size retorna 0 para fila vazia."""
        service, mock_redis = _make_dlq_service_with_mock_redis(llen_response=0)

        with patch("app.shared.resilience.dlq_service._get_redis", AsyncMock(return_value=mock_redis)):
            size = await service.queue_size("vagas_normal")

        assert size == 0


# ---------------------------------------------------------------------------
# Seção 4 — requeue (retry)
# ---------------------------------------------------------------------------

class TestDLQRequeue:

    @pytest.mark.asyncio
    async def test_requeue_returns_true_on_success(self):
        """requeue retorna True quando task é reenfileirada com sucesso."""
        sample_entry = _make_sample_entry()
        service, mock_redis = _make_dlq_service_with_mock_redis(
            lrange_response=[json.dumps(sample_entry)]
        )

        with patch("app.shared.resilience.dlq_service._get_redis", AsyncMock(return_value=mock_redis)):
            with patch("app.shared.resilience.dlq_service.dlq_service._remove_entry", AsyncMock()):
                with patch("app.core.celery_app.celery_app") as mock_celery:
                    mock_celery.send_task = MagicMock()
                    result = await service.requeue("onboarding_low", sample_entry["entry_id"])

        assert result is True

    @pytest.mark.asyncio
    async def test_requeue_returns_false_when_entry_not_found(self):
        """requeue retorna False quando entry_id não encontrado na DLQ."""
        service, mock_redis = _make_dlq_service_with_mock_redis(lrange_response=[])

        with patch("app.shared.resilience.dlq_service._get_redis", AsyncMock(return_value=mock_redis)):
            result = await service.requeue("onboarding_low", str(uuid.uuid4()))

        assert result is False

    @pytest.mark.asyncio
    async def test_requeue_calls_celery_send_task(self):
        """requeue deve chamar celery_app.send_task com os dados da task."""
        sample_entry = _make_sample_entry(task_name="drift.run_batch", queue="onboarding_low")
        service, mock_redis = _make_dlq_service_with_mock_redis(
            lrange_response=[json.dumps(sample_entry)]
        )

        with patch("app.shared.resilience.dlq_service._get_redis", AsyncMock(return_value=mock_redis)):
            with patch("app.shared.resilience.dlq_service.dlq_service._remove_entry", AsyncMock()):
                with patch("app.core.celery_app.celery_app") as mock_celery:
                    mock_celery.send_task = MagicMock()
                    await service.requeue("onboarding_low", sample_entry["entry_id"])

                    mock_celery.send_task.assert_called_once_with(
                        "drift.run_batch",
                        args=[],
                        kwargs=sample_entry["kwargs"],
                        queue="onboarding_low",
                    )


# ---------------------------------------------------------------------------
# Seção 5 — clear
# ---------------------------------------------------------------------------

class TestDLQClear:

    @pytest.mark.asyncio
    async def test_clear_returns_count_of_deleted_entries(self):
        """clear retorna o número de entradas removidas."""
        service, mock_redis = _make_dlq_service_with_mock_redis(llen_response=15)

        with patch("app.shared.resilience.dlq_service._get_redis", AsyncMock(return_value=mock_redis)):
            cleared = await service.clear("evaluation_normal")

        assert cleared == 15

    @pytest.mark.asyncio
    async def test_clear_calls_redis_delete(self):
        """clear deve chamar redis.delete na chave da fila."""
        service, mock_redis = _make_dlq_service_with_mock_redis(llen_response=5)

        with patch("app.shared.resilience.dlq_service._get_redis", AsyncMock(return_value=mock_redis)):
            await service.clear("sourcing_high")

        mock_redis.delete.assert_called_with("dlq:sourcing_high")

    @pytest.mark.asyncio
    async def test_clear_returns_zero_when_redis_unavailable(self):
        """clear retorna 0 quando Redis não está disponível."""
        service, _ = _make_dlq_service_with_mock_redis()

        with patch("app.shared.resilience.dlq_service._get_redis", AsyncMock(return_value=None)):
            cleared = await service.clear("sourcing_high")

        assert cleared == 0


# ---------------------------------------------------------------------------
# Seção 6 — PII masking
# ---------------------------------------------------------------------------

class TestDLQPIIMasking:

    def test_mask_pii_masks_sensitive_keys(self):
        """_mask_pii deve mascarar campos com nomes sensíveis."""
        from app.shared.resilience.dlq_service import DLQService

        kwargs = {
            "company_id": "company-001",
            "candidate_name": "João Silva",
            "email": "joao@example.com",
            "password": "supersecret",
            "cpf": "123.456.789-00",
            "phone": "+5511999999999",
            "regular_field": "valor normal",
        }

        masked = DLQService._mask_pii(kwargs)

        assert masked["email"] == "***"
        assert masked["password"] == "***"
        assert masked["cpf"] == "***"
        assert masked["phone"] == "***"
        assert masked["company_id"] == "company-001"
        assert masked["candidate_name"] == "João Silva"
        assert masked["regular_field"] == "valor normal"

    def test_mask_pii_handles_nested_dicts(self):
        """_mask_pii deve mascarar campos sensíveis em dicts aninhados."""
        from app.shared.resilience.dlq_service import DLQService

        kwargs = {
            "payload": {
                "email": "user@test.com",
                "name": "Usuário",
            },
        }

        masked = DLQService._mask_pii(kwargs)
        assert masked["payload"]["email"] == "***"
        assert masked["payload"]["name"] == "Usuário"

    def test_mask_pii_does_not_modify_non_pii_fields(self):
        """_mask_pii não deve modificar campos que não são PII."""
        from app.shared.resilience.dlq_service import DLQService

        kwargs = {
            "company_id": "company-001",
            "job_id": "job-123",
            "batch_size": 100,
            "active": True,
        }

        masked = DLQService._mask_pii(kwargs)
        assert masked == kwargs


# ---------------------------------------------------------------------------
# Seção 7 — summary
# ---------------------------------------------------------------------------

class TestDLQSummary:

    @pytest.mark.asyncio
    async def test_summary_returns_empty_when_no_queues(self):
        """summary retorna total_entries=0 quando não há filas com entradas."""
        service, mock_redis = _make_dlq_service_with_mock_redis(smembers_response=set())

        with patch("app.shared.resilience.dlq_service._get_redis", AsyncMock(return_value=mock_redis)):
            result = await service.summary()

        assert result["total_entries"] == 0
        assert result["queues"] == {}

    @pytest.mark.asyncio
    async def test_summary_aggregates_queues(self):
        """summary agrega informações de múltiplas filas."""
        service, mock_redis = _make_dlq_service_with_mock_redis(
            smembers_response={"onboarding_low", "evaluation_normal"},
            llen_response=5,
        )

        with patch("app.shared.resilience.dlq_service._get_redis", AsyncMock(return_value=mock_redis)):
            result = await service.summary()

        assert result["total_entries"] == 10
        assert "onboarding_low" in result["queues"]
        assert "evaluation_normal" in result["queues"]
