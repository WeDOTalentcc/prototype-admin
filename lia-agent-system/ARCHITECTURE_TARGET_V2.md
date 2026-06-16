# LIA Agent System — Arquitetura-Alvo V2

> Documento gerado em 2026-05-23 a partir de auditoria do estado real do Replit
> (branch `feat/benefits-prv-canonical`, HEAD `3ebf53520`).
> Substitui ARCHITECTURE_TARGET.md (V1, 2026-04-12) que documentava o target
> da Wave 1 — Wave 1 foi entregue, este V2 cobre o estado real pos-Wave 2.
> Referencias canonical: ADRs 001-035 + LGPD-001/002 + AB-001 + RLHF-001 + WT-2027,
> ARCHITECTURE.md, CLAUDE.md (regras de harness e multi-tenancy).

---

## 1. Diagnostico: Estado Atual (2026-05-23)

### 1.1 Numeros do Sistema

| Metrica | V1 (12/abr) | V2 (23/mai) | Delta |
|---------|-------------|-------------|-------|
| Linhas de codigo Python (app/+libs/) | 443.086 | 588.707 | +145.621 (+33%) |
| Endpoints API (decoradores @router/@app) | 1.716 | 1.872 | +156 (+9%) |
| Dominios (subdirs app/domains/*/) | 62 | 67 | +5 |
| @register_agent (agentes registrados) | 11 | 38 | +27 (+245%) |
| Tools no ToolRegistry | Variavel | Variavel + ADR-022/024 taxonomy | — |
| Arquivos de teste (tests/**/test_*.py) | 378 | 1.025 | +647 (+171%) |
| ADRs em docs/specs/ai/ | ~11 | 30 | +19 |
| Sensores em scripts/check_*.py | ~4 mencionados | 108 | +104 |
| Commits desde 13/abr | — | 2.621 | branch feat/benefits-prv-canonical |
| Cobertura de testes | 45% (target 80%) | nao medido nesta auditoria | — |

### 1.2 O que Funciona Bem (status atualizado)

Tudo que V1 marcou como "funciona bem" continua funcionando, com extensoes:

- ComplianceDomainPrompt ABC: 100% adocao mantida + ADR-031 v3 FairnessGuard L3 default ON cross-sector
- Padrao 4-arquivos para agentes: estendido para 38 agentes (W1-001 multiplicou sourcing)
- Abstracao LLM: LLMProviderABC + ADR-WT-2027 BYOK (chaves per-tenant com track-only quando cliente paga direto)
- LGPD: DSR Art.18 + ADR-LGPD-001 (aggregates derived com gate MIN_DEPT_SAMPLES=10) + ADR-LGPD-002 (training data cross-border)
- Multi-tenancy: get_tenant_db RLS PostgreSQL + ADR-030/v2/v3 RLS defense-in-depth (HIGH-Priority Batch concluido em Sprint 1 T-02)
- Circuit breaker, rate limiting Redis: mantido
- Feature flags com rollout per-company: mantido
- Libs extraidas: 7 pacotes em libs/ + ADR-029 ToolDefinition Unification + Runtime Context Wrapper
- ARCHITECTURE.md com ADRs enforced por CI: ADR-001 (Repository Pattern) + ADR-005 (Response Models) + ADR-006 (PII in Logs) BLOCKING desde Sprint 8

### 1.3 Os Pontos de Quebra que SOBRARAM apos Wave 2

Wave 1 (Fases 1-7 de abril) resolveu os 5 pontos de quebra originais. Audit E2E 2026-05-20 sobre as 9 fases de criacao de vaga descobriu 4 NOVAS classes de falha sistemica:

| Nr | Classe | Onde | Status |
|----|--------|------|--------|
| 1 | F2.B1: 24 endpoints com `: UUID = Path(..., pattern=...)` quebrados em Pydantic 2.10 | endpoints copy-paste | RESOLVIDO via app/shared/types.py (JobIdParam, CandidateIdParam, CompanyIdParam) |
| 2 | F1.O2: POST aceita fields fantasma silenciosamente (Pydantic default extra='ignore') | request body schemas | RESOLVIDO via WeDoBaseModel canonical (extra='forbid') |
| 3 | F4.O1+F5.O1: endpoints com `company_id` no payload (viola multi-tenancy via JWT) | 139 sites pos-refinement | EM PROGRESSO: sensor R2 baseline 139 violations, fix gradual |
| 4 | F6.B3: silent fallback em path critico de IA mascarando NameError | wsi_service/question_generator.py | RESOLVIDO + sensor recomendado (check_no_silent_llm_fallback.py) |
| 5 | SMOKE-#2: 28 sites com `X-Company-ID` Header sobrescrevendo `company_id` do JWT (cross-tenant LGPD break) | 21 arquivos | EM PROGRESSO: sensor R4 baseline 29 violations, fix gradual + ADR-029-v2 oficializou banimento |

### 1.4 Pontos de Quebra Novos Descobertos no Caminho

- **i18n contract drift**: AlertPreferencesPanel shipou 280 LOC com 16 `t()` call sites e zero mudanca em messages/pt-BR.json. Resolvido via sensor `scripts/check_i18n_keys.py` (v2 scope-aware) + describe block "i18n canonical contract" nos testes.
- **ghost settings**: 34 toggles + 34 instrucoes customizadas em `CompanyCultureProfile.lia_field_toggles` sem consumer (UI iludia recrutador). Resolvido via `lia_agent_context_builder.build_company_agent_context` helper canonical.
- **manager approval ghost**: toggle `manager_approval_for_offer` visivel sem gate. Resolvido via `OfferService.check_can_send` pattern canonical para hard toggle gates.
- **Next.js App Router slug conflict**: build inteiro morria com `slug names different` em pasta filha (eligibility-question-templates/[masterId]/customize). Resolvido + sensor `find -mindepth 2 -type d -name '[*]' | sort | uniq -d`.

---

## 2. Arquitetura-Alvo V2 — Target State

```
ENTRY UNIFICADO
  HTTP POST /chat, POST /stream, WebSocket
  TODOS passam pelo mesmo pipeline (Wave 1 entregou)
       |
       v
MIDDLEWARE LAYER (estavel)
  Auth JWT, Tenant RLS (ADR-030 defense-in-depth), Rate Limit, Prompt Injection
       |
       v
RUNTIME CONTEXT LAYER (NOVO - ADR-029)
  RuntimeContext typed dataclass
  with_runtime_context decorator declarativo
  R-008 lockdown: NUNCA _current_company_id.set() direto
  Sensor check_no_direct_contextvar_set.py BLOCKING
       |
       v
MEMORY LAYER (Wave 1 entregou)
  Redis-backed SessionStore + ConversationMemory
  History carregada como turns reais user/assistant
  Persist em TODAS as phases (LIA-M01, M02)
       |
       v
COMPLIANCE LAYER (Wave 1 + Wave 2)
  FairnessGuard L3 default ON cross-sector (ADR-031 v3)
  PII Strip + PromptInjection automatica em base class
  ComplianceDomainPrompt obrigatorio (registry rejeita)
  Per-tenant override controlado (ADR-028 v3) - cliente NAO edita YAML cru
  Layer 3: Audit Log Demographic Proxies (ADR-035)
       |
       v
PROMPT COMPOSER LAYER (NOVO - ADR-028)
  Single Source of Truth para system prompts
  Per-tenant YAML override + hot-reload (v3)
  Per-tenant AI persona (E2): cliente customiza nome+tom sem YAML cru
  SystemPromptBuilder._append_ai_persona_override
  ai_persona_validator: 6 tons canonical, blocklist de marcas
       |
       v
ROUTER LAYER (Wave 1 entregou + extensoes)
  Fast-path: KeywordIntentMatcher (158 linhas) compartilhado em YAML
  18 dominios com config/capabilities.yaml (1 pendente: job_creation)
  554 keywords com fonte unica em YAML
  Info/Action disambiguation via is_info_query()
       |
       v
TOOL REGISTRY LAYER (NOVO - ADR-016/018/022/023/024)
  Four-Registry Architecture (ADR-024)
  Tool Registry Taxonomy: action/info/integration/system (ADR-022)
  Subagent vs Tool Decision Criteria (ADR-023)
  Stage Tools Canonical: STAGE_TOOLS allowlist por estagio
  Capability Map Governance (ADR-025)
  Sensor check_tool_governance.py + check_no_langchain_tool_decorator.py
       |
       v
AGENT LOOP (Wave 1 entregou)
  AgenticLoop service (304 linhas, +37% vs V1)
  LLM raciocina -> Tool Call via function calling nativo
  Tool Result -> LLM interpreta -> Response natural
  38 @register_agent (vs 11 em abril)
       |
       v
POST-PROCESSING (Wave 1 entregou + Wave 2)
  FactChecker, AuditService.log_decision
  Response envelope APIResponse (ADR-008) - adocao parcial: 5/729 endpoints
  Audit Log Demographic Proxies + Fairness Decisions Schema (ADR-035)
  Outbox worker wired (sensor check_outbox_worker_wired.py)
```

### 2.1 Principios Arquiteturais V2

V1 listou 6. V2 adiciona 4 (canonicos pos-Wave 2):

1. COMPLIANCE OPT-OUT IMPOSSIVEL (V1, mantido)
2. UM PIPELINE TODOS OS CAMINHOS (V1, mantido)
3. LOOP AGENTICO SEMPRE (V1, mantido)
4. FONTE UNICA DE VERDADE (V1, mantido + ADR-028 PromptComposer + ADR-029 ToolDefinition)
5. MEMORIA PERSISTENTE (V1, mantido)
6. GRACEFUL DEGRADATION (V1, mantido)
7. **REPOSITORY PATTERN ENFORCED** (NOVO) — Services nao fazem SQL inline. Toda query em repositories/. Sensores BLOCKING desde Sprint 8.
8. **MULTI-TENANCY DEFENSE-IN-DEPTH** (NOVO) — Tres camadas: JWT (require_company_id) + Postgres RLS (ADR-030) + tenant_guard.get_verified_company_id. `X-Company-ID` raw header BANIDO (ADR-029-v2).
9. **HARNESS ENGINEERING DISCIPLINE** (NOVO) — Toda intervencao classificada em guide x sensor. Erro de agente = defeito de harness, nao de prompt. Sensores em scripts/check_*.py + tests/contract/.
10. **GHOST SETTING PROIBIDO** (NOVO) — Toda toggle/instrucao em Configuracoes DEVE ter consumer real. UI sem consumer = mentira pro usuario. Pattern canonical: build_company_agent_context (Camada 2 soft) ou check_can_send (Camada 1 hard).

---

## 3. Mapa de Compliance Cross-Functional V2

### 3.1 Estado Atual por Agente (38 agentes hoje)

Wave 1 tinha 11 agentes ReAct. Wave 2 expandiu para 38 (sourcing multiplicou em 9 sub-agentes via W1-001 em 22/mai). Categorias:

- **Recruiter-facing chat**: pipeline, cv_screening, jobs_management, kanban (+ action/insight/search), talent, policy
- **Sourcing**: sourcing (master) + 9 sub-agentes (search, engagement, enrich, planner, diversity, github, nurture_sequence, passive_pipeline, referral, stackoverflow)
- **Workflow**: communication, autonomous, automation, ats_integration, analytics
- **Studio**: agent_studio, job_creation, wizard, recruiter_assistant
- **Operacionais**: persona, digital_twin, recruitment_campaign, talent_pool, candidate_self_service, interview_scheduling, offer, hiring_policy, company_settings

Compliance status: **100% dos 38 agentes** com FairnessGuard automatica via base class (LIA-C05) + ADR-031 v3 default ON cross-sector. Validado por `scripts/check_agent_compliance.py`.

### 3.2 Vulnerabilidades de Seguranca — Status Wave 2

| Vulnerabilidade V1 | Status hoje |
|--------------------|-------------|
| Tenant bypass no consent | RESOLVIDO (LIA-C07 + ADR-029-v2) |
| Tenant bypass no bias audit | RESOLVIDO |
| DEV_MODE sem API key = admin | RESOLVIDO (`check_no_devmode_in_prod_env.py` BLOCKING) |

| Vulnerabilidade V2 (nova) | Status |
|---------------------------|--------|
| 28 sites com `X-Company-ID` Header overwrite JWT | EM PROGRESSO: ADR-029-v2 baniu, baseline 29 violations no sensor R4 |
| 139 endpoints com `company_id` no request payload | EM PROGRESSO: sensor R2 ratchet, fix gradual |
| Silent fallback em path critico de IA | RESOLVIDO no caso F6.B3, sensor recomendado |
| Cross-tenant query sem filtro explicito | SENSOR ATIVO (`check_no_cross_tenant_query.py` + `check_es_search_has_tenant_filter.py`) |

---

## 4. ADRs Canonicos (30 documentados)

### Pre-existentes (V1)

| ADR | Tema | Status |
|-----|------|--------|
| 001 | Repository Pattern | ENFORCED CI (BLOCKING desde Sprint 8) |
| 002 | Canonical Model Location | OK |
| 003 | Prompt Files | OK |
| 004 | Hardcoded Data | OK |
| 005 | Response Models | ENFORCED CI |
| 006 | PII in Logs | ENFORCED CI |
| 007 | File Size Limits | OK |
| 008 | API Response Envelope | Adocao parcial 5/729 |
| 009 | Event Versioning | OK |
| 010 | Unified Event Publisher | OK |
| 011 | WebSocket Message Schema | OK |

### Novos pos-V1 (Wave 2)

| ADR | Tema | Sensor associado |
|-----|------|------------------|
| 016 | Sistema canonico de registro de tools (T#351) | check_tool_governance.py |
| 017 | Modelo de dados do WSI Voice Screening | check_wsi_calls_log_automated_decision.py |
| 018 | Plano de consolidacao operacional do tool registry (T#382) | check_no_legacy_tool_decorator.py |
| 019 (+v2) | Orchestrator V1->V2 Consolidation (LIA-D06) + Services Deduplication | check_no_duplicate_services.py |
| 020 | LangGraph Graph Encapsulation Pattern | check_no_react_loop_import_in_agents.py |
| 021 | JobCreationGraph (Wizard de Criacao de Vaga) | check_no_duplicate_wizard_domain.py |
| 022 | Tool Registry Taxonomy | check_tool_authoring_surface.py |
| 023 | Subagent vs Tool Decision Criteria | — |
| 024 | Four-Registry Architecture | check_agents_registry_paths.py |
| 025 | Capability Map Governance | check_yaml_decorator_coherence.py |
| 028 (+v2/v3) | Single Source of Truth para System Prompts + YAML version enforcement + per-tenant override | check_prompt_composer_uniformity.py + check_yaml_metadata_version.py + check_tenant_yaml_override.py |
| 029 (+v2) | ToolDefinition Unification + Runtime Context Wrapper + R4 cross-tenant header banido | check_no_direct_contextvar_set.py + check_no_admin_company_in_proxies.py + check_pydantic_R4_only.py |
| 030 (+v2/v3) | Postgres RLS Defense-in-Depth + Baseline + HIGH-Priority Batch | check_table_has_rls_policy.py + check_query_has_tenant_filter.py |
| 031 (+v2/v3) | Protected Attributes YAML + Loader Path + FairnessGuard L3 default ON | check_fairness_layer3_default_on.py |
| 032 | Feedback Wire Canonical Pattern (T-10) | — |
| 035 | Audit Log Demographic Proxies + Fairness Decisions Schema (T-20) | check_audit_log_completeness.py + check_audit_hash_chain_exists.py |
| LGPD-001 | Aggregates derived from candidate data (MIN_*_SAMPLES=10) | tests/unit/test_p0_3_min_samples_gate.py |
| LGPD-002 | Training Data Cross-Border Transfer | check_consent_filter_training_data.py + check_lgpd_region_pinning.py |
| AB-001 | Thompson sampling + FairnessConstraint em A/B testing (T-19) | check_ab_fairness_gate.py |
| RLHF-001 | Custom Claude fine-tune via AWS Bedrock (T-11) | — |
| V3.1 | 30 Repository Stubs Reclassification (T-12 correcao) | check_stub_invariants.py |
| WT-2027 | BYOK Strategy: Track-Only When Tenant Pays Direct | check_credit_gate_respects_byok.py |

---

## 5. Sensores Ativos (108 em scripts/check_*.py)

### Categorias

| Categoria | Sensores principais |
|-----------|---------------------|
| **Repository Pattern (ADR-001)** | check_no_sql_inline_in_services.py, check_no_select_in_services.py, check_no_sql_in_controllers.py |
| **Multi-Tenancy (ADR-029-v2, ADR-030)** | check_company_id_in_routes.py, check_query_has_tenant_filter.py, check_no_cross_tenant_query.py, check_no_direct_contextvar_set.py, check_require_company_id_coverage.py, check_tenant_db.py, check_table_has_rls_policy.py, check_es_search_has_tenant_filter.py, check_no_admin_company_in_proxies.py, check_no_client_id_query_bypass.py, check_no_cid_empty_escape.py, check_tenant_columns_not_null.py, check_tenant_nullable_has_repo_enforcement.py |
| **Tool Registry (ADR-016/018/022/024)** | check_tool_governance.py, check_tool_authoring_surface.py, check_agents_registry_paths.py, check_no_langchain_tool_decorator.py, check_no_legacy_tool_decorator.py, check_no_react_loop_import_in_agents.py, check_no_legacy_base_agent.py, check_stage_tools_canonical.py, check_no_tenant_in_tool_schemas.py, check_tool_output_schemas.py |
| **Compliance / Fairness / LGPD** | check_agent_compliance.py, check_fairness_layer3_default_on.py, check_ab_fairness_gate.py, check_audit_log_completeness.py, check_audit_hash_chain_exists.py, check_no_pii_in_logs.py, check_no_plaintext_pii.py, check_consent_filter_training_data.py, check_lgpd_region_pinning.py, check_voice_stt_pii_strip.py, check_training_data_anonymized.py, check_hate_speech_guard_wired.py, check_credentials_access_has_purpose.py |
| **Prompt Composer (ADR-028)** | check_prompt_composer_uniformity.py, check_no_new_hardcoded_persona.py, check_yaml_metadata_version.py, check_tenant_yaml_override.py |
| **Pydantic Conventions (Wave 2)** | check_pydantic_conventions.py, check_pydantic_R1_ratchet.py, check_pydantic_R1_zero.py, check_pydantic_R2_only.py, check_pydantic_R4_only.py |
| **Lia Field Toggles (Wave 2)** | check_agent_respects_lia_toggles.py, check_data_toggle_matches_persisted_key.py, check_lia_field_definitions_sync.py, check_alert_preferences_schema_sync.py |
| **Domain Structure** | check_canonical_domain_structure.py, check_domain_prompt_super.py, check_domain_registry_health.py, check_init_completeness.py, check_orchestrator_init_completeness.py, check_no_duplicate_wizard_domain.py |
| **Wire / Integration** | check_governance_executor_wired.py, check_c3b_wires_injection_guard.py, check_plan_execute_wiring.py, check_proactive_detectors_registered.py, check_outbox_worker_wired.py, check_feedback_wire (ADR-032) |
| **Data / Hardcoded** | check_alert_rules_not_hardcoded.py, check_integrations_not_hardcoded.py, check_pipeline_stages_not_hardcoded.py, check_screening_not_hardcoded.py, check_webhook_events_not_hardcoded.py, check_no_uuid_aggregate_bug.py, check_no_uuid_varchar_join.py |
| **Imports / Boundaries** | check_forbidden_imports.py, check_llm_imports.py, check_no_direct_llm_sdk_imports.py, check_no_imports_from_deprecated.py, check_no_app_domains_policy_imports.py, check_no_recruitment_stages_direct_import.py, check_no_sub_statuses_direct_import.py |
| **Schema / Drift** | check_schema_drift.py, check_schema_sync_recruitment_stage.py, check_duplicate_pydantic_schemas.py, check_duplicate_indexes.py |
| **Deploy / Safety** | check_no_devmode_in_prod_env.py, check_no_dev_fallback_tokens.py, check_required_env.py, check_anthropic_prompt_caching.py, check_llm_call_has_gate.py, check_llm_factory_enforcement.py, check_credit_gate_respects_byok.py, check_grafana_counter_names.py |
| **Anti-pattern** | check_no_silent_llm_fallback.py, check_no_silent_swallow.py, check_no_getattr_on_models.py, check_no_bak_files.py, check_deprecated_rail_a_tools.py, check_no_observability_services_dup.py, check_no_plaintext_credentials.py, check_no_v1_policy_engine.py |

Total: **108 sensores ativos** (vs 4 mencionados em V1).

---

## 6. Pendencias Conhecidas

### 6.1 Pendencias V1 Carregadas (status hoje)

| Item V1 | Status |
|---------|--------|
| Migrar FastRouter shadow -> primary | NAO VERIFICADO nesta auditoria (arquivo presente) |
| Migrar ActionExecutor shadow -> primary | NAO VERIFICADO nesta auditoria |
| Migrar 729 endpoints -> APIResponse | INCOMPLETO: 5/729 adocao (~0,7%). Rollout gradual parou. |
| Fix 752 ruff errors | NAO VERIFICADO nesta auditoria |
| Split celery_tasks.py (2.108 linhas) | RESOLVIDO: 55 linhas hoje, 8 arquivos em app/jobs/ |
| Remove cache_config.py deprecated | PARCIAL: shim com DeprecationWarning, conteudo zerado |
| Remove Orchestrator v1 deprecated | PARCIAL: 675 linhas ainda, ADR-019 oficializou morte, ainda usado por orchestrator_routes.py |
| Migrar RailsAdapter -> unified_event_publisher | NAO VERIFICADO nesta auditoria |

### 6.2 Pendencias Novas (Wave 2)

| Item | Sensor que detecta | Baseline |
|------|--------------------|----------|
| 139 endpoints com company_id no payload (ADR-029-v2 R2) | check_pydantic_R2_only.py | 139 violations |
| 29 sites com X-Company-ID Header overwrite (ADR-029-v2 R4) | check_pydantic_R4_only.py | 29 violations |
| 694 schemas legacy sem extra='forbid' (R1) | check_pydantic_R1_ratchet.py | 694 violations |
| 12 i18n keys ausentes em messages JSON (AgentCard voice) | scripts/check_i18n_keys.py | 12 violations (era 166 em v1 sensor — 72% falsos positivos eliminados em v2 scope-aware) |
| ADR-001 EXEMPT markers (~50) auditoria periodica | revisao manual | — |
| Fragmentacao lia-agent-system <-> recruiter_agent_v5 (camada IA OFICIAL Anderson) | decisao arquitetural | EM ABERTO |

---

## 7. Metricas de Sucesso V2

| Metrica | V1 Antes | V1 Depois (declarado) | V2 Real (medido) |
|---------|----------|-----------------------|------------------|
| "Como funciona X?" gera explicacao | Nao | Sim | Sim |
| Contexto mantido em 5+ turns | Nao | Sim | Sim |
| Dominios sem ComplianceDomainPrompt | 1 | 0 | 0 |
| Agentes sem FairnessGuard | 3 | 0 | 0 |
| Tenant bypasses raw header (consent/bias audit) | 6 | 0 | 0 (resolvidos) |
| Caminhos sem compliance | 1 SSE | 0 | 0 |
| Phases que persistem memoria | 1/3 | 3/3 | 3/3 |
| Security scans blocking | Nao | Sim | Sim |
| Cache configs conflitantes | 2 | 1 | 1 (cache_strategy canonical) |
| **NOVO: ADRs ENFORCED por CI** | — | 3 (001/005/006) | 3 + ratchet |
| **NOVO: Sensores BLOCKING** | — | — | ~30 (Repository Pattern + RLS + Pydantic R3 + multi-tenancy core) |
| **NOVO: APIResponse adoption** | — | infra criada | 5/729 (~0,7%) |
| **NOVO: Agentes registrados** | 11 | — | 38 |
| **NOVO: Per-tenant AI persona** | — | — | E2 entregue 2026-05-21 |

---

## 8. Verificacao End-to-End V2

Cenarios V1 (mantidos):

1. CONVERSA MULTI-TURN: Oi -> Como funciona a plataforma? -> E o Agent Studio? -> Cria um agente de sourcing. LIA mantem contexto. **VALIDADO**
2. COMPLIANCE: prompt com vies (prefira homens). FairnessGuard bloqueia em chat, SSE, WebSocket, expanded-prompt. **VALIDADO** (ADR-031 v3)
3. TOOL CALLING: Lista minhas vagas ativas. LLM chama tool, recebe resultado, gera resposta natural. **VALIDADO** (agentic_loop.py 304 linhas)
4. STREAMING COM COMPLIANCE: SSE com FairnessGuard executando. **VALIDADO**
5. RESTART RESILIENCE: Reiniciar processo. Conversa recuperada do PostgreSQL. **VALIDADO**

Cenarios V2 (novos):

6. **PER-TENANT AI PERSONA**: cliente customiza nome+tom em "Personalidade da IA" -> persona base lia_persona.yaml NAO mutada -> system prompt recebe override section. (`tests/contract/test_ai_persona_*.py`)
7. **LIA RESPEITA TOGGLES**: recrutador desativa campo X em "Instrucoes LIA por Campo" -> agente NAO injeta esse campo no contexto. (build_company_agent_context filtra is_active=true)
8. **OFFER REQUIRES APPROVAL**: hiring_policy.communication_rules.manager_approval_for_offer=true -> OfferService.check_can_send raise PermissionError -> tools/endpoints retornam requires_approval=True. (`tests/contract/test_offer_approval_gate.py`)
9. **CROSS-TENANT HEADER REJEITADO**: enviar X-Company-ID=outra-company-uuid via header -> 403 se header divergir do JWT (get_verified_company_id). (`tests/security/test_tenant_isolation.py`)
10. **PYDANTIC EXTRA FIELDS**: POST com field extra desconhecido -> HTTP 422 (WeDoBaseModel com extra='forbid').

---

## 9. Roadmap pos-V2

### Curto prazo (Sprint 9+)

- Atualizar backend-ci.yml com TODOS os 108 sensores rodando em PR
- Auditar ~50 EXEMPT markers do ADR-001 (justificativa ainda valida?)
- Fix gradual dos 139 R2 violations (request body com company_id)
- Fix das 12 i18n keys do AgentCard -> promover lint:i18n a blocking
- Decisao arquitetural: fragmentacao lia-agent-system vs recruiter_agent_v5

### Medio prazo

- Migrar 724 endpoints restantes para APIResponse (rollout via @api_envelope)
- Migrar FastRouter + ActionExecutor de shadow para primary
- Add `_require_company_id` aos repos legados sem ele
- Consolidar ContextAggregatorService cross-domain reads (P1 bug em context_aggregator_service.py:204)
- Refinement Pydantic R1 baseline (694 -> ratchet gradual)

### Longo prazo

- 80% coverage de testes (V1 target ainda valido)
- mypy --strict em CI (sprint dedicada)
- Canary metric wsi_fallback_rate em Grafana (REGRA 4 sensor de path critico de IA)
- Remover Orchestrator v1 definitivamente quando orchestrator_routes.py migrar

---

Documento gerado em 2026-05-23.
Substitui ARCHITECTURE_TARGET.md V1 (12/abr) como referencia operacional corrente.
V1 continua valido como registro historico da Wave 1 (Fases 1-7 de abril/2026).
