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
import { render, screen, fireEvent } from "@testing-library/react"
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
    reorderStages: vi.fn(),
    vacancyId: "vac-1",
    templates,
    isLoadingTemplates: false,
    isApplyingTemplate: false,
    onApplyTemplate,
    onSaveAsTemplate,
    isSavingAsTemplate: false,
    ...overrides,
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

describe("JobProcessSection — sub-status/coleta herdados read-only (#5 Fase 1)", () => {
  const stagesWithInherited = [
    {
      stageName: "Triagem",
      name: "screening",
      stageCategory: "system",
      subStatuses: [{ name: "aguardando", display_name: "Aguardando retorno" }],
      dataFields: [{ id: "cpf", displayName: "CPF", category: "document", required: true, auto_collect: false }],
    },
  ]

  it("mostra o acordeão de herança com a contagem", () => {
    render(<JobProcessSection {...makeProps({ isEditing: false, stages: stagesWithInherited })} />)
    expect(screen.getByText(/1 sub-status · 1 campos · herdado/)).toBeInTheDocument()
  })

  it("expande e revela sub-status e campo herdados", () => {
    render(<JobProcessSection {...makeProps({ isEditing: false, stages: stagesWithInherited })} />)
    fireEvent.click(screen.getByText("Sub-status e coleta"))
    expect(screen.getByText("Aguardando retorno")).toBeInTheDocument()
    expect(screen.getByText("CPF")).toBeInTheDocument()
    expect(screen.getByText(/Herdado da empresa/)).toBeInTheDocument()
  })

  it("não mostra o acordeão quando a etapa não tem herança", () => {
    render(<JobProcessSection {...makeProps({ isEditing: false, stages: [{ stageName: "Funil", name: "funnel", stageCategory: "system" }] })} />)
    expect(screen.queryByText("Sub-status e coleta")).not.toBeInTheDocument()
  })
})

describe("JobProcessSection — reordenar por arrastar (#4)", () => {
  const stages = [
    { stageName: "Triagem", name: "screening", stageCategory: "system", isReorderable: false },
    { stageName: "Long List", name: "custom_1", stageCategory: "custom", isReorderable: true },
    { stageName: "Short List", name: "custom_2", stageCategory: "custom", isReorderable: true },
  ]

  it("mostra handles de arrastar para etapas reordenáveis em modo de edição (sem setas up/down)", () => {
    render(<JobProcessSection {...makeProps({ isEditing: true, stages })} />)
    // 2 etapas custom reordenáveis → 2 handles de arrastar
    expect(screen.getAllByLabelText("Arrastar para reordenar")).toHaveLength(2)
  })

  it("não mostra handles de arrastar fora do modo de edição", () => {
    render(<JobProcessSection {...makeProps({ isEditing: false, stages })} />)
    expect(screen.queryAllByLabelText("Arrastar para reordenar")).toHaveLength(0)
  })
})
