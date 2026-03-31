import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Relatório Compartilhado',
  description: 'Relatório de candidato compartilhado via Plataforma LIA',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
