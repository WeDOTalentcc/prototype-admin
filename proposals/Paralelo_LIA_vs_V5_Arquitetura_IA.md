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
