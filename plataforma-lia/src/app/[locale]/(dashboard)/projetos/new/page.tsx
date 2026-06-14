import type { Metadata } from "next"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"
import NovoProjetoWizard from "./NovoProjetoWizard"

export const metadata: Metadata = {
  title: "Novo Projeto | WeDoTalent",
  description: "Crie um novo projeto de recrutamento.",
}

export default function NovoProjetoRoute() {
  return (
    <ErrorBoundarySection>
      <NovoProjetoWizard />
    </ErrorBoundarySection>
  )
}
