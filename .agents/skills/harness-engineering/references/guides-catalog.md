# Catalogo de Guides (feedforward)

Guides reduzem a probabilidade de o agente errar na primeira tentativa. Sao injetados deterministicamente no contexto antes da decisao do LLM.

## Computacionais (deterministicos, baratos)

| Categoria               | Exemplo concreto                                                                 | Onde vive                                           |
|-------------------------|----------------------------------------------------------------------------------|-----------------------------------------------------|
| Regra de projeto        | "Toda rota nova deve ter teste de tenant isolation"                              | `CLAUDE.md`, `AGENTS.md`                            |
| Convencao de naming     | "Hooks de dado prefixados com `use-`; hooks de UI com `useUi`"                  | `CLAUDE.md`, lint custom                             |
| Schema / contrato       | Pydantic model, JSON Schema de tool, OpenAPI spec                                | `app/schemas/`, `app/tools/*/schema.py`             |
| Template                | Skeleton de service, template de commit message, PR template                     | `.github/PULL_REQUEST_TEMPLATE.md`, `templates/`    |
| Linter config           | `ruff.toml`, `eslint.config.js` com regras customizadas                          | raiz do repo                                        |
| System prompt fixo      | Prompt determinístico com role + DomainActions + governance_tags                 | `app/prompts/<agent>/system.md`                     |
| Canonical path          | "Use `app.routes.candidates`, nunca `app.legacy.routes`"                         | `CLAUDE.md`, ADR, CI guard                          |
| Estrutura de pasta      | "Cada agente tem `node.py`, `tools.py`, `prompts/`, `tests/`"                   | `CLAUDE.md`, gerador de scaffold                    |
| Tool description fixa   | Descricao curta + exemplos de uso embutidos no schema da tool                    | tool registry                                       |
| Permission policy       | Lista declarativa de tool x role x tenant                                        | `app/policies/tool_permissions.yaml`                |

## Inferenciais (semanticos, caros)

| Categoria               | Exemplo concreto                                                                 | Onde vive                                           |
|-------------------------|----------------------------------------------------------------------------------|-----------------------------------------------------|
| Instrucao em linguagem natural | "Quando o candidato pedir feedback, use tom empatico e cite criterios objetivos" | `CLAUDE.md`, system prompt do agente                |
| Few-shot examples       | 3-5 pares (input, output) representativos                                        | `app/prompts/<agent>/examples.yaml`                 |
| Persona / role          | "Voce e um recrutador senior, formal, focado em fit cultural"                    | system prompt                                       |
| Decision rubric         | "Priorize: 1) skills tecnicas, 2) experiencia em multi-tenant, 3) cultura"      | system prompt                                       |
| Cross-reference         | "Distinto de X (que faz Y); este aqui faz Z"                                    | descricao de tool ou DomainAction                   |
| Suggested next          | "Apos esta tool, considere chamar sugestao_de_proxima_acao para guiar o usuario" | tool description                                    |

## Heuristica de escolha

1. Se a regra pode ser expressa como **codigo / schema / regex / lista**, vai como **guide computacional**.
2. Se a regra exige **interpretacao semantica / julgamento de tom**, vai como **guide inferencial**.
3. Se a regra envolve **autorizacao** (quem pode fazer o que), nao vira guide — vira **guardrail** (permission gating fora do prompt).

## Sinais de guide ausente

- Mesma instrucao repetida no chat para o agente em sessoes diferentes → falta guide persistente.
- Onboarding novo do time precisa explicar a mesma regra sempre → falta guide em `CLAUDE.md`.
- Bug que aparece em N consumidores ao mesmo tempo → falta guide canonico no produtor.
