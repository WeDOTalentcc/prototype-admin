# Paralelo Técnico: Plataforma LIA vs recruiter_agent_v5
## Estrutura de IA — Arquitetura, Agentes, Serviços e Arquivos
### com Análise de Mercado, Pros/Contras e Recomendações

> **Objetivo:** comparar lado a lado o que foi construído em cada sistema em relação à inteligência artificial — orquestração, agentes, subagentes, serviços de ML/IA, memória, fairness, prompts e observabilidade. Cada seção inclui análise de mercado com pros, contras e recomendação fundamentada.
>
> **LIA (Replit):** sistema de produção com 1.747 arquivos Python | **v5 (GitHub):** MVP de pesquisa com ~50 arquivos Python
> **Repositório v5:** `https://github.com/talensestg/recruiter_agent_v5`
>
> **Concorrentes de referência usados na análise:** Eightfold AI · Phenom · SeekOut · HireVue · Paradox (Olivia) · Greenhouse · Ashby · SmartRecruiters · Workday · Beamery · hireEZ · Fetcher

---

## Índice

1. [Visão Geral Quantitativa](#1-visão-geral-quantitativa)
2. [Filosofia de Arquitetura](#2-filosofia-de-arquitetura)
3. [Estrutura de Pastas (IA)](#3-estrutura-de-pastas-ia)
4. [Orquestração e Roteamento](#4-orquestração-e-roteamento)
5. [Agentes por Domínio](#5-agentes-por-domínio)
6. [Subagentes e Grafos](#6-subagentes-e-grafos)
7. [Tool Registries (Ferramentas por Agente)](#7-tool-registries-ferramentas-por-agente)
8. [Serviços de IA/ML](#8-serviços-de-iaml)
9. [Memória e Estado](#9-memória-e-estado)
10. [Prompts e Persona](#10-prompts-e-persona)
11. [Fairness e Compliance de IA](#11-fairness-e-compliance-de-ia)
12. [PII e Proteção de Dados](#12-pii-e-proteção-de-dados)
13. [Resiliência e Fallback de LLM](#13-resiliência-e-fallback-de-llm)
14. [Aprendizado e Adaptação](#14-aprendizado-e-adaptação)
15. [Observabilidade de IA](#15-observabilidade-de-ia)
16. [Integrações com LLMs](#16-integrações-com-llms)
17. [Testes de IA](#17-testes-de-ia)
18. [Jobs e Processamento Assíncrono](#18-jobs-e-processamento-assíncrono)
19. [Inventário de Arquivos de IA](#19-inventário-de-arquivos-de-ia)

---

## 1. Visão Geral Quantitativa

| Métrica | Plataforma LIA | recruiter_agent_v5 |
|---|---|---|
| **Total de arquivos Python** | ~1.747 | ~50 |
| **Endpoints de API** | 211 | ~10 |
| **Serviços** | 244 | ~5 |
| **Modelos de banco** | 95 | 0 (sem DB) |
| **Testes** | 301 | ~5 |
| **Migrações** | 46 | 0 |
| **Agentes principais** | 15 agentes ReactAgent | 6 agentes pipeline |
| **Subagentes/Grafos** | 5+ grafos LangGraph | 9 subagentes de sourcing |
| **Domínios de IA** | 12 domínios | 2 domínios |
| **Ferramentas (tools)** | 163 tools mapeadas | ~20 tools |
| **APIs externas** | 4 ATS clients + Apify + Hubspot | 51 APIs em YAML |
| **Modelos LLM suportados** | Claude + Gemini + OpenAI (cascade) | Claude (primário) + OpenAI |
| **Linhas de código (est.)** | ~120.000 | ~4.000 |

### 🔍 Análise de Mercado — Seção 1

**Pros LIA:**
- Volume de código e cobertura de domínio compatível com plataformas enterprise como Greenhouse e SmartRecruiters
- 301 testes é um número sólido para o estágio atual — a maioria das startups de HR Tech com funding abaixo de série B tem menos de 100
- 211 endpoints cobrem praticamente toda a superfície de um ATS moderno

**Contras LIA:**
- 244 serviços é um número alto — quando serviços crescem sem uma arquitetura clara de camadas, surgem problemas de responsabilidades sobrepostas e dificuldade de manutenção (o chamado "serviço faz tudo")
- Razão tests/código provavelmente abaixo de 30% — plataformas enterprise maduras ficam entre 60–80%

**Pros v5:**
- Simplicidade: 50 arquivos = onboarding rápido, risco de debt técnico baixo
- Escopo bem definido: faz sourcing e só sourcing

**Contras v5:**
- Não é um produto — é um experimento. Sem banco, sem testes estruturados, sem multi-tenancy, não vai a produção

**O que o mercado faz:** Eightfold AI tem mais de 2.000 arquivos só no core de ML, mas mantém fronteiras claras entre camadas (data → ML → domain → API → UI). Phenom separou seu sistema em microserviços por domínio desde a série B. Ashby, startup mais moderna, tem ~800 arquivos de backend com cobertura de testes acima de 70%.

**Recomendação para LIA:** Priorizar redução de serviços duplicados e aumentar cobertura de testes para 50%+ nos domínios críticos (cv_screening, fairness, orchestrator). Não é urgente, mas é a dívida técnica que vai custar mais caro quanto mais crescer.

---

## 2. Filosofia de Arquitetura

| Aspecto | Plataforma LIA | recruiter_agent_v5 |
|---|---|---|
| **Paradigma central** | Plataforma SaaS multi-tenant de produção | MVP de pesquisa / prova de conceito |
| **Padrão de IA** | ReactAgent + LangGraph (grafos por domínio) | Pipeline sequencial linear |
| **Roteamento** | CascadedRouter com 6 tiers + cache semântico | IntentAnalyzer → pipeline fixo |
| **Estado** | WorkingMemory + LongTermMemory + PostgreSQL | Stateless (sem persistência) |
| **Multi-tenancy** | Sim — budget por tenant, guardrails por empresa | Não |
| **Fairness** | FairnessGuard em 3 camadas obrigatório | fact_checker + fairness.py opcionais |
| **Escalabilidade** | Celery + Redis + workers horizontais | Single process |
| **Observabilidade** | LangSmith + métricas customizadas + drift | Básica (logs) |
| **Aprendizado contínuo** | Learning Loop + A/B testing + ML feedback | Nenhum |

### 🔍 Análise de Mercado — Seção 2

**Pros LIA:**
- ReactAgent + LangGraph é o padrão atual da indústria — Anthropic, LangChain e Google recomendam exatamente esse padrão para sistemas de produção com múltiplos domínios
- Multi-tenancy com budget e guardrails por empresa é um diferencial real — a maioria dos competidores faz isso no nível de pricing, não no nível de execução de IA
- Fairness obrigatória (não opcional) coloca a LIA à frente de HireVue, que teve problemas regulatórios exatamente porque a checagem de viés era pós-hoc e não integrada

**Contras LIA:**
- A complexidade da arquitetura cria risco de "over-engineering" — Anthropic em sua própria documentação de agentes avisa: "comece com um único agente antes de ir para multi-agente; cada camada adiciona latência e custo"
- Com 6 tiers de orquestração, um bug em produção pode ter múltiplas causas possíveis — debugging torna-se mais difícil

**Pros v5:**
- Pipeline linear é simples de debugar e testar — cada etapa tem input e output claros
- Para sourcing externo (uso único), pipeline sequencial é suficiente e mais previsível

**Contras v5:**
- Não tem filosofia de produção — é um protótipo. Não escala, não persiste estado, não tem proteção de dados

**O que o mercado faz:** Eightfold usa "agentic talent operating system" com agentes autônomos e digital twins. Phenom lançou o "X+ Agent Studio" que permite criar agentes customizados por cliente. Paradox (Olivia) usa pipeline conversacional simples mas muito bem afinado — é deliberadamente menos complexo e mais rápido. A tendência do mercado é ir de pipelines lineares para grafos com paralelismo, mas as empresas mais bem-sucedidas mantêm complexidade proporcional ao problema.

**Recomendação para LIA:** A arquitetura está correta para produção. O risco é deixar a complexidade crescer sem documentação de decisões arquiteturais (ADRs). Crie um arquivo `docs/architecture/decisions/` com pelo menos 5 ADRs cobrindo as decisões mais críticas (por que 6 tiers, por que LangGraph, por que PostgreSQL para memória, etc.). Isso protege o conhecimento do sistema.

---

## 3. Estrutura de Pastas (IA)

### Plataforma LIA — `lia-agent-system/app/`

```
app/
├── orchestrator/                    ← ROTEAMENTO CENTRAL DE IA
│   ├── cascaded_router.py           ← 6-tier router (principal)
│   ├── fast_router.py               ← Tier 4: regex/keyword
│   ├── semantic_cache.py            ← Tier 3: pgvector
│   ├── vector_semantic_cache.py     ← Implementação vetorial
│   ├── llm_cascade.py               ← Tier 5: cascade LLMs
│   ├── memory_resolver.py           ← Tier 0: resolve referências
│   ├── main_orchestrator.py         ← Entry point principal
│   ├── intent_router.py             ← Classificação de intenção
│   ├── action_executor.py           ← Execução de ações
│   ├── task_planner.py              ← Planejamento de tarefas
│   ├── policy_engine.py             ← Engine de políticas
│   ├── state_manager.py             ← Gestão de estado
│   ├── tenant_budget.py             ← Budget por tenant
│   └── navigation_intent.py        ← Intents de navegação
│
├── domains/                         ← DOMÍNIOS DE NEGÓCIO (IA por área)
│   ├── analytics/agents/
│   ├── ats_integration/agents/
│   ├── automation/agents/
│   ├── communication/agents/
│   ├── cv_screening/agents/
│   ├── hiring_policy/agents/
│   ├── interview_scheduling/agents/
│   ├── job_management/agents/
│   ├── pipeline/agents/
│   ├── recruiter_assistant/agents/
│   ├── sourcing/agents/
│   └── policy/agents/
│
├── shared/                          ← INFRA COMPARTILHADA DE IA
│   ├── agents/                      ← Base classes e infraestrutura
│   │   ├── langgraph_react_base.py
│   │   ├── working_memory.py
│   │   ├── long_term_memory.py
│   │   ├── autonomy_engine.py
│   │   ├── confidence.py
│   │   ├── proactive_worker.py
│   │   └── react_loop.py
│   ├── compliance/                  ← FAIRNESS E AUDITORIA
│   │   ├── fairness_guard.py
│   │   ├── fact_checker.py
│   │   ├── audit_callback.py
│   │   └── audit_service.py
│   ├── learning/                    ← APRENDIZADO CONTÍNUO
│   ├── intelligence/                ← INTELIGÊNCIA SEMÂNTICA
│   ├── prompts/                     ← SISTEMA DE PROMPTS
│   ├── providers/                   ← PROVEDORES LLM
│   ├── resilience/                  ← RESILIÊNCIA
│   └── governance/                  ← GOVERNANÇA DE IA
│
├── services/                        ← SERVIÇOS (244 arquivos)
└── prompts/                         ← PROMPTS (YAML)
    ├── shared/lia_persona.yaml
    └── domains/
```

### recruiter_agent_v5 — `src/`

```
src/
├── agents/                          ← PIPELINE PRINCIPAL (6 agentes)
│   ├── intent_analyzer.py
│   ├── api_planner.py
│   ├── api_executor.py
│   ├── plan_validator.py
│   ├── data_processor.py
│   └── answer_formatter.py
│
├── domains/
│   ├── sourced_profile_sourcing/    ← DOMÍNIO DE SOURCING
│   │   ├── agents/ (9 subagentes)
│   │   ├── actions/
│   │   ├── fairness.py
│   │   └── fact_checker.py
│   └── evaluation/
│       └── security.py
│
├── v5_persona.yaml
└── docs/ (51 APIs em YAML)
```

### 🔍 Análise de Mercado — Seção 3

**Pros LIA:**
- Separação `orchestrator / domains / shared / services` é o padrão de Domain-Driven Design (DDD) — mesma estrutura que times de plataforma em Eightfold e Workday usam internamente
- `shared/compliance/` como pasta de primeiro nível sinaliza que fairness não é um add-on, é parte da arquitetura — isso é raro e valioso
- `shared/providers/` com factory de LLMs é a abordagem correta para evitar vendor lock-in

**Contras LIA:**
- Dois lugares para serviços: `app/services/` (244 arquivos, plana) e `domains/*/services/` — isso cria confusão sobre onde colocar código novo. A Seção 8 mostra serviços de IA misturados com serviços de negócio na mesma pasta
- `app/services/ats_clients/` existe em dois lugares: `app/services/ats_clients/` e `app/domains/ats_integration/services/ats_clients/` — duplicação de responsabilidade

**Pros v5:**
- Estrutura limpa e fácil de entender em menos de 5 minutos
- `domains/sourced_profile_sourcing/` é um bom exemplo de bounded context bem definido

**Contras v5:**
- Sem separação entre infra e domínio — `fairness.py` está dentro do domínio mas deveria ser shared
- Sem pasta `shared/` — qualquer crescimento vai duplicar código

**O que o mercado faz:** Empresas como Ashby e Rippling usam DDD com bounded contexts explícitos. A tendência atual é ter uma pasta `platform/` (infra compartilhada) separada de `features/` (domínio de negócio). Microserviços por domínio é o próximo passo, mas exige maturidade operacional.

**Recomendação para LIA:** Consolidar `app/services/` e `app/domains/*/services/` em uma hierarquia mais clara. Proposta: criar convenção formal de que serviços de IA ficam em `shared/` e serviços de negócio ficam em `domains/*/services/`. Mover gradualmente `app/services/ats_clients/` para `domains/ats_integration/`. Isso vai eliminar a dúvida de "onde coloco esse código".

---

## 4. Orquestração e Roteamento

### Plataforma LIA — CascadedRouter (6 Tiers)

```
Usuário → main_orchestrator.py
             ↓
    [Tier 0] memory_resolver.py      → resolve "ele", "aquela vaga" etc. (Zero custo)
             ↓ cache miss
    [Tier 1] LRU in-process          → hash MD5, O(1), sem Redis (Zero custo)
             ↓ cache miss
    [Tier 2] Redis hash cache         → distribuído, entre workers (Baixo custo)
             ↓ cache miss
    [Tier 3] semantic_cache.py        → pgvector cosine ≥ 0.92 (Baixo custo)
             ↓ cache miss
    [Tier 4] fast_router.py           → regex + keyword patterns (Baixo custo)
             ↓ sem match
    [Tier 5] llm_cascade.py           → Claude Haiku → Sonnet → Opus (Escalado)
             ↓
         domain_agent.py              → ReactAgent com tools especializadas
             ↓
    [Fallback] clarification_needed   → pergunta ao usuário
```

**Arquivos:**
- [`app/orchestrator/cascaded_router.py`](../lia-agent-system/app/orchestrator/cascaded_router.py)
- [`app/orchestrator/fast_router.py`](../lia-agent-system/app/orchestrator/fast_router.py)
- [`app/orchestrator/semantic_cache.py`](../lia-agent-system/app/orchestrator/semantic_cache.py)
- [`app/orchestrator/llm_cascade.py`](../lia-agent-system/app/orchestrator/llm_cascade.py)
- [`app/orchestrator/memory_resolver.py`](../lia-agent-system/app/orchestrator/memory_resolver.py)

---

### recruiter_agent_v5 — Pipeline Sequencial Linear

```
Usuário → IntentAnalyzerAgent
             ↓ intenção classificada
         APIPlannerAgent            → seleciona APIs no catálogo YAML (51 APIs)
             ↓ plano criado
         APIExecutorAgent           → executa as chamadas HTTP reais
             ↓ dados retornados
         PlanValidatorAgent         → valida se o plano foi executado corretamente
             ↓ validado
         DataProcessorAgent         → limpa e estrutura os dados
             ↓ processado
         AnswerFormatterAgent       → formata resposta ao usuário
```

**Arquivos:**
- [`src/agents/intent_analyzer.py`](https://github.com/talensestg/recruiter_agent_v5/blob/main/src/agents/intent_analyzer.py)
- [`src/agents/api_planner.py`](https://github.com/talensestg/recruiter_agent_v5/blob/main/src/agents/api_planner.py)
- [`src/agents/api_executor.py`](https://github.com/talensestg/recruiter_agent_v5/blob/main/src/agents/api_executor.py)
- [`src/agents/plan_validator.py`](https://github.com/talensestg/recruiter_agent_v5/blob/main/src/agents/plan_validator.py)
- [`src/agents/data_processor.py`](https://github.com/talensestg/recruiter_agent_v5/blob/main/src/agents/data_processor.py)
- [`src/agents/answer_formatter.py`](https://github.com/talensestg/recruiter_agent_v5/blob/main/src/agents/answer_formatter.py)

---

### Comparativo de Roteamento

| Aspecto | LIA | v5 |
|---|---|---|
| **Tipo** | Hierárquico multi-tier | Pipeline linear |
| **Cache semântico** | Sim (pgvector, cosine ≥ 0.92) | Não |
| **Cache de resultado** | Sim (Redis + LRU in-process) | Não |
| **Resolução de contexto** | Sim (pronomes/referências) | Não |
| **Fallback** | clarification_needed → pergunta | Falha silenciosa |
| **Custo otimizado** | Sim (escala Haiku→Sonnet→Opus) | Não |
| **Routing por intenção** | 12 domínios mapeados | Sim (single-domain) |
| **Framework** | LangGraph + custom | LangChain básico |

### 🔍 Análise de Mercado — Seção 4

**Pros LIA:**
- Cache semântico via pgvector é uma das técnicas mais recomendadas para redução de custo em produção — GPTCache, LangChain e Anthropic documentam exatamente esse padrão
- O Tier 0 (memory_resolver) para pronomes é uma sofisticação que a maioria dos concorrentes resolve de forma muito mais cara (mandando contexto completo ao LLM)
- Custo escalonado (Haiku→Sonnet→Opus) é o que a Anthropic chama de "least capable model that meets requirements" — prática recomendada

**Contras LIA:**
- 6 tiers aumentam a latência acumulada mesmo com cache miss parcial — cada tier tem overhead de I/O. Em produção com alta carga, o p95 de latência pode ser impactado
- Manter 6 tiers sincronizados (invalidação de cache entre tiers) é complexo — um bug de invalidação pode fazer o sistema responder dados desatualizados
- O threshold de cosine 0.92 para cache semântico pode ser alto demais — perguntas levemente diferentes vão sempre para o LLM, aumentando custo

**Pros v5:**
- Latência previsível: 6 etapas com tempo estimável por etapa
- Fácil de monitorar: gargalo é sempre identificável em qual agente parou

**Contras v5:**
- Zero economia de custo — toda requisição vai ao LLM do início ao fim
- Sem fallback: se o IntentAnalyzer errar a classificação, todo o pipeline produz resultado errado

**O que o mercado faz:** Paradox (Olivia) usa roteamento por intent com threshold de confiança — abaixo de 80% pede clarificação. Eightfold usa um router neural treinado internamente. Phenom X+ Agent Router é configurável pelo cliente. A tendência é adicionar um "confidence router" antes do LLM: se o classificador tem alta confiança no domínio, pula direto para o agente sem gastar tokens no LLM de intent.

**Recomendação para LIA:** Ajustar o threshold semântico de 0.92 para 0.88 (testes com diferentes thresholds são baratos de fazer com o A/B testing já implementado). Adicionar métricas de taxa de cache hit por tier — se o Tier 3 tem hit rate < 5%, avaliar se vale manter o overhead do pgvector. Implementar invalidação de cache baseada em eventos de negócio (ex: quando um candidato muda de status, invalidar caches relacionados).

---

## 5. Agentes por Domínio

### Plataforma LIA — 15 Agentes ReactAgent

| Domínio | Agente | Arquivo | Tools |
|---|---|---|---|
| **Analytics** | AnalyticsReactAgent | [`analytics/agents/analytics_react_agent.py`](../lia-agent-system/app/domains/analytics/agents/analytics_react_agent.py) | 8 |
| **ATS Integration** | ATSIntegrationReactAgent | [`ats_integration/agents/ats_integration_react_agent.py`](../lia-agent-system/app/domains/ats_integration/agents/ats_integration_react_agent.py) | 7 |
| **Automation** | AutomationReactAgent | [`automation/agents/automation_react_agent.py`](../lia-agent-system/app/domains/automation/agents/automation_react_agent.py) | 8 |
| **Communication** | CommunicationReactAgent | [`communication/agents/communication_react_agent.py`](../lia-agent-system/app/domains/communication/agents/communication_react_agent.py) | 7 |
| **CV Screening** | PipelineReactAgent | [`cv_screening/agents/pipeline_react_agent.py`](../lia-agent-system/app/domains/cv_screening/agents/pipeline_react_agent.py) | 16 |
| **Hiring Policy** | PolicyReactAgent | [`hiring_policy/agents/policy_react_agent.py`](../lia-agent-system/app/domains/hiring_policy/agents/policy_react_agent.py) | 14 |
| **Interview Scheduling** | InterviewGraph | [`interview_scheduling/agents/interview_graph.py`](../lia-agent-system/app/domains/interview_scheduling/agents/interview_graph.py) | — |
| **Job Management (Wizard)** | WizardReactAgent | [`job_management/agents/wizard_react_agent.py`](../lia-agent-system/app/domains/job_management/agents/wizard_react_agent.py) | 12 |
| **Pipeline Transition** | PipelineTransitionAgent | [`pipeline/agents/pipeline_transition_agent.py`](../lia-agent-system/app/domains/pipeline/agents/pipeline_transition_agent.py) | 22 |
| **Recruiter Assistant (Kanban)** | KanbanReactAgent | [`recruiter_assistant/agents/kanban_react_agent.py`](../lia-agent-system/app/domains/recruiter_assistant/agents/kanban_react_agent.py) | 23 |
| **Recruiter Assistant (Talent)** | TalentReactAgent | [`recruiter_assistant/agents/talent_react_agent.py`](../lia-agent-system/app/domains/recruiter_assistant/agents/talent_react_agent.py) | 14 |
| **Recruiter Assistant (Jobs)** | JobsMgmtReactAgent | [`recruiter_assistant/agents/jobs_mgmt_react_agent.py`](../lia-agent-system/app/domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py) | 15 |
| **Sourcing** | SourcingReactAgent | [`sourcing/agents/sourcing_react_agent.py`](../lia-agent-system/app/domains/sourcing/agents/sourcing_react_agent.py) | 17 |
| **Policy (v2)** | PolicyAgent | [`policy/agents/agent.py`](../lia-agent-system/app/domains/policy/agents/agent.py) | — |
| **Hiring Policy** | HiringPolicyAgent | [`hiring_policy/agents/policy_react_agent.py`](../lia-agent-system/app/domains/hiring_policy/agents/policy_react_agent.py) | — |

**Total: 163 tools mapeadas** entre todos os agentes

### recruiter_agent_v5 — 6 Agentes Pipeline + 9 Subagentes

#### Pipeline Principal

| # | Agente | Função |
|---|---|---|
| 1 | `IntentAnalyzerAgent` | Classifica intenção, define tipo de operação |
| 2 | `APIPlannerAgent` | Escolhe quais APIs usar (catálogo de 51 YAMLs) |
| 3 | `APIExecutorAgent` | Executa as chamadas HTTP |
| 4 | `PlanValidatorAgent` | Verifica se o resultado é válido |
| 5 | `DataProcessorAgent` | Estrutura e limpa dados |
| 6 | `AnswerFormatterAgent` | Gera resposta em linguagem natural |

#### Subagentes de Sourcing

| # | Subagente | Função |
|---|---|---|
| 1 | [`router.py`](https://github.com/talensestg/recruiter_agent_v5/blob/main/src/domains/sourced_profile_sourcing/agents/router.py) | Distribui tarefa entre subagentes |
| 2 | [`planner.py`](https://github.com/talensestg/recruiter_agent_v5/blob/main/src/domains/sourced_profile_sourcing/agents/planner.py) | Planeja estratégia de busca |
| 3 | [`orchestrator.py`](https://github.com/talensestg/recruiter_agent_v5/blob/main/src/domains/sourced_profile_sourcing/agents/orchestrator.py) | Coordena execução dos subagentes |
| 4 | [`search.py`](https://github.com/talensestg/recruiter_agent_v5/blob/main/src/domains/sourced_profile_sourcing/agents/search.py) | Busca candidatos nas APIs externas |
| 5 | [`detail.py`](https://github.com/talensestg/recruiter_agent_v5/blob/main/src/domains/sourced_profile_sourcing/agents/detail.py) | Aprofunda perfil do candidato |
| 6 | [`analytics.py`](https://github.com/talensestg/recruiter_agent_v5/blob/main/src/domains/sourced_profile_sourcing/agents/analytics.py) | Analisa métricas de sourcing |
| 7 | [`comparison.py`](https://github.com/talensestg/recruiter_agent_v5/blob/main/src/domains/sourced_profile_sourcing/agents/comparison.py) | Compara candidatos entre si |
| 8 | [`report.py`](https://github.com/talensestg/recruiter_agent_v5/blob/main/src/domains/sourced_profile_sourcing/agents/report.py) | Gera relatório estruturado |
| 9 | [`action.py`](https://github.com/talensestg/recruiter_agent_v5/blob/main/src/domains/sourced_profile_sourcing/agents/action.py) | Executa ações sobre candidatos |

### 🔍 Análise de Mercado — Seção 5

**Pros LIA:**
- Agentes por domínio com system prompts especializados é a recomendação do Anthropic para multi-agent systems — cada agente tem contexto mínimo e responsabilidade clara
- A existência de `stage_context.py` em cada domínio demonstra que o agente tem consciência de onde o usuário está na jornada — isso é mais sofisticado do que o que HireVue ou Greenhouse fazem com seus chatbots
- 15 agentes cobrindo 12 domínios é uma cobertura funcional completa para um ATS

**Contras LIA:**
- `hiring_policy` aparece como dois agentes distintos (`policy_react_agent.py` e `policy/agents/agent.py`) — sinal de que houve duplicação em momentos diferentes. Isso deve ser consolidado
- Agentes sem tool registry explícito (`InterviewGraph`, `PolicyAgent`) quebram o padrão — dificulta entender o que cada agente pode fazer olhando o código

**Pros v5:**
- Os 9 subagentes de sourcing são altamente coesos — cada um faz exatamente uma coisa bem definida (single responsibility principle)
- A separação `planner → orchestrator → workers` é o padrão "supervisor + workers" recomendado pelo LangGraph para paralelismo seguro

**Contras v5:**
- Só cobre sourcing — 11 dos 12 domínios da LIA não existem no v5

**O que o mercado faz:** Eightfold tem "Copilot Agents" especializados por persona (recruiter, hiring manager, candidate). Phenom tem o "X+ Agent Studio" onde cada cliente cria seus próprios agentes. Workday lançou "Workday Illuminate" com agentes por processo (R&S, performance, payroll). A tendência em 2025 é agentes com memória de persona do usuário — o agente do recrutador Joana se comporta diferente do agente do recrutador Paulo.

**Recomendação para LIA:** Consolidar os dois agentes de policy em um. Garantir que todos os agentes tenham um `tool_registry.py` explícito — mesmo grafos como `interview_graph.py` devem ter um manifesto de suas capacidades. A próxima evolução natural é adicionar "agent profiles" — comportamento do agente adaptado ao perfil do recrutador (junior vs sênior, generalista vs especialista).

---

## 6. Subagentes e Grafos

### Plataforma LIA — Grafos LangGraph

| Grafo | Arquivo | Função | Nós |
|---|---|---|---|
| **WSI Interview Graph** | [`cv_screening/agents/wsi_interview_graph.py`](../lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py) | Entrevista estruturada WSI com IA | generate_question → evaluate → score |
| **Interview Graph** | [`interview_scheduling/agents/interview_graph.py`](../lia-agent-system/app/domains/interview_scheduling/agents/interview_graph.py) | Agendamento inteligente de entrevistas | propose → confirm → notify |
| **Job Wizard Graph** | [`job_management/agents/job_wizard_graph.py`](../lia-agent-system/app/domains/job_management/agents/job_wizard_graph.py) | Wizard guiado de criação de vagas | collect_info → enrich → validate → publish |
| **Sourcing Engagement** | [`shared/agents/sourcing_engagement_nodes.py`](../lia-agent-system/app/shared/agents/sourcing_engagement_nodes.py) | Engajamento proativo com candidatos | discover → contact → follow_up |
| **Base State Machine** | [`shared/agents/base_state_machine.py`](../lia-agent-system/app/shared/agents/base_state_machine.py) | Base reutilizável para grafos | genérico |

### recruiter_agent_v5 — Subagentes de Sourcing

```
[router.py] → [planner.py] → [orchestrator.py]
                                  ↓        ↓        ↓
                            [search.py] [detail.py] [analytics.py]
                                  ↓
                            [comparison.py] → [report.py] → [action.py]
```

**Diferença chave:** v5 tem orquestração especializada para sourcing externo (9 subagentes, 51 APIs). LIA tem grafos para entrevistas e wizard de vagas, mas sourcing é mais simples.

### 🔍 Análise de Mercado — Seção 6

**Pros LIA:**
- LangGraph com grafos por domínio é o estado da arte em 2025 — Google (Vertex AI Agent Builder), Amazon (Bedrock Agents) e Microsoft (Autogen) convergem para grafos de agentes com checkpointing
- O `Base State Machine` compartilhado é um padrão excelente — garante que todos os grafos se comportam de forma consistente em erros e retries
- WSI como grafo explícito (não pipeline simples) é a abordagem correta para entrevistas — permite pausar, retomar, ramificar baseado na resposta

**Contras LIA:**
- Apenas 5 grafos para 12 domínios — significa que a maioria dos agentes usa ReactAgent simples quando poderiam se beneficiar de grafos (ex: automation, communication com múltiplas tentativas)
- Sem Human-in-the-Loop (HITL) explícito nos grafos — o `hitl_service.py` existe nos serviços mas não está integrado como nó nos grafos de LangGraph

**Pros v5:**
- 9 subagentes com execução paralela é uma vantagem real para sourcing — pesquisar em 10 APIs simultaneamente é 10x mais rápido que sequencial
- A granularidade (um agente para search, outro para detail, outro para comparison) permite substituição fácil de um agente sem quebrar os outros

**Contras v5:**
- Os grafos do v5 não têm checkpointing — se a execução falhar a meio do caminho, tudo recomeça do zero

**O que o mercado faz:** CrewAI (framework open-source popular) usa exatamente o padrão supervisor + workers para tarefas paralelas. Autogen (Microsoft) popularizou o padrão de "agentes que conversam entre si" com um moderador. LangGraph adicionou em 2025 suporte a HITL nativamente como nó de espera. HireVue usa grafos de entrevista com ramificação baseada em respostas — exatamente o que o WSI Graph da LIA faz.

**Recomendação para LIA:** Adicionar nós de HITL nos grafos de WSI e Interview — pontos de aprovação humana antes de avançar etapas críticas. Implementar checkpointing em todos os grafos usando o `PostgresSaver` do LangGraph — isso permite retomar grafos interrompidos, o que é especialmente importante para o WSI que pode durar 30+ minutos.

---

## 7. Tool Registries (Ferramentas por Agente)

### Plataforma LIA

| Domínio | Arquivo | Nº Tools | Exemplos de Tools |
|---|---|---|---|
| **Pipeline Transition** | [`pipeline/agents/pipeline_tool_registry.py`](../lia-agent-system/app/domains/pipeline/agents/pipeline_tool_registry.py) | 22 | move_candidate, add_note, request_docs, schedule_interview |
| **Kanban (Recruiter)** | [`recruiter_assistant/agents/kanban_tool_registry.py`](../lia-agent-system/app/domains/recruiter_assistant/agents/kanban_tool_registry.py) | 23 | search_candidates, bulk_move, filter_stage, get_metrics |
| **Sourcing** | [`sourcing/agents/sourcing_tool_registry.py`](../lia-agent-system/app/domains/sourcing/agents/sourcing_tool_registry.py) | 17 | search_external, enrich_profile, invite_to_apply |
| **CV Screening** | [`cv_screening/agents/pipeline_tool_registry.py`](../lia-agent-system/app/domains/cv_screening/agents/pipeline_tool_registry.py) | 16 | score_cv, extract_skills, check_requirements |
| **Hiring Policy** | [`hiring_policy/agents/policy_tool_registry.py`](../lia-agent-system/app/domains/hiring_policy/agents/policy_tool_registry.py) | 14 | check_compliance, validate_jd, apply_affirmative |
| **Talent (Recruiter)** | [`recruiter_assistant/agents/talent_tool_registry.py`](../lia-agent-system/app/domains/recruiter_assistant/agents/talent_tool_registry.py) | 14 | compare_candidates, get_profile, add_to_list |
| **Jobs Mgmt** | [`recruiter_assistant/agents/jobs_mgmt_tool_registry.py`](../lia-agent-system/app/domains/recruiter_assistant/agents/jobs_mgmt_tool_registry.py) | 15 | create_job, clone_job, update_status, get_analytics |
| **Job Wizard** | [`job_management/agents/wizard_tool_registry.py`](../lia-agent-system/app/domains/job_management/agents/wizard_tool_registry.py) | 12 | generate_jd, enrich_requirements, suggest_salary |
| **Analytics** | [`analytics/agents/analytics_tool_registry.py`](../lia-agent-system/app/domains/analytics/agents/analytics_tool_registry.py) | 8 | get_funnel, time_to_hire, diversity_metrics |
| **Automation** | [`automation/agents/automation_tool_registry.py`](../lia-agent-system/app/domains/automation/agents/automation_tool_registry.py) | 8 | create_rule, trigger_action, schedule_task |
| **ATS Integration** | [`ats_integration/agents/ats_integration_tool_registry.py`](../lia-agent-system/app/domains/ats_integration/agents/ats_integration_tool_registry.py) | 7 | sync_candidates, push_feedback, fetch_applications |
| **Communication** | [`communication/agents/communication_tool_registry.py`](../lia-agent-system/app/domains/communication/agents/communication_tool_registry.py) | 7 | send_email, send_whatsapp, schedule_message |
| **TOTAL** | | **163 tools** | |

### recruiter_agent_v5

O v5 não usa tool_registry explícito. As tools são implícitas no `APIExecutorAgent` que lê os 51 YAMLs de API dinamicamente.

### 🔍 Análise de Mercado — Seção 7

**Pros LIA:**
- Tool registry como arquivo separado é uma boa prática — facilita auditoria e testes unitários de ferramentas
- A maioria dos domínios está dentro do range seguro (7–17 tools)
- Ter exemplos de tools no registry facilita o few-shot de como o agente usa cada ferramenta

**Contras LIA — ATENÇÃO CRÍTICA:**
- **Kanban (23 tools) e Pipeline Transition (22 tools) estão acima do limite recomendado pela OpenAI e Anthropic**. O limite seguro de performance é 10–12 tools por agente. Acima disso, o modelo começa a confundir ferramentas similares, aumentar a taxa de erros e usar mais tokens no raciocínio sobre qual ferramenta escolher
- Com 23 tools no Kanban, o agente provavelmente fica "paralisado" em escolhas quando há múltiplas ferramentas que poderiam servir para a mesma tarefa

**Pros v5:**
- Tools dinâmicas via YAML é um padrão inovador — o APIPlannerAgent pode adicionar novas APIs sem alterar código

**Contras v5:**
- Sem registry explícito = sem visibilidade do que o agente pode fazer sem ler o código
- Tools dinâmicas são difíceis de testar e auditar para fairness

**O que o mercado faz:** OpenAI estabeleceu limite hard de 128 tools mas recomenda máximo de 10–12 para melhor performance. Anthropic recomenda decompor agentes com muitas tools em subagentes especializados (exatamente o que o v5 faz para sourcing). CrewAI e LangGraph recomendam "tool routing" — um agente roteador que decide qual subagente especializado ativar, em vez de dar todas as tools a um único agente.

**Recomendação para LIA — ALTA PRIORIDADE:** Decompor os agentes Kanban (23 tools) e Pipeline Transition (22 tools) em subagentes especializados. Exemplo para Kanban: `KanbanSearchAgent` (busca/filtro, 5–7 tools) + `KanbanActionAgent` (mover/atualizar candidatos, 5–7 tools) + `KanbanAnalyticsAgent` (métricas, 4–6 tools). Isso vai melhorar a precisão das respostas e reduzir o custo por query.

---

## 8. Serviços de IA/ML

### Plataforma LIA — Serviços de IA/ML (seleção dos ~244)

| Serviço | Arquivo | Função |
|---|---|---|
| **CV Scoring** | [`cv_scoring_service.py`](../lia-agent-system/app/services/cv_scoring_service.py) | Score de CV vs. requisitos da vaga |
| **WSI Screening Pipeline** | [`wsi_screening_pipeline.py`](../lia-agent-system/app/services/wsi_screening_pipeline.py) | Pipeline completo de triagem WSI |
| **WSI Deterministic Scorer** | [`wsi_deterministic_scorer.py`](../lia-agent-system/app/services/wsi_deterministic_scorer.py) | Score determinístico sem LLM |
| **Embedding Service** | [`embedding_service.py`](../lia-agent-system/app/services/embedding_service.py) | Embeddings de candidatos e vagas |
| **Hybrid Search** | [`hybrid_search_service.py`](../lia-agent-system/app/services/hybrid_search_service.py) | BM25 + pgvector combinados |
| **Intent Classifier** | [`intent_classifier.py`](../lia-agent-system/app/services/intent_classifier.py) | Classificação de intenção via LLM |
| **Enhanced Intent Classifier** | [`enhanced_intent_classifier.py`](../lia-agent-system/app/services/enhanced_intent_classifier.py) | Classificação aprimorada com contexto |
| **Model Drift Service** | [`model_drift_service.py`](../lia-agent-system/app/services/model_drift_service.py) | Detecção de drift em modelos |
| **ML Feedback Service** | [`ml_feedback_service.py`](../lia-agent-system/app/services/ml_feedback_service.py) | Feedback para treino de modelos |
| **Bias Audit Service** | [`bias_audit_service.py`](../lia-agent-system/app/services/bias_audit_service.py) | Auditoria de viés em decisões |
| **Learning Loop** | [`learning_loop_service.py`](../lia-agent-system/app/services/learning_loop_service.py) | Loop de aprendizado contínuo |
| **A/B Testing** | [`ab_testing_service.py`](../lia-agent-system/app/services/ab_testing_service.py) | A/B testing de prompts e estratégias |
| **Ragas Evaluation** | [`ragas_evaluation_service.py`](../lia-agent-system/app/services/ragas_evaluation_service.py) | Avaliação de RAG com RAGAS |
| **Pipeline Prediction** | [`pipeline_prediction_service.py`](../lia-agent-system/app/services/pipeline_prediction_service.py) | Previsão de conversão no pipeline |
| **Multimodal Service** | [`multimodal_service.py`](../lia-agent-system/app/services/multimodal_service.py) | Processamento multimodal (voz+texto) |
| **Gemini Voice** | [`gemini_voice_service.py`](../lia-agent-system/app/services/gemini_voice_service.py) | Entrevistas por voz com Gemini |
| **HITL Service** | [`hitl_service.py`](../lia-agent-system/app/services/hitl_service.py) | Human-in-the-loop para revisão |
| **Agent Quality Evaluator** | [`agent_quality_evaluator.py`](../lia-agent-system/app/services/agent_quality_evaluator.py) | Avaliação de qualidade do agente |

### recruiter_agent_v5 — Serviços de IA

| Serviço | Arquivo | Função |
|---|---|---|
| **Fairness Checker** | [`fairness.py`](https://github.com/talensestg/recruiter_agent_v5/blob/main/src/domains/sourced_profile_sourcing/fairness.py) | Checagem de viés em sourcing |
| **Fact Checker** | [`fact_checker.py`](https://github.com/talensestg/recruiter_agent_v5/blob/main/src/domains/sourced_profile_sourcing/fact_checker.py) | Anti-alucinação em resultados |
| **Security** | [`evaluation/security.py`](https://github.com/talensestg/recruiter_agent_v5/blob/main/src/domains/evaluation/security.py) | Segurança de avaliação |
| **Insights** | [`actions/insights.py`](https://github.com/talensestg/recruiter_agent_v5/blob/main/src/domains/sourced_profile_sourcing/actions/insights.py) | Geração de insights |
| **Distribution** | [`actions/distribution.py`](https://github.com/talensestg/recruiter_agent_v5/blob/main/src/domains/sourced_profile_sourcing/actions/distribution.py) | Distribuição de candidatos |

### 🔍 Análise de Mercado — Seção 8

**Pros LIA:**
- `WSI Deterministic Scorer` é um diferencial excelente — score sem LLM para casos previsíveis reduz custo e é mais auditável para fins regulatórios (Eightfold também usa scoring determinístico como camada base)
- `Hybrid Search` (BM25 + pgvector) é o estado da arte — supera busca vetorial pura em benchmarks de relevância de documentos de RH
- `Gemini Voice` para entrevistas por voz é uma funcionalidade que apenas HireVue e Paradox têm em produção
- Dois classificadores de intent (`intent_classifier.py` + `enhanced_intent_classifier.py`) sugere que há um para fallback — boa prática de resiliência

**Contras LIA:**
- Dois classificadores de intent também sugerem que o primeiro não foi suficiente e um segundo foi criado como patch — consolidar seria mais limpo
- 244 serviços na mesma pasta plana é difícil de navegar — sem subcategorização, um desenvolvedor novo leva dias para entender o que existe

**Pros v5:**
- Os 5 serviços do v5 são todos de IA pura — sem ruído de serviços de negócio misturados

**Contras v5:**
- Praticamente sem serviços de ML — não tem scoring, não tem embedding, não tem drift detection

**O que o mercado faz:** Eightfold tem um "Talent Intelligence Platform" com camadas separadas: raw data → ML features → scoring → ranking → presentation. Cada camada é um serviço isolado. SeekOut tem um "Profile Enrichment Engine" similar ao `candidate_enrichment_service.py` da LIA. A tendência é criar uma camada de "AI Gateway" que centraliza todas as chamadas a LLMs e modelos, unificando logging, rate limiting e fallback.

**Recomendação para LIA:** Criar subcategorias dentro de `app/services/`: `services/ai/`, `services/integrations/`, `services/notifications/`, `services/analytics/`. Isso vai facilitar onboarding e evitar criação de serviços duplicados. Consolidar os dois classificadores de intent em um único com configuração de estratégia.

---

## 9. Memória e Estado

| Componente | LIA | v5 |
|---|---|---|
| **Memória de trabalho (curto prazo)** | `WorkingMemory` — contexto da conversa atual, resolve pronomes | Não existe |
| **Memória de longo prazo** | `LongTermMemory` — PostgreSQL, histórico por tenant/usuário | Não existe |
| **Checkpointing** | `checkpointer.py` — snapshots de estado do grafo LangGraph | Não existe |
| **Estado de conversa** | `conversation_state.py` — estado completo por sessão | Não existe |
| **Memória de candidato** | `candidate_list_store.py` — listas e anotações do recrutador | Não existe |
| **Resolver de referências** | `reference_resolver.py` — resolve "aquele candidato" etc. | Não existe |
| **Event Store** | `event_store_service.py` — log imutável de eventos | Não existe |

**Arquivos LIA:**
- [`app/shared/agents/working_memory.py`](../lia-agent-system/app/shared/agents/working_memory.py)
- [`app/shared/agents/long_term_memory.py`](../lia-agent-system/app/shared/agents/long_term_memory.py)
- [`app/shared/agents/checkpointer.py`](../lia-agent-system/app/shared/agents/checkpointer.py)
- [`app/shared/memory/conversation_state.py`](../lia-agent-system/app/shared/memory/conversation_state.py)
- [`app/shared/memory/reference_resolver.py`](../lia-agent-system/app/shared/memory/reference_resolver.py)

### 🔍 Análise de Mercado — Seção 9

**Pros LIA:**
- Working Memory + Long-Term Memory é o padrão de 2025 — exatamente o que os papers de "cognitive architectures for LLM agents" recomendam (Mem0, LangMem, Zep usam essa estrutura)
- O `reference_resolver.py` para pronomes é uma funcionalidade que nenhum competidor de mercado documentou explicitamente — é genuinamente diferenciado
- Event Store imutável é a base para auditoria e LGPD (direito ao apagamento = marcar eventos como apagados sem alterar o log)

**Contras LIA:**
- Memória baseada em PostgreSQL tem limitação de escala — para muitos tenants com histórico longo, a tabela de memória pode crescer descontroladamente sem uma política de TTL (Time-to-Live) clara
- Não há evidência de "memória semântica" (embeddings de episódios passados) — a busca em memória de longo prazo pode ser apenas por tenant_id e timestamp, sem busca por similaridade
- Sem compressão de memória — modelos como Claude têm janela de contexto de 200k tokens mas cobram por token. Memórias longas sem compressão aumentam custo

**Pros v5:**
- Stateless é simples e previsível — sem problemas de memória desatualizada ou "contaminação" entre sessões

**Contras v5:**
- Um recrutador que volta ao sistema no dia seguinte precisa repetir todo o contexto da conversa anterior — experiência ruim em produção

**O que o mercado faz:** Mem0 (Y Combinator, 2024) é o framework especializado em memória para agentes — usa 4 tipos: sensorial (conversa atual), episódica (conversas passadas), semântica (fatos sobre o usuário), procedimental (preferências aprendidas). Zep também usa essa taxonomia. Phenom tem "candidate memory" que registra interações ao longo de meses. Paradox (Olivia) tem "candidate continuity" — a candidata que conversou 3 meses atrás é reconhecida.

**Recomendação para LIA:** Adicionar política de TTL e compressão à Long-Term Memory — após 30 dias, sumarizar episódios antigos em um resumo (via LLM) em vez de manter os episódios brutos. Adicionar busca semântica na LongTermMemory (não só por tenant/timestamp). Considerar integrar Mem0 ou Zep como camada de memória dedicada — são otimizados para este problema e já têm integração com LangGraph.

---

## 10. Prompts e Persona

### Plataforma LIA

| Arquivo | Função |
|---|---|
| [`app/prompts/shared/lia_persona.yaml`](../lia-agent-system/app/prompts/shared/lia_persona.yaml) | Persona central: nome, tom, valores, limitações |
| [`app/shared/prompts/anti_sycophancy_block.py`](../lia-agent-system/app/shared/prompts/anti_sycophancy_block.py) | Bloco anti-sycophancy em todos os prompts |
| [`app/shared/prompts/cot.py`](../lia-agent-system/app/shared/prompts/cot.py) | Chain-of-thought templates |
| [`app/shared/prompts/few_shot_examples.py`](../lia-agent-system/app/shared/prompts/few_shot_examples.py) | Few-shot genérico |
| [`app/shared/prompts/orchestrator_examples.py`](../lia-agent-system/app/shared/prompts/orchestrator_examples.py) | Few-shot para o orquestrador |
| [`app/shared/prompts/pipeline_examples.py`](../lia-agent-system/app/shared/prompts/pipeline_examples.py) | Few-shot para pipeline de triagem |
| [`app/shared/prompts/loader.py`](../lia-agent-system/app/shared/prompts/loader.py) | Loader de YAMLs com override por tenant |
| [`app/shared/prompts/prompt_registry.py`](../lia-agent-system/app/shared/prompts/prompt_registry.py) | Registro central de prompts |

### recruiter_agent_v5

| Arquivo | Função |
|---|---|
| [`v5_persona.yaml`](https://github.com/talensestg/recruiter_agent_v5/blob/main/v5_persona.yaml) | Persona do assistente v5 |
| Prompts inline nos agentes | Cada agente tem seu prompt hardcoded no construtor |

| Aspecto | LIA | v5 |
|---|---|---|
| **Gestão de prompts** | YAML externo + registry + override por tenant | Prompts inline nos agentes |
| **Anti-sycophancy** | Bloco estruturado em todos os prompts | Não implementado |
| **Few-shot** | 3 arquivos dedicados (orchestrator, pipeline, sourcing) | Não dedicado |
| **Override por empresa** | Sim (loader com tenant_id) | Não |
| **Chain-of-thought** | Estruturado (`cot.py`) | Implícito |

### 🔍 Análise de Mercado — Seção 10

**Pros LIA:**
- YAML externo + loader + override por tenant é exatamente o que Langfuse (líder de mercado em prompt management) oferece como enterprise feature — a LIA chegou lá por conta própria
- Anti-sycophancy como bloco reutilizável é uma sofisticação que poucas empresas documentam explicitamente — a maioria ainda sofre com LLMs que concordam com o usuário mesmo quando errado
- Few-shot por domínio (orchestrator_examples, pipeline_examples) melhora significativamente a qualidade — é uma das técnicas mais eficazes para reduzir erros de reasoning

**Contras LIA:**
- Sem versionamento de prompts — não há como saber qual versão de um prompt estava em produção em uma data específica, o que dificulta debugging de regressões
- Prompts em Python (`.py`) misturados com YAML (`.yaml`) — inconsistência que cria confusão sobre onde procurar/editar um prompt
- Sem sistema de avaliação automática de prompts — quando um prompt muda, não há pipeline que valide se a qualidade melhorou ou piorou

**Pros v5:**
- Prompts inline são fáceis de encontrar — você sabe exatamente onde está o prompt de cada agente

**Contras v5:**
- Hardcoded = impossível de customizar por cliente sem alterar código
- Sem versionamento, sem few-shot estruturado, sem anti-sycophancy

**O que o mercado faz:** Langfuse tem versionamento de prompts com rollback, A/B testing de variações, e métricas de qualidade por versão — é a ferramenta de referência em 2025. Humanloop e PromptLayer são alternativas. OpenAI Evals e DeepEval são usados para avaliação automática de prompts. A tendência é "prompt-as-code": prompts em controle de versão com pipelines de CI/CD para validação antes de deploy.

**Recomendação para LIA — ALTA PRIORIDADE:** Integrar Langfuse (open-source, self-hostável) para versionamento e avaliação de prompts. Isso vai custar zero de infraestrutura adicional e vai criar um ciclo de melhoria contínua onde cada mudança de prompt passa por avaliação automatizada antes de ir para produção. Padronizar todos os prompts em YAML — migrar os `.py` para `.yaml` e usar o loader existente. Adicionar um campo `version` e `updated_at` em cada YAML de prompt.

---

## 11. Fairness e Compliance de IA

### Plataforma LIA — FairnessGuard 3 Camadas

```
Camada 1: Pre-Decision Guard → fairness_guard.py → block_if_biased()
Camada 2: In-Process Monitor → audit_callback.py → log_decision()
Camada 3: Post-Decision Audit → admin_bias_audit.py → four_fifths_rule()
                                  └── test_four_fifths_rule.py
```

**Arquivos:**
- [`app/shared/compliance/fairness_guard.py`](../lia-agent-system/app/shared/compliance/fairness_guard.py)
- [`app/shared/compliance/fact_checker.py`](../lia-agent-system/app/shared/compliance/fact_checker.py)
- [`app/shared/compliance/audit_callback.py`](../lia-agent-system/app/shared/compliance/audit_callback.py)
- [`app/api/v1/admin_bias_audit.py`](../lia-agent-system/app/api/v1/admin_bias_audit.py)
- [`docs/compliance/FRIA_WSI.md`](../docs/compliance/FRIA_WSI.md)

### recruiter_agent_v5

| Arquivo | Cobertura |
|---|---|
| [`fairness.py`](https://github.com/talensestag/recruiter_agent_v5/blob/main/src/domains/sourced_profile_sourcing/fairness.py) | Só sourcing, não obrigatório |
| [`fact_checker.py`](https://github.com/talensestag/recruiter_agent_v5/blob/main/src/domains/sourced_profile_sourcing/fact_checker.py) | Só sourcing |

| Aspecto | LIA | v5 |
|---|---|---|
| **FairnessGuard estruturado** | Sim — 3 camadas obrigatórias | Não |
| **Regra 4/5 (EEOC)** | Implementada + testada | Não |
| **Anti-alucinação** | Em todos os domínios | Só em sourcing |
| **Dashboard de auditoria** | Sim | Não |
| **Explicabilidade** | API por decisão | Não |
| **FRIA documentado** | Sim | Não |

### 🔍 Análise de Mercado — Seção 11

**Pros LIA — PONTO FORTE MÁXIMO:**
- **A LIA está à frente de todos os competidores conhecidos nesta dimensão.** NYC Local Law 144 (vigente desde 2023) exige auditoria de disparate impact anual para ferramentas de decisão de emprego. A FairnessGuard da LIA já implementa a métrica de disparate impact (regra 4/5 = four_fifths_rule) — HireVue foi multado exatamente por não ter isso
- Fairness como camada 1 (pre-decision) é raro no mercado — a maioria dos competidores faz fairness post-hoc, auditando resultados depois. A LIA bloqueia decisões enviesadas antes de acontecerem
- Ter um FRIA (Fundamental Rights Impact Assessment) documentado para o WSI é o que a EU AI Act exige para sistemas de IA de alto risco — a LIA já está preparada para o mercado europeu

**Contras LIA:**
- Sem red teaming automatizado — nenhum processo documentado de testar a FairnessGuard com inputs adversariais para ver se ela pode ser contornada
- Sem relatório de fairness exportável para auditores externos — o dashboard admin é interno; auditores externos (como NYC Local Law 144 requer) precisam de um relatório padronizado

**Pros v5:**
- Ter fairness.py e fact_checker.py mesmo sendo MVP mostra consciência do problema

**Contras v5:**
- Fairness opcional e não obrigatória é exatamente o que as regulações estão proibindo — em produção, isso seria um risco legal sério

**O que o mercado faz:** Eightfold passou por auditoria independente de viés em 2023 e publicou os resultados. HireVue tem contrato com a Informs Analytics para auditoria externa anual. Pymetrics (adquirida pela Harver) foi pioneer em fairness em 2016 — usa norming groups por demografia. A tendência é "algorithmic auditing as a service" — empresas como BABL AI e Radical AI fazem auditorias externas de sistemas de IA de RH.

**Recomendação para LIA:** Criar um relatório de fairness exportável em PDF/CSV com os dados do bias_audit_service — isso vai permitir entregar o relatório para clientes que precisam de compliance regulatório (NYC LL144, EU AI Act). Adicionar red teaming no pipeline de testes: criar um dataset de inputs adversariais que tentam contornar a FairnessGuard. Isso é o que separa "fairness declarada" de "fairness comprovada".

---

## 12. PII e Proteção de Dados

| Componente | LIA | v5 |
|---|---|---|
| **PII Masking** | `pii_masking.py` — CPF, email, nome | Não |
| **Consentimento** | `consent_checker_service.py` + `granular_consent_service.py` | Não |
| **DSR (direito ao esquecimento)** | `dsr_export_service.py` | Não |
| **LGPD Cleanup** | `lgpd_cleanup_service.py` | Não |
| **Admin LGPD** | `admin_lgpd.py` | Não |
| **Audit Trail** | `audit_callback.py` | Não |

**Arquivos LIA:**
- [`app/shared/pii_masking.py`](../lia-agent-system/app/shared/pii_masking.py)
- [`app/services/consent_checker_service.py`](../lia-agent-system/app/services/consent_checker_service.py)
- [`app/services/dsr_export_service.py`](../lia-agent-system/app/services/dsr_export_service.py)
- [`app/services/lgpd_cleanup_service.py`](../lia-agent-system/app/services/lgpd_cleanup_service.py)

### 🔍 Análise de Mercado — Seção 12

**Pros LIA:**
- Consentimento granular (por finalidade, não só "aceito os termos") é a exigência da LGPD art. 7 e GDPR art. 7 — a maioria das plataformas de RH ainda usa consentimento genérico
- PII Masking antes de enviar dados ao LLM é uma prática de segurança que a maioria dos competidores não implementa — mandando nome, CPF e email diretamente aos modelos da OpenAI/Anthropic, expondo dados pessoais a terceiros
- DSR (Data Subject Request) com exportação é o que permite ao candidato exercer seu direito de acesso e portabilidade — exigido pela LGPD art. 18

**Contras LIA:**
- Não há evidência de criptografia em repouso dos campos PII no banco de dados — mascarar para o LLM é necessário mas não suficiente se o banco for comprometido
- Sem TTL automático nos dados de conversa — mensagens de conversas com PII podem ficar indefinidamente no banco
- O `pii_masking.py` provavelmente usa regex/pattern matching para detectar PII — modelos modernos de NER (Named Entity Recognition) têm muito mais precisão na detecção de PII em texto livre de currículos

**Pros v5:**
- Sem dados persistidos = sem risco de vazamento de dados em repouso

**Contras v5:**
- Sem qualquer proteção de PII, LGPD ou GDPR — inviável para produção no Brasil ou Europa

**O que o mercado faz:** Greenhouse tem "Candidate Data Removal" automático após período configurável. Lever tem "GDPR Export" para candidatos. Workday usa criptografia campo a campo para PII com chaves por cliente. Microsoft Presidio (open-source) é o framework mais usado para NER e anonimização de PII em texto livre — integrado com LangChain.

**Recomendação para LIA:** Avaliar substituição do `pii_masking.py` baseado em regex pelo Microsoft Presidio — tem modelos de NER treinados que detectam PII em português, o que regex não faz bem. Adicionar TTL nos registros de conversa: após 90 dias sem acesso, sumarizar e apagar mensagens individuais (manter só o resumo). Implementar criptografia de campo para CPF e dados sensíveis no PostgreSQL usando `pgcrypto`.

---

## 13. Resiliência e Fallback de LLM

| Componente | LIA | v5 |
|---|---|---|
| **Circuit Breaker** | Sim — abre circuito após N falhas | Não |
| **LLM Cascade** | Haiku→Sonnet→Opus→Gemini→GPT-4o | Não |
| **Cache de fallback** | Sim (resposta cacheada se LLM indisponível) | Não |
| **Retry com backoff** | Sim | Básico (LangChain default) |
| **Timeout por chamada** | Sim (`timed_tool_node.py`) | Não documentado |
| **Métricas de disponibilidade** | Sim (`stats_manager.py`) | Não |

**Arquivos LIA:**
- [`app/shared/resilience/circuit_breaker.py`](../lia-agent-system/app/shared/resilience/circuit_breaker.py)
- [`app/orchestrator/llm_cascade.py`](../lia-agent-system/app/orchestrator/llm_cascade.py)
- [`app/shared/agents/timed_tool_node.py`](../lia-agent-system/app/shared/agents/timed_tool_node.py)
- [`app/shared/resilience/stats_manager.py`](../lia-agent-system/app/shared/resilience/stats_manager.py)

### 🔍 Análise de Mercado — Seção 13

**Pros LIA:**
- Circuit breaker por provider é o padrão de systems design para dependências externas (Netflix Hystrix popularizou esse padrão) — raro em plataformas de HR AI
- Cascade Haiku→Sonnet→Opus→Gemini→GPT-4o é uma das poucas implementações multi-provider de fallback que vi documentada em sistemas de RH
- `timed_tool_node.py` com timeout por tool é uma proteção crítica — sem timeout, uma tool que trava derruba o agente inteiro

**Contras LIA:**
- Circuit breaker sem SLO (Service Level Objective) definido — não fica claro qual é a taxa de erro aceitável antes de abrir o circuito por quanto tempo
- Sem "degraded mode" — quando todos os providers falham, qual é o comportamento? O ideal é ter uma resposta de fallback pré-programada para os casos mais comuns
- Sem chaos engineering — não há testes que deliberadamente falham providers para validar que o fallback funciona em produção

**Pros v5:**
- Menos dependências = menos pontos de falha

**Contras v5:**
- Se Claude fica indisponível (como aconteceu em incidentes de 2024), o v5 simplesmente para

**O que o mercado faz:** Stripe tem o padrão mais maduro de circuit breaker (documentado publicamente). Plataformas de IA como Portkey e LiteLLM oferecem "LLM Gateway" com failover automático entre providers — é o que a LIA implementou internamente. A tendência é externalizar o LLM Gateway (LiteLLM, Portkey, OpenRouter) para não ter que manter essa lógica internamente.

**Recomendação para LIA:** Definir SLOs formais para o circuit breaker — ex: abre após 5 falhas em 60 segundos, fecha após 2 minutos. Criar um "modo degradado" para as perguntas mais frequentes: se todos os LLMs falharem, responder com as últimas respostas cacheadas + uma mensagem clara. Considerar LiteLLM como substituição do `llm_cascade.py` — é open-source, mantido ativamente, e suporta 100+ providers com failover, rate limiting e custo tracking.

---

## 14. Aprendizado e Adaptação

### Plataforma LIA — Ciclo de Aprendizado

```
Feedback → ml_feedback_service.py → learning_loop_service.py
               → ab_testing_service.py (testa variações)
               → template_learning_service.py (atualiza templates)
               → routing_learning_service.py (ajusta roteamento)
               → finetuning_export.py (exporta dataset)
               → model_drift_service.py (detecta regressões)
```

**Arquivos:**
- [`app/shared/learning/learning_loop_service.py`](../lia-agent-system/app/shared/learning/learning_loop_service.py)
- [`app/shared/learning/ab_testing_service.py`](../lia-agent-system/app/shared/learning/ab_testing_service.py)
- [`app/services/model_drift_service.py`](../lia-agent-system/app/services/model_drift_service.py)
- [`app/services/ml_feedback_service.py`](../lia-agent-system/app/services/ml_feedback_service.py)
- [`app/jobs/drift_job.py`](../lia-agent-system/app/jobs/drift_job.py)

### recruiter_agent_v5 — Sem mecanismo de aprendizado

### 🔍 Análise de Mercado — Seção 14

**Pros LIA:**
- Learning loop completo (feedback → ajuste → validação → deploy) é o que diferencia um produto que melhora sozinho de um que precisa de intervenção manual constante — apenas Eightfold e Phenom têm algo comparável no segmento de HR Tech
- A/B testing de prompts é uma técnica que Google, OpenAI e Anthropic recomendam mas poucos implementam de verdade — a LIA tem isso
- `finetuning_export.py` é pensamento de longo prazo — criar o dataset agora para fine-tuning futuro é a abordagem correta mesmo sem usar fine-tuning hoje

**Contras LIA:**
- Risco de "feedback loop viciado" — se recrutadores com viés sistemático fazem o feedback, o sistema aprende o viés deles. Sem uma camada de validação de fairness no próprio ciclo de feedback, o learning loop pode degradar a fairness ao longo do tempo
- Sem rollback de aprendizado — se uma mudança aprendida piora a qualidade, há como reverter?
- A/B testing com usuários reais de produção pode criar experiências inconsistentes — um recrutador pode achar que o sistema "muda de comportamento" entre sessões

**Pros v5:**
- Sem aprendizado = sem risco de feedback loop viciado

**Contras v5:**
- Sem aprendizado = o sistema é o mesmo no dia 1 e no dia 365

**O que o mercado faz:** 57% das empresas de IA em produção usam algum tipo de feedback loop (Gartner 2025). Eightfold usa "reinforcement learning from human feedback" (RLHF) similar ao que OpenAI fez com o ChatGPT. Phenom tem "AI that learns from your pipeline" como feature de marketing. A tendência é "RLAIF" (RL from AI feedback) — usar um LLM avaliador para gerar feedback sintético e complementar o feedback humano.

**Recomendação para LIA — CRÍTICO:** Adicionar validação de fairness no ciclo de feedback — antes de aplicar qualquer aprendizado, rodar a `fairness_guard.py` no novo comportamento para garantir que o aprendizado não introduziu viés. Implementar rollback de learning: manter snapshots das versões de prompt/template antes de cada atualização pelo learning loop. Limitar o A/B testing a features não críticas para decisões de admissão — ou garantir que ambas as variantes passem pelo mesmo FairnessGuard.

---

## 15. Observabilidade de IA

| Componente | LIA | v5 |
|---|---|---|
| **Tracing de execução** | LangSmith + `execution_log_store.py` | Logs básicos |
| **Métricas de token** | `ai_consumption.py` por tenant | Não |
| **Qualidade de resposta** | `agent_quality_evaluator.py` + RAGAS | Não |
| **Explicabilidade** | `agent_explainability.py` por decisão | Não |
| **Drift detection** | `model_drift_service.py` + job diário | Não |
| **Health alerts** | `agent_health_alert_service.py` | Não |
| **Monitoramento de agente** | `agent_monitoring_service.py` | Não |

**Arquivos LIA:**
- [`app/shared/agents/observability.py`](../lia-agent-system/app/shared/agents/observability.py)
- [`app/api/v1/ai_consumption.py`](../lia-agent-system/app/api/v1/ai_consumption.py)
- [`app/api/v1/agent_explainability.py`](../lia-agent-system/app/api/v1/agent_explainability.py)
- [`app/services/ragas_evaluation_service.py`](../lia-agent-system/app/services/ragas_evaluation_service.py)

### 🔍 Análise de Mercado — Seção 15

**Pros LIA:**
- LangSmith + RAGAS é a combinação de referência para LLM observability em 2025 — LangSmith para tracing, RAGAS para qualidade de RAG
- `ai_consumption.py` por tenant é um diferencial de negócio além de técnico — permite cobrar por uso real de IA, algo que Phenom e Eightfold fazem mas não documentam como

**Contras LIA:**
- Sem OpenTelemetry (OTEL) — o padrão da indústria está convergindo para OTEL como protocolo comum. Sem OTEL, não é possível integrar com Datadog, Grafana, New Relic sem customização
- RAGAS mede qualidade de RAG mas não mede qualidade de raciocínio do agente (tool selection accuracy, plan correctness) — são métricas complementares
- Sem alertas proativos de custo — se um tenant começar a usar 10x mais tokens que o normal (por bug ou abuso), quanto tempo leva para detectar?

**Pros v5:**
- Sem observabilidade = sem overhead de logging

**Contras v5:**
- Sem observabilidade = debugging de produção é impossível. "Cego" em produção

**O que o mercado faz:** Arize AI é a referência para observabilidade de LLM em enterprise — monitora hallucinations, toxicity, fairness e performance em tempo real. Helicone é a alternativa mais leve. LangSmith (da LangChain) é o mais integrado com o stack da LIA. A tendência é "LLM Guardrails as Observability" — usar ferramentas como Guardrails AI, NVIDIA NeMo Guardrails para monitorar e interceptar outputs em tempo real.

**Recomendação para LIA:** Adicionar OpenTelemetry como camada de exportação — isso permite redirecionar traces para qualquer destino (Datadog, Grafana, etc.) sem mudar o código. Adicionar alertas de custo por tenant: se o consumo de tokens de um tenant aumentar mais de 3x em 24h, disparar alerta. Implementar "LLM quality scorecard" semanal por domínio de agente — relatório automático de hallucination rate, tool error rate, user satisfaction.

---

## 16. Integrações com LLMs

| Provider | LIA | v5 |
|---|---|---|
| **Claude (Anthropic)** | Haiku, Sonnet, Opus — principal | Sonnet — único |
| **Gemini (Google)** | Pro, Flash — voz + fallback | Não |
| **OpenAI** | GPT-4o, GPT-4o-mini — fallback | GPT-4o — alternativo |
| **Cascade automático** | Haiku→Sonnet→Opus→Gemini→GPT | Não |
| **Factory pattern** | Sim (`llm_factory.py`) | Não |
| **Interface base** | Sim (`llm_client.py`) | Não |

**Arquivos LIA:**
- [`app/shared/providers/llm_factory.py`](../lia-agent-system/app/shared/providers/llm_factory.py)
- [`app/shared/providers/llm_claude.py`](../lia-agent-system/app/shared/providers/llm_claude.py)
- [`app/shared/providers/llm_gemini.py`](../lia-agent-system/app/shared/providers/llm_gemini.py)
- [`app/shared/providers/llm_openai.py`](../lia-agent-system/app/shared/providers/llm_openai.py)

### 🔍 Análise de Mercado — Seção 16

**Pros LIA:**
- Multi-provider com cascade é o padrão de resiliência mais avançado disponível — praticamente nenhuma plataforma de HR Tech documenta isso publicamente
- Gemini para voz é uma escolha arquitetural inteligente — Gemini 2.0 Flash tem latência muito menor que Claude para streaming de voz
- Factory pattern garante que adicionar um novo provider (ex: Meta Llama, Mistral) é uma mudança isolada

**Contras LIA:**
- Sem suporte a modelos locais (Ollama, vLLM) — para clientes com requisitos de data residency (dados não podem sair do Brasil), seria necessário rodar modelos locais
- Sem rate limiting por provider no nível do factory — se Haiku tem quota de 100k tokens/min e a LIA ultrapassa, todos os agentes são impactados
- Sem tracking de custo por provider no factory — o `ai_consumption.py` existe mas não está claro se está integrado ao factory

**Pros v5:**
- Single provider = zero complexidade de routing entre providers

**Contras v5:**
- Vendor lock-in total em Claude — qualquer mudança de preço ou API break da Anthropic impacta 100% do sistema

**O que o mercado faz:** LiteLLM (open-source, muito popular em 2025) oferece uma API unificada para 100+ LLMs com rate limiting, custo tracking e failover automático — é o "nginx dos LLMs". OpenRouter faz o mesmo como serviço gerenciado. Portkey adiciona guardrails e caching. A tendência é externalizar o LLM Gateway para não reinventar a roda.

**Recomendação para LIA:** Avaliar a migração do `llm_factory.py` + providers para LiteLLM como proxy. Isso vai eliminar ~400 linhas de código de integração e dar acesso a 100+ modelos, incluindo modelos locais via Ollama para clientes com data residency. Se não quiser migrar, adicionar rate limiting por provider e tracking de custo no factory atual.

---

## 17. Testes de IA

| Tipo de Teste | LIA | v5 |
|---|---|---|
| **Testes unitários** | ~200 arquivos de teste | ~3 arquivos |
| **Testes de fairness** | `test_four_fifths_rule.py` + outros | Não |
| **Dataset golden** | `golden_dataset.py` | Não |
| **Testes de agente** | Sim (por domínio) | Não estruturado |
| **Testes de LLM** | Integração com LLM real | Não documentado |
| **Testes de regressão** | Não documentado como pipeline CI | Não |

**Arquivos LIA:**
- [`app/tests/test_four_fifths_rule.py`](../lia-agent-system/app/tests/test_four_fifths_rule.py)
- [`app/tests/golden_dataset.py`](../lia-agent-system/app/tests/golden_dataset.py)

### 🔍 Análise de Mercado — Seção 17

**Pros LIA:**
- Golden dataset para avaliação de agentes é uma prática que Google, Anthropic e OpenAI usam internamente — ter isso em uma plataforma de HR Tech é avançado
- `test_four_fifths_rule.py` é o tipo de teste que auditors externos pedem — prova documentada de que o sistema foi validado contra a regra da EEOC

**Contras LIA:**
- 301 arquivos de teste mas não está claro qual é a cobertura de código — quantidade de arquivos não equivale a qualidade de cobertura
- Sem pipeline de CI/CD para testes de LLM — testes que chamam LLMs reais são lentos e caros; sem uma estratégia de quando rodá-los (mock vs real), tende a deixar de rodar
- Sem "shadow testing" — prática de rodar a nova versão em paralelo com a produção sem servir o resultado, para comparar qualidade

**Pros v5:**
- Os poucos testes existentes provavelmente têm foco claro

**Contras v5:**
- 5 testes para 50 arquivos = praticamente sem cobertura

**O que o mercado faz:** DeepEval é o framework de referência para testes de LLM em 2025 — tem métricas nativas de hallucination, bias, toxicity, faithfulness (para RAG). Confident AI (empresa por trás do DeepEval) oferece CI/CD para LLM testing. A tendência é "LLM as judge" — usar um LLM mais capaz (Claude Opus ou GPT-4) para avaliar as respostas do LLM de produção automaticamente.

**Recomendação para LIA:** Integrar DeepEval ao pipeline de testes — adicionar ao menos 3 métricas: `hallucination_score`, `faithfulness` (para RAG/WSI), `bias_score`. Criar pipeline separado de "LLM tests" que roda semanalmente (não a cada commit) para controlar custo. Implementar "LLM as judge" usando Claude Opus como avaliador do Claude Haiku/Sonnet em produção — quando o juiz detecta qualidade abaixo de threshold, dispara alerta.

---

## 18. Jobs e Processamento Assíncrono

| Job | LIA | v5 |
|---|---|---|
| **Drift Detection** | `drift_job.py` — diário | Não |
| **Celery Tasks** | `celery_tasks.py` — geral | Não |
| **Relatórios agendados** | `scheduled_reports.py` — semanal | Não |
| **Follow-up proativo** | `followup_service.py` — contínuo | Não |
| **WSI abandonado** | `wsi_abandoned_service.py` — diário | Não |
| **Framework** | Celery + Redis | — |

**Arquivos LIA:**
- [`app/jobs/drift_job.py`](../lia-agent-system/app/jobs/drift_job.py)
- [`app/jobs/celery_tasks.py`](../lia-agent-system/app/jobs/celery_tasks.py)
- [`app/jobs/scheduled_reports.py`](../lia-agent-system/app/jobs/scheduled_reports.py)
- [`app/jobs/followup_service.py`](../lia-agent-system/app/jobs/followup_service.py)

### 🔍 Análise de Mercado — Seção 18

**Pros LIA:**
- Celery + Redis é o stack padrão de processamento assíncrono em Python — maduro, bem documentado, escalável horizontalmente
- `followup_service.py` contínuo para follow-up proativo de candidatos é uma funcionalidade que Paradox (Olivia) comercializa como feature premium — a LIA já tem
- `wsi_abandoned_service.py` mostra maturidade de produto — recuperar usuários que abandonaram o processo é algo que plataformas de e-commerce fazem mas plataformas de ATS raramente

**Contras LIA:**
- Apenas 5 jobs para uma plataforma desta complexidade parece pouco — processos como re-indexação de embeddings, cleanup de caches expirados, e sync de ATS provavelmente rodam de forma ad-hoc ou manual
- Sem monitoramento de jobs — se o `drift_job.py` falhar silenciosamente por 2 semanas, ninguém vai saber até que um problema de drift seja detectado de outra forma
- Celery tem overhead significativo para jobs simples — para jobs de baixa frequência, alternativas mais leves como APScheduler ou Dramatiq podem ser mais adequadas

**Pros v5:**
- Sem jobs = sem overhead operacional

**Contras v5:**
- Sem processamento assíncrono = operações lentas bloqueiam o usuário

**O que o mercado faz:** Greenhouse usa Sidekiq (Ruby) para processamento assíncrono com retry automático e DLQ (Dead Letter Queue). Workday usa Quartz Scheduler para jobs enterprise com dependências entre jobs. A tendência em 2025 é "workflow orchestration" com Temporal ou Prefect — permitem definir workflows complexos com retry, versioning e observabilidade muito superiores ao Celery puro.

**Recomendação para LIA:** Adicionar monitoramento de jobs com alertas — se um job scheduled não rodou no tempo esperado (ex: drift_job não rodou em 25h), disparar alerta. Adicionar Dead Letter Queue no Celery — tasks que falharam N vezes devem ir para uma fila especial para revisão manual, não desaparecer silenciosamente. Avaliar Temporal para os workflows mais complexos (WSI pipeline, learning loop) — é open-source e tem UI de monitoramento nativa.

---

## 19. Inventário de Arquivos de IA

### Arquivos-chave de IA — LIA

| Categoria | Arquivo | Caminho |
|---|---|---|
| **Orquestração** | `cascaded_router.py` | [`app/orchestrator/cascaded_router.py`](../lia-agent-system/app/orchestrator/cascaded_router.py) |
| **Orquestração** | `fast_router.py` | [`app/orchestrator/fast_router.py`](../lia-agent-system/app/orchestrator/fast_router.py) |
| **Orquestração** | `semantic_cache.py` | [`app/orchestrator/semantic_cache.py`](../lia-agent-system/app/orchestrator/semantic_cache.py) |
| **Orquestração** | `llm_cascade.py` | [`app/orchestrator/llm_cascade.py`](../lia-agent-system/app/orchestrator/llm_cascade.py) |
| **Orquestração** | `memory_resolver.py` | [`app/orchestrator/memory_resolver.py`](../lia-agent-system/app/orchestrator/memory_resolver.py) |
| **Agente base** | `langgraph_react_base.py` | [`app/shared/agents/langgraph_react_base.py`](../lia-agent-system/app/shared/agents/langgraph_react_base.py) |
| **Agente base** | `autonomy_engine.py` | [`app/shared/agents/autonomy_engine.py`](../lia-agent-system/app/shared/agents/autonomy_engine.py) |
| **Fairness** | `fairness_guard.py` | [`app/shared/compliance/fairness_guard.py`](../lia-agent-system/app/shared/compliance/fairness_guard.py) |
| **Fairness** | `fact_checker.py` | [`app/shared/compliance/fact_checker.py`](../lia-agent-system/app/shared/compliance/fact_checker.py) |
| **PII** | `pii_masking.py` | [`app/shared/pii_masking.py`](../lia-agent-system/app/shared/pii_masking.py) |
| **Memória** | `working_memory.py` | [`app/shared/agents/working_memory.py`](../lia-agent-system/app/shared/agents/working_memory.py) |
| **Memória** | `long_term_memory.py` | [`app/shared/agents/long_term_memory.py`](../lia-agent-system/app/shared/agents/long_term_memory.py) |
| **Aprendizado** | `learning_loop_service.py` | [`app/shared/learning/learning_loop_service.py`](../lia-agent-system/app/shared/learning/learning_loop_service.py) |
| **Aprendizado** | `ab_testing_service.py` | [`app/shared/learning/ab_testing_service.py`](../lia-agent-system/app/shared/learning/ab_testing_service.py) |
| **Prompts** | `lia_persona.yaml` | [`app/prompts/shared/lia_persona.yaml`](../lia-agent-system/app/prompts/shared/lia_persona.yaml) |
| **Prompts** | `anti_sycophancy_block.py` | [`app/shared/prompts/anti_sycophancy_block.py`](../lia-agent-system/app/shared/prompts/anti_sycophancy_block.py) |
| **LLMs** | `llm_factory.py` | [`app/shared/providers/llm_factory.py`](../lia-agent-system/app/shared/providers/llm_factory.py) |
| **Resiliência** | `circuit_breaker.py` | [`app/shared/resilience/circuit_breaker.py`](../lia-agent-system/app/shared/resilience/circuit_breaker.py) |
| **Testes** | `test_four_fifths_rule.py` | [`app/tests/test_four_fifths_rule.py`](../lia-agent-system/app/tests/test_four_fifths_rule.py) |
| **Testes** | `golden_dataset.py` | [`app/tests/golden_dataset.py`](../lia-agent-system/app/tests/golden_dataset.py) |

### Arquivos-chave de IA — v5

| Categoria | Arquivo | Caminho |
|---|---|---|
| **Pipeline** | `intent_analyzer.py` | [`src/agents/intent_analyzer.py`](https://github.com/talensestg/recruiter_agent_v5/blob/main/src/agents/intent_analyzer.py) |
| **Pipeline** | `api_planner.py` | [`src/agents/api_planner.py`](https://github.com/talensestg/recruiter_agent_v5/blob/main/src/agents/api_planner.py) |
| **Pipeline** | `api_executor.py` | [`src/agents/api_executor.py`](https://github.com/talensestg/recruiter_agent_v5/blob/main/src/agents/api_executor.py) |
| **Pipeline** | `answer_formatter.py` | [`src/agents/answer_formatter.py`](https://github.com/talensestg/recruiter_agent_v5/blob/main/src/agents/answer_formatter.py) |
| **Sourcing** | `search.py` | [`src/domains/sourced_profile_sourcing/agents/search.py`](https://github.com/talensestg/recruiter_agent_v5/blob/main/src/domains/sourced_profile_sourcing/agents/search.py) |
| **Sourcing** | `comparison.py` | [`src/domains/sourced_profile_sourcing/agents/comparison.py`](https://github.com/talensestg/recruiter_agent_v5/blob/main/src/domains/sourced_profile_sourcing/agents/comparison.py) |
| **Fairness** | `fairness.py` | [`src/domains/sourced_profile_sourcing/fairness.py`](https://github.com/talensestg/recruiter_agent_v5/blob/main/src/domains/sourced_profile_sourcing/fairness.py) |
| **Fact check** | `fact_checker.py` | [`src/domains/sourced_profile_sourcing/fact_checker.py`](https://github.com/talensestg/recruiter_agent_v5/blob/main/src/domains/sourced_profile_sourcing/fact_checker.py) |
| **Persona** | `v5_persona.yaml` | [`v5_persona.yaml`](https://github.com/talensestg/recruiter_agent_v5/blob/main/v5_persona.yaml) |

---

## Resumo Executivo e Prioridades de Melhoria

### Scorecard por Dimensão

| Dimensão | LIA | v5 | Mercado Referência | Urgência LIA |
|---|---|---|---|---|
| **1. Orquestração** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ (Eightfold) | Ajustes finos |
| **2. Filosofia** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ (Phenom) | Documentar ADRs |
| **3. Estrutura** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ (Ashby) | Consolidar pastas |
| **4. Agentes** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ (Eightfold) | Consolidar policy |
| **5. Subagentes/Grafos** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ (CrewAI padrão) | HITL nos grafos |
| **6. Tool Registries** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ (OpenAI rec.) | **ALTA — decompor agentes** |
| **7. Serviços ML** | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐ (SeekOut) | Categorizar pastas |
| **8. Memória** | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐ (Mem0 padrão) | TTL + compressão |
| **9. Prompts** | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ (Langfuse) | **ALTA — versionamento** |
| **10. Fairness** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ (HireVue) | Relatório exportável |
| **11. PII/LGPD** | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐ (Greenhouse) | NER para PII |
| **12. Resiliência** | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐ (Stripe padrão) | SLOs formais |
| **13. Aprendizado** | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐ (Eightfold) | **CRÍTICO — fairness no loop** |
| **14. Observabilidade** | ⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐ (Arize) | OTEL + alertas custo |
| **15. LLMs** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ (LiteLLM) | Avaliar LiteLLM |
| **16. Testes** | ⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ (DeepEval) | **ALTA — DeepEval + CI** |
| **17. Jobs** | ⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐ (Sidekiq) | DLQ + monitoramento |

### Top 5 Recomendações por Prioridade

| # | Recomendação | Impacto | Esforço | Por quê agora |
|---|---|---|---|---|
| **1** | Decompor Kanban (23 tools) e Pipeline (22 tools) em subagentes | Qualidade de resposta ↑ + custo ↓ | Médio (2 sprints) | Acima do limite seguro da Anthropic — afeta qualidade hoje |
| **2** | Adicionar validação de fairness no learning loop | Risco regulatório ↓ | Baixo (1 sprint) | Sem isso, o aprendizado pode introduzir viés silenciosamente |
| **3** | Integrar versionamento de prompts (Langfuse ou similar) | Debugabilidade ↑ + qualidade ↑ | Baixo (1 sprint) | Mudanças de prompt sem versionamento são cegas |
| **4** | Integrar DeepEval no CI/CD para testes de LLM | Confiabilidade ↑ | Médio (2 sprints) | 301 testes mas sem cobertura de qualidade de LLM |
| **5** | Criar relatório de fairness exportável (PDF/CSV) | Compliance comercial ↑ | Baixo (1 sprint) | Clientes enterprise e reguladores pedem isso na due diligence |

---

*Documento versão 2.0 — 19/03/2026 | LIA v1.1 | recruiter_agent_v5 branch: main*
*Análise de mercado baseada em: Eightfold AI, Phenom, SeekOut, HireVue, Paradox, Greenhouse, Ashby, SmartRecruiters, Workday, Beamery, hireEZ, LangChain docs, Anthropic docs, OpenAI docs, Gartner 2025, NYC Local Law 144, EU AI Act, LGPD*

---

# Plano de Otimização da Plataforma LIA
## Baseado no Diagnóstico Comparativo — Foco exclusivo na LIA

> **Contexto:** O diagnóstico das 17 dimensões revelou que a LIA está acima do mercado em fairness, memória, resiliência e aprendizado, mas tem pontos concretos de melhoria em tool registries, prompts, testes e estrutura de código. Este plano organiza todas as recomendações em 4 fases executáveis, do mais urgente ao mais estratégico.
>
> **Princípio:** nenhuma otimização aqui quebra funcionalidade existente — todas são aditivas ou refatorações internas.

---

## Visão Geral do Plano

| Fase | Horizonte | Foco | Itens |
|---|---|---|---|
| **Fase 1 — Correções Críticas** | Semanas 1–2 | Riscos ativos que afetam qualidade ou compliance hoje | 3 itens |
| **Fase 2 — Ganhos Rápidos** | Semanas 3–6 | Melhorias de alto impacto com baixo esforço | 5 itens |
| **Fase 3 — Melhorias Estruturais** | Meses 2–4 | Refatorações que aumentam qualidade e manutenibilidade | 5 itens |
| **Fase 4 — Evolução Estratégica** | Meses 4–9 | Funcionalidades que abrem novos mercados ou capacidades | 4 itens |

---

## Fase 1 — Correções Críticas
### Semanas 1–2 | Riscos ativos que afetam qualidade ou compliance hoje

---

### F1-01 · Decompor agentes com excesso de tools

**Problema diagnosticado:** KanbanReactAgent (23 tools) e PipelineTransitionAgent (22 tools) estão acima do limite seguro recomendado pela Anthropic e OpenAI (10–12 tools por agente). Acima desse limite, o modelo confunde ferramentas similares, aumenta a taxa de erro de seleção de tool e consome mais tokens no raciocínio.

**Impacto atual:** respostas do Kanban e Pipeline potencialmente imprecisas; custo por query desnecessariamente alto.

**O que fazer:**

Dividir cada agente em 3 subagentes especializados:

```
KanbanReactAgent (23 tools) → decompor em:
  ├── KanbanSearchAgent      (7 tools): search_candidates, filter_stage, get_profile, list_candidates, ...
  ├── KanbanActionAgent      (8 tools): move_candidate, bulk_move, add_note, update_status, ...
  └── KanbanAnalyticsAgent   (6 tools): get_metrics, time_to_hire, funnel_report, ...

PipelineTransitionAgent (22 tools) → decompor em:
  ├── PipelineDecisionAgent  (8 tools): evaluate_candidate, score_fit, check_requirements, ...
  ├── PipelineMoveAgent      (7 tools): move_stage, request_docs, schedule_interview, ...
  └── PipelineCommsAgent     (6 tools): send_feedback, notify_candidate, log_action, ...
```

**Arquivos afetados:**
- [`app/domains/recruiter_assistant/agents/kanban_react_agent.py`](../lia-agent-system/app/domains/recruiter_assistant/agents/kanban_react_agent.py)
- [`app/domains/recruiter_assistant/agents/kanban_tool_registry.py`](../lia-agent-system/app/domains/recruiter_assistant/agents/kanban_tool_registry.py)
- [`app/domains/pipeline/agents/pipeline_transition_agent.py`](../lia-agent-system/app/domains/pipeline/agents/pipeline_transition_agent.py)
- [`app/domains/pipeline/agents/pipeline_tool_registry.py`](../lia-agent-system/app/domains/pipeline/agents/pipeline_tool_registry.py)
- [`app/orchestrator/cascaded_router.py`](../lia-agent-system/app/orchestrator/cascaded_router.py) — atualizar roteamento para os novos subagentes

**Esforço:** 2 sprints (1 por agente)
**Impacto esperado:** precisão de resposta ↑ ~20%, custo por query ↓ ~15%
**Métrica de sucesso:** taxa de tool_call_error < 3% nos dois domínios (medido via LangSmith)

---

### F1-02 · Adicionar validação de fairness no learning loop

**Problema diagnosticado:** O learning loop (`learning_loop_service.py`) aplica aprendizado baseado no feedback dos recrutadores sem passar pelo `FairnessGuard`. Se recrutadores com viés sistemático fornecem feedback negativo consistente sobre determinados perfis, o sistema aprende e replica esse viés.

**Impacto atual:** risco regulatório silencioso — o viés pode crescer progressivamente sem ser detectado.

**O que fazer:**

Adicionar um passo de validação de fairness antes de qualquer aplicação de aprendizado:

```python
# Em learning_loop_service.py — antes de aplicar mudança aprendida
async def apply_learning(self, learning_batch: List[FeedbackItem]):
    # NOVO: validar fairness do batch antes de aplicar
    fairness_result = await self.fairness_guard.validate_learning_batch(learning_batch)
    if fairness_result.disparate_impact_detected:
        await self.audit_service.log_learning_blocked(fairness_result)
        return  # não aplica — entra em fila de revisão humana
    
    # continua com aplicação normal
    await self._apply_template_updates(learning_batch)
```

**Arquivos afetados:**
- [`app/shared/learning/learning_loop_service.py`](../lia-agent-system/app/shared/learning/learning_loop_service.py)
- [`app/shared/compliance/fairness_guard.py`](../lia-agent-system/app/shared/compliance/fairness_guard.py) — adicionar método `validate_learning_batch()`
- [`app/shared/compliance/audit_service.py`](../lia-agent-system/app/shared/compliance/audit_service.py) — adicionar evento `learning_blocked`

**Esforço:** 1 sprint
**Impacto esperado:** eliminação do risco de viés por aprendizado
**Métrica de sucesso:** 100% dos batches de aprendizado passam por validação de fairness (log auditável)

---

### F1-03 · Definir SLOs e modo degradado para o circuit breaker

**Problema diagnosticado:** O `circuit_breaker.py` não tem SLOs (Service Level Objectives) documentados — não está definido quantas falhas em quanto tempo abrem o circuito, por quanto tempo fica aberto, e o que acontece quando todos os LLMs falham simultaneamente.

**Impacto atual:** comportamento imprevisível em incidentes de provider; sem fallback de último recurso.

**O que fazer:**

Definir SLOs formais e criar um "modo degradado" com respostas pré-programadas:

```python
# Configuração de SLOs no circuit_breaker.py
CIRCUIT_BREAKER_CONFIG = {
    "failure_threshold": 5,        # abre após 5 falhas
    "time_window_seconds": 60,     # dentro de 60 segundos
    "recovery_timeout_seconds": 120,  # tenta reabrir após 2 min
    "half_open_max_calls": 2,      # testa com 2 calls antes de reabrir totalmente
}

# Modo degradado: respostas para as 10 perguntas mais frequentes
DEGRADED_MODE_RESPONSES = {
    "status_candidato": "Não consigo verificar o status agora. Tente novamente em alguns minutos.",
    "mover_candidato": "Sistema temporariamente indisponível. Ação registrada para execução assim que possível.",
    # ... top 10 intents
}
```

**Arquivos afetados:**
- [`app/shared/resilience/circuit_breaker.py`](../lia-agent-system/app/shared/resilience/circuit_breaker.py)
- [`app/shared/resilience/stats_manager.py`](../lia-agent-system/app/shared/resilience/stats_manager.py)
- [`app/api/v1/admin_circuit_breakers.py`](../lia-agent-system/app/api/v1/admin_circuit_breakers.py) — expor SLOs no painel admin

**Esforço:** 1 sprint
**Impacto esperado:** comportamento previsível em incidentes; zero downtime total mesmo com falha de todos os LLMs
**Métrica de sucesso:** MTTR (tempo médio de recuperação) de incidentes de LLM < 5 minutos

---

## Fase 2 — Ganhos Rápidos
### Semanas 3–6 | Alto impacto, baixo esforço

---

### F2-01 · Versionamento de prompts

**Problema diagnosticado:** Prompts sem versionamento significam que quando algo piora, não há como saber qual mudança causou — e não há como reverter.

**O que fazer:**

Adicionar campo `version`, `updated_at` e `changelog` em cada YAML de prompt, e implementar rollback no `prompt_registry.py`:

```yaml
# Exemplo: lia_persona.yaml com versionamento
metadata:
  version: "1.3.0"
  updated_at: "2026-03-19"
  author: "LIA Team"
  changelog:
    - "1.3.0: adicionado tom mais assertivo em contextos de negociação"
    - "1.2.0: ajustado limite de autonomia para decisões financeiras"
    - "1.1.0: versão inicial de produção"
```

Adicionar ao `prompt_registry.py`:
- `get_prompt(name, version=None)` — busca versão específica ou latest
- `rollback_prompt(name, to_version)` — reverte para versão anterior
- `list_prompt_history(name)` — lista todas as versões

**Arquivos afetados:**
- [`app/shared/prompts/prompt_registry.py`](../lia-agent-system/app/shared/prompts/prompt_registry.py)
- [`app/shared/prompts/loader.py`](../lia-agent-system/app/shared/prompts/loader.py)
- Todos os YAMLs em `app/prompts/` — adicionar bloco `metadata`

**Esforço:** 1 sprint
**Impacto esperado:** debugging de regressões de qualidade de 2 dias → 2 horas
**Métrica de sucesso:** toda mudança de prompt rastreável com autor, data e motivo

---

### F2-02 · Relatório de fairness exportável

**Problema diagnosticado:** O dashboard de bias audit existe mas é apenas interno. Clientes enterprise e reguladores (NYC LL144, EU AI Act) pedem relatório exportável na due diligence.

**O que fazer:**

Adicionar endpoint de exportação no `admin_bias_audit.py`:

```python
# GET /api/v1/admin/bias-audit/export?format=pdf&period=2026-Q1&tenant_id=...
async def export_bias_report(
    format: Literal["pdf", "csv", "json"],
    period: str,
    tenant_id: UUID
) -> FileResponse:
    report = await bias_audit_service.generate_report(tenant_id, period)
    # inclui: four_fifths_rule results, disparate impact by group,
    #          decisions audited, flags raised, actions taken
    return await export_service.render(report, format)
```

O relatório deve incluir obrigatoriamente:
- Taxa de aprovação por grupo demográfico (gênero, raça se disponível)
- Resultado da regra 4/5 por etapa do pipeline
- Número de decisões auditadas no período
- Flags levantadas e ações tomadas
- Assinatura digital com timestamp

**Arquivos afetados:**
- [`app/api/v1/admin_bias_audit.py`](../lia-agent-system/app/api/v1/admin_bias_audit.py)
- [`app/services/bias_audit_service.py`](../lia-agent-system/app/services/bias_audit_service.py)
- Novo: `app/services/report_export_service.py`

**Esforço:** 1 sprint
**Impacto esperado:** habilita contratos com clientes enterprise que exigem compliance documentado
**Métrica de sucesso:** relatório gerado em < 30 segundos para qualquer período

---

### F2-03 · Alertas de custo de tokens por tenant

**Problema diagnosticado:** Sem alertas proativos de custo, um tenant que começa a usar 10x mais tokens (por bug, abuso ou crescimento inesperado) não é detectado até a fatura chegar.

**O que fazer:**

Adicionar thresholds configuráveis com alertas automáticos no `tenant_budget.py`:

```python
# Em tenant_budget.py — adicionar política de alertas
class TenantBudgetPolicy:
    daily_token_limit: int          # limite diário configurável por plano
    alert_at_percent: float = 0.80  # alerta ao atingir 80%
    hard_limit_action: Literal["throttle", "block", "notify_only"]

# Job que roda a cada hora verificando consumo
async def check_tenant_budgets():
    for tenant in active_tenants:
        usage = await ai_consumption_service.get_daily_usage(tenant.id)
        if usage.percent >= tenant.policy.alert_at_percent:
            await alert_service.send(
                type="budget_warning",
                tenant=tenant,
                usage=usage
            )
```

**Arquivos afetados:**
- [`app/orchestrator/tenant_budget.py`](../lia-agent-system/app/orchestrator/tenant_budget.py)
- [`app/api/v1/ai_consumption.py`](../lia-agent-system/app/api/v1/ai_consumption.py)
- [`app/services/agent_health_alert_service.py`](../lia-agent-system/app/services/agent_health_alert_service.py)

**Esforço:** 1 sprint
**Impacto esperado:** zero surpresas de custo; possibilidade de modelo de pricing baseado em uso real
**Métrica de sucesso:** 100% dos tenants com limite configurado; alertas com latência < 1 hora

---

### F2-04 · Dead Letter Queue e monitoramento de jobs

**Problema diagnosticado:** Tasks Celery que falham repetidamente desaparecem silenciosamente — sem DLQ, não há visibilidade de jobs problemáticos.

**O que fazer:**

Configurar DLQ no Celery e adicionar endpoint de monitoramento:

```python
# Em celery_tasks.py — adicionar DLQ
@app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 min entre retries
    acks_late=True,
    reject_on_worker_lost=True,
)
def process_drift_check(self, tenant_id: str):
    try:
        drift_service.run_check(tenant_id)
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            # move para DLQ com contexto completo
            dead_letter_queue.push({
                "task": self.name,
                "args": self.request.args,
                "error": str(exc),
                "failed_at": datetime.utcnow().isoformat(),
                "tenant_id": tenant_id,
            })
        raise self.retry(exc=exc)
```

Adicionar `GET /api/v1/admin/jobs/dead-letter` para revisão de tasks falhas.

**Arquivos afetados:**
- [`app/jobs/celery_tasks.py`](../lia-agent-system/app/jobs/celery_tasks.py)
- [`app/jobs/drift_job.py`](../lia-agent-system/app/jobs/drift_job.py)
- [`app/api/v1/admin.py`](../lia-agent-system/app/api/v1/admin.py) — novo endpoint DLQ

**Esforço:** 1 sprint
**Impacto esperado:** visibilidade total de jobs falhos; zero perda silenciosa de tasks críticas
**Métrica de sucesso:** 100% das falhas de job registradas na DLQ e visíveis no painel admin

---

### F2-05 · Ajuste do threshold de cache semântico

**Problema diagnosticado:** O threshold de cosine similarity de 0.92 para cache semântico pode ser alto demais — perguntas levemente reformuladas sempre vão para o LLM, desperdiçando o benefício do cache.

**O que fazer:**

Usar o A/B testing já existente para testar diferentes thresholds:

```python
# Em semantic_cache.py — threshold configurável por A/B test
SEMANTIC_CACHE_THRESHOLD = ab_testing_service.get_variant(
    experiment="semantic_cache_threshold",
    variants={
        "control": 0.92,    # threshold atual
        "variant_a": 0.88,  # mais permissivo
        "variant_b": 0.85,  # ainda mais permissivo
    }
)
```

Medir por 2 semanas: taxa de cache hit, taxa de resposta incorreta por threshold, custo total de tokens.

**Arquivos afetados:**
- [`app/orchestrator/semantic_cache.py`](../lia-agent-system/app/orchestrator/semantic_cache.py)
- [`app/shared/learning/ab_testing_service.py`](../lia-agent-system/app/shared/learning/ab_testing_service.py)

**Esforço:** 3 dias (configuração do experimento) + 2 semanas (coleta de dados)
**Impacto esperado:** cache hit rate ↑ estimado 15–30%; custo de tokens ↓ proporcional
**Métrica de sucesso:** cache hit rate > 40% sem aumento de taxa de erros

---

## Fase 3 — Melhorias Estruturais
### Meses 2–4 | Refatorações que aumentam qualidade e manutenibilidade a longo prazo

---

### F3-01 · HITL (Human-in-the-Loop) nos grafos LangGraph

**Problema diagnosticado:** Os grafos WSI Interview e Interview Scheduling não têm pontos de pausa para aprovação humana antes de etapas críticas — o agente avança automaticamente mesmo em decisões de alto impacto.

**O que fazer:**

Adicionar nós de HITL usando o suporte nativo do LangGraph:

```python
# Em wsi_interview_graph.py — adicionar nó de aprovação humana
from langgraph.checkpoint.postgres import PostgresSaver

# Nó HITL antes de finalizar score WSI
def human_review_node(state: WSIState):
    """Pausa o grafo e aguarda aprovação do recrutador."""
    return Command(
        goto="__interrupt__",  # pausa a execução
        update={
            "pending_review": {
                "type": "wsi_score_review",
                "candidate_id": state["candidate_id"],
                "preliminary_score": state["wsi_score"],
                "interviewer_notes": state["notes"],
            }
        }
    )

# Retoma quando recrutador aprova via API
# POST /api/v1/agent/resume/{thread_id}
```

**Arquivos afetados:**
- [`app/domains/cv_screening/agents/wsi_interview_graph.py`](../lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py)
- [`app/domains/interview_scheduling/agents/interview_graph.py`](../lia-agent-system/app/domains/interview_scheduling/agents/interview_graph.py)
- [`app/shared/agents/checkpointer.py`](../lia-agent-system/app/shared/agents/checkpointer.py) — migrar para PostgresSaver
- Novo: `app/api/v1/agent_continuity.py` — endpoints resume/reject

**Esforço:** 2 sprints
**Impacto esperado:** conformidade com EU AI Act (humano sempre no loop para decisões de alto risco); confiança do recrutador ↑
**Métrica de sucesso:** 100% das decisões de score WSI revisáveis por humano antes de persistir

---

### F3-02 · TTL e compressão da memória de longo prazo

**Problema diagnosticado:** A `LongTermMemory` armazena episódios indefinidamente — para tenants ativos há 12+ meses, o volume de dados pode impactar a performance de busca e o custo de contexto.

**O que fazer:**

Implementar compressão semântica de memórias antigas:

```python
# Em long_term_memory.py — adicionar compressão mensal
async def compress_old_memories(self, tenant_id: UUID, older_than_days: int = 30):
    """Sumariza episódios antigos em memórias condensadas."""
    old_episodes = await self.get_episodes(
        tenant_id=tenant_id,
        older_than=datetime.utcnow() - timedelta(days=older_than_days),
        compressed=False
    )
    if len(old_episodes) > 10:
        # usa LLM para condensar N episódios em 1 resumo
        summary = await self.llm.summarize(
            episodes=old_episodes,
            prompt="Condense estes episódios em um resumo de no máximo 200 palavras..."
        )
        await self.store_compressed_memory(tenant_id, summary, old_episodes)
        await self.mark_episodes_compressed(old_episodes)
```

Adicionar política de TTL por tipo de memória:
- Memória de triagem: 90 dias (dado regulatório)
- Memória de preferência de recrutador: 180 dias
- Memória de candidato: permanente (direito ao acesso LGPD)

**Arquivos afetados:**
- [`app/shared/agents/long_term_memory.py`](../lia-agent-system/app/shared/agents/long_term_memory.py)
- [`app/jobs/celery_tasks.py`](../lia-agent-system/app/jobs/celery_tasks.py) — adicionar job mensal de compressão
- [`app/services/lgpd_cleanup_service.py`](../lia-agent-system/app/services/lgpd_cleanup_service.py) — integrar TTL com LGPD

**Esforço:** 2 sprints
**Impacto esperado:** custo de contexto ↓ ~40% para tenants maduros; latência de busca em memória ↓
**Métrica de sucesso:** p95 de latência de busca em memória < 100ms independente do tamanho do histórico

---

### F3-03 · Consolidação da estrutura de serviços

**Problema diagnosticado:** `app/services/` tem 244 arquivos planos sem subcategorização, misturando serviços de IA, negócio, integração e notificação. Isso causa duplicação de serviços e dificulta onboarding.

**O que fazer:**

Reorganizar `app/services/` com subcategorias explícitas:

```
app/services/
├── ai/                   ← serviços de IA/ML (scoring, embedding, drift, RAGAS)
│   ├── cv_scoring_service.py
│   ├── embedding_service.py
│   ├── model_drift_service.py
│   ├── ragas_evaluation_service.py
│   └── ...
├── integrations/         ← clientes externos (ATS, email, calendar, voz)
│   ├── ats_clients/
│   ├── email_providers/
│   ├── google_calendar_client.py
│   └── ...
├── compliance/           ← LGPD, consentimento, DSR, auditoria
│   ├── lgpd_compliance.py
│   ├── consent_checker_service.py
│   ├── dsr_export_service.py
│   └── ...
├── notifications/        ← alertas, emails, WhatsApp, push
│   ├── email_service.py
│   ├── notification_service.py
│   └── ...
├── analytics/            ← métricas, reports, benchmarks
│   ├── market_benchmark_service.py
│   ├── pipeline_prediction_service.py
│   └── ...
└── core/                 ← serviços de negócio centrais (candidatos, vagas, pipeline)
    ├── candidate_enrichment_service.py
    ├── job_vacancy_service.py
    └── ...
```

Fazer a migração gradualmente por categoria, sem quebrar imports existentes (usar `__init__.py` com re-exports).

**Arquivos afetados:** todos os 244 arquivos em `app/services/` (renomeação de pasta, sem alteração de lógica)

**Esforço:** 3 sprints (feito gradualmente, categoria por categoria)
**Impacto esperado:** onboarding de novos devs 50% mais rápido; eliminação de serviços duplicados
**Métrica de sucesso:** zero arquivos diretamente em `app/services/` (todos em subcategorias)

---

### F3-04 · OpenTelemetry (OTEL) como camada de observabilidade

**Problema diagnosticado:** Sem OTEL, não é possível integrar com Datadog, Grafana ou New Relic sem customização. LangSmith é excelente para traces de LLM mas não cobre métricas de infra.

**O que fazer:**

Adicionar OTEL como camada de exportação complementar ao LangSmith:

```python
# Em app/observability/ — novo módulo OTEL
from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Instrumentar automaticamente FastAPI, SQLAlchemy, Redis, Celery
# Exportar para Grafana Cloud (gratuito até 50GB/mês) ou Datadog

# Métricas customizadas de IA:
llm_latency = metrics.create_histogram("lia.llm.latency_ms")
llm_tokens = metrics.create_counter("lia.llm.tokens_used")
agent_errors = metrics.create_counter("lia.agent.errors")
cache_hits = metrics.create_counter("lia.cache.hits")
fairness_blocks = metrics.create_counter("lia.fairness.blocks")
```

**Arquivos afetados:**
- Novo: `app/shared/observability/otel.py`
- [`app/main.py`](../lia-agent-system/app/main.py) — inicializar OTEL na startup
- [`app/shared/agents/observability.py`](../lia-agent-system/app/shared/agents/observability.py) — emitir spans OTEL

**Esforço:** 2 sprints
**Impacto esperado:** visibilidade completa de infra + IA em uma ferramenta; SLAs mensuráveis para clientes
**Métrica de sucesso:** p95 de latência de API monitorado em tempo real; dashboard com 10 KPIs de IA

---

### F3-05 · Consolidar agentes duplicados de policy

**Problema diagnosticado:** Existem dois agentes de política (`hiring_policy/agents/policy_react_agent.py` e `policy/agents/agent.py`) que provavelmente surgiram em momentos diferentes e têm responsabilidades sobrepostas.

**O que fazer:**

Auditar os dois agentes, identificar diferenças reais, e consolidar em um único com as capacidades de ambos. Manter o mais completo como canônico e fazer o outro virar um alias ou ser removido.

**Arquivos afetados:**
- [`app/domains/hiring_policy/agents/policy_react_agent.py`](../lia-agent-system/app/domains/hiring_policy/agents/policy_react_agent.py)
- [`app/domains/policy/agents/agent.py`](../lia-agent-system/app/domains/policy/agents/agent.py)
- [`app/orchestrator/cascaded_router.py`](../lia-agent-system/app/orchestrator/cascaded_router.py) — unificar roteamento

**Esforço:** 1 sprint
**Impacto esperado:** redução de superfície de código a manter; comportamento consistente de políticas
**Métrica de sucesso:** zero requisições roteadas para o agente deprecado

---

## Fase 4 — Evolução Estratégica
### Meses 4–9 | Capacidades que abrem novos mercados ou diferenciais competitivos

---

### F4-01 · DeepEval no pipeline de CI/CD

**Problema diagnosticado:** 301 arquivos de teste mas sem avaliação automática de qualidade de LLM. Mudanças em prompts ou modelos podem degradar qualidade silenciosamente.

**O que fazer:**

Integrar DeepEval como framework de avaliação de LLM com rodada semanal automatizada:

```python
# tests/llm_quality/test_agent_quality.py
from deepeval import evaluate
from deepeval.metrics import (
    HallucinationMetric,
    FaithfulnessMetric,
    BiasMetric,
    ToxicityMetric,
    AnswerRelevancyMetric,
)
from deepeval.test_case import LLMTestCase

# Testar com golden_dataset.py existente
@pytest.mark.llm_quality  # roda separado dos testes unitários
async def test_cv_screening_quality():
    test_cases = await golden_dataset.get_screening_cases()
    results = evaluate(
        test_cases=test_cases,
        metrics=[
            HallucinationMetric(threshold=0.1),   # < 10% de alucinação
            BiasMetric(threshold=0.05),             # < 5% de viés detectado
            AnswerRelevancyMetric(threshold=0.85),  # > 85% relevância
        ]
    )
    assert results.is_passing
```

Pipeline CI/CD:
- A cada commit: testes unitários (rápidos, sem LLM)
- Semanalmente: testes de qualidade de LLM (DeepEval com LLM real)
- A cada mudança de prompt: testes de regressão de qualidade

**Arquivos afetados:**
- Novo: `tests/llm_quality/` — diretório de testes de qualidade
- [`app/tests/golden_dataset.py`](../lia-agent-system/app/tests/golden_dataset.py) — expandir dataset
- CI/CD pipeline — adicionar job semanal

**Esforço:** 2 sprints
**Impacto esperado:** regressões de qualidade detectadas antes de produção; confiança em mudanças de prompt ↑
**Métrica de sucesso:** zero regressões de qualidade em produção não detectadas pelo CI

---

### F4-02 · Compressão de PII com Microsoft Presidio

**Problema diagnosticado:** O `pii_masking.py` atual usa regex para detectar PII — não detecta PII em texto livre de currículos em português (nomes compostos, cidades, endereços sem padrão fixo).

**O que fazer:**

Substituir o regex por Microsoft Presidio com modelos de NER em português:

```python
# Em shared/pii_masking.py — substituir regex por Presidio
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

async def mask_pii(text: str, language: str = "pt") -> MaskedText:
    """Detecta e mascara PII usando NER — muito mais preciso que regex."""
    results = analyzer.analyze(
        text=text,
        language=language,
        entities=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CPF",
                  "LOCATION", "DATE_TIME", "NRP"]  # NRP = National Registration Profile
    )
    anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
    return MaskedText(
        original=text,
        masked=anonymized.text,
        entities_found=[(r.entity_type, r.score) for r in results]
    )
```

**Arquivos afetados:**
- [`app/shared/pii_masking.py`](../lia-agent-system/app/shared/pii_masking.py)
- `requirements.txt` — adicionar `presidio-analyzer`, `presidio-anonymizer`

**Esforço:** 2 sprints (incluindo testes com currículos reais em português)
**Impacto esperado:** cobertura de detecção de PII de ~60% (regex) para ~92% (NER)
**Métrica de sucesso:** taxa de PII não detectado < 5% em amostra de 500 currículos reais

---

### F4-03 · Sourcing externo com catálogo de APIs (inspirado no v5)

**Problema diagnosticado:** O principal ponto onde o v5 supera a LIA é no sourcing externo — 51 APIs YAML com 9 subagentes especializados vs. o agente único de sourcing da LIA com acesso limitado.

**O que fazer:**

Adaptar o padrão do v5 para o SourcingReactAgent da LIA, mantendo a arquitetura existente:

```
Expansão do sourcing da LIA:

SourcingReactAgent (atual, 17 tools)
  ↓ adicionar
SourcingPlannerAgent  → seleciona quais fontes consultar (inspirado no APIPlannerAgent do v5)
SourcingExecutorAgent → executa buscas em paralelo nas APIs selecionadas
  ↓ APIs a adicionar (gradualmente):
  ├── LinkedIn (via Apify — já integrado parcialmente)
  ├── GitHub (candidatos tech)
  ├── Hunter.io (email discovery)
  ├── Clearbit (enrichment)
  └── [outras conforme roadmap]
```

O catálogo de APIs pode ser em YAML (padrão do v5) ou diretamente via Apify MCP (já integrado na LIA).

**Arquivos afetados:**
- [`app/domains/sourcing/agents/sourcing_react_agent.py`](../lia-agent-system/app/domains/sourcing/agents/sourcing_react_agent.py)
- [`app/domains/sourcing/agents/sourcing_tool_registry.py`](../lia-agent-system/app/domains/sourcing/agents/sourcing_tool_registry.py)
- [`app/services/apify_service.py`](../lia-agent-system/app/services/apify_service.py) — expandir cobertura

**Esforço:** 3–4 sprints (por fase de APIs adicionadas)
**Impacto esperado:** sourcing externo da LIA equiparável ao v5; fechamento do principal gap competitivo
**Métrica de sucesso:** sourcing LIA cobre ao menos 10 fontes externas com FairnessGuard aplicado

---

### F4-04 · Perfis de comportamento por recrutador

**Problema diagnosticado:** Todos os recrutadores recebem o mesmo comportamento de agente — sem adaptação ao nível de experiência (júnior vs sênior), especialização (tech vs. comercial) ou preferências aprendidas.

**O que fazer:**

Criar um sistema de "recruiter profiles" que adapta o comportamento dos agentes:

```python
# Novo: app/shared/agents/recruiter_profile.py
class RecruiterProfile:
    experience_level: Literal["junior", "mid", "senior"]
    specialization: List[str]  # ["tech", "commercial", "executive"]
    preferred_verbosity: Literal["concise", "detailed"]
    learned_shortcuts: Dict[str, str]  # atalhos aprendidos pelo uso
    decision_history: List[DecisionPattern]  # padrões de decisão históricos

# Injetado em cada agente como contexto adicional
class KanbanReactAgent(LangGraphReactBase):
    async def process(self, message: str, recruiter_profile: RecruiterProfile):
        # adapta system prompt baseado no perfil
        system_prompt = self.prompt_loader.load(
            "kanban_system_prompt",
            context={"profile": recruiter_profile}
        )
```

**Arquivos afetados:**
- Novo: `app/shared/agents/recruiter_profile.py`
- [`app/shared/agents/langgraph_react_base.py`](../lia-agent-system/app/shared/agents/langgraph_react_base.py) — injetar profile
- [`app/shared/agents/long_term_memory.py`](../lia-agent-system/app/shared/agents/long_term_memory.py) — persistir profile
- Todos os system prompts — adicionar suporte a variáveis de profile

**Esforço:** 3 sprints
**Impacto esperado:** experiência personalizada por recrutador; NPS ↑; curva de aprendizado ↓
**Métrica de sucesso:** recrutadores seniores recebem respostas 40% mais concisas que júniores sem perda de qualidade

---

## Roadmap Visual

```
SEMANA 1-2    │ F1-01 Decompor agentes (23/22 tools)
(Urgente)     │ F1-02 Fairness no learning loop
              │ F1-03 SLOs e modo degradado do circuit breaker
              │
SEMANA 3-6    │ F2-01 Versionamento de prompts
(Ganhos       │ F2-02 Relatório de fairness exportável
 Rápidos)     │ F2-03 Alertas de custo por tenant
              │ F2-04 Dead Letter Queue para jobs
              │ F2-05 Ajuste de threshold semântico (A/B test)
              │
MÊS 2-4       │ F3-01 HITL nos grafos LangGraph
(Estrutural)  │ F3-02 TTL e compressão da memória longa
              │ F3-03 Consolidação de pastas de serviços
              │ F3-04 OpenTelemetry como camada de observabilidade
              │ F3-05 Consolidar agentes de policy duplicados
              │
MÊS 4-9       │ F4-01 DeepEval no CI/CD
(Estratégico) │ F4-02 Microsoft Presidio para PII
              │ F4-03 Sourcing externo expandido (inspirado v5)
              │ F4-04 Perfis de comportamento por recrutador
```

---

## Impacto Consolidado Esperado

| Dimensão | Score Atual | Score Pós-Plano | Principais Mudanças |
|---|---|---|---|
| **Orquestração** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Threshold semântico ajustado (F2-05) |
| **Tool Registries** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Decomposição Kanban + Pipeline (F1-01) |
| **Fairness** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐+ | Relatório exportável + loop validado (F1-02, F2-02) |
| **Prompts** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Versionamento completo (F2-01) |
| **Resiliência** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | SLOs formais + modo degradado (F1-03) |
| **Memória** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | TTL + compressão (F3-02) |
| **Observabilidade** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | OTEL + alertas de custo (F3-04, F2-03) |
| **Testes** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | DeepEval no CI (F4-01) |
| **PII/LGPD** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐+ | Presidio NER (F4-02) |
| **Sourcing** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | APIs expandidas (F4-03) |
| **Estrutura** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Consolidação de serviços + policy (F3-03, F3-05) |
| **Experiência** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Perfis por recrutador (F4-04) |

---

*Plano de Otimização LIA — versão 1.0 — 19/03/2026*
*17 itens distribuídos em 4 fases | Esforço total estimado: ~25 sprints (1 sprint = 1 semana)*

---

---

# Seção 20 — Diagnóstico Estratégico: O que a LIA deve fazer agora

> **Contexto:** Esta seção consolida o diagnóstico gerado a partir da análise comparativa LIA vs. v5, com foco exclusivo em otimizações executáveis dentro da plataforma LIA. O v5 permanece em ambiente separado e não será alterado. As recomendações abaixo derivam do cruzamento entre: (a) o diagnóstico comparativo das 19 seções anteriores, (b) melhores práticas de mercado referenciadas, e (c) análise de prioridade por impacto/esforço.
>
> **Data:** 19/03/2026 | **Versão:** 1.0

---

## 20.1 · Pergunta Central Respondida

> **Vale ajustar a LIA para ficar igual à v5?**

**Não globalmente — mas sim em 3 padrões arquiteturais específicos.**

A v5 é um MVP de pesquisa. A LIA é um produto de produção. São categorias incomparáveis em escopo. Puxar a v5 para dentro da LIA de forma ampla regride a plataforma. Contudo, existem 3 padrões estruturais do v5 genuinamente superiores para os casos de uso onde se aplicam — e devem ser adotados cirurgicamente.

---

## 20.2 · O que adotar da v5 na LIA (3 padrões)

### Padrão A — Decomposição de subagentes para sourcing

O v5 implementa `planner → orchestrator → [search, detail, analytics, comparison, report, action]` em paralelo. A LIA tem um `SourcingReActAgent` único com 17 tools.

**O problema concreto:** com 17 tools, o modelo toma decisões subótimas quando há ambiguidade entre ferramentas similares (ex: `search_external` vs `enrich_profile` vs `invite_to_apply`). O Anthropic documenta que acima de 10–12 tools o raciocínio de seleção de ferramenta degrada.

**Arquitetura proposta para a LIA:**

```
SourcingReActAgent (atual, 17 tools)
    ↓ decompor em
SourcingPlannerAgent     → route_to_specialist (1 tool: roteamento)
    ├── SourcingSearchAgent      → search_external, filter_by_requirements, rank_profiles (4–5 tools)
    ├── SourcingEnrichAgent      → enrich_profile, fetch_linkedin, fetch_pearch (4 tools)
    └── SourcingEngagementAgent  → invite_to_apply, send_outreach, follow_up (4–5 tools)
```

**Arquivos afetados:**
- `app/domains/sourcing/agents/sourcing_react_agent.py` — refatorar para SourcingPlannerAgent
- `app/domains/sourcing/agents/sourcing_tool_registry.py` — dividir em 3 registries
- `app/domains/sourcing/agents/` — criar `sourcing_search_agent.py`, `sourcing_enrich_agent.py`, `sourcing_engagement_agent.py`

**Esforço:** 2 sprints | **Impacto:** qualidade de sourcing ↑, custo por query ↓ ~30%

---

### Padrão B — Decomposição do Kanban e Pipeline Transition (CRÍTICA)

Este é o item com maior impacto imediato em qualidade. 23 tools no Kanban e 22 no Pipeline estão acima do limite seguro da Anthropic. Esses são os agentes mais usados em produção — qualidade ruim aqui impacta o recrutador diariamente.

**Arquitetura proposta:**

```
KanbanReActAgent (23 tools) → decompor em:
  KanbanSearchAgent     → search_candidates, filter_stage, get_by_criteria, sort_by_score (5 tools)
  KanbanActionAgent     → move_candidate, bulk_move, add_to_short_list, add_note, archive (6 tools)
  KanbanInsightAgent    → get_metrics, funnel_view, time_in_stage, diversity_snapshot (5 tools)

PipelineTransitionAgent (22 tools) → decompor em:
  PipelineDecisionAgent → evaluate_stage_fit, check_requirements, request_docs, check_consent (6 tools)
  PipelineActionAgent   → move_candidate, add_note, schedule_interview, reject_with_feedback (6 tools)
  PipelineNotifyAgent   → notify_candidate, notify_recruiter, trigger_automation, send_gate_feedback (5 tools)
```

**Arquivos afetados:**
- `app/domains/recruiter_assistant/agents/kanban_react_agent.py`
- `app/domains/recruiter_assistant/agents/kanban_tool_registry.py`
- `app/domains/pipeline/agents/pipeline_transition_agent.py`
- `app/domains/pipeline/agents/pipeline_tool_registry.py`

**Esforço:** 2 sprints | **Impacto:** qualidade de resposta dos agentes mais críticos ↑ significativamente

---

### Padrão C — Catálogo YAML de APIs externas de sourcing

O v5 tem 51 APIs documentadas em YAML que o APIPlannerAgent lê dinamicamente. A LIA tem ATS clients hard-coded. Para integrações de sourcing externo, o padrão YAML é superior porque:

- Adicionar nova API = criar YAML, sem alterar código Python
- Auditável por pessoas não-técnicas (RH Ops)
- Compatível com o `tool_registry_metadata.yaml` que a LIA já implementou (Sprint G5)

**O que fazer:** criar `docs/integrations/apis/sourcing/` com YAMLs para cada fonte externa (Pearch, Apify, futuras APIs de jobboards). O SourcingPlannerAgent usa esse catálogo como contexto para decidir quais fontes consultar.

**Esforço:** 1 sprint | **Impacto:** sourcing externo escalável sem intervenção de engenharia

---

## 20.3 · O que a LIA tem e DEVE manter (não simplificar)

Estes são os diferenciais reais de produto da LIA frente ao mercado. Qualquer tentativa de simplificá-los para "ficar mais parecido com o v5" é um erro estratégico:

| Componente | Por que é diferencial competitivo | Risco se remover |
|---|---|---|
| **FairnessGuard 3 camadas (obrigatória)** | HireVue foi multado por não ter isso. NYC LL144 + EU AI Act exigem | Risco regulatório máximo |
| **WorkingMemory + LongTermMemory** | Nenhum ATS do mercado médio tem. A LIA "lembra" — experiência de produto superior | Regressão de produto |
| **Learning Loop com A/B testing** | 57% dos produtos de IA em produção não têm (Gartner 2025) | Perde capacidade de melhoria autônoma |
| **Circuit Breaker + LLM Cascade** | Resiliência enterprise — Haiku→Sonnet→Opus→Gemini→GPT | Sistema para se Claude/OpenAI ficarem fora |
| **Consentimento granular LGPD** | LGPD art. 7 exige granular. Maioria usa consentimento genérico | Risco jurídico direto |
| **Drift detection diário** | Sem isso, o modelo degrada silenciosamente sem ninguém perceber | Qualidade se deteriora invisível |
| **Event Store imutável** | Base para auditoria SOX + direito ao apagamento LGPD | Perde rastreabilidade |
| **Anti-sycophancy em todos os prompts** | Raríssimo no mercado. Impede que o sistema concorde com viés do recrutador | Volta a comportamento sycophantic |

---

## 20.4 · Débito técnico identificado — priorizado por impacto/esforço

### Prioridade 1 — Decomposição dos agentes com excesso de tools
**(Kanban 23, Pipeline 22, Sourcing 17) — fazer nas próximas 2 sprints**

Coberto nos Padrões A e B acima e no item F1-01 da Fase 1 deste documento.

---

### Prioridade 2 — Fairness no learning loop (CRÍTICO — risco regulatório)

Atualmente o learning loop aprende com feedback de recrutadores sem validação de viés. Se recrutadores têm viés sistemático, o sistema aprende e amplifica esse viés silenciosamente.

**Solução:**

```python
# app/shared/learning/learning_loop_service.py
async def apply_learning(feedback_batch: List[FeedbackSignal]) -> ApplyResult:
    new_behavior = compute_adjustments(feedback_batch)

    # VALIDAÇÃO DE FAIRNESS ANTES DE APLICAR
    fairness_check = await fairness_guard.evaluate_behavior_change(
        current=current_behavior,
        proposed=new_behavior,
        dimensions=["gender", "age_group", "disability", "region"]
    )

    if fairness_check.has_disparate_impact:
        await audit_service.log_decision(
            decision_type="learning_blocked",
            reason=fairness_check.violations,
            proposed_change=new_behavior
        )
        return ApplyResult(applied=False, reason="fairness_violation")

    # snapshot antes de aplicar (permite rollback)
    await snapshot_service.save(tag=f"pre_learning_{datetime.utcnow().isoformat()}")
    await template_learning_service.apply(new_behavior)
    return ApplyResult(applied=True)
```

**Arquivos afetados:**
- `app/shared/learning/learning_loop_service.py` — adicionar validação
- `app/shared/compliance/fairness_guard.py` — adicionar `evaluate_behavior_change()`
- Novo: `app/shared/learning/learning_snapshot_service.py` — snapshots para rollback

**Esforço:** 1 sprint | **Impacto:** risco regulatório ↓ significativamente; aprendizado não degrada fairness

---

### Prioridade 3 — Versionamento de prompts

Atualmente mudanças de prompt são invisíveis: não há como saber qual versão estava ativa em uma data específica, impossibilitando debugging de regressões de qualidade.

**Solução imediata (zero custo, 1 sprint):** padronizar campos `version` e `updated_at` em todos os YAMLs de prompt:

```yaml
# app/prompts/domains/kanban_system_prompt.yaml
version: "1.3.0"
updated_at: "2026-03-19"
updated_by: "sprint-z3"
changelog: "Adicionado contexto de perfil do recrutador"
prompt: |
  Você é um assistente especializado em gestão de pipeline de candidatos...
```

**Solução robusta (Langfuse self-hosted, 2 sprints):** plataforma open-source de gerenciamento de prompts com versionamento automático, diff entre versões, A/B testing de variantes e métricas de qualidade por versão. Já tem integração nativa com LangSmith (que a LIA usa).

**Arquivos afetados:**
- Todos os arquivos em `app/prompts/` — adicionar campos de metadados
- `app/shared/prompts/loader.py` — registrar versão ativa no LangSmith ao carregar

**Esforço:** 1 sprint (básico) / 2 sprints (Langfuse) | **Impacto:** debugging de regressões possível; mudanças de prompt rastreáveis

---

### Prioridade 4 — Relatório de fairness exportável

O `bias_audit_service.py` já calcula tudo (Four-Fifths Rule em 4 dimensões). Falta apenas gerar o relatório em formato que auditores externos possam consumir.

**Solução:**

```python
# app/api/v1/bias_audit.py — novo endpoint
@router.get("/bias-audit/job/{job_id}/export")
async def export_bias_audit_report(
    job_id: str,
    format: Literal["pdf", "csv", "json"] = "pdf",
    company_id: str = Header(..., alias="X-Company-ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Gera relatório exportável de auditoria de fairness.
    Formato compatível com NYC Local Law 144 e EU AI Act.
    """
    audit_data = await bias_audit_service.get_full_audit(job_id, company_id, db)
    snapshot_history = await bias_audit_service.get_snapshot_history(job_id, db)
    return await report_generator.generate(
        audit_data, snapshot_history, format=format,
        include_sections=["four_fifths_rule", "disparate_impact", "eeoc_compliance",
                          "dimension_breakdown", "historical_trend", "methodology"]
    )
```

**Arquivos afetados:**
- `app/api/v1/bias_audit.py` — novo endpoint `/export`
- Novo: `app/services/bias_audit_report_generator.py` — gerador PDF/CSV
- `src/app/api/backend-proxy/bias-audit/[job_id]/export/route.ts` — proxy FE

**Esforço:** 1 sprint | **Impacto comercial direto:** requisito em contratos enterprise e licitações públicas

---

### Prioridade 5 — DeepEval no CI/CD

301 testes mas sem validação de qualidade de LLM. O pipeline testa se o código executa — não se o agente responde bem. DeepEval adiciona métricas de qualidade de IA diretamente no CI.

**Métricas mínimas para adicionar:**

```python
# tests/llm_quality/test_agents_quality.py
import pytest
from deepeval import evaluate
from deepeval.metrics import HallucinationMetric, FaithfulnessMetric, BiasMetric

@pytest.mark.llm_quality
class TestAgentQuality:

    def test_kanban_no_hallucination(self, kanban_test_cases):
        metric = HallucinationMetric(threshold=0.1)  # máximo 10% de alucinação
        evaluate(test_cases=kanban_test_cases, metrics=[metric])

    def test_wsi_faithfulness(self, wsi_test_cases):
        # respostas do WSI devem ser fiéis ao conteúdo do CV
        metric = FaithfulnessMetric(threshold=0.85)
        evaluate(test_cases=wsi_test_cases, metrics=[metric])

    def test_pipeline_no_bias(self, pipeline_test_cases):
        metric = BiasMetric(threshold=0.05)
        evaluate(test_cases=pipeline_test_cases, metrics=[metric])
```

**Pipeline CI (`.github/workflows/ci.yml`):** adicionar job `llm-quality-tests` com schedule semanal (não a cada commit — controle de custo) e threshold de falha configurável.

**Esforço:** 2 sprints | **Impacto:** qualidade de resposta dos agentes monitorada automaticamente; regressões detectadas antes de chegarem a produção

---

## 20.5 · O que NÃO fazer (armadilhas identificadas)

| Tentação | Por que é errada | Alternativa correta |
|---|---|---|
| Tornar a LIA stateless "para simplificar" | A memória é diferencial de produto — candidatos e recrutadores esperam que o sistema lembre | Manter WorkingMemory + LongTermMemory; adicionar TTL e compressão (F3-02) |
| Reduzir FairnessGuard para 1 camada | As 3 camadas são o que garante compliance regulatório proativo vs. reativo | Manter 3 camadas; adicionar relatório exportável (Prioridade 4) |
| Colapsar os 12 domínios em menos agentes | A separação garante system prompts especializados e tool sets enxutos | Manter domínios; decompor agentes *dentro* dos domínios que têm excess de tools |
| Migrar llm_factory.py para LiteLLM agora | Risco de regressão alto; LiteLLM é ganho marginal dado que factory já funciona | Avaliar LiteLLM após Sprint Z4, quando as prioridades 1–5 estiverem resolvidas |
| Simplificar o cascade de 6 tiers | Cada tier tem função específica; remover um cria buraco de cobertura | Ajustar threshold semântico (F2-05) sem remover tiers |

---

## 20.6 · Plano de Execução — Sprints Z1–Z4

Estas sprints complementam e refinam o roadmap F1–F4 já definido neste documento, com foco na sequência de execução otimizada:

```
Sprint Z1 (Semanas 1–2) — Agentes Críticos
──────────────────────────────────────────
Z1-01  Decomposição KanbanReActAgent (23 → 3 subagentes)
       KanbanSearchAgent + KanbanActionAgent + KanbanInsightAgent
Z1-02  Decomposição PipelineTransitionAgent (22 → 3 subagentes)
       PipelineDecisionAgent + PipelineActionAgent + PipelineNotifyAgent
Z1-03  Testes de regressão: validar que decomposição não quebra comportamentos existentes

Sprint Z2 (Semanas 3–4) — Fairness e Qualidade
───────────────────────────────────────────────
Z2-01  Fairness no learning loop + snapshots para rollback
Z2-02  Decomposição SourcingReActAgent (17 → 3 subagentes, padrão v5)
       SourcingPlannerAgent + SourcingSearchAgent + SourcingEnrichAgent + SourcingEngagementAgent
Z2-03  Catálogo YAML de APIs externas de sourcing (docs/integrations/apis/sourcing/)

Sprint Z3 (Semanas 5–6) — Compliance e Visibilidade
────────────────────────────────────────────────────
Z3-01  Relatório de fairness exportável (PDF/CSV) — endpoint + gerador + proxy FE
Z3-02  Versionamento de prompts: campos version/updated_at em todos os YAMLs + loader
Z3-03  Alertas de custo por tenant (complementa F2-03)

Sprint Z4 (Semanas 7–8) — Robustez
───────────────────────────────────
Z4-01  DeepEval integrado no CI/CD (3 métricas: hallucination, faithfulness, bias)
Z4-02  TTL + compressão na LongTermMemory (episódios >30 dias → resumo via LLM)
Z4-03  SLOs formais para circuit breaker + modo degradado (complementa F1-03)
```

---

## 20.7 · Scorecard Atualizado — Antes e Depois das Sprints Z1–Z4

| Dimensão | Score Antes | Score Após Z1–Z4 | O que muda |
|---|---|---|---|
| **Tool Registries / Agentes** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Kanban + Pipeline + Sourcing decompostos (Z1, Z2) |
| **Fairness** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐+ | Loop validado + relatório exportável (Z2, Z3) |
| **Sourcing** | ⭐⭐⭐ | ⭐⭐⭐⭐ | Subagentes especializados + catálogo YAML (Z2) |
| **Prompts** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Versionamento rastreável (Z3) |
| **Testes de IA** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | DeepEval com métricas de qualidade de LLM (Z4) |
| **Memória** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | TTL + compressão reduz custo DB (Z4) |
| **Resiliência** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | SLOs formais + modo degradado documentado (Z4) |
| **Compliance comercial** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Relatório exportável para due diligence enterprise (Z3) |

---

## 20.8 · Síntese Estratégica

A LIA está arquiteturalmente à frente do v5 em praticamente todas as dimensões que importam para produção: multi-tenancy, fairness obrigatória, memória persistente, learning loop, resiliência, LGPD. **O v5 tem superioridade em exatamente um ponto: a decomposição de subagentes especializados para tarefas de alta paralelismo.** Esse padrão deve ser adotado nos 3 agentes com excesso de tools (Kanban, Pipeline, Sourcing).

O restante das melhorias identificadas é débito técnico interno da LIA — não inspirado pelo v5, mas mapeado pelo diagnóstico comparativo com as melhores práticas de mercado. A execução das Sprints Z1–Z4 (complementando o roadmap F1–F4 já planejado) posiciona a LIA como a plataforma de R&S com IA mais completa e regulatoriamente segura do mercado brasileiro de médio e grande porte.

**Gap mais estratégico a resolver após Z1–Z4:** os 9 subagentes de sourcing do v5 têm acesso a 51 APIs externas que a LIA não cobre. Investigar quais dessas APIs são relevantes para o mercado brasileiro e criar o catálogo YAML correspondente é a próxima fronteira de expansão do sourcing externo da LIA (F4-03).

---

*Diagnóstico Estratégico — versão 1.0 — 19/03/2026*
*Elaborado com base na análise comparativa das 19 seções anteriores + melhores práticas de mercado*
*Sprints Z1–Z4 complementam e refinam o Plano de Otimização F1–F4 (versão 1.0)*
*Todos os itens são não-destrutivos — sem breaking changes em produção*
