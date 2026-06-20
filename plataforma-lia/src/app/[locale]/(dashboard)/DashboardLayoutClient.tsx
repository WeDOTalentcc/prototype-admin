"use client"

import { useState } from "react"
import { usePathname } from "next/navigation"
import { useMemo } from "react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { DashboardApp } from "@/components/dashboard-app"
import { labelFromPath } from "@/lib/navigation/routes"
import { AutomationFromChatBridge } from "@/components/settings/recruitment/AutomationFromChatBridge"
import { useEffect, useState as useStateAlias } from "react"
import { useIsFetching } from "@tanstack/react-query"
import { useLoadingWatchdog } from "@/hooks/shared/use-loading-watchdog"
import { LoadingWatchdogOverlay } from "@/components/ui/loading-watchdog-overlay"
import { Breadcrumbs } from "@/components/shared/Breadcrumbs"

/**
 * Strip the locale prefix from a pathname.
 * "/pt/configuracoes/ai-credits" → "/configuracoes"
 * "/en/chat" → "/chat"
 *
 * Only the FIRST path segment after the locale is matched (we don't
 * keep nested segments because the Sidebar highlighting is per-section,
 * not per-leaf).
 */
/** Renders a global stall overlay when any React Query fetch exceeds 5 s.
 * Must live inside QueryClientProvider to access useIsFetching. */
function LoadingWatchdogBridge() {
  const isFetching = useIsFetching()
  const [isStalled, setIsStalled] = useStateAlias(false)

  useEffect(() => {
    if (isFetching === 0) setIsStalled(false)
  }, [isFetching])

  useLoadingWatchdog(isFetching > 0, () => setIsStalled(true), 5_000)

  return <LoadingWatchdogOverlay isVisible={isStalled && isFetching > 0} />
}

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
            retry: 1,
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
      <LoadingWatchdogBridge />
      <DashboardApp initialPage={initialPage}>
        <div className="flex h-full min-h-0 flex-col">
          <AutomationFromChatBridge />
          <Breadcrumbs className="shrink-0 px-6 pt-3 pb-0" />
          <div className="min-h-0 flex-1 overflow-hidden">
            {children}
          </div>
        </div>
      </DashboardApp>
    </QueryClientProvider>
  )
}
