import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Métricas da Plataforma',
  description: 'Métricas e analytics da Plataforma LIA WeDoTalent',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
