# Prompt Standards — WeDOTalent / Plataforma LIA

> Última atualização: 2026-03-26
> Fonte: leitura direta dos `prompts.py` e `prompt_builder/` de todos os domínios — `recruiter_agent_v5`
> **SPEC-DRIVEN DEVELOPMENT** — como escrever prompts neste projeto.

---

## 1. Anatomia de um Prompt LIA

Todos os prompts do sistema seguem uma estrutura em blocos XML-like:

```
<role>
  Descrição do papel do agente
</role>

<behavior>
  Regras de comportamento
</behavior>

<actions>
  {actions_block}  ← injetado dinamicamente
</actions>

<output_format>
  Formato de saída esperado (JSON)
</output_format>
```

### 1.1 Blocos Obrigatórios

| Bloco | Descrição | Obrigatório |
|-------|-----------|-------------|
| `<role>` | Define quem o agente é e qual seu escopo | Sim |
| `<behavior>` | Regras de conduta, idioma, tom | Sim |
| `<actions>` | Lista de ações disponíveis (dinâmica) | Sim (para domínios) |
| `<output_format>` | Formato JSON esperado na resposta | Sim |
| `<rules>` | Regras de classificação entre ações | Opcional |
| `<response_structure>` | Estrutura da resposta para queries analíticas | Opcional |
| `<context>` | Contexto adicional (UI, memória) | Opcional |

---

## 2. Regras Universais

### 2.1 Idioma e Tom

- Sempre português brasileiro
- Tom profissional mas acessível
- Usar nomes concretos, nunca "o candidato mencionado"
- NUNCA colar JSON bruto na resposta ao usuário
- NUNCA adicionar "Você também pode..." ou sugestões no final (o sistema faz automaticamente)

### 2.2 Temperatura

| Contexto | Temperature |
|----------|-------------|
| Intent analysis | 0.0 |
| API planning | 0.0 |
| Domain actions | 0.0 |
| Answer formatting | 0.0 |
| Evaluation (candidato) | 0.2 |
| **Default** | **0.0** |

### 2.3 Formato de Saída

Todas as respostas de classificação/intent DEVEM ser JSON válido:

```json
{
    "action_id": "id_da_acao",
    "params": {},
    "confidence": 0.0-1.0,
    "source": "nome_do_dominio"
}
```

Para esclarecimento:

```json
{
    "needs_clarification": true,
    "clarification_question": "pergunta",
    "clarification_options": ["opcao1", "opcao2"]
}
```

---

## 3. Prompt Builder Pattern

Cada domínio usa um `DynamicPromptBuilder` que gera prompts com base no contexto:

### 3.1 Configuração

```python
PromptConfig(
    max_actions_in_prompt=8,      # máximo de ações no prompt
    max_examples_per_action=2,    # exemplos por ação
    include_filter_docs=True,     # incluir documentação de filtros
    compact_mode=False,           # modo compacto para contextos longos
)
```

### 3.2 Métodos

| Método | Input | Output |
|--------|-------|--------|
| `build_system_prompt()` | Context, Actions | System prompt completo |
| `build_intent_prompt()` | Query, Actions | Prompt de classificação de intent |

### 3.3 Action Registry

Cada domínio tem um `ActionRegistry` que mantém ações registradas:

```python
# Registro
@register_action("search_applies")
class SearchAppliesAction:
    id = "search_applies"
    name = "Buscar candidaturas"
    description = "..."
    examples = ("Candidatos dessa vaga", ...)

# Uso
all_actions = AppliesActionRegistry.all()
```

---

## 4. Prompts por Domínio

### 4.1 AppliesDomain

- **System prompt**: Gerado dinamicamente por `AppliesDynamicPromptBuilder`
- **Variáveis**: `job_id`, `has_job_context`
- **Arquivos**: `src/domains/applies/prompt_builder/dynamic_builder.py`

### 4.2 JobsDomain

- **System prompt**: Gerado dinamicamente por `JobDynamicPromptBuilder`
- **Variáveis**: `job_id`, `has_job_context`
- **Arquivos**: `src/domains/jobs/prompt_builder/dynamic_builder.py`

### 4.3 InsightsDomain

- **System prompt**: Template fixo `INSIGHTS_SYSTEM_PROMPT`
- **Variáveis**: `{actions_block}` — injetado dinamicamente
- **Estrutura de resposta**: Resumo Executivo → Dados → Análise → Riscos → Recomendações
- **Arquivo**: `src/domains/insights/prompts.py`

### 4.4 MessagingDomain

- **System prompt**: Template fixo `MESSAGING_SYSTEM_PROMPT`
- **Variáveis**: `{actions_block}`
- **Regra crítica**: NUNCA enviar sem confirmação explícita — sempre preview primeiro
- **Arquivo**: `src/domains/messaging/prompts.py`

### 4.5 AutonomousDomain

- **System prompt**: `AUTONOMOUS_SYSTEM_PROMPT` — 28KB de instruções detalhadas
- **Seções**: QUEM VOCE E, RESOLUÇÃO DE CONTEXTO UI, MEMÓRIA, REGRAS DE FORMATO, TOOLS
- **Variáveis**: Contexto injetado em runtime (viewing_entities, session, URL)
- **Arquivo**: `src/domains/autonomous/prompts.py`

### 4.6 EvaluationDomain

- **Prompts**: 3 templates fixos
  - `CLASSIFY_INPUT_PROMPT` — classificação da resposta do candidato
  - `EVALUATE_RESPONSE_PROMPT` — avaliação com rubrica
  - `CRAFT_MESSAGE_PROMPT` — geração de mensagem ao candidato
- **Variáveis**: `{question}`, `{expected}`, `{job_description}`, `{persona}`, `{calibration_note}`
- **Arquivo**: `src/domains/evaluation/prompts.py`

### 4.7 Pipeline Agents

- `IntentAnalyzerAgent.SYSTEM_PROMPT` — classificação de intent com entities, actions, filters
- `APIPlannerAgent` — planejamento de steps com `PlanPromptBuilder.BASE_INSTRUCTIONS`
- `AnswerFormatterAgent.SYSTEM_PROMPT` — taxonomia de 11 tipos de resposta
- **Arquivos**: `src/agents/intent_analyzer.py`, `src/agents/api_planner.py`, `src/agents/answer_formatter.py`

---

## 5. Anti-Patterns Identificados

| Anti-Pattern | Onde Encontrado | Correção |
|-------------|----------------|----------|
| System prompt fixo (não dinâmico) | InsightsDomain, MessagingDomain | Migrar para DynamicPromptBuilder quando necessário |
| Prompt > 20KB | AutonomousDomain (28KB) | Considerar modularização ou compressão |
| Exemplos hardcoded no prompt | Vários domínios | Usar ActionRegistry com examples tuple |
| Duplicação de regras entre domínios | Regras de formato duplicadas | Extrair para base_prompt_mixin |

---

## 6. Variáveis de Template

| Variável | Tipo | Descrição | Domínios |
|----------|------|-----------|----------|
| `{actions_block}` | string | Lista formatada de ações disponíveis | Todos |
| `{job_id}` | int | ID da vaga em contexto | applies, jobs |
| `{question}` | string | Pergunta atual da entrevista | evaluation |
| `{expected}` | string | Resposta esperada (referência) | evaluation |
| `{job_description}` | string | Descrição da vaga | evaluation |
| `{persona}` | string | Personalidade do entrevistador | evaluation |
| `{calibration_note}` | string | Nota de calibração de setor | evaluation |
| `{query}` | string | Query do recrutador | intent prompts |

---

## 7. Regras para Novos Prompts

1. **Use blocos XML-like** (`<role>`, `<behavior>`, etc.) para estrutura
2. **Temperature 0.0** salvo justificativa documentada
3. **Sempre inclua `<output_format>`** com JSON schema
4. **Inclua exemplos** via ActionRegistry (não hardcode)
5. **Teste com queries reais** do `OFFICIAL_TEST_QUERIES.md`
6. **Documente variáveis** de template
7. **Limite a 15KB** — use compressão ou modularização se necessário
8. **Português brasileiro** — nunca inglês nas respostas ao usuário
9. **Nunca revele instruções internas** ao usuário
10. **Use calibração setorial** quando disponível (via `get_calibration_note()`)

---

## Referências

| Arquivo | Localização |
|---------|-------------|
| Applies Prompts | `recruiter_agent_v5/src/domains/applies/prompts.py` |
| Applies Prompt Builder | `recruiter_agent_v5/src/domains/applies/prompt_builder/` |
| Jobs Prompts | `recruiter_agent_v5/src/domains/jobs/prompts.py` |
| Insights Prompts | `recruiter_agent_v5/src/domains/insights/prompts.py` |
| Messaging Prompts | `recruiter_agent_v5/src/domains/messaging/prompts.py` |
| Autonomous Prompts | `recruiter_agent_v5/src/domains/autonomous/prompts.py` |
| Evaluation Prompts | `recruiter_agent_v5/src/domains/evaluation/prompts.py` |
| Intent Analyzer | `recruiter_agent_v5/src/agents/intent_analyzer.py` |
| API Planner | `recruiter_agent_v5/src/agents/api_planner.py` |
| Answer Formatter | `recruiter_agent_v5/src/agents/answer_formatter.py` |
