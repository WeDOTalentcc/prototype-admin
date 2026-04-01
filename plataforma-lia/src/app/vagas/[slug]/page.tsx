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
    title: `${title} | Vagas LIA`,
    description: `Detalhes da vaga ${title} na plataforma LIA.`,
    robots: { index: true, follow: true },
  }
}

export default function PublicVacancyPage() {
  return <VagasDetailClient />
}
