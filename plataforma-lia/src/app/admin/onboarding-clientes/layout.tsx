import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Onboarding de Clientes',
  description: 'Processo de onboarding de novos clientes WeDoTalent',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
