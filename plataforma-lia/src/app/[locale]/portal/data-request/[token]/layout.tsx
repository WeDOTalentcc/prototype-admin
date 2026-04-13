import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "Solicitação de Dados — Portal LGPD",
  description: "Exercício de direitos do titular de dados conforme a LGPD",
  robots: { index: false, follow: false },
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
