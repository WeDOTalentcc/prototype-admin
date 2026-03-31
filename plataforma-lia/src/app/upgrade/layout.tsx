import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Planos e Upgrade',
  description: 'Conheça os planos da Plataforma LIA WeDoTalent',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
