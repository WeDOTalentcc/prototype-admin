import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Créditos de IA',
  description: 'Gerencie seus créditos de inteligência artificial',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
