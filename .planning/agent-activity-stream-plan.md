# Plano: Display rico de atividade da IA (estilo Replit/Manus) no chat unificado

> Fonte da verdade para qualquer agente tocando o streaming de atividade do chat LIA.
> Criado 2026-06-03. Branch ativa: `feat/benefits-prv-canonical`.

## Problema (diagnóstico)

O chat unificado mostra só "IA está pensando..." e depois a resposta final. O agente
roda como caixa-preta: `_run_graph` usa `compiled.ainvoke(...)` (bloqueante), o
`StreamingCallback` só trata tokens de texto, e o único path com granularidade real
(`PlanExecutor`) tem bug de naming que impede status/progress de funcionar.

Defeito de **harness** (não de prompt): falta o SENSOR de observabilidade que transmite
o que o agente faz. Fix no **produtor único** (`StreamingCallback` + `chat_event_serializer`),
nunca nos consumidores de UI.

## Estado da arte (o que já existe)

- FE: `plan-progress-card.tsx`, `chat-status-indicators.tsx` (ThinkingIndicator + ProgressSteps),
  `action-result-card.tsx`, `agent-memory-indicator.tsx`. `ChatMessageList.tsx` já renderiza
  tipos `thinking/progress/command/file-creation/completion/flow/execution_plan/action_result`.
- Transporte: `use-agent-streaming.ts` → `useChatTransport` (WS + fallback SSE). Union
  `StreamingEventType` já inclui `plan_progress`, `panel_update`, `background_task_update`.
- Dados: `app/shared/execution/execution_plan.py` (`ExecutionPlan` + `AgentTask`).

## Decisão de arquitetura

Eventos de tool-call (`on_tool_start`/`on_tool_end`) **disparam durante o `ainvoke` atual** —
não exigem trocar para `astream` nem `streaming=True`. Basta estender o `StreamingCallback`
(já injetado no `config={"callbacks": [...]}` do grafo). Isso entrega ~80% do efeito sem o
refactor arriscado do `_run_graph`. `astream_events` fica para a Fase 2 (raciocínio ao vivo),
atrás de flag.

## Fases

### Fase 0 — Bug do plan_progress  ✅ FEITA (2026-06-03)
- Produtor `PlanExecutor` emite `plan_started/step_running/step_completed/step_skipped/plan_completed`.
- Consumidor `_ws_plan_progress` (agent_chat_ws.py) comparava contra `plan_complete`/`plan_error`
  (nunca emitidos) → status sempre "running", progress sempre 0.
- Fix: helper puro `app/shared/execution/plan_progress_mapper.py` (`map_plan_event` +
  `new_plan_progress_state`) + consumidor usa o helper.
- Sensor: `tests/contract/test_plan_progress_contract.py` (6 testes, verde). Pina nomes
  produtor↔mapper + regressão dos nomes buggados.

### Fase 1 — Eventos de tool-call  ✅ FEITA (2026-06-03)
- Estender `StreamingCallback` (libs/agents-core/lia_agents_core/streaming_callback.py):
  `on_tool_start`→`tool_started`, `on_tool_end`→`tool_finished`, `on_tool_error`,
  `on_agent_action`/`on_chain_start`→`reasoning_step`.
- Serializers novos em `app/shared/chat_event_serializer.py` (single source of truth —
  proibido dict `{"type": ...}` inline). PII via `mask_pii` nos args de tool.
- Wiring: garantir StreamingCallback no config do grafo mesmo com token-streaming OFF;
  nova flag `LIA_WS_AGENT_ACTIVITY` (default ON). Remover `context["streaming_callback"]`
  morto em agent_chat_ws.py:~143.
- FE: adicionar `tool_started/tool_finished/reasoning_step` ao `StreamingEventType` +
  render reusando ProgressSteps.
- Red test: `tests/contract/test_streaming_callback_tool_events.py`.

### Fase 2 — Raciocínio intermediário ao vivo (maior risco, atrás de flag)
- Trocar `ainvoke` por `astream_events(version="v2")` em `_run_graph` (langgraph_base.py:191),
  propagar node-a-node. Flag `LIA_WS_ASTREAM` (default OFF) + fallback automático para ainvoke.
- Cascade obrigatória: `feature-impact` (cross-agent, blast-radius alto).

### Fase 3 — Polish FE: timeline estilo Manus  ✅ FEITA (2026-06-03)
- `AgentActivityTimeline` agrupando reasoning_step + tool_started/finished. Estados
  live→done colapsado. Smoke test rerender (Rules-of-Hooks).

## Ordem: 0 → 1 → 3 → 2.

## Guide + Sensor (harness)

GUIDE (lia-agent-system/CLAUDE.md, seção "WS event contract"): todo evento WS novo DEVE ter
serializer em chat_event_serializer.py, entrar no union StreamingEventType (FE) e ter branch de
render OU estar em IGNORED_EVENTS. Nomes do produtor são canonical; consumidores nunca renomeiam.

SENSOR (lia-agent-system/scripts/check_ws_event_contract.py, futuro): cross-stack — extrai
event_types dos serialize_* e confere contra o union TS do FE. Exit 1 em drift, mensagem com fix.
Já entregue: test_plan_progress_contract.py (Fase 0).

## Débito técnico de harness
- context["streaming_callback"] (agent_chat_ws.py:~143) é código morto → remover na Fase 1.
- StreamingCallback acoplado à flag LIA_WS_TOKEN_STREAMING impede tool events → desacoplar (Fase 1).

---

## ADENDO CRÍTICO — caminho REAL do chat é o ORQUESTRADOR (REST), não o WS (descoberto 2026-06-03)

**Descoberta:** o display construído (Fase 0-3) foi instrumentado no caminho **WS/`LangGraphReActBase`** (`StreamingCallback`). Mas o chat de produção (3 estados: flutuante/lateral/full, todos via `LiaChatMessageList`) roda por **REST → `MainOrchestrator`** (`channel=rest` nos logs, `ACT-DBG`=0). Logo o `StreamingCallback` instrumentado NUNCA dispara nesse caminho. O FE (timeline + sumário nos 3 estados) está correto, mas o backend não emitia eventos pelo caminho certo.

**Arquitetura do caminho real:**
- `chat.py POST /chat` (linha 249) → JSON não-streaming (o que o chat usa hoje).
- `chat.py POST /chat/stream` (linha 977) → SSE (`StreamingResponse text/event-stream`, linha 1093) — EXISTE, FE não usa.
- `MainOrchestrator.process(streaming_callback=...)` → Fase 1 ActionExecutor / Fase 1.5 `AgenticLoop` / Fase 2 ReAct.
- Tools executadas no **`app/orchestrator/execution/agentic_loop.py`** (`AgenticLoop.run`, exec na linha ~255 `self._tool_executor.execute`).
- LLM com tools em `app/domains/ai/services/llm.py:_generate_with_tools_claude` (linha 611); streaming opt-in via ContextVar **`_llm_streaming_callback`** (linha 44) — quando setado, faz `client.messages.stream()` e empurra `{"type":"token",...}`.

**Bug pré-existente corrigido (não era nosso):** `ChatResponse.intent_detected` (str) recebia `OrchestratorIntentResult` em `from_action_result` → `ValidationError string_type` → "dificuldade para processar" (caminho pending-action pós-clarificação). Fix: `field_validator(mode="before")` coage via `str()` em `main_orchestrator.py`. Commit auto-checkpoint.

### Phase 1 ✅ FEITA (commit 88c6bce27)
`AgenticLoop` emite `tool_started`/`tool_finished` por tool (helper `_emit_activity` lê o ContextVar `_llm_streaming_callback` e empurra; fail-safe no-op em REST). 3 contract tests (`tests/contract/test_agentic_loop_activity.py`). ACT-DBG temp removido.

### Phase 2 ⏳ PENDENTE (transporte — gating pra Paulo VER ao vivo)
Hoje o chat usa `POST /chat` (JSON) → `_llm_streaming_callback` não é setado → emits da Phase 1 viram no-op → nada aparece ao vivo. Necessário:
1. **FE usar `/chat/stream` (SSE)** em vez de `/chat` (JSON) pra esse chat (`useChatTransport`/`useChatSocket` ou a chamada REST do float). Decisão: WS (`agent_chat_ws`, que JÁ usa StreamingCallback) OU SSE (`/chat/stream`, orquestrador). Como o chat real é orquestrador, **SSE `/chat/stream` é o caminho coerente**.
2. **Setar `_llm_streaming_callback` ContextVar** nesse caminho (modelo: `agent_chat_sse.py:534` já faz). Garantir que o `_streaming_callback` do `/chat/stream` (chat.py:~920) é setado no ContextVar antes do `main_orch.process`.
3. **FE consumir os eventos** — `useChatSocket` já trata `tool_started/finished/reasoning_step` (Fase 1 FE) e dispara `lia:agent-activity` → `AgentActivityTimeline` (já montado nos 3 estados). Confirmar que o transporte SSE do float passa pelo `useChatSocket` (que faz o dispatch).
4. **reasoning_step**: o texto já streama como tokens via `_generate_with_tools_claude`; opcional emitir `reasoning_step` explícito antes de cada batch de tools.

**Risco/esforço Phase 2:** médio-alto (toca transporte FE + wiring ContextVar). Não fazer no fim de sessão longa — merece execução focada + verificação no preview.

---

# PLANO SSE PONTA-A-PONTA (enterprise) — display de atividade da IA ao vivo (2026-06-04)

> Resultado da auditoria de 3 agentes (FE transport, backend SSE, compliance) sob harness-engineering + canonical-fix + compliance-risk. Abordagem B (push WS lateral) foi DESCARTADA empiricamente (ws_keys=[], sem WS aberta). SSE-e2e é o único caminho viável.

## DESCOBERTA-CHAVE
O FE (`useChatTransport.sendMessageViaSSE`) já mira **`POST /api/v1/chat/{session_id}/stream` = `agent_chat_sse.py:233`** — NÃO o `chat.py:/chat/stream`. Esse endpoint JÁ seta o ContextVar `_llm_streaming_callback` (liga tokens + emits do AgenticLoop) e JÁ aplica `mask_pii` em token. Trabalho é menor do que parecia.

## Cenário (file:line)
- FE consumo SSE pronto: `hooks/chat/useChatTransport.ts:397-542` (`sendMessageViaSSE`, fetch+ReadableStream, endpoint `/api/v1/chat/{id}/stream`). Switch de eventos `useChatSocket.ts:175-489` trata token/message/tool_started/finished/reasoning_step + dispara `lia:agent-activity` (`:395-399`) — roda idêntico em SSE e WS.
- FE gap: `useChatMessages.ts:372-409` — branch SSE é dead code (`transportMode` nunca = "sse"; só "ws"/"disconnected"). `sendMessageViaSSE` nunca é chamado.
- Backend pronto: `agent_chat_sse.py:233` (`/chat/{session_id}/stream`), seta ContextVar (~534-538), mask_pii em token (~523).
- Backend gap: `agent_chat_sse.py:518-531` `_streaming_callback` achata tudo ≠ token em `serialize_thinking` → perde shape de tool_started/finished.
- Produtor de eventos: `agentic_loop.py:_emit_activity` (~30) emite tool_started/finished (só metadata: name/status/duration — sem PII hoje). Tokens: `llm.py:_generate_with_tools_claude:643` (delta CRU, sem mask_pii no produtor).
- AgentActivityTimeline montado: `LiaChatMessageList.tsx:224` (3 estados).

## FASES (compliance-first, cada uma verificável no preview + reversível)

### Fase A — PII no produtor (P0, canonical-fix) [BACKEND]
- Mover `mask_pii` para o PRODUTOR: token em `llm.py:643` (antes do `_stream_cb`) + qualquer conteúdo em `_emit_activity` (`agentic_loop.py`). Garante que TODOS os transportes (chat.py SSE, agent_chat_sse, futuro) saem mascarados — não repetir fix-no-consumidor.
- `_emit_activity`: NUNCA emitir `tc.parameters`/`tool_result_content` crus. Só name/status/duration (já é assim — pinar com teste).
- Red test: `tests/contract/test_stream_pii_masking.py` — stream com CPF/telefone no texto → assert nenhum dígito cru sai. + paridade: texto concatenado dos `token` == saída mascarada do JSON.

### Fase B — repassar activity events no SSE [BACKEND]
- `agent_chat_sse.py:_streaming_callback`: adicionar branch que repassa `tool_started/finished/reasoning_step` preservando shape (via `serialize_*` do `chat_event_serializer`), em vez de achatar em `thinking`.
- Red test: `tests/contract/test_sse_passthrough.py` — callback recebe `{type:tool_started,name:X}` → assert sai no SSE com type+name (não vira thinking).

### Fase C — FE rotear pra SSE (atrás de flag) [FRONTEND]
- `useChatMessages.ts:sendMessage`: chamar `sendMessageViaSSE(...)` quando `NEXT_PUBLIC_CHAT_TRANSPORT=sse` (env), SEM depender de `transportMode==="sse"`. REST permanece fallback default (flag off = comportamento atual intocado).
- Adicionar fallback SSE→REST em `useChatTransport.ts:522` (hoje só emite error ao esgotar retry).
- Validar no preview: auth (ws-token presente), buffering em dev, frame `message` terminal idêntico ao WS, domain default.

### Fase D — verificação + sensores (harness) [AMBOS]
- Preview nos 3 estados: tokens incrementais + chips de tool (🔧→✓ + duração) + message final.
- Sensores: (1) contract stream↔JSON parity pós-mask; (2) sensor estático: todo emit de token/tool em `*sse*.py` + `_emit_activity` passa por mask_pii; (3) red test PII.

### Fase E (opcional) — reasoning_step ao vivo
- AgenticLoop emitir `_emit_activity({type:reasoning_step,...})` antes de cada batch de tools (não existe hoje). Texto via mask_pii.

## Riscos (mitigação)
- Formato terminal: SSE precisa emitir frame `message` idêntico ao WS senão `onMessageComplete` não dispara (bolha final some). → Fase B/C garantir `serialize_message` final.
- Auth: SSE bate direto no backend (não via proxy) — depende do ws-token. → validar; fallback REST.
- post_compliance pós-stream: hoje no-op de redação (ok). Se virar redator → streaming o contorna → exigirá hold-back. DÉBITO documentado.
- Flag default OFF → zero impacto no chat atual até validarmos.

## Ordem: A → B → C → D (→ E opcional). Flag mantém o chat atual intocado até a validação.
