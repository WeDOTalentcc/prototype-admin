import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Portal do Titular',
  description: 'Exercício de direitos LGPD — Portal do Titular de Dados',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
