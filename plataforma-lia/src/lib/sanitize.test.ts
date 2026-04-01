/**
 * Tests for sanitize.ts
 * We test:
 * 1. The SSR strip logic (strips tags but NOT inner text - this is the actual behavior)
 * 2. The pure tag-stripping logic inline
 */
import { describe, it, expect } from "vitest"

// ── Pure logic tests: the tag-stripping regex used in SSR branch ──────────────
describe("SSR tag-stripping regex (inline simulation)", () => {
  function ssrStrip(html: string): string {
    return html.replace(/<[^>]*>/g, "")
  }

  it("strips simple tags, inner text remains", () => {
    const result = ssrStrip("<script>alert(1)</script>Hello")
    expect(result).not.toContain("<script>")
    expect(result).not.toContain("</script>")
    expect(result).toContain("Hello")
  })

  it("strips multiple tags, text content preserved", () => {
    const result = ssrStrip("<b>Bold</b> and <i>italic</i>")
    expect(result).toBe("Bold and italic")
  })

  it("handles empty string", () => {
    expect(ssrStrip("")).toBe("")
  })

  it("handles string with no tags", () => {
    expect(ssrStrip("plain text only")).toBe("plain text only")
  })

  it("strips nested tags", () => {
    const result = ssrStrip("<p><b>nested</b></p>")
    expect(result).toBe("nested")
  })

  it("strips self-closing tags", () => {
    const result = ssrStrip("text<br/>more")
    expect(result).toBe("textmore")
  })

  it("strips tags with attributes", () => {
    const result = ssrStrip('<a href="http://example.com">link</a>')
    expect(result).toBe("link")
  })
})

// ── Test that sanitize functions exist and are callable ────────────────────────
describe("sanitize module exports", () => {
  it("sanitizeHtml and sanitizeEmailHtml are exported functions", async () => {
    const { sanitizeHtml, sanitizeEmailHtml } = await import("./sanitize")
    expect(typeof sanitizeHtml).toBe("function")
    expect(typeof sanitizeEmailHtml).toBe("function")
  })

  it("sanitizeHtml returns a string", async () => {
    const { sanitizeHtml } = await import("./sanitize")
    const result = sanitizeHtml("Hello world")
    expect(typeof result).toBe("string")
  })

  it("sanitizeEmailHtml returns a string", async () => {
    const { sanitizeEmailHtml } = await import("./sanitize")
    const result = sanitizeEmailHtml("Hello world")
    expect(typeof result).toBe("string")
  })
})
