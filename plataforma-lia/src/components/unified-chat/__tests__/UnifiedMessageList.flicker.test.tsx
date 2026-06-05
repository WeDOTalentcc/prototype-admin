// Sensor (2026-06-05) — guarda o fix do flicker "resposta anterior some".
// Bug: o hold reasoning-first escondia a ULTIMA resposta LIA (=_newestLiaId)
// durante o "pensando" de uma NOVA pergunta, porque a nova ainda nao chegou.
// Fix: baseline (msg mais nova no inicio do turno) — so a resposta NOVA e segura.
// Este teste rerenderiza isThinking false->true e exige que o texto anterior fique.
import React from "react"
import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen } from "@testing-library/react"

vi.mock("next-intl", () => ({ useTranslations: () => (k: string) => k }))
vi.mock("@/lib/render-markdown", () => ({ renderMarkdown: (s: string) => s }))
vi.mock("@/hooks/chat/useTypewriter", () => ({
  useTypewriter: (text: string) => ({ displayed: text }),
}))
vi.mock("@/components/chat/plan-progress-card", () => ({ PlanProgressCard: () => null }))
vi.mock("@/components/unified-chat/FlowStepMessage", () => ({ default: () => null }))
vi.mock("@/components/notifications/weekly-digest-chat-message", () => ({
  WeeklyDigestChatMessage: () => null,
}))
vi.mock("@/components/unified-chat/AgentActivityTimeline", () => ({
  AgentActivityTimeline: () => null,
}))
vi.mock("@/components/unified-chat/AgentActivitySummary", () => ({
  AgentActivitySummary: () => null,
}))
vi.mock("@/components/unified-chat/ResponseBlockRenderer", () => ({
  ResponseBlockRenderer: () => null,
}))
vi.mock("@/services/lia-api/feedback-api", () => ({ submitThumbsFeedback: vi.fn() }))
vi.mock("@/lib/toast", () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

beforeEach(() => {
  if (!("scrollIntoView" in HTMLElement.prototype)) {
    HTMLElement.prototype.scrollIntoView = vi.fn() as unknown as () => void
  }
})

import { UnifiedMessageList } from "../UnifiedMessageList"
import type { LiaChatMessage } from "@/hooks/chat/use-lia-chat-connection"

const PREV = "RESPOSTA_ANTERIOR_VISIVEL"

function makeMessages(): LiaChatMessage[] {
  return [
    { id: "u-1", sender: "user", content: "primeira pergunta", timestamp: "12:00" },
    { id: "a-1", sender: "lia", content: PREV, timestamp: "12:00" },
  ]
}

function props(isThinking: boolean) {
  return {
    mode: "sidebar" as const,
    messages: makeMessages(),
    isStreaming: false,
    streamingContent: "",
    isThinking,
    thinkingSteps: [],
    userName: "Test",
    conversationId: "conv-1",
  }
}

describe("UnifiedMessageList — flicker guard", () => {
  it("mantem a resposta LIA anterior visivel quando uma nova pergunta inicia (isThinking)", () => {
    const { rerender } = render(<UnifiedMessageList {...props(false)} />)
    expect(screen.getByText(PREV)).toBeTruthy()

    // Nova pergunta: isThinking liga, mas a resposta nova AINDA nao chegou.
    // Bug antigo: o texto anterior sumia aqui. Fix: ele permanece.
    rerender(<UnifiedMessageList {...props(true)} />)
    expect(screen.getByText(PREV)).toBeTruthy()
  })
})
