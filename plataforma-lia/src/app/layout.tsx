export const dynamic = 'force-dynamic'

import type { Metadata } from "next";
import { Inter, Open_Sans, Crimson_Text, Source_Serif_4 } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider"
import { JWTAuthProvider } from "@/contexts/auth-context"
import { ErrorBoundary } from "@/components/error-boundary"
import { headers } from "next/headers"

import { Toaster as SonnerToaster } from "sonner"
import { LiaFloatProvider } from "@/contexts/lia-float-context"
import { UnifiedChatConditional } from "@/components/unified-chat"
import WorkflowRailWrapper from "@/components/workflow-rail/WorkflowRailWrapper"

async function getServerUser(): Promise<Record<string, unknown> | null> {
  try {
    const headersList = await headers()
    const authHeader = headersList.get('authorization')
    if (!authHeader) return null

    const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

    const response = await fetch(`${BACKEND_URL}/api/v1/auth/me`, {
      method: 'GET',
      headers: {
        'Authorization': authHeader,
        'Content-Type': 'application/json',
      },
      cache: 'no-store',
    })

    if (response.ok) {
      return await response.json()
    }

    // Do not fall back to unverified JWT claims — only trust validated backend responses.
    return null
  } catch {
    return null
  }
}


const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap"
});

const openSans = Open_Sans({
  subsets: ["latin"],
  variable: "--font-open-sans",
  display: "swap"
});

const crimsonText = Crimson_Text({
  subsets: ["latin"],
  weight: ["400", "600", "700"],
  variable: "--font-crimson",
  display: "swap"
});

const sourceSerif4 = Source_Serif_4({
  subsets: ["latin"],
  variable: "--font-source-serif-4",
  display: "swap"
});

export const metadata: Metadata = {
  metadataBase: new URL('https://app.wedotalent.com'),
  title: {
    default: 'Plataforma LIA — WeDoTalent',
    template: '%s | LIA WeDoTalent',
  },
  description: 'Plataforma de recrutamento inteligente com IA — Triagem, Kanban e Análise de Candidatos',
  keywords: ['recrutamento', 'seleção', 'RH', 'IA', 'candidatos', 'vagas', 'WeDoTalent', 'LIA'],
  authors: [{ name: 'WeDoTalent' }],
  creator: 'WeDoTalent',
  publisher: 'WeDoTalent',
  robots: {
    index: false,
    follow: false,
    noarchive: true,
  },
  openGraph: {
    type: 'website',
    locale: 'pt_BR',
    url: 'https://app.wedotalent.com',
    siteName: 'Plataforma LIA',
    title: 'Plataforma LIA — WeDoTalent',
    description: 'Recrutamento inteligente com IA',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'Plataforma LIA WeDoTalent',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Plataforma LIA — WeDoTalent',
    description: 'Recrutamento inteligente com IA',
    images: ['/og-image.png'],
  },
  icons: {
    icon: '/favicon.ico',
    apple: '/apple-touch-icon.png',
  },
  manifest: '/manifest.json',
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const serverUser = await getServerUser()

  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <head suppressHydrationWarning>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link rel="dns-prefetch" href="https://fonts.googleapis.com" />
      </head>
      
      <body 
        className={`${inter.variable} ${openSans.variable} ${crimsonText.variable} ${sourceSerif4.variable} antialiased`}
        suppressHydrationWarning
      >
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
        Ir para o conteúdo principal
      </a>
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          enableSystem={false}
          disableTransitionOnChange
          storageKey="wedo-theme"
        >
          <JWTAuthProvider>
            <LiaFloatProvider>
              <ErrorBoundary>
                {children}

                <SonnerToaster position="top-right" richColors />
                <WorkflowRailWrapper />
                <UnifiedChatConditional />
              </ErrorBoundary>
            </LiaFloatProvider>
          </JWTAuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
