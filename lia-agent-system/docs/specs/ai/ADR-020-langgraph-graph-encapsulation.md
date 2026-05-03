# ADR-020 — LangGraph Graph Encapsulation Pattern

**Status:** Accepted
**Date:** 2026-05-02
**Related:**
- ADR-023 (Subagent vs Tool Decision Criteria)
- `app/agents/` (23 LangGraph agents)
- `app/orchestrator/agent_registry_watcher.py`

---

## Context

O `lia-agent-system` contém 23 agentes que utilizam LangGraph. Durante a auditoria de 2026-05, foram identificados três padrões distintos de instanciação do grafo:

| Padrão | Onde encontrado | Problema |
|--------|----------------|----------|
| `graph = StateGraph(...).compile()` no escopo do módulo | Alguns agentes legados | Falha na importação propaga erro para todo o processo; impede hot-reload |
| `self._graph = self._build_graph().compile()` em `__init__` | Maioria dos agentes recentes | Compila antes de `self.config` estar disponível em alguns casos |
| `_build_graph(self) → StateGraph` com compilação lazy via `self._graph` | Padrão emergente em agentes novos | Correto, mas não documentado como canônico |

A ausência de um padrão documentado gerava inconsistências novas a cada agente escrito. O `AgentRegistryWatcher` (hot-reload) depende de conseguir recriar instâncias de agente sem reiniciar o processo inteiro — o que só é possível se a compilação acontece na instanciação, não no import.

## Decision

Todo grafo LangGraph usado em agentes LIA **deve** ser encapsulado como método `_build_graph(self) -> StateGraph` na classe do agente. O grafo compilado é armazenado em `self._graph` com inicialização lazy (compilado na primeira chamada a `invoke`/`run`, não em `__init__`). Nenhum `StateGraph` pode ser instanciado ou compilado no escopo do módulo.

Regra de implementação canônica:

```python
class MyAgent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self._graph = None  # lazy

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(MyState)
        # ... adiciona nós e arestas usando self.config ...
        return graph

    @property
    def graph(self):
        if self._graph is None:
            self._graph = self._build_graph().compile()
        return self._graph
```

## Consequences

**Positivo:**
- Agentes podem ser hot-reloaded pelo `AgentRegistryWatcher` sem reiniciar o processo.
- Erros de compilação do grafo são capturados na instanciação do agente, não no import do módulo — o restante do sistema continua operacional.
- O grafo pode usar `self.config` livremente (disponível antes da compilação lazy).
- Testabilidade: o grafo pode ser reconstruído por teste com configs diferentes na mesma sessão.

**Negativo:**
- Boilerplate adicional por agente (property `graph` + método `_build_graph`).
- A primeira invocação do agente carrega custo de compilação (único, amortizado).

## Guard

O sensor `scripts/check_module_level_graphs.py` (a criar no Sprint seguinte) falha CI se detectar `StateGraph(` ou `.compile()` fora de método de instância em qualquer arquivo `app/agents/**.py` ou `app/domains/**/agents/**.py`.

## Open Questions

- Se a compilação lazy deve ocorrer eager em `__init__` (melhor para health checks de startup) ou na primeira chamada (melhor para import-time). Decisão atual: lazy na primeira chamada; pode ser revisada se startup health checks precisarem validar todos os grafos.
