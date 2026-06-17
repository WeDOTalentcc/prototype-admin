# LangSmith Setup — LIA Agent System

## Configuração

Adicione as seguintes variáveis de ambiente (`.env` ou secrets do Replit):

```env
# LangSmith Tracing
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__<sua-api-key>
LANGCHAIN_PROJECT=lia-agent-system
LANGCHAIN_WORKSPACE_ID=<seu-workspace-id>
```

## Onde os traces aparecem

Com o `@traceable` implementado, os seguintes spans são enviados ao LangSmith:

| Span | Tipo | Onde |
|------|------|------|
| `ReAct Loop` | chain | `react_loop.py:run()` |
| `Claude Generate` | llm | `llm_claude.py:generate()` |
| `Claude GenerateWithSystem` | llm | `llm_claude.py:generate_with_system()` |
| `Claude GenerateWithTools` | llm | `llm_claude.py:generate_with_tools()` |
| `Claude GenerateStructured` | llm | `llm_claude.py:generate_structured()` |

## Dashboard LangSmith

Acesse: https://smith.langchain.com → Projects → lia-agent-system

Métricas disponíveis:
- Latência por span
- Taxa de erro por provider
- Inputs/outputs de cada LLM call
- Traces completos do ReAct loop (reason → act → observe)

## Verificação

```bash
# Verificar se tracing está ativo
python -c "import langsmith; print(langsmith.utils.get_tracer_project())"

# Após uma chamada ao ReAct loop, verificar no LangSmith dashboard
# ou via API:
curl https://api.smith.langchain.com/api/v1/runs?project_name=lia-agent-system \
  -H "x-api-key: $LANGCHAIN_API_KEY" | jq '.[0].name'
```
