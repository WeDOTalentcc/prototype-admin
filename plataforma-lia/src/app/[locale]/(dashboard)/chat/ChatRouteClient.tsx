"use client"

import { useSearchParams } from "next/navigation"
import { ChatPage } from "@/components/pages/chat-page"

export function ChatRouteClient() {
  const searchParams = useSearchParams()
  const conv = searchParams.get("conv")
  return <ChatPage initialConversationId={conv ?? null} />
}
