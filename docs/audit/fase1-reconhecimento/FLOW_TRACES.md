# FLOW_TRACES.md — Mapa de Fluxos Agênticos com Integração Vertical
**Protocolo:** P02  
**Auditado em:** 2026-04-13  
**Sistema:** LIA Agent System — /home/runner/workspace/lia-agent-system/  
**Auditor:** Claude Opus 4.6 (SSH trace + codebase deep read)

---

## ÍNDICE

| Flow | Nome | Severidade máxima de gaps |
|---|---|---|
| F1 | Busca de Candidatos | 🔴 CRÍTICO |
| F2 | Triagem/Screening WSI | 🔴 CRÍTICO |
| F3 | Avaliação Comportamental/Técnica (WSI Interview) | 🔴 CRÍTICO |
| F4 | Comunicação com Candidato (WhatsApp/Email) | 🔴 CRÍTICO |
| F5 | Agendamento de Entrevista | 🔴 CRÍTICO |
| F6 | Chat Livre do Recrutador (Kanban Insight) | 🟡 ALTO |
| F7 | Criação/Configuração de Vaga | 🟡 ALTO |
| F8 | Relatórios e Analytics | 🟡 ALTO |

---

## FLOW 1 — BUSCA DE CANDIDATOS

```
[Browser] ──WS JSON {type:"message", domain:"recruiter_assistant"}──▶ [agent_chat_ws.py:389]
  → JWT decode → company_id + user_id extraídos (lines 405–406)
  → WSManager.connect() — session registrada com user_id

[SEG LAYER] agent_chat_ws.py:604–658
  → [604] PromptInjectionGuard.check(content)     — bloqueia HIGH risk
  → [622] check_input_security(content)            — SecurityPatterns
  → [637] FairnessGuard.check(content)             — bloqueia se is_blocked (Layer 1)
  → [655] pre_compliance(content, company_id, "recruiter_assistant")
           ⚠ "sourcing" NÃO está em _FAIRNESS_DOMAINS → C3b PII strip NOT aplicado aqui

[CascadedRouter.route()] cascaded_router.py:176
  T0 MemoryResolver — resolve pronomes via WorkingMemory(session_id)
  T1 LRU in-process — MD5 hash → MISS (nova mensagem)
  T2 Redis hash — MISS
  T3 VectorSemanticCache (pgvector cosine ≥ 0.85) — MISS
  T4 FastRouter — regex r"encontrar?\s+\w*\s*candidato" → domain="sourcing", conf≈0.90
     → resultado salvo em LRU + Redis + VectorCache
  (T5 LLM e T6 Autonomous não atingidos)

[DISPATCH] agent_chat_ws.py:796–832
  active_domain = "sourcing"
  → AgentRegistry.get_or_fallback("sourcing_search", fallback="talent")
  → SourcingSearchAgent (ou TalentReActAgent como fallback silencioso)

[TalentReActAgent / SourcingSearchAgent]
  → _fairness_pre_check() — FairnessGuard TERCEIRA vez (talent_react_agent.py:135)
  → _process_langgraph() → LangGraph create_react_agent → tool loop (max 5 iter)

[Tool: search_candidates] query_tools.py:31–186
  SQL: SELECT * FROM candidate
       WHERE company_id = :company_id          -- tenant isolation
         AND years_experience >= :min_exp
         AND location ILIKE '%:location%'
       LIMIT 100 (limit*5 pois has_post_filters=True)
  Post-filter Python (in-memory):
    [c for c in candidates if skill in c.skills]
  → candidates[:20] retornados
  ⚠ Sem ORDER BY → ordem não determinística
  ⚠ company_id filtrado via hasattr(Candidate, 'company_id') — condicional

[RANKING — se chamado explicitamente]
  rank_candidates() → WRFDynamicKService.rank_candidates()
  WRF: combina es_rank + pgv_rank com K dinâmico por qualification_level
  ⚠ search_candidates NÃO chama rank_candidates automaticamente

[AgentOutput]
  message: texto LLM interpretando candidatos
  actions: [AgentAction(call_tool, {tool: "search_candidates"})]
  confidence: 0.82

[Resposta WS]
  _strip_react_json(output.message)
  → post_compliance() (apenas domains em _FAIRNESS_DOMAINS — sourcing excluído)
  → serialize_message(content, confidence, domain, source, actions)
  → ws_mgr.send_to_session(session_id, {...})

[SIDE EFFECTS]
  ✓ ConversationMemory persisted (mensagem + resposta) via _setup_conversation_memory
  ✓ increment_usage(company_id, tokens)
  ⚠ LRU + Redis cache para rota (não para resultado de busca)
  ✗ Nenhum audit_service.log_decision() em search_candidates
  ✗ BiasAuditService.audit_ranking_results() — existe mas NUNCA chamado aqui
```

**CROSS-CUTTING:**
```
├─ Fairness:  ✓ INPUT bloqueado 3× (WS:637, Orchestrator:222, Agent:135)
│             ⚠ RESULTADOS de busca sem bias audit (BiasAuditService existe mas não é chamado)
├─ LGPD:      ⚠ Consentimento do candidato NÃO verificado antes de search_candidates
│             ⚠ C3b NÃO aplica a "sourcing" (c3b_layer.py:17–26 — _FAIRNESS_DOMAINS exclui sourcing)
├─ Bias:      ✗ Ausente nos resultados — BiasAuditService passivo, requer chamada explícita
└─ Error:     ✓ try/except geral em search_candidates
              ⚠ AgentRegistry fallback "talent" silencioso — sem alerta ao usuário
```

**INTEGRATION VERIFIED:**
```
├─ Agente → Tool:      ✓ LangGraph create_react_agent → search_candidates via tool_definition_to_langchain_tool
├─ Tool → Backend:     ✓ SQLAlchemy AsyncSessionLocal direto no tool
├─ Backend → Banco:    ⚠ company_id filter usa hasattr(Candidate,'company_id') — se campo ausente no ORM
│                         filtro é omitido silenciosamente → cross-tenant leak (query_tools.py:79–82)
├─ Backend → Externo:  N/A (busca só DB interno)
├─ Banco → Frontend:   ✓ resultado → LLM interpreta → WS serialize_message → frontend
├─ Resultado → Agente: ✓ tool retorna dict → LangGraph state → AgentOutput.message
├─ Tenant isolation:   ⚠ CONDICIONAL — depende de hasattr(Candidate,'company_id')
└─ Audit trail:        ✗ search_candidates NÃO gera audit log
                       ⚠ C3b post_compliance só para _FAIRNESS_DOMAINS (exclui "sourcing")
```

**GAPS:**
| ID | Severidade | Descrição | Arquivo:Linha |
|---|---|---|---|
| F1-G1 | 🔴 CRÍTICO | `hasattr(Candidate,'company_id')` — filtro de tenant omitido silenciosamente se campo ausente no ORM | query_tools.py:79–82 |
| F1-G2 | 🟠 ALTO | LGPD consent não verificado antes de search_candidates | query_tools.py:44–186 |
| F1-G3 | 🟠 ALTO | BiasAuditService passivo — audit_ranking_results nunca chamado em busca conversacional | query_tools.py:164–178 |
| F1-G4 | 🟡 MÉDIO | C3b não se aplica a domínio "sourcing" — FairnessGuard L3 e PII strip ausentes | c3b_layer.py:17–26 |
| F1-G5 | 🟡 MÉDIO | Sem audit log de search_candidates (SOX/LGPD gap — quem buscou o quê quando) | query_tools.py:186 |
| F1-G6 | 🟡 MÉDIO | Skills filter é post-query Python — ineficiente em escala, pode perder candidatos além do limite pré-filtro | query_tools.py:124–133 |
| F1-G7 | 🟢 BAIXO | Sem ORDER BY em search_candidates → resultados não determinísticos entre execuções | query_tools.py:118–123 |

---

## FLOW 2 — TRIAGEM/SCREENING WSI

```
CAMINHOS DE ENTRADA:
  A) Chat: recruiter digita "triagem automática candidatos vaga X"
     → CascadedRouter T4 regex "triagem" → "cv_screening" → PipelineReActAgent
  B) REST: POST /wsi/screening-pipeline + POST /wsi/interview-graph/sessions (path principal)
  C) Automático: NÃO ENCONTRADO no código — sem automation rule ou webhook trigger explícito

[PATH A — via Chat]
  agent_chat_ws.py → CascadedRouter → "cv_screening" → PipelineReActAgent.process()
  ⚠ PipelineReActAgent.process() chama _process_langgraph() DIRETAMENTE — SEM _fairness_pre_check()
  (contraste: TalentReActAgent tem _fairness_pre_check() em line 135)

[PATH B — WSI Estruturado (path principal)]
  POST /wsi/screening-pipeline → wsi_screening_pipeline_endpoint.py:33
    Auth: get_current_user_or_demo + get_user_company_id (tenant isolation)
    Fetch CompanyScreeningQuestion WHERE company_id=X AND is_active=true
    → WSIScreeningPipeline.build_pipeline(request, company_questions_raw)

[WSIScreeningPipeline.build_pipeline()] wsi_screening_pipeline.py:99
  1. SeniorityResolver: resolve seniority via multi-signal (título+JD+salário+skills)
  2. Distribuição: compact=7q | full=12q
  3. Block 2: company questions (DB CompanyScreeningQuestion)
  4. Block 3: _build_technical_block() → WSIService Bloom/Dreyfus questions
  5. Block 4: _build_behavioral_block() → WSIService Big Five/CBI questions
  6. Rebalancing se total < target
  → WSIScreeningPipelineResponse

[FONTE DE VERDADE — CRITÉRIOS DE TRIAGEM]
  Prioridade em WSIInterviewGraph.load_context():
  1. job_screening_questions DB (recruiter configurou na vaga)
     SELECT * FROM job_screening_questions WHERE job_vacancy_id=:job_id AND is_active=true
     ⚠ SEM filtro company_id — qualquer job_id válido expõe perguntas
  2. WSIScreeningPipeline (fallback — gera via pipeline)
  3. _build_fallback_questions() — 2 questões hardcoded genéricas

[WSIInterviewGraph — State Machine]
  STAGES: INIT → LOAD_CONTEXT → GENERATE_QUESTION → AWAIT_RESPONSE
          → VALIDATE_RESPONSE → SCORE_RESPONSE → ADVANCE → GENERATE_FEEDBACK → COMPLETE

  LOAD_CONTEXT:
    [SEG-4] ConsentCheckerService.check_candidate_consent(purpose="ai_screening")
      → REVOKED → aborta (state.error="LGPD_CONSENT_REVOKED")
      → ABSENT (sem registro) → ⚠ soft warning, prossegue com log

  VALIDATE_RESPONSE:
    [SEG-1] PromptInjectionGuard.check(candidate_response)
    [A3/G1] strip_pii_for_llm_prompt(response) — PII masking antes de scoring
    [A3]    FairnessGuard L2 via fairness_guard_middleware — advisory only

  SCORE_RESPONSE:
    calculate_wsi_deterministic(response_text, competency, "CBI")
    → WSIDeterministicScorer: BARS + Bloom taxonomy + Dreyfus (100% determinístico, sem LLM)
    → PROTECTED_CRITERIA excluídos do scoring
    → audit_service.log_decision("score_candidate", criteria_ignored=PROTECTED_CRITERIA)

  ADVANCE:
    questões restantes → GENERATE_QUESTION  |  completou → HITL GATE

  HITL GATE — interrupt_before="lg_generate_feedback":
    SE __interrupt__ AND NOT hitl_approved:
      hitl_service.request_approval("finalize_wsi_score", {wsi_final_score, technical, behavioral})
      hitl_service.store_resume_info(hitl_context="wsi_finalize_score")
      ⚠ request_approval falha → graph prossegue SEM revisão humana (fail-open line 1057)

  GENERATE_FEEDBACK (após HITL approval):
    calculate_final_wsi_score(technical, behavioral, seniority)
    SENIORITY_WEIGHTS dinâmico: senior → {tech:0.5625, behav:0.4375}
    WSI_CUTOFFS: aprovado≥3.75 | aguardando≥3.0 | reprovado<3.0
    → audit_service.log_decision("wsi_final_evaluation", human_review_required=True)
    → SE reprovado: asyncio.ensure_future(send_gate_feedback()) — fire-and-forget

[DB WRITES — screening]
  ✓ audit_service.log_decision() por bloco + final (BCB 498/SOX)
  ✓ HITL request_approval/store_resume_info gravados
  ⚠ wsi_final_score NÃO gravado diretamente em Candidate.wsi_score pelo graph
     → depende de evento "screening.completed" via platform_event_handlers.py:517
```

**CROSS-CUTTING:**
```
├─ Fairness:  ✓ FairnessGuard L2 em validate_response (advisory)
│             ✓ PROTECTED_CRITERIA excluídos do scoring (determinístico)
│             ⚠ PipelineReActAgent.process() SEM _fairness_pre_check
├─ LGPD:      ✓ ConsentCheckerService em load_context (SEG-4)
│             ⚠ consent ABSENT não bloqueia — soft warning apenas
│             ✓ PII masking antes de scoring (strip_pii_for_llm_prompt)
├─ Bias:      ✓ Scoring 100% determinístico — sem LLM judge, sem dados demográficos
│             ⚠ BiasAuditService não chamado automaticamente ao completar WSI
└─ Error:     ✓ Cada node tem try/except com fallback
              ✓ HITL failure não bloqueia (non-blocking)
              ⚠ Hardcoded fallback questions sem alerta ao recrutador
```

**INTEGRATION VERIFIED:**
```
├─ Agente → Tool:      ✓ PipelineReActAgent → pipeline_tool_registry tools via LangGraph
├─ Tool → Backend:     ✓ WSIInterviewGraph acessa DB diretamente
├─ Backend → Banco:    ⚠ job_screening_questions: SEM company_id filter (wsi_interview_graph.py:350–362)
│                         → qualquer job_id válido expõe perguntas de outra empresa
├─ Backend → Externo:  ⚠ send_gate_feedback() asyncio.ensure_future sem await — fire-and-forget
├─ Banco → Frontend:   ✓ wsi/sessions.py retorna score + recommendation + scores por dimensão
├─ Resultado → Agente: ✓ WSIInterviewState serializado via endpoint + PostgresSaver
├─ Tenant isolation:   ⚠ PARCIAL — endpoint usa company_id ✓, mas load_context usa só job_vacancy_id ✗
└─ Audit trail:        ✓ por bloco + final com human_review_required=True
                       ✓ HITL rejection auditado
                       ⚠ wsi_final_score depende de evento externo para persistência em Candidate
```

**GAPS:**
| ID | Severidade | Descrição | Arquivo:Linha |
|---|---|---|---|
| F2-G1 | 🔴 CRÍTICO | job_screening_questions query sem company_id — cross-tenant data exposure | wsi_interview_graph.py:350–362 |
| F2-G2 | 🟠 ALTO | wsi_final_score não persistido diretamente em Candidate.wsi_score — depende de evento externo | wsi_interview_graph.py:695 |
| F2-G3 | 🟠 ALTO | LGPD soft warning — consent ABSENT não bloqueia, apenas loga | wsi_interview_graph.py:329–333 |
| F2-G4 | 🟠 ALTO | PipelineReActAgent sem _fairness_pre_check — screening via chat não bloqueia inputs discriminatórios no agente | pipeline_react_agent.py:117 |
| F2-G5 | 🟡 MÉDIO | BiasAuditService passivo — adverse impact não detectado automaticamente ao completar WSI | bias_audit_service.py:312 |
| F2-G6 | 🟡 MÉDIO | HITL fail-open — se request_approval falha, graph prossegue sem revisão humana | wsi_interview_graph.py:1057 |
| F2-G7 | 🟡 MÉDIO | C3b post_compliance não aplica a "cv_screening" — respostas de triagem sem FactChecker | c3b_layer.py:17–26 |
| F2-G8 | 🟢 BAIXO | Email fire-and-forget — asyncio.ensure_future sem error callback | wsi_interview_graph.py:752–762 |
| F2-G9 | 🟢 BAIXO | HITL incondicional — interrompe TODOS os candidatos, não apenas casos limítrofes | wsi_interview_graph.py:972 |
| F2-G10 | 🟢 BAIXO | Hardcoded fallback questions sem alerta ao recrutador | wsi_interview_graph.py:428–431 |

---

## FLOW 3 — AVALIAÇÃO COMPORTAMENTAL/TÉCNICA (WSI INTERVIEW ASSÍNCRONO)

```
[Recrutador/Automação]
  → POST /api/v1/automation/execute-action {action_type:"triagem_wsi"}
  → ActivityService.record() + EmailService/WhatsAppService envia convite com link /wsi-async/{token}

[Candidato acessa /wsi-async/{token}]
  → GET /wsi/async/{token} → WSIAsyncSessionService.get_session()
    session_id = f"system:{uuid4()}"
    → Redis (TTL 48h) + PostgreSQL wsi_sessions (best-effort)
  → retorna current_question do estado da sessão

[Candidato responde] → POST /wsi/async/{token}/answer {answer: str}
  → WSIAsyncSessionService.submit_response(session_id, block, question_id, response_text)

[WSIInterviewGraph.start(state)] — LangGraph StateGraph
  Node: lg_load_context
    [SEG-4] ConsentCheckerService.check_candidate_consent(purpose="ai_screening")
      REVOKED → state.stage=ERROR, aborta
      ABSENT → soft_warning, prossegue com log ⚠
    FONTE DE QUESTÕES (prioridade):
      1. job_screening_questions DB (SELECT WHERE job_vacancy_id=:job_id) ← SEM company_id ⚠
      2. WSIScreeningPipeline.build_pipeline() — determinístico, Bloom/Dreyfus calibrado por seniority
      3. 2 questões hardcoded (behavioral + situational)
    → source logado: "saved_db" | "fallback_pipeline" | "hardcoded_fallback"

  Node: lg_generate_question → apresenta WSIQuestionBlock ao candidato

  Node: lg_validate_response
    → FairnessGuard L2 check na resposta do candidato (advisory)
    → PII masking: strip_pii_for_llm_prompt(response) → masked_response em _pending_response
    → stage = SCORE_RESPONSE

  Node: lg_score_response
    → wsi_deterministic_scorer.calculate_wsi_deterministic(masked_response, competency, "CBI")
    SCORING 100% DETERMINÍSTICO (sem LLM):
      TÉCNICO: 0.35*autodeclaração + 0.40*evidence_score + 0.25*bloom_alignment
      COMPORTAMENTAL: 0.35*STAR_structure + 0.40*trait_signals + 0.25*bloom_alignment
      Bloom: keyword matching PT-BR (níveis 1–6)
      Dreyfus: keyword matching (níveis 1–5)
      Penalidades: inflação(-1.0), resp. genérica(-0.5), <20 palavras(-0.3)
      Bônus: humildade(+0.5), evidência excepcional(+0.3)
      Score final: clamped to [1.0, 5.0]
    → AuditService.log_decision("score_candidate", PROTECTED_CRITERIA=ignored, BCB498/SOX)

  Node: lg_advance
    questões_restantes > 0 → lg_generate_question
    else → INTERRUPT before lg_generate_feedback (HITL gate)

[HITL Gate] interrupt_before=["lg_generate_feedback"]
  → hitl_service.request_approval("finalize_wsi_score", {wsi_final_score, technical, behavioral})
  ⚠ se request_approval falha → graph prossegue SEM revisão (fail-open line 1057)
  → hitl_service.store_resume_info(hitl_context="wsi_finalize_score")
  Quando aprovador responde:
    graph.ainvoke(None, config) retoma do checkpoint

[lg_generate_feedback — após HITL]
  → deterministic_final(technical, behavioral, seniority)
    SENIORITY_WEIGHTS: senior→{tech:0.5625, behav:0.4375}; junior→{tech:0.40, behav:0.60}
    WSI_CUTOFFS: aprovado≥3.75, aguardando≥3.0, reprovado<3.0
  → AuditService.log_decision("wsi_final_evaluation", human_review_required=True)
  → SE reprovado: asyncio.ensure_future(send_gate_feedback("gate1_rejected")) ⚠ fire-and-forget
  → state.stage=COMPLETE

[Resultado → Pipeline]
  platform_event_handlers.handle_screening_completed_event()
  → validate_multi_tenancy (multi-tenancy check)
  → WSI_CUTOFFS decision: approved | review | rejected
  → CompanyHiringPolicy.automation_rules["auto_stage_advance"]
  → SE approved + auto_advance: pipeline_stage_service.advance_stage()
  → VacancyCandidate.additional_data atualizado: {screening_decision, wsi_final_score, screening_label, screening_completed_at}
  → WSIFeedbackGenerator → feedback legível para recrutador
  → notification via ActivityService

[PERSISTÊNCIA]
  ✓ WSI state: LangGraph PostgresSaver (thread_id=session_id)
  ⚠ Final scores: VacancyCandidate.additional_data (JSON patch) — NOT wsi_results table (só path de voz)
  ⚠ Naming mismatch: frontend lê `wsi_score` (candidates_metadata.py:541); backend grava `wsi_final_score` → frontend recebe None
  ✓ Audit: por bloco + por sessão via AuditService
```

**CROSS-CUTTING:**
```
├─ Fairness:  ✓ FairnessGuard L2 em validate_response (advisory antes de scoring)
│             ✓ PROTECTED_CRITERIA excluídos de cada log de decisão
│             ✓ Bloom/Dreyfus scoring: sem dados demográficos na fórmula
├─ LGPD:      ✓ ConsentCheckerService em load_context:301–329
│             ✓ PII masking antes de scoring
│             ⚠ Soft warning path: candidato SEM consentimento registrado passa apenas com log
├─ Bias:      ✓ 100% determinístico — sem LLM judge, sem atributos sensíveis
│             ⚠ OCEAN weights default to 1.0 quando F3 indisponível
│             ⚠ SENIORITY_WEIGHTS hardcoded — não calibrado por empresa
└─ Error:     ✓ Cada node tem try/except — falha em score_response loga e avança questão (line 643–645)
              ✓ HITL failure non-blocking (continua sem interrupção)
              ⚠ AuditService failures sempre swallowed (try/except debug log pattern)
```

**INTEGRATION VERIFIED:**
```
├─ Agente → Tool:      ✓ WSIInterviewGraph.start()/submit_response() chamados pela wsi_async API
├─ Tool → Backend:     ✓ WSIAsyncSessionService → Redis + PostgreSQL (best-effort)
├─ Backend → Banco:    ⚠ wsi_results table: INSERT só confirmado em wsi_voice_orchestrator.py:465
│                         Text-WSI scores ficam apenas em VacancyCandidate.additional_data
├─ Backend → Externo:  ✓ PostgresSaver para checkpointing; sem chamadas externas durante scoring
├─ Banco → Frontend:   ⚠ Naming mismatch: wsi_score (frontend) ≠ wsi_final_score (backend dict key)
│                         → campo pode ser None no frontend
├─ Resultado → Agente: ✓ handle_screening_completed_event recebe wsi_final_score via PlatformEvent.payload
├─ Tenant isolation:   ✓ validate_multi_tenancy em platform_event_handlers
│                       ⚠ load_context usa só job_vacancy_id SEM company_id filter
└─ Audit trail:        ✓ por bloco + por sessão
                       ⚠ AuditService failures silenciosamente swallowed
```

**GAPS:**
| ID | Severidade | Descrição | Arquivo:Linha |
|---|---|---|---|
| F3-G1 | 🔴 CRÍTICO | job_screening_questions sem company_id — mesma falha de F2-G1 | wsi_interview_graph.py:350–362 |
| F3-G2 | 🔴 CRÍTICO | HITL fail-open — se request_approval falha, graph prossegue sem revisão humana | wsi_interview_graph.py:1057 |
| F3-G3 | 🟠 ALTO | wsi_results table não escrita no text-WSI path — scores ficam só em JSON adicional de VacancyCandidate | wsi_voice_orchestrator.py:465 vs wsi_interview_graph.py:695 |
| F3-G4 | 🟠 ALTO | Naming mismatch: frontend lê wsi_score, backend grava wsi_final_score → campo None | candidates_metadata.py:541 |
| F3-G5 | 🟠 ALTO | LGPD soft-warning — candidato sem consentimento registrado não é bloqueado | wsi_interview_graph.py:337–343 |
| F3-G6 | 🟡 MÉDIO | Stage advance não disparado para decisão "review" — recrutador não notificado sobre revisão manual necessária | platform_event_handlers.py:563 |
| F3-G7 | 🟡 MÉDIO | asyncio.ensure_future sem await para email de rejeição — fire-and-forget, email pode ser perdido | wsi_interview_graph.py:748–760 |

---

## FLOW 4 — COMUNICAÇÃO COM CANDIDATO (WhatsApp/Email)

```
[TRIGGER — uma de 3 origens:]
  A) POST /api/v1/automation/execute-action {action_type:"email"|"whatsapp"}
  B) TransitionDispatchService.dispatch_for_transition(action_behavior, to_stage)
  C) CommunicationReActAgent.process(AgentInput) — via chat IA

PATH A — execute-action DIRETO (triggers.py:252–380):
  → channel=email → EmailService.send_email()
  → channel=whatsapp → WhatsAppService.send_message()
  ✗ SEM validate_can_send()
  ✗ SEM CandidateOptOut check
  ✗ SEM FairnessGuard
  ✗ SEM audit record

PATH B — TransitionDispatchService:
  → CommunicationMatrixEntry(trigger_name, company_id)
    → is_active=False → skip
    → requires_approval=True → LOG ONLY, NÃO BLOQUEIA ⚠ (enforcement pending)
  → CandidateChannelSelector.select_channels(candidate_id, company_id, channels, message_type)
    1. candidate.preferred_channels
    2. minus CandidateOptOut (opt-out explícito)
    3. minus canais sem LGPD consent (para "marketing" only)
    4. intersect com requested_channels
    5. fallback: ["email"]
  → CommunicationDispatcher._dispatch_single_channel()
    → email → CommunicationDispatcher.send_email() [REAL — chama Mailgun/Resend]
    → whatsapp → CommunicationDispatcher.send_whatsapp() [REAL — chama Twilio]

PATH C — CommunicationReActAgent (via chat):
  → FairnessGuard.check(input.message)
  → SE message_type in {initial_contact, rejection_feedback, offer_letter} AND NOT hitl_approved:
    → hitl_service.request_approval("send_communication")
    → AuditService.log_decision("pending_review", LGPD Art.7)
    → retorna "Aguardando aprovação" — NÃO envia
  → SE hitl_approved → LangGraph ReAct → communication tools
  ✗✗ CRITICAL BUG: communication_tools.send_email() (tool do ReAct agent) NUNCA chama
     CommunicationDispatcher — retorna {simulated: True} após apenas lookup no DB
     (communication_tools.py:104 — send_email, line:195 — send_whatsapp)
     → agente acredita que email/WhatsApp foi enviado; nenhuma entrega ocorre

[CommunicationDispatcher.send_email()] — PATH B apenas (o correto):
  → verifica MAILGUN_CIRCUIT (circuit breaker)
  → SE MAILGUN_API_KEY + MAILGUN_DOMAIN: httpx.Client.post() → Mailgun API
    → sucesso: {provider:"mailgun", message_id, mock:False}
    → falha: tenta Resend como fallback
  → SE RESEND_API_KEY: resend_sdk.Emails.send()
  → SE nenhum provider: PRODUÇÃO → {success:False, error:"No email provider"}

[LGPD CHECKS — PATH B/C]:
  → CommunicationService.validate_can_send():
    1. CandidateOptOut check
    2. CandidateQuarantine (cooling-off 90 dias)
    3. Rate limit (MAX_MESSAGES_PER_DAY=3)
    4. Horário de envio (8h–20h, dias úteis, UTC-3)
  ✗ PATH A bypassa TODOS esses checks

[RETRY LOGIC] CommunicationService._send_with_retry():
  MAX_RETRIES=3, BASE_DELAY=60s, exponential backoff + jitter
  providers: [Mailgun, Resend, Mock] email | [Twilio, WhatsAppBusiness, Mock] WA
  Fora do horário → QUEUED (next_retry_at set)

[WEBHOOK — STATUS] Mailgun:
  POST /webhooks/mailgun → HMAC-SHA256 verificado + timestamp replay 300s
  → CommunicationLog updated: delivered | failed | read
  ✗ WhatsApp: SEM endpoint /webhooks/twilio — status callbacks Twilio ignorados
     CommunicationLog permanece status="sent" independente da entrega real
```

**CROSS-CUTTING:**
```
├─ Fairness:  ✓ FairnessGuard.check() em PATH C (ReAct agent)
│             ✗ PATH A e PATH B SEM FairnessGuard em conteúdo da mensagem
├─ LGPD:      ✓ validate_can_send(): opt-out + quarantine + rate-limit (PATH B/C)
│             ✓ CandidateChannelSelector: LGPD consent para marketing (PATH B)
│             ✗ PATH A bypassa TODOS os checks LGPD
│             ✓ data_request_whatsapp_service: consentimento explícito antes de coleta de dados
├─ Bias:      ✗ Conteúdo do template não é verificado em PATH A ou PATH B
└─ Error:     ✓ Mailgun: circuit breaker + Resend fallback + retry exponencial
              ✓ WhatsApp: TwilioRestException capturada, logada
              ✗ Sem cross-channel failover (WhatsApp falha → sem fallback para email)
              ✗ requires_approval=True não bloqueia — log only
```

**INTEGRATION VERIFIED:**
```
├─ Agente → Tool:      ✗ CRITICAL BUG — communication_tools.send_email/send_whatsapp retornam
│                         simulated=True sem chamar CommunicationDispatcher (communication_tools.py:104, 195)
├─ Tool → Backend:     ✗ mesmo bug — nenhuma chamada real ao EmailService ou Twilio
├─ Backend → Banco:    ✓ CommunicationLog persistido (status PENDING → SENT/FAILED via webhook)
├─ Backend → Externo:  ✓ CommunicationDispatcher REAL chama Mailgun/Resend/Twilio (PATH B direto)
├─ Banco → Frontend:   ✓ CommunicationLog legível via communication_history_service
├─ Resultado → Agente: ⚠ ReAct agent recebe sucesso simulado — acredita que mensagem foi enviada
├─ Tenant isolation:   ✓ company_id scoped em todas as queries de CommunicationLog
└─ Audit trail:        ✓ CommunicationLog + AuditService no HITL
                       ✗ PATH A sem nenhum audit record
```

**GAPS:**
| ID | Severidade | Descrição | Arquivo:Linha |
|---|---|---|---|
| F4-G1 | 🔴 CRÍTICO | communication_tools.send_email/send_whatsapp retornam simulated=True — nenhuma entrega real via PATH C | communication_tools.py:60–115, 120–200 |
| F4-G2 | 🔴 CRÍTICO | PATH A bypassa todos os checks LGPD (opt-out, consent, quarantine, rate-limit) | triggers.py:252–380 |
| F4-G3 | 🟠 ALTO | requires_approval=True não bloqueante — TransitionDispatchService loga e despacha mesmo assim | transition_dispatch_service.py:~130 |
| F4-G4 | 🟠 ALTO | Sem webhook handler Twilio — CommunicationLog WhatsApp permanece "sent" sem confirmação real | (ausente em webhooks/) |
| F4-G5 | 🟠 ALTO | Sem cross-channel failover — falha no WhatsApp não tenta email como fallback | communication_service.py providers list |
| F4-G6 | 🟡 MÉDIO | FairnessGuard ausente em PATH A e PATH B — conteúdo discriminatório pode ser enviado | triggers.py:252–380 |
| F4-G7 | 🟡 MÉDIO | Template A/B testing ausente — template_learning_service registra mas sem split-test routing | template_learning_service.py |

---

## FLOW 5 — AGENDAMENTO DE ENTREVISTA

```
[WS msg] "agenda entrevista com João para amanhã às 14h"
  → agent_chat_ws.py:/ws/chat/{session_id}?domain=recruiter_assistant

[SEG LAYER]
  → PromptInjectionGuard + check_input_security + FairnessGuard + pre_compliance

[CascadedRouter.route()]
  T4 FastRouter: r"agendar?\b" → domain="interview_scheduling", conf≈0.85

[ATENÇÃO — DOIS CAMINHOS POSSÍVEIS:]
  ⚠ VIA WS DIRETA: "interview_scheduling" NÃO está no AgentRegistry (_ensure_agents_loaded)
     → InterviewGraph NÃO é @register_agent("interview_scheduling")
     → AgentRegistry.get_or_fallback → "talent" (TalentReActAgent) — CAMINHO ERRADO

  ✓ VIA CORRETO: MainOrchestrator → Orchestrator.process_request → DomainRegistry
     → InterviewSchedulingDomain.process_intent("agenda entrevista...")
     → KeywordIntentMatcher → IntentResult(action_id="schedule_interview")
     → InterviewSchedulingDomain.execute_action("schedule_interview")
       → _GRAPH_ACTIONS check → _run_interview_graph() [domain.py:561]

[InterviewGraph.invoke(state)] interview_graph.py:183
  → StateGraph.ainvoke(state, config={thread_id:session_id})
  → PostgresSaver checkpointer

  Node 1: interview_state_loader
    → cria/carrega InterviewSchedulingState de workflow_data
    → current_workflow = "interview_scheduling"

  Node 2: interview_details_collector
    [SEG-2] FairnessGuard.check(last_message) — se blocked → fairness_blocked=True, exit
    FairnessGuard.check_implicit_bias() → soft warnings
    → LLM call via get_provider_for_tenant()
      ⚠ chamado SEM company_id → usa provider do sistema, NÃO o LLM do tenant (viola "Choose Your AI")
    → JSON extraído: {candidate_name, preferred_date, preferred_time, candidate_email, interviewer_email, job_title, interview_type}
    → "amanhã" → próximo dia calendário
    → confidence_score baseado em progresso

  LOOP — CAMPOS OBRIGATÓRIOS (7 no total):
    candidate_name, candidate_email, job_title, interview_type,
    interviewer_email, preferred_date, preferred_time
    [interview_scheduling_nodes.py:305–316]
    → MAX_ITERATIONS=8 ciclos conversacionais

  Node 3: interview_router
    → _lg_route_router: se pending → RESPONSE (pergunta ao usuário, espera próximo WS message)
    → cada campo faltando = 1 turno conversacional

  Node 4: interview_validator
    → validate_completeness() — apenas presença dos 7 campos
    ✗ SEM verificação de conflito de calendário
    ✗ SEM verificação de horário comercial

  Node 5: interview_scheduler_executor
    → calendar_service.schedule_interview(...)
      → _get_client(company_id=None, db=None) ← ⚠ company_id NÃO passado
        → SEMPRE retorna app-level MS Graph client
        → Google Calendar e delegated OAuth NUNCA atingidos
      → client.create_calendar_event(organizer_email, attendees, is_online_meeting)
        → candidato + entrevistadores recebem convite via MS Graph API
        → SE as_teams_meeting=True: link Teams gerado
    → Interview DB record criado
      ⚠ company_id NÃO setado no registro (field é nullable) [nodes.py:356–389]

  Node 6: interview_response_planner
    → "Entrevista agendada! Confirmação enviada para {email}"
    ✗ Sem WhatsApp notification separada
    ✗ send_interview_invitation tool (scheduling_tools.py:87) é STUB — apenas loga

[CONFLICT HANDLING]:
  → MS Graph API erro HTTP → caught → workflow_data["interview_scheduling_error"]=str(e)
  → interview_response_planner: status=error com raw error message
  ✗ Sem slot alternativo proposto
  ✗ Sem retry logic

[AUDIT]
  ✓ audit_service.log_decision() no sucesso e no erro (BCB498/SOX)
```

**CROSS-CUTTING:**
```
├─ Fairness:  ✓ FairnessGuard na entrada WS (SEG-3) + dentro de interview_details_collector (SEG-2)
├─ LGPD:      ⚠ candidate_email gravado em plain text em Interview record
│             ⚠ company_id nullable → interview sem isolamento multi-tenant no DB
├─ Bias:      ✓ FairnessGuard bloqueia critérios discriminatórios para agendamento
└─ Error:     ⚠ Conflito retorna erro bruto, sem alternativa — UX degradada
              ✓ DB rollback tentado em caso de falha na escrita
```

**INTEGRATION VERIFIED:**
```
├─ Agente → Tool:      ✓ InterviewGraph → calendar_service.schedule_interview()
├─ Tool → Backend:     ✓ calendar_service → MS Graph API (create_calendar_event)
├─ Backend → Banco:    ✓ Interview model escrito via SQLAlchemy async session
├─ Backend → Externo:  ✓ MS Graph API chamado; Google Calendar reachable mas bypassed
├─ Banco → Frontend:   ⚠ Sem panel_update emitido — resposta é texto puro apenas
├─ Resultado → Agente: ✓ workflow_data["response_data"] → DomainResponse
├─ Tenant isolation:   ⚠ Interview record: company_id nullable, NÃO setado pelo executor
│                         calendar usa credenciais app-level (não per-tenant)
└─ Audit trail:        ✓ audit_service.log_decision() no sucesso e no erro
```

**GAPS:**
| ID | Severidade | Descrição | Arquivo:Linha |
|---|---|---|---|
| F5-G1 | 🔴 CRÍTICO | company_id não passado para calendar_service → sempre usa app-level MS Graph, nunca Google Calendar ou delegated OAuth | interview_scheduling_nodes.py:345 |
| F5-G2 | 🔴 CRÍTICO | Interview DB record sem company_id — viola isolamento multi-tenant | interview_scheduling_nodes.py:357–391 |
| F5-G3 | 🟠 ALTO | Sem verificação de disponibilidade antes de agendar — check_interviewer_availability() existe mas nunca chamado | calendar_service.py:276 |
| F5-G4 | 🟠 ALTO | get_provider_for_tenant() sem tenant_id → LLM de sistema, não do tenant ("Choose Your AI" violado) | interview_scheduling_nodes.py:215 |
| F5-G5 | 🟡 MÉDIO | "interview_scheduling" não registrado no AgentRegistry — se chegar diretamente via WS sem passar pelo MainOrchestrator, cai no fallback "talent" | agent_chat_ws.py:_ensure_agents_loaded |
| F5-G6 | 🟡 MÉDIO | send_interview_invitation tool é STUB — nenhuma notificação WhatsApp/email transacional enviada ao candidato | scheduling_tools.py:87 |
| F5-G7 | 🟢 BAIXO | HITL não implementado para agendamento — workflow_data["hitl_pending"] logado mas nunca setado | interview_graph.py (audit path) |

---

## FLOW 6 — CHAT LIVRE DO RECRUTADOR (KANBAN INSIGHT)

```
[WS msg] "quais candidatos desta vaga têm maior risco de dropout?"
  → agent_chat_ws.py:/ws/chat/{session_id}?domain=recruiter_assistant

[SEG LAYER]
  → PromptInjectionGuard + check_input_security + FairnessGuard + pre_compliance
  → "dropout" não dispara nenhum padrão → passa

[CascadedRouter.route()]
  T0 MemoryResolver: "desta vaga" → tenta resolver job_id do session context
  T1 LRU: MISS
  T2 Redis: MISS
  T3 VectorSemanticCache: MISS (primeiro acesso)
  T4 FastRouter:
    r"candidatos?\s+em\s+risco" → "kanban_insight" — NÃO MATCH para "dropout"
    "dropout" sem regex no FastRouter → MISS ou low-confidence
  T5 LLM Cascade:
    Gemini Flash (LLM_FAST_MODEL): classifica "dropout" → domain="kanban_insight", conf≈0.82–0.88
    SE conf >= 0.80 → retorna resultado (sem escalar para Sonnet)
  → result salvo em LRU + Redis para futuras queries idênticas

[DISPATCH]
  active_domain = "kanban_insight"
  → AgentRegistry.get_or_fallback("kanban_insight")
  → KanbanInsightAgent (registrado via @register_agent("kanban_insight"))

[KanbanInsightAgent.process()] LangGraphReActBase
  → create_react_agent com PostgresSaver checkpoint (thread_id=session_id)
  → system_prompt: KanbanReActAgent DOMAIN_INSTRUCTIONS + ANALYTICS_DOMAIN_SPECIFIC
  → conversation_history: WS local list [-10 msgs] ← NÃO é o DB ConversationMemory (20 msgs)
    ⚠ Dois stores diferentes — reconexão WS perde contexto local

  TOOLS: analyze_stage, identify_bottlenecks, get_candidate_aging, compare_stages,
         suggest_movements, get_journey_metrics, get_at_risk_candidates, get_pipeline_prediction

  ReAct Step 1 — Tool selection:
    "risco de dropout" → get_at_risk_candidates(company_id=company_id, min_risk_level="medium")
    → early_warning_service.get_at_risk_candidates(company_id, "medium")
      SQL: JOINs vacancy_candidates + candidates + job_vacancies
           WHERE jv.company_id = :company_id ✓ (tenant isolation via SQL)
           LEFT JOIN communication_logs for last_contact_at
      EWS score = f(days_since_contact, stage, lia_score)
      → top 15 candidatos sorted by ews_score DESC
    ⚠ get_at_risk_candidates NÃO aceita job_id filter
      → retorna TODOS em risco da empresa, não filtrado pela vaga mencionada

  ReAct Step 2 (se job_id no contexto):
    ⚠ "desta vaga" contexto: só disponível se WS client explicitamente enviou context.job_id
    → sem filtro por job, resposta pode ser incorreta/enganosa

[RESPOSTA]
  → _strip_react_json(output.message)
  → post_compliance(clean_message, _c3b_ctx)
  → conversation_history.append(user + assistant)
  ⚠ KanbanInsightAgent NÃO emite panel_update → resposta é texto puro apenas
  → ws_mgr.send_to_session(serialize_message(content, confidence≈0.75–0.82, domain="kanban_insight"))

[TOKEN STREAMING]
  ✗ NÃO implementado — thinking events chegam durante ReAct iterations
  Texto final chega de uma vez (não token-by-token)
```

**CROSS-CUTTING:**
```
├─ Fairness:  ✓ FairnessGuard na entrada WS
│             ✓ check_rejection_fairness tool disponível (não chamado neste flow)
├─ LGPD:      ⚠ candidate_name retornado em resposta sem anonimização
│             ⚠ EWS score derivado de last_contact_at (dado comportamental)
├─ Bias:      ✓ EWS usa critérios objetivos (dias, stage, lia_score)
│             ⚠ lia_score pode carregar viés do modelo de screening
└─ Error:     ✓ asyncio.wait_for timeout → serialize_error enviado
              ⚠ get_at_risk_candidates SQL failure → retorna [] silenciosamente
```

**INTEGRATION VERIFIED:**
```
├─ Agente → Tool:      ✓ KanbanInsightAgent → get_at_risk_candidates()
├─ Tool → Backend:     ✓ early_warning_service.get_at_risk_candidates() com DB session
├─ Backend → Banco:    ✓ SQL com company_id filter (tenant isolation) ✓
├─ Backend → Externo:  N/A (sem chamadas externas neste flow)
├─ Banco → Frontend:   ⚠ texto puro apenas — sem panel_update, sem structured data para Kanban
├─ Resultado → Agente: ✓ tool result → LLM synthesis → AgentOutput.message
├─ Tenant isolation:   ✓ jv.company_id = :company_id no SQL
└─ Audit trail:        ✗ Nenhum audit_service.log_decision() para queries analíticas
```

**GAPS:**
| ID | Severidade | Descrição | Arquivo:Linha |
|---|---|---|---|
| F6-G1 | 🟠 ALTO | get_at_risk_candidates não filtra por job_id — "desta vaga" retorna todos em risco da empresa | early_warning_service.py:98–157 |
| F6-G2 | 🟠 ALTO | Histórico de conversa duplo e inconsistente — WS local (10 msgs) vs DB ConversationMemory (20 msgs) | agent_chat_ws.py:845 vs main_orchestrator.py:853 |
| F6-G3 | 🟠 ALTO | "dropout" sem regex no T4 FastRouter → sempre LLM Cascade (latência + custo desnecessários) | fast_router.py:199–216 |
| F6-G4 | 🟡 MÉDIO | Sem panel_update — lista de candidatos em risco retornada como texto puro | analytics_react_agent.py:_state_to_output |
| F6-G5 | 🟡 MÉDIO | Token streaming não implementado — usuário espera resposta completa | agent_chat_ws.py |
| F6-G6 | 🟡 MÉDIO | Sem audit trail para queries analíticas — quem perguntou, quando, quais candidatos retornados | analytics_tool_registry.py |
| F6-G7 | 🟢 BAIXO | LIA score na EWS pode carregar viés do modelo de screening | early_warning_service.py:182 |

---

## FLOW 7 — CRIAÇÃO/CONFIGURAÇÃO DE VAGA

```
[WS msg] "criar nova vaga para Engenheiro de Software Sênior"
  → agent_chat_ws.py → CascadedRouter

[CascadedRouter]
  T4 FastRouter: r"criar?\s+\w*\s*vaga" | r"\bvaga\b" → domain="job_management", conf≈0.90
  → active_domain = "job_management"
  → AgentRegistry.get("wizard") → WizardReActAgent

[DUAS IMPLEMENTAÇÕES PARALELAS — ATENÇÃO:]
  | Endpoint/Caminho                | Agente usado        |
  |-------------------------------|---------------------|
  | WS (agent_chat_ws.py)         | WizardReActAgent ✓  |
  | POST /wizard/react-orchestrate | WizardReActAgent (USE_REACT_AGENTS=true) ou JobWizardGraph |
  | POST /wizard/smart-orchestrate | JobWizardGraph (USE_REACT_AGENTS default=false) |
  | Background tasks              | WizardReActAgent    |
  USE_REACT_AGENTS default=false → REST usa JobWizardGraph; WS sempre usa WizardReActAgent

[WizardReActAgent.process()] wizard_react_agent.py
  → _fairness_pre_check(message) — FairnessGuard upfront block ✓
  → _process_langgraph(input) — LangGraph native ReAct
    stage = "input-evaluation" (from context["current_stage"])
    LLM: claude-sonnet-4-6

[6 STAGES DO WIZARD] stage_context.py:STAGE_DEFINITIONS
  1. input-evaluation: coleta title, department (req), + seniority, location, work_model, contract_type (opt)
  2. jd-enrichment: enriquece responsibilities, benefits, description, requirements
  3. salary: coleta salary_min, salary_max, currency, type
  4. competencies: skills (req), behavioral_competencies, certifications, education_level (opt)
  5. wsi-questions: screening_questions, eliminatory_questions
  6. review-publish: summary + confirmação

[STAGE 1 — LLM EXTRACTION]
  LLM (claude-sonnet-4-6) recebe system_prompt com stage_context injetado
  → Intent: START_FROM_SCRATCH | USE_EXISTING | PROVIDE_INFO | CONFIRM | SKIP | ...
  → Extração: title="Engenheiro de Software Sênior", seniority="Sênior" (inferido)
  → Campos faltando: department (req), location, work_model (opt)
  → Agente responde conversacionalmente — nunca pergunta tudo de uma vez

[STAGE 2 — JD ENRICHMENT]
  WizardReActAgent chama generate_enriched_jd tool automaticamente
  → JdEnrichmentService:
    MarketBenchmarkService → SerpAPI (SERP_API_KEY) | LLM fallback
    SkillsCatalogService — catálogo interno curado
    ResponsibilitiesCatalogService — catálogo por área
    CompanyConfigurationService — defaults + benefícios da empresa
    ATSJobHistoryService — histórico da empresa no DB
  → EnrichmentResponse: responsibilities + technical_skills + behavioral_competencies + compensation
    cada sugestão: {source: market_data|company_history|skills_catalog|ai_generated}

[SALARY BENCHMARK]
  Layer 1: SQL em job_vacancies (AVG salary_range por title + department)
  Layer 2: SerpAPI → glassdoor.com.br, linkedin.com, indeed.com.br, catho.com.br, vagas.com.br
    → parse via LLM → salary range estruturado
    Cache: 24h in-memory TTL
  Fallback estático: _SALARY_FALLBACK dict por seniority (ex: senior → R$12k–22k)
  Confidence: "high" (SerpAPI) | "medium" (LLM estimate) | "low" (static fallback)

[COMPETÊNCIAS]
  SkillsCatalogService.suggest_skills(role, seniority, limit=15) — catálogo interno
  SkillsCatalogService.get_behavioral_competencies_for_role(job_title) — catálogo interno
  LLM assist: apenas se catálogo não cobre a função (source="ai_generated")

[HITL — JobWizardGraph path apenas]
  interrupt_before=["stage_transition"]
  Trigger: intent==WizardIntent.CONFIRM AND NOT hitl_approved
  Aprovador aprova: {action:"create_job", job_title, company_id, fields}
  ⚠ hitl_service.request_approval() falha → wizard continua SEM aprovação (fail-open)
  WizardReActAgent path: HITL não confirmado como implementado

[PUBLISH — POST /job-vacancies/{job_id}/publish]
  → job_vacancies.status = "Ativa" (PostgreSQL)
  → job_audit_service.log_publication()
  → event_dispatcher.on_job_status_changed()
  → SE trigger_sourcing=True: sourcing_pipeline_service.run_post_publish_sourcing()
  ✗ ATS sync (Gupy/Pandapé) NÃO disparado no publish — apenas em evento de offer

[LEARNING LOOP — PARCIALMENTE WIRED]
  → capture_wizard_feedback() registra: suggested vs. used, explicitly_rejected
  → wizard_feedback table (company_id, role, field_corrected, created_at)
  → IntelligentDataOrchestrator + LearningPatternsRepository
  ⚠ get_intelligent_salary e get_intelligent_skills registrados mas AUSENTES do STAGE_TOOLS dict
    → feedback capturado mas sugestões inteligentes não chegam ao WizardReActAgent em produção
```

**CROSS-CUTTING:**
```
├─ Fairness:  ✓ PROATIVO — _fairness_pre_check() na entrada (wizard_react_agent.py:114)
│             ✓ FairnessGuard.check() + check_implicit_bias() + check_semantic() em validate_job_requirements
│             ✓ System prompt enumera critérios proibidos com citações legais
├─ LGPD:      ✓ System prompt proíbe CPF/dados sensíveis em requisitos
│             ✓ wizard_feedback table sem PII além de company_id/role
├─ Bias:      ✓ Bias explícito: bloqueado + mensagem educativa com citação legal
│             ✓ Bias implícito: soft warning
│             ✓ Bias semântico: check_semantic via Claude
└─ Error:     ✓ Tool wrappers com graceful fallback
              ⚠ HITL failure não bloqueia (fail-open)
              ✓ LangGraph state["error"] capturado — mensagem genérica ao usuário
```

**INTEGRATION VERIFIED:**
```
├─ Agente → Tool:      ✓ WizardReActAgent → get_wizard_tools() → ToolDefinition list → LangGraph
├─ Tool → Backend:     ✓ save_job_draft → DB INSERT/UPDATE job_vacancies
├─ Backend → Banco:    ✓ AsyncSessionLocal(); wizard_feedback + learning_patterns tables confirmados
├─ Backend → Externo:  ⚠ SerpAPI para salary (requer SERP_API_KEY; LLM fallback sem dados reais)
├─ Banco → Frontend:   ✓ JobWizardState via API response; Redis para persistência mid-session
├─ Resultado → Agente: ✓ tool_results → LangGraph state → response_generator
├─ Tenant isolation:   ✓ company_id obrigatório em todos os tool calls; SQL filtra por company_id
└─ Audit trail:        ✓ job_audit_service.log_publication(); HITL request_approval() com thread_id
```

**GAPS:**
| ID | Severidade | Descrição | Arquivo:Linha |
|---|---|---|---|
| F7-G1 | 🟠 ALTO | Duas implementações paralelas (JobWizardGraph + WizardReActAgent) — comportamento divergente entre REST e WS | wizard_smart_orchestrator.py:611–615, agent_chat_ws.py:339 |
| F7-G2 | 🟠 ALTO | Learning loop não wired ao STAGE_TOOLS — get_intelligent_salary/skills capturados mas nunca surfaceados para o agente | wizard_tool_registry.py:STAGE_TOOLS, job_wizard_tools.py:1141–1148 |
| F7-G3 | 🟠 ALTO | ATS sync não disparado no publish da vaga — apenas em evento de offer | lifecycle.py:128–136, handlers_lifecycle.py:795 |
| F7-G4 | 🟡 MÉDIO | HITL fail-open — se request_approval() falha, wizard cria vaga sem aprovação humana | job_wizard_graph.py:322–327 |
| F7-G5 | 🟡 MÉDIO | SerpAPI ausente → salary benchmark usa estimativa LLM sem dado real; sem alerta claro ao recrutador | market_benchmark_service.py:115–120 |
| F7-G6 | 🟡 MÉDIO | generate_enriched_jd pode ser chamado duas vezes (system prompt instrui + JobWizardGraph pode chamar novamente) | wizard_system_prompt.py, wizard_smart_orchestrator.py:506 |

---

## FLOW 8 — RELATÓRIOS E ANALYTICS

```
CENÁRIO A: "qual o tempo médio de contratação para vagas de tech?"
CENÁRIO B: "gera relatório completo da vaga X"

[CENÁRIO A — ROUTING]
  T4 FastRouter:
    r"m[ée]trica" | r"kpi" | r"dashboard" — NENHUM match para "tempo médio de contratação"
    ✗ "tempo médio" NÃO está nos patterns de analytics
    → cai no T5 LLM Cascade (Gemini Flash → Sonnet)
    → LLM mapeia → domain_id="analytics"

[CENÁRIO B — ROUTING]
  T4 FastRouter: r"gerar?\s+relat[óo]rio" ✓ MATCH → domain="analytics", source="fast_router"

[AnalyticsReActAgent.process()] LangGraphReActBase
  → create_react_agent com LangGraph + PostgresSaver
  → system_prompt: LGPD-safe, nunca expõe CPF/dados sensíveis

[TOOLS DISPONÍVEIS] analytics_tool_registry.py
  | Tool                     | Serviço chamado                          | Tabelas        |
  |--------------------------|------------------------------------------|----------------|
  | get_job_insights         | JobInsightsService (SQL)                 | job_vacancies  |
  | predict_hiring_metrics   | PredictiveAnalyticsService (heurística)  | job_vacancies  |
  | generate_job_report      | JobReportService + PredictiveAnalytics   | job_vacancies, candidates, interviews |
  | generate_candidate_report| CandidateReportService.generate_parecer()| candidates     |
  | get_search_analytics     | SearchAnalyticsService + SQL             | candidates ⚠PII|
  | get_agent_performance    | AgentMonitoringService                   | monitoring     |

[CENÁRIO A — EXECUÇÃO]
  THOUGHT: "TTF médio para tech → get_job_insights"
  ACTION: get_job_insights(job_title="tech", company_id=<ctx>)
    → JobInsightsService.get_time_to_fill(db, company_id, role="tech")
      SQL: SELECT from job_vacancies WHERE company_id=X AND title ILIKE patterns
           Python statistics.mean() e statistics.median() sobre rows retornadas
      Confidence: "high" ≥20 samples | "medium" ≥10 | "low" >0 | "none" = 0
  RESPONSE: texto formatado com TTF + recomendação

[CENÁRIO B — EXECUÇÃO]
  THOUGHT: "Relatório completo → generate_job_report"
  ACTION: generate_job_report(job_id="X", company_id=<ctx>, include_predictions=True)
    → JobReportService._get_funnel_data(job_uuid, db)      — pipeline por stage
    → JobReportService._get_source_analysis(job_uuid, db)  — candidatos por canal
    → JobReportService._get_time_metrics(job_uuid, db)     — tempo médio por stage
    → PredictiveAnalyticsService.predict_time_to_fill(job_id, db) — heurística pura
  RESPONSE: JSON dict formatado em texto pelo LLM → chat apenas
  ✗ Sem PDF, sem HTML, sem download

[PREDICT_HIRING_METRICS — HEURÍSTICA PURA, SEM ML]
  predictive_analytics_service.py:182–277
  base_days = {junior:25, pleno:35, senior:50, lead:60, manager:70, director:90, "c-level":120}
  ajustes: skills_rarity × 20 + salary_competitive × 15 - pipeline_strength × 15
  market_factor = 1.0 HARDCODED (sempre "Normal" — sem dado real de mercado)
  range: predicted_days × 0.7 (otimista) ... × 1.5 (pessimista)

[FAIRNESS — AUSENTE NO ANALYTICS AGENT]
  FairnessReportRepository existe + endpoint /api/v1/fairness-reports funcional
  ✗ AnalyticsReActAgent NÃO tem get_fairness_metrics na registry
  ✗ generate_job_report NÃO inclui fairness/diversidade
  ✗ Recrutador NÃO consegue perguntar sobre métricas de equidade via chat

[DASHBOARD vs CHAT]
  Panel update: SE AgentOutput.metadata["panel_update"] setado → send_panel_update() no WS
  ✗ AnalyticsReActAgent NUNCA seta metadata["panel_update"]
  → todo output analytics vai para CHAT ONLY
  → dashboard panels servidos via REST /api/v1/dashboard_data.py
  ✗ dashboard_data.py:7 — comment confirma: "fictitious data for visualization" — MOCK DATA

[CACHE]
  MarketBenchmarkService: 24h in-memory TTL por query key (MD5 role/seniority/location)
  CascadedRouter: LRU + Redis para rota (não para resultados de analytics)
  Analytics tool results: NÃO cacheados — SQL fresh a cada chamada

[GET_SEARCH_ANALYTICS — RISCO LGPD]
  analytics_tool_registry.py:163–178
  SQL queries candidates table: name, email, phone, location
  PII fetchado e depois descartado — data minimization risk (LGPD Art.6 VI)
```

**CROSS-CUTTING:**
```
├─ Fairness:  ✗ Ausente no analytics agent — não tem get_fairness_metrics tool
│             Dados de fairness existem em /api/v1/fairness-reports mas não wired ao agente
├─ LGPD:      ✓ System prompt: nunca expõe CPF/dados sensíveis
│             ✓ get_search_analytics retorna campos agregados/não-PII no output final
│             ⚠ get_search_analytics faz fetch de PII da tabela candidates antes de descartar
├─ Bias:      ✗ Sem análise de disparate impact nos agregados de analytics
│             ✗ TTF por role, taxas de conversão — sem breakdowns demográficos
└─ Error:     ✓ AnalyticsReActAgent.process() com outer try/except → generic error
              ✓ Tool wrappers retornam {success:False} em falha
              ⚠ confidence cai para 0.40 em state["error"] (analytics_react_agent.py:90)
```

**INTEGRATION VERIFIED:**
```
├─ Agente → Tool:      ✓ AnalyticsReActAgent → get_analytics_tools() + _get_all_enhanced_tools() → LangGraph
├─ Tool → Backend:     ✓ Todos os tools instanciam service classes com DB session async
├─ Backend → Banco:    ✓ AsyncSessionLocal(); job_vacancies, candidates, interviews
├─ Backend → Externo:  ✓ MarketBenchmarkService → SerpAPI (se chave presente)
├─ Banco → Frontend:   ⚠ Resultados vão para chat text only — sem panel_update, sem widget de dashboard
├─ Resultado → Agente: ✓ Tool results como ToolMessage → LangGraph messages → LLM synthesis
├─ Tenant isolation:   ✓ company_id obrigatório em todos os tool calls; SQL filtra por company_id
└─ Audit trail:        ✗ Nenhum audit_service.log_decision() para queries analíticas
```

**GAPS:**
| ID | Severidade | Descrição | Arquivo:Linha |
|---|---|---|---|
| F8-G1 | 🟠 ALTO | "tempo médio de contratação" não tem regex no T4 FastRouter → sempre LLM Cascade (latência + custo) | fast_router.py:271–282 |
| F8-G2 | 🟠 ALTO | Fairness não wired ao analytics agent — recrutador não consegue perguntar sobre equidade/diversidade via chat | analytics_tool_registry.py (tool ausente) |
| F8-G3 | 🟠 ALTO | dashboard_data.py serve MOCK DATA — "fictitious data for visualization" confirmado por comment | dashboard_data.py:7 |
| F8-G4 | 🟡 MÉDIO | panel_update nunca emitido pelo analytics agent — resultados chat-only | analytics_react_agent.py:_state_to_output |
| F8-G5 | 🟡 MÉDIO | Sem audit trail para queries analíticas — quem acessou qual relatório, quando | analytics_tool_registry.py |
| F8-G6 | 🟡 MÉDIO | market_factor hardcoded = 1.0 em predict_time_to_fill — sem sinal real de mercado | predictive_analytics_service.py:247–251 |
| F8-G7 | 🟡 MÉDIO | get_search_analytics faz fetch de PII (name, email, phone) da tabela candidates antes de descartar — data minimization risk LGPD | analytics_tool_registry.py:163–178 |
| F8-G8 | 🟢 BAIXO | Sem export PDF/HTML em generate_job_report — JSON → chat text apenas | analytics_tool_registry.py:_wrap_generate_job_report |

---

## APPENDIX A — MATRIZ DE RISCO CONSOLIDADA (TODOS OS FLOWS)

| ID | Flow | Severidade | Descrição | Arquivo:Linha |
|---|---|---|---|---|
| F1-G1 | F1 | 🔴 CRÍTICO | Tenant isolation condicional via hasattr(Candidate,'company_id') | query_tools.py:79–82 |
| F2-G1 | F2 | 🔴 CRÍTICO | job_screening_questions sem company_id filter | wsi_interview_graph.py:350–362 |
| F3-G1 | F3 | 🔴 CRÍTICO | mesmo que F2-G1 — cross-tenant exposure de perguntas WSI | wsi_interview_graph.py:350–362 |
| F3-G2 | F3 | 🔴 CRÍTICO | HITL fail-open — graph prossegue sem revisão humana se request_approval falha | wsi_interview_graph.py:1057 |
| F4-G1 | F4 | 🔴 CRÍTICO | communication_tools.send_email/send_whatsapp retornam simulated=True — nenhuma entrega real | communication_tools.py:104, 195 |
| F4-G2 | F4 | 🔴 CRÍTICO | PATH A execute-action bypassa todos os checks LGPD | triggers.py:252–380 |
| F5-G1 | F5 | 🔴 CRÍTICO | company_id não passado ao calendar_service → sempre app-level MS Graph | interview_scheduling_nodes.py:345 |
| F5-G2 | F5 | 🔴 CRÍTICO | Interview DB record sem company_id — multi-tenant violation | interview_scheduling_nodes.py:357–391 |
| F1-G2 | F1 | 🟠 ALTO | LGPD consent não verificado em search_candidates | query_tools.py:44–186 |
| F1-G3 | F1 | 🟠 ALTO | BiasAuditService passivo — audit_ranking_results nunca chamado | query_tools.py:164–178 |
| F2-G2 | F2 | 🟠 ALTO | wsi_final_score não persistido diretamente em Candidate.wsi_score | wsi_interview_graph.py:695 |
| F2-G3 | F2 | 🟠 ALTO | LGPD consent ABSENT não bloqueia WSI | wsi_interview_graph.py:329–333 |
| F2-G4 | F2 | 🟠 ALTO | PipelineReActAgent sem _fairness_pre_check | pipeline_react_agent.py:117 |
| F3-G3 | F3 | 🟠 ALTO | wsi_results table não escrita no text-WSI path | wsi_voice_orchestrator.py:465 |
| F3-G4 | F3 | 🟠 ALTO | Naming mismatch: wsi_score (frontend) ≠ wsi_final_score (backend) | candidates_metadata.py:541 |
| F3-G5 | F3 | 🟠 ALTO | LGPD soft-warning: consent ABSENT não bloqueia | wsi_interview_graph.py:337–343 |
| F4-G3 | F4 | 🟠 ALTO | requires_approval=True não bloqueante | transition_dispatch_service.py:~130 |
| F4-G4 | F4 | 🟠 ALTO | Sem webhook handler Twilio — WhatsApp status não rastreado | (ausente) |
| F4-G5 | F4 | 🟠 ALTO | Sem cross-channel failover WhatsApp → email | communication_service.py |
| F5-G3 | F5 | 🟠 ALTO | check_interviewer_availability() existe mas nunca chamado | calendar_service.py:276 |
| F5-G4 | F5 | 🟠 ALTO | get_provider_for_tenant() sem tenant_id → LLM de sistema | interview_scheduling_nodes.py:215 |
| F6-G1 | F6 | 🟠 ALTO | get_at_risk_candidates sem filtro job_id — retorna todos da empresa | early_warning_service.py:98–157 |
| F6-G2 | F6 | 🟠 ALTO | Conversation history duplo e inconsistente (WS local vs DB) | agent_chat_ws.py:845 |
| F6-G3 | F6 | 🟠 ALTO | "dropout" sem regex FastRouter → sempre LLM Cascade | fast_router.py:199–216 |
| F7-G1 | F7 | 🟠 ALTO | Duas implementações wizard paralelas (JobWizardGraph + WizardReActAgent) | wizard_smart_orchestrator.py:611–615 |
| F7-G2 | F7 | 🟠 ALTO | Learning loop não wired ao STAGE_TOOLS | wizard_tool_registry.py:STAGE_TOOLS |
| F7-G3 | F7 | 🟠 ALTO | ATS sync não disparado no publish da vaga | lifecycle.py:128–136 |
| F8-G1 | F8 | 🟠 ALTO | "tempo médio de contratação" sem regex FastRouter | fast_router.py:271–282 |
| F8-G2 | F8 | 🟠 ALTO | Fairness não wired ao analytics agent | analytics_tool_registry.py |
| F8-G3 | F8 | 🟠 ALTO | dashboard_data.py serve MOCK DATA | dashboard_data.py:7 |

---

## APPENDIX B — COBERTURA DO PROTOCOLO P02

| Critério de validação | Status |
|---|---|
| Cada fluxo de negócio traçado E2E? | ✅ Todos os 8 flows cobertos do frontend ao DB |
| Cadeia vertical verificada (agente→tool→backend→banco→frontend)? | ✅ Cada flow tem seção INTEGRATION VERIFIED com 8 dimensões |
| Cross-cutting marcado em cada ponto? | ✅ Fairness/LGPD/Bias/Error tratados por flow |
| Gaps identificados? | ✅ 53 gaps identificados, classificados por severidade |
| Sequência exata de chamadas documentada? | ✅ Notação [Component] → action → [Component] por flow |
| Pontos de decisão rastreados? | ✅ Decision tables em F5, F6, F7, F8; decisões inline em F1–F4 |
| Pontos de falha documentados? | ✅ Fail-open HITL, simulated comms, conditional tenant isolation, dashboard mock data |
| Dependências entre protocolos downstream identificadas? | ✅ P04 (security hardening), P08 (LGPD remediation), P09 (bias audit), P11 (comm fix), P12 (calendar tenant), P16 (analytics fairness), P17 (dashboard real data) |

---

*Gerado por P02 — auditoria técnica IA/LIA. Próximo: P04 (security hardening) baseado em gaps F1-G1, F2-G1, F4-G1, F4-G2, F5-G1, F5-G2.*
