import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Trust Center',
  description: 'Transparência, segurança e conformidade da WeDoTalent',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
