/**
 * Sprint 4 v3 — Studio NÃO tem mais tab "Busca de Talentos"
 *
 * Verifica que a tab `id: "search"` foi removida do array de tabs canonical
 * do AgentStudioPage (movida para sub-tab Sourcing do TalentPoolPage).
 *
 * Mantém leve: lê o source via fs e faz assert estático para evitar overhead
 * de mount completo do Studio (que arrasta hooks/SWR/Zustand pesados).
 */
import { describe, it, expect } from "vitest"
import { readFileSync } from "node:fs"
import { join } from "node:path"

const STUDIO_PATH = join(
  __dirname,
  "..",
  "AgentStudioPage.tsx"
)

describe("AgentStudioPage — sem tab Busca de Talentos (Sprint 4 v3)", () => {
  const src = readFileSync(STUDIO_PATH, "utf-8")

  it("não tem entry de tab id 'search'", () => {
    // Pattern canonical do array de tabs: { id: "search", label: ... }
    expect(src).not.toMatch(/\{\s*id:\s*["']search["'],\s*label:/)
  })

  it("não importa MultiStrategySearchPanel (movido pra TalentPoolPage)", () => {
    expect(src).not.toMatch(
      /import\s+MultiStrategySearchPanel\s+from\s+["']@\/components\/pages-agent-studio\/MultiStrategySearchPanel["']/
    )
  })

  it("não renderiza <MultiStrategySearchPanel /> diretamente", () => {
    expect(src).not.toMatch(/<MultiStrategySearchPanel\s*\/>/)
  })

  it("não tem branch activeTab === 'search'", () => {
    expect(src).not.toMatch(/activeTab\s*===\s*["']search["']/)
  })
})
