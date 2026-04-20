# Fluxo Técnico Completo — Plataforma LIA Alpha 1

**Data:** abril/2026  
**Versão:** 2.0  
**Escopo:** Fluxo end-to-end Alpha 1 — desde Login até Scheduling/Feedback  
**Formato:** Diagrama passo-a-passo por macro-etapa (estilo "11 STEPS" do WSI)  
**Referência:** `ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md` v6.3 (complementar)  
**Auditado contra código em:** abril/2026

---

## COMO LER ESTE DOCUMENTO

Cada macro-etapa do Alpha 1 (E0–E9B) é apresentada como um diagrama técnico passo-a-passo. Cada step mostra:

1. **O request HTTP real** — endpoint, método, payload
2. **O roteamento** — MainOrchestrator, CascadedRouter (6 tiers), domínio destino
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

---

### Convenção de Agentes

Tabela completa dos agentes e sub-agentes registrados no código (abril/2026).

| Rótulo | Classe no código | Domínio | LLM Provider |
|--------|-----------------|---------|--------------|
| Ag.0 | MainOrchestrator | orchestrator | Gemini (produção) |
| Ag.0b | AutonomousReActAgent | orchestrator | Gemini (Tier 6 fallback) |
| Ag.1 | SourcingReActAgent | sourcing | Gemini |
| Ag.1a | SourcingPlannerAgent | sourcing | Gemini |
| Ag.1b | SourcingSearchAgent | sourcing | Gemini |
| Ag.1c | SourcingEnrichAgent | sourcing | Gemini |
| Ag.1d | SourcingEngagementAgent | sourcing | Gemini |
| Ag.1e | GithubSourcingAgent | sourcing | Gemini |
| Ag.1f | StackOverflowSourcingAgent | sourcing | Gemini |
| Ag.1g | DiversitySourcingAgent | sourcing | Gemini |
| Ag.1h | ReferralAgent | sourcing | Gemini |
| Ag.1i | PassivePipelineAgent | sourcing | Gemini |
| Ag.1j | NurtureSequenceAgent | sourcing | Gemini |
| Ag.2 | WSIInterviewGraph | cv_screening | Gemini |
| Ag.3 | WSIService (scoring determinístico) | cv_screening | Sem LLM |
| Ag.3a | VoiceScreeningOrchestrator | voice | PSTN: Gemini Flash 2.5 STT + OpenAI TTS; Web: OpenAI Whisper STT |
| Ag.3b | WSIQuestionGeneratorService | cv_screening / job_creation | Gemini |
| Ag.3c | WSIScreeningPipeline | cv_screening | Gemini |
| Ag.3d | RubricEvaluationService | interview_intelligence | Gemini |
| Ag.4 | PipelineTransitionAgent | pipeline | Gemini |
| Ag.4a | PipelineDecisionAgent | pipeline | Gemini |
| Ag.4b | PipelineContextAgent | pipeline | Gemini |
| Ag.4c | PipelineActionAgent | pipeline | Gemini |
| Ag.5 | KanbanReActAgent | recruiter_assistant | Gemini |
| Ag.5a | KanbanSearchAgent | recruiter_assistant | Gemini |
| Ag.5b | KanbanInsightAgent | recruiter_assistant | Gemini |
| Ag.5c | KanbanActionAgent | recruiter_assistant | Gemini |
| Ag.6 | WizardReActAgent + JobWizardGraph | job_management | Gemini |
| Ag.6a | WizardOrchestratorService | job_management | Gemini |
| Ag.7 | JobsManagementReActAgent | recruiter_assistant | Gemini |
| Ag.8 | TalentReActAgent | recruiter_assistant | Gemini |
| Ag.9 | PolicyReActAgent | hiring_policy | Gemini |
| Ag.10 | CommunicationReActAgent | communication | Gemini |
| Ag.10a | PersonalizedFeedbackService | cv_screening | Gemini |
| Ag.10b | FeedbackGeneratorService | interview_intelligence | Gemini |
| Ag.11 | ATSIntegrationReActAgent ● | ats_integration | Gemini |
| Ag.12 | AnalyticsAgent | analytics | Gemini |
| Ag.13 | AutomationReActAgent | automation | Gemini |
| Ag.14 | InterviewGraph | interview_scheduling | Gemini |
| Ag.14a | InterviewWSIService | interview_intelligence | Gemini |
| — | JobDescriptionGeneratorService | job_management | Claude (Anthropic) |
| — | SkillsOntologyEngine | talent_intelligence | Gemini |

---

## GLOSSÁRIO DE COMPONENTES

### Tipos de Componente

| Tipo | O que é | Exemplo |
|------|---------|---------|
| **Domínio** | Uma área funcional da plataforma. Cada domínio agrupa um conjunto coeso de funcionalidades de negócio. É como um "departamento" da IA. | `sourcing` (busca de candidatos), `cv_screening` (triagem), `communication` (emails/mensagens), `job_management` (vagas), `interview_scheduling` (agendamento) |
| **Agente (Ag.)** | Um "trabalhador IA" autônomo que executa tarefas complexas usando raciocínio passo-a-passo (loop ReAct). Cada agente pertence a um domínio e usa ferramentas (tools) para agir. | Ag.1 SourcingReActAgent (busca candidatos), Ag.2 WSIInterviewGraph (conduz entrevista de triagem) |
| **Serviço** | Um componente que executa uma função específica, geralmente sem raciocínio autônomo. Recebe um input, processa e devolve um resultado. | `JobDescriptionGeneratorService` (gera descrição de vaga), `WSIService` (calcula scores de triagem) |
| **Tool (Ferramenta)** | Uma ação atômica que um agente pode executar. É como uma "mão" do agente — ele decide quando e como usar cada tool. | `search_candidates` (buscar), `send_email` (enviar email), `schedule_interview` (agendar) |
| **Capability (Capacidade)** | Um módulo transversal que é injetado automaticamente em agentes e serviços para adicionar comportamentos de proteção ou inteligência. Não age sozinho — é uma camada que enriquece quem o usa. | FairnessGuard (anti-viés), PII Masking (proteção de dados), AuditTrail (registro auditável) |
| **Orquestrador** | O componente central que recebe todas as requisições e decide qual domínio/agente deve processá-las. É o "recepcionista" que direciona cada pedido ao especialista certo. | `MainOrchestrator` + `CascadedRouter` (6 camadas de roteamento) |
| **Graph (Grafo)** | Um fluxo de trabalho estruturado em etapas (nós) conectadas. Diferente do agente ReAct que raciocina livremente, o graph segue uma sequência definida de passos. | `WSIInterviewGraph` (8 estágios da entrevista WSI), `InterviewGraph` (6 nós do agendamento) |
| **Pipeline** | Uma sequência de processamento onde o output de uma etapa alimenta a próxima. Usado para processar dados em cadeia. | `WSIScreeningPipeline` (triagem curricular em cadeia) |
| **Registry** | O catálogo centralizado de agentes. Quando o orquestrador precisa de um especialista, consulta o registry para encontrá-lo pelo nome. | `"sourcing"` → SourcingReActAgent, `"wizard"` → WizardReActAgent |

### Glossário de Termos

| Termo | Definição |
|-------|-----------|
| **Chat LIA** | Camada conversacional transversal que permite ao recrutador interagir com todos os domínios da plataforma via chat (SSE/WebSocket). Roteado pelo MainOrchestrator com fallback Tier 6 via AutonomousReActAgent. |
| **AutomationEngine** | Motor de automação (domínio `automation`) que executa regras do tipo "quando candidato move para stage X → executar ação Y". Dispara triagens, envia alertas, executa transições sem intervenção manual. |
| **SkillsOntologyEngine** | Serviço do domínio `talent_intelligence` que expande queries de busca usando ontologia semântica de skills. Exemplo: "Python" → inclui "FastAPI", "Django", "asyncio" automaticamente. |
| **BARS / RubricEvaluation** | Behaviorally Anchored Rating Scales implementada via `RubricEvaluationService` (domínio `interview_intelligence`). Cada score WSI (0–10) ancorado em exemplos de comportamento observável. |
| **AI Consumption Outbox** | Serviço de tracking de consumo de tokens LLM por tenant (migration 095). Alimenta o billing e dashboards de uso de IA. |
| **DSR / Portal do Candidato** | Data Subject Requests — exercício de direitos LGPD pelo candidato. Portal público em `/portal/data-request/[token]` com verificação OTP. |
| **Papel DPO** | Data Protection Officer — papel com acesso ao `/api/v1/admin/lgpd` para gestão de DSRs, relatórios de compliance e ações de cleanup. Criado via migration 093. |
| **WSI 0–10** | Escala de score WSI normalizada de 0 a 10 (migration 090), substituindo a escala anterior. Cada dimensão (técnica, comportamental, situacional) pontuada de 0–10. |
| **navigation_intent** | Serviço do orquestrador que detecta quando o recrutador quer navegar para uma página específica e emite `ui_action: "navigate_to"`. |
| **Agent Studio** | ⚠ FORA DO ESCOPO ALPHA 1. Ferramenta para tenants customizarem system prompts de agentes. Código existe mas não exposto no Alpha 1. |
| **Digital Twin / TwinInferenceService** | ⚠ FORA DO ESCOPO ALPHA 1. Réplica digital de candidatos para simulações preditivas. |
| **Talent Pool** | ⚠ FORA DO ESCOPO ALPHA 1. Pool de candidatos passivos gerenciados no longo prazo. |
| **Recruitment Campaign** | ⚠ FORA DO ESCOPO ALPHA 1. Campanhas de marketing de recrutamento. |

### Componentes Transversais (aparecem em várias etapas)

| Componente | Tipo | O que faz | Em linguagem simples |
|------------|------|-----------|----------------------|
| **MainOrchestrator** | Orquestrador | Entry point único — pipeline: ConversationMemory → CascadedRouter (6 tiers) → DomainWorkflow → ReAct Agent. Arquivo: `app/orchestrator/main_orchestrator.py`. | Ponto de entrada único da LIA — processa toda mensagem via CascadedRouter e delega ao domínio correto |
| **CascadedRouter** | Serviço (dentro do Orquestrador) | 6 camadas de roteamento: memória → cache local → cache Redis → busca vetorial → regex → LLM | "GPS de requisições" — tenta o caminho mais rápido primeiro, escala para análise mais profunda se necessário |
| **FairnessGuard** | Capability (3 camadas) | L1: bloqueia viés explícito (350+ padrões). L2: alerta viés implícito. L3: análise semântica por LLM | "Guardião de equidade" — impede que a IA discrimine por gênero, idade, etnia ou qualquer categoria protegida |
| **PII Masking** | Capability (4 camadas) | Remove dados pessoais antes de enviar ao LLM: CPF, nome, endereço, campos sensíveis | "Protetor de privacidade" — a IA nunca vê dados pessoais reais do candidato |
| **AuditTrail** | Capability | Registra toda decisão de forma imutável (append-only), com retenção de 2-5 anos (SOX) | "Cartório digital" — tudo que a IA decide fica registrado e não pode ser alterado |
| **FactChecker** | Capability | Verifica claims do LLM: experiência, certificações, períodos, habilidades | "Verificador de fatos" — confere se o que a IA diz é coerente com os dados reais |
| **BiasAuditSnapshot** | Capability | Aplica Four-Fifths Rule: detecta se um grupo demográfico é aprovado <80% em relação a outro | "Auditor estatístico" — detecta discriminação numérica mesmo que ninguém a tenha intencionado |
| **ConfidenceNode** | Capability | Calibra scores para serem comparáveis entre candidatos e vagas diferentes | "Calibrador de notas" — garante que um 8 em uma vaga signifique o mesmo que um 8 em outra |
| **LearningLoop** | Capability | Observa silenciosamente quando o recrutador aceita, modifica ou rejeita sugestões da IA e aprende com isso | "Aprendiz silencioso" — a IA melhora sem pedir feedback explícito |
| **SkillsOntologyEngine** | Serviço | Expande queries de busca usando ontologia semântica de skills (domínio `talent_intelligence`) | "Tradutor de habilidades" — quando você busca "Python", ele entende que "FastAPI" e "asyncio" também são relevantes |
| **SemanticSearch** | Serviço | Expande termos de busca usando vetores semânticos (embeddings 768-dim via Gemini) | "Tradutor de intenções" — quando você busca "Java", ele entende que "Spring Boot" e "JVM" também são relevantes |
| **CircuitBreaker** | Capability | Protege contra falhas em cascata: se um serviço externo cai, para de chamá-lo temporariamente | "Disjuntor" — evita que a falha de um serviço derrube todo o sistema |
| **PolicyEngine** | Serviço | Define regras por setor: nível de autonomia da IA, quando escalar para humano, limites de uso | "Regulador setorial" — em saúde a IA é mais cautelosa, em RPO tem mais autonomia |
| **AntiSycophancy** | Capability | Impede que a IA concorde com tudo que o recrutador diz — força verificação de premissas | "Advogado do diabo" — a IA discorda quando os dados contradizem o que foi pedido |
| **WorkingMemory** | Capability | Memória de curto prazo do agente durante uma conversa/tarefa | "Bloco de notas" — o agente lembra o que já fez durante a tarefa atual |
| **LongTermMemory** | Capability | Memória de longo prazo com compressão automática após 30 dias | "Memória institucional" — a IA lembra padrões de vagas e candidatos passados |
| **ConversationMemory** | Capability | Tracking de entidades na sessão de chat (última vaga, último candidato, pronomes) | "Contexto de conversa" — quando você diz "ele", a IA sabe de quem está falando |
| **ModelDrift** | Capability | Monitora se os scores e decisões da IA estão mudando ao longo do tempo (janela de 7 dias) | "Detector de desvios" — alerta se a IA começa a aprovar muito mais (ou muito menos) que o normal |
| **AutomationEngine** | Serviço | Motor de regras de automação que dispara ações com base em eventos de pipeline | "Gatilho inteligente" — move candidatos, inicia triagens e envia alertas automaticamente |

---

## DOMÍNIOS DO ALPHA 1

### Domínios Ativos no Alpha 1

| Domínio | Descrição | Status |
|---------|-----------|--------|
| `recruiter_assistant` | Chat LIA + Kanban + Talent + Jobs Management | ● |
| `sourcing` | Busca de candidatos (local, Pearch, Apify, GitHub, StackOverflow, Diversidade) | ● |
| `cv_screening` | Triagem WSI (web, WhatsApp, voz), scoring, perguntas | ● |
| `interview_scheduling` | Agendamento de entrevistas com Google Calendar | ● |
| `job_management` | Criação/edição de vagas, Wizard, JD Generator | ● |
| `job_creation` | Geração de perguntas WSI, briefing de vaga | ● |
| `pipeline` | Transições de estágio, decisões, contexto de candidato | ● |
| `communication` | Emails (SendGrid/Resend), WhatsApp (Twilio), feedback | ● |
| `ats_integration` | Sincronização com ATS externos via Merge.dev | ● |
| `analytics` | KPIs, funil de conversão, predictive analytics | ● |
| `hiring_policy` | Políticas de contratação por setor, HITL thresholds | ● |
| `company_settings` | Configurações de empresa, cultura, benefícios | ● |
| `automation` | Motor de automação, triggers de pipeline | ● |
| `candidate_self_service` | Portal do candidato, status de aplicação, LGPD info | ● |
| `voice` | Triagem por voz: (A) Twilio PSTN → Gemini Flash 2.5 STT + OpenAI TTS; (B) browser audio → OpenAI Whisper STT | ● |
| `consent` | Gestão de consentimento granular por finalidade | ● |
| `lgpd` | Limpeza de dados, DSR, políticas de retenção | ● |
| `interview_intelligence` | BARS/Rubric evaluation, WSI service, feedback generator | ● |
| `talent_intelligence` | SkillsOntologyEngine, análise de mercado | ● |
| `agent_memory` | Memória de longo prazo de agentes, episódios comprimidos | ● |

### Domínios FORA do Escopo Alpha 1

| Domínio | Motivo de exclusão |
|---------|--------------------|
| `digital_twin` | Funcionalidade de réplica digital — fase posterior |
| `agent_studio` | Customização de agentes por tenant — fase posterior |
| `talent_pool` | Pool de candidatos passivos — fase posterior |
| `recruitment_campaign` | Campanhas de marketing de recrutamento — fase posterior |

---

## E0 — CHAT LIA (Assistente do Recrutador) — CAMADA TRANSVERSAL

### O que acontece nesta etapa (visão do processo)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PASSO A PASSO — E0 CHAT LIA (Assistente do Recrutador)                      │
│                                                                               │
│  • O recrutador acessa o chat da LIA em /chat (frontend Next.js)            │
│  • Pode fazer qualquer pergunta em linguagem natural — a LIA entende         │
│    e roteia para o especialista correto automaticamente                      │
│  • Exemplos de comandos via chat:                                             │
│    - "Crie uma vaga de Engenheiro Sênior para o setor financeiro"           │
│    - "Busque candidatos com 5 anos de Python e experiência em AWS"          │
│    - "Aprove todos os candidatos aprovados na triagem de ontem"              │
│    - "Qual é o status do candidato João Silva?"                              │
│    - "Inicie triagem em massa para a vaga 123"                               │
│  • O MainOrchestrator roteia para o domínio correto usando                  │
│    CascadedRouter (6 camadas de fallback)                                    │
│  • Se o intent for navegação → navigation_intent emite ui_action            │
│    → frontend navega automaticamente para a página correta                  │
│  • Fallback Tier 6: AutonomousReActAgent (raciocínio livre) quando          │
│    nenhum dos tiers anteriores consegue classificar o intent                 │
│  • Respostas via SSE (Server-Sent Events) ou WebSocket                      │
│                                                                               │
│  Resultado: Recrutador consegue acionar qualquer etapa (E1–E9B) via chat     │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Detalhamento técnico

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Chat LIA (recruiter_assistant / orchestrator) — CAMADA TRANSVERSAL    │
│  Conversa:  POST /api/v1/lia/conversational                                   │
│  SSE:       POST /api/v1/chat/{session_id}/stream                             │
│  SSE action: POST /api/v1/chat/action                                         │
│  WebSocket: WS   /api/v1/ws/chat/{session_id}                                 │
│  Frontend:  plataforma-lia/src/app/[locale]/chat/page.tsx                    │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    POST /api/v1/lia/conversational (sync) |
    POST /api/v1/chat/{session_id}/stream (SSE) |
    WS /api/v1/ws/chat/{session_id} (WebSocket)
    Body: { message, conversation_id, context_type, entity_id }
    Authorization: Bearer <jwt_token>
    Frontend: plataforma-lia/src/app/[locale]/chat/page.tsx

 2  SecurityPatterns pré-check
    check_input_security: bloqueia prompt injection, exploits
    Se bloqueado → retorna 403 sem processar

 3  FairnessGuard pré-check (L1 + L2)
    L1 Regex: bloqueia mensagens com viés explícito
    L2 Implícito: soft warning sem bloquear
    Warnings propagados na response final

 4  TenantContext enrichment
    TenantContextService.get_context(company_id, db)
    Carrega: setor, policies, LLM provider do tenant
    RecruiterPersonalizationService: estilo, verbosidade, foco

 5  ConversationMemory setup (LIA-M01)
    Persiste mensagem do usuário antes de qualquer fase
    Carrega histórico de conversas anteriores
    Entity tracking: última vaga, último candidato, pronomes

 6  MainOrchestrator — pipeline de fases
    Phase 0: PendingAction — ação aguardando confirmação?
    Phase 1: ActionExecutor — intent detectável por padrão?
    Phase 1.5: AgenticLoop (LLM function calling — LIA_AGENTIC_LOOP=true)
    Phase 2: CascadedRouter → DomainWorkflow → ReAct Agent

 7  CascadedRouter (6 tiers)
    Tier 1: ConversationMemory (memória da sessão)
    Tier 2: SemanticCache local (hash)
    Tier 3: VectorSemanticCache (pgvector — similarity ≥ 0.85)
    Tier 4: Regex patterns
    Tier 5: LLM (Gemini) — classifica intent
    Tier 6: AutonomousReActAgent (fallback — raciocínio livre)

 8  navigation_intent post-process
    detect_navigation_intent(message) → page + confidence
    Se confidence ≥ 0.75 → ui_action = "navigate_to"
    Frontend recebe {page, hint} e navega automaticamente

 9  ConversationMemory persist (LIA-M02)
    Resposta persistida independente de qual fase respondeu
    Histórico disponível para o próximo turno

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E0)                                          │
│  1. SecurityPatterns — prompt injection, exploits ●                          │
│  2. FairnessGuard L1+L2 — pré-roteamento ●                                  │
│  3. PII Masking — logs mascarados ●                                          │
│  4. ConversationMemory — contexto persistido ●                               │
│  5. TenantContext — isolamento por empresa ●                                 │
│  6. RecruiterPersonalization — estilo e preferências ●                       │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E1 — LOGIN — 4 STEPS

### O que acontece nesta etapa (visão do processo)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PASSO A PASSO — E1 LOGIN                                                     │
│                                                                               │
│  • O consultor/recrutador acessa a plataforma LIA pelo navegador             │
│  • Insere seu email e senha na tela de login                                 │
│  • A plataforma autentica as credenciais e gera um token de acesso           │
│  • O recrutador é redirecionado para o dashboard de vagas                    │
│  • Alternativa: login via SSO corporativo (WorkOS) se configurado            │
│  • Proteções ativas: limite de tentativas por IP, logs sem dados pessoais    │
│                                                                               │
│  Resultado: Recrutador autenticado, com acesso à plataforma                  │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Detalhamento técnico

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Login (auth) — 4 STEPS                                       │
│  AuthService [Serviço, domínio auth] — autentica o recrutador                │
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
│  4. Audit Trail — login events ● (ativado em auth.py — login success/failure)│
│  5. LGPD — JWT stateless, sem cookies de sessão ●                            │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E2 — EDITAR/CRIAR VAGA — 8 STEPS

### O que acontece nesta etapa (visão do processo)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PASSO A PASSO — E2 EDITAR/CRIAR VAGA                                        │
│                                                                               │
│  • O recrutador acessa a página de vagas WeDo no dashboard                   │
│  • Opção A — EDITAR VAGA (importada do ATS via Merge.dev):                  │
│    - Seleciona uma vaga já existente (importada do sistema ATS do cliente)   │
│    - NÃO cria a vaga na WeDo — apenas edita os dados que vieram do ATS      │
│    - Define/ajusta requisitos, benefícios, faixa salarial, modelo de         │
│      trabalho (presencial/remoto/híbrido)                                    │
│    - Ag.11 ATSIntegrationReActAgent sincroniza dados do ATS via Merge.dev ● │
│  • Opção B — CRIAR VAGA MANUALMENTE na WeDo:                                │
│    - Clica em "Criar Vaga" → seleciona "Criar Manualmente"                  │
│    - Preenche todos os campos da vaga manualmente                           │
│  • Opção C — CRIAR VAGA VIA WIZARD GUIADO (WizardReActAgent + JobWizardGraph):│
│    - Fluxo guiado em 6 estágios: input → enrichment → salary → competencies │
│      → wsi-questions → review-publish                                        │
│    - POST /api/v1/lia_assistant/wizard                                       │
│  • GERAR JD (Descrição de Vaga) com IA:                                     │
│    - POST /api/v1/briefing/generate-jd                                       │
│    - JobDescriptionGeneratorService [Serviço, job_management] usa Claude     │
│    - SkillsOntologyEngine expande skills automaticamente (talent_intelligence)│
│    - FairnessGuard valida o JD contra 13 categorias protegidas              │
│  • Tudo é registrado no AuditTrail                                           │
│                                                                               │
│  Resultado: Vaga criada/editada com JD de qualidade, sem viés,               │
│  pronta para configurar o roteiro de triagem (E3)                            │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Detalhamento técnico

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
    Wizard guiado: POST /api/v1/lia_assistant/wizard (WizardReActAgent)
    Gerar JD: POST /api/v1/briefing/generate-jd (JobDescriptionGeneratorService)

 2  MainOrchestrator (CascadedRouter) roteia + GuardrailCheck
    Identifica domínio = job_management
    GuardrailRepository (3 níveis): global → tenant → domain
    HiringPolicy carregado por company_id
    PromptInjectionGuard ativado

 3  EnhancedAgentMixin._setup_enhanced()
    Capabilities injetadas automaticamente:
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

 6  JobDescriptionGeneratorService + SkillsOntologyEngine (Claude LLM)
    LLM recebe dados mascarados da vaga
    Gera JD estruturada em markdown:
    → Seções: Sobre, Responsabilidades, Requisitos, Benefícios, Diversidade
    → SEO title + tags
    Anti-sycophancy block (FULL variant) no system prompt
    CircuitBreaker: circuit "anthropic" (failure_threshold=5, recovery=30s)
    SkillsOntologyEngine (talent_intelligence) expande skills sugeridas
    via /api/v1/skills_catalog + ontologia semântica vetorial

 7  AuditTrail registra decisão
    🔒 audit_service.log_decision ativo em jd_generation.py
    Registro: LLM input mascarado, output gerado, FairnessGuard results
    Append-only, retenção 730-1825 dias (SOX)

 8  Resposta ao recrutador (PII demasked)
    JD gerada com dados enriquecidos
    FairnessGuard warnings incluídos (se houver L2 alerts)
    Frontend renderiza JD no modal de edição em configurações de triagem
    ATS Integration: Ag.11 ATSIntegrationReActAgent sincroniza via Merge.dev
    (suporta Greenhouse, Lever, e outros ATS via API unificada Merge.dev)
    Dados persistidos via save_job_draft

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E2)                                          │
│  1. FairnessGuard L1/L2 — input+output check no JD ●                        │
│  2. PII Masking — 4 camadas pré-LLM ●                                       │
│  3. AntiSycophancy FULL — verificação de premissas ●                         │
│  4. CircuitBreaker — circuit "anthropic" ●                                   │
│  5. AuditTrail — log de geração de JD ● (edições manuais ●)                │
│  6. LearningLoop — captura silenciosa de edições ●                           │
│  7. TemplateLearning — auto-template após 3 vagas similares ●                │
│  8. PredictiveAnalytics — predict TTF + salary ●                             │
│  9. SemanticSearch + SkillsOntologyEngine — expansão de skills ●             │
│ 10. ATSIntegration — sync via Merge.dev ●                                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E3 — CONFIGURAR ROTEIRO WSI — 9 STEPS

### O que acontece nesta etapa (visão do processo)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PASSO A PASSO — E3 CONFIGURAR ROTEIRO WSI                                   │
│                                                                               │
│  • A partir da vaga criada/editada na etapa anterior (E2), o recrutador      │
│    precisa configurar as perguntas que serão usadas na triagem dos            │
│    candidatos (WSI = Work Sample Interview)                                   │
│  • O recrutador acessa a TAB CONFIGURAÇÕES da vaga                           │
│    → SEÇÃO PERGUNTAS de Triagem                                              │
│  • Revisa/ajusta o JD (já enriquecido na E2)                                │
│  • Clica em "Criar Roteiro" (modo compacto 7 ou completo 12 perguntas)      │
│  • 🤖 WSIQuestionGeneratorService [Serviço, cv_screening / job_creation]     │
│    gera perguntas WSI automaticamente usando o JD como base:                 │
│    - Bloco Técnico (Bloom 1–6 + Dreyfus 1–5) — nível de profundidade        │
│    - Bloco Comportamental (Big Five OCEAN) — traços de personalidade         │
│    - Bloco Situacional — cenários práticos do dia-a-dia                     │
│  • Escala WSI: 0–10 por dimensão (migration 090)                             │
│  • RubricEvaluationService (interview_intelligence) aplica BARS:             │
│    cada score ancorado em comportamentos observáveis                         │
│  • FairnessGuard valida cada pergunta individualmente                        │
│  • FactChecker valida coerência das perguntas com o JD                       │
│                                                                               │
│  IMPORTANTE: A triagem pode ser ativada na vaga. Candidatos que se           │
│  inscrevem automaticamente recebem convite para triagem. Candidatos          │
│  adicionados pelo recrutador (busca no funil) ou importados do ATS são       │
│  convidados manualmente.                                                     │
│                                                                               │
│  Resultado: Roteiro WSI pronto com perguntas validadas, escala 0–10,         │
│  BARS anchors, sem viés, para ser aplicado aos candidatos (E7)               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Detalhamento técnico

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Configuração de Roteiro WSI (cv_screening) — 9 STEPS         │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Consultor acessa TAB CONFIGURAÇÕES → SEÇÃO PERGUNTAS Triagem
    POST /api/v1/wsi/generate-questions
    Body: { job_id, vacancy_id, mode: "compact"|"full", company_id }
    Authorization: Bearer <jwt_token>

 2  MainOrchestrator (CascadedRouter) roteia + GuardrailCheck
    Identifica domínio = cv_screening / job_creation
    GuardrailRepository (3 níveis) carregado
    HiringPolicy: setor do cliente → regras de perguntas

 3  EnhancedAgentMixin._setup_enhanced()
    Capabilities injetadas:
    FairnessGuard (3 layers) | PII Masking (4 layers)
    AuditTrail | FactChecker | ConfidenceNode
    AntiSycophancy | WorkingMemory | CircuitBreaker

 4  FairnessGuard filtra perguntas
    🔒 L1: Bloqueia perguntas discriminatórias (estado civil, filhos,
       religião, saúde, etc.)
    🔒 L2: Alerta perguntas proxy implicitamente enviesadas
    check_fairness aplicado a cada pergunta gerada

 5  PII Masking remove dados do JD
    JD enviado ao LLM mascarado
    Dados pessoais da vaga não expostos ao modelo

 6  WSIQuestionGeneratorService processa (Gemini LLM)
    Analisa JD + requirements da vaga
    Gera 7 perguntas (compacto) ou 12 (completo):
    → Bloco Técnico: Bloom 1–6 + Dreyfus 1–5
    → Bloco Comportamental: Big Five OCEAN
    → Bloco Situacional: cenários práticos
    Escala WSI 0–10 por dimensão (migration 090)
    RubricEvaluationService (interview_intelligence):
    → Cada pergunta recebe BARS anchors (exemplos de resposta 0/5/10)
    → Metodologia: BARS (Behaviorally Anchored Rating Scales)

 7  FactChecker valida coerência
    🔒 Verifica se perguntas são coerentes com o JD
    🔒 Verifica se requisitos mencionados existem no JD
    Inconsistências → flag de revisão ao recrutador

 8  AuditTrail registra decisão
    🔒 audit_service.log_decision ativo em wsi_questions.py
    Registro: perguntas geradas, FairnessGuard results, FactChecker flags
    Append-only, retenção SOX

 9  Resposta ao recrutador
    Lista de perguntas com: texto, bloco, bloom_level, dreyfus_level,
    big_five_trait, BARS anchors, max_score=10.0
    Recrutador pode editar, remover ou adicionar manualmente
    Salvo em job_screening_questions (fonte da verdade para E7)

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E3)                                          │
│  1. FairnessGuard L1/L2 — por pergunta individual ●                          │
│  2. PII Masking — JD mascarado antes do LLM ●                                │
│  3. FactChecker — coerência perguntas × JD ●                                 │
│  4. AuditTrail — geração de perguntas WSI ● (ativado em wsi_questions.py)   │
│  5. RubricEvaluationService — BARS anchors + escala 0–10 ●                  │
│  6. CircuitBreaker — circuit "gemini" ●                                       │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E4 — BUSCAR CANDIDATOS (Funil) — 10 STEPS

### O que acontece nesta etapa (visão do processo)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PASSO A PASSO — E4 BUSCAR CANDIDATOS (Funil de Talentos)                    │
│                                                                               │
│  • O recrutador acessa o Funil de Talentos e busca candidatos                │
│  • Canais de sourcing disponíveis:                                           │
│    - Local (banco interno LIA)                                               │
│    - Pearch AI (enriquecimento com email e telefone)                         │
│    - Apify (web scraping e enriquecimento externo)                           │
│    - GitHub (perfis de desenvolvedores)                                      │
│    - StackOverflow (perfis técnicos)                                         │
│    - Diversidade (busca com foco em DEI)                                     │
│  • Modos de busca disponíveis:                                               │
│    - IA Natural (linguagem livre)                                            │
│    - Boolean (operadores AND/OR/NOT)                                         │
│    - Perfil Similar (a partir de candidato referência)                       │
│    - Job Description (busca por JD colada/importada)                        │
│    - Archetypes (perfis pré-configurados por área)                          │
│  • SkillsOntologyEngine expande automaticamente a query de busca            │
│    (ex: "Python" → inclui FastAPI, asyncio, Django na busca)                │
│  • Sub-agentes de sourcing coordenados:                                     │
│    Planner → Search → Enrich → Engagement                                   │
│  • Tabela de candidatos: 10 por vez, botão "Carregar +10"                   │
│                                                                               │
│  Resultado: Lista de candidatos ranqueados, com preview inline               │
│  e análise da LIA disponível                                                 │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Detalhamento técnico

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Busca de Candidatos (sourcing) — 10 STEPS                    │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Consultor digita query no campo de busca do Funil
    POST /api/v1/sourcing/search (busca principal)
    POST /api/v1/rag-search (busca semântica RAG)
    Body: { query, job_id, filters, mode, channels, page }
    Authorization: Bearer <jwt_token>
    Channels: local | pearch | apify | github | stackoverflow | diversity

 2  MainOrchestrator (CascadedRouter) roteia
    Domínio = sourcing
    GuardrailRepository (3 níveis) carregado
    PolicyEngine: setor → autonomia + FG L3 configurado

 3  EnhancedAgentMixin._setup_enhanced()
    Capabilities injetadas:
    FairnessGuard (3 layers) | PII Masking (4 layers)
    AuditTrail | BiasAuditSnapshot | ConfidenceNode
    AntiSycophancy OPERATIONAL | WorkingMemory | CircuitBreaker
    LearningLoop | TemplateLearning | PredictiveAnalytics
    SemanticSearch | ConversationMemory | ModelDrift
    RoutingAdaptativo | Calibration | ScoreNormalization

 4  FairnessGuard filtra ANTES do LLM
    🔒 L1+L2: query de busca analisada contra viés explícito e implícito
    🔒 L3 (setor-aware): análise semântica em setores tech/financeiro/saude/rpo
    check_with_sector() ativo na RAGPipelineService.search(**kwargs)

 5  SkillsOntologyEngine + SemanticSearch
    🧠 SkillsOntologyEngine (talent_intelligence):
       Expande query com ontologia de skills
       "Python" → ["FastAPI", "asyncio", "Django", "Flask", ...]
    🧠 SemanticSearch: embeddings 768-dim (Gemini text-embedding-004)
       EmbeddingCacheService (Redis) evita re-embedding
    🧠 LLM Job Classification (gemini): classifica candidato × vaga
       (com cache TTL 1h, max 500 entries)

 6  RAG Pipeline executa busca multi-fonte
    Elasticsearch + PGVector + WRF (Weighted Rank Fusion)
    ES Score Drop Analyzer + PGV Gap Analyzer (pré-WRF)
    WRF Dynamic K: ajuste por nível de qualificação
    Channels ativos:
      Local DB → Pearch AI → Apify (enriquecimento)
      GithubSourcingAgent → StackOverflowSourcingAgent
      DiversitySourcingAgent (DEI-aware)

 7  SourcingReActAgent coordena sub-agentes
    Ag.1a SourcingPlannerAgent: estratégia de busca
    Ag.1b SourcingSearchAgent: execução (ES + PgVector)
    Ag.1c SourcingEnrichAgent: enriquecimento via Apify
    Ag.1d SourcingEngagementAgent: outreach e engajamento
    Ag.1e GithubSourcingAgent: perfis GitHub
    Ag.1f StackOverflowSourcingAgent: perfis StackOverflow
    Ag.1g DiversitySourcingAgent: candidatos DEI
    Ag.1h ReferralAgent: indicações internas
    Ag.1i PassivePipelineAgent: candidatos passivos
    Ag.1j NurtureSequenceAgent: nurturing de longo prazo
    max_iterations=5 | max_tool_calls=3

 8  FactChecker + ConfidenceNode + BiasAuditSnapshot
    🔒 FactChecker: valida claims nas análises LIA
    🔒 ConfidenceNode: score calibrado para comparabilidade real
    🔒 BiasAuditSnapshot: Four-Fifths Rule
    🧠 ScoreNormalization: ajusta por difficulty_coefficient
    🧠 Calibration: feedback explícito/implícito sobre scores

 9  AuditTrail + Learning
    🔒 Audit: log de buscas + scores ● (ativado em sourcing_react_agent.py)
    🧠 LearningLoop: captura accept/modify/reject de candidatos
    🧠 ModelDrift: monitora score_drift + approval_drift (7-day window)
    🧠 PredictiveAnalytics: predict_skill_success integrado

 10 Resposta ao recrutador (PII demasked)
    Tabela de candidatos: 10 por vez + "Carregar +10"
    Preview inline com 4 tabs: Perfil | Atividades | Arquivos | Pareceres
    Like/Dislike feedback por candidato (otimiza busca)
    Prompt expandido da LIA (análise, comparação, ranking)
    Dados PII restaurados na response final
    Email OBRIGATÓRIO | Telefone opcional

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E4)                                          │
│  1. FairnessGuard L1/L2/L3 — busca + análise + response ●                   │
│  2. PII Masking — 4 camadas + ToonService anonymize ●                        │
│  3. FactChecker — valida claims pós-LLM ●                                    │
│  4. BiasAuditSnapshot — Four-Fifths Rule ●                                   │
│  5. ConfidenceNode — calibração de score ●                                   │
│  6. ScoreNormalization — difficulty_coefficient ●                             │
│  7. AuditTrail — buscas + scores ● (ativado)                                │
│  8. LearningLoop — captura silenciosa ●                                      │
│  9. Calibration — feedback dual (explícito + implícito) ●                    │
│ 10. ModelDrift — 4 dimensões monitoradas ●                                   │
│ 11. SkillsOntologyEngine + SemanticSearch — expansão multi-dimensional ●     │
│ 12. RoutingAdaptativo — confidence multipliers ●                             │
│ 13. PredictiveAnalytics — predict_skill_success ●                            │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E5 — APROVAR MAPEADOS (Gate 1) — 9 STEPS

### O que acontece nesta etapa (visão do processo)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PASSO A PASSO — E5 APROVAR MAPEADOS (Gate 1)                                │
│                                                                               │
│  • O recrutador visualiza os candidatos mapeados no Kanban board             │
│  • Para cada candidato, decide: APROVAR ou REPROVAR                          │
│    - Aprovação individual: arrasta o card do candidato para a                │
│      próxima coluna                                                          │
│    - Aprovação em massa: seleciona vários candidatos e aprova               │
│      todos de uma vez (máx. 100)                                             │
│    - Drag-and-drop: pode mover manualmente para qualquer coluna             │
│  • Se REPROVAR: precisa informar o motivo da rejeição                       │
│    - FairnessGuard analisa o motivo contra 13 categorias protegidas         │
│    - Se o motivo for discriminatório → BLOQUEADO automaticamente             │
│  • Ag.4 PipelineTransitionAgent coordena as transições via sub-agentes:     │
│    Decision → Context → Action → Transition                                  │
│  • Automation Engine: regras podem mover candidatos automaticamente          │
│    (ex: "se score WSI ≥ 8 → mover para APROVADO sem intervenção humana")   │
│  • PolicyEngine define se a IA pode aprovar sozinha ou precisa HITL          │
│  • Antes de contatar candidato, verifica consentimento LGPD                 │
│  • Aprovados seguem para contato via email ou WhatsApp (E6)                 │
│  • Reprovados recebem feedback personalizado (E9B)                           │
│  • ⚡ Candidatos que se inscreveram pelo site PULAM esta etapa               │
│    e vão direto para triagem automática                                      │
│                                                                               │
│  Resultado: Candidatos aprovados prontos para contato,                       │
│  reprovados com feedback respeitoso                                           │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Detalhamento técnico

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

 2  MainOrchestrator (CascadedRouter) + PolicyEngine
    Domínio = pipeline + kanban
    🔒 PolicyEngine: ALPHA1_SECTOR_RULES por setor
       Autonomy levels + HITL thresholds
       Determina se ação precisa confirmação humana
    SmartTransitionModal: etapas críticas pedem confirmação
    GuardrailRepository (3 níveis) carregado
    Automation Engine verifica regras automáticas:
    → POST /api/v1/automation/check (verifica triggers ativos)
    → Se regra de auto-aprovação existe → executa sem HITL

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

 5  Pipeline sub-agentes coordenam transição
    Ag.4 PipelineTransitionAgent (orquestrador)
    Ag.4a PipelineDecisionAgent: decide aprovação/rejeição
    Ag.4b PipelineContextAgent: agrega contexto do candidato
    Ag.4c PipelineActionAgent: executa a ação efetiva
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
    🔒 Audit: log de aprovações/rejeições + overrides ● (ativado em pipeline.py + approvals.py)
    🧠 LearningLoop: captura decisões aceitar/rejeitar/modificar suggestion
    🧠 Calibration: implicit feedback (avançar low-score = sinal)
    🧠 ModelDrift: trigger se approval_drift > 10 p.p.
    🧠 RoutingAdaptativo: correções de rota alimentam ajustes

 9  Resposta + Disparo de próxima etapa
    Aprovados → LIA dispara contato (E6)
    Reprovados → LIA envia feedback (E9B)
    ⚡ Inscritos via web BYPASS Gate 1 → triagem automática
    Kanban board atualizado em real-time (WebSocket)
    ATSIntegrationReActAgent: sync status para ATS via Merge.dev ●

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E5)                                          │
│  1. FairnessGuard — auto-check em rejeições + FG L3 pré-check ●              │
│  2. PolicyEngine — HITL thresholds por setor ●                               │
│  3. LGPD — consent check antes de contato ●                                  │
│  4. PII Masking — ativo globalmente ●                                        │
│  5. Escalation — trigger quando AI confidence < threshold ●                  │
│  6. AuditTrail — aprovações/rejeições ● (ativado)                           │
│  7. LearningLoop — captura decisões ●                                        │
│  8. Calibration — implicit feedback ●                                        │
│  9. ModelDrift — approval_drift monitoring ●                                 │
│ 10. AutomationEngine — regras de auto-transição ●                            │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E6 — CONTATO VIA EMAIL + FOLLOW-UP — 8 STEPS

### O que acontece nesta etapa (visão do processo)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PASSO A PASSO — E6 CONTATO VIA EMAIL + FOLLOW-UP                           │
│                                                                               │
│  • Após aprovação no Gate 1 (E5), a LIA envia automaticamente               │
│    um email para o candidato aprovado                                        │
│  • O email contém:                                                            │
│    - Apresentação da vaga e da empresa                                      │
│    - Link para a triagem via CHAT WEB (canal principal)                     │
│    - Opção de informar número de celular para triagem via WhatsApp          │
│    - Link obrigatório de opt-out (LGPD) para cancelar comunicações          │
│  • Ag.10 CommunicationReActAgent personaliza e envia o email                 │
│  • A/B Testing: variantes de template testadas automaticamente               │
│    (feature ativa — 3 experimentos criados no startup)                       │
│  • Cadência de follow-up:                                                    │
│    - Re-envio automático a cada 2 dias se não houver abertura/clique        │
│    - Após 7 dias sem resposta → status "sem_resposta"                       │
│    - O recrutador é notificado (Teams)                                       │
│  • Se o candidato clicou no opt-out → canal de email bloqueado              │
│    para futuras comunicações                                                 │
│                                                                               │
│  Resultado: Candidato contatado por email com link para triagem,             │
│  com follow-up automático de 7 dias (cadência a cada 2 dias)                │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Detalhamento técnico

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

 2  MainOrchestrator (CascadedRouter) roteia
    Domínio = communication
    GuardrailRepository carregado
    Rate limiting verificado: RateLimitRule sliding window por empresa/dia
    CircuitBreaker: circuits "sendgrid" + "resend" (critical tier)

 3  CommunicationReActAgent (Ag.10) processa
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
       seed_email_ab_tests cria 3 experimentos no startup ●
    🧠 TemplateLearning: templates de email aprendidos ●
       (lê de message_queue UNION communication_logs)

 7  Follow-up automático (7 dias, cadência a cada 2 dias)
    Se candidato NÃO abre/clica email:
    → Re-envio automático a cada 2 dias
    → Após 7 dias sem resposta (≈ 3–4 tentativas) → status "sem_resposta"
    → Consultor notificado (Teams)
    Celery Beat schedule para verificação periódica

 8  AuditTrail + Response
    🔒 Audit: log de envios + opens + clicks ● (ativado em communication.py)
    🧠 ConversationMemory: tracking de candidatos contatados
    Resposta ao consultor: confirmação de envio + tracking status

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E6)                                          │
│  1. LGPD — opt-out link obrigatório + HMAC-signed tokens ●                  │
│  2. PII Masking — logs mascarados ●                                          │
│  3. RateLimiting — sliding window por empresa/dia ●                          │
│  4. CircuitBreaker — circuits "sendgrid" + "resend" ●                        │
│  5. A/B Testing — variantes de template ● (3 experimentos ativos)            │
│  6. TemplateLearning — templates aprendidos ●                                │
│  7. AuditTrail — envios/opens/clicks ● (ativado)                            │
│  8. Follow-up automático — 7 dias, cadência 2 dias, Celery Beat ●           │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E7 — TRIAGEM WSI — 11 STEPS

### O que acontece nesta etapa (visão do processo)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PASSO A PASSO — E7 TRIAGEM WSI                                              │
│                                                                               │
│  • O candidato recebeu o email (E6) e clica no link de triagem               │
│  • Existem 3 trilhas de triagem:                                             │
│    TRILHA 1 — Chat Web (canal principal):                                    │
│      Candidato acessa /triagem/[token] no navegador                         │
│      Aceita o termo LGPD (checkbox obrigatório)                             │
│      Responde perguntas WSI via interface de chat                           │
│      Pode pausar e retomar a qualquer momento                               │
│    TRILHA 2 — WhatsApp (canal secundário):                                   │
│      Candidato informou número de celular                                    │
│      LIA inicia conversa via WhatsApp (Twilio)                              │
│      POST /api/v1/triagem/{token}/whatsapp-initiate                         │
│    TRILHA 3 — Voz/Telefone (canal terciário — ver E7-VOZ):                  │
│      Candidato solicita ligação ou recrutador inicia chamada                 │
│      Stack: Twilio Voice + Gemini Flash 2.5 STT + OpenAI TTS                │
│      POST /api/v1/triagem/{token}/request-call                              │
│  • Ag.2 WSIInterviewGraph conduz a entrevista (8 estágios)                  │
│  • Escala WSI 0–10 por dimensão (migration 090)                              │
│  • RubricEvaluationService aplica BARS para scoring                          │
│  • Ag.3 WSIService calcula score final de forma determinística               │
│    (zero custo LLM, zero latência)                                           │
│  • FactChecker valida claims das respostas                                   │
│  • BiasAuditSnapshot aplica Four-Fifths Rule                                 │
│  • Score final: "aprovado" | "aguardando" | "reprovado"                     │
│                                                                               │
│  Resultado: Candidato triado com score WSI 0–10, parecer da IA e            │
│  recomendação, aguardando decisão do recrutador (Gate 2 — E8)                │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Detalhamento técnico

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Triagem (cv_screening + WSI) — 11 STEPS                      │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Frontend (Next.js 15) envia POST /api/chat ou acessa /triagem/[token]
    Request logado via middleware (X-Request-ID auto-gerado)
    Canais: Chat web | WhatsApp (Twilio) | Voz PSTN (Twilio + Gemini Flash 2.5 STT) | Voz web (Whisper STT)
    Candidato clica link do email → página /triagem/[token]

 2  MainOrchestrator (CascadedRouter) roteia + GuardrailCheck
    Identifica domínio = cv_screening
    GuardrailRepository (3 níveis): global → tenant → domain
    HiringPolicy (per-tenant) carregado
    PromptInjectionGuard ativado

 3  EnhancedAgentMixin._setup_enhanced()
    Capabilities injetadas automaticamente:
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

 6  WSI Interview Graph processa
    8 stages: INIT → LOAD_CONTEXT → GENERATE_QUESTION → AWAIT_RESPONSE →
    VALIDATE_RESPONSE → SCORE_RESPONSE → ADVANCE → COMPLETE
    Bloom (1–6) + Dreyfus (1–5) + Big Five (OCEAN)
    Escala WSI 0–10 (migration 090)
    PostgresSaver checkpoint — sessões de 30–120 min via WebSocket
    interview_level: "quick" | "standard" | "full"
    HITL: interrupt_before=["generate_feedback"]
    FONTE DE PERGUNTAS: job_screening_questions (DB) → fallback pipeline
    Verificação de consentimento LGPD (SEG-4) antes de iniciar

 7  Gemini/Claude processa (dados mascarados)
    LLM recebe [CPF_MASKED], [NAME_1], etc.
    Anti-sycophancy block no system prompt
    CircuitBreaker protege contra falha
    Temperature: 0.3 (LLM_AGENT_TEMPERATURE)
    RubricEvaluationService (interview_intelligence):
    → BARS anchors aplicados por pergunta
    → Score 0–10 ancorado em comportamentos observáveis

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
    Retenção: 730-1825 dias (SOX). Não pode ser alterado
    🧠 LearningLoop: captura padrões de resposta por competência
    🧠 ModelDrift: monitora drift em scores WSI (7-day window)
    audit_service.log_decision ativo (EU AI Act compliance)

 11 Resposta ao recrutador (PII demasked)
    WSIFinalReport com recomendação + scores por dimensão:
    technical_score | behavioral_score | situational_score | wsi_final_score
    Escala 0–10 | Dados PII restaurados na resposta (nunca no audit)
    Recomendação: "aprovado" | "aguardando" | "reprovado"

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E7)                                          │
│  1. FairnessGuard L1/L2/L3 — por resposta + scoring ●                        │
│  2. PII Masking — 4 camadas pré-LLM ●                                        │
│  3. FactChecker — 4 tipos de verificação ●                                   │
│  4. BiasAuditSnapshot — Four-Fifths Rule ●                                   │
│  5. ConfidenceNode — calibração de score ●                                   │
│  6. ScoreNormalization — difficulty_coefficient ●                             │
│  7. AuditTrail — SOX-compliant, EU AI Act ●                                  │
│  8. LearningLoop — captura padrões por competência ●                         │
│  9. ModelDrift — drift em scores WSI ●                                       │
│ 10. RubricEvaluationService — BARS + escala 0–10 ●                           │
│ 11. LGPD Consent Check — SEG-4 antes de iniciar entrevista ●                 │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E7-VOZ — TRIAGEM POR LIGAÇÃO TELEFÔNICA

### O que acontece nesta sub-etapa

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PASSO A PASSO — E7-VOZ TRIAGEM POR LIGAÇÃO TELEFÔNICA                       │
│                                                                               │
│  • O candidato solicita triagem por telefone (ou recrutador inicia)         │
│  • Stack técnica — DOIS pipelines de áudio:                                  │
│    PIPELINE A — Twilio PSTN (E7-VOZ — ligação telefônica):                  │
│    - Twilio Voice: telecomunicação (μ-law 8kHz)                            │
│    - Gemini Flash 2.5: STT — mulaw_to_wav() → Gemini API → transcrição     │
│    - OpenAI TTS: voz da LIA → mp3_to_mulaw() → Twilio                      │
│    PIPELINE B — Áudio web (browser):                                         │
│    - POST /api/v1/triagem/{token}/audio → VoiceService.transcribe_audio()  │
│    - OpenAI Whisper (whisper-1): STT para áudio enviado via browser         │
│    - OpenAI TTS: TTS para perguntas da LIA (mesmo provider)                 │
│  • VoiceScreeningOrchestrator coordena todo o fluxo:                         │
│    - Carrega perguntas WSI do banco de dados (job_screening_questions)      │
│    - Verifica consentimento LGPD antes de iniciar                           │
│    - Aplica perguntas sequencialmente por voz                               │
│    - Transcreve respostas via Gemini Flash 2.5 STT                          │
│    - Score determinístico (não usa LLM para scoring — zero custo)           │
│    - Fallback determinístico se LLM falhar                                  │
│  • RESTRIÇÕES:                                                               │
│    - Não é permitido pausar/retomar em chamada ao vivo                      │
│    - Progresso salvo automaticamente ao final da sessão                     │
│  • Audit trail completo (EU AI Act) — transcrição mascarada de PII          │
│                                                                               │
│  Resultado: Candidato triado por voz com score WSI igual ao chat web         │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Detalhamento técnico

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Triagem por Voz (voice) — VoiceScreeningOrchestrator                  │
│  Arquivo: app/domains/voice/services/voice_screening_orchestrator.py          │
└──────────────────────────────────────────────────────────────────────────────┘

ENDPOINTS DE CONTROLE:
  POST /api/v1/triagem/{token}/request-call      → Candidato solicita ligação
  POST /api/v1/triagem/{token}/whatsapp-initiate → Candidato inicia via WhatsApp

WEBHOOK TWILIO:
  POST /api/v1/twilio-voice/status               → Twilio notifica status da chamada
                                                   (CallStatus: completed/failed/busy/etc.)

FLUXO INTERNO:
 1  verify_consent(candidate_id, company_id)
    ConsentCheckerService verifica consentimento para ai_screening
    Se revogado → não inicia chamada

 2  initiate_call(session, db)
    Twilio Voice API cria chamada
    VoiceScreeningOrchestrator.initiate_call() → session criada no DB

 3  Pergunta → Resposta → Score (determinístico)
    LIA faz pergunta via OpenAI TTS
    Candidato responde por voz
    Gemini Flash 2.5 STT transcreve resposta (μ-law → WAV → Gemini API)
    FairnessGuard._check_fairness_on_response() valida resposta
    Score calculado de forma DETERMINÍSTICA (sem LLM — zero latência)
    Fallback determinístico se qualquer serviço LLM falhar

 4  Persistência e Audit
    _persist_session_state() salva estado após cada pergunta
    _mask_transcript_segments() mascara PII na transcrição
    logger.info() — rastreamento via Python standard logging
    Transcrição armazenada com PII mascarado (LGPD Art. 12 / SEG-3B)

 5  Finalização
    finalize_screening(): gera WSIFinalReport
    _register_wsi_session(): registra no sistema de triagem principal
    Webhook /api/v1/twilio-voice/status confirma fim da chamada

RESTRIÇÕES:
  - Sem pause/resume durante chamada ao vivo
  - Sessão não interrompível mid-call
  - Score sempre determinístico (sem LLM path)

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E7-VOZ)                                      │
│  1. LGPD Consent Check — antes de iniciar chamada ●                          │
│  2. PII Masking — transcrição mascarada (_mask_transcript_segments) ●        │
│  3. FairnessGuard — check em cada resposta transcrita ●                      │
│  4. Scoring determinístico — sem LLM (zero viés de geração) ●                │
│  5. AuditTrail — EU AI Act + SOX compliant ●                                 │
│  6. CircuitBreaker — Twilio + Gemini STT + OpenAI TTS ●                      │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## TABELA: TRIGGERS DE TRIAGEM WSI

| # | Gatilho | Como | Endpoint | Automático? |
|---|---------|------|----------|-------------|
| 1 | Candidato se inscreve via web/portal | Aplicação criada | `POST /api/v1/applications` | ● Auto |
| 2 | Convite manual pelo recrutador | Recrutador seleciona candidato | `POST /api/v1/triagem/invite` | Manual |
| 3 | Bulk convite em massa | Recrutador seleciona N candidatos | `POST /api/v1/candidates/bulk/start-screening` | Manual |
| 4 | Candidato solicita ligação | Candidato clica "Quero ser entrevistado por telefone" | `POST /api/v1/triagem/{token}/request-call` | Manual (candidato) |
| 5 | Candidato inicia via WhatsApp | Candidato clica link WhatsApp | `POST /api/v1/triagem/{token}/whatsapp-initiate` | Manual (candidato) |
| 6 | Automation Engine (regra de pipeline) | Regra automática disparada por evento de pipeline | `POST /api/v1/automation/execute-action` action=`triagem_wsi` | ● Auto |
| 7 | Webhook ATS (evento externo) | ATS externo notifica novo candidato via Merge.dev | `POST /api/v1/automation/trigger-event` | ● Auto |

---

## E7A — TRIAGEM ABANDONADA

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PASSO A PASSO — E7A TRIAGEM ABANDONADA                                      │
│                                                                               │
│  • Candidato inicia a triagem mas para de responder                          │
│  • Timeout: 48h sem atividade → 1º lembrete automático (email ou WhatsApp) │
│  • +48h sem retorno → 2º lembrete                                            │
│  • Após 2º lembrete sem retorno → alerta ao consultor (Teams)               │
│  • Progresso parcial SALVO via PostgresSaver checkpoint                      │
│  • Candidato pode retomar de onde parou (exceto triagem por voz)            │
│                                                                               │
│  Resultado: Status "triagem_incompleta" — consultor pode cancelar            │
│  ou aguardar retorno do candidato                                             │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E7B — FEEDBACK PÓS-TRIAGEM

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PASSO A PASSO — E7B FEEDBACK PÓS-TRIAGEM                                   │
│                                                                               │
│  • Ag.2 WSIInterviewGraph: agradece ao candidato, dá feedback sobre          │
│    o processo (não sobre aprovação/reprovação), informa próximos passos     │
│  • Canal: mesmo da triagem (chat web, WhatsApp ou voz)                       │
│  • PersonalizedFeedbackService gera parecer textual personalizado            │
│  • Scores numéricos NÃO são enviados ao candidato                           │
│    (PipelineFeedbackTool._remove_score_references strip numérico)           │
│  • FeedbackGeneratorService (interview_intelligence) gera:                   │
│    - Pontos fortes identificados                                             │
│    - Áreas de desenvolvimento (sem discriminação)                           │
│    - Próximos passos esperados                                               │
│                                                                               │
│  Resultado: Candidato informado sobre próximos passos de forma respeitosa   │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E8 — APROVAR/REPROVAR TRIADOS (Gate 2) — 8 STEPS

### O que acontece nesta etapa (visão do processo)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PASSO A PASSO — E8 APROVAR/REPROVAR TRIADOS (Gate 2)                        │
│                                                                               │
│  • Consultor recebeu alerta (Teams) sobre candidatos triados                 │
│  • Revisa score WSI 0–10 + parecer LIA na plataforma                        │
│  • Aprova → SHORT LIST | Reprova → FEEDBACK                                 │
│  • Ag.10a PersonalizedFeedbackService gera parecer personalizado             │
│    (sem scores numéricos para o candidato)                                   │
│  • Ag.14a InterviewWSIService analisa contexto para entrevista               │
│  • ATSIntegrationReActAgent sincroniza status para o ATS via Merge.dev ●    │
│  • _generate_rediscovery_embedding: candidatos reprovados recebem            │
│    embedding para rediscoberta futura (talent pool futuro)                   │
│                                                                               │
│  Resultado: Aprovados → agendamento de entrevista (E9A)                      │
│  Reprovados → feedback personalizado (E9B)                                   │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Detalhamento técnico

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Gate 2 (pipeline) — 8 STEPS                                  │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Consultor revisa candidatos triados no Kanban
    POST /api/v1/pipeline/transition
    Body: { candidate_ids, from_stage: "triado", to_stage: "aprovado"|"reprovado",
            action: "approve"|"reject", reason, job_id }
    Authorization: Bearer <jwt_token>

 2  MainOrchestrator (CascadedRouter) + PolicyEngine
    Domínio = pipeline
    PolicyEngine: ALPHA1_SECTOR_RULES por setor
    SmartTransitionModal: confirmação em etapas críticas
    Automation Engine: verifica regras automáticas de Gate 2

 3  PipelineTransitionAgent processa
    Ag.4 PipelineTransitionAgent (orquestrador)
    Ag.4b PipelineContextAgent: agrega contexto + scores WSI
    Ag.4a PipelineDecisionAgent: valida a decisão
    Ag.4c PipelineActionAgent: executa transição

 4  FairnessGuard valida rejeições
    🔒 Auto-check em reject_candidate
    🔒 check_rejection_fairness vs 13 categorias protegidas
    Motivo discriminatório → BLOCK + alerta

 5  PersonalizedFeedbackService gera parecer
    Ag.10a PersonalizedFeedbackService (cv_screening):
    → Parecer textual personalizado por candidato
    → PipelineFeedbackTool._remove_score_references:
      strip scores numéricos do feedback ao candidato
    Ag.14a InterviewWSIService (interview_intelligence):
    → Analisa pontos para entrevista presencial

 6  LGPD + Audit
    🔒 PII Masking em logs
    🔒 audit_service.log_decision (ativado em approvals.py)
    Append-only, retenção SOX
    BiasAuditSnapshot: dados coletados em Gate 2

 7  Rediscovery Embedding
    _generate_rediscovery_embedding(candidate_id, job_id):
    Candidatos reprovados recebem embedding para rediscoberta futura
    Permite busca semântica retroativa ("candidatos para vagas similares")

 8  Resposta + Disparo de próxima etapa
    Aprovados → LIA agenda entrevista (E9A)
    Reprovados → LIA envia feedback (E9B)
    ATSIntegrationReActAgent: sync status ATS via Merge.dev ●
    Kanban board atualizado em real-time (WebSocket)

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E8)                                          │
│  1. FairnessGuard — check em rejeições ●                                     │
│  2. PII Masking — logs e feedback mascarados ●                               │
│  3. AuditTrail — Gate 2 decisions ● (ativado em approvals.py)               │
│  4. PolicyEngine — HITL thresholds ●                                         │
│  5. ATSIntegration — sync via Merge.dev ●                                    │
│  6. BiasAuditSnapshot — Four-Fifths Rule (acumulado Gates 1+2) ●             │
│  7. Rediscovery Embedding — candidatos reprovados indexados ●                 │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E9A — AGENDAR ENTREVISTA

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PASSO A PASSO — E9A AGENDAR ENTREVISTA                                      │
│                                                                               │
│  (Se APROVADO no Gate 2) LIA agenda entrevista                               │
│  • Email + WhatsApp ao candidato (data/hora + link reunião)                  │
│  • Ag.14 InterviewGraph [interview_scheduling] coordena:                      │
│    - check_availability: verifica agenda do recrutador (Google Calendar)     │
│    - schedule_interview: cria evento no calendário                           │
│    - ICS Calendar: apenas dtstart/dtend/summary/location/attendee           │
│      (sem dados sensíveis do candidato — data minimization)                 │
│  • CircuitBreaker: "google_calendar"                                          │
│  • Se NÃO encontra horário → alerta ao consultor via Teams                   │
│  • InterviewWSIService (interview_intelligence):                              │
│    analisa respostas WSI para sugerir perguntas de entrevista presencial     │
│                                                                               │
│  Resultado: Entrevista agendada, candidato e recrutador notificados           │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E9B — ENVIAR FEEDBACK

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PASSO A PASSO — E9B ENVIAR FEEDBACK (Reprovados)                            │
│                                                                               │
│  (Se REPROVADO no Gate 1 ou Gate 2) LIA envia feedback respeitoso           │
│  • Ag.10a PersonalizedFeedbackService gera o feedback:                       │
│    - Sem scores numéricos (strip obrigatório)                               │
│    - Pontos fortes identificados durante o processo                         │
│    - Recomendações de desenvolvimento (sem discriminação)                   │
│    - Agradecimento pela participação                                         │
│  • Ag.10b FeedbackGeneratorService (interview_intelligence):                 │
│    gera feedback baseado nos dados da entrevista WSI                        │
│  • Ag.10 CommunicationReActAgent envia via:                                  │
│    - Email (obrigatório)                                                    │
│    - WhatsApp (se consentimento registrado)                                 │
│  • FairnessGuard L1+L2: valida feedback antes de enviar                     │
│  • LGPD: opt-out link incluído                                               │
│                                                                               │
│  Resultado: Candidato recebe feedback respeitoso + recomendações             │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## SEÇÃO TRANSVERSAL: PORTAL DO CANDIDATO + LGPD/DSR

### Portal do Candidato

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PORTAL DO CANDIDATO — LGPD/DSR                                              │
│                                                                               │
│  Frontend (Next.js 15):                                                       │
│    /portal/data-request/[token]  → portal de DSR com verificação OTP        │
│    /shared/[token]               → visualização compartilhada de perfil       │
│                                                                               │
│  Domínio: candidate_self_service                                              │
│  Ações disponíveis:                                                           │
│    get_status     → status atual no pipeline + próximos passos               │
│    get_interview_info → data/hora/formato da entrevista agendada             │
│    get_feedback   → feedback WSI (se habilitado pela empresa)                │
│    get_lgpd_info  → direitos LGPD Art. 20 (decisões automatizadas)          │
│  Segurança: IDOR protection — usa user_id do JWT, não params da URL          │
│                                                                               │
│  Fluxo de DSR (Data Subject Request):                                        │
│    POST /api/v1/data-subject-requests/              → criar solicitação      │
│    GET  /api/v1/data-subject-requests/track/{id}   → status público          │
│    GET  /api/v1/data-subject-requests/stats        → métricas (DPO/Admin)   │
│    PUT  /api/v1/data-subject-requests/{id}/assign  → atribuir ao DPO        │
│    PUT  /api/v1/data-subject-requests/{id}/verify-identity                   │
│    PUT  /api/v1/data-subject-requests/{id}/complete → resolver + notificar  │
│  SLA: 15 dias úteis (LGPD Art. 18)                                           │
│                                                                               │
│  Serviços LGPD:                                                               │
│    dsr_export_service: exporta dados do candidato em JSON (portabilidade)   │
│    lgpd_cleanup_service: deletar dados por retenção (90/180/365 dias)       │
│    granular_consent_service: consentimento por finalidade (7 propósitos)    │
│    ConsentCheckerService: verifica consentimento antes de processar          │
│                                                                               │
│  Endpoints de gestão:                                                         │
│    POST /api/v1/data-subject-requests/         → DSR público                 │
│    POST /api/v1/admin/lgpd/run-cleanup         → gestão DPO (cleanup)        │
│    GET  /api/v1/admin/lgpd/cleanup-status      → status de pendências        │
│    POST /api/v1/consent/...                    → consentimento geral          │
│    POST /api/v1/consent/granular/...           → consentimento por finalidade │
│                                                                               │
│  Papel DPO (migration 093):                                                   │
│    Acesso ao /api/v1/admin/lgpd                                               │
│    Pode atribuir, resolver e notificar DSRs                                   │
│    Relatórios de compliance LGPD                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Consentimento Granular

```
7 finalidades gerenciadas por granular_consent_service:
  1. ai_screening     → processamento de triagem WSI (BLOQUEANTE se revogado)
  2. ai_scoring       → scoring automático (BLOQUEANTE se revogado)
  3. ai_video_analysis → análise de vídeo (BLOQUEANTE se revogado)
  4. ai_comparison    → comparação com outros candidatos
  5. data_retention   → retenção além do processo
  6. marketing        → comunicações de marketing
  7. analytics        → uso de dados em analytics agregado

Fluxo de verificação:
  ConsentCheckerService.check_candidate_consent(candidate_id, company_id, purpose)
  → allowed: bool + reason: str + soft_warning: bool
  Se propósito BLOQUEANTE revogado → operação cancelada + log de auditoria
```

---

## SEÇÃO TRANSVERSAL: AUTOMATION ENGINE

### Automation Engine

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  AUTOMATION ENGINE — Motor de Regras de Pipeline                              │
│                                                                               │
│  Domínio: automation                                                          │
│  Agente: AutomationReActAgent                                                 │
│    app/domains/automation/agents/automation_react_agent.py                   │
│  Serviço: automation_trigger_service                                          │
│    app/domains/automation/services/automation_trigger_service.py             │
│                                                                               │
│  Conceito: Regras "quando X acontece → executar Y"                           │
│  Exemplos:                                                                    │
│    - "quando candidato chega ao stage FUNIL → iniciar triagem WSI"          │
│    - "quando score WSI ≥ 8 → mover para SHORT LIST sem HITL"               │
│    - "quando candidato abandonou triagem há 48h → enviar lembrete"          │
│    - "quando novo candidato via ATS → convidar para triagem"                │
│                                                                               │
│  Endpoints:                                                                   │
│    GET  /api/v1/automation/triggers        → listar triggers ativos          │
│    POST /api/v1/automation/triggers/{id}  → habilitar/desabilitar trigger   │
│    POST /api/v1/automation/check          → verificar e executar triggers    │
│    GET  /api/v1/automation/status         → status do engine                 │
│    GET  /api/v1/automation/stage-suggestions → sugestões por stage           │
│    POST /api/v1/automation/execute-action → executar ação manual             │
│    POST /api/v1/automation/screen-candidate → triagem via automation         │
│    POST /api/v1/automation/trigger-event  → evento externo (ATS)             │
│                                                                               │
│  Ações disponíveis via execute-action:                                        │
│    triagem_wsi      → iniciar triagem WSI automática                         │
│    pipeline_move    → mover candidato de stage                               │
│    send_alert       → enviar alerta ao recrutador                            │
│    send_email       → enviar email ao candidato                              │
│    ats_sync         → sincronizar status no ATS                              │
│                                                                               │
│  Interação com outras etapas:                                                 │
│    E5 Gate 1: regras de auto-aprovação por score                             │
│    E6 Follow-up: cadência automática                                         │
│    E7 Triagem: triggers automáticos de convite                               │
│    E8 Gate 2: regras de auto-aprovação pós-triagem                          │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## SEÇÃO TRANSVERSAL: ADMIN & OBSERVABILIDADE

### Admin Platform + Monitoramento de Agentes

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  ADMIN & OBSERVABILIDADE                                                      │
│                                                                               │
│  ADMIN PLATFORM                                                               │
│    Endpoints: /api/v1/admin/...  (admin.py — prefix "/admin")                │
│    Dashboard Next.js: visão executiva da plataforma                          │
│    Métricas: candidatos processados, vagas ativas, score médio WSI           │
│                                                                               │
│  AGENT MONITORING                                                             │
│    Endpoints: /api/v1/agent-monitoring/...  (prefix "/agent-monitoring")     │
│    Monitoramento: latência por agente, erros, loop iterations                │
│    Métricas Prometheus: login_attempts_total, fairness_blocks_total, etc.    │
│    LangSmith/LangFuse: tracing de chamadas LLM                               │
│    Sentry: error tracking com PII masking                                    │
│    Model Drift: alertas automáticos (WARNING / URGENT)                       │
│    Silent-fallback telemetry: agentes sem domínio mapeado detectados         │
│      (GET /api/v1/orchestrator/health → get_fallback_stats())                │
│                                                                               │
│  FAIRNESS / BIAS ADMIN                                                        │
│    GET /api/v1/admin/compliance/fairness/report  (prefix "/admin/compliance")│
│    GET /api/v1/bias-audit/...                    (prefix "/bias-audit")      │
│    Serviço: bias_detector_service (domínio compliance)                       │
│    Visualização: Four-Fifths Rule por vaga/empresa/período                   │
│    Exportação: relatórios de bias audit para auditoria externa               │
│                                                                               │
│  AI CONSUMPTION OUTBOX (migration 095)                                        │
│    Endpoints: /api/v1/ai-consumption/...  (prefix "/ai-consumption")         │
│    Tracking: tokens consumidos por tenant, por domínio, por agente           │
│    Uso: billing, alertas de custo, otimização de prompts                     │
│    Granularidade: por company_id, por modelo LLM, por período                │
│                                                                               │
│  CIRCUIT BREAKERS                                                             │
│    GET  /api/v1/admin/circuit-breakers               → status de todos       │
│    POST /api/v1/admin/circuit-breakers/{name}/reset  → reset manual          │
│    POST /api/v1/admin/circuit-breakers/reset-all     → reset geral           │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## SEÇÃO TRANSVERSAL: INTEGRAÇÕES EXTERNAS

### Mapa de Integrações (abril/2026)

| Serviço | Finalidade | CircuitBreaker | Status |
|---------|------------|----------------|--------|
| **Twilio Voice** | Chamadas de voz para triagem (E7-VOZ — pipeline PSTN) | "twilio" | ● |
| **Gemini Flash 2.5** (STT) | STT via WAV — pipeline Twilio PSTN: μ-law→WAV→Gemini API | "gemini" | ● |
| **OpenAI Whisper** (STT) | STT para áudio web: `POST /api/v1/triagem/{token}/audio` (upload de áudio do browser) | "openai" (shared) | ● |
| **OpenAI TTS** | Text-to-Speech — voz da LIA (ambos os pipelines) | "openai_tts" | ● |
| **OpenAI** (embeddings) | text-embedding-3-small (1536-dim) — VectorSemanticCache | "openai" | ● |
| **Gemini** (Google) | LLM principal (produção) — todos os agentes | "gemini" | ● |
| **Anthropic Claude** | JD Generator — geração de job descriptions | "anthropic" | ● |
| **GitHub** | Sourcing de desenvolvedores (GithubSourcingAgent) | "github" | ● |
| **Pearch AI** | Sourcing e enriquecimento de candidatos (email + telefone) | "pearch" | ● |
| **Apify** | Web scraping e enriquecimento externo (SourcingEnrichAgent) | "apify" | ● |
| **StackOverflow** | Sourcing de perfis técnicos (StackOverflowSourcingAgent) | "stackoverflow" | ● |
| **Merge.dev** | ATS integration unificada (Greenhouse, Lever, etc.) | "merge" | ● |
| **SendGrid** | Email transacional (primário) | "sendgrid" | ● |
| **Resend** | Email transacional (fallback) | "resend" | ● |
| **WhatsApp via Twilio** | Mensagens WhatsApp para triagem e follow-up | "twilio_whatsapp" | ● |
| **Google Calendar** | Agendamento de entrevistas (InterviewGraph) | "google_calendar" | ● |
| **WorkOS** | SSO corporativo (login enterprise) | "workos" | ● |
| **Redis** | Cache de embeddings, rate limiting, session state | — | ● |
| **LangSmith / LangFuse** | Tracing de chamadas LLM para observabilidade | — | ◐ |

---

## SEÇÃO TRANSVERSAL: COMPLIANCE

### FactChecker — 4 Tipos de Verificação

```
Arquivo: app/shared/compliance/fact_checker.py

Tipo 1: Experiência declarada — claims vs dados de contexto
Tipo 2: Certificações — validade técnica
Tipo 3: Período na empresa — coerência temporal
Tipo 4: Habilidades técnicas — relevância para a vaga
V5: verificações granulares adicionais (salary, count, %, date)

Integração: DomainWorkflow._post_check (enable_fact_checker=True por default)
Claim inconsistente → flag para revisão

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
  Dashboard de Bias Audit: /api/v1/bias-audit/... (●)
  Acesso admin: /api/v1/admin/compliance/fairness/report (●)
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
  ● Ativo em TODAS as etapas: auth.py, jd_generation.py,
    wsi_questions.py, sourcing_react_agent.py, pipeline.py,
    approvals.py, communication.py, rubric_evaluation.py,
    scheduling.py, voice_screening_orchestrator.py
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
ModelDrift: trigger automático quando feedback rejected/ignored acumula
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
seed_email_ab_tests: 3 experimentos criados no startup ●

Etapas ativas: E2, E3, E4, E6, E7, E9
```

### 3. Routing Adaptativo

```
Arquivo: app/services/routing_learning_service.py
Mecanismo: Quando recrutador corrige roteamento, ajusta multipliers
Range: 0.8x (muitos erros) a 1.2x (alta precisão) por domínio
Método: compute_domain_confidence_adjustments(company_id, db)
Silent-fallback telemetry: get_fallback_stats() via /api/v1/orchestrator/health

Etapas ativas: E4, E5, E8
```

### 4. Template Learning

```
Arquivo: app/shared/learning/template_learning_service.py
Mecanismo: Após 3 vagas similares (mesmo setor/seniority), gera template
Métodos: learn_from_job_creation(), suggest_templates_for_improvement()
Data sources: UNION de message_queue e communication_logs (corrigido)

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
Escala: 0–10 (migration 090)
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

Etapas ativas: E0, E2, E3, E4, E5, E6, E7
```

### 10. Semantic Search + SkillsOntologyEngine

```
SemanticSearch:
  Arquivo: app/shared/intelligence/semantic_search_service.py
  Provider: Gemini text-embedding-004 (768 dimensões)
  Cache: Redis para evitar re-embedding
  Domínios: Skills, Job Titles, Industries, Locations

SkillsOntologyEngine:
  Arquivo: app/domains/talent_intelligence/services/skills_ontology_engine.py
  API: /api/v1/skills_catalog + /api/v1/job_embeddings
  Expande queries com ontologia semântica de skills
  Integração: RAGPipelineService.search(**kwargs) — kwargs incluem job_title, sector

Etapas ativas: E2, E3, E4
```

### 11. Voice Analysis (Stack Atual)

```
Arquivo: app/domains/voice/services/voice_screening_orchestrator.py
         app/domains/voice/services/voice_service.py
         app/domains/voice/services/gemini_live_audio_service.py

Stack de voz — DOIS pipelines distintos:
PIPELINE A — Twilio PSTN (voice_screening_orchestrator.py):
  STT: Gemini Flash 2.5 (μ-law → WAV via mulaw_to_wav() → Gemini API)
  TTS: OpenAI TTS (voice="nova" → mp3_to_mulaw() → Twilio)
  Telecomunicação: Twilio Voice (chamadas telefônicas, μ-law 8kHz)
PIPELINE B — Áudio web (triagem.py):
  Endpoint: POST /api/v1/triagem/{token}/audio
  STT: OpenAI Whisper (whisper-1) via VoiceService.transcribe_audio()
  TTS: OpenAI TTS (voice="nova") para perguntas da LIA
PIPELINE C (disponível): Gemini Live Audio (GeminiLiveAudioService — browser↔Gemini WebSocket direto)

Uso: Triagem WSI por voz — candidato responde por áudio
VoiceScreeningOrchestrator: coordena triagem completa por voz
Scoring: sempre determinístico (sem LLM para calcular scores)

Etapas ativas: E7-VOZ
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
Arquivos: app/api/v1/consent_management.py + communication_optout.py
          app/api/v1/granular_consent.py
          app/domains/lgpd/services/granular_consent_service.py

1. Consentimento para triagem WSI (SEG-4):
   WelcomeCard com checkbox explícito obrigatório
   Botões desabilitados até aceite LGPD
   ConsentEvent auditável registrado
   ConsentCheckerService verifica purpose="ai_screening" antes de iniciar

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

4. Consentimento granular por finalidade:
   7 finalidades gerenciadas por granular_consent_service
   POST /api/v1/consent/granular → registrar por propósito
   BLOQUEANTE para: ai_screening, ai_scoring, ai_video_analysis
```

### DSR — Data Subject Requests

```
Endpoints:
  POST /api/v1/data-subject-requests/               → criar DSR público
  GET  /api/v1/data-subject-requests/track/{id}    → status público
  GET  /api/v1/data-subject-requests/stats          → métricas DPO
  PUT  /api/v1/data-subject-requests/{id}/assign    → atribuir DPO
  PUT  /api/v1/data-subject-requests/{id}/verify-identity
  PUT  /api/v1/data-subject-requests/{id}/complete  → resolver + notificar

Serviços:
  dsr_export_service: exporta dados em JSON (portabilidade — LGPD Art. 18 V)
  lgpd_cleanup_service: deleta por retenção (90/180/365 dias)
  granular_consent_service: 7 propósitos de consentimento

Portal público: /portal/data-request/[token]
  Fluxo: loading → OTP verification → form → completed
  Suporte a upload de documentos + submissão parcial

SLA: 15 dias úteis (LGPD Art. 18) — implementado no DSR service

Papel DPO (migration 093):
  Acesso ao /api/v1/admin/lgpd
  Gerência de DSRs, identity verification, relatórios
```

### Data Minimization

```
Princípios aplicados:
  1. ICS Calendar: apenas dtstart/dtend/summary/location/attendee
     Sem dados sensíveis do candidato
  2. ATS Sync (Merge.dev): ATSSyncService filtra dados sensíveis (salário)
     "Dado sensível - não sincronizar"
  3. Feedback: PipelineFeedbackTool._remove_score_references
     Strip scores numéricos do feedback ao candidato
  4. PII Masking: 4 camadas pré-LLM
     LLM nunca vê dados reais
  5. ToonService: anonymize=True para visualização anônima
  6. Transcrição de voz: _mask_transcript_segments() mascara PII
```

### Retenção por Tipo de Dado

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  Tipo de Dado              │ Retenção        │ Base Legal                    │
│───────────────────────────┼─────────────────┼───────────────────────────────│
│  Audit Trail (SOX)         │ 730-1825 dias   │ SOX compliance, Art. 12 LGPD │
│  Scores WSI                │ Duração processo│ Legítimo interesse            │
│  Dados de candidato (PII)  │ Até revogação   │ Consentimento                 │
│  Candidatos rejeitados     │ 90 dias         │ lgpd_cleanup_service          │
│  Mensagens de chat         │ 90 dias         │ lgpd_cleanup_service          │
│  Notas de entrevista       │ 180 dias        │ lgpd_cleanup_service          │
│  Logs de screening/IA      │ 365 dias        │ lgpd_cleanup_service          │
│  Logs de comunicação       │ 365 dias        │ Legítimo interesse            │
│  Embeddings de perfil      │ Indefinido      │ Anonimizados (sem PII)        │
│  Learning patterns         │ Indefinido      │ Agregados (sem PII individual)│
│  LLM prompts/responses     │ 90 dias         │ Auditoria + melhoria          │
│  Conversation memory       │ Sessão          │ Efêmero                       │
│  Long-term memory          │ Compressão 30d  │ Anonimizado                   │
│  Transcrição de voz        │ 90 dias         │ Mascarada (sem PII)           │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## MAPA CONSOLIDADO DE AGENTES

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  MAPA DE AGENTES — ALPHA 1 (abril/2026)                                       │
│                                                                               │
│  Ag.0 MainOrchestrator                                                        │
│    Classe: MainOrchestrator                                                   │
│    Domínio: orchestrator                                                      │
│    LLM: Gemini (CascadedRouter T5) | Fallback: AutonomousReActAgent (T6)    │
│    Tools: CascadedRouter (6-tier), ActionExecutor, PendingAction,            │
│           navigation_intent, AgenticLoop, PreconditionChecker                │
│    Etapas: E0 (chat LIA), E5, E6, E7 (coordenação geral)                   │
│    FG: L1+L2 (pré-roteamento) | Anti-Sycophancy: ORCHESTRATOR               │
│                                                                               │
│  Ag.1 SourcingReActAgent + sub-agentes                                        │
│    Classe: SourcingReActAgent (LangGraphReActBase + EnhancedAgentMixin)       │
│    Sub-agentes: Planner, Search, Enrich, Engagement                          │
│                 GitHub, StackOverflow, Diversity, Referral                   │
│                 PassivePipeline, NurtureSequence                              │
│    Domínio: sourcing                                                          │
│    LLM: Gemini | max_iterations: 5 | max_tool_calls: 3                      │
│    Tools: 15 (search, analyze, compare, rank, outreach, generate_message)    │
│    Etapas: E4 (busca de candidatos)                                          │
│    FG: L1+L2+L3 | PII: ativo | Audit: ●                                    │
│                                                                               │
│  Ag.2 WSIInterviewGraph                                                       │
│    Classe: WSIInterviewGraph (LangGraph StateGraph)                          │
│    Domínio: cv_screening                                                      │
│    LLM: Gemini | 8 stages | Bloom+Dreyfus+BigFive | Escala 0–10              │
│    HITL: interrupt_before=["generate_feedback"]                              │
│    Checkpoint: PostgresSaver (sessões 30-120 min)                            │
│    Etapas: E7 (conduz entrevista WSI), E7B (feedback pós-triagem)            │
│    FG: L1+L2+L3 | PII: ativo | Fact-Check: ativo | Audit: ●                │
│                                                                               │
│  Ag.3 WSIService (Scoring)                                                    │
│    Classe: WSIService + WSIDeterministicScorer                                │
│    Domínio: cv_screening                                                      │
│    LLM: SEM LLM (determinístico — zero latência, zero custo)                 │
│    Escala: 0–10 (migration 090)                                               │
│    Etapas: E4 (score WSI na busca), E7 (calcula score final)                 │
│    ScoreNormalization: difficulty_coefficient ativo                           │
│                                                                               │
│  Ag.3a VoiceScreeningOrchestrator                                             │
│    Domínio: voice                                                             │
│    Pipeline A (PSTN): Twilio Voice + Gemini Flash 2.5 STT + OpenAI TTS      │
│    Pipeline B (web): POST /triagem/{token}/audio → OpenAI Whisper STT       │
│    Scoring: DETERMINÍSTICO (sem LLM para scores)                             │
│    Etapas: E7-VOZ (triagem por ligação telefônica)                           │
│    Endpoints: /api/v1/triagem/{token}/request-call                           │
│               /api/v1/twilio-voice/status  (webhook Twilio)                  │
│                                                                               │
│  Ag.3d RubricEvaluationService                                                │
│    Domínio: interview_intelligence                                            │
│    LLM: Gemini | BARS anchors por pergunta                                   │
│    Etapas: E3 (anchors), E7 (scoring BARS), E8 (análise pós-triagem)        │
│                                                                               │
│  Ag.4 PipelineTransitionAgent + sub-agentes                                   │
│    Classe: PipelineTransitionAgent (LangGraphReActBase + EnhancedAgentMixin) │
│    Sub-agentes: PipelineDecisionAgent, PipelineContextAgent,                 │
│                 PipelineActionAgent                                           │
│    Domínio: pipeline | LLM: Gemini                                           │
│    Invocação: POST /api/v1/pipeline/interpret-context (direta)               │
│    Tools: 20 | Etapas: E5, E8 (transições de pipeline)                       │
│                                                                               │
│  Ag.5 KanbanReActAgent + sub-agentes                                          │
│    Classe: KanbanReActAgent                                                   │
│    Sub-agentes: KanbanSearchAgent, KanbanInsightAgent, KanbanActionAgent     │
│    Registry: "kanban" | Domínio: recruiter_assistant | LLM: Gemini           │
│    Tools: 22 (maior número) | Etapas: E5, E8 (Kanban board)                 │
│                                                                               │
│  Ag.6 WizardReActAgent + JobWizardGraph                                       │
│    Registry: "wizard" | Domínio: job_management | LLM: Gemini               │
│    6 stages: input-evaluation → jd-enrichment → salary → competencies →      │
│              wsi-questions → review-publish                                   │
│    Tools: 10 | Etapas: E2, E3 (criação/edição de vagas)                      │
│    WizardOrchestratorService: coordena wizard multi-step                      │
│                                                                               │
│  Ag.7 JobsManagementReActAgent                                                │
│    Registry: "jobs_management" | Domínio: recruiter_assistant | LLM: Gemini  │
│    Etapas: E0 (operações de vagas via chat), E2                               │
│                                                                               │
│  Ag.8 TalentReActAgent                                                        │
│    Registry: "talent" | Domínio: recruiter_assistant | LLM: Gemini           │
│    Tools: 13 | Stages: discovery → analysis → action_planning               │
│    Etapas: E4 (funil de talentos)                                            │
│                                                                               │
│  Ag.9 PolicyReActAgent                                                        │
│    Registry: "policy" | Domínio: hiring_policy | LLM: Gemini                │
│    Tools: 13 | Setup wizard por blocos                                       │
│    Etapas: Transversal (configuração de políticas por setor)                 │
│                                                                               │
│  Ag.10 CommunicationReActAgent + serviços                                     │
│    Classes: CommunicationReActAgent (ReAct)                                  │
│             PersonalizedFeedbackService (Ag.10a)                             │
│             FeedbackGeneratorService (Ag.10b, interview_intelligence)        │
│    Domínios: communication + cv_screening + interview_intelligence           │
│    LLM: Gemini | max_iterations: 5                                           │
│    Etapas: E5 (feedback rejeição), E6 (contato email),                      │
│            E8 (feedback Gate 2), E9B (feedback reprovado)                    │
│    FG: L1+L2 | LGPD: opt-out obrigatório                                    │
│                                                                               │
│  Ag.11 ATSIntegrationReActAgent ●                                             │
│    Classe: ATSIntegrationReActAgent                                           │
│    Domínio: ats_integration | LLM: Gemini                                    │
│    Integração: Merge.dev (Greenhouse, Lever, e outros ATS via API unificada) │
│    Tools: sync_candidate_to_ats, fetch_candidate_from_ats, validate_fields   │
│    Etapas: E2 (sync ATS), E5 (sync status), E8 (sync status)                │
│    Status: ● Funcional via Merge.dev                                          │
│                                                                               │
│  Ag.12 AnalyticsAgent                                                         │
│    Domínio: analytics | LLM: Gemini                                           │
│    Etapas: Transversal (KPIs, funil, relatórios)                             │
│    PredictiveAnalytics: TTF, salary, skill_success                           │
│                                                                               │
│  Ag.13 AutomationReActAgent                                                   │
│    Classe: AutomationReActAgent                                               │
│    Domínio: automation | LLM: Gemini                                          │
│    Serviço: automation_trigger_service                                        │
│    Etapas: E5, E6, E7, E8 (triggers automáticos)                             │
│                                                                               │
│  Ag.14 InterviewGraph + InterviewWSIService                                   │
│    Classe: InterviewGraph (LangGraph StateGraph)                             │
│    Domínio: interview_scheduling | LLM: Gemini | 6 nós                      │
│    Tools: schedule_interview, check_availability, reschedule, cancel         │
│    InterviewWSIService (Ag.14a, interview_intelligence):                      │
│    → analisa WSI para sugerir perguntas de entrevista presencial             │
│    Etapas: E9A (agendar entrevista)                                          │
│    CircuitBreaker: "google_calendar"                                         │
│                                                                               │
│  SERVIÇOS ESPECIALIZADOS (sem rótulo Ag.):                                   │
│                                                                               │
│  JobDescriptionGeneratorService                                              │
│    Domínio: job_management | LLM: Claude (Anthropic)                         │
│    Etapas: E2 (gera JD), E3 (JD como base para WSI)                         │
│    Endpoint: POST /api/v1/briefing/generate-jd                               │
│                                                                               │
│  SkillsOntologyEngine                                                         │
│    Domínio: talent_intelligence                                               │
│    Etapas: E2, E4 (expansão de skills)                                       │
│    API: /api/v1/skills_catalog + /api/v1/job_embeddings                      │
│                                                                               │
│  WSIScreeningPipeline                                                         │
│    Domínio: cv_screening | LLM: Gemini                                       │
│    Etapas: E4 (triagem/screening na busca), E7 (fallback de perguntas)      │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Grafo de Dependências

```
                    ┌──────────────┐
                    │    Ag.0      │
                    │ Orchestrator │
                    └──────┬───────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
   ┌─────▼────┐    ┌───────▼───────┐  ┌──────▼─────┐
   │  Ag.1    │    │    Ag.2       │  │   Ag.11    │
   │ Sourcing │    │ WSIInterview  │  │    ATS     │
   │ (10 sub) │    │    Graph      │  │ Merge.dev  │
   └─────┬────┘    └───────┬───────┘  └──────┬─────┘
         │                 │                 │
   ┌─────▼────┐    ┌───────▼───────┐         │
   │  Ag.8    │    │    Ag.3       │         │
   │  Talent  │    │  WSIService   │         │
   └──────────┘    │(determinístico│         │
                   └───────┬───────┘         │
                           │                 │
               ┌───────────┼─────────────────┘
               │           │
         ┌─────▼────┐ ┌────▼──────┐
         │  Ag.4    │ │  Ag.10    │
         │ Pipeline │ │  Commun.  │
         │ (4 sub)  │ │(feedback) │
         └─────┬────┘ └────┬──────┘
               │           │
         ┌─────▼────┐ ┌────▼──────┐
         │  Ag.5    │ │  Ag.14    │
         │  Kanban  │ │Interview  │
         │ (3 sub)  │ │Scheduling │
         └──────────┘ └───────────┘

         ┌─────────────────────────┐
         │      Ag.13              │
         │  AutomationEngine       │
         │  (dispara E5/E6/E7/E8) │
         └─────────────────────────┘
```

---

## FORA DO ESCOPO ALPHA 1

As seguintes funcionalidades têm código existente mas estão **explicitamente excluídas** do Alpha 1:

| Funcionalidade | Domínio/Classe | Motivo |
|----------------|---------------|--------|
| **Agent Studio** | `agent_studio`, `AgentTemplate`, `_YamlDomainProxy` | Customização de agentes por tenant — fase posterior |
| **Digital Twin** | `digital_twin`, `TwinInferenceService` | Réplica digital de candidatos — fase posterior |
| **Talent Pool** | `talent_pool` | Pool gerenciado de candidatos passivos — fase posterior |
| **Recruitment Campaign** | `recruitment_campaign` | Campanhas de marketing de recrutamento — fase posterior |

> Nota: A infra de Agent Studio existe no código (`get_domain_for_company()` em `registry.py` consulta `AgentTemplate` publicados). Não está exposta no Alpha 1 mas é não-destrutiva — tenants sem templates publicados recebem o domínio padrão WeDO.

---

*Documento gerado a partir do código real do lia-agent-system (Replit) e documentação specs existente. Complementa o `ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md` com nível de detalhe técnico passo-a-passo por etapa. Última auditoria contra o código: abril/2026 (v2.0).*
