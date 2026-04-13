import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Redefinir Senha',
  description: 'Redefina sua senha da Plataforma LIA WeDoTalent',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
