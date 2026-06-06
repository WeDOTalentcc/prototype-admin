/**
 * Sensor: JobProcessSection — template selector gate + hydration-safe + apply confirm.
 *
 * Skill: harness-engineering (sensor computacional) + lia-testing.
 *
 * Trava 2 P0 (auditoria Paulo 2026-06-06):
 *  - #2 GATE: o seletor de template e "Salvar como template" só aparecem em modo
 *    de edição (isEditing). Antes, apareciam sempre → era possível trocar/sobrescrever
 *    o pipeline da vaga sem clicar em "Editar".
 *  - #1 HIDRATAÇÃO: não usar <select>/<option> nativo (ícone <svg> dentro de <option>
 *    quebrava a hidratação em /pt/jobs). Substituído pelo Select do design system (Radix).
 *  - #2 CONFIRM: aplicar template NÃO dispara onApplyTemplate na renderização — passa por
 *    um AlertDialog de confirmação (ação destrutiva).
 */

import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen } from "@testing-library/react"
import "@testing-library/jest-dom/vitest"
import { JobProcessSection } from "../JobProcessSection"

const onApplyTemplate = vi.fn()
const onSaveAsTemplate = vi.fn()

const templates = [
  { id: "tpl-1", name: "Tech", stages: [{ name: "a" }, { name: "b" }] },
  { id: "tpl-2", name: "Vendas", stages: [{ name: "a" }] },
]

function makeProps(overrides: Record<string, unknown> = {}) {
  return {
    stages: [],
    rawStages: [],
    loadingCompanyPipeline: false,
    isEditing: false,
    LIA_ASSISTED_STAGES: [],
    LIA_ASSISTED_STAGE_NAMES: [],
    addStage: vi.fn(),
    removeStage: vi.fn(),
    updateStage: vi.fn(),
    moveStage: vi.fn(),
    vacancyId: "vac-1",
    templates,
    isLoadingTemplates: false,
    isApplyingTemplate: false,
    onApplyTemplate,
    onSaveAsTemplate,
    isSavingAsTemplate: false,
    ...overrides,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } as any
}

describe("JobProcessSection — template controls gate (#2)", () => {
  beforeEach(() => {
    onApplyTemplate.mockClear()
    onSaveAsTemplate.mockClear()
  })

  it("NÃO mostra controles de template fora do modo de edição", () => {
    render(<JobProcessSection {...makeProps({ isEditing: false })} />)
    expect(screen.queryByText("Aplicar template...")).not.toBeInTheDocument()
    expect(screen.queryByText("Salvar como template")).not.toBeInTheDocument()
  })

  it("mostra controles de template em modo de edição", () => {
    render(<JobProcessSection {...makeProps({ isEditing: true })} />)
    expect(screen.getByText("Aplicar template...")).toBeInTheDocument()
    expect(screen.getByText("Salvar como template")).toBeInTheDocument()
  })
})

describe("JobProcessSection — hidratação segura (#1)", () => {
  it("não renderiza <option> nativo (usa Select do design system)", () => {
    const { container } = render(<JobProcessSection {...makeProps({ isEditing: true })} />)
    expect(container.querySelectorAll("option").length).toBe(0)
  })
})

describe("JobProcessSection — aplicar template exige confirmação (#2)", () => {
  it("não dispara onApplyTemplate na renderização e não abre o diálogo automaticamente", () => {
    render(<JobProcessSection {...makeProps({ isEditing: true })} />)
    expect(onApplyTemplate).not.toHaveBeenCalled()
    expect(screen.queryByText("Aplicar template de pipeline?")).not.toBeInTheDocument()
  })
})
