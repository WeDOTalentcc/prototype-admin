import { describe, it, expect } from "vitest"
import { escapeHtml, cleanAgentResponse, parseChatMarkdown } from "./chat-format"

describe("escapeHtml", () => {
  it("escapes & character", () => {
    expect(escapeHtml("a & b")).toBe("a &amp; b")
  })

  it("escapes < and > characters", () => {
    expect(escapeHtml("<div>")).toBe("&lt;div&gt;")
  })

  it("escapes double and single quotes", () => {
    expect(escapeHtml('"hello"')).toBe("&quot;hello&quot;")
    expect(escapeHtml("it's")).toBe("it&#39;s")
  })

  it("returns unchanged string with no special chars", () => {
    expect(escapeHtml("hello world")).toBe("hello world")
  })
})

describe("cleanAgentResponse", () => {
  it("returns raw string unchanged when no JSON block", () => {
    expect(cleanAgentResponse("Hello there")).toBe("Hello there")
  })

  it("processes a raw JSON agent response and extracts 'response' field", () => {
    const raw = '{"thought": "thinking", "response": "Hi there!"}'
    const result = cleanAgentResponse(raw)
    // The function extracts the response field from top-level JSON
    expect(result).toContain("Hi there!")
  })

  it("trims leading and trailing whitespace/newlines", () => {
    const result = cleanAgentResponse("\n\nHello\n\n")
    expect(result).toBe("Hello")
  })

  it("returns raw string as fallback when result is empty", () => {
    expect(cleanAgentResponse("")).toBe("")
  })

  it("returns text unchanged when it is plain prose", () => {
    const plain = "This is a normal response message."
    expect(cleanAgentResponse(plain)).toBe(plain)
  })

  it("strips complete <thought>...</thought> blocks", () => {
    const raw = "<thought>\n1. O recrutador quer resumo\n2. Ferramentas: check_pipeline\n</thought>\nAqui está seu resumo."
    expect(cleanAgentResponse(raw)).toBe("Aqui está seu resumo.")
  })

  it("strips incomplete <thought> blocks during streaming", () => {
    const raw = "<thought>\n1. Pensando sobre a pergunta\n2. Vou usar search_candidates"
    expect(cleanAgentResponse(raw)).toBe("")
  })

  it("strips multiple <thought> blocks", () => {
    const raw = "<thought>pensamento 1</thought>Olá!<thought>pensamento 2</thought> Como posso ajudar?"
    expect(cleanAgentResponse(raw)).toBe("Olá! Como posso ajudar?")
  })

  it("handles case-insensitive <Thought> tags", () => {
    const raw = "<Thought>raciocínio</Thought>Resposta final."
    expect(cleanAgentResponse(raw)).toBe("Resposta final.")
  })
})

describe("parseChatMarkdown", () => {
  it("converts **bold** to <strong>", () => {
    const result = parseChatMarkdown("This is **bold** text")
    expect(result).toContain("<strong>bold</strong>")
  })

  it("converts *italic* to <em>", () => {
    const result = parseChatMarkdown("This is *italic* text")
    expect(result).toContain("<em>italic</em>")
  })

  it("converts unordered list items to <ul><li>", () => {
    const result = parseChatMarkdown("- Item 1\n- Item 2")
    expect(result).toContain("<ul")
    expect(result).toContain("<li>Item 1</li>")
    expect(result).toContain("<li>Item 2</li>")
  })

  it("escapes HTML special chars in plain text", () => {
    const result = parseChatMarkdown("<script>alert(1)</script>")
    expect(result).not.toContain("<script>")
    expect(result).toContain("&lt;script&gt;")
  })

  it("renders ordered list items to <ol><li>", () => {
    const result = parseChatMarkdown("1. First\n2. Second")
    expect(result).toContain("<ol")
    expect(result).toContain("<li>First</li>")
  })
})
