import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Templates de Sistema',
  description: 'Gerenciamento de templates de comunicação',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
