/**
 * Sprint B.6 (P2-2 onboarding) — QuickReplies integration.
 *
 * Garante que LiaChatMessageList renderiza <QuickReplies/> inline quando
 * mensagem da LIA tem metadata.quick_reply_preset, e que click no botão
 * dispara handleChipSend com o value canonical.
 */

import React from "react"
import { render, screen, fireEvent } from "@testing-library/react"
import { describe, it, expect, vi } from "vitest"

import { LiaChatMessageList } from "@/components/lia-float/LiaChatMessageList"
import type { FloatMessage } from "@/hooks/chat/use-float-conversation"

vi.mock("@/stores/auth-store", () => ({
  useAuthStore: (sel: (s: { user: { name: string; email: string } }) => unknown) =>
    sel({ user: { name: "Tester", email: "t@example.com" } }),
}))

vi.mock("@/components/chat/message-feedback", () => ({
  MessageFeedback: () => null,
}))

function renderList(messages: FloatMessage[], handleChipSend = vi.fn()) {
  const ref = React.createRef<HTMLDivElement>()
  render(
    <LiaChatMessageList
      showHistory={false}
      recentChats={[]}
      handleLoadConversation={vi.fn()}
      isFetchingHistory={false}
      isEmpty={messages.length === 0}
      messages={messages}
      currentScope="home"
      contextPage={null}
      handleChipSend={handleChipSend}
      hitlPending={null}
      sendApproval={vi.fn()}
      isStreaming={false}
      streamingContent=""
      conversationId="conv-1"
      messagesEndRef={ref}
    />
  )
  return { handleChipSend }
}

describe("LiaChatMessageList — Sprint B.6 quick replies integration", () => {
  it("não renderiza QuickReplies quando mensagem da LIA não tem metadata", () => {
    const msg: FloatMessage = {
      id: "m1",
      sender: "lia",
      content: "Olá!",
      timestamp: "10:00",
    }
    renderList([msg])
    expect(screen.queryByTestId("quick-replies")).not.toBeInTheDocument()
  })

  it("renderiza QuickReplies preset=boolean quando mensagem da LIA tem hint", () => {
    const msg: FloatMessage = {
      id: "m1",
      sender: "lia",
      content: "Aceita?",
      timestamp: "10:00",
      metadata: { quick_reply_preset: "boolean" },
    }
    renderList([msg])
    expect(screen.getByTestId("quick-replies")).toBeInTheDocument()
    expect(screen.getByTestId("quick-reply-sim")).toBeInTheDocument()
    expect(screen.getByTestId("quick-reply-não")).toBeInTheDocument()
  })

  it("click no quick reply dispara handleChipSend com value canonical", () => {
    const msg: FloatMessage = {
      id: "m1",
      sender: "lia",
      content: "Modelo de trabalho?",
      timestamp: "10:00",
      metadata: { quick_reply_preset: "work_model" },
    }
    const { handleChipSend } = renderList([msg])
    fireEvent.click(screen.getByTestId("quick-reply-hibrido"))
    expect(handleChipSend).toHaveBeenCalledTimes(1)
    expect(handleChipSend).toHaveBeenCalledWith("hibrido")
  })

  it("não renderiza QuickReplies em mensagens do usuário mesmo com metadata", () => {
    const msg: FloatMessage = {
      id: "m1",
      sender: "user",
      content: "sim",
      timestamp: "10:00",
      metadata: { quick_reply_preset: "boolean" },
    }
    renderList([msg])
    expect(screen.queryByTestId("quick-replies")).not.toBeInTheDocument()
  })
})
