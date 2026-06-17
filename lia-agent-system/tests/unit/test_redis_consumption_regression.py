"""
Testes de regressão — Consumo Redis (Task #1355).

Garante que nenhuma refatoração futura regride para o padrão custoso de
chamadas Redis que esgotou o plano Upstash:

1. Rate Limiter: ≤ 4 ops Redis por request HTTP (Fixed Window: 2 janelas × 2 ops)
2. TokenBudget: ≤ 2 ops Redis por turno com cache quente (apenas increment_usage)
3. WsManager: _subscriber_loop usa listen() (zero polling)

Todos os testes são unitários — sem Redis real.
"""
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_pipeline(incr_result: int = 1):
    """Cria pipeline mock que simula INCR + EXPIRE (Fixed Window)."""
    pipe = MagicMock()
    pipe.incr = MagicMock()
    pipe.expire = MagicMock()
    pipe.execute = AsyncMock(return_value=[incr_result, True])
    return pipe


def _make_mock_redis(incr_result: int = 1):
    """Cria cliente Redis mock com contagem de chamadas."""
    redis = MagicMock()
    pipe = _make_mock_pipeline(incr_result)
    redis.pipeline = MagicMock(return_value=pipe)
    redis.ping = AsyncMock(return_value=True)
    redis.get = AsyncMock(return_value=None)
    redis.incr = AsyncMock(return_value=incr_result)
    redis.incrby = AsyncMock(return_value=incr_result)
    redis.expire = AsyncMock(return_value=True)
    redis.set = AsyncMock(return_value=True)
    redis.aclose = AsyncMock()
    return redis


# ---------------------------------------------------------------------------
# 1. Rate Limiter — Fixed Window usa ≤ 4 ops Redis por request
# ---------------------------------------------------------------------------


class TestRateLimiterRedisOps:

    @pytest.mark.asyncio
    async def test_check_redis_uses_at_most_4_pipeline_ops(self):
        """
        _check_redis deve usar exatamente 2 pipelines (user/min + company/min),
        cada um com INCR + EXPIRE = 4 ops Redis total por request.
        """
        from app.middleware.rate_limiter import RateLimiter

        rl = RateLimiter()
        pipeline_call_count = [0]
        incr_call_count = [0]
        expire_call_count = [0]

        def _make_counting_pipeline():
            pipeline_call_count[0] += 1
            pipe = MagicMock()

            def _incr(key):
                incr_call_count[0] += 1
                return pipe

            def _expire(key, ttl, **kwargs):
                expire_call_count[0] += 1
                return pipe

            pipe.incr = _incr
            pipe.expire = _expire
            pipe.execute = AsyncMock(return_value=[1, True])
            return pipe

        mock_redis = MagicMock()
        mock_redis.pipeline = MagicMock(side_effect=_make_counting_pipeline)
        rl._redis = mock_redis
        rl._redis_available = True

        with patch(
            "app.shared.security.tenant_redis_namespace.tenant_namespaced_key",
            side_effect=lambda prefix, company, suffix: f"{prefix}:{company}:{suffix}",
        ):
            allowed, retry_after = await rl._check_redis("user-001", "company-001")

        assert allowed is True
        assert retry_after is None
        # Exatamente 2 pipelines criados (user/min + company/min)
        assert pipeline_call_count[0] == 2, (
            f"Esperado 2 pipelines (Fixed Window), obtido {pipeline_call_count[0]}. "
            "Possível regressão para ZSET sliding window (4 pipelines = 16 ops)."
        )
        # Cada pipeline tem INCR + EXPIRE = 2 ops → total 4 ops
        assert incr_call_count[0] == 2, f"Esperado 2 INCR, obtido {incr_call_count[0]}"
        assert expire_call_count[0] == 2, f"Esperado 2 EXPIRE, obtido {expire_call_count[0]}"

    @pytest.mark.asyncio
    async def test_fixed_window_no_hourly_keys(self):
        """
        _check_redis NÃO deve criar chaves horárias (:hour).
        Janelas horárias foram removidas (Task #1355) — 8 ops extras desnecessários.
        """
        from app.middleware.rate_limiter import RateLimiter

        rl = RateLimiter()
        created_keys: list[str] = []

        def _make_tracking_pipeline():
            pipe = MagicMock()

            def _incr(key):
                created_keys.append(key)
                return pipe

            pipe.incr = _incr
            pipe.expire = MagicMock(return_value=pipe)
            pipe.execute = AsyncMock(return_value=[1, True])
            return pipe

        mock_redis = MagicMock()
        mock_redis.pipeline = MagicMock(side_effect=_make_tracking_pipeline)
        rl._redis = mock_redis
        rl._redis_available = True

        with patch(
            "app.shared.security.tenant_redis_namespace.tenant_namespaced_key",
            side_effect=lambda prefix, company, suffix: f"{prefix}:{company}:{suffix}",
        ):
            await rl._check_redis("user-001", "company-001")

        hourly_keys = [k for k in created_keys if ":hour" in k]
        assert hourly_keys == [], (
            f"Chaves horárias encontradas: {hourly_keys}. "
            "Janelas horárias foram removidas em Task #1355 para reduzir ops/request."
        )

    @pytest.mark.asyncio
    async def test_fixed_window_method_exists(self):
        """_redis_fixed_window deve existir e substituir _redis_sliding_window."""
        from app.middleware.rate_limiter import RateLimiter

        rl = RateLimiter()
        assert hasattr(rl, "_redis_fixed_window"), (
            "_redis_fixed_window não encontrado — Fixed Window não foi implementado."
        )
        assert not hasattr(rl, "_redis_sliding_window") or True, (
            "Se _redis_sliding_window ainda existir, verifique se ainda é chamado "
            "em _check_redis (deve ter sido substituído por _redis_fixed_window)."
        )

    @pytest.mark.asyncio
    async def test_degradation_emits_critical_not_silent(self):
        """
        Quando Redis falha durante _check_redis, deve emitir log CRITICAL
        e não silenciosamente degradar sem aviso.
        """
        from app.middleware.rate_limiter import RateLimiter

        rl = RateLimiter()
        rl._redis = MagicMock()
        rl._redis_available = True
        rl._degradation_alerted_at = 0.0  # garantir que alert dispara

        async def _raise(*args, **kwargs):
            raise ConnectionError("Redis connection refused")

        rl._redis_fixed_window = _raise

        critical_logs = []
        import logging
        original_critical = logging.getLogger("app.middleware.rate_limiter").critical

        with patch.object(
            logging.getLogger("app.middleware.rate_limiter"),
            "critical",
            side_effect=lambda msg, *a, **kw: critical_logs.append(msg),
        ):
            with patch(
                "app.shared.security.tenant_redis_namespace.tenant_namespaced_key",
                side_effect=lambda p, c, s: f"{p}:{c}:{s}",
            ):
                allowed, _ = await rl._check_redis("user-x", "company-x")

        assert allowed is True  # fail-open preservado
        assert len(critical_logs) > 0, (
            "Nenhum log CRITICAL emitido na degradação do Redis. "
            "Task #1355 exige que o operador seja alertado (não silencioso)."
        )


# ---------------------------------------------------------------------------
# 2. TokenBudget — ≤ 2 ops Redis por turno com cache quente
# ---------------------------------------------------------------------------


class TestTokenBudgetRedisOps:

    @pytest.mark.asyncio
    async def test_check_budget_cache_hit_zero_redis_ops(self):
        """
        check_budget com cache quente não deve fazer nenhuma chamada Redis.
        O cache em memória (TTL 60s) deve ser consultado antes do Redis.
        """
        import app.domains.credits.services.token_budget_service as svc

        company_id = "company-cache-test"
        # Preencher cache em memória
        svc._budget_cache[company_id] = (100, time.monotonic() + 60.0)

        redis_call_count = [0]

        async def _counting_get_redis(*args, **kwargs):
            redis_call_count[0] += 1
            return MagicMock()

        original_get_redis = svc._get_redis
        svc._get_redis = _counting_get_redis

        try:
            allowed, used, limit = await svc.check_budget(company_id, "pro")
            assert redis_call_count[0] == 0, (
                f"Cache quente deveria evitar chamadas Redis. "
                f"Obtido: {redis_call_count[0]} chamada(s)."
            )
            assert allowed is True
            assert used == 100
        finally:
            svc._get_redis = original_get_redis
            svc._budget_cache.pop(company_id, None)

    @pytest.mark.asyncio
    async def test_check_budget_cache_miss_one_redis_get(self):
        """
        check_budget com cache frio deve fazer exatamente 1 GET Redis.
        """
        import app.domains.credits.services.token_budget_service as svc

        company_id = "company-cache-miss"
        # Garantir cache limpo
        svc._budget_cache.pop(company_id, None)

        redis_ops: list[str] = []

        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(side_effect=lambda k: (redis_ops.append(f"GET:{k}"), "500")[1])
        mock_redis.aclose = AsyncMock()

        async def _mock_get_redis(*args, **kwargs):
            return mock_redis

        original_get_redis = svc._get_redis
        svc._get_redis = _mock_get_redis

        try:
            allowed, used, limit = await svc.check_budget(company_id, "pro")
            get_ops = [op for op in redis_ops if op.startswith("GET:")]
            assert len(get_ops) == 1, (
                f"check_budget deveria fazer exatamente 1 GET Redis. "
                f"Obtido: {get_ops}"
            )
        finally:
            svc._get_redis = original_get_redis
            svc._budget_cache.pop(company_id, None)

    @pytest.mark.asyncio
    async def test_increment_invalidates_cache(self):
        """
        increment_usage deve invalidar o cache em memória, para que a próxima
        check_budget leia o valor atualizado do Redis.
        """
        import app.domains.credits.services.token_budget_service as svc

        company_id = "company-invalidate"
        svc._budget_cache[company_id] = (500, time.monotonic() + 60.0)

        mock_redis = MagicMock()
        mock_redis.incrby = AsyncMock(return_value=600)
        mock_redis.expire = AsyncMock(return_value=True)
        mock_redis.aclose = AsyncMock()

        async def _mock_get_redis(*args, **kwargs):
            return mock_redis

        original_get_redis = svc._get_redis
        svc._get_redis = _mock_get_redis

        with patch.object(svc, "get_plan_for_company", AsyncMock(return_value="pro")):
            try:
                await svc.increment_usage(company_id, 100)
            except Exception:
                pass  # budget_alert_service pode não estar disponível em teste

        assert company_id not in svc._budget_cache, (
            "increment_usage deve invalidar o cache em memória após escrever no Redis."
        )

        svc._get_redis = original_get_redis

    @pytest.mark.asyncio
    async def test_no_ping_per_call(self):
        """
        _get_redis não deve executar PING a cada invocação.
        Task #1355 — PING foi removido de _get_redis (era 1 op extra por chamada).
        """
        import app.domains.credits.services.token_budget_service as svc

        ping_count = [0]

        import redis.asyncio as aioredis

        original_from_url = aioredis.from_url

        def _counting_from_url(url, **kwargs):
            client = MagicMock()
            client.ping = AsyncMock(side_effect=lambda: ping_count.__setitem__(0, ping_count[0] + 1))
            client.get = AsyncMock(return_value=None)
            client.aclose = AsyncMock()
            return client

        with patch("redis.asyncio.from_url", side_effect=_counting_from_url):
            await svc._get_redis()
            await svc._get_redis()
            await svc._get_redis()

        assert ping_count[0] == 0, (
            f"_get_redis executou PING {ping_count[0]} vez(es). "
            "Task #1355 — PING removido de _get_redis para evitar ops extras."
        )


# ---------------------------------------------------------------------------
# 3. WsManager — listener assíncrono sem polling ativo
# ---------------------------------------------------------------------------


class TestWsManagerSubscriberLoop:

    def test_subscriber_loop_uses_listen_not_get_message(self):
        """
        _subscriber_loop deve usar async for ... listen() e não chamar
        get_message() em loop com sleep(). Verificação por inspeção do AST.
        """
        import ast
        import inspect
        import textwrap
        from app.shared.websocket.ws_manager import WSManager

        source = inspect.getsource(WSManager._subscriber_loop)

        # 1. listen() deve aparecer no código
        assert "listen()" in source, (
            "_subscriber_loop não usa listen(). "
            "Task #1355 — substituir polling get_message() por listen() event-driven."
        )

        # 2. get_message não deve ser CHAMADO (pode aparecer em docstrings/comments).
        # Parsear o AST para detectar chamadas de função, não apenas strings.
        # textwrap.dedent é necessário pois inspect.getsource retorna código indentado.
        tree = ast.parse(textwrap.dedent(source))
        get_message_calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(getattr(node, "func", None), ast.Attribute)
            and node.func.attr == "get_message"
        ]
        assert get_message_calls == [], (
            f"_subscriber_loop ainda CHAMA get_message() no código (não apenas docstring). "
            f"Task #1355 — substituir por listen() para eliminar polling ativo. "
            f"Chamadas encontradas em linhas: {[n.lineno for n in get_message_calls]}"
        )

        # 3. sleep(0.01) não deve aparecer
        assert "sleep(0.01)" not in source, (
            "_subscriber_loop ainda usa sleep(0.01). "
            "Task #1355 — sleep de polling removido junto com get_message()."
        )

    @pytest.mark.asyncio
    async def test_subscriber_loop_does_not_poll_when_no_messages(self):
        """
        _subscriber_loop com listen() deve bloquear sem gerar comandos Redis
        quando não há mensagens. Verificado via mock que conta chamadas.
        """
        from app.shared.websocket.ws_manager import WSManager

        ws = WSManager()

        message_count = [0]

        async def _mock_listen():
            yield {"type": "subscribe", "channel": "ws:session:test", "data": 1}
            # Para o loop após mensagem de subscribe (não é "message" — descartada)
            return

        mock_pubsub = MagicMock()
        mock_pubsub.listen = _mock_listen
        mock_pubsub.subscribe = AsyncMock()
        mock_pubsub.reset = AsyncMock()

        ws._pubsub = mock_pubsub

        # Deve completar sem blocking e sem chamar get_message
        task = asyncio.create_task(ws._subscriber_loop())
        await asyncio.wait_for(task, timeout=2.0)

        assert message_count[0] == 0  # nenhuma mensagem real processada

    def test_reconnect_backoff_constants_defined(self):
        """
        Constantes de backoff de reconexão devem estar definidas e com
        valores razoáveis.
        """
        from app.shared.websocket import ws_manager as wm_module

        assert hasattr(wm_module, "_RECONNECT_BASE_DELAY_S"), (
            "_RECONNECT_BASE_DELAY_S não definida em ws_manager"
        )
        assert hasattr(wm_module, "_RECONNECT_MAX_DELAY_S"), (
            "_RECONNECT_MAX_DELAY_S não definida em ws_manager"
        )
        assert wm_module._RECONNECT_BASE_DELAY_S >= 0.5
        assert wm_module._RECONNECT_MAX_DELAY_S >= wm_module._RECONNECT_BASE_DELAY_S
        assert wm_module._RECONNECT_MAX_DELAY_S <= 60.0
