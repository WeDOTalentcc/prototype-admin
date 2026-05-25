/**
 * Sprint 5 — AgentStudioPage decommission do showCreateModal (path #3).
 *
 * Verifica que o estado legado `showCreateModal` + `setSelectedTemplate`
 * + função inline `CreateAgentModal` foram removidos. O sector tile click
 * agora abre o wizard canonical (CreateAgentWizard) via `openWizard(...)`
 * com `initialConfig.prefilledSector` + name derivado.
 *
 * Pattern: source-level static assertions (canonical do
 * AgentStudioPage.tabsNoSearch.test.tsx). Evita overhead de mount.
 *
 * Plan ref: AGENT_STUDIO_IMPLEMENTATION_PLAN.md §6 Sprint 5 +
 * AGENT_STUDIO_DEEP_AUDIT.md A.7 (consolidação dos 6 entry-points).
 */
import { describe, it, expect } from "vitest"
import { readFileSync } from "node:fs"
import { join } from "node:path"

const STUDIO_PATH = join(__dirname, "..", "AgentStudioPage.tsx")

describe("AgentStudioPage — Sprint 5 decommission CreateAgentModal", () => {
  const src = readFileSync(STUDIO_PATH, "utf-8")

  it("não declara state showCreateModal", () => {
    expect(src).not.toMatch(/\[\s*showCreateModal\s*,\s*setShowCreateModal\s*\]/)
  })

  it("não chama setShowCreateModal em lugar nenhum", () => {
    expect(src).not.toMatch(/setShowCreateModal\s*\(/)
  })

  it("não declara state selectedTemplate (era exclusivo do modal antigo)", () => {
    expect(src).not.toMatch(
      /\[\s*selectedTemplate\s*,\s*setSelectedTemplate\s*\]/,
    )
  })

  it("não define função inline CreateAgentModal", () => {
    expect(src).not.toMatch(/function\s+CreateAgentModal\s*\(/)
  })

  it("sector tile onClick chama openWizard (não setShowCreateModal)", () => {
    // Pattern canonical pós-Sprint 5: button do sector tile invoca openWizard
    // com prefilledSector. Match permissivo (qualquer assinatura openWizard
    // dentro do map dos templates) — mas garante que showCreateModal sumiu.
    expect(src).toMatch(/openWizard\s*\(/)
  })

  it("import de DialogFooter (era usado apenas pelo modal removido) foi removido", () => {
    // DialogFooter era usado SÓ no CreateAgentModal interno (linhas 1137/1162).
    expect(src).not.toMatch(/\bDialogFooter\b/)
  })
})
