/**
 * Sprint 3 Parte 2 — adapter canonical tests.
 */
import { describe, expect, it } from "vitest"

import {
  mapCatalogToLegacy,
  mapCatalogListToLegacy,
  mapSectorIdToVertical,
} from "../agent-template-catalog-adapter"
import type { AgentTemplateCatalog } from "@/types/agent-template-catalog"

const FIXTURE: AgentTemplateCatalog = {
  id: "tpl-triagem-tech",
  slug: "triagem-tech",
  name: "Triagem Tech",
  description: "Filtra candidatos tech.",
  category_id: "screening",
  sector_id: "tech",
  system_prompt: "prompt base",
  allowed_tools: ["search_candidates"],
  context_level: "standard",
  max_steps: 8,
  temperature: 0.3,
  enable_memory: true,
  excluded_tools: [],
  tags: ["popular", "tech"],
  vertical_prompts: { tech: "prompt tech" },
  icon: "Code",
  accent_color: "graphite",
  badge_variant: null,
  sort_order: 1,
  is_active: true,
  company_id: null,
  created_at: "2026-05-25T00:00:00Z",
  updated_at: "2026-05-25T00:00:00Z",
}

describe("agent-template-catalog-adapter — sector reverse map", () => {
  it("tech canonical → tech legacy", () => {
    expect(mapSectorIdToVertical("tech")).toBe("tech")
  })

  it("saude (PT-BR canonical) → health (legacy EN)", () => {
    expect(mapSectorIdToVertical("saude")).toBe("health")
  })

  it("educacao → education + varejo → retail", () => {
    expect(mapSectorIdToVertical("educacao")).toBe("education")
    expect(mapSectorIdToVertical("varejo")).toBe("retail")
  })

  it("null/undefined/generico → null (generic)", () => {
    expect(mapSectorIdToVertical(null)).toBeNull()
    expect(mapSectorIdToVertical(undefined)).toBeNull()
    expect(mapSectorIdToVertical("generico")).toBeNull()
  })

  it("sector desconhecido → null fallback safe", () => {
    expect(mapSectorIdToVertical("xpto")).toBeNull()
  })
})

describe("agent-template-catalog-adapter — mapCatalogToLegacy", () => {
  it("renomeia category_id → category e sector_id → vertical", () => {
    const out = mapCatalogToLegacy(FIXTURE)
    expect(out.category).toBe("screening")
    expect(out.vertical).toBe("tech")
  })

  it("propaga campos snake_case canonical sem perda", () => {
    const out = mapCatalogToLegacy(FIXTURE)
    expect(out.system_prompt).toBe("prompt base")
    expect(out.allowed_tools).toEqual(["search_candidates"])
    expect(out.context_level).toBe("standard")
    expect(out.max_steps).toBe(8)
    expect(out.temperature).toBe(0.3)
    expect(out.enable_memory).toBe(true)
    expect(out.tags).toEqual(["popular", "tech"])
  })

  it("icon null no backend → fallback 'Box'", () => {
    const out = mapCatalogToLegacy({ ...FIXTURE, icon: null })
    expect(out.icon).toBe("Box")
  })

  it("domain é derivado de category_id (consumer legacy compat)", () => {
    const out = mapCatalogToLegacy(FIXTURE)
    expect(out.domain).toBe("screening")
  })

  it("vertical_prompts null no backend → undefined no consumer", () => {
    const out = mapCatalogToLegacy({ ...FIXTURE, vertical_prompts: null })
    expect(out.vertical_prompts).toBeUndefined()
  })

  it("sector_id null → vertical null (generic)", () => {
    const out = mapCatalogToLegacy({ ...FIXTURE, sector_id: null })
    expect(out.vertical).toBeNull()
  })
})

describe("agent-template-catalog-adapter — mapCatalogListToLegacy", () => {
  it("mapeia lista mantendo ordem", () => {
    const a = { ...FIXTURE, id: "a" }
    const b = { ...FIXTURE, id: "b", sector_id: "saude" }
    const out = mapCatalogListToLegacy([a, b])
    expect(out).toHaveLength(2)
    expect(out[0].id).toBe("a")
    expect(out[1].id).toBe("b")
    expect(out[1].vertical).toBe("health")
  })

  it("lista vazia → lista vazia (não fallback silencioso)", () => {
    expect(mapCatalogListToLegacy([])).toEqual([])
  })
})
