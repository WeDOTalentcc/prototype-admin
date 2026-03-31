import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Vagas',
  description: 'Gerencie e acompanhe vagas de emprego com inteligência artificial',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
