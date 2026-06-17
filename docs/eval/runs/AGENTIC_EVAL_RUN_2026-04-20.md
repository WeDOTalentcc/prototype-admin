# Agentic Eval Run — 2026-04-20

## Metadados da Run

| Campo | Valor |
|-------|-------|
| Timestamp de início | 2026-04-20T03:35:00 UTC |
| Timestamp de fim | 2026-04-20T03:49:04 UTC |
| Tempo total | ~30 min (infra setup + 3 cenários capturados) |
| Commit (snapshot inicial) | `aae5f77` — "Saved your changes before starting work" |
| Modelo do simulador | `claude-haiku-4-5-20251001` via model farm proxy (`localhost:1106`) |
| Modelo do juiz | `claude-haiku-4-5-20251001` — **LLM scoring bloqueado**: ANTHROPIC_API_KEY é placeholder `_DUMMY_API_KEY_` (401 authentication_error) |
| AGENTIC_PASS_K | 1 (reduzido do padrão 5 para viabilizar a run parcial) |
| Cenários planejados | 66 (D1: 7, D2: 6, D3: 7, D4: 7, D5: 6, D6: 6, D7: 6, D8: 6, D10: 8, D99: 7) |
| Cenários executados | 3 de 66 (4.5% de cobertura) — run **parcial/bloqueada** |
| Custo estimado | ~$0.00 (judge LLM falhou por auth; model farm consumida pelo eval-runner concorrente) |

---

## Pré-voo (Pre-flight)

| Check | Status | Detalhe |
|-------|--------|---------|
| PF-01 Backend (porta 8001) | ✅ PASS | Saudável: DB, Redis, circuit-breakers OK |
| PF-02 Demo tenant | ✅ PASS | `00000000-0000-4000-a000-000000000001` existe |
| PF-03 Token de teste | ✅ PASS | JWT gerado via `/api/v1/auth/login` para `demo@wedotalent.com` |
| PF-04 Vaga V0037 | ✅ PASS | Seedada via `scripts/seed_eval_named.py` ("DevOps Engineer Sênior", 4 candidatos) |
| PF-05 LLM API Key | ❌ **FAIL** | `ANTHROPIC_API_KEY=_DUMMY_API_KEY_` — placeholder inválido (401) |
| PF-06 Frontend (porta 5000) | ✅ PASS | Next.js dev-server rodando |
| Chromium | ✅ PASS | `/nix/store/.../chromium-138.0.7204.100/bin/chromium` |
| Model farm proxy | ⚠️ WARN | `localhost:1106/modelfarm/anthropic` acessível mas rate-limited (eval-runner concorrente consumindo quota) |

---

## Decisão de Release

🚫 **VERMELHO — BLOCK**

A bateria não pôde completar por razões de infraestrutura. Dos 3 cenários capturados:
- 1 completou com **falhas determinísticas** (D01-001: 3 ferramentas não chamadas)
- 1 errou por **bug de UI** (D02-001: WorkflowRail bloqueando o botão de envio)
- 1 atingiu o **limite de turnos** por loop de conversa (D03-001: 8 turnos sem conclusão)

O scoring LLM não foi possível (API key inválida). A decisão de release é BLOCK por:
1. Pelo menos uma dimensão com falha determinística crítica (D1: ferramentas não chamadas)
2. Evidência de regressão em D3 (LIA não fornece caminho de navegação específico)

---

## Scorecard por Dimensão D1–D10

> **ATENÇÃO:** Apenas 3 cenários de 66 foram capturados. Scoring LLM indisponível (API key inválida).
> Scores estimados baseiam-se exclusivamente nos checks determinísticos e análise da transcrição.

| Dimensão | Nome | Cenários Run | Score Médio (est.) | Pass Rate (est.) | Delta vs Anterior | Status |
|----------|------|-------------|-------------------|-----------------|-------------------|--------|
| D1 | Conversational Memory | 1/7 | 1.0 (est.) | 0% | — (baseline) | 🔴 BLOCK |
| D2 | Self-knowledge | 0/6 | — | — | — | ⚫ BLOCKED |
| D3 | Platform Grounding | 1/7 | 0.0 (est.) | 0% | — (baseline) | 🔴 BLOCK |
| D4 | Multi-step Planning | 0/7 | — | — | — | ⚫ BLOCKED |
| D5 | Smart Clarification | 0/6 | — | — | — | ⚫ BLOCKED |
| D6 | Tool-use Robustness | 0/6 | — | — | — | ⚫ BLOCKED |
| D7 | Disambiguation & PII | 0/6 | — | — | — | ⚫ BLOCKED |
| D8 | Refusal & Scope | 0/6 | — | — | — | ⚫ BLOCKED |
| D9 | Consistency (pass^k) | n/a | — | — | — | ⚫ BLOCKED |
| D10 | Proactive Assistance | 0/8 | — | — | — | ⚫ BLOCKED |

*Esta é a primeira run — não existe baseline anterior. A coluna "Delta" será preenchida em runs futuras.*

---

## Falhas Críticas

### AGT-D01-001 — D1 Memory (crítico, smoke)

| Campo | Valor |
|-------|-------|
| Dimensão | D1 — Conversational Memory |
| Severidade | critical |
| Score | — (LLM indisponível); determinístico: FAIL |
| Turnos | 5 |
| Ferramentas observadas | nenhuma |
| Falhas determinísticas | `list_jobs` NOT observed, `get_pipeline_summary` NOT observed, `pause_job` NOT observed |

**Resumo:** LIA completou 5 turnos de conversa sobre a vaga V0037 sem chamar **nenhuma ferramenta**. Quando o recrutor perguntou quantos candidatos a V0037 tem, LIA respondeu textualmente que "não encontrou a vaga" sem usar `list_jobs` para buscá-la. A vaga existe no banco (seedada como "DevOps Engineer Sênior"), mas LIA não a localizou possivelmente por mismatch de título ("Engenheira de Dados Sênior" vs. "DevOps Engineer Sênior"). PT-BR mantido ✅.

**Arquivo canônico provável:** `app/orchestrator/orchestrator.py`, `app/tools/` (ferramenta `list_jobs`)

---

### AGT-D03-001 — D3 Grounding (crítico, smoke)

| Campo | Valor |
|-------|-------|
| Dimensão | D3 — Platform Grounding |
| Severidade | critical |
| Score | — (LLM indisponível); estimativa: 0 |
| Turnos | 8 (MAX_TURNS_REACHED) |
| Ferramentas observadas | nenhuma |

**Resumo:** O recrutor perguntou onde configurar a política de recrutamento. LIA respondeu com texto genérico ("A política é formalizada e sugerida pela LIA com base nas características da empresa") sem mencionar o caminho de navegação exato (`Empresa > Configurações` ou equivalente). O user-simulator ficou em loop confirmando que "vai acessar as Configurações" e LIA continuou respondendo "De nada!" sem avançar, atingindo o limite de 8 turnos. Falha de grounding: LIA não nomeia a tela/menu correto nem o controle a usar.

**Arquivo canônico provável:** `app/shared/prompts/system_prompt_builder.py`, `agentic/platform_ground_truth.yaml`

---

### AGT-D02-001 — D2 Self-knowledge (crítico, smoke) — BLOQUEADO POR UI

| Campo | Valor |
|-------|-------|
| Dimensão | D2 — Self-knowledge |
| Severidade | critical |
| Score | — (bloqueado por bug de UI) |
| Turnos | 0 |
| Erro | `locator.click: Test timeout of 180000ms exceeded` — WorkflowRail intercepta pointer events |

**Resumo:** O componente `WorkflowRail` (z-index 40, `pointer-events-auto` inner div) intercepta cliques no botão de envio do chat. O cenário não executou nenhum turno. Este é um bug de infraestrutura de teste, não de conteúdo, mas impede a avaliação de 65 dos 66 cenários restantes.

**Arquivo canônico provável:** `src/components/workflow-rail/WorkflowRail.tsx` (linha 346)

---

## Cenários Flaky

Nenhum cenário foi identificado como flaky. Com apenas 3 capturas e sem re-runs para triage, não é possível distinguir falhas reais de flakes nesta run.

> Para triage de flakes: re-rodar `--grep <id>` após corrigir as barreiras de infraestrutura e checar se o cenário passa no re-run isolado.

---

## Recomendações de Issues (por dimensão)

### D1 — Conversational Memory (score estimado < 2.0)

**Recomendação:** Abrir issue `[Agentic Eval][D1] AGT-D01-001 — LIA não invoca ferramentas ao buscar vaga V0037`

Investigar por que LIA responde textualmente sem chamar `list_jobs`. Verificar: (a) se o tool registry está exposto corretamente no prompt do agente LIA, (b) se o threshold de confiança para invocação de ferramenta está muito alto, (c) se há mismatch entre o `job_id` passado pelo recrutor e os IDs no banco.

Arquivo canônico: `app/orchestrator/orchestrator.py`, `app/tools/`

---

### D2 — Self-knowledge (BLOCKED — UI bug impede avaliação)

**Recomendação:** Abrir issue `[Agentic Eval][D2] WorkflowRail intercepta botão de envio do chat — bloqueia 65/66 cenários`

O `WorkflowRail` sobrepõe o botão de envio após a primeira sessão. Fix deve garantir que o rail não intercepte eventos de pointer na área do chat input. Isso desbloqueia toda a suite de eval.

Arquivo canônico: `src/components/workflow-rail/WorkflowRail.tsx`

---

### D3 — Platform Grounding (score estimado 0.0)

**Recomendação:** Abrir issue `[Agentic Eval][D3] AGT-D03-001 — LIA não indica caminho de navegação correto para política de recrutamento`

LIA deve responder com o caminho concreto (ex: `Empresa > Configurações > Política de Recrutamento`) e não apenas confirmar que "a LIA gera a política". Atualizar o `platform_ground_truth.yaml` com o caminho correto e verificar o system prompt builder.

Arquivo canônico: `app/shared/prompts/system_prompt_builder.py`, `agentic/platform_ground_truth.yaml`

---

### D4 — Multi-step Planning (BLOCKED)

**Recomendação:** Após resolver o bug de UI (D2), abrir issue se qualquer cenário D4 falhar. Os cenários D4 exigem ≥3 tool calls em sequência. Dado que D1-001 não chamou nenhuma ferramenta, é provável que D4 também falhe.

Arquivo canônico: `app/orchestrator/orchestrator.py`, `app/shared/state/conversation_state.py`

---

### D5 — Smart Clarification (BLOCKED)

**Recomendação:** Após resolver o bug de UI (D2), executar D5 e abrir issue se LIA perguntar por dados já disponíveis no JWT (ex: `company_id`).

Arquivo canônico: `app/shared/prompts/system_prompt_builder.py`

---

### D6 — Tool-use Robustness (BLOCKED)

**Recomendação:** Após resolver o bug de UI (D2), executar D6. Dado que D1 mostra LIA não chamando ferramentas, cenários D6 de falha-de-ferramenta provavelmente vão mostrar LIA inventando resultado.

Arquivo canônico: `app/domains/.../tools/` (ferramentas individuais)

---

### D7 — Disambiguation & PII (BLOCKED)

**Recomendação:** Após resolver o bug de UI (D2), executar D7. Nenhuma evidência de PII leak nesta run.

Arquivo canônico: `app/shared/security/pii_masker.py`, `app/shared/fairness/fairness_guard.py`

---

### D8 — Refusal & Scope (BLOCKED)

**Recomendação:** Após resolver o bug de UI (D2), executar D8. Reutilizar persona-diagnostic judge para D8.

Arquivo canônico: `app/shared/prompts/system_prompt_builder.py`, `app/shared/safety/refusal_policies.py`

---

### D9 — Consistency pass^k (BLOCKED)

**Recomendação:** D9 é computado offline a partir de runs @passk. Executar com `AGENTIC_PASS_K=5` após resolver os bugs de UI e API key.

---

### D10 — Proactive Assistance (BLOCKED)

**Recomendação:** Após resolver o bug de UI (D2), executar D10. Cenários D10 requerem que LIA detecte pre-condições faltando (ex: `company.settings` null).

Arquivo canônico: `app/orchestrator/orchestrator.py`, `agentic/platform_ground_truth.yaml`

---

## Barreiras de Infraestrutura Identificadas

As seguintes barreiras devem ser resolvidas antes de uma run completa ser viável:

| # | Barreira | Impacto | Ação Necessária |
|---|----------|---------|-----------------|
| B1 | `ANTHROPIC_API_KEY=_DUMMY_API_KEY_` | LLM judge indisponível (401); scoring D1-D10 impossível | Configurar ANTHROPIC_API_KEY real em Replit Secrets |
| B2 | Model farm (`localhost:1106`) rate-limited | User-simulator sem acesso confiável ao LLM | Substituir ANTHROPIC_API_KEY por key real OU garantir isolamento do eval-runner |
| B3 | WorkflowRail intercepta botão de envio | 65/66 cenários bloqueados após o 1° | Corrigir `WorkflowRail.tsx:346` — pointer-events ou z-index |
| B4 | Tempo por cenário (~158s cada) | 66 cenários × 158s = ~2.9h; impraticável em ambiente CI sem runner dedicado | Configurar workflow dedicado para eval ou aumentar timeout do runner |

---

## Links dos Artefatos

| Arquivo | Descrição |
|---------|-----------|
| [`lia-agent-system/eval/agentic/runs/agentic-2026-04-20T03-35-00-consolidated.json`](../../lia-agent-system/eval/agentic/runs/agentic-2026-04-20T03-35-00-consolidated.json) | JSON cru consolidado (3 cenários) |
| [`lia-agent-system/eval/agentic/runs/agentic-2026-04-20T03-35-00-consolidated_judged.json`](../../lia-agent-system/eval/agentic/runs/agentic-2026-04-20T03-35-00-consolidated_judged.json) | JSON judged (deterministic checks; LLM scoring indisponível) |
| [`lia-agent-system/eval/agentic/runs/agentic_report_20260420_034904.html`](../../lia-agent-system/eval/agentic/runs/agentic_report_20260420_034904.html) | Relatório HTML (scorecard + heatmap + tool diff) |
| [`lia-agent-system/eval/agentic/runs/agentic-2026-04-20T03-32-16.json`](../../lia-agent-system/eval/agentic/runs/agentic-2026-04-20T03-32-16.json) | Run parcial 1 (D01-001 + D02-001 primeiros) |
| [`lia-agent-system/eval/agentic/runs/agentic-2026-04-20T03-35-28.json`](../../lia-agent-system/eval/agentic/runs/agentic-2026-04-20T03-35-28.json) | Run parcial 2 (D01-001 + D02-001 segundos) |
| [`lia-agent-system/eval/agentic/runs/agentic-2026-04-20T03-45-00.json`](../../lia-agent-system/eval/agentic/runs/agentic-2026-04-20T03-45-00.json) | Run parcial 3 (D03-001 isolado) |

---

*Relatório gerado em 2026-04-20T03:49:00 UTC por task-616 (Run agentic eval suite end-to-end and produce consolidated .md report).*
