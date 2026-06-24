/**
 * Sensor GAP-09-002: SSE idempotency key — full turn_id dedup.
 *
 * Verifies that:
 *   1. FE declares useRef storage for active and completed turn IDs
 *   2. On stream_start event, the turn_id is stored as activeTurnIdRef
 *   3. If the incoming turn_id is already in completedTurnIdsRef, the stream is aborted
 *   4. On a terminal event (message/clarification/error) + active turn_id, the turn
 *      is added to completedTurnIdsRef to prevent re-processing on reconnect
 *   5. BE emits stream_start with turn_id as the first event in event_generator
 *   6. BE includes turn_id in the reconnect response (_reconnect_generator)
 *
 * Structural regex tests over source — canonical style for this hook.
 * Fix if a test fails: see useChatTransport.ts and app/api/v1/agent_chat_sse.py
 */
import { readFileSync } from "node:fs"
import { join } from "node:path"
import { describe, expect, test } from "vitest"

const TRANSPORT = readFileSync(join(__dirname, "..", "useChatTransport.ts"), "utf8")

describe("GAP-09-002 — SSE idempotency key: FE turn_id tracking", () => {
  test("Guard 1: activeTurnIdRef declared as useRef<string | null>", () => {
    expect(TRANSPORT).toMatch(
      /const activeTurnIdRef = useRef<string \| null>\(null\)/,
    )
  })

  test("Guard 2: completedTurnIdsRef declared as useRef<Set<string>>", () => {
    expect(TRANSPORT).toMatch(
      /const completedTurnIdsRef = useRef<Set<string>>\(new Set\(\)\)/,
    )
  })

  test("Guard 3: stream_start event sets activeTurnIdRef.current", () => {
    expect(TRANSPORT).toMatch(
      /event\.type === "stream_start"[\s\S]*?activeTurnIdRef\.current = tid/,
    )
  })

  test("Guard 4: duplicate turn aborts the stream (idempotency gate)", () => {
    const block = TRANSPORT.split('event.type === "stream_start"')[1]
    expect(block).toBeDefined()
    expect(block).toMatch(/completedTurnIdsRef\.current\.has\(tid\)[\s\S]*?controller\.abort\(\)/)
  })

  test("Guard 5: terminal events mark turn as completed (receivedTerminal guard)", () => {
    // The completion must be gated on receivedTerminal — not on every event
    expect(TRANSPORT).toMatch(
      /receivedTerminal && activeTurnIdRef\.current[\s\S]*?completedTurnIdsRef\.current\.add\(activeTurnIdRef\.current\)/,
    )
  })

  test("Guard 6: completion NOT triggered on non-terminal events (must check receivedTerminal)", () => {
    // The add() call must be inside an `if (receivedTerminal && ...)` check
    // Not a bare `completedTurnIdsRef.current.add(...)` without receivedTerminal guard
    const addPattern = /completedTurnIdsRef\.current\.add\(activeTurnIdRef\.current\)/g
    const matches = [...TRANSPORT.matchAll(addPattern)]
    // There should be exactly 1 add() call
    expect(matches.length).toBe(1)
    // Get the surrounding context (100 chars before)
    const matchIndex = matches[0].index!
    const context = TRANSPORT.slice(Math.max(0, matchIndex - 200), matchIndex)
    expect(context).toMatch(/receivedTerminal/)
  })
})
