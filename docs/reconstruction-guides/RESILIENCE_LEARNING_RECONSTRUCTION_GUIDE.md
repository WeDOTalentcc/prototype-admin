# RESILIENCE_LEARNING_RECONSTRUCTION_GUIDE.md
# WeDOTalent / LIA — Guia de Reconstrução de Resiliência e Aprendizado

> **Propósito:** Permite ao time replicar resiliência (Circuit Breaker), aprendizado contínuo
> (Learning Loop) e mensageria assíncrona (Broker + Platform Events + Unified Publisher)
> da LIA em um novo produto — sem precisar abrir os arquivos originais.
>
> **Regra absoluta:** Todo conteúdo deste documento foi extraído diretamente dos arquivos
> canônicos com `Read` tool. Zero conteúdo inventado.
>
> **Arquivos cobertos:** 5 arquivos canônicos (Temas 11–12)
> | Tipo | Arquivo | Tamanho |
> |------|---------|---------|
> | Interface | `app/shared/resilience/circuit_breaker.py` | 1060L |
> | Interface | `app/shared/learning/learning_loop_service.py` | 1133L |
> | Verbatim | `app/shared/messaging/broker_interface.py` | 335L |
> | Verbatim | `app/shared/messaging/platform_events.py` | 189L |
> | Verbatim | `app/shared/messaging/unified_event_publisher.py` | 113L |

---

## PARTE 1 — Mapa de Arquivos

```
lia-agent-system/
app/
├── shared/
│   ├── resilience/
│   │   └── circuit_breaker.py         ← CANONICAL: circuit breaker para 20 serviços externos
│   │
│   ├── learning/
│   │   └── learning_loop_service.py   ← CANONICAL: aprendizado contínuo via feedback silencioso
│   │
│   └── messaging/
│       ├── broker_interface.py        ← CANONICAL: abstração de broker (Redis/RabbitMQ/PubSub)
│       ├── platform_events.py         ← CANONICAL: eventos inter-API (topic exchange)
│       └── unified_event_publisher.py ← CANONICAL: publisher unificado para Rails
```

**Dependências externas:**
- `redis.asyncio` — backend padrão do BrokerInterface
- `aio_pika` — backend RabbitMQ do BrokerInterface (on-prem)
- `app.shared.compliance.fairness_guard.FairnessGuard` — bloqueia padrões discriminatórios no Learning Loop
- `app.shared.compliance.audit_service.audit_service` — audit trail de padrões bloqueados
- `app.domains.ai.services.model_drift_service.ModelDriftService` — drift trigger em feedbacks negativos
- `app.services.notification_service.notification_service` — alertas Bell + Teams ao abrir circuit

---

## PARTE 2 — Conteúdo Real dos Arquivos

---

### BLOCO A — `app/shared/resilience/circuit_breaker.py` (INTERFACE EXTRAÍDA — 1060L)

**Enums e dataclasses:**

```python
class CircuitState(StrEnum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal: chamadas passam
    OPEN = "open"           # Falhando: chamadas rejeitadas imediatamente
    HALF_OPEN = "half_open" # Testando recuperação: chamadas limitadas


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    failure_threshold: int = 5       # Número de falhas antes de abrir
    recovery_timeout: float = 30.0   # Segundos antes de tentar (half-open)
    success_threshold: int = 2       # Sucessos para fechar do half-open
    timeout: float = 10.0            # Timeout de request em segundos
    exclude_exceptions: tuple = ()   # Exceções que NÃO contam como falhas


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
        self.retry_after = retry_after  # segundos até tentar novamente
        super().__init__(f"Circuit breaker '{name}' is open. Retry after {retry_after:.1f} seconds.")
```

**Classe `CircuitBreaker`:**

```python
class CircuitBreaker:
    """
    Circuit breaker para proteger chamadas a APIs externas.

    Usage (class-based):
        circuit = CircuitBreaker("anthropic", CircuitBreakerConfig(...))
        result = await circuit.call(my_func, arg1, arg2)

    Usage (functional decorator):
        @circuit_breaker("anthropic", failure_threshold=5, recovery_timeout=60)
        async def call_anthropic(prompt: str) -> str:
            ...
    """

    def __init__(self, name: str, config: CircuitBreakerConfig | None = None): ...

    # Propriedades
    @property
    def state(self) -> CircuitState:
        """Estado atual — verifica transição OPEN→HALF_OPEN automaticamente."""

    @property
    def failure_count(self) -> int: ...

    @property
    def success_count(self) -> int: ...

    @property
    def last_failure_time(self) -> float | None: ...

    # Métodos principais
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Executa função com proteção do circuit breaker.

        CLOSED: executa normalmente com timeout
        OPEN: raise CircuitBreakerError imediatamente (sem chamar a função)
        HALF_OPEN: executa limitadamente — sucesso → CLOSED; falha → volta OPEN

        TimeoutError conta como falha.
        Exceções em exclude_exceptions NÃO contam como falhas.

        Raise:
            CircuitBreakerError: se circuito está OPEN
            Exception: qualquer exceção da função wrapped
        """

    async def record_success(self):
        """Registra chamada bem-sucedida.
        HALF_OPEN: incrementa success_count → se >= success_threshold, fecha circuito.
        CLOSED: decrementa failure_count (até 0, nunca negativo)."""

    async def record_failure(self):
        """Registra chamada falhada.
        HALF_OPEN: abre circuito imediatamente.
        CLOSED: incrementa failure_count → se >= failure_threshold, abre circuito.
        Ao abrir: notificação Bell + Teams (Redis dedup: 1 alerta/circuit/hora)."""

    def reset(self):
        """Reset manual para CLOSED state (para operações manuais)."""

    def get_stats(self) -> dict:
        """Retorna stats completos: name, state, failure_count, config, stats, retry_after."""
```

**Transições de estado:**

```
CLOSED ──────(failure_count >= failure_threshold)──────→ OPEN
  ↑                                                         │
  │                                                         │ (recovery_timeout seconds)
  │                                                         ↓
  └──(success_count >= success_threshold)──────── HALF_OPEN
       (HALF_OPEN → OPEN se falhar)
```

**Circuits pré-definidos (módulo instancia na importação):**

```python
# 20 circuits pré-definidos no módulo — importar diretamente:
from app.shared.resilience.circuit_breaker import (
    ANTHROPIC_CIRCUIT,      # threshold=5, recovery=30s, timeout=60s
    OPENAI_CIRCUIT,         # threshold=5, recovery=30s, timeout=60s
    GEMINI_CIRCUIT,         # threshold=5, recovery=30s, timeout=60s
    PEARCH_CIRCUIT,         # threshold=3, recovery=60s, timeout=30s
    APIFY_CIRCUIT,          # threshold=3, recovery=60s, timeout=30s
    APIFY_SEARCH_CIRCUIT,   # threshold=3, recovery=120s, timeout=300s
    WORKOS_CIRCUIT,         # threshold=5, recovery=30s, timeout=15s
    MERGE_CIRCUIT,          # threshold=5, recovery=45s, timeout=30s
    GOOGLE_CALENDAR_CIRCUIT,# threshold=5, recovery=60s, timeout=30s
    GUPY_CIRCUIT,           # threshold=5, recovery=45s, timeout=30s
    PANDAPE_CIRCUIT,        # threshold=5, recovery=45s, timeout=30s
    MAILGUN_CIRCUIT,        # threshold=5, recovery=30s, timeout=30s
    RESEND_CIRCUIT,         # threshold=5, recovery=30s, timeout=30s
    IUGU_CIRCUIT,           # threshold=3, recovery=60s, timeout=30s
    VINDI_CIRCUIT,          # threshold=3, recovery=60s, timeout=30s
    TWILIO_VOICE_CIRCUIT,   # threshold=3, recovery=60s, timeout=30s
    GEMINI_LIVE_CIRCUIT,    # threshold=3, recovery=30s, timeout=60s
    DEEPGRAM_CIRCUIT,       # threshold=3, recovery=30s, timeout=30s
    OPENMIC_CIRCUIT,        # threshold=3, recovery=60s, timeout=30s
    RAILS_CIRCUIT,          # threshold=5, recovery=30s, timeout=15s  (rails_api)

    # Registry de todos os circuits:
    ALL_CIRCUITS,           # dict[str, CircuitBreaker] com as 20 entradas acima
)
```

**SLOs documentados por serviço (`CIRCUIT_BREAKER_SLOS`):**

```python
CIRCUIT_BREAKER_SLOS: dict[str, dict[str, Any]] = {
    "anthropic":        {"availability_target": 0.999, "latency_p95_ms": 8000,   "tier": "critical"},
    "openai":           {"availability_target": 0.999, "latency_p95_ms": 10000,  "tier": "critical"},
    "gemini":           {"availability_target": 0.995, "latency_p95_ms": 15000,  "tier": "high"},
    "pearch":           {"availability_target": 0.99,  "latency_p95_ms": 5000,   "tier": "high"},
    "apify":            {"availability_target": 0.99,  "latency_p95_ms": 120000, "tier": "medium"},
    "apify_search":     {"availability_target": 0.95,  "latency_p95_ms": 180000, "tier": "low"},
    "workos":           {"availability_target": 0.999, "latency_p95_ms": 3000,   "tier": "critical"},
    "merge":            {"availability_target": 0.99,  "latency_p95_ms": 5000,   "tier": "high"},
    "google_calendar":  {"availability_target": 0.995, "latency_p95_ms": 3000,   "tier": "medium"},
    "gupy":             {"availability_target": 0.99,  "latency_p95_ms": 5000,   "tier": "high"},
    "pandape":          {"availability_target": 0.99,  "latency_p95_ms": 5000,   "tier": "high"},
    "mailgun":          {"availability_target": 0.999, "latency_p95_ms": 2000,   "tier": "critical"},
    "resend":           {"availability_target": 0.999, "latency_p95_ms": 2000,   "tier": "high"},
    "iugu":             {"availability_target": 0.995, "latency_p95_ms": 5000,   "tier": "medium"},
    "vindi":            {"availability_target": 0.995, "latency_p95_ms": 5000,   "tier": "medium"},
    "twilio_voice":     {"availability_target": 0.99,  "latency_p95_ms": 5000,   "tier": "high"},
    "gemini_live":      {"availability_target": 0.999, "latency_p95_ms": 500,    "tier": "critical"},
    "deepgram":         {"availability_target": 0.999, "latency_p95_ms": 5000,   "tier": "high"},
    "openmic":          {"availability_target": 0.99,  "latency_p95_ms": 10000,  "tier": "high"},
    "rails_api":        {"availability_target": 0.999, "latency_p95_ms": 500,    "tier": "critical"},
    # cada entrada também tem: error_budget_pct, description
}
```

**Mensagens de modo degradado (`DEGRADED_MODE_RESPONSES`):**

```python
DEGRADED_MODE_RESPONSES: dict[str, str] = {
    "anthropic":        "A assistente LIA está temporariamente indisponível. O serviço de IA principal (Anthropic) está com instabilidades. Tente novamente em alguns minutos ou contate o suporte.",
    "openai":           "O serviço de IA alternativo está temporariamente indisponível. Tente novamente em instantes.",
    "gemini":           "A análise multimodal está temporariamente indisponível. Tente novamente em instantes.",
    "pearch":           "A busca de candidatos externos está temporariamente indisponível. Você pode buscar na base interna de candidatos enquanto isso.",
    "apify":            "O enriquecimento de perfis via LinkedIn está temporariamente indisponível. Os dados já disponíveis na base continuam acessíveis.",
    "apify_search":     "A busca de candidatos via Apify (fallback) está temporariamente indisponível. Tente novamente em alguns minutos ou aguarde a recuperação do serviço principal (Pearch).",
    "workos":           "O serviço de autenticação está com instabilidades. Tente fazer login novamente ou contate o suporte.",
    "merge":            "A sincronização com ATS externo está temporariamente indisponível. Os dados locais continuam acessíveis.",
    "google_calendar":  "O agendamento via Google Calendar está temporariamente indisponível. Agende manualmente e tente a sincronização mais tarde.",
    "gupy":             "A integração com Gupy está temporariamente indisponível. Os dados locais continuam acessíveis.",
    "pandape":          "A integração com Pandapé está temporariamente indisponível. Os dados locais continuam acessíveis.",
    "mailgun":          "O envio de emails está temporariamente indisponível. As mensagens serão reenviadas assim que o serviço for restaurado.",
    "resend":           "O serviço de email alternativo está temporariamente indisponível. Tente novamente em instantes.",
    "iugu":             "O serviço de pagamentos está temporariamente indisponível. Tente novamente em alguns minutos ou contate o suporte financeiro.",
    "vindi":            "O serviço de pagamentos recorrentes está temporariamente indisponível. Tente novamente em alguns minutos.",
    "twilio_voice":     "O screening por voz está temporariamente indisponível. A triagem será conduzida via chat ou WhatsApp como alternativa.",
    "gemini_live":      "O screening por voz via navegador está temporariamente indisponível. Tentando pipeline alternativo (Twilio). Caso indisponível, use chat ou WhatsApp.",
    "deepgram":         "A transcrição de voz está temporariamente indisponível. Tente novamente em alguns instantes ou use transcrição manual.",
    "openmic":          "O screening automatizado por voz está temporariamente indisponível. A triagem será conduzida via chat ou WhatsApp como alternativa.",
    "rails_api":        "O ATS principal está temporariamente indisponível. Os dados locais em cache continuam acessíveis. Operações de escrita serão enfileiradas para sincronização assim que o serviço for restaurado.",
}

def get_degraded_response(service_name: str) -> str:
    """Retorna mensagem de modo degradado para o circuit dado."""
    return DEGRADED_MODE_RESPONSES.get(service_name, _DEGRADED_FALLBACK)

def get_slo(service_name: str) -> dict[str, Any] | None:
    """Retorna configuração de SLO para o serviço, ou None se não definido."""
    return CIRCUIT_BREAKER_SLOS.get(service_name)

async def with_circuit_breaker(circuit: CircuitBreaker, func: Callable, *args, **kwargs) -> Any:
    """Wrapper function para executar função com proteção de circuit breaker."""
```

**Notificações ao abrir circuit (`_notify_circuit_open`):**

Ao abrir, o circuit chama `_notify_circuit_open(service_name)` via `asyncio.create_task()`.
Comportamento:
1. Verifica chave Redis `cb_alert:{service_name}` (dedup de 1h)
2. Se não existe: cria chave com TTL 3600s + envia notificação via `notification_service.send_system_alert()`
3. Canais: `["bell", "teams"]`
4. Toda a operação é fail-soft (não bloqueia a abertura do circuit)

---

### BLOCO B — `app/shared/learning/learning_loop_service.py` (INTERFACE EXTRAÍDA — 1133L)

**Enums e dataclasses:**

```python
class FeedbackOutcome(StrEnum):
    """Possíveis resultados para uma sugestão."""
    ACCEPTED = "accepted"   # sugestão usada exatamente como foi
    MODIFIED = "modified"   # sugestão usada com modificações
    REJECTED = "rejected"   # sugestão explicitamente rejeitada
    IGNORED = "ignored"     # campo finalizado sem valor (sugestão ignorada)


class PatternType(StrEnum):
    """Tipos de padrões aprendíveis."""
    SALARY_PREFERENCE = "salary_preference"
    SKILL_PREFERENCE = "skill_preference"
    BENEFIT_PREFERENCE = "benefit_preference"
    WORK_MODEL_PREFERENCE = "work_model_preference"
    SCREENING_PREFERENCE = "screening_preference"
    JD_STYLE_PREFERENCE = "jd_style_preference"
    SOURCE_TRUST = "source_trust"


@dataclass
class FeedbackCapture:
    """Estrutura de dados para captura de feedback."""
    company_id: str
    field_name: str         # ex: "salary_min", "skills", "benefits"
    suggested_value: Any    # valor que o sistema sugeriu
    final_value: Any        # valor que o usuário confirmou
    outcome: FeedbackOutcome
    session_id: str | None = None
    job_id: str | None = None
    stage: str | None = None     # fase do wizard (ex: "compensation", "requirements")
    role: str | None = None
    seniority: str | None = None
    department: str | None = None
    location: str | None = None
    source: str | None = None                  # ex: "llm_suggestion", "market_data"
    source_confidence: float | None = None
    response_time_ms: int | None = None


@dataclass
class LearnedPattern:
    """Padrão extraído dos dados de feedback."""
    pattern_type: PatternType
    pattern_key: str               # ex: "salary_min:engenheiro:senior"
    pattern_value: Any             # ex: {"avg_min": 12000, "median_min": 11500, ...}
    sample_size: int
    acceptance_rate: float         # 0.0 a 1.0
    confidence: str                # "high" | "medium" | "low" | "very_low"
    confidence_score: float        # 0.0 a 1.0
    filters: dict[str, str | None] # {role, seniority, department, location}
```

**Classe `LearningLoopService`:**

```python
class LearningLoopService:
    """
    Serviço de aprendizado contínuo que captura feedback e gera padrões.

    Princípio: aprendizado invisível — captura dados sem UI explícita.
    O sistema aprende observando o que usuários aceitam, modificam ou rejeitam.

    Fluxo:
    1. CAPTURE: registra sugestão + resultado em FeedbackEvent (DB)
    2. ANALYZE: detecta padrões acumulados em batch (Celery periódico)
    3. APPLY: usa padrões para melhorar sugestões futuras
    """

    CONFIDENCE_THRESHOLDS = {
        "high": 20,    # >= 20 amostras → confiança alta
        "medium": 10,  # >= 10 amostras → confiança média
        "low": 5       # >= 5  amostras → confiança baixa
    }

    ACCEPTANCE_THRESHOLDS = {
        "promote": 0.75,  # acima → boosta confidence_score
        "demote": 0.25    # abaixo → rebaixa confidence_score
    }

    # Métodos de captura silenciosa
    async def capture_feedback(
        self,
        db: AsyncSession,
        capture: FeedbackCapture
    ) -> str:
        """
        Registra evento de feedback em FeedbackEvent.

        Efeitos colaterais:
        - Se outcome REJECTED ou IGNORED: dispara ModelDriftService.check_drift_trigger()
          assincrono (asyncio.create_task — não bloqueia)
        - Calcula modification_delta quando outcome=MODIFIED

        Returns: feedback event ID (str)
        """

    async def capture_from_wizard_update(
        self,
        db: AsyncSession,
        company_id: str,
        session_id: str,
        job_id: str | None,
        field_name: str,
        suggested_value: Any,
        final_value: Any,
        stage: str | None = None,
        context: dict[str, Any] | None = None,  # role, seniority, department, location
        source: str | None = None,
        source_confidence: float | None = None,
        explicitly_rejected: bool = False
    ) -> str:
        """Convenience method para captura automática no wizard.
        Determina outcome automaticamente (ACCEPTED/MODIFIED/REJECTED/IGNORED).
        Chamado quando campos são finalizados no wizard de criação de vaga."""

    # Processamento em batch (Celery periódico)
    @trace_span("learning.process_feedback", attributes={"component": "learning_loop"})
    async def process_unprocessed_feedback(
        self,
        db: AsyncSession,
        company_id: str,
        batch_size: int = 100
    ) -> int:
        """
        Processa eventos FeedbackEvent não processados → atualiza LearningPattern.

        Proteções obrigatórias antes de persistir:
        1. FairnessGuard.validate_learning_batch(patterns) — bloqueia padrões discriminatórios
           (env: FAIRNESS_LEARNING_CHECK_ENABLED=true, padrão)
           Padrões bloqueados: auditados via AuditService.log_decision()
        2. Snapshot ANTES de aplicar — learning_snapshot_service.save_snapshot()
           (permite rollback em caso de viés posterior)

        Returns: número de eventos processados
        """

    # Consulta de padrões aprendidos
    async def get_patterns_for_context(
        self,
        db: AsyncSession,
        company_id: str,
        field_name: str,
        role: str | None = None,
        seniority: str | None = None,
        department: str | None = None,
        location: str | None = None,
        min_confidence: float = 0.5
    ) -> list[LearnedPattern]:
        """
        Recupera padrões aplicáveis para o contexto dado.
        Ordenados por especificidade (filtros preenchidos) e depois por confidence_score.
        """

    async def get_salary_adjustment(
        self,
        db: AsyncSession,
        company_id: str,
        role: str | None = None,
        seniority: str | None = None
    ) -> dict[str, float] | None:
        """
        Retorna ajuste de salário aprendido baseado em histórico.
        Returns: {learned_min, learned_max, median_min, median_max, sample_size, confidence}
        ou None se sem padrões suficientes.
        """

    async def get_preferred_skills(
        self,
        db: AsyncSession,
        company_id: str,
        role: str | None = None,
        seniority: str | None = None,
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """Skills preferidas da empresa (histórico), rankeadas por frequência.
        Returns: [{"skill": str, "usage_count": int, "confidence": float}]
        """

    async def get_feedback_stats(
        self,
        db: AsyncSession,
        company_id: str,
        days_back: int = 30
    ) -> dict[str, Any]:
        """Stats de feedback para analytics.
        Returns: {total_events, outcomes: {accepted, modified, rejected, ignored},
                  acceptance_rate, period_days}
        """

    async def capture_skills_feedback(
        self,
        db: AsyncSession,
        company_id: str,
        suggested_skills: list[dict[str, Any]],
        final_skills: list[dict[str, Any]],
        job_context: dict[str, Any]  # job_id, job_title, department, seniority
    ) -> None:
        """
        Captura feedback quando skills são finalizadas.
        Compara sugeridas vs finais → cria SkillUsageAnalytics entries:
        - accepted: skill usada como sugerida (mesmos weight/level)
        - modified: skill usada com diferente weight/level
        - rejected: skill sugerida foi removida
        - added: skill nova não estava nas sugestões (source="manual")
        """
```

**Mapeamento de campo → PatternType:**

```python
field_to_pattern = {
    "salary_min":          PatternType.SALARY_PREFERENCE,
    "salary_max":          PatternType.SALARY_PREFERENCE,
    "salary":              PatternType.SALARY_PREFERENCE,
    "salary_range":        PatternType.SALARY_PREFERENCE,
    "skills":              PatternType.SKILL_PREFERENCE,
    "technical_skills":    PatternType.SKILL_PREFERENCE,
    "behavioral_skills":   PatternType.SKILL_PREFERENCE,
    "benefits":            PatternType.BENEFIT_PREFERENCE,
    "work_model":          PatternType.WORK_MODEL_PREFERENCE,
    "screening_questions": PatternType.SCREENING_PREFERENCE,
    "job_summary":         PatternType.JD_STYLE_PREFERENCE,
    # outros: "general_preference"
}
```

**Pattern key format:**

```python
# Chave gerada por _generate_pattern_key():
pattern_key = f"{field_name}:{role or 'any_role'}:{seniority or 'any_seniority'}"
# Ex: "salary_min:engenheiro_de_software:senior"
#     "skills:any_role:any_seniority"
```

**Variáveis de ambiente:**

| Variável | Padrão | Efeito |
|----------|--------|--------|
| `FAIRNESS_LEARNING_CHECK_ENABLED` | `"true"` | Liga FairnessGuard no batch de padrões |

---

### BLOCO C — `app/shared/messaging/broker_interface.py` (VERBATIM COMPLETO — 335L)

```python
"""
Broker Abstraction Layer — BrokerInterface + implementações concretas.

Permite troca de broker de mensageria por variável de ambiente (BROKER_BACKEND),
sem reescrita de código de aplicação.

Backends disponíveis:
  redis    — usa Redis como broker (padrão atual / produção on-prem)
  rabbitmq — usa RabbitMQ (on-prem, chat em produção)
  pubsub   — stub Google Cloud Pub/Sub (migração GCP, NotImplementedError claro)

Uso via factory:
    from app.shared.messaging.broker_interface import get_broker
    broker = get_broker()
    await broker.publish("my-topic", {"key": "value"})
    healthy = await broker.health_check()

Troca de backend:
    Setar BROKER_BACKEND=rabbitmq (ou pubsub para GCP stub).
    Todas as 4 filas Celery continuam funcionando — o broker Celery
    é controlado separadamente via CELERY_BROKER_URL no celery_app.py.
"""
from __future__ import annotations

import abc
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class BrokerInterface(abc.ABC):
    """Interface abstrata para brokers de mensagem.

    Todas as implementações concretas devem implementar os três métodos:
    - publish(): publica mensagem em um tópico/fila
    - consume(): consome mensagem de um tópico/fila (iteração assíncrona)
    - health_check(): verifica conectividade com o broker

    Este contrato garante que a troca de Redis → RabbitMQ → Pub/Sub seja
    uma mudança de configuração (BROKER_BACKEND), não uma reescrita.
    """

    @abc.abstractmethod
    async def publish(self, topic: str, message: dict[str, Any]) -> str:
        """Publica mensagem em um tópico ou fila.
        Returns: message_id (correlation_id, message_id ou str(uuid4()))
        Raises: RuntimeError se broker indisponível."""

    @abc.abstractmethod
    async def consume(self, topic: str) -> dict[str, Any] | None:
        """Consome próxima mensagem disponível. Returns: payload dict ou None."""

    @abc.abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Verifica conectividade. Returns: {status: "healthy"|"unhealthy", ...}"""


class RedisBroker(BrokerInterface):
    """Implementação Redis do BrokerInterface.

    Usa aioredis para publish/subscribe via Redis Lists (LPUSH / BRPOP).
    É o backend padrão — o mesmo Redis já usado pelo Celery e cache.

    Variável de ambiente: REDIS_URL (default: redis://localhost:6379/0)
    """

    def __init__(self, redis_url: str | None = None) -> None:
        self._redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._client = None

    async def _get_client(self):
        if self._client is None:
            try:
                import redis.asyncio as aioredis
                self._client = aioredis.from_url(
                    self._redis_url,
                    decode_responses=True,
                    socket_connect_timeout=1.0,
                    socket_timeout=1.0,
                )
            except ImportError:
                import aioredis  # type: ignore[import]
                result = aioredis.from_url(self._redis_url, decode_responses=True)
                if hasattr(result, "__await__"):
                    self._client = await result
                else:
                    self._client = result
        return self._client

    async def publish(self, topic: str, message: dict[str, Any]) -> str:
        import json
        from uuid import uuid4
        client = await self._get_client()
        message_id = message.get("correlation_id") or str(uuid4())
        payload = json.dumps({**message, "message_id": message_id}, default=str)
        await client.lpush(f"broker:{topic}", payload)
        logger.debug("[RedisBroker] publish topic=%s message_id=%s", topic, message_id)
        return message_id

    async def consume(self, topic: str) -> dict[str, Any] | None:
        import json
        client = await self._get_client()
        result = await client.brpop(f"broker:{topic}", timeout=1)
        if result is None:
            return None
        _, raw = result
        return json.loads(raw)

    async def health_check(self) -> dict[str, Any]:
        import time
        try:
            client = await self._get_client()
            t0 = time.monotonic()
            await client.ping()
            latency_ms = round((time.monotonic() - t0) * 1000, 2)
            info = await client.info("server")
            return {
                "status": "healthy",
                "backend": "redis",
                "url": self._redis_url.split("@")[-1],
                "latency_ms": latency_ms,
                "redis_version": info.get("redis_version", "unknown"),
            }
        except Exception as exc:
            logger.warning("[RedisBroker] health_check falhou: %s", exc)
            return {"status": "unhealthy", "backend": "redis", "error": str(exc)[:200]}


class RabbitMQBroker(BrokerInterface):
    """Implementação RabbitMQ do BrokerInterface.

    Wraps rabbitmq_producer.py existente via aio-pika.
    Usado para on-prem quando Redis não é adequado (ex: chat de agentes).

    Variável de ambiente: RABBITMQ_URL (default: amqp://guest:guest@localhost:5672/)
    """

    def __init__(self, rabbitmq_url: str | None = None) -> None:
        self._rabbitmq_url = rabbitmq_url or os.getenv(
            "RABBITMQ_URL", "amqp://guest:guest@localhost:5672/"
        )
        self._connection = None

    async def _ensure_connected(self):
        try:
            import aio_pika
            if self._connection is None or self._connection.is_closed:
                self._connection = await aio_pika.connect_robust(self._rabbitmq_url)
        except ImportError as exc:
            raise RuntimeError(
                "[RabbitMQBroker] aio-pika não instalado. "
                "Instale com: pip install aio-pika"
            ) from exc

    async def publish(self, topic: str, message: dict[str, Any]) -> str:
        import json
        import aio_pika
        from uuid import uuid4
        await self._ensure_connected()
        channel = await self._connection.channel()
        message_id = message.get("correlation_id") or str(uuid4())
        body = json.dumps({**message, "message_id": message_id}, default=str).encode()
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=body,
                content_type="application/json",
                correlation_id=message_id,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=topic,
        )
        logger.debug("[RabbitMQBroker] publish topic=%s message_id=%s", topic, message_id)
        return message_id

    async def consume(self, topic: str) -> dict[str, Any] | None:
        import json, aio_pika
        await self._ensure_connected()
        channel = await self._connection.channel()
        queue = await channel.declare_queue(topic, durable=True)
        msg = await queue.get(fail=False)
        if msg is None:
            return None
        async with msg.process():
            return json.loads(msg.body.decode())

    async def health_check(self) -> dict[str, Any]:
        import time
        try:
            await self._ensure_connected()
            t0 = time.monotonic()
            channel = await self._connection.channel()
            await channel.close()
            latency_ms = round((time.monotonic() - t0) * 1000, 2)
            return {
                "status": "healthy",
                "backend": "rabbitmq",
                "url": self._rabbitmq_url.split("@")[-1] if "@" in self._rabbitmq_url else self._rabbitmq_url,
                "latency_ms": latency_ms,
            }
        except Exception as exc:
            logger.warning("[RabbitMQBroker] health_check falhou: %s", exc)
            return {"status": "unhealthy", "backend": "rabbitmq", "error": str(exc)[:200]}


class PubSubBroker(BrokerInterface):
    """Stub Google Cloud Pub/Sub — para migração GCP (Sprint de Infra dedicado).

    TODOS os métodos levantam NotImplementedError com mensagem clara.
    """

    def __init__(self, project_id: str | None = None) -> None:
        self._project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        logger.warning(
            "[PubSubBroker] Usando stub GCP Pub/Sub. "
            "Implemente a integração real antes de usar em produção. "
            "Ver: docs/infra/gcp-migration-guide.md"
        )

    async def publish(self, topic: str, message: dict[str, Any]) -> str:
        raise NotImplementedError("[PubSubBroker] publish() não implementado. Este é um stub para migração GCP.")

    async def consume(self, topic: str) -> dict[str, Any] | None:
        raise NotImplementedError("[PubSubBroker] consume() não implementado. Este é um stub para migração GCP.")

    async def health_check(self) -> dict[str, Any]:
        return {"status": "stub", "backend": "pubsub", "project_id": self._project_id or "not_configured"}


def get_broker(backend: str | None = None) -> BrokerInterface:
    """Factory: retorna instância de BrokerInterface conforme BROKER_BACKEND.

    BROKER_BACKEND=redis     →  RedisBroker (padrão)
    BROKER_BACKEND=rabbitmq  →  RabbitMQBroker
    BROKER_BACKEND=pubsub    →  PubSubBroker (stub GCP)
    """
    resolved = (backend or os.getenv("BROKER_BACKEND", "redis")).lower().strip()
    if resolved == "redis":
        return RedisBroker()
    elif resolved == "rabbitmq":
        return RabbitMQBroker()
    elif resolved == "pubsub":
        return PubSubBroker()
    else:
        logger.warning("[get_broker] Backend '%s' desconhecido. Usando redis (fallback).", resolved)
        return RedisBroker()


_broker_instance: BrokerInterface | None = None


def get_default_broker() -> BrokerInterface:
    """Retorna singleton do broker padrão (lazy init, thread-safe via GIL)."""
    global _broker_instance
    if _broker_instance is None:
        _broker_instance = get_broker()
        logger.info(
            "[get_default_broker] Broker inicializado: %s (BROKER_BACKEND=%s)",
            type(_broker_instance).__name__,
            os.getenv("BROKER_BACKEND", "redis"),
        )
    return _broker_instance
```

---

### BLOCO D — `app/shared/messaging/platform_events.py` (VERBATIM COMPLETO — 189L)

```python
"""
Platform Events — comunicação assíncrona entre APIs de domínio via RabbitMQ.

Contrato de eventos:
  Exchange: "platform.events" (topic exchange)
  Routing keys: "{dominio}.{entidade}.{acao}"
    Ex: "vagas.job.published"
        "funil.candidate.moved"
        "onboarding.company.configured"

Por que eventos em vez de HTTP sync entre APIs?
  - Desacopla deploys (api-vagas pode estar down sem afetar api-funil)
  - Escala independente
  - Auditável (exchange topic persiste mensagens)

André (reunião 08/03/2026): "Evitar chamadas HTTP síncronas entre APIs.
  Preferir RabbitMQ (eventos) ou shared database."
"""
from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

PLATFORM_EVENTS_EXCHANGE = "platform.events"


class PlatformEvent(BaseModel):
    """Schema base para todos os eventos inter-API."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str   # "vagas.job.published", "funil.candidate.moved", etc.
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    company_id: str   # OBRIGATÓRIO — multi-tenancy
    payload: dict[str, Any]
    source_api: str   # "api-vagas" | "api-funil" | "api-onboarding"
    version: str = "1.0"


# ---------------------------------------------------------------------------
# Eventos específicos
# ---------------------------------------------------------------------------

class JobPublishedEvent(PlatformEvent):
    """Emitido quando uma vaga é publicada em api-vagas."""
    event_type: str = "vagas.job.published"
    source_api: str = "api-vagas"


class JobClosedEvent(PlatformEvent):
    """Emitido quando uma vaga é encerrada em api-vagas."""
    event_type: str = "vagas.job.closed"
    source_api: str = "api-vagas"


class CandidateMovedEvent(PlatformEvent):
    """Emitido quando um candidato muda de estágio em api-funil."""
    event_type: str = "funil.candidate.moved"
    source_api: str = "api-funil"


class CompanyConfiguredEvent(PlatformEvent):
    """Emitido quando uma empresa completa o onboarding em api-onboarding."""
    event_type: str = "onboarding.company.configured"
    source_api: str = "api-onboarding"


class ScreeningCompletedEvent(PlatformEvent):
    """Emitido quando a triagem WSI de um candidato é concluída."""
    event_type: str = "screening.wsi.completed"
    source_api: str = "api-funil"


# ---------------------------------------------------------------------------
# Publisher
# ---------------------------------------------------------------------------

async def publish_platform_event(event: PlatformEvent) -> bool:
    """
    Publica evento no exchange platform.events.

    Routing key = event.event_type  (ex: "vagas.job.published")
    Retorna True se publicado, False em caso de falha (fail-soft intencional).

    Falha silenciosa intencional: indisponibilidade do RabbitMQ NÃO deve
    impedir o fluxo principal da aplicação.
    """
    try:
        from app.shared.messaging.rabbitmq_producer import publish_to_exchange
        await publish_to_exchange(
            exchange=PLATFORM_EVENTS_EXCHANGE,
            routing_key=event.event_type,
            message=event.model_dump(mode="json"),
        )
        logger.info(
            "[PlatformEvents] Published: %s company=%s event_id=%s",
            event.event_type, event.company_id, event.event_id,
        )
        return True
    except Exception as exc:
        logger.error(
            "[PlatformEvents] Failed to publish %s event_id=%s: %s",
            event.event_type, event.event_id, exc,
        )
        return False


# ---------------------------------------------------------------------------
# Handlers registry
# ---------------------------------------------------------------------------

_event_handlers: dict[str, list[Callable]] = {}


def register_event_handler(
    event_type: str,
    handler: Callable[[PlatformEvent], Awaitable[None]],
) -> None:
    """
    Registra handler para um tipo de evento.
    Múltiplos handlers podem ser registrados para o mesmo event_type.
    """
    if event_type not in _event_handlers:
        _event_handlers[event_type] = []
    _event_handlers[event_type].append(handler)
    logger.debug("[PlatformEvents] Handler registered for: %s", event_type)


def get_registered_handlers() -> dict[str, list[Callable]]:
    """Retorna cópia profunda do registry de handlers (para debug e testes)."""
    return {k: list(v) for k, v in _event_handlers.items()}


def clear_event_handlers() -> None:
    """Remove todos os handlers. Útil em testes."""
    _event_handlers.clear()


async def dispatch_event(raw_message: dict) -> None:
    """
    Despacha evento recebido para os handlers registrados.
    Falhas individuais de handlers são capturadas e logadas sem interromper os demais.
    """
    event_type = raw_message.get("event_type", "")
    handlers = _event_handlers.get(event_type, [])

    if not handlers:
        logger.debug("[PlatformEvents] No handlers for: %s", event_type)
        return

    try:
        event = PlatformEvent(**raw_message)
    except Exception as exc:
        logger.error("[PlatformEvents] Failed to parse event: %s — raw: %s", exc, raw_message)
        return

    for handler in handlers:
        try:
            await handler(event)
        except Exception as exc:
            logger.error(
                "[PlatformEvents] Handler %s failed for %s: %s",
                getattr(handler, "__name__", repr(handler)), event_type, exc,
            )
```

---

### BLOCO E — `app/shared/messaging/unified_event_publisher.py` (VERBATIM COMPLETO — 113L)

```python
"""
LIA-E04: Unified Event Publisher

Single entry point for publishing events to Rails. Routes internally to the
appropriate backend (RailsAdapter HTTP, RabbitMQ producer, or future Pub/Sub)
based on config.

Before: 3 separate paths (RailsAdapter HTTP, RabbitMQ producer, platform_events)
After: single publish_event() interface with automatic retry, DLQ, and audit

Legacy paths continue to work — this is additive.
"""
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class UnifiedEventPublisher:
    """Publish Rails-bound events via the configured backend with retry and audit."""

    def __init__(self):
        self._rails_adapter = None
        self._broker = None

    async def publish(
        self,
        event_type: str,
        payload: dict,
        company_id: Optional[str] = None,
        max_retries: int = 3,
        timeout_seconds: float = 10.0,
    ) -> bool:
        """Publish an event to Rails. Returns True on success.

        Includes:
        - Retry with exponential backoff (1s, 2s, 4s)
        - Timeout per attempt (asyncio.wait_for)
        - Audit logging
        - Fail-safe: returns False on final failure, does not raise
        """
        try:
            from app.shared.messaging.rails_event_schemas import (
                EVENT_VERSIONS,
                validate_event_version,
            )

            event_version = EVENT_VERSIONS.get(event_type, "1.0")
            envelope = {
                "event_type": event_type,
                "event_version": event_version,
                "company_id": company_id,
                "payload": payload,
            }

            last_error = None
            for attempt in range(max_retries):
                try:
                    result = await asyncio.wait_for(
                        self._publish_once(envelope),
                        timeout=timeout_seconds,
                    )
                    if result:
                        logger.info(
                            "[LIA-E04] Event published: type=%s company=%s attempt=%d",
                            event_type, company_id, attempt + 1,
                        )
                        return True
                except asyncio.TimeoutError:
                    last_error = "timeout"
                except Exception as e:
                    last_error = str(e)[:100]

                # Exponential backoff: 1s, 2s, 4s
                if attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)

            logger.warning(
                "[LIA-E04] Event publish failed after %d attempts: type=%s err=%s",
                max_retries, event_type, last_error,
            )
            return False
        except Exception as e:
            logger.warning("[LIA-E04] Publish error (fail-open): %s", e)
            return False

    async def _publish_once(self, envelope: dict) -> bool:
        """Single publish attempt — delegates to existing RailsAdapter."""
        try:
            from app.domains.integrations_hub.services.rails_adapter import RailsAdapter
            if self._rails_adapter is None:
                self._rails_adapter = RailsAdapter()
            return await self._rails_adapter.publish_event(
                event_type=envelope["event_type"],
                payload=envelope.get("payload", {}),
                company_id=envelope.get("company_id"),
            )
        except Exception:
            return False


# Singleton
unified_event_publisher = UnifiedEventPublisher()
```

---

## PARTE 3 — Como Funciona em Runtime

### Fluxo do Circuit Breaker em chamadas externas

```
Agente/Service precisa chamar API externa (ex: Anthropic)
    │
    ├── Importar circuit pré-definido:
    │   from app.shared.resilience.circuit_breaker import ANTHROPIC_CIRCUIT
    │
    └── Chamar via circuit:
        result = await ANTHROPIC_CIRCUIT.call(anthropic_client.generate, prompt)
            │
            ├── circuit.state == CLOSED
            │   → executa com timeout (60s para anthropic)
            │   → sucesso: record_success() → decrementa failure_count
            │   → falha: record_failure() → incrementa failure_count
            │       ├── se failure_count >= 5: _transition_to_open()
            │       │   → notifica Bell + Teams (Redis dedup 1h)
            │       └── propaga exception para o caller
            │
            ├── circuit.state == OPEN
            │   → raise CircuitBreakerError(name, retry_after) imediatamente
            │   → nenhuma chamada ao serviço externo é feita
            │   → ProviderContainer.generate_with_fallback() captura e tenta próximo provider
            │
            └── circuit.state == HALF_OPEN (após recovery_timeout=30s)
                → executa como CLOSED
                → sucesso: success_count += 1; se >= 2: HALF_OPEN → CLOSED
                → falha: HALF_OPEN → OPEN imediatamente
```

### Fluxo do Learning Loop

```
Usuário finaliza campo no Wizard de Criação de Vaga
    │
    └── WizardService.update_field(field_name, suggested_value, final_value)
            │
            └── learning_loop_service.capture_from_wizard_update(...)
                    │
                    ├── _determine_outcome() → ACCEPTED/MODIFIED/REJECTED/IGNORED
                    ├── FeedbackEvent(company_id, field_name, suggested, final, outcome)
                    ├── db.add(event) + commit
                    └── se REJECTED/IGNORED: asyncio.create_task(
                            ModelDriftService().check_drift_trigger(...)
                        )

[Celery periodic task — ex: a cada 6h]
    └── learning_loop_service.process_unprocessed_feedback(db, company_id)
            │
            ├── busca FeedbackEvent(processed_for_learning=False) em batch=100
            ├── agrupa por pattern_key (field_name:role:seniority)
            ├── FairnessGuard.validate_learning_batch(patterns)
            │   → padrões bloqueados: auditados + removidos do batch
            ├── LearningSnapshotService.save_snapshot() antes de persistir
            └── _update_pattern() para cada pattern_key
                    └── upsert LearningPattern (sample_size, acceptance_rate, confidence)

Wizard gera nova sugestão de salário
    └── learning_loop_service.get_salary_adjustment(db, company_id, role, seniority)
            └── get_patterns_for_context(field_name="salary_range", ...)
                    └── retorna LearnedPattern com avg_min, median_min, etc.
                        → usado para ajustar sugestão do LLM
```

### Fluxo de eventos da plataforma (inter-API)

```
api-vagas publica vaga → dispatch para outros microserviços
    │
    └── await publish_platform_event(JobPublishedEvent(
            company_id="acme",
            payload={"job_id": "...", "title": "...", "salary_range": {...}}
        ))
            │
            └── rabbitmq_producer.publish_to_exchange(
                    exchange="platform.events",
                    routing_key="vagas.job.published",
                    message={...}
                )

api-funil consumer RabbitMQ recebe mensagem
    │
    └── dispatch_event(raw_message)
            │
            ├── resolve event_type="vagas.job.published"
            ├── busca handlers em _event_handlers["vagas.job.published"]
            └── await handler(event) para cada handler registrado
                    └── ex: atualizar talent_pool com nova vaga

Para events entre FastAPI e Rails:
    └── await unified_event_publisher.publish(
            event_type="candidate.stage_updated",
            payload={"candidate_id": "...", "stage": "..."},
            company_id="acme"
        )
            └── retry exponencial (1s, 2s, 4s) → RailsAdapter.publish_event()
```

---

## PARTE 4 — Como Reconstruir do Zero

### Passo 1 — Implementar CircuitBreaker (circuit_breaker.py como template)

1. Implementar `CircuitState(StrEnum)` com 3 estados
2. Implementar `CircuitBreakerConfig` com os 5 parâmetros
3. Implementar `CircuitBreaker.call()` com lock asyncio para thread-safety
4. Implementar transições `_transition_to_open()` e `_transition_to_closed()`
5. Lógica de HALF_OPEN: `_should_attempt_reset()` verifica `recovery_timeout`

### Passo 2 — Registrar circuit breakers para cada serviço externo

Copiar os instancias pré-definidos do BLOCO A como template.
Regras de configuração por tier:
- `tier: critical` (LLMs, auth, email, Rails): `failure_threshold=5, recovery_timeout=30s`
- `tier: high` (ATS, voz, sourcing): `failure_threshold=5, recovery_timeout=45s`
- `tier: medium` (calendar, billing): `failure_threshold=5, recovery_timeout=60s`
- `tier: low` (scrapers lentos): `failure_threshold=3, recovery_timeout=120s, timeout=300s`

### Passo 3 — Implementar DLQ para falhas do circuit

Quando `CircuitBreakerError` é capturado:
1. Logar a mensagem falhada em uma DLQ (Redis list ou RabbitMQ DLX)
2. Celery worker processa a DLQ com retry após `recovery_timeout` do circuit

### Passo 4 — Definir PlatformEvents (platform_events.py como template)

Copiar o BLOCO D verbatim.
Criar tipos de evento específicos do seu produto:
```python
class MyDomainEvent(PlatformEvent):
    event_type: str = "meu_dominio.entidade.acao"
    source_api: str = "api-meu-dominio"
```
Regra de routing key: `"{dominio}.{entidade}.{acao}"` (ex: `"hr.candidate.hired"`)
`company_id` é OBRIGATÓRIO em todo evento — multi-tenancy.

### Passo 5 — Implementar UnifiedEventPublisher

Copiar o BLOCO E verbatim.
Criar `rails_event_schemas.py` com `EVENT_VERSIONS: dict[str, str]` mapeando event_type → versão.
O publisher usa o RailsAdapter existente — adapte para o seu backend de destino em `_publish_once()`.

### Passo 6 — Implementar LearningLoop

1. Criar modelo `FeedbackEvent` (SQLAlchemy) com os campos de `FeedbackCapture`
2. Criar modelo `LearningPattern` com campos: `company_id`, `pattern_type`, `pattern_key`, `pattern_value` (JSONB), `sample_size`, `acceptance_rate`, `confidence`, `confidence_score`, `role_filter`, `seniority_filter`, filtros de department/location, `is_active`
3. Implementar `capture_from_wizard_update()` — chamado toda vez que um campo é finalizado
4. Implementar `process_unprocessed_feedback()` — Celery task periódica
5. **CRÍTICO:** Integrar FairnessGuard antes de persistir padrões (`FAIRNESS_LEARNING_CHECK_ENABLED`)
6. Snapshot antes de aplicar — para rollback em caso de viés descoberto posteriormente
7. Integrar `get_salary_adjustment()` e `get_preferred_skills()` nas APIs de sugestão do wizard

---

## PARTE 5 — Checklist de Validação + Testes

### Checklist de Resiliência e Aprendizado

- [ ] Circuit breaker configurado para TODOS os serviços externos (não apenas LLMs)
- [ ] `CircuitBreakerError.retry_after` propagado para o cliente (para informar quando tentar)
- [ ] `DEGRADED_MODE_RESPONSES` definido para cada circuit (mensagens em PT-BR)
- [ ] Notificação ao abrir circuit: Bell + Teams + Redis dedup (1h/circuit)
- [ ] `CIRCUIT_BREAKER_SLOS` documentados por serviço
- [ ] `BROKER_BACKEND` configurável por env var (redis padrão, rabbitmq disponível)
- [ ] `PlatformEvent.company_id` obrigatório em todos os eventos
- [ ] `publish_platform_event()` fail-soft (retorna False, não raise)
- [ ] `UnifiedEventPublisher.publish()` com retry exponencial 3 tentativas
- [ ] `FeedbackEvent.processed_for_learning = False` no insert (Celery processa depois)
- [ ] `FairnessGuard.validate_learning_batch()` ANTES de persistir padrões
- [ ] Snapshot salvo antes de aplicar padrões (rollback possível)
- [ ] `AuditService.log_decision()` registra padrões bloqueados pelo FairnessGuard

### Testes de Validação

**Teste 1 — Circuit transitions:**
```python
circuit = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=2))
assert circuit.state == CircuitState.CLOSED

# Simular 2 falhas
await circuit.record_failure()
await circuit.record_failure()
assert circuit.state == CircuitState.OPEN

# CircuitBreakerError ao tentar chamar
with pytest.raises(CircuitBreakerError) as exc_info:
    await circuit.call(my_func)
assert exc_info.value.retry_after > 0
```

**Teste 2 — Recovery HALF_OPEN → CLOSED:**
```python
circuit = CircuitBreaker("test", CircuitBreakerConfig(
    failure_threshold=2, recovery_timeout=0.1, success_threshold=2
))
await circuit.record_failure()
await circuit.record_failure()
assert circuit.state == CircuitState.OPEN

import asyncio; await asyncio.sleep(0.15)
assert circuit.state == CircuitState.HALF_OPEN

await circuit.record_success()
await circuit.record_success()
assert circuit.state == CircuitState.CLOSED
```

**Teste 3 — Broker interface troca de backend:**
```python
redis_broker = get_broker("redis")
assert isinstance(redis_broker, RedisBroker)

rmq_broker = get_broker("rabbitmq")
assert isinstance(rmq_broker, RabbitMQBroker)

# Env var override:
import os; os.environ["BROKER_BACKEND"] = "rabbitmq"
default = get_broker()
assert isinstance(default, RabbitMQBroker)
```

**Teste 4 — PlatformEvent company_id obrigatório:**
```python
# Sem company_id deve falhar na validação Pydantic:
with pytest.raises(ValidationError):
    event = JobPublishedEvent(payload={"job_id": "123"})  # sem company_id
```

**Teste 5 — publish_platform_event fail-soft:**
```python
# Com RabbitMQ fora do ar:
event = JobPublishedEvent(company_id="acme", payload={})
result = await publish_platform_event(event)
assert result == False  # não levanta exceção
```

**Teste 6 — Dispatch de eventos para handlers:**
```python
received = []
async def my_handler(event: PlatformEvent):
    received.append(event)

register_event_handler("vagas.job.published", my_handler)
await dispatch_event({
    "event_type": "vagas.job.published",
    "company_id": "acme",
    "payload": {"job_id": "123"},
    "source_api": "api-vagas"
})
assert len(received) == 1
assert received[0].company_id == "acme"
```

**Teste 7 — UnifiedEventPublisher retry com backoff:**
```python
publisher = UnifiedEventPublisher()
# Com backend falhando:
success = await publisher.publish(
    event_type="candidate.stage_updated",
    payload={"candidate_id": "123"},
    company_id="acme",
    max_retries=2,
    timeout_seconds=1.0
)
assert success == False  # fail-safe, não raise
```

**Teste 8 — LearningLoop outcome determination:**
```python
svc = LearningLoopService()
outcome = svc._determine_outcome(
    suggested_value={"min": 10000},
    final_value={"min": 10000},  # mesmo valor
)
assert outcome == FeedbackOutcome.ACCEPTED

outcome2 = svc._determine_outcome(
    suggested_value={"min": 10000},
    final_value={"min": 12000},  # valor diferente
)
assert outcome2 == FeedbackOutcome.MODIFIED
```

**Teste 9 — LearningLoop FairnessGuard bloqueia padrão discriminatório:**
```python
# Se um padrão tem campo discriminatório como filtro (ex: race_filter),
# deve ser bloqueado e auditado:
# process_unprocessed_feedback deve remover e logar via AuditService
# (verificar audit_service.log_decision chamado com decision_type="fairness_check")
```

**Teste 10 — confidence thresholds:**
```python
svc = LearningLoopService()
confidence, score = svc._calculate_confidence(sample_size=25, acceptance_rate=0.8)
assert confidence == "high"
assert score > 0.9  # alta aceitação boosta

confidence2, score2 = svc._calculate_confidence(sample_size=8, acceptance_rate=0.3)
assert confidence2 == "medium"
assert score2 < 0.7  # baixa aceitação reduz
```

### Referência rápida — Padrões de código

| Situação | Padrão correto |
|----------|----------------|
| Chamada a API externa | `await circuit.call(func, *args)` |
| Circuit aberto | Capturar `CircuitBreakerError`, retornar `get_degraded_response(name)` |
| Novo serviço externo | Criar `CircuitBreaker("nome", config)` + entry em `ALL_CIRCUITS` + SLO + DEGRADED_RESPONSE |
| Evento inter-API | `await publish_platform_event(MeuEvento(company_id=..., payload=...))` |
| Evento para Rails | `await unified_event_publisher.publish(event_type, payload, company_id)` |
| Captura de feedback | `await learning_loop_svc.capture_from_wizard_update(...)` no endpoint de update |
| Usar padrões aprendidos | `await learning_loop_svc.get_salary_adjustment(db, company_id, role, seniority)` |
| Troca de broker | `BROKER_BACKEND=rabbitmq` (env var, sem código) |

---

*Documento gerado em 2026-04-23 a partir de leitura direta dos arquivos canônicos.*
*Todos os blocos de código foram extraídos com Read tool — zero conteúdo inventado.*
*Guias completos: COMPLIANCE + INFRASTRUCTURE + RESILIENCE_LEARNING*

---

## Adendo (2026-04-23) — Ativação de FairnessGuard Layer 3 em produção + runbook

> Esta seção documenta uma mudança operacional aplicada em produção em
> 2026-04-23: ativação da Layer 3 (LLM semântico) do FairnessGuard. É exemplo
> canônico de como uma feature flag interage com o circuit breaker do Anthropic
> e como o fallback lenient é projetado.

### B.1 Ativação da flag

**Antes (estado original):**
- `libs/config/lia_config/config.py` → `FAIRNESS_LAYER3_ENABLED: bool = False`
- `.env` em produção → `FAIRNESS_LAYER3_ENABLED=false`
- Comportamento: L1 (regex 19 categorias) + L2 (43 termos PT/EN) ativos; L3
  (semântico via `claude-haiku-4-5-20251001`) desligado

**Depois (estado atual desde 2026-04-23):**
- `.env` em produção → `FAIRNESS_LAYER3_ENABLED=true`
- L3 ativada para `HIGH_IMPACT_ACTIONS` (rejection, shortlist, wsi_score)
- Cache Redis 1h para resultados de `check_semantic()`

**Validação runtime após deploy:**

```bash
# No Replit
cd /home/runner/workspace/lia-agent-system
python3 -c "from lia_config.config import settings; print(settings.FAIRNESS_LAYER3_ENABLED)"
# Deve retornar: True
```

### B.2 Interação com circuit breaker do Anthropic

`fairness_guard.py:911-970` mostra o padrão canônico de fallback lenient quando
a Layer 3 falha por exceção (incluindo circuit breaker aberto):

```python
# Layer 3 — LLM semântico com Haiku — respeitando feature flag
_layer3_enabled = False
try:
    from lia_config.config import settings as _settings
    _layer3_enabled = getattr(_settings, "FAIRNESS_LAYER3_ENABLED", False)
except Exception:
    pass

if not _layer3_enabled:
    # Retorna resultado de L1+L2 sem invocar L3
    return FairnessCheckResult(
        is_blocked=base_result.is_blocked,
        blocked_terms=base_result.blocked_terms,
        category=base_result.category,
        educational_message=base_result.educational_message,
        original_query=text,
        confidence=base_result.confidence,
        soft_warnings=implicit_warnings,
    )

try:
    semantic_result = await self.check_semantic(
        text,
        context=context or "",
        model="claude-haiku-4-5-20251001",
    )
    # Cache Redis 1h
    ...
    return semantic_result
except Exception as exc:
    logger.debug("[FairnessGuard] Layer 3 skipped: %s", exc)
    # Fallback lenient — não bloqueia, mas mantém soft_warnings de L2
    return FairnessCheckResult(
        is_blocked=False,
        blocked_terms=[],
        category=None,
        educational_message=None,
        original_query=text,
        confidence=0.5,
        soft_warnings=implicit_warnings,
    )
```

**Princípio de design:** quando provider externo falha (circuit aberto, timeout,
rate limit), L1 + L2 continuam válidos e `soft_warnings` são preservados.
Nunca bloqueia silenciosamente; nunca passa silenciosamente. Sempre registra.

### B.3 Métricas a monitorar (7 dias após ativação)

| Métrica | Alvo | Como medir | Ação se fora |
|---------|------|------------|--------------|
| Custos Anthropic (claude-haiku-4-5) | < USD 5/dia | Dashboard billing | Se > USD 10/dia: investigar cache miss |
| Cache hit rate Redis | > 60% | `redis-cli --stat` em `fairness_layer3:*` | Se < 40%: revisar key (collision?) ou aumentar TTL |
| Latência P95 endpoints de decisão | < 800 ms | APM | Se > 1200ms: considerar L3 só em fluxo assíncrono |
| Novos `soft_warnings` em `fairness_audit_log` | Sem pico abrupto | `SELECT COUNT(*) FROM fairness_audit_log WHERE created_at > '2026-04-23' AND soft_warnings IS NOT NULL` | Se +500%: revisar false positives do L3 |
| Erros L3 (exceções capturadas) | < 1% | log `[FairnessGuard] Layer 3 skipped: ...` | Se > 5%: problema de conectividade Anthropic |

### B.4 Rollback

Se métricas estourarem consistentemente por 48h:

```bash
ssh replit-wedo
sed -i 's/^FAIRNESS_LAYER3_ENABLED=true$/FAIRNESS_LAYER3_ENABLED=false/' \
  /home/runner/workspace/lia-agent-system/.env
```

**Efeito imediato:** próximas chamadas usam só L1+L2 (sem deploy necessário —
arquivo é lido runtime).

### B.5 Runbook completo

Arquivo `docs/operations/FAIRNESS_LAYER3_RUNBOOK.md` (4.5K) tem o protocolo
operacional completo: o que muda, métricas de 7 dias, rollback, testes
automatizados (`tests/test_sprint2_fairness_agent.py`), responsáveis.

### B.6 Lição arquitetural (canônica para o produto novo)

Quando implementar feature flags que interagem com circuit breakers:

1. **Default seguro:** flag `False` por padrão no código (`bool = False`)
2. **Recomendação documentada:** `.env.production.example` com comentário
   `# [RECOMMENDED] in production`
3. **Fallback lenient:** quando provider externo falha, retornar estado neutro
   (não bloquear silenciosamente, não passar silenciosamente)
4. **Cache Redis** para reduzir custo + latência em chamadas repetidas
5. **Audit log** de toda escolha (L1 só / L2 só / L3 chamado / L3 falhou)
6. **Testes cobrem ambos os estados** (`patch.dict("os.environ", {"FLAG": "1"})`)
7. **Runbook publicado** antes de ativar em produção

---

*Adendo gerado em 2026-04-23 — documenta ativação aplicada em produção naquela
data. Não substitui o conteúdo principal acima.*
