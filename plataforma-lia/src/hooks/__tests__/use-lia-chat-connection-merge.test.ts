/**
 * Tests — mergeSeededBackgroundTask (Task #865)
 *
 * Covers the race-guard semantics in the chat connection facade:
 * synchronous seed must NOT downgrade a row that already reached a
 * terminal status via the WS event stream.
 */
import { describe, expect, it } from "vitest"
import { mergeSeededBackgroundTask } from "@/hooks/chat/use-lia-chat-connection"
import type { BackgroundTaskEvent } from "@/hooks/chat/lia-chat-connection-types"

function task(
  task_id: string,
  status: BackgroundTaskEvent["status"],
  extra: Partial<BackgroundTaskEvent> = {},
): BackgroundTaskEvent {
  return {
    task_id,
    task_type: "wizard",
    label: "Importação de Job Description",
    status,
    ...extra,
  }
}

describe("mergeSeededBackgroundTask", () => {
  it("appends a brand-new task_id", () => {
    const out = mergeSeededBackgroundTask([], task("t-1", "queued"))
    expect(out).toHaveLength(1)
    expect(out[0]).toMatchObject({ task_id: "t-1", status: "queued" })
  })

  it("overwrites a stale non-terminal entry with the same task_id", () => {
    const prev = [task("t-1", "running", { message: "stale" })]
    const out = mergeSeededBackgroundTask(prev, task("t-1", "queued", { message: "fresh" }))
    expect(out).toHaveLength(1)
    expect(out[0]).toMatchObject({ status: "queued", message: "fresh" })
  })

  it("does NOT downgrade a `completed` row back to `queued` (race guard)", () => {
    const completed = task("t-1", "completed", { result: { imported_jd_id: "jd-9" } })
    const prev = [completed]
    const out = mergeSeededBackgroundTask(prev, task("t-1", "queued"))
    // Same array reference returned — no React re-render, no downgrade.
    expect(out).toBe(prev)
    expect(out[0].status).toBe("completed")
    expect(out[0].result).toEqual({ imported_jd_id: "jd-9" })
  })

  it("does NOT downgrade a `failed` row back to `running` (race guard)", () => {
    const failed = task("t-1", "failed", { message: "fairness_blocked: ..." })
    const prev = [failed]
    const out = mergeSeededBackgroundTask(prev, task("t-1", "running"))
    expect(out).toBe(prev)
    expect(out[0].status).toBe("failed")
    expect(out[0].message).toContain("fairness_blocked")
  })

  it("preserves unrelated tasks when merging", () => {
    const prev = [task("other", "running"), task("t-1", "queued")]
    const out = mergeSeededBackgroundTask(prev, task("t-1", "running", { message: "now running" }))
    expect(out).toHaveLength(2)
    expect(out[0]).toBe(prev[0])
    expect(out[1]).toMatchObject({ task_id: "t-1", status: "running", message: "now running" })
  })
})
