# LIA — Master Doc de Vantagens Arquiteturais + Guia de Implementação em LangChain/LangGraph

> Todo o que a LIA tem de diferencial em relação a uma baseline de agente ATS (ex.: `recruiter_agent_v5`), com a evidência no código e um roteiro prático de **como portar cada camada para um projeto LangChain + LangGraph novo**.

Este doc é o ponto único de entrada. Cada seção tem:
- **O que é** e por que importa
- **Como a LIA faz** (arquivo canônico, mecanismo em ≤5 bullets, snippet real)
- **Como replicar em LangChain/LangGraph** (snippet pronto de copiar/colar)

---

## Índice

1. [Tabela executiva de vantagens](#1-tabela-executiva)
2. [Ordem de adoção recomendada](#2-ordem-de-adoção)
3. **Core Agent Layer**
   - [3.1 LangGraph base com PII auto-strip](#31-langgraph-base-com-pii-auto-strip)
   - [3.2 Tool Registry + ACL](#32-tool-registry--acl)
   - [3.3 Multi-provider LLM com fallback](#33-multi-provider-llm)
   - [3.4 CascadedRouter 8 tiers](#34-cascadedrouter)
   - [3.5 Sourcing sub-agents + Juicebox calibration](#35-sourcing-sub-agents)
   - [3.6 Studio Agents (Tier 7)](#36-studio-agents)
4. **Safety & Compliance**
   - [4.1 Multi-tenant isolation](#41-multi-tenant-isolation)
   - [4.2 PII masking pipeline](#42-pii-masking)
   - [4.3 Audit trail universal](#43-audit-trail)
   - [4.4 FairnessGuard 3 camadas](#44-fairnessguard)
   - [4.5 HITL gates](#45-hitl-gates)
   - [4.6 Granular Consent (LGPD)](#46-granular-consent)
   - [4.7 Data Subject Rights](#47-dsr)
   - [4.8 Bias Audit + Four-Fifths](#48-bias-audit)
   - [4.9 Model Drift Detection](#49-model-drift)
   - [4.10 PolicyEngine (sector defaults)](#410-policyengine)
5. **Resilience & Scale**
   - [5.1 Circuit Breakers](#51-circuit-breakers)
   - [5.2 Event Store (append-only)](#52-event-store)
   - [5.3 RAG híbrido + pgvector](#53-rag-híbrido)
   - [5.4 Celery 4-queue priority](#54-celery)
   - [5.5 Multi-channel notifications](#55-notifications)
6. **Business Layer**
   - [6.1 Digital Twins](#61-digital-twins)
   - [6.2 WSI Interview (StateGraph)](#62-wsi)
7. **Observability & Ops**
   - [7.1 LangSmith tracing + cost](#71-langsmith)
   - [7.2 Runbooks operacionais](#72-runbooks)
   - [7.3 SOC2/ISO/Trust Center](#73-compliance-frameworks)

---

## 1. Tabela Executiva

| # | Vantagem | Baseline | LIA | Impacto |
|---|----------|----------|-----|---------|
| 1 | Tools registradas | 73 | **260+ tools** em 48 arquivos (74 no YAML canônico) | Cobertura |
| 2 | LLM providers | 1 | **3** com fallback automático | Resiliência |
| 3 | Sourcing sub-agents | 1 | **10 ReAct especializados** | Decomposição |
| 4 | HITL gates | 0 | **3 gates** (Job Wizard, Pipeline, WSI) | Compliance |
| 5 | Fairness patterns | ~20 | **~210 regex + 70 implicit** em 3 camadas | LGPD/EU AI Act |
| 6 | Router tiers | ReAct único | **8 tiers** (cache → regex → LLM cascade → ReAct) | Custo -80% |
| 7 | Custom agents | ❌ | **Tier 7** com marketplace | Extensibilidade |
| 8 | Multi-tenant | implícito | **ContextVar + TenantProviderRegistry** | Isolamento forte |
| 9 | PII masking | ❌ | **3 camadas** (regex + Presidio opcional) | LGPD Art. 11 |
| 10 | Audit trail | logs | **AuditCallback universal + SOX 7 anos** | SOX/BCB 498 |
| 11 | Circuit breakers | ❌ | **11 breakers** + admin API | SLO-driven |
| 12 | Event Store | ❌ | **DomainEvent append-only** + reconstrução | Event sourcing |
| 13 | Bias Audit | ❌ | **Four-Fifths + chi-square** snapshots | EEOC |
| 14 | Model Drift | ❌ | **4 triggers diários** (score/approval/cost/latency) | MLOps |
| 15 | PolicyEngine | ❌ | **6 setores** com defaults + audit | RPO |
| 16 | RAG híbrido | ❌ | **BM25 + pgvector** com alpha blending | Busca semântica |
| 17 | Celery queues | 1 | **4 priority queues** + DLQ | SLA |
| 18 | Notifications | 1 canal | **7 canais** (bell/email/teams/wpp/chat/push/in-app) | UX |
| 19 | Digital Twins | ❌ | **Embedding K-NN** SME-personas | Auto-calibração |
| 20 | WSI | ❌ | **StateGraph Dreyfus/Bloom/BigFive** | Metodologia |
| 21 | Observability | logs | **LangSmith traced + cost per call** | Debug |
| 22 | Runbooks | ❌ | **RUNBOOK_DEGRADATION + INCIDENT_PLAYBOOKS** | On-call |
| 23 | Trust Center | ❌ | **SOC2/ISO/SOX/LGPD/GDPR/BACEN** tracking | Enterprise |

---

## 2. Ordem de Adoção

**Fase 1 — fundação (semanas 1–3):**
1. LangGraph base com PII strip (§3.1)
2. Tool Registry + ACL (§3.2)
3. Multi-tenant ContextVar (§4.1)
4. Multi-provider com fallback (§3.3)

**Fase 2 — safety (semanas 4–6):**
5. Audit trail (§4.3)
6. FairnessGuard Layer 1+2 (§4.4)
7. HITL gates em ações destrutivas (§4.5)
8. Circuit breakers (§5.1)

**Fase 3 — eficiência (semanas 7–9):**
9. CascadedRouter tiers 0–5 (§3.4)
10. RAG híbrido (§5.3)
11. LangSmith (§7.1)

**Fase 4 — compliance avançado (semanas 10+):**
12. Bias Audit (§4.8)
13. Model Drift (§4.9)
14. Granular Consent + DSR (§4.6, §4.7)
15. Event Store (§5.2)

**Fase 5 — extensibilidade:**
16. Tier 7 Studio Agents (§3.6)
17. Digital Twins (§6.1)

---

## 3. Core Agent Layer

### 3.1 LangGraph Base com PII Auto-Strip

**O que é:** base class de todos os agentes ReAct da LIA. Adiciona PII masking automático, callbacks de audit, tool timeouts e checkpointing.

**LIA:** `lia-agent-system/libs/agents-core/lia_agents_core/langgraph_react_base.py` (525 linhas).
- `LangGraphReActBase(LangGraphBase)` usa `create_react_agent` + `TimedToolNode`
- `_sanitize_messages_pii()` strippa `HumanMessage`/`AIMessage` antes do grafo (preserva `SystemMessage`)
- `TimedToolNode` — wrapper de `ToolNode` com `default_timeout_seconds=15` + overrides por tool
- Checkpointer: `PostgresSaver` em prod, `MemorySaver` em dev
- `AuditCallback` + `StreamingCallback` injetados via `config["callbacks"]`

```python
tool_node = TimedToolNode(
    tools=tools, domain=self.domain_name,
    default_timeout_seconds=15,
    tool_timeouts=self._per_tool_timeouts)
self._compiled = create_react_agent(
    model=model, tools=tool_node, checkpointer=self._checkpointer)
```

**Implementação portável:**

```python
# shared/agents/base.py
from abc import ABC, abstractmethod
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import HumanMessage, AIMessage
from shared.pii import strip_pii_for_llm_prompt

class LangGraphReActBase(ABC):
    enable_pii_strip: bool = True
    tool_timeout_seconds: int = 15

    @abstractmethod
    def tools(self) -> list: ...
    @abstractmethod
    def system_prompt(self) -> str: ...
    @abstractmethod
    def model(self): ...

    def _sanitize(self, messages):
        if not self.enable_pii_strip:
            return messages
        out = []
        for m in messages:
            if isinstance(m, (HumanMessage, AIMessage)):
                m = type(m)(content=strip_pii_for_llm_prompt(m.content))
            out.append(m)
        return out

    def build(self, checkpointer):
        return create_react_agent(
            model=self.model(),
            tools=self.tools(),
            state_modifier=self.system_prompt(),
            checkpointer=checkpointer,
        )

    async def invoke(self, messages, thread_id):
        messages = self._sanitize(messages)
        agent = self.build(PostgresSaver.from_conn_string(os.getenv("DB_URL")))
        return await agent.ainvoke(
            {"messages": messages},
            config={"configurable": {"thread_id": thread_id},
                    "recursion_limit": self.tool_timeout_seconds},
        )
```

---

### 3.2 Tool Registry + ACL

**O que é:** catalogação declarativa de todas as tools, com ACL por tenant + agente + escopo (multi-nível).

**LIA:** `lia-agent-system/app/tools/registry.py` + `tool_permissions.yaml` + `tool_registry_metadata.yaml`.
- Cada tool é `ToolDefinition(name, description, parameters, handler, allowed_agents, scope)`
- Escopos: `GLOBAL | TALENT_FUNNEL | JOB_TABLE | IN_JOB | UNIVERSAL`
- `tool_permissions.yaml` define permissões globais + overrides por tenant
- Validação cruzada código ↔ YAML no startup (`validate_registry_against_yaml`)
- **260+ tools em 48 arquivos** — ver `LIA_TOOLS_CATALOG.md`

**Implementação portável:** ver seção 6 do `LIA_TOOLS_CATALOG.md` (documento irmão).

---

### 3.3 Multi-Provider LLM

**O que é:** fallback automático entre providers quando um falha ou o circuit breaker abre.

**LIA:** `lia-agent-system/app/shared/providers/llm_factory.py` (544 linhas).
- `LLMProviderFactory` — registro de classes de provider
- `ProviderContainer` — DI por tenant com `primary + fallback_order`
- `FALLBACK_ORDER = ["gemini", "claude", "openai"]`
- `TenantProviderRegistry` singleton: `_containers[tenant_id] → ProviderContainer`
- API key do tenant se presente, senão chave do sistema

```python
FALLBACK_ORDER: list[str] = ["gemini", "claude", "openai"]
self._primary = primary or os.environ.get("LLM_DEFAULT_PROVIDER", "gemini")
self._fallback_order = [self._primary] + [p for p in FALLBACK_ORDER if p != self._primary]
```

**Implementação portável:**

```python
# shared/providers/factory.py
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from dataclasses import dataclass

FALLBACK_ORDER = ["gemini", "claude", "openai"]

@dataclass
class TenantConfig:
    tenant_id: str
    primary: str = "gemini"
    api_keys: dict = None  # {"claude": "...", ...}

def _make_provider(name: str, api_key: str | None = None):
    match name:
        case "claude":
            return ChatAnthropic(model="claude-sonnet-4-6", api_key=api_key) if api_key else ChatAnthropic(model="claude-sonnet-4-6")
        case "gemini":
            return ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key) if api_key else ChatGoogleGenerativeAI(model="gemini-2.5-flash")
        case "openai":
            return ChatOpenAI(model="gpt-4o", api_key=api_key) if api_key else ChatOpenAI(model="gpt-4o")

def build_llm(config: TenantConfig):
    order = [config.primary] + [p for p in FALLBACK_ORDER if p != config.primary]
    llms = [_make_provider(p, (config.api_keys or {}).get(p)) for p in order]
    return llms[0].with_fallbacks(llms[1:])  # nativo LangChain

# Cache por tenant
_registry: dict[str, object] = {}
def get_llm_for_tenant(tenant_id: str, config: TenantConfig):
    if tenant_id not in _registry:
        _registry[tenant_id] = build_llm(config)
    return _registry[tenant_id]
```

---

### 3.4 CascadedRouter

**O que é:** 8 tiers de roteamento em ordem crescente de custo. Primeiro que retorna confiança suficiente ganha.

**LIA:** `lia-agent-system/app/orchestrator/cascaded_router.py` (792 linhas).

| Tier | Mecanismo | Custo |
|------|-----------|-------|
| 0 | MemoryResolver (pronomes) | ~0 |
| 1 | LRU hash in-process | ~0 |
| 2 | Redis hash cache | ~1ms |
| 3 | pgvector cosine | ~10ms |
| 4 | FastRouter (regex) | ~0 |
| 5 | LLM cascade Haiku→Sonnet→Opus | $$ |
| 6 | AutonomousReAct (fallback) | $$$ |
| 7 | Studio Agent matcher | $$ |
| — | clarification_needed | — |

**Implementação portável:** ver `TIER_6_7_REACT_FALLBACK_AND_STUDIO_AGENTS.md` (documento irmão).

---

### 3.5 Sourcing Sub-Agents + Juicebox Calibration

**O que é:** 10 sub-agentes ReAct especializados, cada um com pool próprio de tools, orquestrados sequencialmente por stage do pipeline. Calibração tipo Juicebox: feedback humano ajusta `search_strategy` automaticamente.

**LIA:**
- Agents: `lia-agent-system/app/domains/sourcing/agents/` (11 arquivos `*_agent.py`)
- Orchestrator: `lia-agent-system/app/services/sourcing_agent_orchestrator.py`
- Persistência: `SourcingAgent` + `SourcingAgentSignal` tables

Sub-agentes: `planner`, `search`, `enrich`, `engagement`, `github`, `stackoverflow`, `diversity`, `passive_pipeline`, `nurture_sequence`, `referral`.

Calibração:
1. Cada feedback (approve/reject) vira `SourcingAgentSignal`
2. LLM extrai critérios do feedback → muta `search_strategy` JSON
3. `calibration_v += 1`
4. Min 3 aprovações antes de promover signals a estratégia

**Implementação portável:**

```python
# domains/sourcing/orchestrator.py
from enum import StrEnum
from sqlalchemy.dialects.postgresql import JSONB
from langgraph.graph import StateGraph, END

class SourcingStage(StrEnum):
    PLAN = "plan"
    SEARCH = "search"
    ENRICH = "enrich"
    ENGAGE = "engage"

STAGE_TO_AGENT = {
    SourcingStage.PLAN: PlannerAgent,
    SourcingStage.SEARCH: SearchAgent,
    SourcingStage.ENRICH: EnrichAgent,
    SourcingStage.ENGAGE: EngagementAgent,
}

async def run_sourcing(job_id: str, stages: list[SourcingStage]):
    state = {"job_id": job_id, "candidates": []}
    for stage in stages:
        Agent = STAGE_TO_AGENT[stage]
        agent = Agent().build(checkpointer)
        state = await agent.ainvoke(state)
    return state

# Calibração
async def process_feedback(agent_id, signal_type, signal_text):
    sa = await db.get(SourcingAgent, agent_id)
    # LLM extrai critérios
    extracted = await llm.invoke(f"Extraia critérios de: {signal_text}")
    # Muta strategy
    if signal_type == "positive":
        sa.search_strategy["positive_signals"].extend(extracted)
    else:
        sa.search_strategy["exclusions"].extend(extracted)
    sa.calibration_v += 1
    await db.add(SourcingAgentSignal(agent_id=agent_id, signal_type=signal_type, text=signal_text))
    await db.commit()
```

---

### 3.6 Studio Agents (Tier 7)

Ver `TIER_6_7_REACT_FALLBACK_AND_STUDIO_AGENTS.md` — cobertura completa com modelo de dados, runtime, guardrails e marketplace.

---

## 4. Safety & Compliance

### 4.1 Multi-Tenant Isolation

**O que é:** garantir que queries, tools e providers nunca cruzem `company_id`.

**LIA:**
- `lia-agent-system/app/shared/tenant_guard.py::get_verified_company_id` — middleware valida JWT
- `_CURRENT_COMPANY_ID: ContextVar[str]` em `autonomous_react_agent.py:22`
- `_tenant_safe_wrapper` envolve cada tool handler
- Toda query scopea por `company_id` (obrigatório em todo model SQLAlchemy)

```python
import contextvars
_CURRENT_COMPANY_ID: contextvars.ContextVar[str] = contextvars.ContextVar(
    "company_id", default="")

def _tenant_safe_wrapper(handler):
    async def wrapped(*args, **kwargs):
        cid = _CURRENT_COMPANY_ID.get()
        if not cid:
            raise RuntimeError("Tool called without company_id context")
        kwargs["_company_id"] = cid
        return await handler(*args, **kwargs)
    return wrapped
```

**Implementação portável:**

```python
# shared/tenant.py
import contextvars
from functools import wraps
from fastapi import Request, HTTPException

_CURRENT_COMPANY_ID = contextvars.ContextVar("company_id", default="")

def set_company_context(company_id: str):
    return _CURRENT_COMPANY_ID.set(company_id)

def get_company_id() -> str:
    cid = _CURRENT_COMPANY_ID.get()
    if not cid:
        raise RuntimeError("Missing company_id context")
    return cid

def tenant_safe(handler):
    @wraps(handler)
    async def wrapped(*args, **kwargs):
        kwargs["company_id"] = get_company_id()
        return await handler(*args, **kwargs)
    return wrapped

async def tenant_guard_middleware(request: Request, call_next):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    claims = verify_jwt(token)
    header_cid = request.headers.get("X-Company-Id")
    if header_cid and header_cid != claims["company_id"]:
        raise HTTPException(403, "Company mismatch")
    token_set = set_company_context(claims["company_id"])
    try:
        return await call_next(request)
    finally:
        _CURRENT_COMPANY_ID.reset(token_set)
```

---

### 4.2 PII Masking Pipeline

**O que é:** mascaramento multi-camada de PII antes de prompts LLM e em todos os logs.

**LIA:** `lia-agent-system/app/shared/pii_masking.py` (221 linhas).
- Layer 1 regex: CPF, email, telefone BR, RG, CNPJ (~9 padrões para LLM, 4 para logs)
- Layer 3: quase-identificadores (ano de graduação, idade, endereço)
- Layer 4 (opt-in): Microsoft Presidio NER (`PERSON`, `EMAIL_ADDRESS`, `LOCATION`, etc.)
- `PIIMaskingFilter(logging.Filter)` — redact em `record.msg`, `args`, exceções
- `install_global_pii_masking()` registra em root logger + handlers + Celery workers

```python
def strip_pii_for_llm_prompt(text: str) -> str:
    if not _LLM_PROMPT_PII_STRIPPING_ENABLED or not text:
        return text
    result = text
    for pattern, replacement in _LLM_PROMPT_PII_PATTERNS:
        result = pattern.sub(replacement, result)
    return _presidio_layer4_strip(result)
```

**Implementação portável:**

```python
# shared/pii.py
import re, os
import logging

_ENABLED = os.getenv("PII_MASKING_ENABLED", "true").lower() == "true"

PATTERNS = [
    (re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"), "[CPF]"),  # CPF BR
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "[EMAIL]"),
    (re.compile(r"\b(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?9?\d{4}-?\d{4}\b"), "[PHONE]"),
    (re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b"), "[CNPJ]"),
]

def strip_pii(text: str) -> str:
    if not _ENABLED or not text:
        return text
    for pat, repl in PATTERNS:
        text = pat.sub(repl, text)
    # Layer 4 opcional:
    if os.getenv("PII_PRESIDIO_ENABLED") == "true":
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine
            results = _analyzer.analyze(text=text, language="pt")
            text = _anonymizer.anonymize(text=text, analyzer_results=results).text
        except ImportError:
            pass  # fail-safe
    return text

class PIIFilter(logging.Filter):
    def filter(self, record):
        if isinstance(record.msg, str):
            record.msg = strip_pii(record.msg)
        if record.args:
            record.args = tuple(strip_pii(str(a)) if isinstance(a, str) else a for a in record.args)
        return True

def install_pii_filter():
    f = PIIFilter()
    root = logging.getLogger()
    root.addFilter(f)
    for h in root.handlers:
        h.addFilter(f)
```

---

### 4.3 Audit Trail Universal

**O que é:** todo LLM call, tool call e decisão de agente gera registro de auditoria com custo, latência e critérios.

**LIA:**
- `lia-agent-system/app/shared/compliance/audit_service.py`
- `lia-agent-system/libs/audit/lia_audit/audit_callback.py`
- Model `audit_logs` + `sox_audit_logs` (7 anos)
- `PROTECTED_CRITERIA` (idade, gênero, etnia, foto, instituição, endereço) → `criteria_ignored`
- `RETENTION_PERIODS`: score=730 dias, send_message=1825, schedule=365
- `_MODEL_PRICING_PER_1K` calcula custo por call

```python
audit_callback = AuditCallback(
    user_id=str(input.user_id or "system"),
    company_id=str(input.company_id or ""),
    session_id=str(input.session_id),
    domain=self.domain_name,
    agent_type="langgraph_react",
)
# injetado em config["callbacks"]
```

**Implementação portável:**

```python
# shared/audit.py
from langchain_core.callbacks import BaseCallbackHandler
from datetime import datetime, timedelta, UTC
from uuid import uuid4

PRICING = {
    "claude-sonnet-4-6":  {"input": 0.003, "output": 0.015},  # $/1k tokens
    "gemini-2.5-flash":   {"input": 0.000075, "output": 0.0003},
    "gpt-4o":             {"input": 0.005, "output": 0.015},
}

class AuditCallback(BaseCallbackHandler):
    def __init__(self, user_id, company_id, session_id, domain, agent_type):
        self.user_id, self.company_id = user_id, company_id
        self.session_id, self.domain, self.agent_type = session_id, domain, agent_type
        self.total_cost = 0.0
        self.call_ids = {}

    def on_llm_start(self, serialized, prompts, *, run_id, **kw):
        self.call_ids[run_id] = (datetime.now(UTC), serialized.get("kwargs", {}).get("model"))

    def on_llm_end(self, response, *, run_id, **kw):
        start, model = self.call_ids.pop(run_id)
        usage = response.llm_output.get("token_usage", {}) if response.llm_output else {}
        pricing = PRICING.get(model, {"input": 0, "output": 0})
        cost = (usage.get("prompt_tokens", 0) * pricing["input"]
                + usage.get("completion_tokens", 0) * pricing["output"]) / 1000
        self.total_cost += cost
        _persist_audit_log(
            id=uuid4(), user_id=self.user_id, company_id=self.company_id,
            session_id=self.session_id, domain=self.domain,
            decision_type="llm_call", model=model, cost=cost,
            latency_ms=(datetime.now(UTC) - start).total_seconds() * 1000,
            tokens_in=usage.get("prompt_tokens", 0),
            tokens_out=usage.get("completion_tokens", 0),
        )
```

Uso em agentes: `graph.ainvoke(..., config={"callbacks": [AuditCallback(...)]})`.

---

### 4.4 FairnessGuard 3 Camadas

**O que é:** detecção de linguagem discriminatória em 3 camadas (regex → implicit bias → LLM semântico).

**LIA:** `lia-agent-system/app/shared/compliance/fairness_guard.py` (1007 linhas) + `c3b_layer.py`.
- Layer 1: 19 categorias × ~210 regex (PT+EN) — `DISCRIMINATORY_CATEGORIES`
- Layer 2: ~70 termos implícitos PT/EN com mensagem educativa — `IMPLICIT_BIAS_TERMS`
- Layer 3: Haiku-based semantic check em ações críticas (`HIGH_IMPACT_ACTIONS = 14 ações`) — gated por `FAIRNESS_LAYER3_ENABLED`
- Text unicode-normalizado (`_normalize_text`) — casamento sem acentos
- `c3b_layer.py` orquestra: PII strip → FairnessGuard L3 → LLM → audit

**Implementação portável:**

```python
# shared/fairness.py
import re, unicodedata, os
from dataclasses import dataclass, field

DISCRIMINATORY = {
    "gender":    [r"\b(só|apenas)\s+(homens|mulheres)\b", r"\bsexo\s+masculino\b"],
    "age":       [r"\baté\s+\d+\s+anos\b", r"\bjovem\s+apenas\b"],
    "race":      [r"\bboa\s+aparência\b", r"\bpele\s+clara\b"],
    "disability":[r"\bsem\s+deficiência\b"],
    # ... replique as 19 categorias da LIA
}
IMPLICIT = {
    "culture fit": "'Culture fit' pode mascarar viés. Use 'culture add'.",
    "jovem":       "'Jovem' é proxy de idade. Especifique competência.",
}

_COMPILED = {k: [re.compile(p, re.IGNORECASE) for p in v]
             for k, v in DISCRIMINATORY.items()}

def _normalize(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()

@dataclass
class FairnessResult:
    is_blocked: bool = False
    categories: list[str] = field(default_factory=list)
    educational_message: str | None = None
    layer: int = 0

def check(text: str, action: str | None = None) -> FairnessResult:
    norm = _normalize(text)
    # Layer 1
    hits = [cat for cat, pats in _COMPILED.items() if any(p.search(norm) for p in pats)]
    if hits:
        return FairnessResult(True, hits, f"Conteúdo com viés discriminatório: {', '.join(hits)}", 1)
    # Layer 2
    for term, msg in IMPLICIT.items():
        if term in norm:
            return FairnessResult(False, ["implicit"], msg, 2)  # warn, não bloqueia
    # Layer 3 (opt-in + ação crítica)
    if (os.getenv("FAIRNESS_LAYER3_ENABLED") == "true"
            and action in {"rejection", "shortlist", "wsi_score", "sourcing_search"}):
        if _semantic_llm_check(text, action):
            return FairnessResult(True, ["semantic"], "Detectado viés semântico", 3)
    return FairnessResult(False, [], None, 0)
```

**Integração como nó LangGraph antes do LLM:**

```python
def fairness_node(state):
    last = state["messages"][-1].content
    r = check(last, state.get("action"))
    if r.is_blocked:
        return {"messages": [AIMessage(content=r.educational_message)], "blocked": True}
    return state

builder.add_node("fairness", fairness_node)
builder.add_conditional_edges("fairness",
    lambda s: END if s.get("blocked") else "llm_call")
```

---

### 4.5 HITL Gates

**O que é:** pausa no LangGraph antes de ações críticas para aprovação humana.

**LIA:** `lia-agent-system/app/domains/cv_screening/services/hitl_service.py` + `api/v1/hitl.py`.
- 3 gates via `interrupt_before`:
  1. Job Wizard → antes de `create_job`
  2. Pipeline → antes de transição de candidato
  3. WSI → antes de gerar feedback final
- Persistência dupla: Redis TTL 24h + Postgres (`hitl_pending_actions`, `hitl_audit_trail`)
- WebSocket `approval_required` ↔ `approval_response`

**Implementação portável:** ver `TIER_6_7_REACT_FALLBACK_AND_STUDIO_AGENTS.md` §3.4 (cobertura completa com snippets).

---

### 4.6 Granular Consent (LGPD)

**O que é:** consentimento por finalidade específica, não um "sim/não" monolítico.

**LIA:** `lia-agent-system/app/domains/lgpd/services/granular_consent_service.py`.
- 7 tipos: `ai_screening`, `ai_scoring`, `ai_video_analysis`, `ai_comparison`, `data_retention`, `marketing`, `analytics`
- `BLOCKING_PURPOSES` (4 primeiros) — revocação para processamento
- `GranularConsentSummary.all_blocking_given` → gate antes de operação IA

**Implementação portável:**

```python
# domains/lgpd/consent.py
from enum import StrEnum
from dataclasses import dataclass

class Purpose(StrEnum):
    AI_SCREENING = "ai_screening"
    AI_SCORING = "ai_scoring"
    AI_VIDEO = "ai_video_analysis"
    AI_COMPARISON = "ai_comparison"
    DATA_RETENTION = "data_retention"
    MARKETING = "marketing"
    ANALYTICS = "analytics"

BLOCKING = {Purpose.AI_SCREENING, Purpose.AI_SCORING,
            Purpose.AI_VIDEO, Purpose.AI_COMPARISON}

@dataclass
class ConsentSummary:
    candidate_id: str
    given: set[Purpose]

    @property
    def all_blocking_given(self) -> bool:
        return BLOCKING.issubset(self.given)

async def require_consent(candidate_id: str, purpose: Purpose):
    summary = await load_consent(candidate_id)
    if purpose in BLOCKING and purpose not in summary.given:
        raise PermissionError(f"Consentimento ausente para {purpose}")
```

Gate antes de qualquer tool IA:

```python
async def analyze_cv_handler(candidate_id: str, **kw):
    await require_consent(candidate_id, Purpose.AI_SCREENING)
    # ... análise
```

---

### 4.7 Data Subject Rights (DSR)

**O que é:** portal público onde candidato exerce direitos LGPD (acesso, correção, portabilidade, exclusão).

**LIA:** `lia-agent-system/libs/models/lia_models/data_request.py` + `app/api/v1/data_request.py`.
- `DataRequestTemplate` — campos configuráveis por empresa
- 14 tipos de campo: TEXT, CPF, CNPJ, EMAIL, PHONE, DATE, FILE, PHOTO, ADDRESS, SELECT, TEXTAREA, ...
- 5 status: PENDING, PARTIALLY_FILLED, COMPLETED, EXPIRED, CANCELLED
- 4 triggers: MANUAL, AUTOMATIC, STAGE_ENTRY, STAGE_EXIT
- Token público `secrets.token_urlsafe()` — candidato preenche sem login
- Canal WhatsApp dedicado (`data_request_whatsapp_service.py`)

**Implementação portável:** modelo simples (exemplo):

```python
from enum import StrEnum
import secrets
from datetime import datetime, timedelta, UTC

class DSRType(StrEnum):
    ACCESS = "access"
    CORRECTION = "correction"
    PORTABILITY = "portability"
    ERASURE = "erasure"

async def create_dsr(candidate_id: str, dsr_type: DSRType, company_id: str):
    token = secrets.token_urlsafe(32)
    req = DataSubjectRequest(
        id=uuid4(), candidate_id=candidate_id, company_id=company_id,
        type=dsr_type, status="pending", access_token=token,
        expires_at=datetime.now(UTC) + timedelta(days=30),
    )
    await db.add(req); await db.commit()
    portal_url = f"https://portal.example.com/dsr/{token}"
    await send_email(candidate.email, f"Exercite seu direito: {portal_url}")
    return req
```

---

### 4.8 Bias Audit + Four-Fifths

**O que é:** auditoria estatística periódica usando Four-Fifths Rule (EEOC) e chi-square para detecção de disparate impact.

**LIA:** `lia-agent-system/app/shared/services/bias_audit_service.py` (521 linhas) + `BiasAuditSnapshot` model.
- 4 dimensões: `gender`, `age_group` (<30/30-44/45+), `disability`, `region`
- `FOUR_FIFTHS_THRESHOLD = 0.80` (adverse_impact_ratio = min_rate / max_rate)
- Chi-square via `scipy.stats.chi2_contingency` quando disponível
- `eeoc_compliant = four_fifths_ok AND not_statistically_significant`
- Snapshot persiste só dados agregados (**zero PII**)

```python
APPROVAL_THRESHOLD = 60.0
FOUR_FIFTHS_THRESHOLD = 0.80
```

**Implementação portável:**

```python
# compliance/bias_audit.py
from scipy.stats import chi2_contingency
from dataclasses import dataclass

@dataclass
class BiasResult:
    dimension: str
    rates: dict[str, float]           # group → approval_rate
    adverse_impact_ratio: float       # min/max
    four_fifths_ok: bool
    chi2_p_value: float
    eeoc_compliant: bool

def audit_dimension(evaluations: list[dict], dimension: str) -> BiasResult:
    # evaluations: [{"group": "F", "approved": True}, ...]
    groups = {}
    for e in evaluations:
        g = e[dimension]
        groups.setdefault(g, {"approved": 0, "total": 0})
        groups[g]["total"] += 1
        if e["approved"]:
            groups[g]["approved"] += 1
    rates = {g: d["approved"]/d["total"] for g, d in groups.items() if d["total"]}
    aip = min(rates.values()) / max(rates.values()) if rates else 1.0
    four_fifths = aip >= 0.80
    # Chi-square
    table = [[d["approved"], d["total"]-d["approved"]] for d in groups.values()]
    _, p, _, _ = chi2_contingency(table)
    return BiasResult(dimension, rates, aip, four_fifths, p,
                      eeoc_compliant=(four_fifths and p >= 0.05))
```

---

### 4.9 Model Drift Detection

**O que é:** detecção diária de drift em score, approval rate, cost e latency comparando janelas de 7 dias.

**LIA:** `lia-agent-system/app/domains/ai/services/model_drift_service.py` (427 linhas).
- 4 triggers:
  - `score_drift` — Δ avg WSI > 0.5
  - `approval_drift` — Δ rate > 10 p.p.
  - `cost_drift` — Δ % > 20%
  - `latency_drift` — Δ P95 > 50%
- Celery Beat: `drift.run_batch` a 06h Brasília
- `DriftStatus` com nível `ok|warning|critical`

**Implementação portável:**

```python
# mlops/drift.py
from datetime import datetime, timedelta, UTC
from statistics import mean
from dataclasses import dataclass

SCORE_DRIFT_THRESHOLD = 0.5
APPROVAL_DRIFT_THRESHOLD = 0.10
COST_DRIFT_THRESHOLD = 0.20
LATENCY_DRIFT_THRESHOLD = 0.50
WINDOW_DAYS = 7

@dataclass
class DriftStatus:
    level: str                         # ok|warning|critical
    score_delta: float
    approval_delta: float
    cost_delta_pct: float
    latency_delta_pct: float
    triggered: list[str]

async def run_drift_batch() -> DriftStatus:
    now = datetime.now(UTC)
    recent = (now - timedelta(days=WINDOW_DAYS), now)
    baseline = (now - timedelta(days=2*WINDOW_DAYS), now - timedelta(days=WINDOW_DAYS))

    r_scores = await _fetch_scores(recent); b_scores = await _fetch_scores(baseline)
    score_delta = abs(mean(r_scores) - mean(b_scores))

    triggered = []
    if score_delta > SCORE_DRIFT_THRESHOLD: triggered.append("score")
    # ... approval, cost, latency

    level = "critical" if len(triggered) >= 2 else "warning" if triggered else "ok"
    return DriftStatus(level, score_delta, ..., triggered)

# Celery:
@celery_app.task
def drift_run_batch():
    asyncio.run(run_drift_batch())
```

---

### 4.10 PolicyEngine

**O que é:** aplicação de defaults por setor (tech, varejo, logística, financeiro, saúde, RPO) numa tacada, com audit trail.

**LIA:** `lia-agent-system/app/domains/policy/services/policy_engine_service.py` (1096 linhas).
- `ALPHA1_SECTOR_RULES` — perfis com `autonomy_level`, `hitl_threshold`, `auto_approve_threshold`, `max_pipeline_days`, `fairness_layer3_enabled`
- `save_policy_block(company_id, sector)` — upsert idempotente
- Audit via `audit_service.log_decision(action="apply_sector_defaults")`
- Avaliação também cobre rate limit (sliding window), escalation rules

```python
ALPHA1_SECTOR_RULES = {
    "tech": {"autonomy_level": "high", "hitl_threshold": 0.65,
             "auto_approve_threshold": 0.85, "max_pipeline_days": 30,
             "fairness_layer3_enabled": True},
    "varejo": {...},
    "logistica": {...},
}
```

**Implementação portável:**

```python
# policy/engine.py
SECTOR_RULES = {
    "tech":     {"autonomy": "high", "hitl_threshold": 0.65, "max_days": 30},
    "retail":   {"autonomy": "med",  "hitl_threshold": 0.80, "max_days": 45},
    "logistics":{"autonomy": "low",  "hitl_threshold": 0.90, "max_days": 60},
}

async def apply_sector_defaults(company_id: str, sector: str, user_id: str):
    defaults = SECTOR_RULES[sector]
    existing = await db.execute(
        select(CompanyPolicy).where(CompanyPolicy.company_id == company_id))
    row = existing.scalar_one_or_none()
    if row is None:
        row = CompanyPolicy(company_id=company_id)
        db.add(row)
    row.automation_rules = defaults
    await db.commit()
    await audit.log_decision(
        action="apply_sector_defaults",
        company_id=company_id, user_id=user_id,
        metadata={"sector": sector, "defaults": defaults})
    return row
```

---

## 5. Resilience & Scale

### 5.1 Circuit Breakers

**O que é:** breakers para 11 serviços externos (LLMs, Pearch, Apify, WorkOS, Merge, Deepgram, etc.).

**LIA:** `lia-agent-system/app/shared/resilience/circuit_breaker.py` (1060 linhas).
- Estados: `CLOSED | OPEN | HALF_OPEN`
- Default: `failure_threshold=5`, `recovery_timeout=30s`, `success_threshold=2`, `timeout=60s`
- Singletons: `ANTHROPIC_CIRCUIT`, `OPENAI_CIRCUIT`, `GEMINI_CIRCUIT`, `PEARCH_CIRCUIT`, `APIFY_CIRCUIT`, `WORKOS_CIRCUIT`, `MERGE_CIRCUIT`, `GEMINI_LIVE_CIRCUIT`, `DEEPGRAM_CIRCUIT`, `OPENMIC_CIRCUIT`, `RAILS_CIRCUIT`
- Admin API: `GET/POST /api/v1/admin/circuit-breakers`
- `_notify_circuit_open()` — alerta Bell+Teams com dedup Redis 1h

**Implementação portável:**

```python
# resilience/breaker.py
import asyncio, time, os
from enum import StrEnum

class State(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, name, failure_threshold=5, recovery_timeout=30,
                 success_threshold=2, timeout=60):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.state = State.CLOSED
        self.failures = 0
        self.successes = 0
        self.opened_at = None

    async def call(self, fn, *args, **kw):
        if self.state == State.OPEN:
            if time.time() - self.opened_at < self.recovery_timeout:
                raise CircuitBreakerOpenError(self.name)
            self.state = State.HALF_OPEN
        try:
            result = await asyncio.wait_for(fn(*args, **kw), timeout=self.timeout)
        except Exception:
            self.failures += 1
            if self.failures >= self.failure_threshold:
                self._open()
            raise
        else:
            if self.state == State.HALF_OPEN:
                self.successes += 1
                if self.successes >= self.success_threshold:
                    self._close()
            else:
                self.failures = 0
            return result

    def _open(self):
        self.state = State.OPEN; self.opened_at = time.time()
        # notificar
    def _close(self):
        self.state = State.CLOSED; self.failures = self.successes = 0

ANTHROPIC_CIRCUIT = CircuitBreaker("anthropic")
GEMINI_CIRCUIT = CircuitBreaker("gemini")
OPENAI_CIRCUIT = CircuitBreaker("openai")
```

---

### 5.2 Event Store (Append-Only)

**O que é:** event sourcing para entidades críticas (candidate, job, pipeline) com reconstrução de estado por replay.

**LIA:** `lia-agent-system/app/domains/analytics/services/event_store_service.py` + `DomainEvent` model.
- Append-only: só `append`, `get_history`, `reconstruct_state`
- `sequence_number` auto-incrementado por `(aggregate_type, aggregate_id)` via `MAX + 1`
- Uniqueness constraint `uq_domain_events_sequence`
- Fail-open em write errors (não bloqueia fluxo principal)

```python
next_seq = (await db.scalar(
    select(func.coalesce(func.max(DomainEvent.sequence_number), 0))
    .where(DomainEvent.aggregate_type == at,
           DomainEvent.aggregate_id == ai))) + 1
event = DomainEvent(aggregate_type=at, sequence_number=next_seq, ...)
db.add(event)
```

**Implementação portável:**

```python
# eventstore/service.py
from sqlalchemy import select, func
from uuid import UUID, uuid4

async def append_event(db, aggregate_type: str, aggregate_id: UUID,
                       event_type: str, event_data: dict,
                       company_id: UUID, created_by: UUID):
    next_seq = (await db.scalar(
        select(func.coalesce(func.max(DomainEvent.sequence_number), 0))
        .where(DomainEvent.aggregate_type == aggregate_type,
               DomainEvent.aggregate_id == aggregate_id))) + 1
    event = DomainEvent(
        id=uuid4(), aggregate_type=aggregate_type, aggregate_id=aggregate_id,
        sequence_number=next_seq, event_type=event_type, event_data=event_data,
        company_id=company_id, created_by=created_by)
    try:
        db.add(event); await db.commit()
        return True
    except Exception as e:
        logger.warning(f"Event store append failed: {e}")
        await db.rollback()
        return False

async def reconstruct_state(db, aggregate_type, aggregate_id):
    events = (await db.scalars(
        select(DomainEvent).where(
            DomainEvent.aggregate_type == aggregate_type,
            DomainEvent.aggregate_id == aggregate_id)
        .order_by(DomainEvent.sequence_number))).all()
    state = {}
    for ev in events:
        state = _apply_event(state, ev)  # fold
    return state
```

---

### 5.3 RAG Híbrido + pgvector

**O que é:** busca que combina BM25 (keyword) + pgvector (semântico) com peso configurável.

**LIA:** `lia-agent-system/app/domains/ai/services/rag_pipeline_service.py` + endpoint `/api/v1/candidates/rag-search`.
- `alpha=0.0` → BM25 only, `alpha=1.0` → semântico only
- Semântico: pgvector cosine sobre `routing_cache_vectors` (`ivfflat` index), threshold 0.75
- Keyword: Postgres `tsvector/tsquery` sobre candidatos
- Fairness stub: `max_single_gender_ratio = 0.70` no top-10

**Implementação portável:**

```python
# rag/hybrid.py
from sqlalchemy import select, text
import numpy as np

async def hybrid_search(db, query: str, company_id: str, limit: int = 20,
                        alpha: float = 0.5):
    # 1. Embed query
    query_vec = await embed(query)  # 768-dim

    # 2. Semantic (pgvector cosine)
    sem_sql = text("""
        SELECT candidate_id, 1 - (embedding <=> :qv) AS sim
        FROM candidate_embeddings
        WHERE company_id = :cid
        ORDER BY embedding <=> :qv LIMIT :k
    """)
    sem = await db.execute(sem_sql, {"qv": query_vec, "cid": company_id, "k": limit*3})
    sem_scores = {r.candidate_id: r.sim for r in sem}

    # 3. Keyword (BM25)
    kw_sql = text("""
        SELECT id AS candidate_id,
               ts_rank_cd(search_vector, plainto_tsquery(:q)) AS rank
        FROM candidates
        WHERE company_id = :cid AND search_vector @@ plainto_tsquery(:q)
        ORDER BY rank DESC LIMIT :k
    """)
    kw = await db.execute(kw_sql, {"q": query, "cid": company_id, "k": limit*3})
    kw_scores = {r.candidate_id: r.rank for r in kw}

    # 4. Blend
    all_ids = set(sem_scores) | set(kw_scores)
    def norm(d): 
        mx = max(d.values()) if d else 1
        return {k: v/mx for k, v in d.items()}
    s_n, k_n = norm(sem_scores), norm(kw_scores)
    blended = {cid: alpha*s_n.get(cid, 0) + (1-alpha)*k_n.get(cid, 0)
               for cid in all_ids}
    return sorted(blended.items(), key=lambda x: -x[1])[:limit]
```

---

### 5.4 Celery 4 Priority Queues

**O que é:** 4 filas Celery com prioridades distintas + DLQ para retries exaustos.

**LIA:** `lia-agent-system/libs/config/lia_config/celery_app.py` (349 linhas).
- `sourcing_high` (pri 8), `evaluation_normal` (pri 5), `vagas_normal` (pri 5), `onboarding_low` (pri 3), default `celery`
- `x-max-priority: 10` em todas
- Broker abstract: `BROKER_BACKEND=redis|rabbitmq|pubsub`
- `LIATask(Task)` — `on_failure` push pra DLQ após esgotar retries
- `worker_process_init` signal — instala PII filter em cada worker
- Beat: drift diário 06h, LGPD cleanup 02h, digest segunda 08h, RAGAS daily

**Implementação portável:**

```python
# celery_app.py
from celery import Celery, Task
from kombu import Queue

app = Celery("myapp", broker=os.getenv("CELERY_BROKER_URL"))

app.conf.task_queues = (
    Queue("high",   routing_key="high",   queue_arguments={"x-max-priority": 10}),
    Queue("normal", routing_key="normal", queue_arguments={"x-max-priority": 10}),
    Queue("low",    routing_key="low",    queue_arguments={"x-max-priority": 10}),
)
app.conf.task_routes = {
    "sourcing.*":    {"queue": "high",   "priority": 8},
    "evaluation.*":  {"queue": "normal", "priority": 5},
    "onboarding.*":  {"queue": "low",    "priority": 3},
}

class AppTask(Task):
    autoretry_for = (Exception,)
    max_retries = 3

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        if self.request.retries >= self.max_retries:
            dlq_service.push_failure(task_id, str(exc), args, kwargs)
```

---

### 5.5 Multi-Channel Notifications

**O que é:** um service unificado que envia para 7 canais.

**LIA:** `lia-agent-system/libs/messaging/lia_messaging/notification_service.py` (1308 linhas).
- Canais: `BELL | EMAIL | TEAMS | WHATSAPP | CHAT | IN_APP | PUSH`
- Prioridade: `URGENT | ACTION_REQUIRED | INFO | SUCCESS | WARNING`
- Tipos proativos: `MORNING_BRIEFING`, `APPROVAL_REQUEST`, `SCREENING_COMPLETED`, `INTERVIEW_REMINDER`, `VACANCY_EXPIRING`, `WEEKLY_DIGEST`
- Beat: `briefing-daily` 06h, `digest-weekly` segunda 08h

**Implementação portável:**

```python
# notifications/service.py
from enum import StrEnum

class Channel(StrEnum):
    BELL = "bell"; EMAIL = "email"; TEAMS = "teams"
    WHATSAPP = "whatsapp"; CHAT = "chat"; PUSH = "push"

CHANNEL_HANDLERS = {
    Channel.EMAIL:    send_email,
    Channel.TEAMS:    send_teams_card,
    Channel.WHATSAPP: send_whatsapp,
    Channel.BELL:     insert_bell,
    # ...
}

async def notify(user_id: str, channels: list[Channel], type_: str,
                 title: str, body: str, data: dict | None = None):
    prefs = await load_user_preferences(user_id)
    tasks = []
    for ch in channels:
        if ch in prefs.muted_channels: continue
        tasks.append(CHANNEL_HANDLERS[ch](user_id, title, body, data))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    await persist_notification(user_id, channels, type_, title, body, results)
```

---

## 6. Business Layer

### 6.1 Digital Twins

**O que é:** agente que imita decisões de um SME específico via K-NN sobre histórico de decisões vetorizadas.

**LIA:** `lia-agent-system/app/services/twin_inference_service.py` + `twin_knowledge_indexer.py`.
- `DigitalTwin` table: `twin_name`, `sme_user_id`, `specialties[]`, `twin_embedding: Vector(768)`, `accuracy_pct`
- `TwinDecision` — histórico de calls do SME (approved/rejected/maybe) com `candidate_snapshot`, `job_snapshot` (JSONB), `embedding: Vector(768)`
- `evaluate()`: embed candidato → K-NN K=5 → few-shot prompt (aprovados + rejeitados) → LLM gera score + reasoning first-person
- `TwinEvaluation` — `score`, `decision`, `reasoning`, `confidence` (baseado em corpus size + similarity)

**Implementação portável:**

```python
# twins/inference.py
async def evaluate_with_twin(twin_id: str, candidate: dict, job: dict):
    twin = await db.get(DigitalTwin, twin_id)
    cand_emb = await embed(f"{candidate['summary']} {' '.join(candidate['skills'])}")

    # K-NN nos últimos decisions do SME
    neighbors = await db.execute(text("""
        SELECT candidate_snapshot, job_snapshot, decision, reasoning,
               1 - (embedding <=> :q) AS sim
        FROM twin_decisions
        WHERE twin_id = :tid
        ORDER BY embedding <=> :q LIMIT 5
    """), {"q": cand_emb, "tid": twin_id})

    # Few-shot prompt
    examples = "\n\n".join(
        f"Candidato: {n.candidate_snapshot}\nVaga: {n.job_snapshot}\n"
        f"Decisão: {n.decision}\nRaciocínio: {n.reasoning}"
        for n in neighbors)
    prompt = f"""Você é o SME {twin.twin_name}. Analise como você analisaria.
Exemplos seus:
{examples}

Agora este candidato:
Candidato: {candidate}
Vaga: {job}
Dê score 0-100, decisão (approved/rejected/maybe) e raciocínio em primeira pessoa."""
    result = await llm.invoke(prompt)
    return parse_twin_evaluation(result, corpus_size=len(neighbors))
```

---

### 6.2 WSI Interview (StateGraph, não ReAct)

**O que é:** metodologia proprietária de entrevista estruturada (Dreyfus + Bloom + Big Five) implementada como StateGraph determinístico.

**LIA:** `lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py`.
- `WSIInterviewStage` StrEnum: `INIT → LOAD_CONTEXT → GENERATE_QUESTION → AWAIT_RESPONSE → VALIDATE_RESPONSE → SCORE_RESPONSE → ADVANCE → GENERATE_FEEDBACK → COMPLETE`
- `WSIQuestionBlock`: `block_type` (technical/behavioral/situational), `competency`, `bloom_level` (1-6), `dreyfus_level` (1-5), `big_five_trait`, `max_score`
- LangSmith `@traceable` em cada nó
- HITL antes de `GENERATE_FEEDBACK`

**Por que StateGraph e não ReAct:** fluxo previsível → Graph; raciocínio autônomo → ReAct. Auditoria por-nó para BCB 498/SOX.

**Implementação portável:**

```python
# wsi/graph.py
from langgraph.graph import StateGraph, END
from typing import TypedDict

class WSIState(TypedDict):
    candidate_id: str
    questions: list[dict]
    current_idx: int
    responses: list[dict]
    scores: dict[str, float]
    feedback: str | None

def generate_question_node(state: WSIState):
    q = generate_next_question(state)
    state["questions"].append(q)
    return state

def score_response_node(state: WSIState):
    last_resp = state["responses"][-1]
    score = score_with_rubric(last_resp, state["questions"][state["current_idx"]])
    state["scores"][last_resp["question_id"]] = score
    return state

def advance_node(state: WSIState):
    state["current_idx"] += 1
    return state

def should_continue(state: WSIState):
    return "generate_question" if state["current_idx"] < len(state["questions"]) else "generate_feedback"

builder = StateGraph(WSIState)
builder.add_node("generate_question", generate_question_node)
builder.add_node("score_response", score_response_node)
builder.add_node("advance", advance_node)
builder.add_node("generate_feedback", generate_feedback_node)
builder.set_entry_point("generate_question")
builder.add_edge("generate_question", "score_response")
builder.add_edge("score_response", "advance")
builder.add_conditional_edges("advance", should_continue,
    {"generate_question": "generate_question", "generate_feedback": "generate_feedback"})
builder.add_edge("generate_feedback", END)

graph = builder.compile(
    checkpointer=checkpointer,
    interrupt_before=["generate_feedback"],  # HITL
)
```

---

## 7. Observability & Ops

### 7.1 LangSmith Tracing + Cost

**O que é:** tracing distribuído de toda call LLM com custo calculado por modelo.

**LIA:** `lia-agent-system/app/config/langsmith.py` (68 linhas).

```python
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = langsmith_api_key
os.environ["LANGCHAIN_PROJECT"] = "lia-agent-system"
```

- Aceita `LANGSMITH_API_KEY` ou `LANGCHAIN_API_KEY`
- WSI nodes + router tiers decorados com `@traceable`/`trace_span`
- `AuditCallback` calcula custo via `_MODEL_PRICING_PER_1K`
- Latência por tool via `TimedToolNode` labeled por domain + tool

**Implementação portável:** igual ao snippet acima. Para custo, usar o `AuditCallback` da §4.3. Para spans manuais:

```python
from langsmith import traceable

@traceable(run_type="chain", name="cascaded_router.tier5_llm_cascade")
async def tier5_llm_cascade(query, context):
    ...
```

---

### 7.2 Runbooks Operacionais

**LIA:** `lia-agent-system/docs/RUNBOOK_DEGRADATION.md`, `lia-agent-system/docs/RUNBOOK_INCIDENT_PLAYBOOKS.md`.
- Card por circuit: threshold 5 falhas/60s, recovery 30s, alerta Prometheus `CircuitBreakerOpen{circuit="..."}` > 2min
- Playbook PB-01: LLM primário down → verifica fallback → escala L3/L4 se ambos abertos
- Links diretos: `POST /api/v1/admin/circuit-breakers/{name}/reset`

**Recomendação portável:** `docs/RUNBOOK.md` com uma seção por breaker/serviço, sempre com:
1. Sintoma
2. Como confirmar (query/endpoint)
3. Ação imediata
4. Quando escalar
5. Rollback

---

### 7.3 SOC2 / ISO 27001 / Trust Center

**LIA:** `lia-agent-system/libs/models/lia_models/trust_center.py`, `audit_logs.py` + endpoints `/api/v1/trust-center`, `/api/v1/compliance-controls`.
- `ComplianceFrameworkTypeEnum`: `ISO_27001, SOC_2_TYPE_I, SOC_2_TYPE_II, SOX, LGPD, GDPR, BACEN_4893, PCI_DSS`
- `CompanyControlStatusEnum`: progresso por controle `NOT_STARTED → IN_PROGRESS → IMPLEMENTED → VERIFIED`
- `TrustCenterSettings` + `Subprocessor` + `TrustCenterResource` + `TrustCenterUpdate` — portal público
- `SOXAuditLog` — retenção 7 anos

**Recomendação portável:** adicionar após compliance básico (LGPD, audit). É mais content/infra do que código.

---

## 8. Referências Cruzadas

| Assunto | Doc |
|---------|-----|
| Tools detalhadas (260+, 48 arquivos) | `LIA_TOOLS_CATALOG.md` |
| Tier 6 (ReAct fallback) e Tier 7 (Studio) | `TIER_6_7_REACT_FALLBACK_AND_STUDIO_AGENTS.md` |
| Comparativo LIA × baseline | `LIA_VS_BASELINE_COMPARISON.md` |
| Arquitetura geral | `ARCHITECTURE.md` |
| CLAUDE.md (identidade/stack/fluxo) | `/CLAUDE.md` |

---

## 9. Arquivos Canônicos da LIA (índice rápido)

```
Core agent:
  libs/agents-core/lia_agents_core/langgraph_react_base.py
  app/tools/registry.py
  app/tools/tool_registry_metadata.yaml
  app/tools/tool_permissions.yaml
  app/shared/providers/llm_factory.py
  app/orchestrator/cascaded_router.py

Safety:
  app/shared/tenant_guard.py
  app/shared/pii_masking.py
  app/shared/compliance/audit_service.py
  app/shared/compliance/fairness_guard.py
  app/shared/compliance/c3b_layer.py
  app/domains/cv_screening/services/hitl_service.py
  app/domains/lgpd/services/granular_consent_service.py
  app/domains/lgpd/services/dsr_export_service.py
  app/shared/services/bias_audit_service.py
  app/domains/ai/services/model_drift_service.py
  app/domains/policy/services/policy_engine_service.py

Resilience:
  app/shared/resilience/circuit_breaker.py
  app/domains/analytics/services/event_store_service.py
  app/domains/ai/services/rag_pipeline_service.py
  libs/config/lia_config/celery_app.py
  libs/messaging/lia_messaging/notification_service.py

Business:
  app/services/twin_inference_service.py
  app/domains/cv_screening/agents/wsi_interview_graph.py

Sourcing (10 sub-agents):
  app/domains/sourcing/agents/*.py
  app/services/sourcing_agent_orchestrator.py

Studio (Tier 7):
  app/domains/agent_studio/custom_agent_runtime.py
  libs/models/lia_models/custom_agent.py

Observability:
  app/config/langsmith.py
  libs/audit/lia_audit/audit_callback.py

Ops:
  docs/RUNBOOK_DEGRADATION.md
  docs/RUNBOOK_INCIDENT_PLAYBOOKS.md
```
