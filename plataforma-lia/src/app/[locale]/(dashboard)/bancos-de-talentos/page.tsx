import type { Metadata } from "next"
import BancosClient from "./BancosClient"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"

export const metadata: Metadata = {
  title: "Bancos de Talentos | WeDoTalent",
  description: "Crie e gerencie bancos de talentos vivos com sourcing automático e triagem contínua.",
}

export default function BancosDeTalentosPage() {
  return (
    <ErrorBoundarySection>
      <BancosClient />
    </ErrorBoundarySection>
  )
}
