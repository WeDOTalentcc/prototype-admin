import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Funil de Candidatos',
  description: 'Funil Kanban de gestão de candidatos',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
