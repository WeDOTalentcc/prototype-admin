/**
 * Tests for chat-page/constants — emptyConversation and modernConversation
 * These are data constants (no DOM), safe to test without rendering.
 */
import { describe, it, expect } from "vitest"
import { emptyConversation } from "./empty-conversations"
import { modernConversation } from "./modern-conversations"

describe("emptyConversation", () => {
  it("is an array", () => {
    expect(Array.isArray(emptyConversation)).toBe(true)
  })

  it("is empty (no messages)", () => {
    expect(emptyConversation).toHaveLength(0)
  })
})

describe("modernConversation", () => {
  it("is an array", () => {
    expect(Array.isArray(modernConversation)).toBe(true)
  })

  it("has at least one message", () => {
    expect(modernConversation.length).toBeGreaterThan(0)
  })

  it("each message has id, sender, and timestamp", () => {
    for (const msg of modernConversation) {
      expect(msg).toHaveProperty("id")
      expect(msg).toHaveProperty("sender")
      expect(msg).toHaveProperty("timestamp")
    }
  })

  it("messages have sender 'lia' or 'user'", () => {
    const validSenders = new Set(["lia", "user"])
    for (const msg of modernConversation) {
      expect(validSenders.has(msg.sender)).toBe(true)
    }
  })

  it("has at least one 'lia' message and one 'user' message", () => {
    const liaMessages = modernConversation.filter(m => m.sender === "lia")
    const userMessages = modernConversation.filter(m => m.sender === "user")
    expect(liaMessages.length).toBeGreaterThan(0)
    expect(userMessages.length).toBeGreaterThan(0)
  })

  it("message ids are all numbers", () => {
    for (const msg of modernConversation) {
      expect(typeof msg.id).toBe("number")
    }
  })

  it("message timestamps are non-empty strings", () => {
    for (const msg of modernConversation) {
      expect(typeof msg.timestamp).toBe("string")
      expect(msg.timestamp.length).toBeGreaterThan(0)
    }
  })
})
