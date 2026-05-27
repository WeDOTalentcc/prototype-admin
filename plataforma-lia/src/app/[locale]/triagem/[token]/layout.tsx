import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "Triagem de Candidato",
  description: "Processo de triagem automatizada com a assistente de recrutamento",
  robots: { index: false, follow: false },
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
