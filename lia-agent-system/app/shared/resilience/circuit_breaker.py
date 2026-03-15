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
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Any, Optional, Dict
import asyncio
import time
import logging
import functools
from functools import wraps

logger = logging.getLogger(__name__)

try:
    from app.observability.metrics import circuit_breaker_state as _cb_state_metric
    _METRICS_AVAILABLE = True
except ImportError:
    _METRICS_AVAILABLE = False

_CB_STATE_VALUES = {"closed": 0, "half_open": 1, "open": 2}


async def _notify_circuit_open(service_name: str) -> None:
    """Notifica Bell + Teams quando circuit breaker abre. Redis dedup: 1 alerta/circuit/hora."""
    try:
        from app.core.database import AsyncSessionLocal
        import time  # noqa: F401 — usado implicitamente

        # Redis dedup: evitar flood de alertas
        try:
            import redis.asyncio as _aioredis
            from lia_config.config import settings as _settings
            _redis = _aioredis.from_url(_settings.REDIS_URL, decode_responses=True)  # síncrono
            dedup_key = f"cb_alert:{service_name}"
            if await _redis.get(dedup_key):
                await _redis.aclose()
                return  # Já notificado na última hora
            await _redis.setex(dedup_key, 3600, "1")  # TTL 1 hora
            await _redis.aclose()
        except Exception:
            pass  # Segue sem dedup se Redis indisponível

        # Enviar notificação
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
    except Exception as _e:
        logger.debug("[CircuitBreaker] Notification failed (non-blocking): %s", _e)


class CircuitState(str, Enum):
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
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None


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
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
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
                logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN")
        return self._state
    
    @property
    def failure_count(self) -> int:
        return self._failure_count
    
    @property
    def success_count(self) -> int:
        return self._success_count
    
    @property
    def last_failure_time(self) -> Optional[float]:
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
            
        except asyncio.TimeoutError:
            logger.error(f"Circuit breaker '{self.name}': Request timed out after {self.config.timeout}s")
            await self.record_failure()
            raise
            
        except Exception as e:
            if isinstance(e, self.config.exclude_exceptions):
                await self.record_success()
                raise
            
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
                logger.debug(f"Circuit breaker '{self.name}': Failure count {self._failure_count}/{self.config.failure_threshold}")
                
                if self._failure_count >= self.config.failure_threshold:
                    self._transition_to_open()
    
    def _transition_to_open(self):
        """Transition to OPEN state."""
        self._state = CircuitState.OPEN
        self._last_state_change = time.time()
        self._success_count = 0
        self._stats.state_changes += 1
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
        if _METRICS_AVAILABLE:
            _cb_state_metric.labels(service=self.name).set(_CB_STATE_VALUES["open"])

    def _transition_to_closed(self):
        """Transition to CLOSED state."""
        self._state = CircuitState.CLOSED
        self._last_state_change = time.time()
        self._failure_count = 0
        self._success_count = 0
        self._stats.state_changes += 1
        logger.info(f"Circuit breaker '{self.name}' is now CLOSED")
        if _METRICS_AVAILABLE:
            _cb_state_metric.labels(service=self.name).set(_CB_STATE_VALUES["closed"])
    
    def reset(self):
        """Manually reset the circuit breaker to CLOSED state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._last_state_change = time.time()
        logger.info(f"Circuit breaker '{self.name}' manually reset to CLOSED")
    
    def get_stats(self) -> Dict:
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

STACKONE_CIRCUIT = CircuitBreaker(
    "stackone",
    CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=45.0,
        success_threshold=2,
        timeout=30.0,
    )
)

SENDGRID_CIRCUIT = CircuitBreaker(
    "sendgrid",
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

ALL_CIRCUITS: Dict[str, CircuitBreaker] = {
    "anthropic": ANTHROPIC_CIRCUIT,
    "openai": OPENAI_CIRCUIT,
    "gemini": GEMINI_CIRCUIT,
    "pearch": PEARCH_CIRCUIT,
    "workos": WORKOS_CIRCUIT,
    "merge": MERGE_CIRCUIT,
    "google_calendar": GOOGLE_CALENDAR_CIRCUIT,
    "gupy": GUPY_CIRCUIT,
    "pandape": PANDAPE_CIRCUIT,
    "stackone": STACKONE_CIRCUIT,
    "sendgrid": SENDGRID_CIRCUIT,
    "resend": RESEND_CIRCUIT,
    "iugu": IUGU_CIRCUIT,
    "vindi": VINDI_CIRCUIT,
}


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


def get_all_circuit_stats() -> Dict[str, Dict]:
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


_circuits: Dict[str, CircuitBreakerState] = {}


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
    fallback: Optional[Callable] = None,
):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            cb = _get_circuit(service_name, failure_threshold, recovery_timeout, half_open_max_calls)

            if not _should_allow_call(cb):
                if fallback:
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


def get_circuit_status(service_name: str) -> Optional[Dict[str, Any]]:
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


def get_all_circuits_status() -> Dict[str, Any]:
    return {name: get_circuit_status(name) for name in _circuits}


def reset_circuit(service_name: str) -> None:
    if service_name in _circuits:
        _circuits[service_name].state = CircuitState.CLOSED
        _circuits[service_name].failure_count = 0
        logger.info(f"[CIRCUIT-BREAKER] '{service_name}' manually reset to CLOSED")
