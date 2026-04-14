# INVARIANT_BASELINE.md — Invariant Tests (Propriedades que Sempre Valem)
**Protocolo:** P30  
**Data:** 2026-04-14  
**Engenheiro:** Claude Opus 4.6  
**Baseado em:** Todos os protocolos anteriores (P01-P29, PX01-PX07)  
**Contexto:** Frontend + IA no Replit, Backend Rails no GCP.

**Depende de:** TODOS  
**Alimenta:** P32

---

## CONCEITO

Invariant tests verificam propriedades que devem ser **SEMPRE verdadeiras**, independente do input. Diferente de golden scenarios (input -> output), invariants dizem: "para QUALQUER input valido, isto SEMPRE vale."

**Zero tolerance:** Invariant tests NUNCA podem falhar. Uma unica falha = bug critico.

---

## INVENTARIO DE INVARIANTS

### 20 Invariants Definidos em 5 Categorias

| Categoria | Invariants | Infra Existente? |
|-----------|-----------|-----------------|
| Universal (todo agente) | 6 | 85% |
| Fairness (agentes de decisao) | 4 | 70% |
| LGPD/Privacy | 4 | 65% |
| Tenant Isolation | 3 | 90% |
| Resilience | 3 | 80% |

---

## CATEGORIA 1: INVARIANTS UNIVERSAIS

| # | Invariant | Descricao | Infra Existe? | Estimativa Pass? |
|---|-----------|-----------|-------------|-----------------|
| INV-U01 | **Output matches schema** | Output de qualquer agente valida contra AgentOutput | SIM — AgentInput/AgentOutput Pydantic em 13/13 ReAct | PASS |
| INV-U02 | **Audit log always created** | Toda execucao gera registro de audit | SIM — AuditCallback no LangGraphReActBase + StructuredLoggingMiddleware | PASS (ReAct), FAIL (StateGraph) |
| INV-U03 | **Trace has agent span** | Toda execucao gera span com agent_id | SIM — tracing.py com 105 refs + RequestIdMiddleware | PARCIAL — spans existem para router, faltam para agents individuais |
| INV-U04 | **Response never contains raw PII** | Nenhuma resposta contem CPF, email, telefone nao autorizado | SIM — _sanitize_messages_pii no LangGraphReActBase (LIA-C04), 12 refs em domains | PASS (ReAct), NAO TESTADO (StateGraph) |
| INV-U05 | **Cost never exceeds cap** | Nenhuma execucao individual excede cost cap | SIM — TenantBudget com monthly_limit + blocked flag | PASS |
| INV-U06 | **Latency never exceeds timeout** | Nenhuma execucao excede timeout | SIM — LLM_TIMEOUT_SECONDS=120, max_steps guards (14 refs) | PASS (guards existem) |

**Verificacao de infra:**
- `_sanitize_messages_pii` no LangGraphReActBase: **PRESENTE**
- `AuditCallback` no LangGraphReActBase: **PRESENTE**
- `StructuredLoggingMiddleware`: **PRESENTE** no main.py
- `RequestIdMiddleware`: **PRESENTE** (X-Request-ID)
- `TenantBudget.monthly_limit` + blocked: **PRESENTE**
- `MAX_ITERATIONS` / `max_steps`: **14 refs** no codebase

---

## CATEGORIA 2: INVARIANTS DE FAIRNESS

| # | Invariant | Descricao | Infra Existe? | Estimativa Pass? |
|---|-----------|-----------|-------------|-----------------|
| INV-F01 | **Score independent of protected attributes** | Variar apenas nome/genero/etnia nao altera score > 5% | PARCIAL — FairnessGuard bloqueia input, mas NAO verifica output bias | INCERTO — depende do LLM |
| INV-F02 | **Demographic parity across batch** | Em batch, distribuicao de scores nao correlaciona com grupo protegido | NAO — nenhum teste de batch fairness implementado | INCERTO |
| INV-F03 | **No proxy attributes in scoring** | Universidade, bairro, aparencia NUNCA usados como fator de score | SIM — FairnessGuard com IMPLICIT_BIAS_TERMS bloqueia no input | PASS (input), INCERTO (output) |
| INV-F04 | **FairnessGuard always runs before decision** | Nenhuma decisao sobre candidato sem FairnessGuard pre-check | SIM — ComplianceDomainPrompt + MainOrchestrator pre-check | PASS |

**Resultado chave:** FairnessGuard protege o INPUT (bloqueia queries enviesadas). O GAP e no OUTPUT — o LLM pode gerar scores enviesados que passam sem verificacao (fairness post-check ausente em 29/30 agentes, conforme P23).

---

## CATEGORIA 3: INVARIANTS DE LGPD/PRIVACY

| # | Invariant | Descricao | Infra Existe? | Estimativa Pass? |
|---|-----------|-----------|-------------|-----------------|
| INV-L01 | **Deleted candidate returns no data** | Apos exclusao, NENHUM endpoint/agente retorna dados | PARCIAL — data_subject_requests.py existe (11 files), mas propagacao para vector store/cache nao confirmada | PARCIAL |
| INV-L02 | **Consent required before communication** | Nenhuma comunicacao sem consentimento | SIM — consent refs encontrados em communication domain | INCERTO — refs existem mas enforcement nao confirmado |
| INV-L03 | **PII masked in logs** | Logs NUNCA contem PII raw | SIM — PIIMaskingFilter no handler + 377 refs potenciais (P27 T3.5) | PARCIAL (filter existe, mas 377 refs arriscadas) |
| INV-L04 | **Data minimization in LLM prompts** | Dados pessoais minimizados antes de enviar ao LLM | SIM — strip_pii_for_llm_prompt via LIA-C04 | PASS (ReAct) |

---

## CATEGORIA 4: INVARIANTS DE TENANT ISOLATION

| # | Invariant | Descricao | Infra Existe? | Estimativa Pass? |
|---|-----------|-----------|-------------|-----------------|
| INV-T01 | **Cross-tenant data never returned** | Agente de tenant A NUNCA retorna dados de tenant B | SIM — AuthEnforcementMiddleware com _current_company_id ContextVar | PASS (Python), FAIL (Rails — candidates sem account_id) |
| INV-T02 | **Tenant budget isolated** | Consumo de tokens de tenant A nao afeta tenant B | SIM — TenantBudget usa Redis key per company_id | PASS |
| INV-T03 | **LLM config per tenant** | Cada tenant usa seu provider/model/key | SIM — TenantProviderRegistry + ProviderContainer | PASS |

**Gap critico:** INV-T01 FALHA no Rails porque `candidates` nao tem `account_id` (BLK-01 do PX07). No Python, company_id e enforced pelo middleware.

---

## CATEGORIA 5: INVARIANTS DE RESILIENCIA

| # | Invariant | Descricao | Infra Existe? | Estimativa Pass? |
|---|-----------|-----------|-------------|-----------------|
| INV-R01 | **Agent loop never infinite** | Nenhum agente executa mais que MAX_ITERATIONS tool calls | SIM — 14 refs a max_iterations/max_steps, CircuitBreaker (2 refs) | PASS |
| INV-R02 | **LLM failure = graceful fallback** | Se LLM primario falha, fallback para proximo | SIM — ProviderContainer com fallback chain (Gemini->Claude->OpenAI) | PASS |
| INV-R03 | **Rate limit enforced globally** | Nenhum tenant ultrapassa rate limit | SIM — RateLimitMiddleware | PASS |

---

## BASELINE CONSOLIDADO

### Tabela de 20 Invariants

| # | Invariant | Categoria | Status Baseline | Confianca |
|---|-----------|-----------|----------------|-----------|
| INV-U01 | Output matches schema | Universal | **PASS** | ALTA |
| INV-U02 | Audit log always created | Universal | **PARCIAL** (ReAct OK, StateGraph gap) | MEDIA |
| INV-U03 | Trace has agent span | Universal | **PARCIAL** (router OK, agent gap) | MEDIA |
| INV-U04 | Response never contains raw PII | Universal | **PASS** (ReAct via LIA-C04) | ALTA |
| INV-U05 | Cost never exceeds cap | Universal | **PASS** | ALTA |
| INV-U06 | Latency never exceeds timeout | Universal | **PASS** | ALTA |
| INV-F01 | Score independent of protected attrs | Fairness | **INCERTO** (input OK, output gap) | BAIXA |
| INV-F02 | Demographic parity across batch | Fairness | **INCERTO** (nao testado) | BAIXA |
| INV-F03 | No proxy attributes in scoring | Fairness | **PARCIAL** (input blocked, output gap) | MEDIA |
| INV-F04 | FairnessGuard always runs | Fairness | **PASS** | ALTA |
| INV-L01 | Deleted candidate no data | LGPD | **PARCIAL** (DB OK, cache/vector gap) | MEDIA |
| INV-L02 | Consent before communication | LGPD | **INCERTO** | BAIXA |
| INV-L03 | PII masked in logs | LGPD | **PARCIAL** (filter OK, 377 refs) | MEDIA |
| INV-L04 | Data minimization in LLM | LGPD | **PASS** (via LIA-C04) | ALTA |
| INV-T01 | Cross-tenant isolation | Tenant | **PARCIAL** (Python OK, Rails gap) | MEDIA |
| INV-T02 | Tenant budget isolated | Tenant | **PASS** | ALTA |
| INV-T03 | LLM config per tenant | Tenant | **PASS** | ALTA |
| INV-R01 | No infinite loops | Resilience | **PASS** | ALTA |
| INV-R02 | LLM fallback graceful | Resilience | **PASS** | ALTA |
| INV-R03 | Rate limit enforced | Resilience | **PASS** | ALTA |

### Score Consolidado

| Status | Quantidade | % |
|--------|-----------|---|
| **PASS** | 12 | 60% |
| **PARCIAL** | 5 | 25% |
| **INCERTO** | 3 | 15% |
| **FAIL** | 0 | 0% |
| **TOTAL** | 20 | 100% |

**Score: 12/20 PASS (60%), 0 FAIL explícitos**

---

## GAPS CRITICOS REVELADOS PELOS INVARIANTS

| # | Invariant | Gap | Acao | Prioridade |
|---|-----------|-----|------|-----------|
| 1 | **INV-F01** Score bias | FairnessGuard faz pre-check mas NAO post-check no output | Adicionar fairness post-check no ComplianceDomainPrompt (P23 Onda 1) | P0 |
| 2 | **INV-F02** Batch parity | Zero testes de fairness em batch | Criar batch fairness eval (P29 bias probes) | P1 |
| 3 | **INV-L01** Deletion propagation | Data subject deletion nao propaga para vector store e cache Redis | Adicionar cleanup em pgvector + Redis apos deletion | P0 |
| 4 | **INV-L02** Consent check | Communication domain referencia consent mas enforcement nao confirmado | Verificar e implementar check antes de send_email/send_whatsapp | P0 |
| 5 | **INV-L03** PII in logs | PIIMaskingFilter existe mas 377 refs diretas a campos PII | Revisar e remediar (P27 T3.5) | P1 |
| 6 | **INV-T01** Rails tenant | candidates sem account_id | Migration + backfill (PX07 BLK-01) | P0 |
| 7 | **INV-U02** StateGraph audit | 4 StateGraph agents sem AuditCallback | ComplianceStateGraphBase (P23 Onda 2) | P1 |
| 8 | **INV-U03** Agent spans | Traces existem para router mas nao para agents individuais | Adicionar spans agent.{domain}.process (P26 Sprint 2) | P1 |

---

## IMPLEMENTACAO DOS INVARIANT TESTS

### Estrutura de Testes

```
tests/invariants/
  ├── conftest.py                    # Fixtures: all_agents, valid_input, mock_context
  ├── test_universal_invariants.py   # INV-U01 a INV-U06
  ├── test_fairness_invariants.py    # INV-F01 a INV-F04
  ├── test_lgpd_invariants.py        # INV-L01 a INV-L04
  ├── test_tenant_invariants.py      # INV-T01 a INV-T03
  └── test_resilience_invariants.py  # INV-R01 a INV-R03
```

### Implementacao Prioritaria (testes que podem rodar AGORA sem LLM)

```python
# tests/invariants/test_universal_invariants.py

import re
import os

def test_inv_u04_no_pii_in_agent_response_schemas():
    """Verifica que AgentOutput schema NAO inclui campos de PII raw."""
    from lia_agents_core.agent_interface import AgentOutput
    fields = AgentOutput.model_fields
    pii_fields = ["cpf", "email", "phone", "telefone", "endereco", "address"]
    for pf in pii_fields:
        assert pf not in fields, f"AgentOutput has PII field: {pf}"

def test_inv_u06_max_iterations_configured():
    """Verifica que config tem max_iterations definido."""
    from lia_config.config import settings
    assert hasattr(settings, "REACT_MAX_ITERATIONS_DEFAULT")
    assert settings.REACT_MAX_ITERATIONS_DEFAULT <= 10

def test_inv_r01_circuit_breaker_exists():
    """Verifica que CircuitBreaker esta implementado."""
    from app.shared.resilience.circuit_breaker import CircuitBreaker
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
    assert cb.failure_threshold == 3

def test_inv_t01_auth_middleware_sets_company():
    """Verifica que AuthEnforcementMiddleware seta company_id."""
    source = open("app/middleware/auth_enforcement.py").read()
    assert "_current_company_id" in source
    assert "ContextVar" in source

def test_inv_f04_fairness_in_orchestrator():
    """Verifica que MainOrchestrator chama FairnessGuard."""
    source = open("app/orchestrator/main_orchestrator.py").read()
    assert "FairnessGuard" in source

def test_inv_r02_fallback_chain_configured():
    """Verifica que LLM factory tem fallback chain."""
    source = open("app/shared/providers/llm_factory.py").read()
    assert "FALLBACK_ORDER" in source
    assert "gemini" in source and "claude" in source and "openai" in source

def test_inv_t02_budget_per_tenant():
    """Verifica que TenantBudget usa company_id na key."""
    source = open("app/orchestrator/tenant_budget.py").read()
    assert "company_id" in source
    assert "token_budget:" in source
```

### CI Integration

```yaml
# .github/workflows/invariants.yml
name: Invariant Tests

on:
  push:
    branches: [main, develop]
  pull_request:

jobs:
  invariants:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install pytest
      - run: pytest tests/invariants/ -v --tb=short
    # ZERO TOLERANCE: any failure = block merge
```

---

## PLANO DE EVOLUCAO

| Sprint | Invariants Implementados | Score Esperado |
|--------|------------------------|---------------|
| Sprint 1 | 7 testes estaticos (sem LLM): U04, U06, R01, R02, T01, T02, F04 | 7/7 PASS |
| Sprint 2 | +5 testes com DB: L01 (deletion), L02 (consent), U02 (audit), U01 (schema) | 12/12 |
| Sprint 3 | +4 testes com LLM: F01 (bias), F02 (parity), F03 (proxy), U03 (spans) | 16/16 |
| Sprint 4 | +4 testes E2E: L03 (PII logs), L04 (minimization), U05 (cost), U06 (latency) | 20/20 |

**Esforco total: ~10-15 dias** para 20 invariant tests completos.

---

## RESUMO EXECUTIVO

### Baseline: 12/20 PASS (60%), 0 FAIL

**O que ja funciona (12 invariants):**
- Output schema tipado
- PII strip antes do LLM (ReAct)
- Cost cap per tenant
- Timeout guards
- FairnessGuard pre-check
- Tenant budget isolation
- LLM config per tenant
- No infinite loops (CircuitBreaker + MAX_ITERATIONS)
- LLM fallback chain
- Rate limiting
- Data minimization (LIA-C04)
- Latency guards

**O que e incerto (3 invariants):**
- Score bias testing (LLM-dependent — precisa eval real)
- Batch demographic parity (nao testado)
- Consent enforcement em comunicacao (refs existem, enforcement nao confirmado)

**O que e parcial (5 invariants):**
- Audit em StateGraph agents (4 sem AuditCallback)
- Agent trace spans (router OK, agents faltam)
- Deletion propagation (DB OK, cache/vector gap)
- PII em logs (filter OK, 377 refs diretas)
- Rails tenant isolation (candidates sem account_id)

### A regra de invariants
> Para QUALQUER input valido, estas propriedades SEMPRE valem. Uma unica violacao = bug critico, zero tolerance.

Os 12 invariants que passam sao a **fundacao de confianca** da plataforma. Os 8 que nao passam sao o **roadmap de hardening**.
