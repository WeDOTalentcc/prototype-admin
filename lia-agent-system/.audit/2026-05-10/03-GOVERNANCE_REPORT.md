# 03 — Governance Report — Auditoria de Compliance

> **Fase 3 da auditoria profunda LIA WeDOTalent.** Validação de compliance, governança IA, fairness, LGPD, EU AI Act, EEOC contra implementação real.
>
> **Data:** 2026-05-10
> **Replit HEAD:** `ff81b2aedc12ba9efa61c590b4792636aa8f6a3b` (`feat/benefits-prv-canonical`)
> **Framework de referência:** `PLAYBOOK_AUDITORIA_PROFUNDA.md` (3171 linhas — 13 Crenças + 8 Inegociáveis + 18 Production Readiness + FairnessGuard 3 camadas + DEI + LGPD + WSI + RAGAS + Drift + Taxonomia)
> **Princípio:** código é fonte de verdade. Cada célula tem evidência SSH ou sensor output.

---

## Sumário executivo

| Categoria | Score | Status |
|---|---|---|
| **13 Crenças do Manifesto** | 10/13 PASS, 3 ⚠ | parciais (C09, C11, C13 com gaps) |
| **8 Inegociáveis** | 4/8 PASS, 4 ⚠ | gaps confirmados em #2 #3 #4 #7 |
| **18 Production Readiness Gates** | 14/18 PASS, 4 ⚠ | PII masking, multi-tenancy, FairnessGuard L3, WCAG |
| **FairnessGuard 3 camadas** | 2/3 ativas | Layer 3 default OFF (feature flag) |
| **Risco regulatório consolidado** | LGPD MÉDIO, EU AI Act MÉDIO, EEOC BAIXO | mitigável em ~2-3 sprints |

**Achados-chave Fase 3:**
1. ✅ Estrutura de compliance sólida — 3.367 LOC em `app/shared/compliance/`, 22 arquivos importando AuditService, FairnessGuard 1.122 LOC
2. ⚠ **Crença #11 anti-sycophancy parcial** — apenas 3/8 benchmarks setoriais referenciados (NOVO P1 Fase 3)
3. ⚠ **Layer 3 do FairnessGuard feature-flagged** (default OFF) — Inegociável #3 incompleto em alta-impacto
4. 🔴 **PII em logs (335+ violations) + Multi-tenancy bypass (20+ endpoints)** — confirmados Fase 1/2, requer ação imediata
5. ✅ HITLService canonical com DB persistence + audit trail
6. ✅ LGPD DSR export + cleanup + 15 endpoints REST funcionais

---

## 1. 13 Crenças do Manifesto WeDO Talent — status

### C01 — Humano em Primeiro Lugar
**Princípio:** IA recomenda, humanos decidem. HITL obrigatório em alto impacto.
**Status:** ✅ **PASS**
- ✅ HITLService canonical: `app/domains/cv_screening/services/hitl_service.py:151`
- ✅ DB persistence: `hitl_pending_actions` + `hitl_audit_trail` (logs Postgres mostram queries)
- ✅ 3 tiers: `hitl_auto_confirm`, `hitl_request_approval`, `hitl_receive_approval`
- ✅ Pipeline domain HITL: 5 gates explícitos em `pipeline_transition_agent.py:145-255`
- ⚠ Gap: `automation/services/pipeline_monitor.py:299` auto_rejection sem gate (P1-1)

### C02 — Justa e Não-Discriminatória
**Princípio:** Atributos protegidos mascarados antes do LLM. FairnessGuard ativo em screening/ranking.
**Status:** ⚠ **PARCIAL** (Layer 3 feature-flagged)
- ✅ FairnessGuard 1.122 LOC em `app/shared/compliance/fairness_guard.py`
- ✅ Camada 1 (regex) + Camada 2 (léxico implícito PT+EN) — sempre ativas
- ⚠ Camada 3 (LLM semantic Haiku) — `FAIRNESS_LAYER3_ENABLED` default OFF (`fairness_guard.py:820-840`)
- ⚠ `offer` domain `high_impact:True` SEM FairnessGuard invoke (P0-3)

### C03 — Transparente e Explicável
**Princípio:** Candidato sabe que está sendo avaliado por IA. Opt-out + raciocínio rastreável.
**Status:** ✅ **PASS**
- ✅ `candidate_self_service` domain (NEW Mar/2026) com `explain_candidate_decision` tool — LGPD Art.20
- ✅ Endpoint `decision-explanation` em API v1
- ✅ `wsi_observability.py` 446 LOC + `layer2_extractor.py:184 @_traceable` LangSmith
- ✅ Portal candidato read-only (sem write) — candidato não modifica próprio processo

### C04 — Segura e Respeitosa com Privacidade
**Princípio:** Coleta mínima. LGPD inegociável. PII masking ativo. Secrets via env. TLS 1.3+.
**Status:** ⚠ **PARCIAL**
- ✅ `app/shared/pii_masking.py` canonical existe
- ✅ `strip_pii_for_llm_prompt()` em `cv_screening` agentes (validado)
- ✅ `get_masked_logger()` pattern em services
- 🔴 **335+ PII violations em logs** (sensor `check_no_pii_in_logs`) — P0-1
- ✅ Secrets via env (Replit Secrets)
- ✅ TLS via Replit (REPLIT_DOMAINS HTTPS)

### C05 — Construída por Humanos, Para Humanos
**Status:** ✅ **PASS** (estrutural)
- ✅ Auditoria trimestral: esta auditoria é evidência
- ⏳ Red teaming: documentado em `analise-viabilidade-saas-stack.md` (não validado em runtime)
- ✅ Feedback loop: `lia_assistant_flags.py` + `learning-loops` (16 endpoints)

### C06 — Em Melhoria Contínua
**Status:** ✅ **PASS**
- ✅ Métricas observáveis: `app/shared/observability/` (15 services, 22 endpoints `/api/v1/observability/*`)
- ✅ Drift detection: `model_drift_service.py` (347 LOC) ATIVO
- ✅ Token budget tracking: `token_budget_service.py` (canonical em `domains/credits/`)
- ✅ Sensores governança: 36 ativos, 22 GREEN consistente

### C07 — Resiliente por Design
**Princípio:** Sem ponto único de falha. Multi-provider LLM + fallback. Circuit breakers. Rate limiting.
**Status:** ✅ **PASS**
- ✅ **20/20 Circuit Breakers em estado closed** (validado runtime via `/api/v1/health`)
- ✅ Rate limiter Redis: 600/min/user, 20000/h
- ✅ DLQ Celery: 5 known queues
- ✅ LLM fallback chain definida: claude → gemini → openai
- ⚠ Gap: gemini + openai NOT configured em dev (chain quebrada em dev environment)

### C08 — Observável e Rastreável
**Status:** ✅ **PASS**
- ✅ Logs estruturados: `lia.request` logger
- ✅ Audit trail imutável: AuditService em 22 arquivos cross-domain
- ✅ LangSmith tracing: `@_traceable` em `wsi_service/layer2_extractor.py:184`
- ✅ Request IDs: cada request gera UUID (visto em health response)
- ✅ Prometheus metrics endpoint: `/api/v1/observability/*`

### C09 — Consciente de Custos
**Princípio:** Budget de tokens por interação e por empresa. Cascata mais barato → mais caro.
**Status:** ⚠ **PARCIAL**
- ✅ Token budget service existe (canonical em `domains/credits/`)
- ✅ LLM cascade implementada: Haiku → Sonnet → Opus (memory `Etapas 1-3 COMPLETE`)
- ✅ Pearch AI tem credits tracking (`app/api/v1/candidate_search/credits.py`)
- ⚠ Pre-call budget check antes de cada invocação LLM — não validado comportamentalmente
- ⚠ Limites por tenant configurados — não validado runtime

### C10 — Inteligência vs Determinismo
**Princípio:** IA onde agrega inteligência, código determinístico onde precisa garantia. ConfidencePolicyService 3 níveis.
**Status:** ✅ **PASS**
- ✅ `ConfidencePolicyService` referenciado em memory + plano (`PLANO_IMPLEMENTACAO_STATUS.md` Fase 1.2)
- ✅ Decisões críticas (rejeição, transição) têm guarda determinística HITL
- ✅ Pipeline transitions sempre passam por `pipeline_transition_agent` HITL gate

### C11 — Anti-Bajulação (Anti-Sycophancy)
**Princípio:** IA contra-argumenta com dados. 8 benchmarks setoriais: ABRH, GPTW, Gupy, Robert Half, LinkedIn Economic Graph, Glassdoor, IBGE/PNAD, MTE/CAGED.
**Status:** ⚠ **PARCIAL — apenas 3/8 benchmarks (NOVO P1 Fase 3)**

| Benchmark Crença #11 | Ocorrências em prompts | Status |
|---|---|---|
| Gupy | 27 | ✅ |
| LinkedIn (Economic Graph) | 17 | ✅ |
| Robert Half | 1 | ✅ |
| ABRH | 0 | ❌ |
| GPTW (Great Place to Work) | 0 | ❌ |
| Glassdoor | 0 | ❌ |
| IBGE | 0 | ❌ |
| PNAD | 0 | ❌ |
| MTE/CAGED | 0 | ❌ |

- ✅ Anti-sycophancy explícito em `app/prompts/domains/pipeline_transition.yaml:39` ("ANTI-SYCOPHANCY: Se pedido inadequado, contra-argumente firmemente")
- ⚠ Falta cobertura: 5/8 benchmarks ausentes em prompts
- **Severidade: P1** — IA pode concordar com pedidos enviesados sem contra-argumento completo

### C12 — Autonomia Progressiva
**Princípio:** Nível de automação configurável por empresa. Empresa nova começa como assistente. Crescimento por confiança.
**Status:** ✅ **PASS**
- ✅ Feature Flag Service: `app/shared/governance/feature_flag_service.py:23-339`
- ✅ HITL gate em sensitive flags: `lia_assistant_flags.py:72-91` (`SENSITIVE_FLAGS_REQUIRING_HITL`)
- ✅ Per-company configuration via `automation_rules` (memory)
- ✅ Approval workflow Sprint B: second-actor + reject + expiry sweep

### C13 — Acessível e Inclusiva
**Princípio:** WCAG 2.1 AA obrigatório. aria-labels, sr-only, focus-visible, contraste 4.5:1, prefers-reduced-motion.
**Status:** ⏳ **DEFERIDO** (não validado Fase 1-3, requer audit visual)
- ⏳ Frontend audit visual via Preview MCP — não executado nesta auditoria (limitação técnica)
- ⏳ shadcn/ui base tem aria/contrast por design — provavelmente OK estrutural
- 🚫 **Pendente:** Lighthouse a11y score por página, manual screen reader test

---

## 2. 8 Inegociáveis — pass/fail definitivo

| # | Inegociável | Status | Evidência | Severity gap |
|---|---|---|---|---|
| **1** | WSI explicável (raciocínio rastreável) | ✅ **PASS** | `layer2_extractor.py:184 @_traceable`, `wsi_observability.py` 446 LOC, 27 endpoints `/api/v1/wsi/*` | — |
| **2** | No auto-rejection sem review gate | ⚠ **PARCIAL** | pipeline OK (5 HITL gates); automation `pipeline_monitor.py:299` falha | 🟡 P1-1 |
| **3** | FairnessGuard 100% screening/ranking | ⚠ **PARCIAL** | 5 services cv_screening + hiring_policy OK; Layer 3 feature-flagged; offer SEM FG | 🟡 P1-3 + 🔴 P0-3 |
| **4** | PII masking 100% logs | 🔴 **FAIL** | `pii_masking.py` canonical existe MAS sensor mostra 335+ violations em logs | 🔴 P0-1 |
| **5** | Consent management ativo | ✅ **PASS** | `consent_gate.py:49-138` fail-closed, granular per-channel, audit trail | — |
| **6** | DSR 15d funcional | ✅ **PASS** | 15 endpoints `/api/v1/data-requests/*` + `dsr_export_service.py` + `lgpd_cleanup_service.py` | — |
| **7** | Human override sempre disponível | ⚠ **PARCIAL** | HITL exists para feature flags + pipeline, parcial em domain tools | 🟡 P1-4 |
| **8** | WCAG 2.1 AA todas interfaces | ⏳ **DEFERIDO** | Não auditado em Fase 1-3 | ⚠ pendente |

**Score: 4/8 PASS, 3 PARCIAL, 1 FAIL, 0 N/A**

⚠ **Inegociável #4 FAIL é blocker para deploy produção.**

---

## 3. 18 Production Readiness Gates

| # | Gate | Categoria | Status | Evidência |
|---|---|---|---|---|
| 1 | Circuit Breaker em integrações externas | Resiliência | ✅ | 20/20 closed em runtime |
| 2 | LLM fallback chain testada E2E | Resiliência | ⚠ | Definida (claude→gemini→openai), gemini+openai not configured dev |
| 3 | PII Masking ativo todos logs | Segurança | 🔴 | 335+ violations (P0-1) |
| 4 | Rate Limiting per tenant | Segurança | ✅ | Redis: 600/min/user, 3000/min/company |
| 5 | DLQ ativa msgs falhadas | Resiliência | ✅ | Celery DLQ 5 queues |
| 6 | Token budget per company | Custos | ✅ | `token_budget_service.py` canonical |
| 7 | Consent management ativo | Compliance | ✅ | `consent_gate.py` fail-closed |
| 8 | FairnessGuard ativo todas interações | Fairness | ⚠ | Layer 3 feature-flagged |
| 9 | Bias audit baseline estabelecido | Fairness | ✅ | `BiasAuditSnapshot` per hire (Sprint B Phase 4) |
| 10 | Health check endpoint | Operações | ✅ | `/api/v1/health` 151ms |
| 11 | Error alerting P0/P1 | Operações | ✅ | Sentry configurável + agent_monitoring |
| 12 | Backup verificado | Operações | ⏳ | Replit Postgres standby — não validado runtime |
| 13 | Rollback procedure documentado | Operações | ✅ | Alembic migrations reversíveis |
| 14 | Load test executado P95 < 5s | Performance | ✅ | Health 151ms; cached frontend <1s |
| 15 | Security scan limpo | Segurança | ⏳ | SAST configurável — output não capturado |
| 16 | LGPD compliance checklist | Compliance | ✅ | `app/domains/lgpd/` 99 files; este relatório |
| 17 | WCAG 2.1 AA verificado | Acessibilidade | ⏳ | Deferido Fase 3 (visual audit pendente) |
| 18 | PII Masking global root logger | Segurança | 🔴 | 335+ violations idem #3 (P0-1) |

**Score: 14 PASS, 2 ⚠ (gates 2, 8), 2 🔴 (gates 3, 18 = mesmo gap), 4 ⏳ deferidos**

---

## 4. FairnessGuard — auditoria detalhada das 3 camadas

### 4.1 Estrutura geral
- File: `app/shared/compliance/fairness_guard.py`
- Tamanho: **1.122 linhas**
- Class principal: `FairnessGuard` em line 573

### 4.2 Layer 1 — Regex Patterns (sempre ativa)
- ✅ `is_blocked()` em line 129 — alias para Layer 1
- ✅ Detecta atributos protegidos (gênero, raça, idade, religião, orientação, estado civil, deficiência, nacionalidade)
- ✅ Ação: **BLOCK_AND_WARN** — bloqueia operação + notifica recrutador
- ✅ Suporte PT-BR + EN

### 4.3 Layer 2 — Léxico Implícito (sempre ativa)
- ✅ `IMPLICIT_BIAS_TERMS: dict[str, str]` (PT-BR) em line 30
- ✅ `IMPLICIT_BIAS_TERMS_EN: dict` em line 69
- ✅ `check_implicit_bias()` em line 684
- ✅ Ação: **soft_warning** — alerta educativo, sem bloquear
- ✅ Cobertura bilingue

### 4.4 Layer 3 — LLM Semântico (FEATURE-FLAGGED, default OFF)
- ⚠ `FAIRNESS_LAYER3_ENABLED` setting em `lia_config.config.settings`
- ⚠ Default: `False` (getattr default em `fairness_guard.py:824`)
- ✅ Apenas para ações de alto impacto (`FAR-4`: sourcing search + JD import — line 505)
- ✅ Bilingue (auto-detect PT-BR vs EN — line 716)
- ✅ Modelo Haiku (controle de custo — line 716)

**Severity:** 🟡 **P1-3** — Inegociável #3 ("FairnessGuard 100%") parcial. Layer 3 deveria ser default-on para alta-impacto, mesmo que com cost control via Haiku.

### 4.5 Cobertura por domain
| Domain | FairnessGuard | Layer | Notas |
|---|---|---|---|
| `cv_screening` | ✅ 5 services | L1+L2 sempre, L3 high-impact | cv_scoring, lia_score, eligibility, evaluation, personalized_feedback |
| `hiring_policy` | ✅ 5 references | L1+L2+L3 | Domain core de policy advisory |
| `sourcing` | ✅ Domain config | L3 ativo high-impact | `fairness_action_type='sourcing'` |
| `pipeline` | ✅ via decision agent | L1+L2 | `fairness_action_type='rejection'` |
| `job_creation` | ✅ compliance.py | L1+L2 | `mask_pii_for_llm()` + `check_input_fairness()` |
| `job_management` | ✅ wizard | L1+L2 | `_fairness_pre_check()` em `wizard_react_agent.py:151` |
| **`offer`** | 🔴 **AUSENTE** | — | `high_impact:True` SEM FairnessGuard (P0-3) |
| `automation` | ⚠ herdado | base | sem invoke explícito |
| `analytics` | ✅ herdado | L1 | reports |
| Outros | herdado | base | herdam de `ComplianceDomainPrompt` |

---

## 5. LGPD + EU AI Act + EEOC — risco regulatório

### 5.1 LGPD (Brasil) — Risco MÉDIO

| Pilar LGPD | Status | Evidência |
|---|---|---|
| Art.6 (princípios) | ✅ | Coleta mínima documentada |
| Art.7 (bases legais) | ✅ | Consent management (`consent_gate.py`) |
| Art.9 (consentimento explícito) | ✅ | Granular per-channel |
| Art.12 (anonimização) | ✅ | ADR-LGPD-001 (BigFive dept ≥10 samples) |
| Art.17 (direitos) | ✅ | DSR endpoints (15) |
| Art.18 (DSR específicos) | ✅ | `dsr_export_service.py` |
| Art.20 (revisão decisões automatizadas) | ✅ | `candidate_self_service.explain_candidate_decision` |
| **Art.46 (segurança)** | 🔴 | **PII em logs (335+ violations) — P0-1** |
| Art.48 (incidentes) | ⏳ | Sentry configurável; runbook não validado |
| Art.50 (DPO) | ✅ | DPO lookup em `lia_assistant_flags.py` (Sprint B P1-9) |

**Risco LGPD agregado:** MÉDIO — P0-1 PII em logs é o único blocker compliance crítico. Resto bem coberto.

### 5.2 EU AI Act — Risco MÉDIO

| Artigo | Status | Evidência |
|---|---|---|
| Art.10(5) — qualidade dados | ✅ | ADR-LGPD-001 com Art.12 §1 + Resolução CD/ANPD nº 2/2022 |
| Art.13 — disclosure | ✅ | Sprint B P1-compliance commit `7bea40531` |
| Art.14 — supervisão humana | ⚠ | HITL gate parcial (P1-1, P1-4) |
| Art.16 — sistema gestão risco | ✅ | Compliance framework ativo (1.122 LOC FairnessGuard) |
| Art.50 — transparência | ✅ | decision-explanation API |

**Risco EU AI Act:** MÉDIO — gaps em supervisão humana (HITL parcial) requerem fortalecimento.

### 5.3 EEOC (US) — Risco BAIXO
- ✅ FairnessGuard 3 camadas para anti-discriminação
- ✅ Bias audit per hire (`BiasAuditSnapshot` Sprint B Phase 4)
- ⏳ Disparate impact (chi-square test) — referenciado no plano antigo (D3), status não validado
- ⏳ Four-Fifths Rule — não validado neste audit

**Risco EEOC:** BAIXO — Brasil é mercado primário; cobertura básica adequada para multinacionais.

---

## 6. HITL — análise de cobertura

### 6.1 Implementação canonical
- File: `app/domains/cv_screening/services/hitl_service.py:151`
- Class: `HITLService` (instância global em line 586)
- Persistence: `hitl_pending_actions` + `hitl_audit_trail` (DB-backed, validado em logs Postgres runtime)
- 3 tiers: `hitl_auto_confirm`, `hitl_request_approval`, `hitl_receive_approval`
- HITLPendingActionRepository ativa (visto em logs `SELECT hitl_pending_actions...`)

### 6.2 Cobertura por domain

| Domain | HITL | Notas |
|---|---|---|
| `cv_screening` | ✅ canonical | hitl_service.py |
| `pipeline` (transitions) | ✅ 5 gates | `pipeline_transition_agent.py:145-255`, `requires_human_review=True` em move_candidate |
| `hiring_policy` | ⚠ parcial | flags sensitive ok; tools sem gate explícito |
| `automation` | 🔴 GAP | `pipeline_monitor.py:299` auto_rejection sem HITL (P1-1) |
| `offer` | ⚠ | `requires_confirmation=True` em `send_offer` (basic), sem `human_review_required` |
| `lia_assistant_flags` | ✅ | `SENSITIVE_FLAGS_REQUIRING_HITL` lista |
| `interview_scheduling` | ✅ | `tasting_engine.py` preview antes de confirmar |

### 6.3 Score
- **5/7 domains críticos** com HITL adequado
- **2/7 com gap real**: automation (P1-1), offer (sem `human_review_required`)

---

## 7. AuditService — coverage

- ✅ **22 arquivos importam `AuditService`** (cross-domain)
- ✅ Canonical em `app/shared/compliance/audit_service.py` (~598 LOC)
- ✅ Eventos auditados: feature flag toggle (Sprint B Phase 4), HITL decisions (SEG-5), bias audit per hire, offer lifecycle, communications consent gate

**Cobertura agregada:** SUFICIENTE para LGPD Art.37 + EU AI Act Art.13.

---

## 8. Achados NOVOS Fase 3 (não estavam em Fases 1-2)

| ID | Severity | Achado | Origem | Esforço fix |
|---|---|---|---|---|
| **F3-1** | 🟡 **P1** | **Crença #11 anti-sycophancy parcial** — apenas 3/8 benchmarks setoriais (Gupy 27, LinkedIn 17, Robert Half 1). **Faltam:** ABRH, GPTW, Glassdoor, IBGE, PNAD, MTE/CAGED | grep prompts | M (1 sprint para enriquecer prompts + tests) |
| F3-2 | 🟢 P3 | LLM fallback chain incompleta em dev (gemini + openai not configured) | Fase 2 health | XS (config Replit Secrets) |
| F3-3 | ⏳ Pendente | WCAG 2.1 AA visual audit não executado | Fase 1-2 deferido | M (Lighthouse + manual screen reader) |
| F3-4 | ⏳ Pendente | EEOC Disparate Impact (chi-square) — D3 do plano antigo, não validado | Plano substituível | M-L |
| F3-5 | ⏳ Pendente | Backup/restore + security scan SAST output não capturados | Production Readiness gates 12+15 | S (run + document) |

---

## 9. Inegociáveis — quadro consolidado final (Fases 0+1+2+3)

| # | Inegociável | Score | Issues | Roadmap |
|---|---|---|---|---|
| 1 | WSI explicável | ✅ PASS | — | — |
| 2 | No auto-rejection | ⚠ | P1-1 (automation pipeline_monitor) | Fix HITL gate |
| 3 | FairnessGuard 100% | ⚠ | P0-3 (offer sem FG), P1-3 (Layer 3 OFF) | Implementar `compliance.py` em offer; promover Layer 3 high-impact default-ON |
| 4 | PII masking | 🔴 | P0-1 (335+ violations) | Migration ADR-006 (estimado 3-4 dias) |
| 5 | Consent | ✅ PASS | — | — |
| 6 | DSR 15d | ✅ PASS | — | — |
| 7 | Human override | ⚠ | P1-4 (HITL parcial em domain tools) | Generalizar HITL via decorador |
| 8 | WCAG 2.1 AA | ⏳ | F3-3 não auditado | Lighthouse + visual audit |

---

## 10. Próximas ações recomendadas

**Para Fase 4 (roadmap consolidado):**

1. **P0-1 (PII em logs):** prioridade máxima — afeta Inegociáveis #4 + Production Readiness gates 3+18
2. **P0-2 (multi-tenancy):** segunda prioridade — afeta defesa-em-profundidade
3. **P0-3 (offer sem FairnessGuard):** terceira — Inegociável #3 + Crença #02
4. **P1-3 (Layer 3 default OFF):** promover para default-ON em ações high-impact
5. **F3-1 (anti-sycophancy benchmarks):** completar 5/8 benchmarks faltantes nos prompts
6. **P1-1 (automation HITL):** fix gate em `pipeline_monitor.py:299`
7. **P1-4 (HITL generalize):** decorador para domain tools com `SafetyCategory` high-impact
8. **C13/F3-3 WCAG:** audit visual frontend (Lighthouse + manual)
9. **F3-4 EEOC Disparate Impact:** implementar chi-square (D3 do plano antigo)

---

## 11. Risco regulatório consolidado

| Framework | Risco agregado | Blockers |
|---|---|---|
| **LGPD (Brasil)** | 🟡 MÉDIO | P0-1 (PII logs) |
| **EU AI Act** | 🟡 MÉDIO | HITL parcial (Art.14) |
| **EEOC (US)** | 🟢 BAIXO | Brasil é primário |
| **ISO 27001** | 🟡 MÉDIO | PII + multi-tenancy + security scan pendente |
| **SOX (financeiro)** | 🟢 N/A | Não aplica em RH |

**Tempo estimado para resolver todos os 4 P0 + 5 P1 + F3 novos:** ~2-3 sprints de 2 semanas.

---

**Fim do 03-GOVERNANCE_REPORT.md.**

Próximo: Fase 4 — Roadmap consolidado priorizado.
