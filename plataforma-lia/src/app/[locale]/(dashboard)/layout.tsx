import type { Metadata } from "next"
import DashboardLayoutClient from "./DashboardLayoutClient"

export const metadata: Metadata = {
  title: "WeDoTalent",
}

/**
 * Canonical layout for all routes inside `[locale]/(dashboard)/`.
 *
 * Wraps every subpage (chat, agent-studio, configuracoes, etc.) with
 * the DashboardApp shell so the global Sidebar, LiaFloat panel and
 * GlobalSearchModal are present on every dashboard route.
 *
 * Post-mortem 2026-04-29 wizard-domain-hint-leak audit: before this
 * layout existed, only `/[locale]/page.tsx` (root `/`) rendered the
 * Sidebar via DashboardApp. Subroutes like `/[locale]/configuracoes/`
 * rendered their client component bare, so the Sidebar disappeared
 * and the user had no way back to other pages without typing URLs.
 *
 * Skill canônica: harness-engineering [guide computacional] +
 *                 canonical-fix (single shell source — DashboardApp).
 */
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <DashboardLayoutClient>{children}</DashboardLayoutClient>
}
