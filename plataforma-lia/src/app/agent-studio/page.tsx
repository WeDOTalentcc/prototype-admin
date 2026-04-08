import type { Metadata } from "next"
import AgentStudioClient from "./AgentStudioClient"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"

export const metadata: Metadata = {
  title: "Agent Studio | LIA — WeDo Talent",
  description: "Crie agentes de sourcing a partir de templates por setor. Configure calibração e automação.",
}

export default function AgentStudioPage() {
  return (
    <ErrorBoundarySection>
      <AgentStudioClient />
    </ErrorBoundarySection>
  )
}
