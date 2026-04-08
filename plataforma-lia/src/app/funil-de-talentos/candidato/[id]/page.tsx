import type { Metadata } from "next"
import CandidatoDetailClient from "./CandidatoDetailClient"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>
}): Promise<Metadata> {
  const { id } = await params
  return {
    title: `Candidato ${id} | LIA — WeDo Talent`,
    description: "Perfil detalhado do candidato com análise de competências, histórico profissional e avaliação por inteligência artificial.",
    robots: { index: false, follow: false },
  }
}

export default function CandidateProfilePage() {
  return (
    <ErrorBoundarySection>
      <CandidatoDetailClient />
    </ErrorBoundarySection>
  )
}
