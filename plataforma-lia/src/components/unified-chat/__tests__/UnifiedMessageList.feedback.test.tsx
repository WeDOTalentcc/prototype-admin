/**
 * Task #570 — UI guards for the chat message actions.
 *
 * Coverage:
 *  1. The thumbs-down popover renders the three reason categories
 *     (`inaccurate`, `wrong_tone`, `hallucinated`) plus the textarea —
 *     the audit's UX requirement for qualitative signals.
 *  2. Persisted thumbs hydrate from `LiaChatMessage.thumbs` so a refresh
 *     doesn't blank out the user's prior rating (audit gap F3).
 *  3. Clicking the regenerate button calls the parent handler with the
 *     assistant message id (the supersede handshake's entry point).
 *
 * The component calls `useTranslations('chat.messageActions')` (see
 * `messages/{en,pt-BR}.json` → "chat.messageActions"). Each interaction below
 * is documented with the bare key name `t(<key>)` reads — the mock turns
 * those into raw strings so the assertions can match by identity.
 */
import React from "react"
import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"

// `useTranslations(namespace)` returns a function that takes a key and
// resolves to the translated string. The mock collapses both into the bare
// key (no namespace prefix) so the tests assert on the exact key used in
// the component, e.g. `t('thumbsDownReasonTitle')` → `"thumbsDownReasonTitle"`.
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

vi.mock("@/components/unified-chat/FlowStepMessage", () => ({
  default: () => null,
}))

vi.mock("@/components/notifications/weekly-digest-chat-message", () => ({
  WeeklyDigestChatMessage: () => null,
}))

import { UnifiedMessageList } from "../UnifiedMessageList"
import type { LiaChatMessage } from "@/hooks/chat/use-lia-chat-connection"
import { submitThumbsFeedback } from "@/services/lia-api/feedback-api"
import { toast } from "@/lib/toast"

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

  it("hydrates pre-existing thumbs state from message.thumbs (audit gap F3)", () => {
    // The chat-history loader populates `thumbs` on each LiaChatMessage from
    // the GET /lia/feedback/by-conversation hydration call. The action row
    // must reflect that on first render so a refresh doesn't blank out the
    // user's prior rating.
    const messages = makeMessages()
    messages[1] = { ...messages[1], thumbs: "up" }

    render(
      <UnifiedMessageList
        mode="sidebar"
        messages={messages}
        isStreaming={false}
        streamingContent=""
        isThinking={false}
        thinkingSteps={[]}
        userName="Test"
        conversationId="conv-1"
      />,
    )
    // When the thumbs-up is active the button switches to the active aria-label.
    expect(screen.getByRole("button", { name: "helpfulActiveAriaLabel" })).toBeTruthy()
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

  it("persists thumbs-up via conversationId and forwards the lia_response context (Task #1297)", () => {
    // Root-cause guard: the conversationId prop MUST reach the action row so
    // the POST actually fires, and the captured LIA text must travel as
    // message_context so the backend can learn from the real answer.
    vi.mocked(submitThumbsFeedback).mockClear()
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

    fireEvent.click(screen.getByRole("button", { name: "helpfulAriaLabel" }))
    expect(submitThumbsFeedback).toHaveBeenCalledWith("conv-1", "a-1", "up", {
      messageContext: { lia_response: "Aqui vai o status do pipeline." },
    })
  })

  it("fails loud (toast.error, no network call) when conversationId is missing (Task #1297)", () => {
    // canonical-fix: no silent fallback. Without a conversationId we cannot
    // persist, so the user is told instead of being shown a fake optimistic
    // success that never reaches the backend (the original dead-capture bug).
    vi.mocked(submitThumbsFeedback).mockClear()
    vi.mocked(toast.error).mockClear()
    render(
      <UnifiedMessageList
        mode="sidebar"
        messages={makeMessages()}
        isStreaming={false}
        streamingContent=""
        isThinking={false}
        thinkingSteps={[]}
        userName="Test"
        conversationId={null}
      />,
    )

    fireEvent.click(screen.getByRole("button", { name: "helpfulAriaLabel" }))
    expect(submitThumbsFeedback).not.toHaveBeenCalled()
    expect(toast.error).toHaveBeenCalled()
  })
})
