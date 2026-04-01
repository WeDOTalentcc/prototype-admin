# Auditoria do Guia de Migração v5 → Compliance (v2.2)

> **Auditor:** Agent | **Data:** 2026-04-01
> **Arquivo auditado:** `WeDO/guias/GUIA_MIGRACAO_V5_COMPLIANCE.md` (3307 linhas, v2.2)
> **Fontes de verificação:**
> - GitHub: `WeDOTalent/recruiter_agent_v5` (repo v5)
> - Replit: `lia-agent-system/` (repo LIA)

---

## Erro Fundamental — Premissa Falsa (Linha 98)

O guia afirma:

> "O v5 e a LIA são o **mesmo codebase** (`lia-agent-system`). O que chamamos de 'v5' são os patterns antigos (Flat/keyword/hardcoded) e a 'LIA' são os patterns novos (ReAct/LLM/YAML) — coexistem no mesmo repositório."

**ISTO É FALSO.** São repositórios completamente separados:

| | v5 | LIA |
|---|---|---|
| **Repo** | `WeDOTalent/recruiter_agent_v5` (GitHub) | `lia-agent-system` (Replit) |
| **Framework** | Sync (`psycopg2`, Celery, RabbitMQ) | Async (`SQLAlchemy asyncio`, FastAPI) |
| **Workflow** | `DomainState` (TypedDict, LangGraph `StateGraph`) | `WorkflowState` (dataclass, async pipeline) |
| **Router** | `DomainOrchestrator` → `DomainWorkflow` (LangGraph) | `CascadedRouter` (6 tiers) → `DomainWorkflow` (async) |
| **Audit** | `psycopg2` direto, `ON CONFLICT DO UPDATE SET` | `SQLAlchemy async`, `ON CONFLICT DO NOTHING` |
| **Base class** | `DomainPrompt` com `ActionType` enum | `DomainPrompt` (ABC) sem `ActionType` |

Este erro fundamental contamina sistematicamente todas as seções do guia, causando atribuições incorretas de componentes LIA ao v5.

---

## Inventário de Erros por Problema

### E1 — P2: `_pre_check`/`_post_check` atribuídos ao v5

**Guia diz (L106):** "`DomainWorkflow._pre_check` aplica FairnessGuard automaticamente"
**Guia diz (L141):** "Compliance roda em `_pre_check` (antes) e `_post_check` (depois)"

**Realidade:**
- **v5** `src/domains/workflow.py`: Usa `DomainState` (TypedDict) + `StateGraph` com nós `DomainIntentAgent.analyze`, `DomainActionExecutor.execute`, `DomainAnswerFormatter.format`. **NÃO tem `_pre_check` nem `_post_check`.**
- **LIA** `app/domains/workflow.py`: Tem `_pre_check` (L226-256) que chama `FairnessGuard.check()` e `_post_check` (L437-467) que chama `FactChecker.check_response()`.

**Correção:** P2 e P5 devem dizer que `_pre_check`/`_post_check` são **LIA-only**. O v5 não tem compliance automática no workflow.

---

### E2 — P3.a: Arquivo errado e diagnóstico invertido

**Guia diz (L116):** "`ON CONFLICT DO UPDATE` em `libs/audit/lia_audit/audit_callback.py`"

**Realidade:**
- **v5** `src/services/audit/audit_writer.py`: Usa `ON CONFLICT (execution_id) DO UPDATE SET` — **este é o bug real**
- **LIA** `libs/audit/lia_audit/audit_writer.py` (L80): Usa `ON CONFLICT (execution_id) DO NOTHING` — **já corrigido**
- **LIA** `libs/audit/lia_audit/audit_callback.py`: É um callback handler (LangChain `BaseCallbackHandler`), não contém SQL

**Correção:** O bug está em **v5** `src/services/audit/audit_writer.py` (usa `DO UPDATE SET`). A LIA já usa `DO NOTHING` em `libs/audit/lia_audit/audit_writer.py`. O guia aponta o arquivo errado e inverte quem tem o bug.

---

### E3 — P3.b: `LangGraphReActBase` atribuído ao v5

**Guia diz (L124):** "adicionar `strip_pii_for_llm_prompt` no `LangGraphReActBase` antes de montar o prompt"

**Realidade:**
- `LangGraphReActBase` é **LIA-only** (`libs/agents-core/`)
- v5 tem `pii_filter.py` em `src/services/pii_filter.py` com `mask_pii()` e `PIIMaskingFilter` para logging
- v5 não tem `LangGraphReActBase`

**Correção:** A solução proposta é válida para LIA, mas o guia deve distinguir: v5 já tem PII masking para logs, LIA precisa expandir para prompts via `LangGraphReActBase`.

---

### E4 — P3.c: FactChecker no `_post_check` atribuído ao v5

**Guia diz (L126-129):** "FactChecker no `DomainWorkflow._post_check` [...] Já é **global** via workflow"

**Realidade:**
- v5 FactChecker existe **somente** em `src/domains/sourced_profile_sourcing/fact_checker.py` — local ao sourcing
- LIA FactChecker é global em `app/shared/compliance/fact_checker.py` e chamado no `_post_check` do `DomainWorkflow`
- v5 `DomainWorkflow` (LangGraph StateGraph) NÃO chama FactChecker

**Correção:** FactChecker global via `_post_check` é LIA-only. No v5, FactChecker é local ao sourcing.

---

### E5 — P4: Arquivos de FairnessGuard errados

**Guia diz (L131):** "FairnessGuard importado direto em `sourcing_react_agent.py` (L151), `policy_react_agent.py`, `pipeline_tool_registry.py` (L513)"

**Realidade:**
- `sourcing_react_agent.py`, `policy_react_agent.py`, `pipeline_tool_registry.py` são **arquivos LIA** (em `lia-agent-system/app/agents/`)
- v5 FairnessGuard está em:
  - `src/domains/jobs/fairness.py` → classe `JobFairnessGuard` com `BLOCKED_FILTERS` e `check_filters()`
  - `src/domains/sourced_profile_sourcing/fairness.py` → classe mais elaborada com `SensitiveAttribute` enum, `FairnessMetrics`
- v5 NÃO tem `sourcing_react_agent.py` nem `policy_react_agent.py`

**Correção:** Substituir referências a arquivos LIA pelos arquivos v5 reais.

---

### E6 — P5: `_pre_check`/`_post_check` novamente atribuídos ao v5

**Guia diz (L141-144):** "Compliance roda em `_pre_check` (antes) e `_post_check` (depois) [...] Gap: **durante** o processamento"

**Realidade:** Mesmo erro que E1. v5 não tem `_pre_check`/`_post_check`. O gap no v5 é muito pior: não há compliance **em nenhum ponto** do workflow (exceto FairnessGuard local no sourcing e jobs).

---

### E7 — P8: `ActionExecutorService` e `_KEYWORD_ACTION_MAP` atribuídos ao v5

**Guia diz (L177):** "`ActionExecutorService` em `action_executor.py` com `ACTIONABLE_INTENTS`"
**Guia diz (L180):** "os `_KEYWORD_ACTION_MAP` em cada `domain.py` podem ser removidos"

**Realidade:**
- v5 NÃO tem `ActionExecutorService` nem `_KEYWORD_ACTION_MAP`
- v5 usa `_CONTEXT_ACTION_PATTERNS` (lista de tuplas `(regex, action_id)`) em `src/domains/jobs/domain.py`
- `ActionExecutorService` é LIA-only

**Correção:** Referir `_CONTEXT_ACTION_PATTERNS` em vez de `_KEYWORD_ACTION_MAP`.

---

### E8 — P9.a: `_KEYWORD_ACTION_MAP` inexistente no v5

**Guia diz (L192):** "`_KEYWORD_ACTION_MAP` em cada `domain.py` — `analytics/domain.py` (L11-113), `interview_scheduling/domain.py` (L19-128)"

**Realidade:**
- v5 NÃO tem `_KEYWORD_ACTION_MAP`
- v5 usa `_CONTEXT_ACTION_PATTERNS` (somente em `jobs/domain.py` confirmado)
- `analytics/domain.py` e `interview_scheduling/domain.py` referem-se a domínios LIA

**Correção:** Substituir por `_CONTEXT_ACTION_PATTERNS`.

---

### E9 — P9.b: `NEGATION_DETECTION_BLOCK` e `interaction_patterns.py` atribuídos ao v5

**Guia diz (L197):** "`NEGATION_DETECTION_BLOCK` em `interaction_patterns.py` já existe como bloco injetável"

**Realidade:**
- v5 NÃO tem `interaction_patterns.py` nem `NEGATION_DETECTION_BLOCK`
- Estes são componentes LIA

**Correção:** Clarificar que são LIA-only; v5 não tem detecção de negação.

---

### E10 — P11: `PromptRegistry`, `PromptLoader`, YAMLs atribuídos ao v5

**Guia diz (L232):** "`PromptRegistry` + `PromptLoader` + 10 YAMLs de domínio"
**Guia diz (L242):** "`few_shot_examples.py` com categorias"
**Guia diz (L247):** "`ANTI_SYCOPHANCY_BLOCK`, `CHAIN_OF_THOUGHT_BLOCK`, `NEGATION_DETECTION_BLOCK`, `DEFENSIVE_BLOCK` em `interaction_patterns.py`"

**Realidade:**
- v5 NÃO tem `PromptRegistry`, `PromptLoader`, `few_shot_examples.py`, `interaction_patterns.py`
- v5 usa prompts hardcoded em `prompts.py` dentro de cada domínio
- Todos esses componentes são LIA-only

**Correção:** Clarificar que v5 usa prompts hardcoded; esses componentes existem na LIA e devem ser adotados.

---

### E11 — P12: `ToolRegistry` e `tool_registry_metadata.yaml` ambíguos

**Guia diz (L267):** "`ToolRegistry` em `registry.py` + metadata YAML"

**Realidade:**
- v5 tem `src/domains/registry.py` (DomainRegistry, não ToolRegistry)
- v5 domínios usam `prompt_builder/action_registry.py` por domínio
- LIA tem ToolRegistry separado

---

### E12 — Tabela de cobertura (L373-386) atribui audit a `src/services/audit/`

**Guia diz (L384):** "audit_callback existe em src/services/audit/ mas é mutável (ON CONFLICT DO UPDATE)"

**Realidade:** Parcialmente correto para v5 (`src/services/audit/audit_writer.py` usa `DO UPDATE`). Mas o guia confunde com `audit_callback.py` que na LIA é um callback handler sem SQL.

---

## Resumo de Impacto

| Categoria | Contagem | Gravidade |
|-----------|----------|-----------|
| Premissa falsa (mesmo codebase) | 1 | **Crítica** — contamina todo o documento |
| Arquivos LIA atribuídos ao v5 | 8 | **Alta** — causa confusão na migração |
| Componentes LIA inexistentes no v5 | 7 | **Alta** — ações propostas impossíveis no v5 |
| Diagnóstico invertido (P3.a) | 1 | **Crítica** — audit fix já feito na LIA |
| Nomes de variáveis/classes errados | 3 | **Média** — `_KEYWORD_ACTION_MAP` vs `_CONTEXT_ACTION_PATTERNS` |

**Total:** 20 erros identificados que requerem correção para a v2.3.

---

## Matriz de Status por Problema (P2–P13 + Subitens)

| # | Problema | Status v2.2 | Status v2.3 | Detalhe |
|---|----------|-------------|-------------|---------|
| P2 | Audit trail parcial | INCORRETO | CORRETO | `_pre_check`/`_post_check` clarificados como LIA-only; v5 não tem compliance no workflow |
| P3 | Compliance gaps (geral) | INCORRETO | CORRETO | Seção reescrita com distinção v5 vs LIA |
| P3.a | Audit `ON CONFLICT` | INCORRETO (invertido) | CORRETO | Bug em v5 `audit_writer.py` (DO UPDATE SET); LIA já usa DO NOTHING |
| P3.b | PII logging | INCORRETO | CORRETO | `LangGraphReActBase` removido (LIA-only); v5 tem `mask_pii()` para logs |
| P3.c | FactChecker ausente | INCORRETO | CORRETO | FactChecker global via `_post_check` é LIA-only; v5 tem fact_checker local (sourcing) |
| P4 | FairnessGuard incompleto | INCORRETO | CORRETO | Arquivos LIA substituídos por v5 reais (`jobs/fairness.py`, `sourcing/fairness.py`) |
| P5 | Compliance gaps detalhados | INCORRETO | CORRETO | Todas refs a `_pre_check`/`_post_check` como LIA-only |
| P5.a | Audit consistency | PARCIAL | CORRETO | Corrigido para refletir dois repos |
| P5.b | PII nos logs | INCORRETO | CORRETO | `LangGraphReActBase` removido; v5 usa `mask_pii()` |
| P5.c | FactChecker | INCORRETO | CORRETO | Clarificado como LIA-only via `_post_check` |
| P6 | Avaliações sem BARS | CORRETO | CORRETO | Diagnóstico original já era preciso |
| P7 | Multi-turn context loss | CORRETO | CORRETO | Diagnóstico original já era preciso |
| P8 | Flat domains sem ReAct | INCORRETO | CORRETO | `ActionExecutorService` substituído por `DomainOrchestrator` (v5) |
| P9 | Keyword/regex matching frágil | INCORRETO | CORRETO | Seção reescrita com `_CONTEXT_ACTION_PATTERNS` |
| P9.a | Keyword matching | INCORRETO | CORRETO | `_KEYWORD_ACTION_MAP` → `_CONTEXT_ACTION_PATTERNS` (regex tuples) |
| P9.b | Negação não detectada | INCORRETO | CORRETO | `NEGATION_DETECTION_BLOCK`/`interaction_patterns.py` removidos (LIA-only) |
| P10 | Context loss em integrações | CORRETO | CORRETO | Diagnóstico original já era preciso |
| P11 | Prompt hardcoded | INCORRETO | CORRETO | `PromptRegistry`, `PromptLoader`, YAMLs, `few_shot_examples.py` removidos (LIA-only) |
| P11.a | Prompt injection | CORRETO | CORRETO | Diagnóstico original já era preciso |
| P11.b | Sem few-shot | INCORRETO | CORRETO | `few_shot_examples.py` removido (LIA-only) |
| P11.c | Sem anti-sycophancy | INCORRETO | CORRETO | `ANTI_SYCOPHANCY_BLOCK` removido (LIA-only) |
| P11.d | Sem versionamento | CORRETO | CORRETO | Diagnóstico original já era preciso |
| P11.e | Sem consistency | INCORRETO | CORRETO | `interaction_patterns.py` removido (LIA-only) |
| P11.f | Prompt leaking | INCORRETO | CORRETO | Refs a LIA-only components removidas |
| P12 | Tool registry sem governança | PARCIAL | CORRETO | Clarificado `DomainRegistry` (v5) vs `ToolRegistry`/`ActionExecutorService` (LIA) |
| P13 | Observabilidade incompleta | CORRETO | CORRETO | Diagnóstico original já era preciso |

**Resumo da Matriz:**
- **CORRETO na v2.2:** 7 itens (P6, P7, P10, P11.a, P11.d, P13 + diagnósticos parciais)
- **INCORRETO/PARCIAL na v2.2 → CORRETO na v2.3:** 20 itens corrigidos
- **Status final v2.3:** 27/27 itens CORRETO

---

## Correções Aplicadas na v2.3

1. **L98** — Remover a premissa falsa "mesmo codebase"; documentar que são repos separados
2. **P2 (L106-109)** — Corrigir: `_pre_check`/`_post_check` são LIA-only; v5 não tem compliance no workflow
3. **P3.a (L116-119)** — Corrigir: bug está em v5 `src/services/audit/audit_writer.py`; LIA já usa `DO NOTHING`
4. **P3.b (L121-124)** — Corrigir: `LangGraphReActBase` é LIA-only
5. **P3.c (L126-129)** — Corrigir: FactChecker global via `_post_check` é LIA-only
6. **P4 (L131-134)** — Corrigir: trocar arquivos LIA por arquivos v5 reais
7. **P5 (L141-158)** — Corrigir: `_pre_check`/`_post_check` são LIA-only
8. **P8 (L177-180)** — Corrigir: v5 não tem `ActionExecutorService` nem `_KEYWORD_ACTION_MAP`
9. **P9.a (L192-195)** — Corrigir: v5 usa `_CONTEXT_ACTION_PATTERNS`
10. **P9.b (L197-200)** — Corrigir: `NEGATION_DETECTION_BLOCK`/`interaction_patterns.py` são LIA-only
11. **P11 (L232-265)** — Corrigir: `PromptRegistry`, `PromptLoader`, YAMLs, `few_shot_examples.py`, `interaction_patterns.py` são LIA-only
12. **Tabela cobertura (L384)** — Corrigir referência ao arquivo de audit correto
13. **Seção 3.2 (L758)** — Corrigir: domínios v5 lidos de `WeDOTalent/recruiter_agent_v5/src/domains/`, não de `lia-agent-system/app/domains/`
14. **Seção 3.2 (L788)** — Corrigir: YAMLs estão em `lia-agent-system`, v5 usa prompts inline em `prompts.py`; v5 não tem acesso ao `PromptLoader` da LIA
15. **Seção 3.5 (L1033)** — Corrigir: path do exemplo de prompt v5 para `src/domains/applies/domain.py`

### Verificação de Referências por Seção

| Seção | Refs v5 verificadas | Refs LIA verificadas | Status |
|-------|---------------------|----------------------|--------|
| 1 (Executive Summary) | L98: repos separados ✅ | L98: `lia-agent-system` ✅ | CORRETO |
| 2 (Diagnóstico P2-P13) | `src/domains/workflow.py` ✅, `src/domains/base.py` ✅, `src/services/audit/audit_writer.py` ✅, `src/domains/jobs/fairness.py` ✅, `src/domains/sourced_profile_sourcing/fairness.py` ✅ | `app/domains/workflow.py` ✅, `app/shared/compliance/fairness_guard.py` ✅, `app/shared/compliance/fact_checker.py` ✅ | CORRETO |
| 3 (Roteamento + Inventário) | `_CONTEXT_ACTION_PATTERNS` ✅, `src/domains/*/domain.py` ✅ | `CascadedRouter` ✅, `PromptRegistry` ✅, `app/prompts/domains/` ✅ | CORRETO |
| 3.5 (Prompts) | `src/domains/applies/domain.py` ✅, `prompts.py` inline ✅ | `app/prompts/domains/*.yaml` ✅, `PromptLoader` ✅ | CORRETO |
| 5 (Componentes) | `src/services/audit/` ✅, `src/services/pii_filter.py` ✅ | LIA source paths ✅ | CORRETO |
| 7-11 (Sprints) | Target paths `src/services/compliance/` ✅ | Source paths `lia-agent-system/...` ✅ | CORRETO |
