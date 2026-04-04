# Prompt Standards — WeDOTalent / Plataforma LIA

> Última atualização: 2026-03-26
> Fonte: leitura direta de todos os `*_system_prompt.py`, `prompts.py`, YAML domain configs, `defensive_prompts.py`, `anti_sycophancy_block.py`, `interaction_patterns.py` e `PromptLoader`
> **SPEC-DRIVEN DEVELOPMENT** — como prompts são estruturados, carregados e mantidos neste projeto.

---

## 1. Visão Geral da Arquitetura de Prompts

O sistema LIA usa uma arquitetura de prompts em 3 camadas:

```
┌──────────────────────────────────────────────────────────────┐
│  CAMADA 1 — YAML COMPARTILHADOS (shared/)                    │
│  lia_persona.yaml:  LIA_PERSONA, HR_VOCABULARY,              │
│                     DATA_PERSISTENCE_GUIDELINES,              │
│                     ETHICAL_GUIDELINES                        │
│  agent_prompts.yaml: 11 agent-specific prompts               │
│  defensive.yaml:    clarification triggers, out-of-scope,    │
│                     error recovery, ambiguity detection       │
└────────────────────────┬─────────────────────────────────────┘
                         │ PromptLoader.load()
┌────────────────────────▼─────────────────────────────────────┐
│  CAMADA 2 — YAML POR DOMÍNIO (domains/)                      │
│  10 arquivos: sourcing.yaml, cv_screening.yaml,              │
│  job_management.yaml, pipeline_transition.yaml,              │
│  recruiter_assistant.yaml, interview_scheduling.yaml,        │
│  communication.yaml, automation.yaml, ats_integration.yaml,  │
│  analytics.yaml                                              │
│  Cada um define: metadata, persona, scope_in, scope_out,     │
│                  behavioral_rules, system_prompt,             │
│                  intent_examples                              │
└────────────────────────┬─────────────────────────────────────┘
                         │ importado por
┌────────────────────────▼─────────────────────────────────────┐
│  CAMADA 3 — SYSTEM PROMPTS PYTHON (agents/)                   │
│  Prompts detalhados inline em Python:                         │
│  wizard_system_prompt.py (242 linhas)                        │
│  kanban_system_prompt.py (282 linhas)                        │
│  sourcing_system_prompt.py (239 linhas)                      │
│  pipeline_system_prompt.py, talent_system_prompt.py,         │
│  jobs_mgmt_system_prompt.py, policy_system_prompt.py,        │
│  + 5 outros domínios                                         │
│  + anti_sycophancy_block.py (3 variantes)                    │
│  + interaction_patterns.py (NEGATION, CONFIRMATION, CoT)     │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. PromptLoader — Sistema de Carregamento YAML

### 2.1 Implementação

```
Arquivo: app/shared/prompts/loader.py

class PromptLoader:
    _cache: Dict[str, Any] = {}   # Cache in-memory estático

    @classmethod
    def load(cls, path: str) -> Dict[str, Any]:
        # path relativo a app/prompts/ → carrega YAML + cache
        # Ex: PromptLoader.load("shared/lia_persona")
        #     PromptLoader.load("domains/sourcing")

    @classmethod
    def get_domain_prompt(cls, domain_id: str) -> str:
        # Atalho: carrega domains/{domain_id}.yaml → retorna system_prompt

    @classmethod
    def get_shared_prompt(cls, name: str, key: str = None) -> str:
        # Atalho: carrega shared/{name}.yaml → retorna prompt específico
```

### 2.2 Diretório de Prompts

```
app/prompts/
├── shared/
│   ├── lia_persona.yaml      # Persona LIA, vocabulário RH, ética, persistência
│   ├── agent_prompts.yaml    # 11 prompts de agentes especializados (1.687 linhas)
│   └── defensive.yaml        # Triggers de clarificação, out-of-scope, error recovery
└── domains/
    ├── sourcing.yaml          # Busca de talentos
    ├── cv_screening.yaml      # Triagem e WSI
    ├── job_management.yaml    # Criação/gestão de vagas
    ├── pipeline_transition.yaml # Transições de etapa
    ├── recruiter_assistant.yaml # Assistência geral
    ├── interview_scheduling.yaml
    ├── communication.yaml
    ├── automation.yaml
    ├── ats_integration.yaml
    └── analytics.yaml
```

---

## 3. Anatomia de um Prompt LIA

### 3.1 Estrutura Padrão — System Prompt Python (Inline)

Os system prompts dos agentes principais seguem um padrão de seções com delimitadores `=== SEÇÃO ===`:

```
=== IDENTIDADE ===
- Nome: LIA (Assistente de Recrutamento com IA)
- Personalidade: Profissional, amigável, eficiente e proativa
- Idioma: Português Brasileiro (PT-BR)
- Tom: Conversacional mas competente

=== FILOSOFIA CENTRAL ===
O chat é a interface principal. [Regras de interação]

=== INSTRUÇÕES REACT ===
Ciclo: RACIOCINE → AJA → OBSERVE
Ações possíveis: call_tool | respond | ask_clarification

=== ESTÁGIOS DO [DOMÍNIO] ===
[Lista numerada de estágios do fluxo]

=== COLETA DE [CAMPOS/CRITÉRIOS] ===
[Regras de extração de dados da conversa]

=== COMPLIANCE E ÉTICA ===
[Regras de FairnessGuard, LGPD]

=== FAIRNESS_AND_COMPLIANCE ===
[Critérios proibidos com citação legal]

=== PREVENÇÃO DE SYCOPHANCY ===
[5 regras absolutas anti-bajulação]

=== VERIFICAÇÃO DE PREMISSAS ===
[Regras de validação de afirmações do recrutador]

=== TRATAMENTO DE ERROS ===
[Regras de error handling amigável]

=== FORMATO DE RESPOSTA ===
[Markdown, JSON para tool calls]

=== REGRAS CRÍTICAS ===
[7 regras absolutas que nunca podem ser violadas]
```

### 3.2 Estrutura Padrão — YAML por Domínio

```yaml
metadata:
  domain: "sourcing"
  version: "2.0"
  updated_at: "2026-03-19"
  description: "System prompt for Sourcing & Talent Search domain"

persona: |
  Especialista em busca ativa de talentos...

scope_in:
  - Busca de candidatos em banco interno
  - Busca externa via Pearch AI
  - [lista de capacidades]

scope_out:
  - Triagem detalhada de CV (→ cv_screening)
  - Agendamento de entrevistas (→ interview_scheduling)

behavioral_rules:
  - Sempre apresentar score de compatibilidade
  - Nunca inferir atributos protegidos
  - [regras de comportamento]

system_prompt: |
  Você é LIA, especialista em [domínio] da WeDOTalent.
  ## Sua Missão
  ## O Que Você Faz
  ## Regras de Comportamento
  ## Formato de Resposta

intent_examples:
  - "buscar candidatos para esta vaga"
  - "encontrar profissionais com experiência em Python"
```

### 3.3 Estrutura Padrão — YAML Compartilhado

```yaml
metadata:
  domain: "shared"
  version: "1.0"
  description: "..."

prompts:
  lia_persona: |
    ## Persona LIA
    ### Identidade
    ### Tom de Comunicação
    ### Evite
    ### Use

  hr_vocabulary: |
    ## Vocabulário Técnico de RH Brasileiro
    [tabelas por categoria: Processo, Avaliação, Senioridade, etc.]

  data_persistence_guidelines: |
    ## Diretrizes de Persistência de Dados (OBRIGATÓRIO)
    [5 regras de persistência com tabela de campos críticos]

  ethical_guidelines: |
    ## Diretrizes Éticas Obrigatórias
    [4 seções: Critérios Permitidos, Proibidos, Linguagem, Transparência]
```

---

## 4. Catálogo de Variáveis de Template

### 4.1 Variáveis do Wizard System Prompt

| Variável | Fonte | Uso |
|----------|-------|-----|
| `{memory_summary}` | `WorkingMemoryService` | Resumo da memória de trabalho do agente |
| `{stage_context}` | Stage context injector | Contexto formatado do estágio atual |
| `{{context}}` | `get_agent_prompt()` | Contexto genérico injetado em agent prompts |

### 4.2 Variáveis dos Prompts Defensivos

| Variável | Fonte | Uso |
|----------|-------|-----|
| `{message}` | Mensagem do usuário | Detecção de ambiguidade |
| `{context}` | Contexto da sessão | Estado atual para validação |
| `{error}` | Exception capturada | Prompt de error recovery |
| `{operation}` | Operação que falhou | Contexto da operação |
| `{action}` | Ação de confirmação | Template de confirmação |
| `{options}` | Lista de opções | Apresentação de alternativas |
| `{saved_data}` | Dados salvos | Confirmação de persistência |
| `{ats_status}` | Status de sync | Status de sincronização ATS |
| `{next_steps}` | Próximos passos | Orientação ao recrutador |

### 4.3 Variáveis de Clarificação (defensive.yaml)

| Key | Template | Quando usar |
|-----|----------|-------------|
| `missing_job` | "Qual vaga você está trabalhando?" | Contexto de vaga ausente |
| `missing_candidate` | "Qual candidato você está avaliando?" | Contexto de candidato ausente |
| `ambiguous_action` | "Não tenho certeza do que você quer fazer..." | Intenção ambígua |
| `missing_date` | "Para quando você gostaria de agendar?" | Data/horário faltante |
| `missing_criteria` | "Quais critérios você gostaria de usar?" | Critérios de busca ausentes |
| `confirm_action` | "Só para confirmar: você quer {action}?" | Confirmação de ação |
| `partial_match` | "Não encontrei exatos, mas similares..." | Resultados parciais |
| `empty_result` | "Não encontrei resultados com esses critérios..." | Busca sem resultados |

---

## 5. Blocos Compartilhados Reutilizáveis

### 5.1 Anti-Sycophancy — 3 Variantes

O sistema possui 3 variantes do bloco anti-sycophancy, selecionadas por contexto do agente:

```
Arquivo: app/shared/prompts/anti_sycophancy_block.py

ANTI_SYCOPHANCY_OPERATIONAL  → Talent, Kanban, Jobs Management
  - Contexto de análise/ação
  - 5 regras: não concordar com filtros discriminatórios, verificar
    antes de confirmar, discordância com dados

ANTI_SYCOPHANCY_FULL         → Wizard, Policy
  - Contexto consultivo/estratégico
  - 5 regras + VERIFICAÇÃO DE PREMISSAS (5 sub-regras)
  - Mais restritivo: verificar histórico, nunca mudar silenciosamente

ANTI_SYCOPHANCY_ORCHESTRATOR → Orchestrator
  - Versão compacta (1 frase)
  - Ponto de entrada global
```

**Crença #11 do Manifesto WeDOTalent**: "Anti-sycophancy em 100% das interações IA."

### 5.2 Interaction Patterns — Módulo Compartilhado

```
Arquivo: app/shared/prompts/interaction_patterns.py

NEGATION_WORDS = {"não", "espera", "ainda não", "calma", "volta",
                  "cancelar", "parar", "desistir", "esqueça", ...}
                  (20+ palavras)

CONFIRMATION_WORDS = {"sim", "pode", "vamos", "avança", "ok",
                      "beleza", "perfeito", "bora", "certo", ...}
                      (22+ palavras)

NEGATION_DETECTION_BLOCK = """
  Antes de executar qualquer ação:
  - Se negação explícita → CANCELE a ação
  - Se ambiguidade → PERGUNTE antes
  - Para ações irreversíveis → SEMPRE confirme
  - NUNCA execute ação que o usuário acabou de negar
"""

CHAIN_OF_THOUGHT_BLOCK = """
  SEMPRE raciocine antes de responder:
  <thought>
  1. O que o recrutador realmente precisa?
  2. Quais ferramentas são relevantes?
  3. Há risco de compliance, fairness ou LGPD?
  4. Qual o próximo passo concreto?
  </thought>
"""

ANTI_SYCOPHANCY_BLOCK = """
  5 regras: nunca concordar para evitar conflito,
  dados contradizem pedido → apresentar dados primeiro, etc.
"""
```

### 5.3 Defensive Prompt Section

Bloco padrão injetado em todos os agentes via `get_defensive_prompt_section()`:

```
## Tratamento de Ambiguidades e Erros

### Quando Pedir Clarificação
1. Intenção não clara
2. Informações essenciais faltando (vaga, candidato, data)
3. Múltiplas interpretações possíveis
4. Contexto não corresponde à solicitação

### Respostas para Solicitações Fora do Escopo
1. Recuse educadamente
2. Explique brevemente o motivo
3. Sugira o que PODE fazer
4. Ofereça redirecionar

### Tratamento de Erros
1. Nunca exponha detalhes técnicos
2. Mensagens amigáveis e construtivas
3. Ofereça alternativas
4. Registre o erro (logging)

### Confirmação de Ações Críticas
1. Confirme antes de executar
2. Mostre resumo do que será feito
3. Informe quando concluído
4. Detalhe onde os dados foram salvos

### Cancelamento Mid-Flow
1. Confirme o cancelamento
2. Limpe estado do workflow
3. Ofereça opções de próximos passos
4. Não perca dados já salvos
```

---

## 6. Few-Shot Examples — Padrão de Implementação

### 6.1 Estrutura (sourcing/prompts.py)

O sistema usa few-shot examples como dicionários Python com 4 campos:

```python
SEARCH_PYTHON_CANDIDATES = {
    "user": "Busque candidatos Python sênior...",
    "assistant": """🔍 **Resultado da Busca**
        [resposta formatada com tabelas, análise, persistência, próximos passos]""",
    "intent": "search_candidates",
    "context": {
        "vaga": "Desenvolvedor Backend Python",
        "vaga_id": "DEV-PY-2024-001",
        "etapa": "sourcing",
        "skills_buscadas": ["Python", "FastAPI", "AWS"]
    }
}
```

### 6.2 Catálogo de Few-Shot Examples (Sourcing)

| Nome | Intent | Cenário |
|------|--------|---------|
| `SEARCH_PYTHON_CANDIDATES` | `search_candidates` | Busca com resultados abundantes (56 candidatos) |
| `GENERATE_BOOLEAN_STRING` | `generate_boolean` | Geração de boolean string com variações |
| `SUGGEST_CANDIDATES_FOR_JOB` | `suggest_candidates` | Sugestão de candidatos do banco interno |
| `PERSONALIZED_OUTREACH` | `personalized_outreach` | Mensagem personalizada (WhatsApp + LinkedIn) |
| `EMPTY_SEARCH_RESPONSE` | `search_candidates` | Busca vazia com recomendações de flexibilização |

### 6.3 Padrão de Resposta dos Few-Shot Examples

Todas as respostas few-shot seguem este template:

```
[Emoji] **Título da Ação**

**Resumo/Contexto**: [dados da operação]

---

**Dados Principais**: [tabelas, listas, métricas]

---

**Análise**: [distribuições, tendências, alertas]

---

💾 **Persistência**
- [o que foi salvo]
- Sincronizado com ATS: ✅/❌

➡️ **Próximos Passos Sugeridos**
1. [ação 1]
2. [ação 2]
3. [ação 3]

Deseja que eu [ação sugerida]?
```

---

## 7. Formato de Output do ReAct Loop

### 7.1 JSON de Raciocínio (WIZARD_REASONING_PROMPT)

```json
{
    "thought": "seu raciocínio sobre a situação atual",
    "action": "call_tool | respond | ask_clarification",
    "tool_name": "nome da ferramenta (null se não chamar ferramenta)",
    "tool_args": {},
    "response": "sua resposta ao usuário (null se chamar ferramenta)"
}
```

### 7.2 Ações Disponíveis

| Action | Quando usar | Output esperado |
|--------|-------------|-----------------|
| `respond` | Resposta final ao usuário | `response` com texto em PT-BR + markdown |
| `call_tool` | Precisa executar ferramenta | `tool_name` + `tool_args` |
| `ask_clarification` | Informação insuficiente | `response` com perguntas ao recrutador |

### 7.3 Formato de Resposta ao Usuário

Regras de formatação em todas as respostas:
- **Markdown** para destaques (`**negrito**`, listas, tabelas)
- **Idioma**: sempre PT-BR
- **Nunca**: JSON, stack traces, IDs internos, códigos de erro
- **Emojis**: máximo 1-2 quando apropriado
- **Tratamento**: sempre "você", nunca "vc" ou "tu"

---

## 8. Regras de Temperatura por Domínio

| Contexto | Temperature | Justificativa |
|----------|-------------|---------------|
| ReAct reasoning | `0.3` | Decisões determinísticas, tool calling preciso |
| Default LLM | `settings.LLM_DEFAULT_TEMPERATURE` | Configurável via settings |
| Cascade (Haiku) | `0.3` | Classificação rápida |
| Cascade (Sonnet) | `0.3` | Raciocínio principal |
| OpenAI fallback | `0.7` | Maior criatividade para fallback |

---

## 9. Cascaded Router — Prompts para Classificação de Intenção

O sistema usa um router em 6 tiers com custo crescente:

| Tier | Mecanismo | Custo | Latência |
|------|-----------|-------|----------|
| 0 | MemoryResolver (pronomes/referências) | Zero | ~0ms |
| 1 | LRU in-process (hash MD5) | Zero | O(1) |
| 2 | Redis hash cache (distribuído) | Baixo | ~1ms |
| 3 | VectorSemanticCache (pgvector, cosine ≥ 0.92) | Médio | ~5ms |
| 4 | FastRouter (regex/keyword patterns) | Baixo | O(n) |
| 5 | LLM Cascade (Haiku→Sonnet→Opus) | Alto | ~1-5s |
| Fallback | `clarification_needed` (pergunta ao usuário) | Zero | 0ms |

### 9.1 LLM Cascade — Thresholds de Confiança

```python
cascade = [
    (LLM_FAST_MODEL,     LLM_CASCADE_FAST_THRESHOLD = 0.80),
    (LLM_PRIMARY_MODEL,  LLM_CASCADE_MID_THRESHOLD  = 0.70),
    (LLM_POWERFUL_MODEL, LLM_CASCADE_FALLBACK_THRESHOLD = 0.60),
]
```

Se nenhum modelo atingir o threshold mínimo → `requires_human=True`.

---

## 10. Prompt de Detecção de Ambiguidade

```
Analise a mensagem do usuário e identifique se há ambiguidades:

MENSAGEM: {message}
CONTEXTO ATUAL: {context}

VERIFIQUE:
1. A intenção está clara? (O que o usuário quer fazer?)
2. O alvo está claro? (Qual vaga/candidato/entrevista?)
3. Os parâmetros estão completos? (Datas, critérios, etc.)
4. Há conflito com o contexto atual?

RESPONDA EM JSON:
{
    "is_ambiguous": true/false,
    "ambiguity_type": "intent|target|parameters|conflict|none",
    "missing_info": ["lista do que falta"],
    "clarification_needed": "pergunta a fazer se ambíguo",
    "confidence": 0.0-1.0
}
```

---

## 11. Prompt de Error Recovery

```
Ocorreu um erro durante a operação. Analise e sugira recuperação:

ERRO: {error}
OPERAÇÃO: {operation}
CONTEXTO: {context}

DETERMINE:
1. O erro é recuperável?
2. Há dados parciais que podem ser salvos?
3. Qual a melhor forma de informar o usuário?
4. Que ação alternativa pode ser oferecida?

RESPONDA EM JSON:
{
    "recoverable": true/false,
    "partial_data_available": true/false,
    "user_message": "mensagem amigável para o usuário",
    "suggested_action": "ação alternativa se aplicável",
    "retry_possible": true/false
}
```

---

## 12. Out-of-Scope Responses — Catálogo

| Categoria | Resposta | Acrescenta "O que posso fazer"? |
|-----------|----------|-------------------------------|
| `general` | "Essa solicitação está fora do meu escopo. Posso ajudar com recrutamento, seleção..." | ✅ Sim |
| `medical` | "Não posso fornecer informações médicas. Consulte um profissional." | ✅ Sim |
| `legal` | "Não posso dar conselhos legais. Consulte um advogado." | ✅ Sim |
| `financial` | "Não posso dar conselhos financeiros. Consulte um profissional certificado." | ✅ Sim |
| `personal` | "Prefiro manter o foco em questões profissionais de recrutamento." | ❌ Não |
| `inappropriate` | "Não posso ajudar com essa solicitação. Vamos focar em recrutamento?" | ❌ Não |
| `technical_limit` | "Essa funcionalidade ainda não está disponível, mas estou sempre aprendendo!" | ✅ Sim |
| `external_system` | "Não tenho acesso a esse sistema externo. Posso ajudar com Gupy, Pandapé e Merge.dev." | ✅ Sim |

---

## 13. Diretrizes Éticas Obrigatórias em Prompts

### 13.1 Critérios Permitidos (whitelist)

- Competências técnicas (hard skills) declaradas e comprovadas
- Competências comportamentais (soft skills) observadas
- Experiência relevante para a posição
- Respostas às perguntas de triagem/entrevista
- Adequação aos requisitos da vaga
- Fit cultural observável em comportamentos

### 13.2 Critérios Proibidos (blacklist)

- Nome do candidato (pode indicar gênero/etnia)
- Idade ou ano de formatura
- Foto ou aparência física
- Instituição de ensino específica (apenas nível educacional)
- Gaps no currículo (não penalizar)
- Estado civil ou filhos
- Endereço ou bairro
- Origem étnica ou nacionalidade

### 13.3 FAIRNESS_AND_COMPLIANCE — Critérios com Base Legal

| Critério Proibido | Base Legal | Mensagem de Recusa |
|-------------------|-----------|-------------------|
| Faixa etária | Lei 10.741/2003 (Estatuto do Idoso) | "Não posso incluir faixa etária como requisito..." |
| Gênero específico | CF Art. 7°, XXX | "Critérios de gênero são discriminatórios..." |
| Aparência física | Jurisprudência TST | "Aparência não é critério profissional válido..." |
| Estado civil/família | LGPD Art. 11 | "Dados sobre estado civil não podem ser requisitos..." |
| Etnia/origem | Lei 7.716/1989 | "Critérios étnicos violam Lei 7.716/1989..." |
| Universidade específica | Jurisprudência trabalhista | "Viés socioeconômico..." |
| Origem geográfica (remoto) | CF Art. 3°, IV | Princípio da igualdade |

**Exceção permitida**: Vagas afirmativas (PCD, negros, mulheres em STEM, 50+).

---

## 14. Mapeamento de Domínios para Prompts

### 14.1 Prompt Loading Map

| Domínio | YAML Config | System Prompt Python | Blocos Importados |
|---------|-------------|---------------------|-------------------|
| `job_management` (Wizard) | `domains/job_management.yaml` | `wizard_system_prompt.py` (242 lines) | — (inline) |
| `sourcing` | `domains/sourcing.yaml` | `sourcing_system_prompt.py` (239 lines) | `ANTI_SYCOPHANCY_OPERATIONAL`, `NEGATION_DETECTION_BLOCK` |
| `cv_screening` | `domains/cv_screening.yaml` | `pipeline_system_prompt.py` | — |
| `recruiter_assistant` (Kanban) | `domains/recruiter_assistant.yaml` | `kanban_system_prompt.py` (282 lines) | `ANTI_SYCOPHANCY_BLOCK`, `CHAIN_OF_THOUGHT_BLOCK`, `NEGATION_DETECTION_BLOCK` |
| `recruiter_assistant` (Talent) | `domains/recruiter_assistant.yaml` | `talent_system_prompt.py` | `ANTI_SYCOPHANCY_OPERATIONAL`, `NEGATION_DETECTION_BLOCK` |
| `recruiter_assistant` (Jobs Mgmt) | `domains/recruiter_assistant.yaml` | `jobs_mgmt_system_prompt.py` | — |
| `pipeline` | `domains/pipeline_transition.yaml` | `pipeline_system_prompt.py` | — |
| `hiring_policy` | — | `policy_system_prompt.py` | — |
| `interview_scheduling` | `domains/interview_scheduling.yaml` | `interview_system_prompt.py` | — |
| `communication` | `domains/communication.yaml` | `communication_system_prompt.py` | — |
| `automation` | `domains/automation.yaml` | `automation_system_prompt.py` | — |
| `ats_integration` | `domains/ats_integration.yaml` | `ats_integration_system_prompt.py` | — |
| `analytics` | `domains/analytics.yaml` | `analytics_system_prompt.py` | — |

### 14.2 Shared Prompts Loading Map

| Python Variable | YAML Source | Key |
|----------------|-------------|-----|
| `LIA_PERSONA` | `shared/lia_persona.yaml` | `prompts.lia_persona` |
| `HR_VOCABULARY` | `shared/lia_persona.yaml` | `prompts.hr_vocabulary` |
| `DATA_PERSISTENCE_GUIDELINES` | `shared/lia_persona.yaml` | `prompts.data_persistence_guidelines` |
| `ETHICAL_GUIDELINES` | `shared/lia_persona.yaml` | `prompts.ethical_guidelines` |
| `ORCHESTRATOR_PROMPT` | `shared/agent_prompts.yaml` | `prompts.orchestrator` |
| `JOB_PLANNER_PROMPT` | `shared/agent_prompts.yaml` | `prompts.job_planner` |
| `SOURCING_PROMPT` | `shared/agent_prompts.yaml` | `prompts.sourcing` |
| `CV_SCREENING_PROMPT` | `shared/agent_prompts.yaml` | `prompts.cv_screening` |
| `INTERVIEWER_PROMPT` | `shared/agent_prompts.yaml` | `prompts.interviewer` |
| `WSI_EVALUATOR_PROMPT` | `shared/agent_prompts.yaml` | `prompts.wsi_evaluator` |
| `SCHEDULING_PROMPT` | `shared/agent_prompts.yaml` | `prompts.scheduling` |
| `ANALYST_FEEDBACK_PROMPT` | `shared/agent_prompts.yaml` | `prompts.analyst_feedback` |
| `ATS_INTEGRATOR_PROMPT` | `shared/agent_prompts.yaml` | `prompts.ats_integrator` |
| `RECRUITER_ASSISTANT_PROMPT` | `shared/agent_prompts.yaml` | `prompts.recruiter_assistant` |
| `PROACTIVE_INSIGHTS_PROMPT` | `shared/agent_prompts.yaml` | `prompts.proactive_insights` |
| `CLARIFICATION_TRIGGERS` | `shared/defensive.yaml` | `prompts.clarification_triggers` |
| `OUT_OF_SCOPE_RESPONSES` | `shared/defensive.yaml` | `prompts.out_of_scope_responses` |
| `AMBIGUITY_DETECTION_PROMPT` | `shared/defensive.yaml` | `prompts.ambiguity_detection_prompt` |
| `ERROR_RECOVERY_PROMPT` | `shared/defensive.yaml` | `prompts.error_recovery_prompt` |

---

## 15. Fontes de Verdade por Componente

| Comportamento | Fonte Canônica | Status |
|---------------|---------------|--------|
| Prompt YAML loading + cache | `app/shared/prompts/loader.py` → `PromptLoader` | Implementado |
| Domain system prompts (inline Python) | `app/domains/*/agents/*_system_prompt.py` | Implementado |
| Anti-sycophancy blocks | `app/shared/prompts/anti_sycophancy_block.py` | Implementado (3 variantes) |
| Interaction patterns (negation/confirmation) | `app/shared/prompts/interaction_patterns.py` | Implementado |
| Defensive prompts (clarification/error) | `app/shared/robustness/defensive_prompts.py` + `shared/defensive.yaml` | Implementado |
| Few-shot examples (sourcing only) | `app/domains/sourcing/prompts.py` | Implementado (1 domínio) |
| Cascaded router prompts | `app/orchestrator/cascaded_router.py` | Implementado |
| LLM cascade (confidence thresholds) | `app/services/llm.py` → `generate_with_cascade()` | Implementado |
| Ethical guidelines / FAIRNESS_AND_COMPLIANCE | `shared/lia_persona.yaml` + inline nos system prompts | Duplicação: YAML e inline coexistem |
| ReAct reasoning JSON format | `react_loop.py` → `_parse_reasoning()` | Implementado |

---

## 16. Anti-Patterns Identificados

### 16.1 Duplicação de Prompts

O `wizard_system_prompt.py` define inline as mesmas regras de `=== COMPLIANCE E ÉTICA ===` e `=== FAIRNESS_AND_COMPLIANCE ===` que existem em `ethical_guidelines` no YAML compartilhado. Isso cria risco de drift entre as duas fontes.

### 16.2 Prompts Mockados no Frontend (Archived)

3 tabs do Talent Funnel (Pipelines, Personas, Mapping) foram arquivadas em `plataforma-lia/src/components/talent-funnel-tabs/_archived/`. Cada uma implementava `handleLIAInsights()` com respostas hardcoded locais — sem LLM ou backend real. O componente ativo `candidates-page.tsx` usa `handleLIAChatMessage()` e `handleLIAClick()` para interação com o backend LIA; `tasks-page.tsx` usa `handleLIAAction()` para ações contextuais por vaga.

### 16.3 Inconsistência de Idioma em Fallbacks

O error handler genérico do ReAct loop retorna fallback em inglês:
```
"I encountered an error while processing your request. Please try again."
```
Enquanto o circuit breaker handler retorna em português:
```
"O serviço de IA está temporariamente indisponível..."
```

### 16.4 Temperatura Hardcoded vs Configurável

O `ReActConfig` define `temperature: float = 0.3` como default fixo, enquanto o `LLMService` usa `settings.LLM_DEFAULT_TEMPERATURE`. Não há garantia de que o valor seja o mesmo.

### 16.5 Few-Shot Examples Apenas em Sourcing

Apenas o domínio `sourcing/prompts.py` possui few-shot examples estruturados (5 exemplos). Outros domínios com prompts complexos (kanban, talent, jobs_mgmt) em `app/domains/recruiter_assistant/prompts/` existem mas com escopo diferente (prompts de assistentes, não few-shot).

---

## 17. Regras de Escrita de Prompts

**Nota**: As regras abaixo são o padrão-alvo (target standard). Atualmente, os agentes Wizard, Kanban, Sourcing e Talent seguem a maioria delas. Domínios mais simples (automation, analytics, communication) podem não implementar todos os blocos obrigatórios.

### 17.1 Obrigatórias

1. Todo prompt DEVE ser em Português Brasileiro (PT-BR)
2. Todo prompt DEVE incluir bloco `=== IDENTIDADE ===` com nome LIA
3. Todo prompt DEVE incluir bloco `=== INSTRUÇÕES REACT ===` com ciclo R-A-O
4. Todo prompt DEVE incluir ou importar bloco anti-sycophancy
5. Todo prompt DEVE definir `scope_in` e `scope_out` (no YAML ou inline)
6. Todo prompt DEVE incluir regras de tratamento de erro amigável
7. Todo prompt DEVE proibir exposição de JSON, IDs internos ou stack traces

### 17.2 Recomendadas

1. Usar seções com delimitadores `=== SEÇÃO ===` para prompts longos
2. Incluir exemplos de interação inline no system prompt
3. Definir `behavioral_rules` explícitas no YAML
4. Usar o `CHAIN_OF_THOUGHT_BLOCK` para agentes que precisam de raciocínio estruturado
5. Incluir `NEGATION_DETECTION_BLOCK` em agentes que executam ações destrutivas

### 17.3 Proibidas

1. Prompts em inglês em agentes voltados ao recrutador
2. Uso de termos técnicos de IA sem explicação ao recrutador
3. Decisões autônomas sem confirmação do recrutador para ações irreversíveis
4. Concordância automática com o recrutador (sycophancy)
5. Criação de critérios discriminatórios mesmo se solicitados pelo recrutador

---

## 18. Vocabulário Técnico de RH — Referência

O YAML `lia_persona.yaml` define tabelas de vocabulário por categoria:

| Categoria | Exemplos de Termos |
|-----------|-------------------|
| Processo Seletivo | Funil de contratação, Pipeline, Etapa, Taxa de conversão, Shortlist, Longlist |
| Avaliação | Fit cultural, Soft skills, Hard skills, Competência, Parecer, Score |
| Senioridade | Estágio, Trainee, Júnior, Pleno, Sênior, Especialista, Coordenador, Gerente, Diretor |
| Contratação | CLT, PJ, Temporário, Terceirizado, Freelancer |
| Remuneração | Pretensão salarial, Faixa salarial, PLR, Bônus, Benefícios flexíveis |
| Modalidades | Presencial, Remoto, Híbrido, Home office, Anywhere office |
| Profissionais RH | Recrutador, Headhunter, Business Partner, Tech Recruiter, Hiring Manager |
| Etapas | Triagem, Screening, Entrevista técnica, Entrevista comportamental, Case, Proposta |
