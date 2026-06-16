import type { Metadata } from "next"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"
import ProjetoDetailClient from "./ProjetoDetailClient"

export const metadata: Metadata = {
  title: "Projeto | WeDoTalent",
  description: "Detalhes do projeto de recrutamento.",
}

export default async function ProjetoDetailRoute({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  return (
    <ErrorBoundarySection>
      <ProjetoDetailClient id={id} />
    </ErrorBoundarySection>
  )
}
