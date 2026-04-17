# Inventário Completo de Documentos de Referência — Plataforma LIA

**Data:** 31/03/2026
**Versão:** 1.0
**Escopo:** Todos os documentos, arquivos de configuração, prompts, seeds e referências consumidos em runtime pela plataforma LIA
**Referência:** Auditoria Alpha 1 Fase 6, Bandas Transversais (24 Dimensões × 8 Domínios)

### Nota Metodológica

- **Paths:** Todos os caminhos de arquivo são relativos à raiz do monorepo. Arquivos do backend estão sob `lia-agent-system/`, frontend sob `plataforma-lia/`, e documentos de referência externos em `attached_assets/`.
- **Critério de inclusão:** Arquivos que são (a) consumidos em runtime por agentes, serviços ou middleware, (b) carregados como seed/configuração no startup, ou (c) servem como documentação de referência que informa o design mas não é carregada em runtime.
- **Tipo:** Estático = versionado em código, não muda em runtime. Dinâmico = DB-backed ou state que muda em runtime. Seed = dados iniciais populados uma vez no startup. API externa = integração com serviço externo.
- **Verificação:** Todos os paths foram verificados contra a árvore do repositório em 31/03/2026.

---

## Índice

1. [Persona & Identity](#1-persona--identity)
2. [System Prompts por Domínio](#2-system-prompts-por-domínio)
3. [Domain Prompt YAMLs](#3-domain-prompt-yamls)
4. [Few-Shot Examples](#4-few-shot-examples)
5. [Compliance & FairnessGuard](#5-compliance--fairnessguard)
6. [PII & LGPD](#6-pii--lgpd)
7. [Configurações & Rules](#7-configurações--rules)
8. [WSI & Avaliação](#8-wsi--avaliação)
9. [Templates de Vaga por Setor](#9-templates-de-vaga-por-setor)
10. [Robustness & Resilience](#10-robustness--resilience)
11. [Inteligência & Learning](#11-inteligência--learning)
12. [Memory & Search](#12-memory--search)
13. [Governance & Monitoring](#13-governance--monitoring)
14. [Communication & Integrations](#14-communication--integrations)
15. [Documentação Técnica (docs/)](#15-documentação-técnica-docs)
16. [Tabela-Resumo & Gaps](#16-tabela-resumo--gaps)

---

## 1. Persona & Identity

Arquivos que definem a identidade, tom de comunicação e comportamento ético da LIA. São injetados em **todos os 11 agentes ReAct** via `EnhancedAgentMixin._setup_enhanced()` na inicialização de cada agente.

| # | Arquivo | Descrição | Consumido por | Momento no Fluxo | Tipo |
|---|---------|-----------|---------------|-------------------|------|
| 1.1 | `lia-agent-system/app/prompts/shared/lia_persona.yaml` | Persona LIA (identidade, tom, vocabulário HR, diretrizes éticas, regras de persistência de dados) | Todos os agentes via `PromptLoader.get_shared_prompt("lia_persona")` | Inicialização do agente (system prompt) | Estático |
| 1.2 | `lia-agent-system/app/prompts/shared/agent_prompts.yaml` | System prompts completos para cada agente (orchestrator, job_planner, sourcing, cv_screening, communication, etc.) — ~1687 linhas | `PromptLoader`, `PromptRegistry` → cada agente carrega seu bloco | Inicialização do agente (system prompt) | Estático |
| 1.3 | `lia-agent-system/app/prompts/shared/defensive.yaml` | Prompts defensivos: triggers de clarificação, respostas out-of-scope, recuperação de erros, confirmação de ações | Todos os agentes via `EnhancedAgentMixin` | Runtime — quando detecta ambiguidade, erro ou solicitação fora do escopo | Estático |
| 1.4 | `lia-agent-system/app/shared/prompts/anti_sycophancy_block.py` | 3 variantes anti-bajulação: `OPERATIONAL` (Talent, Kanban, Jobs), `FULL` (Wizard, Policy), `ORCHESTRATOR` (ponto de entrada global) — Crença #11 WeDO | System prompts de todos os agentes operacionais | Injetado no system prompt; ativo em cada interação com recrutador | Estático |
| 1.5 | `lia-agent-system/app/shared/prompts/interaction_patterns.py` | Padrões compartilhados: `NEGATION_WORDS` (30+ termos), `CONFIRMATION_WORDS` (30+ termos), blocos `NEGATION_DETECTION_BLOCK`, `CHAIN_OF_THOUGHT_BLOCK`, `ANTI_SYCOPHANCY_BLOCK` | Todos os agentes (detecção de intenção pré-LLM) | Runtime — antes de executar qualquer ação | Estático |
| 1.6 | `lia-agent-system/app/shared/prompts/cot.py` | Chain-of-Thought Builder: 4 estratégias (Standard, Zero-Shot, Self-Consistency, Tree-of-Thought), 5 tipos de tarefa (job_extraction, salary_analysis, intent_classification, orchestration, competency_extraction) | Todos os agentes que fazem raciocínio complexo | Runtime — wrappa prompts com instrução CoT antes de enviar ao LLM | Estático |
| 1.7 | `lia-agent-system/app/shared/prompts/templates.py` | Templates de prompt reutilizáveis para formatação | `PromptRegistry`, agentes via `PromptLoader` | Build-time do system prompt | Estático |
| 1.8 | `lia-agent-system/app/shared/prompts/prompt_registry.py` | Registry central de prompts — gerencia cache e resolução de prompts por domínio/shared | Todos os agentes no startup | Inicialização | Estático |
| 1.9 | `lia-agent-system/app/shared/prompts/loader.py` | `PromptLoader` — carregamento YAML centralizado com cache. Resolve paths em `lia-agent-system/app/prompts/domains/` e `lia-agent-system/app/prompts/shared/` | Todos os agentes, `PromptRegistry` | Inicialização (com cache) | Estático |

### Diagrama de Injeção

```
EnhancedAgentMixin._setup_enhanced()
  ├── PromptLoader.get_shared_prompt("lia_persona") → lia_persona.yaml
  ├── PromptLoader.get_shared_prompt("agent_prompts", agent_key) → agent_prompts.yaml
  ├── ANTI_SYCOPHANCY_{variant} → anti_sycophancy_block.py
  ├── CHAIN_OF_THOUGHT_BLOCK → interaction_patterns.py
  ├── NEGATION_DETECTION_BLOCK → interaction_patterns.py
  ├── defensive.yaml (clarification_triggers, out_of_scope)
  ├── FairnessGuard (3 camadas) → fairness_guard.py
  ├── PII Masking (4 camadas) → pii_masking.py
  ├── AuditService → audit_service.py
  ├── ConfidenceNode → confidence.py
  ├── BiasAuditSnapshot → bias_audit
  ├── CircuitBreaker → circuit_breaker.py
  └── WorkingMemory → working_memory.py
```

---

## 2. System Prompts por Domínio

Cada domínio possui um system prompt Python dedicado que define o comportamento especializado do agente. Estes são os 14 system prompts identificados no código:

| # | Arquivo | Domínio/Agente | Descrição | Momento no Fluxo | Tipo |
|---|---------|----------------|-----------|-------------------|------|
| 2.1 | `lia-agent-system/app/domains/analytics/agents/analytics_system_prompt.py` | Analytics Agent | Prompt para análise de KPIs, funil de conversão, relatórios de recrutamento | Quando recrutador pede relatórios/métricas | Estático |
| 2.2 | `lia-agent-system/app/domains/ats_integration/agents/ats_integration_system_prompt.py` | ATS Integration Agent | Sincronização com ATS externos (Gupy, Pandapé, Merge.dev) | Sync de candidatos/vagas com ATS | Estático |
| 2.3 | `lia-agent-system/app/domains/automation/agents/automation_system_prompt.py` | Automation Agent | Automação de tarefas recorrentes, triggers, scheduled actions | Pipeline automation, proactive alerts | Estático |
| 2.4 | `lia-agent-system/app/domains/communication/agents/communication_system_prompt.py` | Communication Agent | Envio de emails, WhatsApp, feedback, notificações | Outreach, feedback, comunicação com candidatos | Estático |
| 2.5 | `lia-agent-system/app/domains/cv_screening/agents/pipeline_system_prompt.py` | CV Screening / Pipeline Agent | Triagem de currículos, scoring WSI, pareceres | Fluxo de triagem (11 steps) | Estático |
| 2.6 | `lia-agent-system/app/domains/hiring_policy/agents/policy_system_prompt.py` | Hiring Policy Agent | Regras de contratação, compliance, aprovações HITL | Consulta de políticas, validação de ações | Estático |
| 2.7 | `lia-agent-system/app/domains/interview_scheduling/agents/interview_system_prompt.py` | Interview Scheduling Agent | Agendamento de entrevistas, ICS, calendário | Quando recrutador pede agendamento | Estático |
| 2.8 | `lia-agent-system/app/domains/job_management/agents/wizard_system_prompt.py` | Job Wizard Agent | Criação guiada de vagas (wizard multi-step) | Fluxo de criação de vaga | Estático |
| 2.9 | `lia-agent-system/app/domains/pipeline/agents/pipeline_system_prompt.py` | Pipeline Management Agent | Gestão de pipeline, transições de estágio, decisões | Movimentação de candidatos entre estágios | Estático |
| 2.10 | `lia-agent-system/app/domains/policy/agents/system_prompt.py` | Policy Agent (consolidated) | Engine de políticas consolidada | Validação de regras de negócio | Estático |
| 2.11 | `lia-agent-system/app/domains/recruiter_assistant/agents/kanban_system_prompt.py` | Kanban Assistant Agent | Visualização e gestão do quadro Kanban de candidatos | Consulta de pipeline visual | Estático |
| 2.12 | `lia-agent-system/app/domains/recruiter_assistant/agents/talent_system_prompt.py` | Talent Assistant Agent | Assistente de análise de talentos, comparação de candidatos | Análise comparativa de candidatos | Estático |
| 2.13 | `lia-agent-system/app/domains/recruiter_assistant/agents/jobs_mgmt_system_prompt.py` | Jobs Management Assistant | Gestão de vagas pelo assistente do recrutador | Operações CRUD de vagas via chat | Estático |
| 2.14 | `lia-agent-system/app/domains/sourcing/agents/sourcing_system_prompt.py` | Sourcing Agent | Busca de candidatos (local + Pearch AI), boolean search, outreach | Busca e captação de talentos | Estático |

### Sub-agentes de Sourcing e Pipeline

| # | Arquivo | Sub-agente | Descrição |
|---|---------|-----------|-----------|
| 2.15 | `lia-agent-system/app/domains/sourcing/agents/sourcing_planner_agent.py` | Sourcing Planner | Planejamento de estratégia de busca |
| 2.16 | `lia-agent-system/app/domains/sourcing/agents/sourcing_search_agent.py` | Sourcing Search | Execução de buscas (ES + PgVector) |
| 2.17 | `lia-agent-system/app/domains/sourcing/agents/sourcing_enrich_agent.py` | Sourcing Enrich | Enriquecimento de perfis via Apify |
| 2.18 | `lia-agent-system/app/domains/sourcing/agents/sourcing_engagement_agent.py` | Sourcing Engagement | Outreach e engajamento de candidatos |
| 2.19 | `lia-agent-system/app/domains/pipeline/agents/pipeline_action_agent.py` | Pipeline Action | Execução de ações no pipeline |
| 2.20 | `lia-agent-system/app/domains/pipeline/agents/pipeline_decision_agent.py` | Pipeline Decision | Decisões de transição de estágio |
| 2.21 | `lia-agent-system/app/domains/pipeline/agents/pipeline_context_agent.py` | Pipeline Context | Agregação de contexto para decisão |
| 2.22 | `lia-agent-system/app/domains/pipeline/agents/pipeline_transition_agent.py` | Pipeline Transition | Transição efetiva entre estágios |

---

## 3. Domain Prompt YAMLs

Arquivos YAML em `lia-agent-system/app/prompts/domains/` carregados pelo `PromptLoader` e `PromptRegistry`. Contêm configurações de domínio, tool descriptions e instruções específicas.

| # | Arquivo | Domínio | Consumido por | Momento no Fluxo | Tipo |
|---|---------|---------|---------------|-------------------|------|
| 3.1 | `lia-agent-system/app/prompts/domains/analytics.yaml` | Analytics | Analytics Agent, Report Service | Inicialização do agente analytics | Estático |
| 3.2 | `lia-agent-system/app/prompts/domains/ats_integration.yaml` | ATS Integration | ATS Integration Agent, Sync Services | Sync com ATS externo | Estático |
| 3.3 | `lia-agent-system/app/prompts/domains/automation.yaml` | Automation | Automation Agent, Scheduler | Configuração de automações | Estático |
| 3.4 | `lia-agent-system/app/prompts/domains/communication.yaml` | Communication | Communication Agent, Email/WhatsApp Services | Envio de comunicações | Estático |
| 3.5 | `lia-agent-system/app/prompts/domains/cv_screening.yaml` | CV Screening | CV Screening Agent, WSI Interview Graph | Triagem de candidatos | Estático |
| 3.6 | `lia-agent-system/app/prompts/domains/interview_scheduling.yaml` | Interview Scheduling | Interview Scheduling Agent | Agendamento de entrevistas | Estático |
| 3.7 | `lia-agent-system/app/prompts/domains/job_management.yaml` | Job Management | Job Wizard Agent, Job Template Service | Criação/edição de vagas | Estático |
| 3.8 | `lia-agent-system/app/prompts/domains/pipeline_transition.yaml` | Pipeline Transition | Pipeline Transition Agent, Pipeline Action Agent | Transições de estágio no pipeline | Estático |
| 3.9 | `lia-agent-system/app/prompts/domains/recruiter_assistant.yaml` | Recruiter Assistant | Kanban Agent, Talent Agent, Jobs Mgmt Agent | Assistente do recrutador (chat) | Estático |
| 3.10 | `lia-agent-system/app/prompts/domains/sourcing.yaml` | Sourcing | Sourcing Agent (Planner, Search, Enrich, Engagement) | Busca de candidatos | Estático |

---

## 4. Few-Shot Examples

Exemplos estruturados que melhoram a precisão das respostas LLM via in-context learning.

| # | Arquivo | Descrição | Consumido por | Momento no Fluxo | Tipo |
|---|---------|-----------|---------------|-------------------|------|
| 4.1 | `lia-agent-system/app/shared/prompts/few_shot_examples.py` | 6 categorias: Job Extraction (5 ex.), Intent Classification (6 ex.), Salary Analysis (3 ex.), Competency Extraction (4 ex.), Orchestration Decisions (4 ex.), Responsibility Generation (2 ex.) | Orchestrator (intent), Job Wizard (extraction), Sourcing (competency) | Adicionados ao prompt antes da chamada LLM | Estático |
| 4.2 | `lia-agent-system/app/shared/prompts/intent_few_shot_examples.py` | 20 exemplos para Tier 3 LLM Router: 10 CLAROS (confidence ≥ 0.85) + 10 AMBÍGUOS (≤ 0.55). Cobre 7 domínios | `IntentRouter` (Tier 3 — fallback LLM) | Roteamento de intenção quando Tier 1 (regex) e Tier 2 (similarity) falham | Estático |
| 4.3 | `lia-agent-system/app/shared/prompts/examples/orchestrator_examples.py` | Exemplos específicos para decisões do Orchestrator | `MainOrchestrator`, `CascadedRouter` | Roteamento de mensagens do recrutador | Estático |
| 4.4 | `lia-agent-system/app/shared/prompts/examples/pipeline_examples.py` | Exemplos de transições de pipeline, decisões de estágio | Pipeline Agents (Action, Decision, Transition) | Decisão de movimentação de candidatos | Estático |
| 4.5 | `lia-agent-system/app/shared/prompts/examples/sourcing_examples.py` | Exemplos de queries de busca, boolean strings, ranking | Sourcing Agent (Search, Planner) | Construção de queries de busca | Estático |
| 4.6 | `lia-agent-system/app/shared/prompts/examples/job_planner_examples.py` | Exemplos de extração de JD, geração de perguntas WSI | Job Wizard Agent, WSI Service | Criação de vagas e geração de perguntas | Estático |

---

## 5. Compliance & FairnessGuard

Documentos que implementam as 3 camadas de fairness, auditoria SOX-compliant e guardrails por domínio. Fazem parte das **Bandas Transversais** — ativados via `EnhancedAgentMixin` em todos os domínios habilitados.

| # | Arquivo | Descrição | Consumido por | Momento no Fluxo | Tipo |
|---|---------|-----------|---------------|-------------------|------|
| 5.1 | `lia-agent-system/app/shared/compliance/fairness_guard.py` | FairnessGuard (3 camadas, ~806 linhas): L1 = 13 categorias protegidas + 350+ patterns regex; L2 = 25+ termos proxy de viés implícito; L3 = análise semântica via LLM (Claude Haiku), sector-aware | Todos os agentes (via `EnhancedAgentMixin`), RAG pipeline, pipeline transitions, communication tools, sourcing | **L1+L2:** Pré-LLM (regex) a cada interação. **L3:** Ações de alto impacto (rejeição, comunicação, scoring) por setor | Estático (L1/L2) + Dinâmico (L3 — chamada LLM) |
| 5.2 | `lia-agent-system/app/shared/compliance/fairness_guard_middleware.py` | Middleware FastAPI que aplica FairnessGuard em endpoints selecionados | Endpoints de pipeline, communication, scoring | Request middleware (antes do handler) | Estático |
| 5.3 | `lia-agent-system/app/shared/compliance/fact_checker.py` | Verificação factual pós-LLM: valida salários, contagens, percentuais, datas geradas pela LLM | Todos os agentes que retornam dados numéricos/factuais | Pós-LLM (step 8 no fluxo de triagem) | Estático |
| 5.4 | `lia-agent-system/app/shared/compliance/audit_service.py` | AuditService SOX-compliant: registro imutável (append-only), retenção 730-1825 dias | Todos os agentes, endpoints críticos (JD generation, WSI, pipeline transitions) | Cada decisão/ação significativa (step 10 no fluxo de triagem) | Dinâmico (DB-backed) |
| 5.5 | `lia-agent-system/app/shared/compliance/audit_callback.py` | Callback para integração com LangGraph — registra decisões de agentes automaticamente | Agentes LangGraph (via callback handler) | Cada step do grafo de agente | Dinâmico |
| 5.6 | `lia-agent-system/app/shared/compliance/audit_writer.py` | Writer assíncrono para audit trail — batch writes para performance | `AuditService` | Background (async batch) | Dinâmico |
| 5.7 | `lia-agent-system/app/shared/compliance/audit_storage.py` | Camada de storage para audit trail | `AuditWriter` | Persistência | Dinâmico |
| 5.8 | `lia-agent-system/app/shared/compliance/audit_models.py` | Modelos Pydantic/SQLAlchemy para audit trail | `AuditService`, `AuditWriter` | Serialização/persistência | Estático |
| 5.9 | `lia-agent-system/app/shared/compliance/guardrail_repository.py` | Repository de guardrails — carrega regras do DB por domínio/tenant | Todos os agentes via `EnhancedAgentMixin` | Inicialização do agente | Dinâmico (DB-backed) |
| 5.10 | `lia-agent-system/app/core/seeds/guardrails_seed.py` | Seed de guardrails primários e secundários por domínio — populam o DB na primeira execução | `GuardrailRepository` (via seed no startup) | Startup (lifespan) — uma vez | Seed |

### Cobertura Transversal do FairnessGuard

Conforme a imagem de Bandas Transversais (24 Dimensões × 8 Domínios):

| Domínio | fairness.py | Habilitado |
|---------|:-----------:|:----------:|
| jobs (Job Management) | OK | Sim |
| appl. (Applications/CV Screening) | X | Parcial |
| eval. (Evaluation/WSI) | X | Parcial |
| sched. (Scheduling) | X | Não |
| srcp. (Sourcing) | OK | Sim |
| insig. (Insights/Analytics) | X | Não |
| msg. (Communication) | X | Parcial |
| auto. (Automation) | X | Não |
| **LIA (Orchestrator)** | **auto** | **Sim** |

---

## 6. PII & LGPD

Documentos que implementam proteção de dados pessoais (LGPD) e mascaramento de PII. Banda transversal ativa em todos os domínios via `EnhancedAgentMixin`.

| # | Arquivo | Descrição | Consumido por | Momento no Fluxo | Tipo |
|---|---------|-----------|---------------|-------------------|------|
| 6.1 | `lia-agent-system/app/shared/pii_masking.py` | PII Masking (4 camadas): L1 = Regex (CPF, email, telefone); L2 = NER (nomes); L3 = Presidio (opt-in); L4 = Global logging filter (`PIIMaskingFilter`) | Todos os agentes (pré-LLM), AuditService, logging global | **Pré-LLM** (step 5 no fluxo de triagem): CPF → `[CPF_MASKED]`, nome → `[NAME_1]`, endereço → `[ADDR_MASKED]`. **O LLM NUNCA vê dados pessoais reais** | Estático (config) + Dinâmico (runtime) |
| 6.2 | `lia-agent-system/app/api/v1/lgpd_compliance.py` | Endpoints LGPD compliance | API pública | Request de compliance | Dinâmico |
| 6.3 | `lia-agent-system/app/api/v1/data_subject_requests.py` | Endpoints DSR (Data Subject Requests) — direitos do titular | API pública, DPO | Solicitação de acesso/exclusão/portabilidade | Dinâmico |
| 6.4 | `lia-agent-system/app/api/v1/consent_management.py` | Endpoints de gestão de consentimento | Frontend (triagem), API | Coleta e revogação de consentimento | Dinâmico |
| 6.5 | `lia-agent-system/app/api/v1/granular_consent.py` | Consentimento granular por finalidade | Frontend, API | Coleta de consentimento por tipo de processamento | Dinâmico |
| 6.6 | `lia-agent-system/app/api/v1/communication_optout.py` | Opt-out de comunicações (quarentena 3 meses) | Communication Service, WhatsApp Service | Quando candidato pede para não ser contatado | Dinâmico |

### Proteções LGPD Ativadas no Fluxo de Triagem (11 Steps)

1. PII nunca chega ao LLM — 4 camadas de mascaramento pré-LLM (LGPD Art.12, 46)
2. FairnessGuard 3 layers — bloqueia vieses explícitos e implícitos ANTES
3. BiasAuditSnapshot — Four-Fifths Rule: detecta se taxa de aprovação de grupo demográfico < 80% de outro
4. ConfidenceNode — calibra scores para serem comparáveis e significativos
5. FactChecker pós-LLM — verifica claims factuais do candidato
6. Audit Trail SOX — registro imutável, 7 anos, append-only
7. WSI com Bloom+Dreyfus — progressão de dificuldade + cobertura por competências

---

## 7. Configurações & Rules

Arquivos de configuração que controlam regras de negócio, pesos, limites e políticas por setor.

| # | Arquivo | Descrição | Consumido por | Momento no Fluxo | Tipo |
|---|---------|-----------|---------------|-------------------|------|
| 7.1 | `lia-agent-system/app/config/default_rules.json` | Regras de negócio padrão: rate limits, escalations, aprovações, thresholds de autonomia | `PolicyEngineService`, `RateLimitMiddleware` | Startup (carregadas como defaults); runtime (avaliadas a cada request) | Seed (JSON) |
| 7.2 | `lia-agent-system/app/services/policy_engine_service.py` | Policy Engine com **Alpha 1 Sector Rules** (tech, financeiro, saúde, RPO, varejo, logística): autonomia, HITL thresholds, FairnessGuard L3 por setor | Todos os agentes (via `EnhancedAgentMixin`), Pipeline Transition Agent | Cada decisão que requer validação de policy — define se ação é auto/HITL/bloqueada | Dinâmico (DB-backed + defaults) |
| 7.3 | `lia-agent-system/app/config/industry_weights.py` | Universal Scoring Model + WSI weights por indústria: pesos de hard skills, soft skills, experiência, formação por setor | WSI Service, Score Normalization, CV Screening Agent | Scoring de candidatos — define pesos de cada dimensão | Estático |
| 7.4 | `lia-agent-system/app/config/cache_config.py` | Configuração de cache: TTLs, max entries, estratégias de invalidação | `CacheManagerService`, Semantic Search, RAG Pipeline | Inicialização de caches | Estático |
| 7.5 | `lia-agent-system/app/config/langsmith.py` | Configuração de tracing LangSmith/LangFuse para observabilidade de LLM | Todos os agentes LLM | Inicialização (habilita tracing) | Estático (env-based) |

### Sector Rules (Policy Engine)

| Setor | Autonomia | HITL Threshold | FG L3 | Rationale |
|-------|-----------|----------------|--------|-----------|
| tech | Média | Médio | Sim | Alta regulação em IA hiring |
| financeiro | Baixa | Alto | Sim | BCB 498, SOX compliance |
| saúde | Baixa | Alto | Sim | Profissão regulada, segurança do paciente |
| RPO | Alta | Baixo | Sim | Volume hiring, significância estatística |
| varejo | Alta | Baixo | Não | Menor risco, L1+L2 suficientes |
| logística | Alta | Baixo | Não | Menor risco, L1+L2 suficientes |

---

## 8. WSI & Avaliação

Documentos que implementam a metodologia WSI (WeDO Screening Intelligence) — Bloom's Taxonomy + Dreyfus Model + Big Five.

| # | Arquivo | Descrição | Consumido por | Momento no Fluxo | Tipo |
|---|---------|-----------|---------------|-------------------|------|
| 8.1 | `lia-agent-system/app/domains/cv_screening/constants/wsi_constants.py` | Constantes WSI: dimensões de avaliação, distribuições de senioridade, escalas Bloom (1-6), Dreyfus (1-5), Big Five (OCEAN) | WSI Service, WSI Interview Graph, Score Normalization | Geração de perguntas WSI + scoring | Estático |
| 8.2 | `lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py` | Grafo LangGraph para entrevista WSI (1.141 linhas): 8 stages — INIT → LOAD → GENERATE → AWAIT → VALIDATE → SCORE → ADVANCE → COMPLETE. PostgresSaver checkpoint | CV Screening Agent, Triagem endpoints | Fluxo completo de triagem (step 6 no fluxo de 11 steps) | Estático (grafo) + Dinâmico (state) |
| 8.3 | `lia-agent-system/training/rag_knowledge/wsi_methodology/report_templates.md` | Templates de relatório WSI para RAG knowledge base | Semantic Search, RAG Pipeline | Quando agente precisa gerar relatórios WSI formatados | Estático (RAG KB) |
| 8.4 | `lia-agent-system/app/services/wsi_service.py` | WSI Service: geração de perguntas CBI/Bloom/Dreyfus/Big Five, scoring, calibração | WSI Interview Graph, CV Screening endpoints | Geração e avaliação de perguntas WSI | Dinâmico |
| 8.5 | `lia-agent-system/app/services/score_normalization_service.py` | Normalização de scores: z-score, percentil, calibração por senioridade | WSI Service, CV Screening Agent | Pós-scoring — normaliza para comparabilidade (step 9 no fluxo) | Dinâmico |
| 8.6 | `lia-agent-system/app/services/calibration_service.py` | Calibração de scores + BiasAuditSnapshot + Four-Fifths Rule: detecta se taxa de aprovação de grupo demográfico < 80% de outro | WSI Service, Score Normalization | Pós-scoring — calibra para comparabilidade real (step 9) | Dinâmico |

---

## 9. Templates de Vaga por Setor

Templates de vaga pré-definidos por setor/indústria. Consumidos pelo Job Wizard e Template Learning Service.

| # | Arquivo | Setor | Qtd Templates | Consumido por | Tipo |
|---|---------|-------|:---:|---------------|------|
| 9.1 | `lia-agent-system/app/data/templates/tecnologia.py` | Tecnologia | Variável | Job Wizard, Template Seeder | Estático |
| 9.2 | `lia-agent-system/app/data/templates/financas.py` | Finanças | Variável | Job Wizard, Template Seeder | Estático |
| 9.3 | `lia-agent-system/app/data/curated_templates_tech.py` | Tecnologia (curado) | 10+ | Job Template Service, Template Learning | Estático |
| 9.4 | `lia-agent-system/app/data/curated_templates_vendas.py` | Vendas | 10+ | Job Template Service, Template Learning | Estático |
| 9.5 | `lia-agent-system/app/data/curated_templates_saude.py` | Saúde | 10+ | Job Template Service, Template Learning | Estático |
| 9.6 | `lia-agent-system/app/data/curated_templates_rh.py` | Recursos Humanos | 10+ | Job Template Service, Template Learning | Estático |
| 9.7 | `lia-agent-system/app/data/curated_templates_operacoes.py` | Operações | 10+ | Job Template Service, Template Learning | Estático |
| 9.8 | `lia-agent-system/app/data/curated_templates_marketing.py` | Marketing | 10+ | Job Template Service, Template Learning | Estático |
| 9.9 | `lia-agent-system/app/data/curated_templates_financas.py` | Finanças (curado) | 10+ | Job Template Service, Template Learning | Estático |
| 9.10 | `lia-agent-system/app/data/curated_templates_customer_success.py` | Customer Success | 10+ | Job Template Service, Template Learning | Estático |
| 9.11 | `lia-agent-system/app/data/curated_templates_cs.py` | Ciência da Computação / CS | 10+ | Job Template Service, Template Learning | Estático |
| 9.12 | `lia-agent-system/app/data/curated_templates_administrativo.py` | Administrativo | 10+ | Job Template Service, Template Learning | Estático |
| 9.13 | `lia-agent-system/app/data/brazilian_job_templates.py` | Multi-setor (Brasil) | 50+ | Job Wizard, Template Seeder, JD Generation | Estático |

### Fluxo de Consumo

```
Recrutador inicia criação de vaga
  → Job Wizard detecta setor
  → Template Learning recomenda template (se ≥3 jobs anteriores)
  → Fallback: curated_templates_{setor}.py
  → Template Seeder popula campos pré-preenchidos
  → Recrutador customiza via wizard multi-step
```

---

## 10. Robustness & Resilience

Documentos que protegem a plataforma contra falhas, injeção de prompt, inputs inválidos e erros de sistema. Bandas transversais ativas via `EnhancedAgentMixin`.

| # | Arquivo | Descrição | Consumido por | Momento no Fluxo | Tipo |
|---|---------|-----------|---------------|-------------------|------|
| 10.1 | `lia-agent-system/app/shared/robustness/defensive_prompts.py` | Proteção contra prompt injection: wrappa todas as chamadas LLM com instruções de segurança | Todos os agentes (via `EnhancedAgentMixin`) | Pré-LLM — adicionado ao system prompt | Estático |
| 10.2 | `lia-agent-system/app/shared/robustness/response_filter.py` | Filtro pós-LLM: detecta e remove conteúdo inapropriado, PII vazado, ou instruções de jailbreak na resposta | Todos os agentes | Pós-LLM — antes de retornar ao usuário | Estático |
| 10.3 | `lia-agent-system/app/shared/robustness/input_validation.py` | Validação de input: sanitização, limites de tamanho, detecção de padrões maliciosos | Todos os endpoints, agentes | Pré-processamento (antes de tudo) | Estático |
| 10.4 | `lia-agent-system/app/shared/robustness/intent_schemas.py` | Schemas de intenção: define estrutura esperada para cada tipo de intent | `IntentRouter`, `CascadedRouter` | Roteamento de intenção | Estático |
| 10.5 | `lia-agent-system/app/shared/robustness/error_handling.py` | Tratamento de erros centralizado: fallbacks, retry logic, mensagens amigáveis | Todos os agentes e services | Quando ocorre exceção | Estático |
| 10.6 | `lia-agent-system/app/shared/robustness/context_management.py` | Gestão de contexto: truncamento, priorização, window sliding | Agentes com contexto longo | Pré-LLM (otimização de contexto) | Estático |
| 10.7 | `lia-agent-system/app/shared/resilience/circuit_breaker.py` | Circuit breaker: protege contra cascata de falhas em serviços externos (LLM, Pearch, ATS) | Todos os serviços que chamam APIs externas | Runtime — abre circuito após N falhas consecutivas | Dinâmico (state) |
| 10.8 | `lia-agent-system/app/shared/resilience/dlq_service.py` | Dead Letter Queue: mensagens que falharam N vezes vão para DLQ para retry manual | Communication Service, ATS Sync, Automation | Após N retries falhados | Dinâmico (DB-backed) |
| 10.9 | `lia-agent-system/app/shared/resilience/stats_manager.py` | Estatísticas de resiliência: tracking de circuit breaker states, retry counts, failure rates | Monitoring, Health endpoints | Contínuo (background) | Dinâmico |
| 10.10 | `lia-agent-system/app/shared/resilience/cache_manager_service.py` | Cache manager: gestão centralizada de caches (Redis, in-memory, TTL) | Semantic Search, RAG Pipeline, LLM Job Classification | Operações de cache | Dinâmico |

---

## 11. Inteligência & Learning

Documentos que implementam o ciclo fechado de aprendizado: captura silenciosa → A/B testing → learning loop → model drift → finetuning export.

| # | Arquivo | Descrição | Consumido por | Momento no Fluxo | Tipo |
|---|---------|-----------|---------------|-------------------|------|
| 11.1 | `lia-agent-system/app/shared/learning/learning_loop_service.py` | Learning Loop (captura silenciosa): registra padrões de uso em todos os endpoints sem impactar latência | Todos os endpoints (middleware-style) | **Cada request** — captura em background | Dinâmico |
| 11.2 | `lia-agent-system/app/shared/learning/ab_testing_service.py` | A/B Testing: hash-based assignment, z-score, p-value, `get_variant`, `record_result`, `get_test_results` (~307 linhas) | Endpoints de prompt variant, email templates | Assignment na request; resultado quando conversão ocorre | Dinâmico (DB-backed) |
| 11.3 | `lia-agent-system/app/shared/intelligence/template_learning/template_learning_service.py` | Template Learning: auto-recomenda templates após 3 jobs. `record_send`, `recommend_template`, `get_performance` (~150 linhas) | Job Wizard, Email Service | Recomendação na criação de vaga; learning em cada send/open/click | Dinâmico (DB-backed) |
| 11.4 | `lia-agent-system/app/shared/intelligence/ab_testing/email_template_seeder.py` | Email Template Seeder: popula variantes de A/B testing de email no startup (~80 linhas) | Startup (lifespan) | Seed na inicialização — uma vez | Seed |
| 11.5 | `lia-agent-system/app/services/routing_learning_service.py` | Routing Learning: confidence multipliers para melhorar roteamento de intenção ao longo do tempo | `IntentRouter`, `CascadedRouter` | Pós-roteamento — ajusta confidence baseado em feedback | Dinâmico |
| 11.6 | `lia-agent-system/app/services/model_drift_service.py` | Model Drift Detection (4 dimensões): accuracy, latency, token usage, fairness drift | Monitoring, Alert Service | Background (periódico) — detecta degradação do modelo | Dinâmico |
| 11.7 | `lia-agent-system/app/shared/learning/learning_snapshot_service.py` | Learning Snapshot: pontos de rollback para estados de aprendizado | Learning Loop, A/B Testing | Quando snapshot é criado (manual ou automático) | Dinâmico |
| 11.8 | `lia-agent-system/app/shared/learning/finetuning_export.py` | Finetuning Export: exporta dados de learning loop em formato para finetuning de LLMs | Admin endpoints | Manual (export sob demanda) | Dinâmico |

---

## 12. Memory & Search

Documentos que gerenciam memória conversacional, busca semântica, embeddings e resolução de referências.

| # | Arquivo | Descrição | Consumido por | Momento no Fluxo | Tipo |
|---|---------|-----------|---------------|-------------------|------|
| 12.1 | `lia-agent-system/app/shared/memory/conversation_state.py` | Estado conversacional: entity tracking, pronoun resolution, slot filling | Todos os agentes (via `EnhancedAgentMixin`) | **Cada turno** — persiste entre interações | Dinâmico |
| 12.2 | `lia-agent-system/app/shared/memory/candidate_list_store.py` | Store de listas de candidatos: mantém resultados de busca entre turnos | Sourcing Agent, Talent Agent | Pós-busca — armazena para referência posterior | Dinâmico |
| 12.3 | `lia-agent-system/app/shared/memory/reference_resolver.py` | Resolução de referências: "ele", "esse candidato", "a vaga" → entidade correta | Orchestrator, todos os agentes | Pré-processamento de cada mensagem | Dinâmico |
| 12.4 | `lia-agent-system/libs/agents-core/lia_agents_core/long_term_memory.py` | Long-term Memory: episódios + compressão LLM. Comprime após 30 dias. Integra com LangGraph checkpointer | Agentes com memória habilitada | Leitura a cada turno; compressão em background (30d) | Dinâmico |
| 12.5 | `lia-agent-system/app/shared/intelligence/semantic_search_service.py` | Semantic Search: Gemini 768-dim embeddings, Redis cache, busca por similaridade semântica | RAG Pipeline, Sourcing Agent, Job Matching | Busca semântica de candidatos/vagas | Dinâmico |
| 12.6 | `lia-agent-system/app/shared/intelligence/embedding_service.py` | Embedding Service: geração e cache de embeddings vetoriais | Semantic Search, Job Embedding Service | Geração de embeddings para novos documentos | Dinâmico |
| 12.7 | `lia-agent-system/app/shared/intelligence/smart_extractor.py` | Smart Extractor: extração estruturada de dados de texto livre (CV, JD, mensagens) | CV Parser, JD Import, Job Wizard | Extração de campos de documentos não-estruturados | Dinâmico |
| 12.8 | `lia-agent-system/app/shared/intelligence/param_patterns.py` | Param Patterns: padrões regex para extração de parâmetros (datas, valores, nomes) | Input Validation, Smart Extractor | Pré-processamento de input | Estático |

---

## 13. Governance & Monitoring

Documentos que implementam feature flags, monitoramento de agentes, sampling para revisão humana e alertas de drift.

| # | Arquivo | Descrição | Consumido por | Momento no Fluxo | Tipo |
|---|---------|-----------|---------------|-------------------|------|
| 13.1 | `lia-agent-system/app/shared/governance/feature_flag_service.py` | Feature Flags: controla rollout de features de compliance (FairnessGuard L3, Template Learning, A/B Testing) | Todos os serviços que verificam feature flags | Cada request (check de flag) | Dinâmico (DB-backed) |
| 13.2 | `lia-agent-system/app/shared/governance/agent_monitoring_service.py` | Agent Monitoring: rastreia aderência a guidelines em real-time (compliance rate, fairness rate, SLA) | Todos os agentes | Contínuo (metrics collection) | Dinâmico |
| 13.3 | `lia-agent-system/app/services/human_review_sampling_service.py` | Human Review Sampling: seleciona amostras de decisões de agentes para revisão humana (por risco, por setor) | Pipeline Transition, CV Screening, Communication | Pós-decisão — sampling baseado em risco | Dinâmico |
| 13.4 | `lia-agent-system/app/services/drift_alert_service.py` | Drift Alerts: notificações quando model drift excede threshold | Model Drift Service, Monitoring | Background (periódico) | Dinâmico |

---

## 14. Communication & Integrations

Documentos de serviços de comunicação e integrações externas.

| # | Arquivo | Descrição | Consumido por | Momento no Fluxo | Tipo |
|---|---------|-----------|---------------|-------------------|------|
| 14.1 | `lia-agent-system/app/domains/communication/services/email_service.py` | Email Service (SendGrid/Resend): envio de emails transacionais e em lote | Communication Agent, Automation | Envio de feedback, outreach, notificações | Dinâmico (API externa) |
| 14.2 | `lia-agent-system/app/domains/communication/services/whatsapp_service.py` | WhatsApp Service (Twilio): envio de mensagens WhatsApp, templates, media | Communication Agent, Triagem WhatsApp | Outreach, triagem, follow-up | Dinâmico (API externa) |
| 14.3 | `lia-agent-system/app/domains/communication/services/email_templates_data.py` | Templates de email pré-definidos: feedback positivo/negativo, outreach, confirmação de entrevista | Email Service | Seleção de template no envio | Estático |
| 14.4 | `lia-agent-system/app/services/voice_service.py` | Voice Service (Deepgram/Whisper + OpenAI TTS): transcrição e síntese de voz | Triagem por voz, Voice Screening | Triagem por voz (alternativa a chat/WhatsApp) | Dinâmico (API externa) |
| 14.5 | `lia-agent-system/app/services/microsoft_graph_service.py` | Microsoft Graph: integração com Teams, calendário Outlook | Interview Scheduling, Communication | Agendamento via Teams, notificações | Dinâmico (API externa) |
| 14.6 | `lia-agent-system/app/domains/sourcing/services/apify_service.py` | Apify Service (5 actors): scraping de LinkedIn, GitHub, Glassdoor para enriquecimento de perfis | Sourcing Enrich Agent | Enriquecimento de perfis de candidatos | Dinâmico (API externa) |
| 14.7 | `lia-agent-system/app/domains/interview_scheduling/services/scheduling_service.py` | Scheduling Service: geração de ICS, conflito de agenda, timezone handling | Interview Scheduling Agent | Agendamento de entrevistas | Dinâmico |
| 14.8 | `lia-agent-system/app/domains/ats_integration/services/gupy_service.py` | Gupy ATS Client: sync de vagas e candidatos com Gupy | ATS Integration Agent | Sync bidirecional com Gupy | Dinâmico (API externa) |
| 14.9 | `lia-agent-system/app/domains/ats_integration/services/pandape_service.py` | Pandapé ATS Client: sync com Pandapé | ATS Integration Agent | Sync bidirecional com Pandapé | Dinâmico (API externa) |
| 14.10 | `lia-agent-system/app/domains/ats_integration/services/merge_ats_service.py` | Merge.dev ATS Client: sync com ATS via Merge API (universal connector) | ATS Integration Agent | Sync com qualquer ATS suportado pelo Merge | Dinâmico (API externa) |
| 14.11 | `lia-agent-system/app/domains/sourcing/services/pearch_service.py` | Pearch AI Client: busca externa de candidatos | Sourcing Search Agent | Busca externa (quando banco local insuficiente) | Dinâmico (API externa) |
| 14.12 | `lia-agent-system/app/services/rag_pipeline_service.py` | RAG Pipeline: busca semântica + ElasticSearch + PgVector + WRF reranking | Sourcing Agent, Talent Funnel | Busca unificada de candidatos | Dinâmico |
| 14.13 | `lia-agent-system/app/services/wrf_dynamic_k_service.py` | WRF Dynamic K: reranking dinâmico de resultados de busca (~100 linhas) | RAG Pipeline | Pós-busca (reranking) | Dinâmico |
| 14.14 | `lia-agent-system/app/domains/sourcing/services/llm_job_classification_service.py` | LLM Job Classification: classificação semântica de fit job-candidato (~120 linhas) | RAG Pipeline (pós-WRF) | Pós-reranking (classificação de qualificação) | Dinâmico |
| 14.15 | `lia-agent-system/app/domains/communication/services/communication_service.py` | Communication Service central: dispatcher de comunicações multi-canal + `CandidateQuarantine` (3 meses) | Communication Agent, todos os canais | Despacho de comunicações | Dinâmico |
| 14.16 | `lia-agent-system/app/services/google_calendar_client.py` | Google Calendar Client: integração com Google Calendar para disponibilidade e agendamento | Interview Scheduling Agent, Scheduling Service | Agendamento de entrevistas via Google Calendar | Dinâmico (API externa) |

---

## 15. Documentação Técnica (docs/)

Documentos de referência em `lia-agent-system/docs/` que servem como guias, specs e runbooks.

| # | Arquivo | Descrição | Status de Consumo pelo Código |
|---|---------|-----------|-------------------------------|
| 15.1 | `lia-agent-system/docs/FRIA_EU_AI_ACT.md` | Fundamental Rights Impact Assessment — EU AI Act compliance | Referência (não consumido em runtime) |
| 15.2 | `lia-agent-system/docs/RUNBOOK_BACKUP_RECOVERY.md` | Runbook de backup e recovery | Referência operacional |
| 15.3 | `lia-agent-system/docs/RUNBOOK_DEGRADATION.md` | Runbook de degradação graceful | Referência operacional |
| 15.4 | `lia-agent-system/docs/RUNBOOK_INCIDENT_PLAYBOOKS.md` | Playbooks de incidentes | Referência operacional |
| 15.5 | `lia-agent-system/docs/API_REFERENCE.md` | Referência completa da API (362+ endpoints) | Referência (OpenAPI auto-gerado) |
| 15.6 | `attached_assets/WSI_FLOW_PONTA_A_PONTA_(1)_1776425690186.md` | Fluxo WSI ponta-a-ponta (canônico) | Referência metodológica autoritativa |
| 15.7 | `attached_assets/WSI_METHODOLOGY_COMPLETE_v2.bak_1776458966926.md` | Metodologia WSI v2 (canônico, complementar) | Referência metodológica autoritativa |
| 15.8 | `lia-agent-system/docs/methodology/AI_GOVERNANCE.md` | Governança de IA: princípios, guardrails, HITL | Referência — informa FairnessGuard e Policy Engine |
| 15.9 | `lia-agent-system/docs/methodology/AI_SOURCING_METHODOLOGY.md` | Metodologia de sourcing: boolean search, canais, estratégias | Referência — informa Sourcing Agent prompts |
| 15.10 | `lia-agent-system/docs/ai-prompts/AI_PROMPT_CREATION_GUIDE.md` | Guia de criação de prompts: boas práticas, CoT, few-shot | Referência — informa `cot.py` e few-shot design |
| 15.11 | `lia-agent-system/docs/ai-prompts/AI_PROMPTS_CATALOG.md` | Catálogo de todos os prompts da plataforma | Referência — catálogo de referência |
| 15.12 | `lia-agent-system/docs/FAIRNESS_GUARD_COVERAGE.md` | Cobertura do FairnessGuard: categorias, patterns, endpoints | Referência — documenta `fairness_guard.py` |
| 15.13 | `lia-agent-system/docs/integrations/ATS_INTEGRATION_SPEC.md` | Spec de integração com ATS (Gupy, Pandapé, Merge) | Referência — informa ATS services |
| 15.14 | `lia-agent-system/docs/integrations/PEARCH_GUIDE.md` | Guia de integração com Pearch AI | Referência — informa `pearch_service.py` |
| 15.15 | `lia-agent-system/docs/integrations/MICROSOFT_INTEGRATION_GUIDE.md` | Guia de integração com Microsoft Graph/Teams | Referência — informa `microsoft_graph_service.py` |
| 15.16 | `lia-agent-system/docs/workflows/WORKFLOW_COMPLETO.md` | Fluxo completo da plataforma | Referência arquitetural |
| 15.17 | `lia-agent-system/docs/workflows/communication-workflow.md` | Workflow de comunicação multi-canal | Referência — informa Communication Agent |
| 15.18 | `lia-agent-system/docs/workflows/JOB_FREEZE_WORKFLOW.md` | Workflow de congelamento de vagas | Referência — informa Job Management |
| 15.19 | `lia-agent-system/docs/architecture/AI_AGENT_AUDIT_REPORT.md` | Relatório de auditoria de agentes IA | Referência — informa monitoring |
| 15.20 | `lia-agent-system/docs/architecture/IMPLEMENTATION_ROADMAP.md` | Roadmap de implementação | Referência de planejamento |
| 15.21 | `lia-agent-system/docs/CONCEITOS_IA_WEDOTALENT.md` | Conceitos de IA da WeDOTalent | Referência conceitual |
| 15.22 | `lia-agent-system/docs/MAPA_CAMADA_INTELIGENCIA.md` | Mapa da camada de inteligência | Referência arquitetural |
| 15.23 | `lia-agent-system/docs/PLANO_CICLO_FECHADO_LIA.md` | Plano do ciclo fechado de aprendizado | Referência — informa Learning Loop |

### Documento Externo de Referência

| # | Arquivo | Descrição | Status de Consumo |
|---|---------|-----------|-------------------|
| 15.24 | `attached_assets/WEDOTALENT_GUIA_COMPLETO_v3.3_PT.md` | Guia Completo WeDOTalent v3.3: 13 Crenças, 8 Inegociáveis, 18 Production Readiness, metodologia WSI, governance, compliance | Referência máxima — informa toda a arquitetura de compliance, governance e avaliação |

---

## 16. Tabela-Resumo & Gaps

### 16.1 Contagem por Categoria

| # | Categoria | Qtd Arquivos | Tipo Predominante | Consumo Runtime |
|---|-----------|:---:|-------------------|:---:|
| 1 | Persona & Identity | 9 | Estático (YAML/PY) | Sim — todos os agentes |
| 2 | System Prompts por Domínio | 22 | Estático (PY) | Sim — cada agente |
| 3 | Domain Prompt YAMLs | 10 | Estático (YAML) | Sim — via PromptLoader |
| 4 | Few-Shot Examples | 6 | Estático (PY) | Sim — in-context learning |
| 5 | Compliance & FairnessGuard | 10 | Misto (Estático + DB) | Sim — banda transversal |
| 6 | PII & LGPD | 6 | Misto (Estático + API) | Sim — banda transversal |
| 7 | Configurações & Rules | 5 | Misto (JSON/PY + DB) | Sim — policy engine |
| 8 | WSI & Avaliação | 6 | Misto (Estático + Dinâmico) | Sim — fluxo de triagem |
| 9 | Templates de Vaga por Setor | 13 | Estático (PY) | Sim — Job Wizard |
| 10 | Robustness & Resilience | 10 | Misto | Sim — banda transversal |
| 11 | Inteligência & Learning | 8 | Dinâmico (DB-backed) | Sim — ciclo fechado |
| 12 | Memory & Search | 8 | Dinâmico | Sim — cada turno |
| 13 | Governance & Monitoring | 4 | Dinâmico | Sim — contínuo |
| 14 | Communication & Integrations | 16 | Dinâmico (API externa) | Sim — por demanda |
| 15 | Documentação Técnica | 24 | Estático (MD) | Não — referência |
| | **TOTAL** | **157** | | |

### 16.2 Distribuição por Tipo

| Tipo | Qtd | Descrição |
|------|:---:|-----------|
| Estático (hardcoded) | ~68 | Prompts, constants, templates, configs — versionados em código |
| Dinâmico (DB-backed) | ~42 | Guardrails, policies, learning data, audit trail — persistidos no PostgreSQL |
| Seed | ~4 | Dados iniciais populados no startup (guardrails, A/B testing, templates) |
| API externa | ~10 | Integrações com serviços externos (SendGrid, Twilio, Pearch, Apify, etc.) |
| Referência (não runtime) | ~24 | Documentação técnica, guias, specs — não consumidos pelo código |
| RAG Knowledge Base | ~1 | Arquivos em `lia-agent-system/training/rag_knowledge/` indexados para busca semântica |

### 16.3 Cobertura das Bandas Transversais (24 Dimensões × 8 Domínios + LIA)

**Dimensões Originais (11):**

| Dimensão | Arquivo Principal | Cobertura (de 8 domínios) | LIA |
|----------|-------------------|:---:|:---:|
| fairness.py | `fairness_guard.py` | 2/8 (jobs, srcp) | auto |
| cache.py | `cache_manager_service.py` | 3/8 (jobs, appl, msg) | auto |
| memory.py | `conversation_state.py` | 3/8 (jobs, appl, srcp) | auto |
| cards.py | Componentes frontend | 2/8 | auto |
| tasks.py (Celery) | Tasks assíncronas | 1/8 (jobs) | ⚠ |
| fact_checker.py | `fact_checker.py` | 1/8 (jobs) | auto |
| security.py | `input_validation.py` | 2/8 (jobs, sched) | auto |
| dispatcher.py | `communication_dispatcher.py` | 1/8 (jobs) | auto |
| graph.py / nodes.py | LangGraph nodes | 1/8 (jobs) | auto |
| agents/ | Agentes ReAct | 1/8 (jobs) | auto |
| react_agent.py | `react_agent_registry.py` | 1/8 (jobs) | auto |

**Novas Dimensões (13) — TODAS `X` nos 8 domínios, apenas `auto` na LIA:**

| Dimensão | Arquivo Principal | Status |
|----------|-------------------|--------|
| audit/ (SOX) | `audit_service.py` | Apenas LIA (auto) |
| guardrails.py (DB) | `guardrail_repository.py` | Apenas LIA (auto) |
| confidence.py | `confidence.py` (agents-core) | Apenas LIA (auto) |
| bias_audit.py | Via `calibration_service.py` | Apenas LIA (auto) |
| pii_masking.py (pré-LLM) | `pii_masking.py` | Apenas LIA (auto) |
| hiring_policy.py | `policy_engine_service.py` | Apenas LIA (auto) |
| feedback/ (learning) | `learning_loop_service.py` | Apenas LIA (auto) |
| anti_sycophancy.py | `anti_sycophancy_block.py` | Apenas LIA (auto) |
| persona.py (YAML) | `lia_persona.yaml` | Apenas LIA (auto) |
| wsi_graph.py | `wsi_interview_graph.py` | Apenas LIA (auto) |
| checkpoints/ | LangGraph PostgresSaver | Apenas LIA (auto) |
| dlq_service.py | `dlq_service.py` | Apenas LIA (auto) |
| semantic_intel.py | `semantic_search_service.py` | Apenas LIA (auto) |

### 16.4 Documentos Referenciados no Guia v3.3 mas NÃO Existentes como Arquivo Separado

| Conceito do Guia v3.3 | Status no Código | Observação |
|------------------------|------------------|------------|
| Manual do DPO (Data Protection Officer) | Não existe como arquivo | Funcionalidade distribuída em `pii_masking.py`, `lgpd_compliance.py`, `data_subject_requests.py` |
| Matriz RACI de Compliance | Não existe como arquivo | Responsabilidades definidas inline nos services |
| Playbook de Incident Response para IA | Parcial em `RUNBOOK_INCIDENT_PLAYBOOKS.md` | Falta seção específica para falhas de LLM/bias detectado |
| SLA de Resposta por Setor | Não existe como arquivo | Definido inline em `policy_engine_service.py` (sector rules) |
| Catálogo de Métricas DEI | Não existe como arquivo | Métricas distribuídas em `bias_audit`, `fairness_guard`, `calibration_service` |
| Template de DPIA (Data Protection Impact Assessment) | Parcial em `FRIA_EU_AI_ACT.md` | FRIA cobre EU AI Act mas não DPIA específico LGPD |
| Glossário Unificado de Termos RH-IA | Parcial em `lia_persona.yaml` (hr_vocabulary) | Vocabulário HR existe mas não inclui termos de IA/ML |
| Guia de Onboarding de Novos Agentes | Não existe como arquivo | Processo é implícito: criar domain/, agents/, system_prompt, registrar no `react_agent_registry` |
| Runbook de Rollback de Learning | Não existe como arquivo | Funcionalidade existe em `learning_snapshot_service.py` mas sem runbook |
| Benchmark de Fairness por Setor | Não existe como arquivo | Thresholds definidos inline em `fairness_guard.py` e `policy_engine_service.py` |

### 16.5 Documentos que Existem no Repositório mas NÃO São Consumidos pelo Código

| Arquivo | Descrição | Potencial de Consumo |
|---------|-----------|---------------------|
| `lia-agent-system/docs/FRIA_EU_AI_ACT.md` | FRIA EU AI Act | Poderia alimentar FairnessGuard com critérios EU AI Act |
| `lia-agent-system/docs/methodology/AI_GOVERNANCE.md` | Governança de IA | Poderia ser indexado no RAG para consultas de policy |
| `lia-agent-system/docs/methodology/AI_SOURCING_METHODOLOGY.md` | Metodologia sourcing | Poderia ser few-shot para Sourcing Agent |
| `lia-agent-system/docs/ai-prompts/AI_PROMPT_CREATION_GUIDE.md` | Guia de prompts | Poderia ser RAG KB para admin de prompts |
| `lia-agent-system/docs/ai-prompts/AI_PROMPTS_CATALOG.md` | Catálogo de prompts | Poderia alimentar `PromptRegistry` dinamicamente |
| `lia-agent-system/docs/integrations/ATS_INTEGRATION_SPEC.md` | Spec ATS | Poderia ser RAG KB para ATS Integration Agent |
| `lia-agent-system/docs/integrations/PEARCH_GUIDE.md` | Guia Pearch | Poderia ser RAG KB para Sourcing Agent |
| `lia-agent-system/docs/integrations/MICROSOFT_INTEGRATION_GUIDE.md` | Guia Microsoft | Poderia ser RAG KB para Scheduling Agent |
| `lia-agent-system/docs/workflows/WORKFLOW_COMPLETO.md` | Workflow completo | Poderia alimentar Orchestrator com fluxo de referência |
| `attached_assets/WEDOTALENT_GUIA_COMPLETO_v3.3_PT.md` | Guia WeDO v3.3 | Poderia ser indexado no RAG como referência máxima de governance |
| `lia-agent-system/docs/CONCEITOS_IA_WEDOTALENT.md` | Conceitos IA | Poderia ser RAG KB para onboarding |
| `lia-agent-system/docs/PLANO_CICLO_FECHADO_LIA.md` | Plano ciclo fechado | Poderia alimentar Learning Loop com targets |

---

## Apêndice A: Infraestrutura Core (agents-core)

Arquivos em `lia-agent-system/libs/agents-core/lia_agents_core/` que compõem a infraestrutura transversal dos agentes:

| Arquivo | Descrição | Consumido por |
|---------|-----------|---------------|
| `enhanced_agent_mixin.py` | Mixin que injeta 16 capacidades em cada agente (FairnessGuard, PII, Audit, Anti-Sycophancy, etc.) | Todos os 11 agentes ReAct |
| `react_agent_registry.py` | Registry de agentes ReAct — registra e resolve agentes por domínio | Startup, Orchestrator |
| `langgraph_base.py` | Base class para agentes LangGraph | Todos os agentes baseados em grafo |
| `langgraph_react_base.py` | Base class para agentes ReAct + LangGraph | Agentes ReAct |
| `long_term_memory.py` | Memória de longo prazo com compressão LLM | Agentes com memória habilitada |
| `confidence.py` | ConfidenceNode — calibração de confidence scores | Pipeline agents |
| `checkpointer.py` | PostgresSaver checkpointer para LangGraph | WSI Interview Graph |
| `working_memory.py` | Working memory para agentes | Todos os agentes |
| `observability.py` | Integração com LangSmith/LangFuse | Todos os agentes |
| `nodes.py` | Nodes base para grafos LangGraph | Agentes baseados em grafo |
| `execution_log_store.py` | Log de execução de agentes | Todos os agentes |
| `state_machine.py` | Máquina de estados para agentes | Agentes com estado |
| `streaming_callback.py` | Callback para streaming de respostas | Agentes com streaming |
| `timed_tool_node.py` | Node com timeout para tools | Agentes com tools externas |

## Apêndice B: Orchestrator

Arquivos em `lia-agent-system/app/orchestrator/` que compõem o ponto de entrada central:

| Arquivo | Descrição | Consumido por |
|---------|-----------|---------------|
| `main_orchestrator.py` | Orchestrator principal — ponto de entrada de todas as mensagens do recrutador | API endpoints de chat |
| `intent_router.py` | Roteamento de intenção (3 tiers: regex → similarity → LLM) | MainOrchestrator |
| `cascaded_router.py` | Router cascateado com fallback entre tiers | IntentRouter |
| `fast_router.py` | Tier 1 — regex-based fast routing | CascadedRouter |
| `semantic_cache.py` | Cache semântico para respostas frequentes | MainOrchestrator |
| `policy_engine.py` | Policy engine inline no orchestrator | MainOrchestrator |
| `context_adapter.py` | Adaptador de contexto para agentes | MainOrchestrator |
| `memory_resolver.py` | Resolução de memória para contexto | MainOrchestrator |
| `state_manager.py` | Gestão de estado do orchestrator | MainOrchestrator |
| `task_planner.py` | Planejador de tarefas multi-step | MainOrchestrator |
| `pending_action.py` | Ações pendentes de confirmação HITL | MainOrchestrator |
| `action_executor.py` | Executor de ações aprovadas | MainOrchestrator |

---

*Documento gerado em 31/03/2026 — Inventário completo de 157 documentos de referência organizados em 15 categorias + 2 apêndices.*
