/**
 * Task #570 — UI guards for the chat message actions.
 *
 * Coverage:
 *  1. The thumbs-down popover renders the three reason categories
 *     (`inaccurate`, `wrong_tone`, `hallucinated`) plus the textarea —
 *     the audit's UX requirement for qualitative signals.
 *  2. Clicking the regenerate button calls the parent handler with the
 *     assistant message id (the supersede handshake's entry point).
 */
import React from "react"
import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

// The popover from Radix needs scrollIntoView in jsdom; stub it.
beforeEach(() => {
  if (!("scrollIntoView" in HTMLElement.prototype)) {
    HTMLElement.prototype.scrollIntoView = vi.fn() as unknown as () => void
  }
  if (!("hasPointerCapture" in HTMLElement.prototype)) {
    HTMLElement.prototype.hasPointerCapture = vi.fn(() => false) as unknown as (id: number) => boolean
    HTMLElement.prototype.releasePointerCapture = vi.fn() as unknown as (id: number) => void
    HTMLElement.prototype.setPointerCapture = vi.fn() as unknown as (id: number) => void
  }
})

vi.mock("@/services/lia-api/feedback-api", () => ({
  submitThumbsFeedback: vi.fn().mockResolvedValue({ feedback_id: "fb-1", status: "recorded" }),
}))

vi.mock("@/lib/toast", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}))

vi.mock("@/lib/render-markdown", () => ({
  renderMarkdown: (s: string) => s,
}))

vi.mock("@/components/chat/plan-progress-card", () => ({
  PlanProgressCard: () => null,
}))

vi.mock("@/components/chat/typing-indicator", () => ({
  TypingIndicator: () => null,
}))

vi.mock("@/components/workflow-rail/FlowStepMessage", () => ({
  default: () => null,
}))

vi.mock("@/components/notifications/weekly-digest-chat-message", () => ({
  WeeklyDigestChatMessage: () => null,
}))

import { UnifiedMessageList } from "../UnifiedMessageList"
import type { LiaChatMessage } from "@/hooks/chat/use-lia-chat-connection"

function makeMessages(): LiaChatMessage[] {
  return [
    {
      id: "u-1",
      sender: "user",
      content: "Como está o pipeline?",
      timestamp: "12:00",
    },
    {
      id: "a-1",
      sender: "lia",
      content: "Aqui vai o status do pipeline.",
      timestamp: "12:00",
    },
  ]
}

describe("UnifiedMessageList — message actions (Task #570)", () => {
  it("renders thumbs-down popover with the three reason categories and a textarea", () => {
    render(
      <UnifiedMessageList
        mode="sidebar"
        messages={makeMessages()}
        isStreaming={false}
        streamingContent=""
        isThinking={false}
        thinkingSteps={[]}
        userName="Test"
        conversationId="conv-1"
      />,
    )

    // Open the thumbs-down popover.
    const downBtn = screen.getByRole("button", { name: "notHelpfulAriaLabel" })
    fireEvent.click(downBtn)

    // The three category chips and the textarea are wired to i18n keys
    // that this test mocks to return the key itself.
    expect(screen.getByText("thumbsDownReasonTitle")).toBeTruthy()
    expect(screen.getByText("thumbsDownCategory.inaccurate")).toBeTruthy()
    expect(screen.getByText("thumbsDownCategory.wrong_tone")).toBeTruthy()
    expect(screen.getByText("thumbsDownCategory.hallucinated")).toBeTruthy()
    expect(screen.getByPlaceholderText("thumbsDownPlaceholder")).toBeTruthy()
  })

  it("invokes onRegenerate with the assistant message id when the regenerate button is clicked", () => {
    const onRegenerate = vi.fn()
    render(
      <UnifiedMessageList
        mode="sidebar"
        messages={makeMessages()}
        isStreaming={false}
        streamingContent=""
        isThinking={false}
        thinkingSteps={[]}
        userName="Test"
        conversationId="conv-1"
        onRegenerate={onRegenerate}
      />,
    )

    const regenBtn = screen.getByRole("button", { name: "regenerateAriaLabel" })
    fireEvent.click(regenBtn)
    expect(onRegenerate).toHaveBeenCalledWith("a-1")
  })
})
