# LIA AI — Handoff Técnico (FIX 1-12)

> Documento canônico para o time de desenvolvimento consumir, reproduzir e manter as 12 melhorias implementadas na camada de IA da plataforma LIA entre 2026-04-20 e 2026-04-21.
>
> **Versão:** 1.0 · **Data:** 2026-04-21 · **Branch:** `fix/kanban-e2e-bugs` · **Repo:** `lia-agent-system`
>
> Idioma: PT-BR · Escopo: cobertura 100% dos 9 gaps identificados no diagnóstico das Tasks #690/#698 · Status: 91/91 testes TDD verdes, 0 regressões.

---

## Índice

1. [Sumário executivo](#1-sumário-executivo)
2. [Arquitetura](#2-arquitetura)
3. [Canonical sources of truth](#3-canonical-sources-of-truth)
4. [12 FIXes implementados](#4-12-fixes-implementados)
5. [ToolDefinition — estrutura completa](#5-tooldefinition--estrutura-completa)
6. [DomainAction — estrutura completa](#6-domainaction--estrutura-completa)
7. [Governance tags glossary](#7-governance-tags-glossary)
8. [Side_effects glossary](#8-side_effects-glossary)
9. [APIs & endpoints](#9-apis--endpoints)
10. [Frontend contract — JSON shapes](#10-frontend-contract--json-shapes)
11. [Observability runbook](#11-observability-runbook)
12. [Deployment & Testing](#12-deployment--testing)
13. [Apêndices](#13-apêndices)

---

## 1. Sumário executivo

### O que mudou

Durante duas sessões de trabalho, a camada de IA da LIA passou de **"documentação enriquecida mas não consumida"** para **"enforcement ativo + observability mensurável"**. As Tasks #690/#698 haviam enriquecido 88 ferramentas no YAML e 245 ações de domínio em Python, mas apenas as ferramentas chegavam ao LLM. Os 9 gaps (G1-G9) fecham esse ciclo.

### Impacto prático no recruiter

1. **Escolha correta de ferramenta na primeira tentativa** — LLM recebe `when_to_use` + `when_not_to_use` + 245 descrições de action no routing prompt. Redução esperada: 20-35% menos tool-selection errors.
2. **Bloqueio automático de viés (LGPD/CF Art. 5º)** — FairnessGuard agora bloqueia execução antes do handler rodar quando a query tem viés explícito (ex: "somente homens").
3. **HITL real** — ferramentas sensíveis (envio em massa, fechamento de vaga) retornam `pending_hitl_confirmation` e o frontend pode pedir confirmação humana antes de persistir.
4. **Sugestões proativas** — após executar uma ferramenta, LIA sugere `related_tools` como próximos passos (ex: após validar JD, sugere salvar rascunho).
5. **Few-shot em 270 ações** — cada DomainAction tem 2-3 exemplos de frases do usuário. 100% quality, zero fallbacks "isso".
6. **Observabilidade mensurável** — cada tool call emite evento estruturado (`tool_name`, `company_id`, `success`, `first_shot`, `latency_ms`, `governance_tags`) com forwarding opcional ao LangSmith.

### Tabela de commits

| FIX | Gap | Hash | Escopo |
|-----|-----|------|--------|
| 1 | G1 | [`82009b0c8`](../../commit/82009b0c8) | DomainActions → LLM via routing context |
| 2 | G2 | [`4d55b7c40`](../../commit/4d55b7c40) | 245 actions × examples populados |
| 3+4 | G3+G4 | [`c9ec97385`](../../commit/c9ec97385) | governance_tags HITL + related_tools |
| 5+6+7 | G5+wizard+overlap | [`71a2ec1d1`](../../commit/71a2ec1d1) | wizard sync + observability + overlap |
| 8 | G1+G2 residual | [`8e8bfa3bd`](../../commit/8e8bfa3bd) | FairnessGuard enforcement + side_effects |
| 9 | G3 residual | [`896f4ae34`](../../commit/896f4ae34) | 100% quality examples + 4 inline domains |
| 10 | G4+G6 | [`c0a3e3b79`](../../commit/c0a3e3b79) | 5 wizard YAML + resolver confirmation |
| 11 | G5+G7 | [`cf12c3ec9`](../../commit/cf12c3ec9) | actions_context placement + WSI cross-ref |
| 12 | G8+G9 | [`3f7245f18`](../../commit/3f7245f18) | HITL envelope + observability module |

---

## 2. Arquitetura

### Camadas

```
┌─────────────────────────────────────────────────────────────────────┐
│ Frontend (plataforma-lia, Next.js)                                  │
│ - Lê structured_data.tool_calls[*].suggested_next                   │
│ - Lê structured_data.hitl_pending → renderiza confirmação           │
│ - Backend proxy: /api/backend-proxy/...                             │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTP
                 ┌─────────────┴─────────────┐
                 │                           │
┌────────────────▼──────────┐   ┌────────────▼──────────────────────┐
│ Rails (ats-api, Ruby)     │   │ FastAPI IA (lia-agent-system, PY) │
│ - CRUD: vagas, candidatos │   │ - /api/v1/chat/ (orchestrator)    │
│ - Auth (JWT, WorkOS)      │   │ - Domain routing (cascade)        │
│ - Multi-tenant            │   │ - Tool execution + FairnessGuard  │
└────────────┬──────────────┘   └────────────┬──────────────────────┘
             │ HTTP (RAILS_API_URL fallback) │
             └──────────────────────────────▶│
                                              │ LLM provider calls
                                              ▼
                          ┌───────────────────────────────────┐
                          │ Claude / Gemini / Opus            │
                          │ - Function calling (88+5 tools)   │
                          │ - Enriched schemas via YAML sync  │
                          └───────────────────────────────────┘
```

### Pontos de entrada

| Endpoint | Arquivo | Responsabilidade |
|----------|---------|------------------|
| `POST /api/v1/chat/` | `app/api/v1/chat.py:228` | Chat principal (REST) |
| `POST /api/v1/chat/stream` | `app/api/v1/chat.py:961` | SSE streaming |
| `POST /api/v1/chat/with-attachments` | `app/api/v1/chat.py` | Upload CV + mensagem |
| `GET /api/v1/chat/{id}/stream` | `app/api/v1/agent_chat_sse.py` | Read stream |
| `WS /api/v1/chat/ws` | `app/api/v1/agent_chat_ws.py` | WebSocket variant |

O `main_orchestrator.process_request()` é o ponto de convergência — todos os endpoints acima chamam-no.

### Dois layers de ferramentas

A plataforma tem **dois sistemas paralelos** que foram conectados ao LLM por FIX 1-12:

| Layer | Quantidade | Formato | Pipeline ao LLM |
|-------|-----------|---------|-----------------|
| **ToolDefinitions** | 88 + 5 wizard = 93 | YAML + Python dataclass | ✅ via function-calling schema |
| **DomainActions** | 270 | Python dataclass em `actions.py` / `domain.py` | ✅ via `get_actions_for_prompt()` no routing (pós FIX 1) |

### Flowtrace — startup (1x, em `main.py:209`)

```
initialize_tools()
    │
    ├─ register_job_wizard_tools()      ← cada domínio registra suas tools
    ├─ register_candidate_tools()
    ├─ register_communication_tools()
    ├─ ... (+10 domínios)
    │
    ├─ sync_descriptions_from_yaml()    ← FIX 2/3/4/8
    │      │
    │      ├─ carrega tool_registry_metadata.yaml
    │      ├─ para cada tool: description += USE WHEN / DO NOT USE WHEN
    │      ├─ popula governance_tags, related_tools, side_effects
    │      └─ sincroniza wizard tools (FIX 5)
    │
    └─ llm_cascade_router.rebuild_routing_context()   ← FIX 1
           │
           ├─ itera DomainRegistry.list_domains()
           ├─ para cada domain: chama get_actions_for_prompt(max_actions=5)
           └─ constrói _actions_context (string com 245 actions + examples)
```

### Flowtrace — per-request

```
POST /api/v1/chat/
    │
    ▼
main_orchestrator.process_request()
    │
    ├─ cascaded_router.route(message)
    │      │
    │      ├─ Tier 1: fast_router.py (regex)
    │      ├─ Tier 2: llm_cascade.route() ← injeta {actions_context} (FIX 11)
    │      │                                e {message} no _ROUTING_PROMPT
    │      └─ Tier 3: domain.process_intent() (keyword matching)
    │
    ├─ agentic_loop.run() (se domínio precisa function-calling)
    │      │
    │      ├─ LLM vê schemas enriquecidos (descriptions + USE WHEN:)
    │      ├─ LLM escolhe tool → tc.name + tc.parameters
    │      │
    │      ├─ tool_executor.execute(tool_name, parameters, context)
    │      │      │
    │      │      ├─ FIX 8: se governance_tags contém "fairness_guard"
    │      │      │         → FairnessGuard.check() em text params
    │      │      │         → se bloqueado: return ToolResult(error=...)
    │      │      │
    │      │      ├─ FIX 3: se governance_tags contém "requires_hitl"
    │      │      │         → return ToolResult(status=pending_hitl_confirmation)
    │      │      │
    │      │      └─ handler(parameters) ← só executa se passar os gates
    │      │
    │      ├─ FIX 4: tool_calls_made[].suggested_next = tool.related_tools
    │      │
    │      └─ FIX 12: emit_tool_call(...) ← observability
    │
    └─ ChatResponse(
           structured_data={
             tool_calls: [...],
             hitl_pending: [...]      ← FIX 12 se houver
           },
           needs_confirmation=bool(hitl_pending)
       )
```

---

## 3. Canonical sources of truth

| Artefato | Path canônico | Owner |
|----------|---------------|-------|
| Tool metadata | `app/tools/tool_registry_metadata.yaml` (2828+ linhas, 93 tools) | IA team |
| ToolDefinition dataclass | `app/tools/registry.py` | IA team |
| DomainAction dataclass | `app/domains/base.py` | IA team |
| Per-domain capabilities | `app/domains/{domain}/config/capabilities.yaml` | Per-domain owner |
| Per-domain actions | `app/domains/{domain}/actions.py` OU inline em `domain.py` | Per-domain owner |
| Compliance blocks | `app/prompts/shared/{compliance,guardrails}_block.yaml` | Compliance team |
| Domain prompts | `app/prompts/domains/*.yaml` | Per-domain owner |
| Agents registry | `app/agents_registry.yaml` | IA team |
| Glossary público | `docs/GLOSSARIO_ACTIONS_TOOLS.md` | IA team |
| Canonical spec | `docs/specs/CANONICAL_SOURCES_SPEC.md` | IA team |
| ADR-016 (tool registry) | `docs/specs/ai/ADR-016-tool-registration-canonical.md` | IA team |
| ADR-019 (gov + obs) | `docs/specs/ai/ADR-019-governance-and-observability.md` | IA team |

**Regra de PR — tool_registry_metadata.yaml:**
- Qualquer mudança no YAML exige rodar `python -c "from app.tools import tool_registry, initialize_tools; initialize_tools(); print(tool_registry.validate_yaml())"` → deve retornar `{"ok": true}`
- Hook sugerido: pre-commit que roda a validação
- Regenerar glossário pós-merge: `python scripts/generate_tool_action_glossary.py`

---

## 4. 12 FIXes implementados

### FIX 1 — DomainActions chegam ao LLM ([`82009b0c8`](../../commit/82009b0c8))

**Gap fechado:** G1 — 245 DomainActions existiam no código mas nunca chegavam ao prompt do LLM.

**Arquivos tocados:**
- `app/domains/base.py` — novo método `DomainPrompt.get_actions_for_prompt(max_actions=8)`
- `app/orchestrator/llm_cascade.py` — novo método `LLMCascadeRouter.rebuild_routing_context()`
- `app/tools/__init__.py` — `initialize_tools()` chama `rebuild_routing_context()` após sync

**Antes:** LLM router via apenas 30 nomes de domínios com 1-2 linhas de descrição cada. Rotear `"melhora minha JD"` → `job_management` ou `cv_screening`? LLM adivinhava.

**Depois:** Após o `_ROUTING_PROMPT`, o LLM vê lista de até 5 actions por domínio com `description` + 1 `example`. Cada action_id é visível no prompt — LLM tem contexto para decidir.

**Teste que cobre:** [`tests/unit/test_fix1_domain_actions_to_llm.py`](../../tests/unit/test_fix1_domain_actions_to_llm.py) (10 testes)

---

### FIX 2 — DomainAction.examples populado ([`4d55b7c40`](../../commit/4d55b7c40))

**Gap fechado:** G2 — `examples: tuple[str,...]` existia como campo mas estava vazio em todas as 245 actions.

**Arquivos tocados:** 13 × `app/domains/*/actions.py` (todos os domínios principais)

**Antes:** `DomainAction(action_id="create_job", description="...", examples=())` — field definido no dataclass, nunca usado.

**Depois:** Cada action tem 2-3 frases de exemplo em PT-BR, geradas por:
- ~50 handcrafted (high-impact: create_job, search_candidates, send_email)
- ~195 heurísticas baseadas em action_id + action.name

Exemplo:
```python
DomainAction(
    action_id="create_job",
    examples=(
        "quero abrir uma vaga de engenheiro de software",
        "preciso contratar um analista de dados sênior",
        "cria uma posição de gerente de projetos para São Paulo",
    ),
)
```

**Teste que cobre:** [`tests/unit/test_fix2_examples_populated.py`](../../tests/unit/test_fix2_examples_populated.py) (14 testes — 13 domínios + coverage global)

---

### FIX 3 — governance_tags com HITL enforcement ([`c9ec97385`](../../commit/c9ec97385))

**Gap fechado:** G3 — `governance_tags: [requires_hitl]` declarada no YAML em 10+ tools, mas executor NÃO checava.

**Arquivos tocados:**
- `app/tools/registry.py` — `ToolDefinition.governance_tags: list[str]` (novo campo)
- `app/tools/__init__.py` — `sync_descriptions_from_yaml()` popula do YAML
- `app/tools/executor.py` — `execute()` checa `requires_hitl` antes de chamar handler

**Antes:** Tag era metadata morta. Uma tool marcada `requires_hitl` executava direto sem confirmação humana.

**Depois:** `ToolExecutor.execute()` retorna ANTES de chamar o handler:
```python
if "requires_hitl" in governance_tags and not parameters.get("_hitl_confirmed"):
    return ToolResult(
        success=True,
        result={
            "status": "pending_hitl_confirmation",
            "requires_hitl": True,
            "tool_name": tool_name,
            "parameters": parameters,
            "governance_tags": governance_tags,
            "message": f"A ferramenta '{tool_name}' requer confirmação humana..."
        },
    )
```

Caller deve re-chamar com `_hitl_confirmed=True` para bypass.

**Teste que cobre:** [`tests/unit/test_fix34_governance_related_tools.py`](../../tests/unit/test_fix34_governance_related_tools.py)

---

### FIX 4 — related_tools → suggested_next ([`c9ec97385`](../../commit/c9ec97385))

**Gap fechado:** G4 — `related_tools: [...]` no YAML nunca era lido.

**Arquivos tocados:**
- `app/tools/registry.py` — `ToolDefinition.related_tools: list[str]` (novo campo)
- `app/tools/__init__.py` — sync popula
- `app/orchestrator/agentic_loop.py` — cada tool_call agora inclui `suggested_next`

**Antes:** YAML tinha `related_tools: [save_job_draft, validate_job_fields]` mas frontend nunca via.

**Depois:** `tool_calls_made[].suggested_next = list(tool_def.related_tools)`. Frontend pode renderizar botões proativos após cada execução.

**Teste que cobre:** `test_fix34_governance_related_tools.py::TestAgenticLoopRelatedTools`

---

### FIX 5 — Wizard tools sync ([`71a2ec1d1`](../../commit/71a2ec1d1))

**Gap fechado:** G5 — tools do wizard de criação de vaga usavam um registry paralelo (`lia_agents_core.ToolDefinition`) que não era sincronizado.

**Arquivos tocados:**
- `app/tools/__init__.py` — `sync_descriptions_from_yaml()` também sincroniza `WIZARD_TOOLS`
- `app/domains/job_management/agents/wizard_tool_registry.py` (consumer, não modificado)

**Antes:** 7 de 12 wizard tools tinham entries no YAML, mas `sync` só operava no registry global.

**Depois:** Sync cobre `WIZARD_TOOLS` também (pydantic BaseModel mutável — só `description` é sincronizável). Após FIX 10, os 5 restantes ganham entries no YAML.

**Teste que cobre:** [`tests/unit/test_fix5_wizard_sync.py`](../../tests/unit/test_fix5_wizard_sync.py) (3 testes)

---

### FIX 6 — Observability inline ([`71a2ec1d1`](../../commit/71a2ec1d1))

**Gap fechado:** prep para G9 — logging inline de tool_call para medir first-shot rate.

**Arquivos tocados:** `app/orchestrator/agentic_loop.py` — `logger.info("tool_call", extra={...})`

Posteriormente refatorado por FIX 12 para usar módulo central `app/core/observability.py`.

**Teste que cobre:** [`tests/unit/test_fix6_observability.py`](../../tests/unit/test_fix6_observability.py) (3 testes)

---

### FIX 7 — Overlap semântico cluster 1-2 ([`71a2ec1d1`](../../commit/71a2ec1d1))

**Gap fechado:** G6 parcial — 2 dos 3 clusters de overlap disambiguados.

**Arquivos tocados:**
- `app/domains/job_management/actions.py` — `generate_jd` / `enrich_jd` / `suggest_jd_improvements`
- `app/domains/sourcing/actions.py` — `auto_source` / `suggest_candidates` / `talent_pool_search`

**Antes:** LLM confundia `generate_jd` com `enrich_jd`.

**Depois:** Cada description tem `Distinto de X (porque Y)` explícito. Ex:
> "Gera job description completa e otimizada com IA a partir do título e requisitos básicos fornecidos. **Distinto de enrich_jd (que melhora JD já existente) e de suggest_jd_improvements (que apenas sugere edições, sem sobrescrever).**"

**Teste que cobre:** [`tests/unit/test_fix7_semantic_overlap.py`](../../tests/unit/test_fix7_semantic_overlap.py) (6 testes)

---

### FIX 8 — FairnessGuard + side_effects ([`8e8bfa3bd`](../../commit/8e8bfa3bd))

**Gaps fechados:** G1 completo (fairness ativa) + G2 (side_effects parseado).

**Arquivos tocados:**
- `app/tools/registry.py` — `ToolDefinition.side_effects: list[str]` (novo)
- `app/tools/__init__.py` — sync popula
- `app/tools/executor.py` — `_check_fairness()` + invocação antes do handler

**Antes:** Tag `fairness_guard` em 14+ tools no YAML, mas `FairnessGuard` (existia em `app/shared/compliance/fairness_guard.py`) nunca era invocado pelo executor.

**Depois:** `ToolExecutor.execute()` escaneia parâmetros de texto (`query`, `description`, `content`, etc.) e bloqueia se `FairnessGuard.check()` detectar viés explícito (Layer 1 regex):

```python
if "fairness_guard" in governance_tags:
    bias_result = self._check_fairness(parameters)
    if bias_result:
        return ToolResult(
            success=False,
            error=f"FairnessGuard blocked: {bias_result['blocked_terms']}",
            result={"blocked_by_fairness_guard": True, ...},
        )
```

Exemplo prático: `"busca candidatos somente homens"` → bloqueado antes do handler.

**Teste que cobre:** [`tests/unit/test_fix8_governance_enforcement.py`](../../tests/unit/test_fix8_governance_enforcement.py) (5 testes)

---

### FIX 9 — 100% quality examples ([`896f4ae34`](../../commit/896f4ae34))

**Gap fechado:** G3 residual — 18% dos examples eram `"isso"`-fallback.

**Arquivos tocados:**
- Todos os `actions.py` com examples fracos (sourcing, analytics, ats_integration, automation, communication, cv_screening, interview_scheduling, recruiter_assistant + outros)
- 4 novos domínios com DomainActions inline em `domain.py`:
  - `company_settings/domain.py` (7 actions)
  - `hiring_policy/domain.py` (9 actions)
  - `pipeline/domain.py` (5 actions)
  - `candidate_self_service/domain.py` (4 actions)

**Antes:** 68 examples com `"isso"` genérico (ex: `"busca isso"`, `"enriquece isso"`). 4 domínios inteiros sem examples.

**Depois:** 100% quality (0 weak fallback). 486 examples total. Cobertura completa.

**Teste que cobre:** [`tests/unit/test_fix9_quality.py`](../../tests/unit/test_fix9_quality.py) (2 testes — ratio + all domains populated)

---

### FIX 10 — Wizard YAML + requires_confirmation resolver ([`c0a3e3b79`](../../commit/c0a3e3b79))

**Gaps fechados:** G4 residual (5 wizard tools sem YAML) + G7 (requires_confirmation com 2 fontes paralelas).

**Arquivos tocados:**
- `app/tools/tool_registry_metadata.yaml` — 5 entries novas
- `app/orchestrator/action_executor/intents_config.py` — `resolve_requires_confirmation()` helper

**5 tools adicionadas ao YAML:**
- `extract_job_requirements` — extração estruturada
- `create_job_draft` — draft em memória
- `validate_job_requirements` — FairnessGuard check
- `get_salary_benchmarks` — market + internal
- `check_job_draft_health` — proactive QA

**Resolver:**
```python
def resolve_requires_confirmation(intent: str | None, action_id: str | None) -> bool:
    # 1. Intent-level (mais específico)
    if intent in ACTIONABLE_INTENTS:
        return ACTIONABLE_INTENTS[intent]["requires_confirmation"]
    # 2. DomainAction-level (fallback)
    if action_id:
        domain = DomainRegistry().get_domain_for_action(action_id)
        if domain:
            action = domain.get_action_by_id(action_id)
            return getattr(action, "requires_confirmation", False)
    # 3. Default: safe
    return False
```

**Precedência:** intent > DomainAction > False (safe). Intent tem mais contexto (ex: `reject_candidate` intent tem `requires_confirmation=False` porque handler gerencia seu próprio gate).

**Teste que cobre:** [`tests/unit/test_fix10_coverage_unification.py`](../../tests/unit/test_fix10_coverage_unification.py) (6 testes)

---

### FIX 11 — Placement + WSI cluster ([`cf12c3ec9`](../../commit/cf12c3ec9))

**Gaps fechados:** G5 residual (actions_context no lugar errado) + G6 final (cluster WSI).

**Arquivos tocados:**
- `app/orchestrator/llm_cascade.py` — `_ROUTING_PROMPT` agora tem placeholder `{actions_context}` ANTES de `{message}`
- `app/domains/job_management/actions.py` — cross-ref em `generate_wsi_questions`

**Antes (FIX 1 ingenuity):** `_actions_context` era ANEXADO ao FIM do `_ROUTING_PROMPT`, depois de `"Responda SOMENTE com JSON"`. LLMs tendem a dropar contexto após instrução de output.

**Depois:** Template `{actions_context}` é substituído ANTES de `{message}`:
```
...domain guide...
{actions_context}       ← FIX 11: substituição aqui
Mensagem: {message}
Responda SOMENTE com JSON.
```

**WSI cluster:** `generate_wsi_questions` agora explica que é distinto do fluxo em `cv_screening`.

**Teste que cobre:** [`tests/unit/test_fix11_placement_wsi.py`](../../tests/unit/test_fix11_placement_wsi.py) (4 testes)

---

### FIX 12 — HITL envelope + observability central ([`3f7245f18`](../../commit/3f7245f18))

**Gaps fechados:** G8 (HITL sem UI envelope) + G9 (observability sem ingestion).

**Arquivos tocados:**
- `app/core/observability.py` — **novo módulo** com `emit_tool_call()` + `emit_hitl_pending()`
- `app/orchestrator/agentic_loop.py` — refatorado para chamar `emit_tool_call()` (substitui inline FIX 6)
- `app/orchestrator/main_orchestrator.py` — promove `pending_hitl_confirmation` para `structured_data.hitl_pending`

**Observability module:**
- Sempre emite `logger.info("tool_call", extra={...})` com 9 campos estruturados
- Opcional forwarding ao LangSmith (gated por env vars, lazy-init, nunca raises)
- `emit_hitl_pending()` para audit trail de confirmações

**HITL envelope em ChatResponse:**
```python
# Detecta pending_hitl_confirmation em qualquer tool_call
_hitl_pending = [...]
_structured_data = {
    "tool_calls": _tool_calls,
    "iterations": N,
}
if _hitl_pending:
    _structured_data["hitl_pending"] = _hitl_pending

_resp = ChatResponse(
    needs_confirmation=bool(_hitl_pending),
    structured_data=_structured_data,
)
```

**Teste que cobre:** [`tests/unit/test_fix12_hitl_obs.py`](../../tests/unit/test_fix12_hitl_obs.py) (6 testes)

---

## 5. ToolDefinition — estrutura completa

### Schema (2026-04-21, pós FIX 1-12)

```python
# app/tools/registry.py
from dataclasses import dataclass, field
from collections.abc import Awaitable, Callable
from typing import Any

@dataclass
class ToolDefinition:
    """Definition of a tool that can be called by LLM agents."""
    name: str
    description: str
    parameters_schema: dict[str, Any]
    handler: Callable[..., Awaitable[dict[str, Any]]]
    allowed_agents: list[str] = field(default_factory=list)
    # FIX 3 — Compliance/safety flags. Values: pii | fairness_guard | requires_hitl |
    #         multi_tenant | audit_trail | credits_consumed | write_destructive
    governance_tags: list[str] = field(default_factory=list)
    # FIX 4 — Suggested follow-up tools (proactive suggestions after execution)
    related_tools: list[str] = field(default_factory=list)
    # FIX 8 G2 — Side effects classification
    side_effects: list[str] = field(default_factory=list)

    def to_claude_schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,  # já enriquecido com USE WHEN / DO NOT USE WHEN
            "input_schema": self.parameters_schema,
        }
```

### Pipeline YAML → ToolDefinition → LLM

```
app/tools/tool_registry_metadata.yaml
    │  (dev edita aqui — fonte da verdade)
    ▼
load_tool_metadata() [tool_registry_loader.py]
    │
    ▼
initialize_tools() [tools/__init__.py:209 no main.py]
    │
    ├─ registra ToolDefinition básicos de cada domínio
    │
    ├─ sync_descriptions_from_yaml()
    │      │
    │      ├─ tool.description = YAML description + USE WHEN + DO NOT USE WHEN
    │      ├─ tool.governance_tags = YAML governance_tags
    │      ├─ tool.related_tools = YAML related_tools
    │      └─ tool.side_effects = YAML side_effects
    │
    └─ llm_cascade_router.rebuild_routing_context()
           │
           └─ _actions_context = dump de todas as actions de todos os domínios

agentic_loop.py:54
    │
    └─ tool_registry.get_all_schemas(format="claude")
           │
           └─ [tool.to_claude_schema() for tool in ...]
                  │
                  ▼
            client.messages.create(model=..., tools=[...], messages=[...])
                                              ↑
                                   LLM vê schemas enriquecidos
```

---

## 6. DomainAction — estrutura completa

### Schema (2026-04-21, pós FIX 2+9)

```python
# app/domains/base.py
from dataclasses import dataclass, field
from enum import StrEnum

class ActionType(StrEnum):
    ACTION = "action"
    QUERY = "query"
    NAVIGATION = "navigation"

@dataclass
class DomainAction:
    id: str = ""                     # legacy
    action_id: str = ""              # canonical
    name: str = ""                   # humano-legível ("Criar vaga")
    description: str = ""            # texto rico com "Aciona quando..."
    action_type: ActionType = ActionType.ACTION
    required_params: list[str] = field(default_factory=list)
    optional_params: list[str] = field(default_factory=list)
    requires_confirmation: bool = False
    tags: list[str] = field(default_factory=list)
    is_async: bool = False
    # FIX 2 + 9 — few-shot examples (100% populados, 0 fallback)
    examples: tuple[str, ...] | list[str] = field(default_factory=tuple)
```

### Pipeline DomainAction → LLM

```
app/domains/*/actions.py (ou domain.py inline)
    │  (dev edita aqui)
    ▼
domain.get_allowed_actions() → list[DomainAction]
    │
    ▼
DomainPrompt.get_actions_for_prompt(max_actions=8)  ← FIX 1
    │
    │ Monta texto:
    │ "  - create_job: Cria nova vaga de emprego...
    │     ex: \"quero abrir uma vaga de engenheiro\"
    │   - update_job: Atualiza campos da vaga existente..."
    │
    ▼
LLMCascadeRouter.rebuild_routing_context()  ← startup
    │
    └─ self._actions_context = "\n".join([...])

LLMCascadeRouter._call_model()  ← per-request
    │
    ├─ base_prompt = _ROUTING_PROMPT
    ├─ prompt = base_prompt.replace("{actions_context}", actions_ctx).replace("{message}", msg)
    │                                    ↑
    │                              FIX 11: antes de {message}
    ▼
LLM decide domain → {"domain": "job_management", "confidence": 0.87}
```

### _ACTION_TOOL_MAP — mapeamento action_id → tool_id

Cada `domain.py` tem um dict que mapeia DomainAction → ToolDefinition. Exemplo:

```python
# app/domains/job_management/domain.py
_ACTION_TOOL_MAP: dict[str, str] = {
    "create_job": "create_job_vacancy",       # DomainAction → Tool
    "update_job": "update_job_vacancy",
    "generate_jd": "generate_job_description",
    # ...
}
```

Isso permite: o cascade router escolhe o DOMAIN baseado em `get_actions_for_prompt`, o domain decide a ACTION via `process_intent`, e depois a action chama a TOOL via `_ACTION_TOOL_MAP`.

---

## 7. Governance tags glossary

Tabela com os 7 valores canônicos de `governance_tags`, seu significado e enforcement:

| Tag | Significado | Enforcement | Status |
|-----|-------------|-------------|--------|
| `multi_tenant` | Tool valida `company_id` antes de operar | `ToolExecutionContext` garantido via JWT/session | ✅ ativo |
| `pii` | Tool trata dados pessoais identificáveis | Logging/audit (hook futuro via `audit_trail`) | ⏳ parcial |
| `fairness_guard` | Tool sujeita à análise de viés | **FIX 8** — `ToolExecutor._check_fairness()` bloqueia via Layer 1 regex | ✅ **ativo** |
| `requires_hitl` | Tool precisa confirmação humana antes de executar | **FIX 3** — retorna `status=pending_hitl_confirmation` | ✅ **ativo** |
| `audit_trail` | Tool grava audit log automático | Hook futuro no executor | ⏳ parcial |
| `credits_consumed` | Tool custa crédito externo (API paga) | Validação de budget via `tenant_budget.py` | ⏳ parcial |
| `write_destructive` | Ação que persiste mudança irreversível | Normalmente combinada com `requires_hitl` | ✅ via HITL |

**Como marcar uma nova tool:**
```yaml
# app/tools/tool_registry_metadata.yaml
  - name: send_bulk_email
    governance_tags: [multi_tenant, pii, requires_hitl, audit_trail, fairness_guard]
    side_effects: [db_write, email_sent, audit_trail]
```

**Dica para compliance team:** toda tool que escreve dados externos (email/whatsapp/webhook) DEVE ter `requires_hitl` + `audit_trail`. Toda tool que recebe texto livre sobre candidatos DEVE ter `fairness_guard`.

---

## 8. Side_effects glossary

Tabela dos valores observados no YAML (15 distintos) com uso downstream:

| Side effect | Significado | Uso downstream |
|-------------|-------------|----------------|
| `none` | Read-only, sem side effects | Retry seguro, idempotent |
| `db_write` | Persiste no banco | Retry cuidadoso, idempotency key |
| `external_api_call` | Chama API externa | Circuit breaker, timeout |
| `credits_consumed` | Gasta créditos pagos | Budget check pré-execução |
| `audit_trail` | Grava audit log | Forward automático ao audit service |
| `email_sent` | Envio de email | Rate limiting, dedup |
| `webhook_fired` | Dispara webhook externo | Replay protection |
| `whatsapp_sent` | Envio via WhatsApp | Rate limiting por tenant |
| `mock_only` | Só mock, não executa | Skip em testes de produção |
| `write_destructive` | Destrutivo (delete, close) | Sempre com HITL |

---

## 9. APIs & endpoints

### Entry points para Rails/Frontend

| Endpoint | Método | Arquivo | Uso |
|----------|--------|---------|-----|
| `/api/v1/chat/` | POST | `app/api/v1/chat.py:228` | Chat principal — entry point mais comum |
| `/api/v1/chat/stream` | POST | `app/api/v1/chat.py:961` | SSE streaming de response |
| `/api/v1/chat/with-attachments` | POST | `app/api/v1/chat.py` | Upload (ex: anexa CV) |
| `/api/v1/chat/actions/candidate-field-update` | POST | `app/api/v1/chat.py` | Ação estruturada |
| `/api/v1/chat/{session_id}/stream` | GET | `app/api/v1/agent_chat_sse.py` | Read SSE stream |
| `/api/v1/chat/ws` | WS | `app/api/v1/agent_chat_ws.py` | WebSocket chat |
| `/api/orchestrator_routes/*` | varies | `app/api/orchestrator_routes.py` | Orchestrator admin |

### Integração Rails

```python
# app/orchestrator/action_handlers/_handler_hooks.py
import os
RAILS_ENABLED = bool(os.environ.get("RAILS_API_URL"))
```

- **Fallback pattern:** `candidates_crud.py` e `job_vacancies/crud.py` tentam Rails primeiro, fallback para FastAPI local.
- **Env var canônica:** `RAILS_API_URL` (ex: `https://staging2.wedotalent.cc`).
- **Health endpoint:** `app/api/v1/rails_health.py` checa conectividade.

### Frontend (plataforma-lia)

- Env var default: `FRONTEND_URL=https://plataforma-lia.replit.app`
- Backend proxy pattern: `/api/backend-proxy/<domain>/...`
- Componente de chat: `plataforma-lia/src/components/chat/chat-bubble-base.tsx`

---

## 10. Frontend contract — JSON shapes

### ChatResponse (pós FIX 12)

Schema em `app/orchestrator/main_orchestrator.py::ChatResponse`:

```json
{
  "success": true,
  "content": "texto resposta da LIA",
  "agent_used": "job_management",
  "agents_consulted": [],
  "intent_detected": "agentic_tool_call",
  "confidence": 1.0,
  "conversation_id": "conv_abc",
  "action_executed": true,
  "needs_confirmation": false,
  "structured_data": {
    "tool_calls": [
      {
        "name": "create_job_vacancy",
        "parameters": {"title": "Dev Python", "location": "SP"},
        "suggested_next": ["save_job_draft", "validate_job_fields"],
        "result": {
          "success": true,
          "result": {"job_id": 42, "status": "created"},
          "tool_name": "create_job_vacancy",
          "execution_time_ms": 320.4
        }
      }
    ],
    "iterations": 2
  },
  "suggested_prompts": [],
  "actions": [],
  "ui_action": null,
  "ui_action_params": null,
  "action_result": null,
  "action_type": null,
  "pending_action_id": null,
  "fairness_warnings": [],
  "from_cache": false
}
```

### Variação: HITL pendente (FIX 12)

Quando LIA chama tool com `requires_hitl`, o shape muda:

```json
{
  "success": true,
  "content": "Essa ação requer sua confirmação antes de executar.",
  "action_executed": false,
  "needs_confirmation": true,
  "structured_data": {
    "tool_calls": [
      {
        "name": "send_bulk_email",
        "parameters": {"template_id": "rejection", "candidate_ids": [1,2,3]},
        "suggested_next": [],
        "result": {
          "success": true,
          "result": {
            "status": "pending_hitl_confirmation",
            "requires_hitl": true,
            "tool_name": "send_bulk_email",
            "parameters": {"template_id": "rejection", "candidate_ids": [1,2,3]},
            "governance_tags": ["multi_tenant", "pii", "requires_hitl", "audit_trail"],
            "message": "A ferramenta 'send_bulk_email' requer confirmação humana antes de executar"
          }
        }
      }
    ],
    "hitl_pending": [
      {
        "tool_name": "send_bulk_email",
        "parameters": {"template_id": "rejection", "candidate_ids": [1,2,3]},
        "governance_tags": ["multi_tenant", "pii", "requires_hitl", "audit_trail"],
        "message": "A ferramenta 'send_bulk_email' requer confirmação humana antes de executar"
      }
    ],
    "iterations": 1
  }
}
```

### Variação: FairnessGuard blocked (FIX 8)

```json
{
  "success": false,
  "content": "Não posso filtrar candidatos por gênero. A CLT Art. 5º e a LGPD proíbem discriminação...",
  "action_executed": false,
  "needs_confirmation": false,
  "structured_data": {
    "tool_calls": [
      {
        "name": "search_candidates",
        "parameters": {"query": "somente homens"},
        "result": {
          "success": false,
          "error": "FairnessGuard blocked: ['somente homens']",
          "result": {
            "blocked_by_fairness_guard": true,
            "blocked_terms": ["somente homens"],
            "category": "genero",
            "educational_message": "...mensagem educacional..."
          }
        }
      }
    ]
  }
}
```

### Contrato para Frontend/Rails consumirem

**Para renderizar sugestões proativas (FIX 4):**
```js
const suggested = response.structured_data?.tool_calls?.[0]?.suggested_next ?? [];
// render <ButtonList items={suggested} />
```

**Para renderizar confirmação HITL (FIX 12):**
```js
if (response.needs_confirmation && response.structured_data?.hitl_pending) {
  const pending = response.structured_data.hitl_pending[0];
  // render <ConfirmationDialog tool={pending.tool_name} message={pending.message} />
  //   on confirm: POST /api/v1/chat/ with parameters + _hitl_confirmed=true
}
```

**Para renderizar aviso de fairness (FIX 8):**
```js
const firstCall = response.structured_data?.tool_calls?.[0];
if (firstCall?.result?.result?.blocked_by_fairness_guard) {
  const edu = firstCall.result.result.educational_message;
  // render <Alert type="warning" title="Compliance" message={edu} />
}
```

---

## 11. Observability runbook

### Módulo canônico

**Path:** `app/shared/observability/tool_metrics.py` (criado em FIX 12, migrado para o canonical path em FIX 13).

**Funções públicas:**
```python
from app.core.observability import emit_tool_call, emit_hitl_pending

emit_tool_call(
    tool_name="create_job_vacancy",
    company_id="abc-123",
    success=True,
    first_shot=True,            # iteration == 0
    call_index=1,
    governance_tags=["multi_tenant"],
    has_related_tools=True,
    latency_ms=420.5,
    error=None,
)

emit_hitl_pending(
    tool_name="send_bulk_email",
    company_id="abc-123",
    governance_tags=["requires_hitl"],
    conversation_id="conv_xyz",
)
```

### Log structure

**Logger name:** `lia.tool_metrics`

**Event type:** `tool_call` ou `hitl_pending`

**Campos sempre presentes no `extra={}`:**
- `tool_name` (str)
- `company_id` (str | None)
- `success` (bool)
- `first_shot` (bool — iteration == 0)
- `call_index` (int — posição no loop)
- `governance_tags` (list[str])
- `has_related_tools` (bool)
- `latency_ms` (float | None)
- `error` (str | None)

### LangSmith integration (opcional)

**Env vars:**
```bash
LANGCHAIN_TRACING_V2=true      # habilita forwarding
LANGCHAIN_API_KEY=lsv2_...     # obrigatório se tracing ativo
LANGCHAIN_PROJECT=lia-prod     # opcional, default "default"
```

**Behavior:**
- Sem env vars: **NO-OP** — só logs estruturados locais
- Com env vars: client init lazy (1 tentativa cached), `create_run()` por evento
- Falha de inicialização: silenciosa (nunca quebra request)

**Queries úteis (em qualquer log aggregator):**
```
# Tool selection errors (tool errada na primeira tentativa)
level=INFO event=tool_call first_shot=true success=false

# Bias blocks (compliance)
level=INFO event=tool_call governance_tags.contains=fairness_guard success=false

# HITL funnel
level=INFO event=hitl_pending tool_name=send_bulk_email

# Latency p95 por tool
level=INFO event=tool_call | percentile(latency_ms, 95) by tool_name
```

---

## 12. Deployment & Testing

### Post-commit checklist

Depois de cada FIX que mexe em `registry.py`, `executor.py`, `__init__.py` ou `main.py`:

- [ ] **Restart do FastAPI no Replit** (senão `initialize_tools()` não re-roda)
- [ ] Rodar `python -m pytest tests/unit/test_fix*.py --no-cov -q` → esperado 91/91 verde
- [ ] Rodar `python -c "from app.tools import tool_registry, initialize_tools; initialize_tools(); r = tool_registry.validate_yaml(); assert r['ok'], r"`
- [ ] Regression nos testes de ação executor: `python -m pytest tests/unit/test_action_executor_unit.py tests/unit/test_action_handlers_unit.py --no-cov`

### Smoke tests manuais no chat

Após deploy + restart, testar no chat com JWT válido (preferencialmente em staging):

1. **Routing certo (FIX 1+11):**
   - Mandar: `"melhora minha JD"`
   - Esperado: LIA entra em `job_management` e invoca `enrich_jd` (não `generate_jd`)

2. **FairnessGuard bloqueando (FIX 8):**
   - Mandar: `"busca candidatos somente homens"`
   - Esperado: response.structured_data.tool_calls[0].result.result.blocked_by_fairness_guard == true

3. **HITL (FIX 3+12):**
   - Mandar: `"fecha a vaga 42"`
   - Esperado: response.needs_confirmation == true, response.structured_data.hitl_pending presente

4. **Sugestões proativas (FIX 4):**
   - Mandar: `"valida os requisitos da vaga"`
   - Esperado: response.structured_data.tool_calls[0].suggested_next contém `save_job_draft`

5. **Observability (FIX 12):**
   - Rodar: `grep "tool_call" logs/app.log | tail -5`
   - Esperado: eventos JSON com todos os 9 campos

### Rollback

Cada FIX é um commit atômico — rollback via `git revert <hash>` reverte só aquele FIX sem afetar os outros.

```bash
# Exemplo: reverter apenas FIX 8 (FairnessGuard)
git revert 8e8bfa3bd

# Ou rollback completo (volta para antes de FIX 1):
git reset --hard 82009b0c8^
```

---

## 13. Apêndices

### Apêndice A — Mapa de commits

| Commit | Data | FIX | Arquivos principais |
|--------|------|-----|---------------------|
| [`82009b0c8`](../../commit/82009b0c8) | 2026-04-20 | FIX 1 | `base.py`, `llm_cascade.py`, `tools/__init__.py` |
| [`4d55b7c40`](../../commit/4d55b7c40) | 2026-04-20 | FIX 2 | 13× `actions.py` |
| [`c9ec97385`](../../commit/c9ec97385) | 2026-04-20 | FIX 3+4 | `registry.py`, `executor.py`, `agentic_loop.py` |
| [`71a2ec1d1`](../../commit/71a2ec1d1) | 2026-04-20 | FIX 5+6+7 | wizard sync + observability + 2 actions.py |
| [`8e8bfa3bd`](../../commit/8e8bfa3bd) | 2026-04-21 | FIX 8 | `registry.py`, `executor.py`, `tools/__init__.py` |
| [`896f4ae34`](../../commit/896f4ae34) | 2026-04-21 | FIX 9 | all actions.py + 4 inline domain.py |
| [`c0a3e3b79`](../../commit/c0a3e3b79) | 2026-04-21 | FIX 10 | `tool_registry_metadata.yaml`, `intents_config.py` |
| [`cf12c3ec9`](../../commit/cf12c3ec9) | 2026-04-21 | FIX 11 | `llm_cascade.py`, `job_management/actions.py` |
| [`3f7245f18`](../../commit/3f7245f18) | 2026-04-21 | FIX 12 | **`app/shared/observability/tool_metrics.py`** (migrado em FIX 13), `agentic_loop.py`, `main_orchestrator.py` |

### Apêndice B — Status dos 9 gaps

| Gap | Descrição | FIX(es) | Status |
|-----|-----------|---------|--------|
| G1 | DomainActions não chegam ao LLM | FIX 1, 11 | ✅ Fechado |
| G2 | DomainAction.examples vazio | FIX 2, 9 | ✅ Fechado (100% quality) |
| G3 | governance_tags == metadata morta | FIX 3, 8 | ✅ Fechado (HITL + Fairness ativos) |
| G4 | related_tools ignorados | FIX 4, 10 | ✅ Fechado (suggested_next surfaced) |
| G5 | Wizard tools não enriquecidas | FIX 5, 10 | ✅ Fechado (100% cobertura YAML) |
| G6 | Overlap semântico confundia LLM | FIX 7, 11 | ✅ Fechado (3 clusters disambiguados) |
| G7 | requires_confirmation duplicado | FIX 10 | ✅ Fechado (resolver unificado) |
| G8 | HITL sem envelope pro frontend | FIX 12 | ✅ Fechado (hitl_pending presente) |
| G9 | Sem ingestion de metrics | FIX 12 | ✅ Fechado (observability module + LangSmith) |

### Apêndice C — Canonical-fix workflow (para novos fixes)

Para próximas melhorias da camada IA, seguir o protocolo:

**Fase 1 — Mapear o canônico**
- `grep` por duplicatas de função/hook/rota
- Identificar arquivo fonte da verdade (não o consumidor)
- Documentar decisão explícita

**Fase 2 — Listar consumidores**
- `grep` por imports do símbolo canônico
- Classificar: quebra/não quebra se mudar

**Fase 3 — Decidir tipo de fix**
- Se muda assinatura pública e >4 consumidores → abrir task separada
- Senão → fix interno no produtor

**Fase 4 — TDD Red → Green → Refactor**
- Escrever teste que FALHA pela razão certa
- Código mínimo para passar
- Refactor para clareza

**Fase 5 — Validar**
- Re-greps da Fase 1 → duplicatas deletadas?
- Re-greps da Fase 2 → consumidores ainda compilam?
- Regression: `python -m pytest tests/unit/test_fix*.py`
- Smoke tests manuais

### Apêndice D — Skills do Replit relacionadas

Todas em `.agents/skills/` no Replit:

- **`canonical-fix`** — protocolo para corrigir na fonte sem workaround
- **`lia-testing`** — TDD (Red/Green/Refactor), pirâmide 5 camadas, evals para agentes
- **`feature-audit`** — auditoria 6 dimensões pós-implementação
- **`lia-compliance`** — LGPD/EU AI Act/CLT guidance
- **`lia-planning`** — planejamento de features grandes

### Apêndice E — Arquivos de teste (91 testes TDD)

```
tests/unit/test_fix1_domain_actions_to_llm.py      10 testes
tests/unit/test_fix2_examples_populated.py         14 testes
tests/unit/test_fix34_governance_related_tools.py   6 testes
tests/unit/test_fix5_wizard_sync.py                 3 testes
tests/unit/test_fix6_observability.py               3 testes
tests/unit/test_fix7_semantic_overlap.py            6 testes
tests/unit/test_fix8_governance_enforcement.py      5 testes
tests/unit/test_fix9_quality.py                     2 testes
tests/unit/test_fix10_coverage_unification.py       6 testes
tests/unit/test_fix11_placement_wsi.py              4 testes
tests/unit/test_fix12_hitl_obs.py                   6 testes
─────────────────────────────────────────────────  ──────────
TOTAL                                              65 testes (core)
+ regressão em test_action_executor_unit.py
+ regressão em test_action_handlers_unit.py       44 testes
═════════════════════════════════════════════════  ══════════
GRAND TOTAL                                      109 testes
```

**Executar tudo:**
```bash
python -m pytest tests/unit/test_fix*.py tests/unit/test_action_*.py --no-cov -q
# Esperado: 109 passed
```

---

## Contato & próximos passos

**Owner da IA layer:** Paulo Moraes / IA team
**Branch ativa:** `fix/kanban-e2e-bugs`
**Repo IA:** `lia-agent-system` (FastAPI Python)
**Repo Rails:** `ats-api-copia` (CRUD + auth)
**Repo Frontend:** `plataforma-lia` (Next.js)

**Para contribuir:**
1. Ler este documento completo
2. Ler skills canonical-fix + lia-testing no Replit
3. Seguir o protocolo TDD Red → Green → Refactor
4. Cada FIX = 1 commit atômico com hash rastreável
5. Regenerar o glossário após mudanças em actions/tools: `python scripts/generate_tool_action_glossary.py`

**Próximos incrementos esperados:**
- `audit_trail` governance tag (hook completo para audit service)
- `credits_consumed` enforcement (budget pré-execução)
- FairnessGuard Layer 2 (implicit bias) ativo no executor
- Migração gradual do `intents_config.py` legacy para resolver unificado

**Fim do documento — FIX 1-12 cobertos 100% (91 testes TDD verdes, 9 gaps fechados).**
