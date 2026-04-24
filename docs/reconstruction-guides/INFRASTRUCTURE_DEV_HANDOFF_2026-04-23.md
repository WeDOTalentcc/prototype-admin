# Infrastructure — Handoff para o time de dev (2026-04-23)

> Replicação no produto novo (IA repo separada) da camada de infraestrutura de
> agentes da LIA: `AgentType` enum, `LangGraphReActBase`, `@tool_handler`
> decorator, `ToolRegistry`, `CascadedRouter` (8 tiers), `MainOrchestrator`
> (4 fases), `ChatResponse` schema, `LLMProviderFactory` (tenant-aware).
> Este documento é o ponto de entrada; o manual técnico completo é o
> `INFRASTRUCTURE_RECONSTRUCTION_GUIDE.md` (72K).

---

## O que esta camada faz

É o **esqueleto de execução** da LIA. Recebe mensagem → roteia para agente certo → executa tools → retorna resposta estruturada. Tudo isso com observabilidade e multi-tenant-aware.

Características-chave:
- 15 agentes ativos cada um com especialização própria
- 100+ tools distribuídas por domínio com permissões via `tool_permissions.yaml`
- Orquestração em 4 fases (intent → routing → execution → response)
- Roteamento em cascata de 8 tiers (do mais barato/rápido para o mais sofisticado)
- Provider de LLM consciente do tenant (BYOK — Bring Your Own Key)

---

## Arquitetura (resumo)

```
Usuário → MainOrchestrator
            ├── Fase 1: Intent classification (intent_classification.yaml)
            ├── Fase 2: CascadedRouter (8 tiers)
            │            └── escolhe AgentType
            ├── Fase 3: Agent execution (LangGraphReActBase)
            │            ├── SystemPromptBuilder.build()
            │            ├── ReAct loop (Reason → Act → Observe)
            │            └── Tools (registradas via @tool_handler)
            └── Fase 4: ChatResponse schema (20 campos)
```

### Componentes canônicos

| Componente | Arquivo | Responsabilidade |
|-----------|---------|------------------|
| `AgentType` enum | `libs/agents-core/lia_agents_core/agent_interface.py` | Enum com 15 tipos (orchestrator, sourcing, cv_screening, wsi_evaluator, ...) |
| `LangGraphReActBase` | `libs/agents-core/lia_agents_core/langgraph_react_base.py` | Base class de todos os agentes — loop ReAct, hooks `_get_dynamic_domain_instructions()` |
| `SystemPromptBuilder` | `app/shared/prompts/system_prompt_builder.py` | Compositor do system prompt em 9 passos (ver LIA_PERSONA Parte 9.4) |
| `@tool_handler` | `app/shared/tool_handler.py` | Decorator que valida company_id + audit log + metrics |
| `MainOrchestrator` | `app/orchestrator/main_orchestrator.py` | Orquestra as 4 fases |
| `CascadedRouter` | `app/orchestrator/cascade_router/` | 8 tiers de roteamento (regex → embeddings → LLM) |
| `LLMProviderFactory` | `app/shared/llm/llm_provider_factory.py` | Retorna provider correto (Anthropic/OpenAI/Azure) por tenant (BYOK) |
| `ChatResponse` | `app/schemas/chat_response.py` | Schema unificado de retorno (20 campos documentados em INFRASTRUCTURE BLOCO H) |
| `ToolRegistry` | `app/shared/tools/registry.py` | Registro central de tools com permissions via `tool_permissions.yaml` |

---

## O que muda para o dev no produto novo (IA repo)

### Invariantes obrigatórias

1. **Todo agente herda de `LangGraphReActBase`.** Se criar classe própria, perde ReAct loop + hooks de compliance. Exceção: agentes fora do SystemPromptBuilder (PolicyAgent, PipelineTransitionAgent) que têm motivo arquitetural documentado.

2. **Especialização via `_get_dynamic_domain_instructions(input)` em runtime, NÃO via class attribute `DOMAIN_INSTRUCTIONS`.** Este bug foi corrigido no Sprint 1 — se voltar a fazer class attribute, `stage_context` e `memory_summary` ficam vazios.

3. **Tool registration via `@tool_handler("<domain>", require_company=True)`.** Decorator injeta `company_id` do JWT, faz audit log, enforce permissions do `tool_permissions.yaml`.

4. **Novo agente de decisão:** adicionar ao `_DECISION_AGENTS` frozenset no `system_prompt_builder.py`. Senão recebe variante `operational` do `compliance_block.yaml` (LGPD mínimo, sem fairness).

5. **ChatResponse obrigatório:** todo endpoint que retorna ao chat usa o schema de 20 campos. Não criar response dict ad-hoc.

6. **LLM provider via factory.** Nunca importar `from anthropic import ...` diretamente. Usar `LLMProviderFactory.get(company_id)` que respeita BYOK.

### Padrão de criação de agente novo

```python
# 1. Enum
class AgentType(str, Enum):
    MY_NEW_AGENT = "my_new_agent"

# 2. Domain YAML: app/prompts/domains/my_new_agent.yaml (Formato A)
# 3. Entry em agent_prompts.yaml[prompts]["my_new_agent"]
# 4. Class
class MyNewAgent(LangGraphReActBase):
    agent_type = AgentType.MY_NEW_AGENT

    def _get_dynamic_domain_instructions(self, input) -> str:
        # usa input.stage, input.candidate_id, etc
        return f"... contexto dinâmico ..."

# 5. Tools em app/domains/my_new_agent/tools/
@tool_handler("my_new_agent", require_company=True)
async def my_new_tool(**kwargs):
    ...

# 6. Registry: app/domains/my_new_agent/agents/tool_registry.py
# 7. Roteamento: atualizar orchestrator.yaml + domain_routing.yaml
# 8. Se for agente de decisão: _DECISION_AGENTS frozenset
# 9. Teste: pytest tests/integration/test_persona_invariants.py
```

### O que NÃO precisa fazer

- Não reimplementar ReAct loop — `LangGraphReActBase` tem
- Não criar cache de prompts próprio — `@lru_cache` no `SystemPromptBuilder` já cobre
- Não reinventar permissions — `tool_permissions.yaml` é SSoT
- Não fazer `if agent_type == X:` em vários lugares — usar enum + roteamento YAML

---

## Componentes a replicar (prioridade)

### Ordem de implementação sugerida

1. **`AgentType` enum + `LangGraphReActBase`** — fundação
2. **`SystemPromptBuilder`** — 9 passos exatos (copiar verbatim de LIA_PERSONA §9.4)
3. **`@tool_handler` + `ToolRegistry`** — infraestrutura de tools
4. **`LLMProviderFactory`** — já com BYOK por company_id
5. **`ChatResponse` schema** — 20 campos (verbatim em INFRASTRUCTURE BLOCO H)
6. **`MainOrchestrator` (4 fases)** — integra tudo
7. **`CascadedRouter` (8 tiers)** — pode começar com tier 1-3 e adicionar sofisticação depois
8. **Agentes individuais** — copiar de LIA conforme necessidade (começar por orchestrator, cv_screening, sourcing, recruiter_assistant)

### Arquivos canônicos a replicar ipsis litteris

| Arquivo | Por quê |
|---------|---------|
| `libs/agents-core/lia_agents_core/agent_interface.py` | Define contrato (`AgentInput`, `AgentOutput`, `AgentType`) |
| `libs/agents-core/lia_agents_core/langgraph_react_base.py` | Base class de TODOS os agentes — hooks críticos |
| `libs/agents-core/lia_agents_core/react_loop.py` | ToolDefinition + ReAct implementation |
| `app/shared/prompts/system_prompt_builder.py` | 9 passos de injeção (não mudar ordem) |
| `app/shared/tool_handler.py` | Decorator com company_id + audit + metrics |
| `app/config/tool_permissions.yaml` | Mapa tool → permission |
| `app/config/domain_routing.yaml` | AgentType → domain YAML |
| `app/schemas/chat_response.py` | 20 campos unificados |
| `app/orchestrator/main_orchestrator.py` | 4 fases da orquestração |

---

## Dependências

```
Compliance (COMPLIANCE_DEV_HANDOFF) ← IMPLEMENTAR ANTES
   ↑ system_prompt_builder injeta compliance_block automaticamente
   ↑ tool_handler faz audit log
   ↑ TenantGuard valida company_id

Infrastructure (ESTE GUIA)
   ↓ expõe AgentType + tools + orquestração

Resilience (RESILIENCE_DEV_HANDOFF)
   ↑ CircuitBreaker ao redor de LLM calls
   ↑ Learning loop consome outputs de agentes
```

**Não começar antes de Compliance estar funcional** — o `@tool_handler` depende de `AuditService` e `TenantGuard`.

---

## Validação / Testes

```bash
# Contratos de agentes
pytest tests/integration/test_agent_contracts.py -x

# Invariantes de persona (toca system_prompt_builder)
pytest tests/integration/test_persona_invariants.py -x

# Linter customizado
python scripts/check_agent_type_consistency.py  # enum vs YAML vs código
python scripts/check_tool_permissions.py         # tools registradas têm entry no YAML
```

Smoke test manual:
```python
from app.shared.prompts.system_prompt_builder import SystemPromptBuilder
prompt = SystemPromptBuilder.build(
    agent_type="orchestrator",
    user_name="Teste",
    context_page="dashboard",
)
assert "LIA" in prompt
assert "REGRA ZERO" in prompt  # _IDENTITY_OVERRIDE
assert len(prompt) > 2000      # persona + platform + compliance todos injetados
```

---

## Diferenças do ambiente da sua empresa

| Dimensão | LIA (Replit) | Produto novo |
|----------|--------------|--------------|
| Frontend | `plataforma-lia` (Next.js) | Seu FE próprio |
| Backend IA | monorepo em `lia-agent-system/` | IA repo separada |
| Backend CRUD | Rails em `ats-api-copia` | Mesmo Rails, integrado com seu FE |
| Deploy | Replit workflows | Ambiente próprio |
| LLM providers | BYOK via `LLMProviderFactory` | Mesma arquitetura (reutilizar) |
| Multi-tenant | `TenantGuard` + JWT | Mesma arquitetura (reutilizar) |

**Integração com `ats-api-copia`:** endpoints de CRUD de candidatos, vagas, pipeline ficam no Rails. A IA (agentes, tools LLM, prompts) fica na repo separada. Contrato entre elas: HTTP JSON via `rails_client` (já existe no Replit em `app/shared/rails_client.py`).

---

## Referências

- **Manual técnico:** `INFRASTRUCTURE_RECONSTRUCTION_GUIDE.md` (72K) — contém verbatim de todos os componentes, 10 blocos (A-J) com código exato
- **Mapa:** `CANONICAL_FILES_BY_THEME.md` temas 5-10 (Observabilidade, Infra de Agentes, Orquestração, LLM Providers, Multi-tenancy, Tool Permissions)
- **Persona (dependente):** `LIA_DEV_HANDOFF_2026-04-23.md` + `LIA_PERSONA_RECONSTRUCTION_GUIDE.md` Parte 9

---

## Não fazer

- `git push` — commits locais; push manual pelo Paulo
- Criar classe de agente que não herde de `LangGraphReActBase`
- Hardcode de modelo LLM em código de agente — sempre via `LLMProviderFactory`
- Import direto de `anthropic` em agent code
- Tool sem `@tool_handler` — vai rodar sem audit + sem company_id validation
- Class attribute `DOMAIN_INSTRUCTIONS` (bug recorrente — usar hook dinâmico)

---

*Handoff gerado em 2026-04-23 | Próxima revisão: quando novo AgentType ou LLM provider for adicionado*
