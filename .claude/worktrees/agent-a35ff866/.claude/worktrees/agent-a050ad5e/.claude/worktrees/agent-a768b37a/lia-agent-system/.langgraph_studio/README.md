# LangGraph Studio — Debug e Inspeção dos Grafos LIA

## O que é

LangGraph Studio é a IDE visual oficial para desenvolvimento e debug de grafos LangGraph.
Permite visualizar fluxos de execução, inspecionar estado em cada nó, replay de execuções e edição ao vivo.

## Grafos disponíveis

| Nome | Arquivo | Descrição |
|------|---------|-----------|
| `wizard_graph` | `app/domains/job_management/agents/job_wizard_graph.py` | Wizard de criação de vagas (StateGraph completo) |
| `wsi_interview_graph` | `app/domains/cv_screening/agents/wsi_interview_graph.py` | Entrevistas WSI com estado serializado (StateGraph) |
| `interview_graph` | `app/domains/interview_scheduling/agents/interview_graph.py` | Agendamento de entrevistas (StateGraph) |

> Agentes ReAct (wizard_react, pipeline_react, sourcing_react, etc.) usam `create_react_agent`
> e não expõem um grafo compilado no módulo — não são configurados no `langgraph.json`.

## Como usar

### Pré-requisitos

```bash
pip install langgraph-cli
```

### Iniciar o Studio

```bash
cd /home/runner/workspace/lia-agent-system
langgraph dev
```

O Studio abre em `http://localhost:8123` por padrão.

### Configuração

O arquivo `langgraph.json` na raiz do projeto define os grafos registrados.
O Studio lê as variáveis de ambiente de `.env`.

### Inspecionar estado de checkpoints

No Studio, clique em qualquer nó para ver:
- Input/output do nó
- Estado completo do grafo naquele ponto
- Histórico de execuções anteriores (via MemorySaver em dev, PostgresSaver em prod)

### Replay de execuções

1. Selecione um thread (session_id) na barra lateral
2. Clique em "Replay" para re-executar qualquer passo
3. Edite o estado e continue a execução a partir de qualquer ponto

### Variáveis de ambiente necessárias

```env
ANTHROPIC_API_KEY=...          # LLM principal
DATABASE_URL=...               # PostgreSQL (para PostgresSaver em prod)
REDIS_URL=...                  # Redis
USE_LANGGRAPH_NATIVE=true      # Ativa paths LangGraph nativos
```

## Estrutura dos grafos

Cada grafo segue o padrão 4 arquivos:
- `agent.py` / `*_graph.py` — definição do grafo
- `tool_registry.py` — ferramentas disponíveis
- `system_prompt.py` — prompt do sistema
- `stage_context.py` — contexto de estágio por nó

## Referências

- [LangGraph Studio docs](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/)
- [LangGraph Cloud](https://langchain-ai.github.io/langgraph/cloud/)
- Arquitetura interna: `app/shared/agents/` e `libs/agents-core/`
