---
name: harness-engineering-lia
version: 1.0.0
description: |
  Aplica harness engineering especificamente no stack LIA (lia-agent-system FastAPI +
  ats-api-copia Rails + plataforma-lia Next.js + LangGraph agents multi-tenant).
  Complementa a skill genérica `harness-engineering` com exemplos canônicos dos
  FIX 1-13 e pointers para os arquivos reais do stack.

  Use quando trabalhar em:
  - lia-agent-system, especialmente app/tools/, app/orchestrator/, app/domains/
  - tool_registry_metadata.yaml, ToolDefinition, DomainAction
  - governance_tags, side_effects, related_tools, FairnessGuard, HITL
  - observability (emit_tool_call, lia.tool_metrics, LangSmith)
  - multi-tenancy enforcement, compliance LGPD no stack LIA

  Também usar quando usuário mencionar:
  - "FIX 1-13", "G1-G9", "ADR-019", "GLOSSARIO_ACTIONS_TOOLS", "PARTE I", "PARTE J"
  - "audit_tool_routing.py", "sync_descriptions_from_yaml", "rebuild_routing_context"
  - "pending_hitl_confirmation", "hitl_pending envelope"
  - "tool_registry", "_ACTION_TOOL_MAP", "DomainPrompt"

  Depende conceitualmente da skill `harness-engineering` (global). Carregar juntas
  quando ambas derem match — a global traz o método, esta traz os exemplos concretos
  do LIA.
triggers:
  - lia harness
  - harness lia
  - harness FIX
  - governance tags
  - fairness guard executor
  - FIX 1-13
  - tool registry lia
---

# Harness Engineering — Stack LIA

## Stack layout (onde o harness vive)

```
plataforma-lia (Next.js)
    │
    ▼
ats-api-copia (Rails, CRUD + auth)
    │   RAILS_API_URL fallback
    ▼
lia-agent-system (FastAPI, IA harness)
    ├─ app/tools/              ← tool layer canônico
    ├─ app/orchestrator/       ← planning loop + cascade router
    ├─ app/domains/            ← DomainActions + ReAct agents
    ├─ app/shared/observability/ ← sensors + tool_metrics
    └─ app/shared/compliance/  ← FairnessGuard + guardrails
```

## FIX 1-13 como taxonomia canônica

Todos os FIX implementados em `fix/kanban-e2e-bugs` são casos concretos das 4 células da taxonomia Böckeler. Use como referência ao propor novos fixes:

| FIX | Commit | Célula | Arquivo canônico |
|-----|--------|--------|-------------------|
| **FIX 1** — DomainActions → LLM | `82009b0c8` | Guide computacional (feedforward) | `app/domains/base.py::get_actions_for_prompt()` + `app/orchestrator/llm_cascade.py::rebuild_routing_context()` |
| **FIX 2+9** — examples populados | `4d55b7c40` + `896f4ae34` | Guide inferencial (feedforward) | 17 × `app/domains/*/actions.py` + inline em 4 `domain.py` |
| **FIX 3** — `requires_hitl` enforcement | `c9ec97385` | Guardrail (permission gating) | `app/tools/executor.py::execute()` → `pending_hitl_confirmation` |
| **FIX 4** — `suggested_next` | `c9ec97385` | Guide inferencial downstream | `app/tools/registry.py::ToolDefinition.related_tools` + `agentic_loop.py` |
| **FIX 5** — Wizard tools sync | `71a2ec1d1` | Guide computacional | `app/tools/__init__.py::sync_descriptions_from_yaml()` estendido |
| **FIX 7+11** — cross-refs de cluster | `71a2ec1d1` + `cf12c3ec9` | Guide inferencial | `app/domains/job_management/actions.py`, `app/domains/sourcing/actions.py` |
| **FIX 8** — FairnessGuard ativo | `8e8bfa3bd` | Sensor computacional L1 + guardrail | `app/tools/executor.py::_check_fairness()` + `app/shared/compliance/fairness_guard.py` |
| **FIX 10** — wizard YAML coverage | `c0a3e3b79` | Guide computacional | `app/tools/tool_registry_metadata.yaml` (+5 entries) |
| **FIX 10** — `resolve_requires_confirmation` | `c0a3e3b79` | Guide computacional (SoT) | `app/orchestrator/action_executor/intents_config.py` |
| **FIX 11** — `{actions_context}` placement | `cf12c3ec9` | Guide computacional | `app/orchestrator/llm_cascade.py::_ROUTING_PROMPT` |
| **FIX 12** — HITL envelope | `3f7245f18` | Sensor computacional (estrutural) | `app/orchestrator/main_orchestrator.py` → `ChatResponse.structured_data.hitl_pending` |
| **FIX 12** — `emit_tool_call` | `3f7245f18` → `453a46615` | Sensor computacional (observability) | `app/shared/observability/tool_metrics.py` |
| **FIX 13** — canonical path migration | `453a46615` | Guide computacional (CI guard) | `docs/specs/CANONICAL_SOURCES_SPEC.md` §1.2 forbidden paths |

**Gap honesto:** ainda falta sensor inferencial em produção (LLM-as-judge em PR ou runtime). Próxima evolução.

## Arquivos canônicos-alvo (onde mexer — e onde NÃO mexer)

| Objetivo | Arquivo canônico | NÃO mexer |
|----------|-------------------|-----------|
| Adicionar tool nova (YAML) | `app/tools/tool_registry_metadata.yaml` | `registry.py` (só dataclass) |
| Adicionar DomainAction | `app/domains/{domain}/actions.py` OU inline `domain.py` | `_ACTION_TOOL_MAP` manual em `domain.py` |
| Novo governance tag | Primeiro adicionar em `executor.py::execute()` enforcement, depois declarar no YAML | Decidir no prompt do LLM |
| Novo sensor computacional | `tests/unit/test_fix*.py` (TDD) + regra em `scripts/` | LLM-as-judge como primeira linha |
| Novo guide em CLAUDE.md | `docs/LIA_AI_HANDOFF.md` + cross-ref no `DEVELOPER_HANDOFF.md` | Prompt do agente direto |
| Observability tool call | `app/shared/observability/tool_metrics.py::emit_tool_call()` | Logger solto em agentic_loop |

## Padrões canônicos do projeto (enforcement automático)

1. **Single source of truth YAML → ToolDefinition.** `tool_registry_metadata.yaml` é canônico. `sync_descriptions_from_yaml()` no startup popula `description`, `governance_tags`, `related_tools`, `side_effects`, `when_to_use`, `when_not_to_use`.
2. **HITL envelope estruturado.** Frontend consome `structured_data.hitl_pending[]`. Backend produz via `ToolExecutor` quando `"requires_hitl" in governance_tags`.
3. **emit_tool_call para toda execução.** Não criar logger solto — usar `app.shared.observability.tool_metrics::emit_tool_call()`.
4. **CI guard via forbidden paths.** `docs/specs/CANONICAL_SOURCES_SPEC.md` §1.2 é a fonte. Se quiser bloquear path novo, adicionar ali.
5. **Multi-tenancy.** `company_id` sempre via `ToolExecutionContext` (JWT/session), nunca do payload.
6. **FairnessGuard enforcement.** Tools que recebem text params de candidato DEVEM ter `governance_tags: [..., fairness_guard]` no YAML.

## Follow-ups abertos (candidatos a próximos FIX)

Contexto para propostas novas:

- **`pii` governance tag enforcement** — declarado em várias tools, mas ainda sem hook no executor. Candidato a sensor + guardrail.
- **`audit_trail` governance tag enforcement** — similar. Forward automático ao audit service.
- **`credits_consumed` enforcement** — budget check pré-execução por tenant.
- **LLM-as-judge em PR** — sensor inferencial que falta (gap identificado em FIX 1-13).
- **CI guard** para `app.core.observability` (path proibido agora que FIX 13 migrou) — adicionar em `scripts/check_forbidden_imports.py`.
- **Glossary regeneration em CI** — `scripts/generate_tool_action_glossary.py --check` pre-commit ou GitHub Action.

Qualquer um desses é candidato natural a virar FIX 14+. Aplicar o workflow default da skill genérica (diagnóstico → root cause → 2 eixos → priorizar computacional → mensagem otimizada → persistência).

## Cross-refs obrigatórios para propostas

Ao propor qualquer fix no stack LIA, referenciar:

- [`docs/LIA_AI_HANDOFF.md`](docs/LIA_AI_HANDOFF.md) — overview técnico (13 seções)
- [`docs/specs/ai/ADR-019-governance-and-observability.md`](docs/specs/ai/ADR-019-governance-and-observability.md) — decisões arquiteturais (FIX 3, 8, 12, 13)
- [`docs/GLOSSARIO_ACTIONS_TOOLS.md`](docs/GLOSSARIO_ACTIONS_TOOLS.md) — 103 tools × 281 actions (regenerar via `scripts/generate_tool_action_glossary.py`)
- [`docs/specs/CANONICAL_SOURCES_SPEC.md`](docs/specs/CANONICAL_SOURCES_SPEC.md) — registry de paths canônicos
- `DEVELOPER_HANDOFF.md` PARTE I (FIX 1-13) + PARTE J (Jornada Completa)

## Formato de entrega

Além do bloco genérico da skill `harness-engineering`, toda proposta LIA-específica deve incluir:

```
─────────────────────────────────────────────────
FIX LIA proposto:
  - ID: FIX <N>
  - Gap correspondente: G<N> (se aplicável)
  - Arquivo canônico: <path>
  - Test TDD: tests/unit/test_fix<N>_*.py
  - Commit message proposto: <conventional commits>
  - Cross-ref docs: <lista dos docs a atualizar>

Impacto no GLOSSARIO:
  - [ ] Regenerar via scripts/generate_tool_action_glossary.py

Deploy checklist:
  - [ ] Restart FastAPI workflow no Replit
  - [ ] pytest tests/unit/test_fix*.py --no-cov
  - [ ] smoke test manual: <frase natural>
─────────────────────────────────────────────────
```

## Quando ativar outras skills em conjunto

- `harness-engineering` (global) — método base. Sempre carregar junto.
- `canonical-fix` — onde colocar o fix (qual arquivo canônico).
- `lia-testing` — TDD Red→Green→Refactor para sensors computacionais.
- `feature-audit` — auditoria 6-dimensões dos 11 componentes de harness.
- `production-quality` + `production-quality:modules:ai-architecture` — padrões de qualidade para agentes.
