import type { Metadata } from "next"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"
import SettingsPageEnhanced from "@/components/pages/settings-page-enhanced"

export const metadata: Metadata = {
  title: "Configurações | LIA — WeDo Talent",
  description: "Configure sua conta, preferências da plataforma, integrações e configurações da empresa no LIA WeDoTalent.",
}

export default function ConfiguracoesPage() {
  return (
    <ErrorBoundarySection>
      <SettingsPageEnhanced />
    </ErrorBoundarySection>
  )
}
