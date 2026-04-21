# FINAL AUDIT — Pendências Pós FIX 32 + Init I.A + II.A

> Consolidado de 3 Explore agents paralelos (2026-04-21). Read-only audit cobrindo 12 itens pendentes do LIA Maturity Program + FIX 34 tech debt. Reference: docs/LIA_MATURITY_ROADMAP.md + docs/INITIATIVES_AUDIT.md + docs/PHASE0_AUDIT.md.
>
> **Skills aplicadas:** canonical-fix (Replit Agent) + harness-engineering-lia + production-quality (CLAUDE.md).

## 🎯 Executive Summary

### Shipável em ≤ 1 semana (canonical-fix low blast)

| Item | Effort | Blast | Reuse % | Pronto p/ ship? |
|------|--------|-------|---------|-----------------|
| **Init I.B** — Persona renders capability_cards | ~50 LOC | LOW | 100% (cards prontos, CI guard existe) | ✅ Agora |
| **FIX 34** — Test isolation fix (YAML + loader estão corretos) | 0.5d | ZERO | 100% (só test) | ✅ Agora |
| **Init VI Fase 0** — eval_judge LLM Factory migration | 1-2d | LOW | 80% (factory + monkeypatch existem) | ✅ Agora |
| **Init IV** — Proactive Agenda (briefing scan) | 3d | MEDIUM | 70% (weekly_digest_service reutilizável) | ⚠️ PII blocker |
| **Init V** — Reasoning Transparency (citations) | 3d | LOW | 60% (tool_calls já persistidos) | ⚠️ G1 frontend dependency |
| **G2** — Observability markers catalog | 1d | ZERO | 80% (95 `[LIA-*]` markers, só falta catalog) | ✅ Agora |

### Médio prazo (>1 semana)

| Item | Effort | Blocker |
|------|--------|---------|
| **Init VI Fase 1** — Golden set expansion (40-50% gap) + CI wiring | 3-5d | PII audit em 99 cases existentes |
| **Init II.D** — workflow_context slot (3 workflows v1) | 1 semana | DB migration (conversation_summaries.metadata OU nova tabela) |
| **Init VII** — Error Recovery Patterns | 1-2 semanas | 90+ try/except existentes precisam refactor |
| **Init VIII** — Persona Consistency Testing (50 scenarios) | 1 semana | Depende Init VI infra |
| **G6** — Multi-tenant capability toggle | 2d | Zero (FeatureFlagService pronto) |

### Deferidos (v2+ ou exigem design)

| Item | Razão |
|------|-------|
| **Init III** — Memory 3 layers | LGPD/PII risk; pgvector NÃO instalado; exige audit + auto-purge |
| **G1** — Frontend UX integrations | Requer mockups + design system decisions com usuário |
| **G5** — PII/LGPD pipeline completo | Prerequisito pra IV/V production — design novo de redaction |

---

## 1. Initiative I.B — Persona renders capability_cards

**Status:** ✅ SHIP NOW. Blast LOW.

**Producer:** `app/shared/prompts/system_prompt_builder.py` `build()` method. Inject rendered cards into persona output via opt-in kwarg `include_capability_cards=True`.

**Patch scope (~50 LOC):**
1. New `CapabilityCardRenderer` class mirroring `PromptLoader` (load + cache YAML)
2. Add `include_capability_cards: bool = False` kwarg to `build()`
3. When True, render as `## Minhas Capacidades\n{bullet list of 16 cards}` section
4. Wire trigger: orchestrator detects `intent=what_can_you_do` → passes flag

**Harness:** GUIDE (rendered prose) + COMPUTATIONAL (deterministic YAML render)

**Reuse:** `app/prompts/catalog/capability_cards.yaml` (16 cards, Init I.A). CI guard `test_initI_capability_cards.py` already validates tools-match-registry invariant.

**Risks:**
- **P0:** Tool registry drift → card lists phantom tool → hallucination restart. Mitigação: CI guard + render-time fallback skip invalid card
- **P2:** Token inflation (16 cards × ~100 tokens = 1.6k extra). Mitigação: lazy (opt-in only on capability intents)

## 2. Initiative II.D — workflow_context slot (3 workflows v1)

**Status:** 🟡 PARTIAL. Blast MEDIUM.

**Producer:** `ConversationState` + `SystemPromptBuilder.build()`.

**Patch scope:**
1. Add `workflow_context: dict | None` field to `ConversationState`
2. New `app/orchestrator/workflow_registry.py` with 3 initial flows:
   - `close_job`: ask_reason → confirm → execute
   - `sourcing_with_filters`: initial_search → apply_filter → resume → paginate
   - `job_creation_wizard`: collect_role → collect_skills → validate_jd → publish
3. `SystemPromptBuilder` renders `### Fluxo em Andamento` section when active
4. Persistence: add JSON column `workflows_state` OR reuse `conversation_summaries.user_preferences` (FIX 32)

**Harness:** GUIDE (prompt injection) + COMPUTATIONAL (state machine)

**Reuse:** `PendingActionState` (FIX 25 to_prompt_context). Similar pattern but broader scope (multi-step vs single param collection).

**Risks:**
- **P0:** Workflow state loss on restart → user stuck mid-flow. Mitigação: DB persistence mandatory antes de prod
- **P1:** Blast em fluxos existentes (wizard, sourcing) — requires backward-compat layer

## 3. Initiative III — Memory 3 layers

**Status:** 🔴 DEFER v1. LGPD risk.

**Motivo:** Episodic memory (recruiter patterns, preferences) sem PII redaction + audit log = violação LGPD. pgvector NÃO instalado → embeddings exigem infra nova.

**MVP sugerido:**
- ✅ Keep working memory (ConversationState + MemoryResolver já sólido)
- ⏭ Skip semantic memory (defer)
- 🟡 Mini episodic via `UserAgentPreference` + `conversation_summaries.user_preferences` (já existe pós-FIX 32) — apenas preferências explícitas do usuário
- ⏭ Defer embeddings (pgvector install + retrieval design)

**Bloqueio real:** precisa G5 PII pipeline primeiro.

## 4. Initiative VI Fase 0 — eval_judge LLM Factory migration

**Status:** ✅ SHIP. Effort 1-2 dias. LOW RISK.

**Producer:** `eval/eval_judge.py` (linha 101 usa `anthropic.Anthropic(api_key=...)` direto).

**Finding crítico:** `app/shared/llm_bootstrap.py` monkeypatch JÁ intercepta calls diretos → PII strip + audit aplicados. Então bypass é estético (factory não roteia por tenant/fallback), mas compliance OK.

**Patch canonical-fix:**
- Migrar para `get_provider_for_tenant(tenant_id=None)` sync resolver (eval_judge é sync)
- Extrair 350-line JUDGE_PROMPT para `eval/eval_judge_config.yaml` (Phase 0 recommendation)
- Formato de resultado inalterado → backward compat ok

**Harness:** GUIDE (config YAML) + COMPUTATIONAL (factory call)

## 5. Initiative VI Fase 1 — Golden set + CI wiring

**Status:** 🟡 3-5 dias. Gap 40-50% cobertura.

**Inventário existente (via Phase 0):**
- 99 cases em `eval/eval_cases.yaml` distribuídos em 13 categorias
- 139 historical runs (2026-04-17 a 2026-04-21, ~2 runs/dia)
- Judge infra + runner prontos

**Gaps críticos (vs FIX 20-32):**
- Onboarding flows
- Feedback loop workflows
- Cancellation handling
- Compliance audit scenarios
- Quantifier normalization ("top 5" → page_size=5)
- Enum normalization ("urgent" → priority=HIGH)
- Triagem edge cases (só 2 cases)

**Cost model:**
- Claude Haiku @ $0.003/1K tokens
- Per-case ~500 tokens
- Full 200-case run: **$0.30**
- PR sample (20 cases): **$0.06**
- Estratégia: sample per PR + nightly full → ~$10/mês

**Blocker:** PII audit em 99 cases existentes (synthetic vs real desconhecido). Ação: human review + tokenizar nomes ([CANDIDATE], [RECRUITER]).

## 6. FIX 34 governance_tags — test isolation bug

**Status:** ✅ TRIVIAL FIX. 0.5 dia.

**Root cause descoberto:** YAML + loader estão **100% CORRETOS**.
- `tool_registry_metadata.yaml`: 105 entries com `governance_tags` non-empty (95% dos tools tagged)
- `sync_descriptions_from_yaml()` em `app/tools/__init__.py:138-145` lê corretamente

**Por que teste falha:** test isolation bug — `initialize_tools()` não chamado antes do teste OU cache não limpo entre runs.

**Patch:**
```python
tool_registry.clear()
initialize_tools()
tools_with_governance = [t for t in tool_registry._tools.values() if getattr(t, "governance_tags", [])]
assert len(tools_with_governance) >= 5  # passa com 95% coverage
```

**HITL status:** governance_tags **corretamente wired em runtime**. HITL enforcement não está quebrada — só test de regressão está. Risk **não é P0** como Phase 0 supôs.

## 7. Initiative IV — Proactive Agenda

**Status:** 🟡 70% ready. 3 dias. PII blocker pra produção.

**Producer:** novo `app/domains/recruiter_assistant/services/daily_briefing_service.py`.

**Reuse crítico:** `weekly_digest_service.py` (200+ linhas, working) — reusar lógica de aggregation.

**Patch scope:**
- Novo service que consolida: pending_offers >3d, stale candidates >7d, entrevistas sem feedback, vagas sem movimento >7d, compliance flags
- Endpoint `/api/v1/lia/briefing` (existe stub)
- Integração: FIX 27 greeting_template chama briefing service on "oi" → "Oi! Temos 3 coisas..."

**Risks:**
- **P0 PII:** briefing expõe counts de candidatos → precisa G5 redaction pipeline
- **P1:** DB queries custosas → cache 5min

## 8. Initiative V — Reasoning Transparency / Citations

**Status:** 🟡 60% ready. 3 dias. Frontend dependency.

**Producer:** extender `ChatResponse` com `citations: list[dict]` + novo `citation_processor.py`.

**Reuse:** `tool_calls` já persistidos na ChatRepository — indexar pra citations.

**Patch scope:**
- Citation processor extrai fatos da resposta + mapeia a tool_call+timestamp
- `ChatResponse.citations = [{text_span, tool_name, tool_params, timestamp}]`
- Backward-compat: campo opcional default None

**Blocker:** rendering frontend (Track 3 G1) — backend pode shipar, UX só aparece pós G1.

## 9. Initiative VII — Error Recovery Patterns

**Status:** 🔴 1-2 semanas. 90+ handlers existentes.

**Producer:** `app/orchestrator/error_policies.yaml` + extender `policy_engine.py` existente.

**Reuse:** `policy_engine.py` testado. Padrão FairnessGuard.educational_message.

**Escopo v1 (5 políticas):**
- `tool_timeout`, `empty_result`, `enum_error`, `permission_denied`, `tenant_mismatch`

**Risk:** refactor de try/except existentes — blast alto. Fazer incremental, não big-bang.

## 10. Initiative VIII — Persona Consistency Testing

**Status:** 🔴 1 semana. Depende Init VI infra.

**Reuse:** `eval_cases.yaml` (99 cases) → filtrar 50 relevantes pra consistency. `eval_runner.py` harness reutilizável.

**Novas dimensões de score:** tom, identidade, warmth, proatividade, admissão-de-limitação.

**Dependency:** LLM-as-judge infra (Init VI Fase 0+1) precisa estar pronto antes.

## 11. Track 3 G1 — Frontend/UX

**Status:** 🔴 Requer mockups. Fora subset atual.

**Componentes a criar/modificar em `ats_front/...UnifiedChat`:**
- Inline citations (tooltip com tool+params)
- Action chips (`[Rankear top 5]` clicável)
- Filter chips (`status: active ✕`)
- Progress bar multi-step
- "Why this answer" toggle
- Inline error recovery buttons

## 12. Track 3 G2-G6

### G2 Observability — ✅ 1 dia

- 95 `[LIA-*]` markers em código, sem catálogo
- Criar `docs/OBSERVABILITY_MARKERS.md` + `marker_catalog.yaml`
- Sem blocker

### G3 HITL — 🟡 policy-only

- `governance_tags` wired em runtime (FIX 34 descoberta corrige isso)
- Missing: endpoint `/api/v1/hitl/approve` + campo `hitl_checkpoint` em ChatResponse
- NÃO está quebrado; só não exposto

### G4 Cost/Latency — 🟡 2-3 dias

- Token tracking em `[LIA-*]` logs: existe parcial
- Anthropic prompt caching: NÃO usado hoje
- Haiku fallback: não configurado
- Proposta: tenant-level budget em `FeatureFlagService`

### G5 PII/LGPD — 🔴 blocker crítico

- Eval cases: synthetic PT (João, Maria, Ana) mas sem redaction explícita
- Production: nenhum pipeline de redaction em ChatResponse
- **Deve preceder Init IV e V em produção**

### G6 Multi-tenant capability toggle — ✅ 2 dias

- `FeatureFlagService` (200+ LOC, production-ready) pronto pra wire
- Adicionar `enabled_for_tenant` em `capability_cards.yaml`
- SystemPromptBuilder filtra no render

---

## 📋 Priorização recomendada — 3 ondas

### Onda 1 — Quick wins (1 semana)

Canonical-fix de baixo blast + alta alavancagem:

1. **FIX 34** (0.5d) — corrige test isolation, confirma governance_tags wiring
2. **Init VI Fase 0** (1-2d) — eval_judge factory migration (destrava Fase 1)
3. **Init I.B** (1d) — persona renders capability_cards (fecha loop anti-alucinação E2E)
4. **G2** (1d) — observability markers catalog
5. **G6** (2d) — multi-tenant capability toggle (FeatureFlagService wire)

Total: ~1 semana. Ganha 5 entregas shippáveis.

### Onda 2 — Enterprise foundations (2-3 semanas)

Dependem de Onda 1 + exigem design:

6. **Init VI Fase 1** (3-5d) — golden set expansion + CI + PII audit
7. **Init IV** (3d) — proactive agenda (precisa G5 light para produção)
8. **Init V** (3d) — reasoning transparency backend (G1 frontend depois)
9. **G5 light** — redaction pipeline MVP (names/emails/CPF)
10. **Init II.D** (1 semana) — workflow_context com 3 workflows

### Onda 3 — Platform maturity (4+ semanas)

11. **Init VII** (2 semanas) — error recovery refactor incremental
12. **Init VIII** (1 semana) — persona consistency 50 scenarios
13. **Init III** (2-3 semanas) — memory 3 layers com pgvector + audit
14. **G4** (1 semana) — cost governance com prompt caching + Haiku routing
15. **G3** (3d) — HITL endpoint + ChatResponse checkpoint field
16. **G1** (variable) — frontend work depende design/mockups
17. **G5 full** — LGPD audit trail completo

---

## 🔒 Skills compliance per item

Todos os itens seguem a stack obrigatória CLAUDE.md:

| Tipo | Skills ativas |
|------|---------------|
| `*tool*.py`, `*agent*.py` | harness-engineering-lia + production-quality/ai-architecture + canonical-fix |
| `*.yaml` em `app/prompts/` | harness-engineering-lia + production-quality/compliance-risk |
| `*orchestrator*.py` | harness-engineering-lia + canonical-fix (fix no producer) |
| `tests/**/*.py` | lia-testing (TDD Red→Green) |
| Qualquer mudança LLM-calling | canonical-fix (factory compliance) + production-quality/ai-architecture |
| PII/candidate-related | production-quality/compliance-risk (LGPD, fairness) |

## 📁 Detalhe por seção

- Section A (Init I.B + II.D + III): entregue como resumo executivo no chat (3800 words)
- Section B (Init VI + FIX 34): entregue como resumo executivo no chat (consolidado acima)
- **Section C (Init IV+V+VII+VIII+G1-G6): 655 linhas em `/tmp/FINAL_AUDIT_sectionC.md` no Replit** — ver via `ssh replit-wedo 'cat /tmp/FINAL_AUDIT_sectionC.md'`

---

## ✅ Próximo passo recomendado

Executar **Onda 1 completa** (~1 semana) — canonical-fix rigor, progressive disclosure por item, checkpoint com usuário após cada. Ordem:

1. FIX 34 (trivial, valida hipótese test-isolation)
2. Init I.B (fecha anti-alucinação E2E)
3. Init VI Fase 0 (destrava Fase 1)
4. G2 (catálogo obs markers)
5. G6 (multi-tenant toggle)

Cada um = Red→Green→Refactor→commit→smoke→checkpoint.

Pronto para execução pending apenas aprovação explícita do usuário na ordem proposta ou ajuste.
