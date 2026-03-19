# ADR 002 — Quando usar LangGraph (Graph) vs. ReAct Loop

**Data:** 04/março/2026
**Status:** Aceito
**Decisores:** André (arquiteto sênior), Victor (lead dev)

---

## Contexto

O codebase tem dois padrões de agente:
1. **LangGraph Graph** (`job_wizard_graph.py`) — fluxo com nós, edges e checkpoints
2. **ReAct Loop** (`react_loop.py`) — loop Reason-Act-Observe iterativo

Ambos coexistem. Este ADR define quando usar cada um.

---

## Decisão

### Usar LangGraph Graph quando:

- O fluxo tem **etapas discretas e conhecidas** com transições explícitas (ex: Wizard de vaga: DRAFT → REVIEW → PUBLISH)
- É necessário **checkpoint/restore de estado** entre sessões longas (usuário abandona e volta)
- O processo tem **branches condicionais complexos** que dependem do output de etapas anteriores
- A operação tem **etapas paralelas** (ex: buscar candidatos em Pearch E no banco simultaneamente)
- O fluxo precisa ser **auditável e rastreável** etapa a etapa (compliance, SOX)

**Exemplos no codebase:**
- `job_wizard_graph.py` — criação de vaga em múltiplas etapas

### Usar ReAct Loop quando:

- O agente precisa **decidir dinamicamente** quais ferramentas usar (não sabe o fluxo de antemão)
- A tarefa é **aberta e conversacional** (o usuário pode fazer qualquer pergunta)
- O número de etapas é **variável e imprevisível**
- Simplicidade é mais importante que auditabilidade de etapas
- Max 5-10 iterações (operações curtas)

**Exemplos no codebase:**
- `pipeline_transition_agent.py` — movimentar candidatos com lógica variável
- `sourcing_react_agent.py` — busca com critérios dinâmicos
- `kanban_react_agent.py` — ações no kanban baseadas em contexto
- `policy_react_agent.py` — configuração de política conversacional

---

## Regra de Ouro

```
Fluxo conhecido + etapas discretas + checkpoint necessário → LangGraph Graph
Decisão dinâmica + conversacional + ferramentas variáveis → ReAct Loop
```

---

## Consequências

- Novos agentes devem ser classificados nesta decisão antes de implementar
- Hibridização (Graph com nós que executam ReAct) é permitida e recomendada para fluxos complexos
- `job_wizard_graph.py` pode ter nós que instanciam um `ReActLoop` para sub-tarefas dinâmicas
