# LIA Agent System — Arquitetura-Alvo e Plano de Refatoracao

> Documento gerado a partir de auditoria profunda do codigo (2026-04-12).
> Define o target state da arquitetura e o plano de 7 fases para alcancar.
> Referencia: ARCHITECTURE.md (ADRs 001-007), REFACTOR_PLAN.md, HARDENING_PLAN.md

---

## 1. Diagnostico: Estado Atual

### 1.1 Numeros do Sistema

| Metrica | Valor |
|---------|-------|
| Linhas de codigo Python | 443.086 |
| Endpoints API | 1.716 |
| Dominios total | 62 - 16 AI + 38 CRUD + 8 hibridos |
| Agentes ReAct registrados | 11 |
| Tools no ToolRegistry | Variavel por tenant |
| Arquivos de teste | 378 |
| Cobertura de testes | 45% - target 80% |

### 1.2 O que Funciona Bem

- ComplianceDomainPrompt ABC com 100% adocao nos 15 de 16 AI domains
- Padrao 4-arquivos para agentes: agent + tools + prompt + context + YAML registry
- Abstracao LLM: LLMProviderABC com Claude, Gemini, OpenAI, chaves per-tenant
- LGPD: DSR Art.18, consent versionado SHA256, PII masking, cleanup jobs
- Multi-tenancy RLS PostgreSQL via get_tenant_db
- Circuit breaker, rate limiting Redis, graceful degradation
- Feature flags com rollout per-company
- Libs extraidas: 7 pacotes em libs/
- ARCHITECTURE.md com ADRs enforced por CI

### 1.3 Os 5 Pontos de Quebra End-to-End

Uma demanda do usuario hoje:

```
Usuario envia mensagem
  POST /chat --> MainOrchestrator.process
    SecurityCheck ............ OK
    FairnessGuard ............ OK
    TenantContext ............ OK
    Phase 0: PendingAction
      FALHA: Retorna SEM persistir memoria
    Phase 1: ActionExecutor - regex sobre texto cru
      FALHA: Regex decide sem LLM, sem contexto de conversa
      FALHA: Resultado cru vai direto ao usuario sem interpretacao
      FALHA: Retorna SEM persistir memoria
    Phase 2: CascadedRouter --> Domain --> Agent --> Response
      OK: Memoria persistida
      OK: LLM pode gerar resposta natural
      PARCIAL: LLM recebe so 1 mensagem sem historico como turns
      PARCIAL: 3 agentes sem FairnessGuard direto
```

POST /chat/stream SSE segue caminho SEPARADO:

```
Usuario envia mensagem via stream
  POST /stream --> Claude direto via AsyncAnthropic
    FALHA: SEM MainOrchestrator
    FALHA: SEM compliance, fairness, routing, dominios
```

| Nr | Onde Quebra | Arquivo e Linha | Efeito |
|----|-----------|-----------------|--------|
| 1 | Phase 0/1 retornam antes de persistir memoria | main_orchestrator.py:307,313 | LIA esquece |
| 2 | ActionExecutor usa regex sem LLM sem historico | action_executor/utils.py:81-87 | Intent errado |
| 3 | LLM recebe so 1 mensagem nao turns reais | orchestrator.py:394 | Sem multi-turn |
| 4 | Tool results vao cru ao usuario | main_orchestrator.py:487-495 | Respostas roboticas |
| 5 | SSE bypassa toda a stack | chat.py:686-760 | Zero compliance em streaming |

---

## 2. Arquitetura-Alvo - Target State

```
ENTRY UNIFICADO
  HTTP POST /chat, POST /stream, WebSocket
  TODOS passam pelo mesmo pipeline
       |
       v
MIDDLEWARE LAYER - ja existe, funciona
  Auth JWT, Tenant RLS, Rate Limit, Prompt Injection
       |
       v
MEMORY LAYER - fix: carregar ANTES de qualquer phase
  Redis-backed SessionStore + ConversationMemory
  History carregada como turns reais user/assistant
  Persist em TODAS as phases nao so Phase 2
       |
       v
COMPLIANCE LAYER - fix: enforcement automatico
  FairnessGuard, PII Strip, PromptInjection
  Na base class do agent nao manual por agent
  ComplianceDomainPrompt obrigatorio - registry rejeita
       |
       v
ROUTER LAYER - fix: separar domain de intent
  Fast-path: KeywordIntentMatcher compartilhado em YAML
  LLM fallback quando confidence menor que threshold
  Dominios declaram capabilities: info vs action
       |
       v
AGENT LOOP - fix: SEMPRE, nao opcional
  LLM raciocina --> Tool Call via function calling nativo
  Tool Result --> LLM interpreta --> Response natural
  ToolRegistry como FONTE UNICA, schemas conectados
       |
       v
POST-PROCESSING - fix: TODAS as respostas passam
  FactChecker, AuditService.log_decision, Persist
  Response envelope padronizado
```

### 2.1 Principios Arquiteturais

1. COMPLIANCE OPT-OUT IMPOSSIVEL: a infra garante que TODA execucao passa por compliance
2. UM PIPELINE TODOS OS CAMINHOS: HTTP/SSE/WS passam pelo mesmo processamento
3. LOOP AGENTICO SEMPRE: LLM raciocina antes de agir, interpreta depois de executar
4. FONTE UNICA DE VERDADE: intents em YAML, cache config em 1 lugar, schemas compartilhados
5. MEMORIA PERSISTENTE: toda mensagem salva, historico como turns reais
6. GRACEFUL DEGRADATION: feature flags para rollout gradual de cada mudanca

---

## 3. Mapa de Compliance Cross-Functional

### 3.1 Estado Atual por Agente

| Agente | Fairness | Audit Decision | PII | Tenant | Prompt Injection |
|--------|----------|---------------|-----|--------|-----------------|
| pipeline | OK L3 | OK | OK Auto | OK | OK Domain |
| sourcing | OK L3+HITL | OK | OK Auto | OK | OK Domain |
| cv_screening | OK L2+MW | OK | OK Auto | OK | OK Agent+Domain |
| communication | OK L1 | OK | OK Auto | OK | OK Domain |
| autonomous | OK L1 | OK | OK Auto | OK | OK Domain |
| talent | OK Mixin | PARCIAL | OK Auto | OK | OK Domain |
| kanban | OK Mixin | PARCIAL | OK Auto | OK | OK Domain |
| jobs_management | OK Mixin | PARCIAL | OK Auto | OK | OK Domain |
| policy | OK Instance | PARCIAL | OK Auto | OK | OK Domain |
| analytics | MISSING | PARCIAL | OK Auto | OK | OK Domain |
| automation | MISSING | PARCIAL | OK Auto | OK | OK Domain |
| ats_integration | MISSING | PARCIAL | OK Auto | OK | OK Domain |
| job_creation | BYPASS | PARCIAL | Manual | Parcial | BYPASS |
| agent_studio | OK Domain | PARCIAL | OK Auto | Parcial | OK Domain |

### 3.2 Causa Raiz

Dois caminhos com regras diferentes:
- Via DomainWorkflow: compliance automatica para ComplianceDomainPrompt
- Via _try_react_agent: compliance MANUAL - cada agent decide

Target: compliance AUTOMATICA na base class, impossivel bypass.

### 3.3 Vulnerabilidades de Seguranca - fix imediato

| Vulnerabilidade | Arquivo | Fix |
|----------------|---------|-----|
| Tenant bypass no consent | app/api/v1/granular_consent.py:21-35 | _require_company_id para get_verified_company_id |
| Tenant bypass no bias audit | app/api/v1/bias_audit.py | Mesmo fix |
| DEV_MODE sem API key = admin | app/middleware/auth_enforcement.py | Fail-closed: rejeitar se sem key |

---

## 4. Plano de Implementacao - 7 Fases

### Fase 1: Compliance Enforcement - impossivel bypass

Objetivo: Nenhum agente ou dominio pode escapar de fairness, PII, audit.
Dependencias: Nenhuma - primeira fase
Risco: BAIXO

| Arquivo | Mudanca |
|---------|---------|
| app/domains/base.py | pre_process_compliance e post_process_compliance concretos no DomainPrompt |
| app/domains/registry.py | register_domain REJEITA dominios sem ComplianceDomainPrompt |
| app/domains/job_creation/domain.py | Migrar DomainPrompt para ComplianceDomainPrompt |
| libs/agents-core langgraph_react_base.py | FairnessGuard.check automatico em _process_langgraph |
| libs/agents-core langgraph_react_base.py | AuditService.log_decision automatico em _state_to_output |
| app/domains/workflow.py | pre_process_compliance ANTES de _try_react_agent |
| app/api/v1/granular_consent.py | _require_company_id para get_verified_company_id JWT |
| app/api/v1/bias_audit.py | Mesmo fix tenant bypass |

Verificacao: grep ComplianceDomainPrompt vs DomainPrompt = 0 bypasses

### Fase 2: Memoria e Contexto - LIA lembra tudo

Objetivo: Toda mensagem persistida. LLM recebe historico como turns reais.
Dependencias: Nenhuma - paralela com Fase 1
Risco: MEDIO - feature flag MULTI_TURN_HISTORY

| Arquivo | Mudanca |
|---------|---------|
| app/orchestrator/main_orchestrator.py:288-315 | _setup_conversation_memory ANTES de Phase 0 |
| app/orchestrator/main_orchestrator.py:307,313 | _persist_response apos Phase 0/1 nao pular |
| app/orchestrator/orchestrator.py:394 | ChatPromptTemplate com HumanMessage/AIMessage turns reais |
| app/orchestrator/state_manager.py | Warning log quando fallback in-memory em producao |
| app/orchestrator/action_executor/utils.py:81-87 | Receber history para detectar loops |

Verificacao: 3 mensagens seguidas na mesma conversa - LIA referencia anteriores

### Fase 3: Pipeline Unificado - um caminho sem bypass

Objetivo: SSE passa pelo mesmo pipeline de compliance e routing.
Dependencias: Fase 1
Risco: MEDIO - feature flag SSE_UNIFIED_PIPELINE

| Arquivo | Mudanca |
|---------|---------|
| app/api/v1/chat.py:686-760 | stream_message usa MainOrchestrator |
| app/orchestrator/main_orchestrator.py | Novo metodo process_streaming |

Verificacao: SSE + FairnessGuard executando via log grep

### Fase 4: Loop Agentico Real - LIA pensa antes de agir

Objetivo: LLM raciocina, chama tool, interpreta resultado.
Dependencias: Fases 2 e 3
Risco: ALTO - feature flag AGENTIC_LOOP_ENABLED, rollout por dominio

| Arquivo | Mudanca |
|---------|---------|
| app/tools/registry.py | to_claude_schema e to_gemini_schema conectados ao path |
| app/orchestrator/orchestrator.py:394 | llm.bind_tools com tool_schemas |
| app/orchestrator/main_orchestrator.py:487-495 | LLM interpreta resultado antes de retornar |
| app/orchestrator/action_executor/executor.py | ActionExecutor vira tool provider |
| app/domains/workflow.py | Step de interpretacao LLM pos execute_action |

Verificacao: "como funciona Agent Studio?" gera explicacao nao acao

### Fase 5: Fonte Unica de Intents - config nao codigo

Objetivo: Eliminar 16 _KEYWORD_ACTION_MAP hardcoded. YAML configuravel.
Dependencias: Fase 4
Risco: MEDIO - matcher paralelo antigo+novo

| Arquivo | Mudanca |
|---------|---------|
| app/shared/services/keyword_intent_matcher.py NOVO | KeywordIntentMatcher compartilhado |
| app/domains/*/config/capabilities.yaml NOVO | Intents por dominio em YAML |
| Cada app/domains/*/domain.py | process_intent delega para matcher |
| app/orchestrator/fast_router.py | Carregar patterns de YAML |
| app/orchestrator/action_executor/utils.py | _detect_intent_from_message usa matcher |

Verificacao: Benchmark 200 queries com accuracy >= anterior

### Fase 6: API Contract e Rails Integration

Objetivo: Response envelope padrao. Contrato compartilhado.
Dependencias: Fase 3
Risco: BAIXO a MEDIO

| Arquivo | Mudanca |
|---------|---------|
| app/schemas/api_envelope.py NOVO | APIResponse padrao |
| app/api/v1/*.py multiplos | Retornar APIResponse nao dicts |
| app/shared/messaging/rails_event_schemas.py | event_version + validacao |

Verificacao: APIResponse.model_validate em toda resposta = 0 erros

### Fase 7: Deploy Safety e Consolidacao

Objetivo: Seguranca operacional. Codigo limpo.
Dependencias: Todas anteriores
Risco: BAIXO a MEDIO

| Arquivo | Mudanca |
|---------|---------|
| Dockerfile.prod:39-47 | Alembic fora do CMD |
| .github/workflows/ci.yml:55-56 | Remover --ignore tests/e2e e test_agents |
| .github/workflows/deploy.yml:19-28 | Remover continue-on-error em security |
| app/jobs/celery_tasks.py | Dividir 2108 linhas por dominio |
| app/config/cache_config.py | Consolidar com cache_strategy.py |
| ARCHITECTURE.md | Atualizar ADRs com decisoes desta refatoracao |

Verificacao: CI E2E verde. Security blocking. Arquivos menores que 500 linhas.

---

## 5. Sequenciamento

Fase 1 Compliance e Fase 2 Memoria: PARALELAS sem dependencia

Fase 3 Pipeline: requer Fase 1

Fase 4 Agentic Loop: requer Fases 2 e 3

Fase 5 Intents: requer Fase 4

Fase 6 API/Rails: requer Fase 3, paralela com 4 e 5

Fase 7 Deploy: requer Fase 3, paralela com 4 e 5

---

## 6. Metricas de Sucesso

| Metrica | Antes | Depois |
|---------|-------|--------|
| Como funciona X gera explicacao | Nao | Sim |
| Contexto mantido em 5+ turns | Nao | Sim |
| Dominios sem ComplianceDomainPrompt | 1 | 0 |
| Agentes sem FairnessGuard | 3 | 0 |
| Tenant bypasses raw header | 2 | 0 |
| Caminhos sem compliance | 1 SSE | 0 |
| Phases que persistem memoria | 1 de 3 | 3 de 3 |
| E2E tests rodando em CI | Nao | Sim |
| Security scans blocking | Nao | Sim |
| Cache configs conflitantes | 2 | 1 |

---

## 7. Verificacao End-to-End

Apos todas as fases, testar:

1. CONVERSA MULTI-TURN: Oi - Como funciona a plataforma? - E o Agent Studio? - Cria um agente de sourcing. LIA mantém contexto e resolve cada pedido.

2. COMPLIANCE: Enviar prompt com vies tipo prefira homens. FairnessGuard bloqueia em QUALQUER caminho: chat, SSE, agent.

3. TOOL CALLING: Lista minhas vagas ativas. LLM chama tool, recebe resultado, gera resposta natural.

4. STREAMING COM COMPLIANCE: Usar SSE e verificar que FairnessGuard e routing executam.

5. RESTART RESILIENCE: Reiniciar processo. Conversa anterior recuperada do Redis/PostgreSQL.

---

Documento aprovado em 2026-04-12.
Implementacao inicia por Fases 1 e 2 em paralelo.
Feature flags garantem rollout seguro.


---

## 2026-05-23 · Wave 1+2 + Sprint X.A progress

**Wave 1 Compliance Emergencial · 100% closed (7/7)**
- W1-001 Agent registry canonical (Phase A) · `5a2c883b4`
- W1-002 BaseAgent legacy delete · `2cf3aef1e` · −517 LOC
- W1-003 PolicyEngine V1 delete · `4b697255b` · −176 LOC
- W1-004 ToolExecutor governance (Phase A · Steps 2/7/8) · `293ea1c85`
- W1-005 PromptInjectionGuard hardening · `b4e08cfd7`
- W1-006 Audit hash chain (part 1) · `6a33cd63b` + `42c96c175`
- W1-007 HateSpeechGuard pt-BR 5 layers · `c4330566a`

**Sprint 2.1 · 100% closed (2/2)**
- W2-008 Anthropic prompt caching · `d5965e214` · 50-80% LLM cost economy
- W2-012 LGPD Art 33 region pinning (Phase A) · `bc7a64e27`

**Sprint 2.2 · 100% closed (1/1)**
- W2-009 Idempotency-Key Rails mutations · `9f9d9aba0`

**Sprint 2.3 · Phase A**
- W2-010 Canonical Rails client + OTel (Phase A) · `4a3339701`

**Sprint X.A Quick Wins (Wave 3+4) · em progresso**
- W3-013 Sentry PII 3→12 patterns · `6f9afca35`
- W3-015 FactChecker result wired em c3b post · `ebd6d2381`
- W3-016 LIA_DISABLE_C3B audit event · `ebd6d2381`
- W3-026 partial ToolDefinition.version · `511b14047`
- W3-028 LangSmith fail-fast em prod · `6f9afca35`
- W3-029 Grafana counter names sensor · `511b14047`
- W3-030 OutboxDrainerWorker lifespan wiring · `b3a6acf7f`
- W4-031 requirements.txt deps pin · `b3a6acf7f`
- W4-033 Dead code purge · `ac3f2caad` · −188,739 LOC

**Stats acumulados:** 20 items canonical · 14+ sensores BLOCKING ·
~140 TDD tests verde · −188k LOC líquido pós-W4-033.

Pre-audit framework: 4 parallel agents recon antes de Wave 3 revelou
diagnostic over-stated 14× recorrente — items canonical são
significativamente menores que diagnostic sugere.
