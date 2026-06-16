import type { Metadata } from "next"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"
import { CentralComunicacaoRouteClient } from "./CentralComunicacaoRouteClient"

export const metadata: Metadata = {
  title: "Central Comunicação | WeDoTalent",
  description: "Sistema unificado de comunicação multi-canal.",
}

export default function CentralComunicacaoRoute() {
  return (
    <ErrorBoundarySection>
      <CentralComunicacaoRouteClient />
    </ErrorBoundarySection>
  )
}
