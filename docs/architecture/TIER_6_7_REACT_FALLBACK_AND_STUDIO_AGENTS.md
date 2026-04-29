# Tier 6 (ReAct Fallback) e Tier 7 (Studio Agents) — Como a LIA Faz e Como Portar para LangChain/LangGraph

> Dois tiers opcionais do `CascadedRouter` da LIA que resolvem dois problemas diferentes:
> - **Tier 6** — última rede de segurança quando nenhum roteador determinístico capturou a intenção
> - **Tier 7** — agentes customizados criados por usuários finais, vinculados a vagas/talent pools
>
> Este doc cobre: o papel de cada tier, implementação real na LIA, contraste com o `recruiter_agent_v5` (baseline) e receita para replicar em um projeto LangChain/LangGraph externo.

---

## 1. O CascadedRouter em 30 Segundos

`CascadedRouter` (`lia-agent-system/app/orchestrator/cascaded_router.py`) é uma cascata de **8 tiers (0–7)**. Primeiro que retornar confiança suficiente ganha. Regra de ouro: o tier mais barato é tentado antes.

| Tier | Mecanismo | Custo | Quando usa |
|------|-----------|-------|------------|
| 0 | `MemoryResolver` (pronome/anáfora) | ~0 | "e o outro?" → resolve referência |
| 1 | LRU hash in-process | ~0 | frase idêntica já vista nesta instância |
| 2 | Redis hash (`SemanticCache`) | ~1ms | frase idêntica já vista em qualquer instância |
| 3 | pgvector (`VectorSemanticCache`) | ~10ms | frase **semanticamente similar** (cosine ≥ threshold) |
| 4 | `FastRouter` (regex/keyword) | ~0 | padrões fixos ("criar vaga", "listar candidatos") |
| 5 | `LLMCascadeRouter` (Haiku→Sonnet→Opus) | $ | classificação LLM com escalada |
| **6** | **`AutonomousReActAgent`** | $$$ | **fallback cross-domain** (opt-in) |
| **7** | **Studio Agent Matcher** | $$ | **agente custom do usuário** vinculado a vaga/pool |
| — | `clarification_needed` | — | último recurso: pedir esclarecimento |

**Disciplina de fallthrough:** cada tier devolve `RouteResult | None`. Se `None` ou confiança < limiar, continua.

---

## 2. Tier 6 — ReAct Fallback (Desligado por Default)

### 2.1 Papel

Quando os tiers determinísticos (0–4) falham e o LLM router (5) não atinge confiança ≥ `ROUTER_LLM_CASCADE_MIN_CONFIDENCE` (default 0.5), a request cai no Tier 6. Aqui um agente ReAct com acesso a **~40 ferramentas cross-domain** tenta resolver a pergunta diretamente, sem classificar em domínio.

### 2.2 Por que fica desligado

```python
if _os.getenv("AUTONOMOUS_REACT_ENABLED", "false").lower() == "true":
    # só então tenta Tier 6
```
`cascaded_router.py:462`. Razões:

- **Custo:** cada chamada pode consumir 5k+ tokens (vários ciclos thought/action/observation).
- **Latência:** 10+ segundos em pior caso.
- **Imprevisibilidade:** ReAct pode escolher tools erradas; Tiers 0–5 são determinísticos ou quase.
- **Circuit breaker global:** `failure_threshold=3`, `recovery_timeout=30s` — se falhar 3x, o tier é desligado por 30s.

O uso típico: habilitar em staging, observar em produção sob flag para tenants específicos, medir taxa de sucesso antes de GA.

### 2.3 Implementação na LIA

**Agent:** `lia-agent-system/app/domains/autonomous/agents/autonomous_react_agent.py`
```python
class AutonomousReActAgent(LangGraphReActBase, EnhancedAgentMixin):
    DOMAIN_INSTRUCTIONS = "acionado porque a solicitação cruza múltiplos domínios..."
    MAX_STEPS = int(os.getenv("AUTONOMOUS_REACT_MAX_STEPS", "10"))
```

**Tool pool:** `autonomous_tool_registry.py` — `AUTONOMOUS_TOOL_POOL` com ~40 tools curadas de `job_management`, `sourcing`, `cv_screening`, `pipeline`, `analytics`, `interview_scheduling`, `communication`. Inclui `rag_search`, `summarize_context`, `clarify_request` — tools de meta-raciocínio.

**Integração no router:**
```python
# cascaded_router.py (Tier 6)
result = await autonomous_agent.ainvoke(query, context)
if result.confidence >= 0.5:
    return RouteResult(domain_id="autonomous", confidence=result.confidence, source="react_fallback")
return None  # continua para Tier 7 ou clarificação
```

**Safety:** herda tudo de `LangGraphReActBase` — PII masking, AuditCallback, FairnessGuard, LangSmith tracing. Checkpointer Postgres → threads retomáveis.

### 2.4 Contraste com `recruiter_agent_v5` (baseline)

Em `/home/victhor/ats_mercado/recruiter_agent_v5/src/domains/autonomous/`:

- **`UniversalReActAgent` é a espinha dorsal única.** Não existe cascata antes — todo request cai no ReAct.
- Prompt declara "~73 ferramentas que cobrem toda a API do ATS".
- `StateGraph` custom com `build_call_model`, `build_call_tools`, `build_should_continue`, `build_evaluate_response` (+ nó crítico que decide retry).
- Infra extra: `ReActObserver`, `ModelRouter` (seleção dinâmica de LLM por step), `detect_playbook` (playbooks fixos para queries conhecidas), compressão de contexto (`SMART_COMPRESS_CHARS`, `FILE_OFFLOAD_CHARS`).

**Trade-off:** o v5 é mais simples de raciocinar ("tudo passa pelo mesmo lugar") mas paga ReAct em **100% dos requests**. A LIA só paga quando realmente precisa.

### 2.5 Como replicar em LangChain/LangGraph

```python
# shared/routing/cascade.py
from dataclasses import dataclass
from typing import Optional, Callable, Awaitable

@dataclass
class RouteResult:
    domain_id: str
    confidence: float
    source: str
    payload: dict

RouterFn = Callable[[str, dict], Awaitable[Optional[RouteResult]]]

class CascadedRouter:
    def __init__(self, tiers: list[tuple[str, RouterFn, float]]):
        # (name, fn, min_confidence)
        self.tiers = tiers

    async def route(self, query: str, context: dict) -> RouteResult:
        for name, fn, min_conf in self.tiers:
            try:
                result = await fn(query, context)
            except Exception:
                continue  # tier falhou, tenta o próximo
            if result and result.confidence >= min_conf:
                return result
        return RouteResult("clarification", 0.0, "fallback",
                           {"message": "Não entendi. Pode detalhar?"})
```

**ReAct fallback** como função de tier:

```python
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic
import os

_react_agent = None

def _build_react():
    global _react_agent
    if _react_agent is None:
        _react_agent = create_react_agent(
            model=ChatAnthropic(model="claude-sonnet-4-6"),
            tools=get_autonomous_tool_pool(),  # sua curadoria cross-domain
        )
    return _react_agent

async def tier6_react_fallback(query: str, context: dict) -> Optional[RouteResult]:
    if os.getenv("AUTONOMOUS_REACT_ENABLED", "false").lower() != "true":
        return None
    agent = _build_react()
    out = await agent.ainvoke(
        {"messages": [("user", query)]},
        config={"configurable": {"thread_id": context["thread_id"]},
                "recursion_limit": 10},
    )
    confidence = _estimate_confidence(out)  # heurística sua
    if confidence < 0.5:
        return None
    return RouteResult("autonomous", confidence, "react_fallback",
                       {"response": out["messages"][-1].content})
```

**Circuit breaker** em torno do tier (usar `pybreaker` ou equivalente):

```python
import pybreaker
_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=30)

async def tier6_guarded(query, context):
    try:
        return await _breaker.call_async(tier6_react_fallback, query, context)
    except pybreaker.CircuitBreakerError:
        return None  # pula tier 6, deixa cascata continuar
```

---

## 3. Tier 7 — Studio Agents (Custom Agents)

### 3.1 Papel

Usuário final cria um agente via UI — nome, role, system prompt, ferramentas permitidas, modelo, temperatura — e deploya para uma vaga ou talent pool específico. Quando uma request chega com aquele contexto (`job_id` ou `talent_pool_id`), o Tier 7 identifica o agente ativo e o executa no lugar dos domínios built-in.

### 3.2 Modelo de Dados

`lia-agent-system/libs/models/lia_models/custom_agent.py`:

```python
class CustomAgent(Base):
    __tablename__ = "custom_agents"
    id: UUID
    company_id: UUID          # multi-tenant obrigatório
    created_by: UUID
    name: str
    role: str
    system_prompt: Text
    allowed_tools: ARRAY(String)        # whitelist
    excluded_tools: ARRAY(String)       # blocklist extra
    domain: str = "general"
    status: Enum(draft, active, paused, archived)
    version: int
    config: JSONB                        # extras livres
    max_steps: int = 8
    temperature: float = 0.7
    model_override: str | None
    enable_memory: bool
    context_level: Enum(full, standard, minimal)
    total_executions: int
    avg_confidence: float
    is_marketplace_published: bool
```

Modelos irmãos no mesmo arquivo:
- `AgentMarketplaceListing` — listagem pública (`pending_review / approved / rejected / unpublished`)
- `AgentInstallation` — quando company X instala o agente publicado de company Y

### 3.3 Runtime

`lia-agent-system/app/domains/agent_studio/custom_agent_runtime.py` — `CustomAgentRuntime(LangGraphReActBase, EnhancedAgentMixin)`.

**Montagem do tool pool** (`_get_tools()`):
1. Começa com `autonomous_tool_pool` (~40 ferramentas base)
2. Adiciona tools do domínio declarado (sourcing, pipeline, screening, communication, analytics, job_management, automation)
3. Intersecta com `allowed_tools` do `CustomAgent`
4. Remove `excluded_tools`
5. Remove `_RESTRICTED_TOOLS` (blocklist global: `delete_candidate`, `delete_job`, `drop_tenant`, `bulk_delete`, `modify_permissions`, `change_plan`, `admin_override`, `bulk_sync_candidates`, `finalize_hiring`, `batch_move`)

**Guardrails em 3 camadas** antes da execução (`execute()`):
1. `SecurityPatterns` — injeção de prompt, strings maliciosas
2. `PromptInjectionGuard` — LLM-based detection
3. `FairnessGuard` — bloqueio de linguagem discriminatória

`FairnessGuard` roda **também na saída** de cada tool (verifica output antes de devolver ao usuário).

**Tenant isolation:** `ContextVar _CURRENT_COMPANY_ID` + `_tenant_safe_wrapper` — cada tool é envelopada para garantir que queries no banco filtrem por `company_id`.

**`context_level`** controla o quanto do histórico/persona vai pro prompt:
- `full` — todo histórico + few-shot + persona completa
- `standard` — histórico recente + persona resumida
- `minimal` — só a query atual + system prompt

### 3.4 Deployment e Matching

`agent_deployment_service.py`:

```python
deployments = await service.find_active_deployments_for_trigger(
    target_type="job" | "talent_pool",
    target_id=context.job_id or context.talent_pool_id,
    trigger_mode="manual" | "auto",
    company_id=context.company_id,
)
```

O Tier 7 do `cascaded_router.py` (linhas 497–606):

```python
if context.get("job_id") and context.get("company_id"):
    deps = await agent_deployment_service.find_active_deployments_for_trigger(...)
    if deps:
        runtime = await get_or_create_runtime(deps[0].custom_agent_id)
        return RouteResult(
            domain_id=f"custom:{runtime.name}",
            confidence=0.70,
            source="studio_agent",
            payload={"runtime": runtime},
        )
```

### 3.5 API + Frontend

- `POST /api/v1/custom-agents` — criar agente
- `GET /api/v1/custom-agents/available-tools` — devolve `PLATFORM_TOOLS_REGISTRY` (15 tools platform-level com classificação `read`/`write`; writes exigem `confirm=True`)
- `GET/POST /api/v1/agent-templates` — templates base prontos
- Frontend: `plataforma-lia/src/components/pages-agent-studio/` (`AgentStudioPage.tsx`, `AgentsTab.tsx`, `CustomAgentsTab.tsx`, `MarketplaceTab.tsx`)

**Quota:** `studio_metering_service.check_and_increment_quota` roda antes de cada criação — plan-based (por tenant).

### 3.6 Como replicar em LangChain/LangGraph

**1. Modelo de dados** (SQLAlchemy/Prisma/qualquer ORM):

```python
# models/custom_agent.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from uuid import UUID, uuid4

class CustomAgent(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID]
    name: Mapped[str]
    system_prompt: Mapped[str]
    allowed_tools: Mapped[list[str]] = mapped_column(ARRAY(String))
    excluded_tools: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    max_steps: Mapped[int] = mapped_column(default=8)
    temperature: Mapped[float] = mapped_column(default=0.7)
    model_override: Mapped[str | None]
    status: Mapped[str] = mapped_column(default="draft")
    config: Mapped[dict] = mapped_column(JSONB, default=dict)
```

**2. Runtime factory**:

```python
# agents/custom_runtime.py
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic

RESTRICTED_TOOLS = {"delete_user", "drop_table", "admin_override"}

async def build_custom_agent(agent_id: UUID, tool_pool: list, checkpointer):
    agent = await db.get(CustomAgent, agent_id)
    if agent.status != "active":
        raise ValueError(f"Agent {agent.name} não está ativo")

    allowed = set(agent.allowed_tools)
    excluded = set(agent.excluded_tools) | RESTRICTED_TOOLS
    tools = [t for t in tool_pool
             if t.name in allowed and t.name not in excluded]

    model = ChatAnthropic(
        model=agent.model_override or "claude-sonnet-4-6",
        temperature=agent.temperature,
    )
    return create_react_agent(
        model, tools=tools,
        state_modifier=agent.system_prompt,
        checkpointer=checkpointer,
    )
```

**3. Deployment + routing**:

```python
# routing/tier7.py
async def tier7_studio_agent(query: str, context: dict) -> Optional[RouteResult]:
    target_id = context.get("job_id") or context.get("talent_pool_id")
    if not target_id or not context.get("company_id"):
        return None
    dep = await find_active_deployment(target_id, context["company_id"])
    if not dep:
        return None
    runtime = await build_custom_agent(dep.custom_agent_id, TOOL_POOL, checkpointer)
    out = await runtime.ainvoke(
        {"messages": [("user", query)]},
        config={"configurable": {"thread_id": context["thread_id"]}}
    )
    return RouteResult(
        domain_id=f"custom:{dep.custom_agent_id}",
        confidence=0.70,
        source="studio_agent",
        payload={"response": out["messages"][-1].content},
    )
```

**4. Guardrails antes da execução**:

```python
async def safe_execute(runtime, query, context):
    # Input guards
    check_security_patterns(query)
    await check_prompt_injection(query)
    fairness = check_fairness(query)
    if fairness.is_blocked:
        return {"blocked": True, "message": fairness.educational_message}

    # Tenant isolation
    _CURRENT_COMPANY_ID.set(context["company_id"])
    try:
        out = await runtime.ainvoke({"messages": [("user", query)]})
    finally:
        _CURRENT_COMPANY_ID.set(None)

    # Output guards
    for msg in out["messages"]:
        if isinstance(msg, AIMessage):
            if check_fairness(msg.content).is_blocked:
                msg.content = "[conteúdo filtrado por política de fairness]"
    return out
```

---

## 4. Quando Usar Cada Tier

| Cenário | Tier recomendado |
|---------|------------------|
| Query determinística conhecida ("listar vagas") | Tier 4 (FastRouter) |
| Query ambígua mas dentro de um domínio | Tier 5 (LLM router) |
| Query cross-domain rara ou exploratória | **Tier 6 (ReAct fallback)** — se o custo se justifica |
| Usuário quer comportamento customizado para sua vaga | **Tier 7 (Studio Agent)** |
| Query totalmente fora de escopo | Clarification fallback |

**Heurística:** se mais de 10% dos requests caem em Tier 6, você tem um problema de cobertura nos tiers 4–5. O fallback existe para a cauda longa, não para o caminho principal.

---

## 5. Ordem de Adoção em Projeto Externo

1. **CascadedRouter** como scaffold — começa com 2 tiers (regex + LLM router).
2. **Adicionar Tier 6 ReAct sob flag** — `AUTONOMOUS_REACT_ENABLED=false`. Habilita em staging, mede.
3. **Circuit breaker e budget guard** antes de expor Tier 6 em produção.
4. **Modelo `CustomAgent` + API de CRUD** — Tier 7 só faz sentido depois que existe UI para criar os agentes.
5. **Marketplace** (opcional) — só após ter ≥10 agentes custom ativos e demanda de compartilhamento.

---

## 6. Arquivos de Referência

| Camada | Caminho |
|--------|---------|
| CascadedRouter | `lia-agent-system/app/orchestrator/cascaded_router.py` |
| Tier 6 Agent | `lia-agent-system/app/domains/autonomous/agents/autonomous_react_agent.py` |
| Tier 6 Tool Pool | `lia-agent-system/app/domains/autonomous/agents/autonomous_tool_registry.py` |
| Tier 7 Runtime | `lia-agent-system/app/domains/agent_studio/custom_agent_runtime.py` |
| Tier 7 Domain | `lia-agent-system/app/domains/agent_studio/domain.py` |
| CustomAgent Model | `lia-agent-system/libs/models/lia_models/custom_agent.py` |
| Deployment Service | `lia-agent-system/app/services/agent_deployment_service.py` |
| Marketplace Service | `lia-agent-system/app/services/agent_marketplace_service.py` |
| API Custom Agents | `lia-agent-system/app/api/v1/custom_agents.py` |
| API Templates | `lia-agent-system/app/api/v1/agent_templates.py` |
| Frontend Agent Studio | `plataforma-lia/src/components/pages-agent-studio/` |
| Baseline ReAct (v5) | `recruiter_agent_v5/src/domains/autonomous/` |

---

## 7. Principais Diferenças LIA × `recruiter_agent_v5`

| Aspecto | `recruiter_agent_v5` | LIA |
|---------|----------------------|-----|
| ReAct | Primário (100% dos requests) | Tier 6 — fallback opt-in |
| Custom agents | Não tem | Tier 7 completo (UI + marketplace) |
| Tool pool | ~73 ferramentas, seleção dinâmica | Cascata: 40 (autonomous) → 120+ (domínios) → filtrado por `allowed_tools` |
| Custo médio | Alto (ReAct sempre) | Baixo (tiers 0–4 resolvem maioria) |
| Previsibilidade | Baixa (LLM decide sempre) | Alta (tiers determinísticos cobrem 80%+) |
| Playbooks | Sim (`detect_playbook`) | Implícito nos tiers 3–4 |

A LIA trocou simplicidade arquitetural (v5: "tudo ReAct") por **eficiência de custo e previsibilidade** (cascata + ReAct só como rede de segurança).
