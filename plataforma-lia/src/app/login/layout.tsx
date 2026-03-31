import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Entrar',
  description: 'Acesse a Plataforma LIA WeDoTalent com suas credenciais',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
