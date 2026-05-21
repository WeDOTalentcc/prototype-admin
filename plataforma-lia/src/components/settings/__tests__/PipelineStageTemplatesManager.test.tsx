/**
 * Smoke tests — PipelineStageTemplatesManager (P0.G #1)
 *
 * Cobre patterns canonical:
 *  1. render: monta componente, espera lista render com nome do template
 *  2. filter chips: clique em "Master canonical" / "Customs da empresa" muda lista
 *  3. startCreate: clique em "Nova stage" abre form de criação
 *  4. permission gate: isAdmin=false + currentUserId=null → edit/delete não aparecem
 *     em customs alheios (created_by !== currentUserId)
 *
 * Pattern: mock do hook canonical via vi.mock; smoke render apenas. Não testa
 * integration com API real (esse é trabalho dos hooks tests).
 */
import React from "react"
import { describe, test, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, within } from "@testing-library/react"

import { PipelineStageTemplatesManager } from "../PipelineStageTemplatesManager"
import type { PipelineStageTemplate } from "@/hooks/pipeline/use-pipeline-stage-templates"

const masterTemplate: PipelineStageTemplate = {
  id: "master-1",
  company_id: null,
  is_master_template: true,
  parent_template_id: null,
  data: {
    label: "Triagem CV",
    key: "triagem_cv",
    order: 100,
    is_default_in_pipeline: true,
    action_behavior: "screening",
    default_channel: "email",
  },
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  created_by: null,
  deleted_at: null,
}

const customOwnTemplate: PipelineStageTemplate = {
  id: "custom-own-1",
  company_id: "company-uuid",
  is_master_template: false,
  parent_template_id: null,
  data: {
    label: "Stage minha",
    key: "stage_minha",
    order: 200,
    is_default_in_pipeline: false,
  },
  created_at: "2026-01-02T00:00:00Z",
  updated_at: "2026-01-02T00:00:00Z",
  created_by: "user-self",
  deleted_at: null,
}

const customForeignTemplate: PipelineStageTemplate = {
  id: "custom-foreign-1",
  company_id: "company-uuid",
  is_master_template: false,
  parent_template_id: null,
  data: {
    label: "Stage alheia",
    key: "stage_alheia",
    order: 300,
    is_default_in_pipeline: false,
  },
  created_at: "2026-01-03T00:00:00Z",
  updated_at: "2026-01-03T00:00:00Z",
  created_by: "user-other",
  deleted_at: null,
}

const hookReturnValue = {
  templates: [masterTemplate, customOwnTemplate, customForeignTemplate],
  masterCount: 1,
  customCount: 2,
  total: 3,
  isLoading: false,
  error: null,
  refetch: vi.fn(),
  createCustom: vi.fn(),
  updateTemplate: vi.fn(),
  deleteTemplate: vi.fn(),
  customizeMaster: vi.fn(),
}

vi.mock("@/hooks/pipeline/use-pipeline-stage-templates", async () => {
  const actual = await vi.importActual<
    typeof import("@/hooks/pipeline/use-pipeline-stage-templates")
  >("@/hooks/pipeline/use-pipeline-stage-templates")
  return {
    ...actual,
    usePipelineStageTemplates: vi.fn(() => hookReturnValue),
  }
})

describe("PipelineStageTemplatesManager — smoke (P0.G #1)", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  test("renders Manager card title + lista de templates", () => {
    render(
      <PipelineStageTemplatesManager isAdmin={true} currentUserId="user-self" />,
    )
    expect(
      screen.getByText("Gerenciador de Stages do Pipeline"),
    ).toBeInTheDocument()
    expect(screen.getByText("Triagem CV")).toBeInTheDocument()
    expect(screen.getByText("Stage minha")).toBeInTheDocument()
    expect(screen.getByText("Stage alheia")).toBeInTheDocument()
  })

  test("filter chips: clicar 'Master canonical' filtra só masters", () => {
    render(
      <PipelineStageTemplatesManager isAdmin={true} currentUserId="user-self" />,
    )
    // antes: vê custom e master
    expect(screen.getByText("Stage minha")).toBeInTheDocument()

    fireEvent.click(screen.getByRole("button", { name: /Master canonical/i }))

    expect(screen.getByText("Triagem CV")).toBeInTheDocument()
    expect(screen.queryByText("Stage minha")).not.toBeInTheDocument()
    expect(screen.queryByText("Stage alheia")).not.toBeInTheDocument()
  })

  test("startCreate: clicar 'Nova stage' abre form de criação", () => {
    render(
      <PipelineStageTemplatesManager isAdmin={true} currentUserId="user-self" />,
    )
    expect(screen.queryByText("Criar stage nova")).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole("button", { name: /Nova stage/i }))

    expect(screen.getByText("Criar stage nova")).toBeInTheDocument()
    expect(
      screen.getByPlaceholderText(/Label \(ex: Triagem CV\)/i),
    ).toBeInTheDocument()
  })

  test("permission gate: isAdmin=false + currentUserId=null esconde edit/delete em customs alheios", () => {
    render(
      <PipelineStageTemplatesManager isAdmin={false} currentUserId={null} />,
    )

    // Stage alheia (created_by = "user-other"): sem edit/delete
    const foreignRow = screen.getByText("Stage alheia").closest("div.flex.items-start")
    expect(foreignRow).not.toBeNull()
    const foreignButtons = within(foreignRow as HTMLElement).queryAllByRole("button")
    // Custom alheio sem ser admin: nenhum botão (sem customize porque não é master,
    // sem edit porque não é owner, sem delete porque não é admin)
    expect(foreignButtons.length).toBe(0)

    // Master: aparece apenas o botão "Customizar" (Copy icon)
    const masterRow = screen.getByText("Triagem CV").closest("div.flex.items-start")
    const masterButtons = within(masterRow as HTMLElement).queryAllByRole("button")
    expect(masterButtons.length).toBe(1)
    expect(masterButtons[0]).toHaveAttribute("title", "Customizar (cria cópia)")
  })
})
