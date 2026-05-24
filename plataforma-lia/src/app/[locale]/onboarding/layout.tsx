import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Onboarding | LIA — WeDo Talent',
  description: 'Configure sua conta e conheça a LIA, sua assistente de recrutamento.',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
