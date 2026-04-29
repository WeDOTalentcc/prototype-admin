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
 * Navigate to a job's detail page. Returns true if navigation happened.
 *
 * Currently always returns false (route does not exist). When product
 * restores the route, change this function — DO NOT add `router.push`
 * calls directly in components. The reason this helper exists is to keep
 * that change surface to a single file.
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
  console.warn(
    `[job-navigation] /jobs/<id> route does not exist yet — jobId=${jobId}. ` +
      `When canonical route is decided, update src/lib/navigation/job-navigation.ts.`,
  )
  toast.success(
    jobTitle ? `Vaga "${jobTitle}" salva.` : "Vaga salva.",
    { description: "Atualize a lista para visualizá-la." },
  )
  // Suppress unused-arg warning while keeping the API stable for the
  // future implementation that will use `router.push(...)`.
  void router
  return false
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
      "Use o chat com a LIA: peça 'criar vaga com estes candidatos' " +
      "ou abra o wizard manualmente.",
  })
  return false
}
