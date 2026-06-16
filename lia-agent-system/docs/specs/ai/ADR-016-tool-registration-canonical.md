# ADR-016: Sistema canônico de registro de ferramentas (Task #351)

**Status:** Accepted
**Data:** 2026-04-17
**Relacionado:** ADR-015 (S7.1/S7.2/S7.3), Task #350 (não-execução), `RAILS_API_INTEGRATION.md`
**Sucessor operacional:** ADR-018 (plano de execução, acceptance criteria, canary fitness tests — Task #382)

---

## Contexto

Hoje convivem três peças que parecem fazer a "mesma coisa":

| # | Peça | Onde | O que faz hoje |
|---|------|------|----------------|
| 1 | `ToolRegistry` global + `ToolDefinition` | `app/tools/registry.py` (169 linhas) | Container in-memory de ferramentas; gera schemas Claude/Gemini; consultado por orchestrator, `agentic_loop`, `executor`, `libs/agents-core/nodes`, `agent_studio`, `ai/services`. Populado no boot por `app/tools/__init__.py:initialize_tools()` (~84 ferramentas, ~12 módulos). |
| 2 | `@tool_handler` decorator | `app/shared/tool_handler.py` (115 linhas) | Wrapper canônico para autoria de ferramenta de domínio: tenant check (`company_id` obrigatório), module gating (feature flags por empresa), normalização de erro, formato de resposta padronizado. Usado por **30** arquivos `*_tool_registry.py` em `app/domains/*/agents/`. |
| 3 | `tool_permissions.yaml` + loader + `scope_config.py` | `app/tools/` (~840 linhas no total) | Camada declarativa de governança: (a) mapeia `scope → [tool_names]` para escopos de UI (`TALENT_FUNNEL`, `JOB_TABLE`, `IN_JOB`), (b) lista `restricted_tools` que exigem HITL, (c) configura `llm_provider` / `llm_fallback_order` por tenant — consumido por `llm_factory._load_from_permissions` (linhas 349-369). |

A Task #350 propôs apagar três desses arquivos como "código morto"; a verificação mostrou que estão vivos. O ADR-015 §S7.2 já anotou que `GlobalToolRegistry` foi aposentado — sobraram exatamente as três peças acima, e nenhuma é redundante uma da outra: elas têm responsabilidades **diferentes**, não duplicadas. O que falta é um contrato explícito de quem é "fonte" e quem é "consumidor".

## Decisão

### 1. `@tool_handler` + `*_tool_registry.py` é a superfície canônica de **autoria**

Toda ferramenta nova nasce como uma função decorada com `@tool_handler(domain=..., require_company=True, module=...)` dentro de `app/domains/<domínio>/tools/` e é exposta via `get_<domínio>_tools()` em `app/domains/<domínio>/agents/<algo>_tool_registry.py`. Não se escreve mais `tool_registry.register(ToolDefinition(...))` à mão.

Justificativa: é onde já vivem 30 registries e ~80% das ferramentas; carrega tenant isolation, module gating, fail-closed e formato de erro uniformes; e é coberto pelo guard S7.3 (proibição do `@tool` do langchain).

### 2. `app/tools/registry.py` continua, mas vira **plumbing de execução**, não superfície de autoria

`ToolRegistry` permanece como o índice in-memory que `ActionExecutor`, `agentic_loop` e o orchestrator consultam por nome para obter `ToolDefinition.handler` + schema. O `initialize_tools()` passa a ser puramente um agregador: percorre os `get_*_tools()` dos domínios e chama `tool_registry.register(...)` em nome deles. Nenhum código de produto fora de `app/tools/__init__.py` deve invocar `tool_registry.register` diretamente.

Justificativa: orchestrator e executor precisam de um lookup central por `name`; reescrever isso é trabalho gratuito. O custo é só renomear mentalmente "registry" como "router de execução".

### 3. `tool_permissions.yaml` continua, com **escopo reduzido**

Quebramos a YAML em três responsabilidades, com destinos diferentes:

| Conteúdo atual | Destino canônico | Por quê |
|---|---|---|
| `scopes:` (mapping `scope → tool_names`) | **Permanece em YAML.** Versão-controlado com o código. | É governança de UI/contexto, baixa cardinalidade, muda raramente, precisa de code review. |
| `restricted_tools:` (HITL gating) | **Permanece em YAML.** | Mesmo motivo + audit trail por commit. |
| `llm_provider` / `llm_fallback_order` por tenant | **Migra para DB** (`tenant_llm_config`, já existe — ver `llm_factory.load_from_db`). YAML mantém só os defaults do sistema. | Configuração por-tenant não pertence a um arquivo versionado; já existe caminho DB e o `_load_from_permissions` atual é só um fallback sem owner claro. |

### 4. Integração com `rails-ats-api` não move o registro de ferramentas

Quando o bridge para `ats-api-copia` for ligado (ver `RAILS_API_INTEGRATION.md`), as ferramentas continuam **registradas em Python** via `@tool_handler`. O que muda é a *implementação interna* da função decorada: ela passa a chamar o `RailsAdapter` (HTTP, com circuit breaker) em vez do repositório local quando `RAILS_API_URL` está setado. Isso preserva tenant check, scope, HITL e audit num único lugar (Python) em vez de fragmentar em dois sistemas de permissão (Python + Rails).

A única exceção autorizada é se o Rails ganhar tools próprias para um agente que rode dentro do Rails — esse caso ainda não existe e quando existir merece um ADR próprio.

## Consequências

**Bom:** autoria fica em um só lugar (`@tool_handler`); execução fica em um só lugar (`ToolRegistry`); governança de escopo fica em um só lugar (YAML); config por-tenant sai da YAML e vai pro DB onde já tem dono.

**Ruim:** `app/tools/registry.py` continua existindo apesar de não ser superfície de autoria, o que pode confundir leitores. Mitigação: docstring no topo do arquivo deixando claro "esta é a tabela de roteamento de execução, autoria mora em `@tool_handler`".

**Custo de migração:** baixo. As 30 registries de domínio já estão no padrão canônico. Os ajustes são pontuais (ver plano abaixo).

## Plano de migração (não execução, apenas ordem)

Escopo: apenas o que muda *além* do que já está pronto. Cada item é uma task futura.

1. **Documentar** (este ADR + parágrafo S7.4 em `ARCHITECTURE.md`). ← feito nesta task.
2. **Docstring em `app/tools/registry.py`** marcando o arquivo como "execution router, not authoring surface" e apontando para `@tool_handler`.
3. **Auditoria de chamadas diretas a `tool_registry.register`** fora de `app/tools/__init__.py` e fora de `app/tools/registry.py` em si. O grep inicial mostrou 12 módulos grandfathered no `ALLOW_LIST` do guard S7.5; cada um precisa ser convertido para `@tool_handler` + `get_<domínio>_tools()` agregado em `initialize_tools()`. **Progresso:** `app/domains/cv_screening/tools/cv_match_tool.py` migrado (Task #417) — restam 11 entradas no allow list.
4. **Migração da config LLM por tenant para DB:**
   - 4a. Garantir que `tenant_llm_config` cobre `llm_provider` + `llm_fallback_order` (parece já cobrir — confirmar schema).
   - 4b. Mudar `llm_factory._load_from_permissions` para ser apenas o fallback de sistema (sem `tenant_id`); o caminho normal vira `load_from_db(tenant_id)`.
   - 4c. Remover de `tool_permissions.yaml` quaisquer entradas que sejam config-por-tenant (manter só defaults globais).
   - 4d. Migration de dados: ler YAML existente, popular `tenant_llm_config` para tenants já configurados.
5. **Guard de CI (S7.5):** ✅ Task #354 — `scripts/check_tool_authoring_surface.py` falha se aparecer `tool_registry.register(` fora de `app/tools/__init__.py` / `app/tools/registry.py`. Espelha o estilo dos guards S7.1–S7.3, com `ALLOW_LIST` grandfathereando os 12 módulos pré-existentes; novos arquivos são bloqueados desde o dia 1. Wired no pre-commit como `tool-authoring-surface` e documentado em `ARCHITECTURE.md` §S7.5.
6. **Atualizar onboarding/README** do `lia-agent-system` para descrever os três papéis (autoria / execução / escopo) com um exemplo de "como adicionar uma tool nova".

Itens 2-3 são pequenos. Item 4 é o maior (data migration). Item 5-6 são polimento e podem ir junto com qualquer task que mexa em tools.

## Não-decisões (deixadas em aberto de propósito)

- Se o `ToolRegistry` deveria ser substituído por um simples `dict[str, ToolDefinition]`. Sim, provavelmente; mas o ganho é estético e não justifica risco enquanto o orchestrator depende dele.
- Como o `agent_studio` deve ler o registry. Hoje lê direto; a alternativa seria via API HTTP. Fica para quando o studio sair de protótipo.
- Schema de validação para `tool_permissions.yaml` (jsonschema/pydantic). Recomendado, mas fora do escopo desta decisão.
