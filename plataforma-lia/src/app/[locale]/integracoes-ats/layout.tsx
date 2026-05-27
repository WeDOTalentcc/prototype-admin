import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Integrações ATS | WeDoTalent',
  description: 'Configure suas integrações com sistemas ATS externos.',
  robots: { index: false, follow: false },
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
