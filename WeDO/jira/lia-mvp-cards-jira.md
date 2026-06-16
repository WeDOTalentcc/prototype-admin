# PLATAFORMA LIA MVP - ESPECIFICAÇÃO COMPLETA + CARDS JIRA

**Data:** Fevereiro 2026  
**Versão:** 2.4  
**Última Atualização:** 09 Fevereiro 2026  
**Status:** Documento de Referência para Desenvolvimento

---

# PARTE 1: VISÃO GERAL, ÍNDICES E ANÁLISES

## TODO PROJETO REPLIT — WeDo Talent — Paulo Moraes

> **Objetivo:** Lista consolidada do que precisa ser construído no protótipo Replit e no ambiente de produção para implementar todas as features do Talent Funnel (doc `epic-wdt-talent-funnel.md`) e dos cards MAP-001 a MAP-013 do Épico 3.  
> **Data:** 08 Fevereiro 2026  
> **Referências cruzadas:** `epic-wdt-talent-funnel.md` (27 cards WDT ativos, 3 cancelados)

---

### PARTE 1: O QUE CONSTRUIR NO PROTÓTIPO REPLIT (Referência Visual/Funcional)

O protótipo Replit serve como **referência de comportamento e UX** para o time de produção (Vue/Nuxt/Rails). Tudo que for construído aqui será convertido pelo time externo.

#### 1.1 FRONTEND — Componentes e Páginas a Criar/Adaptar

**PRIORIDADE CRÍTICA (MVP — Sprint 1-2)**

- [ ] **Serviço de Busca Paginada no Frontend** (MAP-007 / WDT-001)
  - Hook `useSearchPaginated` que chama `POST /api/backend-proxy/search/paginated`
  - Gerenciar estado: candidates[], exclude_ids[], has_more, search_id
  - Acumular exclude_ids a cada página carregada
  - Passar exclude_ids na próxima requisição para garantir resultados únicos
  - Integração: MAP-009 (exclusão ES) e MAP-010 (exclusão PGV) são transparentes no backend

- [ ] **Paginação On-Demand na Busca de Candidatos** (MAP-008 / WDT-002)
  - Componente `LoadMoreButton` com estado (loading, idle, no-more-results)
  - Substituir scroll infinito por botão "Carregar mais 10"
  - Contador: "Mostrando X de Y candidatos relevantes"
  - Acumular candidatos exibidos (não substituir)
  - Consome hook `useSearchPaginated` (MAP-007)
  - Arquivo ref: `plataforma-lia/src/components/search/search-results-card.tsx`

- [ ] **Botões Like/Dislike no Card de Candidato** (MAP-012 / WDT-007)
  - Ícones thumbs up/down em cada card de resultado de busca
  - Toggle: clicar novamente remove feedback
  - Feedback visual imediato (cor verde/vermelho) com optimistic update
  - Loading state durante save
  - Estado sincronizado entre páginas
  - Arquivo ref: `plataforma-lia/src/components/search/search-results-card.tsx`

- [ ] **Remover Ordenação Automática por Score** (MAP-013 / WDT-005)
  - Exibir candidatos na ordem retornada pela API (sem sort no front por padrão)
  - Manter scores visíveis nos cards (badge)
  - Dropdown de ordenação manual: "Relevância (padrão)" | "Score (maior)" | "Nome A-Z" | "Data"
  - Tooltip: "Candidatos relevantes para sua busca"
  - Novo componente: `SearchSortDropdown`

**PRIORIDADE ALTA (MVP — Sprint 2)**

- [ ] **Lista de Candidatos da Base com Cards** (MAP-001)
  - Verificar se componente `CandidatesTable` já exibe cards no layout correto
  - Card do candidato deve conter: foto, nome, título, skills (badges), score (badge colorido), localização, última atividade
  - Selecionar múltiplos candidatos (checkboxes)
  - Loading skeleton durante carregamento

- [ ] **Busca Semântica Simulada** (MAP-002)
  - Input de busca inteligente (já existe `smart-search-input.tsx`)
  - Resultado deve simular retorno ES+PGV+WRF com score unificado
  - Integração com backend Python (endpoint a criar)

- [ ] **Painel de Filtros Avançados** (MAP-003)
  - Já existe `advanced-filters-modal.tsx` — verificar se cobre:
    - Skills (autocomplete)
    - Experiência (slider range 0-20+)
    - Localização (autocomplete)
    - Disponibilidade (imediata, 15d, 30d)
    - Faixa salarial (slider range)
    - Senioridade (junior/pleno/senior/especialista)
    - Modelo (remoto/híbrido/presencial)
    - **NOVOS filtros**: shortlisted (com data inclusão, vaga origem), placement (data colocação, vaga destino, empresa cliente), vaga específica (dropdown com busca), data cadastro
  - Salvar filtros como preset
  - Chips de filtros ativos com remoção individual
  - Botão "Limpar todos"

- [ ] **Modal Adicionar Candidato a Vaga** (MAP-004)
  - Já existe `add-to-job-modal.tsx` — verificar se cobre:
    - Fluxo individual (hover no card → botão → modal)
    - Fluxo em massa (checkboxes → barra flutuante → modal)
    - Dropdown de vagas com busca
    - Tratamento de duplicados
    - Toast com feedback e link para vaga
    - Limite de 100 candidatos em massa

- [ ] **Badge Matching Score IA** (MAP-005)
  - Badge colorido no card do candidato (verde 80-100, amarelo 60-79, vermelho 0-59)
  - Tooltip com breakdown ao hover (Skills 65%, Experiência 85%, etc.)
  - Click expande explicação textual completa
  - Visual de barras de progresso por dimensão

- [ ] **Painel Sugestões Proativas LIA** (MAP-006)
  - Badge no menu: "Sugestões LIA (5)"
  - Painel/modal com cards de sugestão agrupados por vaga
  - Card: foto + nome + score badge + motivo (1-2 linhas)
  - Botões: Aceitar | Rejeitar | Depois
  - Aceitar = adiciona a vaga; Rejeitar = remove + aprende; Depois = move para final

**PRIORIDADE MÉDIA (Pós-MVP — Épico 16)**

- [ ] **Badge de Classificação de Vaga** (WDT-010)
  - Chip colorido na vaga: Alta (roxo), Média (azul), Baixa (verde)
  - Dropdown para override manual pelo recrutador
  - Tooltip explicando impacto na busca

- [ ] **Dashboard de Métricas de Feedback** (WDT-008)
  - Página admin com gráficos (Chart.js ou similar)
  - Donut: likes vs dislikes
  - Barras: taxa de like por faixa de score
  - Tabela: feedback por recrutador
  - Filtros por período (7d, 30d, 90d)

- [x] **Score Breakdown por Requisito** (WDT-022) ✅ Implementado (Replit) — Cap 99, floor rounding, evidence weights, André's scoring formulas

**PRIORIDADE FUTURA (Pós-MVP — Épicos 17-18)**

- [x] ~~**Interface Admin Gestão de Critérios** (WDT-017)~~ ❌ CANCELADO — Sistema auto-evolutivo, sem interface admin manual

- [ ] **Toggle Requisito Excludente** (WDT-023)
  - Switch no formulário de requisitos da vaga: "Excludente"
  - Visual: switch vermelho indicando eliminação automática

- [ ] **Feedback de Qualidade Pós-Busca** (WDT-025)
  - Componente que aparece após resultados carregarem
  - Alert "info" se satisfatório
  - Dialog com sugestões de refinamento se não satisfatório
  - Botão "Aplicar sugestão" por sugestão

- [ ] **Flags de Inconsistência** (WDT-026)
  - Chip amarelo "⚠ Alerta" no card do candidato flagado
  - Tooltip com mensagem específica da inconsistência

- [ ] **Dashboard Observabilidade de Busca** (WDT-030)
  - Gauge charts: taxa queda, gap semântico, estabilidade
  - Line charts: tokens/busca, tempo resposta p50/p95/p99
  - Donut: like/dislike ratio
  - Funnel chart: candidatos filtrados por etapa
  - Auto-refresh 60s

- [ ] **Página Admin Experimentos A/B** (WDT-028)
  - Criar/gerenciar experimentos
  - Dashboard de resultados por variante

- [ ] **Página Admin Learning Insights** (WDT-027)
  - Lista de sugestões de ajuste do sistema
  - Botões aprovar/rejeitar por sugestão

- [x] ~~**Painel de Recomendações de Critérios** (WDT-019)~~ ❌ CANCELADO — Sistema auto-evolutivo, sem dashboard admin

- [x] ~~**Simulador de Impacto de Critérios** (WDT-020)~~ ❌ CANCELADO — Substituído por auto-seed de catálogos

---

#### 1.2 BACKEND PYTHON (FastAPI — lia-agent-system)

**PRIORIDADE CRÍTICA (MVP)**

- [ ] **Endpoint de Busca Paginada Simulada** (MAP-007 / WDT-001)
  - `POST /api/v1/search/paginated`
  - Aceitar: query, page, limit (fixo 10), exclude_ids[], job_id, filters
  - Retornar: candidates[], total_found, has_more, search_id
  - Simular WRF com dados mock/seedados
  - Rota proxy Next.js: `/api/backend-proxy/search/paginated`

- [ ] **API de Feedback Like/Dislike** (MAP-011 / WDT-006)
  - `POST /api/v1/searches/{search_id}/candidates/{id}/feedback`
  - `DELETE /api/v1/searches/{search_id}/candidates/{id}/feedback`
  - `GET /api/v1/searches/{search_id}/feedbacks`
  - Schema: search_id, candidate_id, user_id, feedback_type (like/dislike), snapshots (query + score)
  - Unicidade: um feedback por candidato por busca por usuário
  - Já existe `candidate_feedback_service.py` — verificar e adaptar

- [ ] **Matching Score Service** (MAP-005)
  - `POST /api/v1/lia/matching-score`
  - Prompt Gemini/Claude para análise candidato × vaga
  - Output JSON: score 0-100, breakdown por dimensão, explicação textual
  - Cache 24h por par (job_id, candidate_id)
  - Já existe `lia_score_service.py` — verificar e adaptar

**PRIORIDADE ALTA**

- [ ] **Sugestões Proativas de Candidatos** (MAP-006)
  - `GET /api/v1/lia/suggestions`
  - `POST /api/v1/lia/suggestions/{id}/feedback`
  - Buscar candidatos score > 75 para vagas abertas
  - Excluir já adicionados e rejeitados
  - Máximo 10 por vaga

**PRIORIDADE MÉDIA (Pós-MVP)**

- [ ] **Classificação Automática de Nível de Vaga** (WDT-009)
  - `POST /api/v1/ai/classify-job-level`
  - Prompt Gemini: classificar em Alta/Média/Baixa
  - Response: { level, confidence, reasoning }

- [x] **Integração Critérios com Prompt LLM** (WDT-018) ✅ Implementado (Replit) — _format_criteria_examples(), "DO NOT INFER" rule, fuzzy matching

- [x] **Sistema Explicit/Implicit/Inferred** (WDT-021) ✅ Implementado (Replit) — EvidenceType enum, 18 vague language indicators, anomaly flags, essential exclusion

- [ ] **Análise Pós-Busca com Feedback de Qualidade** (WDT-025)
  - `POST /api/v1/ai/analyze-search-quality`
  - LLM avalia os 10 resultados como conjunto
  - Retorna: quality_score, suggestions[], is_satisfactory

- [ ] **Motor de Aprendizado via Feedback** (WDT-027)
  - `POST /api/v1/ai/analyze-feedback-patterns`
  - Correlação: critérios × feedback × tipo vaga
  - Output: sugestões de ajuste com confiança

- [x] ~~**Recomendação de Critérios via LLM** (WDT-019)~~ ❌ CANCELADO — Sistema auto-evolutivo

- [x] ~~**Refinamento de Prompt com Evidências** (WDT-020)~~ ❌ CANCELADO — Substituído por auto-seed

- [ ] **Instrumentação de Métricas e Logging** (WDT-029)
  - Structured logging para pipeline de busca (latência, tokens, erros)
  - Prometheus metrics exporter para busca paginada, WRF, LLM calls
  - Healthcheck endpoint: `GET /api/v1/search/health`

---

### PARTE 2: O QUE O TIME DE PRODUÇÃO PRECISA CONSTRUIR (Rails + Vue + Python)

> Esta seção é a referência para o time externo implementar no ambiente de produção (Ruby on Rails 7.x + Vue 3/Nuxt 3/Vuetify 3 + Python FastAPI).

#### 2.1 BACKEND RAILS — Services, Models, Migrations, APIs

**SPRINT 1 — CRÍTICO**

- [ ] **Endpoint de Busca Paginada** (MAP-007 / WDT-001)
  - Controller: `app/controllers/api/v1/search_controller.rb`
  - Service: `app/services/search/paginated_search_service.rb`
  - Orquestra: ES query + PGV query + WRF merge
  - Response: 10 candidatos, search_id, has_more, exclude_ids
  - Migration: `create_search_sessions` (id, user_id, job_id, query, results_cache, exclude_ids[])

- [ ] **Adaptar ES Query para Exclusão de IDs** (MAP-009 / WDT-003)
  - Service: `app/services/search/elasticsearch_query_builder.rb`
  - Adicionar `must_not: [{ ids: { values: exclude_ids } }]`
  - Validar: limite 500 IDs, não afetar scoring
  - Benchmark rake task com 0/10/50/100/500 IDs

- [ ] **Adaptar PG Vector Query para Exclusão de IDs** (MAP-010 / WDT-004)
  - Service: `app/services/search/pgvector_query_service.rb`
  - Usar neighbor gem: `.where.not(candidate_id: exclude_ids)`
  - Validar: distância cossenos idêntica com/sem exclusão
  - NOT EXISTS se > 500 IDs

- [ ] **API de Feedback Like/Dislike** (MAP-011 / WDT-006)
  - Migration: `create_candidate_feedbacks` com snapshots JSONB
  - Model: `CandidateFeedback` com enum, scopes, validações
  - Controller: CRUD + unicidade [search_id, candidate_id, user_id]
  - Routes: nested under searches
  - Multi-tenant: scoping por company_id

**SPRINT 2**

- [ ] **Busca Semântica com ES + PGV + WRF** (MAP-002)
  - Service Objects para cada componente do pipeline
  - WRF Service com fórmula: `score = sum(1 / (K + rank_i))`
  - K padrão = 60 (fixo no MVP, dinâmico pós-MVP)
  - Cache Redis por query + filters

- [ ] **Filtros Avançados de Candidatos** (MAP-003)
  - Suportar: skills, experiência, localização, disponibilidade, salário, senioridade, modelo
  - Novos: shortlisted (desdobramentos), placement (desdobramentos), vaga específica, data
  - Presets salvos: `filter_presets` table (JSONB)
  - Debounce 300ms no endpoint

- [ ] **Adicionar Candidato a Vaga** (MAP-004)
  - `POST /api/v1/job-vacancies/{jobId}/add-candidates`
  - Seleção individual e em massa (limite 100)
  - Constraint UNIQUE(job_id, candidate_id)
  - Response: { added, duplicates, errors }

- [ ] **Matching Score IA** (MAP-005)
  - Service: `MatchingScoreService`
  - Chama Python FastAPI para análise LLM
  - Cache Redis 24h por (job_id, candidate_id)
  - Recálculo ao atualizar vaga ou candidato

- [ ] **Sugestões Proativas de Candidatos** (MAP-006)
  - Service: `ProactiveSuggestionsService`
  - Job scheduler para refresh diário (Sidekiq)
  - Score mínimo 75, máximo 10 por vaga
  - Feedback aceitar/rejeitar/depois

**SPRINT 3-5 — PÓS-MVP**

- [ ] **Classificação Automática de Nível de Vaga** (WDT-009) ⚠️ BLOQUEANTE
  - Migration: `add_column :jobs, :qualification_level` (enum: alta/média/baixa)
  - Callback after_save para classificar via Python FastAPI
  - Override manual possível

- [ ] **Cálculo de Taxa de Queda de Score ES** (WDT-011)
  - Service: `app/services/search/es_score_drop_analyzer.rb`
  - Thresholds por qualification_level: alta 40%, média 55%, baixa 70%
  - Configurável via ENV vars

- [ ] **Cálculo de Gap Semântico PGV** (WDT-012)
  - Service: `app/services/search/pgv_gap_analyzer.rb`
  - Multipliers por qualification_level: alta 1.5x, média 2.0x, baixa 2.5x

- [ ] **Teste de Estabilidade Intra-Query** (WDT-013)
  - Rake task: `rails search:stability_test[query,5]`
  - Endpoint admin only
  - Alerta se estabilidade < 80%

- [ ] **K Dinâmico no WRF** (WDT-014)
  - Alta: K=20-30, Média: K=40-50, Baixa: K=60-80
  - Valores via ENV: `WRF_K_ALTA`, `WRF_K_MEDIA`, `WRF_K_BAIXA`

- [ ] **Filtro Pré-WRF Combinado** (WDT-015)
  - Service: `app/services/search/pre_wrf_filter_service.rb`
  - Orquestra: EsScoreDropAnalyzer + PgvGapAnalyzer → WrfService

**SPRINT 6-11 — GAME CHANGER**

- [x] **Schema Base de Critérios de Avaliação** (WDT-016) ⚠️ GAME CHANGER ✅ Implementado (Replit — SQLAlchemy/Python)
  - Modelo: `lia-agent-system/app/models/evaluation_criteria.py`
  - Auto-seed de TECH_SKILLS_CATALOG, BEHAVIORAL_COMPETENCIES_CATALOG, RESPONSIBILITIES_CATALOG
  - Categories: technical_skill, behavioral_competency, experience, education, certification, language, responsibility
  - JSONB para evidências positivas/negativas
  - Fuzzy matching, effectiveness auto-update via feedback

- [x] **Sistema Explicit/Implicit/Inferred** (WDT-021) ✅ Implementado (Replit)

- [x] **Score de Confiança por Requisito** (WDT-022) ✅ Implementado (Replit)

**SPRINT 12-17 — FEATURES AVANÇADAS**

- [ ] **Requisitos Excludentes** (WDT-023)
  - Migration: `add_column :job_requirements, :is_excludent, :boolean`
  - Filtro pré-WRF por requisitos excludentes

- [ ] **Enriquecimento de Perfil via Web** (WDT-024)
  - Sidekiq job + SerpAPI + LLM
  - Rate limit: 10/hora por company

- [ ] **Flags de Inconsistência** (WDT-026)
  - Service: `app/services/search/inconsistency_detector.rb`
  - 4 regras heurísticas configuráveis

- [ ] **Motor de Aprendizado** (WDT-027)
  - Job semanal (Sidekiq)
  - Model: `LearningInsight` com aprovação humana obrigatória

- [ ] **Framework A/B Testing** (WDT-028)
  - Model: `Experiment` com variantes JSONB
  - Distribuição estável via hash do user_id

- [ ] **Instrumentação de Métricas** (WDT-029)
  - Logging service para cada etapa do pipeline de busca
  - Table: `search_pipeline_logs` (search_id, stage, duration_ms, tokens, error)
  - Rake task: `rails search:metrics_report[7d]`

- [x] ~~**Recomendação e Refinamento de Critérios** (WDT-019 / WDT-020)~~ ❌ CANCELADOS — Sistema auto-evolutivo, substituído por auto-seed

---

#### 2.2 FRONTEND VUE/VUETIFY — Componentes e Páginas

**SPRINT 1**

- [ ] **CandidateFeedbackButtons.vue** (WDT-007)
  - v-btn icon: mdi-thumb-up (success), mdi-thumb-down (error)
  - Composable: `useCandidateFeedback.ts`
  - API service: `feedbackApi.ts`

- [ ] **LoadMorePagination.vue** (WDT-002)
  - v-btn "Carregar mais 10"
  - Composable: `useSearchPagination.ts`
  - Acumular exclude_ids

**SPRINT 2**

- [ ] **SearchSortDropdown.vue** (WDT-005)
  - v-select com 4 opções de ordenação
  - Sort local (sem re-request)
  - Emit 'update:sortBy'

- [ ] **QualificationBadge.vue** (WDT-010)
  - v-chip com cores por nível + v-tooltip
  - Override via v-select inline

- [ ] **FeedbackDashboard.vue** (WDT-008)
  - ApexCharts: donut, barras, tabela
  - v-select para período

**SPRINT 7+**

- [x] ~~**EvaluationCriteria.vue** + **CriterionForm.vue** + **EvidenceList.vue** (WDT-017)~~ ❌ CANCELADO

- [x] **ScoreBreakdown.vue** (WDT-022) ✅ Backend implementado (Replit), Vue component pendente produção

- [ ] **SearchQualityFeedback.vue** (WDT-025)
  - v-dialog com sugestões pós-busca
  - v-btn "Aplicar sugestão"

- [ ] **LearningInsights.vue** (WDT-027)
  - Lista de sugestões pendentes com approve/reject

- [ ] **Experiments.vue** (WDT-028)
  - CRUD de experimentos com dashboard de resultados

- [ ] **SearchObservability.vue** (WDT-030)
  - 8 métricas em grid de cards com ApexCharts
  - Auto-refresh 60s

- [x] ~~**CriteriaRecommendations.vue** (WDT-019)~~ ❌ CANCELADO

- [x] ~~**CriteriaImpactSimulator.vue** (WDT-020)~~ ❌ CANCELADO

---

#### 2.3 IA / PYTHON FASTAPI — Endpoints e Services

**MVP**

- [ ] **Pipeline de Busca Paginada** (WDT-001)
  - Orquestrar ES + PGV + WRF no Python se necessário
  - Retornar 10 candidatos por vez

- [ ] **Matching Score via LLM** (MAP-005)
  - Prompt Gemini com contexto vaga + candidato
  - Output JSON estruturado: score, breakdown, explanation

**PÓS-MVP**

- [ ] **Classificação de Nível de Vaga via LLM** (WDT-009)
  - Prompt: analisar título + descrição + requisitos + salário
  - Response: { level, confidence, reasoning }

- [x] **Criteria Prompt Builder** (WDT-018) ✅ Implementado (Replit) — _format_criteria_examples() em rubric_evaluation_service.py

- [x] **Classificação Explicit/Implicit/Inferred** (WDT-021) ✅ Implementado (Replit)

- [ ] **Análise Pós-Busca** (WDT-025)
  - Endpoint: `POST /api/v1/ai/analyze-search-quality`
  - LLM avalia conjunto de 10 resultados

- [ ] **Motor de Aprendizado** (WDT-027)
  - Endpoint: `POST /api/v1/ai/analyze-feedback-patterns`
  - Correlação critérios × feedback
  - NUNCA aplicar automaticamente — human-in-the-loop

---

#### 2.4 DADOS E INFRAESTRUTURA

**MVP**

- [ ] **Table: search_sessions** (WDT-001)
  - id, user_id, job_id, query, results_cache (jsonb), exclude_ids (array), company_id, created_at

- [ ] **Table: candidate_feedbacks** (WDT-006)
  - id, search_id, candidate_id, user_id, job_id, company_id, feedback_type (enum), search_query_snapshot (jsonb), candidate_score_snapshot (jsonb), timestamps
  - Unique index: [search_id, candidate_id, user_id]

- [ ] **Table: matching_scores** (MAP-005)
  - job_id, candidate_id, score, breakdown (jsonb), explanation, calculated_at

- [ ] **Table: lia_suggestions** (MAP-006)
  - id, job_id, candidate_id, score, reason, status, feedback

- [ ] **Table: filter_presets** (MAP-003)
  - id, user_id, name, filters (jsonb)

**PÓS-MVP**

- [ ] **Column: jobs.qualification_level** (WDT-009)
  - enum: baixa/media/alta + confidence + reasoning + override

- [x] **Table: evaluation_criteria** (WDT-016) ✅ Implementado (Replit — SQLAlchemy)
  - Fields: id (UUID), name, category, subcategory, positive_evidences (JSONB), negative_evidences (JSONB), evaluation_guidelines, effectiveness_score, usage_count, feedback_count, source, is_active

- [ ] **Table: search_metrics** (WDT-030)
  - search_id, es_score_drop_rate, pgv_gap_mean, stability_index, tokens_used, response_time_ms, etc.

- [ ] **Table: experiments** (WDT-028)
  - name, status, parameter_name, variants (jsonb), start/end dates, min_sample_size

- [ ] **Table: learning_insights** (WDT-027)
  - suggestion_type, target, current_value, suggested_value, confidence, reasoning, status, approved_by

- [ ] **Column: job_requirements.is_excludent** (WDT-023)

---

#### 2.5 DOCUMENTAÇÃO TÉCNICA

- [ ] **Arquitetura do Pipeline de Busca** (WDT-029)
  - `docs/search/ARCHITECTURE.md` — Diagrama ES + PGV + WRF (Mermaid)
  - `docs/search/PARAMETERS.md` — Tabela de parâmetros ajustáveis com ENV vars
  - `docs/search/TROUBLESHOOTING.md` — 10+ problemas comuns
  - `docs/search/PROMPTS.md` — Todos os prompts LLM do pipeline

---

## DOCUMENTOS RELACIONADOS

| Documento | Descrição | Atualização |
|-----------|-----------|-------------|
| [configuracoes-admin-cards-jira.md](./configuracoes-admin-cards-jira.md) | **58 Cards Config Admin** (Jira WT-1047 a WT-1104) | 27 Jan ✅ |
| [MVP_DEVELOPMENT_SPEC.md](./MVP_DEVELOPMENT_SPEC.md) | Especificação MVP detalhada original | 26 Jan ✅ |
| [LIA_UNIFIED_METHODOLOGY.md](./LIA_UNIFIED_METHODOLOGY.md) | Metodologia unificada 4 camadas | 22 Jan ✅ |
| [WSI_METHODOLOGY_REFERENCE.md](./WSI_METHODOLOGY_REFERENCE.md) | Referência WSI (Bloom, Dreyfus, Big Five) | 22 Jan ✅ |
| [PLANO_ACAO_AGENTES_IA.md](./PLANO_ACAO_AGENTES_IA.md) | Plano de ação dos agentes IA | Disponível ✅ |
| [proposals/job-wizard-enhancement-plan.md](./proposals/job-wizard-enhancement-plan.md) | Wizard de Criação de Vagas v4.0 (6 estágios) | 02 Fev ✅ |
| [epic-wdt-talent-funnel.md](./epic-wdt-talent-funnel.md) | **27 Cards WDT ativos** (3 cancelados) Funil de Talentos (ES+PGV+WRF) com prompts IA | 08 Fev ✅ |
| [00-design-system-v4.md](../plataforma-lia/docs/design-system/00-design-system-v4.md) | **Design System LIA v4.1** — Monocromático + acentos WeDo, Light-first, Vuetify 3.x, Tailwind | Fev ✅ |
| [admin-wedotalent-cards-jira.md](./admin-wedotalent-cards-jira.md) | **Admin Layer** — Cards WeDo Talent Admin | Disponível ✅ |

---

## VISÃO GERAL DO MVP

### Objetivo
Entregar um sistema funcional onde o recrutador consiga:
- Criar/editar vagas e configurar roteiro de triagem WSI (via modal no preview da vaga)
- Pesquisar e adicionar candidatos em vagas (busca manual OU solicitação para LIA buscar)
- Ter a LIA gerando perguntas de triagem automaticamente
- **Aprovar candidatos mapeados** antes da LIA iniciar contato (Gate 1)
- Ter a LIA fazendo contato via WhatsApp e triagem WSI
- **Aprovar/reprovar candidatos triados** com base no score WSI (Gate 2)
- Ter a LIA agendando entrevistas (aprovados) ou dando feedback (reprovados)

> **Nota:** O Wizard Conversacional (Épico 2) foi adiado para pós-MVP. No MVP, a criação de vagas é feita via formulário direto e a edição do roteiro de triagem WSI é feita via modal na tab "Roteiro de Triagem" do preview da vaga (Tabela de Vagas → Preview → Roteiro de Triagem → Editar).

### Escopo MVP
O MVP termina no **agendamento da entrevista pela LIA**. Etapas posteriores (entrevista, proposta, contratação) serão gerenciadas no ATS integrado.

### Portões de Aprovação (Gates)

| Gate | Momento | Ação do Recrutador | Se APROVADO | Se REPROVADO |
|------|---------|-------------------|-------------|--------------|
| **Gate 1** | Após mapeamento | Aprovar candidatos para triagem | LIA inicia contato WhatsApp | LIA envia feedback → Coluna "Reprovados" |
| **Gate 2** | Após triagem WSI | Aprovar/Reprovar com base no score | LIA agenda entrevista | LIA envia feedback → Coluna "Reprovados" |

### Fontes de Candidatos

| Fonte | Descrição | Quem Adiciona |
|-------|-----------|---------------|
| **Base Interna** | Candidatos já cadastrados na plataforma | Recrutador busca e adiciona |
| **Busca Global** | LinkedIn, Pearch, outras fontes externas | LIA busca e sugere |
| **Importação ATS** | Candidatos vindos do ATS integrado | Sistema importa automaticamente |
| **Inscrição via Link** | Candidatos via link publicado em redes sociais | Candidato se auto-cadastra via WhatsApp |

---

## FLUXO MVP DETALHADO

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           FLUXO MVP - PLATAFORMA LIA                            │
└─────────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐                              ┌──────────────┐
    │  RECRUTADOR  │                              │     LIA      │
    └──────┬───────┘                              └──────┬───────┘
           │                                             │
           │  1. CRIAR/EDITAR VAGA                        │
           │  ─────────────────────────────────────────► │
           │  • Cria vaga via formulário                 │
           │  • Define requisitos, benefícios            │
           │  • Configura roteiro de triagem WSI         │
           │    (Preview Vaga → Roteiro → Modal Edição)  │
           │                                             │
           │                    2. GERAR PERGUNTAS       │
           │  ◄───────────────────────────────────────── │
           │  • LIA analisa requisitos da vaga           │
           │  • Gera perguntas WSI (Blocos 2-5)          │
           │  • Recrutador edita/ajusta via modal        │
           │                                             │
           │  3. BUSCAR CANDIDATOS                       │
           │  ─────────────────────────────────────────► │
           │  • Solicita busca na base interna           │
           │  • Solicita busca global (Pearch/LinkedIn)  │
           │                                             │
           │                    4. MAPEAR CANDIDATOS     │
           │  ◄───────────────────────────────────────── │
           │  • LIA busca e ranqueia candidatos          │
           │  • Adiciona candidatos na vaga → FUNIL      │
           │                                             │
           │  5. APROVAR MAPEADOS (Gate 1)               │
           │  ─────────────────────────────────────────► │
           │  • Aprova → TRIAGEM | Reprova → REPROVADO   │
           │                                             │
           │                    6. CONTATAR VIA WHATSAPP │
           │  ◄───────────────────────────────────────── │
           │  • LIA envia mensagem de abordagem          │
           │  • Aguarda resposta do candidato            │
           │                                             │
           │                    7. FAZER TRIAGEM WSI     │
           │  ◄───────────────────────────────────────── │
           │  • LIA conduz conversa via WhatsApp         │
           │  • Aplica perguntas, calcula Score WSI      │
           │                                             │
           │  8. APROVAR/REPROVAR TRIADOS (Gate 2)       │
           │  ─────────────────────────────────────────► │
           │  • Aprova → SHORT LIST | Reprova → FEEDBACK │
           │                                             │
           │                    9A. AGENDAR ENTREVISTA   │
           │  ◄───────────────────────────────────────── │
           │  (Se APROVADO) LIA agenda via Teams         │
           │                                             │
           │                    9B. DAR FEEDBACK         │
           │  ◄───────────────────────────────────────── │
           │  (Se REPROVADO) LIA envia feedback          │
           │                                             │
           ▼                                             ▼
    ┌──────────────────────────────────────────────────────────┐
    │              FIM DO ESCOPO MVP                           │
    │  Candidatos aprovados: Entrevista agendada               │
    │  Candidatos reprovados: Feedback enviado                 │
    └──────────────────────────────────────────────────────────┘
```

---

## FLUXO DE ESTADOS DO CANDIDATO

```
                                    ┌─────────────┐
                                    │   INÍCIO    │
                                    └──────┬──────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ ETAPA 1: FUNIL                                                              │
│ Candidatos mapeados pela LIA (busca interna + global)                       │
│ Sub-status: mapeado, aguardando_aprovacao                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                           │
                         ┌─────────────────┴─────────────────┐
                         │ Recrutador aprova? (Gate 1)       │
                    ┌────┴────┐                         ┌────┴────┐
                    │   SIM   │                         │   NÃO   │
                    └────┬────┘                         └────┬────┘
                         │                                   │
                         ▼                                   ▼
┌─────────────────────────────────────┐     ┌─────────────────────────────────┐
│ ETAPA 2: TRIAGEM                    │     │ REPROVADO (Gate 1)              │
│ LIA contata via WhatsApp            │     │ LIA envia feedback automático   │
│ LIA aplica perguntas WSI            │     │ Sub-status: feedback_enviado    │
└─────────────────────────────────────┘     └─────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ ETAPA 3: TRIAGEM CONCLUÍDA                                                  │
│ Score WSI calculado | Parecer LIA gerado | Notificação enviada              │
└─────────────────────────────────────────────────────────────────────────────┘
                                           │
                         ┌─────────────────┴─────────────────┐
                         │ Recrutador aprova? (Gate 2)       │
                    ┌────┴────┐                         ┌────┴────┐
                    │   SIM   │                         │   NÃO   │
                    └────┬────┘                         └────┬────┘
                         │                                   │
                         ▼                                   ▼
┌─────────────────────────────────────┐     ┌─────────────────────────────────┐
│ ETAPA 4: SHORT LIST                 │     │ REPROVADO (Gate 2)              │
│ LIA agenda entrevista               │     │ LIA envia feedback automático   │
│ Sub-status: entrevista_agendada     │     │ Sub-status: feedback_enviado    │
└─────────────────────────────────────┘     └─────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ ETAPA 5: ENTREVISTA AGENDADA                                                │
│ ═══════════════════════════════════════════════════════════════════════════ │
│                         FIM DO ESCOPO MVP                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## STATUS DAS FUNCIONALIDADES

| Módulo | Funcionalidade | Status | Observação |
|--------|----------------|--------|------------|
| Autenticação | Login/Logout | 📋 Pendente | - |
| Funil de Talentos | Busca de candidatos | 📋 Pendente | - |
| Funil de Talentos | Filtros de busca | 📋 Pendente | - |
| Funil de Talentos | Adicionar candidatos à vaga | 📋 Pendente | - |
| Vagas | Listar vagas | 📋 Pendente | - |
| Vagas | Criar/Editar vaga (formulário) | 📋 Pendente | Sem wizard conversacional no MVP |
| Vagas | Preview da vaga (tabs) | 📋 Pendente | Inclui tab Roteiro de Triagem |
| Roteiro WSI | Modal edição de roteiro de triagem | 📋 Pendente | Criar/editar perguntas WSI |
| Roteiro WSI | Geração automática de perguntas (LIA) | 📋 Pendente | Integração com backend WSI |
| Kanban | Estrutura básica (colunas) | 📋 Pendente | - |
| Kanban | Drag and drop | 📋 Pendente | - |
| Kanban | Feedback implícito | 📋 Pendente | Captura em transições |
| Tabela | Estrutura básica | 📋 Pendente | CandidateTableRow.tsx |
| Tabela | Preview lateral | 📋 Pendente | - |
| Pipeline | Cards de etapas (carrossel) | 📋 Pendente | - |
| Agentes IA | 10 agentes especializados (v2.2) | 📋 Pendente | Arquitetura multi-agente |
| Templates | 326 templates curados | 📋 Pendente | 9 categorias |

---

## INTEGRAÇÕES MVP

| Integração | Propósito | Status | Prioridade |
|------------|-----------|--------|------------|
| **Claude (Anthropic)** | LLM para agentes, perguntas, parecer | 📋 Pendente | Crítica |
| **Gemini (Google)** | Busca semântica, embeddings, multimodal | 📋 Pendente | Alta |
| **OpenAI** | LLM alternativo, fallback, TTS | 📋 Pendente | Média |
| **WhatsApp (Twilio)** | Comunicação com candidatos | 📋 Pendente | Crítica |
| **Microsoft Graph** | Calendário, Teams, Outlook | 📋 Pendente | Alta |
| **WorkOS** | SSO, MFA, SCIM | 📋 Pendente | Média |
| **Gupy** | Integração ATS Brasil | 📋 Pendente | Média |
| **Pandapé** | Integração ATS Brasil | 📋 Pendente | Média |
| **StackOne** | Unified HRIS/ATS API | 📋 Pendente | Média |
| **Merge** | Multi-ATS/HRIS Integration | 📋 Pendente | Média |
| **Pearch** | Busca global de candidatos | 📋 Pendente | Alta |
| **Deepgram** | Speech-to-Text (Nova-2) | 📋 Pendente | Média |

---

## CRONOGRAMA DE SEMANAS

| Semana | Período | Cards | Foco Principal |
|--------|---------|-------|----------------|
| **Semana 1** | 09/fev → 13/fev | 61 | **Fundação**: Auth, Kanban, Mapeamento, Integrações (WorkOS+Twilio) |
| **Semana 2** | 16/fev → 20/fev | 47 | **Core**: WSI, Triagem, Templates, Agendamento, Integrações (MS Graph+LLM) |
| **Semana 3** | 23/fev → 27/fev | 33 | **Finalização**: Score WSI, Gates, Notificações, Agentes IA, Integrações (Apify) |

**Duração total:** 3 semanas (15 dias úteis) — 09/fev a 27/fev/2026

### Caminho Crítico
```
Auth → Criação de Vaga → Roteiro WSI (Modal) → Mapeamento → Perguntas WSI → WhatsApp → Triagem → Score → Gates → Agendamento
```

---

## CHECKLIST DE ENTREGA MVP

### Recrutador consegue:
- [ ] Fazer login
- [ ] Criar/editar vaga via formulário
- [ ] Configurar roteiro de triagem WSI via modal (Preview Vaga → Roteiro de Triagem → Editar)
- [ ] Buscar candidatos (base + global)
- [ ] Adicionar candidatos à vaga
- [ ] Visualizar kanban com drag-and-drop
- [ ] Aprovar candidatos mapeados (Gate 1)
- [ ] Ver score WSI após triagem
- [ ] Aprovar/reprovar candidatos triados (Gate 2)
- [ ] Ver entrevista agendada no calendário
- [ ] Receber notificações

### LIA consegue:
- [ ] Gerar perguntas de triagem WSI automaticamente
- [ ] Contatar candidato via WhatsApp
- [ ] Conduzir triagem conversacional
- [ ] Calcular score WSI (backend)
- [ ] Gerar parecer textual
- [ ] Agendar entrevista automaticamente
- [ ] Enviar feedback para reprovados

---

# CARDS JIRA DETALHADOS

> A partir daqui estão os **141 cards MVP ativos** + 50 pós-MVP + 3 cancelados + 3 removidos/consolidados = 197 cards detalhados.

---

## RESUMO EXECUTIVO

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                VISÃO GERAL DOS CARDS MVP                                      │
│                             (Atualizado: 09 Fevereiro 2026)                                   │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                │
│   FLUXO CORE MVP:                                                                              │
│   ─────────────────                                                                            │
│   Recrutador cria vaga (formulário) → Configura roteiro WSI (modal) → Busca candidatos        │
│   → Aprova mapeados (Gate 1) → LIA contata via WhatsApp → LIA faz triagem                     │
│   → Recrutador aprova/reprova triados (Gate 2) → LIA agenda entrevista                        │
│                                                                                                │
│   CRONOGRAMA: 3 SEMANAS (09/fev a 27/fev)                                                     │
│   ──────────────────────────────────────────                                                  │
│   │ Semana 1 │ 61 cards │ 09-13/fev │ Fundação: Auth, Kanban, Mapeamento, Integrações       │ │
│   │ Semana 2 │ 47 cards │ 16-20/fev │ Core: WSI, Triagem, Templates, Agendamento            │ │
│   │ Semana 3 │ 33 cards │ 23-27/fev │ Finalização: Score, Gates, Notificações, Agentes      │ │
│   └──────────┴──────────┴───────────┴───────────────────────────────────────────────────────┘│
│                                                                                                │
│   DISTRIBUIÇÃO POR ÉPICO (MVP):                                                                │
│   ──────────────────────────────                                                               │
│   │ É1:  Autenticação           │  6 cards │ Sprint 1   │ 🔧 0 prontos │                  │  │
│   │ É3:  Busca/Mapeamento       │ 13 cards │ Sprint 1-2 │ ✅ 5 prontos │ 12 S1 + 1 S2     │  │
│   │ É4:  Geração Perguntas WSI  │  8 cards │ Sprint 2   │ 🔧 0 prontos │ 5 WSI + 3 do É2  │  │
│   │ É5:  Triagem WhatsApp       │ 12 cards │ Sprint 2   │ 🔧 0 prontos │ TRI-011 pós      │  │
│   │ É6:  Score WSI              │  8 cards │ Sprint 3   │ 🔧 0 prontos │                  │  │
│   │ É7:  Gates Aprovação        │  8 cards │ Sprint 3   │ 🔧 0 prontos │                  │  │
│   │ É8:  Templates              │  8 cards │ Sprint 2   │ 🔧 0 prontos │                  │  │
│   │ É9:  Agendamento            │  8 cards │ Sprint 2   │ 🔧 0 prontos │                  │  │
│   │ É10: Notificações           │  6 cards │ Sprint 3   │ 🔧 0 prontos │ NOT-007 pós      │  │
│   │ É11: Kanban/Tabela          │ 29 cards │ Sprint 1   │ 🔧 0 prontos │ KAN-005 rem      │  │
│   │ É14: Integrações MVP        │ 27 cards │ Sprint 1-3 │ 🔧 0 prontos │ 5 pós + 1 cons   │  │
│   │ É15: Agentes IA             │  8 cards │ Sprint 3   │ 🔧 0 prontos │                  │  │
│   └─────────────────────────────┴──────────┴────────────┴──────────────┘                  │  │
│                                                                                                │
│   ÉPICOS PÓS-MVP:                                                                             │
│   ──────────────────                                                                           │
│   │ É2:  Wizard Conversacional  │ 11 cards │ Pós-MVP │ 3 migrados → É4                    │  │
│   │ É12: JD/Wizard Avançado     │  5 cards │ Pós-MVP │ Preview JD + serviços avançados     │  │
│   │ É13: Config Avançadas       │  6 cards │ Pós-MVP │ Configurações LIA + importação      │  │
│   │ É16: Otimização Estatística │  8 cards │ Pós-MVP │ Dashboard, classificação, WRF       │  │
│   │ É17: Base de Critérios      │  4 cards │ Pós-MVP │ Schema, LLM, evidências (+3 canc.)  │  │
│   │ É18: Aprendizado Avançado   │  6 cards │ Pós-MVP │ Excludentes, enriquecimento, A/B    │  │
│   │ É19: Observabilidade        │  2 cards │ Pós-MVP │ Documentação + dashboard             │  │
│   │ Cards individuais adiados   │  8 cards │ Pós-MVP │ MAP-014, TRI-011, NOT-007, INTs     │  │
│   └─────────────────────────────┴──────────┴─────────┴────────────────┘                   │  │
│                                                                                                │
│   TOTAIS:                                                                                      │
│   ────────                                                                                     │
│   MVP: 141 cards ativos (61 Sprint1 + 47 Sprint2 + 33 Sprint3)                                │
│   Pós-MVP: 50 cards ativos                                                                     │
│   Cancelados: 3 cards (WDT-017, 019, 020 — sistema auto-evolutivo)                            │
│   Removidos/Consolidados: 3 cards (WSI-004, KAN-005, INT-MSG-001)                             │
│   TOTAL GERAL: 197 cards                                                                       │
│                                                                                                │
│   PROGRESSO: ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 0% - Início do desenvolvimento                   │
│                                                                                                │
│   Decisões de alinhamento (06-09/02/2026):                                                     │
│   • É2 (Wizard Conversacional) adiado — MVP usa formulário + modal de roteiro WSI             │
│   • É12 (JD/Wizard Avançado) e É13 (Config Avançadas) movidos para Pós-MVP                   │
│   • É16-É19 (Talent Funnel WDT) categorizados como Pós-MVP                                   │
│   • É4 corrigido: 8 cards (5 WSI + 3 WIZ migrados de É2)                                     │
│   • MAP-013/WDT-005 movido de Sprint 1 para Sprint 2 (conforme YAML)                         │
│                                                                                                │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## MAPA DE CARDS POR SPRINT

### SPRINT 1 — Semana 1 (09-13/fev) — FUNDAÇÃO (61 cards)

**É1: Autenticação (6 cards)**

| Card | Nome | Resumo | Tipo | Complexidade |
|------|------|--------|------|-------------|
| AUTH-001 | Tela de Login | Login com email/senha, branding dinâmico por tenant | Frontend | Baixa (3) |
| AUTH-002 | Integração WorkOS SSO | SSO SAML/OIDC para clientes enterprise via WorkOS | Integração | Alta (8) |
| AUTH-003 | Middleware de Autenticação JWT | Validação JWT em rotas protegidas, extração user/company | Backend | Média (5) |
| AUTH-004 | Gestão de Sessão e Refresh Token | Access/refresh tokens, rotação, revogação via Redis | Backend | Média (5) |
| AUTH-005 | Wildcard SSL + Google Cloud Multi-Brand | SSL wildcard *.wedotalent.cc, DNS, middleware tenant | Infraestrutura | Média (5) |
| AUTH-006 | Revisão Final de Design pelo Lucas | Revisão assets visuais: logos, paleta, ícones, white label | Design | Baixa (3) |

**É3: Busca e Mapeamento (12 cards — MAP-013 no Sprint 2)**

| Card | Nome | Resumo | Tipo | Complexidade |
|------|------|--------|------|-------------|
| MAP-001 | Lista de Candidatos da Base | Componente de listagem de candidatos com dados básicos | Frontend | Média (5) |
| MAP-002 | Busca Semântica ES + PG Vector + WRF | Engine de busca combinando Elasticsearch + embeddings + WRF | Backend | Alta (8) |
| MAP-003 | Filtros Avançados | Filtros por localização, skills, experiência, shortlisted | Full-Stack | Média (5) |
| MAP-004 | Adicionar Candidato à Vaga | Ação de vincular candidato encontrado ao pipeline da vaga | Full-Stack | Média (5) |
| MAP-005 | Matching Score IA | Score de compatibilidade candidato-vaga via LLM | AI | Alta (8) |
| MAP-006 | Sugestões Proativas LIA | LIA sugere candidatos proativamente baseado no perfil da vaga | AI | Alta (8) |
| MAP-007 | Endpoint Busca Paginada (WDT-001) | API retornando 10 candidatos por vez com paginação cursor | Backend | Média (5) |
| MAP-008 | Paginação On-Demand (WDT-002) | Botão "Carregar mais 10" acumulando exclude_ids | Frontend | Baixa (3) |
| MAP-009 | Exclusão de IDs no ES (WDT-003) | Adaptar query ES para excluir candidatos já exibidos | Backend | Baixa (3) |
| MAP-010 | Exclusão de IDs no PG Vector (WDT-004) | Adaptar query PG Vector para excluir candidatos já exibidos | Backend | Baixa (2) |
| MAP-011 | API Feedback Like/Dislike (WDT-006) | Endpoint para registrar feedback positivo/negativo do recrutador | Backend | Média (5) |
| MAP-012 | Componente Like/Dislike (WDT-007) | Botões thumb-up/thumb-down no card de candidato | Frontend | Baixa (3) |

**É11: Kanban e Tabela de Candidatos (29 cards)**

| Card | Nome | Resumo | Tipo | Complexidade |
|------|------|--------|------|-------------|
| KAN-001 | Estrutura do Kanban 4 Colunas | Layout Kanban: Funil, Triagem, Entrevista, Reprovados | Frontend | Alta (8) |
| KAN-002 | Card de Candidato | Card resumido: nome, score, skills, localização, atividade | Frontend | Média (5) |
| KAN-003 | Drag-and-Drop entre Colunas | Arrastar candidatos entre etapas do pipeline | Frontend | Alta (8) |
| KAN-004 | Menu de Ações do Card | Context menu: ver perfil, agendar, reprovar, mover | Frontend | Média (5) |
| KAN-006 | Badge de Score WSI no Card | Indicador visual do score WSI no card do candidato | Frontend | Baixa (3) |
| KAN-007 | Filtro por Status/Etapa | Filtrar candidatos por status dentro do Kanban | Frontend | Média (5) |
| KAN-008 | Busca de Candidato por Nome | Campo de busca rápida por nome no Kanban | Frontend | Baixa (3) |
| KAN-010 | Feedback Implícito em Transições | Registrar feedback automático quando candidato muda de etapa | Backend | Média (5) |
| KAN-011 | Disparar Triagem em Lote | Iniciar triagem WSI para múltiplos candidatos de uma vaga | Full-Stack | Média (5) |
| KAN-012 | Solicitar Novos Candidatos Refinados | Pedir mais candidatos com critérios ajustados via LIA | AI + Full-Stack | Alta (8) |
| KAN-013 | Buscar Candidatos Similares | Encontrar candidatos similares a um selecionado via IA | AI + Full-Stack | Alta (8) |
| TAB-001 | Tabela de Candidatos | View alternativa ao Kanban em formato tabular | Frontend | Alta (8) |
| TAB-002 | Colunas Ordenáveis | Ordenação por nome, score, data, status nas colunas | Frontend | Baixa (3) |
| TAB-003 | Seleção Múltipla (Checkbox) | Checkboxes para selecionar vários candidatos | Frontend | Baixa (3) |
| TAB-004 | Paginação | Paginação da tabela de candidatos | Frontend | Baixa (3) |
| TAB-005 | Barra de Ações em Massa | Barra de ações para candidatos selecionados em lote | Frontend | Média (5) |
| PRV-001 | Preview Lateral do Candidato | Painel lateral com detalhes do candidato selecionado | Frontend | Alta (8) |
| PRV-002 | Tab Perfil | Aba com dados básicos, experiência, formação | Frontend | Média (5) |
| PRV-003 | Tab Atividades | Aba com histórico de interações e movimentações | Frontend | Média (5) |
| PRV-004 | Tab Arquivos | Aba com CV, documentos e anexos do candidato | Frontend | Média (5) |
| PRV-005 | Tab Parecer LIA | Aba com análise e parecer gerado pela LIA | Frontend | Média (5) |
| VAG-001 | Tabela de Vagas | Listagem de vagas com título, status, candidatos, data | Frontend | Média (5) |
| VAG-002 | Tabs de Status | Abas: Ativas, Pausadas, Fechadas para filtrar vagas | Frontend | Baixa (3) |
| VAG-003 | Menu de Ações da Vaga | Context menu: editar, pausar, duplicar, arquivar | Frontend | Baixa (3) |
| VAG-004 | Pausar/Ativar Vaga | Toggle de status ativo/pausado com confirmação | Full-Stack | Baixa (3) |
| VAG-005 | Duplicar Vaga | Criar nova vaga baseada em uma existente | Full-Stack | Baixa (3) |
| VAG-006 | Arquivar Vaga | Mover vaga para arquivo com motivo | Full-Stack | Baixa (3) |
| VAG-007 | Contador de Candidatos por Etapa | Badge com quantidade de candidatos em cada etapa | Frontend | Baixa (3) |
| VAG-008 | Navegação Vaga → Kanban | Click na vaga abre Kanban com candidatos filtrados | Frontend | Baixa (2) |

**É14: Integrações — WorkOS + Twilio (14 cards)**

| Card | Nome | Resumo | Tipo | Complexidade |
|------|------|--------|------|-------------|
| INT-WOS-001 | Configurar WorkOS Account | Setup da conta WorkOS, API keys, environments | Integração | Baixa (3) |
| INT-WOS-002 | SSO SAML/OIDC | Implementar fluxo SSO com SAML 2.0 e OIDC | Backend | Alta (8) |
| INT-WOS-003 | Directory Sync SCIM | Sincronização de diretório via SCIM para provisioning | Backend | Alta (8) |
| INT-WOS-004 | MFA Enforcement | Forçar autenticação multi-fator por política de tenant | Backend | Média (5) |
| INT-WOS-005 | User Management SDK | Gestão de usuários via WorkOS SDK (CRUD, roles) | Backend | Média (5) |
| INT-WOS-006 | Webhook de Eventos | Processar eventos WorkOS (user created, SSO linked) | Backend | Baixa (3) |
| INT-WOS-007 | Admin Portal | Portal admin para gestão de SSO e diretório | Frontend | Alta (8) |
| INT-TWI-001 | Configurar Twilio Account | Setup conta Twilio, API keys, WhatsApp sandbox | Integração | Baixa (3) |
| INT-TWI-002 | Sandbox WhatsApp | Ambiente de teste WhatsApp via Twilio sandbox | Backend | Baixa (3) |
| INT-TWI-003 | Número de Produção | Provisionar número WhatsApp de produção verificado | Integração | Baixa (3) |
| INT-TWI-004 | Webhook de Mensagens | Receber mensagens WhatsApp via webhook Twilio | Backend | Média (5) |
| INT-TWI-005 | Templates Aprovados Meta | Submeter e gerenciar templates aprovados pelo Meta | Integração | Média (5) |
| INT-TWI-006 | Status Delivery Reports | Rastrear status de entrega das mensagens (sent/delivered/read) | Backend | Baixa (3) |
| INT-TWI-007 | Rate Limiting e Filas | Controle de taxa de envio e fila de mensagens | Backend | Média (5) |

### SPRINT 2 — Semana 2 (16-20/fev) — CORE (47 cards)

**É3: Busca/Mapeamento (1 card)**

| Card | Nome | Resumo | Tipo | Complexidade |
|------|------|--------|------|-------------|
| MAP-013 | Remover Ordenação por Ranking (WDT-005) | Remover sort automático por score para evitar viés | Frontend | Baixa (2) |

**É4: Geração de Perguntas WSI (8 cards)**

| Card | Nome | Resumo | Tipo | Complexidade |
|------|------|--------|------|-------------|
| WSI-001 | Motor de Geração de Perguntas | Engine IA para gerar perguntas de triagem por bloco WSI | AI | Muito Alta (13) |
| WSI-002 | Blocos de Metodologia WSI | Blocos 2-5 WSI: empresa, elegibilidade, técnico, comportamental | Backend | Alta (8) |
| WSI-003 | Preview de Perguntas | Visualização das perguntas geradas antes de aprovar | Frontend | Média (5) |
| WSI-005 | Aprovação de Perguntas | Recrutador aprova/rejeita perguntas geradas pela LIA | Full-Stack | Baixa (3) |
| WSI-006 | Edição via Prompt Conversacional | Editar perguntas WSI pedindo alterações em linguagem natural | AI + Full-Stack | Alta (8) |
| WIZ-008 | Formulário de Edição Completa (do É2) | Formulário completo para edição de todos os campos da vaga | Full-Stack | Alta (8) |
| WIZ-012 | Estágio de Perguntas WSI (do É2) | Interface do estágio de perguntas no wizard | Frontend | Alta (8) |
| WIZ-013 | Quality Gates WSI (do É2) | Validação de qualidade mínima das perguntas WSI | Backend | Média (5) |

**É5: Triagem WhatsApp (12 cards)**

| Card | Nome | Resumo | Tipo | Complexidade |
|------|------|--------|------|-------------|
| TRI-001 | Config WhatsApp Business API | Configurar provider WhatsApp com abstração multi-provider | Integração | Alta (8) |
| TRI-002 | Envio de Mensagem Inicial | Enviar primeira mensagem de abordagem ao candidato | Backend | Média (5) |
| TRI-003 | Webhook de Recebimento | Receber e processar respostas dos candidatos via webhook | Backend | Média (5) |
| TRI-004 | Fluxo Conversacional LIA | LIA conduz triagem WSI via conversa natural no WhatsApp | AI | Muito Alta (13) |
| TRI-005 | Persistência de Conversa | Salvar histórico completo da conversa com metadados | Backend | Média (5) |
| TRI-006 | Tela de Monitoramento | Dashboard para acompanhar conversas de triagem em tempo real | Frontend | Alta (8) |
| TRI-007 | Timeout e Retentativas | Reenvio automático após timeout, com limite de tentativas | Backend | Média (5) |
| TRI-008 | Opt-out e Consentimento LGPD | Mecanismo de opt-out e registro de consentimento LGPD | Backend | Média (5) |
| TRI-009 | Templates de Mensagem WhatsApp | Templates de mensagem para triagem aprovados pelo Meta | Full-Stack | Média (5) |
| TRI-010 | Envio em Massa (Bulk) | Disparar triagem para múltiplos candidatos simultaneamente | Full-Stack | Alta (8) |
| TRI-013 | Reporte de Problemas pelo Candidato | Candidato pode reportar dificuldades técnicas durante triagem | Full-Stack | Média (5) |
| TRI-014 | Pesquisa de Alternativas a Twilio | Avaliação de providers alternativos → Recomendação: Gupshup | Pesquisa | Baixa (3) |

**É8: Templates de Comunicação (8 cards)**

| Card | Nome | Resumo | Tipo | Complexidade |
|------|------|--------|------|-------------|
| TPL-001 | Template de Abordagem Inicial | Mensagem padrão de primeiro contato com candidato | Full-Stack | Baixa (3) |
| TPL-002 | Template de Agendamento | Mensagem para convidar candidato para entrevista | Full-Stack | Baixa (3) |
| TPL-003 | Template de Confirmação | Mensagem de confirmação de agendamento | Full-Stack | Baixa (3) |
| TPL-004 | Template Pós-Entrevista | Mensagem de follow-up após entrevista | Full-Stack | Baixa (3) |
| TPL-005 | Editor de Templates (WYSIWYG) | Editor visual para criar e customizar templates | Frontend | Alta (8) |
| TPL-006 | Variáveis Dinâmicas | Suporte a variáveis {{nome}}, {{vaga}}, {{data}} nos templates | Backend | Média (5) |
| TPL-007 | Preview de Template | Pré-visualização do template renderizado com dados reais | Frontend | Baixa (3) |
| TPL-008 | Sync Templates WhatsApp com Meta | Sincronizar templates com Meta Business Manager para aprovação | Integração | Média (5) |

**É9: Agendamento Automático (8 cards)**

| Card | Nome | Resumo | Tipo | Complexidade |
|------|------|--------|------|-------------|
| AGE-001 | Integração Microsoft Graph | Conectar com MS Graph para calendários e Teams | Integração | Muito Alta (13) |
| AGE-002 | Consulta de Disponibilidade | Verificar slots livres no calendário do recrutador | Backend | Alta (8) |
| AGE-003 | Sugestão Inteligente de Horários | IA sugere melhores horários considerando timezone e preferências | AI | Alta (8) |
| AGE-004 | Criação de Evento Teams | Criar reunião Teams automaticamente com link | Backend | Média (5) |
| AGE-005 | Confirmação do Candidato via WhatsApp | Candidato confirma entrevista respondendo no WhatsApp | Full-Stack | Média (5) |
| AGE-006 | Reagendamento | Fluxo para remarcar entrevista com nova disponibilidade | Full-Stack | Média (5) |
| AGE-007 | Lembretes Automáticos | Lembrete 24h antes para recrutador e candidato | Backend | Baixa (3) |
| AGE-008 | Cancelamento com Notificação | Cancelar entrevista notificando todas as partes | Full-Stack | Baixa (3) |

**É14: Integrações — MS Graph + LLM (10 cards)**

| Card | Nome | Resumo | Tipo | Complexidade |
|------|------|--------|------|-------------|
| INT-MSG-002 | OAuth Flow Microsoft | Fluxo OAuth 2.0 para autorização Microsoft Graph | Backend | Média (5) |
| INT-MSG-003 | Calendar API | Integração com Calendar API para ler/criar eventos | Backend | Média (5) |
| INT-MSG-004 | Teams Meeting API | Criar reuniões Teams programaticamente | Backend | Média (5) |
| INT-MSG-006 | Token Refresh | Auto-refresh de tokens Microsoft expirados | Backend | Baixa (3) |
| INT-LLM-002 | Cliente Google Gemini | Client SDK para chamadas ao Google Gemini | Backend | Média (5) |
| INT-LLM-005 | Gestão de Prompts (Versioning) | Versionamento e gestão de prompts LLM | Backend | Média (5) |
| INT-LLM-006 | Cache de Respostas LLM | Cache Redis para respostas LLM frequentes | Backend | Média (5) |
| INT-LLM-007 | Monitoramento de Custos | Dashboard de custos por modelo/tenant/operação | Backend | Média (5) |
| INT-LLM-008 | Rate Limiting LLM | Limitar chamadas LLM por tenant e por minuto | Backend | Baixa (3) |
| INT-LLM-009 | Logging de Conversas | Registrar todas interações LLM para auditoria | Backend | Baixa (3) |

### SPRINT 3 — Semana 3 (23-27/fev) — FINALIZAÇÃO (33 cards)

**É6: Score WSI (8 cards)**

| Card | Nome | Resumo | Tipo | Complexidade |
|------|------|--------|------|-------------|
| SCO-001 | Cálculo de Score WSI | Algoritmo de cálculo do score por dimensão e geral | AI | Muito Alta (13) |
| SCO-002 | Modelo Big Five Comportamental | Avaliação de traços comportamentais via Big Five | AI | Alta (8) |
| SCO-003 | Avaliação Bloom/Dreyfus | Classificação de nível técnico via taxonomia Bloom/Dreyfus | AI | Alta (8) |
| SCO-004 | Parecer Textual LIA | Parecer narrativo gerado pela LIA sobre o candidato | AI | Alta (8) |
| SCO-005 | Visualização de Score (Radar Chart) | Gráfico radar com dimensões do score WSI | Frontend | Média (5) |
| SCO-006 | Breakdown de Dimensões WSI | Detalhamento por dimensão com evidências e justificativas | Frontend | Média (5) |
| SCO-007 | Comparação entre Candidatos | Comparar scores de múltiplos candidatos lado a lado | Full-Stack | Alta (8) |
| SCO-008 | Histórico de Scores | Registro histórico de scores para auditoria e evolução | Backend | Média (5) |

**É7: Gates de Aprovação (8 cards)**

| Card | Nome | Resumo | Tipo | Complexidade |
|------|------|--------|------|-------------|
| GAT-001 | Gate 1: Aprovar Mapeados | Portão para aprovar candidatos após mapeamento | Full-Stack | Alta (8) |
| GAT-002 | Gate 2: Aprovar Triados | Portão para aprovar candidatos após triagem WSI | Full-Stack | Alta (8) |
| GAT-003 | Modal de Reprovação com Motivo | Modal para registrar motivo da reprovação | Frontend | Baixa (3) |
| GAT-004 | Geração de Feedback LIA | LIA gera feedback construtivo para candidatos reprovados | AI | Alta (8) |
| GAT-005 | Envio Automático de Feedback | Enviar feedback de reprovação automaticamente | Backend | Média (5) |
| GAT-006 | Aprovação/Reprovação em Massa | Aprovar ou reprovar múltiplos candidatos de uma vez | Full-Stack | Média (5) |
| GAT-007 | Histórico de Decisões (Audit Trail) | Log de todas decisões de aprovação/reprovação | Backend | Média (5) |
| GAT-008 | Aprendizagem IA sobre Aprovações | IA aprende padrões de aprovação/reprovação do recrutador | AI + Backend | Alta (8) |

**É10: Notificações (6 cards)**

| Card | Nome | Resumo | Tipo | Complexidade |
|------|------|--------|------|-------------|
| NOT-001 | Sistema de Notificações (Bell Icon) | Ícone de sino com dropdown de notificações | Full-Stack | Alta (8) |
| NOT-002 | Notificações em Tempo Real (WebSocket) | Push de notificações via WebSocket | Backend | Alta (8) |
| NOT-003 | Preferências de Notificação | Configurar quais notificações receber e por qual canal | Full-Stack | Média (5) |
| NOT-004 | Notificações Push (PWA) | Push notifications via Service Worker (PWA) | Backend | Alta (8) |
| NOT-005 | Histórico de Notificações | Lista completa de notificações passadas com filtros | Full-Stack | Média (5) |
| NOT-006 | Badge de Não Lidas | Contador visual de notificações não lidas | Frontend | Baixa (2) |

**É15: Agentes IA (8 cards)**

| Card | Nome | Resumo | Tipo | Complexidade |
|------|------|--------|------|-------------|
| AGT-001 | Agente Avaliador WSI | Agente especializado em avaliar respostas WSI | AI | Muito Alta (13) |
| AGT-002 | Agente de Triagem Curricular | Agente para análise e triagem de currículos | AI | Muito Alta (13) |
| AGT-003 | Agente de Agendamento | Agente para gerenciar agendamentos automaticamente | AI | Alta (8) |
| AGT-004 | Orquestrador de Pipeline Chat | Orquestrador central dos agentes no pipeline de chat | AI | Alta (8) |
| TRI-012 | Serviço de Pré-Qualificação | Serviço backend para pré-qualificação automatizada | Backend | Alta (8) |
| DAT-001 | Sistema de Solicitação de Dados | Interface para LIA solicitar dados adicionais ao recrutador | Frontend | Alta (8) |
| ENT-001 | Análise de Transcrição de Entrevista | Analisar transcrição de entrevista e extrair insights | Backend | Muito Alta (13) |
| KAN-009 | Componentes Kanban Modulares | Componentes reutilizáveis e modulares do Kanban | Frontend | Muito Alta (13) |

**É14: Integrações — Apify (3 cards)**

| Card | Nome | Resumo | Tipo | Complexidade |
|------|------|--------|------|-------------|
| INT-APY-001 | Configurar Apify Account | Setup conta Apify para web scraping | Integração | Baixa (3) |
| INT-APY-002 | LinkedIn Scraper Actor | Actor Apify para scraping de perfis LinkedIn | Backend | Média (5) |
| INT-APY-003 | Integração com Sourcing Agent | Conectar Apify com agente de sourcing da LIA | AI | Alta (8) |

### CARDS PÓS-MVP (50 cards ativos)

**É2: Wizard Conversacional (11 cards)**

| Card | Nome | Resumo | Tipo | Complexidade |
|------|------|--------|------|-------------|
| WIZ-001 | Interface Chat Conversacional | Chat para criação de vaga via conversa com LIA | Frontend | Alta (8) |
| WIZ-002 | Orquestrador de Intenções | Classificador de intenções do recrutador no chat | AI | Muito Alta (13) |
| WIZ-003 | Serviço de Insights de Mercado | Dados de mercado para sugestões contextualizadas | Backend | Alta (8) |
| WIZ-004 | Gerador de Job Description | Geração automática de JD baseada na conversa | AI | Alta (8) |
| WIZ-005 | Salvamento de Rascunho | Auto-save do rascunho durante criação conversacional | Backend | Baixa (3) |
| WIZ-006 | Sugestões Clicáveis | Chips/botões de sugestão contextual no chat | Frontend | Média (5) |
| WIZ-007 | Preview da Vaga (Live) | Preview em tempo real da vaga sendo criada | Full-Stack | Média (5) |
| WIZ-009 | Skip Calibração Conversacional | Pular etapas já preenchidas no wizard conversacional | Full-Stack | Baixa (3) |
| WIZ-010 | Estágio de Salário Interativo | Interface interativa para definir faixa salarial | Frontend | Média (5) |
| WIZ-011 | Estágio de Competências | Interface para definir competências requeridas | Frontend | Alta (8) |
| WIZ-014 | Revisão Metodologia Wizard com André | Validação da metodologia conversacional com especialista | Processo | Baixa (2) |

**É12: JD/Wizard Avançado (5 cards)**

| Card | Nome | Resumo | Tipo | Complexidade |
|------|------|--------|------|-------------|
| JD-001 | Preview de JD com Sugestões LIA | Preview da JD com sugestões inline da LIA | Frontend | Média (5) |
| JD-002 | JD Completo para Publicação | JD formatada e pronta para publicação em job boards | Frontend | Média (5) |
| JDW-001 | Interação com Sugestões LIA | Backend para processar aceite/rejeição de sugestões | Backend | Alta (8) |
| JDW-002 | Análise de Compensação de Mercado | Análise salarial de mercado por cargo/região | Backend | Alta (8) |
| JDW-003 | Insights de Mercado para Vagas | Dados de mercado (demanda, concorrência, tendências) | Backend | Média (5) |

**É13: Config Avançadas (6 cards)**

| Card | Nome | Resumo | Tipo | Complexidade |
|------|------|--------|------|-------------|
| CFG-001 | LIA Field Toggles | On/Off por campo para controlar sugestões da LIA | Frontend | Média (5) |
| CFG-002 | Verificação de Completude | Validar se vaga tem todos campos obrigatórios preenchidos | Backend | Baixa (3) |
| CFG-003 | Configuração de Jornada | Customizar etapas do pipeline por empresa | Frontend | Média (5) |
| CFG-004 | Hub de Comunicação | Central de comunicação multi-canal (email + WhatsApp) | Frontend | Alta (8) |
| CFG-005 | Dados da Empresa para LIA | Configurar dados da empresa para contextualizar LIA | Frontend | Média (5) |
| IMP-001 | Importação Inteligente | Importar vagas de outras plataformas/ATS | Frontend | Alta (8) |

**É16: Otimização Estatística de Busca (8 cards)** — ver detalhes no Índice de Cards (É16)

**É17: Base de Critérios de Avaliação (4 cards ativos)** — ver detalhes no Índice de Cards (É17)

**É18: Aprendizado e Features Avançadas (6 cards)** — ver detalhes no Índice de Cards (É18)

**É19: Observabilidade e Documentação (2 cards)** — ver detalhes no Índice de Cards (É19)

**Cards individuais adiados (8 cards)**

| Card | Nome | Resumo | Tipo | Complexidade |
|------|------|--------|------|-------------|
| MAP-014 | Revisão Qualidade de Busca com André | Sessão com especialista para validar qualidade da busca | Processo | Baixa (2) |
| TRI-011 | Pré-Qualificação Automatizada | Filtro automático antes da triagem WSI completa | Backend | Alta (8) |
| NOT-007 | Notificações via Microsoft Teams | Enviar notificações ao recrutador via MS Teams | Integração | Alta (8) |
| INT-LLM-001 | Cliente Anthropic Claude | Client SDK para chamadas ao Claude | Backend | Média (5) |
| INT-LLM-003 | Router de Modelos | Roteamento inteligente entre modelos LLM | Backend | Alta (8) |
| INT-LLM-004 | Fallback entre Modelos | Fallback automático se modelo principal falhar | Backend | Média (5) |
| INT-MSG-005 | Webhook de Eventos MS Graph | Receber eventos de calendário via webhook | Backend | Média (5) |
| INT-MSG-007 | Multi-tenant Calendar | Suporte a calendários múltiplos por tenant | Backend | Alta (8) |

### CARDS CANCELADOS (3 cards — É17)

| Card | Motivo |
|------|--------|
| WDT-017 | Cancelado — Interface admin gestão de critérios (sistema auto-evolutivo) |
| WDT-019 | Cancelado — Dashboard gestão e métricas de critérios (sistema auto-evolutivo) |
| WDT-020 | Cancelado — Alimentação inicial com RH sênior (substituído por auto-seed) |

### CARDS REMOVIDOS/CONSOLIDADOS (3 cards)

| Card | Motivo |
|------|--------|
| WSI-004 | Removido — edição manual substituída por WSI-006 (prompt conversacional) |
| KAN-005 | Obsoleto — ícones de ação rápida redundantes com KAN-004 |
| INT-MSG-001 | Consolidado em AGE-001 — config Azure unificada |

**RESUMO:**
- **Sprint 1:** 61 cards (Fundação)
- **Sprint 2:** 47 cards (Core)
- **Sprint 3:** 33 cards (Finalização)
- **Pós-MVP:** 50 cards ativos (É2, É12, É13, É16-É19 + cards individuais adiados)
- **Cancelados:** 3 cards (WDT-017, WDT-019, WDT-020)
- **Removidos/Consolidados:** 3 cards (WSI-004, KAN-005, INT-MSG-001)
- **TOTAL MVP:** 141 cards ativos
- **TOTAL GERAL:** 197 cards (141 MVP + 50 pós-MVP + 3 cancelados + 3 removidos)

---

## CONVENÇÕES DE NOMENCLATURA

| Prefixo | Tipo | Descrição |
|---------|------|-----------|
| `[BACKEND]` | API/Lógica | Endpoints, serviços, banco de dados |
| `[FRONTEND]` | UI | Componentes, telas, interações |
| `[FULL-STACK]` | Ambos | Feature completa end-to-end |
| `[INTEGRAÇÃO]` | Externa | APIs terceiros, webhooks |
| `[AI]` | Inteligência | LLM, prompts, agentes |

---

## ÍNDICE DE CARDS

### ÉPICO 1: Autenticação (6 cards)
| Card | Título | Tipo | Fase | Sprint | Status | Notas | Backlog | Déb. Técnico |
|------|--------|------|------|--------|--------|-------|---------|-------------|
| AUTH-001 | Tela de Login | Frontend | MVP | 1 | 📋 Pendente | Branding dinâmico por tenant | P0 Crítico | — |
| AUTH-002 | Integração WorkOS SSO | Integração | MVP | 1 | 📋 Pendente | SSO SAML/OIDC enterprise | P0 Crítico | — |
| AUTH-003 | Middleware de Autenticação | Backend | MVP | 1 | 📋 Pendente | JWT em rotas protegidas | P0 Crítico | — |
| AUTH-004 | Gestão de Sessão JWT | Backend | MVP | 1 | 📋 Pendente | Refresh token + Redis | P0 Crítico | — |
| AUTH-005 | Wildcard SSL + Google Cloud Multi-Brand | Infraestrutura | MVP | 1 | 📋 Pendente | *.wedotalent.cc, DNS | P0 Crítico | — |
| AUTH-006 | Revisão Final de Design pelo Lucas | Design | MVP | 1 | 📋 Pendente | Logos, paleta, ícones | P0 Crítico | — |

### ÉPICO 2: Wizard Conversacional ⏸️ PÓS-MVP (14 cards — 0 MVP + 11 pós-MVP + 3 migrados p/ Épico 4)
> ⏸️ Épico inteiro movido para Pós-MVP (decisão 06/fev/2026). WIZ-008, WIZ-012, WIZ-013 migrados para Épico 4 (WSI).

| Card | Título | Tipo | Fase | Sprint | Status | Notas | Backlog | Déb. Técnico |
|------|--------|------|------|--------|--------|-------|---------|-------------|
| WIZ-001 | Interface Chat Conversacional | Frontend | Pós-MVP | Pós-MVP | 📦 Pós-MVP | — | P3 Baixo | — |
| WIZ-002 | Orquestrador de Intenções | AI | Pós-MVP | Pós-MVP | 📦 Pós-MVP | — | P3 Baixo | — |
| WIZ-003 | Serviço de Insights de Mercado | Backend | Pós-MVP | Pós-MVP | 📦 Pós-MVP | — | P3 Baixo | — |
| WIZ-004 | Gerador de Job Description | AI | Pós-MVP | Pós-MVP | 📦 Pós-MVP | — | P3 Baixo | — |
| WIZ-005 | Salvamento de Rascunho | Backend | Pós-MVP | Pós-MVP | 📦 Pós-MVP | — | P3 Baixo | — |
| WIZ-006 | Sugestões Clicáveis | Frontend | Pós-MVP | Pós-MVP | 📦 Pós-MVP | — | P3 Baixo | — |
| WIZ-007 | Preview da Vaga (Live) | Full-Stack | Pós-MVP | Pós-MVP | 📦 Pós-MVP | — | P3 Baixo | — |
| WIZ-008 | Formulário de Edição Completa | Full-Stack | MVP | 2 | ➡️ Migrado p/ Épico 4 | migrado do É2 | P1 Alto | Migração |
| WIZ-009 | Skip Calibração Conversacional | Full-Stack | Pós-MVP | Pós-MVP | 📦 Pós-MVP | — | P3 Baixo | — |
| WIZ-010 | Estágio de Salário Interativo | Frontend | Pós-MVP | Pós-MVP | 📦 Pós-MVP | — | P3 Baixo | — |
| WIZ-011 | Estágio de Competências | Frontend | Pós-MVP | Pós-MVP | 📦 Pós-MVP | — | P3 Baixo | — |
| WIZ-012 | Estágio de Perguntas WSI | Frontend | MVP | 2 | ➡️ Migrado p/ Épico 4 | migrado do É2 | P1 Alto | Migração |
| WIZ-013 | Quality Gates WSI | Backend | MVP | 2 | ➡️ Migrado p/ Épico 4 | migrado do É2 | P1 Alto | Migração |
| WIZ-014 | Revisão Metodologia Wizard com André | Processo/Validação | Pós-MVP | Pós-MVP | ⏸️ Pós-MVP | — | P3 Baixo | — |

### ÉPICO 3: Busca e Mapeamento (14 cards — 13 MVP + 1 pós-MVP)
| Card | Título | Tipo | Fase | Sprint | Status | Notas | Backlog | Déb. Técnico |
|------|--------|------|------|--------|--------|-------|---------|-------------|
| MAP-001 | Lista de Candidatos da Base | Frontend | MVP | 1 | ✅ Feito | 5 já prontos | P1 Alto | — |
| MAP-002 | Busca Semântica ES + PG Vector + WRF | Backend | MVP | 1 | ✅ Feito | 5 já prontos | P1 Alto | — |
| MAP-003 | Filtros Avançados (incl. shortlisted/placement) | Full-Stack | MVP | 1 | 🔧 Em progresso | — | P1 Alto | — |
| MAP-004 | Adicionar Candidato à Vaga | Full-Stack | MVP | 1 | ✅ Feito | 5 já prontos | P1 Alto | — |
| MAP-005 | Matching Score IA | AI | MVP | 1 | ✅ Feito | 5 já prontos | P1 Alto | — |
| MAP-006 | Sugestões Proativas LIA | AI | MVP | 1 | ✅ Feito | 5 já prontos | P1 Alto | — |
| MAP-007 | Endpoint Busca Paginada (WDT-001) | Backend | MVP | 1 | 📋 Pendente | WDT-001 | P2 Médio | — |
| MAP-008 | Paginação On-Demand (WDT-002) | Frontend | MVP | 1 | 📋 Pendente | WDT-002 | P2 Médio | — |
| MAP-009 | Exclusão de IDs no ES (WDT-003) | Backend | MVP | 1 | 📋 Pendente | WDT-003 | P2 Médio | — |
| MAP-010 | Exclusão de IDs no PG Vector (WDT-004) | Backend | MVP | 1 | 📋 Pendente | WDT-004 | P2 Médio | — |
| MAP-011 | API Feedback Like/Dislike (WDT-006) | Backend | MVP | 1 | 📋 Pendente | WDT-006 | P2 Médio | — |
| MAP-012 | Componente Like/Dislike (WDT-007) | Frontend | MVP | 1 | 📋 Pendente | WDT-007 | P2 Médio | — |
| MAP-013 | Remover Ordenação por Ranking (WDT-005) | Frontend | MVP | 2 | 📋 Pendente | WDT-005 | P2 Médio | Refactor |
| MAP-014 | Revisão de Qualidade de Busca com André | Processo/Validação | Pós-MVP | Pós-MVP | ⏸️ Pós-MVP | — | P2 Médio | — |

> **📄 Cards WDT detalhados:** [epic-wdt-talent-funnel.md](./epic-wdt-talent-funnel.md) — 23 cards restantes com prompts IA para Cursor/VSCode

### ÉPICO 4: Geração de Perguntas WSI (8 cards — 7 MVP + 1 removido, inclui 3 migrados do Épico 2)
> **Nota (06/fev/2026):** WIZ-008, WIZ-012, WIZ-013 migrados do Épico 2 (Wizard) para cá.

| Card | Título | Tipo | Fase | Sprint | Status | Notas | Backlog | Déb. Técnico |
|------|--------|------|------|--------|--------|-------|---------|-------------|
| WSI-001 | Motor de Geração de Perguntas | AI | MVP | 2 | 📋 Pendente | — | P1 Alto | — |
| WSI-002 | Blocos de Metodologia WSI | Backend | MVP | 2 | 📋 Pendente | Blocos 2-5 WSI | P1 Alto | — |
| WSI-003 | Preview de Perguntas | Frontend | MVP | 2 | 📋 Pendente | — | P1 Alto | — |
| WSI-004 | Edição Manual de Perguntas | Full-Stack | — | — | ❌ Removido | Substituído por WSI-006 | — | — |
| WSI-005 | Aprovação de Perguntas | Full-Stack | MVP | 2 | 📋 Pendente | — | P1 Alto | — |
| WSI-006 | Edição de Perguntas WSI via Prompt Conversacional | AI + Full-Stack | MVP | 2 | 📋 Pendente | — | P1 Alto | — |
| WIZ-008 | Formulário de Edição Completa (migrado do Épico 2) | Full-Stack | MVP | 2 | 📋 Pendente | migrado do É2 | P1 Alto | Migração |
| WIZ-012 | Estágio de Perguntas WSI (migrado do Épico 2) | Frontend | MVP | 2 | 📋 Pendente | migrado do É2 | P1 Alto | Migração |
| WIZ-013 | Quality Gates WSI (migrado do Épico 2) | Backend | MVP | 2 | 📋 Pendente | migrado do É2 | P1 Alto | Migração |

### ÉPICO 5: Triagem WhatsApp (14 cards — 12 MVP + 1 pós-MVP + 1 pesquisa)
| Card | Título | Tipo | Fase | Sprint | Status | Notas | Backlog | Déb. Técnico |
|------|--------|------|------|--------|--------|-------|---------|-------------|
| TRI-001 | Configuração WhatsApp Business API (Provider Abstrato) | Integração | MVP | 2 | 📋 Pendente | Multi-provider | P0 Crítico | — |
| TRI-002 | Envio de Mensagem Inicial | Backend | MVP | 2 | 📋 Pendente | — | P0 Crítico | — |
| TRI-003 | Webhook de Recebimento | Backend | MVP | 2 | 📋 Pendente | — | P0 Crítico | — |
| TRI-004 | Fluxo Conversacional LIA | AI | MVP | 2 | 📋 Pendente | — | P0 Crítico | — |
| TRI-005 | Persistência de Conversa | Backend | MVP | 2 | 📋 Pendente | — | P0 Crítico | — |
| TRI-006 | Transcrição da Triagem no Card de Atividade | Frontend | MVP | 2 | 📋 Pendente | — | P0 Crítico | — |
| TRI-007 | Timeout e Retentativas | Backend | MVP | 2 | 📋 Pendente | — | P0 Crítico | — |
| TRI-008 | Opt-out e Consentimento | Backend | MVP | 2 | 📋 Pendente | LGPD | P0 Crítico | — |
| TRI-009 | Templates de Mensagem | Full-Stack | MVP | 2 | 📋 Pendente | — | P0 Crítico | — |
| TRI-010 | Envio em Massa (Bulk) | Full-Stack | MVP | 2 | 📋 Pendente | — | P0 Crítico | — |
| TRI-011 | Pré-Qualificação Automatizada | Backend | Pós-MVP | Pós-MVP | ⏸️ Pós-MVP | — | P2 Médio | — |
| TRI-013 | Sistema de Reporte de Problemas pelo Candidato | Full-Stack | MVP | 2 | 📋 Pendente | — | P0 Crítico | — |
| TRI-014 | Pesquisa de Alternativas a Twilio | Pesquisa | MVP | 2 | 🔄 Pesquisa Concluída | Recomendação: Gupshup | P0 Crítico | — |

### ÉPICO 6: Score WSI (8 cards)
| Card | Título | Tipo | Fase | Sprint | Status | Notas | Backlog | Déb. Técnico |
|------|--------|------|------|--------|--------|-------|---------|-------------|
| SCO-001 | Cálculo de Score WSI | AI | MVP | 3 | 📋 Pendente | — | P1 Alto | — |
| SCO-002 | Modelo Big Five Comportamental | AI | MVP | 3 | 📋 Pendente | — | P1 Alto | — |
| SCO-003 | Avaliação Bloom/Dreyfus | AI | MVP | 3 | 📋 Pendente | — | P1 Alto | — |
| SCO-004 | Parecer Textual LIA | AI | MVP | 3 | 📋 Pendente | — | P1 Alto | — |
| SCO-005 | Visualização de Score | Frontend | MVP | 3 | 📋 Pendente | Radar chart | P1 Alto | — |
| SCO-006 | Breakdown de Dimensões | Frontend | MVP | 3 | 📋 Pendente | — | P1 Alto | — |
| SCO-007 | Comparação entre Candidatos | Full-Stack | MVP | 3 | 📋 Pendente | — | P1 Alto | — |
| SCO-008 | Histórico de Scores | Backend | MVP | 3 | 📋 Pendente | Auditoria | P1 Alto | — |

### ÉPICO 7: Gates de Aprovação (8 cards)
| Card | Título | Tipo | Fase | Sprint | Status | Notas | Backlog | Déb. Técnico |
|------|--------|------|------|--------|--------|-------|---------|-------------|
| GAT-001 | Gate 1: Aprovar Mapeados | Full-Stack | MVP | 3 | 📋 Pendente | — | P1 Alto | — |
| GAT-002 | Gate 2: Aprovar Triados | Full-Stack | MVP | 3 | 📋 Pendente | — | P1 Alto | — |
| GAT-003 | Modal de Reprovação | Frontend | MVP | 3 | 📋 Pendente | Com motivo | P1 Alto | — |
| GAT-004 | Geração de Feedback LIA | AI | MVP | 3 | 📋 Pendente | — | P1 Alto | — |
| GAT-005 | Envio de Feedback | Backend | MVP | 3 | 📋 Pendente | Automático | P1 Alto | — |
| GAT-006 | Aprovação em Massa | Full-Stack | MVP | 3 | 📋 Pendente | — | P1 Alto | — |
| GAT-007 | Histórico de Decisões | Backend | MVP | 3 | 📋 Pendente | Audit trail | P1 Alto | — |
| GAT-008 | Aprendizagem da IA sobre Aprovações/Reprovações | AI + Backend | MVP | 3 | 📋 Pendente | — | P1 Alto | — |

### ÉPICO 8: Templates de Comunicação (8 cards)
| Card | Título | Tipo | Fase | Sprint | Status | Notas | Backlog | Déb. Técnico |
|------|--------|------|------|--------|--------|-------|---------|-------------|
| TPL-001 | Template de Abordagem Inicial | Full-Stack | MVP | 2 | 📋 Pendente | — | P2 Médio | — |
| TPL-002 | Template de Agendamento | Full-Stack | MVP | 2 | 📋 Pendente | — | P2 Médio | — |
| TPL-003 | Template de Confirmação | Full-Stack | MVP | 2 | 📋 Pendente | — | P2 Médio | — |
| TPL-004 | Template Pós-Entrevista | Full-Stack | MVP | 2 | 📋 Pendente | — | P2 Médio | — |
| TPL-005 | Editor de Templates | Frontend | MVP | 2 | 📋 Pendente | WYSIWYG | P2 Médio | — |
| TPL-006 | Variáveis Dinâmicas | Backend | MVP | 2 | 📋 Pendente | {{nome}}, {{vaga}} | P2 Médio | — |
| TPL-007 | Preview de Template | Frontend | MVP | 2 | 📋 Pendente | — | P2 Médio | — |
| TPL-008 | Sincronização de Templates WhatsApp com Meta | Integração | MVP | 2 | 📋 Pendente | Meta Business Mgr | P2 Médio | — |

### ÉPICO 9: Agendamento Automático (8 cards)
| Card | Título | Tipo | Fase | Sprint | Status | Notas | Backlog | Déb. Técnico |
|------|--------|------|------|--------|--------|-------|---------|-------------|
| AGE-001 | Integração Microsoft Graph | Integração | MVP | 2 | 📋 Pendente | Calendários + Teams | P1 Alto | — |
| AGE-002 | Consulta de Disponibilidade | Backend | MVP | 2 | 📋 Pendente | — | P1 Alto | — |
| AGE-003 | Sugestão de Horários | AI | MVP | 2 | 📋 Pendente | Timezone + preferências | P1 Alto | — |
| AGE-004 | Criação de Evento Teams | Backend | MVP | 2 | 📋 Pendente | — | P1 Alto | — |
| AGE-005 | Confirmação do Candidato | Full-Stack | MVP | 2 | 📋 Pendente | Via WhatsApp | P1 Alto | — |
| AGE-006 | Reagendamento | Full-Stack | MVP | 2 | 📋 Pendente | — | P1 Alto | — |
| AGE-007 | Lembretes Automáticos | Backend | MVP | 2 | 📋 Pendente | 24h antes | P1 Alto | — |
| AGE-008 | Cancelamento | Full-Stack | MVP | 2 | 📋 Pendente | Com notificação | P1 Alto | — |

### ÉPICO 10: Notificações (7 cards — 6 MVP + 1 pós-MVP)
| Card | Título | Tipo | Fase | Sprint | Status | Notas | Backlog | Déb. Técnico |
|------|--------|------|------|--------|--------|-------|---------|-------------|
| NOT-001 | Sistema de Notificações Bell | Full-Stack | MVP | 3 | 📋 Pendente | — | P2 Médio | — |
| NOT-002 | Notificações em Tempo Real | Backend | MVP | 3 | 📋 Pendente | WebSocket | P2 Médio | — |
| NOT-003 | Preferências de Notificação | Full-Stack | MVP | 3 | 📋 Pendente | — | P2 Médio | — |
| NOT-004 | Notificações Push | Backend | MVP | 3 | 📋 Pendente | PWA | P2 Médio | — |
| NOT-005 | Histórico de Notificações | Full-Stack | MVP | 3 | 📋 Pendente | — | P2 Médio | — |
| NOT-006 | Badge de Não Lidas | Frontend | MVP | 3 | 📋 Pendente | — | P2 Médio | — |
| NOT-007 | Notificações para Recrutador via Microsoft Teams | Integração | Pós-MVP | Pós-MVP | 📋 Pendente | — | P2 Médio | — |

### ÉPICO 11: Kanban e Tabela de Candidatos (29 cards MVP + 1 removido + 1 movido p/ É15)
| Card | Título | Tipo | Fase | Sprint | Status | Notas | Backlog | Déb. Técnico |
|------|--------|------|------|--------|--------|-------|---------|-------------|
| KAN-001 | Estrutura do Kanban 4 Colunas | Frontend | MVP | 1 | 📋 Pendente | — | P2 Médio | — |
| KAN-002 | Card de Candidato | Frontend | MVP | 1 | 📋 Pendente | — | P2 Médio | — |
| KAN-003 | Drag-and-Drop entre Colunas | Frontend | MVP | 1 | 📋 Pendente | — | P2 Médio | — |
| KAN-004 | Menu de Ações do Card | Frontend | MVP | 1 | 📋 Pendente | — | P2 Médio | — |
| KAN-005 | Ícones de Ação Rápida | Frontend | — | — | ⚠️ Obsoleto | Redundante com KAN-004 | — | Obsoleto |
| KAN-006 | Badge de Score WSI | Frontend | MVP | 1 | 📋 Pendente | — | P2 Médio | — |
| KAN-007 | Filtro por Status | Frontend | MVP | 1 | 📋 Pendente | — | P2 Médio | — |
| KAN-008 | Busca de Candidato | Frontend | MVP | 1 | 📋 Pendente | — | P2 Médio | — |
| ~~KAN-009~~ | ~~Componentes Kanban Modulares~~ | Frontend | — | 3 | ➡️ Movido p/ É15 | Contabilizado em É15 | — | — |
| KAN-010 | Feedback Implícito em Transições | Backend | MVP | 1 | 📋 Pendente | — | P2 Médio | — |
| KAN-011 | Disparar Triagem em Lote Dentro da Vaga | Full-Stack | MVP | 1 | 📋 Pendente | — | P2 Médio | — |
| KAN-012 | Solicitar Novos Candidatos com Critérios Refinados | AI + Full-Stack | MVP | 1 | 📋 Pendente | — | P2 Médio | — |
| KAN-013 | Buscar Candidatos Similares | AI + Full-Stack | MVP | 1 | 📋 Pendente | — | P2 Médio | — |
| TAB-001 | Tabela de Candidatos | Frontend | MVP | 1 | 📋 Pendente | — | P2 Médio | — |
| TAB-002 | Colunas Ordenáveis | Frontend | MVP | 1 | 📋 Pendente | — | P2 Médio | — |
| TAB-003 | Seleção Múltipla | Frontend | MVP | 1 | 📋 Pendente | — | P2 Médio | — |
| TAB-004 | Paginação | Frontend | MVP | 1 | 📋 Pendente | — | P2 Médio | — |
| TAB-005 | Ações em Massa (Barra) | Frontend | MVP | 1 | 📋 Pendente | — | P2 Médio | — |
| PRV-001 | Preview Lateral do Candidato | Frontend | MVP | 1 | 📋 Pendente | — | P2 Médio | — |
| PRV-002 | Tab Perfil | Frontend | MVP | 1 | 📋 Pendente | — | P2 Médio | — |
| PRV-003 | Tab Atividades | Frontend | MVP | 1 | 📋 Pendente | — | P2 Médio | — |
| PRV-004 | Tab Arquivos | Frontend | MVP | 1 | 📋 Pendente | — | P2 Médio | — |
| PRV-005 | Tab Parecer LIA | Frontend | MVP | 1 | 📋 Pendente | — | P2 Médio | — |
| VAG-001 | Tabela de Vagas | Frontend | MVP | 1 | 📋 Pendente | — | P2 Médio | — |
| VAG-002 | Tabs de Status | Frontend | MVP | 1 | 📋 Pendente | — | P2 Médio | — |
| VAG-003 | Menu de Ações da Vaga | Frontend | MVP | 1 | 📋 Pendente | — | P2 Médio | — |
| VAG-004 | Pausar/Ativar Vaga | Full-Stack | MVP | 1 | 📋 Pendente | — | P2 Médio | — |
| VAG-005 | Duplicar Vaga | Full-Stack | MVP | 1 | 📋 Pendente | — | P2 Médio | — |
| VAG-006 | Arquivar Vaga | Full-Stack | MVP | 1 | 📋 Pendente | — | P2 Médio | — |
| VAG-007 | Contador de Candidatos | Frontend | MVP | 1 | 📋 Pendente | — | P2 Médio | — |
| VAG-008 | Navegação Vaga → Kanban | Frontend | MVP | 1 | 📋 Pendente | — | P2 Médio | — |

### ÉPICO 14: Integrações MVP (33 cards — 27 MVP + 5 pós-MVP + 1 consolidado)
| Card | Título | Tipo | Fase | Sprint | Status | Notas | Backlog | Déb. Técnico |
|------|--------|------|------|--------|--------|-------|---------|-------------|
| INT-WOS-001 | Configurar WorkOS Account | Integração | MVP | 1 | 📋 Pendente | API keys, environments | P0 Crítico | — |
| INT-WOS-002 | SSO SAML/OIDC | Backend | MVP | 1 | 📋 Pendente | — | P0 Crítico | — |
| INT-WOS-003 | Directory Sync SCIM | Backend | MVP | 1 | 📋 Pendente | — | P0 Crítico | — |
| INT-WOS-004 | MFA Enforcement | Backend | MVP | 1 | 📋 Pendente | — | P0 Crítico | — |
| INT-WOS-005 | User Management SDK | Backend | MVP | 1 | 📋 Pendente | — | P0 Crítico | — |
| INT-WOS-006 | Webhook de Eventos | Backend | MVP | 1 | 📋 Pendente | — | P0 Crítico | — |
| INT-WOS-007 | Admin Portal | Frontend | MVP | 1 | 📋 Pendente | — | P0 Crítico | — |
| INT-TWI-001 | Configurar Twilio Account | Integração | MVP | 1 | 📋 Pendente | WhatsApp sandbox | P0 Crítico | — |
| INT-TWI-002 | Sandbox WhatsApp | Backend | MVP | 1 | 📋 Pendente | — | P0 Crítico | — |
| INT-TWI-003 | Número de Produção | Integração | MVP | 1 | 📋 Pendente | — | P0 Crítico | — |
| INT-TWI-004 | Webhook de Mensagens | Backend | MVP | 1 | 📋 Pendente | — | P0 Crítico | — |
| INT-TWI-005 | Templates Aprovados Meta | Integração | MVP | 1 | 📋 Pendente | — | P0 Crítico | — |
| INT-TWI-006 | Status Delivery Reports | Backend | MVP | 1 | 📋 Pendente | — | P0 Crítico | — |
| INT-TWI-007 | Rate Limiting e Filas | Backend | MVP | 1 | 📋 Pendente | — | P0 Crítico | — |
| INT-MSG-001 | Configurar Azure App | Integração | — | — | 🔄 Consolidado em AGE-001 | Config unificada | — | Consolidado |
| INT-MSG-002 | OAuth Flow Microsoft | Backend | MVP | 2 | 📋 Pendente | OAuth 2.0 | P1 Alto | — |
| INT-MSG-003 | Calendar API | Backend | MVP | 2 | 📋 Pendente | — | P1 Alto | — |
| INT-MSG-004 | Teams Meeting API | Backend | MVP | 2 | 📋 Pendente | — | P1 Alto | — |
| INT-MSG-005 | Webhook de Eventos | Backend | Pós-MVP | Pós-MVP | 🔄 Pós-MVP | — | P2 Médio | — |
| INT-MSG-006 | Token Refresh | Backend | MVP | 2 | 📋 Pendente | Auto-refresh | P1 Alto | — |
| INT-MSG-007 | Multi-tenant Calendar | Backend | Pós-MVP | Pós-MVP | 🔄 Pós-MVP | — | P2 Médio | — |
| INT-LLM-001 | Cliente Anthropic Claude | Backend | Pós-MVP | Pós-MVP | ⏸️ Pós-MVP | — | P2 Médio | — |
| INT-LLM-002 | Cliente Google Gemini | Backend | MVP | 2 | 📋 Pendente | — | P1 Alto | — |
| INT-LLM-003 | Router de Modelos | Backend | Pós-MVP | Pós-MVP | ⏸️ Pós-MVP | — | P2 Médio | — |
| INT-LLM-004 | Fallback entre Modelos | Backend | Pós-MVP | Pós-MVP | ⏸️ Pós-MVP | — | P2 Médio | — |
| INT-LLM-005 | Gestão de Prompts | Backend | MVP | 2 | 📋 Pendente | Versioning | P2 Médio | — |
| INT-LLM-006 | Cache de Respostas | Backend | MVP | 2 | 📋 Pendente | Redis | P2 Médio | — |
| INT-LLM-007 | Monitoramento de Custos | Backend | MVP | 2 | 📋 Pendente | — | P2 Médio | — |
| INT-LLM-008 | Rate Limiting LLM | Backend | MVP | 2 | 📋 Pendente | — | P2 Médio | — |
| INT-LLM-009 | Logging de Conversas | Backend | MVP | 2 | 📋 Pendente | Auditoria | P2 Médio | — |
| INT-APY-001 | Configurar Apify Account | Integração | MVP | 3 | 📋 Pendente | Web scraping | P2 Médio | — |
| INT-APY-002 | LinkedIn Scraper Actor | Backend | MVP | 3 | 📋 Pendente | — | P2 Médio | — |
| INT-APY-003 | Integração com Sourcing Agent | AI | MVP | 3 | 📋 Pendente | — | P2 Médio | — |

---


### ÉPICO 12: JD e Wizard Avançado (5 cards) ⏸️ PÓS-MVP
| Card | Título | Tipo | Fase | Sprint | Status | Notas | Backlog | Déb. Técnico |
|------|--------|------|------|--------|--------|-------|---------|-------------|
| JD-001 | Preview de JD com Sugestões LIA | Frontend | Pós-MVP | Pós-MVP | 📋 Pendente | — | P3 Baixo | — |
| JD-002 | JD Completo para Publicação | Frontend | Pós-MVP | Pós-MVP | 📋 Pendente | — | P3 Baixo | — |
| JDW-001 | Interação com Sugestões LIA | Backend | Pós-MVP | Pós-MVP | 📋 Pendente | — | P3 Baixo | — |
| JDW-002 | Análise de Compensação de Mercado | Backend | Pós-MVP | Pós-MVP | 📋 Pendente | — | P3 Baixo | — |
| JDW-003 | Insights de Mercado para Vagas | Backend | Pós-MVP | Pós-MVP | 📋 Pendente | — | P3 Baixo | — |

### ÉPICO 13: Configurações Avançadas (6 cards) ⏸️ PÓS-MVP
| Card | Título | Tipo | Fase | Sprint | Status | Notas | Backlog | Déb. Técnico |
|------|--------|------|------|--------|--------|-------|---------|-------------|
| CFG-001 | LIA Field Toggles | Frontend | Pós-MVP | Pós-MVP | 📋 Pendente | — | P3 Baixo | — |
| CFG-002 | Verificação de Completude | Backend | Pós-MVP | Pós-MVP | 📋 Pendente | — | P3 Baixo | — |
| CFG-003 | Configuração de Jornada | Frontend | Pós-MVP | Pós-MVP | 📋 Pendente | — | P3 Baixo | — |
| CFG-004 | Hub de Comunicação | Frontend | Pós-MVP | Pós-MVP | 📋 Pendente | — | P3 Baixo | — |
| CFG-005 | Dados da Empresa para LIA | Frontend | Pós-MVP | Pós-MVP | 📋 Pendente | — | P3 Baixo | — |
| IMP-001 | Importação Inteligente | Frontend | Pós-MVP | Pós-MVP | 📋 Pendente | — | P3 Baixo | — |

### ÉPICO 15: Agentes IA Especializados (8 cards) 🆕
| Card | Título | Tipo | Fase | Sprint | Status | Notas | Backlog | Déb. Técnico |
|------|--------|------|------|--------|--------|-------|---------|-------------|
| AGT-001 | Agente Avaliador WSI | AI | MVP | 3 | 📋 Pendente | — | P2 Médio | — |
| AGT-002 | Agente de Triagem Curricular | AI | MVP | 3 | 📋 Pendente | — | P2 Médio | — |
| AGT-003 | Agente de Agendamento | AI | MVP | 3 | 📋 Pendente | — | P2 Médio | — |
| AGT-004 | Orquestrador de Pipeline Chat | AI | MVP | 3 | 📋 Pendente | — | P2 Médio | — |
| TRI-012 | Serviço de Pré-Qualificação | Backend | MVP | 3 | 📋 Pendente | — | P2 Médio | — |
| DAT-001 | Sistema de Solicitação de Dados | Frontend | MVP | 3 | 📋 Pendente | — | P2 Médio | — |
| ENT-001 | Análise de Transcrição | Backend | MVP | 3 | 📋 Pendente | — | P2 Médio | — |
| KAN-009 | Componentes Kanban Modulares | Frontend | MVP | 3 | 📋 Pendente | Vindo do É11 | P2 Médio | — |

---

## ÉPICOS PÓS-MVP: OTIMIZAÇÃO DO FUNIL DE TALENTOS (24 cards, 150 SP) 🆕

> **📄 Documento completo:** [epic-wdt-talent-funnel.md](./epic-wdt-talent-funnel.md)  
> **Origem:** Análise metodológica com André (especialista em busca) + reunião Paulo/Anderson  
> **Arquitetura:** Elasticsearch + PG Vector + WRF (Weighted Rank Fusion)  
> **Cada card inclui prompt para IA (Cursor/VSCode)** considerando diferenças de stack Replit vs Produção

### ÉPICO 16: Otimização Estatística de Busca (8 cards, 38 SP) 🆕
| Card | Título | Tipo | Fase | Sprint | SP | Status | Backlog | Déb. Técnico |
|------|--------|------|------|--------|-----|--------|---------|-------------|
| WDT-008 | Dashboard básico de métricas de feedback | Full-Stack | MVP | 2 | 5 | 📋 Pendente | P2 Médio | — |
| WDT-009 | Classificação automática nível qualificação vaga | AI/Backend | MVP | 3 | 8 | 📋 Pendente | P2 Médio | — |
| WDT-010 | Exibição e override da classificação | Frontend | MVP | 3 | 2 | 📋 Pendente | P2 Médio | — |
| WDT-011 | Cálculo taxa de queda de score (ES) | Backend | Pós-MVP | 4 | 5 | 📋 Pendente | P2 Médio | — |
| WDT-012 | Cálculo gap semântico (PG Vector) | Backend | Pós-MVP | 4 | 5 | 📋 Pendente | P2 Médio | — |
| WDT-013 | Teste de estabilidade intra-query | Backend | Pós-MVP | 4 | 3 | 📋 Pendente | P2 Médio | — |
| WDT-014 | Parametrização dinâmica do K no WRF | Backend | Pós-MVP | 5 | 5 | 📋 Pendente | P2 Médio | Otimização |
| WDT-015 | Filtro pré-WRF combinando análises | Backend | Pós-MVP | 5 | 5 | 📋 Pendente | P2 Médio | Otimização |

### ÉPICO 17: Base de Critérios de Avaliação (4 cards ativos + 3 cancelados, 26 SP) 🆕 ⭐ GAME CHANGER
| Card | Título | Tipo | Fase | Sprint | SP | Status | Backlog | Déb. Técnico |
|------|--------|------|------|--------|-----|--------|---------|-------------|
| WDT-016 | Schema e modelo base de critérios | Backend | Pós-MVP | 6 | 8 | ✅ Implementado (Replit) | P1 Alto | — |
| WDT-017 | ~~Interface admin para gestão de critérios~~ | Frontend | — | 7 | ~~8~~ | ❌ Cancelado | — | — |
| WDT-018 | Integração critérios com prompt LLM | AI/Backend | Pós-MVP | 8 | 8 | ✅ Implementado (Replit) | P1 Alto | — |
| WDT-019 | ~~Dashboard de gestão e métricas critérios~~ | Full-Stack | — | 9 | ~~5~~ | ❌ Cancelado | — | — |
| WDT-020 | ~~Alimentação inicial 50-100 critérios RH sênior~~ | Data | — | 9-10 | ~~13~~ | ❌ Cancelado | — | — |
| WDT-021 | Sistema Explicit/Implicit/Inferred | AI/Backend | Pós-MVP | 10 | 5 | ✅ Implementado (Replit) | P1 Alto | — |
| WDT-022 | Score de confiança individual por requisito | Full-Stack | Pós-MVP | 11 | 5 | ✅ Implementado (Replit) | P1 Alto | — |

> **⚠️ NOTA DE IMPLEMENTAÇÃO (08 Fev 2026):** Fase 3 implementada no protótipo Replit com 4 cards core e 34 testes. 3 cards cancelados (WDT-017, 019, 020) — sistema auto-evolutivo sem interfaces admin. Detalhes em `epic-wdt-talent-funnel.md`.

### ÉPICO 18: Aprendizado e Features Avançadas (6 cards, 42 SP) 🆕
| Card | Título | Tipo | Fase | Sprint | SP | Status | Backlog | Déb. Técnico |
|------|--------|------|------|--------|-----|--------|---------|-------------|
| WDT-023 | Toggle requisito essencial excludente | Full-Stack | Pós-MVP | 12 | 5 | 📋 Pendente | P2 Médio | — |
| WDT-024 | Enriquecimento de perfil sob demanda via web | Backend | Pós-MVP | 13 | 8 | 📋 Pendente | P2 Médio | — |
| WDT-025 | Análise pós-busca com feedback qualidade | Full-Stack | Pós-MVP | 13 | 5 | 📋 Pendente | P2 Médio | — |
| WDT-026 | Flags automáticas de inconsistência | Backend | Pós-MVP | 14 | 3 | 📋 Pendente | P2 Médio | — |
| WDT-027 | Motor de aprendizado via feedback | AI/Backend | Pós-MVP | 15-16 | 13 | 📋 Pendente | P2 Médio | — |
| WDT-028 | Framework de A/B testing parâmetros | Full-Stack | Pós-MVP | 17 | 8 | 📋 Pendente | P2 Médio | — |

### ÉPICO 19: Observabilidade e Documentação de Busca (2 cards, 16 SP) 🆕
| Card | Título | Tipo | Fase | Sprint | SP | Status | Backlog | Déb. Técnico |
|------|--------|------|------|--------|-----|--------|---------|-------------|
| WDT-029 | Documentação técnica completa sistema busca | Docs | Pós-MVP | 2+/18 | 8 | 📋 Pendente | P3 Baixo | — |
| WDT-030 | Dashboard observabilidade sistema busca | Full-Stack | Pós-MVP | 18 | 8 | 📋 Pendente | P2 Médio | — |


---

## STATUS DO DOCUMENTO

**Documento completo** — 197 cards especificados (atualizado: 09/02/2026). 141 MVP ativos, 50 pós-MVP, 3 cancelados, 3 removidos/consolidados.

### Épicos Especificados (atualizado 09/02/2026):

**MVP (141 cards ativos):**
- **É1:** Autenticação e Onboarding (6 cards) 📋 Sprint 1
- **É3:** Busca e Mapeamento (13 cards — 12 S1 + 1 S2) 📋 ✅ 5 prontos; MAP-014 pós-MVP; inclui 7 WDT migrados
- **É4:** Geração de Perguntas WSI (8 cards) 📋 Sprint 2; WSI-004 removido; +WIZ-008/012/013 do É2
- **É5:** Triagem WhatsApp (12 cards) 📋 Sprint 2; TRI-011 pós-MVP
- **É6:** Score WSI (8 cards) 📋 Sprint 3
- **É7:** Gates de Aprovação (8 cards) 📋 Sprint 3
- **É8:** Templates de Comunicação (8 cards) 📋 Sprint 2
- **É9:** Agendamento Automático (8 cards) 📋 Sprint 2
- **É10:** Notificações (6 cards) 📋 Sprint 3; NOT-007 pós-MVP
- **É11:** Kanban e Tabela de Candidatos (29 cards) 📋 Sprint 1; KAN-005 removido, KAN-009 em É15
- **É14:** Integrações MVP (27 cards) 📋 Sprint 1-3; 5 pós-MVP + 1 consolidado
- **É15:** Agentes IA (8 cards) 📋 Sprint 3

**Pós-MVP (50 cards ativos):**
- **É2:** Wizard Conversacional (11 cards) ⏸️ Épico completo adiado; 3 migrados → É4
- **É12:** JD/Wizard Avançado (5 cards) ⏸️
- **É13:** Config Avançadas (6 cards) ⏸️
- **É16:** Otimização Estatística de Busca (5 cards pós-MVP + 3 MVP) ⏸️ WDT-008/009/010 em S2-S3; WDT-011..015 pós-MVP
- **É17:** Base de Critérios de Avaliação (4 cards ativos + 3 cancelados) ⏸️ WDT-016,018,021,022
- **É18:** Aprendizado e Features Avançadas (6 cards) ⏸️ WDT-023..028
- **É19:** Observabilidade e Documentação (2 cards) ⏸️ WDT-029,030

---

## DIAGRAMA DE DEPENDÊNCIAS ENTRE ÉPICOS

### Visão Geral — Fluxo de Dependências MVP

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           SPRINT 1 — FUNDAÇÃO                                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────┐                                                               │
│  │  É1: AUTH        │ ◄── BLOQUEANTE PARA TUDO                                      │
│  │  (6 cards)       │     Todas as rotas protegidas dependem de auth                │
│  │  Sprint 1        │                                                               │
│  └────────┬─────────┘                                                               │
│           │                                                                          │
│     ┌─────┼──────────────────────────────────────┐                                  │
│     │     │                                      │                                  │
│     ▼     ▼                                      ▼                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐                   │
│  │  É3: MAPEAMENTO  │  │  É11: KANBAN     │  │  É14: INTEGRAÇÕES│                   │
│  │  (13 cards)      │  │  (29 cards)      │  │  (27 cards)      │                   │
│  │  Sprint 1-2      │  │  Sprint 1        │  │  Sprint 1-3      │                   │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘                   │
│           │                     │                      │                             │
│           │              ┌──────┘                      │                             │
│           │              │                             │                             │
└───────────┼──────────────┼─────────────────────────────┼─────────────────────────────┘
            │              │                             │
┌───────────┼──────────────┼─────────────────────────────┼─────────────────────────────┐
│           │      SPRINT 2 — CORE AI + COMUNICAÇÃO      │                             │
├───────────┼──────────────┼─────────────────────────────┼─────────────────────────────┤
│           │              │                             │                             │
│           ▼              │                             ▼                             │
│  ┌──────────────────┐    │                    INT-TWI (WhatsApp)                      │
│  │  É4: WSI         │    │                    INT-MSG (Microsoft)                     │
│  │  PERGUNTAS       │    │                    INT-LLM (AI Models)                     │
│  │  (8 cards)       │    │                             │                             │
│  │  Sprint 2        │    │                    ┌────────┘                             │
│  └────────┬─────────┘    │                    │                                      │
│           │              │                    ▼                                      │
│           │              │           ┌──────────────────┐                            │
│           ▼              │           │  É9: AGENDAMENTO │                            │
│  ┌──────────────────┐    │           │  (8 cards)       │                            │
│  │  É5: TRIAGEM     │◄───┘          │  Sprint 2        │                            │
│  │  WHATSAPP        │               │  Depende: INT-MSG│                            │
│  │  (12 cards)      │               └──────────────────┘                            │
│  │  Sprint 2        │                                                               │
│  │  Depende: É4+É14 │    ┌──────────────────┐  ┌──────────────────┐                 │
│  └────────┬─────────┘    │  É8: TEMPLATES   │  │  É16: OTIMIZAÇÃO │                 │
│           │              │  (8 cards)       │  │  BUSCA (3 MVP)   │                 │
│           │              │  Sprint 2        │  │  Sprint 2-3      │                 │
│           │              │  Depende: É5     │  │  Depende: É3     │                 │
│           │              └──────────────────┘  └──────────────────┘                 │
│           │                                                                          │
└───────────┼──────────────────────────────────────────────────────────────────────────┘
            │
┌───────────┼──────────────────────────────────────────────────────────────────────────┐
│           │                     SPRINT 3 — SCORING + APROVAÇÃO                       │
├───────────┼──────────────────────────────────────────────────────────────────────────┤
│           │                                                                          │
│           ▼                                                                          │
│  ┌──────────────────┐    ┌──────────────────┐                                       │
│  │  É6: SCORE WSI   │───►│  É7: GATES       │                                       │
│  │  (8 cards)       │    │  APROVAÇÃO       │                                       │
│  │  Sprint 3        │    │  (8 cards)       │                                       │
│  │  Depende: É5     │    │  Sprint 3        │                                       │
│  └──────────────────┘    │  Depende: É6     │                                       │
│                          └────────┬─────────┘                                       │
│                                   │                                                  │
│  ┌──────────────────┐    ┌────────┴─────────┐    ┌──────────────────┐               │
│  │  É10: NOTIFIC.   │    │  É15: AGENTES IA │    │  É14: INTEGRAÇÕES│               │
│  │  (6 cards)       │    │  (8 cards)       │    │  (restantes S3)  │               │
│  │  Sprint 3        │    │  Sprint 3        │    │  INT-APY (Apify) │               │
│  │  Depende: É1     │    │  Depende: É4-É7  │    └──────────────────┘               │
│  └──────────────────┘    └──────────────────┘                                       │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Cadeia Crítica MVP (Caminho Mais Longo)

```
É1 (Auth) → É3 (Mapeamento) → É4 (WSI Perguntas) → É5 (Triagem WhatsApp) → É6 (Score WSI) → É7 (Gates) → É15 (Agentes IA)
   S1            S1                  S2                     S2                    S3                S3            S3
```

> **O caminho crítico cruza os 3 sprints.** Atrasos em É1 ou É3 impactam todo o pipeline.

### Dependências Inter-Épicos (Cards Específicos)

| De (Origem) | Para (Destino) | Tipo | Descrição |
|-------------|----------------|------|-----------|
| AUTH-001/003/005 | Todos os épicos | Bloqueante | Login, middleware e SSL habilitam todas as rotas |
| MAP-001, MAP-002 | KAN-001+ | Dados | Kanban consome lista de candidatos da busca |
| MAP-002, MAP-005 | É4 (WSI) | Dados | Matching score alimenta geração de perguntas |
| WSI-001 | TRI-004 | Bloqueante | Perguntas WSI são usadas no fluxo conversacional da triagem |
| INT-TWI-001 | É5 (Triagem) | Bloqueante | WhatsApp API habilita todo o épico de triagem |
| TRI-003, TRI-004 | SCO-001 | Dados | Respostas da triagem alimentam cálculo de score |
| SCO-001 | GAT-001, GAT-002 | Bloqueante | Gates usam score WSI para decisão de aprovação |
| GAT-001 | TRI-002 | Sequencial | Gate 1 aprova mapeados antes do envio para triagem |
| GAT-001 | KAN-011 | Sequencial | Triagem em lote depende de aprovação no Gate 1 |
| INT-MSG-001 | AGE-001+ | Bloqueante | Microsoft Graph habilita todo o agendamento |
| TPL-001+ | TRI-009 | Dados | Templates de mensagem usados na triagem |
| KAN-002, SCO-001 | KAN-006 | Dados | Badge WSI no card depende do score calculado |
| É4 + É5 + É6 + É7 | É15 (Agentes) | Bloqueante | Agentes IA orquestram todos os épicos core |

### Dependências Pós-MVP

```
É3 (Mapeamento MVP) ──→ É16 (Otimização Busca) ──→ É17 (Critérios Avaliação) ──→ É18 (Aprendizado)
                                    │
                                    └──→ É19 (Observabilidade)

É2 (Wizard Conversacional) ← independente, pode ser desenvolvido em paralelo pós-MVP
É12 (JD Avançado) ← depende de É2
É13 (Config Avançadas) ← independente
```

### Legenda

| Símbolo | Significado |
|---------|-------------|
| ──► | Dependência direta (A deve estar pronto antes de B) |
| ◄── | Épico que recebe dependência |
| BLOQUEANTE | Sem este card/épico, o destino não pode iniciar |
| Dados | Destino usa dados gerados pela origem, mas pode iniciar em paralelo |
| Sequencial | Deve ser executado na ordem indicada |

---

**Documento consolidado - Plataforma LIA MVP**  
**WeDoTalent - Fevereiro 2026**

---


# PARTE 2: CARDS DETALHADOS POR ÉPICO

---

## ÉPICO 1: AUTENTICAÇÃO

---

### CARD AUTH-001: Tela de Login
**Épico:** É1 — Autenticação

```yaml
Titulo: [FRONTEND] Tela de Login
Tipo: Feature
Area: Full-Stack
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 3
Prioridade: Crítica
Epic: EPIC-AUTH
Status: 📋 Pendente Jira

Dependencias: AUTH-005

Descricao: |
  Tela de login da plataforma LIA com suporte a email/senha
  e integração futura com SSO via WorkOS, com branding dinâmico por tenant (logo, cores, nome da empresa carregados via subdomínio).

Historia de Usuario: |
  Como recrutador, eu quero fazer login na plataforma
  para acessar minhas vagas e candidatos.

Regras de Negocio:
  1. Email obrigatório e validado
  2. Senha mínimo 8 caracteres
  3. Checkbox "Lembrar-me" para persistir sessão
  4. Link "Esqueci minha senha"
  5. Redirecionamento após login para /dashboard
  6. Suporte futuro a SSO (botão "Entrar com SSO")
  7. Logo e cores carregados dinamicamente por subdomínio (ex: itau.wedotalent.cc)

Requisitos Tecnicos:
  Frontend:
    - LoginPage component (React)
    - Formulário com react-hook-form
    - Validação com zod
    - Toast de erro/sucesso
    - Detecção de subdomínio, carregamento dinâmico de branding via GET /api/v1/tenants/{subdomain}/branding
  Backend:
    - POST /api/v1/auth/login
    - Response: { token, user, expires_at }
  Dados:
    - users: id, email, password_hash, name, company_id, role
  Validacoes:
    - Email: formato válido
    - Senha: mínimo 8 chars

Design & Componentes:
  Componentes Existentes:
    - Input - campos de texto
    - Button - submit
    - Card - container do formulário
    - Toast - feedback (sonner)
    - Checkbox - lembrar-me
  Novos Componentes:
    - LoginForm - formulário de login
  Design Tokens:
    Background: --lia-bg-primary (#FFFFFF)
    Accent: --wedo-cyan (#60BED1)
    Text: --lia-text-primary (#111827)
    Error: --electric-red (#de1c31)
  Layout:
    Container: max-w-md mx-auto, center vertical
    Card: lia-card com lia-shadow-md
    Logo: centralizado acima do form
    Spacing: gap-6 entre elementos
  Estados:
    - Default, Hover, Focus, Loading, Error, Success
  Acessibilidade:
    - Labels em todos os campos
    - Tab order correto
    - Mensagens de erro anunciadas

Comportamento de UI:
  Fluxo Principal:
    1. Usuário acessa /login
    2. Preenche email e senha
    3. Clica em "Entrar"
    4. Loading spinner no botão
    5. Sucesso: redirect para /dashboard
    6. Erro: toast vermelho com mensagem
  
  Estados de Botoes:
    Entrar:
      - Default: bg-wedo-cyan, texto branco
      - Hover: bg-wedo-cyan-hover
      - Loading: spinner + "Entrando..."
      - Disabled: durante loading
  
  Validacoes Inline:
    Email:
      - Erro: "Email inválido"
    Senha:
      - Erro: "Mínimo 8 caracteres"
  
  Mensagens de Feedback:
    - Erro credenciais: "Email ou senha incorretos"
    - Erro servidor: "Erro ao conectar. Tente novamente."
    - Sucesso: redirect silencioso


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Login funciona com credenciais válidas
  - [ ] Erros exibidos corretamente
  - [ ] Redirect após login
  - [ ] Responsivo mobile

Criterios de Aceitacao:
  - [ ] Email inválido mostra erro
  - [ ] Senha < 8 chars mostra erro
  - [ ] Credenciais inválidas mostra toast
  - [ ] Login válido redireciona

Arquivos de Referencia (Prototipo Replit):
  - page.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/access/page.tsx
  - auth-context.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/auth-context.tsx
  - auth-headers.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/api/auth-headers.ts
  - workos.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/workos.ts
```

---

### CARD AUTH-002: Integração WorkOS SSO
**Épico:** É1 — Autenticação

```yaml
Titulo: [INTEGRAÇÃO] Configurar WorkOS SSO
Tipo: Integração
Area: Integração
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 8
Prioridade: Alta
Epic: EPIC-AUTH
Status: 📋 Pendente Jira
Dependencias: AUTH-001

Descricao: |
  Integrar WorkOS para suporte a Single Sign-On (SSO) com
  SAML e OIDC para clientes enterprise.

Historia de Usuario: |
  Como admin de empresa enterprise, eu quero fazer login
  usando o SSO da minha empresa para não precisar de senha separada.

Regras de Negocio:
  1. SSO opcional por empresa (config por tenant)
  2. Suporte a SAML 2.0 e OIDC
  3. Provisionamento automático de usuário no primeiro login
  4. Mapeamento de roles via SCIM
  5. Fallback para email/senha se SSO indisponível
  6. Sessão SSO respeita política do IdP

Requisitos Tecnicos:
  Backend:
    - GET /api/v1/auth/sso/authorize
    - GET /api/v1/auth/sso/callback
    - POST /api/v1/auth/sso/logout
    - WorkOS SDK Python
  Frontend:
    - Botão "Entrar com SSO" na tela de login
    - Redirect para WorkOS hosted login
    - Callback handler
  Dados:
    - companies: sso_enabled, sso_connection_id, sso_domain
    - users: sso_user_id, identity_provider
  Validacoes:
    - Domínio de email deve corresponder ao domínio SSO

Integracoes Externas:
  WorkOS:
    - Tipo: Identity Provider
    - SDK: workos-python
    - Endpoints: 
      - SSO: api.workos.com/sso
      - Directory Sync: api.workos.com/directory-sync
    - Secrets: WORKOS_API_KEY, WORKOS_CLIENT_ID
    - Custo: $125/connection/mês (SSO) ou Enterprise pricing
    - Documentação: https://workos.com/docs

Design & Componentes:
  Componentes Existentes:
    - Button - "Entrar com SSO"
    - Divider - "ou"
  Novos Componentes:
    - SSOButton - botão estilizado para SSO
    - SSODomainInput - input para detectar SSO por domínio
  Design Tokens:
    Button SSO: bg-white, border --lia-border-subtle
    Icon: logo do provider (quando disponível)
  Layout:
    Posição: abaixo do formulário principal
    Divider: "──── ou ────"
  Estados:
    - Default, Hover, Loading, Redirect

Comportamento de UI:
  Fluxo Principal:
    1. Usuário clica "Entrar com SSO"
    2. (Opcional) Input de email para detectar conexão
    3. Redirect para WorkOS hosted login
    4. Usuário autentica no IdP da empresa
    5. Callback para /api/v1/auth/sso/callback
    6. Criação/atualização de usuário
    7. Redirect para /dashboard
  
  Fluxo Alternativo - Detecção por Domínio:
    1. Usuário digita email
    2. Sistema detecta domínio com SSO configurado
    3. Mostra botão "Continuar com SSO [Empresa]"
    4. Click redireciona para IdP específico

DoD:
  - [ ] SSO SAML funciona
  - [ ] SSO OIDC funciona
  - [ ] Usuário criado no primeiro login
  - [ ] Logout funciona (SSO + local)
  - [ ] Fallback para email/senha

Criterios de Aceitacao:
  - [ ] Redirect para IdP funciona
  - [ ] Callback cria usuário
  - [ ] Sessão persiste corretamente
  - [ ] Domínio SSO detectado automaticamente

Arquivos de Referencia (Prototipo Replit):
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/auth/workos/sso/route.ts
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/auth/workos/callback/route.ts
  - workos.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/workos.ts
  - workos-links.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/workos-links.ts
  - workos-admin-portal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/admin/workos-admin-portal.tsx
  - workos-link-card.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/admin/workos-link-card.tsx
  - workos.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/workos.py
  - workos_provisioning_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/workos_provisioning_service.py
```

---

### CARD AUTH-003: Middleware de Autenticação
**Épico:** É1 — Autenticação

```yaml
Titulo: [BACKEND] Middleware de Autenticação JWT
Tipo: Feature
Area: Full-Stack
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 5
Prioridade: Crítica
Epic: EPIC-AUTH
Status: 📋 Pendente Jira

Descricao: |
  Middleware para validar JWT em todas as rotas protegidas,
  extrair informações do usuário e verificar permissões.

Historia de Usuario: |
  Como sistema, eu preciso validar tokens em cada requisição
  para garantir que apenas usuários autenticados acessem recursos.

Regras de Negocio:
  1. Token JWT no header Authorization: Bearer {token}
  2. Validar assinatura, expiração e issuer
  3. Extrair user_id, company_id, role do token
  4. Injetar user no contexto da requisição
  5. Retornar 401 para token inválido/expirado
  6. Retornar 403 para permissão insuficiente
  7. Rotas públicas marcadas com @public decorator

Requisitos Tecnicos:
  Backend:
    - AuthMiddleware class (FastAPI)
    - Depends(get_current_user) para rotas protegidas
    - @public decorator para rotas públicas
    - PyJWT para validação
  Dados:
    - JWT payload: { user_id, company_id, role, exp, iat }
  Validacoes:
    - Assinatura: HMAC-SHA256 ou RS256
    - Expiração: exp < now
    - Issuer: iss == "lia-platform"
  Configuração:
    - JWT_SECRET_KEY (env)
    - JWT_ALGORITHM: HS256
    - JWT_EXPIRATION: 24h (access), 7d (refresh)

Integracoes Externas:
  Nenhuma - lógica interna

Design & Componentes:
  N/A - Backend only

Comportamento de API:
  Headers Requeridos:
    Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
  
  Respostas de Erro:
    401 Unauthorized:
      - Token ausente: { "detail": "Token não fornecido" }
      - Token inválido: { "detail": "Token inválido" }
      - Token expirado: { "detail": "Token expirado" }
    403 Forbidden:
      - Sem permissão: { "detail": "Permissão insuficiente" }
  
  Contexto Injetado:
    request.state.user = {
      "id": "uuid",
      "email": "user@company.com",
      "company_id": "uuid",
      "role": "recruiter"
    }

DoD:
  - [ ] Middleware valida tokens corretamente
  - [ ] 401 para token inválido
  - [ ] 403 para permissão insuficiente
  - [ ] Contexto do usuário disponível nas rotas
  - [ ] Testes unitários passando

Criterios de Aceitacao:
  - [ ] Token válido permite acesso
  - [ ] Token expirado retorna 401
  - [ ] Token malformado retorna 401
  - [ ] Rota pública acessível sem token

Arquivos de Referencia (Prototipo Replit):
  - auth-context.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/auth-context.tsx
  - auth-headers.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/api/auth-headers.ts
  - workos-session.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/workos-session.ts
  - session-crypto.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/session-crypto.ts
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/auth/workos/session/route.ts
  - models.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/auth/models.py
  - schemas.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/auth/schemas.py
```

---

### CARD AUTH-004: Gestão de Sessão JWT
**Épico:** É1 — Autenticação

```yaml
Titulo: [BACKEND] Gestão de Sessão e Refresh Token
Tipo: Feature
Area: Full-Stack
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 5
Prioridade: Alta
Epic: EPIC-AUTH
Status: 📋 Pendente Jira
Dependencias: AUTH-003

Descricao: |
  Sistema de refresh tokens para renovar sessões sem
  exigir novo login, com revogação e rotação de tokens.

Historia de Usuario: |
  Como recrutador, eu quero permanecer logado por dias
  sem precisar digitar senha novamente.

Regras de Negocio:
  1. Access token: 15 minutos de validade
  2. Refresh token: 7 dias de validade
  3. Refresh token armazenado em httpOnly cookie
  4. Rotação: novo refresh token a cada refresh
  5. Revogação: invalidar todos tokens no logout
  6. Blacklist de tokens revogados (Redis)
  7. Máximo 5 sessões ativas por usuário

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/auth/refresh
    - POST /api/v1/auth/logout
    - POST /api/v1/auth/logout-all
    - GET /api/v1/auth/sessions
  Dados:
    - refresh_tokens: id, user_id, token_hash, expires_at, created_at, revoked_at
    - sessions: id, user_id, device_info, ip, last_active
  Cache:
    - Redis: blacklist de tokens revogados
    - TTL: igual ao tempo restante do token

Integracoes Externas:
  Redis:
    - Tipo: Cache/Blacklist
    - Uso: Token blacklist, session cache
    - Secret: REDIS_URL (via Replit)
    - Custo: Incluído no Replit

Design & Componentes:
  N/A - Backend only

Comportamento de API:
  POST /api/v1/auth/refresh:
    Request: (cookie com refresh_token)
    Response: {
      "access_token": "eyJ...",
      "expires_at": "2026-01-22T15:00:00Z"
    }
    Set-Cookie: refresh_token=eyJ...; HttpOnly; Secure; SameSite=Strict
  
  POST /api/v1/auth/logout:
    Request: Authorization header
    Response: { "message": "Logout realizado" }
    Effect: Revoga refresh token atual
  
  POST /api/v1/auth/logout-all:
    Request: Authorization header
    Response: { "message": "Todas as sessões encerradas" }
    Effect: Revoga todos os tokens do usuário
  
  GET /api/v1/auth/sessions:
    Response: {
      "sessions": [
        { "id": "uuid", "device": "Chrome/Windows", "ip": "...", "last_active": "..." }
      ]
    }

DoD:
  - [ ] Refresh token funciona
  - [ ] Rotação implementada
  - [ ] Logout revoga token
  - [ ] Blacklist no Redis
  - [ ] Limite de sessões funciona

Criterios de Aceitacao:
  - [ ] Access token renovado via refresh
  - [ ] Refresh token antigo invalidado após uso
  - [ ] Logout remove sessão
  - [ ] 6ª sessão remove a mais antiga

Arquivos de Referencia (Prototipo Replit):
  - workos-session.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/workos-session.ts
  - session-crypto.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/session-crypto.ts
  - useSessionRefresh.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/useSessionRefresh.ts
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/auth/workos/refresh/route.ts
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/auth/workos/session/route.ts
  - models.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/auth/models.py
  - schemas.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/auth/schemas.py
```

---

### CARD AUTH-005: Wildcard SSL + Google Cloud Multi-Brand
**Épico:** É1 — Autenticação

```yaml
Titulo: "[INFRA] Configuração Wildcard SSL + Google Cloud para Multi-Brand/Subdomínio"
Tipo: Infraestrutura
Area: Infraestrutura
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 5
Prioridade: Crítica
Epic: EPIC-AUTH
Status: 📋 A Criar no Jira
Dependencias: Nenhuma (card fundacional)

Descricao: |
  Configurar certificado SSL wildcard (*.wedotalent.cc) e DNS no Google Cloud
  para suportar subdomínios por empresa (ex: itau.wedotalent.cc, ambev.wedotalent.cc).
  Isso habilita white label e customização de marca por tenant.
  Inclui middleware de resolução de tenant, tabela de tenants no banco,
  configuração Nginx para wildcard routing e detecção client-side de subdomínio.

Historia de Usuario: |
  Como administrador da plataforma, eu quero que cada empresa cliente
  tenha seu próprio subdomínio (ex: itau.wedotalent.cc) para oferecer
  uma experiência white label com logo e cores customizadas.

Regras de Negocio:
  1. Wildcard SSL para *.wedotalent.cc (Let's Encrypt ou Google-managed)
  2. DNS configurado no Google Cloud DNS com registro *.wedotalent.cc
  3. Nginx/proxy reverso roteando por subdomínio → tenant_id
  4. Redirecionamento de www e root para subdomínio padrão (app.wedotalent.cc)
  5. Suporte futuro a domínio customizado (ex: rh.itau.com.br) via campo custom_domain
  6. Tenant padrão (fallback) se subdomínio não encontrado na tabela
  7. Cache de resolução de tenant com TTL de 5 minutos
  8. Subdomínios reservados: www, app, api, admin, staging, dev

Requisitos Tecnicos:
  Frontend:
    - Detecção de subdomínio via window.location.hostname no client-side
    - Hook useTenant() que resolve tenant a partir do subdomínio
    - ThemeProvider dinâmico que aplica cores e logo do tenant
    - Fallback para branding padrão WeDo Talent se tenant não encontrado
    - Carregamento de logo via URL do tenant (logo_url)
  Backend:
    - Middleware TenantResolver que extrai subdomínio do Host header
    - Tabela tenants: id (UUID), subdomain (VARCHAR UNIQUE), company_name, logo_url, primary_color, secondary_color, custom_domain (nullable), favicon_url, created_at, updated_at
    - Endpoint GET /api/v1/tenants/{subdomain}/branding → { company_name, logo_url, primary_color, secondary_color, favicon_url }
    - Nginx config com server_name *.wedotalent.cc e proxy_pass para app
    - Validação de subdomínio: lowercase, alfanumérico + hífens, 3-63 chars
  Dados:
    - tenants: id, subdomain, company_name, logo_url, primary_color, secondary_color, custom_domain, favicon_url, is_active, created_at, updated_at
    - Seed inicial: tenant "app" (padrão WeDo Talent) + tenant "demo" (para testes)
  Validacoes:
    - Subdomínio deve ser único e não estar na lista de reservados
    - logo_url deve ser URL válida (HTTPS)
    - primary_color deve ser hex válido (#RRGGBB)
    - custom_domain deve ter CNAME configurado antes de ativar

Design & Componentes:
  Componentes Existentes:
    - LoginPage - tela de login (já existe)
    - AuthContext - contexto de autenticação
    - ThemeProvider - Next.js theme provider
  Novos Componentes:
    - TenantProvider - provider de contexto de tenant
    - TenantBrandingLoader - loader assíncrono de branding
    - DynamicLogo - componente que renderiza logo do tenant
  Design Tokens:
    Background: --lia-bg-primary (dinâmico por tenant, default #FFFFFF)
    Accent: --wedo-cyan (dinâmico por tenant, default #60BED1)
    Text: --lia-text-primary (#111827)
    Fallback: --lia-bg-secondary (#F3F4F6)
  Layout:
    Container: Mesmo layout do login atual
    Logo: Substituído dinamicamente pelo logo_url do tenant
    Cores: primary_color aplicada em botões e accents
    Favicon: favicon_url do tenant no <head>
  Estados:
    - Loading: skeleton enquanto resolve tenant
    - Resolved: branding do tenant aplicado
    - Fallback: branding padrão WeDo Talent
    - Error: tenant não encontrado → fallback + log
  Acessibilidade:
    - Contraste mínimo WCAG AA entre primary_color e texto
    - Alt text no logo dinâmico com company_name
    - Fallback de cor se primary_color não passar contraste

Comportamento de UI:
  Fluxo Principal:
    1. Usuário acessa itau.wedotalent.cc
    2. Client detecta subdomínio "itau" via window.location.hostname
    3. TenantProvider chama GET /api/v1/tenants/itau/branding
    4. Loading skeleton enquanto resolve
    5. Branding carregado: logo Itaú, cor laranja, favicon Itaú
    6. Tela de login renderiza com branding customizado
    7. Após login, branding persiste em toda a sessão

  Layout:
    Desktop: Logo centralizado (max 200px largura), card de login centralizado
    Mobile: Logo 100% largura com padding, card full-width
    Tablet: Mesmo layout desktop com max-w-md

  Estados de Botoes:
    Entrar:
      - Default: bg dinâmico (primary_color do tenant)
      - Hover: primary_color com 10% darker
      - Loading: spinner + "Entrando..."
      - Disabled: opacity 50% durante loading

  Validacoes Inline:
    Subdominio:
      - Não encontrado: fallback silencioso para branding padrão
    Logo:
      - Erro de carregamento: fallback para texto do company_name

  Mensagens de Feedback:
    - Tenant não encontrado: log interno, UX sem erro visível (fallback)
    - SSL inválido: erro de browser (não controlável pelo app)
    - Branding carregado: transição suave de skeleton para conteúdo

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md (Seções: 1.2 Paleta de Cores, 2.1 Botões, 2.2 Inputs & Forms, 2.3 Cards)"
  Figma: "[A ser preenchido pelo time de Design — tela de login multi-tenant]"
  Assets:
    - "Logo WeDo Talent (fallback): /public/logos/wedo-talent-logo.svg"
    - "Favicon padrão: /public/favicon.ico"
  Tokens:
    - "accent-primary: dinâmico por tenant (default #60BED1)"
    - "bg-primary: dinâmico por tenant (default #FFFFFF)"
    - "text-primary: #111827"

DoD:
  - [ ] Wildcard SSL emitido e configurado no Google Cloud
  - [ ] DNS wildcard *.wedotalent.cc configurado e propagado
  - [ ] Nginx config com wildcard server_name funcionando
  - [ ] Middleware TenantResolver extraindo subdomínio do Host header
  - [ ] Tabela tenants criada com migration e seed inicial
  - [ ] Endpoint GET /api/v1/tenants/{subdomain}/branding retornando dados
  - [ ] Frontend detectando subdomínio e aplicando branding dinâmico
  - [ ] Fallback para tenant padrão se subdomínio não encontrado
  - [ ] Cache de resolução de tenant com TTL 5min
  - [ ] Teste com 2+ subdomínios (itau.wedotalent.cc, demo.wedotalent.cc)
  - [ ] Responsivo mobile

Criterios de Aceitacao:
  - [ ] itau.wedotalent.cc resolve para tenant correto com branding Itaú
  - [ ] demo.wedotalent.cc resolve para tenant demo com branding demo
  - [ ] SSL válido em qualquer subdomínio (*.wedotalent.cc)
  - [ ] Logo e cores carregam dinamicamente por tenant
  - [ ] Subdomínio inexistente mostra branding padrão WeDo Talent (fallback)
  - [ ] Subdomínios reservados (www, api, admin) não conflitam
  - [ ] Favicon atualizado por tenant
  - [ ] Performance: resolução de tenant < 200ms (com cache)

Arquivos de Referencia (Prototipo Replit):
  - login-page.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/login-page.tsx
  - auth-context.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/auth-context.tsx
  - auth-headers.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/api/auth-headers.ts
  - workos.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/workos.ts
```

---

### CARD AUTH-006: Revisão Final de Design pelo Lucas
**Épico:** É1 — Autenticação

```yaml
Titulo: "[DESIGN] Revisão Final de Design/Marca pelo Lucas"
Tipo: Design
Area: Processo/Validação
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 3
Prioridade: Alta
Epic: EPIC-AUTH
Status: 📋 A Criar no Jira
Dependencias: AUTH-001

Descricao: |
  Lucas faz revisão final dos assets visuais: logo atualizado da WeDo Talent,
  marca da LIA, ícones, paleta de cores, e aplica nas telas de login/onboarding.
  Entrega inclui guia de marca para white label e assets em múltiplos formatos
  (SVG, PNG @1x/@2x/@3x).

Historia de Usuario: |
  Como stakeholder, eu quero que a identidade visual da plataforma
  esteja atualizada e consistente antes do lançamento do MVP,
  garantindo profissionalismo e reconhecimento de marca.

Regras de Negocio:
  1. Logo WeDo Talent atualizado (versões: completo, ícone, monocromático)
  2. Logo LIA atualizado (avatar, ícone, variações de cor)
  3. Paleta de cores validada e documentada (primária, secundária, semânticas)
  4. Assets para tela de login (background, ilustrações, logo)
  5. Assets para onboarding (ícones de etapas, ilustrações)
  6. Guia de marca para white label (o que pode/não pode ser customizado)
  7. Favicon e Open Graph images atualizados
  8. Email templates com marca atualizada (headers, footers)

Requisitos Tecnicos:
  Frontend:
    - Substituir assets de logo/marca em /public/logos/
    - Atualizar favicon.ico e apple-touch-icon.png
    - Atualizar Open Graph images em /public/images/
    - Aplicar paleta validada nos design tokens (globals.css)
  Backend:
    - Nenhuma alteração direta
  Dados:
    - Nenhuma alteração
  Validacoes:
    - SVG acessível (título e descrição)
    - PNG mínimo 2x para retina
    - Favicon em múltiplos tamanhos (16, 32, 180, 192, 512)

Design & Componentes:
  Componentes Existentes:
    - LoginPage - tela de login (atualizar logo)
    - Sidebar - menu lateral (atualizar logo)
    - Header - cabeçalho (atualizar logo)
    - EmailTemplate - templates de email (atualizar marca)
  Novos Componentes:
    - Nenhum (apenas atualização de assets)
  Design Tokens:
    Primary: --wedo-cyan (#60BED1) — a ser validado pelo Lucas
    Secondary: --wedo-navy (#1E3A5F) — a ser validado pelo Lucas
    Accent: --lia-purple (#8B5CF6) — a ser validado pelo Lucas
    Success: --wedo-green (#22C55E)
    Error: --electric-red (#de1c31)
    Warning: --wedo-yellow (#EAB308)
  Layout:
    Logo no Login: centralizado, max-width 200px, margin-bottom 32px
    Logo no Sidebar: 140px × auto, padding 16px
    Favicon: quadrado, fundo transparente (SVG) ou sólido (ICO)
  Estados:
    - Default: logo padrão WeDo Talent
    - White Label: logo substituído pelo tenant (AUTH-005)
    - Dark Mode: versão monocromática clara (futuro)
    - Loading: skeleton no lugar do logo
  Acessibilidade:
    - Alt text descritivo em todos os logos ("Logo WeDo Talent")
    - SVGs com role="img" e aria-label
    - Contraste WCAG AA em todas as variações de cor

Comportamento de UI:
  Fluxo Principal:
    1. Lucas entrega assets via Figma/Google Drive
    2. Dev substitui arquivos em /public/logos/ e /public/images/
    3. Atualiza referências de importação nos componentes
    4. Atualiza design tokens no globals.css se paleta mudar
    5. Verifica todas as telas: login, sidebar, header, emails
    6. Deploy e validação visual

  Layout:
    Login: Logo centralizado acima do formulário
    Sidebar: Logo no topo, versão compacta quando sidebar colapsado
    Header: Logo pequeno (32px height) à esquerda
    Emails: Logo no header do template, 200px max-width

  Estados de Botoes:
    N/A (card de design, sem botões novos)

  Validacoes Inline:
    N/A

  Mensagens de Feedback:
    - Assets não carregados: fallback para texto "WeDo Talent"
    - Imagem corrompida: alt text visível

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md (Seções: 1.2 Paleta de Cores, 1.3 Tipografia, 2.14 Avatars — Referência global de marca)"
  Figma: "[A ser preenchido pelo Lucas — link do projeto de marca]"
  Assets:
    - "Logo WeDo Talent: /public/logos/wedo-talent-logo.svg (a ser atualizado)"
    - "Logo LIA: /public/logos/lia-avatar.svg (a ser atualizado)"
    - "Favicon: /public/favicon.ico (a ser atualizado)"
  Tokens:
    - "accent-primary: #60BED1 (a ser validado)"
    - "accent-secondary: #1E3A5F (a ser validado)"
    - "lia-accent: #8B5CF6 (a ser validado)"

DoD:
  - [ ] Assets entregues pelo Lucas (logo, ícones, paleta)
  - [ ] Logo WeDo Talent atualizado na tela de login
  - [ ] Logo WeDo Talent atualizado no sidebar e header
  - [ ] Logo LIA (avatar) atualizado
  - [ ] Favicon atualizado em todos os tamanhos
  - [ ] Open Graph images atualizadas
  - [ ] Email templates com marca atualizada
  - [ ] Paleta de cores aplicada nos design tokens
  - [ ] Guia de marca para white label documentado
  - [ ] Todas as telas verificadas visualmente

Criterios de Aceitacao:
  - [ ] Logo WeDo Talent aparece corretamente em login, sidebar, header
  - [ ] Logo LIA aparece no chat e interações com IA
  - [ ] Favicon correto no browser tab
  - [ ] Paleta de cores consistente em toda a plataforma
  - [ ] Email templates com marca atualizada (verificar em 3 clients: Gmail, Outlook, Apple Mail)
  - [ ] Assets em SVG com acessibilidade (alt text, aria-label)
  - [ ] Guia de white label entregue e revisado

Arquivos de Referencia (Prototipo Replit):
  - login-page.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/login-page.tsx
  - auth-context.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/auth-context.tsx
  - globals.css: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/styles/globals.css
  - logos: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/public/logos/
```

---

## ÉPICO 2: WIZARD CONVERSACIONAL ⏸️ PÓS-MVP

> ⏸️ **ÉPICO INTEIRO MOVIDO PARA PÓS-MVP** — Decisão da reunião de 06/fev/2026 (Paulo + Anderson). O wizard conversacional completo é pós-MVP. No MVP, a criação de vagas será feita via formulário básico.
>
> **Exceções migradas para Épico 4 (WSI):** WIZ-008, WIZ-012 e WIZ-013 foram migrados para o Épico 4 (Geração de Perguntas WSI) pois são necessários para o fluxo de edição de vaga e geração de perguntas WSI no MVP.

### Arquitetura Técnica do Wizard (Referência Pós-MVP)

#### Intelligence Layer - Camada Centralizada de Inteligência

O Intelligence Layer (`lia-agent-system/app/services/intelligence_layer_service.py`) é a camada centralizada que fornece sugestões inteligentes para o Wizard.

**Métodos Públicos Implementados:**

| Método | Descrição |
|--------|-----------|
| `assess_data_quality()` | Avalia qualidade dos dados do draft |
| `build_intelligence_context()` | Constrói contexto para sugestões (Company Settings + ATS + Templates) |
| `apply_pattern_adjustment()` | Aplica ajustes baseados em padrões detectados |
| `generate_field_suggestion()` | Gera sugestão para campo específico com fonte e confiança |
| `log_insight()` | Registra insight para aprendizado |
| `record_insight_outcome()` | Registra resultado do insight (aceito/rejeitado) |
| `refresh_patterns()` | Atualiza padrões da empresa com novos dados |
| `get_wizard_enhancements()` | Obtém melhorias específicas para cada etapa do wizard |

**Hierarquia de Fontes de Dados (Prioridade):**

| # | Fonte | Precisão | Descrição |
|---|-------|----------|-----------|
| 1 | Company Settings | 100% | Configurações no Menu Configurações |
| 2 | Histórico LIA | 95% | Vagas criadas anteriormente na LIA |
| 3 | JDs Importados ATS | 85% | Gupy, Pandapé, StackOne, Merge |
| 4 | Workforce Planning | 80% | Planos de contratação |
| 5 | ETL Completo | 75% | Extração de sistemas externos |
| 6 | Templates Curados | 70% | 326 templates (fallback) |

#### ATS Clients - Integrações Implementadas

Localização: `lia-agent-system/app/services/ats_clients/`

| Cliente | Arquivo | Funcionalidades |
|---------|---------|-----------------|
| **Base** | `base.py` | Interface abstrata para todos os clientes |
| **Gupy** | `gupy.py` | Import/Export JDs, sync candidatos, webhooks |
| **Pandapé** | `pandape.py` | Import/Export JDs, sync candidatos, webhooks |
| **StackOne** | `stackone.py` | Unified HRIS/ATS API |
| **Merge** | `merge.py` | Multi-ATS/HRIS Integration |

#### Fast Track Mode - Reutilização de Vagas

O Fast Track permite criar novas vagas a partir de vagas anteriores ou templates curados:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           FAST TRACK MODE                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐       │
│  │  Vaga Anterior   │    │  Template Curado │    │   JD do ATS      │       │
│  │  (Histórico LIA) │    │  (326 templates) │    │  (Importado)     │       │
│  └────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘       │
│           │                       │                       │                  │
│           └───────────────────────┼───────────────────────┘                  │
│                                   │                                          │
│                                   ▼                                          │
│                    ┌──────────────────────────────┐                         │
│                    │  LIA apresenta dados         │                         │
│                    │  Recrutador confirma/ajusta  │                         │
│                    │  (Uma única revisão)         │                         │
│                    └──────────────────────────────┘                         │
│                                   │                                          │
│                                   ▼                                          │
│                    ┌──────────────────────────────┐                         │
│                    │  Publicação direta           │                         │
│                    │  (Pula etapas redundantes)   │                         │
│                    └──────────────────────────────┘                         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Características Fast Track:**
- **Copia tudo, pergunta uma vez**: Não fragmenta confirmações
- **Revisão concentrada**: Todos ajustes em uma única etapa
- **Regeneração inteligente**: Se algo crítico muda, LIA pergunta se deve regenerar dependências (ex: WSI questions)
- **Templates curados**: 326 templates em 9 categorias (tecnologia, comercial, RH, administrativo, finanças, operações, saúde, marketing, customer_success)

#### Templates Curados (326 total)

| Categoria | Quantidade | Subcategorias |
|-----------|------------|---------------|
| **tecnologia** | 119 | desenvolvimento, dados, infra, seguranca, design, gestao, arquitetura, qualidade, produto |
| **comercial** | 98 | inside_sales, field_sales, customer_success, gestao, canais, vendas_tecnicas, ecommerce, sales_ops |
| **rh** | 32 | recrutamento, business_partner, dp, remuneracao, td, desenvolvimento, cultura, gestao |
| **administrativo** | 21 | geral, secretariado, facilities, compras, documentacao, patrimonio, gestao |
| **financas** | 19 | contabilidade, fiscal, controladoria, planejamento, tesouraria, auditoria, gestao |
| **operacoes** | 14 | logistica, supply_chain, compras, qualidade, comex, gestao |
| **saude** | 13 | enfermagem, medicina, terapias, farmacia, gestao |
| **marketing** | 8 | digital, conteudo, branding, performance, growth, gestao |
| **customer_success** | 2 | cs_management, onboarding |

**WSI Quality Gates (100% compliance):**
- Mínimo 5 skills técnicas (com níveis: basic, intermediate, advanced)
- Mínimo 3 competências comportamentais (com justificativas)
- Mínimo 5 responsabilidades

---

### CARD WIZ-001: Interface Chat Conversacional
**Épico:** É2 — Wizard Conversacional

```yaml
Titulo: [FRONTEND] Interface de Chat Conversacional
Tipo: Feature
Area: Full-Stack
Sprint: Pós-MVP
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 8
Prioridade: Crítica
Epic: EPIC-WIZARD
Status: 📦 Backlog (Pós-MVP)

Descricao: |
  Interface de chat para criação de vagas conversacionalmente
  com a LIA, incluindo mensagens, sugestões clicáveis e resumo.

Historia de Usuario: |
  Como recrutador, eu quero criar uma vaga conversando com a LIA
  para não precisar preencher formulários extensos.

Regras de Negocio:
  1. Chat em tempo real com streaming de resposta
  2. Histórico de mensagens persistido
  3. Sugestões clicáveis para respostas rápidas
  4. Resumo da vaga atualizado em tempo real
  5. Botão "Pular para formulário" disponível
  6. Salvar rascunho a qualquer momento
  7. Voltar e editar mensagens anteriores

Requisitos Tecnicos:
  Frontend:
    - ChatInterface component (React)
    - MessageBubble (LIA vs User)
    - SuggestionButtons component
    - JobSummaryPanel component
    - InputArea com envio
    - Streaming via EventSource/SSE
  Backend:
    - POST /api/v1/wizard/message (streaming)
    - GET /api/v1/wizard/session/{id}
    - POST /api/v1/wizard/session/{id}/save
  Dados:
    - wizard_sessions: id, vacancy_id, messages, status, created_at
  Validacoes:
    - Mensagem não vazia
    - Sessão pertence ao usuário

Design & Componentes:
  Componentes Existentes:
    - Button - enviar, sugestões
    - Card - container
    - Input - campo de mensagem
    - Avatar - LIA e usuário
    - Skeleton - loading
  Novos Componentes:
    - ChatInterface - container principal
    - MessageBubble - bolha de mensagem
    - SuggestionChips - botões de sugestão
    - JobSummaryCard - resumo da vaga
    - StreamingText - texto com efeito typewriter
  Design Tokens:
    LIA Bubble: bg-lia-bg-secondary, border-left --wedo-cyan
    User Bubble: bg-wedo-cyan-light, align-right
    Suggestions: bg-white, border --wedo-cyan, hover bg-wedo-cyan-light
  Layout:
    Container: h-full flex flex-col
    Chat Area: flex-1 overflow-y-auto
    Summary: fixed right ou bottom (mobile)
    Input: sticky bottom
  Estados:
    - Typing (LIA pensando...)
    - Streaming (texto aparecendo)
    - Waiting (aguardando input)
    - Complete (vaga pronta)
  Acessibilidade:
    - aria-live="polite" para novas mensagens
    - Keyboard navigation para sugestões
    - Screen reader anuncia LIA respondendo

Comportamento de UI:
  Fluxo Principal:
    1. Usuário clica "Nova Vaga" → abre chat
    2. LIA envia mensagem de boas-vindas
    3. Usuário responde (texto ou clica sugestão)
    4. LIA processa e responde com streaming
    5. Resumo lateral atualiza em tempo real
    6. Ao completar, botão "Finalizar Vaga" aparece
  
  Estados de Mensagem:
    Enviando:
      - Bolha do usuário aparece imediatamente
      - Indicador "Enviando..." sutil
    LIA Respondendo:
      - Indicador "..." pulsando
      - Texto aparece caractere a caractere (streaming)
    Sugestões:
      - Aparecem após resposta da LIA
      - Click envia como mensagem do usuário
  
  Animações:
    - Scroll automático para última mensagem
    - Fade-in para novas mensagens
    - Typewriter para streaming
    - Pulse para indicador de digitação


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Chat funciona com streaming
  - [ ] Sugestões clicáveis funcionam
  - [ ] Resumo atualiza em tempo real
  - [ ] Histórico persistido
  - [ ] Responsivo mobile

Criterios de Aceitacao:
  - [ ] Mensagem enviada aparece instantaneamente
  - [ ] Resposta LIA aparece com streaming
  - [ ] Sugestões enviam mensagem ao clicar
  - [ ] Resumo reflete dados coletados
  - [ ] Botão salvar rascunho funciona

Arquivos de Referencia (Prototipo Replit):
  - ExpandedChatContext.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/expanded-chat/ExpandedChatContext.tsx
  - WizardHeader.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/expanded-chat/components/WizardHeader.tsx
  - WizardSidebar.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/expanded-chat/components/WizardSidebar.tsx
  - expanded-chat-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/expanded-chat-modal.tsx
  - voice-chat-button.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/chat/voice-chat-button.tsx
  - message-feedback.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/chat/message-feedback.tsx
  - use-job-wizard-backend.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/use-job-wizard-backend.ts
  - types.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/job-wizard/types.ts
```

---

### CARD WIZ-002: Orquestrador de Intenções
**Épico:** É2 — Wizard Conversacional

```yaml
Titulo: [AI] Orquestrador de Intenções do Wizard
Tipo: AI/Backend
Area: Full-Stack
Sprint: Pós-MVP
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 13
Prioridade: Crítica
Epic: EPIC-WIZARD
Status: 📦 Backlog (Pós-MVP)
Dependencias: WIZ-001

Descricao: |
  Sistema de IA que classifica a intenção do usuário e
  roteia para o handler apropriado (coleta de dados, 
  perguntas, insights, etc).

Historia de Usuario: |
  Como LIA, eu preciso entender o que o recrutador quer
  para responder de forma inteligente e coletar os dados certos.

Regras de Negocio:
  1. Classificar intenção: resposta_direta, pergunta, correcao, confirmacao
  2. Extrair entidades: cargo, salario, skills, local, modelo
  3. Manter contexto da conversa (últimas N mensagens)
  4. Validar dados extraídos contra schema da vaga
  5. Solicitar clarificação quando ambíguo
  6. Não repetir perguntas já respondidas
  7. Fluxo não-linear (usuário pode pular perguntas)

Requisitos Tecnicos:
  Backend:
    - IntentClassifier class
    - EntityExtractor class
    - WizardOrchestrator class
    - ConversationContext class
  AI:
    - Prompt de classificação de intenção
    - Prompt de extração de entidades (NER)
    - Few-shot examples para cada intenção
  Dados:
    - wizard_sessions: messages (array), extracted_data (jsonb)
  Cache:
    - Contexto da conversa em Redis (TTL 1h)

Integracoes Externas:
  Claude/Gemini:
    - Tipo: LLM
    - Uso: Classificação, extração, geração
    - Model: claude-3-sonnet (classificação), gemini-1.5-flash (extração)
    - Secret: via Replit Integrations
    - Custo: ~$0.003 por mensagem

Design & Componentes:
  N/A - Backend/AI

Comportamento de API:
  POST /api/v1/wizard/message:
    Request: {
      "session_id": "uuid",
      "message": "Preciso de um dev senior com React"
    }
    Response (streaming): {
      "type": "message",
      "content": "Ótimo! Um Desenvolvedor Senior...",
      "suggestions": ["R$ 15-18k", "R$ 18-22k", "Outro"],
      "extracted": {
        "title": "Desenvolvedor Senior",
        "skills": ["React"],
        "level": "senior"
      }
    }
  
  Intenções Suportadas:
    - provide_info: usuário dando informação
    - ask_question: usuário perguntando algo
    - correct: usuário corrigindo dado anterior
    - confirm: usuário confirmando dado
    - skip: usuário pulando pergunta
    - help: usuário pedindo ajuda

DoD:
  - [ ] Classificação de intenção funciona
  - [ ] Extração de entidades funciona
  - [ ] Contexto mantido entre mensagens
  - [ ] Fluxo não-linear funciona
  - [ ] Testes com 50+ exemplos

Criterios de Aceitacao:
  - [ ] "Quero um dev React" extrai skill e título
  - [ ] "Na verdade é Vue" corrige skill anterior
  - [ ] "Pula essa" marca campo como opcional
  - [ ] Contexto preservado após 10 mensagens

Arquivos de Referencia (Prototipo Replit):
  - intent_classifier.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/intent_classifier.py
  - enhanced_intent_classifier.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/enhanced_intent_classifier.py
  - job_wizard_graph.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/agents/job_wizard_graph.py
  - nodes.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/agents/nodes.py
  - wizard_smart_orchestrator.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/wizard_smart_orchestrator.py
  - wizard_orchestrator_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wizard_orchestrator_service.py
```

---

### CARD WIZ-003: Serviço de Insights de Mercado
**Épico:** É2 — Wizard Conversacional

```yaml
Titulo: [BACKEND] Serviço de Insights de Mercado
Tipo: Backend
Area: Backend
Sprint: Pós-MVP
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 8
Prioridade: Média
Epic: EPIC-WIZARD
Status: 📦 Backlog (Pós-MVP)

Descricao: |
  Serviço que fornece dados de mercado (salários, tempo de contratação,
  skills demandadas) para enriquecer as sugestões da LIA.

Historia de Usuario: |
  Como recrutador, eu quero ver dados de mercado enquanto crio a vaga
  para definir salário e requisitos competitivos.

Regras de Negocio:
  1. Dados baseados em vagas similares (internas + mercado)
  2. Faixa salarial por cargo/senioridade/região
  3. Tempo médio de preenchimento
  4. Skills mais demandadas para o cargo
  5. Cache de 24h para dados de mercado
  6. Fallback para médias gerais se sem dados específicos

Requisitos Tecnicos:
  Backend:
    - MarketInsightsService class
    - GET /api/v1/insights/salary
    - GET /api/v1/insights/skills
    - GET /api/v1/insights/time-to-fill
  Dados:
    - market_insights: cargo, region, salary_min, salary_max, avg_days, top_skills
    - vacancies: dados históricos internos
  Cache:
    - Redis: insights por cargo+região (TTL 24h)
  Agregações:
    - Mediana salarial (não média)
    - Percentis 25/50/75

Integracoes Externas:
  Dados Internos:
    - Tipo: Database aggregation
    - Uso: Vagas e contratações anteriores
    - Secret: Nenhum (dados internos)
  
  Dados Externos (futuro):
    - Glassdoor API, LinkedIn Salary
    - Custo: Enterprise pricing
    - Status: Pós-MVP

Design & Componentes:
  N/A - Backend only

Comportamento de API:
  GET /api/v1/insights/salary?cargo=desenvolvedor&nivel=senior&regiao=sp:
    Response: {
      "cargo": "Desenvolvedor Senior",
      "regiao": "São Paulo",
      "salario": {
        "p25": 12000,
        "mediana": 16000,
        "p75": 22000
      },
      "amostra": 45,
      "atualizado_em": "2026-01-20"
    }
  
  GET /api/v1/insights/skills?cargo=desenvolvedor-frontend:
    Response: {
      "cargo": "Desenvolvedor Frontend",
      "skills": [
        { "nome": "React", "demanda": 85 },
        { "nome": "TypeScript", "demanda": 78 },
        { "nome": "Vue", "demanda": 45 }
      ]
    }

DoD:
  - [ ] Endpoint de salário funciona
  - [ ] Endpoint de skills funciona
  - [ ] Cache implementado
  - [ ] Fallback para médias gerais

Criterios de Aceitacao:
  - [ ] Retorna faixa salarial para cargo conhecido
  - [ ] Retorna top 10 skills
  - [ ] Cache funciona (segunda chamada rápida)
  - [ ] Fallback quando cargo não encontrado

Arquivos de Referencia (Prototipo Replit):
  - market_benchmark_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/market_benchmark_service.py
  - job_insights_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/job_insights_service.py
  - compensation_analysis_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/compensation_analysis_service.py
  - intelligence_layer_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/intelligence_layer_service.py
  - job_wizard_tools.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/tools/job_wizard_tools.py
```

---

### CARD WIZ-004: Gerador de Job Description
**Épico:** É2 — Wizard Conversacional

```yaml
Titulo: [AI] Gerador de Job Description
Tipo: AI/Backend
Area: Full-Stack
Sprint: Pós-MVP
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 8
Prioridade: Alta
Epic: EPIC-WIZARD
Status: 📦 Backlog (Pós-MVP)
Dependencias: WIZ-002

Descricao: |
  Geração automática de descrição completa da vaga (JD)
  baseada nos dados coletados no wizard.

Historia de Usuario: |
  Como recrutador, eu quero que a LIA gere uma descrição
  profissional da vaga para economizar tempo.

Regras de Negocio:
  1. Gerar JD completa com seções padrão
  2. Tom de voz configurável (formal, casual, técnico)
  3. Incluir benefícios da empresa (se configurados)
  4. SEO-friendly para job boards
  5. Edição manual após geração
  6. Regenerar seções específicas
  7. Limite de 5.000 caracteres

Requisitos Tecnicos:
  Backend:
    - JDGeneratorService class
    - POST /api/v1/wizard/generate-jd
    - PUT /api/v1/wizard/regenerate-section
  AI:
    - Prompt template com seções
    - Tone modifiers
    - Few-shot examples por indústria
  Dados:
    - vacancies: description (text), description_sections (jsonb)
  Seções Padrão:
    - Sobre a empresa
    - Sobre a vaga
    - Responsabilidades
    - Requisitos
    - Diferenciais
    - Benefícios
    - Como se candidatar

Integracoes Externas:
  Claude:
    - Tipo: LLM
    - Uso: Geração de texto
    - Model: claude-3-sonnet
    - Custo: ~$0.01 por JD

Design & Componentes:
  N/A - Backend only (frontend no WIZ-007)

Comportamento de API:
  POST /api/v1/wizard/generate-jd:
    Request: {
      "vacancy_id": "uuid",
      "tone": "professional",
      "include_benefits": true
    }
    Response: {
      "description": "# Desenvolvedor Senior React\n\n## Sobre a Empresa...",
      "sections": {
        "about_company": "...",
        "about_role": "...",
        "responsibilities": ["...", "..."],
        "requirements": ["...", "..."],
        "nice_to_have": ["...", "..."],
        "benefits": ["...", "..."]
      },
      "char_count": 3240
    }

DoD:
  - [ ] JD gerada com todas as seções
  - [ ] Tom configurável funciona
  - [ ] Benefícios incluídos quando configurados
  - [ ] Limite de caracteres respeitado

Criterios de Aceitacao:
  - [ ] JD contém todas as 7 seções
  - [ ] Tom "casual" usa linguagem informal
  - [ ] Benefícios da empresa aparecem
  - [ ] Regenerar seção específica funciona

Arquivos de Referencia (Prototipo Replit):
  - jd_generator_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/jd_generator_service.py
  - jd_enrichment_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/jd_enrichment_service.py
  - jd_import_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/jd_import_service.py
  - job_wizard_tools.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/tools/job_wizard_tools.py
  - EnrichedJDStage.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/expanded-chat/stages/EnrichedJDStage.tsx
```

---

### CARD WIZ-005: Salvamento de Rascunho
**Épico:** É2 — Wizard Conversacional

```yaml
Titulo: [BACKEND] Salvamento de Rascunho da Vaga
Tipo: Backend
Area: Backend
Sprint: Pós-MVP
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 5
Prioridade: Alta
Epic: EPIC-WIZARD
Status: 📦 Backlog (Pós-MVP)

Descricao: |
  Sistema de salvamento automático e manual de rascunhos
  durante a criação da vaga no wizard.

Historia de Usuario: |
  Como recrutador, eu quero que meu progresso seja salvo
  para continuar depois sem perder dados.

Regras de Negocio:
  1. Autosave a cada 30 segundos de inatividade
  2. Salvamento manual via botão
  3. Rascunhos listados em "Minhas Vagas"
  4. Rascunho expira após 30 dias
  5. Converter rascunho em vaga ativa
  6. Máximo 10 rascunhos por usuário

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/vacancies/draft
    - PUT /api/v1/vacancies/draft/{id}
    - GET /api/v1/vacancies/drafts
    - POST /api/v1/vacancies/draft/{id}/publish
    - DELETE /api/v1/vacancies/draft/{id}
  Frontend:
    - Debounced autosave hook
    - Indicador "Salvando..." / "Salvo"
  Dados:
    - vacancies: status='draft', draft_data (jsonb), last_saved_at

Integracoes Externas:
  Nenhuma

Design & Componentes:
  Componentes:
    - AutosaveIndicator - "Salvo há 2 min"
    - DraftCard - card na lista de vagas
  Estados:
    - Saving: "Salvando..."
    - Saved: "Salvo há X min"
    - Error: "Erro ao salvar" + retry

Comportamento de UI:
  Autosave:
    1. Usuário para de digitar
    2. Timer de 30s inicia
    3. Após 30s, salva automaticamente
    4. Indicador muda para "Salvando..."
    5. Sucesso: "Salvo há 1 min" (atualiza timer)
    6. Erro: "Erro ao salvar" + botão retry
  
  Salvamento Manual:
    1. Usuário clica "Salvar rascunho"
    2. Salva imediatamente
    3. Toast "Rascunho salvo"

DoD:
  - [ ] Autosave funciona
  - [ ] Salvamento manual funciona
  - [ ] Lista de rascunhos exibe
  - [ ] Publicar rascunho funciona
  - [ ] Expiração de 30 dias

Criterios de Aceitacao:
  - [ ] Dados salvos após 30s de inatividade
  - [ ] Rascunho aparece na lista de vagas
  - [ ] Continuar rascunho carrega dados
  - [ ] Publicar converte para vaga ativa

Arquivos de Referencia (Prototipo Replit):
  - use-job-draft.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/use-job-draft.ts
  - use-wizard-auto-save.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/use-wizard-auto-save.ts
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/backend-proxy/wizard/smart-orchestrate/route.ts
  - wizard_data_priority_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wizard_data_priority_service.py
  - wizard_smart_orchestrator.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/wizard_smart_orchestrator.py
```

---

### CARD WIZ-006: Sugestões Clicáveis
**Épico:** É2 — Wizard Conversacional

```yaml
Titulo: [FRONTEND] Sugestões Clicáveis no Chat
Tipo: Frontend
Area: Frontend
Sprint: Pós-MVP
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 5
Prioridade: Alta
Epic: EPIC-WIZARD
Status: 📦 Backlog (Pós-MVP)
Dependencias: WIZ-001

Descricao: |
  Botões de sugestão que aparecem após respostas da LIA
  para acelerar a entrada de dados comuns.

Historia de Usuario: |
  Como recrutador, eu quero clicar em sugestões prontas
  para responder mais rápido sem digitar.

Regras de Negocio:
  1. Sugestões aparecem após cada resposta LIA
  2. Máximo 4 sugestões por vez
  3. Sugestões baseadas no contexto (salário, modelo, etc)
  4. Click envia como mensagem do usuário
  5. Opção "Outro" para resposta livre
  6. Sugestões desaparecem após resposta

Requisitos Tecnicos:
  Frontend:
    - SuggestionChips component
    - Animação de entrada/saída
    - Click handler envia mensagem
  Backend:
    - Sugestões incluídas na resposta da LIA
  Dados:
    - Sugestões geradas dinamicamente pelo orquestrador

Design & Componentes:
  Componentes:
    - SuggestionChip - botão individual
    - SuggestionGroup - container com chips
  Design Tokens:
    Default: bg-white, border --wedo-cyan, text --wedo-cyan
    Hover: bg-wedo-cyan-light (10%)
    Active: bg-wedo-cyan, text white
  Layout:
    Container: flex flex-wrap gap-2
    Chip: px-4 py-2 rounded-full
    Position: abaixo da última mensagem LIA
  Animações:
    - Fade-in staggered (cada chip com delay)
    - Fade-out ao enviar resposta

  Acessibilidade:
    - Keyboard navigation (Tab, Enter, Space, Escape)
    - Labels e placeholders descritivos
    - ARIA-labels em elementos interativos
    - Focus visible em todos os elementos clicáveis
    - Mensagens de erro anunciadas por screen readers
    - Contraste mínimo WCAG AA (4.5:1)

Comportamento de UI:
  Fluxo:
    1. LIA responde com sugestões no payload
    2. Chips aparecem com animação staggered
    3. Usuário clica em um chip
    4. Chip "pulsa" brevemente
    5. Mensagem do usuário aparece no chat
    6. Todos os chips desaparecem
    7. LIA processa e responde
  
  Tipos de Sugestão:
    Faixas Salariais:
      ["R$ 5-8k", "R$ 8-12k", "R$ 12-18k", "Outro"]
    Modelos de Trabalho:
      ["Remoto", "Híbrido", "Presencial"]
    Senioridade:
      ["Júnior", "Pleno", "Sênior", "Especialista"]
    Confirmação:
      ["Sim, está correto", "Preciso ajustar"]


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Chips aparecem após resposta LIA
  - [ ] Click envia mensagem
  - [ ] Animações funcionam
  - [ ] "Outro" permite resposta livre

Criterios de Aceitacao:
  - [ ] Máximo 4 chips exibidos
  - [ ] Click envia valor como mensagem
  - [ ] Chips somem após seleção
  - [ ] Responsivo em mobile

Arquivos de Referencia (Prototipo Replit):
  - use-wizard-suggestions.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/use-wizard-suggestions.ts
  - use-lia-suggestions.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/use-lia-suggestions.ts
  - AISuggestionBadge.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/ai/AISuggestionBadge.tsx
  - expandable-ai-prompt.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/expandable-ai-prompt.tsx
  - wizard_suggestions.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/wizard_suggestions.py
```

---

### CARD WIZ-007: Preview da Vaga (Live)
**Épico:** É2 — Wizard Conversacional

```yaml
Titulo: [FULL-STACK] Preview da Vaga em Tempo Real
Tipo: Full-Stack
Area: Full-Stack
Sprint: Pós-MVP
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 8
Prioridade: Média
Epic: EPIC-WIZARD
Status: 📦 Backlog (Pós-MVP)
Dependencias: WIZ-002

Descricao: |
  Painel lateral que mostra o resumo da vaga sendo criada,
  atualizando em tempo real conforme dados são coletados.

Historia de Usuario: |
  Como recrutador, eu quero ver um resumo da vaga enquanto converso
  para acompanhar o que já foi preenchido.

Regras de Negocio:
  1. Resumo atualiza em tempo real
  2. Campos preenchidos destacados
  3. Campos pendentes indicados
  4. Barra de progresso visual
  5. Click em campo pendente sugere pergunta
  6. Collapse em mobile (bottom sheet)

Requisitos Tecnicos:
  Frontend:
    - JobSummaryPanel component
    - ProgressBar component
    - FieldStatus indicators
    - Realtime sync via context/state
  Backend:
    - Dados extraídos retornados em cada resposta
  Dados:
    - extracted_data do wizard_session

Design & Componentes:
  Componentes:
    - JobSummaryPanel - container lateral
    - SummaryField - campo individual
    - ProgressBar - barra de progresso
    - CollapsibleSheet - mobile bottom sheet
  Design Tokens:
    Panel: bg-white, border-left --lia-border-subtle
    Field Filled: text --lia-text-primary
    Field Pending: text --lia-text-tertiary, italic
    Progress: bg-wedo-cyan
  Layout:
    Desktop: fixed right, w-80
    Mobile: bottom sheet, collapsible
    Campos: stacked vertical, gap-3

  Acessibilidade:
    - Keyboard navigation (Tab, Enter, Space, Escape)
    - Labels e placeholders descritivos
    - ARIA-labels em elementos interativos
    - Focus visible em todos os elementos clicáveis
    - Mensagens de erro anunciadas por screen readers
    - Contraste mínimo WCAG AA (4.5:1)

Comportamento de UI:
  Atualização em Tempo Real:
    1. LIA responde com extracted_data
    2. Panel atualiza campos correspondentes
    3. Animação de highlight no campo atualizado
    4. Progress bar incrementa
  
  Campos Exibidos:
    - Título da vaga
    - Empresa
    - Faixa salarial
    - Modelo (remoto/híbrido/presencial)
    - Local
    - Skills principais
    - Senioridade
    - Tipo de contrato
  
  Interações:
    - Hover em campo: tooltip com status
    - Click em pendente: foca chat para coletar
    - Collapse/expand em mobile


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Panel exibe todos os campos
  - [ ] Atualização em tempo real funciona
  - [ ] Progress bar reflete completude
  - [ ] Responsivo mobile (bottom sheet)

Criterios de Aceitacao:
  - [ ] Campo atualiza quando LIA extrai dado
  - [ ] Campos pendentes aparecem em itálico
  - [ ] Barra de progresso precisa
  - [ ] Mobile mostra bottom sheet

Arquivos de Referencia (Prototipo Replit):
  - ReviewPublishStage.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/job-wizard/stages/ReviewPublishStage.tsx
  - WizardSidebar.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/expanded-chat/components/WizardSidebar.tsx
  - types.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/job-description/types.ts
  - use-job-draft.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/use-job-draft.ts
```

---

### CARD WIZ-008: Formulário de Edição Completa
**Épico:** É4 — Geração de Perguntas WSI

```yaml
Titulo: [FULL-STACK] Formulário de Edição Completa da Vaga
Tipo: Full-Stack
Area: Full-Stack
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 8
Prioridade: Média
Epic: EPIC-WSI
Status: 📋 Pendente Jira
Dependencias: WIZ-005

Descricao: |
  Formulário tradicional para editar todos os campos da vaga,
  acessível via "Pular para formulário" ou após wizard.

Historia de Usuario: |
  Como recrutador, eu quero editar a vaga em um formulário
  para ajustar detalhes que prefiro preencher manualmente.

Regras de Negocio:
  1. Todos os campos editáveis
  2. Validação em tempo real
  3. Autosave (debounce 1s)
  4. Preview da JD renderizada
  5. Campos obrigatórios destacados
  6. Botão "Publicar Vaga" no final

Requisitos Tecnicos:
  Frontend:
    - VacancyEditForm component
    - Múltiplas seções (abas ou accordion)
    - react-hook-form + zod
    - Rich text editor para descrição
  Backend:
    - PUT /api/v1/vacancies/{id}
    - PATCH /api/v1/vacancies/{id}/publish
  Dados:
    - vacancies: todos os campos

Design & Componentes:
  Componentes:
    - VacancyEditForm - container principal
    - FormSection - seção colapsável
    - RichTextEditor - editor de descrição
    - TagInput - skills (chips)
    - SalaryRangeInput - slider de salário
    - LocationPicker - autocomplete de cidade
  Seções:
    1. Informações Básicas (título, área, senioridade)
    2. Requisitos (skills, experiência, formação)
    3. Compensação (salário, benefícios, modelo)
    4. Descrição (rich text)
    5. Configurações (status, publicação)

  Acessibilidade:
    - Keyboard navigation (Tab, Enter, Space, Escape)
    - Labels e placeholders descritivos
    - ARIA-labels em elementos interativos
    - Focus visible em todos os elementos clicáveis
    - Mensagens de erro anunciadas por screen readers
    - Contraste mínimo WCAG AA (4.5:1)

Comportamento de UI:
  Navegação:
    - Tabs ou stepper para seções
    - Indicador de seções com erros
    - Scroll suave entre seções
  
  Validação:
    - Inline nos campos
    - Resumo de erros no topo ao submeter
    - Campos obrigatórios com asterisco
  
  Publicação:
    - Validar todos os campos obrigatórios
    - Modal de confirmação
    - Redirect para Kanban da vaga


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Todos os campos editáveis
  - [ ] Validação funciona
  - [ ] Autosave implementado
  - [ ] Publicar vaga funciona

Criterios de Aceitacao:
  - [ ] Dados do wizard carregam no form
  - [ ] Erros de validação exibem inline
  - [ ] Autosave salva após 1s
  - [ ] Publicar muda status para "ativa"

Arquivos de Referencia (Prototipo Replit):
  - InputEvaluationStage.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/job-wizard/stages/InputEvaluationStage.tsx
  - SalaryStage.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/expanded-chat/stages/SalaryStage.tsx
  - CompetenciesStage.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/expanded-chat/stages/CompetenciesStage.tsx
  - WSIQuestionsStage.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/expanded-chat/stages/WSIQuestionsStage.tsx
  - ReviewPublishStage.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/job-wizard/stages/ReviewPublishStage.tsx
  - WizardSidebar.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/expanded-chat/components/WizardSidebar.tsx
  - types.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/job-wizard/types.ts
```

> **Nota**: Card migrado do Épico 2 (Wizard) para Épico 4 (WSI) por decisão da reunião de 06/fev/2026. No MVP, o wizard é pós-MVP; apenas a edição da vaga e geração de perguntas WSI ficam.

---

### CARD WIZ-009: Skip Calibração Conversacional
**Épico:** É2 — Wizard Conversacional

```yaml
Titulo: [FULL-STACK] Skip Calibração Conversacional
Tipo: Feature
Area: Full-Stack
Sprint: Pós-MVP
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 3
Prioridade: Alta
Epic: EPIC-WIZARD
Status: 📦 Backlog (Pós-MVP)

Descricao: |
  Fluxo conversacional que permite ao recrutador pular a etapa de
  calibração de busca, definindo o Match Threshold diretamente
  no painel lateral durante o wizard.

Historia de Usuario: |
  Como recrutador experiente, eu quero pular a calibração de busca
  para criar vagas mais rapidamente quando já conheço bem o perfil.

Regras de Negocio:
  1. LIA pergunta se recrutador quer calibrar ou pular
  2. Se pular, exibe slider de Match Threshold (70-90%)
  3. Threshold salvo na vaga para busca automática
  4. Opção de calibrar depois disponível

Requisitos Tecnicos:
  Frontend:
    - SkipCalibrationDialog component
    - MatchThresholdSlider component
  Backend:
    - PATCH /api/v1/vacancies/{id}/threshold

DoD:
  - [ ] Fluxo de skip funciona
  - [ ] Threshold persistido
  - [ ] Busca usa threshold

Criterios de Aceitacao:
  - [ ] Recrutador pode pular calibração
  - [ ] Threshold define filtro de busca
  - [ ] Opção de calibrar depois

Arquivos de Referencia (Prototipo Replit):
  - calibration-dashboard.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/calibration/calibration-dashboard.tsx
  - lia-feedback-widget.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/calibration/lia-feedback-widget.tsx
  - index.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/calibration/index.tsx
  - calibration-card.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/calibration-card.tsx
  - calibration_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/calibration_service.py
```

---

### CARD WIZ-010: Estágio de Salário Interativo
**Épico:** É2 — Wizard Conversacional

```yaml
Titulo: [FRONTEND] Estágio de Salário Interativo
Tipo: Feature
Area: Full-Stack
Sprint: Pós-MVP
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 5
Prioridade: Alta
Epic: EPIC-WIZARD
Status: 📦 Backlog (Pós-MVP)
Dependencias: WIZ-001

Descricao: |
  Estágio do wizard para definição interativa de faixa salarial
  com análise de mercado, comparação com histórico e sugestões
  da LIA baseadas em dados reais.

Historia de Usuario: |
  Como recrutador, eu quero definir a faixa salarial com ajuda
  da LIA para garantir competitividade no mercado.

Regras de Negocio:
  1. LIA sugere faixa com base em cargo, senioridade e região
  2. Exibe comparação com mercado (percentis)
  3. Alerta se faixa abaixo do mercado
  4. Permite ajuste com justificativa

Requisitos Tecnicos:
  Frontend:
    - SalaryStage.tsx component
    - SalaryRangeSlider component
    - MarketComparisonChart component
  Backend:
    - GET /api/v1/insights/salary

DoD:
  - [ ] Estágio funciona no wizard
  - [ ] Comparação de mercado exibida
  - [ ] Alertas configurados

Criterios de Aceitacao:
  - [ ] Faixa salarial definida
  - [ ] Comparação visual com mercado
  - [ ] Sugestões da LIA

Arquivos de Referencia (Prototipo Replit):
  - SalaryStage.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/expanded-chat/stages/SalaryStage.tsx
  - WizardSidebar.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/expanded-chat/components/WizardSidebar.tsx
  - compensation_analysis_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/compensation_analysis_service.py
  - market_benchmark_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/market_benchmark_service.py
```

---

### CARD WIZ-011: Estágio de Competências
**Épico:** É2 — Wizard Conversacional

```yaml
Titulo: [FRONTEND] Estágio de Competências
Tipo: Feature
Area: Full-Stack
Sprint: Pós-MVP
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 8
Prioridade: Crítica
Epic: EPIC-WIZARD
Status: 📦 Backlog (Pós-MVP)
Dependencias: WIZ-001

Descricao: |
  Estágio do wizard para definição de competências técnicas
  e comportamentais com sugestões inteligentes da LIA,
  níveis de proficiência e pesos para matching.

Historia de Usuario: |
  Como recrutador, eu quero definir as competências necessárias
  com ajuda da LIA para gerar perguntas WSI precisas.

Regras de Negocio:
  1. LIA sugere competências baseadas no cargo
  2. Competências técnicas com nível (básico, intermediário, avançado)
  3. Competências comportamentais com justificativa
  4. Pesos para cálculo de matching
  5. Mínimo 5 técnicas + 3 comportamentais

Requisitos Tecnicos:
  Frontend:
    - CompetenciesStage.tsx component
    - SkillSelector component
    - BehavioralCompetencyCard component
  Backend:
    - POST /api/v1/competencies/suggest

DoD:
  - [ ] Estágio funciona no wizard
  - [ ] Sugestões da LIA
  - [ ] Quality gates validados

Criterios de Aceitacao:
  - [ ] 5+ competências técnicas
  - [ ] 3+ competências comportamentais
  - [ ] Níveis definidos

Arquivos de Referencia (Prototipo Replit):
  - CompetenciesStage.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/expanded-chat/stages/CompetenciesStage.tsx
  - AddSkillModal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/expanded-chat/modals/AddSkillModal.tsx
  - skills_catalog_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/skills_catalog_service.py
  - skills_catalog.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/skills_catalog.py
```

---

### CARD WIZ-012: Estágio de Perguntas WSI
**Épico:** É4 — Geração de Perguntas WSI

```yaml
Titulo: [FRONTEND] Estágio de Perguntas WSI
Tipo: Feature
Area: Full-Stack
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 8
Prioridade: Crítica
Epic: EPIC-WSI
Status: 📋 Pendente Jira
Dependencias: WIZ-001

Descricao: |
  Estágio do wizard para geração e revisão de perguntas
  de triagem WSI, incluindo preview, edição e aprovação
  das perguntas geradas pela LIA.

Historia de Usuario: |
  Como recrutador, eu quero revisar e aprovar as perguntas
  de triagem antes de publicar a vaga.

Regras de Negocio:
  1. LIA gera perguntas baseadas em competências
  2. Preview das perguntas por bloco WSI
  3. Recrutador pode editar/remover perguntas
  4. Regeneração de perguntas individuais
  5. Aprovação final antes de publicar

Requisitos Tecnicos:
  Frontend:
    - WSIQuestionsStage.tsx component
    - QuestionPreview component
    - QuestionEditor component
  Backend:
    - POST /api/v1/wsi/generate-questions
    - PUT /api/v1/wsi/questions/{id}

DoD:
  - [ ] Estágio funciona no wizard
  - [ ] Perguntas geradas corretamente
  - [ ] Edição funciona

Criterios de Aceitacao:
  - [ ] Preview de perguntas
  - [ ] Edição inline
  - [ ] Regeneração funciona

Arquivos de Referencia (Prototipo Replit):
  - WSIQuestionsStage.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/expanded-chat/stages/WSIQuestionsStage.tsx
  - WSIQualityBar.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/expanded-chat/components/WSIQualityBar.tsx
  - wsi_question_generator.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_question_generator.py
  - wsi_question_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_question_service.py
  - wsi_questions.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/wsi_questions.py
```

> **Nota**: Card migrado do Épico 2 (Wizard) para Épico 4 (WSI) por decisão da reunião de 06/fev/2026. No MVP, o wizard é pós-MVP; apenas a edição da vaga e geração de perguntas WSI ficam.

---

### CARD WIZ-013: Quality Gates WSI
**Épico:** É4 — Geração de Perguntas WSI

```yaml
Titulo: [BACKEND] Quality Gates WSI
Tipo: Feature
Area: Full-Stack
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 5
Prioridade: Alta
Epic: EPIC-WSI
Status: 📋 Pendente Jira
Dependencias: WIZ-002

Descricao: |
  Sistema de validação que garante que a vaga atende aos
  critérios mínimos de qualidade WSI antes de publicação:
  competências, perguntas e dados obrigatórios.

Historia de Usuario: |
  Como sistema, eu quero validar que todas as vagas
  publicadas têm dados suficientes para triagem WSI.

Regras de Negocio:
  1. Mínimo 5 competências técnicas
  2. Mínimo 3 competências comportamentais
  3. Mínimo 5 responsabilidades
  4. Perguntas WSI geradas e aprovadas
  5. Faixa salarial definida
  6. Bloqueio de publicação se gates falham

Requisitos Tecnicos:
  Frontend:
    - useWSIQualityGates.ts hook
    - QualityGateIndicator component
  Backend:
    - POST /api/v1/vacancies/{id}/validate-wsi

DoD:
  - [ ] Validação funciona
  - [ ] Bloqueio se inválido
  - [ ] Mensagens claras

Criterios de Aceitacao:
  - [ ] Gates validados antes de publicar
  - [ ] Erros exibidos ao recrutador
  - [ ] Possível ignorar com justificativa

Arquivos de Referencia (Prototipo Replit):
  - WSIQualityBar.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/expanded-chat/components/WSIQualityBar.tsx
  - wsi_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_service.py
  - confidence_policy_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/confidence_policy_service.py
  - wsi.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/wsi.py
  - wsi_endpoints.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/wsi_endpoints.py
```

> **Nota**: Card migrado do Épico 2 (Wizard) para Épico 4 (WSI) por decisão da reunião de 06/fev/2026. No MVP, o wizard é pós-MVP; apenas a edição da vaga e geração de perguntas WSI ficam.

---

### CARD WIZ-014: Revisão Metodologia Wizard com André
**Épico:** É2 — Wizard Conversacional

```yaml
Titulo: "[PROCESSO] Revisão de Metodologia Wizard Ponta a Ponta com André"
Tipo: Processo/Validação
Area: Processo/Validação
Sprint: Pós-MVP
Pontos: 5
Prioridade: Média
Epic: EPIC-WIZARD
Status: ⏸️ Pós-MVP
Dependencias: WSI-001, TRI-004, SCO-001

Descricao: |
  Sessão de revisão com André para validar toda a metodologia WSI
  implementada no wizard: geração de perguntas, condução de triagem,
  avaliação de respostas, e cálculo de scores. Só pode acontecer
  quando o fluxo completo (wizard → perguntas → triagem → score)
  estiver funcional no protótipo ou em staging.

Historia de Usuario: |
  Como responsável pela metodologia WSI, André quer validar que a
  implementação técnica preserva a integridade científica do método,
  incluindo sequência de perguntas, critérios de avaliação e pesos.

Regras de Negocio:
  1. Pré-requisito: geração de perguntas WSI (Épico 4) funcional
  2. Pré-requisito: triagem WhatsApp (Épico 5) funcional com respostas
  3. Pré-requisito: cálculo de score WSI (Épico 6) funcional
  4. André valida: sequência de perguntas, critérios de avaliação, pesos por bloco
  5. André valida: tom conversacional da LIA na triagem
  6. André valida: interpretação de respostas e scoring
  7. Resultado: documento de validação + lista de ajustes necessários
  8. Ajustes geram novos cards de correção no backlog
  9. Segunda rodada de validação após ajustes implementados

Requisitos Tecnicos:
  Frontend:
    - Nenhum componente novo direto
    - Demo funcional do fluxo completo para André testar
    - Possibilidade de gravar sessão para referência
  Backend:
    - Nenhuma alteração direta
    - Dados de teste com vagas e candidatos realistas para validação
  Dados:
    - Seed de vagas de teste variadas (tech, comercial, liderança)
    - Seed de candidatos simulados para triagem
  Validacoes:
    - Checklist de validação metodológica (preparar antes da sessão)
    - Documento de conformidade WSI preenchido por André

Design & Componentes:
  Componentes Existentes:
    - JobWizard - wizard de criação de vaga (fluxo completo)
    - WSIQuestionsStage - estágio de perguntas WSI
    - WSIQuestionsPanel - painel de perguntas geradas
    - ScreeningChat - chat de triagem (candidato)
    - ScoreDisplay - exibição de score WSI
  Novos Componentes:
    - Nenhum (validação de processo, não de UI)
  Design Tokens:
    N/A (sem alterações visuais)
  Layout:
    N/A (sessão presencial/remota de validação)
  Estados:
    - Pré-validação: preparação de dados e ambiente
    - Em validação: sessão com André em andamento
    - Pós-validação: documento de feedback recebido
    - Ajustes: cards de correção criados e em andamento
  Acessibilidade:
    N/A (processo, não componente)

Comportamento de UI:
  Fluxo Principal:
    1. Preparar ambiente de staging/demo com dados realistas
    2. Agendar sessão de 2-3h com André
    3. André navega pelo fluxo: criar vaga → gerar perguntas → simular triagem → ver scores
    4. André documenta observações por bloco WSI
    5. Consolidar feedback em documento de validação
    6. Criar cards de ajuste para cada item identificado
    7. Implementar ajustes
    8. Segunda rodada de validação (se necessário)

  Layout:
    N/A (processo de validação)

  Estados de Botoes:
    N/A

  Validacoes Inline:
    N/A

  Mensagens de Feedback:
    N/A

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md (Seções: PARTE 3 Padrões de Interface — Referência metodológica)"
  Figma: "N/A (processo de validação)"
  Assets:
    - "Checklist de validação WSI (a ser criado antes da sessão)"
    - "Template de documento de validação metodológica"
  Tokens:
    - "N/A"

DoD:
  - [ ] Sessão de validação realizada com André (2-3h)
  - [ ] Documento de validação criado com observações por bloco WSI
  - [ ] Ajustes identificados registrados como cards no Jira
  - [ ] Priorização dos ajustes definida com André
  - [ ] Segunda rodada de validação agendada (se necessário)

Criterios de Aceitacao:
  - [ ] André consegue navegar pelo fluxo completo: vaga → perguntas → triagem → score
  - [ ] Perguntas geradas estão em conformidade com a metodologia WSI
  - [ ] Sequência de blocos WSI respeita a ordem metodológica
  - [ ] Critérios de avaliação e pesos estão corretos por bloco
  - [ ] Tom conversacional da LIA é adequado para triagem profissional
  - [ ] Scoring de respostas reflete a metodologia validada
  - [ ] Documento de validação assinado/aprovado por André

Arquivos de Referencia (Prototipo Replit):
  - WSIQuestionsStage.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/job-wizard/stages/WSIQuestionsStage.tsx
  - WSIQuestionsPanel.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/ui-actions/panels/WSIQuestionsPanel.tsx
  - screening-config: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/screening-config/
  - wsi-components: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/wsi/
```

---

## ÉPICO 3: BUSCA E MAPEAMENTO

---

### CARD MAP-001: Lista de Candidatos da Base
**Épico:** É3 — Busca e Mapeamento

> **⚠️ DISCLAIMER — Protótipo Replit em Atualização:** O protótipo Replit deste card ainda não foi atualizado com as sugestões da reunião com o André. **As melhorias de UI serão implementadas no protótipo Replit para servir como referência visual atualizada para a implementação em Vue/Nuxt/Vuetify.** Aguarde a atualização do protótipo antes de usar os componentes como referência final de UI.

```yaml
Titulo: [FRONTEND] Lista de Candidatos da Base
Tipo: Frontend
Area: Frontend
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 5
Prioridade: Alta
Epic: EPIC-MAPPING
Status: 📋 Pendente Jira

Descricao: |
  Tela de listagem de candidatos da base interna com cards
  informativos, paginacao e visualizacao em grid/lista.

Historia de Usuario: |
  Como recrutador, eu quero visualizar todos os candidatos da base
  para identificar potenciais talentos para minhas vagas.

Regras de Negocio:
  1. Exibir foto, nome, titulo atual e localizacao
  2. Mostrar skills principais (max 5 chips)
  3. Indicar status (disponivel, empregado, etc)
  4. Paginacao de 20 candidatos por pagina
  5. Toggle entre visualizacao grid e lista
  6. Ordenacao por nome, data de cadastro, relevancia

Requisitos Tecnicos:
  Frontend:
    - CandidateList component (React)
    - CandidateCard component
    - Paginacao com react-query
    - Toggle grid/lista
  Backend:
    - GET /api/backend-proxy/candidates
    - Query params: page, limit, sort, order
  Dados:
    - candidates: id, name, email, phone, title, location, skills, avatar_url, status

Design & Componentes:
  Componentes Existentes:
    - Card - container do candidato
    - Avatar - foto do candidato
    - Badge - skills e status
    - Pagination - navegacao entre paginas
    - Toggle - grid/lista
    - Skeleton - loading state
  Novos Componentes:
    - CandidateCard - card individual
    - CandidateGrid - layout em grid
    - CandidateListView - layout em lista
  Design Tokens:
    Background: --lia-bg-primary (#FFFFFF)
    Card: lia-card com lia-shadow-sm
    Text: --lia-text-primary (#111827)
    Badge Skills: bg-wedo-cyan-light, text-wedo-cyan
    Badge Status: varies (green, yellow, gray)
  Layout:
    Container: max-w-7xl mx-auto
    Grid: grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4
    List: flex flex-col gap-3
  Estados:
    - Loading (skeletons)
    - Empty (ilustracao + CTA)
    - Populated (cards)
    - Error (retry)
  Acessibilidade:
    - Cards navegaveis por teclado
    - ARIA labels para acoes
    - Alt text em avatares
    - Focus visible nos cards

Comportamento de UI:
  Fluxo Principal:
    1. Usuario acessa /funil-de-talentos
    2. Skeleton loading enquanto carrega
    3. Cards aparecem em grid (padrao)
    4. Hover no card mostra acoes rapidas
    5. Click no card abre preview lateral
    6. Scroll infinito ou paginacao

  Interacoes:
    Card Hover:
      - Sombra aumenta
      - Botoes de acao aparecem
    Toggle Grid/Lista:
      - Animacao suave de transicao
    Paginacao:
      - Scroll to top ao mudar pagina


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Lista de candidatos exibe corretamente
  - [ ] Paginacao funciona
  - [ ] Toggle grid/lista funciona
  - [ ] Responsivo mobile

Criterios de Aceitacao:
  - [ ] Cards exibem foto, nome, titulo, skills
  - [ ] Maximo 5 skills por card
  - [ ] Paginacao de 20 por pagina
  - [ ] Toggle alterna entre grid e lista

Arquivos de Referencia (Prototipo Replit):
  - search-results-card.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/search-results-card.tsx
  - search-preview-card.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/search-preview-card.tsx
  - CandidatesTable.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/candidates/CandidatesTable.tsx
  - CandidatesHeader.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/candidates/CandidatesHeader.tsx
  - types.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/candidates/types.ts
  - candidate-preview.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/candidate-preview.tsx
  - useSearchFlow.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/useSearchFlow.ts
```

---

### CARD MAP-002: Busca Semântica com Elasticsearch + PG Vector + WRF
**Épico:** É3 — Busca e Mapeamento

> **⚠️ DISCLAIMER — Protótipo Replit em Atualização:** O protótipo Replit deste card ainda não foi atualizado com as sugestões da reunião com o André. **As melhorias de UI serão implementadas no protótipo Replit para servir como referência visual atualizada para a implementação em Vue/Nuxt/Vuetify.** Aguarde a atualização do protótipo antes de usar os componentes como referência final de UI.

```yaml
Titulo: [BACKEND] Busca Semântica com Elasticsearch + PG Vector + WRF
Tipo: Backend
Area: Backend
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 8
Prioridade: Alta
Epic: EPIC-MAPPING
Status: 📋 Pendente Jira

Descricao: |
  Serviço de busca híbrida com arquitetura dual:
  - Elasticsearch 8.x para busca full-text/keyword (chave-valor, BM25)
  - PG Vector (pgvector extension) para busca semântica via embeddings
  - WRF (Weighted Rank Fusion) para fusão dos resultados de ambas as fontes
  
  O Gemini (text-embedding-004) é utilizado para gerar os embeddings
  que são armazenados e buscados via PG Vector.
  
  Nota reunião Victhor: Arquitetura confirmada como ES (armazenamento 
  chave-valor/full-text) + PG Vector (semântico) + WRF para fusão de resultados.

Historia de Usuario: |
  Como recrutador, eu quero buscar candidatos descrevendo o perfil
  em linguagem natural para encontrar matches mais precisos,
  combinando busca por palavras-chave e busca semântica.

Regras de Negocio:
  1. Aceitar queries em linguagem natural
  2. Busca paralela: Elasticsearch (full-text/BM25) + PG Vector (semântico)
  3. Gerar embeddings com Gemini text-embedding-004 para PG Vector
  4. WRF (Weighted Rank Fusion) para merge dos resultados
  5. Threshold minimo de similaridade semântica: 0.7
  6. Cache de embeddings de candidatos
  7. Retornar candidatos ranqueados pelo score combinado WRF

Requisitos Tecnicos:
  Backend:
    - POST /api/backend-proxy/search/candidates
    - HybridSearchService class (orquestra ES + PG Vector + WRF)
    - Elasticsearch 8.x para busca chave-valor/full-text (BM25)
    - PG Vector (pgvector extension) para busca semântica/embedding
    - WRF (Weighted Rank Fusion) para fusão de resultados de ambas as fontes
    - Gemini embedding model (text-embedding-004) para gerar embeddings no PG Vector
  Dados:
    - Elasticsearch: índices de candidatos (full-text, skills, títulos)
    - candidate_embeddings: candidate_id, embedding (vector 768) no PG Vector
    - Indice HNSW para busca rápida no PG Vector
  Validacoes:
    - Query minimo 3 palavras
    - Query maximo 500 caracteres

Integracoes Externas:
  Google Gemini:
    - Tipo: Embeddings (para PG Vector)
    - Model: text-embedding-004
    - Dimensao: 768
    - Endpoint: generativelanguage.googleapis.com
    - Secret: GOOGLE_AI_API_KEY (ja configurado)
    - Custo: ~$0.00004 por 1000 tokens
    - Rate Limit: 1500 RPM
  Elasticsearch:
    - Versão: 8.x
    - Uso: Busca full-text/keyword (BM25), armazenamento chave-valor

Design & Componentes:
  N/A - Backend only

Comportamento de API:
  POST /api/backend-proxy/search/candidates:
    Request: {
      "query": "desenvolvedor react senior com experiencia em fintech",
      "limit": 10,
      "min_similarity": 0.7,
      "filters": {
        "location": "Sao Paulo",
        "min_experience_years": 5
      }
    }
    Response: {
      "candidates": [
        {
          "id": "uuid",
          "name": "Joao Silva",
          "title": "Senior React Developer",
          "wrf_score": 0.92,
          "es_score": 0.88,
          "semantic_score": 0.95,
          "skills": ["React", "TypeScript", "Node.js"],
          "location": "Sao Paulo"
        }
      ],
      "total_available": 45,
      "has_more": true,
      "query_embedding_cached": true
    }

DoD:
  - [ ] Elasticsearch busca full-text funciona
  - [ ] PG Vector busca semântica funciona
  - [ ] WRF merge resultados corretamente
  - [ ] Embeddings gerados via Gemini corretamente
  - [ ] Cache de embeddings implementado

Criterios de Aceitacao:
  - [ ] Query natural retorna candidatos relevantes
  - [ ] Score WRF combinado de 0 a 1
  - [ ] Filtros combinam com busca híbrida
  - [ ] Tempo de resposta < 2s
  - [ ] Resultados ES e PG Vector são fundidos via WRF

Arquivos de Referencia (Prototipo Replit):
  - useSemanticSearch.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/useSemanticSearch.ts
  - useUnifiedSearch.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/useUnifiedSearch.ts
  - candidate-search.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/api/candidate-search.ts
  - smart-search-input.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/smart-search-input.tsx
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - embedding_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/embedding_service.py
  - vacancy_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/vacancy_search_service.py
  - search_assistant.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/search_assistant.py
```

---

### CARD MAP-003: Filtros Avancados
**Épico:** É3 — Busca e Mapeamento

> **⚠️ DISCLAIMER — Protótipo Replit em Atualização:** O protótipo Replit deste card ainda não foi atualizado com as sugestões da reunião com o André. **As melhorias de UI serão implementadas no protótipo Replit para servir como referência visual atualizada para a implementação em Vue/Nuxt/Vuetify.** Aguarde a atualização do protótipo antes de usar os componentes como referência final de UI.

```yaml
Titulo: [FULL-STACK] Filtros Avancados de Candidatos
Tipo: Full-Stack
Area: Full-Stack
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 13
Prioridade: Alta
Epic: EPIC-MAPPING
Status: 📋 Pendente Jira

Descricao: |
  Sistema de filtros combinados para refinar busca de candidatos
  por skills, experiencia, localizacao, disponibilidade e mais.
  
  Nota reunião Victhor: Filtros de shortlisted/placement apresentaram 
  dificuldade técnica com desdobramentos (data, vagas específicas). 
  Felipe quase finalizou.

Historia de Usuario: |
  Como recrutador, eu quero aplicar multiplos filtros na busca
  para encontrar candidatos que atendam criterios especificos.

Regras de Negocio:
  1. Filtros combinaveis (AND logico)
  2. Skills: autocomplete com sugestoes
  3. Experiencia: slider de anos (0-20+)
  4. Localizacao: autocomplete de cidades
  5. Disponibilidade: imediata, 15 dias, 30 dias, etc
  6. Faixa salarial: slider de range
  7. Senioridade: junior, pleno, senior, especialista
  8. Modelo: remoto, hibrido, presencial
  9. Salvar filtros como preset
  10. Filtro por status de pipeline: shortlisted, placement
  11. Filtro por vaga específica (dropdown com busca)
  12. Filtro por data: período de cadastro, período de última atualização
  13. Desdobramentos de shortlisted: data de inclusão, vaga de origem
  14. Desdobramentos de placement: data de colocação, vaga de destino, empresa cliente

Requisitos Tecnicos:
  Frontend:
    - FilterPanel component
    - FilterChips component (tags ativas)
    - Autocomplete para skills e localizacao
    - Range sliders para experiencia e salario
    - Preset de filtros salvos
  Backend:
    - GET /api/backend-proxy/candidates?filters=...
    - GET /api/backend-proxy/search/filters/presets
    - POST /api/backend-proxy/search/filters/presets
  Dados:
    - filter_presets: id, user_id, name, filters (jsonb)

Design & Componentes:
  Componentes Existentes:
    - Select - filtros dropdown
    - Slider - ranges numericos
    - Checkbox - opcoes multiplas
    - Button - aplicar, limpar
    - Badge - filtros ativos
  Novos Componentes:
    - FilterPanel - painel lateral/colapsavel
    - FilterChip - tag de filtro ativo
    - SkillAutocomplete - busca de skills
    - LocationAutocomplete - busca de cidades
    - RangeSlider - slider duplo para ranges
    - FilterPresetSelect - dropdown de presets salvos
  Design Tokens:
    Panel: bg-white, border-right --lia-border-subtle
    Active Filter: bg-wedo-cyan-light, text-wedo-cyan
    Clear Button: text --electric-red
  Layout:
    Desktop: sidebar left, w-72
    Mobile: bottom sheet colapsavel
    Chips: flex flex-wrap gap-2 acima dos resultados

  Acessibilidade:
    - Keyboard navigation (Tab, Enter, Space, Escape)
    - Labels e placeholders descritivos
    - ARIA-labels em elementos interativos
    - Focus visible em todos os elementos clicáveis
    - Mensagens de erro anunciadas por screen readers
    - Contraste mínimo WCAG AA (4.5:1)

Comportamento de UI:
  Fluxo Principal:
    1. Usuario abre painel de filtros
    2. Seleciona/digita valores desejados
    3. Filtros aplicam em tempo real (debounce 300ms)
    4. Chips de filtros ativos aparecem
    5. Click no X do chip remove filtro
    6. Botao "Limpar todos" reseta

  Interacoes:
    Skill Autocomplete:
      - Digitar 2+ chars mostra sugestoes
      - Click ou Enter seleciona
      - Chip adicionado, input limpa
    Range Slider:
      - Drag handles para ajustar
      - Labels mostram valores atuais
    Salvar Preset:
      - Click "Salvar filtros"
      - Modal com input de nome
      - Preset aparece no dropdown


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Todos os filtros funcionam
  - [ ] Filtros combinam corretamente
  - [ ] Chips de filtros ativos exibem
  - [ ] Presets podem ser salvos

Criterios de Aceitacao:
  - [ ] Autocomplete de skills funciona
  - [ ] Slider de experiencia filtra corretamente
  - [ ] Multiplos filtros aplicam AND
  - [ ] Limpar remove todos os filtros
  - [ ] Filtro shortlisted funciona com desdobramentos
  - [ ] Filtro placement funciona com desdobramentos
  - [ ] Filtro por data de cadastro funciona
  - [ ] Filtro por vaga específica com busca

Arquivos de Referencia (Prototipo Replit):
  - advanced-search.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/advanced-search.tsx
  - advanced-filters-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/advanced-filters-modal.tsx
  - filter-autocomplete.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/filter-autocomplete.tsx
  - SkillsFilterInput.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/SkillsFilterInput.tsx
  - LocationFilterInput.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/LocationFilterInput.tsx
  - CompanyFilterInput.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/CompanyFilterInput.tsx
  - IndustryFilterInput.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/IndustryFilterInput.tsx
  - LanguageFilterInput.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/LanguageFilterInput.tsx
  - UniversitiesFilterInput.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/UniversitiesFilterInput.tsx
  - ExpertiseAreasInput.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/ExpertiseAreasInput.tsx
  - DegreeRequirementsInput.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/DegreeRequirementsInput.tsx
  - GraduationYearInput.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/GraduationYearInput.tsx
  - RadiusDropdown.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/RadiusDropdown.tsx
  - TimezoneDropdown.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/TimezoneDropdown.tsx
  - FundingStagesInput.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/FundingStagesInput.tsx
```

---

### CARD MAP-004: Adicionar Candidato a Vaga
**Épico:** É3 — Busca e Mapeamento

> **⚠️ DISCLAIMER — Protótipo Replit em Atualização:** O protótipo Replit deste card ainda não foi atualizado com as sugestões da reunião com o André. **As melhorias de UI serão implementadas no protótipo Replit para servir como referência visual atualizada para a implementação em Vue/Nuxt/Vuetify.** Aguarde a atualização do protótipo antes de usar os componentes como referência final de UI.

```yaml
Titulo: [FULL-STACK] Adicionar Candidato a Vaga
Tipo: Full-Stack
Area: Full-Stack
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 5
Prioridade: Alta
Epic: EPIC-MAPPING
Status: 📋 Pendente Jira
Dependencias: MAP-001

Descricao: |
  Funcionalidade para adicionar um ou mais candidatos a uma vaga
  especifica, movendo-os para a coluna "Funil" do kanban.

Historia de Usuario: |
  Como recrutador, eu quero adicionar candidatos encontrados
  a uma vaga para iniciar o processo de triagem.

Regras de Negocio:
  1. Selecao individual ou em massa
  2. Escolher vaga destino via modal/dropdown
  3. Candidato nao pode estar duplicado na vaga
  4. Candidato adicionado vai para coluna "Funil"
  5. Notificacao de sucesso com link para vaga
  6. Historico de adicao registrado
  7. Limite de 100 candidatos por adicao em massa

Requisitos Tecnicos:
  Frontend:
    - AddToJobModal component
    - Checkbox de selecao multipla
    - JobSelect dropdown com busca
    - Bulk action bar quando selecao ativa
  Backend:
    - POST /api/backend-proxy/job-vacancies/{jobId}/add-candidates
    - Request: { candidate_ids: string[] }
    - Response: { added: number, duplicates: number, errors: [] }
  Dados:
    - job_candidates: job_id, candidate_id, stage, added_at, added_by
    - Constraint: UNIQUE(job_id, candidate_id)

Design & Componentes:
  Componentes Existentes:
    - Modal - container do dialogo
    - Select - dropdown de vagas
    - Checkbox - selecao de candidatos
    - Button - confirmar, cancelar
    - Toast - feedback
  Novos Componentes:
    - AddToJobModal - modal de adicao
    - JobSelectDropdown - select com busca de vagas
    - BulkActionBar - barra flutuante para acoes em massa
  Design Tokens:
    Modal: bg-white, lia-shadow-lg
    Select: bg-white, border --lia-border-default
    Confirm: bg-wedo-cyan
    Cancel: bg-lia-bg-tertiary
  Layout:
    Modal: max-w-md, centered
    Bulk Bar: fixed bottom, w-full, bg-wedo-cyan
  Estados:
    - Idle (botao habilitado)
    - Selecting (checkbox ativo)
    - Modal Open
    - Loading (spinner)
    - Success (toast)
    - Error (toast vermelho)
  Acessibilidade:
    - Modal trap focus
    - ESC fecha modal
    - ARIA labels em checkboxes
    - Anuncio de resultados

Comportamento de UI:
  Fluxo Individual:
    1. Usuario hover no card do candidato
    2. Botao "Adicionar a vaga" aparece
    3. Click abre modal com dropdown de vagas
    4. Usuario seleciona vaga
    5. Click "Adicionar"
    6. Loading spinner
    7. Toast "Candidato adicionado a [vaga]"

  Fluxo em Massa:
    1. Usuario clica checkbox em candidatos
    2. Barra flutuante aparece: "X selecionados"
    3. Click "Adicionar a vaga"
    4. Modal com dropdown de vagas
    5. Confirmar adicao
    6. Toast "X candidatos adicionados a [vaga]"
    7. Se duplicados: "X ja estavam na vaga"

  Estados de Botoes:
    Adicionar:
      - Default: bg-wedo-cyan, text white
      - Hover: bg-wedo-cyan-hover
      - Loading: spinner + "Adicionando..."
      - Disabled: nenhum candidato selecionado
    Cancelar:
      - Default: bg-transparent, text --lia-text-secondary
      - Hover: bg-lia-bg-tertiary

  Mensagens de Feedback:
    - Sucesso individual: "Candidato adicionado a [Vaga Name]"
    - Sucesso massa: "X candidatos adicionados a [Vaga Name]"
    - Duplicados: "X candidatos ja estavam na vaga"
    - Erro: "Erro ao adicionar. Tente novamente."


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Adicao individual funciona
  - [ ] Adicao em massa funciona
  - [ ] Duplicados tratados corretamente
  - [ ] Toast de feedback exibe
  - [ ] Historico de adicao registrado

Criterios de Aceitacao:
  - [ ] Candidato aparece no Kanban da vaga
  - [ ] Duplicado nao cria novo registro
  - [ ] Limite de 100 em massa respeitado
  - [ ] Link no toast navega para vaga

Arquivos de Referencia (Prototipo Replit):
  - add-to-job-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/modals/add-to-job-modal.tsx
  - add-candidates-to-vacancy-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/modals/add-candidates-to-vacancy-modal.tsx
  - add-candidate-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/modals/add-candidate-modal.tsx
  - new-candidate-unified-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/modals/new-candidate-unified-modal.tsx
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/backend-proxy/candidates/bulk/assign-job/route.ts
```

---

### CARD MAP-005: Matching Score IA
**Épico:** É3 — Busca e Mapeamento

> **⚠️ DISCLAIMER — Protótipo Replit em Atualização:** O protótipo Replit deste card ainda não foi atualizado com as sugestões da reunião com o André. **As melhorias de UI serão implementadas no protótipo Replit para servir como referência visual atualizada para a implementação em Vue/Nuxt/Vuetify.** Aguarde a atualização do protótipo antes de usar os componentes como referência final de UI.

```yaml
Titulo: [AI] Matching Score entre Candidato e Vaga
Tipo: AI
Area: Backend-IA
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 8
Prioridade: Alta
Epic: EPIC-MAPPING
Status: 📋 Pendente Jira
Dependencias: MAP-002

Descricao: |
  Sistema de scoring automatico que calcula a compatibilidade
  entre candidato e vaga usando IA (Gemini/Claude).

Historia de Usuario: |
  Como recrutador, eu quero ver um score de compatibilidade
  para priorizar candidatos mais adequados a vaga.

Regras de Negocio:
  1. Score de 0 a 100 (ou 0 a 5 estrelas)
  2. Considerar skills match (peso 40%)
  3. Considerar experiencia (peso 30%)
  4. Considerar localizacao/modelo (peso 15%)
  5. Considerar pretensao salarial (peso 15%)
  6. Explicacao textual do score
  7. Recalcular ao atualizar vaga ou candidato
  8. Cache de scores por 24h

Requisitos Tecnicos:
  Backend:
    - POST /api/backend-proxy/lia/matching-score
    - MatchingScoreService class
    - Prompt engineering para analise
    - Cache Redis para scores
  AI:
    - Claude ou Gemini para analise
    - Prompt com contexto de vaga + candidato
    - Output estruturado (JSON)
  Dados:
    - matching_scores: job_id, candidate_id, score, breakdown, explanation, calculated_at

Integracoes Externas:
  Claude (Anthropic):
    - Tipo: LLM
    - Model: claude-3-haiku (rapido) ou claude-3-sonnet (preciso)
    - Secret: ANTHROPIC_API_KEY (ja configurado)
    - Custo: ~$0.001 por score (haiku)
  Gemini:
    - Tipo: LLM
    - Model: gemini-1.5-flash
    - Secret: GOOGLE_AI_API_KEY (ja configurado)
    - Custo: ~$0.0005 por score

Design & Componentes:
  Componentes Existentes:
    - Badge - score numerico
    - Progress - barra de compatibilidade
    - Tooltip - explicacao detalhada
  Novos Componentes:
    - MatchingScoreBadge - badge com score e cor
    - MatchingBreakdown - breakdown das dimensoes
    - MatchingExplanation - texto explicativo expandivel
  Design Tokens:
    Score Alto (80-100): --wedo-green (#22C55E)
    Score Medio (60-79): --electric-yellow (#EAB308)
    Score Baixo (0-59): --electric-red (#de1c31)
  Layout:
    Badge: inline-flex, rounded-full, px-3 py-1
    Breakdown: grid 2 cols, gap-2
    Explanation: text-sm, collapsible

Comportamento de UI:
  Exibicao do Score:
    - Badge colorido no card do candidato
    - Tooltip com breakdown ao hover
    - Click expande explicacao completa

  Fluxo de Calculo:
    1. Candidato adicionado a vaga
    2. Job enfileirado para calculo de score
    3. Worker processa com IA
    4. Score salvo e exibido em tempo real
    5. Recalculo automatico se vaga/candidato atualizar

  Breakdown Visual:
    Skills Match: [====------] 65%
    Experiencia: [========--] 85%
    Localizacao: [==========] 100%
    Salario:     [======----] 70%
    TOTAL:       [=======---] 78%

DoD:
  - [ ] Score calculado corretamente
  - [ ] Breakdown por dimensao disponivel
  - [ ] Explicacao textual gerada
  - [ ] Cache de 24h funciona
  - [ ] Badge colorido exibe no card

Criterios de Aceitacao:
  - [ ] Score de 0-100 exibe no card
  - [ ] Cores refletem faixa de score
  - [ ] Tooltip mostra breakdown
  - [ ] Explicacao acessivel ao expandir
  - [ ] Recalculo ao atualizar dados

Arquivos de Referencia (Prototipo Replit):
  - search-results-card.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/search-results-card.tsx
  - candidate-comparison.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/candidate-comparison.tsx
  - lia_score_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/lia_score_service.py
  - candidate_comparison_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/candidate_comparison_service.py
  - cv_scoring_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/cv_scoring_service.py
```

---

### CARD MAP-006: Sugestoes Proativas LIA
**Épico:** É3 — Busca e Mapeamento

> **⚠️ DISCLAIMER — Protótipo Replit em Atualização:** O protótipo Replit deste card ainda não foi atualizado com as sugestões da reunião com o André. **As melhorias de UI serão implementadas no protótipo Replit para servir como referência visual atualizada para a implementação em Vue/Nuxt/Vuetify.** Aguarde a atualização do protótipo antes de usar os componentes como referência final de UI.

```yaml
Titulo: [AI] Sugestoes Proativas de Candidatos
Tipo: AI
Area: Backend-IA
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 8
Prioridade: Media
Epic: EPIC-MAPPING
Status: 📋 Pendente Jira
Dependencias: MAP-002, MAP-005

Descricao: |
  LIA sugere proativamente candidatos para vagas abertas
  com base em matching automatico e comportamento do recrutador.

Historia de Usuario: |
  Como recrutador, eu quero receber sugestoes de candidatos
  para vagas que tenho abertas, sem precisar buscar manualmente.

Regras de Negocio:
  1. Analisar vagas abertas do usuario
  2. Buscar candidatos com score > 75
  3. Excluir candidatos ja na vaga
  4. Excluir candidatos rejeitados anteriormente
  5. Maximo 10 sugestoes por vaga
  6. Refresh diario das sugestoes
  7. Feedback do usuario melhora sugestoes (learn)
  8. Notificacao quando novas sugestoes disponiveis

Requisitos Tecnicos:
  Backend:
    - GET /api/backend-proxy/lia/suggestions
    - POST /api/backend-proxy/lia/suggestions/{id}/feedback
    - ProactiveSuggestionsService class
    - Job scheduler para refresh diario
  AI:
    - Reusa busca semantica + matching score
    - Filtros de exclusao aplicados
  Dados:
    - lia_suggestions: id, job_id, candidate_id, score, reason, status, feedback
    - feedback: accepted, rejected, later

Integracoes Externas:
  Reusa integracoes de MAP-002 e MAP-005

Design & Componentes:
  Componentes Existentes:
    - Card - sugestao individual
    - Button - aceitar, rejeitar, depois
    - Badge - score
    - Toast - feedback
  Novos Componentes:
    - SuggestionsPanel - painel de sugestoes
    - SuggestionCard - card com acoes
    - LIAInsightBadge - badge "Sugestao LIA"
  Design Tokens:
    Panel: bg-wedo-cyan-light (5%), border-wedo-cyan
    Badge LIA: bg-wedo-cyan, text white
    Accept: bg-wedo-green
    Reject: bg-transparent, text-electric-red
  Layout:
    Panel: sidebar ou modal
    Cards: stack vertical, gap-4
    Actions: flex gap-2, align right

Comportamento de UI:
  Notificacao de Sugestoes:
    1. Badge no menu "Sugestoes LIA (5)"
    2. Click abre painel/pagina de sugestoes
    3. Cards agrupados por vaga

  Acoes por Sugestao:
    Aceitar:
      - Adiciona candidato a vaga
      - Remove da lista de sugestoes
      - Toast "Adicionado a [vaga]"
    Rejeitar:
      - Remove da lista
      - Registra feedback negativo
      - LIA aprende a nao sugerir similar
    Depois:
      - Mantem na lista
      - Move para final

  Card de Sugestao:
    - Foto + nome + titulo
    - Score badge
    - Motivo da sugestao (1-2 linhas)
    - Botoes: Aceitar | Rejeitar | Depois

DoD:
  - [ ] Sugestoes geradas automaticamente
  - [ ] Acoes funcionam (aceitar/rejeitar/depois)
  - [ ] Feedback registrado
  - [ ] Notificacao de novas sugestoes
  - [ ] Refresh diario funciona

Criterios de Aceitacao:
  - [ ] Maximo 10 sugestoes por vaga
  - [ ] Score minimo 75 para sugerir
  - [ ] Candidatos rejeitados nao reaparecem
  - [ ] Aceitar adiciona a vaga corretamente

Arquivos de Referencia (Prototipo Replit):
  - use-lia-suggestions.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/use-lia-suggestions.ts
  - AISuggestionBadge.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/ai/AISuggestionBadge.tsx
  - proactive-actions.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/autonomous/proactive-actions.tsx
  - proactive-actions-bell.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/autonomous/proactive-actions-bell.tsx
  - proactive_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/proactive_service.py
  - proactive_alert_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/proactive_alert_service.py
```

---

### CARD MAP-007: Endpoint de Busca Paginada
**Épico:** É3 — Busca e Mapeamento

> **⚠️ DISCLAIMER — Protótipo Replit em Atualização:** O protótipo Replit deste card ainda não foi atualizado com as sugestões da reunião com o André. **As melhorias de UI serão implementadas no protótipo Replit para servir como referência visual atualizada para a implementação em Vue/Nuxt/Vuetify.** Aguarde a atualização do protótipo antes de usar os componentes como referência final de UI.

```yaml
Titulo: "[BE] Endpoint de busca paginada com limit 10"
Tipo: Backend
Area: Backend
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 5
Prioridade: Crítica
Epic: EPIC-MAPPING
Status: 📋 Pendente Jira
Dependencias: MAP-002

Descricao: |
  Refatorar endpoint de busca de candidatos para retornar apenas 10 
  resultados por página. Paginação stateless via exclude_ids.
  
  Origem: Card WDT-001 (Revisão de qualidade André)
  
  Implementação:
  - Alterar controller de busca para limitar a 10 candidatos
  - Receber parâmetro 'exclude_ids' (array de IDs já retornados)
  - Passar exclude_ids para queries de Elasticsearch e PG Vector
  - Manter paginação stateless
  - Remover seletor de quantidade do frontend

Historia de Usuario: |
  Como recrutador, eu quero receber 10 candidatos por vez na busca
  para ter resultados mais rápidos e relevantes.

Regras de Negocio:
  1. Máximo 10 candidatos por chamada de API
  2. IDs já retornados não aparecem em páginas subsequentes
  3. Paginação stateless via exclude_ids
  4. Performance < 2s por página
  5. Validação: exclude_ids max 500 elementos

Requisitos Tecnicos:
  Backend:
    - Controller de busca com limit 10
    - Parâmetros: query (string), exclude_ids (array), filters (hash)
    - Response: { candidates: [...], total_available: int, has_more: bool }
    - Multi-tenant scoping por company_id

DoD:
  - [ ] Endpoint retorna máximo 10 candidatos por chamada
  - [ ] IDs excluídos não aparecem em páginas subsequentes
  - [ ] Performance < 2s por página
  - [ ] Multi-tenant scoping validado

Criterios de Aceitacao:
  - [ ] GET retorna max 10 candidatos
  - [ ] Enviar exclude_ids filtra corretamente
  - [ ] has_more=false quando não há mais resultados
  - [ ] Performance não degrada com 500 IDs excluídos

Arquivos de Referencia (Prototipo Replit):
  - useSearchFlow.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/useSearchFlow.ts
  - candidate-search.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/api/candidate-search.ts
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - vacancy_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/vacancy_search_service.py
  - search_assistant.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/search_assistant.py
```

---

### CARD MAP-008: Componente de Paginação On-Demand
**Épico:** É3 — Busca e Mapeamento

> **⚠️ DISCLAIMER — Protótipo Replit em Atualização:** O protótipo Replit deste card ainda não foi atualizado com as sugestões da reunião com o André. **As melhorias de UI serão implementadas no protótipo Replit para servir como referência visual atualizada para a implementação em Vue/Nuxt/Vuetify.** Aguarde a atualização do protótipo antes de usar os componentes como referência final de UI.

```yaml
Titulo: "[FE] Componente de paginação on-demand"
Tipo: Frontend
Area: Frontend
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 3
Prioridade: Crítica
Epic: EPIC-MAPPING
Status: 📋 Pendente Jira
Dependencias: MAP-007

Descricao: |
  Componente de paginação para busca de candidatos com botão 
  "Carregar mais 10 candidatos".
  
  Origem: Card WDT-002 (Revisão de qualidade André)
  
  Implementação:
  - Botão 'Carregar mais 10 candidatos' ao final da lista
  - Acumular IDs retornados no state
  - Enviar exclude_ids a cada nova requisição
  - Loading state durante busca
  - Indicador de 'fim dos resultados' quando retornar < 10

Historia de Usuario: |
  Como recrutador, eu quero poder carregar mais candidatos sob demanda
  para explorar o funil de forma progressiva.

Regras de Negocio:
  1. Botão "Carregar mais 10 candidatos" visível ao final da lista
  2. Lista acumula candidatos (não substitui)
  3. Estado de loading durante busca
  4. Mensagem "Todos os candidatos relevantes foram exibidos" quando não há mais
  5. IDs acumulados enviados como exclude_ids

DoD:
  - [ ] Botão "Carregar mais" funcional
  - [ ] Lista acumula candidatos corretamente
  - [ ] Loading state visível durante busca
  - [ ] Mensagem quando não há mais resultados

Criterios de Aceitacao:
  - [ ] Clicar "Carregar mais" adiciona 10 candidatos à lista
  - [ ] IDs acumulados corretamente em exclude_ids
  - [ ] Loading spinner durante requisição
  - [ ] Botão desaparece quando has_more=false

Arquivos de Referencia (Prototipo Replit):
  - search-results-card.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/search-results-card.tsx
  - CandidatesTable.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/candidates/CandidatesTable.tsx
  - useSearchFlow.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/useSearchFlow.ts
  - use-talent-funnel.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/use-talent-funnel.ts
```

---

### CARD MAP-009: Adaptar Elasticsearch Query para Exclusão de IDs
**Épico:** É3 — Busca e Mapeamento

> **⚠️ DISCLAIMER — Protótipo Replit em Atualização:** O protótipo Replit deste card ainda não foi atualizado com as sugestões da reunião com o André. **As melhorias de UI serão implementadas no protótipo Replit para servir como referência visual atualizada para a implementação em Vue/Nuxt/Vuetify.** Aguarde a atualização do protótipo antes de usar os componentes como referência final de UI.

```yaml
Titulo: "[BE] Adaptar Elasticsearch query para exclusão de IDs"
Tipo: Backend
Area: Backend
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 3
Prioridade: Crítica
Epic: EPIC-MAPPING
Status: 📋 Pendente Jira
Dependencias: MAP-007

Descricao: |
  Modificar query builder do Elasticsearch para suportar exclusão 
  de IDs já retornados via must_not.
  
  Origem: Card WDT-003 (Revisão de qualidade André)
  
  Implementação:
  - Adicionar cláusula 'must_not' com 'ids' filter no bool query
  - Validar que exclusão não afeta scoring dos demais candidatos
  - Manter performance com listas de até 500 IDs excluídos

Historia de Usuario: |
  Como sistema de busca, eu preciso excluir candidatos já retornados
  das queries Elasticsearch para evitar duplicatas na paginação.

Regras de Negocio:
  1. must_not com ids filter no bool query
  2. Exclusão não deve afetar scoring dos demais
  3. Performance < 2s com até 500 IDs excluídos
  4. Benchmark antes/depois documentado

DoD:
  - [ ] Query com exclusão retorna resultados corretos
  - [ ] Performance não degrada com até 500 IDs
  - [ ] Scores não são afetados pela exclusão

Criterios de Aceitacao:
  - [ ] Candidatos excluídos não aparecem nos resultados
  - [ ] Scores dos candidatos restantes idênticos (com e sem exclusão)
  - [ ] Performance < 2s com 500 IDs excluídos

Arquivos de Referencia (Prototipo Replit):
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - vacancy_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/vacancy_search_service.py
  - search_assistant.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/search_assistant.py
```

---

### CARD MAP-010: Adaptar PG Vector Query para Exclusão de IDs
**Épico:** É3 — Busca e Mapeamento

> **⚠️ DISCLAIMER — Protótipo Replit em Atualização:** O protótipo Replit deste card ainda não foi atualizado com as sugestões da reunião com o André. **As melhorias de UI serão implementadas no protótipo Replit para servir como referência visual atualizada para a implementação em Vue/Nuxt/Vuetify.** Aguarde a atualização do protótipo antes de usar os componentes como referência final de UI.

```yaml
Titulo: "[BE] Adaptar PG Vector query para exclusão de IDs"
Tipo: Backend
Area: Backend
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 2
Prioridade: Crítica
Epic: EPIC-MAPPING
Status: 📋 Pendente Jira
Dependencias: MAP-007

Descricao: |
  Modificar query de busca semântica no PG Vector para suportar exclusão
  de IDs já retornados.
  
  Origem: Card WDT-004 (Revisão de qualidade André)
  
  Implementação:
  - Adicionar WHERE id NOT IN (:excluded_ids) na query pgvector
  - Validar que distância de cossenos não é afetada
  - Testar com volumes crescentes de exclusão

Historia de Usuario: |
  Como sistema de busca semântica, eu preciso excluir candidatos já retornados
  das queries PG Vector para evitar duplicatas na paginação.

Regras de Negocio:
  1. WHERE id NOT IN na query pgvector
  2. Distância de cossenos não afetada pela exclusão
  3. Performance OK com 500 IDs excluídos
  4. Prepared statements para segurança

DoD:
  - [ ] Query com exclusão funcional
  - [ ] Distâncias semânticas corretas
  - [ ] Testes de regressão passando

Criterios de Aceitacao:
  - [ ] Candidatos excluídos não aparecem nos resultados
  - [ ] Distância de cossenos idêntica (com e sem exclusão)
  - [ ] Performance OK com 500 IDs excluídos

Arquivos de Referencia (Prototipo Replit):
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - embedding_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/embedding_service.py
  - search_assistant.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/search_assistant.py
```

---

### CARD MAP-011: API de Feedback Like/Dislike
**Épico:** É3 — Busca e Mapeamento

> **⚠️ DISCLAIMER — Protótipo Replit em Atualização:** O protótipo Replit deste card ainda não foi atualizado com as sugestões da reunião com o André. **As melhorias de UI serão implementadas no protótipo Replit para servir como referência visual atualizada para a implementação em Vue/Nuxt/Vuetify.** Aguarde a atualização do protótipo antes de usar os componentes como referência final de UI.

```yaml
Titulo: "[BE] API de feedback Like/Dislike para candidatos"
Tipo: Backend
Area: Backend
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 5
Prioridade: Crítica
Epic: EPIC-MAPPING
Status: 📋 Pendente Jira
Dependencias: Nenhuma

Descricao: |
  Sistema de feedback binário (like/dislike) para candidatos 
  retornados na busca. Fundamento para todo aprendizado futuro.
  
  Origem: Card WDT-006 (Revisão de qualidade André)
  André classificou como PRIORIDADE MUITO ALTA.
  
  Schema DB:
  - candidate_feedbacks: id, search_id, candidate_id, user_id,
    feedback_type (like/dislike), job_id, search_query_snapshot,
    candidate_score_snapshot, created_at

Historia de Usuario: |
  Como recrutador, eu quero poder dar like ou dislike em candidatos
  para que o sistema aprenda minhas preferências.

Regras de Negocio:
  1. Um feedback por candidato por busca por usuário
  2. Toggle: clicar novamente remove o feedback
  3. Snapshot do score e query salvos para análise futura
  4. Feedback vinculado à busca E à vaga
  5. Multi-tenant: feedback scoped por company_id

DoD:
  - [ ] Endpoints funcionais com validações
  - [ ] Um feedback por candidato por busca por usuário
  - [ ] Snapshot do score e query salvos
  - [ ] Multi-tenant scoping

Criterios de Aceitacao:
  - [ ] POST cria feedback com tipo like ou dislike
  - [ ] POST com mesmo candidato/busca/user atualiza existente
  - [ ] DELETE remove feedback
  - [ ] GET lista todos feedbacks de uma busca
  - [ ] Snapshots salvos corretamente
  - [ ] Multi-tenant scoping por company_id

Arquivos de Referencia (Prototipo Replit):
  - candidate_feedback_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/candidate_feedback_service.py
  - feedback_learning_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/feedback_learning_service.py
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/backend-proxy/search/calibration/feedback/route.ts
```

---

### CARD MAP-012: Componente Like/Dislike no Card de Candidato
**Épico:** É3 — Busca e Mapeamento

> **⚠️ DISCLAIMER — Protótipo Replit em Atualização:** O protótipo Replit deste card ainda não foi atualizado com as sugestões da reunião com o André. **As melhorias de UI serão implementadas no protótipo Replit para servir como referência visual atualizada para a implementação em Vue/Nuxt/Vuetify.** Aguarde a atualização do protótipo antes de usar os componentes como referência final de UI.

```yaml
Titulo: "[FE] Componente Like/Dislike no card de candidato"
Tipo: Frontend
Area: Frontend
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 3
Prioridade: Alta
Epic: EPIC-MAPPING
Status: 📋 Pendente Jira
Dependencias: MAP-011

Descricao: |
  Adicionar botões de like/dislike em cada card de candidato 
  na lista de resultados.
  
  Origem: Card WDT-007 (Revisão de qualidade André)
  
  Implementação:
  - Ícones de thumbs up/down no card
  - Toggle (clique novamente para remover)
  - Feedback visual imediato (optimistic update)
  - Persistir via API

Historia de Usuario: |
  Como recrutador, eu quero poder dar like ou dislike rapidamente
  em cada candidato para registrar minha avaliação inicial.

Regras de Negocio:
  1. Botões visíveis em cada card de candidato
  2. Feedback persiste ao navegar entre páginas
  3. Toggle funcional (clicar novamente remove)
  4. Loading state durante save
  5. Feedback visual imediato (optimistic update)

DoD:
  - [ ] Botões visíveis e funcionais
  - [ ] Feedback persiste ao navegar
  - [ ] Toggle funcional
  - [ ] Loading state durante save

Criterios de Aceitacao:
  - [ ] Ícones thumbs up/down visíveis em cada card
  - [ ] Like ativo (verde) persiste via API
  - [ ] Dislike ativo (vermelho) persiste via API
  - [ ] Clicar novamente no mesmo botão remove feedback
  - [ ] Estado sincronizado ao carregar mais candidatos

Arquivos de Referencia (Prototipo Replit):
  - search-results-card.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/search-results-card.tsx
  - message-feedback.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/chat/message-feedback.tsx
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/backend-proxy/search/calibration/feedback/route.ts
```

---

### CARD MAP-013: Remover Ordenação Automática por Ranking
**Épico:** É3 — Busca e Mapeamento

> **⚠️ DISCLAIMER — Protótipo Replit em Atualização:** O protótipo Replit deste card ainda não foi atualizado com as sugestões da reunião com o André. **As melhorias de UI serão implementadas no protótipo Replit para servir como referência visual atualizada para a implementação em Vue/Nuxt/Vuetify.** Aguarde a atualização do protótipo antes de usar os componentes como referência final de UI.

```yaml
Titulo: "[FE] Remover ordenação automática por ranking"
Tipo: Frontend
Area: Frontend
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 2
Prioridade: Alta
Epic: EPIC-MAPPING
Status: 📋 Pendente Jira
Dependencias: MAP-001

Descricao: |
  Remover a ordenação automática de candidatos por score na interface.
  
  Origem: Card WDT-005 (Revisão de qualidade André - movido do Épico 16 para Épico 3)
  
  Contexto: Ranking ordenado cria expectativa de que o primeiro é sempre 
  melhor, gerando questionamentos sobre viés e removendo autonomia do recrutador.
  
  Implementação:
  - Exibir candidatos na ordem retornada pela API (sem sort no front)
  - Manter scores visíveis em cada card
  - Adicionar dropdown 'Ordenar por: Score / Nome / Data'
  - Default: sem ordenação (ordem de retorno)

Historia de Usuario: |
  Como recrutador, eu quero ver candidatos relevantes sem hierarquia
  rígida de ranking para poder avaliar com autonomia e sem viés.

Regras de Negocio:
  1. Candidatos não são ordenados por score por padrão
  2. Scores continuam visíveis nos cards
  3. Dropdown de ordenação manual: Score / Nome / Data
  4. Ordenação acontece apenas no frontend (não refaz busca)

DoD:
  - [ ] Candidatos não são ordenados por score por padrão
  - [ ] Scores visíveis mas não hierarquizados
  - [ ] Opção de ordenação manual disponível

Criterios de Aceitacao:
  - [ ] Lista exibe candidatos na ordem da API por padrão
  - [ ] Dropdown de ordenação funcional
  - [ ] Score visível em cada card sem criar hierarquia

Arquivos de Referencia (Prototipo Replit):
  - search-results-card.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/search-results-card.tsx
  - useSearchFlow.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/useSearchFlow.ts
  - useUnifiedSearch.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/useUnifiedSearch.ts
```

---

### CARD MAP-014: Revisão de Qualidade de Busca com André
**Épico:** É3 — Busca e Mapeamento

```yaml
Titulo: "[PROCESSO] Revisão de Qualidade de Busca com André"
Tipo: Processo/Validação
Area: Processo/Validação
Sprint: Pós-MVP
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 3
Prioridade: Média
Epic: EPIC-MAPPING
Status: ⏸️ Pós-MVP
Dependencias: MAP-001, MAP-003

Descricao: |
  André revisa a qualidade dos resultados de busca: relevância dos candidatos
  retornados, ordenação, filtros, e documenta feedback sobre gaps de qualidade.
  Sessão prática com busca funcional (ElasticSearch + PGVector + WRF) para
  validar que o sistema retorna candidatos relevantes para diferentes perfis de vaga.

Historia de Usuario: |
  Como responsável pela qualidade de recrutamento, André quer validar
  que os resultados de busca são relevantes e bem ordenados, garantindo
  que recrutadores encontrem os melhores candidatos rapidamente.

Regras de Negocio:
  1. Pré-requisito: busca semântica funcional (MAP-001 + MAP-002)
  2. Pré-requisito: filtros avançados funcionando (MAP-003)
  3. André testa 5-10 buscas com perfis variados (tech, comercial, liderança)
  4. Avaliação por busca: relevância top-5, relevância top-10, falsos positivos
  5. Documentar gaps: candidatos esperados mas não retornados
  6. Documentar ruído: candidatos irrelevantes no top-10
  7. Feedback sobre ordenação: o melhor candidato está no topo?
  8. Resultado: documento de feedback + lista de ajustes de scoring/ranking

Requisitos Tecnicos:
  Frontend:
    - Nenhum componente novo direto
    - Busca funcional com resultados reais para André testar
    - Filtros avançados aplicáveis durante teste
  Backend:
    - Nenhuma alteração direta
    - Dados reais ou realistas seedados para buscas de teste
    - Logs de busca habilitados para análise posterior
  Dados:
    - Base de candidatos seedada com perfis variados (mínimo 100)
    - Vagas de teste com diferentes perfis e requisitos
  Validacoes:
    - Checklist de qualidade de busca (preparar antes da sessão)
    - Métricas: precision@5, precision@10, NDCG por busca

Design & Componentes:
  Componentes Existentes:
    - SmartSearchInput - campo de busca inteligente
    - SearchResultsCard - card de resultado de busca
    - AdvancedFiltersModal - filtros avançados
    - MatchingScoreBadge - badge de score
  Novos Componentes:
    - Nenhum (validação de qualidade, não de UI)
  Design Tokens:
    N/A (sem alterações visuais)
  Layout:
    N/A (sessão de validação)
  Estados:
    - Pré-validação: preparar dados e checklist
    - Em validação: André testando buscas
    - Pós-validação: feedback documentado
    - Ajustes: implementação de melhorias
  Acessibilidade:
    N/A (processo, não componente)

Comportamento de UI:
  Fluxo Principal:
    1. Preparar ambiente com base de candidatos realista (100+ perfis)
    2. Preparar checklist de qualidade com 10 buscas planejadas
    3. Agendar sessão de 1-2h com André
    4. André executa cada busca e avalia resultados
    5. Anotar por busca: top-5 relevantes? falsos positivos? faltando alguém?
    6. Testar filtros: skill, experiência, localização, senioridade
    7. Documentar feedback consolidado
    8. Criar cards de ajuste para gaps identificados

  Layout:
    N/A (processo de validação)

  Estados de Botoes:
    N/A

  Validacoes Inline:
    N/A

  Mensagens de Feedback:
    N/A

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md (Seções: 2.5 Tabelas, 2.6 Badges & Tags, 2.13 Progress Indicators)"
  Figma: "N/A (processo de validação)"
  Assets:
    - "Checklist de qualidade de busca (a ser criado antes da sessão)"
    - "Template de feedback de qualidade"
  Tokens:
    - "N/A"

DoD:
  - [ ] Sessão de revisão realizada com André (1-2h)
  - [ ] Feedback documentado por busca (mínimo 5 buscas avaliadas)
  - [ ] Gaps de qualidade identificados e registrados
  - [ ] Ajustes de scoring/ranking documentados como cards
  - [ ] Métricas de precision@5 e precision@10 calculadas

Criterios de Aceitacao:
  - [ ] André consegue buscar candidatos com busca semântica
  - [ ] Filtros avançados funcionam corretamente na sessão
  - [ ] Top-5 resultados são relevantes em pelo menos 80% das buscas
  - [ ] Falsos positivos identificados são < 20% dos resultados
  - [ ] Feedback documentado com ações claras de melhoria
  - [ ] Cards de ajuste criados para cada gap identificado

Arquivos de Referencia (Prototipo Replit):
  - search-results-card.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/search-results-card.tsx
  - smart-search-input.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/smart-search-input.tsx
  - advanced-filters-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/filters/advanced-filters-modal.tsx
  - search hooks: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/
```


---

### CARDS WDT — TALENT FUNNEL (Fase 1: Quick Wins do Épico 3)

> Estes cards WDT pertencem ao Épico 3 e são Quick Wins do sistema de Talent Funnel.


---

### CARD WDT-001: Endpoint de Busca Paginada
**Épico:** É3 — Busca e Mapeamento

```yaml
Titulo: "[BE] Endpoint de busca paginada com limit 10"
Tipo: Story
Sprint: 1
Pontos: 5
Horas: 8
Prioridade: Crítica
Epic: EPIC-3 (Busca e Mapeamento)
Fase: Fase 1 - Quick Wins
Status: 📋 Pendente Jira
Labels: quick-win, search, performance

Descricao: |
  Refatorar endpoint de busca de candidatos para retornar apenas 10 
  resultados por página.
  
  Contexto: Atualmente o usuário pode solicitar 20/50/100 candidatos, 
  gerando custo excessivo de tokens e degradando WRF.
  
  Implementação:
  - Alterar controller de busca para limitar a 10 candidatos
  - Receber parâmetro 'exclude_ids' (array de IDs já retornados)
  - Passar exclude_ids para queries de Elasticsearch e PG Vector
  - Manter offset/cursor para paginação stateless
  - Remover seletor de quantidade do frontend

Historia de Usuario: |
  Como recrutador, eu quero receber 10 candidatos por vez na busca
  para ter resultados mais rápidos e relevantes, podendo carregar
  mais candidatos conforme necessidade.

Regras de Negocio:
  1. Máximo 10 candidatos por chamada de API
  2. IDs já retornados não podem aparecer em páginas subsequentes
  3. Paginação stateless via exclude_ids
  4. Performance < 2s por página
  5. Seletor de quantidade removido do frontend

Requisitos Tecnicos:
  Backend (Rails):
    - Controller: app/controllers/api/v1/searches_controller.rb
    - Parâmetros: query (string), exclude_ids (array integer), filters (hash)
    - Response: { candidates: [...], total_available: int, has_more: bool }
    - Validação: exclude_ids max 500 elementos
    - Scoping: company_id obrigatório (multi-tenant)
  Elasticsearch:
    - Query builder: app/services/search/elasticsearch_query_builder.rb
    - Adicionar must_not com ids filter
  PG Vector:
    - Query: app/services/search/pgvector_query_service.rb
    - WHERE id NOT IN (:excluded_ids)
  Testes:
    - RSpec: spec/controllers/api/v1/searches_controller_spec.rb
    - Cenários: paginação normal, com exclusão, lista vazia, max exclusões

DoD:
  - [ ] Endpoint retorna máximo 10 candidatos por chamada
  - [ ] IDs excluídos não aparecem em páginas subsequentes
  - [ ] Performance < 2s por página
  - [ ] Testes unitários cobrindo paginação e exclusão
  - [ ] Multi-tenant scoping validado

Criterios de Aceitacao:
  - [ ] GET /api/v1/searches retorna max 10 candidatos
  - [ ] Enviar exclude_ids filtra corretamente
  - [ ] has_more=false quando não há mais resultados
  - [ ] Performance não degrada com 500 IDs excluídos
  - [ ] Testes RSpec passando

Dependencias: Nenhuma
Bloqueia: WDT-002, WDT-003, WDT-004

Arquivos de Referencia (Prototipo Replit):
  - useSearchFlow.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/useSearchFlow.ts
  - candidate-search.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/api/candidate-search.ts
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - vacancy_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/vacancy_search_service.py
  - search_assistant.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/search_assistant.py
```

###### Prompt para IA (Cursor/VSCode) — WDT-001

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x + Vue.js 3 + Vuetify 3 + Nuxt 3
- Banco: PostgreSQL + Elasticsearch 8.x + PG Vector (pgvector extension)
- Background Jobs: Sidekiq + Redis
- Mensageria: RabbitMQ (comunicação entre serviços)
- IA/Agentes: Python 3.11 + FastAPI + LangGraph + LangChain + Gemini 2.5 Flash
- Cache: Redis
- Testes: RSpec (Rails) + Vitest (Vue) + pytest (Python)
- API: RESTful com versionamento /api/v1/
- Autenticação: JWT via WorkOS SSO
- Multi-tenant: Scoping por company_id em todas as queries
- Referência visual: Protótipo React/Next.js/Tailwind no Replit (copiar COMPORTAMENTO, não código)

PADRÕES DE CÓDIGO:
- Rails: Service Objects para lógica de negócio, Concerns para compartilhamento, Serializers para API
- Vue: Composition API (<script setup>), composables para lógica reutilizável, Pinia para state
- Python: Classes com typing, async/await, Pydantic models
- Todos: TypeScript/tipagem estrita, sem any/untyped

---

TAREFA: Refatorar o endpoint de busca de candidatos para retornar máximo 10 resultados 
por página com suporte a exclusão de IDs já retornados.

OBJETIVO: Reduzir ~80% do custo de tokens limitando resultados a 10 por chamada.

IMPLEMENTAÇÃO NECESSÁRIA:

1. Controller (Rails):
   Arquivo: app/controllers/api/v1/searches_controller.rb
   - Aceitar parâmetro exclude_ids (array de integers)
   - Limitar resultados a 10 (constante RESULTS_PER_PAGE = 10)
   - Validar exclude_ids.length <= 500
   - Retornar { candidates: [...], total_available: int, has_more: bool }
   - Garantir scoping por current_user.company_id (multi-tenant)

2. Service Object para orquestração:
   Arquivo: app/services/search/paginated_search_service.rb
   
   class Search::PaginatedSearchService
     RESULTS_PER_PAGE = 10
     MAX_EXCLUDE_IDS = 500
     
     def initialize(query:, exclude_ids: [], filters: {}, company_id:)
       @query = query
       @exclude_ids = exclude_ids.first(MAX_EXCLUDE_IDS)
       @filters = filters
       @company_id = company_id
     end
     
     def call
       es_results = elasticsearch_search
       pgv_results = pgvector_search
       merged = wrf_merge(es_results, pgv_results)
       {
         candidates: merged.first(RESULTS_PER_PAGE),
         total_available: merged.size,
         has_more: merged.size > RESULTS_PER_PAGE
       }
     end
   end

3. Elasticsearch Query Builder:
   Arquivo: app/services/search/elasticsearch_query_builder.rb
   - Adicionar cláusula must_not com { ids: { values: exclude_ids } } no bool query
   - NÃO alterar scoring (exclusão não deve afetar relevância dos demais)
   - Testar com listas de 0, 10, 100, 500 IDs

4. PG Vector Query:
   Arquivo: app/services/search/pgvector_query_service.rb
   - Adicionar WHERE id NOT IN (:excluded_ids) na query de busca semântica
   - Garantir que distância de cossenos não é afetada
   - Usar prepared statements para performance

5. Testes RSpec:
   Arquivo: spec/services/search/paginated_search_service_spec.rb
   - Testar: retorna máximo 10, exclui IDs fornecidos, has_more correto,
     limita exclude_ids a 500, aplica scoping company_id, performance com 500 IDs

NÃO FAZER:
- NÃO criar paginação baseada em offset/page number (usar exclude_ids)
- NÃO permitir que o frontend escolha quantidade de resultados
- NÃO armazenar estado de paginação no server (stateless)
- NÃO alterar a lógica do WRF — apenas limitar o output
- NÃO esquecer multi-tenant scoping

REFERÊNCIA REPLIT:
O protótipo React/Next.js tem lista de candidatos com paginação.
Copiar o COMPORTAMENTO (paginação on-demand), mas implementar em Rails (backend).
```

---

### CARD WDT-002: Componente de Paginação On-Demand
**Épico:** É3 — Busca e Mapeamento

```yaml
Titulo: "[FE] Componente de paginação on-demand"
Tipo: Story
Sprint: 1
Pontos: 3
Horas: 5
Prioridade: Crítica
Epic: EPIC-3 (Busca e Mapeamento)
Fase: Fase 1 - Quick Wins
Status: 📋 Pendente Jira
Labels: quick-win, search, ux

Descricao: |
  Criar componente Vue.js de paginação para busca de candidatos.
  
  Implementação:
  - Botão 'Carregar mais 10 candidatos' ao final da lista
  - Acumular IDs retornados no state (Pinia)
  - Enviar exclude_ids a cada nova requisição
  - Loading state durante busca
  - Indicador de 'fim dos resultados' quando retornar < 10

Historia de Usuario: |
  Como recrutador, eu quero poder carregar mais candidatos sob demanda
  para explorar o funil de forma progressiva sem sobrecarga de informação.

Regras de Negocio:
  1. Botão "Carregar mais 10 candidatos" visível ao final da lista
  2. Lista acumula candidatos (não substitui)
  3. Estado de loading durante busca
  4. Mensagem "Todos os candidatos relevantes foram exibidos" quando não há mais
  5. IDs acumulados enviados como exclude_ids

Requisitos Tecnicos:
  Frontend (Vue.js 3 + Vuetify 3):
    - Componente: src/components/search/CandidateSearchResults.vue
    - Composable: src/composables/useSearchPagination.ts
    - Store (Pinia): src/stores/searchStore.ts
    - Vuetify components: v-btn, v-progress-circular, v-alert
  Integração:
    - GET /api/v1/searches?query=X&exclude_ids=[1,2,3]
  Estado:
    - searchStore.candidates: Candidate[] (acumulado)
    - searchStore.excludeIds: number[] (IDs já retornados)
    - searchStore.hasMore: boolean
    - searchStore.isLoading: boolean

DoD:
  - [ ] Botão "Carregar mais" funcional
  - [ ] Lista acumula candidatos corretamente
  - [ ] Loading state visível durante busca
  - [ ] Mensagem quando não há mais resultados
  - [ ] Testes Vitest passando

Criterios de Aceitacao:
  - [ ] Clicar "Carregar mais" adiciona 10 candidatos à lista
  - [ ] IDs acumulados corretamente em exclude_ids
  - [ ] Loading spinner durante requisição
  - [ ] Botão desaparece quando has_more=false
  - [ ] Estado preservado ao navegar e voltar

Dependencias: WDT-001
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - search-results-card.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/search-results-card.tsx
  - CandidatesTable.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/candidates/CandidatesTable.tsx
  - useSearchFlow.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/useSearchFlow.ts
  - use-talent-funnel.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/use-talent-funnel.ts
```

###### Prompt para IA (Cursor/VSCode) — WDT-002

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x + Vue.js 3 + Vuetify 3 + Nuxt 3
- Testes: Vitest (Vue)
- API: RESTful com versionamento /api/v1/
- Multi-tenant: Scoping por company_id em todas as queries

PADRÕES DE CÓDIGO:
- Vue: Composition API (<script setup>), composables para lógica reutilizável, Pinia para state
- Vuetify 3: Usar componentes nativos (v-btn, v-card, v-progress-circular, etc.)
- TypeScript estrito, sem any

---

TAREFA: Criar componente Vue.js de paginação on-demand para lista de candidatos.

OBJETIVO: O recrutador vê 10 candidatos por vez e pode carregar mais sob demanda.

IMPLEMENTAÇÃO:

1. Pinia Store:
   Arquivo: src/stores/searchStore.ts
   - Estado: candidates (Candidate[], acumulado), excludeIds (number[]),
     hasMore (boolean), isLoading (boolean), query (string), filters (object)
   - Action loadMore(): chama API com exclude_ids, acumula candidatos,
     atualiza excludeIds e hasMore
   - Action resetSearch(): limpa tudo

2. Composable:
   Arquivo: src/composables/useSearchPagination.ts
   - Exporta: candidates, hasMore, isLoading, loadMore, reset
   - Usa storeToRefs para reatividade

3. Componente Vue:
   Arquivo: src/components/search/CandidateSearchResults.vue
   - v-card para cada candidato na lista
   - v-btn "Carregar mais 10 candidatos" (variant="outlined", color="primary")
     visível quando hasMore && !isLoading
   - v-progress-circular quando isLoading
   - v-alert type="info" "Todos os candidatos relevantes foram exibidos"
     quando !hasMore && candidates.length > 0

4. Testes Vitest:
   Arquivo: src/components/search/__tests__/CandidateSearchResults.spec.ts
   - Testar botão, loading, mensagem de fim, acumulação

NÃO FAZER:
- NÃO usar paginação numérica (1, 2, 3...) — usar botão "Carregar mais"
- NÃO substituir lista ao carregar — ACUMULAR
- NÃO usar React ou Tailwind — este é projeto Vue.js + Vuetify
- NÃO armazenar estado de paginação no localStorage
```

---

### CARD WDT-003: Adaptar Elasticsearch Query para Exclusão de IDs
**Épico:** É3 — Busca e Mapeamento

```yaml
Titulo: "[BE] Adaptar Elasticsearch query para exclusão de IDs"
Tipo: Task
Sprint: 1
Pontos: 3
Horas: 5
Prioridade: Crítica
Epic: EPIC-3 (Busca e Mapeamento)
Fase: Fase 1 - Quick Wins
Status: 📋 Pendente Jira
Labels: quick-win, search

Descricao: |
  Modificar query builder do Elasticsearch para suportar exclusão 
  de IDs já retornados.
  
  Implementação:
  - Adicionar cláusula 'must_not' com 'ids' filter no bool query
  - Validar que exclusão não afeta scoring dos demais candidatos
  - Manter performance com listas de até 500 IDs excluídos
  - Benchmark antes/depois

Historia de Usuario: |
  Como sistema de busca, eu preciso excluir candidatos já retornados
  das queries Elasticsearch para evitar duplicatas na paginação.

Requisitos Tecnicos:
  Backend (Rails):
    - Service: app/services/search/elasticsearch_query_builder.rb
    - Método: build_query(query:, filters:, exclude_ids: [])
    - Adicionar: bool > must_not > [{ ids: { values: exclude_ids } }]
    - Benchmark: rake benchmark:es_exclusion
  Testes:
    - RSpec: spec/services/search/elasticsearch_query_builder_spec.rb
    - Cenários: sem exclusão, 10 IDs, 100 IDs, 500 IDs
    - Performance: medir tempo com volumes crescentes

DoD:
  - [ ] Query com exclusão retorna resultados corretos
  - [ ] Performance não degrada com até 500 IDs
  - [ ] Scores não são afetados pela exclusão
  - [ ] Benchmark documentado

Criterios de Aceitacao:
  - [ ] Candidatos excluídos não aparecem nos resultados
  - [ ] Scores dos candidatos restantes idênticos (com e sem exclusão)
  - [ ] Performance < 2s com 500 IDs excluídos
  - [ ] Testes RSpec passando

Dependencias: WDT-001
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - vacancy_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/vacancy_search_service.py
  - search_assistant.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/search_assistant.py
```

###### Prompt para IA (Cursor/VSCode) — WDT-003

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x
- Banco: PostgreSQL + Elasticsearch 8.x
- Testes: RSpec
- Gem: elasticsearch-ruby

---

TAREFA: Modificar o Elasticsearch query builder para suportar exclusão de IDs.

IMPLEMENTAÇÃO:

1. Elasticsearch Query Builder:
   Arquivo: app/services/search/elasticsearch_query_builder.rb
   
   def build_query(query:, filters: {}, exclude_ids: [], company_id:)
     bool_query = {
       must: build_must_clauses(query),
       filter: build_filter_clauses(filters, company_id)
     }
     
     if exclude_ids.present?
       bool_query[:must_not] = [
         { ids: { values: exclude_ids.map(&:to_s) } }
       ]
     end
     
     { query: { bool: bool_query }, size: 10, _source: candidate_fields }
   end

2. Pontos críticos:
   - must_not com ids filter NÃO afeta scoring dos demais (filter context)
   - Converter IDs para strings se o _id do ES é string
   - Limitar array a 500 IDs (validação no controller)

3. Benchmark rake task:
   Arquivo: lib/tasks/benchmark.rake
   - Medir tempo com 0, 10, 50, 100, 500 IDs excluídos

4. Testes RSpec:
   - Sem exclusão: retorna sem must_not
   - Com exclude_ids: adiciona must_not, não afeta scoring, aceita até 500

NÃO FAZER:
- NÃO usar must_not com term queries individuais (usar ids filter otimizado)
- NÃO colocar exclusão no must context (afetaria scoring)
- NÃO permitir arrays > 500 sem validação
```

---

### CARD WDT-004: Adaptar PG Vector Query para Exclusão de IDs
**Épico:** É3 — Busca e Mapeamento

```yaml
Titulo: "[BE] Adaptar PG Vector query para exclusão de IDs"
Tipo: Task
Sprint: 1
Pontos: 2
Horas: 4
Prioridade: Crítica
Epic: EPIC-3 (Busca e Mapeamento)
Fase: Fase 1 - Quick Wins
Status: 📋 Pendente Jira
Labels: quick-win, search

Descricao: |
  Modificar query de busca semântica no PG Vector para suportar exclusão.
  
  Implementação:
  - Adicionar WHERE id NOT IN (:excluded_ids) na query pgvector
  - Validar que distância de cossenos não é afetada
  - Testar com volumes crescentes de exclusão

Historia de Usuario: |
  Como sistema de busca semântica, eu preciso excluir candidatos já retornados
  das queries PG Vector para evitar duplicatas na paginação.

Requisitos Tecnicos:
  Backend (Rails):
    - Service: app/services/search/pgvector_query_service.rb
    - Query: SELECT *, embedding <=> :query_vector AS distance
             FROM candidate_embeddings
             WHERE company_id = :company_id
             AND id NOT IN (:excluded_ids)
             ORDER BY distance ASC LIMIT 10
    - Usar prepared statements / parameterized queries
  Testes:
    - RSpec: spec/services/search/pgvector_query_service_spec.rb

DoD:
  - [ ] Query com exclusão funcional
  - [ ] Distâncias semânticas corretas
  - [ ] Testes de regressão passando

Criterios de Aceitacao:
  - [ ] Candidatos excluídos não aparecem nos resultados
  - [ ] Distância de cossenos idêntica (com e sem exclusão)
  - [ ] Performance OK com 500 IDs excluídos
  - [ ] Testes RSpec passando

Dependencias: WDT-001
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - embedding_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/embedding_service.py
  - search_assistant.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/search_assistant.py
```

###### Prompt para IA (Cursor/VSCode) — WDT-004

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x
- Banco: PostgreSQL + PG Vector (pgvector extension)
- Testes: RSpec
- Gem: neighbor (pgvector)

---

TAREFA: Modificar a query PG Vector para suportar exclusão de IDs já retornados.

IMPLEMENTAÇÃO:

1. PG Vector Query Service:
   Arquivo: app/services/search/pgvector_query_service.rb
   
   Opção 1 - SQL direto:
   sql = "SELECT c.*, ce.embedding <=> $1 AS distance
          FROM candidate_embeddings ce
          JOIN candidates c ON c.id = ce.candidate_id
          WHERE ce.company_id = $2
          AND ce.candidate_id NOT IN (#{exclude_ids.join(',')})
          ORDER BY distance ASC LIMIT $3"
   
   Opção 2 - ActiveRecord com neighbor gem (PREFERÍVEL):
   scope = CandidateEmbedding
     .where(company_id: company_id)
     .nearest_neighbors(:embedding, query_embedding, distance: :cosine)
     .limit(limit)
   scope = scope.where.not(candidate_id: exclude_ids) if exclude_ids.present?
   scope.includes(:candidate)

2. Validações:
   - Distância de cossenos NÃO é afetada por exclusão (verificar com testes)
   - NOT IN com arrays grandes pode ser lento — considerar NOT EXISTS se > 500
   - Usar parameterized queries (NÃO string interpolation)

NÃO FAZER:
- NÃO usar string interpolation na query (SQL injection)
- NÃO alterar a função de distância
- NÃO permitir arrays > 500 sem validação no controller
```

---

### CARD WDT-006: API de Feedback Like/Dislike
**Épico:** É3 — Busca e Mapeamento

```yaml
Titulo: "[BE] API de feedback Like/Dislike para candidatos"
Tipo: Story
Sprint: 1
Pontos: 5
Horas: 8
Prioridade: Crítica
Epic: EPIC-3 (Busca e Mapeamento)
Fase: Fase 1 - Quick Wins
Status: 📋 Pendente Jira
Labels: quick-win, feedback, learning

Descricao: |
  Criar sistema de feedback binário (like/dislike) para candidatos 
  retornados na busca.
  
  Contexto: Fundamento para todo aprendizado futuro do sistema. 
  André classificou como PRIORIDADE MUITO ALTA.
  
  Schema DB:
  - candidate_feedbacks: id, search_id, candidate_id, user_id, 
    feedback_type (like/dislike), job_id, search_query_snapshot, 
    candidate_score_snapshot, created_at
  
  Endpoints:
  - POST /api/v1/searches/:search_id/candidates/:id/feedback
  - GET /api/v1/searches/:search_id/feedbacks (listagem)
  - DELETE /api/v1/searches/:search_id/candidates/:id/feedback (remover)

Historia de Usuario: |
  Como recrutador, eu quero poder dar like ou dislike em candidatos
  retornados na busca para que o sistema aprenda minhas preferências
  e melhore os resultados futuros.

Regras de Negocio:
  1. Um feedback por candidato por busca por usuário
  2. Toggle: clicar novamente remove o feedback
  3. Snapshot do score e query salvos para análise futura
  4. Feedback vinculado à busca E à vaga
  5. Multi-tenant: feedback scoped por company_id

Requisitos Tecnicos:
  Backend (Rails):
    - Model: app/models/candidate_feedback.rb
    - Controller: app/controllers/api/v1/candidate_feedbacks_controller.rb
    - Migration: db/migrate/xxx_create_candidate_feedbacks.rb
    - Serializer: app/serializers/candidate_feedback_serializer.rb
    - Validações: uniqueness [search_id, candidate_id, user_id]
  Schema:
    - candidate_feedbacks:
      - id (bigint PK)
      - search_id (bigint FK)
      - candidate_id (bigint FK)
      - user_id (bigint FK)
      - job_id (bigint FK)
      - company_id (bigint FK)
      - feedback_type (enum: like/dislike)
      - search_query_snapshot (jsonb)
      - candidate_score_snapshot (jsonb)
      - created_at, updated_at
    - Índices: [search_id, candidate_id, user_id] unique, [company_id], [job_id]

DoD:
  - [ ] Migration criada e executada
  - [ ] Endpoints funcionais com validações
  - [ ] Um feedback por candidato por busca por usuário
  - [ ] Snapshot do score e query salvos
  - [ ] Testes de integração

Criterios de Aceitacao:
  - [ ] POST cria feedback com tipo like ou dislike
  - [ ] POST com mesmo candidato/busca/user atualiza existente
  - [ ] DELETE remove feedback
  - [ ] GET lista todos feedbacks de uma busca
  - [ ] Snapshots salvos corretamente em JSONB
  - [ ] Validação de unicidade funcional
  - [ ] Multi-tenant scoping por company_id

Dependencias: Nenhuma
Bloqueia: WDT-007, WDT-008, WDT-027, WDT-028

Arquivos de Referencia (Prototipo Replit):
  - candidate_feedback_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/candidate_feedback_service.py
  - feedback_learning_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/feedback_learning_service.py
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/backend-proxy/search/calibration/feedback/route.ts
```

###### Prompt para IA (Cursor/VSCode) — WDT-006

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x
- Banco: PostgreSQL
- Testes: RSpec
- API: RESTful /api/v1/
- Multi-tenant: Scoping por company_id

---

TAREFA: Criar sistema de feedback binário (like/dislike) para candidatos.
Este é o FUNDAMENTO para todo aprendizado futuro do sistema.

IMPLEMENTAÇÃO:

1. Migration:
   class CreateCandidateFeedbacks < ActiveRecord::Migration[7.1]
     def change
       create_table :candidate_feedbacks do |t|
         t.references :search, null: false, foreign_key: true
         t.references :candidate, null: false, foreign_key: true
         t.references :user, null: false, foreign_key: true
         t.references :job, null: false, foreign_key: true
         t.references :company, null: false, foreign_key: true
         t.integer :feedback_type, null: false
         t.jsonb :search_query_snapshot, default: {}
         t.jsonb :candidate_score_snapshot, default: {}
         t.timestamps
       end
       add_index :candidate_feedbacks,
         [:search_id, :candidate_id, :user_id],
         unique: true, name: 'idx_feedback_unique_per_search'
     end
   end

2. Model:
   class CandidateFeedback < ApplicationRecord
     belongs_to :search
     belongs_to :candidate
     belongs_to :user
     belongs_to :job
     belongs_to :company
     enum feedback_type: { like: 0, dislike: 1 }
     validates :feedback_type, presence: true
     validates :candidate_id, uniqueness: {
       scope: [:search_id, :user_id],
       message: "já possui feedback nesta busca"
     }
     before_create :capture_snapshots
     scope :for_company, ->(company_id) { where(company_id: company_id) }
     scope :likes, -> { where(feedback_type: :like) }
     scope :dislikes, -> { where(feedback_type: :dislike) }
   end

3. Controller:
   module Api::V1
     class CandidateFeedbacksController < BaseController
       before_action :set_search
       def create
         feedback = @search.candidate_feedbacks.find_or_initialize_by(
           candidate_id: params[:candidate_id], user_id: current_user.id
         )
         feedback.assign_attributes(feedback_params)
         feedback.company_id = current_user.company_id
         feedback.job_id = @search.job_id
         if feedback.save
           render json: CandidateFeedbackSerializer.new(feedback), status: :ok
         else
           render json: { errors: feedback.errors.full_messages }, status: :unprocessable_entity
         end
       end
       def index
         feedbacks = @search.candidate_feedbacks.where(company_id: current_user.company_id)
         render json: CandidateFeedbackSerializer.new(feedbacks)
       end
       def destroy
         feedback = @search.candidate_feedbacks.find_by!(
           candidate_id: params[:candidate_id], user_id: current_user.id
         )
         feedback.destroy!
         head :no_content
       end
     end
   end

4. Routes:
   namespace :api do
     namespace :v1 do
       resources :searches do
         resources :candidate_feedbacks, only: [:create, :index, :destroy],
           path: 'candidates/:candidate_id/feedback'
       end
     end
   end

5. Testes RSpec:
   Testar: criação, unicidade, toggle, snapshots, multi-tenant scoping, listagem, remoção.

IMPORTÂNCIA: Os snapshots de query e score são essenciais para análise retroativa
no motor de aprendizado futuro (WDT-027, WDT-028).

NÃO FAZER:
- NÃO permitir feedback sem search_id
- NÃO esquecer os snapshots (dados históricos irrecuperáveis)
- NÃO expor feedbacks entre companies (multi-tenant)
```

---

### CARD WDT-007: Componente Like/Dislike no Card de Candidato
**Épico:** É3 — Busca e Mapeamento

```yaml
Titulo: "[FE] Componente Like/Dislike no card de candidato"
Tipo: Story
Sprint: 1
Pontos: 3
Horas: 5
Prioridade: Alta
Epic: EPIC-3 (Busca e Mapeamento)
Fase: Fase 1 - Quick Wins
Status: 📋 Pendente Jira
Labels: quick-win, feedback, ux

Descricao: |
  Adicionar botões de like/dislike em cada card de candidato 
  na lista de resultados.
  
  Implementação:
  - Ícones de thumbs up/down no card
  - Toggle (clique novamente para remover)
  - Feedback visual imediato (cor/destaque)
  - Persistir via API
  - Estado sincronizado entre páginas

Historia de Usuario: |
  Como recrutador, eu quero poder dar like ou dislike rapidamente
  em cada candidato para registrar minha avaliação inicial
  e ajudar o sistema a aprender.

Regras de Negocio:
  1. Botões visíveis em cada card de candidato
  2. Feedback persiste ao navegar entre páginas
  3. Toggle funcional (clicar novamente remove)
  4. Loading state durante save
  5. Feedback visual imediato (optimistic update)

Requisitos Tecnicos:
  Frontend (Vue.js 3 + Vuetify 3):
    - Componente: src/components/search/CandidateFeedbackButtons.vue
    - Composable: src/composables/useCandidateFeedback.ts
    - API: src/api/feedbackApi.ts
    - Vuetify: v-btn com v-icon (mdi-thumb-up, mdi-thumb-down)
    - Cores: like = success (green), dislike = error (red), inativo = grey
  Integração:
    - POST /api/v1/searches/:search_id/candidates/:id/feedback
    - DELETE /api/v1/searches/:search_id/candidates/:id/feedback

DoD:
  - [ ] Botões visíveis e funcionais
  - [ ] Feedback persiste ao navegar
  - [ ] Toggle funcional
  - [ ] Loading state durante save
  - [ ] Testes Vitest passando

Criterios de Aceitacao:
  - [ ] Ícones thumbs up/down visíveis em cada card
  - [ ] Clicar em like ativa (verde) e persiste via API
  - [ ] Clicar em dislike ativa (vermelho) e persiste via API
  - [ ] Clicar novamente no mesmo botão remove feedback
  - [ ] Estado sincronizado ao carregar mais candidatos

Dependencias: WDT-006
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - search-results-card.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/search-results-card.tsx
  - message-feedback.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/chat/message-feedback.tsx
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/backend-proxy/search/calibration/feedback/route.ts
```

###### Prompt para IA (Cursor/VSCode) — WDT-007

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Vue.js 3 + Vuetify 3 + Nuxt 3
- Testes: Vitest
- API: RESTful /api/v1/

---

TAREFA: Criar componente Vue.js de Like/Dislike para o card de candidato.

IMPLEMENTAÇÃO:

1. API Service:
   Arquivo: src/api/feedbackApi.ts
   - create(searchId, candidateId, { feedback_type: 'like' | 'dislike' })
   - remove(searchId, candidateId)
   - list(searchId)

2. Composable:
   Arquivo: src/composables/useCandidateFeedback.ts
   - Exporta: currentFeedback (ref), isLoading (ref), toggleFeedback (fn)
   - toggleFeedback('like'|'dislike'): se já ativo, remove; se diferente, atualiza

3. Componente Vue:
   Arquivo: src/components/search/CandidateFeedbackButtons.vue
   - v-btn icon size="small" para like (mdi-thumb-up)
     color="success" quando ativo, "grey" quando inativo
     variant="flat" quando ativo, "text" quando inativo
   - v-btn icon size="small" para dislike (mdi-thumb-down)
     color="error" quando ativo, "grey" quando inativo
   - Props: searchId (number), candidateId (number), initialFeedback (string|null)

4. Testes Vitest:
   - Testar toggle, loading, estado visual, persistência

DESIGN:
- Usar ícones Material Design (mdi-thumb-up, mdi-thumb-down) do Vuetify
- Like ativo: variant="flat" color="success"
- Dislike ativo: variant="flat" color="error"
- Inativo: variant="text" color="grey"
- Optimistic update: mudar cor imediatamente, reverter se API falhar

NÃO FAZER:
- NÃO usar React ou Tailwind
- NÃO usar ícones de terceiros (usar mdi do Vuetify)
- NÃO implementar campo de comentário (será card futuro)
```

---

### CARD WDT-005: Remover Ordenação Automática por Ranking
**Épico:** É3 — Busca e Mapeamento

```yaml
Titulo: "[FE] Remover ordenação automática por ranking"
Tipo: Story
Sprint: 2
Pontos: 2
Horas: 3
Prioridade: Alta
Epic: EPIC-3 (Busca e Mapeamento) — movido do Épico 16
Fase: Fase 1 - Quick Wins
Status: 📋 Pendente Jira
Labels: quick-win, ux, ethics

Descricao: |
  Remover a ordenação automática de candidatos por score na interface.
  
  Contexto: Ranking ordenado cria expectativa de que o primeiro é sempre 
  melhor, gerando questionamentos sobre viés comercial (candidatos pagantes) 
  e removendo autonomia do recrutador.
  
  Implementação:
  - Exibir candidatos na ordem retornada pela API (sem sort no front)
  - Manter scores visíveis em cada card de candidato
  - Adicionar botão/dropdown 'Ordenar por: Score / Nome / Data'
  - Default: sem ordenação (ordem de retorno)

Historia de Usuario: |
  Como recrutador, eu quero ver candidatos relevantes sem hierarquia
  rígida de ranking para poder avaliar com autonomia e sem viés.

Requisitos Tecnicos:
  Frontend (Vue.js 3 + Vuetify 3):
    - Componente: src/components/search/SearchSortDropdown.vue
    - Vuetify: v-select com opções de ordenação
    - Opções: "Relevância (padrão)" | "Score (maior)" | "Nome A-Z" | "Data"
    - Default: ordem de retorno da API
    - Tooltip: "Candidatos relevantes para sua busca"
  Dados:
    - Scores continuam visíveis nos cards (badge ou chip)
    - Ordenação acontece apenas no frontend (não refaz busca)

DoD:
  - [ ] Candidatos não são ordenados por score por padrão
  - [ ] Scores visíveis mas não hierarquizados
  - [ ] Opção de ordenação manual disponível
  - [ ] Tooltip informativo

Criterios de Aceitacao:
  - [ ] Lista exibe candidatos na ordem da API por padrão
  - [ ] Dropdown de ordenação funcional
  - [ ] Tooltip explica que são "candidatos relevantes"
  - [ ] Score visível em cada card sem criar hierarquia

Dependencias: Nenhuma
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - search-results-card.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/search-results-card.tsx
  - useSearchFlow.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/useSearchFlow.ts
  - useUnifiedSearch.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/useUnifiedSearch.ts
```

###### Prompt para IA (Cursor/VSCode) — WDT-005

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Vue.js 3 + Vuetify 3 + Nuxt 3
- Testes: Vitest

---

TAREFA: Remover ordenação automática por score e adicionar dropdown de ordenação manual.

OBJETIVO: Evitar viés comercial e devolver autonomia ao recrutador.

IMPLEMENTAÇÃO:

1. Componente SearchSortDropdown.vue:
   - v-select com items: [
       { title: 'Relevância (padrão)', value: 'default' },
       { title: 'Score (maior primeiro)', value: 'score_desc' },
       { title: 'Nome A-Z', value: 'name_asc' },
       { title: 'Data de cadastro', value: 'date_desc' }
     ]
   - Default: 'default' (ordem da API)
   - Emit 'update:sortBy' para componente pai

2. Ordenação no frontend:
   - computed sortedCandidates que aplica sort local (sem nova requisição)
   - 'default': mantém ordem da API (sem sort)
   - 'score_desc': sort por score decrescente
   - 'name_asc': sort por nome alfabético
   - 'date_desc': sort por data mais recente

3. Tooltip no header:
   - v-tooltip no título da lista: "Estes são candidatos relevantes 
     para sua busca. Use o filtro de ordenação se preferir uma ordem específica."

NÃO FAZER:
- NÃO remover scores dos cards (devem continuar visíveis)
- NÃO reordenar automaticamente por score
- NÃO chamar API ao mudar ordenação (sort é local)
```

---

---

## ÉPICO 4: GERACAO DE PERGUNTAS WSI

> **Nota (06/fev/2026):** Os cards WIZ-008 (Formulário de Edição Completa), WIZ-012 (Estágio de Perguntas WSI) e WIZ-013 (Quality Gates WSI) foram migrados do Épico 2 (Wizard Conversacional) para este épico por decisão da reunião de alinhamento. O Épico 2 inteiro foi movido para Pós-MVP, mas esses 3 cards são necessários para o fluxo de edição de vaga e geração de perguntas WSI no MVP.

---

### CARD WSI-001: Motor de Geracao de Perguntas
**Épico:** É4 — Geração de Perguntas WSI

```yaml
Titulo: [AI] Motor de Geracao de Perguntas WSI
Tipo: AI
Area: Backend-IA
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 13
Prioridade: Critica
Epic: EPIC-WSI
Status: 📋 Pendente Jira

Descricao: |
  Motor de IA que gera perguntas de triagem personalizadas
  baseadas na metodologia WSI (WeDoTalent Skill Index) usando
  os frameworks CBI, Bloom, Dreyfus e Big Five.

Historia de Usuario: |
  Como recrutador, eu quero que a LIA gere perguntas de triagem
  automaticamente para validar as competencias da vaga.

Regras de Negocio:
  1. Analisar requisitos tecnicos e comportamentais da vaga
  2. Gerar 6-10 perguntas (modelo WSI Compact/Compact+)
  3. Distribuir entre blocos: tecnico, comportamental, cultural
  4. Variar tipos: autodeclaracao, contextual, microcase, situacional
  5. Incluir rubrica de avaliacao por pergunta
  6. Permitir regeneracao individual ou total
  7. Perguntas em portugues brasileiro

Requisitos Tecnicos:
  Backend:
    - POST /api/backend-proxy/screening/questions/generate
    - QuestionGeneratorService class
    - Prompt template com metodologia WSI
    - Parser de output estruturado
  AI:
    - Claude claude-3-sonnet para qualidade
    - Fallback para Gemini gemini-1.5-pro
    - Context: requisitos da vaga + metodologia WSI
  Dados:
    - screening_questions: id, job_id, question_text, type, category, rubric, order, generated_by_ai
    - question_types: autodeclaracao, contextual, microcase, situacional
    - categories: technical, behavioral, cultural

Integracoes Externas:
  Claude (Anthropic):
    - Tipo: LLM
    - Model: claude-3-sonnet
    - Secret: ANTHROPIC_API_KEY (ja configurado)
    - Custo: ~$0.015 por geracao
  Gemini (fallback):
    - Model: gemini-1.5-pro
    - Secret: GOOGLE_AI_API_KEY (ja configurado)
    - Custo: ~$0.01 por geracao

Design & Componentes:
  N/A - Backend/AI only (frontend no WSI-003)

Comportamento de API:
  POST /api/backend-proxy/screening/questions/generate:
    Request: {
      "job_id": "uuid",
      "model": "compact",  // compact (6-8) ou compact_plus (8-10)
      "focus_areas": ["technical", "behavioral"],
      "custom_instructions": "Focar em React e lideranca"
    }
    Response: {
      "questions": [
        {
          "id": "uuid",
          "text": "De 1 a 5, como voce avalia seu dominio em React?",
          "type": "autodeclaracao",
          "category": "technical",
          "skill": "React",
          "followup": "Cite um projeto complexo que desenvolveu com React.",
          "rubric": {
            "1": "Nunca usou ou conhecimento apenas teorico",
            "2": "Usou em projetos simples com supervisao",
            "3": "Desenvolve de forma autonoma projetos medios",
            "4": "Lida com arquiteturas complexas e otimizacao",
            "5": "Referencia tecnica, define padroes e mentora"
          },
          "evaluation_criteria": ["evidencias_concretas", "nivel_bloom", "consistencia"],
          "order": 1
        }
      ],
      "metadata": {
        "model": "compact",
        "total_questions": 7,
        "distribution": {
          "technical": 4,
          "behavioral": 2,
          "cultural": 1
        }
      }
    }

DoD:
  - [ ] Perguntas geradas com base na vaga
  - [ ] Distribuicao entre blocos correta
  - [ ] Rubricas incluidas
  - [ ] Regeneracao funciona
  - [ ] Fallback entre modelos IA

Criterios de Aceitacao:
  - [ ] 6-10 perguntas geradas por vaga
  - [ ] Tipos variados (autodeclaracao, situacional, etc)
  - [ ] Rubrica 1-5 por pergunta
  - [ ] Tempo de geracao < 15s

Arquivos de Referencia (Prototipo Replit):
  - wsi_question_generator.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_question_generator.py
  - wsi_question_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_question_service.py
  - wsi_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_service.py
  - wsi_questions.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/wsi_questions.py
  - wsi.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/wsi.py
```

---

### CARD WSI-002: Blocos de Metodologia WSI
**Épico:** É4 — Geração de Perguntas WSI

```yaml
Titulo: [BACKEND] Blocos de Metodologia WSI
Tipo: Backend
Area: Backend
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 8
Prioridade: Alta
Epic: EPIC-WSI
Status: 📋 Pendente Jira
Dependencias: WSI-001

Descricao: |
  Implementar os 4 frameworks cientificos da metodologia WSI
  (CBI, Bloom, Dreyfus, Big Five) como modulos reutilizaveis.

Historia de Usuario: |
  Como sistema, eu preciso aplicar frameworks cientificos
  para garantir perguntas validas e avaliacoes consistentes.

Regras de Negocio:
  1. CBI (Competency-Based Interviewing):
     - Perguntas situacionais baseadas em comportamentos passados
     - Estrutura STAR (Situation, Task, Action, Result)
     - Peso: validacao de experiencia real
  2. Taxonomia de Bloom:
     - Niveis cognitivos: Lembrar, Compreender, Aplicar, Analisar, Criar
     - Mapear tipo de pergunta para nivel
     - Peso: profundidade da resposta
  3. Modelo Dreyfus:
     - Escala 1-5: Novice, Advanced Beginner, Competent, Proficient, Expert
     - Rubrica padrao por skill
     - Peso: maturidade tecnica
  4. Big Five (OCEAN):
     - Abertura, Conscienciosidade, Extroversao, Amabilidade, Estabilidade
     - Perguntas comportamentais mapeadas
     - Peso: fit cultural

Requisitos Tecnicos:
  Backend:
    - WSIMethodologyService class
    - CBIEvaluator module
    - BloomClassifier module
    - DreyfusScorer module
    - BigFiveAnalyzer module
    - Config por empresa (pesos customizaveis)
  Dados:
    - wsi_config: company_id, weights (jsonb), custom_rubrics (jsonb)
    - bloom_levels: enum (remember, understand, apply, analyze, create)
    - dreyfus_levels: enum (novice, advanced_beginner, competent, proficient, expert)

Design & Componentes:
  N/A - Backend only

Comportamento de API:
  Interno - usado pelo QuestionGeneratorService e ScoreCalculatorService

  Exemplo de uso:
    # Classificar nivel Bloom de uma resposta
    bloom_level = BloomClassifier.classify(response_text)
    # Resultado: "apply" (nivel 3)

    # Avaliar com Dreyfus
    dreyfus_score = DreyfusScorer.evaluate(response_text, rubric)
    # Resultado: { level: "competent", score: 3.2, confidence: 0.85 }

    # Analisar Big Five
    big_five = BigFiveAnalyzer.analyze(response_text)
    # Resultado: { O: 4.1, C: 3.8, E: 3.5, A: 4.0, N: 3.2 }

    # CBI: extrair elementos STAR
    star = CBIEvaluator.extract_star(response_text)
    # Resultado: { situation: "...", task: "...", action: "...", result: "..." }

DoD:
  - [ ] CBI extrai elementos STAR
  - [ ] Bloom classifica niveis cognitivos
  - [ ] Dreyfus pontua maturidade
  - [ ] Big Five analisa tracos
  - [ ] Pesos configuraveis por empresa

Criterios de Aceitacao:
  - [ ] Cada framework retorna output estruturado
  - [ ] Pesos padrao aplicados corretamente
  - [ ] Empresa pode customizar pesos
  - [ ] Documentacao da metodologia disponivel

Arquivos de Referencia (Prototipo Replit):
  - wsi_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_service.py
  - wsi_deterministic_scorer.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_deterministic_scorer.py
  - wsi.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/wsi.py
  - wsi_endpoints.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/wsi_endpoints.py
```

---

### CARD WSI-003: Preview de Perguntas
**Épico:** É4 — Geração de Perguntas WSI

```yaml
Titulo: [FRONTEND] Preview de Perguntas Geradas
Tipo: Frontend
Area: Frontend
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 5
Prioridade: Alta
Epic: EPIC-WSI
Status: 📋 Pendente Jira
Dependencias: WSI-001

Descricao: |
  Interface para visualizar as perguntas geradas pela LIA
  antes de aprovar, com destaque para tipo, categoria e rubrica.

Historia de Usuario: |
  Como recrutador, eu quero revisar as perguntas geradas
  para garantir que estao adequadas antes de iniciar triagem.

Regras de Negocio:
  1. Exibir lista ordenada de perguntas
  2. Mostrar tipo (chip colorido)
  3. Mostrar categoria (tecnico, comportamental, cultural)
  4. Expandir para ver rubrica completa
  5. Indicar followup question quando existir
  6. Botao para regenerar pergunta individual
  7. Preview mobile-friendly (candidato vera assim)

Requisitos Tecnicos:
  Frontend:
    - QuestionPreviewList component
    - QuestionPreviewCard component
    - RubricAccordion component
    - RegenerateButton component
  Backend:
    - GET /api/backend-proxy/jobs/{id}/screening-config
    - PATCH /api/backend-proxy/screening/questions/{id}/regenerate

Design & Componentes:
  Componentes Existentes:
    - Card - container da pergunta
    - Badge - tipo e categoria
    - Accordion - rubrica expandivel
    - Button - regenerar, aprovar
    - Skeleton - loading
  Novos Componentes:
    - QuestionPreviewCard - card de pergunta
    - RubricTable - tabela 1-5 da rubrica
    - TypeBadge - badge colorido por tipo
    - CategoryBadge - badge de categoria
    - MobilePreviewToggle - toggle para preview mobile
  Design Tokens:
    Autodeclaracao: bg-blue-100, text-blue-700
    Contextual: bg-green-100, text-green-700
    Microcase: bg-purple-100, text-purple-700
    Situacional: bg-orange-100, text-orange-700
    Technical: bg-gray-100, text-gray-700
    Behavioral: bg-pink-100, text-pink-700
    Cultural: bg-teal-100, text-teal-700
  Layout:
    Container: max-w-3xl mx-auto
    Card: lia-card, p-4, mb-4
    Rubric: grid 5 cols, text-sm
  Estados:
    - Loading (skeleton cards)
    - Populated (lista de perguntas)
    - Regenerating (spinner na pergunta)
    - Empty (nenhuma pergunta ainda)
  Acessibilidade:
    - Cards navegaveis por teclado
    - Accordion acessivel (Enter/Space)
    - ARIA labels para badges

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador acessa config de triagem da vaga
    2. Tab "Perguntas" selecionada
    3. Lista de perguntas exibe (ou skeleton)
    4. Click no card expande rubrica
    5. Click "Regenerar" atualiza pergunta individual

  Interacoes:
    Expandir Rubrica:
      - Click no card ou icone chevron
      - Accordion abre com animacao
      - Tabela 1-5 exibe
    Regenerar Pergunta:
      - Click no botao (icone refresh)
      - Spinner substitui conteudo
      - Nova pergunta aparece com highlight
    Preview Mobile:
      - Toggle mostra preview como WhatsApp
      - Layout simulado de chat

  Estados de Botoes:
    Regenerar:
      - Default: ghost, icon refresh
      - Hover: bg-lia-bg-tertiary
      - Loading: spinner
    Aprovar Todas:
      - Default: bg-wedo-cyan
      - Hover: bg-wedo-cyan-hover
      - Disabled: durante loading


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Lista de perguntas exibe corretamente
  - [ ] Rubrica expande/colapsa
  - [ ] Regenerar funciona
  - [ ] Preview mobile disponivel
  - [ ] Badges de tipo/categoria corretos

Criterios de Aceitacao:
  - [ ] Perguntas ordenadas 1-N
  - [ ] Tipos com cores distintas
  - [ ] Rubrica 1-5 legivel
  - [ ] Regenerar atualiza em tempo real

Arquivos de Referencia (Prototipo Replit):
  - WSIQuestionsStage.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/expanded-chat/stages/WSIQuestionsStage.tsx
  - WSIQualityBar.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/expanded-chat/components/WSIQualityBar.tsx
  - wsi_question_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_question_service.py
  - wsi_questions.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/wsi_questions.py
```

---

### CARD WSI-004: Edicao Manual de Perguntas ❌ REMOVIDO
**Épico:** É4 — Geração de Perguntas WSI

> ❌ **REMOVIDO** — Decisão da reunião de 06/02/2026. Edição manual direta poderia quebrar a integridade da metodologia WSI. Substituído por WSI-006 (edição via prompt conversacional com a LIA).

```yaml
Titulo: [FULL-STACK] Edicao Manual de Perguntas
Tipo: Full-Stack
Area: Full-Stack
Sprint: Removido
Pontos: 5
Prioridade: Media
Epic: EPIC-WSI
Status: ❌ Removido (Substituído por WSI-006 - confirmado 06/02/2026)
Dependencias: WSI-003

Descricao: |
  Permitir que o recrutador edite manualmente o texto
  das perguntas, followups e rubricas geradas pela IA.

Historia de Usuario: |
  Como recrutador, eu quero ajustar as perguntas geradas
  para adequar ao contexto especifico da minha vaga.

Regras de Negocio:
  1. Editar texto da pergunta
  2. Editar texto do followup
  3. Editar itens da rubrica (1-5)
  4. Alterar tipo da pergunta
  5. Alterar categoria
  6. Reordenar perguntas (drag-and-drop)
  7. Adicionar pergunta manual
  8. Excluir pergunta
  9. Historico de edicoes (audit)

Requisitos Tecnicos:
  Frontend:
    - QuestionEditModal component
    - QuestionEditForm component
    - SortableQuestionList component (dnd-kit)
    - AddQuestionButton component
  Backend:
    - PUT /api/backend-proxy/screening/questions/{id}
    - POST /api/backend-proxy/screening/questions
    - DELETE /api/backend-proxy/screening/questions/{id}
    - PATCH /api/backend-proxy/screening/questions/reorder
  Dados:
    - screening_questions: updated_at, updated_by, is_manual
    - question_history: question_id, previous_text, changed_by, changed_at

Design & Componentes:
  Componentes Existentes:
    - Modal - container de edicao
    - Input - texto da pergunta
    - Textarea - rubrica
    - Select - tipo, categoria
    - Button - salvar, cancelar, excluir
  Novos Componentes:
    - QuestionEditForm - formulario de edicao
    - RubricEditor - editor de rubrica 1-5
    - SortableQuestionItem - item arrastavel
  Design Tokens:
    Modal: bg-white, max-w-lg
    Input: border --lia-border-default
    Delete: text --electric-red
  Layout:
    Modal: centered, p-6
    Form: flex flex-col gap-4
    Rubric: 5 inputs stacked

  Acessibilidade:
    - Keyboard navigation (Tab, Enter, Space, Escape)
    - Labels e placeholders descritivos
    - ARIA-labels em elementos interativos
    - Focus visible em todos os elementos clicáveis
    - Mensagens de erro anunciadas por screen readers
    - Contraste mínimo WCAG AA (4.5:1)

Comportamento de UI:
  Fluxo de Edicao:
    1. Click no icone de edicao no card
    2. Modal abre com form preenchido
    3. Editar campos desejados
    4. Click "Salvar"
    5. Modal fecha, card atualiza

  Fluxo de Reordenacao:
    1. Click e segura no handle do card
    2. Arrasta para nova posicao
    3. Drop atualiza ordem
    4. Autosave

  Fluxo de Adicao Manual:
    1. Click "Adicionar pergunta"
    2. Modal abre com form vazio
    3. Preencher campos obrigatorios
    4. Salvar cria nova pergunta

  Fluxo de Exclusao:
    1. Click no icone de lixeira
    2. Confirmacao "Excluir pergunta?"
    3. Confirmar remove da lista

  Estados de Botoes:
    Salvar:
      - Default: bg-wedo-cyan
      - Hover: bg-wedo-cyan-hover
      - Loading: spinner
      - Disabled: form invalido
    Excluir:
      - Default: ghost, text-electric-red
      - Hover: bg-red-50
      - Confirmacao: modal

  Validacoes:
    - Texto da pergunta: obrigatorio, min 10 chars
    - Rubrica: todos os 5 niveis preenchidos
    - Tipo: obrigatorio
    - Categoria: obrigatoria


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Edicao de texto funciona
  - [ ] Edicao de rubrica funciona
  - [ ] Reordenacao funciona
  - [ ] Adicao manual funciona
  - [ ] Exclusao funciona
  - [ ] Historico registrado

Criterios de Aceitacao:
  - [ ] Texto editado salva corretamente
  - [ ] Drag-and-drop reordena lista
  - [ ] Pergunta manual adicionada com is_manual=true
  - [ ] Excluir remove da lista

Arquivos de Referencia (Prototipo Replit):
  - WSIQuestionsStage.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/expanded-chat/stages/WSIQuestionsStage.tsx
  - wsi_question_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_question_service.py
  - wsi_questions.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/wsi_questions.py
```

---

### CARD WSI-005: Aprovacao de Perguntas
**Épico:** É4 — Geração de Perguntas WSI

```yaml
Titulo: [FULL-STACK] Aprovacao de Perguntas para Triagem
Tipo: Full-Stack
Area: Full-Stack
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 5
Prioridade: Alta
Epic: EPIC-WSI
Status: 📋 Pendente Jira
Dependencias: WSI-003, WSI-004

Descricao: |
  Fluxo de aprovacao das perguntas pelo recrutador antes
  de liberar a vaga para triagem automatica pela LIA.

Historia de Usuario: |
  Como recrutador, eu quero aprovar as perguntas revisadas
  para que a LIA possa iniciar a triagem dos candidatos.

Regras de Negocio:
  1. Recrutador deve aprovar antes de iniciar triagem
  2. Minimo 5 perguntas para aprovar
  3. Maximo 12 perguntas por triagem
  4. Aprovacao registra timestamp e usuario
  5. Perguntas nao podem ser editadas apos aprovacao
  6. Opcao de "destrancar" para edicao (reseta aprovacao)
  7. Ao aprovar, vaga muda para status "pronta_para_triagem"

Requisitos Tecnicos:
  Frontend:
    - ApproveQuestionsButton component
    - ApprovalStatusBadge component
    - LockEditWarning component
  Backend:
    - POST /api/backend-proxy/jobs/{id}/screening-config/approve
    - POST /api/backend-proxy/jobs/{id}/screening-config/unlock
    - Validacao de quantidade de perguntas
  Dados:
    - job_screening_config: approved_at, approved_by, is_locked
    - vacancies: status (draft, active, ready_for_screening, screening, closed)

Design & Componentes:
  Componentes Existentes:
    - Button - aprovar, destrancar
    - Badge - status de aprovacao
    - Modal - confirmacao
    - Toast - feedback
  Novos Componentes:
    - ApproveQuestionsButton - botao com validacao
    - ApprovalStatusBadge - badge com timestamp
    - LockWarning - aviso de edicao bloqueada
  Design Tokens:
    Approved: bg-wedo-green, text white
    Pending: bg-yellow-100, text-yellow-700
    Locked: bg-gray-100, text-gray-500
  Layout:
    Button: fixed bottom ou inline
    Badge: inline-flex no header da secao

  Acessibilidade:
    - Keyboard navigation (Tab, Enter, Space, Escape)
    - Labels e placeholders descritivos
    - ARIA-labels em elementos interativos
    - Focus visible em todos os elementos clicáveis
    - Mensagens de erro anunciadas por screen readers
    - Contraste mínimo WCAG AA (4.5:1)

Comportamento de UI:
  Fluxo de Aprovacao:
    1. Recrutador revisa perguntas
    2. Click "Aprovar e Liberar Triagem"
    3. Validacao: 5-12 perguntas?
    4. Modal de confirmacao
    5. Confirmar aprova e tranca edicao
    6. Badge muda para "Aprovado"
    7. Vaga status -> "pronta_para_triagem"

  Fluxo de Destrancamento:
    1. Recrutador precisa editar
    2. Click "Destrancar para Edicao"
    3. Warning: "Triagens em andamento serao afetadas"
    4. Confirmar reseta aprovacao
    5. Edicao liberada

  Estados de Interface:
    Pendente:
      - Botao "Aprovar" habilitado
      - Edicao permitida
      - Badge amarelo "Pendente aprovacao"
    Aprovado:
      - Botao "Destrancar" (secundario)
      - Edicao bloqueada (inputs disabled)
      - Badge verde "Aprovado em [data]"
      - Overlay com cadeado nos cards

  Validacoes:
    < 5 perguntas: "Minimo 5 perguntas necessarias"
    > 12 perguntas: "Maximo 12 perguntas permitidas"

  Mensagens de Feedback:
    - Sucesso: "Perguntas aprovadas! Triagem liberada."
    - Erro validacao: "Ajuste a quantidade de perguntas."
    - Destrancamento: "Edicao liberada. Aprovacao resetada."


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Aprovacao funciona
  - [ ] Validacao de quantidade
  - [ ] Edicao bloqueada apos aprovacao
  - [ ] Destrancamento funciona
  - [ ] Status da vaga atualizado

Criterios de Aceitacao:
  - [ ] 5-12 perguntas para aprovar
  - [ ] Badge mostra status correto
  - [ ] Inputs desabilitados apos aprovacao
  - [ ] Destrancar permite edicao novamente

Arquivos de Referencia (Prototipo Replit):
  - WSIQuestionsStage.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/expanded-chat/stages/WSIQuestionsStage.tsx
  - ReviewPublishStage.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/job-wizard/stages/ReviewPublishStage.tsx
  - wsi_question_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_question_service.py
  - confidence_policy_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/confidence_policy_service.py
```

---

### CARD WSI-006: Edição de Perguntas WSI via Prompt Conversacional
**Épico:** É4 — Geração de Perguntas WSI

```yaml
Titulo: "[AI] Edição de Perguntas WSI via Prompt Conversacional"
Tipo: Feature (AI + Full-Stack)
Area: Backend-IA
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 8
Prioridade: Alta
Epic: EPIC-WSI
Status: 📋 A Criar no Jira
Dependencias: WSI-001, WSI-002, WSI-003
Substitui: WSI-004 (removido — edição manual direta quebra integridade WSI)

Descricao: |
  Em vez de editar perguntas WSI diretamente (o que quebraria a metodologia),
  o recrutador pede ajustes via chat com a LIA. Exemplo: "Não gostei da
  pergunta sobre liderança, quero algo mais voltado a gestão de conflitos".
  A LIA regenera as perguntas mantendo a integridade do WSI.
  Máximo de 5 iterações de ajuste por bloco para evitar degradação da qualidade.

Historia de Usuario: |
  Como recrutador, eu quero pedir ajustes nas perguntas geradas pela LIA
  sem quebrar a metodologia WSI, usando linguagem natural para descrever
  o que precisa mudar.

Regras de Negocio:
  1. Recrutador NÃO edita texto das perguntas diretamente
  2. Recrutador descreve o que quer mudar via chat com LIA
  3. LIA interpreta o pedido e regenera perguntas mantendo conformidade WSI
  4. Novas perguntas mantêm estrutura do bloco WSI (blocos, pesos, sequência)
  5. Preview mostra antes/depois (diff) para comparação clara
  6. Recrutador pode aceitar ou pedir nova iteração
  7. Máximo 5 iterações de ajuste por bloco
  8. Após 5 iterações: mensagem "Limite atingido. Aceite ou volte ao original."
  9. Opção de reverter para perguntas originais a qualquer momento
  10. Log de todas as iterações para auditoria

Requisitos Tecnicos:
  Frontend:
    - QuestionAdjustmentChat: chat inline focado em ajustes de perguntas
    - QuestionDiffView: antes/depois side-by-side das perguntas
    - AdjustmentCounter: indicador "Ajuste 2 de 5"
    - Botões "Aceitar alteração" / "Pedir outro ajuste" / "Reverter ao original"
    - Integrar ao WSIQuestionsStage existente
    - Loading state durante regeneração (skeleton das perguntas)
  Backend:
    - POST /api/v1/wsi/questions/adjust
    - Request: { job_id, block_id, adjustment_prompt, current_questions, iteration_count }
    - Response: { new_questions, wsi_compliance_check, iteration, diff }
    - WSIQuestionAdjuster service com validação de conformidade WSI
    - Validação pós-geração: bloco correto, número de perguntas, formato
    - Persistência de histórico de ajustes: question_adjustment_history
  Dados:
    - question_adjustment_history: id, job_id, block_id, iteration, original_questions, adjusted_questions, adjustment_prompt, wsi_compliance_passed, created_at
  Validacoes:
    - iteration_count <= 5 por bloco
    - adjustment_prompt não vazio (mínimo 10 caracteres)
    - WSI compliance check pós-geração (estrutura de bloco preservada)

Integracoes Externas:
  LLM (Gemini):
    - Tipo: AI API
    - Uso: Regeneração de perguntas WSI com ajustes solicitados pelo recrutador
    - Serviço: wsi_question_adjuster.py
    - SDK: google-generativeai
    - Secret: GEMINI_API_KEY
    - Custo: ~$0.002-0.005 por ajuste (Flash)
    - Rate Limit: 60 RPM (requests por minuto)
    - Documentacao: https://ai.google.dev/docs

Configuracao LLM:
  Modelo: Gemini 2.5 Flash (rápido para iterações)
  Temperature: 0.7
  Max Tokens: 2000
  
  Prompt Template: |
    <role>
    Você é especialista em metodologia WSI (Weighted Structured Interview) da 
    plataforma WeDo Talent. Sua tarefa é regenerar perguntas de avaliação mantendo 
    a integridade metodológica do WSI.
    </role>
    
    <context>
    Vaga: {{job_title}} (Nível: {{seniority_level}})
    Bloco WSI: {{block_name}}
    Competências avaliadas: {{block_competencies}}
    Iteração atual: {{iteration_count}} de 5
    
    Perguntas atuais:
    {{current_questions}}
    Pedido de ajuste do recrutador:
    "{{adjustment_prompt}}"
    </context>
    
    <task>
    1. Analise o pedido do recrutador e regenere as perguntas WSI atendendo ao ajuste solicitado
    2. Mantenha a conformidade metodológica WSI (estrutura de bloco, formato STAR, competências)
    3. Retorne as perguntas ajustadas com resumo das alterações e checklist de conformidade
    </task>
    
    <constraints>
    1. Manter EXATAMENTE o mesmo número de perguntas do bloco original
    2. Preservar o formato situacional/comportamental WSI (STAR method)
    3. Manter alinhamento com as competências definidas para o bloco
    4. Adequar complexidade ao nível de senioridade do cargo
    5. Não introduzir perguntas fora do escopo das competências do bloco
    6. Cada pergunta deve ter critérios de avaliação claros
    7. Perguntas devem ser abertas (evitar sim/não)
    </constraints>
    
    <output_format>
    {
      "adjusted_questions": [
        {
          "id": "q1",
          "question": "...",
          "competency": "...",
          "evaluation_criteria": ["..."],
          "difficulty": "junior|pleno|senior|lead"
        }
      ],
      "changes_summary": "Resumo das alterações realizadas",
      "wsi_compliance_check": {
        "block_structure_preserved": true,
        "question_count_match": true,
        "competencies_aligned": true,
        "format_valid": true
      }
    }
    </output_format>

Design & Componentes:
  Componentes Existentes:
    - WSIQuestionsPanel - painel de perguntas geradas
    - WSIQuestionsStage - estágio do wizard
    - ChatSidebar - sidebar de chat (reutilizar layout)
    - Button - botões de ação
    - Card - container
    - Badge - contador
  Novos Componentes:
    - QuestionAdjustmentChat - chat focado em ajustes WSI
    - QuestionDiffView - visualização antes/depois das perguntas
    - AdjustmentCounter - badge "Ajuste 2 de 5" com barra de progresso
    - RevertButton - botão para reverter ao original
  Design Tokens:
    Before (original): --lia-text-tertiary (#6B7280)
    After (ajustado): --wedo-cyan (#60BED1)
    Accepted: --wedo-green (#22C55E)
    Rejected: --electric-red (#de1c31)
    Counter: --wedo-yellow (#EAB308)
    Diff Added: --lia-bg-success-subtle (#F0FDF4)
    Diff Removed: --lia-bg-error-subtle (#FEF2F2)
  Layout:
    Container: flex row — perguntas (60%) + chat de ajuste (40%)
    DiffView: side-by-side em desktop, stacked em mobile
    Counter: badge no topo do chat (sticky)
    Botões: footer fixo do chat panel
  Estados:
    - Default: perguntas exibidas, chat colapsado
    - Editing: chat aberto, recrutador digitando pedido
    - Loading: skeleton nas perguntas enquanto LLM regenera
    - Diff: antes/depois exibido para comparação
    - Accepted: perguntas novas aplicadas, diff verde
    - Reverted: voltou ao original, toast de confirmação
    - Max Iterations: chat desabilitado, mensagem de limite
  Acessibilidade:
    - Chat com role="log" e aria-live="polite"
    - Diff view com aria-label "Comparação de perguntas"
    - Counter com aria-label "Ajuste 2 de 5"
    - Botões com aria-label descritivo
    - Keyboard navigation: Tab entre chat e diff

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador visualiza perguntas WSI geradas no WSIQuestionsStage
    2. Clica em "Ajustar perguntas" → chat de ajuste abre à direita
    3. Digita pedido: "Quero perguntas mais focadas em gestão de conflitos"
    4. Loading: skeleton nas perguntas + spinner no chat
    5. LIA retorna novas perguntas + diff view (antes/depois)
    6. Recrutador avalia: "Aceitar" ou "Pedir outro ajuste"
    7. Se aceitar: perguntas atualizadas, chat fecha, toast de sucesso
    8. Se pedir ajuste: volta ao passo 3 (iteration_count++)
    9. Se iteration_count == 5: mensagem de limite, só aceitar/reverter

  Layout:
    Desktop: Split view 60/40 (perguntas | chat)
    Tablet: Split view 50/50
    Mobile: Tab switching (perguntas ↔ chat)

  Estados de Botoes:
    Ajustar Perguntas:
      - Default: bg-transparent, border --wedo-cyan, text --wedo-cyan
      - Hover: bg-wedo-cyan/10
      - Active: chat aberto, botão vira "Fechar ajuste"
    Aceitar Alteração:
      - Default: bg-wedo-green, text white
      - Hover: bg-wedo-green/90
      - Disabled: durante loading
    Pedir Outro Ajuste:
      - Default: bg-transparent, border --lia-border-subtle
      - Hover: bg-lia-bg-secondary
      - Disabled: se iteration_count >= 5
    Reverter ao Original:
      - Default: text --electric-red, underline
      - Hover: bg-red-50
      - Confirm: dialog "Tem certeza? Todas as alterações serão perdidas."

  Validacoes Inline:
    Prompt de Ajuste:
      - Vazio: "Descreva o que você gostaria de ajustar nas perguntas"
      - Muito curto (< 10 chars): "Descreva com mais detalhes o ajuste desejado"
    Limite de Iterações:
      - Atingido: "Você atingiu o limite de 5 ajustes para este bloco. Aceite as perguntas atuais ou reverta ao original."

  Mensagens de Feedback:
    - Sucesso ajuste: "Perguntas ajustadas com sucesso! Verifique o antes/depois."
    - Sucesso aceite: "Perguntas atualizadas! ✓ Conformidade WSI validada."
    - Revertido: "Perguntas revertidas ao original."
    - Erro LLM: "Erro ao regenerar perguntas. Tente novamente."
    - Falha conformidade: "As perguntas geradas não passaram na validação WSI. Tentando novamente..."
    - Limite atingido: "Limite de 5 ajustes atingido. Aceite ou reverta."

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md (Seções: 2.3 Cards, 2.2 Inputs & Forms, 2.6 Badges & Tags, 2.13 Progress Indicators)"
  Figma: "[A ser preenchido pelo time de Design — tela de ajuste WSI]"
  Assets:
    - "Ícone de ajuste: lucide-react/Wand2"
    - "Ícone de diff: lucide-react/GitCompare"
    - "Ícone de reverter: lucide-react/RotateCcw"
  Tokens:
    - "diff-added: #F0FDF4"
    - "diff-removed: #FEF2F2"
    - "accent-primary: #60BED1"
    - "success: #22C55E"

DoD:
  - [ ] Chat de ajuste funcional e integrado ao WSIQuestionsStage
  - [ ] LLM (Gemini 2.5 Flash) regenera perguntas a partir do prompt do recrutador
  - [ ] Validação de conformidade WSI pós-geração funcional
  - [ ] Diff view (antes/depois) renderiza corretamente
  - [ ] Contador de iterações funcional (máximo 5 por bloco)
  - [ ] Botão "Reverter ao original" funciona
  - [ ] Persistência de histórico de ajustes no banco
  - [ ] Responsivo (desktop, tablet, mobile)
  - [ ] Loading states e error handling

Criterios de Aceitacao:
  - [ ] Recrutador pede ajuste em linguagem natural e recebe perguntas regeneradas
  - [ ] Perguntas regeneradas mantêm conformidade WSI (estrutura de bloco preservada)
  - [ ] Preview antes/depois (diff) funciona com highlighting de mudanças
  - [ ] Aceitação aplica novas perguntas e fecha chat com toast de sucesso
  - [ ] Rejeição permite novo pedido de ajuste (até 5x)
  - [ ] Após 5 iterações, chat desabilitado com mensagem de limite
  - [ ] Reverter ao original funciona com confirmação
  - [ ] Erro de LLM exibe mensagem amigável e permite retry

Arquivos de Referencia (Prototipo Replit):
  - WSIQuestionsStage.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/job-wizard/stages/WSIQuestionsStage.tsx
  - WSIQuestionsPanel.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/ui-actions/panels/WSIQuestionsPanel.tsx
  - wsi-components: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/wsi/
  - chat-sidebar: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/chat/
  - job-wizard hooks: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/job-wizard/hooks/
```

---

## ÉPICO 5: TRIAGEM WHATSAPP

---

### CARD TRI-001: Configuracao Twilio WhatsApp
**Épico:** É5 — Triagem WhatsApp

```yaml
Titulo: [INTEGRACAO] Configuração WhatsApp Business API (Provider Abstrato)
Tipo: Integracao
Area: Full-Stack
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 8
Prioridade: Critica
Epic: EPIC-TRIAGEM
Status: 🔗 Integracao
Dependencias: TRI-014

Descricao: |
  Configurar integração com provider de WhatsApp Business API (Twilio, Zenvia, Tudu, ou outro selecionado via TRI-014). Implementar abstração de provider para facilitar troca.

Historia de Usuario: |
  Como sistema, eu preciso enviar e receber mensagens WhatsApp
  para conduzir triagens automatizadas com candidatos.

Regras de Negocio:
  1. Usar WhatsApp Business API via Twilio
  2. Numero dedicado por empresa (ou compartilhado MVP)
  3. Templates pre-aprovados pelo Meta
  4. Sessao de 24h apos resposta do usuario
  5. Fallback para SMS se WhatsApp indisponivel
  6. Rate limiting: 1000 msg/minuto (Twilio limit)
  7. Logs de todas as mensagens
  8. Abstração de provider (interface WhatsAppProvider) para suportar múltiplos serviços

Requisitos Tecnicos:
  Backend:
    - TwilioWhatsAppService class
    - Configuracao de credenciais
    - Webhook URL para recebimento
    - Template management
  Dados:
    - whatsapp_config: company_id, twilio_sid, phone_number, webhook_secret
    - message_templates: id, name, content, status (pending, approved, rejected)

Integracoes Externas:
  Twilio:
    - Tipo: Messaging API
    - Produto: WhatsApp Business API
    - Endpoint: api.twilio.com/2010-04-01/Accounts/{sid}/Messages
    - Secrets:
      - TWILIO_ACCOUNT_SID (ja configurado)
      - TWILIO_AUTH_TOKEN (ja configurado)
      - TWILIO_PHONE_NUMBER (ja configurado)
    - Custo: ~$0.005 por mensagem (WA) + $0.01-0.02 (template)
    - Rate Limit: 1000 msg/min
    - Documentacao: https://www.twilio.com/docs/whatsapp

Design & Componentes:
  N/A - Backend only

Comportamento de API:
  Envio de Mensagem:
    POST https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json
    Body: {
      "From": "whatsapp:+14155238886",
      "To": "whatsapp:+5511999999999",
      "Body": "Ola! Aqui e a LIA da WeDoTalent..."
    }
    ou (Template):
    Body: {
      "From": "whatsapp:+14155238886",
      "To": "whatsapp:+5511999999999",
      "ContentSid": "HXXXXXXXXXXXXXXXXXXX"
    }

  Webhook de Recebimento:
    POST /api/webhooks/twilio/whatsapp
    Body (form-encoded): {
      "From": "whatsapp:+5511999999999",
      "To": "whatsapp:+14155238886",
      "Body": "Resposta do candidato",
      "MessageSid": "SMXXXXXXXX"
    }

DoD:
  - [ ] Credenciais configuradas
  - [ ] Envio de mensagem funciona
  - [ ] Webhook recebe mensagens
  - [ ] Templates registrados
  - [ ] Logs de mensagens

Criterios de Aceitacao:
  - [ ] Mensagem enviada chega no WhatsApp
  - [ ] Resposta do candidato recebida
  - [ ] Template aprovado pelo Meta
  - [ ] Rate limiting respeitado

Arquivos de Referencia (Prototipo Replit):
  - whatsapp_twilio_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_twilio_service.py
  - whatsapp_factory.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_factory.py
  - whatsapp_provider.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_provider.py
  - whatsapp.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/whatsapp.py
```

> ⚠️ **DISCLAIMER: CARD RELACIONADO AO MENU DE CONFIGURAÇÕES**
> Este card faz parte do sistema de configurações da plataforma (Settings Menu).
> Consulte também: `docs/configuracoes-admin-cards-jira.md` para cards administrativos complementares.


---

### CARD TRI-002: Envio de Mensagem Inicial
**Épico:** É5 — Triagem WhatsApp

```yaml
Titulo: [BACKEND] Envio de Mensagem Inicial de Triagem
Tipo: Backend
Area: Backend
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 5
Prioridade: Alta
Epic: EPIC-TRIAGEM
Status: 📋 Pendente Jira
Dependencias: TRI-001, GAT-001

Descricao: |
  Servico que envia a mensagem inicial de abordagem
  para candidatos aprovados no Gate 1.

Historia de Usuario: |
  Como LIA, eu preciso enviar a primeira mensagem ao candidato
  para iniciar a conversa de triagem.

Regras de Negocio:
  1. Enviar apenas para candidatos aprovados no Gate 1
  2. Usar template aprovado pelo Meta
  3. Personalizar com nome do candidato e vaga
  4. Registrar tentativa de envio
  5. Marcar candidato como "contato_iniciado"
  6. Retry automatico em caso de falha (max 3x)
  7. Horario de envio: 8h-20h (horario do candidato)

Requisitos Tecnicos:
  Backend:
    - POST /api/backend-proxy/screening/send-initial
    - InitialContactService class
    - Template rendering com variaveis
    - Job queue para processamento assincrono
    - Timezone handling
  Dados:
    - screening_sessions: id, candidate_id, job_id, status, started_at, initial_message_sid
    - status: pending, contacted, in_progress, completed, timeout, opted_out

Integracoes Externas:
  Twilio (via TRI-001)

Design & Componentes:
  N/A - Backend only

Comportamento de API:
  POST /api/backend-proxy/screening/send-initial:
    Request: {
      "candidate_ids": ["uuid1", "uuid2"],
      "job_id": "uuid",
      "template_id": "initial_contact_v1",
      "scheduled_at": null  // null = imediato
    }
    Response: {
      "queued": 2,
      "failed": 0,
      "errors": []
    }

  Template Variables:
    {{candidate_name}}: Nome do candidato
    {{job_title}}: Titulo da vaga
    {{company_name}}: Nome da empresa
    {{estimated_time}}: Tempo estimado (7 min)

  Exemplo de Mensagem:
    "Oi {{candidate_name}}! 👋

    Aqui e a LIA, assistente de recrutamento da {{company_name}}.

    Vi que voce se interessou pela vaga de {{job_title}} e gostaria
    de conhecer melhor suas experiencias.

    Posso te fazer algumas perguntas rapidas agora? Leva uns 7 minutinhos
    e no final te mostro seu score tecnico! 🚀

    Responda 'SIM' para comecarmos ou 'NAO' se preferir outro momento."

DoD:
  - [ ] Mensagem inicial enviada
  - [ ] Template renderizado corretamente
  - [ ] Candidato marcado como contatado
  - [ ] Retry em caso de falha
  - [ ] Horario de envio respeitado

Criterios de Aceitacao:
  - [ ] Mensagem chega no WhatsApp do candidato
  - [ ] Variaveis substituidas corretamente
  - [ ] Status do candidato atualizado
  - [ ] Envio fora do horario agendado para proximo dia

Arquivos de Referencia (Prototipo Replit):
  - whatsapp_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_service.py
  - whatsapp_meta_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_meta_service.py
  - communication_dispatcher.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/communication_dispatcher.py
  - whatsapp.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/whatsapp.py
```

---

### CARD TRI-003: Webhook de Recebimento
**Épico:** É5 — Triagem WhatsApp

```yaml
Titulo: [BACKEND] Webhook de Recebimento de Mensagens
Tipo: Backend
Area: Backend
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 8
Prioridade: Critica
Epic: EPIC-TRIAGEM
Status: 📋 Pendente Jira
Dependencias: TRI-001

Descricao: |
  Endpoint webhook que recebe mensagens do Twilio quando
  candidatos respondem no WhatsApp.

Historia de Usuario: |
  Como sistema, eu preciso receber as respostas dos candidatos
  para processar a conversa de triagem.

Regras de Negocio:
  1. Validar assinatura do Twilio (seguranca)
  2. Identificar candidato pelo numero
  3. Associar mensagem a sessao de triagem ativa
  4. Enfileirar para processamento pela LIA
  5. Responder com 200 OK imediatamente (SLA Twilio)
  6. Tratar mensagens de midia (audio, imagem)
  7. Logar todas as mensagens recebidas

Requisitos Tecnicos:
  Backend:
    - POST /api/webhooks/twilio/whatsapp
    - Validacao de assinatura X-Twilio-Signature
    - Lookup de candidato por telefone
    - Message queue (Redis/RabbitMQ)
    - Processamento assincrono
  Dados:
    - screening_messages: id, session_id, direction (inbound/outbound), content, media_url, received_at

Integracoes Externas:
  Twilio Webhook

Design & Componentes:
  N/A - Backend only

Comportamento de API:
  POST /api/webhooks/twilio/whatsapp:
    Headers:
      X-Twilio-Signature: sha1_hmac_signature
    Body (form-encoded):
      From: whatsapp:+5511999999999
      To: whatsapp:+14155238886
      Body: "SIM"
      MessageSid: SMXXXXXXXXXXXXXXX
      NumMedia: 0
      MediaUrl0: (se tiver midia)
    Response: 200 OK (vazio ou TwiML)

  Fluxo de Processamento:
    1. Validar assinatura Twilio
    2. Parsear body da mensagem
    3. Lookup candidato por telefone
    4. Lookup sessao ativa para candidato
    5. Salvar mensagem no banco
    6. Enfileirar para LIA processar
    7. Retornar 200 OK

  Tratamento de Erros:
    - Assinatura invalida: 403 Forbidden
    - Candidato nao encontrado: criar candidato anonimo
    - Sessao nao encontrada: criar nova sessao ou ignorar

DoD:
  - [ ] Webhook recebe mensagens
  - [ ] Assinatura validada
  - [ ] Candidato identificado
  - [ ] Mensagem salva
  - [ ] Enfileirada para processamento

Criterios de Aceitacao:
  - [ ] Resposta do candidato recebida e salva
  - [ ] Assinatura invalida rejeitada
  - [ ] Processamento assincrono funciona
  - [ ] Midia tratada corretamente

Arquivos de Referencia (Prototipo Replit):
  - whatsapp.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/whatsapp.py
  - webhooks.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/webhooks.py
  - whatsapp_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_service.py
```

---

### CARD TRI-004: Fluxo Conversacional LIA
**Épico:** É5 — Triagem WhatsApp

```yaml
Titulo: [AI] Fluxo Conversacional de Triagem
Tipo: AI
Area: Backend-IA
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 13
Prioridade: Critica
Epic: EPIC-TRIAGEM
Status: 📋 Pendente Jira
Dependencias: TRI-003, WSI-001

Descricao: |
  Agente LIA que conduz a conversa de triagem via WhatsApp,
  aplicando perguntas WSI e avaliando respostas.

Historia de Usuario: |
  Como LIA, eu preciso conduzir uma conversa natural
  para coletar respostas e avaliar o candidato.

Regras de Negocio:
  1. Personalidade: amigavel, profissional, empatica
  2. Aplicar perguntas na ordem definida
  3. Adaptar tom baseado nas respostas
  4. Fazer followup quando resposta superficial
  5. Usar emojis moderadamente
  6. Aceitar respostas em audio (transcrever)
  7. Detectar intencoes: continuar, pausar, desistir, duvida
  8. Limite de tempo por pergunta: 5 minutos
  9. Encerrar com agradecimento e proximo passos

Requisitos Tecnicos:
  Backend:
    - LIAConversationalAgent class
    - Prompt engineering com contexto
    - State machine para fluxo
    - Intent detection
    - Audio transcription (Whisper)
  AI:
    - Claude claude-3-sonnet para qualidade
    - Context: perguntas, respostas anteriores, info do candidato
  Dados:
    - screening_sessions: current_question_index, state, context (jsonb)
    - screening_responses: question_id, response_text, audio_url, evaluation, score

Integracoes Externas:
  Claude (Anthropic):
    - Model: claude-3-sonnet
    - Custo: ~$0.03 por triagem completa
  OpenAI Whisper (transcricao):
    - Model: whisper-1
    - Custo: ~$0.006 por minuto de audio

Design & Componentes:
  N/A - Backend/AI only

Comportamento de Conversa:
  Estado Inicial:
    LIA: "Oi [Nome]! Vamos comecar? 😊"
    Candidato: "SIM"
    LIA: "Otimo! Primeira pergunta: [pergunta 1]"

  Fluxo Normal:
    Candidato: [resposta]
    LIA avalia: {
      completude: "suficiente" | "insuficiente",
      clareza: 0.9,
      evidencias: ["projeto X", "resultado Y"]
    }
    Se suficiente: proxima pergunta
    Se insuficiente: followup "Pode dar um exemplo pratico?"

  Deteccao de Intencoes:
    "preciso de um tempo" → pausar (retomar em 1h)
    "nao quero continuar" → opt-out graceful
    "nao entendi" → reformular pergunta
    "quanto tempo falta" → informar progresso

  Encerramento:
    LIA: "Perfeito, [Nome]! Terminamos 🎉
    
    Seu WSI (score tecnico) ficou em X.X/5.0 - nivel [interpretacao]!
    
    Vou enviar suas respostas para o time de recrutamento
    e em breve voce recebe um retorno.
    
    Obrigada pelo seu tempo! Boa sorte! 🍀"

DoD:
  - [ ] Conversa flui naturalmente
  - [ ] Perguntas aplicadas na ordem
  - [ ] Followups quando necessario
  - [ ] Intencoes detectadas
  - [ ] Audio transcrito

Criterios de Aceitacao:
  - [ ] Triagem completa em 7-10 min
  - [ ] Tom adequado mantido
  - [ ] Respostas avaliadas
  - [ ] Encerramento com score

Arquivos de Referencia (Prototipo Replit):
  - whatsapp_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_service.py
  - conversation_manager.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/conversation_manager.py
  - conversation_memory.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/conversation_memory.py
  - pre_qualification_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/pre_qualification_service.py
```

---

### CARD TRI-005: Persistencia de Conversa
**Épico:** É5 — Triagem WhatsApp

```yaml
Titulo: [BACKEND] Persistencia de Estado da Conversa
Tipo: Backend
Area: Backend
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 5
Prioridade: Alta
Epic: EPIC-TRIAGEM
Status: 📋 Pendente Jira
Dependencias: TRI-004

Descricao: |
  Sistema de persistencia do estado da conversa para
  permitir retomada e recuperacao de falhas.

Historia de Usuario: |
  Como sistema, eu preciso manter o estado da conversa
  para continuar de onde parou em caso de interrupcao.

Regras de Negocio:
  1. Salvar estado apos cada mensagem
  2. Armazenar: pergunta atual, respostas, scores parciais
  3. Timeout de sessao: 24h de inatividade
  4. Permitir retomada pelo candidato
  5. Recuperacao automatica apos falha
  6. Historico completo para auditoria

Requisitos Tecnicos:
  Backend:
    - SessionStateManager class
    - Redis para cache de estado ativo
    - PostgreSQL para persistencia duravel
    - Checkpoint a cada interacao
  Dados:
    - screening_sessions: state (jsonb), last_activity_at, checkpoints (jsonb[])
    - State schema: {
        current_question_index: number,
        questions_answered: number,
        partial_scores: {},
        context_memory: [],
        intent_history: []
      }

Design & Componentes:
  N/A - Backend only

Comportamento de API:
  Interno - usado pelo LIAConversationalAgent

  Save State:
    await SessionStateManager.save(session_id, {
      current_question_index: 3,
      questions_answered: 2,
      partial_scores: { skill_1: 4.2, skill_2: 3.8 },
      context_memory: ["candidato mencionou lideranca", "5 anos exp"],
      last_response: "..."
    })

  Load State:
    state = await SessionStateManager.load(session_id)
    // Retoma do checkpoint

  Retomada:
    LIA: "Oi [Nome]! Vi que paramos no meio da nossa conversa.
    Quer continuar de onde paramos? Estamos na pergunta 3 de 7."

DoD:
  - [ ] Estado salvo apos cada mensagem
  - [ ] Retomada funciona
  - [ ] Timeout de 24h implementado
  - [ ] Historico completo disponivel

Criterios de Aceitacao:
  - [ ] Candidato pode retomar apos interrupcao
  - [ ] Estado recuperado corretamente
  - [ ] Sessao expira apos 24h inativa
  - [ ] Auditoria de todas as interacoes

Arquivos de Referencia (Prototipo Replit):
  - conversation_memory.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/conversation_memory.py
  - memory_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/memory_service.py
  - conversation_manager.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/conversation_manager.py
```

---

### CARD TRI-006: Tela de Monitoramento
**Épico:** É5 — Triagem WhatsApp

```yaml
Titulo: [FRONTEND] Transcrição Completa da Triagem no Card de Atividade do Candidato
Tipo: Frontend
Area: Frontend
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 8
Prioridade: Alta
Epic: EPIC-TRIAGEM
Status: 📋 Pendente Jira
Dependencias: TRI-004

Descricao: |
  Transcrição completa da triagem acessível via card de evento de triagem na tab Activities do preview do candidato. Ao clicar no card do evento de triagem, expande/abre a transcrição completa (timeline de mensagens LIA↔candidato). Também acessível via ícone no card do Kanban e na tabela de candidatos dentro da vaga. NÃO criar aba 'Conversas' separada.

Historia de Usuario: |
  Como recrutador, eu quero consultar a transcrição completa da triagem
  para revisar o histórico de conversa entre a LIA e o candidato.

Regras de Negocio:
  1. A tab Activities do preview do candidato JÁ possui cards de atividades/eventos — o evento de triagem é um desses cards
  2. Ao clicar no card do evento de triagem, exibir transcrição completa em timeline
  3. Cada mensagem mostra: remetente (LIA/candidato), timestamp, conteúdo
  4. Paginação de histórico (20 mensagens por página)
  5. Status da triagem (ativa/concluída/pausada/timeout)
  6. Filtro por vaga (se candidato tem múltiplas triagens)
  7. Indicador visual de mensagens da LIA vs candidato
  8. Ícone de acesso rápido à transcrição no card do Kanban
  9. Ícone de acesso rápido na tabela de candidatos dentro da vaga

Requisitos Tecnicos:
  Frontend:
    - ScreeningTranscriptView component (timeline de mensagens)
    - Adaptar CandidateActivityCard (expand com transcrição)
    - Ícone em CandidateCard (Kanban) e tabela de candidatos
  Backend:
    - GET /api/v1/candidates/{id}/screening-transcript?job_id={job_id} (paginado)

Design & Componentes:
  Componentes Existentes:
    - Card - container de sessao
    - Badge - status
    - Progress - barra de progresso
    - Table - lista de sessoes
    - Skeleton - loading
  Novos Componentes:
    - ScreeningSessionCard - card de sessao ativa
    - ScreeningProgress - progresso visual
    - ScreeningMetrics - cards de metricas
    - MessagePreview - preview de mensagens
    - LiveIndicator - pulso para "ao vivo"
  Design Tokens:
    Aguardando: bg-yellow-100, text-yellow-700
    Em Conversa: bg-green-100, text-green-700, pulso
    Pausado: bg-gray-100, text-gray-700
    Timeout: bg-red-100, text-red-700
    Concluido: bg-blue-100, text-blue-700
  Layout:
    Container: max-w-7xl
    Metricas: grid 4 cols no topo
    Lista: flex flex-col gap-4
  Estados:
    - Loading (skeletons)
    - Empty (nenhuma triagem ativa)
    - Populated (lista de sessoes)
    - Real-time (indicador de live)

  Acessibilidade:
    - Keyboard navigation (Tab, Enter, Space, Escape)
    - Labels e placeholders descritivos
    - ARIA-labels em elementos interativos
    - Focus visible em todos os elementos clicáveis
    - Mensagens de erro anunciadas por screen readers
    - Contraste mínimo WCAG AA (4.5:1)

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador acessa /triagens ou /vagas/{id}/triagens
    2. Metricas carregam no topo
    3. Lista de sessoes abaixo
    4. Atualizacao a cada 5s (ou real-time)

  Card de Sessao:
    - Foto + nome do candidato
    - Badge de status (com pulso se ativo)
    - Progresso: "Pergunta 3 de 7"
    - Tempo: "Ha 4 min"
    - Ultima mensagem (preview truncado)
    - Click expande detalhes

  Metricas:
    - Total de triagens: 45
    - Em andamento: 3 🟢
    - Concluidas hoje: 12
    - Taxa de conclusao: 78%

  Interacoes:
    Click em Card:
      - Expande para ver historico de mensagens
    Filtro por Vaga:
      - Dropdown com vagas ativas
    Filtro por Status:
      - Checkboxes: ativo, pausado, concluido, timeout


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Lista de triagens exibe
  - [ ] Status em tempo real
  - [ ] Metricas calculadas
  - [ ] Filtros funcionam
  - [ ] Atualizacao automatica

Criterios de Aceitacao:
  - [ ] Triagens ativas aparecem com pulso
  - [ ] Progresso atualiza em tempo real
  - [ ] Click expande mensagens
  - [ ] Filtros refinam lista

Arquivos de Referencia (Prototipo Replit):
  - data_request_whatsapp_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/data_request_whatsapp_service.py
  - data_request_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/data_request_service.py
  - whatsapp_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_service.py
  - use-data-request-config.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/use-data-request-config.ts
  - use-data-request-modals.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/use-data-request-modals.ts
```

---

### CARD TRI-007: Timeout e Retentativas
**Épico:** É5 — Triagem WhatsApp

```yaml
Titulo: [BACKEND] Timeout e Retentativas de Mensagem
Tipo: Backend
Area: Backend
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 5
Prioridade: Alta
Epic: EPIC-TRIAGEM
Status: 📋 Pendente Jira
Dependencias: TRI-004

Descricao: |
  Sistema de timeout para respostas e retentativas
  automaticas para recuperar candidatos inativos.

Historia de Usuario: |
  Como LIA, eu preciso lidar com candidatos que demoram
  para responder, reenviando lembretes ou encerrando.

Regras de Negocio:
  1. Timeout por pergunta: 5 minutos
  2. Timeout de sessao: 30 minutos sem resposta
  3. Lembrete apos 3 min: "Oi, ainda esta ai?"
  4. Lembrete apos 5 min: "Posso esperar mais um pouco..."
  5. Timeout apos 30 min: encerrar sessao
  6. Permitir retomada no dia seguinte (1x)
  7. Retry de envio em caso de falha: 3x com backoff

Requisitos Tecnicos:
  Backend:
    - TimeoutManager class
    - Scheduled jobs para verificar timeouts
    - Lembrete templates
    - Retry com exponential backoff
  Dados:
    - screening_sessions: timeout_count, last_reminder_at, retry_attempts

Design & Componentes:
  N/A - Backend only

Comportamento:
  Fluxo de Timeout:
    T+0: LIA envia pergunta
    T+3min: Sem resposta → Lembrete 1
    T+5min: Sem resposta → Lembrete 2
    T+30min: Sem resposta → Timeout
      → Status: "timeout"
      → Mensagem: "Parece que voce esta ocupado. Sem problema!
         Amanha tento contato novamente."
    T+24h: Retry automatico (1x)
      → "Oi [Nome], tudo bem? Ontem paramos no meio.
         Quer continuar? Faltam X perguntas."
    Se nao responder: Encerrar definitivamente

  Retry de Envio:
    Tentativa 1: imediato
    Tentativa 2: apos 30s
    Tentativa 3: apos 2min
    Falha total: marcar para retry manual

DoD:
  - [ ] Timeout detectado corretamente
  - [ ] Lembretes enviados
  - [ ] Sessao encerrada apos 30min
  - [ ] Retry no dia seguinte funciona
  - [ ] Retry de envio com backoff

Criterios de Aceitacao:
  - [ ] Lembrete enviado apos 3min
  - [ ] Sessao timeout apos 30min
  - [ ] Candidato pode retomar apos timeout
  - [ ] Max 1 retry automatico por sessao

Arquivos de Referencia (Prototipo Replit):
  - wsi_deterministic_scorer.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_deterministic_scorer.py
  - cv_scoring_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/cv_scoring_service.py
  - lia_score_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/lia_score_service.py
  - rubric_evaluation_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/rubric_evaluation_service.py
```

---

### CARD TRI-008: Opt-out e Consentimento
**Épico:** É5 — Triagem WhatsApp

```yaml
Titulo: [BACKEND] Opt-out e Gestao de Consentimento
Tipo: Backend
Area: Backend
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 5
Prioridade: Alta
Epic: EPIC-TRIAGEM
Status: 📋 Pendente Jira
Dependencias: TRI-002

Descricao: |
  Sistema para gerenciar opt-out de candidatos e
  consentimento para comunicacao via WhatsApp.

Historia de Usuario: |
  Como candidato, eu quero poder sair da triagem a qualquer
  momento e nao receber mais mensagens.

Regras de Negocio:
  1. Opt-out via palavras: "SAIR", "PARAR", "CANCELAR", "NAO QUERO"
  2. Confirmacao antes de encerrar definitivamente
  3. Candidato pode optar por "depois" sem opt-out
  4. Registro de consentimento inicial (primeiro contato)
  5. Blacklist de numeros que optaram out
  6. LGPD: direito de exclusao de dados
  7. Resposta automatica apos opt-out

Requisitos Tecnicos:
  Backend:
    - ConsentManager class
    - OptOutHandler class
    - Blacklist check antes de enviar
    - Audit log de consentimentos
  Dados:
    - candidate_consents: candidate_id, type (whatsapp, email), granted_at, revoked_at
    - opt_out_blacklist: phone_number, opted_out_at, reason
    - consent_types: whatsapp_contact, data_processing, marketing

Integracoes Externas:
  Nenhuma adicional

Design & Componentes:
  N/A - Backend only

Comportamento:
  Deteccao de Opt-out:
    Candidato: "PARAR" ou "nao quero mais" ou "me tire dessa lista"
    LIA detecta: intent = "opt_out"
    LIA: "Entendi, [Nome]. Voce realmente quer parar?
          Responda 'SIM PARAR' para confirmar."
    Candidato: "SIM PARAR"
    LIA: "Ok, removido. Voce nao recebera mais mensagens.
          Se mudar de ideia, entre em contato pelo site."
    → Adiciona a blacklist
    → Marca consentimento como revogado

  Verificacao antes de Enviar:
    if phone_number in blacklist:
      return "BLOCKED - opted out"
    if not consent_granted:
      return "BLOCKED - no consent"

  Consentimento Inicial:
    Primeiro contato inclui texto:
    "...Ao continuar, voce concorda com nossa Politica de Privacidade
    em [link]. Responda 'NAO' se nao deseja participar."

DoD:
  - [ ] Opt-out detectado
  - [ ] Confirmacao antes de encerrar
  - [ ] Blacklist funciona
  - [ ] Consentimento registrado
  - [ ] Audit log completo

Criterios de Aceitacao:
  - [ ] "SAIR" encerra com confirmacao
  - [ ] Numero na blacklist nao recebe msg
  - [ ] Log de consentimento auditavel
  - [ ] LGPD compliance

Arquivos de Referencia (Prototipo Replit):
  - company-screening-settings.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/company-screening-settings.tsx
  - useScreeningConfig.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/useScreeningConfig.ts
  - use-screening-questions.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/use-screening-questions.ts
```

---

### CARD TRI-009: Templates de Mensagem WhatsApp
**Épico:** É5 — Triagem WhatsApp

```yaml
Titulo: [FULL-STACK] Templates de Mensagem WhatsApp
Tipo: Full-Stack
Area: Full-Stack
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 8
Prioridade: Alta
Epic: EPIC-TRIAGEM
Status: 📋 Pendente Jira
Dependencias: TRI-001, TPL-008

Descricao: |
  Gestao de templates de mensagem WhatsApp que precisam
  ser aprovados pelo Meta antes do uso.

Historia de Usuario: |
  Como admin, eu quero gerenciar templates de mensagem
  para garantir que estao aprovados antes de usar.

Regras de Negocio:
  1. Templates devem ser aprovados pelo Meta
  2. Variaveis permitidas: {{1}}, {{2}}, etc
  3. Categorias: marketing, transactional, utility
  4. Preview antes de submeter
  5. Status: draft, pending, approved, rejected
  6. Historico de versoes
  7. Templates padrao por tipo de mensagem
  8. Templates precisam ser aprovados pelo Meta Business Manager antes de usar (ver TPL-008)

Requisitos Tecnicos:
  Frontend:
    - WhatsAppTemplateList component
    - TemplateEditor component
    - TemplatePreview component
  Backend:
    - GET /api/backend-proxy/whatsapp/templates
    - POST /api/backend-proxy/whatsapp/templates
    - PUT /api/backend-proxy/whatsapp/templates/{id}
    - POST /api/backend-proxy/whatsapp/templates/{id}/submit
  Dados:
    - whatsapp_templates: id, name, content, variables, category, status, meta_template_id

Integracoes Externas:
  Twilio Content API:
    - Endpoint: content.twilio.com/v1/Content
    - Uso: Criar e submeter templates ao Meta
    - Documentacao: https://www.twilio.com/docs/content

Design & Componentes:
  Componentes Existentes:
    - Table - lista de templates
    - Modal - editor
    - Badge - status
    - Button - acoes
  Novos Componentes:
    - TemplateEditor - editor com preview
    - VariableInput - input para variaveis
    - WhatsAppPreview - preview visual de chat
    - StatusBadge - badge com cores por status
  Design Tokens:
    Draft: bg-gray-100
    Pending: bg-yellow-100
    Approved: bg-green-100
    Rejected: bg-red-100
  Layout:
    Editor: 2 cols (form | preview)
    List: table responsiva

  Acessibilidade:
    - Keyboard navigation (Tab, Enter, Space, Escape)
    - Labels e placeholders descritivos
    - ARIA-labels em elementos interativos
    - Focus visible em todos os elementos clicáveis
    - Mensagens de erro anunciadas por screen readers
    - Contraste mínimo WCAG AA (4.5:1)

Comportamento de UI:
  Fluxo de Criacao:
    1. Click "Novo Template"
    2. Preencher nome, categoria, conteudo
    3. Adicionar variaveis {{1}}, {{2}}
    4. Preview mostra como aparece no WhatsApp
    5. Salvar como rascunho
    6. Submeter para aprovacao
    7. Aguardar aprovacao do Meta (24-48h)

  Lista de Templates:
    - Nome, categoria, status, data criacao
    - Acoes: editar (se draft), duplicar, ver historico

  Variaveis Padrao:
    {{1}} = Nome do candidato
    {{2}} = Nome da vaga
    {{3}} = Nome da empresa
    {{4}} = Link/URL


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Lista de templates exibe
  - [ ] Editor funciona
  - [ ] Preview visual correto
  - [ ] Submissao para Meta
  - [ ] Status atualizado

Criterios de Aceitacao:
  - [ ] Template criado como draft
  - [ ] Variaveis renderizam no preview
  - [ ] Submissao envia para Twilio/Meta
  - [ ] Status atualiza apos aprovacao

Arquivos de Referencia (Prototipo Replit):
  - candidate_report_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/candidate_report_service.py
  - report_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/report_service.py
  - explainability_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/explainability_service.py
```

---

### CARD TRI-010: Envio em Massa (Bulk)
**Épico:** É5 — Triagem WhatsApp

```yaml
Titulo: [FULL-STACK] Envio em Massa de Triagens
Tipo: Full-Stack
Area: Full-Stack
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 8
Prioridade: Media
Epic: EPIC-TRIAGEM
Status: 📋 Pendente Jira
Dependencias: TRI-002, GAT-001

Descricao: |
  Funcionalidade para iniciar triagens em massa para
  multiplos candidatos aprovados de uma vez.

Historia de Usuario: |
  Como recrutador, eu quero iniciar triagem para varios
  candidatos de uma vez para acelerar o processo.

Regras de Negocio:
  1. Selecionar multiplos candidatos (checkboxes)
  2. Limite de 50 candidatos por lote
  3. Validar que todos estao aprovados (Gate 1)
  4. Validar numeros de WhatsApp validos
  5. Escalonamento: 5 mensagens por minuto (evitar block)
  6. Progresso em tempo real
  7. Relatorio final: enviados, falhas, invalidos

Requisitos Tecnicos:
  Frontend:
    - BulkScreeningModal component
    - BulkProgressBar component
    - BulkResultsSummary component
  Backend:
    - POST /api/backend-proxy/screening/bulk-send
    - GET /api/backend-proxy/screening/bulk-send/{jobId}/status
    - Job queue com rate limiting
  Dados:
    - bulk_screening_jobs: id, job_id, total, sent, failed, status, started_at, completed_at

Design & Componentes:
  Componentes Existentes:
    - Modal - container
    - Checkbox - selecao
    - Progress - barra
    - Button - acoes
  Novos Componentes:
    - BulkScreeningModal - modal com lista e progresso
    - CandidateSelectionList - lista com checkboxes
    - BulkProgress - progresso com detalhes
    - BulkResults - resumo final
  Design Tokens:
    Progress: bg-wedo-cyan
    Success: --wedo-green
    Failed: --electric-red
    Skipped: --gray-400
  Layout:
    Modal: max-w-2xl
    List: max-h-64 overflow-y-auto
    Progress: sticky bottom

  Acessibilidade:
    - Keyboard navigation (Tab, Enter, Space, Escape)
    - Labels e placeholders descritivos
    - ARIA-labels em elementos interativos
    - Focus visible em todos os elementos clicáveis
    - Mensagens de erro anunciadas por screen readers
    - Contraste mínimo WCAG AA (4.5:1)

Comportamento de UI:
  Fluxo de Envio em Massa:
    1. Recrutador seleciona candidatos no Kanban/Tabela
    2. Click "Iniciar Triagem"
    3. Modal mostra lista selecionada
    4. Validacao: Gate 1 aprovado? WhatsApp valido?
    5. Candidatos invalidos marcados com warning
    6. Click "Enviar para X candidatos"
    7. Barra de progresso atualiza em tempo real
    8. Ao finalizar: resumo com sucesso/falha

  Progresso em Tempo Real:
    [====================] 35/50 enviados
    ✓ 33 enviados com sucesso
    ✗ 2 falhas (numero invalido)
    ⏳ 15 aguardando

  Resumo Final:
    ┌─────────────────────────────┐
    │ Envio Concluido             │
    ├─────────────────────────────┤
    │ ✓ Enviados: 48              │
    │ ✗ Falhas: 2                 │
    │   - +55119... (invalido)    │
    │   - +55119... (opt-out)     │
    ├─────────────────────────────┤
    │ [Ver Detalhes] [Fechar]     │
    └─────────────────────────────┘


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Selecao multipla funciona
  - [ ] Validacao de candidatos
  - [ ] Envio escalonado (rate limit)
  - [ ] Progresso em tempo real
  - [ ] Resumo final exibe

Criterios de Aceitacao:
  - [ ] Maximo 50 por lote
  - [ ] 5 msg/min rate limit
  - [ ] Candidatos invalidos listados
  - [ ] Falhas registradas com motivo

Arquivos de Referencia (Prototipo Replit):
  - wsi_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_service.py
  - wsi_deterministic_scorer.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_deterministic_scorer.py
  - cv_scoring_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/cv_scoring_service.py
```

---

### CARD TRI-011: Pré-Qualificação Automatizada
**Épico:** É5 — Triagem WhatsApp

```yaml
Titulo: [BACKEND] Pré-Qualificação Automatizada de Candidatos
Tipo: Backend
Area: Backend
Sprint: Pós-MVP
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 8
Prioridade: Alta
Epic: EPIC-TRIAGEM
Status: ⏸️ Pós-MVP
Dependencias: TRI-003, TRI-004
Nota: "Precisa definição de autonomia da LIA antes de implementar. Reunião de 06/02/2026: adiar até que haja consenso sobre até onde a LIA pode decidir autonomamente."

Descricao: |
  Sistema de pré-qualificação que avalia automaticamente a aderência
  do candidato à vaga ANTES de iniciar as perguntas de triagem WSI.
  Usa RubricEvaluationService para analisar CV vs requisitos e apresenta
  mensagem humanizada ao candidato com opções de prosseguir ou desistir.
  
  Objetivo: Economizar tempo do candidato e da LIA evitando triagens
  para perfis muito distantes dos requisitos, enquanto mantém a
  decisão final nas mãos do candidato (transparência).

Historia de Usuario: |
  Como candidato, eu quero saber antecipadamente se meu perfil
  está alinhado com a vaga, para que eu possa decidir se vale
  a pena continuar com a triagem ou buscar outras oportunidades.
  
  Como recrutador, eu quero que a LIA pré-filtre candidatos
  muito distantes dos requisitos para otimizar o tempo de triagem.

Regras de Negocio:
  1. Executar após confirmação do CV pelo candidato
  2. Usar RubricEvaluationService para calcular score de aderência
  3. Thresholds configuráveis (padrão: 70/50/30)
  4. Score ≥70%: avança automaticamente para triagem (perfil alinhado)
  5. Score 50-69%: pergunta se quer continuar (perfil parcial)
  6. Score 30-49%: alerta sobre gaps, oferece opções (perfil distante)
  7. Score <30%: desencorajar gentilmente, oferece alternativas (muito distante)
  8. NUNCA mostrar porcentagens ao candidato (mensagens humanizadas)
  9. Explicar gaps de forma transparente ("não encontrei experiência com X")
  10. Opções do candidato: Continuar, Banco de Talentos, Encerrar
  11. Persistir resultado, score e decisão no banco de dados

Requisitos Tecnicos:
  Backend:
    - PreQualificationService class (app/services/pre_qualification_service.py)
    - Integração com RubricEvaluationService
    - Integração com ConversationManager
    - Enum PreQualificationResult (ALIGNED, PARTIAL, DISTANT, VERY_DISTANT)
    - Enum PreQualificationDecision (CONTINUE, TALENT_POOL, DECLINED)
    - Templates de mensagens humanizadas por nível de aderência
    - Botões WhatsApp: prequal_continue, prequal_talent_pool, prequal_decline
  Dados:
    - whatsapp_conversations: pre_qualification_result, pre_qualification_score, pre_qualification_decision
    - Migration 014_add_pre_qualification_fields.sql

Design & Componentes:
  N/A - Backend only (interface via WhatsApp)

Comportamento de Fluxo:
  Estados WhatsApp:
    CONFIRMING_CV → PRE_QUALIFICATION → SCREENING (ou COMPLETED)
  
  Fluxo por Resultado:
    ALIGNED (≥70%):
      - Candidato confirma CV
      - LIA: "Seu perfil está bem alinhado! Vamos às perguntas..."
      - Avança direto para SCREENING (sem perguntar)
    
    PARTIAL (50-69%):
      - LIA: "Analisei seu currículo... [highlight positivo]"
      - LIA: "Porém, a vaga pede X, Y — não encontrei no seu CV."
      - LIA: "Quer continuar com a triagem?"
      - Botões: [Sim, quero continuar] [Não, obrigado]
    
    DISTANT (30-49%):
      - LIA: "Quero ser transparente: sua experiência não está muito alinhada..."
      - LIA: "As chances de avançar são menores nesse caso."
      - Botões: [Continuar mesmo assim] [Banco de talentos] [Encerrar]
    
    VERY_DISTANT (<30%):
      - LIA: "Não encontrei nenhuma das experiências que a vaga exige..."
      - LIA: "Não quero que você perca tempo."
      - Botões: [Banco de talentos] [Continuar mesmo assim] [Encerrar]

  Decisões do Candidato:
    CONTINUE:
      - Avança para SCREENING
      - Registra decisão no banco
    
    TALENT_POOL:
      - Cria candidato no banco de talentos
      - Marca como COMPLETED
      - Envia mensagem de confirmação
    
    DECLINED:
      - Marca como COMPLETED
      - Envia mensagem de despedida

Exemplos de Mensagens:
  PARTIAL:
    "Analisei seu currículo para a vaga de Desenvolvedor Python na TechCorp.
    
    Encontrei experiência relevante com Python e Django — isso é ótimo!
    
    Porém, a vaga também pede experiência com AWS e Docker — e não encontrei 
    essas informações no seu currículo.
    
    Isso não significa que você não possa participar! A triagem conversacional 
    pode revelar experiências que você não mencionou no documento.
    
    Quer continuar com a triagem?"

  VERY_DISTANT:
    "Analisei seu currículo para a vaga de Desenvolvedor Python na TechCorp.
    
    Preciso ser sincera: não encontrei no seu currículo nenhuma das experiências 
    que a vaga exige.
    
    A posição é para desenvolvimento backend com Python, AWS e microsserviços, 
    e sua experiência parece ser em uma área bem diferente.
    
    Não quero que você perca tempo — processos seletivos podem ser longos e 
    frustrantes quando o perfil não se encaixa.
    
    O que você prefere fazer?"

DoD:
  - [ ] PreQualificationService implementado
  - [ ] Integração com RubricEvaluationService
  - [ ] Integração com ConversationManager
  - [ ] Templates de mensagens humanizadas
  - [ ] Botões WhatsApp funcionais
  - [ ] Campos de pré-qualificação no banco
  - [ ] Auto-avanço para perfis alinhados
  - [ ] Opções: continuar, banco de talentos, encerrar

Criterios de Aceitacao:
  - [ ] Candidato com score ≥70% avança direto
  - [ ] Candidato com score <70% recebe opções
  - [ ] Mensagens não mostram porcentagens
  - [ ] Explicação de gaps é transparente
  - [ ] Todas as decisões persistidas no banco
  - [ ] Fluxo funciona via WhatsApp buttons

Arquivos de Referencia (Prototipo Replit):
  - notification_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/notification_service.py
  - communication_dispatcher.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/communication_dispatcher.py
  - kpi-alert-system.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/alerts/kpi-alert-system.tsx
```

---

### CARD TRI-013: Sistema de Reporte de Problemas pelo Candidato
**Épico:** É5 — Triagem WhatsApp

```yaml
Titulo: "[FULL-STACK] Sistema de Reporte de Problemas pelo Candidato"
Tipo: Feature (Full-Stack)
Area: Full-Stack
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 5
Prioridade: Alta
Epic: EPIC-TRIAGEM
Status: 📋 A Criar no Jira
Dependencias: TRI-003, TRI-004

Descricao: |
  Sistema de reporte de problemas durante a triagem via WhatsApp.
  Ao iniciar a triagem (após aceite LGPD), a LIA informa proativamente
  o candidato sobre o procedimento de reporte: se houver qualquer problema,
  ele pode digitar palavras-chave (ex: "AJUDA", "#PROBLEMA") e receberá
  retorno em até 24 horas. Ao detectar a keyword, a LIA pausa a conversa,
  cria um incidente e notifica o time WeDo Talent (suporte/operações),
  NÃO o recrutador do cliente. O time WeDo Talent pode assumir a
  conversa manualmente, resetar a LIA ou escalonar.

Historia de Usuario: |
  Como candidato em triagem via WhatsApp, eu quero ser informado no início
  da triagem sobre como reportar problemas, e se a IA não fizer sentido,
  eu quero poder digitar um código para que o time de suporte me ajude
  em até 24 horas.

Regras de Negocio:
  1. LIA informa procedimento de reporte no INÍCIO da triagem (pós-LGPD):
     "Se a qualquer momento você tiver algum problema ou eu não fizer sentido,
     basta digitar AJUDA que nosso time será notificado e retornará em até 24 horas."
  2. Palavras-chave de escape: "AJUDA", "#PROBLEMA", "PARAR", "HUMANO", "HELP"
  3. Detecção case-insensitive e com tolerância a acentos (AJUDA = ajuda = Ajudá)
  4. Ao detectar keyword: pausar conversa da LIA imediatamente
  5. Criar incidente automático com: candidato_id, job_id, timestamp, últimas 5 mensagens, trigger_keyword
  6. Notificar time WeDo Talent (suporte/operações) — NÃO o recrutador do cliente: push notification + email
  7. Candidato recebe mensagem: "Entendi! Nosso time foi notificado e entrará em contato em até 24 horas. 🙏"
  8. Time WeDo Talent pode: (a) assumir conversa manualmente, (b) resetar LIA, (c) marcar como resolvido, (d) escalonar
  9. SLA de resposta: 24 horas (configurável por tenant)
  10. Escalonamento: se SLA não cumprido, notificar admin WeDo Talent
  11. Incidente resolvido: log de resolução + candidato pode continuar triagem

Requisitos Tecnicos:
  Frontend:
    - IncidentsPanel: lista de incidentes pendentes/resolvidos com filtros (para time WeDo Talent)
    - IncidentDetailView: detalhes do incidente + histórico de conversa + ações
    - IncidentBadge: contador de incidentes pendentes no sidebar/header
    - Botões de ação: "Assumir conversa" / "Resetar LIA" / "Marcar resolvido" / "Escalonar"
    - Integração com sistema de notificações existente
  Backend:
    - Mensagem proativa da LIA no início da triagem (pós-LGPD) informando procedimento de reporte
    - Detecção de palavras-chave no message handler (WhatsApp webhook)
    - POST /api/v1/incidents (criação automática ao detectar keyword)
    - GET /api/v1/incidents (lista paginada com filtros: status, job_id, date)
    - GET /api/v1/incidents/{id} (detalhes + conversa)
    - PATCH /api/v1/incidents/{id} (atualizar status: assigned, resolved)
    - POST /api/v1/incidents/{id}/assign (time WeDo Talent assume)
    - POST /api/v1/incidents/{id}/resolve (marcar resolvido)
    - Notificação push + email para time WeDo Talent (suporte/operações) — NÃO para recrutador do cliente
    - SLA checker: job agendado que verifica incidentes não resolvidos (SLA padrão 24h)
  Dados:
    - screening_incidents: id, candidate_id, job_id, trigger_keyword, last_messages (JSONB), status (enum: open, assigned, resolved, escalated), assigned_to (user_id nullable), resolution_note, sla_deadline, created_at, resolved_at, updated_at
    - incident_notifications: id, incident_id, user_id, channel (push/email), sent_at, read_at
  Validacoes:
    - Palavras-chave não devem gerar falsos positivos em contexto normal
    - Incidente duplicado: não criar novo se já existe incidente aberto para mesmo candidato+vaga
    - SLA deadline: 24 horas a partir da criação do incidente (configurável por tenant)

Design & Componentes:
  Componentes Existentes:
    - NotificationCenter - centro de notificações (adicionar badge)
    - CandidateCard - card do candidato (adicionar indicador de incidente)
    - Sidebar - menu lateral (adicionar badge de incidentes)
    - Toast - feedback de ações
    - Badge - contadores
  Novos Componentes:
    - IncidentsPanel - painel com lista de incidentes (tabela + filtros)
    - IncidentDetailView - detalhes do incidente com timeline de conversa
    - IncidentBadge - badge vermelho com contador no sidebar
    - IncidentActionBar - barra de ações (assumir, resetar, resolver)
    - IncidentSLAIndicator - indicador visual de tempo restante do SLA
  Design Tokens:
    Urgente/Aberto: --electric-red (#de1c31)
    Atribuído: --wedo-yellow (#EAB308)
    Resolvido: --wedo-green (#22C55E)
    Escalado: --electric-red (#de1c31) + pulsing animation
    SLA OK: --wedo-green (#22C55E)
    SLA Warning (< 30min): --wedo-yellow (#EAB308)
    SLA Estourado: --electric-red (#de1c31)
    Background: --lia-bg-primary (#FFFFFF)
    Card Border Incident: --electric-red (#de1c31) / 20% opacity
  Layout:
    IncidentsPanel: full-width table com colunas (candidato, vaga, keyword, status, SLA, ações)
    IncidentDetail: split view — detalhes (60%) + conversa (40%)
    Badge: circle vermelho no sidebar, 20px, font-size 11px
    Mobile: stack vertical (detalhes acima, conversa abaixo)
  Estados:
    - Sem incidentes: painel vazio com ícone e texto "Nenhum incidente pendente"
    - Incidentes pendentes: badge vermelho pulsante no sidebar
    - Incidente aberto: card vermelho com timer SLA
    - Incidente atribuído: card amarelo com nome do operador WeDo Talent
    - Incidente resolvido: card verde com nota de resolução
    - SLA estourado: card vermelho com ícone de alerta + escalonamento
  Acessibilidade:
    - Badge com aria-label "X incidentes pendentes"
    - Lista com role="list" e items com role="listitem"
    - Ações com aria-label descritivo
    - SLA timer com aria-live="polite" para atualizações
    - Cores complementadas com ícones (não depender só de cor)

Comportamento de UI:
  Fluxo Proativo (Início da Triagem):
    1. Candidato aceita LGPD e inicia triagem
    2. LIA envia mensagem proativa informando procedimento de reporte:
       "Se a qualquer momento você tiver algum problema ou eu não fizer sentido,
       basta digitar AJUDA que nosso time será notificado e retornará em até 24 horas."
    3. Triagem prossegue normalmente

  Fluxo de Reporte:
    1. Candidato digita "AJUDA" durante triagem WhatsApp
    2. Backend detecta keyword, pausa conversa da LIA
    3. Candidato recebe: "Entendi! Nosso time foi notificado e entrará em contato em até 24 horas. 🙏"
    4. Incidente criado automaticamente com últimas 5 mensagens
    5. Time WeDo Talent (suporte) recebe notificação push + email
    6. Badge vermelho aparece no sidebar do operador WeDo Talent
    7. Operador abre IncidentsPanel, vê incidente com SLA timer (24h)
    8. Clica no incidente → IncidentDetailView com conversa
    9. Escolhe: "Assumir conversa" (fala direto com candidato), "Resetar LIA", ou "Escalonar"
    10. Ao resolver: marca como resolvido com nota, candidato pode continuar

  Layout:
    Desktop: Sidebar badge + IncidentsPanel full-width + IncidentDetail split 60/40 (painel do time WeDo Talent)
    Tablet: IncidentsPanel full-width, IncidentDetail stacked
    Mobile: Badge no header, lista mobile-friendly, detail full-screen

  Estados de Botoes:
    Assumir Conversa:
      - Default: bg-wedo-cyan, text white
      - Hover: bg-wedo-cyan/90
      - Loading: spinner + "Assumindo..."
      - Disabled: se já atribuído a outro operador
    Resetar LIA:
      - Default: bg-transparent, border --wedo-yellow
      - Hover: bg-wedo-yellow/10
      - Confirm: dialog "Resetar a LIA e retomar triagem automática?"
    Marcar Resolvido:
      - Default: bg-wedo-green, text white
      - Hover: bg-wedo-green/90
      - Requires: nota de resolução obrigatória (mínimo 10 chars)

  Validacoes Inline:
    Nota de Resolução:
      - Vazia: "Descreva como o incidente foi resolvido"
      - Muito curta (< 10 chars): "Detalhe a resolução (mínimo 10 caracteres)"

  Mensagens de Feedback:
    - Incidente criado: "[interno] Novo incidente #123 — candidato João Silva na vaga Analista" (toast para time WeDo Talent)
    - Conversa assumida: "Você assumiu a conversa com João Silva. Mensagens serão enviadas por você."
    - LIA resetada: "LIA reiniciada. A triagem automática continuará de onde parou."
    - Incidente resolvido: "Incidente #123 resolvido. Candidato pode continuar a triagem."
    - SLA estourado: "⚠️ Incidente #123 sem resposta há 24h. Escalonando para admin WeDo Talent."
    - Erro: "Erro ao processar incidente. Tente novamente."

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md (Seções: 2.3 Cards, 2.6 Badges & Tags, 2.8 Toasts & Alerts, 2.11 Dropdowns & Menus)"
  Figma: "[A ser preenchido pelo time de Design — tela de incidentes]"
  Assets:
    - "Ícone de alerta: lucide-react/AlertTriangle"
    - "Ícone de resolver: lucide-react/CheckCircle"
    - "Ícone de assumir: lucide-react/UserCheck"
    - "Ícone de resetar: lucide-react/RotateCcw"
    - "Ícone de SLA: lucide-react/Clock"
  Tokens:
    - "urgente: #de1c31"
    - "atribuido: #EAB308"
    - "resolvido: #22C55E"
    - "bg-primary: #FFFFFF"

DoD:
  - [ ] LIA informa procedimento de reporte no início da triagem (pós-LGPD)
  - [ ] Detecção de palavras-chave de escape funcional no message handler
  - [ ] Conversa da LIA pausada ao detectar keyword
  - [ ] Incidente criado automaticamente com últimas 5 mensagens
  - [ ] Notificação push + email enviada ao time WeDo Talent (NÃO ao recrutador do cliente)
  - [ ] Candidato recebe confirmação com prazo de 24h
  - [ ] IncidentsPanel com lista e filtros funcional (para time WeDo Talent)
  - [ ] IncidentDetailView com conversa e ações funcional
  - [ ] Badge de incidentes no sidebar com contador
  - [ ] Ação "Assumir conversa" funcional
  - [ ] Ação "Resetar LIA" funcional
  - [ ] Ação "Marcar resolvido" com nota obrigatória
  - [ ] SLA timer (24h) e escalonamento funcional
  - [ ] Responsivo (desktop, tablet, mobile)

Criterios de Aceitacao:
  - [ ] LIA envia mensagem proativa sobre reporte no início da triagem (pós-LGPD)
  - [ ] Candidato digita "AJUDA" → conversa pausa imediatamente
  - [ ] Candidato recebe mensagem de confirmação com prazo de 24h
  - [ ] Incidente aparece na lista do time WeDo Talent em < 5 segundos
  - [ ] Notificação push + email recebida pelo time WeDo Talent (NÃO pelo recrutador)
  - [ ] Badge vermelho aparece no sidebar com contagem correta
  - [ ] Operador WeDo Talent consegue ver histórico de conversa no detalhe do incidente
  - [ ] "Assumir conversa" permite envio manual de mensagens ao candidato
  - [ ] "Resetar LIA" retoma triagem automática
  - [ ] SLA timer funciona corretamente (24 horas)
  - [ ] Incidentes duplicados não são criados (mesmo candidato+vaga)

Arquivos de Referencia (Prototipo Replit):
  - notification-center.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/notifications/notification-center.tsx
  - notification-context.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/notifications/notification-context.tsx
  - screening-config: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/screening-config/
  - kanban-board: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/kanban/components/KanbanBoard.tsx
  - candidate-card: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/kanban/components/CandidateCard.tsx
```

---

### CARD TRI-014: Pesquisa de Alternativas a Twilio
**Épico:** É5 — Triagem WhatsApp

> ⚠️ **DISCLAIMER:** A pesquisa e avaliação sobre Twilio e suas alternativas é de responsabilidade exclusiva do **Paulo Moraes**.

```yaml
Titulo: "[PESQUISA] Pesquisa de Alternativas a Twilio para Disparo WhatsApp"
Tipo: Research/Spike
Area: Processo/Validação
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 3
Prioridade: Crítica
Epic: EPIC-TRIAGEM
Status: 🔄 Em Andamento — Pesquisa Concluída, Pendente POC
Jira: WT-1338 (https://wedotalent.atlassian.net/browse/WT-1338)
Responsavel: Paulo Moraes (pesquisa exclusiva)
Dependencias: Nenhuma (card bloqueante — habilita Épico 5 inteiro)
Consolida: INT-ALT-001 (Alternativa a Twilio para WhatsApp — mesmo escopo, card único)

Documento de Pesquisa: docs/pesquisa-alternativas-whatsapp.md

Resultado da Pesquisa (09/fev/2026):
  Recomendacao Principal: Gupshup (Partner Program)
  Modelo Operacional: WeDo Talent como Tech Provider — provisiona WABAs por cliente
  Justificativa: |
    - $0 setup, $0 mensal, $0.001/msg markup (menor custo total)
    - Partner Dashboard multi-WABA nativo
    - Embedded Signup integrado (cliente verifica Meta dentro da plataforma WeDo)
    - API REST documentada, webhooks robustos, forte presença LATAM
  Plano B: 360dialog ($0 markup por mensagem, melhor custo unitário alto volume)
  Descartados MVP: Twilio (markup alto), Zenvia ($649 setup, pricing opaco), Infobip (enterprise-only)
  Custo Estimado: ~$37.88/mês para 2.000 msgs/mês (100 triagens × 20 msgs)
    Nota: Cálculo atualizado com taxas Meta 2026 reais ($0.0625 marketing + $0.0068 utility)
    Conversão BRL: taxa de referência $1 = R$ 5.80

  Comparativo Detalhado de BSPs (atualizado 09/fev/2026):
    Contexto: |
      Desde 01/jul/2025, Meta cobra por mensagem (não mais por conversa).
      Todo BSP cobra taxa Meta + taxa própria.
    
    Taxa Meta Brasil 2026:
      Marketing: $0.0625/msg (R$ 0.36)
      Utility: $0.0068/msg (R$ 0.04)
      Authentication: Similar a utility (volume-tiered)
      Service (resposta em 24h): GRÁTIS

    Provedores Avaliados:
      1_Gupshup:
        Modelo: Pay-as-you-go, sem mensalidade
        Taxa BSP: $0.001/msg (R$ 0.006)
        Markup Marketing jan/2026: +6% via Cloud API
        Setup: $0
        Partner Program: $0 mensal, provisiona números para clientes
        Ideal: Tech Providers (nosso caso), alto volume
      2_Twilio:
        Modelo: Pay-as-you-go, sem mensalidade
        Taxa BSP: $0.005/msg (R$ 0.029) — envio E recebimento
        Falha de entrega: $0.001 extra
        Setup: $0
        Ideal: Devs que precisam de API robusta e docs excelentes
      3_360dialog:
        Modelo: Assinatura mensal + taxa Meta (zero markup)
        Mensalidade: €49 (básico) / €99 (profissional) / até €500 (enterprise)
        Taxa BSP: $0 markup (só paga Meta)
        Ideal: ISVs e parceiros com alto volume
      4_Infobip:
        Modelo: Assinatura + markup por mensagem
        Mensalidade: A partir de €39/mês (módulo Conversations)
        Markup: ~10-15% sobre taxa Meta
        Setup: Negociável (enterprise)
        Ideal: Grandes empresas omnichannel (SMS + Email + WhatsApp)
      5_Zenvia:
        Modelo: Volume escalonado (BRL)
        Business-Initiated: R$ 0.49-0.55/msg
        User-Initiated: R$ 0.22-0.30/msg
        Setup: R$ 649
        Ideal: Empresas que querem faturar 100% em BRL, suporte PT-BR
      6_WATI:
        Modelo: Assinatura + ~20% markup
        Mensalidade: $79-99/mês (5 usuários)
        Markup: ~20% sobre taxa Meta
        Setup: Incluso no plano
        Ideal: Pequenas equipes, interface no-code
      7_Respond_io:
        Modelo: Assinatura somente (zero markup)
        Mensalidade: Sob consulta (estimado $79-199/mês)
        Taxa BSP: $0 (só paga Meta)
        Ideal: Omnichannel (10+ canais), IA integrada, escala
      8_MessageBird:
        Modelo: Pay-as-you-go + markup
        Taxa BSP: $0.005/template + $0.005/sessão
        Setup: $0
        Ideal: Empresas que já usam Bird para SMS

    Simulacao Custo MVP (2.000 msgs/mês — 100 triagens × 20 msgs):
      Premissas: 80% utility (1.600 msgs) + 20% marketing (400 msgs)
      Taxa Meta base: $35.88/mês
      Ranking:
        1_Gupshup: $37.88/mês (~R$ 220) — Taxa Meta + $2.00 markup
        2_Twilio: $45.88/mês (~R$ 265) — Taxa Meta + $10.00 markup
        3_MessageBird: $45.88/mês (~R$ 265) — Taxa Meta + $10.00 markup
        4_Infobip: $82.36/mês (~R$ 475) — Taxa Meta + $4.48 markup + €39 mensalidade
        5_360dialog: $88.88/mês (~R$ 515) — Taxa Meta + $0 markup + €49 mensalidade
        6_WATI: $122.06/mês (~R$ 705) — Taxa Meta + $7.18 markup + $79 mensalidade
        7_Respond_io: $134.88/mês (~R$ 780) — Taxa Meta + $0 markup + ~$99 mensalidade
        8_Zenvia: ~R$ 950/mês — tarifa integrada BRL

    Simulacao Escala (10.000 msgs/mês — 50 clientes):
      Taxa Meta base: $179.40/mês
      Ranking:
        1_Gupshup: $189.40/mês
        2_Twilio: $229.40/mês
        3_360dialog: $286.40/mês (€99 profissional)
        4_Respond_io: $378.40/mês
        5_Zenvia: ~R$ 4.750/mês

    Ranking por Criterio:
      Menor custo MVP: 1-Gupshup, 2-Twilio, 3-MessageBird
      Menor custo escala: 1-Gupshup, 2-Twilio, 3-360dialog
      Melhor API/Docs: 1-Twilio, 2-Gupshup, 3-360dialog
      Multi-tenant (nosso caso): 1-Gupshup, 2-360dialog, 3-Twilio
      Suporte Brasil/PT: 1-Zenvia, 2-Infobip, 3-Gupshup
      Facilidade no-code: 1-WATI, 2-Respond.io, 3-Zenvia
      Zero markup: 1-360dialog, 2-Respond.io

    Recomendacao Final (modelo Tech Provider - provisionar número por cliente):
      1_Principal: Gupshup — menor custo, Partner Program $0, Embedded Signup
      2_Plano B: 360dialog — zero markup alto volume, bom para ISV, mas mensalidade fixa
      3_Alternativa: Twilio — API excelente, mas markup $0.005/msg é 5x maior que Gupshup

Proximos Passos:
  1. Criar conta Partner no Gupshup (Paulo Moraes, 09/02/2026)
  2. Verificar Meta Business Manager da WeDo Talent (09-13/02/2026)
  3. Registrar número de teste e criar template de triagem
  4. POC — enviar/receber mensagens via API
  5. Documentar integração para time de produção

Checklist Documentos Cliente (para provisionar número):
  Obrigatorios:
    - Razão Social
    - CNPJ
    - Endereço comercial
    - Site oficial da empresa
    - Email corporativo (domínio da empresa)
    - Número de telefone (não pode estar ativo no WhatsApp pessoal)
    - Nome de exibição desejado (ex "Itaú Talentos")
  Opcionais:
    - Logo (PNG alta resolução)
    - Descrição curta (até 256 chars)
    - Categoria do negócio
    - Contato interno responsável

Descricao: |
  ⚠️ DISCLAIMER: A pesquisa sobre Twilio e alternativas é de responsabilidade
  exclusiva do Paulo Moraes.

  Pesquisar e comparar alternativas ao Twilio para disparo de mensagens
  WhatsApp Business, priorizando soluções que aceitem número fornecido
  pelo cliente (BYOD — Bring Your Own Device) e tenham homologação
  simplificada no Brasil. Twilio ficou sem sentido por exigir número
  homologado e ter processo complexo no Brasil.
  Este card consolida INT-ALT-001 (mesmo escopo) em um único card.
  
  ATUALIZAÇÃO 09/02/2026: Pesquisa concluída. Recomendação: Gupshup como BSP
  principal, modelo Tech Provider (WeDo provisiona WABAs para cada cliente).
  Documento completo: docs/pesquisa-alternativas-whatsapp.md

Historia de Usuario: |
  Como CTO, eu quero avaliar alternativas ao Twilio para disparo de
  WhatsApp que sejam mais viáveis no Brasil (homologação, custo, suporte),
  para desbloquear o desenvolvimento da triagem via WhatsApp.

Regras de Negocio:
  1. Avaliar mínimo 5 alternativas: Tudu, Zenvia, Slickflow, WhatsApp Business Cloud API, Gupshup
  2. Critérios obrigatórios de avaliação (ver lista abaixo)
  3. Tabela comparativa completa com pontuação por critério
  4. POC (Proof of Concept) com as 2 melhores alternativas
  5. POC deve incluir: envio de mensagem, recebimento de webhook, template Meta
  6. Recomendação final documentada com justificativa
  7. Considerar: escalabilidade (1K → 100K mensagens/mês), multi-tenant, logs/auditoria
  8. Budget de referência: máximo R$ 0,15/mensagem (média)
  9. Resultado deve habilitar implementação de abstração de provider (TRI-001)

Criterios de Avaliacao:
  1. Custo por mensagem (HSM template + sessão 24h)
  2. Facilidade de homologação de número no Brasil (BYOD vs número deles)
  3. Suporte a templates Meta (criação, submissão, aprovação, variáveis)
  4. Webhook de status (enviado, entregue, lido, falha) com latência
  5. SDK/API quality (documentação, tipagem, exemplos, SDKs oficiais)
  6. Suporte Brasil (idioma, SLA de suporte, horário, representante local)
  7. SLA de entrega de mensagens (< 5s para 95% das mensagens)
  8. Sandbox/ambiente de teste gratuito para desenvolvimento
  9. Escalabilidade (throughput, rate limits, filas)
  10. Compliance (LGPD, dados no Brasil, criptografia)

Requisitos Tecnicos:
  Frontend:
    - Nenhum (pesquisa e documentação)
  Backend:
    - POC com 2 providers: script de envio + recebimento de webhook
    - Validar: latência de entrega, formato de webhook, retry policy
    - Documentar interface abstrata para WhatsApp provider
  Dados:
    - Tabela comparativa em formato Markdown/spreadsheet
    - Logs da POC: tempos de entrega, taxas de sucesso, erros
  Validacoes:
    - POC deve enviar mínimo 50 mensagens de teste por provider
    - Webhook deve ser recebido em < 10s após envio
    - Template Meta deve ser aprovado no sandbox

Design & Componentes:
  Componentes Existentes:
    - Nenhum (pesquisa, não UI)
  Novos Componentes:
    - Nenhum (pesquisa, não UI)
  Design Tokens:
    N/A
  Layout:
    N/A (documento de pesquisa)
  Estados:
    - Pesquisa: levantamento de informações e pricing
    - POC: implementação e teste com top 2
    - Análise: consolidação de resultados
    - Recomendação: documento final com decisão
  Acessibilidade:
    N/A

Comportamento de UI:
  Fluxo Principal:
    1. Levantar informações de pricing e features de cada provider
    2. Preencher tabela comparativa com 10 critérios × 5 providers
    3. Pontuar cada provider por critério (1-5)
    4. Selecionar top 2 por pontuação total
    5. Implementar POC com top 2 (envio + webhook + template)
    6. Executar testes: 50 mensagens por provider, medir latência e taxa de sucesso
    7. Consolidar resultados em documento de recomendação
    8. Apresentar para time e tomar decisão

  Layout:
    N/A (documento)

  Estados de Botoes:
    N/A

  Validacoes Inline:
    N/A

  Mensagens de Feedback:
    N/A

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md (Seções: N/A — Card de pesquisa documental)"
  Figma: "N/A (pesquisa)"
  Assets:
    - "Template de tabela comparativa de providers"
    - "Template de documento de recomendação técnica"
  Tokens:
    - "N/A"

DoD:
  - [ ] Tabela comparativa preenchida com 5 providers × 10 critérios
  - [ ] POC implementada com top 2 alternativas
  - [ ] POC testada: mínimo 50 mensagens por provider
  - [ ] Webhook de status validado (enviado, entregue, lido)
  - [ ] Template Meta submetido e aprovado no sandbox de cada provider
  - [ ] Métricas de POC documentadas (latência, taxa sucesso, custo real)
  - [ ] Recomendação final documentada com justificativa
  - [ ] Interface abstrata de WhatsApp provider documentada (para TRI-001)
  - [ ] INT-ALT-001 marcado como consolidado neste card

Criterios de Aceitacao:
  - [ ] Todos os 5 providers avaliados com 10 critérios cada
  - [ ] Pontuação total calculada e ranking definido
  - [ ] POC com top 2 providers funcional (envio + recebimento)
  - [ ] Latência de entrega < 5s para 95% das mensagens em ambas as POCs
  - [ ] Custo por mensagem dentro do budget (≤ R$ 0,15/msg)
  - [ ] Recomendação final clara com provider escolhido
  - [ ] Documento acessível para todo o time técnico
  - [ ] Interface abstrata de provider permite trocar provider sem mudar código de negócio

Arquivos de Referencia (Prototipo Replit):
  - screening-config: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/screening-config/
  - middleware: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/middleware/
  - services: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/
  - whatsapp-related: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/ats_clients/
```

---

## ÉPICO 6: SCORE WSI

---

### CARD SCO-001: Cálculo de Score WSI
**Épico:** É6 — Score WSI

```yaml
Titulo: [AI] Motor de Cálculo de Score WSI
Tipo: Feature
Area: Full-Stack
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 13
Prioridade: Crítica
Epic: EPIC-SCORE-WSI
Status: 📋 Pendente Jira

Descricao: |
  Implementar o motor de cálculo do WSI (WeDoTalent Skill Index) que
  processa as respostas do candidato durante a triagem e gera um
  score final de 0 a 5, utilizando pesos configuráveis por competência.
  Base científica: Bloom + Dreyfus + Big Five + CBI.

Historia de Usuario: |
  Como recrutador, eu quero que a LIA calcule automaticamente um
  score de competência para cada candidato triado, para que eu possa
  tomar decisões baseadas em dados objetivos.

Regras de Negocio:
  1. Score WSI varia de 0.0 a 5.0 (escala Dreyfus)
  2. Fórmula: Score_skill = (0.6 × Autodeclaração) + (0.4 × Contexto)
  3. WSI_final = Σ(Peso_skill × Score_skill) / 100
  4. Pesos padrão: Técnico 70%, Comportamental 30%
  5. Penalidade por inflação: -0.5 a -1.5 se autodeclara alto mas contexto pobre
  6. Bônus por humildade: +0.5 se autodeclara baixo mas demonstra contexto alto
  7. Score arredondado para 1 casa decimal
  8. Guardar breakdown de cada dimensão avaliada

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/wsi/calculate
    - GET /api/v1/wsi/score/{candidate_id}
    - WSICalculatorService class
    - Integração com LLM para análise de respostas
  Frontend:
    - Componente WSIScoreBadge para exibição
    - Hook useWSIScore para buscar score
  Dados:
    - wsi_scores: id, candidate_id, job_id, overall_score, technical_score, behavioral_score, dimensions (JSONB), calculated_at, version
    - wsi_responses: id, candidate_id, question_id, response_text, autodeclaration_score, context_score, bloom_level, dreyfus_level
  Validacoes:
    - Score deve estar entre 0.0 e 5.0
    - Todos os blocos de triagem devem estar completos
    - Penalidades e bônus registrados no breakdown

Integracoes Externas:
  LLM (Claude/Gemini):
    - Tipo: AI API
    - Uso: Análise semântica das respostas para extrair nivel cognitivo e proficiência
    - Serviço: wsi_analyzer_service.py
    - Secret: ANTHROPIC_API_KEY ou GEMINI_API_KEY
    - Custo: ~$0.01-0.03 por candidato (dependendo do tamanho das respostas)

Configuracao LLM:
  Modelo Recomendado: Claude 3.5 Sonnet ou Gemini 1.5 Pro
  Temperatura: 0.2 (determinístico para avaliação)
  Max Tokens: 2000
  
  Prompt Template: |
    <role>
    Você é um avaliador especializado em competências profissionais,
    usando a metodologia WSI (WeDoTalent Skill Index) baseada em Bloom,
    Dreyfus e Big Five.
    </role>
    
    <task>
    Analise a resposta do candidato abaixo e avalie:
    1. Nível cognitivo Bloom (1-6)
    2. Nível de proficiência Dreyfus (1-5)
    3. Consistência entre autodeclaração e evidências
    </task>
    
    <question>{{question}}</question>
    <autodeclaration>{{autodeclaration_score}}/5</autodeclaration>
    <response>{{candidate_response}}</response>
    
    <output_format>
    {
      "bloom_level": 1-6,
      "dreyfus_level": 1-5,
      "context_score": 0.0-5.0,
      "penalty": -1.5 a 0,
      "bonus": 0 a 0.5,
      "reasoning": "Explicação breve da avaliação"
    }
    </output_format>

Design & Componentes:
  Componentes Existentes:
    - Badge - exibição do score
    - Tooltip - explicação do score
    - Skeleton - loading durante cálculo
  Novos Componentes:
    - WSIScoreBadge - badge colorido com score (0-5)
    - WSICalculating - animação durante processamento
  Design Tokens:
    Score Excelente (4.5-5.0): --wedo-green (#22C55E)
    Score Alto (4.0-4.4): --wedo-cyan (#60BED1)
    Score Médio (3.0-3.9): --wedo-yellow (#EAB308)
    Score Regular (2.0-2.9): --wedo-orange (#F97316)
    Score Baixo (<2.0): --electric-red (#de1c31)
    Background: --lia-bg-primary (#FFFFFF)
    Text: --lia-text-primary (#111827)
  Layout:
    Badge: rounded-full, px-3 py-1, font-semibold
    Tooltip: max-w-xs com breakdown
  Estados:
    - Calculating (spinner + "Calculando...")
    - Calculated (score com cor)
    - Error (icone warning + retry)
  Acessibilidade:
    - ARIA-label com valor numérico
    - Cor não é único indicador (texto + ícone)
    - Tooltip acessível via keyboard

Comportamento de UI:
  Fluxo Principal:
    1. Triagem do candidato é finalizada
    2. Sistema dispara cálculo WSI automaticamente
    3. Badge mostra estado "Calculando..." com spinner
    4. LLM processa cada resposta (2-5 segundos)
    5. Score final calculado e persistido
    6. Badge atualiza com score colorido
    7. Notificação enviada ao recrutador
  
  Estados de Badge:
    Calculating:
      - Fundo: --lia-bg-tertiary
      - Texto: "Calculando..."
      - Ícone: spinner animado
    Calculated:
      - Fundo: cor baseada no score
      - Texto: "4.2" (score com 1 decimal)
      - Hover: tooltip com breakdown
    Error:
      - Fundo: --electric-red-light
      - Texto: "Erro"
      - Click: retry cálculo
  
  Mensagens de Feedback:
    - Sucesso: Toast verde "Score WSI calculado: 4.2/5.0"
    - Erro: Toast vermelho "Erro ao calcular score. Tentando novamente..."
    - Retry: Toast azul "Recalculando score..."

DoD:
  - [ ] Motor de cálculo implementado
  - [ ] Fórmula WSI correta
  - [ ] Penalidades e bônus aplicados
  - [ ] Scores persistidos no banco
  - [ ] Badge exibe score colorido
  - [ ] Testes unitários passando (>90% coverage)
  - [ ] Testes de integração com LLM

Criterios de Aceitacao:
  - [ ] Score calculado para todas as dimensões
  - [ ] Breakdown disponível por competência
  - [ ] Cores refletem faixas corretas
  - [ ] Recálculo funciona após erro
  - [ ] Score aparece no card do candidato

Arquivos de Referencia (Prototipo Replit):
  - wsi_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_service.py
  - wsi_deterministic_scorer.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_deterministic_scorer.py
  - lia_score_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/lia_score_service.py
  - wsi.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/wsi.py
```

---

### CARD SCO-002: Modelo Big Five Comportamental
**Épico:** É6 — Score WSI

```yaml
Titulo: [AI] Avaliação Big Five (OCEAN) Comportamental
Tipo: Feature
Area: Full-Stack
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 8
Prioridade: Alta
Epic: EPIC-SCORE-WSI
Status: 📋 Pendente Jira
Dependencias: SCO-001

Descricao: |
  Implementar a avaliação comportamental baseada no modelo Big Five
  (OCEAN) - Openness, Conscientiousness, Extraversion, Agreeableness,
  Neuroticism. Extrair traços comportamentais das respostas do candidato
  durante a triagem conversacional.
  Nota: Big Five é metodologia aplicada na GERAÇÃO de perguntas WSI (Épico 4), não um cálculo de score separado. A visualização aqui mostra os resultados das dimensões Big Five extraídas das respostas da triagem.

Historia de Usuario: |
  Como recrutador, eu quero entender o perfil comportamental do candidato
  baseado em evidências científicas, para avaliar fit cultural e adequação
  ao estilo de trabalho da equipe.

Regras de Negocio:
  1. 5 dimensões OCEAN com score de 1 a 10 cada
  2. Interpretação baseada em Goldberg (1992)
  3. Cada dimensão tem sub-fatores (2-3 por dimensão)
  4. Perfil comparado com ideal da vaga (se configurado)
  5. Não usar para eliminar candidatos, apenas para insights
  6. Exibir interpretação textual de cada traço
  7. Confidencial - não expor ao candidato

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/wsi/big-five/analyze
    - GET /api/v1/wsi/big-five/{candidate_id}
    - BigFiveAnalyzerService class
  Frontend:
    - BigFiveRadarChart component
    - BigFiveInsights panel
  Dados:
    - big_five_profiles: id, candidate_id, job_id, openness, conscientiousness, extraversion, agreeableness, neuroticism, sub_factors (JSONB), analysis_text, created_at
  Validacoes:
    - Scores normalizados para escala 1-10
    - Mínimo 3 respostas comportamentais para análise válida

Integracoes Externas:
  LLM (Claude/Gemini):
    - Tipo: AI API
    - Uso: Análise de linguagem para inferir traços OCEAN
    - Serviço: big_five_analyzer_service.py
    - Secret: ANTHROPIC_API_KEY ou GEMINI_API_KEY
    - Custo: ~$0.005 por análise

Configuracao LLM:
  Modelo Recomendado: Claude 3.5 Haiku ou Gemini 1.5 Flash
  Temperatura: 0.3
  Max Tokens: 1500
  
  Prompt Template: |
    <role>
    Você é um psicólogo organizacional especializado no modelo Big Five
    (OCEAN) de personalidade, validado cientificamente por Costa & McCrae.
    </role>
    
    <task>
    Analise as respostas comportamentais do candidato e infira scores
    para cada dimensão do Big Five. Base sua análise em evidências
    linguísticas e comportamentais demonstradas.
    </task>
    
    <responses>
    {{behavioral_responses}}
    </responses>
    
    <output_format>
    {
      "openness": { "score": 1-10, "confidence": 0.0-1.0, "evidence": "..." },
      "conscientiousness": { "score": 1-10, "confidence": 0.0-1.0, "evidence": "..." },
      "extraversion": { "score": 1-10, "confidence": 0.0-1.0, "evidence": "..." },
      "agreeableness": { "score": 1-10, "confidence": 0.0-1.0, "evidence": "..." },
      "neuroticism": { "score": 1-10, "confidence": 0.0-1.0, "evidence": "..." },
      "summary": "Resumo do perfil comportamental em 2-3 frases"
    }
    </output_format>

Design & Componentes:
  Componentes Existentes:
    - Card - container do perfil
    - Badge - indicadores de nível
    - Tooltip - explicações
  Novos Componentes:
    - BigFiveRadarChart - gráfico radar com 5 eixos (recharts)
    - BigFiveTraitCard - card individual por traço
    - BigFiveComparison - comparação com perfil ideal
  Design Tokens:
    Openness: --wedo-purple (#9860D1)
    Conscientiousness: --wedo-green (#22C55E)
    Extraversion: --wedo-orange (#F97316)
    Agreeableness: --wedo-cyan (#60BED1)
    Neuroticism: --electric-red (#de1c31)
    Background: --lia-bg-secondary (#F9FAFB)
    Border: --lia-border-subtle (#E5E7EB)
  Layout:
    Container: max-w-2xl mx-auto
    Radar Chart: aspect-square, max-w-sm
    Trait Cards: grid 2 colunas em desktop, 1 em mobile
    Spacing: gap-4 entre elementos
  Estados:
    - Loading (skeleton do radar)
    - Loaded (radar animado)
    - Comparison (radar duplo com overlay)
  Acessibilidade:
    - Tabela alternativa ao gráfico para screen readers
    - Descrições textuais de cada traço
    - Cores com padrões distintos (hatching)

Comportamento de UI:
  Fluxo Principal:
    1. Score WSI calculado (SCO-001)
    2. Análise Big Five executada automaticamente
    3. Radar chart renderiza com animação (1.5s)
    4. Hover em cada eixo mostra tooltip com detalhes
    5. Click em traço expande card com evidências
    6. Toggle para comparar com perfil ideal (se configurado)
  
  Estados do Radar:
    Loading:
      - Skeleton circular com pulso
      - Texto: "Analisando perfil..."
    Loaded:
      - Radar animado do centro para fora
      - Labels em cada ponta
      - Área preenchida semi-transparente
    Comparison:
      - Dois polígonos sobrepostos
      - Candidato: área sólida
      - Ideal: linha tracejada
      - Legenda distinguindo ambos
  
  Interações:
    Hover em eixo:
      - Tooltip: nome do traço + score + interpretação
      - Ex: "Conscienciosidade: 8/10 - Altamente organizado e focado"
    Click em eixo:
      - Expande card com evidências da análise
      - Mostra citações das respostas do candidato
    Toggle Comparação:
      - Switch "Comparar com perfil ideal"
      - Mostra overlay quando ativo
  
  Mensagens de Feedback:
    - Sucesso: Silencioso (já faz parte do fluxo WSI)
    - Erro: Toast amarelo "Análise comportamental incompleta - poucas respostas"
    - Confiança baixa: Badge "Baixa confiança" em traços com confidence < 0.6

DoD:
  - [ ] Análise Big Five implementada
  - [ ] 5 dimensões OCEAN calculadas
  - [ ] Radar chart funcional
  - [ ] Comparação com perfil ideal
  - [ ] Evidências por traço
  - [ ] Testes unitários passando

Criterios de Aceitacao:
  - [ ] Radar exibe 5 eixos corretamente
  - [ ] Scores variam de 1 a 10
  - [ ] Tooltips mostram interpretação
  - [ ] Comparação toggle funciona
  - [ ] Perfil salvo no banco

Arquivos de Referencia (Prototipo Replit):
  - big-five-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/big-five-modal.tsx
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/backend-proxy/big-five/profiles/route.ts
  - wsi_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_service.py
```

---

### CARD SCO-003: Avaliação Bloom/Dreyfus
**Épico:** É6 — Score WSI

```yaml
Titulo: [AI] Avaliação Técnica Bloom/Dreyfus
Tipo: Feature
Area: Full-Stack
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 8
Prioridade: Alta
Epic: EPIC-SCORE-WSI
Status: 📋 Pendente Jira
Dependencias: SCO-001

Descricao: |
  Implementar a avaliação de competências técnicas usando a
  Taxonomia de Bloom Revisada (níveis cognitivos) e o Modelo
  Dreyfus (níveis de proficiência). Cada resposta técnica é
  classificada em ambos os frameworks.
  Nota: Bloom/Dreyfus é framework aplicado na GERAÇÃO de perguntas WSI (Épico 4), não avaliação separada. Os scores aqui representam a classificação das respostas da triagem nos frameworks Bloom e Dreyfus.

Historia de Usuario: |
  Como recrutador, eu quero entender o nível de proficiência
  técnica real do candidato, não apenas o que ele declara saber,
  para tomar decisões mais precisas sobre adequação à vaga.

Regras de Negocio:
  1. Bloom: 6 níveis (Lembrar → Criar)
  2. Dreyfus: 5 níveis (Novice → Expert)
  3. Cada competência técnica recebe ambos os scores
  4. Penalidade por inflação: autodeclaração alta + Bloom baixo
  5. Score técnico = média ponderada Dreyfus × peso da competência
  6. Exibir gap entre declarado vs demonstrado
  7. Destacar competências com maior discrepância

Requisitos Tecnicos:
  Backend:
    - Serviço BloomDreyfusEvaluator integrado ao WSI
    - Mapeamento Bloom-Dreyfus (tabela de conversão)
  Frontend:
    - TechnicalSkillsBreakdown component
    - SkillGapIndicator component
  Dados:
    - skill_evaluations: id, wsi_score_id, skill_name, autodeclaration, bloom_level, dreyfus_level, context_score, gap, evidence
  Validacoes:
    - Bloom: 1-6 (inteiro)
    - Dreyfus: 1-5 (inteiro)
    - Gap calculado: autodeclaração - dreyfus_level

Integracoes Externas:
  Parte do fluxo SCO-001 (mesmo LLM)

Configuracao LLM:
  Extensão do prompt SCO-001 para incluir:
  
  Taxonomia Bloom (6 níveis):
    1. Lembrar: Recordar fatos básicos
    2. Compreender: Explicar conceitos
    3. Aplicar: Usar em situações práticas
    4. Analisar: Diferenciar e relacionar
    5. Avaliar: Julgar e justificar
    6. Criar: Gerar soluções novas
  
  Modelo Dreyfus (5 níveis):
    1. Novice: Segue regras rigidamente
    2. Advanced Beginner: Reconhece padrões simples
    3. Competent: Planeja e prioriza
    4. Proficient: Visão holística, adapta
    5. Expert: Intuição, transcende regras

Design & Componentes:
  Componentes Existentes:
    - Progress - barra de nível
    - Badge - indicador de gap
    - Table - lista de competências
  Novos Componentes:
    - SkillLevelBar - barra dupla (declarado vs demonstrado)
    - BloomDreyfusTooltip - explicação dos níveis
    - SkillGapAlert - alerta de discrepância
  Design Tokens:
    Declarado: --lia-text-tertiary (#6B7280)
    Demonstrado: --wedo-cyan (#60BED1)
    Gap Positivo: --wedo-green (#22C55E)
    Gap Negativo: --electric-red (#de1c31)
    Background: --lia-bg-primary (#FFFFFF)
  Layout:
    Container: max-w-3xl mx-auto
    Skill Row: flex, justify-between, items-center
    Bars: h-2, rounded-full, stacked
    Spacing: gap-3 entre skills
  Estados:
    - Loading (skeleton das barras)
    - Loaded (barras animadas)
    - Highlighted (skill com gap > 2)
  Acessibilidade:
    - ARIA-valuenow/valuemax nas barras
    - Texto alternativo para valores
    - Cores com padrões distintos

Comportamento de UI:
  Fluxo Principal:
    1. Análise WSI calcula Bloom/Dreyfus por skill
    2. Lista de competências renderiza com barras duplas
    3. Barra inferior: declaração do candidato (cinza)
    4. Barra superior: nível demonstrado (colorida)
    5. Gap indicator ao lado (positivo verde, negativo vermelho)
    6. Skills com gap > 2 destacadas com borda
  
  Visualização de Skill:
    Layout por Skill:
      - Nome da competência (esquerda)
      - Barras sobrepostas (centro)
      - Badge de gap (direita)
      - Expand para ver evidência (chevron)
    
    Barra Declarado:
      - Posição: abaixo
      - Cor: --lia-text-tertiary (50% opacity)
      - Label: "Declarado: 4/5"
    
    Barra Demonstrado:
      - Posição: acima
      - Cor: baseada no valor (verde=alto, vermelho=baixo)
      - Label: "Demonstrado: 3/5 (Bloom 4, Dreyfus 3)"
    
    Badge de Gap:
      - Positivo (demonstra mais): "+1" verde
      - Zero: "=" cinza
      - Negativo (infla): "-2" vermelho
  
  Interações:
    Hover em skill:
      - Tooltip com breakdown completo
      - Bloom level + descrição
      - Dreyfus level + descrição
    Click em skill:
      - Expande seção com evidências
      - Mostra citação da resposta do candidato
      - Botão "Ver resposta completa"
  
  Alertas:
    Gap >= 2 níveis:
      - Borda --electric-red no skill
      - Ícone warning ao lado
      - Tooltip: "Atenção: possível inflação de competência"

DoD:
  - [ ] Bloom 6 níveis implementados
  - [ ] Dreyfus 5 níveis implementados
  - [ ] Cálculo de gap funcionando
  - [ ] Visualização de barras duplas
  - [ ] Alertas de discrepância
  - [ ] Testes unitários passando

Criterios de Aceitacao:
  - [ ] Cada skill tem Bloom + Dreyfus
  - [ ] Gap calculado corretamente
  - [ ] Cores refletem níveis
  - [ ] Evidências acessíveis
  - [ ] Alerta para inflação (gap > 2)

Arquivos de Referencia (Prototipo Replit):
  - wsi_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_service.py
  - rubric_evaluation_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/rubric_evaluation_service.py
  - wsi_deterministic_scorer.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_deterministic_scorer.py
```

---

### CARD SCO-004: Parecer Textual LIA
**Épico:** É6 — Score WSI

```yaml
Titulo: [AI] Geração de Parecer Textual Estruturado
Tipo: Feature
Area: Full-Stack
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 8
Prioridade: Alta
Epic: EPIC-SCORE-WSI
Status: 📋 Pendente Jira
Dependencias: SCO-001, SCO-002, SCO-003

Descricao: |
  Gerar um parecer textual estruturado sobre o candidato,
  consolidando os scores WSI, Big Five e avaliação técnica
  em um resumo executivo legível pelo recrutador.

Historia de Usuario: |
  Como recrutador, eu quero ler um resumo objetivo sobre
  o candidato em vez de analisar múltiplos gráficos e números,
  para agilizar minha tomada de decisão.

Regras de Negocio:
  1. Parecer estruturado em seções: Resumo, Pontos Fortes, Atenção, Recomendação
  2. Máximo 500 palavras
  3. Tom profissional e objetivo
  4. Não incluir dados sensíveis (idade, gênero, etc)
  5. Baseado exclusivamente em evidências da triagem
  6. Incluir score final e recomendação (Aprovar/Revisar/Reprovar)
  7. Versão editável pelo recrutador (com registro de alteração)

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/wsi/report/generate
    - GET /api/v1/wsi/report/{candidate_id}
    - PUT /api/v1/wsi/report/{candidate_id} (edição)
    - WSIReportGeneratorService class
  Frontend:
    - CandidateReport component
    - ReportEditor (rich text básico)
  Dados:
    - wsi_reports: id, candidate_id, job_id, summary, strengths, concerns, recommendation, recommendation_reason, generated_at, edited_by, edited_at, original_text
  Validacoes:
    - Máximo 500 palavras
    - Recomendação: enum (approve, review, reject)
    - Se editado, manter original para auditoria

Integracoes Externas:
  LLM (Claude/Gemini):
    - Tipo: AI API
    - Uso: Geração do parecer estruturado
    - Serviço: wsi_report_generator_service.py
    - Secret: ANTHROPIC_API_KEY ou GEMINI_API_KEY
    - Custo: ~$0.01-0.02 por parecer

Configuracao LLM:
  Modelo Recomendado: Claude 3.5 Sonnet (melhor qualidade de texto)
  Temperatura: 0.4 (criativo mas consistente)
  Max Tokens: 1500
  
  Prompt Template: |
    <role>
    Você é um consultor de recrutamento sênior escrevendo um
    parecer executivo sobre um candidato para o recrutador.
    </role>
    
    <candidate_data>
    Nome: {{candidate_name}}
    Vaga: {{job_title}}
    Score WSI: {{wsi_score}}/5.0
    Perfil Big Five: {{big_five_summary}}
    Competências Técnicas: {{technical_breakdown}}
    Gaps Identificados: {{gaps}}
    </candidate_data>
    
    <output_format>
    ## Resumo Executivo
    [2-3 frases sobre o candidato e fit geral]
    
    ## Pontos Fortes
    - [Ponto 1]
    - [Ponto 2]
    - [Ponto 3]
    
    ## Pontos de Atenção
    - [Atenção 1]
    - [Atenção 2]
    
    ## Recomendação
    [APROVAR / REVISAR / NÃO APROVAR]
    [Justificativa em 1-2 frases]
    </output_format>
    
    <rules>
    - Máximo 500 palavras
    - Tom profissional e objetivo
    - Baseado apenas em evidências apresentadas
    - Não inferir informações não fornecidas
    </rules>

Design & Componentes:
  Componentes Existentes:
    - Card - container do parecer
    - Badge - recomendação
    - Button - editar, salvar
    - Textarea - edição
  Novos Componentes:
    - CandidateReport - visualização formatada do parecer
    - ReportEditor - editor inline com markdown básico
    - ReportRecommendationBadge - badge colorido da recomendação
  Design Tokens:
    Background: --lia-bg-primary (#FFFFFF)
    Border: --lia-border-subtle (#E5E7EB)
    Text: --lia-text-primary (#111827)
    Headings: --lia-text-secondary (#4B5563)
    Aprovar: --wedo-green (#22C55E)
    Revisar: --wedo-yellow (#EAB308)
    Reprovar: --electric-red (#de1c31)
  Layout:
    Container: max-w-2xl mx-auto
    Card: lia-card com lia-shadow-sm
    Sections: border-b entre seções
    Spacing: gap-6 entre seções
  Estados:
    - Generating (skeleton + spinner)
    - Viewing (texto formatado)
    - Editing (textarea ativa)
    - Edited (badge "Editado" + original disponível)
  Acessibilidade:
    - Headings semânticos (h2, h3)
    - Focus trap no editor
    - ARIA-live para status de salvamento

Comportamento de UI:
  Fluxo Principal:
    1. Score WSI calculado
    2. Botão "Gerar Parecer" disponível
    3. Click inicia geração (loading state)
    4. Parecer renderiza com formatação markdown
    5. Recomendação destacada no topo com badge colorido
    6. Botão "Editar" permite ajustes
    7. Salvamento mantém histórico
  
  Estados do Card:
    Generating:
      - Skeleton lines pulsando
      - Texto: "Gerando parecer..."
      - Spinner no canto
    Viewing:
      - Texto formatado com markdown
      - Badge de recomendação no topo
      - Botão "Editar" no canto
    Editing:
      - Textarea com conteúdo atual
      - Toolbar básica (bold, italic, bullet)
      - Botões "Salvar" e "Cancelar"
      - Preview lado a lado (desktop)
    Edited:
      - Badge "Editado por [Nome] em [Data]"
      - Link "Ver original" para comparar
  
  Interações:
    Editar:
      - Click ativa modo edição
      - Textarea recebe focus
      - ESC cancela edição
    Salvar:
      - Valida tamanho (max 500 palavras)
      - Salva com registro de quem editou
      - Toast de confirmação
    Ver Original:
      - Modal com texto original lado a lado
      - Diff highlighting (opcional)
  
  Mensagens de Feedback:
    - Gerando: Toast azul "Gerando parecer..."
    - Sucesso: Toast verde "Parecer gerado com sucesso"
    - Salvo: Toast verde "Alterações salvas"
    - Erro: Toast vermelho "Erro ao gerar parecer"
    - Warning: Toast amarelo "Parecer excede 500 palavras"

DoD:
  - [ ] Geração de parecer funciona
  - [ ] Formato estruturado (Resumo, Fortes, Atenção, Recomendação)
  - [ ] Edição inline funciona
  - [ ] Histórico de edições
  - [ ] Limite de 500 palavras
  - [ ] Testes unitários passando

Criterios de Aceitacao:
  - [ ] Parecer gerado automaticamente
  - [ ] Recomendação com badge colorido
  - [ ] Edição salva com autoria
  - [ ] Original preservado
  - [ ] PDF exportável (opcional)

Arquivos de Referencia (Prototipo Replit):
  - candidate_report_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/candidate_report_service.py
  - explainability_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/explainability_service.py
  - wsi_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_service.py
```

---

### CARD SCO-005: Visualização de Score
**Épico:** É6 — Score WSI

```yaml
Titulo: [FRONTEND] Dashboard de Visualização de Score WSI
Tipo: Feature
Area: Full-Stack
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 8
Prioridade: Alta
Epic: EPIC-SCORE-WSI
Status: 📋 Pendente Jira
Dependencias: SCO-001, SCO-002, SCO-003

Descricao: |
  Implementar dashboard visual completo para exibição do Score WSI
  do candidato, incluindo gráfico radar de competências, barras
  de progresso por dimensão, e indicadores visuais de fit.

Historia de Usuario: |
  Como recrutador, eu quero visualizar o score do candidato de
  forma clara e intuitiva, com gráficos que me permitam entender
  rapidamente seus pontos fortes e fracos.

Regras de Negocio:
  1. Score geral em destaque (gauge ou número grande)
  2. Radar chart com todas as competências
  3. Barras de progresso por categoria (Técnico, Comportamental)
  4. Código de cores consistente (verde=alto, vermelho=baixo)
  5. Comparação com média da vaga (se disponível)
  6. Responsivo para mobile
  7. Exportável para PDF/imagem

Requisitos Tecnicos:
  Frontend:
    - WSIScoreDashboard component
    - Recharts para gráficos (radar, bar, gauge)
    - React-to-print para exportação
  Backend:
    - GET /api/v1/wsi/score/{candidate_id}/dashboard
    - Inclui dados de comparação com média da vaga
  Dados:
    - Agregação de wsi_scores, big_five_profiles, skill_evaluations

Design & Componentes:
  Componentes Existentes:
    - Card - containers
    - Badge - indicadores
    - Skeleton - loading
    - Tabs - navegação entre views
  Novos Componentes:
    - WSIScoreDashboard - container principal
    - WSIGaugeChart - gauge semicircular do score geral
    - WSIRadarChart - radar de competências (recharts)
    - WSIProgressBars - barras de progresso por categoria
    - WSIComparisonOverlay - comparação com média
    - WSIExportButton - exportação PDF/PNG
  Design Tokens:
    Background Primary: --lia-bg-primary (#FFFFFF)
    Background Secondary: --lia-bg-secondary (#F9FAFB)
    Border: --lia-border-subtle (#E5E7EB)
    Text Primary: --lia-text-primary (#111827)
    Score Excellent: --wedo-green (#22C55E)
    Score High: --wedo-cyan (#60BED1)
    Score Medium: --wedo-yellow (#EAB308)
    Score Low: --wedo-orange (#F97316)
    Score Critical: --electric-red (#de1c31)
  Layout:
    Container: max-w-4xl mx-auto
    Grid: 2 colunas desktop (gauge + radar), 1 coluna mobile
    Cards: lia-card com lia-shadow-sm
    Gauge: aspect-[2/1], centralizado
    Radar: aspect-square, max-w-md
    Progress Bars: full-width, h-3
    Spacing: gap-6 entre cards
  Estados:
    - Loading (skeletons)
    - Loaded (gráficos animados)
    - Comparing (overlay de média)
    - Exporting (loading no botão)
  Acessibilidade:
    - Tabela alternativa para screen readers
    - ARIA-labels em todos os gráficos
    - Cores com padrões distintos
    - Keyboard navigation entre elementos

Comportamento de UI:
  Fluxo Principal:
    1. Usuário abre perfil do candidato
    2. Tab "Score WSI" selecionada
    3. Dashboard carrega com skeleton
    4. Gauge anima de 0 ao score (1s)
    5. Radar anima do centro para fora (1.5s)
    6. Barras de progresso animam (0.5s)
    7. Hover em elementos mostra tooltips
  
  Layout do Dashboard:
    Header:
      - Nome do candidato
      - Vaga
      - Data da triagem
      - Botão "Exportar"
    
    Row 1 (2 colunas):
      - Coluna 1: Gauge Chart (score geral)
      - Coluna 2: Radar Chart (competências)
    
    Row 2 (full-width):
      - Card: Competências Técnicas (barras)
      - Card: Competências Comportamentais (barras)
    
    Row 3 (full-width):
      - Card: Big Five Profile (mini radar)
      - Card: Parecer LIA (preview)
  
  Interações:
    Gauge Chart:
      - Animação de preenchimento ao carregar
      - Tooltip: "Score WSI: 4.2/5.0 - Alto"
      - Cor do arco baseada no score
    
    Radar Chart:
      - Hover em ponto: tooltip com nome + score
      - Click em ponto: expande detalhes da competência
      - Toggle: "Mostrar média da vaga"
    
    Progress Bars:
      - Animação de preenchimento
      - Hover: tooltip com valor numérico
      - Label esquerda: nome da skill
      - Label direita: score/5.0
    
    Comparação:
      - Toggle switch: "Comparar com média"
      - Ativo: linha tracejada no radar + barra secundária
      - Legenda: "Candidato" vs "Média da vaga"
  
  Exportação:
    Click em "Exportar":
      - Dropdown: PDF, PNG, Compartilhar
      - PDF: gera documento com todos os gráficos
      - PNG: screenshot da área visível
      - Compartilhar: copia link (se permitido)
  
  Mensagens de Feedback:
    - Loading: Skeletons animados
    - Erro: Toast vermelho "Erro ao carregar score"
    - Export sucesso: Toast verde "PDF gerado com sucesso"
    - Export erro: Toast vermelho "Erro na exportação"


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Gauge chart funcional
  - [ ] Radar chart funcional
  - [ ] Progress bars funcionais
  - [ ] Comparação com média
  - [ ] Exportação PDF/PNG
  - [ ] Responsivo mobile
  - [ ] Testes E2E passando

Criterios de Aceitacao:
  - [ ] Score geral visível em destaque
  - [ ] Radar mostra todas as competências
  - [ ] Cores refletem níveis corretamente
  - [ ] Tooltips informativos
  - [ ] Export funciona

Arquivos de Referencia (Prototipo Replit):
  - WSIQualityBar.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/expanded-chat/components/WSIQualityBar.tsx
  - search-results-card.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/search-results-card.tsx
  - wsi_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_service.py
```

---

### CARD SCO-006: Breakdown de Dimensões
**Épico:** É6 — Score WSI

```yaml
Titulo: [FRONTEND] Detalhamento por Dimensão de Competência
Tipo: Feature
Area: Full-Stack
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 5
Prioridade: Média
Epic: EPIC-SCORE-WSI
Status: 📋 Pendente Jira
Dependencias: SCO-001, SCO-003

Descricao: |
  Implementar visualização detalhada de cada dimensão do score WSI,
  permitindo ao recrutador entender exatamente como cada competência
  foi avaliada, com evidências e justificativas.

Historia de Usuario: |
  Como recrutador, eu quero ver o detalhamento de cada competência
  avaliada, incluindo as evidências extraídas das respostas do
  candidato, para validar a avaliação da LIA.

Regras de Negocio:
  1. Cada dimensão expandível em accordion
  2. Mostrar: pergunta, resposta resumida, score, evidência
  3. Níveis Bloom e Dreyfus visíveis
  4. Link para resposta completa
  5. Opção de ajustar score manualmente (com registro)
  6. Ordenar por relevância ou por score

Requisitos Tecnicos:
  Frontend:
    - DimensionBreakdown component
    - Accordion com expand/collapse
    - SkillDetailCard component
  Backend:
    - GET /api/v1/wsi/dimensions/{candidate_id}
    - PUT /api/v1/wsi/dimensions/{dimension_id}/override
  Dados:
    - Leitura de skill_evaluations
    - wsi_overrides: id, dimension_id, original_score, new_score, reason, changed_by, changed_at

Design & Componentes:
  Componentes Existentes:
    - Accordion - expandir/colapsar (@radix-ui/react-accordion)
    - Badge - níveis Bloom/Dreyfus
    - Button - ações
    - Input - override de score
  Novos Componentes:
    - DimensionBreakdown - container principal
    - SkillDetailCard - card expandível por skill
    - ScoreOverrideModal - modal para ajuste manual
    - EvidenceQuote - citação formatada da resposta
  Design Tokens:
    Background: --lia-bg-primary (#FFFFFF)
    Background Expanded: --lia-bg-secondary (#F9FAFB)
    Border: --lia-border-subtle (#E5E7EB)
    Text Primary: --lia-text-primary (#111827)
    Text Secondary: --lia-text-secondary (#4B5563)
    Accent: --wedo-cyan (#60BED1)
    Override: --wedo-purple (#9860D1)
  Layout:
    Container: max-w-3xl mx-auto
    Accordion: full-width, border-b entre items
    Expanded Content: p-4, bg-secondary
    Evidence Quote: border-l-4, pl-4, italic
    Spacing: gap-2 entre elementos
  Estados:
    - Collapsed (header apenas)
    - Expanded (conteúdo completo)
    - Overridden (badge "Ajustado")
    - Editing (modal de override)
  Acessibilidade:
    - Accordion com ARIA-expanded
    - Focus management na expansão
    - Keyboard navigation (Enter para toggle)

Comportamento de UI:
  Fluxo Principal:
    1. Lista de dimensões renderiza em accordion
    2. Cada item mostra: nome, score badge, chevron
    3. Click expande com detalhes completos
    4. Detalhes incluem pergunta, resposta, análise
    5. Botão "Ajustar Score" abre modal
    6. Ajuste salvo com justificativa obrigatória
  
  Layout do Accordion Item:
    Header (collapsed):
      - Ícone da categoria (esquerda)
      - Nome da competência
      - Badges: Bloom 4, Dreyfus 3
      - Score badge (direita)
      - Chevron indicando estado
    
    Content (expanded):
      - Pergunta feita ao candidato
      - Resposta resumida (primeiras 200 chars)
      - "Ver resposta completa" link
      - Análise LIA (justificativa do score)
      - Evidências destacadas como quotes
      - Botão "Ajustar Score"
  
  Override de Score:
    Modal:
      - Título: "Ajustar Score de [Competência]"
      - Score atual: badge
      - Input: novo score (1-5, step 0.5)
      - Textarea: justificativa (obrigatório)
      - Botões: "Cancelar", "Salvar Ajuste"
    
    Após Salvar:
      - Badge "Ajustado" aparece no header
      - Tooltip mostra: "Original: 3.0 → Ajustado: 4.0 por [Nome]"
      - Registro para auditoria
  
  Ordenação:
    Toggle/Dropdown:
      - "Por Relevância" (peso da skill)
      - "Por Score (maior → menor)"
      - "Por Score (menor → maior)"
      - "Por Gap" (maior discrepância primeiro)
  
  Mensagens de Feedback:
    - Override salvo: Toast verde "Score ajustado com sucesso"
    - Erro: Toast vermelho "Erro ao salvar ajuste"
    - Justificativa vazia: Validação inline "Justificativa obrigatória"


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Accordion funcional
  - [ ] Detalhes por dimensão
  - [ ] Override com justificativa
  - [ ] Ordenação funcionando
  - [ ] Auditoria de overrides
  - [ ] Testes E2E passando

Criterios de Aceitacao:
  - [ ] Expandir/colapsar funciona
  - [ ] Evidências visíveis
  - [ ] Override registra autor
  - [ ] Badge "Ajustado" aparece
  - [ ] Ordenação altera lista

Arquivos de Referencia (Prototipo Replit):
  - wsi_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_service.py
  - wsi_deterministic_scorer.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_deterministic_scorer.py
  - explainability_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/explainability_service.py
```

---

### CARD SCO-007: Comparação entre Candidatos
**Épico:** É6 — Score WSI

```yaml
Titulo: [FULL-STACK] Comparativo de Candidatos Side-by-Side
Tipo: Feature
Area: Full-Stack
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 13
Prioridade: Alta
Epic: EPIC-SCORE-WSI
Status: 📋 Pendente Jira
Dependencias: SCO-001, SCO-002, SCO-005

Descricao: |
  Implementar funcionalidade de comparação lado a lado entre
  2 a 4 candidatos da mesma vaga, mostrando scores, competências
  e perfis comportamentais em visualização comparativa.

Historia de Usuario: |
  Como recrutador, eu quero comparar candidatos finalistas
  lado a lado para tomar uma decisão mais informada sobre
  qual candidato avançar para entrevista.

Regras de Negocio:
  1. Comparar 2 a 4 candidatos simultaneamente
  2. Mesma vaga obrigatório
  3. Destacar vencedor em cada dimensão
  4. Radar chart sobreposto ou lado a lado
  5. Tabela comparativa de métricas
  6. Exportar comparativo em PDF
  7. Salvar comparativo para revisão futura

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/wsi/compare
    - GET /api/v1/wsi/comparisons/{comparison_id}
    - Body: { candidate_ids: string[], job_id: string }
  Frontend:
    - CandidateComparison component
    - ComparisonRadarOverlay (radares sobrepostos)
    - ComparisonTable (métricas lado a lado)
  Dados:
    - wsi_comparisons: id, job_id, candidate_ids (JSONB), created_by, created_at, notes

Design & Componentes:
  Componentes Existentes:
    - Card - containers
    - Table - comparativo
    - Checkbox - seleção de candidatos
    - Button - ações
  Novos Componentes:
    - CandidateComparisonView - container principal
    - CandidateSelector - multi-select de candidatos
    - ComparisonRadarOverlay - radar com múltiplos polígonos
    - ComparisonMetricsTable - tabela comparativa
    - WinnerHighlight - destaque do vencedor por dimensão
  Design Tokens:
    Candidato 1: --wedo-cyan (#60BED1)
    Candidato 2: --wedo-purple (#9860D1)
    Candidato 3: --wedo-green (#22C55E)
    Candidato 4: --wedo-orange (#F97316)
    Winner: --wedo-green com glow
    Background: --lia-bg-primary (#FFFFFF)
    Border: --lia-border-subtle (#E5E7EB)
  Layout:
    Container: max-w-6xl mx-auto
    Columns: flex, 2-4 colunas iguais
    Radar: full-width, aspect-square
    Table: full-width com scroll horizontal mobile
    Spacing: gap-4 entre colunas
  Estados:
    - Selecting (escolhendo candidatos)
    - Comparing (visualização comparativa)
    - Exporting (gerando PDF)
  Acessibilidade:
    - Tabela com headers apropriados
    - Cores com padrões distintos
    - Screen reader: leitura em ordem lógica

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador está na lista de candidatos da vaga
    2. Seleciona 2-4 candidatos via checkbox
    3. Botão "Comparar Selecionados" aparece
    4. Click abre view de comparação
    5. Radar sobreposto mostra perfis
    6. Tabela mostra métricas lado a lado
    7. Vencedor destacado em cada linha
  
  Seleção de Candidatos:
    Na Lista:
      - Checkbox em cada card de candidato
      - Counter: "2 selecionados"
      - Botão fixo inferior: "Comparar (2)"
      - Máximo 4 selecionados
    
    Se > 4 selecionados:
      - Tooltip: "Máximo 4 candidatos"
      - Checkbox adicional desabilitado
  
  View de Comparação:
    Header:
      - Título: "Comparando Candidatos - [Vaga]"
      - Botão "Voltar"
      - Botão "Exportar PDF"
    
    Seção 1 - Perfis:
      - 2-4 cards lado a lado
      - Foto, nome, score geral
      - Badge de classificação (1º, 2º, etc.)
    
    Seção 2 - Radar Overlay:
      - Um radar com 2-4 polígonos
      - Cores distintas por candidato
      - Legenda abaixo
      - Toggle: "Separar radares"
    
    Seção 3 - Tabela Comparativa:
      - Coluna 1: Dimensão
      - Colunas 2-5: Candidatos
      - Célula com maior valor: destaque verde
      - Hover em célula: tooltip com detalhes
    
    Seção 4 - Parecer Comparativo:
      - Texto gerado por LLM comparando candidatos
      - "Recomendação: [Candidato] é mais indicado porque..."
  
  Interações:
    Radar Overlay:
      - Hover em área: destaca candidato
      - Click em ponto: mostra detalhe da competência
      - Toggle "Separar": muda para radares individuais
    
    Tabela:
      - Hover em linha: destaca em todos
      - Sort por coluna: clicável
      - Winner cell: glow animation
    
    Exportar:
      - Click: loading state
      - Gera PDF com todos os dados
      - Download automático
  
  Mensagens de Feedback:
    - Mínimo 2: Toast amarelo "Selecione ao menos 2 candidatos"
    - Máximo 4: Toast amarelo "Máximo 4 candidatos para comparação"
    - Export sucesso: Toast verde "PDF gerado com sucesso"
    - Salvo: Toast verde "Comparativo salvo"


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Seleção múltipla funciona
  - [ ] Radar overlay funcional
  - [ ] Tabela comparativa
  - [ ] Destaque de vencedores
  - [ ] Exportação PDF
  - [ ] Salvamento de comparativo
  - [ ] Testes E2E passando

Criterios de Aceitacao:
  - [ ] Comparar 2-4 candidatos
  - [ ] Radar mostra todos
  - [ ] Tabela destaca vencedores
  - [ ] PDF exporta corretamente
  - [ ] Comparativo pode ser salvo

Arquivos de Referencia (Prototipo Replit):
  - candidate-comparison.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/candidate-comparison.tsx
  - candidate_comparison_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/candidate_comparison_service.py
  - lia_score_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/lia_score_service.py
```

---

### CARD SCO-008: Histórico de Scores
**Épico:** É6 — Score WSI

```yaml
Titulo: [BACKEND] Histórico e Versionamento de Scores WSI
Tipo: Feature
Area: Full-Stack
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 5
Prioridade: Média
Epic: EPIC-SCORE-WSI
Status: 📋 Pendente Jira
Dependencias: SCO-001

Descricao: |
  Implementar sistema de histórico de scores WSI por candidato,
  permitindo visualizar evolução ao longo de múltiplas triagens
  e processos seletivos diferentes.

Historia de Usuario: |
  Como recrutador, eu quero ver o histórico de scores de um
  candidato recorrente para entender sua evolução ao longo do
  tempo e em diferentes vagas.

Regras de Negocio:
  1. Armazenar todas as versões de score por candidato
  2. Diferenciar por vaga e data
  3. Mostrar evolução temporal (gráfico de linha)
  4. Comparar scores de vagas diferentes
  5. Destacar melhorias e regressões
  6. Reter por 2 anos (LGPD)
  7. Anonimizar após período de retenção

Requisitos Tecnicos:
  Backend:
    - GET /api/v1/wsi/history/{candidate_id}
    - Query params: ?start_date, ?end_date, ?job_ids
    - WSIHistoryService class
  Frontend:
    - ScoreHistoryChart (linha temporal)
    - ScoreHistoryTable (lista de triagens)
  Dados:
    - wsi_scores já tem created_at e job_id
    - Índice: (candidate_id, created_at DESC)

Design & Componentes:
  Componentes Existentes:
    - Card - container
    - Table - lista de histórico
    - Badge - indicadores de variação
  Novos Componentes:
    - ScoreHistoryChart - gráfico de linha temporal (recharts)
    - ScoreHistoryTable - tabela com todas as triagens
    - ScoreVariationBadge - badge de variação (+0.5, -0.3)
  Design Tokens:
    Background: --lia-bg-primary (#FFFFFF)
    Border: --lia-border-subtle (#E5E7EB)
    Line Color: --wedo-cyan (#60BED1)
    Improvement: --wedo-green (#22C55E)
    Regression: --electric-red (#de1c31)
    Neutral: --lia-text-tertiary (#6B7280)
  Layout:
    Container: max-w-3xl mx-auto
    Chart: full-width, h-64
    Table: full-width, striped
    Spacing: gap-6 entre seções
  Estados:
    - Loading (skeleton)
    - Empty (nenhum histórico)
    - Loaded (gráfico + tabela)
    - Filtered (por período/vaga)
  Acessibilidade:
    - Tabela com dados tabulares acessíveis
    - Gráfico com descrição textual
    - Filtros com labels

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador abre perfil do candidato
    2. Tab "Histórico WSI" mostra evolução
    3. Gráfico de linha mostra scores ao longo do tempo
    4. Cada ponto é uma triagem (hover mostra detalhes)
    5. Tabela abaixo lista todas as triagens
    6. Filtros permitem refinar por período ou vaga
  
  Layout do Histórico:
    Header:
      - Título: "Histórico de Avaliações"
      - Filtros: DateRange, MultiSelect de Vagas
      - Botão: "Exportar"
    
    Chart Section:
      - Eixo X: Data
      - Eixo Y: Score (0-5)
      - Linha: evolução do score
      - Pontos: cada triagem
      - Área: preenchida para tendência
    
    Table Section:
      - Colunas: Data, Vaga, Score, Variação, Ações
      - Variação: badge verde (+) ou vermelho (-)
      - Ação: "Ver detalhes" → abre modal com breakdown
  
  Interações:
    Chart:
      - Hover em ponto: tooltip com data, vaga, score
      - Click em ponto: scroll para linha na tabela
      - Zoom: seleção de área para zoom in
    
    Table:
      - Sort por coluna (data, score)
      - Click em linha: expande com resumo
      - "Ver detalhes": modal com breakdown completo
    
    Filtros:
      - DateRange: seleciona período
      - Vagas: multi-select de vagas
      - "Limpar filtros": reset
  
  Estados Especiais:
    Sem Histórico:
      - Ilustração vazia
      - Texto: "Primeira avaliação deste candidato"
      - Sem gráfico, apenas info da triagem atual
    
    Tendência Positiva:
      - Linha gráfico com gradient verde
      - Badge geral: "Evolução positiva"
    
    Tendência Negativa:
      - Linha gráfico com gradient vermelho
      - Badge geral: "Atenção: regressão identificada"
  
  Mensagens de Feedback:
    - Loading: Skeleton chart + table
    - Erro: Toast vermelho "Erro ao carregar histórico"
    - Sem dados: Estado empty state
    - Export: Toast verde "Histórico exportado"

DoD:
  - [ ] Histórico armazenado por triagem
  - [ ] Gráfico de evolução temporal
  - [ ] Tabela de triagens
  - [ ] Filtros por período/vaga
  - [ ] Variação calculada corretamente
  - [ ] Testes unitários passando

Criterios de Aceitacao:
  - [ ] Múltiplas triagens listadas
  - [ ] Gráfico mostra evolução
  - [ ] Variação entre triagens calculada
  - [ ] Filtros funcionam
  - [ ] Exportação funciona

Arquivos de Referencia (Prototipo Replit):
  - wsi_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_service.py
  - candidate-page.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/candidate-page.tsx
  - activity_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/activity_service.py
```

---

## ÉPICO 7: GATES DE APROVAÇÃO

---

### CARD GAT-001: Gate 1 - Aprovar Mapeados
**Épico:** É7 — Gates de Aprovação

```yaml
Titulo: [FULL-STACK] Gate 1: Aprovação de Candidatos Mapeados
Tipo: Feature
Area: Full-Stack
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 8
Prioridade: Crítica
Epic: EPIC-GATES
Status: 📋 Pendente Jira

Descricao: |
  Implementar o primeiro portão de aprovação do fluxo MVP.
  Após o mapeamento de candidatos, o recrutador deve aprovar
  quais candidatos a LIA pode contatar para triagem via WhatsApp.

Historia de Usuario: |
  Como recrutador, eu quero revisar e aprovar os candidatos
  mapeados antes da LIA iniciar contato, para garantir que
  apenas perfis relevantes entrem no processo de triagem.

Regras de Negocio:
  1. Candidatos mapeados ficam em estado "pendente_aprovacao_g1"
  2. Recrutador pode aprovar ou reprovar individualmente
  3. Aprovados movem para "aprovado_para_triagem"
  4. Reprovados movem para "reprovado_g1" + recebem feedback
  5. Notificação ao recrutador quando há pendentes
  6. Timeout de 48h gera lembrete
  7. Ação em massa disponível (aprovar/reprovar selecionados)

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/gates/g1/approve
    - POST /api/v1/gates/g1/reject
    - Body: { candidate_ids: string[], job_id: string, notes?: string }
    - GateApprovalService class
  Frontend:
    - GateApprovalPanel component
    - ApprovalActionBar (ações em massa)
    - CandidateApprovalCard
  Dados:
    - gate_decisions: id, gate_type (g1/g2), candidate_id, job_id, decision (approved/rejected), decided_by, decided_at, notes
    - candidate_job_status: trigger para atualizar status

Design & Componentes:
  Componentes Existentes:
    - Card - container de candidato
    - Button - aprovar, reprovar
    - Checkbox - seleção múltipla
    - Badge - status
    - Toast - feedback
  Novos Componentes:
    - GateApprovalPanel - painel de aprovação
    - ApprovalActionBar - barra de ações em massa flutuante
    - CandidateApprovalCard - card com ações de gate
    - ApprovalConfirmModal - confirmação de ação em massa
  Design Tokens:
    Background: --lia-bg-primary (#FFFFFF)
    Border: --lia-border-subtle (#E5E7EB)
    Approve: --wedo-green (#22C55E)
    Reject: --electric-red (#de1c31)
    Pending: --wedo-yellow (#EAB308)
    Accent: --wedo-cyan (#60BED1)
  Layout:
    Container: max-w-4xl mx-auto
    Grid: 2 colunas desktop, 1 mobile
    Action Bar: fixed bottom, full-width
    Cards: lia-card com border-l-4 por status
    Spacing: gap-4 entre cards
  Estados:
    - Pending (borda amarela)
    - Selected (checkbox marcado)
    - Approved (borda verde, fade out)
    - Rejected (borda vermelha, fade out)
  Acessibilidade:
    - Focus management nas ações
    - ARIA-live para status changes
    - Keyboard shortcuts (A=aprovar, R=reprovar)

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador acessa Kanban da vaga
    2. Coluna "Mapeados" mostra candidatos pendentes
    3. Badge indica "X pendentes de aprovação"
    4. Click em candidato expande card com detalhes
    5. Botões "Aprovar" e "Reprovar" no card
    6. Ação move candidato com animação
    7. Notificação de sucesso
  
  Layout do Card de Aprovação:
    Header:
      - Foto, Nome do candidato
      - Match Score (se disponível)
      - Checkbox (para seleção múltipla)
    
    Body:
      - Resumo do perfil (cargo atual, empresa)
      - Principais skills
      - Fonte (base interna, LinkedIn, etc.)
    
    Footer:
      - Botão "Aprovar" (verde, ícone check)
      - Botão "Reprovar" (vermelho outline, ícone X)
      - Botão "Ver Perfil" (link)
  
  Barra de Ações em Massa:
    Aparece quando >= 1 selecionado:
      - Contador: "X selecionados"
      - Botão "Aprovar Todos" (verde)
      - Botão "Reprovar Todos" (vermelho outline)
      - Botão "Limpar Seleção" (X)
    
    Posição: fixed bottom, above footer
    Animação: slide up quando aparece
  
  Interações:
    Aprovar Individual:
      - Click no botão verde
      - Card anima (fade + border verde)
      - Move para próxima coluna
      - Toast: "Candidato aprovado para triagem"
    
    Reprovar Individual:
      - Click no botão vermelho
      - Abre modal de reprovação (GAT-003)
      - Após confirmar: card anima (fade + border vermelha)
      - Toast: "Candidato reprovado"
    
    Aprovar em Massa:
      - Click em "Aprovar Todos"
      - Modal de confirmação: "Aprovar X candidatos?"
      - Confirma: todos movem simultaneamente
      - Toast: "X candidatos aprovados para triagem"
  
  Notificações:
    Pendentes > 0:
      - Badge no menu da vaga
      - Notificação push (se habilitado)
      - Email após 24h sem ação
    
    Timeout 48h:
      - Email: "Você tem X candidatos aguardando aprovação"
      - In-app: banner amarelo no topo do Kanban
  
  Mensagens de Feedback:
    - Sucesso: Toast verde "Candidato aprovado para triagem"
    - Sucesso massa: Toast verde "X candidatos aprovados"
    - Reprovado: Toast laranja "Candidato reprovado - feedback será enviado"
    - Erro: Toast vermelho "Erro ao processar aprovação"


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Aprovar individual funciona
  - [ ] Reprovar individual abre modal
  - [ ] Seleção múltipla funciona
  - [ ] Ação em massa funciona
  - [ ] Status atualiza corretamente
  - [ ] Notificações configuradas
  - [ ] Testes E2E passando

Criterios de Aceitacao:
  - [ ] Aprovar move para triagem
  - [ ] Reprovar abre modal de motivo
  - [ ] Ação em massa processa todos
  - [ ] Decisões registradas no histórico
  - [ ] Notificação após 24h sem ação

Arquivos de Referencia (Prototipo Replit):
  - pipeline_stage_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/pipeline_stage_service.py
  - stage_automation_engine.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/stage_automation_engine.py
  - stage_transition_automation.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/stage_transition_automation.py
  - stage_transition_automation.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/stage_transition_automation.py
```

---

### CARD GAT-002: Gate 2 - Aprovar Triados
**Épico:** É7 — Gates de Aprovação

```yaml
Titulo: [FULL-STACK] Gate 2: Aprovação de Candidatos Triados
Tipo: Feature
Area: Full-Stack
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 8
Prioridade: Crítica
Epic: EPIC-GATES
Status: 📋 Pendente Jira
Dependencias: GAT-001, SCO-001

Descricao: |
  Implementar o segundo portão de aprovação do fluxo MVP.
  Após a triagem WSI, o recrutador revisa o score e parecer
  da LIA para decidir se avança ou reprova o candidato.

Historia de Usuario: |
  Como recrutador, eu quero avaliar os resultados da triagem
  WSI para decidir quais candidatos avançam para entrevista
  e quais são reprovados com feedback.

Regras de Negocio:
  1. Candidatos triados ficam em estado "pendente_aprovacao_g2"
  2. Score WSI e parecer LIA visíveis para decisão
  3. Aprovados movem para "short_list" → LIA agenda entrevista
  4. Reprovados movem para "reprovado_g2" + recebem feedback
  5. Threshold sugerido: WSI >= 4.0 = sugerir aprovar
  6. WSI < 3.0 = sugerir reprovar (com override possível)
  7. Ação em massa disponível

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/gates/g2/approve
    - POST /api/v1/gates/g2/reject
    - Body: { candidate_ids: string[], job_id: string, notes?: string }
  Frontend:
    - Gate2ApprovalPanel component
    - TriagedCandidateCard (com score WSI)
    - ApprovalSuggestionBadge
  Dados:
    - gate_decisions: reutiliza com gate_type = 'g2'
    - Trigger: aprovado G2 → dispara agendamento

Design & Componentes:
  Componentes Existentes:
    - Todos de GAT-001
    - WSIScoreBadge de SCO-001
    - CandidateReport de SCO-004
  Novos Componentes:
    - Gate2ApprovalPanel - painel específico G2
    - TriagedCandidateCard - card com score WSI
    - ApprovalSuggestionBadge - "Sugerir Aprovar" / "Revisar"
    - ScoreBasedSortToggle - ordenar por score
  Design Tokens:
    (Mesmos de GAT-001)
    Suggest Approve: --wedo-green-light (#D1FAE5)
    Suggest Review: --wedo-yellow-light (#FEF3C7)
    Suggest Reject: --electric-red-light (#FEE2E2)
  Layout:
    (Similar a GAT-001)
    Score Badge: posição de destaque no card
    Parecer Preview: seção expandível
  Estados:
    (Mesmos de GAT-001 + sugestões)
    - Suggest Approve (borda verde tracejada)
    - Suggest Review (borda amarela tracejada)
    - Suggest Reject (borda vermelha tracejada)
  Acessibilidade:
    (Mesmos de GAT-001)

Comportamento de UI:
  Fluxo Principal:
    1. Candidato completa triagem WSI
    2. Recrutador recebe notificação
    3. Acessa coluna "Triados" no Kanban
    4. Cards mostram score WSI em destaque
    5. Badge de sugestão baseado no score
    6. Click expande com parecer LIA
    7. Aprovar → move para Short List + dispara agendamento
    8. Reprovar → abre modal + envia feedback
  
  Layout do Card Triado:
    Header:
      - Foto, Nome
      - Score WSI Badge (grande, colorido)
      - Sugestão Badge ("Aprovar" / "Revisar" / "Atenção")
      - Checkbox
    
    Body:
      - Preview do parecer (primeiras 2 linhas)
      - Big Five mini-icons (5 círculos)
      - "Ver análise completa" link
    
    Footer:
      - Botão "Aprovar para Entrevista" (verde)
      - Botão "Reprovar" (vermelho outline)
      - Botão "Ver Detalhes" (link)
  
  Sugestões Baseadas em Score:
    WSI >= 4.0:
      - Badge: "Sugerir Aprovar" (verde)
      - Card border: verde tracejada
      - Botão aprovar em destaque
    
    WSI 3.0-3.9:
      - Badge: "Revisar" (amarelo)
      - Card border: amarela tracejada
      - Ambos botões neutros
    
    WSI < 3.0:
      - Badge: "Atenção" (vermelho)
      - Card border: vermelha tracejada
      - Alerta: "Score abaixo do threshold"
  
  Ordenação:
    Default: Por score (maior primeiro)
    Opções:
      - Por score (maior → menor)
      - Por score (menor → maior)
      - Por data de triagem
      - Por sugestão
  
  Interações:
    Aprovar:
      - Click no botão verde
      - Confirmação se score < 3.0: "Candidato com score baixo. Deseja aprovar mesmo assim?"
      - Aprovado: move para Short List
      - Dispara: GAT-004 (não) + agendamento
    
    Reprovar:
      - Click no botão vermelho
      - Abre modal GAT-003
      - Após confirmar: move para Reprovados
      - Dispara: GAT-004 + GAT-005
  
  Mensagens de Feedback:
    - Aprovado: Toast verde "Candidato aprovado! LIA iniciará agendamento."
    - Reprovado: Toast laranja "Candidato reprovado. Feedback será enviado."
    - Warning override: Modal "Score abaixo do recomendado. Confirma aprovação?"


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Aprovação G2 funciona
  - [ ] Score WSI visível
  - [ ] Sugestões baseadas em score
  - [ ] Aprovado dispara agendamento
  - [ ] Reprovado dispara feedback
  - [ ] Ação em massa funciona
  - [ ] Testes E2E passando

Criterios de Aceitacao:
  - [ ] Score WSI exibido no card
  - [ ] Sugestões corretas por faixa
  - [ ] Aprovar move para Short List
  - [ ] Reprovar abre modal
  - [ ] Override com confirmação

Arquivos de Referencia (Prototipo Replit):
  - pipeline_stage_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/pipeline_stage_service.py
  - stage_automation_engine.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/stage_automation_engine.py
  - stage_transition_automation.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/stage_transition_automation.py
```

---

### CARD GAT-003: Modal de Reprovação
**Épico:** É7 — Gates de Aprovação

```yaml
Titulo: [FRONTEND] Modal de Reprovação com Motivo
Tipo: Feature
Area: Full-Stack
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 5
Prioridade: Alta
Epic: EPIC-GATES
Status: 📋 Pendente Jira
Dependencias: GAT-001

Descricao: |
  Implementar modal de reprovação que captura o motivo da
  decisão e permite personalizar a mensagem de feedback
  que será enviada ao candidato.

Historia de Usuario: |
  Como recrutador, eu quero registrar o motivo da reprovação
  e personalizar o feedback para o candidato, garantindo uma
  experiência respeitosa mesmo em caso negativo.

Regras de Negocio:
  1. Motivo de reprovação obrigatório (select predefinido)
  2. Comentário interno opcional (não enviado ao candidato)
  3. Preview do feedback que será enviado
  4. Motivo de reprovação obrigatório com categorias predefinidas
  5. Registro para auditoria e calibração
  6. Motivos predefinidos por categoria
  7. Feedback 100% gerado por IA (GAT-004), recrutador NÃO edita diretamente. Apenas visualiza, aprova ou pede regeneração.

Requisitos Tecnicos:
  Frontend:
    - RejectionModal component
    - ReasonSelect (motivos predefinidos)
    - FeedbackPreview (preview da mensagem)
    - RegenerateButton (regenerar feedback)
    - ApproveAndSendButton (aprovar e enviar)
  Backend:
    - Motivos vêm de config ou banco
    - Feedback gerado via GAT-004
  Dados:
    - rejection_reasons: id, code, label, category, feedback_template

Design & Componentes:
  Componentes Existentes:
    - Modal - container (@radix-ui/react-dialog)
    - Select - motivo
    - Textarea - comentário
    - Button - confirmar, cancelar
  Novos Componentes:
    - RejectionModal - modal completo
    - ReasonSelect - select com categorias
    - FeedbackPreview - preview do texto
    - RegenerateButton - regenerar feedback
    - ApproveAndSendButton - aprovar e enviar
  Design Tokens:
    Background: --lia-bg-primary (#FFFFFF)
    Border: --lia-border-subtle (#E5E7EB)
    Header: --electric-red-light (#FEE2E2)
    Text: --lia-text-primary (#111827)
    Confirm: --electric-red (#de1c31)
    Cancel: --lia-text-secondary (#4B5563)
  Layout:
    Modal: max-w-lg, centered
    Sections: gap-6 entre seções
    Preview: border rounded, bg-secondary, p-4
    Buttons: flex justify-end, gap-3
  Estados:
    - Initial (form vazio)
    - Filled (motivo selecionado)
    - Previewing (feedback visível)
    - Regenerating (regenerando feedback)
    - Submitting (loading)
  Acessibilidade:
    - Focus trap no modal
    - ESC fecha modal
    - Label em todos os campos
    - ARIA-describedby para instruções

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador clica "Reprovar" no card
    2. Modal abre com overlay
    3. Select de motivo (obrigatório)
    4. Ao selecionar motivo: preview do feedback aparece
    5. Opção de editar feedback
    6. Comentário interno opcional
    7. Confirmar envia e fecha modal
  
  Layout do Modal:
    Header:
      - Ícone X para fechar
      - Título: "Reprovar Candidato"
      - Subtítulo: nome do candidato
    
    Body:
      Seção 1 - Motivo:
        - Label: "Motivo da reprovação *"
        - Select com grupos:
          - Técnico: "Conhecimento insuficiente", "Experiência abaixo do requisito"
          - Comportamental: "Perfil não alinhado à cultura", "Comunicação inadequada"
          - Processo: "Candidato desistiu", "Não compareceu", "Informações inconsistentes"
          - Outro: "Outro motivo" (habilita campo texto)
      
      Seção 2 - Feedback (aparece após motivo):
        - Label: "Mensagem para o candidato"
        - Preview box com texto gerado
        - Botão "Editar" para customizar
        - Se editando: textarea substitui preview
      
      Seção 3 - Comentário Interno:
        - Label: "Comentário interno (não enviado)"
        - Textarea opcional
        - Placeholder: "Notas para o time..."
    
    Footer:
      - Botão "Cancelar" (outline)
      - Botão "Confirmar Reprovação" (vermelho)
  
  Estados do Botão Confirmar:
    Default:
      - bg-electric-red, texto branco
      - Disabled até motivo selecionado
    Hover:
      - bg-electric-red-dark
    Loading:
      - Spinner + "Processando..."
    Disabled:
      - opacity-50
  
  Validações:
    Motivo:
      - Obrigatório
      - Se "Outro": campo de texto obrigatório
    Feedback:
      - Mínimo 20 caracteres
      - Máximo 500 caracteres
    Comentário:
      - Opcional
      - Máximo 1000 caracteres
  
  Mensagens de Feedback:
    - Erro validação: inline "Campo obrigatório"
    - Sucesso: Modal fecha + Toast "Candidato reprovado"
    - Erro API: Toast vermelho "Erro ao processar reprovação"


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Modal funcional
  - [ ] Motivos predefinidos
  - [ ] Preview de feedback
  - [ ] Edição de feedback
  - [ ] Comentário interno
  - [ ] Validações funcionando
  - [ ] Testes E2E passando

Criterios de Aceitacao:
  - [ ] Motivo obrigatório
  - [ ] Preview aparece após seleção
  - [ ] Edição salva corretamente
  - [ ] Modal fecha após sucesso
  - [ ] Decisão registrada

Arquivos de Referencia (Prototipo Replit):
  - pipeline_stage_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/pipeline_stage_service.py
  - stage_automation_engine.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/stage_automation_engine.py
  - technical_tests.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/technical_tests.py
```

---

### CARD GAT-004: Geração de Feedback LIA
**Épico:** É7 — Gates de Aprovação

```yaml
Titulo: [AI] Geração Automática de Feedback para Candidato
Tipo: Feature
Area: Full-Stack
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 8
Prioridade: Alta
Epic: EPIC-GATES
Status: 📋 Pendente Jira
Dependencias: GAT-003

Descricao: |
  Implementar geração automática de mensagens de feedback
  personalizadas pela LIA, baseadas no motivo de reprovação
  e no perfil do candidato, mantendo tom empático e construtivo.

Historia de Usuario: |
  Como recrutador, eu quero que a LIA gere automaticamente
  um feedback personalizado e respeitoso para candidatos
  reprovados, economizando meu tempo e garantindo consistência.

Regras de Negocio:
  1. Feedback gerado com base no motivo selecionado
  2. Tom empático, profissional e construtivo
  3. Não revelar detalhes internos de avaliação
  4. Incluir agradecimento e abertura para futuras vagas
  5. Personalizar com nome do candidato e vaga
  6. Máximo 200 palavras
  7. Templates base por categoria de motivo
  8. Recrutador apenas visualiza e aprova ou pede regeneração. Sem edição direta do texto.
  9. Se candidato reportou incidente durante triagem (TRI-013), feedback deve ter tom mais empático reconhecendo dificuldade técnica.

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/feedback/generate
    - Body: { candidate_id, job_id, reason_code, context? }
    - FeedbackGeneratorService class
  Frontend:
    - Integrado no RejectionModal (GAT-003)
  Dados:
    - feedback_templates: id, reason_code, base_template, variables
    - generated_feedbacks: id, candidate_id, job_id, reason_code, generated_text, final_text, sent_at

Integracoes Externas:
  LLM (Gemini):
    - Tipo: AI API
    - Uso: Geração de feedback personalizado
    - Serviço: feedback_generator_service.py
    - Secret: GEMINI_API_KEY
    - Custo: ~$0.001 por feedback (Gemini Flash)

Configuracao LLM:
  Modelo Recomendado: Gemini 2.5 Flash (MVP usa exclusivamente Gemini)
  Temperatura: 0.5 (empático mas consistente)
  Max Tokens: 500
  
  Prompt Template: |
    <role>Você é a LIA, assistente de recrutamento da WeDo Talent. Gere feedback profissional e empático para candidato reprovado.</role>
    <context>Vaga: {{job_title}} | Candidato: {{candidate_name}} | Motivo reprovação: {{rejection_reason}} | Score WSI: {{wsi_score}} | Houve incidente na triagem: {{had_incident}}</context>
    <constraints>
    1. Tom profissional e empático
    2. Não mencionar score numérico
    3. Sugerir áreas de desenvolvimento
    4. Se had_incident=true, reconhecer dificuldade técnica com tom mais compreensivo
    5. Máximo 200 palavras
    6. Não prometer recontato futuro
    7. Não mencionar outros candidatos
    </constraints>
    <output_format>{"feedback_text": "...", "tone": "empathetic|neutral|encouraging", "development_areas": ["..."]}</output_format>

Design & Componentes:
  (Integrado ao GAT-003)
  Componentes Existentes:
    - Skeleton - loading durante geração
  Novos Componentes:
    - FeedbackPreview - preview formatado
    - RegenerateButton - regenerar feedback
    - ApproveAndSendButton - aprovar e enviar feedback
  Design Tokens:
    Preview Background: --lia-bg-secondary (#F9FAFB)
    Preview Border: --lia-border-subtle (#E5E7EB)
    AI Indicator: --wedo-purple (#9860D1)
  Layout:
    Preview Box: border rounded, p-4, bg-secondary
    Regenerate: inline-flex com ícone
  Estados:
    - Generating (skeleton pulsando)
    - Generated (texto visível)
    - Regenerating (loading no botão)

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador seleciona motivo no modal
    2. Sistema dispara geração de feedback
    3. Preview box mostra skeleton durante loading
    4. Após 1-2s, texto gerado aparece
    5. Botão "Regenerar" disponível se não gostar
    6. Botão "Editar" permite customizar
    7. Texto final salvo ao confirmar reprovação
  
  Preview Box:
    Header:
      - Ícone AI (Brain)
      - Texto: "Mensagem gerada pela LIA"
      - Botão "Regenerar" (ícone refresh)
    
    Content:
      - Texto formatado do feedback
      - Contador de palavras no canto
    
    Footer:
      - Botão "Editar" (se quiser customizar)
  
  Regenerar:
    Click:
      - Spinner no botão
      - Novo texto substitui anterior
      - Toast: "Novo feedback gerado"
    Limite:
      - Máximo 3 regenerações
      - Após 3: "Edite manualmente ou use o atual"
  
  Editar:
    Click:
      - Preview vira textarea
      - Foco no início do texto
      - Contador de palavras atualiza em tempo real
    Salvar:
      - Click fora ou Enter salva
      - Preview volta com texto editado
      - Badge "Editado" aparece
  
  Mensagens de Feedback:
    - Gerando: Skeleton animado
    - Gerado: Silencioso (já aparece)
    - Regenerado: Toast azul "Novo feedback gerado"
    - Erro: Toast vermelho "Erro ao gerar feedback"
    - Limite: Toast amarelo "Limite de regenerações atingido"

DoD:
  - [ ] Geração automática funciona
  - [ ] Personalização com nome e vaga
  - [ ] Tom empático e profissional
  - [ ] Regeneração funciona (max 3x)
  - [ ] Edição funciona
  - [ ] Limite de palavras respeitado
  - [ ] Testes unitários passando

Criterios de Aceitacao:
  - [ ] Feedback gerado em < 3s
  - [ ] Texto inclui nome do candidato
  - [ ] Regenerar produz texto diferente
  - [ ] Edição persiste corretamente
  - [ ] Feedback salvo no banco

Arquivos de Referencia (Prototipo Replit):
  - pipeline_stage_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/pipeline_stage_service.py
  - stage_automation_engine.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/stage_automation_engine.py
  - batch-approval-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/batch-approval-modal.tsx

Nota: "FeedbackEditor removido. Recrutador não edita texto diretamente — apenas aprova ou pede regeneração."
```

---

### CARD GAT-005: Envio de Feedback
**Épico:** É7 — Gates de Aprovação

```yaml
Titulo: [BACKEND] Envio de Feedback via WhatsApp e Email
Tipo: Feature
Area: Full-Stack
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 5
Prioridade: Alta
Epic: EPIC-GATES
Status: 📋 Pendente Jira
Dependencias: GAT-004

Descricao: |
  Implementar o envio automático do feedback de reprovação
  para o candidato via WhatsApp (preferencial) ou Email,
  com tracking de entrega e leitura.

Historia de Usuario: |
  Como recrutador, eu quero que o feedback seja enviado
  automaticamente ao candidato após a reprovação, sem
  precisar enviar manualmente.

Regras de Negocio:
  1. Canal preferencial: WhatsApp (se candidato tem WhatsApp ativo)
  2. Fallback: Email se WhatsApp não disponível
  3. Envio automático após confirmação de reprovação
  4. Tracking de status: enviado, entregue, lido
  5. Retry automático em caso de falha (max 3x)
  6. Log de todas as tentativas para auditoria
  7. Opção de envio manual se automático falhar

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/feedback/send
    - Body: { candidate_id, job_id, channel: 'whatsapp' | 'email' }
    - FeedbackDeliveryService class
    - Integração com Twilio (WhatsApp) e Mailgun/SMTP (Email)
  Frontend:
    - FeedbackStatusBadge (enviado, entregue, lido)
    - ResendButton (reenvio manual)
  Dados:
    - feedback_deliveries: id, feedback_id, channel, status, sent_at, delivered_at, read_at, attempts, last_error

Integracoes Externas:
  Twilio WhatsApp:
    - Tipo: REST API
    - Uso: Envio de mensagem de feedback
    - Serviço: whatsapp_service.py (já existente)
    - Secret: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
    - Custo: ~$0.05 por mensagem
    - Webhook: status de entrega/leitura
  
  Email (Mailgun):
    - Tipo: REST API
    - Uso: Fallback para candidatos sem WhatsApp
    - Serviço: email_service.py (já existente)
    - Secret: MAILGUN_API_KEY, MAILGUN_DOMAIN
    - Custo: ~$0.001 por email (5.000 grátis/mês por 3 meses)
    - Tracking: open/click tracking

Design & Componentes:
  Componentes Existentes:
    - Badge - status
    - Button - reenviar
    - Tooltip - detalhes de erro
  Novos Componentes:
    - FeedbackStatusBadge - badge com status de entrega
    - FeedbackDeliveryLog - histórico de tentativas
    - ResendFeedbackButton - botão de reenvio
  Design Tokens:
    Pending: --wedo-yellow (#EAB308)
    Sent: --wedo-cyan (#60BED1)
    Delivered: --wedo-green (#22C55E)
    Read: --wedo-green-dark (#16A34A)
    Failed: --electric-red (#de1c31)
  Layout:
    Badge: inline-flex, rounded-full, px-2 py-1
    Log: modal ou expandível com histórico
  Estados:
    - Pending (aguardando envio)
    - Sent (enviado, aguardando entrega)
    - Delivered (entregue ao dispositivo)
    - Read (lido pelo candidato)
    - Failed (falha após retries)
  Acessibilidade:
    - Status anunciado para screen readers
    - Botão de retry acessível

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador confirma reprovação no modal
    2. Feedback salvo no banco
    3. Sistema detecta canal preferido (WhatsApp > Email)
    4. Envia mensagem automaticamente
    5. Badge de status aparece no card do candidato
    6. Webhook atualiza status (entregue, lido)
    7. Se falha: retry automático em 5min, 30min, 2h
    8. Após 3 falhas: notifica recrutador para ação manual
  
  Badge de Status:
    Pending:
      - Cor: amarela
      - Ícone: clock
      - Texto: "Aguardando envio"
    
    Sent:
      - Cor: cyan
      - Ícone: send
      - Texto: "Enviado" + timestamp
    
    Delivered:
      - Cor: verde
      - Ícone: check
      - Texto: "Entregue" + timestamp
    
    Read:
      - Cor: verde escuro
      - Ícone: double-check
      - Texto: "Lido" + timestamp
    
    Failed:
      - Cor: vermelha
      - Ícone: alert
      - Texto: "Falha" + botão retry
  
  Reenvio Manual:
    Aparece quando: Failed
    Click:
      - Spinner no botão
      - Tenta reenvio
      - Sucesso: atualiza para Sent
      - Falha: Toast com erro
    
    Opções:
      - "Reenviar via WhatsApp"
      - "Enviar via Email" (fallback)
  
  Log de Tentativas:
    Click em badge → expande log:
      - Lista de tentativas
      - Data/hora de cada
      - Status de cada
      - Erro (se houver)
  
  Mensagens de Feedback:
    - Enviando: Toast azul "Enviando feedback..."
    - Enviado: Toast verde "Feedback enviado com sucesso"
    - Entregue: Notificação silenciosa (atualiza badge)
    - Lido: Notificação silenciosa (atualiza badge)
    - Falha: Toast vermelho "Falha no envio. Tentando novamente..."
    - Falha final: Toast vermelho "Não foi possível enviar. Use envio manual."

DoD:
  - [ ] Envio via WhatsApp funciona
  - [ ] Envio via Email funciona
  - [ ] Status tracking funciona
  - [ ] Retry automático implementado
  - [ ] Reenvio manual funciona
  - [ ] Log de tentativas disponível
  - [ ] Testes de integração passando

Criterios de Aceitacao:
  - [ ] Feedback enviado automaticamente
  - [ ] Status atualiza via webhook
  - [ ] Fallback para email funciona
  - [ ] Retry após falha funciona
  - [ ] Reenvio manual disponível

Arquivos de Referencia (Prototipo Replit):
  - batch-approval-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/batch-approval-modal.tsx
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/backend-proxy/approvals/route.ts
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/backend-proxy/approvals/[id]/approve/route.ts
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/backend-proxy/approvals/[id]/reject/route.ts
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/backend-proxy/approvals/pending/route.ts
```

---

### CARD GAT-006: Aprovação em Massa
**Épico:** É7 — Gates de Aprovação

```yaml
Titulo: [FULL-STACK] Aprovação e Reprovação em Massa (Bulk)
Tipo: Feature
Area: Full-Stack
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 5
Prioridade: Média
Epic: EPIC-GATES
Status: 📋 Pendente Jira
Dependencias: GAT-001, GAT-002

Descricao: |
  Implementar funcionalidade de aprovar ou reprovar múltiplos
  candidatos simultaneamente, com confirmação e processamento
  assíncrono para grandes volumes.

Historia de Usuario: |
  Como recrutador, eu quero aprovar ou reprovar vários candidatos
  de uma vez, para agilizar meu trabalho quando há muitos
  candidatos pendentes.

Regras de Negocio:
  1. Selecionar múltiplos candidatos via checkbox
  2. Mínimo 2 para habilitar ação em massa
  3. Máximo 50 por operação (para performance)
  4. Processamento assíncrono para > 10 candidatos
  5. Progress indicator durante processamento
  6. Resultado final com contagem (sucesso/falha)
  7. Reprovação em massa requer motivo único para todos

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/gates/bulk/approve
    - POST /api/v1/gates/bulk/reject
    - Body: { candidate_ids: string[], job_id: string, reason_code?: string }
    - BulkApprovalService com job queue
    - Webhook ou polling para status
  Frontend:
    - BulkActionBar component
    - BulkProgressModal
    - BulkResultSummary
  Dados:
    - bulk_operations: id, operation_type, candidate_ids (JSONB), status, started_at, completed_at, results (JSONB)

Design & Componentes:
  Componentes Existentes:
    - Checkbox - seleção
    - Button - ações
    - Modal - confirmação
    - Progress - barra de progresso
  Novos Componentes:
    - BulkActionBar - barra flutuante de ações
    - BulkConfirmModal - confirmação com contador
    - BulkProgressModal - progresso em tempo real
    - BulkResultSummary - resumo do resultado
  Design Tokens:
    Action Bar Background: --lia-bg-tertiary (#F3F4F6)
    Progress: --wedo-cyan (#60BED1)
    Success Count: --wedo-green (#22C55E)
    Failure Count: --electric-red (#de1c31)
  Layout:
    Action Bar: fixed bottom, full-width, h-16, shadow-lg
    Modal: centered, max-w-md
    Progress: w-full, h-2, rounded
  Estados:
    - Selecting (checkboxes ativos)
    - Confirming (modal aberto)
    - Processing (progress modal)
    - Completed (summary modal)
  Acessibilidade:
    - Contador anunciado
    - Progress com ARIA
    - Focus management entre modais

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador seleciona candidatos via checkbox
    2. Action Bar aparece no bottom: "X selecionados"
    3. Click em "Aprovar Todos" ou "Reprovar Todos"
    4. Modal de confirmação aparece
    5. Para reprovação: select de motivo único
    6. Confirma: progress modal aparece
    7. Processamento com progress bar
    8. Conclusão: summary modal com resultados
  
  Action Bar:
    Layout:
      - Contador: "X candidatos selecionados"
      - Botão "Aprovar Todos" (verde)
      - Botão "Reprovar Todos" (vermelho outline)
      - Botão "Limpar" (X icon)
    
    Animação:
      - Slide up quando >= 2 selecionados
      - Slide down quando < 2
    
    Estados:
      - 0-1 selecionados: oculto
      - 2-50 selecionados: visível
      - > 50 selecionados: warning "Máximo 50"
  
  Modal de Confirmação:
    Aprovar:
      - Título: "Aprovar X candidatos?"
      - Subtítulo: "Eles serão movidos para [próxima etapa]"
      - Botões: "Cancelar", "Confirmar Aprovação"
    
    Reprovar:
      - Título: "Reprovar X candidatos?"
      - Select: "Motivo (aplicado a todos)"
      - Checkbox: "Enviar feedback automático"
      - Botões: "Cancelar", "Confirmar Reprovação"
  
  Modal de Progresso:
    Layout:
      - Título: "Processando..."
      - Progress bar: 0-100%
      - Contador: "X de Y processados"
      - Spinner animado
    
    Comportamento:
      - Atualiza em tempo real via polling/websocket
      - Não pode ser fechado durante processamento
      - ESC desabilitado
  
  Modal de Resultado:
    Layout:
      - Título: "Operação concluída"
      - Sucesso: "X candidatos processados com sucesso" (verde)
      - Falhas: "Y falhas" (vermelho) + lista expansível
      - Botão: "Fechar"
    
    Se houver falhas:
      - Lista de candidatos que falharam
      - Motivo de cada falha
      - Botão: "Tentar novamente (Y)"
  
  Mensagens de Feedback:
    - Iniciando: Toast azul "Processando X candidatos..."
    - Concluído: Toast verde "X candidatos processados"
    - Falhas parciais: Toast amarelo "X processados, Y falhas"
    - Erro total: Toast vermelho "Erro no processamento"


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Seleção múltipla funciona
  - [ ] Action bar aparece/desaparece
  - [ ] Confirmação funciona
  - [ ] Processamento assíncrono
  - [ ] Progress em tempo real
  - [ ] Resultado com detalhes
  - [ ] Testes E2E passando

Criterios de Aceitacao:
  - [ ] Selecionar 2-50 candidatos
  - [ ] Aprovar em massa funciona
  - [ ] Reprovar em massa com motivo
  - [ ] Progress atualiza em tempo real
  - [ ] Falhas identificadas no resultado

Arquivos de Referencia (Prototipo Replit):
  - notification_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/notification_service.py
  - stage_automation_engine.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/stage_automation_engine.py
  - kpi-alert-system.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/alerts/kpi-alert-system.tsx
```

---

### CARD GAT-007: Histórico de Decisões
**Épico:** É7 — Gates de Aprovação

```yaml
Titulo: [BACKEND] Histórico e Auditoria de Decisões de Gate
Tipo: Feature
Area: Full-Stack
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 5
Prioridade: Média
Epic: EPIC-GATES
Status: 📋 Pendente Jira
Dependencias: GAT-001, GAT-002

Descricao: |
  Implementar sistema de auditoria completo para todas as
  decisões de gate (aprovação/reprovação), com registro de
  quem, quando, porquê e histórico de alterações.

Historia de Usuario: |
  Como gestor de RH, eu quero visualizar o histórico de todas
  as decisões tomadas no processo seletivo, para auditoria,
  compliance e análise de padrões.

Regras de Negocio:
  1. Registrar todas as decisões de gate (G1 e G2)
  2. Campos: candidato, vaga, decisão, motivo, decisor, timestamp
  3. Registrar overrides (mudança de decisão)
  4. Filtros por período, vaga, decisor, tipo de decisão
  5. Exportar para CSV/Excel
  6. Retenção: 2 anos (LGPD)
  7. Anonimização após período de retenção

Requisitos Tecnicos:
  Backend:
    - GET /api/v1/gates/history
    - Query: ?job_id, ?candidate_id, ?decision, ?decider_id, ?start_date, ?end_date
    - GET /api/v1/gates/history/export
    - GateHistoryService class
  Frontend:
    - GateHistoryTable component
    - GateHistoryFilters
    - GateHistoryExport
  Dados:
    - gate_decisions: já existe, adicionar índices
    - gate_decision_overrides: id, original_decision_id, new_decision, reason, changed_by, changed_at

Design & Componentes:
  Componentes Existentes:
    - Table - lista de histórico (tanstack/react-table)
    - DateRangePicker - filtro de período
    - Select - filtros
    - Button - exportar
  Novos Componentes:
    - GateHistoryTable - tabela paginada com filtros
    - GateHistoryFilters - painel de filtros
    - GateHistoryExport - modal de exportação
    - DecisionTimelineItem - item de timeline
  Design Tokens:
    Background: --lia-bg-primary (#FFFFFF)
    Border: --lia-border-subtle (#E5E7EB)
    Approved: --wedo-green (#22C55E)
    Rejected: --electric-red (#de1c31)
    Override: --wedo-purple (#9860D1)
  Layout:
    Container: max-w-6xl mx-auto
    Filters: sticky top, full-width
    Table: full-width com scroll horizontal
    Pagination: bottom, centered
  Estados:
    - Loading (skeleton table)
    - Loaded (dados visíveis)
    - Empty (nenhum registro)
    - Exporting (loading no botão)
  Acessibilidade:
    - Tabela com headers acessíveis
    - Filtros com labels
    - Paginação navegável via keyboard

Comportamento de UI:
  Fluxo Principal:
    1. Gestor acessa menu "Auditoria" ou "Histórico"
    2. Tabela carrega com registros recentes
    3. Filtros disponíveis no topo
    4. Aplicar filtros atualiza tabela
    5. Click em linha expande detalhes
    6. Botão "Exportar" gera arquivo
  
  Layout da Tabela:
    Colunas:
      - Data/Hora
      - Candidato (nome + link)
      - Vaga (título + link)
      - Gate (G1 / G2)
      - Decisão (Aprovado / Reprovado)
      - Motivo (resumido)
      - Decisor (nome)
      - Ações (ver detalhes)
    
    Filtros:
      - Período (DateRangePicker)
      - Vaga (MultiSelect)
      - Gate (Select: G1, G2, Todos)
      - Decisão (Select: Aprovado, Reprovado, Todos)
      - Decisor (MultiSelect)
    
    Ordenação:
      - Default: Data/Hora DESC
      - Click em header alterna ASC/DESC
  
  Linha Expandida:
    Click em linha:
      - Expande seção abaixo
      - Mostra: motivo completo, comentário interno
      - Se houve override: mostra histórico
      - Link: "Ver perfil do candidato"
  
  Overrides:
    Se decisão foi alterada:
      - Badge "Override" roxo
      - Timeline de alterações
      - Decisão original → Nova decisão
      - Quem alterou, quando, porquê
  
  Exportação:
    Click em "Exportar":
      - Modal com opções
      - Formato: CSV, Excel, PDF
      - Período: usar filtros atuais
      - Colunas: seleção opcional
      - Confirmar: download inicia
  
  Métricas Resumidas (topo):
    Cards de resumo:
      - Total de decisões no período
      - Aprovações: X (Y%)
      - Reprovações: X (Y%)
      - Overrides: X
  
  Mensagens de Feedback:
    - Loading: Skeleton table
    - Empty: "Nenhum registro encontrado"
    - Filtros aplicados: Toast azul "Filtros aplicados"
    - Export sucesso: Toast verde "Arquivo exportado"
    - Erro: Toast vermelho "Erro ao carregar histórico"

DoD:
  - [ ] Histórico completo registrado
  - [ ] Filtros funcionando
  - [ ] Exportação CSV/Excel
  - [ ] Overrides rastreados
  - [ ] Paginação funcional
  - [ ] Métricas resumidas
  - [ ] Testes unitários passando

Criterios de Aceitacao:
  - [ ] Todas as decisões registradas
  - [ ] Filtros refinam resultados
  - [ ] Exportar gera arquivo válido
  - [ ] Overrides visíveis na timeline
  - [ ] Paginação navega corretamente

Arquivos de Referencia (Prototipo Replit):
  - strategic-dashboard.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/dashboard/strategic-dashboard.tsx
  - predictive-analytics-tab.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/dashboard/predictive-analytics-tab.tsx
  - pipeline_stage_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/pipeline_stage_service.py
```

---

### CARD GAT-008: Aprendizagem da IA sobre Aprovações/Reprovações
**Épico:** É7 — Gates de Aprovação

```yaml
Titulo: "[AI + FULL-STACK] Aprendizagem da IA sobre Aprovações/Reprovações"
Tipo: Feature (AI + Full-Stack)
Area: Backend-IA
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 8
Prioridade: Alta
Epic: EPIC-GATES
Status: 📋 A Criar no Jira
Dependencias: GAT-001, GAT-003, GAT-004

Descricao: |
  A LIA aprende com os padrões de aprovação e reprovação dos recrutadores
  para melhorar buscas futuras. Agrega dados por motivo de reprovação,
  perfil do candidato e recrutador, gerando sugestões proativas de ajuste
  nos filtros de busca. Aprendizado segmentado por recrutador E por empresa.

Historia de Usuario: |
  Como recrutador, eu quero que a LIA aprenda com minhas decisões de
  aprovação/reprovação para sugerir ajustes nos critérios de busca e
  melhorar a qualidade dos candidatos apresentados.

Regras de Negocio:
  1. Agregar decisões por motivo, perfil do candidato e recrutador
  2. Após N reprovações pelo mesmo motivo, sugerir ajuste de filtro
  3. Calcular taxa de aprovação por vaga e motivos mais comuns
  4. Aprendizado segmentado por recrutador E por empresa (company_id)
  5. Sugestões proativas: "Nos últimos 30 dias, 80% dos reprovados tinham < 3 anos de experiência. Deseja aumentar o filtro?"
  6. Painel de insights no dashboard com estatísticas
  7. Sugestões inline na busca (junto ao smart-search-input)
  8. Mínimo 10 decisões para gerar primeira sugestão
  9. Recrutador pode aceitar ou ignorar sugestão (feedback loop)

Requisitos Tecnicos:
  Backend:
    - LearningFromDecisionsService class
    - Agregações por reason/profile/recruiter/company
    - Geração de sugestões baseada em padrões
    - POST /api/v1/gates/insights (retorna insights + sugestões)
    - GET /api/v1/gates/stats?job_id={id} (estatísticas por vaga)
    - POST /api/v1/gates/suggestions/{id}/feedback (aceitar/ignorar)
  Frontend:
    - InsightsPanel (dashboard) — painel com gráficos e sugestões
    - Inline suggestions no smart-search-input
  Dados:
    - gate_decision_aggregates: company_id, recruiter_id, reason_code, count, period
    - gate_suggestions: id, company_id, suggestion_type, suggestion_text, confidence, status (pending/accepted/ignored)
  Validacoes:
    - Mínimo 10 decisões para gerar sugestão
    - Confiança mínima 0.7 para exibir sugestão

Integracoes Externas:
  LLM (Gemini):
    - Tipo: AI API
    - Uso: Análise de padrões de decisão e geração de insights textuais
    - Serviço: gate_learning_service.py
    - SDK: google-generativeai
    - Secret: GEMINI_API_KEY
    - Custo: ~$0.01-0.03 por análise (Pro)
    - Rate Limit: 60 RPM
    - Documentacao: https://ai.google.dev/docs

Configuracao LLM:
  Modelo: Gemini 2.5 Pro (análise complexa de padrões)
  Temperatura: 0.4
  Max Tokens: 1000
  Uso: Análise de padrões textuais para gerar insights em linguagem natural
  
  Prompt Template: |
    <role>
    Você é um analista de dados de recrutamento da plataforma WeDo Talent.
    Analise os padrões de decisão dos recrutadores e gere insights acionáveis.
    </role>
    
    <data>
    Decisões recentes (últimos 30 dias):
    {{decision_summary}}
    
    Motivos de reprovação mais frequentes:
    {{top_rejection_reasons}}
    
    Taxa de aprovação por vaga:
    {{approval_rates}}
    </data>
    
    <task>
    1. Identifique padrões relevantes (ex: "80% dos reprovados tinham < 3 anos de experiência")
    2. Gere sugestões de refinamento de critérios de busca
    3. Destaque anomalias (ex: taxa de aprovação muito baixa em vaga específica)
    </task>
    
    <output_format>
    {
      "insights": [
        { "text": "...", "type": "pattern|anomaly|trend", "confidence": 0.0-1.0 }
      ],
      "suggestions": [
        { "text": "...", "action": "adjust_filter|review_criteria|escalate", "impact": "high|medium|low" }
      ]
    }
    </output_format>

Design & Componentes:
  Componentes Existentes:
    - DashboardPage - página de dashboards existente
    - SmartSearchInput - input de busca inteligente
    - Card - container de insights
    - Badge - indicadores
  Novos Componentes:
    - DecisionInsightsPanel - painel de insights de decisões
    - InsightCard - card individual de insight
    - SuggestionInline - sugestão inline na busca
    - ApprovalRateChart - gráfico de taxa de aprovação
  Design Tokens:
    Insight Background: --lia-bg-secondary (#F9FAFB)
    Suggestion: --wedo-cyan (#60BED1)
    Positive Trend: --wedo-green (#22C55E)
    Negative Trend: --electric-red (#de1c31)
    Neutral: --lia-text-tertiary (#6B7280)
  Layout:
    InsightsPanel: max-w-4xl, grid 2 cols
    InsightCard: border rounded, p-4, shadow-sm
    SuggestionInline: inline-flex, bg-cyan-50, rounded-full, px-3 py-1
  Estados:
    - Loading (skeleton)
    - Empty (< 10 decisões, mensagem informativa)
    - Populated (insights + sugestões)
    - Suggestion Accepted (feedback visual)
  Acessibilidade:
    - ARIA-live para sugestões dinâmicas
    - Labels descritivos em gráficos
    - Contraste WCAG AA

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador acessa dashboard
    2. InsightsPanel carrega estatísticas agregadas
    3. Gráfico mostra taxa de aprovação por vaga
    4. Cards de sugestão aparecem se houver padrões detectados
    5. Recrutador clica "Aceitar sugestão" → filtro ajustado na busca
    6. Ou clica "Ignorar" → sugestão removida + feedback registrado

  Layout:
    Desktop: InsightsPanel ocupa seção do dashboard
    Mobile: Cards empilhados verticalmente

  Estados de Botoes:
    Aceitar:
      - Default: bg-wedo-cyan, texto branco
      - Hover: bg-wedo-cyan-dark
      - Loading: spinner
    Ignorar:
      - Default: bg-transparent, texto secondary
      - Hover: bg-gray-100

  Validacoes Inline:
    - "Dados insuficientes para gerar insights (mínimo 10 decisões)"

  Mensagens de Feedback:
    Sucesso: "Sugestão aceita! Filtro ajustado na próxima busca."
    Ignorado: "Sugestão ignorada."

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md (Seções: 2.3 Cards, 2.6 Badges & Tags, 2.1 Botões, PARTE 4 Charts (se existir))"
  Figma: "Seção 8.2 — Gates Insights"
  Assets:
    - "Ícone de lâmpada para sugestões"
    - "Ícone de gráfico para insights"
  Tokens:
    - "--wedo-cyan (#60BED1)"
    - "--lia-bg-secondary (#F9FAFB)"

DoD:
  - [ ] LearningFromDecisionsService funcional com agregações
  - [ ] Endpoint de insights retornando dados reais
  - [ ] InsightsPanel renderizando no dashboard
  - [ ] Sugestões inline aparecendo na busca quando aplicável
  - [ ] Gemini 2.5 Pro gerando insights textuais
  - [ ] Feedback de aceitar/ignorar funcional
  - [ ] Dados segmentados por recrutador e empresa
  - [ ] Responsivo (desktop, tablet)

Criterios de Aceitacao:
  - [ ] Após 10+ reprovações com mesmo motivo, sugestão aparece
  - [ ] Taxa de aprovação por vaga exibida corretamente
  - [ ] Recrutador aceita sugestão → filtro refletido na busca
  - [ ] Recrutador ignora sugestão → não reaparece
  - [ ] Insights textuais gerados pelo Gemini são claros e acionáveis
  - [ ] Dados de uma empresa não vazam para outra (multi-tenant)

Arquivos de Referencia (Prototipo Replit):
  - dashboards-page: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/dashboards-page.tsx
  - smart-search-input: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/smart-search-input.tsx
```

---

## ÉPICO 8: TEMPLATES DE COMUNICAÇÃO

---

### CARD TPL-001: Template de Abordagem Inicial
**Épico:** É8 — Templates de Comunicação

```yaml
Titulo: [FULL-STACK] Template de Mensagem de Abordagem Inicial
Tipo: Feature
Area: Full-Stack
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 5
Prioridade: Alta
Epic: EPIC-TEMPLATES
Status: 📋 Pendente Jira

Descricao: |
  Criar template de mensagem para primeiro contato com candidatos
  aprovados no Gate 1. A mensagem apresenta a oportunidade e
  convida para a triagem WSI via WhatsApp.

Historia de Usuario: |
  Como recrutador, eu quero ter um template profissional para
  o primeiro contato com candidatos, que seja personalizado
  automaticamente e aumente a taxa de resposta.

Regras de Negocio:
  1. Template padrão fornecido pelo sistema
  2. Personalizável por empresa e vaga
  3. Variáveis dinâmicas: {{nome}}, {{vaga}}, {{empresa}}, {{recrutador}}
  4. Limite de caracteres: 1024 (WhatsApp)
  5. Deve incluir opt-out claro
  6. Tom profissional mas acolhedor
  7. Versões para WhatsApp e Email
  8. Template de abordagem dividido em 2: (a) Consentimento LGPD e (b) Apresentação da vaga
  9. Aceitação do approach_consent dispara mensagem proativa TRI-013 (orientação sobre reporte de problemas)

Requisitos Tecnicos:
  Backend:
    - GET /api/v1/templates/approach
    - POST /api/v1/templates/approach
    - PUT /api/v1/templates/approach/{id}
    - TemplateService class
    - Tipos: approach_consent e approach_presentation. Campo type no modelo communication_templates atualizado. Evento de aceitação de consent deve disparar mensagem proativa TRI-013.
  Frontend:
    - ApproachTemplateEditor component
    - TemplatePreview
    - VariableInserter
  Dados:
    - communication_templates: id, type ('approach', 'approach_consent', 'approach_presentation', 'scheduling', 'confirmation', 'post_interview'), company_id, name, content, variables (JSONB), channel ('whatsapp', 'email'), is_default, created_at, updated_at

Design & Componentes:
  Componentes Existentes:
    - Card - container
    - Textarea - edição
    - Button - ações
    - Badge - variáveis
  Novos Componentes:
    - TemplateEditor - editor com suporte a variáveis
    - VariableInserter - dropdown de variáveis
    - TemplatePreview - preview renderizado
    - CharacterCounter - contador com limite
  Design Tokens:
    Background: --lia-bg-primary (#FFFFFF)
    Border: --lia-border-subtle (#E5E7EB)
    Variable: --wedo-cyan (#60BED1) background
    Accent: --wedo-cyan (#60BED1)
    Warning: --wedo-yellow (#EAB308) quando próximo do limite
    Error: --electric-red (#de1c31) quando excede
  Layout:
    Container: max-w-2xl mx-auto
    Editor: full-width, min-h-[200px]
    Preview: border rounded, bg-secondary, p-4
    Variables: inline-flex, flex-wrap, gap-2
    Spacing: gap-6 entre seções
  Estados:
    - Viewing (template salvo)
    - Editing (textarea ativa)
    - Previewing (com dados de exemplo)
    - Saving (loading)
  Acessibilidade:
    - Labels em todos os campos
    - Contador anunciado
    - Variáveis navegáveis via keyboard

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador acessa configuração de templates
    2. Template de abordagem exibido (padrão ou customizado)
    3. Click "Editar" ativa modo edição
    4. Digita texto, insere variáveis via dropdown
    5. Contador de caracteres atualiza em tempo real
    6. Preview mostra mensagem renderizada
    7. Salvar persiste template para a empresa
  
  Layout do Editor:
    Header:
      - Título: "Template de Abordagem Inicial"
      - Badge: "WhatsApp" ou "Email"
      - Botão: "Editar" / "Cancelar"
    
    Editor Area:
      - Toolbar com variáveis clicáveis
      - Textarea com texto do template
      - Contador: "X / 1024 caracteres"
    
    Variáveis Disponíveis:
      - {{nome}} - Nome do candidato
      - {{primeiro_nome}} - Primeiro nome
      - {{vaga}} - Título da vaga
      - {{empresa}} - Nome da empresa
      - {{recrutador}} - Nome do recrutador
      - {{link_triagem}} - Link para iniciar triagem
    
    Preview:
      - Toggle: "Ver preview"
      - Mostra mensagem com dados fictícios
      - Exemplo: "Olá, João! Encontrei seu perfil..."
  
  Template Padrão:
    WhatsApp: |
      Olá, {{primeiro_nome}}! 👋

      Sou {{recrutador}} da {{empresa}}.

      Encontrei seu perfil e acredito que você pode ser um ótimo match para nossa vaga de {{vaga}}.

      Gostaria de conversar com você sobre essa oportunidade. Podemos iniciar uma triagem rápida?

      Basta responder "SIM" para começarmos!

      Se preferir não participar, responda "NÃO" a qualquer momento.
  
  Interações:
    Inserir Variável:
      - Click em variável na toolbar
      - Insere no cursor atual
      - Ou: digitar {{ e autocomplete
    
    Preview Toggle:
      - Switch "Ver preview"
      - Ativo: mostra versão renderizada
      - Preview atualiza em tempo real
    
    Salvar:
      - Valida limite de caracteres
      - Salva para empresa
      - Toast de confirmação
  
  Validações:
    Caracteres:
      - Warning: > 900 (amarelo)
      - Erro: > 1024 (vermelho, bloqueia salvar)
    Variáveis:
      - Validar que todas são conhecidas
      - Erro se variável inválida: "{{xyz}} não reconhecida"
  
  Mensagens de Feedback:
    - Salvo: Toast verde "Template salvo com sucesso"
    - Erro: Toast vermelho "Erro ao salvar template"
    - Warning: Toast amarelo "Template próximo do limite"
    - Variável inválida: Inline "Variável não reconhecida"


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Template padrão disponível
  - [ ] Edição funciona
  - [ ] Variáveis inseridas corretamente
  - [ ] Preview renderiza
  - [ ] Limite de caracteres validado
  - [ ] Salvamento funciona
  - [ ] Testes E2E passando

Criterios de Aceitacao:
  - [ ] Template exibido corretamente
  - [ ] Edição salva corretamente
  - [ ] Variáveis substituídas no preview
  - [ ] Limite de 1024 chars respeitado
  - [ ] Versão WhatsApp e Email

Arquivos de Referencia (Prototipo Replit):
  - email-templates-manager.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/email-templates/email-templates-manager.tsx
  - email-template-form-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/email-templates/email-template-form-modal.tsx
  - template-variables.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/template-variables.ts
  - email_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/email_service.py
  - recruitment_email_templates.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/recruitment_email_templates.py
```

---

### CARD TPL-002: Template de Agendamento
**Épico:** É8 — Templates de Comunicação

```yaml
Titulo: [FULL-STACK] Template de Mensagem de Agendamento
Tipo: Feature
Area: Full-Stack
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 5
Prioridade: Alta
Epic: EPIC-TEMPLATES
Status: 📋 Pendente Jira
Dependencias: TPL-001

Descricao: |
  Criar template de mensagem para convidar candidatos aprovados
  no Gate 2 para agendar entrevista, incluindo link de calendário
  e opções de horários.

Historia de Usuario: |
  Como recrutador, eu quero enviar automaticamente um convite de
  agendamento personalizado, que permita ao candidato escolher
  o melhor horário diretamente.

Regras de Negocio:
  1. Enviado automaticamente após aprovação G2
  2. Inclui link para calendário (Calendly, Cal.com, ou integrado)
  3. Variáveis: {{nome}}, {{vaga}}, {{empresa}}, {{link_agenda}}
  4. Tom entusiasmado (candidato passou para entrevista!)
  5. Inclui prazo para agendar (ex: 48h)
  6. Reminder automático se não agendar

Requisitos Tecnicos:
  Backend:
    - GET /api/v1/templates/scheduling
    - POST /api/v1/templates/scheduling
    - PUT /api/v1/templates/scheduling/{id}
  Frontend:
    - SchedulingTemplateEditor component (reutiliza TPL-001)
  Dados:
    - Reutiliza communication_templates com type='scheduling'

Design & Componentes:
  (Reutiliza componentes de TPL-001)
  Novos Componentes:
    - CalendarLinkGenerator - gerar link de agenda
    - ExpirationPicker - seletor de prazo
  Design Tokens:
    (Mesmos de TPL-001)
    Urgency: --wedo-yellow para prazo
  Layout:
    (Similar a TPL-001)
  Estados:
    (Mesmos de TPL-001)

  Acessibilidade:
    - Keyboard navigation (Tab, Enter, Space, Escape)
    - Labels e placeholders descritivos
    - ARIA-labels em elementos interativos
    - Focus visible em todos os elementos clicáveis
    - Mensagens de erro anunciadas por screen readers
    - Contraste mínimo WCAG AA (4.5:1)

Comportamento de UI:
  (Similar a TPL-001)
  
  Template Padrão:
    WhatsApp: |
      Parabéns, {{primeiro_nome}}! 🎉

      Você foi aprovado(a) para a próxima fase do processo seletivo para {{vaga}} na {{empresa}}!

      Agora, precisamos agendar sua entrevista. Por favor, escolha o melhor horário:

      👉 {{link_agenda}}

      O link estará disponível por 48 horas.

      Estamos ansiosos para conversar com você!
  
  Variáveis Adicionais:
    - {{link_agenda}} - Link para calendário
    - {{prazo}} - Prazo para agendar (ex: "48 horas")
    - {{tipo_entrevista}} - "técnica", "comportamental", etc.
    - {{duracao}} - Duração estimada
  
  Configurações Extras:
    Prazo:
      - Dropdown: 24h, 48h, 72h, 1 semana
      - Default: 48h
    
    Link de Agenda:
      - Integração com calendário do recrutador
      - Ou: link externo (Calendly, etc.)


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Template padrão disponível
  - [ ] Link de agenda inserível
  - [ ] Prazo configurável
  - [ ] Preview funciona
  - [ ] Salvamento funciona
  - [ ] Testes passando

Criterios de Aceitacao:
  - [ ] Template com tom positivo
  - [ ] Link de agenda funcional
  - [ ] Prazo aparece na mensagem
  - [ ] Enviado após aprovação G2

Arquivos de Referencia (Prototipo Replit):
  - whatsapp_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_service.py
  - whatsapp_meta_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_meta_service.py
  - communication_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/communication_service.py
```

---

### CARD TPL-003: Template de Confirmação
**Épico:** É8 — Templates de Comunicação

```yaml
Titulo: [FULL-STACK] Template de Mensagem de Confirmação
Tipo: Feature
Area: Full-Stack
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 3
Prioridade: Média
Epic: EPIC-TEMPLATES
Status: 📋 Pendente Jira
Dependencias: TPL-002

Descricao: |
  Criar template de mensagem de confirmação de entrevista
  agendada, incluindo data, hora, link da reunião e instruções.

Historia de Usuario: |
  Como recrutador, eu quero que candidatos recebam automaticamente
  uma confirmação clara da entrevista agendada, com todos os
  detalhes necessários.

Regras de Negocio:
  1. Enviado automaticamente após agendamento
  2. Inclui: data, hora, timezone, link da reunião
  3. Instruções de preparação (se configuradas)
  4. Opção de adicionar ao calendário do candidato
  5. Contato para dúvidas
  6. Reminder 24h antes e 1h antes

Requisitos Tecnicos:
  Backend:
    - GET /api/v1/templates/confirmation
    - POST /api/v1/templates/confirmation
  Frontend:
    - ConfirmationTemplateEditor component
  Dados:
    - communication_templates com type='confirmation'

Design & Componentes:
  (Reutiliza componentes de TPL-001)

  Acessibilidade:
    - Keyboard navigation (Tab, Enter, Space, Escape)
    - Labels e placeholders descritivos
    - ARIA-labels em elementos interativos
    - Focus visible em todos os elementos clicáveis
    - Mensagens de erro anunciadas por screen readers
    - Contraste mínimo WCAG AA (4.5:1)

Comportamento de UI:
  Template Padrão:
    WhatsApp: |
      ✅ Entrevista Confirmada!

      Olá, {{primeiro_nome}}!

      Sua entrevista para {{vaga}} está confirmada:

      📅 Data: {{data_entrevista}}
      ⏰ Horário: {{hora_entrevista}}
      📍 Link: {{link_reuniao}}

      {{instrucoes}}

      Qualquer dúvida, responda esta mensagem.

      Até lá! 🙌
  
  Variáveis:
    - {{data_entrevista}} - Data formatada
    - {{hora_entrevista}} - Hora com timezone
    - {{link_reuniao}} - Link do Teams/Meet/Zoom
    - {{instrucoes}} - Instruções personalizadas
    - {{entrevistador}} - Nome de quem entrevistará
    - {{duracao}} - Duração estimada


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Template padrão disponível
  - [ ] Variáveis de data/hora funcionam
  - [ ] Link de reunião inserido
  - [ ] Enviado após agendamento
  - [ ] Testes passando

Criterios de Aceitacao:
  - [ ] Confirmação enviada automaticamente
  - [ ] Data/hora corretas
  - [ ] Link funcional
  - [ ] Reminder configurável

Arquivos de Referencia (Prototipo Replit):
  - email-templates-manager.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/email-templates/email-templates-manager.tsx
  - send-email-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/email-templates/send-email-modal.tsx
  - email_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/email_service.py
  - recruitment_email_templates.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/recruitment_email_templates.py
```

---

### CARD TPL-004: Template Pós-Entrevista
**Épico:** É8 — Templates de Comunicação

```yaml
Titulo: [FULL-STACK] Template de Mensagem Pós-Entrevista
Tipo: Feature
Area: Full-Stack
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 3
Prioridade: Média
Epic: EPIC-TEMPLATES
Status: 📋 Pendente Jira
Dependencias: TPL-003

Descricao: |
  Criar template de mensagem de agradecimento e próximos passos
  enviada após a entrevista, mantendo o candidato informado
  sobre o andamento do processo.

Historia de Usuario: |
  Como recrutador, eu quero manter o candidato informado após
  a entrevista sobre os próximos passos e prazo de resposta,
  melhorando a experiência do candidato.

Regras de Negocio:
  1. Enviado X horas após a entrevista (configurável)
  2. Agradecer pela participação
  3. Informar próximos passos e prazo
  4. Tom positivo independente do resultado
  5. Não antecipar resultado (feedback será separado)
  6. Manter engajamento do candidato

Requisitos Tecnicos:
  Backend:
    - GET /api/v1/templates/post_interview
    - POST /api/v1/templates/post_interview
    - Job agendado para envio automático
  Frontend:
    - PostInterviewTemplateEditor component
  Dados:
    - communication_templates com type='post_interview'
    - scheduled_communications: id, template_id, candidate_id, scheduled_at, sent_at

Design & Componentes:
  (Reutiliza componentes de TPL-001)
  Novos Componentes:
    - DelaySelector - tempo após entrevista para envio

  Acessibilidade:
    - Keyboard navigation (Tab, Enter, Space, Escape)
    - Labels e placeholders descritivos
    - ARIA-labels em elementos interativos
    - Focus visible em todos os elementos clicáveis
    - Mensagens de erro anunciadas por screen readers
    - Contraste mínimo WCAG AA (4.5:1)

Comportamento de UI:
  Template Padrão:
    WhatsApp: |
      Olá, {{primeiro_nome}}!

      Obrigado por participar da entrevista para {{vaga}} hoje!

      Foi um prazer conhecer você melhor. 🙂

      Próximos passos:
      - Nosso time irá avaliar os candidatos finalistas
      - Você receberá uma resposta em até {{prazo_resposta}}

      Enquanto isso, fique à vontade para nos enviar dúvidas.

      Atenciosamente,
      {{recrutador}}
  
  Variáveis:
    - {{prazo_resposta}} - Prazo para resposta final
    - {{data_entrevista}} - Data da entrevista realizada
  
  Configurações:
    Delay de Envio:
      - Options: 2h, 4h, 24h, 48h após entrevista
      - Default: 24h
    
    Prazo de Resposta:
      - Options: 3 dias, 1 semana, 2 semanas
      - Default: 1 semana


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Template padrão disponível
  - [ ] Delay configurável
  - [ ] Envio automático funciona
  - [ ] Testes passando

Criterios de Aceitacao:
  - [ ] Mensagem enviada após delay
  - [ ] Tom positivo e informativo
  - [ ] Prazo de resposta incluído
  - [ ] Não revela resultado

Arquivos de Referencia (Prototipo Replit):
  - email-templates-manager.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/email-templates/email-templates-manager.tsx
  - personalized_feedback_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/personalized_feedback_service.py
  - recruitment_email_templates.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/recruitment_email_templates.py
```

---

### CARD TPL-005: Editor de Templates
**Épico:** É8 — Templates de Comunicação

```yaml
Titulo: [FRONTEND] Editor WYSIWYG de Templates
Tipo: Feature
Area: Full-Stack
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 8
Prioridade: Alta
Epic: EPIC-TEMPLATES
Status: 📋 Pendente Jira

Descricao: |
  Implementar editor rico (WYSIWYG) para criação e edição de
  templates de comunicação, com suporte a formatação básica,
  inserção de variáveis e preview em tempo real.

Historia de Usuario: |
  Como recrutador, eu quero criar templates personalizados
  usando um editor visual intuitivo, sem precisar saber HTML
  ou markdown.

Regras de Negocio:
  1. Formatação: bold, italic, links
  2. Inserção de variáveis via dropdown ou autocomplete
  3. Emojis suportados (picker)
  4. Preview lado a lado ou toggle
  5. Versão plain text para WhatsApp
  6. Versão HTML para Email
  7. Limite de caracteres por canal

Requisitos Tecnicos:
  Frontend:
    - TemplateWYSIWYG component
    - Editor: TipTap ou Lexical (leve, extensível)
    - VariableExtension (extensão custom)
    - EmojiPicker integration
  Backend:
    - API já existente de templates
    - Converter: HTML → Plain text
  Dados:
    - Templates salvos com content_html e content_plain

Design & Componentes:
  Componentes Existentes:
    - Card - container
    - Button - toolbar
    - Dropdown - variáveis, emojis
    - Toggle - preview mode
  Novos Componentes:
    - TemplateWYSIWYG - editor principal
    - EditorToolbar - toolbar de formatação
    - VariableDropdown - inserção de variáveis
    - EmojiPicker - seletor de emojis
    - ChannelPreview - preview por canal
  Design Tokens:
    Editor Background: --lia-bg-primary (#FFFFFF)
    Toolbar Background: --lia-bg-tertiary (#F3F4F6)
    Variable Highlight: --wedo-cyan (#60BED1) with bg
    Accent: --wedo-cyan (#60BED1)
    Border: --lia-border-subtle (#E5E7EB)
  Layout:
    Container: max-w-3xl mx-auto
    Toolbar: sticky top, border-b
    Editor: min-h-[300px], p-4
    Preview: side-by-side (desktop) ou toggle (mobile)
    Spacing: gap-4 entre seções
  Estados:
    - Editing (cursor ativo)
    - Previewing (split view)
    - Saving (loading)
  Acessibilidade:
    - Toolbar navegável via keyboard
    - Shortcuts: Ctrl+B (bold), Ctrl+I (italic)
    - ARIA labels nos botões
    - Focus management

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador abre editor de template
    2. Toolbar com opções de formatação no topo
    3. Área de edição com texto do template
    4. Digita e formata conforme necessário
    5. Insere variáveis via dropdown ou {{
    6. Preview atualiza em tempo real
    7. Salva quando satisfeito
  
  Toolbar:
    Layout:
      - Grupo 1: Bold (B), Italic (I), Link (🔗)
      - Grupo 2: Variáveis ({{}}), Emojis (😊)
      - Grupo 3: Preview (👁), Canal (WhatsApp/Email)
      - Grupo 4: Salvar, Cancelar
    
    Estados dos Botões:
      - Default: bg-transparent
      - Hover: bg-lia-interactive-hover
      - Active (formatação aplicada): bg-wedo-cyan-light
      - Disabled: opacity-50
  
  Inserção de Variáveis:
    Via Dropdown:
      - Click em {{}} abre dropdown
      - Lista de variáveis disponíveis
      - Click insere no cursor
    
    Via Autocomplete:
      - Digitar {{ dispara autocomplete
      - Filtra conforme digita
      - Enter confirma seleção
    
    Renderização:
      - Variável aparece como chip colorido
      - Ex: [{{nome}}] com bg-wedo-cyan-light
      - Não editável diretamente (delete para remover)
  
  Preview:
    Desktop:
      - Split view: editor | preview
      - Sincronizado em tempo real
    
    Mobile:
      - Toggle: Editar / Preview
      - Full width cada modo
    
    Por Canal:
      - WhatsApp: plain text com emojis
      - Email: HTML renderizado
      - Toggle para alternar
  
  Emoji Picker:
    - Click no ícone abre picker
    - Categorias: Frequentes, Smileys, Símbolos
    - Search por nome
    - Click insere no cursor
  
  Mensagens de Feedback:
    - Salvo: Toast verde "Template salvo"
    - Erro: Toast vermelho "Erro ao salvar"
    - Limite: Toast amarelo "Próximo do limite de caracteres"


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Editor WYSIWYG funcional
  - [ ] Formatação básica funciona
  - [ ] Variáveis inseríveis
  - [ ] Emojis inseríveis
  - [ ] Preview funciona
  - [ ] Versão WhatsApp e Email
  - [ ] Testes E2E passando

Criterios de Aceitacao:
  - [ ] Bold, italic, link funcionam
  - [ ] Variáveis aparecem como chips
  - [ ] Preview atualiza em tempo real
  - [ ] Salvar persiste corretamente
  - [ ] Limite de caracteres validado

Arquivos de Referencia (Prototipo Replit):
  - email-templates-manager.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/email-templates/email-templates-manager.tsx
  - recruitment_email_templates.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/recruitment_email_templates.py
  - email_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/email_service.py
```

---

### CARD TPL-006: Variáveis Dinâmicas
**Épico:** É8 — Templates de Comunicação

```yaml
Titulo: [BACKEND] Sistema de Variáveis Dinâmicas para Templates
Tipo: Feature
Area: Full-Stack
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 5
Prioridade: Alta
Epic: EPIC-TEMPLATES
Status: 📋 Pendente Jira

Descricao: |
  Implementar sistema de variáveis dinâmicas que substituem
  placeholders nos templates por dados reais do candidato,
  vaga e empresa no momento do envio.

Historia de Usuario: |
  Como sistema, eu preciso substituir variáveis nos templates
  pelos dados corretos antes de enviar a mensagem, para
  personalizar a comunicação automaticamente.

Regras de Negocio:
  1. Variáveis no formato {{nome_variavel}}
  2. Case insensitive: {{Nome}} = {{nome}}
  3. Fallback para valor vazio se dado não existe
  4. Validar variáveis conhecidas ao salvar template
  5. Log de variáveis não encontradas
  6. Suporte a formatação ({{data|format:DD/MM/YYYY}})
  7. Variáveis aninhadas: {{candidato.nome}}

Requisitos Tecnicos:
  Backend:
    - TemplateRenderer class
    - VariableResolver class
    - POST /api/v1/templates/render (preview)
    - GET /api/v1/templates/variables (lista de disponíveis)
  Frontend:
    - VariableList component (lista de disponíveis)
    - VariableAutocomplete (para editor)
  Dados:
    - template_variables: id, name, description, category, example

Design & Componentes:
  Componentes Existentes:
    - Badge - variável como tag
    - Tooltip - descrição
  Novos Componentes:
    - VariableList - lista categorizadas
    - VariableChip - chip de variável no editor
  Design Tokens:
    Variable Background: --wedo-cyan-light (#E0F2FE)
    Variable Text: --wedo-cyan-dark (#0891B2)
    Border: --wedo-cyan (#60BED1)

Comportamento de UI:
  Lista de Variáveis Disponíveis:
    Candidato:
      - {{nome}} - Nome completo
      - {{primeiro_nome}} - Primeiro nome
      - {{email}} - Email
      - {{telefone}} - Telefone
      - {{cargo_atual}} - Cargo atual
      - {{empresa_atual}} - Empresa atual
    
    Vaga:
      - {{vaga}} - Título da vaga
      - {{vaga_id}} - ID da vaga
      - {{departamento}} - Departamento
      - {{local}} - Localização
      - {{modelo}} - Remoto/Híbrido/Presencial
      - {{faixa_salarial}} - Faixa salarial
    
    Empresa:
      - {{empresa}} - Nome da empresa
      - {{empresa_site}} - Website
      - {{recrutador}} - Nome do recrutador
      - {{recrutador_email}} - Email do recrutador
    
    Processo:
      - {{data_entrevista}} - Data da entrevista
      - {{hora_entrevista}} - Hora da entrevista
      - {{link_reuniao}} - Link da reunião
      - {{link_agenda}} - Link para agendar
      - {{link_triagem}} - Link para triagem
      - {{prazo_resposta}} - Prazo de resposta
    
    Score:
      - {{score_wsi}} - Score WSI
      - {{parecer_resumo}} - Resumo do parecer
  
  Resolução de Variáveis:
    Fluxo:
      1. Template: "Olá, {{primeiro_nome}}!"
      2. Contexto: { candidate: { nome: "João Silva" } }
      3. Resolver: extrair "primeiro_nome" → "João"
      4. Output: "Olá, João!"
    
    Fallback:
      - Se variável não existe: string vazia
      - Log warning para debugging
      - Não quebrar mensagem
    
    Formatação:
      - {{data_entrevista|format:DD/MM/YYYY}}
      - {{hora_entrevista|format:HH:mm}}
      - Pipes extensíveis
  
  API:
    GET /api/v1/templates/variables:
      Response:
        - Lista de variáveis disponíveis
        - Categoria, nome, descrição, exemplo
    
    POST /api/v1/templates/render:
      Body:
        - template_id ou content
        - context: { candidate_id, job_id }
      Response:
        - rendered_text
        - missing_variables (se houver)

DoD:
  - [ ] Substituição de variáveis funciona
  - [ ] Fallback para vazio
  - [ ] Formatação de datas funciona
  - [ ] Lista de variáveis disponível
  - [ ] Validação ao salvar template
  - [ ] Testes unitários passando

Criterios de Aceitacao:
  - [ ] {{nome}} substitui pelo nome
  - [ ] Variável inexistente = vazio
  - [ ] Data formatada corretamente
  - [ ] API lista variáveis
  - [ ] Preview renderiza corretamente

Arquivos de Referencia (Prototipo Replit):
  - email-template-form-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/email-templates/email-template-form-modal.tsx
  - email-templates-manager.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/email-templates/email-templates-manager.tsx
  - template-variables.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/template-variables.ts
```

---

### CARD TPL-007: Preview de Template
**Épico:** É8 — Templates de Comunicação

```yaml
Titulo: [FRONTEND] Preview Renderizado de Template
Tipo: Feature
Area: Full-Stack
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 5
Prioridade: Alta
Epic: EPIC-TEMPLATES
Status: 📋 Pendente Jira
Dependencias: TPL-005, TPL-006

Descricao: |
  Implementar componente de preview que renderiza o template
  com dados de exemplo ou dados reais de um candidato selecionado,
  mostrando exatamente como a mensagem será exibida.

Historia de Usuario: |
  Como recrutador, eu quero ver exatamente como a mensagem
  ficará antes de enviar, para garantir que está correta
  e profissional.

Regras de Negocio:
  1. Preview em tempo real enquanto edita
  2. Opção de usar dados de exemplo (fictícios)
  3. Opção de selecionar candidato real para preview
  4. Mostrar versão WhatsApp e Email
  5. Simular aparência de cada canal
  6. Destacar variáveis não resolvidas

Requisitos Tecnicos:
  Frontend:
    - TemplatePreview component
    - WhatsAppPreview (simula interface WhatsApp)
    - EmailPreview (simula email)
    - CandidateSelector (para preview com dados reais)
  Backend:
    - POST /api/v1/templates/render (reutiliza TPL-006)

Design & Componentes:
  Componentes Existentes:
    - Card - container
    - Select - seletor de candidato
    - Tabs - alternar canais
  Novos Componentes:
    - TemplatePreview - container principal
    - WhatsAppPreview - mockup de interface WhatsApp
    - EmailPreview - mockup de email
    - CandidatePreviewSelector - busca candidato para preview
  Design Tokens:
    WhatsApp Background: #E5DDD5 (cor do chat)
    WhatsApp Bubble: #DCF8C6 (verde da mensagem)
    Email Background: --lia-bg-secondary (#F9FAFB)
    Email Card: --lia-bg-primary (#FFFFFF)
    Unresolved Variable: --electric-red-light (#FEE2E2)
  Layout:
    Container: max-w-md mx-auto (simula mobile)
    WhatsApp: aspect-[9/16], rounded-2xl, shadow
    Email: max-w-lg, aspect-[4/3]
    Spacing: p-4 interno
  Estados:
    - Example (dados fictícios)
    - Real (dados de candidato)
    - Loading (buscando dados)
    - Error (variável não resolvida)
  Acessibilidade:
    - Preview é apenas visual
    - Dados anunciados via ARIA
    - Toggle acessível via keyboard

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador está editando template
    2. Preview aparece ao lado (desktop) ou abaixo (mobile)
    3. Default: dados de exemplo
    4. Toggle para selecionar candidato real
    5. Buscar candidato atualiza preview
    6. Tabs para alternar WhatsApp/Email
    7. Variáveis não resolvidas destacadas em vermelho
  
  Layout do Preview:
    Header:
      - Tabs: WhatsApp | Email
      - Toggle: Dados de exemplo | Candidato real
      - Select candidato (se toggle = real)
    
    WhatsApp Preview:
      - Simula header do app (nome da empresa)
      - Área de chat com fundo característico
      - Bolha de mensagem verde
      - Timestamp fictício
      - Ícones de status (enviado/entregue)
    
    Email Preview:
      - Simula cliente de email
      - From, To, Subject
      - Corpo do email
      - Footer com unsubscribe
  
  Dados de Exemplo:
    Candidato:
      - nome: "Maria Silva"
      - primeiro_nome: "Maria"
      - email: "maria.silva@email.com"
      - cargo_atual: "Analista de Dados"
    
    Vaga:
      - vaga: "Desenvolvedor Python Senior"
      - empresa: "TechCorp"
      - local: "São Paulo, SP (Remoto)"
    
    Processo:
      - data_entrevista: "15/02/2026"
      - hora_entrevista: "14:00"
      - link_reuniao: "https://meet.example.com/xyz"
  
  Selecionar Candidato Real:
    Click em toggle → "Candidato real":
      - Aparece campo de busca
      - Digita nome → autocomplete
      - Seleciona candidato
      - Preview atualiza com dados reais
    
    Benefício:
      - Validar que todos os dados existem
      - Ver exatamente como candidato receberá
  
  Variáveis Não Resolvidas:
    Se variável sem valor:
      - Texto: "{{variavel}}" em vermelho
      - Background: red-light
      - Tooltip: "Variável não encontrada"
    
    No topo:
      - Warning: "2 variáveis não resolvidas"
      - Lista das variáveis com problema
  
  Mensagens de Feedback:
    - Loading candidato: Skeleton no preview
    - Erro: Toast vermelho "Erro ao carregar dados"
    - Variáveis missing: Warning inline


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

DoD:
  - [ ] Preview em tempo real
  - [ ] WhatsApp mockup
  - [ ] Email mockup
  - [ ] Dados de exemplo
  - [ ] Dados de candidato real
  - [ ] Variáveis não resolvidas destacadas
  - [ ] Testes E2E passando

Criterios de Aceitacao:
  - [ ] Preview atualiza enquanto edita
  - [ ] WhatsApp parece WhatsApp
  - [ ] Email parece email
  - [ ] Candidato real carrega dados
  - [ ] Missing variables destacadas

Arquivos de Referencia (Prototipo Replit):
  - template-variables.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/template-variables.ts
  - email-template-form-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/email-templates/email-template-form-modal.tsx
  - recruitment_email_templates.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/recruitment_email_templates.py
```

---

### CARD TPL-008: Sincronização de Templates WhatsApp com Meta
**Épico:** É8 — Templates de Comunicação

```yaml
Titulo: "[FULL-STACK] Sincronização de Templates WhatsApp com Meta Business Manager"
Tipo: Feature (Backend + Frontend)
Area: Integração
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 8
Prioridade: Alta
Epic: EPIC-TEMPLATES
Status: 📋 A Criar no Jira
Dependencias: TPL-001, TRI-001

Descricao: |
  Sincronização bidirecional entre os templates de WhatsApp da plataforma
  e o Meta Business Manager. Templates criados na plataforma são submetidos
  ao Meta para aprovação. Status de aprovação (Pending, Approved, Rejected)
  é atualizado via webhook. Suporte ao formato de variáveis Meta ({{1}}, {{2}}).

Historia de Usuario: |
  Como admin, eu quero que os templates de WhatsApp criados na plataforma
  sejam automaticamente submetidos ao Meta para aprovação, e que eu possa
  ver o status de aprovação em tempo real.

Regras de Negocio:
  1. Templates criados na plataforma são submetidos ao Meta Business Manager
  2. Status de aprovação: Pendente Meta, Aprovado, Rejeitado
  3. Motivo de rejeição exibido quando rejeitado pelo Meta
  4. Webhook recebe atualizações de status do Meta
  5. Suporte ao formato de variáveis Meta: {{1}}, {{2}}, {{3}}
  6. Re-submissão possível após correção de template rejeitado
  7. Sync automático ao salvar template na plataforma

Requisitos Tecnicos:
  Backend:
    - MetaTemplateSyncService class
    - WhatsApp Business Management API integration
    - Webhook endpoint para status updates do Meta
    - Tabela whatsapp_template_sync: id, template_id, meta_template_id, status (pending/approved/rejected), rejection_reason, submitted_at, updated_at
    - POST /api/v1/templates/{id}/submit-to-meta
    - GET /api/v1/templates/{id}/meta-status
  Frontend:
    - Badge de status Meta no editor de templates (Pendente Meta, Aprovado, Rejeitado)
    - Exibição de motivo de rejeição quando rejeitado
    - Botão "Re-submeter" para templates rejeitados
  Dados:
    - whatsapp_template_sync: id, template_id, meta_template_id, status, rejection_reason, submitted_at, updated_at
  Validacoes:
    - Variáveis no formato {{N}} validadas antes de submissão
    - Conteúdo dentro dos limites do Meta (1024 chars)

Integracoes Externas:
  WhatsApp Business Management API:
    - Endpoint: graph.facebook.com/v18.0/{waba_id}/message_templates
    - Tipo: REST API
    - Autenticação: Bearer token (System User Token)
    - Webhook: Recebe atualizações de status de templates
    - Documentacao: https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates

  API Contract Details:
    Submit Template:
      Method: POST
      URL: graph.facebook.com/v18.0/{{waba_id}}/message_templates
      Headers:
        Authorization: Bearer {{system_user_token}}
        Content-Type: application/json
      Body: |
        {
          "name": "{{template_name}}",
          "language": "pt_BR",
          "category": "MARKETING|UTILITY|AUTHENTICATION",
          "components": [
            {
              "type": "HEADER",
              "format": "TEXT",
              "text": "{{header_text}}"
            },
            {
              "type": "BODY",
              "text": "{{body_text_with_variables}}"
            },
            {
              "type": "FOOTER",
              "text": "{{footer_text}}"
            }
          ]
        }
      Response: |
        { "id": "meta_template_id", "status": "PENDING", "category": "..." }
    Get Status:
      Method: GET
      URL: graph.facebook.com/v18.0/{{meta_template_id}}
      Response: |
        { "id": "...", "status": "APPROVED|REJECTED|PENDING", "rejected_reason": "..." }
    Webhook Events:
      Subscription: message_template_status_update
      Payload: |
        {
          "entry": [{
            "changes": [{
              "field": "message_template_status_update",
              "value": {
                "event": "APPROVED|REJECTED",
                "message_template_id": "...",
                "message_template_name": "...",
                "reason": "..." 
              }
            }]
          }]
        }
    Required Scopes:
      - whatsapp_business_management
      - whatsapp_business_messaging
    Rate Limits:
      - 200 templates per WABA
      - 10 requests/second

Design & Componentes:
  Componentes Existentes:
    - EmailTemplatesManager - gerenciador de templates existente
    - EmailTemplateFormModal - modal de edição de template
    - Badge - indicadores de status
    - Button - ações
  Novos Componentes:
    - MetaStatusBadge - badge com cores por status Meta
    - RejectionReasonDisplay - exibição do motivo de rejeição
    - ResubmitButton - botão de re-submissão
  Design Tokens:
    Pending: --wedo-yellow (#EAB308)
    Approved: --wedo-green (#22C55E)
    Rejected: --electric-red (#de1c31)
    Badge Background Pending: bg-yellow-100
    Badge Background Approved: bg-green-100
    Badge Background Rejected: bg-red-100
  Layout:
    Badge: inline-flex, rounded-full, px-2.5 py-0.5
    RejectionReason: border-l-4 border-red, bg-red-50, p-3
  Estados:
    - Not Submitted (sem badge)
    - Pending (badge amarelo pulsando)
    - Approved (badge verde estático)
    - Rejected (badge vermelho + motivo)
  Acessibilidade:
    - ARIA-label no badge com status completo
    - Motivo de rejeição anunciado por screen readers

Comportamento de UI:
  Fluxo Principal:
    1. Admin cria/edita template de WhatsApp na plataforma
    2. Ao salvar, template é automaticamente submetido ao Meta
    3. Badge "Pendente Meta" aparece (amarelo, pulsando)
    4. Webhook recebe atualização do Meta
    5a. Se aprovado: badge muda para "Aprovado" (verde)
    5b. Se rejeitado: badge muda para "Rejeitado" (vermelho) + motivo exibido
    6. Se rejeitado: admin corrige e clica "Re-submeter"

  Layout:
    Badge: Ao lado do nome do template no editor
    RejectionReason: Abaixo do editor, em destaque

  Mensagens de Feedback:
    Submetido: "Template submetido ao Meta para aprovação. Aguarde..."
    Aprovado: "Template aprovado pelo Meta! Pronto para uso."
    Rejeitado: "Template rejeitado pelo Meta. Motivo: {{reason}}"

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md (Seções: 2.6 Badges & Tags, 2.1 Botões, 2.8 Toasts & Alerts)"
  Figma: "Seção 8.2 — Meta Template Sync"
  Assets:
    - "Ícone Meta/WhatsApp"
  Tokens:
    - "--wedo-yellow (#EAB308)"
    - "--wedo-green (#22C55E)"
    - "--electric-red (#de1c31)"

DoD:
  - [ ] MetaTemplateSyncService funcional
  - [ ] Submissão de template ao Meta via API
  - [ ] Webhook recebendo atualizações de status
  - [ ] Badge de status renderizando corretamente
  - [ ] Motivo de rejeição exibido quando aplicável
  - [ ] Re-submissão funcional
  - [ ] Variáveis {{N}} validadas

Criterios de Aceitacao:
  - [ ] Template salvo na plataforma → submetido ao Meta automaticamente
  - [ ] Badge de status atualiza conforme resposta do Meta
  - [ ] Motivo de rejeição visível ao admin
  - [ ] Re-submissão após correção funciona
  - [ ] Variáveis Meta ({{1}}, {{2}}) são preservadas e validadas

Arquivos de Referencia (Prototipo Replit):
  - email-templates-manager: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/email-templates/email-templates-manager.tsx
  - email-template-form-modal: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/email-templates/email-template-form-modal.tsx
```

---

## RESUMO DOS CARDS

### ÉPICO 6: Score WSI (8 cards)
| Card | Pontos | Tipo | Prioridade |
|------|--------|------|------------|
| SCO-001 | 13 | AI | 📋 Pendente |
| SCO-002 | 8 | AI | 📋 Pendente |
| SCO-003 | 8 | AI | 📋 Pendente |
| SCO-004 | 8 | AI | Alta |
| SCO-005 | 8 | Frontend | Alta |
| SCO-006 | 5 | Frontend | Média |
| SCO-007 | 13 | Full-Stack | Alta |
| SCO-008 | 5 | Backend | Média |
| **Total** | **68** | | |

### ÉPICO 7: Gates de Aprovação (7 cards)
| Card | Pontos | Tipo | Prioridade |
|------|--------|------|------------|
| GAT-001 | 8 | Full-Stack | Crítica |
| GAT-002 | 8 | Full-Stack | Crítica |
| GAT-003 | 5 | Frontend | Alta |
| GAT-004 | 8 | AI | Alta |
| GAT-005 | 5 | Backend | Alta |
| GAT-006 | 5 | Full-Stack | 📋 Pendente |
| GAT-007 | 5 | Backend | Média |
| **Total** | **44** | | |

### ÉPICO 8: Templates de Comunicação (7 cards)
| Card | Pontos | Tipo | Prioridade |
|------|--------|------|------------|
| TPL-001 | 5 | Full-Stack | 📋 Pendente |
| TPL-002 | 5 | Full-Stack | 📋 Pendente |
| TPL-003 | 3 | Full-Stack | Média |
| TPL-004 | 3 | Full-Stack | Média |
| TPL-005 | 8 | Frontend | 📋 Pendente |
| TPL-006 | 5 | Backend | 📋 Pendente |
| TPL-007 | 5 | Frontend | 📋 Pendente |
| **Total** | **34** | | |

---

## TOTAIS CONSOLIDADOS

| Épico | Cards | Pontos | Sprints |
|-------|-------|--------|---------|
| ÉPICO 6: Score WSI | 8 | 68 | 4-5 |
| ÉPICO 7: Gates de Aprovação | 7 | 44 | 5 |
| ÉPICO 8: Templates | 7 | 34 | 5-6 |
| **TOTAL** | **22** | **146** | 4-6 |

---

> **Arquivo temporário para merge com docs/lia-mvp-cards-jira.md**

## ÉPICO 9: AGENDAMENTO AUTOMÁTICO - CARDS JIRA

---

### CARD AGE-001: Integração Microsoft Graph
**Épico:** É9 — Agendamento Automático

```yaml
Titulo: [INTEGRAÇÃO] Microsoft Graph OAuth e Calendar API
Tipo: Integração
Area: Integração
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 13
Prioridade: Alta
Epic: EPIC-AGE-001
Status: 📋 Pendente Jira

Descricao: |
  Implementar integração completa com Microsoft Graph API para
  autenticação OAuth 2.0 e acesso ao Calendar API. Permitir que
  recrutadores conectem suas contas Microsoft/Office 365 para
  sincronização de calendário e agendamento de entrevistas.

Historia de Usuario: |
  Como recrutador, eu quero conectar minha conta Microsoft
  para que a LIA possa acessar meu calendário e agendar
  entrevistas automaticamente nos horários disponíveis.

Regras de Negocio:
  1. OAuth 2.0 com consentimento do usuário (delegated permissions)
  2. Escopos requeridos: Calendars.ReadWrite, OnlineMeetings.ReadWrite
  3. Refresh token com renovação automática
  4. Múltiplos calendários por empresa (cada recrutador pode conectar)
  5. Desconexão a qualquer momento pelo usuário
  6. Fallback para agendamento manual se sem integração

Requisitos Tecnicos:
  Backend:
    - POST /api/backend-proxy/integrations/microsoft/auth (inicia OAuth)
    - GET /api/backend-proxy/integrations/microsoft/callback (callback OAuth)
    - POST /api/backend-proxy/integrations/microsoft/refresh (renova token)
    - DELETE /api/backend-proxy/integrations/microsoft/disconnect
    - GET /api/backend-proxy/integrations/microsoft/status
  Frontend:
    - MicrosoftConnectButton component
    - IntegrationStatusCard component
    - OAuth popup/redirect flow
  Dados:
    - microsoft_integrations: id, user_id, company_id, access_token, refresh_token, expires_at, scopes, email, created_at
  Validacoes:
    - Token expiration check antes de cada chamada
    - Retry com refresh em caso de 401

Integracoes Externas:
  Microsoft Graph API:
    - Tipo: OAuth 2.0 / REST API
    - Base URL: https://graph.microsoft.com/v1.0
    - Auth URL: https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize
    - Token URL: https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token
    - Secrets Configurados:
      - AZURE_CLIENT_ID (App Registration ID)
      - AZURE_CLIENT_SECRET (Client Secret)
      - AZURE_TENANT_ID (Tenant ID ou "common" para multi-tenant)
    - Redirect URI: https://{domain}/api/integrations/microsoft/callback
    - Scopes: Calendars.ReadWrite, OnlineMeetings.ReadWrite, User.Read
    - Rate Limits: 10,000 requests per 10 minutes per app
    - Custo: Gratuito (parte do Office 365)

Design & Componentes:
  Componentes Existentes:
    - Button - conectar/desconectar
    - Card - container de status
    - Badge - status da conexão
    - Dialog - confirmação de desconexão
    - Toast - feedback de ações (sonner)
  Novos Componentes:
    - MicrosoftConnectButton - botão com logo Microsoft
    - IntegrationStatusCard - card mostrando status da integração
    - OAuthPopup - gerenciamento de popup OAuth
  Design Tokens:
    Background: --lia-bg-primary (#FFFFFF)
    Border: --lia-border-subtle (#E5E7EB)
    Microsoft Blue: #0078D4
    Success: --wedo-green (#10B981)
    Error: --electric-red (#de1c31)
  Layout:
    Container: Card com padding-6
    Status: Badge inline com ícone
    Actions: Botões alinhados à direita
  Estados:
    - Não conectado (botão "Conectar Microsoft")
    - Conectando (loading spinner)
    - Conectado (badge verde + email + botão desconectar)
    - Erro (badge vermelho + mensagem + retry)
  Acessibilidade:
    - Botões com aria-label descritivo
    - Status anunciado para screen readers
    - Focus management no retorno do popup OAuth

Comportamento de UI:
  Fluxo Principal:
    1. Usuário clica "Conectar Microsoft"
    2. Popup OAuth abre (ou redirect em mobile)
    3. Usuário faz login e consente permissões
    4. Callback processa tokens
    5. Popup fecha e status atualiza para "Conectado"
    6. Toast de sucesso "Conta Microsoft conectada"
  
  Estados de Botoes:
    Conectar:
      - Default: bg-[#0078D4] (Microsoft blue), texto branco, ícone Microsoft
      - Hover: bg-[#106EBE] (Microsoft blue hover)
      - Loading: spinner + "Conectando..."
      - Disabled: durante OAuth flow
    Desconectar:
      - Default: bg-transparent, borda --lia-border-subtle, texto --lia-text-secondary
      - Hover: borda --electric-red, texto --electric-red
      - Loading: spinner durante desconexão
  
  Validacoes Inline:
    Conexão:
      - Sucesso: Badge verde "Conectado" + email da conta
      - Erro: Badge vermelho "Falha na conexão" + botão retry
      - Expirado: Badge laranja "Token expirado" + "Reconectar"
  
  Mensagens de Feedback:
    - Sucesso: Toast verde "Conta Microsoft conectada com sucesso"
    - Erro OAuth: Toast vermelho "Falha na autorização. Tente novamente."
    - Desconectado: Toast verde "Conta Microsoft desconectada"
    - Token expirado: Toast laranja "Sessão expirada. Reconecte sua conta."

DoD (Definition of Done):
  - [ ] OAuth flow completo funcionando
  - [ ] Tokens armazenados de forma segura (encrypted)
  - [ ] Refresh automático de tokens
  - [ ] Status de conexão visível no UI
  - [ ] Desconexão funciona corretamente
  - [ ] Testes unitários passando
  - [ ] Testes de integração com Graph API

Criterios de Aceitacao:
  - [ ] Usuário consegue conectar conta Microsoft
  - [ ] OAuth popup funciona em desktop e mobile
  - [ ] Token refresh acontece automaticamente
  - [ ] Status mostra email conectado
  - [ ] Desconexão remove tokens do sistema
  - [ ] Erro de OAuth mostra mensagem clara

Arquivos de Referencia (Prototipo Replit):
  - microsoft_graph_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/microsoft_graph_service.py
  - graph_client.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/graph_client.py
  - calendar_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/calendar_service.py
  - calendar.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/calendar.py
```

---

### CARD AGE-002: Consulta de Disponibilidade
**Épico:** É9 — Agendamento Automático

```yaml
Titulo: [BACKEND] Consulta de Disponibilidade (Busy/Free)
Tipo: Backend
Area: Backend
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 8
Prioridade: Alta
Epic: EPIC-AGE-001
Status: 📋 Pendente Jira
Dependencias: AGE-001

Descricao: |
  Implementar serviço para consultar disponibilidade do calendário
  do recrutador via Microsoft Graph API. Retornar slots livres
  considerando horário comercial, eventos existentes e preferências.

Historia de Usuario: |
  Como LIA, eu preciso consultar a disponibilidade do recrutador
  para sugerir horários válidos para entrevistas, evitando
  conflitos com compromissos existentes.

Regras de Negocio:
  1. Consultar calendário principal do recrutador
  2. Considerar apenas horário comercial (configurável, default 9h-18h)
  3. Respeitar duração padrão de entrevista (30min, 45min, 1h - configurável)
  4. Buffer entre reuniões (15min antes e depois)
  5. Ignorar eventos marcados como "Tentative"
  6. Lookahead de 14 dias (configurável)
  7. Timezone do recrutador respeitado

Requisitos Tecnicos:
  Backend:
    - GET /api/backend-proxy/scheduling/availability
      - Query: recruiter_id, start_date, end_date, duration_minutes
      - Response: array de slots disponíveis
    - GET /api/backend-proxy/scheduling/settings
    - PUT /api/backend-proxy/scheduling/settings
  Frontend:
    - SchedulingSettingsForm component (horário comercial, duração, buffer)
  Dados:
    - scheduling_settings: id, user_id, work_hours_start, work_hours_end, default_duration, buffer_minutes, timezone, lookahead_days
    - cached_availability: id, user_id, date, slots_json, fetched_at (cache 5min)
  Validacoes:
    - Token Microsoft válido
    - Datas dentro do lookahead permitido
    - Duration mínimo 15min, máximo 2h

Integracoes Externas:
  Microsoft Graph Calendar API:
    - Endpoint: GET /me/calendar/getSchedule
    - Request Body:
      schedules: [email]
      startTime: { dateTime, timeZone }
      endTime: { dateTime, timeZone }
      availabilityViewInterval: 30
    - Response: scheduleItems com status (busy, tentative, free, oof, workingElsewhere)
    - Alternativa: GET /me/calendarView para eventos detalhados
    - Rate Limit: 10,000 req/10min

Design & Componentes:
  Componentes Existentes:
    - Input - campos numéricos (horários, duração)
    - Select - timezone
    - Switch - configurações on/off
    - Card - container de configurações
    - Button - salvar
  Novos Componentes:
    - TimeRangePicker - seletor de horário comercial (09:00 - 18:00)
    - DurationSelect - seletor de duração padrão (30min, 45min, 1h)
    - TimezoneSelect - seletor de timezone com busca
  Design Tokens:
    Background: --lia-bg-secondary (#F9FAFB)
    Border: --lia-border-subtle (#E5E7EB)
    Accent: --wedo-cyan (#60BED1)
  Layout:
    Container: Card max-w-lg
    Form: Grid 2 colunas para campos de horário
    Spacing: gap-4 entre seções
  Estados:
    - Loading (skeleton durante fetch de settings)
    - Saved (checkmark verde)
    - Error (mensagem de erro)
  Acessibilidade:
    - Labels em todos os campos
    - Timezone com autocomplete acessível

Comportamento de UI:
  Fluxo Principal:
    1. Administrador acessa configurações de agendamento
    2. Sistema carrega configurações atuais (ou defaults)
    3. Usuário ajusta horário comercial (ex: 09:00 - 18:00)
    4. Usuário define duração padrão (ex: 45min)
    5. Usuário define buffer (ex: 15min)
    6. Autosave com debounce 1s
    7. Toast confirma "Configurações salvas"
  
  Estados de Botoes:
    Salvar (se não autosave):
      - Default: bg-wedo-cyan
      - Hover: bg-wedo-cyan-hover
      - Loading: spinner + "Salvando..."
      - Disabled: nenhuma alteração
  
  Mensagens de Feedback:
    - Sucesso: Toast verde "Configurações de agendamento salvas"
    - Erro: Toast vermelho "Erro ao salvar configurações"
    - Validação: Inline "Horário inválido" se fim < início

DoD (Definition of Done):
  - [ ] API de disponibilidade retorna slots corretos
  - [ ] Horário comercial respeitado
  - [ ] Buffer entre reuniões aplicado
  - [ ] Cache de 5min implementado
  - [ ] Configurações editáveis pelo usuário
  - [ ] Testes unitários passando

Criterios de Aceitacao:
  - [ ] Slots retornados estão realmente livres no calendário
  - [ ] Eventos "busy" são excluídos dos slots
  - [ ] Timezone corretamente aplicado
  - [ ] Performance < 500ms para 14 dias
  - [ ] Cache evita chamadas repetidas

Arquivos de Referencia (Prototipo Replit):
  - scheduling_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/scheduling_service.py
  - calendar_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/calendar_service.py
  - calendar.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/calendar.py
```

---

### CARD AGE-003: Sugestão de Horários (AI)
**Épico:** É9 — Agendamento Automático

```yaml
Titulo: [AI] Sugestão Inteligente de Horários
Tipo: AI
Area: Backend-IA
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 8
Prioridade: Alta
Epic: EPIC-AGE-001
Status: 📋 Pendente Jira
Dependencias: AGE-002

Descricao: |
  Implementar lógica de IA para sugerir os melhores horários
  de entrevista considerando disponibilidade do recrutador,
  preferências do candidato (quando informadas) e padrões
  de confirmação históricos.

Historia de Usuario: |
  Como LIA, eu quero sugerir os 3 melhores horários para
  entrevista considerando a disponibilidade e otimizando
  a chance de confirmação pelo candidato.

Regras de Negocio:
  1. Sempre sugerir 3 opções de horário
  2. Priorizar horários com maior taxa de confirmação histórica
  3. Evitar horários logo após almoço (13h-14h) e fim do dia (após 17h)
  4. Considerar preferências do candidato se informadas
  5. Distribuir sugestões em dias diferentes quando possível
  6. Peso maior para manhãs (9h-12h) baseado em dados

Requisitos Tecnicos:
  Backend:
    - POST /api/backend-proxy/scheduling/suggest
      - Body: recruiter_id, candidate_id, job_id, duration_minutes
      - Response: array de 3 slots sugeridos com score
    - GET /api/backend-proxy/scheduling/patterns (analytics)
  AI:
    - Modelo: Regras heurísticas + ML simples para ranking
    - Features: hora do dia, dia da semana, taxa confirmação histórica
    - Output: slots rankeados por probabilidade de confirmação
  Dados:
    - interview_confirmations: id, scheduled_at, confirmed, day_of_week, hour_of_day
    - candidate_preferences: id, candidate_id, preferred_times (morning/afternoon/evening)

Integracoes Externas:
  Nenhuma adicional (usa dados internos + AGE-002)

Design & Componentes:
  Componentes Existentes:
    - Card - container de sugestões
    - Button - selecionar horário
    - Badge - indicador de "Recomendado"
    - RadioGroup - seleção de horário
  Novos Componentes:
    - TimeSlotCard - card de horário com data, hora, indicador de recomendação
    - TimeSlotPicker - lista de 3 slots para seleção
  Design Tokens:
    Recommended: --wedo-cyan (#60BED1) com badge
    Normal: --lia-bg-secondary (#F9FAFB)
    Selected: borda --wedo-cyan 2px
  Layout:
    Container: flex flex-col gap-3
    Slot Card: padding-4, rounded-lg, hover state
  Estados:
    - Loading (skeleton de 3 cards)
    - Slots disponíveis (3 opções)
    - Nenhum slot (mensagem + ação manual)
    - Selecionado (borda destaque)
  Acessibilidade:
    - RadioGroup com keyboard navigation
    - Labels com data completa para screen readers

Comportamento de UI:
  Fluxo Principal:
    1. LIA precisa sugerir horários para candidato
    2. Sistema chama API de sugestão
    3. Retorna 3 slots ordenados por score
    4. Primeiro slot tem badge "Recomendado"
    5. Candidato seleciona um slot (via WhatsApp ou portal)
    6. Slot selecionado é confirmado
  
  Estados de Botoes:
    Slot Card:
      - Default: bg-lia-bg-secondary, borda sutil
      - Hover: borda --wedo-cyan light
      - Selected: borda --wedo-cyan 2px, bg-wedo-cyan-light
      - Disabled: opacity-50 (slot expirado)
  
  Mensagens de Feedback:
    - Loading: "Buscando melhores horários..."
    - Sucesso: Lista de 3 slots com indicador de recomendação
    - Nenhum slot: "Nenhum horário disponível nos próximos 14 dias"
    - Erro: "Erro ao buscar disponibilidade"

DoD (Definition of Done):
  - [ ] API retorna 3 slots ordenados
  - [ ] Algoritmo de ranking implementado
  - [ ] Horários "ruins" evitados (13h-14h, >17h)
  - [ ] Badge de recomendação no melhor slot
  - [ ] Analytics de padrões coletando dados
  - [ ] Testes unitários passando

Criterios de Aceitacao:
  - [ ] 3 slots retornados em ordem de preferência
  - [ ] Slots distribuídos em dias diferentes
  - [ ] Horários de pico evitados
  - [ ] Performance < 300ms
  - [ ] Fallback para slots aleatórios se modelo falhar

Arquivos de Referencia (Prototipo Replit):
  - scheduling_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/scheduling_service.py
  - autonomous_agent_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/autonomous_agent_service.py
  - calendar_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/calendar_service.py
```

---

### CARD AGE-004: Criação de Evento Teams
**Épico:** É9 — Agendamento Automático

```yaml
Titulo: [BACKEND] Criação de Evento com Link Teams
Tipo: Backend
Area: Backend
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 8
Prioridade: Alta
Epic: EPIC-AGE-001
Status: 📋 Pendente Jira
Dependencias: AGE-001

Descricao: |
  Implementar criação automática de evento no calendário do
  recrutador com geração de link do Microsoft Teams para
  reunião online. Incluir todos os participantes e detalhes
  da entrevista.

Historia de Usuario: |
  Como LIA, eu preciso criar automaticamente um evento de
  entrevista no calendário do recrutador com link do Teams,
  incluindo candidato como participante.

Regras de Negocio:
  1. Criar evento no calendário principal do recrutador
  2. Gerar link do Teams automaticamente (onlineMeeting)
  3. Adicionar candidato como attendee (email obrigatório)
  4. Incluir título padrão: "Entrevista - [Nome Candidato] - [Nome Vaga]"
  5. Incluir descrição com contexto da vaga e link do perfil
  6. Enviar convite automático para todos os participantes
  7. Duração conforme configuração do recrutador

Requisitos Tecnicos:
  Backend:
    - POST /api/backend-proxy/scheduling/create-event
      - Body: recruiter_id, candidate_id, job_id, slot (datetime), duration_minutes
      - Response: event_id, teams_link, ical_link
    - GET /api/backend-proxy/scheduling/event/{event_id}
    - DELETE /api/backend-proxy/scheduling/event/{event_id}
  Dados:
    - scheduled_interviews: id, recruiter_id, candidate_id, job_id, event_id (MS), teams_link, scheduled_at, duration, status (scheduled/confirmed/cancelled)

Integracoes Externas:
  Microsoft Graph Events API:
    - POST /me/events
    - Request Body:
      subject: string
      body: { contentType: "HTML", content: string }
      start: { dateTime, timeZone }
      end: { dateTime, timeZone }
      attendees: [{ emailAddress: { address, name }, type: "required" }]
      isOnlineMeeting: true
      onlineMeetingProvider: "teamsForBusiness"
    - Response: id, webLink, onlineMeeting.joinUrl
    - Permissions: Calendars.ReadWrite, OnlineMeetings.ReadWrite

Design & Componentes:
  Componentes Existentes:
    - Card - confirmação do evento
    - Button - ações (ver no calendar, copiar link)
    - Badge - status do evento
  Novos Componentes:
    - EventConfirmationCard - card com detalhes do evento criado
    - TeamsLinkCopy - botão de copiar link Teams
  Design Tokens:
    Success: --wedo-green (#10B981)
    Teams Purple: #6264A7
    Background: --lia-bg-primary (#FFFFFF)
  Layout:
    Card: padding-6, ícone de calendário, detalhes do evento
    Link: input readonly + botão copiar
  Estados:
    - Creating (spinner)
    - Created (detalhes + link)
    - Error (mensagem + retry)
  Acessibilidade:
    - Link copiável com feedback de "Copiado"
    - Detalhes do evento legíveis por screen readers

Comportamento de UI:
  Fluxo Principal:
    1. Candidato confirma horário sugerido
    2. Sistema chama API de criação de evento
    3. Evento criado no calendário do recrutador
    4. Link Teams gerado
    5. Convite enviado automaticamente
    6. Confirmação exibida com link Teams
  
  Estados de Botoes:
    Copiar Link:
      - Default: bg-transparent, ícone copy
      - Hover: bg-lia-interactive-hover
      - Clicked: ícone check + "Copiado!" por 2s
    Ver no Calendário:
      - Default: link azul sublinhado
      - Hover: underline mais escuro
  
  Mensagens de Feedback:
    - Sucesso: Toast verde "Entrevista agendada com sucesso!"
    - Erro criação: Toast vermelho "Erro ao criar evento. Tente novamente."
    - Erro permissão: Toast vermelho "Sem permissão para criar eventos. Reconecte sua conta Microsoft."

DoD (Definition of Done):
  - [ ] Evento criado corretamente no calendário
  - [ ] Link Teams funcional gerado
  - [ ] Convite enviado aos participantes
  - [ ] Dados salvos no banco local
  - [ ] Testes de integração passando

Criterios de Aceitacao:
  - [ ] Evento aparece no Outlook/Calendar do recrutador
  - [ ] Link Teams abre reunião corretamente
  - [ ] Candidato recebe email de convite
  - [ ] Duração correta conforme configuração
  - [ ] Título e descrição corretos

Arquivos de Referencia (Prototipo Replit):
  - teams_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/teams_service.py
  - microsoft_graph_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/microsoft_graph_service.py
  - teams.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/teams.py
```

---

### CARD AGE-005: Confirmação do Candidato
**Épico:** É9 — Agendamento Automático

```yaml
Titulo: [FULL-STACK] Confirmação do Candidato via WhatsApp
Tipo: Full-Stack
Area: Full-Stack
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 8
Prioridade: Alta
Epic: EPIC-AGE-001
Status: 📋 Pendente Jira
Dependencias: AGE-003, AGE-004, TRI-001

Descricao: |
  Implementar fluxo de confirmação de entrevista pelo candidato
  via WhatsApp. LIA envia opções de horário, candidato responde
  com número da opção, sistema confirma e cria evento.

Historia de Usuario: |
  Como candidato, eu quero escolher um horário de entrevista
  de forma simples via WhatsApp, recebendo confirmação
  imediata com link da reunião.

Regras de Negocio:
  1. LIA envia mensagem com 3 opções de horário numeradas
  2. Candidato responde com número (1, 2 ou 3)
  3. Sistema valida se slot ainda está disponível
  4. Se disponível: cria evento + envia confirmação com link Teams
  5. Se indisponível: oferece novas opções
  6. Timeout de 48h para resposta (reminder após 24h)
  7. Candidato pode solicitar outros horários

Requisitos Tecnicos:
  Backend:
    - POST /api/backend-proxy/scheduling/send-options
      - Body: candidate_id, job_id, slots[]
    - POST /api/backend-proxy/scheduling/confirm
      - Body: candidate_id, selected_slot_index
    - Webhook handler para respostas WhatsApp
  Frontend:
    - SchedulingStatusCard no preview do candidato
    - Timeline de agendamento no tab Atividades
  Dados:
    - scheduling_requests: id, candidate_id, job_id, slots_offered (json), selected_slot, status (pending/confirmed/expired), sent_at, confirmed_at
  Integração:
    - Twilio WhatsApp (reusa TRI-001)

Integracoes Externas:
  Twilio WhatsApp API:
    - Reusa integração do Épico 5 (TRI-001)
    - Templates: scheduling_options, scheduling_confirmed, scheduling_reminder
    - Session messages para respostas livres

Design & Componentes:
  Componentes Existentes:
    - Card - status do agendamento
    - Badge - status (pendente/confirmado/expirado)
    - Timeline - histórico de interações
  Novos Componentes:
    - SchedulingStatusCard - card mostrando status do agendamento
    - SchedulingTimeline - timeline de eventos de agendamento
  Design Tokens:
    Pending: --wedo-yellow (#F59E0B)
    Confirmed: --wedo-green (#10B981)
    Expired: --lia-text-tertiary (#9CA3AF)
  Layout:
    Card: inline no preview lateral
    Timeline: lista vertical cronológica
  Estados:
    - Não iniciado (nenhum agendamento)
    - Opções enviadas (pendente resposta)
    - Confirmado (evento criado)
    - Expirado (sem resposta em 48h)
    - Reagendando (novo fluxo iniciado)
  Acessibilidade:
    - Status legível por screen readers
    - Timeline com timestamps acessíveis

Comportamento de UI:
  Fluxo Principal (WhatsApp):
    1. LIA envia mensagem:
       "Olá [Nome]! Seguem os horários disponíveis para sua entrevista:
       1️⃣ Segunda, 15/01 às 10:00
       2️⃣ Terça, 16/01 às 14:00
       3️⃣ Quarta, 17/01 às 11:00
       Responda com o número da sua preferência."
    2. Candidato responde: "2"
    3. Sistema valida disponibilidade
    4. Sistema cria evento Teams
    5. LIA confirma:
       "Perfeito! Sua entrevista está confirmada:
       📅 Terça, 16/01 às 14:00
       📍 Online via Microsoft Teams
       🔗 Link: [teams_link]
       Até lá!"
  
  Fluxo UI (Recrutador):
    1. Card de status mostra "Aguardando confirmação"
    2. Badge amarelo pulsando
    3. Quando confirmado: badge verde + detalhes do evento
    4. Link para evento no calendário
  
  Mensagens de Feedback:
    - WhatsApp - Slot indisponível: "Ops, esse horário acabou de ser ocupado. Veja as novas opções: [...]"
    - WhatsApp - Resposta inválida: "Não entendi. Por favor, responda com 1, 2 ou 3."
    - WhatsApp - Confirmado: Template com link Teams
    - UI - Toast: "Entrevista confirmada pelo candidato"

DoD (Definition of Done):
  - [ ] Mensagem de opções enviada corretamente
  - [ ] Resposta do candidato processada
  - [ ] Evento criado após confirmação
  - [ ] Link Teams enviado ao candidato
  - [ ] Status atualizado no UI
  - [ ] Timeout e reminder implementados
  - [ ] Testes E2E passando


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

Criterios de Aceitacao:
  - [ ] Candidato recebe 3 opções de horário
  - [ ] Resposta numérica processada corretamente
  - [ ] Slot indisponível oferece novas opções
  - [ ] Confirmação inclui link Teams funcional
  - [ ] Status atualiza em tempo real no dashboard
  - [ ] Reminder enviado após 24h sem resposta

Arquivos de Referencia (Prototipo Replit):
  - scheduling_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/scheduling_service.py
  - whatsapp_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_service.py
  - communication_dispatcher.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/communication_dispatcher.py
```

---

### CARD AGE-006: Reagendamento
**Épico:** É9 — Agendamento Automático

```yaml
Titulo: [FULL-STACK] Fluxo de Reagendamento
Tipo: Full-Stack
Area: Full-Stack
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 8
Prioridade: Media
Epic: EPIC-AGE-001
Status: 📋 Pendente Jira
Dependencias: AGE-005

Descricao: |
  Implementar fluxo completo de reagendamento de entrevista,
  permitindo que candidato ou recrutador solicitem mudança
  de data/hora. Cancelar evento antigo e criar novo.

Historia de Usuario: |
  Como candidato ou recrutador, eu quero poder reagendar
  uma entrevista já confirmada quando houver impedimento,
  sem perder o histórico de interações.

Regras de Negocio:
  1. Reagendamento permitido até 2h antes da entrevista
  2. Máximo de 2 reagendamentos por candidato
  3. Motivo obrigatório para registro
  4. Evento antigo é cancelado automaticamente
  5. Novo fluxo de sugestão de horários inicia
  6. Notificação para ambas as partes
  7. Histórico de reagendamentos mantido

Requisitos Tecnicos:
  Backend:
    - POST /api/backend-proxy/scheduling/reschedule
      - Body: interview_id, reason, requested_by (candidate/recruiter)
    - GET /api/backend-proxy/scheduling/history/{candidate_id}
  Frontend:
    - RescheduleDialog component
    - RescheduleHistoryCard component
  Dados:
    - interview_reschedules: id, interview_id, old_datetime, new_datetime, reason, requested_by, created_at
    - scheduled_interviews.reschedule_count

Integracoes Externas:
  Microsoft Graph API:
    - DELETE /me/events/{event_id} (cancelar evento antigo)
    - POST /me/events (criar novo evento)
  Twilio WhatsApp:
    - Template: interview_rescheduled
    - Mensagem informando cancelamento + novas opções

Design & Componentes:
  Componentes Existentes:
    - Dialog - modal de reagendamento
    - Textarea - campo de motivo
    - Button - confirmar/cancelar
    - Alert - aviso de limite de reagendamentos
  Novos Componentes:
    - RescheduleDialog - modal completo de reagendamento
    - RescheduleHistoryCard - histórico de reagendamentos
  Design Tokens:
    Warning: --wedo-yellow (#F59E0B)
    Danger: --electric-red (#de1c31)
    Background: --lia-bg-primary (#FFFFFF)
  Layout:
    Dialog: max-w-md, centered
    Form: textarea + select de motivo comum
    History: timeline compacta
  Estados:
    - Permitido (pode reagendar)
    - Limite atingido (máximo 2)
    - Muito tarde (<2h para entrevista)
  Acessibilidade:
    - Focus trap no dialog
    - Escape para fechar
    - Mensagens de erro anunciadas

Comportamento de UI:
  Fluxo Principal (Recrutador):
    1. Recrutador clica "Reagendar" no card do candidato
    2. Dialog abre com seletor de motivo
    3. Motivos comuns: "Conflito de agenda", "Emergência", "Solicitação do candidato", "Outro"
    4. Se "Outro": textarea para detalhar
    5. Confirma reagendamento
    6. Sistema cancela evento antigo
    7. Sistema inicia novo fluxo de sugestão
    8. Toast: "Reagendamento iniciado. Novas opções enviadas ao candidato."
  
  Fluxo WhatsApp (Candidato):
    1. Candidato envia: "Preciso reagendar"
    2. LIA responde: "Sem problemas! Qual o motivo?"
    3. Candidato informa motivo
    4. LIA: "Entendi. Vou buscar novos horários. Um momento..."
    5. LIA envia novas opções
  
  Estados de Botoes:
    Reagendar:
      - Default: bg-wedo-yellow-light, texto --wedo-yellow-dark
      - Hover: bg-wedo-yellow-light darker
      - Disabled: limite atingido ou <2h
    Confirmar:
      - Default: bg-wedo-cyan
      - Loading: spinner
  
  Mensagens de Feedback:
    - Sucesso: Toast verde "Reagendamento processado"
    - Limite: Alert vermelho "Limite de 2 reagendamentos atingido"
    - Muito tarde: Alert laranja "Não é possível reagendar com menos de 2h de antecedência"

DoD (Definition of Done):
  - [ ] Fluxo de reagendamento funciona para recrutador
  - [ ] Fluxo de reagendamento funciona para candidato (WhatsApp)
  - [ ] Evento antigo cancelado automaticamente
  - [ ] Novo evento criado após confirmação
  - [ ] Histórico de reagendamentos salvo
  - [ ] Limite de 2 reagendamentos aplicado
  - [ ] Notificações enviadas


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

Criterios de Aceitacao:
  - [ ] Botão "Reagendar" aparece para entrevistas agendadas
  - [ ] Modal exige motivo
  - [ ] Evento antigo removido do calendário
  - [ ] Candidato recebe novas opções
  - [ ] Terceira tentativa é bloqueada
  - [ ] <2h da entrevista bloqueia reagendamento

Arquivos de Referencia (Prototipo Replit):
  - scheduling_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/scheduling_service.py
  - calendar_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/calendar_service.py
```

---

### CARD AGE-007: Lembretes Automáticos
**Épico:** É9 — Agendamento Automático

```yaml
Titulo: [BACKEND] Lembretes Automáticos (24h e 1h)
Tipo: Backend
Area: Backend
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 5
Prioridade: Media
Epic: EPIC-AGE-001
Status: 📋 Pendente Jira
Dependencias: AGE-005

Descricao: |
  Implementar sistema de lembretes automáticos para entrevistas
  agendadas. Enviar notificação 24h antes e 1h antes da entrevista
  para candidato e recrutador.

Historia de Usuario: |
  Como candidato, eu quero receber lembretes antes da minha
  entrevista para não esquecer o compromisso e ter o link
  Teams em mãos.

Regras de Negocio:
  1. Lembrete 24h antes: enviado a candidato e recrutador
  2. Lembrete 1h antes: enviado apenas ao candidato
  3. Incluir link Teams em todos os lembretes
  4. Cancelar lembretes se entrevista for cancelada/reagendada
  5. Não enviar lembretes duplicados
  6. Timezone respeitado para cálculo de horário

Requisitos Tecnicos:
  Backend:
    - Job scheduler (cron/queue) para lembretes
    - Worker: check_interview_reminders (roda a cada 15min)
    - POST /api/backend-proxy/scheduling/reminders/send
  Dados:
    - scheduled_reminders: id, interview_id, reminder_type (24h/1h), scheduled_for, sent_at, cancelled
  Integração:
    - Twilio WhatsApp para candidato
    - Email ou notificação in-app para recrutador

Integracoes Externas:
  Twilio WhatsApp API:
    - Template: interview_reminder_24h
    - Template: interview_reminder_1h
    - Inclui link Teams
  Email (opcional):
    - Mailgun ou similar para recrutador

Design & Componentes:
  Componentes Existentes:
    - (Lembretes são background jobs, sem UI direta)
  Novos Componentes:
    - ReminderSettingsToggle - configuração para desativar lembretes (opcional futuro)
  Design Tokens:
    N/A (background job)
  Layout:
    N/A (background job)
  Estados:
    - Scheduled (agendado)
    - Sent (enviado)
    - Cancelled (cancelado devido a cancelamento/reagendamento)
  Acessibilidade:
    N/A

Comportamento de UI:
  Fluxo Principal (Background):
    1. Cron job roda a cada 15 minutos
    2. Busca entrevistas com lembrete pendente (24h ou 1h no futuro)
    3. Para cada entrevista:
       - 24h antes: envia WhatsApp para candidato + notificação para recrutador
       - 1h antes: envia WhatsApp para candidato
    4. Marca lembrete como enviado
    5. Log para auditoria
  
  Mensagem 24h (Candidato):
    "Olá [Nome]! Lembrete: sua entrevista para [Vaga] é amanhã.
    📅 [Data] às [Hora]
    📍 Online via Microsoft Teams
    🔗 Link: [teams_link]
    Nos vemos lá!"
  
  Mensagem 1h (Candidato):
    "Falta 1 hora para sua entrevista para [Vaga]!
    🔗 Link: [teams_link]
    Boa sorte!"
  
  Notificação Recrutador (24h):
    - In-app: "Entrevista com [Candidato] amanhã às [Hora]"
    - Clique leva ao perfil do candidato

DoD (Definition of Done):
  - [ ] Job scheduler configurado
  - [ ] Lembrete 24h enviado corretamente
  - [ ] Lembrete 1h enviado corretamente
  - [ ] Cancelamento remove lembretes pendentes
  - [ ] Logs de envio para auditoria
  - [ ] Testes de job scheduler passando

Criterios de Aceitacao:
  - [ ] Candidato recebe WhatsApp 24h antes
  - [ ] Candidato recebe WhatsApp 1h antes
  - [ ] Recrutador recebe notificação 24h antes
  - [ ] Link Teams incluído em todos os lembretes
  - [ ] Lembretes não enviados para entrevistas canceladas

Arquivos de Referencia (Prototipo Replit):
  - scheduling_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/scheduling_service.py
  - notification_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/notification_service.py
  - deadline_calculator_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/deadline_calculator_service.py
```

---

### CARD AGE-008: Cancelamento
**Épico:** É9 — Agendamento Automático

```yaml
Titulo: [FULL-STACK] Cancelamento de Entrevista
Tipo: Full-Stack
Area: Full-Stack
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 5
Prioridade: Media
Epic: EPIC-AGE-001
Status: 📋 Pendente Jira
Dependencias: AGE-004

Descricao: |
  Implementar fluxo de cancelamento de entrevista por recrutador
  ou candidato. Remover evento do calendário e notificar todas
  as partes envolvidas.

Historia de Usuario: |
  Como recrutador, eu quero poder cancelar uma entrevista
  quando o candidato for reprovado ou a vaga for fechada,
  notificando o candidato automaticamente.

Regras de Negocio:
  1. Cancelamento permitido a qualquer momento
  2. Motivo obrigatório para registro
  3. Evento removido do calendário Microsoft
  4. Notificação enviada ao candidato via WhatsApp
  5. Candidato movido para coluna "Reprovados" (se motivo for reprovação)
  6. Lembretes pendentes cancelados automaticamente
  7. Histórico mantido para auditoria

Requisitos Tecnicos:
  Backend:
    - DELETE /api/backend-proxy/scheduling/interview/{interview_id}
      - Body: reason, notify_candidate (boolean)
    - Webhook para cancelamento iniciado pelo candidato
  Frontend:
    - CancelInterviewDialog component
    - CancelReasonSelect component
  Dados:
    - scheduled_interviews.status = 'cancelled'
    - scheduled_interviews.cancelled_at, cancelled_by, cancel_reason

Integracoes Externas:
  Microsoft Graph API:
    - DELETE /me/events/{event_id}
    - Ou: PATCH com isCancelled: true para manter histórico
  Twilio WhatsApp:
    - Template: interview_cancelled

Design & Componentes:
  Componentes Existentes:
    - Dialog - modal de cancelamento
    - Select - motivo do cancelamento
    - Button - confirmar/voltar
    - Switch - notificar candidato
  Novos Componentes:
    - CancelInterviewDialog - modal de cancelamento
    - CancelReasonSelect - select com motivos comuns
  Design Tokens:
    Danger: --electric-red (#de1c31)
    Background: --lia-bg-primary (#FFFFFF)
    Text: --lia-text-primary (#111827)
  Layout:
    Dialog: max-w-md, centered
    Form: select + switch + textarea opcional
  Estados:
    - Confirmação pendente (dialog aberto)
    - Cancelando (loading)
    - Cancelado (fechado + toast)
  Acessibilidade:
    - Focus trap no dialog
    - Botão destrutivo com confirmação clara
    - Escape para cancelar ação

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador clica "Cancelar entrevista" no card
    2. Dialog abre com aviso: "Esta ação não pode ser desfeita"
    3. Seleciona motivo: "Candidato reprovado", "Vaga fechada", "Candidato desistiu", "Outro"
    4. Checkbox: "Notificar candidato" (marcado por padrão)
    5. Se "Outro": textarea para detalhar
    6. Confirma cancelamento
    7. Sistema remove evento do calendário
    8. Sistema envia notificação ao candidato (se marcado)
    9. Toast: "Entrevista cancelada"
  
  Estados de Botoes:
    Cancelar Entrevista (trigger):
      - Default: bg-transparent, texto --electric-red, ícone X
      - Hover: bg-electric-red-light
    Confirmar Cancelamento (dialog):
      - Default: bg-electric-red, texto branco
      - Hover: bg-electric-red-dark
      - Loading: spinner + "Cancelando..."
    Voltar:
      - Default: bg-transparent, texto --lia-text-secondary
      - Hover: bg-lia-interactive-hover
  
  Mensagens de Feedback:
    - WhatsApp Candidato: "Olá [Nome], infelizmente sua entrevista para [Vaga] foi cancelada. Agradecemos seu interesse e desejamos sucesso!"
    - Toast Sucesso: "Entrevista cancelada com sucesso"
    - Toast Erro: "Erro ao cancelar entrevista. Tente novamente."

DoD (Definition of Done):
  - [ ] Dialog de cancelamento funciona
  - [ ] Evento removido do calendário Microsoft
  - [ ] Candidato notificado via WhatsApp
  - [ ] Status atualizado para "cancelled"
  - [ ] Lembretes pendentes cancelados
  - [ ] Testes passando


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

Criterios de Aceitacao:
  - [ ] Modal exige motivo para cancelar
  - [ ] Evento desaparece do Outlook
  - [ ] Candidato recebe mensagem de cancelamento
  - [ ] Switch permite não notificar
  - [ ] Status muda para "Cancelado" no UI

Arquivos de Referencia (Prototipo Replit):
  - scheduling_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/scheduling_service.py
  - calendar_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/calendar_service.py
  - notification_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/notification_service.py
```

---

## ÉPICO 10: NOTIFICAÇÕES - CARDS JIRA

---

### CARD NOT-001: Sistema de Notificações Bell
**Épico:** É10 — Notificações

```yaml
Titulo: [FULL-STACK] Sistema de Notificações Bell (Ícone no Header)
Tipo: Full-Stack
Area: Full-Stack
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 8
Prioridade: Alta
Epic: EPIC-NOT-001
Status: 📋 Pendente Jira

Descricao: |
  Implementar sistema completo de notificações com ícone de sino
  no header da aplicação. Dropdown mostra últimas notificações
  com possibilidade de marcar como lidas e navegar para contexto.

Historia de Usuario: |
  Como recrutador, eu quero ver um ícone de notificações no header
  para ficar ciente de eventos importantes sem precisar navegar
  por toda a plataforma.

Regras de Negocio:
  1. Ícone de sino sempre visível no header
  2. Badge vermelho com contador de não lidas
  3. Dropdown mostra últimas 10 notificações
  4. Clique na notificação navega para contexto
  5. Marcar individual como lida
  6. "Marcar todas como lidas" disponível
  7. Tipos: candidato_triado, entrevista_confirmada, mensagem_whatsapp, sistema

Requisitos Tecnicos:
  Backend:
    - GET /api/backend-proxy/notifications?limit=10&unread_only=false
    - PUT /api/backend-proxy/notifications/{id}/read
    - PUT /api/backend-proxy/notifications/read-all
    - GET /api/backend-proxy/notifications/unread-count
  Frontend:
    - NotificationBell component (header)
    - NotificationDropdown component
    - NotificationItem component
  Dados:
    - notifications: id, user_id, type, title, message, data (json), read_at, created_at, action_url

Integracoes Externas:
  Nenhuma (sistema interno)

Design & Componentes:
  Componentes Existentes:
    - Button - ícone de sino
    - Badge - contador
    - Dropdown - menu de notificações
    - Avatar - para notificações de candidatos
  Novos Componentes:
    - NotificationBell - botão com sino + badge
    - NotificationDropdown - dropdown com lista
    - NotificationItem - item individual de notificação
  Design Tokens:
    Badge: --electric-red (#de1c31)
    Unread Background: --wedo-cyan-light (5% opacity)
    Read Background: transparent
    Hover: --lia-interactive-hover
    Text Primary: --lia-text-primary (#111827)
    Text Secondary: --lia-text-secondary (#6B7280)
    Timestamp: --lia-text-tertiary (#9CA3AF)
  Layout:
    Bell: 40x40px, rounded-full
    Badge: 18x18px, absolute top-right, rounded-full
    Dropdown: w-80, max-h-96, overflow-y-auto
    Item: padding-3, border-bottom sutil
  Estados:
    - Sem notificações (sino vazio, sem badge)
    - Com não lidas (badge vermelho com número)
    - Dropdown aberto (lista de notificações)
    - Loading (skeleton no dropdown)
  Acessibilidade:
    - Button com aria-label "Notificações, X não lidas"
    - Dropdown com role="menu"
    - Items com role="menuitem"
    - Escape fecha dropdown
    - Arrow keys navegam itens

Comportamento de UI:
  Fluxo Principal:
    1. Usuário vê ícone de sino no header (direita)
    2. Badge vermelho mostra "5" (5 não lidas)
    3. Clica no sino → dropdown abre
    4. Últimas 10 notificações listadas (não lidas primeiro)
    5. Notificações não lidas têm fundo levemente azul
    6. Clica em uma notificação:
       - Marca como lida
       - Navega para contexto (ex: perfil do candidato)
       - Dropdown fecha
    7. "Ver todas" navega para página de histórico
  
  Tipos de Notificação:
    - candidato_triado: "[Candidato] completou triagem para [Vaga]" + ícone 📋
    - entrevista_confirmada: "Entrevista confirmada com [Candidato]" + ícone 📅
    - entrevista_cancelada: "Entrevista com [Candidato] foi cancelada" + ícone ❌
    - mensagem_whatsapp: "Nova mensagem de [Candidato]" + ícone 💬
    - sistema: "Manutenção programada para [data]" + ícone ⚙️
  
  Estados de Botoes:
    Bell:
      - Default: ícone cinza --lia-text-secondary
      - Hover: ícone --lia-text-primary
      - Active (dropdown aberto): bg-lia-interactive-hover
    Marcar Todas como Lidas:
      - Default: link azul no footer do dropdown
      - Hover: underline
    Ver Todas:
      - Default: link azul centralizado
      - Hover: underline
  
  Mensagens de Feedback:
    - Dropdown vazio: "Nenhuma notificação" com ícone de sino
    - Marcada como lida: nenhum feedback explícito (UI atualiza)
    - Todas lidas: Toast "Todas notificações marcadas como lidas"

DoD (Definition of Done):
  - [ ] Ícone de sino no header
  - [ ] Badge mostra contagem correta
  - [ ] Dropdown abre e fecha corretamente
  - [ ] Notificações listadas com scroll
  - [ ] Marcar como lida funciona
  - [ ] Navegação para contexto funciona
  - [ ] Testes unitários passando


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

Criterios de Aceitacao:
  - [ ] Badge atualiza em tempo real
  - [ ] Clique em notificação navega corretamente
  - [ ] "Marcar todas como lidas" zera badge
  - [ ] Não lidas têm destaque visual
  - [ ] Dropdown fecha ao clicar fora
  - [ ] Acessível por teclado

Arquivos de Referencia (Prototipo Replit):
  - kpi-alert-system.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/alerts/kpi-alert-system.tsx
  - alert-settings-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/alerts/alert-settings-modal.tsx
  - use-proactive-alerts.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/use-proactive-alerts.ts
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/backend-proxy/alerts/route.ts
  - notification_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/notification_service.py
```

---

### CARD NOT-002: Notificações em Tempo Real
**Épico:** É10 — Notificações

```yaml
Titulo: [BACKEND] Notificações em Tempo Real (WebSocket/SSE)
Tipo: Backend
Area: Backend
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 8
Prioridade: Alta
Epic: EPIC-NOT-001
Status: 📋 Pendente Jira
Dependencias: NOT-001

Descricao: |
  Implementar sistema de notificações em tempo real usando
  WebSocket ou Server-Sent Events (SSE). Notificações devem
  aparecer instantaneamente sem necessidade de refresh.

Historia de Usuario: |
  Como recrutador, eu quero receber notificações em tempo real
  quando um candidato responder ou uma triagem for concluída,
  sem precisar atualizar a página.

Regras de Negocio:
  1. Conexão persistente com servidor (WebSocket ou SSE)
  2. Reconexão automática em caso de queda
  3. Heartbeat a cada 30s para manter conexão viva
  4. Notificação aparece instantaneamente no sino
  5. Suporte a múltiplas abas (broadcast para todas)
  6. Fallback para polling se WebSocket falhar

Requisitos Tecnicos:
  Backend:
    - WebSocket endpoint: /ws/notifications
    - Ou SSE endpoint: /api/backend-proxy/notifications/stream
    - Pub/Sub com Redis para broadcast
    - POST /api/backend-proxy/notifications/publish (interno)
  Frontend:
    - WebSocket/SSE client com reconexão
    - useNotifications hook
    - NotificationProvider context
  Dados:
    - notification_channels: user_id, channel_id, connected_at

Integracoes Externas:
  Redis (se usar Pub/Sub):
    - Channel: notifications:{user_id}
    - Message format: { type, data }

Design & Componentes:
  Componentes Existentes:
    - Toast - para notificação visual imediata
  Novos Componentes:
    - NotificationProvider - context React
    - useNotifications - hook para consumir
    - ConnectionStatus - indicador de conexão (dev only)
  Design Tokens:
    N/A (lógica de tempo real, sem UI direta exceto toast)
  Layout:
    Toast: aparece top-right, auto-dismiss 5s
  Estados:
    - Connected (WebSocket ativo)
    - Reconnecting (tentando reconectar)
    - Disconnected (fallback para polling)
  Acessibilidade:
    - Toast com aria-live="polite"
    - Screen reader anuncia novas notificações

Comportamento de UI:
  Fluxo Principal:
    1. Usuário faz login
    2. WebSocket conecta automaticamente
    3. Servidor envia notificação quando evento ocorre
    4. Cliente recebe mensagem
    5. Badge do sino atualiza (+1)
    6. Toast aparece: "[Título da notificação]"
    7. Toast desaparece após 5s (ou click para dispensar)
  
  Reconexão:
    1. WebSocket desconecta (rede instável)
    2. Cliente tenta reconectar após 1s, 2s, 4s, 8s (exponential backoff)
    3. Se reconectar: "Conexão restaurada" (log, não toast)
    4. Se falhar após 5 tentativas: switch para polling a cada 30s
  
  Broadcast Multi-tab:
    1. Notificação recebida em uma aba
    2. Usa BroadcastChannel API para notificar outras abas
    3. Todas abas atualizam badge simultaneamente
  
  Mensagens de Feedback:
    - Toast de notificação: título + mensagem resumida + ícone por tipo
    - Toast de erro: "Problema de conexão. Tentando reconectar..." (apenas após múltiplas falhas)

DoD (Definition of Done):
  - [ ] WebSocket/SSE endpoint funcionando
  - [ ] Reconexão automática implementada
  - [ ] Badge atualiza em tempo real
  - [ ] Toast aparece para novas notificações
  - [ ] Múltiplas abas sincronizadas
  - [ ] Fallback para polling funcionando
  - [ ] Testes de conexão passando

Criterios de Aceitacao:
  - [ ] Notificação aparece em <1s após evento
  - [ ] Reconexão acontece automaticamente
  - [ ] Badge incrementa sem refresh
  - [ ] Funciona em múltiplas abas abertas
  - [ ] Sem memory leaks após múltiplas reconexões

Arquivos de Referencia (Prototipo Replit):
  - notification_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/notification_service.py
  - proactive_alert_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/proactive_alert_service.py
  - use-proactive-alerts.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/use-proactive-alerts.ts
```

---

### CARD NOT-003: Preferências de Notificação
**Épico:** É10 — Notificações

```yaml
Titulo: [FULL-STACK] Preferências de Notificação por Tipo
Tipo: Full-Stack
Area: Full-Stack
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 5
Prioridade: Media
Epic: EPIC-NOT-001
Status: 📋 Pendente Jira
Dependencias: NOT-001

Descricao: |
  Implementar tela de preferências onde usuário pode escolher
  quais tipos de notificação deseja receber e por qual canal
  (in-app, email, push).

Historia de Usuario: |
  Como recrutador, eu quero configurar quais notificações
  recebo para evitar sobrecarga de informações e focar
  no que é mais importante para mim.

Regras de Negocio:
  1. Preferências por tipo de notificação
  2. Canais: in-app (obrigatório), email (opcional), push (opcional)
  3. Algumas notificações são obrigatórias (segurança, sistema)
  4. Defaults sensatos para novos usuários
  5. Alterações aplicam imediatamente
  6. Horário de silêncio (Do Not Disturb) opcional

Requisitos Tecnicos:
  Backend:
    - GET /api/backend-proxy/notifications/preferences
    - PUT /api/backend-proxy/notifications/preferences
  Frontend:
    - NotificationPreferences page
    - PreferenceToggle component
    - DndSchedule component (Do Not Disturb)
  Dados:
    - notification_preferences: id, user_id, notification_type, in_app, email, push, created_at, updated_at
    - dnd_schedule: id, user_id, start_time, end_time, timezone

Integracoes Externas:
  Nenhuma

Design & Componentes:
  Componentes Existentes:
    - Card - container de cada categoria
    - Switch - toggles de canal
    - Select - horários DND
  Novos Componentes:
    - NotificationPreferencesForm - formulário completo
    - PreferenceRow - linha com tipo + 3 toggles
    - DndSchedulePicker - seletor de horário silencioso
  Design Tokens:
    Background: --lia-bg-secondary (#F9FAFB)
    Border: --lia-border-subtle (#E5E7EB)
    Accent: --wedo-cyan (#60BED1)
    Disabled: --lia-text-tertiary (#9CA3AF)
  Layout:
    Container: max-w-2xl mx-auto
    Categories: Cards separados por categoria
    Row: flex justify-between, tipo à esquerda, toggles à direita
  Estados:
    - Default (preferências atuais)
    - Saving (autosave)
    - Saved (checkmark discreto)
    - Locked (notificação obrigatória, toggle disabled)
  Acessibilidade:
    - Labels em todos os switches
    - Descrição de cada tipo de notificação
    - Indicação de obrigatório

Comportamento de UI:
  Fluxo Principal:
    1. Usuário acessa Configurações > Notificações
    2. Categorias listadas:
       - Candidatos: triagem_completa, mensagem_recebida, candidato_adicionado
       - Entrevistas: confirmada, cancelada, reagendada, lembrete
       - Sistema: manutencao, atualizacoes (locked)
    3. Cada linha tem 3 toggles: In-app | Email | Push
    4. Alterar toggle → autosave → indicador "Salvo"
    5. DND: "Silenciar entre [22:00] e [08:00]"
  
  Estados de Toggles:
    In-app (obrigatório):
      - Always on, disabled, com tooltip "Notificação obrigatória"
    Email:
      - Default: off
      - On: bg-wedo-cyan
    Push:
      - Default: off (requer permissão do navegador primeiro)
      - On: bg-wedo-cyan
    Locked (sistema):
      - Todos os 3 toggles disabled
      - Badge "Obrigatório" ao lado do tipo
  
  Mensagens de Feedback:
    - Autosave: Badge discreto "Salvo" por 2s
    - Erro: Toast vermelho "Erro ao salvar preferência"
    - Push sem permissão: Dialog para solicitar permissão

DoD (Definition of Done):
  - [ ] Página de preferências acessível
  - [ ] Todos os tipos de notificação listados
  - [ ] Toggles funcionam e salvam
  - [ ] Autosave implementado
  - [ ] DND schedule funciona
  - [ ] Notificações obrigatórias locked
  - [ ] Testes passando


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

Criterios de Aceitacao:
  - [ ] Toggle altera preferência em tempo real
  - [ ] Preferências persistem após reload
  - [ ] Notificações seguem preferências
  - [ ] DND bloqueia notificações no horário
  - [ ] In-app não pode ser desligado

Arquivos de Referencia (Prototipo Replit):
  - alert-settings-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/alerts/alert-settings-modal.tsx
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/backend-proxy/alerts/preferences/route.ts
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/backend-proxy/alerts/config/route.ts
```

> ⚠️ **DISCLAIMER: CARD RELACIONADO AO MENU DE CONFIGURAÇÕES**
> Este card faz parte do sistema de configurações da plataforma (Settings Menu).
> Consulte também: `docs/configuracoes-admin-cards-jira.md` para cards administrativos complementares.


---

### CARD NOT-004: Notificações Push
**Épico:** É10 — Notificações

```yaml
Titulo: [BACKEND] Notificações Push (Service Worker)
Tipo: Backend
Area: Backend
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 8
Prioridade: Media
Epic: EPIC-NOT-001
Status: 📋 Pendente Jira
Dependencias: NOT-002, NOT-003

Descricao: |
  Implementar notificações push usando Service Worker e Web Push API.
  Notificações aparecem mesmo quando o navegador está em background
  ou fechado (se permitido pelo SO).

Historia de Usuario: |
  Como recrutador, eu quero receber notificações push no meu
  computador/celular mesmo quando não estou na plataforma,
  para não perder eventos importantes.

Regras de Negocio:
  1. Solicitar permissão do navegador
  2. Respeitar preferências do usuário (NOT-003)
  3. Respeitar DND schedule
  4. Click na notificação abre a plataforma no contexto correto
  5. Suporte a Chrome, Firefox, Safari (com limitações)
  6. Fallback gracioso se não suportado

Requisitos Tecnicos:
  Backend:
    - POST /api/backend-proxy/notifications/push/subscribe
      - Body: subscription (PushSubscription object)
    - POST /api/backend-proxy/notifications/push/unsubscribe
    - Web Push library (web-push npm)
    - VAPID keys geradas
  Frontend:
    - Service Worker: sw.js
    - PushManager registration
    - useWebPush hook
  Dados:
    - push_subscriptions: id, user_id, endpoint, p256dh, auth, user_agent, created_at

Integracoes Externas:
  Web Push Protocol:
    - VAPID: Voluntary Application Server Identification
    - Secrets:
      - VAPID_PUBLIC_KEY
      - VAPID_PRIVATE_KEY
      - VAPID_SUBJECT (mailto: ou URL)
    - Endpoint: automaticamente gerenciado por cada navegador (FCM, Mozilla Push Service, etc.)

Design & Componentes:
  Componentes Existentes:
    - Dialog - solicitação de permissão
    - Button - permitir/negar
  Novos Componentes:
    - PushPermissionDialog - dialog explicando benefícios
    - PushStatusBadge - indica se push está ativo
  Design Tokens:
    Primary: --wedo-cyan (#60BED1)
    Background: --lia-bg-primary (#FFFFFF)
  Layout:
    Dialog: max-w-sm, centered
    Push notification: native do OS
  Estados:
    - Not requested (nunca solicitou)
    - Granted (permissão concedida)
    - Denied (permissão negada)
    - Not supported (navegador não suporta)
  Acessibilidade:
    - Dialog acessível
    - Notificações nativas do SO seguem suas configs

Comportamento de UI:
  Fluxo de Permissão:
    1. Usuário ativa "Push" nas preferências
    2. Dialog aparece: "Permitir notificações push?"
       - Explicação: "Receba alertas importantes mesmo quando não estiver na plataforma"
       - Botão: "Permitir" | "Agora não"
    3. Se permitir: navegador solicita permissão nativa
    4. Se granted: subscription salva no servidor
    5. Badge "Push ativo" nas preferências
  
  Fluxo de Notificação:
    1. Evento acontece (ex: candidato respondeu)
    2. Backend verifica preferências do usuário
    3. Se push ativo e fora de DND: envia push
    4. Notificação aparece no OS do usuário
    5. Click na notificação: abre plataforma no contexto
    6. Ação secundária "Dispensar": fecha notificação
  
  Mensagens de Push:
    - Title: "LIA Recruiting"
    - Body: "[Candidato] respondeu sua triagem" ou similar
    - Icon: logo da plataforma
    - Badge: ícone pequeno do sino
    - Actions: ["Abrir", "Dispensar"]
  
  Fallback:
    - Navegador não suporta: toggle de Push fica disabled com tooltip
    - Permissão negada: mensagem explicando como reativar nas configs do navegador

DoD (Definition of Done):
  - [ ] Service Worker registrado
  - [ ] Permissão solicitada e tratada
  - [ ] Subscription salva no servidor
  - [ ] Push enviado pelo backend
  - [ ] Click abre contexto correto
  - [ ] Testes em Chrome e Firefox

Criterios de Aceitacao:
  - [ ] Notificação push aparece no OS
  - [ ] Click navega para contexto correto
  - [ ] Preferências respeitadas
  - [ ] DND bloqueia push no horário
  - [ ] Funciona em background/aba fechada

Arquivos de Referencia (Prototipo Replit):
  - notification_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/notification_service.py
  - communication_dispatcher.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/communication_dispatcher.py
```

---

### CARD NOT-005: Histórico de Notificações
**Épico:** É10 — Notificações

```yaml
Titulo: [FULL-STACK] Histórico de Notificações (Lista Paginada)
Tipo: Full-Stack
Area: Full-Stack
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 5
Prioridade: Baixa
Epic: EPIC-NOT-001
Status: 📋 Pendente Jira
Dependencias: NOT-001

Descricao: |
  Implementar página de histórico completo de notificações
  com lista paginada, filtros por tipo e período, e opção
  de excluir notificações antigas.

Historia de Usuario: |
  Como recrutador, eu quero ver o histórico completo de
  notificações para revisar eventos passados e encontrar
  informações que posso ter perdido.

Regras de Negocio:
  1. Lista paginada (20 por página)
  2. Ordenação por data (mais recentes primeiro)
  3. Filtro por tipo de notificação
  4. Filtro por período (hoje, 7 dias, 30 dias, todos)
  5. Filtro por status (lidas, não lidas, todas)
  6. Excluir notificação individual
  7. Retenção de 90 dias (auto-delete após)

Requisitos Tecnicos:
  Backend:
    - GET /api/backend-proxy/notifications/history
      - Query: page, limit, type, period, status
    - DELETE /api/backend-proxy/notifications/{id}
    - DELETE /api/backend-proxy/notifications/bulk
      - Body: ids[]
    - Cron job para limpeza de notificações > 90 dias
  Frontend:
    - NotificationHistory page
    - NotificationFilters component
    - NotificationList component (paginado)
  Dados:
    - notifications (mesmo de NOT-001)

Integracoes Externas:
  Nenhuma

Design & Componentes:
  Componentes Existentes:
    - Table - lista de notificações
    - Pagination - navegação de páginas
    - Select - filtros
    - Button - ações
    - Checkbox - seleção múltipla
  Novos Componentes:
    - NotificationFilters - barra de filtros
    - NotificationHistoryList - lista com items expandíveis
  Design Tokens:
    Background: --lia-bg-primary (#FFFFFF)
    Border: --lia-border-subtle (#E5E7EB)
    Unread: --wedo-cyan-light (5% opacity)
    Text: --lia-text-primary (#111827)
  Layout:
    Container: max-w-4xl mx-auto
    Filters: flex gap-4, sticky top
    List: divide-y
    Pagination: centered, bottom
  Estados:
    - Loading (skeleton)
    - Empty (nenhuma notificação no período)
    - Loaded (lista paginada)
    - Filtered (com filtros aplicados)
  Acessibilidade:
    - Navegação por teclado na lista
    - Filtros com labels
    - Paginação acessível

Comportamento de UI:
  Fluxo Principal:
    1. Usuário clica "Ver todas" no dropdown de notificações
    2. Página de histórico abre
    3. Filtros no topo: Tipo | Período | Status
    4. Lista mostra 20 notificações por página
    5. Cada item: ícone, título, mensagem resumida, timestamp
    6. Click expande para ver mensagem completa
    7. Botão "Ir para" navega ao contexto
    8. Checkbox + "Excluir selecionadas" para bulk delete
  
  Filtros:
    - Tipo: [Todos, Candidatos, Entrevistas, Sistema]
    - Período: [Hoje, Últimos 7 dias, Últimos 30 dias, Todos]
    - Status: [Todas, Não lidas, Lidas]
  
  Estados de Botoes:
    Excluir:
      - Default: ícone lixeira, bg-transparent
      - Hover: texto --electric-red
    Excluir Selecionadas:
      - Default: bg-electric-red-light, texto --electric-red
      - Hover: bg-electric-red, texto branco
      - Disabled: nenhuma selecionada
    Ir para:
      - Default: link azul
      - Hover: underline
  
  Mensagens de Feedback:
    - Empty: "Nenhuma notificação encontrada" com ícone
    - Deleted: Toast "Notificação excluída"
    - Bulk deleted: Toast "X notificações excluídas"

DoD (Definition of Done):
  - [ ] Página de histórico acessível
  - [ ] Paginação funciona
  - [ ] Filtros funcionam
  - [ ] Delete individual funciona
  - [ ] Delete em massa funciona
  - [ ] Auto-delete de >90 dias implementado
  - [ ] Testes passando


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

Criterios de Aceitacao:
  - [ ] Lista carrega com paginação
  - [ ] Filtros aplicam corretamente
  - [ ] Click navega para contexto
  - [ ] Delete remove da lista
  - [ ] Performance OK com muitas notificações

Arquivos de Referencia (Prototipo Replit):
  - kpi-alert-system.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/alerts/kpi-alert-system.tsx
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/backend-proxy/alerts/route.ts
  - notification_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/notification_service.py
```

---

### CARD NOT-006: Badge de Não Lidas
**Épico:** É10 — Notificações

```yaml
Titulo: [FRONTEND] Badge de Não Lidas (Contador Vermelho)
Tipo: Frontend
Area: Frontend
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 3
Prioridade: Alta
Epic: EPIC-NOT-001
Status: 📋 Pendente Jira
Dependencias: NOT-001

Descricao: |
  Implementar badge vermelho no ícone do sino mostrando
  quantidade de notificações não lidas. Atualizar em tempo
  real e animar quando novo item chega.

Historia de Usuario: |
  Como recrutador, eu quero ver claramente quantas notificações
  não li para saber se há algo que precisa da minha atenção
  imediata.

Regras de Negocio:
  1. Badge vermelho com número de não lidas
  2. Máximo exibido: "99+" para >99
  3. Badge some quando zero não lidas
  4. Animação pulse quando incrementa
  5. Atualização em tempo real (via WebSocket)
  6. Persistir contagem mesmo após reload

Requisitos Tecnicos:
  Backend:
    - GET /api/backend-proxy/notifications/unread-count (já em NOT-001)
  Frontend:
    - NotificationBadge component
    - Animação CSS para pulse
    - useUnreadCount hook
  Dados:
    - Local storage cache do count para UI imediato

Integracoes Externas:
  Nenhuma

Design & Componentes:
  Componentes Existentes:
    - Badge - base shadcn/ui
  Novos Componentes:
    - NotificationBadge - badge específico com animação
  Design Tokens:
    Badge Background: --electric-red (#de1c31)
    Badge Text: white
    Badge Shadow: 0 0 0 2px white (borda para destaque)
  Layout:
    Size: 18x18px (1-2 dígitos), 24x18px (99+)
    Position: absolute, -top-1, -right-1 do sino
    Font: 10px bold
  Estados:
    - Hidden (0 não lidas)
    - Showing (1-99 não lidas)
    - Max (99+ não lidas)
    - Pulsing (nova notificação chegou)
  Acessibilidade:
    - aria-label no sino inclui contagem
    - Animação respeita prefers-reduced-motion

Comportamento de UI:
  Fluxo Principal:
    1. Página carrega → GET unread-count → badge mostra número
    2. WebSocket recebe nova notificação:
       - Count incrementa
       - Badge atualiza
       - Animação pulse por 500ms
    3. Usuário abre dropdown → itens marcados como lidos
    4. Badge decrementa conforme lê
    5. Todas lidas → badge desaparece (fade out)
  
  Animação Pulse:
    - Keyframes: scale(1) → scale(1.2) → scale(1)
    - Duration: 500ms
    - Timing: ease-in-out
    - Trigger: quando count incrementa
  
  Formatação:
    - 0: badge hidden
    - 1-9: "1", "2", ..., "9"
    - 10-99: "10", "11", ..., "99"
    - 100+: "99+"
  
  Responsividade:
    - Mobile: badge ligeiramente maior (20x20px) para toque
    - Desktop: 18x18px padrão

DoD (Definition of Done):
  - [ ] Badge mostra contagem correta
  - [ ] Badge some quando zero
  - [ ] 99+ para grandes números
  - [ ] Animação pulse implementada
  - [ ] Atualização em tempo real
  - [ ] Acessibilidade OK


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

Criterios de Aceitacao:
  - [ ] Badge visível com não lidas
  - [ ] Badge invisível quando zero
  - [ ] Animação ao receber nova
  - [ ] Número atualiza sem refresh
  - [ ] Performance não impactada

Arquivos de Referencia (Prototipo Replit):
  - kpi-alert-system.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/alerts/kpi-alert-system.tsx
  - use-proactive-alerts.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/use-proactive-alerts.ts
```

---

### CARD NOT-007: Notificações para Recrutador via Microsoft Teams
**Épico:** É10 — Notificações

```yaml
Titulo: "[BACKEND] Notificações para Recrutador via Microsoft Teams"
Tipo: Feature (Backend)
Area: Backend
Sprint: Pós-MVP
Pontos: 5
Prioridade: Média
Epic: EPIC-NOT
Status: ⏸️ Pós-MVP
Dependencias: INT-MSG-001

Descricao: |
  Enviar notificações para recrutadores via Microsoft Teams usando
  Microsoft Graph API. Eventos notificáveis: busca concluída, candidato
  triado, incidente de triagem, decisão de gate necessária.
  Configurável por tipo de evento e com suporte multi-tenant.

Historia de Usuario: |
  Como recrutador, eu quero receber notificações da LIA diretamente
  no Microsoft Teams para não perder eventos importantes sem precisar
  abrir a plataforma constantemente.

Regras de Negocio:
  1. Eventos notificáveis: busca concluída, candidato triado, incidente de triagem, decisão de gate necessária
  2. Configurável por tipo de evento (recrutador escolhe quais quer receber via Teams)
  3. Suporte multi-tenant (cada empresa pode ter sua configuração Teams)
  4. Mensagens formatadas com Adaptive Cards (rich formatting)
  5. Deep link para a plataforma na notificação
  6. Rate limiting: máximo 60 msgs/minuto por tenant
  7. Fallback silencioso se Teams indisponível (não bloquear fluxo)

Requisitos Tecnicos:
  Backend:
    - TeamsNotificationService class
    - Microsoft Graph API: Chat.ReadWrite permission
    - Bot Framework proactive messaging
    - Adaptive Card templates por tipo de evento
    - POST /api/v1/notifications/teams/send
    - GET /api/v1/notifications/teams/config
    - PUT /api/v1/notifications/teams/config
  Frontend:
    - Preferências de notificação em Settings (quais eventos receber via Teams)
    - Toggle por tipo de evento
  Dados:
    - teams_notification_config: company_id, user_id, event_types (JSONB), teams_user_id, is_active
    - teams_notification_log: id, user_id, event_type, status (sent/failed), error, sent_at

Integracoes Externas:
  Microsoft Graph API:
    - Tipo: REST API + Bot Framework
    - Scopes: Chat.ReadWrite, User.Read
    - Autenticação: Azure AD OAuth 2.0 (via INT-MSG-001)
    - Documentacao: https://docs.microsoft.com/graph/api/chat-sendactivitynotification

  Adaptive Card Payload Templates:
    busca_concluida: |
      {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "body": [
          { "type": "ColumnSet", "columns": [
            { "type": "Column", "width": "auto", "items": [
              { "type": "Image", "url": "{{platform_logo_url}}", "size": "Small" }
            ]},
            { "type": "Column", "width": "stretch", "items": [
              { "type": "TextBlock", "text": "LIA - WeDo Talent", "weight": "Bolder", "size": "Medium" },
              { "type": "TextBlock", "text": "Busca Concluída", "spacing": "None", "isSubtle": true }
            ]}
          ]},
          { "type": "TextBlock", "text": "A busca para **{{job_title}}** foi concluída.", "wrap": true },
          { "type": "FactSet", "facts": [
            { "title": "Candidatos encontrados", "value": "{{candidates_count}}" },
            { "title": "Score médio", "value": "{{avg_score}}%" },
            { "title": "Vaga", "value": "{{job_title}}" }
          ]}
        ],
        "actions": [
          { "type": "Action.OpenUrl", "title": "Ver Candidatos", "url": "{{deep_link}}" }
        ]
      }
    candidato_triado: |
      {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "body": [
          { "type": "ColumnSet", "columns": [
            { "type": "Column", "width": "auto", "items": [
              { "type": "Image", "url": "{{platform_logo_url}}", "size": "Small" }
            ]},
            { "type": "Column", "width": "stretch", "items": [
              { "type": "TextBlock", "text": "LIA - WeDo Talent", "weight": "Bolder", "size": "Medium" },
              { "type": "TextBlock", "text": "Triagem Concluída", "spacing": "None", "isSubtle": true }
            ]}
          ]},
          { "type": "TextBlock", "text": "A triagem WSI de **{{candidate_name}}** para a vaga **{{job_title}}** foi concluída.", "wrap": true },
          { "type": "FactSet", "facts": [
            { "title": "Candidato", "value": "{{candidate_name}}" },
            { "title": "Score WSI", "value": "{{wsi_score}}%" },
            { "title": "Classificação", "value": "{{wsi_classification}}" },
            { "title": "Vaga", "value": "{{job_title}}" }
          ]}
        ],
        "actions": [
          { "type": "Action.OpenUrl", "title": "Ver Resultado", "url": "{{deep_link}}" }
        ]
      }
    incidente_triagem: |
      {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "body": [
          { "type": "ColumnSet", "columns": [
            { "type": "Column", "width": "auto", "items": [
              { "type": "Image", "url": "{{platform_logo_url}}", "size": "Small" }
            ]},
            { "type": "Column", "width": "stretch", "items": [
              { "type": "TextBlock", "text": "LIA - WeDo Talent", "weight": "Bolder", "size": "Medium" },
              { "type": "TextBlock", "text": "⚠️ Incidente de Triagem", "spacing": "None", "color": "Attention" }
            ]}
          ]},
          { "type": "TextBlock", "text": "Candidato **{{candidate_name}}** reportou um problema durante a triagem.", "wrap": true, "color": "Attention" },
          { "type": "FactSet", "facts": [
            { "title": "Candidato", "value": "{{candidate_name}}" },
            { "title": "Vaga", "value": "{{job_title}}" },
            { "title": "Tipo", "value": "{{incident_type}}" },
            { "title": "Prioridade", "value": "{{priority}}" },
            { "title": "Reportado em", "value": "{{reported_at}}" }
          ]},
          { "type": "TextBlock", "text": "Últimas mensagens:", "weight": "Bolder", "size": "Small" },
          { "type": "TextBlock", "text": "{{last_messages_preview}}", "wrap": true, "isSubtle": true }
        ],
        "actions": [
          { "type": "Action.OpenUrl", "title": "Ver Incidente", "url": "{{deep_link}}" },
          { "type": "Action.OpenUrl", "title": "Assumir Incidente", "url": "{{assign_link}}" }
        ]
      }
    decisao_gate: |
      {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "body": [
          { "type": "ColumnSet", "columns": [
            { "type": "Column", "width": "auto", "items": [
              { "type": "Image", "url": "{{platform_logo_url}}", "size": "Small" }
            ]},
            { "type": "Column", "width": "stretch", "items": [
              { "type": "TextBlock", "text": "LIA - WeDo Talent", "weight": "Bolder", "size": "Medium" },
              { "type": "TextBlock", "text": "Decisão Necessária", "spacing": "None", "isSubtle": true }
            ]}
          ]},
          { "type": "TextBlock", "text": "O candidato **{{candidate_name}}** aguarda decisão de gate para a vaga **{{job_title}}**.", "wrap": true },
          { "type": "FactSet", "facts": [
            { "title": "Candidato", "value": "{{candidate_name}}" },
            { "title": "Vaga", "value": "{{job_title}}" },
            { "title": "Etapa", "value": "{{current_stage}}" },
            { "title": "Score WSI", "value": "{{wsi_score}}%" },
            { "title": "Aguardando desde", "value": "{{pending_since}}" }
          ]}
        ],
        "actions": [
          { "type": "Action.OpenUrl", "title": "Avaliar Candidato", "url": "{{deep_link}}" }
        ]
      }

Design & Componentes:
  Componentes Existentes:
    - CommunicationHub - hub de comunicação em Settings
  Novos Componentes:
    - TeamsNotificationPreferences - toggles por evento
  Design Tokens:
    Teams Purple: #6264A7
    Active: --wedo-green (#22C55E)
    Inactive: --lia-text-tertiary (#6B7280)
  Layout:
    Preferences: Dentro de CommunicationHub, seção "Microsoft Teams"
    Toggles: Lista vertical com label + toggle por evento
  Estados:
    - Not Connected (botão "Conectar Teams")
    - Connected (lista de toggles por evento)
    - Saving (loading no toggle)
  Acessibilidade:
    - Labels em todos os toggles
    - ARIA-describedby explicando cada tipo de evento

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador acessa Settings > Comunicação
    2. Seção "Microsoft Teams" mostra status de conexão
    3. Se não conectado: botão "Conectar Teams" (OAuth)
    4. Se conectado: lista de toggles por tipo de evento
    5. Recrutador ativa/desativa eventos desejados
    6. Notificações enviadas automaticamente quando eventos ocorrem

  Mensagens de Feedback:
    Conectado: "Microsoft Teams conectado com sucesso!"
    Salvo: "Preferências de notificação atualizadas."
    Erro: "Não foi possível enviar notificação via Teams."

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md (Seções: 2.17 Switches & Toggles, 2.3 Cards, 2.1 Botões)"
  Figma: "Seção 8.2 — Teams Notifications"
  Assets:
    - "Ícone Microsoft Teams"
  Tokens:
    - "Teams Purple #6264A7"

DoD:
  - [ ] TeamsNotificationService funcional
  - [ ] Notificações enviadas para os 4 tipos de evento
  - [ ] Preferências configuráveis por recrutador
  - [ ] Adaptive Cards renderizando corretamente no Teams
  - [ ] Deep links funcionando
  - [ ] Multi-tenant suportado

Criterios de Aceitacao:
  - [ ] Recrutador conecta Teams via OAuth
  - [ ] Ativa/desativa eventos específicos
  - [ ] Recebe notificação no Teams quando evento ocorre
  - [ ] Clica no deep link e abre plataforma na seção correta
  - [ ] Dados de um tenant não vazam para outro

Arquivos de Referencia (Prototipo Replit):
  - CommunicationHub: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/settings/CommunicationHub.tsx
```

---

## ÉPICO 11: KANBAN E TABELA DE CANDIDATOS - CARDS JIRA

---

### CARD KAN-001: Estrutura do Kanban 4 Colunas
**Épico:** É11 — Kanban e Tabela de Candidatos

```yaml
Titulo: [FRONTEND] Estrutura do Kanban 4 Colunas
Tipo: Frontend
Area: Frontend
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 8
Prioridade: Alta
Epic: EPIC-KAN-001
Status: 📋 Pendente Jira

Descricao: |
  Implementar estrutura base do Kanban com 4 colunas fixas
  representando as etapas principais do pipeline MVP:
  Funil, Triagem, Entrevista e Reprovados.

Historia de Usuario: |
  Como recrutador, eu quero ver os candidatos organizados
  em colunas por etapa para ter visibilidade do pipeline
  de forma visual e intuitiva.

Regras de Negocio:
  1. 4 colunas fixas: Funil | Triagem | Entrevista | Reprovados
  2. Cada coluna mostra contador de candidatos
  3. Scroll vertical dentro de cada coluna
  4. Scroll horizontal entre colunas (mobile/desktop)
  5. Colunas não podem ser reordenadas (ordem fixa)
  6. Header da coluna com nome e contador

Requisitos Tecnicos:
  Backend:
    - GET /api/backend-proxy/candidates?job_id=X&group_by=stage
  Frontend:
    - KanbanBoard component
    - KanbanColumn component
    - KanbanColumnHeader component
  Dados:
    - candidates.stage: 'funnel' | 'screening' | 'interview' | 'rejected'

Integracoes Externas:
  Nenhuma

Design & Componentes:
  Componentes Existentes:
    - Card - base para colunas
    - ScrollArea - scroll dentro das colunas
  Novos Componentes:
    - KanbanBoard - container flex horizontal
    - KanbanColumn - coluna individual
    - KanbanColumnHeader - header com título e contador
  Design Tokens:
    Column Background: --lia-bg-secondary (#F9FAFB)
    Column Border: --lia-border-subtle (#E5E7EB)
    Header Text: --lia-text-primary (#111827)
    Counter Badge: --lia-bg-tertiary, texto --lia-text-secondary
    Rejected Column: leve tint vermelho no header
  Layout:
    Board: flex, gap-4, overflow-x-auto
    Column: min-w-[280px], max-w-[320px], flex-shrink-0
    Column Height: calc(100vh - 200px) com scroll interno
    Header: sticky top, padding-4
  Estados:
    - Loading (skeleton de 4 colunas)
    - Empty column (mensagem "Nenhum candidato")
    - Populated (cards de candidatos)
  Acessibilidade:
    - Colunas com role="list"
    - Títulos como headings (h3)
    - Scroll acessível por teclado

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador acessa página de candidatos de uma vaga
    2. Toggle "Kanban" ativado (vs Tabela)
    3. 4 colunas renderizam lado a lado
    4. Cada coluna carrega candidatos da etapa correspondente
    5. Scroll horizontal se tela pequena
    6. Scroll vertical dentro de cada coluna
  
  Layout Responsivo:
    - Desktop (>1024px): 4 colunas visíveis
    - Tablet (768-1024px): 2-3 colunas, scroll horizontal
    - Mobile (<768px): 1 coluna visível, swipe horizontal
  
  Cores dos Headers:
    - Funil: --wedo-cyan light
    - Triagem: --wedo-yellow light
    - Entrevista: --wedo-green light
    - Reprovados: --electric-red light

DoD (Definition of Done):
  - [ ] 4 colunas renderizam corretamente
  - [ ] Contadores funcionam
  - [ ] Scroll horizontal funciona
  - [ ] Scroll vertical por coluna funciona
  - [ ] Responsivo em diferentes telas
  - [ ] Acessível por teclado


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

Criterios de Aceitacao:
  - [ ] Colunas mostram nome e contador
  - [ ] Candidatos agrupados por etapa
  - [ ] Scroll funciona em ambas direções
  - [ ] Performance OK com muitos candidatos

Arquivos de Referencia (Prototipo Replit):
  - page.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/jobs/[id]/page.tsx
  - types.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/kanban/types.ts
  - types.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/job-kanban/types.ts
  - use-recruitment-stages.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/use-recruitment-stages.ts
  - recruitment-stages.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/recruitment-stages.ts
  - pipeline_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/pipeline_service.py
```

---

### CARD KAN-002: Card de Candidato
**Épico:** É11 — Kanban e Tabela de Candidatos

```yaml
Titulo: [FRONTEND] Card de Candidato no Kanban
Tipo: Frontend
Area: Frontend
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 5
Prioridade: Alta
Epic: EPIC-KAN-001
Status: 📋 Pendente Jira

Descricao: |
  Implementar card visual do candidato dentro das colunas
  do Kanban, mostrando foto, nome, score WSI (quando disponível)
  e ícones de status/ações rápidas.

Historia de Usuario: |
  Como recrutador, eu quero ver informações resumidas de cada
  candidato no card para fazer triagem visual rápida sem
  precisar abrir o perfil completo.

Regras de Negocio:
  1. Foto do candidato (ou avatar com iniciais)
  2. Nome completo (truncado se muito longo)
  3. Título/cargo atual
  4. Score WSI em badge (quando disponível)
  5. Ícones de status: favorito, mensagem pendente, triagem completa
  6. Click abre preview lateral

Requisitos Tecnicos:
  Backend:
    - (usa dados já carregados do GET candidates)
  Frontend:
    - CandidateCard component
    - CandidateAvatar component
    - ScoreBadge component (preview para KAN-006)
  Dados:
    - candidate: id, name, photo_url, current_title, wsi_score, is_favorite, has_unread_message, screening_status

Integracoes Externas:
  Nenhuma

Design & Componentes:
  Componentes Existentes:
    - Card - base shadcn/ui
    - Avatar - foto ou iniciais
    - Badge - score e status
  Novos Componentes:
    - CandidateCard - card completo do candidato
    - CandidateAvatar - avatar com fallback para iniciais
  Design Tokens:
    Card Background: --lia-bg-primary (#FFFFFF)
    Card Border: --lia-border-subtle (#E5E7EB)
    Card Shadow: --lia-shadow-sm
    Card Hover: --lia-shadow-md
    Name: --lia-text-primary, font-medium
    Title: --lia-text-secondary, text-sm
    Score Badge: varia por score (ver KAN-006)
  Layout:
    Card: padding-3, rounded-lg
    Avatar: 40x40px, rounded-full
    Content: flex-col, gap-1
    Icons: absolute top-right ou bottom-right
  Estados:
    - Default (hover: shadow aumenta)
    - Selected (borda --wedo-cyan)
    - Favorited (ícone coração preenchido)
    - Unread (dot indicator)
  Acessibilidade:
    - Card como button role
    - Nome como label principal
    - Ícones com tooltips/aria-label

Comportamento de UI:
  Fluxo Principal:
    1. Card renderiza com dados do candidato
    2. Avatar mostra foto ou iniciais coloridas
    3. Nome trunca com ellipsis se >25 chars
    4. Título/cargo abaixo do nome
    5. Score badge no canto (se disponível)
    6. Hover: sombra aumenta, cursor pointer
    7. Click: abre preview lateral (PRV-001)
  
  Layout do Card:

Arquivos de Referencia (Prototipo Replit):
  - page.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/jobs/[id]/page.tsx
  - types.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/kanban/types.ts
  - pipeline_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/pipeline_service.py
  - pipeline_stage_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/pipeline_stage_service.py
    ```
    ┌─────────────────────────┐
    │ [Avatar] Nome Sobren... │
    │          Cargo Atual    │
    │ ❤️ 💬    [Score: 85]   │
    └─────────────────────────┘
    ```
  
  Ícones de Status:
    - ❤️ Favorito: vermelho se favoritado
    - 💬 Mensagem: azul se há mensagem não lida
    - ✅ Triado: verde se triagem completa

DoD (Definition of Done):
  - [ ] Card renderiza com todos os dados
  - [ ] Avatar com fallback funciona
  - [ ] Nome e título exibidos
  - [ ] Hover state implementado
  - [ ] Click abre preview
  - [ ] Responsivo

Criterios de Aceitacao:
  - [ ] Foto carrega corretamente
  - [ ] Iniciais aparecem se sem foto
  - [ ] Nome trunca adequadamente
  - [ ] Score badge visível quando disponível
  - [ ] Ícones de status funcionais
```

---

### CARD KAN-003: Drag-and-Drop entre Colunas
**Épico:** É11 — Kanban e Tabela de Candidatos

```yaml
Titulo: [FRONTEND] Drag-and-Drop entre Colunas
Tipo: Frontend
Area: Frontend
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 8
Prioridade: Alta
Epic: EPIC-KAN-001
Status: 📋 Pendente Jira
Dependencias: KAN-001, KAN-002

Descricao: |
  Implementar funcionalidade de arrastar e soltar candidatos
  entre colunas do Kanban para movê-los entre etapas do pipeline.
  Incluir validações de transições permitidas.

Historia de Usuario: |
  Como recrutador, eu quero arrastar candidatos entre colunas
  para alterar a etapa deles no pipeline de forma visual
  e intuitiva.

Regras de Negocio:
  1. Drag de card de candidato
  2. Drop em coluna de destino
  3. Validar transições permitidas (Funil→Triagem, Triagem→Entrevista, etc.)
  4. Transições inválidas: visual feedback + bloqueio
  5. Atualizar backend ao soltar
  6. Optimistic UI update com rollback em caso de erro
  7. Movimento para "Reprovados" exige confirmação

Requisitos Tecnicos:
  Backend:
    - PUT /api/backend-proxy/candidates/{id}/stage
      - Body: { stage: 'screening' | 'interview' | 'rejected' }
  Frontend:
    - react-beautiful-dnd ou @dnd-kit
    - Droppable columns
    - Draggable cards
    - Transition validation logic
  Dados:
    - candidates.stage atualizado

Integracoes Externas:
  Nenhuma

Design & Componentes:
  Componentes Existentes:
    - KanbanBoard (KAN-001)
    - KanbanColumn (KAN-001)
    - CandidateCard (KAN-002)
  Novos Componentes:
    - DroppableColumn wrapper
    - DraggableCard wrapper
    - DropPlaceholder - indicador de onde vai cair
  Design Tokens:
    Dragging: opacity-75, --lia-shadow-lg, rotate ligeiro
    Drop Zone Active: borda --wedo-cyan dashed
    Drop Zone Invalid: borda --electric-red dashed
    Placeholder: bg-wedo-cyan-light, height do card
  Layout:
    Placeholder: mesma altura do card sendo arrastado
    Ghost: segue o cursor
  Estados:
    - Idle (normal)
    - Dragging (card sendo arrastado)
    - Over valid (coluna aceita o drop)
    - Over invalid (coluna rejeita)
    - Dropped (card na nova posição)
  Acessibilidade:
    - Keyboard drag: Enter para iniciar, arrows para mover, Enter para soltar
    - Screen reader announcements durante drag

Comportamento de UI:
  Fluxo Principal:
    1. Usuário pressiona e segura card por 150ms (ou clica e arrasta imediatamente)
    2. Card se destaca (opacity, shadow, leve rotate)
    3. Placeholder aparece na posição original
    4. Ao passar sobre coluna válida: borda verde/cyan, placeholder na coluna
    5. Ao passar sobre coluna inválida: borda vermelha, X indicator
    6. Ao soltar em coluna válida:
       - Card move para nova coluna (optimistic)
       - API chamada em background
       - Toast de sucesso
    7. Se movimento para "Reprovados":
       - Dialog de confirmação antes de executar
       - "Tem certeza? O candidato receberá feedback automático."
  
  Transições Permitidas:
    - Funil → Triagem ✅
    - Funil → Reprovados ✅
    - Triagem → Entrevista ✅
    - Triagem → Reprovados ✅
    - Entrevista → Reprovados ✅
    - Reprovados → (nenhuma) ❌
    - Qualquer retrocesso ❌ (ex: Entrevista → Triagem)
  
  Mensagens de Feedback:
    - Sucesso: Toast verde "Candidato movido para [Etapa]"
    - Erro: Toast vermelho + rollback visual
    - Inválido: Tooltip "Não é possível mover para esta etapa"

DoD (Definition of Done):
  - [ ] Drag and drop funciona
  - [ ] Validações de transição implementadas
  - [ ] Optimistic update implementado
  - [ ] Rollback em caso de erro
  - [ ] Confirmação para "Reprovados"
  - [ ] Acessível por teclado
  - [ ] Testes passando


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

Criterios de Aceitacao:
  - [ ] Card pode ser arrastado entre colunas
  - [ ] Transições inválidas são bloqueadas
  - [ ] API é chamada ao soltar
  - [ ] UI atualiza imediatamente (optimistic)
  - [ ] Erro faz rollback visual
  - [ ] "Reprovados" exige confirmação

Arquivos de Referencia (Prototipo Replit):
  - candidate-preview.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/candidate-preview.tsx
  - candidate-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/candidate-modal.tsx
  - candidate-page.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/candidate-page.tsx
  - search-results-card.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/search-results-card.tsx
```

---

### CARD KAN-004: Menu de Ações do Card
**Épico:** É11 — Kanban e Tabela de Candidatos

```yaml
Titulo: [FRONTEND] Menu de Ações do Card (3 dots)
Tipo: Frontend
Area: Frontend
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 5
Prioridade: Alta
Epic: EPIC-KAN-001
Status: 📋 Pendente Jira
Dependencias: KAN-002

Descricao: |
  Implementar menu de ações contextuais acessível via ícone
  de três pontos no card do candidato. Menu oferece ações
  como mover etapa, enviar mensagem, agendar entrevista, etc.

Historia de Usuario: |
  Como recrutador, eu quero acessar ações rápidas do candidato
  diretamente do card sem precisar abrir o perfil completo.

Regras de Negocio:
  1. Ícone de 3 pontos (MoreVertical) no canto do card
  2. Click abre dropdown com ações contextuais
  3. Ações variam por etapa do candidato
  4. Ações destrutivas requerem confirmação
  5. Atalhos de teclado para ações principais

Requisitos Tecnicos:
  Frontend:
    - DropdownMenu (shadcn/ui)
    - Ações condicionais por etapa
    - Handlers para cada ação
  Backend:
    - Reutiliza endpoints existentes

Integracoes Externas:
  Nenhuma

Design & Componentes:
  Componentes Existentes:
    - DropdownMenu - shadcn/ui
    - DropdownMenuItem - item do menu
    - Separator - divisor entre grupos
  Novos Componentes:
    - CandidateActionsMenu - menu contextual do card
  Design Tokens:
    Trigger: --lia-text-tertiary (hover: --lia-text-primary)
    Menu Background: --lia-bg-primary
    Menu Shadow: --lia-shadow-lg
    Item Hover: --lia-interactive-hover
    Destructive: --electric-red
  Layout:
    Trigger: 24x24px, absolute top-right do card
    Menu: min-w-[180px]
    Items: padding-2
  Estados:
    - Hidden (menu fechado)
    - Open (menu visível)
    - Item hover (highlight)
    - Loading (ação em andamento)
  Acessibilidade:
    - Trigger com aria-haspopup="menu"
    - Menu com role="menu"
    - Items com role="menuitem"
    - Keyboard: arrows para navegar, Enter para selecionar

Comportamento de UI:
  Fluxo Principal:
    1. Hover no card revela ícone de 3 pontos
    2. Click no ícone abre menu dropdown
    3. Menu mostra ações disponíveis para a etapa
    4. Click em ação executa ou abre modal (se destrutivo)
    5. Menu fecha após ação ou click fora
  
  Ações por Etapa:
    Funil:
      - 📋 Ver perfil
      - 📧 Enviar mensagem
      - ✅ Aprovar para triagem
      - ❌ Reprovar (confirmação)
      - ❤️ Favoritar/Desfavoritar
    Triagem:
      - 📋 Ver perfil
      - 💬 Ver conversa WhatsApp
      - ✅ Aprovar para entrevista
      - ❌ Reprovar (confirmação)
      - ❤️ Favoritar/Desfavoritar
    Entrevista:
      - 📋 Ver perfil
      - 📅 Ver/Reagendar entrevista
      - ❌ Cancelar entrevista (confirmação)
      - ❤️ Favoritar/Desfavoritar
    Reprovados:
      - 📋 Ver perfil
      - 📧 Ver feedback enviado
  
  Estados de Items:
    - Default: texto normal
    - Hover: bg-lia-interactive-hover
    - Disabled: opacity-50, cursor-not-allowed
    - Destructive: texto --electric-red

DoD (Definition of Done):
  - [ ] Menu abre e fecha corretamente
  - [ ] Ações variam por etapa
  - [ ] Ações executam corretamente
  - [ ] Confirmação para ações destrutivas
  - [ ] Acessível por teclado
  - [ ] Testes passando


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

Criterios de Aceitacao:
  - [ ] Ícone aparece no hover do card
  - [ ] Menu lista ações corretas por etapa
  - [ ] Ações funcionam corretamente
  - [ ] Ações destrutivas pedem confirmação
  - [ ] Keyboard navigation funciona

Arquivos de Referencia (Prototipo Replit):
  - candidate-decision-flow-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/candidate-decision-flow-modal.tsx
  - contextual-actions-banner.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/contextual-actions-banner.tsx
  - bulk-actions-bar.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/bulk-actions-bar.tsx
```

---

### CARD KAN-005: Ícones de Ação Rápida ❌ OBSOLETO
**Épico:** É11 — Kanban e Tabela de Candidatos

> ❌ **OBSOLETO** — Confirmado na reunião de 06/02/2026. Ações rápidas já cobertas por outros componentes (menu de contexto, batch actions).

```yaml
Titulo: [FRONTEND] Ícones de Ação Rápida no Card
Tipo: Frontend
Area: Frontend
Sprint: 2
Pontos: 3
Prioridade: Media
Epic: EPIC-KAN-001
Status: ❌ Removido (Obsoleto - confirmado 06/02/2026)
Dependencias: KAN-002

Descricao: |
  Implementar ícones clicáveis no card do candidato para ações
  rápidas: adicionar nota, ver LinkedIn, análise IA e favoritar.
  Ícones aparecem no hover do card.

Historia de Usuario: |
  Como recrutador, eu quero ter atalhos visuais para ações
  frequentes diretamente no card do candidato para agilizar
  meu trabalho.

Regras de Negocio:
  1. Ícones aparecem no hover do card
  2. 4 ícones principais: Nota (📝), LinkedIn (🔗), IA (🧠), Favorito (❤️)
  3. Tooltip em cada ícone
  4. Click executa ação diretamente
  5. Favorito toggle on/off com estado visual

Requisitos Tecnicos:
  Frontend:
    - QuickActionIcons component
    - Tooltip component
    - Handlers para cada ação
  Backend:
    - POST /api/backend-proxy/candidates/{id}/note
    - POST /api/backend-proxy/candidates/{id}/favorite

Integracoes Externas:
  LinkedIn (apenas link externo, não API)

Design & Componentes:
  Componentes Existentes:
    - Button - icon buttons
    - Tooltip - shadcn/ui
  Novos Componentes:
    - QuickActionBar - container dos ícones
    - QuickActionButton - botão com ícone + tooltip
  Design Tokens:
    Icon Default: --lia-text-tertiary (#9CA3AF)
    Icon Hover: --lia-text-primary (#111827)
    Favorite Active: --electric-red (#de1c31)
    AI Icon: --wedo-cyan (#60BED1)
    Background Bar: --lia-bg-primary com blur
  Layout:
    Bar: flex, gap-1, absolute bottom ou overlay
    Button: 28x28px, rounded-md
  Estados:
    - Hidden (card não em hover)
    - Visible (card em hover)
    - Icon hover (scale up 1.1)
    - Active (favorito preenchido)
  Acessibilidade:
    - Cada ícone com aria-label
    - Tooltips anunciados
    - Tab navigation

Comportamento de UI:
  Fluxo Principal:
    1. Hover no card revela barra de ícones
    2. Ícones em linha na parte inferior do card
    3. Hover em ícone mostra tooltip
    4. Click executa ação:
       - 📝 Nota: abre modal de adicionar nota
       - 🔗 LinkedIn: abre perfil em nova aba
       - 🧠 IA: abre tab Parecer LIA no preview
       - ❤️ Favorito: toggle on/off instantâneo
  
  Layout da Barra:

Arquivos de Referencia (Prototipo Replit):
  - useJobFiltersPersistence.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/useJobFiltersPersistence.ts
  - useJobColumnConfig.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/useJobColumnConfig.ts
  - column-configuration-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/column-configuration-modal.tsx
    ```
    ┌─────────────────────────┐
    │ [Avatar] Nome...        │
    │          Cargo          │
    │ [📝] [🔗] [🧠] [❤️]    │
    └─────────────────────────┘
    ```
  
  Ações:
    📝 Adicionar Nota:
      - Click abre modal com textarea
      - Salvar adiciona nota ao histórico
    🔗 Ver LinkedIn:
      - Click abre linkedin.com/in/{username} em nova aba
      - Desabilitado se sem LinkedIn
    🧠 Parecer IA:
      - Click abre preview lateral na tab "Parecer LIA"
    ❤️ Favoritar:
      - Click toggle: vazio ↔ preenchido vermelho
      - Animação de pulse ao favoritar

DoD (Definition of Done):
  - [ ] Barra de ícones aparece no hover
  - [ ] Tooltips funcionam
  - [ ] Cada ação executa corretamente
  - [ ] Favorito toggle funciona
  - [ ] Acessível por teclado

Criterios de Aceitacao:
  - [ ] Ícones aparecem suavemente no hover
  - [ ] Tooltips explicam cada ação
  - [ ] Nota abre modal
  - [ ] LinkedIn abre nova aba
  - [ ] Favorito muda estado visual
```

---

### CARD KAN-006: Badge de Score WSI
**Épico:** É11 — Kanban e Tabela de Candidatos

```yaml
Titulo: [FRONTEND] Badge de Score WSI no Card
Tipo: Frontend
Area: Frontend
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 5
Prioridade: Alta
Epic: EPIC-KAN-001
Status: 📋 Pendente Jira
Dependencias: KAN-002, SCO-001

Descricao: |
  Implementar badge visual no card do candidato mostrando
  o score WSI (0-100) com cores indicativas de qualidade.
  Badge só aparece após triagem concluída.

Historia de Usuario: |
  Como recrutador, eu quero ver o score WSI diretamente no
  card para fazer triagem visual rápida e identificar os
  melhores candidatos sem abrir cada perfil.

Regras de Negocio:
  1. Score de 0-100 exibido no badge
  2. Cores por faixa:
     - 85-100: Verde (excelente)
     - 70-84: Azul (bom)
     - 50-69: Amarelo (médio)
     - 0-49: Vermelho (baixo)
  3. Badge só aparece se triagem foi concluída
  4. Tooltip mostra breakdown resumido
  5. Click abre tab Parecer LIA

Requisitos Tecnicos:
  Frontend:
    - WsiScoreBadge component
    - Score color logic
    - Tooltip com breakdown
  Backend:
    - (usa dados do candidate.wsi_score já carregados)
  Dados:
    - candidate.wsi_score: number (0-100)
    - candidate.wsi_breakdown: { technical, behavioral, cultural, communication }

Integracoes Externas:
  Nenhuma

Design & Componentes:
  Componentes Existentes:
    - Badge - base shadcn/ui
    - Tooltip - para breakdown
  Novos Componentes:
    - WsiScoreBadge - badge colorido com score
  Design Tokens:
    Excellent (85-100): --wedo-green (#10B981), bg-green-100
    Good (70-84): --wedo-cyan (#60BED1), bg-cyan-100
    Medium (50-69): --wedo-yellow (#F59E0B), bg-yellow-100
    Low (0-49): --electric-red (#de1c31), bg-red-100
    Text: cor correspondente (darker shade)
  Layout:
    Badge: padding-x-2, padding-y-0.5, rounded-full, font-bold
    Position: canto superior direito do card ou inline com nome
    Size: text-xs (12px)
  Estados:
    - Hidden (triagem não concluída)
    - Visible (score disponível)
    - Hover (tooltip com breakdown)
  Acessibilidade:
    - aria-label "Score WSI: [número] - [categoria]"
    - Cores com contraste adequado
    - Não depende só de cor (número sempre visível)

Comportamento de UI:
  Fluxo Principal:
    1. Card renderiza
    2. Se candidate.wsi_score existe:
       - Badge aparece com número e cor
    3. Hover no badge:
       - Tooltip mostra breakdown:
         "Técnico: 85 | Comportamental: 78 | Cultural: 90 | Comunicação: 82"
    4. Click no badge:
       - Abre preview lateral na tab "Parecer LIA"
  
  Visual do Badge:

Arquivos de Referencia (Prototipo Replit):
  - page.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/jobs/[id]/page.tsx
  - recruitment-stages.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/recruitment-stages.ts
  - pipeline_stage_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/pipeline_stage_service.py
    ```
    ┌──────────┐
    │  Score   │
    │   85     │  → Verde, texto branco ou verde escuro
    └──────────┘
    ```
  
  Faixas de Cor:
    85-100: 🟢 Excelente - "Altamente recomendado"
    70-84:  🔵 Bom - "Recomendado"
    50-69:  🟡 Médio - "Avaliar com atenção"
    0-49:   🔴 Baixo - "Não recomendado"

DoD (Definition of Done):
  - [ ] Badge renderiza com score correto
  - [ ] Cores correspondem às faixas
  - [ ] Tooltip mostra breakdown
  - [ ] Click abre Parecer LIA
  - [ ] Hidden quando sem score
  - [ ] Acessível

Criterios de Aceitacao:
  - [ ] Score visível no card
  - [ ] Cor correta por faixa
  - [ ] Tooltip informativo
  - [ ] Sem score = sem badge
  - [ ] Click leva ao parecer completo
```

---

### CARD KAN-007: Filtro por Status
**Épico:** É11 — Kanban e Tabela de Candidatos

```yaml
Titulo: [FRONTEND] Filtro por Status no Kanban
Tipo: Frontend
Area: Frontend
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 5
Prioridade: Media
Epic: EPIC-KAN-001
Status: 📋 Pendente Jira
Dependencias: KAN-001

Descricao: |
  Implementar filtros na visualização Kanban para filtrar
  candidatos por sub-status dentro de cada coluna (ex: dentro
  de Triagem, filtrar por "aguardando resposta" ou "triagem completa").

Historia de Usuario: |
  Como recrutador, eu quero filtrar candidatos por status
  específico para focar nos que precisam da minha atenção
  imediata.

Regras de Negocio:
  1. Barra de filtros acima do Kanban
  2. Filtros disponíveis:
     - Status: dropdown multi-select
     - Favoritos apenas: toggle
     - Score mínimo: slider ou input
     - Data de adição: range picker
  3. Filtros aplicam em todas as colunas
  4. Contador atualiza com filtros
  5. Limpar filtros com um click

Requisitos Tecnicos:
  Frontend:
    - KanbanFilters component
    - StatusMultiSelect component
    - ScoreRangeSlider component
    - useCandidateFilters hook
  Backend:
    - GET /api/backend-proxy/candidates?filters=...

Integracoes Externas:
  Nenhuma

Design & Componentes:
  Componentes Existentes:
    - Select - multi-select para status
    - Slider - para score mínimo
    - Switch - toggle de favoritos
    - DateRangePicker - se disponível
    - Button - limpar filtros
  Novos Componentes:
    - KanbanFilters - barra de filtros
    - StatusMultiSelect - select com chips
    - ActiveFilterChips - chips dos filtros ativos
  Design Tokens:
    Bar Background: --lia-bg-secondary (#F9FAFB)
    Chip Background: --wedo-cyan-light
    Chip Text: --wedo-cyan-dark
    Clear Button: --lia-text-tertiary
  Layout:
    Bar: flex, gap-4, padding-4, sticky top
    Chips: flex wrap, gap-2
    Responsive: collapse para dropdown em mobile
  Estados:
    - No filters (barra com inputs vazios)
    - Active filters (chips visíveis, "Limpar tudo" aparece)
    - Filtering (loading state momentâneo)
  Acessibilidade:
    - Labels em todos os inputs
    - Chips removíveis com keyboard
    - Screen reader anuncia resultados filtrados

Comportamento de UI:
  Fluxo Principal:
    1. Barra de filtros acima do Kanban
    2. Usuário seleciona "Status: Triagem completa"
    3. Chip aparece mostrando filtro ativo
    4. Kanban filtra para mostrar apenas candidatos com status selecionado
    5. Contadores das colunas atualizam
    6. "Limpar filtros" remove todos os filtros
  
  Filtros Disponíveis:
    - Status: [Mapeado, Aguardando aprovação, Aguardando contato, Em triagem, Triagem completa, Aguardando entrevista, Reprovado]
    - Apenas favoritos: toggle on/off
    - Score mínimo: slider 0-100
    - Adicionado em: date range picker
  
  Estados de Elementos:
    Multi-select:
      - Placeholder: "Filtrar por status"
      - Selected: chips dentro do select
    Slider:
      - Label: "Score mínimo: 70"
      - Track: --lia-bg-tertiary
      - Thumb: --wedo-cyan
    Limpar:
      - Default: texto link "Limpar filtros"
      - Hover: underline
      - Hidden: quando nenhum filtro ativo

DoD (Definition of Done):
  - [ ] Barra de filtros renderiza
  - [ ] Multi-select de status funciona
  - [ ] Toggle de favoritos funciona
  - [ ] Slider de score funciona
  - [ ] Kanban filtra corretamente
  - [ ] Limpar filtros funciona
  - [ ] Chips de filtros ativos


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

Criterios de Aceitacao:
  - [ ] Filtros aplicam em tempo real
  - [ ] Contadores atualizam com filtros
  - [ ] Chips mostram filtros ativos
  - [ ] Limpar remove todos os filtros
  - [ ] URL reflete filtros (shareable)

Arquivos de Referencia (Prototipo Replit):
  - contextual-actions-banner.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/contextual-actions-banner.tsx
  - bulk-actions-bar.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/bulk-actions-bar.tsx
  - candidate-decision-flow-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/candidate-decision-flow-modal.tsx
```

---

### CARD KAN-008: Busca de Candidato
**Épico:** É11 — Kanban e Tabela de Candidatos

```yaml
Titulo: [FRONTEND] Busca de Candidato no Kanban
Tipo: Frontend
Area: Frontend
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 3
Prioridade: Media
Epic: EPIC-KAN-001
Status: 📋 Pendente Jira
Dependencias: KAN-001

Descricao: |
  Implementar campo de busca para encontrar candidatos por
  nome dentro do Kanban. Busca filtra em tempo real enquanto
  usuário digita.

Historia de Usuario: |
  Como recrutador, eu quero buscar candidatos por nome
  para encontrar rapidamente alguém específico no pipeline.

Regras de Negocio:
  1. Campo de busca no topo do Kanban
  2. Busca por nome (primeiro nome, sobrenome ou nome completo)
  3. Busca inicia após 2 caracteres
  4. Debounce de 300ms
  5. Highlight do termo buscado nos resultados
  6. Clear button para limpar busca

Requisitos Tecnicos:
  Frontend:
    - SearchInput component
    - Debounced search logic
    - Text highlight utility
  Backend:
    - (usa dados já carregados, filtra no frontend)
    - Ou GET /api/backend-proxy/candidates?search=...

Integracoes Externas:
  Nenhuma

Design & Componentes:
  Componentes Existentes:
    - Input - campo de busca
    - Button - clear button
  Novos Componentes:
    - CandidateSearchInput - input com ícone e clear
    - HighlightedText - texto com termo destacado
  Design Tokens:
    Input Background: --lia-bg-primary (#FFFFFF)
    Input Border: --lia-border-subtle (#E5E7EB)
    Input Focus: --wedo-cyan border
    Highlight: --wedo-yellow background
    Placeholder: --lia-text-tertiary
  Layout:
    Input: w-64 ou w-full em mobile
    Position: junto aos filtros, à esquerda
    Icon: lupa à esquerda, X à direita quando há texto
  Estados:
    - Empty (placeholder "Buscar candidato...")
    - Typing (texto sendo digitado)
    - Searching (debounce ativo, pode ter loading)
    - Results (resultados filtrados)
    - No results (mensagem "Nenhum candidato encontrado")
  Acessibilidade:
    - Label "Buscar candidato"
    - Clear button com aria-label
    - Anúncio de resultados para screen readers

Comportamento de UI:
  Fluxo Principal:
    1. Campo de busca vazio com placeholder
    2. Usuário começa a digitar
    3. Após 2 caracteres, busca inicia (com debounce 300ms)
    4. Cards são filtrados em todas as colunas
    5. Termo buscado é highlighted nos nomes
    6. Se nenhum resultado: mensagem inline
    7. X para limpar busca e voltar ao estado original
  
  Visual:

Arquivos de Referencia (Prototipo Replit):
  - bulk-actions-bar.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/bulk-actions-bar.tsx
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/backend-proxy/candidates/bulk/update-status/route.ts
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/backend-proxy/candidates/bulk/send-email/route.ts
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/backend-proxy/candidates/bulk/export/route.ts
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/backend-proxy/candidates/bulk/delete/route.ts
    ```
    ┌─────────────────────────────┐
    │ 🔍 Buscar candidato...    X │
    └─────────────────────────────┘
    ```
  
  Estados do Input:
    - Empty: placeholder, sem X
    - Filled: texto, X visível
    - Focus: borda --wedo-cyan
  
  Highlight:
    - Termo buscado destacado com background amarelo
    - Case insensitive match

DoD (Definition of Done):
  - [ ] Campo de busca funciona
  - [ ] Debounce implementado
  - [ ] Filtro aplicado em tempo real
  - [ ] Highlight do termo funciona
  - [ ] Clear button funciona
  - [ ] Mensagem de "nenhum resultado"

Criterios de Aceitacao:
  - [ ] Busca filtra por nome corretamente
  - [ ] Busca inicia após 2 caracteres
  - [ ] Debounce evita chamadas excessivas
  - [ ] Termo é destacado nos resultados
  - [ ] X limpa busca e restaura resultados
```

---

### CARD KAN-010: Feedback Implícito em Transições
**Épico:** É11 — Kanban e Tabela de Candidatos

```yaml
Titulo: [BACKEND] Feedback Implícito em Transições Kanban
Tipo: Backend
Area: Backend
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 5
Prioridade: Alta
Epic: EPIC-KAN-001
Status: 📋 Pendente Jira
Dependencias: KAN-003

Descricao: |
  Implementar sistema de captura de feedback implícito quando o recrutador
  move candidatos entre colunas do Kanban. Cada movimento gera dados de
  feedback que alimentam o modelo de triagem.

Historia de Usuario: |
  Como recrutador, eu quero que o sistema aprenda com minhas decisões
  de mover candidatos para melhorar recomendações futuras.

Regras de Negocio:
  1. Capturar tempo de permanência em cada coluna
  2. Registrar direção do movimento (avanço/rejeição)
  3. Considerar velocidade da decisão como indicador de confiança
  4. Associar feedback ao perfil do candidato e vaga
  5. Não interromper fluxo do recrutador (captura passiva)
  6. Agregar dados por recrutador para personalização

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/kanban/transitions
    - KanbanFeedbackService
    - Modelo: implicit_feedback (candidate_id, job_id, from_column, to_column, time_in_column, recruiter_id, timestamp)
  Frontend:
    - Hook onCardMove já existente (adicionar chamada API)
  Dados:
    - Tabela implicit_feedback com índices para análise
    - Agregações por vaga, recrutador, período

Integracoes Externas:
  Nenhuma

DoD (Definition of Done):
  - [ ] API de registro de transições
  - [ ] Captura de tempo em coluna
  - [ ] Dados salvos corretamente
  - [ ] Não impacta performance do drag

Criterios de Aceitacao:
  - [ ] Cada movimento gera registro de feedback
  - [ ] Tempo em coluna calculado corretamente
  - [ ] Dados associados a candidato/vaga/recrutador
  - [ ] Performance do Kanban não afetada

Arquivos de Referencia (Prototipo Replit):
  - candidate-decision-flow-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/candidate-decision-flow-modal.tsx
  - use-transition-context.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/use-transition-context.ts
  - pipeline_stage_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/pipeline_stage_service.py
```

---

### CARD KAN-011: Disparar Triagem em Lote Dentro da Vaga
**Épico:** É11 — Kanban e Tabela de Candidatos

```yaml
Titulo: "[FULL-STACK] Disparar Triagem WSI em Lote Dentro da Vaga"
Tipo: Feature (Full-Stack)
Area: Full-Stack
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 5
Prioridade: Alta
Epic: EPIC-KAN-001
Status: 📋 A Criar no Jira
Dependencias: KAN-001, GAT-001, TRI-001

Descricao: |
  Permitir que o recrutador selecione candidatos da coluna "Funil Aprovado"
  no Kanban e dispare triagem WSI em lote via WhatsApp. Candidatos selecionados
  recebem mensagens enfileiradas e são movidos para a coluna "Em Triagem".
  Disponível tanto na visualização Kanban quanto na Table view.

Historia de Usuario: |
  Como recrutador, eu quero selecionar múltiplos candidatos aprovados
  e iniciar a triagem WSI para todos de uma vez, sem precisar disparar
  individualmente para cada candidato.

Regras de Negocio:
  1. Seleção múltipla de candidatos na coluna "Funil Aprovado"
  2. Botão "Iniciar Triagem" aparece quando há candidatos selecionados
  3. Confirmação: "Iniciar triagem WSI para N candidatos?"
  4. Mensagens WhatsApp enfileiradas (não disparo simultâneo)
  5. Candidatos movem para coluna "Em Triagem" após disparo
  6. Barra de progresso: "Enviando 3/10..."
  7. Disponível em Kanban e Table views
  8. Limite de 50 candidatos por lote
  9. Erro individual não cancela o lote inteiro

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/screening/batch-start
    - Body: { job_id, candidate_ids[] }
    - Enfileirar mensagens WhatsApp (job queue)
    - Atualizar stage de cada candidato para "em_triagem"
    - Retorno: { total, queued, errors[] }
  Frontend:
    - BatchScreeningButton (aparece quando candidatos selecionados)
    - ScreeningProgressModal (barra de progresso, status por candidato)
    - Checkbox de seleção nos cards de candidato
    - Integração com Kanban e Table views
  Dados:
    - screening_batch: id, company_id, job_id, initiated_by, candidate_ids (JSONB), total_count, queued_count, error_count, status (queued/in_progress/completed/partial_error), started_at, completed_at
  Validacoes:
    - Candidatos devem estar na coluna "Funil Aprovado"
    - Máximo 50 candidatos por lote
    - Candidato não pode ter triagem ativa

Design & Componentes:
  Componentes Existentes:
    - KanbanBoard - board existente
    - KanbanColumn - coluna existente
    - CandidateCard - card de candidato
    - Modal - container de modal
    - Progress - barra de progresso
    - Checkbox - seleção
  Novos Componentes:
    - BatchScreeningButton - botão flutuante de disparo em lote
    - ScreeningProgressModal - modal com progresso de envio
    - BatchConfirmationDialog - confirmação antes de enviar
  Design Tokens:
    Button: --wedo-cyan (#60BED1)
    Progress: --wedo-cyan (#60BED1)
    Success: --wedo-green (#22C55E)
    Error: --electric-red (#de1c31)
    Selected: bg-cyan-50, border-wedo-cyan
  Layout:
    BatchScreeningButton: fixed bottom-right quando candidatos selecionados
    ProgressModal: max-w-md, centered
    Candidate list no modal: max-h-[400px], overflow-y-auto
  Estados:
    - Hidden (nenhum candidato selecionado)
    - Visible (candidatos selecionados, botão aparece)
    - Confirming (dialog de confirmação)
    - Sending (modal de progresso)
    - Completed (resumo final)
    - Partial Error (alguns falharam)
  Acessibilidade:
    - ARIA-label no botão com contagem de selecionados
    - Progress bar com ARIA-valuenow
    - Focus trap no modal

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador seleciona candidatos na coluna "Funil Aprovado" (checkboxes)
    2. BatchScreeningButton aparece: "Iniciar Triagem (N selecionados)"
    3. Click → BatchConfirmationDialog: "Iniciar triagem WSI para N candidatos?"
    4. Confirma → ScreeningProgressModal abre
    5. Barra de progresso: "Enviando 3/10..."
    6. Candidatos movem para "Em Triagem" conforme disparo
    7. Conclusão: "10/10 triagens iniciadas com sucesso"
    8. Se erros: "8/10 iniciadas. 2 falharam: [motivos]"

  Estados de Botoes:
    Iniciar Triagem:
      - Default: bg-wedo-cyan, texto branco, ícone play
      - Hover: bg-wedo-cyan-dark
      - Disabled: opacity-50 (nenhum selecionado)

  Mensagens de Feedback:
    Sucesso: "Triagem iniciada para N candidatos!"
    Parcial: "N triagens iniciadas. X falharam."
    Erro: "Erro ao iniciar triagem em lote."

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md (Seções: 2.1 Botões, 2.19 Checkboxes, 2.4 Modais, 2.13 Progress Indicators)"
  Figma: "Seção 8.2 — Batch Screening"
  Assets:
    - "Ícone play para disparo"
    - "Ícone check para sucesso"
  Tokens:
    - "--wedo-cyan (#60BED1)"
    - "--wedo-green (#22C55E)"

DoD:
  - [ ] Seleção múltipla de candidatos funcional no Kanban
  - [ ] BatchScreeningButton aparece/desaparece corretamente
  - [ ] Confirmação antes de disparar
  - [ ] Progresso de envio em tempo real
  - [ ] Candidatos movem para "Em Triagem"
  - [ ] Funciona em Kanban e Table views
  - [ ] Limite de 50 candidatos respeitado
  - [ ] Responsivo

Criterios de Aceitacao:
  - [ ] Selecionar 5 candidatos → botão aparece com "5 selecionados"
  - [ ] Confirmar → progresso mostra "Enviando 1/5..." até 5/5
  - [ ] Candidatos movem para coluna "Em Triagem" após disparo
  - [ ] Erro em 1 candidato não cancela os outros 4
  - [ ] Resumo final mostra sucesso/falha por candidato

Arquivos de Referencia (Prototipo Replit):
  - job-kanban-page: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/job-kanban-page.tsx
  - KanbanBoard: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/kanban/components/KanbanBoard.tsx
  - KanbanColumn: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/job-kanban/KanbanColumn.tsx
```

---

### CARD KAN-012: Solicitar Novos Candidatos com Critérios Refinados
**Épico:** É11 — Kanban e Tabela de Candidatos

```yaml
Titulo: "[AI + FULL-STACK] Solicitar Novos Candidatos com Critérios Refinados"
Tipo: Feature (AI + Full-Stack)
Area: Backend-IA
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 8
Prioridade: Alta
Epic: EPIC-KAN-001
Status: 📋 A Criar no Jira
Dependencias: KAN-001, MAP-001, GAT-001

Descricao: |
  Botão "Mais candidatos" na tela da vaga que inicia nova busca
  usando a JD + feedback de aprovação/reprovação para refinar critérios.
  A LIA analisa padrões de decisão e sugere refinamentos. Candidatos
  já avaliados são automaticamente excluídos dos resultados.

Historia de Usuario: |
  Como recrutador, eu quero pedir mais candidatos para minha vaga
  com critérios refinados baseados nas decisões que já tomei,
  sem precisar refazer a busca do zero.

Regras de Negocio:
  1. Botão "Mais candidatos" no header da vaga (Kanban e Table)
  2. LIA analisa padrões de aprovação/reprovação para sugerir refinamentos
  3. Excluir automaticamente candidatos já avaliados (aprovados, reprovados, em triagem)
  4. Lista de sugestões de refinamento com aceitar/rejeitar individual
  5. LIA sugere: "Com base nas reprovações, sugiro aumentar experiência mínima para 5 anos"
  6. Recrutador pode aceitar todas, algumas ou nenhuma sugestão
  7. Nova busca executada com critérios refinados
  8. Resultados adicionados à vaga (não substituem existentes)

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/jobs/{id}/request-more-candidates
    - Body: { accepted_suggestions[], custom_criteria? }
    - Analisar padrões de aprovação/reprovação via LLM
    - Excluir candidate_ids já avaliados
    - Retornar: { suggestions[], new_candidates[] }
  Frontend:
    - RefinedSearchModal - modal com sugestões e resultados
    - SuggestionsList - lista de sugestões com aceitar/rejeitar
    - AddMoreButton - botão no header da vaga
  Dados:
    - refinement_sessions: id, company_id, job_id, recruiter_id, suggestions (JSONB), accepted_suggestions (JSONB), new_candidate_ids (JSONB), search_criteria_snapshot (JSONB), created_at

Integracoes Externas:
  LLM (Gemini):
    - Tipo: AI API
    - Uso: Análise de padrões de decisão para sugerir refinamentos de busca
    - Serviço: candidate_refinement_service.py
    - SDK: google-generativeai
    - Secret: GEMINI_API_KEY
    - Custo: ~$0.01-0.03 por análise (Pro)
    - Rate Limit: 60 RPM
    - Documentacao: https://ai.google.dev/docs

Configuracao LLM:
  Modelo: Gemini 2.5 Pro (análise complexa de padrões)
  Temperatura: 0.5
  Max Tokens: 1500
  Uso: Analisar padrões de decisão e gerar sugestões de refinamento em linguagem natural
  
  Prompt Template: |
    <role>
    Você é especialista em talent acquisition da plataforma WeDo Talent.
    Analise os padrões de aprovação/reprovação e sugira refinamentos
    nos critérios de busca para encontrar candidatos mais adequados.
    </role>
    
    <context>
    Vaga: {{job_title}} ({{job_id}})
    Critérios atuais: {{current_criteria}}
    Candidatos avaliados: {{evaluated_count}}
    Aprovados: {{approved_count}} ({{approval_rate}}%)
    Reprovados: {{rejected_count}}
    </context>
    
    <rejection_patterns>
    {{rejection_analysis}}
    </rejection_patterns>
    
    <task>
    Sugira até 5 refinamentos nos critérios de busca baseados nos padrões.
    Cada sugestão deve ter justificativa baseada nos dados.
    </task>
    
    <output_format>
    {
      "suggestions": [
        {
          "field": "experience_years|skills|education|location|salary",
          "current_value": "...",
          "suggested_value": "...",
          "justification": "...",
          "expected_impact": "high|medium|low"
        }
      ]
    }
    </output_format>

Design & Componentes:
  Componentes Existentes:
    - JobKanbanPage - página da vaga
    - SmartSearchInput - input de busca
    - Modal - container
    - Button - ações
  Novos Componentes:
    - RefinedSearchModal - modal principal
    - SuggestionsList - lista de sugestões
    - SuggestionCard - card individual com aceitar/rejeitar
    - AddMoreCandidatesButton - botão no header
  Design Tokens:
    Suggestion: --wedo-cyan-light (#E0F4F8)
    Accepted: --wedo-green (#22C55E)
    Rejected: --electric-red-light (#FEE2E2)
    Button: --wedo-cyan (#60BED1)
  Layout:
    Modal: max-w-2xl, centered
    SuggestionsList: flex flex-col gap-3
    SuggestionCard: border rounded, p-4, flex justify-between
  Estados:
    - Loading (analisando padrões...)
    - Suggestions Ready (lista de sugestões)
    - Searching (buscando com critérios refinados)
    - Results (novos candidatos encontrados)
    - Empty (nenhum candidato novo encontrado)
  Acessibilidade:
    - Focus trap no modal
    - ARIA-label nos botões aceitar/rejeitar
    - Screen reader anuncia sugestões

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador clica "Mais candidatos" no header da vaga
    2. RefinedSearchModal abre com loading: "Analisando padrões de decisão..."
    3. LIA apresenta sugestões de refinamento
    4. Recrutador aceita/rejeita sugestões individualmente
    5. Clica "Buscar com refinamentos"
    6. Loading: "Buscando candidatos com critérios refinados..."
    7. Resultados aparecem com opção de adicionar à vaga

  Estados de Botoes:
    Mais Candidatos:
      - Default: outline, border-wedo-cyan, texto cyan
      - Hover: bg-wedo-cyan, texto branco
    Aceitar Sugestão:
      - Default: bg-green-50, texto green
      - Active: bg-green-500, texto branco
    Rejeitar Sugestão:
      - Default: bg-red-50, texto red
      - Active: bg-red-500, texto branco

  Mensagens de Feedback:
    Analisando: "Analisando padrões de decisão..."
    Buscando: "Buscando candidatos com critérios refinados..."
    Sucesso: "N novos candidatos encontrados!"
    Vazio: "Nenhum candidato novo encontrado com esses critérios."

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md (Seções: 2.4 Modais, 2.3 Cards, 2.1 Botões, 2.6 Badges & Tags)"
  Figma: "Seção 8.2 — Refined Search"
  Assets:
    - "Ícone de busca refinada"
    - "Ícone de sugestão IA"
  Tokens:
    - "--wedo-cyan (#60BED1)"
    - "--wedo-green (#22C55E)"

DoD:
  - [ ] Análise de padrões via Gemini 2.5 Pro funcional
  - [ ] Sugestões de refinamento geradas corretamente
  - [ ] Aceitar/rejeitar sugestões funcional
  - [ ] Busca refinada executada com exclusão de já avaliados
  - [ ] Novos candidatos adicionados à vaga
  - [ ] Modal responsivo

Criterios de Aceitacao:
  - [ ] Botão "Mais candidatos" visível no header da vaga
  - [ ] Sugestões baseadas em padrões reais de decisão
  - [ ] Candidatos já avaliados não aparecem nos resultados
  - [ ] Aceitar sugestão reflete no critério de busca
  - [ ] Novos candidatos adicionados com sucesso à vaga

Arquivos de Referencia (Prototipo Replit):
  - job-kanban-page: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/job-kanban-page.tsx
  - smart-search-input: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/smart-search-input.tsx
```

---

### CARD KAN-013: Buscar Candidatos Similares
**Épico:** É11 — Kanban e Tabela de Candidatos

```yaml
Titulo: "[AI + FULL-STACK] Buscar Candidatos Similares via Embedding"
Tipo: Feature (AI + Full-Stack)
Area: Backend-IA
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 5
Prioridade: Média
Epic: EPIC-KAN-001
Status: 📋 A Criar no Jira
Dependencias: KAN-002, MAP-001

Descricao: |
  Ação "Buscar similares" no menu de contexto do card de candidato.
  Usa embedding do perfil do candidato para busca semântica por vetor,
  retornando top 10 candidatos mais similares. Filtra por vaga (exclui
  candidatos já avaliados). Score de similaridade (%) exibido.

Historia de Usuario: |
  Como recrutador, eu quero encontrar candidatos similares a um perfil
  que aprovei, para ampliar o pool de candidatos qualificados sem
  precisar refazer a busca manualmente.

Regras de Negocio:
  1. Ação disponível no menu de contexto do card de candidato
  2. Busca baseada em embedding do perfil (vetor semântico)
  3. Retorna top 10 candidatos mais similares
  4. Filtrar por vaga: excluir candidatos já avaliados na vaga atual
  5. Score de similaridade (%) exibido em cada resultado
  6. Botão "Adicionar à vaga" em cada resultado
  7. Candidato base exibido no topo do modal para referência

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/candidates/{id}/find-similar
    - Body: { job_id?, limit: 10, exclude_ids[]? }
    - Embedding-based vector search (cosine similarity)
    - Retorno: { base_candidate, similar_candidates[{ candidate, similarity_score }] }
  Frontend:
    - SimilarCandidatesModal - modal com resultados
    - SimilarityScoreBadge - badge com % de similaridade
    - AddToJobButton - botão para adicionar candidato à vaga
  Dados:
    - candidate_embeddings: candidate_id, embedding (vector), updated_at
    - similar_searches: id, base_candidate_id, job_id, results (JSONB), created_at

Integracoes Externas:
  Embedding Service:
    - Tipo: AI API (Embedding)
    - Uso: Gerar embedding do perfil do candidato para busca por similaridade vetorial
    - Serviço: candidate_similarity_service.py
    - SDK: google-generativeai (text-embedding-004)
    - Secret: GEMINI_API_KEY
    - Custo: ~$0.001 por embedding
    - Documentacao: https://ai.google.dev/docs/embeddings
  Vector Database:
    - Tipo: pgvector (extensão PostgreSQL)
    - Uso: Armazenar e buscar embeddings por similaridade cosine
    - Índice: ivfflat ou hnsw para performance
    - Coluna: candidate_embeddings.embedding (vector(768))

Configuracao LLM:
  Modelo Embedding: text-embedding-004 (Google)
  Dimensões: 768
  Busca: Cosine similarity via pgvector
  Top K: 10 resultados
  Threshold: similarity >= 0.7 (70%)
  
  Fluxo:
    1. Perfil do candidato base → texto concatenado (skills + experiência + educação)
    2. Gerar embedding via text-embedding-004
    3. Buscar top 10 candidatos similares via pgvector (cosine similarity)
    4. Filtrar: excluir já avaliados na vaga, similarity >= 0.7
    5. Retornar com score de similaridade (%)

Design & Componentes:
  Componentes Existentes:
    - CandidateCard - card de candidato (menu de contexto)
    - KanbanCard - card na view Kanban
    - Modal - container
    - Badge - indicadores
    - Button - ações
  Novos Componentes:
    - SimilarCandidatesModal - modal com lista de similares
    - SimilarityScoreBadge - badge circular com %
    - SimilarCandidateCard - card compacto de candidato similar
  Design Tokens:
    High Similarity (>80%): --wedo-green (#22C55E)
    Medium Similarity (60-79%): --wedo-cyan (#60BED1)
    Low Similarity (<60%): --wedo-yellow (#EAB308)
    Badge Background: bg-transparent
    Badge Border: border-2
  Layout:
    Modal: max-w-2xl, centered
    Base Candidate: border-b, p-4, bg-secondary (referência)
    Similar List: flex flex-col gap-3, max-h-[500px] overflow-y-auto
    SimilarCandidateCard: flex items-center justify-between, p-3, border rounded
    SimilarityBadge: w-12 h-12, rounded-full, flex items-center justify-center
  Estados:
    - Loading (buscando similares...)
    - Results (lista de similares)
    - Empty (nenhum similar encontrado)
    - Adding (adicionando candidato à vaga)
  Acessibilidade:
    - Focus trap no modal
    - ARIA-label com score de similaridade
    - Lista navegável via keyboard

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador clica menu de contexto (⋮) no card de candidato
    2. Seleciona "Buscar similares"
    3. SimilarCandidatesModal abre com loading
    4. Candidato base exibido no topo (referência)
    5. Lista de top 10 similares com score (%)
    6. Recrutador clica "Adicionar à vaga" em candidatos desejados
    7. Candidato adicionado → toast de confirmação

  Estados de Botoes:
    Buscar Similares (menu):
      - Default: texto com ícone de busca
      - Hover: bg-gray-100
    Adicionar à Vaga:
      - Default: outline, border-wedo-cyan
      - Hover: bg-wedo-cyan, texto branco
      - Added: bg-green-50, texto green, ícone check

  Mensagens de Feedback:
    Buscando: "Buscando candidatos similares..."
    Sucesso: "Candidato adicionado à vaga com sucesso!"
    Vazio: "Nenhum candidato similar encontrado."

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md (Seções: 2.4 Modais, 2.3 Cards, 2.6 Badges & Tags, 2.14 Avatars)"
  Figma: "Seção 8.2 — Similar Candidates"
  Assets:
    - "Ícone de busca similar (DNA/fingerprint)"
  Tokens:
    - "--wedo-green (#22C55E)"
    - "--wedo-cyan (#60BED1)"
    - "--wedo-yellow (#EAB308)"

DoD:
  - [ ] Busca por similaridade via embedding funcional
  - [ ] Top 10 resultados com score de similaridade
  - [ ] Exclusão de candidatos já avaliados na vaga
  - [ ] Modal renderizando corretamente
  - [ ] Adicionar candidato à vaga funcional
  - [ ] Ação disponível no menu de contexto do card

Criterios de Aceitacao:
  - [ ] Menu de contexto mostra "Buscar similares"
  - [ ] Modal exibe candidato base + top 10 similares
  - [ ] Score de similaridade (%) visível em cada resultado
  - [ ] "Adicionar à vaga" funciona e atualiza Kanban
  - [ ] Candidatos já na vaga não aparecem nos resultados

Arquivos de Referencia (Prototipo Replit):
  - CandidateCard: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/kanban/components/CandidateCard.tsx
  - KanbanCard: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/job-kanban/KanbanCard.tsx
```

---

### CARD TAB-001: Tabela de Candidatos
**Épico:** É11 — Kanban e Tabela de Candidatos

```yaml
Titulo: [FRONTEND] Tabela de Candidatos
Tipo: Frontend
Area: Frontend
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 8
Prioridade: Alta
Epic: EPIC-KAN-001
Status: 📋 Pendente Jira

Descricao: |
  Implementar visualização em tabela dos candidatos como
  alternativa ao Kanban. Tabela com colunas configuráveis,
  ordenação e seleção para ações em massa.

Historia de Usuario: |
  Como recrutador, eu quero ver candidatos em formato de
  tabela para ter uma visão mais detalhada e poder comparar
  múltiplos candidatos lado a lado.

Regras de Negocio:
  1. Toggle entre visualização Kanban e Tabela
  2. Colunas padrão: Checkbox, Nome, Email, Telefone, Etapa, Score, Data adição, Ações
  3. Colunas ordenáveis (clique no header)
  4. Row highlight no hover
  5. Click na row abre preview lateral
  6. Checkbox para seleção múltipla

Requisitos Tecnicos:
  Frontend:
    - CandidatesTable component
    - TanStack Table ou similar
    - Column definitions
    - Row selection state
  Backend:
    - GET /api/backend-proxy/candidates?view=table

Integracoes Externas:
  Nenhuma

Design & Componentes:
  Componentes Existentes:
    - Table, TableHeader, TableBody, TableRow, TableCell - shadcn/ui
    - Checkbox - seleção
    - Badge - etapa e score
  Novos Componentes:
    - CandidatesTable - tabela completa
    - ViewToggle - switch Kanban/Tabela
  Design Tokens:
    Header Background: --lia-bg-secondary (#F9FAFB)
    Header Text: --lia-text-secondary, font-medium
    Row Background: --lia-bg-primary
    Row Hover: --lia-interactive-hover
    Row Selected: --wedo-cyan-light (10%)
    Border: --lia-border-subtle
  Layout:
    Table: w-full
    Columns: resizable, min-widths definidos
    Header: sticky top
    Rows: h-14
  Estados:
    - Loading (skeleton rows)
    - Empty (mensagem "Nenhum candidato")
    - Loaded (rows com dados)
    - Row hover (highlight)
    - Row selected (checkbox + background)
  Acessibilidade:
    - Table com role adequado
    - Headers anunciados
    - Keyboard navigation entre cells

Comportamento de UI:
  Fluxo Principal:
    1. Toggle "Tabela" ativado (vs Kanban)
    2. Tabela renderiza com candidatos
    3. Headers clicáveis para ordenar
    4. Hover destaca row
    5. Click na row abre preview lateral
    6. Checkbox seleciona para ações em massa
  
  Colunas Padrão:
    | ☐ | Nome | Email | Telefone | Etapa | Score | Adicionado | ... |
  
  Ordenação:
    - Click no header: ordena ascendente
    - Click novamente: ordena descendente
    - Click terceiro: remove ordenação
    - Ícone de seta indica direção

DoD (Definition of Done):
  - [ ] Tabela renderiza corretamente
  - [ ] Toggle Kanban/Tabela funciona
  - [ ] Ordenação por coluna funciona
  - [ ] Seleção múltipla funciona
  - [ ] Click abre preview
  - [ ] Responsivo (scroll horizontal)


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

Criterios de Aceitacao:
  - [ ] Todos os candidatos listados
  - [ ] Colunas ordenáveis
  - [ ] Checkbox seleciona row
  - [ ] Hover destaca row
  - [ ] Performance OK com muitos candidatos

Arquivos de Referencia (Prototipo Replit):
  - CandidatesTable.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/candidates/CandidatesTable.tsx
  - CandidatesHeader.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/candidates/CandidatesHeader.tsx
  - types.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/candidates/types.ts
  - types.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/tables/types.ts
```

---

### CARD TAB-002: Colunas Ordenáveis
**Épico:** É11 — Kanban e Tabela de Candidatos

```yaml
Titulo: [FRONTEND] Colunas Ordenáveis na Tabela
Tipo: Frontend
Area: Frontend
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 3
Prioridade: Media
Epic: EPIC-KAN-001
Status: 📋 Pendente Jira
Dependencias: TAB-001

Descricao: |
  Implementar ordenação de colunas na tabela de candidatos.
  Click no header ordena por aquela coluna, com indicador
  visual da direção de ordenação.

Historia de Usuario: |
  Como recrutador, eu quero ordenar a tabela por diferentes
  colunas para encontrar rapidamente os candidatos mais
  relevantes (ex: maior score, mais recentes).

Regras de Negocio:
  1. Click no header ativa ordenação
  2. Primeiro click: ascendente (A-Z, 0-100)
  3. Segundo click: descendente (Z-A, 100-0)
  4. Terceiro click: remove ordenação
  5. Apenas uma coluna ordenada por vez
  6. Ícone de seta indica direção
  7. Colunas não ordenáveis: Checkbox, Ações

Requisitos Tecnicos:
  Frontend:
    - Sorting state management
    - SortableHeader component
    - Sort icon component
  Backend:
    - Query param: ?sort=score&order=desc

Integracoes Externas:
  Nenhuma

Design & Componentes:
  Componentes Existentes:
    - TableHeader - shadcn/ui
  Novos Componentes:
    - SortableHeader - header com ícone de sort
    - SortIcon - ícone de seta up/down/neutral
  Design Tokens:
    Header Active: --lia-text-primary
    Sort Icon: --lia-text-tertiary (inactive), --wedo-cyan (active)
  Layout:
    Header: flex, items-center, gap-1
    Sort Icon: 12x12px
  Estados:
    - Unsorted (ícone neutro ou hidden)
    - Ascending (seta para cima)
    - Descending (seta para baixo)
    - Hover (cursor pointer, ícone destaca)
  Acessibilidade:
    - aria-sort no header
    - Screen reader anuncia mudança de ordenação

Comportamento de UI:
  Fluxo Principal:
    1. Hover no header mostra ícone de ordenação (se ordenável)
    2. Click no header "Score"
    3. Tabela ordena por Score ascendente (menor primeiro)
    4. Ícone muda para seta para cima
    5. Click novamente: descendente (maior primeiro)
    6. Seta muda para baixo
    7. Click terceiro: remove ordenação, tabela volta ao default
  
  Visual:

Arquivos de Referencia (Prototipo Replit):
  - CandidatesTable.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/candidates/CandidatesTable.tsx
  - useTableFeatures.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/useTableFeatures.ts
  - use-table-features.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/use-table-features.tsx
    ```
    | Nome ↕ | Score ▲ | Data ↕ |
    ```
    ↕ = neutro (pode ordenar)
    ▲ = ascendente ativo
    ▼ = descendente ativo

DoD (Definition of Done):
  - [ ] Headers clicáveis para ordenar
  - [ ] 3 estados de ordenação (asc, desc, none)
  - [ ] Ícone visual correto
  - [ ] Ordenação aplica nos dados
  - [ ] URL reflete ordenação

Criterios de Aceitacao:
  - [ ] Click ordena corretamente
  - [ ] Ícone indica direção
  - [ ] Terceiro click remove ordenação
  - [ ] Checkbox e Ações não são ordenáveis
```

---

### CARD TAB-003: Seleção Múltipla
**Épico:** É11 — Kanban e Tabela de Candidatos

```yaml
Titulo: [FRONTEND] Seleção Múltipla na Tabela
Tipo: Frontend
Area: Frontend
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 3
Prioridade: Alta
Epic: EPIC-KAN-001
Status: 📋 Pendente Jira
Dependencias: TAB-001

Descricao: |
  Implementar seleção múltipla de candidatos na tabela usando
  checkboxes. Checkbox no header seleciona/deseleciona todos.
  Seleção habilita barra de ações em massa.

Historia de Usuario: |
  Como recrutador, eu quero selecionar múltiplos candidatos
  de uma vez para aplicar ações em massa como aprovar,
  reprovar ou enviar mensagem.

Regras de Negocio:
  1. Checkbox em cada row para seleção individual
  2. Checkbox no header para selecionar/deselecionar todos
  3. Shift+Click para seleção de range
  4. Contador de selecionados exibido
  5. Seleção persiste durante paginação
  6. Barra de ações aparece quando há seleção (TAB-005)

Requisitos Tecnicos:
  Frontend:
    - Selection state (Set ou Array de IDs)
    - Shift+Click logic
    - Header checkbox indeterminate state
  Backend:
    - N/A (seleção é client-side)

Integracoes Externas:
  Nenhuma

Design & Componentes:
  Componentes Existentes:
    - Checkbox - shadcn/ui
  Novos Componentes:
    - SelectionHeader - checkbox do header
    - SelectableRow - row com checkbox
    - SelectionCounter - "X selecionados"
  Design Tokens:
    Checkbox Checked: --wedo-cyan
    Row Selected: --wedo-cyan-light (10%)
    Counter: --lia-text-secondary
  Layout:
    Checkbox Column: w-12, text-center
    Counter: inline no header ou na barra de ações
  Estados:
    - None selected (checkbox empty)
    - Some selected (header checkbox indeterminate)
    - All selected (header checkbox checked)
    - Row selected (checkbox + background)
  Acessibilidade:
    - Checkbox com label (candidato nome)
    - Shift+Click anunciado
    - Contador anunciado para screen readers

Comportamento de UI:
  Fluxo Principal:
    1. Tabela com checkboxes na primeira coluna
    2. Click no checkbox de uma row: seleciona
    3. Click no checkbox do header:
       - Se nenhum selecionado: seleciona todos
       - Se alguns selecionados: seleciona todos
       - Se todos selecionados: deseleciona todos
    4. Shift+Click: seleciona range do último clicado ao atual
    5. Contador atualiza: "5 selecionados"
    6. Barra de ações aparece (TAB-005)
  
  Estados do Header Checkbox:
    - ☐ Empty: nenhum selecionado
    - ▣ Indeterminate: alguns selecionados
    - ☑ Checked: todos selecionados

DoD (Definition of Done):
  - [ ] Checkbox em cada row funciona
  - [ ] Header checkbox funciona
  - [ ] Shift+Click seleciona range
  - [ ] Contador de selecionados
  - [ ] Seleção persiste na paginação
  - [ ] Acessível


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

Criterios de Aceitacao:
  - [ ] Seleção individual funciona
  - [ ] Selecionar todos funciona
  - [ ] Indeterminate state correto
  - [ ] Shift+Click funciona
  - [ ] Contador atualiza corretamente

Arquivos de Referencia (Prototipo Replit):
  - CandidatesTable.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/candidates/CandidatesTable.tsx
  - useCandidatesSelection.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/candidates/hooks/useCandidatesSelection.ts
  - bulk-actions-bar.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/bulk-actions-bar.tsx
```

---

### CARD TAB-004: Paginação
**Épico:** É11 — Kanban e Tabela de Candidatos

```yaml
Titulo: [FRONTEND] Paginação da Tabela
Tipo: Frontend
Area: Frontend
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 5
Prioridade: Media
Epic: EPIC-KAN-001
Status: 📋 Pendente Jira
Dependencias: TAB-001

Descricao: |
  Implementar paginação na tabela de candidatos com controles
  de navegação, seletor de itens por página e informação de
  posição atual.

Historia de Usuario: |
  Como recrutador, eu quero navegar entre páginas de candidatos
  e escolher quantos ver por página para gerenciar listas
  grandes de forma eficiente.

Regras de Negocio:
  1. Paginação no footer da tabela
  2. Itens por página: 10, 25, 50, 100
  3. Navegação: Primeira, Anterior, Próxima, Última
  4. Indicador: "Mostrando 1-25 de 150"
  5. Manter ordenação e filtros ao paginar
  6. Manter seleção ao paginar

Requisitos Tecnicos:
  Frontend:
    - Pagination component
    - PageSizeSelect component
    - usePagination hook
  Backend:
    - GET /api/backend-proxy/candidates?page=2&limit=25

Integracoes Externas:
  Nenhuma

Design & Componentes:
  Componentes Existentes:
    - Button - navegação
    - Select - itens por página
  Novos Componentes:
    - TablePagination - container de paginação
    - PageSizeSelect - select de itens por página
  Design Tokens:
    Background: --lia-bg-secondary
    Button Disabled: --lia-text-tertiary
    Button Active: --wedo-cyan
    Text: --lia-text-secondary
  Layout:
    Container: flex justify-between, padding-4
    Left: info "Mostrando X-Y de Z"
    Right: controles de navegação + select
  Estados:
    - First page (Previous disabled)
    - Last page (Next disabled)
    - Middle page (all enabled)
    - Loading (skeleton)
  Acessibilidade:
    - Botões com aria-label
    - Anúncio de página atual
    - Keyboard navigation

Comportamento de UI:
  Fluxo Principal:
    1. Tabela carrega com 25 itens (default)
    2. Footer mostra: "Mostrando 1-25 de 150 candidatos"
    3. Botões de navegação: ◀◀ ◀ Página 1 de 6 ▶ ▶▶
    4. Click em "Próxima" carrega página 2
    5. Info atualiza: "Mostrando 26-50 de 150"
    6. Select "Itens por página": escolher 50
    7. Tabela recarrega com 50 itens, volta para página 1
  
  Layout:

Arquivos de Referencia (Prototipo Replit):
  - CandidatesTable.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/candidates/CandidatesTable.tsx
  - useSearchFlow.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/useSearchFlow.ts
  - use-talent-funnel.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/use-talent-funnel.ts
    ```
    ┌─────────────────────────────────────────────────────────┐
    │ Mostrando 1-25 de 150    | ◀◀ ◀ [1] 2 3 ... 6 ▶ ▶▶ | 25 ▼│
    └─────────────────────────────────────────────────────────┘
    ```
  
  Estados de Botões:
    - ◀◀ (Primeira): disabled se página 1
    - ◀ (Anterior): disabled se página 1
    - ▶ (Próxima): disabled se última página
    - ▶▶ (Última): disabled se última página

DoD (Definition of Done):
  - [ ] Controles de navegação funcionam
  - [ ] Select de itens por página funciona
  - [ ] Indicador de posição correto
  - [ ] Ordenação mantida ao paginar
  - [ ] Seleção mantida ao paginar
  - [ ] URL reflete página atual

Criterios de Aceitacao:
  - [ ] Navegação entre páginas funciona
  - [ ] Itens por página altera corretamente
  - [ ] Primeiro/Último page funciona
  - [ ] Info atualiza corretamente
  - [ ] Performance OK
```

---

### CARD TAB-005: Ações em Massa (Barra Sticky)
**Épico:** É11 — Kanban e Tabela de Candidatos

```yaml
Titulo: [FRONTEND] Barra de Ações em Massa (Sticky)
Tipo: Frontend
Area: Frontend
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 8
Prioridade: Alta
Epic: EPIC-KAN-001
Status: 📋 Pendente Jira
Dependencias: TAB-003

Descricao: |
  Implementar barra sticky que aparece quando há candidatos
  selecionados, oferecendo ações em massa como aprovar,
  reprovar, enviar mensagem, mover etapa.

Historia de Usuario: |
  Como recrutador, eu quero aplicar ações em múltiplos
  candidatos de uma vez para agilizar meu trabalho quando
  preciso processar muitos candidatos.

Regras de Negocio:
  1. Barra aparece quando há 1+ candidatos selecionados
  2. Ações disponíveis variam por etapa dos selecionados
  3. Ações: Aprovar, Reprovar, Mover etapa, Enviar mensagem, Exportar
  4. Confirmação para ações destrutivas
  5. Feedback de progresso para ações em massa
  6. "Limpar seleção" para deselecionar todos

Requisitos Tecnicos:
  Backend:
    - POST /api/backend-proxy/candidates/bulk/approve
    - POST /api/backend-proxy/candidates/bulk/reject
    - POST /api/backend-proxy/candidates/bulk/move-stage
    - POST /api/backend-proxy/candidates/bulk/send-message
  Frontend:
    - BulkActionsBar component
    - BulkActionButton component
    - Progress indicator

Integracoes Externas:
  Nenhuma

Design & Componentes:
  Componentes Existentes:
    - Button - ações
    - Dialog - confirmação
    - Progress - indicador de progresso
  Novos Componentes:
    - BulkActionsBar - barra sticky
    - BulkActionProgress - modal de progresso
  Design Tokens:
    Bar Background: --lia-bg-primary com shadow
    Bar Border: --lia-border-subtle
    Primary Action: --wedo-cyan
    Destructive Action: --electric-red
    Counter: --wedo-cyan background
  Layout:
    Bar: fixed bottom-0, w-full, padding-4, z-50
    Content: max-w-screen-xl mx-auto, flex justify-between
    Left: contador de selecionados
    Right: botões de ação
  Estados:
    - Hidden (nenhum selecionado)
    - Visible (1+ selecionados)
    - Processing (ação em andamento)
  Acessibilidade:
    - Anúncio quando barra aparece
    - Focus management
    - Escape para fechar/cancelar

Comportamento de UI:
  Fluxo Principal:
    1. Usuário seleciona candidatos (TAB-003)
    2. Barra aparece com slide up animation
    3. Mostra: "5 candidatos selecionados" + botões de ação
    4. Click em "Aprovar todos":
       - Modal de confirmação: "Aprovar 5 candidatos para triagem?"
       - Confirmar → Progress: "Aprovando... 3/5"
       - Conclusão → Toast: "5 candidatos aprovados"
    5. "Limpar seleção" deseleciona e esconde barra
  
  Layout da Barra:

Arquivos de Referencia (Prototipo Replit):
  - bulk-actions-bar.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/bulk-actions-bar.tsx
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/backend-proxy/candidates/bulk/update-status/route.ts
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/backend-proxy/candidates/bulk/send-email/route.ts
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/backend-proxy/candidates/bulk/export/route.ts
    ```
    ┌─────────────────────────────────────────────────────────────────┐
    │  [5] candidatos selecionados   [Limpar]    [Mensagem] [Aprovar] │
    └─────────────────────────────────────────────────────────────────┘
    ```
  
  Ações Disponíveis:
    - ✅ Aprovar: move para próxima etapa
    - ❌ Reprovar: move para Reprovados (confirmação)
    - 📧 Enviar mensagem: abre modal de composição
    - 📥 Exportar: download CSV/Excel
    - 🗑️ Limpar seleção: deseleciona todos
  
  Progress Modal:
    - Título: "Processando..."
    - Barra de progresso: 60% (3/5)
    - Lista de candidatos processados
    - Botão cancelar (se possível)

DoD (Definition of Done):
  - [ ] Barra aparece com seleção
  - [ ] Ações variam por etapa
  - [ ] Confirmação para ações destrutivas
  - [ ] Progress indicator funciona
  - [ ] Feedback de conclusão
  - [ ] Limpar seleção funciona

Criterios de Aceitacao:
  - [ ] Barra slide up suavemente
  - [ ] Contador correto
  - [ ] Todas ações funcionam
  - [ ] Progress mostra andamento
  - [ ] Toast de conclusão
  - [ ] Barra some ao limpar seleção
```

---

### CARD PRV-001: Preview Lateral do Candidato
**Épico:** É11 — Kanban e Tabela de Candidatos

```yaml
Titulo: [FRONTEND] Preview Lateral do Candidato
Tipo: Frontend
Area: Frontend
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 8
Prioridade: Alta
Epic: EPIC-KAN-001
Status: 📋 Pendente Jira
Dependencias: KAN-002

Descricao: |
  Implementar painel lateral (slide panel) que mostra detalhes
  do candidato ao clicar em um card do Kanban ou row da tabela.
  Panel com tabs para diferentes seções de informação.

Historia de Usuario: |
  Como recrutador, eu quero ver detalhes do candidato em um
  painel lateral sem sair da visualização do Kanban/Tabela
  para agilizar a revisão.

Regras de Negocio:
  1. Panel desliza da direita
  2. Header com foto, nome, cargo e ações principais
  3. Tabs: Perfil, Atividades, Arquivos, Parecer LIA
  4. Fechamento: botão X, click fora, ESC
  5. Navegação entre candidatos (setas ←→)
  6. Responsivo (full screen em mobile)

Requisitos Tecnicos:
  Frontend:
    - CandidatePreviewPanel component
    - Sheet/SlidePanel from shadcn/ui
    - Tab navigation
    - Keyboard navigation
  Backend:
    - GET /api/backend-proxy/candidates/{id}/full

Integracoes Externas:
  Nenhuma

Design & Componentes:
  Componentes Existentes:
    - Sheet - slide panel shadcn/ui
    - Tabs - navegação entre seções
    - Avatar - foto do candidato
    - Button - ações
  Novos Componentes:
    - CandidatePreviewPanel - painel completo
    - PreviewHeader - header com info básica
    - PreviewTabs - tabs de conteúdo
  Design Tokens:
    Panel Background: --lia-bg-primary
    Panel Shadow: --lia-shadow-xl
    Header Background: --lia-bg-secondary
    Tab Active: --wedo-cyan
  Layout:
    Panel Width: 400px (desktop), 100% (mobile)
    Header: sticky top, h-20
    Tabs: sticky below header
    Content: scroll interno
  Estados:
    - Closed (hidden)
    - Opening (animação slide)
    - Open (visível)
    - Loading (skeleton no conteúdo)
  Acessibilidade:
    - Focus trap quando aberto
    - ESC para fechar
    - Aria-label no panel
    - Arrow keys para navegar candidatos

Comportamento de UI:
  Fluxo Principal:
    1. Click em card do Kanban ou row da Tabela
    2. Panel desliza da direita (300ms ease-out)
    3. Header mostra foto, nome, cargo do candidato
    4. Tabs carregam: Perfil | Atividades | Arquivos | Parecer LIA
    5. Default: tab Perfil selecionada
    6. Setas ←→ no header navegam para anterior/próximo candidato
    7. X ou click fora fecha o panel
  
  Layout do Header:

Arquivos de Referencia (Prototipo Replit):
  - candidate-page.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/candidate-page.tsx
  - candidate-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/candidate-modal.tsx
    ```
    ┌─────────────────────────────────────────┐
    │ ← →  [Avatar] Nome Sobrenome          X │
    │              Cargo Atual                │
    │ [Aprovar] [Reprovar] [Enviar Mensagem] │
    └─────────────────────────────────────────┘
    ```
  
  Tabs:
    - Perfil: dados pessoais, experiência, skills (PRV-002)
    - Atividades: timeline de interações (PRV-003)
    - Arquivos: CV, documentos anexados (PRV-004)
    - Parecer LIA: análise AI, score WSI (PRV-005)

DoD (Definition of Done):
  - [ ] Panel abre e fecha corretamente
  - [ ] Header com info básica
  - [ ] 4 tabs funcionam
  - [ ] Navegação entre candidatos
  - [ ] Fechamento por X, click fora, ESC
  - [ ] Responsivo

Criterios de Aceitacao:
  - [ ] Click no card abre panel
  - [ ] Animação suave de slide
  - [ ] Tabs navegam corretamente
  - [ ] Setas navegam candidatos
  - [ ] ESC fecha panel
```

---

### CARD PRV-002: Tab Perfil
**Épico:** É11 — Kanban e Tabela de Candidatos

```yaml
Titulo: [FRONTEND] Tab Perfil no Preview
Tipo: Frontend
Area: Frontend
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 5
Prioridade: Alta
Epic: EPIC-KAN-001
Status: 📋 Pendente Jira
Dependencias: PRV-001

Descricao: |
  Implementar conteúdo da tab Perfil no preview lateral,
  mostrando informações pessoais, experiência profissional,
  formação e skills do candidato.

Historia de Usuario: |
  Como recrutador, eu quero ver o perfil completo do candidato
  de forma organizada para avaliar rapidamente sua adequação
  à vaga.

Regras de Negocio:
  1. Seções: Contato, Resumo, Experiência, Formação, Skills
  2. Experiência em timeline cronológica (mais recente primeiro)
  3. Skills com badges coloridos
  4. Links clicáveis (email, telefone, LinkedIn)
  5. Highlight de skills que matcham com a vaga

Requisitos Tecnicos:
  Frontend:
    - ProfileTab component
    - ExperienceTimeline component
    - SkillBadges component
  Backend:
    - (usa dados do GET /candidates/{id}/full)

Integracoes Externas:
  Nenhuma

Design & Componentes:
  Componentes Existentes:
    - Card - seções
    - Badge - skills
    - Link - contatos clicáveis
  Novos Componentes:
    - ProfileSection - seção genérica
    - ExperienceCard - card de experiência
    - SkillBadge - badge de skill com cor
  Design Tokens:
    Section Title: --lia-text-primary, font-semibold
    Section Content: --lia-text-secondary
    Skill Match: --wedo-green background
    Skill Normal: --lia-bg-tertiary
    Link: --wedo-cyan
  Layout:
    Container: padding-4, space-y-6
    Section: card com título e conteúdo
    Experience: timeline vertical
    Skills: flex wrap, gap-2
  Estados:
    - Loading (skeleton)
    - Loaded (dados exibidos)
    - Error (retry button)
  Acessibilidade:
    - Headings por seção
    - Links descritivos
    - Lista de skills navegável

Comportamento de UI:
  Fluxo Principal:
    1. Tab Perfil selecionada
    2. Seções carregam em ordem:
       - Contato: email (link), telefone (link), LinkedIn (link)
       - Resumo: texto livre do candidato
       - Experiência: lista de cargos anteriores
       - Formação: graduação, cursos
       - Skills: badges com skills técnicas e soft skills
    3. Skills que matcham com vaga têm destaque verde
    4. Click em email abre mailto:
    5. Click em telefone abre tel:
    6. Click em LinkedIn abre nova aba
  
  Layout de Experiência:

Arquivos de Referencia (Prototipo Replit):
  - candidate-page.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/candidate-page.tsx
  - wsi_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_service.py
    ```
    ○ Cargo Atual - Empresa
      Jan 2023 - Presente
      Descrição resumida...
    │
    ○ Cargo Anterior - Empresa
      Jan 2021 - Dez 2022
      Descrição resumida...
    ```
  
  Layout de Skills:
    ```
    [Python ✓] [React ✓] [Node.js] [SQL] [Comunicação ✓]
    ```
    ✓ = match com requisitos da vaga

DoD (Definition of Done):
  - [ ] Todas as seções renderizam
  - [ ] Links funcionam
  - [ ] Timeline de experiência
  - [ ] Skills com highlight de match
  - [ ] Responsivo

Criterios de Aceitacao:
  - [ ] Contatos clicáveis
  - [ ] Experiência em ordem cronológica
  - [ ] Skills com match destacadas
  - [ ] Scroll suave no conteúdo
```

---

### CARD PRV-003: Tab Atividades
**Épico:** É11 — Kanban e Tabela de Candidatos

```yaml
Titulo: [FRONTEND] Tab Atividades no Preview
Tipo: Frontend
Area: Frontend
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 5
Prioridade: Media
Epic: EPIC-KAN-001
Status: 📋 Pendente Jira
Dependencias: PRV-001

Descricao: |
  Implementar conteúdo da tab Atividades no preview lateral,
  mostrando timeline de todas as interações com o candidato
  (mensagens, mudanças de etapa, notas, etc).

Historia de Usuario: |
  Como recrutador, eu quero ver o histórico de interações
  com o candidato para entender todo o contexto do processo
  seletivo.

Regras de Negocio:
  1. Timeline cronológica (mais recente primeiro)
  2. Tipos de atividade: mensagem, mudança de etapa, nota, triagem, entrevista
  3. Filtro por tipo de atividade
  4. Autor e timestamp em cada item
  5. Expandir mensagens longas

Requisitos Tecnicos:
  Frontend:
    - ActivitiesTab component
    - ActivityTimeline component
    - ActivityItem component
  Backend:
    - GET /api/backend-proxy/candidates/{id}/activities

Integracoes Externas:
  Nenhuma

Design & Componentes:
  Componentes Existentes:
    - Card - item de atividade
    - Badge - tipo de atividade
    - Avatar - autor
  Novos Componentes:
    - ActivityTimeline - timeline vertical
    - ActivityItem - item individual
    - ActivityFilter - filtro por tipo
  Design Tokens:
    Timeline Line: --lia-border-subtle
    Item Background: --lia-bg-primary
    Type Badge: cores por tipo
    Author: --lia-text-secondary
    Timestamp: --lia-text-tertiary
  Layout:
    Container: padding-4
    Timeline: vertical, left-aligned
    Item: card com icon, conteúdo, metadata
  Estados:
    - Loading (skeleton)
    - Empty ("Nenhuma atividade registrada")
    - Loaded (timeline com items)
    - Filtered (items filtrados)
  Acessibilidade:
    - Timeline com role="list"
    - Items com role="listitem"
    - Timestamps relativos + absolutos

Comportamento de UI:
  Fluxo Principal:
    1. Tab Atividades selecionada
    2. Timeline carrega com atividades recentes primeiro
    3. Cada item mostra:
       - Ícone do tipo (💬📝✅📅)
       - Descrição da atividade
       - Autor (avatar + nome)
       - Timestamp (relativo: "há 2 horas")
    4. Filtro permite ver apenas certos tipos
    5. Click em mensagem expande conteúdo completo
  
  Tipos de Atividade:
    - 💬 Mensagem: conversa WhatsApp
    - 📝 Nota: nota adicionada por recrutador
    - ✅ Etapa: mudança de etapa no pipeline
    - 📅 Entrevista: agendamento/confirmação
    - 🧠 Triagem: triagem WSI completada
    - 📧 Email: email enviado/recebido
  
  Layout da Timeline:

Arquivos de Referencia (Prototipo Replit):
  - candidate-page.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/candidate-page.tsx
  - activity-feed.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/activity-feed.tsx
    ```
    ○ 💬 Mensagem de WhatsApp
      │  "Obrigado pela oportunidade..."
      │  [LIA] há 2 horas
      │
    ○ ✅ Movido para Triagem
      │  [João Silva] há 1 dia
      │
    ○ 📝 Nota adicionada
         "Candidato interessante, priorizar"
         [Maria Santos] há 3 dias
    ```

DoD (Definition of Done):
  - [ ] Timeline renderiza corretamente
  - [ ] Todos os tipos de atividade
  - [ ] Filtro funciona
  - [ ] Expand de mensagens longas
  - [ ] Scroll infinito se muitas atividades

Criterios de Aceitacao:
  - [ ] Atividades em ordem cronológica
  - [ ] Ícones corretos por tipo
  - [ ] Filtro filtra corretamente
  - [ ] Timestamps relativos legíveis
```

---

### CARD PRV-004: Tab Arquivos
**Épico:** É11 — Kanban e Tabela de Candidatos

```yaml
Titulo: [FRONTEND] Tab Arquivos no Preview
Tipo: Frontend
Area: Frontend
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 3
Prioridade: Media
Epic: EPIC-KAN-001
Status: 📋 Pendente Jira
Dependencias: PRV-001

Descricao: |
  Implementar conteúdo da tab Arquivos no preview lateral,
  listando CV e outros documentos anexados ao candidato
  com opções de download e visualização.

Historia de Usuario: |
  Como recrutador, eu quero acessar rapidamente o CV e outros
  documentos do candidato para revisão detalhada.

Regras de Negocio:
  1. Lista de arquivos anexados
  2. Tipos suportados: PDF, DOC, DOCX, imagens
  3. Preview inline para PDFs e imagens
  4. Download de qualquer arquivo
  5. Upload de novos arquivos (por recrutador)
  6. CV destacado no topo

Requisitos Tecnicos:
  Frontend:
    - FilesTab component
    - FileList component
    - FilePreview component
    - FileUpload component
  Backend:
    - GET /api/backend-proxy/candidates/{id}/files
    - POST /api/backend-proxy/candidates/{id}/files

Integracoes Externas:
  Storage (CDN/S3) para arquivos

Design & Componentes:
  Componentes Existentes:
    - Button - download, upload
    - Card - item de arquivo
  Novos Componentes:
    - FileListItem - item com ícone, nome, ações
    - PDFPreview - preview de PDF inline
    - FileUploadZone - zona de upload drag&drop
  Design Tokens:
    Item Background: --lia-bg-secondary
    Item Hover: --lia-interactive-hover
    Icon PDF: --electric-red
    Icon DOC: --wedo-cyan
    Upload Zone: border dashed --lia-border-subtle
  Layout:
    Container: padding-4, space-y-4
    File Item: flex, items-center, gap-3
    Upload Zone: dashed border, h-20
  Estados:
    - Loading (skeleton)
    - Empty ("Nenhum arquivo anexado")
    - Loaded (lista de arquivos)
    - Uploading (progress bar)
  Acessibilidade:
    - Lista de arquivos com role="list"
    - Download buttons com aria-label
    - Drag & drop com keyboard alternative

Comportamento de UI:
  Fluxo Principal:
    1. Tab Arquivos selecionada
    2. Lista de arquivos carrega
    3. CV aparece destacado no topo (se existir)
    4. Cada arquivo mostra:
       - Ícone por tipo (PDF, DOC, IMG)
       - Nome do arquivo
       - Tamanho
       - Data de upload
       - Botões: Preview, Download
    5. Click em Preview abre modal ou inline
    6. Drag & drop ou click para upload de novo arquivo
  
  Layout:

Arquivos de Referencia (Prototipo Replit):
  - candidate-page.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/candidate-page.tsx
  - cv-preview.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/cv/cv-preview.tsx
    ```
    ┌─────────────────────────────────────────┐
    │ 📄 CV_Joao_Silva.pdf  [👁] [⬇]         │
    │    350 KB • Enviado há 3 dias           │
    ├─────────────────────────────────────────┤
    │ 📝 Portfólio.pdf      [👁] [⬇]         │
    │    1.2 MB • Enviado há 3 dias           │
    ├─────────────────────────────────────────┤
    │     + Arraste arquivos ou clique        │
    │       para adicionar                    │
    └─────────────────────────────────────────┘
    ```

DoD (Definition of Done):
  - [ ] Lista de arquivos renderiza
  - [ ] Download funciona
  - [ ] Preview funciona para PDF
  - [ ] Upload funciona
  - [ ] CV destacado

Criterios de Aceitacao:
  - [ ] Arquivos listados corretamente
  - [ ] Download baixa arquivo
  - [ ] Preview abre visualização
  - [ ] Upload aceita drag & drop
  - [ ] Tipos de arquivo com ícones corretos
```

---

### CARD PRV-005: Tab Parecer LIA
**Épico:** É11 — Kanban e Tabela de Candidatos

```yaml
Titulo: [FRONTEND] Tab Parecer LIA no Preview
Tipo: Frontend
Area: Frontend
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 8
Prioridade: Alta
Epic: EPIC-KAN-001
Status: 📋 Pendente Jira
Dependencias: PRV-001, SCO-001

Descricao: |
  Implementar conteúdo da tab Parecer LIA no preview lateral,
  mostrando análise completa da IA incluindo score WSI,
  breakdown por dimensão, parecer textual e recomendação.

Historia de Usuario: |
  Como recrutador, eu quero ver a análise completa da LIA
  sobre o candidato para tomar decisões informadas baseadas
  em dados e insights de IA.

Regras de Negocio:
  1. Score WSI geral em destaque
  2. Breakdown por dimensão (4): Técnico, Comportamental, Cultural, Comunicação
  3. Parecer textual da LIA
  4. Pontos fortes e pontos de atenção
  5. Recomendação final (Recomendado/Avaliar/Não recomendado)
  6. Data da última análise

Requisitos Tecnicos:
  Frontend:
    - LiaOpinionTab component
    - ScoreRadarChart component (radar chart das dimensões)
    - OpinionCard component
    - RecommendationBadge component
  Backend:
    - GET /api/backend-proxy/lia/profile-analysis/candidate/{id}

Integracoes Externas:
  Nenhuma (dados já gerados pelo ÉPICO 6)

Design & Componentes:
  Componentes Existentes:
    - Card - seções
    - Badge - recomendação
    - Progress - barras de dimensão
  Novos Componentes:
    - ScoreGauge - gauge circular do score geral
    - DimensionBars - barras horizontais por dimensão
    - OpinionText - texto formatado do parecer
    - StrengthWeaknessList - lista de pontos fortes/atenção
  Design Tokens:
    Score High: --wedo-green
    Score Medium: --wedo-yellow
    Score Low: --electric-red
    Dimension Labels: --lia-text-secondary
    Opinion Text: --lia-text-primary
    Strength: --wedo-green
    Weakness: --wedo-yellow
  Layout:
    Container: padding-4, space-y-6
    Score Gauge: centered, h-32
    Dimensions: grid ou list
    Opinion: prose text
  Estados:
    - Loading (skeleton)
    - No analysis ("Aguardando triagem")
    - Loaded (análise completa)
  Acessibilidade:
    - Score anunciado para screen readers
    - Barras com labels
    - Parecer legível

Comportamento de UI:
  Fluxo Principal:
    1. Tab Parecer LIA selecionada
    2. Se triagem não concluída: "Aguardando triagem do candidato"
    3. Se triagem concluída:
       - Score geral em gauge grande (ex: 85)
       - Breakdown: Técnico 90 | Comportamental 78 | Cultural 85 | Comunicação 87
       - Parecer textual da LIA
       - Lista de pontos fortes (3-5 items)
       - Lista de pontos de atenção (0-3 items)
       - Badge de recomendação final
  
  Layout:

Arquivos de Referencia (Prototipo Replit):
  - candidate-page.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/candidate-page.tsx
  - candidate_report_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/candidate_report_service.py
  - explainability_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/explainability_service.py
    ```
    ┌─────────────────────────────────────────┐
    │         ┌──────┐                        │
    │         │  85  │  Score WSI             │
    │         └──────┘                        │
    ├─────────────────────────────────────────┤
    │ Técnico        ████████████░░░ 90       │
    │ Comportamental █████████░░░░░░ 78       │
    │ Cultural       ███████████░░░░ 85       │
    │ Comunicação    ███████████░░░░ 87       │
    ├─────────────────────────────────────────┤
    │ Parecer da LIA:                         │
    │ "O candidato demonstra sólida           │
    │ experiência técnica em Python..."       │
    ├─────────────────────────────────────────┤
    │ ✅ Pontos Fortes:                       │
    │ • Experiência relevante                 │
    │ • Comunicação clara                     │
    │ • Fit cultural alto                     │
    ├─────────────────────────────────────────┤
    │ ⚠️ Pontos de Atenção:                   │
    │ • Gaps em liderança                     │
    ├─────────────────────────────────────────┤
    │ [🟢 RECOMENDADO]                        │
    │ Última análise: há 2 horas              │
    └─────────────────────────────────────────┘
    ```

DoD (Definition of Done):
  - [ ] Score gauge renderiza
  - [ ] Breakdown por dimensão
  - [ ] Parecer textual exibido
  - [ ] Pontos fortes e atenção
  - [ ] Badge de recomendação
  - [ ] Estado de aguardando triagem

Criterios de Aceitacao:
  - [ ] Score visível e colorido
  - [ ] 4 dimensões com barras
  - [ ] Parecer completo legível
  - [ ] Listas de pontos formatadas
  - [ ] Recomendação clara
```

---

### CARD VAG-001: Tabela de Vagas
**Épico:** É11 — Kanban e Tabela de Candidatos

```yaml
Titulo: [FRONTEND] Tabela de Vagas
Tipo: Frontend
Area: Frontend
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 8
Prioridade: Alta
Epic: EPIC-KAN-001
Status: 📋 Pendente Jira

Descricao: |
  Implementar tabela principal de listagem de vagas com
  informações resumidas, status, contadores de candidatos
  e ações disponíveis.

Historia de Usuario: |
  Como recrutador, eu quero ver todas as minhas vagas em
  uma tabela organizada para gerenciar múltiplos processos
  seletivos simultaneamente.

Regras de Negocio:
  1. Colunas: Nome, Departamento, Status, Candidatos, Criação, Responsável, Ações
  2. Ordenação por qualquer coluna
  3. Status colorido: Ativa (verde), Pausada (amarelo), Encerrada (cinza)
  4. Contador de candidatos por etapa
  5. Click na row navega para Kanban da vaga
  6. Ações rápidas via menu

Requisitos Tecnicos:
  Frontend:
    - JobsTable component
    - JobRow component
    - StatusBadge component
  Backend:
    - GET /api/backend-proxy/job-vacancies

Integracoes Externas:
  Nenhuma

Design & Componentes:
  Componentes Existentes:
    - Table - shadcn/ui
    - Badge - status
    - Avatar - responsável
  Novos Componentes:
    - JobsTable - tabela de vagas
    - JobStatusBadge - badge colorido de status
    - CandidateCounter - contador mini por etapa
  Design Tokens:
    Active: --wedo-green
    Paused: --wedo-yellow
    Closed: --lia-text-tertiary
    Row Hover: --lia-interactive-hover
  Layout:
    Table: w-full
    Status: badge inline
    Counter: badges mini alinhados
  Estados:
    - Loading (skeleton)
    - Empty ("Nenhuma vaga criada")
    - Loaded (tabela com vagas)
    - Row hover (highlight)
  Acessibilidade:
    - Table com headers
    - Rows clicáveis como links
    - Status anunciado

Comportamento de UI:
  Fluxo Principal:
    1. Página de Vagas carrega
    2. Tabela mostra todas as vagas
    3. Cada row: Nome | Dept | Status | Candidatos | Data | Owner | ...
    4. Hover destaca row
    5. Click na row → navega para Kanban dessa vaga
    6. Menu de ações (3 dots) oferece ações rápidas
  
  Colunas:
    | Vaga | Departamento | Status | Candidatos | Criada em | Responsável | ... |
  
  Candidatos Counter:
    "12 total (5 funil, 4 triagem, 3 entrevista)"
    Ou badges: [5] [4] [3] coloridos por etapa

DoD (Definition of Done):
  - [ ] Tabela renderiza vagas
  - [ ] Ordenação funciona
  - [ ] Status com cores
  - [ ] Contadores corretos
  - [ ] Click navega para vaga
  - [ ] Responsivo


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

Criterios de Aceitacao:
  - [ ] Todas as vagas listadas
  - [ ] Colunas ordenáveis
  - [ ] Status visual claro
  - [ ] Navegação funciona

Arquivos de Referencia (Prototipo Replit):
  - types.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/jobs/types.ts
  - useJobColumnConfig.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/useJobColumnConfig.ts
  - useJobFiltersPersistence.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/useJobFiltersPersistence.ts
```

---

### CARD VAG-002: Tabs de Status
**Épico:** É11 — Kanban e Tabela de Candidatos

```yaml
Titulo: [FRONTEND] Tabs de Status das Vagas
Tipo: Frontend
Area: Frontend
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 3
Prioridade: Media
Epic: EPIC-KAN-001
Status: 📋 Pendente Jira
Dependencias: VAG-001

Descricao: |
  Implementar tabs acima da tabela de vagas para filtrar
  por status: Todas, Ativas, Pausadas, Encerradas.

Historia de Usuario: |
  Como recrutador, eu quero filtrar vagas por status para
  focar nas que estão ativas ou revisar as encerradas.

Regras de Negocio:
  1. Tabs: Todas | Ativas | Pausadas | Encerradas
  2. Contador em cada tab
  3. Default: Ativas
  4. Persist seleção na URL

Requisitos Tecnicos:
  Frontend:
    - JobStatusTabs component
    - Tab counter badges
  Backend:
    - GET /api/backend-proxy/job-vacancies?status=active

Integracoes Externas:
  Nenhuma

Design & Componentes:
  Componentes Existentes:
    - Tabs - shadcn/ui
    - Badge - contador
  Novos Componentes:
    - JobStatusTabs - tabs com contadores
  Design Tokens:
    Tab Active: border-b --wedo-cyan
    Tab Inactive: --lia-text-secondary
    Counter: bg-lia-bg-tertiary
  Layout:
    Tabs: flex, border-b, sticky top
    Counter: badge pequeno ao lado do nome
  Estados:
    - All selected
    - Active selected (default)
    - Paused selected
    - Closed selected
  Acessibilidade:
    - role="tablist"
    - aria-selected

Comportamento de UI:
  Fluxo Principal:
    1. Tabs acima da tabela
    2. Default: "Ativas" selecionada
    3. Contadores: Todas (15) | Ativas (8) | Pausadas (2) | Encerradas (5)
    4. Click em tab filtra tabela
    5. URL atualiza: /vagas?status=paused

DoD (Definition of Done):
  - [ ] Tabs renderizam
  - [ ] Contadores corretos
  - [ ] Filtro funciona
  - [ ] URL reflete tab


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

Criterios de Aceitacao:
  - [ ] Todas as tabs funcionam
  - [ ] Contadores atualizados
  - [ ] Default é Ativas
  - [ ] URL persiste seleção

Arquivos de Referencia (Prototipo Replit):
  - types.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/jobs/types.ts
  - useJobFiltersPersistence.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/useJobFiltersPersistence.ts
```

---

### CARD VAG-003: Menu de Ações da Vaga
**Épico:** É11 — Kanban e Tabela de Candidatos

```yaml
Titulo: [FRONTEND] Menu de Ações da Vaga
Tipo: Frontend
Area: Frontend
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 3
Prioridade: Media
Epic: EPIC-KAN-001
Status: 📋 Pendente Jira
Dependencias: VAG-001

Descricao: |
  Implementar menu de ações contextuais para cada vaga na
  tabela, acessível via ícone de 3 pontos.

Historia de Usuario: |
  Como recrutador, eu quero acessar ações rápidas da vaga
  diretamente da tabela sem precisar abrir a página da vaga.

Regras de Negocio:
  1. Menu com ações: Editar, Pausar/Ativar, Duplicar, Arquivar
  2. Ações variam por status da vaga
  3. Ações destrutivas com confirmação
  4. Atalhos de teclado para power users

Requisitos Tecnicos:
  Frontend:
    - JobActionsMenu component
    - DropdownMenu (shadcn/ui)
  Backend:
    - Reutiliza endpoints existentes

Integracoes Externas:
  Nenhuma

Design & Componentes:
  Componentes Existentes:
    - DropdownMenu - shadcn/ui
    - DropdownMenuItem
  Novos Componentes:
    - JobActionsMenu - menu contextual da vaga
  Design Tokens:
    Trigger: --lia-text-tertiary
    Menu: --lia-bg-primary
    Destructive: --electric-red
  Layout:
    Trigger: 24x24px no final da row
    Menu: min-w-[160px]
  Estados:
    - Closed
    - Open
    - Item hover
  Acessibilidade:
    - role="menu"
    - Keyboard navigation

Comportamento de UI:
  Fluxo Principal:
    1. Hover na row revela ícone de 3 pontos
    2. Click abre menu dropdown
    3. Ações disponíveis por status:
       - Ativa: Editar, Pausar, Duplicar
       - Pausada: Editar, Ativar, Duplicar, Arquivar
       - Encerrada: Ver, Duplicar
    4. Click em ação executa ou abre modal
  
  Ações:
    - 📝 Editar: abre página de edição
    - ⏸️ Pausar: pausa a vaga (confirmação)
    - ▶️ Ativar: reativa vaga pausada
    - 📋 Duplicar: cria cópia da vaga
    - 📦 Arquivar: arquiva vaga (confirmação)

DoD (Definition of Done):
  - [ ] Menu abre e fecha
  - [ ] Ações variam por status
  - [ ] Ações executam corretamente
  - [ ] Acessível por teclado


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

Criterios de Aceitacao:
  - [ ] Ícone aparece no hover
  - [ ] Menu lista ações corretas
  - [ ] Ações funcionam
  - [ ] Confirmação para destrutivas

Arquivos de Referencia (Prototipo Replit):
  - edit-job-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/modals/edit-job-modal.tsx
  - job-status-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/modals/job-status-modal.tsx
  - job-duplicate-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/modals/job-duplicate-modal.tsx
```

---

### CARD VAG-004: Pausar/Ativar Vaga
**Épico:** É11 — Kanban e Tabela de Candidatos

```yaml
Titulo: [FULL-STACK] Pausar/Ativar Vaga
Tipo: Full-Stack
Area: Full-Stack
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 5
Prioridade: Media
Epic: EPIC-KAN-001
Status: 📋 Pendente Jira
Dependencias: VAG-003

Descricao: |
  Implementar funcionalidade de pausar e reativar vagas.
  Vagas pausadas não recebem novos candidatos e LIA para
  de fazer contato ativo.

Historia de Usuario: |
  Como recrutador, eu quero pausar uma vaga temporariamente
  quando preciso focar em outras prioridades, sem perder
  os candidatos já em processo.

Regras de Negocio:
  1. Pausar: vaga fica inativa, LIA para de contatar novos candidatos
  2. Candidatos em processo continuam onde estão
  3. Ativar: vaga volta ao normal
  4. Histórico de pausas mantido
  5. Notificação opcional ao pausar

Requisitos Tecnicos:
  Backend:
    - PUT /api/backend-proxy/job-vacancies/{id}/pause
    - PUT /api/backend-proxy/job-vacancies/{id}/activate
  Frontend:
    - Confirmação modal
    - Status update
  Dados:
    - job_vacancies.status = 'active' | 'paused' | 'closed'
    - job_status_history: id, job_id, old_status, new_status, changed_by, changed_at

Integracoes Externas:
  Nenhuma

Design & Componentes:
  Componentes Existentes:
    - Dialog - confirmação
    - Button - ações
  Novos Componentes:
    - PauseJobDialog - dialog de confirmação com opções
  Design Tokens:
    Pause: --wedo-yellow
    Activate: --wedo-green
  Layout:
    Dialog: max-w-sm
    Options: checkbox de notificar, textarea de motivo
  Estados:
    - Active (pode pausar)
    - Paused (pode ativar)
    - Processing (loading)
  Acessibilidade:
    - Focus no dialog
    - Escape para cancelar

Comportamento de UI:
  Fluxo Pausar:
    1. Click em "Pausar vaga" no menu
    2. Dialog: "Pausar vaga [Nome]?"
       - Checkbox: "Notificar candidatos em processo"
       - Textarea: "Motivo (opcional)"
    3. Confirmar
    4. Status muda para "Pausada"
    5. Toast: "Vaga pausada"
  
  Fluxo Ativar:
    1. Click em "Ativar vaga" no menu
    2. Ativação direta (sem confirmação)
    3. Status muda para "Ativa"
    4. Toast: "Vaga reativada"

DoD (Definition of Done):
  - [ ] Pausar funciona
  - [ ] Ativar funciona
  - [ ] Status atualiza
  - [ ] Histórico salvo
  - [ ] LIA respeita status


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

Criterios de Aceitacao:
  - [ ] Vaga pausada não recebe novos contatos
  - [ ] Reativar restaura funcionamento normal
  - [ ] UI reflete status
  - [ ] Histórico rastreável

Arquivos de Referencia (Prototipo Replit):
  - job-status-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/modals/job-status-modal.tsx
  - job_vacancy_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/job_vacancy_service.py
```

---

### CARD VAG-005: Duplicar Vaga
**Épico:** É11 — Kanban e Tabela de Candidatos

```yaml
Titulo: [FULL-STACK] Duplicar Vaga
Tipo: Full-Stack
Area: Full-Stack
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 5
Prioridade: Media
Epic: EPIC-KAN-001
Status: 📋 Pendente Jira
Dependencias: VAG-003

Descricao: |
  Implementar funcionalidade de duplicar uma vaga existente,
  copiando todas as configurações mas criando uma nova vaga
  sem candidatos.

Historia de Usuario: |
  Como recrutador, eu quero duplicar uma vaga existente para
  criar rapidamente vagas similares sem precisar preencher
  tudo do zero.

Regras de Negocio:
  1. Copiar todos os campos da vaga original
  2. Nova vaga criada como rascunho
  3. Não copiar candidatos
  4. Sufixo "(Cópia)" no título
  5. Abrir em modo edição após duplicar

Requisitos Tecnicos:
  Backend:
    - POST /api/backend-proxy/job-vacancies/{id}/duplicate
  Frontend:
    - Confirmação simples
    - Redirect para edição
  Dados:
    - Nova entry em job_vacancies com duplicated_from_id

Integracoes Externas:
  Nenhuma

Design & Componentes:
  Componentes Existentes:
    - Dialog - confirmação
    - Button
  Design Tokens:
    Primary: --wedo-cyan
  Layout:
    Dialog: simples com mensagem e botões
  Estados:
    - Idle
    - Duplicating (loading)
    - Done (redirect)
  Acessibilidade:
    - Focus management

Comportamento de UI:
  Fluxo:
    1. Click em "Duplicar" no menu
    2. Dialog: "Duplicar vaga [Nome]? Uma cópia será criada como rascunho."
    3. Confirmar
    4. Loading
    5. Redirect para página de edição da nova vaga
    6. Toast: "Vaga duplicada. Edite e publique quando pronta."

DoD (Definition of Done):
  - [ ] Duplicação funciona
  - [ ] Todos os campos copiados
  - [ ] Candidatos não copiados
  - [ ] Redirect para edição
  - [ ] Novo ID gerado


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

Criterios de Aceitacao:
  - [ ] Nova vaga criada como rascunho
  - [ ] "(Cópia)" no título
  - [ ] Página de edição abre
  - [ ] Original inalterada

Arquivos de Referencia (Prototipo Replit):
  - job-duplicate-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/modals/job-duplicate-modal.tsx
  - job_clone_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/job_clone_service.py
```

---

### CARD VAG-006: Arquivar Vaga
**Épico:** É11 — Kanban e Tabela de Candidatos

```yaml
Titulo: [FULL-STACK] Arquivar Vaga
Tipo: Full-Stack
Area: Full-Stack
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 3
Prioridade: Baixa
Epic: EPIC-KAN-001
Status: 📋 Pendente Jira
Dependencias: VAG-003

Descricao: |
  Implementar funcionalidade de arquivar vagas encerradas
  para limpar a visualização principal mantendo histórico.

Historia de Usuario: |
  Como recrutador, eu quero arquivar vagas antigas para
  manter minha lista organizada mas ainda poder acessar
  o histórico quando necessário.

Regras de Negocio:
  1. Apenas vagas encerradas ou pausadas podem ser arquivadas
  2. Vagas arquivadas não aparecem na lista principal
  3. Aba "Arquivadas" mostra vagas arquivadas
  4. Pode desarquivar a qualquer momento
  5. Candidatos mantidos (histórico)

Requisitos Tecnicos:
  Backend:
    - PUT /api/backend-proxy/job-vacancies/{id}/archive
    - PUT /api/backend-proxy/job-vacancies/{id}/unarchive
    - Query: ?archived=true
  Frontend:
    - Aba "Arquivadas" nas tabs
    - Confirmação para arquivar
  Dados:
    - job_vacancies.archived_at

Integracoes Externas:
  Nenhuma

Design & Componentes:
  Componentes Existentes:
    - Dialog - confirmação
    - Tabs - adicionar aba Arquivadas
  Design Tokens:
    Archived: --lia-text-tertiary
  Layout:
    Dialog: simples
    Tab: adicionada ao final
  Estados:
    - Active (pode arquivar)
    - Archived (pode desarquivar)
  Acessibilidade:
    - Ações claras

Comportamento de UI:
  Fluxo Arquivar:
    1. Click em "Arquivar" no menu
    2. Dialog: "Arquivar vaga [Nome]?"
    3. Confirmar → Vaga some da lista principal
    4. Aparece na tab "Arquivadas"
  
  Fluxo Desarquivar:
    1. Na tab "Arquivadas", menu "Desarquivar"
    2. Vaga volta para lista principal (status que tinha)

DoD (Definition of Done):
  - [ ] Arquivar funciona
  - [ ] Desarquivar funciona
  - [ ] Tab Arquivadas existe
  - [ ] Vagas não aparecem na lista principal


Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"

Criterios de Aceitacao:
  - [ ] Vaga arquivada some da lista
  - [ ] Tab Arquivadas mostra vagas
  - [ ] Pode desarquivar
  - [ ] Histórico mantido

Arquivos de Referencia (Prototipo Replit):
  - job-status-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/modals/job-status-modal.tsx
  - job_vacancy_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/job_vacancy_service.py
```

---

### CARD VAG-007: Contador de Candidatos por Etapa
**Épico:** É11 — Kanban e Tabela de Candidatos

```yaml
Titulo: [FRONTEND] Contador de Candidatos por Etapa
Tipo: Frontend
Area: Frontend
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 3
Prioridade: Alta
Epic: EPIC-KAN-001
Status: 📋 Pendente Jira
Dependencias: VAG-001

Descricao: |
  Implementar visualização do contador de candidatos por
  etapa na tabela de vagas, mostrando quantos estão em
  cada coluna do pipeline.

Historia de Usuario: |
  Como recrutador, eu quero ver rapidamente quantos candidatos
  estão em cada etapa de cada vaga para priorizar meu trabalho.

Regras de Negocio:
  1. Mostrar contadores por etapa: Funil | Triagem | Entrevista
  2. Total de candidatos
  3. Cores por etapa
  4. Click expande para detalhes

Requisitos Tecnicos:
  Frontend:
    - StageCounterBadges component
  Backend:
    - (dados já vêm no GET /job-vacancies com candidate_counts)
  Dados:
    - job_vacancy.candidate_counts: { funnel: 5, screening: 4, interview: 3 }

Integracoes Externas:
  Nenhuma

Design & Componentes:
  Componentes Existentes:
    - Badge - contadores
  Novos Componentes:
    - StageCounterBadges - row de badges por etapa
  Design Tokens:
    Funnel: --wedo-cyan-light
    Screening: --wedo-yellow-light
    Interview: --wedo-green-light
    Total: --lia-bg-tertiary
  Layout:
    Badges: flex, gap-1
    Each: rounded, padding-x-2
  Estados:
    - Zero (hidden ou "0")
    - Populated (número visível)
  Acessibilidade:
    - Tooltip com nome da etapa
    - aria-label "X candidatos em Y"

Comportamento de UI:
  Visual:

Arquivos de Referencia (Prototipo Replit):
  - page.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/jobs/[id]/page.tsx
  - recruitment-stages.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/recruitment-stages.ts
  - pipeline_stage_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/pipeline_stage_service.py
    ```
    [5 🔵] [4 🟡] [3 🟢]  12 total
    ```
    Ou: "5 funil, 4 triagem, 3 entrevista"
  
  Hover: tooltip mostra etapa

DoD (Definition of Done):
  - [ ] Badges renderizam
  - [ ] Cores corretas
  - [ ] Números corretos
  - [ ] Tooltip funciona

Criterios de Aceitacao:
  - [ ] Contadores visíveis
  - [ ] Cores por etapa
  - [ ] Total calculado
  - [ ] Hover mostra detalhes
```

---

### CARD VAG-008: Navegação Vaga → Kanban
**Épico:** É11 — Kanban e Tabela de Candidatos

```yaml
Titulo: [FRONTEND] Navegação Vaga → Kanban
Tipo: Frontend
Area: Frontend
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 3
Prioridade: Alta
Epic: EPIC-KAN-001
Status: 📋 Pendente Jira
Dependencias: VAG-001, KAN-001

Descricao: |
  Implementar navegação da lista de vagas para a visualização
  Kanban de candidatos daquela vaga específica.

Historia de Usuario: |
  Como recrutador, eu quero clicar em uma vaga e ir direto
  para o Kanban de candidatos daquela vaga.

Regras de Negocio:
  1. Click na row da vaga navega para Kanban
  2. URL: /vagas/{id}/candidatos
  3. Breadcrumb mostra contexto
  4. Botão de voltar para lista de vagas

Requisitos Tecnicos:
  Frontend:
    - Routing configuration
    - Breadcrumb component
    - Back navigation
  Backend:
    - N/A (navegação client-side)

Integracoes Externas:
  Nenhuma

Design & Componentes:
  Componentes Existentes:
    - Link - navegação
    - Breadcrumb - shadcn/ui
  Design Tokens:
    Link: --wedo-cyan
    Breadcrumb: --lia-text-tertiary
  Layout:
    Row: cursor-pointer
    Breadcrumb: top of Kanban page
  Estados:
    - Navigating (loading)
    - Loaded (Kanban view)
  Acessibilidade:
    - Row como link
    - Breadcrumb como nav

Comportamento de UI:
  Fluxo:
    1. Na lista de vagas, click em uma row
    2. Navegação para /vagas/123/candidatos
    3. Kanban carrega com candidatos dessa vaga
    4. Breadcrumb: Vagas > [Nome da Vaga] > Candidatos
    5. Click em "Vagas" volta para lista
  
  Breadcrumb:

Arquivos de Referencia (Prototipo Replit):
  - page.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/jobs/[id]/page.tsx
  - types.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/jobs/types.ts
    ```
    Vagas > Desenvolvedor Frontend > Candidatos (Kanban)
    ```

DoD (Definition of Done):
  - [ ] Click navega para Kanban
  - [ ] URL correta
  - [ ] Breadcrumb funciona
  - [ ] Voltar funciona

Criterios de Aceitacao:
  - [ ] Navegação funciona
  - [ ] Kanban mostra candidatos da vaga
  - [ ] Breadcrumb contextual
  - [ ] Back button funciona
```

---

## RESUMO DE PONTOS

### Épico 9 - Agendamento Automático
| Card | Pontos |
|------|--------|
| AGE-001 | 13 |
| 📋 Pendente | 8 |
| AGE-003 | 8 |
| AGE-004 | 8 |
| 📋 Pendente | 8 |
| AGE-006 | 8 |
| AGE-007 | 5 |
| AGE-008 | 5 |
| **Total** | **63** |

### Épico 10 - Notificações
| Card | Pontos |
|------|--------|
| NOT-001 | 8 |
| 📋 Pendente | 8 |
| NOT-003 | 5 |
| NOT-004 | 8 |
| NOT-005 | 5 |
| NOT-006 | 3 |
| 📋 Pendente | **37** |

### Épico 11 - Kanban e Tabela de Candidatos
| Card | Pontos |
|------|--------|
| KAN-001 | 8 |
| KAN-002 | 5 |
| KAN-003 | 8 |
| KAN-004 | 5 |
| KAN-005 | 3 |
| 📋 | 5 |
| KAN-007 | 5 |
| KAN-008 | 3 |
| TAB-001 | 8 |
| TAB-002 | 3 |
| TAB-003 | 3 |
| 📋 Pendente | 5 |
| TAB-005 | 8 |
| 📋 Pendente | 8 |
| PRV-002 | 5 |
| PRV-003 | 5 |
| PRV-004 | 3 |
| PRV-005 | 8 |
| VAG-001 | 8 |
| VAG-002 | 3 |
| VAG-003 | 3 |
| VAG-004 | 5 |
| VAG-005 | 5 |
| 📋 Pendente | 3 |
| VAG-007 | 3 |
| VAG-008 | 3 |
| **Total** | **130** |

---

## TOTAL GERAL

| Épico | Cards | Pontos |
|-------|-------|--------|
| Épico 9 - Agendamento | 8 | 63 |
| Épico 10 - Notificações | 6 | 37 |
| Épico 11 - Kanban/Tabela | 26 | 130 |
| **TOTAL** | **40** | **230** |

---
## ÉPICO 12: JOB DESCRIPTION E WIZARD AVANÇADO

> **Novos cards** identificados na análise de implementação (Fevereiro 2026)

---

### CARD JD-001: Preview de Job Description com Sugestões LIA
**Épico:** É12 — JD e Wizard Avançado

```yaml
Titulo: [FRONTEND] Preview de JD com Sugestões LIA
Tipo: Frontend
Area: Frontend
Sprint: Pós-MVP
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 5
Prioridade: Alta
Epic: EPIC-JD-WIZARD
Status: 📦 Backlog (Pós-MVP)
Dependencias: WIZ-004

Descricao: |
  Componente de preview de Job Description (v1) que exibe o rascunho
  da vaga com indicadores visuais de sugestões LIA (💡) e alertas (⚠️).
  Usado para validação antes da publicação.

Historia de Usuario: |
  Como recrutador, eu quero visualizar um preview da descrição da vaga
  com as sugestões da LIA destacadas para revisar antes de publicar.

Regras de Negocio:
  1. Exibir todas as seções da JD em formato preview
  2. Destacar sugestões LIA com ícone 💡
  3. Mostrar alertas de campos incompletos com ⚠️
  4. Indicador de completude no topo
  5. NÃO incluir seção "Processo Seletivo" (apenas na versão final)

Requisitos Tecnicos:
  Frontend:
    - JobDescriptionPreview.tsx component
    - Integração com JobDraft state
    - Renderização de seções condicionais
  Backend:
    - JDTemplateService.generate_preview()
  Dados:
    - JobDescriptionPreview schema

Integracoes Externas:
  Nenhuma

Design & Componentes:
  Componentes:
    - JobDescriptionPreview - container principal
    - SuggestionBadge - indicador de sugestão
    - AlertBadge - indicador de alerta
    - CompletenessIndicator - barra de progresso
  Design Tokens:
    Suggestion: --wedo-cyan (💡)
    Alert: --electric-yellow (⚠️)
    Complete: --wedo-green
  Acessibilidade:
    - ARIA-labels em badges
    - Contraste adequado para indicadores
    - Screen reader friendly

Comportamento de UI:
  Seções Exibidas:
    - Sobre a Empresa
    - A Vaga
    - O Que Você Vai Fazer
    - O Que Buscamos
    - Requisitos Obrigatórios
    - Diferenciais
    - Por Que Trabalhar Conosco
    - Remuneração
    - Nossos Valores

Referencias de Design:
  Design System: "Design System LIA v4.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"

DoD:
  - [ ] Preview renderiza corretamente
  - [ ] Sugestões destacadas
  - [ ] Alertas visíveis
  - [ ] Completude calculada

Criterios de Aceitacao:
  - [ ] Todas as seções exibidas
  - [ ] Sugestões com ícone 💡
  - [ ] Alertas com ícone ⚠️
  - [ ] Barra de completude funcional

Arquivos de Referencia (Prototipo Replit):
  - EnrichedJDStage.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/expanded-chat/stages/EnrichedJDStage.tsx
  - ReviewPublishStage.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/job-wizard/stages/ReviewPublishStage.tsx
  - types.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/job-description/types.ts
  - jd_enrichment_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/jd_enrichment_service.py
  - jd_generator_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/jd_generator_service.py
```

---

### CARD JD-002: Job Description Final para Publicação
**Épico:** É12 — JD e Wizard Avançado

```yaml
Titulo: [FRONTEND] JD Completo para Publicação
Tipo: Frontend
Area: Frontend
Sprint: Pós-MVP
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 5
Prioridade: Alta
Epic: EPIC-JD-WIZARD
Status: 📦 Backlog (Pós-MVP)
Dependencias: JD-001

Descricao: |
  Componente de Job Description final (v2) com todas as informações
  consolidadas, incluindo Processo Seletivo e link de aplicação.
  Versão para publicação em job boards.

Historia de Usuario: |
  Como recrutador, eu quero gerar a versão final da descrição da vaga
  para publicar em job boards e redes sociais.

Regras de Negocio:
  1. Incluir TODAS as seções do preview
  2. Adicionar seção "Processo Seletivo" com timeline
  3. Incluir "Apply At" link
  4. Seção de Diversidade e Inclusão
  5. Formato otimizado para copy/paste

Requisitos Tecnicos:
  Frontend:
    - JobDescriptionFinal.tsx component
    - Timeline de processo seletivo
    - Ações de publicação
  Backend:
    - JDTemplateService.generate_final()
  Dados:
    - JobDescriptionFinal schema
    - InterviewStage list

Integracoes Externas:
  Job Boards:
    - LinkedIn Jobs
    - Indeed

Design & Componentes:
  Componentes:
    - JobDescriptionFinal - container principal
    - InterviewTimeline - processo seletivo visual
    - PublishActions - botões de ação
  Design Tokens:
    Primary: --wedo-cyan
    Timeline: steps visuais
  Acessibilidade:
    - Timeline com ARIA-labels
    - Links acessíveis

Comportamento de UI:
  Seções Adicionais (v2):
    - Processo Seletivo (timeline)
    - Diversidade e Inclusão
    - Link de Candidatura

  Ações:
    - Copiar para clipboard
    - Publicar no LinkedIn
    - Publicar no Indeed
    - Download PDF

Referencias de Design:
  Figma: "[A ser preenchido pelo time de Design]"

DoD:
  - [ ] JD final completo
  - [ ] Timeline de processo seletivo
  - [ ] Ações de publicação
  - [ ] Formato exportável

Criterios de Aceitacao:
  - [ ] Processo Seletivo visível
  - [ ] Link de candidatura funcional
  - [ ] Copy to clipboard funciona
  - [ ] Formato adequado para job boards

Arquivos de Referencia (Prototipo Replit):
  - ReviewPublishStage.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/job-wizard/stages/ReviewPublishStage.tsx
  - job-publish-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/modals/job-publish-modal.tsx
  - jd_generator_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/jd_generator_service.py
  - job_board_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/job_board_service.py
```

---

### CARD JDW-001: Interação com Sugestões LIA via Chat
**Épico:** É12 — JD e Wizard Avançado

```yaml
Titulo: [BACKEND] Sistema de Interação com Sugestões
Tipo: Backend
Area: Backend
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 8
Prioridade: Alta
Epic: EPIC-JD-WIZARD
Status: 📋 Pendente Jira
Dependencias: WIZ-002

Descricao: |
  Serviço que permite recrutadores interagir com sugestões da LIA
  via linguagem natural no chat. Suporta aceitar, rejeitar, substituir,
  ajustar nível e pedir esclarecimentos.

Historia de Usuario: |
  Como recrutador, eu quero responder às sugestões da LIA usando
  linguagem natural para aceitar, rejeitar ou modificar sugestões.

Regras de Negocio:
  1. Detectar intenção do usuário via regex
  2. Suportar múltiplas palavras em skills
  3. Gerar confirmações em português
  4. Atualizar estado do JobDraft

Requisitos Tecnicos:
  Backend:
    - SuggestionInteractionService
    - Regex-based intent detection
    - Multi-word skill support
  Schemas:
    - SuggestionInteractionType enum
    - SuggestionInteractionRequest
    - SuggestionInteractionResponse

Integracoes Externas:
  Nenhuma

Design & Componentes:
  N/A - Backend only

Comportamento de API:
  Comandos Suportados:
    Aceitar:
      - "pode adicionar Docker"
      - "aceito Machine Learning"
    Rejeitar:
      - "não preciso de Kubernetes"
      - "remova SQL"
    Substituir:
      - "troque Docker por Podman"
      - "prefiro Vue ao invés de React"
    Ajustar nível:
      - "Docker como diferencial"
      - "Python é obrigatório"
    Esclarecer:
      - "por que você sugeriu Machine Learning?"

DoD:
  - [ ] Intent detection funciona
  - [ ] Multi-word skills suportados
  - [ ] Confirmações em português
  - [ ] Estado atualizado

Criterios de Aceitacao:
  - [ ] 5 tipos de interação suportados
  - [ ] Regex patterns funcionam
  - [ ] Respostas contextuais

Arquivos de Referencia (Prototipo Replit):
  - EnrichedJDStage.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/expanded-chat/stages/EnrichedJDStage.tsx
  - use-wizard-suggestions.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/use-wizard-suggestions.ts
  - use-lia-suggestions.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/use-lia-suggestions.ts
  - jd_enrichment_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/jd_enrichment_service.py
  - job_wizard_tools.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/tools/job_wizard_tools.py
```

---

### CARD JDW-002: Análise de Compensação de Mercado
**Épico:** É12 — JD e Wizard Avançado

```yaml
Titulo: [BACKEND] Serviço de Análise de Compensação
Tipo: Backend
Area: Backend
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 5
Prioridade: Media
Epic: EPIC-JD-WIZARD
Status: 📋 Pendente Jira
Dependencias: WIZ-003

Descricao: |
  Serviço que analisa dados de mercado para sugerir faixas salariais
  adequadas com base em cargo, senioridade, localização e stack.

Historia de Usuario: |
  Como recrutador, eu quero receber sugestões de faixa salarial
  baseadas em dados de mercado para criar vagas competitivas.

Regras de Negocio:
  1. Considerar cargo e senioridade
  2. Ajustar por localização (capital vs interior)
  3. Considerar stack tecnológico
  4. Fornecer range (min-max)
  5. Indicar percentil de mercado

Requisitos Tecnicos:
  Backend:
    - CompensationAnalysisService
    - Market data integration
    - Salary estimation algorithms

Integracoes Externas:
  Dados de Mercado:
    - Base interna de salários
    - (Futuro: Glassdoor, Levels.fyi)

DoD:
  - [ ] Estimativa de salário funciona
  - [ ] Ajustes por localização
  - [ ] Range min-max calculado

Criterios de Aceitacao:
  - [ ] Sugestões realistas
  - [ ] Considera senioridade
  - [ ] Indica percentil

Arquivos de Referencia (Prototipo Replit):
  - compensation_analysis_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/compensation_analysis_service.py
  - market_benchmark_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/market_benchmark_service.py
  - SalaryStage.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/expanded-chat/stages/SalaryStage.tsx
```

---

### CARD JDW-003: Insights de Mercado para Vagas
**Épico:** É12 — JD e Wizard Avançado

```yaml
Titulo: [BACKEND] Serviço de Insights de Mercado
Tipo: Backend
Area: Backend
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 8
Prioridade: Alta
Epic: EPIC-JD-WIZARD
Status: 📋 Pendente Jira
Dependencias: WIZ-003

Descricao: |
  Serviço que fornece insights data-driven sobre o mercado de trabalho
  para auxiliar na criação de vagas, incluindo time-to-fill prediction,
  success profile insights e tendências de skills.

Historia de Usuario: |
  Como recrutador, eu quero receber insights sobre o mercado para
  tomar decisões informadas na criação de vagas.

Regras de Negocio:
  1. Predição de time-to-fill baseada em histórico
  2. Sugestões de skills em alta demanda
  3. Alertas de requisitos muito restritivos
  4. Comparação com vagas similares

Requisitos Tecnicos:
  Backend:
    - JobInsightsService
    - Pattern detection
    - Historical data analysis

DoD:
  - [ ] Insights gerados
  - [ ] Predições funcionam
  - [ ] Alertas de requisitos

Criterios de Aceitacao:
  - [ ] Time-to-fill estimado
  - [ ] Skills sugeridos
  - [ ] Alertas contextuais

Arquivos de Referencia (Prototipo Replit):
  - job_insights_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/job_insights_service.py
  - market_benchmark_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/market_benchmark_service.py
  - intelligence_layer_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/intelligence_layer_service.py
  - job-insights-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/modals/job-insights-modal.tsx
```

---

## ÉPICO 13: CONFIGURAÇÕES AVANÇADAS

> **Cards de configuração** identificados na análise (Fevereiro 2026)

---

### CARD CFG-001: LIA Field Toggles
**Épico:** É13 — Configurações Avançadas

```yaml
Titulo: [FRONTEND] Configurar Campos Consumidos por LIA
Tipo: Frontend
Area: Frontend
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 5
Prioridade: Media
Epic: EPIC-CONFIG
Status: 📋 Pendente Jira

Descricao: |
  Sistema de toggles que permite recrutadores configurar quais campos
  de dados da empresa os agentes LIA podem consumir para gerar
  conteúdo e sugestões.

Historia de Usuario: |
  Como admin, eu quero controlar quais dados da empresa a LIA pode
  usar para garantir que informações sensíveis não sejam incluídas
  automaticamente nas comunicações.

Regras de Negocio:
  1. Toggle on/off por campo
  2. Agrupamento por categoria
  3. Preview do impacto
  4. Salvamento automático

Requisitos Tecnicos:
  Frontend:
    - LiaFieldToggle.tsx component
    - Field grouping logic
    - Persistence via API

Design & Componentes:
  Componentes:
    - LiaFieldToggle
    - FieldGroup
    - ImpactPreview
  Design Tokens:
    Toggle On: --wedo-cyan
    Toggle Off: --gray-300

DoD:
  - [ ] Toggles funcionam
  - [ ] Salvamento persiste
  - [ ] Preview funciona

Criterios de Aceitacao:
  - [ ] Campos agrupados
  - [ ] Toggle salva automaticamente
  - [ ] LIA respeita configuração

Arquivos de Referencia (Prototipo Replit):
  - lia_field_config_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/lia_field_config_service.py
  - feature_flag_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/feature_flag_service.py
  - WizardSidebar.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/expanded-chat/components/WizardSidebar.tsx
```

> ⚠️ **DISCLAIMER: CARD RELACIONADO AO MENU DE CONFIGURAÇÕES**
> Este card faz parte do sistema de configurações da plataforma (Settings Menu).
> Consulte também: `docs/configuracoes-admin-cards-jira.md` para cards administrativos complementares.


---

### CARD CFG-002: Verificação de Completude de Configuração
**Épico:** É13 — Configurações Avançadas

```yaml
Titulo: [BACKEND] Serviço de Completude de Configuração
Tipo: Backend
Area: Backend
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 5
Prioridade: Media
Epic: EPIC-CONFIG
Status: 📋 Pendente Jira

Descricao: |
  Serviço que verifica a completude das configurações da empresa
  e fornece sugestões híbridas para campos não preenchidos.

Historia de Usuario: |
  Como admin, eu quero ver quais configurações estão incompletas
  e receber sugestões para preenchê-las.

Requisitos Tecnicos:
  Backend:
    - ConfigCompletenessService
    - Hybrid suggestion generation
    - Final review panel data

DoD:
  - [ ] Verificação funciona
  - [ ] Sugestões geradas
  - [ ] Percentual calculado

Criterios de Aceitacao:
  - [ ] Campos incompletos listados
  - [ ] Sugestões úteis
  - [ ] Barra de progresso

Arquivos de Referencia (Prototipo Replit):
  - config_completeness_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/config_completeness_service.py
  - company_configuration_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/company_configuration_service.py
```

> ⚠️ **DISCLAIMER: CARD RELACIONADO AO MENU DE CONFIGURAÇÕES**
> Este card faz parte do sistema de configurações da plataforma (Settings Menu).
> Consulte também: `docs/configuracoes-admin-cards-jira.md` para cards administrativos complementares.


---

### CARD CFG-003: Configuração de Jornada de Recrutamento
**Épico:** É13 — Configurações Avançadas

```yaml
Titulo: [FRONTEND] Editor de Jornada de Recrutamento
Tipo: Frontend
Area: Frontend
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 8
Prioridade: Alta
Epic: EPIC-CONFIG
Status: 📋 Pendente Jira

Descricao: |
  Interface para configurar as etapas da jornada de recrutamento,
  incluindo stages do pipeline, automações e transições.

Historia de Usuario: |
  Como admin, eu quero configurar as etapas do meu processo seletivo
  para refletir o fluxo real da minha empresa.

Requisitos Tecnicos:
  Frontend:
    - RecruitmentJourneyConfig.tsx
    - Stage editor
    - Automation toggles

Design & Componentes:
  Componentes:
    - StageList
    - StageEditor
    - AutomationConfig
    - TransitionRules

DoD:
  - [ ] Stages editáveis
  - [ ] Ordem ajustável
  - [ ] Automações configuráveis

Criterios de Aceitacao:
  - [ ] CRUD de stages funciona
  - [ ] Drag-and-drop para reordenar
  - [ ] Automações salvas

Arquivos de Referencia (Prototipo Replit):
  - recruitment-stages.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/recruitment-stages.ts
  - use-recruitment-stages.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/use-recruitment-stages.ts
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/backend-proxy/company/pipeline-templates/route.ts
  - pipeline_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/pipeline_service.py
  - pipeline.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/pipeline.py
```

> ⚠️ **DISCLAIMER: CARD RELACIONADO AO MENU DE CONFIGURAÇÕES**
> Este card faz parte do sistema de configurações da plataforma (Settings Menu).
> Consulte também: `docs/configuracoes-admin-cards-jira.md` para cards administrativos complementares.


---

### CARD CFG-004: Hub de Comunicação
**Épico:** É13 — Configurações Avançadas

```yaml
Titulo: [FRONTEND] Hub de Configuração de Comunicação
Tipo: Frontend
Area: Frontend
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 13
Prioridade: Alta
Epic: EPIC-CONFIG
Status: 📋 Pendente Jira

Descricao: |
  Hub centralizado para configurar todos os aspectos de comunicação:
  templates de email, WhatsApp, notificações, assinaturas e canais.

Historia de Usuario: |
  Como admin, eu quero configurar todos os templates e canais de
  comunicação em um único lugar organizado.

Requisitos Tecnicos:
  Frontend:
    - CommunicationHub.tsx (85k linhas)
    - Template management
    - Channel configuration
    - Signature editor

Design & Componentes:
  Layout:
    - Tabs por categoria
    - Lista de templates
    - Editor rich text
    - Preview panel

DoD:
  - [ ] Hub completo
  - [ ] Templates editáveis
  - [ ] Canais configuráveis

Criterios de Aceitacao:
  - [ ] CRUD de templates
  - [ ] Preview funciona
  - [ ] Variáveis dinâmicas

Arquivos de Referencia (Prototipo Replit):
  - page.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/admin/configuracoes/comunicacoes/page.tsx
  - BriefingsSection.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/admin/configuracoes/comunicacoes/components/BriefingsSection.tsx
  - AutomationsSection.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/admin/configuracoes/comunicacoes/components/AutomationsSection.tsx
  - types.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/admin/configuracoes/comunicacoes/components/types.ts
  - communication_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/communication_service.py
```

> ⚠️ **DISCLAIMER: CARD RELACIONADO AO MENU DE CONFIGURAÇÕES**
> Este card faz parte do sistema de configurações da plataforma (Settings Menu).
> Consulte também: `docs/configuracoes-admin-cards-jira.md` para cards administrativos complementares.


---

### CARD CFG-005: Dados da Empresa para LIA
**Épico:** É13 — Configurações Avançadas

```yaml
Titulo: [FRONTEND] Seção de Dados da Empresa
Tipo: Frontend
Area: Frontend
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 8
Prioridade: Media
Epic: EPIC-CONFIG
Status: 📋 Pendente Jira

Descricao: |
  Seção para gerenciar os dados da empresa que são consumidos
  pela LIA para gerar conteúdo contextualizado.

Historia de Usuario: |
  Como admin, eu quero cadastrar informações da empresa para
  que a LIA use esses dados nas comunicações automáticas.

Requisitos Tecnicos:
  Frontend:
    - CompanyDataSection.tsx
    - CompanyDataCard.tsx
    - Form validation

DoD:
  - [ ] Dados editáveis
  - [ ] Validação funciona
  - [ ] Salvamento persiste

Criterios de Aceitacao:
  - [ ] Campos de empresa
  - [ ] Valores e cultura
  - [ ] Benefícios

Arquivos de Referencia (Prototipo Replit):
  - company_configuration_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/company_configuration_service.py
  - culture_analyzer_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/culture_analyzer_service.py
  - company_scraper_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/company_scraper_service.py
```

> ⚠️ **DISCLAIMER: CARD RELACIONADO AO MENU DE CONFIGURAÇÕES**
> Este card faz parte do sistema de configurações da plataforma (Settings Menu).
> Consulte também: `docs/configuracoes-admin-cards-jira.md` para cards administrativos complementares.


---

### CARD IMP-001: Importação Inteligente de Dados
**Épico:** É13 — Configurações Avançadas

```yaml
Titulo: [FRONTEND] Smart Import Zone
Tipo: Frontend
Area: Frontend
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 8
Prioridade: Media
Epic: EPIC-CONFIG
Status: 📋 Pendente Jira

Descricao: |
  Zona de importação inteligente que detecta automaticamente o tipo
  de arquivo e extrai dados estruturados para preenchimento de campos.

Historia de Usuario: |
  Como recrutador, eu quero importar dados de arquivos (CSV, Excel, PDF)
  e ter os campos preenchidos automaticamente.

Requisitos Tecnicos:
  Frontend:
    - SmartImportZone.tsx
    - File type detection
    - Data extraction preview

DoD:
  - [ ] Upload funciona
  - [ ] Detecção de tipo
  - [ ] Extração de dados

Criterios de Aceitacao:
  - [ ] CSV/Excel suportados
  - [ ] Preview antes de importar
  - [ ] Mapeamento de campos

Arquivos de Referencia (Prototipo Replit):
  - jd_import_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/jd_import_service.py
  - cv_parser.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/cv_parser.py
  - template_importer_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/template_importer_service.py
  - cv-upload-modal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/cv/cv-upload-modal.tsx
```

> ⚠️ **DISCLAIMER: CARD RELACIONADO AO MENU DE CONFIGURAÇÕES**
> Este card faz parte do sistema de configurações da plataforma (Settings Menu).
> Consulte também: `docs/configuracoes-admin-cards-jira.md` para cards administrativos complementares.


---


## ÉPICO 14: INTEGRAÇÕES MVP

---

## TWILIO WHATSAPP - CARDS

---

### CARD INT-TWI-001: Configurar Twilio Account
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [INTEGRAÇÃO] Configurar Twilio Account
Tipo: Configuração SaaS
Area: Integração
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 3
Prioridade: Crítica
Epic: EPIC-INT-MVP
Status: 🔗 Configuração

Descricao: |
  Criar e configurar conta Twilio para integração com WhatsApp Business API.
  Configurar credenciais, webhook URLs e habilitar serviços necessários.

Historia de Usuario: |
  Como administrador do sistema, eu quero ter uma conta Twilio configurada
  para que a LIA possa enviar e receber mensagens WhatsApp.

Regras de Negocio:
  1. Conta Twilio deve estar verificada
  2. WhatsApp Business API habilitada
  3. Webhook URLs configuradas para ambiente dev e prod
  4. Credenciais armazenadas de forma segura (Secrets)
  5. Billing configurado com alertas de uso

Requisitos Tecnicos:
  Backend:
    - Variáveis de ambiente configuradas
    - Validação de credenciais no startup
  Dados:
    - Secrets: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
  Validacoes:
    - Account SID formato: AC[32 chars hex]
    - Auth Token: 32 chars

Integracoes Externas:
  Twilio:
    - Tipo: REST API + Webhooks
    - Console: https://console.twilio.com
    - SDK: twilio (Python)
    - Secrets:
      - TWILIO_ACCOUNT_SID (formato: ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx)
      - TWILIO_AUTH_TOKEN (32 caracteres)
      - TWILIO_PHONE_NUMBER (formato: whatsapp:+5511999999999)
    - Custo Estimado:
      - WhatsApp Business: $0.005/msg (utility) a $0.0042/msg (service)
      - Número BR: ~$2/mês
      - Mensagens recebidas: $0.005/msg
    - Limites:
      - Rate limit: 80 msg/segundo (Tier 1)
      - Escalável até 1000 msg/s com aprovação

Passo a Passo:
  1. Criar conta em https://www.twilio.com/try-twilio
  2. Verificar email e telefone
  3. Acessar Console → Messaging → Try WhatsApp
  4. Copiar Account SID e Auth Token
  5. Configurar secrets no Replit Secrets Manager
  6. Habilitar WhatsApp Sandbox para testes
  7. Configurar Webhook URLs (dev: ngrok, prod: domain)
  8. Testar conexão com script de validação

DoD (Definition of Done):
  - [ ] Conta Twilio criada e verificada
  - [ ] WhatsApp habilitado na conta
  - [ ] Secrets configurados no Replit
  - [ ] Script de teste de conexão funcionando
  - [ ] Documentação de setup atualizada

Criterios de Aceitacao:
  - [ ] Credenciais validadas via API
  - [ ] Console Twilio mostra conta ativa
  - [ ] Billing configurado com limite
  - [ ] Webhook URL registrada

Arquivos de Referencia (Prototipo Replit):
  - whatsapp_twilio_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_twilio_service.py
  - whatsapp_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_service.py
  - whatsapp_factory.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_factory.py
  - whatsapp.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/whatsapp.py
  - whatsapp_provider.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_provider.py
```

> ⚠️ **DISCLAIMER: CARD RELACIONADO AO MENU DE CONFIGURAÇÕES**
> Este card faz parte do sistema de configurações da plataforma (Settings Menu).
> Consulte também: `docs/configuracoes-admin-cards-jira.md` para cards administrativos complementares.


---

### CARD INT-TWI-002: Sandbox WhatsApp
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [BACKEND] Sandbox WhatsApp para Desenvolvimento
Tipo: Feature
Area: Full-Stack
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 5
Prioridade: Alta
Epic: EPIC-INT-MVP
Status: 📋 Pendente Jira
Dependencias: INT-TWI-001

Descricao: |
  Implementar cliente Twilio para WhatsApp Sandbox, permitindo
  testes de envio e recebimento de mensagens durante desenvolvimento.

Historia de Usuario: |
  Como desenvolvedor, eu quero usar o WhatsApp Sandbox
  para testar o fluxo de mensagens sem número de produção.

Regras de Negocio:
  1. Sandbox permite até 5 números cadastrados
  2. Mensagens expiram após 24h sem resposta
  3. Prefixo obrigatório para sandbox: "join [código]"
  4. Logs de todas as mensagens para debug
  5. Suporte a mensagens de texto, imagem e botões

Requisitos Tecnicos:
  Backend:
    - TwilioWhatsAppClient class
    - send_message(to, body, media_url?)
    - Singleton pattern para client
    - Retry com exponential backoff
  Dados:
    - whatsapp_messages: id, direction, phone, body, status, twilio_sid, created_at
  Validacoes:
    - Número no formato E.164: +55XXXXXXXXXXX
    - Body max 4096 caracteres

Comportamento de API:
  Endpoints:
    - POST /api/v1/whatsapp/send
    - GET /api/v1/whatsapp/status/{message_id}
  
  Request (send):
    ```json
    {
      "to": "+5511999999999",
      "body": "Olá! Esta é uma mensagem de teste.",
      "media_url": null
    }

Arquivos de Referencia (Prototipo Replit):
  - whatsapp_twilio_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_twilio_service.py
  - whatsapp_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_service.py
  - whatsapp_factory.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_factory.py
  - whatsapp.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/whatsapp.py
  - whatsapp_meta_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_meta_service.py
    ```
  
  Response (send):
    ```json
    {
      "success": true,
      "message_id": "uuid",
      "twilio_sid": "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
      "status": "queued"
    }
    ```

Integracoes Externas:
  Twilio WhatsApp Sandbox:
    - Endpoint: https://api.twilio.com/2010-04-01/Accounts/{AccountSid}/Messages.json
    - From: whatsapp:+14155238886 (sandbox number)
    - SDK Method: client.messages.create()
    - Docs: https://www.twilio.com/docs/whatsapp/sandbox

Codigo de Referencia:
  ```python
  from twilio.rest import Client
  
  class TwilioWhatsAppClient:
      def __init__(self):
          self.client = Client(
              settings.TWILIO_ACCOUNT_SID,
              settings.TWILIO_AUTH_TOKEN
          )
          self.from_number = settings.TWILIO_PHONE_NUMBER
      
      async def send_message(self, to: str, body: str, media_url: str = None) -> dict:
          message = self.client.messages.create(
              from_=f"whatsapp:{self.from_number}",
              to=f"whatsapp:{to}",
              body=body,
              media_url=[media_url] if media_url else None
          )
          return {"sid": message.sid, "status": message.status}
  ```

DoD (Definition of Done):
  - [ ] TwilioWhatsAppClient implementado
  - [ ] Endpoint de envio funcionando
  - [ ] Logs de mensagens persistidos
  - [ ] Testes unitários com mocks
  - [ ] Documentação de API

Criterios de Aceitacao:
  - [ ] Mensagem enviada aparece no WhatsApp
  - [ ] Status de entrega retornado
  - [ ] Erro tratado para número inválido
  - [ ] Retry automático em caso de timeout
```

---

### CARD INT-TWI-003: Número de Produção
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [INTEGRAÇÃO] Número WhatsApp Business de Produção
Tipo: Configuração
Area: Integração
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 5
Prioridade: Alta
Epic: EPIC-INT-MVP
Status: 📋 Pendente Jira
Dependencias: INT-TWI-002

Descricao: |
  Configurar número WhatsApp Business oficial para produção,
  incluindo verificação de empresa e aprovação Meta.

Historia de Usuario: |
  Como gerente de produto, eu quero um número WhatsApp oficial
  para que candidatos recebam mensagens profissionais da empresa.

Regras de Negocio:
  1. Número deve ser brasileiro (+55)
  2. Perfil business verificado pelo Meta
  3. Display name aprovado (ex: "LIA - Assistente RH")
  4. Logo e descrição configurados
  5. Horário de atendimento definido

Requisitos Tecnicos:
  Backend:
    - Migração de sandbox para production
    - Atualizar TWILIO_PHONE_NUMBER
    - Configurar fallback para sandbox em dev
  Dados:
    - config: whatsapp_production_number, whatsapp_display_name
  Validacoes:
    - Número verificado no Meta Business

Integracoes Externas:
  Twilio + Meta Business:
    - Tipo: WhatsApp Business API
    - Processo:
      1. Comprar número no Twilio Console
      2. Conectar Facebook Business Manager
      3. Criar WhatsApp Business Account
      4. Submeter para verificação Meta
      5. Aguardar aprovação (2-7 dias)
    - Custo:
      - Número BR: ~$2/mês
      - Mensagens: $0.0042-$0.0745/msg (depende da categoria)
    - Docs: https://www.twilio.com/docs/whatsapp/getting-started

Passo a Passo:
  1. Twilio Console → Phone Numbers → Buy Number (BR)
  2. Messaging → WhatsApp Senders → Add Sender
  3. Conectar Facebook Business Manager
  4. Criar WhatsApp Business Profile:
     - Display Name: "LIA - Assistente de Recrutamento"
     - Logo: 640x640 PNG
     - Description: "Assistente inteligente para processos seletivos"
     - Category: "Human Resources"
  5. Submeter para verificação
  6. Atualizar secrets após aprovação

DoD (Definition of Done):
  - [ ] Número BR adquirido
  - [ ] Perfil business configurado
  - [ ] Verificação Meta aprovada
  - [ ] Secrets de produção atualizados
  - [ ] Teste de envio em produção

Criterios de Aceitacao:
  - [ ] Número aparece com nome "LIA" no WhatsApp
  - [ ] Logo visível no perfil
  - [ ] Mensagens entregues sem restrição
  - [ ] Tier de envio adequado ao volume

Arquivos de Referencia (Prototipo Replit):
  - whatsapp_twilio_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_twilio_service.py
  - whatsapp_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_service.py
  - whatsapp_factory.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_factory.py
  - whatsapp.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/whatsapp.py
```

---

### CARD INT-TWI-004: Webhook de Mensagens
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [BACKEND] Webhook de Recebimento de Mensagens WhatsApp
Tipo: Feature
Area: Full-Stack
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 8
Prioridade: Crítica
Epic: EPIC-INT-MVP
Status: 📋 Pendente Jira
Dependencias: INT-TWI-002

Descricao: |
  Implementar endpoint webhook para receber mensagens e status
  de entrega do Twilio WhatsApp, processando respostas de candidatos.

Historia de Usuario: |
  Como sistema LIA, eu quero receber mensagens de candidatos
  para processar respostas de triagem em tempo real.

Regras de Negocio:
  1. Validar signature do Twilio em todas as requests
  2. Responder 200 OK em menos de 5 segundos
  3. Processar mensagem de forma assíncrona
  4. Identificar candidato pelo número de telefone
  5. Atualizar status da conversa em tempo real
  6. Suportar mensagens de texto, áudio e imagem

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/webhooks/twilio/whatsapp
    - Validação de X-Twilio-Signature
    - Background task para processamento
    - Queue (Redis) para mensagens
  Frontend:
    - Atualização real-time no monitoramento (SSE/WebSocket)
  Dados:
    - whatsapp_messages: atualizar com received messages
    - whatsapp_conversations: status, last_message_at

Comportamento de API:
  Endpoint: POST /api/v1/webhooks/twilio/whatsapp
  
  Headers Esperados:
    - X-Twilio-Signature: [signature]
    - Content-Type: application/x-www-form-urlencoded
  
  Request Body (form-data):

Arquivos de Referencia (Prototipo Replit):
  - whatsapp_twilio_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_twilio_service.py
  - whatsapp_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_service.py
  - whatsapp_factory.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_factory.py
  - whatsapp.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/whatsapp.py
  - webhooks.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/webhooks.py
    ```
    MessageSid=SMxxxxxxxx
    AccountSid=ACxxxxxxxx
    From=whatsapp:+5511999999999
    To=whatsapp:+5511888888888
    Body=Sim, tenho interesse na vaga
    NumMedia=0
    ```
  
  Response:
    ```xml
    <?xml version="1.0" encoding="UTF-8"?>
    <Response></Response>
    ```
    Status: 200 OK (sempre, para evitar retries)

Integracoes Externas:
  Twilio Webhooks:
    - URL: https://[domain]/api/v1/webhooks/twilio/whatsapp
    - Method: POST
    - Formato: application/x-www-form-urlencoded
    - Validação: X-Twilio-Signature (HMAC-SHA1)
    - Docs: https://www.twilio.com/docs/usage/webhooks

Codigo de Referencia:
  ```python
  from fastapi import Request, HTTPException
  from twilio.request_validator import RequestValidator
  
  validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
  
  @router.post("/webhooks/twilio/whatsapp")
  async def twilio_webhook(request: Request, background_tasks: BackgroundTasks):
      form_data = await request.form()
      signature = request.headers.get("X-Twilio-Signature", "")
      url = str(request.url)
      
      if not validator.validate(url, dict(form_data), signature):
          raise HTTPException(status_code=403, detail="Invalid signature")
      
      message_data = {
          "sid": form_data.get("MessageSid"),
          "from": form_data.get("From"),
          "body": form_data.get("Body"),
          "num_media": form_data.get("NumMedia", "0")
      }
      
      background_tasks.add_task(process_incoming_message, message_data)
      
      return Response(
          content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
          media_type="application/xml"
      )
  ```

DoD (Definition of Done):
  - [ ] Endpoint webhook implementado
  - [ ] Validação de signature funcionando
  - [ ] Mensagens persistidas no banco
  - [ ] Background processing com Redis
  - [ ] Logs de auditoria
  - [ ] Testes com mock do Twilio

Criterios de Aceitacao:
  - [ ] Webhook responde 200 em < 5s
  - [ ] Signature inválida retorna 403
  - [ ] Mensagem aparece na conversa
  - [ ] Status atualizado em real-time
```

---

### CARD INT-TWI-005: Templates Aprovados Meta (HSM)
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [INTEGRAÇÃO] Templates de Mensagem Aprovados pelo Meta
Tipo: Configuração + Backend
Area: Integração
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 8
Prioridade: Alta
Epic: EPIC-INT-MVP
Status: 📋 Pendente Jira
Dependencias: INT-TWI-003

Descricao: |
  Criar e submeter templates de mensagem HSM (Highly Structured Messages)
  para aprovação do Meta, permitindo iniciar conversas com candidatos.

Historia de Usuario: |
  Como LIA, eu quero usar templates aprovados pelo Meta
  para iniciar conversas com candidatos de forma proativa.

Regras de Negocio:
  1. Templates obrigatórios para iniciar conversa (fora da janela 24h)
  2. Cada template deve ser aprovado pelo Meta
  3. Suportar variáveis dinâmicas {{1}}, {{2}}, etc
  4. Templates por categoria: abordagem, agendamento, lembrete, feedback
  5. Fallback para mensagem simples dentro da janela 24h
  6. Versionamento de templates

Requisitos Tecnicos:
  Backend:
    - WhatsAppTemplateService class
    - send_template_message(to, template_name, variables)
    - Mapeamento template_name → content_sid
  Dados:
    - whatsapp_templates: id, name, content_sid, category, variables, status, approved_at

Templates a Criar:
  1. triagem_convite:
     - Categoria: UTILITY
     - Texto: "Olá {{1}}! Sou a LIA, assistente de recrutamento da {{2}}. 
              Você foi selecionado(a) para a vaga de {{3}}. 
              Posso fazer algumas perguntas rápidas? Responda SIM para começar."
     - Variáveis: [candidato_nome, empresa_nome, vaga_titulo]
  
  2. agendamento_entrevista:
     - Categoria: UTILITY
     - Texto: "Parabéns {{1}}! Você avançou no processo seletivo para {{2}}. 
              Gostaria de agendar sua entrevista para {{3}} às {{4}}? 
              Responda SIM para confirmar ou NÃO para outras opções."
     - Variáveis: [candidato_nome, vaga_titulo, data, horario]
  
  3. lembrete_entrevista:
     - Categoria: UTILITY
     - Texto: "Olá {{1}}! Lembrete: sua entrevista para {{2}} está agendada para amanhã, 
              {{3}} às {{4}}. Link: {{5}}"
     - Variáveis: [candidato_nome, vaga_titulo, data, horario, link_teams]
  
  4. feedback_reprovacao:
     - Categoria: UTILITY
     - Texto: "Olá {{1}}, agradecemos seu interesse na vaga de {{2}} na {{3}}. 
              Após análise, decidimos seguir com outros candidatos neste momento. 
              Seu perfil ficará em nosso banco para futuras oportunidades."
     - Variáveis: [candidato_nome, vaga_titulo, empresa_nome]

Comportamento de API:
  Endpoint: POST /api/v1/whatsapp/send-template
  
  Request:
    ```json
    {
      "to": "+5511999999999",
      "template_name": "triagem_convite",
      "variables": {
        "1": "Maria Silva",
        "2": "WeDo Talent",
        "3": "Desenvolvedor Python Sênior"
      }
    }

Arquivos de Referencia (Prototipo Replit):
  - whatsapp_twilio_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_twilio_service.py
  - whatsapp_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_service.py
  - whatsapp_factory.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_factory.py
  - whatsapp.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/whatsapp.py
  - whatsapp_meta_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_meta_service.py
  - communication_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/communication_service.py
    ```
  
  Response:
    ```json
    {
      "success": true,
      "message_id": "uuid",
      "twilio_sid": "SMxxxxxxxx",
      "template_used": "triagem_convite"
    }
    ```

Integracoes Externas:
  Meta Business + Twilio:
    - Console: Twilio → Messaging → Content Template Builder
    - Aprovação: 24-48h típico
    - Rejeição: motivo fornecido, resubmissão permitida
    - Docs: https://www.twilio.com/docs/content/whatsapp-templates

DoD (Definition of Done):
  - [ ] 4 templates criados no Twilio Console
  - [ ] Templates submetidos para aprovação
  - [ ] Service de envio de templates
  - [ ] Mapeamento no banco de dados
  - [ ] Fallback para mensagem simples

Criterios de Aceitacao:
  - [ ] Templates aprovados pelo Meta
  - [ ] Mensagem com template enviada corretamente
  - [ ] Variáveis substituídas no texto
  - [ ] Erro tratado para template não aprovado
```

---

### CARD INT-TWI-006: Status Delivery Reports
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [BACKEND] Status Delivery Reports WhatsApp
Tipo: Feature
Area: Full-Stack
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 5
Prioridade: Alta
Epic: EPIC-INT-MVP
Status: 📋 Pendente Jira
Dependencias: INT-TWI-004

Descricao: |
  Implementar recebimento e processamento de status de entrega
  (delivery reports) das mensagens WhatsApp via webhook.

Historia de Usuario: |
  Como recrutador, eu quero ver o status de entrega das mensagens
  para saber se o candidato recebeu/leu a comunicação.

Regras de Negocio:
  1. Rastrear todos os status: queued, sent, delivered, read, failed
  2. Atualizar status em tempo real na UI
  3. Alertar para mensagens com erro de entrega
  4. Registrar timestamp de cada transição
  5. Calcular métricas de entrega (taxa de leitura, etc)

Requisitos Tecnicos:
  Backend:
    - Webhook já existente (INT-TWI-004) processa status
    - StatusUpdateService para atualizar mensagens
    - Emitir eventos SSE/WebSocket para frontend
  Frontend:
    - Ícones de status: ✓ (enviado), ✓✓ (entregue), ✓✓ azul (lido)
  Dados:
    - whatsapp_messages: status, sent_at, delivered_at, read_at, failed_reason

Comportamento de API:
  Webhook Status Callback (recebido do Twilio):

Arquivos de Referencia (Prototipo Replit):
  - whatsapp_twilio_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_twilio_service.py
  - whatsapp_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_service.py
  - whatsapp_factory.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_factory.py
  - whatsapp.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/whatsapp.py
  - communication_dispatcher.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/communication_dispatcher.py
    ```
    MessageSid=SMxxxxxxxx
    MessageStatus=delivered
    To=whatsapp:+5511999999999
    ```
  
  Status possíveis:
    - queued: Mensagem na fila
    - sent: Enviada ao WhatsApp
    - delivered: Entregue ao dispositivo
    - read: Lida pelo destinatário
    - failed: Falha no envio
    - undelivered: Não entregue

  Endpoint consulta: GET /api/v1/whatsapp/messages/{message_id}/status
  
  Response:
    ```json
    {
      "message_id": "uuid",
      "twilio_sid": "SMxxxxxxxx",
      "status": "read",
      "timestamps": {
        "queued_at": "2026-01-22T10:00:00Z",
        "sent_at": "2026-01-22T10:00:01Z",
        "delivered_at": "2026-01-22T10:00:03Z",
        "read_at": "2026-01-22T10:05:00Z"
      }
    }
    ```

Integracoes Externas:
  Twilio Status Callbacks:
    - Configurar em: Console → Messaging → WhatsApp Sender → Status Callback URL
    - URL: https://[domain]/api/v1/webhooks/twilio/status
    - Docs: https://www.twilio.com/docs/sms/api/message-resource#delivery-related-errors

DoD (Definition of Done):
  - [ ] Webhook de status configurado
  - [ ] Status atualizados no banco
  - [ ] Timestamps de transição salvos
  - [ ] Frontend mostra ícones de status
  - [ ] Métricas de entrega calculadas

Criterios de Aceitacao:
  - [ ] Status muda de sent → delivered → read
  - [ ] Ícones corretos na UI
  - [ ] Mensagem failed mostra motivo
  - [ ] Dashboard mostra taxa de leitura
```

---

### CARD INT-TWI-007: Rate Limiting e Filas
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [BACKEND] Rate Limiting e Filas Redis para WhatsApp
Tipo: Feature
Area: Full-Stack
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 8
Prioridade: Alta
Epic: EPIC-INT-MVP
Status: 📋 Pendente Jira
Dependencias: INT-TWI-002, INT-TWI-004

Descricao: |
  Implementar sistema de rate limiting e filas usando Redis
  para controlar o envio de mensagens WhatsApp e evitar throttling.

Historia de Usuario: |
  Como sistema, eu quero controlar a taxa de envio de mensagens
  para respeitar os limites do Twilio e garantir entrega.

Regras de Negocio:
  1. Limite padrão: 80 mensagens/segundo (Tier 1 Twilio)
  2. Fila com prioridades: urgente > normal > batch
  3. Retry automático com exponential backoff
  4. Dead letter queue para mensagens que falharam 3x
  5. Métricas de fila em tempo real
  6. Throttling por empresa (multi-tenant)

Requisitos Tecnicos:
  Backend:
    - WhatsAppQueueService com Redis
    - Worker assíncrono para processar fila
    - Rate limiter com sliding window
    - Celery ou ARQ para background jobs
  Dados:
    - Redis keys: whatsapp:queue:{priority}, whatsapp:rate:{account}, whatsapp:dlq

Comportamento de API:
  Endpoint enfileirar: POST /api/v1/whatsapp/queue
  
  Request:
    ```json
    {
      "messages": [
        {"to": "+5511999999999", "body": "Mensagem 1"},
        {"to": "+5511888888888", "body": "Mensagem 2"}
      ],
      "priority": "normal",
      "scheduled_at": null
    }

Arquivos de Referencia (Prototipo Replit):
  - whatsapp_twilio_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_twilio_service.py
  - whatsapp_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_service.py
  - whatsapp_factory.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/whatsapp_factory.py
  - whatsapp.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/whatsapp.py
  - circuit_breaker.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/circuit_breaker.py
  - automation_scheduler.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/automation_scheduler.py
    ```
  
  Response:
    ```json
    {
      "queued": 2,
      "job_id": "uuid",
      "estimated_completion": "2026-01-22T10:05:00Z"
    }
    ```
  
  Endpoint status fila: GET /api/v1/whatsapp/queue/status
  
  Response:
    ```json
    {
      "pending": 150,
      "processing": 10,
      "completed_last_hour": 500,
      "failed_last_hour": 2,
      "rate_limit_remaining": 70,
      "rate_limit_reset_at": "2026-01-22T10:00:01Z"
    }
    ```

Integracoes Externas:
  Redis:
    - Tipo: In-memory data store
    - Uso: Filas, rate limiting, cache
    - Connection: REDIS_URL (Replit ou externo)
    - Estruturas:
      - Lists para filas (LPUSH/RPOP)
      - Sorted Sets para scheduled (ZADD/ZRANGEBYSCORE)
      - Strings com TTL para rate limiting
    - Custo: Gratuito (Replit) ou ~$15/mês (Redis Cloud)

Codigo de Referencia:
  ```python
  import redis.asyncio as redis
  from datetime import datetime, timedelta
  
  class WhatsAppRateLimiter:
      def __init__(self, redis_client: redis.Redis):
          self.redis = redis_client
          self.rate_limit = 80  # msgs/second
          self.window = 1  # second
      
      async def can_send(self, account_id: str) -> bool:
          key = f"whatsapp:rate:{account_id}"
          current = await self.redis.incr(key)
          if current == 1:
              await self.redis.expire(key, self.window)
          return current <= self.rate_limit
      
      async def enqueue(self, message: dict, priority: str = "normal"):
          queue_key = f"whatsapp:queue:{priority}"
          await self.redis.lpush(queue_key, json.dumps(message))
  ```

DoD (Definition of Done):
  - [ ] Redis configurado e conectado
  - [ ] Rate limiter implementado
  - [ ] Fila com prioridades funcionando
  - [ ] Worker processando mensagens
  - [ ] Dead letter queue configurada
  - [ ] Dashboard de métricas de fila

Criterios de Aceitacao:
  - [ ] Mensagens enfileiradas corretamente
  - [ ] Rate limit respeitado (80/s)
  - [ ] Retry automático em falhas
  - [ ] Mensagens urgentes processadas primeiro
  - [ ] DLQ recebe mensagens que falharam 3x
```

---

## MICROSOFT GRAPH - CARDS

---

### CARD INT-MSG-001: Configurar Azure App Registration
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [INTEGRAÇÃO] Configurar Azure App Registration
Tipo: Configuração SaaS
Area: Integração
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 5
Prioridade: Alta
Epic: EPIC-INT-MVP
Status: 🔗 Configuração

Descricao: |
  Criar e configurar Azure App Registration para integração
  com Microsoft Graph API (Calendar, Teams, Outlook).

Historia de Usuario: |
  Como administrador, eu quero configurar a integração com Microsoft
  para que a LIA possa agendar reuniões no calendário dos recrutadores.

Regras de Negocio:
  1. App Registration em Azure AD
  2. Permissões delegadas para Calendar e OnlineMeetings
  3. Suporte a multi-tenant para diferentes empresas
  4. Redirect URIs para OAuth flow
  5. Client secret com rotação anual
  6. Refazer App Registration (mudança de conta Microsoft). Reunião 06/02/2026: conta original mudou, necessário recriar.

Requisitos Tecnicos:
  Backend:
    - AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID
    - Scopes: Calendars.ReadWrite, OnlineMeetings.ReadWrite
  Dados:
    - Secrets gerenciados no Replit Secrets

Integracoes Externas:
  Azure AD / Microsoft Entra:
    - Console: https://portal.azure.com → App registrations
    - Tipo: OAuth 2.0 Authorization Code Flow
    - Scopes necessários:
      - Calendars.ReadWrite (ler/escrever calendário)
      - OnlineMeetings.ReadWrite (criar reuniões Teams)
      - User.Read (perfil do usuário)
      - offline_access (refresh token)
    - Secrets:
      - AZURE_CLIENT_ID
      - AZURE_CLIENT_SECRET
      - AZURE_TENANT_ID (ou "common" para multi-tenant)
    - Custo: Gratuito (Microsoft Graph API)
    - Docs: https://docs.microsoft.com/graph/overview

Passo a Passo:
  1. Azure Portal → App registrations → New registration
  2. Name: "LIA Platform - Calendar Integration"
  3. Supported account types: "Accounts in any organizational directory" (multi-tenant)
  4. Redirect URI: 
     - Dev: http://localhost:5000/api/auth/microsoft/callback
     - Prod: https://[domain]/api/auth/microsoft/callback
  5. API permissions → Add permission → Microsoft Graph:
     - Delegated: Calendars.ReadWrite
     - Delegated: OnlineMeetings.ReadWrite
     - Delegated: User.Read
     - Delegated: offline_access
  6. Certificates & secrets → New client secret (24 meses)
  7. Copiar: Application (client) ID, Client secret value
  8. Salvar secrets no Replit

DoD (Definition of Done):
  - [ ] App Registration criado no Azure
  - [ ] Permissões configuradas
  - [ ] Redirect URIs para dev e prod
  - [ ] Secrets salvos no Replit
  - [ ] Documentação de setup

Criterios de Aceitacao:
  - [ ] App visível no Azure Portal
  - [ ] Scopes corretos atribuídos
  - [ ] Client secret válido
  - [ ] Teste de OAuth flow básico

Arquivos de Referencia (Prototipo Replit):
  - microsoft_graph_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/microsoft_graph_service.py
  - graph_client.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/graph_client.py
  - microsoft_graph.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/microsoft_graph.py
```

> ⚠️ **DISCLAIMER: CARD RELACIONADO AO MENU DE CONFIGURAÇÕES**
> Este card faz parte do sistema de configurações da plataforma (Settings Menu).
> Consulte também: `docs/configuracoes-admin-cards-jira.md` para cards administrativos complementares.


---

### CARD INT-MSG-002: OAuth Flow Microsoft
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [BACKEND] OAuth Flow Microsoft (Authorization Code)
Tipo: Feature
Area: Full-Stack
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 8
Prioridade: Alta
Epic: EPIC-INT-MVP
Status: 📋 Pendente Jira
Dependencias: INT-MSG-001

Descricao: |
  Implementar fluxo OAuth 2.0 Authorization Code com Microsoft
  para obter tokens de acesso ao Calendar e Teams.

Historia de Usuario: |
  Como recrutador, eu quero conectar minha conta Microsoft
  para que a LIA possa acessar meu calendário.

Regras de Negocio:
  1. OAuth com PKCE para segurança
  2. Tokens armazenados de forma segura (encrypted)
  3. Estado de conexão visível na UI
  4. Suporte a múltiplas contas por empresa
  5. Desconectar a qualquer momento
  6. Re-autorização automática se permissões mudarem

Requisitos Tecnicos:
  Backend:
    - GET /api/v1/auth/microsoft/authorize
    - GET /api/v1/auth/microsoft/callback
    - POST /api/v1/auth/microsoft/disconnect
    - MicrosoftOAuthService class
  Frontend:
    - Botão "Conectar Microsoft 365"
    - Status de conexão
  Dados:
    - microsoft_connections: user_id, access_token (encrypted), refresh_token (encrypted), expires_at, scope

Comportamento de API:
  Iniciar OAuth:
    GET /api/v1/auth/microsoft/authorize
    
    Response: Redirect to Microsoft login

Arquivos de Referencia (Prototipo Replit):
  - microsoft_graph_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/microsoft_graph_service.py
  - graph_client.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/graph_client.py
  - microsoft_graph.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/microsoft_graph.py
    ```
    https://login.microsoftonline.com/common/oauth2/v2.0/authorize?
      client_id={client_id}&
      response_type=code&
      redirect_uri={redirect_uri}&
      scope=Calendars.ReadWrite OnlineMeetings.ReadWrite User.Read offline_access&
      state={state}&
      code_challenge={challenge}&
      code_challenge_method=S256
    ```
  
  Callback:
    GET /api/v1/auth/microsoft/callback?code={code}&state={state}
    
    Backend troca code por tokens:
    POST https://login.microsoftonline.com/common/oauth2/v2.0/token
    
    Response (redirect para frontend):
    ```
    /settings/integrations?microsoft=connected
    ```
  
  Status:
    GET /api/v1/auth/microsoft/status
    
    Response:
    ```json
    {
      "connected": true,
      "email": "recruiter@company.com",
      "expires_at": "2026-01-22T11:00:00Z",
      "scopes": ["Calendars.ReadWrite", "OnlineMeetings.ReadWrite"]
    }
    ```

Integracoes Externas:
  Microsoft Identity Platform:
    - Authorization endpoint: https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize
    - Token endpoint: https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token
    - SDK: msal (Microsoft Authentication Library for Python)
    - Docs: https://docs.microsoft.com/azure/active-directory/develop/v2-oauth2-auth-code-flow

Codigo de Referencia:
  ```python
  from msal import ConfidentialClientApplication
  
  class MicrosoftOAuthService:
      def __init__(self):
          self.app = ConfidentialClientApplication(
              client_id=settings.AZURE_CLIENT_ID,
              client_credential=settings.AZURE_CLIENT_SECRET,
              authority=f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}"
          )
          self.scopes = [
              "Calendars.ReadWrite",
              "OnlineMeetings.ReadWrite",
              "User.Read",
              "offline_access"
          ]
      
      def get_authorization_url(self, state: str) -> str:
          return self.app.get_authorization_request_url(
              scopes=self.scopes,
              state=state,
              redirect_uri=settings.MICROSOFT_REDIRECT_URI
          )
      
      async def exchange_code(self, code: str) -> dict:
          result = self.app.acquire_token_by_authorization_code(
              code=code,
              scopes=self.scopes,
              redirect_uri=settings.MICROSOFT_REDIRECT_URI
          )
          return result
  ```

DoD (Definition of Done):
  - [ ] OAuth flow completo implementado
  - [ ] Tokens armazenados encrypted
  - [ ] Refresh token funcionando
  - [ ] UI de conexão/desconexão
  - [ ] Testes de integração

Criterios de Aceitacao:
  - [ ] Login Microsoft funciona
  - [ ] Tokens salvos no banco
  - [ ] Status de conexão correto
  - [ ] Desconexão remove tokens
```

---

### CARD INT-MSG-003: Calendar API
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [BACKEND] Microsoft Calendar API (Read/Write)
Tipo: Feature
Area: Full-Stack
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 8
Prioridade: Alta
Epic: EPIC-INT-MVP
Status: 📋 Pendente Jira
Dependencias: INT-MSG-002

Descricao: |
  Implementar integração com Microsoft Graph Calendar API para
  consultar disponibilidade e criar eventos de entrevista.

Historia de Usuario: |
  Como LIA, eu quero acessar o calendário do recrutador
  para sugerir horários disponíveis para entrevistas.

Regras de Negocio:
  1. Consultar free/busy do calendário
  2. Criar eventos com duração configurável (30min, 45min, 60min)
  3. Incluir link do Teams automaticamente
  4. Adicionar candidato como attendee
  5. Enviar convite por email (via Graph)
  6. Suportar timezone do recrutador

Requisitos Tecnicos:
  Backend:
    - MicrosoftCalendarService class
    - get_free_busy(user_id, start, end)
    - create_event(user_id, event_data)
    - update_event / delete_event
  Dados:
    - scheduled_interviews: id, recruiter_id, candidate_id, event_id, start, end, teams_link

Comportamento de API:
  Consultar disponibilidade:
    GET /api/v1/calendar/availability?start={iso_date}&end={iso_date}&duration=60
    
    Response:
    ```json
    {
      "available_slots": [
        {"start": "2026-01-23T09:00:00-03:00", "end": "2026-01-23T10:00:00-03:00"},
        {"start": "2026-01-23T14:00:00-03:00", "end": "2026-01-23T15:00:00-03:00"}
      ],
      "timezone": "America/Sao_Paulo"
    }

Arquivos de Referencia (Prototipo Replit):
  - microsoft_graph_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/microsoft_graph_service.py
  - graph_client.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/graph_client.py
  - calendar_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/calendar_service.py
  - calendar.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/calendar.py
    ```
  
  Criar evento:
    POST /api/v1/calendar/events
    
    Request:
    ```json
    {
      "subject": "Entrevista - Maria Silva - Dev Python",
      "start": "2026-01-23T14:00:00-03:00",
      "end": "2026-01-23T15:00:00-03:00",
      "attendees": [
        {"email": "maria.silva@email.com", "name": "Maria Silva"}
      ],
      "include_teams_link": true,
      "body": "Entrevista para vaga de Desenvolvedor Python Sênior"
    }
    ```
    
    Response:
    ```json
    {
      "event_id": "AAMkAGI...",
      "web_link": "https://outlook.office.com/calendar/item/...",
      "teams_link": "https://teams.microsoft.com/l/meetup-join/..."
    }
    ```

Integracoes Externas:
  Microsoft Graph Calendar:
    - Base URL: https://graph.microsoft.com/v1.0
    - Endpoints:
      - GET /me/calendar/calendarView (eventos)
      - POST /me/calendar/getSchedule (free/busy)
      - POST /me/calendar/events (criar)
      - PATCH /me/calendar/events/{id} (atualizar)
      - DELETE /me/calendar/events/{id} (deletar)
    - SDK: msgraph-sdk-python
    - Docs: https://docs.microsoft.com/graph/api/resources/calendar

DoD (Definition of Done):
  - [ ] CalendarService implementado
  - [ ] Free/busy query funcionando
  - [ ] Criação de eventos
  - [ ] Timezone handling correto
  - [ ] Testes com mock do Graph

Criterios de Aceitacao:
  - [ ] Slots disponíveis retornados
  - [ ] Evento criado no Outlook
  - [ ] Candidato recebe convite
  - [ ] Evento aparece no dashboard
```

---

### CARD INT-MSG-004: Teams Meeting API
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [BACKEND] Teams Meeting API (Criar Reunião Online)
Tipo: Feature
Area: Full-Stack
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 5
Prioridade: Alta
Epic: EPIC-INT-MVP
Status: 📋 Pendente Jira
Dependencias: INT-MSG-003

Descricao: |
  Implementar criação de reuniões Microsoft Teams automaticamente
  ao agendar entrevistas, gerando link de acesso.

Historia de Usuario: |
  Como LIA, eu quero criar reuniões Teams automaticamente
  para que entrevistas online tenham link de acesso pronto.

Regras de Negocio:
  1. Criar Teams meeting ao agendar entrevista
  2. Incluir link no evento do calendário
  3. Link acessível para externos (candidatos)
  4. Lobby habilitado por padrão (segurança)
  5. Gravação opcional (configurável)
  6. Suporte a reuniões ad-hoc e agendadas

Requisitos Tecnicos:
  Backend:
    - TeamsMeetingService class
    - create_meeting(organizer_id, subject, start, end)
    - Integrado com CalendarService
  Dados:
    - scheduled_interviews: teams_meeting_id, teams_join_url

Comportamento de API:
  Criar reunião Teams (interno, usado pelo CalendarService):
    POST https://graph.microsoft.com/v1.0/me/onlineMeetings
    
    Request:
    ```json
    {
      "startDateTime": "2026-01-23T14:00:00-03:00",
      "endDateTime": "2026-01-23T15:00:00-03:00",
      "subject": "Entrevista - Maria Silva",
      "lobbyBypassSettings": {
        "scope": "everyone",
        "isDialInBypassEnabled": false
      },
      "allowedPresenters": "organizer"
    }

Arquivos de Referencia (Prototipo Replit):
  - microsoft_graph_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/microsoft_graph_service.py
  - graph_client.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/graph_client.py
  - teams_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/teams_service.py
  - teams.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/teams.py
    ```
    
    Response:
    ```json
    {
      "id": "MeetingId",
      "joinWebUrl": "https://teams.microsoft.com/l/meetup-join/...",
      "subject": "Entrevista - Maria Silva",
      "audioConferencing": {
        "dialinUrl": "https://dialin.teams.microsoft.com/..."
      }
    }
    ```

Integracoes Externas:
  Microsoft Graph Online Meetings:
    - Endpoint: POST /me/onlineMeetings
    - Scopes: OnlineMeetings.ReadWrite
    - Docs: https://docs.microsoft.com/graph/api/application-post-onlinemeetings

DoD (Definition of Done):
  - [ ] TeamsMeetingService implementado
  - [ ] Reunião criada com link
  - [ ] Link incluído no evento
  - [ ] Candidato pode acessar
  - [ ] Testes com mock

Criterios de Aceitacao:
  - [ ] Link Teams gerado
  - [ ] Lobby funcionando
  - [ ] Link válido para externos
  - [ ] Evento mostra link
```

---

### CARD INT-MSG-005: Webhook de Eventos
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [BACKEND] Webhook de Eventos Microsoft Graph
Tipo: Feature
Area: Full-Stack
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 8
Prioridade: Média
Epic: EPIC-INT-MVP
Status: 📋 Pendente Jira
Dependencias: INT-MSG-003

Descricao: |
  Implementar subscriptions do Microsoft Graph para receber
  notificações de alterações em calendário (cancelamentos, reagendamentos).

Historia de Usuario: |
  Como sistema, eu quero ser notificado sobre alterações no calendário
  para manter sincronizadas as entrevistas agendadas.

Regras de Negocio:
  1. Webhook para eventos created, updated, deleted
  2. Renovação automática de subscription (antes de expirar)
  3. Validação de notificação (clientState)
  4. Sincronização delta para recuperar perdas
  5. Notificar recrutador sobre alterações do candidato

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/webhooks/microsoft/notifications
    - GraphSubscriptionService class
    - Background job para renovar subscriptions
  Dados:
    - graph_subscriptions: id, user_id, subscription_id, resource, expires_at

Comportamento de API:
  Endpoint webhook: POST /api/v1/webhooks/microsoft/notifications
  
  Validation request (Microsoft verifica endpoint):
    POST /api/v1/webhooks/microsoft/notifications?validationToken=xxx
    
    Response: 200 OK + validationToken (plain text)
  
  Notification request:
    ```json
    {
      "value": [
        {
          "subscriptionId": "...",
          "clientState": "secret",
          "changeType": "updated",
          "resource": "me/events/AAMkAGI...",
          "resourceData": {
            "@odata.type": "#Microsoft.Graph.Event",
            "id": "AAMkAGI..."
          }
        }
      ]
    }

Arquivos de Referencia (Prototipo Replit):
  - microsoft_graph_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/microsoft_graph_service.py
  - graph_client.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/graph_client.py
  - webhooks.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/webhooks.py
    ```
    
    Response: 202 Accepted

Integracoes Externas:
  Microsoft Graph Subscriptions:
    - Criar: POST /subscriptions
    - Renovar: PATCH /subscriptions/{id}
    - Resource: /me/events
    - ChangeTypes: created, updated, deleted
    - Max expiration: 3 dias para calendário
    - Docs: https://docs.microsoft.com/graph/webhooks

DoD (Definition of Done):
  - [ ] Webhook endpoint implementado
  - [ ] Subscription criada por usuário
  - [ ] Renovação automática
  - [ ] Alterações refletidas no sistema
  - [ ] Testes de integração

Criterios de Aceitacao:
  - [ ] Validação do Microsoft funciona
  - [ ] Notificações recebidas
  - [ ] Evento alterado sincronizado
  - [ ] Subscription renova antes de expirar
```

---

### CARD INT-MSG-006: Token Refresh
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [BACKEND] Token Refresh Automático Microsoft
Tipo: Feature
Area: Full-Stack
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 5
Prioridade: Crítica
Epic: EPIC-INT-MVP
Status: 📋 Pendente Jira
Dependencias: INT-MSG-002

Descricao: |
  Implementar refresh automático de access tokens Microsoft
  antes de expirar, garantindo acesso contínuo ao Graph API.

Historia de Usuario: |
  Como sistema, eu quero que tokens sejam renovados automaticamente
  para que integrações não quebrem por expiração.

Regras de Negocio:
  1. Access token expira em ~1 hora
  2. Refresh token válido por 90 dias (se usado)
  3. Renovar access token 5 min antes de expirar
  4. Re-autorização se refresh token inválido
  5. Notificar usuário se necessário re-login
  6. Retry com exponential backoff em erros

Requisitos Tecnicos:
  Backend:
    - TokenRefreshService class
    - Middleware para verificar expiração
    - Background job para refresh proativo
  Dados:
    - microsoft_connections: access_token, refresh_token, expires_at, refresh_error_count

Comportamento de API:
  Refresh interno (não exposto):
    POST https://login.microsoftonline.com/common/oauth2/v2.0/token
    
    Request:

Arquivos de Referencia (Prototipo Replit):
  - microsoft_graph_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/microsoft_graph_service.py
  - graph_client.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/graph_client.py
    ```
    grant_type=refresh_token
    client_id={client_id}
    client_secret={client_secret}
    refresh_token={refresh_token}
    scope=Calendars.ReadWrite OnlineMeetings.ReadWrite User.Read offline_access
    ```
    
    Response:
    ```json
    {
      "access_token": "eyJ...",
      "token_type": "Bearer",
      "expires_in": 3600,
      "refresh_token": "OAQABAA...",
      "scope": "..."
    }
    ```

Codigo de Referencia:
  ```python
  class TokenRefreshService:
      async def ensure_valid_token(self, user_id: str) -> str:
          connection = await self.get_connection(user_id)
          
          if connection.expires_at < datetime.utcnow() + timedelta(minutes=5):
              new_tokens = await self.refresh_access_token(connection.refresh_token)
              await self.update_tokens(user_id, new_tokens)
              return new_tokens["access_token"]
          
          return connection.access_token
      
      async def refresh_access_token(self, refresh_token: str) -> dict:
          response = await self.http_client.post(
              "https://login.microsoftonline.com/common/oauth2/v2.0/token",
              data={
                  "grant_type": "refresh_token",
                  "client_id": settings.AZURE_CLIENT_ID,
                  "client_secret": settings.AZURE_CLIENT_SECRET,
                  "refresh_token": refresh_token,
                  "scope": " ".join(self.scopes)
              }
          )
          return response.json()
  ```

DoD (Definition of Done):
  - [ ] TokenRefreshService implementado
  - [ ] Refresh proativo funcionando
  - [ ] Erros tratados com retry
  - [ ] Notificação para re-login quando necessário
  - [ ] Logs de auditoria de refresh

Criterios de Aceitacao:
  - [ ] Token renovado antes de expirar
  - [ ] Chamadas Graph usam token válido
  - [ ] Erro de refresh notifica usuário
  - [ ] Logs mostram refreshes realizados
```

---

### CARD INT-MSG-007: Multi-tenant Calendar
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [BACKEND] Multi-tenant Calendar Support
Tipo: Feature
Area: Full-Stack
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 8
Prioridade: Média
Epic: EPIC-INT-MVP
Status: 📋 Pendente Jira
Dependencias: INT-MSG-003, INT-MSG-006

Descricao: |
  Implementar suporte a múltiplas contas Microsoft por empresa,
  permitindo que diferentes recrutadores conectem seus calendários.

Historia de Usuario: |
  Como empresa, eu quero que cada recrutador conecte seu calendário
  para que entrevistas sejam agendadas no calendário correto.

Regras de Negocio:
  1. Cada usuário conecta sua própria conta Microsoft
  2. Tokens isolados por usuário
  3. Admin pode ver status de conexão de todos
  4. Fallback para calendário padrão se usuário não conectado
  5. Suporte a múltiplos tenants Azure (empresas diferentes)
  6. Seleção de calendário específico (se múltiplos)

Requisitos Tecnicos:
  Backend:
    - MultiTenantCalendarService
    - Seleção de usuário para operações de calendário
    - Admin endpoint para listar conexões
  Frontend:
    - Lista de usuários com status de conexão
    - Configuração de calendário padrão
  Dados:
    - microsoft_connections: company_id, user_id, tenant_id, calendar_id

Comportamento de API:
  Listar conexões (admin):
    GET /api/v1/company/microsoft-connections
    
    Response:
    ```json
    {
      "connections": [
        {
          "user_id": "uuid",
          "user_name": "João Silva",
          "email": "joao@company.com",
          "connected": true,
          "last_sync": "2026-01-22T10:00:00Z"
        },
        {
          "user_id": "uuid2",
          "user_name": "Maria Santos",
          "email": "maria@company.com",
          "connected": false,
          "last_sync": null
        }
      ],
      "default_calendar_user": "uuid"
    }

Arquivos de Referencia (Prototipo Replit):
  - microsoft_graph_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/microsoft_graph_service.py
  - graph_client.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/graph_client.py
  - calendar_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/calendar_service.py
  - scheduling_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/scheduling_service.py
    ```
  
  Configurar calendário padrão:
    PUT /api/v1/company/microsoft-connections/default
    
    Request:
    ```json
    {
      "user_id": "uuid"
    }
    ```

DoD (Definition of Done):
  - [ ] Múltiplas conexões por empresa
  - [ ] Isolamento de tokens
  - [ ] Admin pode ver conexões
  - [ ] Calendário padrão configurável
  - [ ] Testes multi-tenant

Criterios de Aceitacao:
  - [ ] Dois recrutadores conectados
  - [ ] Entrevista agendada no calendário correto
  - [ ] Admin vê status de todos
  - [ ] Fallback para padrão funciona
```

---

## LLM INTEGRATIONS - CARDS

---

### CARD INT-LLM-001: Cliente Anthropic Claude ⏸️ PÓS-MVP
**Épico:** É14 — Integrações MVP

> ⏸️ **ADIADO PARA PÓS-MVP** — Reunião de 06/02/2026. MVP usa exclusivamente Gemini. Claude só será implementado se cliente enterprise exigir.

```yaml
Titulo: [BACKEND] Cliente Anthropic Claude
Tipo: Feature
Area: Full-Stack
Sprint: Pós-MVP
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 5
Prioridade: Crítica
Epic: EPIC-INT-MVP
Status: ⏸️ Pós-MVP

Descricao: |
  Cliente Python para Anthropic Claude API a ser implementado
  via Replit AI Integrations. Usado para geração de texto,
  análise de CVs e conversas de triagem.

Historia de Usuario: |
  Como LIA, eu quero usar Claude para gerar respostas
  inteligentes e analisar perfis de candidatos.

Regras de Negocio:
  1. Modelo padrão: claude-3-5-sonnet
  2. Max tokens configurável por tipo de tarefa
  3. Temperature ajustável
  4. System prompt padronizado para LIA
  5. Retry automático em erros 429/500
  6. Logging de requests para auditoria

Requisitos Tecnicos:
  Backend:
    - AnthropicClient via Replit Integration
    - Wrapper LIAAnthropicService
  Dados:
    - llm_requests: model, tokens_in, tokens_out, cost, latency

Integracoes Externas:
  Anthropic Claude (via Replit):
    - SDK: anthropic (instalado via integration)
    - Modelos: claude-3-5-sonnet-20241022, claude-3-haiku-20240307
    - Autenticação: Gerenciada pelo Replit
    - Custo: ~$3/1M input tokens, ~$15/1M output tokens (Sonnet)
    - Docs: https://docs.anthropic.com/claude/reference

Status: ⏸️ Pós-MVP

DoD (Definition of Done):
  - [ ] Integration instalada
  - [ ] Client wrapper implementado
  - [ ] Testes básicos passando
  - [ ] Logging configurado

Criterios de Aceitacao:
  - [ ] Chamadas à API funcionando
  - [ ] Resposta em formato esperado
  - [ ] Erros tratados corretamente

Arquivos de Referencia (Prototipo Replit):
  - llm_router_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/llm.py
```

---

### CARD INT-LLM-002: Cliente Google Gemini
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [BACKEND] Cliente Google Gemini
Tipo: Feature
Area: Full-Stack
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 5
Prioridade: Crítica
Epic: EPIC-INT-MVP
Status: 📋 Pendente Jira

Descricao: |
  Cliente Python para Google Gemini API a ser implementado
  via Replit AI Integrations. Usado para busca semântica,
  embeddings e tarefas com grande contexto.

Historia de Usuario: |
  Como LIA, eu quero usar Gemini para busca semântica
  e processamento de documentos longos.

Regras de Negocio:
  1. Modelo padrão: gemini-1.5-pro
  2. Grande janela de contexto (1M tokens)
  3. Embeddings para busca semântica
  4. Suporte a multimodal (imagens de CV)
  5. Fallback para Claude em erros

Requisitos Tecnicos:
  Backend:
    - GeminiClient via Replit Integration
    - Wrapper LIAGeminiService
  Dados:
    - llm_requests: model, tokens_in, tokens_out, cost, latency

Integracoes Externas:
  Google Gemini (via Replit):
    - SDK: google-generativeai (instalado via integration)
    - Modelos: gemini-1.5-pro, gemini-1.5-flash
    - Autenticação: Gerenciada pelo Replit
    - Custo: Gratuito até 60 req/min, depois $0.075/1M input tokens
    - Docs: https://ai.google.dev/docs

Status: 📋 Pendente Jira e funcionando via Replit Integration

DoD (Definition of Done):
  - [ ] Integration instalada
  - [ ] Client wrapper implementado
  - [ ] Embeddings funcionando
  - [ ] Testes passando

Criterios de Aceitacao:
  - [ ] Chamadas à API funcionando
  - [ ] Embeddings gerados
  - [ ] Grande contexto suportado

Arquivos de Referencia (Prototipo Replit):
  - llm_router_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/llm.py
  - gemini_voice_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/gemini_voice_service.py
```

---

### CARD INT-LLM-003: Router de Modelos ⏸️ PÓS-MVP
**Épico:** É14 — Integrações MVP

> ⏸️ **ADIADO PARA PÓS-MVP** — Reunião de 06/02/2026. Router multi-modelo desnecessário sem Claude no MVP. Com Gemini-only, routing é direto.

```yaml
Titulo: [BACKEND] Router de Modelos LLM
Tipo: Feature
Area: Full-Stack
Sprint: Pós-MVP
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 8
Prioridade: Alta
Epic: EPIC-INT-MVP
Status: ⏸️ Pós-MVP
Dependencias: INT-LLM-001, INT-LLM-002

Descricao: |
  Implementar router inteligente que seleciona o modelo LLM
  ideal baseado no tipo de tarefa, custo e latência desejada.

Historia de Usuario: |
  Como sistema, eu quero usar o modelo mais adequado para cada tarefa
  para otimizar custo e qualidade das respostas.

Regras de Negocio:
  1. Mapeamento task_type → modelo recomendado
  2. Override manual por empresa (configuração)
  3. Consideração de custo/latência/qualidade
  4. Fallback automático se modelo indisponível
  5. A/B testing opcional entre modelos
  6. Logging de decisões para análise

Requisitos Tecnicos:
  Backend:
    - LLMRouter class
    - route(task_type, context_size) → ModelConfig
    - Configuração via arquivo/banco
  Dados:
    - llm_routing_config: task_type, primary_model, fallback_model, max_tokens, temperature

Mapeamento de Tarefas:
  ```yaml
  task_routing:
    job_description_generation:
      primary: claude-3-5-sonnet
      fallback: gemini-1.5-pro
      max_tokens: 2000
      temperature: 0.7
    
    cv_analysis:
      primary: gemini-1.5-pro  # grande contexto
      fallback: claude-3-5-sonnet
      max_tokens: 4000
      temperature: 0.3
    
    triagem_conversation:
      primary: claude-3-5-sonnet
      fallback: claude-3-haiku
      max_tokens: 500
      temperature: 0.8
    
    score_calculation:
      primary: claude-3-5-sonnet
      fallback: gemini-1.5-pro
      max_tokens: 1500
      temperature: 0.2
    
    semantic_search:
      primary: gemini-embedding
      fallback: null
    
    quick_response:
      primary: claude-3-haiku
      fallback: gemini-1.5-flash
      max_tokens: 200
      temperature: 0.5

Arquivos de Referencia (Prototipo Replit):
  - llm_router_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/llm.py
  ```

Comportamento de API:
  Roteamento interno (não exposto):
    ```python
    router = LLMRouter()
    model_config = router.route(
        task_type="cv_analysis",
        context_size=50000,  # tokens
        latency_requirement="normal"  # fast, normal, slow
    )
    # Returns: ModelConfig(model="gemini-1.5-pro", ...)
    ```
  
  Configuração por empresa:
    PUT /api/v1/company/llm-config
    
    Request:
    ```json
    {
      "task_overrides": {
        "triagem_conversation": {
          "primary": "claude-3-haiku",
          "reason": "custo reduzido"
        }
      }
    }
    ```

DoD (Definition of Done):
  - [ ] LLMRouter implementado
  - [ ] Mapeamento task→modelo
  - [ ] Override por empresa
  - [ ] Fallback automático
  - [ ] Testes de roteamento

Criterios de Aceitacao:
  - [ ] Task correta usa modelo correto
  - [ ] Fallback ativado em erro
  - [ ] Config empresa aplicada
  - [ ] Logs de decisão salvos
```

---

### CARD INT-LLM-004: Fallback entre Modelos ⏸️ PÓS-MVP
**Épico:** É14 — Integrações MVP

> ⏸️ **ADIADO PARA PÓS-MVP** — Reunião de 06/02/2026. Fallback desnecessário sem múltiplos modelos no MVP. Gemini-only simplifica.

```yaml
Titulo: [BACKEND] Fallback Automático entre Modelos LLM
Tipo: Feature
Area: Full-Stack
Sprint: Pós-MVP
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 5
Prioridade: Alta
Epic: EPIC-INT-MVP
Status: ⏸️ Pós-MVP
Dependencias: INT-LLM-003

Descricao: |
  Implementar fallback automático quando modelo primário falha,
  garantindo disponibilidade contínua do serviço de IA.

Historia de Usuario: |
  Como sistema, eu quero que falhas de um modelo sejam
  automaticamente tratadas usando modelo alternativo.

Regras de Negocio:
  1. Fallback em erros 429 (rate limit), 500, timeout
  2. Máximo 2 tentativas no primário antes de fallback
  3. Circuit breaker se modelo falhar muitas vezes
  4. Logging de todos os fallbacks
  5. Alertas se fallback frequente
  6. Métricas de sucesso/falha por modelo

Requisitos Tecnicos:
  Backend:
    - FallbackHandler decorator/wrapper
    - CircuitBreaker class
    - Retry com exponential backoff
  Dados:
    - llm_metrics: model, success_count, failure_count, last_failure

Codigo de Referencia:
  ```python
  from tenacity import retry, stop_after_attempt, wait_exponential
  
  class LLMFallbackHandler:
      def __init__(self, router: LLMRouter):
          self.router = router
          self.circuit_breakers: dict[str, CircuitBreaker] = {}
      
      async def call_with_fallback(
          self, 
          task_type: str, 
          prompt: str,
          **kwargs
      ) -> LLMResponse:
          config = self.router.route(task_type)
          
          try:
              if self.circuit_breakers.get(config.model, {}).is_open:
                  raise CircuitOpenError()
              
              return await self._call_model(config.model, prompt, **kwargs)
          
          except (RateLimitError, TimeoutError, CircuitOpenError) as e:
              logger.warning(f"Primary model failed: {e}, trying fallback")
              
              if config.fallback:
                  return await self._call_model(config.fallback, prompt, **kwargs)
              raise
      
      @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1))
      async def _call_model(self, model: str, prompt: str, **kwargs):
          # Call appropriate client based on model
          pass

Arquivos de Referencia (Prototipo Replit):
  - llm_router_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/llm.py
  - circuit_breaker.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/circuit_breaker.py
  ```

DoD (Definition of Done):
  - [ ] FallbackHandler implementado
  - [ ] Circuit breaker funcionando
  - [ ] Retry com backoff
  - [ ] Métricas de fallback
  - [ ] Alertas configurados

Criterios de Aceitacao:
  - [ ] Erro 429 aciona fallback
  - [ ] Circuit breaker abre após 5 falhas
  - [ ] Chamada bem-sucedida após fallback
  - [ ] Métricas mostram taxa de fallback
```

---

### CARD INT-LLM-005: Gestão de Prompts
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [BACKEND] Gestão de Prompts (Templates)
Tipo: Feature
Area: Full-Stack
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 8
Prioridade: Alta
Epic: EPIC-INT-MVP
Status: 📋 Pendente Jira
Dependencias: INT-LLM-001, INT-LLM-002

Descricao: |
  Implementar sistema de templates de prompts versionados,
  permitindo gerenciar, testar e atualizar prompts da LIA.

Historia de Usuario: |
  Como desenvolvedor, eu quero gerenciar prompts de forma centralizada
  para iterar rapidamente sem alterar código.

Regras de Negocio:
  1. Templates versionados (git-like)
  2. Variáveis dinâmicas {{variable}}
  3. System prompt + user prompt
  4. Prompts por tarefa e idioma
  5. A/B testing de prompts
  6. Métricas de qualidade por prompt
  7. Tabela de consumo agrupada por company_id

Requisitos Tecnicos:
  Backend:
    - PromptTemplateService class
    - render(template_id, variables)
    - CRUD de templates
    - Versionamento
    - Dashboard mostra consumo por empresa (tokens, custo, requests)
  Dados:
    - prompt_templates: id, name, version, system_prompt, user_prompt, variables_schema
    - prompt_versions: template_id, version, content, created_at

Comportamento de API:
  Listar templates:
    GET /api/v1/prompts
    
    Response:
    ```json
    {
      "templates": [
        {
          "id": "triagem_inicio",
          "name": "Início da Triagem",
          "version": "1.2.0",
          "variables": ["candidato_nome", "vaga_titulo", "empresa_nome"]
        }
      ]
    }

Arquivos de Referencia (Prototipo Replit):
  - llm_router_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/llm.py
    ```
  
  Renderizar prompt:
    POST /api/v1/prompts/render
    
    Request:
    ```json
    {
      "template_id": "triagem_inicio",
      "variables": {
        "candidato_nome": "Maria Silva",
        "vaga_titulo": "Dev Python",
        "empresa_nome": "WeDo Talent"
      }
    }
    ```
    
    Response:
    ```json
    {
      "system_prompt": "Você é a LIA, assistente de RH da WeDo Talent...",
      "user_prompt": "Inicie a triagem com Maria Silva para a vaga de Dev Python..."
    }
    ```

Templates Iniciais:
  ```yaml
  - id: lia_system
    name: LIA System Prompt
    system_prompt: |
      Você é a LIA (Layered Intelligence Assistant), uma assistente de RH 
      inteligente e empática. Sua função é conduzir triagens de candidatos
      de forma natural e profissional, avaliando fit cultural e competências.
      
      Empresa: {{empresa_nome}}
      Vaga: {{vaga_titulo}}
      
      Diretrizes:
      - Seja cordial mas profissional
      - Faça perguntas abertas
      - Evite perguntas discriminatórias
      - Colete informações relevantes para a vaga
  
  - id: triagem_pergunta
    name: Pergunta de Triagem
    user_prompt: |
      Faça a próxima pergunta ao candidato {{candidato_nome}}.
      
      Contexto da conversa até agora:
      {{historico_conversa}}
      
      Próxima pergunta planejada:
      {{pergunta_atual}}
      
      Adapte a pergunta ao tom da conversa.
  ```

DoD (Definition of Done):
  - [ ] PromptTemplateService implementado
  - [ ] CRUD de templates
  - [ ] Versionamento funcionando
  - [ ] Renderização com variáveis
  - [ ] Templates iniciais criados

Criterios de Aceitacao:
  - [ ] Template criado e versionado
  - [ ] Variáveis substituídas corretamente
  - [ ] Versão anterior recuperável
  - [ ] A/B test configurável
```

---

### CARD INT-LLM-006: Cache de Respostas
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [BACKEND] Cache de Respostas LLM (Redis)
Tipo: Feature
Area: Full-Stack
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 5
Prioridade: Média
Epic: EPIC-INT-MVP
Status: 📋 Pendente Jira
Dependencias: INT-LLM-003

Descricao: |
  Implementar cache Redis para respostas LLM idênticas,
  reduzindo custo e latência em operações repetitivas.

Historia de Usuario: |
  Como sistema, eu quero cachear respostas LLM
  para reduzir custos e melhorar performance.

Regras de Negocio:
  1. Cache baseado em hash do prompt
  2. TTL configurável por tipo de tarefa
  3. Invalidação manual possível
  4. Não cachear conversas dinâmicas
  5. Métricas de hit/miss rate
  6. Limite de tamanho do cache
  7. Cachear perguntas E respostas WSI (não só prompts). Cache de perguntas geradas por job_id + block_id.

Requisitos Tecnicos:
  Backend:
    - LLMCacheService class
    - get_or_call(prompt_hash, ttl, call_func)
    - Redis como backend
  Dados:
    - Redis keys: llm:cache:{prompt_hash}

Configuração de TTL:
  ```yaml
  cache_ttl:
    job_description_generation: 86400  # 24h
    cv_analysis: 3600  # 1h (CV pode ser atualizado)
    score_calculation: 1800  # 30min
    semantic_search: 86400  # 24h
    triagem_conversation: 0  # não cachear

Arquivos de Referencia (Prototipo Replit):
  - response_cache_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/response_cache_service.py
  - ai_cache_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/ai_cache_service.py
  - cache_manager_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/cache_manager_service.py
  ```

Codigo de Referencia:
  ```python
  import hashlib
  import json
  
  class LLMCacheService:
      def __init__(self, redis: Redis):
          self.redis = redis
      
      def _hash_prompt(self, prompt: str, model: str) -> str:
          content = f"{model}:{prompt}"
          return hashlib.sha256(content.encode()).hexdigest()
      
      async def get_or_call(
          self, 
          prompt: str, 
          model: str,
          ttl: int,
          call_func: Callable
      ) -> str:
          if ttl == 0:
              return await call_func()
          
          cache_key = f"llm:cache:{self._hash_prompt(prompt, model)}"
          cached = await self.redis.get(cache_key)
          
          if cached:
              logger.info(f"Cache HIT for {cache_key[:20]}")
              return json.loads(cached)
          
          result = await call_func()
          await self.redis.setex(cache_key, ttl, json.dumps(result))
          logger.info(f"Cache MISS, stored for {ttl}s")
          
          return result
  ```

DoD (Definition of Done):
  - [ ] LLMCacheService implementado
  - [ ] TTL por tipo de tarefa
  - [ ] Hit/miss logging
  - [ ] Métricas de cache
  - [ ] Invalidação manual

Criterios de Aceitacao:
  - [ ] Prompt idêntico retorna do cache
  - [ ] TTL respeitado
  - [ ] Conversas não cacheadas
  - [ ] Hit rate visível no dashboard
```

---

### CARD INT-LLM-007: Monitoramento de Custos
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [BACKEND] Monitoramento de Custos LLM
Tipo: Feature
Area: Full-Stack
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 5
Prioridade: Alta
Epic: EPIC-INT-MVP
Status: 📋 Pendente Jira
Dependencias: INT-LLM-003

Descricao: |
  Implementar tracking de custos de uso de LLMs por empresa,
  usuário e tarefa, com alertas de budget.

Historia de Usuario: |
  Como admin, eu quero monitorar custos de IA
  para controlar gastos e otimizar uso.

Regras de Negocio:
  1. Calcular custo por request (input + output tokens)
  2. Agregar por empresa, usuário, tarefa
  3. Budget mensal por empresa
  4. Alertas em 50%, 80%, 100% do budget
  5. Dashboard com gráficos de custo
  6. Exportar relatório de custos
  7. Dashboard de custos agrupado por empresa com alertas. Visão consolidada no admin mostrando consumo por company_id com breakdown por modelo e task_type.

Requisitos Tecnicos:
  Backend:
    - LLMCostTracker class
    - track_request(model, tokens_in, tokens_out, company_id)
    - get_costs(company_id, period)
  Dados:
    - llm_usage: id, company_id, user_id, model, tokens_in, tokens_out, cost_usd, task_type, created_at
    - company_llm_budgets: company_id, monthly_budget_usd, alert_threshold_percent

Preços por Modelo (USD):
  ```yaml
  pricing:
    claude-3-5-sonnet:
      input: 0.003  # per 1K tokens
      output: 0.015
    claude-3-haiku:
      input: 0.00025
      output: 0.00125
    gemini-1.5-pro:
      input: 0.000075
      output: 0.0003
    gemini-1.5-flash:
      input: 0.000015
      output: 0.00006

Arquivos de Referencia (Prototipo Replit):
  - token_tracking_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/token_tracking_service.py
  - ConsumptionChart.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/admin/ai-consumption/ConsumptionChart.tsx
  - ConsumptionSummaryCard.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/admin/ai-consumption/ConsumptionSummaryCard.tsx
  - AgentBreakdown.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/admin/ai-consumption/AgentBreakdown.tsx
  ```

Comportamento de API:
  Dashboard de custos:
    GET /api/v1/admin/llm-costs?period=month
    
    Response:
    ```json
    {
      "total_cost_usd": 245.67,
      "budget_usd": 500.00,
      "budget_used_percent": 49.1,
      "by_model": {
        "claude-3-5-sonnet": 180.00,
        "gemini-1.5-pro": 50.00,
        "claude-3-haiku": 15.67
      },
      "by_task": {
        "triagem_conversation": 120.00,
        "cv_analysis": 80.00,
        "job_description": 45.67
      },
      "daily_trend": [
        {"date": "2026-01-20", "cost": 25.00},
        {"date": "2026-01-21", "cost": 30.00}
      ]
    }
    ```

DoD (Definition of Done):
  - [ ] LLMCostTracker implementado
  - [ ] Custos calculados por request
  - [ ] Dashboard de custos
  - [ ] Alertas de budget
  - [ ] Relatório exportável

Criterios de Aceitacao:
  - [ ] Custo correto por modelo
  - [ ] Agregação por empresa
  - [ ] Alerta enviado em 80%
  - [ ] Gráfico de tendência
```

---

### CARD INT-LLM-008: Rate Limiting LLM
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [BACKEND] Rate Limiting para LLM
Tipo: Feature
Area: Full-Stack
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 5
Prioridade: Alta
Epic: EPIC-INT-MVP
Status: 📋 Pendente Jira
Dependencias: INT-LLM-003

Descricao: |
  Implementar rate limiting para chamadas LLM por empresa,
  evitando abuse e garantindo fair usage entre tenants.

Historia de Usuario: |
  Como sistema, eu quero limitar chamadas LLM por empresa
  para garantir recursos para todos os clientes.

Regras de Negocio:
  1. Limite por minuto por empresa
  2. Limite por dia por empresa
  3. Diferentes limites por plano (starter, pro, enterprise)
  4. Queue para requests excedentes
  5. Header com limite restante
  6. 429 Too Many Requests quando excedido

Requisitos Tecnicos:
  Backend:
    - LLMRateLimiter class
    - Sliding window counter (Redis)
    - Middleware para checar limite
  Dados:
    - Redis keys: llm:rate:{company_id}:{window}

Limites por Plano:
  ```yaml
  rate_limits:
    starter:
      requests_per_minute: 20
      requests_per_day: 500
      tokens_per_day: 100000
    
    professional:
      requests_per_minute: 50
      requests_per_day: 2000
      tokens_per_day: 500000
    
    enterprise:
      requests_per_minute: 200
      requests_per_day: 10000
      tokens_per_day: 2000000

Arquivos de Referencia (Prototipo Replit):
  - llm_router_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/llm.py
  - circuit_breaker.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/circuit_breaker.py
  ```

Comportamento de API:
  Response Headers (todas as chamadas LLM):
    ```
    X-RateLimit-Limit: 50
    X-RateLimit-Remaining: 45
    X-RateLimit-Reset: 1706000000
    ```
  
  Quando excedido:
    Status: 429 Too Many Requests
    ```json
    {
      "error": "rate_limit_exceeded",
      "message": "Limite de 50 requests/minuto excedido",
      "retry_after": 30
    }
    ```

DoD (Definition of Done):
  - [ ] LLMRateLimiter implementado
  - [ ] Limites por plano
  - [ ] Headers de rate limit
  - [ ] 429 quando excedido
  - [ ] Dashboard de uso

Criterios de Aceitacao:
  - [ ] Limite respeitado por empresa
  - [ ] Headers corretos em responses
  - [ ] 429 após exceder
  - [ ] Reset funciona corretamente
```

---

### CARD INT-LLM-009: Logging de Conversas
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [BACKEND] Logging de Conversas LLM (Audit)
Tipo: Feature
Area: Full-Stack
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 8
Prioridade: Alta
Epic: EPIC-INT-MVP
Status: 📋 Pendente Jira
Dependencias: INT-LLM-001, INT-LLM-002

Descricao: |
  Implementar logging completo de todas as interações com LLMs
  para auditoria, debug e melhoria contínua.

Historia de Usuario: |
  Como admin, eu quero ver histórico de conversas LLM
  para auditar decisões e melhorar prompts.

Regras de Negocio:
  1. Logar: prompt, response, model, tokens, latency
  2. Associar a candidato/vaga quando aplicável
  3. Retenção configurável (default 90 dias)
  4. LGPD: possibilidade de anonimizar
  5. Exportar para análise
  6. Não logar dados sensíveis (mask PII)

Requisitos Tecnicos:
  Backend:
    - LLMConversationLogger class
    - log(request, response, metadata)
    - Busca por candidato/vaga
    - PII masking
  Dados:
    - llm_conversations: id, company_id, user_id, candidate_id, job_id, 
      model, prompt_hash, prompt (encrypted), response (encrypted),
      tokens_in, tokens_out, latency_ms, created_at

Comportamento de API:
  Listar conversas (admin):
    GET /api/v1/admin/llm-conversations?candidate_id={id}&limit=50
    
    Response:
    ```json
    {
      "conversations": [
        {
          "id": "uuid",
          "created_at": "2026-01-22T10:00:00Z",
          "model": "claude-3-5-sonnet",
          "task_type": "triagem_conversation",
          "candidate_name": "Maria Silva",
          "job_title": "Dev Python",
          "prompt_preview": "Faça a próxima pergunta...",
          "response_preview": "Maria, conte-me sobre sua experiência...",
          "tokens_in": 500,
          "tokens_out": 150,
          "latency_ms": 1200
        }
      ],
      "total": 25,
      "has_more": false
    }

Arquivos de Referencia (Prototipo Replit):
  - conversation_memory.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/conversation_memory.py
  - memory_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/memory_service.py
  - chat.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/chat.py
    ```
  
  Ver conversa completa:
    GET /api/v1/admin/llm-conversations/{id}
    
    Response:
    ```json
    {
      "id": "uuid",
      "full_prompt": "Sistema: Você é a LIA...\nUsuário: Faça a próxima pergunta...",
      "full_response": "Maria, conte-me sobre sua experiência com Python...",
      "metadata": {
        "candidate_id": "uuid",
        "job_id": "uuid",
        "conversation_turn": 3
      }
    }
    ```

DoD (Definition of Done):
  - [ ] LLMConversationLogger implementado
  - [ ] Dados encriptados no banco
  - [ ] PII masking funcionando
  - [ ] Busca por candidato/vaga
  - [ ] Retenção automática

Criterios de Aceitacao:
  - [ ] Todas as conversas logadas
  - [ ] Dados encriptados em repouso
  - [ ] PII removido quando solicitado
  - [ ] Exportação funciona
```

---

## WORKOS AUTH - CARDS

---

### CARD INT-WOS-001: Configurar WorkOS Account
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [INTEGRAÇÃO] Configurar WorkOS Account
Tipo: Configuração SaaS
Area: Integração
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 3
Prioridade: Crítica
Epic: EPIC-INT-MVP
Status: 🔗 Configuração

Descricao: |
  Criar e configurar conta WorkOS para autenticação enterprise
  com SSO, Directory Sync e User Management.

Historia de Usuario: |
  Como administrador, eu quero configurar WorkOS
  para oferecer SSO enterprise aos clientes.

Regras de Negocio:
  1. Conta WorkOS ativa
  2. Environment configurado (sandbox/production)
  3. Redirect URIs para OAuth
  4. Webhook endpoint registrado
  5. Client ID e Secret armazenados

Requisitos Tecnicos:
  Backend:
    - WORKOS_CLIENT_ID, WORKOS_API_KEY
    - Webhook endpoint configurado
  Dados:
    - Secrets gerenciados no Replit

Integracoes Externas:
  WorkOS:
    - Console: https://dashboard.workos.com
    - SDK: workos-python
    - Funcionalidades:
      - SSO (SAML/OIDC)
      - Directory Sync (SCIM)
      - User Management
      - Admin Portal
      - MFA
    - Custo: Gratuito até 1M MAU, depois $0.05/MAU
    - Docs: https://workos.com/docs

Passo a Passo:
  1. Criar conta em https://workos.com
  2. Dashboard → Organizations → Create (para cada cliente enterprise)
  3. Configuration → Redirect URIs:
     - Dev: http://localhost:5000/api/auth/workos/callback
     - Prod: https://[domain]/api/auth/workos/callback
  4. Configuration → Webhooks:
     - URL: https://[domain]/api/webhooks/workos
     - Events: user.*, dsync.*, sso.*
  5. Copiar: Client ID, API Key
  6. Salvar secrets no Replit

DoD (Definition of Done):
  - [ ] Conta WorkOS criada
  - [ ] Redirect URIs configurados
  - [ ] Webhook registrado
  - [ ] Secrets salvos
  - [ ] Teste de conexão

Criterios de Aceitacao:
  - [ ] Dashboard acessível
  - [ ] API Key válida
  - [ ] Webhook recebe eventos

Arquivos de Referencia (Prototipo Replit):
  - workos.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/workos.ts
  - workos-links.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/workos-links.ts
  - workos.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/workos.py
```

> ⚠️ **DISCLAIMER: CARD RELACIONADO AO MENU DE CONFIGURAÇÕES**
> Este card faz parte do sistema de configurações da plataforma (Settings Menu).
> Consulte também: `docs/configuracoes-admin-cards-jira.md` para cards administrativos complementares.


---

### CARD INT-WOS-002: SSO SAML/OIDC
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [BACKEND] SSO SAML/OIDC com WorkOS
Tipo: Feature
Area: Full-Stack
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 8
Prioridade: Alta
Epic: EPIC-INT-MVP
Status: 📋 Pendente Jira
Dependencias: INT-WOS-001

Descricao: |
  Implementar Single Sign-On enterprise usando WorkOS,
  suportando SAML 2.0 e OIDC para clientes corporativos.

Historia de Usuario: |
  Como usuário enterprise, eu quero fazer login com SSO da minha empresa
  para usar credenciais corporativas.

Regras de Negocio:
  1. SSO por domínio de email (ex: @empresa.com → SSO)
  2. Suporte a SAML 2.0 e OIDC
  3. Just-in-time provisioning de usuários
  4. Mapeamento de atributos (nome, email, role)
  5. Fallback para login normal se SSO não configurado
  6. Login iniciado pelo IdP suportado

Requisitos Tecnicos:
  Backend:
    - GET /api/v1/auth/sso/authorize?email={email}
    - GET /api/v1/auth/sso/callback
    - WorkOSSSOService class
  Frontend:
    - Input de email para detectar SSO
    - Botão "Continuar com SSO"
  Dados:
    - sso_connections: company_id, connection_id, provider, domain

Comportamento de API:
  Iniciar SSO:
    GET /api/v1/auth/sso/authorize?email=user@enterprise.com
    
    Response: Redirect to WorkOS/IdP
  
  Callback:
    GET /api/v1/auth/sso/callback?code={code}
    
    Backend processa:
    1. Troca code por profile
    2. Cria/atualiza usuário
    3. Gera JWT
    4. Redirect para app

Codigo de Referencia:
  ```python
  from workos import WorkOS
  
  workos = WorkOS(settings.WORKOS_API_KEY)
  
  class WorkOSSSOService:
      async def get_authorization_url(self, email: str) -> str:
          connection = await self._get_connection_for_email(email)
          
          return workos.sso.get_authorization_url(
              connection=connection.id,
              redirect_uri=settings.WORKOS_REDIRECT_URI,
              state=self._generate_state()
          )
      
      async def handle_callback(self, code: str) -> User:
          profile = workos.sso.get_profile_and_token(code)
          
          user = await self._find_or_create_user(
              email=profile.email,
              name=profile.first_name + " " + profile.last_name,
              company_id=profile.organization_id
          )
          
          return user

Arquivos de Referencia (Prototipo Replit):
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/auth/workos/sso/route.ts
  - route.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/api/auth/workos/callback/route.ts
  - workos.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/workos.ts
  ```

DoD (Definition of Done):
  - [ ] SSO flow completo
  - [ ] SAML e OIDC suportados
  - [ ] JIT provisioning
  - [ ] Mapeamento de atributos
  - [ ] Testes de integração

Criterios de Aceitacao:
  - [ ] Login SSO funciona
  - [ ] Usuário criado automaticamente
  - [ ] Atributos mapeados
  - [ ] Fallback para login normal
```

---

### CARD INT-WOS-003: Directory Sync SCIM
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [BACKEND] Directory Sync SCIM com WorkOS
Tipo: Feature
Area: Full-Stack
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 8
Prioridade: Média
Epic: EPIC-INT-MVP
Status: 📋 Pendente Jira
Dependencias: INT-WOS-002

Descricao: |
  Implementar sincronização de diretório (SCIM) via WorkOS
  para provisionar/desprovisionar usuários automaticamente.

Historia de Usuario: |
  Como admin enterprise, eu quero que usuários sejam sincronizados
  do meu diretório corporativo automaticamente.

Regras de Negocio:
  1. Sync automático de usuários do IdP
  2. Criar usuário quando adicionado ao grupo
  3. Desativar usuário quando removido
  4. Atualizar atributos quando alterados
  5. Suportar grupos para mapeamento de roles
  6. Webhook para mudanças em tempo real

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/webhooks/workos (eventos dsync.*)
    - DirectorySyncService class
    - Processamento assíncrono de eventos
  Dados:
    - directory_users: workos_id, email, name, status, synced_at
    - directory_groups: workos_id, name, role_mapping

Comportamento de API:
  Webhook recebido:
    POST /api/v1/webhooks/workos
    
    Evento user.created:
    ```json
    {
      "event": "dsync.user.created",
      "data": {
        "id": "user_xxx",
        "first_name": "Maria",
        "last_name": "Silva",
        "email": "maria@enterprise.com",
        "groups": [{"id": "group_xxx", "name": "Recruiters"}],
        "directory_id": "dir_xxx"
      }
    }

Arquivos de Referencia (Prototipo Replit):
  - use-scim-config.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/use-scim-config.ts
  - workos_provisioning_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/workos_provisioning_service.py
  - workos.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/workos.py
    ```
    
    Ação: Criar usuário com role baseada no grupo

DoD (Definition of Done):
  - [ ] Webhook de SCIM
  - [ ] Criar usuário em user.created
  - [ ] Desativar em user.deleted
  - [ ] Atualizar em user.updated
  - [ ] Mapeamento de grupos

Criterios de Aceitacao:
  - [ ] Usuário criado via sync
  - [ ] Usuário desativado via sync
  - [ ] Grupos mapeados para roles
  - [ ] Sync em tempo real
```

---

### CARD INT-WOS-004: MFA Enforcement
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [BACKEND] MFA Enforcement com WorkOS
Tipo: Feature
Area: Full-Stack
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 5
Prioridade: Alta
Epic: EPIC-INT-MVP
Status: 📋 Pendente Jira
Dependencias: INT-WOS-002

Descricao: |
  Implementar Multi-Factor Authentication obrigatório
  para usuários admin e opcionalmente para todos.

Historia de Usuario: |
  Como admin, eu quero exigir MFA para usuários
  para aumentar a segurança da plataforma.

Regras de Negocio:
  1. MFA obrigatório para admins
  2. MFA opcional para usuários regulares
  3. Suporte a TOTP (authenticator apps)
  4. Códigos de backup
  5. Política configurável por empresa
  6. Reminder para configurar MFA

Requisitos Tecnicos:
  Backend:
    - MFAEnrollmentService class
    - POST /api/v1/auth/mfa/enroll
    - POST /api/v1/auth/mfa/verify
    - Middleware para verificar MFA
  Frontend:
    - Tela de configuração MFA
    - QR code para TOTP
    - Input de código de verificação
  Dados:
    - user_mfa: user_id, totp_secret (encrypted), backup_codes, enabled_at

Comportamento de API:
  Iniciar enrollment:
    POST /api/v1/auth/mfa/enroll
    
    Response:
    ```json
    {
      "totp_uri": "otpauth://totp/LIA:user@email.com?secret=XXX&issuer=LIA",
      "qr_code_base64": "data:image/png;base64,...",
      "backup_codes": ["123456", "234567", ...]
    }

Arquivos de Referencia (Prototipo Replit):
  - workos.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/workos.ts
  - auth-context.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/auth-context.tsx
    ```
  
  Verificar código:
    POST /api/v1/auth/mfa/verify
    
    Request:
    ```json
    {
      "code": "123456"
    }
    ```
    
    Response:
    ```json
    {
      "verified": true,
      "mfa_enabled": true
    }
    ```

DoD (Definition of Done):
  - [ ] TOTP enrollment
  - [ ] Verificação de código
  - [ ] Backup codes
  - [ ] Política por empresa
  - [ ] UI de configuração

Criterios de Aceitacao:
  - [ ] QR code escaneável
  - [ ] Código válido aceito
  - [ ] Backup code funciona
  - [ ] Admin obrigado a ter MFA
```

---

### CARD INT-WOS-005: User Management SDK
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [BACKEND] User Management com WorkOS SDK
Tipo: Feature
Area: Full-Stack
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 8
Prioridade: Alta
Epic: EPIC-INT-MVP
Status: 📋 Pendente Jira
Dependencias: INT-WOS-001

Descricao: |
  Implementar gestão de usuários usando WorkOS User Management
  para login, registro e gerenciamento de perfis.

Historia de Usuario: |
  Como usuário, eu quero me registrar e fazer login
  usando email/senha ou autenticação social.

Regras de Negocio:
  1. Registro com email/senha
  2. Login com email/senha
  3. Magic link (passwordless)
  4. Reset de senha
  5. Verificação de email
  6. Perfil editável

Requisitos Tecnicos:
  Backend:
    - WorkOSUserService class
    - POST /api/v1/auth/register
    - POST /api/v1/auth/login
    - POST /api/v1/auth/magic-link
    - POST /api/v1/auth/reset-password
  Frontend:
    - Tela de registro
    - Tela de login
    - Tela de reset senha
  Dados:
    - Usuários gerenciados no WorkOS (source of truth)
    - Local: user_profiles (dados adicionais)

Comportamento de API:
  Registro:
    POST /api/v1/auth/register
    
    Request:
    ```json
    {
      "email": "user@email.com",
      "password": "SecurePassword123!",
      "first_name": "Maria",
      "last_name": "Silva"
    }

Arquivos de Referencia (Prototipo Replit):
  - workos.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/workos.ts
  - workos-session.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/lib/workos-session.ts
  - workos.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/workos.py
    ```
    
    Response:
    ```json
    {
      "user_id": "user_xxx",
      "email_verification_required": true
    }
    ```
  
  Login:
    POST /api/v1/auth/login
    
    Request:
    ```json
    {
      "email": "user@email.com",
      "password": "SecurePassword123!"
    }
    ```
    
    Response:
    ```json
    {
      "access_token": "eyJ...",
      "refresh_token": "...",
      "user": {
        "id": "user_xxx",
        "email": "user@email.com",
        "name": "Maria Silva"
      }
    }
    ```

DoD (Definition of Done):
  - [ ] Registro funcionando
  - [ ] Login funcionando
  - [ ] Magic link opcional
  - [ ] Reset de senha
  - [ ] Verificação de email

Criterios de Aceitacao:
  - [ ] Usuário registrado no WorkOS
  - [ ] Login retorna tokens
  - [ ] Email de verificação enviado
  - [ ] Reset senha funciona

Nota: "⚠️ Avaliar necessidade — pode não ser necessário se plataforma é exclusivamente web (sem app mobile). WorkOS User Management SDK é mais relevante para apps com fluxos nativos. Reunião 06/02/2026."
```

---

### CARD INT-WOS-006: Webhook de Eventos
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [BACKEND] Webhook de Eventos WorkOS
Tipo: Feature
Area: Full-Stack
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 5
Prioridade: Alta
Epic: EPIC-INT-MVP
Status: 📋 Pendente Jira
Dependencias: INT-WOS-001

Descricao: |
  Implementar endpoint para receber webhooks do WorkOS
  sobre eventos de usuários, SSO e directory sync.

Historia de Usuario: |
  Como sistema, eu quero receber eventos do WorkOS
  para manter dados sincronizados em tempo real.

Regras de Negocio:
  1. Validar signature do WorkOS
  2. Processar eventos de forma assíncrona
  3. Idempotência (não processar duplicados)
  4. Retry automático se processamento falhar
  5. Logging de todos os eventos

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/webhooks/workos
    - Validação de X-WorkOS-Signature
    - Background processing
  Dados:
    - webhook_events: id, event_type, payload, processed_at, status

Eventos Tratados:
  ```yaml
  events:
    user.created: Criar usuário local
    user.updated: Atualizar perfil
    user.deleted: Desativar usuário
    session.created: Log de login
    dsync.user.created: Provisionar via SCIM
    dsync.user.updated: Atualizar via SCIM
    dsync.user.deleted: Desprovisionar
    dsync.group.created: Criar grupo/role
    connection.activated: SSO pronto
    connection.deactivated: SSO desativado

Arquivos de Referencia (Prototipo Replit):
  - webhooks.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/webhooks.py
  - workos.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/workos.py
  ```

Comportamento de API:
  Webhook:
    POST /api/v1/webhooks/workos
    
    Headers:
    - X-WorkOS-Signature: sha256=xxx
    
    Body:
    ```json
    {
      "event": "user.created",
      "data": {
        "id": "user_xxx",
        "email": "user@email.com",
        "first_name": "Maria"
      },
      "created_at": "2026-01-22T10:00:00Z"
    }
    ```
    
    Response: 200 OK

DoD (Definition of Done):
  - [ ] Webhook endpoint
  - [ ] Validação de signature
  - [ ] Handlers por evento
  - [ ] Background processing
  - [ ] Logging de eventos

Criterios de Aceitacao:
  - [ ] Signature válida aceita
  - [ ] Signature inválida rejeitada
  - [ ] Eventos processados
  - [ ] Duplicados ignorados
```

---

### CARD INT-WOS-007: Admin Portal
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [FRONTEND] Admin Portal WorkOS
Tipo: Feature
Area: Full-Stack
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 8
Prioridade: Média
Epic: EPIC-INT-MVP
Status: 📋 Pendente Jira
Dependencias: INT-WOS-002, INT-WOS-003

Descricao: |
  Implementar painel administrativo para clientes enterprise
  configurarem SSO e Directory Sync usando WorkOS Admin Portal.

Historia de Usuario: |
  Como admin de empresa cliente, eu quero configurar SSO
  sem precisar de suporte técnico.

Regras de Negocio:
  1. Self-service para configurar SSO
  2. Self-service para Directory Sync
  3. Link temporário para configuração
  4. Status de conexão visível
  5. Logs de sincronização
  6. Suporte a múltiplos IdPs

Requisitos Tecnicos:
  Backend:
    - POST /api/v1/admin/sso/portal-link
    - GET /api/v1/admin/sso/status
    - WorkOSAdminPortalService
  Frontend:
    - Seção SSO em Configurações
    - Botão "Configurar SSO"
    - Status de conexão
  Dados:
    - organization_connections: org_id, connection_type, status, configured_at

Comportamento de API:
  Gerar link do Admin Portal:
    POST /api/v1/admin/sso/portal-link
    
    Response:
    ```json
    {
      "link": "https://id.workos.com/portal/launch?token=xxx",
      "expires_at": "2026-01-22T11:00:00Z"
    }

Arquivos de Referencia (Prototipo Replit):
  - workos-admin-portal.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/admin/workos-admin-portal.tsx
  - workos-link-card.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/admin/workos-link-card.tsx
  - use-workos-metrics.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/use-workos-metrics.ts
    ```
    
    Nota: Link expira em 1 hora
  
  Status de conexão:
    GET /api/v1/admin/sso/status
    
    Response:
    ```json
    {
      "sso": {
        "configured": true,
        "provider": "Okta",
        "domain": "enterprise.com",
        "last_login": "2026-01-22T09:00:00Z"
      },
      "directory_sync": {
        "configured": true,
        "provider": "Azure AD",
        "users_synced": 150,
        "last_sync": "2026-01-22T08:00:00Z"
      }
    }
    ```

Design & Componentes:
  Componentes:
    - SSOConfigCard - card com status e botão configurar
    - DirectorySyncCard - status de sync
    - ConnectionStatusBadge - badge verde/vermelho
  Layout:
    - Seção em /configuracoes/empresa/sso
    - Cards lado a lado em desktop

DoD (Definition of Done):
  - [ ] Portal link generation
  - [ ] Status de conexão
  - [ ] UI de configuração
  - [ ] Logs de sync visíveis
  - [ ] Documentação para clientes

Criterios de Aceitacao:
  - [ ] Link abre Admin Portal
  - [ ] SSO configurável pelo cliente
  - [ ] Status atualizado após config
  - [ ] Directory Sync visível
```

---

### CARD INT-APY-001: Configurar Apify Account
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [INTEGRAÇÃO] Configurar Apify Account
Tipo: Integração
Area: Integração
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 3
Prioridade: Alta
Epic: EPIC-INT-MVP
Status: 📋 Pendente Jira
Dependencias: Nenhuma

Descricao: |
  Setup inicial da conta Apify para integração com actors de
  scraping do LinkedIn. Configuração de API key, webhooks e
  limites de uso.

Historia de Usuario: |
  Como administrador, eu quero configurar a integração com Apify
  para habilitar sourcing automatizado de candidatos.

Regras de Negocio:
  1. Conta Apify com plano adequado ao volume
  2. API key armazenada como secret
  3. Webhooks configurados para notificação de conclusão
  4. Monitoramento de uso e custos
  5. Limites de requisições respeitados
  6. Fallback em caso de indisponibilidade

Requisitos Tecnicos:
  Backend:
    - ApifyService base
    - Secret: APIFY_API_KEY
    - Webhook endpoint: POST /api/webhooks/apify
  Configuração:
    - Rate limiting por conta
    - Retry logic com backoff
  Monitoramento:
    - Logs de chamadas
    - Alertas de quota

Integracoes Externas:
  Apify: Platform API, Actor API

DoD (Definition of Done):
  - [ ] Conta Apify configurada
  - [ ] API key em secrets
  - [ ] Webhook funcionando
  - [ ] Testes de conectividade

Criterios de Aceitacao:
  - [ ] API key válida e funcional
  - [ ] Webhook recebe notificações
  - [ ] Logs de uso implementados

Arquivos de Referencia (Prototipo Replit):
  - apify_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/apify_service.py
  - apify_mcp_client.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/apify_mcp_client.py
```

---

### CARD INT-APY-002: LinkedIn Scraper Actor
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [BACKEND] LinkedIn Scraper Actor
Tipo: Backend
Area: Backend
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 8
Prioridade: Alta
Epic: EPIC-INT-MVP
Status: 📋 Pendente Jira
Dependencias: INT-APY-001

Descricao: |
  Implementar integração com actor Apify para busca de perfis
  no LinkedIn. O actor busca candidatos com base em critérios
  como cargo, localização, skills e empresa.

Historia de Usuario: |
  Como recrutador, eu quero que a LIA busque candidatos no LinkedIn
  automaticamente com base nos requisitos da vaga.

Regras de Negocio:
  1. Busca por título, localização, empresa, skills
  2. Limite de resultados por busca configurável
  3. Deduplicação de candidatos já importados
  4. Rate limiting para evitar bloqueios
  5. Parsing de dados do perfil (nome, cargo, empresa, experiência)
  6. Armazenamento em staging antes de import

Requisitos Tecnicos:
  Backend:
    - LinkedInScraperService
    - POST /api/v1/sourcing/linkedin/search
    - GET /api/v1/sourcing/linkedin/results/:runId
  Dados:
    - linkedin_scraper_runs: id, job_id, params, status, results_count
    - linkedin_candidates_staging: perfis brutos antes de importação
  Actor:
    - Apify LinkedIn Scraper (actor público ou custom)
    - Parâmetros: search query, location, limit

Integracoes Externas:
  Apify: LinkedIn Scraper Actor

DoD (Definition of Done):
  - [ ] Integração com actor funcionando
  - [ ] Parsing de resultados
  - [ ] Deduplicação implementada
  - [ ] Rate limiting ativo

Criterios de Aceitacao:
  - [ ] Busca retorna candidatos relevantes
  - [ ] Dados parseados corretamente
  - [ ] Candidatos duplicados detectados
  - [ ] Limites respeitados

Arquivos de Referencia (Prototipo Replit):
  - apify_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/apify_service.py
  - company_scraper_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/company_scraper_service.py
```

---

### CARD INT-APY-003: Integração com Sourcing Agent
**Épico:** É14 — Integrações MVP

```yaml
Titulo: [AI] Integração Scraper com Agente de Sourcing
Tipo: AI
Area: Backend-IA
Sprint: Pós-MVP
Pontos: 8
Prioridade: Alta
Epic: EPIC-INT-MVP
Status: ⏸️ Pós-MVP
Dependencias: INT-APY-002, AGT-001

Descricao: |
  Conectar o LinkedIn Scraper com o Agente de Sourcing da LIA
  para automatizar busca e qualificação inicial de candidatos
  com base na vaga.

Historia de Usuario: |
  Como recrutador, eu quero que a LIA faça sourcing automático
  e pré-qualifique candidatos do LinkedIn para minha vaga.

Regras de Negocio:
  1. Agente analisa requisitos da vaga
  2. Gera query de busca otimizada para LinkedIn
  3. Dispara scraper com parâmetros adequados
  4. Recebe resultados e faz triagem inicial
  5. Rankeia candidatos por fit com a vaga
  6. Sugere top candidatos para recrutador revisar

Requisitos Tecnicos:
  Backend:
    - SourcingAgentService
    - POST /api/v1/agents/sourcing/start
    - Orquestração: vaga → query → scraper → triagem → ranking
  AI:
    - Prompt para gerar queries de busca
    - Prompt para avaliar fit candidato/vaga
    - Score de relevância (0-100)
  Dados:
    - sourcing_runs: job_id, agent_run_id, candidates_found, candidates_qualified
    - sourcing_results: candidate_id, job_id, fit_score, agent_notes

Integracoes Externas:
  Apify: Via INT-APY-002
  LLM: Via INT-LLM-003 (Router)

DoD (Definition of Done):
  - [ ] Agente gera queries de busca
  - [ ] Scraper disparado automaticamente
  - [ ] Triagem inicial funciona
  - [ ] Ranking de candidatos

Criterios de Aceitacao:
  - [ ] Query gerada é relevante para vaga
  - [ ] Candidatos buscados e qualificados
  - [ ] Top candidatos apresentados ao recrutador
  - [ ] Processo end-to-end funcionando

Arquivos de Referencia (Prototipo Replit):
  - apify_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/apify_service.py
  - sourcing_pipeline_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/sourcing_pipeline_service.py
  - sourcing_pipeline.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/sourcing_pipeline.py
```

---

## ÉPICO 15: AGENTES ESPECIALIZADOS

> **Arquitetura Multi-Agente v2.2** - 10 agentes ativos + 3 deprecated (Fevereiro 2026)
>
> **Arquivos de agentes:** `lia-agent-system/app/agents/`
> **Arquivos de prompts:** `lia-agent-system/app/agents/prompts/` (11 prompts registrados)

### Tabela de Agentes v2.2

| ID | Agente | Arquivo | Prompt | Status |
|----|--------|---------|--------|--------|
| Ag.0 | Orchestrator | `orchestrator.py` | `ORCHESTRATOR_PROMPT` | ✅ Ativo |
| Ag.1 | JobIntakeAgent | `job_intake_agent.py` | `JOB_PLANNER_PROMPT` | ✅ Ativo |
| Ag.2 | SourcingAgent | `sourcing_agent.py` | `SOURCING_PROMPT` | ✅ Ativo |
| Ag.3 | TriagemCurricular | `triagem_curricular_agent.py` | `CV_SCREENING_PROMPT` | ✅ Ativo |
| Ag.4 | EntrevistadorWSI | `entrevistador_agent.py` | `INTERVIEWER_PROMPT` | ✅ Ativo |
| Ag.5 | AvaliadorWSI | `avaliador_wsi_agent.py` | `WSI_EVALUATOR_PROMPT` | ✅ Ativo |
| Ag.6 | SchedulingAgent | `scheduling_agent.py` | `SCHEDULING_PROMPT` | ✅ Ativo |
| Ag.7 | AnalistaFeedback | `analista_feedback_agent.py` | `ANALYST_FEEDBACK_PROMPT` | ✅ Ativo |
| Ag.8 | IntegradorATS | `integrador_ats_agent.py` | `ATS_INTEGRATOR_PROMPT` | ✅ Ativo |
| Ag.9 | TaskPlanner | `task_planner_agent.py` | `RECRUITER_ASSISTANT_PROMPT` | ✅ Ativo |
| - | ScreeningAgent | `screening_agent.py` | - | ⚠️ Deprecated |
| - | CommunicationAgent | `communication_agent.py` | - | ⚠️ Deprecated |
| - | AnalyticsAgent | `analytics_agent.py` | - | ⚠️ Deprecated |

### Componentes Compartilhados de Prompts

| Componente | Descrição |
|------------|-----------|
| `LIA_PERSONA` | Identidade e tom de comunicação da LIA |
| `HR_VOCABULARY` | Vocabulário técnico de RH brasileiro |
| `ETHICAL_GUIDELINES` | Diretrizes éticas (para agentes de avaliação) |
| `DATA_PERSISTENCE_GUIDELINES` | Regras de salvamento e sync ATS |

---

### CARD AGT-001: Agente Avaliador WSI
**Épico:** É15 — Agentes IA Especializados

```yaml
Titulo: [AI] Agente Avaliador WSI
Tipo: AI
Area: Backend-IA
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 13
Prioridade: Alta
Epic: EPIC-AGENTS
Status: 📋 Pendente Jira

Descricao: |
  Agente especializado em avaliação WSI que analisa respostas de
  candidatos e calcula scores usando metodologia Bloom/Dreyfus.

Historia de Usuario: |
  Como sistema, eu quero um agente que avalie respostas de
  candidatos de forma consistente e determinística.

Requisitos Tecnicos:
  Backend:
    - avaliador_wsi_agent.py
    - Integration with wsi_deterministic_scorer
    - Bloom/Dreyfus level detection

DoD:
  - [ ] Avaliação funciona
  - [ ] Scores determinísticos
  - [ ] Níveis detectados

Criterios de Aceitacao:
  - [ ] Bloom levels corretos
  - [ ] Dreyfus levels corretos
  - [ ] Score final calculado

Arquivos de Referencia (Prototipo Replit):
  - wsi_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_service.py
  - wsi_deterministic_scorer.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_deterministic_scorer.py
  - autonomous_agent_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/autonomous_agent_service.py
  - agent_monitoring_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/agent_monitoring_service.py
```

---

### CARD AGT-002: Agente de Triagem Curricular
**Épico:** É15 — Agentes IA Especializados

```yaml
Titulo: [AI] Agente de Triagem Curricular
Tipo: AI
Area: Backend-IA
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 13
Prioridade: Alta
Epic: EPIC-AGENTS
Status: 📋 Pendente Jira

Descricao: |
  Agente que analisa currículos e realiza triagem automatizada
  comparando com requisitos da vaga.

Historia de Usuario: |
  Como sistema, eu quero um agente que analise currículos
  e classifique candidatos por aderência à vaga.

Requisitos Tecnicos:
  Backend:
    - triagem_curricular_agent.py
    - CV parsing integration
    - Requirement matching

DoD:
  - [ ] Triagem funciona
  - [ ] Matching calculado
  - [ ] Parecer gerado

Criterios de Aceitacao:
  - [ ] CV analisado
  - [ ] Score de aderência
  - [ ] Justificativa textual

Arquivos de Referencia (Prototipo Replit):
  - cv_scoring_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/cv_scoring_service.py
  - cv_parser.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/cv_parser.py
  - autonomous_agent_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/autonomous_agent_service.py
  - pre_qualification_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/pre_qualification_service.py
```

---

### CARD AGT-003: Agente Inteligente de Agendamento
**Épico:** É15 — Agentes IA Especializados

```yaml
Titulo: [AI] Agente de Agendamento Inteligente
Tipo: AI
Area: Backend-IA
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 13
Prioridade: Alta
Epic: EPIC-AGENTS
Status: 📋 Pendente Jira
Dependencias: AGE-001

Descricao: |
  Agente que gerencia agendamento de entrevistas de forma inteligente,
  integrando com Microsoft Graph para criar eventos Teams.

Historia de Usuario: |
  Como sistema, eu quero um agente que agende entrevistas
  automaticamente considerando disponibilidade.

Requisitos Tecnicos:
  Backend:
    - scheduling_agent.py (61k linhas)
    - Microsoft Graph integration
    - Conflict detection

DoD:
  - [ ] Agendamento funciona
  - [ ] Teams meeting criado
  - [ ] Conflitos detectados

Criterios de Aceitacao:
  - [ ] Integração MS Graph
  - [ ] Link Teams gerado
  - [ ] Convites enviados

Arquivos de Referencia (Prototipo Replit):
  - scheduling_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/scheduling_service.py
  - autonomous_agent_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/autonomous_agent_service.py
  - calendar_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/calendar_service.py
  - agent_monitoring_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/agent_monitoring_service.py
```

---

### CARD TRI-012: Serviço de Pré-Qualificação
**Épico:** É15 — Agentes IA Especializados

```yaml
Titulo: [BACKEND] Serviço de Pré-Qualificação Automatizada
Tipo: Backend
Area: Backend
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 8
Prioridade: Alta
Epic: EPIC-TRI
Status: 📋 Pendente Jira

Descricao: |
  Serviço que realiza pré-qualificação automatizada de candidatos
  antes da triagem completa, com detecção de duplicatas.

Historia de Usuario: |
  Como sistema, eu quero pré-qualificar candidatos automaticamente
  para otimizar o processo de triagem.

Requisitos Tecnicos:
  Backend:
    - pre_qualification_service.py
    - Duplicate detection
    - Basic eligibility check

DoD:
  - [ ] Pré-qualificação funciona
  - [ ] Duplicatas detectadas
  - [ ] Elegibilidade verificada

Criterios de Aceitacao:
  - [ ] Candidatos pré-filtrados
  - [ ] Duplicatas marcadas
  - [ ] Status atualizado

Arquivos de Referencia (Prototipo Replit):
  - pre_qualification_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/pre_qualification_service.py
  - eligibility_verification_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/eligibility_verification_service.py
  - wsi_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_service.py
```

---

### CARD DAT-001: Sistema de Solicitação de Dados
**Épico:** É15 — Agentes IA Especializados

```yaml
Titulo: [FRONTEND] Sistema de Solicitação de Dados
Tipo: Frontend
Area: Frontend
Sprint: 3
Início: 23/fev
Término: 27/fev
Data Inicio Jira: 2026-02-23
Data Termino Jira: 2026-02-27
Pontos: 8
Prioridade: Media
Epic: EPIC-DATA
Status: 📋 Pendente Jira

Descricao: |
  Interface para gerenciar solicitações de dados aos candidatos,
  incluindo verificação OTP e upload de arquivos.

Historia de Usuario: |
  Como recrutador, eu quero solicitar documentos e informações
  adicionais aos candidatos de forma organizada.

Requisitos Tecnicos:
  Frontend:
    - DataRequestTab.tsx
    - OTP verification flow
    - File upload handling

DoD:
  - [ ] Solicitações criadas
  - [ ] OTP funciona
  - [ ] Uploads funcionam

Criterios de Aceitacao:
  - [ ] Múltiplos tipos de dados
  - [ ] Verificação OTP
  - [ ] Status de resposta

Arquivos de Referencia (Prototipo Replit):
  - data_request_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/data_request_service.py
  - data_request_whatsapp_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/data_request_whatsapp_service.py
  - use-data-request-config.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/use-data-request-config.ts
  - use-data-request-modals.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/use-data-request-modals.ts
```

---

### CARD ENT-001: Análise de Transcrição de Entrevista
**Épico:** É15 — Agentes IA Especializados

```yaml
Titulo: [BACKEND] Serviço de Análise de Transcrição
Tipo: Backend
Area: Backend
Sprint: 2
Início: 16/fev
Término: 20/fev
Data Inicio Jira: 2026-02-16
Data Termino Jira: 2026-02-20
Pontos: 13
Prioridade: Alta
Epic: EPIC-INTERVIEW
Status: 📋 Pendente Jira

Descricao: |
  Serviço que analisa transcrições de entrevistas do Microsoft Teams,
  aplica scoring WSI e extrai insights comportamentais.

Historia de Usuario: |
  Como recrutador, eu quero que a transcrição da entrevista seja
  analisada automaticamente para identificar pontos-chave.

Requisitos Tecnicos:
  Backend:
    - interview_transcript_analysis_service.py
    - Teams transcription integration
    - WSI scoring on responses
    - Behavioral analysis

DoD:
  - [ ] Transcrição processada
  - [ ] Scores aplicados
  - [ ] Insights extraídos

Criterios de Aceitacao:
  - [ ] Integração Teams funciona
  - [ ] Perguntas identificadas
  - [ ] Respostas avaliadas

Arquivos de Referencia (Prototipo Replit):
  - interview_transcript_analysis_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/interview_transcript_analysis_service.py
  - multimodal_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/multimodal_service.py
  - deepgram_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/deepgram_service.py
  - transcription.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/transcription.py
```

---

### CARD KAN-009: Componentes Kanban Modulares
**Épico:** É15 — Agentes IA Especializados

```yaml
Titulo: [FRONTEND] Refatoração Modular do Kanban
Tipo: Frontend
Area: Frontend
Sprint: 1
Início: 09/fev
Término: 13/fev
Data Inicio Jira: 2026-02-09
Data Termino Jira: 2026-02-13
Pontos: 13
Prioridade: Alta
Epic: EPIC-KAN
Status: 📋 Pendente Jira

Descricao: |
  Refatoração do sistema Kanban de 10k+ linhas para arquitetura
  modular com componentes, hooks e utilities separados.

Historia de Usuario: |
  Como desenvolvedor, eu quero componentes Kanban modulares
  para facilitar manutenção e reutilização.

Estrutura Implementada:
  plataforma-lia/src/components/kanban/:
    - types.ts - Interfaces KanbanCandidate, DynamicStage
    - constants.ts - SYSTEM_STAGES, LEGACY_MAPPING
    - utils/ - stage-utils, filter-utils, status-utils
    - hooks/ - useDragDrop, useKanbanFilters, etc
    - components/ - CandidateCard, KanbanColumn, KanbanBoard

DoD:
  - [ ] Arquivos separados
  - [ ] Hooks reutilizáveis
  - [ ] Utils compartilhados

Criterios de Aceitacao:
  - [ ] Componentes independentes
  - [ ] Types centralizados
  - [ ] Hooks funcionais

Arquivos de Referencia (Prototipo Replit):
  - types.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/kanban/types.ts
  - types.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/pages/job-kanban/types.ts
  - page.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/app/jobs/[id]/page.tsx
  - use-recruitment-stages.ts: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/hooks/use-recruitment-stages.ts
```


---


---

### CARD AGT-004: Orquestrador de Pipeline Chat
**Épico:** É15 — Agentes IA Especializados
> ⚠️ Card pendente de especificação detalhada. Referência: Índice É15.

## ÉPICO 16: OTIMIZAÇÃO ESTATÍSTICA DE BUSCA (8 cards, 38 SP)
**Objetivo:** Otimizar pipeline de busca com análise estatística adaptativa por tipo de vaga
**Sprint Alvo:** 2-5
**Prioridade:** 🔴 Crítica
**Dependências:** ÉPICO 3 (Busca e Mapeamento)

> **Timing:** Sprints 2-5
> **Impacto:** Eliminar irrelevantes antes do WRF, parametrização adaptativa
> **Pré-requisito:** WDT-009 (classificação de vaga) é bloqueante para WDT-010, 011, 012, 014
> **Referência completa:** `docs/epic-wdt-talent-funnel.md`
> **Nota:** WDT-005 foi movido para Épico 3 (Quick Wins) — incluído aqui como referência cruzada

| Card | Título | Tipo | Status | Dependências | Pontos |
|------|--------|------|--------|--------------|--------|
| WDT-005 | Remover ordenação automática por ranking | Frontend | 📋 Pendente | - | 2 |
| WDT-008 | Dashboard básico de métricas de feedback | Full-Stack | 📋 Pendente | WDT-006 | 5 |
| WDT-009 | Classificação automática de nível de qualificação da vaga | Backend | 📋 Pendente | - | 8 |
| WDT-010 | Exibição e override da classificação de vaga | Frontend | 📋 Pendente | WDT-009 | 2 |
| WDT-011 | Cálculo de taxa de queda de score (Elasticsearch) | Backend | 📋 Pendente | WDT-009 | 5 |
| WDT-012 | Cálculo de gap semântico (PG Vector) | Backend | 📋 Pendente | WDT-009 | 5 |
| WDT-013 | Teste de estabilidade intra-query (dev/staging) | Backend | 📋 Pendente | - | 3 |
| WDT-014 | Parametrização dinâmica do K no WRF | Backend | 📋 Pendente | WDT-009 | 5 |
| WDT-015 | Filtro pré-WRF combinando análises estatísticas | Backend | 📋 Pendente | WDT-011, WDT-012 | 5 |

**Total:** 9 cards (8 originais + WDT-005 ref.) | Pontos: 40 | Status: Pendente Jira

---

##### WDT-005: Remover Ordenação Automática por Ranking (Referência Cruzada)

> **⚠️ Card principal localizado no Épico 3 (MAP-013 / WDT-005).** Ver detalhes completos, YAML e Prompt para IA na seção detalhada do Épico 3 acima.

---

### CARD WDT-008: Dashboard Básico de Métricas de Feedback
**Épico:** É16 — Otimização Estatística de Busca

```yaml
Titulo: "[BE/FE] Dashboard básico de métricas de feedback"
Tipo: Story
Sprint: 2
Pontos: 5
Horas: 8
Prioridade: Média
Epic: EPIC-16 (Otimização Estatística de Busca)
Fase: Fase 1 - Quick Wins
Status: 📋 Pendente Jira
Labels: feedback, analytics, dashboard

Descricao: |
  Dashboard simples para visualizar padrões de feedback dos recrutadores.
  
  Métricas:
  - Total likes vs dislikes por período
  - Taxa de like por faixa de score (o score X-Y tem %N de likes?)
  - Top motivos de dislike (se campo de comentário existir)
  - Feedback por tipo de vaga
  - Feedback por recrutador

Historia de Usuario: |
  Como admin, eu quero visualizar padrões de feedback dos recrutadores
  para entender se os resultados da busca estão satisfatórios.

Requisitos Tecnicos:
  Backend (Rails):
    - Controller: app/controllers/api/v1/admin/feedback_analytics_controller.rb
    - Service: app/services/analytics/feedback_analytics_service.rb
    - Queries agregadas em CandidateFeedback
    - Cache Redis com TTL 5 min para queries pesadas
  Frontend (Vue.js 3 + Vuetify 3):
    - Página: src/pages/admin/FeedbackDashboard.vue
    - Componentes: gráficos com Chart.js ou ApexCharts
    - Vuetify: v-card, v-data-table, v-chip para métricas

DoD:
  - [ ] Dashboard acessível para admins
  - [ ] Gráficos de like/dislike ratio
  - [ ] Filtros por período e tipo de vaga
  - [ ] Dados atualizados (cache 5 min)

Criterios de Aceitacao:
  - [ ] Total likes vs dislikes exibido
  - [ ] Taxa de like por faixa de score calculada
  - [ ] Filtros por período funcionais
  - [ ] Apenas admins acessam

Dependencias: WDT-006
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - strategic-dashboard.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/dashboard/strategic-dashboard.tsx
  - chart-components.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/charts/chart-components.tsx
  - candidate_feedback_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/candidate_feedback_service.py
  - search_analytics_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/search_analytics_service.py
```

###### Prompt para IA (Cursor/VSCode) — WDT-008

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x + Vue.js 3 + Vuetify 3 + Nuxt 3
- Cache: Redis
- Testes: RSpec + Vitest

---

TAREFA: Criar dashboard de métricas de feedback (like/dislike) para admins.

IMPLEMENTAÇÃO:

Backend (Rails):
1. Service: app/services/analytics/feedback_analytics_service.rb
   - total_by_type(period:): COUNT group by feedback_type
   - like_rate_by_score_range: agrupa feedbacks por faixa de score (0-25, 25-50, etc.)
   - feedback_by_job_type: agrupa por qualification_level da vaga
   - feedback_by_recruiter: agrupa por user_id
   - Cachear com Redis.cache(key, expires_in: 5.minutes)

2. Controller: app/controllers/api/v1/admin/feedback_analytics_controller.rb
   - GET /api/v1/admin/feedback-analytics
   - Parâmetros: period (7d, 30d, 90d), job_type (optional)
   - Autorização: apenas role=admin

Frontend (Vue.js):
1. Página: src/pages/admin/FeedbackDashboard.vue
   - Usar ApexCharts (vue3-apexcharts) para gráficos
   - Gráfico de donut: likes vs dislikes
   - Gráfico de barras: like rate por faixa de score
   - v-data-table: feedback por recrutador
   - v-select para filtro de período

NÃO FAZER:
- NÃO expor dados entre companies (multi-tenant)
- NÃO calcular em real-time sem cache (usar Redis)
```

---

### CARD WDT-009: Classificação Automática de Nível de Qualificação da Vaga
**Épico:** É16 — Otimização Estatística de Busca

```yaml
Titulo: "[BE] Classificação automática de nível de qualificação da vaga"
Tipo: Story
Sprint: 3
Pontos: 8
Horas: 16
Prioridade: Crítica
Epic: EPIC-16 (Otimização Estatística de Busca)
Fase: Fase 2 - Análise Estatística
Status: 📋 Pendente Jira
Labels: search, classification, blocker

Descricao: |
  Criar sistema de classificação automática do nível de qualificação 
  de vagas usando LLM.
  
  Contexto: André identificou que critérios para CEO são completamente 
  diferentes de atendente de loja. Esta classificação é BLOQUEANTE para 
  toda parametrização adaptativa (WDT-011, WDT-012, WDT-014).
  
  Implementação:
  - Prompt LLM (Gemini) para analisar descrição da vaga
  - Classificar em: Alta (Executive Search), Média (Especialista), Baixa (Operacional)
  - Salvar classificação no modelo Job (campo qualification_level)
  - Override manual possível pelo recrutador

Historia de Usuario: |
  Como sistema, eu preciso classificar automaticamente o nível de
  qualificação da vaga para adaptar os parâmetros de busca e avaliação.

Regras de Negocio:
  1. Classificação automática ao criar/editar vaga
  2. 3 níveis: alta (executive search), média (especialista), baixa (operacional)
  3. Campo salvo no banco (qualification_level)
  4. Override manual possível pelo recrutador
  5. Classificação afeta K do WRF e thresholds de filtragem

Requisitos Tecnicos:
  Backend (Rails + Python):
    - Migration: adicionar qualification_level (enum) na tabela jobs
    - Rails Service: app/services/jobs/qualification_classifier_service.rb
    - Chamada para Python FastAPI: POST /api/v1/ai/classify-job-level
    - Callback after_save no modelo Job para classificar
  Python (FastAPI):
    - Endpoint: POST /api/v1/ai/classify-job-level
    - Prompt Gemini para classificação
    - Response: { level: "alta"|"media"|"baixa", confidence: float, reasoning: string }
  Testes:
    - RSpec: spec/services/jobs/qualification_classifier_service_spec.rb
    - pytest: tests/test_classify_job_level.py
    - Testar com 20+ vagas de tipos diferentes

DoD:
  - [ ] Classificação automática ao criar/editar vaga
  - [ ] 3 níveis funcionais: alta/média/baixa
  - [ ] Campo salvo no banco
  - [ ] Override manual possível
  - [ ] Testes com 20+ vagas de diferentes tipos
  - [ ] Prompt documentado e versionado

Criterios de Aceitacao:
  - [ ] Vaga de CEO classificada como "alta"
  - [ ] Vaga de desenvolvedor sênior classificada como "média"
  - [ ] Vaga de atendente classificada como "baixa"
  - [ ] Recrutador pode alterar classificação manualmente
  - [ ] Classificação persiste no banco
  - [ ] Testes passando

Dependencias: Nenhuma
Bloqueia: WDT-010, WDT-011, WDT-012, WDT-014

Arquivos de Referencia (Prototipo Replit):
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - job_context_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/job_context_service.py
  - lia_score_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/lia_score_service.py
```

###### Prompt para IA (Cursor/VSCode) — WDT-009

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x + Python 3.11 + FastAPI
- Banco: PostgreSQL
- IA: Gemini 2.5 Flash via LangChain
- Testes: RSpec + pytest

---

TAREFA: Criar classificação automática de nível de qualificação da vaga usando LLM.
ESTE CARD É BLOQUEANTE para toda parametrização adaptativa.

IMPLEMENTAÇÃO:

1. Migration (Rails):
   add_column :jobs, :qualification_level, :integer, default: 1
   # enum: { baixa: 0, media: 1, alta: 2 }
   add_column :jobs, :qualification_confidence, :float
   add_column :jobs, :qualification_reasoning, :text
   add_column :jobs, :qualification_override, :boolean, default: false

2. Model Job (Rails):
   enum qualification_level: { baixa: 0, media: 1, alta: 2 }
   after_save :classify_qualification, if: :saved_change_to_description?

3. Service (Rails):
   app/services/jobs/qualification_classifier_service.rb
   - Chama Python FastAPI: POST /api/v1/ai/classify-job-level
   - Body: { title, description, requirements, salary_range }
   - Salva resultado no Job
   - Não sobrescreve se qualification_override=true

4. Endpoint Python (FastAPI):
   app/routers/ai/classification.py
   
   Prompt Gemini:
   "Analise esta vaga e classifique o nível de qualificação:
   - ALTA: Cargos de diretoria, C-level, VP, posições de executive search
   - MEDIA: Especialistas, seniores, coordenadores, gerentes de área
   - BAIXA: Operacionais, júnior, assistentes, atendimento
   
   Vaga: {title}
   Descrição: {description}
   Requisitos: {requirements}
   Faixa salarial: {salary_range}
   
   Responda em JSON: { level: 'alta'|'media'|'baixa', confidence: 0-1, reasoning: 'texto' }"

5. Testes:
   - Testar com vagas CEO, Dev Sênior, Atendente
   - Verificar que override manual não é sobrescrito
   - Testar callback after_save

NÃO FAZER:
- NÃO hardcodar classificação
- NÃO ignorar salary_range na classificação (é forte indicador)
- NÃO sobrescrever override manual do recrutador
```

---

### CARD WDT-010: Exibição e Override da Classificação de Vaga
**Épico:** É16 — Otimização Estatística de Busca

```yaml
Titulo: "[FE] Exibição e override da classificação de vaga"
Tipo: Task
Sprint: 3
Pontos: 2
Horas: 4
Prioridade: Alta
Epic: EPIC-16 (Otimização Estatística de Busca)
Fase: Fase 2 - Análise Estatística
Status: 📋 Pendente Jira
Labels: ux, classification

Descricao: |
  Exibir a classificação automática na interface de edição de vaga 
  e permitir override manual.
  - Badge visual (Alta/Média/Baixa) na vaga
  - Dropdown para override manual
  - Tooltip explicando impacto na busca

Historia de Usuario: |
  Como recrutador, eu quero ver a classificação da minha vaga e poder
  ajustá-la se discordar da classificação automática.

Requisitos Tecnicos:
  Frontend (Vue.js 3 + Vuetify 3):
    - Componente: src/components/jobs/QualificationBadge.vue
    - v-chip com cores: alta=purple, média=blue, baixa=green
    - v-select para override
    - v-tooltip explicando impacto

DoD:
  - [ ] Badge visível na vaga
  - [ ] Override funcional
  - [ ] Tooltip informativo

Criterios de Aceitacao:
  - [ ] Badge com cor correta por nível
  - [ ] Override altera classificação via API
  - [ ] Tooltip explica impacto na busca

Dependencias: WDT-009
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - search-results-card.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/search-results-card.tsx
  - advanced-search.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/advanced-search.tsx
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
```

###### Prompt para IA (Cursor/VSCode) — WDT-010

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Vue.js 3 + Vuetify 3 + Nuxt 3

---

TAREFA: Exibir classificação de vaga com badge visual e permitir override.

IMPLEMENTAÇÃO:
1. Componente QualificationBadge.vue:
   - v-chip com cores por nível:
     alta: color="deep-purple" icon="mdi-crown"
     média: color="blue" icon="mdi-briefcase"
     baixa: color="green" icon="mdi-account-hard-hat"
   - v-tooltip: "Esta vaga foi classificada como [nível]. Isso afeta a 
     precisão da busca e critérios de avaliação."
   - v-select inline para override (se admin/recrutador)

2. Props: qualificationLevel, canOverride, confidence
3. Emit: 'update:level' com PATCH para API

NÃO FAZER:
- NÃO usar cores do accent LIA (cyan) — usar cores semânticas
```

---

### CARD WDT-011: Cálculo de Taxa de Queda de Score (Elasticsearch)
**Épico:** É16 — Otimização Estatística de Busca

```yaml
Titulo: "[BE] Cálculo de taxa de queda de score (Elasticsearch)"
Tipo: Story
Sprint: 4
Pontos: 5
Horas: 10
Prioridade: Alta
Epic: EPIC-16 (Otimização Estatística de Busca)
Fase: Fase 2 - Análise Estatística
Status: 📋 Pendente Jira
Labels: search, statistics, optimization

Descricao: |
  Implementar análise estatística de taxa de queda de score nos resultados
  do Elasticsearch.
  
  Contexto: André propôs identificar o 'cotovelo' onde scores começam a 
  achatar para filtrar candidatos irrelevantes ANTES do WRF.
  
  Fórmula: queda_percentual = ((score_melhor - score_pior) / score_melhor) * 100
  
  Implementação:
  - Calcular queda percentual entre top score e cada candidato
  - Identificar ponto de inflexão (cotovelo) na curva
  - Threshold dinâmico baseado em qualification_level da vaga
  - Filtrar candidatos abaixo do threshold antes do WRF
  - Logar análise para observabilidade

Historia de Usuario: |
  Como sistema de busca, eu preciso identificar automaticamente onde os
  scores do Elasticsearch deixam de ser significativos para filtrar
  candidatos irrelevantes antes do WRF.

Requisitos Tecnicos:
  Backend (Rails):
    - Service: app/services/search/es_score_drop_analyzer.rb
    - Recebe: array de resultados ES com scores
    - Calcula: queda percentual entre cada candidato e o top
    - Identifica: ponto de inflexão (cotovelo)
    - Thresholds por qualification_level:
      - Alta: queda > 40% = corte
      - Média: queda > 55% = corte
      - Baixa: queda > 70% = corte
    - Output: candidatos filtrados + log de análise
  Testes:
    - RSpec: spec/services/search/es_score_drop_analyzer_spec.rb

DoD:
  - [ ] Cálculo implementado e testado
  - [ ] Threshold adaptativo por tipo de vaga
  - [ ] Log de análise salvo
  - [ ] Candidatos abaixo do threshold filtrados
  - [ ] Métricas: % de candidatos filtrados por busca

Criterios de Aceitacao:
  - [ ] Ponto de inflexão identificado corretamente
  - [ ] Thresholds aplicados por qualification_level
  - [ ] Log registra: total candidatos, ponto de corte, % filtrados
  - [ ] Testes com datasets variados passando

Dependencias: WDT-009
Bloqueia: WDT-015

Arquivos de Referencia (Prototipo Replit):
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - search_analytics_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/search_analytics_service.py
  - vacancy_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/vacancy_search_service.py
```

###### Prompt para IA (Cursor/VSCode) — WDT-011

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x
- Banco: Elasticsearch 8.x
- Testes: RSpec

---

TAREFA: Implementar análise de taxa de queda de score nos resultados Elasticsearch
para filtrar candidatos irrelevantes ANTES do WRF.

IMPLEMENTAÇÃO:

1. Service:
   Arquivo: app/services/search/es_score_drop_analyzer.rb

   class Search::EsScoreDropAnalyzer
     THRESHOLDS = {
       alta:  0.40,  # corte quando queda > 40%
       media: 0.55,  # corte quando queda > 55%
       baixa: 0.70   # corte quando queda > 70%
     }.freeze

     def initialize(results:, qualification_level:)
       @results = results.sort_by { |r| -r[:score] }
       @level = qualification_level.to_sym
       @threshold = THRESHOLDS[@level]
     end

     def analyze
       return @results if @results.size <= 1
       top_score = @results.first[:score]
       cutoff_index = find_cutoff(top_score)
       filtered = @results.first(cutoff_index)
       log_analysis(top_score, cutoff_index)
       filtered
     end

     private

     def find_cutoff(top_score)
       @results.each_with_index do |result, idx|
         drop = (top_score - result[:score]) / top_score.to_f
         return idx if drop > @threshold
       end
       @results.size
     end

     def log_analysis(top_score, cutoff_index)
       Rails.logger.info("[EsScoreDropAnalyzer] level=#{@level} " \
         "total=#{@results.size} cutoff_at=#{cutoff_index} " \
         "filtered=#{@results.size - cutoff_index} " \
         "top_score=#{top_score}")
     end
   end

2. Configurar thresholds como variáveis de ambiente para ajuste sem deploy:
   ES_SCORE_DROP_THRESHOLD_ALTA=0.40
   ES_SCORE_DROP_THRESHOLD_MEDIA=0.55
   ES_SCORE_DROP_THRESHOLD_BAIXA=0.70

3. Testes com datasets variados:
   - Queda gradual (muitos candidatos relevantes)
   - Queda abrupta (poucos relevantes)
   - Todos com score similar (sem corte)
   - Um único candidato relevante (corte em 1)

NÃO FAZER:
- NÃO hardcodar thresholds sem fallback para env vars
- NÃO aplicar corte se resultado tem < 3 candidatos
```

---

### CARD WDT-012: Cálculo de Gap Semântico (PG Vector)
**Épico:** É16 — Otimização Estatística de Busca

```yaml
Titulo: "[BE] Cálculo de gap semântico (PG Vector)"
Tipo: Story
Sprint: 4
Pontos: 5
Horas: 10
Prioridade: Alta
Epic: EPIC-16 (Otimização Estatística de Busca)
Fase: Fase 2 - Análise Estatística
Status: 📋 Pendente Jira
Labels: search, statistics, optimization

Descricao: |
  Implementar análise de gap semântico nos resultados do PG Vector.
  
  Contexto: Similar à taxa de queda do ES, mas para distância de cossenos.
  
  Implementação:
  - Calcular diferença de distância entre candidatos consecutivos
  - Identificar 'salto' na distância (gap significativo)
  - Threshold dinâmico baseado em qualification_level
  - Filtrar candidatos após o gap antes de enviar para WRF
  - Análise de desvio padrão complementar

Historia de Usuario: |
  Como sistema de busca, eu preciso identificar onde a distância
  semântica dá um "salto" significativo para filtrar candidatos
  irrelevantes do PG Vector antes do WRF.

Requisitos Tecnicos:
  Backend (Rails):
    - Service: app/services/search/pgv_gap_analyzer.rb
    - Recebe: array de resultados PGV com distâncias
    - Calcula: diferença de distância entre candidatos consecutivos
    - Identifica: gap > N * desvio padrão
    - Threshold adaptativo por qualification_level
    - Output: candidatos filtrados + log de análise
  Testes:
    - RSpec: spec/services/search/pgv_gap_analyzer_spec.rb

DoD:
  - [ ] Gap calculado corretamente
  - [ ] Threshold adaptativo funcional
  - [ ] Filtro pré-WRF implementado
  - [ ] Logs de análise salvos

Criterios de Aceitacao:
  - [ ] Gap identificado entre candidatos consecutivos
  - [ ] Threshold aplicado por qualification_level
  - [ ] Candidatos após gap removidos
  - [ ] Log com métricas de filtragem

Dependencias: WDT-009
Bloqueia: WDT-015

Arquivos de Referencia (Prototipo Replit):
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - embedding_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/embedding_service.py
  - search_analytics_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/search_analytics_service.py
```

###### Prompt para IA (Cursor/VSCode) — WDT-012

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x
- Banco: PostgreSQL + PG Vector
- Testes: RSpec

---

TAREFA: Implementar análise de gap semântico nos resultados PG Vector.

IMPLEMENTAÇÃO:

1. Service:
   Arquivo: app/services/search/pgv_gap_analyzer.rb

   class Search::PgvGapAnalyzer
     GAP_MULTIPLIERS = {
       alta:  1.5,  # gap > 1.5x desvio padrão = corte
       media: 2.0,
       baixa: 2.5
     }.freeze

     def initialize(results:, qualification_level:)
       @results = results.sort_by { |r| r[:distance] }
       @level = qualification_level.to_sym
       @multiplier = GAP_MULTIPLIERS[@level]
     end

     def analyze
       return @results if @results.size <= 2
       gaps = calculate_consecutive_gaps
       std_dev = standard_deviation(gaps)
       mean_gap = gaps.sum / gaps.size.to_f
       cutoff = find_gap_cutoff(gaps, mean_gap, std_dev)
       @results.first(cutoff + 1)
     end

     private

     def calculate_consecutive_gaps
       @results.each_cons(2).map { |a, b| b[:distance] - a[:distance] }
     end

     def find_gap_cutoff(gaps, mean, std_dev)
       threshold = mean + (@multiplier * std_dev)
       gaps.each_with_index do |gap, idx|
         return idx if gap > threshold
       end
       @results.size - 1
     end
   end

NÃO FAZER:
- NÃO confundir distância (menor=melhor) com score (maior=melhor)
- NÃO aplicar corte se < 3 candidatos
```

---

### CARD WDT-013: Teste de Estabilidade Intra-Query
**Épico:** É16 — Otimização Estatística de Busca

```yaml
Titulo: "[BE] Teste de estabilidade intra-query (dev/staging)"
Tipo: Story
Sprint: 4
Pontos: 3
Horas: 6
Prioridade: Média
Epic: EPIC-16 (Otimização Estatística de Busca)
Fase: Fase 2 - Análise Estatística
Status: 📋 Pendente Jira
Labels: search, quality, diagnostics

Descricao: |
  Criar ferramenta de diagnóstico que executa mesma query múltiplas 
  vezes e verifica consistência.
  
  Contexto: André alertou que se rankings mudam significativamente 
  entre execuções idênticas, a parametrização precisa de ajuste.

Historia de Usuario: |
  Como desenvolvedor, eu quero testar se a mesma busca retorna resultados
  consistentes para garantir estabilidade do sistema.

Requisitos Tecnicos:
  Backend (Rails):
    - Rake task: lib/tasks/search_stability.rake
    - Endpoint admin: GET /api/v1/admin/search-stability?query=X&runs=5
    - Executa query N vezes (3-5x)
    - Compara IDs e posições retornadas
    - Calcula índice de estabilidade (% candidatos que mantêm posição)
    - Alerta se divergência > threshold configurável

DoD:
  - [ ] Task executável via CLI ou admin
  - [ ] Relatório de estabilidade gerado
  - [ ] Alerta em caso de instabilidade
  - [ ] Resultados comparados por fonte (ES vs PGV)

Criterios de Aceitacao:
  - [ ] Rake task funcional: rails search:stability_test[query,5]
  - [ ] Relatório com % de estabilidade
  - [ ] Comparação ES vs PGV separada
  - [ ] Alerta quando estabilidade < 80%

Dependencias: Nenhuma
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - search_analytics_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/search_analytics_service.py
```

###### Prompt para IA (Cursor/VSCode) — WDT-013

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x
- Banco: Elasticsearch + PG Vector

---

TAREFA: Criar ferramenta de diagnóstico de estabilidade de queries.

IMPLEMENTAÇÃO:

1. Rake task:
   lib/tasks/search_stability.rake
   
   namespace :search do
     desc "Test search query stability"
     task :stability_test, [:query, :runs] => :environment do |t, args|
       query = args[:query]
       runs = (args[:runs] || 5).to_i
       
       es_results = runs.times.map { elasticsearch_search(query) }
       pgv_results = runs.times.map { pgvector_search(query) }
       
       es_stability = calculate_stability(es_results)
       pgv_stability = calculate_stability(pgv_results)
       
       puts "ES Stability: #{es_stability}%"
       puts "PGV Stability: #{pgv_stability}%"
       puts "WARNING: Unstable!" if es_stability < 80 || pgv_stability < 80
     end
   end

2. calculate_stability: compara IDs retornados em cada run
   - % de IDs que aparecem em TODAS as runs
   - Variação de posição média por candidato

NÃO FAZER:
- NÃO rodar em produção automaticamente (apenas dev/staging)
- NÃO expor endpoint para usuários comuns (admin only)
```

---

### CARD WDT-014: Parametrização Dinâmica do K no WRF
**Épico:** É16 — Otimização Estatística de Busca

```yaml
Titulo: "[BE] Parametrização dinâmica do K no WRF"
Tipo: Story
Sprint: 5
Pontos: 5
Horas: 8
Prioridade: Alta
Epic: EPIC-16 (Otimização Estatística de Busca)
Fase: Fase 2 - Análise Estatística
Status: 📋 Pendente Jira
Labels: search, wrf, optimization

Descricao: |
  Tornar o parâmetro K do Weighted Rank Fusion dinâmico baseado no tipo de vaga.
  
  Contexto: K padrão é 60. André explicou: K menor = mais criterioso, 
  K maior = menos criterioso.
  
  Implementação:
  - Alta qualificação: K=20-30 (mais criterioso)
  - Média qualificação: K=40-50
  - Baixa qualificação: K=60-80 (menos criterioso)
  - Usar qualification_level da vaga para selecionar K
  - Valores configuráveis via settings/env (não hardcoded)
  - Logar K utilizado em cada busca

Historia de Usuario: |
  Como sistema de busca, eu preciso ajustar automaticamente a
  sensibilidade do WRF com base na complexidade da vaga.

Requisitos Tecnicos:
  Backend (Rails):
    - Service: app/services/search/wrf_service.rb (modificar)
    - Receber qualification_level e selecionar K
    - Valores via ENV: WRF_K_ALTA=25, WRF_K_MEDIA=45, WRF_K_BAIXA=70
    - Log do K utilizado em cada busca
  Testes:
    - RSpec: comparar resultados com K fixo vs dinâmico

DoD:
  - [ ] K dinâmico implementado
  - [ ] Valores configuráveis externamente
  - [ ] Log do K por busca
  - [ ] Testes comparando K fixo vs dinâmico

Criterios de Aceitacao:
  - [ ] Vaga alta usa K=20-30
  - [ ] Vaga média usa K=40-50
  - [ ] Vaga baixa usa K=60-80
  - [ ] K logado em cada busca
  - [ ] Valores ajustáveis via ENV

Dependencias: WDT-009
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - vacancy_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/vacancy_search_service.py
  - search_analytics_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/search_analytics_service.py
```

###### Prompt para IA (Cursor/VSCode) — WDT-014

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x
- Banco: PostgreSQL + Elasticsearch + PG Vector

---

TAREFA: Tornar o K do Weighted Rank Fusion dinâmico por tipo de vaga.

IMPLEMENTAÇÃO:

1. Modificar WRF Service:
   app/services/search/wrf_service.rb

   K_VALUES = {
     alta:  ENV.fetch('WRF_K_ALTA', 25).to_i,
     media: ENV.fetch('WRF_K_MEDIA', 45).to_i,
     baixa: ENV.fetch('WRF_K_BAIXA', 70).to_i
   }.freeze

   def merge(es_results, pgv_results, qualification_level:)
     k = K_VALUES[qualification_level.to_sym]
     Rails.logger.info("[WRF] K=#{k} for level=#{qualification_level}")
     
     # WRF formula: score = sum(1 / (k + rank_i))
     merged_scores = {}
     [es_results, pgv_results].each do |results|
       results.each_with_index do |candidate, rank|
         id = candidate[:id]
         merged_scores[id] ||= 0
         merged_scores[id] += 1.0 / (k + rank + 1)
       end
     end
     merged_scores.sort_by { |_, score| -score }.map(&:first)
   end

NÃO FAZER:
- NÃO hardcodar K sem fallback para ENV
- NÃO alterar a fórmula WRF (apenas o K)
```

---

### CARD WDT-015: Filtro Pré-WRF Combinando Análises Estatísticas
**Épico:** É16 — Otimização Estatística de Busca

```yaml
Titulo: "[BE] Filtro pré-WRF combinando análises estatísticas"
Tipo: Story
Sprint: 5
Pontos: 5
Horas: 10
Prioridade: Alta
Epic: EPIC-16 (Otimização Estatística de Busca)
Fase: Fase 2 - Análise Estatística
Status: 📋 Pendente Jira
Labels: search, wrf, performance

Descricao: |
  Orquestrar filtros estatísticos (taxa de queda + gap semântico) antes do WRF.
  
  Contexto: André propôs não passar automaticamente 100 de cada fonte. 
  Passar apenas os relevantes.
  
  Pipeline:
  - ES results → taxa de queda → candidatos filtrados ES
  - PGV results → gap semântico → candidatos filtrados PGV
  - Merge: candidatos filtrados ES + PGV → WRF
  - Exemplo: Se saíram 20 do ES e 40 do PGV, WRF recebe 60 (não 200)

Historia de Usuario: |
  Como sistema de busca, eu preciso filtrar candidatos irrelevantes
  de cada fonte ANTES do WRF para melhorar qualidade e performance.

Requisitos Tecnicos:
  Backend (Rails):
    - Service: app/services/search/pre_wrf_filter_service.rb
    - Orquestra: EsScoreDropAnalyzer + PgvGapAnalyzer + WrfService
    - Log de quantos foram filtrados em cada etapa
  Testes:
    - RSpec: spec/services/search/pre_wrf_filter_service_spec.rb

DoD:
  - [ ] Pipeline implementado e testado
  - [ ] WRF recebe apenas candidatos pré-filtrados
  - [ ] Redução mensurável no volume do WRF
  - [ ] Métricas de filtragem por etapa

Criterios de Aceitacao:
  - [ ] ES filtra por taxa de queda
  - [ ] PGV filtra por gap semântico
  - [ ] WRF recebe união dos filtrados
  - [ ] Log com total por etapa

Dependencias: WDT-011, WDT-012
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - vacancy_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/vacancy_search_service.py
  - search_analytics_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/search_analytics_service.py
```

###### Prompt para IA (Cursor/VSCode) — WDT-015

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x
- Banco: Elasticsearch + PG Vector

---

TAREFA: Orquestrar filtros estatísticos antes do WRF.

IMPLEMENTAÇÃO:

1. Service:
   app/services/search/pre_wrf_filter_service.rb

   class Search::PreWrfFilterService
     def initialize(es_results:, pgv_results:, qualification_level:)
       @es_results = es_results
       @pgv_results = pgv_results
       @level = qualification_level
     end

     def call
       filtered_es = Search::EsScoreDropAnalyzer.new(
         results: @es_results, qualification_level: @level
       ).analyze

       filtered_pgv = Search::PgvGapAnalyzer.new(
         results: @pgv_results, qualification_level: @level
       ).analyze

       log_filtering(filtered_es, filtered_pgv)

       Search::WrfService.new.merge(
         filtered_es, filtered_pgv,
         qualification_level: @level
       )
     end

     private

     def log_filtering(es, pgv)
       Rails.logger.info("[PreWRF] ES: #{@es_results.size}→#{es.size} | " \
         "PGV: #{@pgv_results.size}→#{pgv.size} | " \
         "WRF receives: #{es.size + pgv.size}")
     end
   end

NÃO FAZER:
- NÃO pular filtros se qualification_level não está definido (usar default :media)
- NÃO passar todos os candidatos ao WRF sem filtrar
```

---

## ÉPICO 17: BASE DE CRITÉRIOS DE AVALIAÇÃO (4 cards ativos + 3 cancelados, 26 SP)
**Objetivo:** Base estruturada de critérios de avaliação — "coração do sistema" segundo André
**Sprint Alvo:** 6-11
**Prioridade:** 🔴 Crítica — GAME CHANGER
**Dependências:** WDT-016 é independente (pode começar em paralelo)

> **⚠️ NOTA DE IMPLEMENTAÇÃO (08 Fev 2026):** A Fase 3 foi implementada no protótipo Replit com 4 cards core (WDT-016, WDT-018, WDT-021, WDT-022) e 34 testes unitários passando. 3 cards de interface admin (WDT-017, WDT-019, WDT-020) foram CANCELADOS conforme filosofia de design: sistema auto-evolutivo sem interfaces manuais.

---

### CARD WDT-016: Schema e Modelo da Base de Critérios
**Épico:** É17 — Base de Critérios de Avaliação

```yaml
Titulo: "[BE] Schema e modelo da base de critérios de avaliação"
Tipo: Story
Sprint: 6
Pontos: 8
Horas: 16
Prioridade: Crítica
Epic: EPIC-17 (Base de Critérios de Avaliação)
Fase: Fase 3 - Base Critérios
Status: ✅ Implementado (Replit)
Labels: criteria, game-changer, core

Descricao: |
  Criar schema do banco de dados para a base de critérios de avaliação.
  
  Contexto: André classificou como GAME CHANGER. Esta base será o coração 
  do sistema e diferencial competitivo impossível de copiar.
  
  Schema (ORIGINAL — ver Implementação Realizada abaixo):
  Table: evaluation_criteria
  - id (PK)
  - name (string) - ex: 'Senioridade em Tech'
  - category (string) - ex: 'Técnico', 'Comportamental', 'Liderança'
  - subcategory (string, nullable)
  - positive_evidences (jsonb) - array de evidências positivas
  - negative_evidences (jsonb) - array de evidências negativas
  - weight (integer, 1-10)
  - qualification_levels (array) - quais níveis se aplicam
  - effectiveness_score (float) - atualizado por aprendizado
  - status (enum) - rascunho/validado/arquivado
  - company_id (FK, nullable) - null = global, preenchido = company-specific

  IMPLEMENTAÇÃO REALIZADA (Protótipo Replit — Python/FastAPI):
  Modelo SQLAlchemy em lia-agent-system/app/models/evaluation_criteria.py
  Table: evaluation_criteria
  - id (UUID PK)
  - name (String 300, indexed)
  - category (String 50, indexed) — categories: technical_skill, behavioral_competency, experience, education, certification, language, responsibility
  - subcategory (String 100, nullable)
  - positive_evidences (JSONB) — array de evidências positivas
  - negative_evidences (JSONB) — array de evidências negativas
  - evaluation_guidelines (Text, nullable) — diretrizes de avaliação
  - effectiveness_score (Float, default 0.5) — atualizado automaticamente via feedback
  - usage_count (Integer, default 0)
  - feedback_count (Integer, default 0)
  - source (String 50, default "seed")
  - is_active (Boolean, default True) — substitui status enum (draft/validated/archived)
  - created_at, updated_at (DateTime)
  
  SEM: weight, qualification_levels, status enum, company_id
  Critérios são GLOBAIS, auto-populados dos catálogos existentes.
  
  Service em lia-agent-system/app/services/evaluation_criteria_service.py:
  - Auto-seed de TECH_SKILLS_CATALOG, BEHAVIORAL_COMPETENCIES_CATALOG, RESPONSIBILITIES_CATALOG
  - Evidence patterns por categoria (positive_templates, negative_templates, guideline_template)
  - Skill-specific evidence para Python, Java, React, AWS, SQL, Docker, Kubernetes, ML, Liderança, Comunicação
  - Fuzzy matching via SequenceMatcher para requirement→criteria lookup
  - Effectiveness auto-updated via feedback (update_effectiveness method)

Historia de Usuario: |
  Como plataforma, eu preciso de uma base estruturada de critérios 
  de avaliação para guiar a LLM na análise de candidatos com diretrizes
  claras e baseadas em expertise de RH sênior.

Requisitos Tecnicos:
  Backend (Rails):
    - Migration: db/migrate/xxx_create_evaluation_criteria.rb
    - Model: app/models/evaluation_criterion.rb
    - Controller: app/controllers/api/v1/evaluation_criteria_controller.rb
    - Serializer: app/serializers/evaluation_criterion_serializer.rb
    - Seeds: db/seeds/evaluation_criteria.rb (10 critérios exemplo)
    - Validações: name presence, weight 1-10, category inclusion

DoD:
  - [x] Migration executada (SQLAlchemy model no protótipo Replit)
  - [x] Modelo com validações (EvaluationCriteria SQLAlchemy)
  - [x] Auto-seed com catálogos existentes (TECH_SKILLS, BEHAVIORAL, RESPONSIBILITIES)
  - [x] Fuzzy matching para lookup de critérios
  - [x] Effectiveness auto-update via feedback
  - [ ] Modelo Rails com validações (produção — equipe externa)
  - [ ] CRUD API funcional (produção)
  - [ ] Testes de modelo e controller (produção)

Criterios de Aceitacao:
  - [x] Base de critérios auto-populada dos catálogos
  - [x] Evidence patterns por categoria
  - [x] Fuzzy matching funcional
  - [x] Effectiveness score atualizado via feedback
  - [ ] Scoping por company_id (produção — não necessário no protótipo)
  - [ ] Testes RSpec passando (produção)

Dependencias: Nenhuma
Bloqueia: WDT-018, WDT-021, WDT-022, WDT-027

Arquivos Implementados (Prototipo Replit):
  - lia-agent-system/app/models/evaluation_criteria.py
  - lia-agent-system/app/services/evaluation_criteria_service.py

Arquivos de Referencia (Prototipo Replit):
  - skills_catalog_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/skills_catalog_service.py
  - skills_catalog.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/skills_catalog.py
  - responsibilities_catalog_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/responsibilities_catalog_service.py
```

##### Prompt para IA (Cursor/VSCode) — WDT-016

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x
- Banco: PostgreSQL
- Testes: RSpec

---

TAREFA: Criar schema completo para base de critérios de avaliação.
ESTE É O GAME CHANGER — diferencial competitivo impossível de copiar.

IMPLEMENTAÇÃO:

1. Migration:
   create_table :evaluation_criteria do |t|
     t.string :name, null: false
     t.string :category, null: false  # Técnico, Comportamental, Liderança
     t.string :subcategory
     t.jsonb :positive_evidences, default: []  # ["5+ anos gerenciando equipes", ...]
     t.jsonb :negative_evidences, default: []  # ["Nunca liderou diretamente", ...]
     t.integer :weight, default: 5  # 1-10
     t.string :qualification_levels, array: true, default: []  # ["alta", "media"]
     t.float :effectiveness_score, default: 0.5  # 0-1, atualizado por aprendizado
     t.integer :status, default: 0  # enum: draft/validated/archived
     t.references :company, foreign_key: true, null: true  # null = global
     t.timestamps
   end
   add_index :evaluation_criteria, :category
   add_index :evaluation_criteria, :status
   add_index :evaluation_criteria, :company_id

2. Model:
   class EvaluationCriterion < ApplicationRecord
     enum status: { draft: 0, validated: 1, archived: 2 }
     validates :name, presence: true, uniqueness: { scope: :company_id }
     validates :weight, inclusion: { in: 1..10 }
     validates :category, inclusion: { in: %w[tecnico comportamental lideranca cultural] }
     scope :global, -> { where(company_id: nil) }
     scope :for_company, ->(id) { where(company_id: [nil, id]) }
     scope :for_level, ->(level) { where("? = ANY(qualification_levels)", level) }
     scope :active, -> { where(status: :validated) }
   end

3. Seeds com 10 critérios exemplo cobrindo:
   - Técnico: "Profundidade Técnica", "Arquitetura de Sistemas"
   - Comportamental: "Comunicação Executiva", "Adaptabilidade"
   - Liderança: "Gestão de Equipes", "Visão Estratégica"

NÃO FAZER:
- NÃO usar relação has_many para evidências (JSONB é mais flexível)
- NÃO esquecer company_id nullable (critérios globais vs company-specific)
```

---

### CARD WDT-017: Interface Admin para Gestão de Critérios — ❌ CANCELADO
**Épico:** É17 — Base de Critérios de Avaliação

> **❌ CANCELADO (08 Fev 2026):** Cancelado conforme filosofia de design: sistema auto-evolutivo sem interfaces de admin. Critérios são auto-populados dos catálogos existentes (TECH_SKILLS_CATALOG, BEHAVIORAL_COMPETENCIES_CATALOG, RESPONSIBILITIES_CATALOG) e auto-atualizados via feedback. Nenhuma entrada manual necessária.

```yaml
Titulo: "[FE] Interface admin para gestão de critérios"
Tipo: Story
Sprint: 7
Pontos: 8
Horas: 16
Prioridade: Alta
Epic: EPIC-17 (Base de Critérios de Avaliação)
Fase: Fase 3 - Base Critérios
Status: ❌ Cancelado (não implementado)
Labels: criteria, admin, ux

Descricao: |
  Criar interface administrativa para RH sênior cadastrar e gerenciar 
  critérios de avaliação.
  
  Implementação:
  - Tela de listagem com filtros (categoria, peso, status)
  - Formulário de criação com campos dinâmicos para evidências
  - Adicionar/remover evidências positivas e negativas (array)
  - Seleção de peso e qualification_levels
  - Status: rascunho → validado
  - Busca e ordenação na listagem
  - Preview de como o critério será usado pelo LLM

Requisitos Tecnicos:
  Frontend (Vue.js 3 + Vuetify 3):
    - Página: src/pages/admin/EvaluationCriteria.vue
    - Componentes: CriterionForm.vue, CriterionCard.vue, EvidenceList.vue
    - Vuetify: v-data-table, v-dialog, v-chip-group, v-combobox

DoD:
  - [ ] CRUD completo funcional na UI
  - [ ] Campos dinâmicos para evidências
  - [ ] Filtros e busca na listagem
  - [ ] Workflow de validação
  - [ ] Responsivo

Criterios de Aceitacao:
  - [ ] Listar critérios com filtros funcionais
  - [ ] Criar critério com evidências dinâmicas
  - [ ] Editar e arquivar critérios
  - [ ] Mudar status draft → validated
  - [ ] Preview do prompt LLM

Dependencias: WDT-016
Bloqueia: WDT-020

Arquivos de Referencia (Prototipo Replit):
  - AdminTemplateHub.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/admin/AdminTemplateHub.tsx
  - skills_catalog_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/skills_catalog_service.py
  - skills_catalog.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/skills_catalog.py
```

##### Prompt para IA (Cursor/VSCode) — WDT-017

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Vue.js 3 + Vuetify 3 + Nuxt 3
- Testes: Vitest

---

TAREFA: Criar interface admin para gestão de critérios de avaliação.

IMPLEMENTAÇÃO:

1. Página principal: src/pages/admin/EvaluationCriteria.vue
   - v-data-table-server com colunas: Nome, Categoria, Peso, Status, Ações
   - Filtros: v-select categoria, v-slider peso, v-select status
   - v-text-field busca por nome
   - v-btn "Novo Critério" abre v-dialog com formulário

2. Formulário CriterionForm.vue:
   - v-text-field: nome
   - v-select: categoria (Técnico, Comportamental, Liderança, Cultural)
   - v-slider: peso (1-10)
   - v-chip-group: qualification_levels (Alta, Média, Baixa) - multi-select
   - EvidenceList (componente dinâmico):
     - Lista de v-text-field para cada evidência
     - v-btn "Adicionar evidência" (append)
     - v-btn icon "Remover" (splice)
     - Seção "Evidências Positivas" e "Evidências Negativas" separadas
   - Preview section: mostra como o critério será formatado no prompt LLM

3. EvidenceList.vue (componente reutilizável):
   - Props: modelValue (string[]), label, color
   - v-for com v-text-field para cada item
   - Botão adicionar/remover
   - Emit 'update:modelValue'

NÃO FAZER:
- NÃO usar textarea para evidências (uma por campo)
- NÃO permitir salvar sem pelo menos 1 evidência positiva
```

---

### CARD WDT-018: Integração de Critérios com Prompt da LLM
**Épico:** É17 — Base de Critérios de Avaliação

```yaml
Titulo: "[BE] Integração de critérios com prompt da LLM"
Tipo: Story
Sprint: 8
Pontos: 8
Horas: 14
Prioridade: Crítica
Epic: EPIC-17 (Base de Critérios de Avaliação)
Fase: Fase 3 - Base Critérios
Status: ✅ Implementado (Replit)
Labels: criteria, llm, core

Descricao: |
  Integrar a base de critérios com os prompts de avaliação da LLM (Gemini).
  
  Contexto: Injetar critérios relevantes no prompt para que a LLM tenha 
  diretrizes claras sobre o que constitui evidência forte, fraca ou negativa.
  
  Implementação (ORIGINAL):
  - Selecionar critérios relevantes baseado na vaga (categoria, qualification_level)
  - Formatar critérios como seção estruturada do prompt
  - Incluir evidências positivas e negativas como exemplos
  - Controlar tamanho do prompt (não injetar todos)
  - Ranking de critérios por relevância para a vaga
  - Benchmark de custo de tokens antes/depois

  IMPLEMENTAÇÃO REALIZADA (Protótipo Replit):
  Arquivo: lia-agent-system/app/services/rubric_evaluation_service.py
  - Método _format_criteria_examples() injeta critérios no RUBRIC_EVALUATION_PROMPT
  - Fuzzy matching via EvaluationCriteriaService.get_criteria_for_requirements()
  - Critérios formatados com evidências positivas E negativas como exemplos
  - Instrução "DO NOT INFER" explicitamente adicionada ao prompt
  - Classificação de tipo de evidência (explicit/implicit/inferred) requerida por requisito
  - Detecção de linguagem vaga dispara downgrade automático
  - Integração com metodologia de scoring do André

Requisitos Tecnicos:
  Backend (Python FastAPI):
    - Service: app/services/ai/criteria_prompt_builder.py
    - Selecionar top N critérios por relevância
    - Formatar como seção do prompt
    - Controlar max_tokens dedicados a critérios (< 20% do prompt total)
  Testes:
    - pytest: tests/test_criteria_prompt_builder.py

DoD:
  - [ ] Critérios injetados no prompt dinamicamente
  - [ ] Seleção inteligente por relevância
  - [ ] Custo de tokens controlado (< 20% aumento)
  - [ ] Melhoria mensurável na qualidade das avaliações
  - [ ] Testes A/B com/sem critérios

Criterios de Aceitacao:
  - [ ] Prompt inclui critérios relevantes para a vaga
  - [ ] Max 10 critérios por prompt (controle de tokens)
  - [ ] Evidências positivas e negativas incluídas
  - [ ] Custo de tokens < 20% aumento vs. sem critérios

Dependencias: WDT-016
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - skills_catalog_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/skills_catalog_service.py
  - nodes.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/agents/nodes.py
  - job_wizard_tools.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/tools/job_wizard_tools.py

Arquivos Implementados (Prototipo Replit):
  - lia-agent-system/app/services/rubric_evaluation_service.py (linhas ~524-556 para _format_criteria_examples, linhas ~327-520 para RUBRIC_EVALUATION_PROMPT)
```

##### Prompt para IA (Cursor/VSCode) — WDT-018

```
CONTEXTO DO PROJETO WEDO TALENT:
- IA: Python 3.11 + FastAPI + LangChain + Gemini 2.5 Flash
- Banco: PostgreSQL (acessado via Rails API)

---

TAREFA: Integrar base de critérios com prompts de avaliação da LLM.

IMPLEMENTAÇÃO:

1. Service Python:
   app/services/ai/criteria_prompt_builder.py

   class CriteriaPromptBuilder:
     MAX_CRITERIA = 10
     
     def build(self, job_data: dict, criteria: list[dict]) -> str:
       relevant = self._select_relevant(job_data, criteria)
       return self._format_prompt_section(relevant[:self.MAX_CRITERIA])
     
     def _select_relevant(self, job_data, criteria):
       level = job_data.get('qualification_level', 'media')
       category_match = [c for c in criteria 
                         if level in c['qualification_levels']]
       return sorted(category_match, key=lambda c: -c['weight'])
     
     def _format_prompt_section(self, criteria):
       sections = []
       for c in criteria:
         sections.append(f"""
         CRITÉRIO: {c['name']} (Peso: {c['weight']}/10)
         Categoria: {c['category']}
         Evidências FORTES (o que procurar): {', '.join(c['positive_evidences'])}
         Evidências FRACAS (sinais negativos): {', '.join(c['negative_evidences'])}
         """)
       return "\\n".join(sections)

2. Injeção no prompt principal de avaliação:
   - Adicionar seção "CRITÉRIOS DE AVALIAÇÃO" antes das instruções de análise
   - LLM deve referenciar critérios na justificativa

NÃO FAZER:
- NÃO injetar todos os critérios (controlar tokens)
- NÃO chamar Rails DB diretamente do Python (usar API)
```

---

### CARD WDT-019: Dashboard de Gestão e Métricas de Critérios — ❌ CANCELADO
**Épico:** É17 — Base de Critérios de Avaliação

> **❌ CANCELADO (08 Fev 2026):** Cancelado conforme filosofia de design: inteligência auto-evolutiva sem dashboards de admin. Effectiveness score é atualizado automaticamente via feedback. Métricas são coletadas de forma transparente pelo sistema.

```yaml
Titulo: "[BE/FE] Dashboard de gestão e métricas de critérios"
Tipo: Story
Sprint: 9
Pontos: 5
Horas: 10
Prioridade: Média
Epic: EPIC-17 (Base de Critérios de Avaliação)
Fase: Fase 3 - Base Critérios
Status: ❌ Cancelado (não implementado)
Labels: criteria, analytics

Descricao: |
  Dashboard para acompanhar uso e efetividade dos critérios.
  
  Métricas:
  - Critérios mais utilizados
  - Critérios com melhor taxa de like/dislike
  - Cobertura de critérios por categoria de vaga
  - Critérios sem uso (candidatos a remoção)
  - Evolução ao longo do tempo

Requisitos Tecnicos:
  Backend (Rails):
    - Service: app/services/analytics/criteria_analytics_service.rb
    - Queries agregadas cruzando critérios com feedbacks
  Frontend (Vue.js 3 + Vuetify 3):
    - Página: src/pages/admin/CriteriaDashboard.vue
    - Gráficos com ApexCharts

DoD:
  - [ ] Dashboard funcional e responsivo
  - [ ] Métricas atualizadas em real-time
  - [ ] Filtros por período e categoria

Criterios de Aceitacao:
  - [ ] Top 10 critérios mais usados exibidos
  - [ ] Taxa de efetividade por critério
  - [ ] Critérios sem uso destacados
  - [ ] Filtros funcionais

Dependencias: WDT-016, WDT-006
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - AdminTemplateHub.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/admin/AdminTemplateHub.tsx
  - strategic-dashboard.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/dashboard/strategic-dashboard.tsx
  - skills_catalog_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/skills_catalog_service.py
```

##### Prompt para IA (Cursor/VSCode) — WDT-019

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x + Vue.js 3 + Vuetify 3
- Cache: Redis

---

TAREFA: Criar dashboard de métricas de critérios de avaliação.

IMPLEMENTAÇÃO:

Backend:
- Service cruzando evaluation_criteria com candidate_feedbacks
- Métricas: uso por critério, efetividade (like rate quando critério usado),
  cobertura por categoria, critérios sem uso

Frontend:
- ApexCharts para gráficos de barras e donut
- v-data-table para listagem detalhada
- Filtros por período e categoria
```

---

### CARD WDT-020: Alimentação Inicial com RH Sênior — ❌ CANCELADO / SUBSTITUÍDO
**Épico:** É17 — Base de Critérios de Avaliação

> **❌ CANCELADO / SUBSTITUÍDO (08 Fev 2026):** Substituído por auto-seed automático dos catálogos existentes. O sistema se auto-popula com critérios gerados a partir de TECH_SKILLS_CATALOG (~hundreds de skills), BEHAVIORAL_COMPETENCIES_CATALOG (~dozens de competências com subcategories), e RESPONSIBILITIES_CATALOG. Nenhum workshop manual ou importação CSV necessária. Evidence patterns são gerados automaticamente com templates por categoria.

```yaml
Titulo: "[DATA] Alimentação inicial: 50-100 critérios com RH sênior"
Tipo: Task
Sprint: 9-10
Pontos: 13
Horas: 40
Prioridade: Alta
Epic: EPIC-17 (Base de Critérios de Avaliação)
Fase: Fase 3 - Base Critérios
Status: ❌ Cancelado / Substituído
Labels: criteria, data, onboarding

Descricao: |
  Workshop com equipe de RH sênior da Talenses para alimentar a base 
  inicial de critérios.
  
  Atividades:
  - 3-4 sessões de 2h com RH sênior
  - Mapear critérios para vagas de alta, média e baixa qualificação
  - Definir evidências positivas e negativas para cada critério
  - Validar pesos e categorias
  - Documentar processo para futuras alimentações
  
  Meta: 50-100 critérios validados cobrindo as principais categorias.

Requisitos Tecnicos:
  Processo:
    - Template de captura: planilha/formulário padronizado
    - Script de importação: lib/tasks/import_criteria.rake
    - Validação automática de formato e completude
  Dados:
    - Critérios cobrindo todas as categorias: Técnico, Comportamental, Liderança, Cultural
    - Critérios para os 3 níveis de qualificação
    - Mínimo 3 evidências positivas e 2 negativas por critério

DoD:
  - [ ] Mínimo 50 critérios cadastrados e validados
  - [ ] Cobertura de todas as categorias principais
  - [ ] Critérios para os 3 níveis de qualificação
  - [ ] Documentação do processo

Criterios de Aceitacao:
  - [ ] 50+ critérios com status "validated"
  - [ ] Cada critério com 3+ evidências positivas
  - [ ] Cada critério com 2+ evidências negativas
  - [ ] Cobertura dos 3 níveis (alta, média, baixa)
  - [ ] Processo documentado para futuras sessões

Dependencias: WDT-017
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - skills_catalog_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/skills_catalog_service.py
  - template_importer_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/template_importer_service.py
  - learning_loop_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/learning_loop_service.py
```

##### Prompt para IA (Cursor/VSCode) — WDT-020

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x

---

TAREFA: Criar script de importação massiva de critérios de avaliação.

IMPLEMENTAÇÃO:

1. Rake task: lib/tasks/import_criteria.rake
   - Ler CSV/XLSX com colunas: nome, categoria, subcategoria, evidencias_positivas,
     evidencias_negativas, peso, niveis_qualificacao
   - Validar formato e completude
   - Criar registros via EvaluationCriterion
   - Log de importação com sucesso/erros

2. Template CSV para workshops:
   name,category,subcategory,positive_evidences,negative_evidences,weight,levels
   "Senioridade Tech","tecnico","","5+ anos|Liderou projetos","Sem experiência",8,"alta,media"

3. Validações na importação:
   - Nome obrigatório e único
   - Mínimo 3 evidências positivas
   - Mínimo 2 evidências negativas
   - Peso 1-10
   - Categoria válida

NÃO FAZER:
- NÃO importar sem validação
- NÃO sobrescrever critérios existentes sem flag --force
```

---

### CARD WDT-021: Sistema de Classificação Explicit/Implicit/Inferred
**Épico:** É17 — Base de Critérios de Avaliação

```yaml
Titulo: "[BE] Sistema de classificação Explicit/Implicit/Inferred"
Tipo: Story
Sprint: 10
Pontos: 5
Horas: 10
Prioridade: Alta
Epic: EPIC-17 (Base de Critérios de Avaliação)
Fase: Fase 3 - Base Critérios
Status: ✅ Implementado (Replit)
Labels: evidence, llm, quality

Descricao: |
  Implementar sistema de tipos de evidência na avaliação LLM.
  
  Contexto: André propôs 3 níveis:
  - Explicit: candidato atende critério conforme diretriz (mais confiável)
  - Implicit: parece atender mas sem confirmação direta
  - Inferred: LLM inferiu baseado em interpretação (perigoso)
  
  Implementação (ORIGINAL):
  - Atualizar prompt para LLM retornar match_level por requisito
  - Schema: {requirement, match_level, evidence_text, confidence}
  - Requisitos essenciais: apenas 'explicit' aceito
  - Diferenciais: 'implicit' e 'inferred' aceitos com peso reduzido
  - Filtrar/penalizar 'inferred' automaticamente no score

  IMPLEMENTAÇÃO REALIZADA (Protótipo Replit — todos os 8 mecanismos do André):
  1. EvidenceType enum (explicit, implicit, inferred) em app/schemas/rubric.py
  2. Evidence weights: explicit=1.0, implicit=0.7, inferred=0.3
  3. Detecção de linguagem vaga: 18 indicadores bilíngues
     PT: "pode ter", "indica que", "sugere", "provavelmente", "talvez", "aparentemente", "possivelmente", "parece que", "supostamente"
     EN: "probably", "suggests", "may have", "might", "possibly", "appears to", "seems", "likely", "could have"
  4. Auto-downgrade: linguagem vaga → evidence_type vira "inferred" com confidence máx 0.3
  5. Anomaly flags: exceeds_ratio (>80% exceeds), skills_ratio (competencies_count < skills_matched), inferred_meets_exceeds (inferred mas meets/exceeds), low_experience_high_score
  6. Regra de exclusão essential: se QUALQUER requisito essential tem level="missing" OU (level="partial/meets/exceeds" E evidence_type!="explicit") → auto_excluded=True, score=0 antes do WRF
  7. Confidence scoring: 0.0-1.0 por requisito

Requisitos Tecnicos:
  Backend (Python FastAPI):
    - Atualizar prompt de avaliação
    - Pydantic model para resposta estruturada
    - Penalização: explicit=1.0, implicit=0.7, inferred=0.3
  Testes:
    - pytest com diferentes tipos de currículos

DoD:
  - [x] LLM retorna match_level para cada requisito (EvidenceType enum)
  - [x] Filtro de essenciais apenas com explicit (regra de exclusão automática)
  - [x] Penalização de inferred implementada (EVIDENCE_WEIGHTS)
  - [x] Detecção de linguagem vaga (18 indicadores bilíngues)
  - [x] Anomaly flags implementados
  - [x] Testes passando (34 testes, 13 classes)

Criterios de Aceitacao:
  - [x] Resposta inclui evidence_type para cada requisito
  - [x] Requisitos essenciais rejeitam implicit/inferred (auto-exclusão)
  - [x] Score penalizado para inferred (weight 0.3)
  - [x] Linguagem vaga detectada e downgradada automaticamente
  - [x] Anomaly flags gerados para padrões suspeitos
  - [x] Testes passando

Dependencias: WDT-016
Bloqueia: WDT-022, WDT-023

Arquivos de Referencia (Prototipo Replit):
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - lia_score_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/lia_score_service.py
  - confidence_policy_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/confidence_policy_service.py

Arquivos Implementados (Prototipo Replit):
  - lia-agent-system/app/schemas/rubric.py (EvidenceType enum, RequirementEvaluation com evidence_type/confidence/vague_language_detected/anomaly_flags)
  - lia-agent-system/app/services/rubric_evaluation_service.py (_detect_vague_language, _detect_anomalies, evidence weight application)
```

##### Prompt para IA (Cursor/VSCode) — WDT-021

```
CONTEXTO DO PROJETO WEDO TALENT:
- IA: Python 3.11 + FastAPI + LangChain + Gemini 2.5 Flash

---

TAREFA: Implementar classificação de tipo de evidência (Explicit/Implicit/Inferred).

IMPLEMENTAÇÃO:

1. Pydantic model:
   class RequirementMatch(BaseModel):
     requirement: str
     match_level: Literal["explicit", "implicit", "inferred"]
     evidence_text: str
     confidence: float  # 0-1

2. Prompt atualizado:
   "Para cada requisito, classifique o nível de evidência:
   - EXPLICIT: O currículo CONFIRMA diretamente este requisito com dados concretos
   - IMPLICIT: O currículo SUGERE este requisito mas sem confirmação direta
   - INFERRED: Você está INFERINDO com base em interpretação (MARQUE COMO TAL)
   
   REGRA: Para requisitos ESSENCIAIS, apenas EXPLICIT é aceito."

3. Penalização no score:
   WEIGHTS = {"explicit": 1.0, "implicit": 0.7, "inferred": 0.3}
   adjusted_score = raw_score * WEIGHTS[match_level]

NÃO FAZER:
- NÃO aceitar inferred para requisitos essenciais
- NÃO tratar implicit e explicit como iguais
```

---

### CARD WDT-022: Score de Confiança Individual por Requisito
**Épico:** É17 — Base de Critérios de Avaliação

```yaml
Titulo: "[BE/FE] Score de confiança individual por requisito"
Tipo: Story
Sprint: 11
Pontos: 5
Horas: 10
Prioridade: Média
Epic: EPIC-17 (Base de Critérios de Avaliação)
Fase: Fase 3 - Base Critérios
Status: ✅ Implementado (Replit)
Labels: evidence, transparency

Descricao: |
  Implementar score individual por requisito ao invés de score único.
  
  Implementação (ORIGINAL):
  - LLM retorna score 0-100 por requisito obrigatório
  - Armazenar breakdown: {requirement: score, match_level, evidence}
  - UI: expandir card do candidato para ver breakdown
  - Score total = média ponderada dos individuais

  IMPLEMENTAÇÃO REALIZADA (Protótipo Replit — fórmulas do André):
  - adjusted_score = points × EVIDENCE_WEIGHTS[evidence_type]
  - final_score = min(99.0, floor(Σ(score_i × weight_i × evidence_weight_i) / Σ(100 × weight_i)))
  - Cap 99: score máximo nunca é 100 (garante margem para revisão humana)
  - Floor rounding: scores arredondados para inteiros (elimina ruído decimal, ex: 84.98 → 84)
  - raw_score: preservado para transparência antes de cap/floor
  - Auto-exclusão: requisito essential com missing ou evidence não-explicit → score=0, auto_excluded=True
  - Scoring methodology tagged como "andre_v1"
  - RubricEvaluationResult schema inclui: score, raw_score, auto_excluded, exclusion_reasons, anomaly_flags, scoring_methodology
  - 34 testes unitários passando cobrindo todos os 8 mecanismos do André

Requisitos Tecnicos:
  Backend:
    - Atualizar response schema do avaliador LLM
    - Salvar breakdown no JSONB do candidate_evaluation
  Frontend (Vue.js 3 + Vuetify 3):
    - Componente: src/components/candidates/ScoreBreakdown.vue
    - v-expansion-panel para expandir detalhes
    - v-progress-linear por requisito com cor por match_level

DoD:
  - [x] Score por requisito retornado (RequirementEvaluation schema)
  - [x] Fórmula de scoring com evidence weights implementada
  - [x] Cap 99 com floor rounding
  - [x] Auto-exclusão para essential com missing/non-explicit evidence
  - [x] raw_score preservado para transparência
  - [x] 34 testes passando (13 classes de teste)
  - [ ] UI com breakdown expansível (produção — equipe externa)

Criterios de Aceitacao:
  - [x] Cada requisito com score individual e evidence_type
  - [x] Score ajustado por evidence weights (1.0/0.7/0.3)
  - [x] Cap 99 e floor rounding funcionando
  - [x] Auto-exclusão por requisitos essential
  - [x] Methodology tagged como "andre_v1"
  - [ ] Card expandível mostrando detalhes (produção)

Dependencias: WDT-021
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - lia_score_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/lia_score_service.py
  - confidence_policy_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/confidence_policy_service.py
  - wsi_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/wsi_service.py

Arquivos Implementados (Prototipo Replit):
  - lia-agent-system/app/services/rubric_evaluation_service.py (scoring logic, _calculate_score method)
  - lia-agent-system/app/schemas/rubric.py (RubricEvaluationResult schema com score, raw_score, auto_excluded, exclusion_reasons, anomaly_flags, scoring_methodology)
  - lia-agent-system/tests/test_phase3_andre_methodology.py (34 testes, 13 classes de teste)
```

##### Prompt para IA (Cursor/VSCode) — WDT-022

```
CONTEXTO DO PROJETO WEDO TALENT:
- Backend: Python FastAPI + Rails
- Frontend: Vue.js 3 + Vuetify 3

---

TAREFA: Implementar score individual por requisito com breakdown visual.

IMPLEMENTAÇÃO:

Backend (Python):
- LLM retorna: [{ requirement, score: 0-100, match_level, evidence_text }]
- Score total: soma ponderada (peso do requisito * score * weight_match_level) / soma pesos

Frontend (Vue):
- ScoreBreakdown.vue:
  - v-expansion-panels para expandir card do candidato
  - Para cada requisito: v-progress-linear com cor:
    - explicit: color="success"
    - implicit: color="warning"
    - inferred: color="error"
  - Label: "{requisito}: {score}% ({match_level})"
  - evidence_text em v-card-text

NÃO FAZER:
- NÃO mostrar apenas score total sem breakdown
```

---

#### FASE 3 — ARQUIVOS IMPLEMENTADOS NO PROTÓTIPO REPLIT

| Arquivo | Descrição |
|---------|-----------|
| `lia-agent-system/app/models/evaluation_criteria.py` | Modelo SQLAlchemy: EvaluationCriteria com JSONB positive/negative evidences |
| `lia-agent-system/app/services/evaluation_criteria_service.py` | Service: auto-seed, fuzzy matching, effectiveness update |
| `lia-agent-system/app/services/rubric_evaluation_service.py` | Integração com prompt LLM, scoring André, vague language, anomalies |
| `lia-agent-system/app/schemas/rubric.py` | Schemas Pydantic: EvidenceType, RequirementEvaluation, RubricEvaluationResult |
| `lia-agent-system/tests/test_phase3_andre_methodology.py` | 34 testes unitários, 13 classes de teste |

**Mecanismos do André Implementados:**
1. ✅ Base de evidências positivas/negativas para prompts (WDT-016)
2. ✅ Classificação explicit/implicit/inferred com pesos 1.0/0.7/0.3 (WDT-021)
3. ✅ Detecção de linguagem vaga — 18 indicadores bilíngues PT/EN (WDT-021)
4. ✅ Flags de anomalia — exceeds_ratio, skills_ratio, inferred meets/exceeds, low experience (WDT-021)
5. ✅ Exclusão automática — essential missing OR essential com evidence!=explicit → score=0 (WDT-022)
6. ✅ Cap 99 com floor rounding (WDT-022)
7. ✅ Confidence score por requisito 0.0-1.0 (WDT-021)
8. ✅ Instrução explícita "DO NOT INFER" no prompt (WDT-018)

---

## ÉPICO 18: APRENDIZADO E FEATURES AVANÇADAS (6 cards, 42 SP)
**Objetivo:** Sistema auto-evolutivo + features de alto valor para executive search
**Sprint Alvo:** 12-17
**Prioridade:** 🟠 Alta
**Dependências:** ÉPICO 17 (Base de Critérios) e WDT-006 (Like/Dislike)

---

### CARD WDT-023: Toggle de Requisito Essencial Excludente
**Épico:** É18 — Aprendizado e Features Avançadas

```yaml
Titulo: "[BE/FE] Toggle de requisito essencial excludente"
Tipo: Story
Sprint: 12
Pontos: 5
Horas: 8
Prioridade: Alta
Epic: EPIC-18 (Aprendizado e Features Avançadas)
Fase: Fase 4 - Features Avançadas
Status: 📋 Pendente Jira
Labels: requirements, filter, quality

Descricao: |
  Permitir que recrutador marque requisitos como excludentes (no-go).
  
  Contexto: André questionou se 'essencial' é excludente ou apenas valorizado.
  
  Implementação:
  - Toggle na UI de criação de vaga: 'Este requisito é excludente'
  - Backend: se requisitos_essenciais_atendidos < threshold, excluir candidato
  - Excluir ANTES do WRF (economia de processamento)
  - Log de candidatos excluídos por requisitos não atendidos

Requisitos Tecnicos:
  Backend (Rails):
    - Adicionar campo is_excludent (boolean) no modelo JobRequirement
    - Filtro pré-WRF: verificar requisitos excludentes com match_level=explicit
  Frontend (Vue.js 3 + Vuetify 3):
    - v-switch no formulário de requisitos da vaga
    - Label: "Excludente (candidato sem este requisito será eliminado)"

DoD:
  - [ ] Toggle funcional na criação de vaga
  - [ ] Candidatos excluídos antes do WRF
  - [ ] Log de exclusões acessível
  - [ ] Threshold configurável

Criterios de Aceitacao:
  - [ ] Toggle visível e funcional
  - [ ] Candidatos sem requisito excludente não aparecem
  - [ ] Exclusão antes do WRF (economia)
  - [ ] Log com candidatos excluídos

Dependencias: WDT-021
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - advanced-search.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/advanced-search.tsx
  - SkillsFilterInput.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/search/SkillsFilterInput.tsx
```

##### Prompt para IA (Cursor/VSCode) — WDT-023

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x + Vue.js 3 + Vuetify 3

---

TAREFA: Implementar toggle de requisito excludente na criação de vaga.

IMPLEMENTAÇÃO:

Backend (Rails):
1. Migration: add_column :job_requirements, :is_excludent, :boolean, default: false
2. No pipeline de busca, antes do WRF:
   - Verificar se candidato atende TODOS requisitos excludentes com match_level=explicit
   - Se não atende, excluir do pipeline
   - Log: "[Excludent] Candidate #{id} excluded: missing #{requirement}"

Frontend (Vue):
1. No formulário de requisitos da vaga:
   v-switch v-model="requirement.is_excludent"
   label="Excludente" hint="Candidato será eliminado sem este requisito"
   color="error"
```

---

### CARD WDT-024: Enriquecimento de Perfil Sob Demanda via Web
**Épico:** É18 — Aprendizado e Features Avançadas

```yaml
Titulo: "[BE] Enriquecimento de perfil sob demanda via web"
Tipo: Story
Sprint: 13
Pontos: 8
Horas: 16
Prioridade: Média
Epic: EPIC-18 (Aprendizado e Features Avançadas)
Fase: Fase 4 - Features Avançadas
Status: 📋 Pendente Jira
Labels: enrichment, executive-search

Descricao: |
  Permitir enriquecer perfil de candidato com informações da web.
  
  Fontes:
  - Google Scholar (publicações acadêmicas)
  - Escavador (referências jurídicas/acadêmicas)
  - Busca web geral (entrevistas, palestras, artigos)
  
  Implementação:
  - Botão 'Enriquecer perfil' no card do candidato
  - Background job (Sidekiq) para scraping
  - LLM analisa e estrutura informações encontradas
  - Salvar enriquecimento vinculado ao perfil
  - Rate limiting e controle de custos

Requisitos Tecnicos:
  Backend (Rails):
    - Job: app/jobs/profile_enrichment_job.rb (Sidekiq)
    - Service: app/services/candidates/profile_enrichment_service.rb
    - Model: app/models/candidate_enrichment.rb
    - Fontes: Google Scholar API, Escavador, SerpAPI
  Python (FastAPI):
    - Endpoint para análise LLM do conteúdo coletado
  Frontend (Vue.js 3 + Vuetify 3):
    - Botão "Enriquecer perfil" no card do candidato
    - Status: pendente → processando → concluído
    - Expandir card para ver dados enriquecidos

DoD:
  - [ ] Botão funcional na UI
  - [ ] Enriquecimento async via job Sidekiq
  - [ ] Informações estruturadas e salvas
  - [ ] Controle de custos implementado

Criterios de Aceitacao:
  - [ ] Botão dispara job em background
  - [ ] Status atualizado em real-time (ActionCable/polling)
  - [ ] Dados enriquecidos visíveis no perfil
  - [ ] Rate limit: max 10 enriquecimentos/hora por company

Dependencias: Nenhuma
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - candidate_enrichment_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/candidate_enrichment_service.py
  - pearch_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/pearch_service.py
  - apify_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/apify_service.py
  - sourcing.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/api/v1/sourcing.py
```

##### Prompt para IA (Cursor/VSCode) — WDT-024

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x + Python FastAPI
- Background Jobs: Sidekiq + Redis
- IA: Gemini 2.5 Flash

---

TAREFA: Criar sistema de enriquecimento de perfil de candidato via web.

IMPLEMENTAÇÃO:

1. Job Sidekiq: app/jobs/profile_enrichment_job.rb
   - Recebe: candidate_id, company_id
   - Executa: busca em fontes web → LLM estrutura → salva
   - Rate limit: max 10/hora por company (Redis counter)

2. Service: app/services/candidates/profile_enrichment_service.rb
   - Busca Google Scholar via SerpAPI
   - Busca geral via SerpAPI
   - Envia conteúdo para FastAPI: POST /api/v1/ai/enrich-profile
   - LLM estrutura: publicações, palestras, menções, artigos

3. Model: CandidateEnrichment
   - candidate_id, source, raw_data (jsonb), structured_data (jsonb),
     status (pending/processing/completed/failed), created_at

ATENÇÃO LEGAL:
- Não fazer scraping de LinkedIn (violação ToS)
- Usar apenas fontes públicas
- Respeitar robots.txt
```

---

### CARD WDT-025: Análise Pós-Busca com Feedback de Qualidade
**Épico:** É18 — Aprendizado e Features Avançadas

```yaml
Titulo: "[BE/FE] Análise pós-busca com feedback de qualidade"
Tipo: Story
Sprint: 13
Pontos: 5
Horas: 10
Prioridade: Média
Epic: EPIC-18 (Aprendizado e Features Avançadas)
Fase: Fase 4 - Features Avançadas
Status: 📋 Pendente Jira
Labels: feedback, ux, quality

Descricao: |
  Após retornar 10 candidatos, LLM analisa qualidade geral e dá feedback.
  
  Implementação:
  - LLM avalia os 10 resultados como conjunto
  - Retorna: 'Resultados OK' ou 'Sugestão: refine sua busca'
  - Sugestões concretas de refinamento
  - Modal com feedback e sugestões
  - Botão 'Aplicar sugestão' para refinar automaticamente

Requisitos Tecnicos:
  Backend (Python FastAPI):
    - Endpoint: POST /api/v1/ai/analyze-search-quality
    - Recebe: candidatos retornados, query original, vaga
    - Retorna: quality_score, suggestions[], is_satisfactory
  Frontend (Vue.js 3 + Vuetify 3):
    - Componente: SearchQualityFeedback.vue
    - v-dialog com sugestões
    - v-btn "Aplicar sugestão" para cada sugestão

DoD:
  - [ ] Análise automática após busca
  - [ ] Feedback claro ao usuário
  - [ ] Sugestões de refinamento concretas
  - [ ] Modal funcional

Criterios de Aceitacao:
  - [ ] Análise executa após cada busca
  - [ ] Sugestões específicas (não genéricas)
  - [ ] Botão "Aplicar" funcional
  - [ ] Não bloqueia fluxo (assíncrono)

Dependencias: WDT-016
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - candidate_feedback_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/candidate_feedback_service.py
  - search_analytics_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/search_analytics_service.py
  - feedback_learning_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/feedback_learning_service.py
```

##### Prompt para IA (Cursor/VSCode) — WDT-025

```
CONTEXTO DO PROJETO WEDO TALENT:
- IA: Python FastAPI + Gemini 2.5 Flash
- Frontend: Vue.js 3 + Vuetify 3

---

TAREFA: Criar análise pós-busca com feedback de qualidade.

IMPLEMENTAÇÃO:

Backend (Python):
- Endpoint: POST /api/v1/ai/analyze-search-quality
- Prompt: "Analise estes 10 candidatos retornados para a vaga '{title}'.
  Avalie: diversidade de perfis, cobertura de requisitos, gaps evidentes.
  Retorne: { quality_score: 0-100, is_satisfactory: bool,
  suggestions: [{ text: 'Considere ampliar...', action: 'add_keyword:python' }] }"

Frontend (Vue):
- Componente que aparece após resultados carregarem
- v-alert type="info" se satisfatório
- v-dialog com lista de sugestões se não satisfatório
- v-btn para cada sugestão que modifica a query automaticamente
```

---

### CARD WDT-026: Flags Automáticas de Inconsistência
**Épico:** É18 — Aprendizado e Features Avançadas

```yaml
Titulo: "[BE] Flags automáticas de inconsistência"
Tipo: Story
Sprint: 14
Pontos: 3
Horas: 6
Prioridade: Média
Epic: EPIC-18 (Aprendizado e Features Avançadas)
Fase: Fase 4 - Features Avançadas
Status: 📋 Pendente Jira
Labels: quality, flags, heuristics

Descricao: |
  Implementar flags automáticas para detectar inconsistências na avaliação.
  
  Regras heurísticas:
  - Currículo com < 3 competências marcado como 'exceeded' em 5+ requisitos
  - Currículo com < 50 palavras atendendo requisitos complexos
  - Score > 95% em vaga altamente qualificada com perfil incompleto
  - Discrepância > 40% entre score ES e score PGV para mesmo candidato

Requisitos Tecnicos:
  Backend (Rails):
    - Service: app/services/search/inconsistency_detector.rb
    - Flag model ou campo JSONB no candidate_evaluation
    - Regras configuráveis (não hardcoded)
  Frontend:
    - v-chip color="warning" icon="mdi-alert" no card do candidato flagado

DoD:
  - [ ] Regras heurísticas implementadas
  - [ ] Flag visível no card do candidato
  - [ ] Candidatos flagados separados/destacados
  - [ ] Dashboard de anomalias

Criterios de Aceitacao:
  - [ ] 4 regras heurísticas implementadas
  - [ ] Flags visíveis no card
  - [ ] Admin pode ver todos os flagados
  - [ ] Regras configuráveis

Dependencias: Nenhuma
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - search_analytics_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/search_analytics_service.py
  - proactive_alert_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/proactive_alert_service.py
```

##### Prompt para IA (Cursor/VSCode) — WDT-026

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x
- Banco: PostgreSQL

---

TAREFA: Implementar detecção automática de inconsistências em avaliações.

IMPLEMENTAÇÃO:

1. Service: app/services/search/inconsistency_detector.rb

   RULES = [
     { name: "low_competencies_high_score",
       condition: ->(eval) { eval.competencies_count < 3 && eval.exceeded_count >= 5 },
       message: "Poucas competências mas muitos requisitos excedidos" },
     { name: "short_cv_complex_match",
       condition: ->(eval) { eval.cv_word_count < 50 && eval.complex_requirements_met > 3 },
       message: "CV muito curto atendendo requisitos complexos" },
     { name: "suspiciously_high_score",
       condition: ->(eval) { eval.score > 95 && eval.qualification_level == 'alta' && eval.profile_incomplete? },
       message: "Score muito alto para perfil incompleto em vaga executive" },
     { name: "source_score_discrepancy",
       condition: ->(eval) { (eval.es_score - eval.pgv_score).abs > 40 },
       message: "Discrepância significativa entre ES e PGV" }
   ]

2. Executar após cada avaliação, salvar flags em JSONB
3. Frontend: v-chip color="warning" no card com tooltip da mensagem
```

---

### CARD WDT-027: Motor de Aprendizado via Feedback
**Épico:** É18 — Aprendizado e Features Avançadas

```yaml
Titulo: "[BE] Motor de aprendizado via feedback (Like/Dislike)"
Tipo: Story
Sprint: 15-16
Pontos: 13
Horas: 24
Prioridade: Alta
Epic: EPIC-18 (Aprendizado e Features Avançadas)
Fase: Fase 5 - Aprendizado
Status: 📋 Pendente Jira
Labels: learning, evolution, core

Descricao: |
  Construir motor de análise de padrões nos feedbacks para evolução automática.
  
  Implementação:
  - Análise de correlação: quais critérios geram mais likes?
  - Identificar padrões de dislike por tipo de vaga
  - Sugestão de ajuste de thresholds baseada em dados
  - Atualização do effectiveness_score dos critérios
  - Pipeline: feedback → análise → sugestão → aprovação humana → aplicação

Requisitos Tecnicos:
  Backend (Rails + Python):
    - Rails Job: app/jobs/learning_analysis_job.rb (semanal)
    - Python Service: app/services/ai/learning_engine.py
    - Correlação: critérios × feedback × tipo vaga × qualification_level
    - Output: sugestões de ajuste com confiança
    - Aprovação humana obrigatória antes de aplicar
  Frontend (Vue.js 3 + Vuetify 3):
    - Página: src/pages/admin/LearningInsights.vue
    - Lista de sugestões pendentes com botão aprovar/rejeitar

DoD:
  - [ ] Pipeline funcional end-to-end
  - [ ] Sugestões de ajuste geradas automaticamente
  - [ ] Aprovação humana antes de aplicar
  - [ ] Métricas de evolução do sistema

Criterios de Aceitacao:
  - [ ] Job semanal executa e gera insights
  - [ ] Sugestões com confiança e justificativa
  - [ ] Admin aprova/rejeita sugestões
  - [ ] effectiveness_score atualizado após aprovação

Dependencias: WDT-006, WDT-016
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - feedback_learning_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/feedback_learning_service.py
  - candidate_feedback_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/candidate_feedback_service.py
  - learning_loop_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/learning_loop_service.py
  - pattern_detector_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/pattern_detector_service.py
```

##### Prompt para IA (Cursor/VSCode) — WDT-027

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x + Python 3.11 + FastAPI
- Background Jobs: Sidekiq
- IA: Gemini 2.5 Flash

---

TAREFA: Criar motor de aprendizado baseado em feedbacks like/dislike.

IMPLEMENTAÇÃO:

1. Job semanal (Sidekiq):
   app/jobs/learning_analysis_job.rb
   - Coleta feedbacks da última semana
   - Envia para Python: POST /api/v1/ai/analyze-feedback-patterns
   - Salva sugestões como LearningInsight records

2. Python Service:
   app/services/ai/learning_engine.py
   - Correlaciona: critérios usados × feedback recebido
   - Identifica: "critério X tem 80% dislike em vagas operacionais"
   - Gera: sugestão de ajuste com confiança e justificativa
   - Pipeline: human-in-the-loop (NUNCA aplicar automaticamente)

3. Model: LearningInsight
   - suggestion_type (threshold_adjust/weight_change/criteria_retire)
   - target (evaluation_criterion_id ou parameter name)
   - current_value, suggested_value, confidence, reasoning
   - status (pending/approved/rejected)
   - approved_by (user_id)

4. Frontend: lista de sugestões com approve/reject

NÃO FAZER:
- NUNCA aplicar ajustes automaticamente — sempre aprovação humana
- NÃO gerar sugestões com < 50 feedbacks de base
```

---

### CARD WDT-028: Framework de A/B Testing de Parâmetros
**Épico:** É18 — Aprendizado e Features Avançadas

```yaml
Titulo: "[BE] Framework de A/B testing de parâmetros"
Tipo: Story
Sprint: 17
Pontos: 8
Horas: 14
Prioridade: Média
Epic: EPIC-18 (Aprendizado e Features Avançadas)
Fase: Fase 5 - Aprendizado
Status: 📋 Pendente Jira
Labels: ab-testing, optimization

Descricao: |
  Criar framework para testar diferentes configurações de parâmetros.
  
  Parâmetros testáveis: K (WRF), thresholds, pesos de critérios, prompts.
  
  Implementação:
  - Config de experimentos (% tráfego, variantes)
  - Tracking de qual variante foi usada em cada busca
  - Análise estatística de resultados (p-value, confiança)
  - Dashboard de experimentos

Requisitos Tecnicos:
  Backend (Rails):
    - Model: app/models/experiment.rb
    - Service: app/services/experiments/ab_test_service.rb
    - Tracking: salvar experiment_variant_id em cada busca
    - Análise: estatística básica (média, desvio, p-value)
  Frontend (Vue.js 3 + Vuetify 3):
    - Página: src/pages/admin/Experiments.vue
    - Criar/gerenciar experimentos
    - Dashboard de resultados

DoD:
  - [ ] Framework funcional
  - [ ] Pelo menos 1 experimento executado
  - [ ] Análise estatística automatizada
  - [ ] Dashboard de resultados

Criterios de Aceitacao:
  - [ ] Criar experimento com variantes
  - [ ] Tráfego distribuído conforme config
  - [ ] Tracking de variante por busca
  - [ ] Relatório com p-value

Dependencias: WDT-006
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - search_analytics_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/search_analytics_service.py
  - feature_flag_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/feature_flag_service.py
```

##### Prompt para IA (Cursor/VSCode) — WDT-028

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x + Vue.js 3 + Vuetify 3
- Cache: Redis

---

TAREFA: Criar framework de A/B testing para parâmetros de busca.

IMPLEMENTAÇÃO:

1. Model Experiment:
   - name, description, status (draft/running/completed)
   - parameter_name (ex: "wrf_k", "es_threshold")
   - variants (jsonb): [{ name: "control", value: 60, traffic: 50 }, 
                         { name: "variant_a", value: 30, traffic: 50 }]
   - start_date, end_date, min_sample_size

2. Service: app/services/experiments/ab_test_service.rb
   - assign_variant(experiment_id, user_id): usa hash para distribuição estável
   - get_parameter(parameter_name, user_id): retorna valor da variante
   - Salvar variant_id em cada search record

3. Dashboard:
   - Listar experimentos com status
   - Para cada: métricas (like_rate, score_mean) por variante
   - Análise estatística básica

NÃO FAZER:
- NÃO mudar variante de um usuário no meio do experimento
- NÃO rodar A/B sem sample size mínimo
```

---

## ÉPICO 19: OBSERVABILIDADE E DOCUMENTAÇÃO DE BUSCA (2 cards, 16 SP)
**Objetivo:** Manutenibilidade, troubleshooting, onboarding de novos devs
**Sprint Alvo:** 2+ e 18
**Prioridade:** 🟡 Média
**Dependências:** Nenhum (documentação) / WDT-011/012/013 (dashboard)

---

### CARD WDT-029: Documentação Técnica Completa do Sistema de Busca
**Épico:** É19 — Observabilidade e Documentação de Busca

```yaml
Titulo: "[DOC] Documentação técnica completa do sistema de busca"
Tipo: Task
Sprint: 2+
Pontos: 8
Horas: 16
Prioridade: Média
Epic: EPIC-19 (Observabilidade e Documentação de Busca)
Fase: Fase 6 - Docs & Infra
Status: 📋 Pendente Jira
Labels: docs, architecture

Descricao: |
  Criar e manter documentação técnica abrangente.
  
  Tópicos:
  - Arquitetura: ES + PGV + WRF (diagrama de fluxo)
  - Pipeline de busca completo (step by step)
  - Parâmetros: quais são, como ajustá-los, valores padrão
  - Elasticsearch: qual texto é usado (bruto vs. expandido pela LLM)
  - Prompts: documentar todos os prompts e seus propósitos
  - Troubleshooting: problemas comuns e soluções
  - Ruby/Benedetti Score: documentar fórmula e parametrização

Requisitos Tecnicos:
  Documentação:
    - Formato: Markdown no repositório (docs/)
    - Diagramas: Mermaid.js ou ASCII
    - Versionada junto com código
    - Atualizada a cada mudança significativa no pipeline

DoD:
  - [ ] Documentação acessível (wiki/confluence/repo)
  - [ ] Diagramas de arquitetura
  - [ ] Todos os parâmetros documentados
  - [ ] Guia de troubleshooting

Criterios de Aceitacao:
  - [ ] Pipeline documentado step-by-step
  - [ ] Parâmetros com valores padrão e ranges
  - [ ] Troubleshooting com 10+ problemas comuns
  - [ ] Atualizado com últimas mudanças

Dependencias: Nenhuma
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - semantic_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/semantic_search_service.py
  - search_analytics_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/search_analytics_service.py
  - vacancy_search_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/vacancy_search_service.py
```

##### Prompt para IA (Cursor/VSCode) — WDT-029

```
CONTEXTO DO PROJETO WEDO TALENT:
- Arquitetura: Elasticsearch + PG Vector + WRF (Weighted Rank Fusion)
- Ambiente: Ruby on Rails + Python FastAPI

---

TAREFA: Criar documentação técnica completa do sistema de busca.

TÓPICOS OBRIGATÓRIOS:

1. docs/search/ARCHITECTURE.md
   - Diagrama do pipeline completo (Mermaid)
   - Fluxo: Query → ES + PGV → Filtros estatísticos → WRF → Resultado
   - Componentes e responsabilidades

2. docs/search/PARAMETERS.md
   - Tabela de todos os parâmetros ajustáveis
   - Valores padrão, ranges recomendados, env vars
   - K do WRF, thresholds de score, gap multipliers

3. docs/search/TROUBLESHOOTING.md
   - Resultados irrelevantes: como diagnosticar
   - Performance lenta: checklist
   - Instabilidade de ranking: como detectar e corrigir
   - Discrepância ES vs PGV: o que significa

4. docs/search/PROMPTS.md
   - Todos os prompts LLM usados no pipeline
   - Propósito de cada um
   - Como iterar/versionar prompts
```

---

### CARD WDT-030: Dashboard de Observabilidade do Sistema de Busca
**Épico:** É19 — Observabilidade e Documentação de Busca

```yaml
Titulo: "[BE/FE] Dashboard de observabilidade do sistema de busca"
Tipo: Story
Sprint: 18
Pontos: 8
Horas: 16
Prioridade: Média
Epic: EPIC-19 (Observabilidade e Documentação de Busca)
Fase: Fase 6 - Docs & Infra
Status: 📋 Pendente Jira
Labels: monitoring, dashboard, ops

Descricao: |
  Dashboard unificado de monitoramento do sistema de busca.
  
  Métricas:
  - Taxa de queda de score por busca
  - Gap semântico médio
  - Estabilidade intra-query
  - Uso de tokens por busca e acumulado
  - Like/dislike ratio por período
  - Tempo de resposta (p50, p95, p99)
  - Candidatos filtrados por etapa do pipeline
  - Distribuição de qualification_level das vagas

Requisitos Tecnicos:
  Backend (Rails):
    - Service: app/services/analytics/search_observability_service.rb
    - Métricas coletadas em cada busca (salvar em search_metrics table)
    - Cache Redis para aggregações
  Frontend (Vue.js 3 + Vuetify 3):
    - Página: src/pages/admin/SearchObservability.vue
    - ApexCharts para gráficos
    - Auto-refresh a cada 60s

DoD:
  - [ ] Dashboard funcional com todas as métricas
  - [ ] Alertas para anomalias
  - [ ] Histórico de métricas
  - [ ] Filtros por período, tipo de vaga, recrutador

Criterios de Aceitacao:
  - [ ] 8 métricas exibidas
  - [ ] Alerta quando estabilidade < 80%
  - [ ] Alerta quando like_rate < 30%
  - [ ] Histórico de 90 dias
  - [ ] Auto-refresh funcional

Dependencias: WDT-011, WDT-012, WDT-013
Bloqueia: Nenhum

Arquivos de Referencia (Prototipo Replit):
  - strategic-dashboard.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/dashboard/strategic-dashboard.tsx
  - chart-components.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/charts/chart-components.tsx
  - search_analytics_service.py: https://replit.com/@paulogmoraesjr/workspace#lia-agent-system/app/services/search_analytics_service.py
  - ConsumptionChart.tsx: https://replit.com/@paulogmoraesjr/workspace#plataforma-lia/src/components/admin/ai-consumption/ConsumptionChart.tsx
```

##### Prompt para IA (Cursor/VSCode) — WDT-030

```
CONTEXTO DO PROJETO WEDO TALENT:
- Ambiente: Ruby on Rails 7.x + Vue.js 3 + Vuetify 3
- Cache: Redis

---

TAREFA: Criar dashboard de observabilidade do sistema de busca.

IMPLEMENTAÇÃO:

Backend:
1. Migration: create_table :search_metrics
   - search_id, es_score_drop_rate, pgv_gap_mean, stability_index,
     tokens_used, response_time_ms, candidates_filtered_es,
     candidates_filtered_pgv, wrf_input_count, wrf_output_count,
     qualification_level, created_at

2. Service: coleta métricas em cada busca (after_action no controller)
3. Aggregação: Redis cache com TTL 60s para dashboard

Frontend:
1. Página com grid de cards:
   - Card 1: Taxa queda média (gauge chart)
   - Card 2: Gap semântico médio (gauge chart)
   - Card 3: Estabilidade (gauge com alerta)
   - Card 4: Tokens/busca (line chart 30 dias)
   - Card 5: Like/dislike ratio (donut chart)
   - Card 6: Tempo resposta p50/p95/p99 (line chart)
   - Card 7: Candidatos filtrados por etapa (funnel chart)
   - Card 8: Distribuição qualification_level (bar chart)

2. Alertas: v-alert type="warning" quando métricas fora do threshold
3. Auto-refresh: setInterval 60s ou vue-use useIntervalFn
```

---

