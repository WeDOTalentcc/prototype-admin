# Relatório Completo de Capacidades e Prompts — LIA (WeDOTalent)
**Versão:** 2.0 — 13/03/2026
**Fonte:** Auditoria direta do código-fonte (`lia-agent-system/` + `plataforma-lia/`)
**Propósito:** Mapeamento técnico exaustivo de toda a arquitetura de prompts, interação entre chats, agentes ReAct, capacidades, templates de resposta, análises, sistema preditivo, resiliência, compliance, governança, aprendizado, limitações, dívidas técnicas e oportunidades de evolução.

**Metodologia:** Auditoria de 13/03/2026 via leitura direta de arquivos-fonte. Verificados: endpoints, escopos (`scope_config.py`), registros de agentes (`react_agent_registry.py`), ferramentas, templates de prompt e serviços. Exemplos de resposta marcados como "ilustrativo" são sintéticos baseados nos templates/schemas do código; os demais refletem schemas e formatos reais. Recomenda-se revisão mensal para atualizar contagens de tools e referências de linha.

---

## Sumário

1. [Arquitetura de Prompts e Interação entre Chats](#1-arquitetura-de-prompts-e-interação-entre-chats)
2. [Os 11 Agentes ReAct](#2-os-11-agentes-react)
3. [Capacidades Detalhadas](#3-capacidades-detalhadas)
4. [Templates de Resposta do Chat](#4-templates-de-resposta-do-chat)
5. [Análises e Relatórios](#5-análises-e-relatórios)
6. [Sistema Preditivo e Insights](#6-sistema-preditivo-e-insights)
7. [Quick Actions e Ações Bulk](#7-quick-actions-e-ações-bulk)
8. [Resiliência e Circuit Breakers](#8-resiliência-e-circuit-breakers)
9. [Gestão de Custos e Token Tracking](#9-gestão-de-custos-e-token-tracking)
10. [ConfidencePolicyService — Autonomia de Ações](#10-confidencepolicyservice--autonomia-de-ações)
11. [Governança de Agentes](#11-governança-de-agentes)
12. [Aprendizado Contínuo e Memória](#12-aprendizado-contínuo-e-memória)
13. [FairnessGuard — 3 Camadas de Proteção Anti-Viés](#13-fairnessguard--3-camadas-de-proteção-anti-viés)
14. [Pre-Qualification Pipeline](#14-pre-qualification-pipeline)
15. [Personalized Feedback Service](#15-personalized-feedback-service)
16. [LGPD — Proteção de Dados Pessoais](#16-lgpd--proteção-de-dados-pessoais)
17. [EU AI Act — Conformidade com IA de Alto Risco](#17-eu-ai-act--conformidade-com-ia-de-alto-risco)
18. [Compliance Multi-Framework](#18-compliance-multi-framework)
19. [Framework de Teste de Viés — Bias Audit Service](#19-framework-de-teste-de-viés--bias-audit-service)
20. [Model Drift e Monitoramento Contínuo](#20-model-drift-e-monitoramento-contínuo)
21. [Taxonomia de Incidentes](#21-taxonomia-de-incidentes)
22. [Production Readiness](#22-production-readiness)
23. [Limitações, Dívidas Técnicas e Funcionalidades Incompletas](#23-limitações-dívidas-técnicas-e-funcionalidades-incompletas)
24. [Oportunidades e Capacidades Ausentes](#24-oportunidades-e-capacidades-ausentes)
25. [Referência de Arquivos](#25-referência-de-arquivos)

---

## 1. Arquitetura de Prompts e Interação entre Chats

### 1.1 Os 3 Níveis de Chat

A plataforma possui **3 camadas de chat** com contextos, escopos e lógica de decisão distintos:

#### 1.1.1 Float Chat (candidates-page.tsx)

- **Localização:** `plataforma-lia/src/components/pages/candidates-page.tsx`
- **Contexto:** Página de funil de talentos (listagem geral de candidatos)
- **Escopo de ferramentas:** `TALENT_FUNNEL` — `scope_config.py` filtra ferramentas para:
  - **Query (11):** `search_candidates`, `get_candidate_details`, `get_candidate_stats`, `compare_candidates`, `get_talent_quality`, `get_talent_engagement`, `get_talent_availability`, `get_diversity_metrics`, `get_candidate_history`, `get_ml_predictions`, `get_conversion_patterns`
  - **Action (9):** `add_candidate_to_vacancy`, `reject_candidate`, `shortlist_candidate`, `add_to_list`, `hide_candidate`, `send_email`, `send_whatsapp`, `send_bulk_email`, `export_candidates`
- **Endpoint API:** `callOrchestratedTalentChat()` → `POST /api/backend-proxy/orchestrator/talent-chat`
- **Backend:** `app/api/v1/orchestrated_talent_chat.py` (v3.0 — ActionExecutor + PendingActionState + closed-loop)
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
- **Escopo de ferramentas:** `IN_JOB` — `scope_config.py` filtra para:
  - **Query (14):** `get_job_details`, `get_vacancy_funnel`, `get_candidate_details`, `get_activity_summary`, `get_pending_actions`, `compare_candidates`, `get_candidate_stats`, `get_bottleneck_analysis`, `get_job_velocity`, `get_job_quality_metrics`, `get_stakeholder_metrics`, `get_prediction_metrics`, `get_job_benchmark`, `get_smart_alerts`
  - **Action (11):** `update_candidate_stage`, `bulk_update_candidates_stage`, `reject_candidate`, `shortlist_candidate`, `add_to_list`, `hide_candidate`, `wsi_screening`, `send_email`, `send_whatsapp`, `schedule_interview`, `send_feedback`
- **Endpoint API:** `callOrchestratedJobChat()` → `POST /api/backend-proxy/orchestrator/job-chat`
- **Backend:** `app/api/v1/orchestrated_job_chat.py` (v2.0 — closed-loop action execution)

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
- **Contexto:** Chat full-page com LIA — acesso a todas as capacidades
- **Escopo:** `GLOBAL` — ferramentas restritas a `generate_report` e `schedule_report` (ver `scope_config.py`)
- **Endpoint API:** `liaApi.orchestratorProcess()` → `POST /api/backend-proxy/orchestrator/process` (com suporte a WebSocket via `wsSendMessage`)
- **Capacidades completas:**
  - Quick actions pré-definidas: "Criar uma nova vaga", "Solicitar aprovação", "Compartilhar candidatos com gestor", "Solicitar feedback de entrevista", "Consultar candidato", "Adicionar candidato", "Reagendar entrevista"
  - Ações contextuais sobre candidatos selecionados: comparar perfis, adicionar a vaga
  - Busca via Pearch AI (deep search externo) e busca local
  - Histórico de conversas persistente
  - Suporte a anexos (arquivos + áudio)
  - Resumo automático a cada N mensagens (`ROUTER_SUMMARY_EVERY_N_MESSAGES`)

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
│  → liaApi.orchestratorProcess() → /orchestrator/process  │
│  (+ WebSocket wsSendMessage)                            │
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

**Exemplo de interação (ilustrativo):**
```
Usuário: "Quero criar uma vaga de Engenheiro de Dados Senior"
→ Roteamento: CascadedRouter → domain "job_management" → WizardReActAgent
→ Thought: "Preciso coletar mais informações sobre a vaga"
→ Action: get_company_config() → obtém configurações da empresa
→ Action: get_intelligent_skills("Engenheiro de Dados Senior") → sugestões de skills
→ Action: get_intelligent_salary("Engenheiro de Dados", "Senior", "São Paulo") → faixa salarial
→ Resposta LIA: "Ótimo! Vou criar a vaga de Engenheiro de Dados Senior. Baseado nas vagas similares da sua empresa, sugiro: Skills: Python, Spark, Airflow, SQL, AWS. Faixa salarial: R$ 18.000-25.000. Posso gerar a descrição completa?"
```

### 2.2 Pipeline Agent (Triagem de CVs)
- **Domain:** `pipeline` | **Classe:** `PipelineReActAgent` | **Max iterations:** 5 | **Provider:** Claude
- **Arquivo:** `app/domains/cv_screening/agents/pipeline_react_agent.py`
- **Escopo IN (10 capacidades):** consultar dados do candidato, scores WSI, triagem, atualizar dados cadastrais, solicitar coleta de dados, extrair preferências de execução, combinar tarefas, sugerir ações/sub-status, personalizar comunicação, verificar fairness em rejeição
- **Escopo OUT (7 restrições):** outros candidatos, busca de novos, comparar vagas, adicionar em outra vaga, configurar pipeline, analytics gerais, templates de comunicação
- **Ferramentas:** `update_candidate_stage`, `add_candidate_to_vacancy`, `reject_candidate`, `shortlist_candidate`, `bulk_update_candidates_stage`, `add_to_list`, `wsi_screening`, `hide_candidate` (8 tools)

**Exemplo de interação (ilustrativo):**
```
Usuário: "Faça a triagem WSI do candidato João Silva"
→ Roteamento: CascadedRouter → domain "cv_screening" → PipelineReActAgent
→ Thought: "Preciso executar triagem WSI para o candidato"
→ Action: wsi_screening(candidate_id="abc123", job_id="job456")
→ Observation: {score: 78, competencies: [{name: "Comunicação", level: "Avançado"}, ...]}
→ Resposta LIA: "Triagem WSI concluída para João Silva. Score geral: 78/100. Destaques: Comunicação (Avançado), Trabalho em equipe (Intermediário). Pontos de atenção: Gestão de conflitos (Básico). Deseja prosseguir com a próxima etapa?"
```

### 2.3 Sourcing Agent (Busca de Candidatos)
- **Domain:** `sourcing` | **Classe:** `SourcingReActAgent` | **Max iterations:** 5 | **Provider:** Claude
- **Arquivo:** `app/domains/sourcing/agents/sourcing_react_agent.py`
- **Escopo:** Busca local (PostgreSQL) + busca externa (Pearch AI), scoring de match, análise de perfil
- **Triggers:** "buscar candidatos", "encontrar perfis", "sourcing"
- **Ferramentas:** `search_candidates`, `get_candidate_details`, `get_candidate_stats`, `get_candidate_history`, `get_talent_quality`, `get_talent_engagement`, `get_talent_availability`, `get_diversity_metrics`, `get_market_benchmarks` (9 tools)

**Exemplo de interação (ilustrativo):**
```
Usuário: "Busque desenvolvedores Python senior em São Paulo"
→ Roteamento: CascadedRouter → domain "sourcing" → SourcingReActAgent
→ Thought: "Busca por desenvolvedores Python senior em SP"
→ Action: search_candidates(query="desenvolvedor Python senior", location="São Paulo", limit=20)
→ Observation: {candidates: [{name: "Ana Costa", score: 92, ...}, ...], total: 47}
→ Resposta LIA: "Encontrei 47 candidatos para Desenvolvedor Python Senior em São Paulo. Os top 5: 1) Ana Costa (92% fit) - 8 anos exp, 2) Carlos Mendes (89% fit) - 6 anos exp... Deseja ver detalhes de algum candidato?"
```

### 2.4 Talent Agent (Assistente de Talentos)
- **Domain:** `talent` | **Classe:** `TalentReActAgent` | **Max iterations:** 5 | **Provider:** Claude
- **Arquivo:** `app/domains/recruiter_assistant/agents/talent_react_agent.py`
- **Prompt:** `app/domains/recruiter_assistant/prompts/talent_assistant_prompts.py`
- **Escopo:** Assistência no funil de talentos, operações sobre candidatos
- **FairnessGuard:** Integrado

**Exemplo de interação (ilustrativo):**
```
Usuário: "Quais candidatos estão parados há mais de 7 dias no funil?"
→ Roteamento: CascadedRouter → domain "recruiter_assistant" → TalentReActAgent
→ Thought: "Preciso identificar candidatos inativos"
→ Action: get_candidate_stats(filter="inactive_7_days")
→ Resposta LIA: "Encontrei 12 candidatos sem movimentação há mais de 7 dias: 5 na etapa Triagem, 4 em Entrevista Técnica, 3 em Proposta. Recomendo priorizar os 4 em Entrevista Técnica. Deseja que eu envie um lembrete aos entrevistadores?"
```

### 2.5 Jobs Management Agent (Portfólio de Vagas)
- **Domain:** `jobs_management` | **Classe:** `JobsMgmtReActAgent` | **Max iterations:** 5 | **Provider:** Claude
- **Arquivo:** `app/domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py`
- **Prompt:** `app/domains/recruiter_assistant/prompts/jobs_management_prompts.py`
- **Escopo:** Gestão do portfólio de vagas (listar, filtrar, analisar status)
- **FairnessGuard:** Integrado

**Exemplo de interação (ilustrativo):**
```
Usuário: "Quais vagas estão abertas há mais de 30 dias?"
→ Roteamento: CascadedRouter → domain "recruiter_assistant" → JobsMgmtReActAgent
→ Resposta LIA: "Você tem 8 vagas abertas há mais de 30 dias: 1) Dev Backend Senior (45 dias, 23 candidatos), 2) PM Pleno (38 dias, 15 candidatos)... As vagas #1 e #3 têm poucos candidatos qualificados. Sugiro ampliar as fontes de sourcing."
```

### 2.6 Kanban Agent (Análise do Pipeline)
- **Domain:** `kanban` | **Classe:** `KanbanReActAgent` | **Max iterations:** 5 | **Provider:** Claude
- **Arquivo:** `app/domains/recruiter_assistant/agents/kanban_react_agent.py`
- **Prompt:** `app/domains/recruiter_assistant/prompts/kanban_assistant_prompts.py`
- **Escopo:** Análise e operações no kanban; 18 tipos de comando (ver seção 4.2)
- **FairnessGuard:** Integrado | **GUARDRAIL_TOOLS:** Integrados

**Exemplo de interação (ilustrativo):**
```
Usuário: "Rankeie os candidatos desta vaga por fit"
→ Roteamento: detect_command_type() → RANKEAR_CANDIDATOS → KanbanReActAgent
→ Resposta LIA (JSON formatado):
{
  "ranking": [
    {"posicao": 1, "candidato_nome": "Maria Santos", "score_fit": 95, "principais_forcas": ["10 anos Python", "Liderança técnica"], "principais_gaps": ["Sem experiência com Kafka"], "justificativa": "Perfil altamente alinhado com requisitos técnicos e culturais"},
    {"posicao": 2, "candidato_nome": "Pedro Lima", "score_fit": 88, ...}
  ],
  "insights": "Pool competitivo com 3 candidatos acima de 85% de fit",
  "recomendacao": "Agendar entrevista técnica com os top 3"
}
```

### 2.7 Policy Agent (Políticas de Contratação)
- **Domain:** `policy` | **Classe:** `PolicyReActAgent` | **Max iterations:** 5 | **Provider:** Claude
- **Arquivo:** `app/domains/hiring_policy/agents/policy_react_agent.py`
- **Prompt:** `app/domains/hiring_policy/agents/policy_system_prompt.py`
- **Escopo:** CRUD de políticas de contratação, validação de compliance, regras de aprovação

**Exemplo de interação (ilustrativo):**
```
Usuário: "Qual é a política de aprovação para vagas acima de R$ 20.000?"
→ Roteamento: CascadedRouter → domain "hiring_policy" → PolicyReActAgent
→ Resposta LIA: "Para vagas com salário acima de R$ 20.000, a política vigente requer: 1) Aprovação do gestor direto, 2) Aprovação do diretor de área, 3) Validação do RH. Prazo máximo: 5 dias úteis. Deseja criar ou alterar esta política?"
```

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

**Exemplo de interação (ilustrativo):**
```
Usuário: "Preciso preencher a vaga de Tech Lead até sexta-feira"
→ Roteamento: CascadedRouter → domain "automation" → AutomationReActAgent
→ Thought: "Preciso decompor em subtarefas com prazo apertado"
→ Resposta LIA: "Plano de execução para preencher Tech Lead até sexta:
  1. [PARALELO] Sourcing IA (Pearch) + busca banco interno (hoje)
  2. [SEQ] Triagem top 10 candidatos (hoje-amanhã)
  3. [PARALELO] Agendar entrevistas técnicas + enviar teste (amanhã)
  4. [SEQ] Painel final + proposta (quinta)
  Agentes envolvidos: Sourcing, Pipeline, Communication, Scheduling
  Deseja que eu execute este plano?"
```

### 2.9 Analytics Agent (KPIs e Previsões)
- **Domain:** `analytics` | **Classe:** `AnalyticsReActAgent` | **Max iterations:** 6 | **Provider:** Claude
- **Arquivo:** `app/domains/analytics/agents/analytics_react_agent.py`
- **Prompt:** `app/domains/analytics/agents/analytics_system_prompt.py`
- **Ferramentas:** 19 tools (ver seção 6)

**Exemplo de interação (ilustrativo):**
```
Usuário: "Como está a performance do funil da vaga Dev Backend?"
→ Roteamento: CascadedRouter → domain "analytics" → AnalyticsReActAgent
→ Action: get_prediction_metrics(job_id="job789", time_range="30d")
→ Action: get_conversion_patterns(job_id="job789")
→ Resposta LIA: "Performance da vaga Dev Backend (últimos 30 dias):
  - 156 candidatos totais, 89 triados, 34 entrevistados, 12 finalistas, 3 contratados
  - Taxa de conversão geral: 1.9%
  - Gargalo: Etapa Entrevista Técnica (tempo médio 8.3 dias vs benchmark 5 dias)
  - Previsão TTF: mais 15 dias para preencher as 2 vagas restantes"
```

### 2.10 Communication Agent (Multi-canal LGPD)
- **Domain:** `communication` | **Classe:** `CommunicationReActAgent` | **Max iterations:** 6 | **Provider:** Claude
- **Arquivo:** `app/domains/communication/agents/communication_react_agent.py`
- **Canais:** Email, WhatsApp, Teams
- **Ferramentas:** `send_email`, `send_whatsapp`, `schedule_interview`, `send_bulk_email`, `send_feedback` (5 tools)

**Exemplo de interação (ilustrativo):**
```
Usuário: "Envie um email de feedback para os 3 candidatos rejeitados na vaga de UX Designer"
→ Roteamento: CascadedRouter → domain "communication" → CommunicationReActAgent
→ Thought: "Preciso enviar feedback personalizado para 3 candidatos rejeitados"
→ Action: send_bulk_email(candidate_ids=["c1","c2","c3"], template="rejection_feedback", job_title="UX Designer")
→ Resposta LIA: "Emails de feedback enviados para 3 candidatos:
  - Ana Oliveira (ana@email.com) — Enviado
  - Bruno Costa (bruno@email.com) — Enviado
  - Carla Dias (carla@email.com) — Enviado
  Cada email inclui feedback personalizado sobre pontos fortes e áreas de desenvolvimento."
```

### 2.11 ATS Integration Agent (Integração Bidirecional)
- **Domain:** `ats_integration` | **Classe:** `ATSIntegrationReActAgent` | **Max iterations:** 6 | **Provider:** Claude
- **Arquivo:** `app/domains/ats_integration/agents/ats_integration_react_agent.py`
- **Provedores:** Gupy, Pandapé, Merge (multi-ATS), StackOne (multi-ATS internacional)
- **Fluxos:** Push (WeDOTalent → ATS), Pull (ATS → WeDOTalent)
- **Princípios:** Multi-tenant obrigatório (`company_id`), LGPD (dados sensíveis NÃO sincronizados), idempotência, auditoria SOX/ISO 27001
- **Prompt:** Inclui regras de SOX/ISO 27001 para trilha de auditoria

**Exemplo de interação (ilustrativo):**
```
Usuário: "Sincronize os candidatos aprovados da vaga Tech Lead com o Gupy"
→ Roteamento: CascadedRouter → domain "ats_integration" → ATSIntegrationReActAgent
→ Thought: "Preciso fazer push dos candidatos aprovados para o Gupy"
→ Resposta LIA: "Sincronização com Gupy concluída:
  - 5 candidatos aprovados enviados
  - 4 sincronizados com sucesso
  - 1 falha (Carlos Mendes — email duplicado no Gupy, ID: gupy_err_4521)
  Dados sensíveis (CPF, endereço) NÃO foram sincronizados conforme política LGPD."
```

---

## 3. Capacidades Detalhadas

### 3.1 WSI Screening (Entrevista por Voz Estruturada)

- **O que faz:** Executa triagem de candidatos via entrevista estruturada em 7 blocos
- **Input:** `candidate_id`, `job_vacancy_id`, `questions[]`
- **Processing:** IA (Claude via WSI Evaluator Agent) — 7 dimensões avaliadas
- **Output:** Score 0–100, classificação (Avançar/Revisar/Rejeitar), justificativa por bloco
- **Execução:** IA real (Claude Sonnet)
- **FairnessGuard:** Integrado — 3 camadas verificam output antes de finalizar score
- **Arquivo:** `app/domains/cv_screening/agents/wsi_interview_graph.py`

**7 Dimensões Avaliadas:**
1. Abertura e apresentação
2. Motivação para a vaga
3. Experiência técnica relevante
4. Soft skills e comunicação
5. Pretensão salarial e benefícios
6. Disponibilidade e logística
7. Fechamento e próximos passos

### 3.2 LIA Score (Scoring Unificado)

- **O que faz:** Calcula pontuação unificada de fit do candidato para uma vaga
- **Input:** rubric scores, WSI scores, prerequisites, recency, calibration_adjustment
- **Processing:** Local (sem LLM) — fórmula ponderada com pesos por cenário
- **Output:** Score 0–100 com breakdown por componente
- **Arquivo:** `lia-agent-system/app/services/lia_score_service.py`

**Fórmula:** `LIA_Score = Σ(peso_componente × score_componente × DataAvailability)`

**Cenários de peso:**
- **WSI + Rubrica:** WSI 40%, Rubrica 30%, Prerequisites 15%, Recency 15%
- **Apenas WSI:** WSI 55%, Prerequisites 25%, Recency 20%
- **Apenas Rubrica:** Rubrica 55%, Prerequisites 25%, Recency 20%
- **Sem avaliação:** Prerequisites 50%, Recency 50%

### 3.3 Avaliação por Rubrica Multi-dimensional

- **O que faz:** Avaliação estruturada com rubricas customizáveis
- **Input:** candidato, vaga, rubricas selecionadas
- **Processing:** IA real (Claude)
- **Output:** Score por rubrica + score consolidado + justificativa
- **Arquivo:** `lia-agent-system/app/services/rubric_evaluation_service.py`

### 3.4 Busca Inteligente de Candidatos

- **O que faz:** Busca local (PostgreSQL) + busca externa (Pearch AI)
- **Input:** query texto livre, filtros estruturados
- **Processing:** Local + API externa
- **Output:** Lista de candidatos com scores de match
- **Ferramentas:** `search_candidates` em `app/domains/sourcing/tools/query_tools.py`

### 3.5 Comparação de Candidatos

- **O que faz:** Comparação multi-dimensional entre 2+ candidatos
- **Input:** `candidate_ids[]`, `job_context`
- **Processing:** IA real (Claude via Kanban Agent)
- **Output:** Tabela comparativa com dimensões, scores, recomendação
- **Ferramenta:** `compare_candidates` em `app/domains/analytics/tools/analytics_query_tools.py`
- **Endpoint:** `POST /orchestrator/job-chat` com `detect_command_type() → COMPARAR_CANDIDATOS`
- **Prompt template:** `kanban_assistant_prompts.py` → `COMPARAR_CANDIDATOS` (linha 280)

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

#### Exemplo completo: `funnel_analysis` (ilustrativo)

**Input do usuário:** "Analise o funil da vaga Dev Backend Senior"

**Resposta LIA (formato baseado no template de `job_analytics_prompt_service.py`):**
```markdown
## Análise do Funil — Dev Backend Senior

### Candidatos por Etapa
| Etapa               | Candidatos | % do Total |
|---------------------|-----------|------------|
| Aplicação           | 156       | 100%       |
| Triagem Curricular  | 89        | 57%        |
| Entrevista Técnica  | 34        | 22%        |
| Entrevista Final    | 12        | 7.7%       |
| Proposta            | 5         | 3.2%       |
| Contratado          | 3         | 1.9%       |

### Taxa de Conversão por Etapa
- Aplicação → Triagem: **57%** (benchmark: 60%)
- Triagem → Entrevista: **38%** (benchmark: 35%) ✅
- Entrevista → Final: **35%** (benchmark: 40%) ⚠️
- Final → Proposta: **42%** (benchmark: 50%) ⚠️
- Proposta → Contratação: **60%** (benchmark: 70%) ⚠️

### Gargalos Identificados
1. **Entrevista Técnica** — Tempo médio: 8.3 dias (benchmark: 5 dias)
2. **Proposta** — Taxa de aceitação abaixo do benchmark

### Recomendações
- Adicionar mais entrevistadores técnicos para reduzir tempo
- Revisar competitividade salarial na etapa de proposta
```

**Fallback offline:** `{"success": false, "error": "Serviço indisponível. Tente novamente em alguns minutos."}`

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

#### Exemplo completo: `resumir_perfil` (ilustrativo)

**Input do usuário:** "Me fale sobre a candidata Maria Santos"

**Resposta LIA (JSON formatado como markdown):**
```json
{
  "resumo_executivo": "Maria Santos é uma profissional senior com 8 anos de experiência em desenvolvimento backend, atualmente como Tech Lead na Nubank.",
  "perfil_profissional": {
    "cargo_atual": "Tech Lead",
    "empresa_atual": "Nubank",
    "experiencia_anos": 8,
    "formacao": "Ciência da Computação - USP",
    "principais_skills": ["Python", "Go", "Kubernetes", "AWS", "System Design"],
    "certificacoes": ["AWS Solutions Architect", "CKA"]
  },
  "analise_fit": {
    "score_fit": 92,
    "pontos_fortes": ["Experiência sólida em arquitetura distribuída", "Liderança técnica comprovada", "Stack alinhada com requisitos"],
    "pontos_atencao": ["Sem experiência com Kafka (requisito desejável)", "Pretensão salarial 15% acima da faixa"],
    "fit_cultural": "Alto — histórico de mentoria e contribuições open source"
  },
  "perguntas_entrevista": [
    "Como você lidou com uma migração de monolito para microsserviços?",
    "Descreva uma situação de conflito técnico na equipe e como resolveu"
  ],
  "proximos_passos": "Recomendo agendar entrevista técnica com o time de arquitetura"
}
```

**Fallback offline:** Retorna dados básicos do banco sem análise IA: nome, cargo, empresa, skills cadastradas.

#### Exemplo completo: `mover_candidato` (ilustrativo — ação com HITL)

**Input do usuário:** "Mova o João Silva para Entrevista Técnica"

**Resposta LIA (needs_confirmation: true):**
```
Entendi! Vou mover o candidato João Silva para a etapa **Entrevista Técnica**.

Confirmação necessária:
- Candidato: João Silva
- De: Triagem Curricular
- Para: Entrevista Técnica
- Vaga: Dev Backend Senior

Confirma esta movimentação?
```

**Após confirmação do usuário:**
```
João Silva movido para Entrevista Técnica com sucesso!
Próximo passo sugerido: Agendar entrevista técnica com o gestor.
```

**Fallback offline:** `"Desculpe, não foi possível executar a movimentação. Tente novamente em alguns minutos."`

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

#### Exemplo completo: "top 5" (ilustrativo)

**Input do usuário:** "Top 5 candidatos para essa busca"

**Resposta LIA:**
```markdown
## Top 5 Candidatos — Busca: Desenvolvedor Python Senior

| # | Candidato        | LIA Score | Experiência | Localização  | Destaque                          |
|---|------------------|-----------|-------------|--------------|-----------------------------------|
| 1 | Ana Costa        | 92        | 8 anos      | São Paulo    | Tech Lead na Nubank, AWS cert.    |
| 2 | Carlos Mendes    | 89        | 6 anos      | Remoto       | Contribuidor Django, speaker      |
| 3 | Beatriz Lima     | 87        | 7 anos      | São Paulo    | Data Platform no iFood            |
| 4 | Diego Santos     | 85        | 5 anos      | Campinas     | MLOps + Python, startup exp.      |
| 5 | Elena Ferreira   | 83        | 9 anos      | Rio de Janeiro| Backend Lead na Stone             |

### Análise do Pool
- **Score médio:** 87.2 (acima do benchmark de 75)
- **Disponibilidade:** 3/5 disponíveis para contato imediato
- **Faixa salarial:** R$ 16.000 - R$ 28.000
```

**Fallback offline:** "Olá! Sou a LIA, sua assistente de recrutamento. Recebi sua mensagem sobre 'Top 5 candidatos para essa busca...' Como posso ajudar você hoje?" com `suggested_prompts: ["Criar uma nova vaga", "Buscar candidatos", "Ver minhas tarefas pendentes"]`

#### Exemplo completo: "comparar" (ilustrativo)

**Input do usuário:** "Compare Ana Costa e Carlos Mendes"

**Resposta LIA:**
```markdown
## Comparação: Ana Costa vs Carlos Mendes

| Dimensão              | Ana Costa (92)        | Carlos Mendes (89)     |
|-----------------------|-----------------------|------------------------|
| Experiência           | 8 anos                | 6 anos                 |
| Stack técnica         | Python, Go, K8s, AWS  | Python, Django, Docker |
| Liderança             | Tech Lead (3 anos)    | IC Senior              |
| Certificações         | AWS SA, CKA           | Nenhuma                |
| Disponibilidade       | 30 dias               | Imediata               |
| Pretensão salarial    | R$ 25.000             | R$ 20.000              |

### Recomendação
Ana Costa é mais adequada para a posição devido à experiência em liderança técnica e certificações. Carlos Mendes é uma opção sólida se o budget for mais restrito e houver disponibilidade imediata.
```

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

## 8. Limitações e Dívidas Técnicas

1. **Anti-sycophancy** — Regra presente no system prompt mas não validada por guardrail automatizado em todos os agentes.
2. **FairnessGuard** — Integrado em Wizard, Talent, Jobs Management, Kanban; ausente em Analytics, Automation, ATS Integration.
3. **LGPD em ATS** — Dados sensíveis não sincronizados, mas a lista de campos sensíveis é hardcoded.
4. **Auditoria** — SOX/ISO 27001 mencionados no prompt do ATS Agent, mas sem implementação de audit trail centralizado.

---

## 9. Resiliência e Circuit Breakers

### 9.1 Arquitetura de Circuit Breaker

**Arquivo:** `lia-agent-system/app/shared/resilience/circuit_breaker.py` (682 linhas)

O sistema implementa o padrão Circuit Breaker para proteger chamadas a APIs externas, prevenindo falhas em cascata quando serviços ficam indisponíveis.

**3 Estados do Circuit Breaker:**

```
┌─────────┐    failure_count ≥ threshold    ┌──────┐
│ CLOSED  │ ──────────────────────────────→ │ OPEN │
│(Normal) │                                 │(Blk) │
└─────────┘                                 └──┬───┘
     ↑                                         │
     │ half_open_calls ≥ max_calls              │ recovery_timeout expirado
     │ (todos sucesso)                          ↓
     │                                    ┌───────────┐
     └────────────────────────────────── │ HALF_OPEN │
           recuperação confirmada         │ (Teste)   │
                                          └───────────┘
```

**Configuração padrão (`CircuitBreakerConfig`):**

| Parâmetro             | Valor Padrão | Descrição                                    |
|-----------------------|-------------|----------------------------------------------|
| `failure_threshold`   | 5           | Falhas consecutivas para abrir o circuit     |
| `recovery_timeout`    | 30.0s       | Tempo antes de tentar recovery (HALF_OPEN)   |
| `success_threshold`   | 2           | Sucessos em HALF_OPEN para fechar circuit    |
| `timeout`             | 10.0s       | Timeout de cada request individual           |
| `exclude_exceptions`  | ()          | Exceções que não contam como falha           |

### 9.2 Circuits Registrados

Os circuit breakers são criados dinamicamente via decorator `@circuit_breaker()` ou instanciação direta de `CircuitBreaker`. O sistema utiliza um dicionário `_circuits: Dict[str, CircuitBreakerState]` como registry lazy — circuits são criados no primeiro uso via `_get_circuit()`.

**Serviços protegidos identificados no codebase:**

| Circuit Name     | Serviço Protegido                | Arquivo que consome                                      |
|------------------|----------------------------------|----------------------------------------------------------|
| `anthropic`      | API Claude (Anthropic)           | Chamadas LLM dos 11 agentes ReAct                       |
| `openai`         | API OpenAI (GPT-4o, GPT-4-turbo)| Fallback LLM, embeddings                                |
| `gemini`         | API Google Gemini                | Modelo alternativo para scoring                          |
| `pearch`         | Pearch AI (busca candidatos)     | `app/domains/sourcing/tools/query_tools.py`              |
| `workos`         | WorkOS (SSO/SCIM)                | `app/auth/` (autenticação enterprise)                    |
| `merge`          | Merge API (ATS unificado)        | `app/domains/ats_integration/`                           |
| `google_calendar`| Google Calendar API              | `app/domains/interview_scheduling/`                      |
| `gupy`           | ATS Gupy (integração)            | `app/domains/ats_integration/services/ats_clients/gupy.py` |
| `pandape`        | ATS Pandapé (integração)         | `app/domains/ats_integration/services/ats_clients/pandape.py` |
| `stackone`       | StackOne (ATS unificado)         | `app/domains/ats_integration/services/ats_clients/stackone.py` |
| `sendgrid`       | SendGrid (email transacional)    | `app/services/email_service.py`                          |
| `resend`         | Resend (email fallback)          | `app/services/email_service.py`                          |

### 9.3 Notificação de Abertura de Circuit

Quando um circuit breaker transiciona para OPEN, o sistema envia notificação automática:

**Arquivo:** `circuit_breaker.py` → `_notify_circuit_open()`

**Mecanismo:**
1. **Redis dedup:** chave `cb_alert:{service_name}` com TTL 1 hora — evita flood de alertas
2. **Canais:** Bell (notificação in-app) + Teams (Microsoft Teams)
3. **Mensagem:** "O circuit breaker para '{service_name}' foi aberto após múltiplas falhas. Chamadas estão sendo rejeitadas automaticamente. O circuit tentará recuperação em 30s."
4. **Non-blocking:** execução via `loop.create_task()` — nunca bloqueia o request principal

### 9.4 Implementação Dual

O arquivo `circuit_breaker.py` contém **duas implementações**:

1. **Classe `CircuitBreaker`** (linhas 117-340) — Implementação orientada a objetos com lock asyncio, estatísticas detalhadas (`CircuitBreakerStats`), e classe registry `ALL_CIRCUITS`. Usada para instanciação direta.

2. **Decorator `circuit_breaker()`** (linhas 626-655) — Implementação funcional via `_circuits` dict com `CircuitBreakerState` dataclass. Usado como decorator em funções async.

**APIs de diagnóstico:**
- `get_circuit_status(service_name)` — status de um circuit específico
- `get_all_circuits_status()` — status de todos os circuits registrados
- `reset_circuit(service_name)` — reset manual para CLOSED
- `reset_all_circuits()` — reset de todos os circuits

**Métricas Prometheus:** `circuit_breaker_state` gauge (0=closed, 1=half_open, 2=open) exportada quando módulo de observabilidade está disponível.

### 9.5 Fallback Strategy

Quando o circuit está OPEN, o sistema suporta fallbacks configuráveis:

```python
@circuit_breaker("anthropic", failure_threshold=5, recovery_timeout=60, fallback=my_fallback_fn)
async def call_anthropic(prompt: str) -> str:
    ...
```

- Se `fallback` é definido e circuit está OPEN → executa fallback em vez de lançar exceção
- Se `fallback` não é definido → lança `CircuitBreakerError(name, retry_after)`
- O Orchestrator captura `CircuitBreakerError` e retorna mensagem amigável ao usuário

---

## 10. Gestão de Custos e Token Tracking

### 10.1 TokenTrackingService

**Arquivo:** `lia-agent-system/app/services/token_tracking_service.py` (722 linhas)

Serviço de monitoramento em tempo real de uso de tokens LLM com estimativa de custos e enforcement de limites por usuário e empresa.

### 10.2 Modelos e Preços Suportados

**Dicionário `TOKEN_PRICES` — 10 modelos com preços por 1K tokens (USD):**

| Modelo              | Input ($/1K) | Output ($/1K) | Uso na Plataforma                    |
|---------------------|-------------|---------------|--------------------------------------|
| `claude-3-sonnet`   | $0.003      | $0.015        | Modelo principal dos 11 agentes      |
| `claude-3-haiku`    | $0.00025    | $0.00125      | Tier 5 LLM Cascade (roteamento)      |
| `claude-3-opus`     | $0.015      | $0.075        | Tier 5 LLM Cascade (fallback final)  |
| `claude-3.5-sonnet` | $0.003      | $0.015        | Avaliação WSI, JD enriquecida        |
| `gpt-4o`            | $0.005      | $0.015        | Alternativa OpenAI (quando config.)  |
| `gpt-4o-mini`       | $0.00015    | $0.0006       | Tarefas leves (classificação)        |
| `gpt-4-turbo`       | $0.01       | $0.03         | Análises complexas (quando config.)  |
| `gpt-3.5-turbo`     | $0.0005     | $0.0015       | Embeddings, classificação rápida     |
| `gemini-1.5-pro`    | $0.00125    | $0.005        | Alternativa Google (quando config.)  |
| `gemini-1.5-flash`  | $0.000075   | $0.0003       | Tarefas rápidas/baratas              |

### 10.3 Limites Padrão (DEFAULT_LIMITS)

| Limite                          | Valor Padrão    | Escopo           |
|---------------------------------|-----------------|------------------|
| `daily_tokens_per_user`         | 500.000         | Por usuário/dia  |
| `daily_tokens_per_company`      | 5.000.000       | Por empresa/dia  |
| `monthly_cost_per_company`      | $500.00         | Por empresa/mês  |
| `hourly_tokens_per_user`        | 100.000         | Por usuário/hora |
| `requests_per_minute_per_user`  | 60              | Por usuário/min  |

**Limites customizáveis:** `set_custom_limits(company_id, limits)` permite override por empresa. O merge é aditivo — limites não especificados usam DEFAULT_LIMITS.

### 10.4 Alertas de Consumo

**Thresholds de alerta:** `ALERT_THRESHOLDS = [80, 100]`

- Ao atingir 80% do limite → alerta de aviso (warning)
- Ao atingir 100% do limite → alerta de bloqueio (block) + request rejeitado

### 10.5 Funcionalidades

| Método                    | Descrição                                              |
|---------------------------|--------------------------------------------------------|
| `record_usage()`          | Registra uso de tokens por operação na tabela `ai_consumption` |
| `get_usage_summary()`     | Resumo de uso por período (dia/mês)                    |
| `check_limits()`          | Verifica se usuário/empresa está dentro dos limites    |
| `get_cost_estimate()`     | Calcula custo estimado baseado no modelo e tokens      |
| `_calculate_cost_cents()` | Calcula custo em centavos usando `TOKEN_PRICES`        |

### 10.6 Retenção de Logs

**Constante:** `AI_LOG_RETENTION_DAYS` (definido em `app/models/ai_consumption.py`)

Logs de consumo de IA são marcados com `scheduled_deletion_at` para limpeza automática pelo `lgpd_cleanup_service.py` após o período de retenção (365 dias por padrão para `ai_logs`).

---

## 11. ConfidencePolicyService — Autonomia de Ações

### 11.1 Visão Geral

**Arquivo:** `lia-agent-system/app/services/confidence_policy_service.py`

O ConfidencePolicyService determina se a LIA pode executar uma ação autonomamente, notificar o recrutador, ou pedir confirmação. Funciona como gate entre a decisão do agente e a execução real da ação.

### 11.2 Níveis de Confiança

O serviço define 3 níveis de ação baseados na confiança calculada:

| Nível             | Threshold         | Comportamento                                                 |
|-------------------|--------------------|---------------------------------------------------------------|
| `APPLY_SILENT`    | confidence ≥ 0.85 | LIA executa a ação automaticamente sem notificar o recrutador |
| `APPLY_NOTIFY`    | confidence ≥ 0.70 | LIA executa a ação e notifica o recrutador sobre o que foi feito |
| `ASK_USER`        | confidence < 0.70 | LIA apresenta a proposta e aguarda confirmação do recrutador  |

### 11.3 Cálculo de Confiança por Fonte

O serviço mantém um dicionário de confiança base por fonte de dados:

```python
SOURCE_BASE_CONFIDENCES = {
    "cv_parsing": 0.75,
    "wsi_evaluation": 0.80,
    "rubric_evaluation": 0.85,
    "manual_input": 0.95,
    "pearch_api": 0.70,
    "linkedin_scraping": 0.65,
}
```

### 11.4 Modificadores de Confiança

| Modificador                | Valor    | Condição                                            |
|----------------------------|----------|------------------------------------------------------|
| `MULTI_SOURCE_AGREE_BONUS` | +0.10    | Quando 2+ fontes concordam no mesmo resultado        |
| `DISAGREE_PENALTY`         | -0.30    | Quando fontes divergem significativamente             |

**Fórmula:** `confidence_final = base_confidence + bonuses - penalties`

### 11.5 Integração com Fluxo HITL

```
Agente propõe ação
     │
     ▼
ConfidencePolicyService.evaluate(action, sources, confidence)
     │
     ├── ≥ 0.85 → APPLY_SILENT → ActionExecutor.execute()
     │
     ├── ≥ 0.70 → APPLY_NOTIFY → ActionExecutor.execute() + Notification
     │
     └── < 0.70 → ASK_USER → PendingActionStore.store() → HITL flow
```

---

## 12. Governança de Agentes

### 12.1 EnhancedAgentMixin — Ciclo de Vida de 5 Etapas

**Arquivo:** `lia-agent-system/libs/agents-core/lia_agents_core/enhanced_agent_mixin.py` (301 linhas)

Todos os 11 agentes ReAct herdam de `EnhancedAgentMixin`, que adiciona memória, autonomia e aprendizado ao ciclo ReAct padrão.

**Ciclo de vida de 5 etapas:**

```
1. _setup_enhanced(domain)
   ├── Inicializa WorkingMemoryService (memória de curto prazo)
   ├── Inicializa LongTermMemoryService (memória de longo prazo)
   ├── Inicializa MemoryIntegration (ponte entre WM e LTM)
   ├── Inicializa AutonomyEngine (políticas de autonomia)
   └── Inicializa LearningExtractor (extração de aprendizados)

2. _get_memory_context(session_id, company_id)
   └── MemoryIntegration.get_enriched_context()
       → Injeta memórias relevantes no system prompt antes do ReAct loop

3. _resolve_guardrails(company_id)
   ├── 1. AutonomyEngine.resolve_guardrails() (política da empresa)
   ├── 2. Fallback: GuardrailRepository.get_blocked_tools() (banco de dados)
   └── 3. Último recurso: lista estática DEFAULT_GUARDRAIL_TOOLS

4. ReAct Loop (Thought → Action → Observation → ...)
   └── Tools = base_tools + insight_tools + proactive_tools + predictive_tools

5. _post_loop_learning(state, company_id, session_id)
   └── LearningExtractor.extract_and_save()
       → Salva aprendizados na LongTermMemoryService
```

### 12.2 AutonomyEngine — 3 Níveis de Autonomia

**Arquivo:** `lia-agent-system/libs/agents-core/lia_agents_core/autonomy_engine.py`

O AutonomyEngine determina o nível de autonomia da LIA por empresa, controlando quais ações requerem confirmação humana.

**3 Níveis:**

| Nível           | Descrição                                                | Ações que requerem HITL                   |
|-----------------|----------------------------------------------------------|-------------------------------------------|
| `CONSERVATIVE`  | Todas as ações destrutivas requerem confirmação          | move, reject, delete, send, bulk_update   |
| `BALANCED`      | Ações de leitura e comunicação são autônomas             | reject, delete, bulk_update, finalize     |
| `AUTONOMOUS`    | Apenas ações irreversíveis requerem confirmação          | delete, finalize_hiring                   |

**Guardrails por nível (`GUARDRAILS_BY_LEVEL`):**
- `CONSERVATIVE`: `["move_candidate", "batch_move", "finalize_hiring", "delete_job", "reject_candidate", "send_bulk_email", "update_candidate_field"]`
- `BALANCED`: `["finalize_hiring", "delete_job", "reject_candidate", "send_bulk_email"]`
- `AUTONOMOUS`: `["finalize_hiring", "delete_job"]`

### 12.3 Guardrails Estáticos (Fallback)

**Arquivo:** `enhanced_agent_mixin.py` → `_resolve_guardrails()`

Se tanto o AutonomyEngine quanto o GuardrailRepository falharem, o sistema usa uma lista estática como último recurso:

```python
_DEFAULT_GUARDRAIL_TOOLS = [
    "move_candidate",
    "batch_move",
    "finalize_hiring",
    "delete_job",
    "reject_candidate",
    "send_bulk_email",
    "update_candidate_field",
]
```

**Estratégia de fallback em 3 camadas:**
1. AutonomyEngine (política da empresa via `CompanyHiringPolicy`)
2. GuardrailRepository (banco de dados via `AsyncSessionLocal`)
3. Lista estática (hardcoded — modo mais restritivo)

### 12.4 Ferramentas Compartilhadas Aprimoradas

O `EnhancedAgentMixin` injeta 3 categorias de ferramentas compartilhadas em todos os agentes:

| Categoria          | Arquivo                                     | Ferramentas incluídas                           |
|--------------------|---------------------------------------------|--------------------------------------------------|
| Insight Tools      | `app/shared/tools/insight_tools.py`         | Análise histórica, tendências, padrões           |
| Proactive Tools    | `app/shared/tools/proactive_tools.py`       | Detecção de riscos, alertas proativos            |
| Predictive Tools   | `app/shared/tools/predictive_tools.py`      | Previsões, recomendações, forecasting            |

### 12.5 Anti-Sycophancy

Todos os 11 agentes incluem regra anti-sycophancy no system prompt:

- **Bloco compartilhado:** `ANTI_SYCOPHANCY_OPERATIONAL` (importado de módulo comum)
- **Regra:** "Nunca confirme pedidos discriminatórios ou que violem compliance. Apresente alternativas com dados quando necessário."
- **Enforcement:** Via FairnessGuard (pré-processamento) + regra no prompt (em runtime)
- **Limitação:** Sem guardrail automatizado em runtime para validar resposta final — depende do LLM seguir a instrução

---

## 13. Aprendizado Contínuo e Memória

### 13.1 LearningExtractor

**Arquivo:** `lia-agent-system/libs/agents-core/lia_agents_core/learning_extractor.py`

Extrai aprendizados de cada execução do ciclo ReAct e os classifica em 3 categorias:

| Categoria    | Descrição                                              | Exemplo                                           |
|-------------|--------------------------------------------------------|---------------------------------------------------|
| `pattern`   | Padrões recorrentes identificados nas interações       | "Recrutador sempre pede ranking após triagem"     |
| `preference`| Preferências do recrutador/empresa detectadas          | "Empresa X prefere candidatos com certificação AWS" |
| `insight`   | Insights sobre o processo de recrutamento              | "Vagas tech demoram 2x mais que vagas admin"      |

### 13.2 LongTermMemoryService

**Arquivo:** `lia-agent-system/libs/agents-core/lia_agents_core/long_term_memory.py`

Armazena memórias de longo prazo classificadas por tipo:

**4 Tipos de Memória Válidos (`VALID_MEMORY_TYPES`):**

| Tipo        | Propósito                                     | Exemplo de Uso                                    |
|-------------|-----------------------------------------------|---------------------------------------------------|
| `pattern`   | Padrões de comportamento do recrutador         | "Sempre rejeita candidatos sem experiência X"     |
| `preference`| Preferências persistentes da empresa/recrutador| "Prefere entrevistas às terças e quintas"         |
| `learning`  | Aprendizados extraídos do LearningExtractor    | "WSI scores > 80 correlacionam com contratação"  |
| `outcome`   | Resultados de ações e decisões                 | "Candidato contratado após score 85 + entrevista"|

### 13.3 WorkingMemoryService

**Arquivo:** `lia-agent-system/libs/agents-core/lia_agents_core/working_memory.py`

Memória de curto prazo para o contexto da sessão atual:
- Mantém estado entre turnos do chat
- Limitada a 20 mensagens por contexto LLM
- Resumo automático a cada N mensagens
- Isolada por sessão (session-safe via `AgentFactory`)

### 13.4 MemoryIntegration

**Arquivo:** `lia-agent-system/libs/agents-core/lia_agents_core/memory_integration.py`

Ponte entre WorkingMemory e LongTermMemory:
- `get_enriched_context()` — recupera e formata memórias relevantes para injeção no system prompt
- Combina memórias de curto prazo (sessão) com memórias de longo prazo (empresa/recrutador)
- Filtra por domínio e relevância

### 13.5 FeedbackLearningService

**Arquivo:** `lia-agent-system/app/services/feedback_learning_service.py`

Processa feedback dos recrutadores (thumbs up/down, rating, correções) para melhorar futuras respostas:

- **Feedback positivo (thumbs up / rating ≥ 4):** Armazenado como dados de treinamento de qualidade
- **Feedback negativo com correção:** Gera par DPO (Direct Preference Optimization) para fine-tuning
- **Padrões de feedback:** Identificados e salvos como `learning` na LongTermMemory

### 13.6 OutcomeTracker

**Arquivo:** `lia-agent-system/app/domains/job_management/services/outcome_tracker.py`

Rastreia resultados de contratações para correlacionar com decisões da LIA:
- Candidatos contratados após recomendação → `outcome` positivo
- Candidatos rejeitados que foram recontratados → `outcome` a revisar
- Dados alimentam o loop de aprendizado do LIA Score

### 13.7 TrainingDataService — Export para Fine-tuning

**Arquivo:** `lia-agent-system/app/services/training_data_service.py` (506 linhas)

Exporta dados de treinamento de alta qualidade para fine-tuning de modelos LLM:

**3 Formatos de Exportação:**

| Formato        | Método                      | Estrutura                                            |
|----------------|------------------------------|------------------------------------------------------|
| **OpenAI**     | `export_openai_format()`     | `{"messages": [{"role": "system", ...}, {"role": "user", ...}, {"role": "assistant", ...}]}` |
| **Anthropic**  | `export_anthropic_format()`  | Formato nativo Anthropic com `\n\nHuman:` e `\n\nAssistant:` |
| **DPO Pairs**  | `export_dpo_pairs()`         | `{"chosen": boa_resposta, "rejected": resposta_original, "prompt": user_message}` |

**Critérios de Qualidade (`_is_quality_response`):**
- Rating ≥ 4 OU thumbs == "up"
- Response length > 50 caracteres (`MIN_RESPONSE_LENGTH`)
- Sem padrões de erro (7 patterns: "erro", "error", "exception", "falha", etc.)
- Confidence score ≥ 0.7 (`MIN_CONFIDENCE_SCORE`)

**System Prompt para Treinamento:**
```
Você é LIA, uma assistente inteligente especializada em recrutamento e seleção.
Você ajuda recrutadores a:
- Criar vagas de emprego completas e atrativas
- Definir competências e requisitos adequados
- Analisar faixas salariais do mercado
- Gerar descrições de cargo profissionais
Responda sempre em português brasileiro, de forma clara e objetiva.
```

---

## 14. FairnessGuard — 3 Camadas de Proteção Anti-Viés

### 14.1 Visão Geral

**Arquivo:** `lia-agent-system/app/shared/compliance/fairness_guard.py` (382 linhas)

O FairnessGuard é um middleware que intercepta queries antes do processamento pelos agentes, verificando indicadores de viés discriminatório. Quando detectado, retorna uma mensagem educativa em vez de processar a query.

### 14.2 Camada 1 — Filtro Regex (Viés Explícito)

**9 categorias discriminatórias com patterns regex compilados:**

| Categoria                | Patterns | Legislação Referenciada                    | Exemplo de Detecção                    |
|--------------------------|----------|---------------------------------------------|----------------------------------------|
| `genero`                 | 6        | Art. 5º CLT, LGPD                          | "apenas homens", "sexo masculino"      |
| `raca_etnia`             | 4        | CF Art. 5º, Lei 7.716/89                   | "somente brancos", "excluir negros"    |
| `idade`                  | 9        | Estatuto do Idoso, CLT                     | "máximo 35 anos", "excluir maiores de" |
| `religiao`               | 3        | CF Art. 5º VI                              | "apenas cristãos", "excluir ateus"     |
| `orientacao_sexual`      | 3        | STF ADO 26                                 | "apenas heterossexuais", "excluir gays"|
| `estado_civil`           | 3        | CLT                                        | "somente solteiros", "excluir casados" |
| `deficiencia`            | 4        | Lei 8.213/91, Lei 13.146/15               | "excluir deficientes", "sem PCD"       |
| `maternidade_paternidade`| 7        | CLT Art. 373-A, Lei 9.029/95              | "plano de ter filhos", "engravidar"    |
| `nacionalidade`          | 3        | CF Art. 5º                                 | "apenas brasileiros", "excluir estrangeiros"|

**Total: 42 patterns regex** distribuídos em 9 categorias.

**Cada categoria inclui:**
- `terms[]` — lista de patterns regex (compilados e cacheados em `_COMPILED_PATTERNS`)
- `message` — mensagem educativa personalizada com referência legal

### 14.3 Camada 2 — Léxico Implícito (Viés Sutil)

**Dicionário `IMPLICIT_BIAS_TERMS` — 11 termos com mensagens educativas:**

| Termo Detectado                      | Tipo de Viés                    | Mensagem (resumida)                                     |
|--------------------------------------|----------------------------------|---------------------------------------------------------|
| `boa aparencia`                      | Discriminação estética           | "Use critérios objetivos de apresentação profissional"  |
| `bairros nobres`                     | Discriminação socioeconômica     | "Considere critérios de disponibilidade ou mobilidade"  |
| `regiao nobre`                       | Discriminação socioeconômica     | "Considere critérios de disponibilidade ou mobilidade"  |
| `universidades de primeira linha`    | Elitismo acadêmico               | "Avalie competências e resultados"                      |
| `faculdade de ponta`                 | Elitismo acadêmico               | "Avalie competências e resultados"                      |
| `escola particular`                  | Discriminação socioeconômica     | "Avalie formação e competências"                        |
| `clube social`                       | Discriminação de classe          | "Pode configurar discriminação socioeconômica"          |
| `perfil adequado`                    | Viés inconsciente                | "Especifique competências objetivas"                    |
| `apresentacao pessoal`               | Discriminação estética           | "Use critérios objetivos"                               |
| `morar proximo`                      | Discriminação socioeconômica     | "Considere disponibilidade ou trabalho remoto"          |
| `boa familia`                        | Discriminação de origem          | "Use critérios profissionais"                           |

**Normalização:** `_normalize_text()` remove acentos via NFD para matching case-insensitive e accent-insensitive.

### 14.4 Camada 3 — LLM Judge (Opt-in)

**Ativação:** Variável de ambiente `FAIRNESS_LAYER3_ENABLED=true`
**Modelo:** Claude Sonnet
**Processo:** LLM revisa o output do agente antes de finalizar score
**Uso recomendado:** Clientes em segmentos regulados (financeiro, saúde)

### 14.5 FairnessCheckResult

**Dataclass de retorno:**

```python
@dataclass
class FairnessCheckResult:
    is_blocked: bool           # True se Camada 1 detectou viés explícito
    blocked_terms: List[str]   # Termos que causaram o bloqueio
    category: Optional[str]    # Categoria discriminatória (genero, idade, etc.)
    educational_message: str   # Mensagem educativa com base legal
    original_query: str        # Query original do recrutador
    confidence: float          # Confiança na detecção (0.0-1.0)
    soft_warnings: List[str]   # Avisos da Camada 2 (não bloqueantes)
```

### 14.6 Integração com Agentes

O FairnessGuard está integrado em **4 agentes** via `EnhancedAgentMixin`:
- Wizard Agent (criação de vagas)
- Talent Agent (funil de talentos)
- Jobs Management Agent (portfólio de vagas)
- Kanban Agent (pipeline)

**Ausente em 7 agentes:** Analytics, Automation, ATS Integration, Communication, Sourcing, Pipeline, Policy

### 14.7 Métricas

**Prometheus counter:** `fairness_blocks_total` — incrementado a cada bloqueio por categoria.
Exportada quando módulo de observabilidade está disponível (`_METRICS_AVAILABLE`).

---

## 15. Pre-Qualification Pipeline

### 15.1 PreQualificationService

**Arquivo:** `lia-agent-system/app/services/pre_qualification_service.py`

Serviço que executa triagem automática de candidatos antes da avaliação WSI completa, filtrando candidatos que não atendem requisitos mínimos.

**Critérios de pré-qualificação:**
- Requisitos obrigatórios da vaga (skills, experiência mínima, localização)
- Disponibilidade do candidato
- Match mínimo com a descrição da vaga

### 15.2 ScoreNormalizationService

**Arquivo:** `lia-agent-system/app/services/score_normalization_service.py`

Normaliza scores entre diferentes avaliadores e vagas para garantir comparabilidade:

**Fator de normalização:** `0.7 ≤ factor ≤ 1.3`
- Calculado como: `factor = max(0.7, min(1.3, raw_factor))`
- Previne que normalização distorça scores excessivamente
- Aplica-se a scores WSI e rubric para cada avaliador/vaga

---

## 16. Personalized Feedback Service

### 16.1 Visão Geral

**Arquivo:** `lia-agent-system/app/services/personalized_feedback_service.py`

Gera feedback personalizado para candidatos rejeitados, adaptando tom e conteúdo ao contexto.

### 16.2 3 Tons de Feedback

| Tom              | Quando usado                                  | Estilo                                                    |
|------------------|-----------------------------------------------|----------------------------------------------------------|
| `encouraging`    | Candidato com potencial, vaga muito sênior    | Destaca pontos fortes, sugere áreas de desenvolvimento   |
| `professional`   | Rejeição padrão por fit ou skills             | Objetivo, claro, com pontos positivos e gaps             |
| `constructive`   | Candidato com gaps significativos             | Foco em ações concretas de melhoria com recursos sugeridos|

### 16.3 Conteúdo do Feedback

O feedback personalizado inclui:
- Agradecimento pela participação no processo
- Pontos fortes identificados na avaliação
- Áreas de desenvolvimento (sem expor informações discriminatórias)
- Sugestões de próximos passos (cursos, certificações, etc.)
- Convite para futuras oportunidades

### 16.4 Compliance

- Feedback **nunca** inclui menção a categorias protegidas (FairnessGuard)
- PII masking aplicado antes de enviar ao LLM para geração
- Feedback registrado no audit trail para LGPD Art. 20

---

## 17. LGPD — Proteção de Dados Pessoais

### 17.1 Arquitetura LGPD

A plataforma implementa compliance LGPD em 6 pilares:

```
┌─────────────────────────────────────────────────────────────────┐
│                        LGPD COMPLIANCE                           │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────────┤
│Consent   │ PII      │ DSR      │ Data     │ Breach   │ DPO      │
│Mgmt      │ Masking  │ Export   │ Cleanup  │ Notify   │ Registry │
├──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│consent_  │pii_      │dsr_      │lgpd_     │lgpd_     │lgpd_     │
│checker   │masking   │export    │cleanup   │compliance│compliance│
│_service  │.py       │_service  │_service  │.py       │.py       │
└──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
```

### 17.2 ConsentCheckerService — Gate de Consentimento

**Arquivo:** `lia-agent-system/app/services/consent_checker_service.py`

Checagem obrigatória antes de qualquer operação que processe dados pessoais:

**Modos de operação:**
- `soft_warning` (default): Log de aviso quando consentimento ausente, mas permite prosseguir
- `hard_block`: Bloqueia operação completamente quando consentimento ausente

**Controle:** Variável de ambiente `LGPD_CONSENT_ABSENT_HARD_BLOCK`

**Consentimentos verificados:**
- Gravação de voz (WSI)
- Processamento por IA
- Retenção de dados por 180 dias
- Compartilhamento com ferramentas de terceiros (Pearch, etc.)

### 17.3 PII Masking

**Arquivo:** `lia-agent-system/app/shared/pii_masking.py`

**2 componentes:**

1. **`strip_pii_for_llm_prompt(text)`** — Remove PII antes de enviar ao LLM:
   - CPF, RG
   - Email, telefone
   - Endereço completo
   - Nome completo (quando identificável)

2. **`PIIMaskingFilter`** — Filtro de logging instalado em todos os workers:
   - Intercepta logs antes de escrita
   - Mascara PII automaticamente
   - Previne vazamento acidental em logs de aplicação

### 17.4 DSR Export Service — Portabilidade de Dados

**Arquivo:** `lia-agent-system/app/services/dsr_export_service.py`

Implementa LGPD Art. 18 V — Portabilidade de dados:

**Dados exportados:**
- Dados pessoais básicos (nome, email, telefone, localização, LinkedIn)
- Histórico de vagas e etapas (até 100 registros)
- Avaliações LIA (scores, recomendações, strengths, gaps — até 50 registros)
- Logs de consentimento LGPD
- Histórico de comunicações enviadas

**Dados NÃO exportados:**
- Dados de outros candidatos
- Dados internos de recrutadores
- Modelos proprietários LIA

**Formato:** JSON estruturado, legível por máquina e humano (`LIA DSR Export v1.0`)

**Endpoint:** `POST /api/v1/data-subject-requests` → tipo `portabilidade_dados`

### 17.5 LGPD Cleanup Service — Retenção de Dados

**Arquivo:** `lia-agent-system/app/services/lgpd_cleanup_service.py` (264 linhas)

**Política de retenção (`RETENTION_DAYS`):**

| Tipo de Dado           | Retenção | Ação após expiração                   |
|------------------------|----------|----------------------------------------|
| `rejected` candidates  | 90 dias  | Exclusão permanente (hard delete)      |
| `withdrawn` candidates | 90 dias  | Exclusão permanente (hard delete)      |
| `interview_notes`      | 180 dias | Exclusão permanente (hard delete)      |
| `screening_logs`       | 365 dias | Exclusão permanente (hard delete)      |
| `ai_logs`              | 365 dias | Exclusão de registros `AiConsumption`  |

**Mecanismo:**
1. `schedule_deletion_for_candidate()` — Seta `scheduled_deletion_at` no registro do candidato quando rejeitado/desistente
2. `run_cleanup(dry_run=True|False)` — Job diário que deleta registros expirados
3. **DRY-RUN obrigatório:** Sempre rodar com `dry_run=True` primeiro para validar escopo
4. **Audit trail:** Toda exclusão é logada com `candidate_id`, `company_id`, `scheduled_deletion_at`
5. **Multi-tenant:** Nunca cruza dados entre empresas (scoped por `company_id`)

**Tabelas limpas:**
- `candidates` — registros com `scheduled_deletion_at ≤ now`
- `vacancy_candidates` — registros associados com `scheduled_deletion_at ≤ now`
- `ai_consumption` — logs de IA com `scheduled_deletion_at ≤ now`

### 17.6 LGPD Compliance API

**Arquivo:** `lia-agent-system/app/api/v1/lgpd_compliance.py` (916 linhas)

**3 módulos principais:**

| Módulo                           | Endpoints | Artigos LGPD           |
|----------------------------------|-----------|------------------------|
| DPO Registry                     | CRUD      | Art. 41                |
| Breach Notifications             | CRUD + notify | Art. 48 (48h)      |
| Automated Decision Explanations  | CRUD + review | Art. 20            |

**API Endpoints:**

```
GET    /api/v1/lgpd/stats                              # Estatísticas LGPD consolidadas
GET    /api/v1/lgpd/dpo                                # Listar registros DPO
POST   /api/v1/lgpd/dpo                                # Registrar DPO
GET    /api/v1/lgpd/dpo/{company_id}                   # DPO por empresa
GET    /api/v1/lgpd/breaches                            # Listar incidentes
POST   /api/v1/lgpd/breaches                            # Registrar incidente
POST   /api/v1/lgpd/breaches/{id}/notify-anpd           # Notificar ANPD (48h)
POST   /api/v1/lgpd/breaches/{id}/notify-subjects       # Notificar titulares
POST   /api/v1/lgpd/breaches/{id}/resolve               # Resolver incidente
GET    /api/v1/lgpd/decisions                            # Decisões automatizadas
POST   /api/v1/lgpd/decisions                            # Registrar decisão
POST   /api/v1/lgpd/decisions/{id}/request-review        # Solicitar revisão humana
POST   /api/v1/lgpd/decisions/{id}/complete-review       # Completar revisão
```

**Estatísticas LGPD (`LGPDComplianceStats`):**
- `dpo_registered` / `dpo_active`
- `total_breaches` / `open_breaches` / `breaches_pending_anpd`
- `total_automated_decisions` / `pending_human_reviews` / `completed_human_reviews`

### 17.7 Portal do Titular

**Endpoint base:** `/api/v1/data-subject-requests/`

**7 tipos de requisição suportados:**
1. Acesso aos dados (Art. 18 I-II)
2. Correção de dados (Art. 18 III)
3. Anonimização (Art. 18 IV)
4. Portabilidade (Art. 18 V) — via DSR Export Service
5. Eliminação de dados (Art. 18 VI)
6. Informação sobre compartilhamento (Art. 18 VII)
7. Revisão de decisão automatizada (Art. 20)

**Fluxo de atendimento:**
```
Candidato solicita → Sistema registra → Atribuição a responsável →
Verificação de identidade → Processamento → Conclusão → Notificação ao candidato
```

**APIs do Portal do Titular:**
```
GET    /api/v1/data-subject-requests/                     # Lista requisições
POST   /api/v1/data-subject-requests/                     # Criar requisição
GET    /api/v1/data-subject-requests/{id}                 # Detalhes
PUT    /api/v1/data-subject-requests/{id}/assign          # Atribuir responsável
PUT    /api/v1/data-subject-requests/{id}/verify-identity # Verificar identidade
PUT    /api/v1/data-subject-requests/{id}/process         # Processar
PUT    /api/v1/data-subject-requests/{id}/complete        # Concluir
PUT    /api/v1/data-subject-requests/{id}/reject          # Rejeitar
GET    /api/v1/data-subject-requests/stats                # Estatísticas
GET    /api/v1/data-subject-requests/export               # Exportar
```

### 17.8 Mapeamento de Dados (80+ tabelas)

**Referência:** `docs/compliance/WEDOTALENT_COMPLIANCE_ARCHITECTURE.md` → Seção 3

**Classificação de dados (5 níveis):**

| Classificação       | Descrição                  | Exemplos                          |
|---------------------|----------------------------|-----------------------------------|
| Público             | Dados não sensíveis        | Nome da empresa, cargo            |
| Interno             | Uso interno apenas         | Métricas, configurações           |
| Confidencial        | Dados de negócio           | Candidatos, vagas                 |
| Sensível (LGPD)     | Dados pessoais             | CPF, email, telefone              |
| Altamente Sensível  | Dados especiais            | Saúde, biometria, raça            |

**Tabelas de Candidatos (Sensíveis — LGPD):**

| Tabela                   | Dados                                  | Retenção              |
|--------------------------|----------------------------------------|-----------------------|
| `candidates`             | Nome, email, telefone, CPF, endereço   | Conforme política     |
| `candidate_experiences`  | Histórico profissional                 | Conforme política     |
| `candidate_education`    | Formação acadêmica                     | Conforme política     |
| `candidate_attachments`  | CVs, documentos                        | Conforme política     |
| `vacancy_candidates`     | Associação vaga-candidato              | Vida da vaga + 2 anos |

**Tabelas de IA e Decisões Automatizadas:**

| Tabela                                | Dados                         | Retenção    |
|---------------------------------------|-------------------------------|-------------|
| `ai_inference_logs`                   | Logs de inferência IA         | 2 anos      |
| `automated_decision_explanations`     | Explicações de decisão        | 5 anos      |
| `lia_opinions`                        | Pareceres da LIA              | 5 anos      |
| `lia_profile_analyses`                | Análises de perfil            | 5 anos      |
| `bias_audit_reports`                  | Auditorias de viés            | 7 anos      |
| `calibration_feedback`                | Feedback de calibração        | 2 anos      |
| `model_evaluations`                   | Avaliações de modelo          | 2 anos      |

**Tabelas de Compliance e Auditoria:**

| Tabela                                | Dados                         | Retenção    |
|---------------------------------------|-------------------------------|-------------|
| `sox_audit_logs`                      | Logs SOX-compliant            | 7 anos      |
| `compliance_control_library`          | 218 controles (7 frameworks)  | Permanente  |
| `compliance_health_check_items`       | 242 itens de verificação      | Permanente  |
| `data_subject_requests`               | Requisições de titulares      | 5 anos      |
| `consent_records`                     | Registros de consentimento    | 5 anos      |
| `breach_notifications`                | Notificações de incidente     | 10 anos     |

---

## 18. EU AI Act — Conformidade com IA de Alto Risco

### 18.1 Classificação do Sistema

**Documento:** `docs/compliance/FRIA_WSI.md` (355 linhas)

**Classificação EU AI Act:** Sistema de IA de alto risco — Anexo III, ponto 4
("Employment, workers management and access to self-employment")

O WSI (Voice Screening Interview) é classificado como alto risco por ser um sistema de IA usado para recrutamento e seleção de candidatos.

### 18.2 FRIA — Avaliação de Impacto em Direitos Fundamentais

**6 Direitos Fundamentais Avaliados:**

| Direito             | Risco Identificado                                      | Mitigação Implementada                                   | Risco Residual |
|---------------------|--------------------------------------------------------|----------------------------------------------------------|----------------|
| Dignidade humana    | Avaliação desumanizante por voz sem contexto pessoal    | Blocos estruturados com abertura humanizada               | Baixo          |
| Não-discriminação   | Viés em ASR para sotaques regionais, gagueira           | FairnessGuard 3 camadas; Bias Audit Four-Fifths Rule     | Médio          |
| Privacidade         | Coleta de dados biométricos (voz), processamento LLM    | PII masking; retenção 180 dias; anonimização             | Baixo          |
| Devido processo     | Decisão adversa sem possibilidade de contestação        | HITL path; LGPD Art. 20 endpoint ativo; SLA 15 dias     | Baixo          |
| Transparência       | Candidato não sabe que é avaliado por IA                | ConsentCheckerService Gate 1 obrigatório                  | Baixo          |
| Equidade de acesso  | Candidatos sem microfone de qualidade penalizados       | Score de qualidade de áudio não penaliza resposta        | Médio          |

### 18.3 Artigos EU AI Act Aplicáveis

| Artigo    | Requisito                          | Implementação na Plataforma                              |
|-----------|-------------------------------------|----------------------------------------------------------|
| Art. 9    | Gestão de riscos contínua          | FRIA documentado; Bias Audit mensal; Model Drift diário |
| Art. 10   | Dados de treino e auditoria        | BiasAuditService; TrainingDataService                    |
| Art. 13   | Transparência para candidatos      | Aviso no início da chamada; ConsentCheckerService        |
| Art. 14   | Supervisão humana                  | HITL path obrigatório para decisões adversas             |
| Annex III | Classificação alto risco           | Sistema WSI classificado como Annex III ponto 4          |

### 18.4 HITL (Human-in-the-Loop) — Triggers Automáticos

**Arquivo:** `app/services/hitl_service.py`

O HITL path é acionado automaticamente nas seguintes condições:

| Trigger                                   | Condição                              | Ação                                        |
|-------------------------------------------|---------------------------------------|----------------------------------------------|
| Score na zona cinzenta                    | WSI score entre 40–60                 | Enviar para revisão de recrutador sênior     |
| FairnessGuard Camada 2 ou 3 sinalizada   | Viés implícito ou LLM Judge flag     | Revisão obrigatória antes de finalizar       |
| Candidato solicita revisão               | LGPD Art. 20 endpoint                 | SLA 15 dias úteis                            |
| Qualidade de áudio abaixo do threshold   | Métricas de áudio do Deepgram         | Fallback para avaliação textual              |

**Notificação:** Recrutador recebe Bell (in-app) + Teams com link direto para revisão.

**Pontos de Intervenção Humana e SLAs:**

| Gatilho                                | Ação Requerida            | SLA              |
|----------------------------------------|---------------------------|------------------|
| Confiança < 70%                        | Revisão obrigatória       | 24 horas         |
| Decisão de rejeição final              | Aprovação gerencial       | 48 horas         |
| Score de viés elevado (FairnessGuard)  | Análise de compliance     | 72 horas         |
| Reclamação do candidato (Art. 20)      | Investigação DPO          | 5 dias úteis     |
| Auditoria de viés periódica            | Revisão completa          | Mensal           |

### 18.5 FRIA — Riscos Residuais

**Documento:** `docs/compliance/FRIA_WSI.md` → Seção 9

Riscos remanescentes **após** aplicação de todas as salvaguardas. Metodologia: Probabilidade (1–5) × Impacto (1–5) = Score. Aceitável ≤ 9.

| # | Risco Residual                                                                      | P×I  | Classificação |
|---|--------------------------------------------------------------------------------------|------|---------------|
| R1| Viés de ASR para sotaques muito específicos (interior Norte/Nordeste)                | 8    | Aceitável     |
| R2| Variância alta em avaliação de soft skills (Bloco 4 WSI)                             | 6    | Aceitável     |
| R3| Candidato com gagueira leve não identificado pelo filtro de qualidade de áudio       | 8    | Aceitável     |
| R4| Prompt injection via resposta do candidato não detectado por FairnessGuard           | 5    | Aceitável     |
| R5| Deriva de modelo LLM entre versões sem atualização de rubrica                        | 6    | Aceitável     |
| R6| Ausência de conteúdo em bloco WSI interpretada como nota baixa                       | 6    | Aceitável     |
| R7| Candidatos inexperientes em entrevistas por voz com desempenho abaixo do potencial   | 9    | Aceitável     |

**Nenhum risco residual classificado como Inaceitável (≥ 15).**

**Plano de Tratamento:**

| Risco | Ação de Mitigação                                                              | Prazo   |
|-------|---------------------------------------------------------------------------------|---------|
| R1    | Ampliar golden dataset de sotaques em `tests/fixtures/golden_dataset.py`       | Q2 2026 |
| R7    | Guia de orientação pré-entrevista enviado 24h antes via WhatsApp/e-mail        | Q2 2026 |
| R3    | Detecção de gagueira leve na camada de qualidade de áudio; HITL automático     | Q3 2026 |
| R5    | Benchmark de modelo na suite de CI/CD para regressão cross-versão              | Q2 2026 |

### 18.6 Declaração de Conformidade EU AI Act

**Documento:** `docs/compliance/FRIA_WSI.md` → Seção 11

O sistema WSI é aprovado para uso com as seguintes condições obrigatórias:

1. **Consentimento explícito** do candidato antes de cada sessão (via `ConsentCheckerService`)
2. **HITL ativo**: revisão humana obrigatória para scores em zona cinzenta (40–60)
3. **Bias Audit mensal**: frequência mínima conforme Four-Fifths Rule
4. **Não exclusividade**: score WSI não pode ser o único critério de eliminação
5. **Transparência**: candidatos informados da utilização de IA no início da sessão

**Documento de referência:** RIPD-LIA-WSI-2026-001 (validade 12 meses, próxima revisão 03/2027)

**Gatilhos de revisão antecipada:**
- Mudança de modelo LLM
- Novo regulamento EU AI Act
- Resultado adverso em Bias Audit
- Incidente de discriminação reportado

---

## 19. Compliance Multi-Framework

### 19.1 Compliance Health Check

**Documento:** `docs/compliance/WEDOTALENT_COMPLIANCE_ARCHITECTURE.md` (1678 linhas)
**Rota admin:** `/compliance/health-check`

Dashboard interativo com **242 itens** de verificação distribuídos em **7 frameworks regulatórios:**

| Framework         | Itens | Escopo                                                |
|-------------------|-------|-------------------------------------------------------|
| ISO 27001:2022    | 96    | Controles de segurança da informação (A.5–A.8)       |
| SOC 2 Type II     | 61    | Trust Services Criteria (CC1–CC9, A1, C1, PI1, P1–P8)|
| SOX 404           | 27    | Controles internos, ITGCs, SoD, evidências            |
| LGPD              | 17    | Princípios, direitos do titular, obrigações           |
| BCB 498/2025      | 13    | Seguro cibernético, coberturas obrigatórias           |
| EU AI Act         | 13    | Governança de IA, alto risco, transparência           |
| NYC LL144         | 11    | Auditoria de viés em AEDT, métricas de impacto       |
| **TOTAL**         | **242** | **100% sincronizado com biblioteca de controles**   |

### 19.2 Funcionalidades do Health Check

- Verificação interativa de status por item (compliant / partial / non_compliant / not_applicable)
- Links para documentação oficial de cada framework
- Sincronização automática com biblioteca de controles (`/sync-from-library`)
- Filtros por framework, status e prioridade
- Estatísticas em tempo real por categoria
- Mapeamento de prioridade (mandatory → critical, optional → medium)

**APIs:**
```
GET    /api/v1/health-check/items                # Lista todos os itens
GET    /api/v1/health-check/items/{id}           # Item específico
PUT    /api/v1/health-check/items/{id}           # Atualiza status
GET    /api/v1/health-check/summary              # Resumo por framework
POST   /api/v1/health-check/sync-from-library    # Sincroniza da biblioteca
```

### 19.3 SOX — Trilha de Auditoria

**Tabela:** `sox_audit_logs`
**Retenção:** 7 anos (financeiro)

Logs SOX-compliant para todas as operações sensíveis:
- Movimentação de candidatos entre etapas
- Alterações em políticas de contratação
- Aprovações de vagas com salário acima de threshold
- Exclusão de registros (LGPD cleanup)

**8 Controles SOX implementados:**

| ID     | Controle                    | Evidência                      |
|--------|------------------------------|--------------------------------|
| SOX-01 | Segregação de funções        | `sod_roles`, `sod_conflicts`   |
| SOX-02 | Logs imutáveis               | `sox_audit_logs` (7 anos)      |
| SOX-03 | Controle de acesso           | RBAC + MFA                     |
| SOX-04 | Aprovação de transações      | Workflow de `approvals`        |
| SOX-05 | Trilha de auditoria          | Todos os registros             |
| SOX-06 | Backup e recuperação         | DR automático                  |
| SOX-07 | Gestão de mudanças           | Git + deploy controlado        |
| SOX-08 | Monitoramento de violações   | `sod_violations`               |

### 19.3.1 Logs de Decisão Automatizada

**Tabela:** `automated_decision_explanations`
**Referência:** LGPD Art. 20, EU AI Act Art. 13

| Campo                  | Descrição                            | Obrigatório |
|------------------------|--------------------------------------|-------------|
| `decision_id`          | ID único da decisão                  | Sim         |
| `agent_name`           | Agente responsável                   | Sim         |
| `decision_type`        | Tipo (screening, ranking, etc.)      | Sim         |
| `input_data`           | Dados de entrada (hash, sem PII)     | Sim         |
| `output`               | Resultado da decisão                 | Sim         |
| `confidence`           | Score de confiança (0–1)             | Sim         |
| `reasoning`            | Explicação em linguagem natural      | Sim         |
| `criteria_used`        | Critérios utilizados                 | Sim         |
| `criteria_ignored`     | Critérios desconsiderados            | Sim         |
| `human_review_required`| Flag para revisão humana             | Sim         |
| `model_version`        | Versão do modelo                     | Sim         |
| `timestamp`            | Data/hora                            | Sim         |

### 19.4 SoD — Segregação de Funções

**Tabelas:** `sod_roles`, `sod_conflicts`, `sod_violations`
**Rota admin:** `/compliance/auditoria` → submódulo SoD

Detecção em tempo real de conflitos de segregação de funções:
- Definição de papéis e funções incompatíveis
- Monitoramento contínuo de violações
- Aprovação de exceções com justificativa

### 19.5 BCB 498 — Seguro Cibernético

**Tabelas:** `insurance_policies`, `insurance_coverages`, `insurance_claims`

Aplicável a clientes instituições financeiras reguladas pelo Banco Central:
- Controles de qualidade e validação de modelos de IA
- Documentação de governança de algoritmos
- Trilha de auditoria completa de decisões automatizadas
- Gestão de apólices de seguro cibernético

**12 Controles BCB implementados:**

| ID     | Controle                       | Evidência                      |
|--------|--------------------------------|--------------------------------|
| BCB-01 | Apólice de seguro              | `insurance_policies`           |
| BCB-02 | Cobertura data breach          | `insurance_coverages`          |
| BCB-03 | Cobertura ransomware           | `insurance_coverages`          |
| BCB-04 | Cobertura business interruption| `insurance_coverages`          |
| BCB-05 | Cobertura regulatory defense   | `insurance_coverages`          |
| BCB-06 | Cobertura cyber liability      | `insurance_coverages`          |
| BCB-07 | Cobertura forensics            | `insurance_coverages`          |
| BCB-08 | Cobertura notification costs   | `insurance_coverages`          |
| BCB-09 | Cobertura crisis management    | `insurance_coverages`          |
| BCB-10 | Alertas de renovação           | Sistema automático             |
| BCB-11 | Registro de sinistros          | `insurance_claims`             |
| BCB-12 | Dashboard de compliance        | `/insurance/bcb-compliance`    |

**APIs:** 19 endpoints em `/api/v1/insurance/`

### 19.6 ISO 22301 — Continuidade de Negócios

**Tabelas:** `business_processes`, `disaster_recovery_plans`, `continuity_tests`

- BIA (Business Impact Analysis) por processo crítico
- DRP (Disaster Recovery Plans)
- Testes de continuidade com registro

**APIs:** 12 endpoints em `/api/v1/continuity/`

### 19.7 Trust Center

**Rota admin:** `/compliance/trust-center`

Portal público de confiança para clientes:

| Submódulo          | Público   | Conteúdo                          |
|--------------------|-----------|-----------------------------------|
| Certificações      | Externo   | Selos, certificados               |
| Subprocessadores   | Externo   | Lista de terceiros                |
| Recursos           | Externo   | Políticas, whitepapers            |

---

## 20. Framework de Teste de Viés — Bias Audit Service

### 20.1 Visão Geral

**Arquivo:** `lia-agent-system/app/services/bias_audit_service.py` (290 linhas)

Calcula adverse impact real usando dados de `RubricEvaluation` + `Candidate` por vaga, retornando apenas estatísticas agregadas sem PII (LGPD-safe).

### 20.2 Four-Fifths Rule

**Princípio:** Se a taxa de aprovação do grupo com menor taxa é inferior a 4/5 (80%) da taxa do grupo com maior taxa, existe adverse impact.

**Constantes:**
- `APPROVAL_THRESHOLD = 60.0` — Score mínimo para considerar candidato "aprovado"
- `FOUR_FIFTHS_THRESHOLD = 0.80` — Limiar da Four-Fifths Rule

**Fórmula:**
```
adverse_impact_ratio = taxa_menor_grupo / taxa_maior_grupo
se ratio < 0.80 → alert_level = "warning"
se ratio ≥ 0.80 → alert_level = "ok"
```

### 20.3 4 Dimensões Auditadas

| Dimensão      | Grupos                                       | Função de Classificação                   |
|---------------|----------------------------------------------|-------------------------------------------|
| `gender`      | masculino, feminino, não informado            | `candidate.gender` (lowercase)            |
| `age_group`   | <30, 30-44, 45+                              | `_age_group(candidate.date_of_birth)`     |
| `disability`  | com PCD, sem PCD                              | `candidate.has_disability` (boolean)      |
| `region`      | por `location_state`                          | `candidate.location_state`                |

**Faixas etárias (screening-compliance §4):**
- `AGE_GROUP_YOUNG` = "<30"
- `AGE_GROUP_MID` = "30-44"
- `AGE_GROUP_SENIOR` = "45+"

### 20.4 DTOs de Resultado

**`DemographicAuditResult`:**
```python
dimension: str                    # "gender" | "age_group" | "disability" | "region"
groups: Dict[str, Dict]           # {label: {"count": N, "approved": N, "rate": float}}
adverse_impact_ratio: float       # menor_taxa / maior_taxa
below_threshold: bool             # ratio < 0.80
alert_level: str                  # "ok" | "warning"
```

**`BiasAuditReport`:**
```python
job_id: str
evaluated_at: datetime
total_candidates: int
dimensions: List[DemographicAuditResult]
has_alerts: bool                  # True se qualquer dimensão below_threshold
```

### 20.5 Snapshot Histórico

**Modelo:** `BiasAuditSnapshot`

Snapshots de auditorias são salvos para compliance SOX/ISO 27001:
- Frequência: auditoria mensal automática
- Retenção: 7 anos (tabela `bias_audit_reports`)
- Cada snapshot inclui todas as 4 dimensões com contagens e ratios

### 20.6 Referências de Compliance

| Referência           | Requisito                                            |
|---------------------|------------------------------------------------------|
| dei-fairness §4     | Four-Fifths Rule — adverse_impact_ratio ≥ 0.80      |
| LGPD Art. 5         | Dados pessoais / dado sensível — agregação sem PII  |
| EU AI Act Art. 10   | Dados de treino e auditoria                          |
| SOX / ISO 27001     | Evidência de fairness com dados reais                |

---

## 21. Model Drift e Monitoramento Contínuo

### 21.1 Monitoramento de Drift

**Referência:** `docs/compliance/FRIA_WSI.md` → Seção 7.1

**Triggers monitorados:**
- Desvio de score médio (WSI / LIA Score)
- Taxa de aprovação por grupo demográfico
- Custo por avaliação
- Latência P95 das chamadas LLM
- Variância de scores entre avaliações do mesmo candidato

### 21.2 Agendamento e Cadência de Auditoria

| Auditoria                  | Frequência  | Referência FRIA              | Responsável          |
|----------------------------|-------------|-------------------------------|----------------------|
| Model Drift batch job      | Diário      | `drift.run_batch` Celery Beat | Automático           |
| Bias Audit (Four-Fifths)   | Mensal      | FRIA §7.2                     | Automático + DPO     |
| Red Team                   | Semestral   | FRIA §7.3                     | Equipe interna + ext.|
| Revisão de Prompts         | Trimestral  | FRIA §7.4                     | Produto + IA         |
| FRIA revisão completa      | Anual       | FRIA §8                       | DPO + CTO            |

**Alerta automático:** Bell + Teams quando 2+ triggers ativos (`drift_alert_service`)

### 21.3 Red Team — Teste de Adversário

**Referência:** `docs/compliance/FRIA_WSI.md` → Seção 7.3

- **Execução:** Equipe interna + auditoria externa independente
- **Escopo:** Injeção de candidatos fictícios com características protegidas para verificar viés de output
- **Artefatos de teste:** `tests/fairness/test_four_fifths_rule.py` + `tests/fixtures/golden_dataset.py`
- **Resultado:** Documentado em `docs/compliance/red_team_YYYY_S[1|2].md (nomeação por ano/semestre)`

### 21.4 Revisão de Prompts

**Referência:** `docs/compliance/FRIA_WSI.md` → Seção 7.4

- **Escopo:** Auditoria dos system prompts WSI em `app/domains/cv_screening/agents/system_prompt.py`
- **Verificações:** Linguagem neutra, ausência de critérios implicitamente discriminatórios
- **Resultado:** Documentado em `docs/compliance/AUDITORIA_SYSTEM_PROMPTS_YYYY_MM.md (nomeação por ano/mês)`

### 21.5 Ações de Remediação

Quando drift é detectado:
1. Alerta automático para equipe de IA
2. Snapshot de comparação (antes/depois)
3. Revisão manual dos triggers ativos
4. Se necessário: recalibração de thresholds ou rollback de modelo
5. Registro em `docs/compliance/incidentes/` se classificado como incidente

---

## 22. Taxonomia de Incidentes

### 22.1 Gestão de Incidentes

**Rota admin:** `/compliance/monitoramento` → submódulo Incidentes

| Campo            | Descrição                                 |
|------------------|-------------------------------------------|
| Ticket ID        | Identificador único do incidente          |
| Severidade       | Critical / High / Medium / Low            |
| Tipo             | Security / Compliance / Operational / AI  |
| Status           | Open / Investigating / Resolved / Closed  |
| RCA              | Root Cause Analysis (obrigatório ao fechar)|
| Responsável      | Atribuído via workflow                    |
| Tabela DB        | `compliance_incidents` (auditável SOX)    |

### 22.2 Incidentes de IA

Tipos específicos para a plataforma LIA:

| Tipo de Incidente           | Exemplo                                         | Severidade Default |
|-----------------------------|--------------------------------------------------|--------------------|
| Viés detectado pós-produção | Four-Fifths Rule violada em auditoria mensal     | High               |
| Model drift significativo   | Score médio WSI desviou >15% em 30 dias          | High               |
| FairnessGuard bypass        | Query discriminatória não bloqueada              | Critical           |
| PII leak em logs            | Dados pessoais identificados em log de produção  | Critical           |
| Circuit breaker persistente | Serviço OPEN por >1 hora sem recovery            | Medium             |
| LLM hallucination           | Resposta factualmente incorreta da LIA           | Medium             |
| Consent violation           | Processamento sem consentimento registrado       | High               |
| Prompt injection            | Score alterado por resposta maliciosa do candidato| Critical           |
| Adverse impact < 0.65       | Abaixo do limiar NYC LL144 em qualquer dimensão  | Critical           |

### 22.3 Definição de Incidente Grave (EU AI Act Art. 73)

**Referência:** `docs/compliance/FRIA_WSI.md` → Seção 10.1

Um incidente no sistema WSI é classificado como **grave** se:
- Candidato eliminado por decisão automatizada com evidência de discriminação por critério protegido
- Taxa de adverse impact ratio < 0.65 em qualquer dimensão
- Falha de segurança com exposição de dados biométricos de voz
- Score de candidato alterado indevidamente por prompt injection confirmado

### 22.4 Fluxo de Resposta a Incidentes

**Referência:** `docs/compliance/FRIA_WSI.md` → Seção 10.2

```
Detecção (Sistema / Reclamação)
    ↓
T+0h:  Registrar incidente em #compliance-incidents (Teams) + criar ticket
    ↓
T+4h:  DPO notificado — avaliação de gravidade (grave / não grave)
    ↓
T+24h: Se grave → Contenção imediata (suspender avaliações da empresa afetada)
    ↓
T+72h: Análise de causa raiz (engenharia + IA)
    ↓
T+15d: Notificação ao regulador competente (ANPD / autoridade EU AI Act)
    ↓
T+30d: Relatório de incidente final + plano de correção
    ↓
T+60d: Verificação de eficácia das correções aplicadas
```

### 22.5 Contatos e Responsabilidades

| Papel          | Responsabilidade                                  | Canal                           |
|----------------|---------------------------------------------------|----------------------------------|
| DPO            | Notificação regulatória, comunicação ao titular   | `privacidade@wedotalent.com.br` |
| CISO           | Contenção técnica, análise forense                | Slack `#security-incidents`     |
| Engenharia IA  | Análise de causa raiz, correção de modelo         | Jira projeto `LIA-COMPLIANCE`  |
| Jurídico       | Avaliação de responsabilidade civil/regulatória   | `juridico@wedotalent.com.br`   |

### 22.6 Breach Notification (LGPD Art. 48)

**Arquivo:** `lia-agent-system/app/api/v1/lgpd_compliance.py`

Incidentes de segurança que envolvem dados pessoais seguem fluxo LGPD:

| Etapa                     | Prazo           | Responsável         |
|---------------------------|-----------------|---------------------|
| Detecção e registro       | Imediato        | Sistema automático  |
| Classificação de impacto  | 4 horas         | DPO / Segurança     |
| Notificação ANPD          | 48 horas (legal)| DPO                 |
| Notificação dos titulares | 5 dias úteis    | DPO + Comunicação   |
| Resolução e RCA           | 30 dias         | Equipe responsável  |

**Notificação ao titular (Art. 48):**
- Canal: e-mail registrado + notificação no portal do candidato
- Conteúdo obrigatório: natureza dos dados, medidas adotadas, DPO de contato, data do incidente

### 22.7 Registro de Incidentes

Todos os incidentes (graves e não graves) registrados em:
- `docs/compliance/incidentes/INCIDENTE_<ANO>_<SEQ>.md`
- Banco de dados: tabela `compliance_incidents` (auditável SOX/ISO 27001, retenção 7 anos)

---

## 23. Production Readiness

### 23.1 Checklist de Prontidão

Baseado nos 242 itens do Compliance Health Check e nas 13 Crenças do WeDO Talent Guide v3.3:

**Infraestrutura:**

| Item                        | Status      | Arquivo/Serviço                                |
|-----------------------------|-------------|------------------------------------------------|
| Circuit breakers (12)       | Implementado| `app/shared/resilience/circuit_breaker.py`     |
| Token tracking / limites    | Implementado| `app/services/token_tracking_service.py`       |
| Métricas Prometheus         | Implementado| `app/observability/metrics.py`                 |
| Redis cache (TTL config.)   | Implementado| CascadedRouter Tier 2                          |
| pgvector semantic cache     | Implementado| CascadedRouter Tier 3                          |
| Rate limiting               | Configurado | `DEFAULT_LIMITS` no TokenTrackingService       |
| Audit logging (SOX)         | Implementado| `sox_audit_logs` table                         |

**Compliance:**

| Item                                | Status         | Arquivo/Serviço                               |
|--------------------------------------|----------------|------------------------------------------------|
| FairnessGuard (3 camadas)           | Parcial (4/11) | `app/shared/compliance/fairness_guard.py`      |
| Bias Audit (Four-Fifths Rule)       | Implementado   | `app/services/bias_audit_service.py`           |
| PII Masking (2 componentes)         | Implementado   | `app/shared/pii_masking.py`                    |
| Consent Checker (Gate 1)            | Implementado   | `app/services/consent_checker_service.py`      |
| LGPD Cleanup (daily job)            | Implementado   | `app/services/lgpd_cleanup_service.py`         |
| DSR Export (portabilidade)          | Implementado   | `app/services/dsr_export_service.py`           |
| HITL path (4 triggers)             | Implementado   | `app/services/hitl_service.py`                 |
| FRIA documentado                    | Implementado   | `docs/compliance/FRIA_WSI.md`                  |
| Health Check (242 itens, 7 FW)     | Implementado   | `docs/compliance/WEDOTALENT_COMPLIANCE_ARCHITECTURE.md` |
| Anti-sycophancy (11 agentes)       | Implementado   | System prompts de todos os agentes             |

**Governança de Agentes:**

| Item                               | Status       | Arquivo/Serviço                                  |
|-------------------------------------|-------------|--------------------------------------------------|
| EnhancedAgentMixin (5 etapas)      | Implementado| `libs/agents-core/lia_agents_core/enhanced_agent_mixin.py` |
| AutonomyEngine (3 níveis)          | Implementado| `libs/agents-core/lia_agents_core/autonomy_engine.py`      |
| LongTermMemory (4 tipos)           | Implementado| `libs/agents-core/lia_agents_core/long_term_memory.py`     |
| LearningExtractor (3 categorias)   | Implementado| `libs/agents-core/lia_agents_core/learning_extractor.py`   |
| TrainingDataService (3 formatos)   | Implementado| `app/services/training_data_service.py`          |
| ConfidencePolicyService            | Implementado| `app/services/confidence_policy_service.py`      |

### 23.2 Itens Pendentes para Produção

| Item                                    | Prioridade | Complexidade |
|----------------------------------------|------------|-------------|
| FairnessGuard em todos os 11 agentes   | P0         | Baixa       |
| Guardrail automatizado anti-sycophancy | P1         | Média       |
| JobReportModal com dados reais (backend)| P1         | Média       |
| WSI Voice (real, não text-only)        | P2         | Alta        |
| Audit trail centralizado (SOX/ISO)     | P1         | Média       |
| Dashboard de Model Drift               | P2         | Média       |
| Streaming de pensamentos ReAct via WS  | P3         | Média       |

---

## 24. Limitações, Dívidas Técnicas e Funcionalidades Incompletas

### 24.1 Processamento Local vs IA

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

### 24.2 Fallbacks Hardcoded

1. **Orchestrator fallback** — Se LLM falha, retorna: "Olá! Sou a LIA, sua assistente de recrutamento. Recebi sua mensagem sobre '{msg[:50]}..'" com 3 sugestões fixas
2. **CascadedRouter fallback** — Se nenhum tier resolve, retorna clarificação com 6 opções fixas
3. **VectorSemanticCache** — Inicialização graciosa; se pgvector indisponível, pula silenciosamente
4. **PlanDetector** — Falha silenciosa via try/except (non-blocking)
5. **CircuitBreaker** — Fallback configurável por circuit; se não definido, lança `CircuitBreakerError`
6. **Guardrails** — 3 camadas de fallback (AutonomyEngine → DB → lista estática)

### 24.3 Detecção de Intenção por Keywords

- `isGenericQuestion()` — 5 regex + 46 keywords de busca; frágil para termos novos
- `analysisCommands[]` — 8 padrões fixos de string matching
- `detect_command_type()` — keywords por KanbanCommandType; pode falhar para variações
- `_TECHNICAL_PATTERNS` — 5 padrões de string matching para detecção de resposta técnica

### 24.4 Cache

- **Tier 1 (LRU):** In-process, não distribuído entre workers; eviction FIFO
- **Tier 2 (Redis):** Implementado via `SemanticCache` com TTL configurável
- **Response Cache:** Funcional, mas sem invalidação automática por eventos (ex: novo candidato adicionado)

### 24.5 Funcionalidades Incompletas

1. **handleOpenRubricAnalysis orphaned** — Função em `candidates-page.tsx` (linha 6424) sem call sites; modal ainda renderiza mas não é acessível via botão
2. **JobReportModal com dados mock** — Dados hardcoded no frontend (funnelMetrics, channelPerformance, timeline, budget); sem integração com backend real
3. **WSI Voice** — Não implementado; WSI é text-only
4. **Calibração limitada** — Implementada no frontend sem agente ReAct dedicado; depende 100% do Pearch AI
5. **Arquivo monolítico** — `candidates-page.tsx` tem 10.398 linhas; `lia-api.ts` tem 4.943 linhas
6. **Notificações** — `JobCreatedNotificationRequest` suporta email + Teams; WhatsApp ausente

### 24.6 Dívidas Técnicas

1. **IntentRouter legado** — Coexiste com LLM Cascade como fallback; duplicação de lógica
2. **Mapeamento agent_type → domain** — Hardcoded em `AGENT_TYPE_TO_DOMAIN`; sem registro dinâmico
3. **AgentFactory vs get_agent** — Dois padrões coexistem; `get_agent()` NÃO é session-safe mas é usado em código legado
4. **PolicyEngine** — DB service pode ser `None`; validação pode falhar silenciosamente
5. **Detecção de resposta técnica** — String matching (`_TECHNICAL_PATTERNS`); frágil com novas mensagens
6. **Escopo GLOBAL** — `scope_config.py` limita a apenas `generate_report` + `schedule_report`, mas o chat-page envia tudo para o Orchestrator que ignora scope na execução
7. **Circuit breaker dual** — Duas implementações no mesmo arquivo (classe + decorator); deveria ser unificado
8. **FairnessGuard parcial** — Apenas 4/11 agentes têm FairnessGuard integrado; gap de compliance

### 24.7 Compliance

1. **Anti-sycophancy** — Presente em todos os agentes (via bloco compartilhado ou equivalente no prompt), porém sem guardrail automatizado em runtime
2. **FairnessGuard** — Integrado em 4 agentes (Wizard, Talent, Jobs Management, Kanban); ausente em Analytics, Automation, ATS Integration, Communication, Sourcing, Pipeline, Policy
3. **LGPD em ATS** — Lista de campos sensíveis não sincronizados é hardcoded
4. **Audit trail** — SOX/ISO 27001 mencionados no prompt do ATS Agent, mas sem implementação de audit trail centralizado
5. **ConsentChecker mode** — Default é `soft_warning` (não bloqueia); deveria ser `hard_block` em produção
6. **Bias Audit** — Dimensão `disability` depende de campo `has_disability` no registro do candidato, que pode não estar preenchido

---

## 25. Oportunidades e Capacidades Ausentes

### 25.1 Score Clicável no Funil

**Status:** Ausente
**Descrição:** Permitir que recrutador clique no LIA Score de um candidato no funil e veja breakdown detalhado (rubricas, WSI, prerequisites, recency) com explicação de cada componente
**Complexidade:** Média — dados já existem no `lia_score_service.py`; precisa de endpoint dedicado + componente UI
**Arquivos relevantes:** `lia_score_service.py` (fórmula), `candidates-page.tsx` (UI)

### 25.2 Análise Comparativa com IA Real

**Status:** Parcialmente implementado (via `compare_candidates` tool)
**Descrição:** Análise comparativa multi-dimensional entre candidatos com visualização lado-a-lado no frontend
**Gap:** Não há componente visual dedicado para comparação; resultado aparece apenas como texto no chat
**Arquivos relevantes:** `analytics_query_tools.py`, `kanban_assistant_prompts.py`

### 25.3 Fit Cultural com Dados de Entrevista

**Status:** Ausente
**Descrição:** Avaliar fit cultural do candidato usando dados de entrevistas realizadas (notas do entrevistador, sentimento, alinhamento de valores)
**Gap:** WSI avalia competências comportamentais, mas não há cruzamento com dados de entrevista reais
**Arquivos relevantes:** `lia_score_service.py` (scoring), `pipeline_react_agent.py` (pipeline)

### 25.4 Auto-routing Inteligente

**Status:** Parcialmente implementado (CascadedRouter)
**Descrição:** Roteamento que aprende com o tempo quais agentes foram mais úteis para cada tipo de mensagem
**Gap:** CascadedRouter usa cache (melhora velocidade) mas não faz aprendizado; peso dos tiers é estático
**Arquivos relevantes:** `cascaded_router.py`, `llm_cascade.py`

### 25.5 Insights Proativos no Kanban

**Status:** Parcialmente implementado (SaturationBadge)
**Descrição:** LIA sugere proativamente ações no kanban (ex: "3 candidatos parados há 7 dias na etapa Entrevista")
**Gap:** SaturationBadge existe mas é reativo (badge estático); falta ProactiveAgentWorker integrado ao kanban UI
**Arquivos relevantes:** `SaturationBadge.tsx`, `proactive_agent_worker.py`

### 25.6 Relatório Cross-vagas

**Status:** Ausente
**Descrição:** Relatório consolidado comparando métricas entre todas as vagas da empresa (TTF, qualidade, custo, fontes)
**Gap:** `comparative_analysis` command existe mas compara apenas vagas selecionadas; falta dashboard consolidado
**Arquivos relevantes:** `job_analytics_prompt_service.py`, `job-report-modal.tsx`

### 25.7 ML Adaptativo

**Status:** Parcialmente implementado (LIA Score com pesos fixos)
**Descrição:** Modelo que ajusta pesos do scoring baseado em feedback de contratações reais
**Gap:** `Calibration_Adjustment` existe na fórmula do LIA Score mas é sempre 0; falta loop de feedback
**Arquivos relevantes:** `lia_score_service.py` (fórmula com `Calibration_Adjustment`), `learning_analytics_service.py`

### 25.8 Benchmark de Mercado Real

**Status:** Parcialmente implementado (via `salary_benchmark` command)
**Descrição:** Benchmark de mercado com dados reais e atualizados (salário, tempo de contratação, volume)
**Gap:** Benchmark salarial usa IA para estimar; não há integração com fontes de dados de mercado reais (ex: Glassdoor, Levels.fyi)
**Arquivos relevantes:** `job_wizard_tools.py` (`search_salary_benchmark`, `get_intelligent_salary`)

### 25.9 WSI Assíncrono

**Status:** Ausente
**Descrição:** Enviar triagem WSI para candidato e processar respostas assincronamente quando o candidato responder
**Gap:** WSI é síncrono (recrutador inicia, LIA processa em tempo real); não há fluxo de envio + coleta assíncrona
**Arquivos relevantes:** `wsi_screening` tool, `pipeline_react_agent.py`

### 25.10 Outras Oportunidades

| Oportunidade                           | Complexidade | Impacto |
|----------------------------------------|-------------|---------|
| Registro dinâmico de agentes (YAML)    | Alta        | Alto    |
| Multi-model por agente (GPT/Gemini)    | Média       | Alto    |
| RAG por domínio (embeddings)           | Alta        | Alto    |
| Validar escopo de tools no backend     | Baixa       | Alto    |
| Ativar FairnessGuard em todos agentes  | Baixa       | Alto    |
| Remover IntentRouter legado            | Baixa       | Médio   |
| Streaming de pensamentos ReAct via WS  | Média       | Médio   |
| Unificar circuit breaker (classe+deco) | Baixa       | Médio   |
| Dashboard real-time de Model Drift     | Média       | Alto    |
| Bias Audit Dashboard no frontend       | Média       | Alto    |

---

## 26. Referência de Arquivos

### 26.1 Orquestração

| Arquivo | Responsabilidade |
|---------|-----------------|
| `lia-agent-system/app/orchestrator/orchestrator.py` | Orchestrator principal: process_request(), memória, cache, planos |
| `lia-agent-system/app/orchestrator/cascaded_router.py` | CascadedRouter 6 tiers com métricas Prometheus |
| `lia-agent-system/app/orchestrator/fast_router.py` | FastRouter regex/keyword (Tier 4) |
| `lia-agent-system/app/orchestrator/llm_cascade.py` | LLM Cascade Haiku→Sonnet→Opus (Tier 5) |
| `lia-agent-system/app/orchestrator/action_executor.py` | Execução closed-loop de ações (move, email, triagem) |
| `lia-agent-system/app/orchestrator/pending_action.py` | Store de ações pendentes para HITL |
| `lia-agent-system/app/orchestrator/memory_resolver.py` | Resolução de pronomes/referências (Tier 0) |

### 26.2 Agentes

| Arquivo | Responsabilidade |
|---------|-----------------|
| `lia-agent-system/libs/agents-core/lia_agents_core/react_agent_registry.py` | Registry Singleton + AgentFactory session-safe |
| `lia-agent-system/libs/agents-core/lia_agents_core/enhanced_agent_mixin.py` | Mixin: memória, autonomia, aprendizado (5 etapas) |
| `lia-agent-system/libs/agents-core/lia_agents_core/autonomy_engine.py` | AutonomyEngine: 3 níveis de autonomia |
| `lia-agent-system/libs/agents-core/lia_agents_core/learning_extractor.py` | LearningExtractor: 3 categorias |
| `lia-agent-system/libs/agents-core/lia_agents_core/long_term_memory.py` | LongTermMemoryService: 4 tipos de memória |
| `lia-agent-system/libs/agents-core/lia_agents_core/working_memory.py` | WorkingMemoryService: memória de sessão |
| `lia-agent-system/libs/agents-core/lia_agents_core/memory_integration.py` | MemoryIntegration: ponte WM↔LTM |
| `lia-agent-system/app/domains/job_management/agents/wizard_react_agent.py` | Wizard Agent (criação de vagas) |
| `lia-agent-system/app/domains/cv_screening/agents/pipeline_react_agent.py` | Pipeline Agent (triagem CVs) |
| `lia-agent-system/app/domains/sourcing/agents/sourcing_react_agent.py` | Sourcing Agent (busca candidatos) |
| `lia-agent-system/app/domains/recruiter_assistant/agents/talent_react_agent.py` | Talent Agent (funil) |
| `lia-agent-system/app/domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py` | Jobs Management Agent (portfólio vagas) |
| `lia-agent-system/app/domains/recruiter_assistant/agents/kanban_react_agent.py` | Kanban Agent (pipeline) |
| `lia-agent-system/app/domains/hiring_policy/agents/policy_react_agent.py` | Policy Agent (políticas) |
| `lia-agent-system/app/domains/automation/agents/automation_react_agent.py` | Automation Agent (decomposição tarefas) |
| `lia-agent-system/app/domains/analytics/agents/analytics_react_agent.py` | Analytics Agent (KPIs, previsões) |
| `lia-agent-system/app/domains/communication/agents/communication_react_agent.py` | Communication Agent (multi-canal LGPD) |
| `lia-agent-system/app/domains/ats_integration/agents/ats_integration_react_agent.py` | ATS Integration Agent (Gupy, Pandapé, Merge, StackOne) |

### 26.3 Compliance e Governança

| Arquivo | Responsabilidade |
|---------|-----------------|
| `lia-agent-system/app/shared/compliance/fairness_guard.py` | FairnessGuard: 9 categorias, 42 patterns, 11 termos implícitos |
| `lia-agent-system/app/shared/pii_masking.py` | PII Masking: strip_pii_for_llm_prompt + PIIMaskingFilter |
| `lia-agent-system/app/services/bias_audit_service.py` | Bias Audit: Four-Fifths Rule, 4 dimensões |
| `lia-agent-system/app/services/consent_checker_service.py` | ConsentCheckerService: Gate 1, soft_warning/hard_block |
| `lia-agent-system/app/services/lgpd_cleanup_service.py` | LGPD Cleanup: retenção 90-365 dias, dry-run |
| `lia-agent-system/app/services/dsr_export_service.py` | DSR Export: portabilidade LGPD Art. 18 V |
| `lia-agent-system/app/services/confidence_policy_service.py` | ConfidencePolicy: 3 níveis de autonomia de ação |
| `lia-agent-system/app/api/v1/lgpd_compliance.py` | API LGPD: DPO, Breaches, Decisions (916 linhas) |
| `docs/compliance/FRIA_WSI.md` | FRIA: Avaliação de impacto EU AI Act (355 linhas) |
| `docs/compliance/WEDOTALENT_COMPLIANCE_ARCHITECTURE.md` | Arquitetura de compliance: 242 itens, 7 frameworks (1678 linhas) |

### 26.4 Resiliência e Custos

| Arquivo | Responsabilidade |
|---------|-----------------|
| `lia-agent-system/app/shared/resilience/circuit_breaker.py` | Circuit Breaker: 12 circuits, 3 estados, notificação |
| `lia-agent-system/app/services/token_tracking_service.py` | Token Tracking: 10 modelos, limites, custos |
| `lia-agent-system/app/services/training_data_service.py` | Training Data: 3 formatos export (OpenAI, Anthropic, DPO) |
| `lia-agent-system/app/services/feedback_learning_service.py` | Feedback Learning: thumbs, rating, correções |
| `lia-agent-system/app/domains/job_management/services/outcome_tracker.py` | Outcome Tracker: correlação decisão ↔ contratação |

### 26.5 Aprendizado e Analytics

| Arquivo | Responsabilidade |
|---------|-----------------|
| `lia-agent-system/app/services/predictive_analytics_service.py` | Serviço preditivo de contratação |
| `lia-agent-system/app/services/search_analytics_service.py` | Analytics de busca de candidatos |
| `lia-agent-system/app/services/response_cache_service.py` | Cache de respostas por intent |
| `lia-agent-system/app/services/pre_qualification_service.py` | Pre-qualification: triagem automática pré-WSI |
| `lia-agent-system/app/services/personalized_feedback_service.py` | Feedback personalizado: 3 tons |
| `lia-agent-system/app/services/score_normalization_service.py` | Score normalization: fator 0.7-1.3 |
| `lia-agent-system/app/services/lia_score_service.py` | LIA Score: fórmula unificada, pesos por cenário |

### 26.6 Prompts e Templates

| Arquivo | Responsabilidade |
|---------|-----------------|
| `lia-agent-system/app/domains/recruiter_assistant/prompts/kanban_assistant_prompts.py` | 18 Kanban Command Templates + detect_command_type() |
| `lia-agent-system/app/domains/analytics/services/job_analytics_prompt_service.py` | 8 Analytics Command Templates + COMMAND_TEMPLATES |
| `lia-agent-system/app/domains/recruiter_assistant/prompts/talent_assistant_prompts.py` | Talent Agent prompts |
| `lia-agent-system/app/domains/recruiter_assistant/prompts/jobs_management_prompts.py` | Jobs Management prompts |
| `lia-agent-system/app/tools/scope_config.py` | Configuração de escopo: TALENT_FUNNEL, JOB_TABLE, IN_JOB, GLOBAL |

### 26.7 API Endpoints

| Arquivo | Responsabilidade |
|---------|-----------------|
| `lia-agent-system/app/api/v1/orchestrated_job_chat.py` | Endpoint /orchestrator/job-chat (Kanban) |
| `lia-agent-system/app/api/v1/lia_assistant.py` | Endpoint /orchestrator/talent-chat (Float) |
| `lia-agent-system/app/api/v1/lgpd_compliance.py` | 20 endpoints LGPD (DPO, Breaches, Decisions) |

### 26.8 Frontend (plataforma-lia/)

| Arquivo | Responsabilidade |
|---------|-----------------|
| `src/components/pages/candidates-page.tsx` | Float Chat, busca, análise, UnifiedBulkActionsBar, ProactiveInsightCard |
| `src/components/pages/job-kanban-page.tsx` | Kanban Chat, pipeline visual, SaturationBadge, drag-and-drop |
| `src/components/pages/chat-page.tsx` | Chat Full dedicado, Quick Actions, histórico, WebSocket |
| `src/components/rubric-evaluation-modal.tsx` | Modal de avaliação por rubrica multi-dimensional |
| `src/components/proactive-insight-card.tsx` | Card de insights proativos após busca |
| `src/components/kanban/components/SaturationBadge.tsx` | Badge de saturação do pipeline por canal |
| `src/components/job-report-modal.tsx` | Modal de relatório da vaga com export PDF |
| `src/components/ui/unified-bulk-actions-bar.tsx` | Barra de ações bulk (9 ações) |
| `src/components/contextual-actions-banner.tsx` | Banner de ações contextuais (8 ações) |
| `src/services/lia-api.ts` | Client API (4943 linhas) |
| `src/lib/api/kanban-assistant.ts` | API helpers: callOrchestratedTalentChat(), callOrchestratedJobChat() |
| `src/contexts/lia-float-context.tsx` | Estado global do Float/Super Prompt |

### 26.9 Documentação de Compliance

| Arquivo | Responsabilidade |
|---------|-----------------|
| `docs/compliance/FRIA_WSI.md` | FRIA — Avaliação de Impacto em Direitos Fundamentais (355 linhas) |
| `docs/compliance/WEDOTALENT_COMPLIANCE_ARCHITECTURE.md` | Arquitetura de Compliance (1678 linhas, 242 itens, 7 frameworks) |
| `docs/analises/MAPA_INTELIGENCIA_LIA_COMPLETO.md` | Mapa de inteligência LIA (v3.0) |

---

*Documento gerado por auditoria automatizada do código-fonte em 13/03/2026. Versão 2.0 — expandido com 15 novas seções e caminhos de arquivo exatos.*