import type { Metadata } from "next"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"
import { SettingsRouteClient } from "./SettingsRouteClient"

export const metadata: Metadata = {
  title: "Configurações | WeDoTalent",
  description: "Configure sua conta, preferências da plataforma, integrações e configurações da empresa no LIA WeDoTalent.",
}

export default function ConfiguracoesPage() {
  return (
    <ErrorBoundarySection>
      <SettingsRouteClient />
    </ErrorBoundarySection>
  )
}
