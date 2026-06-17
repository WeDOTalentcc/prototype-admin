import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Bancos de Talentos',
  description: 'Gerencie bancos de talentos vivos com sourcing automático',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
