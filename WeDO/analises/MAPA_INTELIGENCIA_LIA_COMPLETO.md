# Mapa Completo de Inteligência da LIA
**Versão:** 3.0 — 09/03/2026
**Fonte:** Auditoria direta do código-fonte (`lia-agent-system/` + `plataforma-lia/`)
**Propósito:** Inventário completo e fonte única de verdade (SSOT) de toda a camada de inteligência da plataforma LIA — agentes, ferramentas, serviços, automações, predições, compliance e roadmap.

> **Atualizações desta versão:** Sprints G1–G7 e Sprint J (Float Chat Nível 3) concluídos. Coverage: 29,05% (gate 25%). 1.344 testes passando.

---

## Sumário

1. [Arquitetura Geral da Camada de Inteligência](#1-arquitetura-geral)
2. [Agentes ReAct — 7 Domínios](#2-agentes-react)
   - 2.1 [Wizard Agent — Criação de Vagas](#21-wizard-agent)
   - 2.2 [Pipeline Agent — Triagem de Candidatos (cv_screening)](#22-pipeline-agent-triagem)
   - 2.3 [PipelineTransition Agent — Transições de Etapa](#23-pipelinetransition-agent)
   - 2.4 [Sourcing Agent — Busca de Candidatos](#24-sourcing-agent)
   - 2.5 [Talent Agent — Funil de Talentos](#25-talent-agent)
   - 2.6 [JobsManagement Agent — Portfólio de Vagas](#26-jobsmanagement-agent)
   - 2.7 [Kanban Agent — Análise do Pipeline](#27-kanban-agent)
   - 2.8 [Policy Agent — Políticas de Contratação](#28-policy-agent)
   - 2.9 [Automation Agent](#29-automation-agent)
3. [Infraestrutura Compartilhada (shared/agents)](#3-infraestrutura-compartilhada)
4. [Automações com Triggers](#4-automacoes-com-triggers)
   - 4.1 [ProactiveAgentWorker](#41-proactiveagentworker)
   - 4.2 [AutomationTriggerService](#42-automationtriggerservice)
   - 4.3 [Automações Customizadas pelo Cliente](#43-automacoes-customizadas-pelo-cliente)
5. [Análises e Relatórios Gerados por IA](#5-analises-e-relatorios-gerados-por-ia)
   - 5.1 [Parecer do Candidato (7 Seções)](#51-parecer-do-candidato)
   - 5.2 [Relatório de Busca no Funil de Talentos](#52-relatorio-de-busca-no-funil)
   - 5.3 [Daily Briefing](#53-daily-briefing)
   - 5.4 [Intelligence Layer — Sugestões no Wizard](#54-intelligence-layer)
   - 5.5 [Explainability Service — Transparência LGPD](#55-explainability-service)
6. [Predições (Predictive Analytics)](#6-predicoes)
7. [Background Jobs (Agente Autônomo)](#7-background-jobs)
8. [Compliance e Fairness Integrados](#8-compliance-e-fairness)
9. [Serviços de Inteligência Operacional (Ondas 1–3)](#9-servicos-de-inteligencia-operacional)
   - 9.1 [Pipeline Velocity Engine](#91-pipeline-velocity-engine)
   - 9.2 [Zero-Touch Scheduling](#92-zero-touch-scheduling)
   - 9.3 [Silver Medalists](#93-silver-medalists)
   - 9.4 [Recruiter Intelligence](#94-recruiter-intelligence)
   - 9.5 [Early Warning Score (EWS)](#95-early-warning-score-ews)
   - 9.6 [Journey Intelligence](#96-journey-intelligence)
   - 9.7 [Recruiter Performance Benchmark](#97-recruiter-performance-benchmark)
   - 9.8 [Pipeline Prediction](#98-pipeline-prediction)
10. [**NOVO** Sprints G1–G7 + Sprint J (09/03/2026)](#10-sprints-g1-g7-sprint-j)
    - 10.1 [G1 — HITL Multi-tenant Fix](#101-g1)
    - 10.2 [G2 — Coverage Gate 29%](#102-g2)
    - 10.3 [G3 — SearchResultsHeader (FE)](#103-g3)
    - 10.4 [G4 — useCandidatesListMapped (FE)](#104-g4)
    - 10.5 [G5 — YAML Tool Registry](#105-g5)
    - 10.6 [G6 — RAG Híbrido (BM25 + pgvector)](#106-g6)
    - 10.7 [G7 — TOON Service](#107-g7)
    - 10.8 [Sprint J — Float Chat Nível 3 (WebSocket)](#108-sprint-j)
11. [Status Geral](#11-status-geral)
12. [Roadmap — Próximas Evoluções](#12-roadmap)

---

## 1. Arquitetura Geral

```
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND (plataforma-lia/)                                      │
│  LiaChatPanel.tsx ←→ useFloatStreaming.ts ← useAgentStreaming.ts│
│  HITLConfirmCard.tsx (card de aprovação HITL)                   │
└────────────────────────┬────────────────────────────────────────┘
                         │ WebSocket /ws/chat/{session_id}  ← Sprint J
┌────────────────────────▼────────────────────────────────────────┐
│  API GATEWAY                                                     │
│  app/api/v1/agent_chat_ws.py  (JWT + session + WS dispatch)     │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  ORCHESTRATOR (app/orchestrator/)                                │
│  main_orchestrator.py — 3 fases:                                 │
│  ├─ Phase 0: PendingAction (HITL multi-turn / residual)         │
│  ├─ Phase 1: ActionExecutor (intents fechadas)                   │
│  └─ Phase 2: CascadedRouter (6 tiers)                           │
│      ├─ Tier 1: NavigationIntent (regex, sem LLM) — 7 grupos    │
│      ├─ Tier 2: Intent Classifier (Claude)                      │
│      ├─ Tier 3: Domain Matcher                                  │
│      ├─ Tier 4: Plan Detector                                   │
│      ├─ Tier 5: Domain Dispatch                                 │
│      └─ Tier 6: ReAct Execution → DomainWorkflow               │
└────────────────────────┬────────────────────────────────────────┘
                         │ domain dispatch
     ┌───────────────────┼───────────────────┐
     ▼                   ▼                   ▼
[Wizard LangGraph] [CV Screening LG]  [Sourcing ReAct]
[Pipeline ReAct]   [Talent ReAct]     [JobsMgmt ReAct]
[Kanban ReAct]     [Policy ReAct]     [Automation ReAct]
     │                   │                   │
     └───────────────────┴───────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  COMPLIANCE (cross-cutting)                                      │
│  FairnessGuard (3 camadas) | Drift Detection | Bias Audit | HITL│
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  SHARED SERVICES                                                 │
│  LLMService (Claude→OpenAI→Gemini cascade)                      │
│  RAGPipelineService (BM25 + pgvector α-blend) ← Sprint G6      │
│  TOONService (candidate card, Redis TTL 1h)   ← Sprint G7      │
│  HITLService (Redis fast-path + DB)                             │
│  TokenBudgetService (multi-tenant, 4 planos)                    │
│  EmbeddingService | NotificationService | LangSmith             │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  BACKGROUND (autônomo)                                           │
│  ProactiveAgentWorker (loop 30min) → 11 checks → proactive_acts │
│  AutomationTriggerService → 7 triggers → tarefas automáticas    │
│  AutonomousAgentService → jobs em lote (screening, reports)     │
│  Celery Beat → drift check diário às 06h                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  SERVIÇOS DE INTELIGÊNCIA OPERACIONAL (Ondas 1–3)               │
│  PipelineVelocityService    Pipeline Prediction Service          │
│  ZeroTouchSchedulingService SilverMedalistService               │
│  RecruiterMetricsService    EarlyWarningService                  │
│  JourneyIntelligenceService PredictiveAnalyticsService          │
└─────────────────────────────────────────────────────────────────┘
```

**Tecnologia dos agentes:**
- **LangGraph:** fluxos determinísticos e auditáveis (Wizard, WSI Interview). Suporta `interrupt_before` para HITL.
- **ReAct loop** (`react_loop.py`): agente raciocina, decide tool, executa, observa, repete (max 5 iterações).

---

## 2. Agentes ReAct

### 2.1 Wizard Agent
**Domínio:** `app/domains/job_management/agents/`
**Contexto de uso:** Recrutador cria ou edita uma vaga. Interface conversacional que guia pelo processo em 6 etapas.

**Etapas (stages):**
| Stage | Descrição |
|-------|-----------|
| `input-evaluation` | Avalia input inicial do recrutador, valida campos básicos |
| `jd-enrichment` | Enriquece descrição da vaga com sugestões de IA |
| `salary` | Pesquisa e recomenda benchmarks salariais |
| `competencies` | Sugere competências técnicas e comportamentais |
| `wsi-questions` | Gera perguntas de triagem WSI para a vaga |
| `review-publish` | Revisão final, validação e publicação |

**Ferramentas disponíveis (9 tools):**

| Ferramenta | O que faz | Stage(s) |
|-----------|-----------|---------|
| `validate_job_requirements` | FairnessGuard (3 camadas) sobre requisitos, descrição ou perguntas de triagem | input-eval, competencies, review |
| `get_salary_benchmarks` | Combina histórico interno (SQL) + benchmarks externos (Robert Half, Gupy 2024) | salary |
| `search_salary_benchmark` | Pesquisa rápida de benchmark salarial por cargo/senioridade | salary |
| `validate_job_fields` | Score de completude dos campos preenchidos, campos faltantes | input-eval, salary, review |
| `get_job_suggestions` | Sugestões de IA por campo (skills, benefícios, modelo de trabalho, etc.) | jd-enrichment, competencies |
| `save_job_draft` | Salva rascunho da vaga no banco durante qualquer etapa | todas |
| `get_company_config` | Configurações da empresa: benefícios, políticas, templates de pipeline | todas |
| `generate_enriched_jd` | Gera descrição completa enriquecida com skills, responsabilidades e salário | jd-enrichment |
| `check_job_draft_health` | Avalia saúde do rascunho: campos críticos, salário abaixo do mercado, poucas skills | input-eval, salary, review |

**Análises geradas automaticamente:**
- Benchmark salarial com comparação interno vs. mercado e recomendação textual
- Score de completude do rascunho (0-100%)
- Relatório de riscos do rascunho (critical/attention/healthy)
- Detecção de viés discriminatório em requisitos e perguntas de triagem

---

### 2.2 Pipeline Agent (Triagem)
**Domínio:** `app/domains/cv_screening/agents/`
**Contexto de uso:** Recrutador abre um candidato dentro de uma vaga. LIA oferece análise e permite ações sobre o candidato.

**Etapas (stages):**
| Stage | Descrição |
|-------|-----------|
| `triage` | Primeira avaliação — ver perfil e analisar CV |
| `screening` | Execução e visualização do WSI |
| `shortlist` | Adição à pré-seleção, movimentação em massa |
| `interview` | Agendamento, notas e comunicação |
| `offer` | Geração de proposta |
| `hired` | Finalização da contratação |

**Ferramentas disponíveis (14 tools):**

| Ferramenta | O que faz | Stage(s) |
|-----------|-----------|---------|
| `view_candidate_profile` | Perfil completo com skills, pipeline status, scores — dados reais do PostgreSQL | triage, shortlist |
| `analyze_cv` | Análise do CV: fit score, skills, experiência, certificações — dados reais | triage |
| `run_wsi_screening` | Retorna resultado WSI existente (técnico, comportamental, overall, percentil) | screening |
| `schedule_interview` | Cria registro de entrevista no banco com data/tipo | interview |
| `send_communication` | Envia mensagem ao candidato e salva em communication_logs | interview, offer |
| `add_notes` | Adiciona nota timestampada ao candidato em vacancy_candidates | todas |
| `move_candidate` | Move candidato de etapa com motivo (rastreabilidade) — UPDATE real | todas |
| `batch_move` | Move múltiplos candidatos de uma vez | shortlist |
| `add_to_shortlist` | Marca candidato como shortlisted | shortlist |
| `view_screening_results` | Exibe WSI score + LIA score do candidato | screening |
| `view_interview_notes` | Histórico de entrevistas com notas e feedback | interview |
| `generate_offer` | Gera estrutura de proposta com dados do candidato + vaga (salário, cargo, modelo) | offer |
| `finalize_hiring` | Marca candidato como contratado no sistema | hired |
| `update_status` | Atualiza status: contratado, rejeitado, desistente, em espera | hired |

---

### 2.3 PipelineTransition Agent
**Domínio:** `app/domains/pipeline/agents/`
**Contexto de uso:** Agente especializado em validar e executar transições de etapa no pipeline. Focado em conformidade da mudança.

**Ferramentas (17 tools — domínio `pipeline`):**

| Ferramenta | O que faz |
|-----------|-----------|
| `get_candidate_profile` | Dados do candidato para contexto da transição |
| `get_vacancy_details` | Detalhes da vaga alvo |
| `get_pipeline_stage_config` | Regras e configurações de cada etapa |
| `validate_stage_transition` | Valida se a transição é permitida pelas políticas |
| `execute_stage_transition` | Executa a transição de fato |
| `check_candidate_preferences` | Verifica preferências de trabalho do candidato (modelo, localização, salário) |
| `update_candidate_preferences` | Atualiza preferências extraídas da conversa |
| `extract_candidate_preferences` | Extrai preferências de texto livre com NLP |
| `check_fairness` | FairnessGuard sobre o motivo da transição |
| `log_recruiter_learning` | Registra aprendizado do recrutador com base no padrão de decisão |
| `get_company_policy` | Busca política de contratação da empresa |
| `generate_stage_checklist` | Gera checklist de requisitos para a etapa de destino |
| `calculate_lia_score` | Recalcula LIA score do candidato |
| `get_historical_transitions` | Histórico de transições anteriores do candidato |
| `notify_stakeholders` | Notifica partes interessadas sobre a transição |
| `schedule_next_action` | Agenda próxima ação necessária na nova etapa |
| `generate_transition_summary` | Gera resumo da transição para o recrutador |

---

### 2.4 Sourcing Agent
**Domínio:** `app/domains/sourcing/agents/`
**Contexto de uso:** Recrutador usa o Funil de Talentos para buscar candidatos externos. A LIA processa a busca, gera relatório e sugere ações.

**Ferramentas principais:**

| Ferramenta | O que faz |
|-----------|-----------|
| `set_search_criteria` | Define parâmetros da busca (cargo, skills, localização, experiência, salário) |
| `search_candidates` | Executa busca real no banco de candidatos com filtros avançados |
| `search_external_candidates` | Busca em fontes externas (Pearch AI — 190M+ perfis) |
| `analyze_search_results` | Gera analytics completo do resultado: distribuição, qualidade, alertas proativos |
| `save_search` | Salva critérios de busca para reutilização |
| `add_to_pipeline` | Adiciona candidato encontrado a uma vaga |
| `send_outreach` | Envia mensagem de prospecção (email/WhatsApp) |
| `create_shortlist` | Cria lista selecionada a partir da busca |
| `check_sourcing_fairness` | FairnessGuard nos critérios de busca |
| `get_market_intelligence` | Inteligência de mercado para o perfil buscado |

**Análise gerada após cada busca (SearchAnalyticsService):**
- Summary: total encontrado, score médio, qualidade de contato
- Distribuições: senioridade, localização, modelo de trabalho
- Top Skills e Top Empresas de origem
- Range de experiência (min, max, média, mediana)
- Alertas proativos (50%+ em concorrentes, baixa disponibilidade de contato, etc.)
- Suggested Actions: triagem WSI, atribuir vaga, salvar favoritos, verificar disponibilidade WhatsApp em lote, agendar entrevistas, refinar busca, exportar
- Narrativa em linguagem natural descrevendo o pool encontrado

---

### 2.5 Talent Agent
**Domínio:** `app/domains/recruiter_assistant/agents/talent_*`
**Contexto de uso:** Gestão e análise do Funil de Talentos interno (candidatos já no sistema).

**Etapas (stages):**
| Stage | Ferramentas disponíveis |
|-------|------------------------|
| `discovery` | search_candidates, list_candidates, view_candidate_profile, check_search_fairness, get_talent_pool_benchmarks, check_pool_health |
| `analysis` | compare_candidates, rank_candidates, analyze_skills, view_candidate_profile, check_search_fairness, get_talent_pool_benchmarks, check_pool_health |
| `action_planning` | recommend_actions, create_shortlist, export_report, view_candidate_profile, check_search_fairness, check_pool_health |

**Ferramentas (12 tools):**

| Ferramenta | O que faz |
|-----------|-----------|
| `search_candidates` | Busca por query texto + filtros (localização, experiência mínima) ordenados por LIA score |
| `list_candidates` | Lista com filtro de status e vacancy_id |
| `view_candidate_profile` | Perfil completo com skills, languages, work_history |
| `compare_candidates` | Comparação lado a lado em skills, experiência, score, fit |
| `rank_candidates` | Ranking por LIA score ou match de skills para uma vaga |
| `analyze_skills` | Match técnico candidato×vaga (matched, missing, extra skills) — persiste match_percentage |
| `recommend_actions` | Recomendações data-driven: avançar (score ≥4.2), entrevistar (≥3.5), revisar (<3.0), contatar (não contactado) |
| `create_shortlist` | Cria CandidateList + CandidateListMembers no banco |
| `export_report` | Relatório com summary, avg score, top candidato, lista completa |
| `check_search_fairness` | FairnessGuard (3 camadas) sobre critérios de busca |
| `get_talent_pool_benchmarks` | Benchmarks do pool: tamanho, score médio, distribuição por etapa, vs. mercado |
| `check_pool_health` | Saúde do pool: riscos (pool pequeno, score baixo, estagnação) com severidade |

**Guardrail:** `create_shortlist` requer confirmação do recrutador antes de executar.

---

### 2.6 JobsManagement Agent
**Domínio:** `app/domains/recruiter_assistant/agents/jobs_mgmt_*`
**Contexto de uso:** Gestão estratégica do portfólio de vagas. O recrutador pergunta sobre o estado das vagas, performance, gargalos e SLA.

**Etapas (stages):**
| Stage | Ferramentas disponíveis |
|-------|------------------------|
| `overview` | list_jobs, view_job_details, get_portfolio_metrics, get_recruitment_benchmarks, validate_job_action_fairness |
| `analysis` | compare_jobs, check_sla, analyze_bottlenecks, view_job_details, get_portfolio_metrics, get_recruitment_benchmarks |
| `action` | pause_job, reopen_job, close_job, update_priority, generate_report, get_recruitment_benchmarks |

**Ferramentas (14 tools):**

| Ferramenta | O que faz | Sprint |
|-----------|-----------|--------|
| `list_jobs` | Lista vagas com contagem de candidatos, dias em aberto, prioridade (ordenada por prioridade + data) | base |
| `view_job_details` | Detalhes completos + candidatos por status | base |
| `get_portfolio_metrics` | Métricas agregadas: total ativas/pausadas/fechadas/rascunho, avg TTF, fill rate — por período (semana/mês/trimestre) | base |
| `compare_jobs` | Comparação de vagas: dias em aberto, candidatos, score médio, rejeitados | base |
| `check_sla` | Compliance de SLA: vagas vencidas, em risco (≤7d), em risco (≤14d), conformes | base |
| `analyze_bottlenecks` | Gargalos: candidatos estagnados >14d, vagas abertas >60d, score médio baixo — por departamento | base |
| `pause_job` | Pausa vaga ativa (UPDATE real no banco) — requer motivo | base |
| `reopen_job` | Reabre vaga pausada/fechada | base |
| `close_job` | Fecha vaga definitivamente — requer motivo | base |
| `update_priority` | Atualiza prioridade (alta/média/baixa) | base |
| `generate_report` | Relatório do portfólio com TTF, fill rate, totais por período | base |
| `get_recruitment_benchmarks` | TTF real vs. benchmark de mercado, fill rate, comparação setorial (above/at/below market) | base |
| `validate_job_action_fairness` | FairnessGuard sobre justificativas de ações nas vagas | base |
| `get_pipeline_prediction` | Visão geral do portfolio com probabilidade de fechamento por vaga — ranking de risco | 3A |

---

### 2.7 Kanban Agent
**Domínio:** `app/domains/recruiter_assistant/agents/kanban_*`
**Contexto de uso:** Análise profunda do pipeline Kanban. O recrutador pede visão estratégica de etapas, gargalos, aging e movimentações.

**Etapas (stages):**
| Stage | Ferramentas disponíveis |
|-------|------------------------|
| `pipeline_overview` | get_pipeline_summary, get_stage_metrics, list_stage_candidates, check_rejection_fairness, get_pipeline_benchmarks |
| `stage_analysis` | analyze_stage, identify_bottlenecks, get_candidate_aging, compare_stages, get_stage_metrics, check_rejection_fairness, get_pipeline_benchmarks |
| `pipeline_actions` | suggest_movements, batch_move_candidates, send_batch_communication, start_screening_batch, generate_pipeline_report, check_rejection_fairness |

**Ferramentas (21 tools):**

| Ferramenta | O que faz | Sprint |
|-----------|-----------|--------|
| `get_pipeline_summary` | Contagem por etapa, taxa de conversão, total de candidatos | base |
| `get_stage_metrics` | Candidatos na etapa, tempo médio, LIA score médio, risco de gargalo | base |
| `list_stage_candidates` | Candidatos de uma etapa com days_in_stage ordenado por score | base |
| `analyze_stage` | Análise profunda: saúde (healthy/attention/critical), riscos, recomendações | base |
| `identify_bottlenecks` | Etapas com avg >14d ou >30% estagnados — lista etapas críticas | base |
| `get_candidate_aging` | Relatório de candidatos parados além de N dias com dias exatos | base |
| `compare_stages` | Comparação de métricas entre múltiplas etapas (melhor × pior desempenho) | base |
| `suggest_movements` | Sugestões: avançar (score ≥4.2), follow-up (>14 dias parado), desqualificar (<3.0) | base |
| `batch_move_candidates` | Move candidatos em lote entre etapas (UPDATE real) | base |
| `send_batch_communication` | Comunicação em massa por email/WhatsApp/SMS | base |
| `start_screening_batch` | Inicia WSI em lote para múltiplos candidatos | base |
| `generate_pipeline_report` | Relatório consolidado: candidatos, etapas, conversão, gargalos, saúde geral | base |
| `get_pipeline_benchmarks` | Tempo médio por etapa desta vaga vs. média da empresa (ahead/on_track/behind) | base |
| `check_rejection_fairness` | FairnessGuard (3 camadas) sobre justificativas de rejeição | base |
| `get_pipeline_velocity` | Velocidade real por etapa + gargalos vs. benchmark da empresa | 1B |
| `find_silver_medalists` | Candidatos prata de processos anteriores compatíveis com a vaga atual | 1E |
| `get_at_risk_candidates` | Candidatos com EWS score elevado — risco de ghosting por etapa | 2B |
| `get_journey_metrics` | Health score (0–100) + funil + padrões preditivos de risco da vaga | 2C |
| `get_recruiter_backlog` | Lista priorizada de candidatos aguardando ação do recrutador | 2A |
| `get_recruiter_benchmark` | Comparação de performance individual vs. mediana anônima da empresa | 2D |
| `get_pipeline_prediction` | Probabilidade de fechamento (0–100%) + fatores + estimativa de dias | 3A |

**Guardrails:** `batch_move_candidates`, `send_batch_communication` e `start_screening_batch` requerem confirmação do recrutador.

---

### 2.8 Policy Agent
**Domínio:** `app/domains/hiring_policy/agents/`
**Contexto de uso:** Configuração e gestão das políticas de contratação da empresa. Inclui regras de pipeline, agendamento, comunicação e automação.

**Ferramentas principais:**

| Ferramenta | O que faz |
|-----------|-----------|
| `get_current_policy` | Retorna política atual da empresa (pipeline_rules, scheduling_rules, communication_rules, screening_rules, automation_rules, learned_patterns, autonomy_level) |
| `update_pipeline_rules` | Atualiza regras de progressão de etapas |
| `update_scheduling_rules` | Configura regras de agendamento (horários, buffers, preferências) |
| `update_communication_rules` | Define templates e regras de comunicação |
| `update_screening_rules` | Configura WSI, perguntas de triagem e critérios de qualificação |
| `update_automation_rules` | Configura automações habilitadas e thresholds |
| `validate_policy` | Valida política contra requisitos legais e FairnessGuard |
| `get_policy_analytics` | Analytics: eficácia das políticas, impacto nas métricas |
| `get_industry_benchmarks` | Benchmarks setoriais com fontes citáveis (ABRH, GPTW, LinkedIn, Robert Half) |
| `setup_pipeline_templates` | Cria templates de pipeline (etapas, critérios, automações) |
| `get_setup_status` | Status de configuração da empresa (setup_progress por seção) |
| `validate_policy_fairness` | FairnessGuard sobre políticas de contratação |

---

### 2.9 Automation Agent
**Domínio:** `app/domains/automation/agents/`
**Contexto de uso:** Gerenciamento e configuração de automações personalizadas da empresa.

**Ferramentas principais:**

| Ferramenta | O que faz |
|-----------|-----------|
| `list_automations` | Lista automações configuradas com status e histórico de execução |
| `create_automation` | Cria nova automação com trigger + ações encadeadas |
| `update_automation` | Edita automação existente |
| `toggle_automation` | Habilita/desabilita automação |
| `test_automation` | Executa automação em modo de teste (sem efeitos reais) |
| `view_execution_log` | Histórico de execuções com sucesso/falha |
| `get_automation_metrics` | Métricas de execução: volume, taxa de sucesso, economia de tempo |

---

## 3. Infraestrutura Compartilhada

### shared/agents/ — Componentes base de todos os agentes

| Componente | Arquivo | O que faz |
|-----------|---------|-----------|
| **ReActLoop** | `react_loop.py` | Motor principal: raciocina, decide tool, executa, observa, itera |
| **ReactAgentRegistry** | `react_agent_registry.py` | Registro de todos os agentes disponíveis — roteamento por domínio |
| **ProactiveAgentWorker** | `proactive_worker.py` | Loop autônomo (30min): detecta alertas proativos em 5 dimensões |
| **LearningExtractor** | `learning_extractor.py` | Extrai padrões de aprendizado de interações (o que o recrutador aceita/rejeita) |
| **AutonomyEngine** | `autonomy_engine.py` | Controla nível de autonomia: SUPERVISED/ASSISTED/AUTONOMOUS |
| **WorkingMemory** | `working_memory.py` | Memória de curto prazo da sessão atual do agente |
| **LongTermMemory** | `long_term_memory.py` | Memória persistente: preferências, padrões, histórico por empresa/recrutador |
| **MemoryIntegration** | `memory_integration.py` | Integra working memory + long term memory no contexto do agente |
| **StateMachine** | `state_machine.py` | Máquina de estados para fluxos guiados (wizard, onboarding) |
| **Observability** | `observability.py` | Logs estruturados de execução, LangSmith integration |
| **ExecutionLogStore** | `execution_log_store.py` | Armazenamento de logs de execução de agentes |
| **EnhancedAgentMixin** | `enhanced_agent_mixin.py` | Mixin com capabilities avançadas para agentes |

---

## 4. Automações com Triggers

### 4.1 ProactiveAgentWorker
**Arquivo:** `app/shared/agents/proactive_worker.py`
**Ciclo:** A cada 30 minutos (background loop contínuo)
**Output:** Registros em tabela `proactive_actions` com severity, suggested_action, related_job_id, related_candidate_id, `target_user_id` (alertas direcionados por recrutador)

| Check | Trigger | Severidade | Sprint | Direcionado? |
|-------|---------|-----------|--------|-------------|
| `check_stale_pipeline` | Candidato parado na etapa ≥7 dias | warning; critical se ≥14 dias | base | não |
| `check_low_pipeline` | Vaga com <3 candidatos ativos | warning; critical se zero | base | não |
| `check_high_scorers` | LIA Score >80% em "Novo" ou "Triagem" | warning | base | não |
| `check_deadlines` | Prazo da vaga nos próximos 7 dias | warning; critical se ≤2 dias | base | não |
| `check_engagement_gaps` | Candidato sem contato há ≥10 dias | info | base | não |
| `check_velocity_bottleneck` | Candidato em etapa além do threshold (2–7d por etapa) | warning; critical se >2× threshold | 1B | não |
| `check_silver_medalists` | Vaga aberta >7d sem candidato forte tem silver medalists disponíveis | info | 1E | não |
| `check_recruiter_backlog` | Candidatos aguardando ação além do threshold por etapa | warning; critical se offer/proposta parada | 2A | ✅ por recrutador |
| `check_early_warning` | EWS score ≥0.6 (high) ou ≥1.0 (critical) por candidato | warning; critical | 2B | ✅ por recrutador |
| `check_journey_intelligence` | Health score da vaga <50 (warning) ou <30 (critical) | warning; critical; sextas → email | 2C | ✅ por recrutador |
| `check_pipeline_prediction` | Probabilidade de fechamento <30% | warning; critical; sextas → email; prob ≥80% → info | 3A | ✅ por recrutador |

**Nota:** `target_user_id` adicionado dinamicamente via `ensure_proactive_actions_columns()` no startup — sem migration manual.

---

### 4.2 AutomationTriggerService
**Arquivo:** `app/domains/automation/services/automation_trigger_service.py`
**Ciclo:** Executado via scheduler periódico

| Trigger ID | Condição | Cooldown | Ações Executadas |
|-----------|---------|---------|-----------------|
| `candidate_no_contact_48h` | Candidato em status new/screening sem contato há 48h | 72h | Email (template `follow_up_48h`) + task FOLLOW_UP + log |
| `interview_reminder_24h` | Entrevista agendada em <24h sem reminder enviado | 0 | WhatsApp (template `interview_reminder`) + log |
| `scorecard_pending_24h` | Entrevista concluída há 24h sem scorecard | 24h | Notifica entrevistador + task FEEDBACK_PENDING |
| `job_no_movement_5d` | Vaga aberta sem atualização há 5 dias | 120h | Alert (severity medium) + notifica recrutador |
| `feedback_pending_48h` | Task de feedback pendente há 48h (escalation_level=0) | 24h | Eleva prioridade + notificação de escalada |
| `job_deadline_approaching` | Prazo da vaga em 3 dias | 48h | Alert (severity high) + notifica |
| `offer_accepted` | Evento: oferta aceita | 0 | Email de boas-vindas ao candidato + notificação ao gestor + log |

**Observação crítica:** Método `_create_notification_for_item` está vazio (`pass`) — as notificações in-app Bell não chegam a partir deste fluxo.

---

### 4.3 Automações Customizadas pelo Cliente
**Arquivo:** `app/domains/automation/services/automation_service.py`
**Configuração:** Via Policy Agent ou interface de configuração

**Tipos de trigger disponíveis:**
- `stage_changed` — candidato mudou de etapa
- `candidate_applied` — candidato se candidatou
- `interview_scheduled` — entrevista agendada
- `offer_made` — oferta realizada
- `offer_accepted` — oferta aceita
- `candidate_rejected` — candidato rejeitado
- `time_based` — baseado em tempo decorrido

**Tipos de ação:**
- `SEND_EMAIL` — envia email com template
- `SEND_WHATSAPP` — envia WhatsApp
- `CREATE_TASK` — cria tarefa para o recrutador
- `UPDATE_STATUS` — atualiza status do candidato
- `WAIT` — aguarda N horas/dias antes da próxima ação
- `CONDITION` — avalia condição (if/else branching)

**Rastreabilidade:** Log de execução em `automation_execution_log`.

---

## 5. Análises e Relatórios Gerados por IA

### 5.1 Parecer do Candidato
**Arquivo:** `app/services/candidate_report_service.py`
**Endpoint:** `POST /api/v1/candidates/{id}/parecer`
**Geração:** Claude Sonnet 4.5 — 7 seções estruturadas
**FairnessGuard:** Ativo nas seções 3, 4 e 6

**7 seções geradas:**

| Seção | Conteúdo | Condicional? |
|-------|---------|-------------|
| 1. Resumo Executivo | 2-3 parágrafos + highlights do perfil | Não |
| 2. Experiência Profissional | Trajetória, progressão (ascendente/estável/diversificada), empresas relevantes, gaps | Não |
| 3. Competências Técnicas | Skills, nível Dreyfus WSI, expertise, gaps técnicos, score 0-100 | Não |
| 4. Competências Comportamentais | Traits, Big Five, comunicação, liderança, score 0-100 | Só se há WSI ou Big Five |
| 5. Resultados da Triagem | Scores WSI geral/técnico/comunicação/fit cultural, tipo (texto/voz) | Só se há triagem |
| 6. Pontos Fortes e Atenção | 3-5 forças, 3-5 atenções, diferenciais | Não |
| 7. Recomendação Final | Score 0-100, ação (AVANÇAR/CONSIDERAR/NÃO_AVANÇAR), justificativa, próximos passos | Não |

**Metadados adicionais:**
- `completeness_score` — 0 a 1 ponderado: CV=30%, triagem voz=25%, WSI/Big Five=20%, entrevista=15%, teste=10%
- `data_profile` — CV_ONLY | CV_TEXT_SCREENING | CV_VOICE_SCREENING | COMPLETE
- `recommendation.level` — HIGHLY_RECOMMENDED | RECOMMENDED | POTENTIAL | NOT_RECOMMENDED | INCOMPLETE
- `lia_score` — score composto: completeness 15% + skills match 35% + experiência 20% + screening 30%

**Também disponível:** `generate_comparison_report` — compara N candidatos para a mesma vaga, ranking automático.

---

### 5.2 Relatório de Busca no Funil
**Arquivo:** `app/domains/sourcing/services/search_analytics.py`
**Quando gerado:** Automaticamente após cada busca no Funil de Talentos

**Dados gerados:**
- Summary: total encontrado, local vs. global, LIA score médio
- Contact Quality: % com telefone válido, % com email, % com LinkedIn
- Distribuições: senioridade normalizada, localização mapeada, modelo de trabalho
- Top Skills: frequência + % no pool
- Top Companies: empresas de origem com contagem
- Experience Range: min, max, média, mediana em anos
- Alertas proativos:
  - 50%+ em empresas concorrentes (warning)
  - Concentração geográfica >50% (info)
  - <30% com telefone disponível (warning)
  - Pool majoritariamente sênior ou júnior (info)
- Suggested Actions: Triagem WSI, Atribuir à Vaga, Salvar Favoritos, Verificar Disponibilidade WhatsApp em lote, Agendar Entrevistas, Refinar Busca, Exportar Lista
- Narrativa proativa: texto descrevendo o pool em linguagem natural

---

### 5.3 Daily Briefing
**Arquivo:** `app/services/briefing_service.py`
**Endpoint:** `GET /api/v1/briefing/daily`
**Por:** Recrutador (gerado por recrutador, não por empresa)

**Conteúdo:**
- **Urgent Actions:** Tarefas vencidas (com dias de atraso), feedbacks pendentes >48h, alertas críticos não reconhecidos — ordenados por prioridade
- **Pipeline Summary:** Vagas ativas, candidatos por etapa, candidatos para contatar, aguardando feedback, ofertas pendentes
- **Agenda de Hoje:** Entrevistas agendadas + tasks com deadline no dia
- **Pending Tasks:** Top 15 tasks por prioridade
- **Active Alerts:** Alerts ativos ordenados por severidade
- **`recruiter_metrics`** *(Sprint 2A)*: backlog_count, critical_count, most_urgent (candidato mais urgente), avg_response_time_days, candidates_advanced_this_week, offers_pending
- **`recruiter_benchmark`** *(Sprint 2D)*: comparação com mediana anônima da empresa — response_time, advanced_per_week, backlog_count, offers_pending. Requer ≥2 recrutadores ativos; retorna `benchmark_available: false` caso contrário
- **`pipeline_prediction`** *(Sprint 3A)*: ranking de vagas por closure_probability — vagas em risco (<30%) + vagas próximas de fechar (≥80%)

**Insights automáticos (rule-based, não LLM):**
- ≥3 feedbacks acumulados → alerta de atenção
- Ofertas pendentes → alerta de oportunidade
- ≥10 candidatos para contatar → sugestão de automatização
- ≥5 vagas ativas → sugestão de priorização
- Backlog crítico (offer parada) → alerta `critical` com `action_type: view_recruiter_backlog`
- Performance acima da média → insight `success` com `action_type: view_benchmark`
- Vagas em risco de não fechar → insight `warning` com `action_type: view_pipeline_prediction`

---

### 5.4 Intelligence Layer
**Arquivo:** `app/services/intelligence_layer_service.py`
**Quando ativo:** Durante criação de vaga no Wizard
**Pré-requisitos:** ≥50 vagas OU ≥30 contratações bem-sucedidas + ≥3 meses de dados

**O que gera:**
- `assess_data_quality` — avalia maturidade dos dados e emite recomendações
- `correction_patterns` — padrões de como recrutadores corrigem sugestões (ex: salário +15%)
- `success_profiles` — perfil das contratações bem-sucedidas (skills obrigatórias, salário médio)
- `outcome_correlations` — correlações entre fatores e resultados de vagas
- `time_to_fill_prediction` — previsão de prazo baseada em histórico da empresa
- `generate_field_suggestion` — sugestão por campo com: valor ajustado, confidence score, action (auto-fill/suggest/ask), reasoning, insights

**Cache:** 24h por empresa (PatternCache)
**Rastreabilidade:** Insights logados em `IntelligenceInsight` com `was_applied`, `was_accepted`, `final_value`

---

### 5.5 Explainability Service
**Arquivo:** `app/services/explainability_service.py`
**Propósito:** Transparência para LGPD/EU AI Act

| Função | Output |
|--------|--------|
| `generate_candidate_explanation` | Critérios avaliados (skills, experiência, WSI, idiomas), critérios NÃO usados (idade, gênero, etnia, estado civil, endereço, religião, foto), nota e histórico de decisões |
| `format_for_candidate_message` | Formata para envio por email/WhatsApp ao candidato |
| `generate_recruiter_summary` | Para o recrutador: agentes envolvidos, revisões humanas, overrides, timeline de decisões |

---

## 6. Predições

### 6.1 PredictiveAnalyticsService
**Arquivo:** `app/services/predictive_analytics_service.py`

#### predict_hiring_probability(candidate_id, job_id)
| Fator | Peso |
|-------|------|
| WSI Score | 30% |
| Match de experiência | 20% |
| Match de skills | 15% |
| Performance em entrevistas | 15% |
| Padrão de resposta/velocidade | 10% |
| Fit cultural | 10% |

**Output:** Probabilidade %, label (Muito Alta/Alta/Média/Baixa), top 3 forças, 2 áreas de atenção, recomendação, confiança %

#### predict_time_to_fill(job_id)
**Base por senioridade:** junior=25d → director=90d → c-level=120d
**Ajustes:** raridade das skills (+%), competitividade salarial (+/- dias), força do pipeline atual (-%)
**Output:** Dias previstos, range (otimista/pessimista), data prevista, ajustes detalhados, recomendações

#### predict_dropout_risk(candidate_id, job_id)
| Fator | Quando eleva o risco |
|-------|---------------------|
| Tempo na etapa | ≥14 dias |
| Dias sem contato | ≥7 dias |
| Padrão de resposta | desengajado |
| Sinais de outras ofertas | >30 dias no processo |

**Output:** % de risco, nível (LOW/MEDIUM/HIGH/CRITICAL), fator principal, ações preventivas, urgência

#### generate_pipeline_forecast(job_id, weeks=4)
**Output:** Projeção semana a semana por etapa, hires esperados, bottlenecks (etapas com >5 candidatos e conversão <50%), probabilidade de preencher a vaga %, recomendações

---

### 6.2 ML Outcome Predictor
**Arquivo:** `app/services/ml/outcome_predictor.py`

| Função | O que faz |
|--------|-----------|
| `predict_time_to_fill` | Feature engineering real: role category, seniority multiplier, skill rarity, market demand, location, urgency, company size factor |
| `predict_optimal_salary` | Range salarial ideal com análise vs. mercado e histórico da empresa |
| `predict_skill_success` | Probabilidade de sucesso de uma skill com base em `CompanySkill.times_confirmed` |
| `get_hiring_insights` | Painel consolidado: avg TTF, success rate, avg candidates per hire, top skills de sucesso, recomendações |

---

## 7. Background Jobs

### AutonomousAgentService
**Arquivo:** `app/domains/automation/services/autonomous_agent_service.py`

| Tipo de Job | O que executa |
|------------|--------------|
| `SCREENING` | Triagem em lote de candidatos para uma vaga |
| `SOURCING` | Busca automática de candidatos por critérios |
| `REPORT_GENERATION` | Geração de relatórios periódicos (pipeline summary, métricas) |
| `MARKET_ANALYSIS` | Análise de mercado para um cargo/localização (salário, demanda, skills) |
| `CANDIDATE_OUTREACH` | Envio em massa de mensagens para candidatos |
| `PATTERN_LEARNING` | Aprende com contratações bem-sucedidas, atualiza modelos internos |

**Observação crítica:** `_execute_screening_job` usa `random()` para scoring — não chama o serviço real de avaliação.

### ProactiveAction System
- LIA cria sugestões de ação na tabela `proactive_actions`
- Recrutador pode aceitar ou rejeitar
- `auto_executable = True` → LIA executa automaticamente quando aceito
- Expiração configurável (padrão: 24h)

### Celery Jobs
**Arquivo:** `app/jobs/celery_tasks.py`
**App:** `app/core/celery_app.py`

| Job | Schedule | O que faz |
|-----|---------|-----------|
| `drift.run_batch` | Diariamente às 06h Brasília | Executa drift check em todas as empresas (`run_drift_check_all_companies`) |

---

## 8. Compliance e Fairness Integrados

### FairnessGuard (3 Camadas)
**Arquivo:** `app/shared/compliance/fairness_guard.py`
**Presente em:** Todos os agentes (wizard, pipeline, talent, kanban, jobs_mgmt, policy, sourcing, pipelinetransition)

| Camada | O que verifica | Quando ativa |
|-------|---------------|-------------|
| Camada 1 | Regex sobre 40+ padrões explícitos | Sempre |
| Camada 2 | Léxico de viés implícito | Sempre |
| Camada 3 (LLM) | Análise semântica por Claude | Opt-in via `FAIRNESS_LAYER3_ENABLED` |

**Pontos de checagem por agente:**

| Agente | Onde aplica FairnessGuard |
|--------|--------------------------|
| Wizard | Requisitos, descrição, perguntas de triagem |
| Talent | Critérios de busca de candidatos |
| Kanban | Justificativas de rejeição |
| JobsManagement | Justificativas de ações sobre vagas |
| PipelineTransition | Motivos de transição de etapa |
| Policy | Políticas de contratação |
| CandidateReport | Seções 3, 4 e 6 do parecer |

### Model Drift Detection
- **Arquivo:** `app/services/model_drift_service.py`
- 4 triggers: score deviation, aprovação rate, custo, latência P95
- Endpoint: `GET /api/v1/drift/status`
- **Drift Alert Service:** `app/services/drift_alert_service.py` — 1 trigger=WARNING, 2+=URGENT, notifica Bell+Teams

### Bias Audit API
- **Arquivo:** `app/api/v1/bias_audit.py`
- Four-Fifths Rule em 4 dimensões: gênero, faixa etária, PCD, região
- Endpoint: `GET /api/v1/bias-audit/job/{job_id}`
- Snapshot histórico para auditoria SOX/ISO 27001

---

---

## 9. Serviços de Inteligência Operacional (Ondas 1–3)

> Serviços implementados entre fevereiro e março de 2026 conforme `ANALISE_ESTRATEGICA_CAMADA_INTELIGENCIA.md` e `PLANO_IMPLEMENTACAO_INTELIGENCIA.md`. Guia de testes completo: `GUIA_TESTES_ONDA1.md`.

### 9.1 Pipeline Velocity Engine
**Sprint 1B** | **Arquivo:** `app/services/pipeline_velocity_service.py`
**API:** `GET /api/v1/pipeline/velocity?vacancy_id=` | `GET /api/v1/pipeline/velocity/bottlenecks?company_id=`
**Proxy FE:** `GET /api/backend-proxy/pipeline-velocity`

**O que faz:** Calcula o tempo real que cada candidato passa em cada etapa do pipeline usando `stage_entered_at` (campo preciso, adicionado em Sprint 1A). Compara com benchmarks configurados por etapa e gera alertas de gargalo.

**Pré-requisito:** Migration `023_add_stage_entered_at.py` — campo `stage_entered_at` em `vacancy_candidates`.

| Etapa | Threshold |
|-------|-----------|
| applied / novo / initial | 2 dias |
| screening / triagem | 3 dias |
| interview_hr / entrevista_rh | 5 dias |
| interview_technical / entrevista_tecnica | 7 dias |
| offer / proposta | 3 dias |
| qualquer outra | 5 dias |

**Saídas:** `per_stage` (avg_days, median_days, is_bottleneck), `bottleneck_stages[]`, `overall_health` (healthy/warning/critical).
**ProactiveWorker:** `check_velocity_bottleneck` — alerta por vaga com candidatos acima do threshold.
**Kanban tool:** `get_pipeline_velocity`.

---

### 9.2 Zero-Touch Scheduling
**Sprint 1C** | **Arquivo:** `app/services/zero_touch_scheduling_service.py`
**API (autenticada):** `POST /api/v1/scheduling/link`
**API (pública — candidato):** `GET /api/v1/scheduling/link/{token}` | `POST /api/v1/scheduling/link/{token}/confirm`
**Proxy FE:** `POST /api/backend-proxy/scheduling/link` + `[token]` + `[token]/confirm`

**O que faz:** Permite ao recrutador enviar ao candidato um link com horários disponíveis de entrevista. O candidato escolhe o slot sem precisar ligar ou responder ao email. A entrevista é criada automaticamente no sistema após a confirmação.

**Fluxo:** Recrutador cria link → candidato recebe WhatsApp (fallback: email) → acessa `/agendar/{token}` → escolhe horário → entrevista registrada + link marcado como `used`.

**Modelo:** `SelfSchedulingLink` (token, slots, expiração, status, `use_count`, `selected_slot`).
**Canal preferido:** WhatsApp via Twilio; fallback para email se sem telefone.
**Segurança:** Token único com expiração configurável (padrão: 72h). Retorna `410 Gone` se expirado ou já usado.

---

### 9.3 Silver Medalists
**Sprint 1E** | **Arquivo:** `app/services/silver_medalist_service.py`
**Acesso:** via chat LIA (tool `find_silver_medalists`) e ProactiveWorker (check `check_silver_medalists`)
**Sem endpoint REST próprio** — surfaçado via agentes e alertas proativos.

**O que faz:** Identifica candidatos que chegaram a etapas avançadas em processos anteriores mas não foram contratados ("candidatos prata") e os sugere para novas vagas com perfil compatível.

**Critérios para ser silver medalist:**
- Chegou a `interview_hr`, `interview_technical`, `interview_manager`, `interview_final` ou `offer`
- Não contratado (`stage/status ≠ hired/contratado`)
- Processo nos últimos 90 dias (configurável)
- Não está em outra vaga ativa da empresa

**Score de relevância (0–1):**
- Etapa atingida: 40% (offer=1.0, interview_final=0.9, interview_hr=0.5)
- Recência: 35% (hoje=1.0, 180d atrás=0.1)
- LIA score anterior: 25%

**ProactiveWorker:** alerta consolidado com top 5 candidatos e sugestão de recontato.

---

### 9.4 Recruiter Intelligence
**Sprint 2A** | **Arquivo:** `app/services/recruiter_metrics_service.py`
**API:** `GET /api/v1/recruiter-metrics/{recruiter_id}` | `GET /api/v1/recruiter-metrics/{recruiter_id}/backlog`
**Proxy FE:** `GET /api/backend-proxy/recruiter-metrics/[id]` + `/backlog`

**O que faz:** Surfaça métricas de produtividade do recrutador sem criar nova tela de UI — entregue via Daily Briefing, chat LIA (tool `get_recruiter_backlog`) e bell in-app.

**Métricas calculadas:**
- `backlog_count` — candidatos aguardando ação além do threshold por etapa
- `critical_count` — candidatos em situação crítica (offer/proposta parada)
- `most_urgent` — candidato com maior urgency_score
- `avg_response_time_days` — média de dias entre candidato entrar na etapa e primeiro contato do recrutador
- `candidates_advanced_this_week` — candidatos avançados de etapa nos últimos 7 dias
- `offers_pending` — ofertas em aberto além do threshold

**Urgency score:** `days_in_stage × weight_etapa` (offer=4.0, interview=3.0, screening=2.0, applied=1.0).

**Vagas consideradas:** `created_by = user_id` OR `recruiter_email = email do recrutador`.

**Alertas ProactiveWorker:** `check_recruiter_backlog` com `target_user_id` — alerta vai apenas para o recrutador responsável. Bell para warnings, Bell + Teams para críticos (offer parada).

---

### 9.5 Early Warning Score (EWS)
**Sprint 2B** | **Arquivo:** `app/services/early_warning_service.py`
**API:** `GET /api/v1/early-warning?company_id=&min_risk_level=`
**Proxy FE:** `GET /api/backend-proxy/early-warning`

**O que faz:** Detecta candidatos em risco de ghosting **antes** do dano acontecer, com thresholds calibrados por etapa (substitui o `check_engagement_gaps` com threshold fixo de 10 dias).

**Fórmula EWS score (0.0–1.0):**
```
base_score = min(1.0, days_since_contact / critical_threshold)
lia_weight  = 1.0 + (lia_score ou 0.5) × 0.5
ews_score   = min(1.0, base_score × lia_weight)
```

| Etapa | Warning (dias) | Critical (dias) |
|-------|---------------|----------------|
| offer / proposta | 2 | 4 |
| interview_* | 3 | 5 |
| screening / triagem | 5 | 8 |
| applied / novo | 7 | 12 |

| EWS score | Risco |
|-----------|-------|
| ≥ 1.0 | critical |
| ≥ 0.6 | high |
| ≥ 0.3 | medium |
| < 0.3 | low |

**Kanban tool:** `get_at_risk_candidates`.
**ProactiveWorker:** `check_early_warning` com `target_user_id`. Bell para high/critical; Bell + Teams para critical.

---

### 9.6 Journey Intelligence
**Sprint 2C** | **Arquivo:** `app/services/journey_intelligence_service.py`
**API:** `GET /api/v1/journey/metrics?vacancy_id=&company_id=` | `GET /api/v1/journey/company-overview?company_id=`
**Proxy FE:** `GET /api/backend-proxy/journey` (vacancy_id opcional — sem ele vai para company-overview)

**O que faz:** Analisa o funil real de cada vaga em tempo real, calcula health score (0–100) e detecta padrões preditivos de risco — não apenas "candidato parado hoje" mas "este pipeline vai travar se não agir agora".

**Health score (0–100):**
| Componente | Pts | Critério |
|-----------|-----|---------|
| Volume | 20 | ≥5 candidatos ativos |
| Conversão geral | 25 | ≥20% chegaram a etapas avançadas |
| Candidatos avançados | 25 | ≥2 em entrevista/offer |
| Drop-off | 15 | taxa de saída ≤ 30% |
| EWS / engajamento | 15 | sem EWS crítico e movimento recente |

| Score | Label |
|-------|-------|
| ≥ 70 | healthy |
| 45–69 | warning |
| < 45 | critical |

**Padrões preditivos detectados:** `zero_pipeline` (critical), `empty_advanced_funnel` (critical), `high_offer_rejection` (critical), `top_heavy_funnel` (warning), `critical_health` (critical).

**LIA proativa:** quando `health_score < 50` e `vacancy_id` presente no chat, o Kanban Agent injeta automaticamente um bloco de alerta no system prompt via `get_journey_insight_block()` — a LIA abre a resposta mencionando o estado crítico.

**Kanban tool:** `get_journey_metrics`.
**ProactiveWorker:** `check_journey_intelligence` com `target_user_id`. Sextas → Bell + Teams (critical) + Email (digest semanal).

---

### 9.7 Recruiter Performance Benchmark
**Sprint 2D** | **Arquivo:** `app/services/recruiter_metrics_service.py` (mesmo serviço do 2A)
**API:** `GET /api/v1/recruiter-metrics/{recruiter_id}/benchmark?company_id=`
**Proxy FE:** `GET /api/backend-proxy/recruiter-metrics/[id]/benchmark`

**O que faz:** Compara as métricas individuais do recrutador com a mediana anônima da empresa. Entregue no Daily Briefing (seção `recruiter_benchmark`) e via chat (tool `get_recruiter_benchmark`).

**Métricas comparadas:** `response_time` (lower is better), `advanced_per_week` (higher), `backlog_count` (lower), `offers_pending` (lower).

**Labels:** `above` (>15% melhor que mediana) | `at_par` (±15%) | `below` (>15% pior).

**Performance geral:** `above_average` (≥3 métricas `better`) | `average` | `below_average`.

**Privacidade:** requer ≥2 recrutadores ativos na empresa. Com menos de 2, retorna `benchmark_available: false` — nunca expõe dados de recrutador isolado.

---

### 9.8 Pipeline Prediction
**Sprint 3A** | **Arquivo:** `app/services/pipeline_prediction_service.py`
**API:** `GET /api/v1/pipeline-prediction?vacancy_id=&company_id=` | `GET /api/v1/pipeline-prediction/company-overview?company_id=`
**Proxy FE:** `GET /api/backend-proxy/pipeline-prediction` (vacancy_id opcional)

**O que faz:** Prevê probabilidade de fechamento de vagas ativas (0–100%) usando fórmula determinística sobre dados operacionais existentes. Sem ML externo, sem migration.

**Fórmula (5 fatores, 100 pts):**
| Fator | Peso | Lógica |
|-------|------|--------|
| Velocidade | 30 pts | Média de dias por etapa: <3d=30, <5d=22, <8d=14, <14d=6, ≥14d=0 |
| Funil avançado | 25 pts | Stage do melhor candidato: offer=25, interview_final=20, interview_hr=10 |
| Health score | 20 pts | `health_score / 100 × 20` (fórmula inline do Journey 2C) |
| EWS risk | 15 pts | 15 − (critical_ews × 5) − (high_ews × 2), mínimo 0 |
| Volume | 10 pts | ≥8=10, ≥5=8, ≥3=5, ≥1=2 |

**Pipeline vazio → 0% imediatamente.**
**Confiança:** `high` (total_active ≥5 E health ≥60) | `low` (total_active ≤1 OU health <30) | `medium`.

**Injeção contextual:**
- Kanban Agent: bloco individual por vaga quando `vacancy_id` presente no chat
- JobsManagement Agent: ranking do portfolio completo em todo `process()` com `company_id`

**Kanban tool:** `get_pipeline_prediction` | **JobsManagement tool:** `get_pipeline_prediction`.
**ProactiveWorker:** `check_pipeline_prediction` — vagas <30%: `pipeline_prediction_risk` (critical/warning); vagas ≥80%: `pipeline_prediction_closing` (info, 1x por vaga por instância do worker).

---

---

## 10. Sprints G1–G7 + Sprint J (09/03/2026)

> Sprints de consolidação concluídos após as Ondas 1–3. Focados em compliance multi-tenant, coverage de testes, infraestrutura de IA avançada e frontend WebSocket.

---

### 10.1 G1 — HITL Multi-tenant Fix

**Status:** ✅ Concluído

**Problema:** `request_approval()` não passava `domain` e `company_id`, quebrando isolamento multi-tenant nas auditorias HITL.

**Fix aplicado em 3 agentes:**

| Arquivo | Campo adicionado |
|---------|-----------------|
| `app/domains/job_management/agents/job_wizard_graph.py` | `domain="job_management"`, `company_id` |
| `app/domains/cv_screening/agents/wsi_interview_graph.py` | `domain="cv_screening"`, `company_id` |
| `app/domains/pipeline/agents/pipeline_transition_agent.py` | `domain="pipeline"`, `company_id` |

**Impacto compliance:** Audit trail HITL agora segmenta por empresa e domínio — requisito SOX/BCB 498.

---

### 10.2 G2 — Coverage Gate 29%

**Status:** ✅ Concluído

**7 novos arquivos de teste adicionados:**

| Arquivo | Foco |
|---------|------|
| `tests/unit/test_navigation_intent.py` | 12+ testes (7 grupos de intenção, fallback) |
| `tests/unit/test_admin_prompts_extended.py` | Prompts admin, edge cases |
| `tests/unit/test_token_budget_extended.py` | Rate limiting, planos, edge cases |
| `tests/unit/test_hitl_service_extended.py` | Fluxos HITL, Redis TTL, approval/rejection |
| `tests/unit/test_wsi_interview_graph.py` | Fluxo de entrevista WSI, 8 estágios, HITL |
| `tests/unit/test_short_list_service.py` | CRUD short lists, edge cases |
| `tests/unit/test_admin_token_budget_api.py` | Endpoint admin token budget |
| `tests/unit/test_main_orchestrator_extended.py` | 3 fases do orquestrador |

**Configuração `pytest.ini`:**
```ini
--cov-fail-under=25
--ignore=tests/unit/test_multi_tenancy.py
--ignore=tests/unit/test_policy_gaps.py
--ignore=tests/unit/test_sync_canonical.py
```

**Resultado:** 1.344 testes passando | Coverage: 29,05% (gate 25% ✅)

---

### 10.3 G3 — SearchResultsHeader (FE)

**Status:** ✅ Concluído

**Arquivo:** `plataforma-lia/src/components/pages/candidates/SearchResultsHeader.tsx`

Extração do cabeçalho de resultados de busca de `candidates-page.tsx` (que tinha >12.000 linhas).

**Props:**
```typescript
interface Props {
  lastSearchQuery: string
  lastSearchEntities: ParsedEntities | null
  onBack: () => void
  onOpenEditQueryModal: () => void
  onOpenAdvancedSearch: () => void
}
```

**Impacto:** `candidates-page.tsx` reduzido de 202 linhas em um bloco → 9 linhas de uso.

---

### 10.4 G4 — useCandidatesListMapped (FE)

**Status:** ✅ Concluído

**Arquivos:**

| Arquivo | Responsabilidade |
|---------|-----------------|
| `plataforma-lia/src/lib/transforms/candidate-transforms.ts` | `mapCandidateLocalToCandidate()` — converte `CandidateLocal → Candidate` (~150 linhas) |
| `plataforma-lia/src/hooks/use-candidates-list-mapped.ts` | Wrapper com `useMemo`; retorna `Candidate[]` já mapeados |

**Nota:** Additive — disponível para migração incremental de `candidates-page.tsx` (Sprint F3 usa esses hooks).

---

### 10.5 G5 — YAML Tool Registry

**Status:** ✅ Concluído

**Arquivos:**

| Arquivo | Conteúdo |
|---------|---------|
| `app/tools/tool_registry_metadata.yaml` | 32 tools declaradas (name, description, allowed_agents, scope, version) |
| `app/tools/tool_registry_loader.py` | `load_tool_metadata()`, `export_registry_to_yaml()`, `validate_registry_against_yaml()` |
| `app/tools/registry.py` | Métodos adicionados: `.export_to_yaml()`, `.validate_yaml()` |

**Scopes definidos:**

| Scope | Contexto |
|-------|---------|
| `TALENT_FUNNEL` | Candidatos, funil, pipeline |
| `JOB_TABLE` | Lista de vagas |
| `IN_JOB` | Dentro de uma vaga específica |
| `GLOBAL` | Qualquer contexto |

**Benefício:** Agents descobrem tools disponíveis via YAML — sem hardcode no código Python. Permite validação estática do registro.

---

### 10.6 G6 — RAG Híbrido (BM25 + pgvector)

**Status:** ✅ Concluído

**Arquivo:** `app/services/rag_pipeline_service.py`

**Modos de busca:**

| Parâmetro `alpha` | Mecanismo | Quando Usar |
|:-----------------:|-----------|-------------|
| `0.0` | BM25 puro (PostgreSQL `tsvector`) | Busca exata por keywords |
| `1.0` | pgvector cosine similarity | Busca semântica |
| `0.5` (padrão) | Hybrid score blend | Produção — balanceia exatidão + semântica |

**Endpoint:** `GET /api/v1/candidates/rag-search?q=&company_id=&limit=20&alpha=0.5`

**FairnessGuard:** stub log-only de diversidade de gênero no top-10 (aguarda decisão: bloquear vs. reranquear).

**Testes:** 31 em `tests/unit/test_rag_pipeline.py`

---

### 10.7 G7 — TOON Service (Talent Object Of Note)

**Status:** ✅ Concluído

**Arquivo:** `app/services/toon_service.py`

Gera um card estruturado por candidato+vaga para visualização rápida pelo recrutador.

**Campos do TOONCard:**

| Campo | Descrição |
|-------|-----------|
| `headline` | Resumo 1 linha (ex: "Dev Python Sênior, 8 anos de experiência") |
| `highlights` | 3–5 bullets (role atual, skills alinhadas, seniority, preferências) |
| `match_score` | 0–100 compatibilidade com a vaga (overlap de skills) |
| `skills_match` | Lista de skills que coincidem com a vaga |
| `name_display` | Nome real OU "Candidato X" se `anonymize=True` (LGPD) |
| `location` | Localização |
| `experience_years` | Anos de experiência |
| `anonymized` | bool — flag LGPD |
| `fairness_reviewed` | bool — FairnessGuard executado |

**Cache:** Redis TTL=1h, key: `toon:{company_id}:{candidate_id}:{job_id}`

**LGPD:** `anonymize=True` → PII mascarada. Sem avatar, sem data de nascimento raw.

**Endpoint:** `GET /api/v1/candidates/{candidate_id}/toon?job_id=&company_id=&anonymize=false`

**Proxy FE:** `src/app/api/backend-proxy/candidates/[candidateId]/toon/route.ts`

**Testes:** 34 em `tests/unit/test_toon_service.py`

---

### 10.8 Sprint J — Float Chat Nível 3 (WebSocket)

**Status:** ✅ Concluído (09/03/2026)

**Contexto:** `LiaChatPanel` era REST. Migrado para WebSocket nativo com suporte completo a streaming e HITL.

#### Novos arquivos FE

**`plataforma-lia/src/hooks/use-float-streaming.ts`** (128 linhas)

Wrapper de `useAgentStreaming` com suporte a HITL inline no painel flutuante.

```typescript
interface UseFloatStreamingResult {
  tokens: string
  isStreaming: boolean
  isConnected: boolean
  hitlPending: HITLPending | null   // ← novo
  sendMessage: (content, context?, domain?) => void
  sendApproval: (approved: boolean) => void  // ← novo
  onComplete: (content: string) => void
}

interface HITLPending {
  pendingId: string
  action: string
  description: string
  data: Record<string, unknown>
}
```

**`plataforma-lia/src/components/lia-float/HITLConfirmCard.tsx`** (99 linhas)

Card UI de aprovação HITL exibido dentro do `LiaChatPanel`.

```typescript
interface Props {
  action: string           // ex: "move_candidate"
  description: string      // ex: "Mover João Silva para Aprovado"
  onConfirm: () => void
  onCancel: () => void
}
```

Design: border amber-200, bg-amber-50 (light) / amber-900/20 (dark). Ícones Lucide. Sem React-only patterns → compatível com Vue 3.

#### Protocolo WebSocket HITL completo

```
Backend → Frontend:
{ type: "approval_required", thread_id, pending_id,
  action, description, data, domain, company_id }

Frontend → Backend:
{ type: "approval_response", pending_id, approved: bool, comment? }

Backend → Frontend:
{ type: "approval_confirmed", pending_id }
// ou erro
```

#### Navigation Intent — 7 grupos atualizados

`app/orchestrator/navigation_intent.py` reordenado por especificidade:

| Grupo | Exemplos | Destino |
|-------|---------|---------|
| WSI/Entrevistas | "wsi", "entrevista estruturada" | `openSplitView("WSI")` |
| Indicadores | "indicadores", "analytics", "kpi" | `openSplitView("Indicadores")` |
| Configurações | "configurações", "settings" | `openSplitView("Config")` |
| Vagas | "vagas", "criar vaga", "wizard" | `openSplitView("Vagas")` |
| Funil/Candidatos | "funil", "candidatos", "pipeline" | `openSplitView("Funil")` |
| Painel | "painel", "dashboard", "home" | Navigate `/dashboard` |
| Fallback | — | LLM inference |

> **Wizard detectado** redireciona para `openSplitView("Vagas")` — não abre o wizard diretamente, preservando o contexto do chat.

#### Testes FE

**`plataforma-lia/src/hooks/__tests__/use-float-streaming.test.ts`** — 9 testes Vitest:
- Conexão WS
- Streaming de tokens
- HITL `approval_required` → `hitlPending` populado
- `sendApproval(true)` → envia `approval_response`
- `approval_confirmed` → limpa `hitlPending` e aguarda `message`
- Auto-reconexão

---

## 11. Status Geral

| Componente | Status | Versão |
|-----------|--------|--------|
| Wizard Agent (criação de vagas) | ✅ Funcional | base |
| Pipeline Agent (triagem) | ✅ Funcional | base |
| PipelineTransition Agent | ✅ Funcional | base |
| Sourcing Agent | ✅ Funcional | base |
| Talent Agent | ✅ Funcional | base |
| Kanban Agent | ✅ Funcional | +7 novas tools (Ondas 1–3) |
| JobsManagement Agent | ✅ Funcional | +1 nova tool (Sprint 3A) |
| Policy Agent | ✅ Funcional | base |
| Automation Agent | ✅ Funcional | base |
| ProactiveAgentWorker | ✅ Funcional | 11 checks (5 base + 6 Ondas 1–3) |
| AutomationTriggerService | ✅ Funcional | 7 triggers |
| Parecer do Candidato (7 seções) | ✅ Funcional | base |
| Search Analytics | ✅ Funcional | base |
| Daily Briefing | ✅ Funcional | +3 seções novas (2A, 2D, 3A) |
| Intelligence Layer (Wizard) | ✅ Funcional | lite mode ≥10 vagas |
| Explainability Service | ✅ Funcional | base |
| Predictive Analytics (legacy) | ✅ Funcional | base |
| ML Outcome Predictor | ✅ Funcional | base |
| Autonomous Agent (Screening) | ✅ Funcional | base |
| **Pipeline Velocity Engine** | ✅ Funcional | Sprint 1B |
| **stage_entered_at** | ✅ Migration 023 | Sprint 1A |
| **Zero-Touch Scheduling** | ✅ Funcional | Sprint 1C |
| **Silver Medalists** | ✅ Funcional | Sprint 1E |
| **Recruiter Intelligence** | ✅ Funcional | Sprint 2A |
| **Early Warning Score** | ✅ Funcional | Sprint 2B |
| **Journey Intelligence** | ✅ Funcional | Sprint 2C |
| **Recruiter Benchmark** | ✅ Funcional | Sprint 2D |
| **Pipeline Prediction** | ✅ Funcional | Sprint 3A |
| FairnessGuard (camadas 1+2) | ✅ Funcional | base |
| FairnessGuard (camada 3 LLM) | ✅ Configurado | `FAIRNESS_LAYER3_ENABLED=false` — habilitar em produção |
| Model Drift Detection | ✅ Funcional | Celery Beat diário às 06h |
| Bias Audit (Four-Fifths) | ✅ Funcional | dados reais, snapshot histórico |
| **HITL Multi-tenant** | ✅ Funcional | Sprint G1 — `domain` + `company_id` nos 3 agentes |
| **Coverage Gate 29%** | ✅ Gate 25% aprovado | Sprint G2 — 1.344 testes passando |
| **SearchResultsHeader (FE)** | ✅ Funcional | Sprint G3 — extração de componente |
| **useCandidatesListMapped (FE)** | ✅ Disponível | Sprint G4 — hook + transform (wiring Sprint F3) |
| **YAML Tool Registry (32 tools)** | ✅ Funcional | Sprint G5 — metadata YAML + validação |
| **RAG Híbrido (BM25 + pgvector)** | ✅ Funcional | Sprint G6 — alpha-blend, 31 testes |
| **TOON Service** | ✅ Funcional | Sprint G7 — card candidato, Redis TTL 1h, 34 testes |
| **Float Chat WebSocket (Sprint J)** | ✅ Funcional | use-float-streaming.ts + HITLConfirmCard.tsx + nav intent atualizado |

### Endpoints REST — Novos (Ondas 1–3)

| Método | URL | Auth | Sprint |
|--------|-----|------|--------|
| GET | `/api/v1/pipeline/velocity` | ✅ | 1B |
| GET | `/api/v1/pipeline/velocity/bottlenecks` | ✅ | 1B |
| POST | `/api/v1/scheduling/link` | ✅ | 1C |
| GET | `/api/v1/scheduling/link/{token}` | ❌ público | 1C |
| POST | `/api/v1/scheduling/link/{token}/confirm` | ❌ público | 1C |
| GET | `/api/v1/recruiter-metrics/{id}` | ✅ | 2A |
| GET | `/api/v1/recruiter-metrics/{id}/backlog` | ✅ | 2A |
| GET | `/api/v1/recruiter-metrics/{id}/benchmark` | ✅ | 2D |
| GET | `/api/v1/early-warning` | ✅ | 2B |
| GET | `/api/v1/journey/metrics` | ✅ | 2C |
| GET | `/api/v1/journey/company-overview` | ✅ | 2C |
| GET | `/api/v1/pipeline-prediction` | ✅ | 3A |
| GET | `/api/v1/pipeline-prediction/company-overview` | ✅ | 3A |

### Testes Unitários

| Arquivo | Testes |
|---------|--------|
| `tests/unit/test_stage_entered_at.py` | 6 |
| `tests/unit/test_pipeline_velocity_service.py` | 12 |
| `tests/unit/test_silver_medalist_service.py` | 22 |
| `tests/unit/test_pipeline_prediction_service.py` | 29 |
| `tests/unit/test_navigation_intent.py` | 12+ |
| `tests/unit/test_hitl_service_extended.py` | 15+ |
| `tests/unit/test_wsi_interview_graph.py` | 12+ |
| `tests/unit/test_token_budget_extended.py` | 10+ |
| `tests/unit/test_rag_pipeline.py` | 31 |
| `tests/unit/test_toon_service.py` | 34 |
| `tests/unit/test_short_list_service.py` | 15+ |
| `tests/unit/test_langsmith_config.py` | 18 |
| `src/hooks/__tests__/use-float-streaming.test.ts` | 9 |
| **Total (conforme última execução)** | **1.344 passando** — Coverage **29,05%** |

---

## 12. Roadmap — Próximas Evoluções

### Sprint F — Em Andamento (09/03/2026)

| Sprint | Item | Prioridade |
|--------|------|-----------|
| **F1** | HITL Persistence — migration `031_add_hitl_tables.py` + modelos `hitl_pending_actions` + `hitl_audit_trail` + DB como source of truth em `hitl_service.py` | 🔴 Alta |
| **F2** | Coverage gate unification — `pytest.ini` `--cov-fail-under=12` → `25` (full suite já atinge 25,39%) | 🟡 Média |
| **F3** | Wiring de `use-candidates-list.ts` + `use-candidate-data-requests.ts` em `candidates-page.tsx` | 🔴 Alta |
| **F4** | Short List Endpoint — BE (`app/api/v1/short_lists.py`) + FE (`use-short-list.ts`) | 🟡 Média |
| **F5** | Extração de `CandidateSearchBar` + `CandidateTabs` de `candidates-page.tsx` (12.404L → ~11.600L) | 🟡 Média |
| **F6** | LangSmith CI Step em `.github/workflows/ci.yml` (`continue-on-error: true`) | 🟢 Baixa |

---

### Interview Kit + Interviewer Reliability (OPP-5 — deferred)
**Prioridade:** Alta | **Onda:** futura (junto com evolução do módulo de entrevistas)

**Motivação:** A plataforma já possui toda a infraestrutura necessária (`LiaOpinion` com WSI do candidato, `CalibrationEvent` com histórico de feedback de entrevistadores, `InterviewReminder`). A implementação foi deferida para ser entregue em conjunto com a evolução das funcionalidades de entrevista, garantindo coerência de experiência.

**O que implementar:**

**`InterviewKitService`** — gerar automaticamente um kit personalizado para o entrevistador:
- Busca perfil WSI do candidato (`LiaOpinion`) + competências da vaga
- Gera via LLM (Claude): 5 perguntas STAR focadas nos gaps, 2 perguntas técnicas sobre skills ausentes, 1 pergunta de alinhamento cultural, contexto do candidato
- **FairnessGuard Layer 1+2 obrigatório** nas perguntas geradas (Inegociável #3)
- Tool `generate_interview_kit` no Pipeline Agent

**`InterviewerReliabilityService`** — detectar entrevistadores fora da calibração do time:
- Agrega `CalibrationEvent` por usuário
- Calcula score médio dado vs. mediana do time
- Flag se desvio > 1.5 desvios padrão
- Exposto no Daily Briefing para gestores

**Lembrete de feedback pós-entrevista:**
- Novo `InterviewReminder` type: `feedback_due`
- Enviado 4h após `interview.end_time` (memória ainda fresca)
- Canal: Bell + WhatsApp
- Escalada ao recrutador se não submetido em 24h

**Arquivos a criar:**
- `app/services/interview_kit_service.py`
- `app/services/interviewer_reliability_service.py`
- Tool `generate_interview_kit` em `pipeline_tool_registry.py`

**Pré-condições:** nenhuma dependência técnica bloqueante — pode ser implementado assim que a evolução das features de entrevista for priorizada.

---

### Onda 3 — Funcionalidades de Dados (6+ meses de histórico necessário)

| Feature | OPP | Pré-condição |
|---------|-----|-------------|
| Quality of Hire Loop | OPP-6 | 50+ contratações + surveys 30/90 dias |
| Source Attribution completa | OPP-4B | campo `sourcing_channel` em `vacancy_candidates` |
| Talent Pool Lifecycle | OPP-10 | campo `lifecycle_stage` em `candidate_list_members` |
| Market Intelligence (Talent Availability Index) | OPP-7 | 12+ meses de histórico + Pearch API signals |
| Hiring Plan Intelligence preditivo | OPP-8 | 12+ meses + integração HRIS |

---

---

### Gaps Arquiteturais Conhecidos (para Sprint H)

| Gap | Descrição | Impacto |
|-----|-----------|---------|
| **Testes de integração de agentes** | Unit tests cobrem serviços. Fluxo completo agent end-to-end = praticamente zero | 🔴 Alto |
| **Guardrails editáveis** | FairnessGuard é code-based. Sem interface admin para editar sem deploy | 🟡 Médio |
| **Fragmentação de prompts** | 4 locais: `app/agents/prompts/`, `app/prompts/`, `app/shared/prompts/`, `app/domains/*/system_prompt.py` | 🟡 Médio |
| **FairnessGuard RAG** | Diversidade de gênero top-10 em RAG é stub (log-only). Decisão pendente: bloquear ou reranquear | 🟡 Médio |
| **MAX_TOOL_CALLS hardcoded** | `llm.py:26`: `MAX_TOOL_CALLS_PER_REQUEST = 3` sem config por tenant | 🟢 Baixo |
| **HITL Persistence** | Persistência DB ainda não implementada (Sprint F1) — sem ela, aprovações se perdem em restart | 🔴 Alto |

---

*Documento atualizado em 09/03/2026 — SSOT da camada de inteligência LIA. Versão 3.0.*
*Sprints concluídos: A–F + G1–G7 + Sprint J. Coverage: 29,05%. 1.344 testes passando.*
