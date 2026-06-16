# LIA Agent System — Relatorio Consolidado de Refatoracao V2

> **Periodo coberto:** 2026-04-13 a 2026-05-23 (40 dias)
> **Escopo:** Wave 2 — pos-Wave 1 (Fases 1-7 de abril, ver V1)
> **Resultado:** 2.621 commits no Replit branch `feat/benefits-prv-canonical`,
> 30 ADRs documentados (+19 desde V1), 108 sensores ativos (+104),
> 38 agentes registrados (+27), 1.025 arquivos de teste (+647), 145K LOC adicionados.

---

## 1. CONTEXTO INICIAL

V1 (LIA_REFACTORING_REPORT.md, 12-13/abr) entregou 7 fases de refatoracao arquitetural com 41 tags LIA-* e 52 arquivos modificados. As 7 fases resolveram os 5 pontos de quebra observados nos screenshots originais (LIA esquecia contexto, regex disparava acao para "como funciona X?", SSE bypassava compliance, etc.).

**A Wave 1 entregou o que prometeu.** Sintomas originais foram eliminados. Os 4 arquivos novos criados em abril continuam vivos e cresceram em LOC (sinal de uso real, nao codigo morto):

- `app/orchestrator/agentic_loop.py` 222 -> 304 linhas
- `app/shared/services/keyword_intent_matcher.py` 158 linhas (estavel)
- `app/schemas/api_envelope.py` 110 -> 127 linhas
- `app/shared/messaging/unified_event_publisher.py` 95 -> 112 linhas

Apos Wave 1, o desenvolvimento continuou no Replit (branch `feat/benefits-prv-canonical`) ao longo de 40 dias. **Wave 2 cobre tudo que aconteceu pos-Wave 1 ate 2026-05-23 (HEAD `3ebf53520`).**

### 1.1 Por que existir um V2

V1 e um documento congelado de 12-13/abr. Em 40 dias, o codigo evoluiu em escala:

| Metrica | V1 | V2 | Multiplicador |
|---------|----|----|---------------|
| LOC Python | 443K | 588K | 1.33x |
| Agentes registrados | 11 | 38 | 3.5x |
| Testes | 378 | 1.025 | 2.7x |
| ADRs | ~11 | 30 | 2.7x |
| Sensores | ~4 | 108 | 27x |

Manter V1 como referencia "viva" mente ao leitor. Wave 2 e um capitulo novo que merece seu proprio documento.

---

## 2. AUDITORIAS REALIZADAS (pos-V1)

### 2.1 Audit E2E Criacao de Vaga (2026-05-20)

`~/Documents/wedotalent_audit_2026-05-20/` consolidou auditoria das 9 fases de criacao de vaga (F1: ATS Importada -> F2: Rascunho -> F3: Enriquecida -> F4: WSI Config -> F5: Aguardando Aprovacao -> F6: Publicada -> F7: Ao Vivo -> F8: Sourcing -> F9: Triagem).

**4 classes de falha sistemica de harness descobertas:**

| Classe | Falha | Sites afetados | Status |
|--------|-------|----------------|--------|
| F2.B1 | `: UUID = Path(..., pattern=...)` quebra build em Pydantic 2.10 | 24 endpoints | RESOLVIDO via app/shared/types.py |
| F1.O2 | POST aceita fields fantasma (Pydantic default extra='ignore') | request bodies project-wide | RESOLVIDO via WeDoBaseModel |
| F4.O1+F5.O1 | endpoints com `company_id` no payload (multi-tenancy via JWT viola) | 139 sites | EM PROGRESSO (sensor R2) |
| F6.B3 | silent fallback em geracao IA mascarando NameError dias/semanas | wsi_service/question_generator.py | RESOLVIDO + sensor recomendado |

### 2.2 Audit SMOKE-#2 LGPD (2026-05-20)

Auditoria descobriu **28 sites em 21 arquivos com cross-tenant data manipulation via header `X-Company-ID`** (user mandava header com outra company-id e operava sobre dados de outra empresa). LGPD/multi-tenancy break.

| Arquivos afetados (amostra) | Status |
|------------------------------|--------|
| candidates_consent.py | RESOLVIDO (3 handlers fix) |
| billing, policies, communication, teams, triagem, big_five, alerts, client_users, communications, event_history, rubric_evaluation, saas_metrics, saturation, technical_tests, toon, admin_agents | EM PROGRESSO (baseline 29 sensor R4) |

### 2.3 Audit Menu Configuracoes Inteligencia Agentes (2026-05-21)

`~/Documents/wedotalent_audit_2026-05-21/menu_configuracoes_inteligencia_agentes.md` descobriu que o painel "Instrucoes LIA por Campo" expunha **34 toggles + 34 strings de instrucao customizada persistidos em `CompanyCultureProfile.lia_field_toggles` e `lia_instructions`, mas NENHUM agente lia esses valores.** Recrutador customizava 34 dimensoes acreditando influenciar a LIA — estava editando JSON inerte.

Mesmo padrao em `manager_approval_for_offer`: toggle visivel em Politicas de Recrutamento sem consumer em `app/domains/offer/`. Ofertas saiam sem aprovacao.

### 2.4 Audit i18n Contract Drift (2026-05-23)

AlertPreferencesPanel shipou 280 LOC com 16 `t()` call sites e **zero mudancas em messages/pt-BR.json**. Pagina mostrou 19 `MISSING_MESSAGE` errors no Next dev overlay. Build passava, vitest passava (fixture local mascarava), eslint passava — bug so detectavel em runtime no browser.

---

## 3. ARQUITETURA-ALVO V2 (delta sobre V1)

V1 propos 6 layers: Entry -> Middleware -> Memory -> Compliance -> Router -> Agent Loop -> Post-Processing.

V2 mantem tudo + adiciona 2 layers entre Middleware e Memory + 1 entre Router e Agent Loop:

```
ENTRY UNIFICADO                                    [V1 - estavel]
  HTTP, SSE, WebSocket
       |
MIDDLEWARE LAYER                                   [V1 - estavel]
  Auth JWT, Tenant RLS, Rate Limit, Prompt Injection
       |
RUNTIME CONTEXT LAYER                              [V2 - NOVO]
  ADR-029: RuntimeContext typed dataclass
  with_runtime_context decorator declarativo
  R-008 lockdown: ContextVar set restrito a helpers canonical
       |
MEMORY LAYER                                       [V1 - estavel]
  Redis SessionStore + ConversationMemory + persist em todas as phases
       |
COMPLIANCE LAYER                                   [V1 + V2 extensoes]
  V1: FairnessGuard automatico via base class + ComplianceDomainPrompt
  V2: ADR-031 v3 FairnessGuard L3 default ON cross-sector
  V2: ADR-035 Audit Log Demographic Proxies + Fairness Decisions Schema
       |
PROMPT COMPOSER LAYER                              [V2 - NOVO]
  ADR-028: Single Source of Truth para system prompts
  ADR-028-v3: Per-tenant YAML override + hot-reload
  E2: Per-tenant AI persona (cliente customiza nome+tom sem YAML cru)
  SystemPromptBuilder._append_ai_persona_override
       |
ROUTER LAYER                                       [V1 - estavel]
  Fast-path KeywordIntentMatcher + 18 capabilities.yaml
       |
TOOL REGISTRY LAYER                                [V2 - NOVO]
  ADR-016: Sistema canonico de registro de tools
  ADR-022: Tool Registry Taxonomy
  ADR-023: Subagent vs Tool Decision Criteria
  ADR-024: Four-Registry Architecture
       |
AGENT LOOP                                         [V1 - estavel, +37% LOC]
  agentic_loop.py 304 linhas (+82 vs V1)
  38 @register_agent (vs 11 em abril)
       |
POST-PROCESSING                                    [V1 + V2 extensoes]
  V1: FactChecker, AuditService.log_decision
  V2: outbox worker wired (check_outbox_worker_wired.py)
  V2: ADR-032 Feedback Wire canonical
```

---

## 4. AS WAVES DE TRABALHO IMPLEMENTADAS POS-V1

Wave 2 organiza-se em **6 fluxos paralelos** ao longo de 40 dias. Diferente de V1 (7 fases sequenciais), Wave 2 e tematico:

### FLUXO A: Sprint B+ canonical-truth (Ondas 1-3)

> Memoria: `project_sprint_b_learning_loops.md`

**Objetivo:** consolidar canonical-truth pos-Wave 1 — eliminar duplicacoes de service, garantir wsi-api canonical, eliminar app/api/wsi_endpoints.py legacy.

**Tags:** prefixo `A.Fase X` e `B.Fase Y`.

| Marco | Entrega |
|-------|---------|
| Sprint B+ | 18 commits, 6 P1 bugs reais corrigidos |
| Onda 1 canonical-truth | Plan&Execute/B10/C9/H4/A2 todos wired (docs diziam TODO) |
| Onda 2 canonical-truth | B.Fase 1+2 + A.Fase 1+2+3 (16 commits novos) |
| Onda 3 canonical-truth | 11 sensores harness novos |
| **A.Fase 3 fechou** | wsi-api 12/12 canonical, app/api/wsi_endpoints.py DELETADO (-986 LOC), 6 sites canonical-first writes |

**ADRs novos resultantes:** 026 (nao listado nas paginas mas mencionado em memoria), 027 (idem), ADR-001 Caminho C (formalizou EXEMPT markers como mecanismo controlado).

### FLUXO B: ADR-001 Repository Pattern Enforcement (Sprint 5.9 -> Sprint 8)

> CLAUDE.md secao "ADR-001 Repository Pattern enforcement (Sprint B+)"

**Objetivo:** sensor 1 (raw SQL em services) + sensor 2 (select direto em services) BLOCKING desde Sprint 8.

**Estado Sprint 8 (2026-05-07):**

- Sensor 1 (`check_no_sql_inline_in_services.py`): 0 violations BLOCKING
- Sensor 2 (`check_no_select_in_services.py`): 0 violations BLOCKING (418 originais -> 0)

**Estrategia:** 39 novos repositorios + ~25 estendidos + ~50 EXEMPT markers documentados.

**Repositorios novos:** ScreeningQuestionSetRepository (9 metodos), CalibrationRepository (13 metodos), WsiRepository (+8 metodos), JobVacancyCrudRepository (+3), CompanyProfileRepository (+2), DepartmentRepository, BenefitRepository, CultureValueRepository, InterviewRepository, CandidateRepository, VacancyCandidateRepository, WhatsAppRepository, TasksRepository, AlertRepository.

### FLUXO C: Pydantic Conventions R1-R6 (audit E2E 2026-05-20)

> CLAUDE.md secao "Pydantic Conventions canonical"

**Objetivo:** 4 regras computacionais + 1 regra documentacional + 1 anti-pattern banido. Sensores em `scripts/check_pydantic_conventions.py` + `tests/contract/test_endpoint_smoke.py` (1798 endpoints, ~34s).

**Regras canonicas:**

| Regra | Descricao | Status |
|-------|-----------|--------|
| R1 | Request body schemas usam `extra='forbid'` ou herdam de WeDoBaseModel | 694 violations baseline (legacy ratchet) |
| R2 | `company_id` proibido em request payload | 139 violations baseline |
| R3 | Path UUID type SEM `pattern` constraint (use type aliases canonical) | **0 violations** |
| R4 | `x_company_id` Header anti-pattern PROIBIDO | 29 violations baseline |
| R5 | Exception handler global + `debug=False` obrigatorios em main.py | OK |
| R6 | (alias para R4 LGPD context) | OK |

**Type aliases canonical:**
- `JobIdParam = Annotated[str, Path(..., pattern=UUID_OR_BIGINT_PATTERN)]`
- `CandidateIdParam`, `CompanyIdParam` (UUID-only)
- `WeDoBaseModel(BaseModel)` com `extra='forbid'` + `validate_assignment=True`

Single source of truth: `app/shared/types.py`.

**Fixes P0 aplicados:**
- F2.B1: 24 sites UUID -> str (R3)
- F2.B2: debug=False + TypeError handler (R5)
- F7.B1: sourcing import error
- F6.B3: safe_json_parse import
- SMOKE-#2 LGPD: 3 handlers candidates_consent.py removendo x_company_id Header overwrite

### FLUXO D: Per-tenant AI Persona (E2, 2026-05-21)

> CLAUDE.md secao "Per-tenant AI persona canonical pattern (E2)"

**Objetivo:** cliente customiza nome+tom da IA per-tenant SEM acesso ao YAML cru. Persona base + tenant override YAML continuam imutaveis pelo cliente — so admin WeDOTalent edita.

**Arquitetura:**

```
UI cliente: tab "Personalidade da IA"
  - input nome (validado 2-20 chars + blocklist marcas)
  - cards de tom (6 canonical)
  - preview ao vivo
       |
PUT /api/v1/company-ai-persona
       v
ai_persona_validator (DRY single source of truth)
       v
CompanyHiringPolicy.communication_rules
  .ai_persona = {name, tone}
  .lia_tone (legacy, sincronizado)
       v
SystemPromptBuilder.build(..., ai_persona={name, tone})
  -> APPENDA sections (Override Persona + Tom Customizado)
  -> lia_persona.yaml base NUNCA e mutada
```

**Tons canonical (6):** definidos em `CANONICAL_AI_TONES` mapeados 1-1 para `TONE_INSTRUCTIONS`. Adicionar tom novo exige commit em `ai_persona_validator.py` + mirror em `use-ai-persona.ts` (TS canonical types).

**Arquivos canonical:**
- `app/domains/persona/services/ai_persona_validator.py`
- `app/domains/persona/services/ai_persona_service.py`
- `app/api/v1/company_ai_persona.py` (REST cliente)
- `app/api/v1/admin_prompts.py` (YAML cru staff WeDOTalent)
- `app/shared/prompts/system_prompt_builder.py:_append_ai_persona_override`
- `plataforma-lia/src/components/settings/AiPersonaPanel.tsx`
- `plataforma-lia/src/hooks/company/use-ai-persona.ts`
- `tests/contract/test_ai_persona_*.py` (67+ sensores)

### FLUXO E: lia_field_toggles canonical pattern (2026-05-21)

> CLAUDE.md secao "lia_field_toggles canonical pattern"

**Objetivo:** eliminar **ghost settings** — todo toggle/instrucao exposto em Configuracoes DEVE ter consumer real.

**Pattern canonical:**

```python
from app.shared.services.lia_agent_context_builder import (
    build_company_agent_context,
)

context_prompt = await build_company_agent_context(
    company_id=current_company_id,
    db=db,
    job_context={"title": ..., "department": ...},
)
system_prompt = f"{base_persona}\n\n{context_prompt}\n\n{task_instructions}"
```

Helper delega ao `LiaFieldConfigService` que filtra por `is_active` + anexa `lia_instructions` como "_Instrucao do recrutador: ..._" inline. Toggle off -> field NAO injetado. Instruction custom -> authority signal pro LLM.

**Para callers que usam `ContextAggregatorService.get_full_context`:** filtragem AUTOMATICA desde 2026-05-21 via `AggregatedContext.lia_filtered_prompt` populado on-load.

**Pattern hard gate (Camada 1):** `OfferService.check_can_send` — service-de-dominio e ponto unico de enforcement, raise `<PermissionError-subclass>` ANTES de qualquer side effect. Defense-in-depth: metodo de transicao (`mark_sent`) tambem enforça.

**Sensor modelo:** `tests/contract/test_offer_approval_gate.py` (5 testes unit puros, baseline 2026-05-21).

### FLUXO F: Multi-Tenancy Defense-in-Depth (ADR-029-v2, ADR-030 trilogia)

> CLAUDE.md secao "ADR-029-v2: R4 cross-tenant Header anti-pattern BANIDO"

**Objetivo:** tres camadas de defesa contra cross-tenant data manipulation.

1. **JWT (auth layer):** `require_company_id` (entrypoint canonical).
2. **Cross-check (header layer):** `tenant_guard.get_verified_company_id` - 403 se header divergir do JWT.
3. **Postgres RLS (storage layer):** ADR-030/v2/v3 — toda tabela com RLS policy aplicada, sensor `check_table_has_rls_policy.py` e `check_query_has_tenant_filter.py`.

**ADR-030 HIGH-Priority Batch (T-02 Sprint 1):** v3 fechou as tabelas criticas. ADR-030-v2 baseline + gaps documentou cobertura.

**Sensor R4 BLOCKING:** `scripts/check_pydantic_conventions.py` R4 detecta `x_company_id: ... = Header(...)` + assignment `company_id = x_company_id ...`. Baseline 29 violations, em fix gradual.

---

## 5. INVENTARIO DE ADRs CANONICOS (V1 + Wave 2)

V1 mencionava ADRs 001-011 (11 ADRs). Wave 2 adicionou 19 ADRs:

### ADRs V1 (mantidos, status atualizado)

| ADR | Tema | Status |
|-----|------|--------|
| 001 | Repository Pattern | ENFORCED CI BLOCKING (Sprint 8) |
| 002 | Canonical Model Location | OK |
| 003 | Prompt Files | OK |
| 004 | Hardcoded Data | OK |
| 005 | Response Models | ENFORCED CI |
| 006 | PII in Logs | ENFORCED CI |
| 007 | File Size Limits | OK |
| 008 | API Response Envelope | Adocao 5/729 (incompleto) |
| 009 | Event Versioning | OK |
| 010 | Unified Event Publisher | OK |
| 011 | WebSocket Message Schema | OK |

### ADRs novos Wave 2

| ADR | Titulo |
|-----|--------|
| 016 | Sistema canonico de registro de tools (T#351) |
| 017 | Modelo de dados do WSI Voice Screening — quem e fonte de verdade |
| 018 | Plano de consolidacao operacional do tool registry (T#382) |
| 019 (+v2) | Orchestrator V1->V2 Consolidation (LIA-D06 Cleanup) + Services Deduplication |
| 020 | LangGraph Graph Encapsulation Pattern |
| 021 | JobCreationGraph (Wizard de Criacao de Vaga) |
| 022 | Tool Registry Taxonomy |
| 023 | Subagent vs Tool Decision Criteria |
| 024 | Four-Registry Architecture |
| 025 | Capability Map Governance |
| 028 (+v2/v3) | Single Source of Truth para System Prompts (PromptComposer) + YAML version enforcement + Per-tenant YAML override + hot-reload |
| 029 (+v2) | ToolDefinition Unification + Runtime Context Wrapper + R4 cross-tenant Header anti-pattern BANIDO |
| 030 (+v2/v3) | Postgres RLS Defense-in-Depth + Baseline + HIGH-Priority Batch |
| 031 (+v2/v3) | Protected Attributes YAML Governance + LGPD/Fairness + Loader Path + FairnessGuard L3 default ON cross-sector |
| 032 | Feedback Wire Canonical Pattern (T-10) |
| 035 | Audit Log Demographic Proxies + Fairness Decisions Schema (T-20) |
| LGPD-001 | Aggregates derived from candidate data (MIN_*_SAMPLES=10) |
| LGPD-002 | Training Data Cross-Border Transfer |
| AB-001 | Thompson sampling + FairnessConstraint em A/B testing (T-19) |
| RLHF-001 | Custom Claude fine-tune via AWS Bedrock (T-11) |
| V3.1 | 30 Repository Stubs Reclassification (T-12 correcao) |
| WT-2027 | BYOK Strategy: Track-Only When Tenant Pays Direct |

**Total: 30 ADRs canonical em `docs/specs/ai/`.**

---

## 6. INVENTARIO DE SENSORES (108 em scripts/check_*.py)

V1 mencionava 4 sensores. Wave 2 tem 108. Categorias:

| Categoria | Sensores | BLOCKING? |
|-----------|----------|-----------|
| Repository Pattern (ADR-001) | 3 | SIM (Sprint 8) |
| Multi-Tenancy / RLS (ADR-029-v2, ADR-030) | 13 | PARCIAL (R3 SIM, R4 ratchet) |
| Tool Registry (ADR-016/018/022/024) | 10 | PARCIAL |
| Compliance / Fairness / LGPD | 13 | PARCIAL |
| Prompt Composer (ADR-028) | 4 | warn-only |
| Pydantic Conventions (Wave 2) | 5 | R3 SIM, R1/R2/R4 ratchet |
| Lia Field Toggles (Wave 2) | 4 | warn-only |
| Domain Structure | 6 | OK |
| Wire / Integration | 6 | OK |
| Data / Hardcoded | 8 | OK |
| Imports / Boundaries | 7 | OK |
| Schema / Drift | 4 | OK |
| Deploy / Safety | 8 | SIM (no-devmode) |
| Anti-pattern | 8 | OK |
| i18n contract (Wave 2) | 1 (em plataforma-lia/scripts/) | warn-only |

**~30 sensores BLOCKING hoje.** Restante e warn-only com ratchet.

---

## 7. METRICAS DE IMPACTO ANTES vs DEPOIS

| Metrica | V1 antes (12/abr) | V1 depois (13/abr) | V2 hoje (23/mai) |
|---------|--------------------|---------------------|------------------|
| "Como funciona X?" gera explicacao | Nao | Sim | Sim |
| Contexto mantido em 5+ turns | Nao | Sim | Sim |
| Dominios sem ComplianceDomainPrompt | 1 | 0 | 0 |
| Agentes sem FairnessGuard automatica | 3 | 0 | 0 (38 agentes!) |
| Tenant bypasses raw header (consent/bias) | 6 endpoints | 0 | 0 (mantido) |
| Caminhos de entry sem compliance | 5/9 | 0/9 | 0/9 |
| Phases que persistem memoria | 1/3 | 3/3 | 3/3 |
| Fonte de intents | 16 dicts + 200 regex | YAML + matcher | YAML + matcher (18/19 yamls) |
| Security scans blocking deploy | Nao | Sim | Sim |
| Tool results interpretados pelo LLM | Nao (cru) | Sim (A01, A02) | Sim (304 linhas agentic_loop) |
| Loop agentico real (function calling) | Nao | Sim opt-in (A04) | Sim default |
| **NOVO Wave 2: ADR-001 Repository Pattern** | inline SQL | inline SQL | 0 violations BLOCKING |
| **NOVO Wave 2: Per-tenant AI persona** | hardcoded | hardcoded | E2 entregue 2026-05-21 |
| **NOVO Wave 2: Ghost settings** | 34+ toggles inertes | 34+ toggles inertes | 0 (consumer obrigatorio) |
| **NOVO Wave 2: Cross-tenant header** | usado em 28+ sites | usado em 28+ sites | BANIDO ADR-029-v2, 29 violations restantes |
| **NOVO Wave 2: Pydantic R3 (UUID+pattern)** | 24 sites broken | 24 sites broken | 0 violations |
| **NOVO Wave 2: Postgres RLS** | parcial | parcial | HIGH-Priority Batch concluido |
| **NOVO Wave 2: ADRs documentados** | ~11 | ~11 | 30 |
| **NOVO Wave 2: Sensores ativos** | ~4 | ~4 | 108 |
| **NOVO Wave 2: Agentes registrados** | 11 | 11 | 38 |
| **NOVO Wave 2: Testes** | ~378 | ~378 | 1025 |

### Taxa de Cobertura Wave 2

- **9/9 entry points** com compliance (V1, mantido)
- **18/19 dominios com `domain.py`** tem `config/capabilities.yaml` (V1 prometia 15, hoje 18 + 1 sem-YAML em job_creation justificado)
- **38/38 agentes** ReAct com FairnessGuard automatica via base class + L3 default ON
- **31 tabelas** com RLS policy aplicada (ADR-030 v3 HIGH-Priority Batch)
- **30 ADRs documentados** em `docs/specs/ai/`
- **108 sensores ativos** em `scripts/check_*.py`
- **1.025 arquivos de teste** distribuidos em `tests/{contract,unit,integration,e2e,security}/`

---

## 8. PENDENCIAS NAO BLOQUEANTES

### Pendencias V1 carregadas (status hoje)

| Item | Status V2 |
|------|-----------|
| Migrar FastRouter shadow -> primary | Nao verificado nesta auditoria |
| Migrar ActionExecutor shadow -> primary | Nao verificado nesta auditoria |
| Migrar 729 endpoints -> APIResponse | 5/729 adocao (~0,7%) — rollout estagnado |
| Fix 752 ruff errors | Nao verificado nesta auditoria |
| Split celery_tasks.py | RESOLVIDO (2108 -> 55 linhas, 8 arquivos em app/jobs/) |
| Remove cache_config.py deprecated | PARCIAL (shim zerado com DeprecationWarning) |
| Remove Orchestrator v1 deprecated | PARCIAL (675 linhas, ADR-019 oficializou morte, ainda usado por orchestrator_routes.py) |
| Migrar RailsAdapter -> unified_event_publisher | Nao verificado nesta auditoria |

### Pendencias Wave 2 (Sprint 9+)

| Item | Onde |
|------|------|
| Fix 139 R2 violations (company_id em request payload) | check_pydantic_R2_only.py |
| Fix 29 R4 violations (X-Company-ID header overwrite) | check_pydantic_R4_only.py |
| Refinement R1 baseline 694 -> ratchet gradual | check_pydantic_R1_ratchet.py |
| Fix 12 i18n keys ausentes (AgentCard voice) | plataforma-lia/scripts/check_i18n_keys.py |
| Auditar ~50 EXEMPT markers ADR-001 (justificativa ainda valida?) | revisao manual |
| Decisao arquitetural: fragmentacao lia-agent-system vs recruiter_agent_v5 | EM ABERTO |
| Bug fix P1 context_aggregator_service.py:204 (ignora company_id apesar de EXEMPT) | manual |
| Canary metric `wsi_fallback_rate` em Grafana | infra |
| Promover lint:i18n a blocking apos fix do AgentCard | frontend-ci.yml |

### Pendencias V1 que viraram pendencias V2

- **APIResponse adoption** ficou parada em 5/729 (~0,7%). Decisao: continuar rollout via `@api_envelope` ou abandonar e remover a infra?
- **Orchestrator v1** continua em produção via `orchestrator_routes.py`. Decisao: deprecar `orchestrator_routes.py` ou manter ate la?

---

## 9. COMO VALIDAR EM PRODUCAO V2

### Cenarios V1 (mantidos, ainda validos)

1. Conversa multi-turn: Oi -> Como funciona? -> E o Agent Studio? -> Cria agente sourcing. LIA mantem contexto.
2. Compliance em todos os caminhos: prompt com vies bloqueado em chat/SSE/WS/expanded-prompt.
3. Tool calling com interpretacao: "Lista minhas vagas ativas" gera resposta natural, nao cru.
4. Restart resilience: reiniciar processo, conversa recuperada do PostgreSQL.
5. Info vs Action disambiguation: "como funciona X?" explica; "lista X" age.

### Cenarios V2 (novos)

6. **Per-tenant AI persona**: cliente troca tom para "amigavel-relaxado" e nome para "Nina" em "Personalidade da IA" -> proxima mensagem da LIA usa esse tom e nome -> persona base lia_persona.yaml NAO foi mutada (verificavel via git diff).
7. **LIA respeita toggles**: recrutador desativa "experience.specific_company" em Instrucoes LIA por Campo -> agente NAO injeta esse campo no contexto -> validavel via log `[LIA-FIELD] filtered out experience.specific_company`.
8. **Offer requires approval**: politica `manager_approval_for_offer=true` -> tentar mandar oferta via tool/endpoint -> retorna `requires_approval=True` -> NAO envia email/whatsapp.
9. **Cross-tenant header rejeitado**: enviar `X-Company-ID=outra-company-uuid` via header -> 403 se header divergir do JWT.
10. **Pydantic extra fields**: POST `/jd/import` com field extra `legacy_metadata` desconhecido -> HTTP 422 explicito (WeDoBaseModel extra='forbid').
11. **Repository Pattern enforced**: tentar add `db.execute(text("SELECT ..."))` em service novo sem `# ADR-001-EXEMPT` -> CI quebra com mensagem canonical pre-commit.

### Feature flags Wave 2

```bash
# V1 mantidos
LIA_AGENTIC_INTERPRET=true       # Phase 4 LIA-A03 (default true)
LIA_AGENTIC_LOOP=true            # Phase 4 LIA-A04 (default true em maio)
LIA_SKIP_MIGRATIONS_IN_CMD=true  # Phase 7 LIA-D02 (default true em maio)

# V2 novos
LIA_FAIRNESS_L3_DEFAULT_ON=true  # ADR-031 v3 (default true)
LIA_PER_TENANT_PERSONA=true       # E2 (default true)
LIA_FIELD_TOGGLES_ENFORCED=true   # E2 ghost settings fix
```

### Logs para Observabilidade V2

Buscar nos logs estes prefixos:

- `[LIA-A01]` Interpretacao LLM rodando (V1)
- `[LIA-A04]` Loop agentico ativo (V1)
- `[LIA-I02]` Info query detectada (V1)
- `[LIA-M01]` Memoria configurada antes de Phase 0 (V1)
- `[LIA-P01]` Compliance no SSE rodando (V1)
- `[LIA-FIELD]` lia_field_toggles filtragem aplicada (V2)
- `[LIA-PERSONA]` Per-tenant AI persona override aplicada (V2)
- `[LIA-FAIRNESS-L3]` ADR-031 v3 cross-sector check (V2)
- `[ADR-001-EXEMPT]` SQL inline ou select direto com justificativa (V2)
- `[RLS]` Postgres RLS policy aplicada na query (V2)

---

## 10. CONCLUSAO

**Wave 2 (40 dias, 2.621 commits) consolidou o que Wave 1 entregou e estendeu em 5 fluxos paralelos:**

1. **Sprint B+ canonical-truth** — wsi-api 12/12, wsi_endpoints.py deletado (-986 LOC), 6 P1 bugs corrigidos
2. **ADR-001 Repository Pattern enforcement** — 0 violations BLOCKING em ambos sensores, 39 repos novos + 25 estendidos
3. **Pydantic Conventions R1-R6** — 4 classes de falha sistemica corrigidas (audit E2E 2026-05-20)
4. **Per-tenant AI persona (E2)** — cliente customiza nome+tom sem YAML cru, 67+ sensores
5. **lia_field_toggles canonical** — 34 ghost settings viraram consumers reais via `build_company_agent_context`
6. **Multi-tenancy defense-in-depth** — JWT + tenant_guard + Postgres RLS (ADR-030 HIGH-Priority Batch concluido)

**ADRs:** 11 -> 30. **Sensores:** 4 -> 108. **Agentes:** 11 -> 38. **Testes:** 378 -> 1025. **LOC:** 443K -> 588K.

**Os 5 sintomas originais V1 continuam resolvidos.** Os 4 novos pontos de quebra descobertos pelo audit E2E 2026-05-20 estao em 3 status: RESOLVIDO (F2.B1, F6.B3), EM PROGRESSO (F4.O1+F5.O1, SMOKE-#2), com sensores ratchet ativos.

**Risco baixo mantido:** todas as mudancas backwards-compatible. Feature flags + sensores warn-only -> blocking via ratchet. Zero quebra esperada em producao.

**Pendencia estrategica em aberto:** decisao sobre fragmentacao `lia-agent-system` (legado transitorio) vs `recruiter_agent_v5` (camada IA OFICIAL Anderson) — frontend ainda chama `lia-agent-system`, migracao em curso. Discutir com Anderson antes de qualquer trabalho novo de config UI.

---

> **Documento gerado em:** 2026-05-23
> **Branch coberta:** `feat/benefits-prv-canonical` HEAD `3ebf53520`
> **Total de ADRs:** 30 (V1 + Wave 2)
> **Total de sensores:** 108
> **Agentes registrados:** 38
> **Arquivos de teste:** 1.025
> **Linhas Python (app/+libs/):** 588.707
> **Commits desde V1:** 2.621
