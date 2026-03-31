import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Integrações',
  description: 'Configure integrações com sistemas externos na Plataforma LIA',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
