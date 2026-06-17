import type { Metadata } from "next"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"
import JobDetail from "./JobDetailClient"

export const metadata: Metadata = {
  title: "Vaga | WeDoTalent",
  description: "Detalhes da vaga e quadro Kanban de candidatos.",
}

export default function JobDetailRoute() {
  return (
    <ErrorBoundarySection>
      <JobDetail />
    </ErrorBoundarySection>
  )
}
