/**
 * Canonical helper for navigating to a job's detail / list view.
 *
 * Post-mortem 2026-04-29 wizard-domain-hint-leak audit:
 *   The Next.js page `/[locale]/(dashboard)/jobs/[jobId]/page.tsx` was
 *   deleted on commit f7627f1bf without updating producers. Components
 *   across the codebase synthesized URLs like `/jobs/${jobId}` and
 *   `/jobs/new?candidates=...` independently, every one of them now
 *   landing on a 404 page.
 *
 *   Until product decides the canonical "view job detail / list" route
 *   (candidate paths: `/teams-tab/vagas`, restore `/jobs`, integrate
 *   into chat, ...), this helper centralizes the knowledge of "we don't
 *   have a route for this yet" so:
 *
 *     - There is exactly ONE place to change when the route is decided.
 *     - All consumers route through here (single source of truth).
 *     - User does not see a confusing 404 — they see a success toast.
 *     - Developer sees a console warning and can grep for the helper.
 *
 * Skill canônica: harness-engineering [guide computacional] +
 *                 canonical-fix (single navigation source).
 */
import type { AppRouterInstance } from "next/dist/shared/lib/app-router-context.shared-runtime"
import { toast } from "sonner"

/**
 * Extract the current locale segment from `window.location.pathname`.
 *
 * Canonical locales are 2-letter codes — `pt` (default) and `en` —
 * mirroring `src/i18n/config.ts` and `DashboardLayoutClient`'s
 * `/^\/[a-z]{2}(?=\/|$)/` strip. The next-intl middleware (`localePrefix:
 * 'always'`) injects the prefix on every request, so on the client the
 * regex match below virtually always succeeds. Falls back to `"pt"`
 * (the app's `defaultLocale`) on SSR or when no prefix is present.
 */
function currentLocale(): string {
  if (typeof window === "undefined") return "pt"
  const match = window.location.pathname.match(/^\/([a-z]{2})(?=\/|$)/)
  return match?.[1] ?? "pt"
}

/**
 * Navigate to a job's detail page (`/[locale]/jobs/<id>`). Returns true
 * if navigation was triggered.
 *
 * Route restored 2026-05-19 under `(dashboard)/jobs/[id]/` so the page
 * inherits the global Sidebar + LiaFloat shell. This helper remains the
 * single navigation source — DO NOT add `router.push('/jobs/...')`
 * directly in components; the sensor at
 * `src/lib/navigation/__tests__/job-navigation.test.ts` will fail.
 */
export function navigateToJobDetail(
  router: AppRouterInstance | null,
  jobId: string,
  jobTitle?: string,
): boolean {
  if (!jobId) {
    console.warn("[job-navigation] navigateToJobDetail called without jobId")
    return false
  }
  if (!router) {
    console.warn(
      `[job-navigation] navigateToJobDetail called without router — ` +
        `falling back to toast for jobId=${jobId}`,
    )
    toast.success(
      jobTitle ? `Vaga "${jobTitle}" salva.` : "Vaga salva.",
      { description: "Atualize a lista para visualizá-la." },
    )
    return false
  }
  const locale = currentLocale()
  router.push(`/${locale}/jobs/${encodeURIComponent(jobId)}`)
  return true
}

/**
 * Navigate to the "new job from candidates" flow.
 * Same rationale as `navigateToJobDetail`. Currently always returns false.
 */
export function navigateToNewJobFromCandidates(
  candidateIds: string[],
): boolean {
  if (candidateIds.length === 0) {
    console.warn(
      "[job-navigation] navigateToNewJobFromCandidates called without candidateIds",
    )
    return false
  }
  console.warn(
    `[job-navigation] /jobs/new route does not exist yet — ` +
      `candidateCount=${candidateIds.length}. When canonical route is ` +
      `decided, update src/lib/navigation/job-navigation.ts.`,
  )
  toast.info("Criar nova vaga com candidatos selecionados", {
    description:
      "Use o chat com a IA: peça 'criar vaga com estes candidatos' " +
      "ou abra o wizard manualmente.",
  })
  return false
}
