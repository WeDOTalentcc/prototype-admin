"use client"

import React from "react"
import { ChatPageFullscreen } from "@/components/unified-chat/ChatPageFullscreen"

export function ChatPage({ initialConversationId }: { initialConversationId?: string | null }) {
  return <ChatPageFullscreen initialConversationId={initialConversationId} />
}
