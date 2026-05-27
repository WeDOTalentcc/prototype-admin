export const dynamic = 'force-dynamic'

import { NextIntlClientProvider } from 'next-intl'
import { getMessages, setRequestLocale } from 'next-intl/server'
import { notFound } from 'next/navigation'
import { routing } from '@/i18n/routing'
import type { Locale } from '@/i18n/config'
import { ThemeProvider } from "@/components/theme-provider"
import { JWTAuthProvider } from "@/contexts/auth-context"
import { ErrorBoundary } from "@/components/error-boundary"
import { headers } from "next/headers"
import { Toaster as SonnerToaster } from "sonner"
import { LiaFloatProvider } from "@/contexts/lia-float-context"
import DeferredLayoutClients from "@/components/layout/DeferredLayoutClients"

async function getServerUser(): Promise<Record<string, unknown> | null> {
  try {
    const headersList = await headers()
    const authHeader = headersList.get('authorization')
    if (!authHeader) return null

    const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

    // QW3 audit 2026-05-22: layout.tsx tem `export const dynamic = "force-dynamic"`,
    // entao TODA navegacao SSR-renderiza esperando este fetch. Quando o backend
    // FastAPI esta lento (restart, hung, OOM), sem timeout = tela preta 30s+
    // antes do user ver qualquer HTML. Timeout de 3s + null fallback garante
    // que o layout SEMPRE responde em <3s. Middleware ja valida JWT entao
    // serverUser eh apenas conveniencia (passa pro window.__INITIAL_USER__).
    const response = await fetch(`${BACKEND_URL}/api/v1/auth/me`, {
      method: 'GET',
      headers: {
        'Authorization': authHeader,
        'Content-Type': 'application/json',
      },
      cache: 'no-store',
      signal: AbortSignal.timeout(3000),
    })

    if (response.ok) {
      return await response.json()
    }

    return null
  } catch {
    // Timeout, network error, ou backend hung — render layout sem user data.
    // Cliente busca via /api/auth/me apos hidratacao se precisar.
    return null
  }
}

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }))
}

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params
  const isEn = locale === 'en'

  return {
    title: {
      default: isEn ? 'WeDoTalent' : 'WeDoTalent',
      template: '%s | WeDoTalent',
    },
    description: isEn
      ? 'Intelligent AI-powered recruitment platform — Screening, Kanban and Candidate Analysis'
      : 'Plataforma de recrutamento inteligente com IA — Triagem, Kanban e Análise de Candidatos',
    keywords: isEn
      ? ['recruitment', 'hiring', 'HR', 'AI', 'candidates', 'jobs', 'WeDoTalent']
      : ['recrutamento', 'seleção', 'RH', 'IA', 'candidatos', 'vagas', 'WeDoTalent'],
    authors: [{ name: 'WeDoTalent' }],
    creator: 'WeDoTalent',
    publisher: 'WeDoTalent',
    robots: {
      index: false,
      follow: false,
      noarchive: true,
    },
    openGraph: {
      type: 'website' as const,
      locale: isEn ? 'en_US' : 'pt_BR',
      url: 'https://app.wedotalent.com',
      siteName: 'WeDoTalent',
      title: isEn ? 'WeDoTalent' : 'WeDoTalent',
      description: isEn ? 'Intelligent AI-powered recruitment' : 'Recrutamento inteligente com IA',
      images: [
        {
          url: '/og-image.png',
          width: 1200,
          height: 630,
          alt: 'WeDoTalent',
        },
      ],
    },
    twitter: {
      card: 'summary_large_image' as const,
      title: isEn ? 'WeDoTalent' : 'WeDoTalent',
      description: isEn ? 'Intelligent AI-powered recruitment' : 'Recrutamento inteligente com IA',
      images: ['/og-image.png'],
    },
  }
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode
  params: Promise<{ locale: string }>
}) {
  const { locale } = await params

  if (!routing.locales.includes(locale as Locale)) {
    notFound()
  }

  setRequestLocale(locale)

  const [messages, serverUser] = await Promise.all([
    getMessages(),
    getServerUser(),
  ])

  return (
    <>
      <script
        dangerouslySetInnerHTML={{
          __html: `document.documentElement.lang="${locale === 'en' ? 'en' : 'pt-BR'}";`,
        }}
      />
      {serverUser && (
        <script
          dangerouslySetInnerHTML={{
            __html: `window.__INITIAL_USER__=${JSON.stringify(serverUser)};`,
          }}
        />
      )}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-modal focus:px-4 focus:py-2 focus:bg-wedo-cyan focus:text-white focus:rounded-lg focus:text-sm focus:font-medium focus:shadow-lg"
      >
        {locale === 'en' ? 'Skip to main content' : 'Ir para o conteúdo principal'}
      </a>
      <NextIntlClientProvider messages={messages}>
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          enableSystem={false}
          forcedTheme="light"
          disableTransitionOnChange
          storageKey="wedo-theme"
        >
          <JWTAuthProvider>
            <LiaFloatProvider>
              <ErrorBoundary>
                {children}
                <SonnerToaster position="top-right" richColors />
                <DeferredLayoutClients />
              </ErrorBoundary>
            </LiaFloatProvider>
          </JWTAuthProvider>
        </ThemeProvider>
      </NextIntlClientProvider>
    </>
  )
}
