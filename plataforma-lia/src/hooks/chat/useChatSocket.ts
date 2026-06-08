"use client";
import type { ResponseBlock } from "@/types/rrp-blocks";

/**
 * useChatSocket — WebSocket connection management and event handling for LIA chat.
 *
 * Manages: WS auth token, streaming connection, event dispatch (HITL, panels,
 * background tasks, plan progress, thinking steps, fairness warnings).
 */

import {
  type StreamingEvent,
  useAgentStreaming,
} from "@/hooks/ai/use-agent-streaming";
import { useCallback, useEffect, useRef, useState } from "react";
import type {
  BackgroundTaskEvent,
  HITLPending,
  MessageCompleteExtras,
  PanelUpdateEvent,
} from "./lia-chat-connection-types";
import type { TransportMode } from "./useChatTransport";

export interface UseChatSocketOptions {
  sessionId: string;
  onMessageComplete?: (
    content: string,
    executionPlan?: Record<string, unknown>,
    extras?: MessageCompleteExtras,
  ) => void;
  onPanelUpdate?: (event: PanelUpdateEvent) => void;
}

export interface UseChatSocketReturn {
  tokens: string;
  isStreaming: boolean;
  isConnected: boolean;
  isReconnecting: boolean;
  reconnectAttempt: number;
  error: string | null;
  transportMode: TransportMode;
  connect: () => void;
  disconnect: () => void;
  wsSend: (
    content: string,
    context: Record<string, unknown>,
    domain: string,
  ) => boolean;
  sendRaw: (data: Record<string, unknown>) => void;
  /** Task #383 (F2): bumped on every WS event recebido. useChatMessages usa
   *  pra detectar "send aceito mas zero respostas" e cair pro REST. */
  wsEventTickRef: React.MutableRefObject<number>;
  clearTokens: () => void;
  sendMessageViaSSE: (
    sessionId: string,
    message: string,
    domain?: string,
    context?: Record<string, unknown>,
    conversationId?: string | null,
  ) => void;

  hitlPending: HITLPending | null;
  hitlRef: React.MutableRefObject<HITLPending | null>;
  setHitlPending: React.Dispatch<React.SetStateAction<HITLPending | null>>;
  thinkingSteps: string[];
  isThinking: boolean;
  setIsThinking: React.Dispatch<React.SetStateAction<boolean>>;
  fairnessWarnings: string[];
  setFairnessWarnings: React.Dispatch<React.SetStateAction<string[]>>;
  backgroundTasks: BackgroundTaskEvent[];
  setBackgroundTasks: React.Dispatch<
    React.SetStateAction<BackgroundTaskEvent[]>
  >;
  planProgressSteps: Array<{
    task_id: string;
    action_id: string;
    domain_id: string;
    status: string;
  }>;
  activePlanId: string | null;

  conversationIdFromWs: string | null;
}

export function useChatSocket({
  sessionId,
  onMessageComplete,
  onPanelUpdate,
}: UseChatSocketOptions): UseChatSocketReturn {
  const [hitlPending, setHitlPending] = useState<HITLPending | null>(null);
  const hitlRef = useRef<HITLPending | null>(null);
  const onCompleteRef = useRef(onMessageComplete);
  const onPanelUpdateRef = useRef(onPanelUpdate);

  const [planProgressSteps, setPlanProgressSteps] = useState<
    Array<{
      task_id: string;
      action_id: string;
      domain_id: string;
      status: string;
    }>
  >([]);
  const [activePlanId, setActivePlanId] = useState<string | null>(null);
  const [thinkingSteps, setThinkingSteps] = useState<string[]>([]);
  // (2026-06-05) Marca de fim-de-turno: começa `true` para que a PRIMEIRA
  // atividade de cada turno LIMPE os passos do turno anterior (antes não havia
  // reset → "understanding/composing" acumulavam entre turnos e dentro do turno
  // a cada iteração do agentic_loop). Vira `false` na 1ª atividade do turno e
  // volta a `true` no `message`/`error`. Não limpamos no fim do turno para o
  // card persistir durante o hand-off gracioso até o próximo turno começar.
  const turnClosedRef = useRef(true);
  const [isThinking, setIsThinking] = useState(false);
  const [fairnessWarnings, setFairnessWarnings] = useState<string[]>([]);
  const [backgroundTasks, setBackgroundTasks] = useState<BackgroundTaskEvent[]>(
    [],
  );
  const [wsAuthToken, setWsAuthToken] = useState<string | undefined>(undefined);
  const [conversationIdFromWs, setConversationIdFromWs] = useState<
    string | null
  >(null);
  // Task #383 (F2): contador monotônico bumpado a cada evento WS recebido.
  // useChatMessages tira snapshot antes do wsSend e checa após N segundos —
  // se o tick não mudou, o send foi engolido e ele cai pro REST.
  const wsEventTickRef = useRef(0);
  // Gap #3: snapshot da atividade do turno atual; anexada a metadata da
  // mensagem final e limpa a cada `message`.
  const agentActivityBufferRef = useRef<
    Array<{ kind: string; name: string; status: string; durationMs?: number }>
  >([]);

  useEffect(() => {
    // BUG-AUDIT #277 / H2a+H4: o ws-token pode demorar (cold-start backend do
    // dev-auto-login até 15s) ou cair em 503 transitório — sem retry o header
    // Authorization ficava undefined pra sempre nessa instância, bloqueando
    // WS e SSE. Fazemos retry curto com backoff; enquanto isso o REST cobre.
    let cancelled = false;
    const maxAttempts = 3;
    const baseDelay = 1500;

    const attempt = async (n: number): Promise<void> => {
      if (cancelled) return;
      try {
        const r = await fetch("/api/auth/ws-token");
        if (cancelled) return;
        if (r.ok) {
          const data = (await r.json()) as { token?: string };
          if (!cancelled && data?.token) {
            setWsAuthToken(data.token);
            return;
          }
        }
        // 401 definitivo → não insistir (sem credenciais)
        if (r.status === 401) return;
      } catch (err) {
        if (cancelled) return;
        console.warn(
          "[useChatSocket] ws-token fetch failed (attempt",
          n + 1,
          ")",
          err,
        );
      }
      if (n + 1 < maxAttempts && !cancelled) {
        setTimeout(() => {
          void attempt(n + 1);
        }, baseDelay * Math.pow(2, n));
      }
    };

    void attempt(0);
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    onCompleteRef.current = onMessageComplete;
  }, [onMessageComplete]);
  useEffect(() => {
    onPanelUpdateRef.current = onPanelUpdate;
  }, [onPanelUpdate]);

  const handleEvent = useCallback((event: StreamingEvent) => {
    // Task #383 (F2): só contam eventos que provam que o backend RECEBEU e
    // está RESPONDENDO ao último `message` enviado. `pong` (keep-alive) e
    // outros eventos de housekeeping NÃO suprimem o watchdog — senão um
    // socket "vivo mas surdo" continuaria escondendo o silent drop.
    const RESPONSE_RELEVANT_EVENTS: ReadonlySet<string> = new Set([
      "thinking",
      "token",
      "token_done",
      "message",
      "clarification",
      "error",
      "approval_required",
      "approval_confirmed",
      "plan_progress",
      "panel_update",
      "background_task_update",
      "tool_started",
      "tool_finished",
      "reasoning_step",
    ]);
    if (RESPONSE_RELEVANT_EVENTS.has(event.type)) {
      wsEventTickRef.current += 1;
    }
    switch (event.type as string) {
      case "thinking":
        setIsThinking(true);
        if (event.content) {
          const _content = event.content as string;
          const _reset = turnClosedRef.current;
          if (_reset) turnClosedRef.current = false;
          setThinkingSteps((prev) => {
            const base = _reset ? [] : prev;
            return base.includes(_content) ? base : [...base, _content];
          });
        }
        break;

      case "plan_progress": {
        const planEvent = event as unknown as Record<string, unknown>;
        const planEventType = planEvent.event as string;
        if (planEventType === "plan_started") {
          setActivePlanId((planEvent.plan_id as string) || null);
          setPlanProgressSteps([]);
        } else if (
          planEventType === "step_running" ||
          planEventType === "step_completed" ||
          planEventType === "step_skipped"
        ) {
          setPlanProgressSteps((prev) => {
            const taskId = planEvent.task_id as string;
            const existing = prev.findIndex((s) => s.task_id === taskId);
            const step = {
              task_id: taskId,
              action_id: (planEvent.action_id as string) || "",
              domain_id: (planEvent.domain_id as string) || "",
              status:
                planEventType === "step_running"
                  ? "running"
                  : planEventType === "step_skipped"
                    ? "skipped"
                    : (planEvent.status as string) || "completed",
            };
            if (existing >= 0) {
              const updated = [...prev];
              updated[existing] = step;
              return updated;
            }
            return [...prev, step];
          });
        } else if (planEventType === "plan_completed") {
          setActivePlanId(null);
        }
        break;
      }

      case "approval_required": {
        const pending: HITLPending = {
          pendingId: event.pending_id ?? "",
          threadId: event.thread_id ?? "",
          action: event.action ?? "",
          description: event.description ?? "",
          data: event.data ?? {},
        };
        hitlRef.current = pending;
        setHitlPending(pending);
        window.dispatchEvent(
          new CustomEvent("hitl:approval_required", {
            detail: {
              pending_id: event.pending_id,
              thread_id: event.thread_id,
              action: event.action,
              description: event.description,
              data: event.data,
              domain: (event as Record<string, unknown>).domain ?? "",
              ws_session_id: sessionId,
              requested_at: new Date().toISOString(),
            },
          }),
        );
        break;
      }

      case "approval_confirmed":
        // Task #1110 — clear the HITL card explicitly so tabs receiving
        // the cross-tab broadcast (`broadcast_to_user` from
        // agent_chat_ws.py) hide the stale "pendente" card without
        // waiting for an F5. CRITICAL: only clear when the resolved
        // pending_id matches the local one — otherwise an
        // `approval_confirmed` broadcast from a DIFFERENT conversation
        // (same recruiter, two unrelated chats open) would wipe a
        // legitimate local pending. The originating tab still clears via
        // the subsequent `message` (hitl_resume) event regardless, so
        // this guard is purely a safety net for the broadcast path.
        if (
          event.pending_id &&
          hitlRef.current?.pendingId === event.pending_id
        ) {
          hitlRef.current = null;
          setHitlPending(null);
        }
        window.dispatchEvent(
          new CustomEvent("hitl:approval_resolved", {
            detail: { pending_id: event.pending_id },
          }),
        );
        break;

      case "wizard_stage": {
        // Bridge backend wizard stage payloads (ws_stage_payload) to the
        // job-wizard WizardContext via a window event. Subscribers (the
        // WizardProvider) hydrate stage-specific state such as the
        // FairnessGuard `dropped_questions` / `fairness_warning` so the
        // wizard banner reflects what the backend actually sent.
        if (typeof window !== "undefined") {
          const wsEvent = event as unknown as Record<string, unknown>;
          // Onda 2 (PLAN_FIX_wizard_memory_loss 2026-05-10): forward thread_id
          // from the WS event so useWizardFlow can persist the LangGraph
          // checkpointer thread and recover the session across refresh / HITL.
          window.dispatchEvent(
            new CustomEvent("lia:wizard-stage-payload", {
              detail: {
                type: "wizard_stage",
                thread_id: wsEvent.thread_id,
                stage: wsEvent.stage,
                data: (wsEvent.data as Record<string, unknown>) || {},
                completeness: (wsEvent.completeness as number) ?? 0,
                requires_approval: Boolean(wsEvent.requires_approval),
              },
            }),
          );
        }
        break;
      }

      case "panel_update": {
        const panelEvent = event as unknown as Record<string, unknown>;
        onPanelUpdateRef.current?.({
          panel_type: (panelEvent.panel_type as string) || "",
          panel_data: (panelEvent.panel_data as Record<string, unknown>) || {},
          panel_title: panelEvent.panel_title as string | undefined,
          action: (panelEvent.action as "open" | "update" | "close") || "open",
        });
        break;
      }

      case "background_task_update": {
        const bgEvent = event as unknown as Record<string, unknown>;
        const taskUpdate: BackgroundTaskEvent = {
          task_id: (bgEvent.task_id as string) || "",
          task_type:
            (bgEvent.task_type as BackgroundTaskEvent["task_type"]) ||
            "analysis",
          label: (bgEvent.label as string) || "",
          status:
            (bgEvent.status as BackgroundTaskEvent["status"]) || "running",
          progress: bgEvent.progress as number | undefined,
          message: bgEvent.message as string | undefined,
          result: bgEvent.result as Record<string, unknown> | undefined,
        };
        setBackgroundTasks((prev) => {
          const idx = prev.findIndex((t) => t.task_id === taskUpdate.task_id);
          if (idx >= 0) {
            const updated = [...prev];
            updated[idx] = taskUpdate;
            return updated;
          }
          return [...prev, taskUpdate];
        });
        break;
      }

      case "tool_started":
      case "tool_finished":
      case "reasoning_step": {
        // Fase 1 (2026-06-03): live agent activity. Push a readable line into
        // the existing thinking surface AND dispatch a decoupled window event
        // (`lia:agent-activity`) that the Fase 3 timeline component subscribes
        // to. Mirrors the wizard_stage / hitl:* window-event idiom.
        const actEvent = event as unknown as Record<string, unknown>;
        setIsThinking(true);
        const _name = (actEvent.name as string) || "ferramenta";
        const label =
          event.type === "reasoning_step"
            ? (actEvent.label as string) || "Raciocinando\u2026"
            : event.type === "tool_started"
              ? `\ud83d\udd27 ${_name}\u2026`
              : `\u2713 ${_name}`;
        // Reset no 1º passo de um novo turno + dedupe: o agentic_loop reemite
        // a mesma fase ("understanding"/"composing") a cada iteração; sem isto
        // o card mostrava as fases repetidas N vezes e acumuladas entre turnos.
        const _resetTurn = turnClosedRef.current;
        if (_resetTurn) turnClosedRef.current = false;
        setThinkingSteps((prev) => {
          const base = _resetTurn ? [] : prev;
          return base.includes(label) ? base : [...base, label];
        });
        if (event.type === "tool_finished") {
          agentActivityBufferRef.current.push({
            kind: "tool",
            name: _name,
            status: (actEvent.status as string) === "error" ? "error" : "ok",
            durationMs:
              typeof actEvent.duration_ms === "number"
                ? (actEvent.duration_ms as number)
                : undefined,
          });
        } else if (event.type === "reasoning_step") {
          // Dedupe por fase no buffer persistido (vira message.metadata.
          // agent_activity -> AgentActivitySummary): o agentic_loop reemite a
          // mesma fase a cada iteração; sem isto o resumo histórico repetia
          // "understanding"/"composing" N vezes. Buffer é resetado por turno.
          const _phase = (actEvent.label as string) || "";
          const _dup = agentActivityBufferRef.current.some(
            (a) => a.kind === "reasoning" && a.name === _phase,
          );
          if (!_dup) {
            agentActivityBufferRef.current.push({
              kind: "reasoning",
              name: _phase,
              status: "ok",
            });
          }
        }
        if (typeof window !== "undefined") {
          window.dispatchEvent(
            new CustomEvent("lia:agent-activity", { detail: { ...actEvent } }),
          );
        }
        break;
      }

      case "message":
        setIsThinking(false);
        turnClosedRef.current = true;
        hitlRef.current = null;
        setHitlPending(null);
        if (
          (event as any).conversation_id &&
          typeof (event as any).conversation_id === "string"
        ) {
          setConversationIdFromWs((event as any).conversation_id);
        }
        if (
          event.fairness_warnings &&
          (event.fairness_warnings as string[]).length > 0
        ) {
          setFairnessWarnings(event.fairness_warnings as string[]);
        } else {
          setFairnessWarnings([]);
        }
        if (event.content) {
          const eventRec = event as unknown as Record<string, unknown>;
          const execPlan = eventRec.execution_plan as
            | Record<string, unknown>
            | undefined;
          // PR-D — extrai ui_action / ui_action_params do payload WS para
          // que `lia-float-context` possa despachar via `useUIAction`.
          const uiAction =
            typeof eventRec.ui_action === "string"
              ? eventRec.ui_action
              : undefined;
          const uiActionParams =
            eventRec.ui_action_params &&
            typeof eventRec.ui_action_params === "object"
              ? (eventRec.ui_action_params as Record<string, unknown>)
              : undefined;
          const _activity = agentActivityBufferRef.current;
          const responseBlocks = Array.isArray(eventRec.response_blocks)
            ? (eventRec.response_blocks as ResponseBlock[])
            : undefined;
          const extras =
            uiAction || uiActionParams || _activity.length || responseBlocks
              ? {
                  ui_action: uiAction,
                  ui_action_params: uiActionParams,
                  agent_activity: _activity.length ? [..._activity] : undefined,
                  response_blocks: responseBlocks,
                }
              : undefined;
          agentActivityBufferRef.current = [];
          onCompleteRef.current?.(event.content, execPlan, extras);
        }
        break;

      case "error": {
        // BUG-AUDIT #277 / H7: garantir que "LIA digitando" sai quando
        // qualquer caminho (WS, SSE) reporta erro — sem isso o indicador
        // ficava preso ligado quando o stream quebrava antes do primeiro
        // evento "message".
        setIsThinking(false);
        turnClosedRef.current = true;
        // Harness fix (2026-06-06): NUNCA engolir o erro. O produtor
        // (agent_chat_sse.py / chat.py) ja manda uma mensagem clara
        // (ex: budget_exhausted → "Limite diario de uso de IA atingido...").
        // Surfacar como mensagem visivel ao usuario — sem isso um limite de
        // cota ou falha de LLM se disfarca de "chat morto". Mesmo caminho do
        // branch "clarification".
        const errEvent = event as unknown as {
          message?: string;
          error_code?: string;
        };
        const errMessage =
          errEvent.message?.trim() ||
          "Nao consegui responder agora. Tente novamente em instantes.";
        onCompleteRef.current?.(errMessage, undefined, {
          isError: true,
          errorCode: errEvent.error_code,
        });
        break;
      }

      case "clarification": {
        // Tier 8 fallback from cascaded_router — backend sends:
        // { type: "clarification", question: string, options: string[] | {label,value}[] }
        setIsThinking(false);
        turnClosedRef.current = true;
        const evt = event as unknown as {
          question?: string;
          options?: Array<string | { label?: string; value?: string }>;
        };
        const question = evt.question ?? "";
        const optionsArr = (evt.options ?? [])
          .map((opt) => {
            if (typeof opt === "string") return { label: opt, value: opt };
            return {
              label: opt.label ?? opt.value ?? "",
              value: opt.value ?? opt.label ?? "",
            };
          })
          .filter((o) => o.label && o.value);
        if (question) {
          onCompleteRef.current?.(question, undefined, {
            options: optionsArr,
            isClarification: true,
          });
        }
        break;
      }

      default:
        break;
    }
  }, []);

  const {
    tokens,
    isStreaming,
    isConnected,
    isReconnecting,
    reconnectAttempt,
    error,
    transportMode,
    connect,
    disconnect,
    sendMessage: _wsSendRaw,
    sendRaw,
    clearTokens,
    sendMessageViaSSE: _sendViaSSERaw,
  } = useAgentStreaming(sessionId, { authToken: wsAuthToken }, handleEvent);

  useEffect(() => {
    if (wsAuthToken && isConnected) {
      disconnect();
      setTimeout(() => connect(), 50);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [wsAuthToken]);

  // Fix reasoning bleed (2026-06-06): reseta thinkingSteps + turnClosedRef ao
  // ENVIAR nova mensagem (sinal inequivoco de novo turno). Sem isto, os passos
  // de turnos anteriores vazavam no expander "X passos" do turno atual (o reset
  // via turnClosedRef no fim do turno SSE nao era confiavel). Produtor unico.
  const wsSend = useCallback(
    (content: string, context: Record<string, unknown>, domain: string) => {
      setThinkingSteps([]);
      agentActivityBufferRef.current = [];
      turnClosedRef.current = true;
      return _wsSendRaw(content, context, domain);
    },
    [_wsSendRaw],
  );
  const sendMessageViaSSE = useCallback(
    (
      sid: string,
      message: string,
      domain?: string,
      context?: Record<string, unknown>,
      conversationId?: string | null,
    ) => {
      setThinkingSteps([]);
      agentActivityBufferRef.current = [];
      turnClosedRef.current = true;
      _sendViaSSERaw(sid, message, domain, context, conversationId);
    },
    [_sendViaSSERaw],
  );

  return {
    tokens,
    isStreaming,
    isConnected,
    isReconnecting,
    reconnectAttempt,
    error,
    transportMode,
    connect,
    disconnect,
    wsSend,
    sendRaw,
    clearTokens,
    sendMessageViaSSE,
    wsEventTickRef,
    hitlPending,
    hitlRef,
    setHitlPending,
    thinkingSteps,
    isThinking,
    fairnessWarnings,
    setFairnessWarnings,
    backgroundTasks,
    setBackgroundTasks,
    planProgressSteps,
    activePlanId,
    conversationIdFromWs,
    setIsThinking, // expor para que useChatMessages dispare o indicador "LIA digitando" também no caminho REST/SSE (BUG-13)
  };
}
