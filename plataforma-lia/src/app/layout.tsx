export const dynamic = 'force-dynamic'

import type { Metadata } from "next";
import { Inter, Open_Sans, Crimson_Text } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider"
import { JWTAuthProvider } from "@/contexts/auth-context"
import { ErrorBoundary } from "@/components/error-boundary"
import { Toaster } from "@/components/ui/toaster"
import { SetupAlertBadge } from "@/components/ui/setup-alert-badge"
import { Toaster as SonnerToaster } from "sonner"
import { LiaFloatProvider } from "@/contexts/lia-float-context"
import { LiaFloatConditional } from "@/components/lia-float/LiaFloatConditional"
import { CookieConsent } from "@/components/ui/cookie-consent"


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

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <head suppressHydrationWarning>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link rel="dns-prefetch" href="https://fonts.googleapis.com" />
      </head>
      
      <body 
        className={`${inter.variable} ${openSans.variable} ${crimsonText.variable} antialiased`}
        suppressHydrationWarning
      >
      {/* Skip to content — acessibilidade para navegação por teclado */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[9999] focus:px-4 focus:py-2 focus:bg-wedo-cyan focus:text-white focus:rounded-lg focus:text-sm focus:font-medium focus:shadow-lg"
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
                <SetupAlertBadge />
                <Toaster />
                <SonnerToaster position="top-right" />
                <LiaFloatConditional />
              </ErrorBoundary>
            </LiaFloatProvider>
          </JWTAuthProvider>
        </ThemeProvider>
        <CookieConsent />
      </body>
    </html>
  );
}
