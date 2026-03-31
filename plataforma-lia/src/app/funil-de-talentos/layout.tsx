import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Funil de Talentos',
  description: 'Visualize e gerencie o funil de recrutamento de candidatos',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
