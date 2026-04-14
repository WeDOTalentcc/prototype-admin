# ML_PLATFORM_CONCEPTS_AUDIT.md — Auditoria de ML, Aprendizado e Conceitos de Plataforma
**Protocolo:** P19  
**Data:** 2026-04-14  
**Auditor:** Claude Opus 4.6  
**Repositórios auditados:**
- IA Layer: `lia-agent-system/` (Replit)
- Backend: `ats-api-copia/` (Rails 7.1, GitHub wedocc2026/wedotalentcc, deploy GCP)
- Contexto: Frontend + IA no Replit, Backend no GCP. Integração Rails<>Python via RabbitMQ (em configuração). Redis/RabbitMQ sendo configurados no GCP.

**Depende de:** P01 (PLATFORM_MAP)  
**Alimenta:** P21, P24

---

## SCORE GERAL: 2.1 / 5

| Dimensão | Score | Peso |
|----------|-------|------|
| Modelos de ML (além do LLM) | 1.5/5 | 25% |
| Aprendizado com Feedback | 2.5/5 | 25% |
| Personalização por Tenant | 3.0/5 | 20% |
| Integração ML <> Agentes | 1.5/5 | 15% |
| Conceitos de Plataforma | 2.5/5 | 15% |

---

## PASSO 1: INVENTÁRIO DE CAPACIDADES DE ML NO CÓDIGO

### A. MODELOS DE ML (Além do LLM)

#### 1. OutcomePredictor (Rule-Based)
- **Arquivo:** `app/services/ml/outcome_predictor.py`
- **Framework:** Puro Python (dataclasses, sem sklearn/pytorch/transformers)
- **O que faz:** Prediz time-to-fill, salary range, skill success, hiring insights
- **Tipo real:** NAO é ML — são heurísticas rule-based com feature multipliers
- **Treinamento:** Nunca treinado. Usa tabelas estáticas de multiplicadores
- **Versionamento:** ModelRegistry (in-memory, v1.0.0) — NAO persiste entre restarts
- **Métricas:** Registradas pelo ModelRegistry (record_prediction), mas in-memory apenas — perdem-se no restart
- **Integrado com:** API /ml/predict/*, chamado por endpoints REST

**Veredicto:** É um motor de regras disfarçado de ML. Funciona para MVP, mas não aprende.

#### 2. OutcomeFeatureEngineer
- **Arquivo:** `app/services/ml/feature_engineering.py`
- **Framework:** Puro Python
- **O que faz:** Extrai 20+ features de vagas (seniority, salary, skills, location, etc.)
- **Features extraídas:** role_category, seniority_level, salary_midpoint, num_required_skills, skill_rarity_score, market_demand_score, creation_quarter, company_size_category, etc.
- **Qualidade:** Boa engenharia de features. Pronta para alimentar ML real
- **Problema:** Features extraídas mas consumidas apenas pelo rule-based predictor — sem modelo ML por trás

#### 3. ModelRegistry (In-Memory)
- **Arquivo:** `app/services/ml/model_registry.py`
- **O que faz:** Registra, versiona, compara modelos
- **Modelos registrados:** 3 (time_to_fill_predictor, salary_predictor, skill_success_predictor)
- **Todos v1.0.0**, type=rule_based ou frequency_based
- **CRITICO:** Registry é in-memory — perde estado no restart. Em produção, precisaria MLflow/S3/DB
- **Performance tracking:** ModelPerformance com accuracy, mean_error — mas nunca avaliado contra dados reais

#### 4. VectorSemanticCache (pgvector)
- **Arquivo:** `app/orchestrator/vector_semantic_cache.py`
- **Embedding models:** OpenAI text-embedding-3-small (1536 dims) + fallback Gemini text-embedding-004 (768 dims)
- **O que faz:** Cache semântico para roteamento de intenções — reduz chamadas LLM 40-60%
- **Storage:** pgvector (routing_cache_vectors table)
- **Threshold:** cosine similarity >= 0.85
- **Status:** FUNCIONAL e sofisticado

#### 5. Job Embeddings
- **Arquivo:** `app/api/v1/job_embeddings.py` + `app/domains/job_management/services/job_embedding_service.py`
- **O que faz:** Embedding semântico de vagas para busca similar + Fast Track
- **Uso:** Busca de vagas similares, sugestões Fast Track
- **Status:** FUNCIONAL

#### 6. Digital Twin (RAG Few-Shot)
- **Arquivo:** `app/services/twin_inference_service.py`
- **O que faz:** Avalia candidatos simulando o raciocínio de um SME (especialista)
- **Técnica:** Embed candidato -> K-NN search em twin_decisions (pgvector) -> Few-shot prompt com exemplos approved/rejected -> LLM gera score + reasoning
- **Confidence:** Calculada com base no tamanho do corpus e similaridade
- **Status:** Estrutura sofisticada, mas depende de corpus de decisões do twin. Sem dados iniciais = cold start

#### 7. WSI Scoring
- **Arquivo:** `app/domains/cv_screening/services/cv_screening_batch_service.py`
- **Fórmula:** WSI = (tecnico * 0.70) + (comportamental * 0.30)
- **Thresholds:** auto_approve >= 75, review >= 55
- **Tipo:** Weighted scoring (NAO é ML) — pesos fixos
- **Status:** FUNCIONAL, mas sem aprendizado

### ACHADO CRITICO: ZERO Modelos ML Treinados
**Não existe NENHUM modelo sklearn, pytorch, transformers no codebase.** Tudo que é chamado de "ML" são heurísticas rule-based ou LLM prompting. A feature engineering está pronta, mas não alimenta nenhum modelo treinável.

---

### B. APRENDIZADO COM FEEDBACK

#### 1. Calibration Loop (CalibrationService)
- **Arquivo:** `app/domains/analytics/services/calibration_service.py`
- **DB Models:** CalibrationEvent, CalibrationSuggestion, CalibrationWeight (libs/models)
- **Tipos de feedback registrados:**
  - **Explícito:** thumbs up/down do recrutador (EXPLICIT_AGREE, EXPLICIT_DISAGREE)
  - **Implícito:** stage changes (IMPLICIT_ADVANCE, IMPLICIT_REJECT, IMPLICIT_OVERRIDE)
  - **Pós-contratação:** POST_HIRE_SUCCESS, POST_HIRE_FAILURE
- **Divergence detection:** Identifica quando recrutador rejeita candidato com score LIA > 70 ou avança candidato com score < 60
- **Suggestion generation:** Gera sugestões de ajuste de pesos baseada em divergências (ex: "Reduzir peso de habilidades técnicas")
- **Approve/Reject flow:** Recrutador pode aprovar/rejeitar sugestões de calibração
- **Score delta tracking:** Cada evento registra delta (ex: +15 para post_hire_success, -15 para failure)

**Loop implementado?**
```
Agente sugere candidato
  -> Recrutador aceita/rejeita
  -> CalibrationEvent registrado
  -> get_divergences() detecta padrões
  -> generate_suggestions() propõe ajustes
  -> Recrutador aprova
  -> CalibrationWeight atualizado
  -> MAS: próxima sugestão NAO consulta CalibrationWeight automaticamente
```

**Veredicto:** O LOOP DE FEEDBACK NAO FECHA. Feedback é coletado e sugestões geradas, mas os weights ajustados não são consumidos automaticamente pelos agentes no momento de scoring. É um dashboard informativo, não um sistema de aprendizado.

#### 2. Suggestion Feedback (SuggestionFeedbackService)
- **Arquivo:** `app/api/v1/suggestion_feedback.py`
- **O que faz:** Registra aceite/rejeição de sugestões LIA durante wizard
- **Stats:** Taxa de aceitação por campo (salary, skills, seniority, etc.)
- **Adjustments endpoint:** /suggestion-feedback/{company_id}/adjustments — calcula ajustes baseados em feedback histórico
- **Consome FeedbackLearningService.apply_learning()** — Este loop fecha parcialmente

#### 3. Wizard Feedback (FeedbackLearningService)
- **Arquivo:** `app/domains/analytics/services/feedback_learning_service.py`
- **DB Model:** WizardFeedback — registra correções do recrutador durante wizard
- **Padrão detectado:** Se LIA sugere R$15k e recrutadores corrigem sistematicamente para R$18k+, identifica padrão
- **apply_learning():** Aplica ajustes em novas sugestões baseado em correções anteriores
- **Confidence tiers:** high (>=10 samples), medium (>=5), low (<5)
- **Status:** Loop parcialmente fechado — apply_learning existe mas precisa ser invocado explicitamente pelos agentes

#### 4. Search Feedback
- **Arquivo:** `app/api/v1/search_feedback.py`
- **O que faz:** Like/dislike em candidatos retornados pela busca
- **Storage:** SearchFeedback model com candidate_id, feedback_type, job_id
- **Consome:** Feedback coletado mas NAO alimenta re-ranking futuro

#### 5. Learning Outcomes (JobOutcome)
- **Arquivo:** `app/api/v1/learning_outcomes.py`
- **O que faz:** Registra desfecho de vagas (filled, cancelled, expired, reposted)
- **Métricas:** time_to_fill, candidate_count por etapa, satisfaction_score
- **Patterns endpoint:** Agrupa por role/seniority/department
- **Consome:** OutcomePredictor consulta dados de outcomes para heurísticas — mas NAO treina modelo

#### 6. EnhancedAgentMixin (Learning Extractor)
- **Arquivo:** `libs/agents-core/lia_agents_core/enhanced_agent_mixin.py`
- **O que faz:** Após cada ReAct loop, extrai "learnings" e salva em long-term memory
- **Componentes:**
  - LearningExtractor — extrai aprendizados do estado do loop
  - LongTermMemoryService — persiste em memória de longo prazo
  - WorkingMemoryService — memória de sessão
  - MemoryIntegration — combina ambas para enriquecer contexto
- **Todos os 15+ ReAct agents usam via mixin** (sourcing, wizard, pipeline, communication, analytics, automation, etc.)
- **Status:** Loop funciona — agente aprende e injeta context na próxima interação

---

### C. PERSONALIZACAO POR TENANT

| Recurso | Implementado? | Arquivo |
|---------|---------------|---------|
| LLM provider por tenant | SIM | app/shared/providers/llm_factory.py (ProviderContainer + TenantProviderRegistry) |
| API keys por tenant | SIM | app/shared/tenant_llm_context.py (Gemini/Claude/OpenAI) |
| LLM routing por tenant | SIM | app/api/v1/llm_config.py (chat/embedding/screening/voice -> provider) |
| Token budget por tenant | SIM | app/orchestrator/tenant_budget.py (Redis, mensal, per-request) |
| Custom agents por tenant | SIM | app/domains/agent_studio/custom_agent_runtime.py (Agent Studio) |
| Guardrails por tenant | SIM | enhanced_agent_mixin.py -> AutonomyEngine -> GuardrailRepository |
| Persona por tenant | PARCIAL | System prompt do Agent Studio é customizável; agentes core usam prompt fixo |
| Vocabulário por tenant | NAO | Não implementado — terminologia é fixa |
| Pesos de scoring por tenant | NAO | WSI usa pesos fixos (0.70/0.30) para todos |
| Pipeline etapas por tenant | SIM | Via Rails (Apartment multi-tenant schemas) |

### D. PERSONALIZACAO POR RECRUTADOR

| Recurso | Implementado? | Detalhes |
|---------|---------------|----------|
| Preferências aprendidas | PARCIAL | EnhancedAgentMixin salva learnings por sessão, mas não por recrutador |
| Histórico de decisões | SIM | CalibrationEvent registra por user_id |
| Atalhos/defaults | NAO | Não implementado |
| Estilo de comunicação | NAO | Mesmo tom para todos os recrutadores |

### E. PERSONALIZACAO POR VAGA/PROCESSO

| Recurso | Implementado? | Detalhes |
|---------|---------------|----------|
| Critérios ajustados durante processo | PARCIAL | Via calibration session (manual), mas não automático |
| Feedback entrevistas refina busca | NAO | Interview feedback registrado mas não re-alimenta sourcing |
| Padrões por empresa | PARCIAL | FeedbackLearningService.apply_learning() considera company_id + role |

---

## PASSO 2: MATURIDADE DO APRENDIZADO

### Escala de Maturidade (0-5)

| Capacidade | Nível Atual | Nível Alvo | Gap | Esforço | Evidência |
|------------|-------------|------------|-----|---------|-----------|
| **Ranking de candidatos** | 1 (Configurável — pesos WSI fixos) | 3 (Supervised) | 2 | L | WSI = tecnico*0.70 + comportamental*0.30, sem retrain |
| **Predição time-to-fill** | 1 (Rule-based com multipliers) | 3 (Supervised) | 2 | L | OutcomePredictor usa heurísticas estáticas |
| **Predição salarial** | 1 (Rule-based com matrizes role/seniority) | 3 (Supervised) | 2 | M | salary_predictor v1.0.0 sem dados reais |
| **Calibração LIA<>Recrutador** | 2 (Feedback loop básico — coleta sem auto-ajuste) | 4 (Contínuo) | 2 | L | CalibrationService registra mas não fecha loop |
| **Sugestão de wizard** | 2.5 (Feedback loop com apply_learning) | 3 (Supervised) | 0.5 | S | FeedbackLearningService já ajusta sugestões |
| **Busca de candidatos (re-ranking)** | 0 (Estático) | 3 (Supervised) | 3 | XL | search_feedback coletado mas não re-alimenta ranking |
| **Personalização comunicação** | 0 (Estático) | 2 (Feedback loop) | 2 | M | Mesmo tom para todos |
| **Detecção de intent** | 2 (Cache semântico aprende novos padrões) | 3 (Supervised) | 1 | S | VectorSemanticCache melhora com uso |
| **Digital Twin inference** | 2 (Few-shot com histórico) | 3 (Supervised) | 1 | M | twin_decisions como corpus — depende de volume |
| **Matching vaga-candidato** | 1.5 (Embeddings + heurísticas) | 4 (Contínuo) | 2.5 | XL | Embeddings existem, aprendizado não |
| **Skill success prediction** | 1 (Frequency-based) | 3 (Supervised) | 2 | M | Conta frequência de skills em contratações |
| **Agente memory (cross-session)** | 3 (LongTermMemory + LearningExtractor) | 4 (Contínuo) | 1 | M | MELHOR capacidade de aprendizado da plataforma |

### Resumo de Maturidade
- **Nível médio atual:** 1.4/5
- **Nível alvo médio:** 3.2/5
- **Gap médio:** 1.8 níveis

---

## PASSO 3: INTEGRACAO ML <> AGENTES

| Capacidade ML | Agente Consumidor | Método de Integração | Loop Fechado? | Fallback se Falha | Confiança Exposta? |
|---------------|-------------------|---------------------|---------------|--------------------|--------------------|
| OutcomePredictor | API REST /ml/predict/* | HTTP (não integrado com agentes) | NAO | HTTPException 500 | SIM confidence_level |
| VectorSemanticCache | CascadedRouter (Tier 3) | Direto (in-process) | SIM (auto-popula) | Passa para Tier 4 | N/A |
| Job Embeddings | SearchAssistant, FastTrack | Service call | NAO | Fallback para busca keyword | SIM min_similarity |
| CalibrationService | Nenhum agente consome automaticamente | DESCONECTADO | NAO | N/A | N/A |
| FeedbackLearningService | Wizard (via apply_learning) | Service call | PARCIAL | Usa suggestion sem ajuste | SIM confidence tier |
| SearchFeedback | Nenhum agente consome | DESCONECTADO | NAO | N/A | N/A |
| Digital Twin | CustomAgentRuntime (via TwinInferenceService) | Service call + pgvector | PARCIAL (depende corpus) | score=50 decision=maybe | SIM confidence float |
| EnhancedAgentMixin | Todos os 15+ ReAct agents | Mixin (in-process) | SIM | String vazia | N/A |
| WSI Scoring | CVScreeningBatchService | Direto (fórmula) | NAO | N/A | N/A |
| FairnessGuard | MainOrchestrator + todos agentes | Pre-check + tool output | SIM | fail-safe (allow) | PARCIAL is_blocked only |

### ACHADO CRITICO: 4 dos 10 sistemas de ML/feedback estão DESCONECTADOS dos agentes
- **OutcomePredictor:** Tem API REST mas nenhum agente chama
- **CalibrationService:** Dashboard-only, weights não consumidos
- **SearchFeedback:** Coleta likes/dislikes que ninguém usa
- **WSI Scoring:** Pesos fixos, calibration não alimenta

---

## PASSO 4: CONCEITOS DE PLATAFORMA NO CÓDIGO

### A. LLM FACTORY

| Aspecto | Status | Detalhes |
|---------|--------|----------|
| **Existe no código?** | SIM | app/shared/providers/llm_factory.py |
| **Model selection** | SIM | ProviderContainer per-tenant com primary + fallback order |
| **Fallback chain** | SIM | Gemini -> Claude -> OpenAI (configurável por tenant) |
| **Cost tracking** | SIM | TenantBudget via Redis — mensal + per-request |
| **Per-tenant isolation** | SIM | TenantProviderRegistry -> ProviderContainer per company_id |
| **Routing por operação** | SIM | chat/embedding/screening/voice -> provider diferente |
| **SSOT?** | PARCIAL | LLMProviderFactory (deprecated global) coexiste com ProviderContainer (per-tenant). Ambos funcionam. |
| **Quem usa** | SIM | Todos agentes via get_provider_for_tenant(), embedding via EmbeddingProviderFactory |
| **Quem bypassa** | PARCIAL | app/api/v1/internal_llm.py usa get_provider_for_tenant() sem company_id (usa global default) |
| **Budget enforcement** | SIM | check_request_budget_before_llm() chamado antes de cada geração |
| **Circuit breaker** | SIM | Por provider, failure_threshold=3, recovery_timeout=30s |

**Veredicto: 4.0/5** — Sofisticado. Tenant isolation real. Mas LLMProviderFactory deprecated ainda não removido.

### B. TENANT MODEL

| Aspecto | Status | Detalhes |
|---------|--------|----------|
| **Implementação Python** | SIM | company_id contextvar em auth_enforcement.py -> flui para LLM, budget, guardrails |
| **Implementação Rails** | SIM | Apartment gem — schema isolation por tenant no PostgreSQL |
| **Middleware enforcement** | SIM | AuthEnforcementMiddleware extrai company_id do JWT e seta contextvar |
| **DB isolation** | PARCIAL | Python: company_id como coluna (row-level). Rails: schema-level (Apartment). Modelos diferentes de isolamento |
| **Agentes respeitam** | SIM | CustomAgentRuntime._tenant_safe_wrapper() injeta company_id em todas as tools |
| **LLM per-tenant** | SIM | Via TenantProviderRegistry + tenant_llm_context.py |
| **Budget per-tenant** | SIM | Redis token_budget:{company_id}:{YYYY-MM} |
| **Config per-tenant** | SIM | llm_config table com providers, routing, fallback order por company |

**Veredicto: 3.5/5** — Implementação sólida no Python. Gap: modelo de isolamento diferente entre Python (row-level) e Rails (schema-level) pode causar inconsistências quando integração via RabbitMQ estiver ativa.

### C. PESSOA / LIFECYCLE

| Aspecto | Status | Detalhes |
|---------|--------|----------|
| **Modelo Person** | NAO | Não existe. Usa Candidate model |
| **lifecycle_status** | PARCIAL | Job vacancy tem lifecycle (lifecycle.py): draft -> published -> paused -> closed. Candidato NAO tem lifecycle explícito |
| **Transições** | PARCIAL | Job: publish, pause, resume, close, archive, clone. Candidato: movido entre stages do pipeline mas sem lifecycle formal |
| **Agentes respeitam lifecycle?** | PARCIAL | De vagas sim (verificam status). De candidatos não — tratam tudo como "candidato ativo" |
| **candidate->hired->employee->alumni** | NAO | Não implementado. Uma vez que JobOutcome(FILLED) é registrado, candidato permanece como candidato no sistema |

**Veredicto: 1.5/5** — Job lifecycle existe e funciona. Person/Candidate lifecycle completamente ausente. Sem distinção entre lead, candidato ativo, contratado, alumni. Gap crítico para CRM de talentos.

### D. AGENT STUDIO

| Aspecto | Status | Detalhes |
|---------|--------|----------|
| **Runtime** | SIM | CustomAgentRuntime — herda LangGraphReActBase + EnhancedAgentMixin |
| **Configura o quê** | SIM | system_prompt, allowed_tools, max_steps, temperature, model_override, context_level |
| **Tool filtering** | SIM | 15 tools em _RESTRICTED_TOOLS (bloqueadas). Pool de 40+ tools autonomous + domain-specific |
| **Tenant isolation** | SIM | _tenant_safe_wrapper() injeta company_id e bloqueia writes sem confirm=True |
| **FairnessGuard on output** | SIM | Verifica bias no output de cada tool do agente customizado |
| **Metering** | SIM | studio_metering_service — quota por tipo de agente, billing por uso |
| **Marketplace** | SIM | Browse, publish, install, uninstall — estrutura completa |
| **Carrega config dinamicamente** | SIM | Runtime recebe config no constructor, não hardcoded |

**Veredicto: 4.0/5** — Muito sofisticado. Tenant-safe, metered, com marketplace. Principal gap: agentes do Studio não têm acesso ao CalibrationService para auto-calibrar.

### E. OUTROS CONCEITOS

| Conceito | Path | Maturidade | Consumidores | Não-Consumidores | Divergências |
|----------|------|------------|-------------|-------------------|-------------|
| **CascadedRouter** | app/orchestrator/cascaded_router.py | Alta | MainOrchestrator | — | Nenhuma |
| **FairnessGuard** | app/shared/compliance/fairness_guard.py | Alta | Orchestrator, Studio, ML Salary, todos agentes | — | Nenhuma |
| **PolicyEngine** | app/orchestrator/policy_engine.py | Média | Orchestrator | Agentes individuais (acessam diretamente, não via engine) | policy_engine.py vs AutonomyEngine — dois conceitos similares |
| **EmbeddingCacheService** | app/shared/services/embedding_cache_service.py | Alta | VectorSemanticCache, JobEmbeddings | SearchAssistant (poderia usar cache) | — |
| **NotificationService** | app/services/notification_service.py | Média | TenantBudget, automations | Calibration (deveria notificar divergências) | — |
| **AuditLogRepository** | app/domains/admin/repositories/audit_log_repository.py | Alta | LLM Config, Auth, Admin | ML predictions (não auditam) | — |

---

## RECOMENDACOES PRIORIZADAS

### P0 — Fechar o Loop de Calibração (MAIOR ROI)
**O que:** Fazer CalibrationWeight ser consumido automaticamente pelos agentes no momento de scoring
**Arquivo:** calibration_service.py -> conectar com cv_screening_batch_service.py
**Impacto:** Transforma dashboard informativo em sistema de aprendizado real
**Esforço:** S (1-2 dias)
**De Nível 2 -> Nível 3**

### P0 — Search Feedback -> Re-ranking
**O que:** Usar likes/dislikes de SearchFeedback para boostar/penalizar candidatos em buscas futuras
**Arquivo:** search_feedback.py -> integrar com multi_strategy_search.py
**Impacto:** Busca melhora com cada interação do recrutador
**Esforço:** M (3-5 dias)
**De Nível 0 -> Nível 2**

### P1 — Candidate Lifecycle Model
**O que:** Adicionar lifecycle_status enum ao Candidate: lead -> active -> finalist -> hired -> employee -> alumni -> inactive
**Impacto:** Base para CRM de talentos, re-engajamento, nurturing
**Esforço:** M (3-5 dias para modelo + migrations, L para agentes consumirem)

### P1 — Remover LLMProviderFactory Deprecated
**O que:** Migrar todos os consumers para get_provider_for_tenant() e remover class-level state
**Impacto:** Elimina risco de leak entre tenants via global state
**Esforço:** S (1-2 dias — a maioria já migrou)

### P1 — Treinar Primeiro Modelo ML Real
**O que:** Usar OutcomeFeatureEngineer + JobOutcome data para treinar XGBoost de time-to-fill
**Impacto:** Predição real vs heurística. Feature engineering já está pronta
**Esforço:** M (5-7 dias para treinar, avaliar, deploy com ModelRegistry)
**Pré-requisito:** Mínimo ~200 outcomes registrados para significância estatística

### P2 — Persistir ModelRegistry
**O que:** Migrar ModelRegistry de in-memory para PostgreSQL ou MLflow
**Impacto:** Models, versions e performance sobrevivem restarts
**Esforço:** S (2-3 dias)

### P2 — WSI Pesos por Tenant
**O que:** Tornar pesos WSI (0.70/0.30) configuráveis por tenant
**Impacto:** Empresas tech podem priorizar técnico; empresas de vendas podem priorizar comportamental
**Esforço:** S (1-2 dias — já tem CalibrationWeight como base)

### P2 — Personalização por Recrutador
**O que:** LearningExtractor salvar learnings por user_id além de session_id
**Impacto:** LIA se adapta ao estilo de cada recrutador individualmente
**Esforço:** M (3-4 dias)

---

## RESUMO EXECUTIVO

### O que a plataforma faz bem
1. **LLM Factory** é sofisticada — per-tenant isolation, fallback chains, cost tracking, circuit breakers
2. **Agent Studio** é production-ready — tenant-safe, metered, marketplace
3. **EnhancedAgentMixin** implementa aprendizado real via LongTermMemory — melhor capacidade de ML
4. **Feature Engineering** está pronta para alimentar modelos reais
5. **Infraestrutura de feedback** completa — 6 canais de coleta (calibration, wizard, search, suggestion, outcome, learning extractor)

### O que está quebrado
1. **Zero modelos ML treinados** — tudo é rule-based ou LLM prompting
2. **Loops de feedback não fecham** — 4/6 canais coletam dados que ninguém consome
3. **Person lifecycle inexistente** — candidato não tem estados de vida
4. **ModelRegistry efêmero** — perde tudo no restart
5. **Scoring fixo para todos** — WSI 0.70/0.30 universal, calibration weights decorativos

### Metáfora
A plataforma é como um corredor de Fórmula 1 com telemetria de última geração — sensores medindo tudo (6 canais de feedback) — mas que nunca ajusta o setup do carro com os dados coletados. O dashboard mostra divergências lindas, mas o motor continua com os mesmos parâmetros do dia 1.

### Nível de Maturidade Global: 1.4/5 (entre Configurável e Feedback Loop Básico)
**Target: 3.0/5 (Supervised Learning) — gap de 1.6 níveis**
