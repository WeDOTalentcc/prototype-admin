# ADR-019 — Governance Enforcement & Observability (FIX 8 + FIX 12)

**Status:** Accepted
**Date:** 2026-04-21
**Authors:** Paulo Moraes / IA Team
**Related commits:** `8e8bfa3bd` (FIX 8), `3f7245f18` (FIX 12)
**Supersedes:** — (novo ADR, complementa ADR-016 e ADR-018)

---

## Contexto

Até 2026-04-20, a plataforma LIA tinha:

1. **`governance_tags`** declaradas em 88 ferramentas no `tool_registry_metadata.yaml` (valores: `pii`, `fairness_guard`, `requires_hitl`, `multi_tenant`, `audit_trail`, `credits_consumed`, `write_destructive`), mas **o `ToolExecutor` não checava nenhuma delas**. Tags eram metadata morta.
2. **`FairnessGuard`** implementado em `app/shared/compliance/fairness_guard.py` com 3 camadas (regex L1, ML L2, semantic L3), mas **nunca invocado pelo `ToolExecutor`**. Era usado apenas como middleware FastAPI em alguns endpoints específicos.
3. **Métricas de tool selection** existiam como `logger.info("tool_call", ...)` inline em `agentic_loop.py`, mas sem canal de ingestion. Logs ficavam locais, sem visibilidade agregada. Impossível medir first-shot rate, bias block rate, HITL funnel.
4. **HITL** (Human-in-the-Loop) existia como campo em `DomainAction.requires_confirmation` e `intents_config.requires_confirmation` (duas fontes paralelas), mas **nenhum enforcement ativo** no executor.

Esse conjunto violava LGPD Art. 12 (minimização de dados pessoais em decisões de IA) e CF Art. 5º (proibição de discriminação em processos seletivos), além de deixar o time cego para métricas de qualidade do LLM.

---

## Decisão

### Decisão 1 — FairnessGuard enforcement no ToolExecutor (FIX 8)

Toda ferramenta marcada `governance_tags=[..., "fairness_guard", ...]` passa a ter seus parâmetros de texto (`query`, `description`, `content`, `prompt`, etc.) escaneados pelo `FairnessGuard.check()` **antes** de chamar o handler. Se Layer 1 (regex) detectar viés explícito (ex: `"somente homens"`), a execução é bloqueada e retornada como:

```python
ToolResult(
    success=False,
    error=f"FairnessGuard blocked: {blocked_terms}",
    result={
        "blocked_by_fairness_guard": True,
        "blocked_terms": [...],
        "category": "genero" | "raca_etnia" | "idade" | ...,
        "educational_message": "...",
    },
)
```

**Escolha técnica:** apenas Layer 1 (regex) no hot-path. Layer 2 (ML) e Layer 3 (semantic LLM) são caros e não-determinísticos — ficam para endpoints específicos que podem arcar com a latência.

### Decisão 2 — HITL via ToolResult.pending_hitl_confirmation (FIX 3)

Toda ferramenta marcada `governance_tags=[..., "requires_hitl", ...]` que receba parâmetros SEM `_hitl_confirmed=True` retorna imediatamente:

```python
ToolResult(
    success=True,  # é sucesso porque respondeu — só não executou
    result={
        "status": "pending_hitl_confirmation",
        "requires_hitl": True,
        "tool_name": ...,
        "parameters": ...,          # re-enviar com _hitl_confirmed=True para bypass
        "governance_tags": [...],
        "message": "...",
    },
)
```

O `main_orchestrator` promove isso para `ChatResponse.structured_data.hitl_pending` e seta `needs_confirmation=True` (FIX 12). Frontend renderiza diálogo de confirmação; ao confirmar, refaz a chamada com `_hitl_confirmed=True`.

**Escolha técnica:** `_hitl_confirmed` como parameter mágico no handler call (não campo separado na API) para minimizar superfície de mudança no frontend.

### Decisão 3 — Observability module centralizado (FIX 12)

Criar `app/core/observability.py` como **único ponto** de emissão de eventos de tool call:

```python
def emit_tool_call(
    *,
    tool_name: str,
    company_id: str | None,
    success: bool,
    first_shot: bool,
    call_index: int,
    governance_tags: list[str] | None = None,
    has_related_tools: bool = False,
    latency_ms: float | None = None,
    error: str | None = None,
) -> None:
    """Always emits structured log; optionally forwards to LangSmith."""
```

- Sempre emite `logger.info("tool_call", extra={...})`
- Forwarding opcional ao LangSmith gated por `LANGCHAIN_TRACING_V2=true` + `LANGCHAIN_API_KEY`
- Lazy-init + cached do client (1 tentativa)
- **Nunca raises** — observability falha silenciosa para não quebrar request flow

### Decisão 4 — Resolver de `requires_confirmation` (FIX 10)

Duas fontes paralelas (intent-level em `ACTIONABLE_INTENTS` e action-level em `DomainAction`) serviam propósitos diferentes. Em vez de forçar unificação (que destruiria semântica), criou-se um resolver com **precedência intent > action > False**:

```python
def resolve_requires_confirmation(intent: str | None, action_id: str | None) -> bool:
    if intent and intent in ACTIONABLE_INTENTS:
        return ACTIONABLE_INTENTS[intent]["requires_confirmation"]
    if action_id:
        domain = DomainRegistry().get_domain_for_action(action_id)
        if domain:
            action = domain.get_action_by_id(action_id)
            return bool(getattr(action, "requires_confirmation", False))
    return False  # safe default
```

---

## Alternativas consideradas (rejeitadas)

### Alt 1 — FairnessGuard Layer 2/3 no hot-path
Rejeitado: Layer 2 (ML) adiciona ~200-500ms por chamada. Layer 3 (LLM semantic) adiciona ~2-5s e custa tokens. Bloqueio inline quebraria UX do chat.
**Trade-off aceito:** viés implícito mais sutil pode passar. Mitigação: `fairness_warnings` array em `ChatResponse` populado pelos middlewares FastAPI nos endpoints críticos (não inline).

### Alt 2 — HITL via campo separado na resposta
Rejeitado: exigiria mudança coordenada em 3 repos (IA Python, Rails, Frontend). A solução `parameters["_hitl_confirmed"]` é internal-only e não quebra contratos públicos.

### Alt 3 — Unificar `requires_confirmation` forçando uma fonte vencer
Rejeitado: `ACTIONABLE_INTENTS[intent]["requires_confirmation"]` captura contexto específico de invocação (ex: `reject_candidate` intent tem `False` porque o handler gerencia o próprio gate). `DomainAction.requires_confirmation` é a propriedade geral da ação. São sinais diferentes — eliminar um perderia informação.

### Alt 4 — Adicionar LangSmith como dependência obrigatória
Rejeitado: `langsmith` é opcional no projeto (outros endpoints já fazem import condicional). Manter o mesmo padrão: `try/except ImportError` + env var gate.

---

## Consequências

### Positivas

- **Compliance LGPD ativo** — viés explícito bloqueado no executor, educational message volta pro usuário
- **HITL enforcement real** — tools sensíveis não executam sem confirmação
- **Métricas mensuráveis** — first-shot rate, governance-tag distribution, HITL funnel observáveis
- **Source of truth unificada para confirmation** — resolver único, precedência clara
- **Backwards compatible** — `_hitl_confirmed` e governance_tags adicionais não quebram código legado
- **Non-blocking observability** — emit_tool_call NUNCA levanta exceção; LangSmith totalmente opcional

### Negativas / Trade-offs

- **Fairness Layer 1 cobre apenas viés explícito (regex)** — frases sutis como "buscar candidato jovem e dinâmico" não são pegos. Mitigação: fairness middleware nos endpoints críticos + Layer 3 em revisão de JD antes de publicar.
- **`_hitl_confirmed` leaked via parameters** — pequeno acoplamento. Alternativa "campo separado no contexto de execução" foi considerada mas adicionaria mais superfície.
- **Duas fontes de `requires_confirmation`** — mantidas vivas. Pode confundir. Mitigação: resolver canônico documentado + doc-comment nos dois lados apontando pro resolver.
- **Logging depende de env vars corretas** — em dev/staging sem `LANGCHAIN_*`, apenas logs locais. Mitigação: documentado no handoff (seção 11).

---

## Validação

### Testes TDD

- `tests/unit/test_fix8_governance_enforcement.py` — 5 testes (side_effects field, YAML sync, FairnessGuard block, neutral pass, no-tag skip)
- `tests/unit/test_fix10_coverage_unification.py` — 6 testes (resolver exists, intent precedence, action fallback, safe default)
- `tests/unit/test_fix12_hitl_obs.py` — 6 testes (module exists, LangSmith disabled by default, agentic_loop uses helper, HITL envelope)

### Smoke tests manuais

1. `"busca candidatos somente homens"` → FairnessGuard block visible no `structured_data`
2. `"envia email pra todos os reprovados"` → `hitl_pending` no envelope, `needs_confirmation=true`
3. `emit_tool_call()` com env vars vazias → no-op silencioso
4. `emit_tool_call()` com `LANGCHAIN_TRACING_V2=true` + chave → span no LangSmith

### Observabilidade

Queries úteis em LangSmith / log aggregator:
- `event=tool_call first_shot=true success=false` → tool selection errors (proxy para LLM quality)
- `event=tool_call governance_tags.contains=fairness_guard success=false` → bias block rate
- `event=hitl_pending` → HITL funnel (frequência de confirmações humanas)

---

## Referências

- ADR-016 — Tool Registration Canonical (`tool_registry.register()` centralized)
- ADR-018 — Tool Registry Consolidation Migration
- **Código canônico:**
  - `app/tools/executor.py` — `ToolExecutor._check_fairness()`, HITL gate
  - `app/core/observability.py` — `emit_tool_call()`, `emit_hitl_pending()`
  - `app/orchestrator/action_executor/intents_config.py` — `resolve_requires_confirmation()`
  - `app/shared/compliance/fairness_guard.py` — `FairnessGuard.check()`
- **Legislação:**
  - LGPD Art. 12 — minimização de dados pessoais
  - CF Art. 5º + Lei 7.716/89 — proibição de discriminação
  - Lei 9.029/95 — discriminação em processos seletivos
  - EU AI Act Art. 13 — transparência em IA de alto risco

---

## Addendum — FIX 13 (canonical-path migration)

**Commit:** `<TBD after commit>`  ·  **Date:** 2026-04-21

O módulo criado em FIX 12 em `app/core/observability.py` foi migrado para o path canônico `app/shared/observability/tool_metrics.py` conforme Section 1 de `docs/specs/CANONICAL_SOURCES_SPEC.md` (todo observability deve ficar sob `app.shared.observability.*`).

Mudanças:
- `git mv app/core/observability.py app/shared/observability/tool_metrics.py`
- Imports atualizados em `agentic_loop.py`, `main_orchestrator.py` e 2 test files
- Refactor para reutilizar `app.shared.observability.langsmith.is_langsmith_enabled()` (evita duplicação do check de env var)
- `CANONICAL_SOURCES_SPEC.md` §1.1 atualizado com o novo módulo; §1.2 bloqueia o path legado; §7 removeu o TODO de migração

Todos os 65 testes FIX 1-12 permanecem verdes após a migração.
