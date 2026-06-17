# MIGRATION_PLAN.md — Plano de Migracao Priorizado
**Protocolo:** P32  
**Data:** 2026-04-14  
**Tech Lead:** Claude Opus 4.6  
**Baseado em:** 38 protocolos de auditoria (P01-P31, PX01-PX07)  
**Contexto:** Frontend + IA no Replit, Backend Rails no GCP. RabbitMQ/Redis sendo configurados no GCP.

**Depende de:** P21-P31 (tudo)  
**Alimenta:** P33-P40

---

## PRINCIPIOS DO PLANO

1. **Nunca reescrever tudo** — migração incremental, produto sempre funcional
2. **Quick wins primeiro** — momentum gera confiança
3. **Bloqueadores antes de features** — infra antes de agentes
4. **Cada task tem "done" = teste** — sem task sem critério de verificação
5. **Risco mínimo** — mudanças estruturais nos momentos certos

---

## WAVE 0: DESBLOQUEADORES (Semana 1-2)

> Sem esta wave, nada mais funciona. São os 15 bloqueadores do PX07.

### Sprint 0: Config Imediata (~4 horas)

| # | Task | Arquivo(s) | Compl. | Risco | Dep. | Done = |
|---|------|-----------|--------|-------|------|--------|
| 0.1 | **Revogar API Key Atlassian** (PX06-BLK-14) | `/workspace/replit` + admin.atlassian.com | S | BAIXO | — | Key antiga retorna 401 |
| 0.2 | **Fix CORS Rails** → ENV.fetch (PX01-BLK-02) | `config/initializers/cors.rb` | S | BAIXO | — | Requests de prod aceitas |
| 0.3 | **Configurar RAILS_API_URL** (PX01-BLK-03) | Replit Secrets | S | BAIXO | — | `RAILS_ENABLED=True` |
| 0.4 | **Compartilhar JWT SECRET_KEY** (PX01-BLK-04) | Replit Secrets + Rails credentials | S | MEDIO | — | Token Python valido no Rails |
| 0.5 | **Rotear MagicLinksController** (PX01-BLK-05) | `config/routes.rb` | S | BAIXO | — | GET `/v1/auth/magic-link/verify` retorna 200 |
| 0.6 | **Rotear OnboardingController** (PX01-BLK-06) | `config/routes.rb` | S | BAIXO | — | GET `/v1/onboarding/progress` retorna 200 |
| 0.7 | **Configurar MAILGUN_API_KEY** (PX03-BLK-08) | Replit Secrets | S | BAIXO | — | Email real enviado (testar com test@) |
| 0.8 | **Configurar TWILIO + ENVIRONMENT=production** (PX03-BLK-09) | Replit Secrets | S | BAIXO | — | WhatsApp real enviado |
| 0.9 | **Fix JobImportWorker account_id** (PX01-BLK-11) | `app/workers/job_import_worker.rb:35-36` | S | BAIXO | — | Jobs importados com account correto do payload |
| 0.10 | **Fix proxy onboarding fallback** (PX05-BLK-13) | `src/app/api/backend-proxy/onboarding/[...path]/route.ts` | S | BAIXO | — | Retorna 503 se RAILS_BACKEND_URL vazio |
| 0.11 | **Configurar SENTRY_DSN** (PX06) | Replit Secrets + GCP | S | BAIXO | — | Erro capturado aparece no Sentry |
| 0.12 | **Mover DEV_AUTO_LOGIN para .env** (PX06-IND-07) | `docker-compose.yml` → `.env` | S | BAIXO | — | docker-compose sem credenciais |

### Sprint 1: Tenant Isolation + Schema (3-5 dias)

| # | Task | Arquivo(s) | Compl. | Risco | Dep. | Done = |
|---|------|-----------|--------|-------|------|--------|
| 1.1 | **Migration candidates.account_id** (PX01-BLK-01) | Nova migration Rails | M | ALTO | 0.3 | Column existe + index + FK |
| 1.2 | **Backfill account_id** nos candidatos existentes | Script de data migration | M | ALTO | 1.1 | Zero candidates com account_id NULL |
| 1.3 | **rails db:migrate && db:schema:dump** no GCP (PX04-BLK-10) | GCP console | M | MEDIO | 1.1 | schema.rb atualizado com 85 migrations |
| 1.4 | **Fix ResourceLoader** com tenant scope (PX01-BLK-12) | `concerns/resource_loader.rb` | S | MEDIO | 1.1 | find_by filtra por account_id |
| 1.5 | **Fix SearchRenderer** tenant scope (PX01-T03) | `concerns/search_renderer.rb` | S | MEDIO | 1.1 | Elasticsearch filtra por account_id |
| 1.6 | **Add index on users.email** (PX04-IND-09) | Nova migration Rails | S | BAIXO | 1.3 | EXPLAIN mostra index scan |
| 1.7 | **Configurar Sentry no Rails** (PX06-IND-06) | Gemfile + initializer | S | BAIXO | — | Erro Rails capturado no Sentry |

### Sprint 2: Workers + WebSocket (3-5 dias)

| # | Task | Arquivo(s) | Compl. | Risco | Dep. | Done = |
|---|------|-----------|--------|-------|------|--------|
| 2.1 | **Implementar 6 handlers LiaEventsWorker** (PX01-BLK-07) | `workers/lia_events_worker.rb` | M | MEDIO | 0.3, 1.1 | screening/interview/offer/enrichment/pipeline/onboarding processados no DB Rails |
| 2.2 | **WSManager → Redis Pub/Sub** (PX01-BLK-15) | `app/shared/websocket/ws_manager.py` | M | MEDIO | — | WS funciona com 2+ workers |
| 2.3 | **Bunny connection pool** (PX01-PAR-04) | `services/message_service/event_publisher.rb` | S | BAIXO | — | 1 connection reusada |
| 2.4 | **OTEL endpoint configurado** (PX06-IND-05) | Replit Secrets / GCP | S | BAIXO | — | Traces visiveis no GCP Cloud Trace |

**CHECKPOINT WAVE 0:** Integracao basica Rails <> Python funcional. Todos os 15 bloqueadores resolvidos. E2E-06/07 (tenant isolation) e E2E-08 (RabbitMQ) passam.

---

## WAVE 1: FIO CONDUTOR (Semana 3-6)

> Conectar cross-cutting, fechar loops, padronizar.

### Sprint 3: Compliance + Feedback Loops (5-7 dias)

| # | Task | Arquivo(s) | Compl. | Risco | Dep. | Done = |
|---|------|-----------|--------|-------|------|--------|
| 3.1 | **FairnessGuard post-check em todos agentes** (P23 Onda 1) | `compliance_base.py` | S | BAIXO | — | T-NEW-2 (P28) passa; INV-F01 melhora |
| 3.2 | **CalibrationWeight.load() no EnhancedMixin** (P23 Onda 1) | `enhanced_agent_mixin.py` | S | BAIXO | — | T-NEW-1 (P28) passa; agentes usam weights |
| 3.3 | **CalibrationEvent.record() no EnhancedMixin** (P23 Onda 1) | `enhanced_agent_mixin.py` | S | BAIXO | 3.2 | Calibration events registrados automaticamente |
| 3.4 | **SearchFeedback → re-ranking** (P19-P0) | `multi_strategy_search.py` | M | MEDIO | — | Likes/dislikes influenciam ranking futuro |
| 3.5 | **Consent check antes de comunicacao** (INV-L02) | `communication_tool_registry.py` | S | BAIXO | — | E2E-17 passa; INV-L02 PASS |
| 3.6 | **Deletion propagation para cache/vector** (INV-L01) | `data_subject_requests.py` | M | MEDIO | — | E2E-16 passa; INV-L01 PASS |

### Sprint 4: Observability + CI/CD (5-7 dias)

| # | Task | Arquivo(s) | Compl. | Risco | Dep. | Done = |
|---|------|-----------|--------|-------|------|--------|
| 4.1 | **Agent spans** `agent.{domain}.process` (P26 Sprint 2) | 15 react agents | M | BAIXO | 2.4 | Traces mostram span por agente |
| 4.2 | **LLM spans** com tokens/cost (P26 Sprint 2) | LangGraphReActBase | M | BAIXO | 2.4 | Cost per call visivel no trace |
| 4.3 | **Handoff spans** entre dominios (P26 Sprint 2) | CascadedRouter | S | BAIXO | 4.1 | INV-U03 PASS |
| 4.4 | **CI/CD Python** (PX06-PAR-13) | `.github/workflows/ci-python.yml` | M | BAIXO | — | PRs rodam lint + tests + fitness |
| 4.5 | **CI/CD Frontend** (PX06-PAR-14) | `.github/workflows/ci-frontend.yml` | M | BAIXO | — | PRs rodam lint + typecheck + build |
| 4.6 | **Fitness functions no CI** (P27) | `.github/workflows/fitness.yml` | S | BAIXO | 4.4 | Baseline 8/12 enforced no merge |
| 4.7 | **Alertas CRITICAL no GCP** (P26 Sprint 1) | GCP Cloud Monitoring | M | BAIXO | 0.11 | ALT-C01 a C05 ativos |

**CHECKPOINT WAVE 1:** Cross-cutting enforcement completo. Feedback loops fechados. CI/CD ativo para 3 repos. Observability com tracing e alertas.

---

## WAVE 2: INTELIGENCIA (Semana 7-10)

> Tornar agentes mais inteligentes: prompts, reasoning, eval.

### Sprint 5: Prompt Migration (5-7 dias)

| # | Task | Arquivo(s) | Compl. | Risco | Dep. | Done = |
|---|------|-----------|--------|-------|------|--------|
| 5.1 | **Criar compliance_block.yaml** (P25) | `app/prompts/shared/` | S | BAIXO | — | Bloco de compliance reutilizavel |
| 5.2 | **Criar guardrails_block.yaml** (P25) | `app/prompts/shared/` | S | BAIXO | — | Bloco de guardrails reutilizavel |
| 5.3 | **Migrar 12 DOMAIN_SPECIFIC inline → YAML** (P25/P27-T2.2) | 12 files `*_system_prompt.py` → `config/prompts.yaml` | M | MEDIO | 5.1, 5.2 | T2.2 (P27) passa; zero inline prompts |
| 5.4 | **Platform awareness injection** (P25 Secao 8) | `system_prompt_builder.py` | M | MEDIO | — | Agentes sabem quais integracoes ativas |
| 5.5 | **Protected attributes para YAML** (P22) | `config/protected_attributes.yaml` | S | BAIXO | — | FairnessGuard consome YAML |

### Sprint 6: Eval Framework (5-7 dias)

| # | Task | Arquivo(s) | Compl. | Risco | Dep. | Done = |
|---|------|-----------|--------|-------|------|--------|
| 6.1 | **Eval runner CLI** (P24 Fase 1) | `cli/eval_runner.py` | M | BAIXO | — | `eval run --suite unit` funciona |
| 6.2 | **Golden datasets: 10 screening + 10 sourcing** (P29 Fase 2) | `tests/eval/datasets/` | M | BAIXO | 6.1 | 20 scenarios executaveis |
| 6.3 | **Rubrics YAML para 5 agentes** (P24 Fase 1) | `tests/eval/rubrics/` | S | BAIXO | 6.1 | 5 rubrics completas |
| 6.4 | **Bias probes: 8 pares** (P29) | `tests/eval/datasets/*/bias_probes.yaml` | S | BAIXO | 6.1 | 8 probes executaveis |
| 6.5 | **Unit evals no CI** (P24 Fase 3) | `.github/workflows/eval.yml` | S | BAIXO | 6.1, 4.4 | PRs que tocam agentes rodam evals |

**CHECKPOINT WAVE 2:** Prompts migrados para YAML. Eval framework operacional. Bias probes rodando. Platform awareness ativo.

---

## WAVE 3: INTEGRACAO (Semana 11-14)

> Consertar cadeias verticais, CRUD migration, schema alignment.

### Sprint 7: CRUD Migration (5-7 dias)

| # | Task | Arquivo(s) | Compl. | Risco | Dep. | Done = |
|---|------|-----------|--------|-------|------|--------|
| 7.1 | **Remover job_vacancies/crud.py** do Python (P21) | `app/api/v1/job_vacancies/crud.py` | M | ALTO | 0.3 | CRUD jobs via RAILS_API_URL |
| 7.2 | **Remover candidates/candidates_crud.py** do Python (P21) | `app/api/v1/candidates/candidates_crud.py` | M | ALTO | 1.1 | CRUD candidates via RAILS_API_URL |
| 7.3 | **UUID strategy: fork_uuid no Rails** (P21-G) | Migration Rails `add_column :candidates, :fork_uuid` | M | MEDIO | 1.1 | RailsAdapter lookup por fork_uuid |
| 7.4 | **Atualizar CORS para dominio GCP** (PX06-P1) | Rails cors.rb + Python CORS_ORIGINS | S | BAIXO | — | Dominio real aceito |

### Sprint 8: Vertical Integration Tests (5-7 dias)

| # | Task | Arquivo(s) | Compl. | Risco | Dep. | Done = |
|---|------|-----------|--------|-------|------|--------|
| 8.1 | **E2E-06/07: Tenant isolation tests** (P31 Sprint 1) | `tests/e2e/` | M | BAIXO | 1.1 | PASS com zero vazamento |
| 8.2 | **E2E-02/03/04: Core chain tests** (P31 Sprint 2) | `tests/e2e/` | M | BAIXO | 2.1 | Pipeline + search + screening passam |
| 8.3 | **E2E-08: RabbitMQ propagation** (P31 Sprint 2) | `tests/e2e/` | M | MEDIO | 2.1 | Evento Python persiste no Rails |
| 8.4 | **E2E-01/12: Email + template** (P31 Sprint 3) | `tests/e2e/` | M | BAIXO | 0.7 | Email real + template resolved |

**CHECKPOINT WAVE 3:** CRUD unificado no Rails. UUID alignment. 10+ E2E tests passando.

---

## WAVE 4: ROBUSTEZ (Semana 15-16)

> Hardening, monitoring, cleanup.

### Sprint 9: Hardening (5-7 dias)

| # | Task | Arquivo(s) | Compl. | Risco | Dep. | Done = |
|---|------|-----------|--------|-------|------|--------|
| 9.1 | **ComplianceStateGraphBase** (P23 Onda 2) | Novo base class | M | MEDIO | 3.1 | 4 StateGraph agents com PII+audit |
| 9.2 | **Error hierarchy LIAError** (P22) | `app/shared/errors.py` | M | BAIXO | — | Erros tipados em 10+ endpoints |
| 9.3 | **Audit consolidation** (P22) | `app/shared/compliance/audit_service.py` | M | MEDIO | — | 7 implementacoes → 1 |
| 9.4 | **PII in logs remediation** (P27-T3.5) | 377 refs | M | MEDIO | — | T3.5 PASS |
| 9.5 | **JWT blacklist no logout** (PX06-IND-03) | Redis set | S | BAIXO | — | Token revogado retorna 401 |
| 9.6 | **Atualizar Rails 7.1.0 → 7.1.5+** (PX06-PAR-15) | Gemfile | S | MEDIO | — | CVEs corrigidos |
| 9.7 | **Pin versions Gemfile** (PX06-IND-08) | Gemfile | S | BAIXO | — | elasticsearch, sneakers, jwt pinnados |

### Sprint 10: Dashboards + Monitoring (5-7 dias)

| # | Task | Arquivo(s) | Compl. | Risco | Dep. | Done = |
|---|------|-----------|--------|-------|------|--------|
| 10.1 | **Dashboard agent quality** (P26 Sprint 3) | Frontend `/configuracoes/agent-quality` | M | BAIXO | 4.1 | Scores por agente visiveis |
| 10.2 | **ML Predictions dashboard** (P20-P1) | Frontend page | M | BAIXO | — | Time-to-fill visivel |
| 10.3 | **Calibration dashboard** (P20-P1) | Frontend page | M | BAIXO | 3.2 | Divergencias LIA<>recrutador visiveis |
| 10.4 | **Alertas WARNING** (P26 Sprint 3) | GCP Cloud Monitoring | M | BAIXO | 4.7 | ALT-W01 a W07 ativos |
| 10.5 | **Langfuse integration** (P26 Sprint 3) | Config | S | BAIXO | 2.4 | LLM traces em Langfuse |

**CHECKPOINT WAVE 4:** Plataforma hardened. Dashboards operacionais. Monitoring completo.

---

## WAVE 5: CERTIFICACAO (Semana 17+)

> Provar qualidade mensuravel. ML real. Diferenciacao.

### Sprint 11: Eval + ML (5-7 dias)

| # | Task | Arquivo(s) | Compl. | Risco | Dep. | Done = |
|---|------|-----------|--------|-------|------|--------|
| 11.1 | **Integration evals** (P24 Fase 4) | `tests/eval/` | M | BAIXO | 6.1 | 8 handoff scenarios passam |
| 11.2 | **Adversarial evals** (P24 Fase 5) | `tests/eval/` | M | BAIXO | 6.1 | 8 ataques detectados |
| 11.3 | **Drift monitoring** (P24 Fase 6) | Celery beat + alertas | M | BAIXO | 4.7 | Quality degradation detectada |
| 11.4 | **Treinar primeiro modelo ML real** (P19-P1) | XGBoost time-to-fill | M | MEDIO | dados suficientes | MAE < heuristica atual |
| 11.5 | **Persistir ModelRegistry** em DB (P19-P2) | PostgreSQL | S | BAIXO | — | Models sobrevivem restart |

### Sprint 12: Features Premium (5-7 dias)

| # | Task | Arquivo(s) | Compl. | Risco | Dep. | Done = |
|---|------|-----------|--------|-------|------|--------|
| 12.1 | **Candidate lifecycle model** (P19-P1) | Nova migration + model | M | MEDIO | 1.1 | lead→active→hired→alumni enum |
| 12.2 | **Digital Twin config UI** (P20-P2) | Frontend page | M | BAIXO | — | Tenant configura twins |
| 12.3 | **WSI pesos por tenant** (P19-P2) | CalibrationWeight → WSI | S | BAIXO | 3.2 | 0.70/0.30 configuravel |
| 12.4 | **Personalizacao por recrutador** (P19-P2) | LearningExtractor por user_id | M | MEDIO | — | LIA adapta ao estilo |
| 12.5 | **"Explain Decision" button** (P20-P2) | Frontend component | S | BAIXO | — | Reasoning visivel por score |

**CHECKPOINT WAVE 5:** Qualidade mensuravel. ML real rodando. Features premium ativas.

---

## WAVE 6: CLEANUP (Continuo)

| # | Task | Compl. | Quando |
|---|------|--------|--------|
| 6.1 | Remover LLMProviderFactory deprecated (P22) | S | Qualquer momento apos Wave 1 |
| 6.2 | Remover pagina /funil legacy (PX05-IND-01) | S | Qualquer momento |
| 6.3 | CSP com nonce (PX05-IND-02) | M | Quando Next.js suportar |
| 6.4 | Redis Sentinel/Cluster (PX03-IND-11) | L | Quando escala justificar |
| 6.5 | Redis auth (PX03-IND-12) | S | Wave 4 |
| 6.6 | Encriptar PII no Redis (PX03-IND-13) | M | Wave 4 |
| 6.7 | Apartment elevators (PX01-PAR-01) | M | Quando multi-tenant escalar |
| 6.8 | RBAC enforcement (PX01-PAR-03) | L | Wave 5+ |
| 6.9 | Stripe real (PX03-PAR-05) | M | Quando monetizacao |
| 6.10 | Account lockout (PX06-IND-04) | M | Wave 4 |

---

## TIMELINE VISUAL

```
Semana  1  2  3  4  5  6  7  8  9  10  11  12  13  14  15  16  17  18+
        |-----WAVE 0-----|
        S0  S1  S2
                    |--------WAVE 1--------|
                    S3      S4
                                    |--------WAVE 2--------|
                                    S5      S6
                                                    |--------WAVE 3--------|
                                                    S7      S8
                                                                    |----WAVE 4----|
                                                                    S9      S10
                                                                                |----WAVE 5--->
                                                                                S11     S12
```

---

## METRICAS DE SUCESSO POR WAVE

| Wave | Metrica Chave | Baseline | Meta |
|------|-------------|---------|------|
| **Wave 0** | Bloqueadores PX07 resolvidos | 0/15 | 15/15 |
| **Wave 0** | Conectividade vertical (P31) | 82% | 95% |
| **Wave 1** | Fitness functions (P27) | 8/12 | 12/12 |
| **Wave 1** | Contract tests (P28) | 11/17 | 15/17 |
| **Wave 1** | Invariants (P30) | 12/20 | 16/20 |
| **Wave 2** | Golden scenarios (P29) | 70% estimado | 85% |
| **Wave 2** | Inline prompts (P27-T2.2) | 12 violations | 0 |
| **Wave 3** | E2E tests passando (P31) | 0/18 | 10/18 |
| **Wave 3** | CRUD duplicado | 2 modulos | 0 |
| **Wave 4** | Platform health (PX01) | 50/100 | 80/100 |
| **Wave 4** | ML maturity (P19) | 1.4/5 | 2.5/5 |
| **Wave 5** | Golden scenarios | 85% | 95% |
| **Wave 5** | Agent eval CI | Manual | Automatico |

---

## ESFORCO TOTAL ESTIMADO

| Wave | Sprints | Dias | Pessoas |
|------|---------|------|---------|
| Wave 0 | 3 (S0-S2) | 10-15 | 1-2 devs |
| Wave 1 | 2 (S3-S4) | 10-14 | 1-2 devs |
| Wave 2 | 2 (S5-S6) | 10-14 | 1-2 devs |
| Wave 3 | 2 (S7-S8) | 10-14 | 2 devs |
| Wave 4 | 2 (S9-S10) | 10-14 | 1-2 devs |
| Wave 5 | 2 (S11-S12) | 10-14 | 1-2 devs |
| **TOTAL** | **12 sprints** | **~60-85 dias** | **1-2 devs** |

**Com 1 dev full-time:** ~4-5 meses
**Com 2 devs:** ~2.5-3 meses (waves parcialmente paralelizaveis)

---

## RISCOS E MITIGACOES

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|-------------|---------|-----------|
| Rails migration quebra prod | MEDIA | ALTO | Testar em staging primeiro; backup antes |
| CRUD migration perde dados | MEDIA | ALTO | Fork_uuid garante mapeamento; dual-write durante transicao |
| LLM update degrada qualidade | MEDIA | MEDIO | Eval framework (Wave 2) detecta antes do deploy |
| Redis crash perde estado | MEDIA | ALTO | Redis Sentinel (Wave 6) + graceful degradation |
| Equipe pequena, escopo grande | ALTA | MEDIO | Waves priorizadas — Wave 0-1 ja entregam 80% do valor |

---

## RESUMO EXECUTIVO

### A regra dos 80/20
**Wave 0 + Wave 1 (Semana 1-6) resolvem 80% dos problemas** — bloqueadores, compliance, feedback loops, CI/CD, observability. As waves seguintes sao refinamento.

### Sequencia critica
```
Wave 0 (desbloqueadores) → Wave 1 (fio condutor) → Wave 2 (inteligencia)
  |                           |                         |
  v                           v                         v
  Rails integrado             Cross-cutting completo    Prompts + eval
  Email/WhatsApp real         Feedback loops fechados   CI com quality gates
  Tenant isolation            Tracing + alertas         Bias testing
```

### O que NAO muda
- LangGraph como engine (ja correto)
- ComplianceDomainPrompt enforcement (ja funciona)
- CascadedRouter 8 tiers (ja funciona)
- BFF pattern 478 rotas (ja funciona)
- EnhancedAgentMixin memory/learning (ja funciona)

### O que muda
- Infra de integracao (Rails <> Python)
- Feedback loops (fechados)
- Prompts (YAML + platform awareness)
- Observability (ativado)
- CI/CD (criado)
- Eval framework (criado)
- CRUD unificado (migrado para Rails)

### Custo total
**~60-85 dias de trabalho (4-5 meses com 1 dev, 2.5-3 meses com 2).** Nenhuma reescrita — tudo e completar, conectar, ativar.
