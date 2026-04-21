# Catalogo de Guides (feedforward)

Guides reduzem a probabilidade de o agente errar na primeira tentativa. Sao injetados deterministicamente no contexto antes da decisao do LLM.

> **Como usar este catalogo:** as duas primeiras secoes sao **canonicas para a Plataforma LIA** — exemplos reais, com path, descricao e celula da matriz. Use-os como template antes de propor qualquer guide novo. As duas ultimas secoes ("Generico") ficam como referencia metodologica para domínios que ainda nao tem equivalente LIA.

---

## Guides computacionais — instancias canonicas LIA

| ID interno | Guide                                          | Onde vive                                                                                          | Origem na remediacao | Descricao curta                                                                                                       |
|------------|------------------------------------------------|----------------------------------------------------------------------------------------------------|----------------------|-----------------------------------------------------------------------------------------------------------------------|
| G-LIA-01   | DomainAction como contrato de capacidade       | `lia-agent-system/app/domains/*/actions.py` + `lia-agent-system/app/domains/*/domain.py`           | FIX 1                | Cada acao do dominio e expressa como classe tipada com `id`, `description`, `examples`, `requires_confirmation`. Substitui prompt em texto livre por contrato consultavel pelo router. |
| G-LIA-02   | Glossario auto-gerado de Tools/DomainActions   | `lia-agent-system/docs/GLOSSARIO_ACTIONS_TOOLS.md` (gerado por `scripts/generate_tool_action_glossary.py`) | FIX 1-12             | Source of truth unico — 103 tools + DomainActions com governance_tags, side_effects e status. Forca convergencia entre prompt, registry e codigo. |
| G-LIA-03   | governance_tags no tool registry               | `lia-agent-system/app/tools/tool_registry_metadata.yaml`                                           | FIX 3, FIX 8         | YAML declara `governance_tags` (`fairness_guard`, `requires_hitl`, `multi_tenant`, `pii`, `audit_trail`) por tool. Lido pelo executor antes de toda chamada. |
| G-LIA-04   | requires_confirmation em DomainAction          | `lia-agent-system/app/orchestrator/action_executor/intents_config.py`                              | FIX 10               | Mapping centralizado intent -> DomainAction com `requires_confirmation: True` para acoes sensiveis (`mover_candidato`, `fechar_vaga`). Resolver unificado evita drift prompt vs codigo. |
| G-LIA-05   | YAML coverage do Wizard                        | `lia-agent-system/app/tools/tool_registry_metadata.yaml` (entradas para `extract_job_requirements`, `validate_job_requirements`, etc.) | FIX 5, FIX 10        | Wizard de criacao de vaga compartilha o mesmo registry — toda tool de wizard tem entry YAML, evitando que descricao no prompt e descricao no registry divirjam. |
| G-LIA-06   | Cluster cross-references nas descriptions      | DomainActions em `app/domains/job_management/`, `app/domains/cv_screening/`, `app/domains/sourcing/` | FIX 7, FIX 11        | Acoes semanticamente parecidas (`generate_wsi_questions` em job_management vs cv_screening) carregam texto "Distinto de X (que faz Y)". Reduz ambiguidade no router LLM. |
| G-LIA-07   | Routing prompt com `{actions_context}` antes de `{message}` | `lia-agent-system/app/orchestrator/llm_cascade.py` (`_ROUTING_PROMPT`)                       | FIX 11 (G5)          | Ordem do prompt foi consertada: contexto de acoes injetado **antes** da mensagem do usuario para evitar "lost in the middle" no roteamento. |
| G-LIA-08   | Few-shot examples populados em toda DomainAction | `app/domains/*/actions.py` (validado por `tests/unit/test_fix2_examples_populated.py`)             | FIX 2, FIX 9         | Toda DomainAction tem >= 1 exemplo concreto para few-shot intent matching. Gate de qualidade: <10% de exemplos fracos ("isso"-fallback heuristic). |
| G-LIA-09   | Canonical path enforcement (UUID vs BigInt)    | `lia-agent-system/docs/adr/003-id-strategy-lia-vs-rails.md` + `tests/api/test_dual_id_route_shadowing.py` | Migracao Rails->LIA  | ADR define dual-ID strategy; teste estrutural impoe `DUAL_ID_PATH_PATTERN` em 100+ rotas para impedir shadowing entre legacy e canonico. |
| G-LIA-10   | Canonical sources spec                         | `lia-agent-system/docs/CANONICAL_SOURCES_SPEC.md`                                                  | FIX 1-13             | Documento normativo que diz qual diretorio/arquivo e fonte unica para cada conceito (DomainActions, prompts, registry, schemas). Evita duplicacao em consumidores. |
| G-LIA-11   | RLS contract                                   | `lia-agent-system/docs/RLS_CONTRACT.md`                                                            | Tenant isolation     | Contrato de Row-Level Security: toda tabela multi-tenant declara coluna `tenant_id` e politica RLS. Template de migracao Alembic ja inclui. |
| G-LIA-12   | Anti-agent-hijack guard                        | `lia-agent-system/app/orchestrator/main_orchestrator.py` (regression test em `tests/unit/test_fix14_no_agent_hijack.py`) | FIX 14               | Regra estrutural: hint de onboarding nao pode forcar `_agent_type`. Teste estrutural varre o source para garantir que o anti-pattern nao volta. |

## Guides inferenciais — instancias canonicas LIA

| ID interno | Guide                                                  | Onde vive                                                                                  | Origem na remediacao | Descricao curta                                                                                                |
|------------|--------------------------------------------------------|--------------------------------------------------------------------------------------------|----------------------|----------------------------------------------------------------------------------------------------------------|
| G-LIA-13   | Tom empatico em feedback ao candidato                  | `lia-agent-system/app/prompts/domains/wsi_layer2_extraction.yaml` + system prompts WSI     | Stage 2              | Instrucao em linguagem natural sobre tom + criterios objetivos quando interagir com candidato.                 |
| G-LIA-14   | Persona/role por dominio (recrutador senior, hunter)   | system prompts em `lia-agent-system/app/prompts/domains/*`                                 | FIX 1, Stage 2       | Cada dominio carrega persona explicita no system prompt para alinhar tom e prioridade de decisao.              |
| G-LIA-15   | Decision rubric WSI                                    | `lia-agent-system/docs/CONCEITOS_IA_WEDOTALENT.md` + prompts WSI                           | Stage 2              | Rubrica de priorizacao explicita (skills tecnicas > experiencia multi-tenant > cultura) instrui LLM em casos abertos. |
| G-LIA-16   | Suggested next na descricao da tool (`related_tools`)  | `app/tools/tool_registry_metadata.yaml` campo `related_tools`                              | FIX 3, FIX 4         | Descricao de cada tool sugere proximas acoes plausiveis para guiar o LLM em fluxos multi-step.                 |

## Generico — guides computacionais (referencia metodologica)

| Categoria               | Exemplo concreto                                                                 | Onde vive                                           |
|-------------------------|----------------------------------------------------------------------------------|-----------------------------------------------------|
| Regra de projeto        | "Toda rota nova deve ter teste de tenant isolation"                              | `CLAUDE.md`, `AGENTS.md`                            |
| Convencao de naming     | "Hooks de dado prefixados com `use-`; hooks de UI com `useUi`"                  | `CLAUDE.md`, lint custom                            |
| Schema / contrato       | Pydantic model, JSON Schema de tool, OpenAPI spec                                | `app/schemas/`, `app/tools/*/schema.py`             |
| Template                | Skeleton de service, template de commit message, PR template                     | `.github/PULL_REQUEST_TEMPLATE.md`, `templates/`    |
| Linter config           | `ruff.toml`, `eslint.config.js` com regras customizadas                          | raiz do repo                                        |
| System prompt fixo      | Prompt deterministico com role + DomainActions + governance_tags                 | `app/prompts/<agent>/system.md`                     |
| Canonical path          | "Use `app.routes.candidates`, nunca `app.legacy.routes`"                         | `CLAUDE.md`, ADR, CI guard                          |
| Estrutura de pasta      | "Cada agente tem `node.py`, `tools.py`, `prompts/`, `tests/`"                    | `CLAUDE.md`, gerador de scaffold                    |
| Tool description fixa   | Descricao curta + exemplos de uso embutidos no schema da tool                    | tool registry                                       |
| Permission policy       | Lista declarativa de tool x role x tenant                                        | `app/policies/tool_permissions.yaml`                |

## Generico — guides inferenciais (referencia metodologica)

| Categoria                       | Exemplo concreto                                                                 | Onde vive                                           |
|---------------------------------|----------------------------------------------------------------------------------|-----------------------------------------------------|
| Instrucao em linguagem natural  | "Quando o candidato pedir feedback, use tom empatico e cite criterios objetivos" | `CLAUDE.md`, system prompt do agente                |
| Few-shot examples               | 3-5 pares (input, output) representativos                                        | `app/prompts/<agent>/examples.yaml`                 |
| Persona / role                  | "Voce e um recrutador senior, formal, focado em fit cultural"                    | system prompt                                       |
| Decision rubric                 | "Priorize: 1) skills tecnicas, 2) experiencia em multi-tenant, 3) cultura"       | system prompt                                       |
| Cross-reference                 | "Distinto de X (que faz Y); este aqui faz Z"                                     | descricao de tool ou DomainAction                   |
| Suggested next                  | "Apos esta tool, considere chamar sugestao_de_proxima_acao"                      | tool description                                    |

---

## Heuristica de escolha

1. Se a regra pode ser expressa como **codigo / schema / regex / lista**, vai como **guide computacional**.
2. Se a regra exige **interpretacao semantica / julgamento de tom**, vai como **guide inferencial**.
3. Se a regra envolve **autorizacao** (quem pode fazer o que), nao vira guide — vira **guardrail** (permission gating fora do prompt). Ver G-LIA-03 / G-LIA-04 para o padrao na LIA.

## Sinais de guide ausente

- Mesma instrucao repetida no chat para o agente em sessoes diferentes -> falta guide persistente.
- Onboarding novo do time precisa explicar a mesma regra sempre -> falta guide em `CLAUDE.md` ou no glossario (G-LIA-02).
- Bug que aparece em N consumidores ao mesmo tempo -> falta guide canonico no produtor (canonical-fix). Ver G-LIA-09 / G-LIA-10.
