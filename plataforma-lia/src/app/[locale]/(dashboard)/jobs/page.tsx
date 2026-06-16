import type { Metadata } from "next"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"
import { JobsPage } from "@/components/pages/jobs-page"

export const metadata: Metadata = {
  title: "Vagas | WeDoTalent",
  description: "Acompanhe e gerencie todas as suas vagas: status, candidatos, publicações e ações da IA.",
}

export default function VagasRoute() {
  return (
    <ErrorBoundarySection>
      <JobsPage />
    </ErrorBoundarySection>
  )
}
