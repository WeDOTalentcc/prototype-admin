# Fluxo Técnico Completo — Plataforma LIA Alpha 1

**Data:** 31/03/2026  
**Versão:** 1.0  
**Escopo:** Fluxo end-to-end Alpha 1 — desde Login até Scheduling/Feedback  
**Formato:** Diagrama passo-a-passo por macro-etapa (estilo "11 STEPS" do WSI)  
**Referência:** `ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md` v6.3 (complementar)

---

## COMO LER ESTE DOCUMENTO

Cada macro-etapa do Alpha 1 (E1–E9B) é apresentada como um diagrama técnico passo-a-passo, seguindo o formato visual dos "11 STEPS" do fluxo de triagem WSI (ver imagem de referência). Cada step mostra:

1. **O request HTTP real** — endpoint, método, payload
2. **O roteamento** — DomainOrchestrator, CascadedRouter (6 tiers), domínio destino
3. **Os mixins/capabilities injetados** — EnhancedAgentMixin, AuditTrail, WorkingMemory, etc.
4. **FairnessGuard** — quais camadas (L1 explicit, L2 implicit, L3 semantic) atuam ANTES e DEPOIS do LLM
5. **PII Masking** — 4 camadas pré-LLM (CPF, nome, endereço, campos sensíveis)
6. **Processamento** — qual agente/serviço, qual LLM, qual graph/loop
7. **FactChecker** — 4 tipos de verificação pós-LLM
8. **ConfidenceNode + BiasAuditSnapshot** — calibração, Four-Fifths Rule
9. **AuditTrail** — o que é registrado, append-only, retenção SOX
10. **Response final** — dados demasked, scores, recomendação

### Legenda de Status

| Símbolo | Significado |
|---------|------------|
| ● | Ativo — funcionando no código |
| ◐ | Disponível — código existe, precisa ativar/configurar |
| ○ | A implementar — código não existe |
| ⚠ | Gap bloqueante — requer ação antes do MVP |
| 🔒 | Camada de proteção/compliance |
| 🧠 | Camada de inteligência/learning |

### Convenção de Agentes

| Rótulo | Classe no código | Domínio | LLM Provider |
|--------|-----------------|---------|--------------|
| Ag.0 | MainOrchestrator | orchestrator | Gemini (produção) |
| Ag.2 | SourcingReActAgent | sourcing | Gemini |
| Ag.3 | TriagemCurricular (CV Screening) | cv_screening | Gemini |
| Ag.4 | WSIInterviewGraph | cv_screening | Gemini |
| Ag.5 | WSIService (scoring) | cv_screening | Determinístico (sem LLM) |
| Ag.6 | InterviewGraph | interview_scheduling | Gemini |
| Ag.7 | CommunicationReActAgent / PersonalizedFeedbackService | communication / cv_screening | Gemini |
| Ag.8 | ATSIntegrationReActAgent ⚠ PÓS-MVP | ats_integration | Gemini |
| — | WSIQuestionGenerator / WSIScreeningQuestionGenerator | cv_screening | Gemini |
| — | WSIScreeningPipeline | cv_screening | Gemini |
| — | WSIVoiceOrchestrator | cv_screening | Gemini + Deepgram |
| — | JobDescriptionGeneratorService | job_management | Claude (Anthropic) |

---

## E1 — LOGIN — 4 STEPS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Login (auth) — 4 STEPS                                       │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Frontend (Next.js 15) envia POST /api/v1/auth/login
    Body: { "email": "user@company.com", "password": "secret" }
    Request logado automaticamente via middleware (X-Request-ID)

 2  AuthService autentica + gera JWT
    Valida email/password via bcrypt (has_secure_password)
    Gera access_token (JWT, 1800s) + refresh_token
    Valida is_active=True (dependency: get_current_active_user)
    WorkOS SSO disponível como alternativa (rotas /auth/workos)
    CircuitBreaker: circuit "workos" (failure_threshold=5, recovery=30s)

 3  RateLimitMiddleware protege contra brute-force
    Redis-backed sliding window (por IP + email)
    Fallback in-memory se Redis indisponível
    Prometheus: login_attempts_total counter

 4  Resposta ao recrutador
    TokenResponse: { access_token, refresh_token, token_type: "bearer", expires_in: 1800 }
    Frontend armazena token via useCookie('auth_token')
    Redireciona para /user/dashboard

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E1)                                          │
│  1. RateLimitMiddleware — sliding window por IP + email ●                     │
│  2. PII Masking — logs de login mascarados (PIIMaskingFilter global) ●        │
│  3. CircuitBreaker — circuit "workos" para SSO ●                              │
│  4. Audit Trail — login events ◐ (código existe, precisa ativar em auth.py)  │
│  5. LGPD — JWT stateless, sem cookies de sessão ●                            │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E2 — EDITAR/CRIAR VAGA — 8 STEPS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Edição/Criação de Vaga (job_management) — 8 STEPS            │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Consultor acessa POST /api/v1/job-vacancies (criar) ou
    PUT /api/v1/job-vacancies/{vacancy_id} (editar)
    Body: { title, description, department, seniority_level, employment_type,
            work_model, location_city, salary_min, salary_max, required_skills }
    Authorization: Bearer <jwt_token>
    Se "Gerar JD" acionado: POST /api/v1/briefing/generate-jd

 2  DomainOrchestrator roteia + GuardrailCheck
    Identifica domínio = job_management
    GuardrailRepository (3 níveis): global → tenant → domain
    HiringPolicy carregado por company_id
    PromptInjectionGuard ativado

 3  EnhancedAgentMixin._setup_enhanced()
    16 capabilities injetadas automaticamente:
    FairnessGuard (3 layers) | PII Masking (4 layers)
    AuditTrail | BiasAuditSnapshot | ConfidenceNode
    AntiSycophancy (FULL variant) | WorkingMemory | CircuitBreaker
    LearningLoop | TemplateLearning | PredictiveAnalytics
    SemanticSearch | ConversationMemory

 4  FairnessGuard filtra ANTES do LLM
    🔒 L1 Explicit: Regex ~350 patterns em 13 categorias
       Bloqueia requisitos discriminatórios no JD (gênero, idade, etnia, religião,
       deficiência, estado civil, orientação sexual, gravidez, aparência,
       classe social, política, nacionalidade, saúde)
    🔒 L2 Implicit: Detecta termos proxy enviesados ("dinâmico" → age proxy,
       "boa aparência" → appearance proxy) — alerta (log only)
    Input + Output check via check_fairness em jd_generation.py

 5  PII Masking remove dados sensíveis
    4 camadas pré-LLM: CPF → [CPF_MASKED]
    nome → [NAME_1] | endereço → [ADDR_MASKED]
    Campos sensíveis strip via strip_pii_for_llm_prompt
    O LLM NUNCA vê dados pessoais reais

 6  JobDescriptionGeneratorService processa (Claude LLM)
    LLM recebe dados mascarados da vaga
    Gera JD estruturada em markdown:
    → Seções: Sobre, Responsabilidades, Requisitos, Benefícios, Diversidade
    → SEO title + tags
    Anti-sycophancy block (FULL variant) no system prompt
    CircuitBreaker: circuit "anthropic" (failure_threshold=5, recovery=30s)
    🧠 SemanticSearch expande skills sugeridas (Gemini 768-dim)
    🧠 PredictiveAnalytics: predict_time_to_fill, predict_optimal_salary

 7  AuditTrail registra decisão
    🔒 audit_service.log_decision ativo em jd_generation.py
    Registro: LLM input mascarado, output gerado, FairnessGuard results
    Append-only, retenção 730-1825 dias (SOX)
    🧠 LearningLoop captura edições do wizard (salary, skills, benefits)
    🧠 TemplateLearning: após 3 vagas similares, gera template automático

 8  Resposta ao recrutador (PII demasked)
    JD gerada com dados restaurados (nomes, endereços reais)
    FairnessGuard warnings incluídos (se houver L2 alerts)
    Frontend renderiza JD no modal de edição
    Dados persistidos via save_job_draft

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E2)                                          │
│  1. FairnessGuard L1/L2 — input+output check no JD ●                        │
│  2. PII Masking — 4 camadas pré-LLM ●                                       │
│  3. AntiSycophancy FULL — verificação de premissas ●                         │
│  4. CircuitBreaker — circuit "anthropic" ●                                   │
│  5. AuditTrail — log de geração de JD ● (edições manuais ◐)                │
│  6. LearningLoop — captura silenciosa de edições ●                           │
│  7. TemplateLearning — auto-template após 3 vagas similares ●               │
│  8. PredictiveAnalytics — predict TTF + salary ●                             │
│  9. SemanticSearch — expansão de skills ●                                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E3 — CONFIGURAR ROTEIRO WSI — 9 STEPS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Configuração de Roteiro WSI (cv_screening) — 9 STEPS         │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Consultor acessa TAB CONFIGURAÇÕES → SEÇÃO PERGUNTAS Triagem
    POST /api/v1/wsi/generate-questions
    Body: { job_id, mode: "complete"|"compact", job_description, requirements }
    Authorization: Bearer <jwt_token>

 2  DomainOrchestrator roteia + GuardrailCheck
    Identifica domínio = cv_screening
    GuardrailRepository (3 níveis): global → tenant → domain
    HiringPolicy (per-tenant) carregado
    PromptInjectionGuard ativado

 3  EnhancedAgentMixin._setup_enhanced()
    Capabilities injetadas:
    FairnessGuard (3 layers) | PII Masking (4 layers)
    AuditTrail | ConfidenceNode
    AntiSycophancy | WorkingMemory | CircuitBreaker
    LearningLoop | ConversationMemory | SemanticSearch

 4  JobDescriptionGeneratorService (se JD ausente)
    Se o JD não existe ou precisa ajuste, gera/melhora antes
    Mesmo fluxo da E2 (Claude LLM, FG L1/L2, PII Masking)
    Resultado: JD completa como base para perguntas WSI

 5  FairnessGuard filtra ANTES do LLM
    🔒 L1 Explicit: Valida cada pergunta candidata contra ~350 patterns
    🔒 L2 Implicit: Detecta perguntas com proxy bias
    check_fairness per-question em wsi_questions.py
    Bloqueia perguntas que violem 13 categorias protegidas

 6  PII Masking + strip do JD
    strip_pii_for_llm_prompt aplica 4 camadas
    JD enviado ao LLM sem dados identificáveis

 7  WSIQuestionGenerator processa (Gemini LLM)
    Recebe JD mascarada + requisitos da vaga
    Gera perguntas WSI em blocos estruturados:
    → Bloco 2: Técnico (Bloom 1-6, Dreyfus 1-5)
    → Bloco 3: Comportamental (Big Five traits)
    → Bloco 4: Situacional (cenários práticos)
    → Bloco 5: Cultural Fit
    Cada WSIQuestionBlock: block_id, block_type, question, competency,
    bloom_level, dreyfus_level, big_five_trait, max_score, trait_weight
    🧠 SemanticSearch expande competências sugeridas

 8  FactChecker verifica APÓS o LLM
    🔒 4 tipos de verificação:
    → Experiência declarada: claims vs dados de contexto
    → Certificações: validade técnica
    → Período na empresa: coerência temporal
    → Habilidades técnicas: relevância para a vaga
    Claim inconsistente → flag para revisão
    enable_fact_checker=True por default em DomainWorkflow._post_check

 9  AuditTrail registra + Resposta ao consultor
    🔒 audit_service.log_decision ativo em wsi_questions.py
    Registro: perguntas geradas, FG results, fact-check flags
    Append-only, retenção SOX
    🧠 LearningLoop captura edições nas perguntas
    Resposta: lista de perguntas WSI para revisão/ajuste no modal

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E3)                                          │
│  1. FairnessGuard L1/L2 — per-question check ●                              │
│  2. PII Masking — 4 camadas pré-LLM ●                                       │
│  3. FactChecker — 4 tipos de verificação pós-LLM ●                          │
│  4. AuditTrail — log de geração de roteiro WSI ●                             │
│  5. LearningLoop — captura edições de perguntas ●                            │
│  6. SemanticSearch — expansão de competências ●                              │
│  7. ConversationMemory — tracking da vaga ativa ●                            │
│  STATUS: Compliance completo para esta etapa ✓                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E4 — BUSCAR CANDIDATOS (Funil de Talentos) — 10 STEPS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Busca de Candidatos (sourcing) — 10 STEPS                    │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Consultor acessa Funil de Talentos
    GET /api/v1/candidates/search?query=...&skills=...&location=...
    Modos de busca: IA Natural | Boolean | Perfil Similar |
                    Job Description | Archetypes
    Authorization: Bearer <jwt_token>

 2  DomainOrchestrator roteia via CascadedRouter (6 tiers)
    Tier 0: MemoryResolver — resolve pronomes ("ele", "essa vaga")
    Tier 1: LRU in-process — hash MD5, O(1)
    Tier 2: Redis hash cache — distribuído
    Tier 3: VectorSemanticCache — pgvector, cosine ≥ 0.92
    Tier 4: FastRouter — regex/keyword, confiança ≥ 0.7
    Tier 5: LLM Cascade — Gemini (produção)
    Domínio destino = sourcing
    GuardrailRepository (3 níveis) + HiringPolicy carregado

 3  EnhancedAgentMixin._setup_enhanced()
    Capabilities completas injetadas:
    FairnessGuard (3 layers) | PII Masking (4 layers)
    AuditTrail | BiasAuditSnapshot | ConfidenceNode
    AntiSycophancy OPERATIONAL | WorkingMemory | LongTermMemory
    CircuitBreaker | LearningLoop | Calibration
    ScoreNormalization | RoutingAdaptativo | ModelDrift
    PredictiveAnalytics | ConversationMemory | SemanticSearch

 4  FairnessGuard filtra ANTES do LLM
    🔒 L1 Explicit: Bloqueia buscas discriminatórias (MainOrchestrator L35-47)
    🔒 L2 Implicit: Alerta proxy terms na busca (MainOrchestrator L48-62)
    🔒 L3 Semantic (setor-condicionada): Análise semântica profunda
       Setores com L3 ativo: tech, financeiro, saude, rpo
       check_with_sector() ativo em sourcing_agent, RAG pipeline
    _LEARNING_PROTECTED_FIELDS bloqueia learning de: gender, age, ethnicity,
    marital_status, photo, institution, address, religion, disability, cv_gaps

 5  PII Masking + anonimização
    4 camadas pré-LLM para candidatos
    strip_pii_for_llm_prompt em todos os perfis
    ToonService anonymize=True para modo anônimo (LGPD)

 6  Motor de Busca multi-tier
    Busca 2-tier: Local (PostgreSQL, gratuito) → Global (Pearch AI 190M+, pago)
    Elasticsearch + PGVector + WRF (Weighted Rank Fusion):
    → ES Score Drop Analyzer + PGV Gap Analyzer (pré-WRF)
    → WRF Dynamic K (ajuste por nível de qualificação)
    → LLM Job Classification para otimização de K values
    🧠 SemanticSearch: expansão semântica de skills/títulos/indústrias
       (Gemini text-embedding-004, 768-dim, Redis cache)
    CircuitBreaker: circuit "pearch" (failure_threshold=3, recovery=60s)

 7  Ag.2 SourcingReActAgent processa
    ReAct loop: max_iterations=5, max_tool_calls=3
    Tools: search_candidates, analyze_profile, score_candidate,
           compare_candidates, rank_candidates, generate_message
    WorkingMemory + LongTermMemory ativos
    🧠 RoutingAdaptativo: confidence multipliers 0.8x-1.2x por domínio

 8  FactChecker + ConfidenceNode + BiasAuditSnapshot
    🔒 FactChecker: valida claims nas análises LIA
       enable_fact_checker=True por default em DomainWorkflow._post_check
    🔒 ConfidenceNode: score calibrado para comparabilidade real
       confidence_score = tool_success_ratio × 0.7 + completion_ratio × 0.3
    🔒 BiasAuditSnapshot: Four-Fifths Rule
       Detecta se taxa de aprovação de grupo demográfico < 80% de outro
    🧠 ScoreNormalization: ajusta por difficulty_coefficient
    🧠 Calibration: feedback explícito/implícito sobre scores

 9  AuditTrail + Learning
    🔒 Audit: log de buscas + scores ◐ (precisa ativar em candidates.py)
    🧠 LearningLoop: captura accept/modify/reject de candidatos
    🧠 ModelDrift: monitora score_drift + approval_drift (7-day window)
    🧠 PredictiveAnalytics: predict_skill_success integrado

 10 Resposta ao recrutador (PII demasked)
    Tabela de candidatos: 10 por vez + "Carregar +10"
    Preview inline com 4 tabs: Perfil | Atividades | Arquivos | Pareceres
    Like/Dislike feedback por candidato (otimiza busca)
    Prompt expandido da LIA (análise, comparação, ranking)
    Dados PII restaurados na response final

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E4)                                          │
│  1. FairnessGuard L1/L2/L3 — busca + análise + response ●                   │
│  2. PII Masking — 4 camadas + ToonService anonymize ●                        │
│  3. FactChecker — valida claims pós-LLM ●                                    │
│  4. BiasAuditSnapshot — Four-Fifths Rule ●                                   │
│  5. ConfidenceNode — calibração de score ●                                   │
│  6. ScoreNormalization — difficulty_coefficient ●                             │
│  7. AuditTrail — buscas + scores ◐ (precisa ativar)                         │
│  8. LearningLoop — captura silenciosa ●                                      │
│  9. Calibration — feedback dual (explícito + implícito) ●                    │
│ 10. ModelDrift — 4 dimensões monitoradas ●                                   │
│ 11. SemanticSearch — expansão 768-dim ●                                      │
│ 12. RoutingAdaptativo — confidence multipliers ●                             │
│ 13. PredictiveAnalytics — predict_skill_success ●                            │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E5 — APROVAR MAPEADOS (Gate 1) — 9 STEPS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Aprovação Gate 1 (pipeline + kanban) — 9 STEPS               │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Consultor no Kanban board move candidato(s)
    POST /api/v1/pipeline/transition
    Body: { candidate_ids, from_stage, to_stage, action: "approve"|"reject",
            reason, job_id }
    Aprovação INDIVIDUAL ou EM MASSA (max 100)
    Drag-and-drop manual para qualquer coluna
    Authorization: Bearer <jwt_token>

 2  DomainOrchestrator + PolicyEngine
    Domínio = pipeline + kanban
    🔒 PolicyEngine: ALPHA1_SECTOR_RULES por setor
       Autonomy levels + HITL thresholds
       Determina se ação precisa confirmação humana
    SmartTransitionModal: etapas críticas pedem confirmação
    GuardrailRepository (3 níveis) carregado

 3  EnhancedAgentMixin._setup_enhanced()
    Capabilities injetadas:
    FairnessGuard (3 layers) | PII Masking (4 layers)
    AuditTrail | ConfidenceNode | BiasAuditSnapshot
    AntiSycophancy OPERATIONAL | WorkingMemory
    CircuitBreaker | LearningLoop | Calibration
    RoutingAdaptativo | ModelDrift | ConversationMemory

 4  FairnessGuard valida rejeições
    🔒 Auto-check em reject_candidate (candidate_tools.py)
    🔒 FG L3 pré-check no PipelineTransitionAgent
    check_rejection_fairness: motivo de rejeição analisado contra
    13 categorias protegidas
    Se motivo discriminatório → BLOCK + alerta ao consultor

 5  PipelineTransitionAgent interpreta contexto
    LangGraph ReAct (invocação direta, não via registry)
    POST /api/v1/pipeline/interpret-context
    Tools: validate_transition, get_candidate_profile,
           get_candidate_wsi_scores, suggest_sub_status,
           check_rejection_fairness, extract_preferences
    20 tools disponíveis no registry

 6  LGPD: Consentimento antes de contato
    🔒 CandidateChannelSelector.select_channels verifica:
       → LGPDConsent (consentimento registrado)
       → CandidateOptOut (opt-out por canal)
    WhatsApp: estado AWAITING_CONSENT com mensagem explícita
    Sem consentimento → contato bloqueado

 7  PolicyEngine: Escalation + HITL
    🔒 trigger_escalation quando AI confidence < threshold
    Threshold configurável por setor (ALPHA1_SECTOR_RULES)
    Se HITL necessário → pausa para decisão humana
    Notification: Bell + Teams

 8  AuditTrail + Learning
    🔒 Audit: log de aprovações/rejeições + overrides ◐ (precisa ativar)
    🧠 LearningLoop: captura decisões aceitar/rejeitar/modificar suggestion
    🧠 Calibration: implicit feedback (avançar low-score = sinal)
    🧠 ModelDrift: trigger se approval_drift > 10 p.p.
    🧠 RoutingAdaptativo: correções de rota alimentam ajustes

 9  Resposta + Disparo de próxima etapa
    Aprovados → LIA dispara contato (E6)
    Reprovados → LIA envia feedback (E9B)
    ⚡ Inscritos via web BYPASS Gate 1 → triagem automática
    Kanban board atualizado em real-time (ActionCable/WebSocket)

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E5)                                          │
│  1. FairnessGuard — auto-check em rejeções + FG L3 pré-check ●              │
│  2. PolicyEngine — HITL thresholds por setor ●                               │
│  3. LGPD — consent check antes de contato ●                                  │
│  4. PII Masking — ativo globalmente ●                                        │
│  5. Escalation — trigger quando AI confidence < threshold ●                  │
│  6. AuditTrail — aprovações/rejeições ◐ (precisa ativar)                    │
│  7. LearningLoop — captura decisões ●                                        │
│  8. Calibration — implicit feedback ●                                        │
│  9. ModelDrift — approval_drift monitoring ●                                 │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E6 — CONTATO VIA EMAIL + FOLLOW-UP — 8 STEPS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Contato Email + Follow-up (communication) — 8 STEPS          │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Ag.0 MainOrchestrator dispara contato após Gate 1
    POST /api/v1/communications/send
    Body: { candidate_id, job_id, channel: "email", template_id,
            personalization: { candidate_name, job_title, screening_link } }
    Contato primário: SEMPRE email

 2  DomainOrchestrator roteia
    Domínio = communication
    GuardrailRepository carregado
    Rate limiting verificado: RateLimitRule sliding window por empresa/dia
    CircuitBreaker: circuits "sendgrid" + "resend" (critical tier)

 3  CommunicationReActAgent (Ag.7) processa
    ReAct loop: max_iterations=5
    Tools registradas (communication_tool_registry.py):
    → send_email, send_whatsapp, get_communication_history,
      schedule_message, check_rate_limit
    Legacy tools (communication_tools.py): send_feedback, send_bulk_email

 4  PII Masking em logs
    🔒 PIIMaskingFilter: emails não logam dados pessoais
    Conteúdo do email NÃO mascarado (é para o candidato)
    Logs de envio: PII stripped

 5  LGPD: Opt-out + Consent
    🔒 Opt-out link incluído no email (obrigatório)
    communication_optout.py: HMAC-signed tokens
    ConsentEvent auditável: registro de consentimento/revogação
    Se opt-out registrado → canal bloqueado para futuro

 6  Email enviado com 2 opções
    A) Link para triagem via CHAT WEB (canal principal)
    B) Solicita nº celular → WhatsApp (canal secundário)
    🧠 A/B Testing: variantes de template de email
       seed_email_ab_tests cria 3 experimentos no startup
    🧠 TemplateLearning: templates de email aprendidos

 7  Follow-up automático (7 dias)
    Se candidato NÃO abre/clica email:
    → Re-envio automático a cada 24h por 7 dias consecutivos
    → Após 7 dias sem resposta → status "sem_resposta"
    → Consultor notificado (Teams)
    Celery Beat schedule para verificação periódica

 8  AuditTrail + Response
    🔒 Audit: log de envios + opens + clicks ◐ (precisa ativar)
    🧠 ConversationMemory: tracking de candidatos contatados
    Resposta ao consultor: confirmação de envio + tracking status

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E6)                                          │
│  1. LGPD — opt-out link obrigatório + HMAC-signed tokens ●                  │
│  2. PII Masking — logs mascarados ●                                          │
│  3. RateLimiting — sliding window por empresa/dia ●                          │
│  4. CircuitBreaker — circuits "sendgrid" + "resend" ●                        │
│  5. A/B Testing — variantes de template ●                                    │
│  6. TemplateLearning — templates aprendidos ●                                │
│  7. AuditTrail — envios/opens/clicks ◐ (precisa ativar)                     │
│  8. Follow-up automático — 7 dias, Celery Beat ●                             │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E7 — TRIAGEM WSI (cv_screening + WSI) — 11 STEPS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Triagem (cv_screening + WSI) — 11 STEPS                      │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Frontend (Next.js 15) envia POST /api/chat
    Request logado via middleware (X-Request-ID auto-gerado)
    Canais: Chat web (link do email) | WhatsApp | Voz (Twilio/OpenMic.ai)
    Candidato clica link do email → página /triagem/[token]

 2  DomainOrchestrator roteia + GuardrailCheck
    Identifica domínio = cv_screening
    GuardrailRepository (3 níveis): global → tenant → domain
    HiringPolicy (per-tenant) carregado
    PromptInjectionGuard ativado

 3  EnhancedAgentMixin._setup_enhanced()
    16 capabilities injetadas automaticamente:
    FairnessGuard (3 layers) | PII Masking (4 layers)
    AuditTrail | BiasAuditSnapshot | ConfidenceNode
    AntiSycophancy | WorkingMemory | CircuitBreaker
    LearningLoop | Calibration | ScoreNormalization | ModelDrift

 4  FairnessGuard filtra ANTES do LLM
    3 camadas: (1) Regex → bloqueia "rejeitar por idade"
    (2) Implícito → detecta vieses indiretos ("bairro nobre")
    (3) LLM → análise semântica de fairness
    check_with_sector() ativo em rubric_evaluation.py
    Setores com L3: tech, financeiro, saude, rpo

 5  PII Masking remove dados sensíveis
    4 camadas pré-LLM: CPF → [CPF_MASKED]
    nome → [NAME_1] | endereço → [ADDR_MASKED]
    O LLM NUNCA vê dados pessoais reais

 6  WSI Interview Graph processa (1.141L)
    8 stages: INIT → LOAD → GENERATE → AWAIT →
    VALIDATE → SCORE → ADVANCE → COMPLETE
    Bloom (1-6) + Dreyfus (1-5) + Big Five (OCEAN)
    PostgresSaver checkpoint — sessões de 30-120 min via WebSocket
    interview_level: "quick" | "standard" | "full"
    HITL: interrupt_before=["lg_generate_feedback"]

 7  Gemini/Claude processa (dados mascarados)
    LLM recebe [CPF_MASKED], [NAME_1], etc.
    Anti-sycophancy block no system prompt
    CircuitBreaker protege contra falha
    Temperature: 0.3 (LLM_AGENT_TEMPERATURE)

 8  FactChecker verifica APÓS o LLM
    🔒 4 tipos: experiência declarada, certificações,
    período na empresa, habilidades técnicas
    Claim inconsistente → flag para revisão
    enable_fact_checker=True por default

 9  ConfidenceNode calibra + BiasAuditSnapshot
    Score calibrado para comparabilidade real
    confidence_score = tool_success_ratio × 0.7 + completion_ratio × 0.3
    🔒 Four-Fifths Rule — detecta se taxa de aprovação
    de grupo demográfico < 80% de outro
    🧠 ScoreNormalization: ajusta por difficulty_coefficient
    🧠 Calibration: feedback dual sobre scores WSI

 10 AuditTrail registra TUDO (append-only)
    Registro imutável: request, fairness check, PII masks,
    LLM response, fact-check, scores, bias audit
    Retenção: 7 anos (SOX). Não pode ser alterado
    🧠 LearningLoop: captura padrões de resposta por competência
    🧠 ModelDrift: monitora drift em scores WSI (7-day window)

 11 Resposta ao recrutador (PII demasked)
    WSIFinalReport com recomendação + 3 scores
    (tech/behavioral) + wsi_final_score
    Dados PII restaurados na resposta (nunca no audit)
    Recomendação: "aprovado" | "aguardando" | "reprovado"

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E7)                                          │
│  1. PII nunca chega ao LLM — 4 camadas de mascaramento pré-LLM ●            │
│  2. FairnessGuard 3 layers — bloqueia vieses explícitos e implícitos ●       │
│  3. BiasAuditSnapshot — Four-Fifths Rule detecta discriminação estatística ● │
│  4. ConfidenceNode — calibra scores para serem comparáveis e significativos ●│
│  5. FactChecker pós-LLM — verifica claims factuais do candidato ●            │
│  6. Audit Trail SOX — registro imutável, 7 anos, append-only ◐              │
│  7. WSI com Bloom+Dreyfus — progressão de dificuldade + cobertura ●          │
│  8. LGPD consent — WelcomeCard com checkbox explícito obrigatório ●          │
│  9. Anti-sycophancy — bloqueia concordância automática ●                     │
│ 10. ScoreNormalization — difficulty_coefficient por versão de roteiro ●       │
│ 11. Voice Analysis — STT Deepgram/Whisper + TTS OpenAI ●                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E7A — TRIAGEM ABANDONADA — 5 STEPS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Triagem Abandonada (cv_screening) — 5 STEPS                  │
└──────────────────────────────────────────────────────────────────────────────┘

 1  Detecção de abandono
    Candidato inicia WSI mas para de responder
    Celery Beat: task "wsi-abandoned-check" roda a cada 4h
    Verifica WSIInterviewState: last_activity_at vs now()
    Progresso parcial SALVO via PostgresSaver checkpoint

 2  1º Lembrete (48h sem atividade)
    Timeout: 48h sem atividade detectado
    Ag.7 CommunicationReActAgent envia lembrete
    Canal: mesmo da triagem (chat web, WhatsApp ou voz)
    Mensagem personalizada com progresso parcial

 3  2º Lembrete (+48h sem retorno)
    96h total sem atividade
    Segundo lembrete automático enviado
    Tom mais urgente, informa deadline

 4  Alerta ao consultor
    Após 2º lembrete sem retorno
    Alerta via Teams ao consultor responsável
    Candidato marcado como "triagem_abandonada"
    Consultor decide: re-engajar ou descartar

 5  Estado final
    Progresso parcial permanece salvo
    Scores parciais disponíveis para consultor
    Candidato pode retomar se consultor re-enviar link
    Audit: abandono registrado com timestamps

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E7A)                                         │
│  1. Checkpoint — progresso parcial salvo (PostgresSaver) ●                   │
│  2. Celery Beat — verificação automática a cada 4h ●                         │
│  3. Notification — alerta ao consultor via Teams ●                            │
│  4. LGPD — dados parciais com consentimento original ●                       │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E7B — FEEDBACK PÓS-TRIAGEM — 4 STEPS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Feedback Pós-Triagem (cv_screening) — 4 STEPS                │
└──────────────────────────────────────────────────────────────────────────────┘

 1  Triagem WSI completa
    Ag.4 WSIInterviewGraph atinge stage GENERATE_FEEDBACK
    HITL: interrupt_before=["lg_generate_feedback"]
    Score WSI calculado + recomendação gerada

 2  Feedback gerado ao candidato
    Ag.4 agradece participação
    Dá feedback construtivo sobre performance
    Informa próximos passos do processo
    Canal: mesmo da triagem (chat web, WhatsApp ou voz)

 3  FairnessGuard valida feedback
    🔒 FG L1/L2 em rubric_evaluation.py
    Feedback não pode conter viés ou dados discriminatórios
    PipelineFeedbackTool._remove_score_references: strip scores numéricos
    FairnessGuard sanitiza texto do feedback

 4  Notificação ao consultor
    Alerta via Teams: "Triagem WSI concluída para [candidato]"
    Score WSI + parecer LIA disponíveis na plataforma
    Candidato aguarda decisão Gate 2

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E7B)                                         │
│  1. FairnessGuard — feedback sem viés ●                                      │
│  2. Score stripping — remove scores numéricos do feedback ●                  │
│  3. HITL — interrupt_before para review humano ●                             │
│  4. Notification — alerta ao consultor ●                                     │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E8 — APROVAR/REPROVAR TRIADOS (Gate 2) — 8 STEPS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Aprovação Gate 2 (pipeline + kanban + analytics) — 8 STEPS    │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Consultor recebeu alerta Teams (E7B)
    Acessa Kanban board: POST /api/v1/pipeline/transition
    Body: { candidate_ids, from_stage: "triagem", to_stage: "shortlist"|"rejected",
            action, reason, wsi_reviewed: true }
    Revisa score WSI + parecer LIA antes de decidir

 2  DomainOrchestrator + PolicyEngine
    Domínio = pipeline + kanban + analytics
    🔒 PolicyEngine: HITL thresholds por setor (ALPHA1_SECTOR_RULES)
    Determina autonomia: AI pode decidir sozinha vs precisa HITL

 3  FairnessGuard valida rejeições
    🔒 Auto-check em reject_candidate (candidate_tools.py)
    🔒 FG L3 pré-check no PipelineTransitionAgent
    Motivo de rejeição analisado contra 13 categorias
    Se discriminatório → BLOCK + alerta

 4  LGPD: Sanitização de dados para próxima etapa
    🔒 PipelineFeedbackTool._remove_score_references: strip scores numéricos
    🔒 FairnessGuard sanitiza feedback
    🔒 ats_integration_stage_context.py: define campos internos vs ATS
    Dados compartilhados com próxima etapa minimizados

 5  PersonalizedFeedbackService (Ag.7) gera parecer
    Se REPROVADO: gera feedback personalizado para candidato
    FairnessGuard valida feedback antes de enviar
    Embedding do perfil gerado para re-discovery futuro
    _generate_rediscovery_embedding via embedding_service.py

 6  ConfidenceNode + BiasAuditSnapshot
    🔒 Score calibrado para comparabilidade
    🔒 Four-Fifths Rule: verifica equidade estatística Gate 2
    Se anomalia → alerta ao consultor

 7  AuditTrail + Learning
    🔒 Audit: log de aprovação/rejeição Gate 2 ◐ (precisa ativar)
    🧠 LearningLoop: feedback sobre decisões Gate 2
    🧠 Calibration: implicit feedback (avançar low-WSI = sinal)
    🧠 ModelDrift: monitora approval_drift Gate 2
    🧠 RoutingAdaptativo: correções entre domínios

 8  Resultado + Disparo
    Aprovados → SHORT LIST → E9A (agendar entrevista)
    Reprovados → E9B (enviar feedback)
    Kanban atualizado em real-time
    🧠 LongTermMemory: episódio salvo para referência futura

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E8)                                          │
│  1. FairnessGuard — auto-check rejeções + FG L3 ●                           │
│  2. PolicyEngine — HITL thresholds por setor ●                               │
│  3. LGPD — data minimization + score stripping ●                             │
│  4. BiasAuditSnapshot — Four-Fifths Rule Gate 2 ●                            │
│  5. AuditTrail — aprovações Gate 2 ◐ (precisa ativar)                       │
│  6. LearningLoop + Calibration + ModelDrift ●                                │
│  7. Embedding — rediscovery de candidatos reprovados ●                       │
│  8. LongTermMemory — episódios salvos ●                                      │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E9A — AGENDAR ENTREVISTA — 7 STEPS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Agendamento de Entrevista (interview_scheduling) — 7 STEPS    │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Candidato APROVADO no Gate 2 → trigger automático
    POST /api/v1/scheduling/create
    Body: { candidate_id, job_id, interview_type, preferred_dates }
    Authorization: Bearer <jwt_token>

 2  DomainOrchestrator roteia
    Domínio = interview_scheduling
    Ag.6 InterviewGraph ativado
    GuardrailRepository carregado
    CircuitBreaker: circuit "google_calendar" (recovery=60s)

 3  Ag.6 InterviewGraph processa
    LangGraph StateGraph: 6 nós
    Tools: schedule_interview, check_availability,
           reschedule_interview, cancel_interview
    Busca horários disponíveis no Google Calendar
    Se NÃO encontra horário → alerta ao consultor via Teams

 4  LGPD: Data Minimization no ICS
    🔒 SchedulingService.generate_ics_content:
    Apenas dtstart/dtend/summary/location/attendee
    SEM dados sensíveis do candidato no arquivo ICS
    Mínimo necessário para o agendamento funcionar

 5  Comunicação multi-canal
    Email + WhatsApp ao candidato (data/hora + link reunião)
    Ag.7 CommunicationReActAgent envia por ambos canais
    Template personalizado com dados da vaga e entrevistador

 6  AuditTrail + Learning
    🔒 Audit: log de agendamento ◐ (precisa ativar)
    🧠 LearningLoop: feedback sobre qualidade da sugestão
    🧠 LongTermMemory: episódio salvo (EnhancedAgentMixin._post_loop_learning)

 7  Resposta ao consultor
    Confirmação de agendamento + detalhes
    Calendar invite enviado a todos os participantes
    Status atualizado no Kanban

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E9A)                                         │
│  1. LGPD — data minimization no ICS ●                                        │
│  2. CircuitBreaker — circuit "google_calendar" ●                             │
│  3. PII Masking — ativo globalmente ●                                        │
│  4. AuditTrail — agendamento ◐ (precisa ativar)                             │
│  5. LongTermMemory — episódios salvos ●                                      │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E9B — ENVIAR FEEDBACK (Reprovado) — 6 STEPS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Feedback para Reprovado (communication) — 6 STEPS             │
└──────────────────────────────────────────────────────────────────────────────┘

 1  Trigger: Candidato REPROVADO no Gate 2
    Ag.0 MainOrchestrator dispara feedback
    Domínio = communication + cv_screening

 2  PersonalizedFeedbackService (Ag.7) gera feedback
    Analisa perfil + scores WSI + motivo de rejeição
    Gera feedback construtivo e personalizado
    🔒 FairnessGuard L1/L2: valida feedback antes de envio
    PipelineFeedbackTool._remove_score_references: strip scores

 3  PII Masking + FairnessGuard
    🔒 PII: dados pessoais protegidos em logs
    🔒 FG: feedback não contém viés ou discriminação
    Texto sanitizado por FairnessGuard

 4  CommunicationReActAgent envia
    Email (primário) + WhatsApp (se número disponível)
    Template personalizado com feedback construtivo
    🧠 A/B Testing: variantes de template de feedback
    🧠 TemplateLearning: templates aprendidos

 5  Embedding para rediscovery
    🧠 _generate_rediscovery_embedding:
    Gera embedding do perfil (Gemini text-embedding-004, 768-dim)
    Salvo via embedding_cache_service.py
    Permite re-discovery em vagas futuras similares

 6  AuditTrail + Response
    🔒 Audit: log de feedback enviado ◐ (precisa ativar)
    🧠 LearningLoop: feedback sobre qualidade do feedback gerado
    Status final do candidato atualizado no Kanban
    🧠 LongTermMemory: episódio completo salvo

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E9B)                                         │
│  1. FairnessGuard L1/L2 — feedback sem viés ●                                │
│  2. Score stripping — remove scores numéricos ●                              │
│  3. PII Masking — dados protegidos ●                                         │
│  4. A/B Testing — variantes de feedback ●                                    │
│  5. TemplateLearning — templates aprendidos ●                                │
│  6. Embedding — rediscovery futuro ●                                         │
│  7. AuditTrail — feedback ◐ (precisa ativar)                                │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## SEÇÃO TRANSVERSAL: GOVERNANÇA TÉCNICA

### Policy Engine — Motor de Políticas por Setor

```
Arquivo: app/services/policy_engine_service.py

ALPHA1_SECTOR_RULES — Regras por setor:
┌──────────────────────────────────────────────────────────────────────────────┐
│  Setor        │ Autonomy  │ HITL Threshold │ FG L3  │ Rate Limit │ Escalation│
│──────────────┼───────────┼────────────────┼────────┼────────────┼───────────│
│  tech         │ medium    │ medium         │ ativo  │ standard   │ ativo     │
│  financeiro   │ low       │ high           │ ativo  │ strict     │ ativo     │
│  saude        │ low       │ high           │ ativo  │ strict     │ ativo     │
│  rpo          │ high      │ low            │ ativo  │ relaxed    │ ativo     │
│  varejo       │ medium    │ medium         │ inativo│ standard   │ ativo     │
│  logistica    │ medium    │ medium         │ inativo│ standard   │ ativo     │
└──────────────────────────────────────────────────────────────────────────────┘

Funcionalidades:
- Autonomy Levels: low (tudo precisa HITL) | medium (ações críticas) | high (auto)
- HITL Thresholds: % de confiança abaixo do qual AI escala para humano
- trigger_escalation: quando AI confidence < threshold por setor
- Rate Limiter: sliding window por empresa/dia/endpoint
- Planos: Starter / Pro / Enterprise (tokens mensais, agentes, automações)
  PLAN_LIMITS_ENFORCE=true
```

### CircuitBreaker — 14+1 Circuits

```
Arquivo: app/shared/resilience/circuit_breaker.py

Padrão de 3 Estados: CLOSED → OPEN → HALF_OPEN → CLOSED
  CLOSED: chamadas passam; cada falha incrementa contador
  OPEN: todas rejeitadas com CircuitBreakerError + retry_after
  HALF_OPEN: permite chamadas limitadas para testar recuperação

14 circuits pré-configurados:
┌──────────────────────────────────────────────────────────────────────────────┐
│  Circuit         │ Failures │ Recovery │ Success │ Timeout │ Tier      │
│─────────────────┼──────────┼──────────┼─────────┼─────────┼───────────│
│  anthropic       │ 5        │ 30s      │ 2       │ 60s     │ critical  │
│  openai          │ 5        │ 30s      │ 2       │ 60s     │ critical  │
│  gemini          │ 5        │ 30s      │ 2       │ 60s     │ high      │
│  pearch          │ 3        │ 60s      │ 2       │ 30s     │ high      │
│  workos          │ 5        │ 30s      │ 2       │ 15s     │ critical  │
│  merge           │ 5        │ 45s      │ 2       │ 30s     │ high      │
│  google_calendar │ 5        │ 60s      │ 2       │ 30s     │ medium    │
│  gupy            │ 5        │ 45s      │ 2       │ 30s     │ high      │
│  pandape         │ 5        │ 45s      │ 2       │ 30s     │ high      │
│  sendgrid        │ 5        │ 30s      │ 2       │ 30s     │ critical  │
│  resend          │ 5        │ 30s      │ 2       │ 30s     │ high      │
│  iugu            │ 3        │ 60s      │ 2       │ 30s     │ medium    │
│  vindi           │ 3        │ 60s      │ 2       │ 30s     │ medium    │
│  llm_react_reason│ 3        │ 60s      │ 2       │ 30s     │ (ReAct)   │
└──────────────────────────────────────────────────────────────────────────────┘

Notificação de Circuit Open (COMP-3):
  Redis dedup: máximo 1 alerta por circuit por hora
  Canais: Bell (in-app) + Teams (webhook)
  Mensagem: "⚡ Circuit Breaker ABERTO: {service_name}"
  Prometheus: circuit_breaker_state (0=closed, 1=half_open, 2=open)

Degraded Mode Responses (14 mensagens PT-BR):
  Cada serviço tem mensagem amigável quando circuit OPEN
  Fallback genérico: "Este serviço está temporariamente indisponível."
```

### PromptInjectionGuard

```
Ativado em todo request que chega ao DomainOrchestrator
Detecta tentativas de prompt injection no input do usuário
Bloqueia execução se injeção detectada
Registra tentativa no audit log
```

### Anti-Sycophancy — 3 Variantes

```
Arquivo: app/shared/prompts/anti_sycophancy_block.py

ANTI_SYCOPHANCY_OPERATIONAL → Talent, Kanban, Jobs Management
  5 regras: não concordar com filtros discriminatórios,
  verificar antes de confirmar, discordância com dados

ANTI_SYCOPHANCY_FULL → Wizard, Policy
  5 regras + VERIFICAÇÃO DE PREMISSAS (5 sub-regras)
  Mais restritivo: verificar histórico, nunca mudar silenciosamente

ANTI_SYCOPHANCY_ORCHESTRATOR → Orchestrator
  Versão compacta (1 frase) — ponto de entrada global

Crença #11 do Manifesto WeDOTalent:
"Anti-sycophancy em 100% das interações IA."
```

---

## SEÇÃO TRANSVERSAL: COMPLIANCE TÉCNICO

### FairnessGuard — 3 Camadas

```
Arquivo: app/shared/compliance/fairness_guard.py

Layer 1: Explicit Bias Block
  ~350+ patterns em 13 categorias:
  gender, age, ethnicity, religion, disability, marital_status,
  sexual_orientation, pregnancy, appearance, social_class,
  political, nationality, health
  Ação: BLOCK — impede processamento
  Integração: MainOrchestrator (pré-roteamento)

Layer 2: Implicit Bias Soft Warning
  Proxy terms detectados:
  "dinâmico" → age proxy | "boa aparência" → appearance proxy
  Ação: WARN — permite com alerta (log only)
  Integração: MainOrchestrator (pré-roteamento)

Layer 3: Semantic Analysis (LLM-based)
  Provider: Gemini (análise semântica profunda)
  Ação: WARN ou BLOCK dependendo da severidade
  Condicionada por setor: ALPHA1_SECTOR_RULES[sector].fairness_layer3_enabled
  Ativo em: tech, financeiro, saude, rpo
  Inativo em: varejo, logistica

Protected Fields (Learning Loop):
  _LEARNING_PROTECTED_FIELDS = {gender, age, ethnicity, marital_status,
  photo, institution, address, religion, disability, cv_gaps}
  validate_learning_batch() bloqueia patterns discriminatórios ANTES de persistir

Pontos de integração:
  - MainOrchestrator L35-62 (L1/L2 pré-roteamento)
  - jd_generation.py (L1/L2 input+output)
  - wsi_questions.py (per-question check)
  - rubric_evaluation.py (reasoning check)
  - candidate_tools.py (reject_candidate auto-check)
  - PipelineTransitionAgent (L3 pré-check)
  - sourcing_agent (L3 via check_with_sector)
  - communication_tools (L3)
  - RAG pipeline (L3)
```

### PII Masking — 4 Camadas

```
Arquivo: app/shared/pii_masking.py

Camada 1: CPF → [CPF_MASKED]
Camada 2: nome → [NAME_1], [NAME_2], etc.
Camada 3: endereço → [ADDR_MASKED]
Camada 4: campos sensíveis → [FIELD_MASKED]

Função: strip_pii_for_llm_prompt (global)
PIIMaskingFilter: filtro global de logs
Presidio: opt-in para detecção avançada

Regra absoluta: O LLM NUNCA vê dados pessoais reais
Demasking: dados restaurados na response final ao recrutador
Audit: dados mascarados no registro (nunca reais)
```

### FactChecker — 4 Tipos de Verificação

```
Arquivo: app/shared/compliance/fact_checker.py

Tipo 1: Experiência declarada — claims vs dados de contexto
Tipo 2: Certificações — validade técnica
Tipo 3: Período na empresa — coerência temporal
Tipo 4: Habilidades técnicas — relevância para a vaga

Integração: DomainWorkflow._post_check (enable_fact_checker=True por default)
Claim inconsistente → flag para revisão
V5: verificações granulares adicionais (salary, count, %, date)

Pontos de integração:
  - wsi_questions.py (valida claims nas perguntas)
  - sourcing (valida claims nas análises)
  - rubric_evaluation.py (valida scores e claims WSI)
```

### BiasAuditSnapshot — Four-Fifths Rule

```
ConfidenceNode + BiasAuditSnapshot integrados

ConfidenceNode:
  confidence_score = tool_success_ratio × 0.7 + completion_ratio × 0.3
  Score calibrado para comparabilidade real

BiasAuditSnapshot:
  Four-Fifths Rule: se taxa de aprovação de grupo demográfico < 80% de outro
  → alerta automático
  Dados coletados em cada Gate (1 e 2)
  Dashboard de Bias Audit: ○ (pendente — backend coleta dados)
```

### AuditTrail — SOX-Compliant

```
Arquivo: app/shared/compliance/audit_service.py

8 decision types registráveis
Append-only: registros NUNCA podem ser alterados
Retenção: 730-1825 dias (SOX — ~2-5 anos)
record_human_review: registra overrides humanos

O que é registrado:
  - Request original (mascarado)
  - FairnessGuard results (L1/L2/L3)
  - PII masks aplicados
  - LLM response completa
  - FactChecker flags
  - Scores + bias audit
  - Decisão final + motivo

Status de ativação por etapa:
  ● Ativo: jd_generation.py, wsi_questions.py
  ◐ Precisa ativar: auth.py, candidates.py, pipeline tools,
    rubric_evaluation.py, communication
```

---

## SEÇÃO TRANSVERSAL: INTELIGÊNCIA

### 1. Learning Loop (Captura Silenciosa)

```
Arquivo: app/shared/learning/learning_loop_service.py (1137 linhas)
Mecanismo: Observa accept/modify/reject do recrutador sem pedir feedback
Outcomes: accepted | modified | rejected | ignored
Pattern Types: salary_preference, skill_preference, benefit_preference,
               work_model_preference, screening_preference,
               jd_style_preference, source_trust
Confidence: ≥20 samples=high, ≥10=medium, ≥5=low
FairnessGuard: validate_learning_batch() bloqueia discriminação ANTES de persistir
ModelDrift: trigger automático quando feedback rejected/ignored
Snapshot: learning_snapshot_service salva snapshot pré-learning (rollback Z2-01)

Etapas ativas: E2, E3, E4, E5, E7, E8, E9
```

### 2. A/B Testing

```
Arquivo: app/shared/learning/ab_testing_service.py (307 linhas)
Mecanismo: Hash-based traffic splitting (MD5 → bucket 0-9999)
Estatísticas: z-score, p-value (erfc), 95% CI, improvement %
Significância: p < 0.05 AND |improvement| > 5%
Modelo: PromptVariant + ABTestResult
API: GET/POST testes + GET variant via api/v1/ab_testing.py
seed_email_ab_tests: 3 experimentos criados no startup

Etapas ativas: E2, E3, E4, E6, E7, E9
```

### 3. Routing Adaptativo

```
Arquivo: app/services/routing_learning_service.py
Mecanismo: Quando recrutador corrige roteamento, ajusta multipliers
Range: 0.8x (muitos erros) a 1.2x (alta precisão) por domínio
Método: compute_domain_confidence_adjustments(company_id, db)

Etapas ativas: E4, E5, E8
```

### 4. Template Learning

```
Arquivo: app/shared/learning/template_learning_service.py
Mecanismo: Após 3 vagas similares (mesmo setor/seniority), gera template
Métodos: learn_from_job_creation(), suggest_templates_for_improvement()
UNION de fontes corrigida (email + JD + feedback)

Etapas ativas: E2, E6, E9
```

### 5. Calibration

```
Arquivo: app/services/calibration_service.py
Mecanismo: Dual feedback
  Explícito: thumbs up/down do recrutador
  Implícito: avançar candidato low-score = sinal positivo
Output: CalibrationSuggestion (ex: "Reduzir peso de skill técnica em 15%")
Métodos: record_explicit_feedback(), record_implicit_feedback(), generate_suggestions()

Etapas ativas: E4, E5, E7, E8
```

### 6. Score Normalization

```
Arquivo: app/domains/cv_screening/services/score_normalization_service.py
Mecanismo: Ajusta scores baseado no difficulty_coefficient da versão do questionário
Objetivo: Candidatos com versões mais difíceis não penalizados

Etapas ativas: E4, E7
```

### 7. Predictive Analytics

```
Arquivo: app/domains/analytics/services/predictive_analytics_service.py
        + app/services/ml/outcome_predictor.py
API: app/api/v1/predictive_analytics.py
Agent Tools: predictive_tools.py — integrado em agentes

Métodos:
  predict_time_to_fill(db, job_data, company_id) → dias + confidence
  predict_optimal_salary(db, job_data, company_id) → faixa competitiva
  predict_skill_success(db, skill_name, company_id) → probabilidade

Etapas ativas: E2, E4
```

### 8. Model Drift

```
Arquivo: app/services/model_drift_service.py
4 dimensões monitoradas (janela de 7 dias):
  Score Drift: variação > 0.5 pts
  Approval Drift: variação > 10 p.p.
  Cost Drift: aumento significativo de custo LLM
  Latency Drift: degradação de tempo de resposta
Trigger: automático pelo Learning Loop quando feedback negativo acumula
Batch: drift.run_batch — diário 06h Brasília (Celery Beat)
Alerta: 1 trigger=WARNING, 2+=URGENT → Bell + Teams

Etapas ativas: E4, E5, E7, E8
```

### 9. Conversation Memory

```
Arquivo: app/shared/memory/conversation_state.py
Mecanismo: Estado efêmero da sessão de chat
Recursos:
  Entity tracking (última vaga, último candidato mencionado)
  Pronoun resolution ("conte mais sobre ele" → resolve)
  Active filters tracking (filtros persistem na sessão)

Etapas ativas: E2, E3, E4, E5, E6, E7
```

### 10. Semantic Search

```
Arquivo: app/shared/intelligence/semantic_search_service.py
Provider: Gemini text-embedding-004 (768 dimensões)
Cache: Redis para evitar re-embedding
Domínios: Skills, Job Titles, Industries, Locations
Métodos: expand_query(domain, query), expand_skills(), expand_job_titles()
Embedding Service: app/shared/intelligence/embedding_service.py

Etapas ativas: E2, E3, E4
```

### 11. Voice Analysis

```
Arquivo: app/services/voice_service.py
STT Providers: Deepgram (primário), Whisper (fallback)
TTS Provider: OpenAI (voice="nova")
Uso: Triagem WSI por voz — candidato responde por áudio
WSIVoiceOrchestrator: coordena triagem por voz

Etapas ativas: E7
```

### 12. Long-Term Memory

```
Arquivo: libs/agents-core/lia_agents_core/long_term_memory.py
Mecanismo: Episódios + compressão LLM após 30 dias
Integração:
  EnhancedAgentMixin._post_loop_learning: salva learnings após cada ReAct loop
  _get_memory_context: enriquece system prompt com memórias históricas
Background processing via Celery tasks

Etapas ativas: E4, E8, E9A, E9B
```

---

## SEÇÃO TRANSVERSAL: LGPD / DATA PROTECTION

### Consent Flow

```
Arquivo: app/api/v1/lgpd.py + communication_optout.py

1. Consentimento para triagem WSI:
   WelcomeCard com checkbox explícito obrigatório
   Botões desabilitados até aceite LGPD
   ConsentEvent auditável registrado

2. Consentimento para contato:
   CandidateChannelSelector.select_channels verifica:
   → LGPDConsent (consentimento registrado por canal)
   → CandidateOptOut (opt-out por canal)
   WhatsApp: estado AWAITING_CONSENT com mensagem explícita
   Sem consentimento → canal bloqueado

3. Opt-out em emails:
   Link obrigatório em todo email
   HMAC-signed tokens (anti-tampering)
   ConsentEvent auditável: revogação registrada
```

### DSR — Data Subject Requests

```
Endpoints LGPD (api/v1/lgpd.py):
  GET /api/v1/lgpd/data-export/{candidate_id} — export completo
  DELETE /api/v1/lgpd/data-delete/{candidate_id} — anonymize/delete
  GET /api/v1/lgpd/consent/{candidate_id} — consultar consentimentos
  POST /api/v1/lgpd/consent — registrar consentimento
  Portal público: /portal/data-request/[token]

Status: Endpoints existem ○ (pendente integração completa)
```

### Data Minimization

```
Princípios aplicados:
  1. ICS Calendar: apenas dtstart/dtend/summary/location/attendee
     Sem dados sensíveis do candidato
  2. ATS Sync: ATSSyncService filtra dados sensíveis (salário)
     "Dado sensível - não sincronizar"
  3. Feedback: PipelineFeedbackTool._remove_score_references
     Strip scores numéricos do feedback ao candidato
  4. PII Masking: 4 camadas pré-LLM
     LLM nunca vê dados reais
  5. ToonService: anonymize=True para visualização anônima
```

### Retenção por Tipo de Dado

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  Tipo de Dado              │ Retenção        │ Base Legal                    │
│───────────────────────────┼─────────────────┼───────────────────────────────│
│  Audit Trail (SOX)         │ 730-1825 dias   │ SOX compliance, Art. 12 LGPD │
│  Scores WSI                │ Duração processo│ Legítimo interesse            │
│  Dados de candidato (PII)  │ Até revogação   │ Consentimento                 │
│  Logs de comunicação       │ 365 dias        │ Legítimo interesse            │
│  Embeddings de perfil      │ Indefinido      │ Anonimizados (sem PII)        │
│  Learning patterns         │ Indefinido      │ Agregados (sem PII individual)│
│  LLM prompts/responses     │ 90 dias         │ Auditoria + melhoria          │
│  Conversation memory       │ Sessão          │ Efêmero                       │
│  Long-term memory          │ Compressão 30d  │ Anonimizado                   │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## MAPA CONSOLIDADO DE AGENTES

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  MAPA DE AGENTES — ALPHA 1                                                    │
│                                                                               │
│  Ag.0 MainOrchestrator                                                        │
│    Classe: MainOrchestrator                                                   │
│    Domínio: orchestrator                                                      │
│    LLM: Gemini (CascadedRouter T5)                                           │
│    Tools: CascadedRouter (6-tier), ActionExecutor, PendingAction             │
│    Etapas: E5, E6, E7 (coordenação geral)                                   │
│    FG: L1+L2 (pré-roteamento) | Anti-Sycophancy: ORCHESTRATOR               │
│                                                                               │
│  Ag.2 SourcingReActAgent                                                      │
│    Classe: SourcingReActAgent (LangGraphReActBase + EnhancedAgentMixin)       │
│    Domínio: sourcing                                                          │
│    Registry: "sourcing"                                                       │
│    LLM: Gemini | max_iterations: 5 | max_tool_calls: 3                      │
│    Tools: 15 (search, analyze, compare, rank, outreach, generate_message)    │
│    Etapas: E4 (busca de candidatos)                                          │
│    FG: L1+L2+L3 | PII: ativo | Audit: ◐                                    │
│                                                                               │
│  Ag.3 TriagemCurricular (CV Screening)                                        │
│    Domínio: cv_screening                                                      │
│    LLM: Gemini                                                                │
│    Etapas: E4 (triagem curricular na busca)                                  │
│    FG: L1+L2+L3 | PII: ativo | Fact-Check: ativo | Audit: ◐                │
│                                                                               │
│  Ag.4 WSIInterviewGraph                                                       │
│    Classe: WSIInterviewGraph (LangGraph StateGraph)                          │
│    Domínio: cv_screening                                                      │
│    LLM: Gemini | 8 stages | Bloom+Dreyfus+BigFive                           │
│    HITL: interrupt_before=["lg_generate_feedback"]                           │
│    Checkpoint: PostgresSaver (sessões 30-120 min)                            │
│    Etapas: E7 (conduz entrevista WSI), E7B (feedback pós-triagem)            │
│    FG: L1+L2+L3 | PII: ativo | Fact-Check: ativo | Audit: ◐                │
│                                                                               │
│  Ag.5 WSIService (Scoring)                                                    │
│    Classe: WSIService + WSIDeterministicScorer                                │
│    Domínio: cv_screening                                                      │
│    LLM: SEM LLM (determinístico — zero latência, zero custo)                 │
│    Etapas: E4 (score WSI na busca), E7 (calcula score final)                 │
│    ScoreNormalization: difficulty_coefficient ativo                           │
│                                                                               │
│  Ag.6 InterviewGraph                                                          │
│    Classe: InterviewGraph (LangGraph StateGraph)                             │
│    Domínio: interview_scheduling                                              │
│    LLM: Gemini | 6 nós                                                       │
│    Tools: schedule_interview, check_availability, reschedule, cancel         │
│    Etapas: E9A (agendar entrevista)                                          │
│    CircuitBreaker: "google_calendar"                                         │
│                                                                               │
│  Ag.7 CommunicationReActAgent + PersonalizedFeedbackService                  │
│    Classes: CommunicationReActAgent (ReAct) + PersonalizedFeedbackService    │
│    Domínios: communication + cv_screening                                    │
│    LLM: Gemini | max_iterations: 5                                           │
│    Tools: send_email, send_whatsapp, get_history, schedule_message           │
│    Etapas: E5 (feedback rejeição Gate 1), E6 (contato email),               │
│            E8 (feedback Gate 2), E9B (feedback reprovado)                    │
│    FG: L1+L2 | LGPD: opt-out obrigatório                                    │
│                                                                               │
│  Ag.8 ATSIntegrationReActAgent ⚠ PÓS-MVP                                   │
│    Classe: ATSIntegrationReActAgent                                           │
│    Domínio: ats_integration                                                   │
│    LLM: Gemini                                                                │
│    Tools: sync_candidate_to_ats, fetch_candidate_from_ats, validate_fields   │
│    Etapas: E2 (sync ATS), E5 (sync status), E8 (sync status)                │
│    Status: Código existe, depende de credenciais de produção                 │
│                                                                               │
│  SERVIÇOS AUXILIARES (sem rótulo Ag.):                                        │
│                                                                               │
│  WSIQuestionGenerator / WSIScreeningQuestionGenerator                         │
│    Domínio: cv_screening | LLM: Gemini                                       │
│    Etapas: E3 (gera perguntas WSI)                                           │
│                                                                               │
│  WSIScreeningPipeline                                                         │
│    Domínio: cv_screening | LLM: Gemini                                       │
│    Etapas: E4 (triagem/screening na busca)                                   │
│                                                                               │
│  WSIVoiceOrchestrator                                                         │
│    Domínio: cv_screening | LLM: Gemini + Deepgram + OpenAI TTS              │
│    Etapas: E7 (triagem por voz)                                              │
│                                                                               │
│  JobDescriptionGeneratorService                                              │
│    Domínio: job_management | LLM: Claude (Anthropic)                         │
│    Etapas: E2 (gera JD), E3 (JD como base para WSI)                         │
│                                                                               │
│  PipelineTransitionAgent                                                      │
│    Classe: PipelineTransitionAgent (LangGraphReActBase + EnhancedAgentMixin) │
│    Domínio: pipeline | LLM: Gemini                                           │
│    Invocação: POST /api/v1/pipeline/interpret-context (direta)               │
│    Tools: 20 | Etapas: E5, E8 (transições de pipeline)                       │
│                                                                               │
│  WizardReActAgent                                                             │
│    Registry: "wizard" | Domínio: job_management | LLM: Gemini               │
│    6 stages: input-evaluation → jd-enrichment → salary → competencies →      │
│              wsi-questions → review-publish                                   │
│    Tools: 10 | Etapas: E2, E3 (criação/edição de vagas)                      │
│                                                                               │
│  KanbanReActAgent                                                             │
│    Registry: "kanban" | Domínio: recruiter_assistant | LLM: Gemini           │
│    Tools: 22 (maior número) | Etapas: E5, E8 (Kanban board)                 │
│                                                                               │
│  TalentReActAgent                                                             │
│    Registry: "talent" | Domínio: recruiter_assistant | LLM: Gemini           │
│    Tools: 13 | Stages: discovery → analysis → action_planning               │
│    Etapas: E4 (funil de talentos)                                            │
│                                                                               │
│  PolicyReActAgent                                                             │
│    Registry: "policy" | Domínio: hiring_policy | LLM: Gemini                │
│    Tools: 13 | Setup wizard por blocos                                       │
│    Etapas: Transversal (configuração de políticas)                           │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Grafo de Dependências

```
                    ┌──────────────┐
                    │    Ag.0      │
                    │ Orchestrator │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼────┐ ┌────▼─────┐ ┌────▼─────┐
        │  Ag.2    │ │  Ag.4   │ │  Ag.8   │
        │ Sourcing │ │Entrev.  │ │ ATS Int.│
        └─────┬────┘ │  WSI    │ └────┬────┘
              │      └────┬────┘      │
              │           │           │
        ┌─────▼────┐ ┌────▼─────┐    │
        │  Ag.3    │ │  Ag.5   │    │
        │ Triagem  │ │Avaliador│    │
        │Curricular│ │  WSI    │    │
        └──────────┘ └────┬────┘    │
                          │         │
                    ┌─────▼────┐    │
                    │  Ag.7    │◄───┘
                    │Analista  │
                    │Feedback  │
                    └─────┬────┘
                          │
                    ┌─────▼────┐
                    │  Ag.6    │
                    │Scheduling│
                    └──────────┘
```

---

## GAPS CONSOLIDADOS — AÇÕES PENDENTES

### Audit Trail (Prioridade: MVP)

| Etapa | O que falta | Arquivo |
|-------|------------|---------|
| E1 Login | Ativar audit de login | auth.py |
| E4 Busca | Ativar audit de buscas | candidates.py |
| E5 Gate 1 | Ativar audit de aprovações/rejeições | pipeline tools |
| E6 Contato | Ativar audit de envios | communication |
| E7 Triagem | Ativar audit por pergunta/resposta/score | rubric_evaluation.py |
| E8 Gate 2 | Ativar audit de aprovações Gate 2 | pipeline tools |
| E9A Scheduling | Ativar audit de agendamentos | scheduling |
| E9B Feedback | Ativar audit de feedback enviado | communication |

### Infraestrutura (Prioridade: PÓS MVP)

| Item | Status |
|------|--------|
| API keys produção (Twilio, Resend, ATS) | Pendente |
| Elasticsearch + PGVector produção | Pendente |
| Bell notification (in-app) | Pendente |
| Bias Audit Dashboard (Four-Fifths Rule) | Pendente |
| EU AI Act Risk Classification | Pendente |
| LGPD DSR completo (export/delete) | Parcial |
| SOX Audit Export | Pendente |
| Predictive Analytics UI | Pendente |

---

*Documento gerado a partir do código real do lia-agent-system (Replit) e documentação specs existente. Complementa o `ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md` com nível de detalhe técnico passo-a-passo por etapa.*
