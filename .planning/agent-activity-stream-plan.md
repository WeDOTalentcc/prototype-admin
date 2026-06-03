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

### Fase 1 — Eventos de tool-call (fundação, baixo risco)
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

### Fase 3 — Polish FE: timeline colapsável estilo Manus
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
