import { describe, it, expect, vi } from "vitest"
import {
  navigationCatalog,
  buildNavigationCommands,
  buildActionCommands,
} from "@/lib/navigation/navigation-commands"
import { CANONICAL_PAGES, canonicalPageToUrl } from "@/lib/canonical-pages"

describe("Fase 1 — navigationCatalog (DRY de canonical-pages.ts)", () => {
  it("inclui páginas navegáveis e exclui detalhes-sem-id + general", () => {
    const ids = navigationCatalog("pt").map((c) => c.page)
    expect(ids).toContain(CANONICAL_PAGES.VAGAS)
    expect(ids).toContain(CANONICAL_PAGES.CONFIGURACOES)
    expect(ids).toContain(CANONICAL_PAGES.DASHBOARD)
    expect(ids).not.toContain(CANONICAL_PAGES.VAGA_DETALHE) // precisa id
    expect(ids).not.toContain(CANONICAL_PAGES.GENERAL)
  })

  it("url de cada item bate com canonicalPageToUrl (fonte única)", () => {
    for (const item of navigationCatalog("pt")) {
      expect(item.url).toBe(canonicalPageToUrl(item.page, "pt"))
    }
  })

  it("INVARIANTE anti-drift: cobre TODA página com rota não-null", () => {
    const navigable = (Object.values(CANONICAL_PAGES) as string[]).filter(
      (p) => canonicalPageToUrl(p as never, "pt") !== null,
    )
    expect(navigationCatalog("pt").length).toBe(navigable.length)
  })

  it("respeita o locale", () => {
    const cat = navigationCatalog("en")
    const vagas = cat.find((c) => c.page === CANONICAL_PAGES.VAGAS)
    expect(vagas?.url).toBe("/en/jobs")
  })
})

describe("Fase 1 — buildNavigationCommands (CommandPalette)", () => {
  it("gera CommandItem categoria navigation, id nav-, onSelect navega", () => {
    const navigate = vi.fn()
    const cmds = buildNavigationCommands({ locale: "pt", navigate })
    expect(cmds.length).toBeGreaterThan(0)
    for (const c of cmds) {
      expect(c.id.startsWith("nav-")).toBe(true)
      expect(c.category).toBe("navigation")
      expect(c.label.startsWith("Ir para ")).toBe(true)
    }
    const vagas = cmds.find((c) => c.id === `nav-${CANONICAL_PAGES.VAGAS}`)
    expect(vagas).toBeDefined()
    vagas!.onSelect()
    expect(navigate).toHaveBeenCalledWith("/pt/jobs")
  })
})


describe("Fase 2 — buildActionCommands (catálogo do capability_map)", () => {
  it("gera CommandItem categoria actions, id action-, onSelect manda label à LIA", () => {
    const sendMessage = vi.fn()
    const items = [
      { intent: "compare_candidates", label: "Comparar candidatos" },
      { intent: "close_job", label: "Encerrar vaga", requires_confirmation: true },
    ]
    const cmds = buildActionCommands(items, sendMessage)
    expect(cmds).toHaveLength(2)
    expect(cmds[0].id).toBe("action-compare_candidates")
    expect(cmds[0].category).toBe("actions")
    cmds[0].onSelect()
    expect(sendMessage).toHaveBeenCalledWith("Comparar candidatos")
    // destrutivo sinaliza confirmação
    expect(cmds[1].description).toContain("confirma")
  })

  it("lista vazia → nenhum comando (sem crash)", () => {
    expect(buildActionCommands([], () => {})).toEqual([])
  })
})
