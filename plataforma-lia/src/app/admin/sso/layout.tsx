import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'SSO Empresarial',
  description: 'Configuração de Single Sign-On empresarial',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
