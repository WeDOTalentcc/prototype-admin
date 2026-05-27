import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Recuperar Senha',
  description: 'Recupere o acesso à sua conta na WeDoTalent',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
