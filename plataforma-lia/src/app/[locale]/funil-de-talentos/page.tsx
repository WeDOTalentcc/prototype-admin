import type { Metadata } from "next"
import FunilDeTalentosClient from "./FunilDeTalentosClient"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"

export const metadata: Metadata = {
  title: "Funil de Talentos | LIA — WeDo Talent",
  description: "Gerencie seu banco de talentos, listas de candidatos e buscas salvas. Encontre os melhores perfis para suas vagas com filtros inteligentes.",
}

export default function FunilDeTalentosPage() {
  return (
    <ErrorBoundarySection>
      <FunilDeTalentosClient />
    </ErrorBoundarySection>
  )
}
