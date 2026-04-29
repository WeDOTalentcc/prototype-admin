"use client"

import { usePathname } from "next/navigation"
import { useMemo } from "react"
import { DashboardApp } from "@/components/dashboard-app"

/**
 * Maps a stripped pathname (without /<locale>) to the `currentPage`
 * value DashboardApp uses to highlight the active Sidebar item.
 *
 * Keep keys aligned with the route folders in
 * `[locale]/(dashboard)/<route>/page.tsx`. Keep values aligned with
 * the `case` labels in `dashboard-app.tsx::renderCurrentPage()`.
 */
const ROUTE_TO_PAGE: Record<string, string> = {
  "/chat": "Conversar",
  "/agent-studio": "Estúdio de Agentes",
  "/configuracoes": "Configurações",
  "/biblioteca-lia": "Biblioteca LIA",
  "/bancos-de-talentos": "Bancos de Talentos",
  "/central-comunicacao": "Central Comunicação",
  "/ajuda": "Ajuda",
}

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
  return ROUTE_TO_PAGE[firstSegment] ?? "Conversar"
}

export default function DashboardLayoutClient({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()
  const initialPage = useMemo(
    () => pathnameToCurrentPage(pathname),
    [pathname],
  )

  return <DashboardApp initialPage={initialPage}>{children}</DashboardApp>
}
