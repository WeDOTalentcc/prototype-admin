# Diagnóstico Completo: Prompts e Chats da Plataforma LIA

**Data:** Janeiro 2026  
**Escopo:** Análise de todos os componentes de IA conversacional da plataforma

---

## 📋 Índice

1. [Resumo Executivo](#resumo-executivo)
2. [Tabela Resumo de Todos os Prompts](#tabela-resumo)
3. [Análise Detalhada por Prompt](#análise-detalhada)
   - [1. Jobs Page (Gestão de Vagas)](#1-jobs-page)
   - [2. Job Kanban Page (Dentro de uma Vaga)](#2-job-kanban-page)
   - [3. Candidates Page (Funil de Talentos)](#3-candidates-page)
   - [4. Talent Funnel Tabs](#4-talent-funnel-tabs)
   - [5. Job Creation Wizard](#5-job-creation-wizard)
4. [Arquitetura dos Endpoints](#arquitetura-endpoints)
5. [Mapa de Capacidades](#mapa-capacidades)
6. [Análise de Gaps e Limitações](#gaps-limitacoes)
7. [Plano de Ação Prioritizado](#plano-acao)

---

## 📊 Resumo Executivo {#resumo-executivo}

A plataforma LIA possui **5 interfaces de chat/prompt principais**, cada uma com diferentes níveis de maturidade:

| Nível | Descrição | Qtd |
|-------|-----------|-----|
| 🟢 **Orquestrado** | Conectado ao multi-agent orchestrator com routing inteligente | 3 |
| 🟡 **Parcial** | Conectado a API específica mas sem orquestrador completo | 1 |
| 🔴 **Mock** | Comandos simulados sem backend real | 3 |

### Descobertas Principais

1. **3 prompts usam orquestrador real** (Jobs, Job Kanban, Candidates)
2. **3 tabs do Talent Funnel usam MOCK** (Pipelines, Personas, Mapping)
3. **1 wizard usa API específica** (Job Creation Wizard)
4. **Capacidade de UI Actions** implementada mas subutilizada

---

## 📋 Tabela Resumo de Todos os Prompts {#tabela-resumo}

| # | Página/Componente | Componente UI | Endpoint Backend | Status | Agentes Disponíveis |
|---|-------------------|---------------|------------------|--------|---------------------|
| 1 | **Jobs Page** (Gestão de Vagas) | `ExpandedChatModal` | `/orchestrator/jobs-management` | 🟢 Orquestrado | RecruiterAssistant, JobPlanner |
| 2 | **Job Kanban Page** (Dentro de uma vaga) | `ExpandedChatModal` | `/orchestrator/job-chat` | 🟢 Orquestrado | AvaliadorWSI, AnalistaFeedback, Sourcing, TriagemCurricular, RecruiterAssistant |
| 3 | **Candidates Page** (Funil de Talentos) | `ExpandableAIPrompt` | `/orchestrator/talent-chat` | 🟢 Orquestrado | AvaliadorWSI, Sourcing, TalentAssistant |
| 4a | **Pipelines Tab** | `ExpandableAIPrompt` | ❌ Mock local | 🔴 Mock | Nenhum (simulado) |
| 4b | **Personas Tab** | `ExpandableAIPrompt` | ❌ Mock local | 🔴 Mock | Nenhum (simulado) |
| 4c | **Mapping Tab** | `ExpandableAIPrompt` | ❌ Mock local | 🔴 Mock | Nenhum (simulado) |
| 5 | **Job Creation Wizard** | `ExpandedChatModal` (modo wizard) | `/lia/job-wizard` | 🟡 Parcial | LIA Wizard + Skills Catalog |

---

## 🔍 Análise Detalhada por Prompt {#análise-detalhada}

### 1. Jobs Page (Gestão de Vagas) {#1-jobs-page}

#### 📍 Localização
- **Arquivo:** `plataforma-lia/src/components/pages/jobs-page.tsx`
- **Componente UI:** `ExpandedChatModal`
- **Contexto:** Visão geral de todas as vagas da empresa

#### 🔌 Endpoint Usado
```typescript
// plataforma-lia/src/lib/api/kanban-assistant.ts
callOrchestratedJobsManagement(request: OrchestratedJobsManagementRequest)
// POST /api/backend-proxy/orchestrator/jobs-management
```

#### ✅ Capacidades Atuais
- Análise de portfólio de vagas
- Comparação entre vagas
- Identificação de vagas críticas/urgentes
- Disparo de UI Action `start_job_wizard` para criar nova vaga
- Sugestão de filtros
- Resumo de métricas consolidadas

#### ❌ Limitações
- Não acessa dados granulares de candidatos
- Não pode executar ações em massa
- UI Actions limitadas a 3 tipos: `start_job_wizard`, `filter_jobs`, `compare_jobs`

#### 🏗️ Arquitetura
```
Frontend (ExpandedChatModal)
    ↓ callOrchestratedJobsManagement()
    ↓ jobs_context: {total, active, paused, urgent...}
Backend (/orchestrator/jobs-management)
    ↓ Orchestrator.process_request()
    ↓ Routing por intent
Agents: RecruiterAssistant, JobPlanner
    ↓
Response + ui_action + suggested_prompts
```

#### 🔧 Contexto Enviado ao Backend
```typescript
{
  message: string,
  jobs_context: {
    total: number,
    active: number,
    paused: number,
    completed: number,
    urgent: number,
    withoutCandidates: number,
    totalCandidates: number,
    currentFilter?: string
  },
  selected_jobs?: Array<{id, title, department, status}>,
  top_jobs?: Array<{...métricas detalhadas}>,
  conversation_history?: Array<{role, content}>
}
```

---

### 2. Job Kanban Page (Dentro de uma Vaga) {#2-job-kanban-page}

#### 📍 Localização
- **Arquivo:** `plataforma-lia/src/components/pages/job-kanban-page.tsx`
- **Componente UI:** `ExpandedChatModal`
- **Contexto:** Gestão de candidatos de uma vaga específica

#### 🔌 Endpoint Usado
```typescript
// plataforma-lia/src/lib/api/kanban-assistant.ts
callOrchestratedJobChat(request: OrchestratedJobChatRequest)
// POST /api/backend-proxy/orchestrator/job-chat
```

#### ✅ Capacidades Atuais
- **Ranking de candidatos** por WSI Score, Fit Score
- **Análise de funil** com gargalos identificados
- **Comparação de candidatos** selecionados
- **Análise Big Five** de personalidade
- **Identificação de candidatos parados** (stalled > 7 dias)
- **Sugestões de próximos passos** contextuais
- **UI Actions:** 
  - `start_job_wizard` - Criar nova vaga
  - `start_candidate_wizard` - Adicionar candidato
- **Ações em Bulk:**
  - `move_stage` - Mover candidatos de etapa
  - `send_feedback` - Enviar feedback

#### ❌ Limitações
- Não executa ações diretamente (apenas sugere)
- Não pode editar dados de candidatos
- Não agenda entrevistas automaticamente
- Análise WSI depende de dados pré-processados

#### 🏗️ Arquitetura
```
Frontend (ExpandedChatModal)
    ↓ callOrchestratedJobChat()
    ↓ job_context + candidates[] + selected_candidate_ids
Backend (/orchestrator/job-chat)
    ↓ job_context_service.enrich_from_frontend_data()
    ↓ build_enriched_context_summary()
    ↓ Orchestrator.process_request()
Agents:
  - AvaliadorWSI (ranking, comparação)
  - AnalistaFeedback (gargalos, métricas)
  - Sourcing (busca similar)
  - TriagemCurricular (análise CV)
  - RecruiterAssistant (geral)
    ↓
Response + actions[] + suggested_prompts
```

#### 🔧 Contexto Enviado ao Backend
```typescript
{
  message: string,
  job_context: {
    id?: string,
    title: string,
    department?: string,
    level?: string,
    requirements?: string[],
    skills?: string[],
    location?: string,
    salary?: string,
    workModel?: string,
    deadline?: string
  },
  candidates: Array<{
    id: string,
    name: string,
    role?: string,
    currentCompany?: string,
    score?: number,
    wsiScore?: number,
    wsiTechnical?: number,
    wsiBehavioral?: number,
    fitScore?: number,
    skills?: string[],
    stage?: string,
    subStatus?: string,
    daysInStage?: number,
    bigFive?: Record<string, number>,
    hasCV?: boolean
  }>,
  selected_candidate_ids?: string[],
  conversation_id?: string
}
```

#### 📊 Métricas Calculadas pelo Backend
- `funnel_metrics.total_candidates`
- `funnel_metrics.health_status` (healthy/warning/critical)
- `funnel_metrics.bottleneck_stage`
- `funnel_metrics.stalled_candidates[]`
- `funnel_metrics.candidates_needing_feedback[]`
- `funnel_metrics.by_stage` (contagem por etapa)

---

### 3. Candidates Page (Funil de Talentos) {#3-candidates-page}

#### 📍 Localização
- **Arquivo:** `plataforma-lia/src/components/pages/candidates-page.tsx`
- **Componente UI:** `ExpandableAIPrompt`
- **Contexto:** Busca e gestão de talentos (sourcing)

#### 🔌 Endpoint Usado
```typescript
// plataforma-lia/src/lib/api/kanban-assistant.ts
callOrchestratedTalentChat(request: OrchestratedTalentChatRequest)
// POST /api/backend-proxy/orchestrator/talent-chat
```

#### ✅ Capacidades Atuais
- **Busca inteligente** com NLP (natural language)
- **Comparação de candidatos** selecionados
- **Análise de perfil** individual
- **Busca por perfil similar** (LinkedIn/CV)
- **Ranking por fit** com vaga de referência
- **UI Actions:**
  - `start_job_wizard` - Criar vaga
  - `switch_search_mode` - Mudar modo de busca
  - `open_communication_modal` - Contatar
  - `open_schedule_modal` - Agendar
  - `open_screening_modal` - Triagem WSI
  - `trigger_export` - Exportar
  - `open_add_to_list_modal` - Adicionar à lista

#### ❌ Limitações
- Busca global (Pearch) requer créditos
- Análise de skills limitada ao catálogo
- Não cria candidatos automaticamente
- Não envia comunicações diretamente

#### 🏗️ Arquitetura
```
Frontend (ExpandableAIPrompt)
    ↓ callOrchestratedTalentChat()
    ↓ candidates[] + search_context + target_job
Backend (/orchestrator/talent-chat)
    ↓ detect_talent_intent()
    ↓ build_talent_context_summary()
    ↓ Orchestrator.route_message()
Agents:
  - Sourcing (busca)
  - AvaliadorWSI (análise, ranking)
  - TalentAssistant (geral)
    ↓
Response + ui_action + suggested_prompts
```

#### 🔧 Contexto Enviado ao Backend
```typescript
{
  message: string,
  candidates: Array<{
    id: string,
    name: string,
    current_title?: string,
    current_company?: string,
    location?: string,
    skills?: string[],
    experience_years?: number,
    lia_score?: number,
    wsi_score?: number,
    source?: string
  }>,
  selected_candidate_ids?: string[],
  search_context?: {
    query?: string,
    mode?: string,
    total_results?: number,
    local_results?: number,
    global_results?: number,
    active_filters?: Record<string, unknown>
  },
  target_job?: {
    id?: string,
    title?: string,
    department?: string,
    level?: string,
    skills?: string[]
  },
  conversation_id?: string
}
```

---

### 4. Talent Funnel Tabs {#4-talent-funnel-tabs}

#### 📍 Localização
- **Arquivos:**
  - `plataforma-lia/src/components/talent-funnel-tabs/pipelines-tab.tsx`
  - `plataforma-lia/src/components/talent-funnel-tabs/personas-tab.tsx`
  - `plataforma-lia/src/components/talent-funnel-tabs/mapping-tab.tsx`
- **Componente UI:** `ExpandableAIPrompt`
- **Contexto:** Gestão de pipelines, personas e mapeamento de empresas

#### ⚠️ ALERTA: PROMPTS EM MOCK

Estes 3 tabs **NÃO USAM ORQUESTRADOR**. Eles têm handlers locais que simulam respostas de IA.

#### 🔌 Endpoint Usado
```typescript
// NÃO HÁ ENDPOINT REAL
// Usa função local onCommand que gera respostas mockadas
```

#### Implementação Mock (exemplo de pipelines-tab.tsx):
```typescript
const handleLIACommand = (command: string) => {
  const cmd = command.toLowerCase().trim()
  
  if (cmd.includes('analise') || cmd.includes('análise')) {
    addLiaMessage(`📊 **Análise de Pipelines**
    
    Baseado nos ${pipelines.length} pipelines ativos:
    - Taxa média de sucesso: 90.3%
    - Tempo médio para contratação: 12.7 dias
    - Pipeline mais eficiente: "UX Designers Sênior" (92%)
    - Atenção: "Liderança Tech" está em rascunho
    
    **Recomendação:** Ativar o pipeline de Liderança Tech...`)
  }
  // ... outras condições mockadas
}
```

#### ✅ Capacidades Atuais (Mock)
- **Pipelines:** Análise superficial, otimização, criação, comparação
- **Personas:** Análise, criação a partir de vagas, sugestões
- **Mapping:** Análise de empresas, inteligência competitiva

#### ❌ Limitações CRÍTICAS
- 🔴 **Sem backend real** - Todas as respostas são pré-programadas
- 🔴 **Não acessa dados reais** - Usa dados mockados
- 🔴 **Não persiste ações** - Comandos não têm efeito
- 🔴 **Sem aprendizado** - Não usa LLM real
- 🔴 **Respostas limitadas** - Só funciona para keywords específicas

#### 🏗️ Arquitetura Atual (Quebrada)
```
Frontend (ExpandableAIPrompt)
    ↓ onCommand(command)
    ↓ handleLIACommand(command)
    ↓ if/else com keywords
Mock Response (texto estático)
    ↓
setLiaMessages([...messages, mockResponse])
```

---

### 5. Job Creation Wizard {#5-job-creation-wizard}

#### 📍 Localização
- **Arquivo:** `plataforma-lia/src/components/expanded-chat-modal.tsx`
- **Modo:** Wizard (isWizardMode=true)
- **Contexto:** Criação conversacional de vagas

#### 🔌 Endpoint Usado
```typescript
// plataforma-lia/src/services/lia-api.ts
orchestrateWizardMessage(request)
// POST /api/backend-proxy/lia/job-wizard
```

#### ✅ Capacidades Atuais
- **Extração de campos** a partir de descrição livre
- **Sugestões de salário** baseadas em mercado
- **Catálogo de skills** técnicas e comportamentais
- **Geração de perguntas WSI** para triagem
- **Análise de remuneração** vs benchmark
- **Validação de completude** por estágio

#### Estágios do Wizard:
1. `input-evaluation` - Avaliação inicial
2. `salary` - Remuneração
3. `competencies` - Competências
4. `wsi-questions` - Perguntas de triagem
5. `review-publish` - Revisão e publicação
6. `search-calibration` - Busca e calibração

#### ❌ Limitações
- Wizard sequencial (não pula etapas inteligentemente)
- Publicação ainda requer confirmação manual
- Calibração de candidatos não usa sourcing automático

#### 🏗️ Arquitetura
```
Frontend (ExpandedChatModal - Wizard Mode)
    ↓ orchestrateWizardMessage()
    ↓ stage + user_input + context
Backend (/lia/job-wizard)
    ↓ EnhancedIntentClassifier
    ↓ SkillsCatalogService
    ↓ MarketBenchmarkService
    ↓ LLM (structured outputs)
    ↓
WizardStepResponse {
  detected_criteria,
  benchmarks,
  suggestions,
  field_origins,
  lia_message
}
```

---

## 🏗️ Arquitetura dos Endpoints {#arquitetura-endpoints}

### Endpoints Orquestrados (Multi-Agent)

| Endpoint | Arquivo Backend | Usa Orchestrator | Agentes |
|----------|-----------------|------------------|---------|
| `/orchestrator/jobs-management` | `orchestrated_job_chat.py` (reused) | ✅ Sim | RecruiterAssistant, JobPlanner |
| `/orchestrator/job-chat` | `orchestrated_job_chat.py` | ✅ Sim | AvaliadorWSI, AnalistaFeedback, Sourcing, TriagemCurricular |
| `/orchestrator/talent-chat` | `orchestrated_talent_chat.py` | ✅ Sim | AvaliadorWSI, Sourcing, TalentAssistant |

### Endpoints Específicos (Sem Multi-Agent)

| Endpoint | Arquivo Backend | Usa LLM | Função |
|----------|-----------------|---------|--------|
| `/lia/job-wizard` | `lia_assistant.py` | ✅ Sim | Wizard de criação de vagas |
| `/lia/suggestions` | `lia_assistant.py` | ❌ Não | Cards dinâmicos homepage |
| `/lia/job-insights` | `lia_assistant.py` | ✅ Sim | Insights de vagas |

### Fluxo do Orchestrator

```
                    ┌─────────────────┐
                    │   Orchestrator   │
                    │ (Router Central) │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼────┐         ┌─────▼────┐         ┌────▼────┐
   │ Intent  │         │ Context  │         │  Agent  │
   │Classifier│         │ Enricher │         │ Selector │
   └────┬────┘         └─────┬────┘         └────┬────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
     ┌───────────────────────┼───────────────────────┐
     │                       │                       │
┌────▼─────┐          ┌──────▼──────┐         ┌─────▼─────┐
│ Avaliador │          │  Analista   │         │  Sourcing │
│   WSI    │          │  Feedback   │         │   Agent   │
└──────────┘          └─────────────┘         └───────────┘
```

---

## 🗺️ Mapa de Capacidades {#mapa-capacidades}

### Matriz Funcionalidade x Prompt

| Funcionalidade | Jobs Page | Job Kanban | Candidates | Pipelines | Personas | Mapping | Wizard |
|----------------|-----------|------------|------------|-----------|----------|---------|--------|
| Análise de métricas | ✅ | ✅ | ✅ | 🔴 Mock | 🔴 Mock | 🔴 Mock | ❌ |
| Ranking de candidatos | ❌ | ✅ | ✅ | ❌ | 🔴 Mock | ❌ | ❌ |
| Comparação | ✅ (vagas) | ✅ (candidatos) | ✅ | 🔴 Mock | ❌ | ❌ | ❌ |
| Criar vaga | ✅ (UI Action) | ✅ (UI Action) | ✅ (UI Action) | ❌ | ❌ | ❌ | ✅ |
| Editar dados | ❌ | ❌ | ❌ | 🔴 Mock | 🔴 Mock | ❌ | ✅ |
| Enviar comunicação | ❌ | ❌ | ✅ (UI Action) | ❌ | ❌ | ❌ | ❌ |
| Agendar entrevista | ❌ | ❌ | ✅ (UI Action) | ❌ | ❌ | ❌ | ❌ |
| Busca inteligente | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Análise de perfil | ❌ | ✅ | ✅ | ❌ | 🔴 Mock | ❌ | ❌ |
| Gerar perguntas WSI | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Sugestão de salário | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

**Legenda:**
- ✅ Funciona com backend real
- ✅ (UI Action) Dispara ação no frontend
- 🔴 Mock - Resposta simulada
- ❌ Não disponível

---

## 🚨 Análise de Gaps e Limitações {#gaps-limitacoes}

### Gap 1: Talent Funnel Tabs Sem Backend

**Impacto:** 🔴 Crítico  
**Tabs afetadas:** Pipelines, Personas, Mapping

**Problema:**
```typescript
// pipelines-tab.tsx
const handleLIACommand = (command: string) => {
  // Tudo é mock - não há chamada de API
  if (cmd.includes('analise')) {
    addLiaMessage(`📊 **Análise de Pipelines**...`) // Texto estático
  }
}
```

**Consequências:**
- Usuário não tem acesso a análise real de pipelines
- Não pode criar personas com IA real
- Mapeamento de empresas é apenas visualização

### Gap 2: Ações Não Executáveis

**Impacto:** 🟡 Médio  
**Prompts afetados:** Todos os orquestrados

**Problema:**
Os prompts podem sugerir ações mas não executam diretamente. Dependem de UI Actions que abrem modais.

**Exemplo:**
```typescript
// Backend sugere ação
actions: [{
  type: "bulk_action",
  action: "send_feedback",
  label: "Enviar feedback para 5 candidatos",
  candidate_ids: ["id1", "id2", ...]
}]

// Frontend precisa implementar handler
// Atualmente apenas mostra como sugestão
```

### Gap 3: Contexto Limitado Entre Sessões

**Impacto:** 🟡 Médio  
**Prompts afetados:** Todos

**Problema:**
`conversation_id` existe mas histórico de conversa é limitado. Não há memória de longo prazo.

### Gap 4: Sem Tools/Function Calling Real

**Impacto:** 🟡 Médio  
**Prompts afetados:** Todos os orquestrados

**Problema:**
Os agentes respondem texto mas não executam tools reais (ex: criar candidato, enviar email, atualizar status).

---

## 📋 Plano de Ação Prioritizado {#plano-acao}

### Fase 1: Correção Crítica (Sprint 1-2)

#### 1.1 Conectar Talent Funnel Tabs ao Orquestrador

**Prioridade:** 🔴 P0 - Crítico

**Arquivos a modificar:**
- `pipelines-tab.tsx`
- `personas-tab.tsx`
- `mapping-tab.tsx`

**Implementação:**
```typescript
// Substituir handleLIACommand por:
const handleLIACommand = async (command: string) => {
  const response = await callOrchestratedTalentChat({
    message: command,
    candidates: [], // Candidatos do pipeline/persona
    search_context: {
      mode: 'pipeline_management', // Novo modo
      pipeline_id: selectedPipeline
    }
  })
  
  addLiaMessage(response.content)
  handleUIAction(response.ui_action, response.ui_action_params)
}
```

**Backend necessário:**
- Criar intent handlers para pipeline/persona/mapping
- Adicionar agentes especializados ou expandir Sourcing

**Estimativa:** 5-8 dias

---

#### 1.2 Criar Endpoint `/orchestrator/pipeline-chat`

**Prioridade:** 🔴 P0 - Crítico

**Arquivo:** `lia-agent-system/app/api/v1/orchestrated_pipeline_chat.py`

**Intents a suportar:**
```python
PIPELINE_INTENTS = {
    "analyze_pipeline": "Análise de performance do pipeline",
    "optimize_pipeline": "Sugestões de otimização",
    "compare_pipelines": "Comparar pipelines",
    "create_pipeline": "Criar novo pipeline",
    "duplicate_pipeline": "Clonar pipeline existente",
}

PERSONA_INTENTS = {
    "analyze_persona": "Análise de persona",
    "create_persona": "Criar persona de vaga",
    "expand_candidate_base": "Expandir base de candidatos",
}

MAPPING_INTENTS = {
    "analyze_company": "Análise de empresa",
    "identify_talents": "Identificar talentos na empresa",
    "monitor_company": "Monitorar movimentações",
}
```

**Estimativa:** 3-5 dias

---

### Fase 2: Melhorias de Capacidade (Sprint 3-4)

#### 2.1 Implementar Tool Calling Real

**Prioridade:** 🟡 P1 - Alto

**Objetivo:** Permitir que agentes executem ações reais, não apenas sugiram.

**Tools a implementar:**
```python
class AvailableTools(Enum):
    CREATE_CANDIDATE = "create_candidate"
    UPDATE_CANDIDATE_STAGE = "update_candidate_stage"
    SEND_EMAIL = "send_email"
    SCHEDULE_INTERVIEW = "schedule_interview"
    CREATE_JOB = "create_job"
    ADD_TO_LIST = "add_to_list"
    EXPORT_CANDIDATES = "export_candidates"
```

**Arquitetura proposta:**
```
User Message
    ↓
Orchestrator
    ↓
Agent + LLM (com tool definitions)
    ↓
Tool Call Decision
    ↓
Tool Executor
    ↓
Result + Response
```

**Estimativa:** 10-15 dias

---

#### 2.2 Adicionar Memória de Conversa

**Prioridade:** 🟡 P1 - Alto

**Implementação:**
- Usar `conversation_id` para recuperar histórico
- Armazenar em banco ou Redis
- Limitar a últimas N mensagens

**Estimativa:** 3-5 dias

---

### Fase 3: Capacidades Avançadas (Sprint 5+)

#### 3.1 Agente Autônomo para Pipelines

**Prioridade:** 🟢 P2 - Médio

**Funcionalidades:**
- Monitoramento proativo de gargalos
- Sugestões automáticas de otimização
- Alertas de candidatos parados

---

#### 3.2 Integração com Sourcing Externo

**Prioridade:** 🟢 P2 - Médio

**Funcionalidades:**
- Busca automática quando pipeline esvazia
- Enriquecimento de perfis
- Scoring preditivo

---

#### 3.3 Análise de Mercado para Mapping

**Prioridade:** 🟢 P3 - Baixo

**Funcionalidades:**
- Crawling de LinkedIn Company Pages
- Detecção de movimentações (layoffs, expansões)
- Alertas de talentos disponíveis

---

## 📊 Resumo do Plano

| Fase | Itens | Prioridade | Estimativa | Impacto |
|------|-------|------------|------------|---------|
| **1.1** | Conectar Tabs ao Orchestrator | P0 | 5-8 dias | 🔴 Crítico |
| **1.2** | Endpoint pipeline-chat | P0 | 3-5 dias | 🔴 Crítico |
| **2.1** | Tool Calling Real | P1 | 10-15 dias | 🟡 Alto |
| **2.2** | Memória de Conversa | P1 | 3-5 dias | 🟡 Alto |
| **3.1** | Agente Autônomo Pipelines | P2 | 8-10 dias | 🟢 Médio |
| **3.2** | Sourcing Externo | P2 | 10-15 dias | 🟢 Médio |
| **3.3** | Análise de Mercado | P3 | 15-20 dias | 🟢 Baixo |

**Total Fase 1:** 8-13 dias  
**Total Fase 2:** 13-20 dias  
**Total Fase 3:** 33-45 dias

---

## 🔗 Referências de Arquivos

### Frontend
- `plataforma-lia/src/components/expanded-chat-modal.tsx`
- `plataforma-lia/src/components/expandable-ai-prompt.tsx`
- `plataforma-lia/src/components/pages/jobs-page.tsx`
- `plataforma-lia/src/components/pages/job-kanban-page.tsx`
- `plataforma-lia/src/components/pages/candidates-page.tsx`
- `plataforma-lia/src/components/talent-funnel-tabs/pipelines-tab.tsx`
- `plataforma-lia/src/components/talent-funnel-tabs/personas-tab.tsx`
- `plataforma-lia/src/components/talent-funnel-tabs/mapping-tab.tsx`
- `plataforma-lia/src/lib/api/kanban-assistant.ts`

### Backend
- `lia-agent-system/app/api/v1/lia_assistant.py`
- `lia-agent-system/app/api/v1/orchestrated_job_chat.py`
- `lia-agent-system/app/api/v1/orchestrated_talent_chat.py`
- `lia-agent-system/app/orchestrator/__init__.py`
- `lia-agent-system/app/agents/specialized/`

---

*Documento gerado em Janeiro 2026 - Atualizar conforme evolução da plataforma*
