# Consolidacao: rotear a bolha pro supervisor (decisao Paulo 2026-06-04)
Branch: feat/benefits-prv-canonical. Continuacao de .planning/fase-a-supervisor-plan.md.

## Mapa de transportes do chat (CONFIRMADO no codigo, 2026-06-04)
| Superficie FE | Hook | Endpoint | Cerebro |
|---|---|---|---|
| chat-page | useChatPageHandlers (`/api/lia/chat/stream`) | chat.py `/chat/stream` → stream_message → _sse_via_orchestrator | **MainOrchestrator (SUPERVISOR + Phase 1.5 + handoffs)** |
| bolha (primario) | useLiaChatPanelState.wsSend → useChatSocket | `/api/v1/ws/chat/{session_id}` (agent_chat_ws) | CascadedRouter → agent.process (1 AGENTE) |
| bolha (fallback) | useChatTransport.sendMessageViaSSE | `/api/v1/chat/{session_id}/stream` (agent_chat_sse) | CascadedRouter → agent.process (1 AGENTE) |
| acoes/REST | useChatMessages | `/api/backend-proxy/chat/message` | (REST, nao-stream) |

CHAVE: SO o chat-page passa pelo supervisor. A bolha (WS+SSE) vai direto a 1 domain
agent via CascadedRouter — NAO ve os handoffs, NAO ve a Fase A, e o view_context que ela
ja recebe (context via getPageContext) vai pro agente roteado, nao pro supervisor.

Evidencia: agent_chat_ws.py linhas 1117-1141 (CascadedRouter) + 1262/1327 (agent.process);
agent_chat_sse.py 343-356 (CascadedRouter) + 542/552 (agent.process). chat.py SO tem
/chat/stream (stream_message → MainOrchestrator). Log live: SSEChat=0, MainOrchestrator=1.

## Objetivo da consolidacao
A bolha (WS + SSE) deve passar pelo MESMO supervisor (MainOrchestrator) que o chat-page.
Aposentar o caminho CascadedRouter→1-agente como roteador primario (vira fallback ou
sub-delegacao do supervisor). Assim P0.1 (view_context) + handoffs + Fase A valem em TODAS
as superficies — o "tudo pelo chat" de verdade.

## Feature-parity a cobrir (o que agent_chat_ws/sse fazem que o supervisor precisa ter)
Auditar antes de trocar (senao perde feature):
1. CascadedRouter routing (Tier 0.5 pre-route) — MainOrchestrator ja roteia internamente? confirmar.
2. Wizard session pin (should_pin_to_wizard) — MainOrchestrator tem deteccao de wizard? (vi refs a wizard no main_orchestrator; confirmar paridade).
3. Eventos de stream esperados pelo FE: token, clarification, panel update, message terminal,
   keepalive (502 fix _drain_queue_with_keepalive). MainOrchestrator/_sse_via_orchestrator
   emite os mesmos? (hoje _sse_via_orchestrator so emite token/_done/_error — GAP provavel
   em clarification/panel).
4. session_id semantics (WS usa session_id; /chat/stream usa conversation_id).
5. _llm_streaming_callback ContextVar (activity stream P0.3) — ja setado no agent_chat_sse;
   _sse_via_orchestrator tem seu proprio _streaming_callback.
6. Budget check / wizard timeout / keepalive.

## Estrategia (incremental, atras de flag)
- FASE 1 (parity audit): mapear os 6 itens acima — o que o supervisor ja cobre vs falta.
  Produzir tabela parity. (read-only, sem risco.)
- FASE 2 (backend): fazer agent_chat_sse (fallback, mais simples que WS) rotear pro
  MainOrchestrator quando flag `LIA_BUBBLE_VIA_SUPERVISOR=true`. Portar os event types
  faltantes (clarification/panel) pro _sse_via_orchestrator. TDD. Boot smoke.
- FASE 3 (backend): mesma coisa pro agent_chat_ws (WS primario) — mais complexo (transporte
  WS, keepalive). Atras da mesma flag.
- FASE 4: validar live (flag on) na bolha; comparar com chat-page. Curar/ajustar.
- FASE 5: flag default on; aposentar o caminho CascadedRouter→1-agente (ou rebaixar a
  sub-delegacao via handoff do supervisor).

## Riscos
- Eventos de stream divergentes → bolha pode quebrar (clarification/panel/keepalive). MITIGAR: portar event types ANTES de trocar; flag.
- Wizard flow (criacao de vaga) passa pela bolha? Se sim, parity de wizard pin e CRITICO.
- WS keepalive/502 em operacoes longas (WSI ~100s) — _sse_via_orchestrator tem keepalive? (provavel GAP).

## Proximo passo
FASE 1 (parity audit) — read-only, produz a tabela de paridade. So depois mexer em codigo.


---

## RESULTADO FASE 1 — TABELA DE PARIDADE (audit read-only, 2026-06-04)

Auditados: agent_chat_sse.py (bolha fallback), agent_chat_ws.py (bolha primario),
chat.py `_sse_via_orchestrator` + `stream_message` + `send_message`, main_orchestrator.py
`process` (-> ChatResponse).

### Descoberta-chave
O gap de event types NAO e estrutural — e de SERIALIZACAO. O `MainOrchestrator.process()`
retorna `ChatResponse` (main_orchestrator.py:168) que JA carrega tudo que a bolha precisa:
`actions`, `ui_action`/`ui_action_params` (=painel), `structured_data` (=panel_data),
`needs_params` (=clarification), `needs_confirmation`/`pending_action_id` (=HITL approval),
`fairness_warnings`, `suggested_prompts`, `conversation_id`, `error_code`/`error_category`.
O `_sse_via_orchestrator` recebe esse result rico no `_done` e DESCARTA todos os campos
exceto o texto. Alem disso, ja existe REST companion `POST /chat` -> `send_message`
(chat.py:249) que mapeia ui_action/workflow_data/search_results/intent/entities do
orch_result — logica reaproveitavel para a serializacao do stream.

Arquitetura atual real:
- chat-page = THIN stream (so texto via _sse_via_orchestrator) + REST estruturado (send_message).
- bolha = FAT stream (texto + painel + HITL + wizard + clarification, tudo no WS/SSE).

### Tabela (6 dimensoes)

| # | Dimensao | Bolha SSE | Bolha WS | Supervisor (_sse_via_orchestrator + MainOrchestrator) | Veredito |
|---|---|---|---|---|---|
| 1 | Routing | CascadedRouter + wizard pin -> 1 agente | idem (ws:1119-1141, agent.process ws:1326) | MainOrchestrator: roteamento multi-fase interno (Phase 0-2) + handoffs (Fase A). SUPERIOR ao CascadedRouter. | ✅ SEM GAP — e o objetivo (supervisor ganha) |
| 2 | Wizard pin | should_pin_to_wizard (Task #1080) ANTES do router (sse:343-348) | idem (ws:1104-1114) | Phase 1.4 _try_wizard_canonical + heuristica start patterns (mo:1046) + handler pin | ⚠️ PARIDADE PARCIAL — bolha usa helper canonico `should_pin_to_wizard`; supervisor usa heuristica propria. Risco de divergencia. Acao Fase 2/3: alinhar supervisor a chamar o MESMO produtor `should_pin_to_wizard` (fix no produtor) ou provar equivalencia. |
| 3 | Event types do stream | 10: thinking, token, token_done, message(rico), panel_update, tool_started, tool_finished, reasoning_step, error, keepalive | 14: +clarification, +approval_required/confirmed(HITL), +wizard_stage, +background_task_update, +plan_progress, +connected, +ping/pong | 3: token, [DONE], error. Info estruturada existe no ChatResponse mas e descartada. | 🔴 GAP PRINCIPAL (nao-estrutural). Portar emissao pos-_done reusando `chat_event_serializer.py` + logica de `send_message`. tool_*/keepalive sao exceção (ver #5,#6). |
| 4 | session_id vs conversation_id | session_id (path) controla tudo; conv_id passthrough | session_id (path); conv_id no context (ws:1356) | conversation_id (cria/recupera conversa no DB; chat.py:1007-1013) | ⚠️ Semantica diferente. Mapear session_id<->conversation_id ao rotear bolha pro supervisor (`derive_thread_id` ja existe). |
| 5 | Activity stream (_llm_streaming_callback / tool_*) | PRESENTE: ContextVar setado, emite tool_*/reasoning via llm.py (sse:562-563) | AUSENTE no WS (comentario ws:1255 confirma; usa StreamingCallback LangChain interno) | streaming_callback aceito por process() mas so trata token/token_done; tool events NAO repassados pelo _sse_via_orchestrator | 🔴 GAP = P0.3 (pendencia ja separada). Confirmar se commit 88c6bce27 (AgenticLoop emite via _llm_streaming_callback) ja cobre o lado producer; falta o _sse_via_orchestrator REPASSAR tool_started/finished. |
| 6 | Keepalive / budget / timeout | _drain_queue_with_keepalive (15s heartbeat, 502 fix WSI~100s) + check_budget + LLM_TIMEOUT | ping 300s + check_budget + _AGENT_TIMEOUT | timeout 60s na fila SEM keepalive + ai_credit_gate pre-check no process() | 🔴 GAP keepalive: ops longas (WSI ~100s) > 60s derrubam o stream do supervisor. Budget OK. Portar `_drain_queue_with_keepalive` (funcao existe na bolha). |

### Bug latente encontrado (P1) — corrigir junto da Fase 2
chat.py:953-956 — `_sse_via_orchestrator` le `result_obj.message`, mas `ChatResponse`
(main_orchestrator.py:168) tem campo `.content`, NAO `.message`. No caminho fallback
(quando full_response_parts esta vazio = sem streaming parcial) o texto vira "" e NADA e
emitido. Mascarado pelo streaming normal de tokens. Fix: `getattr(result_obj, "content", "")`.

### Plano FASE 2 revisado (risco menor que o supunha o plano original)
Ordem recomendada (agent_chat_sse primeiro = fallback mais simples; flag LIA_BUBBLE_VIA_SUPERVISOR):
1. Fix bug .message->.content + emitir evento `message` estruturado pos-_done reusando
   `chat_event_serializer.py` + a logica de mapeamento de `send_message`:
   actions, ui_action->panel_update, needs_params->clarification,
   needs_confirmation/pending_action_id->approval_required, fairness_warnings.
2. Portar `_drain_queue_with_keepalive` pro `_sse_via_orchestrator` (keepalive 502 fix).
3. Mapear session_id<->conversation_id (derive_thread_id) no roteamento da bolha.
4. tool_* (P0.3): confirmar produtor (88c6bce27) e repassar no callback do _sse_via_orchestrator.
5. Wizard pin (#2): alinhar supervisor ao helper canonico should_pin_to_wizard.
6. Flag-gate em agent_chat_sse: quando LIA_BUBBLE_VIA_SUPERVISOR=true, rotear pro MainOrchestrator. TDD + boot smoke.
FASE 3 (WS): + HITL (approval_required/confirmed), wizard_stage, plan_progress, background_task_update — maior superficie.

### Sensor proposto (harness — Fase 2)
Sensor computacional que falha se um campo novo de `ChatResponse` (main_orchestrator.py)
nao tiver mapeamento correspondente no serializer do `_sse_via_orchestrator` — previne
recidiva do gap "supervisor produz mas nao serializa". (warn -> blocking quando baseline=0.)


---

## PROGRESSO FASE 2 (2026-06-04)

Itens de NUCLEO feitos (melhoram o supervisor; default deixa o chat-page intocado):
- ✅ **Item 1 — serializacao estruturada** (commit `5c98d61b0`). `_sse_via_orchestrator`
  ganhou `emit_structured: bool = False`. Quando True (caminho bolha), helper puro
  `_orchestrator_result_to_frames(result, conversation_id)` serializa o ChatResponse em
  frames de paridade: `message` rico (actions/fairness/navigation via ui_action),
  `clarification` (needs_params), `approval_required` (needs_confirmation). Tokens em
  shape canonico + pass-through de tool_started/finished/reasoning_step/panel_update
  (P0.3). **Bug P1 corrigido**: lia `.content` (era `.message`). Default False =
  chat-page intocado. 5 testes deterministicos.
- ✅ **Item 2 — keepalive 502-fix** (commit `3f9ce02b0`). Loop antigo abortava apos 60s
  de silencio; WSI ~100s derrubava. Agora poll `keepalive_after_s`(15s)→`: keepalive`,
  aborta so apos `hard_timeout_s`(180s). 6o teste.

Sensor (feedback): `tests/contract/test_sse_supervisor_structured.py` (6 testes,
orchestrator mockado, roda headless). Regressao: test_chat_orchestrator_timeout +
test_sse_passthrough + test_reasoning_streaming verdes. APP BOOT OK (1863 rotas).

### GUIDE (feedforward) — produtor unico de serializacao do supervisor
`_orchestrator_result_to_frames` (chat.py) e o PONTO UNICO que serializa o ChatResponse
do MainOrchestrator em eventos de stream. Ao adicionar um campo de UI ao ChatResponse
(main_orchestrator.py:168) que a bolha precise renderizar, mapeie-o AQUI (e cubra com
um teste em test_sse_supervisor_structured.py). Nao reimplementar serializacao no
agent_chat_sse/ws — eles devem convergir para este produtor.

### Itens RESTANTES da Fase 2 (proxima etapa — VALIDACAO LIVE)
- **Item 6 — flag-gate da bolha** (`LIA_BUBBLE_VIA_SUPERVISOR`, default OFF): em
  agent_chat_sse, APOS o wizard pin (preserva wizard na bolha, evita divergencia #2),
  desviar o caminho auto/recruiter do CascadedRouter+agent.process para
  `MainOrchestrator.process` quando flag ON. Mapping session_id->conversation_id.
  Reusa o `_streaming_callback` da bolha (ja serializa tokens/tools = cobre item 4).
  RISCO: muda o transporte da bolha — infra testavel headless (mock), mas comportamento
  real (roteamento/delegacao) so valida LIVE (armadilha: headless nao roda domain agents
  /checkpointer). Default OFF = zero risco em prod; Paulo liga no preview (Fase 4).
- **Item 5 — wizard pin**: EVITADO pelo design do item 6 (desvio acontece depois do pin).
- **Item 4 — tool_* P0.3**: pass-through ja feito no _sse_via_orchestrator; producer
  (88c6bce27) a confirmar live.
- Depois: FASE 3 (agent_chat_ws, +HITL/wizard_stage/plan_progress) e FASE 4/5 (validar
  live, flag default on, aposentar CascadedRouter->1-agente).
