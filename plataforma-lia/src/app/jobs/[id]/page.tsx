import type { Metadata } from "next"
import JobDetailClient from "./JobDetailClient"

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>
}): Promise<Metadata> {
  const { id } = await params
  return {
    title: `Vaga ${id} | LIA — WeDo Talent`,
    description: "Detalhes da vaga, candidatos inscritos e kanban de seleção. Gerencie o processo seletivo com inteligência artificial.",
    robots: { index: false, follow: false },
  }
}

export default function JobPage() {
  return <JobDetailClient />
}
