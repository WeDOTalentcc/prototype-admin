# ADR-029 — ToolDefinition Unification + Runtime Context Wrapper

**Status**: Accepted (Sprint 1B Sprint 1C landed; Sprint 3 RuntimeContext pending)
**Data**: 2026-05-06
**Contexto**: Wizard bug audit revelou 2 ToolDefinition classes coexistindo + 145 tenant ID leaks
**Sprint**: Q2 Canonical Refactor (Sprint 0)

---

## Contexto

Sistema atual tem **2 classes ToolDefinition** diferentes:

1. `app/tools/registry.py:ToolDefinition` (dataclass, 16 campos)
   - Usada em ~20 arquivos via `from app.tools.registry import ToolDefinition, tool_registry`
   - Schemas em campo `parameters_schema: Dict[str, Any]`

2. `lia_agents_core.react_loop.ToolDefinition` (Pydantic BaseModel, 30+ campos)
   - Usada em ~40 arquivos via `from lia_agents_core.react_loop import ToolDefinition`
   - Schemas em campo `parameters: Dict[str, Any]`
   - Tem flags governance: `requires_company_id`, `touches_pii`, `lgpd_legal_basis`, etc.

### Inventário (verificado)

```
$ grep -rn "^class.*ToolDefinition\b" app/ libs/
app/tools/registry.py:16:class ToolDefinition:
libs/agents-core/lia_agents_core/react_loop.py: class ToolDefinition

$ find app -name "*tool*.py" -o -name "*registry*.py" | wc -l
62 files

$ grep -rln "from.*ToolDefinition\|import.*ToolDefinition" app/ | wc -l
54 importers
```

### Problemas observados (bug 2026-05-06)

1. **Schema fields divergentes**: `parameters` vs `parameters_schema`
2. **Tenant IDs misturados com user-facing params**: 145 ocorrências de `company_id` em schemas (limpas tactically em commits 5b4c351c3 + f6417ba70)
3. **Sem runtime context wrapper**: handler tem que ler `kwargs.get("company_id")` manualmente
4. **Anti-pattern enterprise**: OpenAI Assistants, Anthropic Tool Use, LangGraph all separate user-facing schema from runtime context

---

## Decisão

### 1. **Adotar `lia_agents_core.react_loop.ToolDefinition` como canonical**

Razão: já tem governance fields (`requires_company_id`, `touches_pii`, `lgpd_legal_basis`, `affects_candidate_decision`) que `app/tools/registry.py` não tem.

`app/tools/registry.py:ToolDefinition` é deprecated. Migration plan:
- 20 arquivos atualizados para importar de `lia_agents_core`
- Field rename: `parameters_schema` → `parameters`
- `tool_registry` (global) deprecated em favor de domain-specific registries

### 2. **Tool schemas: APENAS user-facing parameters**

Tenant IDs (`company_id`, `tenant_id`, `organization_id`) **PROIBIDOS** em `parameters` properties/required.

```python
# ANTI-PATTERN (proibido)
parameters = {
    "properties": {
        "title": {...},
        "company_id": {...},  ❌ tenant context
    }
}

# CANONICAL
parameters = {
    "properties": {
        "title": {...},   ✅ user-facing only
    }
}
```

### 3. **Runtime Context Wrapper (NEW)**

Tools recebem context via decorator/wrapper, não via tool call:

```python
# app/tools/runtime_context.py (NOVO)

from contextvars import ContextVar
_current_runtime_ctx: ContextVar["RuntimeContext"] = ContextVar("runtime_ctx")

@dataclass
class RuntimeContext:
    company_id: str
    user_id: str
    user_role: str
    request_id: str
    # ... outros campos do JWT/session

def with_runtime_context(injects: list[str]):
    """Decorator para tool handlers — injeta context da ContextVar.
    
    Usage:
        @with_runtime_context(injects=["company_id", "user_id"])
        async def create_job(title: str, *, company_id: str, user_id: str):
            # company_id/user_id vêm do middleware-set ContextVar
    """
    def decorator(fn):
        @wraps(fn)
        async def wrapper(**llm_args):
            ctx = _current_runtime_ctx.get()
            for key in injects:
                llm_args[key] = getattr(ctx, key)
            return await fn(**llm_args)
        return wrapper
    return decorator
```

Middleware (`app/middleware/auth_enforcement.py`) seta `_current_runtime_ctx` no início de cada request. Tool handlers leem via decorator.

### 4. **Sensor blocking**

`scripts/check_no_tenant_in_tool_schemas.py` (já existe) **promovido para blocking** após Sprint 3 completo.

Adicionar novo sensor: `check_tool_handlers_use_runtime_context.py` — detecta handlers que recebem `company_id` como parâmetro normal (não via decorator).

---

## Migration plan (Sprint 3)

| Phase | Task | Esforço |
|---|---|---|
| 3.1 | Criar `RuntimeContext` + `with_runtime_context` decorator + tests | 6h |
| 3.2 | Wire middleware: `_current_runtime_ctx.set(RuntimeContext(...))` | 2h |
| 3.3 | Migrate 20 tools de `app/tools/registry.py` → `lia_agents_core.react_loop` | 8h |
| 3.4 | Migrate 40 tool handlers para usar `@with_runtime_context` | 12h |
| 3.5 | Sensor warn → blocking | 1h |
| 3.6 | Deprecate + delete `app/tools/registry.py:ToolDefinition` | 2h |
| **Total** | | **~31h** |

---

## Consequências

### Positivas
- ✅ 2 → 1 ToolDefinition class
- ✅ Schemas só user-facing (LLM nunca vê tenant)
- ✅ Handler signature simplificada
- ✅ Multi-tenancy fail-closed at decorator level (computational)
- ✅ Alinha com OpenAI Assistants, Anthropic Tool Use, LangGraph

### Negativas
- ⚠️ ~31h refator
- ⚠️ Risco regressão (mitigado por sensor + tests)
- ⚠️ Backward compat: handlers existentes que recebem `company_id` precisam atualizar

### Reversibilidade
Reversível durante migration. Após Sprint 3 + sensor blocking, custo alto.

---

## Métricas de sucesso

- ToolDefinition classes: 2 → 1
- Tool schemas com tenant ID: 0 (já zerado tactically; bloqueia regressão)
- Handlers usando runtime context decorator: 100% (40+)
- Sensor `check_no_tenant_in_tool_schemas`: blocking
- Sensor `check_tool_handlers_use_runtime_context`: blocking
- Tests: handler signature uniforme

---

## Referências

- Bug origem: sessão Sprint B+ wizard "ID empresa"
- ADR-001 (Repository Pattern)
- ADR-027 (Legacy /api/wsi decommission) — padrão similar
- CLAUDE.md REGRA 1 (multi-tenancy)
- OpenAI Function Calling Guide (separação user-args vs context)
- LangGraph Tools docs (bind_tools com context)
