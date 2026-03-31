import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Configurações do Sistema',
  description: 'Configurações globais da Plataforma LIA WeDoTalent',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
