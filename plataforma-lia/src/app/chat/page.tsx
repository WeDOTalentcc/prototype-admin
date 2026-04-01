import type { Metadata } from "next"
import { ChatPage } from "@/components/pages/chat-page"

export const metadata: Metadata = {
  title: "Chat LIA | LIA — WeDo Talent",
  description: "Converse com a LIA, sua assistente de recrutamento com inteligência artificial. Tire dúvidas, analise candidatos e obtenha insights.",
}

export default function ChatRoute() {
  return <ChatPage />
}
