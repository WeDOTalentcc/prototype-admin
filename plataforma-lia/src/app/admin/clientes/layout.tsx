import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Clientes',
  description: 'Gestão de clientes na Plataforma LIA WeDoTalent',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
