"""
Circuit Breaker pattern for external API resilience.

Prevents cascading failures by tracking API call failures and temporarily
blocking calls to failing services.

States:
- CLOSED: Normal operation, calls pass through
- OPEN: Service is failing, calls blocked with fallback
- HALF_OPEN: Testing if service recovered, limited calls allowed

Usage (functional decorator):
    @circuit_breaker("anthropic", failure_threshold=5, recovery_timeout=60)
    async def call_anthropic(prompt: str) -> str:
        ...

Usage (class-based):
    circuit = CircuitBreaker("anthropic", CircuitBreakerConfig(...))
    result = await circuit.call(my_func, arg1, arg2)
"""
import asyncio
import functools
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, StrEnum
from functools import wraps
from typing import Any


logger = logging.getLogger(__name__)

# Prometheus gauge canonical pattern (vide wizard_session_service.py:42-62).
# Idempotente entre reimports + fail-open se prometheus indisponível.
# Estado encoded em float: 0=closed, 1=half_open, 2=open (vide _CB_STATE_VALUES).
try:  # pragma: no cover — exercitado via integração
    from prometheus_client import Gauge as _PromGauge  # type: ignore
    from prometheus_client import REGISTRY as _PROM_REGISTRY  # type: ignore

    _existing = getattr(_PROM_REGISTRY, "_names_to_collectors", {}).get(
        "lia_circuit_breaker_state"
    )
    if _existing is not None:
        _cb_state_metric = _existing
    else:
        _cb_state_metric = _PromGauge(
            "lia_circuit_breaker_state",
            "Circuit breaker state per service: 0=closed, 1=half_open, 2=open.",
            labelnames=("service",),
        )
except Exception:  # pragma: no cover — fail-OPEN se prometheus indisponível
    _cb_state_metric = None

_CB_STATE_VALUES = {"closed": 0, "half_open": 1, "open": 2}


async def _notify_circuit_open(service_name: str) -> None:
    """Notifica Bell + Teams quando circuit breaker abre. Redis dedup: 1 alerta/circuit/hora."""
    try:
        import time  # noqa: F401 — usado implicitamente

        from app.core.database import AsyncSessionLocal

        # Redis dedup: evitar flood de alertas
        try:
            import redis.asyncio as _aioredis
            from lia_config.config import settings as _settings
            _redis = _aioredis.from_url(_settings.REDIS_URL, decode_responses=True, socket_connect_timeout=5, socket_timeout=5)  # síncrono
            dedup_key = f"cb_alert:{service_name}"
            if await _redis.get(dedup_key):
                await _redis.aclose()
                return  # Já notificado na última hora
            await _redis.setex(dedup_key, 3600, "1")  # TTL 1 hora
            await _redis.aclose()
        except Exception:
            pass  # Segue sem dedup se Redis indisponível

        # Enviar notificação com timeout (evita hang se DB indisponível)
        async def _do_notify() -> None:
            async with AsyncSessionLocal() as db:
                from app.services.notification_service import notification_service
                await notification_service.send_system_alert(
                    db=db,
                    title=f"⚡ Circuit Breaker ABERTO: {service_name}",
                    message=(
                        f"O circuit breaker para '{service_name}' foi aberto após múltiplas falhas. "
                        f"Chamadas estão sendo rejeitadas automaticamente. "
                        f"O circuit tentará recuperação em {30}s."
                    ),
                    severity="warning",
                    channels=["bell", "teams"],
                    metadata={"circuit_name": service_name, "event": "circuit_open"},
                )

        try:
            await asyncio.wait_for(_do_notify(), timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning(
                "[CircuitBreaker] Notification DB call timed out for %s (non-blocking)",
                service_name,
            )
    except Exception as _e:
        logger.debug("[CircuitBreaker] Notification failed (non-blocking): %s", _e)


class CircuitState(StrEnum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    failure_threshold: int = 5       # Number of failures before opening
    recovery_timeout: float = 30.0   # Seconds before trying again (half-open)
    success_threshold: int = 2       # Number of successes to close from half-open
    timeout: float = 10.0            # Request timeout in seconds
    exclude_exceptions: tuple = ()   # Exceptions that should not count as failures


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    state_changes: int = 0
    last_failure_time: float | None = None
    last_success_time: float | None = None


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open and rejects a request."""
    def __init__(self, name: str, retry_after: float):
        self.name = name
        self.retry_after = retry_after
        super().__init__(f"Circuit breaker '{name}' is open. Retry after {retry_after:.1f} seconds.")


class CircuitBreaker:
    """
    Circuit breaker for protecting external API calls.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service is failing, reject all requests immediately
    - HALF_OPEN: Testing if service recovered, allow limited requests
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig | None = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None
        self._last_state_change: float = time.time()
        self._lock = asyncio.Lock()
        self._stats = CircuitBreakerStats()
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state, checking for automatic transitions."""
        if self._state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._state = CircuitState.HALF_OPEN
                self._last_state_change = time.time()
                self._stats.state_changes += 1
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN")
        return self._state

    @property
    def is_open(self) -> bool:
        """True quando o circuit esta OPEN (rejeita chamadas)."""
        return self.state == CircuitState.OPEN

    @property
    def failure_count(self) -> int:
        return self._failure_count
    
    @property
    def success_count(self) -> int:
        return self._success_count
    
    @property
    def last_failure_time(self) -> float | None:
        return self._last_failure_time
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self._last_failure_time is None:
            return True
        return (time.time() - self._last_failure_time) >= self.config.recovery_timeout
    
    def _get_retry_after(self) -> float:
        """Calculate seconds until circuit might close."""
        if self._last_failure_time is None:
            return 0
        elapsed = time.time() - self._last_failure_time
        return max(0, self.config.recovery_timeout - elapsed)
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with circuit breaker protection.
        
        Args:
            func: Async function to call
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Result of the function call
            
        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Any exception from the wrapped function
        """
        async with self._lock:
            current_state = self.state
            self._stats.total_calls += 1
            
            if current_state == CircuitState.OPEN:
                self._stats.rejected_calls += 1
                retry_after = self._get_retry_after()
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.warning(f"Circuit breaker '{self.name}' is OPEN. Rejecting request.")
                raise CircuitBreakerError(self.name, retry_after)
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=self.config.timeout
                )
            else:
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, lambda: func(*args, **kwargs)),
                    timeout=self.config.timeout
                )
            
            await self.record_success()
            return result
            
        except TimeoutError:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.error(f"Circuit breaker '{self.name}': Request timed out after {self.config.timeout}s")
            await self.record_failure()
            raise
            
        except Exception as e:
            if isinstance(e, self.config.exclude_exceptions):
                await self.record_success()
                raise
            
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.error(f"Circuit breaker '{self.name}': Request failed with {type(e).__name__}: {e}")
            await self.record_failure()
            raise
    
    async def record_success(self):
        """Record a successful call."""
        async with self._lock:
            self._stats.successful_calls += 1
            self._stats.last_success_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.debug(f"Circuit breaker '{self.name}': Success in HALF_OPEN ({self._success_count}/{self.config.success_threshold})")
                
                if self._success_count >= self.config.success_threshold:
                    self._transition_to_closed()
            elif self._state == CircuitState.CLOSED:
                self._failure_count = max(0, self._failure_count - 1)
    
    async def record_failure(self):
        """Record a failed call."""
        async with self._lock:
            self._stats.failed_calls += 1
            self._last_failure_time = time.time()
            self._stats.last_failure_time = self._last_failure_time
            
            if self._state == CircuitState.HALF_OPEN:
                self._transition_to_open()
            elif self._state == CircuitState.CLOSED:
                self._failure_count += 1
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.debug(f"Circuit breaker '{self.name}': Failure count {self._failure_count}/{self.config.failure_threshold}")
                
                if self._failure_count >= self.config.failure_threshold:
                    self._transition_to_open()
    
    def _transition_to_open(self):
        """Transition to OPEN state."""
        self._state = CircuitState.OPEN
        self._last_state_change = time.time()
        self._success_count = 0
        self._stats.state_changes += 1
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.warning(f"Circuit breaker '{self.name}' is now OPEN")
        # COMP-3: Notificação quando circuit abre (Bell + Teams, Redis dedup 1h/circuit)
        try:
            import asyncio as _asyncio
            _loop = None
            try:
                _loop = _asyncio.get_running_loop()
            except RuntimeError:
                pass
            if _loop and _loop.is_running():
                _loop.create_task(_notify_circuit_open(self.name))
        except Exception:
            pass
        if _cb_state_metric is not None:
            _cb_state_metric.labels(service=self.name).set(_CB_STATE_VALUES["open"])

    def _transition_to_closed(self):
        """Transition to CLOSED state."""
        self._state = CircuitState.CLOSED
        self._last_state_change = time.time()
        self._failure_count = 0
        self._success_count = 0
        self._stats.state_changes += 1
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Circuit breaker '{self.name}' is now CLOSED")
        if _cb_state_metric is not None:
            _cb_state_metric.labels(service=self.name).set(_CB_STATE_VALUES["closed"])
    
    def reset(self):
        """Manually reset the circuit breaker to CLOSED state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._last_state_change = time.time()
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Circuit breaker '{self.name}' manually reset to CLOSED")
    
    def get_stats(self) -> dict:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout,
            },
            "stats": {
                "total_calls": self._stats.total_calls,
                "successful_calls": self._stats.successful_calls,
                "failed_calls": self._stats.failed_calls,
                "rejected_calls": self._stats.rejected_calls,
                "state_changes": self._stats.state_changes,
                "last_failure_time": self._stats.last_failure_time,
                "last_success_time": self._stats.last_success_time,
            },
            "retry_after": self._get_retry_after() if self.state == CircuitState.OPEN else None,
        }


ANTHROPIC_CIRCUIT = CircuitBreaker(
    "anthropic",
    CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=30.0,
        success_threshold=2,
        timeout=60.0,
    )
)

OPENAI_CIRCUIT = CircuitBreaker(
    "openai",
    CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=30.0,
        success_threshold=2,
        timeout=60.0,
    )
)

DEEPSEEK_CIRCUIT = CircuitBreaker(
    "deepseek",
    CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=30.0,
        success_threshold=2,
        timeout=60.0,
    )
)

GEMINI_CIRCUIT = CircuitBreaker(
    "gemini",
    CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=30.0,
        success_threshold=2,
        timeout=60.0,
    )
)

PEARCH_CIRCUIT = CircuitBreaker(
    "pearch",
    CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=60.0,
        success_threshold=2,
        timeout=30.0,
    )
)

APIFY_CIRCUIT = CircuitBreaker(
    "apify",
    CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=60.0,
        success_threshold=2,
        timeout=30.0,
    )
)

APIFY_SEARCH_CIRCUIT = CircuitBreaker(
    "apify_search",
    CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=120.0,
        success_threshold=2,
        timeout=300.0,
    )
)

WORKOS_CIRCUIT = CircuitBreaker(
    "workos",
    CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=30.0,
        success_threshold=2,
        timeout=15.0,
    )
)

MERGE_CIRCUIT = CircuitBreaker(
    "merge",
    CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=45.0,
        success_threshold=2,
        timeout=30.0,
    )
)

GOOGLE_CALENDAR_CIRCUIT = CircuitBreaker(
    "google_calendar",
    CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=60.0,
        success_threshold=2,
        timeout=30.0,
    )
)

GUPY_CIRCUIT = CircuitBreaker(
    "gupy",
    CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=45.0,
        success_threshold=2,
        timeout=30.0,
    )
)

PANDAPE_CIRCUIT = CircuitBreaker(
    "pandape",
    CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=45.0,
        success_threshold=2,
        timeout=30.0,
    )
)

MAILGUN_CIRCUIT = CircuitBreaker(
    "mailgun",
    CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=30.0,
        success_threshold=2,
        timeout=30.0,
    )
)

RESEND_CIRCUIT = CircuitBreaker(
    "resend",
    CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=30.0,
        success_threshold=2,
        timeout=30.0,
    )
)

IUGU_CIRCUIT = CircuitBreaker(
    "iugu",
    CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=60.0,
        success_threshold=2,
        timeout=30.0,
    )
)

VINDI_CIRCUIT = CircuitBreaker(
    "vindi",
    CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=60.0,
        success_threshold=2,
        timeout=30.0,
    )
)

TWILIO_VOICE_CIRCUIT = CircuitBreaker(
    "twilio_voice",
    CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=60.0,
        success_threshold=2,
        timeout=30.0,
    )
)

GEMINI_LIVE_CIRCUIT = CircuitBreaker(
    "gemini_live",
    CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=30.0,
        success_threshold=2,
        timeout=60.0,
    )
)

DEEPGRAM_CIRCUIT = CircuitBreaker(
    "deepgram",
    CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=30.0,
        success_threshold=2,
        timeout=30.0,
    )
)

OPENMIC_CIRCUIT = CircuitBreaker(
    "openmic",
    CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=60.0,
        success_threshold=2,
        timeout=30.0,
    )
)

RAILS_CIRCUIT = CircuitBreaker(
    "rails_api",
    CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=30.0,
        success_threshold=2,
        timeout=15.0,
    )
)

ALL_CIRCUITS: dict[str, CircuitBreaker] = {
    "anthropic": ANTHROPIC_CIRCUIT,
    "openai": OPENAI_CIRCUIT,
        "deepseek": DEEPSEEK_CIRCUIT,
        "deepseek": DEEPSEEK_CIRCUIT,
    "gemini": GEMINI_CIRCUIT,
    "pearch": PEARCH_CIRCUIT,
    "apify": APIFY_CIRCUIT,
    "apify_search": APIFY_SEARCH_CIRCUIT,
    "workos": WORKOS_CIRCUIT,
    "merge": MERGE_CIRCUIT,
    "google_calendar": GOOGLE_CALENDAR_CIRCUIT,
    "gupy": GUPY_CIRCUIT,
    "pandape": PANDAPE_CIRCUIT,
    "mailgun": MAILGUN_CIRCUIT,
    "resend": RESEND_CIRCUIT,
    "iugu": IUGU_CIRCUIT,
    "vindi": VINDI_CIRCUIT,
    "twilio_voice": TWILIO_VOICE_CIRCUIT,
    "gemini_live": GEMINI_LIVE_CIRCUIT,
    "deepgram": DEEPGRAM_CIRCUIT,
    "openmic": OPENMIC_CIRCUIT,
    "rails_api": RAILS_CIRCUIT,
}


# F1-03: SLOs documentados por serviço — usados no admin endpoint e para error budget tracking
CIRCUIT_BREAKER_SLOS: dict[str, dict[str, Any]] = {
    "anthropic": {
        "availability_target": 0.999,   # 99.9% → ~43 min downtime/mês
        "latency_p95_ms": 8000,
        "error_budget_pct": 0.1,
        "tier": "critical",
        "description": "LLM primário — Claude (Anthropic)",
    },
    "openai": {
        "availability_target": 0.999,
        "latency_p95_ms": 10000,
        "error_budget_pct": 0.1,
        "tier": "critical",
        "description": "LLM alternativo — OpenAI GPT",
    },
    "gemini": {
        "availability_target": 0.995,
        "latency_p95_ms": 15000,
        "error_budget_pct": 0.5,
        "tier": "high",
        "description": "LLM multimodal — Google Gemini",
    },
    "pearch": {
        "availability_target": 0.99,
        "latency_p95_ms": 5000,
        "error_budget_pct": 1.0,
        "tier": "high",
        "description": "Busca de candidatos — Pearch AI (190M+ perfis)",
    },
    "apify": {
        "availability_target": 0.99,
        "latency_p95_ms": 120000,
        "error_budget_pct": 1.0,
        "tier": "medium",
        "description": "Enriquecimento de candidatos — Apify LinkedIn scraper",
    },
    "apify_search": {
        "availability_target": 0.95,
        "latency_p95_ms": 180000,
        "error_budget_pct": 5.0,
        "tier": "low",
        "description": "Busca de candidatos fallback — Apify LinkedIn People Search (3-step pipeline)",
    },
    "workos": {
        "availability_target": 0.999,
        "latency_p95_ms": 3000,
        "error_budget_pct": 0.1,
        "tier": "critical",
        "description": "Autenticação SSO/SCIM — WorkOS",
    },
    "merge": {
        "availability_target": 0.99,
        "latency_p95_ms": 5000,
        "error_budget_pct": 1.0,
        "tier": "high",
        "description": "Conector multi-ATS — Merge.dev",
    },
    "google_calendar": {
        "availability_target": 0.995,
        "latency_p95_ms": 3000,
        "error_budget_pct": 0.5,
        "tier": "medium",
        "description": "Agendamento — Google Calendar",
    },
    "gupy": {
        "availability_target": 0.99,
        "latency_p95_ms": 5000,
        "error_budget_pct": 1.0,
        "tier": "high",
        "description": "ATS — Gupy",
    },
    "pandape": {
        "availability_target": 0.99,
        "latency_p95_ms": 5000,
        "error_budget_pct": 1.0,
        "tier": "high",
        "description": "ATS — Pandapé",
    },
    "mailgun": {
        "availability_target": 0.999,
        "latency_p95_ms": 2000,
        "error_budget_pct": 0.1,
        "tier": "critical",
        "description": "Email transacional primário — Mailgun",
    },
    "resend": {
        "availability_target": 0.999,
        "latency_p95_ms": 2000,
        "error_budget_pct": 0.1,
        "tier": "high",
        "description": "Email transacional fallback — Resend",
    },
    "iugu": {
        "availability_target": 0.995,
        "latency_p95_ms": 5000,
        "error_budget_pct": 0.5,
        "tier": "medium",
        "description": "Pagamentos — Iugu",
    },
    "vindi": {
        "availability_target": 0.995,
        "latency_p95_ms": 5000,
        "error_budget_pct": 0.5,
        "tier": "medium",
        "description": "Pagamentos recorrentes — Vindi",
    },
    "twilio_voice": {
        "availability_target": 0.99,
        "latency_p95_ms": 5000,
        "error_budget_pct": 1.0,
        "tier": "high",
        "description": "Screening por voz — Twilio Programmable Voice",
    },
    "gemini_live": {
        "availability_target": 0.999,
        "latency_p95_ms": 500,
        "error_budget_pct": 0.5,
        "tier": "critical",
        "description": "Screening por voz — Gemini Live Audio (VoIP)",
    },
    "deepgram": {
        "availability_target": 0.999,
        "latency_p95_ms": 5000,
        "error_budget_pct": 0.1,
        "tier": "high",
        "description": "Transcrição de voz STT — Deepgram Nova-2",
    },
    "openmic": {
        "availability_target": 0.99,
        "latency_p95_ms": 10000,
        "error_budget_pct": 1.0,
        "tier": "high",
        "description": "Triagem automatizada por voz — OpenMic.ai",
    },
    "rails_api": {
        "availability_target": 0.999,
        "latency_p95_ms": 500,
        "error_budget_pct": 0.1,
        "tier": "critical",
        "description": "ATS core — WeDOTalent Rails API (candidatos, vagas, aplicações)",
    },
}

# F1-03: respostas de modo degradado — retornadas quando o circuit está OPEN
# e nenhum fallback específico está disponível
DEGRADED_MODE_RESPONSES: dict[str, str] = {
    "anthropic": (
        "A assistente LIA está temporariamente indisponível. "
        "O serviço de IA principal (Anthropic) está com instabilidades. "
        "Tente novamente em alguns minutos ou contate o suporte."
    ),
    "openai": (
        "O serviço de IA alternativo está temporariamente indisponível. "
        "Tente novamente em instantes."
    ),
    "gemini": (
        "A análise multimodal está temporariamente indisponível. "
        "Tente novamente em instantes."
    ),
    "pearch": (
        "A busca de candidatos externos está temporariamente indisponível. "
        "Você pode buscar na base interna de candidatos enquanto isso."
    ),
    "apify": (
        "O enriquecimento de perfis via LinkedIn está temporariamente indisponível. "
        "Os dados já disponíveis na base continuam acessíveis."
    ),
    "apify_search": (
        "A busca de candidatos via Apify (fallback) está temporariamente indisponível. "
        "Tente novamente em alguns minutos ou aguarde a recuperação do serviço principal (Pearch)."
    ),
    "workos": (
        "O serviço de autenticação está com instabilidades. "
        "Tente fazer login novamente ou contate o suporte."
    ),
    "merge": (
        "A sincronização com ATS externo está temporariamente indisponível. "
        "Os dados locais continuam acessíveis."
    ),
    "google_calendar": (
        "O agendamento via Google Calendar está temporariamente indisponível. "
        "Agende manualmente e tente a sincronização mais tarde."
    ),
    "gupy": (
        "A integração com Gupy está temporariamente indisponível. "
        "Os dados locais continuam acessíveis."
    ),
    "pandape": (
        "A integração com Pandapé está temporariamente indisponível. "
        "Os dados locais continuam acessíveis."
    ),
    "mailgun": (
        "O envio de emails está temporariamente indisponível. "
        "As mensagens serão reenviadas assim que o serviço for restaurado."
    ),
    "resend": (
        "O serviço de email alternativo está temporariamente indisponível. "
        "Tente novamente em instantes."
    ),
    "iugu": (
        "O serviço de pagamentos está temporariamente indisponível. "
        "Tente novamente em alguns minutos ou contate o suporte financeiro."
    ),
    "vindi": (
        "O serviço de pagamentos recorrentes está temporariamente indisponível. "
        "Tente novamente em alguns minutos."
    ),
    "twilio_voice": (
        "O screening por voz está temporariamente indisponível. "
        "A triagem será conduzida via chat ou WhatsApp como alternativa."
    ),
    "gemini_live": (
        "O screening por voz via navegador está temporariamente indisponível. "
        "Tentando pipeline alternativo (Twilio). Caso indisponível, use chat ou WhatsApp."
    ),
    "deepgram": (
        "A transcrição de voz está temporariamente indisponível. "
        "Tente novamente em alguns instantes ou use transcrição manual."
    ),
    "openmic": (
        "O screening automatizado por voz está temporariamente indisponível. "
        "A triagem será conduzida via chat ou WhatsApp como alternativa."
    ),
    "rails_api": (
        "O ATS principal está temporariamente indisponível. "
        "Os dados locais em cache continuam acessíveis. "
        "Operações de escrita serão enfileiradas para sincronização assim que o serviço for restaurado."
    ),
}

_DEGRADED_FALLBACK = (
    "Este serviço está temporariamente indisponível. Tente novamente em alguns minutos."
)


def get_degraded_response(service_name: str) -> str:
    """Retorna mensagem de modo degradado para o circuit dado (F1-03)."""
    return DEGRADED_MODE_RESPONSES.get(service_name, _DEGRADED_FALLBACK)


def get_slo(service_name: str) -> dict[str, Any] | None:
    """Retorna a configuração de SLO para o serviço, ou None se não definido (F1-03)."""
    return CIRCUIT_BREAKER_SLOS.get(service_name)


async def with_circuit_breaker(circuit: CircuitBreaker, func: Callable, *args, **kwargs) -> Any:
    """
    Wrapper function to execute a function with circuit breaker protection.
    
    Args:
        circuit: The circuit breaker to use
        func: The function to execute
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Result of the function call
        
    Raises:
        CircuitBreakerError: If circuit is open
        Exception: Any exception from the wrapped function
    """
    return await circuit.call(func, *args, **kwargs)


def circuit_breaker_decorator(circuit: CircuitBreaker):
    """
    Decorator to wrap a function with circuit breaker protection.
    
    Usage:
        @circuit_breaker_decorator(ANTHROPIC_CIRCUIT)
        async def call_anthropic_api():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await circuit.call(func, *args, **kwargs)
        return wrapper
    return decorator


def get_all_circuit_stats() -> dict[str, dict]:
    """Get statistics for all registered circuit breakers."""
    return {name: circuit.get_stats() for name, circuit in ALL_CIRCUITS.items()}


def reset_all_circuits():
    """Reset all circuit breakers to CLOSED state."""
    for circuit in ALL_CIRCUITS.values():
        circuit.reset()
    logger.info("All circuit breakers reset to CLOSED")


@dataclass
class CircuitBreakerState:
    """Lightweight state tracker for functional-style circuit breaker."""
    service_name: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0
    last_success_time: float = 0.0
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    half_open_max_calls: int = 3
    half_open_calls: int = 0
    total_calls: int = 0
    total_failures: int = 0
    total_circuit_opens: int = 0


_circuits: dict[str, CircuitBreakerState] = {}


def _get_circuit(
    service_name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    half_open_max_calls: int = 3,
) -> CircuitBreakerState:
    if service_name not in _circuits:
        _circuits[service_name] = CircuitBreakerState(
            service_name=service_name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            half_open_max_calls=half_open_max_calls,
        )
    return _circuits[service_name]


def _should_allow_call(cb: CircuitBreakerState) -> bool:
    if cb.state == CircuitState.CLOSED:
        return True

    if cb.state == CircuitState.OPEN:
        if time.time() - cb.last_failure_time >= cb.recovery_timeout:
            cb.state = CircuitState.HALF_OPEN
            cb.half_open_calls = 0
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"[CIRCUIT-BREAKER] '{cb.service_name}' → HALF_OPEN (testing recovery)")
            return True
        return False

    if cb.state == CircuitState.HALF_OPEN:
        return cb.half_open_calls < cb.half_open_max_calls

    return False


def _record_success(cb: CircuitBreakerState) -> None:
    cb.success_count += 1
    cb.last_success_time = time.time()
    cb.total_calls += 1

    if cb.state == CircuitState.HALF_OPEN:
        cb.half_open_calls += 1
        if cb.half_open_calls >= cb.half_open_max_calls:
            cb.state = CircuitState.CLOSED
            cb.failure_count = 0
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"[CIRCUIT-BREAKER] '{cb.service_name}' → CLOSED (recovered)")


def _record_failure(cb: CircuitBreakerState, error: Exception) -> None:
    cb.failure_count += 1
    cb.total_failures += 1
    cb.total_calls += 1
    cb.last_failure_time = time.time()

    if cb.state == CircuitState.HALF_OPEN:
        cb.state = CircuitState.OPEN
        cb.total_circuit_opens += 1
        logger.warning(
            f"[CIRCUIT-BREAKER] '{cb.service_name}' → OPEN (failed during recovery): {error}"
        )
        # COMP-3: notificação async (non-blocking)
        try:
            import asyncio as _asyncio
            _loop = None
            try:
                _loop = _asyncio.get_running_loop()
            except RuntimeError:
                pass
            if _loop and _loop.is_running():
                _loop.create_task(_notify_circuit_open(cb.service_name))
        except Exception:
            pass
    elif cb.failure_count >= cb.failure_threshold:
        cb.state = CircuitState.OPEN
        cb.total_circuit_opens += 1
        logger.warning(
            f"[CIRCUIT-BREAKER] '{cb.service_name}' → OPEN "
            f"(failures={cb.failure_count}/{cb.failure_threshold}): {error}"
        )
        # COMP-3: notificação async (non-blocking)
        try:
            import asyncio as _asyncio
            _loop = None
            try:
                _loop = _asyncio.get_running_loop()
            except RuntimeError:
                pass
            if _loop and _loop.is_running():
                _loop.create_task(_notify_circuit_open(cb.service_name))
        except Exception:
            pass


def circuit_breaker(
    service_name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    half_open_max_calls: int = 3,
    fallback: Callable | None = None,
):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            cb = _get_circuit(service_name, failure_threshold, recovery_timeout, half_open_max_calls)

            if not _should_allow_call(cb):
                if fallback:
                    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                    logger.info(f"[CIRCUIT-BREAKER] '{service_name}' using fallback")
                    return await fallback(*args, **kwargs) if callable(fallback) else fallback
                raise CircuitBreakerError(service_name, cb.state)

            try:
                result = await func(*args, **kwargs)
                _record_success(cb)
                return result
            except Exception as e:
                _record_failure(cb, e)
                if fallback and cb.state == CircuitState.OPEN:
                    return await fallback(*args, **kwargs) if callable(fallback) else fallback
                raise

        return wrapper
    return decorator


def get_circuit_status(service_name: str) -> dict[str, Any] | None:
    cb = _circuits.get(service_name)
    if not cb:
        return None
    return {
        "service": cb.service_name,
        "state": cb.state.value,
        "failure_count": cb.failure_count,
        "total_calls": cb.total_calls,
        "total_failures": cb.total_failures,
        "total_circuit_opens": cb.total_circuit_opens,
        "last_failure": cb.last_failure_time,
    }


def get_all_circuits_status() -> dict[str, Any]:
    return {name: get_circuit_status(name) for name in _circuits}


def reset_circuit(service_name: str) -> None:
    if service_name in _circuits:
        _circuits[service_name].state = CircuitState.CLOSED
        _circuits[service_name].failure_count = 0
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"[CIRCUIT-BREAKER] '{service_name}' manually reset to CLOSED")


def validate_llm_circuit_configs() -> dict[str, Any]:
    """Validate that LLM circuit breakers have safe timeout and fallback configuration.

    Called at startup to assert that all LLM circuits (Anthropic, OpenAI, Gemini)
    have appropriate timeouts so they don't block indefinitely and will trigger
    fallback behaviour after the configured threshold.

    Returns:
        dict with validation results per LLM service.
    """
    _LLM_CIRCUITS = {
        "anthropic": ANTHROPIC_CIRCUIT,
        "openai": OPENAI_CIRCUIT,
        "gemini": GEMINI_CIRCUIT,
    }
    _MIN_TIMEOUT = 30.0       # LLM calls must time out in <= 120s; require at least 30s
    _MAX_TIMEOUT = 120.0
    _MIN_THRESHOLD = 3        # Must open after at most 10 failures
    _MAX_THRESHOLD = 10

    results: dict[str, Any] = {}
    all_ok = True
    for name, cb in _LLM_CIRCUITS.items():
        cfg = cb.config
        issues = []
        if not (_MIN_TIMEOUT <= cfg.timeout <= _MAX_TIMEOUT):
            issues.append(f"timeout={cfg.timeout}s outside [{_MIN_TIMEOUT}, {_MAX_TIMEOUT}]s")
        if not (_MIN_THRESHOLD <= cfg.failure_threshold <= _MAX_THRESHOLD):
            issues.append(f"failure_threshold={cfg.failure_threshold} outside [{_MIN_THRESHOLD}, {_MAX_THRESHOLD}]")
        if cfg.recovery_timeout <= 0:
            issues.append(f"recovery_timeout={cfg.recovery_timeout}s must be > 0")
        ok = len(issues) == 0
        if not ok:
            all_ok = False
        results[name] = {
            "ok": ok,
            "timeout_s": cfg.timeout,
            "failure_threshold": cfg.failure_threshold,
            "recovery_timeout_s": cfg.recovery_timeout,
            "success_threshold": cfg.success_threshold,
            "issues": issues,
        }
    results["_all_ok"] = all_ok
    return results


# ---------------------------------------------------------------------------
# Versao SINCRONA do circuit breaker (audit 2026-06-05 P1).
# CircuitBreaker.call e async-only; caminhos sincronos (ex: JdEnrichmentService.
# enrich -> self.llm.invoke) precisavam de circuit_breaker_call + CircuitBreakerOpenError.
# Esses simbolos eram importados de app.shared.services.circuit_breaker (shim ->
# este modulo) mas NUNCA existiram => ImportError => os consumidores caiam em
# `except ImportError: <chamada direta sem circuito>` (dead code). Aqui o produtor
# canonico passa a expor a API que os consumidores esperam.
# ---------------------------------------------------------------------------


class CircuitBreakerOpenError(CircuitBreakerError):
    """Circuito aberto — rejeita request. Subclasse de CircuitBreakerError (compat
    com `except CircuitBreakerError` existente)."""


class _SyncCircuitState:
    __slots__ = ("failures", "opened_at", "config")

    def __init__(self, config: "CircuitBreakerConfig"):
        self.failures = 0
        self.opened_at: float | None = None
        self.config = config


_sync_circuit_registry: dict[str, _SyncCircuitState] = {}


def circuit_breaker_call(
    func,
    *args,
    circuit_key: str = "default",
    config: "CircuitBreakerConfig | None" = None,
    **kwargs,
):
    """Executa ``func`` de forma SINCRONA com protecao de circuit breaker por ``circuit_key``.

    Abre apos ``failure_threshold`` falhas consecutivas; meia-abertura (uma
    tentativa) apos ``recovery_timeout``. Levanta ``CircuitBreakerOpenError``
    quando o circuito esta aberto (sem invocar ``func``). Best-effort (sem lock):
    adequado para resiliencia, nao para invariante de correcao.
    """
    st = _sync_circuit_registry.get(circuit_key)
    if st is None:
        st = _SyncCircuitState(config or CircuitBreakerConfig())
        _sync_circuit_registry[circuit_key] = st

    if st.opened_at is not None:
        elapsed = time.time() - st.opened_at
        if elapsed < st.config.recovery_timeout:
            raise CircuitBreakerOpenError(
                circuit_key, st.config.recovery_timeout - elapsed
            )
        # janela de recovery expirou -> meia-abertura: permite uma tentativa
        st.opened_at = None
        st.failures = 0

    try:
        result = func(*args, **kwargs)
    except Exception:
        st.failures += 1
        if st.failures >= st.config.failure_threshold:
            st.opened_at = time.time()
        raise
    st.failures = 0
    st.opened_at = None
    return result
