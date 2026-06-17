# Theme I2 — Tool Architecture

**Layer:** Infrastructure  |  **Última verificação de código:** 2026-04-24
**Fonte de verdade:** `lia-agent-system/app/shared/tool_handler.py` + `app/tools/` no Replit

---

## O que é este tema

O sistema de **ferramentas (tools)** da LIA é a camada de execução de ações concretas. As ferramentas são funções Python async chamadas pelo LangGraph ReAct loop quando o LLM decide que precisa de informação ou quer executar uma ação. Cada tool tem:

1. **Handler Python** — função async decorada com `@tool_handler(domain, require_company, module)` que executa a lógica real
2. **Metadados YAML** — `tool_registry_metadata.yaml` declara nome, descrição (enviada ao LLM), `allowed_agents`, `scope` e parâmetros JSONSchema
3. **Permissões YAML** — `tool_permissions.yaml` organiza tools por scope (TALENT_FUNNEL/JOB_TABLE/IN_JOB/GLOBAL) e lista tools destrutivas

**Boundary com temas irmãos:**
- **I1 Agent Architecture** — agentes chamam `_get_tools()` que retorna LangChain tools; `TimedToolNode` executa com timeout + FairnessGuard
- **I3 Orchestration** — o `ActionExecutor` chama tools diretamente em alguns fluxos (não apenas via ReAct)
- **C1 Fairness** — `TimedToolNode` aplica `FairnessGuard` em tool call args (LIA-C03)
- **C8 Module Gating** — `@tool_handler(module="bulk_actions")` aplica gating de billing

---

## Arquivos conectados (5 Python + 2 YAML)

### Camada Config (Python lê — 2 YAMLs)

| Arquivo | Path canônico | Quando é consumido |
|---------|---------------|--------------------|
| `tool_registry_metadata.yaml` | `app/tools/tool_registry_metadata.yaml` | Startup via `validate_registry_against_yaml()` + por `load_tool_metadata()` em runtime |
| `tool_permissions.yaml` | `app/tools/tool_permissions.yaml` | Lido pelo `CascadedRouter` (I3) para verificar escopo antes de rotear |

### Camada Código (5 arquivos Python)

| Arquivo | Path canônico | Linhas | Responsabilidade |
|---------|---------------|:---:|-----------------|
| `tool_handler.py` | `app/shared/tool_handler.py` | 207 | Decorator `@tool_handler` — company_id check + module gating + error handling + response formatting |
| `tool_registry_loader.py` | `app/tools/tool_registry_loader.py` | 156 | `load_tool_metadata()`, `export_registry_to_yaml()`, `validate_registry_against_yaml()` |
| `tool_adapter.py` | `libs/agents-core/lia_agents_core/tool_adapter.py` | 71 | `ToolDefinition` schema + `tool_definition_to_langchain_tool()` — adapta para `StructuredTool` LangChain |
| `timed_tool_node.py` | `libs/agents-core/lia_agents_core/timed_tool_node.py` | 356 | `TimedToolNode` — executa tools com timeout 15s + FairnessGuard (LIA-C03) + métricas |
| `app/domains/<X>/tools/<domain>_tools.py` | por domínio | varies | Implementação dos handlers por domínio (pipeline, sourcing, wizard, etc.) |

### Integration points

- **Agentes** (I1) chamam `_get_tools()` → lista de `StructuredTool` LangChain → passada para `create_react_agent()`
- **TimedToolNode** (I1/I2) executa cada tool com `asyncio.wait_for(timeout)` + FairnessGuard
- **CascadedRouter** (I3) usa `tool_permissions.yaml` para determinar escopo de ferramentas disponíveis por contexto
- **module_gating.py** (C8) chamado pelo `@tool_handler(module=...)` para gating de billing
- **tenant_llm_context** (C5) fornece `company_id` via contextvar como fallback 2 no decorator

---

## Lógica IN → OUT

### Decorator @tool_handler

```python
# Assinatura completa:
@tool_handler(
    domain: str,                  # ex: "pipeline", "sourcing", "wizard"
    require_company: bool = True, # se True, tool é bloqueada sem company_id
    module: Optional[str] = None, # ex: "bulk_actions" → aplica module gating (C8)
)
```

**Fluxo de execução do decorator:**

```
1. COMPANY_ID CHECK (quando require_company=True):
   a. kwargs.get("company_id")  ← argumento direto
   b. _context.company_id        ← AgenticLoop path (_context injetado)
   c. get_current_llm_tenant()   ← LangGraph contextvar (AuthEnforcementMiddleware)
   Se nenhum resolve → retorna {"success": False, "message": "Tenant isolation error..."}

2. MODULE GATING (quando module= fornecido):
   a. check_tool_module_access(func_name, company_id, db) → {allowed, status}
   b. allowed=False + TASTING_TOOLS → executa mas retorna partial_data (preview)
   c. allowed=False → build_degraded_response(func_name, module) com upgrade CTA
   d. status="beta" → envolve resposta com build_beta_response()

3. EXECUÇÃO:
   result = await func(**kwargs)

4. RESPONSE FORMATTING:
   a. Se result já tem "success" key → pass-through (tool controla o formato)
   b. Senão → {"success": True, "data": result, "message": "OK"}
   c. Exceção → {"success": False, "data": {}, "message": str(exc)}

5. BETA WRAPPER (se access_result.status == "beta"):
   result = build_beta_response(result, module)
```

**Resposta padrão de erro de tenant:**
```python
_TENANT_REQUIRED_RESPONSE = {
    "success": False,
    "data": {},
    "message": "Tenant isolation error: 'company_id' é obrigatório. "
               "Nenhuma query de dados pode ser executada sem contexto de tenant.",
}
```

### Padrão de tool handler (exemplo real — pipeline_tools.py)

```python
@tool_handler(domain="pipeline", require_company=True)
async def move_candidate_to_stage(
    candidate_id: str = "",
    job_id: str = "",
    new_stage: str = "",   # "applied"|"screening"|"interview"|"offer"|"hired"|"rejected"
    reason: str = "",
    **kwargs: Any,          # recebe company_id, db, _context, etc.
) -> dict:
    """Moves a candidate to a new stage in the hiring pipeline.
    [docstring enviada ao LLM como descrição da tool]
    """
    return {
        "candidate_id": candidate_id,
        "new_stage": new_stage,
        "reason": reason,
        "moved_at": datetime.now(UTC).isoformat(),
    }
    # tool_handler envolve em {"success": True, "data": {...}, "message": "OK"}
```

### ToolDefinition e adaptação LangChain

```python
# libs/agents-core/lia_agents_core/tool_adapter.py

class ToolDefinition(BaseModel):
    name: str              # identificador único
    description: str       # enviado ao LLM
    parameters: Dict[str, Any]  # JSONSchema dos argumentos
    function: Callable     # função async ou sync
    
    class Config:
        arbitrary_types_allowed = True

def tool_definition_to_langchain_tool(td: ToolDefinition) -> StructuredTool:
    # Converte para StructuredTool LangChain compatível com create_react_agent
    # Suporta async e sync automaticamente
```

**Uso em agente de domínio:**
```python
# em pipeline_tool_registry.py
from lia_agents_core.tool_adapter import ToolDefinition, tool_definition_to_langchain_tool
from app.domains.pipeline.tools.pipeline_tools import move_candidate_to_stage

_TOOLS_DEFS = [
    ToolDefinition(
        name="move_candidate_to_stage",
        description="Moves a candidate to a new stage in the hiring pipeline.",
        parameters={"type": "object", "required": ["candidate_id", "new_stage"], ...},
        function=move_candidate_to_stage,
    ),
    ...
]

ALL_TOOLS = [tool_definition_to_langchain_tool(td) for td in _TOOLS_DEFS]
```

### tool_registry_metadata.yaml — estrutura por tool

```yaml
# app/tools/tool_registry_metadata.yaml  — 1025 linhas, 85 tools
tools:
  - name: search_salary_benchmark
    description: Search for salary benchmark data for a given job role...
    allowed_agents: [job_planner, job_intake, orchestrator, job_wizard]
    scope: JOB_TABLE
    version: "1.0"
    parameters:
      type: object
      required: [job_title]
      properties:
        job_title: {type: string}
        seniority: {type: string}
        location: {type: string}
```

**Funções do loader:**
```python
# load_tool_metadata() → dict[tool_name, metadata_dict]
metadata = load_tool_metadata()  # usa _DEFAULT_YAML_PATH

# validate_registry_against_yaml() → {ok, missing_in_yaml, missing_in_registry, description_mismatches}
report = validate_registry_against_yaml(ALL_TOOLS)
if not report["ok"]:
    raise RuntimeError("Tool registry out of sync with YAML")

# export_registry_to_yaml() → YAML string (usa-se para regenerar o arquivo)
yaml_str = export_registry_to_yaml(ALL_TOOLS, path=Path("tool_registry_metadata.yaml"))
```

### tool_permissions.yaml — scopes e tools destrutivas

```yaml
# app/tools/tool_permissions.yaml  — 250 linhas
version: '1.0'
global:
  scopes:
    talent_funnel:    # candidatos no talent pool
      query:  [search_candidates, get_candidate_details, compare_candidates, ...]
      action: [add_candidate_to_vacancy, reject_candidate, send_email, ...]
    
    job_table:        # listagem de vagas
      query:  [search_jobs, get_job_details, get_pipeline_stats, ...]
      action: [create_job, update_job, pause_job, close_job, publish_job, ...]
    
    in_job:           # dentro de uma vaga específica
      query:  [get_job_details, get_vacancy_funnel, get_candidate_details, ...]
      action: [update_candidate_stage, bulk_update_candidates_stage, reject_candidate, ...]
    
    global:           # cross-context (disponível em todos os escopos)
      query:  [...]
      action: [...]

# Tools que exigem confirmação do usuário:
destructive_tools:
  - send_message       # mensagem WhatsApp/email para candidato
  - update_candidate_stage
  - publish_job
  - create_offer_letter
  - record_hiring_outcome
  - create_job
  - update_job
  - ...

tenants: {}  # overrides por tenant — suportado mas vazio (config vive no DB)
```

### Side effects

- **Audit log** (C7): `@tool_handler` não audita diretamente; o `AuditCallback` (I1) captura tool calls via LangGraph
- **Métricas** (I5): `TimedToolNode` emite `tool_call_duration_seconds{domain, tool}` + `tool_call_errors_total{domain, tool}`
- **Module gating** (C8): `check_tool_module_access()` gera `module_gate_denials_total` metric + audit log

### Escalation / HITL

| Cenário | Ação |
|---------|------|
| `company_id` ausente (require_company=True) | Retorna `_TENANT_REQUIRED_RESPONSE` imediatamente (fail-closed) |
| Module gating: plano insuficiente | Retorna `build_degraded_response()` com upgrade CTA (não crash) |
| Module gating: context incompleto (sem db) | Fail-closed: retorna `build_degraded_response()` + log WARNING |
| Exception dentro da tool | `tool_handler` captura + loga + retorna `{"success": False, "message": str(exc)}` |
| Tool timeout (>15s) | `TimedToolNode` injeta `ToolMessage` de erro no grafo (agente responde sem crash) |
| FairnessGuard bloqueia tool call | `TimedToolNode` não executa a tool + log + `FairnessViolation` no audit |

---

## Instruções para Claude Code / Cursor

### "Implementa Tool Architecture no v5"

```
1. COPIE arquivos base:
   cp app/shared/tool_handler.py  → <v5>/app/shared/tool_handler.py
   cp app/tools/tool_registry_loader.py → <v5>/app/tools/tool_registry_loader.py
   cp app/tools/tool_registry_metadata.yaml → <v5>/app/tools/tool_registry_metadata.yaml
   cp app/tools/tool_permissions.yaml → <v5>/app/tools/tool_permissions.yaml
   cp libs/agents-core/lia_agents_core/tool_adapter.py → <v5>/libs/agents-core/.../

2. VALIDAÇÃO na startup (app/main.py ou app/api/routes.py):
   from app.tools.tool_registry_loader import validate_registry_against_yaml
   from app.domains.<X>.agents.tool_registry import ALL_TOOLS
   report = validate_registry_against_yaml(ALL_TOOLS)
   if not report["ok"]:
       raise RuntimeError(f"Tool registry out of sync: {report}")

3. CONFIGURE tool_permissions.yaml para o escopo do v5
   (adicionar/remover tools conforme funcionalidades)

4. VERIFIQUE:
   - pytest tests/unit/test_tool_handler.py
   - pytest tests/unit/test_tool_registry_loader.py
```

### "Cria nova tool"

```
1. CRIE a função handler em app/domains/<domain>/tools/<domain>_tools.py:

   @tool_handler(domain="<domain>", require_company=True)
   async def my_new_tool(
       param1: str = "",
       param2: int = 0,
       **kwargs: Any,         # sempre incluir **kwargs (recebe company_id, db, etc.)
   ) -> dict:
       """Descrição enviada ao LLM — seja específico sobre o que a tool faz.
       
       Args:
           param1: ...
           param2: ...
       
       Returns:
           dict com os campos resultado.
       """
       # Lógica aqui — NÃO precisa fazer try/except (decorator trata)
       # NÃO precisa formatar {success, data, message} (decorator trata)
       # SÓ faça return da data diretamente:
       return {"result": "value"}

2. ADICIONE ToolDefinition no tool_registry do agente:
   # em app/domains/<domain>/agents/<domain>_tool_registry.py
   ToolDefinition(
       name="my_new_tool",
       description="Exatamente a mesma docstring da função",
       parameters={
           "type": "object",
           "required": ["param1"],
           "properties": {
               "param1": {"type": "string", "description": "..."},
               "param2": {"type": "integer", "description": "..."},
           }
       },
       function=my_new_tool,
   )

3. ADICIONE entrada em tool_registry_metadata.yaml:
   - name: my_new_tool
     description: "Exatamente a mesma docstring"
     allowed_agents: [<domain>]
     scope: IN_JOB   # ou TALENT_FUNNEL / JOB_TABLE / GLOBAL
     version: "1.0"
     parameters:
       type: object
       required: [param1]
       properties:
         param1: {type: string}

4. EXECUTE validação (não esqueça):
   validate_registry_against_yaml(ALL_TOOLS)  # deve retornar ok=True

5. TESTES:
   - Unit: mock company_id → tool retorna sucesso
   - Unit: sem company_id → retorna _TENANT_REQUIRED_RESPONSE (não 500)
   - Integration: agente chama tool e recebe resposta formatada
```

### "Gatea tool por plano de billing"

```
# 1. Adicione module= ao decorator:
@tool_handler(domain="pipeline", require_company=True, module="bulk_actions")
async def bulk_reject_candidates(...):

# 2. Registre o módulo em module_plans table (C8):
#    INSERT INTO module_plans (module_name, required_plan)
#    VALUES ('bulk_actions', 'enterprise');

# 3. Tool retorna automaticamente build_degraded_response() para plano insuficiente
#    com mensagem "Upgrade para Enterprise para usar esta feature"

# Para preview (TASTING_TOOLS): retorna dados parciais para trial tenants
# Adicionar tool name em TASTING_TOOLS em module_gating.py
```

### Setup em CLAUDE.md

```markdown
## Infrastructure: Tool Architecture (I2)

- **Decorator:** `@tool_handler(domain, require_company=True, module=None)` em todo handler
- **company_id:** Resolvido em 3 fallbacks — kwargs → _context → contextvar (nunca fail-open)
- **Formato de retorno:** Tool retorna dict direto; decorator envolve em {success, data, message}
- **YAML SSoT:** `tool_registry_metadata.yaml` (85 tools) — descrição, allowed_agents, scope, params
- **Escopo 4 níveis:** TALENT_FUNNEL / JOB_TABLE / IN_JOB / GLOBAL
- **Module gating:** `@tool_handler(module="feature_name")` + `module_plans` table (C8)
- **Nova tool:** handler.py → ToolDefinition → tool_registry_metadata.yaml → validate_registry_against_yaml()

Consultar `themes/infrastructure/I2_TOOL_ARCHITECTURE.md`.
```

### Setup em `.cursor/rules/tool-architecture.mdc`

```
---
description: "I2 Tool Architecture"
alwaysApply: false
---

Quando o usuário pedir para:
- Criar nova tool/ferramenta para um agente
- Gatear tool por plano de billing
- Adicionar permissões a uma tool existente

1. Leia themes/infrastructure/I2_TOOL_ARCHITECTURE.md
2. Sempre use @tool_handler(domain, require_company=True)
3. Sempre inclua **kwargs no handler (recebe company_id, db, _context)
4. Return da data diretamente — decorator formata a resposta
5. Adicione ToolDefinition no tool_registry do agente
6. Adicione entrada em tool_registry_metadata.yaml
7. Execute validate_registry_against_yaml() para verificar sync
8. NUNCA hardcode company_id — sempre de kwargs["company_id"]
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

- Nomes de domínios nas tools (ex: "pipeline_v2" em vez de "pipeline")
- Scopes no `tool_permissions.yaml` (adicionar novos, remover não usados)
- `scope` de cada tool (TALENT_FUNNEL/JOB_TABLE/etc.)
- Quantidade de tools por registry (85 é o atual — v5 pode ter mais/menos)
- Backend de db (SQLAlchemy → qualquer ORM desde que interface seja compatível)
- Resposta formatada das tools (estrutura interna do `data`)

### NÃO pode adaptar

| Invariante | Por quê | Consequência |
|-----------|---------|--------------|
| `require_company=True` padrão | Multi-tenancy (C5) — toda query deve ser isolada por tenant | Query sem company_id vaza dados entre tenants |
| `**kwargs` em handlers | `company_id`, `db`, `_context` são injetados dinamicamente | `TypeError` se parâmetro explícito sem default |
| Fallback 3 via `get_current_llm_tenant()` | LangGraph path não tem `_context` — único jeito de resolver | Tool recebe empty company_id no LangGraph path |
| `tool_registry_metadata.yaml` como SSoT de descrições | Descrições no YAML são enviadas ao LLM; divergência = comportamento imprevisível | LLM usa descrição errada para decidir quando chamar a tool |
| `validate_registry_against_yaml()` na startup | Detecta tool em Python sem entrada no YAML e vice-versa | Tools invisíveis para o LLM ou YAML com entradas órfãs |
| `build_degraded_response()` em vez de 403 | LLM não lida bem com HTTP errors — retorno estruturado permite resposta graceful | Agente lança exceção não tratada ao usuário |

---

## Checklist de completude (P0/P1/P2)

- [ ] **(P0)** `@tool_handler` importado e funcionando em todos os handlers de domínio
- [ ] **(P0)** `company_id` resolvido em 3 caminhos (fail-closed quando ausente)
- [ ] **(P0)** `tool_registry_metadata.yaml` em sync com handlers (validate na startup)
- [ ] **(P0)** `ToolDefinition.function` aponta para função async (não sync pura)
- [ ] **(P0)** `tool_definition_to_langchain_tool()` converte todas as tools sem erro
- [ ] **(P1)** `tool_permissions.yaml` com scopes corretos por contexto de UI
- [ ] **(P1)** Module gating configurado para tools premium (`module=` no decorator)
- [ ] **(P1)** `build_degraded_response()` retorna mensagem em PT-BR com upgrade CTA
- [ ] **(P1)** `TimedToolNode` com timeout 15s padrão em todos os agentes (I1)
- [ ] **(P2)** `export_registry_to_yaml()` usado para regenerar YAML após mudanças em massa
- [ ] **(P2)** TASTING_TOOLS configurados para preview em plano trial
- [ ] **(P2)** Documentação de cada tool (docstring) alinhada com `description` no YAML

---

## Gotchas e erros comuns

| Sintoma | Causa | Como evitar |
|---------|-------|-------------|
| Tool sempre retorna "Tenant isolation error" | `company_id` não chega via nenhum dos 3 caminhos | Verificar: (1) AgentInput.company_id preenchido, (2) `set_current_llm_tenant()` chamado no middleware, (3) `_context` injetado em AgenticLoop |
| LLM nunca chama a tool | Tool não está em `_get_tools()` do agente OU descrição YAML está vaga | Verificar `tool_definition_to_langchain_tool()` executado; melhorar descrição no YAML |
| `validate_registry_against_yaml` retorna `ok=False` | Tool em Python sem entrada no YAML (ou vice-versa) | Adicionar entrada no YAML; nunca criar handler sem YAML correspondente |
| Tool funciona sem company_id em dev | `require_company=False` esquecido em testing, ou `ENVIRONMENT=development` com contextvar preenchido | Sempre usar `require_company=True` em prod; testes devem passar company_id explicitamente |
| Module gating bloqueia tool em massa (bug) | `check_tool_module_access()` retornando `allowed=False` por falha de DB | Monitorar `module_gate_denials_total` metric; fail-closed = degraded response |
| TypeError em handler | Parâmetro sem default + sem `**kwargs` | Sempre adicionar `**kwargs: Any` ao final dos parâmetros do handler |
| Tool descrita mas não disponível no agente | Tool está no YAML mas não no `_get_tools()` do agente específico | Verificar `allowed_agents` no YAML; verificar `_TOOLS_DEFS` no tool_registry do agente |

---

## Testes obrigatórios

| Teste | Path sugerido | Cenário |
|-------|--------------|---------|
| company_id fail-closed | `tests/unit/test_tool_handler.py` | Chamar tool sem company_id → `_TENANT_REQUIRED_RESPONSE` (não crash) |
| company_id fallback contextvar | `tests/unit/test_tool_handler.py` | `set_current_llm_tenant("co123")` → tool recebe company_id correto |
| Response formatting | `tests/unit/test_tool_handler.py` | Tool retorna raw dict → decorator envolve em {success, data, message} |
| Pass-through | `tests/unit/test_tool_handler.py` | Tool retorna dict com "success" key → decorator não re-envolve |
| Module gating denied | `tests/unit/test_tool_handler.py` | `module="enterprise_feature"` + plano trial → `build_degraded_response()` |
| ToolDefinition to LangChain | `tests/unit/test_tool_adapter.py` | `tool_definition_to_langchain_tool(td)` → `StructuredTool` com name + description corretos |
| YAML validate ok | `tests/unit/test_tool_registry_loader.py` | All tools registradas têm entrada no YAML → `ok=True` |
| YAML validate missing | `tests/unit/test_tool_registry_loader.py` | Tool em Python sem entrada no YAML → `missing_in_yaml` não vazio |
| load_tool_metadata | `tests/unit/test_tool_registry_loader.py` | YAML com 85 tools → dict com 85 chaves |
| FairnessGuard em tool call | `tests/unit/test_timed_tool_node.py` | Args com atributo protegido → tool bloqueada (LIA-C03, C1) |

---

## Referências

### Bundles verbatim
- `INFRASTRUCTURE_YAMLS_CANONICAL_BUNDLE.md` — `technical_config/tool_permissions.yaml` + `technical_config/tool_registry_metadata.yaml`

### Reconstruction guides
- `INFRASTRUCTURE_RECONSTRUCTION_GUIDE.md` BLOCO D (tool registry)

### Cross-references
- **I1 Agent Architecture** — `_get_tools()` usa `ToolDefinition` + `tool_definition_to_langchain_tool()`; `TimedToolNode` executa com timeout
- **I3 Orchestration** — `CascadedRouter` usa `tool_permissions.yaml` para escopo disponível por contexto
- **C1 Fairness** — `TimedToolNode` chama `FairnessGuard` antes de executar tool (LIA-C03)
- **C5 Multi-tenancy** — `get_current_llm_tenant()` (fallback 3) depende do `set_current_llm_tenant()` em `AuthEnforcementMiddleware`
- **C8 Module Gating** — `@tool_handler(module=...)` chama `check_tool_module_access()` de `module_gating.py`
- **I5 Observability** — `TimedToolNode` emite métricas por tool; `audit_callback` captura tool calls

---

*Documento gerado em 2026-04-24 | Zero invenção — todo conteúdo verificado via SSH no Replit*
