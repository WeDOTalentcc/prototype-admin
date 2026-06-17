# LIA Maturity Roadmap

> **Source of truth** para o programa de maturidade da LIA iniciado em 2026-04-21 após auditoria adversarial de conversa real (25+ turns) mostrando bugs de tooling, prompt/persona e state management além de gaps de produto (explainability, eval, HITL, observability).
>
> Este doc substitui relatórios ad-hoc e é o tracker canônico. Atualizar checkboxes a cada PR merged.

---

## Princípios não-negociáveis

1. **Canonical-fix** (Replit agent skill): todo bug fixa no producer, nunca workaround no consumer, nunca silent fallback.
2. **Harness engineering** (`~/.claude/skills/harness-engineering-lia`): toda intervenção classificada em guide × sensor × computacional × inferencial. Preferir computacional sempre que factível.
3. **Progressive disclosure**: cada FIX/Initiative é unidade atômica (TDD Red→Green→Refactor→smoke→commit→checkpoint). Nunca empilhar sem validação do usuário.
4. **Commit limpo**: 1 commit por FIX/Initiative com mensagem que descreve honestamente o escopo — lição de PARTE L (auto-checkpoint camuflado).
5. **Doc freshness**: nenhum `.md` consumido como spec sem validação de staleness (ver Phase 0).
6. **LGPD/fairness**: toda mudança que toca candidato/calibração/empresa passa por `production-quality/compliance-risk`.

---

## Stack de skills por tipo de arquivo

| Tipo de arquivo | Skills obrigatórias |
|-----------------|---------------------|
| `*tool*.py`, `*agent*.py` | harness-engineering-lia + production-quality/ai-architecture + canonical-fix |
| `*.yaml` em `app/prompts/` | harness-engineering-lia + production-quality/compliance-risk |
| `*orchestrator*.py` | harness-engineering-lia + canonical-fix |
| `tests/**/*.py` | lia-testing (TDD) |
| Novo tool | harness-engineering-lia + production-quality/integration-patterns |
| PII/candidate-related | production-quality/compliance-risk (LGPD/fairness) |

---

## Phase 0 — Discovery exaustiva (PRÉ-REQUISITO)

Antes de qualquer FIX, produzir `docs/PHASE0_AUDIT.md` contendo:

### 0.1 Inventário (o que já existe no Replit)

- [ ] Golden sets / eval conversations (`eval/`, `tests/evals/`, `tests/golden/`, `tests/fixtures/conversations/`)
- [ ] Test fixtures (padrões TDD vigentes, FIX 1-19)
- [ ] Capability docs (`app/prompts/`, `docs/`, local `LIA_AI_LAYER_CAPABILITIES.md`, `LIA_AGENTS_DETAILED.md`)
- [ ] Tool registry completo (`app/tools/`, `app/domains/*/tools/`, glossary auto-gen)
- [ ] Prompt blocks (`shared/*.yaml`, `domains/*.yaml`)
- [ ] Eval results históricos (`eval/eval_results_*.json`)
- [ ] HITL / governance (`governance_tags`, FairnessGuard, compliance_base)
- [ ] Telemetry markers (`[LIA-*]` logs, tool_metrics)

### 0.2 Doc Freshness Matrix (crítico)

Classificar cada `.md` relevante em 3 tiers:

- **T1 Canônico** — auto-gerado ou push recente no branch canônico → trust
- **T2 Humano mantido** — fact-check antes de consumir
- **T3 Suspeito/legado** — read-only, validar cada afirmação

**Docs sinalizados pelo usuário para classificação explícita:**

| Doc | Local | Tier presumido | Ação |
|-----|-------|----------------|------|
| Tool/action canonical guide | GitHub `wedotalent02202026` branch `replit-sync` | T1 | Baixar, diff vs registry, declarar source of truth |
| Glossary auto-gen output | lia-agent-system | T1 | Re-rodar, comparar |
| `LIA_AI_LAYER_CAPABILITIES.md` | local Mac | T3 | Fact-check vs tool registry; se stale, archive |
| `LIA_AGENTS_DETAILED.md` | local Mac | T3 | Validar vs `app/agents/`; se stale, archive |
| `LIA_REFACTORING_REPORT.md` | local Mac | T3 histórico | Read-only |
| `ARCHITECTURE*.md` | local | T3 | Preferir código |
| `DEVELOPER_HANDOFF.md` | Replit | T2 | Trust com verificação |
| `CANONICAL_SOURCES_SPEC.md` | local | T2 | Validar post-FIX 13 |

**Fact-check protocol por doc T2/T3:**
1. `git log -1 --format="%ci %s" -- <path>` → quando mexido?
2. Grep afirmações factuais (tool names, endpoints, flags) vs código
3. ≥ 1 stale → marcar ⚠️ STALE + não usar como spec
4. Stale recuperável → replacement pela versão canônica
5. Obsoleto → archive em `docs/archive/` com sticker "do not consume"

### 0.3 Deliverable

`docs/PHASE0_AUDIT.md` contendo: inventário + freshness matrix + gap analysis + decisão de reuso + riscos + baseline métricas + **canonical source resolution** (qual fonte é canônica para cada tipo de informação daqui pra frente).

**Gate:** NÃO começa Track 1 sem esse doc aprovado pelo usuário.

---

## TRACK 1 — FIX tácticos (bug-fix sprint da conversa-base)

Resolve os sintomas observados no chat real pastado pelo usuário. Cada FIX: TDD Red→Green, regression total (145/145 atual + novos), smoke real no chat pós-restart.

### Fase A — P0 blockers

- [ ] **FIX 20** — Pagination em `search_jobs`
  - Root: `app/domains/job_management/tools/query_tools.py:48,124` (hardcoded limit=20)
  - Mudança: +`offset`, +`total_count` no retorno; persona diz "mostrando 20 de N"
  - Test: cobertura para `limit+offset`, `total_count` exato

### Fase B — P1 tooling

- [ ] **FIX 21** — `list_message_templates()` + `preview_template(template_id)`
  - Root: `app/domains/communication/tools/communication_tools.py` (missing tool)
  - Reuse: `generate_candidate_feedback` com `preview=True`

- [ ] **FIX 22** — Enum normalizer PT→EN em `close_job.reason`
  - Root: `job_tools.py:366-378` aceita enum mas sem translation layer
  - Mudança: `_PT_ENUM_MAP` OU orchestrator coerce pré-call

- [ ] **FIX 24** — Remover capacidades alucinadas da persona
  - Root: `lia_persona.yaml` + `recruiter_assistant.yaml` mencionam "prever", "conversão entre etapas" sem tool
  - Teste regression: `test_no_hallucinated_capabilities.py` (parse YAML, cross-ref registry)

### Fase C — P1 prompt+state

- [ ] **FIX 23** — Generalizar FIX 17 `capability_truthfulness` para open-ended discovery
  - Root: `guardrails_block.yaml:33-45` fira só em tool específico, não em "o que sabe fazer?"
  - Mudança: sub-bloco `open_ended_discovery` + `app/prompts/catalog/capability_cards.yaml` (vem completo da Initiative I)

- [ ] **FIX 25** — Injeção de `pending_action` + `collected_params` no system prompt
  - Root: `main_orchestrator.py:1411` `_extract_param_value()` raw + PendingActionState.collected_params não re-injetado
  - Mudança: bloco estruturado `## CONTEXTO DE AÇÃO PENDENTE` antes de `llm_cascade.run()`

- [ ] **FIX 26** — Quantifier patterns + contextual inference rule
  - Root: `memory_resolver.py:151` sem quantifiers; `lia_persona.yaml` sem `contextual_inference`
  - Mudança: `_QUANTIFIER_PATTERNS` regex + nova regra persona (resposta 1-2 palavras = continuação)

### Fase D — P2 polish

- [ ] **FIX 27** — Greeting template dinâmico (Sierra-style)
  - Root: `lia_persona.yaml:140-142` fallback one-liner
  - Mudança: template "Oi {user}! ... {n_vagas_abertas}... Por onde começamos?" + SystemPromptBuilder reuse

- [ ] **FIX 28** — Filter state + proatividade de dados
  - Root: `ConversationState` sem `active_filters`; `recruiter_assistant.yaml` sem `proatividade_dados`
  - Mudança: slot + regra "nunca dizer 'você gostaria de navegar'"

### Fase E — Continuous

- [ ] Eval set mínimo (30 conversas sintéticas cobrindo FIX 20-28)
- [ ] CI guard: `scripts/check_capability_drift.py` (parseia YAMLs vs tool registry)

**Smoke test consolidado (pós Fase D):** reproduzir os 25+ turns da conversa-base e validar cada bug da tabela de sintomas está closed.

---

## TRACK 2 — Programa de Maturidade Enterprise

Transforma LIA em produto enterprise-grade (Sierra/Glean/Fin level). Priorização sugerida: **I + II + VI** como trio de maior alavancagem.

### Initiative I — Grounded Capability System

- [ ] Schema `app/prompts/catalog/capabilities/*.yaml` — cards {id, title, user_phrasing[], tools[], example_input, example_output, preconditions[], success_metric}
- [ ] Renderer: persona lista capabilities por render de cards (não prosa)
- [ ] CI guard: cada capability mapeia ≥1 tool real
- [ ] Doc recruiter: "aqui está tudo que LIA faz, com exemplos"

### Initiative II — Structured State Machine (Rasa/LangGraph-style)

- [ ] 4 slots formais em `ConversationState`:
  - `pending_action` (tool+collected_params+missing_params)
  - `active_filters` (sticky)
  - `last_entity` ({type, id} pra pronouns/refs)
  - `workflow_context` (fluxo multi-turn)
- [ ] Injeção determinística dos 4 slots no system prompt a cada turn (não via history)

### Initiative III — Conversational Memory (3 camadas)

- [ ] Working memory (parcial hoje via MemoryResolver)
- [ ] Semantic memory (tenant-level: setor, processo, benefícios, tom) via embeddings
- [ ] Episodic memory (preferências do recruiter aprendidas por conversa)
- [ ] Infra: pgvector + retrieval

### Initiative IV — Proactive Agenda System

- [ ] `briefing_scan` na abertura de sessão: ofertas pendentes, candidatos stale, entrevistas sem feedback, vagas sem movimento, compliance flags
- [ ] Greeting vira "Oi X! Temos 3 coisas pra olhar..." (Sierra/Fin pattern)

### Initiative V — Reasoning Transparency / Explainability

- [ ] Inline citations por resposta factual (tool+params+timestamp)
- [ ] UI tooltip "why this answer"
- [ ] Chain-of-thought toggle

### Initiative VI — Continuous LLM-as-Judge Eval

- [ ] Golden set 100-200 conversas (sourcing, triagem, feedback, cancelamento, compliance, onboarding, edge cases)
- [ ] Judge (Claude Sonnet) scoring: grounding, clarity, actionability, tone, safety
- [ ] Trigger: cada PR em `app/prompts/` ou `app/orchestrator/`
- [ ] Dashboard drift ao longo do tempo

### Initiative VII — Error Recovery Patterns

- [ ] `app/orchestrator/error_policies.yaml` — catálogo determinístico de respostas a falhas
- [ ] Cobertura mínima: tool_timeout, empty_result, enum_error, permission_denied, tenant_mismatch

### Initiative VIII — Persona Consistency Testing

- [ ] Suite 50 cenários (identity, warmth, proatividade, limitação, tom)
- [ ] Scoring via LLM-as-judge + snapshot testing

---

## TRACK 3 — Dimensões transversais (G1-G6)

### G1 — Frontend/UX integrations

- [ ] Audit componentes atuais do chat (`ats_front/.../UnifiedChat`)
- [ ] Render structured data: inline citations (tooltip), action chips, filter chips, progress bar, "why this answer"
- [ ] Inline error recovery ([retry], [ajustar filtro])

### G2 — Observability / Telemetry

- [ ] Métricas por turn: `tool_call_count`, `tool_latency_p50/p95`, `hallucination_flag`, `clarification_spam_rate`, `action_success_rate`, `user_follow_up_rate`
- [ ] Dashboard Grafana/Metabase + alertas de drift

### G3 — Human-in-the-Loop

- [ ] Audit: quais tools com `governance_tags: [destructive, external_comms]` têm HITL real vs só tag
- [ ] Preview bloqueante + confirmação + audit trail imutável em `close_job`, `send_feedback`, `publish_job`

### G4 — Cost / Latency governance

- [ ] Token budget por turn (warn if > N)
- [ ] Cost dashboard por tenant
- [ ] Cache de prompt sections estáveis (capability catalog)
- [ ] Haiku fallback em turns simples

### G5 — PII / LGPD em evals, logs, memory

- [ ] Pipeline redaction automática (CPF, email, telefone, nomes)
- [ ] Synthetic personas para golden set público
- [ ] Retention policy (eval_results_*.json não indefinido no repo)

### G6 — Multi-tenant capability toggle

- [ ] Capability cards com flag `enabled_for_tenant: default_on | default_off | gated_by_plan`
- [ ] Persona render filtra runtime
- [ ] Discussão de pricing/packaging

---

## Roadmap temporal (6 semanas)

| Semana | Foco | Entregáveis |
|--------|------|-------------|
| 0 | Phase 0 | PHASE0_AUDIT.md, freshness matrix, canonical source resolution |
| 1 | Track 1 A+B | FIX 20 + 21 + 22 + 24 |
| 2 | Track 1 C+D+E | FIX 23 + 25 + 26 + 27 + 28 + eval mínimo + CI guard |
| 3 | Track 2 I+II | Capability catalog + state machine |
| 4 | Track 2 III+IV | Memory layers + proactive agenda |
| 5 | Track 2 V+VI | Explainability + eval harness completo |
| 6 | Track 2 VII+VIII + Track 3 | Error policies + persona suite + G1-G6 priorizados |

Cada fase = commit separado, restart uvicorn, smoke real, checkpoint com usuário.

---

## Ponto em aberto (requer curadoria do usuário)

**G1 UI/UX design** — inline citations, action chips, filter chips, "why this answer" exigem mockups antes de implementação. Sem isso, estimativa firme não é honesta.

---

## Histórico do documento

- **2026-04-21** (criação): pós audit adversarial + FIX 19 + Tasks A+B+C. Usuário validou plano com Phase 0 + 3 tracks + 6 gaps.

---

## Tracker global

**Status atual:** Phase 0 pendente (gate para Track 1)

- [ ] Phase 0 — Discovery + freshness matrix
- [ ] Track 1 Fase A (FIX 20)
- [ ] Track 1 Fase B (FIX 21/22/24)
- [ ] Track 1 Fase C (FIX 23/25/26)
- [ ] Track 1 Fase D (FIX 27/28)
- [ ] Track 1 Fase E (eval + CI)
- [ ] Initiative I (Capability Catalog)
- [ ] Initiative II (State Machine)
- [ ] Initiative III (Memory)
- [ ] Initiative IV (Proactive Agenda)
- [ ] Initiative V (Explainability)
- [ ] Initiative VI (Eval Harness)
- [ ] Initiative VII (Error Policies)
- [ ] Initiative VIII (Persona Suite)
- [ ] G1 Frontend/UX
- [ ] G2 Observability
- [ ] G3 HITL
- [ ] G4 Cost governance
- [ ] G5 PII/LGPD
- [ ] G6 Multi-tenant toggle
