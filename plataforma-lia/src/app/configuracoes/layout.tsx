import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Configurações',
  description: 'Configurações da conta e da Plataforma LIA WeDoTalent',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
