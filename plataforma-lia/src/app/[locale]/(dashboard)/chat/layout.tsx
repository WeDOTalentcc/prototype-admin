import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Chat',
  description: 'Converse com a LIA, sua assistente de recrutamento com IA',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
