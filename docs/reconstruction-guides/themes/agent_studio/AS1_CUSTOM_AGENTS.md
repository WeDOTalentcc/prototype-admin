# Theme: AS1 — Agent Studio & Custom Agents — Agent Studio Layer

## O que é este tema

O Agent Studio é o sistema que permite recrutadores criarem, configurarem e implantarem **agentes LIA customizados** sem escrever código. Cada agente customizado recebe um system prompt, um conjunto de ferramentas permitidas, configurações de comportamento (temperatura, max_steps) e um **piso de inteligência mínima** injetado automaticamente.

O tema abrange quatro subsistemas distintos:
1. **CustomAgentRuntime** — executor LangGraph que interpola intelligence floor + prompt do cliente + tools do registro
2. **AgentTemplate** — camada de persistência com versionamento e herança (WeDO global → customização do cliente)
3. **Marketplace** — publicação, navegação e instalação de agentes entre empresas
4. **Sourcing agents** — classe de agentes de busca multi-estratégia (distinta dos custom agents, mas gerida no mesmo domínio)

**Boundary com temas irmãos:** I1 (Agent Architecture) documenta `LangGraphReActBase` — base herdada pelo `CustomAgentRuntime`. I2 (Tool Architecture) documenta `tool_handler` e `tool_registry_loader` — infraestrutura usada pelo `PLATFORM_TOOLS_REGISTRY`. AS1 documenta apenas o runtime de agentes criados por clientes e a camada de persistência de templates.

---

## Arquivos conectados (11 total)

### Camada Persona (LLM vê — 3 arquivos)

| Arquivo | Bundle/Guide | Como é injetado |
|---------|-------------|----------------|
| `app/config/agent_studio/intelligence_floor.yaml` | LIA Bundle | `CustomAgentRuntime.__init__` carrega via `yaml.safe_load`; conteúdo de `floor_instructions` é prefixado ao `system_prompt` do cliente (linha ~80 de `custom_agent_runtime.py`) |
| `app/config/agent_templates/templates.yaml` | LIA Bundle | Semeado via script ou API admin; não injetado no LLM diretamente — serve de base para `system_prompt_yaml` do `AgentTemplate` |
| `app/domains/agent_studio/config/capabilities.yaml` | Infrastructure Bundle | `AgentStudioDomain.__init__` carrega para roteamento de intent (35+ keyword→action) |

### Camada Config (Python lê — 2 arquivos)

| Arquivo | Bundle/Guide | Quando é consumido |
|---------|-------------|-------------------|
| `app/config/agent_studio/intelligence_floor.yaml` | LIA Bundle | No `__init__` do `CustomAgentRuntime` — uma vez por instância |
| `app/config/agent_templates/templates.yaml` | LIA Bundle | Semeado na tabela `agent_templates` via script de seed ou API admin; não recarregado em runtime |

### Camada Código (6 arquivos Python)

| Arquivo | Path canônico | Responsabilidade |
|---------|--------------|----------------|
| `custom_agent_runtime.py` | `app/domains/agent_studio/custom_agent_runtime.py` | Executor principal: IntelligenceFloor + prompt + tools + memory + contextvars company_id |
| `domain.py` | `app/domains/agent_studio/domain.py` | `AgentStudioDomain` — 13 action handlers; estende `ComplianceDomainPrompt` |
| `actions.py` | `app/domains/agent_studio/actions.py` | `AGENT_STUDIO_ACTIONS` — 20 `DomainAction` com params e `requires_confirmation` |
| `agent_templates.py` | `app/api/v1/agent_templates.py` | CRUD REST de `AgentTemplate`; `ALLOWED_DOMAINS` (9); validação YAML obrigatória |
| `agent_studio_quality.py` | `app/api/v1/agent_studio_quality.py` | Quality score + evaluate endpoints para agentes existentes |
| `sector_templates.py` | `app/api/v1/sector_templates.py` | `SectorTemplateSummary`, `ApplySectorRequest`, `ApplySectorResponse` |
| `agent_template_repository.py` | `app/domains/ai/repositories/agent_template_repository.py` | DAL assíncrono do `AgentTemplate`; `list_templates` retorna global + do tenant |

### Integration points

- **I1 Agent Architecture** → `CustomAgentRuntime` herda `LangGraphReActBase` + `EnhancedAgentMixin`
- **I2 Tool Architecture** → `PLATFORM_TOOLS_REGISTRY` mapeia tool names para o registry de tools do domínio
- **C1 Fairness** → `AgentStudioDomain` estende `ComplianceDomainPrompt` (injeta FairnessGuard no system prompt)
- **C5 Multi-tenancy** → `_CURRENT_COMPANY_ID` contextvars isola dados do agente por tenant
- **R4 Background Jobs** → `execute_custom_agent` pode despachar execuções para fila Celery se definido no `ASYNC_ELIGIBLE_ACTIONS`
- **I9 Data Layer** → `AgentTemplate` model + migrations (`agent_templates` table + dois índices)

---

## Lógica IN → OUT

### Input (criar agente)

```
POST /api/v1/agent-templates/
Authorization: Bearer <JWT com company_id>
{
  "name": "Meu Triador",
  "domain": "sourcing",           # deve estar em ALLOWED_DOMAINS
  "system_prompt_yaml": "...",     # YAML com campo 'prompt' obrigatório
  "base_template_id": "triagem_rapida"  # opcional — traceabilidade
}
```

### Input (executar agente)

```
POST /api/v1/agent-studio/{agent_id}/execute
{
  "message": "Triagem da vaga #42",
  "context": { "job_id": "42" }
}
```

### Processing (criar)

```
1. JWT → company_id (NUNCA do payload)
2. AgentTemplateCreate.validate_domain() → verifica ALLOWED_DOMAINS (9)
3. AgentTemplateCreate.validate_yaml() → yaml.safe_load + verifica campo 'prompt'
4. AgentTemplateRepository.create() → INSERT agent_templates (status=DRAFT)
5. Resposta: AgentTemplateResponse (id, company_id, name, domain, version=1, status=DRAFT)
```

### Processing (executar)

```
1. JWT → company_id → _CURRENT_COMPANY_ID.set(company_id)  ← ContextVar
2. Carregar AgentTemplate (company_id filter OU is_global=True)
3. Carregar intelligence_floor.yaml → floor_instructions
4. Construir system_prompt:
   a. floor_instructions (ANTES do prompt do cliente — hardcoded)
   b. system_prompt do AgentTemplate (client's prompt)
5. Filtrar allowed_tools contra PLATFORM_TOOLS_REGISTRY (16 tools)
6. Remover _RESTRICTED_TOOLS (frozenset de 17 ops destrutivas)
7. Instanciar CustomAgentRuntime(
       agent_id, agent_name,
       system_prompt=<floor + client>,
       allowed_tools=<filtrado>,
       domain, max_steps=8, temperature=0.7,
       company_id=company_id, enable_memory=True, context_level="full"
   )
8. CustomAgentRuntime.run(message) → LangGraph ReAct loop
9. Retorna ChatResponse
```

### Output

```python
# AgentTemplate criado
AgentTemplateResponse(
    id: str,            # UUID gerado
    company_id: str,    # do JWT
    name: str,
    domain: str,
    system_prompt_yaml: str,
    version: int,       # começa em 1
    status: str,        # "draft"
    base_template_id: str | None,
    created_at: datetime,
    published_at: None,
    archived_at: None
)
```

### Escalation / HITL

- `publish_to_marketplace` → `requires_confirmation=True` (pede confirmação antes de publicar para outras empresas)
- `pause_agent`, `deactivate_agent`, `uninstall_agent` → `requires_confirmation=True`
- `install_from_marketplace` → `requires_confirmation=True` (instala agente de terceiro — revisão de segurança implícita)

---

## Componentes críticos

### PLATFORM_TOOLS_REGISTRY (16 tools)

> **Verificado via SSH 2026-04-24.** A versão abaixo é o conteúdo real de `custom_agent_runtime.py` linhas 17-34. Três tools diferem da versão anterior do doc: o código tem `get_company_culture`, `summarize_context`, `clarify_request` em vez de `list_applications`, `get_candidate_score`, `get_interview_details`.

```python
# app/domains/agent_studio/custom_agent_runtime.py (verificado SSH 2026-04-24)
PLATFORM_TOOLS_REGISTRY = {
    # READ (11)
    "search_candidates": "read",
    "list_jobs": "read",
    "get_job_details": "read",
    "get_candidate_details": "read",
    "get_pipeline_summary": "read",
    "search_talent_pool": "read",
    "get_analytics_summary": "read",
    "get_company_culture": "read",
    "get_evaluation_criteria": "read",
    "summarize_context": "read",
    "clarify_request": "read",
    # WRITE (5)
    "move_candidate": "write",
    "send_email": "write",
    "update_candidate_field": "write",
    "schedule_interview": "write",
    "create_note": "write",
}
```

### _RESTRICTED_TOOLS (permanentemente bloqueadas)

> **Verificado via SSH 2026-04-24.** A frozenset real tem **17 entradas** (expandida nas Etapas 2 e 3 do audit OWASP LLM06 — não apenas 6 como documentado anteriormente).

```python
# app/domains/agent_studio/custom_agent_runtime.py (verificado SSH 2026-04-24)
_RESTRICTED_TOOLS = frozenset({
    # Etapa 1 (original — 6)
    "delete_candidate",
    "delete_job",
    "delete_company",
    "bulk_delete",
    "reset_pipeline",
    "drop_tenant",
    # Etapa 2 (OWASP LLM06 audit — +6)
    "modify_permissions",
    "change_plan",
    "admin_override",
    "bulk_sync_candidates",
    "finalize_hiring",
    "batch_move",
    # Etapa 3 (expansão — +5)
    "batch_move_candidates",
    "reject_autonomous_action",
    "calibrate_sourcing_agent",
    "advance_campaign_stage",
    "move_pool_to_job",
})
```

Essas ferramentas **nunca** são expostas a agentes customizados. Não é possível desbloqueá-las via configuração — são frozenset em runtime.

### _CURRENT_COMPANY_ID contextvars

```python
_CURRENT_COMPANY_ID: contextvars.ContextVar[str] = contextvars.ContextVar(
    "custom_agent_company_id", default=""
)
```

Garante isolamento multi-tenant durante execução assíncrona concorrente. O `company_id` é definido antes do `run()` do agente e propagado para todas as tool calls via contextvars (não via argumento).

### Intelligence Floor (6 seções)

```yaml
# app/config/agent_studio/intelligence_floor.yaml (version: 1)
# Injetado ANTES do prompt do cliente
floor_instructions: |
  [PISO DE INTELIGENCIA — INSTRUCOES AUTOMATICAS]

  DESAMBIGUACAO:        # ask before act se pedido for ambíguo
  FALLBACK QUANDO FERRAMENTA FALHA:  # traduzir erro técnico para PT-BR de negócio
  TOM E VOCABULARIO:    # HR vocabulary: pipeline, shortlist, triagem, fit cultural
  PROATIVIDADE MINIMA:  # sugere 1-2 próximos passos após completar tarefa
  VERIFICACAO DE CONSISTENCIA:  # alerta dados estranhos; nunca inventa
  CONTEXTO DE PLATAFORMA:  # WeDOTalent; respeita configs específicas da empresa
```

Regra crítica: o prompt do cliente pode **sobrescrever** os comportamentos do floor, mas **não pode removê-los** — o floor é prefixado, não substituído.

### AgentTemplate — modelo e versionamento

```python
# libs/models/lia_models/agent_template.py
class AgentTemplateStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class AgentTemplate(Base):
    __tablename__ = "agent_templates"
    __table_args__ = (
        Index("ix_agent_templates_company_domain", "company_id", "domain", "status"),
        Index("ix_agent_templates_public", "domain", "status"),
    )
    id: Mapped[str]                 # UUID string
    company_id: Mapped[Optional[str]]  # NULL = WeDO global; preenchido = cliente
    name: Mapped[str]               # max 500 chars
    domain: Mapped[str]             # um de ALLOWED_DOMAINS
    system_prompt_yaml: Mapped[str] # YAML com {{variable_name}}
    version: Mapped[int]            # inicia em 1; incrementa a cada save
    status: Mapped[str]             # DRAFT → PUBLISHED → ARCHIVED
    base_template_id: Mapped[Optional[str]]  # FK self (traceabilidade)
    created_by: Mapped[str]
    created_at, published_at, archived_at: Mapped[datetime]
```

**Regra de herança:** `AgentTemplateRepository.list_templates(company_id=X)` retorna:
```python
where(or_(AgentTemplate.company_id == company_id, AgentTemplate.is_global.is_(True)))
```
Ou seja: templates do próprio tenant + templates públicos WeDO (fallback global).

### ALLOWED_DOMAINS (9)

```python
# app/api/v1/agent_templates.py
ALLOWED_DOMAINS = [
    "sourcing", "pipeline", "wsi", "lia_assistant", "job_wizard",
    "candidate_search", "automation", "analytics", "compliance",
]
```

### AgentTemplateCreate — validação obrigatória

```python
@validator("system_prompt_yaml")
def validate_yaml(cls, v):
    data = yaml.safe_load(v)
    if not isinstance(data, dict):
        raise ValueError("YAML deve ser um dicionário com campos 'name', 'prompt'")
    if "prompt" not in data:
        raise ValueError("Campo 'prompt' obrigatório no YAML")
    return v
```

YAML deve ser dicionário e **deve conter campo `prompt`**. Sistema recusa criação sem esse campo.

### AGENT_STUDIO_ACTIONS (20 ações)

```python
# app/domains/agent_studio/actions.py — AGENT_STUDIO_ACTIONS
# Sourcing / Calibração (8):
create_sourcing_agent, calibrate_agent, get_agent_status, list_agents,
recalibrate_agent, pause_agent*, list_sector_templates, run_multi_strategy

# Custom Agents (4):
create_custom_agent, list_custom_agents, test_custom_agent, execute_custom_agent

# Marketplace (5):
publish_to_marketplace*, browse_marketplace, install_from_marketplace*,
deactivate_agent*, uninstall_agent*

# Crew / Consumo / Help (3):
assign_to_crew, get_studio_consumption, explain_agent_studio

# * requires_confirmation=True
```

### Templates pré-configurados (7)

| id | category | max_steps | temperature | Tools principais |
|----|----------|-----------|-------------|-----------------|
| `triagem_rapida` | screening | 10 | 0.3 | search_candidates, move_candidate |
| `sourcing_diversidade` | sourcing | 10 | 0.5 | search_candidates, search_talent_pool |
| `followup_automatico` | communication | 8 | 0.5 | send_email, get_candidate_details |
| `analise_pipeline` | analytics | 8 | — | get_pipeline_summary, get_analytics_summary |
| `assistente_entrevista` | screening | 10 | 0.4 | get_evaluation_criteria, create_note |
| `engajamento_talentos` | sourcing | 8 | 0.6 | search_talent_pool, send_email |
| `assistente_geral` | general | 8 | 0.5 | — (sem tools fixas) |

---

## CrewExecutor — Orquestração Multi-Agente em Crew

> **Verificado via SSH 2026-04-24.** Dados extraídos de `app/domains/agent_studio/`, `libs/agents-core/lia_agents_core/agent_bus.py`, e `libs/models/lia_models/crew_*.py` pelo agente de auditoria.

O subsistema de **Crews** permite combinar múltiplos agentes (custom ou nativos) em um plano de execução DAG com delegação via `AgentBus`. É o mecanismo que permite um custom agent coordenar outros agentes sem acoplamento direto.

---

### CrewPlanExecutor

```python
# app/domains/agent_studio/crew_executor.py (verificado SSH 2026-04-24)
class CrewPlanExecutor:
    def __init__(self, task_handlers: dict, use_bus_delegation: bool = False):
        # task_handlers: {handler_name: callable}
        # use_bus_delegation: True → delega via AgentBus.request() ao invés de chamar handler direto
```

**Fluxo `execute(crew_plan, company_id)` — 5 etapas:**

```
1. Feature flag check  → CREW_DELEGATION_ENABLED (env var fallback True)
2. DAG validation      → verifica ciclos e dependências em crew_plan.tasks
3. Main loop           → asyncio.gather para tasks em paralelo (mesma camada do DAG)
                         tasks seriais aguardam dependência resolução antes do gather
4. Status resolution   → CrewExecutionStatus.COMPLETED / FAILED / PARTIAL
5. Context cleanup     → CrewContext.cleanup() (mantém TTL no Redis, não deleta)
```

**Delegação via AgentBus:**

```python
async def _delegate_via_bus(self, task: CrewTask, crew_ctx: CrewContext) -> dict:
    return await agent_bus.request(
        to_agent=task.role.agent_type,
        payload={"task": task.dict(), "context": crew_ctx.get_relevant(task)},
        company_id=crew_ctx.company_id,
        timeout_seconds=30.0
    )
```

---

### AgentBus — Canais Redis

```python
# libs/agents-core/lia_agents_core/agent_bus.py
# Canal de entrada:
"lia:agent_bus:{company_id}:{to_agent}"     # pub/sub por company_id + agente alvo

# Canal de resposta correlacionado:
"lia:agent_bus:reply:{correlation_id}"      # correlation_id = uuid4() gerado no request()
```

**`AgentBus.request(to_agent, payload, company_id, timeout_seconds=30)` — sequência:**
```
1. correlation_id = uuid4()
2. PUBLISH → lia:agent_bus:{company_id}:{to_agent}
3. SUBSCRIBE → lia:agent_bus:reply:{correlation_id}
4. WAIT timeout_seconds → raises AgentBusTimeoutError se sem resposta
5. RETURN payload da resposta
```

**Multi-tenancy:** o `company_id` no canal garante que agentes de tenants diferentes nunca recebem mensagens entre si — mesmo que dois tenants tenham agentes com o mesmo `agent_type`.

---

### CrewContext — Redis-backed

```python
# CREW_CONTEXT_PREFIX = "lia:crew_ctx"
# DEFAULT_TTL_SECONDS = 3600  (1 hora)

# Chave Redis:
"lia:crew_ctx:{company_id}:{execution_id}"

# context_mappings — como resultados de tasks anteriores fluem para tasks subsequentes:
# "{task_id}.{result_key}"  →  injetado em task.params via crew_ctx.resolve_mapping()
```

**Exemplo de `context_mappings`:**

```python
# Em crew_plan.tasks[1]:
"params": {
    "candidate_profile": "{sourcing_task.top_candidates[0]}",  # resultado de task anterior
    "job_requirements": "{jd_task.enriched_jd}"
}
# CrewContext.resolve_mapping() substitui antes de executar a task
```

---

### Modelos de Dados (8 classes)

```python
# libs/models/lia_models/ (crew_*.py — verificado SSH 2026-04-24)

class CrewRoleType(str, Enum):
    SOURCING = "sourcing"
    SCREENING = "screening"
    PIPELINE = "pipeline"
    ANALYTICS = "analytics"
    COMMUNICATION = "communication"

class CrewTaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class CrewExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"

class CrewRole(Base):          # tabela crew_roles
    id, name, agent_type, role_type: CrewRoleType, capabilities: JSONB

class CrewTask(Base):          # tabela crew_tasks
    id, plan_id: FK CrewPlan, role_id: FK CrewRole,
    depends_on: ARRAY[UUID],   # IDs de tasks predecessoras
    params: JSONB,
    context_mappings: JSONB,   # "{task_id.result_key}" mappings
    status: CrewTaskStatus, result: JSONB, error: str

class CrewPlan(Base):          # tabela crew_plans
    id, crew_id: FK AgentCrew, tasks: relationship CrewTask,
    created_by, created_at, metadata: JSONB

class AgentCrew(Base):         # tabela agent_crews
    id, company_id, name, description,
    roles: relationship CrewRole,
    is_active: bool

class CrewExecutionResult:     # dataclass (não SQLAlchemy)
    execution_id: str
    status: CrewExecutionStatus
    task_results: dict[str, dict]   # {task_id: result_dict}
    errors: list[str]
    started_at: datetime
    completed_at: datetime | None
    duration_seconds: float | None
```

---

### CrewAuditService — 5 Eventos

```python
# app/domains/agent_studio/crew_audit_service.py
# Wraps audit_service.log_decision() com context de crew

class CrewAuditService:
    def log_crew_started(crew_id, execution_id, company_id, plan_summary) -> None
    def log_task_completed(task_id, task_name, company_id, result_summary) -> None
    def log_task_failed(task_id, task_name, company_id, error) -> None
    def log_delegation_request(from_agent, to_agent, correlation_id, company_id) -> None
    def log_crew_completed(execution_id, status, company_id, summary) -> None

# Todos chamam audit_service.log_decision() com:
#   decision_type = "crew_execution"
#   company_id = JWT-sourced company_id (nunca do payload)
```

---

### CREW_DELEGATION_ENABLED — Feature Flag

```python
# app/domains/agent_studio/crew_executor.py
CREW_DELEGATION_ENABLED: bool = (
    os.environ.get("CREW_DELEGATION_ENABLED", "true").lower() == "true"
)

# CrewPlanExecutor.execute():
if not CREW_DELEGATION_ENABLED:
    return CrewExecutionResult(status=CrewExecutionStatus.FAILED,
                               errors=["Crew execution disabled via feature flag"])
```

**Comportamento quando desabilitado:** falha explícita com mensagem — não executa nada. Chamadores devem checar o resultado.

---

### Padrão de Uso em crew_examples.py

```python
# app/domains/agent_studio/crew_examples.py

def build_job_opening_sourcing_crew(company_id: str) -> AgentCrew:
    """Crew pré-definida: JD enrichment → sourcing → screening → pipeline move."""
    # Define 4 roles: jd_enricher, sourcer, screener, pipeline_manager
    # Define 4 tasks em DAG:
    #   jd_task (sem deps) → sourcing_task (deps=[jd_task]) →
    #   screening_task (deps=[sourcing_task]) → pipeline_task (deps=[screening_task])
    # context_mappings conectam resultados entre tasks

def get_production_handlers() -> dict:
    """Retorna task_handlers para inicializar CrewPlanExecutor em produção."""
    # Mapeia handler_name → callable de cada domínio:
    # "jd_enrich" → JdEnrichmentService.enrich
    # "source_candidates" → SourcingAgent.execute_tool("search_candidates")
    # "screen_candidates" → WSIService.quick_screen
    # "move_to_pipeline" → PipelineAgent.execute_tool("move_candidate")
```

**Instanciação típica:**
```python
handlers = get_production_handlers()
executor = CrewPlanExecutor(task_handlers=handlers, use_bus_delegation=True)
crew_plan = build_job_opening_sourcing_crew(company_id=company_id).to_plan()
result: CrewExecutionResult = await executor.execute(crew_plan, company_id=company_id)
```

---

### Regras imutáveis de Crew

| Regra | Por quê é imutável |
|-------|--------------------|
| `company_id` sempre do JWT, nunca do `crew_plan` payload | Multi-tenancy — plan malicioso pode tentar referenciar dados de outro tenant |
| `CrewAuditService` obrigatório em toda execução | EU AI Act Art. 12 + auditabilidade de decisões encadeadas |
| `CREW_DELEGATION_ENABLED` deve ser falso em ambientes sem Redis | AgentBus usa Redis para pub/sub — sem Redis, o `request()` pendura indefinidamente se timeout não estiver configurado |
| `depends_on` forma DAG acíclico | Ciclos causam deadlock em `asyncio.gather` (tasks esperando umas às outras) |
| `context_mappings` só leem resultados de tasks predecessoras | Leitura de tasks futuras seria `None` → resultado imprevisível |

---

## Instruções para Claude Code / Cursor

### "Implementa Agent Studio no v5"

**Passo 1 — Modelo e migração**
```bash
# Criar lia_models/agent_template.py (copiar de fonte canônica)
# Adicionar em lia_models/__init__.py:
from .agent_template import AgentTemplate
# Criar migration:
alembic revision --autogenerate -m "add_agent_templates"
# Conferir: cria tabela agent_templates + 2 índices
```

**Passo 2 — Repository**
```bash
# Criar app/domains/ai/repositories/agent_template_repository.py
# Implementar: list_templates (or_ company_id + is_global), get_by_id,
#              create, update, soft_delete, hard_delete
# NUNCA confiar em company_id do payload — sempre injetar via dependency
```

**Passo 3 — Intelligence Floor YAML**
```bash
# Criar app/config/agent_studio/intelligence_floor.yaml
# Copiar floor_instructions com as 6 seções exatas
# Criar app/config/agent_templates/templates.yaml com os 7 templates
```

**Passo 4 — CustomAgentRuntime**
```bash
# Criar app/domains/agent_studio/custom_agent_runtime.py
# Obrigatório:
#   _CURRENT_COMPANY_ID: contextvars.ContextVar (NÃO threading.local)
#   PLATFORM_TOOLS_REGISTRY (16 tools: read/write)
#   _RESTRICTED_TOOLS = frozenset (17 ops destrutivas)
#   CustomAgentRuntime extends LangGraphReActBase, EnhancedAgentMixin
#   __init__ carrega intelligence_floor.yaml e prefixa ao system_prompt
```

**Passo 5 — Domain e Actions**
```bash
# Criar app/domains/agent_studio/domain.py
#   AgentStudioDomain extends ComplianceDomainPrompt
#   domain_id = "agent_studio"
#   13 action handlers
# Criar app/domains/agent_studio/actions.py
#   AGENT_STUDIO_ACTIONS = 20 DomainAction (copiar exato — nomes são contratos)
```

**Passo 6 — API**
```bash
# Criar app/api/v1/agent_templates.py
#   ALLOWED_DOMAINS (9 exatos)
#   AgentTemplateCreate com @validator("domain") + @validator("system_prompt_yaml")
#   _DualId via _path_patterns.DUAL_ID_PATH_PATTERN (evita shadowing de rotas)
# Criar app/api/v1/agent_studio_quality.py
# Criar app/api/v1/sector_templates.py
# Registrar em app/api/routes.py
```

**Passo 7 — Seed de templates**
```bash
# Script de seed que lê templates.yaml e insere com company_id=None (global WeDO)
# Status inicial = PUBLISHED (disponíveis imediatamente)
```

### "Adiciona custom agent a uma feature nova"

1. Verificar que o `domain` desejado está em `ALLOWED_DOMAINS` — se não estiver, adicionar lá primeiro
2. Criar template no YAML (`app/config/agent_templates/templates.yaml`) com o formato correto (`prompt` field obrigatório)
3. Criar `DomainAction` correspondente em `AGENT_STUDIO_ACTIONS` se for uma nova ação conversacional
4. Instanciar `CustomAgentRuntime` passando `company_id` do JWT (nunca hardcoded)
5. Verificar que as tools necessárias estão em `PLATFORM_TOOLS_REGISTRY` — se write, adicionar explicitamente

### Setup em CLAUDE.md (snippet)

```markdown
## Agent Studio (AS1)
- Fonte: themes/agent_studio/AS1_CUSTOM_AGENTS.md
- Intelligence floor: app/config/agent_studio/intelligence_floor.yaml
- ALWAYS prefix floor_instructions BEFORE client system_prompt
- company_id isolation: use _CURRENT_COMPANY_ID contextvars (never threading.local)
- Restricted tools (frozenset, never expose): delete_candidate, delete_job,
  delete_company, bulk_delete, reset_pipeline, drop_tenant
- Templates: app/config/agent_templates/templates.yaml (7 seeds, company_id=None)
- Domain validation: ALLOWED_DOMAINS (9) enforced in API schema
```

### Setup em Cursor rules (.cursor/rules/agent-studio.mdc)

```
---
description: Agent Studio custom agent rules
globs: ["*agent_studio*", "*custom_agent*", "*agent_template*"]
---
# Agent Studio Rules
- Intelligence floor MUST be prefixed before client prompt (never replace)
- company_id isolation via contextvars.ContextVar (not thread-local)
- _RESTRICTED_TOOLS frozenset: never expose delete/bulk/drop operations
- ALLOWED_DOMAINS: sourcing, pipeline, wsi, lia_assistant, job_wizard,
  candidate_search, automation, analytics, compliance
- AgentTemplate YAML must contain 'prompt' field (validator enforces)
- Published versions are immutable — create new version to edit
- list_templates must filter: or_(company_id == tenant, is_global == True)
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

| Item | Flexível porque |
|------|----------------|
| Nomes dos templates em `templates.yaml` | São seeds de UI, não contratos de API |
| Temperatura e max_steps default | Parâmetros de tuning, não arquiteturais |
| Número de tools em `PLATFORM_TOOLS_REGISTRY` | Pode adicionar mais read tools; write tools precisam de revisão |
| Path do intelligence floor YAML | Configurável via settings, desde que seja carregado antes do prompt |
| Campos adicionais em `AgentTemplate` | Migração aditiva (sem remoção de campos existentes) |
| Implementação do `AgentTemplateRepository` | Interface pode variar, semântica de `or_(company_id, is_global)` é imutável |
| Formato de `system_prompt_yaml` | Pode usar campos adicionais além de `prompt` |
| Quantidade de ações em `AGENT_STUDIO_ACTIONS` | Pode adicionar ações novas |

### NÃO pode adaptar (arquitetural ou operacional)

| Item | Por quê é imutável |
|------|--------------------|
| `_RESTRICTED_TOOLS` frozenset (17 ops) | Proteção de dados de produção — remoção de qualquer item é risco P0 de destruição de dados multi-tenant |
| Intelligence floor prefixado ANTES do prompt do cliente | Contrato de comportamento mínimo; se vir depois, pode ser anulado pelo prompt do cliente |
| `_CURRENT_COMPANY_ID` via `contextvars.ContextVar` (não `threading.local`) | FastAPI + asyncio: `threading.local` não propaga em contextos assíncronos concorrentes |
| `company_id` sempre do JWT (nunca do payload) | Multi-tenancy — exploração cross-tenant via payload é vetor de ataque P0 |
| Validação de `domain` contra `ALLOWED_DOMAINS` | Evita execução de agentes em domínios sem controles de compliance implementados |
| Validação de `prompt` no YAML do template | Sem esse campo, o CustomAgentRuntime falha em runtime de forma silenciosa |
| `AgentTemplateStatus.PUBLISHED` → imutável | Auditoria: versões publicadas são contratos; editar publicado é novo DRAFT |
| `is_global=True` para templates WeDO (company_id=None) | Fallback de herança — quebrar isso significa que clientes sem templates não têm ponto de partida |
| DUAL_ID_PATH_PATTERN em rotas de template | Previne shadowing de rotas estáticas (Task #489/455 pattern) |

---

## Checklist de completude

### P0 — Críticos (bloqueiam deploy)

- [ ] (P0) `_CURRENT_COMPANY_ID` implementado como `contextvars.ContextVar` (não `threading.local`)
- [ ] (P0) `company_id` extraído do JWT — nunca do corpo da requisição em nenhum endpoint de agent studio
- [ ] (P0) `_RESTRICTED_TOOLS` frozenset contém todos os 17 nomes exatos (verificar lista completa em `custom_agent_runtime.py`)
- [ ] (P0) Intelligence floor carregado de YAML e **prefixado ANTES** do system_prompt do cliente
- [ ] (P0) `AgentStudioDomain` estende `ComplianceDomainPrompt` (FairnessGuard injetado)
- [ ] (P0) `ALLOWED_DOMAINS` validado no schema — agente não é criado em domain fora da lista
- [ ] (P0) `AgentTemplateRepository.list_templates` usa `or_(company_id == x, is_global == True)` — nunca retorna templates de outros tenants

### P1 — Importantes

- [ ] (P1) `validate_yaml` verifica que YAML é dict E contém campo `prompt`
- [ ] (P1) `AgentTemplateStatus` lifecycle: DRAFT → PUBLISHED → ARCHIVED implementado
- [ ] (P1) Versões PUBLISHED são imutáveis (update cria novo DRAFT)
- [ ] (P1) `base_template_id` FK a self preservado para rastreabilidade de customizações
- [ ] (P1) `publish_to_marketplace` com `requires_confirmation=True` — bot não publica sem confirmação
- [ ] (P1) Índices `ix_agent_templates_company_domain` + `ix_agent_templates_public` criados na migration
- [ ] (P1) `DUAL_ID_PATH_PATTERN` importado de `_path_patterns.py` (não implementado inline)
- [ ] (P1) 7 templates seed inseridos com `company_id=None` e `status=PUBLISHED`

### P2 — Qualidade

- [ ] (P2) `intelligence_floor.yaml` com todas as 6 seções exatas (DESAMBIGUACAO, FALLBACK, TOM, PROATIVIDADE, CONSISTENCIA, CONTEXTO)
- [ ] (P2) `AgentStudioDomain.domain_id = "agent_studio"` (exato — é chave de roteamento)
- [ ] (P2) `AGENT_STUDIO_ACTIONS` com os 20 action_ids exatos (são contratos da UI conversacional)
- [ ] (P2) `capabilities.yaml` com 35+ keyword→action mappings para intent routing
- [ ] (P2) Endpoints de quality score (`/agent-studio/{id}/quality-score`) implementados
- [ ] (P2) `soft_delete` (is_active=False) vs `hard_delete` usados conforme contrato
- [ ] (P2) Logs de consumo de tokens/créditos por agente (`get_studio_consumption`)

---

## Gotchas e erros comuns

### 1. threading.local em vez de contextvars

```python
# ❌ ERRADO — não propaga em asyncio
_company_id = threading.local()

# ✅ CORRETO
_CURRENT_COMPANY_ID: contextvars.ContextVar[str] = contextvars.ContextVar(
    "custom_agent_company_id", default=""
)
```

Em FastAPI com asyncio, `threading.local` não propaga para coroutines. O resultado é `company_id = ""` em tool calls filhas, causando vazamento de dados cross-tenant.

### 2. Prompt do cliente sobrescrevendo o intelligence floor

```python
# ❌ ERRADO — floor vira texto, pode ser ignorado
system_prompt = client_prompt + "\n\n" + floor_instructions

# ✅ CORRETO — floor é prefixado, não sufixado
system_prompt = floor_instructions + "\n\n" + client_prompt
```

Se o floor vier depois, o LLM pode priorizar instruções do cliente que contradigam o floor.

### 3. Expor _RESTRICTED_TOOLS por engano

```python
# ❌ ERRADO — filtra apenas allowed_tools sem checar restricted
tools = [t for t in PLATFORM_TOOLS_REGISTRY if t in allowed_tools]

# ✅ CORRETO — duplo filtro
tools = [t for t in PLATFORM_TOOLS_REGISTRY
         if t in allowed_tools and t not in _RESTRICTED_TOOLS]
```

### 4. company_id do payload em vez do JWT

```python
# ❌ ERRADO — payload pode ser forjado
company_id = request.body.company_id

# ✅ CORRETO
company_id = current_user.company_id  # extraído do JWT via get_verified_company_id
_CURRENT_COMPANY_ID.set(company_id)
```

### 5. Template YAML sem campo 'prompt'

```yaml
# ❌ ERRADO — validator vai rejeitar
name: "Meu Agente"
instructions: "Você é..."

# ✅ CORRETO
name: "Meu Agente"
prompt: "Você é..."
variables:
  - job_title
```

### 6. Editar template PUBLISHED diretamente

Templates com `status=PUBLISHED` são imutáveis (auditoria). O `AgentTemplateRepository.update()` deve verificar status antes de atualizar — se PUBLISHED, criar nova instância com version+1 e status=DRAFT, não modificar o existente.

### 7. list_templates sem filtro de is_global

```python
# ❌ ERRADO — cliente só vê os próprios templates, sem fallback
q = q.where(AgentTemplate.company_id == company_id)

# ✅ CORRETO — próprios + WeDO globais
q = q.where(or_(AgentTemplate.company_id == company_id, AgentTemplate.is_global.is_(True)))
```

### 8. ALLOWED_DOMAINS com domínio sem compliance implementado

Adicionar um domínio novo em `ALLOWED_DOMAINS` sem implementar os controles de compliance correspondentes (FairnessGuard, LGPD, auditoria) cria vetor de bypass. Só adicionar após implementar os guards.

### 9. DUAL_ID_PATH_PATTERN ignorado

Sem o pattern, a rota `GET /agent-templates/list` pode ser capturada pelo handler `GET /agent-templates/{id}` causando 404 ou 422 em rotas estáticas (Task #455 bug class).

---

## Testes obrigatórios

| Teste | Path sugerido | Cenário |
|-------|--------------|---------|
| Isolamento multi-tenant | `tests/unit/test_custom_agent_runtime.py` | Dois tenants executando agentes concorrentes → company_id não vaza entre contextos |
| _RESTRICTED_TOOLS bloqueadas | `tests/unit/test_custom_agent_runtime.py` | Tentar passar "delete_candidate" em allowed_tools → deve ser removida silenciosamente |
| Intelligence floor prefixado | `tests/unit/test_custom_agent_runtime.py` | system_prompt do runtime deve começar com floor_instructions |
| YAML sem 'prompt' field | `tests/unit/test_agent_templates_api.py` | POST com YAML sem 'prompt' → 422 |
| Domain inválido | `tests/unit/test_agent_templates_api.py` | POST com domain="invalid" → 422 |
| list_templates retorna globais | `tests/integration/test_agent_templates.py` | Tenant sem templates custom → recebe 7 WeDO globais |
| Publicação requer confirmação | `tests/e2e/test_agent_studio.py` | publish_to_marketplace sem confirmação → bot pergunta antes de executar |
| company_id do JWT (não payload) | `tests/security/test_agent_studio_tenant_isolation.py` | Payload com company_id falso → ignorado, usa JWT |
| PUBLISHED imutável | `tests/unit/test_agent_template_repository.py` | Update em template PUBLISHED → cria novo DRAFT v2 |

---

## Referências

| Recurso | Localização |
|---------|------------|
| LIA_PERSONA guide — §9.7 (intelligence_floor verbatim) | `/Users/paulomoraes/Documents/Python/LIA_PERSONA_RECONSTRUCTION_GUIDE.md` §9.7 |
| Infrastructure guide — §B (Agent Architecture base) | `themes/infrastructure/I1_AGENT_ARCHITECTURE.md` |
| Infrastructure guide — §D (Tool Architecture) | `themes/infrastructure/I2_TOOL_ARCHITECTURE.md` |
| C1 Fairness (FairnessGuard em ComplianceDomainPrompt) | `themes/compliance/C1_FAIRNESS_AND_ANTI_DISCRIMINATION.md` |
| C5 Multi-tenancy (_CURRENT_COMPANY_ID contextvars) | `themes/compliance/C5_MULTI_TENANCY_AND_ISOLATION.md` |
| I9 Data Layer (AgentTemplate migration) | `themes/infrastructure/I9_DATA_LAYER_AND_MIGRATIONS.md` |
| Handoff LIA Partes A-F | `DEVELOPER_HANDOFF.md` (1204 linhas) |
