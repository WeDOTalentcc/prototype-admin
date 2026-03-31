import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Acesso',
  description: 'Controle de acesso à Plataforma LIA WeDoTalent',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
