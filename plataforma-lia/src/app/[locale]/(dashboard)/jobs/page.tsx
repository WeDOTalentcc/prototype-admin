import type { Metadata } from "next"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"
import { JobsPage } from "@/components/pages/jobs-page"

export const metadata: Metadata = {
  title: "Vagas | LIA — WeDo Talent",
  description: "Acompanhe e gerencie todas as suas vagas: status, candidatos, publicações e ações da LIA.",
}

export default function VagasRoute() {
  return (
    <ErrorBoundarySection>
      <JobsPage />
    </ErrorBoundarySection>
  )
}
