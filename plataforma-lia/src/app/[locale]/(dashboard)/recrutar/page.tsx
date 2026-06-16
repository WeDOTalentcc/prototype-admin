import type { Metadata } from "next"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"
import { PipelineOverviewPage } from "@/components/pages/pipeline-overview-page"

export const metadata: Metadata = {
  title: "Recrutar | WeDoTalent",
  description: "Visão global do pipeline de recrutamento.",
}

export default function RecrutarRoute() {
  return (
    <ErrorBoundarySection>
      <PipelineOverviewPage />
    </ErrorBoundarySection>
  )
}
