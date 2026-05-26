"use client"

import { useState } from "react"
import { usePathname } from "next/navigation"
import { useMemo } from "react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { ReactQueryDevtools } from "@tanstack/react-query-devtools"
import { DashboardApp } from "@/components/dashboard-app"
import { labelFromPath } from "@/lib/navigation/routes"
import { OnboardingChatBanner } from "@/components/onboarding/OnboardingChatBanner"

/**
 * Strip the locale prefix from a pathname.
 * "/pt/configuracoes/ai-credits" → "/configuracoes"
 * "/en/chat" → "/chat"
 *
 * Only the FIRST path segment after the locale is matched (we don't
 * keep nested segments because the Sidebar highlighting is per-section,
 * not per-leaf).
 */
function pathnameToCurrentPage(pathname: string | null): string {
  if (!pathname) return "Conversar"
  // Strip optional `/xx` locale prefix.
  const noLocale = pathname.replace(/^\/[a-z]{2}(?=\/|$)/, "")
  // Keep only the first segment (e.g. "/configuracoes/ai-credits" → "/configuracoes").
  const firstSegment = "/" + (noLocale.split("/").filter(Boolean)[0] ?? "")
  return labelFromPath(firstSegment) ?? "Conversar"
}

export default function DashboardLayoutClient({
  children,
}: {
  children: React.ReactNode
}) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            retry: 2,
            refetchOnWindowFocus: false,
          },
        },
      }),
  )
  const pathname = usePathname()
  const initialPage = useMemo(
    () => pathnameToCurrentPage(pathname),
    [pathname],
  )

  return (
    <QueryClientProvider client={queryClient}>
      <DashboardApp initialPage={initialPage}>
        <OnboardingChatBanner onOpenChat={() => window.dispatchEvent(new CustomEvent("lia:open-onboarding-chat", { detail: {} }))} />
        {children}
      </DashboardApp>
      {process.env.NODE_ENV === "development" && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  )
}
