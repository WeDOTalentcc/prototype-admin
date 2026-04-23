# Auditoria — Gap Analysis: Backend Rails

## Contexto

O documento de arquitetura do especialista de IA propoe uma camada robusta de auditabilidade (secao 7). Esta analise mapeia o que **ja existe neste projeto Rails**, o que **e responsabilidade do projeto Python (agente)**, e o que **de fato falta implementar aqui**.

---

## O que JA EXISTE neste projeto

### 1. ActivityLog — Audit trail de CRUD (tenant-scoped)

| Item | Detalhe |
|---|---|
| Modelo | `ActivityLog` — `reference_type`, `reference_id`, `action`, `changeset` (JSONB), `user_id`, `category`, `ip_address` |
| Concern | `HasActivityLog` — callbacks automaticos em `after_create`, `after_update`, `after_destroy` |
| Modelos cobertos | `Job`, `Apply`, `Candidate` |
| Funcionalidades | Registra changeset (from/to por campo), suporta rollback de updates, Searchkick indexado |
| Arquivos | `app/models/concerns/has_activity_log.rb`, `app/models/activity_log.rb` |

### 2. AuditLog — Auditoria de seguranca/SSO (tenant-scoped)

| Item | Detalhe |
|---|---|
| Modelo | `AuditLog` — `action`, `resource_type`, `resource_id`, `metadata` (JSONB), `ip_address`, `user_agent`, `workos_event_id` |
| Service | `Workos::AuditService` — registra eventos e sincroniza com WorkOS Audit Logs |
| Uso atual | Login SSO, eventos de autenticacao |
| Arquivos | `app/models/audit_log.rb`, `app/services/workos/audit_service.rb` |

### 3. LlmUsage — Tracking de chamadas LLM (public schema)

| Item | Detalhe |
|---|---|
| Modelo | `LlmUsage` — `model`, `operation`, `input_tokens`, `output_tokens`, `total_tokens`, `cost_usd`, `latency_ms`, `success`, `error_message`, `context` (JSONB) |
| Services | `Llm::UsageTracker` (wrapper generico), tracking direto no `GeminiClient` |
| Funcionalidades | Registra cada chamada LLM individual com tokens, custo calculado, latencia, contexto |
| Arquivos | `app/models/llm_usage.rb`, `app/services/llm/usage_tracker.rb`, `app/services/gemini_client.rb` |

### 4. LlmQuota + LlmQuotaUsage — Rate limiting por tenant (public schema)

| Item | Detalhe |
|---|---|
| Modelos | `LlmQuota` (planos starter/pro/enterprise/custom, limites mensais, burst RPM), `LlmQuotaUsage` (consumo acumulado por periodo) |
| Service | `Llm::RateLimiter` — verifica burst, custo mensal, requests mensais antes de cada chamada |
| Jobs | `Llm::MonthlyQuotaSetupJob`, `Llm::QuotaUsageSyncJob`, `Llm::ExpireExtraBudgetJob` |
| Equivale no doc a | Secao 13.6 "Rate Limiting por Empresa" |
| Arquivos | `app/models/llm_quota.rb`, `app/models/llm_quota_usage.rb`, `app/services/llm/rate_limiter.rb`, `app/services/llm/cost_calculator.rb` |

---

## O que NAO EXISTE e NAO e responsabilidade deste projeto

Estes itens sao 100% do **projeto Python (agente LangGraph)**. O Rails nao precisa implementar nada para eles:

| Feature | Secao no doc | Por que e do Python |
|---|---|---|
| AuditCallback (LangGraph) | 7.3 | E um `BaseCallbackHandler` do LangChain/LangGraph que intercepta nos, tools e chamadas LLM dentro da execucao do grafo. Codigo 100% Python. |
| Agent execution tracking (gravar `execution_id`, `nodes_visited`, `tools_used`, `confidence`) | 7.2 | O agente Python e quem executa o grafo e conhece os nos/tools/confidence. Ele grava no banco dele (Alembic/SQLAlchemy) ou no S3. |
| Log pesado em S3/GCS (prompts completos, respostas brutas, state snapshots) | 7.2 | O agente Python e quem tem acesso ao prompt completo e resposta bruta da LLM. Ele grava no S3. |
| Reconstrucao de timeline | 7.4 | Endpoint do Python — ele le seus proprios dados de auditoria (PG + S3) e monta a timeline. |
| Orquestrador (escada de custo, roteamento Tier 0-3) | 4 | Logica 100% do agente Python. |
| Cache semantico do roteador | 4.2 | pgvector/Redis gerenciado pelo Python. |
| Checkpoints LangGraph (PostgresSaver) | 5.4 | Tabelas gerenciadas pelo LangGraph no Python. |
| Streaming por no via WebSocket | 5.5 | `astream()` do LangGraph, publicado via WS pelo Python. |
| Metricas de agentes (confianca, iteracoes, tool calls) | 12.2 | Prometheus/metricas coletadas pelo Python. |

---

## O que FALTA neste projeto (acoes reais)

Apenas itens que sao genuinamente responsabilidade do Rails:

### GAP 1 — Expandir HasActivityLog para mais modelos

Hoje apenas `Job`, `Apply`, `Candidate` tem audit trail de CRUD. Modelos com dados sensiveis ou criticos que deveriam ter:

- `SelectiveProcess`
- `Evaluation` / `EvaluationCandidate`
- `Department`
- `Interview`
- `Pipeline` / `PipelineStage`
- `SourcedProfile`
- `Team` / `TeamMember`

**Esforco:** Baixo — adicionar `include HasActivityLog` em cada modelo.

### GAP 2 — Job de retention/cleanup de logs antigos

Nao existe nenhum mecanismo para limpar registros antigos de `activity_logs`, `audit_logs` e `llm_usages`. Com o tempo essas tabelas crescem sem controle.

**Esforco:** Medio — criar Sidekiq cron job que arquiva/deleta registros mais velhos que X dias.

### GAP 3 — PII masking nos logs do Rails

O `ActivityLog` pode registrar mudancas em campos sensiveis (email, telefone, CPF de candidatos) no changeset. Nao existe filtro para mascarar PII antes de gravar.

**Esforco:** Medio — criar concern/utility que sanitiza campos sensiveis no changeset antes de persistir.

---

## Cards Jira

### CARD 1

```
Summary: Expandir HasActivityLog para modelos criticos
Type: Task
Priority: Medium
Labels: audit, backend, tech-debt
Story Points: 3

Description:
h3. Objetivo
Adicionar audit trail de CRUD (ActivityLog) em modelos que atualmente nao registram mudancas.

h3. Modelos a incluir
* SelectiveProcess
* Evaluation
* EvaluationCandidate
* Department
* Interview
* Pipeline / PipelineStage
* SourcedProfile
* Team / TeamMember

h3. Implementacao
Adicionar `include HasActivityLog` em cada modelo listado.

h3. Criterios de aceite
* Cada modelo listado registra create/update/destroy no ActivityLog
* Changeset grava corretamente os campos alterados (from/to)
* Testes existentes continuam passando
* Nenhum impacto de performance perceptivel (callbacks sao leves)
```

### CARD 2

```
Summary: Criar job de retention para logs de auditoria e LLM usage
Type: Task
Priority: Low
Labels: audit, backend, infra
Story Points: 5

Description:
h3. Objetivo
Evitar crescimento indefinido das tabelas de log criando um Sidekiq cron job que arquiva/remove registros antigos.

h3. Tabelas afetadas
* activity_logs — reter 6 meses
* audit_logs — reter 12 meses
* llm_usages — reter 6 meses

h3. Implementacao
* Criar `Audit::RetentionCleanupJob` com Sidekiq
* Configurar no sidekiq-cron (schedule.yml) para rodar 1x/semana
* Usar `find_each` + `delete_all` em batches para nao travar o banco
* Apartment::Tenant.each para activity_logs (tenant-scoped)
* Direto no public para llm_usages e audit_logs

h3. Criterios de aceite
* Job roda sem erros em todos os tenants
* Registros mais antigos que o periodo definido sao removidos
* Log de execucao com contagem de registros removidos
* Rspec cobrindo cenarios de retencao
```

### CARD 3

```
Summary: Implementar PII masking no ActivityLog changeset
Type: Task
Priority: Medium
Labels: audit, backend, lgpd, security
Story Points: 5

Description:
h3. Objetivo
Garantir que campos sensiveis (CPF, email pessoal, telefone, salario) sejam mascarados no changeset do ActivityLog antes de persistir, cumprindo LGPD.

h3. Campos a mascarar
* cpf: "123.456.789-00" → "***.***.789-00"
* email: "joao@email.com" → "joa***@email.com"
* mobile_phone / phone: "(11) 99999-1234" → "(11) *****-1234"
* current_salary / salary_expectation: valor → "***"

h3. Implementacao
* Criar module `PiiMasking` em `app/models/concerns/` ou `app/lib/`
* Integrar no `HasActivityLog#log_activity` antes de gravar o changeset
* Lista de campos sensiveis configuravel por modelo (constante `PII_FIELDS`)

h3. Criterios de aceite
* Changeset gravado no ActivityLog nunca contem valores completos de PII
* Campos nao-PII continuam sendo gravados normalmente
* Rollback continua funcionando (mascarar apenas no log, nao no rollback)
* RSpec validando mascaramento
```

---

## Conclusao

De tudo que o documento de arquitetura propoe na secao de Auditabilidade (secao 7), a grande maioria (AuditCallback, agent execution tracking, S3 logs, timeline, orquestrador) e responsabilidade do **projeto Python/LangGraph**.

No Rails, ja temos a base solida: `ActivityLog`, `AuditLog`, `LlmUsage`, `LlmQuota`. Os 3 gaps reais sao melhorias incrementais de baixo/medio esforco que podem ser priorizadas conforme necessidade.
