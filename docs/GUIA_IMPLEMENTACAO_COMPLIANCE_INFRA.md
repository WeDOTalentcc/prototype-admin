# Guia de Implementação — LGPD/Fairness/PII/Rate-Limit/DLQ/Webhooks

> Este documento é um **blueprint acionável** para replicar em outro projeto os 6 pilares de compliance e infra já implementados na plataforma LIA (WeDOTalent). Cada seção traz: contratos, arquivos-modelo, trechos de código prontos para adaptar, env vars, testes recomendados e pegadinhas conhecidas.

**Stack origem:** FastAPI (Python 3.11) + SQLAlchemy 2.0 async + Alembic + Celery + RabbitMQ + Redis + PostgreSQL.

---

## Índice

1. [LGPD/GDPR Compliance Dedicado](#1-lgpdgdpr-compliance-dedicado)
2. [Fairness / Bias Detection](#2-fairness--bias-detection)
3. [PII Masking](#3-pii-masking)
4. [Rate Limiting](#4-rate-limiting)
5. [DLQ — Dead Letter Queue](#5-dlq--dead-letter-queue)
6. [Webhooks (Mailgun, MS Graph, genéricos)](#6-webhooks-mailgun-ms-graph-genéricos)
7. [Ordem de implementação recomendada](#7-ordem-de-implementação-recomendada)
8. [Matriz de env vars](#8-matriz-de-env-vars)

---

## 1. LGPD/GDPR Compliance Dedicado

### Objetivo
Atender: **Art. 18 LGPD** (direitos do titular), **Art. 20** (decisões automatizadas com revisão humana), **Art. 48** (notificação de incidentes à ANPD em 48h), **Art. 15/16** (retenção e anonimização), consentimento granular por finalidade.

### Estrutura de diretórios sugerida
```
app/
├── api/v1/
│   ├── lgpd_compliance.py          # Endpoints DPO, breaches, decisions
│   ├── data_subject_requests.py    # DSR endpoints
│   └── consent.py                  # Granular consent
├── domains/lgpd/
│   ├── services/
│   │   ├── granular_consent_service.py
│   │   ├── dsr_export_service.py
│   │   ├── lgpd_cleanup_service.py
│   │   └── consent_checker_service.py
│   └── repositories/
│       └── lgpd_repository.py
├── models/
│   ├── data_request.py
│   ├── breach_notification.py
│   ├── automated_decision.py
│   └── company_retention_policy.py
└── tasks/
    └── lgpd_cleanup_task.py        # Celery beat schedule diário
```

### Modelos essenciais

```python
# app/models/data_request.py
from enum import Enum
from sqlalchemy import String, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

class DSRType(str, Enum):
    ACCESS = "access"
    ERASURE = "erasure"
    PORTABILITY = "portability"
    RECTIFICATION = "rectification"
    OBJECTION = "objection"

class DSRStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"

class DataRequest(Base):
    __tablename__ = "data_requests"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    company_id: Mapped[str] = mapped_column(index=True)
    subject_id: Mapped[str]          # quem solicitou (email ou user_id)
    request_type: Mapped[DSRType] = mapped_column(SAEnum(DSRType))
    status: Mapped[DSRStatus]
    payload: Mapped[dict] = mapped_column(JSONB)   # dados exportados (quando aplicável)
    requested_at: Mapped[datetime]
    completed_at: Mapped[datetime | None]
    sla_deadline: Mapped[datetime]    # 15 dias corridos (LGPD)
```

```python
# app/models/automated_decision.py
class AutomatedDecision(Base):
    __tablename__ = "automated_decisions"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    company_id: Mapped[str] = mapped_column(index=True)
    subject_id: Mapped[str]
    decision_type: Mapped[str]        # ex: "screening_rejection"
    model_name: Mapped[str]
    model_version: Mapped[str]
    explanation_text: Mapped[str]     # explicação em linguagem natural
    input_snapshot: Mapped[dict] = mapped_column(JSONB)
    output_snapshot: Mapped[dict] = mapped_column(JSONB)
    requires_human_review: Mapped[bool] = mapped_column(default=False)
    human_review_status: Mapped[str | None]   # pending/approved/overturned
    human_reviewer_id: Mapped[str | None]
    human_review_at: Mapped[datetime | None]
    human_review_notes: Mapped[str | None]
    created_at: Mapped[datetime]
```

```python
# app/models/breach_notification.py
class BreachSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class BreachNotification(Base):
    __tablename__ = "breach_notifications"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    company_id: Mapped[str]
    severity: Mapped[BreachSeverity]
    detected_at: Mapped[datetime]
    affected_data_types: Mapped[list[str]] = mapped_column(ARRAY(String))
    affected_subjects_count: Mapped[int]
    description: Mapped[str]
    anpd_notified_at: Mapped[datetime | None]       # deadline 48h
    subjects_notified_at: Mapped[datetime | None]
    resolved_at: Mapped[datetime | None]
    remediation_actions: Mapped[list[str]] = mapped_column(ARRAY(String))
```

### Consentimento granular — 7 finalidades de IA

```python
# app/domains/lgpd/services/granular_consent_service.py
from enum import Enum

class ConsentPurpose(str, Enum):
    AI_SCREENING = "ai_screening"           # triagem automatizada
    AI_SCORING = "ai_scoring"               # pontuação/ranking
    AI_VIDEO_ANALYSIS = "ai_video"          # análise de entrevistas
    AI_COMPARISON = "ai_comparison"         # comparação entre candidatos
    DATA_RETENTION_EXTENDED = "data_retention"  # retenção além do padrão
    MARKETING = "marketing"
    ANALYTICS = "analytics"

class GranularConsentService:
    async def get_consent(self, subject_id: str, purpose: ConsentPurpose) -> bool:
        row = await self.repo.find(subject_id, purpose)
        return bool(row and row.granted and not row.revoked_at)

    async def update_batch(self, subject_id: str, updates: dict[ConsentPurpose, bool]):
        for purpose, granted in updates.items():
            await self.repo.upsert(subject_id, purpose, granted, actor=subject_id)

    async def require(self, subject_id: str, purpose: ConsentPurpose):
        if not await self.get_consent(subject_id, purpose):
            raise ConsentRequiredError(purpose)
```

### Endpoints REST obrigatórios

| Path | Método | Propósito |
|------|--------|-----------|
| `/api/v1/data-subject-requests` | POST / GET | Criar/listar DSR |
| `/api/v1/data-subject-requests/{id}/complete` | PUT | Marcar concluído (anexa export) |
| `/api/v1/data-subject-requests/{id}/reject` | PUT | Rejeitar com motivação |
| `/api/v1/consent/granular/{subject_id}` | GET | Resumo de consentimentos |
| `/api/v1/consent/granular/{subject_id}/update` | POST | Atualizar em lote |
| `/api/v1/lgpd/breaches` | POST / GET | Reportar/listar breaches |
| `/api/v1/lgpd/breaches/{id}/notify-anpd` | PUT | Marcar ANPD notificada (48h) |
| `/api/v1/lgpd/breaches/{id}/resolve` | PUT | Resolver com remediation |
| `/api/v1/lgpd/decisions` | POST / GET | Registrar decisões automatizadas |
| `/api/v1/lgpd/decisions/{id}/request-human-review` | POST | Art. 20 LGPD |
| `/api/v1/lgpd/schedule-deletion` | POST | Agendar exclusão |
| `/api/v1/admin/lgpd/run-cleanup` | POST | Disparar cleanup (`dry_run=true` default) |

### Job de limpeza (Celery beat)

```python
# app/tasks/lgpd_cleanup_task.py
from celery.schedules import crontab

@celery_app.task(name="lgpd.run_cleanup_daily", bind=True, max_retries=3)
def run_cleanup_daily(self, dry_run: bool = False):
    # 1. Encontrar candidatos rejeitados há > 90 dias sem consent de retenção estendida
    # 2. Anonimizar (name, email, cpf, phone → hash) ou deletar conforme política da empresa
    # 3. Registrar em audit_log cada ação
    # 4. Se dry_run=True, só contar
    return service.execute(dry_run=dry_run)

celery_app.conf.beat_schedule["lgpd-cleanup"] = {
    "task": "lgpd.run_cleanup_daily",
    "schedule": crontab(hour=2, minute=0),   # 02:00 UTC diário
}
```

### Política de retenção por empresa

```python
class CompanyRetentionPolicy(Base):
    company_id: Mapped[str] = mapped_column(primary_key=True)
    retention_months: Mapped[int] = mapped_column(default=24)
    auto_anonymize: Mapped[bool] = mapped_column(default=True)
    retain_rejected_days: Mapped[int] = mapped_column(default=90)
    retain_hired_years: Mapped[int] = mapped_column(default=5)   # obrigações trabalhistas
```

### Export DSR (formato estruturado)

```python
class DsrExportService:
    async def export(self, subject_id: str) -> dict:
        return {
            "profile": await self.profile_repo.get(subject_id),
            "applications": await self.app_repo.list_by_subject(subject_id),
            "evaluations": await self.eval_repo.list_by_subject(subject_id),
            "consents": await self.consent_repo.history(subject_id),
            "communications": await self.comm_repo.list_by_subject(subject_id),
            "automated_decisions": await self.decision_repo.list_by_subject(subject_id),
            "exported_at": datetime.utcnow().isoformat(),
            "format_version": "1.0",
        }
```

### Testes mínimos
- DSR de acesso retorna JSON com 100% dos dados do titular
- DSR de exclusão propaga para tabelas relacionadas (ON DELETE CASCADE ou service-level)
- Breach POST cria registro com `anpd_deadline = detected_at + 48h`
- AutomatedDecision sem consentimento de `ai_screening` → 403
- Cleanup `dry_run=true` não altera dados, só conta

### Pegadinhas
- **Hashing de email** (SHA-256) para conseguir buscar DSR após anonimização
- **LGPD Art. 16** exige retenção para "cumprimento de obrigação legal" — hired_years deve ser maior
- **Decisões automatizadas com impacto significativo** exigem explicação em linguagem natural, não só feature importance
- Secret do portal do titular deve ser **one-time token** com expiração

---

## 2. Fairness / Bias Detection

### Objetivo
Detectar e bloquear **preconceito** em prompts LLM e auditar estatisticamente **disparate impact** nos resultados dos agentes.

### Arquitetura em 3+1 camadas

| Camada | O que faz | Bloqueia? | Custo |
|--------|-----------|-----------|-------|
| **L1 — Regex direto** | Termos explícitos (idade, gênero, raça, bairros nobres, universidades "de ponta") | Sim | ~1ms |
| **L2 — Léxico implícito** | Proxies ("energia jovem", "boa aparência", "boa família") | Sim (ou soft warning) | ~2ms |
| **L3 — Semântico NLP** | Embeddings + classificador | Sim | ~50ms |
| **L4 — Presidio NER** (opt-in) | Entidades PII/demográficas avançadas | Não (logging) | ~200ms |

### Arquivos-modelo

```
app/shared/compliance/
├── fairness_guard.py              # motor principal
├── fairness_guard_middleware.py   # decorators/helpers
├── c3b_layer.py                   # L3 semântico
└── protected_attributes.yaml      # config
```

### Motor

```python
# app/shared/compliance/fairness_guard.py
from dataclasses import dataclass, field

@dataclass
class FairnessCheckResult:
    is_blocked: bool
    category: str | None = None          # "age", "gender", "race", "socioeconomic"
    confidence: float = 0.0
    blocked_terms: list[str] = field(default_factory=list)
    layer: str | None = None             # "L1", "L2", "L3", "L4"
    soft_warning: bool = False

class FairnessGuard:
    def __init__(self, enabled=True, blocking=True, soft_warnings=True):
        self.enabled = enabled
        self.blocking = blocking
        self.soft_warnings = soft_warnings
        self._l1_patterns = self._load_l1()
        self._l2_lexicon = self._load_l2()

    def check(self, text: str, context: dict | None = None) -> FairnessCheckResult:
        if not self.enabled:
            return FairnessCheckResult(is_blocked=False)

        # L1
        l1 = self._check_l1(text)
        if l1.is_blocked and self.blocking:
            self._log_audit(text, l1, blocked=True)
            return l1

        # L2
        l2 = self._check_l2(text)
        if l2.is_blocked:
            l2.soft_warning = not self.blocking and self.soft_warnings
            self._log_audit(text, l2, blocked=self.blocking)
            if self.blocking:
                return l2

        # L3 (se habilitado)
        if self._l3_enabled:
            l3 = self._check_l3_semantic(text)
            if l3.is_blocked:
                self._log_audit(text, l3, blocked=True)
                return l3

        return FairnessCheckResult(is_blocked=False)
```

### Termos exemplo (PT-BR)

```yaml
# app/config/protected_attributes.yaml
l1_direct:
  age:
    - "entre 20 e 30 anos"
    - "jovem"
    - "até 25 anos"
  gender:
    - "prefiro homens"
    - "somente mulheres"
  race:
    - "pessoa branca"
    - "pele clara"
  socioeconomic:
    - "bairro nobre"
    - "universidade de ponta"
    - "apenas USP"

l2_implicit:
  age_proxy:
    - "energia jovem"
    - "disposição de jovem"
  appearance_proxy:
    - "boa aparência"
    - "boa apresentação pessoal"
  class_proxy:
    - "boa família"
    - "berço bom"
```

### Uso em agentes/endpoints

```python
from app.shared.compliance.fairness_guard_middleware import check_fairness

@router.post("/jobs/{job_id}/description")
async def update_description(job_id: str, body: DescriptionUpdate):
    result = check_fairness(body.text, context={"endpoint": "job_description"})
    if result.is_blocked:
        raise HTTPException(422, detail={
            "error": "fairness_violation",
            "category": result.category,
            "terms": result.blocked_terms,
            "suggestion": "Remova referências a atributos demográficos protegidos",
        })
    # prosseguir...
```

### Bias Audit — Four-Fifths Rule (80% test)

```python
# app/shared/services/bias_audit_service.py
class BiasAuditService:
    DIMENSIONS = ["gender", "age_group", "disability", "region"]

    async def audit_job(self, job_id: str) -> BiasAuditSnapshot:
        snapshot = {}
        for dim in self.DIMENSIONS:
            rates = await self._selection_rates(job_id, dim)
            # rates = {"male": 0.45, "female": 0.25, "non_binary": 0.30}
            if rates:
                min_rate = min(rates.values())
                max_rate = max(rates.values())
                ratio = min_rate / max_rate if max_rate > 0 else 1.0
                snapshot[dim] = {
                    "rates": rates,
                    "disparate_impact_ratio": ratio,
                    "passes_four_fifths": ratio >= 0.8,
                }
        return await self.repo.save_snapshot(job_id, snapshot)
```

### Log de auditoria (LGPD-safe)

```python
class FairnessAuditLog(Base):
    id: Mapped[UUID]
    company_id: Mapped[str]
    query_hash: Mapped[str] = mapped_column(String(64))   # SHA-256, não guarda texto
    category: Mapped[str | None]
    blocked_terms: Mapped[list[str]] = mapped_column(JSONB)
    confidence: Mapped[float]
    is_blocked: Mapped[bool]
    is_soft_warning: Mapped[bool]
    context: Mapped[dict] = mapped_column(JSONB)   # endpoint, agent, user_id_hash
    created_at: Mapped[datetime]
```

### Env vars
```bash
FAIRNESS_GUARD_ENABLED=true
FAIRNESS_GUARD_BLOCKING_ENABLED=true
FAIRNESS_GUARD_SOFT_WARNINGS=true
FAIRNESS_LAYER3_ENABLED=false          # opt-in (custo LLM)
FAIRNESS_LAYER4_PRESIDIO_ENABLED=false # opt-in (NER)
```

### Testes mínimos
- L1 bloqueia "jovem de boa aparência" com `category=age+appearance`
- L2 registra soft_warning quando blocking=false
- Four-Fifths calcula corretamente com distribuição conhecida
- `query_hash` não colide para textos diferentes
- Log **nunca** armazena texto cru (só hash)

### Pegadinhas
- Inglês + Português: manter dois lexicons separados
- Falsos positivos em termos técnicos ("júnior/sênior" é OK em contexto de seniority)
- Context matters: "cor da pele" pode aparecer em vaga de maquiagem — usar whitelist por `context.endpoint`

---

## 3. PII Masking

### Objetivo
Nunca vazar PII em: **logs de aplicação**, **prompts enviados a LLMs**, **DLQ**, **respostas de erro**, **APIs de terceiros**.

### Estratégia em 4 camadas

```
┌──────────────────────────────────────────────────────┐
│ L1: Regex básico (CPF, email, telefone, RG, CNPJ)    │
│ L2: Quase-identificadores (ano formatura, idade)     │
│ L3: NER via spaCy/Presidio (PERSON, LOCATION, DATE)  │
│ L4: Criptografia em repouso (Fernet) + TTL indexes   │
└──────────────────────────────────────────────────────┘
```

### Arquivo principal

```python
# app/shared/pii_masking.py
import re
import logging
import hashlib

CPF_RE       = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
CNPJ_RE      = re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b")
EMAIL_RE     = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
PHONE_BR_RE  = re.compile(r"\(?\d{2}\)?\s?9?\d{4}-?\d{4}")
RG_RE        = re.compile(r"\b\d{1,2}\.\d{3}\.\d{3}-?[\dxX]\b")

def mask_pii_basic(text: str) -> str:
    text = CPF_RE.sub("***.***.***-**", text)
    text = CNPJ_RE.sub("**.***.***/****-**", text)
    text = EMAIL_RE.sub(lambda m: f"{m.group()[0]}***@***", text)
    text = PHONE_BR_RE.sub("(**) *****-****", text)
    text = RG_RE.sub("**.***.***-*", text)
    return text

class PIIMaskingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = mask_pii_basic(record.msg)
        if record.args:
            record.args = tuple(
                mask_pii_basic(a) if isinstance(a, str) else a
                for a in record.args
            )
        return True

def install_global_pii_masking():
    f = PIIMaskingFilter()
    root = logging.getLogger()
    root.addFilter(f)
    for handler in root.handlers:
        handler.addFilter(f)
```

### LLM prompt stripping

```python
def strip_pii_for_llm_prompt(prompt: str, enable_presidio: bool = False) -> str:
    prompt = mask_pii_basic(prompt)                              # L1
    prompt = _strip_quasi_identifiers(prompt)                    # L2
    if enable_presidio:
        prompt = _presidio_anonymize(prompt, language="pt")      # L3/L4
    return prompt

def _strip_quasi_identifiers(text: str) -> str:
    # idade explícita
    text = re.sub(r"\b\d{1,3}\s*anos\b", "[idade]", text, flags=re.I)
    # ano de formatura
    text = re.sub(r"(formad[oa]\s+em\s+)\d{4}", r"\1[ano]", text, flags=re.I)
    return text
```

### Criptografia de campos

```python
# app/shared/encryption/encrypted_field_mixin.py
from cryptography.fernet import Fernet
import os

_fernet = Fernet(os.environ["FIELD_ENCRYPTION_KEY"].encode())

def encrypt_field(value: str | None) -> bytes | None:
    if value is None:
        return None
    return _fernet.encrypt(value.encode())

def decrypt_field(token: bytes | None) -> str | None:
    if token is None:
        return None
    return _fernet.decrypt(token).decode()

def hash_field(value: str) -> str:
    return hashlib.sha256(value.lower().encode()).hexdigest()
```

### Migração dual-write (3 fases)

```python
# Fase 1: adicionar colunas _encrypted + _hash, continuar escrevendo plaintext
op.add_column("candidates", sa.Column("email_encrypted", sa.LargeBinary))
op.add_column("candidates", sa.Column("email_hash", sa.String(64), index=True))

# Fase 2: backfill + dual-write no código
# Fase 3: parar de escrever plaintext + drop coluna plaintext
```

### Env vars
```bash
PII_MASKING_ENABLE_GLOBAL=true
LLM_PROMPT_PII_STRIPPING_ENABLED=true
LLM_PROMPT_PRESIDIO_ENABLED=false
FIELD_ENCRYPTION_KEY=<gerada por: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">
```

### Testes
- `mask_pii_basic("CPF 123.456.789-00")` → contém `***.***.***-**`
- Logger filter: `log.info("email %s", "a@b.com")` → saída com `a***@***`
- Round-trip `decrypt(encrypt(x)) == x`
- Presidio OFF → não chama spaCy (latência)

### Pegadinhas
- Não mascarar em **tempo de escrita** no banco (destrói dados) — só em logs/LLM
- `hashlib.sha256(email.lower())` — sempre normalizar antes do hash para busca funcionar
- Cuidar de **structured logs** (JSON): o filter precisa processar campos aninhados
- Se usar `print()` em vez de logger, o filter **não pega**

---

## 4. Rate Limiting

### Objetivo
Proteger contra abuso (burst de requests, scraping, brute force) com granularidade **por usuário + por empresa (tenant)**, usando **sliding window** atômico em Redis.

### Arquivo principal

```python
# app/middleware/rate_limiter.py
import time
import asyncio
import redis.asyncio as aioredis
from fastapi import Request, HTTPException

class RateLimiter:
    LIMITS = {
        "per_minute_per_user": (600, 60),
        "per_hour_per_user": (20_000, 3600),
        "per_minute_per_company": (3_000, 60),
        "per_hour_per_company": (60_000, 3600),
    }
    RECONNECT_COOLDOWN = 30.0

    def __init__(self, redis_url: str):
        self._redis_url = redis_url
        self._redis: aioredis.Redis | None = None
        self._last_reconnect_attempt = 0.0
        self._in_memory: dict[str, list[float]] = {}

    async def _get_redis(self) -> aioredis.Redis | None:
        if self._redis is not None:
            return self._redis
        now = time.time()
        if now - self._last_reconnect_attempt < self.RECONNECT_COOLDOWN:
            return None
        self._last_reconnect_attempt = now
        try:
            r = aioredis.from_url(self._redis_url, socket_timeout=0.5)
            await r.ping()
            self._redis = r
            return r
        except Exception:
            return None

    async def check(self, key: str, limit: int, window_sec: int) -> tuple[bool, int]:
        """Retorna (allowed, remaining)."""
        r = await self._get_redis()
        if r is not None:
            return await self._check_redis(r, key, limit, window_sec)
        return self._check_memory(key, limit, window_sec)

    async def _check_redis(self, r, key, limit, window_sec):
        now = time.time()
        async with r.pipeline(transaction=True) as pipe:
            pipe.zremrangebyscore(key, 0, now - window_sec)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, window_sec + 10)
            _, _, count, _ = await pipe.execute()
        return count <= limit, max(0, limit - count)

    def _check_memory(self, key, limit, window_sec):
        now = time.time()
        q = self._in_memory.setdefault(key, [])
        self._in_memory[key] = [t for t in q if t > now - window_sec]
        self._in_memory[key].append(now)
        count = len(self._in_memory[key])
        return count <= limit, max(0, limit - count)

class RateLimitMiddleware:
    EXCLUDED_PATHS = ("/health", "/docs", "/openapi.json", "/redoc", "/metrics")

    def __init__(self, app, limiter: RateLimiter):
        self.app = app
        self.limiter = limiter

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        path = scope["path"]
        if any(path.startswith(p) for p in self.EXCLUDED_PATHS):
            return await self.app(scope, receive, send)

        request = Request(scope, receive)
        user_id = self._extract_user(request)
        company_id = self._extract_company(request)

        for scope_name, (limit, window) in RateLimiter.LIMITS.items():
            if "user" in scope_name and user_id:
                key = f"rl:user:{user_id}:{scope_name}"
            elif "company" in scope_name and company_id:
                key = f"rl:company:{company_id}:{scope_name}"
            else:
                continue
            allowed, remaining = await self.limiter.check(key, limit, window)
            if not allowed:
                return await self._reject(send, limit, window, remaining)
        return await self.app(scope, receive, send)

    async def _reject(self, send, limit, window, remaining):
        headers = [
            (b"content-type", b"application/json"),
            (b"retry-after", str(window).encode()),
            (b"x-ratelimit-limit", str(limit).encode()),
            (b"x-ratelimit-remaining", str(remaining).encode()),
        ]
        await send({"type": "http.response.start", "status": 429, "headers": headers})
        await send({"type": "http.response.body", "body": b'{"error":"rate_limit_exceeded"}'})
```

### Registro

```python
# app/main.py
from app.middleware.rate_limiter import RateLimiter, RateLimitMiddleware

limiter = RateLimiter(redis_url=os.environ["REDIS_URL"])
app.add_middleware(RateLimitMiddleware, limiter=limiter)
```

### Limites sugeridos

| Escopo | Por minuto | Por hora |
|--------|-----------|----------|
| Usuário | 600 | 20.000 |
| Empresa (tenant) | 3.000 | 60.000 |

> Ajustar por endpoint crítico com decorator `@custom_rate_limit(100, 60)` caso necessário.

### Testes
- 601º request dentro de 60s → 429
- Redis offline → fallback in-memory mantém proteção local
- Reconnect cooldown evita storm de conexões
- Headers `Retry-After` e `X-RateLimit-*` presentes

### Pegadinhas
- Fallback in-memory **não compartilha entre workers** — aceitar essa degradação ou usar Redis como hard-dep
- `ZADD` com timestamp duplicado: usar `{now}:{uuid}` como member se preocupar com colisão em alta concorrência
- Paths excluídos devem incluir health-checks do Kubernetes/Load Balancer

---

## 5. DLQ — Dead Letter Queue

### Objetivo
Capturar tasks Celery que falharam após todas as retries, com **PII masking**, **TTL** e **endpoints admin** para inspecionar/re-enfileirar/limpar.

### Arquitetura

```
Celery task falha
      ↓ (on_failure)
DLQService.push_failure()
      ↓
Redis LIST `dlq:{queue}` (LPUSH + LTRIM MAX_ENTRIES=1000)
      ↓
Redis SET `dlq:index` (registra filas com entradas)
      ↓
TTL 7 dias
      ↓
Admin API lista/requeue/clear
      ↓
Bell notification se task é crítica
```

### Serviço

```python
# app/shared/resilience/dlq_service.py
import json
import uuid
from datetime import datetime
import redis.asyncio as aioredis
from app.shared.pii_masking import mask_pii_basic

DLQ_TTL = 7 * 24 * 3600
MAX_ENTRIES = 1000
SENSITIVE_KEYS = {"password", "token", "secret", "cpf", "email", "phone", "api_key"}
CRITICAL_TASKS = {
    "lgpd.run_cleanup_daily",
    "audit.apply_lifecycle_policy",
    "drift.run_batch",
    "followup.process_pending",
}

def _mask_kwargs(kwargs: dict) -> dict:
    out = {}
    for k, v in kwargs.items():
        if k.lower() in SENSITIVE_KEYS:
            out[k] = "***"
        elif isinstance(v, str):
            out[k] = mask_pii_basic(v)
        elif isinstance(v, dict):
            out[k] = _mask_kwargs(v)
        else:
            out[k] = v
    return out

class DLQService:
    def __init__(self, redis_url: str):
        self._redis = aioredis.from_url(redis_url)

    async def push_failure(self, task_name, queue, args, kwargs, exc, tb, retries, company_id=None):
        entry = {
            "entry_id": str(uuid.uuid4()),
            "task_name": task_name,
            "queue": queue,
            "args": list(args),
            "kwargs": _mask_kwargs(kwargs or {}),
            "exception_type": type(exc).__name__,
            "exception_msg": str(exc),
            "traceback": tb,
            "retries": retries,
            "company_id": company_id,
            "failed_at": datetime.utcnow().isoformat(),
        }
        key = f"dlq:{queue}"
        async with self._redis.pipeline() as pipe:
            pipe.lpush(key, json.dumps(entry))
            pipe.ltrim(key, 0, MAX_ENTRIES - 1)
            pipe.expire(key, DLQ_TTL)
            pipe.sadd("dlq:index", queue)
            await pipe.execute()

        if task_name in CRITICAL_TASKS:
            await self._notify_bell(task_name, entry)

    async def list_queues(self) -> list[dict]:
        queues = await self._redis.smembers("dlq:index")
        out = []
        for q in queues:
            count = await self._redis.llen(f"dlq:{q.decode()}")
            out.append({"queue": q.decode(), "count": count})
        return out

    async def list_entries(self, queue: str, limit: int = 50) -> list[dict]:
        raw = await self._redis.lrange(f"dlq:{queue}", 0, limit - 1)
        return [json.loads(r) for r in raw]

    async def requeue(self, queue: str, entry_id: str, celery_app) -> bool:
        entries = await self.list_entries(queue, limit=MAX_ENTRIES)
        target = next((e for e in entries if e["entry_id"] == entry_id), None)
        if not target:
            return False
        celery_app.send_task(
            target["task_name"],
            args=target["args"],
            kwargs=target["kwargs"],
            queue=queue,
        )
        # Remover entrada (LREM)
        await self._redis.lrem(f"dlq:{queue}", 1, json.dumps(target))
        return True

    async def clear(self, queue: str):
        await self._redis.delete(f"dlq:{queue}")
        await self._redis.srem("dlq:index", queue)
```

### Base task Celery

```python
# app/shared/async_processing/lia_task.py
from celery import Task

class LIATask(Task):
    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True
    max_retries = 5
    acks_late = True
    reject_on_worker_lost = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        import asyncio
        asyncio.run(dlq_service.push_failure(
            task_name=self.name,
            queue=self.request.delivery_info.get("routing_key", "celery"),
            args=args,
            kwargs=kwargs,
            exc=exc,
            tb=str(einfo),
            retries=self.request.retries,
            company_id=(kwargs or {}).get("company_id"),
        ))

@celery_app.task(base=LIATask, name="my.task")
def my_task(...):
    ...
```

### Endpoints admin

| Path | Método | Descrição |
|------|--------|-----------|
| `/api/v1/admin/dlq` | GET | Lista filas com contagem |
| `/api/v1/admin/dlq/{queue}` | GET | Lista últimas 50 entradas |
| `/api/v1/admin/dlq/{queue}/{entry_id}/requeue` | POST | Re-enfileira |
| `/api/v1/admin/dlq/{queue}` | DELETE | Limpa fila |

### Testes
- Task falha 5x → entra na DLQ
- `kwargs = {"email": "a@b.com", "password": "x"}` → stored com `email: "a***@***"` e `password: "***"`
- Requeue executa nova task com mesmos args/kwargs (mascarados ou originais? — **originais**, re-puxar do backend)
- LTRIM mantém só últimas 1000
- Task crítica dispara Bell

### Pegadinhas
- `asyncio.run()` dentro de `on_failure`: se o task já roda em event loop, usar `asyncio.create_task` + sync bridge
- Kwargs mascarados no **display**, mas requeue precisa dos originais — solução: salvar também payload cifrado, ou re-buscar no banco
- `LREM` com JSON serializado: cuidado com ordering de keys (usar `sort_keys=True` ao serializar)

---

## 6. Webhooks (Mailgun, MS Graph, genéricos)

### Objetivo
**Receber** webhooks externos com validação de assinatura e **emitir** webhooks para clientes com HMAC-SHA256.

### Modelo

```python
# app/models/webhook.py
from enum import Enum

class WebhookEvent(str, Enum):
    AGENT_EXECUTION_COMPLETED = "agent.execution.completed"
    AGENT_EXECUTION_FAILED = "agent.execution.failed"
    CANDIDATE_CREATED = "candidate.created"
    CANDIDATE_ENRICHED = "candidate.enriched"
    # ... adicionar conforme domínio

class Webhook(Base):
    __tablename__ = "webhooks"
    id: Mapped[UUID]
    company_id: Mapped[str] = mapped_column(index=True)
    name: Mapped[str]
    url: Mapped[str]                              # max 2048
    events: Mapped[list[str]] = mapped_column(ARRAY(String))
    secret: Mapped[str]                           # random 32 bytes, retornado só uma vez
    is_active: Mapped[bool] = mapped_column(default=True)
    total_deliveries: Mapped[int] = mapped_column(default=0)
    total_failures: Mapped[int] = mapped_column(default=0)
    last_delivery_at: Mapped[datetime | None]
    last_status_code: Mapped[int | None]
    last_error: Mapped[str | None]
    created_by: Mapped[str]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
```

### Dispatcher (outbound)

```python
# app/services/webhook_dispatcher.py
import hmac
import hashlib
import json
import time
import httpx

class WebhookDispatcher:
    MAX_RETRIES = 5
    BACKOFF_BASE = 2   # 2, 4, 8, 16, 32 sec

    async def dispatch(self, webhook: Webhook, event_type: str, data: dict):
        if event_type not in webhook.events or not webhook.is_active:
            return
        payload = {
            "webhook_id": str(webhook.id),
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": data,
        }
        body = json.dumps(payload, sort_keys=True).encode()
        timestamp = str(int(time.time()))
        sig_base = f"{timestamp}.".encode() + body
        signature = hmac.new(webhook.secret.encode(), sig_base, hashlib.sha256).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": f"sha256={signature}",
            "X-Webhook-Timestamp": timestamp,
            "X-Webhook-Event": event_type,
        }

        for attempt in range(self.MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    r = await client.post(webhook.url, content=body, headers=headers)
                await self._record(webhook, r.status_code, None)
                if 200 <= r.status_code < 300:
                    return
            except Exception as e:
                await self._record(webhook, None, str(e))
            await asyncio.sleep(self.BACKOFF_BASE ** attempt)
        # Esgotou retries → alerta
```

### Validação (cliente)

```python
# documentar para quem consome nossos webhooks:
def verify_signature(body: bytes, timestamp: str, signature_header: str, secret: str) -> bool:
    if signature_header.startswith("sha256="):
        signature_header = signature_header[7:]
    # Proteção contra replay (5 minutos)
    if abs(time.time() - int(timestamp)) > 300:
        return False
    sig_base = f"{timestamp}.".encode() + body
    expected = hmac.new(secret.encode(), sig_base, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)
```

### Mailgun (inbound)

```python
# app/api/v1/mailgun_webhooks.py
from fastapi import APIRouter, Request, HTTPException
import hmac, hashlib, os, time

router = APIRouter()
MAILGUN_SIGNING_KEY = os.environ["MAILGUN_WEBHOOK_SIGNING_KEY"]
MAX_TIMESTAMP_AGE = 300

@router.post("/webhooks/mailgun")
async def mailgun_webhook(request: Request):
    payload = await request.json()
    sig = payload.get("signature", {})
    timestamp = sig.get("timestamp")
    token = sig.get("token")
    signature = sig.get("signature")

    if not all([timestamp, token, signature]):
        raise HTTPException(400, "missing signature fields")
    if abs(time.time() - int(timestamp)) > MAX_TIMESTAMP_AGE:
        raise HTTPException(401, "timestamp too old")

    expected = hmac.new(
        MAILGUN_SIGNING_KEY.encode(),
        f"{timestamp}{token}".encode(),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(401, "invalid signature")

    event_data = payload.get("event-data", {})
    event = event_data.get("event")
    status_map = {
        "delivered": "delivered",
        "failed": "failed",
        "opened": "read",
        "complained": "complained",
        "unsubscribed": "unsubscribed",
    }
    # processar: atualizar status de email_log usando event_data['message']['headers']['message-id']
    return {"ok": True}
```

### MS Graph (inbound)

```python
# app/api/v1/microsoft_graph.py
@router.post("/webhooks/microsoft-graph")
async def ms_graph_webhook(request: Request):
    validation_token = request.query_params.get("validationToken")
    if validation_token:
        # Handshake inicial — echo do token como text/plain
        return Response(content=validation_token, media_type="text/plain")

    body = await request.json()
    for notification in body.get("value", []):
        # validar clientState (definido na subscription creation)
        if notification.get("clientState") != os.environ["MS_GRAPH_CLIENT_STATE"]:
            continue
        resource = notification.get("resource")        # ex: "Users/{id}/messages/{id}"
        change_type = notification.get("changeType")   # created/updated/deleted
        # processar
    return Response(status_code=202)
```

### Endpoints de gerenciamento

| Path | Método | Descrição |
|------|--------|-----------|
| `/api/v1/webhooks/events` | GET | Lista tipos de eventos disponíveis |
| `/api/v1/webhooks` | POST | Criar (retorna `secret` uma única vez) |
| `/api/v1/webhooks` | GET | Listar (não expõe secret) |
| `/api/v1/webhooks/{id}` | PATCH | Atualizar |
| `/api/v1/webhooks/{id}` | DELETE | Remover |
| `/api/v1/webhooks/{id}/test` | POST | Enviar payload de teste |
| `/api/v1/webhooks/{id}/deliveries` | GET | Histórico de deliveries |

### Testes
- HMAC válido passa, inválido → 401
- Timestamp > 5 min → 401 (replay protection)
- Dispatcher retry com backoff exponencial
- `WebhookEvent.AGENT_EXECUTION_COMPLETED` só dispara para webhooks que têm esse event na lista
- MS Graph `validationToken` handshake responde `text/plain`

### Pegadinhas
- Mailgun usa `sha256(timestamp + token)`, GitHub usa `sha256(body)`, Stripe usa `timestamp.body` — **cada provider tem seu esquema**
- Sempre usar `hmac.compare_digest` (timing-safe), nunca `==`
- `httpx.AsyncClient` dentro de worker: cuidar do `follow_redirects=False` para evitar SSRF
- `url` do webhook deve ser validada: bloquear `localhost`, `127.0.0.1`, ranges privados (RFC 1918)
- Expor `secret` somente na **criação**; GET nunca retorna

---

## 7. Ordem de implementação recomendada

Para minimizar retrabalho, implementar nesta ordem:

1. **PII Masking** (base — usado por todos os outros)
2. **Rate Limiting** (barato, protege durante desenvolvimento dos demais)
3. **DLQ** (requer Celery já configurado; protege produção cedo)
4. **Webhooks** (consome dispatcher + HMAC; usa DLQ para falhas)
5. **LGPD** (depende de audit_log, consent, encryption já prontos)
6. **Fairness/Bias** (depende de logging com PII masking + audit_log)

Cada item é **deployável isoladamente** via feature flag (`*_ENABLED=false` default).

---

## 8. Matriz de env vars

```bash
# ── PII Masking ───────────────────────────────────────────
PII_MASKING_ENABLE_GLOBAL=true
LLM_PROMPT_PII_STRIPPING_ENABLED=true
LLM_PROMPT_PRESIDIO_ENABLED=false
FIELD_ENCRYPTION_KEY=<Fernet.generate_key()>

# ── Rate Limiting ─────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0
RATE_LIMIT_ENABLED=true

# ── DLQ ───────────────────────────────────────────────────
DLQ_TTL_SECONDS=604800
DLQ_MAX_ENTRIES=1000
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672/
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# ── Webhooks ──────────────────────────────────────────────
MAILGUN_WEBHOOK_SIGNING_KEY=<from-mailgun-dashboard>
MS_GRAPH_CLIENT_STATE=<random-secret>
AZURE_TENANT_ID=...
AZURE_CLIENT_ID=...
AZURE_CLIENT_SECRET=...
WEBHOOK_MAX_RETRIES=5
WEBHOOK_TIMEOUT_SECONDS=10

# ── LGPD ──────────────────────────────────────────────────
LGPD_DPO_EMAIL=dpo@company.com
LGPD_DEFAULT_RETENTION_MONTHS=24
LGPD_RETAIN_REJECTED_DAYS=90
LGPD_RETAIN_HIRED_YEARS=5
ANPD_NOTIFICATION_DEADLINE_HOURS=48

# ── Fairness ──────────────────────────────────────────────
FAIRNESS_GUARD_ENABLED=true
FAIRNESS_GUARD_BLOCKING_ENABLED=true
FAIRNESS_GUARD_SOFT_WARNINGS=true
FAIRNESS_LAYER3_ENABLED=false
FAIRNESS_LAYER4_PRESIDIO_ENABLED=false
```

---

## Referências (arquivos do projeto LIA para consulta)

| Tópico | Arquivo canônico |
|--------|------------------|
| LGPD | `lia-agent-system/app/api/v1/lgpd_compliance.py` |
| LGPD | `lia-agent-system/app/domains/lgpd/services/granular_consent_service.py` |
| LGPD | `lia-agent-system/app/domains/lgpd/services/dsr_export_service.py` |
| LGPD | `lia-agent-system/alembic/versions/053_add_company_retention_policy.py` |
| Fairness | `lia-agent-system/app/shared/compliance/fairness_guard.py` |
| Fairness | `lia-agent-system/app/shared/services/bias_audit_service.py` |
| Fairness | `lia-agent-system/app/config/protected_attributes.yaml` |
| PII | `lia-agent-system/app/shared/pii_masking.py` |
| PII | `lia-agent-system/app/shared/encryption/encrypted_field_mixin.py` |
| PII | `lia-agent-system/alembic/versions/060_encrypt_pii_fields_and_ttl_indexes.py` |
| Rate Limit | `lia-agent-system/app/middleware/rate_limiter.py` |
| DLQ | `lia-agent-system/app/shared/resilience/dlq_service.py` |
| DLQ | `lia-agent-system/app/api/v1/admin_dlq.py` |
| Webhook | `lia-agent-system/app/api/v1/webhooks.py` |
| Webhook | `lia-agent-system/app/api/v1/mailgun_webhooks.py` |
| Webhook | `lia-agent-system/app/api/v1/microsoft_graph.py` |
| Webhook | `lia-agent-system/app/services/webhook_dispatcher.py` |
