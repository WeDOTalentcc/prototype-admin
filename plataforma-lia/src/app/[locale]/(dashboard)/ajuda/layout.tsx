import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Central de Ajuda',
  description: 'Suporte e documentação da WeDoTalent',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
