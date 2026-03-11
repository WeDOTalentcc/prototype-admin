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
import { LiaChatButton } from "@/components/lia-float/LiaChatButton"
import { LiaChatPanel } from "@/components/lia-float/LiaChatPanel"


const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter"
});

const openSans = Open_Sans({
  subsets: ["latin"],
  variable: "--font-open-sans"
});

const crimsonText = Crimson_Text({
  subsets: ["latin"],
  weight: ["400", "600", "700"],
  variable: "--font-crimson",
  display: "swap"
});

export const metadata: Metadata = {
  title: "WeDo Talent - Plataforma de Recrutamento com IA",
  description: "Plataforma de recrutamento inteligente com LIA - sua assistente de IA para gestão de talentos",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <head suppressHydrationWarning />
      
      <body 
        className={`${openSans.className} ${inter.variable} ${openSans.variable} ${crimsonText.variable}`}
        suppressHydrationWarning
      >
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
                <LiaChatPanel />
                <LiaChatButton />
              </ErrorBoundary>
            </LiaFloatProvider>
          </JWTAuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
