import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Acesso Negado | WeDoTalent',
  description: 'Você não tem permissão para acessar esta área.',
  robots: { index: false, follow: false },
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
