/**
 * Tests — GlossaryHighlightedText component (Task #759)
 *
 * - Wraps canonical glossary terms in highlight spans
 * - Skips terms that appear inside <a>/<code>/<pre> blocks
 * - Fetches the canonical definition on hover from the same endpoint /definir uses
 * - Renders the tooltip with the definition once it arrives
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { __resetGlossaryCache } from "@/services/lia-api/glossary-api"
import { GlossaryHighlightedText } from "../glossary-highlighted-text"

vi.mock("@/lib/sanitize", () => ({
  sanitizeHtml: (s: string) => s,
}))

const TERMS_PAYLOAD = {
  success: true,
  data: {
    terms: [
      { name: "WSI", sigla: "WSI", definition: "ignored", category: "Scoring" },
      { name: "Bloom", sigla: "", definition: "ignored", category: "Behavioral" },
    ],
    total_loaded: 2,
  },
}

const DEFINITION_PAYLOAD = {
  success: true,
  data: {
    name: "WSI (Workforce Suitability Index)",
    sigla: "WSI",
    definition: "Indice composto que combina aderencia tecnica e comportamental.",
    category: "Scoring",
  },
}

function makeFetch() {
  return vi.fn(async (input: RequestInfo) => {
    const url = typeof input === "string" ? input : input.toString()
    if (url === "/api/backend-proxy/api/v1/glossary/terms") {
      return new Response(JSON.stringify(TERMS_PAYLOAD), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    }
    if (url.startsWith("/api/backend-proxy/api/v1/glossary/terms/")) {
      return new Response(JSON.stringify(DEFINITION_PAYLOAD), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    }
    return new Response("not found", { status: 404 })
  })
}

beforeEach(() => {
  __resetGlossaryCache()
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe("GlossaryHighlightedText", () => {
  it("highlights canonical terms in the rendered HTML", async () => {
    vi.stubGlobal("fetch", makeFetch())
    render(<GlossaryHighlightedText html="<p>O WSI usa Bloom para ponderar.</p>" />)
    await waitFor(() => {
      expect(document.querySelectorAll("[data-glossary-term]")).toHaveLength(2)
    })
    const labels = Array.from(
      document.querySelectorAll("[data-glossary-term]"),
    ).map((el) => el.getAttribute("data-glossary-term"))
    expect(labels).toEqual(expect.arrayContaining(["WSI", "Bloom"]))
  })

  it("does not highlight terms that appear inside code or anchor blocks", async () => {
    vi.stubGlobal("fetch", makeFetch())
    render(
      <GlossaryHighlightedText html='<p>Veja <a href="/x">WSI</a> e <code>Bloom</code>.</p>' />,
    )
    await waitFor(() => {
      expect(document.querySelector("[data-glossary-term]")).toBeNull()
    })
  })

  it("opens the tooltip with the canonical definition on hover", async () => {
    vi.stubGlobal("fetch", makeFetch())
    render(<GlossaryHighlightedText html="<p>O WSI orienta a triagem.</p>" />)
    const trigger = await waitFor(() => {
      const node = document.querySelector("[data-glossary-term]")
      if (!node) throw new Error("no trigger yet")
      return node as HTMLElement
    })
    fireEvent.mouseOver(trigger)
    await screen.findByText(
      "Indice composto que combina aderencia tecnica e comportamental.",
    )
  })

  it("opens the side drawer with the full entry when the term is clicked", async () => {
    vi.stubGlobal("fetch", makeFetch())
    render(<GlossaryHighlightedText html="<p>O WSI orienta a triagem.</p>" />)
    const trigger = await waitFor(() => {
      const node = document.querySelector("[data-glossary-term]")
      if (!node) throw new Error("no trigger yet")
      return node as HTMLElement
    })
    fireEvent.click(trigger)
    const drawer = await screen.findByTestId("glossary-drawer")
    expect(drawer).toBeInTheDocument()
    await screen.findByText(
      "Indice composto que combina aderencia tecnica e comportamental.",
    )
    // Deep link affordances are visible inside the drawer
    expect(screen.getByTestId("glossary-drawer-copy-link")).toBeInTheDocument()
    const docsLink = screen.getByTestId(
      "glossary-drawer-docs-link",
    ) as HTMLAnchorElement
    expect(docsLink.getAttribute("href")).toContain(
      "/docs/GLOSSARY.md#wsi-workforce-suitability-index",
    )
  })

  it("opens the drawer automatically when ?glossary= is present in the URL", async () => {
    vi.stubGlobal("fetch", makeFetch())
    window.history.replaceState({}, "", "/?glossary=WSI")
    render(<GlossaryHighlightedText html="<p>Sem termos aqui.</p>" />)
    await screen.findByTestId("glossary-drawer")
    await screen.findByText(
      "Indice composto que combina aderencia tecnica e comportamental.",
    )
    window.history.replaceState({}, "", "/")
  })

  it("still opens the drawer via deep link when the terms list endpoint fails", async () => {
    const fetchImpl = vi.fn(async (input: RequestInfo) => {
      const url = typeof input === "string" ? input : input.toString()
      if (url === "/api/backend-proxy/api/v1/glossary/terms") {
        return new Response("boom", { status: 500 })
      }
      if (url.startsWith("/api/backend-proxy/api/v1/glossary/terms/")) {
        return new Response(JSON.stringify(DEFINITION_PAYLOAD), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      }
      return new Response("not found", { status: 404 })
    })
    vi.stubGlobal("fetch", fetchImpl)
    window.history.replaceState({}, "", "/?glossary=WSI")
    render(<GlossaryHighlightedText html="<p>Sem termos aqui.</p>" />)
    await screen.findByTestId("glossary-drawer")
    await screen.findByText(
      "Indice composto que combina aderencia tecnica e comportamental.",
    )
    window.history.replaceState({}, "", "/")
  })
})
