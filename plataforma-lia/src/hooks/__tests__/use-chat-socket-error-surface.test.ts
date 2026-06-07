/**
 * Harness fix (2026-06-06): eventos `error` do backend (budget_exhausted, LLM
 * failure, timeout, bloqueio de seguranca) NUNCA podem ser engolidos pelo chat.
 *
 * Bug observado: usuario mandava "oi" no chat unificado e nao recebia NADA --
 * a bolha "Pensando" sumia e nenhuma mensagem aparecia. Causa: o produtor
 * (agent_chat_sse.py) emitia {type:"error", message, error_code} corretamente,
 * mas o consumidor `useChatSocket` no `case "error"` so desligava o indicador
 * de digitacao e descartava `event.message`. Um limite de cota se disfarcava
 * de "chat morto".
 *
 * Contrato: ao receber um evento `error`, o socket DEVE surfacar a mensagem ao
 * usuario via `onMessageComplete(message, undefined, { isError: true, errorCode })`.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";

const h = vi.hoisted(() => ({
  onEvent: undefined as undefined | ((e: Record<string, unknown>) => void),
}));

vi.mock("@/hooks/ai/use-agent-streaming", () => ({
  useAgentStreaming: (
    _sessionId: string,
    _options: unknown,
    onEvent?: (e: Record<string, unknown>) => void,
  ) => {
    h.onEvent = onEvent;
    return {
      tokens: "",
      isStreaming: false,
      isConnected: false,
      isReconnecting: false,
      reconnectAttempt: 0,
      error: null,
      transportMode: "ws" as const,
      connect: vi.fn(),
      disconnect: vi.fn(),
      sendMessage: vi.fn(() => true),
      sendRaw: vi.fn(),
      clearTokens: vi.fn(),
      sendMessageViaSSE: vi.fn(),
    };
  },
}));

import { useChatSocket } from "../chat/useChatSocket";

describe("useChatSocket -- surfacar evento de erro ao usuario", () => {
  beforeEach(() => {
    h.onEvent = undefined;
  });

  it("budget_exhausted: entrega a mensagem do backend via onMessageComplete", () => {
    const onMessageComplete = vi.fn();
    renderHook(() => useChatSocket({ sessionId: "sess-err", onMessageComplete }));

    expect(h.onEvent).toBeTypeOf("function");

    const budgetMsg =
      "Limite diario de uso de IA atingido (10.000 / 10.000 tokens). O budget sera renovado a meia-noite UTC.";
    act(() => {
      h.onEvent!({
        type: "error",
        message: budgetMsg,
        error_code: "budget_exhausted",
      });
    });

    expect(onMessageComplete).toHaveBeenCalledTimes(1);
    const [content, execPlan, extras] = onMessageComplete.mock.calls[0];
    expect(content).toBe(budgetMsg);
    expect(execPlan).toBeUndefined();
    expect(extras).toMatchObject({ isError: true, errorCode: "budget_exhausted" });
  });

  it("erro generico sem message: entrega um fallback nao-vazio (nunca silencioso)", () => {
    const onMessageComplete = vi.fn();
    renderHook(() => useChatSocket({ sessionId: "sess-err2", onMessageComplete }));

    act(() => {
      h.onEvent!({ type: "error" });
    });

    expect(onMessageComplete).toHaveBeenCalledTimes(1);
    const [content, , extras] = onMessageComplete.mock.calls[0];
    expect(typeof content).toBe("string");
    expect((content as string).length).toBeGreaterThan(0);
    expect(extras).toMatchObject({ isError: true });
  });
});
