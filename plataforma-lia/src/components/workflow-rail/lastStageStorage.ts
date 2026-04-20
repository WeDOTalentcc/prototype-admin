/**
 * lastStageStorage — persist the recruiter's last active funnel stage
 * across sessions, keyed by userId.
 *
 * Stored value falls back to "initial" if missing, malformed, or stale
 * (older than STALE_AFTER_MS, currently 7 days). All operations are safe
 * to call during SSR — they no-op when `window` is unavailable.
 */

import type { FunnelStageKey } from "./workflowRailCatalog"

const STORAGE_PREFIX = "workflow-rail:last-stage:"
const STALE_AFTER_MS = 7 * 24 * 60 * 60 * 1000 // 7 days

const VALID_STAGES: ReadonlySet<FunnelStageKey> = new Set([
  "initial",
  "create_job",
  "sourcing",
  "screening",
  "interview",
  "offer",
  "hired",
  "analytics",
])

interface StoredStage {
  stage: FunnelStageKey
  updatedAt: number
}

function storageKey(userId: string): string {
  return `${STORAGE_PREFIX}${userId}`
}

export function loadLastStage(userId: string): FunnelStageKey {
  if (typeof window === "undefined" || !userId) return "initial"
  try {
    const raw = window.localStorage.getItem(storageKey(userId))
    if (!raw) return "initial"
    const parsed = JSON.parse(raw) as Partial<StoredStage>
    if (!parsed || typeof parsed !== "object") return "initial"
    if (typeof parsed.updatedAt !== "number") return "initial"
    if (Date.now() - parsed.updatedAt > STALE_AFTER_MS) return "initial"
    if (!parsed.stage || !VALID_STAGES.has(parsed.stage as FunnelStageKey)) return "initial"
    return parsed.stage as FunnelStageKey
  } catch {
    return "initial"
  }
}

export function saveLastStage(userId: string, stage: FunnelStageKey): void {
  if (typeof window === "undefined" || !userId) return
  try {
    const payload: StoredStage = { stage, updatedAt: Date.now() }
    window.localStorage.setItem(storageKey(userId), JSON.stringify(payload))
  } catch {
    // Quota exceeded or storage disabled — ignore silently.
  }
}
