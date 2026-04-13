import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Criar Conta',
  description: 'Crie sua conta na Plataforma LIA WeDoTalent',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
