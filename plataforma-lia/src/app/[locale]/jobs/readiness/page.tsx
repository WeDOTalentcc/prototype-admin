import type { Metadata } from "next"
import { Suspense } from "react"
import { ReadinessHubPage } from "@/components/pages/jobs/readiness/ReadinessHubPage"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"

export const metadata: Metadata = {
  title: "Hub de Prontidão | LIA — WeDo Talent",
  description:
    "Prepare suas vagas importadas do ATS para começar a triar candidatos com a LIA. Pipeline visual de prontidão por estágio, com ações em lote e aprovação humana.",
}

export default function ReadinessRoutePage() {
  return (
    <ErrorBoundarySection>
      <Suspense fallback={null}>
        <ReadinessHubPage />
      </Suspense>
    </ErrorBoundarySection>
  )
}
