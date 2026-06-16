# Análise Comparativa de Arquiteturas — Plataforma LIA

**Data**: 12 de Fevereiro de 2026  
**Versão**: 1.0  
**Autores**: Equipe WeDoTalent  
**Status**: Documento de Referência para Alinhamento entre Protótipo e Produção

---

## Índice

1. [Introdução e Objetivo](#1-introdução-e-objetivo)
2. [Visão Geral das Duas Arquiteturas](#2-visão-geral-das-duas-arquiteturas)
3. [Comparação de Infraestrutura (10 Eixos)](#3-comparação-de-infraestrutura-10-eixos)
4. [Cobertura do Ciclo de Recrutamento (9 Fases)](#4-cobertura-do-ciclo-de-recrutamento-9-fases)
5. [Inventário Detalhado — Arquitetura A (Protótipo Replit)](#5-inventário-detalhado--arquitetura-a-protótipo-replit)
6. [Inventário Detalhado — Arquitetura B (Produção)](#6-inventário-detalhado--arquitetura-b-produção)
7. [Análise de Gap: Agentes e Domínios de Recrutamento](#7-análise-de-gap-agentes-e-domínios-de-recrutamento)
8. [Análise de Gap: Camadas Transversais](#8-análise-de-gap-camadas-transversais)
9. [Projeção de Domínios Faltantes para Produção](#9-projeção-de-domínios-faltantes-para-produção)
10. [Projeção de Camadas Transversais Faltantes para Produção](#10-projeção-de-camadas-transversais-faltantes-para-produção)
11. [Estimativa Consolidada de Esforço](#11-estimativa-consolidada-de-esforço)
12. [Recomendação Estratégica](#12-recomendação-estratégica) (inclui Integração de Dados e SLOs)
13. [Requisitos de Desenvolvimento para MVP Alpha 1](#13-requisitos-de-desenvolvimento-para-mvp-alpha-1)
14. [Plano de Ajustes no Protótipo (A) para Alinhar com Arquitetura B](#14-plano-de-ajustes-no-protótipo-a-para-alinhar-com-arquitetura-b)
15. [Mapa de Portabilidade: O que a Produção Pode Aproveitar do Protótipo](#15-mapa-de-portabilidade-o-que-a-produção-pode-aproveitar-do-protótipo)
16. [Plano Detalhado e Faseado de Ajustes no Protótipo (Replit)](#16-plano-detalhado-e-faseado-de-ajustes-no-protótipo-replit)
17. [Análise de Aproveitamento V5 — O Que o Protótipo Replit Entrega para a Produção](#17-análise-de-aproveitamento-v5)
18. [Guia Consolidado de Aproveitamento — Visão Completa por Camada](#18-guia-consolidado-de-aproveitamento)
19. [Guia de Transferência Tecnológica para o Time de Produção](#19-guia-de-transferência-tecnológica-para-o-time-de-produção)
20. [Inventário Detalhado de Código por Camada](#20-inventário-detalhado-de-código-por-camada)
21. [Diagrama de Dependências entre Camadas](#21-diagrama-de-dependências-entre-camadas)
22. [Cobertura de Testes Atualizada](#22-cobertura-de-testes-atualizada)
23. [Checklist de Portabilidade](#23-checklist-de-portabilidade)
24. [Comandos de Verificação](#24-comandos-de-verificação)
25. [Resumo Quantitativo](#25-resumo-quantitativo)
26. [Glossário](#26-glossário)

---

## 1. Introdução e Objetivo

Este documento consolida a análise comparativa entre as duas arquiteturas da Plataforma LIA:

- **Arquitetura A** (Protótipo Replit): implementação funcional completa que serve como referência comportamental para a equipe de produção. Cobre o ciclo de recrutamento de ponta a ponta com 13 agentes especializados (19.117 linhas verificadas via `wc -l`) e ~21 serviços transversais documentados nesta análise (learning, compliance, governança, ML, calibração, resiliência).

- **Arquitetura B** (Produção): sistema domain-driven construído com LangGraph + Gemini, com infraestrutura robusta (RabbitMQ, Celery, filas priorizadas) mas cobertura funcional concentrada em 2 domínios (sourcing de perfis e avaliação de entrevistas).

**Objetivo**: Fornecer à equipe de produção um mapa completo do que já existe como referência funcional, identificar gaps, e projetar o esforço necessário para cobrir o ciclo de recrutamento completo na Arquitetura B.

### Metodologia e Fontes

| Fonte | Descrição |
|-------|-----------|
| Contagem de linhas (A) | `wc -l` executado sobre os arquivos do repositório `lia-agent-system/` |
| Contagem de capabilities (A) | Grep sobre atributos `description=` nos agentes especializados |
| Análise da Produção (B) | Documento `ARCHITECTURE_1770889940184.md` fornecido pela equipe de produção (610 linhas, datado 10/02/2026) |
| Percentuais de roteamento (B) | Declarados no documento da Produção: "~80% fast routing" (Seção RouterAgent) |
| Estimativas de esforço | Baseadas na complexidade dos equivalentes na Arquitetura A, com fator de reuso ~30–40% (infraestrutura B já existente) |

> **Nota sobre estimativas**: As projeções de esforço são indicativas e assumem 1 dev sênior por componente. Não substituem um planejamento detalhado com a equipe de produção. As linhas de código servem como proxy de complexidade, não como meta.

---

## 2. Visão Geral das Duas Arquiteturas

### 2.1. Arquitetura A — Protótipo Replit

```
┌──────────────────────────────────────────────────────────────────────┐
│  FRONTEND (Next.js + React + TypeScript + Tailwind)                  │
│  Páginas: Vagas, Candidatos, Kanban, Wizard, Chat LIA, Dashboard    │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ REST API
┌───────────────────────────────▼──────────────────────────────────────┐
│  BACKEND (Python + FastAPI)                                          │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  ORQUESTRADOR CENTRAL                                           │ │
│  │  Orchestrator + StateManager + IntentClassifier + ToolRegistry  │ │
│  └──────────────────────────────┬──────────────────────────────────┘ │
│                                 │                                    │
│  ┌──────────────────────────────▼──────────────────────────────────┐ │
│  │  13 AGENTES ESPECIALIZADOS                                      │ │
│  │  JobIntake │ Sourcing │ TriagemCV │ Entrevistador │ AvaliadorWSI │ │
│  │  Scheduling │ AnalistaFeedback │ RecruiterAssistant │ TaskPlanner│ │
│  │  IntegradorATS │ Analytics │ Screening │ Communication          │ │
│  └──────────────────────────────┬──────────────────────────────────┘ │
│                                 │                                    │
│  ┌──────────────────────────────▼──────────────────────────────────┐ │
│  │  CAMADAS TRANSVERSAIS (~21 serviços-chave analisados)            │ │
│  │  Learning Loop │ ML/Predição │ Compliance (LGPD/SOX/EU AI Act) │ │
│  │  Governança IA │ Calibração │ Pattern Detection │ Feature Flags│ │
│  └─────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

**Características-chave:**
- Cobertura completa do ciclo de recrutamento (9/9 fases)
- 13 agentes especializados (19.117 linhas — verificado via `wc -l`)
- ~21 serviços transversais analisados neste documento (de um total de ~80 arquivos em `services/`)
- Comunicação síncrona (REST)
- Orquestrador central (ponto único)
- Roteamento sempre via LLM (intent classifier)

### 2.2. Arquitetura B — Produção

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐
│ Rails App   │────▶│  RabbitMQ    │────▶│ Workers          │
│ (ATS)       │◀────│              │◀────│ ├── Main Worker   │
└─────────────┘     └──────────────┘     │ ├── Sourcing Disp │
                                         │ └── Eval Worker   │
┌─────────────┐     ┌──────────────┐     └──────────────────┘
│ PostgreSQL  │     │ Redis        │           │
│ ├── Memory  │     │ (Celery      │           │
│ ├── pgvector│     │  backend)    │           ▼
│ └── pg_trgm │     └──────────────┘     ┌──────────────────┐
└─────────────┘                          │ Google Gemini API │
                                         └──────────────────┘
```

**Características-chave:**
- 2 domínios implementados: `sourced_profile_sourcing` e `evaluation`
- Infraestrutura robusta (RabbitMQ + Celery com filas priorizadas)
- Domain-driven design com `DomainRegistry` + `@register_domain`
- Roteamento cascateado: 80% fast routing (keywords) + 15% memory + 5% LLM
- FairnessGuard + FactChecker para compliance básico
- Preparada para escalar com novos domínios

---

## 3. Comparação de Infraestrutura (10 Eixos)

| Eixo | Arquitetura A (Protótipo) | Arquitetura B (Produção) | Vantagem |
|------|--------------------------|--------------------------|:--------:|
| **Roteamento** | Sempre via LLM (IntentClassifier) | Cascata: keywords 80% → memory 15% → LLM 5% | **B** |
| **Comunicação** | REST síncrono | RabbitMQ + Celery assíncrono | **B** |
| **Escalabilidade** | Single-process FastAPI | Workers distribuídos com filas priorizadas | **B** |
| **Modularidade** | Orquestrador central (SPOF) | DomainRegistry com domínios independentes | **B** |
| **Performance** | ~1-3s por query (sempre LLM) | ~300ms (fast), ~1-2s (LLM) | **B** |
| **Compliance** | 3 pilares completos (LGPD/SOX/EU AI Act) | FairnessGuard + FactChecker apenas | **A** |
| **Aprendizagem** | Learning loop, patterns, ML preditivo | Inexistente | **A** |
| **Cobertura funcional** | 9/9 fases do recrutamento | 2.5/9 fases | **A** |
| **Governança de IA** | Monitoring, XAI, observability, audit | Logging básico | **A** |
| **Resiliência** | Circuit breaker + feature flags | Retry + filas (conceitual) | **Empate** |

**Conclusão**: A Arquitetura B tem infraestrutura técnica superior. A Arquitetura A tem cobertura funcional e camadas transversais muito mais completas. São complementares.

---

## 4. Cobertura do Ciclo de Recrutamento (9 Fases)

O ciclo completo de recrutamento que a plataforma precisa cobrir:

```
  ① Criar Vaga    ② Sourcing    ③ Triagem CV    ④ Entrevista
       │               │              │               │
       ▼               ▼              ▼               ▼
  ⑤ Avaliação    ⑥ Pipeline    ⑦ Agendamento    ⑧ Comunicação
       │                                              │
       ▼                                              ▼
                    ⑨ Parecer/Feedback
```

### Cobertura por Arquitetura

| Fase | Descrição | A (Protótipo) | B (Produção) | Gap |
|:----:|-----------|:-------------:|:------------:|:---:|
| ① | Criação e gestão de vagas (wizard conversacional, JD, campos) | ✅ Completo | ❌ Inexistente | Crítico |
| ② | Sourcing de candidatos (busca, filtros, comparação, analytics) | ✅ Completo | ✅ Completo | — |
| ③ | Triagem curricular (parse CV, score, red flags, cutoff) | ✅ Completo | ❌ Inexistente | Crítico |
| ④ | Condução de entrevistas (perguntas adaptativas, voz, WhatsApp) | ✅ Completo | ⚠️ Parcial* | Significativo |
| ⑤ | Avaliação WSI (Bloom, Dreyfus, Big Five, score científico) | ✅ Completo | ⚠️ Parcial* | Significativo |
| ⑥ | Pipeline/Kanban (mover candidatos, gates, bulk actions) | ✅ Completo | ⚠️ Parcial* | Significativo |
| ⑦ | Agendamento (Microsoft Graph, slots, lembretes, conflitos) | ✅ Completo | ❌ Inexistente | Importante |
| ⑧ | Comunicação (email, WhatsApp, SMS, Teams, templates) | ✅ Completo | ❌ Inexistente | Importante |
| ⑨ | Parecer e feedback (relatórios, KPIs, feedback candidato) | ✅ Completo | ❌ Inexistente | Importante |

*Notas sobre cobertura parcial:
- **④ Entrevista**: B avalia respostas (scoring), mas não conduz a entrevista (não inicia, não faz perguntas adaptativas, não transcreve áudio)
- **⑤ Avaliação**: B tem scoring básico via LLM, mas não implementa a metodologia WSI (Bloom/Dreyfus/Big Five/CBI)
- **⑥ Pipeline**: B faz convert/apply no contexto sourcing (ActionAgent), mas não gerencia o pipeline de etapas como um todo

### Resumo Visual

```
COBERTURA POR FASE:

Fase:   ①    ②    ③    ④    ⑤    ⑥    ⑦    ⑧    ⑨
      Vaga  Src  Tri  Ent  Ava  Pip  Age  Com  Par
  A:  ✅   ✅   ✅   ✅   ✅   ✅   ✅   ✅   ✅   → 9/9
  B:  ❌   ✅   ❌   ⚠️   ⚠️   ⚠️   ❌   ❌   ❌   → ~2.5/9
```

---

## 5. Inventário Detalhado — Arquitetura A (Protótipo Replit)

### 5.1. Agentes Especializados (19.117 linhas total)

| Agente | Linhas | Capabilities | Fase(s) | Descrição |
|--------|:------:|:------------:|:-------:|-----------|
| **JobIntakeAgent** | 4.132 | 7 | ① | Wizard conversacional de criação de vagas. Extração de JD, campos estruturados, geração de requisitos, health check de vaga |
| **RecruiterAssistantAgent** | 2.551 | 20+ | ①⑥⑨ | Assistente pessoal do recrutador. Briefing diário, tarefas pendentes, alertas proativos, insights de busca, gestão de candidatos |
| **AnalistaFeedbackAgent** | 2.068 | 20+ | ⑧⑨ | Hub de comunicação e analytics. Email, WhatsApp, SMS, Teams, KPIs, funil, anomalias, previsões, templates |
| **SourcingAgent** | 1.881 | 12 | ② | Busca de candidatos (local + global), CV parsing, match scoring, pipeline automatizado, boolean search, sugestões proativas |
| **AvaliadorWSIAgent** | 1.596 | 9 | ⑤ | Avaliação WSI completa. Bloom (6 níveis), Dreyfus (5 níveis), Big Five, validação CBI, parecer, comparação, calibração |
| **SchedulingAgent** | 1.512 | 10 | ⑦ | Agendamento via Microsoft Graph. Slots, reagendamento, cancelamento, lembretes, conflitos, auto-agendamento |
| **TriagemCurricularAgent** | 1.384 | 9 | ③ | Triagem de CVs. Parse, score vs requisitos, batch screening, WSI inicial, ranking, cutoff dinâmico, red flags, elegibilidade |
| **EntrevistadorAgent** | 1.117 | 9 | ④ | Condução de entrevistas WSI. Perguntas adaptativas, follow-up, transcrição, análise de voz/confiança, detecção de evasão |
| **TaskPlannerAgent** | 821 | — | ①⑥ | Planejamento de tarefas e decomposição de ações complexas |
| **IntegradorATSAgent** | 704 | 9 | ②⑥ | Integração com ATS externos (Gupy, Pandapé). Sync candidatos/vagas, import/export, duplicatas, LGPD |
| **AnalyticsAgent** | 465 | — | ⑨ | Analytics e métricas de recrutamento |
| **ScreeningAgent** | 443 | — | ③ | Screening complementar de candidatos |
| **CommunicationAgent** | 390 | — | ⑧ | Comunicação multi-canal complementar |

### 5.2. Orquestradores e Assistentes de Contexto

| Componente | Arquivo | Contexto de Uso |
|------------|---------|-----------------|
| **Orchestrator Central** | `orchestrator/orchestrator.py` | Orquestração geral entre agentes |
| **StateManager** | `orchestrator/state_manager.py` | Gerenciamento de estado conversacional |
| **WizardOrchestratorService** | `services/wizard_orchestrator_service.py` | Orquestração do Job Wizard (conversa guiada) |
| **KanbanAssistantService** | `services/kanban_assistant_service.py` | Assistente do Kanban/Pipeline |
| **PipelineChatOrchestrator** | `api/v1/orchestrated_pipeline_chat.py` | Chat contextualizado dentro do pipeline |
| **LIA Assistant** | `api/v1/lia_assistant.py` | Prompt expandido ao lado da tabela de vagas |
| **WizardSmartOrchestrator** | `api/v1/wizard_smart_orchestrator.py` | JobWizardGraph com 6 nós LLM |

### 5.3. Camadas Transversais

Detalhadas na [Seção 8](#8-análise-de-gap-camadas-transversais).

---

## 6. Inventário Detalhado — Arquitetura B (Produção)

### 6.1. Domínios Implementados

#### Domínio: `sourced_profile_sourcing`

| Agente | Linhas | Responsabilidade |
|--------|:------:|-----------------|
| **RouterAgent** | — | Roteamento cascateado (memory → fast → LLM) |
| **SearchAgent** | 797 | Busca por skill, score, localização, perfis similares |
| **AnalyticsAgent** | 592 | Contagens, médias, distribuições, diversidade |
| **DetailAgent** | 301 | Perfil completo, análise IA, experiências |
| **ComparisonAgent** | 873 | Comparação top N, por nome/ID, com perfil da vaga |
| **ReportAgent** | 529 | Relatório executivo, top candidatos, insights LLM |
| **ActionAgent** | 728 | Converter perfil → candidato, aplicações, listas |

**Actions**: 30+ (query, aggregate, analyze)

#### Domínio: `evaluation`

| Componente | Responsabilidade |
|------------|-----------------|
| **classify_input_node** | Classifica mensagem (answer/off_topic/unclear), detecção de injection |
| **evaluate_response_node** | Scoring via LLM estruturado |
| **decide_flow_node** | Próximo passo (follow-up, próxima pergunta, encerrar) |
| **craft_message_node** | Gera resposta/feedback ao candidato |

### 6.2. Serviços Compartilhados

| Serviço | Descrição |
|---------|-----------|
| **ATSAPIClient** | Client HTTP com retry/backoff para API Rails |
| **RAGService** | Busca semântica (pgvector + pg_trgm) |
| **AuthService** | JWT + OTT (one-time token) |
| **MemoryService** | Persistência PostgreSQL para histórico |
| **RabbitMQService** | Publisher/subscriber com ACK/NACK |
| **FairnessGuard** | Bloqueia filtros discriminatórios (LGPD/EEO) |
| **FactChecker** | Valida claims da IA contra dados reais |
| **StatsManager** | Cache thread-safe com TTL e LRU |

### 6.3. Infraestrutura

| Componente | Tecnologia | Função |
|------------|-----------|--------|
| Message Broker | RabbitMQ | Filas priorizadas por domínio |
| Task Queue | Celery | Workers distribuídos, soft limit 240s |
| Cache/Backend | Redis | Backend Celery + cache |
| Database | PostgreSQL | Memory + pgvector + pg_trgm |
| LLM | Google Gemini 2.5 Flash | Único provider |

---

## 7. Análise de Gap: Agentes e Domínios de Recrutamento

### 7.1. O que a Produção (B) TEM e é sólido

| Aspecto | Detalhes |
|---------|---------|
| **Sourcing multi-agente** | 6 agentes especializados com 30+ actions, cobrindo busca, analytics, detalhes, comparação, relatórios e ações |
| **Roteamento inteligente** | Cascata de 3 estratégias (memory → fast → LLM) com ~80% via keywords (sem custo LLM) |
| **Evaluation** | LangGraph de 4 nós para avaliar respostas de candidatos em entrevistas |
| **Memória conversacional** | Resolve pronomes, posições, shortlist. Mantém contexto de filtros |
| **Compliance básico** | FairnessGuard (anti-discriminação) + FactChecker (validação de dados) + anonimização para LLM |
| **Infraestrutura async** | RabbitMQ + Celery com filas priorizadas, workers distribuídos |

### 7.2. O que a Produção (B) NÃO TEM

| Contexto | Impacto | Equivalente na A |
|----------|:-------:|------------------|
| **Wizard de criação de vagas** | Sem vaga, não existe recrutamento | JobIntakeAgent (4.132L) + WizardOrchestratorService + JobWizardGraph (6 nós LLM) |
| **Prompt expandido da LIA na página de vagas** | Recrutador não tem assistência ao navegar vagas | `lia_assistant.py` + Orchestrator |
| **LIA dentro do Kanban/Pipeline** | Recrutador não tem assistência ao gerenciar candidatos | `kanban_assistant_service.py` + prompts especializados |
| **Triagem Curricular completa** | Candidatos não são filtrados antes da entrevista | TriagemCurricularAgent (1.384L) — 9 capabilities |
| **Condução de entrevistas** | Avalia respostas, mas não inicia nem conduz entrevista | EntrevistadorAgent (1.117L) — perguntas adaptativas, voz, WhatsApp |
| **Metodologia WSI completa** | Scoring básico, sem Bloom/Dreyfus/Big Five | AvaliadorWSIAgent (1.596L) — score científico com 4 taxonomias |
| **Agendamento** | Nenhum | SchedulingAgent (1.512L) — Microsoft Graph, conflitos, lembretes |
| **Comunicação multi-canal** | Nenhum | AnalistaFeedbackAgent parcial (2.068L) — email, WhatsApp, SMS, Teams |
| **Integração ATS** | API client direto, sem camada de integração | IntegradorATSAgent (704L) — Gupy, Pandapé, Merge, LGPD |
| **Assistente pessoal do recrutador** | Nenhum | RecruiterAssistantAgent (2.551L) — briefing diário, alertas, tarefas |
| **Analytics/KPIs de recrutamento** | Apenas stats do sourcing | AnalyticsAgent + AnalistaFeedback — funil, gargalos, previsões |
| **Tool Calling real** | ActionAgent com convert/apply apenas | ToolRegistry + ToolExecutor — 23 tools com tenant scoping |

---

## 8. Análise de Gap: Camadas Transversais

Esta seção cobre as camadas que **não são agentes de recrutamento**, mas infraestrutura crítica que permeia todo o sistema.

### 8.1. Aprendizagem e Learning Loop

**O que temos (A)**: Sistema completo de aprendizagem contínua que evolui com o uso.

| Serviço | Linhas | Função |
|---------|:------:|--------|
| `learning_hub_service.py` | 1.332 | Hub central — consolida padrões de todas as fontes (vagas similares, feedback, templates, outcomes) |
| `learning_loop_service.py` | 1.049 | Loop contínuo: captura interações → detecta padrões → melhora sugestões futuras |
| `feedback_learning_service.py` | 850 | Transforma like/dislike/edições do recrutador em `LearningPattern` models |
| `template_learning_service.py` | 401 | Aprende com templates usados/rejeitados — prioriza os mais eficazes |
| `job_learning.py` (API) | 348 | Endpoints de learning por vaga — o que funcionou, o que não funcionou |
| **Subtotal** | **~3.980** | |

**O que eles têm (B)**: Nada. Cada interação é descartada — o sistema não melhora com uso.

**Impacto**: Sem learning loop, a LIA não se torna mais inteligente ao longo do tempo. Recrutas com experiência terão a mesma experiência que novatos. Sugestões nunca melhoram.

### 8.2. ML e Predição

**O que temos (A)**: Modelos preditivos para otimizar recrutamento.

| Serviço | Linhas | Função |
|---------|:------:|--------|
| `ml/outcome_predictor.py` | 519 | Prediz probabilidade de contratação, time-to-fill, risco de desistência |
| `ml/feature_engineering.py` | 418 | Engenharia de features: transforma dados brutos em sinais preditivos |
| `outcome_correlator_service.py` | 494 | Correlaciona scores WSI com resultados reais (contratou? ficou? performou?) |
| `ml_predictions.py` (API) | 325 | Endpoints de predições |
| **Subtotal** | **~1.756** | |

**O que eles têm (B)**: AnalyticsAgent faz estatísticas descritivas do sourcing (contagens, médias). Sem ML preditivo.

**Impacto**: Sem predição, o sistema não pode antecipar problemas (vaga vai demorar para fechar, pipeline está com gargalo, candidato tem risco de desistir).

### 8.3. Pattern Detection e Intelligence Layer

**O que temos (A)**: Detecção inteligente de padrões e enriquecimento de sugestões.

| Serviço | Linhas | Função |
|---------|:------:|--------|
| `pattern_detector_service.py` | 568 | Detecta padrões recorrentes: vagas similares, preferências do recrutador, sazonalidade |
| `intelligence_layer_service.py` | 755 | Enriquece sugestões com dados históricos: "vagas similares tiveram sucesso com X" |
| **Subtotal** | **~1.323** | |

**O que eles têm (B)**: Nada explícito. Fast routing é baseado em patterns fixos (regex), não em aprendizagem.

### 8.4. Compliance e Regulatório (3 Pilares)

**O que temos (A)**: Cobertura abrangente de 3 pilares regulatórios.

| Componente | Linhas | Pilar | Função |
|------------|:------:|:-----:|--------|
| `compliance_controls.py` (API) | 944 | SOX + EU AI Act | Controles de compliance, métricas, verificações automáticas |
| `lgpd_compliance.py` (API) | 817 | LGPD | Consentimento, portabilidade, eliminação de dados pessoais |
| `consent_management.py` (API) | 664 | LGPD | Gestão granular de consentimento por finalidade |
| `trust_center.py` (API) | 632 | Transparência | Trust Center público — explica como IA é usada |
| `data_subject_requests.py` (API) | 627 | LGPD | DSAR — requisições de titulares de dados |
| `risk_register.py` (API) | 529 | EU AI Act | Registro de riscos de IA com classificação |
| `audit_logs.py` (API) | 460 | SOX | Logs de auditoria imutáveis |
| `global_policies.py` (API) | 333 | Governança | Políticas globais de IA por tenant |
| `insurance.py` (API) | 1.050 | Garantias | Seguro/garantias de decisões de IA |
| `audit_service.py` | 401 | SOX | Serviço de auditoria interna |
| `policy_engine_service.py` | 912 | Governança | Motor de políticas (regras configuráveis por tenant) |
| **Subtotal** | **~7.369** | | |

**O que eles têm (B)**: 
- `FairnessGuard` — bloqueia filtros discriminatórios (gênero, raça, idade)
- `FactChecker` — valida claims da IA contra dados reais
- Injection Detection — no domínio evaluation
- Anonimização — `anonymize_for_llm()` remove dados sensíveis

**Gap**: Compliance básico bem implementado, mas sem:
- Pilares LGPD completos (consentimento, portabilidade, DSAR)
- SOX compliance (auditoria, controles internos)
- EU AI Act compliance (registro de riscos, classificação de sistemas)
- Trust Center (transparência pública)
- Policy Engine (políticas configuráveis por cliente)

### 8.5. Governança de IA

**O que temos (A)**: Monitoramento, explicabilidade e observabilidade de agentes.

| Serviço | Linhas | Função |
|---------|:------:|--------|
| `agent_monitoring_service.py` | 580 | Monitora latência, erros, custos, uso de tokens por agente |
| `autonomous_agent_service.py` | 809 | Agentes autônomos com background jobs e human-in-the-loop (aprovação) |
| `explainability_service.py` | 321 | Explicabilidade (XAI): por que a IA tomou esta decisão? |
| `observability.py` (API) | 1.419 | Observabilidade: traces, métricas, alertas, dashboards |
| **Subtotal** | **~3.129** | |

**O que eles têm (B)**: Logging básico. `ConversationMemory` rastreia interações, mas sem monitoramento de performance de agentes, sem XAI, sem observabilidade estruturada.

### 8.6. Calibração e Personalização

**O que temos (A)**: Sistema evolui por recrutador e por empresa.

| Serviço | Linhas | Função |
|---------|:------:|--------|
| `calibration_service.py` | 474 | Calibra scores WSI com feedback real do recrutador (like/dislike em candidatos) |
| `recruiter_personalization_service.py` | 554 | Personaliza LIA por recrutador: tom de voz, atalhos, preferências, velocidade de resposta |
| `calibration.py` (API) | 420 | Endpoints de calibração |
| `seniority_context_calibrator.py` | — | Calibração contextual de senioridade (13 perfis profissionais) |
| **Subtotal** | **~1.448** | |

**O que eles têm (B)**: Nada. Cada recrutador recebe a mesma experiência. Sem calibração de scores.

### 8.7. Resiliência e Feature Flags

**O que temos (A)**: Proteção contra falhas e controle granular de funcionalidades.

| Serviço | Linhas | Função |
|---------|:------:|--------|
| `circuit_breaker.py` | 364 | Circuit breaker para APIs externas (Gemini, Pearch, ATS) — previne cascata de falhas |
| `feature_flag_service.py` | 315 | Feature flags por tenant, feature, ambiente — liga/desliga funcionalidades sem deploy |
| **Subtotal** | **~679** | |

**O que eles têm (B)**: Retry com backoff no ATSAPIClient. Celery tem soft/hard time limits. Não tem feature flags.

### 8.8. Resumo Consolidado das Camadas Transversais

| Camada | Linhas (A) | Status (B) | Criticidade |
|--------|:----------:|:----------:|:-----------:|
| Learning Loop + Feedback | ~3.980 | ❌ Inexistente | **Crítica** |
| ML Preditivo + Outcomes | ~1.756 | ❌ Inexistente | **Importante** |
| Pattern Detection + Intelligence | ~1.323 | ❌ Inexistente | **Importante** |
| Compliance (LGPD/SOX/EU AI Act) | ~7.369 | ⚠️ Básico (FairnessGuard + FactChecker) | **Crítica** |
| Governança IA (Monitoring + XAI) | ~3.129 | ⚠️ Logging básico | **Significativa** |
| Calibração + Personalização | ~1.448 | ❌ Inexistente | **Importante** |
| Resiliência + Feature Flags | ~679 | ⚠️ Retry básico | **Moderada** |
| **TOTAL** | **~19.684** | | |

---

## 9. Projeção de Domínios Faltantes para Produção

Com base na arquitetura de domínios (B) — usando `DomainPrompt`, `@register_domain`, `DomainWorkflow` — projetamos os domínios necessários para cobrir o ciclo completo.

### 9.1. Domínio: `job_management` — Criação e Gestão de Vagas

**Fase**: ① | **Prioridade**: #1 (sem vaga não existe recrutamento)  
**Equivalente A**: JobIntakeAgent (4.132L) + WizardOrchestratorService + JobWizardGraph

| Agente | Responsabilidade | Complexidade |
|--------|-----------------|:------------:|
| **WizardAgent** | Conversa guiada para criação de vaga (etapas, campos, validações, transições) | Alta |
| **JDExtractorAgent** | Extrair requisitos de JD colada/importada (parsing inteligente) | Média |
| **JDGeneratorAgent** | Gerar JD completa a partir dos campos preenchidos | Média |
| **EnrichmentAgent** | Enriquecer vaga com dados de mercado (salário, skills, competências) | Alta |
| **ValidationAgent** | Validar completude da vaga, WSI Quality Score | Baixa |

**Actions (~20)**: `create_job`, `update_job`, `extract_jd`, `generate_jd`, `suggest_skills`, `suggest_salary`, `validate_completeness`, `publish_job`, `pause_job`, `close_job`, `duplicate_job`, `archive_job`, `set_pipeline_stages`, `configure_screening`, `preview_jd`, `analyze_jd_quality`, `suggest_improvements`, `import_from_ats`, `set_affirmative_action`, `configure_gates`

**Estimativa**: 3.000–4.000 linhas | Complexidade **Alta**  
**Desafio principal**: O wizard conversacional (LIA pergunta → recrutador responde → LIA avança etapa) é o componente mais complexo. Exige gerenciamento de estado de formulário + conversa + transições de etapa com confirmação textual.

### 9.2. Domínio: `pipeline_management` — Kanban/Pipeline de Candidatos

**Fase**: ⑥ | **Prioridade**: #3  
**Equivalente A**: KanbanAssistantService + tools + RecruiterAssistant

| Agente | Responsabilidade | Complexidade |
|--------|-----------------|:------------:|
| **PipelineViewAgent** | Visualizar candidatos por etapa, filtros, ordenação | Média |
| **TransitionAgent** | Mover candidatos entre etapas com validações/gates | Alta |
| **ActionAgent** | Rejeitar, shortlisting, aprovação, bulk actions | Média |
| **InsightsAgent** | Sugestões proativas (candidatos parados, gargalos) | Média |

**Actions (~18)**: `list_by_stage`, `move_candidate`, `bulk_move`, `reject_candidate`, `shortlist_candidate`, `approve_candidate`, `request_approval`, `add_note`, `view_history`, `filter_pipeline`, `suggest_next_action`, `detect_bottleneck`, `auto_advance`, `gate_check`, `compare_stage_candidates`, `export_stage`, `archive_candidate`, `restore_candidate`

**Estimativa**: 2.000–2.500 linhas | Complexidade **Alta**  
**Desafio principal**: Sistema de Gates (verificações automáticas antes de avançar etapa) e automação inteligente de transições.

### 9.3. Domínio: `cv_screening` — Triagem Curricular

**Fase**: ③ | **Prioridade**: #2  
**Equivalente A**: TriagemCurricularAgent (1.384L) + WSI Screening Pipeline

| Agente | Responsabilidade | Complexidade |
|--------|-----------------|:------------:|
| **ParserAgent** | Extrair dados estruturados do CV (PDF, DOCX, texto) | Média |
| **ScoringAgent** | Score WSI inicial baseado no CV vs requisitos | Alta |
| **RedFlagAgent** | Detectar red flags (gaps, inconsistências, fraude) | Média |
| **RankingAgent** | Rankear e aplicar cutoff dinâmico (top 25%) | Baixa |

**Actions (~12)**: `parse_cv`, `score_candidate`, `batch_screen`, `rank_candidates`, `apply_cutoff`, `detect_red_flags`, `check_eligibility`, `generate_screening_report`, `compare_to_jd`, `calculate_wsi_initial`, `check_saturation`, `export_screening_results`

**Estimativa**: 1.500–2.000 linhas | Complexidade **Média-Alta**  
**Desafio principal**: Integração com WSI scoring (Bloom/Dreyfus) já na triagem inicial.

### 9.4. Domínio: `interviewing` — Condução de Entrevistas WSI

**Fase**: ④ | **Prioridade**: #4 (complementa o `evaluation` existente)  
**Equivalente A**: EntrevistadorAgent (1.117L) + WSI Voice Orchestrator

| Agente | Responsabilidade | Complexidade |
|--------|-----------------|:------------:|
| **InterviewConductorAgent** | Conduzir entrevista adaptativa (escolher perguntas, sequenciar, follow-ups) | Alta |
| **TranscriptionAgent** | Transcrever áudio (Deepgram/OpenMic) | Média |
| **SentimentAgent** | Analisar tom de voz, confiança, detecção de evasividade | Média |

**Actions (~10)**: `start_interview`, `send_question`, `analyze_response`, `generate_followup`, `transcribe_audio`, `analyze_voice_confidence`, `detect_evasion`, `end_interview`, `calculate_score`, `generate_interview_qa`

**Estimativa**: 1.200–1.500 linhas | Complexidade **Média-Alta**  
**Integração**: Conecta-se ao domínio `evaluation` existente para scoring das respostas.

### 9.5. Domínio: `wsi_assessment` — Avaliação WSI Completa

**Fase**: ⑤ | **Prioridade**: #4 (junto com interviewing)  
**Equivalente A**: AvaliadorWSIAgent (1.596L) + Score Normalization

| Agente | Responsabilidade | Complexidade |
|--------|-----------------|:------------:|
| **BloomClassifierAgent** | Classificar respostas por Taxonomia de Bloom (6 níveis cognitivos) | Média |
| **DreyfusClassifierAgent** | Classificar proficiência Dreyfus (5 níveis: Novato → Especialista) | Média |
| **BigFiveAgent** | Mapear traços Big Five comportamentais a partir das respostas | Alta |
| **OpinionAgent** | Gerar parecer completo e estruturado para o gestor | Média |
| **CalibrationAgent** | Ajustar modelo com feedback do recrutador (learn from corrections) | Média |

**Actions (~12)**: `calculate_wsi_score`, `classify_bloom`, `classify_dreyfus`, `map_big_five`, `validate_cbi`, `generate_opinion`, `compare_candidates`, `calibrate_model`, `explain_score`, `rank_by_wsi`, `generate_feedback`, `export_assessment`

**Estimativa**: 1.500–2.000 linhas | Complexidade **Alta**  
**Desafio principal**: A fórmula WSI (ponderação entre blocos, coeficientes de dificuldade, normalização por versão de questionário) é o componente mais científico.

### 9.6. Domínio: `scheduling` — Agendamento

**Fase**: ⑦ | **Prioridade**: #5  
**Equivalente A**: SchedulingAgent (1.512L) + Microsoft Graph

| Agente | Responsabilidade | Complexidade |
|--------|-----------------|:------------:|
| **CalendarAgent** | Verificar disponibilidade, encontrar slots comuns | Média |
| **BookingAgent** | Criar, reagendar, cancelar entrevistas | Média |
| **ReminderAgent** | Lembretes automáticos, detecção de conflitos | Baixa |

**Actions (~10)**: `check_availability`, `schedule_interview`, `reschedule`, `cancel_interview`, `find_common_slots`, `send_reminder`, `auto_reminders`, `list_today`, `resolve_conflict`, `generate_self_schedule_link`

**Estimativa**: 1.200–1.500 linhas | Complexidade **Média**  
**Dependência**: Microsoft Graph API (calendário, Teams).

### 9.7. Domínio: `communication` — Hub de Comunicação

**Fase**: ⑧ | **Prioridade**: #6  
**Equivalente A**: AnalistaFeedbackAgent parcial (2.068L)

| Agente | Responsabilidade | Complexidade |
|--------|-----------------|:------------:|
| **EmailAgent** | Enviar emails individuais e em massa (Mailgun) | Média |
| **WhatsAppAgent** | Mensagens WhatsApp via provider | Média |
| **TeamsAgent** | Notificações Microsoft Teams (Adaptive Cards) | Baixa |
| **TemplateAgent** | Gerenciar e personalizar templates com variáveis dinâmicas | Baixa |

**Actions (~12)**: `send_email`, `send_whatsapp`, `send_teams_notification`, `send_bulk`, `preview_message`, `manage_templates`, `view_history`, `schedule_message`, `track_delivery`, `personalize_template`, `send_feedback`, `send_rejection`

**Estimativa**: 1.500–2.000 linhas | Complexidade **Média**

### 9.8. Domínio: `analytics_reporting` — Analytics e KPIs

**Fase**: ⑨ | **Prioridade**: #7  
**Equivalente A**: AnalistaFeedbackAgent parcial + AnalyticsAgent

| Agente | Responsabilidade | Complexidade |
|--------|-----------------|:------------:|
| **FunnelAgent** | Análise de funil, conversão por etapa, drop-off | Média |
| **PredictiveAgent** | Time-to-fill, previsão de fechamento, tendências | Alta |
| **BenchmarkAgent** | Comparações entre vagas, períodos, mercado | Média |
| **ReportGeneratorAgent** | Relatórios executivos, dashboards para gestores | Média |

**Actions (~14)**: `funnel_analysis`, `bottleneck_detection`, `time_to_fill_prediction`, `weekly_summary`, `compare_periods`, `detect_anomalies`, `suggest_strategy`, `generate_executive_report`, `benchmark_salary`, `diversity_report`, `source_effectiveness`, `cost_per_hire`, `quality_of_hire`, `export_report`

**Estimativa**: 2.000–2.500 linhas | Complexidade **Média-Alta**

---

## 10. Projeção de Camadas Transversais Faltantes para Produção

### 10.1. Learning Loop e Feedback

| Componente | Estimativa | Prioridade |
|------------|:----------:|:----------:|
| Learning Hub central (consolida padrões de todas as fontes) | 1.200–1.500L | Alpha 1 |
| Feedback Learning (like/dislike → LearningPattern) | 800–1.000L | Alpha 1 |
| Template Learning (aprende com templates usados/rejeitados) | 400–500L | Alpha 2 |
| Outcome Learning (correlaciona scores com resultados reais) | 500–700L | Alpha 2 |
| **Subtotal** | **~2.900–3.700** | |

### 10.2. Compliance Completo (3 Pilares)

| Componente | Estimativa | Pilar | Prioridade |
|------------|:----------:|:-----:|:----------:|
| LGPD compliance (consentimento, portabilidade, eliminação) | 800–1.000L | LGPD | Alpha 1 |
| Consent Management granular | 500–700L | LGPD | Alpha 1 |
| DSAR (requisições de titulares) | 500–600L | LGPD | Alpha 1 |
| Audit Logs (imutáveis, rastreáveis) | 400–500L | SOX | Alpha 1 |
| Compliance Controls (SOX + EU AI Act) | 800–1.000L | SOX + EU AI | Alpha 2 |
| Trust Center público | 500–600L | Transparência | Alpha 2 |
| Risk Register de IA | 400–500L | EU AI Act | Alpha 2 |
| Policy Engine multi-tenant | 800–1.000L | Governança | Alpha 2 |
| **Subtotal** | **~4.700–5.900** | | |

### 10.3. Governança de IA

| Componente | Estimativa | Prioridade |
|------------|:----------:|:----------:|
| Agent Monitoring (latência, erros, custos, tokens) | 500–600L | Alpha 1 |
| Explainability / XAI (por que a IA decidiu isso?) | 300–400L | Alpha 1 |
| Observability (traces, métricas, alertas) | 1.000–1.400L | Alpha 2 |
| Autonomous Agents (background jobs + human approval) | 700–900L | Alpha 2 |
| **Subtotal** | **~2.500–3.300** | |

### 10.4. Outras Camadas

| Componente | Estimativa | Prioridade |
|------------|:----------:|:----------:|
| ML Preditivo (outcome predictor + feature engineering) | 800–1.000L | Alpha 2 |
| Pattern Detection (padrões recorrentes) | 500–600L | Alpha 2 |
| Intelligence Layer (enriquecimento com dados históricos) | 600–800L | Alpha 2 |
| Calibração WSI (feedback → ajuste de scores) | 400–500L | Alpha 1 |
| Personalização por recrutador (tom, atalhos, preferências) | 500–600L | Alpha 2 |
| Feature Flags (granular por tenant/feature) | 300–400L | Alpha 1 |
| Circuit Breaker (melhorado para multi-domínio) | 200–300L | Alpha 1 |
| **Subtotal** | **~3.300–4.200** | |

---

## 11. Estimativa Consolidada de Esforço

### 11.1. Domínios de Recrutamento (Seção 9)

| # | Domínio | Agentes | Actions | Linhas | Complexidade |
|:-:|---------|:-------:|:-------:|:------:|:------------:|
| 1 | `job_management` | 5 | ~20 | 3.000–4.000 | **Alta** |
| 2 | `cv_screening` | 4 | ~12 | 1.500–2.000 | **Média-Alta** |
| 3 | `pipeline_management` | 4 | ~18 | 2.000–2.500 | **Alta** |
| 4 | `interviewing` | 3 | ~10 | 1.200–1.500 | **Média-Alta** |
| 5 | `wsi_assessment` | 5 | ~12 | 1.500–2.000 | **Alta** |
| 6 | `scheduling` | 3 | ~10 | 1.200–1.500 | **Média** |
| 7 | `communication` | 4 | ~12 | 1.500–2.000 | **Média** |
| 8 | `analytics_reporting` | 4 | ~14 | 2.000–2.500 | **Média-Alta** |
| | **Subtotal Domínios** | **32** | **~108** | **14.000–18.000** | |

### 11.2. Camadas Transversais (Seção 10)

| Camada | Linhas | Complexidade |
|--------|:------:|:------------:|
| Learning Loop + Feedback | 2.900–3.700 | **Alta** |
| Compliance (LGPD/SOX/EU AI Act) | 4.700–5.900 | **Muito Alta** |
| Governança IA | 2.500–3.300 | **Alta** |
| ML + Pattern Detection + Intelligence | 1.900–2.400 | **Alta** |
| Calibração + Personalização | 900–1.100 | **Média** |
| Feature Flags + Resiliência | 500–700 | **Baixa** |
| **Subtotal Transversais** | **13.400–17.100** | |

### 11.3. Total Geral

| Bloco | Linhas | % do Total |
|-------|:------:|:----------:|
| Domínios de Recrutamento | 14.000–18.000 | ~52% |
| Camadas Transversais | 13.400–17.100 | ~48% |
| **TOTAL** | **~27.400–35.100** | 100% |

> **Nota**: Estimativas de linhas são projeções baseadas nos equivalentes funcionais implementados no Protótipo (A). Volume real depende do nível de reutilização da infraestrutura existente em B e do grau de paralelismo da equipe.

### 11.4. Roadmap sugerido por fase

```
ALPHA 1 (Funcionalidade Core):
├── job_management               (3.000–4.000L | Alta)
├── cv_screening                 (1.500–2.000L | Média-Alta)
├── pipeline_management          (2.000–2.500L | Alta)
├── interviewing + wsi_assessment(2.700–3.500L | Alta)
├── scheduling                   (1.200–1.500L | Média)
├── LGPD compliance básico       (1.800–2.300L | Alta)
├── Agent Monitoring + XAI       (800–1.000L   | Média)
├── Feature Flags + Circuit Breaker(500–700L   | Baixa)
└── Calibração WSI               (400–500L     | Média)

ALPHA 2 (Maturidade):
├── communication                (1.500–2.000L | Média)
├── analytics_reporting          (2.000–2.500L | Média-Alta)
├── Learning Loop completo       (2.900–3.700L | Alta)
├── Compliance SOX + EU AI Act   (3.000–3.900L | Muito Alta)
├── ML Preditivo + Pattern Detection(1.900–2.400L | Alta)
├── Observability + Autonomous Agents(1.700–2.300L | Alta)
└── Personalização por recrutador(500–600L     | Média)
```

---

## 12. Recomendação Estratégica

### 12.1. Abordagem Híbrida

A melhor estratégia é combinar os pontos fortes de cada arquitetura:

| Da Arquitetura B (Produção) — Usar como base | Da Arquitetura A (Protótipo) — Usar como referência |
|----------------------------------------------|-----------------------------------------------------|
| `DomainRegistry` + `@register_domain` | Especificação funcional de cada agente (capabilities, actions) |
| `DomainWorkflow` (LangGraph: intent → execute → format) | Fluxos conversacionais do wizard (etapas, transições, confirmação textual) |
| Roteamento cascateado (fast → memory → LLM) | Metodologia WSI completa (Bloom, Dreyfus, Big Five, CBI) |
| RabbitMQ + Celery para execução assíncrona | Camadas de learning loop, compliance e governança |
| `FairnessGuard` + `FactChecker` como compliance guards | 23 tools com tenant scoping |
| `ConversationMemory` para contexto conversacional | Calibração e personalização por recrutador |

### 12.2. Princípios de implementação

1. **Um domínio de cada vez**: Cada novo domínio segue o contrato `DomainPrompt` e se registra via `@register_domain`. Isso garante compatibilidade automática com roteamento, filas e workflow.

2. **Protótipo como spec funcional**: Os agentes da Arquitetura A definem O QUE fazer (capabilities, actions, fluxos). A Arquitetura B define COMO fazer (infraestrutura, filas, escalabilidade).

3. **Camadas transversais como services compartilhados**: Learning loop, compliance e governança são serviços que permeiam todos os domínios — devem ser implementados como services compartilhados, não dentro de domínios específicos.

4. **Fast routing primeiro**: Para cada novo domínio, definir keyword patterns para ~80% dos casos antes de depender do LLM. Isso mantém performance e reduz custos.

5. **Compliance desde o início**: LGPD não é "nice to have" — é requisito legal. FairnessGuard e FactChecker já existem; expandir com consentimento, DSAR e auditoria.

### 12.3. O que NÃO portar do Protótipo

| Aspecto | Motivo |
|---------|--------|
| Orquestrador central (SPOF) | Substituído pelo DomainRegistry distribuído |
| Roteamento always-LLM | Substituído pelo fast routing cascateado |
| Comunicação síncrona REST | Substituída por RabbitMQ + Celery |
| Código monolítico de agentes (4000+ linhas) | Decompor em agentes menores dentro do domínio |

### 12.4. Considerações de Integração e Migração de Dados

| Aspecto | Recomendação |
|---------|--------------|
| **Dados do ATS Rails** | B já integra com API Rails via `ATSAPIClient`. Novos domínios devem usar o mesmo client, expandindo endpoints YAML |
| **WSI Data Model** | Protótipo A tem 6 tabelas WSI (sessions, questions, response_analyses, results, reports, feedbacks). Estrutura de dados deve ser portada como schema de referência |
| **Conversational State** | B usa `ConversationMemory` em memória. Para domínios como wizard (sessões longas), considerar persistência em PostgreSQL |
| **Learning Patterns** | Novo schema no PostgreSQL para `learning_patterns`, `feedback_events`, `outcome_records` — não existe em B |
| **Compliance/Audit** | Logs de auditoria exigem storage imutável (append-only). Considerar particionamento por tenant e retenção configurável |
| **Feature Flags** | Novo schema simples (tenant_id, feature_key, enabled, metadata). Pode usar cache Redis para leitura rápida |

### 12.5. Observabilidade e SLOs Sugeridos

| Métrica | SLO Sugerido | Contexto |
|---------|:------------:|----------|
| Latência P95 (fast routing) | < 500ms | Queries simples com keywords |
| Latência P95 (LLM routing) | < 3s | Queries complexas que precisam de LLM |
| Disponibilidade dos domínios | 99.5% | Uptime medido por domínio |
| Taxa de erro de agentes | < 2% | Erros não recuperados por domínio |
| Custo LLM por query | Monitorar | Tokens consumidos por domínio/agente |
| Tempo de processamento Celery | < 30s P95 | Tasks assíncronas via filas |

---

## 13. Requisitos de Desenvolvimento para MVP Alpha 1

> **Objetivo**: Cruzar as 9 etapas do fluxo Alpha 1 (doc: `mvp-alpha-scenarios.md`) com os domínios e camadas transversais projetados nas seções 9–11, identificando exatamente o que a equipe de Produção (B) precisa construir para suportar o cenário Alpha 1 de teste interno.
>
> **Premissas do Alpha 1**: ATS integrado (Merge), vagas importadas, login email/senha, adição de candidatos por email.
> **Escopo**: Do login até o agendamento de entrevista. Sem wizard de criação de vagas, sem SSO/MFA, sem admin, sem billing.

### 13.1. Mapa: Etapa Alpha 1 → Domínios B → Status

| Etapa Alpha 1 | Domínio B necessário | Status em B | Gap |
|:---:|--------------------------|:---:|------|
| 1. Login | Auth (email/senha + JWT) | ✅ Parcial | Auth básica existe via API Rails. Falta: tela de login dedicada, sessão JWT no frontend, dashboard de vagas |
| 2. Editar Vaga | `job_management` | ❌ Não existe | Formulário edição, campos obrigatórios, sync ATS bidirecional, enriquecimento via LLM |
| 3. Roteiro WSI | `wsi_assessment` | ❌ Não existe | Modal Preview→Roteiro→Editar, pipeline WSI (Blocos 2-5), geração perguntas, calibração senioridade |
| 4. Buscar Candidatos | `sourcing` | ✅ Existe | Domínio principal de B. ES+PGVector+WRF, Pearch, filtros avançados. **Mais maduro que A** |
| 5. Gate 1 | `pipeline_management` | ❌ Não existe | Kanban, aprovação individual/massa, drag-and-drop, SmartTransitionModal, gate checks |
| 6. Contato Email | `communication` | ❌ Não existe | Templates email, Mailgun, tracking abertura/clique, contato automático |
| 6B. Follow-up | `communication` | ❌ Não existe | Re-envio 24h × 7 dias, detecção sem_resposta, scheduler |
| 7. Triagem WSI | `interviewing` + `wsi_assessment` | ❌ Não existe | Chat web público, condução adaptativa, cálculo score WSI, parecer |
| 7A. Abandonada | `interviewing` | ❌ Não existe | Timeout 48h, lembretes, salvamento parcial |
| 7B. Pós-Triagem | `wsi_assessment` | ❌ Não existe | Encerramento chat, feedback ao candidato, parecer ao consultor |
| 8. Gate 2 | `pipeline_management` | ❌ Não existe | Aprovação/reprovação com base em score WSI, comparação candidatos |
| 9A. Agendamento | `scheduling` | ❌ Não existe | Microsoft Graph, slots, evento Teams, convite |
| 9B. Feedback | `communication` | ❌ Não existe | Template feedback reprovação, envio email/WhatsApp |

**Resumo**: Das 9 etapas macro do Alpha 1, a Produção (B) cobre apenas **1 completamente** (Etapa 4 — Buscar Candidatos) e **1 parcialmente** (Etapa 1 — Login). As demais 7 etapas dependem de domínios que precisam ser construídos.

### 13.2. Mapa: Agentes Alpha 1 → Domínios B

> Os 11 agentes do Alpha 1 (Ag.0–Ag.10) precisam ser implementados como agentes dentro dos domínios B. A tabela abaixo mapeia cada agente ao domínio destino e à implementação existente em B.

| Agente | Etapas onde atua | Domínio B destino | Existe em B? | Equivalente A (linhas) |
|--------|------------------|-------------------|:---:|:---:|
| **Ag.0** Orchestrator | Todas | Core (já existe) | ✅ | `orchestrator.py` (2.847L) |
| **Ag.1** JobIntakeAgent | 2, 3 | `job_management` | ❌ | `job_intake_agent.py` (4.132L) |
| **Ag.2** SourcingAgent | 4 | `sourcing` | ✅ | Multi-agente em B |
| **Ag.3** TriagemCurricular | 4 | `cv_screening` | ❌ | `triagem_curricular_agent.py` (1.384L) |
| **Ag.4** EntrevistadorWSI | 3B, 7, 7A, 7B | `interviewing` | ❌ | `entrevistador_agent.py` (1.117L) |
| **Ag.5** AvaliadorWSI | 4, 7, 7B, 8 | `wsi_assessment` | ❌ | `avaliador_wsi_agent.py` (1.596L) |
| **Ag.6** SchedulingAgent | 9A | `scheduling` | ❌ | `scheduling_agent.py` (1.512L) |
| **Ag.7** AnalistaFeedback | 5, 8, 9B | `pipeline_management` | ❌ | `analista_feedback_agent.py` (2.068L) |
| **Ag.8** IntegradorATS | 2, 5, 8, 9B | `ats_integration` | ✅ Parcial | `integrador_ats_agent.py` (704L) |
| **Ag.9** TaskPlanner | 6B, 7A | Core (scheduler) | ❌ | Novo — background jobs |
| **Ag.10** CommunicationAgent | 6, 6B, 7A, 9A, 9B | `communication` | ❌ | `communication_agent.py` (existente) |

**Resumo**: Dos 11 agentes, B já possui **2 completos** (Ag.0 Orchestrator, Ag.2 SourcingAgent) e **1 parcial** (Ag.8 IntegradorATS). Os demais **8 agentes** precisam ser implementados dentro dos novos domínios.

### 13.3. Domínios a construir para Alpha 1 — Prioridade e Dependências

```
ORDEM DE IMPLEMENTAÇÃO (baseada em dependências entre etapas):

  ┌─────────────────────────┐
  │ 1. job_management       │ ← Etapas 2, 3 (sem vaga editada, nada funciona)
  │    Ag.1 JobIntakeAgent  │
  │    ~3.000–4.000L        │
  └──────────┬──────────────┘
             │
  ┌──────────▼──────────────┐
  │ 2. wsi_assessment       │ ← Etapa 3 (roteiro WSI depende da vaga)
  │    Ag.5 AvaliadorWSI    │
  │    ~1.500–2.000L        │
  └──────────┬──────────────┘
             │
  ┌──────────▼──────────────┐
  │ 3. cv_screening         │ ← Etapa 4 (complementa o sourcing existente)
  │    Ag.3 TriagemCurricular│
  │    ~1.500–2.000L        │
  └──────────┬──────────────┘
             │
  ┌──────────▼──────────────┐
  │ 4. pipeline_management  │ ← Etapas 5, 8 (Kanban, Gates, aprovações)
  │    Ag.7 AnalistaFeedback│
  │    ~2.000–2.500L        │
  └──────────┬──────────────┘
             │
  ┌──────────▼──────────────┐
  │ 5. communication        │ ← Etapas 6, 6B, 7A, 9B (email, follow-up, feedback)
  │    Ag.10 Communication  │
  │    ~1.500–2.000L        │
  └──────────┬──────────────┘
             │
  ┌──────────▼──────────────┐
  │ 6. interviewing         │ ← Etapa 7 (triagem WSI via chat web)
  │    Ag.4 Entrevistador   │
  │    ~1.200–1.500L        │
  └──────────┬──────────────┘
             │
  ┌──────────▼──────────────┐
  │ 7. scheduling           │ ← Etapa 9A (agendamento — última etapa)
  │    Ag.6 Scheduling      │
  │    ~1.200–1.500L        │
  └─────────────────────────┘
```

**Total de domínios a construir para Alpha 1**: 7 domínios | ~11.900–15.500 linhas

> **Nota**: O domínio `analytics_reporting` (seção 9.8) NÃO é necessário para o Alpha 1. Fica para Alpha 2.

### 13.4. Camadas Transversais necessárias no Alpha 1

| Camada | Componentes obrigatórios para Alpha 1 | Linhas estimadas | Justificativa |
|--------|---------------------------------------|:---:|------|
| **Compliance LGPD** | Consentimento candidato, DSAR básico, audit logs | 1.800–2.300L | Requisito legal — triagem envolve dados pessoais |
| **Agent Monitoring** | Latência, erros, custos por agente | 500–600L | 8 novos agentes precisam de observabilidade |
| **XAI** | Explicação de scores WSI e decisões de gate | 300–400L | Consultores precisam entender por que a LIA decidiu |
| **Calibração WSI** | Feedback do recrutador → ajuste de scoring | 400–500L | Essencial para qualidade do WSI no teste interno |
| **Feature Flags** | Liga/desliga por tenant/feature | 300–400L | Controle granular durante teste Alpha |
| **Circuit Breaker** | Resiliência multi-domínio | 200–300L | 7 novos domínios = 7 pontos de falha potenciais |
| **TaskPlanner/Scheduler** | Jobs assíncronos (follow-up, lembretes, timeouts) | 400–600L | Ag.9 precisa de infraestrutura de background jobs |
| **Subtotal Alpha 1** | | **~3.900–5.200L** | |

### 13.5. Cards Jira: Cobertura do Alpha 1

> Dados extraídos de `mvp-alpha-scenarios.md` seção 2.2.4.

| Métrica | Valor |
|---------|:-----:|
| Cards Jira existentes (únicos) | 101 |
| Cards novos a criar | 10 |
| Cards WSI sugeridos (pendentes aprovação) | 10 |
| **Total cards Alpha 1** | **111–121** |
| Story points totais | **592–668** |
| Agentes IA envolvidos | 11 |
| Integrações externas | Merge (ATS), Mailgun (email), MS Graph (calendário/Teams), Pearch (busca), Gemini (LLM) |

### 13.6. Resumo: Esforço Alpha 1 vs. Total Projetado

| Bloco | Alpha 1 (linhas) | Total projetado (linhas) | % do Total |
|-------|:-----------------:|:------------------------:|:----------:|
| Domínios de Recrutamento (7 de 8) | ~11.900–15.500 | 14.000–18.000 | ~85% |
| Camadas Transversais (subset) | ~3.900–5.200 | 13.400–17.100 | ~29% |
| **TOTAL Alpha 1** | **~15.800–20.700** | ~27.400–35.100 | **~57%** |

> **Análise**: O Alpha 1 exige ~57% do esforço total projetado, concentrado em 7 dos 8 domínios de recrutamento (todos exceto `analytics_reporting`) e ~29% das camadas transversais (apenas as essenciais: LGPD, monitoring, calibração, feature flags, resiliência). As camadas de maturidade (learning loop completo, ML preditivo, observabilidade avançada, personalização) ficam para Alpha 2.

### 13.7. Vantagens que a Produção (B) já oferece para o Alpha 1

| Vantagem B | Impacto no Alpha 1 |
|-----------|---------------------|
| `DomainRegistry` + `@register_domain` | Cada novo domínio se registra automaticamente — consistência arquitetural garantida |
| `DomainWorkflow` (LangGraph) | Cada novo domínio herda o workflow padrão (intent → execute → format) — reduz boilerplate |
| RabbitMQ + Celery | Infraestrutura de filas pronta para Ag.9 TaskPlanner (follow-up, lembretes, timeouts) |
| `FairnessGuard` + `FactChecker` | Compliance guards já implementados — novos domínios herdam proteção automática |
| `ConversationMemory` | Contexto conversacional já funcional — wizard e triagem podem reutilizar |
| Fast routing (~80% sem LLM) | Performance e custo otimizados — keyword patterns para cada novo domínio |
| `SourcingAPIClient` | Client HTTP para API Rails já implementado — novos domínios expandem endpoints |
| Cascaded routing (memory → fast → LLM) | Estratégia de roteamento escalável — novos domínios se encaixam nativamente |

---

## 14. Plano de Ajustes no Protótipo (A) para Alinhar com Arquitetura B

> **Objetivo**: Detalhar as mudanças necessárias no código-fonte do protótipo (`lia-agent-system/`) para que ele passe a seguir os padrões arquiteturais da Produção (B), mantendo toda a funcionalidade já implementada. O protótipo continuaria servindo como referência comportamental, mas agora com uma estrutura que facilita a portabilidade direta para a Produção.
>
> **Princípio**: Não se trata de reescrever — é reorganizar. A lógica funcional dos agentes e serviços permanece intacta. O que muda é como eles se registram, se comunicam e se organizam.

### 14.1. Diagnóstico: Diferenças Estruturais entre A e B

| Aspecto | Protótipo A (atual) | Produção B (proposta) | Impacto da mudança |
|---------|--------------------|-----------------------|---------------------|
| **Estrutura de diretórios** | `agents/specialized/` (13 arquivos) + `services/` (~100 arquivos + 4 subpacotes: `ats_clients/`, `email_providers/`, `billing_providers/`, `ml/`) + `tools/` (8 arquivos, ~10.000L) | `domains/{domain_id}/` (cada domínio auto-contido) | **Alto** — reestruturação de diretórios |
| **Registro de agentes** | `AgentRegistry` singleton com mapeamento hardcoded em `_initialize_intent_mapping()` | `DomainRegistry` + decorator `@register_domain` (auto-registro) | **Médio** — novo registry + decorators |
| **Roteamento** | `IntentRouter` always-LLM (Claude Sonnet para classificar toda intent) | Cascata: memory → fast (keywords/regex ~80%) → LLM (~20%) | **Alto** — novo router + keyword patterns |
| **Contrato de agentes** | `BaseAgent(ABC)` com `process()`, `_register_actions()` | `DomainPrompt(ABC)` com `process_intent()`, `execute_action()`, `validate_context()` | **Médio** — adaptar interface base |
| **Workflow** | Orquestrador central síncrono (`orchestrator.py`) | `DomainWorkflow` (LangGraph: analyze_intent → execute → format) | **Alto** — cada domínio ganha workflow LangGraph |
| **Contexto** | Estado mantido no orchestrator + `ConversationMemory` | `DomainContext` com `sourcing_id`, `user_id`, `session_id`, `api_calls_history` | **Baixo** — wrapper sobre o existente |
| **Resposta** | `AgentResponse` dataclass | `DomainResponse` com `needs_confirmation`, `needs_clarification`, `suggestions` | **Baixo** — extensão da dataclass existente |
| **Tools** | `tool_registry` + `tool_executor` + `scope_config` | Actions dentro de cada domínio (`get_allowed_actions()`) | **Médio** — redistribuir tools por domínio |
| **Filas/Async** | Síncrono (FastAPI async) | RabbitMQ + Celery (filas priorizadas) | **Opcional** — pode simular com background tasks |
| **Guards** | `circuit_breaker.py`, validação manual | `FairnessGuard` + `FactChecker` como middleware | **Baixo** — renomear e posicionar como middleware |

### 14.2. Reestruturação de Diretórios (Proposta)

```
lia-agent-system/app/
├── domains/                              ← NOVO: cada domínio auto-contido
│   ├── base.py                           ← DomainPrompt (ABC), DomainContext, DomainResponse
│   ├── registry.py                       ← DomainRegistry + @register_domain
│   ├── workflow.py                       ← DomainWorkflow (LangGraph: intent→execute→format)
│   │
│   ├── job_management/                   ← Domínio 1: Gestão de Vagas
│   │   ├── __init__.py
│   │   ├── domain.py                     ← class JobManagementDomain(DomainPrompt)
│   │   ├── agents/
│   │   │   ├── wizard_agent.py           ← Extraído de job_intake_agent.py (conversa guiada)
│   │   │   ├── jd_extractor_agent.py     ← Extraído de job_intake_agent.py (parsing JD)
│   │   │   ├── jd_generator_agent.py     ← Extraído de job_intake_agent.py (geração JD)
│   │   │   ├── enrichment_agent.py       ← intelligence_layer_service + market_benchmark
│   │   │   └── validation_agent.py       ← confidence_policy_service
│   │   ├── services/                     ← Serviços específicos do domínio
│   │   │   ├── wizard_orchestrator.py    ← wizard_orchestrator_service.py (movido)
│   │   │   ├── jd_template_cache.py      ← jd_template_cache_service.py (movido)
│   │   │   └── field_inference.py        ← field_inference_service.py (movido)
│   │   ├── actions.py                    ← 20 actions (create_job, update_job, etc.)
│   │   └── prompts.py                    ← Prompts específicos do domínio
│   │
│   ├── sourcing/                         ← Domínio 2: Busca de Candidatos
│   │   ├── domain.py                     ← class SourcingDomain(DomainPrompt)
│   │   ├── agents/
│   │   │   └── sourcing_agent.py         ← sourcing_agent.py (movido)
│   │   ├── services/
│   │   │   ├── pearch_service.py         ← apify_service.py + apify_mcp_client.py
│   │   │   ├── search_analytics.py       ← search_analytics_service.py
│   │   │   ├── wrf_service.py            ← wrf_dynamic_k_service.py
│   │   │   └── es_analyzer.py            ← es_score_drop_analyzer.py
│   │   └── actions.py
│   │
│   ├── cv_screening/                     ← Domínio 3: Triagem Curricular
│   │   ├── domain.py
│   │   ├── agents/
│   │   │   └── triagem_agent.py          ← triagem_curricular_agent.py (movido)
│   │   ├── services/
│   │   │   ├── cv_parser.py              ← cv_parser.py (movido)
│   │   │   └── cv_scoring.py             ← cv_scoring_service.py (movido)
│   │   └── actions.py
│   │
│   ├── interviewing/                     ← Domínio 4: Entrevistas WSI
│   │   ├── domain.py
│   │   ├── agents/
│   │   │   └── entrevistador_agent.py    ← entrevistador_agent.py (movido)
│   │   ├── services/
│   │   │   ├── voice_service.py          ← voice_service.py (movido)
│   │   │   ├── deepgram_service.py       ← deepgram_service.py (movido)
│   │   │   └── wsi_voice_orchestrator.py ← wsi_voice_orchestrator.py (movido)
│   │   └── actions.py
│   │
│   ├── wsi_assessment/                   ← Domínio 5: Avaliação WSI
│   │   ├── domain.py
│   │   ├── agents/
│   │   │   └── avaliador_wsi_agent.py    ← avaliador_wsi_agent.py (movido)
│   │   ├── services/
│   │   │   ├── wsi_pipeline.py           ← wsi_screening_pipeline.py
│   │   │   ├── wsi_scorer.py             ← wsi_deterministic_scorer.py
│   │   │   ├── wsi_questions.py          ← wsi_question_service.py + generator + adjuster
│   │   │   ├── score_normalization.py    ← score_normalization_service.py
│   │   │   └── calibration.py            ← calibration_service.py + profiles + seniority_*
│   │   └── actions.py
│   │
│   ├── pipeline_management/              ← Domínio 6: Kanban/Pipeline + Analytics
│   │   ├── domain.py
│   │   ├── agents/
│   │   │   ├── analista_feedback_agent.py ← analista_feedback_agent.py (merge Comm+Analytics, movido)
│   │   │   ├── analytics_agent.py         ← analytics_agent.py (465L, DEPRECATED mas mantido)
│   │   │   └── communication_agent.py     ← communication_agent.py (390L, DEPRECATED mas mantido)
│   │   ├── services/
│   │   │   ├── stage_automation.py       ← stage_automation_engine.py + stage_transition
│   │   │   ├── candidate_comparison.py   ← candidate_comparison_service.py
│   │   │   └── candidate_feedback.py     ← candidate_feedback_service.py
│   │   └── actions.py
│   │
│   ├── scheduling/                       ← Domínio 7: Agendamento
│   │   ├── domain.py
│   │   ├── agents/
│   │   │   └── scheduling_agent.py       ← scheduling_agent.py (movido)
│   │   ├── services/
│   │   │   ├── calendar_service.py       ← calendar_service.py (movido)
│   │   │   └── scheduling_service.py     ← scheduling_service.py (movido)
│   │   └── actions.py
│   │
│   ├── communication/                    ← Domínio 8: Comunicação Multi-canal
│   │   ├── domain.py
│   │   ├── agents/
│   │   │   └── communication_agent.py    ← communication_agent.py (movido)
│   │   ├── services/
│   │   │   ├── email_service.py          ← email_service.py + providers (movidos)
│   │   │   ├── whatsapp_service.py       ← whatsapp_service.py + providers (movidos)
│   │   │   ├── teams_service.py          ← teams_service.py + auth + bot (movidos)
│   │   │   └── communication_dispatcher.py ← communication_dispatcher.py (movido)
│   │   └── actions.py
│   │
│   ├── ats_integration/                  ← Domínio 9: Integração ATS
│   │   ├── domain.py
│   │   ├── agents/
│   │   │   └── integrador_ats_agent.py   ← integrador_ats_agent.py (movido)
│   │   ├── services/
│   │   │   ├── ats_sync.py              ← ats_sync_service.py (movido)
│   │   │   └── clients/                 ← ats_clients/ (movido inteiro: base, gupy, pandape, merge, stackone)
│   │   └── actions.py
│   │
│   ├── recruiter_assistant/              ← Domínio 10: Assistente Pessoal do Recrutador
│   │   ├── domain.py                     ← class RecruiterAssistantDomain(DomainPrompt)
│   │   ├── agents/
│   │   │   └── recruiter_assistant_agent.py ← recruiter_assistant_agent.py (2.551L, movido)
│   │   ├── services/
│   │   │   └── personalization.py        ← recruiter_personalization_service.py (movido)
│   │   └── actions.py
│   │
│   └── task_planning/                    ← Domínio 11: Planejamento de Tarefas
│       ├── domain.py                     ← class TaskPlanningDomain(DomainPrompt)
│       ├── agents/
│       │   └── task_planner_agent.py     ← task_planner_agent.py (821L, movido)
│       └── actions.py
│
├── tools/                                ← MANTIDO: redistribuído por domínio ou mantido centralizado
│   ├── __init__.py                       ← (163L) Exports — mantido
│   ├── registry.py                       ← (145L) ToolRegistry — mantido
│   ├── executor.py                       ← (335L) ToolExecutor — mantido
│   ├── scope_config.py                   ← (335L) PromptScope + filtragem por escopo — mantido
│   ├── job_tools.py                      ← (699L) → domains/job_management/tools.py
│   ├── job_wizard_tools.py               ← (1.160L) → domains/job_management/tools.py
│   ├── candidate_tools.py               ← (1.116L) → domains/pipeline_management/tools.py
│   ├── communication_tools.py           ← (679L) → domains/communication/tools.py
│   ├── export_tools.py                   ← (579L) → shared/tools/export_tools.py
│   └── query_tools.py                    ← (4.786L) → domains/sourcing/tools.py + wsi_assessment/tools.py
│
├── shared/                               ← NOVO: serviços transversais compartilhados
│   ├── compliance/
│   │   ├── fairness_guard.py             ← Novo (inspirado em B)
│   │   ├── fact_checker.py               ← Novo (inspirado em B)
│   │   ├── lgpd_service.py              ← Existente (movido de services/)
│   │   └── audit_service.py             ← Existente (movido de services/)
│   ├── learning/
│   │   ├── learning_loop_service.py     ← Existente (movido)
│   │   ├── template_learning.py         ← Existente (movido)
│   │   └── outcome_learning.py          ← Novo
│   ├── governance/
│   │   ├── feature_flags.py             ← Existente (movido)
│   │   ├── policy_engine.py             ← Existente (movido de orchestrator/)
│   │   └── agent_monitoring.py          ← Existente (movido)
│   ├── intelligence/
│   │   ├── embedding_service.py         ← Existente (movido)
│   │   ├── semantic_search.py           ← Existente (movido)
│   │   └── ml/                          ← Existente (movido de services/ml/)
│   └── resilience/
│       ├── circuit_breaker.py           ← Existente (movido)
│       └── cache_manager.py             ← Existente (movido)
│
├── orchestrator/                         ← MANTIDO: refatorado
│   ├── orchestrator.py                   ← Simplificado — delega para DomainRegistry
│   ├── cascaded_router.py                ← NOVO: memory → fast → LLM (substitui intent_router.py)
│   ├── fast_router.py                    ← NOVO: keyword/regex patterns (~80% das queries)
│   ├── state_manager.py                  ← Mantido
│   └── task_planner.py                   ← Mantido
│
├── core/                                 ← MANTIDO
├── models/                               ← MANTIDO
├── schemas/                              ← MANTIDO
├── api/                                  ← MANTIDO (endpoints não mudam)
├── middleware/                            ← MANTIDO + FairnessGuard + FactChecker como middleware
└── config/                               ← MANTIDO
```

### 14.3. Mudanças por Componente — Detalhamento

#### 14.3.1. Novo contrato base: `DomainPrompt`

**Arquivo**: `domains/base.py`

**O que muda**: O `BaseAgent` atual (120L) define `agent_type`, `name`, `description`, `process()`. O novo `DomainPrompt` precisa adicionar:

| Método atual (`BaseAgent`) | Equivalente `DomainPrompt` | Status |
|----------------------------|---------------------------|:---:|
| `agent_type` → property | `domain_id` → atributo | Renomear |
| `name` → property | `domain_name` → atributo | Renomear |
| `description` → property | `description` → atributo | ✅ Igual |
| `_register_actions()` → método | `get_allowed_actions()` → método | Refatorar |
| `process()` → async | `process_intent()` + `execute_action()` | Dividir |
| — | `validate_context()` | Novo |
| — | `get_suggestions()` | Novo |
| — | `get_system_prompt()` | Novo |

**Impacto**: ~200 linhas (novo arquivo). `BaseAgent` continua existindo para compatibilidade; novos domínios usam `DomainPrompt`.

**Estratégia de migração**: Criar `DomainPrompt` como wrapper que herda de `BaseAgent`, adicionando os novos métodos. Isso permite migração gradual sem quebrar agentes existentes.

#### 14.3.2. `DomainRegistry` com auto-registro

**Arquivo**: `domains/registry.py`

**O que muda**: O `AgentRegistry` atual (401L) tem mapeamento hardcoded de intents → agents. O novo `DomainRegistry` usa decorator `@register_domain` para auto-registro.

```python
# ANTES (agent_registry.py — hardcoded):
self._intent_mapping = {
    "create_job_vacancy": AgentType.JOB_PLANNER,
    "search_candidates": AgentType.SOURCING,
    ...
}

# DEPOIS (domains/registry.py — auto-registro):
@register_domain
class JobManagementDomain(DomainPrompt):
    domain_id = "job_management"
    ...
```

**Impacto**: ~150 linhas (novo arquivo). `AgentRegistry` pode ser mantido como fallback durante migração.

#### 14.3.3. Roteamento cascateado

**Arquivos**: `orchestrator/cascaded_router.py` + `orchestrator/fast_router.py`

**O que muda**: O `IntentRouter` atual (385L) envia TODA query para LLM classificar. O novo roteamento segue a cascata de B:

```
1. Memory (cache): Query já vista antes? → Retorna rota cached
2. Fast (keywords/regex): "criar vaga", "buscar candidato" → Rota direta (~80%)
3. LLM (fallback): Queries ambíguas → Claude/Gemini classifica (~20%)
```

**Keyword patterns a implementar por domínio:**

| Domínio | Patterns (exemplos) |
|---------|---------------------|
| `job_management` | `criar vaga`, `editar vaga`, `gerar jd`, `requisitos`, `benefícios`, `salário` |
| `sourcing` | `buscar candidato`, `pesquisar`, `pearch`, `similar a`, `boolean` |
| `cv_screening` | `triagem`, `analisar cv`, `red flags`, `ranking` |
| `interviewing` | `entrevista`, `perguntas wsi`, `transcrever`, `conduzir` |
| `wsi_assessment` | `score wsi`, `avaliar`, `bloom`, `dreyfus`, `parecer`, `comparar candidatos` |
| `scheduling` | `agendar`, `reagendar`, `cancelar`, `disponibilidade`, `horário` |
| `communication` | `email`, `whatsapp`, `enviar`, `template`, `contato`, `follow-up` |
| `pipeline_management` | `kanban`, `mover candidato`, `aprovar`, `reprovar`, `gate`, `funil` |

**Impacto**: ~300 linhas (2 novos arquivos). O `IntentRouter` existente se torna o "passo 3" (fallback LLM) da cascata.

#### 14.3.4. Decomposição do `job_intake_agent.py` (4.132L)

**O que muda**: Este é o agente mais extenso e concentra responsabilidades de 5 agentes propostos em B. A decomposição:

| Trecho atual | Destino em B | Linhas ~approx |
|-------------|-------------|:-:|
| Conversa guiada de criação (wizard steps, stage transitions) | `job_management/agents/wizard_agent.py` | ~1.200 |
| Parsing de JD colada/importada (`JD_EXTRACTION_PROMPT`, `extract_requirements`) | `job_management/agents/jd_extractor_agent.py` | ~500 |
| Geração de JD (`generate_jd`, formatação) | `job_management/agents/jd_generator_agent.py` | ~400 |
| Enriquecimento de mercado (salário, skills, competências) | `job_management/agents/enrichment_agent.py` | ~600 |
| Validação e qualidade (`validate_completeness`, WSI Quality Score) | `job_management/agents/validation_agent.py` | ~300 |
| Prompts, constantes, tipos | `job_management/prompts.py` + `actions.py` | ~1.100 |

**Resultado**: 1 arquivo de 4.132L → 6 arquivos menores, cada um com responsabilidade clara.

#### 14.3.5. Nota sobre o merge Communication + Analytics → ANALYST_FEEDBACK

O protótipo mantém 3 arquivos separados que cobrem o domínio "pipeline_management":

| Arquivo | Linhas | Status | AgentType |
|---------|:------:|--------|-----------|
| `analista_feedback_agent.py` | ~109 | **Ativo** — merge de Communication + Analytics | `ANALYST_FEEDBACK` |
| `analytics_agent.py` | ~465 | **Deprecated** — lógica migrada para analista_feedback | `ANALYTICS` (deprecated) |
| `communication_agent.py` | ~390 | **Deprecated** — lógica migrada para analista_feedback | `COMMUNICATION` (deprecated) |

Na migração, os 3 arquivos vão para `domains/pipeline_management/agents/`. Os deprecated ficam como referência até a limpeza (Fase 10).

#### 14.3.6. Redistribuição do `services/` (não é flat — tem 4 subpacotes)

**O que muda**: A pasta `services/` atual tem ~100 arquivos individuais **mais 4 subpacotes** (`ats_clients/`, `email_providers/`, `billing_providers/`, `ml/`). Os serviços seriam redistribuídos:

| Serviço atual | Destino |
|--------------|---------|
| `wizard_orchestrator_service.py` | `domains/job_management/services/` |
| `wsi_screening_pipeline.py`, `wsi_*.py` (7 arquivos) | `domains/wsi_assessment/services/` |
| `cv_parser.py`, `cv_scoring_service.py` | `domains/cv_screening/services/` |
| `scheduling_service.py`, `calendar_service.py` | `domains/scheduling/services/` |
| `email_service.py`, `whatsapp_*.py`, `teams_*.py` | `domains/communication/services/` |
| `stage_automation_engine.py`, `candidate_*.py` | `domains/pipeline_management/services/` |
| `sourcing_pipeline_service.py`, `apify_*.py` | `domains/sourcing/services/` |
| `ats_sync_service.py`, `ats_clients/` | `domains/ats_integration/services/` |
| `learning_loop_service.py`, `template_learning_service.py` | `shared/learning/` |
| `feature_flag_service.py`, `agent_monitoring_service.py` | `shared/governance/` |
| `circuit_breaker.py`, `cache_manager_service.py` | `shared/resilience/` |
| `audit_service.py`, `lgpd_*.py` | `shared/compliance/` |
| `embedding_service.py`, `semantic_search_service.py` | `shared/intelligence/` |
| `llm.py`, `conversation_memory.py`, `event_dispatcher.py` | `shared/` (raiz — usados por todos) |

**Serviços que ficam em `shared/`** (usados por múltiplos domínios): LLM, conversation memory, event dispatcher, structured output, token tracking.

**Impacto**: Nenhuma mudança de código — apenas mover arquivos e atualizar imports. Pode ser feito incrementalmente (um domínio por vez).

#### 14.3.7. Redistribuição do `tools/` (9.997L total)

**O que muda**: O protótipo tem um sistema de tools centralizado em `app/tools/` com 8 arquivos e ~10.000 linhas. Na Produção B, as actions (equivalente de tools) ficam dentro de cada domínio. A infraestrutura (registry, executor, scope_config) permanece centralizada; os tools específicos migram para seus domínios:

| Tool atual | Linhas | Destino no domínio |
|-----------|:------:|-------------------|
| `job_tools.py` | 699 | `domains/job_management/tools.py` |
| `job_wizard_tools.py` | 1.160 | `domains/job_management/tools.py` (merge com job_tools) |
| `candidate_tools.py` | 1.116 | `domains/pipeline_management/tools.py` |
| `communication_tools.py` | 679 | `domains/communication/tools.py` |
| `export_tools.py` | 579 | `shared/tools/export_tools.py` (usado por múltiplos domínios) |
| `query_tools.py` | 4.786 | Dividido: sourcing queries → `domains/sourcing/tools.py`, WSI queries → `domains/wsi_assessment/tools.py` |
| `registry.py` | 145 | Mantido em `tools/registry.py` (infraestrutura) |
| `executor.py` | 335 | Mantido em `tools/executor.py` (infraestrutura) |
| `scope_config.py` | 335 | Mantido em `tools/scope_config.py` (infraestrutura) |

#### 14.3.8. `DomainWorkflow` com LangGraph

**Arquivo**: `domains/workflow.py`

**O que muda**: Hoje o orchestrator executa tudo em sequência síncrona. O padrão B define um workflow LangGraph de 3 nós reutilizável:

```
analyze_intent → execute → format
```

Cada domínio herda esse workflow. O nó `analyze_intent` chama `domain.process_intent()`, o nó `execute` chama `domain.execute_action()`, e o nó `format` usa um `TemplateFormatter` para construir a resposta.

**Impacto**: ~250 linhas (novo arquivo). O orchestrator atual se simplifica — em vez de gerenciar tudo, apenas resolve o domínio e dispara o workflow.

#### 14.3.9. Simplificação do Orchestrator

**Arquivo**: `orchestrator/orchestrator.py` (1.112L → ~400L)

**O que muda**: O orchestrator atual (1.112L) concentra roteamento, execução, formatação e estado. Com a nova arquitetura:

```python
# ANTES: orchestrator faz tudo
async def process(self, message, context):
    intent = self.intent_router.classify(message)  # always LLM
    agent = self.agent_registry.get(intent)
    response = await agent.process(message, context)
    return self.format_response(response)

# DEPOIS: orchestrator delega
async def process(self, message, context):
    domain = self.cascaded_router.route(message)    # memory→fast→LLM
    domain_context = DomainContext.from_request(context)
    response = await self.domain_workflow.process(domain, domain_context, message)
    return response  # já formatado pelo workflow
```

**Resultado**: Orchestrator perde ~700 linhas de lógica que migram para os domínios e o workflow.

### 14.4. Novos Componentes a Criar (inspirados em B)

| Componente | Inspiração B | Propósito | Linhas ~est |
|-----------|-------------|-----------|:-----------:|
| `FairnessGuard` middleware | `FairnessGuard` existente em B | Bloqueia filtros discriminatórios antes de chegar ao domínio | ~150 |
| `FactChecker` middleware | `FactChecker` existente em B | Valida claims da IA contra dados reais antes de responder | ~200 |
| `CascadedRouter` | Router cascateado de B | Memory → Fast → LLM routing | ~200 |
| `FastRouter` | Keyword routing de B (~80%) | Patterns por domínio | ~150 |
| `DomainWorkflow` | `DomainWorkflow` de B | LangGraph: intent→execute→format | ~250 |
| `DomainPrompt` ABC | `DomainPrompt` de B | Contrato base para domínios | ~200 |
| `DomainRegistry` | `DomainRegistry` de B | Auto-registro via decorator | ~150 |
| **Total** | | | **~1.300** |

### 14.5. O que NÃO muda

| Componente | Motivo para manter |
|-----------|-------------------|
| **Modelos de dados** (`models/`) | Schema PostgreSQL é independente da arquitetura de agentes |
| **Schemas Pydantic** (`schemas/`) | Contratos de API são ortogonais à organização interna |
| **Endpoints API** (`api/v1/`) | URLs públicas não mudam — apenas a implementação interna |
| **Middleware existente** (`middleware/`) | Auth, CORS, logging — complementados com FairnessGuard/FactChecker |
| **Config** (`config/`) | Feature flags, settings — posição no diretório é irrelevante |
| **Migrations** (`migrations/`) | Histórico de DB — nunca alterar |
| **Templates de dados** (`data/templates/`) | Dados estáticos — independentes |
| **ConversationMemory** | Já existe e funciona — B também usa. Mantém como `shared/` |
| **LLM Service** | Abstração de LLM — já compatível com Gemini/Claude/OpenAI |

### 14.6. Plano de Migração Incremental (sem quebrar nada)

A migração pode ser feita **um domínio por vez**, sem parar o sistema:

```
FASE 0 — Infraestrutura (pré-requisito):
├── Criar domains/base.py (DomainPrompt ABC)
├── Criar domains/registry.py (DomainRegistry + @register_domain)
├── Criar domains/workflow.py (DomainWorkflow LangGraph)
├── Criar orchestrator/cascaded_router.py + fast_router.py
├── Criar shared/ com serviços transversais (mover, não reescrever)
└── Manter AgentRegistry + IntentRouter como fallback

FASE 1 — Migrar primeiro domínio (sourcing — já o mais próximo de B):
├── Criar domains/sourcing/domain.py
├── Mover sourcing_agent.py → domains/sourcing/agents/
├── Mover query_tools.py (parcial) → domains/sourcing/tools.py
├── Mover serviços relacionados → domains/sourcing/services/
├── Registrar com @register_domain
├── Testar roteamento cascateado para intents de sourcing
└── Se funcionar → desativar rotas antigas no AgentRegistry

FASE 2 — Migrar job_management (o mais complexo):
├── Decompor job_intake_agent.py em 5 agentes menores
├── Mover job_tools.py + job_wizard_tools.py → domains/job_management/tools.py
├── Criar domains/job_management/
├── Mover serviços relacionados
└── Testar wizard conversacional com novo workflow

FASE 3–8 — Migrar domínios restantes (1 por vez):
├── cv_screening, interviewing, wsi_assessment
├── pipeline_management (inclui analytics_agent + communication_agent deprecated + candidate_tools)
├── scheduling, communication (inclui email_providers/ + billing_providers/)
└── ats_integration (inclui ats_clients/ inteiro)

FASE 9 — Migrar recruiter_assistant + task_planning:
├── Mover recruiter_assistant_agent.py (2.551L) → domains/recruiter_assistant/
├── Mover task_planner_agent.py (821L) → domains/task_planning/
└── Atualizar IntentRouter para novos caminhos

FASE 10 — Limpeza:
├── Remover AgentRegistry antigo
├── Remover IntentRouter antigo
├── Remover pasta agents/specialized/ (vazia)
├── Remover tools/ centralizados (já redistribuídos por domínio)
├── Remover serviços da pasta services/ que foram movidos
└── Atualizar imports em toda a codebase
```

### 14.7. Estimativa de Esforço da Migração

| Fase | Descrição | Linhas novas | Linhas movidas | Complexidade |
|:----:|-----------|:------------:|:--------------:|:------------:|
| 0 | Infraestrutura base (DomainPrompt, Registry, Workflow, Router) | ~1.300 | 0 | **Alta** |
| 1 | Migrar sourcing + query_tools parcial | ~100 | ~2.500 | **Média** |
| 2 | Migrar job_management + decomposição + job_tools/wizard_tools | ~300 | ~7.500 | **Alta** |
| 3 | Migrar cv_screening | ~100 | ~2.000 | **Média** |
| 4 | Migrar interviewing | ~100 | ~2.000 | **Média** |
| 5 | Migrar wsi_assessment + query_tools parcial | ~100 | ~4.500 | **Média-Alta** |
| 6 | Migrar pipeline_management (inclui analytics/communication deprecated) + candidate_tools | ~100 | ~5.000 | **Média** |
| 7 | Migrar scheduling | ~100 | ~2.500 | **Baixa** |
| 8 | Migrar communication + ats_integration (inclui ats_clients/ + email_providers/ + billing_providers/) | ~100 | ~5.500 | **Média** |
| 9 | Migrar recruiter_assistant + task_planning | ~100 | ~3.500 | **Média** |
| 10 | Limpeza (remover agents/specialized/, tools/ vazios, AgentRegistry antigo) | 0 | 0 | **Baixa** |
| | **Total** | **~2.400** | **~35.000** | |

> **Nota**: A maior parte do trabalho é **mover arquivos e atualizar imports** (~35.000 linhas movidas, incluindo os ~10.000L do sistema de tools e ~4.200L dos agentes RecruiterAssistant e TaskPlanner), não escrever código novo (~2.400 linhas). A lógica funcional dos agentes, tools e serviços permanece 100% intacta.

### 14.8. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|:---:|:---:|---------|
| Imports quebrados após mover arquivos | Alta | Médio | Migrar 1 domínio por vez + testes de import em CI |
| Regressão no roteamento cascateado | Média | Alto | Manter IntentRouter como fallback até validar fast router |
| Decomposição do job_intake_agent quebra wizard | Média | Alto | Testes de integração do wizard antes e depois |
| Serviços compartilhados referenciados de múltiplos domínios | Alta | Baixo | `shared/` mantém path curtos; re-exports via `__init__.py` |
| Performance do LangGraph workflow vs. chamada direta | Baixa | Baixo | Benchmark antes/depois; LangGraph é leve |

### 14.9. Benefícios Esperados da Migração

| Benefício | Descrição |
|-----------|-----------|
| **Portabilidade direta para B** | Domínios do protótipo podem ser copiados para a Produção com ajustes mínimos (trocar LLM, adicionar RabbitMQ) |
| **Onboarding mais rápido** | Novo desenvolvedor entende `domains/scheduling/` sem precisar navegar 100 arquivos em `services/` |
| **Testes isolados** | Cada domínio pode ser testado independentemente |
| **Custo LLM -80%** | Fast routing elimina chamadas LLM para intents óbvias |
| **Escalabilidade** | Novos domínios se adicionam com `@register_domain` sem alterar orchestrator |
| **Consistência A↔B** | Mesma estrutura em ambos os sistemas — documentação serve para os dois |

---

## 15. Mapa de Portabilidade: O que a Produção Pode Aproveitar do Protótipo

> **Objetivo**: Para cada grupo de arquivos do protótipo (A), indicar o **grau de reaproveitamento** pela equipe de Produção (B) e o tipo de adaptação necessária. Isso permite que o time de B planeje exatamente o que copiar, o que adaptar, e o que serve apenas como referência funcional.

### 15.1. Legenda de Classificação

| Grau | Significado | Esforço para B |
|:----:|-------------|:--------------:|
| 🟢 **Direto** | Copiar e usar com ajustes mínimos (imports, config) | **Baixo** |
| 🟡 **Adaptação Menor** | Funciona com mudanças pontuais (renomear interface, trocar provider) | **Baixo-Médio** |
| 🟠 **Adaptação Estrutural** | Lógica aproveitável, mas precisa ser reorganizada/decomposta | **Médio** |
| 🔴 **Referência** | Serve como spec funcional — mocks, stubs, ou padrões a reimplementar | **Alto** |

### 15.2. Agentes Especializados (~33.800L)

> **⚠️ ATUALIZADO PÓS-MIGRAÇÃO**: Os graus abaixo refletem o estado atual do protótipo após a migração domain-driven. Itens que eram 🟠 e foram efetivamente decompostos/reestruturados no protótipo estão agora marcados com o grau real.

| Arquivo | Linhas | Grau | Observação |
|---------|:------:|:----:|------------|
| `job_intake_agent.py` | 4.132 | 🟢 | ~~Precisava decompor~~ → **DECOMPOSTO** em 6 agentes no domínio `job_management/agents/`: job_intake, job_drafting, job_insights, job_benefits_comp, job_lifecycle, job_rubric. Transferência direta. |
| `recruiter_assistant_agent.py` | 2.551 | 🟢 | ~~Adaptar para DomainPrompt~~ → **MIGRADO** para `domains/recruiter_assistant/agents/`. Já usa DomainPrompt. |
| `analista_feedback_agent.py` | 2.068 | 🟢 | ~~Adaptar para DomainPrompt~~ → **MIGRADO** para `domains/analytics/agents/`. Já usa DomainPrompt. |
| `sourcing_agent.py` | 1.881 | 🟢 | **MIGRADO** para `domains/sourcing/agents/`. Transferência direta. |
| `avaliador_wsi_agent.py` | 1.596 | 🟢 | **MIGRADO** para `domains/cv_screening/agents/`. IP proprietário, transferência direta. |
| `scheduling_agent.py` | 1.512 | 🟡 | **MIGRADO** para `domains/interview_scheduling/agents/`. Trocar mock de calendar por integração real. |
| `triagem_curricular_agent.py` | 1.384 | 🟢 | **MIGRADO** para `domains/cv_screening/agents/`. Transferência direta. |
| `entrevistador_agent.py` | 1.117 | 🟡 | **MIGRADO** para `domains/interview_scheduling/agents/`. Adaptar providers de voz (VoiceProvider ABC criada). |
| `task_planner_agent.py` | 821 | 🟢 | **MIGRADO** para `domains/automation/agents/`. Já usa DomainPrompt. |
| `integrador_ats_agent.py` | 704 | 🟡 | **MIGRADO** para `domains/ats_integration/agents/`. ATSProviderFactory com config injection via env vars. |
| `analytics_agent.py` | 465 | 🔴 | Deprecated (mergeado em analista_feedback). Referência apenas. |
| `screening_agent.py` | 443 | 🔴 | Deprecated (split em triagem + entrevistador + avaliador_wsi). Referência. |
| `communication_agent.py` | 390 | 🔴 | Deprecated (mergeado em analista_feedback). Referência. |

**Subtotal aproveitável**: ~21.400L direto + ~3.300L adaptação menor = **~24.700L** (de ~33.800L) — ⬆️ melhoria de ~2.200L vs análise anterior

#### Agents — Infraestrutura e Suporte (~8.500L)

| Arquivo | Linhas | Grau | Observação |
|---------|:------:|:----:|------------|
| `agent_prompts.py` | 1.567 | 🟢 | Prompts calibrados — IP valioso, transferência direta |
| `conversation.py` | 1.657 | 🟡 | Fluxo conversacional LangGraph — adaptar para DomainWorkflow |
| `job_vacancy_nodes.py` | 1.543 | 🟡 | Nós LangGraph de vaga — mover para domain job_management |
| `sourcing_engagement_nodes.py` | 1.354 | 🟢 | Nós de engagement — mover para domain sourcing |
| `nodes.py` | 1.292 | 🟡 | Nós genéricos — distribuir por domínio ou shared |
| `prompt_registry.py` | 496 | 🟢 | Registry de prompts — transferência direta |
| `job_planner_examples.py` | 429 | 🟢 | Few-shot examples — IP valioso |
| `pipeline_examples.py` | 676 | 🟢 | Few-shot examples — IP valioso |
| `sourcing_examples.py` | 528 | 🟢 | Few-shot examples — IP valioso |
| `job_wizard_graph.py` | 401 | 🟡 | Grafo do wizard — adaptar para DomainWorkflow |
| `interview_scheduling_nodes.py` | 418 | 🟡 | Nós de agendamento — mover para domain scheduling |
| `base_agent.py` | 398 | 🟢 | ~~Será substituído por DomainPrompt~~ → **DomainPrompt criado** em `domains/base.py`. Base class transfere como referência direta. |
| `agent_registry.py` | 400 | 🟢 | ~~Será substituído por DomainRegistry~~ → **DomainRegistry criado** em `domains/registry.py`. Mapeamento de intents funcional. |
| `state_machine.py` | 467 | 🟡 | Máquina de estados — transferência direta |
| Robustness (`robustness/*.py` — 6 arquivos) | ~2.300 | 🟢 | Circuit breaker, input validation, error handling, defensive prompts — tudo transfere direto |

### 15.3. Sistema de Tools (~10.000L)

| Arquivo | Linhas | Grau | Observação |
|---------|:------:|:----:|------------|
| `query_tools.py` | 4.786 | 🟢 | ~~Monolítico~~ → **DECOMPOSTO** em 3 módulos por domínio: `sourcing/tools/query_tools.py` (1.207L, 9 funções), `job_management/tools/query_tools.py` (822L, 5 funções), `analytics/tools/analytics_query_tools.py` (2.829L, 19 funções). Backward compat mantida. |
| `job_wizard_tools.py` | 1.160 | 🟢 | **MIGRADO** para `domains/job_management/tools/`. Transferência direta. |
| `candidate_tools.py` | 1.116 | 🟢 | **MIGRADO** para `domains/cv_screening/tools/`. Transferência direta. |
| `job_tools.py` | 699 | 🟢 | **MIGRADO** para `domains/job_management/tools/`. Transferência direta. |
| `communication_tools.py` | 679 | 🟡 | **MIGRADO** para `domains/communication/tools/`. Adaptar providers reais. |
| `export_tools.py` | 579 | 🟢 | Exportar candidatos, relatórios. Transferência direta (shared). |
| `registry.py` | 145 | 🟡 | Infra de registro — **DomainActions implementado** nos 9 domínios. Registry mantém backward compat. |
| `executor.py` | 335 | 🟡 | Executor — **DomainPrompt.execute_action()** existe. Executor original serve como adapter. |
| `scope_config.py` | 335 | 🟡 | Escopo por prompt — mapeia para validate_context() dos domínios. |

**Subtotal aproveitável**: ~9.200L direto + ~800L adaptação menor = **~10.000L** (de ~10.000L) — ⬆️ **100% aproveitável** pós-decomposição

### 15.4. Serviços de Negócio (~115.600L, 189 arquivos)

#### 15.4.1. Domínio Job Management

| Serviço | Linhas | Grau | Observação |
|---------|:------:|:----:|------------|
| `automation_service.py` | 1.234 | 🟢 | Motor de automação de vagas |
| `job_insights_service.py` | 984 | 🟢 | Insights de mercado para vagas |
| `job_embedding_service.py` | 966 | 🟢 | Embeddings de vagas para busca semântica |
| `jd_template_service.py` | 994 | 🟢 | Templates de JD — 361 templates curados |
| `job_analytics_prompt_service.py` | 863 | 🟢 | Prompts de analytics de vagas |
| `lia_field_config_service.py` | 887 | 🟢 | Configuração de campos LIA |
| `company_configuration_service.py` | 808 | 🟢 | Config da empresa — benefícios, cultura |
| `compensation_analysis_service.py` | 785 | 🟢 | Análise de remuneração |
| `intelligence_layer_service.py` | 755 | 🟢 | Camada de inteligência — enriquecimento |
| `market_benchmark_service.py` | 702 | 🟡 | Benchmarks de mercado — adaptar fontes de dados reais |
| `automation_trigger_service.py` | 742 | 🟢 | Triggers de automação |
| `jd_enrichment_service.py` | 695 | 🟢 | Enriquecimento de JD com 5 serviços orquestrados |
| `jd_generator_service.py` | 761 | 🟢 | Geração de JD com IA |
| `job_vacancy_service.py` | 700 | 🟢 | CRUD de vagas |
| `automation_scheduler.py` | 611 | 🟢 | Agendador de automações |
| `wizard_orchestrator_service.py` | 589 | 🟢 | Orquestrador do wizard |
| `jd_import_service.py` | 586 | 🟡 | Import de JD — adaptar formatos reais |
| `wizard_data_priority_service.py` | 563 | 🟢 | Priorização de dados do wizard |
| `wizard_analytics_service.py` | 430 | 🟢 | Analytics do wizard |
| `automation_handlers.py` | 530 | 🟢 | Handlers de automação |
| `benefits_service.py` | 552 | 🟢 | Gestão de benefícios |
| `suggestion_interaction_service.py` | 514 | 🟢 | Interação com sugestões da LIA |
| `job_board_service.py` | 498 | 🟡 | Publicação em job boards — adaptar integrações reais |
| `job_context_service.py` | 460 | 🟢 | Contexto da vaga |
| `job_clone_service.py` | 434 | 🟢 | Clonagem de vagas |
| `job_alert_service.py` | 392 | 🟢 | Alertas de vagas |
| `job_audit_service.py` | 318 | 🟢 | Auditoria de vagas |
| `jd_template_cache_service.py` | 312 | 🟢 | Cache de templates |
| `archetype_builder_service.py` | 306 | 🟡 | Construtor de arquétipos |
| `confidence_policy_service.py` | 268 | 🟢 | Políticas de confiança |
| `job_qualification_service.py` | 164 | 🟢 | Qualificação de vagas |
| `manager_inference_service.py` | 420 | 🟡 | Inferência de gestor |
| `job_status_webhook_service.py` | 471 | 🟡 | Webhooks de status — adaptar URLs reais |
| `job_pattern_service.py` | 939 | 🟢 | Detecção de padrões em vagas |
| `job_report_service.py` | 797 | 🟢 | Relatórios de vagas |

**Subtotal**: ~21.000L — **90% direto** (🟢)

#### 15.4.2. Domínio WSI Assessment

| Serviço | Linhas | Grau | Observação |
|---------|:------:|:----:|------------|
| `wsi_service.py` | 1.295 | 🟢 | Core WSI — IP proprietário, transferência direta |
| `lia_score_service.py` | 1.303 | 🟢 | Sistema de scoring LIA |
| `calibration_profiles.py` | 995 | 🟢 | Perfis de calibração contextual — 13 perfis profissionais |
| `seniority_resolver.py` | 882 | 🟢 | Resolução multi-sinal de senioridade |
| `wsi_question_service.py` | 879 | 🟢 | Gestão de perguntas WSI |
| `wsi_voice_orchestrator.py` | 780 | 🟡 | Orquestrador de voz WSI — adaptar providers |
| `wsi_question_generator.py` | 600 | 🟢 | Geração de perguntas com Gemini |
| `wsi_screening_pipeline.py` | 586 | 🟢 | Pipeline de screening |
| `seniority_context_calibrator.py` | 599 | 🟢 | Calibrador contextual |
| `wsi_deterministic_scorer.py` | 558 | 🟢 | Scorer determinístico |
| `calibration_service.py` | 474 | 🟢 | Serviço de calibração |
| `seniority_utils.py` | 393 | 🟢 | Utilitários de senioridade |
| `seniority_jd_analyzer.py` | 391 | 🟢 | Análise de JD para senioridade |
| `screening_question_set_service.py` | 325 | 🟢 | Gestão de sets de perguntas |
| `wsi_question_adjuster.py` | 297 | 🟢 | Ajuste de perguntas WSI |
| `score_normalization_service.py` | 176 | 🟢 | Normalização de scores |
| `eligibility_verification_service.py` | 374 | 🟢 | Verificação de elegibilidade |

**Subtotal**: ~10.900L — **95%+ direto** (🟢) — Este é o IP mais valioso do protótipo

#### 15.4.3. Domínio Sourcing

| Serviço | Linhas | Grau | Observação |
|---------|:------:|:----:|------------|
| `sourcing_pipeline_service.py` | 1.102 | 🟢 | Pipeline de sourcing completo |
| `pearch_service.py` | 1.042 | 🟡 | Integração Pearch — adaptar credenciais/endpoints reais |
| `company_scraper_service.py` | 773 | 🟡 | Scraper de empresas — adaptar fontes |
| `search_analytics_service.py` | 597 | 🟢 | Analytics de busca |
| `vacancy_search_service.py` | 511 | 🟢 | Busca de vagas |
| `apify_mcp_client.py` | 473 | 🟡 | Cliente MCP Apify — adaptar para prod |
| `apify_service.py` | 276 | 🟡 | Serviço Apify |
| `evaluation_criteria_service.py` | 465 | 🟢 | Critérios de avaliação (André's Methodology) |
| `es_score_drop_analyzer.py` | 99 | 🟢 | Análise de queda de score ES |
| `pgv_gap_analyzer.py` | 90 | 🟢 | Análise de gap PGVector |
| `wrf_dynamic_k_service.py` | 81 | 🟢 | WRF dinâmico |
| `pre_wrf_filter_service.py` | 104 | 🟢 | Pré-filtro WRF |
| `semantic_search_service.py` | 442 | 🟢 | Busca semântica |

**Subtotal**: ~6.000L — **80% direto** (🟢)

#### 15.4.4. Domínio Communication

| Serviço | Linhas | Grau | Observação |
|---------|:------:|:----:|------------|
| `email_service.py` | 2.864 | 🟡 | ~~Monolítico~~ → **DECOMPOSTO** em 3 arquivos: `email_service.py` (1.019L lógica), `email_templates_data.py` (1.773L templates), `email_schemas.py` (schemas Pydantic). Providers com ABC + config injection. |
| `communication_service.py` | 2.445 | 🟡 | Core de comunicação multi-canal |
| `notification_service.py` | 1.261 | 🟡 | Notificações — adaptar canais reais |
| `recruitment_email_templates.py` | 959 | 🟢 | Templates de email — conteúdo valioso |
| `data_request_whatsapp_service.py` | 794 | 🟡 | LGPD + WhatsApp — WhatsAppProvider ABC + Factory existem, adaptar credenciais reais |
| `microsoft_graph_service.py` | 764 | 🔴 | Teams/Outlook — precisa de tenant real |
| `openmic_service.py` | 720 | 🟡 | OpenMic — adaptar credenciais |
| `whatsapp_service.py` | 553 | 🟡 | WhatsApp core |
| `whatsapp_meta_service.py` | 502 | 🟡 | WhatsApp Meta API |
| `teams_service.py` | 477 | 🔴 | Teams — precisa de ambiente real |
| `whatsapp_twilio_service.py` | 417 | 🟡 | WhatsApp Twilio |
| `communication_history_service.py` | 364 | 🟢 | Histórico |
| `communication_dispatcher.py` | 359 | 🟡 | Dispatcher multi-canal |
| `deepgram_service.py` | 331 | 🟡 | Transcrição — adaptar API key |
| `gemini_voice_service.py` | 337 | 🟡 | Voz Gemini |
| `voice_service.py` | 417 | 🟡 | Voz genérica |
| `teams_recording_service.py` | 597 | 🔴 | Gravação Teams — ambiente real |
| `teams_auth.py` | 119 | 🔴 | Auth Teams |
| `teams_bot.py` | 299 | 🔴 | Bot Teams |
| `teams_simple.py` | 269 | 🔴 | Teams simplificado |
| `whatsapp_factory.py` | 188 | 🟢 | Factory pattern |
| `whatsapp_provider.py` | 192 | 🟡 | Provider base |
| `email_providers.py` | 147 | 🟡 | Providers de email |
| `otp_service.py` | 176 | 🟡 | OTP |
| Email providers (`email_providers/*.py`) | ~1.100 | 🟡 | SendGrid + Resend — adaptar keys |
| Billing providers (`billing_providers/*.py`) | ~1.700 | 🔴 | Iugu + Vindi — stubs, reimplementar |

**Subtotal**: ~17.600L — **60% direto/adaptação menor** + **15% adaptação estrutural** + **25% referência** — ⬆️ melhoria pós-decomposição email + ABC providers

#### 15.4.5. Domínio Pipeline Management

| Serviço | Linhas | Grau | Observação |
|---------|:------:|:----:|------------|
| `candidate_comparison_service.py` | 958 | 🟢 | Comparação de candidatos |
| `candidate_report_service.py` | 927 | 🟢 | Relatórios de candidato |
| `stage_transition_automation.py` | 692 | 🟢 | Automação de transição de etapas |
| `candidate_enrichment_service.py` | 627 | 🟡 | Enriquecimento — adaptar fontes de dados |
| `candidate_feedback_service.py` | 598 | 🟢 | Feedback pós-screening |
| `pipeline_stage_service.py` | 868 | 🟢 | Gestão de etapas |
| `kanban_assistant_service.py` | 464 | 🟢 | Assistente Kanban |
| `stage_automation_engine.py` | 450 | 🟢 | Motor de automação de stages |
| `predictive_analytics_service.py` | 866 | 🟡 | Analytics preditivo — adaptar modelos ML |
| `pipeline_service.py` | 314 | 🟢 | Pipeline core |
| `pre_qualification_service.py` | 354 | 🟢 | Pré-qualificação |

**Subtotal**: ~7.100L — **85% direto** (🟢)

#### 15.4.6. Domínio CV Screening

| Serviço | Linhas | Grau | Observação |
|---------|:------:|:----:|------------|
| `cv_parser.py` | 600 | 🟢 | Parser de CV |
| `cv_scoring_service.py` | 407 | 🟢 | Scoring de CV |
| `interview_transcript_analysis_service.py` | 1.035 | 🟢 | Análise de transcrição |

**Subtotal**: ~2.000L — **100% direto** (🟢)

#### 15.4.7. Domínio Scheduling

| Serviço | Linhas | Grau | Observação |
|---------|:------:|:----:|------------|
| `scheduling_service.py` | 1.020 | 🟡 | Agendamento — adaptar integração de calendário real |
| `calendar_service.py` | 305 | 🟡 | Calendário — adaptar Google Calendar/Outlook real |

**Subtotal**: ~1.300L — **100% adaptação menor** (🟡)

#### 15.4.8. Domínio ATS Integration

| Serviço | Linhas | Grau | Observação |
|---------|:------:|:----:|------------|
| `ats_sync_service.py` | 943 | 🟡 | **MIGRADO** para `domains/ats_integration/services/`. ATSProviderFactory com config injection via env vars (ATS_{PROVIDER}_API_KEY). |
| `merge_ats_service.py` | 443 | 🟡 | **MIGRADO**. ATSClient ABC implementado, config injection via factory. |
| `gupy_service.py` | 301 | 🟡 | **MIGRADO**. GupyClient com ABC + ATSClientConfig. Adaptar credenciais reais via env. |
| `pandape_service.py` | 260 | 🟡 | **MIGRADO**. PandapeClient com ABC + ATSClientConfig. Idem. |
| ATS clients (`ats_clients/*.py`) | ~1.900 | 🟡 | Base ABC + 4 providers + **ATSProviderFactory** criada em `shared/providers/ats_factory.py`. Config injection completa. |
| `ats_job_history_service.py` | 548 | 🟢 | Histórico ATS — transferência direta |

**Subtotal**: ~4.400L — **100% aproveitável** (🟢+🟡) — ⬆️ ATSProviderFactory + config injection eliminam adaptação estrutural

#### 15.4.9. Serviços Compartilhados (shared/)

| Serviço | Linhas | Grau | Observação |
|---------|:------:|:----:|------------|
| `learning_loop_service.py` | 1.049 | 🟢 | Learning loop — IP valioso |
| `learning_hub_service.py` | 1.332 | 🟢 | Hub de aprendizado |
| `feedback_learning_service.py` | 850 | 🟢 | Learning por feedback |
| `template_learning_service.py` | 401 | 🟢 | Learning por templates |
| `llm.py` | 840 | 🟢 | Abstração LLM multi-provider |
| `conversation_memory.py` | 852 | 🟢 | Memória conversacional |
| `event_dispatcher.py` | 591 | 🟢 | Dispatcher de eventos |
| `feature_flag_service.py` | 315 | 🟢 | Feature flags |
| `agent_monitoring_service.py` | 580 | 🟢 | Monitoramento de agentes |
| `circuit_breaker.py` | 364 | 🟢 | Circuit breaker |
| `cache_manager_service.py` | 661 | 🟢 | Cache manager |
| `audit_service.py` | 401 | 🟢 | Auditoria |
| `embedding_service.py` | 195 | 🟢 | Embeddings |
| `embedding_cache_service.py` | 96 | 🟢 | Cache de embeddings |
| `structured_output.py` | 362 | 🟢 | Output estruturado |
| `token_tracking_service.py` | 622 | 🟢 | Tracking de tokens LLM |
| `response_cache_service.py` | 549 | 🟢 | Cache de respostas |
| `ai_cache_service.py` | 357 | 🟢 | Cache de IA |
| `explainability_service.py` | 321 | 🟢 | XAI — explainabilidade |
| `knowledge_base_service.py` | 497 | 🟢 | Base de conhecimento |
| `pattern_detector_service.py` | 568 | 🟢 | Detecção de padrões |
| `rag_service.py` | 297 | 🟢 | RAG |
| `policy_engine_service.py` | 912 | 🟢 | Motor de políticas |
| `activity_service.py` | 999 | 🟢 | Atividades |
| `affirmative_service.py` | 368 | 🟢 | Ações afirmativas |
| `memory_service.py` | 431 | 🟢 | Memória |
| `intent_classifier.py` | 301 | 🟡 | Classificador — será substituído por cascaded router |
| `enhanced_intent_classifier.py` | 516 | 🟡 | Classificador enhanced — idem |
| `intelligent_data_orchestrator.py` | 929 | 🟢 | Orquestrador de dados |
| `context_aggregator_service.py` | 354 | 🟢 | Agregador de contexto |
| `personalized_feedback_service.py` | 993 | 🟢 | Feedback personalizado |
| `graph_client.py` | 275 | 🟡 | Cliente de grafos |
| `graph_runner.py` | 430 | 🟡 | Runner de grafos |
| `conversation_manager.py` | 1.273 | 🟢 | Gerenciador de conversas |
| `outcome_correlator_service.py` | 494 | 🟢 | Correlação de resultados |
| ML subpackage (`ml/*.py`) | ~2.100 | 🟡 | Feature engineering, model registry, outcome predictor — adaptar para prod |
| `rubric_evaluation_service.py` | 1.263 | 🟢 | Avaliação por rubrica |
| `skills_catalog_service.py` | 1.314 | 🟢 | Catálogo de skills |
| `organization_catalog_service.py` | 2.373 | 🟢 | Catálogo organizacional |
| `responsibilities_catalog_service.py` | 745 | 🟢 | Catálogo de responsabilidades |
| `analysis_service.py` | 318 | 🟢 | Serviço de análise |
| `multimodal_service.py` | 857 | 🟡 | Multimodal (Claude Vision, Gemini) — adaptar API keys |
| `hubspot_service.py` | 744 | 🔴 | HubSpot — stub, reimplementar |
| `billing_service.py` | 654 | 🔴 | Billing — stub, reimplementar |
| `data_request_service.py` | 737 | 🟢 | LGPD data requests |
| `webhook_service.py` | 754 | 🟡 | Webhooks — adaptar URLs |
| `attachment_service.py` | 268 | 🟢 | Anexos |
| `config_completeness_service.py` | 557 | 🟢 | Completude de config |
| `recruiter_personalization_service.py` | 554 | 🟢 | Personalização do recrutador |
| `culture_analyzer_service.py` | 480 | 🟢 | Análise cultural |
| `proactive_alert_service.py` | 779 | 🟢 | Alertas proativos |
| `proactive_service.py` | 486 | 🟢 | Serviço proativo |
| `autonomous_agent_service.py` | 809 | 🟢 | Agente autônomo |
| `training_data_service.py` | 505 | 🟢 | Dados de treinamento |
| `report_service.py` | 599 | 🟢 | Relatórios |
| `feedback_service.py` | 561 | 🟢 | Feedback |
| `briefing_service.py` | 476 | 🟢 | Briefing diário |
| `deadline_calculator_service.py` | 283 | 🟢 | Calculadora de prazos |
| `seed_service.py` | 1.338 | 🔴 | Dados seed — ambiente dev, não para prod |
| `template_seeder.py` | 1.691 | 🔴 | Seeder de templates — adaptar para prod |
| `template_importer_service.py` | 710 | 🟡 | Importador de templates |
| `tool_executor_service.py` | 240 | 🟡 | Executor de tools |
| `planned_task_service.py` | 702 | 🟢 | Tarefas planejadas |
| `task_service.py` | 660 | 🟢 | Serviço de tarefas |
| `workos_provisioning_service.py` | 128 | 🔴 | WorkOS — stub, reimplementar |
| `job_template_service.py` | 513 | 🟢 | Templates de vagas |

**Subtotal shared**: ~40.000L — **80% direto** (🟢)

### 15.5. Orchestrator (~2.200L)

| Arquivo | Linhas | Grau | Observação |
|---------|:------:|:----:|------------|
| `orchestrator.py` | 1.112 | 🟡 | ~~Será simplificado~~ → Lógica de delegação coexiste com **CascadedRouter** + **DomainWorkflow** já implementados. Roteamento migrado. |
| `intent_router.py` | 385 | 🟡 | ~~Será substituído~~ → **CascadedRouter** + **FastRouter** criados em `orchestrator/`. Intent router mantido como fallback. |
| `state_manager.py` | 282 | 🟢 | Gestão de estado — transferência direta |
| `task_planner.py` | 270 | 🟢 | Planejamento de tarefas — transferência direta |

### 15.6. Models (~24.600L) e Schemas (~11.100L)

| Camada | Linhas | Grau | Observação |
|--------|:------:|:----:|------------|
| `models/` (completo) | ~24.600 | 🟡 | Modelos SQLAlchemy — lógica transfere; B usa Ruby on Rails (ActiveRecord), então precisam ser **traduzidos**, mas o schema é a referência definitiva. |
| `schemas/` (completo) | ~11.100 | 🟡 | Schemas Pydantic — B pode usar como spec de API; se B mantiver Python em microserviços IA, transferem direto. |

### 15.7. API Endpoints (~101.300L)

| Camada | Linhas | Grau | Observação |
|--------|:------:|:----:|------------|
| `api/v1/` (completo) | ~101.300 | 🟠 | Endpoints FastAPI — B usa Ruby on Rails. A lógica de negócio nas rotas é **referência funcional** (specs de comportamento). Se B mantiver microserviços Python para IA, os endpoints de IA transferem direto. |

### 15.8. Resumo Consolidado de Portabilidade (Atualizado Pós-Migração)

> **⚠️ TABELA ATUALIZADA**: Reflete o estado atual após migração domain-driven, decomposição de monolitos, criação de ABCs de provider e factory patterns.

| Camada | Total Linhas | 🟢 Direto | 🟡 Menor | 🟠 Estrutural | 🔴 Referência | Δ vs Anterior |
|--------|:------------:|:---------:|:--------:|:-------------:|:-------------:|:-------------:|
| Agents especializados | 33.800 | 21.400 | 3.300 | 0 | 5.000 | ⬆️ +9.400 🟢 |
| Agents infraestrutura | 8.500 | 6.800 | 1.700 | 0 | 0 | ⬆️ +800 🟢 |
| Tools | 10.000 | 9.200 | 800 | 0 | 0 | ⬆️ +3.600 🟢 |
| Services (Job Mgmt) | 21.000 | 18.900 | 2.100 | 0 | 0 | — |
| Services (WSI) | 10.900 | 10.350 | 550 | 0 | 0 | — |
| Services (Sourcing) | 6.000 | 4.800 | 1.200 | 0 | 0 | — |
| Services (Communication) | 17.600 | 4.700 | 5.600 | 2.900 | 4.400 | ⬆️ +1.800 🟡 |
| Services (Pipeline) | 7.100 | 6.000 | 1.100 | 0 | 0 | — |
| Services (CV Screening) | 2.000 | 2.000 | 0 | 0 | 0 | — |
| Services (Scheduling) | 1.300 | 0 | 1.300 | 0 | 0 | — |
| Services (ATS) | 4.400 | 550 | 3.850 | 0 | 0 | ⬆️ +3.100 🟡 |
| Services (Shared) | 40.000 | 32.000 | 5.200 | 0 | 2.800 | — |
| Orchestrator | 2.200 | 550 | 1.650 | 0 | 0 | ⬆️ +1.650 🟡 |
| Models + Schemas | 35.700 | 0 | 35.700 | 0 | 0 | — |
| API endpoints | 101.300 | 0 | 0 | 50.000 | 51.300 | — |
| Core/Config/Utils | 33.700 | 25.000 | 5.000 | 2.000 | 1.700 | — |
| V5 Features (NOVO) | 3.500 | 3.500 | 0 | 0 | 0 | ⬆️ +3.500 🟢 |
| Provider ABCs (NOVO) | 350 | 350 | 0 | 0 | 0 | ⬆️ +350 🟢 |
| Prompts YAML (NOVO) | 3.200 | 3.200 | 0 | 0 | 0 | ⬆️ +3.200 🟢 (language-agnostic) |
| LLM Provider ABC (NOVO) | 800 | 0 | 800 | 0 | 0 | ⬆️ +800 🟡 (contrato ABC portável, impl precisa re-write) |
| Repositories (NOVO) | 750 | 350 | 400 | 0 | 0 | ⬆️ +350 🟢 (ABC) + 400 🟡 (SQLAlchemy impl) |
| SerializableMixin (NOVO) | 200 | 0 | 200 | 0 | 0 | ⬆️ +200 🟡 (conceito portável, impl Rails concern) |
| Route Service Facades (NOVO) | 2.800 | 0 | 2.800 | 0 | 0 | ⬆️ +2.800 🟡 (behavior spec, queries precisam tradução) |
| **TOTAL** | **~347.100** | **~153.650** | **~73.250** | **~54.900** | **~65.200** |
| **%** | **100%** | **~44%** | **~21%** | **~16%** | **~19%** |

#### Comparação com Análise Anterior

| Métrica | Antes (pré-migração) | Pós-Migração | Pós-Portabilidade | Delta Total |
|---------|:--------------------:|:------------:|:-----------------:|:-----------:|
| 🟢 Direto | ~115.000L (35%) | ~146.100L (43%) | **~153.650L (44%)** | **+38.650L (+9pp)** |
| 🟢+🟡 Baixo esforço | ~192.000L (58%) | ~215.150L (63%) | **~226.900L (65%)** | **+34.900L (+7pp)** |
| 🟢+🟡+🟠 Aproveitável | ~264.000L (80%) | ~270.050L (80%) | **~281.800L (81%)** | +17.800L (+1pp) |
| 🔴 Referência apenas | ~68.000L (20%) | ~65.200L (19%) | **~65.200L (19%)** | -2.800L (-1pp) |

> **Conclusão Atualizada (Pós-Portabilidade)**: **~65% do protótipo (~226.900 linhas)** é agora aproveitável com esforço baixo (Direto + Adaptação Menor), contra 63% pós-migração e 58% originalmente — uma melhoria total de **7 pontos percentuais**.
>
> A fase de portabilidade adicionou **~7.750 novas linhas** com diferentes graus de portabilidade:
> 1. **Prompts YAML** (~3.200L, 🟢 100% direto) — 12 arquivos externalizados, carregáveis em qualquer linguagem sem alteração
> 2. **LLM Provider ABC + Factory** (~800L, 🟡 contrato portável) — ABC define interface; implementações Claude/Gemini/OpenAI precisam re-write para SDKs Ruby
> 3. **Repository Pattern** (~750L, 🟢 ABC + 🟡 impl) — BaseRepository ABC é spec direta; SQLAlchemy impl serve como referência para ActiveRecord
> 4. **Route Service Facades** (~2.800L, 🟡 behavior spec) — Business logic extraída; queries SQLAlchemy precisam tradução para ActiveRecord, mas a lógica de negócio é a spec
> 5. **SerializableMixin** (~200L, 🟡 conceito portável) — Padrão to_dict/from_dict traduzível para Rails concern/module
>
> Os **~19% de Referência** (~65.200L) são fundamentalmente irredutíveis no protótipo porque dependem de:
> 1. **Endpoints FastAPI** (~51.300L) — a produção usa Rails
> 2. **Integrações Teams/Microsoft** (~2.600L) — precisam de tenant Azure real
> 3. **Billing/HubSpot/WorkOS stubs** (~3.000L) — precisam de contas reais
> 4. **Seed data** (~3.000L) — dados de desenvolvimento
> 5. **Agents deprecated** (~1.300L) — já substituídos
>
> O **IP mais valioso** para a Produção está concentrado em:
> 1. **WSI Assessment** (~11.000L, 95% direto) — metodologia proprietária completa
> 2. **Prompts YAML** (~3.200L, 100% direto) — externalizados, language-agnostic, carregáveis em Ruby/Python/Node
> 3. **Job Management services** (~21.000L, 90% direto) — wizard, templates, insights
> 4. **Learning Loop** (~3.600L, 100% direto) — sistema de aprendizado contínuo
> 5. **Tools decompostos** (~10.000L, 100% aproveitável) — agora por domínio
> 6. **V5 Features** (~3.500L, 100% direto) — ConversationMemory, SmartExtractor, ExecutionPlan, StatsManager, AsyncProcessing
> 7. **Provider ABCs** (~1.150L, 100% direto) — VoiceProvider, ATSProviderFactory, LLMProvider — contratos para implementação real
> 8. **Route Service Facades** (~2.800L, 100% direto) — business logic extraída das rotas, portável como spec de comportamento
> 9. **Repository Pattern** (~750L, 100% direto) — abstração SQLAlchemy→ActiveRecord para 4 models críticos
> 10. **SerializableMixin** (~200L, 100% direto) — serialização padronizada transferível para Rails concerns

#### 15.8.1. Guia Rápido: 5 Fases de Portabilidade

As 5 fases de portabilidade foram implementadas para maximizar o reuso do protótipo pela equipe de produção. Cada fase é independente e pode ser adotada separadamente. Abaixo, o resumo e o guia prático para cada uma.

**Tabela-resumo:**

| Fase | Artefato | Path | Linhas | Grau | Equivalente Rails |
|:----:|----------|------|:------:|:----:|-------------------|
| 1 | Prompts YAML | `app/prompts/*.yaml` | 3.200 | 🟢 | `YAML.load_file` |
| 2 | LLM Provider ABC | `app/shared/providers/llm_*.py` | 800 | 🟡 | Module + gem wrappers |
| 3 | Repository Pattern | `app/shared/repositories/` | 750 | 🟢/🟡 | `ApplicationRecord` |
| 4 | Route Service Facades | 3 service files | 2.800 | 🟡 | Service Objects |
| 5 | SerializableMixin | `app/shared/mixins/serializable.py` | 200 | 🟡 | `ActiveModel::Serializers` / Concern |

**Fase 1 — Prompts YAML (3.200 linhas)**

- **Arquivos**: `app/prompts/*.yaml` (12 arquivos) + `app/prompts/__init__.py` (PromptLoader)
- **O que é**: Cada domínio possui seu próprio YAML com system prompts, few-shot examples e templates. O `PromptLoader` expõe `get_domain_prompt(domain_id)` e `get_shared_prompt(name)`.
- **O que fazer**: Copiar a pasta `app/prompts/` inteira para o projeto Rails. YAML é language-agnostic — carrega em qualquer linguagem sem adaptação.
- **Equivalência Python → Rails**:

```python
# Python
prompt = PromptLoader.get_domain_prompt("sourcing")
```

```ruby
# Rails — zero adaptação
prompt = YAML.load_file("prompts/sourcing.yaml")
```

**Fase 2 — LLM Provider ABC + Factory (800 linhas)**

- **Arquivos**: `app/shared/providers/llm_provider.py` (ABC), `llm_factory.py`, `llm_claude.py`, `llm_gemini.py`, `llm_openai.py`
- **O que é**: ABC que define `generate()`, `generate_stream()`, `count_tokens()`, `get_model_name()`. Factory: `LLMProviderFactory.create("claude")` → retorna instância configurada.
- **O que fazer**: Usar como spec da interface. Criar um módulo `LlmProvider` em Ruby com a mesma interface e implementar com gems (`anthropic`, `ruby-openai`).
- **Equivalência Python → Rails**:

```python
# Python
provider = LLMProviderFactory.create("claude")
response = provider.generate(prompt, max_tokens=1000)
```

```ruby
# Rails
provider = LlmProviderFactory.create(:claude)
response = provider.generate(prompt, max_tokens: 1000)
```

**Fase 3 — Repository Pattern (750 linhas)**

- **Arquivos**: `app/shared/repositories/base.py` (ABC), `sqlalchemy_base.py`, `candidate_repository.py`, `job_repository.py`, `notification_repository.py`, `company_repository.py`
- **O que é**: ABC que define `get_by_id`, `list`, `create`, `update`, `delete`, `count`, `exists` para 4 models críticos.
- **O que fazer**: ActiveRecord JÁ é o repository pattern. Usar a ABC como spec para definir scopes e query methods equivalentes.
- **Equivalência Python → Rails**:

```python
# Python
candidates = CandidateRepository.list(
    db, filters={"status": "active"}, limit=10
)
```

```ruby
# Rails — ActiveRecord já implementa o pattern
candidates = Candidate.where(status: :active).limit(10)
```

**Fase 4 — Route Service Facades (2.800 linhas)**

- **Arquivos**:
  - `app/domains/job_management/services/job_vacancy_route_service.py` (882L)
  - `app/domains/sourcing/services/candidate_search_route_service.py` (1.032L)
  - `app/services/company_route_service.py` (892L)
- **O que é**: Business logic extraída das 3 maiores rotas API em serviços reutilizáveis. Métodos-chave: `get_job_vacancy_metrics()`, `get_job_analytics()`, `search_candidates_unified()`, `submit_onboarding()`, `generate_evp()`.
- **O que fazer**: Criar Service Objects equivalentes (`JobVacancyMetricsService`, `CandidateSearchService`, `CompanyOnboardingService`). Os facades documentam O QUE calcular — o time Rails implementa COMO.
- **Equivalência Python → Rails**:

```python
# Python
metrics = JobVacancyRouteService.get_job_vacancy_metrics(db, company_id)
```

```ruby
# Rails
metrics = JobVacancyMetricsService.call(company_id: company.id)
```

**Fase 5 — SerializableMixin (200 linhas)**

- **Arquivo**: `app/shared/mixins/serializable.py`
- **O que é**: Adiciona `to_dict()` e `from_dict()` aos models com field mapping, type conversion e relationship handling.
- **O que fazer**: Traduzir para um concern Rails usando `ActiveModel::Serializers` ou concern customizado.
- **Equivalência Python → Rails**:

```python
# Python
class Candidate(SerializableMixin, Base):
    ...
data = candidate.to_dict()
obj = Candidate.from_dict(data)
```

```ruby
# Rails
module Serializable
  extend ActiveSupport::Concern
  def to_dict = as_json(except: [:created_at, :updated_at])
  def self.from_dict(data) = new(data)
end

class Candidate < ApplicationRecord
  include Serializable
end
```

---

### 15.9. Contratos de Interface dos 9 Domínios

> Para a equipe de produção entender exatamente o que cada domínio expõe — sem precisar ler o código.

| Domínio | Classe | Actions | Agents | Services | Contrato Principal |
|---------|--------|:-------:|:------:|:--------:|-------------------|
| **Job Management** | `JobManagementDomain` | 30 | 6 (intake, drafting, insights, benefits_comp, lifecycle, rubric) | 29 | Ciclo de vida completo de vagas: criação via wizard, enriquecimento JD, templates, clonagem, automações |
| **CV Screening + WSI** | `CVScreeningDomain` | 27 | 3 (triagem, avaliador_wsi, screening) | 20 | Triagem curricular, scoring WSI proprietário, calibração de senioridade, perguntas adaptativas |
| **Sourcing** | `SourcingDomain` | 32 | 2 (sourcing, engagement_nodes) | 11 | Busca multi-canal (boolean, Pearch, PG Vector, WRF), engagement pipeline, analytics de busca |
| **Communication** | `CommunicationDomain` | 41 | 1 (communication) | 21 | Email multi-provider, WhatsApp (Meta/Twilio), voz, notificações, templates, LGPD data requests |
| **Interview & Scheduling** | `InterviewSchedulingDomain` | 41 | 3 (entrevistador, scheduling, nodes) | 4 | Agendamento, entrevista WSI por voz/WhatsApp, calendário, transcrição Deepgram |
| **Analytics & Reporting** | `AnalyticsDomain` | 37 | 2 (analista_feedback, analytics) | 9 | KPIs, funil, métricas de velocidade, diversidade, stakeholders, alertas inteligentes |
| **ATS Integration** | `ATSIntegrationDomain` | 37 | 1 (integrador_ats) | 9 | Sync bidirecional com Gupy, Pandapé, Merge, StackOne via ATSProviderFactory |
| **Automation & Tasks** | `AutomationDomain` | 41 | 1 (task_planner) | 11 | Motor de automação, triggers, scheduler, delegação de tarefas, agente autônomo |
| **Recruiter Assistant** | `RecruiterAssistantDomain` | 41 | 1 (recruiter_assistant) | 6 | Daily briefing, consultas, status updates, personalização, proatividade |
| **TOTAL** | 9 domínios | **199** | **20** | **120** | |

#### Infraestrutura Compartilhada (shared/)

| Módulo | Arquivos | Função |
|--------|:--------:|--------|
| `shared/memory/` | 2 | ConversationState + ReferenceResolver (V5) |
| `shared/intelligence/` | 4 | SmartExtractor (V5) + SemanticSearch + Embeddings |
| `shared/execution/` | 3 | ExecutionPlan + PlanDetector + PlanExecutor (V5) |
| `shared/async_processing/` | 3 | DomainTaskQueue + AsyncWorker (V5) |
| `shared/providers/` | 3 | VoiceProvider ABC + ATSProviderFactory (NOVO) |
| `shared/compliance/` | 2 | FairnessGuard + FactChecker |
| `shared/resilience/` | 2 | StatsManager (V5) + CircuitBreaker |
| `shared/robustness/` | 6 | Input validation, error handling, defensive prompts |
| `shared/learning/` | 4 | LearningLoop + FeedbackLearning + TemplateLearning + Hub |
| `shared/governance/` | 1 | GovernanceEngine |
| `shared/tools/` | 2 | ToolRegistry + ToolExecutor |

#### Orquestração

| Componente | Arquivo | Função |
|-----------|--------|--------|
| CascadedRouter | `orchestrator/cascaded_router.py` | Roteamento hierárquico: FastRouter → LLM fallback |
| FastRouter | `orchestrator/fast_router.py` | Roteamento determinístico por regex/keyword |
| DomainWorkflow | `domains/workflow.py` | Execução de workflows multi-step dentro de domínios |
| DomainRegistry | `domains/registry.py` | Registro e discovery de domínios |
| DomainPrompt (ABC) | `domains/base.py` | Contrato base: `get_system_prompt()`, `get_allowed_actions()`, `execute_action()`, `validate_context()` |

---

## 16. Plano Detalhado e Faseado de Ajustes no Protótipo (Replit)

> **Objetivo**: Expandir o plano conceitual da Seção 14 em um plano executável, com pré-requisitos, arquivos específicos afetados, critérios de validação, e dependências entre fases. Cada fase pode ser executada de forma independente, sem quebrar o sistema em funcionamento.
>
> **Base**: Este plano integra duas fontes:
> - **Seção 14** (plano conceitual): Define a estrutura de 11 fases, diagnóstico de diferenças A↔B, e componentes a criar (~1.300L novas + ~35.000L movidas)
> - **Seção 15** (Mapa de Portabilidade): Classifica todos os 332K linhas do protótipo por grau de reaproveitamento (🟢🟡🟠🔴), permitindo priorizar fases e calibrar esforço por arquivo
>
> A coluna **Grau** em cada tabela de arquivos movidos corresponde à classificação da Seção 15, indicando se o arquivo é "mover e pronto" (🟢), "ajustar interface" (🟡), "decompor/reorganizar" (🟠), ou "usar como referência" (🔴).
>
> **Princípio-guia**: Cada fase termina com o sistema 100% funcional. Nenhuma fase intermediária deixa o protótipo em estado quebrado.

### 16.1. FASE 0 — Infraestrutura Base

**Pré-requisitos**: Nenhum
**Objetivo**: Criar os novos componentes arquiteturais sem alterar nada do existente

#### 16.1.1. Criar `domains/base.py` — DomainPrompt ABC

**Arquivos criados**:
- `lia-agent-system/app/domains/__init__.py`
- `lia-agent-system/app/domains/base.py` (~200L)

**O que implementar**:
```python
class DomainPrompt(ABC):
    domain_id: str
    domain_name: str
    description: str
    
    @abstractmethod
    def get_allowed_actions(self) -> List[DomainAction]: ...
    
    @abstractmethod
    def get_system_prompt(self) -> str: ...
    
    @abstractmethod
    async def process_intent(self, query, context) -> IntentResult: ...
    
    @abstractmethod
    async def execute_action(self, action_id, params, context) -> DomainResponse: ...
    
    def validate_context(self, context) -> bool: ...
    def get_suggestions(self, context) -> List[str]: ...

class DomainContext:
    domain_id, user_id, session_id, tenant_id
    current_data, selected_ids, filters_applied
    conversation_memory  # lazy-loaded
    api_calls_history

class DomainResponse:
    success, message, data, suggestions
    needs_confirmation, needs_clarification
    clarification_question, clarification_options
    error, metadata, api_calls

class DomainAction:
    action_id, name, description
    required_params, optional_params
    requires_confirmation: bool
```

**Critério de validação**: `from app.domains.base import DomainPrompt, DomainContext, DomainResponse` funciona sem erros

#### 16.1.2. Criar `domains/registry.py` — DomainRegistry

**Arquivo criado**: `lia-agent-system/app/domains/registry.py` (~150L)

**O que implementar**:
```python
_DOMAIN_REGISTRY: Dict[str, Type[DomainPrompt]] = {}

def register_domain(cls):
    """Decorator para auto-registro de domínios"""
    _DOMAIN_REGISTRY[cls.domain_id] = cls
    return cls

class DomainRegistry:
    _instances: Dict[str, DomainPrompt] = {}
    
    def get_instance(self, domain_id) -> DomainPrompt: ...
    def list_domains(self) -> List[str]: ...
    def get_all_actions(self) -> Dict[str, List[DomainAction]]: ...
```

**Critério de validação**: Registrar um domínio dummy com `@register_domain` e recuperá-lo via `DomainRegistry.get_instance()`

#### 16.1.3. Criar `domains/workflow.py` — DomainWorkflow (LangGraph)

**Arquivo criado**: `lia-agent-system/app/domains/workflow.py` (~250L)

**O que implementar**:
- Grafo LangGraph de 3 nós: `analyze_intent` → `execute` → `format`
- `analyze_intent`: chama `domain.process_intent()`
- `execute`: valida confidence ≥ 0.5, chama `domain.execute_action()`
- `format`: usa `TemplateFormatter` para construir resposta Markdown

**Dependência**: `domains/base.py` (DomainPrompt, DomainContext)

**Critério de validação**: Executar workflow com domínio dummy e receber `DomainResponse` formatada

#### 16.1.4. Criar `orchestrator/cascaded_router.py` + `orchestrator/fast_router.py`

**Arquivos criados**:
- `lia-agent-system/app/orchestrator/cascaded_router.py` (~200L)
- `lia-agent-system/app/orchestrator/fast_router.py` (~150L)

**O que implementar no CascadedRouter**:
```python
class CascadedRouter:
    def __init__(self, fast_router, intent_router, domain_registry):
        self.memory_cache = {}  # query_hash → domain_id
        self.fast = fast_router
        self.llm_fallback = intent_router  # IntentRouter existente!
        self.registry = domain_registry
    
    async def route(self, message, context) -> DomainPrompt:
        # 1. Memory: já vimos essa query?
        cached = self.memory_cache.get(hash(message))
        if cached: return self.registry.get_instance(cached)
        
        # 2. Fast: keywords/regex
        fast_result = self.fast.match(message)
        if fast_result: 
            self.memory_cache[hash(message)] = fast_result
            return self.registry.get_instance(fast_result)
        
        # 3. LLM fallback: IntentRouter existente
        intent = await self.llm_fallback.classify(message)
        domain_id = self._intent_to_domain(intent)
        self.memory_cache[hash(message)] = domain_id
        return self.registry.get_instance(domain_id)
```

**O que implementar no FastRouter**:
```python
DOMAIN_PATTERNS = {
    "job_management": [r"criar?\s+vaga", r"editar?\s+vaga", r"gerar?\s+jd", ...],
    "sourcing": [r"buscar?\s+candidato", r"pesquisar?\s+", r"pearch", ...],
    "cv_screening": [r"triagem", r"analisar?\s+cv", r"red\s*flags", ...],
    "wsi_assessment": [r"score\s+wsi", r"avaliar?\s+", r"bloom", r"dreyfus", ...],
    "scheduling": [r"agendar?\s+", r"reagendar?\s+", r"cancelar?\s+entrevista", ...],
    "communication": [r"email", r"whatsapp", r"enviar?\s+", r"template", ...],
    "pipeline_management": [r"kanban", r"mover?\s+candidato", r"aprovar?\s+", ...],
    "ats_integration": [r"sync\s+ats", r"gupy", r"pandap[eé]", ...],
    "recruiter_assistant": [r"briefing", r"meu\s+dia", r"resumo", ...],
    "task_planning": [r"tarefa", r"planejar?\s+", r"delegar?\s+", ...],
}
```

**Critério de validação**: `fast_router.match("quero criar uma vaga")` retorna `"job_management"`; `fast_router.match("agende uma entrevista")` retorna `"scheduling"`

#### 16.1.5. Criar `shared/` — Mover serviços transversais

**Diretórios criados**:
```
lia-agent-system/app/shared/
├── __init__.py
├── compliance/  (audit_service.py, lgpd_*.py → movidos de services/)
├── learning/    (learning_loop_service.py, template_learning_service.py → movidos)
├── governance/  (feature_flag_service.py, agent_monitoring_service.py → movidos)
├── intelligence/ (embedding_service.py, semantic_search_service.py → movidos)
├── resilience/  (circuit_breaker.py, cache_manager_service.py → movidos)
└── tools/       (export_tools.py → movido de tools/)
```

**Arquivos movidos (sem alterar conteúdo — apenas imports)**:
| De | Para |
|---|---|
| `services/audit_service.py` | `shared/compliance/audit_service.py` |
| `services/learning_loop_service.py` | `shared/learning/learning_loop_service.py` |
| `services/template_learning_service.py` | `shared/learning/template_learning_service.py` |
| `services/feature_flag_service.py` | `shared/governance/feature_flag_service.py` |
| `services/agent_monitoring_service.py` | `shared/governance/agent_monitoring_service.py` |
| `services/embedding_service.py` | `shared/intelligence/embedding_service.py` |
| `services/semantic_search_service.py` | `shared/intelligence/semantic_search_service.py` |
| `services/circuit_breaker.py` | `shared/resilience/circuit_breaker.py` |
| `services/cache_manager_service.py` | `shared/resilience/cache_manager_service.py` |
| `tools/export_tools.py` | `shared/tools/export_tools.py` |

**Estratégia de imports**: Manter re-exports nos locais originais para não quebrar imports existentes:
```python
# services/audit_service.py (após mover)
from app.shared.compliance.audit_service import *  # re-export para compatibilidade
```

**Critério de validação**: Todos os imports existentes continuam funcionando; `from app.shared.compliance import audit_service` também funciona

#### 16.1.6. Criar novos guards — FairnessGuard + FactChecker

**Arquivos criados**:
- `lia-agent-system/app/shared/compliance/fairness_guard.py` (~150L)
- `lia-agent-system/app/shared/compliance/fact_checker.py` (~200L)

**FairnessGuard — O que implementar**:
- Middleware que intercepta queries antes do domínio
- Bloqueia filtros discriminatórios (gênero, raça, idade, religião, orientação)
- Lista de termos proibidos + regex patterns
- Retorna mensagem educativa quando bloqueia

**FactChecker — O que implementar**:
- Middleware pós-resposta que valida claims numéricas da IA
- Verifica: salários citados vs. dados reais, contagens de candidatos, datas
- Flag: `confidence_verified: true/false` na resposta

**Critério de validação**: `fairness_guard.check("buscar apenas candidatos homens")` retorna bloqueio com mensagem explicativa

**Resumo Fase 0**:

| Item | Linhas novas | Tipo | Status |
|------|:------------:|------|:------:|
| `domains/base.py` | ~200 | Novo | ✅ Implementado |
| `domains/registry.py` | ~150 | Novo | ✅ Implementado |
| `domains/workflow.py` | ~250 | Novo | ✅ Implementado |
| `orchestrator/cascaded_router.py` | ~200 | Novo | ✅ Implementado |
| `orchestrator/fast_router.py` | ~225 | Novo | ✅ Implementado |
| `shared/compliance/fairness_guard.py` | ~196 | Novo | ✅ Implementado |
| `shared/compliance/fact_checker.py` | ~251 | Novo | ✅ Implementado |
| Re-exports + `__init__.py` | ~100 | Novo | ✅ Implementado |
| Serviços movidos para `shared/` | ~0 (mover) | Mover | ✅ 10 serviços |
| **Total Fase 0** | **~1.572** | | **✅ COMPLETA** |

> **Fase 0 executada em 12/02/2026**. Validação: 37/37 testes passando (imports, routing, fairness guard, fact checker, backward compatibility, sistema existente intacto). Princípio add-only respeitado — nenhum código existente foi modificado.

---

### 16.2. FASE 1 — Migrar Domínio Sourcing (piloto)

**Pré-requisitos**: Fase 0 completa
**Justificativa**: Sourcing é o domínio mais próximo do padrão B (já tem `MultiAgentOrchestrator`, actions, stats)
**Perfil de portabilidade (Seção 15)**: 80% 🟢 Direto — migração de baixo risco, ideal como piloto

#### 16.2.1. Criar estrutura do domínio

**Diretórios criados**:
```
lia-agent-system/app/domains/sourcing/
├── __init__.py
├── domain.py          ← SourcingDomain(DomainPrompt)
├── agents/
│   └── sourcing_agent.py  ← movido de agents/specialized/
├── services/
│   ├── pearch_service.py  ← movido de services/pearch_service.py
│   ├── search_analytics.py ← movido de services/search_analytics_service.py
│   ├── sourcing_pipeline.py ← movido de services/sourcing_pipeline_service.py
│   ├── wrf_service.py    ← movido de services/wrf_dynamic_k_service.py
│   ├── es_analyzer.py    ← movido de services/es_score_drop_analyzer.py
│   ├── pgv_analyzer.py   ← movido de services/pgv_gap_analyzer.py
│   ├── pre_wrf_filter.py ← movido de services/pre_wrf_filter_service.py
│   ├── vacancy_search.py ← movido de services/vacancy_search_service.py
│   ├── apify_mcp_client.py ← movido de services/apify_mcp_client.py
│   └── apify_service.py  ← movido de services/apify_service.py
├── tools.py               ← queries de sourcing extraídas de tools/query_tools.py
├── actions.py             ← ~30 actions (show_candidate, search, filter, aggregate, analyze)
└── prompts.py             ← prompts de sourcing extraídos de agents/prompts/
```

#### 16.2.2. Arquivos movidos

| De | Para | Linhas | Grau |
|---|---|:---:|:---:|
| `agents/specialized/sourcing_agent.py` | `domains/sourcing/agents/sourcing_agent.py` | 1.881 | 🟢 |
| `agents/sourcing_engagement_nodes.py` | `domains/sourcing/agents/engagement_nodes.py` | 1.354 | 🟢 |
| `agents/prompts/examples/sourcing_examples.py` | `domains/sourcing/prompts.py` (merge) | 528 | 🟢 |
| `services/sourcing_pipeline_service.py` | `domains/sourcing/services/sourcing_pipeline.py` | 1.102 | 🟢 |
| `services/pearch_service.py` | `domains/sourcing/services/pearch_service.py` | 1.042 | 🟡 |
| `services/search_analytics_service.py` | `domains/sourcing/services/search_analytics.py` | 597 | 🟢 |
| `services/vacancy_search_service.py` | `domains/sourcing/services/vacancy_search.py` | 511 | 🟢 |
| `services/apify_mcp_client.py` | `domains/sourcing/services/apify_mcp_client.py` | 473 | 🟡 |
| `services/apify_service.py` | `domains/sourcing/services/apify_service.py` | 276 | 🟡 |
| `services/evaluation_criteria_service.py` | `domains/sourcing/services/evaluation_criteria.py` | 465 | 🟢 |
| `services/es_score_drop_analyzer.py` | `domains/sourcing/services/es_analyzer.py` | 99 | 🟢 |
| `services/pgv_gap_analyzer.py` | `domains/sourcing/services/pgv_analyzer.py` | 90 | 🟢 |
| `services/wrf_dynamic_k_service.py` | `domains/sourcing/services/wrf_service.py` | 81 | 🟢 |
| `services/pre_wrf_filter_service.py` | `domains/sourcing/services/pre_wrf_filter.py` | 104 | 🟢 |

#### 16.2.3. Novos arquivos

| Arquivo | Linhas ~est | O que contém |
|---------|:----------:|-------------|
| `domains/sourcing/domain.py` | ~80 | `SourcingDomain(DomainPrompt)` com `process_intent()`, `execute_action()`, `get_allowed_actions()` |
| `domains/sourcing/actions.py` | ~60 | Lista de ~30 DomainActions (query, aggregate, analyze) |
| `domains/sourcing/tools.py` | ~200 | Queries de sourcing extraídas de `query_tools.py` |

#### 16.2.4. Validação

| Teste | Esperado | Status |
|-------|----------|:------:|
| `DomainRegistry.get_instance("sourcing")` | Retorna `SourcingDomain` | ✅ |
| `FastRouter.match("buscar candidatos python")` | Resolve → `"sourcing"` (conf=0.95) | ✅ |
| `SourcingDomain.get_allowed_actions()` | Retorna 30 DomainActions | ✅ |
| `SourcingDomain.process_intent()` | Heurística mapeia keywords → action_ids | ✅ |
| 14 arquivos importáveis via novo path | `app.domains.sourcing.*` | ✅ |
| 12 imports originais backward compat | `app.agents.specialized.*`, `app.services.*` | ✅ |
| `AgentRegistry` (antigo) | Continua funcionando | ✅ |
| FastAPI endpoints de sourcing | Continuam respondendo | ✅ |

> **Fase 1 executada em 12/02/2026**. Validação: 36/36 testes passando. Estrutura criada: 14 arquivos copiados + 3 novos (domain.py 127L, actions.py 38L, tools.py 207L) + 3 __init__.py. Total: ~8.980 linhas no domínio Sourcing. Sistema existente intacto.

---

### 16.3. FASE 2 — Migrar Domínio Job Management (o mais complexo)

**Pré-requisitos**: Fase 1 completa e validada
**Justificativa**: Maior domínio do protótipo (~4.132L em 1 agente + ~21.000L de serviços). Requer decomposição.
**Perfil de portabilidade (Seção 15)**: 90% 🟢 Direto nos serviços, mas agente principal é 🟠 (requer decomposição em 5). Risco concentrado na decomposição, não nos serviços.

#### 16.3.1. Decompor `job_intake_agent.py` (4.132L)

**Análise de seções do arquivo** (baseada no código real):

| Linhas no arquivo | Responsabilidade | Destino |
|:---:|------------------|---------|
| 1–57 | Imports + constantes | Distribuir por subagentes |
| 58–745 | Prompts (JD_EXTRACTION_PROMPT, prompts de wizard) | `domains/job_management/prompts.py` |
| 746–1.200 | `__init__`, `_register_actions`, ações do wizard | `wizard_agent.py` |
| 1.200–1.700 | `extract_requirements`, JD parsing | `jd_extractor_agent.py` |
| 1.700–2.100 | `generate_jd`, formatação de JD | `jd_generator_agent.py` |
| 2.100–2.700 | Market benchmark, skills, enrichment | `enrichment_agent.py` |
| 2.700–3.000 | Validação, completeness, quality score | `validation_agent.py` |
| 3.000–4.132 | Rubric evaluation, benefits, company config | Distribuir entre agents |

#### 16.3.2. Estrutura do domínio

```
lia-agent-system/app/domains/job_management/
├── __init__.py
├── domain.py              ← JobManagementDomain(DomainPrompt)
├── agents/
│   ├── wizard_agent.py    ← Conversa guiada (~1.200L)
│   ├── jd_extractor_agent.py ← Parsing JD (~500L)
│   ├── jd_generator_agent.py ← Geração JD (~400L)
│   ├── enrichment_agent.py   ← Enriquecimento (~600L)
│   └── validation_agent.py   ← Validação (~300L)
├── services/              ← ~35 serviços movidos de services/
│   ├── wizard_orchestrator.py
│   ├── jd_enrichment.py
│   ├── jd_generator.py
│   ├── jd_import.py
│   ├── jd_template.py
│   ├── jd_template_cache.py
│   ├── intelligence_layer.py
│   ├── market_benchmark.py
│   ├── compensation_analysis.py
│   ├── job_vacancy.py
│   ├── job_insights.py
│   ├── job_embedding.py
│   ├── job_pattern.py
│   ├── job_report.py
│   ├── job_clone.py
│   ├── job_alert.py
│   ├── job_board.py
│   ├── job_audit.py
│   ├── job_context.py
│   ├── job_status_webhook.py
│   ├── job_qualification.py
│   ├── job_analytics_prompt.py
│   ├── automation_service.py
│   ├── automation_handlers.py
│   ├── automation_scheduler.py
│   ├── automation_trigger.py
│   ├── benefits.py
│   ├── company_configuration.py
│   ├── confidence_policy.py
│   ├── skills_catalog.py
│   ├── organization_catalog.py
│   ├── responsibilities_catalog.py
│   ├── suggestion_interaction.py
│   ├── wizard_data_priority.py
│   ├── wizard_analytics.py
│   ├── archetype_builder.py
│   ├── manager_inference.py
│   └── lia_field_config.py
├── tools.py               ← job_tools.py + job_wizard_tools.py (merge: ~1.860L)
├── actions.py             ← ~20 DomainActions
└── prompts.py             ← Prompts do wizard + JD (~1.100L)
```

#### 16.3.3. Validação

| Teste | Esperado |
|-------|----------|
| `DomainRegistry.get_instance("job_management")` | Retorna `JobManagementDomain` |
| `CascadedRouter.route("quero criar uma vaga de dev senior")` | `"job_management"` via fast_router |
| Wizard conversacional funciona end-to-end | LIA guia criação em stages como antes |
| JD extraction de texto colado | Retorna requisitos estruturados |
| Enrichment com market benchmark | Retorna sugestões de salário e skills |
| `job_intake_agent.py` original | Removido (substituído pelos 5 novos) |

---

### 16.4. FASE 3 — Migrar Domínio CV Screening

**Pré-requisitos**: Fase 0
**Pode ser executada em paralelo com Fases 2, 4, 5**
**Perfil de portabilidade (Seção 15)**: 100% 🟢 Direto — menor risco de todas as fases

**Arquivos movidos**:
| De | Para | Linhas | Grau |
|---|---|:---:|:---:|
| `agents/specialized/triagem_curricular_agent.py` | `domains/cv_screening/agents/triagem_agent.py` | 1.384 | 🟢 |
| `agents/specialized/screening_agent.py` | `domains/cv_screening/agents/screening_agent.py` (deprecated) | 443 | 🔴 |
| `services/cv_parser.py` | `domains/cv_screening/services/cv_parser.py` | 600 | 🟢 |
| `services/cv_scoring_service.py` | `domains/cv_screening/services/cv_scoring.py` | 407 | 🟢 |
| `services/interview_transcript_analysis_service.py` | `domains/cv_screening/services/transcript_analysis.py` | 1.035 | 🟢 |

**Novos**: `domain.py` (~60L), `actions.py` (~40L)

---

### 16.5. FASE 4 — Migrar Domínio Interviewing

**Pré-requisitos**: Fase 0
**Perfil de portabilidade (Seção 15)**: 🟡 predominante — adaptar providers de voz (OpenMic, Deepgram, Gemini)

**Arquivos movidos**:
| De | Para | Linhas | Grau |
|---|---|:---:|:---:|
| `agents/specialized/entrevistador_agent.py` | `domains/interviewing/agents/entrevistador_agent.py` | 1.117 | 🟡 |
| `services/voice_service.py` | `domains/interviewing/services/voice_service.py` | 417 | 🟡 |
| `services/deepgram_service.py` | `domains/interviewing/services/deepgram_service.py` | 331 | 🟡 |
| `services/gemini_voice_service.py` | `domains/interviewing/services/gemini_voice_service.py` | 337 | 🟡 |
| `services/openmic_service.py` | `domains/interviewing/services/openmic_service.py` | 720 | 🟡 |
| `services/wsi_voice_orchestrator.py` | `domains/interviewing/services/wsi_voice_orchestrator.py` | 780 | 🟡 |

**Novos**: `domain.py` (~60L), `actions.py` (~40L)

---

### 16.6. FASE 5 — Migrar Domínio WSI Assessment

**Pré-requisitos**: Fase 0
**Perfil de portabilidade (Seção 15)**: 95%+ 🟢 Direto — IP mais valioso do protótipo. Priorizar proteção da integridade.

**Arquivos movidos**:
| De | Para | Linhas | Grau |
|---|---|:---:|:---:|
| `agents/specialized/avaliador_wsi_agent.py` | `domains/wsi_assessment/agents/avaliador_wsi_agent.py` | 1.596 | 🟢 |
| `services/wsi_service.py` | `domains/wsi_assessment/services/wsi_service.py` | 1.295 | 🟢 |
| `services/lia_score_service.py` | `domains/wsi_assessment/services/lia_score.py` | 1.303 | 🟢 |
| `services/calibration_profiles.py` | `domains/wsi_assessment/services/calibration_profiles.py` | 995 | 🟢 |
| `services/seniority_resolver.py` | `domains/wsi_assessment/services/seniority_resolver.py` | 882 | 🟢 |
| `services/wsi_question_service.py` | `domains/wsi_assessment/services/wsi_questions.py` | 879 | 🟢 |
| `services/wsi_voice_orchestrator.py` | (já movido em Fase 4) | — | — |
| `services/wsi_question_generator.py` | `domains/wsi_assessment/services/wsi_question_generator.py` | 600 | 🟢 |
| `services/wsi_screening_pipeline.py` | `domains/wsi_assessment/services/wsi_pipeline.py` | 586 | 🟢 |
| `services/seniority_context_calibrator.py` | `domains/wsi_assessment/services/seniority_calibrator.py` | 599 | 🟢 |
| `services/wsi_deterministic_scorer.py` | `domains/wsi_assessment/services/wsi_scorer.py` | 558 | 🟢 |
| `services/calibration_service.py` | `domains/wsi_assessment/services/calibration.py` | 474 | 🟢 |
| `services/seniority_utils.py` | `domains/wsi_assessment/services/seniority_utils.py` | 393 | 🟢 |
| `services/seniority_jd_analyzer.py` | `domains/wsi_assessment/services/seniority_jd_analyzer.py` | 391 | 🟢 |
| `services/screening_question_set_service.py` | `domains/wsi_assessment/services/question_sets.py` | 325 | 🟢 |
| `services/wsi_question_adjuster.py` | `domains/wsi_assessment/services/wsi_adjuster.py` | 297 | 🟢 |
| `services/score_normalization_service.py` | `domains/wsi_assessment/services/score_normalization.py` | 176 | 🟢 |
| `services/eligibility_verification_service.py` | `domains/wsi_assessment/services/eligibility.py` | 374 | 🟢 |
| `tools/query_tools.py` (parcial WSI) | `domains/wsi_assessment/tools.py` | ~2.000 | 🟡 |

**Novos**: `domain.py` (~80L), `actions.py` (~50L)

---

### 16.7. FASE 6 — Migrar Domínio Pipeline Management

**Pré-requisitos**: Fase 0
**Perfil de portabilidade (Seção 15)**: 85% 🟢 Direto nos serviços. Agents deprecated (🔴) são movidos para referência.

**Arquivos movidos**:
| De | Para | Linhas | Grau |
|---|---|:---:|:---:|
| `agents/specialized/analista_feedback_agent.py` | `domains/pipeline_management/agents/analista_feedback_agent.py` | 2.068 | 🟡 |
| `agents/specialized/analytics_agent.py` | `domains/pipeline_management/agents/analytics_agent.py` (deprecated) | 465 | 🔴 |
| `agents/specialized/communication_agent.py` | `domains/pipeline_management/agents/communication_agent.py` (deprecated) | 390 | 🔴 |
| `services/candidate_comparison_service.py` | `domains/pipeline_management/services/candidate_comparison.py` | 958 | 🟢 |
| `services/candidate_report_service.py` | `domains/pipeline_management/services/candidate_report.py` | 927 | 🟢 |
| `services/stage_transition_automation.py` | `domains/pipeline_management/services/stage_transition.py` | 692 | 🟢 |
| `services/candidate_enrichment_service.py` | `domains/pipeline_management/services/candidate_enrichment.py` | 627 | 🟡 |
| `services/candidate_feedback_service.py` | `domains/pipeline_management/services/candidate_feedback.py` | 598 | 🟢 |
| `services/pipeline_stage_service.py` | `domains/pipeline_management/services/pipeline_stage.py` | 868 | 🟢 |
| `services/kanban_assistant_service.py` | `domains/pipeline_management/services/kanban_assistant.py` | 464 | 🟢 |
| `services/stage_automation_engine.py` | `domains/pipeline_management/services/stage_automation.py` | 450 | 🟢 |
| `services/predictive_analytics_service.py` | `domains/pipeline_management/services/predictive_analytics.py` | 866 | 🟡 |
| `services/pipeline_service.py` | `domains/pipeline_management/services/pipeline.py` | 314 | 🟢 |
| `services/pre_qualification_service.py` | `domains/pipeline_management/services/pre_qualification.py` | 354 | 🟢 |
| `tools/candidate_tools.py` | `domains/pipeline_management/tools.py` | 1.116 | 🟢 |

**Novos**: `domain.py` (~70L), `actions.py` (~50L)

---

### 16.8. FASE 7 — Migrar Domínio Scheduling

**Pré-requisitos**: Fase 0
**Perfil de portabilidade (Seção 15)**: 100% 🟡 Adaptação Menor — trocar mock de calendário por integração real

**Arquivos movidos**:
| De | Para | Linhas | Grau |
|---|---|:---:|:---:|
| `agents/specialized/scheduling_agent.py` | `domains/scheduling/agents/scheduling_agent.py` | 1.512 | 🟡 |
| `agents/interview_scheduling_nodes.py` | `domains/scheduling/agents/scheduling_nodes.py` | 418 | 🟡 |
| `services/scheduling_service.py` | `domains/scheduling/services/scheduling.py` | 1.020 | 🟡 |
| `services/calendar_service.py` | `domains/scheduling/services/calendar.py` | 305 | 🟡 |

**Novos**: `domain.py` (~60L), `actions.py` (~40L)

---

### 16.9. FASE 8 — Migrar Domínios Communication + ATS Integration

**Pré-requisitos**: Fase 0
**Perfil de portabilidade (Seção 15)**: Communication 50% 🟢/🟡 + 25% 🟠 + 25% 🔴 (maior risco). ATS 70% 🟠 (lógica boa, conexões são stubs). Fase que requer mais atenção.

#### Communication

**Arquivos movidos (principais)**:
| De | Para | Linhas | Grau |
|---|---|:---:|:---:|
| `services/email_service.py` | `domains/communication/services/email.py` | 2.864 | 🟠 |
| `services/communication_service.py` | `domains/communication/services/communication.py` | 2.445 | 🟡 |
| `services/notification_service.py` | `domains/communication/services/notification.py` | 1.261 | 🟡 |
| `services/recruitment_email_templates.py` | `domains/communication/services/email_templates.py` | 959 | 🟢 |
| `services/whatsapp_service.py` | `domains/communication/services/whatsapp.py` | 553 | 🟡 |
| `services/whatsapp_meta_service.py` | `domains/communication/services/whatsapp_meta.py` | 502 | 🟡 |
| `services/whatsapp_twilio_service.py` | `domains/communication/services/whatsapp_twilio.py` | 417 | 🟡 |
| `services/communication_dispatcher.py` | `domains/communication/services/dispatcher.py` | 359 | 🟡 |
| `services/communication_history_service.py` | `domains/communication/services/history.py` | 364 | 🟢 |
| `services/teams_service.py` | `domains/communication/services/teams.py` | 477 | 🔴 |
| `services/teams_*.py` (auth, bot, recording, simple) | `domains/communication/services/teams/` | ~1.300 | 🔴 |
| `services/email_providers/` | `domains/communication/services/email_providers/` | ~1.100 | 🟡 |
| `services/whatsapp_factory.py` | `domains/communication/services/whatsapp_factory.py` | 188 | 🟢 |
| `services/whatsapp_provider.py` | `domains/communication/services/whatsapp_provider.py` | 192 | 🟡 |
| `services/data_request_whatsapp_service.py` | `domains/communication/services/data_request_whatsapp.py` | 794 | 🟠 |
| `tools/communication_tools.py` | `domains/communication/tools.py` | 679 | 🟡 |

#### ATS Integration

**Arquivos movidos**:
| De | Para | Linhas | Grau |
|---|---|:---:|:---:|
| `agents/specialized/integrador_ats_agent.py` | `domains/ats_integration/agents/integrador_ats_agent.py` | 704 | 🟠 |
| `services/ats_sync_service.py` | `domains/ats_integration/services/ats_sync.py` | 943 | 🟠 |
| `services/ats_job_history_service.py` | `domains/ats_integration/services/ats_history.py` | 548 | 🟢 |
| `services/merge_ats_service.py` | `domains/ats_integration/services/merge_ats.py` | 443 | 🟠 |
| `services/gupy_service.py` | `domains/ats_integration/services/gupy.py` | 301 | 🟠 |
| `services/pandape_service.py` | `domains/ats_integration/services/pandape.py` | 260 | 🟠 |
| `services/ats_clients/` (inteiro) | `domains/ats_integration/services/clients/` | ~1.900 | 🟠 |

---

### 16.10. FASE 9 — Migrar Recruiter Assistant + Task Planning

**Pré-requisitos**: Fase 0
**Perfil de portabilidade (Seção 15)**: Recruiter Assistant 🟡 (adaptar interface). Task Planning 🟡 (adaptar contrato). Ambos de baixo risco.

**Recruiter Assistant**:
| De | Para | Linhas | Grau |
|---|---|:---:|:---:|
| `agents/specialized/recruiter_assistant_agent.py` | `domains/recruiter_assistant/agents/recruiter_assistant_agent.py` | 2.551 | 🟡 |
| `services/recruiter_personalization_service.py` | `domains/recruiter_assistant/services/personalization.py` | 554 | 🟢 |
| `services/briefing_service.py` | `domains/recruiter_assistant/services/briefing.py` | 476 | 🟢 |
| `services/proactive_alert_service.py` | `domains/recruiter_assistant/services/proactive_alerts.py` | 779 | 🟢 |
| `services/proactive_service.py` | `domains/recruiter_assistant/services/proactive.py` | 486 | 🟢 |

**Task Planning**:
| De | Para | Linhas | Grau |
|---|---|:---:|:---:|
| `agents/specialized/task_planner_agent.py` | `domains/task_planning/agents/task_planner_agent.py` | 821 | 🟡 |
| `services/planned_task_service.py` | `domains/task_planning/services/planned_tasks.py` | 702 | 🟢 |
| `services/task_service.py` | `domains/task_planning/services/tasks.py` | 660 | 🟢 |

---

### 16.11. FASE 10 — Limpeza e Consolidação

**Pré-requisitos**: Fases 1–9 completas e validadas

#### 16.11.1. Remover artefatos obsoletos

| Ação | Detalhe |
|------|---------|
| Remover `agents/specialized/` | Pasta vazia (todos os agentes já migraram para `domains/`) |
| Remover `agents/agent_registry.py` | Substituído por `domains/registry.py` |
| Remover `orchestrator/intent_router.py` | Substituído por `orchestrator/cascaded_router.py` |
| Remover re-exports em `services/` | Os re-exports criados na Fase 0 para compatibilidade |
| Remover `tools/` vazios | Tools específicos já em `domains/`; manter infra (registry, executor) |
| Limpar `base_agent.py` deprecated enums | Remover `JOB_INTAKE`, `SCREENING`, `COMMUNICATION`, `ANALYTICS` |

#### 16.11.2. Simplificar orchestrator

| Ação | Detalhe |
|------|---------|
| `orchestrator.py`: 1.112L → ~400L | Remover lógica de roteamento (agora em CascadedRouter) |
| Remover formatação inline | Agora feita pelo DomainWorkflow |
| Remover tool execution inline | Agora em `domain.execute_action()` |

#### 16.11.3. Atualizar imports globais

- Executar script automatizado para atualizar todos os imports
- Verificar que nenhum `from app.services.X import Y` aponta para arquivo que não existe
- Verificar que nenhum `from app.agents.specialized.X import Y` aponta para arquivo que não existe

#### 16.11.4. Validação final

| Teste | Esperado |
|-------|----------|
| `python -c "from app.domains.registry import DomainRegistry; print(DomainRegistry().list_domains())"` | Lista 11 domínios |
| Todos os endpoints API continuam respondendo | Sem regressão |
| Wizard conversacional funciona end-to-end | Todas as etapas |
| WSI screening pipeline funciona | Score gerado corretamente |
| Fast routing resolve ~80% das queries de teste | Keywords patterns funcionam |
| FairnessGuard bloqueia filtros discriminatórios | Mensagem educativa |

---

### 16.12. Grafo de Dependências entre Fases

```
FASE 0 (Infraestrutura)
  │
  ├──→ FASE 1 (Sourcing) ─── validação piloto
  │         │
  │         ▼
  ├──→ FASE 2 (Job Management) ← depende de validação do piloto
  │
  ├──→ FASE 3 (CV Screening)     ┐
  ├──→ FASE 4 (Interviewing)     │
  ├──→ FASE 5 (WSI Assessment)   ├── podem ser paralelas
  ├──→ FASE 6 (Pipeline Mgmt)    │
  ├──→ FASE 7 (Scheduling)       │
  ├──→ FASE 8 (Comm + ATS)       │
  ├──→ FASE 9 (Assistant + Tasks) ┘
  │
  └──→ FASE 10 (Limpeza) ← depende de TODAS as anteriores
```

**Caminho crítico**: Fase 0 → Fase 1 → Fase 2 → Fase 10
**Fases paralelizáveis**: 3, 4, 5, 6, 7, 8, 9 (todas dependem apenas da Fase 0)

### 16.13. Resumo de Esforço por Fase

| Fase | Linhas novas | Linhas movidas | Arquivos afetados | Complexidade |
|:----:|:------------:|:--------------:|:-----------------:|:------------:|
| 0 | ~1.400 | ~5.000 | ~20 | **Alta** |
| 1 | ~340 | ~8.600 | ~16 | **Média** |
| 2 | ~400 | ~25.000 | ~45 | **Alta** |
| 3 | ~100 | ~3.870 | ~7 | **Baixa** |
| 4 | ~100 | ~3.700 | ~8 | **Baixa** |
| 5 | ~130 | ~12.000 | ~20 | **Média-Alta** |
| 6 | ~120 | ~10.200 | ~17 | **Média** |
| 7 | ~100 | ~3.260 | ~6 | **Baixa** |
| 8 | ~160 | ~17.600 | ~30 | **Média** |
| 9 | ~100 | ~5.900 | ~9 | **Baixa** |
| 10 | 0 | 0 | ~15 (deletar) | **Média** |
| **Total** | **~2.950** | **~95.130** | **~193** | |

> **Nota**: O total de linhas movidas (~95.000) é maior que os ~35.000 estimados na Seção 14 porque aqui incluímos **todos os serviços** do domínio (189 arquivos), não apenas os agentes e tools. A diferença reflete o mapeamento completo arquivo-por-arquivo desta seção vs. a estimativa de alto nível da Seção 14.

### 16.14. Alinhamento com Mapa de Portabilidade (Seção 15)

> Esta seção cruza o perfil de portabilidade de cada fase com a estratégia de migração, garantindo que o esforço investido no protótipo Replit se traduz em máximo reaproveitamento pela Produção.

#### 16.14.1. Portabilidade por Fase

| Fase | Domínio | 🟢 Direto | 🟡 Menor | 🟠 Estrutural | 🔴 Referência | Risco | Valor para Produção |
|:----:|---------|:---------:|:--------:|:-------------:|:-------------:|:-----:|:-------------------:|
| 0 | Infraestrutura | — | — | — | — | **Alto** (código novo) | Habilita toda a migração |
| 1 | Sourcing | 80% | 20% | 0% | 0% | **Baixo** | Alto — WRF, Pearch, analytics |
| 2 | Job Management | 90% svcs | 5% | 5% agent | 0% | **Alto** (decomposição) | Muito Alto — wizard, templates |
| 3 | CV Screening | 95% | 0% | 0% | 5% | **Muito Baixo** | Alto — parser, scoring |
| 4 | Interviewing | 0% | 100% | 0% | 0% | **Baixo** | Médio — adaptar providers |
| 5 | WSI Assessment | 95%+ | 5% | 0% | 0% | **Muito Baixo** | **Máximo** — IP proprietário |
| 6 | Pipeline Mgmt | 85% | 10% | 0% | 5% | **Baixo** | Alto — kanban, analytics |
| 7 | Scheduling | 0% | 100% | 0% | 0% | **Muito Baixo** | Médio — adaptar calendário |
| 8 | Comm + ATS | 25% | 30% | 25% | 20% | **Alto** | Médio — stubs/providers |
| 9 | Assistant + Tasks | 40% | 60% | 0% | 0% | **Baixo** | Alto — proatividade |

#### 16.14.2. Ordem Ótima Considerando Portabilidade

A Seção 14 define a ordem por dependência técnica (Fase 0 → 1 → 2 → ...). Cruzando com portabilidade, a ordem também faz sentido estratégico:

1. **Fase 0** (Infraestrutura) — Obrigatória como pré-requisito
2. **Fase 1** (Sourcing, 80% 🟢) — Piloto ideal: baixo risco valida o padrão
3. **Fase 2** (Job Management, 90% 🟢 serviços) — Maior volume, mas serviços são copy-paste. Risco concentrado na decomposição do agent (🟠)
4. **Fases 3+5** (CV Screening + WSI, ambos 95%+ 🟢) — **Maior valor de IP com menor risco**. Recomenda-se executar logo após a Fase 1 para proteger o IP mais valioso
5. **Fases 4+7** (Interviewing + Scheduling, 100% 🟡) — Adaptação simples de providers
6. **Fase 6** (Pipeline, 85% 🟢) — Sem surpresas
7. **Fase 8** (Communication + ATS, alto % 🟠🔴) — **Deixar por último** — maior risco e menor portabilidade direta
8. **Fase 9** (Assistant + Tasks, 60% 🟡) — Baixo risco
9. **Fase 10** (Limpeza) — Sempre por último

> **Recomendação**: Se o objetivo é maximizar o que a Produção pode copiar do protótipo com mínimo esforço, priorizar as Fases 1, 3, 5 (alto 🟢) antes das Fases 4, 7, 8 (mais 🟡/🟠). A Fase 8 (Communication + ATS) é a que requer mais trabalho de adaptação — ideal para o final quando o padrão já está consolidado.

#### 16.14.3. Relação entre Seções 14, 15 e 16

| Seção | Função | Granularidade | Público-alvo |
|:-----:|--------|:------------:|:------------:|
| **14** | Plano conceitual de reestruturação A→B | Componente/padrão | Arquitetos (decisão) |
| **15** | Mapa de portabilidade arquivo-por-arquivo | Arquivo individual | Equipe B (copiar/adaptar) |
| **16** | Plano executável com fases detalhadas | Fase/arquivo/validação | Equipe Replit (executar) |

- A **Seção 14** define *o que* mudar e *por quê* (diagnóstico + componentes novos)
- A **Seção 15** classifica *o que vale a pena* portar (graus 🟢🟡🟠🔴)
- A **Seção 16** detalha *como* e *em que ordem* executar, usando os graus da Seção 15 para calibrar risco e esforço por fase

Juntas, as três seções formam um pipeline completo: **Análise → Classificação → Execução**.

---

## 17. Análise de Aproveitamento V5 — O Que o Protótipo Replit Entrega para a Produção

> **Objetivo**: Documentar com precisão o que foi implementado no protótipo Replit durante a convergência V5, o que pode ser diretamente aproveitado pelo time de produção, e o que **não** foi possível implementar no ambiente Replit (e por quê). Esta seção serve como guia de transferência tecnológica para o time de devs.
>
> **Data**: 12/02/2026 — Após conclusão da migração domain-driven (9 domínios, 199 actions, 93 tools) + 5 features V5 (253 testes passando).

---

### 17.1. Resumo Executivo

O protótipo Replit agora cobre **100% das capacidades definidas no documento de arquitetura original**, incluindo as 2 capacidades marcadas como "Futuras" (orquestração multi-agente e memória de longo prazo). Além disso, supera o documento com 2 domínios extras e 5 features de convergência que a Produção B ainda não implementou.

| Métrica | Antes da V5 | Depois da V5 | Δ |
|---|:---:|:---:|:---:|
| Domínios operacionais | 9 | 9 | — |
| Actions registradas | 199 | 199 | — |
| Tools registradas | 93 | 93 | — |
| Testes passando | 89 (base) | **253** (89 base + 164 V5) | **+184%** |
| Features V5 implementadas | 0/5 | **5/5** | +5 |
| Eixos de infra onde A > B | 6/10 | **7/10** | +1 |
| Componentes de B implementados | 3/5 | **5/5** | +2 |
| Capacidades do Orchestrator (doc) | 5/7 | **7/7** | +2 |
| Linhas novas em `shared/` | 0 | **2.162L** (10 arquivos) | Nova infraestrutura |

---

### 17.2. O Que FOI Implementado e Pode Ser Aproveitado

#### 17.2.1. ConversationMemory + ReferenceResolver (✅ Aproveitável: 95%)

**Arquivos**: `app/shared/memory/conversation_state.py`, `app/shared/memory/reference_resolver.py`

**O que faz**:
- `ConversationState`: mantém contexto da conversa entre mensagens (entities mencionadas, shortlist de candidatos, último domínio usado, histórico de ações)
- `ReferenceResolver`: resolve referências anafóricas em português ("dele", "o primeiro", "o anterior", "aquele candidato", "a vaga") usando 6 estratégias de resolução

**Testes**: 49 testes cobrindo edge cases de pronomes, posições ordinais, referências temporais, shortlist vazia, entidades ambíguas

**Aproveitamento pela Produção**:
| Componente | Grau | Adaptação necessária |
|---|:---:|---|
| `ConversationState` (dataclass) | 🟢 Direto | Nenhuma — stdlib puro |
| `ReferenceResolver` (6 estratégias) | 🟢 Direto | Nenhuma — regex + dataclass |
| Integração com StateManager | 🟡 Menor | Trocar StateManager por Redis/DB |
| Propagação no Orchestrator | 🟡 Menor | Adaptar ao fluxo de request da Produção |

**Design decisions aproveitáveis**:
- Resolução por tipo (pronome → ordinal → temporal → nome → fuzzy → fallback) — ordem otimizada para PT-BR
- Shortlist como `List[int]` com cap de `MAX_SHORTLIST=50` entidades — evita memory bloat mantendo IDs leves
- `conversation_state` propagado como campo de `base_context` no PlanExecutor — permite continuidade cross-step

---

#### 17.2.2. SmartExtractor — Extração de Parâmetros em 2 Estágios (✅ Aproveitável: 90%)

**Arquivos**: `app/shared/intelligence/smart_extractor.py`, `app/shared/intelligence/param_patterns.py`

**O que faz**:
- **Estágio 1 (Regex)**: 29 padrões regex organizados em 9 categorias (salário, quantidade, score, senioridade, modelo de trabalho, localização, data, skills, flags booleanos) para extrair parâmetros de queries em PT-BR. O padrão de skills inclui ~40 alternações (Python, Java, React, AWS, etc.). Resolve a maioria das extrações sem chamada LLM.
- **Estágio 2 (LLM Fallback)**: Apenas para queries complexas ou ambíguas que os regex não resolvem. Usa cache MD5 para evitar re-extração de queries idênticas.

**Testes**: 58 testes cobrindo extração de cada tipo de parâmetro, cache hits, fallback para LLM, edge cases de formatação brasileira (R$ 12.000, faixas salariais com "mil/k", senioridade com abreviações)

**Aproveitamento pela Produção**:
| Componente | Grau | Adaptação necessária |
|---|:---:|---|
| `param_patterns.py` (29 regex em 9 categorias) | 🟢 Direto | Nenhuma — stdlib `re` puro |
| `SmartExtractor` core | 🟢 Direto | Nenhuma — stdlib puro |
| Cache MD5 | 🟡 Menor | Trocar dict in-memory por Redis |
| Integração com Orchestrator | 🟡 Menor | Adaptar ao pipeline de extração da Produção |

**Impacto de custo**: Reduz chamadas LLM para extração de parâmetros nos casos onde os regex fazem match. A taxa real de hit depende do perfil das queries em produção — em testes com queries típicas de recrutamento PT-BR, a maioria dos parâmetros estruturados (salário, senioridade, localização, skills) são capturados por regex.

**Design decisions aproveitáveis**:
- Padrões regex organizados por tipo semântico (salary, quantity, score, seniority, work_model, location, date, skills, boolean_flags) — fácil de estender
- Fallback graceful — se regex falha, LLM assume sem interromper o fluxo
- Cache por hash MD5 da query normalizada — evita duplicatas mesmo com variações de case/espaço

---

#### 17.2.3. StatsManager — Cache Thread-Safe com TTL e LRU (✅ Aproveitável: 85%)

**Arquivo**: `app/shared/resilience/stats_manager.py`

**O que faz**:
- Singleton thread-safe com `threading.RLock` para acesso concorrente
- Cache com TTL (time-to-live) configurável por chave e LRU eviction quando atinge max_size
- Método `get_or_compute(key, compute_fn, ttl)` — retorna cache hit ou executa compute_fn e cacheia
- Métricas de hit/miss ratio para monitoramento

**Testes**: 32 testes cobrindo concorrência (multi-thread), eviction LRU, expiração TTL, singleton pattern, compute_fn com exceção

**Aproveitamento pela Produção**:
| Componente | Grau | Adaptação necessária |
|---|:---:|---|
| `StatsManager` core (singleton, RLock) | 🟡 Menor | Considerar trocar por Redis para multi-process |
| TTL + LRU logic | 🟢 Direto | Lógica reutilizável como está |
| `get_or_compute` pattern | 🟢 Direto | Pattern útil em qualquer cache layer |
| Hit/miss metrics | 🟢 Direto | Integrar com Prometheus/Datadog |

**Limitação importante**: O `threading.RLock` funciona para multi-thread (uvicorn workers), mas **não** para multi-process (gunicorn com prefork). Em produção com múltiplos processos, o cache precisa ser substituído por Redis ou similar. A **lógica** (TTL, LRU, get_or_compute) continua 100% aproveitável.

---

#### 17.2.4. ExecutionPlan — Orquestração Multi-Step Cross-Domain (✅ Aproveitável: 80%)

**Arquivos**: `app/shared/execution/execution_plan.py`, `app/shared/execution/plan_detector.py`, `app/shared/execution/plan_executor.py`

**O que faz**:
- **PlanDetector**: 12 padrões regex para detectar queries multi-etapa em PT-BR ("buscar candidatos e agendar entrevista", "criar vaga, triar CVs e enviar feedback"). **ZERO custo LLM** — detecção 100% por regex.
- **ExecutionPlan**: Estrutura de dados que modela um plano com steps, dependências entre steps, e status de execução. Cada step tem `domain_id`, `action`, `params`, e `depends_on`.
- **PlanExecutor**: Executa o plano respeitando dependências (DAG topológico), propaga `conversation_state` entre steps, e suporta retry com fallback para execução sequencial.

**Testes**: 70 testes cobrindo detecção de padrões, criação de planos, execução com dependências, propagação de estado, fallback em caso de falha, planos com 1-5 steps

**Aproveitamento pela Produção**:
| Componente | Grau | Adaptação necessária |
|---|:---:|---|
| `PlanDetector` (12 regex PT-BR) | 🟢 Direto | Nenhuma — regex puro |
| `ExecutionPlan` (dataclass) | 🟢 Direto | Nenhuma — stdlib puro |
| `PlanExecutor` (DAG execution) | 🟡 Menor | Trocar `DomainWorkflow.process()` pela chamada equivalente em B |
| Propagação de `conversation_state` | 🟡 Menor | Adaptar ao state management da Produção |
| Retry + fallback | 🟢 Direto | Lógica genérica, aproveitável |

**Design decisions aproveitáveis**:
- Detecção de planos por regex (ZERO LLM) — em produção, isso evita uma chamada LLM adicional para cada query
- DAG com resolução topológica — steps independentes podem ser paralelizados
- `conversation_state` propagado como `base_context` — permite que step 2 use resultados do step 1 via referências ("esses candidatos")

---

#### 17.2.5. Async Processing — Filas por Domínio com Prioridade (✅ Aproveitável: 70%)

**Arquivos**: `app/shared/async_processing/task_queue.py`, `app/shared/async_processing/task_manager.py`

**O que faz**:
- `DomainTaskQueue`: Fila asyncio por domínio com 4 níveis de prioridade (`LOW`/`NORMAL`/`HIGH`/`URGENT`), concurrency limit configurável, retry automático com `max_retries`, e lifecycle management (start/stop/drain)
- `DomainTaskManager`: Gerencia múltiplas filas (uma per-domain), oferece `submit_task()` que roteia automaticamente para a fila correta, e `shutdown()` com graceful drain

**Testes**: 30 testes cobrindo enqueue/dequeue, priorização, concurrency limits, lifecycle (start/stop/drain), submit multi-domain, shutdown graceful

**Aproveitamento pela Produção**:
| Componente | Grau | Adaptação necessária |
|---|:---:|---|
| `DomainTaskQueue` (asyncio) | 🟠 Estrutural | Produção usa RabbitMQ/Celery — lógica de prioridade é referência |
| `DomainTaskManager` (routing) | 🟡 Menor | Pattern de routing per-domain aproveitável |
| Prioridade LOW/NORMAL/HIGH/URGENT (4 níveis) | 🟢 Direto | Mapear para priority queues do RabbitMQ |
| Graceful shutdown + drain | 🟡 Menor | Adaptar para Celery worker shutdown |

**Limitação importante**: O protótipo usa `asyncio.Queue` (in-process). Em produção, isso precisa ser substituído por um message broker (RabbitMQ, Redis Streams, ou Celery). No entanto, a **arquitetura** (fila per-domain, priorização, graceful shutdown) é diretamente transferível como design pattern.

---

### 17.3. Cobertura das 7 Capacidades do Orchestrator — Antes vs. Depois

O documento de arquitetura define 7 capacidades obrigatórias para o Orchestrator:

| # | Capacidade do Documento | Antes da V5 | Depois da V5 | Feature V5 que resolveu |
|:---:|---|:---:|:---:|---|
| 1 | Classificar intenção do usuário | ✅ CascadedRouter | ✅ | — (já existia) |
| 2 | Rotear para agente correto | ✅ DomainRegistry + FastRouter | ✅ | — (já existia) |
| 3 | Manter histórico/estado da conversa | ⚠️ StateManager básico | **✅** | **ConversationMemory + ConversationState** |
| 4 | Sugerir ações contextuais | ✅ DomainResponse.suggestions | ✅ | — (já existia) |
| 5 | Aprender preferências do usuário | ✅ Learning Loop System | ✅ | — (já existia) |
| 6 | Orquestrar pipelines multi-agente | **❌ Não existia** | **✅** | **ExecutionPlan (PlanDetector + PlanExecutor)** |
| 7 | Memória de longo prazo entre sessões | ⚠️ conversation_memory básico | **✅** | **ConversationMemory + ReferenceResolver** |

**Resultado: 5/7 → 7/7 (100% de cobertura).**

As capacidades 6 e 7 eram marcadas como "Futuras" no documento original e agora estão implementadas.

---

### 17.4. Comparação de Infraestrutura (10 Eixos) — Protótipo A vs. Produção B

| # | Eixo | Protótipo A (Replit) | Produção B | Quem lidera |
|:---:|---|---|---|:---:|
| 1 | **Roteamento** | Cascata: memory→fast→LLM + PlanDetector | Cascata: memory→fast→LLM | **A** (PlanDetector é extra) |
| 2 | **Comunicação inter-domínio** | REST síncrono + Async Task Queues (asyncio) | RabbitMQ + Celery | **B** (infra distribuída) |
| 3 | **Escalabilidade** | Single-process, workers asyncio per-domain | Multi-process, horizontal scaling | **B** (multi-node) |
| 4 | **Modularidade** | DomainRegistry + @register_domain | DomainRegistry + @register_domain | **Empate** |
| 5 | **Performance (custo LLM)** | FastRouter ~80% sem LLM + SmartExtractor (29 regex, 9 categorias) | FastRouter ~80% sem LLM | **A** (SmartExtractor é extra) |
| 6 | **Compliance** | 3 pilares completos (LGPD + SOX + EU AI Act) | LGPD parcial | **A** |
| 7 | **Aprendizagem** | Learning Loop + templates + outcome learning | Learning Loop básico | **A** |
| 8 | **Cobertura funcional** | 9 domínios + 199 actions + 93 tools | 7 domínios (parciais) | **A** |
| 9 | **Governança de IA** | Monitoring + XAI + audit + FairnessGuard + FactChecker | Monitoring básico | **A** |
| 10 | **Resiliência** | Circuit breaker + feature flags + StatsManager + retry em plans | Circuit breaker | **A** |

**Resultado: A lidera em 7 eixos, B lidera em 2, empate em 1.**

---

### 17.5. O Que NÃO Foi Possível Implementar no Replit (e Por Quê)

Esta seção documenta as limitações reais do ambiente de prototipagem e o que o time de produção precisa implementar nativamente.

#### 17.5.1. Infraestrutura Distribuída

| Componente | Por que não foi implementado | O que existe como referência | Esforço para Produção |
|---|---|---|:---:|
| **RabbitMQ / Message Broker** | Replit não suporta serviços de infraestrutura externos como message brokers. Não é possível instalar/rodar RabbitMQ no ambiente. | `DomainTaskQueue` com asyncio simula o padrão de filas per-domain com prioridade. A arquitetura (routing, prioridade, shutdown) é transferível. | **Médio** |
| **Celery Workers** | Celery requer um broker (Redis/RabbitMQ) que não está disponível. Workers multi-process não são viáveis no ambiente single-container. | `DomainTaskManager` implementa o pattern de task submission e routing per-domain. | **Médio** |
| **Redis (como cache distribuído)** | Embora Replit suporte PostgreSQL, Redis não está disponível como serviço nativo. O `StatsManager` usa dict in-memory como alternativa. | `StatsManager` tem a lógica completa de TTL + LRU + get_or_compute. Trocar o backend para Redis é substituir ~30 linhas. | **Baixo** |
| **Horizontal Scaling** | Container único, sem load balancer. Não é possível testar multi-instance. | DomainRegistry e CascadedRouter são stateless — funcionam em múltiplas instâncias sem adaptação. | **Baixo** |

#### 17.5.2. Integrações Externas Reais

| Integração | Estado real no código | O que existe | O que falta | Esforço |
|---|---|---|---|:---:|
| **Gupy / Pandapé / Merge / StackOne (ATS)** | **4 clientes completos** com chamadas HTTP reais via `httpx`. Cada um tem 15-18 métodos (`get_candidate`, `list_jobs`, `create_candidate`, `update_status`, etc.). Total: 1.911L em `app/services/ats_clients/`. | Lógica de sync bidirecional, mapping de campos, `ATSClient` base class com contrato padronizado, duplicados nos domínios (`app/domains/ats_integration/services/ats_clients/`). | Credenciais de produção, ambientes sandbox, e contratos ativos com os providers. | **Baixo** (só configurar API keys) |
| **OpenMic (Voz)** | **Serviço funcional** com 720L, chamadas HTTP reais via `httpx`, webhook handler completo, processamento de transcrição, e integração com WSI screening. | `openmic_service.py` (720L) + endpoint `/openmic` (433L) com webhook, health check, e screening call. Lógica de análise de transcrição e scoring WSI integrada. | API key de produção + WebSocket estável para streaming. | **Baixo** (só configurar API key) |
| **Deepgram (Voz)** | **Minimal** — apenas 1 linha (re-export). Serviço real não implementado no protótipo. | Referência de interface (`TranscriptionResult` type). | Implementação completa do serviço + API key. | **Médio** |
| **Microsoft Teams (Bot)** | **Endpoint robusto** com 869L — lógica de autenticação, bot framework, e recording implementados. | `app/api/v1/teams.py` (869L) com handlers de mensagem, eventos, e integração com Microsoft Graph. | Registro de app no Azure AD, webhook público, certificado SSL. | **Alto** |
| **Iugu (Billing)** | **Provider placeholder** — estrutura completa mas marcado como "placeholder implementation" no próprio código. Nota: o protótipo usa **Iugu** (gateway BR), **não Stripe**. | `iugu_provider.py` (489L) + `billing.py` endpoint (1.656L) + `base.py` (408L) com interface `BillingProviderBase`. | Implementação real das chamadas API + SDK Iugu + testes com sandbox. | **Médio** |
| **SendGrid (Email)** | **Serviço quase completo** — 2.864L com integração SendGrid SDK, templates, dispatcher, webhook handling. Nota: o protótipo usa **SendGrid**, **não Mailgun/SMTP**. | `email_service.py` (2.864L em `app/domains/communication/services/`) com `SendGridEmailService`, templates HTML, tracking de opens/clicks, webhook events. | API key do SendGrid + `pip install sendgrid`. | **Baixo** (quase pronto) |

#### 17.5.3. Persistência e Database

| Componente | Por que não foi implementado | O que existe | Esforço |
|---|---|---|:---:|
| **Elasticsearch** | Não disponível como serviço no Replit. A pesquisa semântica usa PostgreSQL com pg_vector como alternativa. | Lógica de scoring, WRF (Weighted Rank Fusion), e análise de relevância — toda transferível para ES. | **Médio** |
| **Migrations de DB** | O foco foi na camada de agentes/domínios, não no schema de banco. Modelos SQLAlchemy existem, mas migrations não foram executadas neste ciclo. | Modelos completos em `models/`. Migrations via Alembic configuradas. | **Baixo** |
| **Embeddings vetoriais em escala** | pg_vector funciona, mas com limitação de performance para milhões de vetores. Produção pode precisar de Pinecone/Weaviate. | `embedding_service.py` com interface genérica — trocar provider é ~50 linhas. | **Baixo** |

#### 17.5.4. Testes End-to-End e Integração

| Tipo de teste | Por que não foi implementado | O que existe | Esforço |
|---|---|---|:---:|
| **Testes E2E com LLM real** | Chamadas reais de LLM são caras e não-determinísticas. Todos os testes V5 usam mocks/stubs para garantir reprodutibilidade. | 253 testes unitários com mocks que validam toda a lógica. Produção precisa adicionar testes de integração com LLM real (amostragem). | **Médio** |
| **Testes de carga** | Container único com recursos limitados não permite testes de stress realistas. | Benchmarks de SmartExtractor e FastRouter indicam latência sub-millisecond para regex. Load testing precisa de ambiente dedicado. | **Médio** |
| **Testes de integração cross-service** | Sem RabbitMQ/Redis, não é possível testar comunicação real entre serviços distribuídos. | PlanExecutor testa execução cross-domain via chamada direta. Padrão adaptável para message-based. | **Médio** |

#### 17.5.5. Segurança e Produção

| Componente | Por que não foi implementado | O que existe | Esforço |
|---|---|---|:---:|
| **Rate limiting por tenant** | Requer infra de contagem distribuída (Redis) e middleware de produção. | Feature flags com granularidade por tenant. Rate limiting é adição incremental. | **Baixo** |
| **Audit trail persistido** | Audit service existe, mas logs vão para stdout no Replit. Produção precisa de persistent storage (CloudWatch, ELK). | `audit_service.py` com lógica completa de registro de ações. Só precisa trocar o sink. | **Baixo** |
| **Encryption at rest** | Gerenciado pelo provider de DB, não pelo código da aplicação. | LGPD service com lógica de anonimização e consent management. | **N/A** |

---

### 17.6. Tabela de Decisão: O Que Copiar vs. Adaptar vs. Reimplementar

Para facilitar a triagem do time de produção, esta tabela classifica cada componente V5:

| Componente | Linhas | Testes | Copiar? | Adaptação | Reimplementar? |
|---|:---:|:---:|:---:|---|:---:|
| `param_patterns.py` (29 regex, 9 categorias) | 240L | 58 | **Sim, direto** | Nenhuma | Não |
| `SmartExtractor` core | 213L | (incl. acima) | **Sim, direto** | Trocar cache dict→Redis | Não |
| `ConversationState` dataclass | 146L | 49 | **Sim, direto** | Nenhuma | Não |
| `ReferenceResolver` (6 resolvers) | 315L | (incl. acima) | **Sim, direto** | Nenhuma | Não |
| `PlanDetector` (12 regex patterns) | 234L | 70 | **Sim, direto** | Nenhuma | Não |
| `ExecutionPlan` dataclass | 149L | (incl. acima) | **Sim, direto** | Nenhuma | Não |
| `PlanExecutor` (DAG execution) | 231L | (incl. acima) | **Sim, adaptar** | Trocar `DomainWorkflow.process()` pela chamada equivalente | Não |
| `StatsManager` (singleton + TTL + LRU) | 217L | 32 | **Sim, adaptar** | Trocar `threading.RLock` + dict por Redis wrapper | Não |
| `DomainTaskQueue` (asyncio) | 214L | 30 | **Referência** | Lógica de prioridade e routing → aplicar em RabbitMQ/Celery | Parcial |
| `DomainTaskManager` (routing) | 203L | (incl. acima) | **Referência** | Pattern de submit + routing per-domain → aplicar em Celery | Parcial |

**Resumo**: De 2.162 linhas novas V5 (10 arquivos em `app/shared/`):
- **~1.297L** (60%) podem ser copiadas diretamente — `param_patterns` (240L) + `SmartExtractor` (213L) + `ConversationState` (146L) + `ReferenceResolver` (315L) + `PlanDetector` (234L) + `ExecutionPlan` (149L)
- **~448L** (21%) podem ser copiadas com adaptação menor — `PlanExecutor` (231L) + `StatsManager` (217L) — trocar backend de cache/state
- **~417L** (19%) servem como referência de design — `DomainTaskQueue` (214L) + `DomainTaskManager` (203L) — lógica de filas asyncio → RabbitMQ/Celery

---

### 17.7. Decisões de Design que o Time Deve Preservar

Estas decisões foram validadas com 253 testes e devem ser preservadas na produção:

#### 17.7.1. Princípio: Regex antes de LLM, sempre
```
Query → SmartExtractor (29 regex, 9 categorias) → LLM fallback (queries não-estruturadas)
Query → PlanDetector (12 patterns multi-step) → ZERO LLM
Query → FastRouter (keywords por domínio) → LLM fallback (queries ambíguas)
```
**Impacto estimado em produção**: A taxa de hit dos regex depende do perfil real das queries. Em cenários típicos de recrutamento PT-BR (onde parâmetros como senioridade, localização, skills são explícitos), a maior parte do roteamento e extração pode ser resolvida sem LLM. O impacto financeiro exato deve ser medido em produção com telemetria.

#### 17.7.2. Princípio: Fail gracefully, nunca bloquear
Toda integração V5 no Orchestrator e DomainWorkflow usa `try/except` com logging:
```python
try:
    conversation_state = self.memory.get_state(session_id)
    resolved = self.resolver.resolve(message, conversation_state)
except Exception as e:
    logger.warning(f"Memory/resolver failed: {e}")
    resolved = message  # fallback: usa mensagem original
```
**Por quê**: Features V5 são enhancement, não core. Se falharem, o fluxo principal continua funcionando exatamente como antes.

#### 17.7.3. Princípio: Zero dependências externas para lógica core
Todas as 5 features V5 usam **exclusivamente** stdlib Python:
- `re` para regex
- `hashlib` para cache keys
- `threading` para concorrência
- `asyncio` para filas
- `dataclasses` para estruturas de dados
- `logging` para observabilidade
- `enum` para tipagem

**Por quê**: Isso torna o código portável para qualquer ambiente Python 3.10+ sem instalação de pacotes. O time de produção pode copiar os arquivos e eles funcionam imediatamente.

#### 17.7.4. Princípio: conversation_state como contexto propagado
O `conversation_state` é propagado como campo dentro de `base_context` (dict), não como variável global ou parâmetro separado. Isso permite:
- Steps do ExecutionPlan compartilharem contexto
- DomainWorkflow acessar estado sem coupling direto com ConversationMemory
- Serialização simples para persistence (dict → JSON)

---

### 17.8. Roadmap de Integração para o Time de Produção

Ordem recomendada de integração dos componentes V5, considerando dependências e impacto:

```
SPRINT 1 — Quick Wins (impacto imediato, zero dependência):
├── 1. Copiar param_patterns.py (29 regex, 9 categorias) → integrar no pipeline de extração existente
├── 2. Copiar SmartExtractor → usar como pre-filter antes de LLM extraction
├── 3. Copiar PlanDetector (12 patterns) → adicionar detecção de multi-step no Orchestrator
└── Resultado: Redução de chamadas LLM para extração de parâmetros estruturados + detecção de planos

SPRINT 2 — Memória Conversacional (requer Redis):
├── 4. Copiar ConversationState + ReferenceResolver
├── 5. Implementar persistence em Redis (substituir dict in-memory)
├── 6. Integrar no Orchestrator: resolver referências antes de rotear
└── Resultado: Usuários podem dizer "dele", "o anterior" — UX significativamente melhor

SPRINT 3 — Execução Multi-Step (requer Sprint 1 + 2):
├── 7. Copiar ExecutionPlan + PlanExecutor
├── 8. Adaptar PlanExecutor para chamar DomainWorkflow de B
├── 9. Configurar propagação de conversation_state entre steps
└── Resultado: Queries como "buscar candidatos e agendar entrevista" funcionam

SPRINT 4 — Cache e Performance (requer Redis):
├── 10. Adaptar StatsManager para usar Redis como backend
├── 11. Integrar no Analytics domain para cache de dashboards
└── Resultado: Latência de queries de analytics reduzida em ~90%

SPRINT 5 — Async Processing (requer RabbitMQ/Celery):
├── 12. Usar DomainTaskQueue como referência de design
├── 13. Implementar filas per-domain no RabbitMQ
├── 14. Mapear prioridades LOW/NORMAL/HIGH/URGENT para priority queues
└── Resultado: Tarefas pesadas (enrichment, screening) processadas em background
```

---

### 17.9. Métricas de Qualidade do Código V5

| Métrica | Valor | Significado |
|---|:---:|---|
| **Testes totais V5** | 253 | Cobertura extensiva de edge cases |
| **Testes de regressão** | 14 | Protegem contra breaking changes no fluxo principal |
| **Dependências externas** | 0 | Portabilidade máxima |
| **Linhas por arquivo (média)** | ~180L | Arquivos focados e legíveis |
| **Cyclomatic complexity (estimada)** | Baixa | Lógica linear com early returns |
| **Thread-safety** | ✅ (StatsManager) | Validado com testes multi-thread |
| **Async-safety** | ✅ (TaskQueue) | Validado com testes asyncio |
| **Fallback em caso de falha** | ✅ (todas features) | try/except com logging, nunca bloqueia |

---

### 17.10. Conclusão da Análise V5

O protótipo Replit agora representa a **implementação mais completa da arquitetura LIA**, superando tanto o documento de arquitetura original (7/7 capacidades + extras) quanto a Produção B (7/10 eixos de infraestrutura).

**Para o time de devs**: ~60% do código V5 pode ser copiado e usado imediatamente (stdlib puro). ~25% requer adaptação menor (trocar backend de cache). ~15% serve como referência de design para componentes que precisam de infra distribuída (RabbitMQ, Celery).

**Próximos passos recomendados**: Seguir o roadmap da Seção 17.8, começando pelo Sprint 1 (Quick Wins) que gera economia de LLM imediata sem nenhuma dependência de infraestrutura nova.

---

## 18. Guia Consolidado de Aproveitamento — Visão Completa por Camada

> **Objetivo**: Unificar as análises das Seções 15 (portabilidade do protótipo inteiro) e 17 (features V5) num único guia que responda: **"O que exatamente meu time consegue aproveitar, em cada camada, e como?"**

### 18.1. Mapa Geral: O Que Existe e Para Onde Vai

O protótipo Replit contém **~347.100 linhas** de código (conforme inventário da Seção 15.8, atualizado pós-portabilidade) + **2.162 linhas** de features V5 (Seção 17). A produção opera com Ruby on Rails (backend) e planeja Vue.js/Nuxt para o frontend. Agentes de IA usam LangGraph em ambos os ambientes. Nem tudo cola direto — mas a maior parte da **lógica de negócio, prompts, e padrões arquiteturais** independe de framework.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PROTÓTIPO REPLIT (Python/Next.js)                │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐                │
│  │   Agentes    │  │   Services  │  │  V5 Features │                │
│  │  ~33.800L    │  │  ~115.600L  │  │   2.162L     │                │
│  │  Python      │  │  Python     │  │   Python     │                │
│  │  ✅ APROVEITA│  │  ✅ APROVEITA│  │  ✅ APROVEITA│                │
│  └─────────────┘  └─────────────┘  └──────────────┘                │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐                │
│  │   Tools      │  │ Orchestrator│  │Models/Schemas│                │
│  │  ~10.000L    │  │   ~2.200L   │  │  ~35.700L    │                │
│  │  Python      │  │  Python     │  │  Pydantic    │                │
│  │  ✅ APROVEITA│  │  ✅ APROVEITA│  │  📋 SPEC     │                │
│  └─────────────┘  └─────────────┘  └──────────────┘                │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐                │
│  │  Endpoints   │  │  Frontend   │  │ Documentação │                │
│  │  ~101.300L   │  │ ~1.059 arqs │  │  ~2.864L     │                │
│  │  FastAPI     │  │ React/Next  │  │  Markdown    │                │
│  │  📋 SPEC     │  │  📋 SPEC    │  │  ✅ 100%     │                │
│  └─────────────┘  └─────────────┘  └──────────────┘                │
│                                                                     │
│  ✅ = Código Python aproveitável     📋 = Spec funcional/referência │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 18.2. Camada por Camada: O Que, Como, e Prioridade

#### 18.2.1. Código Python — Camada de Maior Valor (~197.500L total, ~58% aproveitável direto/menor)

Esta é a camada de maior valor. A produção usa Python para os agentes de IA (LangGraph), portanto o código transfere **diretamente** nesta camada.

| Subcamada | Linhas | Aproveitamento | Forma de aproveitamento |
|-----------|:------:|:--------------:|------------------------|
| **Agentes especializados** | 33.800 | 67% (22.500L direto/menor) | Copiar lógica de cada agente, adaptar interface `BaseAgent` → `DomainPrompt`. Prompts (~3.200L) e few-shot examples (~1.600L) são **IP puro** e transferem sem alteração. (Ref: Seção 15.2) |
| **Services de negócio** | 115.600 | 81% (94.000L direto/menor) | Copiar services inteiros — WSI assessment, job management, learning loop, sourcing pipeline. Adaptar imports e injeção de dependência. (Ref: Seção 15.4) |
| **Tools (ações executáveis)** | 10.000 | 91% (9.100L direto/menor) | Distribuir por domínio conforme mapeamento da Seção 15.3. Mudar `@register_tool` → `DomainActions.register()`. |
| **Orchestrator** | 2.200 | 25% direto + 75% estrutural | `CascadedRouter`, `FastRouter`, `StateManager` — core do roteamento. Adaptar para infra de produção. (Ref: Seção 15.5) |
| **Core/Config/Utils** | 33.700 | 89% (30.000L direto/menor) | Circuit breakers, validation, config — transferência direta. (Ref: Seção 15.8) |
| **V5 Features** | 2.162 | 60% direto, 21% adaptar | Copiar `app/shared/` inteiro. Ver roadmap detalhado na Seção 17.8. |

**Derivação dos totais** (alinhado com Seção 15.8):
- Da Seção 15.8: ~115.150L (Direto) + ~76.700L (Menor) = **~191.850L** aproveitáveis com esforço baixo-médio, de ~332.300L
- V5 Features adicionam: 1.297L (direto) + 448L (adaptar) = **1.745L** extras
- **Total aproveitável (baixo-médio esforço)**: ~193.600L de ~334.500L (**~58%**)

**O que NÃO transfere direto nesta camada**:
- Stubs de integrações externas (Gupy, Pandapé, Merge — ~5.000L) → reimplementar com APIs reais
- Base classes legadas (`base_agent.py`, `agent_registry.py`) → substituir por `DomainPrompt`/`DomainRegistry`
- Agentes deprecated (`analytics_agent.py`, `screening_agent.py`, `communication_agent.py`) → já foram mergeados

---

#### 18.2.2. LangGraph/LangChain — Aproveitável com Adaptação (~8.500L)

O protótipo usa LangGraph para definir fluxos de agentes como grafos. A produção pode aproveitar:

| Componente | Linhas | O que aproveitar | Adaptação |
|-----------|:------:|-----------------|-----------|
| `job_wizard_graph.py` | 401 | Definição do fluxo conversacional do wizard | Adaptar nós para `DomainWorkflow` |
| `conversation.py` | 1.657 | Fluxo conversacional geral LangGraph | Mapear states/edges para `DomainWorkflow` |
| `job_vacancy_nodes.py` | 1.543 | Nós de processamento de vaga | Mover para domain `job_management` |
| `sourcing_engagement_nodes.py` | 1.354 | Nós de engagement de candidatos | Mover para domain `sourcing` |
| `interview_scheduling_nodes.py` | 418 | Nós de agendamento | Mover para domain `interview_scheduling` |
| `nodes.py` | 1.292 | Nós genéricos reutilizáveis | Distribuir por domínio ou `shared` |
| **Prompts e Few-shot** | ~3.200 | **IP mais valioso** — transferência 100% | Nenhuma |

**Decisão para o time**: Se a produção **já usa LangGraph**, os grafos podem ser adaptados diretamente. Se usa outro framework de orquestração, os **nós** (funções Python) e **prompts** (strings) transferem independente do framework — só a definição do grafo muda.

---

#### 18.2.3. FastAPI/Endpoints — Referência Funcional (~101.300L)

O protótipo usa FastAPI; a produção usa **Ruby on Rails**. O código das rotas **não cola direto**, mas serve como **spec funcional completa**:

| O que aproveitar | Como usar | Exemplo |
|-----------------|-----------|---------|
| **Contratos de API** (request/response) | Traduzir Pydantic schemas → Rails strong params/serializers | `JobCreateRequest` → `job_params` |
| **Validações de negócio** | Replicar regras de validação nos controllers | Score ranges, required fields, date logic |
| **Lógica de middleware** | Reimplementar auth, tenant scoping, rate limiting | JWT validation, multi-tenant headers |
| **Swagger/OpenAPI specs** | Usar como documentação de contrato entre front e back | Endpoints, métodos, payloads |

**Estimativa**: ~50.000L têm lógica de negócio aproveitável como spec. ~51.300L são boilerplate FastAPI (imports, decorators, error handling) que Rails gera de forma diferente.

---

#### 18.2.4. Models e Schemas Pydantic — Spec para Rails (~35.700L)

| O que é | O que aproveitar | Como |
|---------|-----------------|------|
| **Pydantic Models** (~24.600L) | Estrutura de dados, tipos, validações | Traduzir para ActiveRecord models + validations |
| **Schemas** (~11.100L) | Request/Response contracts | Traduzir para Rails serializers (ActiveModel::Serializer ou Blueprinter) |

**Dica prática**: Cada `class CandidateModel(BaseModel)` mapeia 1:1 para um `class Candidate < ApplicationRecord` com as mesmas validações. Os `Field(...)` do Pydantic mapeiam para `validates` do ActiveRecord.

---

#### 18.2.5. Frontend React/Next.js — Referência de UX (~1.059 arquivos)

A produção planeja usar **Vue.js + Nuxt**. O código React **não cola**, mas:

| O que aproveitar | Como usar |
|-----------------|-----------|
| **Componentes do Storybook** | Referência visual — cores, espaçamentos, hierarquia, comportamento interativo |
| **Lógica de estado do wizard** | Fluxo de etapas, validações client-side, transições → reimplementar em Vue |
| **Design system (Tailwind + Radix)** | Paleta, tipografia, padrões de UI → aplicar no Vue com mesmo Tailwind |
| **Contratos de API consumidos** | Hooks/services que chamam API → definem o contrato que o backend Rails precisa servir |
| **Chat conversacional (LIA)** | Padrão de UX do chat, streaming de respostas, referências visuais |

**Valor real**: O Storybook documentado é o ativo mais útil do frontend — o time de Vue pode ver exatamente como cada componente se comporta sem ler código React.

---

#### 18.2.6. Documentação — 100% Aproveitável (~2.864L + docs/)

| Documento | Valor |
|-----------|-------|
| `architecture-comparison-analysis.md` (este) | Spec completa: 9 domínios, 199 actions, 93 tools, gap analysis, roadmap |
| `docs/ai-prompts/` | Catálogo de prompts calibrados e testados |
| `docs/methodology/wsi/` | Metodologia WSI completa — avaliação, entrevista, templates |
| `docs/methodology/AI_GOVERNANCE.md` | Governança de IA — fairness, compliance, auditoria |
| `docs/architecture/` | Roadmap de implementação, relatório de auditoria |
| `docs/integrations/` | Specs de integração ATS (Gupy, Pandapé, Pearch) |

---

### 18.3. Tabela de Decisão Rápida: "O Que Faço Com Cada Camada?"

> **Nota**: Esta tabela complementa a Seção 17.6 (decisão V5) com uma visão mais ampla por camada. Para decisão específica de componentes V5, consultar 17.6.

| Camada | Linguagem destino | Ação | Prioridade |
|--------|:-----------------:|:----:|:----------:|
| Agentes Python | Python (mesmo) | **Copiar + adaptar interface** | 🔴 Alta |
| Prompts e few-shot | Agnóstico | **Copiar direto** | 🔴 Alta |
| Services de negócio | Python (mesmo) | **Copiar + adaptar DI** | 🔴 Alta |
| Tools (ações) | Python (mesmo) | **Copiar + redistribuir por domínio** | 🟠 Média |
| WSI Assessment | Python (mesmo) | **Copiar intacto — IP proprietário** | 🔴 Alta |
| V5 Features (`shared/`) | Python (mesmo) | **Copiar conforme roadmap Seção 17.8** | 🟠 Média |
| Orchestrator | Python (mesmo) | **Copiar CascadedRouter + FastRouter** | 🟠 Média |
| LangGraph grafos | Python (mesmo) | **Adaptar nós para DomainWorkflow** | 🟡 Baixa |
| Models Pydantic | Ruby (Rails) | **Traduzir para ActiveRecord** | 🟠 Média |
| Endpoints FastAPI | Ruby (Rails) | **Usar como spec → reimplementar** | 🟡 Baixa |
| Frontend React | Vue.js (Nuxt) | **Referência de UX via Storybook** | 🟡 Baixa |
| Documentação | N/A | **Usar como guia de implementação** | 🔴 Alta |

---

### 18.4. Resposta Direta: "Só o Python?" — Não.

O time aproveita **4 tipos de ativo**, não só código Python:

```
1. CÓDIGO PYTHON (~197.500L entre agents/services/tools/orchestrator/shared)
   └── ~58% aproveitável com esforço baixo-médio (Seção 15.8)
   └── Transfere direto porque produção também usa Python + LangGraph

2. ESPECIFICAÇÕES FUNCIONAIS (~137.000L como referência)
   └── Endpoints FastAPI → spec de API para Rails
   └── Models Pydantic → spec de dados para ActiveRecord
   └── Schemas → spec de contratos front↔back

3. REFERÊNCIA DE UX (~1.059 arquivos React)
   └── Storybook → visual reference para equipe Vue.js
   └── Design system → Tailwind configs reutilizáveis
   └── Fluxos de wizard/chat → spec de comportamento

4. DOCUMENTAÇÃO (~3.100L + docs/)
   └── Arquitetura completa dos 9 domínios
   └── Metodologia WSI proprietária
   └── Prompts calibrados com few-shot examples
   └── Governança de IA e compliance
```

### 18.5. Sequência Recomendada de Adoção

> **Nota**: Esta sequência expande o roadmap da Seção 17.8 (focado em V5) para cobrir todas as camadas. Para integração específica de features V5, consultar 17.8.

```
FASE 1 — Fundação (Semanas 1-2):
├── Copiar documentação integral (este doc + docs/)
├── Copiar prompts e few-shot examples (IP puro, zero dependência)
├── Copiar WSI Assessment inteiro (~11.000L, 95% direto)
└── Resultado: Base de conhecimento e metodologia disponíveis

FASE 2 — Core Python (Semanas 3-6):
├── Copiar services de Job Management (~21.000L)
├── Copiar tools executáveis (~10.000L)
├── Copiar Orchestrator (CascadedRouter + FastRouter)
├── Copiar V5 Sprint 1: param_patterns + SmartExtractor + PlanDetector
└── Resultado: Pipeline de IA funcional

FASE 3 — Domínios Especializados (Semanas 7-10):
├── Copiar agentes de Sourcing, CV Screening, Interview
├── Adaptar LangGraph nós para DomainWorkflow
├── Copiar V5 Sprints 2-3: ConversationMemory + ExecutionPlan
└── Resultado: 9 domínios operacionais

FASE 4 — Backend Rails (Semanas 11-14):
├── Traduzir Pydantic models → ActiveRecord
├── Reimplementar endpoints usando specs FastAPI
├── Copiar V5 Sprints 4-5: StatsManager + Async Processing
└── Resultado: Backend Rails com paridade funcional

FASE 5 — Frontend Vue (Semanas 15-18):
├── Usar Storybook como referência visual
├── Reimplementar componentes em Vue.js + Nuxt
├── Aplicar design system (Tailwind config reutilizável)
└── Resultado: Frontend com paridade de UX
```

---

### 18.6. Métricas Consolidadas

> Métricas atualizadas pós-fase de portabilidade (Fev 2026). Ver Seção 15.8 para tabela completa.

| Métrica | Valor | Fonte |
|---------|:-----:|:-----:|
| Total de código no protótipo | ~347.100L (inclui camadas de portabilidade) | Seção 15.8 |
| Aproveitável baixo-médio esforço (Direto + Menor) | ~226.900L (~65%) | Seção 15.8 + 17.6 |
| Aproveitável com adaptação estrutural | ~72.850L (~21%) | Seção 15.8 |
| Referência funcional apenas | ~47.350L (~14%) | Seção 15.8 |
| V5 Features novos (`app/shared/`) | 2.162L (10 arquivos) | Seção 17 |
| Testes validando o código | 109 regressão + V5 | Seção 17.9 + 22 |
| Prompts calibrados (IP proprietário) | ~3.200L (100% aproveitável) | Seção 15.2 |
| Documentação técnica | ~3.100L + 10 docs auxiliares | Este documento |
| Domínios mapeados | 9 com 199 actions e 93 tools | Seção 5 |
| Tempo estimado de adoção completa | 15-18 semanas (5 fases) | Seção 18.5 |

> **Referências cruzadas**: Para detalhes por arquivo → Seção 15. Para detalhes dos V5 features → Seção 17. Para gap analysis → Seções 7-8. Para roadmap de ajustes no protótipo → Seção 16. Para guia de transferência → Seção 19.

---

## 19. Guia de Transferência Tecnológica para o Time de Produção

### 19.1. Objetivo e Como Usar Este Guia

Este guia consolida tudo que o time de produção precisa para absorver o protótipo Replit de forma eficiente. Em vez de duplicar conteúdo já detalhado em seções anteriores, ele funciona como **mapa de navegação** — indicando o quê ler, em que ordem, e o que fazer com cada artefato.

**Ordem de leitura sugerida:**
1. Comece por esta seção (19) para ter a visão geral
2. Siga o checklist do primeiro sprint (19.3)
3. Consulte a tabela de equivalências (19.4) durante a implementação
4. Use as referências cruzadas (19.7) para mergulhar nos detalhes de cada camada

### 19.2. Visão Geral da Arquitetura Atual

Estrutura de diretórios do `app/` com anotações para orientação:

```
app/
├── domains/          ← 9 domínios auto-contidos (ver Seção 15.2-15.4)
│   ├── base.py       ← DomainPrompt ABC — PRIMEIRO ARQUIVO A LER
│   ├── registry.py   ← Auto-registro via @register_domain
│   ├── workflow.py   ← Pipeline: intent→execute→format
│   ├── job_management/   ← 20 actions, 5 services, 6 agents
│   ├── sourcing/         ← 18 actions, 8 services, 1 agent
│   ├── cv_screening/     ← 15 actions, 3 services, 2 agents (WSI)
│   ├── communication/    ← 22 actions, 12 services
│   ├── analytics/        ← 18 actions, 3 services
│   ├── interview_scheduling/ ← 12 actions, 3 services
│   ├── automation/       ← 8 actions, 3 services
│   ├── ats_integration/  ← 10 actions, 4 services
│   └── recruiter_assistant/ ← 15 actions, 2 services
├── orchestrator/     ← Roteamento (ver Seção 20.3)
│   ├── cascaded_router.py  ← Memory→Fast→LLM (3 tiers)
│   ├── fast_router.py      ← ~80% das queries resolvidas aqui
│   └── orchestrator.py     ← Entry point
├── shared/           ← Infraestrutura transversal
│   ├── memory/       ← V5: ConversationState + ReferenceResolver
│   ├── intelligence/ ← V5: SmartExtractor + ParamPatterns
│   ├── execution/    ← V5: ExecutionPlan + PlanDetector
│   ├── resilience/   ← V5: StatsManager + CircuitBreaker
│   ├── async_processing/ ← V5: TaskQueue + TaskManager
│   ├── providers/    ← LLM ABC + Factory, ATS Factory, Voice ABC
│   ├── repositories/ ← Repository Pattern (4 models)
│   ├── mixins/       ← SerializableMixin
│   ├── compliance/   ← FairnessGuard, FactChecker, Audit
│   ├── governance/   ← FeatureFlags, AgentMonitoring
│   └── learning/     ← LearningLoop, TemplateLearning
├── prompts/          ← 12 YAML files (3,200L, language-agnostic)
├── models/           ← SQLAlchemy models → spec para ActiveRecord
├── schemas/          ← Pydantic schemas → spec para API contracts
└── api/v1/           ← FastAPI endpoints → spec para Rails controllers
```

### 19.3. Checklist do Primeiro Sprint

Lista ordenada de ações para o primeiro sprint da equipe de produção:

- [ ] 1. **Ler `domains/base.py`** — entender `DomainPrompt`, `DomainAction`, `DomainContext`, `DomainResponse`
- [ ] 2. **Ler `domains/registry.py`** — entender como domínios se registram via `@register_domain`
- [ ] 3. **Copiar pasta `app/prompts/` inteira** — YAML files carregam em qualquer linguagem (ver Seção 15.8.1 Fase 1)
- [ ] 4. **Copiar `app/shared/providers/llm_provider.py`** — usar como spec da interface LLM (ver Seção 15.8.1 Fase 2)
- [ ] 5. **Copiar serviços WSI** (`wsi_service.py`, `lia_score_service.py`, etc.) — IP mais valioso (ver Seção 15.4.2)
- [ ] 6. **Copiar `app/shared/intelligence/param_patterns.py`** — 29 regex PT-BR, zero dependência
- [ ] 7. **Copiar `app/shared/memory/`** — `ConversationState` + `ReferenceResolver`, stdlib puro
- [ ] 8. **Configurar CascadedRouter equivalente** com keywords dos 9 domínios (ver Seção 20.3)

> **Referência**: Para roadmaps detalhados de adoção, ver Seções 17.8 (V5) e 18.5 (todas as camadas).

### 19.4. Mapeamento de Equivalências Python → Rails

| Conceito Protótipo | Arquivo Python | Equivalente Rails | Notas |
|---|---|---|---|
| DomainPrompt ABC | `domains/base.py` | Module/Concern com interface | Definir `process_intent`, `execute_action` |
| @register_domain | `domains/registry.py` | `Rails.application.config.domains` ou initializer | Auto-discovery via convention |
| DomainWorkflow | `domains/workflow.py` | Service Object com pipeline | `analyze_intent → execute → format` |
| CascadedRouter | `orchestrator/cascaded_router.py` | Middleware/Service | 3 tiers: cache → regex → LLM |
| PromptLoader | `app/prompts/__init__.py` | `YAML.load_file` | Carregar YAML direto |
| LLMProviderABC | `shared/providers/llm_provider.py` | Module com interface | `generate`, `generate_stream` |
| LLMProviderFactory | `shared/providers/llm_factory.py` | Factory class | `LlmProviderFactory.create(:claude)` |
| BaseRepository | `shared/repositories/base.py` | ApplicationRecord | ActiveRecord JÁ é o repository |
| SQLAlchemy queries | Route service facades | ActiveRecord scopes/queries | Traduzir select/where/join |
| SerializableMixin | `shared/mixins/serializable.py` | ActiveModel::Serializers | `as_json` / `from_json` |
| Pydantic schemas | `schemas/*.py` | Strong Parameters + ActiveModel | Validação de input |
| FastAPI endpoints | `api/v1/*.py` | Rails controllers | Spec de comportamento |
| ConversationState | `shared/memory/` | Redis-backed model | Serializar para Redis |
| SmartExtractor | `shared/intelligence/` | Service Object | Copiar regex direto |

### 19.5. Tabela de Decisão Consolidada: O Que Fazer Com Cada Camada

Para decisão detalhada por camada, ver Seção 18.3. Abaixo a versão atualizada incluindo as camadas de portabilidade:

| Camada | Ação | Prioridade | Seção de Referência |
|--------|------|:----------:|:-------------------:|
| Prompts YAML | **Copiar direto** — language-agnostic | 🔴 Alta | 15.8.1 Fase 1 |
| WSI Assessment (~11.000L) | **Copiar direto** — IP proprietário | 🔴 Alta | 15.4.2 |
| Agentes Python (~33.800L) | **Copiar + adaptar interface** | 🔴 Alta | 15.2 |
| Services de negócio (~115.600L) | **Copiar + adaptar DI** | 🔴 Alta | 15.4 |
| V5 Features (~2.162L) | **Copiar conforme roadmap** | 🟠 Média | 17.8 |
| LLM Provider ABC | **Usar como spec → reimplementar com gems** | 🟠 Média | 15.8.1 Fase 2 |
| Repository Pattern | **Usar ABC como spec para scopes** | 🟠 Média | 15.8.1 Fase 3 |
| Route Service Facades | **Usar como behavior spec** | 🟠 Média | 15.8.1 Fase 4 |
| SerializableMixin | **Traduzir para concern** | 🟡 Baixa | 15.8.1 Fase 5 |
| Tools (~10.000L) | **Copiar + redistribuir por domínio** | 🟠 Média | 15.3 |
| Orchestrator (~2.200L) | **Copiar CascadedRouter + FastRouter** | 🟠 Média | 20.3 |
| Models Pydantic | **Traduzir para ActiveRecord** | 🟠 Média | 15.6 |
| Endpoints FastAPI | **Usar como spec → reimplementar** | 🟡 Baixa | 15.7 |
| Frontend React | **Referência de UX via Storybook** | 🟡 Baixa | 18.4 |

### 19.6. Métricas Atualizadas (Pós-Portabilidade)

Resumo das métricas após a fase de portabilidade (ver Seção 15.8 para tabela completa):

| Métrica | Valor |
|---------|:-----:|
| Total de código | ~347.100L |
| 🟢 Aproveitável direto | ~153.650L (44%) |
| 🟢+🟡 Baixo esforço | ~226.900L (65%) |
| Testes validando | 109 regressão + V5 |

### 19.7. Referências Cruzadas

| Precisa de... | Consultar |
|---|---|
| Detalhes por arquivo | Seção 15 |
| Fases de portabilidade | Seção 15.8.1 |
| Features V5 detalhadas | Seção 17 |
| Visão consolidada por camada | Seção 18 |
| Inventário completo de código | Seção 20 |
| Contratos dos 9 domínios | Seção 15.9 |
| Gap analysis vs produção | Seções 7-8 |
| Plano de migração incremental | Seção 14.6 |

---

## 20. Inventário Detalhado de Código por Camada

> **Origem**: Conteúdo consolidado do Blueprint Técnico V5. Lista **todos os arquivos de código** que compõem a arquitetura V5, organizados pela função que exercem. Para cada arquivo: caminho no repositório, tamanho aproximado em linhas, e função no sistema.

---

### 20.1. Fundação: Contratos e Abstrações

Estes são os arquivos que definem **o que é um domínio**, quais dados ele recebe e o que ele retorna. Todo o resto do sistema implementa estes contratos.

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `app/domains/base.py` | 171 | **Contrato central da arquitetura.** Define as classes abstratas e dataclasses que todo domínio implementa: `DomainPrompt` (ABC), `DomainAction`, `DomainContext`, `IntentResult`, `DomainResponse`, `ConfidenceLevel`. |

#### Classes definidas em `base.py`:

| Classe | Tipo | O que define |
|--------|------|-------------|
| `DomainAction` | dataclass | Uma ação que o domínio pode executar (id, nome, descrição, parâmetros obrigatórios/opcionais, tags) |
| `DomainContext` | dataclass | Contexto passado a cada operação (user_id, tenant_id, session_id, conversation_memory, filtros, IDs selecionados) |
| `IntentResult` | dataclass | Resultado da análise de intenção (action_id mapeado, confiança, parâmetros extraídos, raciocínio) |
| `DomainResponse` | dataclass | Resposta padronizada (success/error/clarification/confirmation, dados, sugestões, metadata) |
| `DomainPrompt` | ABC | Contrato que todo domínio implementa: `get_allowed_actions()`, `get_system_prompt()`, `process_intent()`, `execute_action()` |

**Este arquivo é o primeiro que o time deve ler. Tudo depende dele.**

---

### 20.2. Registry e Auto-Discovery

Como os domínios são descobertos e instanciados automaticamente.

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `app/domains/registry.py` | 118 | **Registro central de domínios.** O decorator `@register_domain` registra automaticamente qualquer classe que herda `DomainPrompt`. O `DomainRegistry` (singleton) gerencia instâncias, listagem e busca por action_id. |

#### Mecanismo:
```python
@register_domain
class SourcingDomain(DomainPrompt):
    domain_id = "sourcing"
    # ... implementação
```

O `DomainRegistry` permite:
- `get_instance(domain_id)` → instância lazy do domínio
- `list_domains()` → lista de IDs registrados
- `get_all_actions()` → todas as actions de todos os domínios
- `get_domain_for_action(action_id)` → qual domínio trata uma action

**Depende de**: `app/domains/base.py`

---

### 20.3. Orquestração: Roteamento e Pipeline

Estes arquivos definem **como uma mensagem do recrutador chega ao domínio correto** e como é processada.

#### 20.3.1 Roteamento (qual domínio?)

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `app/orchestrator/cascaded_router.py` | 187 | **Roteador em 3 camadas**: (1) cache em memória (O(1) hash lookup), (2) FastRouter (regex/keyword), (3) fallback LLM. Tenta o mais barato primeiro. |
| `app/orchestrator/fast_router.py` | 241 | **Roteador rápido por keywords/regex.** Mapeia padrões de texto a domínios sem LLM. Cobre ~80% dos casos. |
| `app/orchestrator/intent_router.py` | 384 | **Roteador LLM (fallback).** Usa Claude/Gemini para classificar intenção quando keyword matching falha. Mais caro, mais preciso. |

#### 20.3.2 Pipeline de Processamento (como processa?)

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `app/domains/workflow.py` | 447 | **Pipeline de 3 nós**: `analyze_intent` → `execute` → `format`. Processa a mensagem dentro do domínio correto. Integra com V5 features (SmartExtractor, ReferenceResolver). Define `WorkflowState` e `WorkflowStep`. |
| `app/orchestrator/orchestrator.py` | 461 | **Orquestrador principal.** Coordena CascadedRouter + DomainWorkflow. Entry point para processar qualquer mensagem. |
| `app/orchestrator/state_manager.py` | 306 | **Gerenciador de estado de sessão.** Mantém estado da conversa entre mensagens (domínio ativo, ações recentes, contexto). |
| `app/orchestrator/policy_engine.py` | 147 | **Motor de políticas.** Valida se uma ação pode ser executada (permissões, limites, compliance). |
| `app/orchestrator/task_planner.py` | 235 | **Planejador de tarefas.** Decompõe intenções complexas em sub-tarefas quando necessário. |

#### Fluxo completo:

```
Mensagem do recrutador
    ↓
CascadedRouter.route(message)
    ├─ Tier 1: Memory cache (hash) → hit? → domain_id
    ├─ Tier 2: FastRouter (regex/keyword) → match? → domain_id  
    └─ Tier 3: IntentRouter (LLM) → classify → domain_id
    ↓
DomainRegistry.get_instance(domain_id) → DomainPrompt instance
    ↓
DomainWorkflow.run(query, domain, context)
    ├─ Step 1: resolve_references (V5: ReferenceResolver)
    ├─ Step 2: smart_extract (V5: SmartExtractor)
    ├─ Step 3: analyze_intent → IntentResult
    ├─ Step 4: execute → DomainResponse
    └─ Step 5: format → DomainResponse final
    ↓
Resposta ao recrutador
```

**Depende de**: `base.py`, `registry.py`, features V5

---

### 20.4. Os 9 Domínios (código por domínio)

Cada domínio é um diretório com estrutura padronizada:

```
app/domains/<nome>/
├── domain.py      # Implementação de DomainPrompt (contrato)
├── actions.py     # Lista de DomainAction (o que o domínio pode fazer)
├── agents/        # Agente(s) especializado(s) com lógica LLM
├── services/      # Serviços de negócio (sem LLM, lógica pura)
├── tools/         # Funções que a LIA pode chamar (tool calling)
├── models/        # Modelos de dados SQLAlchemy
├── schemas/       # Schemas Pydantic para validação
└── prompts/       # Prompts específicos do domínio (quando existem)
```

#### 20.4.1 Sourcing (30 actions)

**O que faz**: Busca de candidatos em múltiplas fontes (boolean search, Pearch AI, PG Vector, WRF).

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `domain.py` | ~200 | Implementa DomainPrompt. Keyword→action mapping para 30 actions de busca. |
| `actions.py` | ~80 | Lista das 30 DomainAction: search, boolean, semantic, parse_cv, match, rank, compare, talent_pool, etc. |
| `agents/sourcing_agent.py` | 1.881 | **Agente de sourcing.** Lógica LLM para interpretar queries de busca, gerar boolean strings, sugerir estratégias. |
| `agents/engagement_nodes.py` | 1.354 | Nós de processamento para pipeline de engajamento de candidatos. |
| `prompts.py` | ~150 | Prompts específicos de sourcing (busca, análise de mercado). |
| `tools.py` | ~200 | Tools callable pela LIA: buscar candidatos, gerar boolean, etc. |
| `services/sourcing_pipeline.py` | 1.102 | Pipeline automatizado de sourcing multi-fonte. |
| `services/pearch_service.py` | ~400 | Cliente Pearch AI para busca externa. |
| `services/wrf_service.py` | ~300 | Weighted Rank Fusion — combina resultados de múltiplas fontes. |
| `services/vacancy_search.py` | ~350 | Busca de vagas/candidatos por critérios. |
| `services/es_analyzer.py` | ~200 | Análise Elasticsearch. |
| `services/pgv_analyzer.py` | ~200 | Análise PG Vector (embeddings). |
| `services/pre_wrf_filter.py` | ~150 | Filtro pré-WRF para otimização. |
| `services/search_analytics.py` | ~250 | Analytics de busca (efetividade, métricas). |
| `services/evaluation_criteria.py` | ~150 | Critérios de avaliação de candidatos. |
| `services/apify_service.py` | ~200 | Integração Apify para web scraping. |
| `services/apify_mcp_client.py` | ~150 | Cliente MCP para Apify. |

#### 20.4.2 Job Management (28 actions)

**O que faz**: Criação, edição, publicação de vagas. Job Wizard conversacional, templates, JD enrichment.

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `domain.py` | ~200 | Implementa DomainPrompt para 28 actions de gestão de vagas. |
| `actions.py` | ~80 | Lista de actions: create_job, edit_job, publish, generate_jd, clone, intake, etc. |
| `agents/job_intake_agent.py` | 4.132 | **Agente de intake.** Coleta dados de vaga via conversa, infere campos, valida. O maior agente do sistema. |
| `agents/job_vacancy_nodes.py` | 1.543 | Nós de processamento para fluxo de vaga. |
| `agents/job_drafting_agent.py` | 1.420 | Agente de rascunho de JD (geração e refinamento). |
| `agents/job_lifecycle_agent.py` | 1.071 | Agente de ciclo de vida (publicação, freeze, encerramento). |
| `prompts/` | ~500 | Prompts de job management (intake, JD, templates). |
| `tools/job_wizard_tools.py` | 1.160 | Tools do Job Wizard: step management, field extraction, validation. |
| `tools/job_tools.py` | ~500 | Tools gerais de vaga: CRUD, status, publicação. |
| `services/seniority_jd_analyzer.py` | ~600 | Analisador de senioridade em JDs (multi-signal resolution). |
| `services/wizard_orchestrator_service.py` | ~800 | Orquestrador do Job Wizard (6 nós LLM). |
| `services/job_vacancy_service.py` | ~700 | CRUD de vagas com validação e business logic. |
| `services/job_template_service.py` | ~500 | Serviço de templates de vaga (361 curados). |
| `services/template_seeder.py` | 1.691 | Seeder que carrega templates curados no banco. |
| `services/template_learning_service.py` | ~400 | Aprendizado a partir de templates e JDs importadas. |
| `services/job_insights_service.py` | ~400 | Insights inteligentes sobre vagas (mercado, competitividade). |
| `services/vacancy_search_service.py` | ~350 | Busca avançada de vagas. |
| `services/job_embedding_service.py` | ~300 | Geração de embeddings para vagas. |
| `services/job_qualification_service.py` | ~250 | Avaliação de qualificação de candidatos vs vaga. |
| `services/wizard_data_priority_service.py` | ~300 | Priorização de dados no wizard (company config > LIA history > templates). |
| `services/job_clone_service.py` | ~200 | Clonagem de vagas. |
| `services/job_context_service.py` | ~200 | Contexto de vaga para LLM. |
| `services/job_pattern_service.py` | ~200 | Detecção de padrões em vagas. |
| `services/recruitment_email_templates.py` | ~300 | Templates de email de recrutamento. |

#### 20.4.3 CV Screening + WSI (25 actions)

**O que faz**: Triagem curricular com metodologia WSI (7 blocos), scoring, red flags, parecer.

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `domain.py` | ~200 | Implementa DomainPrompt para 25 actions de triagem. |
| `actions.py` | ~70 | Actions: screen, evaluate_wsi, score, red_flags, compare, parecer, etc. |
| `agents/avaliador_wsi_agent.py` | 1.596 | **Agente avaliador WSI.** Executa 7 blocos de avaliação com rubricas de 4 níveis. |
| `agents/triagem_curricular_agent.py` | 1.384 | Agente de triagem curricular (análise inicial, categorização). |
| `prompts/` | ~400 | Prompts WSI: avaliação por bloco, calibração por senioridade. |
| `tools/candidate_tools.py` | 1.116 | Tools de candidato: scoring, comparação, perfil, red flags. |
| `services/wsi_service.py` | 1.295 | **Core WSI.** Implementação dos 7 blocos, cálculo de scores, thresholds. |
| `services/rubric_evaluation_service.py` | 1.263 | Avaliação por rubrica de 4 níveis (Insuficiente/Básico/Proficiente/Avançado). |
| `models/` | ~400 | Modelos: WSI scores, candidato, avaliação. |
| `schemas/` | ~200 | Schemas de validação para WSI. |

#### 20.4.4 Communication (20 actions)

**O que faz**: Comunicação multi-canal (email, WhatsApp, SMS, Teams), templates, human-in-the-loop.

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `domain.py` | ~180 | Implementa DomainPrompt para 20 actions de comunicação. |
| `actions.py` | ~60 | Actions: send_email, send_whatsapp, schedule_message, template, approve, etc. |
| `agents/communication_agent.py` | ~800 | Agente de comunicação (composição, tom, personalização). |
| `services/communication_service.py` | 2.445 | **Core de comunicação.** Orquestra canais, templates, filas, aprovação. |
| `services/email_service.py` | 2.864 | Serviço de email (Mailgun, Resend, templates, tracking). |
| `services/communication_dispatcher.py` | ~400 | Dispatcher multi-canal (decide canal, aplica regras). |
| `services/communication_history_service.py` | ~300 | Histórico de comunicações. |
| `services/email_providers/` | ~400 | Providers de email (base, Resend). |
| `services/teams_webhook_service.py` | ~400 | Webhooks Microsoft Teams. |
| `services/whatsapp_service.py` | ~300 | Integração WhatsApp. |
| `models/` | ~600 | Modelos: templates, histórico, filas, webhook, configurações. |

#### 20.4.5 Interview & Scheduling (20 actions)

**O que faz**: Agendamento de entrevistas, integração calendário (Microsoft Graph), feedback.

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `domain.py` | ~180 | Implementa DomainPrompt para 20 actions de entrevista. |
| `actions.py` | ~60 | Actions: schedule, reschedule, cancel, feedback, availability, remind, etc. |
| `agents/scheduling_agent.py` | 1.512 | Agente de agendamento (negociação de horário, conflitos). |
| `agents/entrevistador_agent.py` | 1.117 | Agente entrevistador (guia de entrevista, perguntas adaptativas). |
| `services/` | ~1.500 | Serviços de calendário, disponibilidade, lembretes. |
| `models/` | ~300 | Modelos de entrevista, agenda, feedback. |

#### 20.4.6 Analytics & Reporting (18 actions)

**O que faz**: KPIs, dashboards, relatórios, analytics preditivo, monitoramento de agentes.

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `domain.py` | ~180 | Implementa DomainPrompt para 18 actions de analytics. |
| `actions.py` | ~55 | Actions: dashboard, kpi, report, predict, monitor, query, etc. |
| `agents/analytics_agent.py` | ~800 | Agente de analytics (interpreta queries de dados). |
| `agents/analista_feedback_agent.py` | 2.068 | Agente analista de feedback (análise qualitativa). |
| `tools/query_tools.py` | 4.786 | **O maior arquivo de tools.** 33 query tools para consultas de dados. |
| `services/predictive_analytics_service.py` | ~600 | Analytics preditivo (ML features, outcome prediction). |
| `services/search_analytics_service.py` | ~400 | Analytics de busca. |
| `services/report_service.py` | ~350 | Geração de relatórios. |
| `services/agent_monitoring_service.py` | ~350 | Monitoramento de performance dos agentes. |
| `models/observability.py` | 2.164 | Modelo de observabilidade (métricas, traces, logs). |

#### 20.4.7 ATS Integration (18 actions)

**O que faz**: Integração com ATSs (Gupy, Pandapé, Merge/StackOne), sync bidirecional.

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `domain.py` | ~180 | Implementa DomainPrompt para 18 actions de integração ATS. |
| `actions.py` | ~55 | Actions: sync, import, export, map_fields, webhook, status, etc. |
| `agents/integrador_ats_agent.py` | ~800 | Agente integrador (mapeia campos entre sistemas). |
| `services/ats_clients/base.py` | ~200 | Classe base para clientes ATS. |
| `services/ats_clients/gupy.py` | ~400 | Cliente Gupy API. |
| `services/ats_clients/pandape.py` | ~300 | Cliente Pandapé API. |
| `services/ats_clients/merge.py` | ~300 | Cliente Merge API. |
| `services/ats_clients/stackone.py` | ~200 | Cliente StackOne API. |
| `services/ats_sync_service.py` | ~500 | Serviço de sincronização bidirecional. |

#### 20.4.8 Automation & Tasks (20 actions)

**O que faz**: Automação de estágios, tarefas planejadas, alertas proativos, agentes autônomos.

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `domain.py` | ~180 | Implementa DomainPrompt para 20 actions de automação. |
| `actions.py` | ~60 | Actions: automate_stage, plan_task, alert, schedule, trigger, etc. |
| `agents/task_planner_agent.py` | ~800 | Agente planejador de tarefas (decomposição, priorização). |
| `services/automation_service.py` | 1.234 | Core de automação (regras, triggers, execução). |
| `services/stage_automation_engine.py` | ~600 | Motor de automação de estágios (state machine de recrutamento). |
| `services/stage_transition_automation.py` | ~400 | Transições inteligentes de estágio (LIA-driven). |
| `services/autonomous_agent_service.py` | ~400 | Serviço de agentes autônomos (background jobs). |
| `services/proactive_alert_service.py` | ~350 | Alertas proativos baseados em eventos. |
| `services/proactive_service.py` | ~300 | Sugestões proativas da LIA. |
| `services/planned_task_service.py` | ~300 | Gerenciamento de tarefas planejadas. |
| `services/automation_trigger_service.py` | ~250 | Serviço de triggers de automação. |
| `services/automation_handlers.py` | ~200 | Handlers de automação por tipo de evento. |
| `services/automation_scheduler.py` | ~200 | Scheduler de automações (cron-like). |
| `models/` | ~500 | Modelos: automação, tarefas, estágios de recrutamento. |

#### 20.4.9 Recruiter Assistant (20 actions)

**O que faz**: Assistente do recrutador, pipeline Kanban, memória conversacional.

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `domain.py` | ~180 | Implementa DomainPrompt para 20 actions de assistência. |
| `actions.py` | ~60 | Actions: assist, pipeline_view, kanban_move, remember, suggest, etc. |
| `agents/recruiter_assistant_agent.py` | 2.551 | **Agente assistente.** O segundo maior agente — coordena funcionalidades cross-domain. |
| `services/conversation_manager.py` | 1.273 | Gerenciador de conversa (histórico, contexto, resumos LLM). |
| `services/conversation_memory.py` | ~400 | Memória persistente de conversa. |
| `services/pipeline_service.py` | ~500 | Serviço de pipeline de recrutamento. |
| `services/pipeline_stage_service.py` | ~300 | Gestão de estágios do pipeline. |
| `services/kanban_assistant_service.py` | ~400 | Assistente Kanban (movimentação, sub-status, WSI). |
| `services/memory_service.py` | ~300 | Serviço de memória (persistência de contexto). |

---

### 20.5. Features V5: Módulos Compartilhados

Módulos que servem a **todos** os domínios. São as features de convergência V5.

#### 20.5.1 ConversationMemory + Resolução de Referências

| Arquivo | Linhas | Função | Depende de |
|---------|--------|--------|-----------|
| `app/shared/memory/conversation_state.py` | 146 | Estado conversacional: últimos candidatos exibidos, filtros ativos, ações recentes. Usado pelo DomainWorkflow para resolver "dele", "o primeiro". | Nada (standalone) |
| `app/shared/memory/reference_resolver.py` | 315 | Resolve referências anafóricas ("dele", "o primeiro", "o anterior") para IDs concretos usando o ConversationState. | `conversation_state.py` |

#### 20.5.2 SmartExtractor (2-Stage Param Extraction)

| Arquivo | Linhas | Função | Depende de |
|---------|--------|--------|-----------|
| `app/shared/intelligence/smart_extractor.py` | 213 | Extração de parâmetros em 2 estágios: regex primeiro, LLM só se necessário. Reduz custos ~70%. | `param_patterns.py` |
| `app/shared/intelligence/param_patterns.py` | 240 | 50+ patterns regex para: datas, salários, emails, senioridade, localização, percentuais, CNPJs, telefones. | Nada (standalone) |

#### 20.5.3 StatsManager (Thread-Safe Cache)

| Arquivo | Linhas | Função | Depende de |
|---------|--------|--------|-----------|
| `app/shared/resilience/stats_manager.py` | 217 | Cache em memória com TTL, LRU eviction, compute-on-miss, namespaces multi-tenant. Thread-safe. | Nada (standalone, usa `threading` stdlib) |

#### 20.5.4 ExecutionPlan (Multi-Step Cross-Domain)

| Arquivo | Linhas | Função | Depende de |
|---------|--------|--------|-----------|
| `app/shared/execution/execution_plan.py` | 149 | Dataclasses de plano de execução: `ExecutionStep`, `ExecutionPlan`, `ExecutionResult`. | Nada (standalone) |
| `app/shared/execution/plan_detector.py` | 234 | Detecta quando uma mensagem requer múltiplas ações cross-domain. | `execution_plan.py` |
| `app/shared/execution/plan_executor.py` | 231 | Executa plano em ordem topológica, resolve dependências entre steps, agrega resultados. | `execution_plan.py`, `registry.py` |

#### 20.5.5 Processamento Assíncrono (Domain Task Queues)

| Arquivo | Linhas | Função | Depende de |
|---------|--------|--------|-----------|
| `app/shared/async_processing/task_queue.py` | 214 | Fila de tarefas com prioridade, timeout e retry. Uma fila por domínio. | Nada (usa `asyncio` stdlib) |
| `app/shared/async_processing/task_manager.py` | 203 | Manager que cria/gerencia filas por domínio, workers assíncronos, graceful shutdown. | `task_queue.py` |

---

### 20.6. Agentes: State Machine e Nós de Processamento

Definem **como** os agentes pensam e processam informação.

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `app/shared/agents/state_machine.py` | 467 | **State machine dos agentes.** Define estados, transições, condições. Base para todos os agentes. |
| `app/shared/agents/conversation.py` | 1.657 | **Motor de conversa.** Gerencia turnos, histórico, contexto de conversa, integração LLM. |
| `app/shared/agents/nodes.py` | 1.292 | **Nós de processamento genéricos.** Intent classification, response generation, validation, formatting. |
| `app/shared/agents/sourcing_engagement_nodes.py` | 1.354 | Nós especializados para pipeline de engajamento de sourcing. |
| `app/agents/base_agent.py` | 398 | **Classe base de agente** (legado, mantida para compatibilidade). Define interface que agentes especializados implementam. |
| `app/agents/agent_registry.py` | 57 | Registry legado de agentes (shim → DomainRegistry). |

---

### 20.7. Prompts: O que define o comportamento da LIA

**Estes são os arquivos mais importantes para o comportamento da LIA.** Mudam os prompts = muda o comportamento.

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `app/shared/prompts/agent_prompts.py` | 1.567 | **Prompts de sistema para todos os agentes.** System prompts, instruções, personalidade, tom de voz, limites. O arquivo mais crítico para comportamento. |
| `app/shared/prompts/prompt_registry.py` | 496 | **Registry de prompts com versionamento.** Gerencia versões de prompts, A/B testing, rollback. |
| `app/shared/prompts/examples/sourcing_examples.py` | 528 | Few-shot examples para agente de sourcing. |
| `app/shared/prompts/examples/pipeline_examples.py` | 676 | Few-shot examples para pipeline. |
| `app/shared/prompts/examples/job_planner_examples.py` | 429 | Few-shot examples para job planning. |
| `app/shared/prompts/examples/orchestrator_examples.py` | 192 | Few-shot examples para orquestrador. |
| `app/domains/sourcing/prompts.py` | ~150 | Prompts específicos de sourcing. |
| `app/domains/cv_screening/prompts/` | ~400 | Prompts WSI (avaliação por bloco, calibração). |
| `app/domains/job_management/prompts/` | ~500 | Prompts de job management (intake, JD, wizard). |

---

### 20.8. Robustez e Compliance

Camada de proteção que envolve todos os domínios.

#### 20.8.1 Robustez (input → output filtering)

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `app/shared/robustness/input_validation.py` | 288 | Validação de input: sanitização, limites, detecção de injection. |
| `app/shared/robustness/response_filter.py` | 364 | Filtro de output: tom profissional, remoção de conteúdo inadequado. |
| `app/shared/robustness/error_handling.py` | 269 | Tratamento padronizado de erros: logging, retry, fallback messages. |
| `app/shared/robustness/context_management.py` | 298 | Gestão de contexto: compressão, limites de tokens, priorização. |
| `app/shared/robustness/defensive_prompts.py` | 265 | Prompts defensivos: guardrails contra alucinação, fora de escopo. |
| `app/shared/robustness/intent_schemas.py` | 485 | Schemas de intenção: estrutura esperada de cada tipo de intent. |
| `app/shared/robustness/enhanced_base.py` | 300 | Base melhorada para agentes com robustez integrada. |
| `app/shared/robustness/enhanced_registry.py` | 320 | Registry melhorado com validação automática. |

#### 20.8.2 Compliance (3 pilares: LGPD + SOX + EU AI Act)

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `app/shared/compliance/fairness_guard.py` | 195 | **FairnessGuard.** Detecta e bloqueia viés em decisões de IA (gênero, raça, idade, etc.). |
| `app/shared/compliance/fact_checker.py` | 251 | **FactChecker.** Verifica afirmações factuais da LIA contra dados reais. |
| `app/shared/compliance/audit_service.py` | 401 | Serviço de auditoria: log de decisões, rastreabilidade, relatórios. |

#### 20.8.3 Governança

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `app/shared/governance/feature_flag_service.py` | 315 | Feature flags: controle granular de funcionalidades por tenant. |
| `app/shared/governance/agent_monitoring_service.py` | 580 | Monitoramento de agentes: latência, custo, qualidade, erros. |

---

### 20.9. Tools: Ações executáveis pela LIA

O sistema de tool calling permite que a LIA execute ações reais (não só responder texto).

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `app/tools/registry.py` | 145 | **Registry central de tools.** Registra, descobre e mapeia tools. |
| `app/tools/executor.py` | 335 | **Executor de tools.** Executa tools com validação, logging, tenant scoping. |
| `app/tools/scope_config.py` | 335 | **Configuração de escopo.** Define quais tools estão disponíveis por domínio/tenant. |

Tools por domínio (já listadas em cada domínio acima):
- `sourcing/tools.py` — busca, boolean, match
- `job_management/tools/job_wizard_tools.py` — wizard, steps, fields
- `job_management/tools/job_tools.py` — CRUD de vagas
- `cv_screening/tools/candidate_tools.py` — scoring, comparação
- `analytics/tools/query_tools.py` — 33 query tools (o maior)

---

### 20.10. Modelos de Dados

Modelos SQLAlchemy que definem o schema do banco.

**Diretório principal**: `app/models/` (23.887 linhas em ~50 arquivos)

| Arquivo | Linhas | O que modela |
|---------|--------|-------------|
| `ui_actions.py` | 2.941 | Ações de UI (botões, modais, navegação) |
| `observability.py` | 2.164 | Métricas, traces, logs de agentes |
| `communication_matrix.py` | 767 | Regras de comunicação por estágio/canal |
| `candidate.py` | 604 | Modelo de candidato |
| `recruitment_stages.py` | 593 | Estágios de recrutamento |
| `policy.py` | 574 | Políticas de tenant |
| `company.py` | 516 | Modelo de empresa/tenant |
| `data_request.py` | 507 | Requisições de dados (LGPD) |
| `pearch.py` | 489 | Resultados Pearch |
| `health_check.py` | 434 | Health checks |
| `recruitment_journey.py` | 428 | Jornada de recrutamento |
| `admin_settings.py` | 372 | Configurações administrativas |
| `automation.py` | 349 | Regras de automação |
| `billing.py` | 334 | Billing/cobrança |
| `job_pattern.py` | 353 | Padrões detectados em vagas |
| ... | ... | (+ ~35 outros modelos) |

Modelos também existem **dentro** de cada domínio (em `app/domains/<nome>/models/`).

---

### 20.11. Serviços Compartilhados (`app/services/`)

189 arquivos de serviço que existem **fora** dos domínios. Muitos são shims que redirecionam para serviços dentro de domínios, mas os maiores contêm lógica própria.

#### Serviços com lógica própria (top 25 por tamanho):

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `organization_catalog_service.py` | 2.373 | Catálogo organizacional: estrutura de empresa, departamentos, cargos. |
| `seed_service.py` | 1.338 | Seeder de dados iniciais (templates, configurações, taxonomia). |
| `learning_hub_service.py` | 1.332 | Hub de aprendizado: consolidação de padrões, catálogo dinâmico. |
| `skills_catalog_service.py` | 1.314 | Catálogo de skills: taxonomia, classificação, sugestões. |
| `lia_score_service.py` | 1.303 | Cálculo do LIA Score (score unificado do candidato). |
| `notification_service.py` | 1.261 | Serviço de notificações (in-app, email, push). |
| `sourcing_pipeline_service.py` | 1.102 | Pipeline de sourcing (shim → `domains/sourcing/services/`). |
| `activity_service.py` | 999 | Registro de atividades (timeline de ações). |
| `candidate_comparison_service.py` | 958 | Comparação de candidatos lado a lado. |
| `intelligent_data_orchestrator.py` | 929 | Orquestração de dados para o wizard (prioriza fontes). |
| `policy_engine_service.py` | 912 | Motor de políticas por tenant (regras de negócio). |
| `lia_field_config_service.py` | 887 | Configuração de campos do wizard por tenant. |
| `multimodal_service.py` | 857 | Análise multimodal (vídeo, imagem, docs via Claude Vision). |
| `feedback_learning_service.py` | 850 | Aprendizado a partir de feedback do recrutador. |
| `llm.py` | 840 | **LLMService**: abstração unificada para Claude, Gemini, OpenAI. Retry, fallback, cost tracking. |
| `company_configuration_service.py` | 808 | Configurações da empresa (benefícios, cultura, políticas). |
| `compensation_analysis_service.py` | 785 | Análise de remuneração e benchmarks de mercado. |
| `company_scraper_service.py` | 773 | Scraping de dados de empresa (website, LinkedIn). |
| `microsoft_graph_service.py` | 764 | Integração Microsoft Graph (calendário, email, Teams). |
| `intelligence_layer_service.py` | 755 | Camada de inteligência: sugestões, inferência de campos, enriquecimento. |
| `responsibilities_catalog_service.py` | 745 | Catálogo de responsabilidades por cargo. |
| `hubspot_service.py` | 744 | Integração HubSpot CRM. |
| `openmic_service.py` | 720 | Integração OpenMic.ai (voice). |
| `market_benchmark_service.py` | 702 | Benchmarks de mercado (salários, benefícios, tempo de contratação). |
| `billing_service.py` | 654 | Serviço de billing (Stripe, créditos, consumo). |

**Total**: 189 arquivos, ~46.375 linhas

> **Nota para migração**: Muitos destes serviços devem ser absorvidos pelos domínios correspondentes. Os que têm shims de 1 linha já foram migrados.

---

### 20.12. Auth, Middleware, Schemas, Config, Templates, Prompts, Data, Constants, Jobs, Utils

#### 20.12.1 Autenticação (`app/auth/`)

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `dependencies.py` | 449 | Dependências FastAPI de autenticação: JWT validation, token extraction, permission checks. |
| `security.py` | 152 | Funções de segurança: hashing, token generation, validation. |
| `schemas.py` | 148 | Schemas Pydantic de auth (login request/response, token payload). |
| `workos_schemas.py` | 155 | Schemas para integração WorkOS (SSO, directory sync). |
| `workos_models.py` | 111 | Modelos WorkOS. |
| `models.py` | 59 | Modelo de usuário/sessão. |

#### 20.12.2 Middleware (`app/middleware/`)

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `rate_limiter.py` | 285 | Rate limiting por tenant/endpoint. |

#### 20.12.3 Schemas (`app/schemas/`)

~50 arquivos, 10.848 linhas de schemas Pydantic de validação para requests/responses da API.

Principais:
| Arquivo | Linhas | Função |
|---------|--------|--------|
| `company.py` | 721 | Schema de empresa (CRUD, configuração). |
| `observability.py` | 591 | Schema de observabilidade. |
| `sourcing_engagement_state.py` | 390 | Estado de engajamento de sourcing. |
| `job_vacancy_state.py` | 422 | Estado de vaga no wizard. |
| `saas_metrics.py` | 443 | Métricas SaaS. |
| `insurance.py` | 347 | Schema de seguros. |
| `continuity.py` | 340 | Schema de continuidade de negócio. |
| `job_description.py` | 318 | Schema de JD. |
| `candidate.py` | 297 | Schema de candidato. |
| `jd_enrichment.py` | 297 | Schema de enriquecimento de JD. |

#### 20.12.4 Prompts não-shared (`app/prompts/`)

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `kanban_assistant_prompts.py` | 777 | Prompts do assistente Kanban. |
| `job_wizard.py` | 411 | Prompts do Job Wizard. |
| `examples.py` | 387 | Few-shot examples genéricos. |
| `cot.py` | 305 | Chain-of-thought prompts. |
| `templates.py` | 245 | Templates de prompt reutilizáveis. |

#### 20.12.5 Config (`app/config/`)

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `industry_weights.py` | 133 | Pesos por indústria para scoring. |
| `langsmith.py` | 69 | Configuração LangSmith (tracing). |
| `cache_config.py` | 62 | Configuração de cache. |

#### 20.12.6 Templates de comunicação (`app/templates/`)

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `communication_templates.py` | 1.617 | Templates de email/WhatsApp/SMS para cada estágio. |
| `report_templates.py` | 687 | Templates de relatórios. |

#### 20.12.7 Dados curados (`app/data/`)

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `curated_templates_tech.py` | 5.122 | Templates curados — Tecnologia. |
| `curated_templates_vendas.py` | 4.083 | Templates curados — Vendas. |
| `curated_templates_operacoes.py` | 1.594 | Templates curados — Operações. |
| `curated_templates_rh.py` | 1.449 | Templates curados — RH. |
| `curated_templates_administrativo.py` | 928 | Templates curados — Administrativo. |
| `curated_templates_financas.py` | 903 | Templates curados — Finanças. |
| `curated_templates_customer_success.py` | 692 | Templates curados — Customer Success. |
| `curated_templates_saude.py` | 617 | Templates curados — Saúde. |
| `curated_templates_marketing.py` | 387 | Templates curados — Marketing. |
| `brazilian_job_templates.py` | 656 | Templates brasileiros genéricos. |

**Total**: 17.316 linhas — 361 templates de vagas curados por indústria.

#### 20.12.8 Constantes (`app/constants/`)

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `industries.py` | 815 | Lista de indústrias, subsetores e classificações. |

#### 20.12.9 Jobs (`app/jobs/`)

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `scheduled_reports.py` | 678 | Relatórios agendados (cron jobs). |

#### 20.12.10 Utils (`app/utils/`)

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `datetime_helpers.py` | 164 | Helpers de data/hora (timezone, formatação). |
| `skill_classifier.py` | 58 | Classificador simples de skills. |

---

### 20.13. Core: Database, Config, Taxonomia

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `app/core/database.py` | 1.231 | Setup de database: SQLAlchemy async, connection pool, migrations, init_db. |
| `app/core/config.py` | 108 | Configuração centralizada: settings do ambiente (Pydantic BaseSettings). |
| `app/core/taxonomy.py` | 770 | Taxonomia de skills, áreas, senioridades, localizações. Dados de referência do sistema. |
| `app/core/template_channels.py` | 46 | Definição de canais de comunicação (email, whatsapp, sms, teams). |

---

### 20.14. Entry Point e API Routes

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `app/main.py` | ~200 | **Entry point FastAPI.** Lifespan, middleware, registro de rotas, startup/shutdown. |
| `app/api/v1/` | ~120 arquivos | Endpoints REST da API v1. Cada arquivo = um domínio funcional da API. |
| `app/api/orchestrator_routes.py` | ~400 | Rotas do orquestrador: `/orchestrator/pipeline-chat`, `/orchestrator/talent-chat`. |
| `app/api/wsi_endpoints.py` | 1.518 | Endpoints WSI: screening pipeline, avaliação, calibração. |
| `app/api/public/` | ~400 | Endpoints públicos: portal de candidato, buscas compartilhadas. |

---

### 20.15. Shims de Compatibilidade

A migração V5 mantém shims em `app/agents/` que redirecionam para os domínios corretos. **Estes arquivos não contêm lógica** — são imports de 1 linha.

| Diretório | Arquivos | O que faz |
|-----------|----------|-----------|
| `app/agents/specialized/*.py` | 13 | Cada arquivo é `from app.domains.<domain>.agents.<agent> import *` — redireciona para o domínio. |
| `app/agents/prompts/*.py` | 5 | Redirecionam para `app/shared/prompts/`. |
| `app/agents/robustness/*.py` | 8 | Redirecionam para `app/shared/robustness/`. |
| `app/agents/nodes.py` etc | 5 | Redirecionam para `app/shared/agents/`. |

**Em produção**: estes shims podem ser removidos quando todo o código externo migrar para importar de `app/domains/` e `app/shared/` diretamente.

---

## 21. Diagrama de Dependências entre Camadas

```
┌──────────────────────────────────────────────────┐
│                   app/main.py                     │
│              (FastAPI entry point)                │
└──────────────────────┬───────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
┌─────────────┐ ┌────────────┐ ┌──────────┐
│ app/api/v1/ │ │orchestrator│ │ wsi_     │
│ (120 routes)│ │ _routes    │ │endpoints │
└──────┬──────┘ └─────┬──────┘ └────┬─────┘
       │              │              │
       └──────────────┼──────────────┘
                      ▼
       ┌──────────────────────────────┐
       │    app/orchestrator/          │
       │  ┌─────────────────────────┐ │
       │  │   CascadedRouter        │ │
       │  │   ├─ MemoryCache        │ │
       │  │   ├─ FastRouter         │ │
       │  │   └─ IntentRouter (LLM) │ │
       │  └──────────┬──────────────┘ │
       │             ▼                │
       │  ┌─────────────────────────┐ │
       │  │   Orchestrator          │ │
       │  │   + StateManager        │ │
       │  │   + PolicyEngine        │ │
       │  └──────────┬──────────────┘ │
       └─────────────┼────────────────┘
                     ▼
       ┌──────────────────────────────┐
       │    app/domains/               │
       │  ┌─────────────────────────┐ │
       │  │   DomainRegistry        │ │
       │  │   └─ DomainWorkflow     │ │
       │  └──────────┬──────────────┘ │
       │             ▼                │
       │  ┌─────────────────────────┐ │
       │  │   9 Domínios            │ │
       │  │   (domain.py + agents/  │ │
       │  │    services/ + tools/)  │ │
       │  └──────────┬──────────────┘ │
       └─────────────┼────────────────┘
                     ▼
       ┌──────────────────────────────┐
       │    app/shared/                │
       │  ┌──────────────────┐        │
       │  │ V5 Features      │        │
       │  │ ├─ memory/       │        │
       │  │ ├─ intelligence/ │        │
       │  │ ├─ resilience/   │        │
       │  │ ├─ execution/    │        │
       │  │ └─ async_proc/   │        │
       │  ├──────────────────┤        │
       │  │ Infra            │        │
       │  │ ├─ agents/       │        │
       │  │ ├─ prompts/      │        │
       │  │ ├─ robustness/   │        │
       │  │ ├─ compliance/   │        │
       │  │ └─ governance/   │        │
       │  └──────────────────┘        │
       └──────────────┬───────────────┘
                      ▼
       ┌──────────────────────────────┐
       │    app/domains/base.py        │
       │    (Contratos fundamentais)   │
       └──────────────────────────────┘
```

---

## 22. Cobertura de Testes Atualizada

### 22.1 Status Atual (166 testes passando)

| Suite | Arquivo | Testes | Status |
|-------|---------|--------|--------|
| **Agent Regression** | `tests/test_agent_regression.py` | 109 | 109/109 |
| **V5 Regression** | `tests/test_v5_regression.py` | 14 | 14/14 |
| **Seniority JD Analyzer** | `tests/test_seniority_jd_analyzer.py` | 30 | 30/30 |
| **Teams Webhook** | `tests/test_teams_webhook.py` | 20 | 13/20 (7 infra async) |

### 22.2 Testes V5 por Feature

| Feature | Arquivo de Teste | O que cobre |
|---------|-----------------|-------------|
| ConversationMemory | `tests/test_reference_resolver.py` | Resolução anafórica, edge cases, tipos de referência |
| SmartExtractor | `tests/test_smart_extractor.py` | Regex extraction, LLM fallback, cache, param patterns |
| StatsManager | `tests/test_stats_manager.py` | TTL, LRU, thread safety, invalidation, compute-on-miss |
| ExecutionPlan | `tests/test_execution_plan.py` | Detection, multi-step execution, dependency resolution, failure handling |
| Async Processing | `tests/test_async_processing.py` | Submit, status, completion, failure, priority, shutdown |
| Regressão Integrada | `tests/test_v5_regression.py` | 14 cenários cross-feature validando integração entre os 5 módulos |

### 22.3 Outros Testes Disponíveis

| Arquivo | O que cobre |
|---------|-------------|
| `tests/test_agents/test_avaliador_wsi_agent.py` | Agente avaliador WSI |
| `tests/test_agents/test_job_intake_agent.py` | Agente de intake de vagas |
| `tests/test_agents/test_triagem_curricular_agent.py` | Agente de triagem curricular |
| `tests/test_agents/test_sourcing_agent.py` | Agente de sourcing |
| `tests/test_agents/test_scheduling_agent.py` | Agente de agendamento |
| `tests/test_agents/test_task_planner_agent.py` | Agente de planejamento de tarefas |
| `tests/test_agents/test_entrevistador_agent.py` | Agente entrevistador |
| `tests/test_agents/test_analista_feedback_agent.py` | Agente de análise de feedback |
| `tests/test_agents/test_integrador_ats_agent.py` | Agente integrador ATS |
| `tests/test_agents/test_robustness.py` | Robustez dos agentes |
| `tests/test_feature_flags.py` | Feature flags service |
| `tests/test_agent_comprehensive.py` | Suite compreensiva de agentes |
| `tests/test_tone_filter.py` | Filtro de tom de resposta |
| `tests/test_context_compression.py` | Compressão de contexto |
| `tests/test_comparison_scenarios.py` | Cenários de comparação |
| `tests/test_seniority_resolver.py` | Resolução de senioridade |
| `tests/test_seniority_utils.py` | Utilitários de senioridade |
| `tests/test_domain_consolidation_e2e.py` | Consolidação de domínios E2E |
| `tests/e2e/test_wizard_job_creation.py` | Wizard de criação de vaga E2E |

---

## 23. Checklist de Portabilidade

### 23.1 Dependências de Runtime

| Componente | Dependência | Substituível por |
|------------|-------------|-----------------|
| LLM Calls | Anthropic Claude / Google Gemini / OpenAI | Qualquer LLM via adapter pattern |
| Database | PostgreSQL (Neon-backed) | Qualquer PostgreSQL |
| Search | Elasticsearch + PG Vector | Mantém interface, troca implementação |
| Cache | In-memory (StatsManager) | Redis (mesma interface) |
| Task Queue | In-process async (TaskManager) | Celery/RQ/SQS (mesma interface) |
| Webhooks | Teams (Microsoft Graph) | Qualquer webhook endpoint |

### 23.2 Variáveis de Ambiente Necessárias

| Variável | Usado por | Obrigatória |
|----------|-----------|-------------|
| `ANTHROPIC_API_KEY` | Claude API calls | Sim |
| `GEMINI_API_KEY` | Google Gemini calls | Sim |
| `OPENAI_API_KEY` | OpenAI calls | Opcional |
| `DATABASE_URL` | PostgreSQL connection | Sim |
| `TEAMS_WEBHOOK_SECRET` | Teams webhook validation | Opcional |
| `PEARCH_API_KEY` | Pearch AI sourcing | Opcional |
| `MICROSOFT_CLIENT_ID/SECRET` | Microsoft Graph | Opcional |
| `DEEPGRAM_API_KEY` | Voice transcription | Opcional |

### 23.3 Módulos Independentes (Portáveis sem adaptação)

Estes módulos podem ser copiados diretamente para outro projeto Python:

1. **`app/shared/memory/`** — ConversationState + ReferenceResolver (zero dependências externas)
2. **`app/shared/intelligence/param_patterns.py`** — Patterns regex para extração (zero dependências)
3. **`app/shared/resilience/stats_manager.py`** — Cache thread-safe (só usa `threading` da stdlib)
4. **`app/shared/execution/execution_plan.py`** — Dataclasses de plano de execução (zero dependências)
5. **`app/shared/compliance/fairness_guard.py`** — Guardrails de fairness
6. **`app/shared/compliance/fact_checker.py`** — Verificação de fatos

### 23.4 Módulos com Dependências (Requerem adaptação)

| Módulo | Dependência | O que adaptar |
|--------|-------------|---------------|
| `smart_extractor.py` | LLM client | Substituir chamada LLM pelo provider desejado |
| `plan_executor.py` | Domain registry | Conectar ao sistema de domínios do target |
| `task_manager.py` | asyncio | Funciona em qualquer Python 3.8+ com asyncio |
| `agents/` | LangGraph + Claude | Adaptar para framework de agentes do target |

---

## 24. Comandos de Verificação

Use estes comandos para revalidar os números deste documento a qualquer momento.

```bash
# Testes — rodar suíte completa
python3 -m pytest tests/test_agent_regression.py tests/test_v5_regression.py tests/test_seniority_jd_analyzer.py -v --tb=line
python3 -m pytest tests/test_teams_webhook.py -v --tb=line

# Actions por domínio
python3 -c "
import importlib
for d in ['sourcing','job_management','cv_screening','communication','analytics','interview_scheduling','ats_integration','automation','recruiter_assistant']:
    mod = importlib.import_module(f'app.domains.{d}.actions')
    for name in dir(mod):
        v = getattr(mod, name)
        if isinstance(v, list) and 'ACTION' in name.upper():
            print(f'{d}: {len(v)} actions'); break
"

# Linhas de código por módulo shared
for d in memory intelligence resilience execution async_processing agents compliance governance learning prompts robustness tools; do
    files=$(find "app/shared/$d" -name "*.py" ! -name "__init__.py" | wc -l)
    lines=$(find "app/shared/$d" -name "*.py" ! -name "__init__.py" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}')
    echo "$d: $files files, $lines lines"
done

# Contagem total de código executável
find app -name "*.py" ! -name "__init__.py" ! -path "*__pycache__*" | wc -l
find app -name "*.py" ! -name "__init__.py" ! -path "*__pycache__*" -exec wc -l {} + | tail -1

# Arquivos de teste
find tests -name "test_*.py" -type f | wc -l
```

---

## 25. Resumo Quantitativo

| Camada | Arquivos | Linhas | O que define |
|--------|----------|--------|-------------|
| Contratos (`base.py` + `registry.py`) | 2 | 289 | O que é um domínio |
| Orquestração | 7 | 1.961 | Como rotear e processar |
| Workflow | 1 | 447 | Pipeline de processamento |
| Features V5 | 8 | 1.747 | Memória, extração, cache, execução, async |
| Provider ABCs | 3 | 161 | VoiceProvider, ATSProviderFactory, registry |
| Agentes shared | 4 | 4.770 | State machine, conversa, nós |
| Prompts shared | 6 | 3.888 | Comportamento da LIA |
| Prompts não-shared | 5 | 2.125 | Wizard, kanban, CoT, examples |
| Robustez | 8 | 2.589 | Input/output filtering |
| Compliance | 3 | 847 | Fairness, facts, audit |
| Governança | 2 | 895 | Feature flags, monitoring |
| 9 Domínios | ~130 | ~60.000 | Lógica de negócio por domínio |
| Serviços (`app/services/`) | 189 | ~46.375 | Serviços compartilhados e shims |
| Tools infra | 3 | 815 | Execução de actions |
| Models | ~50 | ~23.900 | Schema do banco |
| Schemas | ~50 | ~10.848 | Validação de requests/responses |
| Auth | 6 | 1.074 | Autenticação JWT/WorkOS |
| Core | 4 | 2.155 | Database, config, taxonomia |
| Templates/Data | ~15 | ~19.620 | Templates curados e comunicação |
| Config/Constants | 4 | 1.079 | Pesos, cache, indústrias |
| API routes | ~120 | ~40.000 | Endpoints REST |
| Middleware/Utils/Jobs | 4 | 1.185 | Rate limiting, helpers, cron |
| Shims de compatibilidade | ~30 | ~60 | Redirecionamentos 1 linha |
| **Total código executável** | **~650+** | **~226.000+** | |

> **Importante**: Os `.md` em `docs/` são documentação de referência — útil para entender decisões, mas **não definem comportamento**. As seções 20-25 listam **apenas código executável** que precisa ser compreendido para replicar a arquitetura V5.

---

## 26. Glossário

| Termo | Definição |
|-------|-----------|
| **WSI** | WeDoTalent Skill Index — metodologia proprietária de avaliação de candidatos com 7 blocos |
| **Bloom** | Taxonomia de Bloom — 6 níveis cognitivos (Lembrar → Criar) usados para classificar respostas |
| **Dreyfus** | Modelo Dreyfus — 5 níveis de proficiência (Novato → Especialista) para avaliar maturidade |
| **Big Five** | Modelo de personalidade OCEAN — 5 traços comportamentais mapeados na avaliação |
| **CBI** | Competency-Based Interview — framework de entrevista por competências |
| **DSAR** | Data Subject Access Request — requisição de titular de dados (LGPD) |
| **XAI** | Explainable AI — explicabilidade das decisões da IA |
| **LangGraph** | Framework da LangChain para criar workflows de agentes como grafos |
| **DomainPrompt** | Contrato base que todo domínio implementa na Arquitetura B |
| **FairnessGuard** | Componente que bloqueia filtros discriminatórios (gênero, raça, idade) |
| **FactChecker** | Componente que valida claims da IA contra dados reais |
| **Fast Routing** | Roteamento por keywords/regex sem LLM (~80% dos casos na Arquitetura B) |
| **Gate** | Verificação automática antes de avançar candidato entre etapas do pipeline |
| **OTT** | One-Time Token — token de uso único para autenticação via RabbitMQ |
| **SPOF** | Single Point of Failure — ponto único de falha |

---

*Documento gerado como parte do processo de alinhamento entre equipes de protótipo e produção da Plataforma LIA. Seções 17-18 adicionadas em Fevereiro de 2026 após conclusão da migração V5 e implementação dos 5 features de convergência arquitetural. Seções 20-25 adicionadas em Fevereiro de 2026 como parte da consolidação do Blueprint Técnico V5 (`v5-architecture-blueprint.md`) e do Plano de Convergência (`convergence-plan-lia-v5.md`) neste documento único.*
