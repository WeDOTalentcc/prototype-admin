# Relatório Completo de Capacidades e Prompts — LIA (WeDOTalent)
**Versão:** 1.0 — 13/03/2026
**Fonte:** Auditoria direta do código-fonte (`lia-agent-system/` + `plataforma-lia/`)
**Propósito:** Mapeamento técnico exaustivo de toda a arquitetura de prompts, interação entre chats, agentes ReAct, capacidades, templates de resposta, análises, sistema preditivo, limitações, dívidas técnicas e oportunidades de evolução.

---

## Sumário

1. [Arquitetura de Chats e Interação](#1-arquitetura-de-chats-e-interação)
2. [Sistema de Roteamento — CascadedRouter](#2-sistema-de-roteamento--cascadedrouter)
3. [Orchestrator — Fluxo de Processamento](#3-orchestrator--fluxo-de-processamento)
4. [Agentes ReAct — Registro e Capacidades](#4-agentes-react--registro-e-capacidades)
5. [System Prompts por Agente](#5-system-prompts-por-agente)
6. [Ferramentas (Tools) por Domínio](#6-ferramentas-tools-por-domínio)
7. [Templates de Resposta e Análises](#7-templates-de-resposta-e-análises)
8. [Sistema Preditivo e Analytics](#8-sistema-preditivo-e-analytics)
9. [Limitações e Dívidas Técnicas](#9-limitações-e-dívidas-técnicas)
10. [Oportunidades de Evolução](#10-oportunidades-de-evolução)

---

## 1. Arquitetura de Chats e Interação

A plataforma LIA possui **3 camadas de chat** distintas, cada uma com contexto, escopo e prompts diferenciados:

### 1.1 Float Chat (candidates-page.tsx)

- **Localização:** `plataforma-lia/src/components/pages/candidates-page.tsx`
- **Contexto:** Página de funil de talentos (listagem geral de candidatos)
- **Escopo:** `TALENT_FUNNEL` — limita ferramentas a operações sobre o funil global
- **Endpoint API:** `callOrchestratedTalentChat()` → `POST /api/backend-proxy/orchestrator/talent-chat`
- **Capacidades:**
  - Busca e filtragem de candidatos no funil
  - Operações bulk via `UnifiedBulkActionsBar` (9 ações):
    - Mover etapa, rejeitar, enviar email, agendar entrevista, adicionar a vaga, mover para lista, exportar, esconder, triagem WSI
  - Operações contextuais via `ContextualActionsBanner` (8 ações):
    - Mover etapa, rejeitar, enviar email, agendar entrevista, adicionar a vaga, mover para lista, esconder, triagem WSI
  - `RubricEvaluationModal` — avaliação por rubrica (modal com dados WSI)
- **Prompt implícito:** O contexto `TALENT_FUNNEL` filtra as ferramentas disponíveis via `scope_config.py`

### 1.2 Kanban Chat (job-kanban-page.tsx)

- **Localização:** `plataforma-lia/src/components/pages/job-kanban-page.tsx`
- **Contexto:** Kanban de uma vaga específica (pipeline de candidatos por etapa)
- **Escopo:** `IN_JOB` — ferramentas limitadas ao contexto de uma vaga
- **Endpoint API:** `callOrchestratedJobChat()` → `POST /api/backend-proxy/orchestrator/job-chat`
- **Capacidades:**
  - Gestão de candidatos dentro de uma vaga específica
  - Mesmas ações bulk do Float Chat, contextualizadas à vaga
  - Drag-and-drop entre etapas do pipeline
  - `RubricEvaluationModal` — mesma funcionalidade do Float Chat

### 1.3 Chat Dedicado (chat-page.tsx)

- **Localização:** `plataforma-lia/src/components/pages/chat-page.tsx`
- **Contexto:** Chat full-page com LIA — acesso a todas as capacidades
- **Escopo:** `GLOBAL` — ferramentas restritas a `generate_report` e `schedule_report` (ver `scope_config.py`)
- **Endpoint API:** `liaApi.sendMessage()` → `POST /api/backend-proxy/chat` (com suporte a WebSocket via `wsSendMessage`)
- **Capacidades completas:**
  - Quick actions pré-definidas: "Criar uma nova vaga", "Solicitar aprovação", "Compartilhar candidatos com gestor", "Solicitar feedback de entrevista", "Consultar candidato", "Adicionar candidato", "Reagendar entrevista"
  - Ações contextuais sobre candidatos selecionados: comparar perfis, adicionar a vaga
  - Busca via Pearch AI (deep search externo) e busca local
  - Histórico de conversas persistente
  - Suporte a anexos (arquivos + áudio)
  - Resumo automático a cada N mensagens (`ROUTER_SUMMARY_EVERY_N_MESSAGES`)

### 1.4 Interação entre Chats

```
┌─────────────────────────────────────────────────────────┐
│  Float Chat (candidates-page)                           │
│  Escopo: TALENT_FUNNEL                                  │
│  → callOrchestratedTalentChat() → /orchestrator/talent-chat │
├─────────────────────────────────────────────────────────┤
│  Kanban Chat (job-kanban-page)                          │
│  Escopo: IN_JOB                                        │
│  → callOrchestratedJobChat() → /orchestrator/job-chat    │
├─────────────────────────────────────────────────────────┤
│  Chat Full (chat-page)                                  │
│  Escopo: GLOBAL                                         │
│  → liaApi.sendMessage() → /chat (+ WebSocket wsSendMessage) │
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

**Escopo de ferramentas (scope_config.py):**

| Escopo           | Mapeamento de contexto                    |
|------------------|-------------------------------------------|
| `TALENT_FUNNEL`  | `"talent_funnel"`, `"candidates"`         |
| `JOB_TABLE`      | `"job_table"`, `"jobs"`, `"vacancies"`    |
| `IN_JOB`         | `"in_job"`, `"pipeline"`                  |
| `GLOBAL`         | `"global"` (default; ferramentas: `generate_report`, `schedule_report`) |

---

## 2. Sistema de Roteamento — CascadedRouter

**Arquivo:** `lia-agent-system/app/orchestrator/cascaded_router.py`

### 2.1 Arquitetura de 6 Tiers (custo crescente)

| Tier | Nome                | Mecanismo                          | Complexidade | Custo |
|------|---------------------|------------------------------------|--------------|-------|
| 0    | MemoryResolver      | Resolução de pronomes/referências  | O(1)         | Zero  |
| 1    | LRU in-process      | Hash MD5 em memória local          | O(1)         | Zero  |
| 2    | Redis hash cache    | Distribuído, exato, entre workers  | O(1)         | Baixo |
| 3    | VectorSemanticCache | pgvector, cosine similarity ≥ 0.92 | O(n)         | Baixo |
| 4    | FastRouter          | Regex/keyword patterns             | O(n)         | Baixo |
| 5    | LLM Cascade         | Haiku → Sonnet → Opus              | O(1)         | Alto  |
| FB   | Clarification       | Pergunta ao usuário                | N/A          | Zero  |

### 2.2 Fluxo de Resolução

```
Mensagem → Tier 0 (resolve pronomes via WorkingMemory)
         → Tier 1 (cache MD5 in-process)
         → Tier 2 (Redis hash exato)
         → Tier 3 (pgvector cosine ≥ 0.92)
         → Tier 4 (FastRouter regex/keyword)
         → Tier 5 (LLM Cascade: Haiku → Sonnet → Opus)
         → Fallback: clarification_needed (pergunta ao usuário)
```

### 2.3 RouteResult

```python
@dataclass
class RouteResult:
    domain_id: str            # Ex: "job_management", "sourcing"
    confidence: float         # 0.0 a 1.0
    source: str               # "memory", "redis_cache", "fast_router", "llm_cascade:haiku"
    matched_pattern: str      # Regex que deu match (Tier 4)
    needs_clarification: bool # True quando nenhum tier resolveu
    clarification_question: str
    clarification_options: List[str]  # 6 opções padrão
```

### 2.4 Mapeamento Agent → Domain

```python
AGENT_TYPE_TO_DOMAIN = {
    "job_planner": "job_management",
    "job_intake": "job_management",
    "sourcing": "sourcing",
    "cv_screening": "cv_screening",
    "screening": "cv_screening",
    "wsi_evaluator": "cv_screening",
    "interviewer": "interview_scheduling",
    "scheduling": "interview_scheduling",
    "analyst_feedback": "analytics",
    "analytics": "analytics",
    "communication": "communication",
    "ats_integrator": "ats_integration",
    "recruiter_assistant": "recruiter_assistant",
    "task_planner": "automation",
}
```

### 2.5 Opções de Clarificação (Fallback)

Quando nenhum tier resolve a intenção:
1. "Criar ou gerenciar uma vaga"
2. "Buscar ou avaliar candidatos"
3. "Acompanhar pipeline / triagem"
4. "Agendar entrevistas"
5. "Relatórios e analytics"
6. "Outra solicitação"

### 2.6 Métricas Prometheus

- `router_tier_hit_total` — contagem de hits por tier
- `router_latency_ms` — latência por tier
- `router_confidence_histogram` — distribuição de confiança por modelo

---

## 3. Orchestrator — Fluxo de Processamento

**Arquivo:** `lia-agent-system/app/orchestrator/orchestrator.py`

### 3.1 System Prompt Principal (LIA)

```
Você é LIA, a assistente inteligente de recrutamento da WeDOTalent.
Profissional de RH experiente, amigável e eficiente.
Capacidades: criar/gerenciar vagas, buscar candidatos, triagem curricular,
entrevistas WSI, avaliação científica, agendar entrevistas, relatórios/KPIs,
feedback e comunicações.

Regra anti-sycophancy: nunca confirme pedidos discriminatórios ou que violem compliance.
Apresente alternativas com dados quando necessário.
```

### 3.2 Fluxo `process_request()`

```
1. Sanitização da mensagem (sanitize_text)
2. Detecção de cancelamento/reinício
3. Recuperação de estado da conversa (last_agent, current_job, current_candidate)
4. Roteamento via CascadedRouter.route()
5. Verificação de cache (para intents cacheáveis)
6. Validação de política (PolicyEngine.validate_request)
7. Detecção de plano multi-step (PlanDetector)
   → Se detectado: PlanExecutor.execute() → resposta consolidada
8. Despacho para domínio (DomainRegistry → DomainWorkflow)
9. Verificação de resposta técnica → fallback para LLM se necessário
10. Cache da resposta (se intent cacheável)
11. Retorno ao frontend
```

### 3.3 Intents Cacheáveis

```python
_cacheable_intents = {
    "pipeline_stats", "job_status", "candidate_count", "stage_distribution",
    "funnel_analysis", "job_insights", "market_data", "salary_benchmark",
    "analytics", "recommendations", "skills_analysis", "candidate_search"
}
```

### 3.4 Detecção de Resposta Técnica

O Orchestrator detecta respostas "técnicas" que não devem ser exibidas ao usuário:
- "Keyword heuristic matched"
- "Ferramenta '"
- "Ação '"
- "encaminhada para o agente"
- "executada para ação"
- "Processado com sucesso."

Quando detectada, faz fallback para chamada direta ao LLM (Claude) com o system prompt da LIA.

### 3.5 Memória Conversacional

- `process_request_with_memory()` — versão com persistência em DB
- Histórico limitado a 20 mensagens por contexto LLM
- Resumo automático a cada N mensagens (`ROUTER_SUMMARY_EVERY_N_MESSAGES`)
- Suporte a `ConversationState` para manter estado entre turnos

---

## 4. Agentes ReAct — Registro e Capacidades

**Arquivo:** `lia-agent-system/libs/agents-core/lia_agents_core/react_agent_registry.py`

### 4.1 Arquitetura do Registry

- **Padrão:** Singleton (`ReactAgentRegistry`)
- **Armazenamento:** Classes (não instâncias) + configs
- **Instanciação:** Lazy via `get_agent()` ou session-safe via `AgentFactory.create_agent()`
- **AgentFactory:** Cria instância nova com `WorkingMemoryService` e `ReActObserver` isolados por sessão

### 4.2 Os 11 Agentes Registrados

| # | Domain            | Classe                      | Descrição                                          | Max Iter | Provider |
|---|-------------------|-----------------------------|-----------------------------------------------------|----------|----------|
| 1 | `wizard`          | `WizardReActAgent`          | Wizard de criação de vagas                          | 5        | Claude   |
| 2 | `pipeline`        | `PipelineReActAgent`        | Pipeline de triagem de CVs                          | 5        | Claude   |
| 3 | `sourcing`        | `SourcingReActAgent`        | Sourcing e busca de candidatos                      | 5        | Claude   |
| 4 | `talent`          | `TalentReActAgent`          | Assistente de talentos (funil)                      | 5        | Claude   |
| 5 | `jobs_management` | `JobsMgmtReActAgent`        | Gestão de vagas (portfólio)                         | 5        | Claude   |
| 6 | `kanban`          | `KanbanReActAgent`          | Assistente do kanban de recrutamento                | 5        | Claude   |
| 7 | `policy`          | `PolicyReActAgent`          | Configuração de políticas de contratação            | 5        | Claude   |
| 8 | `automation`      | `AutomationReActAgent`      | Decomposição de tarefas e planejamento de execução  | 6        | Claude   |
| 9 | `analytics`       | `AnalyticsReActAgent`       | Analytics, KPIs e previsões de contratação          | 6        | Claude   |
| 10| `communication`   | `CommunicationReActAgent`   | Comunicação multi-canal com conformidade LGPD       | 6        | Claude   |
| 11| `ats_integration` | `ATSIntegrationReActAgent`  | Integração bidirecional com plataformas ATS         | 6        | Claude   |

### 4.3 Herança e Mixins

Todos os agentes herdam de:
- `LangGraphReActBase` — base LangGraph para ciclo ReAct (Thought → Action → Observation)
- `EnhancedAgentMixin` — funcionalidades aprimoradas (ferramentas extras, guardrails)

### 4.4 AgentFactory — Instanciação Session-Safe

```python
agent = AgentFactory(registry).create_agent(
    domain="wizard",
    session_id="sess-123",
    company_id="company-abc",
    user_id="user-456"
)
# Cada instância recebe:
# - WorkingMemoryService isolada
# - ReActObserver com contexto de sessão
# - _session_context com IDs
```

---

## 5. System Prompts por Agente

### 5.1 Wizard Agent (job_management)

**Arquivo:** `app/domains/job_management/agents/wizard_react_agent.py`
**Responsabilidade:** Criação guiada de vagas com sugestões inteligentes
**Prompt principal:**
- Persona LIA como consultora de RH
- Capacidade de sugerir requisitos, skills, faixas salariais
- FairnessGuard integrado (verifica bias em descrições de vaga)
- Fluxo: coleta dados → valida campos → gera JD enriquecida → salva rascunho

### 5.2 Pipeline Agent (cv_screening)

**Arquivo:** `app/domains/cv_screening/agents/pipeline_react_agent.py`
**Responsabilidade:** Triagem de CVs e movimentação no pipeline
**Prompt principal:**
- Escopo IN (10 capacidades): consultar dados do candidato, scores WSI, triagem, atualizar dados, preferências de execução, sugestões baseadas em padrões
- Escopo OUT (7 restrições): não pode buscar outros candidatos, comparar vagas, configurar pipeline, acessar analytics gerais
- Verificação de fairness em motivos de rejeição
- Personalização de comunicação por tom/idioma

### 5.3 Sourcing Agent

**Arquivo:** `app/domains/sourcing/agents/sourcing_react_agent.py`
**Responsabilidade:** Busca e atração de candidatos
**Capacidades:** Busca local (PostgreSQL) + busca externa (Pearch AI), scoring de match, análise de perfil

### 5.4 Talent Agent (recruiter_assistant)

**Arquivo:** `app/domains/recruiter_assistant/agents/talent_react_agent.py`
**Prompt:** `app/domains/recruiter_assistant/prompts/talent_assistant_prompts.py`
**Responsabilidade:** Assistência no funil de talentos
**FairnessGuard:** Integrado para verificação de bias

### 5.5 Jobs Management Agent (recruiter_assistant)

**Arquivo:** `app/domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py`
**Prompt:** `app/domains/recruiter_assistant/prompts/jobs_management_prompts.py`
**Responsabilidade:** Gestão do portfólio de vagas
**FairnessGuard:** Integrado

### 5.6 Kanban Agent (recruiter_assistant)

**Arquivo:** `app/domains/recruiter_assistant/agents/kanban_react_agent.py`
**Prompt:** `app/domains/recruiter_assistant/prompts/kanban_assistant_prompts.py`
**Responsabilidade:** Análise e operações no kanban de recrutamento
**Extras:** GUARDRAIL_TOOLS integrados, FairnessGuard

### 5.7 Policy Agent (hiring_policy)

**Arquivo:** `app/domains/hiring_policy/agents/policy_react_agent.py`
**Prompt:** `app/domains/hiring_policy/agents/policy_system_prompt.py`
**Responsabilidade:** Configuração de políticas de contratação
**Capacidades:** CRUD de políticas, validação de compliance, regras de aprovação

### 5.8 Automation Agent

**Arquivo:** `app/domains/automation/agents/automation_react_agent.py`
**Prompt:** `app/domains/automation/agents/automation_system_prompt.py`
**Responsabilidade:** Decomposição de tarefas complexas de recrutamento
**Capacidades detalhadas:**
- Decomposição de tarefas em subtarefas executáveis com IA
- Priorização inteligente (urgência × impacto × criticidade)
- DAG de dependências (grafos acíclicos direcionados)
- Planos de execução com paralelismo
- Identificação de próximas tarefas prontas
- Agentes delegáveis: `job_planner`, `sourcing`, `cv_screening`, `interviewer`, `wsi_evaluator`, `scheduling`, `analyst_feedback`

### 5.9 Analytics Agent

**Arquivo:** `app/domains/analytics/agents/analytics_react_agent.py`
**Prompt:** `app/domains/analytics/agents/analytics_system_prompt.py`
**Responsabilidade:** Analytics, KPIs e previsões de contratação

### 5.10 Communication Agent

**Arquivo:** `app/domains/communication/agents/communication_react_agent.py`
**Responsabilidade:** Comunicação multi-canal com conformidade LGPD
**Canais:** Email, WhatsApp, Teams

### 5.11 ATS Integration Agent

**Arquivo:** `app/domains/ats_integration/agents/ats_integration_react_agent.py`
**Responsabilidade:** Integração bidirecional com plataformas ATS
**Provedores suportados:**
- **Gupy:** Plataforma BR líder; mapeamento de fase, observações, dados básicos
- **Pandapé:** Plataforma BR; score WSI, pretensão salarial, parecer RH
- **Merge:** Conector multi-ATS via API unificada; campos customizáveis
- **StackOne:** Conector multi-ATS internacional; custom_fields

**Fluxos:**
- Push (WeDOTalent → ATS): validar campos → sincronizar → confirmar
- Pull (ATS → WeDOTalent): importar → manter SSOT no WeDOTalent

**Princípios:**
- Multi-tenant obrigatório (`company_id`)
- LGPD: dados sensíveis NÃO sincronizados com ATS
- Idempotência em operações de sync
- Auditoria completa (SOX/ISO 27001)

### 5.12 Prompt Anti-Sycophancy (transversal)

A regra anti-sycophancy está presente em todos os agentes, porém implementada de duas formas distintas:
- **Via bloco compartilhado** `ANTI_SYCOPHANCY_OPERATIONAL` (importado explicitamente por: Automation, Communication, Analytics, ATS Integration)
- **Via regra equivalente embutida no prompt** (Wizard, Pipeline, Jobs Management, Kanban, Policy, Talent, Sourcing)
- **Regra comum:** Nunca confirmar pedidos discriminatórios; apresentar alternativas com dados

---

## 6. Ferramentas (Tools) por Domínio

### 6.1 Analytics Tools (19 ferramentas)

| Ferramenta                | Descrição                                    |
|---------------------------|----------------------------------------------|
| `get_pipeline_stats`      | Estatísticas do pipeline                     |
| `get_vacancy_funnel`      | Funil da vaga                                |
| `compare_candidates`      | Comparação de candidatos                     |
| `get_activity_summary`    | Resumo de atividades                         |
| `get_pending_actions`     | Ações pendentes                              |
| `get_recruiter_metrics`   | Métricas do recrutador                       |
| `get_velocity_metrics`    | Métricas de velocidade                       |
| `get_efficiency_metrics`  | Métricas de eficiência                       |
| `get_comparative_metrics` | Métricas comparativas                        |
| `get_workload_distribution` | Distribuição de carga de trabalho          |
| `get_bottleneck_analysis` | Análise de gargalos                          |
| `get_stakeholder_metrics` | Métricas de stakeholders                     |
| `get_hiring_quality`      | Qualidade de contratação                     |
| `get_prediction_metrics`  | Métricas preditivas                          |
| `get_cost_metrics`        | Métricas de custo                            |
| `get_trends`              | Tendências                                   |
| `get_ml_predictions`      | Previsões ML                                 |
| `get_conversion_patterns` | Padrões de conversão                         |
| `get_smart_alerts`        | Alertas inteligentes                         |

### 6.2 Communication Tools (5 ferramentas)

| Ferramenta             | Descrição                                   |
|------------------------|---------------------------------------------|
| `send_email`           | Envio de email individual                   |
| `send_whatsapp`        | Envio de WhatsApp                           |
| `schedule_interview`   | Agendamento de entrevista                   |
| `send_bulk_email`      | Envio de email em massa                     |
| `send_feedback`        | Envio de feedback                           |

### 6.3 CV Screening / Pipeline Tools (8 ferramentas)

| Ferramenta                    | Descrição                                 |
|-------------------------------|-------------------------------------------|
| `update_candidate_stage`      | Mover candidato entre etapas              |
| `add_candidate_to_vacancy`    | Adicionar candidato à vaga                |
| `reject_candidate`            | Rejeitar candidato                        |
| `shortlist_candidate`         | Shortlistar candidato                     |
| `bulk_update_candidates_stage`| Movimentação em massa                     |
| `add_to_list`                 | Adicionar à lista                         |
| `wsi_screening`               | Triagem WSI comportamental                |
| `hide_candidate`              | Ocultar candidato                         |

### 6.4 Job Management / Wizard Tools (9 ferramentas)

| Ferramenta                | Descrição                                    |
|---------------------------|----------------------------------------------|
| `search_salary_benchmark` | Benchmark salarial                           |
| `validate_job_fields`     | Validação de campos da vaga                  |
| `get_job_suggestions`     | Sugestões inteligentes para a vaga           |
| `save_job_draft`          | Salvar rascunho de vaga                      |
| `get_company_config`      | Configuração da empresa                      |
| `get_intelligent_salary`  | Sugestão salarial inteligente                |
| `get_intelligent_skills`  | Sugestão de skills inteligente               |
| `capture_wizard_feedback` | Captura de feedback do wizard                |
| `generate_enriched_jd`    | Geração de JD enriquecida                    |

### 6.5 Sourcing Tools (9 ferramentas)

| Ferramenta                | Descrição                                    |
|---------------------------|----------------------------------------------|
| `search_candidates`       | Busca de candidatos (local + Pearch)         |
| `get_candidate_details`   | Detalhes do candidato                        |
| `get_candidate_stats`     | Estatísticas do candidato                    |
| `get_candidate_history`   | Histórico do candidato                       |
| `get_talent_quality`      | Qualidade do talento                         |
| `get_talent_engagement`   | Engajamento do talento                       |
| `get_talent_availability` | Disponibilidade do talento                   |
| `get_diversity_metrics`   | Métricas de diversidade                      |
| `get_market_benchmarks`   | Benchmarks de mercado                        |

### 6.6 Recruiter Assistant / Pipeline Tools

| Ferramenta                | Descrição                                    |
|---------------------------|----------------------------------------------|
| `create_pipeline_stage`   | Criação de etapa no pipeline                 |

### 6.7 Automation, ATS Integration, Policy Tools

Esses domínios possuem módulos `__init__.py` com funções `get_*_tools()` que retornam ferramentas específicas (implementação via `StructuredTool.from_function`).

---

## 7. Templates de Resposta, Análises e Componentes de UI

### 7.1 RubricEvaluationModal (Avaliação por Rubrica)

**Arquivo:** `plataforma-lia/src/components/rubric-evaluation-modal.tsx`
**Ativação:** Via botão na interface de candidatos (Float Chat ou Kanban)
**Execução:** IA (Claude via agente Pipeline) gera avaliação; frontend renderiza

Estrutura de dados da avaliação:

```typescript
interface RubricEvaluationData {
  candidateId: string
  candidateName: string
  jobTitle: string
  overallScore: number      // Score geral 0-100
  overallGrade: string      // "A+", "A", "B+", etc.
  dimensions: {
    name: string            // Ex: "Experiência Técnica"
    score: number           // 0-100
    weight: number          // Peso da dimensão
    criteria: {
      name: string          // Ex: "Proficiência em React"
      score: number
      maxScore: number
      evidence: string      // Evidência do CV/entrevista
    }[]
  }[]
  strengths: string[]       // Pontos fortes
  concerns: string[]        // Pontos de atenção
  recommendation: string    // Recomendação final
  wsiData?: {               // Dados WSI (se disponível)
    overallScore: number
    competencies: {
      name: string
      score: number
      level: string
    }[]
  }
}
```

### 7.2 ProactiveInsightCard (Análise Proativa de Busca)

**Arquivo:** `plataforma-lia/src/components/proactive-insight-card.tsx`
**Ativação:** Exibido automaticamente após busca de candidatos em `candidates-page.tsx`
**Execução:** Backend gera `SearchAnalytics` via endpoint `/analyze`; frontend renderiza card expansível

**Input → Processing → Output:**
- **Input:** Query de busca + resultados de candidatos
- **Processing:** Backend analisa distribuições, contatos, skills, empresas, senioridade (processamento local, sem LLM)
- **Output:** Card com resumo, alertas, ações sugeridas

```typescript
interface SearchAnalytics {
  summary: {
    total_candidates: number
    local_count: number        // Candidatos do banco local
    global_count: number       // Candidatos do Pearch AI
    average_lia_score: number  // Score médio de match
  }
  contact_quality: {
    with_valid_phone: number
    with_valid_email: number
    with_linkedin: number
    phone_percentage: number
    email_percentage: number
  }
  distributions: {
    seniority: Record<string, number>   // Ex: {"Senior": 45, "Pleno": 30}
    location: Record<string, number>    // Ex: {"São Paulo": 60, "Remoto": 20}
    work_model: Record<string, number>  // Ex: {"Híbrido": 50, "Remoto": 30}
  }
  top_skills: Array<{ skill: string; count: number; percentage: number }>
  top_companies: Array<{ company: string; count: number }>
  experience_range: { min: number; max: number; average: number; median: number }
  alerts: Array<{ type: 'warning' | 'info' | 'success'; message: string }>
  suggested_actions: Array<{
    id: string; label: string; icon: string;
    description: string; action_type: string
  }>
  narrative?: string   // Resumo em linguagem natural (gerado por IA quando disponível)
}
```

### 7.3 SaturationBadge (Indicador de Saturação de Pipeline)

**Arquivo:** `plataforma-lia/src/components/kanban/components/SaturationBadge.tsx`
**Ativação:** Exibido automaticamente no header do kanban de cada vaga
**Execução:** Processamento local (backend calcula thresholds); sem LLM
**Endpoint:** `GET /api/backend-proxy/job-vacancies/{jobId}/saturation-status/`

**Input → Processing → Output:**
- **Input:** `jobId`
- **Processing:** Backend calcula `approved_count / saturation_threshold` por canal (orgânico vs sourcing)
- **Output:** Badge colorido (verde/amarelo/vermelho) com popover de detalhes

```typescript
interface SaturationStatus {
  job_id: string
  approved_count: number
  saturation_threshold: number
  is_saturated: boolean
  slots_remaining: number
  recommendation: "continue_screening" | "pause_screening"
  saturation_percentage: number
  queued_count: number
  last_screened_at: string | null
  saturation_disabled_until: string | null
  counts_by_channel: { web: number; whatsapp: number; sourcing: number; ats: number }
  organic: { count: number; threshold: number; is_saturated: boolean; slots_remaining: number; percentage: number }
  sourcing: { count: number; threshold: number; is_saturated: boolean; slots_remaining: number; percentage: number }
  unlock_increment: number   // Incremento ao desbloquear threshold
  unlock_hours: number       // Horas de desativação temporária
}
```

**Ações do usuário:**
- `increase_threshold` → `POST /job-vacancies/{jobId}/unlock-pipeline/` (aumenta threshold)
- `disable_temporarily` → `POST /job-vacancies/{jobId}/unlock-pipeline/` (desativa por N horas)

### 7.4 JobReportModal (Relatório Completo da Vaga)

**Arquivo:** `plataforma-lia/src/components/job-report-modal.tsx`
**Ativação:** Via botão em `jobs-page.tsx` e `job-kanban-page.tsx`
**Execução:** Processamento local (dados mockados no frontend atualmente)
**Exportação:** PDF via `html2canvas` + `jsPDF`

**Seções selecionáveis (7):**
1. **Overview** — Informações gerais da vaga
2. **Funnel** — Métricas de funil (total candidatos, screening, interview, final, hired, taxa conversão, time-to-hire, custo)
3. **Candidates** — Top candidatos com score, status e fit
4. **Timeline** — Cronograma com eventos (vaga publicada → triagem → entrevistas → decisão → contratação)
5. **Costs** — Orçamento (total, gasto, restante, breakdown por categoria)
6. **Performance** — Channel performance (LinkedIn, Website, LIA Database, Referral) com qualidade e custo
7. **Recommendations** — Métricas de qualidade (NPS, satisfação candidato/gestor, benchmarks mercado)

### 7.5 Kanban Command Templates (18 Comandos)

**Arquivo:** `lia-agent-system/app/domains/recruiter_assistant/prompts/kanban_assistant_prompts.py`
**Execução:** IA (Claude via agente Kanban); cada comando tem prompt template com formato JSON obrigatório

| # | Comando                 | Descrição                                          | Tipo        |
|---|-------------------------|----------------------------------------------------|-------------|
| 1 | `rankear_candidatos`    | Ranking de candidatos por fit com a vaga           | Análise IA  |
| 2 | `performance_funil`     | Análise de métricas do pipeline                    | Análise IA  |
| 3 | `gargalos_processo`     | Identificação de gargalos no processo              | Análise IA  |
| 4 | `comparar_candidatos`   | Comparação detalhada entre candidatos              | Análise IA  |
| 5 | `resumir_perfil`        | Resumo do perfil do candidato                      | Análise IA  |
| 6 | `candidatos_ativos`     | Lista de candidatos ativos na vaga                 | Query local |
| 7 | `taxa_conversao`        | Taxa de conversão por etapa                        | Query local |
| 8 | `tempo_medio`           | Tempo médio por etapa do pipeline                  | Query local |
| 9 | `candidatos_parados`    | Candidatos sem movimentação recente                | Query local |
| 10| `top_candidatos`        | Top candidatos por score/fit                       | Análise IA  |
| 11| `mover_candidato`       | Mover candidato entre etapas                       | Ação        |
| 12| `enviar_email`          | Enviar email para candidato                        | Ação        |
| 13| `disparar_triagem`      | Iniciar triagem WSI                                | Ação        |
| 14| `agendar_entrevista`    | Agendar entrevista                                 | Ação        |
| 15| `solicitar_dados`       | Solicitar dados adicionais do candidato            | Ação        |
| 16| `analisar_perfil`       | Análise aprofundada do perfil                      | Análise IA  |
| 17| `aprovar_candidato`     | Aprovar candidato para próxima etapa               | Ação        |
| 18| `analise_geral`         | Análise geral do pipeline (fallback default)       | Análise IA  |

**Exemplo de template (rankear_candidatos):**
```json
{
  "ranking": [
    {
      "posicao": 1,
      "candidato_id": "id",
      "candidato_nome": "nome",
      "score_fit": 95,
      "principais_forcas": ["força 1", "força 2"],
      "principais_gaps": ["gap 1"],
      "justificativa": "Breve justificativa do ranking"
    }
  ],
  "insights": "Observações gerais sobre o pool de candidatos",
  "recomendacao": "Próximos passos recomendados"
}
```

### 7.6 Job Analytics Command Templates (8 Comandos)

**Arquivo:** `lia-agent-system/app/domains/analytics/services/job_analytics_prompt_service.py`
**Execução:** IA (via agentes especializados por comando)

| # | Comando                  | Agente Executor         | Contexto Requerido | Descrição                                |
|---|--------------------------|-------------------------|--------------------|------------------------------------------|
| 1 | `funnel_analysis`        | AnalistaFeedbackAgent   | `job_id`           | Análise de funil: candidatos por etapa, taxa de conversão, gargalos |
| 2 | `comparative_analysis`   | AnalistaFeedbackAgent   | `job_ids`          | Comparação de métricas entre vagas       |
| 3 | `bottleneck_detection`   | AnalistaFeedbackAgent   | `job_id`           | Detecção de gargalos: tempo de espera, candidatos parados |
| 4 | `time_to_fill_prediction`| AnalistaFeedbackAgent   | `job_id`           | Previsão de fechamento baseada em dados históricos |
| 5 | `candidate_quality_score`| AvaliadorWSIAgent       | `job_id`           | Score de qualidade: fit técnico, cultural, diversidade |
| 6 | `sourcing_effectiveness` | SourcingAgent           | `job_id`           | Efetividade de sourcing: canais, conversão, custo |
| 7 | `weekly_summary`         | AnalistaFeedbackAgent   | (nenhum)           | Resumo semanal: novos candidatos, movimentações, entrevistas |
| 8 | `salary_benchmark`       | JobIntakeAgent          | `job_id`           | Benchmark salarial vs mercado            |

### 7.7 Templates de Comunicação

**Arquivo:** `lia-agent-system/app/domains/communication/tools/communication_tools.py`
**Execução:** IA (Claude via Communication Agent) gera conteúdo; envio via serviço de email/WhatsApp

| Template                    | Canais        | Input                                  | Output                           |
|-----------------------------|---------------|----------------------------------------|----------------------------------|
| Email de feedback positivo  | Email         | candidato_id, vaga, decisão           | Email personalizado com próximos passos |
| Email de feedback negativo  | Email         | candidato_id, vaga, motivo            | Email gentil com encorajamento   |
| Agendamento de entrevista   | Email, Teams  | candidato_id, data, hora, formato     | Convite com link/local           |
| Bulk email                  | Email         | lista candidatos, template            | Emails em massa personalizados   |
| Follow-up WhatsApp          | WhatsApp      | candidato_id, contexto                | Mensagem curta e profissional    |
| Notificação de vaga criada  | Email, Teams  | vaga completa (ver 7.8)              | Notificação para recrutador/gestor |

### 7.8 Job Created Notification

**Arquivo:** `plataforma-lia/src/services/lia-api.ts`
**Execução:** Backend local (sem LLM); disparo via serviço de notificação

```typescript
interface JobCreatedNotificationRequest {
  job_id, job_title, department, location, work_model,
  seniority_level, job_description,
  technical_requirements: { name, level, required }[],
  behavioral_competencies: { name, weight }[],
  languages: { name, level }[],
  salary_range: { min, max, currency },
  benefits: string[],
  deadline_screening, deadline_shortlist, deadline_closing,
  interview_stages: { stageName, order, sla }[],
  publishing_platforms: { linkedin, indeed, website },
  urgency_level, is_confidential, is_affirmative,
  recruiter_email, recruiter_name, manager_email, manager_name,
  channels: ('email' | 'teams')[]
}
```

### 7.9 Calibration Session (Calibração de Candidatos)

**Arquivo:** `plataforma-lia/src/services/lia-api.ts`
**Execução:** Backend (Pearch AI + scoring local); sem agente ReAct dedicado
**Endpoints:** `POST /calibration/start`, `POST /calibration/feedback`, `GET /calibration/status`

**Input → Processing → Output:**
- **Input:** `job_vacancy_id`, `job_description`, `technical_skills[]`, `behavioral_competencies[]`
- **Processing:** Pearch AI busca candidatos → scoring de match → montagem de perfis calibrados
- **Output:** Lista de `CalibrationCandidate` com scores, experiências, skills mapeados

```typescript
interface CalibrationCandidate {
  id, name, photoUrl, linkedinUrl,
  currentRole, currentCompany, location, education,
  highlights: { icon, label, value }[],
  experiences: { company, role, period, duration, skills[] }[],
  educationHistory: { institution, degree, field, period }[],
  skillMap: { category, skills[] }[],
  languages: string[],
  matchCriteria: { criteria, met, score }[],
  overallScore: number,
  averageTenure, currentTenure
}
```

**Fluxo de feedback:**
1. Recrutador avalia candidato (aprova/rejeita com `lia_score` e `feedback_reason`)
2. Sistema atualiza `CalibrationStatusResponse` (`approved_count`, `rejected_count`, `is_complete`)
3. Candidatos aprovados podem ser adicionados ao pipeline via `addCandidatesToPipeline()`

---

## 8. Sistema Preditivo e Analytics

### 8.1 Job Analytics Prompt Service

**Arquivo:** `lia-agent-system/app/domains/analytics/services/job_analytics_prompt_service.py`
**Execução:** IA (Claude via agentes especializados) ou processamento local conforme o comando

**Fluxo de execução:**
```
1. Orchestrator.process_analytics_request(command, context)
2. Se command ∈ COMMAND_TEMPLATES → execute_command(command, context)
   Senão → analyze_natural_query(command, context) [NLU via LLM]
3. Retorno estruturado: { command, agent_used, response, data, charts, suggestions, metadata }
```

**8 Command Templates** — ver seção 7.6 para lista completa com agentes executores.

### 8.2 Ferramentas Preditivas (Analytics Agent)

**Execução:** Todas via IA (Claude); dados alimentados por queries ao PostgreSQL

| Ferramenta              | Input                      | Processing                              | Output                                    |
|-------------------------|----------------------------|-----------------------------------------|-------------------------------------------|
| `get_prediction_metrics`| `job_id`, `time_range`    | Query histórico + modelo de regressão   | Previsões de hiring (prazo, probabilidade)|
| `get_ml_predictions`    | `job_id`, `model_type`    | Modelo ML treinado em dados da empresa  | Previsões com confidence intervals        |
| `get_conversion_patterns`| `job_id` ou `company_id` | Análise de padrões no funil             | Taxas de conversão por etapa/fonte        |
| `get_smart_alerts`      | `company_id`, `threshold` | Detecção de anomalias e tendências      | Lista de alertas com severidade           |
| `get_trends`            | `metric`, `time_range`    | Séries temporais de métricas            | Tendências com visualização              |
| `get_bottleneck_analysis`| `job_id`                 | Análise de tempos por etapa             | Gargalos identificados com recomendações |

### 8.3 Serviços de Inteligência Operacional

**Arquivos:** `lia-agent-system/app/services/predictive_analytics_service.py`, `search_analytics_service.py`, `wizard_analytics_service.py`, `learning_analytics_service.py`

| # | Serviço                       | Tipo de Execução | Endpoint/Surfacing UI              | Dados Utilizados                     |
|---|-------------------------------|------------------|------------------------------------|--------------------------------------|
| 1 | Pipeline Velocity Engine      | Local (query)    | Kanban page, Analytics dashboard   | Timestamps de movimentação por etapa |
| 2 | Zero-Touch Scheduling         | IA + Local       | Communication Agent, Calendar API  | Disponibilidade, preferências, SLAs  |
| 3 | Silver Medalists              | IA (matching)    | Sourcing Agent, ProactiveInsightCard| Histórico de candidatos rejeitados   |
| 4 | Recruiter Intelligence        | Local (metrics)  | Analytics dashboard                | Volume, velocidade, qualidade por recruiter |
| 5 | Early Warning Score (EWS)     | IA (anomaly det.)| SaturationBadge, SmartAlerts       | Pipeline metrics, tempos, saturação  |
| 6 | Journey Intelligence          | Local + IA       | Kanban page                        | Touchpoints do candidato no pipeline |
| 7 | Recruiter Perf. Benchmark     | Local (metrics)  | Analytics dashboard                | KPIs comparativos entre recrutadores |
| 8 | Pipeline Prediction           | IA (ML model)    | JobReportModal, Analytics          | Dados históricos de vagas similares  |

### 8.4 Response Cache Service

**Arquivo:** `lia-agent-system/app/services/response_cache_service.py`
**Execução:** Local (sem LLM)

- Cache de respostas para intents analíticas recorrentes
- `generate_cache_key()` baseado em intent + contexto + mensagem + company_id
- Invalidação por entidade: `invalidate_for_job()`, `invalidate_for_candidate()`, `invalidate_for_company()`
- Invalidação por padrão regex: `invalidate_by_pattern()`
- Intents cacheáveis: `pipeline_stats`, `job_status`, `candidate_count`, `stage_distribution`, `funnel_analysis`, `job_insights`, `market_data`, `salary_benchmark`, `analytics`, `recommendations`, `skills_analysis`, `candidate_search`

---

## 9. Limitações e Dívidas Técnicas

### 9.1 Limitações Conhecidas

1. **handleOpenRubricAnalysis orphaned** — Função em `candidates-page.tsx` sem call sites (modal ainda renderiza mas a função que o abre não é chamada)
2. **Cache in-process (Tier 1)** — Não é distribuído entre múltiplos workers; LRU simples com eviction FIFO
3. **VectorSemanticCache** — Inicialização graciosa (nunca falha), mas pode ficar indisponível silenciosamente
4. **Max iterations** — Agentes limitados a 5-6 iterações ReAct, o que pode truncar tarefas complexas
5. **Memória conversacional** — Limitada a 20 mensagens por contexto LLM; resumo automático pode perder detalhes
6. **Scope filtering** — Ferramentas filtradas por escopo no frontend, mas o backend não valida escopo no nível de execução de tool
7. **AgentFactory vs get_agent** — Dois padrões coexistem: `get_agent()` (cacheado, não session-safe) e `AgentFactory.create_agent()` (session-safe); código legado pode usar o primeiro

### 9.2 Dívidas Técnicas

1. **Detecção de resposta técnica** — Baseada em string matching (`_TECHNICAL_PATTERNS`); frágil e pode falhar com novas mensagens
2. **IntentRouter legado** — Coexiste com LLM Cascade como fallback; duplicação de lógica
3. **Mapeamento agent_type → domain** — Hardcoded em `AGENT_TYPE_TO_DOMAIN`; sem registro dinâmico
4. **PolicyEngine** — Validação de políticas é síncrona (`await`) mas a engine usa DB service que pode ser None
5. **PlanDetector** — Detecção de plano multi-step é não-blocking (falha silenciosa via try/except)
6. **Calibration flow** — Implementado no frontend (`lia-api.ts`) mas sem agente ReAct dedicado
7. **Pearch AI** — Busca externa com créditos; sem circuit breaker explícito para falhas de API
8. **Notificações** — `JobCreatedNotificationRequest` suporta email + Teams, mas não WhatsApp

### 9.3 Pontos de Atenção de Compliance

1. **Anti-sycophancy** — Regra presente em todos os agentes (via bloco compartilhado ou equivalente no prompt), porém sem guardrail automatizado que valide enforcement em runtime
2. **FairnessGuard** — Integrado em Wizard, Talent, Jobs Management, Kanban; ausente em Analytics, Automation, ATS Integration
3. **LGPD em ATS** — Dados sensíveis não sincronizados, mas a lista de campos sensíveis é hardcoded
4. **Auditoria** — SOX/ISO 27001 mencionados no prompt do ATS Agent, mas sem implementação de audit trail centralizado

---

## 10. Oportunidades de Evolução

### 10.1 Curto Prazo (Quick Wins)

1. **Ativar FairnessGuard** em todos os 11 agentes (atualmente só em 4)
2. **Remover IntentRouter legado** — CascadedRouter já cobre todos os cenários
3. **Validar escopo de tools no backend** — Adicionar middleware que valida `PromptScope` antes de executar tool
4. **Circuit breaker para Pearch AI** — Implementar fallback automático para busca local

### 10.2 Médio Prazo

1. **Agente de Calibração dedicado** — Mover lógica de calibração do frontend para um ReAct Agent
2. **Cache distribuído (Tier 1)** — Migrar de LRU in-process para Redis com TTL configurável
3. **Streaming de respostas** — WebSocket já existe (Sprint J), mas agentes ReAct não streamam pensamentos intermediários
4. **Audit trail centralizado** — Implementar logging estruturado para todas as operações de sync ATS

### 10.3 Longo Prazo

1. **Registro dinâmico de agentes** — Permitir registro via YAML/JSON sem deploy
2. **Multi-model por agente** — Permitir que cada agente use modelo diferente (GPT-4, Gemini, Claude) baseado em custo/performance
3. **Feedback loop** — Usar feedback de calibração para re-treinar scoring de match
4. **RAG por domínio** — Embeddings específicos para cada domínio de agente (vagas, candidatos, políticas)

---

## Anexo A: Arquivos-Fonte Auditados

| Arquivo | Descrição |
|---------|-----------|
| `plataforma-lia/src/components/pages/candidates-page.tsx` | Float Chat + UnifiedBulkActionsBar + ProactiveInsightCard |
| `plataforma-lia/src/components/pages/job-kanban-page.tsx` | Kanban Chat + Pipeline + SaturationBadge |
| `plataforma-lia/src/components/pages/chat-page.tsx` | Chat Full dedicado |
| `plataforma-lia/src/components/rubric-evaluation-modal.tsx` | Modal de avaliação por rubrica |
| `plataforma-lia/src/components/proactive-insight-card.tsx` | Card de insights proativos de busca |
| `plataforma-lia/src/components/kanban/components/SaturationBadge.tsx` | Badge de saturação do pipeline |
| `plataforma-lia/src/components/job-report-modal.tsx` | Modal de relatório da vaga (PDF) |
| `plataforma-lia/src/components/ui/unified-bulk-actions-bar.tsx` | Barra de ações bulk (9 ações) |
| `plataforma-lia/src/services/lia-api.ts` | Client API (4943 linhas) |
| `plataforma-lia/src/lib/api/kanban-assistant.ts` | API helpers para chats orquestrados |
| `lia-agent-system/app/orchestrator/orchestrator.py` | Orchestrator principal |
| `lia-agent-system/app/orchestrator/cascaded_router.py` | CascadedRouter 6 tiers |
| `lia-agent-system/libs/agents-core/lia_agents_core/react_agent_registry.py` | Registry + AgentFactory |
| `lia-agent-system/app/domains/*/agents/*react_agent.py` | 11 agentes ReAct |
| `lia-agent-system/app/domains/*/agents/*system_prompt*.py` | System prompts por domínio |
| `lia-agent-system/app/domains/recruiter_assistant/prompts/*.py` | Prompts + 18 Kanban Command Templates |
| `lia-agent-system/app/domains/analytics/services/job_analytics_prompt_service.py` | 8 Analytics Command Templates |
| `lia-agent-system/app/domains/*/tools/*.py` | Ferramentas por domínio |
| `lia-agent-system/app/tools/scope_config.py` | Configuração de escopo de tools |
| `lia-agent-system/app/services/predictive_analytics_service.py` | Serviço preditivo |
| `lia-agent-system/app/services/search_analytics_service.py` | Analytics de busca |
| `docs/analises/MAPA_INTELIGENCIA_LIA_COMPLETO.md` | Documento de referência existente |

---

*Documento gerado por auditoria automatizada do código-fonte em 13/03/2026.*
