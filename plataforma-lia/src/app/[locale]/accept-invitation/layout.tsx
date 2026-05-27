import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Aceitar Convite',
  description: 'Aceite o convite para a WeDoTalent',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
