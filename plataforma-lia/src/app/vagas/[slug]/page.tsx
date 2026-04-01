import type { Metadata } from "next"
import VagasDetailClient from "./VagasDetailClient"

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>
}): Promise<Metadata> {
  const { slug } = await params
  const title = slug.replace(/-/g, " ").replace(/\b\w/g, (l: string) => l.toUpperCase())
  return {
    title: `${title} | Vagas LIA — WeDo Talent`,
    description: `Candidate-se para a vaga de ${title}. Processo seletivo com triagem inteligente por IA da Plataforma LIA WeDoTalent.`,
    robots: { index: true, follow: true },
  }
}

export default function PublicVacancyPage() {
  return <VagasDetailClient />
}
