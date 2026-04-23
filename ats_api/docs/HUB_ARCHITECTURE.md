# Hub Multi-Agent: Meta-Orquestrador de Domínios

## Context

O sistema atual tem 2 domínios isolados (`sourced_profile_sourcing` e `evaluation`) + um modo global. O Rails decide qual domínio chamar via campo `domain` na mensagem. Isso limita o sistema a operar um domínio por vez.

O objetivo é criar um **Hub** — um meta-orquestrador que recebe uma instrução do usuário, analisa quais domínios/multi-agentes precisa chamar, decompõe em sub-tarefas, e coordena a execução entre múltiplos domínios. Exemplo: "busque os top 5 candidatos do sourcing X e crie applies para a vaga Y" → sourcing (busca) → global/novo domínio (cria applies).

---

## Arquitetura Atual (Como é Hoje)

```
Rails Backend (envia domain explícito)
    │
    ▼
MessageRouter.route()
    ├─ domain presente → DomainOrchestrator → DomainWorkflow → Domain específico
    │                                                            ├─ sourced_profile_sourcing (MultiAgentOrchestrator + 6 agents)
    │                                                            └─ evaluation (4-node LangGraph)
    └─ domain ausente  → WorkflowOrchestrator (6-node global pipeline)
```

Limitações:
- Um domínio por request
- Rails precisa saber qual domínio chamar
- Não há composição cross-domain

---

## Arquitetura Proposta (Hub)

```
Rails Backend (envia query + context, SEM domain obrigatório)
    │
    ▼
MessageRouter.route()
    ├─ domain explícito  → DomainOrchestrator (mantém compatibilidade)
    ├─ hub_mode: true    → HubOrchestrator (NOVO)
    └─ sem domain        → WorkflowOrchestrator (global, mantém)

HubOrchestrator
    │
    ├─ 1. HubPlanner (LLM) — Analisa query, descobre domínios necessários, cria plano
    │     - Recebe: query + domain_catalog (auto-descoberto via DomainRegistry)
    │     - Retorna: HubExecutionPlan com lista de HubTask ordenadas
    │
    ├─ 2. HubExecutor — Executa plano sequencialmente/paralelamente
    │     - Para cada HubTask:
    │       a) Monta DomainContext específico
    │       b) Chama DomainOrchestrator.process_query() (reusa 100% do existente)
    │       c) Coleta resultado e disponibiliza para próximas tasks
    │
    ├─ 3. HubContextManager — Gerencia dados entre domínios
    │     - Mantém resultados intermediários
    │     - Resolve dependências entre tasks (output de um → input de outro)
    │     - Mantém memória conversacional cross-domain
    │
    └─ 4. HubResponseBuilder — Consolida respostas de múltiplos domínios
          - Combina mensagens
          - Unifica suggestions
          - Gera resumo executivo se necessário
```

---

## Componentes Novos

### 1. `src/hub/orchestrator.py` — HubOrchestrator
- Ponto de entrada do hub
- Recebe query + context_data (sem domain obrigatório)
- Coordena planner → executor → response builder
- Reusa `DomainOrchestrator` existente para execução de cada domínio

### 2. `src/hub/planner.py` — HubPlanner
- Usa LLM (Gemini) para analisar a query
- Recebe catálogo de domínios (auto-gerado via DomainRegistry)
  - Cada domínio expõe: domain_id, domain_name, description, allowed_actions
- Retorna `HubExecutionPlan`:
  ```python
  @dataclass
  class HubTask:
      domain_id: str
      query: str
      context_overrides: Dict[str, Any]
      depends_on: Optional[str]
      output_key: str

  @dataclass
  class HubExecutionPlan:
      tasks: List[HubTask]
      strategy: str  # "sequential" | "parallel" | "mixed"
      reasoning: str
  ```
- Se a query envolve apenas 1 domínio → plano com 1 task (fast path)
- Se é cross-domain → plano com múltiplas tasks encadeadas

### 3. `src/hub/executor.py` — HubExecutor
- Executa tasks do plano
- Para cada task:
  - Monta `context_data` com `domain_id` e dados necessários
  - Se tem `depends_on`, injeta resultado da task anterior no context
  - Chama `DomainOrchestrator.process_query(domain_id, query, context_data)`
  - Armazena resultado em `results[task.output_key]`
- Suporta execução paralela para tasks independentes (asyncio/threading)

### 4. `src/hub/context_manager.py` — HubContextManager
- Armazena resultados intermediários (dict de output_key → DomainResponse)
- Resolve referências entre tasks
- Transforma output de um domínio no formato esperado pelo próximo
- Mantém session_id e conversation memory cross-domain

### 5. `src/hub/response_builder.py` — HubResponseBuilder
- Recebe lista de DomainResponse de cada task executada
- Se 1 task → retorna response direto
- Se múltiplas → combina mensagens, unifica dados, lista suggestions de todos
- Pode usar LLM para gerar resposta consolidada natural

### 6. `src/hub/catalog.py` — DomainCatalog
- Lê DomainRegistry e gera catálogo formatado para o LLM
- Para cada domínio registrado, extrai:
  - domain_id, domain_name, description
  - Lista de actions com descrição e exemplos
- Gera prompt de catálogo para o HubPlanner
- Cacheia o catálogo (domínios não mudam em runtime)

---

## Mudanças em Código Existente

### `src/services/message_router.py` (mínima mudança)
- Adicionar terceira rota no `route()`:
  - Se `hub_mode: true` no message → `HubOrchestrator.process()`
  - Mantém rotas existentes intactas (retrocompatibilidade total)

### `src/domains/base.py` (sem mudança)
- Contratos DomainPrompt, DomainContext, DomainResponse continuam iguais

### `src/domains/orchestrator.py` (sem mudança)
- HubExecutor chama `DomainOrchestrator.process_query()` diretamente

### `src/domains/registry.py` (sem mudança)
- HubCatalog usa `DomainRegistry.list_domains()` e `DomainRegistry.get_instance()`

---

## Estrutura de Arquivos

```
src/hub/
├── __init__.py
├── orchestrator.py        # HubOrchestrator - ponto de entrada
├── planner.py             # HubPlanner - LLM decide quais domínios chamar
├── executor.py            # HubExecutor - executa plano chamando DomainOrchestrator
├── context_manager.py     # HubContextManager - dados entre domínios
├── response_builder.py    # HubResponseBuilder - consolida respostas
├── catalog.py             # DomainCatalog - gera catálogo de domínios para o LLM
└── models.py              # HubTask, HubExecutionPlan, HubResult
```

---

## Fluxo de Execução (Exemplo)

**Query:** "Busque os top 3 candidatos com Python do sourcing 123 e gere um relatório comparativo"

1. **MessageRouter** → detecta `hub_mode: true` → `HubOrchestrator.process()`
2. **HubPlanner** (LLM) analisa query + catálogo de domínios:
   - Identifica: precisa do domínio `sourced_profile_sourcing`
   - Cria plano com 1 task (single-domain, fast path):
     ```
     Task 1: sourced_profile_sourcing
       query: "Busque os top 3 candidatos com Python e gere um relatório comparativo"
       context: {sourcing_id: "123"}
     ```
3. **HubExecutor** → chama `DomainOrchestrator.process_query("sourced_profile_sourcing", query, context)`
4. Internamente, o MultiAgentOrchestrator do sourcing detecta multi-step e usa seus agentes
5. **HubResponseBuilder** → retorna DomainResponse direto (single task)

**Query cross-domain:** "Avalie as respostas do candidato João da entrevista e verifique o perfil dele no sourcing 456"

1. **HubPlanner** cria plano:
   ```
   Task 1: evaluation → "Avalie as respostas do candidato João"
   Task 2: sourced_profile_sourcing → "Mostre o perfil detalhado de João"
     context: {sourcing_id: "456"}
   ```
2. **HubExecutor** executa ambas (podem ser paralelas, sem dependência)
3. **HubResponseBuilder** combina as 2 respostas em uma consolidada

---

## Decisões de Design

1. **Trigger**: Flag explícita `hub_mode: true` enviada pelo Rails. Controle total do backend sobre quando usar o hub
2. **Global mode**: WorkflowOrchestrator (6-node pipeline) continua separado e independente. Hub é exclusivamente para orquestração cross-domain
3. **3 rotas no MessageRouter**: domain explícito → DomainOrchestrator | hub_mode → HubOrchestrator | sem domain → WorkflowOrchestrator

## Transição e Compatibilidade

1. **Fase 1**: Hub funciona quando `hub_mode: true` na mensagem. Rotas existentes (`domain` explícito e global) continuam intactas
2. **Fase 2**: Rails começa a enviar `hub_mode: true` para features que precisam de composição cross-domain
3. **Fase 3**: Novos domínios (jobs, candidates, applies, testes) são adicionados via `@register_domain` e automaticamente ficam disponíveis no Hub

---

## Sobre Arquivos Desnecessários no sourced_profile_sourcing

Identificados durante a análise:

1. **`actions/` inteiro (14 arquivos)** — Marcado como deprecated no `__init__.py`. Lógica duplicada com `agents/`. O `domain.py` ainda usa ambos os caminhos. Recomendação: migrar tudo para agents/ e remover actions/
2. **`param_extractor.py` vs `smart_extractor.py`** — Dois sistemas de extração de parâmetros. Consolidar em um só
3. **`fact_checker.py`** — Property existe no BaseAgent mas não é chamada. Implementação possivelmente incompleta
4. **`models.py`** — Sem imports encontrados nos outros arquivos
5. **`template_formatter.py`** — Sem imports explícitos encontrados, formatação feita inline nos agents

---

## Verificação

1. Criar testes unitários para HubPlanner (mock LLM, verificar geração de plano)
2. Criar testes para HubExecutor (mock DomainOrchestrator, verificar execução sequencial e paralela)
3. Teste de integração: query single-domain pelo hub (deve funcionar igual ao fluxo atual)
4. Teste de integração: query cross-domain (2 domínios)
5. Testar retrocompatibilidade: mensagens com `domain` explícito continuam funcionando
6. Testar via CLI: `python main.py` com query de teste
