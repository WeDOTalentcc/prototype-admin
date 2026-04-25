# Execution Plan — 31 Thematic Operational Docs

> **Progressive disclosure:** cada doc tem sua própria seção auto-contida abaixo.
> Ao executar um doc, leia APENAS sua seção + os arquivos listados em "Pre-write audit".
> Não precisa carregar o plano master (`esse-front-end-rustling-lollipop.md`).

---

## Status global

- **Passo 0 (pré-req):** ✅ Bundles expandidos 55/55 YAMLs (LIA 32 + Compliance 2 + Infrastructure 21)
- **Fase 1 Compliance:** 0/8 — PENDING
- **Fase 2 Infrastructure:** 0/11 — PENDING
- **Fase 3 Persona:** 0/4 — PENDING
- **Fase 4 Resilience:** 0/4 — PENDING
- **Fase 5 Agent Studio:** 0/1 — PENDING
- **Fase 6 Operational:** 0/3 — PENDING
- **Finalização:** README master + atualização CANONICAL + 5 handoffs — PENDING

**Total: 0/31 docs entregues**

---

## Workflow por doc (6 passos — não pular)

```
1. LER seção do doc abaixo no execution plan (2-5 KB)
2. PRE-WRITE AUDIT: ler TODOS os arquivos listados (via SSH se Replit, Read se local)
3. WRITE: preencher template com apenas conteúdo verificado (zero invenção)
4. SCP para Replit
5. GATE: 4 verificações (paths existem, MD5 sync, cross-refs válidos, grep-check)
6. Atualizar status no execution plan + avançar para próximo
```

---

## Template comum (todos os 31 docs seguem)

```markdown
# Theme: <Nome> — <Layer>

## O que é este tema
[1-2 parágrafos — definição + escopo + boundary com temas irmãos]

## Arquivos conectados (N total)
### Camada Persona (LLM vê — X arquivos)
### Camada Config (Python lê — Y arquivos)
### Camada Código (Z arquivos Python)
### Integration points

## Lógica IN → OUT
### Input
### Processing
### Output
### Escalation / HITL

## Instruções para Claude Code / Cursor
### "Implementa <tema> no v5"
### "Adiciona <tema> a uma feature nova"
### Setup em CLAUDE.md (snippet pronto)
### Setup em Cursor rules (snippet pronto)

## Adaptação à estrutura diferente do v5
### Pode adaptar sem quebrar
### NÃO pode adaptar (base legal ou arquitetural)

## Checklist de completude (com P0/P1/P2)

## Gotchas e erros comuns

## Testes obrigatórios

## Referências
```

Tamanho esperado: 10-18K por doc.

---

## Regras absolutas — ZERO INVENÇÃO

1. Toda afirmação precisa de fonte verificada (código Python / YAML / guide / URL regulatória)
2. Proibido: "provavelmente funciona assim" sem leitura; citar função inexistente; inventar parâmetros
3. CLAUDE.md: multi-tenancy JWT, LGPD atributos, fairness antes de LLM, sem hardcode, P0/P1/P2
4. Harness: classificar regras em guide/sensor + computacional/inferencial
5. 3-source para temas sensíveis (C1-C8): YAML + Python + teste → código é verdade se divergir
6. Zero git push; commits locais no Replit; Paulo push manual via replit-sync

---

## Gate de verificação por doc

```bash
# 1. Paths Python existem
for path in <python_paths>; do
  ssh replit-wedo "test -f /home/runner/workspace/lia-agent-system/$path" || echo "MISSING: $path"
done

# 2. YAMLs presentes nos bundles
for yaml in <yaml_names>; do
  grep -l "$yaml" /Users/paulomoraes/Documents/Python/LIA_YAMLS_*.md \
    /Users/paulomoraes/Documents/Python/COMPLIANCE_YAMLS_*.md \
    /Users/paulomoraes/Documents/Python/INFRASTRUCTURE_YAMLS_*.md \
    || echo "MISSING YAML: $yaml"
done

# 3. Cross-references apontam para seções reais
# 4. MD5 Mac ↔ Replit idêntico
```

---

# FASE 1 — COMPLIANCE (8 docs)

## C1 — Fairness & Anti-Discrimination

**Status:** PENDING
**Output Mac:** `/Users/paulomoraes/Documents/Python/themes/compliance/C1_FAIRNESS_AND_ANTI_DISCRIMINATION.md`
**Output Replit:** `/home/runner/workspace/docs/reconstruction-guides/themes/compliance/C1_FAIRNESS_AND_ANTI_DISCRIMINATION.md`

**Pre-write audit (ler antes de escrever):**

YAMLs (local em `/tmp/wedo-prompts/`):
- `technical_config/protected_attributes.yaml`
- `technical_config/fairness_post_check.yaml`
- `shared/compliance_block.yaml` (seções decision.fairness + decision.bias)
- `domains/cv_screening.yaml`, `pipeline_transition.yaml`, `hiring_policy.yaml`, `autonomous.yaml`, `culture_analysis.yaml`, `wsi_evaluation.yaml`

Python canônico (SSH Replit):
- `app/shared/compliance/fairness_guard.py`
- `app/shared/compliance/fairness_guard_middleware.py`
- `app/shared/compliance/bias_audit_service.py`
- `app/shared/compliance/protected_attributes.py`
- `app/shared/compliance/scoring_safeguards.py`
- `app/shared/compliance/domain_validators.py`
- `app/domains/compliance_base.py`

Guides/handoffs (locais):
- COMPLIANCE_RECONSTRUCTION_GUIDE.md §10.2, §10.3
- FAIRNESS_LAYER3_RUNBOOK.md
- `responsible-ai/eu-ai-act-technical-documentation-pt.md` §6

**Seções obrigatórias no doc:**
- L1/L2/L3 FairnessGuard
- 14 atributos protegidos (SSoT `protected_attributes.yaml`)
- 4/5 rule / Disparate Impact Ratio (NYC LL144)
- Ação afirmativa (Lei 8.213/91 PCD + Lei 12.990/2014 pretos/pardos + mulheres STEM)
- Cultural fit como proxy de viés
- Bias audit pre-deploy vs post-deploy (fluxos separados)
- `fairness_rules` em domain YAMLs (quando obrigatório)

**Output gate:**
- [ ] Template 10 seções completas
- [ ] 7 paths Python verificados
- [ ] 9 YAMLs referenciados presentes em bundles
- [ ] Cross-refs para COMPLIANCE §10 válidos
- [ ] MD5 Mac↔Replit

---

## C2 — LGPD PII & Data Minimization

**Status:** PENDING
**Output:** `themes/compliance/C2_LGPD_PII_AND_DATA_MINIMIZATION.md`

**Pre-write audit:**

YAMLs:
- `shared/compliance_block.yaml` (seções decision.lgpd, communication.lgpd, operational.lgpd)
- `shared/guardrails_block.yaml` (seção data_safety)

Python (SSH):
- `app/shared/pii_masking.py`
- `app/shared/compliance/fairness_guard.py` (função `_strip_pii` antes de L3)

Guides:
- COMPLIANCE_RECONSTRUCTION_GUIDE.md BLOCO E (pii_masking verbatim)

**Seções obrigatórias:**
- LGPD Art. 6 (minimização)
- LGPD Art. 11 (dados sensíveis — lista fechada)
- PII masking layers (presidio + regex fallback)
- Data safety em `guardrails_block.yaml`
- PII strip antes de L3 do FairnessGuard

**Output gate:** padrão (4 checks)

---

## C3 — LGPD Consent & Data Subject Rights

**Status:** PENDING
**Output:** `themes/compliance/C3_LGPD_CONSENT_AND_DATA_SUBJECT.md`

**Pre-write audit:**

YAMLs: nenhum (100% código).

Python (SSH):
- `app/domains/consent/dependencies.py`
- `app/domains/consent/repositories/` (todos os arquivos)
- `app/domains/data_subject/dependencies.py`
- `app/domains/data_subject/repositories/` (todos)
- `app/domains/lgpd/dependencies.py`
- `app/domains/lgpd/repositories/` (todos)
- `app/domains/lgpd/services/` (todos)

Guides:
- COMPLIANCE_RECONSTRUCTION_GUIDE.md §10.5 (LGPD requirements)

**Seções obrigatórias:**
- LGPD Arts. 7-9 (consentimento)
- LGPD Art. 15 (acesso)
- LGPD Art. 17 (exclusão / direito ao esquecimento)
- LGPD Art. 18 (portabilidade)
- Fluxo `data_subject_request` (handler + repository)
- Consent granular vs global
- Retenção / tombstoning

**Output gate:** padrão

---

## C4 — LGPD Art. 20 Right to Contest + Candidate Portal

**Status:** PENDING
**Output:** `themes/compliance/C4_LGPD_ART20_RIGHT_TO_CONTEST.md`

**Pre-write audit:**

YAMLs:
- `domains/candidate_self_service.yaml`
- `shared/compliance_block.yaml` (seção right_to_contest em decision + communication)

Python (SSH):
- `app/api/v1/candidate_portal.py`
- `app/api/v1/candidate_portal_explanation.py`
- `app/api/v1/decision_explanation.py`
- `app/domains/candidate_self_service/agents/candidate_react_agent.py`
- `app/domains/candidate_self_service/agents/candidate_tool_registry.py`
- `app/domains/candidate_self_service/agents/candidate_system_prompt.py`
- `app/domains/candidate_self_service/tools/explain_candidate_decision.py`
- `app/domains/candidate_self_service/tools/get_application_status.py`
- `app/domains/candidate_self_service/tools/get_interview_info.py`
- `app/domains/candidate_self_service/tools/get_wsi_feedback.py`
- `app/domains/candidate_self_service/services/candidate_status_service.py`
- `app/domains/candidate_self_service/repositories/candidate_status_repository.py`

Guides:
- LIA_PERSONA_RECONSTRUCTION_GUIDE.md §9.8 (candidate portal architecture)
- COMPLIANCE_RECONSTRUCTION_GUIDE.md §11.1 (endpoint ponte)
- `responsible-ai/eu-ai-act-technical-documentation-pt.md` §9

**Seções obrigatórias:**
- LGPD Art. 20 (revisão + explicação de critérios)
- EU AI Act Art. 86 (right to explanation)
- Fluxo candidate-facing (JWT token + rate limit + anti-IDOR)
- `_sanitize_decision()` — `_FORBIDDEN_FIELDS` SSoT
- `_ART_86_NOTICE` template
- Tool registry whitelist (4 tools)
- Audit log via `log_portal_access`

**Output gate:** padrão

---

## C5 — Multi-tenancy & Isolation

**Status:** PENDING
**Output:** `themes/compliance/C5_MULTI_TENANCY_AND_ISOLATION.md`

**Pre-write audit:**

YAMLs:
- `shared/guardrails_block.yaml` (seção multi_tenancy)

Python (SSH):
- `app/shared/tenant_guard.py`
- `app/shared/tenant_session.py`
- `app/shared/tenant_llm_context.py`
- `app/shared/session_bridge.py`
- `app/middleware/auth_enforcement.py`
- `app/auth/dependencies.py` (para `get_verified_company_id`)

Guides:
- COMPLIANCE_RECONSTRUCTION_GUIDE.md BLOCO G (tenant_guard verbatim)

**Seções obrigatórias:**
- Regra: `company_id` sempre do JWT, nunca do payload
- `TenantGuard.get_verified_company_id()` como dependency
- Anti-IDOR pattern
- Session lifecycle + `tenant_session`
- LLM context isolado por tenant (`tenant_llm_context`)
- Fallback/erro quando JWT ausente

**Output gate:** padrão

---

## C6 — Prompt Injection Defense + Encryption

**Status:** PENDING
**Output:** `themes/compliance/C6_PROMPT_INJECTION_AND_ENCRYPTION.md`

**Pre-write audit:**

YAMLs:
- `shared/guardrails_block.yaml` (seção prompt_security)
- `shared/defensive.yaml`

Python (SSH):
- `app/shared/compliance/prompt_injection_guard.py`
- `app/shared/compliance/c3b_layer.py`
- `app/shared/prompts/interaction_patterns.py` (PROMPT_INJECTION_PATTERNS + DEFENSIVE_BLOCK)
- `app/shared/compliance/guardrail_repository.py`
- `app/shared/prompt_injection.py`
- `app/shared/security/redis_crypto.py`
- `app/shared/security/wsi_hashing.py`
- `app/core/secrets_provider.py`

Guides:
- LIA_PERSONA_RECONSTRUCTION_GUIDE.md §9.5 (interaction_patterns verbatim)

**Seções obrigatórias:**
- 12 regex patterns de prompt injection
- DEFENSIVE_BLOCK (quando injetar)
- C3B Layer (Compliance Control Block — gate antes de LLM)
- Encryption: redis_crypto (dados em cache) + wsi_hashing (one-way)
- Secrets provider (env + rotação)
- Jailbreak detection + escalação

**Output gate:** padrão

---

## C7 — Audit Trail & Compliance Lint

**Status:** PENDING
**Output:** `themes/compliance/C7_AUDIT_TRAIL_AND_COMPLIANCE_LINT.md`

**Pre-write audit:**

YAMLs:
- `shared/compliance_block.yaml` (seção decision.audit)

Python (SSH):
- `app/shared/compliance/audit_service.py`
- `app/shared/compliance/audit_storage.py`
- `app/shared/compliance/audit_writer.py`
- `app/shared/compliance/audit_callback.py`
- `app/shared/compliance/audit_models.py`
- `app/shared/compliance/scoring_safeguards.py`
- `libs/audit/lia_audit/audit_callback.py`
- `libs/audit/lia_audit/audit_models.py`
- `libs/audit/lia_audit/audit_storage.py`
- `libs/audit/lia_audit/audit_writer.py`
- `alembic/versions/015_add_fairness_audit_log.py`
- `libs/models/lia_models/audit_log.py`
- 19 scripts em `scripts/check_*.py`

Guides:
- COMPLIANCE_RECONSTRUCTION_GUIDE.md §10.2 C8
- `responsible-ai/eu-ai-act-technical-documentation-pt.md` §5.3

**Seções obrigatórias:**
- Audit service + storage + writer (pipeline)
- Callback handlers
- Scoring safeguards (log de cada scoring)
- Tabela `fairness_audit_log` (Alembic 015)
- 19 lint scripts (o que cada um verifica)
- Retention + querying patterns

**Output gate:** padrão

---

## C8 — Policy Engine & Governance

**Status:** PENDING
**Output:** `themes/compliance/C8_POLICY_ENGINE_AND_GOVERNANCE.md`

**Pre-write audit:**

YAMLs: nenhum.

Python (SSH):
- `app/orchestrator/policy_engine.py`
- `app/shared/services/policy_engine_service.py`
- `app/shared/policy_middleware.py`
- `app/shared/policy_helper.py`
- `app/shared/policy_sync_service.py`
- `app/orchestrator/precondition_checker.py`
- `app/shared/governance/feature_flag_service.py`
- `app/shared/module_gating.py`

Guides: nenhum específico (tema relativamente novo na doc).

**Seções obrigatórias:**
- Distinção: PolicyEngine (runtime) vs HiringPolicyAgent (LLM)
- Fluxo de sincronização de políticas Rails → LIA
- Middleware de policy (avaliação por request)
- Feature flags (kill switches)
- Module gating (libera/bloqueia features por tenant)
- Precondition checker (o que roda antes de ações)

**Output gate:** padrão

---

# FASE 2 — INFRASTRUCTURE (11 docs)

## I1 — Agent Architecture

**Status:** PENDING
**Output:** `themes/infrastructure/I1_AGENT_ARCHITECTURE.md`

**Pre-write audit:**

YAMLs:
- `technical_config/agents_registry.yaml` (via bundle Infrastructure)

Python (SSH):
- `libs/agents-core/lia_agents_core/langgraph_react_base.py`
- `langgraph_base.py`, `agent_interface.py`, `agent_bus.py`
- `react_agent_registry.py`, `base_state_machine.py`, `state_machine.py`
- `react_loop.py`, `agent_scaffold.py`, `autonomy_engine.py`
- `confidence.py`, `contracts.py`, `enhanced_agent_mixin.py`
- `nodes.py`, `proactive_worker.py`, `tool_adapter.py`, `timed_tool_node.py`
- `app/core/agent_registry_watcher.py`
- 2-3 samples de `app/domains/<X>/agents/*_react_agent.py`

Guides:
- INFRASTRUCTURE_RECONSTRUCTION_GUIDE.md §B, §C

**Seções obrigatórias:**
- AgentType enum + contrato `AgentInput/AgentOutput`
- `LangGraphReActBase` (classe base)
- ReAct loop (Reason-Act-Observe)
- `agents_registry.yaml` + hot-reload via watcher
- Como criar novo agente (passo-a-passo)
- State machine + checkpointer
- Tool adapter + timed_tool_node

**Output gate:** padrão

---

## I2 — Tool Architecture

**Status:** PENDING
**Output:** `themes/infrastructure/I2_TOOL_ARCHITECTURE.md`

**Pre-write audit:**

YAMLs:
- `technical_config/tool_permissions.yaml`
- `technical_config/tool_registry_metadata.yaml`

Python (SSH):
- `app/shared/tool_handler.py`
- `app/tools/tool_registry_loader.py`
- 3-5 samples de tools em `app/domains/<X>/tools/*.py`
- `libs/agents-core/lia_agents_core/tool_adapter.py`
- `libs/agents-core/lia_agents_core/timed_tool_node.py`

Guides:
- INFRASTRUCTURE_RECONSTRUCTION_GUIDE.md BLOCO D

**Seções obrigatórias:**
- Decorator `@tool_handler("<domain>", require_company=True)`
- ToolRegistry + validação startup via `validate_yaml()`
- `tool_permissions.yaml` (mapa tool → allowed_agents + scope)
- `tool_registry_metadata.yaml` (SSoT descrições + params JSONSchema)
- Padrão ToolDefinition
- Scopes: TALENT_FUNNEL / JOB_TABLE / IN_JOB / GLOBAL

**Output gate:** padrão

---

## I3 — Orchestration (4 phases + Cascade 8 tiers)

**Status:** PENDING
**Output:** `themes/infrastructure/I3_ORCHESTRATION.md`

**Pre-write audit:**

YAMLs:
- `technical_config/domain_routing.yaml`

Python (SSH):
- `app/orchestrator/main_orchestrator.py`
- `cascaded_router.py`, `fast_router.py`, `agentic_loop.py`
- `chat_adapter.py`, `context_adapter.py`, `domain_mappings.py`
- `orchestrator.py`, `llm_cascade.py`, `pending_action.py`
- `registry.py`, `state_manager.py`, `task_planner.py`
- `tasting_engine.py`, `temporal_resolver.py`, `tenant_budget.py`
- `wizard_state.py`, `action_executor/` (listar arquivos), `action_handlers/`

Guides:
- INFRASTRUCTURE_RECONSTRUCTION_GUIDE.md §E

**Seções obrigatórias:**
- 4 fases do MainOrchestrator
- CascadedRouter 8 tiers (regex → embeddings → LLM)
- Domain routing YAML
- Action executor vs action handlers
- State management + wizard state
- Tenant budget (controle de custo LLM)

**Output gate:** padrão

---

## I4 — LLM Providers (BYOK)

**Status:** PENDING
**Output:** `themes/infrastructure/I4_LLM_PROVIDERS.md`

**Pre-write audit:**

YAMLs: nenhum.

Python (SSH):
- `app/shared/providers/llm_provider.py`
- `app/shared/providers/llm_factory.py`
- `app/shared/llm_bootstrap.py`
- `scripts/check_llm_factory_enforcement.py`
- `scripts/check_llm_imports.py`

Guides:
- INFRASTRUCTURE_RECONSTRUCTION_GUIDE.md §F
- LLM_FACTORY_HANDOFF_v2.md

**Seções obrigatórias:**
- BYOK (Bring Your Own Key) por `company_id`
- `LLMProviderFactory.get(company_id)`
- Provedores suportados (Anthropic, OpenAI, Azure)
- Model anchoring (versões pinned)
- Enforcement: `check_llm_factory_enforcement.py` proíbe import direto

**Output gate:** padrão

---

## I5 — Observability & Agent Quality

**Status:** PENDING
**Output:** `themes/infrastructure/I5_OBSERVABILITY.md`

**Pre-write audit:**

Python (SSH):
- `app/core/observability.py`
- `app/schemas/observability.py`
- `app/api/v1/observability.py`
- `app/domains/observability/repositories/observability_repository.py`
- `app/api/v1/agent_quality_dashboard.py`
- `app/api/v1/fairness_reports.py`
- `libs/agents-core/lia_agents_core/observability.py`
- `libs/agents-core/lia_agents_core/execution_log_store.py`
- `app/core/sentry.py`
- `app/shared/quality/` (listar)
- `app/jobs/drift_job.py`

Guides:
- INFRASTRUCTURE_RECONSTRUCTION_GUIDE.md §G

**Seções obrigatórias:**
- Tracing (spans por agente + tool)
- Métricas (latência, custo, tokens)
- Agent Quality Dashboard
- Fairness Reports
- Execution log store
- Drift job (detecção de divergência)
- Integração Sentry

**Output gate:** padrão

---

## I6 — API Layer / Routes / ChatResponse (inclui WebSocket)

**Status:** PENDING
**Output:** `themes/infrastructure/I6_API_LAYER_AND_WEBSOCKET.md`

**Pre-write audit:**

Python (SSH):
- `app/schemas/api_envelope.py`
- `app/schemas/chat_response.py`
- `app/api/routes.py`
- `app/api/v1/_path_patterns.py`
- 3-5 samples de endpoints em `app/api/v1/`
- `app/shared/websocket/ws_manager.py`
- `app/shared/websocket/ws_message_schemas.py`
- `app/shared/chat_event_serializer.py`
- `libs/agents-core/lia_agents_core/streaming_callback.py`
- `app/shared/errors.py`

Guides:
- INFRASTRUCTURE_RECONSTRUCTION_GUIDE.md BLOCO H (ChatResponse 20 campos)

**Seções obrigatórias:**
- ADR-005 (response_model obrigatório)
- ADR-006 (no PII in logs)
- ADR-008 (APIResponse envelope)
- ADR-014 (all routes /api/v1)
- ChatResponse 20 campos
- WebSocket manager + streaming
- Error handling patterns
- Path patterns (anti-IDOR + routing shadowing)

**Output gate:** padrão

---

## I7 — Intent Classification & Routing

**Status:** PENDING
**Output:** `themes/infrastructure/I7_INTENT_ROUTING.md`

**Pre-write audit:**

YAMLs:
- `domains/intent_classification.yaml`
- `technical_config/domain_routing.yaml`
- 17 × `capabilities.yaml` (via bundle Infrastructure)

Python (SSH):
- `app/shared/services/keyword_intent_matcher.py`
- `app/shared/services/intent_classifier.py`
- `app/shared/services/enhanced_intent_classifier.py`
- `app/orchestrator/navigation_intent.py`
- 2-3 samples de `app/domains/<X>/domain.py` (que consomem capabilities.yaml)

Guides:
- INFRASTRUCTURE_RECONSTRUCTION_GUIDE.md §E cascade tier 1-3

**Seções obrigatórias:**
- KeywordIntentMatcher (tier 1 — regex fast path)
- Intent classifier (tier 2 — embeddings)
- Enhanced classifier (tier 3 — LLM fallback)
- NavigationIntentDetector
- `capabilities.yaml` loader pattern (em cada domain.py)
- Domain routing final

**Output gate:** padrão

---

## I8 — Authentication & Authorization

**Status:** PENDING
**Output:** `themes/infrastructure/I8_AUTH_AND_AUTHORIZATION.md`

**Pre-write audit:**

Python (SSH):
- `app/auth/dependencies.py`
- `app/auth/rails_jwt.py`
- `app/auth/security.py`
- `app/auth/models.py`, `schemas.py`
- `app/auth/workos_models.py`, `workos_schemas.py`
- `app/core/auth.py`
- `app/middleware/auth_enforcement.py`

**Seções obrigatórias:**
- JWT Rails (shared secret pattern)
- WorkOS integration (SSO)
- `get_current_user` dependency
- `get_verified_company_id` dependency
- Auth enforcement middleware
- Candidate portal JWT (separado do recruiter JWT)

**Output gate:** padrão

---

## I9 — Data Layer / Database / Migrations

**Status:** PENDING
**Output:** `themes/infrastructure/I9_DATA_LAYER_AND_MIGRATIONS.md`

**Pre-write audit:**

Python (SSH):
- `app/core/database.py`
- `app/core/redis_client.py`
- `alembic.ini`
- 3-5 migrations samples de `alembic/versions/`
- 5-10 models samples de `libs/models/lia_models/`
- 2-3 repositories samples de `app/shared/repositories/` + `app/domains/<X>/repositories/`

**Seções obrigatórias:**
- SQLAlchemy async patterns
- 95 migrations organizadas por tema
- 120 models (grupo por feature)
- Repository pattern
- Redis client (cache + queues)
- Migration naming convention

**Output gate:** padrão

---

## I10 — Middleware & Request Lifecycle

**Status:** PENDING
**Output:** `themes/infrastructure/I10_MIDDLEWARE_AND_REQUEST_LIFECYCLE.md`

**Pre-write audit:**

Python (SSH):
- `app/middleware/auth_enforcement.py`
- `app/middleware/rate_limiter.py`
- `app/middleware/request_id.py`
- `app/middleware/response_envelope.py`
- `app/middleware/trial_enforcement.py`
- `app/core/logging_middleware.py`
- `app/core/logging_config.py`
- `app/api/routes.py` (registro)

**Seções obrigatórias:**
- Ordem de middleware (importante)
- Rate limiter (por tenant + candidate token)
- Request ID tracing
- Response envelope consistency
- Trial enforcement (SaaS billing)
- Logging middleware (structured)

**Output gate:** padrão

---

## I11 — RAG / Semantic Search / Embeddings

**Status:** PENDING
**Output:** `themes/infrastructure/I11_RAG_SEMANTIC_SEARCH.md`

**Pre-write audit:**

Python (SSH):
- `app/domains/ai/services/rag_service.py`
- `app/domains/ai/services/rag_pipeline_service.py`
- `app/domains/ai/services/ragas_evaluation_service.py`
- `app/shared/intelligence/embedding_service.py`
- `app/shared/intelligence/semantic_search_service.py`
- `app/shared/intelligence/smart_extractor.py`
- `app/shared/intelligence/chunking/` (listar)
- `app/orchestrator/vector_semantic_cache.py`
- `app/orchestrator/semantic_cache.py`
- `app/api/v1/rag_search.py`
- `app/shared/cache_strategy.py`

**Seções obrigatórias:**
- Pipeline RAG (chunk → embed → retrieve → rerank)
- Embedding service (modelo + provider)
- Vector semantic cache
- Chunking strategies
- RAGAS evaluation (quality metrics)
- Cache strategy (L1/L2/L3 caches)

**Output gate:** padrão

---

# FASE 3 — PERSONA (4 docs)

## P1 — System Prompt Composition (9 steps)

**Status:** PENDING
**Output:** `themes/persona/P1_SYSTEM_PROMPT_COMPOSITION.md`

**Pre-write audit:**

YAMLs:
- `shared/lia_persona.yaml`, `agent_prompts.yaml`, `compliance_block.yaml`, `guardrails_block.yaml`
- `platform/platform_manifest.yaml`

Python (SSH):
- `app/shared/prompts/system_prompt_builder.py`
- `app/shared/platform_manifest.py`
- `app/shared/prompts/loader.py`
- `app/domains/compliance_base.py`
- `app/core/prompt_version_loader.py`

Guides:
- LIA_PERSONA_RECONSTRUCTION_GUIDE.md §9.4 (9 passos)
- BLOCO B/C/F (verbatim)

**Seções obrigatórias:**
- 9 passos exatos do `SystemPromptBuilder.build()`
- `_IDENTITY_OVERRIDE` (hardcoded)
- `_PLATFORM_KNOWLEDGE` via `render_platform_knowledge_snippet()`
- `ComplianceDomainPrompt` + `GuardrailsDomainPrompt`
- `@lru_cache` patterns
- Prompt version loader

**Output gate:** padrão

---

## P2 — Specialization per Agent

**Status:** PENDING
**Output:** `themes/persona/P2_AGENT_SPECIALIZATION.md`

**Pre-write audit:**

YAMLs:
- `shared/agent_prompts.yaml` (11 agent_types)
- 24 × `domains/*.yaml`

Python (SSH):
- `app/shared/prompts/agent_prompts.py`
- 3-5 samples de `app/domains/<X>/agents/*_system_prompt.py`
- `app/domains/compliance_base.py`

Guides:
- LIA_PERSONA_RECONSTRUCTION_GUIDE.md §9.2, §9.6, §9.11

**Seções obrigatórias:**
- 11 agent_types em `agent_prompts.yaml`
- 5 formatos estruturais (A/B/C/D/E) dos 24 domain YAMLs
- Como criar novo agent_type
- Como criar novo domain YAML (formato A preferido)
- `ComplianceDomainPrompt` variant selection (decision/communication/operational)

**Output gate:** padrão

---

## P3 — Conversation Memory / Context State

**Status:** PENDING
**Output:** `themes/persona/P3_CONVERSATION_MEMORY.md`

**Pre-write audit:**

Python (SSH):
- `app/shared/memory/conversation_state.py`
- `app/shared/memory_resolver.py`
- `libs/agents-core/lia_agents_core/working_memory.py`
- `libs/agents-core/lia_agents_core/long_term_memory.py`
- `libs/agents-core/lia_agents_core/memory_integration.py`
- `libs/agents-core/lia_agents_core/checkpointer.py`
- `app/shared/prompts/system_prompt_builder.py` (função `_detect_ongoing_conversation`)

Guides:
- LIA_PERSONA_RECONSTRUCTION_GUIDE.md §9.4 passo 5

**Seções obrigatórias:**
- `ConversationState` (last_entity, mentioned_candidates, last_job_id)
- Working memory vs long_term memory
- Memory integration layer
- Checkpointer (LangGraph)
- Detecção de conversa em andamento
- Anti-re-apresentação pattern

**Output gate:** padrão

---

## P4 — Interaction Patterns

**Status:** PENDING
**Output:** `themes/persona/P4_INTERACTION_PATTERNS.md`

**Pre-write audit:**

YAMLs:
- `shared/defensive.yaml`

Python (SSH):
- `app/shared/prompts/anti_sycophancy_block.py`
- `app/shared/prompts/interaction_patterns.py`
- `app/shared/prompts/cot.py`
- `app/shared/prompts/few_shot_examples.py`
- `app/shared/prompts/intent_few_shot_examples.py`
- `app/shared/prompts/training_persona.py`

Guides:
- LIA_PERSONA_RECONSTRUCTION_GUIDE.md §9.3, §9.5

**Seções obrigatórias:**
- 3 variantes anti-sycophancy (OPERATIONAL/FULL/ORCHESTRATOR)
- NEGATION_WORDS + CONFIRMATION_WORDS
- CHAIN_OF_THOUGHT_BLOCK
- NEGATION_DETECTION_BLOCK
- DEFENSIVE_BLOCK + PROMPT_INJECTION_PATTERNS
- Few-shot examples patterns
- Crença #11 Manifesto (anti-sycophancy em 100%)

**Output gate:** padrão

---

# FASE 4 — RESILIENCE (4 docs)

## R1 — Circuit Breakers

**Status:** PENDING
**Output:** `themes/resilience/R1_CIRCUIT_BREAKERS.md`

**Pre-write audit:**

Python (SSH):
- `app/shared/resilience/circuit_breaker.py`
- `app/shared/services/circuit_breaker.py`
- `app/api/v1/admin_circuit_breakers.py`

Guides:
- RESILIENCE_LEARNING_RECONSTRUCTION_GUIDE.md Parte A
- RESILIENCE_LEARNING_RECONSTRUCTION_GUIDE.md Adendo B (fallback FairnessGuard L3)

**Seções obrigatórias:**
- 3 estados: Closed / Open / Half-Open
- `@anthropic_circuit`, `@openai_circuit`, etc. decorators
- 20 circuitos ativos (listar)
- Fallback lenient pattern (ex: FairnessGuard L3)
- Admin panel para monitorar

**Output gate:** padrão

---

## R2 — Learning Loop + A/B Testing + Calibration

**Status:** PENDING
**Output:** `themes/resilience/R2_LEARNING_LOOP_AND_AB_TESTING.md`

**Pre-write audit:**

Python (SSH):
- `app/shared/learning/learning_loop_service.py`
- `app/shared/learning/ab_testing_service.py`
- `app/shared/learning/learning_snapshot_service.py`
- `app/shared/learning/template_learning_service.py`
- `app/shared/learning/finetuning_export.py`
- `libs/agents-core/lia_agents_core/learning_extractor.py`
- `app/shared/ml/ttf_predictor.py`
- `app/shared/ab_testing.py`
- `libs/models/lia_models/calibration.py` (se existir)

Guides:
- RESILIENCE_LEARNING_RECONSTRUCTION_GUIDE.md Parte B

**Seções obrigatórias:**
- Learning loop (feedback → weights)
- A/B testing framework
- Learning snapshots
- Template learning
- Fine-tuning export (data preparation)
- TTF (Time-to-Fill) predictor
- CalibrationWeight model

**Output gate:** padrão

---

## R3 — Messaging & Events

**Status:** PENDING
**Output:** `themes/resilience/R3_MESSAGING_AND_EVENTS.md`

**Pre-write audit:**

Python (SSH):
- `app/shared/messaging/broker_interface.py`
- `app/shared/messaging/unified_event_publisher.py`
- `app/shared/messaging/rails_event_publisher.py`
- `app/shared/messaging/platform_events.py`
- `app/shared/messaging/message_schemas.py`
- `app/shared/messaging/dispatchers.py`
- `app/shared/messaging/rabbitmq_producer.py`
- `app/shared/messaging/rabbitmq_consumer.py`
- `app/shared/messaging/celery_config.py`
- `libs/messaging/lia_messaging/email.py`, `teams.py`, `whatsapp.py`, `notification_service.py`
- `app/api/v1/platform_event_handlers.py`

Guides:
- RESILIENCE_LEARNING_RECONSTRUCTION_GUIDE.md Parte C (BrokerInterface)

**Seções obrigatórias:**
- BrokerInterface abstrato
- 3 providers (Redis, RabbitMQ, PubSub) — troca via env
- UnifiedEventPublisher
- PlatformEvent schema
- Rails event publisher (envia para Rails)
- Notification channels (email, teams, whatsapp)
- Event handlers patterns

**Output gate:** padrão

---

## R4 — Background Jobs / Async / Schedulers

**Status:** PENDING
**Output:** `themes/resilience/R4_BACKGROUND_JOBS_AND_SCHEDULERS.md`

**Pre-write audit:**

Python (SSH):
- `app/jobs/celery_tasks.py`
- `app/jobs/drift_job.py`
- `app/jobs/followup_service.py`
- `app/jobs/scheduled_reports.py`
- `app/jobs/webhook_tasks.py`
- `app/jobs/wsi_abandoned_service.py`
- `app/jobs/tasks/` (listar)
- `app/core/celery_app.py`
- `app/shared/async_processing/task_manager.py`
- `task_queue.py`, `task_scheduler.py`, `task_persistence.py`
- `enhanced_task_manager.py`, `priority_calculator.py`

**Seções obrigatórias:**
- Celery app configuration
- Task definition patterns
- Scheduler (periodic tasks)
- Task queue + priority
- Task persistence (retry + resume)
- Drift job (ML model health)
- Follow-up service (auto nudges)

**Output gate:** padrão

---

# FASE 5 — AGENT STUDIO (1 doc)

## AS1 — Agent Studio & Custom Agents

**Status:** PENDING
**Output:** `themes/agent_studio/AS1_CUSTOM_AGENTS.md`

**Pre-write audit:**

YAMLs:
- `helpers/intelligence_floor.yaml`
- `agent_templates/templates.yaml`
- `capabilities/agent_studio.capabilities.yaml`

Python (SSH):
- `app/domains/agent_studio/custom_agent_runtime.py`
- `app/domains/agent_studio/domain.py`
- `app/domains/agent_studio/actions.py`
- `app/api/v1/agent_templates.py`
- `app/api/v1/agent_studio_quality.py`
- `app/api/v1/sector_templates.py`
- `app/domains/ai/repositories/agent_template_repository.py`

Guides:
- LIA_PERSONA_RECONSTRUCTION_GUIDE.md §9.7 (intelligence_floor verbatim)

**Seções obrigatórias:**
- Custom agent runtime (recrutador cria agente próprio)
- Intelligence floor (qualidade mínima garantida)
- Templates pré-configurados (8+ templates)
- Sector-specific templates
- Quality dimensions (Agent Studio Quality)
- Fluxo: template → customização → deploy

**Output gate:** padrão

---

# FASE 6 — OPERATIONAL (3 docs)

## O1 — Testing Strategy

**Status:** PENDING
**Output:** `themes/operational/O1_TESTING_STRATEGY.md`

**Pre-write audit:**

YAMLs:
- `tests/eval/rubrics/*.yaml` (via SSH)
- `tests/eval/datasets/*.yaml`
- `eval/agentic_cases/*.yaml`
- `tests/eval/bias_probes/pairs.yaml`

Python (SSH):
- `tests/integration/test_persona_invariants.py`
- Samples de `tests/contract/`, `tests/e2e/`, `tests/unit/`, `tests/security/`
- `eval/` framework files
- 19 scripts `scripts/check_*.py`

**Seções obrigatórias:**
- Persona invariants (regression guard)
- Contract tests (API schemas)
- E2E tests (happy path)
- Security tests (red team)
- Eval framework (bias probes + scenarios)
- 19 lint scripts (cada um valida um invariant)
- Pipeline CI/CD

**Output gate:** padrão

---

## O2 — Configuration & Feature Flags

**Status:** PENDING
**Output:** `themes/operational/O2_CONFIGURATION_AND_FEATURE_FLAGS.md`

**Pre-write audit:**

Python (SSH):
- `libs/config/lia_config/config.py`
- `.env`, `.env.example`, `.env.production.example`
- `app/shared/governance/feature_flag_service.py`
- `app/core/secrets_provider.py`
- `app/core/config.py`

Guides:
- FAIRNESS_LAYER3_RUNBOOK.md (template de runbook)
- COMPLIANCE_RECONSTRUCTION_GUIDE.md §11.2

**Seções obrigatórias:**
- Settings pattern (Pydantic BaseSettings)
- .env convention (default false pra flags)
- .env.production.example como referência
- Feature flag service
- Secrets provider (rotação + vault)
- Runbook pattern (o que monitorar ao ativar flag)

**Output gate:** padrão

---

## O3 — External Integrations

**Status:** PENDING
**Output:** `themes/operational/O3_EXTERNAL_INTEGRATIONS.md`

**Pre-write audit:**

YAMLs:
- `docs/integrations/apis/sourcing/sourcing_apis_catalog.yaml`

Python (SSH):
- `app/shared/rails_client.py`
- `app/shared/rails_migration/` (listar)
- `libs/messaging/lia_messaging/whatsapp.py`, `teams.py`, `email.py`, `notification_service.py`
- Pearch AI adapter (path a descobrir)
- Microsoft Graph adapter (path a descobrir)
- HubSpot client (path a descobrir)
- `app/shared/channels/channel_router.py`
- `app/shared/channels/multi_channel_service.py`
- `app/shared/channels/adapters/`

**Seções obrigatórias:**
- Rails client (HTTP JSON para ats-api-copia)
- Rails migration helpers
- Pearch AI (190M+ perfis externos)
- Microsoft Graph (calendário)
- WhatsApp Meta Cloud API
- HubSpot CRM
- Channel router (mensagem → canal adequado)

**Output gate:** padrão

---

# FINALIZAÇÃO

## README master `themes/README.md`

**Status:** PENDING
**Output:** `themes/README.md`

Conteúdo:
- Índice 31 temas com 1 linha cada
- Mapa "recurso → tema principal + cross-cutting"
- Snippet CLAUDE.md pronto
- Snippet .cursor/rules/ pronto
- Instruções de navegação

## Atualização docs existentes

- `CANONICAL_FILES_BY_THEME.md`: adicionar seção "Thematic Operational Docs" (link para themes/)
- `LIA_DEV_HANDOFF_2026-04-23.md`: linha "Consulte themes/ para receitas"
- `COMPLIANCE_DEV_HANDOFF_2026-04-23.md`: idem
- `INFRASTRUCTURE_DEV_HANDOFF_2026-04-23.md`: idem
- `RESILIENCE_DEV_HANDOFF_2026-04-23.md`: idem
- `FRONTEND_DEV_HANDOFF_2026-04-23.md`: idem

---

## Progress tracker (atualizar após cada doc)

| Fase | Doc | Status | Timestamp |
|------|-----|--------|-----------|
| 1 | C1 Fairness | PENDING | — |
| 1 | C2 LGPD PII | PENDING | — |
| 1 | C3 LGPD Consent | PENDING | — |
| 1 | C4 LGPD Art.20 | PENDING | — |
| 1 | C5 Multi-tenancy | PENDING | — |
| 1 | C6 Prompt Injection + Encryption | PENDING | — |
| 1 | C7 Audit + Lint | PENDING | — |
| 1 | C8 Policy Engine | PENDING | — |
| 2 | I1 Agent Architecture | PENDING | — |
| 2 | I2 Tool Architecture | PENDING | — |
| 2 | I3 Orchestration | PENDING | — |
| 2 | I4 LLM Providers | PENDING | — |
| 2 | I5 Observability | PENDING | — |
| 2 | I6 API Layer + WebSocket | PENDING | — |
| 2 | I7 Intent Routing | PENDING | — |
| 2 | I8 Auth | PENDING | — |
| 2 | I9 Data Layer | PENDING | — |
| 2 | I10 Middleware | PENDING | — |
| 2 | I11 RAG / Semantic | PENDING | — |
| 3 | P1 System Prompt | PENDING | — |
| 3 | P2 Specialization | PENDING | — |
| 3 | P3 Memory / Context | PENDING | — |
| 3 | P4 Interaction Patterns | PENDING | — |
| 4 | R1 Circuit Breakers | PENDING | — |
| 4 | R2 Learning + A/B | PENDING | — |
| 4 | R3 Messaging / Events | PENDING | — |
| 4 | R4 Background Jobs | PENDING | — |
| 5 | AS1 Custom Agents | PENDING | — |
| 6 | O1 Testing | PENDING | — |
| 6 | O2 Config / Flags | PENDING | — |
| 6 | O3 Integrations | PENDING | — |
| F | README master | PENDING | — |
| F | CANONICAL update | PENDING | — |
| F | 5 handoffs update | PENDING | — |

---

*Execution plan criado em 2026-04-24. Progressive disclosure: leia apenas a seção do doc atual + atualize status após cada um.*
