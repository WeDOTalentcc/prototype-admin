import type { Metadata } from "next"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"
import CandidateProfilePage from "./CandidatoDetailClient"

export const metadata: Metadata = {
  title: "Candidato | LIA — WeDo Talent",
  description: "Perfil completo do candidato.",
}

export default function CandidatoDetailRoute() {
  return (
    <ErrorBoundarySection>
      <CandidateProfilePage />
    </ErrorBoundarySection>
  )
}
