import { describe, it, expect } from "vitest"
import { buildSavedSearchPayload } from "./saved-search-utils"

// Pina P1-7: saveCurrentSearch gravava em sessionStorage('current-search-data')
// que ninguem le -> "Busca salva!" mas nunca aparecia na aba. O fix monta o
// payload canonico e chama talentFunnel.addSavedSearch (produtor que a aba le).
describe("buildSavedSearchPayload (P1-7)", () => {
  it("monta nome com prefixo+data, query do termo, filtros dos quickFilters", () => {
    const p = buildSavedSearchPayload({
      searchTerm: "Product Manager",
      quickFilters: ["remoto", "pleno"],
      dateLabel: "06/06/2026",
      namePrefix: "Busca",
    })
    expect(p.name).toBe("Busca 06/06/2026")
    expect(p.query).toBe("Product Manager")
    expect(p.filters).toEqual({ quickFilters: ["remoto", "pleno"] })
  })

  it("default mode=natural, source=local quando nao informados", () => {
    const p = buildSavedSearchPayload({ searchTerm: "x", dateLabel: "d", namePrefix: "Busca" })
    expect(p.mode).toBe("natural")
    expect(p.source).toBe("local")
    expect(p.filters).toBeUndefined()
  })

  it("respeita mode/source explicitos", () => {
    const p = buildSavedSearchPayload({
      searchTerm: "x", dateLabel: "d", namePrefix: "Busca", mode: "boolean", source: "hybrid",
    })
    expect(p.mode).toBe("boolean")
    expect(p.source).toBe("hybrid")
  })
})
