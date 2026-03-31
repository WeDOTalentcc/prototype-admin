import type { Metadata } from "next"

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>
}): Promise<Metadata> {
  const { id } = await params
  return {
    title: ,
    description: "Detalhes da vaga, candidatos e kanban de seleção",
    robots: { index: false, follow: false },
  }
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
