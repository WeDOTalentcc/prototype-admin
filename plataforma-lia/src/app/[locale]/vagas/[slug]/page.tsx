import type { Metadata } from "next"
import VagasDetailClient from "./VagasDetailClient"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>
}): Promise<Metadata> {
  const { slug } = await params
  const title = slug.replace(/-/g, " ").replace(/\b\w/g, (l: string) => l.toUpperCase())
  return {
    title: `${title} | WeDoTalent`,
    description: `Candidate-se para a vaga de ${title}. Processo seletivo com triagem inteligente por IA da WeDoTalent.`,
    robots: { index: true, follow: true },
  }
}

export default async function PublicVacancyPage({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  return (
    <ErrorBoundarySection>
      <VagasDetailClient slug={slug} />
    </ErrorBoundarySection>
  )
}
