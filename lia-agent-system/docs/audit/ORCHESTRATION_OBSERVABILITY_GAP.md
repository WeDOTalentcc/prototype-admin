# Gap de Observabilidade na Orquestração — CascadedRouter

**Data**: 2026-04-12
**Versão**: 1.0
**Escopo**: Análise do gap de observabilidade no roteamento de intenções (CascadedRouter) e proposta de solução reaproveitando a infraestrutura `lia_audit`

---

## 1. Gap Identificado

### 1.1 Estado Atual do Registro de Decisões de Roteamento

O `CascadedRouter` (`app/orchestrator/cascaded_router.py`) implementa um pipeline de 7 tiers para resolver a intenção de cada mensagem do usuário:

| Tier | Mecanismo | Custo |
|------|-----------|-------|
| 0 | MemoryResolver (pronomes/referências) | Zero |
| 1 | LRU in-process (hash MD5) | Zero |
| 2 | Redis hash cache (distribuído) | Negligível |
| 3 | VectorSemanticCache (pgvector, cosine ≥ 0.85) | Baixo |
| 4 | FastRouter (regex/keyword) | Baixo |
| 5 | LLM Cascade (Haiku → Sonnet → Opus) | Alto |
| 6 | AutonomousReActAgent (cross-domain) | Alto |
| Fallback | Clarificação ao usuário | Zero |

Atualmente, as decisões de roteamento são registradas por **três mecanismos, todos com limitações significativas**:

#### a) OpenTelemetry Spans (`@trace_span`)

O decorator `@trace_span("router.route")` e os spans internos (`router.tier1_lru_cache`, `router.tier5_llm_cascade`, etc.) registram atributos como `hit`, `confidence_score`, `domain_id`, `latency_ms` em cada tier.

**Limitação**: Spans dependem de um **collector externo** (Jaeger, Tempo, etc.) para serem persistidos. Sem collector configurado, todos os dados são descartados. Não há garantia de persistência em ambientes de desenvolvimento ou staging.

**Referência**: `app/shared/tracing.py` (`get_tracer`, `trace_span`)

#### b) `_stats` In-Memory

O dicionário `self._stats` acumula contadores (`memory_hits`, `redis_hits`, `llm_hits`, etc.) durante o ciclo de vida da instância.

**Limitação**: Dados são **voláteis** — perdem-se a cada restart do worker. Não há serialização para disco ou banco. Múltiplos workers (Gunicorn/Uvicorn) mantêm contadores independentes sem agregação.

#### c) `logger.debug` Não-Estruturado

Mensagens como `CascadedRouter: fast match for '...' → domain_id` são emitidas em nível DEBUG.

**Limitação**: Logs em formato **não-estruturado** (texto livre), sem campos indexáveis. Em produção com nível INFO+, esses logs nem sequer são emitidos. Não permitem consulta por confiança, tier, domínio ou sessão.

### 1.2 Auditoria no MainOrchestrator

O método `MainOrchestrator._audit_output` (`app/orchestrator/main_orchestrator.py`) persiste registros de auditoria **apenas quando o resultado contém `candidate_id` ou `job_id`**:

```python
_should_audit = bool(
    result.get("candidate_id") or result.get("job_id") or result.get("job_vacancy_id")
)
```

Isso significa que **a grande maioria das interações** — perguntas gerais, navegação, buscas exploratórias, conversas de suporte — não gera nenhum registro persistente de auditoria. A decisão de roteamento que levou àquela interação simplesmente desaparece.

### 1.3 O Que Não É Possível Hoje

Não existe registro persistente e estruturado que conecte o fluxo completo de uma decisão de roteamento:

```
mensagem recebida → tiers tentados → tier que resolveu → confiança → domínio escolhido → custo
```

Isso impede:

1. **Validar mensagens individuais** — quando um usuário reporta que a LIA "não entendeu", não há como reconstruir quais tiers foram tentados e por que o domínio final foi escolhido
2. **Calibrar a orquestração em cenários de baixa confiança** — sem dados históricos de decisões com confidence < 0.5, não é possível ajustar thresholds do FastRouter ou do LLM Cascade
3. **Monitorar custo real de roteamento** — tiers 5 e 6 chamam LLMs (Haiku, Sonnet, Opus) e o AutonomousReActAgent, mas o custo dessas chamadas no contexto de roteamento não é rastreado separadamente do custo de execução do agente
4. **Analisar padrões de fallback** — sem dados, não é possível identificar quais tipos de mensagem consistentemente caem para tiers caros (5/6) e poderiam ser capturados por regras no FastRouter (tier 4)
5. **Auditar decisões para compliance** — em cenários regulatórios (LGPD, WeDO Governance), pode ser necessário justificar por que uma mensagem foi roteada para determinado agente

---

## 2. Proposta de Solução

### 2.1 Princípio: Reaproveitar a Infraestrutura Existente

A biblioteca `lia_audit` já fornece uma infraestrutura robusta de auditoria dual (PG + Storage). A proposta é criar um registro análogo ao `ExecutionAuditRecord` (`libs/audit/lia_audit/audit_models.py`) específico para decisões de roteamento, reaproveitando o `AuditWriter` (acessado via `get_audit_writer()`, padrão module-level singleton em `libs/audit/lia_audit/audit_writer.py`) para persistência.

### 2.2 Novo Modelo: `RoutingAuditRecord`

Criar um dataclass em `libs/audit/lia_audit/audit_models.py`, análogo ao `ExecutionAuditRecord`:

```python
@dataclass
class RoutingAuditRecord:
    routing_id: str = ""                    # UUID único da decisão
    session_id: str = ""
    user_id: str = ""
    company_id: str = ""
    message_hash: str = ""                  # MD5 da mensagem normalizada
    message_preview: str = ""               # primeiros 200 chars (PII mascarado)

    # Resultado final
    resolved_domain: str = ""
    resolved_tier: str = ""                 # "tier1_lru", "tier5_llm_cascade", etc.
    confidence: float = 0.0
    matched_pattern: str | None = None

    # Tiers tentados
    tiers_attempted: list[dict] = field(default_factory=list)
    # Cada dict: {"tier": "tier4_fast_router", "hit": False, "confidence": 0.0, "latency_ms": 12.3}

    # Custo (relevante para tiers 5/6)
    estimated_cost_usd: float = 0.0
    llm_model_used: str | None = None
    tokens_total: int = 0

    # Metadados
    timestamp: str = ""
    total_latency_ms: float = 0.0
    needs_clarification: bool = False
    ab_variant: str | None = None

    # Storage
    storage_path: str | None = None
```

### 2.3 Persistência Dual via `AuditWriter`

Estender o `AuditWriter` (`libs/audit/lia_audit/audit_writer.py`) com um método `persist_routing`:

- **PostgreSQL** → tabela `routing_decision_log` com metadados indexáveis
- **Storage (S3/local)** → payload completo incluindo `tiers_attempted` com detalhes de cada tier

Isso segue exatamente o padrão já implementado para `ExecutionAuditRecord`:
- `_save_full_payload` → storage de objeto
- `_save_metadata` → INSERT na tabela PG

### 2.4 Tabela PostgreSQL: `routing_decision_log`

```sql
CREATE TABLE routing_decision_log (
    routing_id        UUID PRIMARY KEY,
    session_id        VARCHAR(255) NOT NULL,
    company_id        VARCHAR(255) NOT NULL,
    user_id           VARCHAR(255),
    message_hash      VARCHAR(32) NOT NULL,           -- MD5
    message_preview   VARCHAR(200),                   -- PII mascarado
    resolved_domain   VARCHAR(100) NOT NULL,
    resolved_tier     VARCHAR(50) NOT NULL,
    confidence        FLOAT NOT NULL DEFAULT 0.0,
    matched_pattern   TEXT,
    estimated_cost    FLOAT DEFAULT 0.0,
    llm_model_used    VARCHAR(100),
    total_latency_ms  FLOAT DEFAULT 0.0,
    needs_clarification BOOLEAN DEFAULT FALSE,
    ab_variant        VARCHAR(100),
    storage_path      VARCHAR(500),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_routing_company_ts ON routing_decision_log (company_id, created_at DESC);
CREATE INDEX idx_routing_domain ON routing_decision_log (resolved_domain);
CREATE INDEX idx_routing_tier ON routing_decision_log (resolved_tier);
CREATE INDEX idx_routing_confidence ON routing_decision_log (confidence);
CREATE INDEX idx_routing_session ON routing_decision_log (session_id);
```

Indices projetados para as consultas mais comuns:
- Filtrar por empresa + período (dashboard)
- Agrupar por domínio (distribuição de intenções)
- Filtrar por tier (análise de custo)
- Filtrar por confiança baixa (calibração de thresholds)

### 2.5 Integração no CascadedRouter

No método `route()` do `CascadedRouter`, após resolver o domínio final e antes de retornar o `RouteResult`, chamar o `AuditWriter` para persistir o `RoutingAuditRecord`. A coleta de dados dos tiers tentados já existe parcialmente nos spans — basta acumular em uma lista local durante a execução.

Ponto de integração: cada bloco `async with _tracer.start_span(...)` já possui os atributos necessários. A mudança é acumular esses dados também em uma lista `_tiers_log` e, ao final, construir e persistir o `RoutingAuditRecord`.

### 2.6 API de Consulta

Seguindo o padrão do `audit_timeline.py` (`app/api/v1/audit_timeline.py`), expor endpoints para consulta:

```
GET /api/v1/audit/routing?company_id=&domain=&tier=&min_confidence=&max_confidence=&limit=
  → Lista decisões de roteamento com filtros

GET /api/v1/audit/routing/{routing_id}
  → Detalhe completo de uma decisão (carrega payload do storage)

GET /api/v1/audit/routing/stats?company_id=&period=
  → Agregações: distribuição por tier, domínio, faixa de confiança, custo acumulado
```

Filtros especialmente úteis:
- `max_confidence=0.5` → decisões de baixa confiança para calibração
- `tier=tier5_llm_cascade` → decisões que custaram chamadas LLM
- `needs_clarification=true` → casos onde o sistema pediu clarificação ao usuário

### 2.7 Diagrama do Fluxo Proposto

```
                          Mensagem do Usuário
                                │
                                ▼
                        ┌───────────────┐
                        │ CascadedRouter│
                        │   .route()    │
                        └───────┬───────┘
                                │
                    ┌───────────┼───────────┐
                    │     Cascade 7 Tiers    │
                    │                        │
                    │  Tier 0: Memory        │──┐
                    │  Tier 1: LRU           │  │
                    │  Tier 2: Redis         │  │ Acumula _tiers_log[]
                    │  Tier 3: Vector        │  │ para cada tier tentado
                    │  Tier 4: FastRouter    │  │
                    │  Tier 5: LLM Cascade   │  │ (custo estimado nos tiers 5/6)
                    │  Tier 6: Autonomous    │──┘
                    │  Fallback: Clarify     │
                    └───────────┬────────────┘
                                │
                    RouteResult (domain, confidence, tier)
                                │
                    ┌───────────┼───────────┐
                    │                        │
                    ▼                        ▼
            Retorna para              RoutingAuditRecord
            MainOrchestrator          construído com _tiers_log
                                             │
                                             ▼
                                    ┌─────────────────┐
                                    │   AuditWriter    │
                                    │ (get_audit_      │
                                    │  writer())       │
                                    └────────┬────────┘
                                             │
                                ┌────────────┼────────────┐
                                │                          │
                                ▼                          ▼
                    ┌───────────────────┐     ┌────────────────────┐
                    │    PostgreSQL      │     │   Storage (S3)     │
                    │ routing_decision_  │     │ payload completo   │
                    │ log (metadados)    │     │ (tiers_attempted,  │
                    │                    │     │  detalhes LLM)     │
                    └───────────────────┘     └────────────────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │  API /audit/      │
                    │  routing          │
                    │  (filtros por     │
                    │  confiança, tier, │
                    │  domínio, custo)  │
                    └───────────────────┘
```

---

## 3. Arquivos Referenciados

| Arquivo | Papel na Análise |
|---------|-----------------|
| `app/orchestrator/cascaded_router.py` | Router 7-tier — onde o gap existe. Possui `_stats` volátil, spans OTel, e `logger.debug` |
| `app/orchestrator/main_orchestrator.py` | `_audit_output` — só persiste quando há `candidate_id`/`job_id` |
| `libs/audit/lia_audit/audit_models.py` | `ExecutionAuditRecord` e `RequestCostRecord` — modelos a serem seguidos |
| `libs/audit/lia_audit/audit_writer.py` | `AuditWriter` (module-level singleton via `get_audit_writer()`) com persistência dual (PG + Storage) |
| `libs/audit/lia_audit/audit_callback.py` | `AuditCallback` — callback LangChain que usa `AuditWriter` para persistir |
| `app/api/v1/audit_timeline.py` | Endpoints de consulta de auditoria — padrão a seguir para a API de routing |
| `app/shared/tracing.py` | `get_tracer`, `trace_span` — infraestrutura OTel atual |
| `app/orchestrator/fast_router.py` | Tier 4 (regex/keyword) — calibração depende de dados históricos |

---

## 4. Prioridade e Impacto

### Prioridade: Alta

- Sem este registro, **não há como debugar decisões de roteamento** em produção
- O custo de roteamento (tiers 5/6) é invisível — pode representar gasto significativo não monitorado
- A calibração de thresholds (`ROUTER_FAST_CONFIDENCE_THRESHOLD`, `ROUTER_LLM_CASCADE_MIN_CONFIDENCE`) é feita às cegas

### Impacto Estimado

- **Código novo**: ~200-300 linhas (modelo, extensão do writer, integração no router)
- **Migration**: 1 tabela + 5 indices
- **API**: 3 endpoints seguindo padrão existente
- **Risco**: Baixo — a persistência via `AuditWriter` é best-effort e error-tolerant (erros são logados mas não propagados, nunca bloqueia a execução do agente). Para minimizar impacto de latência, considerar despacho via `asyncio.create_task` no ponto de integração

---

**Autor**: LIA Agent System Audit
**Data**: 2026-04-12
**Próximo passo**: Implementar `RoutingAuditRecord` e integrar no `CascadedRouter.route()`
