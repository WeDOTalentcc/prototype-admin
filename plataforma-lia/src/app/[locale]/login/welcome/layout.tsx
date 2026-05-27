import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Bem-vindo',
  description: 'Bem-vindo à WeDoTalent',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
