import { redirect } from "next/navigation"

// Force dynamic rendering: without this Next 16 prerenders the redirect at
// build time inside the [locale] segment and resolves the destination to
// "/undefined", because the locale param is unknown during prerender. We need
// the redirect to run per-request so it always emits "Location: /" cleanly.
export const dynamic = "force-dynamic"

/**
 * Legacy URL redirect (T002, fork_spa_switch).
 *
 * The Funil de Talentos canvas now lives inside the dashboard SPA shell
 * (rendered by `dashboard-app.tsx` via `setCurrentPage("Funil de Talentos")`).
 * This route is preserved only so external links / bookmarks land somewhere
 * meaningful — we 308-redirect to the SPA root, where the i18n middleware
 * re-injects the active locale and the dashboard mounts the canvas via
 * the sidebar navigation default state.
 *
 * The old client (`FunilDeTalentosClient.tsx`) stays in this folder because
 * it remains the single source of truth that was graduated into
 * `components/pages/candidates-page.tsx` — once the SPA-mounted version
 * proves stable across a release, both this folder and the legacy client
 * can be deleted.
 */
export default function FunilDeTalentosLegacyRoute() {
  redirect("/")
}
