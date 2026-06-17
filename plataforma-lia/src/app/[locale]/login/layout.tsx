import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Entrar',
  description: 'Acesse a WeDoTalent com suas credenciais',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
