import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "Relatório Compartilhado",
  description: "Relatório de candidato compartilhado via WeDoTalent",
  robots: { index: false, follow: false },
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
