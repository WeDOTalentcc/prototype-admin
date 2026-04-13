import type { Metadata } from "next"
import { DashboardApp } from "@/components/dashboard-app"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"

export const metadata: Metadata = {
  title: "Funil de Candidatos | LIA — WeDo Talent",
  description: "Visualize e gerencie candidatos no funil Kanban de recrutamento. Mova candidatos entre etapas e acompanhe o pipeline de seleção.",
}

export default function FunilPage() {
  return (
    <ErrorBoundarySection>
      <DashboardApp />
    </ErrorBoundarySection>
  )
}
