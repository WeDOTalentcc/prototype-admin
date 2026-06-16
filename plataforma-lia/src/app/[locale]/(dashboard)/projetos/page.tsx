import type { Metadata } from "next"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"
import { ProjetosSection } from "@/components/pages/jobs/ProjetosSection"

export const metadata: Metadata = {
  title: "Projetos | WeDoTalent",
  description: "Projetos de recrutamento ativos.",
}

export default function ProjetosRoute() {
  return (
    <ErrorBoundarySection>
      <div className="p-6">
        <ProjetosSection />
      </div>
    </ErrorBoundarySection>
  )
}
