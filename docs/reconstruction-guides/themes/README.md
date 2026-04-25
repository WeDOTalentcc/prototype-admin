# Thematic Operational Docs — LIA Agent System v4

> **🤖 Para AI assistants (Cursor / Claude Code):** leia primeiro [`HOW_TO_USE_WITH_AI_ASSISTANT.md`](HOW_TO_USE_WITH_AI_ASSISTANT.md) — contém 3 prompts prontos (Bootstrap + Implementar + Verificar) que cobrem todo o ciclo de implementação de um layer.

## O que são estes docs

33 "receitas executáveis" para replicar o LIA no produto v5. Cada doc cobre um tema com:
- O mecanismo real (código verificado via SSH no Replit)
- Arquivos conectados (YAMLs + Python)
- Lógica IN/OUT + side effects
- Instruções explícitas para Claude Code / Cursor
- Regras de adaptação (flexível vs imutável por lei/arquitetura)
- Checklist P0/P1/P2 + gotchas + testes

**Princípio:** zero invenção. Toda afirmação tem fonte em código canônico lido do Replit.

---

## Índice dos 33 temas

### Compliance Layer (8 docs)

| # | Doc | Descrição de 1 linha |
|---|-----|---------------------|
| C1 | [C1_FAIRNESS_AND_ANTI_DISCRIMINATION.md](compliance/C1_FAIRNESS_AND_ANTI_DISCRIMINATION.md) | FairnessGuard 3 camadas + 4/5 rule + ação afirmativa + cultural fit como proxy de viés |
| C2 | [C2_LGPD_PII_AND_DATA_MINIMIZATION.md](compliance/C2_LGPD_PII_AND_DATA_MINIMIZATION.md) | PII masking + data minimization + atributos protegidos + LGPD Arts. 6 e 11 |
| C3 | [C3_LGPD_CONSENT_AND_DATA_SUBJECT.md](compliance/C3_LGPD_CONSENT_AND_DATA_SUBJECT.md) | Consentimento + direitos do titular (Arts. 7-9, 15, 17, 18) + repos de consent/DSR |
| C4 | [C4_LGPD_ART20_RIGHT_TO_CONTEST.md](compliance/C4_LGPD_ART20_RIGHT_TO_CONTEST.md) | Direito de contestação de decisão automatizada + Candidate Portal + EU AI Act Art. 86 |
| C5 | [C5_MULTI_TENANCY_AND_ISOLATION.md](compliance/C5_MULTI_TENANCY_AND_ISOLATION.md) | TenantGuard + company_id via JWT + session isolation + token-level enforcement |
| C6 | [C6_PROMPT_INJECTION_AND_ENCRYPTION.md](compliance/C6_PROMPT_INJECTION_AND_ENCRYPTION.md) | 12 regex de injection + C3B layer + Redis encryption + secrets provider |
| C7 | [C7_AUDIT_TRAIL_AND_COMPLIANCE_LINT.md](compliance/C7_AUDIT_TRAIL_AND_COMPLIANCE_LINT.md) | Audit trail S3/file + 13 lint scripts + fairness_audit_log + compliance scoring |
| C8 | [C8_POLICY_ENGINE_AND_GOVERNANCE.md](compliance/C8_POLICY_ENGINE_AND_GOVERNANCE.md) | PolicyEngine runtime + precondition checker + module gating + feature flags governance |

### Infrastructure Layer (11 docs)

| # | Doc | Descrição de 1 linha |
|---|-----|---------------------|
| I1 | [I1_AGENT_ARCHITECTURE.md](infrastructure/I1_AGENT_ARCHITECTURE.md) | LangGraph ReAct base + 15 agent classes + AgentBus + state machine + autonomy engine |
| I2 | [I2_TOOL_ARCHITECTURE.md](infrastructure/I2_TOOL_ARCHITECTURE.md) | @tool_handler canonical surface + HITL + module gating + tool registry |
| I3 | [I3_ORCHESTRATION.md](infrastructure/I3_ORCHESTRATION.md) | 4-phase orchestrator + 8-tier Cascade + fast router + context adapter + tenant budget |
| I4 | [I4_LLM_PROVIDERS.md](infrastructure/I4_LLM_PROVIDERS.md) | BYOK + LLM factory (Anthropic/OpenAI/Gemini) + embedding providers |
| I5 | [I5_OBSERVABILITY.md](infrastructure/I5_OBSERVABILITY.md) | Sentry + OTEL + execution log + agent quality dashboard + drift detection |
| I6 | [I6_API_LAYER_AND_WEBSOCKET.md](infrastructure/I6_API_LAYER_AND_WEBSOCKET.md) | ChatResponse 20 campos + API envelope + WebSocket + streaming + ADR-005/006/008/014 |
| I7 | [I7_INTENT_ROUTING.md](infrastructure/I7_INTENT_ROUTING.md) | Intent classifier + keyword matcher + 17 capabilities.yaml + Tier 1-3 routing |
| I8 | [I8_AUTH_AND_AUTHORIZATION.md](infrastructure/I8_AUTH_AND_AUTHORIZATION.md) | JWT + WorkOS + Rails JWT shared secret + auth enforcement middleware |
| I9 | [I9_DATA_LAYER_AND_MIGRATIONS.md](infrastructure/I9_DATA_LAYER_AND_MIGRATIONS.md) | 95 migrations + 120 models SQLAlchemy + repositories + async session |
| I10 | [I10_MIDDLEWARE_AND_REQUEST_LIFECYCLE.md](infrastructure/I10_MIDDLEWARE_AND_REQUEST_LIFECYCLE.md) | 5 middleware (auth, rate limiter, request_id, response_envelope, trial) + logging |
| I11 | [I11_RAG_SEMANTIC_SEARCH.md](infrastructure/I11_RAG_SEMANTIC_SEARCH.md) | RAG pipeline + RAGAS evaluation + vector semantic cache + embedding service + chunking |
| I12 | [I12_VOICE_SCREENING.md](infrastructure/I12_VOICE_SCREENING.md) | Dois pipelines independentes: Twilio PSTN (~$0.41) + Gemini Live Audio (~$0.065) + WSI scoring + LGPD HTTP 451 |

### Persona Layer (5 docs)

| # | Doc | Descrição de 1 linha |
|---|-----|---------------------|
| P1 | [P1_SYSTEM_PROMPT_COMPOSITION.md](persona/P1_SYSTEM_PROMPT_COMPOSITION.md) | 9 steps de composição + ComplianceDomainPrompt + GuardrailsDomainPrompt + versioning |
| P2 | [P2_AGENT_SPECIALIZATION.md](persona/P2_AGENT_SPECIALIZATION.md) | 11 agent_types + 24 domain YAMLs + system_prompt por agente + capabilities |
| P3 | [P3_CONVERSATION_MEMORY.md](persona/P3_CONVERSATION_MEMORY.md) | 4 camadas de memória: LRU + in-memory + WorkingMemory (PG) + LongTermMemory (PG) |
| P4 | [P4_INTERACTION_PATTERNS.md](persona/P4_INTERACTION_PATTERNS.md) | Anti-sycophancy 3 variantes + CoT + DEFENSIVE_BLOCK + 12 regex de injection |
| P5 | [P5_WIZARD_WSI.md](persona/P5_WIZARD_WSI.md) | LangGraph 11 nós + 2 HITL + FairnessGuard 7 gates + quality score F1.B + geração de perguntas CBI |

### Resilience Layer (4 docs)

| # | Doc | Descrição de 1 linha |
|---|-----|---------------------|
| R1 | [R1_CIRCUIT_BREAKERS.md](resilience/R1_CIRCUIT_BREAKERS.md) | 18 circuits + 4 SLO tiers + DEGRADED_MODE PT-BR + admin REST API |
| R2 | [R2_LEARNING_LOOP_AND_AB_TESTING.md](resilience/R2_LEARNING_LOOP_AND_AB_TESTING.md) | Silent feedback + A/B testing MD5 buckets + calibration + TTF predictor (XGBoost) |
| R3 | [R3_MESSAGING_AND_EVENTS.md](resilience/R3_MESSAGING_AND_EVENTS.md) | BrokerInterface ABC + 3 backends + UnifiedEventPublisher + 13 domain→4 queue map |
| R4 | [R4_BACKGROUND_JOBS_AND_SCHEDULERS.md](resilience/R4_BACKGROUND_JOBS_AND_SCHEDULERS.md) | Celery 4 filas + LIATask DLQ + Beat 14 tasks + DomainTaskManager async |

### Agent Studio Layer (1 doc)

| # | Doc | Descrição de 1 linha |
|---|-----|---------------------|
| AS1 | [AS1_CUSTOM_AGENTS.md](agent_studio/AS1_CUSTOM_AGENTS.md) | CustomAgentRuntime + intelligence floor + PLATFORM_TOOLS_REGISTRY + AgentTemplate versionamento |

### Operational Layer (3 docs)

| # | Doc | Descrição de 1 linha |
|---|-----|---------------------|
| O1 | [O1_TESTING_STRATEGY.md](operational/O1_TESTING_STRATEGY.md) | 5 eval suites + 5 rubrics LLM-as-judge + 8 bias probes + 13 lint scripts |
| O2 | [O2_CONFIGURATION_AND_FEATURE_FLAGS.md](operational/O2_CONFIGURATION_AND_FEATURE_FLAGS.md) | Settings 8 subclasses + FeatureFlagService 3-tier + SecretsProvider + module gating |
| O3 | [O3_EXTERNAL_INTEGRATIONS.md](operational/O3_EXTERNAL_INTEGRATIONS.md) | Rails Client + MultiChannelService 5 canais + sourcing APIs (Pearch, Apify, Gupy, etc.) |

---

## Mapa "recurso → tema principal + temas cross-cutting"

| Recurso a replicar | Tema principal | Temas cross-cutting |
|--------------------|---------------|---------------------|
| FairnessGuard anti-discriminação | C1 | O1 (testes bias), C7 (audit), I1 (agentes) |
| LGPD consentimento e direitos | C3 | C2 (PII), C4 (contestação), I9 (repositories) |
| Portal do candidato | C4 | C3 (consent), I8 (auth), I6 (API) |
| Multi-tenancy JWT | C5 | I8 (auth), I10 (middleware), I9 (data layer) |
| Prompt injection defense | C6 | P4 (interaction patterns), O1 (security tests) |
| Audit trail S3 | C7 | O2 (config), I9 (models) |
| Policy engine | C8 | O2 (feature flags), I2 (tool gating) |
| Agente ReAct LangGraph | I1 | AS1 (custom), I2 (tools), I3 (orchestration) |
| Tool registry | I2 | I1 (agents), C8 (module gating), C7 (lint) |
| Orchestrator cascade | I3 | I7 (intent), I1 (agents), I4 (LLM) |
| BYOK LLM providers | I4 | O2 (config), R1 (circuit breakers), I3 |
| API + WebSocket | I6 | I10 (middleware), I8 (auth) |
| Intent routing | I7 | I3 (orchestration), P2 (capabilities) |
| Auth JWT + WorkOS | I8 | C5 (multi-tenancy), I10 (middleware) |
| Database + migrations | I9 | C7 (fairness_audit_log), I1-I3 |
| System prompt 9 steps | P1 | P2 (specialization), C1 (fairness), C2 (LGPD) |
| Agent specialization | P2 | P1 (composition), I7 (routing), I1 |
| Conversation memory | P3 | I1 (agents), I9 (models) |
| Anti-sycophancy + CoT | P4 | C6 (injection), P1 (composition) |
| Circuit breakers | R1 | O3 (sourcing APIs), I4 (LLM providers) |
| Learning loop | R2 | R4 (celery jobs), I5 (observability) |
| Event broker | R3 | R4 (celery), O3 (notifications) |
| Background jobs | R4 | R2 (learning), R3 (messaging), I5 |
| Custom agents | AS1 | I1 (base), I2 (tools), C1 (compliance) |
| Multi-agent crews (CrewExecutor) | AS1 | I1 (AgentBus), R3 (messaging) |
| Voice screening (PSTN + VoIP) | I12 | C3 (consent), C1 (fairness), C2 (PII), R1 (circuits) |
| Job creation wizard (WSI) | P5 | C1 (fairness 7 gates), C7 (audit), I3 (routing) |
| Testing strategy | O1 | C1 (bias tests), C5 (multi-tenancy tests) |
| Config + flags | O2 | All themes (todos consomem settings) |
| External integrations | O3 | R1 (circuit breakers), C2 (LGPD opt-out) |

---

## Snippet para CLAUDE.md do repo v5

Adicionar no `CLAUDE.md` do repo v5 para que Claude Code indexe todos os temas:

```markdown
## Thematic Operational Docs — LIA v4 Reference

Localização: `docs/reconstruction-guides/themes/`
Índice: `themes/README.md`

### Como usar
Antes de implementar qualquer feature, ler o(s) tema(s) relevante(s).
Cada doc é auto-suficiente — contém código verificado, receitas passo-a-passo e checklists.

### Temas disponíveis (33)

#### Compliance (leitura obrigatória antes de qualquer feature de IA)
- C1 Fairness: themes/compliance/C1_FAIRNESS_AND_ANTI_DISCRIMINATION.md
- C2 LGPD PII: themes/compliance/C2_LGPD_PII_AND_DATA_MINIMIZATION.md
- C3 LGPD Consent: themes/compliance/C3_LGPD_CONSENT_AND_DATA_SUBJECT.md
- C4 Art.20 Contest: themes/compliance/C4_LGPD_ART20_RIGHT_TO_CONTEST.md
- C5 Multi-tenancy: themes/compliance/C5_MULTI_TENANCY_AND_ISOLATION.md
- C6 Prompt Injection: themes/compliance/C6_PROMPT_INJECTION_AND_ENCRYPTION.md
- C7 Audit Trail: themes/compliance/C7_AUDIT_TRAIL_AND_COMPLIANCE_LINT.md
- C8 Policy Engine: themes/compliance/C8_POLICY_ENGINE_AND_GOVERNANCE.md

#### Infrastructure (arquitetura core)
- I1 Agent Arch: themes/infrastructure/I1_AGENT_ARCHITECTURE.md
- I2 Tool Arch: themes/infrastructure/I2_TOOL_ARCHITECTURE.md
- I3 Orchestration: themes/infrastructure/I3_ORCHESTRATION.md
- I4 LLM Providers: themes/infrastructure/I4_LLM_PROVIDERS.md
- I5 Observability: themes/infrastructure/I5_OBSERVABILITY.md
- I6 API+WebSocket: themes/infrastructure/I6_API_LAYER_AND_WEBSOCKET.md
- I7 Intent Routing: themes/infrastructure/I7_INTENT_ROUTING.md
- I8 Auth: themes/infrastructure/I8_AUTH_AND_AUTHORIZATION.md
- I9 Data Layer: themes/infrastructure/I9_DATA_LAYER_AND_MIGRATIONS.md
- I10 Middleware: themes/infrastructure/I10_MIDDLEWARE_AND_REQUEST_LIFECYCLE.md
- I11 RAG: themes/infrastructure/I11_RAG_SEMANTIC_SEARCH.md
- I12 Voice Screening: themes/infrastructure/I12_VOICE_SCREENING.md

#### Persona (comportamento LIA)
- P1 System Prompt: themes/persona/P1_SYSTEM_PROMPT_COMPOSITION.md
- P2 Specialization: themes/persona/P2_AGENT_SPECIALIZATION.md
- P3 Memory: themes/persona/P3_CONVERSATION_MEMORY.md
- P4 Interaction: themes/persona/P4_INTERACTION_PATTERNS.md
- P5 Wizard WSI: themes/persona/P5_WIZARD_WSI.md

#### Resilience
- R1 Circuit Breakers: themes/resilience/R1_CIRCUIT_BREAKERS.md
- R2 Learning Loop: themes/resilience/R2_LEARNING_LOOP_AND_AB_TESTING.md
- R3 Messaging: themes/resilience/R3_MESSAGING_AND_EVENTS.md
- R4 Background Jobs: themes/resilience/R4_BACKGROUND_JOBS_AND_SCHEDULERS.md

#### Agent Studio
- AS1 Custom Agents: themes/agent_studio/AS1_CUSTOM_AGENTS.md

#### Operational
- O1 Testing: themes/operational/O1_TESTING_STRATEGY.md
- O2 Config+Flags: themes/operational/O2_CONFIGURATION_AND_FEATURE_FLAGS.md
- O3 Integrations: themes/operational/O3_EXTERNAL_INTEGRATIONS.md

### Regras de uso
- Compliance themes (C1-C8): ler ANTES de implementar qualquer agente de decisão
- C5 Multi-tenancy: toda operação de leitura/escrita precisa de company_id do JWT
- C1 Fairness: todo agente de scoring/ranking referencia FairnessGuard
- O2 Config: NUNCA hardcodar API keys — sempre via settings ou secrets()
```

---

## Snippets para Cursor rules

### `.cursor/rules/compliance.mdc`

```
---
description: Compliance rules for AI decisions
globs: ["*agent*.py", "*scoring*.py", "*screening*.py", "*ranking*.py"]
---
# Compliance Rules (C1-C8)
- EVERY decision agent: FairnessGuard before LLM call (C1)
- NEVER use: race, religion, gender, ethnicity, marital status, health in AI decisions (C2)
- company_id: ALWAYS from JWT, never from payload (C5)
- Prompt injection: validate against 12 regex patterns before LLM (C6)
- Audit trail: every autonomous decision logged with company_id + agent_id (C7)
- 4/5 rule: selection rate ratio >= 0.80 (NYC LL144) (C1)
Reference: themes/compliance/
```

### `.cursor/rules/infrastructure.mdc`

```
---
description: Infrastructure rules for agents and tools
globs: ["app/domains/*/agents/*.py", "app/domains/*/tools/*.py", "app/orchestrator/*.py"]
---
# Infrastructure Rules (I1-I11)
- Tools: always use @tool_handler(domain, require_company=True) (I2)
- Agents: extend LangGraphReActBase + EnhancedAgentMixin (I1)
- LLM: only instantiate via llm_provider.get_llm() factory (I4)
- DB: repositories only (never SQLAlchemy in controllers) (I9)
- API: every endpoint must declare response_model (I6)
Reference: themes/infrastructure/
```

### `.cursor/rules/operational.mdc`

```
---
description: Operational rules for config, testing, and integrations
globs: ["*config*.py", "tests/**/*.py", "scripts/check_*.py", "*channel*.py"]
---
# Operational Rules (O1-O3)
- Config: from lia_config.config import settings (never instantiate Settings()) (O2)
- Feature flags: await feature_flag_service.is_enabled(db, key, company_id) (O2)
- Rails Client: rails_get/patch/post (always fail-safe, never direct HTTP) (O3)
- Email: AI_GENERATED_FOOTER mandatory + _is_opted_out() check (O3)
- Tests: thresholds ONLY in tests/eval/config.yaml (O1)
- Bias threshold: max_score_delta=0.05 — legal threshold, do not change (O1)
Reference: themes/operational/
```

---

## Instruções de navegação para o dev v5

### Para implementar uma feature nova

1. Identificar qual(is) tema(s) cobrem a feature (usar mapa acima)
2. Ler os docs de Compliance relevantes primeiro (C1-C8 se envolver decisão de IA)
3. Ler o doc de Infrastructure do componente (I1-I11)
4. Seguir a seção "Instruções para Claude Code / Cursor" do doc
5. Usar o checklist P0/P1/P2 do doc antes de abrir PR

### Para debugar um comportamento inesperado

1. Identificar o tema do comportamento
2. Ler a seção "Lógica IN → OUT" do doc
3. Verificar seção "Gotchas e erros comuns"
4. Consultar "Testes obrigatórios" para casos de teste existentes

### Para entender uma integração externa

1. Ler O3 (External Integrations) para visão geral
2. Para sourcing: `docs/integrations/apis/sourcing/sourcing_apis_catalog.yaml`
3. Para circuit breakers das APIs: R1 (Circuit Breakers)

---

## Cobertura dos 33 docs

| Dimensão | Quantidade | Cobertura | Nota |
|----------|:----------:|:---------:|------|
| YAMLs documentados | 55 de 85 total | ~65% documentados | 30 extras = capabilities.yaml por domain + experiments |
| Módulos em `app/shared/` | 52 entradas (top-level) | 100% | Gap analysis SSH: 52, não "~40" |
| Domains em `app/domains/` | 57 funcionais | ~85% | Gaps: voice, job_creation, digital_twin, interview_intelligence |
| Pacotes em `libs/` | 7 | 100% | — |
| Models SQLAlchemy | 120 | 100% (em I9) | Verificado SSH |
| Alembic migrations | 95 (96 total c/ `__init__.py`) | 100% (em I9) | Gaps de número: 036, 038, 039 |
| Lint scripts | 13 | 100% (em C7 + O1) | Verificado SSH |
| Middleware | 5 | 100% (em I10) | — |
| YAMLs de intent | 17 capabilities | 100% (em I7) | Verificado SSH |

---

*Gerado em 2026-04-23 | Fonte: código canônico Replit via SSH | Zero invenção*
