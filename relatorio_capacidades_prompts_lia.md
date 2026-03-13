# Relatório Completo de Capacidades e Prompts — LIA (WeDOTalent)
**Versão:** 1.0 — 13/03/2026
**Fonte:** Auditoria direta do código-fonte (`lia-agent-system/` + `plataforma-lia/`)
**Propósito:** Mapeamento técnico exaustivo de toda a arquitetura de prompts, interação entre chats, agentes ReAct, capacidades, templates de resposta, análises, sistema preditivo, limitações, dívidas técnicas e oportunidades de evolução.

---

## Sumário

1. [Arquitetura de Prompts e Interação entre Chats](#1-arquitetura-de-prompts-e-interação-entre-chats)
2. [Os 11 Agentes ReAct](#2-os-11-agentes-react)
3. [Capacidades Detalhadas](#3-capacidades-detalhadas)
4. [Templates de Resposta do Chat](#4-templates-de-resposta-do-chat)
5. [Análises e Relatórios](#5-análises-e-relatórios)
6. [Sistema Preditivo e Insights](#6-sistema-preditivo-e-insights)
7. [Quick Actions e Ações Bulk](#7-quick-actions-e-ações-bulk)
8. [Limitações, Dívidas Técnicas e Funcionalidades Incompletas](#8-limitações-dívidas-técnicas-e-funcionalidades-incompletas)
9. [Oportunidades e Capacidades Ausentes](#9-oportunidades-e-capacidades-ausentes)
10. [Referência de Arquivos](#10-referência-de-arquivos)

---

## 1. Arquitetura de Prompts e Interação entre Chats

### 1.1 Os 3 Níveis de Chat

A plataforma possui **3 camadas de chat** com contextos, escopos e lógica de decisão distintos:

#### 1.1.1 Float Chat (candidates-page.tsx)

- **Localização:** `plataforma-lia/src/components/pages/candidates-page.tsx`
- **Contexto:** Página de funil de talentos (listagem geral de candidatos)
- **Escopo de ferramentas:** `TALENT_FUNNEL` — `scope_config.py` filtra ferramentas para: `search_candidates`, `get_candidate_details`, `get_candidate_stats`, `compare_candidates`, `get_diversity_metrics`, `update_candidate_stage`, `reject_candidate`, `shortlist_candidate`, `wsi_screening`, `send_email`, `send_whatsapp`, `schedule_interview`, `send_feedback`
- **Endpoint API:** `callOrchestratedTalentChat()` → `POST /api/backend-proxy/orchestrator/talent-chat`
- **Estado expandido (Super Prompt):** Gerenciado via `LiaFloatContext` (`lia-float-context.tsx`):
  - `isOpen` / `isExpanded` — Float mini vs. Super Prompt expandido
  - `expand()` / `collapse()` — Transição entre modos
  - `sharedMessages` — Mensagens compartilhadas entre mini e expandido

**Lógica de decisão local vs. delegar (`handleLIAChatMessage`, linha 5659):**

```
1. Mensagem recebida → normalizar
2. Verificar se é COMANDO DE ANÁLISE (analysisCommands[]):
   - "analisar potencial", "resumo executivo", "top 5", "comparar", etc.
   → Se sim: handleAICommand(message) [processamento IA via backend]
3. Verificar se é PERGUNTA GENÉRICA (isGenericQuestion, linha 5617):
   - Regex: /^(o que|como|por que|quando|onde|quem|quanto)/, /?$/
   - EXCETO se contém searchKeywords: "desenvolvedor", "python", "react", "são paulo", etc.
   → Se é pergunta genérica SEM keywords: handleOrchestratedTalentMessage() → backend orquestrador
4. Senão: executar como BUSCA DE CANDIDATOS via executeSearch()
```

**Função `isGenericQuestion()` (linha 5617):**
- **Input:** texto do usuário
- **Processing:** Verifica regex de padrões interrogativos + ausência de keywords de busca
- **Output:** `boolean` — true se é pergunta genérica (vai para orquestrador), false se é busca
- **Keywords de busca (46 termos):** cargos (desenvolvedor, gerente, analista...), tecnologias (python, react, node...), localidades (são paulo, remoto...), senioridades (junior, pleno, senior...)

#### 1.1.2 Kanban Chat (job-kanban-page.tsx)

- **Localização:** `plataforma-lia/src/components/pages/job-kanban-page.tsx`
- **Contexto:** Kanban de uma vaga específica (pipeline de candidatos por etapa)
- **Escopo de ferramentas:** `IN_JOB` — `scope_config.py` filtra para: `update_candidate_stage`, `reject_candidate`, `shortlist_candidate`, `bulk_update_candidates_stage`, `wsi_screening`, `get_pipeline_stats`, `get_vacancy_funnel`, `compare_candidates`, `send_email`, `schedule_interview`
- **Endpoint API:** `callOrchestratedJobChat()` → `POST /api/backend-proxy/orchestrator/job-chat`

**Lógica de decisão (backend — `orchestrated_job_chat.py`):**

```
1. Request recebida com job_context + candidates + message
2. Backend detecta command_type via detect_command_type(message) → KanbanCommandType
3. Se command_type ∈ _ANALYTICAL_COMMAND_TYPES (12 tipos): análise IA
4. Se command_type ∈ ACTIONABLE_INTENTS: executa ação via ActionExecutor
5. Se é confirmação/rejeição de ação pendente: resolve via PendingActionStore
6. Senão: roteia para Orchestrator.process_request() com contexto enriquecido
```

#### 1.1.3 Chat Dedicado (chat-page.tsx)

- **Localização:** `plataforma-lia/src/components/pages/chat-page.tsx`
- **Contexto:** Chat full-page com LIA — acesso completo
- **Escopo de ferramentas:** `GLOBAL` — `scope_config.py` limita a: `generate_report`, `schedule_report`
- **Endpoint API:** `liaApi.sendMessage()` → `POST /api/backend-proxy/chat` (com suporte a WebSocket via `wsSendMessage`)

**Lógica:** Todas as mensagens vão diretamente ao backend via `sendMessage()`. O backend processa via `Orchestrator.process_request()` com escopo GLOBAL.

### 1.2 Diagrama de Interação

```
┌─────────────────────────────────────────────────────────┐
│  Float Chat (candidates-page)                           │
│  Escopo: TALENT_FUNNEL                                  │
│  Decisão: isGenericQuestion() → orquestrador            │
│           analysisCommands → handleAICommand             │
│           default → executeSearch (busca candidatos)     │
│  → callOrchestratedTalentChat() → /orchestrator/talent-chat │
├─────────────────────────────────────────────────────────┤
│  Kanban Chat (job-kanban-page)                          │
│  Escopo: IN_JOB                                        │
│  Decisão: detect_command_type() → KanbanCommandType     │
│           analytical → análise IA                        │
│           actionable → ActionExecutor                    │
│  → callOrchestratedJobChat() → /orchestrator/job-chat    │
├─────────────────────────────────────────────────────────┤
│  Chat Full (chat-page)                                  │
│  Escopo: GLOBAL                                         │
│  Decisão: todas as mensagens → backend direto            │
│  → liaApi.sendMessage() → /chat (+ WebSocket)            │
└──────────────────────────┬──────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │ Orchestrator │
                    │ + CascadedR. │
                    └──────┬──────┘
                           │ domain dispatch
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        [11 Agentes ReAct via LangGraph]
```

### 1.3 CascadedRouter — 6 Tiers de Roteamento

**Arquivo:** `lia-agent-system/app/orchestrator/cascaded_router.py`

| Tier | Nome                | Mecanismo                          | Custo  | Detalhe                                          |
|------|---------------------|------------------------------------|--------|--------------------------------------------------|
| 0    | MemoryResolver      | Resolução de pronomes/referências  | Zero   | Via `WorkingMemory`; resolve "ele", "essa vaga"  |
| 1    | LRU in-process      | Hash MD5 em memória local          | Zero   | Cache O(1); não distribuído entre workers        |
| 2    | Redis hash cache    | Distribuído, exato, entre workers  | Baixo  | TTL configurável via `ROUTER_CACHE_TTL`          |
| 3    | VectorSemanticCache | pgvector, cosine similarity ≥ 0.92 | Baixo  | Falha graciosamente se indisponível              |
| 4    | FastRouter          | Regex/keyword patterns             | Baixo  | `fast_router.py`; confiança mínima: `ROUTER_FAST_CONFIDENCE_THRESHOLD` |
| 5    | LLM Cascade         | Haiku → Sonnet → Opus              | Alto   | Via `llm_cascade.py`; fallback para IntentRouter legado |
| FB   | Clarification       | Pergunta ao usuário                | Zero   | 6 opções padrão quando nenhum tier resolve       |

**Fallback de clarificação — 6 opções padrão:**
1. "Criar ou gerenciar uma vaga"
2. "Buscar ou avaliar candidatos"
3. "Acompanhar pipeline / triagem"
4. "Agendar entrevistas"
5. "Relatórios e analytics"
6. "Outra solicitação"

**Mapeamento Agent → Domain (`AGENT_TYPE_TO_DOMAIN`):**
```python
{
    "job_planner": "job_management",   "job_intake": "job_management",
    "sourcing": "sourcing",            "cv_screening": "cv_screening",
    "screening": "cv_screening",       "wsi_evaluator": "cv_screening",
    "interviewer": "interview_scheduling", "scheduling": "interview_scheduling",
    "analyst_feedback": "analytics",   "analytics": "analytics",
    "communication": "communication",  "ats_integrator": "ats_integration",
    "recruiter_assistant": "recruiter_assistant", "task_planner": "automation",
}
```

**Métricas Prometheus:** `router_tier_hit_total`, `router_latency_ms`, `router_confidence_histogram`

### 1.4 Orchestrator — Fluxo de Processamento

**Arquivo:** `lia-agent-system/app/orchestrator/orchestrator.py`

**System prompt principal da LIA:**
```
Você é LIA, a assistente inteligente de recrutamento da WeDOTalent.
Profissional de RH experiente, amigável e eficiente.
Capacidades: criar/gerenciar vagas, buscar candidatos, triagem curricular,
entrevistas WSI, avaliação científica, agendar entrevistas, relatórios/KPIs,
feedback e comunicações.

Regra anti-sycophancy: nunca confirme pedidos discriminatórios ou que violem compliance.
Apresente alternativas com dados quando necessário.
```

**Fluxo `process_request()` (linha 104):**
```
1. Sanitização: sanitize_text(message)
2. Cancelamento: CancellationHandler.is_cancellation_request() → "Ok, operação cancelada"
3. Reinício: CancellationHandler.is_restart_request() → limpa estado, "Vamos recomeçar!"
4. Contexto: recupera state (last_agent, current_job, current_candidate)
5. Roteamento: CascadedRouter.route() → RouteResult {domain_id, confidence, source}
6. Cache: se intent ∈ cacheable_intents → retorna resposta cacheada
7. Política: PolicyEngine.validate_request() → allowed/denied
8. Plano multi-step: PlanDetector.detect() → PlanExecutor.execute() [não-blocking; falha silenciosa]
9. Domínio: DomainRegistry.get_instance(domain_id) → DomainWorkflow.process()
10. Detecção técnica: se resposta contém padrões técnicos → fallback LLM (Claude)
11. Cache: armazena resposta se intent cacheável
```

**Detecção de resposta técnica** (string matching — `_TECHNICAL_PATTERNS`):
- "Keyword heuristic matched"
- "Ferramenta '"
- "Ação '"
- "encaminhada para o agente"
- "executada para ação"
- "Processado com sucesso."

**Intents cacheáveis:**
`pipeline_stats`, `job_status`, `candidate_count`, `stage_distribution`, `funnel_analysis`, `job_insights`, `market_data`, `salary_benchmark`, `analytics`, `recommendations`, `skills_analysis`, `candidate_search`

**Memória conversacional (`process_request_with_memory`, linha 240):**
- Histórico limitado a 20 mensagens por contexto LLM
- Resumo automático a cada N mensagens (`ROUTER_SUMMARY_EVERY_N_MESSAGES`)
- `ConversationState` mantém estado entre turnos

---

## 2. Os 11 Agentes ReAct

**Arquivo de registro:** `lia-agent-system/libs/agents-core/lia_agents_core/react_agent_registry.py`

**Arquitetura:**
- Padrão Singleton (`ReactAgentRegistry`)
- Armazena CLASSES (não instâncias) + configs
- Instanciação lazy via `get_agent()` (cacheado, NÃO session-safe) ou `AgentFactory.create_agent()` (session-safe, com `WorkingMemoryService` e `ReActObserver` isolados)
- Todos herdam de `LangGraphReActBase` + `EnhancedAgentMixin`
- Ciclo ReAct: Thought → Action → Observation → (repete até max_iterations)
- Anti-sycophancy presente em todos (via bloco `ANTI_SYCOPHANCY_OPERATIONAL` importado OU regra equivalente no prompt)

### 2.1 Wizard Agent (Criação de Vagas)
- **Domain:** `wizard` | **Classe:** `WizardReActAgent` | **Max iterations:** 5 | **Provider:** Claude
- **Arquivo:** `app/domains/job_management/agents/wizard_react_agent.py`
- **Escopo:** Criação guiada de vagas com sugestões inteligentes
- **Triggers:** "criar vaga", "nova vaga", "abrir posição"
- **FairnessGuard:** Integrado (verifica bias em descrições)
- **Ferramentas:** `search_salary_benchmark`, `validate_job_fields`, `get_job_suggestions`, `save_job_draft`, `get_company_config`, `get_intelligent_salary`, `get_intelligent_skills`, `capture_wizard_feedback`, `generate_enriched_jd` (9 tools)
- **Fluxo:** coleta dados → valida campos → FairnessGuard → gera JD enriquecida → salva rascunho

### 2.2 Pipeline Agent (Triagem de CVs)
- **Domain:** `pipeline` | **Classe:** `PipelineReActAgent` | **Max iterations:** 5 | **Provider:** Claude
- **Arquivo:** `app/domains/cv_screening/agents/pipeline_react_agent.py`
- **Escopo IN (10 capacidades):** consultar dados do candidato, scores WSI, triagem, atualizar dados cadastrais, solicitar coleta de dados, extrair preferências de execução, combinar tarefas, sugerir ações/sub-status, personalizar comunicação, verificar fairness em rejeição
- **Escopo OUT (7 restrições):** outros candidatos, busca de novos, comparar vagas, adicionar em outra vaga, configurar pipeline, analytics gerais, templates de comunicação
- **Ferramentas:** `update_candidate_stage`, `add_candidate_to_vacancy`, `reject_candidate`, `shortlist_candidate`, `bulk_update_candidates_stage`, `add_to_list`, `wsi_screening`, `hide_candidate` (8 tools)

### 2.3 Sourcing Agent (Busca de Candidatos)
- **Domain:** `sourcing` | **Classe:** `SourcingReActAgent` | **Max iterations:** 5 | **Provider:** Claude
- **Arquivo:** `app/domains/sourcing/agents/sourcing_react_agent.py`
- **Escopo:** Busca local (PostgreSQL) + busca externa (Pearch AI), scoring de match, análise de perfil
- **Triggers:** "buscar candidatos", "encontrar perfis", "sourcing"
- **Ferramentas:** `search_candidates`, `get_candidate_details`, `get_candidate_stats`, `get_candidate_history`, `get_talent_quality`, `get_talent_engagement`, `get_talent_availability`, `get_diversity_metrics`, `get_market_benchmarks` (9 tools)

### 2.4 Talent Agent (Assistente de Talentos)
- **Domain:** `talent` | **Classe:** `TalentReActAgent` | **Max iterations:** 5 | **Provider:** Claude
- **Arquivo:** `app/domains/recruiter_assistant/agents/talent_react_agent.py`
- **Prompt:** `app/domains/recruiter_assistant/prompts/talent_assistant_prompts.py`
- **Escopo:** Assistência no funil de talentos, operações sobre candidatos
- **FairnessGuard:** Integrado

### 2.5 Jobs Management Agent (Portfólio de Vagas)
- **Domain:** `jobs_management` | **Classe:** `JobsMgmtReActAgent` | **Max iterations:** 5 | **Provider:** Claude
- **Arquivo:** `app/domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py`
- **Prompt:** `app/domains/recruiter_assistant/prompts/jobs_management_prompts.py`
- **Escopo:** Gestão do portfólio de vagas (listar, filtrar, analisar status)
- **FairnessGuard:** Integrado

### 2.6 Kanban Agent (Análise do Pipeline)
- **Domain:** `kanban` | **Classe:** `KanbanReActAgent` | **Max iterations:** 5 | **Provider:** Claude
- **Arquivo:** `app/domains/recruiter_assistant/agents/kanban_react_agent.py`
- **Prompt:** `app/domains/recruiter_assistant/prompts/kanban_assistant_prompts.py`
- **Escopo:** Análise e operações no kanban; 18 tipos de comando (ver seção 4.2)
- **FairnessGuard:** Integrado | **GUARDRAIL_TOOLS:** Integrados

### 2.7 Policy Agent (Políticas de Contratação)
- **Domain:** `policy` | **Classe:** `PolicyReActAgent` | **Max iterations:** 5 | **Provider:** Claude
- **Arquivo:** `app/domains/hiring_policy/agents/policy_react_agent.py`
- **Prompt:** `app/domains/hiring_policy/agents/policy_system_prompt.py`
- **Escopo:** CRUD de políticas de contratação, validação de compliance, regras de aprovação

### 2.8 Automation Agent (Decomposição de Tarefas)
- **Domain:** `automation` | **Classe:** `AutomationReActAgent` | **Max iterations:** 6 | **Provider:** Claude
- **Arquivo:** `app/domains/automation/agents/automation_react_agent.py`
- **Prompt:** `app/domains/automation/agents/automation_system_prompt.py`
- **Capacidades:**
  - Decomposição de tarefas em subtarefas executáveis
  - Priorização inteligente (urgência × impacto × criticidade)
  - DAG de dependências (grafos acíclicos direcionados)
  - Planos de execução com paralelismo
  - Agentes delegáveis: `job_planner`, `sourcing`, `cv_screening`, `interviewer`, `wsi_evaluator`, `scheduling`, `analyst_feedback`

### 2.9 Analytics Agent (KPIs e Previsões)
- **Domain:** `analytics` | **Classe:** `AnalyticsReActAgent` | **Max iterations:** 6 | **Provider:** Claude
- **Arquivo:** `app/domains/analytics/agents/analytics_react_agent.py`
- **Prompt:** `app/domains/analytics/agents/analytics_system_prompt.py`
- **Ferramentas:** 19 tools (ver seção 6)

### 2.10 Communication Agent (Multi-canal LGPD)
- **Domain:** `communication` | **Classe:** `CommunicationReActAgent` | **Max iterations:** 6 | **Provider:** Claude
- **Arquivo:** `app/domains/communication/agents/communication_react_agent.py`
- **Canais:** Email, WhatsApp, Teams
- **Ferramentas:** `send_email`, `send_whatsapp`, `schedule_interview`, `send_bulk_email`, `send_feedback` (5 tools)

### 2.11 ATS Integration Agent (Integração Bidirecional)
- **Domain:** `ats_integration` | **Classe:** `ATSIntegrationReActAgent` | **Max iterations:** 6 | **Provider:** Claude
- **Arquivo:** `app/domains/ats_integration/agents/ats_integration_react_agent.py`
- **Provedores:** Gupy, Pandapé, Merge (multi-ATS), StackOne (multi-ATS internacional)
- **Fluxos:** Push (WeDOTalent → ATS), Pull (ATS → WeDOTalent)
- **Princípios:** Multi-tenant obrigatório (`company_id`), LGPD (dados sensíveis NÃO sincronizados), idempotência, auditoria SOX/ISO 27001

---

## 3. Capacidades Detalhadas

### 3.1 Avaliação por Rubrica (RubricEvaluationModal)

- **O que faz:** Avalia candidato contra critérios estruturados da vaga, gerando score multi-dimensional
- **Input:** `candidateId`, `jobId`, dados do CV, competências requeridas
- **Processing:** IA (Claude via Pipeline Agent); analisa CV contra cada critério, pesa dimensões, gera evidências
- **Output:** Score 0-100, grade (A+/A/B+/...), dimensões com critérios individuais, pontos fortes/atenção, recomendação, dados WSI (se disponível)
- **Execução:** IA real (Claude)
- **Arquivo:** `plataforma-lia/src/components/rubric-evaluation-modal.tsx`

```typescript
interface RubricEvaluationData {
  overallScore: number       // 0-100
  overallGrade: string       // "A+", "A", "B+", etc.
  dimensions: { name: string; score: number; weight: number;
    criteria: { name: string; score: number; maxScore: number; evidence: string }[]
  }[]
  strengths: string[]
  concerns: string[]
  recommendation: string
  wsiData?: { overallScore: number; competencies: { name: string; score: number; level: string }[] }
}
```

### 3.2 WSI (Work Style Indicator) Screening

- **O que faz:** Triagem comportamental baseada em competências WSI
- **Input:** `candidateId`, `jobId`, competências comportamentais da vaga
- **Processing:** IA (Claude) avalia respostas do candidato contra framework WSI
- **Output:** Score por competência, nível (Básico/Intermediário/Avançado/Expert), parecer geral
- **Execução:** IA real (Claude via Pipeline Agent)
- **Ferramenta:** `wsi_screening` em `app/domains/cv_screening/tools/candidate_tools.py` (linha 563)

### 3.3 LIA Score (Scoring Unificado)

- **O que faz:** Calcula score de compatibilidade (0-100) candidato × vaga
- **Input:** Dados do CV, scores WSI (se disponível), prerequisitos, recência
- **Processing:** Processamento local (sem LLM); fórmula ponderada com redistribuição de pesos
- **Arquivo:** `lia-agent-system/app/services/lia_score_service.py`
- **Execução:** Local (sem IA)

**Fórmula Unified LIA Ranking:**
```
Ranking_Score = (
    Rubricas_Score × W_rubricas +
    WSI_Score × W_wsi +
    Prerequisites_Score × W_prereq +
    Recency_Boost × W_recency +
    Calibration_Adjustment
) × Completeness_Factor
```

**Pesos por cenário de disponibilidade de dados:**
| Cenário           | Rubricas | WSI  | Big Five | Prereq | Recency |
|-------------------|----------|------|----------|--------|---------|
| CV + WSI + Prereq | 0.40     | 0.25 | 0.10     | 0.15   | 0.10    |
| CV + Prereq       | 0.55     | 0.00 | 0.00     | 0.25   | 0.20    |
| CV only           | Redistribuído para rubricas e recency                   |

### 3.4 Busca Híbrida (Local + Pearch AI)

- **O que faz:** Busca candidatos no banco local PostgreSQL e/ou via Pearch AI (externo)
- **Input:** `query` (texto livre ou estruturado), `search_type` ('fast'|'deep'), `limit`, `timeout`
- **Processing:**
  - Busca local: `searchCandidatesLocal()` → `POST /candidates/search/local/` (FREE, sem créditos)
  - Busca externa: `searchCandidates()` → `GET /candidates/search?query=...` (consome créditos Pearch)
- **Output:** `CandidateSearchResponse` com `candidates[]`, `total_results`, `search_time_seconds`, `credits_used`
- **Execução:** Local (busca DB) + API externa (Pearch AI)
- **Arquivo:** `plataforma-lia/src/services/lia-api.ts` (linhas 451-494)

### 3.5 Comparação de Candidatos

- **O que faz:** Compara 2+ candidatos lado a lado (fit técnico, cultural, experiência)
- **Input:** `candidate_ids[]`, `job_context`
- **Processing:** IA (Claude via Kanban/Analytics Agent) + dados locais (LIA Score, WSI)
- **Output:** Ranking comparativo com justificativas, forças/gaps por candidato
- **Execução:** IA real (Claude)
- **Ferramenta:** `compare_candidates` em analytics tools

### 3.6 Calibração de Candidatos

- **O que faz:** Sessão de calibração onde recrutador avalia candidatos pré-selecionados
- **Input:** `job_vacancy_id`, `job_description`, `technical_skills[]`, `behavioral_competencies[]`
- **Processing:** Pearch AI busca candidatos → scoring de match → montagem de perfis calibrados
- **Output:** Lista de `CalibrationCandidate` com scores, experiências, skills mapeados
- **Execução:** API externa (Pearch AI) + processamento local (scoring)
- **Arquivo:** `plataforma-lia/src/services/lia-api.ts` (linhas 144-183)
- **Endpoints:** `POST /calibration/start`, `POST /calibration/feedback`, `GET /calibration/status`

**Fluxo:**
1. Iniciar sessão → Pearch retorna candidatos com `overallScore`
2. Recrutador avalia cada um (aprova/rejeita com `lia_score` e `feedback_reason`)
3. Candidatos aprovados → `addCandidatesToPipeline()` para adicionar ao pipeline

```typescript
interface CalibrationCandidate {
  id, name, photoUrl, linkedinUrl, currentRole, currentCompany, location, education,
  highlights: { icon, label, value }[],
  experiences: { company, role, period, duration, skills[] }[],
  educationHistory: { institution, degree, field, period }[],
  skillMap: { category, skills[] }[], languages: string[],
  matchCriteria: { criteria, met, score }[],
  overallScore: number, averageTenure, currentTenure
}
```

### 3.7 Geração de JD Enriquecida

- **O que faz:** Gera job description completa e otimizada a partir de inputs do wizard
- **Input:** Título, requisitos técnicos, competências, localização, salário
- **Processing:** IA (Claude via Wizard Agent)
- **Output:** JD formatada com seções, keywords SEO, linguagem inclusiva
- **Execução:** IA real (Claude)
- **Ferramenta:** `generate_enriched_jd` em `app/domains/job_management/tools/job_wizard_tools.py`

### 3.8 Benchmark Salarial

- **O que faz:** Compara salário proposto com dados de mercado
- **Input:** `job_title`, `location`, `seniority_level`
- **Processing:** IA (Claude via JobIntake Agent) + dados de mercado
- **Output:** Competitividade, faixa sugerida, ajustes recomendados
- **Execução:** IA real (Claude)
- **Ferramenta:** `search_salary_benchmark`, `get_intelligent_salary`

---

## 4. Templates de Resposta do Chat

### 4.1 Job Analytics — 8 Command Templates

**Arquivo:** `lia-agent-system/app/domains/analytics/services/job_analytics_prompt_service.py`

| # | Comando                  | Agente Executor         | Prompt Template (resumido)                           |
|---|--------------------------|-------------------------|------------------------------------------------------|
| 1 | `funnel_analysis`        | AnalistaFeedbackAgent   | "Analise o funil da vaga {job_title}. Mostre: candidatos por etapa, taxa de conversão, gargalos, tempo médio por etapa." |
| 2 | `comparative_analysis`   | AnalistaFeedbackAgent   | "Compare as vagas selecionadas: {job_titles}. Analise: tempo médio, taxa de conversão, qualidade de candidatos." |
| 3 | `bottleneck_detection`   | AnalistaFeedbackAgent   | "Identifique gargalos na vaga {job_title}: etapas com maior tempo de espera, candidatos parados, ações pendentes." |
| 4 | `time_to_fill_prediction`| AnalistaFeedbackAgent   | "Preveja o tempo para preencher a vaga {job_title} com base em dados históricos e progresso atual." |
| 5 | `candidate_quality_score`| AvaliadorWSIAgent       | "Avalie a qualidade dos candidatos da vaga {job_title}: fit técnico médio, fit cultural, diversidade de fontes." |
| 6 | `sourcing_effectiveness` | SourcingAgent           | "Analise a efetividade do sourcing para {job_title}: melhores canais, taxa de conversão por fonte, custo por candidato." |
| 7 | `weekly_summary`         | AnalistaFeedbackAgent   | "Gere o resumo semanal de recrutamento: novos candidatos, movimentações, entrevistas realizadas, propostas enviadas." |
| 8 | `salary_benchmark`       | JobIntakeAgent          | "Compare o salário da vaga {job_title} com o mercado: está competitivo? Sugestões de ajuste." |

**Fallback offline:** Se agente IA falha, `process_analytics_request()` retorna `{"success": false, "error": str(e)}` — sem template offline alternativo.

### 4.2 Kanban — 18 Command Templates

**Arquivo:** `lia-agent-system/app/domains/recruiter_assistant/prompts/kanban_assistant_prompts.py`

| # | Comando                 | Tipo        | Resposta esperada (JSON format obrigatório)                |
|---|-------------------------|-----------  |------------------------------------------------------------|
| 1 | `rankear_candidatos`    | Análise IA  | `{ranking: [{posicao, candidato_id, score_fit, forcas[], gaps[], justificativa}], insights, recomendacao}` |
| 2 | `performance_funil`     | Análise IA  | `{metricas: {total_candidatos, por_etapa, taxa_conversao_geral, taxa_por_etapa}, performance: {status, pontos_fortes, pontos_atencao, benchmark}}` |
| 3 | `gargalos_processo`     | Análise IA  | `{gargalos: [{etapa, tipo, descricao, impacto, recomendacao}], visao_geral, prioridades}` |
| 4 | `comparar_candidatos`   | Análise IA  | Comparativo detalhado com dimensões e recomendação         |
| 5 | `resumir_perfil`        | Análise IA  | Resumo executivo do candidato                              |
| 6 | `candidatos_ativos`     | Query local | Lista de candidatos ativos na vaga                         |
| 7 | `taxa_conversao`        | Query local | Taxa de conversão por etapa                                |
| 8 | `tempo_medio`           | Query local | Tempo médio por etapa do pipeline                          |
| 9 | `candidatos_parados`    | Query local | Candidatos sem movimentação recente                        |
| 10| `top_candidatos`        | Análise IA  | Top candidatos por score/fit                               |
| 11| `mover_candidato`       | Ação        | Execução via `ActionExecutor.move_candidate()`             |
| 12| `enviar_email`          | Ação        | Execução via `ActionExecutor.send_email()`                 |
| 13| `disparar_triagem`      | Ação        | Execução via `ActionExecutor.start_screening()`            |
| 14| `agendar_entrevista`    | Ação        | Execução via `ActionExecutor.schedule_interview()`         |
| 15| `solicitar_dados`       | Ação        | Execução via `ActionExecutor.request_data()`               |
| 16| `analisar_perfil`       | Análise IA  | Análise aprofundada com recomendações                      |
| 17| `aprovar_candidato`     | Ação        | Execução via `ActionExecutor.approve_candidate()`          |
| 18| `analise_geral`         | Análise IA  | Análise geral do pipeline (fallback default)               |

**Cada template inclui:**
- `keywords[]` — palavras-chave para detecção
- `prompt_template` — prompt com placeholders `{job_context}`, `{candidates_context}`, `{pipeline_context}`
- `response_sections[]` — seções esperadas na resposta
- `follow_up_prompts[]` — sugestões de próximos passos

**Fallback offline:** Templates de análise retornam dados do banco local quando LLM falha. Templates de ação retornam erro com mensagem: "Desculpe, ocorreu um erro ao processar sua requisição."

### 4.3 Float Chat — Comandos de Análise

**Detecção via `analysisCommands[]` (candidates-page.tsx, linha 5664):**

| Comando                    | Ação                                      |
|----------------------------|--------------------------------------------|
| "analisar potencial"       | Análise de potencial de crescimento via IA |
| "resumo executivo"         | Resumo executivo dos resultados de busca   |
| "resumir busca"            | Resumo consolidado da busca                |
| "top 5" / "top5"           | Top 5 melhores candidatos                  |
| "comparar"                 | Comparação entre candidatos selecionados   |
| "pontos a desenvolver"     | Pontos de desenvolvimento                  |
| "vagas ideais"             | Tipos de vagas adequadas                   |
| "definir tipo"             | Classificação de tipo de perfil            |

**Fallback offline:** Se IA falha, o Orchestrator retorna: "Olá! Sou a LIA, sua assistente de recrutamento. Recebi sua mensagem sobre '{mensagem[:50]}...' Como posso ajudar você hoje?" com `suggested_prompts: ["Criar uma nova vaga", "Buscar candidatos", "Ver minhas tarefas pendentes"]`

---

## 5. Análises e Relatórios

### 5.1 ProactiveInsightCard

**Arquivo:** `plataforma-lia/src/components/proactive-insight-card.tsx`
**Ativação:** Exibido automaticamente após busca de candidatos em `candidates-page.tsx`
**Execução:** Processamento local (backend calcula distribuições sem LLM); campo `narrative` opcional (IA quando disponível)

**Dados entregues (`SearchAnalytics`):**
- **Summary:** total_candidates, local_count, global_count, average_lia_score
- **Contact quality:** with_valid_phone, with_valid_email, with_linkedin (contagens + percentuais)
- **Distributions:** seniority (Record), location (Record), work_model (Record)
- **Top skills:** skill + count + percentage
- **Top companies:** company + count
- **Experience range:** min, max, average, median (anos)
- **Alerts:** tipo (warning/info/success) + mensagem
- **Suggested actions:** id, label, icon, description, action_type

**Como são computados:**
- Backend analisa os candidatos retornados pela busca
- Distribuições calculadas por contagem/agrupamento
- Alertas baseados em thresholds (ex: "Poucos candidatos com telefone válido")
- Ações sugeridas baseadas no contexto da busca

### 5.2 SaturationBadge

**Arquivo:** `plataforma-lia/src/components/kanban/components/SaturationBadge.tsx`
**Ativação:** Header do kanban de cada vaga
**Execução:** Processamento local (backend calcula thresholds sem LLM)
**Endpoint:** `GET /api/backend-proxy/job-vacancies/{jobId}/saturation-status/`

**Dados entregues (`SaturationStatus`):**
- `approved_count` / `saturation_threshold` → `saturation_percentage`
- `is_saturated` (boolean), `slots_remaining`
- `recommendation`: `"continue_screening"` | `"pause_screening"`
- Canal orgânico vs sourcing com thresholds independentes
- `last_screened_at`, `saturation_disabled_until`

**Como são computados:**
- Backend conta candidatos aprovados por canal
- Compara com threshold configurado (por empresa/vaga)
- Estados: `normal` (< 90%), `almost` (≥ 90%), `saturated` (orgânico ou sourcing saturado)

**Ações do usuário:**
- Aumentar threshold: `POST /job-vacancies/{jobId}/unlock-pipeline/` com `{action: "increase_threshold", new_threshold}`
- Desativar temporariamente: `{action: "disable_temporarily", disable_hours}`

### 5.3 JobReportModal

**Arquivo:** `plataforma-lia/src/components/job-report-modal.tsx`
**Ativação:** Botão em `jobs-page.tsx` e `job-kanban-page.tsx`
**Execução:** Processamento local (dados atualmente mockados no frontend)
**Exportação:** PDF via `html2canvas` + `jsPDF`

**Seções selecionáveis (7):**
1. **Overview** — Dados gerais da vaga (título, departamento, localização)
2. **Funnel** — Total candidatos (156), screening (89), interview (34), final (12), hired (3), taxa conversão (1.9%), time-to-hire (23 dias), custo (R$ 4.500)
3. **Candidates** — Top 5 com nome, score, status, fit %
4. **Timeline** — Eventos: vaga publicada → triagem → entrevistas → testes → decisão → contratação
5. **Costs** — Budget total/gasto/restante + breakdown (divulgação, plataformas, testes, equipe, LIA/automação)
6. **Performance** — Channel performance: LinkedIn (67 cand, 89% qualidade), Website (45, 76%), LIA Database (28, 92%), Referral (16, 94%)
7. **Recommendations** — NPS (87), satisfação candidato (4.6/5), satisfação gestor (4.8/5), benchmarks mercado

**Nota:** Dados atualmente hardcoded no frontend. Funcionalidade incompleta — precisa integrar com backend real.

### 5.4 SearchAnalytics

Interface compartilhada com `ProactiveInsightCard` (ver 5.1). Utilizada em `candidates-page.tsx` após buscas para fornecer insights automáticos sobre os resultados.

---

## 6. Sistema Preditivo e Insights

### 6.1 Ferramentas Preditivas (Analytics Agent)

**Execução:** IA (Claude via Analytics Agent); dados alimentados por queries ao PostgreSQL

| Ferramenta              | Input                      | Processing                              | Output                               | Surfacing UI                     |
|-------------------------|----------------------------|-----------------------------------------|--------------------------------------|----------------------------------|
| `get_prediction_metrics`| `job_id`, `time_range`    | Query histórico + modelo de regressão   | Previsões de hiring (prazo, prob.)   | Analytics dashboard, Chat        |
| `get_ml_predictions`    | `job_id`, `model_type`    | Modelo ML treinado em dados da empresa  | Previsões com confidence intervals   | Analytics dashboard              |
| `get_conversion_patterns`| `job_id`/`company_id`    | Análise de padrões no funil             | Taxas de conversão por etapa/fonte   | JobReportModal, Chat             |
| `get_smart_alerts`      | `company_id`, `threshold` | Detecção de anomalias e tendências      | Lista de alertas com severidade      | Dashboard, SaturationBadge       |
| `get_trends`            | `metric`, `time_range`    | Séries temporais de métricas            | Tendências com visualização          | Analytics dashboard              |
| `get_bottleneck_analysis`| `job_id`                 | Análise de tempos por etapa             | Gargalos + recomendações             | Kanban Chat, Dashboard           |

### 6.2 Predições Específicas

| Predição                     | Dados Utilizados                            | Endpoint/Serviço                          | Surfacing UI                |
|------------------------------|---------------------------------------------|-------------------------------------------|-----------------------------|
| Probabilidade de contratação | Histórico vagas similares, pool atual       | `predictive_analytics_service.py`         | Chat, Analytics             |
| Time-to-Fill (TTF)           | Tempos por etapa, velocidade pipeline       | `time_to_fill_prediction` command         | Chat, JobReportModal        |
| Risco de dropout             | Tempo parado, engajamento, mercado          | `get_smart_alerts` + `EWS`               | SaturationBadge, Alertas    |
| Previsão de pipeline         | Conversão histórica, volume atual           | `get_ml_predictions`                      | Analytics dashboard         |
| Predição salarial            | Mercado, cargo, localização, senioridade    | `get_intelligent_salary` / `salary_benchmark` | Wizard, Chat            |

### 6.3 Serviços de Inteligência Operacional

**Arquivos:** `app/services/predictive_analytics_service.py`, `search_analytics_service.py`, `wizard_analytics_service.py`, `learning_analytics_service.py`

| # | Serviço                       | Tipo           | Dados Utilizados                     | Surfacing UI                       |
|---|-------------------------------|----------------|--------------------------------------|------------------------------------|
| 1 | Pipeline Velocity Engine      | Local (query)  | Timestamps de movimentação por etapa | Kanban page, Analytics dashboard   |
| 2 | Zero-Touch Scheduling         | IA + Local     | Disponibilidade, preferências, SLAs  | Communication Agent, Calendar API  |
| 3 | Silver Medalists              | IA (matching)  | Histórico de candidatos rejeitados   | Sourcing Agent, ProactiveInsightCard|
| 4 | Recruiter Intelligence        | Local (metrics)| Volume, velocidade, qualidade        | Analytics dashboard                |
| 5 | Early Warning Score (EWS)     | IA (anomaly)   | Pipeline metrics, tempos, saturação  | SaturationBadge, SmartAlerts       |
| 6 | Journey Intelligence          | Local + IA     | Touchpoints do candidato             | Kanban page                        |
| 7 | Recruiter Perf. Benchmark     | Local (metrics)| KPIs comparativos entre recrutadores | Analytics dashboard                |
| 8 | Pipeline Prediction           | IA (ML model)  | Dados históricos vagas similares     | JobReportModal, Analytics          |

### 6.4 Response Cache Service

- Cache de respostas para intents analíticas recorrentes
- `generate_cache_key()`: intent + contexto + mensagem + company_id
- Invalidação por entidade: `invalidate_for_job()`, `invalidate_for_candidate()`, `invalidate_for_company()`
- Invalidação por padrão regex: `invalidate_by_pattern()`

---

## 7. Quick Actions e Ações Bulk

### 7.1 Quick Actions do Chat Full (chat-page.tsx)

| Quick Action                          | Mensagem Enviada                                 |
|---------------------------------------|--------------------------------------------------|
| Criar nova vaga                       | `"Criar uma nova vaga"`                          |
| Solicitar aprovação                   | `"Solicite aprovação de nova vaga"`              |
| Compartilhar com gestor               | `"Compartilhe candidatos com gestor"`            |
| Solicitar feedback                    | `"Solicite feedback de entrevista"`              |
| Consultar candidato                   | `"Consulte informações sobre candidato"`         |
| Adicionar candidato                   | `"Adicione novo candidato"`                      |
| Reagendar entrevista                  | `"Reagende uma entrevista"`                      |
| Agendar entrevista (contextual)       | `"agendar entrevista"`                           |
| Avaliar fit técnico                   | `"avaliar fit técnico do candidato"`             |
| Gerar email follow-up                 | `"gerar email de follow-up"`                     |
| Enviar WhatsApp                       | `"enviar mensagem whatsapp"`                     |
| Comparar perfis                       | `"comparar perfis de candidatos"`                |

### 7.2 Ações Bulk — Funil de Talentos (UnifiedBulkActionsBar)

**Arquivo:** `plataforma-lia/src/components/ui/unified-bulk-actions-bar.tsx`
**Contexto:** `context="funnel"` na candidates-page

| # | Ação              | Prop               | Disponível em Funil | Disponível em Kanban |
|---|-------------------|---------------------|---------------------|----------------------|
| 1 | Mover etapa       | `onMoveStage`      | Sim                 | Sim                  |
| 2 | Rejeitar          | `onReject`          | Sim                 | Sim                  |
| 3 | Enviar email      | `onEmail`           | Sim                 | Sim                  |
| 4 | Agendar entrevista| `onSchedule`        | Sim                 | Sim                  |
| 5 | Adicionar a vaga  | `onAddToVacancy`    | Sim                 | Sim                  |
| 6 | Mover para lista  | `onMoveToList`      | Sim                 | Sim                  |
| 7 | Exportar          | `onExport`          | Sim                 | Sim                  |
| 8 | Esconder          | `onHide`            | Sim                 | Sim                  |
| 9 | Triagem WSI       | `onWSIScreening`    | Sim                 | Sim                  |

### 7.3 Ações Contextuais — ContextualActionsBanner

**Arquivo:** `plataforma-lia/src/components/contextual-actions-banner.tsx`

| # | Ação              | Disponível |
|---|-------------------|------------|
| 1 | Mover etapa       | Sim        |
| 2 | Rejeitar          | Sim        |
| 3 | Enviar email      | Sim        |
| 4 | Agendar entrevista| Sim        |
| 5 | Adicionar a vaga  | Sim        |
| 6 | Mover para lista  | Sim        |
| 7 | Esconder          | Sim        |
| 8 | Triagem WSI       | Sim        |

### 7.4 Ações do Kanban Chat (ActionExecutor)

**Arquivo:** `lia-agent-system/app/orchestrator/action_executor.py`

Ações executadas diretamente pelo backend (closed-loop, sem modal):
- `move_candidate` — move candidato entre etapas
- `send_email` — envia email
- `start_screening` — inicia triagem WSI
- `schedule_interview` — agenda entrevista
- `request_data` — solicita dados adicionais
- `analyze_profile` — análise de perfil
- `approve_candidate` — aprova candidato

Fluxo HITL (Human-in-the-loop):
1. LIA propõe ação → `needs_confirmation: true`
2. Usuário confirma/rejeita → `PendingActionStore`
3. Se confirmado → `ActionExecutor` executa ação real

---

## 8. Limitações, Dívidas Técnicas e Funcionalidades Incompletas

### 8.1 Processamento Local vs IA

| Funcionalidade          | Status Atual                                              |
|-------------------------|------------------------------------------------------------|
| LIA Score               | Local (sem LLM) — fórmula ponderada                      |
| Busca de candidatos     | Local (PostgreSQL) + API externa (Pearch AI)              |
| Distribuições/Analytics | Local — contagens e agrupamentos                          |
| SaturationBadge         | Local — threshold vs contagem                             |
| JobReportModal          | Local — dados hardcoded no frontend (mock)                |
| Avaliação por rubrica   | IA real (Claude)                                          |
| WSI Screening           | IA real (Claude)                                          |
| Comparação candidatos   | IA real (Claude)                                          |
| Ranking                 | IA real (Claude)                                          |
| JD Enriquecida          | IA real (Claude)                                          |
| Benchmark salarial      | IA real (Claude) + dados de mercado                       |

### 8.2 Fallbacks Hardcoded

1. **Orchestrator fallback** — Se LLM falha, retorna: "Olá! Sou a LIA, sua assistente de recrutamento. Recebi sua mensagem sobre '{msg[:50]}..'" com 3 sugestões fixas
2. **CascadedRouter fallback** — Se nenhum tier resolve, retorna clarificação com 6 opções fixas
3. **VectorSemanticCache** — Inicialização graciosa; se pgvector indisponível, pula silenciosamente
4. **PlanDetector** — Falha silenciosa via try/except (non-blocking)

### 8.3 Detecção de Intenção por Keywords

- `isGenericQuestion()` — 5 regex + 46 keywords de busca; frágil para termos novos
- `analysisCommands[]` — 8 padrões fixos de string matching
- `detect_command_type()` — keywords por KanbanCommandType; pode falhar para variações
- `_TECHNICAL_PATTERNS` — 5 padrões de string matching para detecção de resposta técnica

### 8.4 Cache

- **Tier 1 (LRU):** In-process, não distribuído entre workers; eviction FIFO
- **Tier 2 (Redis):** Implementado via `SemanticCache` com TTL configurável
- **Response Cache:** Funcional, mas sem invalidação automática por eventos (ex: novo candidato adicionado)

### 8.5 Funcionalidades Incompletas

1. **handleOpenRubricAnalysis orphaned** — Função em `candidates-page.tsx` (linha 6424) sem call sites; modal ainda renderiza mas não é acessível via botão
2. **JobReportModal com dados mock** — Dados hardcoded no frontend (funnelMetrics, channelPerformance, timeline, budget); sem integração com backend real
3. **WSI Voice** — Não implementado; WSI é text-only
4. **Calibração limitada** — Implementada no frontend sem agente ReAct dedicado; depende 100% do Pearch AI
5. **Arquivo monolítico** — `candidates-page.tsx` tem 10.398 linhas; `lia-api.ts` tem 4.943 linhas
6. **Notificações** — `JobCreatedNotificationRequest` suporta email + Teams; WhatsApp ausente

### 8.6 Dívidas Técnicas

1. **IntentRouter legado** — Coexiste com LLM Cascade como fallback; duplicação de lógica
2. **Mapeamento agent_type → domain** — Hardcoded em `AGENT_TYPE_TO_DOMAIN`; sem registro dinâmico
3. **AgentFactory vs get_agent** — Dois padrões coexistem; `get_agent()` NÃO é session-safe mas é usado em código legado
4. **PolicyEngine** — DB service pode ser `None`; validação pode falhar silenciosamente
5. **Detecção de resposta técnica** — String matching (`_TECHNICAL_PATTERNS`); frágil com novas mensagens
6. **Escopo GLOBAL** — `scope_config.py` limita a apenas `generate_report` + `schedule_report`, mas o chat-page envia tudo para o Orchestrator que ignora scope na execução

### 8.7 Compliance

1. **Anti-sycophancy** — Presente em todos os agentes (via bloco compartilhado ou equivalente no prompt), porém sem guardrail automatizado em runtime
2. **FairnessGuard** — Integrado em 4 agentes (Wizard, Talent, Jobs Management, Kanban); ausente em Analytics, Automation, ATS Integration, Communication, Sourcing, Pipeline, Policy
3. **LGPD em ATS** — Lista de campos sensíveis não sincronizados é hardcoded
4. **Audit trail** — SOX/ISO 27001 mencionados no prompt do ATS Agent, mas sem implementação de audit trail centralizado

---

## 9. Oportunidades e Capacidades Ausentes

### 9.1 Score Clicável no Funil

**Status:** Ausente
**Descrição:** Permitir que recrutador clique no LIA Score de um candidato no funil e veja breakdown detalhado (rubricas, WSI, prerequisites, recency) com explicação de cada componente
**Complexidade:** Média — dados já existem no `lia_score_service.py`; precisa de endpoint dedicado + componente UI
**Arquivos relevantes:** `lia_score_service.py` (fórmula), `candidates-page.tsx` (UI)

### 9.2 Análise Comparativa com IA Real

**Status:** Parcialmente implementado (via `compare_candidates` tool)
**Descrição:** Análise comparativa multi-dimensional entre candidatos com visualização lado-a-lado no frontend
**Gap:** Não há componente visual dedicado para comparação; resultado aparece apenas como texto no chat
**Arquivos relevantes:** `analytics_query_tools.py`, `kanban_assistant_prompts.py`

### 9.3 Fit Cultural com Dados de Entrevista

**Status:** Ausente
**Descrição:** Avaliar fit cultural do candidato usando dados de entrevistas realizadas (notas do entrevistador, sentimento, alinhamento de valores)
**Gap:** WSI avalia competências comportamentais, mas não há cruzamento com dados de entrevista reais
**Arquivos relevantes:** `lia_score_service.py` (scoring), `pipeline_react_agent.py` (pipeline)

### 9.4 Auto-routing Inteligente

**Status:** Parcialmente implementado (CascadedRouter)
**Descrição:** Roteamento que aprende com o tempo quais agentes foram mais úteis para cada tipo de mensagem
**Gap:** CascadedRouter usa cache (melhora velocidade) mas não faz aprendizado; peso dos tiers é estático
**Arquivos relevantes:** `cascaded_router.py`, `llm_cascade.py`

### 9.5 Insights Proativos no Kanban

**Status:** Parcialmente implementado (SaturationBadge)
**Descrição:** LIA sugere proativamente ações no kanban (ex: "3 candidatos parados há 7 dias na etapa Entrevista")
**Gap:** SaturationBadge existe mas é reativo (badge estático); falta ProactiveAgentWorker integrado ao kanban UI
**Arquivos relevantes:** `SaturationBadge.tsx`, `proactive_agent_worker.py`

### 9.6 Relatório Cross-vagas

**Status:** Ausente
**Descrição:** Relatório consolidado comparando métricas entre todas as vagas da empresa (TTF, qualidade, custo, fontes)
**Gap:** `comparative_analysis` command existe mas compara apenas vagas selecionadas; falta dashboard consolidado
**Arquivos relevantes:** `job_analytics_prompt_service.py`, `job-report-modal.tsx`

### 9.7 ML Adaptativo

**Status:** Parcialmente implementado (LIA Score com pesos fixos)
**Descrição:** Modelo que ajusta pesos do scoring baseado em feedback de contratações reais
**Gap:** `Calibration_Adjustment` existe na fórmula do LIA Score mas é sempre 0; falta loop de feedback
**Arquivos relevantes:** `lia_score_service.py` (fórmula com `Calibration_Adjustment`), `learning_analytics_service.py`

### 9.8 Benchmark de Mercado Real

**Status:** Parcialmente implementado (via `salary_benchmark` command)
**Descrição:** Benchmark de mercado com dados reais e atualizados (salário, tempo de contratação, volume)
**Gap:** Benchmark salarial usa IA para estimar; não há integração com fontes de dados de mercado reais (ex: Glassdoor, Levels.fyi)
**Arquivos relevantes:** `job_wizard_tools.py` (`search_salary_benchmark`, `get_intelligent_salary`)

### 9.9 WSI Assíncrono

**Status:** Ausente
**Descrição:** Enviar triagem WSI para candidato e processar respostas assincronamente quando o candidato responder
**Gap:** WSI é síncrono (recrutador inicia, LIA processa em tempo real); não há fluxo de envio + coleta assíncrona
**Arquivos relevantes:** `wsi_screening` tool, `pipeline_react_agent.py`

### 9.10 Outras Oportunidades

| Oportunidade                           | Complexidade | Impacto |
|----------------------------------------|-------------|---------|
| Registro dinâmico de agentes (YAML)    | Alta        | Alto    |
| Multi-model por agente (GPT/Gemini)    | Média       | Alto    |
| RAG por domínio (embeddings)           | Alta        | Alto    |
| Circuit breaker para Pearch AI         | Baixa       | Médio   |
| Validar escopo de tools no backend     | Baixa       | Alto    |
| Ativar FairnessGuard em todos agentes  | Baixa       | Alto    |
| Remover IntentRouter legado            | Baixa       | Médio   |
| Streaming de pensamentos ReAct via WS  | Média       | Médio   |

---

## 10. Referência de Arquivos

### 10.1 Frontend (plataforma-lia/)

| Arquivo | Responsabilidade |
|---------|-----------------|
| `src/components/pages/candidates-page.tsx` | Float Chat, busca, análise, UnifiedBulkActionsBar, ProactiveInsightCard, isGenericQuestion(), handleAICommand() |
| `src/components/pages/job-kanban-page.tsx` | Kanban Chat, pipeline visual, SaturationBadge, drag-and-drop, JobReportModal |
| `src/components/pages/chat-page.tsx` | Chat Full dedicado, Quick Actions, histórico, WebSocket |
| `src/components/rubric-evaluation-modal.tsx` | Modal de avaliação por rubrica multi-dimensional |
| `src/components/proactive-insight-card.tsx` | Card de insights proativos após busca (SearchAnalytics) |
| `src/components/kanban/components/SaturationBadge.tsx` | Badge de saturação do pipeline por canal |
| `src/components/job-report-modal.tsx` | Modal de relatório da vaga com export PDF (dados mock) |
| `src/components/ui/unified-bulk-actions-bar.tsx` | Barra de ações bulk (9 ações, contexto funnel/vacancy) |
| `src/components/contextual-actions-banner.tsx` | Banner de ações contextuais (8 ações) |
| `src/services/lia-api.ts` | Client API (4943 linhas): chat, search, calibration, notifications |
| `src/lib/api/kanban-assistant.ts` | API helpers: callOrchestratedTalentChat(), callOrchestratedJobChat() |
| `src/contexts/lia-float-context.tsx` | Estado global do Float/Super Prompt (isOpen, isExpanded, sharedMessages) |
| `src/components/wsi/` | Componentes WSI (diretório) |

### 10.2 Backend (lia-agent-system/)

| Arquivo | Responsabilidade |
|---------|-----------------|
| `app/orchestrator/orchestrator.py` | Orchestrator principal: process_request(), memória, cache, planos |
| `app/orchestrator/cascaded_router.py` | CascadedRouter 6 tiers com métricas Prometheus |
| `app/orchestrator/fast_router.py` | FastRouter regex/keyword (Tier 4) |
| `app/orchestrator/llm_cascade.py` | LLM Cascade Haiku→Sonnet→Opus (Tier 5) |
| `app/orchestrator/action_executor.py` | Execução closed-loop de ações (move, email, triagem) |
| `app/orchestrator/pending_action.py` | Store de ações pendentes para HITL |
| `app/orchestrator/memory_resolver.py` | Resolução de pronomes/referências (Tier 0) |
| `app/api/v1/orchestrated_job_chat.py` | Endpoint /orchestrator/job-chat (Kanban) |
| `app/api/v1/lia_assistant.py` | Endpoint /orchestrator/talent-chat (Float) |
| `libs/agents-core/lia_agents_core/react_agent_registry.py` | Registry Singleton + AgentFactory session-safe |
| `app/domains/job_management/agents/wizard_react_agent.py` | Wizard Agent (criação de vagas) |
| `app/domains/cv_screening/agents/pipeline_react_agent.py` | Pipeline Agent (triagem CVs) |
| `app/domains/sourcing/agents/sourcing_react_agent.py` | Sourcing Agent (busca candidatos) |
| `app/domains/recruiter_assistant/agents/talent_react_agent.py` | Talent Agent (funil) |
| `app/domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py` | Jobs Management Agent (portfólio vagas) |
| `app/domains/recruiter_assistant/agents/kanban_react_agent.py` | Kanban Agent (pipeline) |
| `app/domains/hiring_policy/agents/policy_react_agent.py` | Policy Agent (políticas) |
| `app/domains/automation/agents/automation_react_agent.py` | Automation Agent (decomposição tarefas) |
| `app/domains/analytics/agents/analytics_react_agent.py` | Analytics Agent (KPIs, previsões) |
| `app/domains/communication/agents/communication_react_agent.py` | Communication Agent (multi-canal LGPD) |
| `app/domains/ats_integration/agents/ats_integration_react_agent.py` | ATS Integration Agent (Gupy, Pandapé, Merge, StackOne) |
| `app/domains/recruiter_assistant/prompts/kanban_assistant_prompts.py` | 18 Kanban Command Templates + detect_command_type() |
| `app/domains/analytics/services/job_analytics_prompt_service.py` | 8 Analytics Command Templates + COMMAND_TEMPLATES |
| `app/services/lia_score_service.py` | LIA Score: fórmula unificada, pesos por cenário, DataAvailability |
| `app/services/predictive_analytics_service.py` | Serviço preditivo de contratação |
| `app/services/search_analytics_service.py` | Analytics de busca de candidatos |
| `app/services/response_cache_service.py` | Cache de respostas por intent |
| `app/tools/scope_config.py` | Configuração de escopo: TALENT_FUNNEL, JOB_TABLE, IN_JOB, GLOBAL |
| `docs/analises/MAPA_INTELIGENCIA_LIA_COMPLETO.md` | Documento de referência existente (v3.0) |

---

*Documento gerado por auditoria automatizada do código-fonte em 13/03/2026.*
