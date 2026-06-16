import { describe, expect, it } from "vitest"
import {
  PAGE_PATHS,
  SPA_ONLY_PAGE_LABELS,
  isDashboardPageLabel,
  labelFromPath,
  pageLabelFromViewParam,
  pathFromLabel,
} from "@/lib/navigation/routes"

describe("navigation/routes", () => {
  it("labelFromPath/pathFromLabel são inversos para toda entrada de PAGE_PATHS", () => {
    for (const [label, path] of Object.entries(PAGE_PATHS)) {
      expect(pathFromLabel(label)).toBe(path)
      expect(labelFromPath(path)).toBe(label)
    }
  })

  it("retorna undefined para entradas desconhecidas (sem fallback silencioso)", () => {
    expect(pathFromLabel("Página Inexistente")).toBeUndefined()
    expect(labelFromPath("/rota-inexistente")).toBeUndefined()
  })

  it("inclui o contrato canônico de Funil de Talentos (replit.md)", () => {
    expect(PAGE_PATHS["Funil de Talentos"]).toBe("/funil-de-talentos")
  })

  it("SPA_ONLY_PAGE_LABELS e PAGE_PATHS são disjuntos (sem ambiguidade conceitual)", () => {
    for (const spaLabel of SPA_ONLY_PAGE_LABELS) {
      expect(spaLabel in PAGE_PATHS).toBe(false)
    }
  })

  it("isDashboardPageLabel reconhece labels com rota e SPA-only, e rejeita o resto", () => {
    for (const label of Object.keys(PAGE_PATHS)) {
      expect(isDashboardPageLabel(label)).toBe(true)
    }
    for (const label of SPA_ONLY_PAGE_LABELS) {
      expect(isDashboardPageLabel(label)).toBe(true)
    }
    expect(isDashboardPageLabel("Painel de Controle")).toBe(false)
    expect(isDashboardPageLabel("Página Inexistente")).toBe(false)
    expect(isDashboardPageLabel("")).toBe(false)
  })
})


describe("navigation/routes — pageLabelFromViewParam (deep-link in-shell)", () => {
  it("resolve labels SPA-only válidos (com e sem encode)", () => {
    expect(pageLabelFromViewParam("Indicadores")).toBe("Indicadores")
    expect(pageLabelFromViewParam("Templates")).toBe("Templates")
    expect(pageLabelFromViewParam(encodeURIComponent("Módulos"))).toBe("Módulos")
  })

  it("resolve também labels com rota (são DashboardPageLabel válidos)", () => {
    expect(pageLabelFromViewParam("Vagas")).toBe("Vagas")
  })

  it("undefined p/ ausente/desconhecido (falha-soft)", () => {
    expect(pageLabelFromViewParam(null)).toBeUndefined()
    expect(pageLabelFromViewParam("")).toBeUndefined()
    expect(pageLabelFromViewParam("Pagina Fake")).toBeUndefined()
  })
})
