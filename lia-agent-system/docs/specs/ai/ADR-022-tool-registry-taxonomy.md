# ADR-022 — Tool Registry Taxonomy

**Status:** Accepted
**Date:** 2026-05-02
**Related:**
- ADR-016 (Sistema canônico de registro de ferramentas)
- ADR-018 (Tool registry consolidation migration)
- `app/tools/registry.py`
- `scripts/check_tool_output_schemas.py` (sensor G-TOOLS)

---

## Context

Auditoria de 2026-05 encontrou 76 ferramentas registradas em `app/tools/registry.py` via `ToolDefinition`, mas 356 funções no codebase que aceitam invocações com assinatura compatível com tool calling. A discrepância criou confusão sobre:

1. Quais funções o `GovernanceToolNode` deve governar.
2. Quais funções o sensor `check_tool_output_schemas.py` deve validar.
3. O que conta como "tool" para fins de billing, auditoria e HITL.

Exemplos das 356 funções: repositórios de domínio (`get_candidate_by_id`), helpers internos de agente (`_format_ranking_result`), handlers de action (`handle_invite_action`). Nenhum desses é exposto via LLM function calling — são implementações internas chamadas programaticamente.

## Decision

**Um "Tool" em LIA é exclusivamente uma callable registrada em `app/tools/registry.py` com um `ToolDefinition` que inclui os campos `name`, `description`, `parameters_schema`, `handler`, e `output_schema`.** O registry é a única fonte de verdade sobre o conjunto de tools.

As 356 funções que não possuem `ToolDefinition` no registry são **service functions internas** — não são tools. Elas não são governadas pelo `GovernanceToolNode`, não são validadas pelo `check_tool_output_schemas.py`, e não aparecem em nenhum schema de LLM function calling.

| Tipo | Definição | Governança | Exemplo |
|------|-----------|------------|---------|
| **Tool** | Registrada em `app/tools/registry.py` com `ToolDefinition` | `GovernanceToolNode`, G-TOOLS sensor, HITL se `restricted_tools` | `search_candidates`, `create_job_posting` |
| **Service function** | Chamada programática interna, sem `ToolDefinition` | Nenhuma (responsabilidade do chamador) | `get_candidate_by_id`, `_format_ranking_result` |

A fronteira é: **se o LLM pode escolher chamar, é uma tool; se só o código chama, é uma service function**.

## Consequences

**Positivo:**
- `check_tool_output_schemas.py` (G-TOOLS) valida apenas as 76 ferramentas registradas — o sensor não falha em falsos positivos por service functions.
- `GovernanceToolNode` governa exatamente o conjunto exposto ao LLM — sem sobre-governança de código interno.
- Onboarding claro: "tool" tem critério de entrada objetivo (registro + `ToolDefinition`).
- Auditoria de HITL é precisa: lista de `restricted_tools` em `tool_permissions.yaml` aponta só para tools reais.

**Negativo:**
- Desenvolvedores que chamam service functions com output parecido com tool output podem não perceber que não estão sujeitos à validação G-TOOLS. Mitigação: docstring em `app/tools/registry.py` explica a distinção.
- 356 - 76 = 280 funções ficam sem validação de output schema formal. Aceito por ora; se um domínio específico apresentar bugs de contrato, pode-se criar um sensor dedicado.

## Não-decisões

- Se service functions devem ter seus próprios schemas de output (pydantic models). Recomendado para domínios críticos (cv_screening, ranking), mas fora do escopo deste ADR.
- Se o número 76 é o correto ou se existem tools não registradas que deveriam estar. Esse inventário é coberto pela ADR-018 e pela task de migração associada.
