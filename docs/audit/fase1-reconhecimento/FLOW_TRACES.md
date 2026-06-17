# FLOW_TRACES.md — Mapa de Fluxos Agênticos com Integração Vertical
**Protocolo:** P02
**Data:** 2026-04-14
**Depende de:** PLATFORM_MAP.md (P01)
**Alimenta:** P04, P08, P09, P11, P12, P16, P17

---

## ÍNDICE DE FLUXOS

| # | Nome do Fluxo | Status Geral | Severidade Máxima |
|---|---|---|---|
| 1 | Busca de Candidatos | PARCIALMENTE FUNCIONAL | 🔴 CRÍTICO |
| 2 | Triagem/Screening WSI | PARCIALMENTE FUNCIONAL | 🔴 CRÍTICO |
| 3 | Avaliação Comportamental/Técnica (WSI Async) | PARCIALMENTE FUNCIONAL | 🔴 CRÍTICO |
| 4 | Comunicação com Candidato | PARCIALMENTE FUNCIONAL | 🔴 CRÍTICO |
| 5 | Agendamento de Entrevista | BLOQUEADO | 🔴 CRÍTICO |
| 6 | Interação Conversacional (Chat Livre) | PARCIALMENTE FUNCIONAL | 🟠 ALTO |
| 7 | Criação/Configuração de Vaga | PARCIALMENTE FUNCIONAL | 🔴 CRÍTICO |
| 8 | Relatórios e Analytics | PARCIALMENTE FUNCIONAL | 🔴 CRÍTICO |

---

## FLOW 1 — BUSCA DE CANDIDATOS
**Status geral:** PARCIALMENTE FUNCIONAL

### Sequência de Chamadas
```
[Recruiter Browser]
  → WebSocket frame: { type: "message", content: "buscar candidatos senior de React", domain: "auto" }
  → [Frontend: plataforma-lia] /ws/chat/{session_id}?token=JWT&domain=auto

[Frontend Proxy — Next.js 15]
  → Conexão WS direta ao AI Layer (sem proxy HTTP intermediário)

[AI Layer — agent_chat_ws.py:387]
  → _extract_auth(token) → company_id, user_id (linha 372)
  → PromptInjectionGuard.check(content) (linha 605) — SEG-1
  → check_input_security(content) (linha 619) — SEG-2
  → FairnessGuard.check(content) (linha 628) — SEG-3
  → pre_compliance(content, company_id, domain) (linha 641) — C3B layer

[CascadedRouter — cascaded_router.py]
  → Tier 0: MemoryResolver (pronomes/referências de contexto)
  → Tier 1: LRU in-process (MD5 hash)
  → Tier 2: Redis hash cache
  → Tier 3: VectorSemanticCache (pgvector ≥ 0.85)
  → Tier 4: FastRouter (fast_router.py:77-90)
       Padrão casado: r"buscar?\s+\w*\s*candidato" → domain="sourcing"
  → Retorna: RouteResult(domain_id="sourcing", confidence=0.9, source="fast_router")

[agent_chat_ws.py:780-789]
  → active_domain = "sourcing"
  → _subagent_for_sourcing(content) → "sourcing_search" (sub-roteamento Z2)

[SourcingSearchAgent — sourcing_search_agent.py]
  → @register_agent("sourcing_search")
  → _get_tools() → sourcing_search_tool_registry.py → ["search_candidates","filter_results","view_candidate"]
  → Herda de SourcingReActAgent → LangGraphReActBase (create_react_agent nativo)

[LangGraph ReAct Loop]
  → LLM (Haiku) decide chamar tool: search_candidates(skills=["React"], seniority="Sênior", limit=20)

[Tool: search_candidates — query_tools.py:37-175]
  → context.company_id injetado (multi-tenant)
  → AsyncSessionLocal → SELECT Candidate WHERE company_id=X AND seniority_level="Sênior" AND skills∋"React"
  → Post-filter skills (in-memory)
  → Retorna: { success: True, data: { candidates: [...], total: N } }

[Opcional — rank_candidates — query_tools.py:178+]
  → Chama wrf_dynamic_k_service (Weighted Rank Fusion)
  → Candidatos ordenados por WRF score combinado (es_rank + pgv_rank)

[SourcingReActAgent → AgentOutput]
  → message: "Encontrei X candidatos sênior de React..."
  → actions: [panel_update com lista ranqueada]

[agent_chat_ws.py → ws_manager.send_to_session]
  → { type: "message", content: "...", confidence: 0.9 }
  → { type: "panel_update", panel_type: "candidate_review", panel_data: {...} }

[Frontend — Next.js]
  → Recebe WS frame → renderiza painel lateral com candidatos ranqueados
```

### Cross-Cutting
```
├─ Fairness: ✓ FairnessGuard inline pré-processamento (agent_chat_ws.py:628-641)
│            ✓ C3B layer pre_compliance antes de passar ao agente
│            ⚠ NÃO aplicado dentro de query_tools.search_candidates — filtros discriminatórios
│              passados via tool args não são bloqueados no nível da tool
├─ LGPD: ⚠ NÃO verificado no flow de busca — consent checker não é chamado em search_candidates
│          (consent verificado apenas no WSI/screening — wsi_interview_graph.py:290-325)
│          Candidatos aparecem na lista sem verificação de consentimento para busca
├─ Bias: ✓ FairnessGuard.IMPLICIT_BIAS_TERMS bloqueia "boa aparência", "periferia" etc.
│          no input do usuário (fairness_guard.py:40-120)
│          ⚠ Bias nos RESULTADOS de ranking não auditado — WRF score sem fairness check
└─ Error handling: ⚠ PARCIAL — try/except genérico em search_candidates retorna erro como
                    string sem status code estruturado; sem retry
```

### INTEGRAÇÃO VERIFICADA
```
├─ Agente → Tool: ✓ — SourcingSearchAgent._get_tools() retorna ToolDefinition registradas;
│                      tool_definition_to_langchain_tool() integra ao create_react_agent
│                      (sourcing_search_agent.py:32-38, sourcing_search_tool_registry.py:10-14)
├─ Tool → Backend: ✓ — search_candidates() usa AsyncSessionLocal direto (SQLAlchemy async);
│                       NÃO chama Rails; lê tabela candidates do PostgreSQL do AI Layer
│                       (query_tools.py:68-132)
├─ Backend → Banco: ✓ — SQLAlchemy async SELECT com WHERE company_id + filtros (query_tools.py:70-108)
├─ Backend → Externo: ⚠ — Pearch AI (busca global) disponível via sourcing_pipeline.py mas
│                           NÃO invocado no flow agent; chat agent usa apenas busca local
├─ Banco → Frontend: ⚠ — Resultado via WS frame (panel_update), não via API REST;
│                          Frontend recebe JSON sem schema validado (any dict)
├─ Resultado → Agente: ✓ — Tool retorna dict estruturado → LLM ReAct lê e formula resposta
├─ Tenant isolation: ⚠ — Depende de `hasattr(Candidate, 'company_id')` em runtime;
│                          se campo ausente no modelo, filter é IGNORADO silenciosamente
│                          (query_tools.py:78)
└─ Audit trail: ⚠ — Busca via agent (query_tools) NÃO chama audit_service;
                    apenas REST endpoint /candidates/search/local faz audit
```

### GAPS
| ID | Severidade | Descrição | Arquivo:Linha |
|---|---|---|---|
| F1-G1 | 🔴 CRÍTICO | LGPD consent não verificado em busca — candidatos aparecem na lista sem gate LGPD | query_tools.py:37 |
| F1-G2 | 🔴 CRÍTICO | Tenant isolation condicional — `if hasattr(Candidate, 'company_id')` silencia ausência do campo em vez de lançar erro | query_tools.py:78 |
| F1-G3 | 🟠 ALTO | Audit trail ausente no path agent — busca via chat não passa por AuditService | query_tools.py (inteiro) |
| F1-G4 | 🟠 ALTO | Fairness nos resultados de ranking ausente — WRF score sem passo de fairness check pós-ranking | query_tools.py:178+ |
| F1-G5 | 🟠 ALTO | Rails completamente desacoplado — AI Layer lê PostgreSQL diretamente; Rails e AI Layer podem ter dados divergentes | routes.rb:39-43 |
| F1-G6 | 🟡 MÉDIO | Timeout ausente no ReAct loop — sem timeout no `agent.process()` call | sourcing_react_agent.py |

---

## FLOW 2 — TRIAGEM/SCREENING WSI
**Status geral:** PARCIALMENTE FUNCIONAL

### Sequência de Chamadas
```
[Recruiter/Sistema]
  → POST /api/v1/wsi/async/invite (wsi_async.py:44)
  ou POST /api/v1/wsi/interview-graph/sessions (wsi/sessions.py:120)

[Frontend — plataforma-lia]
  → /api/backend-proxy/wsi/screening-pipeline → POST Python :8001/api/v1/wsi/screening-pipeline
  → /api/backend-proxy/wsi-async → POST Python :8001/api/v1/search/candidates
     (plataforma-lia/src/app/api/backend-proxy/wsi-async/route.ts — APONTA PARA ENDPOINT ERRADO)

[WSI Session Start — wsi/sessions.py:120-165]
  → WSIInterviewGraph.create_session(candidate_id, job_id, company_id, interview_level)
  → WsiRepository.get_job_vacancy_context(job_id, company_id) — carrega job da DB

[WSIInterviewGraph.start() — wsi_interview_graph.py:990-1005]
  → LangGraph StateGraph compiled → chama node: load_context

[Node: load_context — wsi_interview_graph.py:280-415]
  → Gate LGPD: ConsentCheckerService.check_candidate_consent(candidate_id, company_id, "ai_screening")
    → Se consent revogado: state.error="LGPD_CONSENT_REVOKED", stage=ERROR (linha 305-318)
    → Se exception: logger.warning() → prossegue sem gate (linha 319-324) ← CRÍTICO
  → Carrega perguntas: SELECT * FROM job_screening_questions WHERE job_vacancy_id=:job_id (linha 343)
  → Fallback hierárquico: DB → WSIScreeningPipeline → 2 perguntas hardcoded

[Node: generate_question — wsi_interview_graph.py:460-495]
  → Apresenta WSIQuestionBlock ao candidato → state.awaiting_response = True

[Candidato → POST /interview-graph/sessions/{session_id}/respond (wsi/sessions.py:172)]

[Node: validate_response — wsi_interview_graph.py:500-590]
  → Verifica skip → PromptInjectionGuard.check(response) → PII masking → FairnessGuard check

[Node: score_response — wsi_interview_graph.py:600-660]
  → calculate_wsi_deterministic(response_text, competency_name, question_framework)
  → DeterministicWSIResult { final_score, bloom_level, dreyfus_level, justification }
  → AuditService.log_decision("wsi_block_scored") por bloco (linha 620-640)

[Node: advance — wsi_interview_graph.py:663-680]
  → Loop até todas as perguntas → generate_feedback

[Node: generate_feedback — wsi_interview_graph.py:685-770]
  → calculate_final_wsi_score(technical_scores, behavioral_scores, seniority)
  → SENIORITY_WEIGHTS (ex: senior: tech=0.5625, behav=0.4375)
  → decision: "approved"/"needs_review"/"rejected"
  → AuditService.log_decision("wsi_final_evaluation") — BCB 498/SOX (linha 717-740)

[HITL Gate — wsi_interview_graph.py:1025-1060]
  → hitl_service.request_approval(thread_id, action="finalize_wsi_score", data={scores})
  → Frontend recebe: { type: "approval_required", thread_id, action, data }
  → Recruiter aprova/rejeita via WS

[Persist score — sessions.py:183-200]
  → Resultado retornado via REST response: { wsi_final_score, recommendation, scores }
  → interview_session_store.delete(session_id) — sessão in-memory apagada
  ⚠ NÃO persiste wsi_final_score em tabela Candidate ou VacancyCandidate

[Feedback ao candidato — wsi_interview_graph.py:750-770]
  → Se "reprovado": candidate_feedback_service.send_gate_feedback(email) via asyncio.ensure_future()
```

### Cross-Cutting
```
├─ Fairness: ✓ APLICADO em validate_response — fairness_guard_middleware.check_fairness()
│             analisa resposta do candidato (wsi_interview_graph.py:555-575)
│             ✓ PII masking (strip_pii_for_llm_prompt) antes de scoring
│             ✓ PROTECTED_CRITERIA excluídos de criteria_used no audit trail
│             ⚠ Bias no prompt de geração de perguntas (WSIScreeningPipeline) não auditado
├─ LGPD: ✓ Gate 1 em load_context: ConsentCheckerService.check(candidate_id, "ai_screening")
│          → aborta com state.error="LGPD_CONSENT_REVOKED" se revogado (wsi_interview_graph.py:296-317)
│          ⚠ Falha silenciosa: exception no consent check → prossegue sem gate (linha 319-324)
├─ Bias: ✓ PROTECTED_CRITERIA na auditoria de cada bloco e decisão final
│         ✓ SENIORITY_WEIGHTS documentados e fixos (sem LLM no cálculo final)
│         ⚠ Bias no prompt de geração de perguntas (WSIScreeningPipeline) não auditado
└─ Error handling: ✓ Cada node tem try/except com log e estado de ERROR
                   ⚠ Falhas de ConsentChecker e AuditService são não-bloqueantes (best-effort)
                   ⚠ score_response exception → score 0 silencioso (wsi_interview_graph.py:648)
```

### INTEGRAÇÃO VERIFICADA
```
├─ Agente → Tool: ✓ — WSIInterviewGraph é StateGraph determinístico com nodes explícitos
│                      load_context→generate_question→validate→score→advance→feedback
│                      (wsi_interview_graph.py:830-900)
├─ Tool → Backend: ✓ — wsi_deterministic_scorer.calculate_wsi_deterministic() é pure function;
│                       calcula Bloom/Dreyfus/STAR localmente (wsi_deterministic_scorer.py:1-100)
├─ Backend → Banco: ✓ LEITURA — load_context lê job_screening_questions via SQL direto
│                   ✗ ESCRITA — wsi_final_score NÃO é escrito em Candidate;
│                               interview_session_store é in-memory, apagado após complete
│                               (sessions.py:195)
├─ Backend → Externo: ✓ — candidate_feedback_service.send_gate_feedback (email SMTP) — fire-and-forget
├─ Banco → Frontend: ⚠ — Score retornado via JSON REST, não via DB; refresh perde resultado
├─ Resultado → Agente: ✓ — Após HITL resume, WS reenvia resultado (agent_chat_ws.py:460-480)
├─ Tenant isolation: ✓ — state.company_id propagado em todos os nodes (wsi_interview_graph.py:296, 622)
└─ Audit trail: ✓ FORTE — AuditService.log_decision por bloco + decisão final
                           (wsi_interview_graph.py:618-640, 717-740)
```

### GAPS
| ID | Severidade | Descrição | Arquivo:Linha |
|---|---|---|---|
| F2-G1 | 🔴 CRÍTICO | wsi_final_score NÃO persiste no banco — sessão in-memory deletada após resposta REST | wsi/sessions.py:183-200 |
| F2-G2 | 🔴 CRÍTICO | Frontend /wsi-async route aponta para endpoint errado — backendPath hardcoded como `/api/v1/search/candidates` | plataforma-lia/src/app/api/backend-proxy/wsi-async/route.ts |
| F2-G3 | 🔴 CRÍTICO | ConsentChecker exception silenciosa burla gate LGPD — `except Exception: logger.warning() → prossegue` | wsi_interview_graph.py:319-324 |
| F2-G4 | 🟠 ALTO | interview_session_store in-memory — reinicialização do processo apaga sessões ativas | wsi/sessions.py (toda sessão) |
| F2-G5 | 🟠 ALTO | Fallback hardcoded de 2 perguntas — avaliação ocorre com perguntas genéricas sem validade científica | wsi_interview_graph.py:800-815 |
| F2-G6 | 🟠 ALTO | Rails completamente desacoplado de WSI — Candidate model no Rails sem campo wsi_score | ats-api-copia/config/routes.rb |
| F2-G7 | 🟡 MÉDIO | HITL para WSI sem timeout de notificação — avaliação fica "travada" após 24h (Redis TTL) | hitl_service.py |
| F2-G8 | 🟡 MÉDIO | Bias no pipeline de geração de perguntas — WSIScreeningPipeline gera via LLM sem FairnessGuard | wsi_screening_pipeline.py |

---

## FLOW 3 — AVALIAÇÃO COMPORTAMENTAL/TÉCNICA
**Status geral:** PARCIALMENTE FUNCIONAL

### Sequência de Chamadas
```
[Recruiter/API] → POST /api/v1/wsi/async/invite
  → [wsi_async.py:create_async_invite] → InviteRequest(candidate_id, job_id, company_id)
  → [WSIAsyncSessionService.create_session] (wsi_async_session_service.py:43)
      → session_id = "system:{uuid4()}"
      → Redis: setex("wsi_async:{session_id}", 172800s, session_data) (linha 64)
      → DB: INSERT INTO wsi_session [...] (linha 77)
        ← CRÍTICO: app.models.wsi_session não existe → ImportError silenciado

[Candidate] → GET /api/v1/wsi/async/{token}
  → [wsi_async.py:get_session_state] → Redis: GET "wsi_async:{token}"
  → Retorna: {status, current_question=None, total_questions=0} ← SEMPRE ZERO/NONE

[WSIScreeningPipeline.build_pipeline()] (wsi_screening_pipeline.py)
  → SeniorityResolver.resolve_seniority_full() → effective_seniority
  → _build_company_block() → perguntas da empresa + affirmative action injection
  → _build_technical_block() → WSIService.generate_from_simple_inputs() → LLM (Claude)
  → _build_behavioral_block() → WSIService.generate_from_simple_inputs() → LLM (Claude)
  → calibrate_or_fallback() → Bloom/Dreyfus levels por senioridade
  → WSIScreeningPipelineResponse(questions, blocks, metadata, quality_warnings)

[Candidate] → POST /api/v1/wsi/async/{token}/answer
  → [WSIAsyncSessionService.submit_response()] → Redis update (somente Redis, sem DB)

[Candidate] → GET /api/v1/wsi/async/{token}/complete
  → [wsi_async.py:complete_session] → Redis: status → "completed"
  ← CRÍTICO: NÃO dispara scoring, NÃO publica screening.wsi.completed

[Automation] → POST /api/v1/handle-trigger/screening-completed
  → [handlers_screening.py:handle_screening_completed:421]
  → validate_multi_tenancy(db, candidate_id, vacancy_id, company_id)
  → _score_and_decide():
      → _calculate_wsi(): Path A (structured) ou Path B (transcript → LLM)
      → WSIService.calculate_wsi() → WSIScoreCalculator.calculate()
          → WSI técnico + comportamental (classificação por keywords hardcoded: python, javascript, sql, docker, aws)
          → overall_WSI = (technical * 0.7) + (behavioral * 0.3)
  → _determine_screening_decision(overall_wsi):
      → WSI ≥ 3.75 → aprovado; 3.0-3.75 → aguardando; < 3.0 → nao_aprovado
  → WSIService.generate_candidate_feedback() (LLM)
  → CommunicationService.send_screening_result()
  → AuditService.log_decision() + AutomationExecutionLog INSERT

[PlatformEventHandler via RabbitMQ: "screening.wsi.completed"]
  → handle_screening_completed_event (platform_event_handlers.py:493)
  → Aplica WSI_CUTOFFS → auto-advance ou notify recruiter
```

### Cross-Cutting
```
├─ Fairness: WSI_CUTOFFS fixos (3.75/3.00) documentados. calibrate_or_fallback() por senioridade
│            previne viés por nível. Affirmative action questions são is_eliminatory=False.
│            ⚠ Classificação técnica por keywords hardcoded cria viés contra stacks não listadas
├─ LGPD: Sessão WSI armazena candidate_id + respostas em Redis (TTL 48h) sem criptografia.
│         Consentimento não verificado antes de criar sessão async.
│         Sem mecanismo de exclusão por solicitação do titular para respostas Redis.
├─ Bias: Score determinístico para cálculo final (não LLM) — alinhado com política anti-viés.
│         Extração de evidências via LLM (transcript analysis) pode introduzir viés.
└─ Error handling: Duplo try/except em create_session (Redis + DB); ambos silenciosos.
                   Helpers de _process_screening_completed capturam e retornam False/None
                   sem interromper o fluxo.
```

### INTEGRAÇÃO VERIFICADA
```
├─ Agente → Tool: ⚠ — WSIScreeningPipeline chama WSIService/LLM corretamente; mas
│                      complete_session não conecta a scoring
├─ Tool → Backend: ✗ — communication_tools.py:send_email/send_whatsapp retornam mock
│                       sem chamar CommunicationDispatcher real
├─ Backend → Banco: ⚠ — DB insert de WSISession falha (modelo ausente); respostas Redis-only;
│                        AutomationExecutionLog persiste
├─ Backend → Externo: ✓ — CommunicationDispatcher.send_email → Mailgun/Resend com circuit breaker;
│                          Twilio para WhatsApp
├─ Banco → Frontend: ⚠ — score vem do trigger HTTP, não de evento em tempo real
├─ Resultado → Agente: ✗ — Nenhum evento/callback retorna para o agente após complete_session
├─ Tenant isolation: ✓ — validate_multi_tenancy() obrigatório antes de scoring
└─ Audit trail: ⚠ — AuditService.log_decision() para score final; respostas individuais sem DB
```

### GAPS
| ID | Severidade | Descrição | Arquivo:Linha |
|---|---|---|---|
| F3-G1 | 🔴 CRÍTICO | WSISession model ausente — `from app.models.wsi_session import WSISession` lança ImportError silenciado | wsi_async_session_service.py:77 |
| F3-G2 | 🔴 CRÍTICO | complete_session não dispara scoring — apenas marca Redis como "completed"; nenhum evento publicado | wsi_async.py:complete_session |
| F3-G3 | 🟠 ALTO | Respostas do candidato sem persistência DB — Redis TTL 48h; expiração silenciosa sem audit trail permanente | wsi_async_session_service.py:119 |
| F3-G4 | 🟠 ALTO | Technical skill classification hardcoded — Java, Kotlin, Swift, Rust, Ruby classificados como comportamentais | score_calculator.py:34 |
| F3-G5 | 🟠 ALTO | total_questions sempre zero — create_session não popula total_questions; is_complete nunca calculado | wsi_async.py:submit_answer:is_complete |
| F3-G6 | 🟠 ALTO | current_question nunca servido — get_session_state retorna current_question=None sempre | wsi_async.py:68 |
| F3-G7 | 🟠 ALTO | communication_tools.py não despacha — send_email/send_whatsapp retornam mock sem chamar dispatcher | communication_tools.py:~100 |
| F3-G8 | 🟡 MÉDIO | Duplicate WSI_PASS_THRESHOLD — definido em _shared.py:511 e wsi_deterministic_scorer.py:WSI_CUTOFFS; risco de dessincronização | automation/_shared.py:511 |

---

## FLOW 4 — COMUNICAÇÃO COM CANDIDATO
**Status geral:** PARCIALMENTE FUNCIONAL

### Sequência de Chamadas
```
PATH A — Agent-Initiated (CommunicationReactAgent)
[Recruiter] → ChatMessage → [UnifiedChatEndpoint]
  → [CommunicationReactAgent] (communication_react_agent.py)
  → Tool: send_email ou send_whatsapp (communication_tool_registry.py:282)
      → communication_tools.py:send_email()
          → DB: SELECT Candidate WHERE id=candidate_id
          → Retorna mock success dict ← NÃO chama CommunicationDispatcher
      → communication_tools.py:send_whatsapp()
          → DB: SELECT Candidate for phone/whatsapp
          → Retorna mock success dict ← NÃO chama CommunicationDispatcher

PATH B — Pipeline Transition (TransitionDispatchService)
[PipelineTransitionAgent] → TransitionDispatchService.dispatch_for_transition()
  (transition_dispatch_service.py:dispatch_for_transition)
  → Validates action_behavior in ACTION_BEHAVIOR_SITUATION_MAP
  → DB: SELECT CommunicationMatrixEntry WHERE trigger=trigger_name AND company_id
  → _load_candidate_data(vacancy_candidate_id)
  → CandidateChannelSelector.select_channels() → filtra por preferências + opt-out
  → _build_variables() → substituição de variáveis no template
  → For each channel:
      → Email: EmailTemplate from DB → render → CommunicationDispatcher.send_email() → Mailgun/Resend
      → WhatsApp: CommunicationDispatcher.send_whatsapp() → Twilio

PATH C — Automation Event Handler
[screening_completed trigger] → CommunicationService.send_screening_result()
  (handlers_screening.py:_send_screening_communication)
  → CommunicationService.send_message() (communication_service.py:639)
      → validate_can_send(candidate_id, company_id, channel, message_type):
          → _check_opt_out() → SELECT CandidateOptOut
          → _check_quarantine() → SELECT CandidateQuarantine WHERE quarantine_end > now
          → _check_rate_limit() → COUNT(CommunicationLog) WHERE today (max 3/day)
          → _is_within_sending_hours() → Brazil UTC-3, 08h-20h weekdays only
      → MESSAGE_REQUIRES_APPROVAL → HITL gate para INITIAL_CONTACT, REJECTION, OFFER
      → Provider fallback: Mailgun → Resend → AWS SES → Mock (dev)
      → DB: INSERT CommunicationLog (status=sent, channel, candidate_id, company_id)

[Mailgun Webhook] → POST /webhooks/mailgun (mailgun_webhooks.py)
  → _verify_mailgun_signature() → HMAC-SHA256 + replay protection (|Δt| ≤ 300s)
  → DB: UPDATE CommunicationLog SET status=new_status WHERE provider_message_id=message_id
```

### Cross-Cutting
```
├─ Fairness: Sending hours policy (8h-20h BRT) aplicado uniformemente. Rate limit (3/day)
│            uniformemente aplicado. Template system garante mensagens consistentes.
│            ⚠ Path A bypassa validate_can_send() — sem LGPD check via agent
├─ LGPD: ✓ validate_can_send() enforced em opt-out + quarantine antes de CADA send (Path B/C)
│          ✓ OptoutRepository persiste ConsentEvent com proof_hash (SHA256)
│          ✓ Unsubscribe links via HMAC tokens (communication_optout.py:41)
│          ✗ Path A (agent tools) bypassa validate_can_send() completamente
├─ Bias: Templates pré-aprovados e padronizados. LIA tone uniforme por empresa.
└─ Error handling: ✓ CommunicationService com retry (MAX_RETRIES=3, exponential backoff)
                   ✓ Fallback providers: Mailgun→Resend→Mock
                   ✓ Mailgun webhook com tratamento específico de erros
                   ⚠ TransitionDispatchService engole exceções de CandidateChannelSelector
```

### INTEGRAÇÃO VERIFICADA
```
├─ Agente → Tool: ✗ — Agent tools (Path A) retornam mock — real dispatch nunca acontece
├─ Tool → Backend: ⚠ — Path B e Path C chamam CommunicationDispatcher corretamente
├─ Backend → Banco: ✓ — CommunicationLog INSERT em send; UPDATE em webhook delivery
├─ Backend → Externo: ✓ — CommunicationDispatcher → Mailgun (httpx POST) + Twilio SDK
│                          com circuit breakers
├─ Banco → Frontend: ⚠ — histórico em DB; proxy /api/backend-proxy/communications existe;
│                          delivery status em tempo real depende do Mailgun webhook
├─ Resultado → Agente: ✗ — Sem feedback loop de CommunicationService para o agente após send
├─ Tenant isolation: ✓ — company_id em CommunicationLog, OptOut, Quarantine; validate_multi_tenancy
└─ Audit trail: ⚠ — CommunicationLog para sends válidos; sem audit para Path A mock sends
```

### GAPS
| ID | Severidade | Descrição | Arquivo:Linha |
|---|---|---|---|
| F4-G1 | 🔴 CRÍTICO | Path A (agent tools) nunca dispara real — communication_tools.py retorna mock sem chamar CommunicationDispatcher ou CommunicationService | communication_tools.py:~50 e ~130 |
| F4-G2 | 🔴 CRÍTICO | Path A bypassa LGPD — candidatos com opt-out poderiam receber comunicações se agente fosse real | communication_tools.py:send_email |
| F4-G3 | 🟠 ALTO | WhatsApp sem webhook de delivery — Twilio não tem status de entrega persistido no DB | mailgun_webhooks.py (ausência de twilio_status_webhooks.py) |
| F4-G4 | 🟠 ALTO | matrix_entry.requires_approval não-bloqueante — L3 Human Review Gate logado mas não enforced | transition_dispatch_service.py:~115 |
| F4-G5 | 🟠 ALTO | UNSUBSCRIBE_HMAC_SECRET efêmero — se não configurado, chave gerada no startup; restart invalida todos os links | communication_optout.py:28 |
| F4-G6 | 🟡 MÉDIO | Sending hours sem fila de retry — mensagens bloqueadas retornam falha sem agendamento | communication_service.py:152 |
| F4-G7 | 🟡 MÉDIO | Circuit breaker in-memory — MAILGUN_CIRCUIT e RESEND_CIRCUIT perdem estado no restart | resilience/circuit_breaker.py |
| F4-G8 | 🟢 BAIXO | ConsentEvent sem FK para Candidate — subject_email como string sem foreign key | optout_repository.py:65 |

---

## FLOW 5 — AGENDAMENTO DE ENTREVISTA
**Status geral:** BLOQUEADO

### Sequência de Chamadas
```
[Frontend / Chat UI]
  → POST message {domain: "scheduling", question: "Agendar entrevista técnica com candidato X"}
  → [MessageRouter.route()] (src/services/message_router.py:21)
  → configure_ott_from_message(message) (src/services/ott_service.py)
  → DomainOrchestrator.process_query(domain_id="scheduling") (src/domains/orchestrator.py:37)

[SchedulingDomain.process_intent()] (src/domains/scheduling/domain.py:168)
  → FAST PATH: active session → action_id="schedule_interview" (domain.py:176-185)
  → FAST PATH: _SCHEDULE_INTENT_PATTERN → "schedule_interview", confidence=0.95 (domain.py:187-239)
  → SLOW PATH: LLM intent classify (fallback) (domain.py:241-285)

[ScheduleInterviewAction.schedule_interview()] (actions/schedule_interview.py:17)
  → SchedulingConversationMemory.get_scheduling_session()
  → SchedulingSession() — nova ou retomada
  → get_scheduling_graph() → SchedulingGraph singleton (scheduling/graph.py:739)

[SchedulingGraph.invoke(state, thread_id)] (scheduling/graph.py:734)
  → LangGraph compiled graph com checkpointer (Redis/MemorySaver)

NODES:
  1. _parse_node(state) (graph.py:93) → extrai type, platform, date/time, emails via regex
  2. _infer_node(state) (graph.py:123) → InferenceEngine infere candidate, job, interviewers
  3. _decide_node(state) (graph.py:139) → decide próximo nó (ask/check/confirm/execute)
  4a. _ask_missing_node(state) (graph.py:157) → coleta campos faltantes
  4b. _check_availability_node(state) (graph.py:182)
      → SchedulingAPIClient.get_multi_availability()
        → GET /v1/users/scheduling/availability/multi ← ROTA NÃO EXISTE NO RAILS
        → fallback: GET /v1/users/scheduling/availability ← ROTA NÃO EXISTE NO RAILS
  4c. _offer_slots_node(state) (graph.py:231) → SlotsFormatter.format_slots_table()
  4d. _resolve_conflict_node(state) (graph.py:258) → exibe conflito + alternativas
  4e. _build_confirmation_node(state) (graph.py:282) → ConfirmationFormatter
  5. _execute_node(state) (graph.py:295)
      DIRECT MODE: POST /v1/users/calendar_events ← ROTA NÃO EXISTE NO RAILS
      SELF-SCHEDULING: POST /v1/users/scheduling/links ← ROTA NÃO EXISTE NO RAILS
      BULK MODE: api.get_apply(apply_id) → GET /v1/users/applies/:id (✓ existe)
  6. _finalize_node(state) (graph.py:356) → memory.update_after_scheduling()

[DomainOrchestrator] → AuditCallbackHandler.finalize() (orchestrator.py:130)
  ⚠ Nenhum domain message criado para "scheduling" (orchestrator.py:181-268)
```

### Cross-Cutting
```
├─ Fairness: Ausente neste domínio — scheduling é operacional, não decisório.
├─ LGPD: PII (candidate_email, candidate_name) em plaintext no body do calendar_event;
│         sem mascaramento antes de envio ao MS Graph/Google.
├─ Bias: Não aplicável diretamente.
└─ Error handling: try/except em cada node, mas erros de API retornam needs_more_input=True
                   sem informar o usuário da causa real; AuditCallbackHandler finaliza
                   com status="error" mas sem log estruturado ao banco.
```

### INTEGRAÇÃO VERIFICADA
```
├─ Agente → Tool (SchedulingAPIClient): ✓ — bem estruturado, retry em 401
├─ Tool → Backend Rails (/calendar_events): ✗ — ROTA NÃO EXISTE em routes.rb
├─ Tool → Backend Rails (/scheduling/availability): ✗ — ROTA NÃO EXISTE em routes.rb
├─ Tool → Backend Rails (/scheduling/links): ✗ — ROTA NÃO EXISTE em routes.rb
├─ Tool → Backend Rails (/applies/:id): ✓ — rota existe (GET)
├─ Tool → Backend Rails (/interviews CRUD): ✓ — rota existe via users namespace
├─ Backend → Banco (Interview model): ⚠ — account_id propagado via merge mas Interview não
│                                           inclui Searchable → NoMethodError em produção
├─ Backend → Externo (MS Graph/Google): ✗ — não rastreado; nenhum serviço Rails local para isso
├─ Banco → Frontend: ✗ — nenhuma persistência Rails do evento agendado confirmada
├─ Resultado → Agente: ✓ — DomainResponse retorna corretamente
├─ Tenant isolation: ⚠ — create com account_id OK; index usa perform_search sem scope_to_tenant
└─ Audit trail: ⚠ — AuditCallbackHandler finaliza; sem domain message Rails para scheduling
```

### GAPS
| ID | Severidade | Descrição | Arquivo:Linha |
|---|---|---|---|
| F5-G1 | 🔴 CRÍTICO | Rotas Rails ausentes — GET /v1/users/scheduling/availability, GET /v1/users/scheduling/availability/multi, POST /v1/users/calendar_events, POST /v1/users/scheduling/links não existem | ats-api-copia/config/routes.rb:3-85 |
| F5-G2 | 🔴 CRÍTICO | Interview model sem Searchable — InterviewsController#index chama perform_search que invoca Interview.search_default → NoMethodError | app/models/interview.rb:3 |
| F5-G3 | 🟠 ALTO | Sem domain message para scheduling — DomainOrchestrator só cria message Rails para sourced_profile_sourcing, jobs, applies | src/domains/orchestrator.py:181-268 |
| F5-G4 | 🟠 ALTO | Checkpointer degradado sem Redis — sessão de agendamento perde estado em restart de worker | graph.py:656-663 |
| F5-G5 | 🟡 MÉDIO | Timezone naive em _parse_date_time_pt — datetime.now() sem tzinfo → horários errados fora de America/Sao_Paulo | graph.py:433-501 |
| F5-G6 | 🟡 MÉDIO | PII em payload de calendar event — candidate_email vai plaintext para API externa | graph.py:329-345 |

---

## FLOW 6 — INTERAÇÃO CONVERSACIONAL
**Status geral:** PARCIALMENTE FUNCIONAL

### Sequência de Chamadas
```
[Frontend / Chat UI — plataforma-lia/]
  → POST {hub_mode: true, question: "...", context_data: {session_id, user_id, ...}}
  → [MessageRouter.route()] (src/services/message_router.py:21)
  → hub_mode=True → _process_hub_query() (message_router.py:47-50)
  → HubOrchestrator.process(query, context_data) (hub/orchestrator.py:34)

[HubOrchestrator.process()] (hub/orchestrator.py:34-129)
  FASE 1 — Security: safe_process_input(query) → injection check
  FASE 2 — Session Management:
    → SessionStore.get_or_create(session_id) (hub/session.py:251)
    → Redis GET hub:session:{id} → fallback in-memory dict
    → _restore_pending_from_pg(session) → PendingActionStore (psycopg2) (pending_action_store.py:66)
  FASE 3 — Session hydration:
    → _hydrate_session_from_history() se sem histórico
    → session.add_user_message(query)
  FASE 4 — Path Decision:
    A) Has pending action + query responde → _resolve_pending_action()
    B) Active scheduling + query continua → _route_to_scheduling()
    C) Else → _execute_new_query() ← caminho principal

[_execute_new_query()] → CostLadderRouter.route(query) (src/services/cost_ladder.py:305)

[CostLadderRouter.route()] (cost_ladder.py:305-354)
  TIER 0: _tier0_reference() → resolves pronouns ("essa vaga", "o candidato") do contexto
  TIER 1: _tier1_cache() → Redis HGET routing_cache:{hash(query)}
  TIER 2: _tier2_regex() → 13+ compiled regexes → domain_id + confidence=0.90
  TIER 2.5: _tier25_semantic() → SemanticRoutingCache (embedding similarity)
  TIER 3: _tier3_llm() → LLM classify (gemini-2.5-flash) → JSON {domain_id, confidence}

[HubPlanner se domain_id=None ou multi-intent]
  → HubPlanner.create_plan(query) (hub/planner.py)
  → FAST NAV check → NavigationAction
  → Multi-intent → LLM planner → HubExecutionPlan{tasks}

[HubExecutor.execute(plan)] (hub/executor.py:66)
  → For each task → DomainOrchestrator.process_query(domain_id, task_query, context)

[DomainOrchestrator returns DomainResponse]
  → HubOrchestrator:
    → Se clarification needed → session.set_pending_action() → PG INSERT (pending_action_store.py:87-111)
    → session.add_assistant_message() + update_domain_memory()
    → _extract_context_from_results() → extrai job_id/candidate_id para turns futuros
    → session_store.save(session) → Redis SET hub:session:{id} (TTL 24h)

[HubResponseBuilder.build(result)] (hub/response_builder.py)
  → {success, message, data, navigation_actions, suggestions, metadata}

[Frontend recebe]
  → Chat message renderizado
  → navigation_actions → panel_update, navigate, filter_table
```

### Cross-Cutting
```
├─ Fairness: Ausente no flow conversacional livre — nenhum check de fairness antes de
│            responder perguntas sobre candidatos.
├─ LGPD: ✓ PII mascarado em get_history_for_prompt()
│          ✗ Histórico bruto stored in Redis sem criptografia
│          ⚠ Candidate names/emails podem aparecer em tool call results sem mascaramento
├─ Bias: Respostas sobre "candidatos em risco" derivadas de LLM sem explicabilidade de critérios.
│         Risco de bias amplificado sem fairness check.
└─ Error handling: try/except em todos os tiers; falhas Redis/PG silenciosas (logged, non-blocking);
                   CircuitBreaker ausente no HubOrchestrator (importado apenas em workflow.py)
```

### INTEGRAÇÃO VERIFICADA
```
├─ Agente → Tool (DomainOrchestrator.process_query): ✓
├─ Tool → Backend Rails (applies, jobs, candidates): ✓ — rotas existem
├─ Tool → Backend Rails (interviews index): ⚠ — search_default não existe no modelo
├─ Backend → Banco (PostgreSQL via Rails): ✓ — para modelos com Searchable
├─ Backend → Externo: N/A neste flow
├─ Banco → Frontend (ActionCable Message): ✓ — Message model publica via ActionCable após create
├─ Resultado → Agente (DomainResponse): ✓
├─ Tenant isolation: ⚠ — SessionStore usa session_id=user_id; risco de colisão cross-tenant
│                          se user_ids não são UUID únicos globais (orchestrator.py:47)
└─ Audit trail: ⚠ — AuditCallbackHandler por domain call; hub-level sem audit log próprio;
                    queries hub sem Message Rails para domínios não-sourcing
```

### GAPS
| ID | Severidade | Descrição | Arquivo:Linha |
|---|---|---|---|
| F6-G1 | 🟠 ALTO | Dois stores de memória paralelos sem sincronização — ConversationSession (Hub/Redis) e SchedulingConversationMemory (domínio/in-context) podem divergir | hub/session.py:124-128 vs domains/scheduling/memory.py |
| F6-G2 | 🟠 ALTO | Nenhuma mensagem Rails (Message model) para queries hub — histórico de chat não persiste para domínios não-sourcing | orchestrator.py:181-268 |
| F6-G3 | 🟠 ALTO | Redis armazena PII sem criptografia — histórico de sessão com nomes/emails em plaintext | hub/session.py:277-279 |
| F6-G4 | 🟡 MÉDIO | CircuitBreaker ausente no HubOrchestrator — LLM failures sem fallback automático | hub/orchestrator.py |
| F6-G5 | 🟡 MÉDIO | SessionStore session_id = user_id — dois usuários de tenants diferentes com mesmo user_id numérico → sessões colidem | orchestrator.py:47 |
| F6-G6 | 🟡 MÉDIO | mask_pii parcial — mascarado para prompt de histórico mas não para tool outputs ou pending_action payloads em PG | hub/session.py:109-118 vs pending_action_store.py |
| F6-G7 | 🟢 BAIXO | USE_SUPERVISOR = False hardcoded — impossível ligar supervisor LangGraph em prod sem code change | hub/orchestrator.py:18 |

---

## FLOW 7 — CRIAÇÃO/CONFIGURAÇÃO DE VAGA
**Status geral:** PARCIALMENTE FUNCIONAL

### Sequência de Chamadas
```
[Frontend — UnifiedChat.tsx]
  Recruiter digita "Criar vaga de Product Manager Senior"
  → sendChatMessage(text) via WebSocket → useChatTransport.ts → WS /ws/chat/{sessionId}

[AI Layer — agent_chat_ws.py]
  → MainOrchestrator / CascadedRouter.route() (app/orchestrator/cascaded_router.py)
  → Tier 0-5: MemoryResolver → LRU → Redis → VectorSemanticCache → FastRouter
    FastRouter: r"\b(criar|nova|abrir|publicar)\s+(vaga|posicao|cargo)\b" → "job_creation" (conf ≥ 0.70)
  → Tier 5: LLMCascadeRouter (Gemini Flash → Claude Sonnet → Opus) se conf < 0.70

[Supervisor Graph — supervisor_graph.py]
  → Feature flag: ENABLE_UNIFIED_WIZARD=true/false
    (false → fallback domain "jobs" legado, sem Wizard WSI)
  → AgentRegistry.get_or_fallback("job_creation", fallback_id="talent")
  → WizardReActAgent (app/domains/job_management/agents/wizard_react_agent.py)

[ETAPA 1 — INTAKE NODE]
  → Detecta keywords: título, senioridade, departamento
  → ws_send({ type: "wizard_stage", stage: "intake", completeness: 0.05 })
  → Frontend: IntakePanel.tsx (sidebar split view)

[ETAPA 2 — JD ENRICHMENT NODE]
  → JdEnrichmentService → LLM (Claude 3.5 Sonnet, temp=0.3)
  → FairnessGuardMiddleware.check_fairness({ title, description })
    (app/shared/compliance/fairness_guard_middleware.py)
  → PiiMasker.mask(jd_text) antes de LLM (wizard_wsi_patches/sprint-3/compliance_patches.py)
  → Gera: titulo_padronizado, skills_obrigatorias, fairness_corrections, quality_score
  → HITL #1: recruiter aprova JD → audit_wizard_decision(stage="jd_enrichment")

[ETAPAS 3-6 — BIGFIVE, SALARY, COMPETENCY, WSI QUESTIONS]
  → Big Five: LLM extrai 5 traits NEO-PI-R do JD
  → Salary: SalaryBenchmarkService (Redis → Apify → fallback estático)
  → Competency: seniority_resolver.py (rule-based)
  → WSI Questions: gera CBI/Bloom/Dreyfus; dedup por embedding (threshold 0.85)
  → HITL #2: recruiter aprova perguntas

[ETAPA 7 — REVIEW NODE] (wizard_wsi_patches/sprint-1a/03_review_node_apply_defaults.py:review_node)
  → api_client.get_company_defaults() → aplica defaults ao state
  → Readiness checks: jd_approved, questions_approved, quality_score ≥ 50, etc.

[ETAPA 8 — CALIBRATION NODE] (sprint-4/backend_integrations.py:calibration_node)
  → Aprovação mínima de N candidatos (threshold=3) — HARD enforcement

[ETAPA 9 — PUBLISH NODE] (sprint-1a/02_publish_node_rails_integration.py:publish_node)
  Step 1: ws_send({ stage: "publish", progress: "Criando vaga..." })
  Step 2: POST /v1/users/jobs (Rails JobsController#create)
    → @job = @current_user.jobs.build(job_params.merge(account_id: ...)) (jobs_controller.rb:21)
    → Job#after_create → create_default_selective_processes
      → SelectiveProcess.default_process: 5 etapas pipeline (selective_process.rb:17)
    → Retorna { data: { id: job_id } } via JobSerializer
  Step 3: POST /v1/users/recruitment_campaigns → campaign_id
  Step 4: WSIScreeningPipeline.build_pipeline() ← except ImportError silencioso
  Step 5: POST /v1/users/recruitment_campaigns/{id}/add_checkpoint
  Step 6: ActionCable WorkflowChannel broadcast (sprint-2b/02_actioncable_broadcast_patch.py)
  Step 7: POST /v1/users/jobs/{id}/trigger_automation ← ROTA NÃO EXISTE
  Step 8: POST /v1/users/recruitment_slas × 5 stages ← ROTA NÃO EXISTE
  Step 9: SourcingAgentOrchestrator.create_agent(job_id, campaign_id)
  Step 10: AuditService.log_output(company_id, session_id, "publish_job", fairness_flags)
  Step 11: Share link gerado → ws_send({ stage: "publish", completeness: 0.95 })

[ETAPA 10 — LEARNING LOOP]
  → LearningLoopService captura padrões de salary, skills, JD style
  → LearningExtractor hooks pós em LangGraphReActBase
```

### Cross-Cutting
```
├─ Fairness: ✓ FairnessGuardMiddleware.check_fairness() em JD enrichment (pré-LLM)
│             ✓ FairnessGuard 3 camadas: regex → soft warnings 40+ termos → LLM semântico
│             ✓ PII strip → FairnessGuard L3 para domínio job_management (C3b layer)
│             ✓ fairness_flags registrados no AuditService.log_output()
│             ⚠ FairnessGuard L3 LLM timeout → falha silenciosa (campo não bloqueado)
├─ LGPD: ✓ PiiMasker.mask() antes de LLM (sprint-3/compliance_patches.py)
│          ✓ AuditService.log_output() com retention_until (+5 anos = EU AI Act)
│          ✓ PII masking global via PIIMaskingFilter no root logger
│          ✓ LangGraphReActBase._sanitize_messages_pii() strip antes de LLM calls
├─ Bias: ✓ Correções fairness visíveis no JdEnrichmentPanel
│          ✓ PROTECTED_CRITERIA como criteria_ignored no AuditService
│          ✓ Seniority resolver rule-based (determinístico)
└─ Error handling: publish_node bloqueia em falha Rails para job; non-blocking para campaign/sla/automations
                   WSIScreeningPipeline ImportError silencioso; AuditService non-blocking
```

### INTEGRAÇÃO VERIFICADA
```
├─ Agente → Tool: ✓ — WizardReActAgent via LangGraph tool_map (publish_job em sprint-1a/04)
├─ Tool → Backend: ⚠ — publish_node → Rails POST /v1/users/jobs (✓ mapeado)
│                       trigger_automation → /v1/users/jobs/{id}/trigger_automation (✗ sem rota)
│                       create_recruitment_sla → /v1/users/recruitment_slas (✗ sem rota)
├─ Backend → Banco: ✓ — Job.save + after_create SelectiveProcess × 5 (job.rb:12)
├─ Backend → Externo: ⚠ — ActionCable advance_stage (✓); WebhookDelivery (✗ não implementado)
├─ Banco → Frontend: ⚠ — ActionCable WorkflowChannel para kanban; wizard_stage via Python WS
│                          Dois sistemas WS paralelos não orquestrados (PLATFORM_MAP §11.4)
├─ Resultado → Agente: ✓ — state["job_id"], state["campaign_id"], state["share_link"] propagados
├─ Tenant isolation: ⚠ — AI Layer: RLS + company_id ✓; Rails: JobsController sem scope_to_tenant ✗ (H1)
└─ Audit trail: ⚠ — AuditService chamado mas non-blocking; falha silenciosa possível
                    (lia-hardening/auditing/audit_service_patch.py:80)
```

### GAPS
| ID | Severidade | Descrição | Arquivo:Linha |
|---|---|---|---|
| F7-G1 | 🔴 CRÍTICO | TenantScoped.scope_to_tenant não aplicado em JobsController — qualquer usuário autenticado vê vagas de outros tenants | ats-api-copia/app/controllers/v1/users/jobs_controller.rb:10 |
| F7-G2 | 🔴 CRÍTICO | WSManager singleton em-processo — panel_update wizard não chega a clientes em outros workers Uvicorn | app/shared/websocket/ws_manager.py |
| F7-G3 | 🟠 ALTO | /v1/users/jobs/{id}/trigger_automation não registrado — automações pós-publicação silenciosamente ignoradas | ats-api-copia/config/routes.rb |
| F7-G4 | 🟠 ALTO | WSIScreeningPipeline ImportError silencioso — screening pode não ser ativado sem erro visível | sprint-1a/02_publish_node_rails_integration.py:169 |
| F7-G5 | 🟠 ALTO | AuditService.log_output() non-blocking — decisões do wizard podem não ser auditadas sob falha de DB | lia-hardening/auditing/audit_service_patch.py:80 |
| F7-G6 | 🟠 ALTO | Mapeamento company_id (AI Layer) ↔ account_id (Rails) não documentado — publish_node envia X-Company-ID mas Rails usa account_id do JWT | sprint-1a/02_publish_node_rails_integration.py:31 |
| F7-G7 | 🟡 MÉDIO | /v1/users/recruitment_slas não registrado — SLAs de campanha não criados | ats-api-copia/config/routes.rb |
| F7-G8 | 🟡 MÉDIO | APIFY_API_KEY e SERP_API_KEY ausentes — salary/market benchmark usa dados estáticos genéricos | .env (DIAG §Feature 1) |
| F7-G9 | 🟡 MÉDIO | ENABLE_UNIFIED_WIZARD sem default documentado — se não setada, fallback para domain "jobs" legado sem notificação | sprint-1a/01_supervisor_routing_patch.py:62 |
| F7-G10 | 🟡 MÉDIO | create_default_selective_processes usa Current.user — se nil (job criado programaticamente), pipeline não criado | ats-api-copia/app/models/job.rb:17 |

---

## FLOW 8 — RELATÓRIOS E ANALYTICS
**Status geral:** PARCIALMENTE FUNCIONAL

### Sequência de Chamadas
```
[Frontend — UnifiedChat.tsx ou página Analytics]
  Recruiter digita: "Gerar relatório de vagas abertas"
  → WS /ws/chat/{sessionId} → CascadedRouter.route()
  → Tier 4 FastRouter: "analytics" pattern (conf ≥ 0.70) → domain="analytics"
  → AgentRegistry.get_or_fallback("analytics") (migrate_get_agent.py:69)
  → AnalyticsReActAgent (app/domains/analytics/agents/analytics_react_agent.py)
      → LangGraphReActBase + EnhancedAgentMixin
      → LLM: claude-sonnet-4-6 (LLM_AGENT_MODEL)
      → Budget check: check_request_budget_before_llm() antes de cada call
      → AuditCallback injetado automaticamente (libs/audit/lia_audit/audit_callback.py)
      → LearningExtractor hooks pré-loop

[ReAct Loop — Tool Selection]
  Opção A — Insights de vagas: get_job_insights (ou get_analytics_summary via Agent Studio)
  Opção B — Salary benchmark: get_salary_benchmark (analytics_tool_registry.py:30)
    → SalaryBenchmarkService.get_benchmark(role, seniority, location)
    → 3-tier: Redis cache → Apify (APIFY_API_KEY) → _STATIC_SALARY_BENCHMARKS
  Opção C — Pipeline summary: get_pipeline_summary → Query ao DB por stage/job
  Opção D — Relatório de recrutamento: generate_job_report
    → SystemPromptBuilder.build(agent_type="orchestrator", context_page="jobs")
    → LLM query com dados de vagas: total, active, paused, draft, sla_risk_count
  Opção E — Market benchmark: MarketBenchmarkService (market_benchmark_service.py:23)
    → SerpAPI (SERP_API_KEY) → fallback LLM estimate
  Opção F — Fairness report: app/api/v1/fairness_reports.py
    → app/api/v1/admin_bias_audit.py → FairnessComplianceHub em Configurações

[Predict Time to Fill — Heurística]
  → Algoritmo rule-based: base_days + market_factor (sem modelo ML)
  → PLATFORM_MAP.md:§9.7 — nenhum modelo ML treinado encontrado

[RAGAS Evaluation] (app/domains/ai/services/ragas_evaluation_service.py)
  → Métricas: faithfulness, answer_relevancy, context_precision, context_recall
  → Threshold 0.70 overall → flag para revisão se abaixo
  → Celery batch task: diário 03h UTC (NÃO em tempo real)
  → Retenção 90 dias (agent_ragas_evaluations)

[Resposta → Frontend]
  → WS: { type: "message", content: "..." } + { type: "panel_update", ... }
  → BFF: /api/backend-proxy/analytics/ → Next.js Route Handler → FastAPI:8001

[Personalização por Recrutador — GAP]
  → recruiter_personalization_service.py constrói PersonalizationContext
  → PersonalizationContext NÃO injetada em SystemPromptBuilder
  → LIA gera reports idênticos para todos os recrutadores
```

### Cross-Cutting
```
├─ Fairness: ✓ FairnessGuard L1/L2 aplicado pré-query (bloqueia queries discriminatórias)
│             ⚠ RAG max_single_gender_ratio = 0.70 não chamado no analytics flow
│             ⚠ fairness_report NÃO é tool registrada em analytics_tool_registry
├─ LGPD: ✓ PII masking global no logging (PIIMaskingFilter)
│          ✓ LLM prompt PII stripping (LLM_PROMPT_PII_STRIPPING_ENABLED=true)
│          ✓ Dados RAGAS retidos 90 dias
│          ⚠ Integração com DataSubjectRequest (Rails) não confirmada
├─ Bias: ✓ AuditService registra criteria_used, criteria_ignored (PROTECTED_CRITERIA)
│          ✓ Todo scoring é LLM ou rule-based (sem modelo ML treinado)
└─ Error handling: ✓ ReAct loop: AuditCallback loga erros de tool invocations
                   ✓ Budget exceeded: bloqueia com erro (não silencioso)
                   ✓ LLM fallback: gemini → claude → openai
                   ✓ RAGAS: fail-safe (falha não afeta operação)
```

### INTEGRAÇÃO VERIFICADA
```
├─ Agente → Tool: ⚠ — get_salary_benchmark ✓ (analytics_tool_registry.py:30);
│                      get_job_insights/generate_job_report — existência inferida, não confirmada localmente
├─ Tool → Backend: ⚠ — salary_benchmark → Redis/Apify (✓); market_benchmark → SerpAPI (⚠ key vazia)
├─ Backend → Banco: ✓ — PostgreSQL queries para candidates, jobs, selective_processes (AI Layer DB)
├─ Backend → Externo: ⚠ — SerpAPI fallback LLM (sem API key); RAGAS batch diário
├─ Banco → Frontend: ⚠ — Resposta via WS "message" (✓); "panel_update" → painel analytics (wiring não confirmado)
├─ Resultado → Agente: ✓ — Tool observations propagadas no ReAct loop (LangGraph)
├─ Tenant isolation: ✓ — company_id em todas queries AI Layer; RLS migration 068
└─ Audit trail: ✓ — AuditCallback em todo create_react_agent; AuditService.log_output() chamado
```

### GAPS
| ID | Severidade | Descrição | Arquivo:Linha |
|---|---|---|---|
| F8-G1 | 🔴 CRÍTICO | WSManager singleton em-processo — eventos panel_update analytics não chegam a clientes em diferentes workers Uvicorn | app/shared/websocket/ws_manager.py |
| F8-G2 | 🟠 ALTO | Frontend não conectado ao Rails — dados de RecruitmentCampaign, SelectiveProcess, Interview só disponíveis se Python AI os reexpõe | NEXT_PUBLIC_RAILS_URL comentado (PLATFORM_MAP §H5) |
| F8-G3 | 🟡 MÉDIO | PersonalizationContext não injetada — SystemPromptBuilder.build() não recebe recruiter_context; reports idênticos para todos | recruiter_personalization_service.py / system_prompt_builder.py |
| F8-G4 | 🟡 MÉDIO | RAG pipeline não exposto como tool nos agentes analytics | app/api/v1/rag_search.py / rag_pipeline_service.py |
| F8-G5 | 🟡 MÉDIO | SERP_API_KEY e APIFY_API_KEY ausentes — market/salary benchmark usam dados genéricos ou estimativas LLM | .env (DIAG §Feature 1, PLATFORM_MAP §3.3) |
| F8-G6 | 🟡 MÉDIO | panel_update → LiaFloatProvider wiring não confirmado — relatórios podem não abrir painel lateral dinamicamente | app/shared/websocket/ws_manager.py / lia-float-context.tsx |
| F8-G7 | 🟡 MÉDIO | Predict time-to-fill é heurístico rule-based sem dados históricos por empresa | app/domains/analytics/services/ (PLATFORM_MAP §9.7) |
| F8-G8 | 🟡 MÉDIO | Prometheus removido (Task #138) — métricas de hit rate por tier do router não exportadas | app/orchestrator/cascaded_router.py (PLATFORM_MAP §M5) |
| F8-G9 | 🟢 BAIXO | RAGAS avaliação é batch diário (03h UTC) — qualidade degradada não detectada em tempo real | ragas_evaluation_service.py |

---

## APPENDIX A — MATRIZ DE RISCO CONSOLIDADA

Todos os gaps de todos os fluxos, deduplicados e ordenados por severidade.

### 🔴 CRÍTICO

| ID Canônico | Flows Afetados | Descrição | Arquivo:Linha |
|---|---|---|---|
| C-01 | F1, F2, F3, F5, F7, F8 | **WSManager singleton em-processo** — panel_update não chega a clientes em workers Uvicorn distintos; afeta todo fluxo que usa WS | app/shared/websocket/ws_manager.py |
| C-02 | F1 | **LGPD consent não verificado em busca de candidatos** — candidatos aparecem na lista sem gate LGPD | query_tools.py:37 |
| C-03 | F1, F7 | **Tenant isolation condicional** — `if hasattr(Candidate, 'company_id')` silencia ausência do campo; em F7 JobsController sem scope_to_tenant | query_tools.py:78; jobs_controller.rb:10 |
| C-04 | F2 | **wsi_final_score NÃO persiste no banco** — resultado devolvido via REST e sessão in-memory deletada; dados perdidos | wsi/sessions.py:183-200 |
| C-05 | F2 | **Frontend /wsi-async route aponta para endpoint errado** — backendPath hardcoded como `/api/v1/search/candidates` | plataforma-lia/src/app/api/backend-proxy/wsi-async/route.ts |
| C-06 | F2 | **ConsentChecker exception silenciosa burla gate LGPD** — `except Exception: logger.warning() → prossegue` viola compliance | wsi_interview_graph.py:319-324 |
| C-07 | F3 | **WSISession model ausente** — `from app.models.wsi_session import WSISession` lança ImportError silenciado; persistência DB não ocorre | wsi_async_session_service.py:77 |
| C-08 | F3 | **complete_session não dispara scoring** — apenas marca Redis como "completed"; nenhum evento publicado, scoring nunca executado | wsi_async.py:complete_session |
| C-09 | F4 | **Path A (agent tools) nunca dispara real** — communication_tools.py retorna mock sem chamar dispatcher ou validate_can_send LGPD | communication_tools.py:~50 e ~130 |
| C-10 | F4 | **Path A bypassa LGPD** — candidatos com opt-out ou em quarentena poderiam receber comunicações via agente conversacional | communication_tools.py:send_email |
| C-11 | F5 | **Rotas Rails ausentes para scheduling** — GET /v1/users/scheduling/availability, /availability/multi, POST /v1/users/calendar_events, POST /v1/users/scheduling/links; fluxo completamente bloqueado | ats-api-copia/config/routes.rb:3-85 |
| C-12 | F5 | **Interview model sem Searchable** — InterviewsController#index chama perform_search que invoca Interview.search_default → NoMethodError em produção | app/models/interview.rb:3 |

### 🟠 ALTO

| ID Canônico | Flows Afetados | Descrição | Arquivo:Linha |
|---|---|---|---|
| A-01 | F1, F2, F3, F5, F6, F7, F8 | **Rails completamente desacoplado do Frontend** — todas as proxies BFF apontam para FastAPI:8001; Rails dados acessíveis apenas via reexposição Python | PLATFORM_MAP §H5; routes.rb |
| A-02 | F1 | **Audit trail ausente no path agent** — busca via chat não passa por AuditService; apenas REST endpoint /search/local audita | query_tools.py (inteiro) |
| A-03 | F1 | **Fairness ausente nos resultados de ranking** — WRF score sem passo de fairness check pós-ranking | query_tools.py:178+ |
| A-04 | F2 | **interview_session_store in-memory** — reinicialização do processo apaga sessões ativas sem persistência Redis/DB | wsi/sessions.py |
| A-05 | F2 | **Fallback hardcoded de 2 perguntas** — quando job tem 0 perguntas configuradas e pipeline falha; avaliação sem validade científica | wsi_interview_graph.py:800-815 |
| A-06 | F3 | **Respostas do candidato sem persistência DB** — Redis TTL 48h; expiração silenciosa sem audit trail permanente | wsi_async_session_service.py:119 |
| A-07 | F3 | **Technical skill classification hardcoded** — Java, Kotlin, Swift, Rust, Ruby classificados como comportamentais; WSI distorcido | score_calculator.py:34 |
| A-08 | F3 | **total_questions sempre zero / current_question sempre None** — UI não pode exibir perguntas via endpoint async | wsi_async.py:68, submit_answer:is_complete |
| A-09 | F3 | **communication_tools.py não despacha** — send_email/send_whatsapp retornam mock sem chamar CommunicationDispatcher | communication_tools.py:~100 |
| A-10 | F4 | **WhatsApp sem webhook de delivery** — Twilio não tem confirmação de entrega persistida no DB | ausência de twilio_status_webhooks.py |
| A-11 | F4 | **matrix_entry.requires_approval não-bloqueante** — L3 Human Review Gate logado mas não enforced em TransitionDispatchService | transition_dispatch_service.py:~115 |
| A-12 | F4 | **UNSUBSCRIBE_HMAC_SECRET efêmero** — se não configurado, restart invalida todos os links de unsubscribe ativos; LGPD gap | communication_optout.py:28 |
| A-13 | F5 | **Sem domain message para scheduling** — DomainOrchestrator não cria Message Rails para scheduling; sem histórico de auditoria | src/domains/orchestrator.py:181-268 |
| A-14 | F5 | **Checkpointer degradado sem Redis** — sessão de agendamento perde estado em restart de worker | graph.py:656-663 |
| A-15 | F6 | **Dois stores de memória sem sincronização** — ConversationSession (Hub/Redis) e domain memories (in-context) podem divergir | hub/session.py:124-128 |
| A-16 | F6 | **Redis armazena PII sem criptografia** — histórico de sessão com nomes/emails de candidatos em plaintext | hub/session.py:277-279 |
| A-17 | F6 | **Nenhuma mensagem Rails para queries hub** — histórico de chat não persiste no banco Rails para domínios não-sourcing | orchestrator.py:181-268 |
| A-18 | F7 | **trigger_automation rota não registrada** — automações pós-publicação silenciosamente ignoradas | ats-api-copia/config/routes.rb |
| A-19 | F7 | **WSIScreeningPipeline ImportError silencioso** — screening pode não ser ativado sem erro visível ao recruiter | sprint-1a/02_publish_node_rails_integration.py:169 |
| A-20 | F7 | **AuditService.log_output() non-blocking** — decisões do wizard podem não ser auditadas sob falha de DB | lia-hardening/auditing/audit_service_patch.py:80 |
| A-21 | F7 | **Mapeamento company_id ↔ account_id não documentado** — AI Layer envia X-Company-ID; Rails usa account_id do JWT; sem FK cruzada | sprint-1a/02_publish_node_rails_integration.py:31 |
| A-22 | F8 | **Frontend não conectado ao Rails** — dados de RecruitmentCampaign, SelectiveProcess, Interview indisponíveis para analytics | NEXT_PUBLIC_RAILS_URL comentado |

### 🟡 MÉDIO

| ID Canônico | Flows Afetados | Descrição | Arquivo:Linha |
|---|---|---|---|
| M-01 | F1 | **Timeout ausente no ReAct loop** — sem timeout em agent.process(); WS pode ficar pendurado até 300s keepalive | sourcing_react_agent.py |
| M-02 | F2 | **HITL para WSI sem timeout de notificação** — avaliação fica "travada" sem notificação ao recruiter após expiração | hitl_service.py |
| M-03 | F2 | **Bias no pipeline de geração de perguntas** — WSIScreeningPipeline gera via LLM sem FairnessGuard | wsi_screening_pipeline.py |
| M-04 | F3 | **Duplicate WSI_PASS_THRESHOLD** — definido em _shared.py:511 e wsi_deterministic_scorer.py:WSI_CUTOFFS; risco de dessincronização | automation/_shared.py:511 |
| M-05 | F4 | **Sending hours sem fila de retry** — mensagens bloqueadas retornam falha sem agendamento | communication_service.py:152 |
| M-06 | F4 | **Circuit breaker in-memory** — MAILGUN_CIRCUIT e RESEND_CIRCUIT perdem estado no restart | resilience/circuit_breaker.py |
| M-07 | F5 | **Timezone naive em _parse_date_time_pt** — datetime.now() sem tzinfo → horários errados fora de America/Sao_Paulo | graph.py:433-501 |
| M-08 | F5 | **PII em payload de calendar event** — candidate_email/name em plaintext para API externa (MS Graph/Google) | graph.py:329-345 |
| M-09 | F6 | **CircuitBreaker ausente no HubOrchestrator** — LLM failures sem fallback automático | hub/orchestrator.py |
| M-10 | F6 | **SessionStore session_id = user_id** — risco de colisão cross-tenant se user_ids não são UUID globalmente únicos | orchestrator.py:47 |
| M-11 | F6 | **mask_pii parcial** — tool outputs e pending_action payloads em PG sem mascaramento | hub/session.py:109-118 vs pending_action_store.py |
| M-12 | F7 | **/v1/users/recruitment_slas não registrado** — SLAs de campanha não criados | ats-api-copia/config/routes.rb |
| M-13 | F7 | **APIFY_API_KEY e SERP_API_KEY ausentes** — salary/market benchmark usa dados estáticos | .env (DIAG §Feature 1) |
| M-14 | F7 | **ENABLE_UNIFIED_WIZARD sem default documentado** — fallback para domain legado sem notificação | sprint-1a/01_supervisor_routing_patch.py:62 |
| M-15 | F7 | **create_default_selective_processes usa Current.user** — se nil, pipeline de 5 etapas não criado | ats-api-copia/app/models/job.rb:17 |
| M-16 | F8 | **PersonalizationContext não injetada** — reports idênticos para todos os recrutadores | recruiter_personalization_service.py / system_prompt_builder.py |
| M-17 | F8 | **RAG pipeline não exposto como tool** — busca semântica indisponível para analytics | app/api/v1/rag_search.py |
| M-18 | F8 | **panel_update → LiaFloatProvider wiring não confirmado** — relatórios podem não abrir painel dinâmico | ws_manager.py / lia-float-context.tsx |
| M-19 | F8 | **Predict time-to-fill heurístico** — rule-based sem dados históricos reais por empresa | app/domains/analytics/services/ |
| M-20 | F8 | **Prometheus removido (Task #138)** — métricas de hit rate e latências do router não exportadas | app/orchestrator/cascaded_router.py |

### 🟢 BAIXO

| ID Canônico | Flows Afetados | Descrição | Arquivo:Linha |
|---|---|---|---|
| B-01 | F4 | **ConsentEvent sem FK para Candidate** — subject_email como string sem FK; risco se email mudar | optout_repository.py:65 |
| B-02 | F6 | **USE_SUPERVISOR = False hardcoded** — impossível ligar supervisor LangGraph em prod sem code change | hub/orchestrator.py:18 |
| B-03 | F8 | **RAGAS avaliação batch diário** — qualidade degradada não detectada em tempo real | ragas_evaluation_service.py |

---

## APPENDIX B — COBERTURA DO PROTOCOLO P02

| Critério de Validação | Status | Evidência |
|---|---|---|
| Todos os 8 fluxos mapeados com sequência de chamadas | ✓ | Flows 1-8 documentados com arquivos:linhas |
| Evidências específicas de arquivo:linha preservadas | ✓ | ~120 referências de arquivo:linha preservadas das fontes |
| Cross-cutting concerns documentados por flow | ✓ | Fairness, LGPD, Bias, Error handling em cada flow |
| Matriz de integração verificada (8 dimensões) por flow | ✓ | Agente→Tool→Backend→Banco→Externo→Frontend→TenantIso→Audit |
| Status geral determinado por flow | ✓ | FUNCIONAL / PARCIALMENTE FUNCIONAL / BLOQUEADO |
| Gaps deduplicados no Appendix A | ✓ | 12 CRÍTICOS + 22 ALTOS + 20 MÉDIOS + 3 BAIXOS = 57 total |
| Gaps Rails-Frontend descoplamento mencionado em flows relevantes | ✓ | F1, F2, F5, F6, F7, F8 — consolidado em A-01 |
| Severidade conforme escala definida | ✓ | 4 níveis: CRÍTICO/ALTO/MÉDIO/BAIXO |
| Gaps per-flow referenciam IDs canônicos do Appendix A | ✓ | IDs F*-G* mapeiam para C-*, A-*, M-*, B-* |
| Formato de cada flow conforme template P02 | ✓ | Sequência → Cross-Cutting → Integração → GAPS |
