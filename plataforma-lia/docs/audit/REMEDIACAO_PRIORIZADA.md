# Plano de Remediação Priorizado v1.0
*Versão 1.0 | Data: 2026-04-30 | Baseado em: AUDITORIA_SOBREPOSTA.md v1.0*

> **Convenção:** Cards no formato `R-NNN`, cada um derivado de achado `F-NNN` da Auditoria. **Matriz:** Crítica/P → Wave 0; Crítica/M+G → Wave 1; Alta/P → Wave 0; Alta/M+G → Wave 2; Média/P+M → Wave 3; Média/G → Wave 4; Baixa/P+M → Wave 4; Baixa/G → Excluído. 77 achados auditados → 77 cards de remediação.

---

## Matriz de Priorização

```
                      Esforço
                P (1-2d)  M (3-10d)  G (>10d)
Severidade   ┌──────────┬──────────┬────────┐
Crítica      │  Wave 0  │  Wave 1  │ Wave 1 │
Alta         │  Wave 0  │  Wave 2  │ Wave 2 │
Média        │  Wave 3  │  Wave 3  │ Wave 4 │
Baixa        │  Wave 4  │  Wave 4  │Excluir │
             └──────────┴──────────┴────────┘
```

| Wave | Nome | Cards | Severidades | Esforço Total Estimado |
|---|---|---|---|---|
| **Wave 0** | Quick Wins | 9 | 4×Crítica/P + 5×Alta/P | ~2-3 semanas (paralelo) |
| **Wave 1** | Correção Crítica Estrutural | 3 | 2×Crítica/M + 1×Crítica/G | ~4-6 semanas |
| **Wave 2** | Alta Estrutural | 16 | 14×Alta/M + 2×Alta/G | ~8-12 semanas (2-3 engenheiros) |
| **Wave 3** | Hardening | 32 | 18×Média/P + 14×Média/M | ~8-12 semanas (contínuo) |
| **Wave 4** | Polimento (opcional) | 17 | 2×Média/G + 14×Baixa/P + 1×Baixa/M | Backlog oportunístico |
| **Excluídos** | — | 0 | — | — |
| **Total** | | **77** | | **~22-30 semanas para Wave 0-3** |

**Cronograma macro sugerido (assumindo 2-3 engenheiros backend + 1 compliance + 1 infra):**
- **Semanas 1-3:** Wave 0 — todos os times em paralelo (quick wins de segurança/compliance)
- **Semanas 4-9:** Wave 1 — equipe backend: R-010 → R-011 → R-012 sequenciados por dependência
- **Semanas 10-22:** Wave 2 — sprints de 2 semanas, 2-3 itens por sprint, compliance e backend em paralelo
- **Semanas 23-34:** Wave 3 — hardening contínuo, 3-4 items por sprint
- **Ongoing:** Wave 4 — itens de polimento sem prazo fixo

**Enterprise-ready (SOC 2 / ISO 42001 baseline):** Wave 0 + Wave 1 completos → ~9 semanas

---

## Wave 0 — Quick Wins (9 cards)
*Todos Esforço P (1-2 dias). Executar em paralelo. Bloqueia entrada em produção enterprise.*

---

### R-001: Eliminar bypass BYOK em skills_ontology_engine
- **Achado de origem:** F-001
- **Vista cartográfica afetada:** V12.10 (LLM Factory + BYOK)
- **Componente:** V12.10-LLM4 BYOKSupport
- **Wave:** 0 (Quick Win)
- **Severidade:** Crítica | **Esforço:** Pequeno (1-2 dias)
- **Critério de aceite:**
  - [ ] `app/domains/talent_intelligence/services/skills_ontology_engine.py:531-541` — import `google.generativeai` removido
  - [ ] Substituído por chamada a `get_provider_for_tenant(tenant_id, task="embeddings")`
  - [ ] `os.environ.get("GEMINI_API_KEY")` e `os.environ.get("GOOGLE_API_KEY")` removidos deste arquivo
  - [ ] `python scripts/check_llm_factory_enforcement.py` passa com 0 violações novas
  - [ ] Teste unitário confirma que a chave de API usada é a do tenant (não global)
- **Risco da execução:** baixo — módulo isolado, sem dependências em cascata
- **Dependências:** nenhuma
- **Owner sugerido:** backend

---

### R-002: Adicionar tracking de tokens LLM pré-chamada em todos os callers
- **Achado de origem:** F-205
- **Vista cartográfica afetada:** V12.10 (LLM Factory), V13-F2/F3 (caminhos canônicos)
- **Componente:** V12.10-LLM2 callers
- **Wave:** 0 (Quick Win)
- **Severidade:** Crítica | **Esforço:** Pequeno (1-2 dias)
- **Critério de aceite:**
  - [ ] Todos os 9+ callers de `get_provider_for_tenant()` chamam `track_usage_start(tenant_id, model, domain)` antes de `.complete()`
  - [ ] `track_usage_start` registra no Redis backend do token budget
  - [ ] Arquivos confirmados corrigidos: `wsi/_shared.py:271`, `wsi/reports.py:262`, `candidate_search/archetypes.py:1141` + demais 6
  - [ ] Grafana/Kibana exibe spend de tokens por domínio/tenant dentro de 24h após deploy
- **Risco da execução:** baixo — instrumentação aditiva, sem mudança de comportamento
- **Dependências:** nenhuma
- **Owner sugerido:** backend

---

### R-003: Enriquecer criteria_used no AuditService em decisões críticas
- **Achado de origem:** F-209
- **Vista cartográfica afetada:** V12.5 (Audit Log)
- **Componente:** V12.5-AL3 CriteriaTracking
- **Wave:** 0 (Quick Win)
- **Severidade:** Crítica | **Esforço:** Pequeno (1-2 dias)
- **Critério de aceite:**
  - [ ] `app/shared/compliance/audit_service.py:339,583,615` — `criteria_used=[]` substituído por payload estruturado: `{"model": ..., "prompt_version": ..., "tenant_tier": ..., "fairness_flags": ...}`
  - [ ] `grep -rn "criteria_used=\[\]" app/` retorna 0 resultados em paths de decisão crítica (pipeline transitions, screening, offers)
  - [ ] Teste LGPD explainability: dado um log de decisão, extrai `criteria_used` JSON com ≥3 campos
  - [ ] Teste unitário para `AuditService.log_decision` com payload não vazio
- **Risco da execução:** baixo — campo já é `list` no schema; mudança apenas nos valores passados
- **Dependências:** nenhuma
- **Owner sugerido:** backend + compliance

---

### R-004: Declarar output_schema em todas as ToolDefinitions
- **Achado de origem:** F-212
- **Vista cartográfica afetada:** V9 (Tools e Actions)
- **Componente:** V9-T (todos os tool_registries)
- **Wave:** 0 (Quick Win)
- **Severidade:** Crítica | **Esforço:** Pequeno (1-2 dias)
- **Critério de aceite:**
  - [ ] Todos os 20+ arquivos `*_tool_registry.py` declaram `output_schema: Type[BaseModel]` em cada `ToolDefinition`
  - [ ] `ToolExecutor` valida output via `output_schema.model_validate(result)` antes de retornar ao LLM
  - [ ] `mypy app/domains/**/agents/*_tool_registry.py` passa com 0 erros de retorno não tipificado
  - [ ] Smoke tests de agentes existentes continuam passando
- **Risco da execução:** médio — `output_schema` pode expor callers que fazem cast incorreto; rodar testes completos antes do merge
- **Dependências:** nenhuma
- **Owner sugerido:** backend

---

### R-005: Declarar response_model em todos os endpoints FastAPI críticos
- **Achado de origem:** F-201
- **Vista cartográfica afetada:** A3 (264 routers), V14-CFG
- **Componente:** V14-CFG (routes)
- **Wave:** 0 (Quick Win)
- **Severidade:** Alta | **Esforço:** Pequeno (1-2 dias)
- **Critério de aceite:**
  - [ ] Todos os endpoints WSI, pipeline e sourcing têm `response_model=` Pydantic declarado
  - [ ] `grep -rn "@router\.\(get\|post\|put\|patch\|delete\)(" app/api/v1/wsi/ app/api/v1/pipeline/ | grep -v "response_model"` retorna 0 resultados
  - [ ] OpenAPI spec (`GET /openapi.json`) mostra response schema tipificado para todos esses routers
  - [ ] Testes de contrato existentes passam sem schema mismatch
- **Risco da execução:** médio — adicionar `response_model` ativa serialização Pydantic; respostas com campos extras podem quebrar validação
- **Dependências:** nenhuma
- **Owner sugerido:** backend

---

### R-006: Restringir DEV_MODE a ambientes CI/desenvolvimento (nunca staging/prod)
- **Achado de origem:** F-309
- **Vista cartográfica afetada:** V14-CFG
- **Componente:** V14-CFG (auth_enforcement.py:72-76)
- **Wave:** 0 (Quick Win)
- **Severidade:** Alta | **Esforço:** Pequeno (<1 dia)
- **Critério de aceite:**
  - [ ] `auth_enforcement.py:72-76` — lógica `LIA_DEV_MODE=true` gateada por `ENV in ("test", "development")` — bloqueia se `ENV=staging` ou `ENV=production`
  - [ ] Variável `LIA_DEV_API_KEY` ausente dos templates `.env.staging` e `.env.production`
  - [ ] Teste unitário: `LIA_DEV_MODE=true` + `ENV=production` → request retorna 403
  - [ ] Hook pre-commit bloqueia commit de `.env.staging` com `LIA_DEV_MODE=true`
- **Risco da execução:** baixo — verificar staging atual antes de deploy para garantir que ENV está corretamente configurado
- **Dependências:** nenhuma
- **Owner sugerido:** infra + backend

---

### R-007: Enforçar validação explícita de exp/aud/iss no JWT
- **Achado de origem:** F-318
- **Vista cartográfica afetada:** V14-CFG
- **Componente:** V14-CFG (auth_enforcement.py:247-250)
- **Wave:** 0 (Quick Win)
- **Severidade:** Alta | **Esforço:** Pequeno (1 dia)
- **Critério de aceite:**
  - [ ] `decode_token()` valida explicitamente `exp` (401 se expirado), `aud` (401 se audience incorreto), `iss` (401 se issuer incorreto)
  - [ ] Teste unitário: token expirado → 401
  - [ ] Teste unitário: `aud` errado → 401
  - [ ] Teste unitário: `iss` errado → 401
  - [ ] Nenhuma regressão em tokens válidos
- **Risco da execução:** baixo — validação puramente aditiva; tokens válidos não são afetados
- **Dependências:** nenhuma
- **Owner sugerido:** backend

---

### R-008: Hardening do ContextVar company_id contra JWT forgery
- **Achado de origem:** F-323
- **Vista cartográfica afetada:** V12.11 (Multi-tenancy/RLS)
- **Componente:** V12.11-RLS (auth_enforcement.py)
- **Wave:** 0 (Quick Win)
- **Severidade:** Alta | **Esforço:** Pequeno (1 dia)
- **Critério de aceite:**
  - [ ] `_current_company_id` ContextVar é setado exclusivamente após JWT signature verification passar
  - [ ] `company_id` é extraído exclusivamente das claims do JWT assinado — nunca de request body, query params ou headers customizados
  - [ ] Teste de penetração: `company_id` forjado no body da request não sobrescreve ContextVar
  - [ ] Teste unitário: ContextVar permanece `None` se JWT verification falha
- **Risco da execução:** baixo — se R-007 for implementado primeiro, esta verificação é principalmente confirmação
- **Dependências:** R-007
- **Owner sugerido:** backend

---

### R-009: Confirmar execução do linter BYOK no pipeline CI
- **Achado de origem:** F-325
- **Vista cartográfica afetada:** V12.10 (LLM Factory + BYOK)
- **Componente:** V12.10-LLM5 CILinter
- **Wave:** 0 (Quick Win)
- **Severidade:** Alta | **Esforço:** Pequeno (<1 dia)
- **Critério de aceite:**
  - [ ] `.github/workflows/ci.yml` contém step `python scripts/check_llm_factory_enforcement.py`
  - [ ] Step falha o pipeline se qualquer violação for encontrada (exit code != 0)
  - [ ] Histórico de CI mostra step executando nas últimas 3 runs
  - [ ] Teste: adicionar bypass intencional em arquivo de teste aciona falha no CI
- **Risco da execução:** muito baixo — script já existe; apenas wiring no CI
- **Dependências:** nenhuma
- **Owner sugerido:** infra

---

## Wave 1 — Correção Crítica Estrutural (3 cards)
*Sequenciar: R-010 e R-011 em paralelo, R-012 inicia após R-011.*

---

### R-010: Implementar ToolRegistry tipado com contratos Pydantic de output
- **Achado de origem:** F-200
- **Vista cartográfica afetada:** V9 (Tools e Actions)
- **Componente:** V9-T (todos os tool_registries)
- **Wave:** 1 (Crítica Estrutural)
- **Severidade:** Crítica | **Esforço:** Médio (5-7 dias)
- **Critério de aceite:**
  - [ ] `ToolDefinition` atualizado: `output_schema: Type[BaseModel]` obrigatório; `**kwargs: Any` substituído por `TypedDict` por tool
  - [ ] Todos os 20+ tool registries migrados (sourcing, pipeline, analytics, communication, candidate_self_service, recruiter_assistant, etc.)
  - [ ] `ToolExecutor` valida output via `output_schema.model_validate(result)` antes de retornar
  - [ ] Testes de agentes validam estrutura do output (não apenas non-None)
  - [ ] `mypy --strict app/domains/**/agents/*_tool_registry.py` — 0 erros de `untyped-def`
- **Risco da execução:** alto — superfície grande; alguns tools podem retornar output polimórfico intencionalmente; rodar suite completa de testes antes do merge
- **Dependências:** R-004 (output_schema definido primeiro)
- **Owner sugerido:** backend

---

### R-011: Adicionar company_id a SOXAuditLog + migration + RLS policy
- **Achado de origem:** F-302
- **Vista cartográfica afetada:** V12.5 (Audit Log), V12.11 (Multi-tenancy)
- **Componente:** V12.5-AL1, V12.11-RLS
- **Wave:** 1 (Crítica Estrutural)
- **Severidade:** Crítica | **Esforço:** Médio (7-10 dias)
- **Critério de aceite:**
  - [ ] Modelo `SOXAuditLog` em `libs/models/lia_models/audit_logs.py` ganha `company_id: UUID` NOT NULL
  - [ ] Migration Alembic (≥103) com backfill via JOIN `user_id → users.company_id`
  - [ ] Todos os callers de `AuditService.log_*` populam `company_id` a partir do ContextVar `_current_company_id`
  - [ ] RLS policy `FOR ALL USING (company_id = current_setting('app.current_company_id')::uuid)` adicionada à tabela
  - [ ] Teste de compliance: query cross-tenant retorna 0 rows
  - [ ] Relatório de auditoria SOX scoped corretamente por tenant
- **Risco da execução:** alto — tabela de alta escrita; migration com backfill deve ser zero-downtime; coordenar janela de manutenção
- **Dependências:** R-008 (ContextVar deve ser confiável antes)
- **Owner sugerido:** backend + compliance

---

### R-012: Enforçar get_tenant_db() em todos os repos com raw SQL
- **Achado de origem:** F-306
- **Vista cartográfica afetada:** V12.11 (Multi-tenancy/RLS)
- **Componente:** V12.11-RLS1 (wsi_repository + outros)
- **Wave:** 1 (Crítica Estrutural)
- **Severidade:** Crítica | **Esforço:** Grande (15-20 dias)
- **Critério de aceite:**
  - [ ] Auditoria: `grep -rn "db.execute(text(" app/domains/ app/api/` mapeia todos os 15+ callers
  - [ ] Todos os repos identificados usam `Depends(get_tenant_db)` não `Depends(get_db)` (legacy sem RLS)
  - [ ] `Depends(get_db)` removido de `app/domains/` e `app/api/` (exceto exceções documentadas)
  - [ ] Nova regra de linter (hook pre-commit) bloqueia `Depends(get_db)` em paths de domínio
  - [ ] Teste de integração: query raw em `wsi_repository` retorna apenas rows do tenant corrente
  - [ ] Exceções para queries multi-tenant intencionais (ex: analytics admin) documentadas e revisadas por compliance
- **Risco da execução:** alto — maior escopo de mudança; alguns repos podem ter queries multi-tenant intencionais (admin analytics); documentar exceções antes de migrar
- **Dependências:** R-011 (SOXAuditLog com company_id primeiro)
- **Owner sugerido:** backend

---

## Wave 2 — Alta Estrutural (16 cards)
*Iniciar após Wave 1 aprovado. Sprints de 2 semanas, 2-3 items por sprint em paralelo.*

---

### R-013: Abstrair acoplamento sourcing → credits via evento de domínio
- **Achado de origem:** F-002
- **Vista cartográfica afetada:** V6 (sourcing → credits)
- **Componente:** V6-D1 sourcing, V6-D21 credits
- **Wave:** 2 (Alta Estrutural)
- **Severidade:** Alta | **Esforço:** Médio (5-7 dias)
- **Critério de aceite:**
  - [ ] `sourcing_tool_registry.py:99` — import direto de `credit_service` removido
  - [ ] Substituído por evento de domínio `SourcingCreditConsumed` emitido ao broker
  - [ ] Credits domain tem consumer para `SourcingCreditConsumed`
  - [ ] Teste de integração: operação de sourcing aciona dedução de crédito sem import direto
  - [ ] `isort --check-only app/domains/sourcing/` passa sem imports circulares
- **Risco da execução:** médio — broker assíncrono; estratégia de rollback necessária se evento falhar
- **Dependências:** nenhuma
- **Owner sugerido:** backend

---

### R-014: Abstrair acoplamento sourcing → RAG via interface compartilhada
- **Achado de origem:** F-003
- **Vista cartográfica afetada:** V6 (sourcing → RAG), V12.9
- **Componente:** V6-D1 sourcing, V12.9-RAG
- **Wave:** 2 (Alta Estrutural)
- **Severidade:** Alta | **Esforço:** Médio (5-7 dias)
- **Critério de aceite:**
  - [ ] `sourcing_tool_registry.py` e `pearch_service.py` usam interface abstrata `RAGServicePort` (não `RAGPipelineService` concreto)
  - [ ] `RAGServicePort` reside em `app/shared/` ou `libs/`
  - [ ] Domínio RAG pode ser atualizado/substituído sem tocar sourcing
  - [ ] Testes RAG existentes passam; novo teste de interface adicionado
- **Risco da execução:** médio — design da interface requer alinhamento
- **Dependências:** nenhuma
- **Owner sugerido:** backend

---

### R-015: Quebrar import circular job_management → recruiter_assistant
- **Achado de origem:** F-005
- **Vista cartográfica afetada:** V6 (job_management → recruiter_assistant)
- **Componente:** V6-D19 job_management, V6-D2 recruiter_assistant
- **Wave:** 2 (Alta Estrutural)
- **Severidade:** Alta | **Esforço:** Médio (5-7 dias)
- **Critério de aceite:**
  - [ ] `jd_template_service.py` não importa mais `pipeline_stage_service`
  - [ ] Lógica compartilhada extraída para `app/shared/services/` ou event-driven
  - [ ] `python -m py_compile app/domains/job_management/**/*.py` passa
  - [ ] Teste de import circular: `python -c "import app.domains.job_management; import app.domains.recruiter_assistant"` sem RuntimeError
- **Risco da execução:** médio — lógica compartilhada pode requerer versionamento de API
- **Dependências:** nenhuma
- **Owner sugerido:** backend

---

### R-016: Desacoplar action_handlers de imports diretos de domínio
- **Achado de origem:** F-007
- **Vista cartográfica afetada:** V10 (Cascade Router/Orquestração)
- **Componente:** V10-OR1 (action_handlers/)
- **Wave:** 2 (Alta Estrutural)
- **Severidade:** Alta | **Esforço:** Médio (5-7 dias)
- **Critério de aceite:**
  - [ ] 15+ `app/orchestrator/action_handlers/*.py` usam interfaces/service locator — não imports diretos de domain services
  - [ ] Testes de orchestrator rodam sem instanciar domain services reais
  - [ ] Mudança de assinatura em domain service não quebra testes de orchestrator
  - [ ] Contagem de `mock.patch` em testes de orchestrator diminui (maior testabilidade)
- **Risco da execução:** médio — superfície grande; abordagem faseada recomendada
- **Dependências:** nenhuma
- **Owner sugerido:** backend

---

### R-017: Adicionar company_id a Conversation + migration + RLS
- **Achado de origem:** F-303
- **Vista cartográfica afetada:** V12.11 (Multi-tenancy)
- **Componente:** V12.11-RLS5
- **Wave:** 2 (Alta Estrutural)
- **Severidade:** Alta | **Esforço:** Médio (5-7 dias)
- **Critério de aceite:**
  - [ ] Modelo `conversation.py` ganha `company_id: UUID` NOT NULL
  - [ ] Migration Alembic com backfill via `user_id → users.company_id`
  - [ ] RLS policy adicionada à tabela `conversations`
  - [ ] API de histórico de chat retorna somente conversas do tenant corrente
  - [ ] Teste de isolamento de tenant: tenant B não vê conversas do tenant A
- **Risco da execução:** alto — tabela de alta frequência; migration deve ser zero-downtime
- **Dependências:** R-008, R-011
- **Owner sugerido:** backend

---

### R-018: Adicionar company_id a TechnicalTest + migration + RLS
- **Achado de origem:** F-304
- **Vista cartográfica afetada:** V12.11 (Multi-tenancy)
- **Componente:** V12.11-RLS
- **Wave:** 2 (Alta Estrutural)
- **Severidade:** Alta | **Esforço:** Médio (3-5 dias)
- **Critério de aceite:**
  - [ ] Modelo `technical_tests.py` ganha `company_id: UUID` NOT NULL
  - [ ] Migration com backfill
  - [ ] RLS policy na tabela
  - [ ] Templates de testes técnicos não visíveis cross-tenant
- **Risco da execução:** médio — tabela menor, risco de migration reduzido
- **Dependências:** R-008
- **Owner sugerido:** backend

---

### R-019: Adicionar company_id a ActivityFeed e AgentActivity + RLS
- **Achado de origem:** F-305
- **Vista cartográfica afetada:** V12.11 (Multi-tenancy)
- **Componente:** V12.11-RLS (activity_feed.py, agent_activity.py)
- **Wave:** 2 (Alta Estrutural)
- **Severidade:** Alta | **Esforço:** Médio (3-5 dias)
- **Critério de aceite:**
  - [ ] Ambos os modelos ganham `company_id: UUID` NOT NULL
  - [ ] Migrations com backfill para ambas as tabelas
  - [ ] RLS policies adicionadas
  - [ ] Dashboards de observabilidade escopados por tenant
  - [ ] Exceções para queries admin multi-tenant documentadas e revisadas
- **Risco da execução:** médio — queries de analytics podem ser intencionalmente multi-tenant; documentar exceções
- **Dependências:** R-008
- **Owner sugerido:** backend

---

### R-020: Adicionar legal_basis_id e consent_version_id a modelos PII
- **Achado de origem:** F-312
- **Vista cartográfica afetada:** V12.6 (LGPD)
- **Componente:** V12.6-LGPD2
- **Wave:** 2 (Alta Estrutural)
- **Severidade:** Alta | **Esforço:** Médio (7-10 dias)
- **Critério de aceite:**
  - [ ] `candidate.py` e `client_user.py` ganham `legal_basis_id: UUID` FK → tabela `legal_basis`
  - [ ] `consent_version_id: UUID` FK → `consent_versions` (nullable para registros legados)
  - [ ] API LGPD DSR retorna `legal_basis` por campo PII sob demanda
  - [ ] Teste Art. 18: resposta a requisição de acesso inclui base legal por campo
  - [ ] Migration com default `legal_basis='LEGITIMATE_INTEREST'` para rows existentes (temporário, a ser revisado por compliance)
- **Risco da execução:** alto — requer coordenação com equipe compliance para atribuição de base legal
- **Dependências:** nenhuma
- **Owner sugerido:** backend + compliance

---

### R-021: Adicionar filtro PII pós-compliance em chunks SSE
- **Achado de origem:** F-315
- **Vista cartográfica afetada:** V12.2 (PII), V13-F2
- **Componente:** V12.2-PII1 (agent_chat_sse.py:235-250)
- **Wave:** 2 (Alta Estrutural)
- **Severidade:** Alta | **Esforço:** Médio (5-7 dias)
- **Critério de aceite:**
  - [ ] `agent_chat_sse.py:235-250` — cada chunk yielded passa por `pii_masking.mask(chunk, tenant_pii_config)`
  - [ ] Mascaramento por chunk não quebra UX de streaming (sem buffering artificial)
  - [ ] Teste de integração: stream com CPF de candidato retorna CPF mascarado ao cliente
  - [ ] Teste de performance: latência SSE aumenta <50ms por mensagem
- **Risco da execução:** médio — mudança no pipeline de streaming; testar regressão de latência cuidadosamente
- **Dependências:** nenhuma
- **Owner sugerido:** backend

---

### R-022: Adicionar filtro PII pós-compliance em chunks WebSocket
- **Achado de origem:** F-316
- **Vista cartográfica afetada:** V12.2 (PII)
- **Componente:** V12.2-PII1 (agent_chat_ws.py)
- **Wave:** 2 (Alta Estrutural)
- **Severidade:** Alta | **Esforço:** Médio (3-5 dias)
- **Critério de aceite:**
  - [ ] `agent_chat_ws.py` aplica mesmo mascaramento por chunk que R-021
  - [ ] Teste e2e WebSocket com conteúdo PII: mascarado em trânsito
  - [ ] Nenhuma regressão de desconexão WebSocket
- **Risco da execução:** médio — mesmo padrão de R-021; implementar após R-021 validado
- **Dependências:** R-021
- **Owner sugerido:** backend

---

### R-023: Instrumentar AuditService.log_decision em handlers de API
- **Achado de origem:** F-324
- **Vista cartográfica afetada:** V12.5 (Audit Log)
- **Componente:** V12.5-AL1
- **Wave:** 2 (Alta Estrutural)
- **Severidade:** Alta | **Esforço:** Médio (5-7 dias)
- **Critério de aceite:**
  - [ ] `grep "AuditService.log_decision" app/api/v1/` retorna ≥10 matches (atualmente 0)
  - [ ] Handlers de pipeline transition, screening decision e offer creation chamam `log_decision` com `criteria_used` não vazio
  - [ ] Teste de compliance: audit trail mostra registro de decisão para cada ação via API
  - [ ] Nenhuma regressão de performance (log assíncrono não bloqueia request)
- **Risco da execução:** baixo — chamadas aditivas; log assíncrono não bloqueia
- **Dependências:** R-003 (criteria_used deve ser não vazio)
- **Owner sugerido:** backend + compliance

---

### R-024: Adicionar testes unitários para hiring_policy; marcar policy/ deprecated
- **Achado de origem:** F-401
- **Vista cartográfica afetada:** V6 (hiring_policy domain)
- **Componente:** V6-D9
- **Wave:** 2 (Alta Estrutural)
- **Severidade:** Alta | **Esforço:** Médio (5-7 dias)
- **Critério de aceite:**
  - [ ] `tests/domains/hiring_policy/` tem ≥10 testes unitários cobrindo lógica de avaliação de policy
  - [ ] `app/domains/policy/` tem docstring `@deprecated: use hiring_policy`
  - [ ] Coverage CI para `hiring_policy` ≥80%
  - [ ] Nenhuma regressão em testes existentes
- **Risco da execução:** baixo — testes aditivos; anotação deprecated sem impacto em runtime
- **Dependências:** pode rodar em paralelo com R-025
- **Owner sugerido:** backend

---

### R-025: Remover 14 services deprecated do codebase
- **Achado de origem:** F-408
- **Vista cartográfica afetada:** V6 (domains), V7 (agentes)
- **Componente:** V6 (app/shared/services/)
- **Wave:** 2 (Alta Estrutural)
- **Severidade:** Alta | **Esforço:** Médio (5-7 dias)
- **Critério de aceite:**
  - [ ] `grep -rn "from app.shared.services" app/ tests/` retorna 0 imports de callers não-deprecated
  - [ ] `bias_audit_service.py` — funcionalidade migrada ou deletada com issue de rastreamento
  - [ ] 14 services deletados; CI passa (zero erros de import)
  - [ ] `app/shared/services/` reduzido a ≤5 arquivos
- **Risco da execução:** médio — grep pode perder imports dinâmicos (`importlib`); rodar suite completa antes da deleção
- **Dependências:** nenhuma
- **Owner sugerido:** backend

---

### R-026: Consolidar policy/ em hiring_policy/; deletar stub legado
- **Achado de origem:** F-410
- **Vista cartográfica afetada:** V6 (domains)
- **Componente:** V6-D9 hiring_policy + policy legacy
- **Wave:** 2 (Alta Estrutural)
- **Severidade:** Alta | **Esforço:** Médio (3-5 dias)
- **Critério de aceite:**
  - [ ] `app/domains/policy/` tem 0 importadores ativos no código de produção
  - [ ] Qualquer lógica única em `policy/` migrada para `hiring_policy/`
  - [ ] Diretório `policy/` deletado; sem referências em Celery tasks ou imports dinâmicos
  - [ ] Todos os testes passando pós-deleção
- **Risco da execução:** médio — verificar tasks Celery e imports dinâmicos antes de deletar
- **Dependências:** R-024, R-025
- **Owner sugerido:** backend

---

### R-027: Adicionar testes unitários aos 22 domínios sem cobertura
- **Achado de origem:** F-400
- **Vista cartográfica afetada:** V6 (domains)
- **Componente:** V6-D17, D32, D33-D63 (22 domínios)
- **Wave:** 2 (Alta Estrutural)
- **Severidade:** Alta | **Esforço:** Grande (15-20 dias)
- **Critério de aceite:**
  - [ ] Cada um dos 22 domínios tem ≥1 arquivo de teste em `tests/domains/<domain>/`
  - [ ] Domínios críticos (talent_intelligence, data_subject, digital_twin, trust_center) com ≥5 testes cada
  - [ ] Contagem total de arquivos de teste aumenta em ≥100
  - [ ] `pytest tests/domains/` passa com ≥80% de cobertura nos arquivos novos
- **Risco da execução:** médio — alguns domínios podem exigir mocking de dependências complexas
- **Dependências:** nenhuma
- **Owner sugerido:** backend

---

### R-028: Deprecar orchestrator.py e consolidar em main_orchestrator.py
- **Achado de origem:** F-409
- **Vista cartográfica afetada:** V10 (Cascade Router/Orquestração)
- **Componente:** V10-OR1 + orchestrator.py legacy
- **Wave:** 2 (Alta Estrutural)
- **Severidade:** Alta | **Esforço:** Grande (15-20 dias)
- **Critério de aceite:**
  - [ ] `app/orchestrator/orchestrator.py` (596L) tem 0 callers não-deprecated no código de produção
  - [ ] Toda funcionalidade única de `orchestrator.py` extraída e integrada em `main_orchestrator.py` ou `cascaded_router.py`
  - [ ] `orchestrator.py` deletado ou substituído por shim com `DeprecationWarning`
  - [ ] Suite completa de smoke tests passa com 0 regressões
  - [ ] Testes de integração de agentes confirmam que todos os 32 tipos de agente ainda roteiam corretamente
- **Risco da execução:** alto — orchestrator é o caminho crítico de todas as invocações de agente; migração faseada obrigatória
- **Dependências:** R-016 (action_handlers desacoplados primeiro)
- **Owner sugerido:** backend

---

## Wave 3 — Hardening (32 cards)
*Sprints contínuos de melhoria. 3-4 items por sprint em paralelo.*

---

### R-029: Corrigir bypass google.genai em teams_orchestrator_bridge
- **Achado de origem:** F-015
- **Vista cartográfica afetada:** V6 (communication), V12.10
- **Componente:** V6-D5, V12.10-LLM4
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] `teams_orchestrator_bridge.py:261,375` — import `google.genai` substituído por `get_provider_for_tenant()` ou path adicionado à ALLOWLIST com justificativa
  - [ ] BYOK linter passa com 0 violações novas
- **Risco da execução:** baixo — **Dependências:** R-001, R-009 — **Owner sugerido:** backend

---

### R-030: Auditar voice_screening_orchestrator quanto ao google.genai
- **Achado de origem:** F-016
- **Vista cartográfica afetada:** V6 (voice), V12.10
- **Componente:** V6-D16, V12.10-LLM4
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] `voice_screening_orchestrator.py:929` — verificar se está na ALLOWLIST do linter; se não, migrar para factory (mesmo padrão R-029)
  - [ ] BYOK linter passa; decisão documentada no ALLOWLIST com comentário de justificativa
- **Risco da execução:** baixo — **Dependências:** R-001, R-009 — **Owner sugerido:** backend

---

### R-031: Corrigir Pydantic Optional excessivo em CandidateUpdate
- **Achado de origem:** F-202
- **Vista cartográfica afetada:** V6-D18 (candidates)
- **Componente:** V6-D18 candidate.py schemas
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] Schema `CandidateUpdate` separado em `CandidateCreate` (campos required) e `CandidatePatch` (todos Optional) por operação
  - [ ] Validadores rejeitam `CandidateCreate` sem campos obrigatórios (name, company_id)
  - [ ] Testes de contrato atualizados e passando
- **Risco da execução:** médio — breaking change para consumidores que fazem PATCH com create — **Dependências:** R-005 — **Owner sugerido:** backend

---

### R-032: Adicionar return types explícitos em MainOrchestrator
- **Achado de origem:** F-203
- **Vista cartográfica afetada:** V10-OR1
- **Componente:** V10-OR1 (main_orchestrator.py:346-390)
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] `process()` e todos os métodos públicos têm `-> ChatResponse` ou `-> Optional[ChatResponse]`
  - [ ] `mypy app/orchestrator/main_orchestrator.py` passa com 0 erros
- **Risco da execução:** baixo — **Dependências:** nenhuma — **Owner sugerido:** backend

---

### R-033: Substituir raw tuple returns em wsi_repository por TypedDict/NamedTuple
- **Achado de origem:** F-204
- **Vista cartográfica afetada:** V12.8 (Memory), V6-D16 (voice/wsi)
- **Componente:** V12.8-MEM1
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] `wsi_repository.get_session()` retorna `WSISession` NamedTuple ou TypedDict
  - [ ] Todos os callers com `session[0]`, `session[1]` etc. atualizados para atributos nomeados
  - [ ] Type checker não reporta index access em tuple
- **Risco da execução:** baixo — **Dependências:** nenhuma — **Owner sugerido:** backend

---

### R-034: Propagar correlation_id para chamadas DB/LLM/cache
- **Achado de origem:** F-206
- **Vista cartográfica afetada:** V14-CFG (RequestIdMiddleware)
- **Componente:** V14-CFG (middleware/request_id.py)
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] `request.state.request_id` injetado no DB session header (`SET LOCAL application_name = :request_id`)
  - [ ] LLM factory calls incluem `metadata.request_id` em spans LangSmith/OTel
  - [ ] Redis cache calls usam `x-request-id` como prefixo de chave ou header
  - [ ] Rastreabilidade: dado um `request_id`, trace completo reconstruível
- **Risco da execução:** baixo — instrumentação aditiva — **Dependências:** R-035 — **Owner sugerido:** backend

---

### R-035: Conectar LangSmith com Anthropic/OpenAI clients
- **Achado de origem:** F-211
- **Vista cartográfica afetada:** V12.10 (LLM Factory), V14-CFG
- **Componente:** V12.10-LLM2 (llm_factory.py)
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] `configure_langsmith()` em `app/shared/observability/langsmith.py` envolve Anthropic/OpenAI clients via wrapper equivalente a `wrap_openai()`
  - [ ] Dashboard LangSmith exibe traces de chamadas LLM após deploy em staging
  - [ ] `LANGCHAIN_TRACING_V2=true` presente em `.env.staging`
- **Risco da execução:** baixo — pode adicionar latência se LangSmith for remoto; testar com `sample_rate` — **Dependências:** nenhuma — **Owner sugerido:** backend

---

### R-036: Anotar return types nos métodos de fase do orchestrator
- **Achado de origem:** F-213
- **Vista cartográfica afetada:** V10-OR1
- **Componente:** V10-OR1 (main_orchestrator.py:1132,1302,1382,1439)
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] `_handle_pending_action`, `_try_action_executor`, `_process_via_orchestrator` têm `-> ChatResponse` ou `-> Optional[ChatResponse]`
  - [ ] `mypy` passa nesses métodos
- **Risco da execução:** baixo — **Dependências:** R-032 — **Owner sugerido:** backend

---

### R-037: Substituir except silencioso por metric + Sentry breadcrumb em tool wrappers
- **Achado de origem:** F-214
- **Vista cartográfica afetada:** V9 (Tools e Actions)
- **Componente:** V9-T (diversity_tool_registry + 17 outros)
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] `except Exception as e: logger.debug()` em 20+ wrappers substituído por `logger.error() + metrics.increment("tool.error", tags={"tool": name}) + sentry_sdk.add_breadcrumb()`
  - [ ] Sentry exibe breadcrumbs de erros de tool no contexto de erros
  - [ ] Counter Prometheus `tool_errors_total` visível em staging
- **Risco da execução:** baixo — **Dependências:** nenhuma — **Owner sugerido:** backend

---

### R-038: Adicionar DTOs TypedDict a wsi_compact_pipeline
- **Achado de origem:** F-215
- **Vista cartográfica afetada:** V6-D29 (wsi)
- **Componente:** V6-D29 (wsi_compact_pipeline.py)
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] `wsi_compact_pipeline.py:113-150` — returns dict substituídos por TypedDict ou Pydantic DTOs
  - [ ] Callers atualizados; type checker passa
- **Risco da execução:** baixo — **Dependências:** nenhuma — **Owner sugerido:** backend

---

### R-039: Padronizar ResponseEnvelope em todos os endpoints
- **Achado de origem:** F-217
- **Vista cartográfica afetada:** A3 (routers)
- **Componente:** V14-CFG
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] `wsi/sessions.py:34-80` e demais endpoints offenders retornam `ResponseEnvelope` consistente
  - [ ] OpenAPI spec mostra estrutura de envelope uniforme
  - [ ] Testes de integração de API client passam com novo envelope
- **Risco da execução:** médio — breaking change para consumidores; pode exigir bump de versão de API — **Dependências:** R-005 — **Owner sugerido:** backend

---

### R-040: Substituir **kwargs:Any por TypedDict em tool wrappers
- **Achado de origem:** F-219
- **Vista cartográfica afetada:** V9 (Tools)
- **Componente:** V9-T (diversity_tool_registry + outros)
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] `diversity_tool_registry.py:42-80` e todos os registries substituem `**kwargs: Any` por TypedDict com campos nomeados
  - [ ] `mypy --strict` em registries: 0 erros de "Argument not assignable" para kwargs
  - [ ] Testes de chamada de tool via agente passam sem regressão
- **Risco da execução:** médio — TypedDict pode expor callers passando chaves erradas — **Dependências:** R-004, R-010 — **Owner sugerido:** backend

---

### R-041: Adicionar atributos tenant_id/user_id/model a todos os spans OTel
- **Achado de origem:** F-220
- **Vista cartográfica afetada:** V10 (spans), V12 (observabilidade)
- **Componente:** V10-OR1 (cascaded_router.py:173), V12.10-LLM2
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] Spans em `cascaded_router.py:173` incluem atributos `tenant_id`, `user_id`, `model`, `tier`
  - [ ] Spans do LLM factory incluem `model`, `tokens_input`, `tokens_output`, `latency_ms`
  - [ ] Trace filtrado por `tenant_id` retorna apenas spans daquele tenant
- **Risco da execução:** baixo — **Dependências:** R-034 — **Owner sugerido:** backend

---

### R-042: Registrar endpoints health/seed explicitamente em PUBLIC_PATHS
- **Achado de origem:** F-300
- **Vista cartográfica afetada:** V14-CFG
- **Componente:** V14-CFG (auth_enforcement.py PUBLIC_PATHS)
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] `POST /api/v1/health_check/seed` e `/sync-from-library` explicitamente listados em `PUBLIC_PATHS` (se público) ou protegidos por JWT (se privado)
  - [ ] Teste unitário confirma comportamento correto sem JWT
- **Risco da execução:** baixo — **Dependências:** nenhuma — **Owner sugerido:** backend

---

### R-043: Remover exposição de nomes de variáveis de ambiente em logs de erro
- **Achado de origem:** F-307
- **Vista cartográfica afetada:** V14-CFG
- **Componente:** skills_ontology_engine.py
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] Mensagens de erro ao falhar de obter chave API usam `ConfigurationError` genérico sem expor nomes de variável
  - [ ] Logs de traceback em staging não expõem `GEMINI_API_KEY`/`GOOGLE_API_KEY`
- **Risco da execução:** muito baixo — **Dependências:** R-001 — **Owner sugerido:** backend

---

### R-044: Formalizar GUARDRAIL_TOOLS como Enum SafetyCategory
- **Achado de origem:** F-313
- **Vista cartográfica afetada:** V9 (Tools)
- **Componente:** V9-T (pipeline_action_tool_registry.py)
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] `GUARDRAIL_TOOLS` substituído por `class SafetyCategory(str, Enum): MUTATIVE = "mutative"; READONLY = "readonly"`
  - [ ] ToolDefinitions referenciam `SafetyCategory.MUTATIVE` (não string literals)
  - [ ] `mypy` passa em uso de enum
- **Risco da execução:** muito baixo — **Dependências:** R-004 — **Owner sugerido:** backend

---

### R-045: Restringir CORS allow_methods e allow_headers para produção
- **Achado de origem:** F-317
- **Vista cartográfica afetada:** V14-CFG
- **Componente:** V14-CFG (main.py:471)
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] `allow_methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"]` (explícito, não `"*"`) em config de produção
  - [ ] `allow_headers` restrito ao conjunto necessário (Authorization, Content-Type, X-Request-Id)
  - [ ] Teste em staging: método não listado retorna erro CORS 403
- **Risco da execução:** baixo — `CORS_ORIGINS` já restrito em prod — **Dependências:** nenhuma — **Owner sugerido:** backend + infra

---

### R-046: Configurar threshold mínimo de cobertura no pytest CI
- **Achado de origem:** F-406
- **Vista cartográfica afetada:** V14-CFG (CI)
- **Componente:** V14-CFG (pyproject.toml + ci.yml)
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] `pyproject.toml [tool.coverage.report]` tem `fail_under = 70` (inicial; elevar para 80 após Wave 2)
  - [ ] Step CI `pytest --cov --cov-fail-under=70` falha se cobertura cair
  - [ ] Última run de CI mostra cobertura ≥70%
- **Risco da execução:** baixo — pode requerer Wave 2 (R-027) antes de threshold ser atingível — **Dependências:** R-027 — **Owner sugerido:** infra + backend

---

### R-047: Abstrair acoplamento contact_enrichment → candidate_enrichment
- **Achado de origem:** F-004
- **Vista cartográfica afetada:** V6 (sourcing → candidates)
- **Componente:** V6-D1, V6-D18
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Médio
- **Critério de aceite:**
  - [ ] `contact_enrichment_service.py` usa interface abstrata `CandidateEnrichmentPort`
  - [ ] Domain `candidates` implementa a port; `sourcing` depende apenas da interface
  - [ ] Testes unitários mocam a port; sem import direto de candidates em testes de sourcing
- **Risco da execução:** médio — **Dependências:** nenhuma — **Owner sugerido:** backend

---

### R-048: Abstrair wizard_step_service → intent_classifier via interface
- **Achado de origem:** F-006
- **Vista cartográfica afetada:** V6 (job_management), V12.4
- **Componente:** V6-D19, V12.4-IC1+IC2
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Médio
- **Critério de aceite:**
  - [ ] `wizard_step_service/_shared.py` usa `IntentClassifierPort` — não import direto
  - [ ] Factory seleciona `intent_classifier.py` vs `enhanced_intent_classifier.py` em startup
  - [ ] Teste unitário: mock da port permite testar lógica de wizard independente de AI
- **Risco da execução:** médio — requer definição de lógica de seleção do factory — **Dependências:** nenhuma — **Owner sugerido:** backend

---

### R-049: Criar HTTP client factory centralizada com retry/circuit_breaker
- **Achado de origem:** F-008
- **Vista cartográfica afetada:** V5 (HTTP clients)
- **Componente:** V5 (apify, stackoverflow, github, pearch services)
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Médio
- **Critério de aceite:**
  - [ ] `app/shared/http/client_factory.py` com timeout=30s padrão, retry=3, backoff exponencial, integração com `circuit_breaker` existente
  - [ ] 8+ services em `app/domains/sourcing/` migrados para usar factory
  - [ ] Teste unitário: factory respeita timeout configurado; retry ativado em respostas 5xx
- **Risco da execução:** baixo — módulo de circuit_breaker existente reutilizado — **Dependências:** nenhuma — **Owner sugerido:** backend

---

### R-050: Unificar pipeline_tools.py (recruiter_assistant + pipeline → shared)
- **Achado de origem:** F-009
- **Vista cartográfica afetada:** V9 (Tools)
- **Componente:** V9-T (pipeline_tools.py duplicado)
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Médio
- **Critério de aceite:**
  - [ ] `recruiter_assistant/tools/pipeline_tools.py` (244L) e `pipeline/tools/pipeline_tools.py` (320L) unificados em `app/shared/tools/pipeline_tools.py`
  - [ ] Ambos os domains importam do canonical compartilhado
  - [ ] Cobertura de testes 100% no arquivo unificado; sem regressão
- **Risco da execução:** médio — merge pode revelar comportamentos divergidos — **Dependências:** nenhuma — **Owner sugerido:** backend

---

### R-051: Consolidar memory_resolver.py (eliminar duplicata)
- **Achado de origem:** F-011
- **Vista cartográfica afetada:** V12.8 (Memory)
- **Componente:** V12.8-MEM4
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Médio
- **Critério de aceite:**
  - [ ] `app/orchestrator/memory_resolver.py` (380L) identificado como canonical (maior e mais completo)
  - [ ] `app/shared/memory_resolver.py` (209L) removido; callers migrados para path canonical
  - [ ] `grep -rn "from.*memory_resolver import" .` retorna único path canonical
- **Risco da execução:** médio — orchestrator resolver é maior; validar todos os edge cases antes — **Dependências:** nenhuma — **Owner sugerido:** backend

---

### R-052: Adicionar spans OTel aos wrappers de tool_registry
- **Achado de origem:** F-208
- **Vista cartográfica afetada:** V9 (Tools), V12 (observabilidade)
- **Componente:** V9-T (tool_registries) + V12 OTel
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Médio
- **Critério de aceite:**
  - [ ] Cada wrapper nos 30 registries decorado com `@trace_span(name="tool.{tool_name}")`
  - [ ] Spans incluem atributos `tenant_id`, `tool_name`, `success`, `latency_ms`
  - [ ] OTel collector recebe spans de execução de tools em staging
- **Risco da execução:** baixo — decorator aditivo — **Dependências:** R-041 — **Owner sugerido:** backend

---

### R-053: Adicionar incremento de métrica ao evento token_budget_alert
- **Achado de origem:** F-210
- **Vista cartográfica afetada:** V10-SC6, V12 (observabilidade)
- **Componente:** V10-SC6 (tenant_budget.py:251)
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Médio
- **Critério de aceite:**
  - [ ] `tenant_budget.py:251` emite `metrics.increment("tenant.budget.alert", tags={"tenant_id": ..., "threshold": ...})`
  - [ ] Counter Prometheus `tenant_budget_alerts_total` visível em staging
  - [ ] Regra de alerta configurada em Grafana/Alertmanager para counter > 0
- **Risco da execução:** muito baixo — **Dependências:** nenhuma — **Owner sugerido:** backend + infra

---

### R-054: Hardening do fallback JWT Rails; enforçar binding precoce de company_id
- **Achado de origem:** F-310
- **Vista cartográfica afetada:** V14-CFG
- **Componente:** V14-CFG (auth_enforcement.py:249-266)
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Médio
- **Critério de aceite:**
  - [ ] Fallback JWT Rails valida claim `company_id` de forma independente (não resolução tardia)
  - [ ] Se validação Rails falha, request retorna 401 (não fallback para company_id padrão)
  - [ ] Teste de penetração: JWT adulterado com company_id incorreto → 401
- **Risco da execução:** médio — altera fluxo de auth; validação obrigatória em staging antes de deploy — **Dependências:** R-007, R-008 — **Owner sugerido:** backend

---

### R-055: Encriptar campos name/phone via EncryptedFieldMixin
- **Achado de origem:** F-321
- **Vista cartográfica afetada:** V12.2 (PII)
- **Componente:** V12.2-PII4 (encrypted_field_mixin.py)
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Médio
- **Critério de aceite:**
  - [ ] `candidate.py` e `client_user.py` — campos `name` e `phone` usando `EncryptedFieldMixin`
  - [ ] Migration de dados encripta rows existentes em plaintext
  - [ ] Busca por nome usa hash indexado para lookup de igualdade
  - [ ] Auditoria LGPD: export de PII mostra valores encriptados; decriptação apenas com chave do tenant
- **Risco da execução:** alto — impacto de performance em queries por nome; estratégia de índice obrigatória antes da migration — **Dependências:** R-020 — **Owner sugerido:** backend + compliance

---

### R-056: Implementar harness LLM-as-judge em tests/fitness
- **Achado de origem:** F-402
- **Vista cartográfica afetada:** V12.7 (Output Guardrails)
- **Componente:** V12.7 (tests/fitness/)
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Médio
- **Critério de aceite:**
  - [ ] `tests/fitness/` tem ≥5 casos de teste usando LLM-as-judge para qualidade genérica de output
  - [ ] Critérios do judge: relevância, segurança, não-alucinação, grounding factual
  - [ ] Integração com framework `tests/deepeval/` existente
  - [ ] CI executa testes fitness com budget LLM limitado (max_tokens configurável)
- **Risco da execução:** médio — requer alocação de budget de LLM para CI — **Dependências:** nenhuma — **Owner sugerido:** backend

---

### R-057: Verificar e implementar tests/chaos, load, contract, characterization
- **Achado de origem:** F-403
- **Vista cartográfica afetada:** V12 (tests)
- **Componente:** tests/{chaos,load,contract,characterization}/
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Médio
- **Critério de aceite:**
  - [ ] `tests/contract/`: ≥1 teste pact para contrato Rails ↔ FastAPI
  - [ ] `tests/chaos/`: ≥1 cenário de caos (Redis down → graceful fallback verificado)
  - [ ] `tests/load/`: script Locust ou k6 com ≥1 cenário de carga (ex: 100 req/s em `/api/v1/agent/chat`)
  - [ ] `tests/characterization/`: ≥1 teste golden para comportamento atual de agente
- **Risco da execução:** médio — testes contract requerem coordenação com equipe Rails — **Dependências:** nenhuma — **Owner sugerido:** backend

---

### R-058: Datar e atribuir todos os 79 TODOs com owner + referência de issue
- **Achado de origem:** F-411
- **Vista cartográfica afetada:** V6 (domains)
- **Componente:** (grep TODO no codebase)
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Médio
- **Critério de aceite:**
  - [ ] Todos os 79 TODOs seguem formato `# TODO(owner, ISSUE-NNN, 2026-MM-DD): descrição`
  - [ ] `grep -rn "# TODO" app/ | grep -v "TODO("` retorna 0 resultados (nenhum TODO sem formato)
  - [ ] Hook pre-commit bloqueia adição de TODO sem formato correto
- **Risco da execução:** muito baixo — **Dependências:** nenhuma — **Owner sugerido:** backend (todos)

---

### R-059: Converter star imports de __init__.py para exports explícitos
- **Achado de origem:** F-413
- **Vista cartográfica afetada:** V6 (domains)
- **Componente:** (98 arquivos com `from ... import *`)
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Médio
- **Critério de aceite:**
  - [ ] `__init__.py` não-plugin com `import *` substituídos por `__all__ = [...]` explícito
  - [ ] `grep -rn "from.*import \*" app/` retorna ≤10 resultados (exceções de plugin documentadas)
  - [ ] `mypy --strict` não reporta erros de re-export implícito
- **Risco da execução:** baixo — refactor sem mudança de comportamento — **Dependências:** nenhuma — **Owner sugerido:** backend

---

### R-060: Consolidar caminhos Celery; aposentar tasks de agents_legacy.py
- **Achado de origem:** F-422
- **Vista cartográfica afetada:** V7 (Agentes), V4 (Mensageria)
- **Componente:** V7-A* (agents.py vs agents_legacy.py)
- **Wave:** 3 (Hardening)
- **Severidade:** Média | **Esforço:** Médio
- **Critério de aceite:**
  - [ ] Tasks `drift.run_batch`, `agents.wsi_interview.start`, `agents.triagem.run`, `agents.sourcing.search` migradas para `agents.py` canonical ou deletadas se unused
  - [ ] `Celery inspect registered` em staging exibe apenas 1 task por operação
  - [ ] Flower dashboard sem tasks órfãs
  - [ ] Nenhum schedule no celery_beat referencia nome de task legado
- **Risco da execução:** médio — verificar schedules antes de aposentar — **Dependências:** R-028 — **Owner sugerido:** backend

---

## Wave 4 — Polimento (17 cards, opcional)
*Backlog oportunístico. Sem prazo fixo. Executar quando sprint tiver capacidade residual.*

---

### R-061: Unificar query_tools.py em shared/tools/query_tools.py
- **Achado de origem:** F-010 | **Vista:** V9 | **Componente:** V9-T (3× query_tools.py)
- **Wave:** 4 | **Severidade:** Média | **Esforço:** Grande
- **Critério de aceite:**
  - [ ] 3 `query_tools.py` (sourcing, job_management, analytics) unificados em `app/shared/tools/query_tools.py`
  - [ ] Lógica específica de domínio em sub-módulos; lógica compartilhada canonical
- **Risco:** médio — **Dependências:** R-049, R-050 — **Owner:** backend

---

### R-062: Reduzir diretivas type:ignore de 1540 para <200
- **Achado de origem:** F-412 | **Vista:** V6 | **Componente:** (1540 locais)
- **Wave:** 4 | **Severidade:** Média | **Esforço:** Grande
- **Critério de aceite:**
  - [ ] `grep -rn "type: ignore\|pyright: ignore" app/ libs/` retorna <200 ocorrências
  - [ ] Ocorrências remanescentes documentadas com razão (`# type: ignore[assignment] — Pydantic v2 narrowing`)
  - [ ] Contagem de erros `mypy --strict` decresce mensuravelmente
- **Risco:** médio — Pydantic v2 narrowing pode exigir refactor de models — **Dependências:** R-031, R-040 — **Owner:** backend

---

### R-063: Criar factory para seleção do intent_classifier
- **Achado de origem:** F-012 | **Vista:** V12.4 | **Componente:** V12.4-IC2
- **Wave:** 4 | **Severidade:** Baixa | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] `IntentClassifierFactory.get(tier)` retorna instância correta baseada em tier
  - [ ] Todos os callers usam factory — nenhum import direto de classe concreta
- **Risco:** muito baixo — **Dependências:** R-048 — **Owner:** backend

---

### R-064: Remover shim audit_service; enforçar import canonical
- **Achado de origem:** F-013 | **Vista:** V12.5 | **Componente:** V12.5-AL1
- **Wave:** 4 | **Severidade:** Baixa | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] `app/shared/services/audit_service.py` (shim) deletado
  - [ ] `grep -rn "from app.shared.services.audit_service"` retorna 0 resultados
- **Risco:** muito baixo — **Dependências:** R-025 — **Owner:** backend

---

### R-065: Documentar separação de responsabilidades dos filtros PII
- **Achado de origem:** F-014 | **Vista:** V12.2 | **Componente:** V12.2-PII4
- **Wave:** 4 | **Severidade:** Baixa | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] `app/shared/pii_masking.py` — docstring descreve escopo: mascaramento PII genérico (CPF, email, telefone)
  - [ ] `ats_pii_filter.py` — docstring descreve: campos ATS-específicos além do genérico
  - [ ] Decisão de manter (complementares) ou unificar (overlap) documentada e registrada em issue
- **Risco:** muito baixo — **Dependências:** nenhuma — **Owner:** compliance + backend

---

### R-066: Consolidar audit loggers em único path canonical
- **Achado de origem:** F-017 | **Vista:** V12.5 | **Componente:** V12.5-AL1 (3 paths)
- **Wave:** 4 | **Severidade:** Baixa | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] `app/shared/compliance/audit_service.py` é o único canonical
  - [ ] `app/shared/services/audit_service.py` e `libs/audit/lia_audit/` redirecionados ou removidos
  - [ ] `grep "audit_service" app/shared/services/ libs/audit/` retorna 0 imports ativos
- **Risco:** muito baixo — **Dependências:** R-064 — **Owner:** backend

---

### R-067: Criar política global de timeouts HTTP em settings.py
- **Achado de origem:** F-018 | **Vista:** V5 | **Componente:** V5 (httpx clients)
- **Wave:** 4 | **Severidade:** Baixa | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] `settings.py` define `HTTP_TIMEOUT_DEFAULT=30`, `HTTP_TIMEOUT_AI=60`, `HTTP_TIMEOUT_WEBHOOK=10`
  - [ ] Todos os `httpx.AsyncClient(timeout=...)` usam valores de settings
  - [ ] 1 local para ajustar timeouts globalmente
- **Risco:** muito baixo — **Dependências:** R-049 — **Owner:** backend

---

### R-068: Ativar Sentry performance profiling
- **Achado de origem:** F-207 | **Vista:** V14-CFG | **Componente:** V14-CFG (sentry.py)
- **Wave:** 4 | **Severidade:** Baixa | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] `sentry_sdk.init(profiles_sample_rate=0.1)` em config de produção
  - [ ] Dashboard Sentry exibe dados de profiling para ≥1 endpoint
- **Risco:** muito baixo (overhead mínimo com rate=0.1) — **Dependências:** nenhuma — **Owner:** infra

---

### R-069: Propagar request_id a contextos síncronos do LLM factory
- **Achado de origem:** F-216 | **Vista:** V14-CFG | **Componente:** V14-CFG (auth_enforcement.py:296)
- **Wave:** 4 | **Severidade:** Baixa | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] Contextos síncronos spawned em `auth_enforcement.py:296` carregam `request_id` via `contextvars.copy_context()`
  - [ ] Chamadas LLM factory em contextos síncronos incluem request_id em traces
- **Risco:** muito baixo — **Dependências:** R-034 — **Owner:** backend

---

### R-070: Adicionar job de alerta antecipado de expiração de retenção
- **Achado de origem:** F-218 | **Vista:** V12.5 | **Componente:** V12.5-AL5 RetentionPolicy
- **Wave:** 4 | **Severidade:** Baixa | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] Task Celery beat `compliance.alert_expiry_preview` executa mensalmente
  - [ ] Task envia email para equipe compliance com contagem de registros expirando em ≤90 dias
  - [ ] `RETENTION_PERIODS` config consultado para gerar alertas por tipo
- **Risco:** muito baixo — **Dependências:** nenhuma — **Owner:** compliance + infra

---

### R-071: Documentar campos obrigatórios do UniversalContext
- **Achado de origem:** F-221 | **Vista:** V10-OR1 | **Componente:** V10-OR1 (main_orchestrator.py:346-360)
- **Wave:** 4 | **Severidade:** Baixa | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] Interface `UniversalContext` / `process(ctx)` tem campos obrigatórios documentados em TypedDict ou docstring com `Required[...]`
  - [ ] Campo faltante obrigatório levanta `ContextValidationError` na entrada do orchestrator
- **Risco:** muito baixo — **Dependências:** R-032 — **Owner:** backend

---

### R-072: Deletar agents_legacy.py após confirmar ausência de referências ativas
- **Achado de origem:** F-414 | **Vista:** V8 (Workers), V4 (Mensageria) | **Componente:** V8-W4
- **Wave:** 4 | **Severidade:** Baixa | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] `grep -rn "agents_legacy" app/ tests/` retorna 0 resultados não-test
  - [ ] 4 tasks Celery confirmadas ausentes do registro do worker (`Celery inspect registered`)
  - [ ] `agents_legacy.py` deletado; CI passa
- **Risco:** baixo — confirmar reinício do worker Celery após aposentadoria das tasks — **Dependências:** R-060 — **Owner:** backend

---

### R-073: Deletar ou implementar domínio stub recruitment_journey
- **Achado de origem:** F-416 | **Vista:** V6 | **Componente:** V6-D23
- **Wave:** 4 | **Severidade:** Baixa | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] Decisão de produto documentada: deletar stub OR implementar com issue e prazo
  - [ ] Se deletado: `grep -rn "recruitment_journey" app/ tests/` retorna 0 imports ativos
  - [ ] Se mantido: issue criada com definição de escopo e deadline
- **Risco:** muito baixo — **Dependências:** nenhuma — **Owner:** backend (decisão de produto)

---

### R-074: Reduzir densidade de comentários em main_orchestrator.py para ≤5%
- **Achado de origem:** F-417 | **Vista:** V10-OR1 | **Componente:** V10-OR1 (main_orchestrator.py)
- **Wave:** 4 | **Severidade:** Baixa | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] Comentários dead code e TODO-style removidos; ratio comentários/total ≤5%
  - [ ] Comentários removidos preservados no commit message para histórico
- **Risco:** muito baixo — **Dependências:** R-028 — **Owner:** backend

---

### R-075: Converter star imports não-__init__ para imports explícitos
- **Achado de origem:** F-419 | **Vista:** V6 | **Componente:** (10 arquivos não-__init__)
- **Wave:** 4 | **Severidade:** Baixa | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] 10 arquivos não-`__init__.py` com `import *` convertidos para imports explícitos
  - [ ] `grep "from.*import \*" app/ --include="*.py" ! -name "__init__.py"` retorna 0
- **Risco:** muito baixo — **Dependências:** R-059 — **Owner:** backend

---

### R-076: Documentar feature flags em CONFIGURATION.md
- **Achado de origem:** F-423 | **Vista:** V14-CFG | **Componente:** V14-CFG (feature flags)
- **Wave:** 4 | **Severidade:** Baixa | **Esforço:** Pequeno
- **Critério de aceite:**
  - [ ] `docs/CONFIGURATION.md` lista todas as flags `LIA_V2_*` com: propósito, default, como togglear, data de deprecação
  - [ ] Hook pre-commit bloqueia adição de nova flag sem entrada em CONFIGURATION.md
- **Risco:** muito baixo — **Dependências:** nenhuma — **Owner:** infra + backend

---

### R-077: Integrar mutation testing (mutmut) no CI para módulos críticos
- **Achado de origem:** F-407 | **Vista:** V12 (tests) | **Componente:** V12 (pyproject.toml)
- **Wave:** 4 | **Severidade:** Baixa | **Esforço:** Médio
- **Critério de aceite:**
  - [ ] `mutmut` configurado em `pyproject.toml` para módulos críticos: orchestrator, fairness, pii_masking, auth
  - [ ] Job CI semanal executa mutation tests; mutation score >80% em módulos críticos
  - [ ] Mutations que falham rastreadas como issues no backlog
- **Risco:** baixo — mutation testing pode ser lento; executar somente em paths críticos com timeout — **Dependências:** R-046 — **Owner:** backend

---

## Achados Excluídos do Plano

*Nenhum achado com severidade Baixa + Esforço Grande (Baixa/G) foi identificado na auditoria. Portanto, nenhum achado foi excluído do plano de remediação.*

---

## Resumo por Wave

| Wave | Cards | Esforço Total (dias-pessoa) | Severidades incluídas |
|---|---|---|---|
| Wave 0 | 9 | ~12-18 dias | 4×Crítica/P + 5×Alta/P |
| Wave 1 | 3 | ~25-35 dias | 2×Crítica/M + 1×Crítica/G |
| Wave 2 | 16 | ~90-120 dias | 14×Alta/M + 2×Alta/G |
| Wave 3 | 32 | ~90-120 dias | 18×Média/P + 14×Média/M |
| Wave 4 | 17 | ~30-50 dias (oportunístico) | 2×Média/G + 14×Baixa/P + 1×Baixa/M |
| **Total** | **77** | **~247-343 dias-pessoa** | |

**Referência cruzada com Auditoria:** `grep -oE 'F-[0-9]+' REMEDIACAO_PRIORIZADA.md | sort -u | wc -l` deve retornar 77. Cada achado `F-NNN` de `AUDITORIA_SOBREPOSTA.md` aparece exatamente uma vez como `Achado de origem` neste documento.

*Fim do Plano de Remediação Priorizado v1.0. Todos os 77 cards R-NNN derivados de achados F-NNN com IDs cartográficos referenciados, critérios de aceite verificáveis e owners sugeridos.*
