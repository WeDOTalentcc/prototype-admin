import type { Metadata } from "next"
import { ThemeProvider } from "@/components/theme-provider"
import { JWTAuthProvider } from "@/contexts/auth-context"
import { TeamsSSOProvider } from "@/contexts/teams-sso-context"
import { Toaster } from "sonner"

export const metadata: Metadata = {
  title: "WeDoTalent",
  description: "Plataforma de recrutamento inteligente",
}

export default function TeamsTabLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ThemeProvider attribute="class" defaultTheme="light" enableSystem={false}>
      <JWTAuthProvider>
        <TeamsSSOProvider>
          <div className="h-screen bg-lia-bg-primary overflow-hidden font-sans antialiased">
            {children}
          </div>
          <Toaster position="top-right" richColors />
        </TeamsSSOProvider>
      </JWTAuthProvider>
    </ThemeProvider>
  )
}
