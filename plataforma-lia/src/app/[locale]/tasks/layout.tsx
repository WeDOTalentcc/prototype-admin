import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Tarefas',
  description: 'Gerencie tarefas e atividades de recrutamento',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
