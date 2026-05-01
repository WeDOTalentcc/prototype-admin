import { redirect } from "next/navigation"

// force-dynamic: Next 16 prerenders this redirect at build time inside the
// [locale] segment and resolves to "/undefined" because locale is unknown
// during prerender. Per-request rendering keeps Location: /.
export const dynamic = "force-dynamic"

// Legacy URL → SPA root. Funil canvas lives in dashboard-app.tsx via
// setCurrentPage("Funil de Talentos"). See session_plan T002 (fork_spa_switch).
export default function FunilDeTalentosLegacyRoute() {
  redirect("/")
}
