import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Onboarding | WeDoTalent',
  description: 'Configure sua conta e conheça sua assistente de recrutamento.',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
