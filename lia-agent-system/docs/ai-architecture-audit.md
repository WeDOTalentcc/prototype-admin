# Auditoria de Arquitetura de IA — Plataforma LIA
## WeDoTalent Learning Intelligence Assistant

**Versão:** 7.0  
**Data:** 23 de Fevereiro de 2026  
**Classificação:** Documento Técnico — Confidencial  
**Preparado para:** Revisão por Especialista Externo em Arquitetura de IA

---

## Índice

1. [Resumo Executivo](#1-resumo-executivo)
2. [Fluxos do Produto e Onde a IA Atua](#2-fluxos-do-produto-e-onde-a-ia-atua)
   - 2.0 [Contexto Visual: Telas do Produto e Pontos de IA](#20-contexto-visual-telas-do-produto-e-pontos-de-atuação-da-ia)
   - 2.1 [Wizard de Criação de Vaga](#21-fluxo-wizard-de-criação-de-vaga)
   - 2.2 [Jornada Completa do Candidato](#22-fluxo-jornada-completa-do-candidato-aplicação--contratação)
   - 2.3 [Comunicação WhatsApp com Candidatos](#23-fluxo-comunicação-whatsapp-com-candidatos)
   - 2.4 [Comunicação Teams com Recrutadores](#24-fluxo-comunicação-teams-com-recrutadores)
   - 2.5 [Comunicação Email](#25-fluxo-comunicação-email)
   - 2.6 [Triagem e Scoring WSI Detalhado](#26-fluxo-triagem-e-scoring-wsi-detalhado)
   - 2.7 [Criação de Perguntas de Triagem via Edição de Vaga](#27-fluxo-criação-de-perguntas-de-triagem-via-edição-de-vaga)
   - 2.8 [Inscrição de Candidato via WhatsApp](#28-fluxo-inscrição-de-candidato-via-whatsapp)
   - 2.9 [Pedido de Ajuda do Recrutador Quando IA Falha](#29-fluxo-pedido-de-ajuda-do-recrutador-quando-ia-falha)
   - 2.10 [Comportamento Completo da IA na Triagem](#210-comportamento-completo-da-ia-na-triagem-screening)
3. [Visão Geral da Arquitetura](#3-visão-geral-da-arquitetura)
   - 3.5 [Tech Stack — Diagrama em Camadas](#35-tech-stack--diagrama-em-camadas)
   - 3.6 [Arquitetura LangGraph — Graphs, Nodes e Edges](#36-arquitetura-langgraph--graphs-nodes-e-edges)
   - 3.7 [Processamento Assíncrono — RabbitMQ + Celery](#37-processamento-assíncrono--rabbitmq--celery)
   - 3.8 [Redis — Cache Inteligente de 3 Camadas](#38-redis--cache-inteligente-de-3-camadas)
   - 3.9 [Busca Semântica — Elasticsearch + PG Vector + WRF](#39-busca-semântica--elasticsearch--pg-vector--wrf)
   - 3.10 [Prompts, RAG e Base de Conhecimento](#310-prompts-rag-e-base-de-conhecimento)
   - 3.11 [Fluxo de Dados das IAs — Learning Loop e Feedback](#311-fluxo-de-dados-das-ias--learning-loop-e-feedback)
   - 3.12 [Custos e Consumo de IA — Billing e Token Tracking](#312-custos-e-consumo-de-ia--billing-e-token-tracking)
   - 3.13 [Segurança e Isolamento Multi-Tenant](#313-segurança-e-isolamento-multi-tenant)
   - 3.14 [Personalização por Recrutador — Aprendizagem Adaptativa](#314-personalização-por-recrutador--aprendizagem-adaptativa-individual)
   - 3.15 [ML Preditivo — Outcome Prediction e Feature Engineering](#315-machine-learning-preditivo--outcome-prediction-e-feature-engineering)
   - 3.16 [Clusterização e Padrões Históricos — JobPattern + Learning Hub](#316-clusterização-e-padrões-históricos--jobpattern--learning-hub)
   - 3.17 [Predictive Analytics — 7 Tipos de Predição](#317-predictive-analytics--7-tipos-de-predição)
   - 3.18 [Automação Inteligente — Engine, Triggers, Scheduler e Alertas](#318-automação-inteligente--engine-triggers-scheduler-e-alertas-proativos)
   - 3.19 [Inteligência Contextual — Extração, RAG, WRF e Inferência](#319-inteligência-contextual--extração-rag-wrf-dinâmico-e-inferência)
   - 3.20 [Análise Multimodal e Voz](#320-análise-multimodal-e-voz)
   - 3.21 [Robustez e Qualidade — Enhanced Base Agent](#321-robustez-e-qualidade--enhanced-base-agent--validação--normalização)
   - 3.22 [Automação Progressiva — CompanyHiringPolicy e Níveis de Autonomia](#322-automação-progressiva--companyhiringpolicy-e-níveis-de-autonomia)
   - 3.23 [Arquitetura ReAct Agent System](#323-arquitetura-react-agent-system)
   - 3.24 [Long-Term Memory System](#324-long-term-memory-system)
   - 3.25 [Agent Explainability System](#325-agent-explainability-system)
   - 3.26 [Multi-Channel Communication](#326-multi-channel-communication)
   - 3.27 [Async Task Processing at Scale](#327-async-task-processing-at-scale)
4. [Camada de Orquestração](#4-camada-de-orquestração)
5. [Mapa Completo de Domínios](#5-mapa-completo-de-domínios)
6. [Catálogo de Ações (Actions)](#6-catálogo-de-ações-actions)
7. [Catálogo de Ferramentas (Tools)](#7-catálogo-de-ferramentas-tools)
8. [Catálogo de Serviços (Services)](#8-catálogo-de-serviços-services)
9. [Metodologia WSI](#9-metodologia-wsi)
10. [Sistema de Prompts](#10-sistema-de-prompts)
11. [Compliance, Governança e Mitigação de Bias](#11-compliance-governança-e-mitigação-de-bias)
12. [Integrações Externas](#12-integrações-externas)
13. [Data Architecture](#13-data-architecture-arquitetura-de-dados)
14. [AI vs Non-AI Boundaries](#14-ai-vs-non-ai-boundaries-fronteiras-ia-vs-determinístico)
15. [Performance & Scalability](#15-performance--scalability)
16. [Reliability & Observability](#16-reliability--observability)
17. [Security & Authentication](#17-security--authentication--implementação-detalhada)
18. [Tópicos Avançados de Governança de IA](#18-tópicos-avançados-de-governança-de-ia)
19. [Technical Debt & Risks](#19-technical-debt--risks-dívida-técnica-e-riscos)
20. [Recommendations](#20-recommendations-recomendações)
21. [Pontos de Atenção para o Auditor](#21-pontos-de-atenção-para-o-auditor)

**Apêndices:**
- [Apêndice A: Contagens Detalhadas](#apêndice-a-contagens-detalhadas)
- [Apêndice B: Glossário](#apêndice-b-glossário)
- [Apêndice C: Procedimento de Verificação de Contagens](#apêndice-c-procedimento-de-verificação-de-contagens)

---

## 1. Resumo Executivo

A Plataforma LIA (Learning Intelligence Assistant) é um sistema de recrutamento e seleção potencializado por IA, desenvolvido pela WeDoTalent. Utiliza uma arquitetura multi-agente orientada a domínios (Domain-Driven Agent Architecture v2.2) com **arquitetura ReAct (Reasoning + Acting)** como padrão principal de agentes, para automatizar e aprimorar todo o ciclo de aquisição de talentos — do sourcing à contratação.

### Números-chave da Plataforma

| Métrica | Valor |
|---|---|
| Domínios de IA | 11 |
| Agentes | 7 ReAct + 1 LangGraph + 18 Legacy = **26 agentes** |
| Actions (ações executáveis) | 205 (verificado por grep + contagem manual) |
| Tools (ferramentas de agente) | **89 ReAct** (Wizard:9, Kanban:14, Talent:12, JobsMgmt:13, Policy:13, Sourcing:14, Pipeline:14) + tools legacy |
| Services (serviços de negócio) | **137** (verificado por MAPA doc) |
| Serviços de ML/Predição | 7 (OutcomePredictor, FeatureEngineering, ModelRegistry, OutcomeCorrelator, PatternDetector, PredictiveAnalytics, JobPattern) |
| Serviços de Automação | 6 (StageAutomationEngine, AutomationScheduler, AutomationTrigger, ProactiveAlert, AutonomousAgent, ExecutionPlan) |
| Serviços de Inteligência | 8 (SmartExtractor, RAG, WRFDynamicK, MarketBenchmark, ManagerInference, InferBehavior, InterpretContextLLM, SuggestionInteraction) |
| Compliance Guardrails | 5 (FairnessGuard 3-tier, FactChecker, AuditService, AffirmativeAction, PolicyEngine) + Anti-sycophancy guardrails em todos os agentes ReAct |
| FairnessGuard | 3 camadas: regex normalizado + detecção implícita + análise semântica LLM |
| Anti-sycophancy | Guardrails integrados nos 4 agentes principais (Wizard, Kanban, Talent, JobsMgmt) |
| Few-shot Examples | Integrados em todos os system prompts ReAct |
| Company Context Calibration | STARTUP / PME / CORPORAÇÃO em todos os agentes |
| Long-Term Memory | LongTermMemoryService + MemoryIntegration (cross-session) |
| Agent Explainability | ExecutionLogStore + API + Frontend panel |
| Multi-Channel Communication | ChannelAdapter + ChannelRouter + MultiChannelService (5 adapters: email, WhatsApp, SMS, Teams, in-app) |
| Async Task Processing | TaskRecord + TaskScheduler + EnhancedTaskManager + Dead Letter Queue (DLQ) |
| Production Readiness | Health endpoint unificado, RequestIdMiddleware, Rate Limiter (200/min, 2000/hr) |
| Modelos LLM utilizados | Claude (Anthropic), GPT-4 (OpenAI), Gemini (Google) |
| Framework de orquestração | Cascaded Router (Memory → Regex → LLM) |
| Arquitetura de Agentes | ReAct (4-file pattern: agent.py, tool_registry.py, system_prompt.py, stage_context.py) |
| Metodologia de avaliação | WSI (WeDoTalent Skill Index) — 7 blocos |
| Compliance | LGPD, SOX, EU AI Act |
| Análise Multimodal | Claude Vision (imagem), Gemini (vídeo), PDF extraction |
| Processamento de Voz | Deepgram Nova-2 (STT) + OpenAI TTS |
| Personalização | Adaptativa por recrutador (10+ vagas threshold) |
| Triggers de Automação | 16 tipos + 18 alertas proativos |
| Backend | Python (FastAPI/Uvicorn) |
| Frontend | Next.js + React + TypeScript |

### Objetivo desta Auditoria

Este documento mapeia **completamente** a arquitetura de IA da plataforma para que um especialista externo possa avaliar:

1. Se a arquitetura de agentes e domínios é adequada para os objetivos de recrutamento inteligente
2. Se cada agente tem papel claro, escopo definido e capacidades adequadas
3. Se os fluxos end-to-end (triagem → seleção → contratação) estão cobertos
4. Se compliance, governança e mitigação de bias estão adequadamente implementados
5. Se os grafos de decisão e prompts estão bem estruturados
6. Se a arquitetura de dados, performance, segurança e observabilidade atendem aos requisitos de produção
7. Se os riscos técnicos e dívidas foram adequadamente identificados e priorizados
8. Se o comportamento da IA na triagem está adequado (LGPD, limites, feedback, relatórios)
9. Se as telas do produto refletem corretamente os pontos de atuação da IA (7 telas mapeadas)

---

## 2. Fluxos do Produto e Onde a IA Atua

> **Abordagem didática:** Esta seção apresenta **o que o produto faz** antes de explicar **como ele é construído**. Cada fluxo mostra a jornada do usuário (recrutador ou candidato) e identifica precisamente em que ponto a IA intervém, qual domínio é acionado, quais serviços processam a lógica e quais ferramentas são executadas. Isso permite ao auditor compreender o impacto da IA no produto antes de mergulhar nos detalhes técnicos das seções seguintes.
>
> Para cada fluxo, apresentamos:
> 1. Um **diagrama visual** (ASCII art) mostrando a sequência de etapas
> 2. Uma **tabela de mapeamento** com domínio, serviços, ferramentas, agentes e prompts envolvidos em cada etapa

---

### 2.0 Contexto Visual: Telas do Produto e Pontos de Atuação da IA

Antes de detalhar cada fluxo, é essencial visualizar **onde a IA opera dentro das telas reais do produto**. Os diagramas abaixo representam as 7 telas principais da plataforma, destacando com `[AI]` os pontos onde há processamento por IA/LLM. Isso permite ao auditor compreender o impacto visual e funcional da IA no produto.

**Padrão de Layout (regra geral em todas as telas):**
- **LIA (chat/sidebar)** = sempre à **ESQUERDA** (renderizado primeiro no `flex` container)
- **Conteúdo principal** (tabela/kanban) = ao **CENTRO** (flex-1)
- **Preview de candidato** = sempre à **DIREITA** (400-600px, resizable)
- Código fonte confirma: `flex gap-2` ou `flex gap-4` com LIA como primeiro filho

**Legenda:**
- `[AI]` = Ponto onde IA/LLM é invocada
- `[WSI]` = Scoring WSI (7 blocos)
- `[LIA]` = Assistente conversacional LIA
- `[DET]` = Lógica determinística (sem IA)

---

#### Tela 1: Gestão de Vagas — Tabela (`jobs-page.tsx`)

Layout split: mini prompt LIA no toolbar (max 300px, esquerda). Quando colapsado, apenas toolbar + tabela. O painel LIA expande à **esquerda** da tabela (Tela 2).

**Nota de posicionamento:** O código usa `flex gap-2` com o painel LIA renderizado **antes** da tabela no DOM (linha 3624-3626 de `jobs-page.tsx`), ou seja, a LIA fica sempre à **esquerda** e a tabela à **direita**.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  HEADER: 🧳 Gestão de Vagas                                    [+ Nova Vaga]  │
│  TABS: [Visão Geral | ●Todas(123) | Ativas(89) | Minhas(34) | Arquivadas(12)]  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  TOOLBAR: [Prompt LIA _____(max 300px)] [🔍] [🎤]   [Filtros] [Colunas(6)]    │
│            ↳ ao focar, expande para Tela 2             [Sel. Todos]            │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ TABELA DE VAGAS (ocupa 100% quando LIA colapsado)                      │    │
│  │                                                                         │    │
│  │  ☐ │ ID  │ Vaga           │ Pipeline LIA  │ Status │ Recrutador │ ⋮   │    │
│  │  ──┼─────┼────────────────┼───────────────┼────────┼────────────┼─────│    │
│  │  ☐ │ 001 │ Dev Senior     │ ██▶██▶██▶░░   │ Ativa  │ Ana        │ ⋮   │    │
│  │  ☐ │ 002 │ UX Designer    │ ██▶█░▶░░▶░░   │ Ativa  │ Pedro      │ ⋮   │    │
│  │  ☐ │ 003 │ PM Lead        │ █░▶░░▶░░▶░░   │ Pausa  │ Maria      │ ⋮   │    │
│  │  ☐ │ 004 │ Data Engineer  │ ███▶██▶░░▶░░  │ Ativa  │ Carlos     │ ⋮   │    │
│  │                                                                         │    │
│  │  Pipeline LIA = [Inscritos▶Triagem▶Entrevista▶Proposta] com barras [AI] │    │
│  │  [AI] Insights por vaga (score, alerta via tooltip hover)               │    │
│  │  [AI] Sugestões proativas badge no header (💡 N sugestões da LIA)       │    │
│  │                                                                         │    │
│  │  AÇÕES EM LOTE (JobActionsBar): quando ☐ selecionados                  │    │
│  │  [Publicar] [Insights] [Duplicar] [Alterar Status] [Atribuir Recrut.]  │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Pontos de IA nesta tela:**
| Elemento | Tipo IA | Backend Service | Domínio |
|----------|---------|----------------|---------|
| Busca inteligente | LLM (AI toggle) | `AISearchToggle` → `callOrchestratedJobsManagement` | Sourcing / Job Management |
| LIA Chat (prompt lateral) | LLM conversacional | `callOrchestratedJobsManagement` → Orchestrator | Job Management |
| Insights por vaga | LLM análise | `useLiaSuggestions` → `jd_enrichment_service` | Job Management |
| Sugestões proativas | LLM proativo | `IntelligenceNotifications` | Recruiter Assistant |
| Score pipeline (barra ████) | Determinístico | `CVScoringService` | CV Screening |

---

#### Tela 2: Gestão de Vagas — Painel LIA Expandido (`jobs-page.tsx`, estado `showExpandedLIA`)

Ao focar no mini prompt (Tela 1), o painel LIA expande à **esquerda** da tabela. A tabela é comprimida para a direita. Largura do painel: variável (`liaWidth` px, padrão ~400px). Modo 3 estados: mini prompt → expanded prompt → super chat (60%, max 900px no modo job-creation).

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  HEADER: 🧳 Gestão de Vagas                                    [+ Nova Vaga]  │
│  TABS: [Visão Geral | ●Todas(123) | Ativas(89) | Minhas(34) | Arquivadas(12)]  │
├─────────────────────────────────────────────────────────────────────────────────┤
│  (toolbar oculto quando LIA expandido — showExpandedLIA = true)                │
│                                                                                 │
│  ┌─────────────────────────────┐  ┌────────────────────────────────────────┐   │
│  │ LIA EXPANDED PANEL (~400px) │  │ TABELA DE VAGAS (flex-1, comprimida)  │   │
│  │ ← ESQUERDA                  │  │ → DIREITA                             │   │
│  │                              │  │                                        │   │
│  │ 🧠 "Olá! Sou a Lia."       │  │  ☐ │ Vaga         │ Pipeline │ Status │   │
│  │ "Como posso te ajudar?"      │  │  ──┼──────────────┼──────────┼────────│   │
│  │       [⤢ Expandir] [✕]      │  │  ☐ │ Dev Senior   │ ██▶██▶░░ │ Ativa  │   │
│  │                              │  │  ☐ │ UX Designer  │ ██▶░░▶░░ │ Ativa  │   │
│  │ ┌──────────────────────────┐ │  │  ☐ │ PM Lead      │ █░▶░░▶░░ │ Pausa  │   │
│  │ │ [3 vagas selecionadas]   │ │  │                                        │   │
│  │ └──────────────────────────┘ │  │                                        │   │
│  │                              │  │                                        │   │
│  │ [AI] SUGGESTION CARDS:       │  │                                        │   │
│  │ 💡 "3 vagas com candidatos   │  │                                        │   │
│  │     parados há +7 dias"      │  │                                        │   │
│  │ 💡 "Dev Senior: 5 prontos    │  │                                        │   │
│  │     para entrevista"         │  │                                        │   │
│  │ 💡 "JD de UX Designer pode   │  │                                        │   │
│  │     ser otimizada"           │  │                                        │   │
│  │                              │  │                                        │   │
│  │ [AI] Queries Guide:          │  │                                        │   │
│  │ "compare vagas abertas"      │  │                                        │   │
│  │ "quais precisam atenção?"    │  │                                        │   │
│  │                              │  │                                        │   │
│  │ ┌────────────────────┐       │  │                                        │   │
│  │ │ Prompt: _______[🎤]│       │  │                                        │   │
│  │ └────────────────────┘       │  │                                        │   │
│  └─────────────────────────────┘  └────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Pontos de IA nesta tela:**
| Elemento | Tipo IA | Backend Service | Domínio |
|----------|---------|----------------|---------|
| Suggestion Cards proativas | LLM análise contextual | `useLiaSuggestions` hook → `/lia/expanded-prompt` | Recruiter Assistant |
| Queries Guide | Determinístico (catálogo) | `LiaVacancyQueriesGuide` | — |
| Audio input (🎤) | STT (Deepgram) | `AudioRecordButton` → Deepgram API | Multimodal |
| JD Optimization suggestion | LLM análise | `JDEvaluationPanel` → `jd_enrichment_service` | Job Management |

---

#### Tela 3: Wizard de Criação de Vaga / Super Chat (`jobs-page.tsx`, modo `job-creation`)

O Wizard de criação de vaga reside **dentro da mesma página de vagas** (não é uma página separada). Quando ativado, o `ExpandedChatModal` ocupa **60% à esquerda** (max 900px), e a tabela comprime à direita. Em modo fullscreen (`isChatFullscreen`), o chat cobre 100% da área.

O `ExpandedChatModal` contém internamente: chat à esquerda e painéis contextuais (critérios, JD preview, skills) à direita.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  HEADER: 🧳 Gestão de Vagas                                    [+ Nova Vaga]  │
│  TABS: [Visão Geral | ●Todas | Ativas | Minhas | Arquivadas]                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌────────────────────────────────────────────┐  ┌─────────────────────────┐   │
│  │ SUPER CHAT LIA (60%, max 900px)            │  │ TABELA (comprimida)     │   │
│  │ ← ESQUERDA                                 │  │ → DIREITA               │   │
│  │                                             │  │                         │   │
│  │ ┌─────────────────────┬───────────────────┐ │  │ ☐ Dev Senior  ██▶░░   │   │
│  │ │ CHAT                │ SIDE PANEL        │ │  │ ☐ UX Design   █░▶░░   │   │
│  │ │                     │ (dentro do modal) │ │  │ ☐ PM Lead     ░░▶░░   │   │
│  │ │ [LIA]: "Vamos criar │                   │ │  │                         │   │
│  │ │  uma nova vaga!      │ JOB SUMMARY:     │ │  │ (tabela colapsa para   │   │
│  │ │  Qual o título?"[AI] │ Título: Dev Back │ │  │  dar espaço ao chat)   │   │
│  │ │                     │ Dept: Tecnologia  │ │  │                         │   │
│  │ │ [User]: "Dev Backend│ Skills: Python,Go │ │  │ [⤢] Botão fullscreen  │   │
│  │ │  Senior"            │ Senioridade: Sr   │ │  │  → tabela desaparece   │   │
│  │ │                     │ Modelo: Híbrido   │ │  │                         │   │
│  │ │ [LIA]: "Sugiro:     │ Faixa: R$15-20k  │ │  └─────────────────────────┘   │
│  │ │  • Python, Go       │                   │ │                                │
│  │ │  • Cloud (AWS/GCP)  │ [Editar][Preview] │ │                                │
│  │ │  • Microservices"   │                   │ │                                │
│  │ │                     │ PROGRESS TRACKER: │ │                                │
│  │ │ ⚙ Analisando...    │ ✓ Título          │ │                                │
│  │ │                     │ ✓ Skills          │ │                                │
│  │ │ [📎] [🎤] [Send ▶] │ ○ Salário         │ │                                │
│  │ │                     │ ○ Descrição       │ │                                │
│  │ └─────────────────────┴───────────────────┘ │                                │
│  │  [← Voltar ao prompt lateral]  [⤢ Fullscreen] [✕ Fechar]                   │
│  └────────────────────────────────────────────┘                                │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Pontos de IA nesta tela:**
| Elemento | Tipo IA | Backend Service | Domínio |
|----------|---------|----------------|---------|
| Chat conversacional (Wizard) | LLM (Claude) | `SmartJobWizardOrchestrator` → `JobWizardGraph` | Job Management |
| Sugestão de skills | LLM + Learning Loop | `skill_catalog_service` + `learning_hub_service` | Job Management |
| Sugestão salarial | LLM + dados mercado | `compensation_analysis_service` | Analytics |
| Thinking Indicator | — (UI status) | Estado do grafo LangGraph | — |
| WSI Score Card | WSI engine | `wsi_service.calculate_wsi_score()` | CV Screening |
| Progress Tracker | Determinístico | `WizardStage` state machine | — |
| Command Palette | Determinístico | `CommandPalette` component | — |
| Upload CV/Audio | Multimodal | `CVParserService` / Deepgram STT | Multimodal |
| Side Panel contextual | LLM + DET | `useUIActions` → `SidePanelContainer` | Job Management |

---

#### Tela 4: Job Kanban — Pipeline de Candidatos (`job-kanban-page.tsx`)

Layout `flex gap-2`: LIA sidebar à **esquerda** (quando `showExpandedLIA`), colunas Kanban ao **centro**, preview do candidato à **direita** (quando `isPreviewOpen`). Header com badges de vaga, tabs [Gestão | Editar], e botão LIA.

**Nota:** O Super Chat (`showSuperChat`) ocupa quase 100% com uma barra vertical de navegação (48px) à direita para voltar ao Kanban.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  HEADER: [← Voltar] | "Dev Backend Senior" [Ativa] [Sênior] [Híbrido] [Tech]  │
│          [💡 N sugestões da LIA]                         [Relatório] [Compart.] │
│  TABS: [●Gestão da Vaga | Editar Vaga]                                         │
│  VIEW: [●Kanban | Tabela] [Filtros] [LIA 🧠 toggle]                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────────┐ ┌─────────────────────────────────────────────────────┐   │
│  │ LIA SIDEBAR       │ │ KANBAN BOARD (flex-1, scroll horizontal)           │   │
│  │ ← ESQUERDA        │ │ → CENTRO/DIREITA                                  │   │
│  │ (liaExpandedWidth) │ │                                                    │   │
│  │                    │ │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐│   │
│  │ 🧠 "Olá! Sou a    │ │ │ Inscritos│ │ Triagem  │ │Entrevista│ │Proposta││   │
│  │    Lia."           │ │ │   (24)   │ │   (12)   │ │   (5)    │ │  (1)   ││   │
│  │ [⤢ Super] [✕]     │ │ ├──────────┤ ├──────────┤ ├──────────┤ ├────────┤│   │
│  │                    │ │ │┌────────┐│ │┌────────┐│ │┌────────┐│ │┌──────┐││   │
│  │ [N cand. selec.]   │ │ ││Ana S.  ││ ││Pedro M.││ ││Carla R.││ ││Maria ││   │
│  │                    │ │ ││WSI: 85 ││ ││WSI: 78 ││ ││WSI: 92 ││ ││WSI:95││   │
│  │ 💡 Sugestões LIA:  │ │ ││[AI]████││ ││[AI]███ ││ ││[AI]████││ ││[AI]██││   │
│  │ • "3 candidatos    │ │ ││⭐ Match ││ ││⚠ Gaps  ││ ││✓ Forte ││ ││★ Top ││   │
│  │    parados +7d"    │ │ │└────────┘│ │└────────┘│ │└────────┘│ │└──────┘││   │
│  │ • "Score alto em   │ │ │┌────────┐│ │┌────────┐│ │          │ │        ││   │
│  │    triagem"        │ │ ││João P. ││ ││Maria T.││ │          │ │        ││   │
│  │ • "Candidato em    │ │ ││WSI: 72 ││ ││WSI: 81 ││ │          │ │        ││   │
│  │    risco (alerta)" │ │ │└────────┘│ │└────────┘│ │          │ │        ││   │
│  │                    │ │ └──────────┘ └──────────┘ └──────────┘ └────────┘│   │
│  │ Chat:              │ │                                                    │   │
│  │ > "compare Pedro   │ │ ── Drag & Drop → UniversalTransitionModal [AI] ── │   │
│  │    e Maria"        │ │ [AI] Predição sub-status, ações automáticas        │   │
│  │ [AI] Resposta...   │ │                                                    │   │
│  │                    │ │ AÇÕES EM LOTE (ContextualActionsBanner):           │   │
│  │ [📎] [🎤] [Send]  │ │ [Mensagem] [Mover] [Rejeitar] [Lista] [Comparar]  │   │
│  └──────────────────┘ └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Pontos de IA nesta tela:**
| Elemento | Tipo IA | Backend Service | Domínio |
|----------|---------|----------------|---------|
| WSI Score por candidato | WSI engine + LLM | `wsi_service` + `rubric_evaluation_service` | CV Screening |
| AI Suggestion Badge | LLM contextual | `useCandidateSuggestions` → `AISuggestionBadge` | Recruiter Assistant |
| Transição de etapa (drag) | LLM predição sub-status | `bulk-predict-substatus` → `UniversalTransitionModal` | Pipeline Transition |
| TransitionChatPanel | LLM conversacional | `callOrchestratedJobChat` | Pipeline Transition |
| Super Chat | LLM contextual | `callKanbanAssistant` → Orchestrator | Job Management |
| Batch rejection | LLM (sub-status AI) | `CandidateContextAggregator` + LLM | Pipeline Transition |
| Candidate insights | LLM análise | `lia_insights` (strengths/concerns/recommendation) | CV Screening |

---

#### Tela 5: Job Kanban — Modo Tabela (`job-kanban-page.tsx`, `viewMode="table"`)

Mesma página, alternando para tabela. Layout mantém `flex gap-2`: LIA à **esquerda**, tabela ao **centro**, preview de candidato à **direita**. Acima da tabela, Pipeline Stages Carousel com contagem por etapa (filtro por clique).

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  HEADER: [← Voltar] | "Dev Backend Senior" [badges]       [Relatório][Compart.]│
│  TABS: [●Gestão | Editar]    VIEW: [Kanban | ●Tabela] [Filtros] [LIA 🧠]      │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PIPELINE FLOW: [Inscritos(24)] → [Triagem(12)] → [Entrevista(5)] → [Prop(1)] │
│  (PipelineStagesCarousel — clique filtra tabela)       [Limpar filtro]         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────────┐ ┌──────────────────────────────────┐ ┌────────────────┐  │
│  │ LIA SIDEBAR       │ │ UNIFIED CANDIDATE TABLE          │ │ PREVIEW (400px)│  │
│  │ ← ESQUERDA        │ │ → CENTRO                         │ │ → DIREITA      │  │
│  │                    │ │                                   │ │                │  │
│  │ 🧠 Olá! Sou a Lia │ │  ☐│ Nome    │ Etapa  │WSI│Match│ │ │ [Candidato]    │  │
│  │ [⤢ Super] [✕]     │ │  ─┼─────────┼────────┼───┼─────│ │ │ Ana Silva      │  │
│  │                    │ │  ☐│ Maria L │Proposta│ 95│[AI]★│ │ │ WSI: 85/100   │  │
│  │ Sugestões LIA:     │ │  ☐│ Carla R │Entrev. │ 92│[AI]★│ │ │               │  │
│  │ • "Score alto..."  │ │  ☐│ Lucas F │Teste   │ 88│[AI]☆│ │ │ Skills:        │  │
│  │ • "Parado +7d"     │ │  ☐│ Ana S.  │Inscrita│ 85│[AI]☆│ │ │ Python ████   │  │
│  │                    │ │  ☐│ Pedro M │Triagem │ 78│[AI]☆│ │ │ Go     ███    │  │
│  │ Chat:              │ │                                   │ │               │  │
│  │ > "quais cand..."  │ │  [AI] SubStatus interativo       │ │ Ações:         │  │
│  │ [AI] Resposta...   │ │  [AI] Stage interativo (mover)   │ │ [Avançar]      │  │
│  │                    │ │  Sort: [↕ Nome] [↕ WSI]          │ │ [Rejeitar]     │  │
│  │ [📎] [🎤] [Send]  │ │  Filtros: [Etapa▼] [Score≥__]    │ │ [⤢][✕]        │  │
│  └──────────────────┘ └──────────────────────────────────┘ └────────────────┘  │
│                                                                                 │
│  AÇÕES EM LOTE (ContextualActionsBanner):                                      │
│  [✓ 3 selecionados] [Mensagem] [Mover] [Rejeitar] [Lista] [Comparar]          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Pontos de IA nesta tela:**
| Elemento | Tipo IA | Backend Service | Domínio |
|----------|---------|----------------|---------|
| Coluna WSI Score | WSI engine | `wsi_service` | CV Screening |
| Coluna Match (aderência) | LLM + rubric | `rubric_evaluation_service` | CV Screening |
| Sub-Status interativo | LLM predição | `InteractiveSubStatusCell` → `bulk-predict-substatus` | Pipeline Transition |
| Stage interativo | LLM sugestão | `InteractiveStageCell` → `SmartTransitionModal` | Pipeline Transition |
| Pearch Insights (filtro) | LLM externo | Pearch AI API → `pearch_insights` | Sourcing |
| Sort por score | Determinístico | Frontend sort | — |

---

#### Tela 6: Funil de Talentos — Busca e Resultados (`candidates-page.tsx`)

Layout `flex gap-4` (linha 7812): LIA à **esquerda**, tabela de candidatos ao **centro**, preview do candidato à **direita**. Comentário no código: `ORDEM: LIA à esquerda, Filtros à direita, Tabela ao centro`. Super Chat (`isLiaSuperChat`) faz a tabela colapsar para apenas 14px (ícone vertical).

O prompt LIA com entity parsing em tempo real (debounce 500ms → `/api/backend-proxy/search/parse-query`).

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  HEADER: 👥 Funil de Talentos                                                   │
│  TABS: [●Busca | Favoritos | Histórico | Listas | Buscas Salvas]                │
├─────────────────────────────────────────────────────────────────────────────────┤
│  TOOLBAR: [Prompt LIA max 300px] [🎤][🔍]  [Sel.Todos] [Filtros] [Colunas]    │
│   ↳ ao focar, expande para LIA sidebar (esquerda)                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────────┐ ┌──────────────────────────────────┐ ┌────────────────┐  │
│  │ LIA SIDEBAR       │ │ CANDIDATE TABLE (flex-1)          │ │ PREVIEW        │  │
│  │ ← ESQUERDA        │ │ → CENTRO                         │ │ → DIREITA      │  │
│  │ (~400px)          │ │                                   │ │ (resizable)    │  │
│  │                    │ │                                   │ │                │  │
│  │ 🧠 Olá! Sou a Lia │ │  ☐│ Nome    │Cargo   │Match│Fonte│ │ │ 👤 Ana Costa  │  │
│  │ "Posso criar vagas,│ │  ─┼─────────┼────────┼─────┼─────│ │ │ Backend Sr    │  │
│  │  buscar candidatos"│ │  ☐│ Ana C.  │BEnd Sr │[AI]95│Base│ │ │ São Paulo     │  │
│  │ [⤢ Super] [✕]     │ │  ☐│ Lucas M │FStack  │[AI]88│Base│ │ │               │  │
│  │                    │ │  ☐│ Priya S │Python  │[AI]82│Pch │ │ │ WSI: 85/100  │  │
│  │ [N cand selec.]    │ │                                   │ │ │ Skills:       │  │
│  │ LIA: "Você selec.  │ │  [AI] Match Score = WRF scorer   │ │ │ Python ████  │  │
│  │  3 candidatos..."  │ │  [AI] Parsed Entities:           │ │ │ Go     ███   │  │
│  │                    │ │  [Python] [SP] [Sênior] [3+anos] │ │ │               │  │
│  │ Chat:              │ │  [AI] Feedback: [👍] [👎]         │ │ │ [Avançar]     │  │
│  │ > "buscar devs     │ │                                   │ │ │ [Rejeitar]    │  │
│  │    python fintech" │ │  AÇÕES EM LOTE:                  │ │ │ [📧][📱]      │  │
│  │ [AI] Resposta...   │ │  [Add Vaga][Lista][Msg][Comparar]│ │ │ [⤢ Max][✕]   │  │
│  │ [📎] [🎤] [Send]  │ │                                   │ │ │              │  │
│  └──────────────────┘ └──────────────────────────────────┘ └────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Pontos de IA nesta tela:**
| Elemento | Tipo IA | Backend Service | Domínio |
|----------|---------|----------------|---------|
| Prompt LIA (entity parse) | LLM NLP (debounce 500ms) | `/api/backend-proxy/search/parse-query` → entity extraction | Sourcing |
| Match Score (WRF) | Elasticsearch + PGVector + LLM | `talent_funnel_search` → WRF scorer | Sourcing |
| Search Feedback (👍/👎) | Reinforcement learning | `SearchFeedbackButtons` → `search_feedback_service` | Sourcing |
| Parsed Entities (tags) | LLM NLP | response.entities → UI pills | Sourcing |
| LIA Chat sidebar | LLM conversacional | `callOrchestratedTalentChat` → Orchestrator | Sourcing |
| Auto-expand on selection | Determinístico | `useEffect` (prevSelectedCountRef) | — |
| LIA Batch Analysis | WSI engine + LLM | `LIABatchAnalysis` → `wsi_service` | CV Screening |
| Pearch integration | API externa + LLM | Pearch AI → `promoteCandidateToBase` | Sourcing |
| Audio search (🎤) | STT (Deepgram) | `AudioRecordButton` → Deepgram | Multimodal |
| SuperChat (fullscreen) | LLM conversacional | `isLiaSuperChat` → tabela colapsa 14px | Sourcing |

---

#### Tela 7: Preview de Candidato — Perfil + CV + WSI Scorecard (`candidate-preview.tsx`)

Painel lateral que aparece à **direita** da tabela (tanto no Kanban quanto no Funil de Talentos). Largura: 400px (padrão) ou 600px (maximizado). Resizable via drag na borda esquerda. Contém tabs e navegação entre candidatos (←/→).

```
┌──────────────────────────────────────────────────────────────────────┐
│  CANDIDATE PREVIEW — Painel lateral DIREITO (400-600px)              │
│  ← Handle de resize                          [⤢ Maximizar] [✕]     │
│  [← Anterior] [→ Próximo]  (navegação entre candidatos)             │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  👤 Ana Costa              [🔗 LinkedIn] [📧 Email] [📱 WhatsApp]   │
│  Backend Developer Senior | São Paulo                                │
│  📧 ana@email.com | 📱 +55 11 99999                                 │
│                                                                      │
│  TABS: [Resumo | CV | Triagem | Notas | Histórico]                  │
│                                                                      │
│  ┌──── WSI SCORECARD [AI] ──────────────────────────────────────┐   │
│  │  Score Global: 85/100                                         │   │
│  │                                                               │   │
│  │  B1 Hard Skills:    ████████░░  82%                          │   │
│  │  B2 Soft Skills:    █████████░  90%                          │   │
│  │  B3 Experiência:    ████████░░  80%                          │   │
│  │  B4 Cultural Fit:   █████████░  88%                          │   │
│  │  B5 Motivação:      ████████░░  85%                          │   │
│  │  B6 Potencial:      █████████░  92%                          │   │
│  │  B7 Risco:          ██░░░░░░░░  20% (baixo risco = bom)     │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──── CV PREVIEW [AI] ────────────────────────────────────────┐   │
│  │  [AI] Parsed by CVParserService (Claude Vision)              │   │
│  │  • Experiência: 8 anos (Python, Go, PostgreSQL)              │   │
│  │  • Formação: Eng. Computação — USP                           │   │
│  │  • Última empresa: Nubank (3 anos)                           │   │
│  │  • Skills extraídas: [Python][Go][AWS][Docker][K8s]          │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──── LIA INSIGHTS [AI] ─────────────────────────────────────┐   │
│  │  Strengths: Perfil sênior sólido, fit cultural alto          │   │
│  │  Concerns: Sem experiência com microservices Go              │   │
│  │  Recommendation: Avançar para entrevista técnica             │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  AÇÕES:                                                              │
│  [AI] Triagem WSI: [Iniciar] [Ver resultado]                        │
│  [AI] Big Five: [Aplicar teste]                                      │
│  [AI] English Test: [Aplicar]                                        │
│  [📧 Mensagem] [📋 Mover Etapa] [⭐ Favoritar] [📄 Abrir Página]    │
│  [Agendar Entrevista] [Adicionar a Lista]                            │
└──────────────────────────────────────────────────────────────────────┘
```

**Pontos de IA nesta tela:**
| Elemento | Tipo IA | Backend Service | Domínio |
|----------|---------|----------------|---------|
| WSI Scorecard (7 blocos) | WSI engine + LLM | `wsi_service.calculate_wsi_score()` | CV Screening |
| CV Preview (parsed) | LLM (Claude Vision) | `CVParserService` → multimodal | CV Screening |
| LIA Insights | LLM análise | `lia_insights` (strengths/concerns/recommendation) | CV Screening |
| Triagem WSI | Voice + LLM | `WSIScreeningPipeline` → OpenMic.ai + Claude | CV Screening |
| Big Five test | Psychometric + LLM | `BigFiveModal` → `psychometric_service` | CV Screening |
| English Test | LLM avaliação | `EnglishTestModal` → `english_test_service` | CV Screening |

---

### 2.1 Fluxo: Wizard de Criação de Vaga

O Job Wizard é uma experiência conversacional onde a LIA guia o recrutador pela criação completa de uma vaga. O fluxo é implementado como uma máquina de estados (`WizardStage` enum em `app/shared/agents/state_machine.py`) com um grafo LangGraph (`JobWizardGraph`) que gerencia a coleta de dados.

**Etapas do Wizard (WizardStage enum):**
`INITIAL → TITLE_DEPARTMENT → JOB_SUMMARY → SALARY → COMPETENCIES → SCREENING → REVIEW → SEARCH_CALIBRATION → COMPLETE`

```
Recrutador: "Quero criar uma vaga de Dev Python Senior"
      |
      v
+------------------------------------------------------------+
| ORQUESTRADOR CENTRAL                                        |
|  CascadedRouter detecta intent -> job_management            |
|  WizardOrchestratorService identifica WizardIntent          |
+-----------------------------+------------------------------+
                              |
                              v
+------------------------------------------------------------+
| JobWizardGraph (LangGraph State Machine)                    |
|                                                             |
|  +------------------+    +------------------+               |
|  | job_state_loader |    | job_router       |               |
|  | (carrega estado) |--->| (decide proximo  |               |
|  +------------------+    |  node)           |               |
|                          +--------+---------+               |
|                                   |                         |
|           +-----------+-----------+-----------+             |
|           |           |           |           |             |
|           v           v           v           v             |
|  +-------------+ +----------+ +----------+ +----------+    |
|  | onboarding  | | basics   | | remunera | | technical|    |
|  | _node       | | _collec  | | tion_col | | _matrix  |    |
|  | (INITIAL)   | | tor      | | lector   | | _collec  |    |
|  +-------------+ | (TITLE_  | | (SALARY) | | tor      |    |
|                   | DEPT)    | +----------+ | (COMPET) |    |
|                   +----------+              +----------+    |
|           |           |           |           |             |
|           v           v           v           v             |
|  +-------------+ +----------+ +----------+ +----------+    |
|  | screening   | | wsi_comp | | interview| | governance|   |
|  | _collector  | | etencies | | _flow_co | | _collector|   |
|  | (SCREENING) | | _collec  | | llector  | |           |   |
|  +-------------+ +----------+ +----------+ +----------+    |
|                          |                                  |
|                          v                                  |
|  +------------------+  +------------------+                 |
|  | validator        |  | frame_generator  |                 |
|  | (valida campos)  |  | (gera frame de   |                 |
|  +------------------+  |  resposta)       |                 |
|                         +--------+---------+                |
|                                  |                          |
|                                  v                          |
|  +----------------------------+  +--------------------+     |
|  | job_description_generator  |  | publication_node   |     |
|  | (gera JD com IA)           |  | (publica vaga)     |     |
|  +----------------------------+  +--------------------+     |
+------------------------------------------------------------+
      |
      v
+------------------------------------------------------------+
| FLUXO CONVERSACIONAL (a cada etapa):                        |
|                                                             |
|  1. LIA pergunta -> "Qual o titulo da vaga?"                |
|  2. Recrutador responde -> "Dev Python Senior"              |
|  3. LIA processa via JobWizardGraph                         |
|     -> basics_collector extrai dados                        |
|     -> validator confirma campos                            |
|     -> response_planner gera resposta                       |
|  4. LIA avanca etapa -> TITLE_DEPARTMENT -> JOB_SUMMARY     |
|  5. LIA pergunta proxima etapa -> "Descreva a vaga..."      |
+------------------------------------------------------------+
      |
      v
+------------------------------------------------------------+
| ENRIQUECIMENTO COM IA (durante e apos wizard):              |
|                                                             |
|  - jd_generator_service    -> Gera JD estruturada           |
|  - jd_enrichment_service   -> Benchmarks, skills sugeridas  |
|  - job_insights_service    -> Faixa salarial de mercado     |
|  - get_market_salary_bench -> Dados de remuneracao          |
|  - change_request_processor-> Processa alteracoes           |
+------------------------------------------------------------+
      |
      v
   Vaga criada, enriquecida e publicada
```

**WizardIntent (intencoes detectadas pelo WizardOrchestratorService):**
`PUBLISH_JOB`, `PAUSE_JOB`, `CLOSE_JOB`, `SAVE_DRAFT`, `VALIDATE_FIELDS`, `GET_SUGGESTIONS`, `SEARCH_SALARY`, `UPDATE_FIELD`

#### Tabela de Mapeamento — Wizard de Criação de Vaga

| Etapa | Domínio | Serviços | Ferramentas (Tools) | Agentes | Prompts/LLM |
|-------|---------|----------|---------------------|---------|-------------|
| Detecção de intent | Orquestrador | `CascadedRouter`, `WizardOrchestratorService` | — | — | Regex (Layer 2) ou Claude (Layer 3) |
| Onboarding (INITIAL) | `job_management` | `wizard_orchestrator_service` | `get_wizard_step` | `job_intake_agent` | `job_management.yaml` — prompt de coleta |
| Título e Departamento (TITLE_DEPARTMENT) | `job_management` | `wizard_data_priority_service` | `create_job_vacancy`, `update_job_vacancy` | `job_intake_agent` | Claude — extração de campos |
| Resumo da Vaga (JOB_SUMMARY) | `job_management` | `jd_generator_service`, `jd_enrichment_service` | `generate_job_description`, `enrich_job_description` | `job_drafting_agent` | Claude — geração e enriquecimento de JD |
| Remuneração (SALARY) | `job_management` | `job_insights_service`, `wizard_data_priority_service` | `get_job_analytics` | `job_benefits_comp_agent` | Claude — benchmark salarial |
| Competências (COMPETENCIES) | `job_management` | `wizard_orchestrator_service` | `update_job_vacancy` | `job_rubric_agent` | Claude — extração de competências |
| Triagem (SCREENING) | `job_management` | `wizard_orchestrator_service` | `advance_wizard` | `job_intake_agent` | Claude — perguntas de triagem |
| Revisão (REVIEW) | `job_management` | `wizard_orchestrator_service` | `get_wizard_step`, `get_job_health` | `job_lifecycle_agent` | Claude — validação e sugestões |
| Calibração de Busca (SEARCH_CALIBRATION) | `job_management` | `job_insights_service`, `wizard_analytics_service` | `search_job_templates`, `get_job_analytics` | `job_insights_agent` | Claude — calibração de perfil |
| Publicação (COMPLETE) | `job_management` | `job_vacancy_service`, `job_template_service` | `create_job_vacancy`, `close_job_vacancy`, `pause_job_vacancy` | `job_lifecycle_agent` | — (determinístico) |

**Nodes do Grafo LangGraph (`job_vacancy_nodes.py`):**
`job_state_loader`, `job_router`, `onboarding_node`, `basics_collector`, `remuneration_collector`, `technical_matrix_collector`, `interview_flow_collector`, `screening_collector`, `governance_collector`, `org_structure_collector`, `sourcing_strategy_collector`, `wsi_competencies_collector`, `communication_templates_collector`, `job_description_generator`, `publication_node`, `get_market_salary_benchmark`, `change_request_processor`, `validator`, `frame_generator`, `response_planner`

---

### 2.2 Fluxo: Jornada Completa do Candidato (Aplicação → Contratação)

Este fluxo mostra a jornada end-to-end de um candidato por todas as etapas do pipeline, desde a aplicação até a contratação, identificando em cada etapa quais domínios, serviços e ferramentas de IA são acionados.

```
APLICACAO       TRIAGEM CV      SCREENING WSI    ENTREVISTA
    |               |               |               |
    v               v               v               v
+----------+   +----------+   +----------+   +----------+
| 1.Sourc  |   | 2.CV     |   | 3.WSI    |   | 4.Inter  |
| ing &    |-->| Screen   |-->| Screen   |-->| view &   |
| Captacao |   | ing      |   | ing      |   | Schedul  |
|          |   |          |   |          |   | ing      |
| search   |   | CVParser |   | wsi_ques |   | schedul  |
| _candid  |   | CVScoring|   | tion_gen |   | ing_svc  |
| ates     |   | Service  |   | erator   |   | calendar |
| candidate|   | wsi_scr  |   | wsi_ques |   | _service |
| _match   |   | eening_  |   | tion_svc |   | deepgram |
| pearch   |   | pipeline |   | seniority|   | _service |
| _search  |   |          |   | _resolver|   |          |
+----------+   +----------+   +----------+   +----------+
    |               |               |               |
    v               v               v               v
 Dominio:       Dominio:        Dominio:        Dominio:
 sourcing       cv_screening    cv_screening    interview_
                                                scheduling
    |               |               |               |
    v               v               v               v

AVALIACAO       OFERTA          CONTRATACAO
    |               |               |
    v               v               v
+----------+   +----------+   +----------+
| 5.Avali  |   | 6.Oferta |   | 7.Contr  |
| acao &   |   | & Nego   |   | atacao   |
| Rubrica  |   | ciacao   |   |          |
|          |   |          |   | move_    |
| rubric_  |   | email_   |   | candidate|
| evaluat  |   | service  |   | (pipeline|
| ion_svc  |   | whatsapp |   | _transit |
| score_   |   | _service |   | ion)     |
| normaliz |   | teams_   |   |          |
| ation_svc|   | service  |   |          |
+----------+   +----------+   +----------+
    |               |               |
    v               v               v
 Dominio:       Dominio:        Dominio:
 cv_screening   communication   pipeline_
                                transition
```

**Como a IA toma decisões em cada etapa:**

```
Candidato aplica
      |
      v
[1] SOURCING: IA calcula match candidato-vaga
    -> Embedding similarity + WRF (Weighted Ranking Framework)
    -> Score de compatibilidade 0-100
      |
      v
[2] TRIAGEM CV: IA extrai dados e avalia CV
    -> CVParserService: Claude extrai dados estruturados
    -> CVScoringService: BARS (Behaviorally Anchored Rating Scales)
    -> Score rubrica = SUM(points_i * evidence_weight_i * multiplier_i)
    -> Evidence weights: explicit=1.0, implicit=0.7, inferred=0.3
      |
      v
[3] SCREENING WSI: IA gera e avalia perguntas
    -> Pipeline 5 blocos (ver Fluxo 2.6)
    -> Calibracao de senioridade multi-signal
    -> Taxonomia de Bloom + Modelo de Dreyfus
      |
      v
[4] ENTREVISTA: IA analisa respostas em tempo real
    -> Deepgram Nova-2 transcreve audio
    -> Analise de tom e confianca
    -> Deteccao de respostas evasivas
    -> Follow-up inteligente
      |
      v
[5] AVALIACAO: IA normaliza e rankeia
    -> score_normalization_service: normaliza entre candidatos
    -> Corte dinamico: top 25%
    -> Recomendacao: 85%+ Altamente Recomendado,
       70-84% Recomendado, 55-69% Potencial,
       40-54% Baixo Match, <40% Nao Recomendado
      |
      v
[6] OFERTA: IA personaliza comunicacao
    -> Templates personalizados por canal
    -> CommunicationDispatcher envia via Mailgun/Twilio
      |
      v
[7] CONTRATACAO: IA sugere acoes e move pipeline
    -> predict_sub_status via LLM
    -> suggest_next_action baseado em contexto
    -> AuditService registra decisao final
```

#### Tabela de Mapeamento — Jornada Completa do Candidato

| Etapa | Domínio | Serviços | Ferramentas (Tools) | Agentes | Prompts/LLM |
|-------|---------|----------|---------------------|---------|-------------|
| 1. Aplicação / Sourcing | `sourcing` | `SourcingPipelineService`, `VacancySearchService`, `PearchService`, `WRFService` | `search_candidates`, `candidate_match`, `pearch_search`, `semantic_search` | Sourcing Agent | `sourcing.yaml` — busca semântica e match |
| 2. Triagem de CV | `cv_screening` | `CVParserService`, `CVScoringService`, `wsi_screening_pipeline` | `parse_cv`, `score_cv`, `evaluate_rubric`, `check_eligibility` | CV Screening Agent | `cv_screening.yaml` — extração e scoring |
| 3. Screening WSI | `cv_screening` | `WSIQuestionGenerator`, `WSIQuestionService`, `SeniorityResolver`, `CalibrationProfiles` | `generate_wsi_questions`, `calculate_wsi`, `assess_seniority`, `classify_bloom` | CV Screening Agent | Claude — geração de perguntas, Bloom/Dreyfus |
| 4. Entrevista | `interview_scheduling` | `SchedulingService`, `CalendarService`, `DeepgramService` | `scheduling_schedule_interview`, `scheduling_transcribe_audio`, `scheduling_analyze_voice` | Interview Agent | `interview_scheduling.yaml` — análise de respostas |
| 5. Avaliação | `cv_screening` | `RubricEvaluationService`, `ScoreNormalizationService` | `evaluate_rubric`, `normalize_scores`, `rank_candidates` | CV Screening Agent | Claude — avaliação de evidências |
| 6. Oferta | `communication` | `EmailService`, `WhatsAppService`, `CommunicationService` | `communication_send_email`, `communication_send_whatsapp` | Communication Agent | `communication.yaml` — personalização |
| 7. Contratação | `pipeline_transition` | `KanbanAssistantService` | `move_candidate`, `predict_sub_status`, `suggest_next_action` | Pipeline Agent | Prompt inline — interpretação de contexto |

**Domínios transversais ativos durante toda a jornada:**
- `analytics` — KPIs de funil, previsões de contratação, tempo de preenchimento
- `automation` — StageAutomationEngine dispara automações em cada transição
- `ats_integration` — Sincroniza status e scores com ATS externos (Gupy, Pandapé, Merge)

---

### 2.3 Fluxo: Comunicação WhatsApp com Candidatos

Fluxo completo de comunicação via WhatsApp, desde o envio de uma mensagem até o rastreamento de status e coleta conversacional de dados.

```
Recrutador solicita envio WhatsApp
      |
      v
+------------------------------------------------------------+
| ORQUESTRADOR -> Dominio: communication                      |
| Action: send_whatsapp                                       |
+-----------------------------+------------------------------+
                              |
                              v
+------------------------------------------------------------+
| WhatsAppService (orquestrador principal)                    |
|                                                             |
|  +------------------+                                       |
|  | Verifica opt-out |  CandidateOptOut check                |
|  | e consentimento  |  (LGPD compliance)                    |
|  +--------+---------+                                       |
|           |                                                 |
|           v                                                 |
|  +------------------+    +-------------------------+        |
|  | WhatsAppProvider |    | SendWhatsAppTemplate    |        |
|  | (abstract)       |    | Request (templates      |        |
|  +--------+---------+    | pre-aprovados)          |        |
|           |              +-------------------------+        |
|     +-----+------+                                          |
|     |            |                                          |
|     v            v                                          |
|  +----------+ +------------+                                |
|  | Twilio   | | Meta       |                                |
|  | WhatsApp | | WhatsApp   |                                |
|  | Service  | | Service    |                                |
|  +----------+ +------------+                                |
+-----------------------------+------------------------------+
                              |
                              v
+------------------------------------------------------------+
| CommunicationDispatcher (baixo nivel)                       |
|                                                             |
|  - Twilio REST API: messages.create()                       |
|  - from_: whatsapp:+14155238886 (sandbox)                   |
|  - to: whatsapp:+55XXXXXXXXXXX                              |
|  - Mock success quando Twilio nao configurado               |
+-----------------------------+------------------------------+
                              |
                              v
+------------------------------------------------------------+
| STATUS TRACKING                                             |
|                                                             |
|  PENDING -> QUEUED -> SENT -> DELIVERED -> READ             |
|                                                             |
|  - Webhooks Twilio atualizam status                         |
|  - CommunicationLog registra cada etapa                     |
+------------------------------------------------------------+

--- FLUXO DE COLETA CONVERSACIONAL (DataRequestWhatsAppService) ---

+------------------------------------------------------------+
| DataRequestWhatsAppService                                  |
|                                                             |
|  1. start_collection()                                      |
|     -> Inicia coleta de dados do candidato                  |
|     -> Define campos a coletar                              |
|                                                             |
|  2. process_consent_response()                              |
|     -> Verifica consentimento LGPD                          |
|     -> WhatsAppConversationState = AWAITING_CONSENT         |
|                                                             |
|  3. send_field_request()                                    |
|     -> Envia pergunta sobre proximo campo                   |
|     -> WhatsAppConversationState = COLLECTING_DATA          |
|                                                             |
|  4. process_choice_response()                               |
|     -> Processa respostas de multipla escolha               |
|                                                             |
|  5. process_document_response()                             |
|     -> Processa documentos enviados (CV, certificados)      |
|     -> WhatsAppConversationState = COMPLETED                |
+------------------------------------------------------------+
```

#### Tabela de Mapeamento — Comunicação WhatsApp

| Etapa | Domínio | Serviços | Ferramentas (Tools) | Agentes | Prompts/LLM |
|-------|---------|----------|---------------------|---------|-------------|
| Detecção de intent | Orquestrador | `CascadedRouter` | — | — | Regex/LLM |
| Verificação de opt-out | `communication` | `CommunicationService` (CandidateOptOut) | — | — | — (determinístico) |
| Envio de mensagem | `communication` | `WhatsAppService`, `CommunicationDispatcher` | `communication_send_whatsapp` | Communication Agent | `communication.yaml` |
| Envio por template | `communication` | `WhatsAppService` (SendWhatsAppTemplateRequest) | `communication_send_whatsapp` | — | — (template pré-aprovado) |
| Rastreamento de status | `communication` | `CommunicationService` (CommunicationLog) | `communication_get_history` | — | — (webhook/determinístico) |
| Coleta conversacional | `communication` | `DataRequestWhatsAppService`, `WhatsAppConversationState` | `communication_data_request` | Communication Agent | Claude — interpretação de respostas |
| Processamento de documentos | `communication` / `cv_screening` | `DataRequestWhatsAppService`, `CVParserService` | `parse_cv` | CV Screening Agent | Claude — extração de CV |

**Integrações externas:** Twilio WhatsApp API, Meta WhatsApp Business API

---

### 2.4 Fluxo: Comunicação Teams com Recrutadores

Fluxo completo de comunicação via Microsoft Teams, incluindo notificações por webhook, interações por bot e gravação de reuniões.

```
+------------------------------------------------------------+
| CANAL 1: INCOMING WEBHOOKS (notificacoes de canal)          |
+------------------------------------------------------------+
|                                                             |
| TeamsService                                                |
|  |                                                          |
|  +-> send_message(webhook_url, text, severity)              |
|  |     -> Adaptive Card com niveis:                         |
|  |        INFO (azul), SUCCESS (verde),                     |
|  |        WARNING (amarelo), ERROR (vermelho),              |
|  |        CRITICAL (vermelho escuro)                        |
|  |                                                          |
|  +-> send_alert(webhook_url, title, details, severity)      |
|  |     -> Card com titulo, detalhes, timestamp              |
|  |                                                          |
|  +-> send_candidate_notification(webhook_url, candidate,    |
|        vacancy, action)                                     |
|        -> Card com dados do candidato e acao realizada      |
|                                                             |
+------------------------------------------------------------+

+------------------------------------------------------------+
| CANAL 2: BOT FRAMEWORK (conversas interativas)              |
+------------------------------------------------------------+
|                                                             |
| TeamsBot (Bot Framework SDK)                                |
|  |                                                          |
|  +-> process_activity(activity)                             |
|  |     |                                                    |
|  |     +-> _handle_message (mensagens de texto)             |
|  |     |     -> Roteia para LIA Orchestrator                |
|  |     |     -> Retorna resposta da IA                      |
|  |     |                                                    |
|  |     +-> _handle_conversation_update                      |
|  |     |     -> Boas-vindas a novos membros                 |
|  |     |                                                    |
|  |     +-> _handle_invoke                                   |
|  |           -> Processar acoes de Adaptive Cards           |
|  |                                                          |
|  +-> send_proactive_message(conversation_id, message)       |
|  |     -> Notificacoes proativas para recrutadores          |
|  |                                                          |
|  +-> send_notification(user_id, notification)               |
|        -> Notificacao direta por user_id                    |
|                                                             |
+------------------------------------------------------------+

+------------------------------------------------------------+
| CANAL 3: GRAVACAO DE REUNIOES                               |
+------------------------------------------------------------+
|                                                             |
| TeamsRecordingService                                       |
|  |                                                          |
|  +-> Captura gravacoes de entrevistas no Teams              |
|  +-> Envia para DeepgramService para transcricao            |
|  +-> Resultado disponivel para analise WSI                  |
|                                                             |
+------------------------------------------------------------+

+------------------------------------------------------------+
| AUTENTICACAO                                                |
+------------------------------------------------------------+
|                                                             |
| teams_auth.py                                               |
|  |                                                          |
|  +-> Validacao de tokens do Bot Framework                   |
|  +-> Verificacao de tenant_id                               |
|  +-> Refresh automatico de credenciais                      |
+------------------------------------------------------------+
```

#### Tabela de Mapeamento — Comunicação Teams

| Etapa | Domínio | Serviços | Ferramentas (Tools) | Agentes | Prompts/LLM |
|-------|---------|----------|---------------------|---------|-------------|
| Notificação por webhook | `communication` | `TeamsService` (Incoming Webhooks) | `communication_send_teams` | — | — (determinístico, Adaptive Cards) |
| Alerta de severidade | `communication` | `TeamsService` (send_alert) | `communication_send_teams` | — | — (template com severity levels) |
| Notificação de candidato | `communication` | `TeamsService` (send_candidate_notification) | `communication_send_teams` | Communication Agent | `communication.yaml` — personalização |
| Conversa interativa (Bot) | `communication` + Orquestrador | `TeamsBot` (Bot Framework), `Orchestrator` | — (roteado para domínio adequado) | Todos (via Orchestrator) | Prompt do domínio detectado |
| Mensagem proativa | `communication` | `TeamsBot` (send_proactive_message) | `communication_send_teams` | Recruiter Assistant Agent | `recruiter_assistant.yaml` — insights |
| Gravação de reunião | `communication` / `interview_scheduling` | `TeamsRecordingService`, `DeepgramService` | `scheduling_transcribe_audio` | Interview Agent | Deepgram Nova-2 (transcrição) |
| Autenticação | `communication` | `teams_auth.py` | — | — | — (OAuth2/Bot Framework) |

**Integrações externas:** Microsoft Graph API, Bot Framework SDK, Deepgram

---

### 2.5 Fluxo: Comunicação Email

Fluxo completo de comunicação por email, incluindo envio individual, em massa, templates e gerenciamento de consentimento LGPD.

```
Recrutador solicita envio de email
      |
      v
+------------------------------------------------------------+
| ORQUESTRADOR -> Dominio: communication                      |
| Action: send_email / send_bulk_email                        |
+-----------------------------+------------------------------+
                              |
                              v
+------------------------------------------------------------+
| EmailService (orquestrador principal)                       |
|                                                             |
|  +------------------+                                       |
|  | Template Engine  |  email_templates_data.py              |
|  | Renderiza HTML   |  recruitment_email_templates.py       |
|  | com variaveis    |  (templates de recrutamento)          |
|  +--------+---------+                                       |
|           |                                                 |
|           v                                                 |
|  +------------------+                                       |
|  | MessageProvider  |  (abstract)                           |
|  +--------+---------+                                       |
|           |                                                 |
|     +-----+----------+                                      |
|     |                |                                      |
|     v                v                                      |
|  +----------+  +------------+                               |
|  | Mailgun |  | Mock       |                               |
|  | Provider |  | Email      |                               |
|  | (prod)   |  | Provider   |                               |
|  |          |  | (dev)      |                               |
|  +----------+  +------------+                               |
+-----------------------------+------------------------------+
                              |
                              v
+------------------------------------------------------------+
| CommunicationService (orquestrador unificado multi-canal)   |
|                                                             |
|  +------------------+  +------------------+                 |
|  | PendingApproval  |  | CommunicationLog |                 |
|  | (bulk email      |  | (registro de     |                 |
|  |  requer aprovacao|  |  cada envio)     |                 |
|  |  do gestor)      |  |                  |                 |
|  +------------------+  +------------------+                 |
|                                                             |
|  +------------------+  +------------------+                 |
|  | CandidateOptOut  |  | CandidateQuaran  |                 |
|  | (gestao de       |  | tine (protecao   |                 |
|  |  consentimento   |  |  apos rejeicao:  |                 |
|  |  e opt-out)      |  |  3 meses sem     |                 |
|  |                  |  |  contato)        |                 |
|  +------------------+  +------------------+                 |
|                                                             |
|  +----------------------------------------------+           |
|  | process_queued_messages()                     |           |
|  | -> Processamento assincrono de fila           |           |
|  | -> Retry com backoff em caso de falha         |           |
|  +----------------------------------------------+           |
+-----------------------------+------------------------------+
                              |
                              v
+------------------------------------------------------------+
| CommunicationDispatcher (baixo nivel)                       |
|                                                             |
|  - Mailgun API: mail.send()                                |
|  - From: MAILGUN_FROM_EMAIL (noreply@...)                  |
|  - Reply-To: configuravel                                   |
|  - Mock success quando Mailgun nao configurado             |
|  - Retorna message_id para tracking                         |
+------------------------------------------------------------+
```

#### Tabela de Mapeamento — Comunicação Email

| Etapa | Domínio | Serviços | Ferramentas (Tools) | Agentes | Prompts/LLM |
|-------|---------|----------|---------------------|---------|-------------|
| Detecção de intent | Orquestrador | `CascadedRouter` | — | — | Regex/LLM |
| Renderização de template | `communication` | `EmailService`, `email_templates_data.py`, `recruitment_email_templates.py` | `communication_create_template`, `communication_preview_template` | — | — (template engine) |
| Verificação de opt-out | `communication` | `CommunicationService` (CandidateOptOut) | — | — | — (determinístico, LGPD) |
| Verificação de quarentena | `communication` | `CommunicationService` (CandidateQuarantine) | — | — | — (determinístico, 3 meses) |
| Aprovação de bulk | `communication` | `CommunicationService` (PendingApproval) | `communication_send_bulk` | — | — (requires_confirmation=True) |
| Envio individual | `communication` | `EmailService`, `CommunicationDispatcher` | `communication_send_email` | Communication Agent | `communication.yaml` — personalização |
| Envio em massa | `communication` | `CommunicationService`, `CommunicationDispatcher` | `communication_send_bulk` | Communication Agent | Claude — personalização por candidato |
| Tracking | `communication` | `CommunicationService` (CommunicationLog) | `communication_get_history` | — | — (determinístico) |
| Processamento assíncrono | `communication` | `CommunicationService` (process_queued_messages) | — | — | — (fila com retry) |

**Integrações externas:** Mailgun API

---

### 2.6 Fluxo: Triagem e Scoring WSI Detalhado

Fluxo detalhado do pipeline de triagem WSI (implementado em `wsi_screening_pipeline.py`), mostrando cada bloco de avaliação, os frameworks psicométricos utilizados e como o score final é calculado.

```
Candidato entra no pipeline de triagem
      |
      v
+------------------------------------------------------------+
| PRE-QUALIFICACAO                                            |
|                                                             |
|  pre_qualification_service                                  |
|  -> Verificacao de requisitos minimos (obrigatorios)        |
|  -> Experiencia minima, formacao, idiomas                   |
|                                                             |
|  eligibility_verification_service                           |
|  -> Verificacao de elegibilidade legal                      |
|  -> Disponibilidade, pretensao salarial, localizacao        |
|                                                             |
|  Resultado: ELIGIBLE / NOT_ELIGIBLE / NEEDS_REVIEW          |
+-----------------------------+------------------------------+
                              |
                              v
+------------------------------------------------------------+
| BLOCO 2: PERGUNTAS DE TRIAGEM DA EMPRESA                   |
| (company_default_screening_questions)                       |
|                                                             |
|  - Carregadas do banco de dados da empresa (company_id)     |
|  - Perguntas padrao reutilizaveis entre vagas               |
|  - Sem intervencao de IA (perguntas pre-definidas)          |
+-----------------------------+------------------------------+
                              |
                              v
+------------------------------------------------------------+
| BLOCO 3: PERGUNTAS DE ELEGIBILIDADE WSI                     |
| (wsi_eligibility_questions)                                 |
|                                                             |
|  - Geradas pelo LLM baseadas nos requisitos da vaga        |
|  - DEDUPLICADAS contra perguntas do Bloco 2                |
|  - Focam em criterios eliminatorios                         |
|  - IA garante nao-repeticao de temas ja cobertos            |
+-----------------------------+------------------------------+
                              |
                              v
+------------------------------------------------------------+
| BLOCO 4: AVALIACAO TECNICA                                  |
| (technical_assessment)                                      |
|                                                             |
|  wsi_question_service                                       |
|  |                                                          |
|  +-> Taxonomia de Bloom (profundidade cognitiva)            |
|  |   Lembrar -> Entender -> Aplicar -> Analisar             |
|  |   -> Avaliar -> Criar                                    |
|  |   Cada resposta classificada no nivel adequado            |
|  |                                                          |
|  +-> Modelo de Dreyfus (proficiencia)                       |
|      Novice -> Advanced Beginner -> Competent               |
|      -> Proficient -> Expert                                |
|      Calibrado com anos de experiencia                      |
|                                                             |
|  Perguntas adaptativas: dificuldade ajustada com base       |
|  nas respostas anteriores do candidato                      |
+-----------------------------+------------------------------+
                              |
                              v
+------------------------------------------------------------+
| BLOCO 5: AVALIACAO COMPORTAMENTAL / SITUACIONAL             |
| (behavioral_situational)                                    |
|                                                             |
|  wsi_question_generator                                     |
|  |                                                          |
|  +-> Big Five (OCEAN) mapping                               |
|  |   Openness, Conscientiousness, Extraversion,             |
|  |   Agreeableness, Neuroticism                             |
|  |   Cada resposta mapeada para tracos                      |
|  |                                                          |
|  +-> CBI (Competency-Based Interview)                       |
|      Situacao -> Tarefa -> Acao -> Resultado (STAR)         |
|      Validacao de evidencias comportamentais                 |
|                                                             |
|  Perguntas situacionais contextualizadas para o cargo       |
+-----------------------------+------------------------------+
                              |
                              v
+------------------------------------------------------------+
| CALIBRACAO DE SENIORIDADE                                   |
|                                                             |
|  seniority_context_calibrator                               |
|  -> Calibra expectativas por nivel de senioridade           |
|                                                             |
|  seniority_resolver                                         |
|  -> Determina senioridade final (multi-signal):             |
|     - Anos de experiencia                                   |
|     - Complexidade de projetos                              |
|     - Nivel Dreyfus alcancado                               |
|     - Nivel Bloom predominante                              |
|     - Historico de lideranca                                |
|                                                             |
|  calibration_profiles                                       |
|  -> Perfis de calibracao por industria/cargo                |
+-----------------------------+------------------------------+
                              |
                              v
+------------------------------------------------------------+
| SCORING E NORMALIZACAO                                      |
|                                                             |
|  rubric_evaluation_service                                  |
|  -> BARS (Behaviorally Anchored Rating Scales)              |
|  -> Formula: Score = min(99, round(                         |
|       SUM(points_i * evidence_weight_i * multiplier_i)      |
|       / SUM(100 * multiplier_i) * 100))                     |
|  -> Evidence weights:                                       |
|     explicit = 1.0 | implicit = 0.7 | inferred = 0.3       |
|  -> Auto-exclusao: essential + missing -> score = 0         |
|  -> Cap: 99 (nenhum candidato atinge 100%)                  |
|                                                             |
|  score_normalization_service                                |
|  -> Normaliza scores entre candidatos da mesma vaga         |
|  -> Garante comparabilidade justa                           |
+-----------------------------+------------------------------+
                              |
                              v
+------------------------------------------------------------+
| CLASSIFICACAO E RECOMENDACAO                                |
|                                                             |
|  Thresholds de recomendacao:                                |
|  +--------+----------------------------+------------------+ |
|  | Score  | Classificacao              | Acao             | |
|  +--------+----------------------------+------------------+ |
|  | 85-100 | Altamente Recomendado      | Priorizar entrv  | |
|  | 70-84  | Recomendado                | Considerar proc  | |
|  | 55-69  | Potencial                  | Avaliar gaps     | |
|  | 40-54  | Baixo Match                | Arquivar futuras | |
|  |  0-39  | Nao Recomendado            | Nao prosseguir   | |
|  +--------+----------------------------+------------------+ |
|                                                             |
|  Corte dinamico: top 25% dos candidatos avancam             |
+-----------------------------+------------------------------+
                              |
                              v
+------------------------------------------------------------+
| FEEDBACK PERSONALIZADO                                      |
|                                                             |
|  personalized_feedback_service                              |
|  -> Gera feedback construtivo para cada candidato           |
|  -> Destaca pontos fortes e areas de desenvolvimento        |
|  -> Personalizado por nivel de senioridade e cargo          |
|  -> Compliance LGPD: explicabilidade da decisao             |
+------------------------------------------------------------+
```

#### Tabela de Mapeamento — Triagem e Scoring WSI

| Etapa | Domínio | Serviços | Ferramentas (Tools) | Agentes | Prompts/LLM |
|-------|---------|----------|---------------------|---------|-------------|
| Pré-qualificação | `cv_screening` | `pre_qualification_service`, `eligibility_verification_service` | `pre_qualify_candidate`, `check_eligibility` | CV Screening Agent | Claude — verificação de requisitos |
| Bloco 2: Perguntas empresa | `cv_screening` | `wsi_screening_pipeline` (company questions from DB) | `run_screening_pipeline` | — | — (banco de dados, sem IA) |
| Bloco 3: Elegibilidade WSI | `cv_screening` | `wsi_screening_pipeline`, `WSIQuestionGenerator` | `generate_wsi_questions` | CV Screening Agent | Claude — geração + deduplicação |
| Bloco 4: Avaliação técnica | `cv_screening` | `WSIQuestionService` | `classify_bloom`, `classify_dreyfus`, `generate_wsi_questions` | CV Screening Agent | Claude — classificação Bloom/Dreyfus |
| Bloco 5: Comportamental | `cv_screening` | `WSIQuestionGenerator` | `map_big_five`, `validate_cbi`, `generate_wsi_questions` | CV Screening Agent | Claude — mapeamento Big Five, validação CBI |
| Calibração de senioridade | `cv_screening` | `seniority_context_calibrator`, `seniority_resolver`, `calibration_profiles` | `assess_seniority` | CV Screening Agent | Claude — análise multi-signal |
| Scoring e normalização | `cv_screening` | `rubric_evaluation_service`, `score_normalization_service` | `evaluate_rubric`, `normalize_scores`, `calculate_wsi` | CV Screening Agent | Claude — extração de evidências |
| Classificação | `cv_screening` | `CVScoringService` | `score_cv`, `rank_candidates` | — | — (determinístico, thresholds) |
| Corte dinâmico | `cv_screening` | `CVScoringService` | `dynamic_cutoff` | — | — (determinístico, top 25%) |
| Feedback personalizado | `cv_screening` | `personalized_feedback_service` | `send_candidate_feedback` | CV Screening Agent | Claude — geração de feedback construtivo |

---

### 2.7 Fluxo: Criação de Perguntas de Triagem via Edição de Vaga

Este fluxo cobre o caso em que o recrutador edita uma vaga existente para ajustar as perguntas de triagem (screening questions). As perguntas são geradas e refinadas por IA seguindo a arquitetura de 3 camadas.

```
     RECRUTADOR                         FRONTEND                           BACKEND (IA)
         │                                  │                                  │
         │  1. Abre vaga no Kanban          │                                  │
         │─────────────────────────────────>│                                  │
         │                                  │                                  │
         │  2. Clica aba "Editar Vaga"      │                                  │
         │─────────────────────────────────>│  activeTab='edit'                │
         │                                  │                                  │
         │  3. Navega para seção             │                                  │
         │     "Perguntas de Triagem"       │                                  │
         │─────────────────────────────────>│  Exibe 3 blocos de perguntas:    │
         │                                  │  - Derivadas da JD [AI]          │
         │                                  │  - Banco da empresa [DET]        │
         │                                  │  - Personalizadas [user]         │
         │                                  │                                  │
         │  4a. Pede para LIA refinar       │                                  │
         │      perguntas via chat          │                                  │
         │─────────────────────────────────>│─────────────────────────────────>│
         │                                  │  callOrchestratedJobChat()       │
         │                                  │  → Orchestrator → CV Screening   │
         │                                  │                                  │
         │                                  │  [AI] WSIQuestionGenerator:      │
         │                                  │  - Analisa JD + skills           │
         │                                  │  - Gera perguntas Bloom-mapped   │
         │                                  │  - Calibra por senioridade       │
         │                                  │  - Mapeia Big Five               │
         │                                  │<─────────────────────────────────│
         │                                  │                                  │
         │  4b. OU usa QuestionAdjustment   │                                  │
         │      Chat (inline)               │                                  │
         │─────────────────────────────────>│  QuestionAdjustmentChat:         │
         │  "torne mais técnica"            │  → Envia pergunta + pedido       │
         │  "adicione cenário prático"      │─────────────────────────────────>│
         │                                  │  [AI] Refina pergunta mantendo   │
         │                                  │  mapeamento WSI intacto          │
         │                                  │<─────────────────────────────────│
         │                                  │  QuestionDiffView: mostra antes/ │
         │  5. Revisa diff e aprova         │  depois da alteração             │
         │─────────────────────────────────>│                                  │
         │                                  │                                  │
         │  6. Salva alterações             │                                  │
         │─────────────────────────────────>│  PUT /api/jobs/{id}/screening    │
         │                                  │  AdjustmentCounter: conta edições│
         │                                  │                                  │
```

**Mapeamento Técnico:**

| Etapa | Domínio | Serviço/Componente | IA? |
|-------|---------|--------------------|-----|
| Perguntas derivadas da JD | `cv_screening` | `WSIQuestionGenerator` → `generate_wsi_questions()` | ✅ Claude — Bloom taxonomy mapping |
| Perguntas banco empresa | `cv_screening` | `ScreeningQuestionSetService` → `CompanyScreeningQuestion` model | ❌ Determinístico (DB query) |
| Perguntas customizadas | — | Frontend state | ❌ Input manual |
| Refinamento via chat | `cv_screening` | `QuestionAdjustmentChat` → LLM | ✅ Claude — rewrite com WSI constraints |
| Diff view | — | `QuestionDiffView` component | ❌ Frontend diff |
| Calibração senioridade | `cv_screening` | `seniority_context_calibrator` | ✅ Claude — ajusta complexidade |
| JD Evaluation | `job_management` | `JDEvaluationPanel` → `jd_enrichment_service` | ✅ Claude — avalia qualidade da JD |

---

### 2.8 Fluxo: Inscrição de Candidato via WhatsApp

Este fluxo cobre a jornada do candidato que recebe um convite de triagem via WhatsApp e interage com a LIA para se inscrever/participar do processo seletivo.

```
     CANDIDATO                    WHATSAPP (Twilio)                    BACKEND (LIA)
         │                              │                                  │
         │  1. Recebe mensagem           │                                  │
         │     template de convite       │                                  │
         │<─────────────────────────────│<─────────────────────────────────│
         │                              │  WSITriagemInviteModal →          │
         │                              │  CommunicationDispatcher.         │
         │                              │  send_whatsapp(template_sid)      │
         │                              │                                  │
         │  2. Responde "Quero            │                                  │
         │     participar"               │                                  │
         │─────────────────────────────>│─────────────────────────────────>│
         │                              │  Webhook Twilio → API endpoint    │
         │                              │                                  │
         │                              │  [AI] PreQualificationService:   │
         │                              │  - Analisa CV existente (se há)   │
         │                              │  - Calcula adherence_score        │
         │                              │  - Determina: ALIGNED | PARTIAL  │
         │                              │    | DISTANT | VERY_DISTANT       │
         │                              │                                  │
         │  3. Recebe pre-qualificação   │                                  │
         │     (mensagem humanizada,     │<─────────────────────────────────│
         │      sem percentuais)         │  Mensagem: "Analisei seu CV..."  │
         │<─────────────────────────────│  + botões: [Continuar] [Encerrar]│
         │                              │                                  │
         │  4a. SE "Continuar":          │                                  │
         │─────────────────────────────>│─────────────────────────────────>│
         │                              │  [AI] LGPD Consent Check          │
         │                              │  → Envia termos de privacidade    │
         │  4b. Aceita termos LGPD       │                                  │
         │─────────────────────────────>│─────────────────────────────────>│
         │                              │  communication_consent = true     │
         │                              │                                  │
         │  5. Triagem WSI inicia        │                                  │
         │     (fluxo conversacional     │                                  │
         │      via WhatsApp ou Voice)   │<─────────────────────────────────│
         │<─────────────────────────────│  WSIScreeningPipeline.execute()  │
         │                              │                                  │
         │  6. Respostas do candidato    │                                  │
         │─────────────────────────────>│─────────────────────────────────>│
         │                              │  [AI] Avaliação bloco-a-bloco    │
         │                              │  [AI] Follow-up questions        │
         │                              │  [AI] Score WSI progressivo      │
         │                              │                                  │
         │  7. Feedback final            │                                  │
         │<─────────────────────────────│<─────────────────────────────────│
         │  "Obrigada por participar!    │  [AI] generate_candidate_feedback│
         │   Entraremos em contato."     │  PersonalizedFeedbackService     │
         │                              │                                  │
         │                              │  8. Notifica recrutador           │
         │                              │─────────────────────────────────>│
         │                              │  [AI] Relatório do candidato      │
         │                              │  → Pipeline atualizado            │
         │                              │  → Scorecard WSI disponível       │
```

**Mapeamento Técnico:**

| Etapa | Domínio | Serviço | IA? |
|-------|---------|---------|-----|
| Convite WhatsApp | `communication` | `CommunicationDispatcher.send_whatsapp()` via Twilio | ❌ Template pré-aprovado |
| Pre-qualificação | `cv_screening` | `PreQualificationService.evaluate()` | ✅ `RubricEvaluationService` + LLM |
| Mensagem humanizada | `cv_screening` | `PRE_QUALIFICATION_TEMPLATES` | ❌ Templates com variáveis |
| LGPD consent | `communication` | `communication_consent` flag | ❌ Determinístico |
| Triagem WSI | `cv_screening` | `WSIScreeningPipeline` → `WSIQuestionGenerator` | ✅ Claude — 7 blocos |
| Follow-up questions | `cv_screening` | `wsi_question_generator.generate_follow_up()` | ✅ Claude — contextual |
| Feedback ao candidato | `cv_screening` | `wsi_service.generate_candidate_feedback()` | ✅ Claude — construtivo |
| Relatório ao recrutador | `cv_screening` | `ScreeningAgent._handle_generate_report()` | ✅ Claude — parecer |

**Thresholds de Pre-Qualificação (configuráveis por vaga):**

| Resultado | Score | Comportamento | Botões |
|-----------|-------|---------------|--------|
| `ALIGNED` | ≥ 70% | Auto-avança para triagem | Nenhum |
| `PARTIAL` | 50-69% | Pergunta se quer continuar | [Sim] [Não] |
| `DISTANT` | 30-49% | Aviso honesto de baixa chance | [Continuar] [Banco Talentos] [Encerrar] |
| `VERY_DISTANT` | < 30% | Recomenda alternativas | [Banco Talentos] [Continuar] [Encerrar] |

---

### 2.9 Fluxo: Pedido de Ajuda do Recrutador Quando IA Falha

Este fluxo cobre o caso em que o recrutador encontra um problema com a IA (resposta incorreta, erro, comportamento inesperado) e precisa de suporte.

```
     RECRUTADOR                       FRONTEND                           BACKEND
         │                                │                                  │
         │  1. IA dá resposta estranha    │                                  │
         │     ou erro no chat LIA        │                                  │
         │                                │                                  │
         │  CAMINHO A: Feedback inline    │                                  │
         │  2a. Clica 👎 na resposta      │                                  │
         │─────────────────────────────> │                                  │
         │                                │  LIAFeedbackWidget:              │
         │  3a. Seleciona motivo:         │  - "Resposta incorreta"          │
         │      + comentário opcional     │  - "Não entendeu minha pergunta" │
         │─────────────────────────────> │  - "Informação desatualizada"    │
         │                                │  - "Outro"                       │
         │                                │                                  │
         │                                │  POST /api/feedback              │
         │                                │─────────────────────────────────>│
         │                                │  → FeedbackLoopService           │
         │                                │  → LearningPattern model         │
         │                                │  → Calibration adjustment         │
         │                                │                                  │
         │  CAMINHO B: Chat retry         │                                  │
         │  2b. Reformula pergunta        │                                  │
         │      no chat                   │                                  │
         │─────────────────────────────> │─────────────────────────────────>│
         │  "Não era isso que pedi.       │  Orchestrator detecta:            │
         │   Quero X em vez de Y"         │  - intent: CORRECTION             │
         │                                │  - ConversationMemory mantém      │
         │                                │    contexto anterior               │
         │                                │  - Re-processa com contexto       │
         │                                │<─────────────────────────────────│
         │  Resposta corrigida            │                                  │
         │<───────────────────────────── │                                  │
         │                                │                                  │
         │  CAMINHO C: Escalar problema   │                                  │
         │  2c. Acessa /ajuda             │                                  │
         │─────────────────────────────> │  Página de ajuda:                │
         │                                │  - FAQ com respostas comuns       │
         │  3c. Abre ticket de suporte    │  - Chat com suporte humano       │
         │─────────────────────────────> │  - Link para documentação        │
         │                                │                                  │
         │  CAMINHO D: Calibração         │                                  │
         │  2d. LIA oferece calibrar      │                                  │
         │  "Entendi. Posso ajustar       │                                  │
         │   minhas respostas. O que      │                                  │
         │   estava errado?" [AI]         │                                  │
         │─────────────────────────────> │─────────────────────────────────>│
         │  "O score deveria ser mais     │  RubricEvaluationService:        │
         │   alto porque ele tem 5 anos   │  calibration_feedback()          │
         │   em Python, não 2"            │  → Ajusta peso/evidência         │
         │                                │  → Re-calcula score              │
         │                                │<─────────────────────────────────│
         │  Score atualizado              │                                  │
         │<───────────────────────────── │                                  │
```

**Mapeamento Técnico:**

| Caminho | Domínio | Serviço | IA? |
|---------|---------|---------|-----|
| Feedback 👎 | `recruiter_assistant` | `LIAFeedbackWidget` → `FeedbackLoopService` → `LearningPattern` | ❌ Registro + ✅ Calibração posterior |
| Chat retry/correção | Detectado pelo Orchestrator | `ConversationMemory` + `ReferenceResolver` | ✅ Claude — re-processamento |
| Escalar suporte | — | Página `/ajuda` | ❌ Determinístico |
| Calibração de score | `cv_screening` | `RubricEvaluationService.calibration_feedback()` | ✅ Re-avaliação com novo contexto |

---

### 2.10 Comportamento Completo da IA na Triagem (Screening)

> **Objetivo desta seção:** Documentar com precisão o comportamento da LIA durante a triagem de candidatos — o que ela pode e não pode dizer, como apresenta a vaga, como coleta consentimento LGPD, como interage, quais limites observa, como gera feedback, como cria o relatório, e como notifica o recrutador. Esta seção é crítica para auditoria de compliance (LGPD, EU AI Act) e para validação das regras de interação.

#### 2.10.1 Etapa 0: Consentimento LGPD (Obrigatório Antes de Qualquer Interação)

Antes de iniciar qualquer coleta de dados do candidato, a LIA DEVE obter consentimento explícito.

**Fluxo de consentimento:**

```
LIA → Candidato:
  "Antes de começarmos, preciso informar que vamos coletar e processar
   seus dados pessoais para fins de avaliação neste processo seletivo.
   
   Seus dados serão tratados conforme a Lei Geral de Proteção de Dados
   (LGPD) e nossa Política de Privacidade.
   
   Você autoriza o tratamento dos seus dados para este processo?"
   
   [Sim, autorizo] [Não, obrigado]
```

**Regras de implementação:**
- Flag: `communication_consent` no modelo do candidato
- Se `require_consent_before_contact=True` (config da empresa), bloqueio total sem consentimento
- Consentimento registrado com timestamp e IP (auditoria LGPD)
- Dados sensíveis (pretensão salarial, motivo de saída) requerem consentimento adicional do recrutador antes de perguntar ao candidato
- Config empresarial: `require_consent_before_contact` (em `/api/communication-settings`)
- Módulo LGPD: `/api/lgpd/*` (stats, breach notifications, human review)

**O que a LIA NÃO pode fazer sem consentimento:**
- Coletar qualquer dado pessoal
- Enviar perguntas de triagem
- Analisar CV submetido
- Registrar informações no perfil

#### 2.10.2 Etapa 1: Apresentação da Vaga ao Candidato

Após consentimento, a LIA apresenta a vaga de forma contextualizada.

**Formato da apresentação:**

```
LIA → Candidato:
  "Analisei seu currículo para a vaga de {job_title} na {company_name}.
   
   [SE ALIGNED]: Seu perfil está bem alinhado com o que buscamos!
   Vamos iniciar algumas perguntas para conhecer melhor sua experiência.
   
   [SE PARTIAL]: Notei que você tem experiência em {matched_skills}.
   Porém, a vaga também pede {missing_requirements}.
   Isso não significa que você não possa participar!
   Quer continuar com a triagem?
   
   [SE DISTANT]: Quero ser transparente: percebi que sua experiência
   não está muito alinhada com o que essa vaga exige.
   Você pode continuar se quiser, mas as chances são menores.
   
   [SE VERY_DISTANT]: Preciso ser sincera: não encontrei no seu
   currículo nenhuma das experiências que a vaga exige.
   Não quero que você perca tempo."
```

**Regras da apresentação (implementadas em `PRE_QUALIFICATION_TEMPLATES`):**
- NUNCA mostrar percentuais ou scores numéricos ao candidato
- SEMPRE usar linguagem humanizada e empática
- Ser transparente sobre gaps sem ser cruel
- Oferecer alternativas (banco de talentos, outras vagas)
- Respeitar a decisão do candidato de continuar mesmo com gaps

#### 2.10.3 Regras de Interação e Limites da IA

**O que a LIA PODE dizer/fazer durante a triagem:**

| Categoria | Permitido | Exemplo |
|-----------|-----------|---------|
| Apresentar a vaga | ✅ | "A vaga é para Desenvolvedor Backend na empresa X" |
| Perguntar sobre experiência técnica | ✅ | "Conte sobre sua experiência com Python" |
| Perguntar sobre competências comportamentais | ✅ | "Descreva uma situação em que liderou um projeto" |
| Pedir exemplos concretos (CBI) | ✅ | "Pode dar um exemplo específico de como resolveu isso?" |
| Follow-up contextual | ✅ | "Você mencionou AWS — trabalhou com quais serviços?" |
| Confirmar dados do CV | ✅ | "Os dados do seu currículo estão corretos?" |
| Informar próximos passos | ✅ | "Vou enviar suas informações para análise da equipe" |
| Dar feedback construtivo genérico | ✅ | "Obrigada por participar! Entraremos em contato" |

**O que a LIA NÃO PODE dizer/fazer:**

| Categoria | Proibido | Motivo |
|-----------|----------|--------|
| Revelar score numérico ao candidato | ❌ | Scores são internos para o recrutador |
| Comparar com outros candidatos | ❌ | Violação de privacidade |
| Prometer resultado do processo | ❌ | Decisão é do recrutador |
| Opinar sobre salário do mercado ao candidato | ❌ | Pode influenciar negociação |
| Perguntar sobre idade, estado civil, filhos | ❌ | Critérios proibidos (viés) — `ethical_guidelines` |
| Penalizar gaps no currículo | ❌ | Diretriz ética explícita |
| Usar nome para inferir gênero/etnia | ❌ | Critério proibido |
| Considerar instituição de ensino específica | ❌ | Apenas nível educacional importa |
| Coletar dados sem consentimento LGPD | ❌ | Violação legal |
| Enviar dados sensíveis sem autorização do recrutador | ❌ | `data_persistence_guidelines` |
| Usar linguagem informal/gírias | ❌ | `lia_persona` — formal mas acessível |
| Emojis excessivos | ❌ | Máximo 1-2 quando apropriado |

#### 2.10.4 Persona e Tom de Comunicação

Definido em `app/prompts/shared/lia_persona.yaml`:

| Atributo | Valor |
|----------|-------|
| Nome | LIA (Learning Intelligence Assistant) |
| Tom | Profissional, empático, direto e proativo |
| Linguagem | Formal mas acessível, sem gírias ou abreviações |
| Tratamento | Sempre "você", nunca "vc" ou "tu" |
| Gênero | Linguagem neutra — "a pessoa candidata" ou "o candidato/a candidata" |
| Idioma | Português brasileiro (termos técnicos HR em PT-BR) |
| Proibido | "blz", "tmj", "pra", "vc", "tb", "msm" |
| Emojis | Máximo 1-2, apenas quando contextualizados |

#### 2.10.5 Geração de Feedback para o Candidato

Ao final da triagem, a LIA gera feedback construtivo personalizado.

**Serviço:** `wsi_service.generate_candidate_feedback()` (linha 434 de `wsi_service.py`)

**Regras do feedback:**
- SEMPRE construtivo — nunca destrutivo ou desanimador
- NÃO revelar scores, rankings ou posição relativa
- Agradecer genuinamente pela participação
- Informar prazo estimado de retorno (se configurado)
- NÃO prometer resultado específico
- Linguagem empática e respeitosa

**Estrutura do feedback ao candidato:**

```
LIA → Candidato:
  "Obrigada por participar da triagem para a vaga de {job_title}!
   
   Sua experiência em {top_skills} foi muito relevante para
   nossa avaliação.
   
   {SE há gaps}: Notamos que {gap_area} é uma área que pode
   ser desenvolvida — isso não é um ponto negativo, apenas
   uma observação para seu crescimento profissional.
   
   Próximos passos: A equipe de recrutamento vai analisar
   todas as informações e entrar em contato em até {prazo} dias.
   
   Boa sorte!"
```

#### 2.10.6 Geração do Relatório do Candidato (Parecer)

Após a triagem, a LIA gera um relatório estruturado para o recrutador.

**Serviço:** `ScreeningAgent._handle_generate_report()` → `AvaliadorWSIAgent.generate_parecer()`

**Estrutura do relatório (parecer):**

```
┌─────────────────────────────────────────────────────┐
│  PARECER DO CANDIDATO                               │
│  Candidato: {nome} | Vaga: {titulo}                 │
│  Data: {data} | Gerado por: LIA (ScreeningAgent)    │
├─────────────────────────────────────────────────────┤
│                                                      │
│  WSI SCORECARD                                       │
│  ├── B1 Hard Skills:      82/100  ████████░░        │
│  ├── B2 Soft Skills:      90/100  █████████░        │
│  ├── B3 Experiência:      80/100  ████████░░        │
│  ├── B4 Cultural Fit:     88/100  █████████░        │
│  ├── B5 Motivação:        85/100  ████████░░        │
│  ├── B6 Potencial:        92/100  █████████░        │
│  └── B7 Risco:            20/100  ██░░░░░░░░        │
│  SCORE GLOBAL: 85/100                                │
│                                                      │
│  EVIDÊNCIAS (citações da triagem)                    │
│  - "Trabalhou 3 anos com Python em produção" → B1   │
│  - "Liderou migração de monolito" → B3, B5          │
│  - "Mencionou cultura de feedback" → B4              │
│                                                      │
│  PONTOS FORTES                                       │
│  - Perfil técnico sólido em backend                  │
│  - Experiência com equipes distribuídas              │
│  - Motivação clara para a posição                    │
│                                                      │
│  PONTOS DE ATENÇÃO                                   │
│  - Sem experiência com Go (requisito desejável)      │
│  - Primeira experiência como tech lead                │
│                                                      │
│  RECOMENDAÇÃO                                        │
│  Avançar para entrevista técnica com foco em:        │
│  - Capacidade de liderança técnica                   │
│  - Experiência com microservices em Go               │
│                                                      │
│  SENIORIDADE CALIBRADA: Sênior (multi-signal)        │
│  - CV: Sênior | Triagem: Sênior | Big Five: Pleno+   │
│  - Resolução: Sênior (2/3 signals concordam)         │
│                                                      │
│  COMPLIANCE                                          │
│  - FairnessGuard: ✅ Sem viés detectado              │
│  - FactChecker: ✅ Evidências verificadas            │
│  - LGPD: ✅ Consentimento registrado                 │
└─────────────────────────────────────────────────────┘
```

**Regras do relatório:**
- Scores numéricos APENAS para o recrutador (nunca para o candidato)
- Cada score DEVE ter evidência citada da triagem
- Recomendação DEVE ser acionável (o que perguntar na próxima etapa)
- Senioridade usa resolução multi-signal (CV + Triagem + Big Five)
- FairnessGuard verifica viés em cada avaliação
- FactChecker valida que evidências são reais (não fabricadas)

#### 2.10.7 Notificação ao Recrutador e Entrega do Resultado

```
     BACKEND (LIA)                    FRONTEND                          RECRUTADOR
         │                                │                                  │
         │  1. Triagem completa           │                                  │
         │  → Scorecard WSI gerado        │                                  │
         │  → Parecer gerado              │                                  │
         │                                │                                  │
         │  2. Atualiza pipeline          │                                  │
         │  → Candidato move para         │                                  │
         │    próxima etapa (ou rejeição) │                                  │
         │─────────────────────────────> │                                  │
         │                                │  3. Notificação in-app           │
         │                                │  IntelligenceNotifications:      │
         │                                │  "Triagem de Ana Costa concluída │
         │                                │   Score WSI: 85 — Recomendação:  │
         │                                │   Avançar para entrevista"       │
         │                                │─────────────────────────────────>│
         │                                │                                  │
         │  4. Email/WhatsApp ao          │                                  │
         │     recrutador (se config)     │                                  │
         │─────────────────────────────> │                                  │
         │  CommunicationDispatcher       │                                  │
         │                                │                                  │
         │  5. Dados persistidos:         │                                  │
         │  - WedoTalent: perfil completo │                                  │
         │  - ATS cliente: status sync    │                                  │
         │  - Audit log: todas as ações   │                                  │
         │  - Learning Loop: padrão       │                                  │
```

**Dados persistidos após triagem:**

| Dado | Destino | Sincronização ATS |
|------|---------|-------------------|
| Status do candidato | WedoTalent + ATS | Imediatamente |
| Score WSI (7 blocos) | WedoTalent + ATS (se suportado) | Após avaliação |
| Parecer/Notas | WedoTalent + ATS (se suportado) | Após geração |
| Pretensão salarial | WedoTalent apenas | NÃO sync (dado sensível) |
| Disponibilidade | WedoTalent + ATS | Após confirmação |
| Skills validadas | WedoTalent | Batch semanal |
| Histórico de entrevistas | WedoTalent | NÃO sync |
| Consentimento LGPD | WedoTalent | NÃO sync |

**Regras de sincronização com ATS:**
- Sincronizar APENAS campos que existem no ATS do cliente
- Se campo não existe no ATS → armazenar no WedoTalent como dado complementar
- Registrar log de auditoria para cada sincronização
- Pretensão salarial NUNCA é sincronizada (dado sensível LGPD)

---

## 3. Visão Geral da Arquitetura

### 3.1 Padrão Arquitetural: Domain-Driven Agent Architecture v2.2

A plataforma migrou de um modelo agent-first para um modelo **domain-first**, onde:

- **Domínios** são contratos que definem capacidades, ações e limites de escopo
- **Agentes** são unidades de execução especializadas dentro de domínios
- **Orquestrador** é o hub central que roteia intenções e coordena execução multi-domínio

### 3.2 Diagrama Completo da Arquitetura (11 Domínios)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         USUARIOS                                            │
│                                                                             │
│   Recrutador (Chat)    Candidato (WhatsApp)    Gestor (Teams/Email)         │
└──────────┬──────────────────┬──────────────────────┬───────────────────────┘
           │                  │                      │
           v                  v                      v
┌─────────────────────────────────────────────────────────────────────────────┐
│                     ORQUESTRADOR CENTRAL (LIA)                              │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Cascaded   │  │    State     │  │   Policy     │  │    Task      │    │
│  │   Router     │  │   Manager    │  │   Engine     │  │   Planner    │    │
│  │  (Memory ->  │  │  (sessao +   │  │  (limites +  │  │  (multi-step │    │
│  │  Regex ->    │  │   contexto)  │  │   RBAC)      │  │   execution) │    │
│  │  LLM)        │  │              │  │              │  │              │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                             │
│  ┌──────────────┐                                                           │
│  │ Plan Executor│  Execucao paralela, retry, injecao de contexto           │
│  └──────────────┘                                                           │
└──────────┬──────────────────────────────────────────────────────────────────┘
           │
           │  Roteamento por domain_id (confidence >= threshold)
           │
     ┌─────┴─────┬─────────┬─────────┬─────────┬──────────┐
     │           │         │         │         │          │
     v           v         v         v         v          v
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ 1.SOURC │ │ 2.JOB   │ │ 3.CV    │ │ 4.COMMU │ │ 5.INTER │
│ ING     │ │ MANAGE  │ │ SCREEN  │ │ NICATIO │ │ VIEW &  │
│         │ │ MENT    │ │ ING     │ │ N       │ │ SCHEDUL │
│ 30 act  │ │ 29 act  │ │ 25 act  │ │ 20 act  │ │ 20 act  │
│ 19 tools│ │ 13 tools│ │ 12 tools│ │ 10 tools│ │ 10 tools│
│         │ │         │ │         │ │         │ │         │
│ Pearch  │ │ Wizard  │ │ WSI     │ │ Email   │ │ Calendar│
│ WRF     │ │ JD Gen  │ │ Bloom   │ │ WhatsApp│ │ Deepgram│
│ Embedds │ │ Insights│ │ Dreyfus │ │ Teams   │ │ Voz     │
└─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
     │           │         │         │         │
     v           v         v         v         v
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ 6.ANALY │ │ 7.ATS   │ │ 8.AUTO  │ │ 9.RECRU │ │10.PIPEL │ │11.HIRIN │
│ TICS    │ │ INTEGR  │ │ MATION  │ │ ITER    │ │ INE     │ │ G_POLIC │
│         │ │ ATION   │ │         │ │ ASSIST  │ │ TRANSIT │ │ Y       │
│ 18 act  │ │ 18 act  │ │ 20 act  │ │ 20 act  │ │  5 act  │ │ 14 act  │
│ 10 tools│ │ 10 tools│ │ 10 tools│ │ 10 tools│ │  5 tools│ │ 14 tools│
│         │ │         │ │         │ │         │ │         │ │         │
│ KPIs    │ │ Merge   │ │ Stage   │ │ Kanban  │ │ Move    │ │ Policy  │
│ Predict │ │ Gupy    │ │ Engine  │ │ Memory  │ │ Context │ │ ReAct   │
│ Funnel  │ │ Pandape │ │ Alerts  │ │ Briefing│ │ Predict │ │ Fairness│
└─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
           │                                       │           │
     ┌─────┴───────────────────────────────────────┴───────────┴──┐
     │                                                     │
     v                                                     v
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CAMADAS TRANSVERSAIS (SHARED)                             │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        COMPLIANCE                                    │   │
│  │  FairnessGuard    FactChecker    AuditService    LGPD API           │   │
│  │  (anti-bias)      (veracidade)   (explainability) (portal titular)  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        GOVERNANCA                                    │   │
│  │  AgentMonitoring   FeatureFlags   PolicyEngine    ToolRegistry      │   │
│  │  (health score)    (rollout)      (regras)        (RBAC tools)      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     SERVICOS COMPARTILHADOS                          │   │
│  │  LLMService    EmbeddingService   BillingService   OrgCatalog       │   │
│  │  (multi-LLM)   (vetores)          (assinaturas)    (areas/cargos)   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
           │
           v
┌─────────────────────────────────────────────────────────────────────────────┐
│                      INTEGRACOES EXTERNAS                                    │
│                                                                             │
│  IA: Anthropic (Claude) | OpenAI (GPT-4) | Google (Gemini)                 │
│  Comunicacao: Mailgun | Twilio | Microsoft Graph | Deepgram               │
│  Sourcing: Pearch AI | OpenMic.ai                                          │
│  ATS: Merge.dev | Gupy | Pandape                                           │
│  Negocio: WorkOS (auth) | Stripe (pagamentos) | HubSpot (CRM)             │
└─────────────────────────────────────────────────────────────────────────────┘

TOTAIS: 11 dominios | 219 actions | 89 ReAct tools + legacy tools | 137 services | 3 LLM providers
```

### 3.3 Organização de Código

```
lia-agent-system/
├── app/
│   ├── orchestrator/          # Orquestração central
│   │   ├── orchestrator.py    # Hub principal
│   │   ├── cascaded_router.py # Roteamento em cascata
│   │   ├── intent_router.py   # Classificação LLM de intenções
│   │   ├── state_manager.py   # Gerenciamento de estado
│   │   └── task_planner.py    # Decomposição de tarefas complexas
│   ├── domains/               # 11 domínios de negócio
│   │   ├── base.py            # Contrato ABC (DomainPrompt)
│   │   ├── registry.py        # Registro de domínios
│   │   ├── sourcing/          # Domínio: Sourcing
│   │   ├── job_management/    # Domínio: Gestão de Vagas
│   │   ├── cv_screening/      # Domínio: Triagem de CVs
│   │   ├── communication/     # Domínio: Comunicação
│   │   ├── interview_scheduling/ # Domínio: Entrevistas
│   │   ├── analytics/         # Domínio: Analytics
│   │   ├── ats_integration/   # Domínio: Integração ATS
│   │   ├── automation/        # Domínio: Automação
│   │   ├── recruiter_assistant/ # Domínio: Assistente
│   │   ├── pipeline/          # Domínio: Pipeline Transition (DOMAIN_NAME: "pipeline_transition")
│   │   └── hiring_policy/     # Domínio: Políticas de Contratação (PolicyReActAgent)
│   ├── shared/                # Infraestrutura cross-domain
│   │   ├── agents/            # BaseAgent, ReActLoop, WorkingMemory, LongTermMemory, Observability
│   │   ├── compliance/        # FairnessGuard, AuditService, FactChecker
│   │   ├── governance/        # Monitoramento, Feature Flags
│   │   ├── channels/          # MultiChannel (5 adapters: email, whatsapp, sms, in-app, teams)
│   │   └── async_processing/  # TaskManager, EnhancedTaskManager, TaskScheduler, DLQ
│   ├── services/              # Serviços compartilhados
│   ├── prompts/               # Templates de prompts (YAML)
│   ├── tools/                 # Registry de ferramentas
│   ├── api/v1/                # Endpoints REST
│   ├── config/                # Configurações e regras
│   └── models/                # Modelos de dados
```

### 3.4 Contrato Base de Domínio

Cada domínio implementa a classe abstrata `DomainPrompt`:

```python
class DomainPrompt(ABC):
    domain_id: str          # Identificador único
    domain_name: str        # Nome legível

    def get_allowed_actions(self) -> List[DomainAction]   # Ações permitidas
    def get_system_prompt(self) -> str                     # Prompt do domínio
    async def process_intent(self, query, context) -> IntentResult  # Classificação
    async def execute_action(self, action_id, params, context) -> DomainResponse  # Execução
```

Cada `DomainAction` define:
```python
class DomainAction:
    action_id: str              # Ex: "parse_cv"
    name: str                   # Ex: "Analisar CV"
    description: str            # Descrição para o LLM
    required_params: List[str]  # Parâmetros obrigatórios
    optional_params: List[str]  # Parâmetros opcionais
    requires_confirmation: bool # Requer confirmação humana
    tags: List[str]             # Tags de categorização
    is_async: bool              # Execução assíncrona
```

---

### 3.5 Tech Stack — Diagrama em Camadas

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CAMADA DE APRESENTAÇÃO                             │
│                                                                             │
│  Next.js 14 + React 18 + TypeScript 5.x                                   │
│  Radix UI / shadcn/ui / Tailwind CSS 3.x                                  │
│  WebSocket (chat streaming)                                                │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │ HTTPS / WebSocket
                                v
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CAMADA DE API                                       │
│                                                                             │
│  FastAPI 0.115.5 (Python 3.11)                                             │
│  Uvicorn 0.32.1 (ASGI server)                                              │
│  Pydantic 2.10.3 (validação)                                               │
│                                                                             │
│  Endpoints:                                                                │
│  /api/v1/lia-assistant    → Chat conversacional                            │
│  /api/v1/job-vacancies    → CRUD de vagas                                  │
│  /api/v1/candidates       → Busca e gestão                                 │
│  /api/v1/ai-consumption   → Tracking de uso de IA                          │
│  /api/v1/screening        → Triagem WSI                                    │
│  /api/v1/communications   → Email/WhatsApp/Teams                           │
│  /api/v1/scheduling       → Agendamento                                    │
│  /api/v1/billing          → Assinaturas                                    │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                  │
              v                 v                  v
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────────────────────┐
│  ORQUESTRAÇÃO    │ │  PROCESSAMENTO   │ │     MENSAGERIA E FILAS           │
│                  │ │  ASSINCRONO      │ │                                  │
│  LangChain 0.3.9 │ │  DomainTask     │ │  RabbitMQ 3.x (AMQP broker)     │
│  LangGraph 0.2.53│ │  Manager        │ │  Celery 5.4.0 (workers)          │
│  LangSmith 0.2.5 │ │  AsyncTask      │ │  aio-pika 9.5.3 (async AMQP)    │
│                  │ │  Queue           │ │                                  │
│  Providers:      │ │                  │ │  Filas:                          │
│  langchain-      │ │  9 dominios c/   │ │  - bulk_screening               │
│   anthropic      │ │  actions async:  │ │  - mass_communication           │
│   0.3.22         │ │  bulk_search,    │ │  - ats_sync                     │
│  langchain-      │ │  mass_outreach,  │ │  - report_generation            │
│   openai 0.2.9   │ │  batch_evaluate, │ │  - scheduled_tasks              │
│  langchain-      │ │  mass_email,     │ │                                  │
│   google-vertex  │ │  bulk_sync, etc  │ │  Config:                        │
│   ai 2.0.8       │ │                  │ │  amqp://guest:guest@rabbitmq:   │
│                  │ │  Max 3 paralelos │ │  5672/                           │
│                  │ │  por domínio     │ │  Management UI: :15672           │
└────────┬─────────┘ └────────┬─────────┘ └──────────────┬───────────────────┘
         │                    │                           │
         v                    v                           v
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CAMADA DE DADOS E CACHE                                 │
│                                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌──────────────────┐   │
│  │ PostgreSQL + pgvector│  │ Redis 5.2.0         │  │ Elasticsearch    │   │
│  │                     │  │                     │  │ (Talent Funnel)  │   │
│  │ SQLAlchemy 2.0.36   │  │ Cache 3 camadas:    │  │                  │   │
│  │ Alembic 1.14.0      │  │ L1: Sessão (memory) │  │ Busca semântica  │   │
│  │ asyncpg 0.30.0      │  │ L2: Redis (7 dias)  │  │ + WRF ranking    │   │
│  │ pgvector 0.3.6      │  │ L3: PostgreSQL (30d)│  │                  │   │
│  │                     │  │                     │  │ Pre-WRF Filter   │   │
│  │ Tabelas principais: │  │ Namespaces:         │  │ PGV Gap Analyzer │   │
│  │ - ai_consumption    │  │ - salary_benchmark  │  │ ES Score Drop    │   │
│  │ - ai_credits_balance│  │ - market_data       │  │  Analyzer        │   │
│  │ - conversation_     │  │ - skills_suggestions│  │                  │   │
│  │   memories (vector) │  │ - jd_summary        │  │ Scoring:         │   │
│  │ - knowledge_base    │  │ - company_config    │  │ Candidate Score  │   │
│  │   (vector)          │  │ - learning_patterns │  │ = WRF weighted   │   │
│  │ - interaction_      │  │ - llm_response      │  │   skills + exper │   │
│  │   feedback          │  │ - embeddings        │  │   + semantic     │   │
│  │ - learning_patterns │  │                     │  │   similarity     │   │
│  │ - subscriptions     │  │ TTLs por intent:    │  │                  │   │
│  │ - invoices          │  │ pipeline_stats: 60s │  │                  │   │
│  │                     │  │ candidate_search:   │  │                  │   │
│  │ Embeddings:         │  │  120s               │  │                  │   │
│  │ Vector(768) =       │  │ salary_benchmark:   │  │                  │   │
│  │ text-embedding-004  │  │  600s               │  │                  │   │
│  │ (Google)            │  │ analytics: 90s      │  │                  │   │
│  └─────────────────────┘  └─────────────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                │
                                v
┌─────────────────────────────────────────────────────────────────────────────┐
│                     PROVEDORES EXTERNOS DE IA                               │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────────────────┐  │
│  │ Anthropic        │  │ Google           │  │ OpenAI                    │  │
│  │ Claude Sonnet    │  │ Gemini Pro/Flash │  │ GPT-4 / GPT-4 Turbo      │  │
│  │ Claude Haiku     │  │                  │  │                           │  │
│  │                  │  │ Usos:            │  │ Usos:                     │  │
│  │ Uso principal:   │  │ - Semantic search│  │ - Fallback                │  │
│  │ - Orquestração   │  │ - Embeddings     │  │ - Comparação cross-model  │  │
│  │ - Job Wizard     │  │   (768 dim)      │  │                           │  │
│  │ - WSI Screening  │  │ - Expansão de    │  │                           │  │
│  │ - Análise de CV  │  │   skills         │  │                           │  │
│  │ - Geração de JD  │  │                  │  │                           │  │
│  └─────────────────┘  └─────────────────┘  └───────────────────────────┘  │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────────────────┐  │
│  │ Deepgram         │  │ Pearch AI        │  │ Microsoft Graph           │  │
│  │ Nova-2           │  │ Sourcing global  │  │ Calendar, Mail, Teams     │  │
│  │ Transcrição voz  │  │ de candidatos    │  │ Bot Framework SDK         │  │
│  └─────────────────┘  └─────────────────┘  └───────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘

VERSOES EXATAS (requirements.txt):
  FastAPI 0.115.5 | LangChain 0.3.9 | LangGraph 0.2.53 | Celery 5.4.0
  Redis 5.2.0 | SQLAlchemy 2.0.36 | pgvector 0.3.6 | Pydantic 2.10.3
  aio-pika 9.5.3 | httpx 0.28.1 | Twilio 9.4.0 | msal 1.31.0
```

---

### 3.6 Arquitetura LangGraph — Graphs, Nodes e Edges

A plataforma utiliza **LangGraph** (v0.2.53) para implementar máquinas de estado baseadas em grafos dirigidos. Cada graph define nodes (funções assíncronas que processam estado), edges (transições entre nodes) e conditional edges (decisões baseadas no estado em runtime).

#### 3.6.1 ConversationGraph (Graph Principal)

**Arquivo:** `app/shared/agents/conversation.py`  
**State:** `ConversationState` (TypedDict com LangGraph `add_messages`)  
**Entry point:** `classify_intent`  
**Framework:** `StateGraph` do LangGraph com `langgraph.graph.message.add_messages`

```
                        ┌──────────────┐
                        │ ENTRY POINT  │
                        │classify_intent│
                        └──────┬───────┘
                               │
                               v
                        ┌──────────────┐
                        │extract_      │
                        │entities      │
                        └──────┬───────┘
                               │
                   ┌───────────┼───────────────────────────┐
                   │ (conditional: decide_next_action)      │
            ┌──────┴──────┐  ┌───────┐  ┌────────────┐  ┌─┴──────────────┐
            │execute_     │  │execute│  │job_state_  │  │interview_      │
            │candidate_   │  │global_│  │loader      │  │state_loader    │
            │search       │  │search │  │            │  │                │
            └──────┬──────┘  └───┬───┘  └──────┬─────┘  └───────┬────────┘
                   │             │             │                │
                   │             │             v                v
                   │             │      ┌──────────────┐ ┌──────────────┐
                   │             │      │  job_router   │ │interview_   │
                   │             │      │(conditional)  │ │router       │
                   │             │      └──────┬───────┘ └──────┬───────┘
                   │             │             │                │
                   │             │    ┌────────┼────────┐       │
                   │             │    v        v        v       v
                   │             │ onboard  basics  ... 13   interview_
                   │             │ _node    _coll   nodes    details_coll
                   │             │    │        │        │       │
                   │             │    └────────┼────────┘       v
                   │             │             │          interview_
                   │             │             v          validator
                   │             │       validator  ──>  (conditional)
                   │             │             │          │         │
                   │             │             v          v         v
                   │             │       frame_gen   scheduler  response
                   │             │             │      _executor  _planner
                   │             │             v          │         │
                   │             │       response_        └────┬────┘
                   │             │       planner               │
                   │             │             │               │
                   v             v             v               v
                   └─────────────┴─────────────┴───────────────┘
                                        │
                                        v
                                ┌──────────────┐
                                │generate_     │
                                │response      │──> ask_clarification
                                └──────┬───────┘           │
                                       │                   │
                                       v                   v
                                    [ END ]             [ END ]
```

**Total de nodes:** 44 nodes registrados no graph:
- **Core:** classify_intent, extract_entities, execute_candidate_search, execute_global_search, generate_response, ask_clarification (6)
- **Job Creation (13 steps):** job_state_loader, job_router, onboarding_node, basics_collector, remuneration_collector, org_structure_collector, technical_matrix_collector, sourcing_strategy_collector, wsi_competencies_collector, interview_flow_collector, governance_collector, communication_templates_collector, job_description_generator, publication_node, screening_collector, change_request_processor, validator, frame_generator, response_planner (19)
- **Interview Scheduling:** interview_state_loader, interview_router, interview_details_collector, interview_validator, interview_scheduler_executor, interview_response_planner (6)
- **Sourcing & Engagement (steps 14-27):** sourcing_state_initializer, local_search_node, calibration_node, process_calibration_feedback, volume_assessment_node, global_expansion_node, contact_approval_node, email_outreach_node, async_screening_node, candidate_feedback_node, recruiter_report_node, recruiter_decision_node, auto_scheduling_node, rejection_feedback_node, placement_node, mass_feedback_node (16) — nota: 3 nodes compartilhados com core

**Conditional edges:**
1. `extract_entities` → `decide_next_action` → 6 destinos (search, global, create_job, schedule, response, END)
2. `job_router` → `decide_job_creation_next` → 14 destinos (onboarding a publication + legacy)
3. `interview_validator` → `decide_interview_next` → 2 destinos (executor ou planner)
4. `publication_node` → `decide_after_publication` → 2 destinos (sourcing ou validator)
5. `recruiter_decision_node` → `decide_sourcing_next` → 3 destinos (scheduling, rejection, response)

**ConversationState (schema):**
```python
class ConversationState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]  # LangGraph native
    user_id: str
    user_role: str           # recruiter, hiring_manager, admin
    intent: Optional[str]    # create_job, search_candidates, schedule_interview...
    entities: dict           # NER extraído via LLM
    confidence: float        # 0-1
    current_workflow: Optional[str]
    workflow_step: int
    workflow_data: dict      # Estado persistido do workflow ativo
    next_action: str         # ask_question, execute_action, end
    response: Optional[str]
    context_summary: str     # Memória de conversa resumida
```

#### 3.6.2 JobWizardGraph (Graph Especializado)

**Arquivo:** `app/domains/job_management/agents/job_wizard_graph.py`  
**State:** `JobWizardState` (de `app/agents/state_machine.py`)  
**Entry point:** `intent_classifier`  
**Padrão:** Implementação customizada que replica o padrão LangGraph (NÃO usa `StateGraph` do LangGraph — é uma máquina de estados proprietária com interface similar a LangGraph para consistência arquitetural)

```
                   ┌──────────────────┐
                   │  intent_         │
                   │  classifier      │
                   └────────┬─────────┘
                            │
              ┌─────────────┼─────────────────────────────┐
              │ (conditional edges por WizardIntent)       │
              │                                            │
     ┌────────┴────────┐  ┌───────────────┐  ┌───────────┴──────────┐
     │ START_FROM_      │  │ PROVIDE_INFO  │  │ SKIP / GO_BACK /    │
     │ SCRATCH /        │  │ MODIFY        │  │ CONFIRM             │
     │ USE_EXISTING /   │  │               │  │                     │
     │ USE_TEMPLATE     │  │               │  │                     │
     │ HELP / ASK_Q     │  │               │  │                     │
     └────────┬─────────┘  └───────┬───────┘  └───────────┬─────────┘
              │                    │                      │
              v                    v                      v
     ┌──────────────┐     ┌──────────────┐       ┌──────────────┐
     │ response_    │     │ field_       │       │ stage_       │
     │ generator    │     │ extractor    │       │ transition   │
     └──────────────┘     └──────┬───────┘       └──────┬───────┘
                                 │                      │
                                 v               ┌──────┴──────┐
                          ┌──────────────┐       │ (conditional)│
                          │ tool_router  │       │             │
                          └──────┬───────┘       v             v
                     ┌───────────┼────────┐   [ END ]    intent_
                     │ (cond: tool_calls?)│              classifier
                     v                   v               (loop)
              ┌──────────────┐   ┌──────────────┐
              │ tool_executor│   │ response_    │
              └──────┬───────┘   │ generator    │
                     │           └──────┬───────┘
                     v                  │
              response_generator        │
                     │                  │
                     v                  v
              ┌──────────────┐
              │ stage_       │
              │ transition   │──> END ou loop
              └──────────────┘
```

**Nodes (6):** intent_classifier, field_extractor, tool_router, tool_executor, response_generator, stage_transition

**WizardIntent enum:** START_FROM_SCRATCH, USE_EXISTING, USE_TEMPLATE, PROVIDE_INFO, MODIFY, HELP, ASK_QUESTION, SKIP, GO_BACK, CONFIRM

**WizardStage enum (8 estágios):** Define as 8 etapas da criação de vaga com transições condicionais

**EdgeCondition pattern:**
```python
@dataclass
class EdgeCondition:
    target_node: str
    condition: Optional[Callable[[JobWizardState], bool]] = None
    priority: int = 0  # Higher priority = checked first
```

**Proteção contra loops infinitos:** `MAX_ITERATIONS = 10`

---

### 3.7 Processamento Assíncrono — RabbitMQ + Celery

> **Nota para o auditor:** A arquitetura de mensageria abaixo é extraída da configuração docker-compose, do `DomainTaskManager` (`app/shared/tasks/domain_task_manager.py`), e da configuração Celery (`app/core/celery.py`). Verificar a implementação real dos workers e se todas as filas estão ativas no ambiente de produção.

#### Arquitetura de Mensageria

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PROCESSAMENTO SÍNCRONO                                 │
│                                                                             │
│  FastAPI Handler                                                           │
│       │                                                                     │
│       ├── Operações leves (< 5s): executa direto                           │
│       │   - Intent classification                                          │
│       │   - Entity extraction                                              │
│       │   - Single candidate scoring                                       │
│       │                                                                     │
│       └── Operações pesadas: publica na fila ──────────────────────────┐   │
│           - Bulk screening (500+ candidatos)                           │   │
│           - Mass email/WhatsApp                                        │   │
│           - Full ATS sync                                              │   │
│           - Report generation                                          │   │
│           - Batch stage transitions                                    │   │
└────────────────────────────────────────────────────────────┬────────────┘   
                                                             │               
                                                             v               
┌─────────────────────────────────────────────────────────────────────────────┐
│                       RABBITMQ (Message Broker)                             │
│                                                                             │
│   Exchange: lia_tasks (direct)                                             │
│                                                                             │
│   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐     │
│   │ screening    │ │ communication│ │ ats_sync     │ │ analytics    │     │
│   │ queue        │ │ queue        │ │ queue        │ │ queue        │     │
│   │              │ │              │ │              │ │              │     │
│   │ bulk_screen  │ │ mass_email   │ │ bulk_sync    │ │ full_report  │     │
│   │ batch_eval   │ │ mass_whatsapp│ │ full_import  │ │ export_data  │     │
│   │ full_pipeline│ │ bulk_notif   │ │ full_export  │ │ predictive   │     │
│   └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘     │
│                                                                             │
│   Config: RABBITMQ_URL = amqp://guest:guest@localhost:5672/                │
│   Ports: 5672 (AMQP), 15672 (Management UI)                               │
│   Persistência: rabbitmq_data volume                                       │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   v
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CELERY WORKERS                                        │
│                                                                             │
│   celery -A app.core.celery worker --loglevel=info                         │
│                                                                             │
│   ┌──────────────────────────────────────────────────────────┐             │
│   │ Worker Pool                                               │             │
│   │                                                           │             │
│   │  Task 1: bulk_screening_task                              │             │
│   │    -> WSI pipeline para N candidatos                      │             │
│   │    -> Usa LangChain/Claude para scoring                   │             │
│   │                                                           │             │
│   │  Task 2: mass_communication_task                          │             │
│   │    -> Envia emails/WhatsApp em lote                       │             │
│   │    -> Rate limiting por provider (Twilio, Mailgun)       │             │
│   │                                                           │             │
│   │  Task 3: ats_sync_task                                    │             │
│   │    -> Sincroniza com Gupy/Pandapé/Merge                   │             │
│   │    -> Idempotency e retry automático                      │             │
│   │                                                           │             │
│   │  Task 4: scheduled_reports_task                           │             │
│   │    -> APScheduler-compatible                              │             │
│   │    -> Daily briefings, weekly reports                     │             │
│   └──────────────────────────────────────────────────────────┘             │
│                                                                             │
│   Dependências: postgres (healthy), redis (healthy), rabbitmq (healthy)    │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### DomainTaskManager (Camada de Abstração)

Além do Celery, a plataforma possui um `DomainTaskManager` (Singleton) que gerencia filas in-process por domínio:

```python
ASYNC_ELIGIBLE_ACTIONS = {
    "sourcing":              ["bulk_search", "mass_outreach", "import_candidates"],
    "cv_screening":          ["bulk_screen", "batch_evaluate", "full_pipeline_screen"],
    "communication":         ["mass_email", "mass_whatsapp", "bulk_notification"],
    "analytics":             ["generate_full_report", "export_large_dataset", "predictive_analysis"],
    "ats_integration":       ["bulk_sync", "full_import", "full_export"],
    "automation":            ["batch_stage_transition", "run_automation_rules"],
    "job_management":        ["bulk_publish", "batch_update_jobs"],
    "interview_scheduling":  ["batch_schedule"],
    "recruiter_assistant":   ["generate_daily_briefing"],
}
```

**Configuração:** max_concurrent_per_domain=3, max_queue_size=100

---

### 3.8 Redis — Cache Inteligente de 3 Camadas

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   CACHE MANAGER SERVICE (3 camadas)                         │
│                   app/shared/resilience/cache_manager_service.py             │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ LAYER 1: Session Cache (In-Memory)                                  │   │
│  │                                                                     │   │
│  │ TTL: 1 hora | Max entries: 1000                                    │   │
│  │ Escopo: Por conversa/sessão                                        │   │
│  │ Uso: Cache de respostas recentes, estado de workflow               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                          │ miss                                             │
│                          v                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ LAYER 2: Redis Cache                                                │   │
│  │                                                                     │   │
│  │ TTL: 1-30 dias (por namespace)                                     │   │
│  │ Escopo: Global (compartilhado entre sessões)                       │   │
│  │                                                                     │   │
│  │ Namespaces e TTLs:                                                 │   │
│  │ ┌─────────────────────┬──────────┬───────────────────────────────┐ │   │
│  │ │ Namespace           │ TTL      │ Uso                           │ │   │
│  │ ├─────────────────────┼──────────┼───────────────────────────────┤ │   │
│  │ │ SALARY_BENCHMARK    │ 7 dias   │ Dados salariais de mercado   │ │   │
│  │ │ MARKET_DATA         │ 7 dias   │ Dados de mercado              │ │   │
│  │ │ SKILLS_SUGGESTIONS  │ 30 dias  │ Expansão semântica de skills │ │   │
│  │ │ JD_SUMMARY          │ 7 dias   │ Resumos de JDs               │ │   │
│  │ │ COMPANY_CONFIG      │ 7 dias   │ Configurações da empresa     │ │   │
│  │ │ LEARNING_PATTERNS   │ 30 dias  │ Padrões aprendidos           │ │   │
│  │ │ LLM_RESPONSE        │ 7 dias   │ Respostas de LLM cacheadas   │ │   │
│  │ │ EMBEDDINGS          │ 30 dias  │ Vetores gerados              │ │   │
│  │ └─────────────────────┴──────────┴───────────────────────────────┘ │   │
│  │                                                                     │   │
│  │ Features:                                                          │   │
│  │ - Similarity matching com threshold configurável (0.75-0.90)       │   │
│  │ - Graceful degradation para in-memory quando Redis indisponível    │   │
│  │ - Hash-based cache keys para lookup eficiente                      │   │
│  │ - Multi-tenant via company_id scoping                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                          │ miss                                             │
│                          v                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ LAYER 3: PostgreSQL Cache (dados estáveis)                          │   │
│  │                                                                     │   │
│  │ TTL: 30+ dias                                                      │   │
│  │ Uso: Configurações de empresa, padrões aprendidos, embeddings      │   │
│  │ Tabela: intelligent_cache                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### AI Cache Service (Camada Especializada)

O `AICacheService` (`app/services/ai_cache_service.py`) fornece cache especializado para conteúdo gerado por IA:

| Cache Type | TTL | Similarity Threshold | Uso |
|---|---|---|---|
| jd_generation | 24h | 0.85 | Descrições de vaga geradas |
| wsi_questions | 48h | 0.90 | Perguntas WSI geradas |
| skills_extraction | 72h | 0.80 | Skills extraídas de CVs |
| salary_analysis | 12h | 0.75 | Análises salariais |
| competency_mapping | 48h | 0.85 | Mapeamento de competências |

#### Semantic Search Service (Redis + Gemini)

O `SemanticSearchService` (`app/shared/intelligence/semantic_search_service.py`) combina Redis cache com Gemini para expansão semântica em 7 domínios: Skills, Job Titles, Roles, Industries, Expertise, Fields of Study, Companies.

- **Target:** P95 < 300ms
- **Cache TTL:** 5-10 minutos no Redis
- **Provider:** Google Gemini (rápido para expansão)
- **Frontend debounce:** 400-500ms

---

### 3.9 Busca Semântica — Elasticsearch + PG Vector + WRF

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TALENT FUNNEL SEARCH PIPELINE                            │
│                                                                             │
│  Recrutador digita query                                                   │
│       │                                                                     │
│       v                                                                     │
│  ┌──────────────────┐                                                      │
│  │ SemanticSearch    │  Expansão semântica via Gemini                       │
│  │ Service           │  "Python" → [FastAPI, Django, Flask, PyTorch...]     │
│  └────────┬─────────┘                                                      │
│           │                                                                 │
│     ┌─────┴──────┐                                                         │
│     │            │                                                          │
│     v            v                                                          │
│  ┌──────────┐ ┌──────────────┐                                             │
│  │ Elastic  │ │ PG Vector    │                                             │
│  │ Search   │ │ (pgvector    │                                             │
│  │          │ │  0.3.6)      │                                             │
│  │ Full-text│ │              │                                             │
│  │ + BM25   │ │ Cosine sim   │                                             │
│  │ scoring  │ │ on Vector    │                                             │
│  │          │ │ (768 dims)   │                                             │
│  └────┬─────┘ └──────┬───────┘                                             │
│       │              │                                                      │
│       v              v                                                      │
│  ┌─────────────────────────┐                                               │
│  │ Pre-WRF Filter          │  Filtragem preliminar                         │
│  │ pre_wrf_filter_service  │  (seniority, location, experience)            │
│  └────────────┬────────────┘                                               │
│               │                                                             │
│               v                                                             │
│  ┌─────────────────────────┐                                               │
│  │ WRF (Weighted Ranking   │  Ranking ponderado:                           │
│  │ Framework)              │  Score = w1*skills + w2*experience +           │
│  │                         │         w3*semantic + w4*location +            │
│  │                         │         w5*seniority                           │
│  └────────────┬────────────┘                                               │
│               │                                                             │
│               v                                                             │
│  ┌─────────────────────────┐                                               │
│  │ PGV Gap Analyzer        │  Análise de gaps semânticos                   │
│  │ pgv_gap_analyzer        │  (skills que faltam vs. requeridos)           │
│  └────────────┬────────────┘                                               │
│               │                                                             │
│               v                                                             │
│  ┌─────────────────────────┐                                               │
│  │ ES Score Drop Analyzer  │  Detecta quedas abruptas de score             │
│  │ es_score_drop_analyzer  │  (corte natural de relevância)                │
│  └────────────┬────────────┘                                               │
│               │                                                             │
│               v                                                             │
│  Resultados paginados + feedback loop para otimização estatística          │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Serviços envolvidos:**
- `SemanticSearchService` — Expansão semântica de termos
- `PreWRFFilterService` — Filtragem pré-ranking
- `PGVGapAnalyzer` — Análise de gaps com PG Vector
- `ESScoreDropAnalyzer` — Detecção de corte de relevância
- `EmbeddingService` — Geração de embeddings (text-embedding-004, 768 dimensões)

**Modelos de dados vetoriais:**
- `ConversationMemory` — Vector(768) para busca semântica em memória conversacional
- `KnowledgeBase` — Vector(768) para RAG em documentos da empresa

---

### 3.10 Prompts, RAG e Base de Conhecimento

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SISTEMA DE PROMPTS                                   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ DOMAIN PROMPTS (YAML)                                               │   │
│  │ app/domains/{domain}/prompts.yaml                                   │   │
│  │                                                                     │   │
│  │ Cada domínio define:                                               │   │
│  │ - system_prompt: Contexto e persona do agente                      │   │
│  │ - few_shot_examples: Exemplos de interação                         │   │
│  │ - tool_descriptions: Descrições de ferramentas                     │   │
│  │ - error_templates: Mensagens de erro humanizadas                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ INLINE PROMPTS (Python)                                             │   │
│  │                                                                     │   │
│  │ ConversationGraph:                                                 │   │
│  │ - SYSTEM_PROMPT (app/shared/agents/conversation.py)                │   │
│  │   → Persona LIA, princípios de comunicação, capabilities          │   │
│  │ - Intent classification prompt (in classify_intent node)           │   │
│  │ - Entity extraction prompts (per-intent templates)                 │   │
│  │                                                                     │   │
│  │ JobWizardGraph:                                                    │   │
│  │ - WizardIntent classification prompt                               │   │
│  │ - Field extraction prompts (per-stage)                             │   │
│  │ - Response generation templates                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ RAG KNOWLEDGE BASE                                                  │   │
│  │                                                                     │   │
│  │ Fontes de dados:                                                   │   │
│  │ ┌───────────────────────────────────────────────────────────────┐   │   │
│  │ │ 1. training/rag_knowledge/wsi_methodology/                    │   │   │
│  │ │    └── report_templates.md                                    │   │   │
│  │ │    → Templates de relatórios WSI para geração                │   │   │
│  │ │                                                               │   │   │
│  │ │ 2. KnowledgeBase (tabela PostgreSQL + pgvector)               │   │   │
│  │ │    → Documentos da empresa indexados com Vector(768)          │   │   │
│  │ │    → document_type: job_description, policy, faq, etc.       │   │   │
│  │ │    → Chunking com parent_id para documentos longos           │   │   │
│  │ │                                                               │   │   │
│  │ │ 3. ConversationMemory (tabela PostgreSQL + pgvector)          │   │   │
│  │ │    → Histórico conversacional com embedding                  │   │   │
│  │ │    → Busca semântica por similaridade coseno                 │   │   │
│  │ │    → Escopo: company_id + session_id (multi-tenant)          │   │   │
│  │ │                                                               │   │   │
│  │ │ 4. Prompts examples (Few-shot)                                │   │   │
│  │ │    app/shared/prompts/examples/                               │   │   │
│  │ │    ├── sourcing_examples.py                                   │   │   │
│  │ │    └── job_planner_examples.py                                │   │   │
│  │ └───────────────────────────────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  │ Fluxo de retrieval:                                                │   │
│  │ 1. Mensagem do usuário → EmbeddingService → Vector(768)           │   │
│  │ 2. Busca por similaridade coseno em KnowledgeBase                 │   │
│  │ 3. Top-K documentos injetados no prompt como contexto             │   │
│  │ 4. LLM gera resposta contextualizada                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 3.11 Fluxo de Dados das IAs — Learning Loop e Feedback

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CICLO DE APRENDIZADO CONTÍNUO                            │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 1. CAPTURE (Silencioso)                                             │   │
│  │                                                                     │   │
│  │ InteractionFeedback (tabela)                                       │   │
│  │ - session_id, company_id, user_id                                  │   │
│  │ - user_message + lia_response                                      │   │
│  │ - intent, stage                                                    │   │
│  │ - rating (1-5), thumbs (up/down), correction (texto)              │   │
│  │ - response_time_ms, tools_used, confidence_score                   │   │
│  │ - processed (bool), incorporated_to_rag (bool)                    │   │
│  │                                                                     │   │
│  │ FeedbackService captura:                                           │   │
│  │ - Thumbs up/down explícitos                                        │   │
│  │ - Ratings com feedback textual                                     │   │
│  │ - Correções do usuário (texto melhorado)                           │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                                   │                                         │
│                                   v                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 2. ANALYZE (LearningLoopService)                                    │   │
│  │                                                                     │   │
│  │ Detecção silenciosa de padrões:                                    │   │
│  │ - O que o recrutador ACEITA vs REJEITA vs MODIFICA                 │   │
│  │                                                                     │   │
│  │ FeedbackOutcome: ACCEPTED | MODIFIED | REJECTED | IGNORED          │   │
│  │                                                                     │   │
│  │ PatternTypes detectados:                                           │   │
│  │ ┌─────────────────────────┬────────────────────────────────────┐   │   │
│  │ │ SALARY_PREFERENCE       │ Faixas salariais preferidas        │   │   │
│  │ │ SKILL_PREFERENCE        │ Skills priorizadas                 │   │   │
│  │ │ BENEFIT_PREFERENCE      │ Benefícios preferidos              │   │   │
│  │ │ WORK_MODEL_PREFERENCE   │ Modelo de trabalho (remoto/híbrido)│   │   │
│  │ │ SCREENING_PREFERENCE    │ Preferências de triagem            │   │   │
│  │ │ JD_STYLE_PREFERENCE     │ Estilo de JD (tom, formato)        │   │   │
│  │ │ SOURCE_TRUST            │ Fontes de dados confiáveis         │   │   │
│  │ └─────────────────────────┴────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  │ Confidence Thresholds:                                             │   │
│  │ - high: >= 20 samples    (promote if acceptance >= 75%)            │   │
│  │ - medium: >= 10 samples                                            │   │
│  │ - low: >= 5 samples      (demote if acceptance <= 25%)             │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                                   │                                         │
│                                   v                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 3. APPLY (Melhoria Contínua)                                        │   │
│  │                                                                     │   │
│  │ LearningPattern (tabela):                                          │   │
│  │ - pattern_type + pattern_key                                       │   │
│  │ - trigger_phrases: ["remoto", "home office", ...]                  │   │
│  │ - expected_response_style: "tom informal, exemplos práticos"       │   │
│  │ - preferred_tools: ["job_insights", "salary_benchmark"]            │   │
│  │ - example_good_responses / example_bad_responses                   │   │
│  │ - positive_feedback_count / negative_feedback_count                │   │
│  │ - success_rate (auto-calculated)                                   │   │
│  │ - confidence (0.3 → 0.95 based on sample size)                    │   │
│  │                                                                     │   │
│  │ Uso: Padrões são injetados no prompt do agente para               │   │
│  │ personalizar respostas baseado no histórico da empresa             │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                                   │                                         │
│                                   v                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 4. FINE-TUNING DATA EXPORT                                          │   │
│  │                                                                     │   │
│  │ TrainingDataService (app/services/training_data_service.py):       │   │
│  │                                                                     │   │
│  │ Critérios de qualidade para inclusão:                              │   │
│  │ - Rating >= 4 OU thumbs == 'up'                                    │   │
│  │ - Response length > 50 chars                                       │   │
│  │ - Sem mensagens de erro                                            │   │
│  │ - Confidence score >= 0.7                                          │   │
│  │                                                                     │   │
│  │ Formatos de export:                                                │   │
│  │ ┌──────────────┬───────────────────────────────────────────────┐   │   │
│  │ │ OpenAI       │ {"messages": [system, user, assistant]}       │   │   │
│  │ │ Anthropic    │ {"prompt": "...", "completion": "..."}        │   │   │
│  │ │ DPO          │ {"chosen": good_response, "rejected": bad}   │   │   │
│  │ │              │ (gerado de corrections do usuário)            │   │   │
│  │ └──────────────┴───────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 3.12 Custos e Consumo de IA — Billing e Token Tracking

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AI CONSUMPTION TRACKING                                   │
│                                                                             │
│  Cada chamada LLM registra:                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ AiConsumption (tabela)                                              │   │
│  │                                                                     │   │
│  │ company_id      → Isolamento multi-tenant                          │   │
│  │ user_id         → Quem disparou                                    │   │
│  │ agent_type      → screening | scoring | interview | cv_parsing |   │   │
│  │                   search | matching | communication | analysis     │   │
│  │ operation       → Nome da operação específica                      │   │
│  │ model           → claude-sonnet | claude-haiku | gemini-pro |      │   │
│  │                   gemini-flash | gpt-4 | gpt-4-turbo              │   │
│  │ input_tokens    → Tokens de entrada                                │   │
│  │ output_tokens   → Tokens de saída                                  │   │
│  │ total_tokens    → Total                                            │   │
│  │ cost_cents      → Custo em centavos                                │   │
│  │ candidate_id    → Candidato associado (opcional)                   │   │
│  │ vacancy_id      → Vaga associada (opcional)                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ AiCreditsBalance (tabela — por empresa)                             │   │
│  │                                                                     │   │
│  │ monthly_limit        → Limite mensal de tokens (default: 100.000)  │   │
│  │ current_usage        → Uso no período                              │   │
│  │ period_start/end     → Período de cobrança                         │   │
│  │ overage_allowed      → Permite ultrapassar limite?                 │   │
│  │ overage_rate_cents   → Custo por token excedente                   │   │
│  │                                                                     │   │
│  │ Métricas calculadas:                                               │   │
│  │ - usage_percentage = (current_usage / monthly_limit) * 100         │   │
│  │ - remaining_tokens = max(0, monthly_limit - current_usage)         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  API Endpoints (/api/v1/ai-consumption) — 10 endpoints:                    │
│  - GET  /summary              → Resumo do período atual                    │
│  - GET  /usage                → Uso do período (alias)                     │
│  - GET  /usage/{client_id}    → Uso de cliente específico (admin)          │
│  - GET  /history              → Histórico completo                         │
│  - GET  /by-agent             → Breakdown por tipo de agente               │
│  - GET  /daily                → Consumo diário                             │
│  - GET  /by-day               → Consumo diário (alias)                     │
│  - GET  /balance              → Saldo e limites                            │
│  - POST /record               → Registra consumo (interno)                 │
│  - PUT  /limits/{client_id}   → Atualiza limites (admin)                   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ BILLING SERVICE (Assinaturas SaaS)                                  │   │
│  │ app/services/billing_service.py                                     │   │
│  │                                                                     │   │
│  │ Providers: Iugu (padrão) | Vindi (alternativo)                     │   │
│  │ Modelos: Subscription, Invoice, PaymentMethod                      │   │
│  │ Ciclos: monthly | yearly                                           │   │
│  │ Status: active | trialing | cancelled | past_due                   │   │
│  │                                                                     │   │
│  │ A cobrança de IA é vinculada à assinatura da empresa               │   │
│  │ via company_id (tenant isolation)                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 3.13 Segurança e Isolamento Multi-Tenant

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              ARQUITETURA DE ISOLAMENTO MULTI-TENANT                          │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ CAMADA 1: API (Autenticação e Extração)                             │   │
│  │                                                                     │   │
│  │ Header: X-Company-ID (UUID)                                        │   │
│  │ → Extraído e validado em cada request                              │   │
│  │ → Repassado para DomainContext.tenant_id                           │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                                   │                                         │
│                                   v                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ CAMADA 2: Domain Context (Scoping)                                  │   │
│  │                                                                     │   │
│  │ DomainContext (app/domains/base.py):                                │   │
│  │   domain_id: str                                                   │   │
│  │   user_id: str                                                     │   │
│  │   session_id: str                                                  │   │
│  │   tenant_id: str    ← ISOLAMENTO PRINCIPAL                        │   │
│  │   current_data: dict                                               │   │
│  │   selected_ids: List[str]                                          │   │
│  │   filters_applied: dict                                            │   │
│  │   conversation_memory: Optional[ConversationMemory]                │   │
│  │                                                                     │   │
│  │ Cada domain recebe DomainContext com tenant_id preenchido          │   │
│  │ e deve usá-lo em TODAS as queries ao banco de dados               │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                                   │                                         │
│                                   v                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ CAMADA 3: Dados (Filtro por company_id)                             │   │
│  │                                                                     │   │
│  │ Todas as tabelas críticas incluem company_id (UUID, indexed):      │   │
│  │                                                                     │   │
│  │ ┌───────────────────────────────┬──────────────────────────────┐   │   │
│  │ │ Tabela                       │ Scoping                       │   │   │
│  │ ├───────────────────────────────┼──────────────────────────────┤   │   │
│  │ │ ai_consumption               │ company_id (index)            │   │   │
│  │ │ ai_credits_balance           │ company_id (unique index)     │   │   │
│  │ │ conversation_memories        │ company_id + session_id       │   │   │
│  │ │ knowledge_base               │ company_id + document_type    │   │   │
│  │ │ interaction_feedback          │ company_id (index)            │   │   │
│  │ │ learning_patterns            │ company_id (index)            │   │   │
│  │ │ subscriptions                │ client_id (tenant)            │   │   │
│  │ └───────────────────────────────┴──────────────────────────────┘   │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                                   │                                         │
│                                   v                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ CAMADA 4: IA e Prompts (Isolamento de Contexto)                     │   │
│  │                                                                     │   │
│  │ - LearningPatterns filtrados por company_id                        │   │
│  │   → Empresa A não vê padrões da Empresa B                         │   │
│  │                                                                     │   │
│  │ - ConversationMemory filtrada por company_id + session_id          │   │
│  │   → RAG semântico escopo por tenant                                │   │
│  │                                                                     │   │
│  │ - KnowledgeBase filtrada por company_id                            │   │
│  │   → Documentos da empresa isolados                                 │   │
│  │                                                                     │   │
│  │ - AiConsumption registra company_id                                │   │
│  │   → Billing isolado por tenant                                     │   │
│  │                                                                     │   │
│  │ - AICacheService usa company_id no cache key                       │   │
│  │   → Cache de LLM não vaza entre tenants                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  AUTENTICAÇÃO:                                                             │
│  - WorkOS para SSO e autenticação de recrutadores                         │
│  - Bot Framework SDK + MSAL para autenticação Teams                       │
│  - JWT (python-jose) para tokens de sessão                                 │
│  - Passlib + bcrypt para hash de senhas                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.14 Personalização por Recrutador — Aprendizagem Adaptativa Individual

**Arquivo:** `app/services/recruiter_personalization_service.py`  
**Classe:** `RecruiterPersonalizationService`  
**Ativação:** Automática após **10+ vagas criadas** por recrutador (constante `MIN_JOBS_FOR_PERSONALIZATION`)

O sistema aprende o comportamento individual de cada recrutador e adapta a experiência do wizard, thresholds de confiança, defaults e fluxo de interação.

```
┌─────────────────────────────────────────────────────────────────────────┐
│            PIPELINE DE PERSONALIZAÇÃO POR RECRUTADOR                    │
│                                                                         │
│  Recrutador usa o Wizard (vagas 1-9)                                   │
│       ↓                                                                 │
│  Sistema OBSERVA e GRAVA:                                               │
│  - Campos que o recrutador sempre corrige                               │
│  - Valores que prefere por tipo de vaga                                 │
│  - Se usa JD import ou preenche manualmente                            │
│  - Se prefere fluxo rápido ou detalhado                                │
│       ↓                                                                 │
│  Após 10+ vagas → RecruiterProfile ativado                             │
│       ↓                                                                 │
│  get_personalization_context() retorna:                                 │
│  ┌─────────────────────────────────────────────────┐                   │
│  │ PersonalizationContext                           │                   │
│  │  ├─ profile: RecruiterProfile (DB)               │                   │
│  │  ├─ settings: PersonalizationSettings            │                   │
│  │  ├─ field_preferences: Dict[field, Preference]   │                   │
│  │  ├─ flow_config: WizardFlowConfig                │                   │
│  │  ├─ thresholds: PersonalizedThresholds           │                   │
│  │  ├─ defaults: PersonalizedDefaults               │                   │
│  │  ├─ personalization_level: str                   │                   │
│  │  │   ├─ "disabled" → Settings desligam           │                   │
│  │  │   ├─ "minimal" → <10 vagas, sem dados         │                   │
│  │  │   ├─ "partial" → 10-29 vagas                  │                   │
│  │  │   └─ "full" → 30+ vagas                       │                   │
│  │  └─ is_new_user: bool                            │                   │
│  └─────────────────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────┘
```

**Modelos de dados envolvidos:**

| Modelo | Tabela | Função |
|--------|--------|--------|
| `RecruiterProfile` | `recruiter_profiles` | Perfil acumulado (total_jobs_created, prefers_quick_flow, uses_jd_import, prefers_detailed_explanations) |
| `PersonalizationSettings` | `personalization_settings` | Toggle de enable_personalization por recrutador |
| `RecruiterFieldPreference` | `recruiter_field_preferences` | Preferências por campo (ex: salary_range → override_count, preferred_value, correction_rate) |

**WizardFlowConfig — Configuração adaptativa do fluxo:**

```python
@dataclass
class WizardFlowConfig:
    show_detailed_explanations: bool    # Baseado em prefers_detailed_explanations
    skip_optional_confirmations: bool   # Baseado em prefers_quick_flow
    auto_expand_sections: bool          # Inverso de quick_flow
    suggest_jd_import: bool             # Baseado em uses_jd_import
    highlight_often_corrected: bool     # Sempre True — destaca campos que o recrutador corrige
    pre_select_preferences: bool        # Sempre True — pré-seleciona valores preferidos
```

**PersonalizedThresholds — Limites de confiança adaptativos:**

```python
@dataclass
class ConfidenceThresholds:
    silent_apply: float = 0.85    # Aplica automaticamente sem perguntar
    apply_notify: float = 0.70   # Aplica e notifica
    ask_user: float = 0.50       # Pergunta ao recrutador
    ignore: float = 0.30         # Descarta sugestão

# Se recrutador prefere fluxo rápido:
quick_flow_thresholds = ConfidenceThresholds(
    silent_apply=0.80,   # Threshold mais baixo → mais automação
    apply_notify=0.65,
    ask_user=0.45
)
```

**Onde é aplicado:**
- **Wizard de Criação de Vaga** → `wizard_orchestrator_service.py` chama `get_personalization_context()` no início de cada sessão
- **Sugestões de IA** → Thresholds personalizados determinam se sugestão é aplicada silenciosamente, com notificação, ou se pergunta ao recrutador
- **Defaults de campos** → Campos pré-preenchidos com valores preferidos do recrutador
- **Fluxo do wizard** → Steps opcionais são pulados se recrutador sempre os pula
- **Recálculo** → Perfil recalculado a cada 24h ou quando `total_jobs_created` muda

---

### 3.15 Machine Learning Preditivo — Outcome Prediction e Feature Engineering

O sistema possui uma camada ML completa para previsão de resultados de vagas, construída sobre feature engineering e um registry de modelos.

#### 3.15.1 OutcomePredictor

**Arquivo:** `app/services/ml/outcome_predictor.py`  
**Classe:** `OutcomePredictor`  
**Requisito mínimo:** 30 amostras para ML (`MIN_SAMPLES_FOR_ML`), 100 para confiança alta (`MIN_SAMPLES_FOR_RELIABLE`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│              PIPELINE DE PREDIÇÃO ML                                    │
│                                                                         │
│  Job Data + Company Data                                                │
│       ↓                                                                 │
│  OutcomeFeatureEngineer.extract_job_features()                         │
│       ↓ JobFeatures (20+ features)                                     │
│       ↓                                                                 │
│  OutcomeFeatureEngineer.extract_historical_features(company_id)        │
│       ↓ OutcomeFeatures (avg_time_to_fill, success_rate, etc.)        │
│       ↓                                                                 │
│  ┌───────────────────────────────────────────────────────┐             │
│  │ MODELO: predict_time_to_fill()                         │             │
│  │                                                        │             │
│  │ base_days = base_ttf_by_role[role]                    │             │
│  │   × seniority_multiplier (0.6 intern → 2.5 C-level)  │             │
│  │   × rarity_factor (1.0 + skill_rarity × 0.5)         │             │
│  │   × demand_factor (1.0 − market_demand × 0.3)        │             │
│  │   × location_factor (remote=0.85, onsite=1.15)       │             │
│  │   × size_factor (micro/small=1.1, enterprise=0.9)    │             │
│  │   × urgency_factor (urgent=0.8, normal=1.0)          │             │
│  │                                                        │             │
│  │ Blending com dados históricos:                        │             │
│  │ predicted = model × (1−w) + historical_avg × w       │             │
│  │ onde w = min(1.0, success_rate × 0.5)                │             │
│  │                                                        │             │
│  │ Clamp: min=7 dias, max=180 dias                       │             │
│  │ Range: ±25% do predito                                │             │
│  └───────────────────────────────────────────────────────┘             │
│       ↓                                                                 │
│  TimeToFillPrediction (predicted_days, range_min, range_max,           │
│                        confidence, factors, model_version)              │
└─────────────────────────────────────────────────────────────────────────┘
```

**4 tipos de predição disponíveis:**

| Método | Retorno | Fatores considerados |
|--------|---------|---------------------|
| `predict_time_to_fill()` | `TimeToFillPrediction` | Role, seniority, skill rarity, market demand, location, company size, urgency |
| `predict_salary_range()` | `SalaryRangePrediction` | Role, seniority, location, market data, company historical |
| `predict_skill_success()` | `SkillSuccessPrediction` | Skill name, historical hires with skill, success rate |
| `predict_candidate_fit()` | `PredictionResult` | WSI score, skills match, experience, cultural signals |

**Base TTF por role (em dias):**

| Role | Base (dias) | Role | Base (dias) |
|------|-------------|------|-------------|
| engineering | 35 | marketing | 25 |
| data | 40 | sales | 20 |
| design | 30 | hr | 22 |
| product | 35 | finance | 28 |
| operations | 30 | legal | 35 |

**Seniority multipliers:** intern=0.6, junior=0.7, pleno=1.0, senior=1.3, lead=1.5, staff=1.8, director=2.0, C-level=2.5

#### 3.15.2 Feature Engineering

**Arquivo:** `app/services/ml/feature_engineering.py`  
**Classe:** `OutcomeFeatureEngineer`

Extrai features estruturadas de vagas e resultados históricos para alimentar modelos preditivos.

**JobFeatures (20 features extraídas de cada vaga):**

```python
@dataclass
class JobFeatures:
    role_category: str          # Classificação do cargo (engineering, sales, etc.)
    seniority_level: int        # 0 (intern) a 7 (C-level)
    department_id: str          # Departamento
    location_type: str          # remote, hybrid, onsite
    salary_min: float           # Faixa salarial
    salary_max: float
    salary_midpoint: float      # Ponto médio calculado
    num_required_skills: int    # Quantidade de skills obrigatórias
    num_nice_to_have_skills: int # Quantidade de desejáveis
    has_remote_option: bool     # Tem opção remota
    has_relocation: bool        # Oferece relocação
    company_size_category: str  # micro, small, medium, large, enterprise
    industry_category: str      # Setor (tech, finance, etc.)
    creation_month: int         # Mês de criação (sazonalidade)
    creation_quarter: int       # Trimestre (sazonalidade)
    creation_day_of_week: int   # Dia da semana (padrões temporais)
    is_urgent: bool             # Flag de urgência
    skill_rarity_score: float   # 0.0-1.0, calculado por análise de mercado
    market_demand_score: float  # 0.0-1.0, demanda atual
```

**OutcomeFeatures (features históricas por empresa):**

```python
@dataclass
class OutcomeFeatures:
    avg_time_to_fill: float           # Média de dias para preencher
    median_time_to_fill: float        # Mediana (mais robusta a outliers)
    success_rate: float               # Taxa de sucesso (contratações/vagas)
    avg_candidates_per_hire: float    # Candidatos médios por contratação
    avg_salary_vs_market: float       # Salário vs mercado
    skill_match_rate: float           # Taxa de match de skills
    sourcing_channel_effectiveness: Dict[str, float]  # Eficácia por canal
    stage_conversion_rates: Dict[str, float]          # Conversão por etapa
```

**Seniority Mapping:** intern=0, junior=1, pleno/mid=2, senior=3, lead/manager=4, principal/staff/director=5, VP=6, C-level=7

#### 3.15.3 Model Registry

**Arquivo:** `app/services/ml/model_registry.py`  
**Classe:** `ModelRegistry`

Sistema de versionamento e gestão de modelos ML, preparado para migração futura para MLflow.

```
┌─────────────────────────────────────────────────────────────────────────┐
│              MODEL REGISTRY                                             │
│                                                                         │
│  ModelMetadata                    ModelPerformance                      │
│  ├─ model_id: str (UUID)         ├─ predictions_count: int             │
│  ├─ model_name: str              ├─ correct_predictions: int           │
│  ├─ version: str (semver)        ├─ total_error: float                 │
│  ├─ description: str             ├─ accuracy: float (computed)         │
│  ├─ metrics: Dict[str, float]    └─ mean_error: float (computed)       │
│  ├─ parameters: Dict[str, Any]                                         │
│  ├─ is_active: bool                                                     │
│  └─ is_default: bool                                                    │
│                                                                         │
│  Modelos built-in registrados:                                          │
│  ├─ time_to_fill_predictor v1.0.0 (rule-based, 20 features, default)  │
│  ├─ salary_range_predictor v1.0.0 (rule-based, default)                │
│  ├─ skill_success_predictor v1.0.0 (rule-based, default)               │
│  └─ candidate_fit_predictor v1.0.0 (rule-based, default)               │
│                                                                         │
│  Operações:                                                             │
│  ├─ register_model() → Registra novo modelo com versão                 │
│  ├─ get_model() → Obtém metadata de modelo específico                  │
│  ├─ get_default_model() → Obtém modelo default para tipo               │
│  ├─ set_default() → Define modelo como default                         │
│  ├─ record_prediction() → Registra predição para tracking              │
│  └─ get_performance() → Obtém métricas de performance                  │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 3.15.4 Outcome Correlator — Correlações Estatísticas

**Arquivo:** `app/services/outcome_correlator_service.py`  
**Classe:** `OutcomeCorrelatorService`  
**Requisitos:** MIN_SAMPLE_SIZE=20, SIGNIFICANCE_THRESHOLD=0.05, CORRELATION_THRESHOLD=0.3

Descobre correlações entre características de vagas e seus resultados usando análise estatística (Pearson correlation + p-value).

**Fatores analisados vs Métricas de resultado:**

```
FATORES ANALISÁVEIS:           MÉTRICAS DE RESULTADO:
├─ salary_percentile           ├─ time_to_fill_days
├─ work_model                  ├─ satisfaction_score
├─ seniority                   ├─ candidate_count_total
├─ has_screening_questions     └─ candidate_count_interviewed
└─ pipeline_length
```

**Output:** `CorrelationResult` com correlation (Pearson r), significance (p-value), direction (positive/negative), recommendation (texto acionável).

**Exemplos de insights gerados:**
- "Posições remotas preenchem 30% mais rápido que presenciais"
- "Vagas com 3+ perguntas de screening têm satisfação 15% maior"
- "Faixa salarial acima do percentil 75 reduz time-to-fill em 25%"

#### 3.15.5 Pattern Detector — Detecção de Padrões

**Arquivo:** `app/services/pattern_detector_service.py`  
**Classe:** `PatternDetectorService`  
**Thresholds:** MIN_CORRECTIONS=10, MIN_OUTCOMES=20, HIGH_CONFIDENCE=30 amostras, CACHE=24h

Detecta padrões em correções de recrutadores e resultados de vagas.

```
┌─────────────────────────────────────────────────────────────────────────┐
│              DETECÇÃO DE PADRÕES                                        │
│                                                                         │
│  TIPO 1: Correction Patterns                                           │
│  - Analisa WizardFeedback por company_id                               │
│  - Detecta campos sistematicamente corrigidos                          │
│  - Ex: "Salário sempre ajustado +15% para DevOps Senior"              │
│  - Ex: "Seniority sempre corrigido de Pleno para Senior em Data"      │
│                                                                         │
│  TIPO 2: Success Profiles                                              │
│  - Analisa JobOutcome de vagas preenchidas com sucesso                 │
│  - Identifica características de vagas bem-sucedidas                   │
│  - Ex: "Vagas com 5-8 skills obrigatórias têm melhor success_rate"    │
│                                                                         │
│  Cálculo de Confiança (CV = std_dev / mean):                          │
│  ├─ <5 amostras → confidence=0.30                                      │
│  ├─ 5-9 amostras → confidence=0.50                                     │
│  ├─ 10-19 amostras → confidence=0.70                                   │
│  ├─ 20-49 amostras → confidence=0.80                                   │
│  ├─ 50+ amostras → confidence=0.90                                     │
│  └─ Ajuste por CV: <0.1 → +0.05, >0.5 → −0.10                       │
│                                                                         │
│  Cache: PatternCache armazena patterns com TTL de 24h                  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 3.16 Clusterização e Padrões Históricos — JobPattern + Learning Hub

#### 3.16.1 JobPattern — Padrões de Vagas com pgvector

**Arquivo:** `app/models/job_pattern.py`  
**Classe:** `JobPattern` (SQLAlchemy Model)  
**Tabela:** `job_patterns`  
**Embedding:** pgvector com dimensão 768

```
┌─────────────────────────────────────────────────────────────────────────┐
│              MODELO JobPattern                                          │
│                                                                         │
│  Tabela: job_patterns                                                   │
│  ┌──────────────────────┬────────────────────────────────┐             │
│  │ Campo                │ Tipo / Função                   │             │
│  ├──────────────────────┼────────────────────────────────┤             │
│  │ id                   │ UUID (PK)                       │             │
│  │ company_id           │ UUID (FK, indexed)              │             │
│  │ pattern_type         │ String(50), indexed             │             │
│  │ pattern_key          │ String(255), indexed            │             │
│  │ job_title_normalized │ String(255), indexed            │             │
│  │ department           │ String(100), indexed            │             │
│  │ seniority            │ String(50)                      │             │
│  │ location             │ String(255)                     │             │
│  │ work_model           │ String(50)                      │             │
│  │ sample_count         │ Integer (vagas que geraram)     │             │
│  │ success_count        │ Integer (contratações)          │             │
│  │ success_rate         │ Float (success/sample)          │             │
│  │ avg_salary_min       │ Float (média salário mín)       │             │
│  │ avg_salary_max       │ Float (média salário máx)       │             │
│  │ skill_frequency      │ JSON (skill→count)              │             │
│  │ avg_time_to_fill     │ Float (dias médios)             │             │
│  │ embedding            │ Vector(768) — pgvector          │             │
│  └──────────────────────┴────────────────────────────────┘             │
│                                                                         │
│  Índices:                                                               │
│  ├─ ix_jp_company_type (company_id, pattern_type)                      │
│  ├─ ix_jp_company_title (company_id, job_title_normalized)             │
│  └─ HNSW index no embedding para busca semântica                       │
│                                                                         │
│  Uso em busca semântica:                                                │
│  → Embedding da nova vaga é comparado via cosine similarity            │
│  → Retorna padrões mais similares para sugerir skills, salário,        │
│    tempo de preenchimento esperado                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

**Onde é aplicado:**
- **Wizard Stage 2 (Skills)** → Sugere skills baseado em vagas históricas similares
- **Wizard Stage 3 (Salary)** → Sugere faixa salarial com base em percentis do padrão
- **Previsão de time-to-fill** → Alimenta OutcomePredictor com dados do cluster
- **JD Enrichment** → Enrichment service usa padrões para complementar JDs

#### 3.16.2 Template Learning Service

**Arquivo:** `app/shared/learning/template_learning_service.py`  
**Classe:** `TemplateLearningService`

Aprende com criação de vagas para enriquecer catálogos dinâmicos (skills por role, responsabilidades por cargo, etc.).

#### 3.16.3 Learning Hub — Hub Central de Aprendizagem

**Arquivo:** `app/services/learning_hub_service.py`  
**Classe:** `LearningHubService`  
**Threshold de promoção:** 3 confirmações (`PROMOTION_THRESHOLD`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│              LEARNING HUB — HUB CENTRAL UNIFICADO                       │
│                                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                │
│  │   WIZARD    │    │   AGENTS    │    │  OUTCOMES   │                │
│  │  (Stages    │    │ (Screening, │    │ (JobOutcome, │                │
│  │   1-7)      │    │  Sourcing,  │    │  WizardFeed- │                │
│  │             │    │  etc.)      │    │  back)       │                │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                │
│         │                   │                   │                       │
│         v                   v                   v                       │
│  ┌─────────────────────────────────────────────────────┐               │
│  │ LearningHubService                                   │               │
│  │                                                       │               │
│  │ record_skill_confirmation()                          │               │
│  │   → CompanySkill.times_confirmed++                   │               │
│  │   → Se times_confirmed >= 3 → PROMOTED              │               │
│  │     (aparece como sugestão default)                  │               │
│  │                                                       │               │
│  │ record_responsibility_confirmation()                 │               │
│  │   → CompanyResponsibility.times_confirmed++          │               │
│  │                                                       │               │
│  │ record_agent_feedback()                              │               │
│  │   → AgentFeedback (quality, corrections, context)    │               │
│  │                                                       │               │
│  │ get_learning_context(company_id, role, seniority)    │               │
│  │   → LearningContext com skills, responsabilities,    │               │
│  │     patterns e success_rates filtrados               │               │
│  └─────────────────────────────────────────────────────┘               │
│         │                                                               │
│         v                                                               │
│  ┌─────────────────────────────────────────────────────┐               │
│  │ Modelos de Dados (PostgreSQL)                        │               │
│  │                                                       │               │
│  │ CompanySkill       → skill_name, times_confirmed,    │               │
│  │                      skill_type, role, seniority,    │               │
│  │                      is_promoted, source             │               │
│  │                                                       │               │
│  │ CompanyResponsibility → responsibility_name,         │               │
│  │                          times_confirmed, role       │               │
│  │                                                       │               │
│  │ CompanyPattern     → pattern_type, key, data,        │               │
│  │                      confidence                      │               │
│  │                                                       │               │
│  │ AgentFeedback      → agent_id, action, quality,      │               │
│  │                      corrections, context            │               │
│  └─────────────────────────────────────────────────────┘               │
│                                                                         │
│  Confidence Thresholds:                                                 │
│  ├─ "high" → 10+ confirmações                                          │
│  ├─ "medium" → 5-9 confirmações                                        │
│  └─ "low" → 1-4 confirmações                                           │
│                                                                         │
│  LearningSource (enum):                                                 │
│  ├─ WIZARD_CONFIRMED → Confirmado pelo recrutador no wizard            │
│  ├─ WIZARD_CORRECTED → Corrigido pelo recrutador                       │
│  ├─ JD_IMPORTED → Extraído de JD importada                             │
│  ├─ TEMPLATE → Vindo de template curado                                │
│  └─ AGENT_SUGGESTED → Sugerido por agente de IA                       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 3.17 Predictive Analytics — 7 Tipos de Predição

**Arquivo:** `app/domains/analytics/services/predictive_analytics_service.py`  
**Classe:** `PredictiveAnalyticsService`

Serviço de analytics preditivo que gera predições acionáveis baseadas em dados históricos e heurísticas estatísticas.

```
┌─────────────────────────────────────────────────────────────────────────┐
│              7 TIPOS DE PREDIÇÃO                                        │
│                                                                         │
│  ┌──────────────────────┬────────────────────────────────────────────┐ │
│  │ PredictionType        │ Descrição                                  │ │
│  ├──────────────────────┼────────────────────────────────────────────┤ │
│  │ HIRING_PROBABILITY   │ Probabilidade de contratar candidato       │ │
│  │ TIME_TO_FILL         │ Tempo estimado para preencher vaga         │ │
│  │ DROPOUT_RISK         │ Risco de desistência do candidato          │ │
│  │ PIPELINE_FORECAST    │ Previsão de funil (conversão por etapa)    │ │
│  │ CULTURAL_FIT         │ Aderência cultural do candidato            │ │
│  │ SALARY_ACCEPTANCE    │ Probabilidade de aceitar oferta salarial   │ │
│  │ JOB_SUCCESS          │ Probabilidade de sucesso da vaga           │ │
│  └──────────────────────┴────────────────────────────────────────────┘ │
│                                                                         │
│  RiskLevel: LOW | MEDIUM | HIGH | CRITICAL                             │
└─────────────────────────────────────────────────────────────────────────┘
```

**Detalhamento do predict_hiring_probability():**

```
Fatores com pesos ponderados:
┌────────────────────────┬────────┬──────────────────────────────────────┐
│ Fator                   │ Peso   │ Cálculo                              │
├────────────────────────┼────────┼──────────────────────────────────────┤
│ wsi_score              │ 0.30   │ min(wsi/100, 1.0)                    │
│ experience_match       │ 0.20   │ min(exp_years/req_years, 1.5) / 1.5 │
│ skills_match           │ 0.15   │ % de skills obrigatórias atendidas   │
│ interview_performance  │ 0.15   │ avg_interview_score / 5.0            │
│ response_time          │ 0.10   │ Score baseado em tempo de resposta   │
│ cultural_signals       │ 0.10   │ Sinais de fit cultural               │
├────────────────────────┼────────┼──────────────────────────────────────┤
│ TOTAL                  │ 1.00   │ Soma ponderada → probabilidade       │
└────────────────────────┴────────┴──────────────────────────────────────┘
```

**Detalhamento do predict_dropout_risk():**

```
Fatores de risco de dropout:
├─ dropout_base weight = 0.15 → Risco base por tipo de perfil
├─ time_in_pipeline weight = 0.25 → Mais tempo = mais risco
├─ communication_frequency weight = 0.20 → Menos comunicação = mais risco
├─ response_time weight = 0.10 → Respostas mais lentas = mais risco
└─ Classificação: LOW (<30%), MEDIUM (30-60%), HIGH (60-80%), CRITICAL (>80%)
```

**Onde é aplicado:**
- **Pipeline Kanban** → Badges de risco por candidato (dropout_risk, hiring_probability)
- **Alertas Proativos** → ProactiveAlertService usa dropout_risk para gerar alertas
- **Dashboard KPIs** → Métricas preditivas no painel de analytics
- **Decisões de IA** → Agentes usam probabilidades para priorizar ações

---

### 3.18 Automação Inteligente — Engine, Triggers, Scheduler e Alertas Proativos

#### 3.18.1 Stage Automation Engine

**Arquivo:** `app/domains/automation/services/stage_automation_engine.py`  
**Classe:** `StageAutomationEngine`

Engine central de automação que processa eventos de trigger, avalia regras por empresa, e executa ou sugere ações.

```
┌─────────────────────────────────────────────────────────────────────────┐
│           STAGE AUTOMATION ENGINE — 16 TRIGGERS                         │
│                                                                         │
│  TriggerType (enum):                                                    │
│  ├─ SCREENING_COMPLETED    │ Triagem WSI finalizada                    │
│  ├─ INTERVIEW_SCHEDULED    │ Entrevista agendada                       │
│  ├─ INTERVIEW_COMPLETED    │ Entrevista concluída                      │
│  ├─ CANDIDATE_INACTIVE     │ Candidato inativo por período             │
│  ├─ CANDIDATE_NO_SHOW      │ Candidato não compareceu                  │
│  ├─ OFFER_SENT             │ Oferta enviada                            │
│  ├─ CANDIDATE_HIRED        │ Candidato contratado                      │
│  ├─ CANDIDATE_REJECTED     │ Candidato rejeitado                       │
│  ├─ ATS_SYNC               │ Sincronização com ATS externo             │
│  ├─ STAGE_CHANGED          │ Etapa do pipeline alterada                │
│  ├─ CANDIDATE_APPLIED      │ Nova candidatura recebida                 │
│  ├─ NO_RESPONSE_48H        │ Sem resposta há 48 horas                  │
│  ├─ FEEDBACK_RECEIVED      │ Feedback de entrevistador recebido        │
│  ├─ DEADLINE_APPROACHING   │ Prazo se aproximando                      │
│  ├─ JOB_PUBLISHED          │ Vaga publicada                            │
│  └─ CANDIDATES_SOURCED     │ Candidatos sourced (Pearch/interno)       │
│                                                                         │
│  Fluxo de Processamento:                                                │
│  ┌──────────┐   ┌────────────┐   ┌──────────────────┐                 │
│  │ Evento   │──▸│ Validação  │──▸│ Avaliar Regras   │                 │
│  │ recebido │   │ Multi-     │   │ da empresa       │                 │
│  └──────────┘   │ Tenancy    │   │ (conditions)     │                 │
│                  └────────────┘   └────────┬─────────┘                 │
│                                            │                            │
│                         ┌─────────────────┬┘                           │
│                         │                 │                             │
│                    auto_execute?      create suggestion                 │
│                         │                 │                             │
│                  ┌──────▼──────┐   ┌──────▼──────┐                    │
│                  │ Executar    │   │ Criar suges-│                    │
│                  │ handler     │   │ tão para    │                    │
│                  │ diretamente │   │ aprovação   │                    │
│                  └──────┬──────┘   └──────┬──────┘                    │
│                         │                 │                             │
│                         └────────┬────────┘                            │
│                                  ▼                                      │
│                           Audit Log                                     │
│                                                                         │
│  Condições avaliáveis:                                                  │
│  ├─ min_wsi_score → Score WSI mínimo                                   │
│  ├─ stages → Etapa específica do pipeline                              │
│  ├─ min_confidence → Confiança mínima da IA                            │
│  ├─ source_types → Tipo de fonte (interno, Pearch, etc.)               │
│  └─ min_cv_score → Score mínimo de CV                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 3.18.2 Automation Scheduler

**Arquivo:** `app/domains/automation/services/automation_scheduler.py`  
**Classe:** `AutomationScheduler`  
**Dependência:** APScheduler (CronTrigger + IntervalTrigger)

Executa jobs periódicos para verificar condições e disparar automações:

| Job agendado | Frequência | Função |
|---|---|---|
| Candidatos inativos | Intervalo | Detecta candidatos com 7+ dias sem atividade |
| Interview no-shows | Intervalo | Detecta entrevistas não comparecidas |
| Deadline approaching | Diário | Verifica prazos de vagas se aproximando |
| Candidate no-response | Intervalo | Detecta 48h+ sem resposta de candidato |
| Stage stagnation | Diário | Candidatos parados na mesma etapa há muito tempo |

#### 3.18.3 Automation Trigger Service

**Arquivo:** `app/domains/automation/services/automation_trigger_service.py`  
**Classe:** `AutomationTriggerService`

Gerencia regras de automação condicionais por empresa (criação, ativação, desativação, avaliação de condições).

#### 3.18.4 Proactive Alert Service — 5 Categorias de Alertas Inteligentes

**Arquivo:** `app/domains/automation/services/proactive_alert_service.py`  
**Classe:** `ProactiveAlertService`

```
┌─────────────────────────────────────────────────────────────────────────┐
│          SISTEMA DE ALERTAS PROATIVOS — 5 CATEGORIAS                    │
│                                                                         │
│  PIPELINE (saúde do funil):                                             │
│  ├─ CONVERSION_RATE_LOW → Conversão <5%, cooldown 24h                  │
│  ├─ CANDIDATES_STAGNANT → 5+ candidatos parados há 10+ dias           │
│  ├─ OFFERS_PENDING_LONG → Oferta sem resposta há 72h (URGENT)         │
│  └─ PIPELINE_EMPTY → Menos de 3 candidatos ativos (URGENT)            │
│                                                                         │
│  PRODUCTIVITY (produtividade do recrutador):                            │
│  ├─ TASKS_OVERDUE → 5+ tarefas atrasadas (URGENT)                     │
│  ├─ NO_ACTIVITY → Sem atividade há 2h (INFO)                          │
│  ├─ DAILY_GOAL_RISK → <50% meta às 16h (WARNING)                      │
│  └─ SCORECARDS_PENDING → Scorecards de entrevista pendentes           │
│                                                                         │
│  COMMUNICATION (saúde de comunicação):                                  │
│  ├─ EMAIL_DELIVERY_LOW → Taxa de entrega baixa                        │
│  ├─ CANDIDATES_NO_RESPONSE → Candidatos sem resposta                  │
│  └─ HIGH_OPT_OUT → Taxa alta de opt-out                               │
│                                                                         │
│  PREDICTIVE (insights preditivos):                                      │
│  ├─ DROPOUT_RISK_HIGH → Risco alto de desistência                     │
│  ├─ TIME_TO_FILL_RISK → Vaga em risco de SLA                          │
│  ├─ IDEAL_CANDIDATE_FOUND → Candidato ideal detectado                 │
│  └─ REJECTION_PATTERN → Padrão de rejeição detectado                  │
│                                                                         │
│  SYSTEM (saúde do sistema):                                             │
│  ├─ ATS_SYNC_FAILED → Falha na sincronização ATS                      │
│  ├─ AGENT_HEALTH_LOW → Agente de IA com health baixo                  │
│  ├─ CREDITS_LOW → Créditos de IA acabando                             │
│  └─ AI_DECISION_ERROR → Erro em decisão de IA                         │
│                                                                         │
│  Cada alerta tem:                                                       │
│  ├─ threshold configurável                                              │
│  ├─ severity (INFO, WARNING, URGENT)                                   │
│  └─ cooldown_hours (evita repetição)                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 3.18.5 Autonomous Agent Service

**Arquivo:** `app/domains/automation/services/autonomous_agent_service.py`  
**Classe:** `AutonomousAgentService`

Gerencia agentes autônomos que executam tarefas em background sem intervenção do recrutador.

```
┌─────────────────────────────────────────────────────────────────────────┐
│          SISTEMA DE AGENTES AUTÔNOMOS                                   │
│                                                                         │
│  BackgroundJob (model):                                                 │
│  ├─ company_id: UUID (multi-tenant)                                    │
│  ├─ job_type: str (screening, sourcing, communication, etc.)           │
│  ├─ name: str (nome legível)                                           │
│  ├─ config: JSON (parâmetros do job)                                   │
│  ├─ schedule: str (cron expression para recorrência)                   │
│  ├─ status: JobStatus (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED) │
│  ├─ progress: int (0-100%)                                             │
│  ├─ run_count: int                                                      │
│  └─ next_run_at: datetime (próxima execução agendada)                  │
│                                                                         │
│  ProactiveAction (model):                                               │
│  ├─ company_id: UUID                                                    │
│  ├─ action_type: str (suggest, alert, automate)                        │
│  ├─ status: ActionStatus (PENDING, ACCEPTED, REJECTED, EXECUTED)       │
│  ├─ priority: ActionPriority (LOW, MEDIUM, HIGH, CRITICAL)             │
│  └─ Workflow: Sistema SUGERE → Recrutador ACEITA/REJEITA → Executa    │
│                                                                         │
│  Fluxo:                                                                 │
│  1. create_job() → Cria job com config e schedule                      │
│  2. Scheduler dispara no next_run_at                                    │
│  3. Job executa (ex: triagem de novos candidatos)                      │
│  4. Se resultado requer ação → cria ProactiveAction                    │
│  5. Recrutador vê sugestão → aceita/rejeita                           │
│  6. Se aceita → executa ação automaticamente                           │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 3.18.6 Execution Plan — Planos Multi-Step

**Arquivo:** `app/shared/execution/execution_plan.py`  
**Classes:** `ExecutionPlan`, `AgentTask`

```
┌─────────────────────────────────────────────────────────────────────────┐
│          EXECUTION PLAN — TAREFAS MULTI-STEP                            │
│                                                                         │
│  AgentTask:                                                             │
│  ├─ task_id: str (UUID)                                                │
│  ├─ domain_id: str (qual domínio executa)                              │
│  ├─ action_id: str (qual action executar)                              │
│  ├─ params: Dict (parâmetros da action)                                │
│  ├─ depends_on: List[str] (IDs de tasks que precisam completar antes)  │
│  ├─ status: PENDING | RUNNING | COMPLETED | FAILED | SKIPPED          │
│  ├─ retry_count / max_retries: int (retry automático)                  │
│  ├─ is_critical: bool (se falhar, aborta o plano)                      │
│  └─ context_mappings: Dict (output de task A → input de task B)        │
│                                                                         │
│  ExecutionPlan:                                                         │
│  ├─ plan_id: str                                                        │
│  ├─ tasks: List[AgentTask]                                             │
│  ├─ status: PENDING | IN_PROGRESS | COMPLETED | PARTIAL | FAILED      │
│  └─ Execução respeita depends_on (DAG topológico)                      │
│                                                                         │
│  PlanDetector (app/shared/execution/plan_detector.py):                 │
│  → Detecta automaticamente quando uma requisição precisa               │
│    de múltiplas ações coordenadas e gera ExecutionPlan                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 3.19 Inteligência Contextual — Extração, RAG, WRF Dinâmico e Inferência

#### 3.19.1 SmartExtractor — Extração Inteligente de Parâmetros

**Arquivo:** `app/shared/intelligence/smart_extractor.py`  
**Classes:** `ParamExtractor`, `ExtractionCache`

```
┌─────────────────────────────────────────────────────────────────────────┐
│          SMART EXTRACTOR — REGEX + LLM FALLBACK                         │
│                                                                         │
│  Mensagem do recrutador (texto natural)                                 │
│       ↓                                                                 │
│  1. ExtractionCache.get() → Verifica cache (TTL 300s, max 200 entries) │
│       ↓ (cache miss)                                                    │
│  2. ParamExtractor.extract()                                            │
│       ├─ Para cada ParamPattern no domínio:                            │
│       │   ├─ Aplica regex patterns (re.finditer)                       │
│       │   ├─ Extrai valor pelo group_index                             │
│       │   └─ Normaliza via normalize_fn                                │
│       ├─ Se regex encontrou → source="regex", confidence alta          │
│       └─ Se regex falhou → LLM fallback (source="llm")                │
│       ↓                                                                 │
│  3. ExtractedParams { params, source, confidence, cached,              │
│                       extraction_time_ms, extraction_details }          │
│       ↓                                                                 │
│  4. ExtractionCache.set() → Armazena resultado                        │
│                                                                         │
│  Cache key = MD5(domain_id + normalized_query)                         │
│  Eviction: LRU quando max_entries atingido                             │
│                                                                         │
│  Patterns organizados por domínio via get_patterns_for_domain()        │
│  + UNIVERSAL_PATTERNS (aplicados em todos os domínios)                  │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 3.19.2 RAG Service — Retrieval-Augmented Generation

**Arquivo:** `app/services/rag_service.py`  
**Classe:** `RAGService`

```
┌─────────────────────────────────────────────────────────────────────────┐
│          RAG SERVICE — GERAÇÃO AUMENTADA POR RECUPERAÇÃO                │
│                                                                         │
│  Query do recrutador                                                    │
│       ↓                                                                 │
│  augment_with_context(query, session_id, company_id):                  │
│       ↓                                                                 │
│  ┌─── 3 fontes de contexto (paralelas) ────────────────┐              │
│  │                                                       │              │
│  │ 1. Conversation History (limit=10)                   │              │
│  │    → memory_service.get_conversation_context()       │              │
│  │    → Histórico da sessão atual                       │              │
│  │                                                       │              │
│  │ 2. Similar Messages (limit=5, min_similarity=0.7)    │              │
│  │    → memory_service.search_similar_messages()        │              │
│  │    → Mensagens de OUTRAS sessões semanticamente      │              │
│  │      similares (exclui sessão atual)                 │              │
│  │                                                       │              │
│  │ 3. Knowledge Base (limit=5, min_similarity=0.6)      │              │
│  │    → memory_service.search_knowledge_base()          │              │
│  │    → Documentos da base de conhecimento da empresa   │              │
│  │    → Filtrado por document_types se especificado     │              │
│  └──────────────────────────────────────────────────────┘              │
│       ↓                                                                 │
│  RAGContext {                                                           │
│    conversation_history, similar_messages,                              │
│    knowledge_base_docs, formatted_context                              │
│  }                                                                      │
│       ↓                                                                 │
│  formatted_context alimenta o prompt do LLM                            │
│  (adicionado como contexto antes da mensagem do recrutador)            │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 3.19.3 WRF Dynamic K — Ajuste Dinâmico de Diversidade na Busca

**Arquivo:** `app/services/wrf_dynamic_k_service.py`  
**Classe:** `WRFDynamicKService`

O parâmetro K no Weighted Rank Fusion controla o trade-off entre precisão e diversidade dos resultados. K é ajustado dinamicamente conforme o nível de qualificação da vaga:

```
┌─────────────────────────────────────────────────────────────────────────┐
│          WRF DYNAMIC K — K POR NÍVEL DE QUALIFICAÇÃO                    │
│                                                                         │
│  ┌──────────────┬────────┬─────────────┬──────────────────────────┐    │
│  │ Qualificação │ K      │ ES Weight   │ Comportamento             │    │
│  ├──────────────┼────────┼─────────────┼──────────────────────────┤    │
│  │ Alta         │ 25     │ ES=0.6      │ Mais preciso, menos      │    │
│  │              │        │ PGV=0.4     │ diverso. Prioriza match  │    │
│  │              │        │             │ exato de skills.          │    │
│  ├──────────────┼────────┼─────────────┼──────────────────────────┤    │
│  │ Média        │ 45     │ ES=0.5      │ Equilíbrio entre         │    │
│  │              │        │ PGV=0.5     │ precisão e diversidade.  │    │
│  ├──────────────┼────────┼─────────────┼──────────────────────────┤    │
│  │ Baixa        │ 70     │ ES=0.4      │ Mais diverso. Busca      │    │
│  │              │        │ PGV=0.6     │ semântica pesa mais.     │    │
│  └──────────────┴────────┴─────────────┴──────────────────────────┘    │
│                                                                         │
│  Configurável via env vars: WRF_K_ALTA, WRF_K_MEDIA, WRF_K_BAIXA     │
│                                                                         │
│  Onde é aplicado:                                                       │
│  → Busca de candidatos no Talent Funnel (ES + PGV + WRF)              │
│  → Sourcing automático de candidatos                                   │
│  → Candidate matching para vagas novas                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 3.19.4 Market Benchmark Service — Salários de Mercado via Web Search

**Arquivo:** `app/services/market_benchmark_service.py`  
**Classe:** `MarketBenchmarkService`  
**API:** SerpAPI para busca web + LLM para parsing de resultados

```
Fluxo:
1. Recrutador pede benchmark salarial para role+seniority+location
2. Cache in-memory verificado (TTL configurável)
3. Se cache miss → SerpAPI busca salários públicos (Glassdoor, Indeed, etc.)
4. LLM parseia resultados brutos e extrai faixas salariais estruturadas
5. Resultado inclui source attribution (transparência)
6. Cache atualizado para consultas futuras

Output:
├─ suggested_min, suggested_max (faixa recomendada)
├─ market_percentile (onde a faixa proposta se posiciona)
├─ sources: List[str] (fontes citadas)
└─ competitive_analysis: str (análise textual)
```

#### 3.19.5 Manager Inference Service

**Arquivo:** `app/services/manager_inference_service.py`  
**Classe:** `ManagerInferenceService`

Infere automaticamente o gestor responsável por uma vaga baseado na estrutura departamental da empresa, evitando que o recrutador precise buscar manualmente.

#### 3.19.6 Infer Behavior Service — Inferência de Comportamento de Etapas Custom

**Arquivo:** `app/domains/communication/services/infer_behavior_service.py`  
**Classe:** `InferBehaviorService`

Quando o recrutador cria etapas customizadas no pipeline (ex: "Teste Técnico de Python"), o sistema infere automaticamente qual `action_behavior` associar:

```
Inferência por keywords com scoring:
├─ "screening" → triagem(0.95), screening(0.95), pré-seleção(0.90), filtro(0.80)
├─ "scheduling" → entrevista(0.95), reunião(0.85), agendamento(0.90), dinâmica(0.85)
└─ "evaluation" → teste(0.95), avaliação(0.90), case(0.85), desafio(0.85), técnico(0.70)

Se keywords não forem suficientes → LLM fallback para classificação
```

#### 3.19.7 Interpret Context LLM — Interpretação de Mini-Prompts

**Arquivo:** `app/domains/communication/services/interpret_context_llm_service.py`  
**Classe:** `InterpretContextLLMService`

Quando o recrutador move candidatos no pipeline e digita instruções em texto livre (mini-prompt), o sistema usa Claude para interpretar e extrair informações estruturadas:

```
Input: "Agendar entrevista com João para segunda às 14h, presencial na sede"

Output (JSON estruturado):
├─ action: "schedule_interview"
├─ datetime: "próxima segunda 14:00"
├─ location: "sede"
├─ format: "presencial"
└─ notes: null

Fallback: Se LLM falhar → rule-based extraction (regex)
```

#### 3.19.8 Suggestion Interaction Service

**Arquivo:** `app/services/suggestion_interaction_service.py`  
**Classe:** `SuggestionInteractionService`

Processa interações do recrutador com sugestões da LIA durante o wizard, usando regex (zero latência, sem chamadas LLM):

```
Tipos de interação detectados:
├─ ACCEPT → "aceito", "pode adicionar", "sim, quero"
├─ REJECT → "não quero", "remover", "tirar"
├─ REPLACE → "trocar X por Y", "substituir"
└─ ADJUST_LEVEL → "mudar para obrigatório", "tornar desejável"

Usa SequenceMatcher para fuzzy matching de nomes de skills.
```

---

### 3.20 Análise Multimodal e Voz

#### 3.20.1 MultimodalService — Claude Vision + Gemini Video + PDF

**Arquivo:** `app/services/multimodal_service.py`  
**Classe:** `MultimodalService`

```
┌─────────────────────────────────────────────────────────────────────────┐
│          ANÁLISE MULTIMODAL — 3 PROVEDORES                              │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │ CLAUDE VISION (Anthropic)                                    │       │
│  │ API: api.anthropic.com/v1/messages                          │       │
│  │ Formatos: jpg, jpeg, png, gif, webp                         │       │
│  │                                                              │       │
│  │ Prompts especializados:                                      │       │
│  │ ├─ "general" → Análise geral de imagem (5 critérios)       │       │
│  │ ├─ "resume" → Análise de CV visual (layout 1-10, org.,     │       │
│  │ │              fontes, seções, aparência profissional)       │       │
│  │ ├─ "document" → Análise de documento (tipo, texto,          │       │
│  │ │                seções, logos, formatação)                   │       │
│  │ └─ "professional_photo" → Foto profissional (qualidade,    │       │
│  │                           fundo, vestimenta, score 1-10)     │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │ GEMINI (Google)                                              │       │
│  │ API: generativelanguage.googleapis.com/v1beta                │       │
│  │                                                              │       │
│  │ Prompts especializados:                                      │       │
│  │ ├─ "interview_video" → Análise de entrevista em vídeo      │       │
│  │ │   (body language, eye contact, confiança, fala,            │       │
│  │ │    aparência, presença, score 1-10)                        │       │
│  │ └─ "presentation_video" → Análise de apresentação           │       │
│  │     (presença, estrutura, visual aids, energia, score 1-10) │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │ PDF EXTRACTION                                               │       │
│  │ Formatos: pdf, jpg, jpeg, png, webp                         │       │
│  │ → Extração de texto + análise visual via Claude Vision      │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
│  Onde é aplicado:                                                       │
│  ├─ Upload de CV → resume prompt → layout_score + seções extraídas   │
│  ├─ Foto de candidato → professional_photo → professionalism_score    │
│  ├─ Vídeo de entrevista → interview_video → body_language_score       │
│  ├─ Documentos de candidato → document → extração estruturada         │
│  └─ Apresentação técnica → presentation_video → effectiveness_score   │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 3.20.2 Voice Service + WSI Voice Orchestrator

**Arquivo:** `app/services/voice_service.py`  
**Classe:** `VoiceService`

```
┌─────────────────────────────────────────────────────────────────────────┐
│          PROCESSAMENTO DE VOZ — SPEECH-TO-TEXT + TEXT-TO-SPEECH          │
│                                                                         │
│  TRANSCRIÇÃO (Speech-to-Text):                                          │
│  ├─ PRIMARY: Deepgram Nova-2                                           │
│  │   API: api.deepgram.com/v1/listen                                   │
│  │   Features: smart_format, punctuate, utterances                     │
│  │   Idioma: pt-BR (padrão)                                           │
│  │                                                                      │
│  └─ FALLBACK: OpenAI Whisper                                           │
│      API: api.openai.com/v1/audio/transcriptions                       │
│      Modelo: whisper-1                                                  │
│                                                                         │
│  SÍNTESE (Text-to-Speech):                                              │
│  ├─ Provider: OpenAI TTS                                               │
│  │   API: api.openai.com/v1/audio/speech                               │
│  │   Modelos: tts-1 (fast), tts-1-hd (quality)                        │
│  │   Vozes: alloy, echo, fable, onyx, nova, shimmer                   │
│  │                                                                      │
│  └─ Streaming: Suporte a streaming transcription via WebSocket         │
│                                                                         │
│  Formatos suportados: mp3, wav, webm, m4a, ogg, flac, mpeg            │
│                                                                         │
│  WSI Voice Orchestrator (wsi_voice_orchestrator.py):                   │
│  ├─ Orquestra screening WSI por voz                                    │
│  ├─ Candidato responde perguntas WSI via áudio                         │
│  ├─ VoiceService transcreve → WSI Scorer avalia                       │
│  └─ Resultado: WSI score + transcrição + analysis                      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 3.21 Robustez e Qualidade — Enhanced Base Agent + Validação + Normalização

#### 3.21.1 Enhanced Base Agent

**Arquivo:** `app/shared/robustness/enhanced_base.py`  
**Classe:** `EnhancedBaseAgent` (extends `BaseAgent`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│          ENHANCED BASE AGENT — CAMADA DE ROBUSTEZ                       │
│                                                                         │
│  Features built-in:                                                     │
│                                                                         │
│  1. DYNAMIC can_handle() baseado em IntentSchemas                      │
│     → Cada agente define IntentSchemas com:                            │
│       ├─ intent: str (nome do intent)                                  │
│       ├─ required_entities: List[EntityRequirement]                    │
│       ├─ optional_entities: List[EntityRequirement]                    │
│       └─ calculate_confidence(entities) → float                       │
│     → Router consulta can_handle() para selecionar melhor agente      │
│                                                                         │
│  2. AUTOMATIC Error Handling                                            │
│     → @handle_agent_errors decorator                                   │
│     → AgentError com AgentErrorCode tipado                             │
│     → create_user_friendly_error() traduz erros técnicos              │
│                                                                         │
│  3. INPUT Validation + Sanitization                                     │
│     → sanitize_text() remove XSS, SQL injection, etc.                 │
│     → detect_language() identifica idioma (pt-BR default)             │
│                                                                         │
│  4. CANCELLATION Detection                                              │
│     → CancellationHandler detecta se contexto foi cancelado           │
│     → ContextManager gerencia lifecycle do processamento              │
│                                                                         │
│  5. DEFENSIVE Prompts                                                   │
│     → get_clarification_message() para intents ambíguos               │
│     → get_out_of_scope_response() para requests fora do escopo        │
│     → get_defensive_prompt_section() adiciona guardrails ao prompt     │
│                                                                         │
│  6. TELEMETRY / Metrics                                                 │
│     → total_requests, successful_requests, failed_requests            │
│     → avg_response_time_ms, cancellations                              │
│                                                                         │
│  Hierarquia:                                                            │
│  BaseAgent → EnhancedBaseAgent → [AgentesEspecíficos]                 │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 3.21.2 Score Normalization Service

**Arquivo:** `app/domains/cv_screening/services/score_normalization_service.py`

Normaliza scores entre diferentes fontes (WSI, entrevista, CV, testes) para uma escala unificada, permitindo comparação justa entre candidatos avaliados por métodos diferentes.

#### 3.21.3 Input Validation e Error Handling

**Arquivos:**
- `app/shared/robustness/input_validation.py` → `sanitize_text()`, `detect_language()`, `SupportedLanguage`
- `app/shared/robustness/error_handling.py` → `@handle_agent_errors`, `AgentError`, `AgentErrorCode`, `create_user_friendly_error()`
- `app/shared/robustness/context_management.py` → `CancellationHandler`, `ContextManager`
- `app/shared/robustness/defensive_prompts.py` → Prompts defensivos para guardrails

Todas as interações de IA passam por esta camada de validação antes de atingir qualquer agente ou serviço.

---

### 3.22 Automação Progressiva — CompanyHiringPolicy e Níveis de Autonomia

> **Spec completa:** `plataforma-lia/docs/specs/hiring-policies-spec.md`  
> **Diagramas FigJam:**  
> - [Layout da tela](https://www.figma.com/online-whiteboard/create-diagram/804303f5-3a26-417b-8465-731a8dbd4a50?utm_source=other&utm_content=edit_in_figjam)  
> - [Fluxo de onboarding 19 perguntas](https://www.figma.com/online-whiteboard/create-diagram/b9190356-1ea6-4902-ad00-adf832672f81?utm_source=other&utm_content=edit_in_figjam)  
> - [Arquitetura 5 níveis](https://www.figma.com/online-whiteboard/create-diagram/b8f7d8b3-2dd5-4222-9de1-1ac20537b0e2?utm_source=other&utm_content=edit_in_figjam)  
> **Status:** Planejamento (21/02/2026)

#### 3.22.1 Motivação e Gap Arquitetural

A plataforma possui componentes de automação maduros (seção 3.18), mas **reativos** — só agem quando o recrutador configura manualmente regras ou clica em botões. A LIA não conhece as políticas de contratação da empresa, tornando-a genérica em vez de personalizada.

**Gaps identificados na análise de mercado (Ashby, Lever, Greenhouse, Paradox):**

| Gap | Descrição | Impacto |
|-----|-----------|---------|
| LIA reativa | Só age quando perguntada, não monitora proativamente | Alto |
| Execução multi-step frágil | Não há plano de ação robusto com retry/rollback | Médio |
| Learning loop passivo | Feedback capturado mas não recalibra comportamento | Alto |
| Predições não acionáveis | `OutcomePredictor` calcula mas não sugere ações | Médio |
| Sem políticas por empresa | Todos os tenants tratados com mesmos defaults | Alto |

#### 3.22.2 CompanyHiringPolicy — Modelo de Dados

**Tabela:** `company_hiring_policies` (1 registro por empresa)

```
CompanyHiringPolicy
├── id (UUID, PK)
├── company_id (String, unique, indexed)
├── updated_at, updated_by, setup_progress (0-100%)
│
├── pipeline_rules (JSON)
│   ├── min_interviews_before_offer: int | null
│   ├── manager_approval_for_offer: bool | null
│   ├── max_days_in_stage: {stage_id: days} | null
│   └── pipeline_templates: [] (referência informativa)
│
├── scheduling_rules (JSON)
│   ├── allowed_days: ["mon","tue",...] | null
│   ├── allowed_hours: {start: "09:00", end: "18:00"} | null
│   ├── default_duration_minutes: int | null
│   └── self_scheduling_enabled: bool | null
│
├── communication_rules (JSON)
│   ├── auto_rejection_feedback: bool | null
│   ├── rejection_feedback_deadline_hours: int | null
│   ├── preferred_channel: "whatsapp" | "email" | "both" | null
│   └── lia_tone: "professional" | "friendly" | "formal" | null
│
├── screening_rules (JSON)
│   ├── salary_expectation_filter: bool | null
│   ├── salary_tolerance_percent: int | null
│   ├── experience_policy: "per_job" | "company_wide" | null
│   └── default_screening_questions: [question_id] | []
│
├── automation_rules (JSON)
│   ├── auto_screening: bool | null
│   ├── auto_scheduling: bool | null
│   ├── auto_stage_advance: bool | null
│   └── autonomy_level: "low" | "medium" | "high" | null
│
└── learned_patterns (JSON) → preenchido automaticamente pela LIA
```

**Integração com modelos existentes:**

| Modelo | Campo | Mapeamento |
|--------|-------|------------|
| `RecruitmentStage` | `sla_hours` | `max_days_in_stage` × 24h (via `PolicySyncService`) |
| `RecruitmentStage` | `auto_advance_rules` | Toggle global `auto_stage_advance` habilita/desabilita regras per-stage |
| `ScreeningQuestion` | company-scoped | `default_screening_questions` → IDs auto-adicionados a novas vagas |
| Feature Flags | `ENABLE_AUTO_*` | Cada toggle de automação mapeia para flag `ENABLE_AUTO_{tipo}_{company_id}` |

**Acesso pelos agentes/serviços:**

```python
async def get_company_policy(company_id: str) -> CompanyHiringPolicy:
    """Retorna as políticas da empresa ou defaults se não configurado."""
    policy = await db.query(CompanyHiringPolicy).filter_by(company_id=company_id).first()
    if not policy:
        return CompanyHiringPolicy(company_id=company_id)  # defaults (todos null)
    return policy
```

#### 3.22.3 Onboarding Conversacional — 19 Perguntas em 5 Blocos

A configuração é feita via conversa natural com a LIA (mesma UX do Wizard de Criação de Vagas), dentro de **Configurações → Políticas de Contratação**. Não é obrigatório — a empresa funciona normalmente sem configurar.

```
┌─────────────────────────────────────────────────────────────────┐
│  FLUXO DE ONBOARDING CONVERSACIONAL                             │
│                                                                  │
│  Bloco 1: Pipeline e Processo (4 perguntas)                     │
│  ├─ Q1: Mín. entrevistas antes de proposta                     │
│  ├─ Q2: Aprovação gestor para proposta                         │
│  ├─ Q3: Tempo máximo por etapa (→ sla_hours)                   │
│  └─ Q4: Tipos de vagas com processos diferentes                │
│         │                                                        │
│         ▼ "Quer continuar?" → Sim/Não (resposta no chat)        │
│                                                                  │
│  Bloco 2: Agendamento (4 perguntas)                             │
│  ├─ Q5: Dias permitidos                                        │
│  ├─ Q6: Horários permitidos                                    │
│  ├─ Q7: Duração padrão                                         │
│  └─ Q8: Auto-agendamento pelo candidato                        │
│         │                                                        │
│         ▼ "Quer continuar?" → Sim/Não                           │
│                                                                  │
│  Bloco 3: Comunicação (4 perguntas)                             │
│  ├─ Q9: Feedback automático para reprovados                    │
│  ├─ Q10: Prazo para feedback                                   │
│  ├─ Q11: Canal preferido (WhatsApp/Email)                      │
│  └─ Q12: Tom da LIA (profissional/amigável/formal)             │
│         │                                                        │
│         ▼ "Quer continuar?" → Sim/Não                           │
│                                                                  │
│  Bloco 4: Triagem (3 perguntas)                                 │
│  ├─ Q13: Filtro por pretensão salarial                         │
│  ├─ Q14: Experiência mínima (per-job ou empresa)               │
│  └─ Q15: Perguntas padrão para todas as vagas                  │
│         │                                                        │
│         ▼ "Quer continuar?" → Sim/Não                           │
│                                                                  │
│  Bloco 5: Autonomia da LIA (4 perguntas)                        │
│  ├─ Q16: Triagem automática                                    │
│  ├─ Q17: Agendamento automático                                │
│  ├─ Q18: Mover etapa automático                                │
│  └─ Q19: Nível geral (baixo/médio/alto)                        │
│                                                                  │
│  → Configuração salva (parcial ou completa)                     │
│  → Recrutador pode voltar e ajustar a qualquer momento          │
└─────────────────────────────────────────────────────────────────┘
```

**Regras de condução:**
- A LIA agrupa perguntas por bloco, confirmando entre blocos
- Permite pular perguntas ("Não sei ainda" → mantém null → default genérico)
- Entende respostas naturais: "Terça a quinta" → `["tue","wed","thu"]`
- Valores preenchidos atualizam o painel de políticas em tempo real

#### 3.22.4 UX — Reaproveitamento do Wizard de Vagas

A tela segue **exatamente o mesmo padrão** do Wizard de Criação de Vagas:

```
┌────────────────────────────────────────────────────────────┐
│  ⚙ Configurações                                          │
│  [Empresa] [Equipe] [Integrações] [●Políticas] [Billing]  │
│                                                            │
│  ┌────────────────────┐   ┌────────────────────────────┐  │
│  │  CHAT LIA (~40%)   │   │  PAINEL POLÍTICAS (~60%)   │  │
│  │                     │   │                            │  │
│  │  Mesmo componente   │   │  Tab: Informações          │  │
│  │  de chat do wizard  │   │  registradas               │  │
│  │  de vagas           │   │                            │  │
│  │                     │   │  ┌──────────────────────┐  │  │
│  │  ┌───────────────┐  │   │  │ Pipeline e Processo  │  │  │
│  │  │ Bot: Olá!     │  │   │  │ ✓ Min entrev: 2     │  │  │
│  │  │ Vou te ajudar │  │   │  │ ✓ Aprovação: Sim    │  │  │
│  │  │ a configurar..│  │   │  │ — SLA: não config.   │  │  │
│  │  └───────────────┘  │   │  └──────────────────────┘  │  │
│  │                     │   │  ┌──────────────────────┐  │  │
│  │  ┌───────────────┐  │   │  │ Agendamento          │  │  │
│  │  │ User: Vamos!  │  │   │  │ — Não configurado    │  │  │
│  │  └───────────────┘  │   │  └──────────────────────┘  │  │
│  │                     │   │  ┌──────────────────────┐  │  │
│  │  [Digite...]  [➤]  │   │  │ Comunicação          │  │  │
│  └────────────────────┘   │  └──────────────────────┘  │  │
│                            │  ┌──────────────────────┐  │  │
│                            │  │ Triagem              │  │  │
│                            │  └──────────────────────┘  │  │
│                            │  ┌──────────────────────┐  │  │
│                            │  │ Autonomia da LIA     │  │  │
│                            │  └──────────────────────┘  │  │
│                            └────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

**Componentes reutilizados do wizard:**
- Chat thread (bolhas de mensagem, input, send button)
- Painel lateral com cards colapsáveis
- Barra de progresso
- Preenchimento em tempo real via resposta da LIA

**Diferença:** No wizard de vagas os dados são per-job; nas políticas são globais da empresa e persistentes.

#### 3.22.5 Cinco Níveis de Automação Progressiva

A arquitetura evolui progressivamente, cada nível construindo sobre o anterior:

```
┌─────────────────────────────────────────────────────────────────────┐
│  AUTOMAÇÃO PROGRESSIVA — 5 NÍVEIS                                    │
│                                                                       │
│  Nível 1: AUTO-TRANSITION RULES                                     │
│  ├─ "Quando [evento], mover para [etapa]"                           │
│  ├─ Usa: StageAutomationEngine + CompanyHiringPolicy                │
│  ├─ Status: PARCIAL (engine existe, falta conectar com policy)      │
│  └─ Referência: Ashby (Auto-Advance Rules)                          │
│                                                                       │
│  Nível 2: SMART SUGGESTIONS                                         │
│  ├─ LIA monitora pipeline continuamente e sugere ações              │
│  ├─ Usa: ProactiveAlertService + AutonomousAgentService             │
│  ├─ Status: PARCIAL (serviços existem, falta loop ativo)            │
│  └─ Referência: Lever (Smart Nudges)                                │
│                                                                       │
│  Nível 3: BATCH INTELLIGENCE                                        │
│  ├─ LIA agrupa candidatos similares e propõe ações em lote          │
│  ├─ Usa: CandidateContextAggregator + bulk actions                  │
│  ├─ Status: PARCIAL (componentes existem, falta clustering)         │
│  └─ Referência: Greenhouse (Batch Actions + AI)                     │
│                                                                       │
│  Nível 4: PREDICTIVE PIPELINE                                       │
│  ├─ ML prediz outcomes e sugere pular/acelerar etapas               │
│  ├─ Usa: OutcomePredictor + PredictiveAnalytics                     │
│  ├─ Status: PARCIAL (calcula mas não aciona sugestões)              │
│  └─ Referência: Eightfold (Predictive Talent Intelligence)          │
│                                                                       │
│  Nível 5: AUTONOMOUS PIPELINE                                       │
│  ├─ LIA opera sozinha nas etapas configuradas                       │
│  ├─ Usa: PolicyEngine + feature flags + todas as camadas acima      │
│  ├─ Status: FUTURO (requer todos os níveis anteriores)              │
│  └─ Referência: Paradox (Olivia — autonomous scheduling/screening)  │
│                                                                       │
│  REGRA DE SEGURANÇA: Propostas e contratações NUNCA são 100%        │
│  automáticas, independente do nível. LIA sempre pede confirmação.   │
└─────────────────────────────────────────────────────────────────────┘
```

#### 3.22.6 Mapeamento: Nível de Autonomia → Feature Flags

O campo `autonomy_level` (pergunta 19) traduz-se em comportamentos concretos:

| Nível | Triagem | Agendamento | Mover etapa | Feedback reprovação | Propostas |
|---|---|---|---|---|---|
| `"low"` | LIA apresenta → recrutador decide | LIA sugere → recrutador confirma | Nunca auto | LIA prepara → recrutador envia | Manual |
| `"medium"` | Auto se toggle ativo | Auto se toggle ativo | Auto baixo impacto | Auto se toggle ativo | Confirmação |
| `"high"` | Sempre auto | Sempre auto | Auto exceto proposta | Sempre auto | Confirmação |

**Mapeamento para feature flags:**

```
"low"    → ENABLE_AUTO_{SCREENING|SCHEDULING|STAGE_ADVANCE|REJECTION_FEEDBACK}_{company_id} = false
"medium" → Usa toggles individuais (Q16-Q18 + Q9), sem override
"high"   → Todos os ENABLE_AUTO_* = true (override), exceto ENABLE_AUTO_OFFER = false
```

#### 3.22.7 Motor de Decisão com Confiança Calculada

```
┌──────────────────────────────────────────────────────────┐
│  MOTOR DE DECISÃO DA LIA (por ação)                       │
│                                                            │
│  Entradas:                                                 │
│  ├─ Regras explícitas (CompanyHiringPolicy)   peso: 1.0   │
│  ├─ Padrões aprendidos (learned_patterns)     peso: 0.7   │
│  └─ Defaults genéricos (plataforma)           peso: 0.3   │
│                                                            │
│  Saída: confiança calculada (0.0 — 1.0)                   │
│                                                            │
│  Decisão:                                                  │
│  ├─ confiança > 0.9 + autonomia high                      │
│  │   → Executa ação automaticamente + notifica             │
│  ├─ confiança > 0.7 + autonomia medium                    │
│  │   → Sugere no chat + pede confirmação                  │
│  └─ confiança < 0.7 OU autonomia low                      │
│      → Apenas informa, recrutador age manualmente          │
│                                                            │
│  Feedback loop:                                            │
│  ├─ Recrutador aceitou sugestão → reforça padrão (+0.05)  │
│  ├─ Recrutador rejeitou → reduz peso (-0.1)               │
│  └─ Recrutador alterou → aprende variação nova            │
└──────────────────────────────────────────────────────────┘
```

#### 3.22.8 Fases de Implementação

| Fase | Escopo | Esforço | Dependências |
|------|--------|---------|--------------|
| **Fase 1** | Modelo `CompanyHiringPolicy` + API CRUD + tela Configurações (layout wizard) | Médio | Migration, frontend tab, reutilizar componentes do wizard |
| **Fase 2** | Roteiro 19 perguntas no chat + preenchimento em tempo real do painel | Médio | Fase 1, intent classification para respostas naturais |
| **Fase 3** | Agentes consultam policy antes de agir (scheduling, communication, screening) | Alto | Fase 1, `get_company_policy()` em cada serviço |
| **Fase 4** | Monitor contínuo + sugestões proativas + `PolicySyncService` | Alto | Fases 1-3, `AutomationScheduler` adaptado |
| **Fase 5** | Learning loop ativo (`learned_patterns`) + recalibração automática | Alto | Todas as fases anteriores, `FeedbackLoop` |

**Status de implementação das 19 perguntas:**

| Status | Qtd | Descrição |
|--------|-----|-----------|
| **EXISTENTE** | 5 | Backend já suporta (Q3, Q4, Q11, Q15, Q18) |
| **PARCIAL** | 6 | Serviço existe, falta conectar com policy (Q5, Q6, Q7, Q9, Q16, Q17) |
| **NOVO** | 5 | Requer desenvolvimento (Q1, Q2, Q8, Q10, Q12) |
| **INFORMATIVO** | 2 | Armazena preferência sem enforcement imediato (Q14, Q19) |

---

### 3.23 Arquitetura ReAct Agent System

A plataforma implementa um sistema de agentes autônomos baseado no padrão **ReAct** (Reason-Act-Observe), que substitui progressivamente os agentes legacy baseados em pipelines fixos. A migração é controlada pela feature flag `USE_REACT_AGENTS` com fallback automático para o comportamento legacy.

#### 3.23.1 Padrão de 4 Arquivos por Agente (4-File Pattern)

Cada agente ReAct segue uma estrutura padronizada de 4 arquivos no diretório do domínio:

```
app/domains/{domain}/agents/
├── {name}_react_agent.py    # Classe do agente (implementa BaseAgent)
├── tool_registry.py         # Registro de tools disponíveis para o agente
├── system_prompt.py         # System prompt com persona, regras e few-shot examples
└── stage_context.py         # Contexto por estágio (wizard stages, pipeline phases)
```

**Responsabilidades de cada arquivo:**

| Arquivo | Responsabilidade | Exemplo |
|---------|------------------|---------|
| `*_react_agent.py` | Instanciação do ReActLoop com config, orquestração de input/output, integração com WorkingMemory | `WizardReActAgent`, `KanbanReActAgent` |
| `tool_registry.py` | Lista de `ToolDefinition` com nome, descrição, parâmetros JSON Schema e função async | 9-14 tools por agente |
| `system_prompt.py` | Prompt do sistema com persona LIA, regras de domínio, anti-sycophancy guardrails, company context calibration e few-shot examples | Prompts de ~2000-4000 tokens |
| `stage_context.py` | Enumeração de estágios e contexto adicional injetado no prompt conforme o estágio atual | `WizardStage`, `KanbanPhase` |

#### 3.23.2 ReactAgentRegistry & AgentFactory

```
┌─────────────────────────────────────────────────────────────────┐
│              ReactAgentRegistry (Singleton)                       │
│                                                                   │
│  _registry: Dict[domain, {agent_class, config}]                  │
│                                                                   │
│  register(domain, agent_class, config)                           │
│  get_agent(domain) → BaseAgent (instância cacheada)              │
│  list_domains() → ["wizard","kanban","talent",...]               │
│  get_capabilities() → {domain: {tools, class, config}}           │
│  get_agent_status(domain) → {status, health}                     │
│                                                                   │
│  Domínios registrados (7):                                       │
│  ┌──────────┬──────────────────────┬───────────────────────┐    │
│  │ Domain   │ Agent Class          │ Domain Module          │    │
│  ├──────────┼──────────────────────┼───────────────────────┤    │
│  │ wizard   │ WizardReActAgent     │ job_management         │    │
│  │ kanban   │ KanbanReActAgent     │ recruiter_assistant    │    │
│  │ talent   │ TalentReActAgent     │ recruiter_assistant    │    │
│  │ jobs_mgmt│ JobsMgmtReActAgent   │ recruiter_assistant    │    │
│  │ pipeline │ PipelineReActAgent   │ cv_screening           │    │
│  │ sourcing │ SourcingReActAgent   │ sourcing               │    │
│  │ policy   │ PolicyReActAgent     │ hiring_policy          │    │
│  └──────────┴──────────────────────┴───────────────────────┘    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           v
┌─────────────────────────────────────────────────────────────────┐
│              AgentFactory                                         │
│                                                                   │
│  create_agent(domain, session_id, company_id, user_id)           │
│    → Cria instância NOVA (session-safe)                          │
│    → Injeta WorkingMemoryService                                 │
│    → Injeta ReActObserver                                        │
│    → Garante isolamento entre sessões                            │
│                                                                   │
│  IMPORTANTE: Registry armazena CLASSES, não instâncias.          │
│  AgentFactory cria instância fresca a cada chamada.              │
└─────────────────────────────────────────────────────────────────┘
```

**Arquivo:** `app/shared/agents/react_agent_registry.py`

#### 3.23.3 BaseAgent Interface

Todos os agentes ReAct implementam a interface `BaseAgent` definida em `app/shared/agents/agent_interface.py`:

```python
class BaseAgent(ABC):
    domain_name: str
    available_tools: List[str]

    async def process(self, input: AgentInput) -> AgentOutput
    async def get_status(self) -> dict
```

**Modelos padronizados:**
- `AgentInput`: message, context, session_id, company_id, user_id, conversation_history, metadata
- `AgentOutput`: response, actions (List[AgentAction]), navigation (NavigationCommand), metadata, confidence
- `AgentAction`: action_type (update_field, call_tool, navigate, confirm, save_draft), params, requires_confirmation

#### 3.23.4 AgentWorkingMemory (Estado Persistente por Sessão)

Cada agente mantém estado persistente entre mensagens via `AgentWorkingMemory` (tabela PostgreSQL):

```
AgentWorkingMemory (tabela: agent_working_memory)
├── session_id + domain (chave composta)
├── current_stage: str           ← Estágio atual do wizard/pipeline
├── collected_fields: JSON       ← Campos extraídos {field: {value, confidence, source}}
├── current_plan: JSON           ← Próximos passos planejados
├── pending_actions: JSON        ← Ações aguardando confirmação
├── adjustment_history: JSON     ← Histórico de ajustes (campo, old, new, reason)
├── parecer_data: JSON           ← Dados do parecer/avaliação
├── accepted_suggestions: JSON   ← Sugestões aceitas pelo recrutador
├── rejected_suggestions: JSON   ← Sugestões rejeitadas
├── agent_notes: Text            ← Notas do agente (scratchpad)
├── iteration_count: int         ← Contador de iterações
├── last_intent: str             ← Última intenção classificada
├── last_confidence: float       ← Confiança da última classificação
├── company_id + user_id         ← Multi-tenancy
└── created_at + updated_at      ← Timestamps
```

**WorkingMemoryService** fornece operações:
- `get_or_create(session_id, domain)` → recupera ou cria memória
- `add_collected_field(session_id, domain, field, value, confidence, source)`
- `add_adjustment(session_id, domain, field, old, new, reason)`
- `set_plan(session_id, domain, plan)` → define próximos passos
- `get_context_summary(session_id, domain)` → resumo para injeção no prompt
- `increment_iteration(session_id, domain)`

#### 3.23.5 ReActLoop — Ciclo de Raciocínio Autônomo

O `ReActLoop` é o motor central de raciocínio de cada agente. Implementado em `app/shared/agents/react_loop.py`:

```
┌─────────────────────────────────────────────────────────────────┐
│  ReActLoop.run(message, context, session_id)                     │
│                                                                   │
│  while iteration < max_iterations:                               │
│    ┌─────────────────────────────────────────────────────────┐  │
│    │ 1. REASON (_reason)                                      │  │
│    │    Constrói prompt: system + tools + context + history    │  │
│    │    + observations + extra_context (long-term memories)    │  │
│    │    Chama LLM → JSON {thought, action, tool_name, ...}    │  │
│    └──────────────────────────┬────────────────────────────────┘  │
│                               │                                   │
│    ┌──────────────────────────v────────────────────────────────┐  │
│    │ 2. PARSE & DECIDE                                         │  │
│    │    action == "respond" → gera resposta final, BREAK       │  │
│    │    action == "ask_clarification" → pede info, BREAK       │  │
│    │    action == "call_tool" → continua para ACT              │  │
│    └──────────────────────────┬────────────────────────────────┘  │
│                               │                                   │
│    ┌──────────────────────────v────────────────────────────────┐  │
│    │ 3. ACT (_act)                                             │  │
│    │    Verifica: tool existe? já falhou? duplicata?            │  │
│    │    Verifica: tool em guardrails? → pede confirmação       │  │
│    │    Executa: tool_def.function(**tool_args)                 │  │
│    └──────────────────────────┬────────────────────────────────┘  │
│                               │                                   │
│    ┌──────────────────────────v────────────────────────────────┐  │
│    │ 4. OBSERVE (_observe)                                     │  │
│    │    Interpreta resultado do tool                            │  │
│    │    Adiciona observação ao estado                           │  │
│    └──────────────────────────┬────────────────────────────────┘  │
│                               │                                   │
│    ┌──────────────────────────v────────────────────────────────┐  │
│    │ 5. SHOULD RESPOND? (_should_respond)                      │  │
│    │    Heurística: tool sucedeu? dados suficientes?           │  │
│    │    Sim → gera resposta final, BREAK                       │  │
│    │    Não → continua loop (próxima iteração)                 │  │
│    └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  Proteções:                                                      │
│  - Max iterations (default: 5) → fallback response               │
│  - Duplicate tool call detection (>= 2 repetições → break)       │
│  - Failed tool call tracking (não repete com mesmos params)       │
│  - Guardrail tools → requer confirmação do usuário               │
│  - Error handling → resposta de fallback segura                  │
└─────────────────────────────────────────────────────────────────┘
```

**ReActConfig** define os parâmetros do loop por agente:
- `max_iterations`: 5 (default)
- `system_prompt`: prompt completo do domínio
- `available_tools`: lista de ToolDefinition
- `model_provider`: "claude" | "openai" | "gemini" (default: "claude")
- `model_name`: "claude-sonnet-4-20250514"
- `temperature`: 0.3
- `guardrails`: tools que requerem confirmação
- `extra_context`: memórias de longo prazo injetadas

**ReActState** mantém o estado durante uma execução:
- `messages`, `current_reasoning`, `actions_taken`, `observations`
- `tool_calls_made`, `failed_tool_calls`
- `consecutive_duplicate_count`, `last_tool_call_key`
- `should_respond`, `final_response`, `iteration`, `error`

#### 3.23.6 ReActObserver — Telemetria de Execução

O `ReActObserver` (`app/shared/agents/observability.py`) captura telemetria detalhada de cada execução do loop:

```
ReActObserver
├── start_iteration(iteration)
├── log_reasoning(iteration, reasoning)
├── log_tool_call(iteration, tool_name, tool_args, success, duration_ms)
├── log_decision(iteration, decision: "respond" | "continue" | "error")
└── finalize(user_message, response, confidence) → AgentExecutionLog

AgentExecutionLog:
├── session_id, domain, agent_class
├── start_time, end_time, total_duration_ms
├── total_iterations, tools_called, tools_succeeded, tools_failed
├── final_confidence, model_provider
├── stage_before, stage_after, stage_transitioned
├── iterations: List[IterationLog]  ← Cadeia completa de raciocínio
└── error

IterationLog:
├── iteration, timestamp, phase, duration_ms
├── tool_name, tool_args, tool_success
├── reasoning, observation, decision
└── error
```

#### 3.23.7 Feature Flag USE_REACT_AGENTS

A migração de agentes legacy para ReAct é controlada por feature flag:

```
USE_REACT_AGENTS = true (default)
├── true  → Orchestrator roteia para ReactAgentRegistry.get_agent(domain)
└── false → Orchestrator usa DomainPrompt.process_intent() (legacy)

Fallback automático:
├── Se agente ReAct falha com exceção → tenta fallback legacy
├── Se domínio não tem agente ReAct registrado → usa legacy
└── Logs de fallback para monitoramento da migração
```

---

### 3.24 Long-Term Memory System

O sistema de memória de longo prazo permite que agentes aprendam e retenham conhecimento entre sessões diferentes, acumulando padrões, preferências e outcomes por empresa.

#### 3.24.1 AgentLongTermMemory (Tabela)

```
AgentLongTermMemory (tabela: agent_long_term_memory)
├── company_id (index)          ← Escopo por empresa (multi-tenant)
├── domain: str                 ← Domínio do agente que criou
├── memory_type: str            ← "pattern" | "preference" | "learning" | "outcome"
├── memory_key: str             ← Identificador da memória (ex: "salary_range_dev_senior")
├── memory_value: JSON          ← Valor arbitrário da memória
├── context_tags: JSON          ← Tags para busca por contexto (ex: ["python", "senior"])
├── usage_count: int            ← Quantas vezes foi utilizada (popularidade)
├── relevance_score: float      ← Score de relevância (0.0-1.0, com decay temporal)
├── source_session_id: str      ← Sessão que originou a memória
├── expires_at: DateTime?       ← Expiração opcional
└── created_at + updated_at     ← Timestamps
```

#### 3.24.2 LongTermMemoryService

**Arquivo:** `app/shared/agents/long_term_memory.py`

Operações:
- `store(company_id, domain, memory_type, key, value, tags, session_id)` → cria ou atualiza (upsert por key)
- `recall(company_id, domain?, memory_type?, tags?, limit)` → busca por relevância × popularidade, filtro por tags
- `recall_for_context(company_id, domain, context_text, limit)` → busca semântica por palavras do contexto
- `update_relevance(memory_id, boost)` → reforça relevância (+0.1, max 1.0)
- `decay_relevance(company_id, decay_factor=0.95)` → decaimento temporal de todas as memórias
- `get_company_learnings(company_id, domain?)` → lista learnings de uma empresa
- `record_outcome(company_id, domain, session_id, outcome_type, data, tags)` → registra resultado

**Ranking de relevância:**
```
score = relevance_score × (usage_count + 1)
```
Memórias mais usadas e com maior relevância aparecem primeiro.

#### 3.24.3 MemoryIntegration

**Arquivo:** `app/shared/agents/memory_integration.py`

Ponte entre Working Memory (sessão) e Long-Term Memory (cross-sessão):

```
MemoryIntegration
├── get_enriched_context(session_id, domain, company_id)
│   → Combina Working Memory + Long-Term Memory
│   → Formato injetado no prompt do agente como extra_context
│   → Seções: "=== Session Memory ===" + "=== Cross-Session Learnings ==="
│
├── save_session_learnings(session_id, domain, company_id, learnings)
│   → Persiste aprendizados da sessão atual para uso futuro
│   → Cada learning: {type, key, value, tags}
│
└── get_memory_summary_for_prompt(company_id, domain, context_tags?)
    → Resumo categorizado para injeção no system prompt:
    → "Known Patterns:", "Company Preferences:",
    → "Previous Learnings:", "Recent Outcomes:"
```

---

### 3.25 Agent Explainability System

O sistema de explicabilidade permite auditoria completa do raciocínio dos agentes, armazenando cada execução com cadeia de raciocínio, tools chamadas e decisões tomadas.

#### 3.25.1 ExecutionLogStore

**Arquivo:** `app/shared/agents/execution_log_store.py`

```
AgentExecutionRecord (tabela: agent_execution_records)
├── session_id (index)
├── company_id (index)
├── user_id
├── domain, agent_class
├── user_message, agent_response
├── total_duration_ms, total_iterations
├── tools_called: JSON (lista de nomes)
├── tools_succeeded: int, tools_failed: int
├── final_confidence: float
├── reasoning_chain: JSON         ← Cadeia completa: [{iteration, phase, reasoning, tool, decision}]
├── stage_before, stage_after     ← Transição de estágio
├── stage_transitioned: bool
├── model_provider: str
├── metadata: JSON
└── created_at
```

**Operações do ExecutionLogStore:**
- `save(log_data, company_id, user_id)` → persiste registro de execução
- `get_by_session(session_id, limit)` → histórico de execuções da sessão
- `get_by_company(company_id, domain?, limit)` → execuções por empresa
- `get_timeline(session_id)` → timeline visual de todas as iterações
- `get_stats(company_id)` → métricas agregadas (avg_confidence, avg_iterations, avg_duration_ms, most_used_tools)

#### 3.25.2 Fluxo de Explicabilidade

```
┌──────────────────────────────────────────────────────────────┐
│  FLUXO: Agente Executa → Observer Captura → Store Persiste    │
│                                                                │
│  1. AgentFactory cria agente com ReActObserver injetado        │
│  2. ReActLoop executa, observer captura cada iteração          │
│  3. Ao finalizar, observer.finalize() gera AgentExecutionLog   │
│  4. ExecutionLogStore.save() persiste no PostgreSQL             │
│  5. Frontend consulta via API:                                  │
│     GET /api/v1/agent-monitoring/agents/{agentId}/activities   │
│     → Exibe timeline de raciocínio no painel de explainability │
│                                                                │
│  Dados disponíveis por execução:                               │
│  - Cadeia de raciocínio completa (cada thought/action/observe) │
│  - Tools chamadas com args e resultados                        │
│  - Tempo de cada fase (reason, act, observe)                   │
│  - Confiança final do agente                                   │
│  - Transições de estágio                                       │
│  - Erros e fallbacks                                           │
└──────────────────────────────────────────────────────────────┘
```

---

### 3.26 Multi-Channel Communication

O sistema de comunicação multi-canal fornece uma abstração unificada para envio de mensagens por diferentes canais, com roteamento inteligente e fallback automático.

#### 3.26.1 Arquitetura Multi-Channel

```
┌─────────────────────────────────────────────────────────────────┐
│              MultiChannelService (Singleton)                      │
│              app/shared/channels/multi_channel_service.py         │
│                                                                   │
│  send_message(message, channels, fallback=True)                  │
│  send_bulk(messages, channel) → List[DeliveryResult]             │
│  get_delivery_status(message_id) → DeliveryStatus                │
│  get_available_channels() → List[{channel, available}]           │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              ChannelRouter                                  │  │
│  │  route(message, channels, fallback) → DeliveryResult        │  │
│  │  Tenta canais em ordem, fallback automático se falhar       │  │
│  └──────────────────────────┬────────────────────────────────┘  │
│                              │                                    │
│          ┌───────────┬───────┼───────┬───────────┐               │
│          v           v       v       v           v               │
│  ┌──────────┐ ┌──────────┐ ┌────┐ ┌──────────┐ ┌──────────┐   │
│  │  Email   │ │ WhatsApp │ │SMS │ │  In-App  │ │ MS Teams │   │
│  │ Adapter  │ │ Adapter  │ │Adap│ │ Adapter  │ │ Adapter  │   │
│  │          │ │          │ │ter │ │          │ │          │   │
│  │ Mailgun  │ │ Twilio   │ │Twi │ │ WebSock  │ │ MS Graph │   │
│  └──────────┘ └──────────┘ └────┘ └──────────┘ └──────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**5 Adapters implementados:**

| Adapter | Canal | Provider | Arquivo |
|---------|-------|----------|---------|
| `EmailChannelAdapter` | Email | Mailgun | `adapters/email_adapter.py` |
| `WhatsAppChannelAdapter` | WhatsApp | Twilio | `adapters/whatsapp_adapter.py` |
| `SMSChannelAdapter` | SMS | Twilio | `adapters/sms_adapter.py` |
| `InAppChannelAdapter` | In-App | WebSocket | `adapters/in_app_adapter.py` |
| `MSTeamsChannelAdapter` | MS Teams | MS Graph | `adapters/teams_adapter.py` |

**Modelos:**
- `ChannelMessage`: recipient_name, recipient_contact, subject, body, template_id, metadata
- `DeliveryResult`: success, channel, message_id, status, error
- `DeliveryStatus`: PENDING, SENT, DELIVERED, READ, FAILED
- `ChannelType`: EMAIL, WHATSAPP, SMS, IN_APP, MS_TEAMS

**Contrato base `ChannelAdapter` (ABC):**
```python
class ChannelAdapter(ABC):
    channel_type: ChannelType
    async def send(message: ChannelMessage) → DeliveryResult
    async def check_status(message_id: str) → DeliveryStatus
    async def is_available() → bool
```

---

### 3.27 Async Task Processing at Scale

O sistema de processamento assíncrono nativo substitui a dependência de RabbitMQ+Celery para operações pesadas, com filas in-process, persistência, retry com DLQ e agendamento cron.

#### 3.27.1 Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│              PROCESSAMENTO ASSÍNCRONO NATIVO                      │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  DomainTaskManager (Singleton)                              │  │
│  │  app/shared/async_processing/task_manager.py                │  │
│  │                                                             │  │
│  │  - Gerencia filas por domínio (9 domínios com tasks async) │  │
│  │  - Max 3 tasks paralelos por domínio                       │  │
│  │  - API unificada: submit_task, get_status, cancel          │  │
│  │  - ASYNC_ELIGIBLE_ACTIONS: mapa de ações async por domínio │  │
│  └──────────────────────────┬────────────────────────────────┘  │
│                              │                                    │
│  ┌──────────────────────────v────────────────────────────────┐  │
│  │  EnhancedTaskManager                                        │  │
│  │  app/shared/async_processing/enhanced_task_manager.py       │  │
│  │                                                             │  │
│  │  Estende DomainTaskManager com:                            │  │
│  │  - Persistência em PostgreSQL (TaskRecord)                 │  │
│  │  - Retry automático com backoff                            │  │
│  │  - Dead Letter Queue (DLQ) para tasks falhados             │  │
│  │  - Callbacks: on_task_started, on_task_completed,          │  │
│  │    on_task_failed, on_task_sent_to_dlq                     │  │
│  └──────────────────────────┬────────────────────────────────┘  │
│                              │                                    │
│  ┌──────────────────────────v────────────────────────────────┐  │
│  │  TaskScheduler                                              │  │
│  │  app/shared/async_processing/task_scheduler.py              │  │
│  │                                                             │  │
│  │  - Agendamento cron nativo (parse de expressões cron)      │  │
│  │  - Persistência de schedules em PostgreSQL (TaskSchedule)  │  │
│  │  - Loop de tick a cada 60 segundos                         │  │
│  │  - Suporta: daily, hourly, custom cron expressions         │  │
│  └──────────────────────────┬────────────────────────────────┘  │
│                              │                                    │
│  ┌──────────────────────────v────────────────────────────────┐  │
│  │  DomainTaskQueue                                            │  │
│  │  app/shared/async_processing/task_queue.py                  │  │
│  │                                                             │  │
│  │  - Fila in-process com prioridade (HIGH, NORMAL, LOW)      │  │
│  │  - Workers assíncronos (asyncio.create_task)               │  │
│  │  - Limite de tamanho da fila (max_queue_size=100)          │  │
│  │  - Handlers registráveis por action_id                     │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.27.2 Ações Assíncronas Elegíveis

```
ASYNC_ELIGIBLE_ACTIONS = {
    "sourcing":              ["bulk_search", "mass_outreach", "import_candidates"],
    "cv_screening":          ["bulk_screen", "batch_evaluate", "full_pipeline_screen"],
    "communication":         ["mass_email", "mass_whatsapp", "bulk_notification"],
    "analytics":             ["generate_full_report", "export_large_dataset", "predictive_analysis"],
    "ats_integration":       ["bulk_sync", "full_import", "full_export"],
    "automation":            ["batch_stage_transition", "run_automation_rules"],
    "job_management":        ["bulk_publish", "batch_update_jobs"],
    "interview_scheduling":  ["batch_schedule"],
    "recruiter_assistant":   ["generate_daily_briefing"],
}
```

#### 3.27.3 Dead Letter Queue (DLQ)

Tasks que falham após todas as tentativas de retry são movidos para a DLQ:

```
Task falha → retry_count < max_retries?
├── Sim → Re-enqueue com state=RETRYING
└── Não → on_task_sent_to_dlq(task_id, domain, action, params, error, tenant_id)
           → Persiste em TaskRecord com state=DEAD_LETTER
           → Disponível para reprocessamento manual ou análise
```

---

## 4. Camada de Orquestração

### 4.1 Orchestrator Central

**Arquivo:** `app/orchestrator/orchestrator.py`  
**Classe:** `Orchestrator`

O Orchestrator é o ponto de entrada de todas as requisições do usuário. Sua responsabilidade:

1. **Sanitização** — Limpa e normaliza a entrada do usuário
2. **Validação de Políticas** — Consulta o PolicyEngine antes de processar
3. **Roteamento** — Usa o CascadedRouter para determinar o domínio alvo
4. **Detecção de Planos** — Identifica se a query requer execução multi-step
5. **Execução** — Delega ao domínio ou ao PlanExecutor
6. **Pós-processamento** — Aplica FactChecker e logging de auditoria

### 4.2 Cascaded Router (Roteamento em 3 Camadas)

**Arquivo:** `app/orchestrator/cascaded_router.py`  
**Classe:** `CascadedRouter`

O roteamento usa uma estratégia em cascata para otimizar latência e custo:

```
Query do Usuário
      │
      ▼
┌──────────────┐
│  Camada 1:   │  Verifica cache de sessão/memória
│  Memory      │  Latência: <1ms | Custo: $0
│  Cache       │
└──────┬───────┘
       │ miss
       ▼
┌──────────────┐
│  Camada 2:   │  Regex/keyword matching por domínio
│  FastRouter  │  Latência: <5ms | Custo: $0
│  (Regex)     │  Cada domínio tem _KEYWORD_ACTION_MAP
└──────┬───────┘
       │ confidence < threshold
       ▼
┌──────────────┐
│  Camada 3:   │  Claude classifica intent + domínio
│  IntentRouter│  Latência: 500-2000ms | Custo: ~$0.01
│  (LLM)       │
└──────────────┘
```

**Nota importante sobre routing:** O CascadedRouter retorna um `RouteResult` contendo `domain_id` e `confidence`. No Orchestrator, `intent` é atribuído diretamente ao `route.domain_id` — ou seja, **o conceito de "intent" no Orchestrator é equivalente ao `domain_id`**, não há um sistema de intents separado. A classificação mais granular (qual ação específica dentro do domínio) é feita pelo próprio domínio em seu método `process_intent()`.

**Cada domínio contribui com seu próprio `_KEYWORD_ACTION_MAP`** — um dicionário de palavras-chave em português e inglês mapeadas para actions. Exemplo do domínio CV Screening:

```python
_KEYWORD_ACTION_MAP = {
    "analisar cv": "parse_cv",
    "triagem automática": "auto_screen",
    "calcular wsi": "calculate_wsi_score",
    "score wsi": "calculate_wsi_score",
    ...
}
```

A confiança é calculada por: `confidence = min(0.95, 0.6 + len(keyword) * 0.02)`

### 4.3 State Manager

**Arquivo:** `app/orchestrator/state_manager.py`  
**Classe:** `StateManager`

Gerencia o estado da conversação em memória com persistência em banco:

- Histórico de mensagens por sessão
- Contexto acumulado (vaga ativa, candidato ativo, etapa do wizard)
- Memória persistente cross-sessão (via embedding search)

### 4.4 Task Planner (Execução Multi-Step)

**Arquivo:** `app/orchestrator/task_planner.py`  
**Classe:** `TaskPlanner`

Decompõe queries complexas em tarefas atômicas sequenciais:

```
"Busque candidatos Python sênior e compare com os que já estão no pipeline"
      │
      ▼
Task 0: sourcing.search_candidates(skills=["Python"], seniority="senior")
Task 1: recruiter_assistant.compare_candidates(candidate_ids=task_0.result.ids)
```

O `PlanDetector` usa regex para identificar padrões como "buscar_e_comparar", "triar_e_agendar", etc.

### 4.5 Plan Executor

**Arquivo:** `app/shared/execution/plan_executor.py`  
**Classe:** `PlanExecutor`

Executa planos multi-step com injeção de contexto entre tarefas:
- Resultado da task N é injetado como contexto na task N+1
- Suporta execução paralela quando não há dependências
- Retry com backoff exponencial em caso de falha

---

## 5. Mapa Completo de Domínios

### Visão Geral dos 11 Domínios

| # | Domain ID | Nome | Escopo | Actions | Tools |
|---|-----------|------|--------|---------|-------|
| 1 | `sourcing` | Sourcing | Busca e captação de candidatos | 30 | 19 |
| 2 | `job_management` | Job Management | Criação e gestão de vagas | 29 | 13 |
| 3 | `cv_screening` | CV Screening | Triagem, avaliação WSI, scoring | 25 | 12 |
| 4 | `communication` | Communication | Email, WhatsApp, Teams, SMS, templates | 20 | 10 |
| 5 | `interview_scheduling` | Interview & Scheduling | Agendamento, WSI interview, voz | 20 | 10 |
| 6 | `analytics` | Analytics & Reporting | KPIs, previsões, dashboards | 18 | 10 |
| 7 | `ats_integration` | ATS Integration | Sync bidirecional com ATS externos | 18 | 10 |
| 8 | `automation` | Automation & Tasks | Automações, tarefas, alertas proativos | 20 | 10 |
| 9 | `recruiter_assistant` | Recruiter Assistant | Assistente pessoal do recrutador | 20 | 10 |
| 10 | `pipeline_transition` | Pipeline Transition | Movimentação de candidatos no pipeline | 5 | 5 |
| 11 | `hiring_policy` | Hiring Policy | Configuração de políticas de contratação via ReAct agent | — | 13 (ReAct) |

**Total: 205 actions (legacy), 109 tools (legacy) + 13 ReAct tools (hiring_policy)** *(verificado por grep + contagem manual em 23/02/2026 — ver Apêndice C)*

> **Nota:** O domínio Pipeline Transition define actions e tools inline no `domain.py` (não em arquivos separados `actions.py`/`tools.py`), diferente dos outros domínios. Também utiliza `kanban_assistant_service.py` para lógica de negócio.
>
> **Nota:** O domínio Hiring Policy (#11) utiliza a arquitetura ReAct (4-file pattern) em vez da arquitetura legacy de Actions/Tools. Suas 13 ferramentas são definidas no `policy_tool_registry.py` e expostas ao `ReActLoop` como `ToolDefinition`, não como domain actions tradicionais.

---

### 5.1 Domínio: Sourcing

**Classe:** `SourcingDomain`  
**Escopo:** Busca, captação e pré-qualificação de candidatos em fontes internas e externas.

**Responsabilidades:**
- Busca semântica por embeddings
- Busca booleana avançada
- Integração Pearch AI (busca externa)
- Match candidato-vaga com scoring
- Talent pool management
- Sourcing pipeline automatizado
- Análise de volume e mercado

**Serviços Principais:**
| Serviço | Classe | Função |
|---------|--------|--------|
| `pearch_service.py` | `PearchService` | Integração com Pearch API para sourcing externo |
| `vacancy_search.py` | `VacancySearchService` | Extração de critérios e busca de vagas |
| `sourcing_pipeline.py` | `SourcingPipelineService` | Pipeline automatizado end-to-end |
| `pgv_analyzer.py` | `PgvGapAnalyzer` | Análise de gaps semânticos em qualificações |
| `wrf_service.py` | `WRFService` | Weighted Ranking Framework para avaliação |

---

### 5.2 Domínio: Job Management

**Classe:** `JobManagementDomain`  
**Escopo:** Criação, edição, publicação e análise de vagas de emprego.

**Responsabilidades:**
- Job Wizard conversacional (LIA guia o recrutador)
- Geração de Job Descriptions com IA
- Enriquecimento de JDs (benchmarks, skills, compensação)
- Templates de vagas por indústria
- Health check de vagas
- Sistema de rubricas para avaliação
- Detecção automática de critérios

**Serviços Principais:**
| Serviço | Classe | Função |
|---------|--------|--------|
| `job_vacancy_service.py` | `JobVacancyService` | Ciclo de vida completo de vagas |
| `jd_generator_service.py` | `JobDescriptionGeneratorService` | Geração de JDs estruturadas |
| `wizard_orchestrator_service.py` | `WizardOrchestratorService` | Orquestração do Smart Wizard |
| `job_insights_service.py` | `JobInsightsService` | Insights de mercado e benchmarks |

---

### 5.3 Domínio: CV Screening

**Classe:** `CVScreeningDomain`  
**Escopo:** Triagem automatizada de candidatos usando metodologia WSI.

**Responsabilidades:**
- Parse e extração de dados de CVs (PDF/Docx)
- Scoring automático contra requisitos da vaga
- Cálculo de score WSI (7 blocos)
- Classificação por Taxonomia de Bloom
- Classificação por Modelo Dreyfus
- Mapeamento Big Five (traços comportamentais)
- Validação CBI (Competency-Based Interview)
- Geração de perguntas de triagem WSI
- Avaliação de senioridade multi-signal
- Corte dinâmico (top 25%)
- Detecção de red flags
- Normalização de scores entre candidatos

**Serviços Principais:**
| Serviço | Classe | Função |
|---------|--------|--------|
| `cv_scoring_service.py` | `CVScoringService` | Scoring de CVs contra requisitos |
| `wsi_service.py` | `WSIService` | Implementação da metodologia WSI |
| `cv_parser.py` | `CVParser` | Extração estruturada de CVs |
| `wsi_question_generator.py` | `WSIScreeningQuestionGenerator` | Geração de perguntas WSI |

---

### 5.4 Domínio: Communication

**Classe:** `CommunicationDomain`  
**Escopo:** Comunicação multi-canal com candidatos e stakeholders.

**Responsabilidades:**
- Email individual e em massa
- WhatsApp (via Twilio/Meta)
- Microsoft Teams
- SMS
- Templates de comunicação (criação, edição, preview)
- Histórico de comunicação por candidato
- Convites de triagem e entrevista
- Notificações para stakeholders
- Webhooks de comunicação
- Processamento de solicitações LGPD

**Serviços Principais:**
| Serviço | Classe | Função |
|---------|--------|--------|
| `communication_service.py` | `CommunicationService` | Gerenciamento central de comunicações |
| `whatsapp_service.py` | `WhatsAppService` | Mensageria WhatsApp |
| `email_service.py` | `EmailService` | Envio de emails e templates |
| `teams_service.py` | `TeamsService` | Integração Microsoft Teams |

---

### 5.5 Domínio: Interview & Scheduling

**Classe:** `InterviewSchedulingDomain`  
**Escopo:** Agendamento de entrevistas, condução de entrevistas WSI e análise de voz.

**Responsabilidades:**
- Agendamento, reagendamento e cancelamento de entrevistas
- Verificação de disponibilidade em calendários (Google/Outlook)
- Links de auto-agendamento para candidatos
- Encontrar horários comuns entre participantes
- Lembretes automáticos
- Resolução de conflitos de agenda
- Entrevista WSI completa (perguntas, análise, follow-up)
- Transcrição de áudio (Deepgram Nova-2)
- Análise de voz (tom, confiança)
- Detecção de respostas evasivas
- Triagem rápida (10-15 minutos)

**Serviços Principais:**
| Serviço | Classe | Função |
|---------|--------|--------|
| `calendar_service.py` | `CalendarService` | Integração com calendários |
| `scheduling_service.py` | `SchedulingService` | Lógica de agendamento |
| `deepgram_service.py` | `DeepgramService` | Transcrição de áudio |

---

### 5.6 Domínio: Analytics & Reporting

**Classe:** `AnalyticsDomain`  
**Escopo:** Métricas, KPIs, análise preditiva e dashboards.

**Responsabilidades:**
- Relatórios de KPIs de recrutamento
- Análise de funil de conversão
- Health check de vagas
- Detecção de anomalias
- Comparação entre períodos
- Previsão de métricas e tendências
- Sugestões estratégicas via IA
- Insights de vagas (benchmarks salariais, competências)
- Relatórios de candidatos (comparativo)
- Analytics de busca e wizard
- Previsão de probabilidade de contratação
- Previsão de tempo de preenchimento (time-to-fill)
- Previsão de risco de desistência
- Monitoramento de performance de agentes IA

**Serviços Principais:**
| Serviço | Classe | Função |
|---------|--------|--------|
| `predictive_analytics_service.py` | `PredictiveAnalyticsService` | Modelos preditivos |
| `search_analytics_service.py` | `SearchAnalyticsService` | Métricas de busca |
| `report_service.py` | `ReportService` | Geração de relatórios |

---

### 5.7 Domínio: ATS Integration

**Classe:** `ATSIntegrationDomain`  
**Escopo:** Sincronização bidirecional com plataformas ATS externas.

**Responsabilidades:**
- Sincronização de candidatos e vagas (push/pull)
- Sincronização em massa
- Importação de candidatos e vagas de ATS externos
- Configuração de conexões ATS
- Teste de conexão e health check
- Mapeamento de campos entre sistemas
- Log de auditoria de sincronização
- Resolução de conflitos de dados
- Envio de scores WSI para ATS
- Webhooks de sincronização em tempo real

**Serviços Principais:**
| Serviço | Classe | Função |
|---------|--------|--------|
| `merge_ats_service.py` | `MergeATSService` | Interface unificada via Merge.dev |
| `ats_sync_service.py` | `ATSSyncService` | Gerenciamento de sincronização |
| `gupy_service.py` | `GupyService` | Integração especializada Gupy |

**ATS Suportados:** Gupy, Pandapé, Merge (unificador para múltiplos ATS)

---

### 5.8 Domínio: Automation & Tasks

**Classe:** `AutomationDomain`  
**Escopo:** Automação de tarefas, alertas proativos e agentes autônomos.

**Responsabilidades:**
- Criação, listagem, conclusão e cancelamento de tarefas
- Decomposição de tarefas complexas via IA
- Planejamento de execução com dependências
- Criação e gerenciamento de regras de automação
- Automação de transições de etapa no pipeline
- Predição de sub-status via IA
- Alertas proativos para o recrutador
- Tarefas recorrentes (scheduling)
- Verificações autônomas em background
- Visualização de grafo de dependências

**Serviços Principais:**
| Serviço | Classe | Função |
|---------|--------|--------|
| `automation_service.py` | `AutomationService` | Engine genérica de automação |
| `stage_automation_engine.py` | `StageAutomationEngine` | Automação de transições de etapa |
| `task_service.py` | `TaskService` | Gerenciamento de tarefas async |

---

### 5.9 Domínio: Recruiter Assistant

**Classe:** `RecruiterAssistantDomain`  
**Escopo:** Assistente pessoal inteligente do recrutador.

**Responsabilidades:**
- Briefing diário e resumo de fim de dia
- Respostas a perguntas rápidas
- Planejamento do dia e organização de agenda
- Análise de saúde do pipeline
- Identificação de candidatos parados/inativos
- Sugestão de próxima ação via IA
- Busca de contexto no histórico de conversas
- Memória persistente (salvar/recuperar informações)
- Resumo de conversas
- Análise do quadro Kanban
- Calibração de perfil ideal
- Acompanhamento de metas de recrutamento
- Geração de insights proativos
- Comparação rápida entre candidatos
- Recomendação de próxima etapa
- Movimentação de candidatos no pipeline

**Serviços Principais:**
| Serviço | Classe | Função |
|---------|--------|--------|
| `kanban_assistant_service.py` | `KanbanAssistantService` | Assistente IA do Kanban |
| `conversation_manager.py` | `ConversationManager` | Fluxos de diálogo automatizados |
| `memory_service.py` | `MemoryService` | Memória conversacional persistente |

---

### 5.10 Domínio: Pipeline Transition

**Arquivo:** `app/domains/pipeline/domain.py`  
**Classe:** `PipelineTransitionDomain`  
**DOMAIN_NAME:** `pipeline_transition`  
**Escopo:** Gerenciamento de movimentação de candidatos no pipeline.

**Nota arquitetural:** Diferente dos outros 9 domínios, este domínio define actions e tools **inline** no `domain.py` (via `get_allowed_actions()` e `DOMAIN_TOOLS`), sem arquivos separados `actions.py` ou `tools.py`.

**Actions (5):**
| Action ID | Descrição |
|-----------|-----------|
| `move_candidate` | Move candidato para nova etapa do pipeline |
| `interpret_context` | Interpreta contexto de transição via IA |
| `predict_sub_status` | Prediz sub-status adequado para a etapa |
| `suggest_next_action` | Sugere próxima ação baseada no pipeline |
| `list_pipeline_stages` | Lista etapas disponíveis no pipeline |

**Tools (5):** Mesmos 5 itens, definidos em `DOMAIN_TOOLS` com parâmetros tipados (vacancy_candidate_id, to_stage, from_stage, sub_status, prompt, channel).

**Serviço associado:** `kanban_assistant_service.py` — lógica de negócio para assistência ao pipeline.

**Integração:** Conecta-se à API REST `/api/v1/pipeline/transition/execute` para executar transições, pois a movimentação requer acesso ao banco de dados e contexto completo do candidato.

---

### 5.11 Domínio: Hiring Policy

**Arquivo:** `app/domains/hiring_policy/agents/policy_react_agent.py`  
**Classe:** `PolicyReActAgent`  
**DOMAIN_NAME:** `policy`  
**Escopo:** Configuração conversacional de políticas de contratação da empresa via agente ReAct autônomo.

**Arquitetura:** Este é o primeiro domínio implementado inteiramente com a arquitetura ReAct (4-file pattern), sem usar o sistema legacy de Actions/Tools:

| Arquivo | Função |
|---------|--------|
| `policy_react_agent.py` | Agente principal — implementa `BaseAgent`, orquestra o `ReActLoop` |
| `policy_tool_registry.py` | Registro de 13 ferramentas como `ToolDefinition` para o ReActLoop |
| `policy_system_prompt.py` | System prompt com instruções ReAct, anti-sycophancy e calibração por contexto |
| `policy_stage_context.py` | Contexto por estágio (onboarding, review, consulting) |

**Stages (3):**

| Stage | Fase | Descrição |
|-------|------|-----------|
| `onboarding` | setup | Configuração inicial — guia o recrutador pelos 5 blocos de política |
| `review` | maintenance | Revisão e edição de políticas já configuradas |
| `consulting` | advisory | Consultoria sobre impacto das políticas, benchmarks e trade-offs |

**Tools ReAct (13):**

| Tool Name | Descrição |
|-----------|-----------|
| `get_current_policy` | Carrega políticas atuais da empresa do banco de dados |
| `save_policy_field` | Salva campo específico de política (após validação de compliance) |
| `save_policy_block` | Salva bloco inteiro de política de uma vez |
| `get_policy_summary` | Resumo formatado de todas as políticas configuradas |
| `validate_policy_compliance` | Valida política contra FairnessGuard (3 camadas: regex + implícito + semântico LLM) |
| `get_company_context` | Busca dados reais da empresa (vagas, candidatos, tempos médios) |
| `get_industry_benchmarks` | Benchmarks do setor (8 setores: technology, finance, retail, healthcare, legal, education, manufacturing, services) |
| `get_platform_benchmarks` | Benchmarks calculados dos dados reais da plataforma |
| `explain_policy_impact` | Explica impacto de configuração nos agentes e processos |
| `get_setup_progress` | Progresso da configuração (blocos configurados vs pendentes) |
| `detect_policy_impact_anomalies` | Detecta anomalias causadas pelas políticas (stagnação, SLAs violados) |
| `get_policy_effectiveness_report` | Relatório de efetividade (tempo de contratação, taxa de preenchimento, funil) |
| `apply_industry_defaults` | Aplica configurações padrão do setor em todos os blocos |

**Blocos de Configuração (5):**

| Bloco | Campos | Descrição |
|-------|--------|-----------|
| `pipeline_rules` | min_interviews_before_offer, manager_approval_for_offer, max_days_in_stage, pipeline_templates | Regras de pipeline e processo seletivo |
| `scheduling_rules` | allowed_days, allowed_hours, default_duration_minutes, self_scheduling_enabled | Regras de agendamento de entrevistas |
| `communication_rules` | auto_rejection_feedback, rejection_feedback_deadline_hours, preferred_channel, lia_tone | Regras de comunicação com candidatos |
| `screening_rules` | salary_expectation_filter, salary_tolerance_percent, experience_policy, default_screening_questions | Regras de triagem |
| `automation_rules` | auto_screening, auto_scheduling, auto_stage_advance, autonomy_level | Nível de autonomia da LIA |

**FairnessGuard Integration:**
- Input validation: toda mensagem do recrutador é verificada pelo FairnessGuard antes de processar
- Tool-level validation: `validate_policy_compliance` invoca 3 camadas (regex normalizado, detecção de viés implícito, análise semântica LLM com `deep_check=True`)
- Critérios proibidos hardcoded no system prompt (gênero, raça, idade, religião, orientação sexual, estado civil, PCD, nacionalidade, aparência, situação familiar)

**Industry Benchmarks (8 setores):**
- Dados de referência para technology, finance, retail, healthcare, legal, education, manufacturing, services
- Fontes verificáveis por setor (Gupy, LinkedIn Talent Solutions, Robert Half, ABRH, GPTW, Glassdoor)
- Métricas: avg_interviews, avg_days_per_stage, avg_time_to_fill_days, common_autonomy_level, self_scheduling_adoption

**Anti-sycophancy:**
- System prompt inclui seção explícita de prevenção de sycophancy
- Contra-argumentação obrigatória com dados antes de aceitar configurações arriscadas
- Verificação de premissas: agente consulta ferramentas para validar afirmações do recrutador
- Calibração por contexto: STARTUP/PME/CORPORAÇÃO com recomendações diferenciadas

**Backward-compatible API:**
- Método `process_legacy_format()` bridging o novo agente ReAct com o formato de resposta do antigo `PolicySetupAgent`
- API REST em `/api/v1/hiring-policy/chat` mantém compatibilidade com o frontend existente
- Campos legacy preservados: `reply`, `current_block`, `setup_progress`, `updated_fields`

---

## 6. Catálogo de Ações (Actions)

### 6.1 Sourcing (30 actions)

| Action ID | Nome | Descrição |
|-----------|------|-----------|
| `search_candidates` | Buscar candidatos | Busca com filtros (skills, senioridade, localização) |
| `global_search` | Busca global | Busca em todas as fontes simultaneamente |
| `semantic_search` | Busca semântica | Busca por embeddings/similaridade |
| `generate_boolean` | Gerar boolean | Gera query booleana para busca avançada |
| `parse_cv` | Analisar CV | Extrai dados estruturados de currículo |
| `add_candidate` | Adicionar candidato | Cadastra novo candidato |
| `suggest_candidates` | Sugerir candidatos | Sugere candidatos para uma vaga |
| `match_candidates` | Match de candidatos | Calcula compatibilidade candidato-vaga |
| `enrich_profile` | Enriquecer perfil | Enriquece dados do candidato |
| `auto_source` | Sourcing automático | Pipeline automatizado de sourcing |
| `check_volume` | Verificar volume | Avalia volume de candidatos disponíveis |
| `proactive_suggest` | Sugestão proativa | Sugere ações proativas de sourcing |
| `filter_candidates` | Filtrar candidatos | Filtros avançados |
| `rank_candidates` | Rankear candidatos | Ordena por pontuação |
| `compare_candidates` | Comparar candidatos | Comparação lado a lado |
| `talent_pool_search` | Busca talent pool | Busca no pool interno |
| `pearch_search` | Busca Pearch | Busca via Pearch AI (externo) |
| `build_search_strategy` | Estratégia de busca | Define estratégia de sourcing |
| `analyze_search_results` | Analisar resultados | Analisa efetividade da busca |
| `feedback_search` | Feedback de busca | Registra feedback de resultados |
| `expand_search` | Expandir busca | Amplia critérios |
| `contact_candidates` | Contatar candidatos | Inicia outreach |
| `screen_candidates` | Triagem rápida | Screening inicial |
| `assess_market` | Avaliar mercado | Análise de mercado de talentos |
| `export_candidates` | Exportar candidatos | Exporta lista |
| `import_candidates` | Importar candidatos | Importa de fonte externa |
| `dedup_candidates` | Deduplicar | Remove duplicados |
| `tag_candidates` | Taguear candidatos | Adiciona tags |
| `engagement_pipeline` | Pipeline engagement | Fluxo de engajamento |
| `schedule_outreach` | Agendar outreach | Agenda contato futuro |

### 6.2 Job Management (29 actions)

| Action ID | Nome | Confirmação |
|-----------|------|-------------|
| `create_job` | Criar vaga | - |
| `guided_wizard` | Wizard guiado | - |
| `extract_requirements` | Extrair requisitos | - |
| `generate_rubrics` | Gerar rubricas | - |
| `update_job` | Atualizar vaga | - |
| `health_check` | Health check | - |
| `suggest_strategy` | Sugerir estratégia | - |
| `duplicate_job` | Duplicar vaga | - |
| `create_from_template` | Criar de template | - |
| `clone_job` | Clonar vaga | - |
| `close_job` | Fechar vaga | - |
| `pause_job` | Pausar vaga | - |
| `get_benefits` | Obter benefícios | - |
| `suggest_jd_improvements` | Melhorar JD | - |
| `detect_criteria` | Detectar critérios | - |
| `generate_wsi_questions` | Gerar perguntas WSI | - |
| `advance_wizard_step` | Avançar etapa wizard | - |
| `get_wizard_step_data` | Dados da etapa | - |
| `enrich_jd` | Enriquecer JD | - |
| `import_jd` | Importar JD | - |
| `generate_jd` | Gerar JD | - |
| `job_analytics` | Analytics de vagas | - |
| `qualify_job` | Qualificar vaga | - |
| `publish_job` | Publicar vaga | - |
| `job_status_webhook` | Webhook de status | - |
| `search_templates` | Buscar templates | - |
| `apply_template` | Aplicar template | - |
| `analyze_jd` | Analisar JD | - |
| `suggest_compensation` | Sugerir compensação | - |

### 6.3 CV Screening (25 actions)

| Action ID | Nome | Descrição |
|-----------|------|-----------|
| `parse_cv` | Analisar CV | Extrair dados estruturados |
| `auto_screen` | Triagem automática | Triagem contra requisitos |
| `batch_screen` | Triagem em lote | Múltiplos candidatos |
| `calculate_wsi_score` | Calcular WSI | Score WSI baseado no CV |
| `rank_candidates` | Rankear candidatos | Por score WSI |
| `dynamic_cutoff` | Corte dinâmico | Top 25% |
| `detect_red_flags` | Detectar red flags | No CV |
| `check_saturation` | Verificar saturação | Do pipeline |
| `check_eligibility` | Verificar elegibilidade | Do candidato |
| `classify_bloom` | Classificar Bloom | Taxonomia de Bloom |
| `classify_dreyfus` | Classificar Dreyfus | Modelo Dreyfus |
| `map_big_five` | Mapear Big Five | Traços comportamentais |
| `validate_cbi` | Validar CBI | Framework CBI |
| `generate_report` | Gerar parecer | Parecer completo |
| `compare_candidates` | Comparar candidatos | Lado a lado |
| `calibrate_model` | Calibrar modelo | Com feedback |
| `explain_score` | Explicar score | Detalhamento |
| `evaluate_rubric` | Avaliar rubrica | Rubrica estruturada |
| `generate_questions` | Gerar perguntas | Perguntas WSI |
| `adjust_questions` | Ajustar perguntas | Refinar com IA |
| `voice_screening` | Triagem por voz | WSI por voz |
| `normalize_scores` | Normalizar scores | Entre candidatos |
| `assess_seniority` | Avaliar senioridade | Multi-signal |
| `send_feedback` | Enviar feedback | Personalizado |
| `pre_qualify` | Pré-qualificar | Antes da triagem |

### 6.4 Communication (20 actions)

| Action ID | Nome | Requer Confirmação |
|-----------|------|--------------------|
| `send_email` | Enviar Email | Sim |
| `send_bulk_email` | Enviar Email em Massa | Sim |
| `send_candidate_report` | Enviar Parecer ao Gestor | Sim |
| `send_progress_report` | Relatório de Progresso | Não |
| `send_kpi_report` | Relatório de KPIs | Sim |
| `send_feedback` | Enviar Feedback | Sim |
| `create_template` | Criar Template | Não |
| `edit_template` | Editar Template | Não |
| `list_templates` | Listar Templates | Não |
| `preview_template` | Visualizar Template | Não |
| `notify_stakeholders` | Notificar Stakeholders | Sim |
| `send_whatsapp` | Enviar WhatsApp | Sim |
| `send_teams_message` | Enviar Teams | Sim |
| `send_sms` | Enviar SMS | Sim |
| `get_communication_history` | Histórico | Não |
| `send_screening_invite` | Convite de Triagem | Sim |
| `send_interview_invite` | Convite de Entrevista | Sim |
| `update_preferences` | Preferências de Comunicação | Não |
| `manage_webhook` | Gerenciar Webhook | Não |
| `handle_data_request` | Solicitação LGPD | Sim |

### 6.5 Interview & Scheduling (20 actions)

| Action ID | Nome | Requer Confirmação |
|-----------|------|--------------------|
| `schedule_interview` | Agendar Entrevista | Sim |
| `reschedule_interview` | Reagendar Entrevista | Sim |
| `cancel_interview` | Cancelar Entrevista | Sim |
| `check_availability` | Verificar Disponibilidade | Não |
| `generate_self_scheduling_link` | Link de Auto-agendamento | Não |
| `find_common_slots` | Horários Comuns | Não |
| `send_reminder` | Enviar Lembrete | Sim |
| `schedule_reminders` | Agendar Lembretes | Não |
| `list_today_interviews` | Entrevistas de Hoje | Não |
| `resolve_conflict` | Resolver Conflito | Não |
| `start_wsi_interview` | Iniciar Entrevista WSI | Não |
| `send_question` | Enviar Pergunta | Não |
| `analyze_response` | Analisar Resposta | Não |
| `transcribe_audio` | Transcrever Áudio | Não |
| `analyze_voice` | Analisar Voz | Não |
| `detect_evasive` | Detectar Evasiva | Não |
| `generate_followup` | Follow-up | Não |
| `complete_interview` | Finalizar Entrevista | Não |
| `interview_qa` | Q&A Entrevista | Não |
| `start_quick_screening` | Triagem Rápida | Não |

### 6.6 Analytics (18 actions)

| Action ID | Nome |
|-----------|------|
| `generate_kpi_report` | Gerar Relatório de KPIs |
| `analyze_funnel` | Analisar Funil de Conversão |
| `job_health_check` | Verificar Saúde da Vaga |
| `detect_anomalies` | Detectar Anomalias |
| `compare_periods` | Comparar Períodos |
| `forecast` | Previsão de Métricas |
| `suggest_strategy` | Sugerir Estratégia |
| `answer_data_question` | Responder Pergunta sobre Dados |
| `get_job_insights` | Insights da Vaga |
| `generate_job_report` | Relatório da Vaga |
| `generate_candidate_report` | Relatório de Candidato |
| `get_search_analytics` | Analytics de Busca |
| `get_wizard_analytics` | Analytics do Wizard |
| `predict_hiring_probability` | Probabilidade de Contratação |
| `predict_time_to_fill` | Tempo de Preenchimento |
| `predict_dropout_risk` | Risco de Desistência |
| `get_dashboard_data` | Dados do Dashboard |
| `get_agent_monitoring` | Monitoramento de Agentes |

### 6.7 ATS Integration (18 actions)

| Action ID | Nome | Requer Confirmação |
|-----------|------|--------------------|
| `sync_candidate` | Sincronizar Candidato | Não |
| `sync_job` | Sincronizar Vaga | Não |
| `bulk_sync` | Sincronização em Massa | Sim |
| `pull_candidates` | Importar Candidatos | Não |
| `pull_jobs` | Importar Vagas | Não |
| `check_sync_status` | Verificar Status | Não |
| `configure_ats` | Configurar ATS | Sim |
| `list_connections` | Listar Conexões | Não |
| `test_connection` | Testar Conexão | Não |
| `map_fields` | Mapear Campos | Sim |
| `view_sync_log` | Ver Log | Não |
| `resolve_conflict` | Resolver Conflito | Sim |
| `update_status_ats` | Atualizar Status | Não |
| `send_score_ats` | Enviar Score | Não |
| `sync_interview_result` | Sincronizar Resultado | Não |
| `enable_webhook` | Ativar Webhook | Não |
| `disable_webhook` | Desativar Webhook | Não |
| `view_field_mapping` | Ver Mapeamento | Não |

### 6.8 Automation (20 actions)

| Action ID | Nome | Requer Confirmação |
|-----------|------|--------------------|
| `create_task` | Criar Tarefa | Não |
| `list_tasks` | Listar Tarefas | Não |
| `complete_task` | Concluir Tarefa | Sim |
| `cancel_task` | Cancelar Tarefa | Sim |
| `decompose_task` | Decompor Tarefa | Não |
| `plan_execution` | Planejar Execução | Não |
| `get_next_tasks` | Próximas Tarefas | Não |
| `create_automation` | Criar Automação | Sim |
| `list_automations` | Listar Automações | Não |
| `enable_automation` | Ativar Automação | Sim |
| `disable_automation` | Desativar Automação | Sim |
| `trigger_automation` | Disparar Automação | Sim |
| `view_automation_log` | Ver Log | Não |
| `configure_stage_automation` | Automação de Etapa | Sim |
| `predict_substatus` | Prever Sub-status | Não |
| `check_proactive_alerts` | Alertas Proativos | Não |
| `configure_alert` | Configurar Alerta | Sim |
| `schedule_recurring` | Tarefa Recorrente | Sim |
| `view_task_dependencies` | Ver Dependências | Não |
| `run_autonomous_check` | Verificação Autônoma | Sim |

### 6.9 Recruiter Assistant (20 actions)

| Action ID | Nome | Tags |
|-----------|------|------|
| `daily_briefing` | Briefing Diário | briefing, daily, delegate_to_agent |
| `end_of_day_summary` | Resumo do Dia | summary, daily, delegate_to_agent |
| `quick_question` | Pergunta Rápida | question, quick, delegate_to_agent |
| `plan_day` | Planejar Dia | planning, productivity |
| `pipeline_health` | Saúde do Pipeline | pipeline, health, analysis |
| `stale_candidates` | Candidatos Parados | candidates, stale, pipeline |
| `move_candidate` | Mover Candidato | candidate, move, stage |
| `suggest_action` | Sugerir Ação | suggestion, action, ai |
| `search_context` | Buscar Contexto | search, context, history |
| `save_memory` | Salvar Memória | memory, save, persistent |
| `recall_memory` | Recuperar Memória | memory, recall, search |
| `conversation_summary` | Resumo da Conversa | conversation, summary |
| `kanban_analysis` | Análise do Kanban | kanban, analysis, ai |
| `calibrate_profile` | Calibrar Perfil | calibration, profile |
| `send_notification` | Enviar Notificação | notification, proactive |
| `track_goals` | Acompanhar Metas | goals, tracking, metrics |
| `generate_insights` | Gerar Insights | insights, proactive |
| `compare_candidates` | Comparar Candidatos | candidates, comparison |
| `stage_recommendation` | Recomendar Etapa | stage, recommendation |
| `help_command` | Ajuda | help, commands |

### 6.10 Pipeline Transition (5 actions)

| Action ID | Nome | Requer Confirmação |
|-----------|------|--------------------|
| `move_candidate` | Mover Candidato | Sim |
| `interpret_context` | Interpretar Contexto | Não |
| `predict_sub_status` | Predizer Sub-Status | Não |
| `suggest_next_action` | Sugerir Próxima Ação | Não |
| `list_pipeline_stages` | Listar Etapas | Não |

---

## 7. Catálogo de Ferramentas (Tools)

As ferramentas são os executores reais das ações. Cada domínio expõe tools que podem ser chamados pelos agentes.

### 7.1 Sourcing Tools (19)

| Tool ID | Nome | Descrição |
|---------|------|-----------|
| `search_candidates` | Buscar Candidatos | Busca com filtros (skills, senioridade, localização, experiência, score) |
| `search_jobs` | Buscar Vagas | Busca vagas por status, departamento, senioridade |
| `boolean_search` | Busca Booleana | Gera e executa queries booleanas avançadas |
| `semantic_search` | Busca Semântica | Busca por similaridade de embeddings |
| `pearch_search` | Busca Pearch AI | Busca candidatos externos via Pearch |
| `candidate_match` | Match de Candidatos | Calcula compatibilidade candidato-vaga com pesos |
| `talent_pool_query` | Consulta Talent Pool | Busca no pool interno de talentos |
| `search_analytics` | Análise de Busca | Métricas de efetividade de buscas |
| `volume_check` | Verificação de Volume | Avalia volume disponível para perfil |
| `sourcing_search_candidates` | Busca Avançada | Busca candidatos com filtros avançados de sourcing |
| `sourcing_add_candidate_to_vacancy` | Adicionar a Vaga | Associa candidato a uma vaga |
| `sourcing_get_candidate_details` | Detalhes do Candidato | Obtém detalhes completos de um candidato |
| `sourcing_get_candidate_history` | Histórico | Obtém histórico de interações do candidato |
| `sourcing_get_candidate_stats` | Estatísticas | Estatísticas de candidatura e performance |
| `sourcing_get_talent_quality` | Qualidade do Pool | Análise de qualidade do talent pool |
| `sourcing_rank_candidates` | Ranking | Rankeia candidatos por score e fit |
| `sourcing_reject_candidate` | Rejeitar | Processa rejeição de candidato |
| `sourcing_shortlist_candidate` | Shortlist | Adiciona candidato à shortlist |
| `sourcing_update_candidate_stage` | Atualizar Etapa | Move candidato entre etapas do pipeline |

### 7.2 Job Management Tools (13)

| Tool ID | Nome |
|---------|------|
| `create_job_vacancy` | Criar Vaga |
| `update_job_vacancy` | Atualizar Vaga |
| `close_job_vacancy` | Fechar Vaga |
| `pause_job_vacancy` | Pausar Vaga |
| `duplicate_job_vacancy` | Duplicar Vaga |
| `generate_job_description` | Gerar JD |
| `enrich_job_description` | Enriquecer JD |
| `import_job_description` | Importar JD |
| `search_job_templates` | Buscar Templates |
| `get_job_health` | Health Check |
| `get_wizard_step` | Etapa do Wizard |
| `advance_wizard` | Avançar Wizard |
| `get_job_analytics` | Analytics de Vagas |

### 7.3 CV Screening Tools (12)

| Tool ID | Nome |
|---------|------|
| `parse_cv` | Parse CV |
| `score_cv` | Score CV |
| `evaluate_rubric` | Avaliar Rubrica |
| `calculate_wsi` | Calcular WSI |
| `generate_wsi_questions` | Gerar Perguntas WSI |
| `adjust_wsi_questions` | Ajustar Perguntas |
| `check_eligibility` | Verificar Elegibilidade |
| `normalize_scores` | Normalizar Scores |
| `assess_seniority` | Avaliar Senioridade |
| `send_candidate_feedback` | Enviar Feedback |
| `pre_qualify_candidate` | Pré-qualificar |
| `run_screening_pipeline` | Pipeline de Triagem |

### 7.4 Communication Tools (10)

| Tool ID | Nome |
|---------|------|
| `communication_send_email` | Enviar Email |
| `communication_send_bulk` | Email em Massa |
| `communication_send_whatsapp` | WhatsApp |
| `communication_send_teams` | Microsoft Teams |
| `communication_create_template` | Criar Template |
| `communication_list_templates` | Listar Templates |
| `communication_preview_template` | Preview Template |
| `communication_get_history` | Histórico |
| `communication_manage_webhook` | Gerenciar Webhook |
| `communication_data_request` | Solicitação LGPD |

### 7.5 Interview Scheduling Tools (10)

| Tool ID | Nome |
|---------|------|
| `scheduling_schedule_interview` | Agendar Entrevista |
| `scheduling_reschedule` | Reagendar |
| `scheduling_cancel` | Cancelar |
| `scheduling_check_availability` | Verificar Disponibilidade |
| `scheduling_self_scheduling_link` | Link Auto-agendamento |
| `scheduling_find_slots` | Encontrar Horários |
| `scheduling_send_reminder` | Enviar Lembrete |
| `scheduling_list_today` | Entrevistas de Hoje |
| `scheduling_transcribe_audio` | Transcrever Áudio |
| `scheduling_analyze_voice` | Analisar Voz |

### 7.6 Analytics Tools (10)

| Tool ID | Nome |
|---------|------|
| `analytics_generate_kpi` | Gerar KPIs |
| `analytics_analyze_funnel` | Analisar Funil |
| `analytics_job_health` | Saúde da Vaga |
| `analytics_detect_anomalies` | Detectar Anomalias |
| `analytics_get_insights` | Insights |
| `analytics_generate_report` | Gerar Relatório |
| `analytics_search_analytics` | Analytics de Busca |
| `analytics_predict` | Analytics Preditivo |
| `analytics_dashboard` | Dashboard |
| `analytics_monitoring` | Monitoramento de Agentes |

### 7.7 ATS Integration Tools (10)

| Tool ID | Nome |
|---------|------|
| `ats_sync_candidate` | Sincronizar Candidato |
| `ats_sync_job` | Sincronizar Vaga |
| `ats_pull_candidates` | Importar Candidatos |
| `ats_pull_jobs` | Importar Vagas |
| `ats_check_status` | Verificar Status |
| `ats_list_connections` | Listar Conexões |
| `ats_test_connection` | Testar Conexão |
| `ats_view_sync_log` | Ver Log |
| `ats_update_status` | Atualizar Status |
| `ats_send_score` | Enviar Score |

### 7.8 Automation Tools (10)

| Tool ID | Nome |
|---------|------|
| `automation_create_task` | Criar Tarefa |
| `automation_list_tasks` | Listar Tarefas |
| `automation_complete_task` | Concluir Tarefa |
| `automation_cancel_task` | Cancelar Tarefa |
| `automation_create_rule` | Criar Regra |
| `automation_list_rules` | Listar Regras |
| `automation_enable_rule` | Ativar Automação |
| `automation_disable_rule` | Desativar Automação |
| `automation_trigger` | Disparar Automação |
| `automation_view_log` | Ver Log |

### 7.9 Recruiter Assistant Tools (10)

| Tool ID | Nome |
|---------|------|
| `assistant_pipeline_health` | Saúde do Pipeline |
| `assistant_stale_candidates` | Candidatos Parados |
| `assistant_move_candidate` | Mover Candidato |
| `assistant_search_context` | Buscar Contexto |
| `assistant_save_memory` | Salvar Memória |
| `assistant_recall_memory` | Recuperar Memória |
| `assistant_conversation_summary` | Resumo da Conversa |
| `assistant_kanban_analysis` | Análise Kanban |
| `assistant_send_notification` | Enviar Notificação |
| `assistant_track_goals` | Acompanhar Metas |

### 7.10 Pipeline Transition Tools (5)

| Tool ID | Nome |
|---------|------|
| `move_candidate` | Mover Candidato (via API REST) |
| `interpret_context` | Interpretar Contexto (via LLM) |
| `predict_sub_status` | Predizer Sub-Status |
| `suggest_next_action` | Sugerir Próxima Ação |
| `list_pipeline_stages` | Listar Etapas |

### 7.11 ReAct Agent Tool Registries (89 tools)

As seções 7.1–7.10 documentam as **tools legacy** (109 tools) usadas pela arquitetura original de agentes via LangGraph e chamadas diretas. Com a introdução da **arquitetura ReAct** (Seção 3.23), um novo catálogo de tools foi criado usando o padrão `ToolDefinition` + `tool_registry.py`.

**Diferença fundamental:**
- **Legacy tools** (7.1–7.10): Funções Python chamadas diretamente por agentes LangGraph ou via mapeamento estático action→tool. Acoplamento forte entre agente e tool.
- **ReAct tool registries** (7.11): Cada tool é registrada como `ToolDefinition` (name, description, parameters JSON Schema, function). O `ReActLoop` decide autonomamente quais tools chamar via raciocínio Thought→Action→Observation. Desacoplamento total — o agente escolhe tools por descrição semântica, não por código hardcoded.

**Padrão de arquivo:** Cada agente ReAct possui um `*_tool_registry.py` que exporta `TOOL_DEFINITIONS: List[ToolDefinition]` e opcionalmente `STAGE_TOOLS: Dict[str, List[str]]` para filtrar tools por estágio do wizard/fluxo.

**Total: 89 tools ReAct** distribuídas em 7 registries:

#### 7.11.1 Wizard Tool Registry (9 tools)

**Arquivo:** `app/domains/job_management/agents/wizard_tool_registry.py`
**Agente:** `WizardReActAgent`
**Estágios:** input-evaluation, jd-enrichment, salary, competencies, wsi-questions, review-publish

| Tool | Descrição | Integração |
|------|-----------|------------|
| `validate_job_requirements` | Valida requisitos contra viés discriminatório | FairnessGuard 3-tier |
| `get_salary_benchmarks` | Benchmarks salariais reais (SQL interno + mercado Robert Half/Gupy 2024) | PostgreSQL + dados estáticos |
| `search_salary_benchmark` | Busca benchmarks salariais de mercado por cargo | Dados de mercado |
| `validate_job_fields` | Valida campos preenchidos, score de completude | Validação determinística |
| `get_job_suggestions` | Sugestões de IA para campos (skills, benefícios, competências) | LLM |
| `save_job_draft` | Salva rascunho da vaga no banco | PostgreSQL |
| `get_company_config` | Busca configurações da empresa (benefícios, políticas, cultura) | PostgreSQL |
| `generate_enriched_jd` | Gera JD enriquecida com sugestões baseadas em benchmarks | LLM + dados de mercado |
| `check_job_draft_health` | Avalia saúde do rascunho: riscos, campos faltantes, salário vs mercado | Determinístico + benchmarks |

#### 7.11.2 Kanban Tool Registry (14 tools)

**Arquivo:** `app/domains/recruiter_assistant/agents/kanban_tool_registry.py`
**Agente:** `KanbanReActAgent`

| Tool | Descrição | Integração |
|------|-----------|------------|
| `get_pipeline_benchmarks` | Benchmarks reais do pipeline via SQL (tempo médio por etapa, comparação empresa) | PostgreSQL |
| `get_pipeline_summary` | Resumo geral do pipeline com contagem por etapa | Dados agregados |
| `get_stage_metrics` | Métricas detalhadas de etapa específica (volume, tempo, conversão) | Dados agregados |
| `list_stage_candidates` | Lista candidatos em etapa específica | Dados do pipeline |
| `analyze_stage` | Análise profunda de etapa (saúde, riscos, recomendações) | Análise estratégica |
| `identify_bottlenecks` | Identifica gargalos em todo o pipeline | Análise cross-stage |
| `get_candidate_aging` | Relatório de aging (candidatos parados >N dias) | PostgreSQL |
| `compare_stages` | Compara métricas entre etapas | Análise comparativa |
| `suggest_movements` | Sugestões inteligentes de movimentação de candidatos | IA + dados |
| `batch_move_candidates` | Move múltiplos candidatos entre etapas | Ação em massa |
| `send_batch_communication` | Comunicação em massa (email, WhatsApp, SMS) | Multi-channel |
| `start_screening_batch` | Inicia screening WSI para múltiplos candidatos | WSI engine |
| `generate_pipeline_report` | Gera relatório analytics do pipeline | Relatórios |
| `check_rejection_fairness` | Valida motivo de rejeição contra viés discriminatório | FairnessGuard 3-tier |

#### 7.11.3 Talent Funnel Tool Registry (12 tools)

**Arquivo:** `app/domains/recruiter_assistant/agents/talent_tool_registry.py`
**Agente:** `TalentReActAgent`
**Estágios:** overview, search, analysis, action

| Tool | Descrição | Integração |
|------|-----------|------------|
| `search_candidates` | Busca candidatos por skills, experiência, localização | Busca interna |
| `list_candidates` | Lista candidatos no funil com filtros de status | Dados do funil |
| `view_candidate_profile` | Visualiza perfil completo do candidato | Dados candidato |
| `compare_candidates` | Compara 2+ candidatos lado a lado (skills, experiência, scores) | Análise comparativa |
| `rank_candidates` | Rankeia candidatos por fit score para uma vaga | Scoring + ranking |
| `analyze_skills` | Analisa match de competências candidato vs vaga | Skill matching |
| `recommend_actions` | Gera recomendações de ações para candidatos | IA |
| `create_shortlist` | Cria shortlist a partir de candidatos selecionados | Ação |
| `export_report` | Exporta relatório de análise (ranking, comparison, skills) | Relatórios |
| `check_search_fairness` | Valida critérios de busca contra viés discriminatório | FairnessGuard 3-tier |
| `get_talent_pool_benchmarks` | Benchmarks reais do pool via SQL (tamanho, score médio, distribuição) | PostgreSQL |
| `check_pool_health` | Avalia saúde do pool: riscos (pool pequeno, scores baixos, estagnação) | PostgreSQL + análise |

#### 7.11.4 Jobs Management Tool Registry (13 tools)

**Arquivo:** `app/domains/recruiter_assistant/agents/jobs_mgmt_tool_registry.py`
**Agente:** `JobsMgmtReActAgent`
**Estágios:** overview, analysis, action

| Tool | Descrição | Integração |
|------|-----------|------------|
| `validate_job_action_fairness` | Valida ações de gestão contra viés discriminatório | FairnessGuard 3-tier |
| `get_recruitment_benchmarks` | Benchmarks reais de recrutamento via SQL (TTF, fill rate, comparação mercado) | PostgreSQL + INDUSTRY_BENCHMARKS |
| `list_jobs` | Lista vagas ativas com status e métricas | Dados do portfolio |
| `view_job_details` | Detalhes completos de uma vaga (pipeline, candidatos, métricas) | Dados da vaga |
| `get_portfolio_metrics` | Métricas agregadas do portfolio (taxa preenchimento, tempo médio) | Dados agregados |
| `compare_jobs` | Compara múltiplas vagas lado a lado | Análise comparativa |
| `check_sla` | Verifica compliance de SLA (vagas em risco, vencidas) | Verificação SLA |
| `analyze_bottlenecks` | Identifica gargalos no pipeline por departamento | Análise cross-job |
| `pause_job` | Pausa vaga ativa (requer motivo e confirmação) | Ação |
| `reopen_job` | Reabre vaga pausada/fechada | Ação |
| `close_job` | Fecha vaga definitivamente (requer motivo) | Ação |
| `update_priority` | Atualiza prioridade da vaga (alta, média, baixa) | Ação |
| `generate_report` | Gera relatório do portfolio com métricas e recomendações | Relatórios |

#### 7.11.5 Policy Tool Registry (13 tools)

**Arquivo:** `app/domains/hiring_policy/agents/policy_tool_registry.py`
**Agente:** `PolicyReActAgent`
**Estágios:** onboarding, review, consulting

| Tool | Descrição | Integração |
|------|-----------|------------|
| `get_current_policy` | Carrega políticas atuais da empresa (pipeline, scheduling, communication, screening, automation) | PostgreSQL |
| `save_policy_field` | Salva campo específico de política no banco | PostgreSQL |
| `get_policy_summary` | Resumo das políticas configuradas (blocos, progresso, autonomia) | PostgreSQL |
| `validate_policy_compliance` | Valida texto de política contra viés (FairnessGuard + deep check semântico) | FairnessGuard 3-tier |
| `get_company_context` | Contexto da empresa (jobs, candidatos, perfil, indústria) | PostgreSQL |
| `get_industry_benchmarks` | Benchmarks por setor (8 setores: technology, finance, retail, healthcare, legal, education, manufacturing, services) | Dados estáticos verificáveis |
| `explain_policy_impact` | Explica impacto de uma política com simulação | Análise |
| `get_setup_progress` | Progresso do setup de políticas | PostgreSQL |
| `get_platform_benchmarks` | Benchmarks reais da plataforma via SQL (TTF, preenchimento, por etapa) | PostgreSQL |
| `detect_policy_impact_anomalies` | Detecta anomalias no impacto de políticas | PostgreSQL + análise |
| `get_policy_effectiveness_report` | Relatório de efetividade das políticas | PostgreSQL + análise |
| `save_policy_block` | Salva bloco completo de política | PostgreSQL |
| `apply_industry_defaults` | Aplica defaults do setor à política | INDUSTRY_BENCHMARKS |

#### 7.11.6 Sourcing Tool Registry (14 tools)

**Arquivo:** `app/domains/sourcing/agents/sourcing_tool_registry.py`
**Agente:** `SourcingReActAgent`

| Tool | Descrição | Integração |
|------|-----------|------------|
| `set_search_criteria` | Define parâmetros de busca (role, skills, localização, experiência, salário) | Configuração |
| `suggest_skills` | Sugere skills relevantes baseado em dados reais de candidatos | PostgreSQL |
| `search_candidates` | Executa busca com filtros (skills, localização, senioridade, role) | PostgreSQL |
| `filter_results` | Aplica filtros adicionais aos resultados (experiência, localização, status) | PostgreSQL |
| `view_candidate` | Visualiza detalhes de candidato individual | Dados candidato |
| `analyze_profile` | Análise de perfil com strengths/gaps (skills, experiência, certificações) | PostgreSQL + análise |
| `compare_candidates` | Compara múltiplos perfis com ranking por score | PostgreSQL |
| `score_candidate` | Aplica scoring WSI candidato vs vaga (skill match, seniority, experiência) | PostgreSQL + WSI |
| `add_to_shortlist` | Adiciona candidato à shortlist (com verificação de duplicata) | PostgreSQL |
| `remove_from_shortlist` | Remove candidato da shortlist | PostgreSQL |
| `rank_candidates` | Rankeia candidatos por múltiplos critérios | Ranking engine |
| `send_outreach` | Envia mensagem de outreach para candidato | Comunicação |
| `generate_message` | Gera mensagem personalizada para candidato | LLM |
| `track_response` | Rastreia resposta de candidato a outreach | Tracking |

#### 7.11.7 Pipeline Tool Registry (14 tools)

**Arquivo:** `app/domains/cv_screening/agents/pipeline_tool_registry.py`
**Agente:** `PipelineReActAgent`

| Tool | Descrição | Integração |
|------|-----------|------------|
| `view_candidate_profile` | Perfil completo com dados de pipeline (stage, status, scores) | PostgreSQL |
| `move_candidate` | Move candidato entre etapas do pipeline (com histórico) | PostgreSQL |
| `analyze_cv` | Análise de CV com skills, certificações, expertise | PostgreSQL |
| `run_wsi_screening` | Executa/consulta screening WSI (technical, behavioral, overall) | PostgreSQL + WSI |
| `schedule_interview` | Agenda entrevista com persistência no banco | PostgreSQL |
| `send_communication` | Envia comunicação (email/WhatsApp) com log | PostgreSQL |
| `add_notes` | Adiciona notas ao candidato no pipeline (com timestamp) | PostgreSQL |
| `batch_move` | Move múltiplos candidatos entre etapas | PostgreSQL |
| `add_to_shortlist` | Adiciona candidato à pré-seleção | PostgreSQL |
| `view_screening_results` | Consulta resultados de screening (LIA score, WSI, match) | PostgreSQL |
| `view_interview_notes` | Consulta notas de entrevistas realizadas | PostgreSQL |
| `generate_offer` | Gera proposta/oferta para candidato | Geração |
| `finalize_hiring` | Finaliza processo de contratação | PostgreSQL |
| `update_status` | Atualiza status do candidato no pipeline | PostgreSQL |

#### Resumo de Contagens — Legacy vs ReAct

| Categoria | Contagem | Observação |
|-----------|----------|------------|
| **Legacy tools** (7.1–7.10) | 109 | Arquitetura original LangGraph, chamadas diretas |
| **ReAct tool registries** (7.11) | 89 | Nova arquitetura ReAct, seleção autônoma via ToolDefinition |
| **Total combinado** | 198 | Feature flag `USE_REACT_AGENTS` controla qual camada é usada |

**Nota:** Com `USE_REACT_AGENTS=true` (default), os 7 agentes ReAct usam exclusivamente as 89 tools de seus registries. As 109 tools legacy permanecem ativas para agentes não-ReAct e como fallback automático.

---

## 8. Catálogo de Serviços (Services)

**Total: 137 serviços** (incluindo sub-serviços e providers por domínio)

### 8.1 Visão Geral por Domínio

| Domínio | Quantidade | Principais Responsabilidades |
|---------|-----------|------------------------------|
| job_management | 29 | Wizard, JD generation, templates, vagas, analytics |
| communication | 26 | Email, WhatsApp, Teams, SMS, webhooks, LGPD |
| cv_screening | 20 | WSI, scoring, parsing, screening, calibração |
| automation | 17 | Engine, triggers, scheduler, alertas, monitor |
| sourcing | 12 | Pipeline, busca, WRF, Pearch, Apify |
| recruiter_assistant | 10 | Kanban, Talent, Jobs Mgmt, pipeline, memória |
| analytics | 10 | Relatórios, predição, monitoramento, observabilidade |
| ats_integration | 8 | Sync, Gupy, Pandape, Merge, clientes ATS |
| interview_scheduling | 4 | Agendamento, calendário, Deepgram, transcrição |
| hiring_policy | 1 | PolicyReActAgent (lógica embutida no agente + tools) |

### 8.2 Serviços por Domínio

#### job_management (29 serviços)

| Serviço | Função |
|---------|--------|
| `wizard_orchestrator_service` | Orquestra fluxo do wizard |
| `wizard_data_priority_service` | Prioridade de dados no wizard |
| `wizard_analytics_service` | Analytics do wizard |
| `jd_generation_service` | Geração de JD com IA |
| `jd_enrichment_service` | Enriquecimento de JD |
| `jd_import_service` | Importação de JD existente |
| `jd_template_service` | Templates de JD |
| `jd_template_cache_service` | Cache de templates |
| `job_vacancy_service` | CRUD de vagas |
| `job_vacancy_route_service` | Roteamento de vagas |
| `job_context_service` | Contexto da vaga para agentes |
| `job_embedding_service` | Embeddings de vagas (PGVector) |
| `job_qualification_service` | Qualificação de vagas |
| `job_template_service` | Gestão de templates |
| `job_clone_service` | Clonagem de vagas |
| `job_board_service` | Publicação em job boards |
| `job_alert_service` | Alertas de vagas |
| `job_audit_service` | Auditoria de vagas |
| `job_status_webhook_service` | Webhooks de status |
| `job_analytics_prompt_service` | Prompts analíticos |
| `job_insights_service` | Insights de vagas |
| `job_report_service` | Relatórios de vagas |
| `job_pattern_service` | Padrões de vagas |
| `seniority_jd_analyzer` | Análise de senioridade na JD |
| `template_importer_service` | Importação de templates |
| `template_learning_service` | Learning de templates |
| `template_seeder` | Seed de templates iniciais |
| `vacancy_search_service` | Busca de vagas |
| `outcome_tracker` | Rastreamento de resultados |

#### communication (26 serviços)

| Serviço | Função |
|---------|--------|
| `communication_service` | Serviço principal de comunicação |
| `communication_dispatcher` | Dispatcher de mensagens |
| `communication_history_service` | Histórico de comunicações |
| `email_service` | Serviço de email |
| `email_providers` | Abstrações de provedores |
| `email_providers/base` | Interface base de email |
| `email_providers/resend_provider` | Provider Resend |
| `email_providers/mailgun_provider` | Provider Mailgun |
| `email_templates_data` | Dados de templates de email |
| `whatsapp_service` | Serviço WhatsApp |
| `whatsapp_provider` | Provider WhatsApp |
| `whatsapp_factory` | Factory de WhatsApp |
| `whatsapp_twilio_service` | WhatsApp via Twilio |
| `whatsapp_meta_service` | WhatsApp via Meta API |
| `teams_service` | Serviço Microsoft Teams |
| `teams_auth` | Autenticação Teams |
| `teams_bot` | Bot do Teams |
| `teams_simple` | Integração Teams simplificada |
| `teams_recording_service` | Gravação de reuniões |
| `data_request_service` | Requisições de dados (LGPD) |
| `data_request_whatsapp_service` | Requisições via WhatsApp |
| `transition_dispatch_service` | Dispatch em transições |
| `webhook_service` | Serviço de webhooks |
| `infer_behavior_service` | Inferência de comportamento |
| `interpret_context_llm_service` | Interpretação por LLM |
| `return_event_service` | Eventos de retorno |

#### cv_screening (20 serviços)

| Serviço | Função |
|---------|--------|
| `wsi_service` | Serviço principal WSI |
| `wsi_screening_pipeline` | Pipeline de screening WSI |
| `wsi_question_service` | Gestão de perguntas WSI |
| `wsi_question_generator` | Geração de perguntas por IA |
| `wsi_question_adjuster` | Ajuste de perguntas |
| `wsi_deterministic_scorer` | Scoring determinístico |
| `wsi_voice_orchestrator` | Orquestrador de voz WSI |
| `cv_parser` | Parser de CV (PDF/DOCX) |
| `cv_scoring_service` | Scoring de CV |
| `screening_question_set_service` | Set de perguntas de screening |
| `evaluation_criteria_service` | Critérios de avaliação |
| `eligibility_verification_service` | Verificação de elegibilidade |
| `pre_qualification_service` | Pré-qualificação |
| `rubric_evaluation_service` | Avaliação por rubrica |
| `calibration_profiles` | Perfis de calibração |
| `seniority_context_calibrator` | Calibração por senioridade |
| `seniority_resolver` | Resolução de senioridade |
| `seniority_utils` | Utilidades de senioridade |
| `score_normalization_service` | Normalização de scores |
| `personalized_feedback_service` | Feedback personalizado |

#### automation (17 serviços)

| Serviço | Função |
|---------|--------|
| `automation_service` | Serviço principal de automação |
| `automation_handlers` | Handlers de automação |
| `automation_scheduler` | Scheduler de automações |
| `automation_trigger_service` | Serviço de triggers |
| `autonomous_agent_service` | Serviço de agentes autônomos |
| `stage_automation_engine` | Engine de automação de estágios |
| `stage_transition_automation` | Automação de transições |
| `pipeline_monitor` | Monitor de pipeline |
| `proactive_service` | Serviço proativo |
| `proactive_alert_service` | Alertas proativos |
| `candidate_context_aggregator` | Agregador de contexto |
| `prediction_action_bridge` | Ponte predição-ação |
| `event_action_connector` | Conector evento-ação |
| `pattern_applier` | Aplicador de padrões |
| `learning_automation` | Aprendizado de automações |
| `planned_task_service` | Serviço de tarefas planejadas |
| `task_service` | Serviço de tarefas |

#### sourcing (12 serviços)

| Serviço | Função |
|---------|--------|
| `sourcing_pipeline` | Pipeline de sourcing |
| `candidate_search_route_service` | Roteamento de busca |
| `wrf_service` | WRF (Weighted Ranking Function) |
| `pre_wrf_filter` | Filtro pré-WRF |
| `es_analyzer` | Análise Elasticsearch |
| `pgv_analyzer` | Análise PGVector |
| `evaluation_criteria` | Critérios de avaliação |
| `search_analytics` | Analytics de busca |
| `vacancy_search` | Busca de vagas para sourcing |
| `pearch_service` | Integração Pearch AI |
| `apify_service` | Integração Apify |
| `apify_mcp_client` | Cliente MCP Apify |

#### recruiter_assistant (10 serviços)

| Serviço | Função |
|---------|--------|
| `kanban_assistant_service` | Serviço de assistência Kanban |
| `talent_assistant_service` | Serviço de assistência Talent |
| `jobs_management_assistant_service` | Serviço de assistência Jobs Mgmt |
| `pipeline_service` | Serviço do pipeline de candidatos |
| `pipeline_stage_service` | Serviço de estágios do pipeline |
| `conversation_manager` | Gerenciador de conversação |
| `conversation_memory` | Memória de conversação |
| `memory_service` | Serviço de memória |
| `wizard_action_executor` | Executor de ações do wizard |
| `wizard_analytics_service` | Analytics do wizard |

#### analytics (10 serviços)

| Serviço | Função |
|---------|--------|
| `report_service` | Serviço de relatórios |
| `candidate_report_service` | Relatórios de candidatos |
| `job_report_service` | Relatórios de vagas |
| `job_insights_service` | Insights de vagas |
| `job_analytics_prompt_service` | Prompts analíticos |
| `predictive_analytics_service` | Analytics preditivo |
| `search_analytics_service` | Analytics de busca |
| `wizard_analytics_service` | Analytics do wizard |
| `agent_monitoring_service` | Monitoramento de agentes |
| `wsi_observability` | Observabilidade WSI |

#### ats_integration (8 serviços)

| Serviço | Função |
|---------|--------|
| `ats_sync_service` | Sincronização com ATS |
| `gupy_service` | Serviço Gupy |
| `pandape_service` | Serviço Pandape |
| `merge_ats_service` | Serviço Merge |
| `ats_clients/base` | Interface base de ATS |
| `ats_clients/gupy` | Cliente Gupy |
| `ats_clients/pandape` | Cliente Pandape |
| `ats_clients/merge` | Cliente Merge |

#### interview_scheduling (4 serviços)

| Serviço | Função |
|---------|--------|
| `scheduling_service` | Serviço de agendamento |
| `calendar_service` | Integração de calendário |
| `deepgram_service` | Transcrição Deepgram |
| `interview_transcript_analysis_service` | Análise de transcrições |

#### hiring_policy (lógica no agente)

O domínio `hiring_policy` não possui serviços dedicados em `services/`. Toda a lógica de políticas de contratação é implementada diretamente no `PolicyReActAgent` e suas 13 tools, que interagem com o modelo `CompanyHiringPolicy` no banco de dados. O agente gerencia configuração de políticas, benchmarks por setor (8 setores com fontes ABRH/GPTW), compliance via FairnessGuard e calibração por porte de empresa.

### 8.3 Infraestrutura Compartilhada (shared/)

Além dos serviços de domínio, a infraestrutura compartilhada provê serviços transversais:

#### Multi-Channel Communication (shared/channels/)

| Serviço | Função |
|---------|--------|
| `multi_channel_service` | Serviço unificado de comunicação multi-canal |
| `channel_router` | Roteamento inteligente por canal |
| `channel_adapter` | Interface base de adaptadores |
| `email_adapter` | Adapter de email |
| `whatsapp_adapter` | Adapter WhatsApp |
| `sms_adapter` | Adapter SMS |
| `teams_adapter` | Adapter Microsoft Teams |
| `in_app_adapter` | Adapter in-app (notificações internas) |

#### Async Task Processing (shared/async_processing/)

| Serviço | Função |
|---------|--------|
| `enhanced_task_manager` | Task manager com persistência no banco |
| `task_manager` | Task manager base |
| `task_persistence` | Persistência de tasks no DB |
| `task_scheduler` | Scheduler com cron parser |
| `task_queue` | Fila de tasks com Dead Letter Queue (DLQ) |

#### Outros Serviços Compartilhados

| Serviço | Função |
|---------|--------|
| `fairness_guard` | Guardrail de compliance (3 camadas: regex + implícito + semântico LLM) |
| `audit_service` | Logging de ações sensíveis para compliance |
| `fact_checker` | Verificação de fatos |
| `embedding_service` | Geração de embeddings vetoriais para busca semântica |
| `semantic_search_service` | Busca semântica |
| `smart_extractor` | Extração inteligente de dados |
| `llm_factory` | Factory de providers LLM (Claude, Gemini, OpenAI) |
| `working_memory` | Memória de sessão dos agentes |
| `long_term_memory` | Memória cross-sessão dos agentes |
| `memory_integration` | Ponte WorkingMemory ↔ LongTermMemory |
| `execution_log_store` | Persistência de reasoning chains (explainability) |
| `react_agent_registry` | Registry singleton de agentes ReAct |
| `circuit_breaker` | Proteção contra falhas em cascata |
| `cache_manager_service` | Gerenciador de cache |
| `learning_loop_service` | Loop de aprendizado contínuo |
| `ab_testing_service` | A/B testing |
| `feature_flag_service` | Feature flags |
| `pii_masking` | Mascaramento de PII (LGPD) |
| `structured_logging` | Logging JSON estruturado |
| `billing_service` | Gestão de assinaturas e uso |

---

## 9. Metodologia WSI

### 9.1 O que é WSI (WeDoTalent Skill Index)

O WSI é a metodologia proprietária de avaliação de candidatos da plataforma. Combina frameworks psicométricos estabelecidos em um score composto de 7 blocos.

### 9.2 Os 7 Blocos do WSI

```
┌─────────────────────────────────────────┐
│           WSI SCORE (0-100)             │
├─────────────────────────────────────────┤
│ Bloco 1: Competências Técnicas         │
│   → Hard skills, certificações, stack   │
├─────────────────────────────────────────┤
│ Bloco 2: Competências Comportamentais  │
│   → Soft skills, Big Five mapping       │
├─────────────────────────────────────────┤
│ Bloco 3: Experiência Profissional      │
│   → Histórico, senioridade, progressão  │
├─────────────────────────────────────────┤
│ Bloco 4: Fit Cultural                  │
│   → Alinhamento com valores da empresa  │
├─────────────────────────────────────────┤
│ Bloco 5: Potencial de Crescimento      │
│   → Learning agility, adaptabilidade    │
├─────────────────────────────────────────┤
│ Bloco 6: Formação Acadêmica            │
│   → Educação formal, cursos, idiomas    │
├─────────────────────────────────────────┤
│ Bloco 7: Alinhamento com a Vaga        │
│   → Match específico de requisitos      │
└─────────────────────────────────────────┘
```

### 9.3 Frameworks Psicométricos Integrados

| Framework | Uso no WSI | Implementação |
|-----------|-----------|---------------|
| **Taxonomia de Bloom** | Classificação de profundidade cognitiva das respostas | `classify_bloom` action |
| **Modelo de Dreyfus** | Classificação de nível de proficiência (Novice → Expert) | `classify_dreyfus` action |
| **Big Five (OCEAN)** | Mapeamento de traços de personalidade comportamentais | `map_big_five` action |
| **CBI (Competency-Based Interview)** | Validação de evidências comportamentais em respostas | `validate_cbi` action |

### 9.4 Arquitetura de Perguntas de Triagem (3 Camadas)

```
┌─────────────────────────────────────────┐
│     Camada 1: Derived Questions         │
│  Geradas automaticamente pelo LLM a    │
│  partir dos requisitos da vaga          │
├─────────────────────────────────────────┤
│     Camada 2: Company Bank Questions    │
│  Banco de perguntas da empresa,         │
│  reutilizáveis entre vagas              │
├─────────────────────────────────────────┤
│     Camada 3: Custom Questions          │
│  Perguntas específicas criadas pelo     │
│  recrutador para aquela vaga            │
└─────────────────────────────────────────┘
```

### 9.5 Fluxo de Avaliação WSI

1. **Parse do CV** → Extração estruturada de dados
2. **Scoring Automático** → Avaliação contra requisitos da vaga
3. **Geração de Perguntas** → Perguntas WSI personalizadas
4. **Entrevista WSI** → Perguntas + análise de respostas em tempo real
5. **Cálculo WSI** → Score final dos 7 blocos
6. **Ranking** → Ordenação dos candidatos
7. **Corte Dinâmico** → Seleção do top 25%

### 9.6 Calibração de Senioridade (Multi-Signal)

A avaliação de senioridade usa múltiplos sinais:
- Anos de experiência
- Complexidade de projetos
- Nível de responsabilidade
- Profundidade técnica (Dreyfus)
- Capacidade cognitiva (Bloom)
- Histórico de liderança

---

## 10. Sistema de Prompts

### 10.1 Arquitetura de Prompts

Os prompts são gerenciados em arquivos YAML em `app/prompts/domains/`:

```
app/prompts/
├── domains/
│   ├── cv_screening.yaml
│   ├── job_management.yaml
│   ├── sourcing.yaml
│   ├── analytics.yaml
│   ├── interview_scheduling.yaml
│   ├── communication.yaml
│   ├── ats_integration.yaml
│   ├── automation.yaml
│   └── recruiter_assistant.yaml
└── __init__.py (PromptLoader)
```

### 10.2 Persona LIA (System Prompt Principal)

> "Você é LIA, a assistente inteligente de recrutamento da WeDoTalent. Profissional de RH experiente, amigável e eficiente."

A LIA se apresenta como uma profissional de RH real, não como um chatbot. A filosofia conversacional define:
- Chat é a interface principal (painéis são suporte visual)
- LIA pergunta, recrutador responde
- Transições via confirmação textual ("sim", "pode avançar", etc.)
- Sem botões como interface principal

### 10.3 Prompts por Domínio (Resumo)

| Domínio | Foco do Prompt |
|---------|----------------|
| **CV Screening** | Especialista em avaliação WSI, Taxonomia de Bloom, Modelo Dreyfus, Big Five. Instruções para scoring objetivo e calibração científica. |
| **Job Management** | Especialista em criação de vagas, geração de JD, análise de saúde. Instruções para o wizard conversacional. |
| **Sourcing** | Expert em Pearch AI, busca semântica, queries booleanas. Instruções para otimização de buscas. |
| **Analytics** | Responsável por KPIs, análise de funil, previsão preditiva. Instruções para gerar insights acionáveis. |
| **Interview Scheduling** | Gerencia integrações Microsoft Graph e entrevistas WSI por voz. Instruções para agendamento inteligente. |
| **Communication** | Gerencia comunicação multi-canal. Instruções para personalização de mensagens e compliance LGPD. |
| **ATS Integration** | Especialista em sincronização bidirecional. Instruções para resolução de conflitos de dados. |
| **Automation** | Engine de automação. Instruções para criação de regras e alertas proativos. |
| **Recruiter Assistant** | Assistente pessoal. Instruções para briefings, insights proativos e memória persistente. |

### 10.4 Defensive Prompts

Os prompts incluem instruções defensivas para:
- **Anti-hallucination:** "Só afirme dados que você pode verificar"
- **Anti-bias:** "Nunca use critérios discriminatórios"
- **Confirmação de ações destrutivas:** "Sempre confirme ações irreversíveis"
- **Scope containment:** "Não execute ações fora do seu domínio"

### 10.5 Pipeline Transition Prompt (Inline)

O domínio Pipeline Transition usa prompt inline em vez de YAML:

> "Você é LIA, assistente de recrutamento especializada em gerenciar o pipeline de candidatos. Você pode mover candidatos entre etapas, interpretar contextos de transição, predizer sub-status e sugerir próximas ações baseadas no estado atual do pipeline. Sempre confirme ações destrutivas ou irreversíveis com o recrutador antes de executar."

---

## 11. Compliance, Governança e Mitigação de Bias

### 11.1 Arquitetura de Compliance (3 Pilares)

```
┌─────────────────────────────────────────────────────────┐
│                  CAMADA DE COMPLIANCE                   │
├──────────────┬──────────────────┬───────────────────────┤
│    LGPD      │      SOX         │     EU AI Act         │
│ (Lei Geral   │ (Sarbanes-Oxley) │ (Regulamento EU      │
│  de Proteção │                  │  de Inteligência      │
│  de Dados)   │                  │  Artificial)          │
├──────────────┴──────────────────┴───────────────────────┤
│              COMPONENTES DE ENFORCEMENT                 │
│  ┌──────────────┐ ┌─────────────┐ ┌──────────────────┐  │
│  │ FairnessGuard│ │ FactChecker │ │  AuditService    │  │
│  │ (Anti-bias)  │ │ (Veracidade)│ │ (Explainability) │  │
│  └──────────────┘ └─────────────┘ └──────────────────┘  │
│  ┌──────────────┐ ┌─────────────┐ ┌──────────────────┐  │
│  │ PolicyEngine │ │ LGPD API    │ │  Tool Registry   │  │
│  │ (Regras)     │ │ (Portal)    │ │ (RBAC de Tools)  │  │
│  └──────────────┘ └─────────────┘ └──────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 11.2 FairnessGuard (Mitigação de Bias) — Implementação Detalhada (3 Camadas)

**Arquivo:** `app/shared/compliance/fairness_guard.py`  
**Classe:** `FairnessGuard`  
**Posição no pipeline:** Middleware PRÉ-processamento — intercepta ANTES de qualquer domínio

O FairnessGuard opera em **3 camadas progressivas** de detecção de viés, cada uma com escopo e profundidade crescentes:

```
┌─────────────────────────────────────────────────────────────────────────┐
│     FAIRNESS GUARD — ARQUITETURA 3-TIER DE DETECÇÃO DE VIÉS            │
│                                                                         │
│  Query do recrutador                                                    │
│       ↓                                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ CAMADA 1: Regex Normalizado (check)                             │   │
│  │ ├─ Normalização Unicode (NFD → ASCII) via _normalize_text()    │   │
│  │ ├─ 8 categorias protegidas × N patterns compilados             │   │
│  │ ├─ Aplica em query original E normalizada (dupla verificação)  │   │
│  │ ├─ Se match → is_blocked=True, retorna educational_message     │   │
│  │ └─ Confidence: min(0.95, 0.7 + len(match) * 0.02)             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│       ↓ (sempre executa, mesmo se Camada 1 bloquear)                   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ CAMADA 2: Detecção de Viés Implícito (check_implicit_bias)      │   │
│  │ ├─ 15+ termos de viés implícito em IMPLICIT_BIAS_TERMS dict    │   │
│  │ ├─ Busca substring em texto original E normalizado             │   │
│  │ ├─ Resultado: soft_warnings (não bloqueia, mas alerta)         │   │
│  │ ├─ Exemplos: "boa aparência", "bairros nobres",                │   │
│  │ │   "universidades de primeira linha", "perfil adequado",      │   │
│  │ │   "escola particular", "morar próximo", "boa família"        │   │
│  │ └─ Cada termo tem mensagem educativa com base legal            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│       ↓ (chamada separada, async)                                      │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ CAMADA 3: Análise Semântica LLM (check_semantic)                │   │
│  │ ├─ Usa LLMService para análise contextual profunda             │   │
│  │ ├─ Prompt especializado: identifica vieses implícitos/explícitos│   │
│  │ ├─ Aceita contexto adicional (política, descrição de vaga)     │   │
│  │ ├─ Resultado: extends soft_warnings com alertas semânticos     │   │
│  │ ├─ Fallback gracioso: se LLM indisponível, retorna resultado   │   │
│  │ │   das Camadas 1+2 sem erro                                   │   │
│  │ └─ Uso: PolicyReActAgent (hiring_policy) e validações profundas│   │
│  └─────────────────────────────────────────────────────────────────┘   │
│       ↓                                                                 │
│  FairnessCheckResult {                                                  │
│    is_blocked: bool,                                                    │
│    blocked_terms: List[str],     # Termos que ativaram o bloqueio      │
│    category: str,                # Categoria discriminatória           │
│    educational_message: str,     # Mensagem educativa com base legal   │
│    original_query: str,          # Query original preservada           │
│    confidence: float,            # Confiança na detecção               │
│    soft_warnings: List[str]      # Alertas de viés implícito (Camadas 2+3) │
│  }                                                                      │
│       ↓                                                                 │
│  Se is_blocked=True → Retorna educational_message ao recrutador        │
│  Se soft_warnings → Alertas educacionais (não bloqueantes)             │
│  Se is_blocked=False e sem warnings → Query prossegue para domínio     │
└─────────────────────────────────────────────────────────────────────────┘
```

**8 Categorias Protegidas com Regex Patterns Detalhados (Camada 1):**

| Categoria | Regex Patterns (exemplos) | Mensagem Educativa | Base Legal |
|-----------|--------------------------|-------------------|------------|
| **Gênero** | `\b(apenas\|somente\|só)\s+(\w+\s+)*(homens?\|mulheres?\|masculino\|feminino)\b`, `\b(sexo\|gênero)\s*...(masculino\|feminino)\b`, `\bpreferência\s+por\s+...(homens?\|mulheres?)\b` | "A LIA não pode filtrar candidatos por gênero. A legislação trabalhista brasileira (Art. 5º, CLT) e a LGPD proíbem discriminação por gênero..." | CLT Art. 5º, LGPD |
| **Raça/Etnia** | `\b(apenas\|somente\|só)\s+...(brancos?\|negros?\|pardos?\|indígenas?\|amarelos?)\b`, `\b(raça\|cor\|etnia)\s*...\b` | "...Constituição Federal (Art. 5º) e a Lei 7.716/89 proíbem discriminação racial..." | CF Art. 5º, Lei 7.716/89 |
| **Idade** | `\b(idade\|anos?)\s*(máxim[oa]\|mínim[oa])\s*[:\s]*\d+\b`, `\bexcluir?\s+maiores?\s+de\s+\d+\b`, `\bidade\s+entre\s+\d+\s+e\s+\d+\b` | "...Estatuto do Idoso (Lei 10.741/03) e a CLT proíbem discriminação etária..." | Lei 10.741/03, CLT |
| **Religião** | `\b(apenas\|somente\|só)\s+...(cristãos?\|muçulmanos?\|judeus?\|budistas?\|ateus?)\b` | "...Constituição Federal garante liberdade religiosa (Art. 5º, VI)..." | CF Art. 5º, VI |
| **Orientação Sexual** | `\b(apenas\|somente\|só)\s+...(heterossexuais?\|homossexuais?\|gays?\|lésbicas?)\b`, `\borientação\s+sexual\b` | "...STF reconhece a criminalização da homofobia (ADO 26)..." | ADO 26 (STF) |
| **Estado Civil** | `\b(apenas\|somente\|só)\s+...(solteiros?\|casados?\|divorciados?\|viúvos?)\b`, `\bestado\s+civil\b` | "...CLT proíbe discriminação por estado civil..." | CLT |
| **Deficiência** | `\bexcluir?\s+...(deficientes?\|pcd\|cadeirantes?)\b`, `\bsem\s+defici[eê]ncia\b` | "...Lei Brasileira de Inclusão (Lei 13.146/15) garante igualdade de oportunidades..." | Lei 13.146/15, Lei 8.213/91 |
| **Nacionalidade** | `\b(apenas\|somente\|só)\s+...(brasileiros?\|estrangeiros?)\b`, `\bexcluir?\s+...(estrangeiros?\|imigrantes?)\b` | "...Constituição Federal garante igualdade entre brasileiros e estrangeiros residentes (Art. 5º)..." | CF Art. 5º |

**Suporte bilíngue:** Padrões incluem variantes em inglês (`gender`, `male`, `female`, `race`, `ethnicity`, `age`, `old`, `young`, etc.)

**15+ Termos de Viés Implícito (Camada 2):**

| Termo | Tipo de Viés | Mensagem Educativa |
|-------|-------------|-------------------|
| "boa aparência" | Discriminação estética | Lei 12.984/14 — usar critérios objetivos de apresentação profissional |
| "bairros nobres" / "região nobre" | Discriminação socioeconômica | Considerar critérios de disponibilidade ou mobilidade |
| "universidades de primeira linha" / "faculdade de ponta" | Elitismo acadêmico | Avaliar competências e resultados |
| "escola particular" | Discriminação socioeconômica | Avaliar formação e competências |
| "clube social" | Discriminação de classe | Discriminação socioeconômica ou de classe |
| "perfil adequado" | Viés inconsciente | Termo vago que pode mascarar vieses — especificar competências objetivas |
| "apresentação pessoal" | Discriminação estética | Usar critérios objetivos |
| "morar próximo" | Discriminação socioeconômica | Considerar disponibilidade ou trabalho remoto |
| "boa família" | Discriminação de origem | Usar critérios profissionais |

**Análise Semântica LLM (Camada 3) — `check_semantic()`:**

```python
async def check_semantic(self, text: str, context: str = "") -> FairnessCheckResult:
    result = self.check(text)
    semantic_prompt = (
        "Analise o seguinte texto de política de contratação e identifique "
        "possíveis vieses discriminatórios implícitos ou explícitos. "
        "Responda APENAS com uma lista de alertas, um por linha. "
        "Se não houver vieses, responda 'NENHUM_VIES_DETECTADO'.\n\n"
        f"Texto: {text}\nContexto: {context}"
    )
    response = await llm_service.generate(semantic_prompt)
    if "NENHUM_VIES_DETECTADO" not in response:
        result.soft_warnings.extend(semantic_warnings)
    return result
```

**Importante para o auditor:** O FairnessGuard opera em 3 camadas progressivas:
- **Camada 1 (Regex):** Bloqueio imediato — a query discriminatória nunca atinge o LLM nem o banco de dados
- **Camada 2 (Implícito):** Alertas educacionais — detecta linguagem que pode mascarar viés inconsciente
- **Camada 3 (LLM Semântico):** Análise profunda — identifica vieses sutis que padrões textuais não capturam

### 11.2.1 Integração do FairnessGuard nos Agentes ReAct

O FairnessGuard está integrado diretamente nos system prompts e tools dos agentes ReAct principais:

**Wizard Agent (Job Creation):**
- System prompt inclui: `"Use FairnessGuard PROATIVAMENTE: valide cada campo textual antes de salvar"`
- Tool `validate_job_requirements` invoca FairnessGuard antes de registrar requisitos
- Quando FairnessGuard bloqueia, LIA explica ao recrutador de forma educacional, sem julgamento
- Arquivo: `app/domains/job_management/agents/wizard_system_prompt.py`

**Kanban Agent (Pipeline Analysis):**
- System prompt inclui: `"SEMPRE use check_rejection_fairness ANTES de registrar qualquer rejeição"`
- Rejeições devem ser baseadas em critérios técnicos e objetivos
- Quando FairnessGuard detecta viés, agente sugere reformulação
- Arquivo: `app/domains/recruiter_assistant/agents/kanban_system_prompt.py`

**Policy Agent (Hiring Policy):**
- Usa `check_semantic()` (Camada 3) para análise profunda de políticas de contratação
- Valida políticas inteiras com análise LLM contextual
- Integrado no ciclo de revisão de políticas

### 11.2.2 Anti-Sycophancy Guardrails nos Agentes ReAct

Todos os 4 agentes principais (Wizard, Kanban, Talent, JobsMgmt) incluem guardrails anti-sycophancy integrados nos system prompts para evitar que a IA concorde passivamente com decisões inadequadas do recrutador:

```
┌─────────────────────────────────────────────────────────────────────────┐
│          ANTI-SYCOPHANCY — CONTRA-ARGUMENTAÇÃO BASEADA EM DADOS        │
│                                                                         │
│  Cenário                         │ Comportamento da LIA                │
│  ────────────────────────────────┼──────────────────────────────────── │
│  Salário muito abaixo do mercado │ Apresenta benchmark + contra-      │
│                                  │ argumenta com dados reais           │
│  Requisitos irrealistas          │ Aponta incompatibilidade (ex: 10   │
│  (ex: "10 anos para junior")     │ anos para junior) + sugere ajuste  │
│  Skills conflitantes             │ Identifica conflito (ex: Java +    │
│  (ex: "Java e .NET")             │ .NET) + sugere stack coerente      │
│  Rejeição sem critério objetivo  │ Mostra score do candidato + pede   │
│                                  │ critérios técnicos específicos     │
│  Mover candidatos sem avaliação  │ Recomenda triagem WSI antes de     │
│                                  │ avançar no pipeline                 │
│  Batch move sem critério         │ Sugere ranking antes de mover      │
│                                  │ todos indiscriminadamente           │
│                                                                         │
│  REGRA: "NUNCA concorde silenciosamente com requisitos que              │
│  prejudicam a vaga / comprometam a qualidade do processo."              │
│                                                                         │
│  Se recrutador insiste após ver dados:                                  │
│  → Executa mas documenta: "Configurado conforme solicitado.            │
│  Registro que o benchmark sugere [X]."                                  │
│                                                                         │
│  Calibração por contexto empresa:                                       │
│  STARTUP (<50): Requisitos flexíveis, equity OK, processos ágeis       │
│  PME (50-500): Equilíbrio requisitos/realidade de mercado              │
│  CORPORAÇÃO (>500): Requisitos detalhados, compliance rigoroso          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 11.2.3 LGPD nos Agentes ReAct

Os agentes ReAct possuem instruções LGPD integradas nos system prompts:

- **Wizard:** "A plataforma segue LGPD: nunca solicite dados pessoais sensíveis (raça, religião, orientação sexual, estado civil) nos requisitos da vaga"
- **Kanban:** "A plataforma segue LGPD: proteja dados pessoais dos candidatos em todas as comunicações"
- **Todos os agentes:** Rejeições e decisões são registradas via AuditService com campos de explainability (ver Seção 11.4)

### 11.3 FactChecker (Validação de Veracidade) — Implementação Detalhada

**Arquivo:** `app/shared/compliance/fact_checker.py`  
**Classe:** `FactChecker`  
**Posição no pipeline:** Middleware PÓS-processamento — valida DEPOIS da resposta do LLM

```
┌─────────────────────────────────────────────────────────────────────────┐
│          FACT CHECKER — VALIDAÇÃO PÓS-RESPOSTA                          │
│                                                                         │
│  Resposta do LLM                                                        │
│       ↓                                                                 │
│  FactChecker.check_response(response_text, context)                    │
│       ↓                                                                 │
│  4 VALIDADORES EXECUTADOS EM SEQUÊNCIA:                                │
│                                                                         │
│  1. _check_salary_claims()                                              │
│     Regex: R$\s*([\d.,]+)(?:\s*(?:a|até|-)\s*R$\s*([\d.,]+))?         │
│     Range válido: R$ 1.500 — R$ 200.000                                │
│     Validação: Compara com context["salary_min/max"] se disponível     │
│     Deviation: |claimed - actual| / actual × 100                       │
│                                                                         │
│  2. _check_candidate_counts()                                           │
│     Regex: (\d+)\s*candidatos?                                          │
│     Limite: max 50.000                                                  │
│     Validação: Compara com context["total_candidates"]                 │
│                                                                         │
│  3. _check_percentage_claims()                                          │
│     Regex: (\d+(?:[.,]\d+)?)\s*%                                       │
│     Range: 0% — 100%                                                    │
│                                                                         │
│  4. _check_date_claims()                                                │
│     Regex: (\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})                   │
│     Validação: Formato e razoabilidade                                  │
│       ↓                                                                 │
│  FactCheckResult {                                                      │
│    confidence_verified: bool,         # Se ao menos 1 claim verificado │
│    total_claims: int,                 # Total de claims detectados      │
│    verified_claims: int,              # Verificados contra dados reais │
│    accurate_claims: int,              # Verificados E corretos         │
│    inaccurate_claims: int,            # Verificados mas INCORRETOS     │
│    unverifiable_claims: int,          # Sem dados para verificar       │
│    overall_accuracy: float,           # accurate / verified            │
│    claims: List[FactCheckClaim]       # Detalhes por claim             │
│  }                                                                      │
│       ↓                                                                 │
│  FactCheckClaim por claim:                                              │
│    claim_type: str (salary, count, percentage, date)                   │
│    original_value: Any (valor afirmado pelo LLM)                       │
│    verified_value: Any (valor real do banco)                           │
│    is_accurate: bool                                                    │
│    deviation_pct: float (% de desvio do valor real)                    │
│    source: str (de onde veio o dado de verificação)                    │
│       ↓                                                                 │
│  Se inaccurate_claims > 0 → WARNING no log                            │
│  Metadata adicionada à resposta: response.metadata["fact_check"] = {  │
│    confidence_verified, total_claims, accurate_claims,                 │
│    overall_accuracy, checked_at                                         │
│  }                                                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

### 11.4 AuditService (Explainability) — Implementação Detalhada

**Arquivo:** `app/shared/compliance/audit_service.py`  
**Classe:** `AuditService`  
**Modelo:** `AuditLog` (tabela `audit_logs`)

Logging abrangente de TODAS as decisões de IA para rastreabilidade completa (LGPD Art. 20, EU AI Act Art. 14).

**Mapeamento de Ações para DecisionType:**

```python
DECISION_TYPE_MAPPING = {
    # Scoring de candidatos
    "cv_screening": DecisionType.SCORE_CANDIDATE,
    "screen_candidate": DecisionType.SCORE_CANDIDATE,
    "wsi_evaluation": DecisionType.SCORE_CANDIDATE,
    "calculate_wsi": DecisionType.SCORE_CANDIDATE,
    "quick_screening": DecisionType.SCORE_CANDIDATE,
    "complete_interview": DecisionType.SCORE_CANDIDATE,
    "screening_evaluation": DecisionType.SCORE_CANDIDATE,
    
    # Movimentação de pipeline
    "proceed_to_next_stage": DecisionType.MOVE_STAGE,
    "proceed_to_wsi": DecisionType.MOVE_STAGE,
    
    # Rejeição
    "reject": DecisionType.REJECT_CANDIDATE,
    "rejected": DecisionType.REJECT_CANDIDATE,
    
    # Comunicação, relatórios, modificações
    "send_communication": DecisionType.SEND_COMMUNICATION,
    "generate_report": DecisionType.GENERATE_REPORT,
    "modify_job": DecisionType.MODIFY_JOB,
}
```

**Campos Registrados no AuditLog:**
- `decision_type`: Tipo da decisão (enum)
- `agent_id`: Qual agente tomou a decisão
- `action_id`: Qual action foi executada
- `input_data`: Dados de entrada (contexto)
- `output_data`: Resultado da decisão
- `criteria_evaluated`: Critérios avaliados (prova de não-bias)
- `criteria_ignored`: Critérios deliberadamente ignorados
- `score_before` / `score_after`: Score antes e depois
- `justification`: Justificativa textual da decisão
- `llm_model`: Modelo LLM usado
- `prompt_hash`: Hash do prompt (para reprodutibilidade)
- `company_id`: Tenant (multi-tenant isolation)
- `user_id`: Quem iniciou a ação
- `created_at`: Timestamp

**Retenção LGPD:**
| Tipo | Período | Justificativa |
|------|---------|---------------|
| Decisões de scoring | 730 dias (2 anos) | Prazo prescricional trabalhista |
| Rejeições | 1.095 dias (3 anos) | Prazo para contestação |
| Contratações | 1.825 dias (5 anos) | Registro trabalhista |

### 11.5 Affirmative Action Service (Ações Afirmativas)

**Arquivo:** `app/services/affirmative_action_service.py`

Detecta e gerencia vagas com critérios de ação afirmativa, usando LLM para extração de critérios do texto da vaga.

```
┌─────────────────────────────────────────────────────────────────────────┐
│          AFFIRMATIVE ACTION — DETECÇÃO E GESTÃO                         │
│                                                                         │
│  5 Critérios de Ação Afirmativa:                                        │
│  ├─ Gênero (feminino, identidade de gênero)                            │
│  ├─ Raça/Etnia (pretos, pardos, indígenas)                             │
│  ├─ PcD (pessoa com deficiência — Lei 8.213/91)                        │
│  ├─ 50+ (candidatos acima de 50 anos)                                  │
│  └─ LGBTQIA+ (orientação sexual, identidade de gênero)                │
│                                                                         │
│  Fluxo:                                                                 │
│  1. LLM analisa texto da vaga/requisitos                               │
│  2. Extrai critérios afirmativos mencionados                           │
│  3. AffirmativeAuditLog registra detecção                              │
│  4. Pipeline prioriza candidatos elegíveis                             │
│  5. Compliance garantido: ação afirmativa ≠ discriminação              │
│                                                                         │
│  Distinção legal crítica:                                               │
│  - FairnessGuard BLOQUEIA discriminação negativa                       │
│  - AffirmativeAction PERMITE discriminação positiva (legal)            │
│  - Base: CF Art. 7º, XXXI + Lei 12.990/14 + Lei 8.213/91             │
└─────────────────────────────────────────────────────────────────────────┘
```

### 11.5 PolicyEngine (Regras de Negócio)

**Arquivo:** `app/orchestrator/policy_engine.py`  
**Classe:** `PolicyEngine`

Engine de regras de negócio integrada diretamente no Orchestrator. Valida requisições antes da execução.

**Políticas Padrão Implementadas:**
| Política | Valor |
|----------|-------|
| `max_pearch_searches_per_day` | 10 |
| `max_voice_screenings_per_day` | 20 |
| `max_tokens_per_request` | 50.000 |
| `max_concurrent_requests` | 5 |
| `allow_global_search` | true |
| `require_approval_for_bulk_email` | true |

**Validações por Intent:**
| Intent | Validação |
|--------|-----------|
| `candidate_search` | Limite de buscas Pearch por dia |
| `candidate_screening` | Limite de triagens por voz por dia |
| `communication` | Aprovação obrigatória para envio em massa |
| Outros | Permitido por padrão |

**Comportamento fail-safe:** Em caso de erro na validação de política, a requisição é **permitida por padrão** (fail-open), com logging do erro. Isso é uma decisão de design que prioriza disponibilidade sobre restrição.

**Nota:** Existe também `app/services/policy_engine_service.py` com regras adicionais de negócio (limites de candidatos por vaga, horários de comunicação, escalation engine). As duas implementações coexistem — o PolicyEngine do orchestrator atua como gate principal, enquanto o policy_engine_service contém regras mais granulares disponíveis para os domínios.

### 11.6 LGPD Compliance API

#### Portal do Titular (Data Subject Requests)
**Arquivo:** `app/api/v1/data_subject_requests.py`

Automação dos direitos do titular de dados (LGPD Art. 18):
- **Acesso:** Exportação completa de dados do candidato
- **Correção:** Atualização de dados pessoais
- **Exclusão:** Anonimização/deletion de dados
- **Explicação:** Justificativa de decisões automatizadas

**SLA:** 15 dias úteis para conclusão de solicitações.

#### Gerenciamento de Consentimento
**Arquivo:** `app/api/v1/consent_management.py`

- Controle de versão de consentimentos
- Prova de consentimento com hash SHA-256
- Expiração e renovação automática
- Histórico completo de consentimentos

#### Notificação de Incidentes
**Arquivo:** `app/api/v1/lgpd_compliance.py`

- Registro de DPO (Data Protection Officer)
- Notificação de incidentes em 48 horas (conforme LGPD)
- Relatório de impacto

### 11.7 Tool Registry (RBAC de Ferramentas)

**Arquivo:** `app/tools/registry.py`

Controle de acesso baseado em agentes:
- Cada ferramenta define `allowed_agents` (lista de agentes autorizados)
- Agente de sourcing não pode acessar ferramentas de billing
- Validação estrita de parâmetros antes da execução

### 11.8 Agent Monitoring (Governança de Agentes) — Implementação Detalhada

**Arquivo:** `app/shared/governance/agent_monitoring_service.py`  
**Classe:** `AgentMonitoringService`  
**Modelos:** `AgentActivity`, `AgentMetricsSnapshot` (tabelas `agent_activities`, `agent_metrics_snapshots`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│          AGENT MONITORING — 7 AGENTES MONITORADOS                       │
│                                                                         │
│  ┌──────────────────┬──────┬────────────────────────────┬────────────┐ │
│  │ Agente           │ Icon │ Função                      │ Meta/dia   │ │
│  ├──────────────────┼──────┼────────────────────────────┼────────────┤ │
│  │ job_intake        │ 📋  │ Criação de vagas, JDs       │ 15         │ │
│  │ sourcing          │ 🔍  │ Busca de candidatos         │ 50         │ │
│  │ screening         │ 🎯  │ Triagem e análise           │ 30         │ │
│  │ scheduling        │ 📅  │ Agendamento de entrevistas  │ 20         │ │
│  │ communication     │ ✉️  │ Envio de msgs               │ 40         │ │
│  │ analytics         │ 📊  │ KPIs e métricas             │ 10         │ │
│  │ recruiter_assistant│ 🤖 │ Suporte geral               │ 25         │ │
│  └──────────────────┴──────┴────────────────────────────┴────────────┘ │
│                                                                         │
│  Métricas calculadas:                                                   │
│  ├─ get_global_metrics() → Métricas de hoje vs ontem (todos agentes)  │
│  ├─ get_agent_metrics(agent_id) → Métricas por agente                 │
│  ├─ get_agent_activities() → Atividades recentes com paginação        │
│  └─ create_metrics_snapshot() → Snapshot diário para histórico        │
│                                                                         │
│  Health Score = f(4 métricas):                                         │
│  ├─ Taxa de sucesso (40%)                                              │
│  ├─ Compliance com SLA (30%)                                           │
│  ├─ Tempo médio de resposta (20%)                                      │
│  └─ Taxa de erro (10%)                                                  │
│                                                                         │
│  AgentActivity (registro por ação):                                     │
│  ├─ agent_id, action_type, status (SUCCESS/FAILED/TIMEOUT)            │
│  ├─ duration_ms, input_tokens, output_tokens                           │
│  └─ company_id, user_id, created_at                                    │
│                                                                         │
│  Daily Goal Tracking:                                                   │
│  ├─ Cada agente tem meta diária (daily_goal)                           │
│  ├─ ProactiveAlertService monitora DAILY_GOAL_RISK                     │
│  └─ Se <50% meta às 16h → alerta WARNING gerado                       │
└─────────────────────────────────────────────────────────────────────────┘
```

### 11.9 Webhook Adapters (Inbound Event Processing)

**Arquivo:** `app/domains/automation/services/webhook_adapters.py`  
**Classes:** `WebhookAdapter` (base), `InterviewWebhookAdapter`, `TestWebhookAdapter`, `DocumentWebhookAdapter`

```
┌─────────────────────────────────────────────────────────────────────────┐
│          WEBHOOK ADAPTERS — PROCESSAMENTO DE EVENTOS INBOUND            │
│                                                                         │
│  10 WebhookEventTypes:                                                  │
│  ├─ INTERVIEW_CONFIRMED    │ Entrevista confirmada pelo candidato      │
│  ├─ INTERVIEW_COMPLETED    │ Entrevista concluída                      │
│  ├─ INTERVIEW_CANCELLED    │ Entrevista cancelada                      │
│  ├─ TEST_COMPLETED         │ Teste técnico concluído                   │
│  ├─ TEST_EXPIRED           │ Teste técnico expirado                    │
│  ├─ DOCUMENT_SUBMITTED     │ Documento enviado pelo candidato          │
│  ├─ REFERENCE_COMPLETED    │ Referência profissional completada        │
│  ├─ OFFER_ACCEPTED         │ Oferta aceita                             │
│  ├─ OFFER_DECLINED         │ Oferta recusada                           │
│  └─ CANDIDATE_RESPONSE     │ Resposta genérica do candidato            │
│                                                                         │
│  Idempotency (deduplicação):                                            │
│  ├─ _processed_events: Set[str] → Rastreia event_ids processados      │
│  ├─ is_duplicate(event_id) → Verifica se já foi processado            │
│  └─ mark_processed(event_id) → Registra com metadata                  │
│                                                                         │
│  Event Log:                                                             │
│  ├─ Cada evento processado gera entrada no _event_log                  │
│  ├─ Campos: event_id, event_type, provider, processed_at, result      │
│  └─ Usado para auditoria e debugging                                   │
│                                                                         │
│  Feature Flags:                                                         │
│  ├─ ENABLE_WEBHOOK_INTERVIEW → Habilita webhooks de entrevista        │
│  ├─ ENABLE_WEBHOOK_TEST → Habilita webhooks de teste                  │
│  └─ ENABLE_WEBHOOK_DOCUMENT → Habilita webhooks de documento          │
│  (Todos default=True)                                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 11.11 Feature Flags

**Arquivo:** `app/shared/governance/feature_flag_service.py`

Controle granular de funcionalidades:
- Rollout por porcentagem
- Ativação/desativação por empresa
- Datas de expiração
- Flags específicas: `ENABLE_LLM_SUBSTATUS_PREDICTION`, `ENABLE_WEBHOOK_*`, `learning_hub_enabled`, `ai_suggestions_enhanced`

---

## 12. Integrações Externas

### 12.1 Provedores de IA

| Provedor | Uso | Modelos |
|----------|-----|---------|
| **Anthropic (Claude)** | LLM principal para orquestração, prompts, análise | Claude Sonnet |
| **OpenAI** | LLM complementar, embeddings | GPT-4, text-embedding-ada-002 |
| **Google Gemini** | Análise multimodal (vídeo, imagem, documento) | Gemini Pro |

### 12.2 Integrações de Comunicação

| Serviço | Função |
|---------|--------|
| **Mailgun** | Envio de emails transacionais |
| **Twilio/Meta** | WhatsApp messaging |
| **Microsoft Graph** | Teams, calendários Outlook |
| **Deepgram** | Transcrição de áudio (Nova-2) |

### 12.3 Integrações de Sourcing

| Serviço | Função |
|---------|--------|
| **Pearch AI** | Busca de candidatos externos |
| **OpenMic.ai** | Análise de áudio/voz |

### 12.4 Integrações de ATS

| Serviço | Função |
|---------|--------|
| **Merge.dev** | Unificador de ATS (multi-provider) |
| **Gupy** | ATS brasileiro (integração direta) |
| **Pandapé** | ATS brasileiro (integração direta) |

### 12.5 Integrações de Negócio

| Serviço | Função |
|---------|--------|
| **WorkOS** | Autenticação e SSO |
| **Stripe** | Pagamentos e assinaturas |
| **HubSpot** | CRM e marketing |

---

## 13. Data Architecture (Arquitetura de Dados)

### 13.1 Visão Geral do Schema

**ORM:** SQLAlchemy 2.0 (async) com asyncpg  
**Banco:** PostgreSQL (Neon-backed via Replit)  
**Extensões:** pgvector (busca semântica)  
**Migrações:** Alembic (quando configurado) / auto-create em dev

**Configuração do Pool de Conexões:**
```
Engine Config:
├─ pool_size: settings.DATABASE_POOL_SIZE
├─ max_overflow: settings.DATABASE_MAX_OVERFLOW
├─ pool_pre_ping: True (testa conexões antes de usar)
├─ pool_recycle: 3600s (recicla conexões a cada 1h)
└─ echo: settings.DEBUG (log SQL em debug)
```

### 13.2 Catálogo de Entidades (86 modelos em 45 arquivos)

**Domínio: Candidatos & Recrutamento**

| Modelo | Tabela | Campos-chave | PII |
|--------|--------|-------------|-----|
| `Candidate` | `candidates` | nome, email, telefone, CV, skills, experience | SIM |
| `CandidateAttachment` | `candidate_attachments` | file_url, file_type, original_name | SIM |
| `CandidateList` | `candidate_lists` | name, filters, member_count | NÃO |
| `CandidateFeedback` | `candidate_feedbacks` | feedback_type, rating, notes | PARCIAL |
| `CandidateStageHistory` | `candidate_stage_histories` | stage_from, stage_to, moved_at | NÃO |

**Domínio: Vagas & Templates**

| Modelo | Tabela | Campos-chave |
|--------|--------|-------------|
| `JobVacancy` | `job_vacancies` | title, description, requirements, salary_min/max, status |
| `JobTemplate` | `job_templates` | category, template_data, usage_count |
| `JobPattern` | `job_patterns` | embedding (Vector 768), cluster_id, pattern_data |
| `JobEmbedding` | `job_embeddings` | embedding (Vector 768), content_hash |
| `JobDraft` | `job_drafts` | draft_data, wizard_step, session_id |
| `ImportedJobDescription` | `imported_job_descriptions` | raw_text, extracted_data, source |
| `ScreeningQuestion` | `screening_questions` | question_text, question_type, weight |

**Domínio: Avaliação & WSI**

| Modelo | Tabela | Campos-chave |
|--------|--------|-------------|
| `EvaluationCriteria` | `evaluation_criteria` | category (ENUM), weight, description |
| `CalibrationSession` | `calibration_sessions` | status, feedback_count, weights |
| `VoiceScreeningCall` | `voice_screening_calls` | audio_url, transcript, wsi_score |
| `Rubric` | `rubrics` | criteria, scoring_guide, seniority_level |

**Domínio: Comunicação**

| Modelo | Tabela | Campos-chave | PII |
|--------|--------|-------------|-----|
| `CommunicationHistory` | `communication_history` | channel, recipient, content, status | SIM |
| `WhatsAppConversation` | `whatsapp_conversations` | phone_number, messages | SIM |
| `EmailTemplate` | `email_templates` | subject, body_html, variables | NÃO |
| `CommunicationSettings` | `communication_settings` | channels_config, working_hours | NÃO |

**Domínio: Entrevistas & Agendamento**

| Modelo | Tabela | Campos-chave |
|--------|--------|-------------|
| `Interview` | `interviews` | scheduled_at, type, status, notes |
| `InterviewFeedback` | `interview_feedbacks` | rating, strengths, weaknesses |
| `CalendarAvailability` | `calendar_availabilities` | available_slots, timezone |
| `SelfScheduling` | `self_scheduling` | booking_link, time_slots |

**Domínio: IA & Aprendizado**

| Modelo | Tabela | Campos-chave |
|--------|--------|-------------|
| `ConversationMemory` | `conversation_memories` | embedding (Vector 768), content, session_id |
| `KnowledgeBase` | `knowledge_base` | embedding (Vector 768), document_type, chunks |
| `GraphSession` | `graph_sessions` | graph_type, state_data, current_node |
| `LiaOpinion` | `lia_opinions` | opinion_type, recommendation, confidence |
| `InteractionFeedback` | `interaction_feedbacks` | feedback_type, rating, context |
| `LearningPattern` | `learning_patterns` | pattern_type, pattern_data, usage_count |
| `FeedbackEvent` | `feedback_events` | event_type, context, response |

**Domínio: Compliance & Observabilidade**

| Modelo | Tabela | Campos-chave | LGPD |
|--------|--------|-------------|------|
| `AIInferenceLog` | `ai_inference_logs` | agent_type, input_hash, confidence, human_override | Explainability |
| `DataAccessLog` | `data_access_logs` | user_id, data_type, operation, pii_fields | Art. 37 |
| `ConsentRecord` | `consent_records` | consent_type, granted_at, revoked_at, legal_basis | Art. 8 |
| `IncidentReport` | `incident_reports` | type, severity, root_cause, remediation | SOC2 |
| `ModelEvaluation` | `model_evaluations` | evaluation_type, dimension, metric_value, passed | EU AI Act |
| `ComplianceControl` | `compliance_controls` | framework, control_id, status, evidence | ISO27001 |
| `BiasAuditReport` | `bias_audit_reports` | 11 categorias Tezi AI, overall_score | NYC LL144 |
| `AuditLog` | `audit_logs` | decision_type, criteria, justification | Art. 20 |

**Domínio: Empresa & Multi-tenancy**

| Modelo | Tabela | Campos-chave |
|--------|--------|-------------|
| `Company` | `companies` | name, config, branding |
| `ClientAccount` | `client_accounts` | subscription, plan, limits |
| `User` | `users` | email, role (admin/recruiter/viewer), company_id, workos_id |
| `CompanyCulture` | `company_cultures` | values, principles, assessment_data |
| `CompanyBenefit` | `company_benefits` | benefit_type, description, value |
| `CompanyLearning` | `company_learnings` | learning_type, data, source |

### 13.3 Vector Database (pgvector)

```
┌──────────────────────────────────────────────────────────────────┐
│                 PGVECTOR — BUSCA SEMÂNTICA                       │
│                                                                  │
│  Tabelas com Vector(768):                                        │
│  ├─ conversation_memories → Memória conversacional              │
│  ├─ knowledge_base → Base de conhecimento RAG                   │
│  ├─ job_embeddings → Embeddings de vagas (clusterização)        │
│  ├─ job_patterns → Padrões de vagas (similaridade)              │
│  ├─ query_embeddings → Cache semântico de queries               │
│  └─ intelligent_cache → Cache com similaridade vetorial         │
│                                                                  │
│  Modelo de embedding: text-embedding-004 (768 dimensões)        │
│  Indexação: IVFFlat (quando >10k registros) ou HNSW             │
│  Operador de similaridade: <=> (cosine distance)                │
│  Threshold de similaridade: 0.85 (cache), 0.7 (busca)          │
└──────────────────────────────────────────────────────────────────┘
```

### 13.4 Mapeamento de PII (Dados Pessoais)

| Localização | Tipo de PII | Base Legal LGPD | Retenção |
|-------------|------------|-----------------|----------|
| `candidates.name/email/phone` | Dados cadastrais | Consentimento (Art. 8) | Até revogação |
| `candidate_attachments` (CVs) | Dados profissionais | Legítimo interesse (Art. 10) | 2 anos |
| `communication_history.content` | Conteúdo de mensagens | Execução contratual (Art. 7, V) | 1 ano |
| `voice_screening_calls.audio_url` | Áudio de voz | Consentimento explícito | 90 dias |
| `ai_inference_logs.input_preview` | Preview de dados processados | Obrigação legal (Art. 7, II) | 2 anos |
| `whatsapp_conversations.messages` | Mensagens privadas | Consentimento (Art. 8) | 6 meses |

### 13.5 Data Flow: Ingestão → Processamento → Armazenamento

```
┌──────────────────────────────────────────────────────────────────┐
│                    DATA FLOW PRINCIPAL                            │
│                                                                  │
│  INGESTÃO:                                                       │
│  ├─ API REST (FastAPI) → Validação Pydantic → PostgreSQL        │
│  ├─ Webhook (ATS/WhatsApp/Teams) → Queue → Processamento       │
│  ├─ Upload CV (PDF/DOCX) → Parser → Extração → Candidato       │
│  └─ Importação JD → Extração LLM → JobVacancy                  │
│                                                                  │
│  PROCESSAMENTO:                                                  │
│  ├─ LLM Processing → Structured Output → Validação Pydantic    │
│  ├─ Embedding Generation → pgvector → Indexação                │
│  ├─ WSI Scoring → 7 blocos → Score normalizado                 │
│  └─ Background Jobs → TaskManager nativo → Async processing     │
│                                                                  │
│  ARMAZENAMENTO:                                                  │
│  ├─ PostgreSQL → Dados transacionais (ACID)                     │
│  ├─ pgvector → Embeddings e busca semântica                     │
│  ├─ Redis → Cache de 3 camadas (TTL: 5min/1h/24h)             │
│  └─ S3/Object Storage → Arquivos (CVs, áudios, documentos)     │
│                                                                  │
│  RETRIEVAL:                                                      │
│  ├─ SQL direto → Queries transacionais                          │
│  ├─ Busca semântica → pgvector cosine similarity               │
│  ├─ WRF (Weighted Reciprocal Fusion) → Multi-signal search     │
│  └─ Cache hit → Redis → Resposta imediata                      │
└──────────────────────────────────────────────────────────────────┘
```

---

## 14. AI vs Non-AI Boundaries (Fronteiras IA vs Determinístico)

### 14.1 Mapa de Decisões: O que é IA vs Determinístico

```
┌──────────────────────────────────────────────────────────────────┐
│              IA vs DETERMINÍSTICO — MAPA COMPLETO                │
│                                                                  │
│  DECISÕES 100% IA (LLM):                                        │
│  ├─ Intent classification (o que o recrutador quer)             │
│  ├─ Geração de Job Description                                  │
│  ├─ Análise de CV e extração de dados                          │
│  ├─ WSI scoring qualitativo (blocos comportamentais)           │
│  ├─ Geração de perguntas de triagem                            │
│  ├─ Sugestões de competências e skills                         │
│  ├─ Análise de fit cultural                                     │
│  ├─ Geração de comunicações personalizadas                     │
│  ├─ Análise multimodal (vídeo, imagem, voz)                    │
│  └─ Predição de sub-status de pipeline                         │
│                                                                  │
│  DECISÕES HÍBRIDAS (IA + Regras):                                │
│  ├─ Roteamento de domínio: Memory → Regex → LLM (cascata)     │
│  ├─ WSI scoring quantitativo: LLM extrai + Algoritmo pontua   │
│  ├─ Busca de candidatos: WRF (pesos determinísticos) + embed  │
│  ├─ Personalização: Estatísticas históricas + LLM ajusta      │
│  ├─ Automação de pipeline: Triggers determinísticos + LLM pred│
│  └─ Cache semântico: Cosine similarity (math) + LLM (fallback)│
│                                                                  │
│  DECISÕES 100% DETERMINÍSTICAS:                                  │
│  ├─ Autenticação e autorização (JWT + RBAC)                    │
│  ├─ FairnessGuard (regex pattern matching)                     │
│  ├─ FactChecker (validação numérica com ranges fixos)          │
│  ├─ Rate limiting e PolicyEngine (contadores + limites)        │
│  ├─ Retenção LGPD (dias fixos por tipo)                        │
│  ├─ Pipeline state machine (transições válidas hardcoded)      │
│  ├─ Multi-tenancy isolation (company_id filter)                │
│  ├─ Token tracking e billing (contagem exata)                  │
│  └─ Feature flags (boolean per tenant)                          │
└──────────────────────────────────────────────────────────────────┘
```

### 14.2 Human-in-the-Loop Checkpoints

| Ação | `requires_confirmation` | Impacto | Quem aprova |
|------|------------------------|---------|-------------|
| Envio de email em massa | SIM | Comunicação irreversível | Recrutador |
| Rejeição de candidato | SIM | Decisão final negativa | Recrutador |
| Publicação de vaga | SIM | Exposição pública | Recrutador |
| Movimentação de pipeline | SIM | Mudança de etapa | Recrutador |
| Agendamento de entrevista | SIM | Compromisso com candidato | Recrutador |
| Envio via WhatsApp | SIM | Comunicação direta | Recrutador |
| Geração de JD | NÃO | Preview antes de publicar | — |
| Scoring WSI | NÃO | Informativo, não ação | — |
| Sugestões de skills | NÃO | Sugestão editável | — |
| Busca de candidatos | NÃO | Apenas listagem | — |

**Princípio:** Toda ação que causa efeito externo (envia, publica, rejeita, agenda) requer confirmação. Ações informativas (score, busca, sugestão) são automáticas.

---

## 15. Performance & Scalability

### 15.1 Configuração de Performance Atual

```
┌──────────────────────────────────────────────────────────────────┐
│                    PERFORMANCE — CONFIGURAÇÃO                     │
│                                                                  │
│  Database Pool:                                                  │
│  ├─ pool_size: configurável (settings.DATABASE_POOL_SIZE)       │
│  ├─ max_overflow: configurável (settings.DATABASE_MAX_OVERFLOW) │
│  ├─ pool_pre_ping: True (testa conexões antes de usar)          │
│  └─ pool_recycle: 3600s (previne idle timeout)                  │
│                                                                  │
│  Rate Limiting (PolicyEngine):                                   │
│  ├─ max_pearch_searches_per_day: 10                             │
│  ├─ max_voice_screenings_per_day: 20                            │
│  ├─ max_tokens_per_request: 50.000                              │
│  ├─ max_concurrent_requests: 5                                   │
│  └─ RateLimitRule (DB): per-tenant, configurable                │
│                                                                  │
│  LLM Timeouts:                                                   │
│  ├─ Claude: timeout=120s                                        │
│  ├─ OpenAI: timeout=120s                                        │
│  └─ Gemini: timeout default                                     │
│                                                                  │
│  Cache TTLs (Redis 3 camadas):                                   │
│  ├─ Camada 1 (hot): 5 minutos                                  │
│  ├─ Camada 2 (warm): 1 hora                                    │
│  └─ Camada 3 (cold): 24 horas                                  │
│                                                                  │
│  Background Processing (TaskManager nativo):                     │
│  ├─ TaskScheduler: agendamento e execução de tasks              │
│  ├─ EnhancedTaskManager: retry, DLQ, monitoring                 │
│  ├─ TaskRecord: persistência e tracking de tasks                │
│  ├─ Dead Letter Queue (DLQ): tasks falhadas para reprocessamento│
│  └─ MAX_TOOL_CALLS_PER_REQUEST: 3 (previne loops)              │
└──────────────────────────────────────────────────────────────────┘
```

### 15.2 Bottlenecks Identificados

| Bottleneck | Severidade | Descrição | Mitigação Atual |
|-----------|-----------|-----------|-----------------|
| Latência LLM | ALTA | Chamadas Claude/GPT levam 2-10s cada | Cache semântico, cascaded router |
| Concurrent DB | MÉDIA | Pool pode saturar com muitos agents | pool_pre_ping, pool_recycle |
| Embedding generation | MÉDIA | Gerar embeddings para cada CV/vaga | Batch processing, cache |
| External API limits | MÉDIA | Pearch, Deepgram, Mailgun têm limits | Rate limiting, PolicyEngine |
| Token consumption | ALTA | Custo cresce com volume | Token tracking, billing alerts |

### 15.3 Horizontal Scalability

| Componente | Stateless? | Escalável? | Notas |
|-----------|-----------|-----------|-------|
| FastAPI/Uvicorn | SIM | SIM | Múltiplos workers via --workers |
| TaskManager (async tasks) | SIM | SIM | EnhancedTaskManager com DLQ e retry |
| Redis | N/A | SIM (managed) | Replit managed / external Redis |
| PostgreSQL | N/A | SIM (managed) | Neon auto-scaling |
| LLM calls | SIM | SIM | Sem estado, escalável por natureza |

---

## 16. Reliability & Observability

### 16.1 Logging Strategy

**Framework:** Python `logging` (stdlib) com structured JSON output  
**Formato:** Structured JSON (implementado) — logs estruturados com campos padronizados (timestamp, level, module, request_id, company_id, user_id)  
**Níveis usados:** DEBUG, INFO, WARNING, ERROR

```
Padrão de logging no código:
├─ logger = logging.getLogger(__name__)
├─ Structured JSON output com campos padronizados
├─ request_id injetado automaticamente via RequestIdMiddleware
├─ logger.info(f"User registered: {user.email}")
├─ logger.warning(f"SECURITY: Request without X-Company-ID")
├─ logger.error(f"Failed to process: {str(e)}")
└─ Prefix "SECURITY:" para eventos de segurança
```

### 16.1.1 Production Readiness — Middleware & Rate Limiting

```
┌──────────────────────────────────────────────────────────────┐
│              PRODUCTION READINESS — MIDDLEWARE                 │
│                                                              │
│  RequestIdMiddleware:                                         │
│  ├─ Gera UUID único por request (X-Request-ID header)        │
│  ├─ Propaga request_id em todos os logs                      │
│  ├─ Permite rastreamento end-to-end de requests              │
│  └─ Inclui request_id em respostas HTTP                      │
│                                                              │
│  Rate Limiter Middleware:                                     │
│  ├─ Limite por minuto: 200 requests/min por tenant           │
│  ├─ Limite por hora: 2000 requests/hr por tenant             │
│  ├─ Resposta: HTTP 429 Too Many Requests                     │
│  ├─ Headers: X-RateLimit-Limit, X-RateLimit-Remaining        │
│  └─ Implementação: in-memory + Redis para clusters           │
│                                                              │
│  Health Endpoint Unificado:                                   │
│  ├─ GET /health — status de todos os componentes             │
│  ├─ Verifica: DB, Redis, LLM providers, external APIs        │
│  ├─ Resposta: { status, components: { db, redis, ... } }    │
│  └─ Usado por load balancers e monitoring                    │
└──────────────────────────────────────────────────────────────┘
```

### 16.2 Observability Models (2.165 linhas)

**Arquivo:** `app/models/observability.py` — 15 modelos dedicados a observabilidade

| Modelo | Função | Framework |
|--------|--------|-----------|
| `AIInferenceLog` | Log de toda inferência IA com explainability | EU AI Act |
| `DataAccessLog` | Log de acesso a dados pessoais com PII fields | LGPD Art. 37 |
| `ConsentRecord` | Registro de consentimento com legal_basis | LGPD Art. 8 |
| `IncidentReport` | Incidentes de segurança/compliance | SOC2, ISO27001 |
| `ModelEvaluation` | Avaliação de bias/fairness (11 dimensões Tezi AI) | NYC LL144 |
| `ComplianceControl` | Controles de compliance por framework | ISO27001, SOC2 |
| `BiasAuditReport` | Relatórios de auditoria de bias | EU AI Act |
| `ConsentVersion` | Versionamento de termos de consentimento | LGPD |
| `ConsentEvent` | Eventos de consentimento (grant/revoke/renew) | LGPD |
| `DataSubjectRequest` | Requisições de titulares (Art. 18) | LGPD |
| `BreachNotification` | Notificação de vazamento de dados | LGPD Art. 48 |
| `DataProcessingRecord` | Registro de tratamento de dados | LGPD Art. 37 |
| `ComplianceHealthCheckItem` | Health checks por framework compliance | Multi-framework |

### 16.3 Health Checks

**Arquivo:** `app/models/health_check.py`  
**Frameworks monitorados:** SOX, SOC2, ISO27001, LGPD, BCB498, EUAI, NYC144

```
ComplianceHealthCheckItem:
├─ framework: ComplianceFrameworkType (7 frameworks)
├─ status: IMPLEMENTED | PARTIAL | PENDING | NOT_APPLICABLE | NOT_CHECKED
├─ review_frequency: WEEKLY | MONTHLY | QUARTERLY | ANNUAL
├─ priority: CRITICAL | HIGH | MEDIUM | LOW
├─ evidence: URL + notes
├─ reviewer: assigned person
└─ next_review_at: scheduling automático
```

### 16.4 Error Handling & Taxonomy

| Nível | Tratamento | Exemplo |
|-------|-----------|---------|
| **Agent level** | EnhancedBaseAgent com try/catch, fallback, retry | Falha de LLM → resposta de fallback |
| **Domain level** | Cada action retorna ActionResult com success/error | Erro em busca → mensagem educativa |
| **Orchestrator** | Cascaded Router fallback (cache → regex → LLM) | Falha LLM → regex matching |
| **API level** | HTTPException com status codes apropriados | 401, 403, 404, 422, 500 |
| **Compliance** | IncidentReport com severidade e remediation | Bias detectado → alerta |

---

## 17. Security & Authentication — Implementação Detalhada

### 17.1 Authentication Model

```
┌──────────────────────────────────────────────────────────────────┐
│                  AUTENTICAÇÃO — 2 CAMADAS                         │
│                                                                  │
│  CAMADA 1: JWT Nativo                                            │
│  ├─ Biblioteca: python-jose (JWT)                               │
│  ├─ Hash de senhas: bcrypt                                      │
│  ├─ Access token: 30 minutos                                    │
│  ├─ Refresh token: 7 dias                                       │
│  ├─ Password reset: 24 horas                                    │
│  ├─ Email verification: 7 dias                                  │
│  └─ Invitation: 24 horas                                        │
│                                                                  │
│  CAMADA 2: WorkOS (Enterprise SSO)                               │
│  ├─ SSO via SAML/OIDC                                           │
│  ├─ SCIM provisioning (auto user sync)                          │
│  ├─ Directory sync (AD/Okta/Google)                             │
│  ├─ workos_id: Identificador WorkOS no User model               │
│  ├─ workos_organization_id: Tenant WorkOS                       │
│  └─ is_scim_managed: Flag de gestão externa                     │
└──────────────────────────────────────────────────────────────────┘
```

### 17.2 Authorization (RBAC)

**Arquivo:** `app/auth/models.py`, `app/auth/dependencies.py`

| Role | Permissões | Implementação |
|------|-----------|---------------|
| `admin` | Acesso total, cross-company | `require_admin` dependency |
| `recruiter` | CRUD vagas, candidatos, comunicação (own company) | `require_admin_or_recruiter` |
| `viewer` | Somente leitura (own company) | Default role |

**Multi-tenancy enforcement:**
- `user.can_access_company(company_id)` — admin acessa tudo, outros só own company
- `X-Company-ID` header obrigatório em todas as APIs
- Validação UUID no header (rejeita formatos inválidos)

### 17.3 Consent Management (LGPD)

**Arquivo:** `app/api/v1/consent_management.py`

```
Consent Management:
├─ ConsentVersion: Versionamento de termos (content_hash SHA256)
├─ ConsentEvent: Grant, Revoke, Renew, Expire
├─ Proof hash: SHA256(version_id|email|identifier|event|consent|timestamp)
├─ Subject history: Timeline completa por candidato
└─ Statistics: Agregação por tipo de consentimento
```

**6 Tipos de consentimento:**
1. `DATA_PROCESSING` — Processamento de dados pessoais
2. `AI_SCORING` — Scoring por IA
3. `MARKETING` — Comunicação de marketing
4. `DATA_SHARING` — Compartilhamento com terceiros
5. `AUTOMATED_DECISION` — Decisão automatizada
6. `PROFILE_ENRICHMENT` — Enriquecimento de perfil

### 17.4 Data Subject Rights (LGPD Art. 18)

**Arquivo:** `app/api/v1/data_subject_requests.py`

7 direitos implementados:
1. **Acesso** — Acesso aos dados pessoais
2. **Correção** — Correção de dados inexatos
3. **Exclusão/Anonimização** — Eliminação de dados
4. **Portabilidade** — Exportação de dados
5. **Oposição** — Objeção ao processamento
6. **Restrição** — Restrição de processamento
7. **Explicação** — Explicação de decisões automatizadas

**SLA legal:** 15 dias úteis (calculado com `calculate_sla_deadline()` — exclui finais de semana)  
**Audit trail:** Cada ação no request gera entrada no audit_trail JSON

---

## 18. Tópicos Avançados de Governança de IA

### 18.1 Vendor Lock-in & Portabilidade LLM

| Aspecto | Status | Detalhes |
|---------|--------|---------|
| Camada de abstração | **PRESENTE** | `LLMService` com providers: claude, openai, gemini |
| Fallback automático | **PRESENTE** | Se Claude indisponível → Gemini como fallback |
| Prompts acoplados? | **RISCO** | System prompts otimizados para Claude (pode precisar ajuste para outros) |
| Structured output | **PORTÁVEL** | `StructuredOutputService` converte Pydantic → schema por provider |
| Tool calling | **PARCIAL** | Implementado para Claude e Gemini, formato difere por provider |
| Custo de migração | **MÉDIO** | Abstração existe, mas prompts precisam revalidação |

**LLM Config Atual:**

| Provider | Modelo | Temperature | Max Tokens | Timeout |
|----------|--------|------------|-----------|---------|
| Claude | claude-sonnet-4-6 | 0.7 | 4.096 | 120s |
| OpenAI | gpt-4o | 0.7 | 4.096 | 120s |
| Gemini | gemini-2.5-flash | default | 4.096 | default |

### 18.2 Incident Response para Decisões de IA

**Modelo:** `IncidentReport` (tabela `incident_reports`)

```
┌──────────────────────────────────────────────────────────────────┐
│           INCIDENT RESPONSE — FLUXO                              │
│                                                                  │
│  7 Tipos de Incidente:                                           │
│  ├─ DATA_BREACH: Vazamento de dados                             │
│  ├─ UNAUTHORIZED_ACCESS: Acesso não autorizado                  │
│  ├─ SYSTEM_FAILURE: Falha de sistema                            │
│  ├─ BIAS_DETECTED: Bias detectado em decisão IA                │
│  ├─ SLA_VIOLATION: Violação de SLA                              │
│  ├─ POLICY_VIOLATION: Violação de política                      │
│  └─ PRIVACY_VIOLATION: Violação de privacidade                  │
│                                                                  │
│  4 Severidades: LOW, MEDIUM, HIGH, CRITICAL                     │
│                                                                  │
│  Campos de resposta:                                             │
│  ├─ root_cause: Análise de causa raiz                           │
│  ├─ remediation_actions: Array de ações corretivas              │
│  ├─ notified_parties: Quem foi notificado                       │
│  ├─ status: open → investigating → resolved                    │
│  └─ assigned_to: Responsável pela resolução                     │
│                                                                  │
│  Human Override (AIInferenceLog):                                │
│  ├─ human_override: bool (recrutador sobrescreveu IA?)         │
│  ├─ override_reason: Justificativa textual                      │
│  └─ override_by: UUID do recrutador                             │
└──────────────────────────────────────────────────────────────────┘
```

### 18.3 Evaluation Framework (Qualidade da IA)

**Modelo:** `ModelEvaluation` (tabela `model_evaluations`)

```
┌──────────────────────────────────────────────────────────────────┐
│           EVALUATION FRAMEWORK                                    │
│                                                                  │
│  5 Tipos de Avaliação:                                           │
│  ├─ BIAS_CHECK: Verificação de bias por dimensão                │
│  ├─ FAIRNESS_AUDIT: Auditoria de fairness                       │
│  ├─ ACCURACY_TEST: Teste de acurácia                            │
│  ├─ CALIBRATION_CHECK: Verificação de calibração                │
│  └─ DRIFT_DETECTION: Detecção de drift                          │
│                                                                  │
│  11 Dimensões de Bias (Tezi AI):                                 │
│  ├─ sex_bias, race_ethnicity_bias, age_bias                    │
│  ├─ disability_bias, religion_bias                              │
│  ├─ sexual_orientation_bias, veteran_status_bias                │
│  ├─ language_proficiency_bias, pregnancy_status_bias            │
│  └─ national_origin_bias, intersectional_bias                   │
│                                                                  │
│  Métricas registradas:                                           │
│  ├─ metric_name + metric_value + threshold                     │
│  ├─ passed: bool (valor passou no threshold?)                   │
│  ├─ sample_size + confidence_interval                           │
│  └─ recommendations: Array de recomendações                     │
│                                                                  │
│  Compliance frameworks suportados:                               │
│  NYC_LL144, CO_SB205, EU_AI_ACT, CA_FEHA, LGPD_BRAZIL         │
│                                                                  │
│  BiasAuditReport:                                                │
│  ├─ Auditorias: MONTHLY, QUARTERLY, ANNUAL, ON_DEMAND          │
│  ├─ Auditores: INTERNAL, EXTERNAL, THIRD_PARTY                 │
│  ├─ Status por dimensão: CLEAR, CONSIDER, CONCERN              │
│  └─ overall_score: 0-100 (agregação de todas dimensões)        │
└──────────────────────────────────────────────────────────────────┘
```

### 18.4 Superfície de Ataque Adversarial

| Vetor de Ataque | Risco | Mitigação Atual | Status | Arquivos para Verificação |
|----------------|-------|-----------------|--------|--------------------------|
| **Prompt injection via chat** | ALTO | FairnessGuard (3 camadas: regex + implícito + LLM semântico) + `PromptInjectionGuard` (6 categorias de injection PT/EN com sanitização) | **PRESENTE** | `app/shared/compliance/fairness_guard.py` — classe `FairnessGuard`, métodos `check()`, `check_implicit_bias()`, `check_semantic()`; `app/shared/prompt_injection.py` — classe `PromptInjectionGuard`, 6 categorias de detecção |
| **CV crafting para enganar WSI** | MÉDIO | WSI multi-bloco (7 sinais), calibração cruzada entre blocos, scoring determinístico | **PRESENTE** | `app/services/wsi_service.py` — classe `WSIService`, 7 blocos de avaliação; `app/domains/cv_screening/services/cv_scoring_service.py` — classe `CVScoringService`, scoring e calibração; `app/domains/cv_screening/agents/avaliador_wsi_agent.py` — agente de avaliação WSI |
| **Jailbreak da LIA** | MÉDIO | System prompts com guardrails anti-sycophancy + CONTRA-ARGUMENTAÇÃO, tool calling restrito via `max_iterations` no ReActLoop, anti-sycophancy em todos os 4 agentes principais | **PRESENTE** | `app/shared/agents/react_loop.py` — `ReActConfig.max_iterations` (limite de tool calls por request); `app/domains/job_management/agents/wizard_system_prompt.py` — seções CONTRA-ARGUMENTAÇÃO e guardrails; `app/domains/recruiter_assistant/agents/kanban_system_prompt.py` — idem; `app/domains/recruiter_assistant/agents/talent_system_prompt.py` — idem; `app/domains/recruiter_assistant/agents/jobs_mgmt_system_prompt.py` — idem |
| **Data poisoning via feedback** | BAIXO | Learning extractor com validação de padrões, promoção controlada | **PRESENTE** | `app/shared/agents/learning_extractor.py` — classe `LearningExtractor`, extração e validação de padrões; `app/shared/agents/long_term_memory.py` — classe `LongTermMemoryService`, persistência com `memory_type` e `confidence` |
| **Tenant data leakage** | ALTO | `company_id` filter em todas as queries, RBAC por role (admin/recruiter/viewer), isolamento por tenant no Orchestrator | **PRESENTE** | `app/auth/dependencies.py` — `get_current_user_or_demo()`, extração de `company_id` do JWT; `app/auth/models.py` — modelo `User` com `company_id`; `app/orchestrator/orchestrator.py` — `context.tenant_id` propagado para todos os domínios; `app/orchestrator/policy_engine.py` — `PolicyEngine`, validação de limites por tenant |
| **API abuse** | MÉDIO | Rate limiting middleware (200/min, 2000/hr por tenant), PolicyEngine com limites por recurso, JWT auth obrigatório em endpoints operacionais | **PRESENTE** | `app/orchestrator/policy_engine.py` — classe `PolicyEngine`, limites por recurso (Pearch, voice, tokens, concorrência); `app/auth/dependencies.py` — `get_current_user_or_demo()`, proteção de endpoints; `app/shared/resilience/circuit_breaker.py` — `CircuitBreaker` para APIs externas (3 estados: CLOSED/OPEN/HALF_OPEN) |
| **PII em logs** | MÉDIO | `PIIMasker` redige CPF, email, telefone, nomes em logs + `input_hash` (SHA-256) para desidentificação | **PRESENTE** | `app/shared/pii_masking.py` — classe `PIIMasker`, patterns regex para CPF, email, telefone, nomes; `app/shared/structured_logging.py` — `JSONFormatter` com integração de PII masking automático |

**Nota para o auditor — como verificar cada mitigação:**

1. **Prompt injection**: Abrir `app/shared/prompt_injection.py` e verificar as 6 categorias de detecção. Abrir `app/shared/compliance/fairness_guard.py` e verificar os 3 níveis (método `check()` para regex, `check_implicit_bias()` para implícito, `check_semantic()` para LLM). Testar com queries discriminatórias e com injection attempts.

2. **WSI**: Abrir `app/services/wsi_service.py` e verificar os 7 blocos de avaliação. Verificar que o scoring é determinístico (não depende apenas do LLM) e que há calibração cruzada entre blocos.

3. **Jailbreak**: Abrir os 4 system prompts ReAct (`wizard_system_prompt.py`, `kanban_system_prompt.py`, `talent_system_prompt.py`, `jobs_mgmt_system_prompt.py`) e verificar as seções CONTRA-ARGUMENTAÇÃO. Abrir `app/shared/agents/react_loop.py` e verificar `max_iterations` no `ReActConfig`.

4. **Data poisoning**: Abrir `app/shared/agents/learning_extractor.py` e verificar o fluxo de extração e validação de padrões antes de persistência.

5. **Tenant leakage**: Abrir `app/auth/dependencies.py` e verificar que `company_id` é extraído do JWT. Fazer grep por `company_id` nos repositórios para confirmar que todas as queries filtram por tenant.

6. **API abuse**: Abrir `app/orchestrator/policy_engine.py` e verificar os limites configurados. Verificar rate limiting nos middlewares.

7. **PII**: Abrir `app/shared/pii_masking.py` e verificar os patterns de redação. Fazer grep por `PIIMasker` para confirmar integração no pipeline de logging.

### 18.5 CI/CD e Versionamento de IA

| Aspecto | Status | Detalhes |
|---------|--------|---------|
| Prompt versioning | **PRESENTE** | Todos os 10 domínios com prompts em YAML (`app/prompts/domains/`) + fallback inline, versionados via git |
| Model versioning | **PRESENTE** | `model_version` field em AIInferenceLog |
| A/B testing | **PRESENTE** | `ABTestingManager` (`app/shared/ab_testing.py`) com hash-based assignment e tracking de resultados por variante |
| Staging environment | **PARCIAL** | Feature flags permitem rollout gradual |
| Rollback de prompts | **PARCIAL** | Via git revert, sem rollback automático |
| Training data mgmt | **PRESENTE** | `TrainingDataService` prepara dados para fine-tuning |
| Prompt hash tracking | **PRESENTE** | `prompt_hash` em AuditLog para reprodutibilidade |

---

## 19. Technical Debt & Risks (Dívida Técnica e Riscos)

### 19.1 TODOs e FIXMEs no Código

**Total original:** ~30 ocorrências em 19 arquivos  
**Corrigidos na auditoria (21/02/2026):** 3 críticos (demo-user em chat.py/candidates.py, encriptação ATS) + 9 melhorias de infraestrutura (vide seção 21.2.1)  
**Restantes:** ~18 TODOs de menor prioridade (billing, Teams bot, market data, rate limit DB check, etc.)

| Arquivo | TODO | Impacto | Status |
|---------|------|---------|--------|
| `api/v1/credits.py` | "TODO: Implement real credit management system" | ALTO — billing não implementado | ⏳ PENDENTE |
| ~~`api/v1/chat.py`~~ | ~~`user_id: str = "demo-user"` (hardcoded)~~ | ~~ALTO~~ | ✅ CORRIGIDO — `get_current_user_or_demo()` |
| ~~`api/v1/candidates.py`~~ | ~~`user_id="demo-user"`~~ | ~~ALTO~~ | ✅ CORRIGIDO — `get_current_user_or_demo()` |
| ~~`api/v1/ats.py`~~ | ~~"TODO: Encrypt in production" (API key)~~ | ~~CRÍTICO~~ | ✅ CORRIGIDO — Fernet encryption (`app/shared/encryption.py`) |
| `api/v1/ats.py` | "TODO: Execute sync in background task" | MÉDIO — sync síncrono | ⏳ PENDENTE |
| `domains/communication/services/teams_bot.py` | "TODO: Integrate with LIA conversation agent" | MÉDIO — Teams bot incompleto | ⏳ PENDENTE |
| `domains/job_management/agents/job_vacancy_nodes.py` | "TODO: Integrate with real market data API" | BAIXO — usa dados simulados | ⏳ PENDENTE |
| `orchestrator/policy_engine.py` | "TODO: Check actual usage from database" | MÉDIO — rate limit sem DB check | ⏳ PENDENTE |

### 19.2 Test Coverage

**Arquivos de teste encontrados:** ~35 em `tests/`

| Tipo | Quantidade | Cobertura |
|------|-----------|-----------|
| E2E tests | 8 (`test_pipeline_e2e.py`, `test_domain_consolidation_e2e.py`, etc.) | Pipeline, domínios |
| Agent tests | 3 (`test_agent_comprehensive.py`, `test_agent_regression.py`) | Agentes |
| Feature tests | 4 (`test_feature_flags.py`, `test_feature_flags_integration.py`) | Feature flags |
| Unit tests | ~20 (diversos) | Resolvers, compressão, referências |

**Gaps de teste resolvidos (21/02/2026):**
- ✅ FairnessGuard: 24 testes cobrindo 8 categorias de bias (`tests/test_compliance_fairness.py`)
- ✅ FactChecker: 14 testes cobrindo 4 tipos de claims (`tests/test_compliance_factchecker.py`)
- ✅ LGPD compliance: 6 testes de estrutura de API (`tests/test_compliance_lgpd.py`)
- **Total: 44 testes de compliance adicionados**

**Gaps de teste remanescentes:**
- Sem testes de carga/performance
- Sem testes de integração end-to-end para circuit breakers
- Sem testes para PII masking patterns customizados

### 19.3 Hardcoded Values

| Local | Valor | Deveria ser | Status |
|-------|-------|-------------|--------|
| ~~`api/v1/chat.py:32`~~ | ~~`user_id = "demo-user"`~~ | ~~From JWT auth~~ | ✅ CORRIGIDO — `get_current_user_or_demo()` |
| ~~`api/v1/candidates.py:1031`~~ | ~~`user_id = "demo-user"`~~ | ~~From JWT auth~~ | ✅ CORRIGIDO — `get_current_user_or_demo()` |
| ~~`auth/models.py:31`~~ | ~~`default="demo_company"`~~ | ~~From tenant resolution~~ | ✅ CORRIGIDO — `get_current_user_or_demo()` |
| `api/v1/auth.py:34` | `FRONTEND_URL = "https://plataforma-lia.replit.app"` | From env var | ⏳ PENDENTE |
| Vários | Temperature `0.7` fixo | Configurável por use case | ⏳ PENDENTE |

### 19.4 Single Points of Failure

| SPOF | Impacto | Mitigação |
|------|---------|-----------|
| Claude API (Anthropic) | Sem LLM → plataforma inoperável | Fallback para Gemini implementado |
| PostgreSQL (Neon) | Sem DB → tudo falha | Neon auto-failover, pool_pre_ping |
| Redis | Sem cache → latência alta, mas funcional | Degradação graciosa (fallback DB) |
| TaskManager (async) | Sem processamento async → degradação | DLQ + retry automático, fallback síncrono |

---

## 20. Recommendations (Recomendações)

### 20.1 Críticas (Antes de Produção em Escala)

| # | Recomendação | Impacto | Esforço | Status |
|---|-------------|---------|---------|--------|
| 1 | **~~Eliminar `demo-user` hardcoded~~** — Integrar JWT auth em todas as APIs | CRÍTICO | Médio | ✅ IMPLEMENTADO — `get_current_user_or_demo()` em `auth/dependencies.py` |
| 2 | **~~Encriptar API keys de ATS~~** — Atualmente em plaintext | CRÍTICO | Baixo | ✅ IMPLEMENTADO — Fernet encryption em `app/shared/encryption.py` |
| 3 | **~~Implementar prompt injection protection~~** — Além do FairnessGuard | ALTO | Médio | ✅ IMPLEMENTADO — `PromptInjectionGuard` em `app/shared/prompt_injection.py` |
| 4 | **Implementar billing real** — `credits.py` é stub | ALTO | Alto | ⏳ PENDENTE |
| 5 | **~~Migrar logging para structured JSON~~** — Facilita observabilidade | ALTO | Médio | ✅ IMPLEMENTADO — `StructuredLogger` em `app/shared/structured_logging.py` |

### 20.2 Melhorias de Arquitetura (Priorizadas por Impacto)

| # | Melhoria | Impacto | Esforço | Status |
|---|---------|---------|---------|--------|
| 1 | **~~A/B testing para prompts~~** — Medir impacto de mudanças em prompts | ALTO | Médio | ✅ IMPLEMENTADO — `ABTestingManager` em `app/shared/ab_testing.py` |
| 2 | **~~Distributed tracing~~** — OpenTelemetry para rastrear requests cross-service | ALTO | Médio | ✅ IMPLEMENTADO — `@trace_span` decorator em `app/shared/tracing.py` |
| 3 | **~~Circuit breakers~~** para APIs externas — Pearch, Deepgram, Mailgun | MÉDIO | Baixo | ✅ IMPLEMENTADO — `CircuitBreaker` em `app/shared/resilience/circuit_breaker.py` |
| 4 | **~~Testes automatizados para compliance~~** — FairnessGuard, FactChecker | MÉDIO | Baixo | ✅ IMPLEMENTADO — 44 testes em `tests/test_compliance_*.py` |
| 5 | **~~Cache invalidation strategy~~** — Documentar e padronizar | MÉDIO | Baixo | ✅ IMPLEMENTADO — `CacheStrategy` em `app/shared/cache_strategy.py` |
| 6 | **~~PII masking em logs~~** — Garantir que dados pessoais não vazem em logs | ALTO | Médio | ✅ IMPLEMENTADO — `PIIMasker` em `app/shared/pii_masking.py` |

### 20.3 Componentes Faltantes para Produção

| Componente | Status | Prioridade |
|-----------|--------|-----------|
| ~~Prompt injection filter (genérico)~~ | ✅ IMPLEMENTADO (`app/shared/prompt_injection.py`) | ~~P0~~ |
| ~~Structured logging (JSON)~~ | ✅ IMPLEMENTADO (`app/shared/structured_logging.py`) | ~~P1~~ |
| ~~Distributed tracing (OpenTelemetry)~~ | ✅ IMPLEMENTADO (`app/shared/tracing.py`) | ~~P1~~ |
| ~~Circuit breaker pattern~~ | ✅ IMPLEMENTADO (`app/shared/resilience/circuit_breaker.py`) | ~~P2~~ |
| ~~A/B testing de prompts~~ | ✅ IMPLEMENTADO (`app/shared/ab_testing.py`) | ~~P2~~ |
| Load testing suite | ⏳ PENDENTE | P2 |
| API documentation (OpenAPI auto) | PARCIAL (FastAPI gera) | P3 |
| Monitoring dashboards | ⏳ PENDENTE | P2 |
| ~~CompanyHiringPolicy (modelo + API + tela)~~ | ✅ IMPLEMENTADO — PolicyReActAgent com 13 tools, 3 stages, FairnessGuard integrado (seção 3.23 / 5.11) | ~~P1~~ |
| ~~Automação progressiva (5 níveis)~~ | ✅ IMPLEMENTADO — Integrado no PolicyReActAgent com calibração por porte (STARTUP/PME/CORPORAÇÃO) | ~~P1~~ |

---

## 21. Pontos de Atenção para o Auditor

### 21.1 Pontos Fortes Identificados

1. **Separação clara de domínios:** Cada domínio tem escopo definido, contrato ABC, e actions/tools/services próprios
2. **Roteamento em cascata:** Otimiza custo e latência (cache → regex → LLM)
3. **Compliance multi-camada:** FairnessGuard 3-tier (regex + implícito + LLM semântico) + FactChecker + AuditService cobrem bias, veracidade e rastreabilidade
4. **Metodologia WSI bem estruturada:** 7 blocos com frameworks psicométricos estabelecidos
5. **LGPD implementada em profundidade:** Portal do titular, consentimento, retenção, DPO
6. **Confirmação humana para ações destrutivas:** `requires_confirmation=True` em ações de alto impacto
7. **Multi-tenancy:** `context.tenant_id` presente em todas as execuções de domínio
8. **Feature flags:** Controle granular de funcionalidades por empresa, incluindo `USE_REACT_AGENTS` com fallback automático
9. **Infraestrutura de segurança completa:** Encriptação Fernet, PII masking, prompt injection guard, circuit breakers
10. **Observabilidade moderna:** Structured JSON logging, distributed tracing com `@trace_span`, A/B testing de prompts
11. **Testes de compliance abrangentes:** 44 testes automatizados cobrindo FairnessGuard, FactChecker e LGPD
12. **Arquitetura ReAct madura:** 7 agentes ReAct com 4-file pattern padronizado (agent.py, tool_registry.py, system_prompt.py, stage_context.py), ReactAgentRegistry singleton e AgentFactory
13. **Anti-sycophancy guardrails:** Contra-argumentação baseada em dados nos 4 agentes principais (Wizard, Kanban, Talent, JobsMgmt), com calibração por porte de empresa (STARTUP/PME/CORPORAÇÃO)
14. **Few-shot examples:** Integrados em todos os system prompts ReAct para melhorar consistência e qualidade das respostas
15. **Long-Term Memory:** LongTermMemoryService + MemoryIntegration para continuidade cross-session de preferências e padrões do recrutador
16. **Agent Explainability:** ExecutionLogStore + API + Frontend panel — rastreamento completo do raciocínio ReAct (Thought → Action → Observation)
17. **Multi-Channel Communication:** ChannelAdapter + ChannelRouter + MultiChannelService com 5 adapters (email, WhatsApp, SMS, Teams, in-app)
18. **Async Task Processing:** TaskRecord + TaskScheduler + EnhancedTaskManager + Dead Letter Queue (DLQ) para processamento robusto em escala
19. **Production Readiness:** Health endpoint unificado, RequestIdMiddleware, Rate Limiter (200/min, 2000/hr) por tenant
20. **PolicyReActAgent (Hiring Policy):** Domínio hiring_policy totalmente implementado com 13 tools, 3 stages, FairnessGuard semântico e benchmarks de 8 setores

### 21.2 Pontos que Merecem Atenção (Status Atualizado 23/02/2026)

1. **~~Keyword matching como Layer 2~~** ✅ CORRIGIDO: FastRouter agora usa regex compilado com word-boundary matching. Pipeline domain `process_intent()` migrado de substring para `re.search(r'\b...\b')`. Adicionada penalidade de ambiguidade de 0.15 quando top 2 domínios têm gap de confiança < 0.1.

2. **~~Sobreposição entre domínios~~** ✅ CORRIGIDO: Criado `DomainActionRegistry` (`app/shared/domain_action_registry.py`) com ownership único por ação. Ações compartilhadas usam padrão owner + alias (ex: `compare_candidates` → owner=`cv_screening`, aliases=`sourcing`, `recruiter_assistant`). Método `should_delegate()` redireciona automaticamente.

3. **~~Prompts inline vs. YAML~~** ✅ CORRIGIDO: Pipeline Transition migrado para `app/prompts/domains/pipeline_transition.yaml`. Todos os 10 domínios agora usam prompts em YAML com fallback inline.

4. **~~Delegação `delegate_to_agent`~~** ✅ CORRIGIDO: Criado `DelegationFallbackHandler` (`app/shared/delegation_fallback.py`) com logging de ações não mapeadas, mensagem user-friendly em português, e tracking de stats (últimas 1000 ações). Integrado em `job_management/domain.py`.

5. **~~Validação de parâmetros~~** ✅ CORRIGIDO: Criado decorator `@validate_params` (`app/shared/param_validation.py`) com schemas Pydantic centralizados (`ToolParamSchemas`). Validação automática com mensagens de erro estruturadas em português.

6. **~~Predição de sub-status~~** ✅ CORRIGIDO: `_handle_predict_sub_status` agora faz HTTP bridge para `/api/v1/pipeline/transition/bulk-predict-substatus` via httpx, eliminando o gap de database session. Pattern consistente com `_handle_move_candidate`.

7. **~~Testes de compliance~~** ✅ CORRIGIDO: 44 testes automatizados adicionados — FairnessGuard (24 testes, 8 categorias), FactChecker (14 testes, 4 tipos de claims), LGPD compliance (6 testes de estrutura de API).

### 21.2.1 Novos Módulos de Infraestrutura — 9 Componentes (21/02/2026)

| Componente | Arquivo | Descrição |
|------------|---------|-----------|
| **Encriptação ATS** | `app/shared/encryption.py` | Fernet encryption para API keys de ATS (antes em plaintext) |
| **Circuit Breaker** | `app/shared/resilience/circuit_breaker.py` | 3 estados (CLOSED/OPEN/HALF_OPEN) para APIs externas |
| **PII Masking** | `app/shared/pii_masking.py` | Redação de CPF, email, telefone, nomes em logs (LGPD) |
| **Cache Strategy** | `app/shared/cache_strategy.py` | TTLs por domínio (12 domínios de cache) com invalidação por evento |
| **Prompt Injection** | `app/shared/prompt_injection.py` | Detecção de 6 categorias de injection (PT/EN) com sanitização |
| **Structured Logging** | `app/shared/structured_logging.py` | JSON formatter com context logger e trace correlation |
| **Distributed Tracing** | `app/shared/tracing.py` | Lightweight spans com `@trace_span` decorator e stats |
| **A/B Testing** | `app/shared/ab_testing.py` | Framework de experimentos para prompts com hash-based assignment |
| **Auth Hardening** | `app/auth/dependencies.py` | `get_current_user_or_demo` elimina hardcoded demo-user/demo_company |

### 21.2.2 Mudanças da Arquitetura ReAct (23/02/2026)

A migração para a arquitetura ReAct introduziu mudanças fundamentais na plataforma que o auditor deve considerar:

| Aspecto | Antes (Legacy) | Depois (ReAct) | Impacto |
|---------|---------------|----------------|---------|
| **Padrão de agente** | Classes monolíticas com actions/tools inline | 4-file pattern (agent.py, tool_registry.py, system_prompt.py, stage_context.py) | Separação de responsabilidades, manutenibilidade |
| **Registro de agentes** | Instanciação direta, sem registro central | ReactAgentRegistry (singleton) + AgentFactory | Controle centralizado, feature flags, fallback |
| **Loop de raciocínio** | Execução linear de actions | ReAct loop (Thought → Action → Observation) com ReActObserver | Raciocínio explícito, auditável via ExecutionLogStore |
| **Memória de trabalho** | Contexto efêmero por request | AgentWorkingMemory (sessão) + LongTermMemory (cross-session) | Continuidade, personalização, aprendizado |
| **Tools** | 109 tools legacy (tool_id pattern) | 89 ReAct tools com registries tipados + tools legacy | Tipagem forte, validação automática, documentação |
| **FairnessGuard** | Regex simples (Camada 1 apenas) | 3 camadas (regex + implícito + LLM semântico) integrado nos system prompts | Detecção profunda de viés, educação proativa |
| **Anti-sycophancy** | Não existia | Guardrails nos 4 agentes principais com calibração por porte | Qualidade de decisões, contra-argumentação baseada em dados |
| **Explainability** | AuditLog básico | ExecutionLogStore + API + Frontend panel | Transparência total do raciocínio do agente |
| **Async Processing** | RabbitMQ + Celery (planejado) | TaskManager nativo com DLQ, retry, monitoring | Simplificação operacional, sem dependência externa |
| **Hiring Policy** | CompanyHiringPolicy (modelo planejado) | PolicyReActAgent com 13 tools, 3 stages, benchmarks 8 setores | Domínio totalmente funcional |
| **Feature flag** | Flags individuais por funcionalidade | `USE_REACT_AGENTS` com fallback automático para legacy | Rollout seguro, reversível |

**Riscos da migração ReAct que o auditor deve avaliar:**
1. **Coexistência legacy/ReAct:** Os 18 agentes legacy continuam operando em paralelo — há risco de divergência de comportamento entre agentes legacy e ReAct para o mesmo domínio?
2. **MAX_TOOL_CALLS_PER_REQUEST:** Limite de 3 tool calls por request pode ser restritivo para fluxos complexos do PolicyReActAgent (3 stages)
3. **LongTermMemory persistence:** Dados cross-session aumentam superfície de ataque para data leakage — isolation por tenant está garantida?
4. **ExecutionLogStore volume:** Logs detalhados de raciocínio (Thought/Action/Observation) podem gerar volume significativo — estratégia de retenção definida?

### 21.3 Perguntas para o Auditor Avaliar

1. A granularidade dos 10 domínios (incluindo hiring_policy) é adequada ou há domínios que deveriam ser fundidos/separados?
2. O cascade de roteamento (Memory → Regex → LLM) tem cobertura suficiente para o vocabulário de um recrutador brasileiro?
3. A metodologia WSI com 7 blocos e 4 frameworks psicométricos é suficiente para uma avaliação justa e completa?
4. O FairnessGuard 3-tier (regex + implícito + LLM semântico) oferece cobertura adequada para detectar vieses sutis em políticas de contratação?
5. Os prompts defensivos + anti-sycophancy guardrails são suficientes para prevenir jailbreak, prompt injection e concordância passiva com decisões inadequadas?
6. A retenção de dados (730-1825 dias) está alinhada com as melhores práticas de compliance?
7. O pipeline completo (triagem → contratação) tem pontos cegos onde candidatos podem "se perder"?
8. A arquitetura suporta escala para centenas de empresas e milhares de candidatos simultâneos?
9. A coexistência de 7 agentes ReAct + 18 agentes legacy é sustentável a longo prazo, ou há risco de divergência de comportamento?
10. O sistema de Long-Term Memory mantém isolamento adequado entre tenants para dados cross-session?
11. Os few-shot examples nos system prompts ReAct são representativos o suficiente para cobrir a diversidade de cenários de recrutamento no mercado brasileiro?
12. O ExecutionLogStore (explainability) registra informação suficiente para atender requisitos do EU AI Act Art. 14 e LGPD Art. 20?

---

## Apêndice A: Contagens Detalhadas

| Componente | Quantidade | Método de Verificação |
|------------|-----------|----------------------|
| Domínios de IA | 10 (incluindo hiring_policy) | Contagem manual de classes @register_domain |
| Agentes | **26** (7 ReAct + 1 LangGraph + 18 Legacy) | Contagem de classes em agents/ e domains/*/agents/ |
| Actions (ações) | 205 | grep `action_id` em actions.py (9 domínios) + 5 inline em pipeline/domain.py |
| Tools legacy (ferramentas) | 109 | grep `tool_id` em tools*/ (9 domínios) + 5 inline em pipeline/domain.py (DOMAIN_TOOLS) |
| Tools ReAct | **89** (Wizard:9, Kanban:14, Talent:12, JobsMgmt:13, Policy:13, Sourcing:14, Pipeline:14) | Contagem em tool_registry.py de cada agente ReAct |
| Services (serviços) | **137** | Verificado por MAPA doc (contagem de classes de serviço em todos os domínios) |
| Keyword maps (regex) | ~600 keywords | Contagem de entradas em _KEYWORD_ACTION_MAP |
| System prompts | 10 (todos YAML com fallback inline) + 7 ReAct system_prompt.py | Listagem de app/prompts/domains/ + domains/*/agents/ |
| Compliance rules | 8 categorias de bias |
| FairnessGuard | 3 camadas (regex + implícito + LLM semântico) |
| Anti-sycophancy guardrails | 4 agentes (Wizard, Kanban, Talent, JobsMgmt) |
| LGPD endpoints | 3 módulos (Portal, Consent, DPO) |
| Feature flags | ~10 flags documentadas + `USE_REACT_AGENTS` |
| ATS integrations | 3 (Merge, Gupy, Pandapé) |
| LLM providers | 3 (Anthropic, OpenAI, Google) |
| Communication channels | **5** (Email, WhatsApp, Teams, SMS, in-app) |
| Multi-Channel adapters | 5 (ChannelAdapter + ChannelRouter + MultiChannelService) |
| Async Task Processing | TaskRecord + TaskScheduler + EnhancedTaskManager + DLQ |
| Long-Term Memory | LongTermMemoryService + MemoryIntegration (cross-session) |
| Agent Explainability | ExecutionLogStore + API + Frontend panel |
| Production Readiness | Health endpoint, RequestIdMiddleware, Rate Limiter (200/min, 2000/hr) |
| Database models | 86 (45 arquivos) |
| Observability models | 15 (2.165 linhas em observability.py) |
| Compliance frameworks | 7 (SOX, SOC2, ISO27001, LGPD, BCB498, EUAI, NYC144) |
| TODOs/FIXMEs | ~18 restantes (~12 corrigidos de ~30 originais) |
| Test files | ~35 |
| Compliance tests | 44 (FairnessGuard=24, FactChecker=14, LGPD=6) |
| Shared infrastructure modules | 10 (encryption, delegation_fallback, domain_action_registry, param_validation, pii_masking, cache_strategy, prompt_injection, structured_logging, tracing, ab_testing) |
| LGPD consent types | 6 |
| LGPD subject rights | 7 (Art. 18) |
| Bias dimensions (Tezi AI) | 11 |
| User roles (RBAC) | 3 (admin, recruiter, viewer) |

---

## Apêndice B: Glossário

| Termo | Definição |
|-------|-----------|
| **WSI** | WeDoTalent Skill Index — metodologia proprietária de avaliação de candidatos em 7 blocos |
| **CBI** | Competency-Based Interview — framework de entrevista baseada em competências |
| **JD** | Job Description — descrição de vaga |
| **ATS** | Applicant Tracking System — sistema de rastreamento de candidatos |
| **DPO** | Data Protection Officer — encarregado de proteção de dados |
| **LGPD** | Lei Geral de Proteção de Dados — lei brasileira de proteção de dados |
| **SOX** | Sarbanes-Oxley Act — lei de governança corporativa |
| **EU AI Act** | Regulamento europeu de inteligência artificial |
| **Big Five (OCEAN)** | Modelo de personalidade: Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism |
| **Bloom Taxonomy** | Taxonomia de objetivos educacionais (lembrar, entender, aplicar, analisar, avaliar, criar) |
| **Dreyfus Model** | Modelo de aquisição de habilidades (novice, advanced beginner, competent, proficient, expert) |
| **WRF** | Weighted Ranking Framework — framework de ranking ponderado |
| **PGV** | Post-Graduate Value — análise de gaps semânticos |
| **BARS** | Behaviorally Anchored Rating Scales — escalas de avaliação ancoradas em comportamento |

---

## Apêndice C: Procedimento de Verificação de Contagens

Os números neste documento foram verificados via comandos automatizados em 23/02/2026. Para reproduzir:

### Actions por domínio (legacy):
```bash
for domain in sourcing job_management cv_screening communication interview_scheduling analytics ats_integration automation recruiter_assistant; do
  count=$(grep -c 'action_id' app/domains/$domain/actions.py 2>/dev/null || echo 0)
  echo "$domain: $count actions"
done
```

**Resultado:** sourcing=30, job_management=29, cv_screening=25, communication=20, interview_scheduling=20, analytics=18, ats_integration=18, automation=20, recruiter_assistant=20. **Subtotal: 200 actions.** + pipeline_transition=5 (inline em domain.py). **Total: 205 actions.**

### Tools legacy por domínio:
```bash
for domain in sourcing job_management cv_screening communication interview_scheduling analytics ats_integration automation recruiter_assistant pipeline; do
  count=$(grep -roh '"tool_id": "[^"]*"' app/domains/$domain/tools* 2>/dev/null | sort -u | wc -l)
  echo "$domain: $count unique tools"
done
```

**Resultado:** sourcing=19, job_management=13, cv_screening=12, communication=10, interview_scheduling=10, analytics=10, ats_integration=10, automation=10, recruiter_assistant=10, pipeline=0 (via grep). **Subtotal: 104 tools.** + pipeline_transition=5 (DOMAIN_TOOLS inline em domain.py, não detectados por grep). **Total: 109 tools legacy.**

### Tools ReAct por agente:
```bash
for agent_dir in app/domains/*/agents/; do
  if [ -f "$agent_dir/tool_registry.py" ]; then
    count=$(grep -c 'def ' "$agent_dir/tool_registry.py" 2>/dev/null || echo 0)
    echo "$(basename $(dirname $(dirname $agent_dir))): $count ReAct tools"
  fi
done
```

**Resultado:** Wizard=9, Kanban=14, Talent=12, JobsMgmt=13, Policy=13, Sourcing=14, Pipeline=14. **Total: 89 ReAct tools.**

### Agentes ReAct:
```bash
grep -rl 'class.*ReActAgent' app/domains/*/agents/*.py | wc -l
```

**Resultado:** 7 agentes ReAct (WizardReActAgent, KanbanReActAgent, TalentReActAgent, JobsMgmtReActAgent, PolicyReActAgent, SourcingReActAgent, PipelineReActAgent).

### Services (total):
```bash
grep -rl 'class.*Service' app/services/ app/domains/*/services/ app/shared/ | wc -l
```

**Resultado:** **137 services** (verificado por MAPA doc).

### Nota sobre PolicyEngine
Existem duas implementações coexistentes:
- `app/orchestrator/policy_engine.py` — **Gate principal**, invocado pelo Orchestrator antes de cada requisição. Controla limites de uso (Pearch, voice screening, tokens, concorrência).
- `app/services/policy_engine_service.py` — Regras de negócio adicionais disponíveis para uso por domínios individuais (limites de candidatos por vaga, horários de comunicação, escalation).

O auditor deve verificar se a separação é intencional ou se houve divergência não planejada na evolução do código.

---

*Documento gerado em 21/02/2026, atualizado para v7.0 em 23/02/2026.*

*Mudanças na v7.0:*
- *Seção 1: Resumo Executivo atualizado com números-chave corretos (26 agentes, 89 ReAct tools, 137 services, FairnessGuard 3-tier, anti-sycophancy, Long-Term Memory, Agent Explainability, Multi-Channel, Async Tasks, Production Readiness)*
- *Seção 3: Novas subseções 3.23-3.27 — Arquitetura ReAct Agent System, Long-Term Memory, Agent Explainability, Multi-Channel Communication, Async Task Processing at Scale*
- *Seção 5: Domínio hiring_policy adicionado (5.11) com PolicyReActAgent, 13 tools, 3 stages, FairnessGuard integrado, benchmarks 8 setores*
- *Seção 7: ReAct Agent Tool Registries adicionado (7.11) com 89 tools documentadas por agente*
- *Seção 8: Catálogo de serviços atualizado (~45 → 137), incluindo Hiring Policy, Multi-Channel e Async Task services*
- *Seção 11: FairnessGuard atualizado para 3 camadas (regex + implícito + LLM semântico), integração em Wizard e Kanban, anti-sycophancy e LGPD nos agentes*
- *Seção 16: Corrigida inconsistência "Unstructured → Structured JSON" (já implementado), adicionados Rate Limiter, Health endpoint, RequestIdMiddleware, TaskManager nativo (substituindo referências a RabbitMQ+Celery)*
- *Seções 19-21: CompanyHiringPolicy marcado como IMPLEMENTADO (PolicyReActAgent), novos pontos fortes (ReAct, anti-sycophancy, 3-tier FairnessGuard, LTM), subseção 21.2.2 com mudanças ReAct, perguntas atualizadas para auditor*
- *Apêndices: Contagens atualizadas (Apêndice A), comandos de verificação para ReAct adicionados (Apêndice C)*

*Itens pendentes: billing real, sync assíncrono ATS, Teams bot, market data API, rate limit DB, load testing, monitoring dashboards. Para dúvidas, contatar a equipe de engenharia da WeDoTalent.*
