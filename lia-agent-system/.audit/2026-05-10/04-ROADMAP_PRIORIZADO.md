# 04 — Roadmap Priorizado — Auditoria Profunda LIA

> **Fase 4 da auditoria profunda LIA WeDOTalent — entregável final.** Substitui efetivamente `PLANO_SPRINTS_Y1_Y5.md` (a ser arquivado após este).
>
> **Data:** 2026-05-10
> **Replit HEAD:** `ff81b2aedc12ba9efa61c590b4792636aa8f6a3b` (`feat/benefits-prv-canonical`)
> **Base:** Achados validados nas Fases 0, 1, 2, 3 (todos via SSH/sensor real, não via docs antigos)
> **Princípio:** código = fonte de verdade. Cada item do roadmap aponta para evidência file:line + comando SSH.

---

## Sumário executivo

A plataforma LIA está **estruturalmente sólida** (19 domains agentic, 36 sensores governança, 50+ commits Sprint B + Phase 2.5 OCEAN). O roadmap aqui consolidado tem **20 itens acionáveis priorizados**:

| Severity | Count | Esforço total | Tempo agregado |
|---|---|---|---|
| 🔴 **P0** (blockers compliance) | **3** | M+L+M | ~2 sprints |
| 🟡 **P1** (críticos governança) | **6** | XS+S+M+M+M+S | ~2 sprints |
| 🟢 **P2** (qualidade/consistência) | **7** | XS-M cada | ~1-2 sprints |
| 🔵 **P3** (nice-to-have) | **4** | XS-S | acoplável |

**Tempo total estimado para fechar P0 + P1:** **~4 sprints (8 semanas)** trabalho focado.

**ONDAS DE EXECUÇÃO RECOMENDADAS:**
1. **Onda 1 (Compliance crítico)** — 4 semanas: P0-1 + P0-2 + P0-3
2. **Onda 2 (Governança fortalecimento)** — 3 semanas: P1-1 + P1-2 + P1-3 + P1-4 + F3-1 (anti-sycophancy)
3. **Onda 3 (Qualidade + cobertura)** — 2 semanas: P1-5 (job_management tests) + P2-1..P2-7
4. **Onda 4 (Backlog estratégico)** — após estabilização: P3 + capacidades novas (Y4 do plano antigo)

---

## Tabela completa: 20 achados × ação × esforço × dependência

| ID | Severity | Achado | Domain/File | Ação | Esforço | Dep |
|---|---|---|---|---|---|---|
| **P0-1** | 🔴 | 335+ PII em logs (Inegociável #4 + Production Gate 3+18 + LGPD Art.46) | 15+ files | Migration ADR-006: f-string → `extra={}` | **L** (3-4d) | — |
| **P0-2** | 🔴 | 20+ endpoints sem `_require_company_id()` (multi-tenancy defesa-em-profundidade) | recruitment_stages 9, ats.py 3 | Adicionar `_require_company_id()` ou marker `# multi-tenancy: <reason>` | **M** (2-3d) | — |
| **P0-3** | 🔴 | `offer` `high_impact:True` SEM FairnessGuard (Inegociável #3 + Crença C02) | `app/domains/offer/` | Implementar `compliance.py` espelhando `job_creation/compliance.py` — pre-check em `send_offer` | **M** (2d) | — |
| **P1-1** | 🟡 | `automation/pipeline_monitor.py:299` auto_rejection sem HITL (Inegociável #2) | automation | Adicionar `human_review_required=True` gate + audit log | **S** (1d) | — |
| **P1-2** | 🟡 | Agent compliance gaps em 3 agents (sensor `check_agent_compliance`) | automation_react, autonomous_react, talent_react | Adicionar `@register_agent` + LangGraphReActBase + EnhancedAgentMixin inheritance | **M** (2d) | — |
| **P1-3** | 🟡 | FairnessGuard Layer 3 feature-flagged default OFF (Inegociável #3 incompleto) | `fairness_guard.py:820-840` | Promover `FAIRNESS_LAYER3_ENABLED=true` default em ações high-impact (manter cost control via Haiku) | **S** (1d + monitoring) | — |
| **P1-4** | 🟡 | HITL gate só em feature flags, não em domain tools (Inegociável #7) | shared | Decorador `@require_hitl` + middleware para tools com `SafetyCategory` high-impact | **M** (2-3d) | — |
| **P1-5** | 🟡 | `job_management` 0 testes específicos (29 actions + WizardReActAgent sem cobertura) | tests/domains/job_management/ | TDD: criar mínimo 15 testes E2E agent → domain flow | **M** (3d) | — |
| **F3-1** | 🟡 | Crença #11 anti-sycophancy 3/8 benchmarks (faltam ABRH, GPTW, Glassdoor, IBGE, PNAD, MTE/CAGED) | `app/prompts/domains/*.yaml` | Enriquecer prompts com 5 benchmarks faltantes + tests | **M** (1-2 sprints) | — |
| **P2-1** | 🟢 | `hiring_policy` 2 tools sem FairnessGuard invoke explícito | `tools/policy_tools.py:15-114` | Adicionar `_fairness_guard.run_fairness_check()` em check_diversity_targets + validate_job_requirements | XS (4h) | — |
| **P2-2** | 🟢 | `ats_integration` webhook só valida signature, sem company_id | `app/api/v1/ats.py:649-758` | Adicionar `_require_company_id()` em handler de webhook | XS (2h) | — |
| **P2-3** | 🟢 | `recruitment_campaign` skeleton (4 actions sem agents/tools) | `app/domains/recruitment_campaign/` | Decisão: completar implementação OU declarar como wrapper de `job_management` (capabilities.yaml) | M (2d planejamento + 3-5d impl) | — |
| **P2-4** | 🟢 | `company_settings` `import_benefits_from_data` sem consent validation | `tools/import_tools.py:318-425` | Integrar `consent_gate.py` antes de import | S (1d) | — |
| **P2-5** | 🟢 | ExpandableAIPrompt em frontend mas não em backend recruiter_assistant | plataforma-lia + recruiter_assistant | Validar pattern: é só frontend (ok)? Ou requer endpoint backend? | XS (2h investigation) | — |
| **P2-6** | 🟢 | Auth Enforcement com synthetic dev mode (`auth_enforcement.py:293-296`) | middleware | Garantir que prod env nunca permita LIA_DEV_MODE=true (sensor `check_no_devmode_in_prod_env`) | XS (config validation) | — |
| **F2-1** | 🟢 | 4 páginas frontend retornam 404 (paths antigos) | plataforma-lia/src/app/[locale]/ | Auditar Next.js App Router; documentar mapeamento real (ou criar redirects) | S (1d) | — |
| **F3-2** | 🔵 | LLM fallback chain: gemini + openai not configured em dev | env config | Configurar Replit Secrets (não bloqueia dev) | XS (config) | — |
| **F3-3** | 🔵 | WCAG 2.1 AA visual audit não executado | frontend | Lighthouse a11y score por página + manual screen reader test | M (2-3d) | — |
| **F3-4** | 🔵 | EEOC Disparate Impact (chi-square) não validado (D3 plano antigo) | `bias_audit_service.py` | Implementar `_chi_square_test()` + p-value + flag `eeoc_compliant` | M (2-3d) | — |
| **F3-5** | 🔵 | Backup/restore + security scan SAST output não capturados | infra | Validar Postgres standby + run SAST + document outputs | S (1d) | — |

---

## ONDA 1 — Compliance crítico (4 semanas)

**Meta:** fechar todos 3 P0 antes de qualquer feature nova. Aceleram redução de risco LGPD/Multi-tenancy.

### Sprint 1.1 (semana 1-2) — P0-1 PII em logs

**Objetivo:** zero violations no sensor `check_no_pii_in_logs`.

**Plano TDD:**
1. **Red phase:** sensor já é red (335+ violations). Adicionar test `test_pii_masking_canonical.py` com 3 logs sintéticos contendo PII; expect `PIIMaskingFilter` mascarar.
2. **Migration:** script Python que parseia f-strings em logs (regex `logger\.(info|warning|debug|error)\(f"[^"]*\{[^}]*\}[^"]*"`) e converte para `logger.info("...", extra={"field_masked": mask(field)})`.
3. **Boundary:** estabelecer ADR-006 enforcement em `app/middleware/pii_masking_middleware.py` (root logger filter ativo automaticamente).
4. **Green:** rodar `python scripts/check_no_pii_in_logs.py` → 0 violations.
5. **Commit por arquivo** (335 instances mas pattern repetitivo, ~8-10 commits temáticos).

**Áreas afetadas:**
- `app/api/v1/communications.py` (multiple)
- `app/api/v1/client_users.py` (multiple)
- `app/api/v1/company.py`
- 12+ outros files

**Acceptance:**
- ✅ Sensor green
- ✅ Test `test_pii_masking_canonical.py` passing
- ✅ Logs em runtime (validar via `tail -f /tmp/lia-backend-stdout.log` durante request) sem PII visível

### Sprint 1.3 (semana 2-3) — P0-2 Multi-tenancy bypass

**Objetivo:** zero violations no sensor `check_company_id_in_routes`.

**Plano TDD:**
1. **Red:** sensor já green-blocking (mas warn-only para alguns). Adicionar test E2E que tenta acessar resource de companyB com token de companyA → expect 403/404.
2. **Fix:** adicionar `_require_company_id()` em cada endpoint identificado:
   - `recruitment_stages/stages_crud.py:104` `update_stage()`
   - `recruitment_stages/stages_crud.py:136` `delete_stage()`
   - `stages_substatus.py:120` `patch_sub_status()`
   - `stages_substatus.py:146` `delete_sub_status()`
   - `stages_transition.py:266` `execute_transition()`
   - `stages_ats_mapping.py:79` `delete_ats_mapping()`
   - `ats.py:63-123` `POST /ats/connections`
   - `ats.py:249-289` `POST /ats/field-mappings`
   - `ats.py:411-566` `POST /ats/connections/{id}/sync`
3. **Marker exception:** se algum endpoint legitimamente cross-company (admin analytics), adicionar `# multi-tenancy: <reason>` + path em ALLOWLIST do sensor.
4. **Promoção sensor:** `--block` flag (já BLOCKING).
5. **Green:** sensor 0 violations.

**Acceptance:**
- ✅ Sensor green
- ✅ Test E2E cross-tenant returns 403/404
- ✅ RLS Postgres role continua ativo (logs visiveis)

### Sprint 1.5 (semana 3-4) — P0-3 Offer sem FairnessGuard

**Objetivo:** `app/domains/offer/` com `compliance.py` espelhando `job_creation/compliance.py`.

**Plano TDD:**
1. **Red:** test `test_offer_fairness_pre_send.py` envia offer com texto enviesado ("apenas homens com mais de 30 anos") → expect block.
2. **Implementar:**
   - `app/domains/offer/compliance.py`:
     - `check_input_fairness()` antes de `send_offer`
     - `mask_pii_for_llm()` em offer text generation
     - `emit_offer_audit()` (similar a `emit_job_creation_audit`)
   - Hook em `domain.py` `_dispatch_tool` para chamar `check_input_fairness` antes de `send_offer`/`update_offer_draft`
3. **Anchor:** `OfferDomain` config já tem `fairness_action_type: "offer"` — só falta wire.
4. **Green:** test passing + grep `FairnessGuard` em offer/ retorna ≥3 hits.

**Acceptance:**
- ✅ Sensor `check_agent_compliance` ainda green
- ✅ FairnessGuard invocado em `send_offer`, `update_offer_draft`, `prepare_offer_manual_send`
- ✅ Audit log gerado por offer lifecycle event

---

## ONDA 2 — Governança fortalecimento (3 semanas)

**Meta:** fechar todos P1 (cobertura HITL + Layer 3 + anti-sycophancy + tests).

### Sprint 2.1 — P1-1 + P1-3 + P1-4 (HITL generalize + Layer 3 default-on)

**P1-1:** `automation/pipeline_monitor.py:299` add HITL gate — TDD red→green
**P1-3:** Promover Layer 3 default-on em high-impact:
- Mudar `_layer3_enabled = getattr(_settings, "FAIRNESS_LAYER3_ENABLED", True)` (line 824)
- OU mudar default em `lia_config/config.py` settings.
- Adicionar token budget cap específico para Layer 3 (Haiku é barato mas tem limite per company).
- Test: `test_fairness_layer3_default_on.py` — request high-impact action sem flag explícita → Layer 3 ativa.
**P1-4:** Decorador `@require_hitl` em `app/shared/hitl_decorator.py` aplicável a tools com `SafetyCategory.HIGH_IMPACT`.

### Sprint 2.2 — P1-2 (Agent compliance gaps)

3 agents fix:
- `automation_react_agent.py` — adicionar `@register_agent("automation")` + LangGraphReActBase + EnhancedAgentMixin
- `autonomous_react_agent.py` — idem
- `talent_react_agent.py` — idem (FAR-2 violation)

Test: sensor `check_agent_compliance` green.

### Sprint 2.3 — F3-1 (Anti-sycophancy benchmarks)

Enriquecer prompts em `app/prompts/domains/`:
- `analytics.yaml` — adicionar referências ABRH, GPTW, Glassdoor, IBGE/PNAD, MTE/CAGED
- `hiring_policy.yaml` — idem para policy advisory
- `pipeline_transition.yaml` — anti-sycophancy reforçar com benchmarks
- `company_settings.yaml` — benefits benchmarks ABRH

Test: golden snapshot tests asserting cada prompt cobre 8/8 benchmarks.

---

## ONDA 3 — Qualidade + cobertura (2 semanas)

**Meta:** fechar P1-5 + todos P2.

### Sprint 3.1 — P1-5 job_management testes

Criar `tests/domains/job_management/`:
- `test_create_job_action.py` — agent → service → repo → DB
- `test_publish_job_action.py` — incluindo PII redaction + FairnessGuard pre-check
- `test_close_job_action.py`
- `test_wizard_react_agent_integration.py` — full conversation flow
- `test_29_actions_smoke.py` — uma assertion mínima por action
- (target: ~15 testes)

### Sprint 3.2 — P2 cleanup

- P2-1 `hiring_policy` FairnessGuard invokes (4h)
- P2-2 `ats` webhook company_id (2h)
- P2-3 `recruitment_campaign` decisão arquitetural + impl (M)
- P2-4 `company_settings` consent gate em import (1d)
- P2-5 ExpandableAIPrompt investigation (2h)
- P2-6 prod dev_mode block (sensor)
- F2-1 frontend route consolidation (1d)

---

## ONDA 4 — Backlog estratégico (após Ondas 1-3 estáveis)

### P3/Pending
- F3-2 LLM fallback config produção (Mailgun, Resend, Gemini, OpenAI keys)
- F3-3 WCAG audit visual + Lighthouse + manual screen reader
- F3-4 EEOC Disparate Impact (chi-square test)
- F3-5 Backup/restore drill + SAST output

### Capacidades novas (do plano antigo Y3+Y4 que ainda fazem sentido)
- Confidence Calibration 14/14 agentes (D2 antigo)
- Score breakdown clicável no funil (E1 antigo)
- Análise comparativa visual side-by-side (D9 antigo)
- ML adaptativo loop de feedback (D6 antigo)
- Benchmark salarial real Apify/Glassdoor (D7 antigo)
- Multi-Model por agente (E5 antigo)
- WSI assíncrono (E3 antigo)

---

## Substituição do plano antigo

`PLANO_SPRINTS_Y1_Y5.md` (Y1-Y5, ~428h, 27 itens em Grupos C/D/E) está agora **substituído** por este `04-ROADMAP_PRIORIZADO.md`. Mapping itens antigos → novos:

| Item antigo | Substituído por |
|---|---|
| C1 LGPD campos sensíveis dinâmicos | ✅ Já feito (Sprint Pre-flight + Sprint B P0-3) |
| C2 Audit trail interview | ✅ Já feito (`AuditService.log_action` Sprint B Phase 4) |
| C3 WSI 7 dimensões rubrica | ⏳ Verificar se completo (sensor `check_plan_execute_wiring` 28 patterns) |
| C4 Métricas Prometheus | ✅ Já feito (`/api/v1/observability/*`) |
| D1 JobReportModal Backend Real | (deferido — UX não-bloqueante) |
| D2 Confidence Calibration | Onda 4 backlog |
| D3 Bias Audit Disparate Impact | F3-4 (Onda 4) |
| D4 Bias detection patterns | ✅ Já feito (`BiasAuditSnapshot` Sprint B) |
| D5 Consentimento granular | ✅ Já feito (`granular_consent.py`) |
| D6-D7-D8-D9 | Onda 4 backlog |
| D10 Pearch fallback | ✅ Já feito (Pearch active + Apify fallback) |
| E1-E12 | Onda 4 backlog |

**Itens novos validados em Fases 1-3** que não estavam no plano antigo: P0-1, P0-2, P0-3, P1-1, P1-2, P1-3, P1-4, F3-1.

---

## Anti-Sycophancy honesto: o que esta auditoria NÃO cobriu

Para coerência com a Crença #11, listo limitações desta auditoria:

1. **Frontend audit visual** (Inegociável #8 WCAG, Crença #13) — Preview MCP precisa tunnel/setup; deferido
2. **Comportamental autenticado** — não geramos JWT dev, então P0-1 e P0-2 são *static* + *runtime defense* mas não foram exploited end-to-end
3. **Load testing** — `/api/v1/health` 151ms validado, mas não testamos volume (1000 req/s? P95 sob carga?)
4. **Failure injection** — Circuit Breakers `closed` confirmados, mas não testados quando provider real falha (e.g. desligar Anthropic)
5. **Backup/restore drill** — Postgres standby existe, restore real não validado
6. **Security scan SAST/DAST output** — sensor existe, output não capturado
7. **Multi-region disaster recovery** — N/A para Replit single-region
8. **Cost analysis em produção** — token budget tracking ativo, mas não mensuramos custo real per company
9. **A/B testing comportamental** — feature flags ativos, mas não validamos efeito em métricas
10. **Drift detection em produção** — `model_drift_service.py` ativo, mas não rodamos contra dados reais 30+ dias

**Recomendação:** estas limitações viram backlog explícito (não "nice-to-haves" silenciosos) — Sprint 5+ após estabilização.

---

## Sensor de qualidade do roadmap

| Critério | Status |
|---|---|
| Cada item P0/P1 tem evidência file:line + comando SSH | ✅ |
| Cada item tem severity + esforço + dependências | ✅ |
| Plano TDD presente para todos P0 | ✅ |
| Acceptance criteria explícito para cada Sprint | ✅ |
| Mapping com plano antigo (substituição) | ✅ |
| Limitações desta auditoria documentadas | ✅ |
| Próxima fase clara | ✅ Execução em ondas (não nesta auditoria) |

---

## Encerramento da auditoria

Esta auditoria 2026-05-10 produziu 5 documentos canonical (commits Replit `48cdd3bd9` → `f36544a7c`):
- `00-CAPACIDADES_LIVE.md` (358 linhas)
- `00b-INVENTARIO_DOCUMENTAL.md` (213 linhas, prescritivo)
- `01-MATRIZ_CAPACIDADE_CODIGO.md` (389 linhas, SSH-validated)
- `02-SMOKE_TESTS_RESULTS.md` (327 linhas, runtime)
- `03-GOVERNANCE_REPORT.md` (380 linhas, compliance)
- `04-ROADMAP_PRIORIZADO.md` (este, ~360 linhas)

**Total:** ~2.000 linhas de evidência consolidada, **todas SSH-validated** contra Replit canonical HEAD `ff81b2aed`.

**Próximas ações para Paulo:**
1. **Aprovar** este roadmap (Onda 1 começa imediatamente?)
2. **Decisão sobre PLANO_SPRINTS_Y1_Y5.md antigo:** arquivar via processo Anderson/time canonical (fora do nosso escopo — REGRA ZERO)
3. **Comunicar ao time** os 3 P0 críticos para alinhamento de prioridades
4. **Backlog explícito** das limitações (item 1-10 acima) — viram items separados quando relevante

**Push do Replit:** decisão exclusiva Paulo (CLAUDE.md REGRA ABSOLUTA — nunca menciono).

---

**Fim do 04-ROADMAP_PRIORIZADO.md.**
**Auditoria profunda LIA WeDOTalent 2026-05-10 — concluída.**
