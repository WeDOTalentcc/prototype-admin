# Wizard de Criação de Vagas - Documentação Técnica Completa

> **Versão:** 5.0  
> **Data:** Janeiro 2026  
> **Status:** Documentação Consolidada e Definitiva  
> **Última Atualização:** 28 de Janeiro de 2026  
> **Documentos Consolidados:** `FLUXO_CRIACAO_VAGA.md`, `job-wizard-enhancement-plan.md`, `LIA_PROACTIVE_ANALYSIS_SYSTEM.md`, `SETTINGS_MENU_MAPPING_FOR_WIZARD.md`, `clustering-embeddings-proposal.md`

Este documento é a **referência definitiva** sobre o processo de criação de vagas no Wizard da Plataforma LIA. Consolida toda a documentação técnica, fluxos, arquitetura, sistemas de aprendizado e integrações.

---

## Índice

1. [Resumo Executivo](#1-resumo-executivo)
2. [Arquitetura de IA da Plataforma](#2-arquitetura-de-ia-da-plataforma)
3. [Learning Hub System (5 Fases)](#3-learning-hub-system-5-fases)
4. [Estrutura do Wizard (3 Fases, 7 Etapas)](#4-estrutura-do-wizard-3-fases-7-etapas)
5. [Tipologia de Campos](#5-tipologia-de-campos)
6. [JobDraft - Estado Intermediário](#6-jobdraft---estado-intermediário)
7. [Níveis de Confiança](#7-níveis-de-confiança)
8. [Fluxo Detalhado por Etapa](#8-fluxo-detalhado-por-etapa)
9. [Catálogo de Skills e Competências](#9-catálogo-de-skills-e-competências)
10. [Sistemas Transversais](#10-sistemas-transversais)
11. [Análise de Uso de LLMs](#11-análise-de-uso-de-llms)
    - [11.4 Análise Comparativa: Claude Sonnet vs Gemini Flash](#114-análise-comparativa-claude-sonnet-vs-gemini-flash)
12. [Intelligence Layer](#12-intelligence-layer)
13. [Personalização por Recrutador](#13-personalização-por-recrutador)
14. [Loop de Aprendizagem da IA](#14-loop-de-aprendizagem-da-ia)
15. [Pós-Wizard: Adição de Candidatos](#15-pós-wizard-adição-de-candidatos)
16. [Metodologias de Busca de Candidatos](#16-metodologias-de-busca-de-candidatos)
17. [Notificações Multi-Canal](#17-notificações-multi-canal)
18. [Sistema de Geração de Job Description](#18-sistema-de-geração-de-job-description)
19. [Sistema de Interação com Sugestões via Chat](#19-sistema-de-interação-com-sugestões-via-chat)
20. [Mapeamento de Configurações da Empresa](#20-mapeamento-de-configurações-da-empresa)
21. [Sistema de Análise Proativa da LIA](#21-sistema-de-análise-proativa-da-lia)
22. [Diagnóstico e Recomendações](#22-diagnóstico-e-recomendações)
23. [API Endpoints Implementados](#23-api-endpoints-implementados)
24. [Histórico de Mudanças](#24-histórico-de-mudanças)
25. [Próximos Passos: Clustering e Embeddings](#25-próximos-passos-clustering-e-embeddings)

---

## 1. Resumo Executivo

### 1.1 O que é o Wizard de Criação de Vagas

O Wizard de Criação de Vagas é o fluxo central da Plataforma LIA para abertura de novas posições. Ele guia o recrutador através de etapas estruturadas, utilizando inteligência artificial para:

- Extrair automaticamente informações de descrições em linguagem natural
- Pré-preencher campos com defaults inteligentes da empresa
- Sugerir skills, competências e faixas salariais baseadas em benchmarks
- Gerar perguntas de triagem usando metodologia WSI
- Criar Job Descriptions estruturadas e otimizadas
- Calibrar buscas de candidatos com feedback do recrutador

### 1.2 Objetivos do Sistema

| Objetivo | Descrição |
|----------|-----------|
| **Eficiência** | Reduzir tempo de criação de vagas de horas para minutos |
| **Qualidade** | Garantir vagas completas com todos os critérios necessários |
| **Aprendizado** | Sistema que melhora com o uso (Learning Hub) |
| **Personalização** | Adaptar experiência por recrutador e empresa |
| **Integração** | Conectar com ATSs, job boards e sistemas de RH |

### 1.3 Princípios Orientadores

| Princípio | Descrição |
|-----------|-----------|
| **Flexibilidade** | Manter estrutura atual do wizard, fazer melhorias incrementais |
| **Não-Disruptivo** | Evitar mudanças radicais na dinâmica existente |
| **Conversacional + Formulário** | Equilibrar conversa com campos estruturados |
| **Incremental** | Implementar em fases, validar cada uma |
| **Data-Driven** | Decisões baseadas em dados históricos e outcomes |
| **Personalizado** | Adaptar experiência por recrutador |

### 1.4 Status de Implementação

| Feature | Status | Data |
|---------|--------|------|
| Tipologia de Campos | ✅ Implementado | Jan 2026 |
| JobDraft | ✅ Implementado | Jan 2026 |
| Níveis de Confiança | ✅ Implementado | Jan 2026 |
| Catálogo de Skills | ✅ Implementado | Jan 2026 |
| Intelligence Layer | ✅ Implementado | Jan 2026 |
| Personalização por Recrutador | ✅ Implementado | Jan 2026 |
| API Endpoints | ✅ Implementado | Jan 2026 |
| Feedback Learning | ✅ Implementado | Jan 2026 |
| JD Generation (v1/v2) | ✅ Implementado | Jan 2026 |
| Suggestion Interaction via Chat | ✅ Implementado | Jan 2026 |
| Learning Hub (5 Fases) | ✅ Implementado | Jan 2026 |
| Feature Flags | ✅ Implementado | Jan 2026 |
| Field Toggles | ✅ Implementado | Jan 2026 |
| Teams → WhatsApp Connector | ✅ Implementado | Jan 2026 |

### 1.5 Integrações Completas

- [x] **Pearch AI Integrado** - Substituídas funções mock por chamadas reais (`liaApi.searchCandidatesLocal` e `liaApi.searchCandidates`)
- [x] **Market Benchmark** - Endpoint backend `/job-wizard/salary-benchmark` + método frontend `getSalaryBenchmark` com UI mostrando dados internos + mercado
- [x] **Auto-save de Rascunho** - Hook `useWizardAutoSave` com salvamento dual (localStorage + backend) a cada 30s
- [x] **Restauração de Drafts entre Sessões** - Sistema completo com `wizardDraftId` persistido em localStorage
- [x] **UI de Progresso de Competências** - Contador visual "X/3 Técnicas" e "X/3 Comportamentais" com checkmarks
- [x] **Auto-preenchimento do Menu Configurações** - `fetchCompanyConfig` preenche automaticamente work_model, tech_stack, departments, benefits
- [x] **Calibração Flexível** - Slider para escolher 1-5 candidatos ideais
- [x] **Acessibilidade Aprimorada** - aria-labels, roles e aria-live adicionados em componentes críticos

---

## 2. Arquitetura de IA da Plataforma

### 2.1 Visão Geral do Sistema Multi-Agente

A Plataforma LIA utiliza uma **arquitetura multi-agente** (v2.2) composta por **1 Orquestrador + 9 Agentes Especializados**. Cada agente é responsável por uma área específica do processo de recrutamento.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ORCHESTRATOR (Ag.0)                                │
│   ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐               │
│   │  Intent Router  │ │  Task Planner   │ │  Policy Engine  │               │
│   └────────┬────────┘ └────────┬────────┘ └────────┬────────┘               │
│            │                   │                   │                        │
│            └───────────────────┼───────────────────┘                        │
│                               │                                             │
│            ┌──────────────────┴──────────────────┐                          │
│            ▼                                      ▼                          │
│   ┌─────────────────┐                   ┌─────────────────┐                 │
│   │  State Manager  │                   │ Enhanced Registry│                 │
│   └─────────────────┘                   └─────────────────┘                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   Ag.1        │   │   Ag.2        │   │   Ag.3        │   │   Ag.4        │
│  Job Planner  │   │   Sourcing    │   │  CV Screening │   │  Interviewer  │
│  (Job Intake) │   │               │   │   (Triagem)   │   │  (WSI Voice)  │
└───────────────┘   └───────────────┘   └───────────────┘   └───────────────┘
        │                   │                   │                   │
        ▼                   ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   Ag.5        │   │   Ag.6        │   │   Ag.7        │   │   Ag.8        │
│ WSI Evaluator │   │  Scheduling   │   │ Analyst &     │   │ ATS Integrator│
│ (Avaliador)   │   │  (Agendador)  │   │ Feedback      │   │ (Gupy/Pandapé)│
└───────────────┘   └───────────────┘   └───────────────┘   └───────────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │   Recruiter Assistant │
                        │  (Assistente Pessoal) │
                        └───────────────────────┘
```

### 2.2 Descrição dos Agentes

| ID | Agente | Responsabilidade | Intents Principais |
|----|--------|------------------|-------------------|
| **Ag.0** | **Orchestrator** | Roteamento de intents, memória de contexto, delegação de tarefas | `route_intent`, `plan_tasks` |
| **Ag.1** | **Job Planner** | Criação/edição de vagas, extração de JD, geração de perguntas WSI | `create_job`, `update_job`, `generate_wsi_questions` |
| **Ag.2** | **Sourcing** | Busca de candidatos, strings booleanas, outreach, integração Pearch | `search_candidates`, `pearch_search`, `outreach_whatsapp` |
| **Ag.3** | **CV Screening** | Parsing de CV, triagem curricular, score inicial, detecção de red flags | `parse_cv`, `screen_candidate`, `rank_candidates` |
| **Ag.4** | **Interviewer** | Entrevistas WSI via WhatsApp/voz, transcrição de áudio | `start_wsi_interview`, `voice_screening` |
| **Ag.5** | **WSI Evaluator** | Scoring WSI (Bloom/Dreyfus/Big Five), pareceres, comparação | `calculate_wsi_score`, `compare_candidates`, `generate_parecer` |
| **Ag.6** | **Scheduling** | Agendamento de entrevistas, integração com calendários | `schedule_interview`, `check_availability` |
| **Ag.7** | **Analyst & Feedback** | KPIs, relatórios, comunicação em massa, feedback para candidatos | `generate_kpi_report`, `send_feedback` |
| **Ag.8** | **ATS Integrator** | Sincronização com Gupy/Pandapé, import/export, compliance LGPD | `sync_candidate`, `gupy_sync` |
| **Special** | **Recruiter Assistant** | Assistente pessoal do recrutador, tarefas pendentes, resumos | `task_summary`, `daily_briefing` |

### 2.3 Serviços de Inteligência (Services Layer)

| Serviço | Função | Usado no Wizard |
|---------|--------|-----------------|
| `SkillsCatalogService` | Catálogo de skills com sugestões baseadas em cargo/senioridade | Etapa 1, 3 |
| `LearningHubService` | Hub central de aprendizado - 5 fases completas | Todas etapas |
| `FeatureFlagService` | Controle de rollout gradual de funcionalidades | Todas etapas |
| `LiaFieldConfigService` | Field Toggles para controle de consumo de dados pela IA | Etapa 1-5 |
| `FeedbackLearningService` | Aprende com correções do recrutador | Etapa 4, 7 |
| `PatternDetectorService` | Detecta padrões no histórico de vagas da empresa | Etapa 1, 4 |
| `MarketBenchmarkService` | Benchmarks de salário do mercado | Etapa 4 |
| `CompletenessService` | Verifica completude da vaga e campos obrigatórios | Etapa 6 |
| `JDGeneratorService` | Gera descrições de vaga estruturadas | Etapa 6 |
| `WSIService` | Metodologia WSI para avaliação de candidatos | Etapa 5 |
| `IntelligenceLayerService` | Pattern Detection, Outcome Correlation, Sugestões | Etapa 1-7 |
| `RecruiterPersonalizationService` | Personalização por recrutador | Etapa 1-7 |
| `ConfidencePolicyService` | Cálculo determinístico de confiança | Etapa 1-6 |

### 2.4 Componentes do Orchestrator

| Componente | Função |
|------------|--------|
| **Intent Router** | Classifica a intenção do usuário e roteia para o agente correto |
| **Task Planner** | Decompõe tarefas complexas em subtarefas sequenciais |
| **Policy Engine** | Valida limites, permissões e aprovações |
| **State Manager** | Gerencia estado de conversações e contexto |
| **Enhanced Registry** | Registro de agentes com fallback chains e roteamento por confiança |

### 2.5 Provedores de LLM

| Provider | Modelo | Uso Principal | Usado no Wizard | Tokens Típicos |
|----------|--------|---------------|-----------------|----------------|
| **Anthropic Claude** | claude-sonnet-4-5 | Análises complexas, geração de JD, pareceres | ✅ Sim | 2.000-4.000/chamada |
| **Google Gemini** | gemini-2.5-flash | Extração de entidades, busca semântica | ✅ Sim | 500-1.500/chamada |
| **OpenAI** | gpt-4o | Disponível como fallback alternativo | ❌ Não usado | N/A |

> **Nota:** OpenAI GPT-4o está configurado no `LLMService` mas não é utilizado no fluxo do wizard. Os provedores primários são Claude (para análise/geração) e Gemini (para extração/busca).

### 2.6 Arquitetura Frontend/Backend

#### Arquitetura Anterior
```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (Next.js)                      │
├─────────────────────────────────────────────────────────────┤
│  job-creation-wizard.tsx (3138 linhas)                      │
│  ├── 11 steps fixos                                         │
│  ├── Painéis por step (básico, técnico, comportamental...)  │
│  ├── Chat com LIA à esquerda                                │
│  └── buildContextPrompt() → envia contexto da empresa       │
│                                                              │
│  use-company-lia-instructions.ts                            │
│  ├── 19 campos configuráveis                                │
│  ├── Toggles por campo (admin configura)                    │
│  └── Filtra o que LIA recebe como contexto                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                       │
├─────────────────────────────────────────────────────────────┤
│  job_intake_agent.py (2385 linhas)                          │
│  ├── 8 stages definidos                                     │
│  ├── CRITERIA_DETECTION_PROMPT (extrai campos)              │
│  ├── Prompts por stage (LIA_STAGE_MESSAGES)                 │
│  └── Cria JobVacancy diretamente                            │
└─────────────────────────────────────────────────────────────┘
```

#### Arquitetura Implementada
```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (Next.js)                      │
├─────────────────────────────────────────────────────────────┤
│  job-creation-wizard.tsx (melhorado)                        │
│  ├── 11 steps (mantidos)                                    │
│  ├── ✅ Indicadores de confiança por campo                  │
│  ├── ✅ Badges "Inferido" / "Confirmado" / "Default"        │
│  └── ✅ Painéis adaptam baseado em tipologia                │
│                                                              │
│  ✅ use-job-draft.ts                                        │
│  ├── Estado local do draft                                  │
│  ├── Rastreia inferred_fields vs confirmed_fields           │
│  └── Sincroniza com backend                                 │
│                                                              │
│  ✅ field-confidence-indicator.tsx                          │
│  └── Mostra nível de confiança visual                       │
│                                                              │
│  ✅ field-origin-badge.tsx                                  │
│  └── Mostra origem do valor (inferido, default, benchmark)  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                       │
├─────────────────────────────────────────────────────────────┤
│  ✅ models/job_draft.py                                     │
│  └── JobDraft (estado intermediário antes de JobVacancy)    │
│                                                              │
│  ✅ schemas/field_typology.py                               │
│  └── FieldTypology enum + mapeamento de campos              │
│                                                              │
│  ✅ services/confidence_policy_service.py                   │
│  └── Cálculo determinístico de confiança                    │
│                                                              │
│  ✅ services/skills_catalog_service.py                      │
│  └── Catálogo de skills por área                            │
│                                                              │
│  ✅ services/intelligence_layer_service.py                  │
│  └── Pattern Detection, Outcome Correlation, Suggestions    │
│                                                              │
│  ✅ services/recruiter_personalization_service.py           │
│  └── Personalização por recrutador                          │
│                                                              │
│  job_intake_agent.py (refatorado)                           │
│  ├── Usa tipologia para decidir comportamento               │
│  ├── Retorna confidence_map no response                     │
│  ├── ✅ Integra Intelligence Layer para enriquecimento      │
│  ├── ✅ Integra Personalização por Recrutador               │
│  └── Cria JobDraft em vez de JobVacancy                     │
│                                                              │
│  ✅ api/v1/intelligence.py                                  │
│  └── Endpoints de inteligência (data-quality, context, etc) │
│                                                              │
│  ✅ api/v1/recruiter_profiles.py                            │
│  └── Endpoints de perfil do recrutador                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Learning Hub System (5 Fases)

O Learning Hub é o sistema central de aprendizado da plataforma, implementado em 5 fases:

### 3.1 Fase 1: Skills Learning Loop

**Objetivo:** Aprender padrões de skills por cargo/senioridade

```
┌─────────────────────────────────────────────────────────────────┐
│                    SKILLS LEARNING LOOP                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Recrutador confirma/corrige skill sugerida                  │
│     ↓                                                           │
│  2. CompanyLearning registra confirmação                        │
│     ↓                                                           │
│  3. Após 3+ confirmações → skill é "promovida"                  │
│     ↓                                                           │
│  4. Agentes usam learning context em sugestões futuras          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Modelo:** `CompanyLearning`
- `skill_confirmations`: Dict de skills confirmadas por cargo
- `promoted_skills`: Skills promovidas (threshold: 3 confirmações)

**Endpoint:** `POST /lia/learning/confirm-skill`

### 3.2 Fase 2: Responsibilities Deduplication

**Objetivo:** Eliminar redundância de responsabilidades entre stages

```
┌─────────────────────────────────────────────────────────────────┐
│            RESPONSIBILITIES DEDUPLICATION                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Responsabilidade detectada no Stage 1                       │
│     ↓                                                           │
│  2. Hash SHA256 calculado para normalização                     │
│     ↓                                                           │
│  3. Deduplicação automática (remove variações similares)        │
│     ↓                                                           │
│  4. Confirmação do recrutador armazena versão canônica          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Endpoint:** `POST /lia/learning/confirm-responsibility`

### 3.3 Fase 3: Stage Feedback Learning

**Objetivo:** Aprender com feedback de recrutadores em cada stage

```
┌─────────────────────────────────────────────────────────────────┐
│                  STAGE FEEDBACK LEARNING                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Stages 2-7:                                                    │
│  • Recrutador pode dar thumbs up/down em sugestões              │
│  • Feedback registrado por stage/field/recrutador               │
│  • Sistema ajusta sugestões baseado em padrões                  │
│                                                                  │
│  Métricas coletadas:                                            │
│  • acceptance_rate por stage                                    │
│  • correction_rate por field                                    │
│  • time_spent por stage                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Endpoint:** `POST /api/v1/lia/learning/stage-feedback`

### 3.4 Fase 4: Outcome Learning

**Objetivo:** Conectar resultados de contratação ao aprendizado

```
┌─────────────────────────────────────────────────────────────────┐
│                    OUTCOME LEARNING                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Eventos monitorados:                                           │
│  • Candidato contratado (hired)                                 │
│  • Time-to-fill da vaga                                         │
│  • Desempenho pós-contratação (90 dias)                         │
│  • Retenção (180 dias)                                          │
│                                                                  │
│  Insights gerados:                                              │
│  • Skills que correlacionam com sucesso                         │
│  • Faixas salariais que atraem melhores candidatos              │
│  • Canais de sourcing mais efetivos                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Modelo:** `JobOutcome` (em `feedback_learning.py`)

**Endpoints:**
- `POST /api/v1/lia/learning/job-outcome`
- `POST /api/v1/lia/learning/outcome-insights`

### 3.5 Fase 5: Analytics Dashboard

**Objetivo:** Visualização de métricas de learning e saúde do sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                   ANALYTICS DASHBOARD                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Métricas expostas:                                             │
│  • Health Score (0-100) por empresa                             │
│  • Skills coverage por cargo                                    │
│  • Acceptance rate por stage                                    │
│  • Learning velocity (skills promovidas/mês)                    │
│                                                                  │
│  Status: API Completa, UI Pendente                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Endpoint:** `POST /api/v1/lia/learning/dashboard`

### 3.6 Mapeamento Completo de Endpoints (Learning Hub)

| Fase | Endpoint | Método | Descrição |
|------|----------|--------|-----------|
| 1 - Skills | `/lia/learning/confirm-skill` | POST | Confirma skill para promoção |
| 2 - Responsibilities | `/lia/learning/confirm-responsibility` | POST | Confirma responsabilidade |
| 1-2 | `/lia/learning/context` | POST | Obtém contexto de learning |
| 3 - Stage Feedback | `/api/v1/lia/learning/stage-feedback` | POST | Registra feedback por stage |
| 4 - Outcome | `/api/v1/lia/learning/job-outcome` | POST | Registra outcome de vaga |
| 4 - Outcome | `/api/v1/lia/learning/outcome-insights` | POST | Obtém insights de outcomes |
| 5 - Analytics | `/api/v1/lia/learning/dashboard` | POST | Dashboard de analytics |
| 5 - Analytics | `/api/v1/lia/learning/skills-deduplicated` | POST | Skills deduplicadas |

### 3.7 Sistema de Aprendizado Unificado

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         UNIFIED LEARNING SYSTEM                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  WIZARD STAGE 1                LEARNING HUB                    AGENTS       │
│  ┌─────────────────┐          ┌─────────────────┐          ┌─────────────┐  │
│  │ Recrutador      │          │ LearningHub     │          │ Sourcing    │  │
│  │ confirma/rejeita│─────────▶│ Service         │◀─────────│ Agent       │  │
│  │ skills/resps    │          │                 │          │             │  │
│  │                 │          │ • record_skill  │          │ WSI         │  │
│  │ POST /learning/ │          │ • record_resp   │          │ Evaluator   │  │
│  │ confirm-skill   │          │ • get_context   │          └─────────────┘  │
│  └─────────────────┘          └────────┬────────┘                           │
│                                        │                                     │
│                                        ▼                                     │
│                     ┌─────────────────────────────────────┐                  │
│                     │           DATABASE                  │                  │
│                     │ • CompanySkill (promoted após 3x)   │                  │
│                     │ • CompanyResponsibility (hash dedup)│                  │
│                     │ • AgentFeedback (histórico)         │                  │
│                     │ • CompanyPattern (padrões)          │                  │
│                     └─────────────────────────────────────┘                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Catálogos Dinâmicos (por Empresa)

| Catálogo | Tabela | Promoção | Benefício |
|----------|--------|----------|-----------|
| **Skills Dinâmicas** | `company_skills` | Após 3 confirmações | Sugestões personalizadas por empresa |
| **Responsabilidades** | `company_responsibilities` | Hash SHA256 dedup | Evita repetição, melhora qualidade |
| **Padrões** | `company_patterns` | Detecção automática | "77% das vagas são híbridas" |

#### Isolamento Multi-Tenant

Todos os dados de learning são isolados por `company_id`:
- Skills de Empresa A **nunca** aparecem para Empresa B
- Padrões são calculados apenas com dados históricos da própria empresa
- Feedback de agentes é segregado por empresa

---

## 4. Estrutura do Wizard (3 Fases, 7 Etapas)

### 4.1 Diagrama do Fluxo Consolidado

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                        WIZARD DE CRIAÇÃO DE VAGA v5.0                          │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  FASE 1: CONSTRUÇÃO          FASE 2: ATIVAÇÃO        FASE 3: SELEÇÃO          │
│  ┌─────────────────────┐    ┌──────────────────┐    ┌───────────────────────┐ │
│  │ 1. input-evaluation │    │                  │    │                       │ │
│  │ 2. job-description  │───▶│ 6. review-publish│───▶│ 7. search-calibration │ │
│  │ 3. competencies     │    │                  │    │                       │ │
│  │ 4. salary           │    │                  │    │                       │ │
│  │ 5. wsi-questions    │    │                  │    │                       │ │
│  └─────────────────────┘    └──────────────────┘    └───────────────────────┘ │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                        SISTEMAS TRANSVERSAIS                             │  │
│  ├─────────────────────────────────────────────────────────────────────────┤  │
│  │ Learning Hub │ Feature Flags │ Field Toggles │ Empty Field Notifications │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Mapeamento de Etapas

| Etapa | ID | Fase | Agentes/Serviços | LLM |
|-------|-----|------|------------------|-----|
| 1 | `input-evaluation` | Construção | Job Intake Agent, IntelligenceLayerService | Gemini |
| 2 | `job-description` | Construção | PatternDetectorService, CompanyConfigService | - |
| 3 | `competencies` | Construção | SkillsCatalogService, LearningHubService | - |
| 4 | `salary` | Construção | MarketBenchmarkService, FeedbackLearningService | - |
| 5 | `wsi-questions` | Construção | WSI Generator, WSIService | Claude |
| 6 | `review-publish` | Ativação | CompletenessService, JDGeneratorService | Claude |
| 7 | `search-calibration` | Seleção | Sourcing Agent, WSI Evaluator | Gemini + Claude |

### 4.3 Migração do Fluxo (10 → 7 etapas)

| Fluxo Anterior (10 etapas) | Novo Fluxo (7 etapas) | Mudança |
|---------------------------|----------------------|---------|
| 1. description | 1. input-evaluation | Expandido com análise proativa |
| 2. basic-info | 2. job-description | Renomeado |
| 3. competencies | 3. competencies | Mantido |
| 4. salary | 4. salary | Aprimorado com sugestões |
| 5. wsi-questions | 5. wsi-questions | Mantido |
| 6. review + 7. pre-publish | 6. review-publish | **Consolidado** |
| 8-10. candidate-search/calibration/active-search | 7. search-calibration | **Consolidado** |

### 4.4 FASE 1: CONSTRUÇÃO

#### Etapa 1: Input & Evaluation (`input-evaluation`)

```typescript
interface InputEvaluationData {
  rawDescription: string
  detectedFields: DetectedField[]
  evaluationResult: EvaluationResponse
  messages: ChatMessage[]
}

interface DetectedField {
  field: string
  value: string | number | boolean
  confidence: number
  source: 'text_extraction' | 'company_default' | 'benchmark' | 'inference'
}
```

#### Etapa 2: Job Description (`job-description`)

```typescript
interface JobDescriptionData {
  title: string
  department: string
  location: string
  workModel: 'remote' | 'hybrid' | 'onsite'
  hybridDays?: number
  employmentType: 'clt' | 'pj' | 'freelancer' | 'intern'
  manager?: { id: string; name: string }
  teamSize?: number
  reportingTo?: string
}
```

#### Etapa 3: Competências (`competencies`)

```typescript
interface TechnicalSkill {
  id: string; name: string;
  level: 'Básico' | 'Intermediário' | 'Avançado'
  required: boolean
  category: 'language' | 'framework' | 'database' | 'tool' | 'methodology'
  weight: number // 1-5
  source: 'catalog' | 'detected' | 'manual'
}

interface BehavioralCompetency {
  id: string; name: string; weight: number // 1-5
  justification: string; enabled: boolean
  source: 'catalog' | 'detected' | 'manual'
}
```

#### Etapa 4: Remuneração (`salary`)

```typescript
interface SalaryInfo {
  minSalary: number; maxSalary: number;
  suggestedMin: number; suggestedMax: number;
  minBonus: number; maxBonus: number; bonusCriteria: string;
  benefits: Benefit[];
  marketPosition: 'below' | 'at' | 'above'; percentile: number
}

interface Benefit {
  id: string; name: string; value?: string;
  enabled: boolean; source: 'company_default' | 'manual'
}
```

#### Etapa 5: Triagem WSI (`wsi-questions`)

```typescript
interface WSIQuestion {
  id: string; question: string;
  type: 'open' | 'yes-no' | 'numeric' | 'multiple-choice'
  required: boolean; options?: string[];
  expectedAnswer?: string | number | boolean;
  batch: number // 1, 2, 3 para envio gradual
  category?: 'technical' | 'behavioral' | 'situacional' | 'fit'
  source: 'company_default' | 'job_specific' | 'auto_generated'
}
```

### 4.5 FASE 2: ATIVAÇÃO

#### Etapa 6: Revisão e Publicação (`review-publish`)

```typescript
interface PublishingPlatform {
  id: string; name: string; icon: string;
  enabled: boolean; connected: boolean; estimatedReach: number
}

const AVAILABLE_PLATFORMS: PublishingPlatform[] = [
  { id: 'linkedin', name: 'LinkedIn Jobs', enabled: true, connected: true, estimatedReach: 5000 },
  { id: 'site', name: 'Site Carreiras', enabled: true, connected: true, estimatedReach: 1000 },
  { id: 'gupy', name: 'Gupy', enabled: false, connected: false, estimatedReach: 3000 },
  { id: 'indeed', name: 'Indeed', enabled: false, connected: false, estimatedReach: 8000 }
]
```

### 4.6 FASE 3: SELEÇÃO

#### Etapa 7: Busca e Calibração (`search-calibration`)

```typescript
interface CalibrationCandidate {
  id: string; name: string; photoUrl?: string; linkedinUrl?: string;
  currentRole: string; currentCompany: string; location: string;
  overallScore: number;
  highlights: { icon: string; label: string; value: string }[]
  matchCriteria: CalibrationMatchCriteria[]
}

interface CalibrationMatchCriteria {
  label: string; matched: boolean; value?: string; weight: number
}
```

**Fluxo de Calibração:**
```
1. Busca Inicial (base local + Pearch AI)
     │
     ▼
2. Seleção para Calibração (1-5 candidatos)
     │
     ▼
3. Recrutador avalia cada candidato
     ├── ✅ Aprovar → Adiciona ao kanban + feedback positivo
     └── ❌ Rejeitar → Feedback negativo + motivo
     │
     ▼
4. RecruiterPersonalizationService registra preferências
     │
     ▼
5. Busca refinada com perfil calibrado
```

---

## 5. Tipologia de Campos

### 5.1 Classificação de Campos

Cada campo do wizard é classificado em uma tipologia que define seu comportamento:

```python
class FieldTypology(str, Enum):
    """Tipologia de campos para tratamento diferenciado"""
    
    IMPLICIT = "implicit"
    # Inferidos silenciosamente, não interrompem o fluxo
    # Ex: currency (sempre BRL), country (sempre Brasil)
    
    PROBABLE = "probable"
    # Auto-preenchidos via defaults da empresa
    # Mostrados mas não perguntados ativamente
    # Ex: work_model, employment_type, benefits
    
    CONDITIONAL = "conditional"
    # Ativados por gatilhos semânticos
    # Ex: hybrid_days (só se work_model = hybrid)
    
    CRITICAL = "critical"
    # Obrigatórios, bloqueiam avanço sem validação
    # Ex: job_title, seniority
    
    OPERATIONAL = "operational"
    # Uso interno, não interrompem fluxo
    # Ex: created_by, company_id, timestamps
    
    DERIVED = "derived"
    # Calculados automaticamente
    # Ex: job_complexity, estimated_ttf
```

### 5.2 Mapeamento Completo de Campos

| Campo | Tipologia | Comportamento |
|-------|-----------|---------------|
| `job_title` | CRITICAL | Sempre perguntar se não informado |
| `seniority` | CRITICAL | Inferir + confirmar se confiança < 80% |
| `department` | PROBABLE | Usar default se disponível |
| `location` | PROBABLE | Usar default da empresa |
| `work_model` | PROBABLE | Usar default da empresa |
| `hybrid_days` | CONDITIONAL | Só mostra se work_model = hybrid |
| `employment_type` | PROBABLE | Usar default da empresa |
| `salary_min` | CRITICAL | Sugerir benchmark + confirmar |
| `salary_max` | CRITICAL | Sugerir benchmark + confirmar |
| `currency` | IMPLICIT | Sempre BRL, nunca perguntar |
| `skills` | PROBABLE | Inferir + permitir edição |
| `behavioral_competencies` | PROBABLE | Sugerir baseado em role |
| `benefits` | PROBABLE | Usar defaults da empresa |
| `manager_id` | PROBABLE | Sugerir se detectado no contexto |
| `pipeline_stages` | PROBABLE | Usar template da empresa |
| `screening_questions` | DERIVED | Gerar baseado em WSI |
| `job_description` | DERIVED | Gerar baseado em dados |
| `estimated_ttf` | DERIVED | Calcular baseado em histórico |
| `job_complexity` | DERIVED | Calcular baseado em requisitos |
| `created_by` | OPERATIONAL | Automático, não mostrar |
| `company_id` | OPERATIONAL | Automático, não mostrar |

### 5.3 Implementação da Tipologia

**Arquivo**: `lia-agent-system/app/schemas/field_typology.py`

```python
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass

class FieldTypology(str, Enum):
    IMPLICIT = "implicit"
    PROBABLE = "probable"
    CONDITIONAL = "conditional"
    CRITICAL = "critical"
    OPERATIONAL = "operational"
    DERIVED = "derived"

@dataclass
class FieldDefinition:
    name: str
    typology: FieldTypology
    required: bool = False
    default_source: Optional[str] = None  # "company", "benchmark", "inference"
    condition: Optional[str] = None  # Para CONDITIONAL
    confidence_threshold: float = 0.7  # Threshold para auto-aplicar

FIELD_DEFINITIONS: Dict[str, FieldDefinition] = {
    "job_title": FieldDefinition(
        name="job_title",
        typology=FieldTypology.CRITICAL,
        required=True,
        confidence_threshold=0.9
    ),
    "seniority": FieldDefinition(
        name="seniority",
        typology=FieldTypology.CRITICAL,
        required=True,
        default_source="inference",
        confidence_threshold=0.8
    ),
    # ... demais campos
}
```

---

## 6. JobDraft - Estado Intermediário

### 6.1 Por que JobDraft?

Benefícios do estado intermediário:
- Rastrear quais campos foram inferidos vs confirmados
- Estado de "rascunho" antes de publicar
- Rastrear confiança por campo
- Permitir rollback de campos individuais
- Histórico completo de mudanças

### 6.2 Modelo JobDraft Implementado

**Arquivo**: `lia-agent-system/app/models/job_draft.py`

```python
class JobDraftStatus(str, Enum):
    DRAFT = "draft"           # Rascunho inicial
    STRUCTURED = "structured" # Campos estruturados
    REVIEWED = "reviewed"     # Revisado pelo recrutador
    CONFIRMED = "confirmed"   # Confirmado para publicação
    PUBLISHED = "published"   # Publicado (JobVacancy criada)
    CANCELLED = "cancelled"   # Cancelado

class JobDraft(Base):
    """
    Estado intermediário da vaga antes de publicação.
    Permite rastrear inferências, confirmações e confiança.
    """
    __tablename__ = "job_drafts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False)
    recruiter_id = Column(String, nullable=False)
    conversation_id = Column(String, nullable=True)
    
    # Status do draft
    status = Column(SQLEnum(JobDraftStatus), default=JobDraftStatus.DRAFT)
    current_step = Column(Integer, default=1)
    
    # Input original
    raw_input = Column(Text)
    imported_jd = Column(Text)
    
    # Campos da vaga (estruturados)
    job_title = Column(String(200))
    department = Column(String(100))
    seniority = Column(String(50))
    location = Column(String(200))
    work_model = Column(String(50))
    employment_type = Column(String(50))
    salary_min = Column(Float)
    salary_max = Column(Float)
    currency = Column(String(10), default="BRL")
    
    # Listas estruturadas
    skills = Column(ARRAY(String))
    behavioral_competencies = Column(JSON)
    benefits = Column(ARRAY(String))
    languages = Column(ARRAY(String))
    
    # Campos derivados
    generated_jd = Column(Text)
    screening_questions = Column(JSON)
    pipeline_stages = Column(JSON)
    
    # Rastreamento de origem dos campos
    inferred_fields = Column(JSON, default={})
    # {"seniority": {"value": "Senior", "confidence": 0.85, "source": "text_analysis"}}
    
    confirmed_fields = Column(JSON, default={})
    # {"seniority": {"value": "Senior", "confirmed_at": "2026-01-24T10:00:00"}}
    
    company_defaults_used = Column(JSON, default={})
    # {"work_model": "hybrid", "benefits": [...]}
    
    confidence_map = Column(JSON, default={})
    # {"job_title": 0.95, "seniority": 0.85, "salary_min": 0.65}
    
    # Insights e alertas
    insights = Column(JSON, default=[])
    warnings = Column(JSON, default=[])
    
    # Referência à vaga publicada
    published_job_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    structured_at = Column(DateTime)
    reviewed_at = Column(DateTime)
    published_at = Column(DateTime)
```

### 6.3 DraftFieldHistory - Histórico de Mudanças

```python
class DraftFieldHistory(Base):
    """Histórico de mudanças em campos do draft"""
    __tablename__ = "draft_field_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    draft_id = Column(UUID(as_uuid=True), ForeignKey("job_drafts.id"), nullable=False)
    
    field_name = Column(String(100), nullable=False)
    old_value = Column(JSON)
    new_value = Column(JSON)
    
    change_type = Column(String(50))  # "inferred", "confirmed", "edited", "reverted"
    confidence_at_change = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String)  # recruiter_id ou "system"
```

---

## 7. Níveis de Confiança

### 7.1 Sistema de Confiança Determinístico

**Arquivo**: `lia-agent-system/app/services/confidence_policy_service.py`

```python
class ConfidenceAction(str, Enum):
    APPLY_SILENT = "apply_silent"      # Aplica sem avisar
    APPLY_NOTIFY = "apply_notify"      # Aplica e mostra badge
    ASK_USER = "ask_user"              # Pergunta ao usuário
    ALERT_CONFLICT = "alert_conflict"  # Alerta de conflito

@dataclass
class ConfidenceThresholds:
    """Thresholds configuráveis"""
    silent_apply: float = 0.85   # Aplica silenciosamente
    apply_notify: float = 0.70   # Aplica com notificação
    ask_user: float = 0.50       # Pergunta ao usuário
    # Abaixo de 0.50 = alert_conflict

class ConfidencePolicyService:
    """
    Serviço para cálculo determinístico de confiança.
    NÃO usa LLM - apenas regras e histórico.
    """
    
    def calculate_field_confidence(
        self,
        field: str,
        value: Any,
        sources: Dict[str, Any]
    ) -> float:
        """
        Calcula confiança para um campo de forma determinística.
        
        Sources podem incluir:
        - text_extraction: valor extraído do texto do recrutador
        - company_default: valor default da empresa
        - benchmark: valor de benchmark de mercado
        - similar_jobs: valor de vagas similares
        - correction_history: histórico de correções
        """
        base_confidence = 0.0
        
        # 1. Confiança base por fonte
        source_weights = {
            "text_extraction": 0.7,
            "company_default": 0.85,
            "benchmark": 0.6,
            "similar_jobs": 0.75,
        }
        
        for source, source_value in sources.items():
            if source_value is not None:
                weight = source_weights.get(source, 0.5)
                base_confidence = max(base_confidence, weight)
        
        # 2. Ajuste por histórico de correções
        if "correction_history" in sources:
            history = sources["correction_history"]
            if history.get("correction_rate", 0) > 0.3:
                base_confidence *= 0.8
        
        return min(1.0, base_confidence)
```

### 7.2 Fluxo de Decisão de Confiança

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUXO DE CONFIANÇA                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Confiança ≥ 85%                                                │
│  └── APPLY_SILENT: Aplica valor sem notificação                 │
│                                                                  │
│  70% ≤ Confiança < 85%                                          │
│  └── APPLY_NOTIFY: Aplica + mostra badge "Inferido"             │
│                                                                  │
│  50% ≤ Confiança < 70%                                          │
│  └── ASK_USER: Pergunta ao recrutador                           │
│                                                                  │
│  Confiança < 50%                                                │
│  └── ALERT_CONFLICT: Mostra alerta de conflito                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.3 Indicadores Visuais de Confiança

```typescript
// field-confidence-indicator.tsx
interface ConfidenceIndicatorProps {
  confidence: number
  field: string
  source: 'text_extraction' | 'company_default' | 'benchmark' | 'inference'
}

// Renderização:
// ● Verde (85-100%): Alta confiança
// ● Amarelo (70-84%): Média confiança  
// ● Laranja (50-69%): Baixa confiança
// ● Vermelho (<50%): Conflito
```

---

## 8. Fluxo Detalhado por Etapa

### 8.1 Etapa 1: Input & Evaluation (`input-evaluation`)

**O que o Recrutador Faz:**
- Descreve a vaga em linguagem natural (ou cola JD)
- Visualiza critérios detectados automaticamente
- Recebe análise proativa de compensação vs. mercado

**O que a LIA Faz (Job Intake Agent):**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. RECEBE INPUT DO RECRUTADOR                                               │
│     • Descrição livre: "Preciso de um Dev Python Senior em SP"              │
│     • OU Job Description colada                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  2. EXTRAÇÃO DE ENTIDADES (LLM: Gemini 2.5 Flash)                            │
│     • Cargo: "Desenvolvedor Python"                                         │
│     • Senioridade: "Senior"                                                 │
│     • Skills detectadas: [Python, FastAPI, PostgreSQL]                      │
│     • Modelo de trabalho: "Híbrido" (inferido)                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  3. BUSCA CONFIGURAÇÕES DA EMPRESA                                           │
│     • work_model padrão                                                     │
│     • departamentos disponíveis                                             │
│     • faixa salarial interna para cargos similares                          │
│     • benefícios configurados                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  4. BUSCA LEARNING CONTEXT                                                   │
│     • Skills promovidas para o cargo                                        │
│     • Responsabilidades confirmadas anteriormente                           │
│     • Ajustes aprendidos do recrutador                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  5. APLICA TIPOLOGIA E CALCULA CONFIANÇA                                     │
│     • job_title: CRITICAL, confiança 95%                                    │
│     • seniority: CRITICAL, confiança 85%                                    │
│     • work_model: PROBABLE, confiança 90% (default empresa)                 │
│     • salary_min: CRITICAL, confiança 60% (benchmark)                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  6. RETORNA RESPOSTA COM CAMPOS PRÉ-PREENCHIDOS                              │
│     {                                                                        │
│       "detected_fields": {...},                                             │
│       "confidence_map": {"job_title": 0.95, "seniority": 0.85, ...},        │
│       "suggestions": [...],                                                  │
│       "proactive_insights": {...}                                           │
│     }                                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Tokens LLM Consumidos:** ~1.500 (Gemini Flash)

**Endpoints Utilizados:**
- `POST /api/v1/lia/job-wizard/evaluate`
- `GET /api/v1/company/{id}/field-toggles`
- `POST /lia/learning/context`

### 8.2 Etapa 2: Job Description (`job-description`)

**O que o Recrutador Faz:**
- Confirma/ajusta título, departamento, localização
- Define modelo de trabalho e tipo de contrato
- Visualiza badges de origem dos dados

**O que a LIA Faz:**
- Exibe campos pré-preenchidos com badges de origem
- Sugere ajustes baseados em padrões da empresa
- Detecta campos condicionais (hybrid_days se work_model = hybrid)

**Tokens LLM Consumidos:** 0 (determinístico)

### 8.3 Etapa 3: Competências (`competencies`)

**O que o Recrutador Faz:**
- Seleciona skills técnicas de catálogo expandido
- Define pesos (1-5) para cada skill
- Marca skills como obrigatórias ou desejáveis
- Seleciona competências comportamentais

**O que a LIA Faz:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SUGESTÃO DE SKILLS                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Busca skills promovidas (LearningHub)                                   │
│     └── POST /lia/learning/context → company_learned_skills                 │
│                                                                              │
│  2. Busca catálogo estático por (role, seniority)                           │
│     └── SkillsCatalogService.get_skills_for_role()                          │
│                                                                              │
│  3. Mescla e deduplica                                                      │
│     └── POST /api/v1/lia/learning/skills-deduplicated                       │
│                                                                              │
│  4. Aplica histórico de confirmações do recrutador                          │
│     └── Ajusta ordem baseado em acceptance_rate                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Tokens LLM Consumidos:** 0 (catálogo local)

### 8.4 Etapa 4: Remuneração (`salary`)

**O que o Recrutador Faz:**
- Confirma/ajusta faixa salarial
- Visualiza comparativo interno vs. mercado
- Define bônus e critérios
- Ativa/desativa benefícios

**O que a LIA Faz:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SUGESTÃO DE SALÁRIO                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Busca benchmark interno (vagas similares na empresa)                    │
│     └── GET /job-wizard/salary-benchmark?source=internal                    │
│                                                                              │
│  2. Busca benchmark de mercado (Glassdoor, LinkedIn)                        │
│     └── GET /job-wizard/salary-benchmark?source=market                      │
│                                                                              │
│  3. Aplica ajuste personalizado (RecruiterPersonalizationService)           │
│     └── Se recrutador costuma aumentar 15%, sugere 15% maior                │
│                                                                              │
│  4. Mostra comparativo visual                                               │
│     └── "📊 R$ 18k-22k (interno) | R$ 20k-25k (mercado)"                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Tokens LLM Consumidos:** 0 (APIs externas)

### 8.5 Etapa 5: Triagem WSI (`wsi-questions`)

**O que o Recrutador Faz:**
- Visualiza perguntas geradas automaticamente
- Edita/remove perguntas
- Adiciona perguntas customizadas
- Define ordem de envio (batches)

**O que a LIA Faz (LLM: Claude Sonnet):**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GERAÇÃO DE PERGUNTAS WSI                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Coleta contexto completo da vaga                                        │
│     └── {title, seniority, skills, competencies, responsibilities}          │
│                                                                              │
│  2. Gera perguntas via Claude Sonnet                                        │
│     └── Prompt estruturado com metodologia WSI (Bloom + Dreyfus)            │
│                                                                              │
│  3. Categoriza por tipo                                                     │
│     └── technical, behavioral, situacional, fit                             │
│                                                                              │
│  4. Define batches de envio                                                 │
│     └── Batch 1: Elegibilidade | Batch 2: Técnico | Batch 3: Fit            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Tokens LLM Consumidos:** ~2.000 (Claude)

### 8.6 Etapa 6: Revisão e Publicação (`review-publish`)

**O que o Recrutador Faz:**
- Revisa resumo completo da vaga
- Gera Job Description estruturada
- Seleciona plataformas de publicação
- Publica vaga

**O que a LIA Faz (LLM: Claude Sonnet):**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GERAÇÃO DE JOB DESCRIPTION                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Verifica completude (CompletenessService)                               │
│     └── Campos obrigatórios preenchidos?                                    │
│     └── Skills mínimas definidas?                                           │
│     └── Faixa salarial dentro de limites?                                   │
│                                                                              │
│  2. Gera JD estruturada (JDGeneratorService)                                │
│     └── Seções: About, Responsibilities, Requirements, Benefits             │
│     └── Otimizada para SEO de job boards                                    │
│                                                                              │
│  3. Publica nas plataformas selecionadas                                    │
│     └── LinkedIn Jobs, Site Carreiras, ATS integrado                        │
│                                                                              │
│  4. Cria JobVacancy a partir do JobDraft                                    │
│     └── Status: PUBLISHED                                                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Tokens LLM Consumidos:** ~3.000 (Claude - geração de JD)

### 8.7 Etapa 7: Busca e Calibração (`search-calibration`)

**O que o Recrutador Faz:**
- Visualiza candidatos sugeridos (1-5)
- Aprova/rejeita candidatos para calibração
- Ajusta critérios de busca
- Inicia sourcing proativo

**O que a LIA Faz:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  BUSCA E CALIBRAÇÃO                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Busca inicial (Sourcing Agent)                                          │
│     └── Base local: SQL com filtros                                         │
│     └── Pearch AI: API externa para busca global                            │
│                                                                              │
│  2. Scoring de candidatos                                                   │
│     └── Skills match: 50 pts                                                │
│     └── Seniority match: 10 pts                                             │
│     └── Experience years: 20 pts                                            │
│     └── Title similarity: 15 pts                                            │
│     └── Location: 5 pts                                                     │
│                                                                              │
│  3. Calibração com feedback                                                 │
│     └── Recrutador aprova/rejeita candidatos                                │
│     └── Feedback registrado para refinar busca                              │
│                                                                              │
│  4. Busca refinada                                                          │
│     └── Ajusta pesos baseado em feedback                                    │
│     └── Expande/restringe critérios                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Tokens LLM Consumidos:** ~1.500 (Gemini - expansão semântica)

---

## 9. Catálogo de Skills e Competências

### 9.1 Skills Técnicas por Área

| Área | Skills Técnicas | Skills Comportamentais |
|------|-----------------|------------------------|
| **Engineering** | Python, Java, Node.js, React, TypeScript, SQL, Docker, AWS, Kubernetes | Resolução de Problemas, Pensamento Analítico, Colaboração |
| **Finance** | Excel Avançado, Power BI, SAP, IFRS, Modelagem Financeira | Atenção a Detalhes, Gestão de Risco, Comunicação |
| **HR** | R&S, ATS, LinkedIn Recruiter, Entrevistas por Competências | Empatia, Escuta Ativa, Negociação |
| **Marketing** | SEO, SEM, Google Ads, Analytics, Copywriting | Criatividade, Orientação a Dados, Adaptabilidade |
| **Sales** | Vendas Consultivas, CRM, Salesforce, HubSpot, Negociação B2B | Persuasão, Resiliência, Foco em Resultados |
| **Operations** | Lean, Six Sigma, Project Management, Supply Chain | Organização, Gestão de Tempo, Liderança |
| **Product** | Product Discovery, Agile, User Research, Roadmapping | Visão Estratégica, Comunicação, Priorização |
| **Design** | Figma, Adobe XD, UX Research, Design Systems | Criatividade, Empatia com Usuário, Colaboração |

### 9.2 Catálogos Dinâmicos

Os catálogos são enriquecidos dinamicamente com skills aprendidas:

```python
# SkillsCatalogService - com learning
async def suggest_skills_with_learning(
    db: AsyncSession,
    company_id: str,
    role: str,
    seniority: str,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Retorna:
    - technical_skills: Lista mesclada (dinâmicas + estáticas)
    - company_learned_skills: Skills promovidas da empresa
    - source_mix: {"dynamic": 3, "static": 7}
    """

# ResponsibilitiesCatalogService - com learning
async def suggest_responsibilities_with_learning(
    db: AsyncSession,
    company_id: str,
    role: str,
    seniority: str,
    limit: int = 5
) -> Dict[str, Any]:
    """
    Retorna responsabilidades mescladas priorizando aprendidas
    """
```

### 9.3 Endpoint de Skills Deduplicadas

```
POST /api/v1/lia/learning/skills-deduplicated
Body: {
    "company_id": "uuid",
    "role": "Backend Developer",
    "seniority": "senior",
    "already_selected_skills": ["Python", "Django"]
}
Response: {
    "skills": ["FastAPI", "PostgreSQL", "Redis"],  // sem duplicatas
    "source": "learning_hub"
}
```

---

## 10. Sistemas Transversais

### 10.1 Sistema de Feature Flags

Feature Flags permitem rollout gradual de funcionalidades por empresa ou usuário.

**Flags Disponíveis:**

| Flag | Descrição | Default |
|------|-----------|---------|
| `lia_wizard_v2` | Novo wizard com tipologia | true |
| `learning_hub_enabled` | Aprendizado de skills | true |
| `proactive_salary_analysis` | Análise proativa de salário | true |
| `pearch_integration` | Busca global via Pearch AI | true |
| `jd_generation_v2` | Nova geração de JD | true |
| `skip_confident_stages` | Pular etapas com alta confiança | true |
| `teams_whatsapp_connector` | Conector Teams → WhatsApp | true |
| `recruiter_personalization` | Personalização por recrutador | true |

**Implementação:**

```python
class FeatureFlagService:
    async def is_enabled(
        self,
        flag_name: str,
        company_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Verifica se feature está habilitada para empresa/usuário.
        """
```

### 10.2 Field Toggles

Field Toggles controlam quais dados a LIA pode consumir por empresa.

**Campos Configuráveis:**

| Campo | Descrição | Default |
|-------|-----------|---------|
| `use_company_values` | Usar valores da empresa | true |
| `use_tech_stack` | Usar stack tecnológico | true |
| `use_salary_history` | Usar histórico salarial | true |
| `use_benefits_data` | Usar dados de benefícios | true |
| `use_department_info` | Usar informações de departamentos | true |
| `use_manager_data` | Usar dados de gestores | true |
| `use_evp_data` | Usar EVP da empresa | true |
| `use_big_five_profile` | Usar perfil Big Five | false |
| `use_correction_history` | Usar histórico de correções | true |

**Endpoint de Configuração:**

```
GET /api/v1/company/{company_id}/field-toggles
PUT /api/v1/company/{company_id}/field-toggles
```

### 10.3 Empty Field Notifications

Sistema de notificações no chat quando campos configurados estão vazios.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  EMPTY FIELD NOTIFICATION                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Quando um campo configurado como toggle está vazio:                        │
│                                                                              │
│  1. LIA verifica toggle (is_lia_enabled = true)                             │
│  2. LIA verifica se campo está preenchido                                   │
│  3. Se vazio → notifica no chat:                                            │
│                                                                              │
│     "⚠️ O campo 'Tech Stack' está configurado para uso pela LIA,            │
│      mas não foi preenchido. Isso pode afetar a qualidade das sugestões.    │
│      [Preencher agora] [Ignorar]"                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Endpoint:**

```
GET /api/v1/company/{company_id}/empty-fields
POST /api/v1/company/{company_id}/empty-fields/{field_key}/action
POST /api/v1/company/{company_id}/empty-fields/{field_key}/suggest
```

---

## 11. Análise de Uso de LLMs

### 11.1 Consumo de Tokens por Etapa

| Etapa | LLM | Tokens | Custo Estimado |
|-------|-----|--------|----------------|
| 1. Input Evaluation | Gemini Flash | ~1.500 | $0.0002 |
| 2. Job Description | - | 0 | $0 |
| 3. Competencies | - | 0 | $0 |
| 4. Salary | - | 0 | $0 |
| 5. WSI Questions | Claude Sonnet | ~2.000 | $0.006 |
| 6. Review/Publish | Claude Sonnet | ~3.000 | $0.009 |
| 7. Search/Calibration | Gemini Flash | ~1.500 | $0.0002 |
| **Total por Vaga** | | **~8.000** | **~$0.016** |

### 11.2 Estratégias de Otimização

#### Cache de JD Templates

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CACHE DE JD TEMPLATES                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PROBLEMA:                                                                   │
│  - Cada parsing de JD consome ~1.500 tokens                                 │
│  - Vagas similares reprocessam prompts idênticos                            │
│                                                                              │
│  SOLUÇÃO:                                                                    │
│  - Cache de templates de JD por (role, seniority, department)               │
│  - TTL: 7 dias ou até atualização de configuração                           │
│  - Hash key: SHA256(role + seniority + company_id)                          │
│                                                                              │
│  ECONOMIA ESTIMADA: 30-40% dos tokens de parsing                            │
│                                                                              │
│  IMPLEMENTAÇÃO:                                                              │
│  class JDTemplateCache:                                                      │
│      async def get_or_create_template(                                      │
│          self, role: str, seniority: str, company_id: str                   │
│      ) -> JDTemplate:                                                        │
│          cache_key = self._generate_key(role, seniority, company_id)        │
│          cached = await self.redis.get(cache_key)                           │
│          if cached:                                                          │
│              return JDTemplate.parse_raw(cached)                            │
│          template = await self._generate_template(role, seniority)          │
│          await self.redis.setex(cache_key, 604800, template.json())         │
│          return template                                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Status:** ✅ Implementado (Janeiro 2026)

**Endpoints:**
- `DELETE /api/v1/cache/jd/{company_id}` - Invalida cache da empresa
- `GET /api/v1/cache/jd/metrics` - Métricas de performance
- `POST /api/v1/cache/jd/reset-metrics` - Reseta contadores

#### Cache de Embeddings

| Componente | Tokens Salvos | TTL |
|------------|---------------|-----|
| Skills embeddings | ~200/skill | 30 dias |
| JD section embeddings | ~500/seção | 7 dias |
| Candidate CV embeddings | ~1000/CV | 90 dias |

#### Batch Processing

```python
# Atual: 1 chamada por candidato
for candidate in candidates:
    score = await llm.evaluate(candidate, job)  # 500 tokens × N

# Otimizado: batch de 5-10 candidatos
batches = chunk(candidates, size=5)
for batch in batches:
    scores = await llm.evaluate_batch(batch, job)  # 2000 tokens (vs 2500)
```

**Economia estimada:** 15-20% em avaliações em lote

### 11.3 Fallback Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ESTRATÉGIA DE FALLBACK                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PRIORIDADE 1: Cache local                                                  │
│  ├── Verificar se resultado existe em cache                                 │
│  └── Se hit → retorna imediatamente (0 tokens)                              │
│                                                                              │
│  PRIORIDADE 2: Regras estáticas                                             │
│  ├── Taxonomias locais (skills, títulos, indústrias)                        │
│  ├── Boolean query builder                                                   │
│  └── Se match suficiente → usar sem LLM (0 tokens)                          │
│                                                                              │
│  PRIORIDADE 3: LLM leve (Gemini Flash)                                      │
│  ├── Para expansão semântica                                                │
│  ├── Custo: ~0.0001$/1K tokens                                              │
│  └── Latência: <300ms                                                       │
│                                                                              │
│  PRIORIDADE 4: LLM completo (Claude Sonnet)                                 │
│  ├── Para análise profunda (rubricas, WSI)                                  │
│  ├── Custo: ~0.003$/1K tokens                                               │
│  └── Latência: 2-5 segundos                                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.4 Análise Comparativa: Claude Sonnet vs Gemini Flash

> **Atualizado:** Janeiro 2026

#### Por que Arquitetura Híbrida?

A plataforma utiliza uma **arquitetura híbrida de LLMs** onde cada modelo é usado para tarefas onde se destaca:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ARQUITETURA HÍBRIDA DE LLMs                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      GEMINI 2.5 FLASH                                │    │
│  │  Uso: Extração, Classificação, Busca Semântica                      │    │
│  │  ✅ Extração de entidades do JD (título, skills, seniority)         │    │
│  │  ✅ Expansão semântica para buscas de candidatos                    │    │
│  │  ✅ Classificação rápida de inputs                                  │    │
│  │  Velocidade: ~100-300ms | Custo: $0.30/1M input, $0.60/1M output    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      CLAUDE SONNET 4.5                               │    │
│  │  Uso: Geração de Texto, Análise Complexa, Pareceres                 │    │
│  │  ✅ Gerar perguntas WSI contextualizadas                            │    │
│  │  ✅ Criar Job Description profissional (v2)                         │    │
│  │  ✅ Pareceres de avaliação e análises complexas                     │    │
│  │  Velocidade: 2-5s | Custo: $3.00/1M input, $15.00/1M output         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Comparativo de Preços (Estimativa - Janeiro 2026)

> **Fonte:** Preços públicos das APIs (platform.claude.com, ai.google.dev). Valores podem variar com descontos de volume, batch API ou context caching.

| Modelo | Input/1M tokens | Output/1M tokens | Fator de Custo |
|--------|-----------------|------------------|----------------|
| **Claude Sonnet 4.5** | ~$3.00 | ~$15.00 | Base |
| **Gemini 2.5 Flash** | ~$0.30 | ~$0.60 | **~10-25x mais barato** |
| **Gemini 2.5 Flash (thinking)** | ~$0.30 | ~$2.50 | ~6x mais barato |

#### Custo por Vaga (Cenário Atual vs 100% Gemini)

> **Nota:** Estimativas baseadas na tabela de consumo de tokens da seção 11.1 (~8.000 tokens/vaga). Valores reais podem variar conforme complexidade da vaga e uso de cache.

| Cenário | Custo/vaga | Economia vs Atual |
|---------|------------|-------------------|
| **Atual (Híbrido)** | ~$0.016 | - (conforme seção 11.1) |
| **100% Gemini** | ~$0.002 | **~8x mais barato** |
| **Gemini + Thinking** | ~$0.006 | ~3x mais barato |

#### Trade-offs de Qualidade

> **Avaliação qualitativa** baseada em experiência de uso e benchmarks públicos. Resultados podem variar conforme o caso de uso.

| Aspecto | Claude Sonnet | Gemini Flash |
|---------|---------------|--------------|
| Geração de texto longo | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Raciocínio complexo | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Consistência de formato | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Seguir instruções | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Velocidade | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Custo | ⭐⭐ | ⭐⭐⭐⭐⭐ |

#### Riscos de Migração Total para Gemini

| Tarefa | Risco | Impacto |
|--------|-------|---------|
| **Geração de JD (Etapa 6)** | Alto | JDs menos refinadas e profissionais |
| **Perguntas WSI (Etapa 5)** | Médio | Perguntas menos contextualizadas |
| **Pareceres de Avaliação** | Alto | Análises podem perder nuance |
| **Extração de Entidades (Etapa 1)** | Baixo | Já usa Gemini - sem mudança |

#### Plano de Otimização Recomendado

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PLANO DE MIGRAÇÃO GRADUAL                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  FASE 1: A/B Test (Baixo Risco)                                             │
│  ├── Manter Claude para JD v2 final                                         │
│  ├── Testar Gemini Flash para JD v1 preview                                 │
│  └── Economia esperada: 20-30%                                              │
│                                                                              │
│  FASE 2: Gemini com Thinking Mode (Médio Risco)                             │
│  ├── Etapa 5 (WSI Questions): Gemini 2.5 Flash + thinking                   │
│  ├── Custo: $2.50/1M vs $15/1M do Claude                                    │
│  └── Economia esperada: 50-60%                                              │
│                                                                              │
│  FASE 3: Avaliação de Qualidade                                             │
│  ├── Métricas: taxa de edição de JD pelos recrutadores                      │
│  ├── Feedback qualitativo de usuários                                       │
│  └── Decisão: manter híbrido ou migrar mais tarefas                         │
│                                                                              │
│  ECONOMIA TOTAL POTENCIAL: 50-70% do custo atual                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Configuração Atual no LLMService

**Arquivo:** `lia-agent-system/app/services/llm.py`

| Provider | Modelo | Configuração |
|----------|--------|--------------|
| **Claude** | `claude-sonnet-4-5` | Via Replit AI Integration (`AI_INTEGRATIONS_ANTHROPIC_API_KEY`) |
| **Gemini** | `gemini-2.5-flash` | Via Replit AI Integration (`AI_INTEGRATIONS_GEMINI_API_KEY`) |
| **OpenAI** | `gpt-4o` | Configurado mas não utilizado no wizard |

A escolha do modelo é feita por serviço/agente, não por roteamento central. Cada serviço importa o LLMService e usa `llm.claude`, `llm.openai` ou `llm.generate_with_gemini()`.

#### Conclusão

A arquitetura híbrida atual **equilibra custo e qualidade**:
- **Gemini** para tarefas de extração e busca = custo mínimo, velocidade máxima
- **Claude** para geração de texto e análise complexa = qualidade máxima

Para reduzir custos sem sacrificar qualidade crítica, a recomendação é:
1. Implementar métricas de telemetria para medir uso real de tokens
2. Testar Gemini + thinking mode em tarefas hoje feitas com Claude
3. Avaliar qualidade via feedback dos recrutadores antes de migrar

> **Próximo passo sugerido:** Implementar dashboard de custos LLM com métricas reais antes de decidir migração.

---

## 12. Intelligence Layer

### 12.1 Visão Geral

O Intelligence Layer é uma camada centralizada de inteligência que fornece insights contextuais durante todo o wizard.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    INTELLIGENCE LAYER                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │ Pattern         │  │ Outcome         │  │ Contextual      │             │
│  │ Detection       │  │ Correlation     │  │ Suggestions     │             │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘             │
│           │                    │                    │                       │
│           └────────────────────┼────────────────────┘                       │
│                                │                                            │
│                                ▼                                            │
│                    ┌─────────────────────┐                                  │
│                    │ IntelligenceLayer   │                                  │
│                    │ Service             │                                  │
│                    └─────────────────────┘                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 12.2 Pattern Detection

Detecta padrões no histórico de vagas da empresa:

```python
class PatternDetectorService:
    async def detect_patterns(
        self,
        company_id: str,
        context: Dict[str, Any]
    ) -> List[DetectedPattern]:
        """
        Padrões detectados:
        - "77% das vagas de Dev são híbridas"
        - "Salário médio para Senior: R$ 18k-22k"
        - "Vagas de Engenharia demoram 25 dias para fechar"
        """
```

### 12.3 Outcome Correlation

Correlaciona características de vagas com outcomes de sucesso:

```python
class OutcomeCorrelationService:
    async def get_success_factors(
        self,
        company_id: str,
        role: str,
        seniority: str
    ) -> SuccessFactors:
        """
        Retorna:
        - Skills que correlacionam com contratações bem-sucedidas
        - Faixas salariais que atraem melhores candidatos
        - Tempo médio de fechamento
        """
```

### 12.4 Sugestões Contextuais

Fornece sugestões em tempo real baseadas no contexto:

```python
class ContextualSuggestionService:
    async def get_suggestions(
        self,
        draft: JobDraft,
        current_step: int
    ) -> List[Suggestion]:
        """
        Sugestões por etapa:
        - Etapa 1: "Vagas similares usaram X skills"
        - Etapa 4: "Salário está 10% abaixo do mercado"
        - Etapa 7: "3 candidatos no banco local atendem critérios"
        """
```

### 12.5 Endpoints de Inteligência

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/v1/intelligence/data-quality` | POST | Análise de qualidade de dados |
| `/api/v1/intelligence/context` | POST | Contexto enriquecido |
| `/api/v1/intelligence/patterns` | POST | Padrões detectados |
| `/api/v1/intelligence/suggestions` | POST | Sugestões contextuais |

---

## 13. Personalização por Recrutador

### 13.1 Visão Geral

O sistema aprende com cada recrutador individualmente:
- Suas preferências de vagas
- Padrões de correção
- Velocidade de interação
- Tipos de vagas mais comuns
- Estilo de interação

### 13.2 Modelo RecruiterProfile

**Arquivo**: `lia-agent-system/app/models/recruiter_profile.py`

```python
class RecruiterProfile(Base):
    """
    Perfil de personalização para cada recrutador.
    """
    __tablename__ = "recruiter_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    recruiter_id = Column(String(255), nullable=False, unique=True, index=True)
    company_id = Column(String(255), nullable=False, index=True)
    
    # Estatísticas de uso
    total_jobs_created = Column(Integer, default=0)
    total_corrections_made = Column(Integer, default=0)
    avg_completion_time_seconds = Column(Float, nullable=True)
    
    # Preferências detectadas
    preferred_seniorities = Column(JSON, default=list)
    preferred_departments = Column(JSON, default=list)
    correction_patterns = Column(JSON, default=dict)
    
    # Ajustes personalizados
    confidence_threshold_adjustment = Column(Float, default=0.0)
    wizard_mode = Column(String(50), nullable=True)  # "quick", "detailed", "standard"
    experience_level = Column(String(50), nullable=True)  # "beginner", "intermediate", "expert"
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity_at = Column(DateTime, nullable=True)
```

### 13.3 RecruiterPersonalizationService

```python
class RecruiterPersonalizationService:
    """
    Serviço de personalização baseado em perfil do recrutador.
    """
    
    async def get_personalized_thresholds(
        self,
        recruiter_id: str,
        company_id: str
    ) -> PersonalizedThresholds:
        """
        Retorna thresholds personalizados para este recrutador.
        """
    
    async def get_personalized_defaults(
        self,
        recruiter_id: str,
        company_id: str,
        job_context: Dict[str, Any]
    ) -> PersonalizedDefaults:
        """
        Retorna defaults personalizados para este recrutador.
        """
    
    async def record_event(
        self,
        db: AsyncSession,
        recruiter_id: str,
        company_id: str,
        event_type: str,
        field_name: Optional[str] = None,
        ...
    ) -> Dict[str, Any]:
        """
        Registra evento de personalização para aprendizado.
        
        Event types:
        - field_suggested: A field suggestion was shown
        - field_accepted: Suggestion was accepted without change
        - field_corrected: Suggestion was corrected
        - step_skipped: Optional step was skipped
        - explanation_dismissed: Explanation was closed quickly
        - jd_imported: JD import feature was used
        """
```

### 13.4 Casos de Uso de Personalização

#### Recrutador de Tech (Maria)

**Perfil detectado:**
- Cria principalmente vagas de Dev Sênior
- Sempre aumenta salário sugerido em ~15%
- Pula explicações detalhadas
- Usa JD import frequentemente

**Comportamento personalizado:**
```
Maria: "Dev Python Sênior"

LIA (personalizada):
"Dev Python Sênior para Engenharia. 
Salário: R$ 20.000 - R$ 26.000 (ajustado ao seu padrão).
Skills: Python, FastAPI, AWS.

[Próximo →]"

(Sem explicações longas, fluxo direto, salário já ajustado)
```

#### Recrutador Novo (João)

**Perfil detectado:**
- Apenas 3 vagas criadas
- Dados insuficientes para personalização

**Comportamento:**
```
João: "Dev Python Sênior"

LIA (padrão):
"Entendi que você precisa de um Desenvolvedor Python Sênior!

Vou preencher automaticamente baseado nos dados da empresa:
• Salário: R$ 18.000 - R$ 22.000 (benchmark interno)
• Skills sugeridas: Python, SQL, REST APIs

Quer me contar mais sobre a vaga ou posso continuar com essas configurações?"

(Modo explicativo completo para novo usuário)
```

#### Recrutador Executivo (Carla)

**Perfil detectado:**
- Cria vagas de gestão/diretoria
- Linguagem formal
- Detalhista, não pula etapas
- Faz muitas correções em competências

**Comportamento personalizado:**
```
Carla: "Diretor de Tecnologia"

LIA (personalizada):
"Prezada Carla,

Para a posição de Diretor de Tecnologia, preparei as seguintes sugestões:

**Remuneração Executiva:**
- Faixa salarial: R$ 45.000 - R$ 65.000
- Bônus anual: 3-6 salários

**Competências de Liderança:**
Gostaria de sua validação para estas competências, pois observei que você costuma ajustá-las:
- Visão Estratégica (Essencial)
- Gestão de P&L (Essencial)
- Liderança de Equipes (Essencial)

Poderia confirmar ou ajustar conforme necessário?"

(Tom formal, pedindo confirmação onde costuma corrigir)
```

### 13.5 Privacidade e Transparência

```python
class PersonalizationSettings(Base):
    """Configurações de privacidade controladas pelo usuário"""
    
    # Opt-in/out
    enable_personalization = Column(Boolean, default=True)
    use_correction_history = Column(Boolean, default=True)
    use_preference_detection = Column(Boolean, default=True)
    use_outcome_data = Column(Boolean, default=True)
    
    # Transparência
    show_confidence_indicators = Column(Boolean, default=True)
    explain_suggestions = Column(Boolean, default=True)
```

**Indicadores de Transparência:**
```
LIA: "Salário: R$ 22.000 - R$ 28.000 
     📊 Ajustado ao seu padrão (+15% vs. benchmark)"
     
LIA: "[Próximo →]
     ⚡ Modo rápido ativado (baseado no seu histórico)"
```

### 13.6 API Endpoints de Personalização

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/v1/recruiter-profiles/me` | GET | Retorna perfil do recrutador atual |
| `/api/v1/recruiter-profiles/me/settings` | GET | Retorna configurações de personalização |
| `/api/v1/recruiter-profiles/me/field-preferences` | GET | Retorna preferências por campo |
| `/api/v1/recruiter-profiles/me/thresholds` | GET | Retorna thresholds personalizados |
| `/api/v1/recruiter-profiles/me/events` | POST | Registra evento de personalização |
| `/api/v1/recruiter-profiles/me/recalculate` | POST | Força recálculo do perfil |

---

## 14. Loop de Aprendizagem da IA

### 14.1 Ciclo de Aprendizado

```
┌────────────────────────────────────────────────────────────┐
│                   CICLO DE APRENDIZADO                      │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐ │
│  │Interação│───▶│ Registro│───▶│ Análise │───▶│Atualiza │ │
│  │ Wizard  │    │  Evento │    │ Padrão  │    │ Perfil  │ │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘ │
│       │                                             │       │
│       └─────────────────────────────────────────────┘       │
│                    (próxima interação)                      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 EVENTOS REGISTRADOS                  │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ • field_suggested: campo X sugerido com valor Y     │   │
│  │ • field_accepted: sugestão aceita sem alteração     │   │
│  │ • field_corrected: valor alterado de Y para Z       │   │
│  │ • step_skipped: recrutador pulou etapa opcional     │   │
│  │ • explanation_dismissed: fechou explicação rápido   │   │
│  │ • jd_imported: usou importação de JD                │   │
│  │ • time_spent: tempo em cada etapa                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

### 14.2 WizardFeedback Model

```python
class WizardFeedback(Base):
    """
    Registro de feedback para aprendizado do wizard.
    """
    __tablename__ = "wizard_feedbacks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    user_id = Column(String(255), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), nullable=True)
    company_id = Column(String(255), nullable=False, index=True)
    
    feedback_type = Column(String(50))  # "correction", "acceptance", "skip"
    field_name = Column(String(100), nullable=True)
    
    original_value = Column(JSON)
    final_value = Column(JSON)
    
    context = Column(JSON)  # job context quando feedback foi dado
    
    response_time_ms = Column(Integer, nullable=True)
    confidence_at_suggestion = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 14.3 JobOutcome Model

```python
class JobOutcome(Base):
    """
    Registro de outcomes de vagas para correlação.
    """
    __tablename__ = "job_outcomes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    company_id = Column(String(255), nullable=False, index=True)
    
    outcome_type = Column(String(50))  # "filled", "cancelled", "expired"
    
    time_to_fill_days = Column(Integer, nullable=True)
    candidates_received = Column(Integer, nullable=True)
    candidates_qualified = Column(Integer, nullable=True)
    interviews_conducted = Column(Integer, nullable=True)
    
    hire_quality_score = Column(Float, nullable=True)  # 1-5
    recruiter_satisfaction = Column(Float, nullable=True)  # 1-5
    
    job_snapshot = Column(JSON)  # snapshot do job no momento do outcome
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 15. Pós-Wizard: Adição de Candidatos

### 15.1 Formas de Adicionar Candidatos

Após publicação da vaga, candidatos podem ser adicionados via:

| Forma | Origem | Automação |
|-------|--------|-----------|
| **Busca Ativa** | Sourcing Agent + Pearch AI | Automática |
| **Candidatura Espontânea** | Portal de carreiras | Manual/Automática |
| **Indicação** | Funcionários | Manual |
| **Import CSV** | Base externa | Manual |
| **Integração ATS** | Gupy, Pandapé | Automática |

### 15.2 Pipeline do Kanban

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PIPELINE PADRÃO DO KANBAN                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │
│  │ Triagem │→│Entrevista│→│ Teste   │→│Entrevista│→│ Proposta │           │
│  │ (LIA)   │  │   RH    │  │ Técnico │  │ Gestor  │  │         │           │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘           │
│      │                                                     │                │
│      ▼                                                     ▼                │
│  ┌─────────┐                                        ┌─────────┐            │
│  │Reprovado│                                        │Contratado│            │
│  └─────────┘                                        └─────────┘            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 15.3 Fluxo de Busca Ativa

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FLUXO BUSCA ATIVA (Stage 7.3)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1️⃣ LIA INICIA BUSCA                                                        │
│  ├── Busca no banco local do recrutador                                     │
│  ├── Se insuficiente + Pearch ativo → busca global                          │
│  └── Calcula match score para cada candidato                                │
│                                                                              │
│  2️⃣ ADIÇÃO AO PIPELINE                                                      │
│  ├── Método: `_add_candidates_to_job()` ou `_add_pearch_candidates_to_job()`│
│  ├── Cria registro Interview com:                                           │
│  │   ├── status: "pending"                                                  │
│  │   ├── application_stage: "triagem"                                       │
│  │   ├── interview_type: "triagem"                                          │
│  │   └── created_by: "sourcing_pipeline" ou "sourcing_pipeline_pearch"      │
│  ├── Score: ✅ Pearch e Local salvam lia_score corretamente                 │
│  └── Detalhes: ver seção "ONDE O SCORE É ARMAZENADO" abaixo                 │
│                                                                              │
│  3️⃣ ORDENAÇÃO (apenas em AgentResponse, não persiste no DB)                 │
│  ├── candidatos.sort(key=lambda x: x.get("overall_score", 0), reverse=True) │
│  ├── Aplicado apenas ao retornar resposta para o frontend                   │
│  └── Ordem no banco/kanban: conforme inserção (não por score)               │
│                                                                              │
│  4️⃣ ONDE O SCORE É ARMAZENADO                                               │
│  ├── Candidate.lia_score: Float (modelo candidate.py linha 206/353)         │
│  ├── ✅ Pearch: lia_score=data.get("match_score") na criação                │
│  ├── ✅ Local: lia_score via _calculate_local_match_score() (0-100)         │
│  │   └── Skills(50pts) + Seniority(10pts) + Experience(20pts) +             │
│  │       Title(15pts) + Location(5pts)                                      │
│  ├── Sorting: AgentResponse ordena por overall_score (não persiste no DB)   │
│  └── UI: implementação de exibição depende do frontend (não verificado)     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 16. Metodologias de Busca de Candidatos

### 16.1 Scoring (Boolean Query + CandidateMatcher)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    METODOLOGIA DE SCORING                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PESOS POR CRITÉRIO:                                                        │
│  ├── Skills match: 50 pontos                                                │
│  ├── Experience years: 20 pontos                                            │
│  ├── Title similarity: 15 pontos                                            │
│  ├── Seniority match: 10 pontos                                             │
│  └── Location: 5 pontos                                                     │
│                                                                              │
│  CÁLCULO:                                                                   │
│  score = Σ (peso × match_ratio)                                             │
│  match_ratio = matched_items / total_required                               │
│                                                                              │
│  EXEMPLO:                                                                   │
│  Vaga: Python Senior, São Paulo, 5 skills                                   │
│  Candidato: 4/5 skills, Senior, SP                                          │
│  Score: (50×0.8) + (20×1.0) + (15×0.9) + (10×1.0) + (5×1.0) = 88.5         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 16.2 Rubricas (BARS - Behaviorally Anchored Rating Scales)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    METODOLOGIA WSI + BARS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  NÍVEIS (Taxonomia de Bloom + Dreyfus):                                     │
│                                                                              │
│  5 - Expert/Creator                                                         │
│      "Cria frameworks, lidera inovação, referência na área"                 │
│                                                                              │
│  4 - Proficient/Analyzer                                                    │
│      "Analisa problemas complexos, toma decisões autônomas"                 │
│                                                                              │
│  3 - Competent/Applier                                                      │
│      "Aplica conhecimento em situações novas"                               │
│                                                                              │
│  2 - Advanced Beginner/Understander                                         │
│      "Entende conceitos, precisa de supervisão"                             │
│                                                                              │
│  1 - Novice/Rememberer                                                      │
│      "Lembra informações básicas, executa tarefas simples"                  │
│                                                                              │
│  CÁLCULO:                                                                   │
│  wsi_score = Σ (nivel × peso_competencia) / Σ pesos                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 16.3 Comparação entre Metodologias

| Aspecto | Scoring | Rubricas |
|---------|---------|----------|
| **Velocidade** | Rápido (~100ms) | Lento (~5s com LLM) |
| **Precisão** | Média | Alta |
| **Custo** | Zero tokens | ~500 tokens/candidato |
| **Quando usar** | Triagem inicial, alto volume | Avaliação final, poucos candidatos |
| **Viés** | Baseado em keywords | Baseado em comportamentos |

---

## 17. Notificações Multi-Canal

### 17.1 Canais Disponíveis

- `bell` - Notificação in-app (sino)
- `email` - E-mail automático
- `teams` - Microsoft Teams (webhook)
- `sms` - SMS (via Twilio)

### 17.2 Formato de Notificação de Triagem

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  📬 TEAMS / BELL NOTIFICATION (v2.0 - Janeiro 2026)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Título: "Triagem concluída: {candidate_name}"                              │
│                                                                              │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━              │
│  📋 Vaga: {job_title} (ID: {vacancy_id})                                    │
│  👤 Candidato: {candidate_name} (ID: {candidate_id})                        │
│  👔 Gestor: {hiring_manager_name}                                           │
│  🏢 Departamento: {department}                                              │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━              │
│  📊 Score WSI: {wsi_score}/5 | {tier_emoji} Tier: {tier}                    │
│  ✅ Confiança: {confidence}%                                                │
│  💡 Recomendação: {tier_recommendation}                                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━              │
│                                                                              │
│  Tier Classification:                                                        │
│  ⭐ A (4.0-5.0): Aprovar, Agendar Entrevista, Ver Detalhes                  │
│  🟢 B (3.0-3.9): Ver Detalhes, Aprovar, Solicitar Entrevista                │
│  🟡 C (2.0-2.9): Ver Detalhes, Solicitar Avaliação Adicional                │
│  🔴 D (0.0-1.9): Ver Detalhes, Arquivar                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 17.3 Conector Teams → WhatsApp

**Status:** ✅ IMPLEMENTADO (Janeiro 2026)

O conector Teams→WhatsApp foi implementado com webhook seguro:

| Componente | Status | Código Fonte |
|------------|--------|--------------|
| Notificação Teams (saída) | ✅ Implementado | `teams_service.py:send_message()` |
| Adaptive Cards | ✅ Implementado | `teams_service.py:send_adaptive_card()` |
| Webhook Teams (entrada) | ✅ Implementado | `api/v1/teams.py:webhook_handler()` |
| WhatsApp Screening | ✅ Implementado | `whatsapp_service.py` |
| Trigger Teams→WhatsApp | ✅ Implementado | `teams.py` → `whatsapp_service.start_screening()` |
| Segurança HMAC-SHA256 | ✅ Implementado | Validação obrigatória em produção |
| Audit Logs | ✅ Implementado | `TeamsActionAuditLog` modelo PostgreSQL |

**Endpoints:**
- `POST /api/v1/teams/webhook` - Receber ações de Adaptive Cards
- `GET /api/v1/teams/webhook/audit-logs` - Logs de auditoria

---

## 18. Sistema de Geração de Job Description

### 18.1 Versões do Gerador

| Versão | Características | Status |
|--------|-----------------|--------|
| **v1** | Template estático + variáveis | ✅ Implementado |
| **v2** | LLM (Claude) + otimização SEO | ✅ Implementado |

### 18.2 Estrutura da JD Gerada

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    JOB DESCRIPTION ESTRUTURADA                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. SOBRE A EMPRESA                                                         │
│     └── EVP, cultura, valores (extraídos de CompanyData)                    │
│                                                                              │
│  2. SOBRE A VAGA                                                            │
│     └── Descrição geral, contexto do time, impacto esperado                 │
│                                                                              │
│  3. RESPONSABILIDADES                                                       │
│     └── Lista de atividades principais (deduplicadas)                       │
│                                                                              │
│  4. REQUISITOS TÉCNICOS                                                     │
│     └── Skills obrigatórias e desejáveis                                    │
│                                                                              │
│  5. COMPETÊNCIAS COMPORTAMENTAIS                                            │
│     └── Soft skills essenciais                                              │
│                                                                              │
│  6. O QUE OFERECEMOS                                                        │
│     └── Benefícios, modelo de trabalho, salário (opcional)                  │
│                                                                              │
│  7. PROCESSO SELETIVO                                                       │
│     └── Etapas do pipeline                                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 18.3 Endpoint de Geração

```
POST /api/v1/lia/jd-generator/generate
Body: {
    "job_draft_id": "uuid",
    "version": "v2",
    "include_salary": true,
    "optimize_for": ["linkedin", "indeed"]
}
Response: {
    "generated_jd": "...",
    "word_count": 450,
    "seo_score": 85,
    "tokens_used": 2800
}
```

---

## 19. Sistema de Interação com Sugestões via Chat

### 19.1 Fluxo de Interação

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    INTERAÇÃO COM SUGESTÕES VIA CHAT                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. LIA sugere valor                                                        │
│     └── "Sugiro salário de R$ 18k-22k baseado no mercado"                   │
│                                                                              │
│  2. Recrutador responde no chat                                             │
│     └── "Aumenta para 25k o teto"                                           │
│                                                                              │
│  3. LIA interpreta e aplica                                                 │
│     └── Detecta intenção: ajustar salary_max                                │
│     └── Aplica: salary_max = 25000                                          │
│     └── Confirma: "Pronto! Ajustei o teto para R$ 25.000"                   │
│                                                                              │
│  4. Feedback registrado                                                     │
│     └── WizardFeedback: field_corrected, salary_max, 22000→25000            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 19.2 Comandos Suportados

| Comando | Ação | Exemplo |
|---------|------|---------|
| Ajustar valor | Modifica campo específico | "Coloca 5 anos de experiência" |
| Adicionar skill | Adiciona à lista | "Adiciona Docker às skills" |
| Remover skill | Remove da lista | "Remove PHP" |
| Trocar | Substitui valor | "Troca híbrido por remoto" |
| Confirmar | Aceita sugestão | "Pode manter" |
| Explicar | Pede justificativa | "Por que esse salário?" |

---

## 20. Mapeamento de Configurações da Empresa

### 20.1 Estrutura do Menu Configurações

```
🏢 Empresa & Equipe
├── Dados da Empresa ──────── "company-data"
│   ├── Informações Básicas
│   ├── Cultura e Identidade  
│   ├── Tech Stack
│   ├── Big Five da Empresa
│   └── Idiomas Padrão
├── Informações Estratégicas ── "strategic-info"
├── Departamentos ──────────── "departments"
├── Benefícios ─────────────── "benefits"
└── Usuários ───────────────── "users"

⚙️ Recrutamento
├── Pipeline ───────────────── "pipeline"
├── Perguntas Screening ────── "screening"
├── Status de Candidatos ───── "candidate-statuses"
└── Solicitação de Dados ───── "data-requests"

📊 Planejamento
└── Planejamento de Contratações ─ Workforce Planning
```

### 20.2 CompanyData Interface Completa

```typescript
interface CompanyData {
  // === DADOS BÁSICOS ===
  name: string                    // Razão Social
  tradeName: string               // Nome Fantasia
  cnpj: string                    // CNPJ
  website: string                 // Site Institucional
  email: string                   // Email Principal
  phone: string                   // Telefone Principal
  address: string                 // Endereço Completo
  logo?: string                   // URL do Logo
  industry: string                // Setor/Indústria
  size: string                    // Porte (1-10, 11-50, etc.)
  employee_count?: number         // Número de funcionários
  locations?: string[]            // Filiais/Escritórios
  linkedin_url?: string           // LinkedIn da empresa

  // === CULTURA E IDENTIDADE ===
  mission?: string                // Missão
  vision?: string                 // Visão
  values?: string[]               // Lista de Valores
  coreCompetencies?: string[]     // Competências-chave
  work_model?: string             // Modelo: Híbrido/Remoto/Presencial
  evp_bullets?: string[]          // Employee Value Proposition
  dei_initiatives?: string        // Diversidade e Inclusão

  // === TECNOLOGIA ===
  tech_stack?: string[]           // Stack de tecnologia categorizado
  engineering_culture?: string    // Cultura de engenharia
  default_languages?: string[]    // Idiomas padrão da empresa

  // === BIG FIVE DA EMPRESA ===
  openness_score?: number         // Abertura (0-100)
  conscientiousness_score?: number // Conscienciosidade (0-100)
  extraversion_score?: number     // Extroversão (0-100)
  agreeableness_score?: number    // Amabilidade (0-100)
  stability_score?: number        // Estabilidade Emocional (0-100)

  // === DADOS ESTRATÉGICOS ===
  additional_data?: {
    hiring_volume?: number        // Volume mensal de contratações
    job_types?: string[]          // Tipos de vagas (CLT, PJ, etc.)
    current_ats?: string          // ATS atual
    main_challenges?: string[]    // Principais desafios de recrutamento
    main_priority?: string        // Prioridade principal
  }
}
```

### 20.3 Tech Stack Categorizado

| Categoria | Ícone | Sugestões Padrão |
|-----------|-------|------------------|
| **Backend** | Server | Node.js, Python, Java, .NET, Go, Ruby, PHP, Rust |
| **Frontend** | Layout | React, Vue.js, Angular, Next.js, Svelte, TypeScript |
| **Dados** | Database | PostgreSQL, MongoDB, MySQL, Redis, Elasticsearch |
| **Cloud** | Cloud | AWS, Azure, GCP, Vercel, Heroku, DigitalOcean |
| **DevOps** | Settings | Docker, Kubernetes, Jenkins, GitHub Actions, Terraform |
| **IA/ML** | Brain | TensorFlow, PyTorch, OpenAI, Anthropic, LangChain |
| **ERPs** | Briefcase | SAP, Oracle, Totvs, Salesforce, Dynamics 365 |
| **Design** | Palette | Figma, Adobe XD, Sketch, InVision, Framer |
| **Mobile** | Smartphone | React Native, Flutter, Swift, Kotlin, iOS, Android |

### 20.4 Mapeamento Wizard ↔ Configurações

| Etapa do Wizard | Campos Pré-preenchidos | Fonte |
|-----------------|----------------------|-------|
| **Etapa 1 - Detecção** | Modelo de trabalho, localização | `CompanyData.work_model`, `locations` |
| **Etapa 2 - Básicas** | Departamento, Gestor, Localização | `departments[]`, `managers[]`, `headquarters` |
| **Etapa 3 - Técnicos** | Sugestões de stack, Idiomas | `tech_stack[]`, `default_languages[]` |
| **Etapa 4 - Comportamentais** | Valores, Competências, Big Five | `values[]`, `coreCompetencies[]`, `*_score` |
| **Etapa 5 - Benefícios** | Benefícios ativos | `BenefitsTab` com filtro por senioridade |
| **Etapa 6 - Triagem** | Perguntas padrão | `screening_questions[]` |
| **Etapa 7 - Entrevistas** | Pipeline completo | `recruitment_stages[]` |
| **Etapas 8-10 - Sourcing** | Skills promovidas, Cutoffs calibrados | `LearningHub.get_learning_context()` |

---

## 21. Sistema de Análise Proativa da LIA

### 21.1 Visão Geral

O Wizard utiliza uma **camada de inteligência proativa** que analisa informações em tempo real:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FLUXO DE ANÁLISE PROATIVA DA LIA                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐     ┌──────────────────────────────────────────────┐  │
│  │ Descrição do     │     │              SERVIÇOS DE ANÁLISE             │  │
│  │ Recrutador       │────▶│                                              │  │
│  │                  │     │  ┌────────────────────────────────────────┐  │  │
│  │ "Preciso de um   │     │  │ IntelligenceLayerService               │  │  │
│  │  Dev Python      │     │  │ - Detecção de padrões                  │  │  │
│  │  Sênior para     │     │  │ - Correlação de outcomes               │  │  │
│  │  Dados em SP"    │     │  │ - Sugestões contextuais                │  │  │
│  └──────────────────┘     │  └────────────────────────────────────────┘  │  │
│                           │                    │                          │  │
│                           │                    ▼                          │  │
│                           │  ┌────────────────────────────────────────┐  │  │
│                           │  │ SkillsCatalogService                   │  │  │
│                           │  │ - Catálogo de skills por área          │  │  │
│                           │  │ - Mapeamento cargo → competências      │  │  │
│                           │  │ - Ajuste por senioridade               │  │  │
│                           │  └────────────────────────────────────────┘  │  │
│                           │                    │                          │  │
│                           │                    ▼                          │  │
│                           │  ┌────────────────────────────────────────┐  │  │
│                           │  │ CompensationAnalysisService            │  │  │
│                           │  │ - Política salarial da empresa         │  │  │
│                           │  │ - Benchmark de mercado                 │  │  │
│                           │  │ - Total Compensation                   │  │  │
│                           │  └────────────────────────────────────────┘  │  │
│                           │                    │                          │  │
│                           │                    ▼                          │  │
│                           │  ┌────────────────────────────────────────┐  │  │
│                           │  │ MarketBenchmarkService                 │  │  │
│                           │  │ - Pesquisa web de salários             │  │  │
│                           │  │ - Tendências de mercado                │  │  │
│                           │  │ - Skills em demanda                    │  │  │
│                           │  └────────────────────────────────────────┘  │  │
│                           └──────────────────────────────────────────────┘  │
│                                               │                              │
│                                               ▼                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    PARECER DA LIA (EvaluationResponse)               │   │
│  │  • detected_fields: {title, seniority, department, skills...}        │   │
│  │  • completeness_score: 85%                                           │   │
│  │  • compensation_analysis: {salary, bonus, benefits, total_comp}      │   │
│  │  • suggestions: [{field, suggested, reason, source}...]              │   │
│  │  • recommended_action: "proceed" | "review_compensation" | "missing" │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 21.2 Tipos de Análise Proativa

| Análise | Trigger | Output |
|---------|---------|--------|
| **Salário vs. Mercado** | Etapa 4 | "Faixa 15% abaixo do mercado" |
| **Skills em Alta** | Etapa 3 | "AI/ML está em alta demanda" |
| **TTF Estimado** | Etapa 6 | "Previsão: 28 dias para fechar" |
| **Candidatos Disponíveis** | Etapa 7 | "12 candidatos no banco local" |
| **Competitividade** | Etapa 4 | "Benefícios acima da média" |

---

## 22. Diagnóstico e Recomendações

### 22.1 Status Geral: 99% Completo

| Área | Status | Observação |
|------|--------|------------|
| Learning Hub Infrastructure | ✅ Completo | Modelos, serviço, endpoints |
| Integração com Agentes | ✅ Completo | Sourcing, WSI Evaluator |
| Wizard 7 Etapas | ✅ Completo | Consolidado de 10 para 7 |
| Field Toggles System | ✅ Completo | Controle de consumo de dados |
| Empty Field Notifications | ✅ Completo | Notificações no chat |
| Outcome Learning | ✅ Completo | job-outcome, outcome-insights |
| Stage Feedback | ✅ Completo | stage-feedback, analytics |
| Feature Flags | ✅ Completo | 8 flags com rollout gradual |
| Skills Deduplication | ✅ Completo | Remove redundância |
| Analytics Dashboard (API) | ✅ Completo | learning-dashboard, health score |
| Analytics Dashboard (UI) | 🟡 Pendente | Baixa prioridade |
| JD Template Cache | ✅ Completo | Redis + métricas (Jan/2026) |
| Refatoração UX Etapas 1-3 | ✅ Completo | skip_if_confident + learning (Jan/2026) |
| Teams → WhatsApp Connector | ✅ Completo | Webhook + 20 testes (Jan/2026) |
| Detecção de Idiomas | ✅ Completo | PT-BR, EN-US, ES (Jan/2026) |

### 22.2 Pontos Fortes

1. **Learning Hub robusto** - 5 fases cobrindo todo o ciclo
2. **Integração completa com agentes** - Sourcing e WSI Evaluator funcionais
3. **Personalização por empresa** - Field Toggles e Feature Flags
4. **Transparência** - Origens de campos auto-preenchidos expostas
5. **Feedback loop** - Sistema aprende com correções do recrutador
6. **Otimização de tokens** - JDTemplateCache reduz chamadas LLM redundantes
7. **UX inteligente** - Wizard pula etapas quando LIA tem confiança alta
8. **Multilíngue** - Suporte automático a PT-BR, EN-US e ES

### 22.3 Redundâncias UX Etapas 1-3: Análise

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    REDUNDÂNCIAS DETECTADAS (RESOLVIDAS)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. DETECÇÃO DE SKILLS DUPLICADA                                            │
│     ├── Etapa 1: JD parsing extrai skills do texto                          │
│     ├── Etapa 2: Learning Hub sugere skills da empresa                      │
│     └── Resultado: mesmas skills podem aparecer 2x                          │
│     └── ✅ RESOLVIDO: get_skills_without_duplicates() implementado          │
│                                                                              │
│  2. SENIORITY PERGUNTADO MÚLTIPLAS VEZES                                    │
│     ├── Etapa 1: Detectado do JD                                            │
│     ├── Etapa 2: Confirmado/ajustado                                        │
│     └── Resultado: pergunta redundante se já detectado                      │
│     └── ✅ RESOLVIDO: skip_if_confident=true implementado                   │
│                                                                              │
│  3. DEPARTAMENTO/ÁREA                                                        │
│     ├── Etapa 1: Pode ser inferido do título                                │
│     ├── Etapa 2: Perguntado novamente                                       │
│     └── Resultado: UX repetitiva                                            │
│     └── ✅ RESOLVIDO: threshold 85% pula confirmação                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 22.4 Próximos Passos Sugeridos

| Prioridade | Item | Esforço | Status |
|------------|------|---------|--------|
| Alta | Dashboard Analytics (Frontend) | Médio | 🟡 Pendente |
| Média | Divisão do arquivo monolítico em componentes | Médio | 🟡 Pendente |
| Baixa | Testes E2E completos | Baixo | 🟡 Pendente |
| Baixa | Outcome Learning com ML | Alto | 🟡 Pendente |

---

## 23. API Endpoints Implementados

### 23.1 Tabela Consolidada de Endpoints

| Categoria | Endpoint | Método | Descrição |
|-----------|----------|--------|-----------|
| **Wizard** | `/api/v1/lia/job-wizard/evaluate` | POST | Avalia input inicial |
| **Wizard** | `/api/v1/lia/job-wizard/stage/{n}` | POST | Processa etapa N |
| **Wizard** | `/job-wizard/salary-benchmark` | GET | Benchmark de salário |
| **Draft** | `/api/v1/job-drafts` | POST | Cria draft |
| **Draft** | `/api/v1/job-drafts/{id}` | GET/PUT/DELETE | CRUD de draft |
| **Draft** | `/api/v1/job-drafts/{id}/publish` | POST | Publica draft |
| **Learning** | `/lia/learning/confirm-skill` | POST | Confirma skill |
| **Learning** | `/lia/learning/confirm-responsibility` | POST | Confirma responsabilidade |
| **Learning** | `/lia/learning/context` | POST | Obtém contexto de learning |
| **Learning** | `/api/v1/lia/learning/stage-feedback` | POST | Registra feedback por stage |
| **Learning** | `/api/v1/lia/learning/job-outcome` | POST | Registra outcome |
| **Learning** | `/api/v1/lia/learning/outcome-insights` | POST | Obtém insights |
| **Learning** | `/api/v1/lia/learning/dashboard` | POST | Dashboard de analytics |
| **Learning** | `/api/v1/lia/learning/skills-deduplicated` | POST | Skills deduplicadas |
| **Intelligence** | `/api/v1/intelligence/data-quality` | POST | Análise de qualidade |
| **Intelligence** | `/api/v1/intelligence/context` | POST | Contexto enriquecido |
| **Intelligence** | `/api/v1/intelligence/patterns` | POST | Padrões detectados |
| **Intelligence** | `/api/v1/intelligence/suggestions` | POST | Sugestões contextuais |
| **Personalization** | `/api/v1/recruiter-profiles/me` | GET | Perfil do recrutador |
| **Personalization** | `/api/v1/recruiter-profiles/me/settings` | GET | Configurações |
| **Personalization** | `/api/v1/recruiter-profiles/me/thresholds` | GET | Thresholds personalizados |
| **Personalization** | `/api/v1/recruiter-profiles/me/events` | POST | Registra evento |
| **Personalization** | `/api/v1/recruiter-profiles/me/recalculate` | POST | Recalcula perfil |
| **Field Toggles** | `/api/v1/company/{id}/field-toggles` | GET/PUT | Toggles de campos |
| **Field Toggles** | `/api/v1/company/{id}/empty-fields` | GET | Campos vazios |
| **Field Toggles** | `/api/v1/company/{id}/empty-fields/{key}/action` | POST | Ação em campo vazio |
| **Field Toggles** | `/api/v1/company/{id}/empty-fields/{key}/suggest` | POST | Sugestão para campo |
| **Cache** | `/api/v1/cache/jd/{company_id}` | DELETE | Invalida cache JD |
| **Cache** | `/api/v1/cache/jd/metrics` | GET | Métricas de cache |
| **Cache** | `/api/v1/cache/jd/reset-metrics` | POST | Reseta métricas |
| **JD Generator** | `/api/v1/lia/jd-generator/generate` | POST | Gera JD |
| **Teams** | `/api/v1/teams/webhook` | POST | Webhook Teams |
| **Teams** | `/api/v1/teams/webhook/audit-logs` | GET | Logs de auditoria |

---

## 24. Histórico de Mudanças

### Versão 5.0 - Janeiro 2026 (Consolidação Definitiva)
- ✅ **Consolidação documental**: Unificação de todos os documentos em referência única
- ✅ **Estrutura didática**: Reorganização para facilitar leitura e compreensão
- ✅ **Atualização de status**: Todos os componentes marcados com status atual

### Versão 4.1 - Janeiro 2026 (Learning Hub)
- ✅ **Seção 25.9**: Sistema de Aprendizado Unificado (Learning Hub)
- ✅ **Catálogos Dinâmicos**: `suggest_skills_with_learning()` e `suggest_responsibilities_with_learning()`
- ✅ **Endpoints de Learning**: `/lia/learning/confirm-skill`, `/confirm-responsibility`, `/context`
- ✅ **Stages 8-10**: Integração com Sourcing Agent e WSI Evaluator
- ✅ **Testes de Integração**: 13 testes validando o learning loop completo

### Versão 4.0 - Janeiro 2026 (Consolidação)
- ✅ **Consolidação documental**: Unificação de 4 documentos em um único arquivo abrangente
- ✅ **Seção 24**: Estrutura Completa do Wizard (3 Fases, 7 Etapas)
- ✅ **Seção 25**: Mapeamento de Configurações da Empresa
- ✅ **Seção 26**: Sistema de Análise Proativa da LIA
- ✅ **Seção 27**: Próximos Passos (Clustering e Embeddings)

### Versão 3.0 - Janeiro 2026 (Flow Update)
- ✅ **JD Template Cache**: Implementação completa com Redis
- ✅ **Refatoração UX**: skip_if_confident + learning
- ✅ **Teams → WhatsApp**: Conector com 20 testes
- ✅ **Detecção de Idiomas**: PT-BR, EN-US, ES

### Versão 2.0 - Dezembro 2025
- ✅ **Intelligence Layer**: Pattern Detection, Outcome Correlation
- ✅ **Personalização**: RecruiterProfile, RecruiterPersonalizationService
- ✅ **Feedback Learning**: WizardFeedback, JobOutcome

### Versão 1.0 - Novembro 2025
- ✅ **Wizard inicial**: 10 etapas
- ✅ **Tipologia de Campos**: IMPLICIT, PROBABLE, CONDITIONAL, CRITICAL
- ✅ **JobDraft**: Estado intermediário

---

## 25. Próximos Passos: Clustering e Embeddings

### 25.1 Proposta de Clustering de Vagas

**Objetivo:** Agrupar vagas similares para melhorar sugestões e reduzir tokens.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CLUSTERING DE VAGAS                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. EMBEDDINGS DE VAGAS                                                     │
│     └── Gerar embedding vetorial para cada vaga                             │
│     └── Dimensões: título, skills, responsabilidades, departamento          │
│                                                                              │
│  2. CLUSTERING K-MEANS                                                      │
│     └── Agrupar vagas similares em clusters                                 │
│     └── Identificar "arquétipos" de vagas                                   │
│                                                                              │
│  3. TEMPLATE POR CLUSTER                                                    │
│     └── Gerar template de JD por cluster                                    │
│     └── Pré-popular skills, responsabilidades, salário                      │
│                                                                              │
│  4. ECONOMIA DE TOKENS                                                      │
│     └── Reutilizar templates em vez de gerar do zero                        │
│     └── Estimativa: 40-60% redução em geração de JD                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 25.2 Implementação Proposta

```python
class JobClusteringService:
    """
    Serviço de clustering de vagas para templates.
    """
    
    async def generate_job_embedding(
        self,
        job: JobVacancy
    ) -> List[float]:
        """
        Gera embedding vetorial da vaga.
        """
    
    async def find_similar_cluster(
        self,
        embedding: List[float],
        company_id: str
    ) -> Optional[JobCluster]:
        """
        Encontra cluster mais similar.
        """
    
    async def get_cluster_template(
        self,
        cluster_id: str
    ) -> ClusterTemplate:
        """
        Retorna template do cluster.
        """
```

### 25.3 Arquitetura Proposta

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ARQUITETURA DE EMBEDDINGS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │ Job Created │───▶│ Embedding   │───▶│ Vector DB   │───▶│ Clustering  │  │
│  │             │    │ Generator   │    │ (Pinecone)  │    │ Service     │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│                           │                                      │          │
│                           └──────────────────────────────────────┘          │
│                                          │                                   │
│                                          ▼                                   │
│                               ┌─────────────────────┐                        │
│                               │ Template Generator  │                        │
│                               │ (cached by cluster) │                        │
│                               └─────────────────────┘                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 25.4 Benefícios Esperados

| Benefício | Impacto |
|-----------|---------|
| Redução de tokens | 40-60% menos chamadas LLM |
| Qualidade de JD | Templates refinados por cluster |
| Velocidade | Resposta instantânea para vagas similares |
| Consistência | Padrões por tipo de vaga |

---

## Arquivos de Referência

| Arquivo | Localização |
|---------|-------------|
| **Modelos** | |
| CompanyLearning | `lia-agent-system/app/models/company_learning.py` |
| JobDraft | `lia-agent-system/app/models/job_draft.py` |
| FeedbackLearning | `lia-agent-system/app/models/feedback_learning.py` |
| RecruiterProfile | `lia-agent-system/app/models/recruiter_profile.py` |
| **Services** | |
| LearningHubService | `lia-agent-system/app/services/learning_hub_service.py` |
| SkillsCatalogService | `lia-agent-system/app/services/skills_catalog_service.py` |
| ConfidencePolicyService | `lia-agent-system/app/services/confidence_policy_service.py` |
| IntelligenceLayerService | `lia-agent-system/app/services/intelligence_layer_service.py` |
| RecruiterPersonalizationService | `lia-agent-system/app/services/recruiter_personalization_service.py` |
| JDTemplateCache | `lia-agent-system/app/services/jd_template_cache_service.py` |
| **Agentes** | |
| JobIntakeAgent | `lia-agent-system/app/agents/specialized/job_intake_agent.py` |
| **Schemas** | |
| FieldTypology | `lia-agent-system/app/schemas/field_typology.py` |
| **API** | |
| LearningEndpoints | `lia-agent-system/app/api/v1/lia_learning.py` |
| IntelligenceEndpoints | `lia-agent-system/app/api/v1/intelligence.py` |
| RecruiterProfilesEndpoints | `lia-agent-system/app/api/v1/recruiter_profiles.py` |
| **Frontend** | |
| JobCreationWizard | `plataforma-lia/src/components/job-creation/job-creation-wizard.tsx` |
| useJobDraft | `plataforma-lia/src/hooks/use-job-draft.ts` |
| FieldConfidenceIndicator | `plataforma-lia/src/components/job-creation/field-confidence-indicator.tsx` |

---

> **Documento gerado em:** Janeiro 2026  
> **Versão:** 5.0  
> **Mantido por:** Equipe de Produto LIA
