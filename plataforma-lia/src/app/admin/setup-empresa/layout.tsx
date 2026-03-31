import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Setup da Empresa',
  description: 'Configuração inicial da empresa na Plataforma LIA',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
