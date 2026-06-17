import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Redefinir Senha',
  description: 'Redefina sua senha da WeDoTalent',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
