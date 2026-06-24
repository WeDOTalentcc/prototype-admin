# Mapa de Funcionalidades — MVP Alpha 1 WeDOTalent

**Versão:** 2.0  
**Data:** 17/06/2026  
**Atualizado por:** Auditoria completa do código Replit (`feat/benefits-prv-canonical`) vs. documento v6.3 (31/03/2026)  
**Escopo:** Funcionalidades implementadas, camada IA, compliance, gaps reais  

> **Este documento substitui** `ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md` (v6.3). O documento anterior descrevia ~30% da plataforma real e usava uma taxonomia linear (E1-E9, Ag.0-Ag.8) que não reflete mais a arquitetura atual.

---

## ÍNDICE

1. [Visão Geral do Produto](#1-visão-geral-do-produto)
2. [Números da Plataforma](#2-números-da-plataforma)
3. [Arquitetura de Orquestração IA](#3-arquitetura-de-orquestração-ia)
4. [Jornada do Recrutador — Funcionalidades](#4-jornada-do-recrutador--funcionalidades)
5. [Jornada do Candidato — Funcionalidades](#5-jornada-do-candidato--funcionalidades)
6. [Admin WeDOTalent (Staff) — Funcionalidades](#6-admin-wedotalent-staff--funcionalidades)
7. [Agent Studio & Marketplace](#7-agent-studio--marketplace)
8. [Configurações (Tenant Admin)](#8-configurações-tenant-admin)
9. [Mapa Completo de Domínios IA](#9-mapa-completo-de-domínios-ia)
10. [Camadas de Compliance](#10-camadas-de-compliance)
11. [Camadas de Inteligência](#11-camadas-de-inteligência)
12. [Canais de Comunicação](#12-canais-de-comunicação)
13. [Integração Microsoft Teams](#13-integração-microsoft-teams)
14. [Feature Flags & Caminhos Ativos](#14-feature-flags--caminhos-ativos)
15. [Gaps Reais & Próximos Passos](#15-gaps-reais--próximos-passos)
16. [Arquivos de Referência](#16-arquivos-de-referência)

---

## 1. VISÃO GERAL DO PRODUTO

**WeDOTalent** é uma plataforma de recrutamento e seleção com IA integrada (LIA — assistente de IA), composta por 3 camadas:

| Camada | Stack | Porta | Path Replit |
|--------|-------|-------|-------------|
| **Frontend** | Next.js 16 + React + TypeScript | 3000 | `plataforma-lia/` |
| **Backend IA** | Python + FastAPI + LangGraph | 8001 | `lia-agent-system/` |
| **Backend Rails** (legacy) | Ruby on Rails | 3001 | `ats_api/` |

**Modelo de negócio:** SaaS multi-tenant. Cada empresa (tenant) tem configurações próprias de IA, persona, compliance e processo seletivo.

**Premissa MVP Alpha 1:** Fluxo completo de recrutamento, da importação/criação da vaga até o agendamento de entrevista, com IA assistindo em cada etapa (geração de JD, triagem WSI, scoring, busca, comunicação, feedback).

---

## 2. NÚMEROS DA PLATAFORMA

| Dimensão | Quantidade |
|----------|-----------|
| Domínios backend (IA) | 37 |
| Classes de agente IA | 35+ |
| Serviços backend | 218 |
| Tool registries | 37 |
| Páginas frontend | 66 |
| Rotas proxy API (FE→BE) | 709 |
| Componentes Settings | 60+ |
| Modais | 55+ |
| Hooks React (domínios) | 32 |
| Camadas de compliance | 8+ |
| Módulos de inteligência | 18+ |
| Arquivos de teste | 1.855 |
| Arquivos de voz | 38 |

---

## 3. ARQUITETURA DE ORQUESTRAÇÃO IA

A plataforma evoluiu de um orquestrador central (MainOrchestrator) para **3 caminhos de orquestração** controlados por feature flags:

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAMINHOS DE ORQUESTRAÇÃO                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────┐                            │
│  │  FEDERADO (recruiter_copilot)    │  ← CAMINHO LIVE           │
│  │  LIA_FEDERATED_PRIMARY=true      │                            │
│  │                                  │                            │
│  │  Agente único com scoping        │                            │
│  │  dinâmico de ~15 tools/turno     │                            │
│  │  (de ~179 disponíveis)           │                            │
│  │                                  │                            │
│  │  Entry: agent_chat_sse.py        │                            │
│  └──────────────────────────────────┘                            │
│                                                                  │
│  ┌──────────────────────────────────┐                            │
│  │  WIZARD ORCHESTRATOR             │  ← CRIAÇÃO DE VAGA LIVE   │
│  │  LIA_WIZARD_ORCHESTRATOR=1       │                            │
│  │                                  │                            │
│  │  Fluxo guiado de criação com     │                            │
│  │  gate classifier + sessão        │                            │
│  │                                  │                            │
│  │  Entry: wizard_orchestrator.py   │                            │
│  └──────────────────────────────────┘                            │
│                                                                  │
│  ┌──────────────────────────────────┐                            │
│  │  SUPERVISOR (MainOrchestrator)   │  ← DORMANTE               │
│  │  LIA_BUBBLE_VIA_SUPERVISOR       │  (não ativo em .env)       │
│  │                                  │                            │
│  │  Pipeline: FairnessGuard →       │                            │
│  │  TenantContext → PendingAction → │                            │
│  │  ActionExecutor → CascadedRouter │                            │
│  │  → Domain ReAct Agent            │                            │
│  │                                  │                            │
│  │  Entry: main_orchestrator.py     │                            │
│  └──────────────────────────────────┘                            │
│                                                                  │
│  ┌──────────────────────────────────┐                            │
│  │  HITL GATE                       │  ← DORMANTE (flag off)    │
│  │  LIA_HITL_GATE=on               │                            │
│  │                                  │                            │
│  │  Gate de confirmação humana em   │                            │
│  │  7 tools sensíveis (close_job,   │                            │
│  │  send_email, whatsapp, bulk,     │                            │
│  │  reject, publish)                │                            │
│  └──────────────────────────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

### Agentes Registrados (agents_registry.yaml)

| Nome registro | Domínio | Modelo | Papel |
|--------------|---------|--------|-------|
| pipeline | pipeline | claude-sonnet-4-6 | Gestão do pipeline de candidatos |
| sourcing | sourcing | claude-sonnet-4-6 | Busca e sourcing de candidatos |
| wizard | job_management | claude-sonnet-4-6 | Criação assistida de vagas |
| talent | talent_pool | claude-haiku-4-5 | Gestão de pools de talento |
| talent_funnel | recruiter_assistant | claude-sonnet-4-6 | Busca no funil de talentos |
| kanban | recruiter_assistant | claude-haiku-4-5 | Ações no kanban |
| hiring_policy | hiring_policy | claude-haiku-4-5 | Políticas de contratação |
| analytics | analytics | claude-sonnet-4-6 | Análises e métricas |
| ats_integration | ats_integration | claude-haiku-4-5 | Integração com ATS externo |
| automation | automation | claude-haiku-4-5 | Automação de workflows |
| communication | communication | claude-haiku-4-5 | Comunicação multicanal |
| offer_concierge | offer | — | Gestão de propostas (HITL gate) |

### Sub-agentes por domínio

| Domínio | Sub-agentes |
|---------|------------|
| **recruiter_assistant** | talent_react, talent_funnel_react, jobs_mgmt_react, kanban_react, kanban_action, kanban_insight, kanban_search |
| **sourcing** | sourcing_search, sourcing_planner, sourcing_enrich, sourcing_engagement, diversity_sourcing, github_sourcing, stackoverflow_sourcing, passive_pipeline, nurture_sequence, referral |
| **pipeline** | pipeline_action, pipeline_context, pipeline_decision, pipeline_transition |
| **cv_screening** | wsi_interview_graph (LangGraph), triagem_session_service |
| **job_creation** | graph.py (LangGraph), wizard_orchestrator |
| **interview_scheduling** | interview_graph (LangGraph) |
| **agent_studio** | custom_agent_runtime |

---

## 4. JORNADA DO RECRUTADOR — FUNCIONALIDADES

### 4.1 Dashboard & Visão Global (`/recrutar`)

**Página:** `/recrutar` — Visão Global de Vagas  
**O que faz:** Exibe todas as vagas organizadas por 8 estágios de lifecycle (ats_importada → rascunho → enriquecida → wsi_config → aguardando_aprovacao → publicada → ao_vivo → encerrada). Cards com métricas, CTAs contextuais por estágio.

| Subfuncionalidade | Camada IA | Status |
|-------------------|-----------|--------|
| Cards de vaga com métricas | Sem IA (dados do backend) | ✅ Implementado |
| CTA contextual por estágio | Deep-link para `/jobs/{id}?tab=edit&section=X` | ✅ Implementado |
| Preview lateral de vaga | Painel lateral espelhando kanban | ✅ Implementado |

### 4.2 Criação & Edição de Vagas (`/jobs`)

**Página:** `/jobs` (lista) + `/jobs/[id]` (detalhe com tabs)  
**O que faz:** Criar vaga manualmente ou importar do ATS. Editar dados (requisitos, benefícios, faixa salarial, modelo). Gerar JD com IA. Configurar triagem WSI.

| Subfuncionalidade | Camada IA | Serviço/Agente | Status |
|-------------------|-----------|----------------|--------|
| Criação manual de vaga | — | CRUD endpoints | ✅ |
| Importação do ATS | `ATSSyncService` (Gupy/Pandapé) | ats_integration domain | ⚠ Tombstone (sem `RAILS_API_URL`) |
| Geração de JD (Job Description) | Claude LLM | `JDGeneratorService` | ✅ |
| FairnessGuard no JD gerado | L1 block + L2 warn | `fairness_guard.check` em `jd_generation.py` | ✅ |
| Wizard de criação guiado (chat) | Claude LLM + gate classifier | `wizard_orchestrator` + `wizard_tool_registry` | ✅ (caminho LIVE) |
| Faixa salarial herdada da empresa | Resolução read-time | `match_from_bands` em `_shared.py` | ✅ |
| Benchmark salarial de mercado | Claude LLM (estimativa) | `MarketBenchmarkService` | ✅ (com flag `unverified`) |
| Processo seletivo (pipeline da vaga) | — | Herança + override de estágios | ✅ |
| Perguntas de elegibilidade | Shape canônico `EligibilityQuestionItem` | `EligibilityVerificationService` | ✅ |

### 4.3 Configuração do Roteiro WSI

**Onde:** Tab "Configurações" dentro de `/jobs/[id]`  
**O que faz:** Gerar/editar perguntas de triagem WSI (Work Sample Interview) calibradas por senioridade, competência e personalidade.

| Subfuncionalidade | Camada IA | Serviço/Agente | Status |
|-------------------|-----------|----------------|--------|
| Geração de perguntas WSI | Gemini LLM | `WSIQuestionGeneratorService` | ✅ |
| Calibração Dreyfus/Bloom/Big Five | Heurístico + LLM | `SeniorityContextCalibrator` | ✅ |
| Pipeline unificado (geração+calibração+scoring) | LLM + heurístico | `WSIScreeningPipeline` | ✅ |
| FairnessGuard nas perguntas | L1 block per-question | `wsi_questions.py` | ✅ |
| Fallback sem LLM (templates) | Heurístico | `WSIScreeningQuestionGenerator` | ✅ |
| Edição manual pelo recrutador | — | UI modal | ✅ |

### 4.4 Busca de Candidatos — Funil de Talentos (`/funil-de-talentos`)

**Página:** `/funil-de-talentos`  
**O que faz:** Busca híbrida (Elasticsearch + PGVector + WRF) com 6 modos, filtros avançados, preview inline, like/dislike, prompt expandido da LIA.

| Subfuncionalidade | Camada IA | Serviço/Agente | Status |
|-------------------|-----------|----------------|--------|
| Busca Natural Language | CascadedRouter → SourcingAgent | `sourcing_react_agent` (LangGraph) | ✅ |
| Busca Boolean | Parser booleano | Elasticsearch | ✅ |
| Busca por Perfil Similar | Embedding matching | PGVector + Gemini 768-dim | ✅ |
| Busca por JD | Embedding do JD | PGVector + `semantic_search_service` | ✅ |
| Busca por Arquétipos | Perfis pré-configurados | `archetypes.py` | ✅ |
| Filtros Avançados (MAP-003) | — | Elasticsearch facets | ✅ |
| WRF Dynamic K | Heurístico adaptativo | Weighted Rank Fusion | ✅ |
| LLM Job Classification | Claude LLM | Otimização de K values | ✅ |
| FairnessGuard na busca | L1 block + L2 warn | Pre-check no MainOrchestrator + `search.py` | ✅ |
| Expansão semântica de skills | Gemini embedding | `semantic_search_service` | ✅ |
| Like/Dislike feedback | Learning Loop | `learning_loop_service` | ✅ |
| Preview do candidato (4 tabs) | — | Perfil, Atividades, Arquivos, Pareceres | ✅ |
| Tabela paginada (10/vez) | — | — | ✅ |
| Pearch + Apify (enriquecimento) | Apify actors | `CandidateEnrichmentService` | ✅ (API key configurada) |

### 4.5 Kanban & Pipeline (`/jobs/[id]` tab kanban)

**Página:** `/jobs/[id]` (tab kanban)  
**O que faz:** Visualização kanban dos candidatos por estágio do processo seletivo. Drag-and-drop, aprovação em massa, SmartTransitionModal, scores inline.

| Subfuncionalidade | Camada IA | Serviço/Agente | Status |
|-------------------|-----------|----------------|--------|
| Kanban drag-and-drop | — | `KanbanService` | ✅ |
| Aprovação individual e em massa (max 100) | — | Pipeline tools | ✅ |
| SmartTransitionModal (confirmação) | — | UI component | ✅ |
| Cards com ícones de score (triagem, CV, geral) | WSI scoring | Modais de detalhe | ✅ |
| FairnessGuard na rejeição | L1 auto-check | `reject_candidate` em `candidate_tools.py` | ✅ |
| Sub-estágios customizáveis | — | Herança empresa + override por vaga | ✅ |
| Agente kanban (ações via chat) | Claude LLM | `kanban_react_agent` + sub-agentes | ✅ |
| Agente pipeline (transições) | Claude LLM | `pipeline_transition_agent` | ✅ |

### 4.6 Chat LIA Unificado (`/chat` + painel lateral)

**Página:** `/chat` (full-page) + painel lateral em qualquer página  
**O que faz:** Chat assistente SSE com reasoning progressivo, RRP cards, slash commands, menções, upload de arquivos, wizard inline, HITL cards.

| Subfuncionalidade | Camada IA | Serviço/Agente | Status |
|-------------------|-----------|----------------|--------|
| Chat SSE (transporte principal) | — | `agent_chat_sse.py` | ✅ |
| Reasoning progressivo (passos de pensamento) | StreamingCallback | `_process_langgraph` base | ✅ |
| RRP response blocks (cards estruturados) | LLM → response_blocks | `recruiter_copilot` | ✅ |
| Slash commands | — | UI component | ✅ |
| Menção de candidato/vaga (@) | — | Autocomplete UI | ✅ |
| Upload de JD (arquivo) | — | Smart file upload | ✅ |
| Wizard inline (sugestões + plan cards) | Claude LLM | `WizardSuggestionChips`, `WizardPlanFeedCard` | ✅ |
| HITL confirm cards | — | `HITLService` + `LiaFloatHitlConfirmCard` | ✅ (flag dormante) |
| Inline chat (seleção de texto + ask) | Claude LLM | `POST /inline-chat/ask` | ✅ |
| Navegação por comando LIA | Determinístico | `open_ui` tool (navigate + modal) | ✅ |
| CascadedRouter (6 tiers) | Memory → Redis → pgvector → regex → LLM cascade | `intent_router.py` | ✅ |
| Conversation memory (entity tracking) | Heurístico | `conversation_state.py` | ✅ |
| Long-term memory | LLM compression | `long_term_memory.py` | ✅ |
| Token budget por tenant | Redis counter | `check_budget` em `agent_chat_sse.py` | ✅ |

### 4.7 Projetos de Recrutamento (`/projetos`)

**Página:** `/projetos` + `/projetos/new` + `/projetos/[id]`  
**O que faz:** Agrupar vagas, candidatos e atividades num projeto de recrutamento.

| Subfuncionalidade | Camada IA | Status |
|-------------------|-----------|--------|
| Lista de projetos | — | ✅ |
| Criar projeto (wizard) | — | ✅ |
| Detalhe do projeto | — | ✅ |

### 4.8 Central de Comunicação (`/central-comunicacao`)

**Página:** `/central-comunicacao`  
**O que faz:** Histórico de comunicações (emails, WhatsApp) enviados.

| Subfuncionalidade | Camada IA | Serviço/Agente | Status |
|-------------------|-----------|----------------|--------|
| Histórico de envios | — | Communication domain | ✅ |
| Templates de email | Template Learning | `template_learning_service` | ✅ |
| A/B testing de templates | Hash-based splitting | `ab_testing_service` | ✅ |

### 4.9 Contato & Follow-up Automático

**Onde:** Disparado pelo pipeline (pós-Gate 1)  
**O que faz:** Email de contato com link para triagem web ou solicitação de WhatsApp. Follow-up automático.

| Subfuncionalidade | Camada IA | Serviço/Agente | Status |
|-------------------|-----------|----------------|--------|
| Envio de email de contato | Template + personalização LLM | `CommunicationReActAgent` + `email_service` | ✅ |
| Envio de WhatsApp | Template Meta-approved | `whatsapp_service` (Twilio) | ✅ (depende de creds prod) |
| Follow-up automático (7 dias) | Event-driven | `handlers_screening.py` | ✅ |
| Opt-out LGPD (link no email) | HMAC tokens | `communication_optout_service` | ✅ |
| A/B testing de templates | Hash-based | `ab_testing_service` (3 experimentos seed) | ✅ |
| Template learning | Após 3 vagas similares | `template_learning_service` | ✅ |

### 4.10 Ofertas & Propostas

**Onde:** Pipeline estágio "oferta"  
**O que faz:** Criar, enviar e negociar proposta com gate de aprovação gerencial.

| Subfuncionalidade | Camada IA | Serviço/Agente | Status |
|-------------------|-----------|----------------|--------|
| Criação de draft de proposta | Claude LLM | `offer_concierge_agent` | ✅ |
| Gate de aprovação gerencial (HITL) | Determinístico | `offer_service.check_can_send` | ✅ |
| Envio de proposta | Multi-canal | `send_offer` tool | ✅ |
| Portal de aceitação (candidato) | — | `/portal/proposta/[token]` | ✅ |
| Negociação | LLM | `offer_negotiation_event_repository` | ✅ |

### 4.11 Bancos de Talentos (`/bancos-de-talentos`)

**Página:** `/bancos-de-talentos`  
**O que faz:** Pools segmentados de candidatos para reuso entre vagas.

| Subfuncionalidade | Camada IA | Serviço/Agente | Status |
|-------------------|-----------|----------------|--------|
| Gestão de pools | — | `talent_pool` domain | ✅ |
| Agente talent pool (via chat) | Claude LLM | `talent_react_agent` | ✅ |
| Re-discovery via embedding | Gemini embedding | Auto-trigger em `reject_candidate` | ✅ |

### 4.12 Biblioteca LIA (`/biblioteca-lia`)

**Página:** `/biblioteca-lia`  
**O que faz:** Templates, prompts e recursos de IA.

| Subfuncionalidade | Status |
|-------------------|--------|
| Templates de comunicação | ✅ |
| Prompts reutilizáveis | ✅ |

### 4.13 Tasks (`/tasks`)

**Página:** `/tasks`  
**O que faz:** Gestão de tarefas do recrutador com automação.

| Subfuncionalidade | Camada IA | Status |
|-------------------|-----------|--------|
| Lista de tarefas | — | ✅ |
| Automação de tarefas | `automation` domain | ✅ |

---

## 5. JORNADA DO CANDIDATO — FUNCIONALIDADES

O candidato interage com a plataforma por 6 touchpoints, todos sem login (token-based):

```
Candidato recebe EMAIL
       │
       ├──→ Clica link → /triagem/[token] → TRIAGEM WSI (chat web)
       │         │
       │         ├── Perguntas de elegibilidade (eliminatórias)
       │         ├── Perguntas WSI por blocos (técnico, comportamental)
       │         ├── Voz opcional (Deepgram STT + OpenAI TTS)
       │         ├── Consent LGPD obrigatório (checkbox)
       │         └── Feedback pós-triagem
       │
       ├──→ Responde WhatsApp → TRIAGEM via WhatsApp
       │
       ├──→ Recebe ligação → TRIAGEM por VOZ (Twilio + Gemini Live)
       │
       ├──→ /portal/data-request/[token] → COLETA DE DADOS
       │         └── Upload de documentos solicitados
       │
       ├──→ /portal/proposta/[token] → PROPOSTA / OFERTA
       │         └── Aceitar, negociar ou recusar
       │
       └──→ /vagas/[slug] → PÁGINA PÚBLICA DA VAGA (job board)
```

### 5.1 Triagem WSI (Web Chat)

**Página:** `/triagem/[token]`  
**O que faz:** Entrevista estruturada conduzida pela LIA com scoring por competência.

| Subfuncionalidade | Camada IA | Serviço | Status |
|-------------------|-----------|---------|--------|
| Elegibilidade (eliminatória, antes do WSI) | Determinístico | `eligibility_phase.py` → `EligibilityVerificationService` | ✅ |
| Perguntas WSI por bloco (B2-B5) | LLM (conduz conversa) | `TriagemSessionService` (canônico) | ✅ |
| Follow-up contextual | LLM | `conversation.py` module | ✅ |
| Scoring por competência (0-100) | LLM + heurístico | `score_calculator`, `deterministic_scorer` | ✅ |
| Feedback pós-triagem | LLM | `feedback_generator` | ✅ |
| Consent LGPD (checkbox obrigatório) | — | `ConsentCheckerService.check_candidate_consent` | ✅ |
| Voice mode (microfone) | Deepgram STT + OpenAI TTS | `voice_service.py` | ✅ |
| Abandono (timeout 48h + lembretes) | Event-driven | `handlers_screening.py` | ✅ |
| FairnessGuard em cada resposta | L1 block + L2 warn | Pre-check no Orchestrator | ✅ |
| Reconsideração (2x) em elegibilidade | Determinístico + FairnessGuard | `EligibilityVerificationService` | ✅ |

### 5.2 Triagem por WhatsApp

| Subfuncionalidade | Camada IA | Status |
|-------------------|-----------|--------|
| Envio de perguntas via WhatsApp | Template Meta-approved | ✅ (depende de creds) |
| Consent via WhatsApp (AWAITING_CONSENT) | — | ✅ |
| Coleta de respostas | — | ✅ |

### 5.3 Triagem por Voz

| Subfuncionalidade | Camada IA | Serviço | Status |
|-------------------|-----------|---------|--------|
| Ligação Twilio + Gemini Live | Gemini Live Audio | `voice_core_orchestrator` | ✅ |
| Plugins de voz (WSI, data collection, studio) | Plugin architecture | `voice/plugins/` | ✅ |
| Rate limiting (100 calls/mês/tenant) | Redis counter | `data_request_voice_service` | ✅ |
| Consent LGPD hardcoded (literal legal) | — | `CONSENT_QUESTION` em cada plugin | ✅ |
| Wording per-tenant (nome/tom) | Per-tenant persona | `_build_recording_notice` | ✅ |

### 5.4 Coleta de Dados

**Página:** `/portal/data-request/[token]`  
**O que faz:** Candidato submete documentos solicitados pelo recrutador.

| Subfuncionalidade | Camada IA | Status |
|-------------------|-----------|--------|
| Portal web de upload | — | ✅ |
| Envio por email (real, não stub) | `communication_dispatcher` | ✅ |
| Envio por WhatsApp | `DataRequestWhatsAppService` | ✅ |
| Envio por voz | `DataRequestVoiceService` | ✅ |
| Multi-canal configurável | — | ⚠ Parcial (editor de config pendente) |

### 5.5 Portal de Proposta

**Página:** `/portal/proposta/[token]`  
**O que faz:** Candidato visualiza e responde à proposta de oferta.

| Subfuncionalidade | Status |
|-------------------|--------|
| Visualização da proposta | ✅ |
| Aceitar/recusar | ✅ |
| Negociação | ✅ |

### 5.6 Página Pública da Vaga

**Página:** `/vagas/[slug]`  
**O que faz:** Job board público com detalhes da vaga.

| Subfuncionalidade | Status |
|-------------------|--------|
| Detalhes da vaga | ✅ |
| Aplicação direta | ✅ (bypass Gate 1 → triagem automática) |

### 5.7 Self-Service do Candidato

| Subfuncionalidade | Camada IA | Status |
|-------------------|-----------|--------|
| Status da candidatura | — | ✅ |
| Info de entrevista | — | ✅ |
| Feedback WSI | LLM-generated | ✅ |
| Explicação de decisão | LLM | ✅ (LGPD Art. 20) |

---

## 6. ADMIN WEDOTALENT (STAFF) — FUNCIONALIDADES

**Páginas:** `/wedo-admin/*`  
**Quem acessa:** Apenas equipe interna WeDOTalent (role `wedotalent_admin`)

| Página | O que faz | Status |
|--------|-----------|--------|
| `/wedo-admin` | Dashboard administrativo | ✅ |
| `/wedo-admin/fairness` | Monitoramento de fairness cross-tenant | ✅ |
| `/wedo-admin/fairness/bias-audit` | Auditoria de viés (Four-Fifths Rule) | ✅ |
| `/wedo-admin/governanca/ai-performance` | Performance dos agentes IA | ✅ |
| `/wedo-admin/governanca/ai-transparency` | Transparência/explicabilidade da IA | ✅ |
| `/wedo-admin/governanca/audit-logs` | Visualizador de audit trail | ✅ |
| `/wedo-admin/governanca/automation-rules` | Motor de regras de automação | ✅ |
| `/wedo-admin/governanca/policy-engine` | Configuração do policy engine | ✅ |

---

## 7. AGENT STUDIO & MARKETPLACE

**Páginas:** `/agent-studio` + `/agent-studio/[id]/edit` + `/agent-studio/[id]/kpis` + `/agents/marketplace`

**O que faz:** Criar, configurar e instalar agentes IA customizados por tenant. Marketplace para compartilhar/instalar agentes.

### Estrutura do domínio (`app/domains/agent_studio/`)

| Componente | Arquivo | O que faz |
|-----------|---------|-----------|
| **Runtime** | `custom_agent_runtime.py` | Execução de agentes customizados |
| **Platform Tools** | `platform_tools_loader.py` | Carrega tools da plataforma para agentes custom |
| **Reasoning Trace** | `reasoning_trace_builder.py` | Constrói trace de reasoning para explicabilidade |
| **Marketplace** | `agent_marketplace_repository.py` | Catálogo de agentes disponíveis |
| **Versionamento** | `agent_version_snapshot_repository.py` | Snapshots de versão de agentes |
| **Digital Twin** | `digital_twin_repository.py` | Configuração de gêmeo digital |
| **Pool Assignment** | `pool_agent_assignment_repository.py` | Atribuição de agentes a pools |
| **WhatsApp Plugin** | `whatsapp_agent_plugin.py` | Agentes atuando via WhatsApp |
| **Auditoria** | `_audit_helper.py` | Audit trail de ações do studio |

| Subfuncionalidade | Status |
|-------------------|--------|
| 22+ agentes personalizados | ✅ |
| Marketplace de agentes | ✅ |
| KPIs por agente | ✅ |
| Editor de agente | ✅ |
| Voz no Agent Studio | ✅ (plugin `studio_voice_plugin`) |

---

## 8. CONFIGURAÇÕES (TENANT ADMIN)

**Página:** `/configuracoes` (SPA com routing via `?section=X&subsection=Y`)

### Mapa de seções

| Grupo | Seção | Hub/Panel | O que configura |
|-------|-------|-----------|----------------|
| **Empresa** | `minha-empresa` | MinhaEmpresaHub | Dados da empresa, missão, valores, tech stack |
| | `minha-empresa` → `learning-loops` | LearningLoopsPanel | Configuração de learning loops IA |
| | `minha-empresa` → `instrucoes-lia` | LiaFieldsConfigPanel | 34 toggles + instruções custom por campo da LIA |
| | `minha-empresa` → `contratacao` | ContratacaoHub | Políticas de contratação |
| **Processo** | (pipeline) | RecruitmentPipelineTab | Estágios do processo seletivo (drag-and-drop) |
| | (screening) | RecruitmentScreeningTab | Configuração de triagem |
| | (journey) | JourneyConfig | Jornada do candidato |
| **IA** | `lia-personalizacao` | LiaPersonalizacaoHub | Persona da IA (nome, tom), field toggles |
| | → AI Persona | AiPersonaPanel | Nome (2-20 chars) + tom (6 canônicos) per-tenant |
| **Comunicação** | `comunicacao-alertas` | CommunicationHub | Templates, canais |
| | → Alertas | AlertPreferencesPanel | Regras de alerta, frequência |
| | → Data Channel | DataChannelPanel | Canais de coleta de dados |
| **Usuários** | `usuarios-departamentos` | UsuariosDepartamentosHub | Gestão de usuários, PII visibility matrix |
| | → PII Visibility | PiiFieldVisibilityMatrix | Visibilidade por campo por papel |
| | → Role Defaults | PiiVisibilityRoleDefaults | Defaults de visibilidade por role |
| **Integrações** | `integrations` | IntegrationsHub | Catálogo de integrações, webhooks |
| | → Webhooks | WebhooksPanel | Configuração de webhooks |
| **Compliance** | `fairness-compliance` | FairnessComplianceHub | Fairness, LGPD, consent, audit |
| | → `fairness` | — | Dashboard de fairness |
| | → `studio` | StudioCompliancePanel | Compliance do Agent Studio |
| | → `lgpd-candidatos` | — | LGPD de candidatos |
| | → `consent` | — | Gestão de consentimento |
| | → `audit-summary` | — | Resumo de auditoria |
| **Consumo** | `consumo` | ConsumoHub | Créditos IA, token budget |
| **Workforce** | — | WorkforceHub | Planejamento de força de trabalho |

### Padrões canônicos de Settings

- Todo dado de servidor via `useQuery` (React Query v5), NUNCA `useState + fetch`
- Query keys canônicas em `SETTINGS_QUERY_KEYS`
- Broadcast via `dispatchSettingsUpdate`
- Hubs usam `HubHeader`, `HubLoadingState`, `HubErrorState` de `_shared/`
- Dynamic imports com `<Suspense fallback={<HubLoadingState/>}>`

---

## 9. MAPA COMPLETO DE DOMÍNIOS IA

### 37 domínios em `lia-agent-system/app/domains/`

| Domínio | Camada | Descrição | Tools |
|---------|--------|-----------|-------|
| **ai** | Core IA | Serviços de IA compartilhados (context aggregator) | — |
| **analytics** | Análise | Métricas, predictive analytics, calibração | 2 |
| **agent_studio** | Agentes Custom | Runtime, marketplace, digital twin, versionamento | 2 |
| **ats_integration** | Integração | Sync com ATS externo (Gupy, Pandapé) | 2 |
| **automation** | Automação | Workflows automatizados, event handlers | 2 |
| **billing** | Infra | Faturamento | — |
| **candidates** | Core | CRUD de candidatos, enriquecimento | — |
| **candidate_self_service** | Candidato | Portal self-service do candidato | 1 |
| **communication** | Comunicação | Email, WhatsApp, templates, dispatcher | 2 |
| **company** | Core | Dados da empresa | — |
| **company_settings** | Config | Configurações do tenant | 3 |
| **compliance** | Compliance | Serviços de compliance | — |
| **consent** | LGPD | Gestão de consentimento | — |
| **credits** | Infra | Créditos IA / token budget | — |
| **cv_screening** | Core IA | WSI, triagem, scoring, perguntas, feedback | 4 |
| **digital_twin** | Agentes | Gêmeo digital de agente | — |
| **hiring_policy** | Políticas | Políticas de contratação por empresa/setor | 2 |
| **integrations_hub** | Integração | Hub de integrações | — |
| **interview_intelligence** | Entrevista | Análise inteligente de entrevistas | — |
| **interview_scheduling** | Agendamento | Agendamento de entrevistas (ICS, Teams, self-scheduling) | 2 |
| **job_creation** | Core | Grafo LangGraph + wizard orchestrator de criação | 2 |
| **job_management** | Core | Gestão de vagas, JD generator | 5 |
| **lgpd** | Compliance | Erasure, audit, consent checker, DSR export, incident response, drift alert, cleanup | — |
| **modules** | Infra | Módulos compartilhados | — |
| **offer** | Propostas | Concierge de ofertas com HITL gate | 1 |
| **persona** | IA Config | Persona per-tenant (nome + tom) com validators | — |
| **pipeline** | Core | Pipeline de candidatos (kanban backend), transições | 7 |
| **policy** | Políticas | Motor de regras e sector rules | 1 |
| **recruiter_assistant** | Core IA | Agente federado principal + sub-agentes | 9 |
| **recruitment** | Core | Processo de recrutamento | — |
| **recruitment_campaign** | Campanhas | Gestão de campanhas de recrutamento | — |
| **sourcing** | Core IA | Busca e sourcing (10 sub-agentes especializados) | 10+ |
| **talent_intelligence** | Inteligência | Inteligência de mercado de trabalho | — |
| **talent_pool** | Pools | Gestão de pools de talento | — |
| **voice** | Voz | Multi-canal voz (Twilio, Gemini Live), 3 plugins | — |
| **workforce** | RH | Planejamento de força de trabalho | 1 |

---

## 10. CAMADAS DE COMPLIANCE

### 8+ camadas ativas

| Camada | Arquivo principal | LOC | Referências | Status |
|--------|------------------|-----|------------|--------|
| **FairnessGuard** (L1 block + L2 warn + L3 semantic) | `app/shared/compliance/fairness_guard.py` | 1.248 | 191 refs em `app/api/` | ✅ LIVE, 13+ surfaces |
| **PII Masking** (3 camadas: outbound/LLM/logs) | `app/shared/pii_masking.py` | 60 | Global | ✅ LIVE |
| **Audit Service** (SOX-compliant) | `app/shared/compliance/audit_service.py` | 1.071 | 678 refs | ✅ LIVE |
| **LGPD** (7 serviços) | `app/domains/lgpd/` | — | 8 endpoints API | ✅ LIVE |
| **HITL Gate** (confirmação humana) | `app/api/v1/hitl/` + `app/services/hitl/` | 7 files | 7 tools gated | ✅ (flag dormante) |
| **Tenant Guard** (multi-tenancy fail-closed) | `app/shared/tenant_guard.py` | — | — | ✅ LIVE |
| **RuntimeContext** (ContextVar enforcement) | `app/shared/runtime_context.py` | — | — | ✅ LIVE |
| **Rate Limiting** | `RateLimitMiddleware` em `main.py` | — | Redis sliding window | ✅ LIVE |

### FairnessGuard — Surfaces wired (Jun/2026)

| Surface | Arquivo | Shape |
|---------|---------|-------|
| Chat LIA (SSE) | `agent_chat_sse.py` | HTTP 400 + `log_check()` |
| Chat LIA (WS legado) | `chat.py` | HTTP 400 |
| Busca candidatos (Funil) | `candidate_search/search.py` | HTTP 400 `{fairness_blocked}` |
| Arquétipos de busca | `candidate_search/archetypes.py` | HTTP 400 |
| Motivo de rejeição | `candidates_crud.py` | HTTP 400 |
| Salvar JD/vaga | `job_vacancies/_shared.py` | HTTP 422 |
| Importar JD | `jd_import.py` | Aviso/bloqueio |
| Parecer entrevista (IA) | `interview_notes.py` | Texto substituído |
| Bulk actions | `bulk_actions.py` | Bloqueio |
| Agente Sourcing | `sourcing_react_agent.py` | educational_message |
| Hiring Policy agent | `hiring_policy.py` | HTTP 400 |
| Pipeline Orchestrator | `pipeline_orchestrator.py` | HTTP 400 |
| Task Planner agent | `task_planner.py` | HTTP 400 |

### LGPD — 7 serviços no domínio `lgpd/`

| Serviço | O que faz |
|---------|-----------|
| `consent_checker` | Verifica consentimento antes de processar |
| `granular_consent` | Consentimento granular por finalidade |
| `dsr_export` | Data Subject Request — exportação de dados |
| `incident_response` | Resposta a incidentes de dados |
| `drift_alert` | Alerta de drift de consentimento |
| `cleanup` | Limpeza de dados expirados |
| `lgpd_compliance` | Compliance geral LGPD |

---

## 11. CAMADAS DE INTELIGÊNCIA

### 18+ módulos em 3 diretórios

#### `app/shared/learning/` (9 módulos)

| Módulo | O que faz | Status |
|--------|-----------|--------|
| `learning_loop_service` | Captura silenciosa de accept/modify/reject | ✅ |
| `ab_testing_service` | A/B testing hash-based (z-score, p-value) | ✅ |
| `template_learning_service` | Aprende templates após 3 vagas similares | ✅ |
| `learning_snapshot_service` | Snapshots pré-learning para rollback | ✅ |
| `correction_capture` | Captura correções do recrutador | ✅ |
| `feedback_writer` | Persiste feedback estruturado | ✅ |
| `finetuning_export` | Exporta dados para fine-tuning de modelos | ✅ |
| `implicit_feedback` | Feedback implícito (ações inferidas) | ✅ |
| `golden_curation` | Curadoria de exemplos "golden" | ✅ |

#### `app/shared/intelligence/` (6 módulos)

| Módulo | O que faz | Status |
|--------|-----------|--------|
| `semantic_search_service` | Busca semântica (Gemini 768-dim, Redis cache) | ✅ |
| `embedding_service` | Geração de embeddings (Gemini text-embedding-004) | ✅ |
| `smart_extractor` | Extração inteligente de dados | ✅ |
| `param_patterns` | Padrões de parâmetros para otimização | ✅ |
| `chunking/` | Chunking inteligente para RAG | ✅ |
| `ab_testing/` | A/B testing (diretório com sub-módulos) | ✅ |

#### `app/shared/memory/` (3 módulos)

| Módulo | O que faz | Status |
|--------|-----------|--------|
| `conversation_state` | Estado efêmero de sessão (entity tracking, pronoun resolution) | ✅ |
| `candidate_list_store` | Armazena listas de candidatos em sessão | ✅ |
| `reference_resolver` | Resolve referências ("ele", "essa vaga") | ✅ |

#### Outros módulos de inteligência

| Módulo | Arquivo | Status |
|--------|---------|--------|
| Routing Adaptativo | `app/services/routing_learning_service.py` | ✅ |
| Calibration | `app/services/calibration_service.py` | ✅ |
| Score Normalization | `app/domains/cv_screening/services/score_normalization_service.py` | ✅ |
| Predictive Analytics | `app/services/ml/outcome_predictor.py` + `app/api/v1/predictive_analytics.py` | ✅ |
| Model Drift | `app/services/model_drift_service.py` | ✅ |
| Long-Term Memory | `libs/agents-core/lia_agents_core/long_term_memory.py` | ✅ |
| Voice Analysis | `app/services/voice_service.py` (Deepgram STT + OpenAI TTS) | ✅ |

---

## 12. CANAIS DE COMUNICAÇÃO

| Canal | Provedor | Serviço | Uso principal |
|-------|---------|---------|---------------|
| **Email** | Mailgun (primary) + Resend (fallback) | `email_service.py` | Contato, follow-up, feedback, convites |
| **WhatsApp** | Twilio + Meta | `whatsapp_service.py`, `whatsapp_meta_service.py`, `whatsapp_twilio_service.py` | Triagem, contato, coleta de dados |
| **Chat Web** | SSE (FastAPI) | `TriagemSessionService` + `agent_chat_sse.py` | Triagem WSI (candidato), assistente LIA (recrutador) |
| **Voz** | Twilio + Gemini Live | `twilio_voice_service.py`, `gemini_live_audio_service.py` | Triagem por voz, coleta de dados por voz |
| **Teams** | Microsoft Graph API | `teams_service.py`, `teams_bot.py` | Notificações, dashboard embeddado, canal de decisão |
| **Portal Web** | Next.js | `/portal/data-request/[token]`, `/portal/proposta/[token]` | Self-service candidato |

**Seleção de canal:** `CandidateChannelSelector` em `transition_dispatch_service.py` — determinístico, verifica consent LGPD + opt-out por canal.

---

## 13. INTEGRAÇÃO MICROSOFT TEAMS

**Páginas:** `/teams-tab/*` (7 páginas)  
**O que faz:** Embeda funcionalidades da plataforma dentro do Microsoft Teams.

| Tab Teams | Funcionalidade | Página FE |
|-----------|---------------|-----------|
| Dashboard | Resumo geral | `/teams-tab/dashboard` |
| Recrutar | Visão global de vagas | `/teams-tab/recrutar` |
| Vagas | Lista de vagas | `/teams-tab/vagas` |
| Candidatos | Busca de candidatos | `/teams-tab/candidatos` |
| Funil | Funil de talentos | `/teams-tab/funil-de-talentos` |
| Pipeline | Pipeline de candidatos | `/teams-tab/pipeline` |
| Decidir | Aprovações/decisões | `/teams-tab/decidir` |

**Backend:** `teams_service.py`, `teams_bot.py`, `teams_orchestrator_bridge.py`, `teams_proactivity_engine.py`, `teams_tab_trigger.py`.

---

## 14. FEATURE FLAGS & CAMINHOS ATIVOS

| Flag | Valor atual | O que controla |
|------|------------|----------------|
| `LIA_FEDERATED_PRIMARY` | `true` | Agente federado como caminho principal do chat |
| `LIA_WIZARD_ORCHESTRATOR` | `1` | Wizard como caminho de criação de vaga |
| `LIA_WIZARD_FALLBACK_LLM_DISABLED` | `1` | Desabilita fallback LLM no wizard |
| `LIA_WIZARD_MIN_JD_QUALITY` | `0` | Quality gate mínimo desabilitado |
| `LIA_HITL_GATE` | comentado (off) | Gate HITL dormante |
| `LIA_BUBBLE_VIA_SUPERVISOR` | não definido | Supervisor path dormante |
| `RAILS_ENABLED` | `false` (sem `RAILS_API_URL`) | Integração Rails desativada |
| `APP_ENV` | `development` | Ambiente dev (token budget ilimitado) |

---

## 15. GAPS REAIS & PRÓXIMOS PASSOS

### Gaps que bloqueiam produção

| # | Gap | Impacto | Prioridade |
|---|-----|---------|-----------|
| G1 | **ATS real desconectado** — `RAILS_API_URL` ausente, nós LangGraph são tombstones | Vagas só por criação manual, sem sync com ATS cliente | 🔴 P0 |
| G2 | **Credenciais de produção** — Twilio WhatsApp, Resend/SendGrid, Teams Graph API | Comunicação multi-canal funciona apenas em dev mode | 🔴 P0 |
| G3 | **Validação live E2E** — Muitas features commitadas sem validação live completa | Risco de peças que passam em teste mas não conectam ponta-a-ponta | 🟡 P1 |

### Gaps funcionais

| # | Gap | Impacto | Prioridade |
|---|-----|---------|-----------|
| G4 | **HITL gate dormante** — `LIA_HITL_GATE` comentado, 7 tools prontas mas desativadas | Ações sensíveis (close_job, send_email, reject) sem confirmação humana | 🟡 P1 |
| G5 | **Bell notification in-app** — Teams e Email ativos; falta notificação in-app | Recrutador não vê alertas na plataforma sem acessar Teams/email | 🟡 P1 |
| G6 | **Predictive Analytics UI** — Backend ativo com endpoints; falta UI na página de vagas | Recrutador não vê time-to-fill, salary prediction | 🟢 P2 |
| G7 | **Bias Audit Dashboard** — FairnessGuard coleta dados; falta relatório Four-Fifths Rule | Compliance visual para RH/legal | 🟢 P2 |
| G8 | **EU AI Act Risk Classification** — Mencionado nos docs; sem classificação por agente | Compliance futuro (disclosure obrigatório) | 🟢 P2 |
| G9 | **Coleta de dados multi-canal** — Editor de config por vaga pendente | Recrutador não customiza canais de coleta por vaga | 🟢 P2 |

### Diferenças entre doc anterior e realidade

| O que o doc v6.3 dizia | Realidade Jun/2026 |
|------------------------|-------------------|
| `policy_engine_service.py` ATIVO | **Não existe** como arquivo. Funcionalidade pode estar distribuída |
| 6 camadas de compliance | 8+ camadas (adicionados HITL, TenantGuard, RuntimeContext) |
| 11 camadas de inteligência | 18+ módulos |
| 8 agentes (Ag.0-Ag.8) | 35+ classes de agente com sub-agentes |
| Fluxo linear E1-E9 | Federado + wizard + supervisor (3 caminhos) |
| Audit Trail "PRECISA ATIVAR" em vários pontos | 678 referências — significativamente mais ativo |
| Sem menção a Agent Studio | Vertical completo (marketplace, runtime, KPIs, digital twin) |
| Sem menção a Voice | 38 arquivos, 3 plugins, 3 providers |
| Sem menção a Offer/Proposta | Domínio completo com concierge agent + HITL |
| Sem menção a Persona per-tenant | Implementado (nome + tom + validator) |

---

## 16. ARQUIVOS DE REFERÊNCIA

### Backend Core
| Arquivo | Responsabilidade |
|---------|-----------------|
| `app/orchestrator/execution/main_orchestrator.py` | Orquestrador supervisor (dormante) |
| `app/domains/recruiter_assistant/agents/recruiter_copilot_react_agent.py` | Agente federado (LIVE) |
| `app/domains/job_creation/orchestrator/wizard_orchestrator.py` | Wizard de criação (LIVE) |
| `app/orchestrator/intent_router.py` | CascadedRouter (6 tiers) |
| `app/shared/agents/agents_registry.yaml` | Registry de 12 agentes |
| `app/shared/agents/agent_types.py` | Enum AgentType (15 membros) |

### Compliance
| Arquivo | Responsabilidade |
|---------|-----------------|
| `app/shared/compliance/fairness_guard.py` | FairnessGuard (1.248 LOC, 3 camadas) |
| `app/shared/pii_masking.py` | PII Masking (3 camadas) |
| `app/shared/compliance/audit_service.py` | Audit Trail (1.071 LOC) |
| `app/domains/lgpd/` | LGPD (7 serviços) |
| `app/services/hitl/` | HITL gate (7 arquivos) |
| `app/shared/tenant_guard.py` | Multi-tenancy fail-closed |
| `app/shared/runtime_context.py` | RuntimeContext typed |

### Inteligência
| Arquivo | Responsabilidade |
|---------|-----------------|
| `app/shared/learning/learning_loop_service.py` | Learning Loop |
| `app/shared/learning/ab_testing_service.py` | A/B Testing |
| `app/services/routing_learning_service.py` | Routing Adaptativo |
| `app/shared/learning/template_learning_service.py` | Template Learning |
| `app/services/calibration_service.py` | Calibration |
| `app/domains/cv_screening/services/score_normalization_service.py` | Score Normalization |
| `app/services/ml/outcome_predictor.py` | Predictive Analytics |
| `app/services/model_drift_service.py` | Model Drift (4 dimensões) |
| `app/shared/memory/conversation_state.py` | Conversation Memory |
| `app/shared/intelligence/semantic_search_service.py` | Semantic Search (Gemini 768-dim) |
| `app/services/voice_service.py` | Voice Analysis (Deepgram + OpenAI TTS) |
| `app/shared/intelligence/embedding_service.py` | Embedding Service (Gemini) |
| `libs/agents-core/lia_agents_core/long_term_memory.py` | Long-Term Memory |

### Comunicação
| Arquivo | Responsabilidade |
|---------|-----------------|
| `app/domains/communication/services/email_service.py` | Email (Mailgun/Resend) |
| `app/domains/communication/services/whatsapp_service.py` | WhatsApp (Twilio) |
| `app/domains/communication/services/whatsapp_meta_service.py` | WhatsApp (Meta) |
| `app/domains/voice/services/` | Voz (Gemini Live, Twilio) |
| `app/domains/communication/services/transition_dispatch_service.py` | Dispatcher multicanal |
| `app/domains/interview_scheduling/services/scheduling_service.py` | Agendamento (ICS + Teams) |

### Frontend
| Arquivo/Diretório | Responsabilidade |
|-------------------|-----------------|
| `src/app/[locale]/(dashboard)/` | Páginas do recruiter (20 rotas) |
| `src/app/[locale]/triagem/` | Triagem WSI (candidato) |
| `src/app/[locale]/(staff)/wedo-admin/` | Admin WeDOTalent (8 páginas) |
| `src/app/[locale]/teams-tab/` | Integração Teams (7 páginas) |
| `src/components/unified-chat/` | Chat unificado SSE |
| `src/components/lia-float/` | Painel flutuante LIA |
| `src/components/settings/` | Configurações (60+ componentes) |
| `src/hooks/settings/useSettingsBroadcast.ts` | Query keys + broadcast canônicos |

---

> **Nota de auditoria:** Este documento foi gerado por auditoria automatizada do código em `feat/benefits-prv-canonical` no Replit (`replit-wedo-0405`) em 17/06/2026. Paths e contagens refletem o estado do código nessa data. Funcionalidades marcadas como ✅ significam que o código existe e passa testes; **não** significa necessariamente validação live completa ponta-a-ponta.
