import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Monitoramento de Agentes',
  description: 'Monitoramento de saúde dos agentes de IA',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
