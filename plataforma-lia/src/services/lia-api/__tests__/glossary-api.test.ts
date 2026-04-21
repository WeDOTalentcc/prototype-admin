import { afterEach, describe, expect, it, vi } from "vitest"
import {
  formatGlossaryEntryMarkdown,
  lookupGlossaryTerm,
} from "../glossary-api"

const mockFetch = (responder: (url: string) => Response | Promise<Response>) => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo) => {
      const url = typeof input === "string" ? input : input.toString()
      return responder(url)
    }),
  )
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe("lookupGlossaryTerm", () => {
  it("encodes the term and resolves with the entry on 200", async () => {
    let calledUrl = ""
    mockFetch((url) => {
      calledUrl = url
      return new Response(
        JSON.stringify({
          success: true,
          data: {
            name: "WSI (Workforce Suitability Index)",
            sigla: "WSI",
            definition: "Indice composto.",
            category: "Scoring",
          },
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      )
    })
    const result = await lookupGlossaryTerm("WSI Final")
    expect(calledUrl).toBe("/api/lia/api/v1/glossary/terms/WSI%20Final")
    expect(result.ok).toBe(true)
    if (result.ok) {
      expect(result.entry.sigla).toBe("WSI")
    }
  })

  it("returns a friendly miss message on 404", async () => {
    mockFetch(() => new Response("{}", { status: 404 }))
    const result = await lookupGlossaryTerm("inexistente")
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.status).toBe(404)
      expect(result.message.toLowerCase()).toContain("nao encontrei")
    }
  })

  it("rejects empty terms without hitting the network", async () => {
    const fetchSpy = vi.fn()
    vi.stubGlobal("fetch", fetchSpy)
    const result = await lookupGlossaryTerm("   ")
    expect(result.ok).toBe(false)
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it("surfaces network failures as a non-OK result", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new Error("offline")
      }),
    )
    const result = await lookupGlossaryTerm("WSI")
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.message.toLowerCase()).toContain("sem conexao")
    }
  })
})

describe("formatGlossaryEntryMarkdown", () => {
  it("includes the sigla in the heading when present", () => {
    const md = formatGlossaryEntryMarkdown({
      name: "WSI",
      sigla: "WSI",
      definition: "Indice composto.",
      category: "Scoring",
    })
    expect(md).toContain("**WSI** (WSI)")
    expect(md).toContain("Indice composto.")
    expect(md).toContain("Categoria: Scoring")
    expect(md).toContain("docs/GLOSSARY.md")
  })

  it("omits the parenthesised sigla when missing", () => {
    const md = formatGlossaryEntryMarkdown({
      name: "Bloom",
      sigla: "",
      definition: "Taxonomia.",
      category: "Behavioral",
    })
    expect(md).toContain("**Bloom**")
    expect(md).not.toMatch(/\*\*Bloom\*\*\s*\(/)
  })
})
