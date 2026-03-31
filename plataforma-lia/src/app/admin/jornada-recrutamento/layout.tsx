import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Jornada de Recrutamento',
  description: 'Configuração da jornada de recrutamento',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
