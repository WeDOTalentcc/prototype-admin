import type { Metadata } from "next"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"
import FunilDeTalentosClient from "./FunilDeTalentosClient"

export const metadata: Metadata = {
  title: "Funil de Talentos | LIA — WeDo Talent",
  description: "Visualize o funil consolidado de candidatos das suas vagas e bancos de talentos.",
}

export default function FunilDeTalentosRoute() {
  return (
    <ErrorBoundarySection>
      <FunilDeTalentosClient />
    </ErrorBoundarySection>
  )
}
