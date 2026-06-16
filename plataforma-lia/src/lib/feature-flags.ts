/**
 * Canonical feature flags utility.
 *
 * Pattern: env vars com prefix NEXT_PUBLIC_FF_ * — true/false strings.
 * SSR-safe (não usa window).
 *
 * Para flags runtime mais sofisticadas (per-tenant, per-user), criar
 * sistema dedicado em src/lib/feature-flags/ futuro. Por enquanto,
 * env-based é suficiente para rollout gradual.
 */
export function isFeatureEnabled(flagName: string): boolean {
  if (typeof process === "undefined" || !process.env) return false
  const envKey = `NEXT_PUBLIC_FF_${flagName.toUpperCase()}`
  const value = process.env[envKey]
  return value === "true" || value === "1"
}

/** F5 D7 — inline pencil edit pattern (Surface 2 mode=page). */
export const FF_CANDIDATE_EDIT = "candidate_edit"
