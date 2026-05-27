import type { Metadata } from "next"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"
import { ChatRouteClient } from "./ChatRouteClient"

export const metadata: Metadata = {
  title: "Chat LIA | WeDoTalent",
  description: "Converse com a LIA, sua assistente de recrutamento com inteligência artificial. Tire dúvidas, analise candidatos e obtenha insights.",
}

export default function ChatRoute() {
  return (
    <ErrorBoundarySection>
      <ChatRouteClient />
    </ErrorBoundarySection>
  )
}
