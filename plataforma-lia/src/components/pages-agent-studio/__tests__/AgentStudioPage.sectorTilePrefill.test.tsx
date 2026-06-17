/**
 * AgentStudioPage — sentinela do entry-point "Criar agente" (sector tile + custom).
 *
 * Histórico: o overhaul do Estúdio de Agentes (Fase 2) removeu a função inline
 * `CreateAgentModal` (path #3 antigo) e consolidou a criação de sourcing agent
 * no modal canonical `<CreateCustomAgentModal sourcingCreate />`. O clique no
 * sector tile define `selectedTemplate` + abre `showCreateModal`; o template
 * selecionado é entregue ao modal via `initialTemplate={selectedTemplate}`.
 *
 * Este teste pina:
 *   (a) a remoção definitiva do código morto antigo (regressão: não pode voltar);
 *   (b) o wiring atual do entry-point de criação.
 *
 * Pattern: source-level static assertions (canonical do
 * AgentStudioPage.tabsNoSearch.test.tsx). Evita overhead de mount.
 */
import { describe, it, expect } from "vitest"
import { readFileSync } from "node:fs"
import { join } from "node:path"

const STUDIO_PATH = join(__dirname, "..", "AgentStudioPage.tsx")

describe("AgentStudioPage — entry-point de criação (sector tile + custom)", () => {
  const src = readFileSync(STUDIO_PATH, "utf-8")

  // --- (a) Código morto antigo removido (guarda de regressão) ---

  it("não define função inline CreateAgentModal (removida no overhaul Fase 2)", () => {
    expect(src).not.toMatch(/function\s+CreateAgentModal\s*\(/)
  })

  it("não importa DialogFooter (era usado apenas pelo modal inline removido)", () => {
    expect(src).not.toMatch(/\bDialogFooter\b/)
  })

  // --- (b) Wiring atual do entry-point de criação ---

  it("monta o modal canonical CreateCustomAgentModal com flag sourcingCreate", () => {
    expect(src).toMatch(/<CreateCustomAgentModal[\s\S]*?sourcingCreate/)
  })

  it("entrega o template selecionado ao modal via initialTemplate={selectedTemplate}", () => {
    expect(src).toMatch(/initialTemplate=\{selectedTemplate\}/)
  })

  it("clique no sector tile define selectedTemplate(tpl) e abre showCreateModal", () => {
    expect(src).toMatch(
      /setSelectedTemplate\(tpl\)\s*;\s*setShowCreateModal\(true\)/,
    )
  })

  it("botão de agente custom abre showCreateModal sem template (selectedTemplate null)", () => {
    expect(src).toMatch(
      /setSelectedTemplate\(null\)\s*;\s*setShowCreateModal\(true\)/,
    )
  })
})
