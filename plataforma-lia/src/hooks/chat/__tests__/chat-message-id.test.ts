import { describe, expect, it, vi } from "vitest"
import {
  createMessageId,
  dedupeAppend,
  type LiaChatMessage,
} from "@/hooks/chat/lia-chat-connection-types"

function msg(id: string, content = "x"): LiaChatMessage {
  return { id, sender: "lia", content, timestamp: "00:00" }
}

describe("createMessageId — collision-safe message ids", () => {
  it("returns unique ids even when minted within the same millisecond", () => {
    // Freeze the clock: the legacy `lia-${Date.now()}` pattern returns the SAME
    // string for every call in one tick (a turn emitting text + an action/card
    // synchronously) → React "two children with the same key" → list crash.
    const spy = vi.spyOn(Date, "now").mockReturnValue(1_700_000_000_000)
    try {
      const ids = Array.from({ length: 500 }, () => createMessageId("lia"))
      expect(new Set(ids).size).toBe(ids.length)
      expect(ids.every((id) => id.startsWith("lia-"))).toBe(true)
    } finally {
      spy.mockRestore()
    }
  })

  it("keeps the human-readable prefix", () => {
    expect(createMessageId("user")).toMatch(/^user-/)
    expect(createMessageId("lia")).toMatch(/^lia-/)
  })
})

describe("dedupeAppend — chatMessages never holds two items with the same id", () => {
  it("uniquifies an incoming message whose id already exists (lossless, keeps both)", () => {
    // Reproduces the backend Fase2 case: a message frame + a card frame that
    // share the same backend id. The store must keep BOTH (text + card) while
    // guaranteeing distinct React keys.
    const a = msg("lia-123", "first")
    const b = msg("lia-123", "second-card")
    const list = dedupeAppend(dedupeAppend([], a), b)
    expect(list).toHaveLength(2)
    expect(new Set(list.map((m) => m.id)).size).toBe(2)
    expect(list[0].content).toBe("first")
    expect(list[1].content).toBe("second-card")
  })

  it("appends normally when the id is new", () => {
    const list = dedupeAppend([msg("lia-1")], msg("lia-2"))
    expect(list.map((m) => m.id)).toEqual(["lia-1", "lia-2"])
  })
})
