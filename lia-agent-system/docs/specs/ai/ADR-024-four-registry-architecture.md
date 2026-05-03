# ADR-024 — Four-Registry Architecture

**Status:** Accepted
**Date:** 2026-05-02
**Related:**
- ADR-016 (Tool registration canonical)
- ADR-022 (Tool Registry Taxonomy)
- ADR-025 (Capability Map Governance)
- `app/config/agents_registry.yaml`
- `app/tools/registry.py`
- `app/orchestrator/action_handlers/`
- `app/config/capability_map.yaml`

---

## Context

O `lia-agent-system` cresceu organicamente e acumulou múltiplos pontos de registro de comportamento. Em 2026-05, quatro estruturas distintas coexistem sem papéis formalmente separados:

1. `agents_registry.yaml` — lista agentes e seus configs
2. `app/tools/registry.py` — lista tools e seus handlers
3. `app/orchestrator/action_handlers/` — mapeia action types para funções
4. `app/config/capability_map.yaml` — mapeia capabilities de UI para tools

A ausência de fronteiras claras gerou:
- Tentativas de wiring direto `capability → agent` (contornando o registry de tools)
- Action handlers registrados como tools (confundindo governança)
- Agentes com referências hardcoded a capability names (acoplamento indevido)

## Decision

LIA usa exatamente **4 registries**, cada um com papel distinto e não intercambiável:

### Registry 1 — Agent Registry (`app/config/agents_registry.yaml`)

**Papel:** Mapeia `domain_name → { agent_class, config, llm_profile }`.

**Consumidor:** `AgentFactory` e `AgentRegistryWatcher`.

**Regra:** Apenas agentes LangGraph (subagentes com StateGraph) têm entrada aqui. Tools não têm entrada no Agent Registry.

### Registry 2 — Tool Registry (`app/tools/registry.py`)

**Papel:** Mapeia `tool_name → ToolDefinition` (handler + schemas + metadata de governança).

**Consumidor:** `ActionExecutor`, `agentic_loop`, `GovernanceToolNode`, `AgentStudio`.

**Regra:** Toda tool exposta ao LLM via function calling **deve** ter entrada aqui antes de ser usável. Ver ADR-016 para a superfície canônica de autoria (`@tool_handler`).

### Registry 3 — Handler Registry (`app/orchestrator/action_handlers/`)

**Papel:** Mapeia `action_type (str) → handler_function` para actions do tipo UI (navegação, modais, confirmações) que o orchestrator processa sem passar pelo LLM.

**Consumidor:** `MainOrchestrator._dispatch_action()`.

**Regra:** Handler Registry não se sobrepõe ao Tool Registry. Actions de UI (ex: `navigate_to_candidate`, `open_modal`) vivem aqui; operações de domínio com LLM (ex: `search_candidates`) vivem no Tool Registry.

### Registry 4 — Capability Map (`app/config/capability_map.yaml`)

**Papel:** Mapeia `capability_name (UI slug) → { tool_names[], permissions[], modal_id? }`.

**Consumidor:** Rail A UI (lê em runtime para construir cards de capability), `GovernanceToolNode` (verifica permissões por capability).

**Regra:** Capability Map referencia **tool_names do Tool Registry** — nunca agent names diretamente. A cadeia é: `UI capability → tool(s) → agent (interno, se necessário)`.

### Diagrama de fluxo

```
UI Capability Card
       ↓
Capability Map (Registry 4)
       ↓ tool_names[]
Tool Registry (Registry 2)
       ↓ handler
ActionExecutor / agentic_loop
       ↓ (se subagente necessário)
Agent Registry (Registry 1)
       ↓ agent_class
LangGraph Agent

UI Action (navigate, modal, etc.)
       ↓
Handler Registry (Registry 3)
       ↓ handler_function
Direct execution (sem LLM)
```

### Restrições de cross-registry

| Permitido | Proibido |
|-----------|----------|
| Capability Map → Tool Registry (por `tool_name`) | Capability Map → Agent Registry diretamente |
| Tool Registry → Agent Registry (tool chama subagente internamente) | Handler Registry → Tool Registry (handler não chama tools LLM) |
| Agent Registry referencia tool names no config | Agent Registry hardcoda capability names |

## Consequences

**Positivo:**
- Cada registry tem dono de código e processo de review definidos (ver ADR-025 para Capability Map).
- Eliminação de cross-wiring não documentado que causava ghost cards na UI (UC-P1-28).
- CI guards podem ser escritos por registry com escopo preciso.

**Negativo:**
- Quatro arquivos/estruturas para manter em sincronia quando uma nova capability é adicionada. Mitigação: ADR-025 define processo de gate para Capability Map que força a verificação dos outros registries.
- Desenvolvedores novos precisam entender os 4 papéis antes de adicionar qualquer feature. Mitigação: este ADR + `ARCHITECTURE.md` §Registries (a atualizar).

## Migração pendente

- Auditar Handler Registry atual e remover qualquer action que deveria ser tool (estimativa: 3-5 handlers misclassificados).
- Atualizar `ARCHITECTURE.md` para referenciar este ADR na seção de registries.
