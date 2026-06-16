/**
 * SentenceBuilder canonical impeccable — Sprint A.1
 *
 * Sensor canonical: garante que automation = frase clicavel em PT-BR
 * (não form grid). Detecta regressão pra paradigma anti-canonical.
 */

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"

import {
  SentenceBuilder,
  isValid,
  suggestName,
  type ActionOption,
  type ConditionFieldDef,
  type ConditionOperator,
  type SentenceBuilderState,
  type TriggerOption,
} from "../SentenceBuilder"

// ── Fixtures ──────────────────────────────────────────────────────────────

const mockTriggers: TriggerOption[] = [
  {
    value: "stage_changed",
    label: "chega na etapa",
    description: "candidato muda de etapa",
    params: [
      {
        name: "stage",
        label: "etapa",
        type: "select",
        options: [
          { value: "interview", label: "Entrevista" },
          { value: "offer", label: "Oferta" },
        ],
      },
    ],
  },
  {
    value: "wsi_completed",
    label: "completa WSI",
  },
]

const mockActions: ActionOption[] = [
  {
    value: "send_whatsapp",
    label: "envie WhatsApp",
    params: [{ name: "template", label: "template", type: "string" }],
  },
  {
    value: "move_stage",
    label: "mova para etapa",
  },
]

const mockOperators: ConditionOperator[] = [
  { value: "eq", label: "for igual a" },
  { value: "gt", label: "for maior que" },
]

const mockFields: ConditionFieldDef[] = [
  { value: "wsi_score", label: "score WSI", type: "number" },
  {
    value: "department",
    label: "departamento",
    type: "select",
    options: [
      { value: "eng", label: "Engenharia" },
      { value: "sales", label: "Vendas" },
    ],
  },
]

// ── Helpers ───────────────────────────────────────────────────────────────

function renderBuilder(overrides: Partial<React.ComponentProps<typeof SentenceBuilder>> = {}) {
  const onSave = vi.fn()
  const onCancel = vi.fn()
  const utils = render(
    <SentenceBuilder
      triggers={mockTriggers}
      actions={mockActions}
      operators={mockOperators}
      conditionFields={mockFields}
      onSave={onSave}
      onCancel={onCancel}
      {...overrides}
    />,
  )
  return { ...utils, onSave, onCancel }
}

// ── Pure logic ────────────────────────────────────────────────────────────

describe("SentenceBuilder — pure helpers", () => {
  it("isValid: false quando trigger missing", () => {
    expect(
      isValid({ conditions: [], actions: [{ type: "send_whatsapp", params: {} }] }),
    ).toBe(false)
  })

  it("isValid: false quando nenhuma action", () => {
    expect(
      isValid({ trigger: { type: "stage_changed", params: {} }, conditions: [], actions: [] }),
    ).toBe(false)
  })

  it("isValid: false quando condition incompleta", () => {
    expect(
      isValid({
        trigger: { type: "stage_changed", params: {} },
        conditions: [{ field: "wsi_score", operator: "gt", value: "" }],
        actions: [{ type: "send_whatsapp", params: {} }],
      }),
    ).toBe(false)
  })

  it("isValid: true quando trigger + 1 action", () => {
    expect(
      isValid({
        trigger: { type: "stage_changed", params: {} },
        conditions: [],
        actions: [{ type: "send_whatsapp", params: {} }],
      }),
    ).toBe(true)
  })

  it("suggestName combina trigger + first action em PT-BR canonical", () => {
    const name = suggestName(
      {
        trigger: { type: "stage_changed", params: {} },
        conditions: [],
        actions: [{ type: "send_whatsapp", params: {} }],
      },
      mockTriggers,
      mockActions,
    )
    expect(name).toBe("Quando chega na etapa → envie WhatsApp")
  })
})

// ── Render ────────────────────────────────────────────────────────────────

describe("SentenceBuilder — rendering canonical impeccable", () => {
  it("renderiza frase canonical inicial em PT-BR vazia", () => {
    renderBuilder()
    expect(screen.getByTestId("sentence-builder")).toBeInTheDocument()
    expect(screen.getByText("Quando")).toBeInTheDocument()
    expect(screen.getByTestId("slot-trigger")).toHaveTextContent("selecione um gatilho")
    expect(screen.getByTestId("add-condition")).toBeInTheDocument()
    expect(screen.getByTestId("add-action")).toBeInTheDocument()
  })

  it("abre Popover ao clicar slot trigger e mostra options", async () => {
    const user = userEvent.setup()
    renderBuilder()
    await user.click(screen.getByTestId("slot-trigger"))
    expect(await screen.findByText("chega na etapa")).toBeInTheDocument()
    expect(screen.getByText("completa WSI")).toBeInTheDocument()
  })

  it("selecionar trigger atualiza state e mostra label", async () => {
    const user = userEvent.setup()
    renderBuilder()
    await user.click(screen.getByTestId("slot-trigger"))
    await user.click(await screen.findByText("chega na etapa"))
    await waitFor(() => {
      expect(screen.getByTestId("slot-trigger")).toHaveTextContent("chega na etapa")
    })
  })

  it("adicionar condição abre linha com slots vazios", async () => {
    const user = userEvent.setup()
    renderBuilder()
    await user.click(screen.getByTestId("add-condition"))
    expect(screen.getByTestId("slot-condition-field-0")).toHaveTextContent("selecione um campo")
    expect(screen.getByTestId("slot-condition-operator-0")).toHaveTextContent("selecione o operador")
  })

  it("remover condição limpa state", async () => {
    const user = userEvent.setup()
    renderBuilder()
    await user.click(screen.getByTestId("add-condition"))
    expect(screen.getByTestId("slot-condition-field-0")).toBeInTheDocument()
    await user.click(screen.getByTestId("remove-condition-0"))
    expect(screen.queryByTestId("slot-condition-field-0")).not.toBeInTheDocument()
  })

  it("adicionar ação aparece com slot vazio", async () => {
    const user = userEvent.setup()
    renderBuilder()
    await user.click(screen.getByTestId("add-action"))
    expect(screen.getByTestId("slot-action-0")).toHaveTextContent("selecione uma ação")
    expect(screen.getByText("então")).toBeInTheDocument()
  })
})

// ── Validation ────────────────────────────────────────────────────────────

describe("SentenceBuilder — validation", () => {
  it("save disabled se trigger missing", () => {
    renderBuilder()
    expect(screen.getByTestId("save")).toBeDisabled()
  })

  it("save disabled se nenhuma action", async () => {
    const user = userEvent.setup()
    renderBuilder()
    await user.click(screen.getByTestId("slot-trigger"))
    await user.click(await screen.findByText("completa WSI"))
    expect(screen.getByTestId("save")).toBeDisabled()
  })

  it("save habilitado quando trigger + 1 action", async () => {
    const user = userEvent.setup()
    renderBuilder()
    await user.click(screen.getByTestId("slot-trigger"))
    await user.click(await screen.findByText("completa WSI"))
    await user.click(screen.getByTestId("add-action"))
    await user.click(screen.getByTestId("slot-action-0"))
    await user.click(await screen.findByText("mova para etapa"))
    await waitFor(() => {
      expect(screen.getByTestId("save")).not.toBeDisabled()
    })
  })
})

// ── Smart features ────────────────────────────────────────────────────────

describe("SentenceBuilder — smart canonical features", () => {
  it("auto-name suggestion aparece no placeholder", async () => {
    const user = userEvent.setup()
    renderBuilder()
    await user.click(screen.getByTestId("slot-trigger"))
    await user.click(await screen.findByText("completa WSI"))
    await user.click(screen.getByTestId("add-action"))
    await user.click(screen.getByTestId("slot-action-0"))
    await user.click(await screen.findByText("mova para etapa"))
    await waitFor(() => {
      const input = screen.getByTestId("automation-name") as HTMLInputElement
      expect(input.placeholder).toContain("Quando completa WSI → mova para etapa")
    })
  })

  it("LIA Cyan presence em slots ativos (canonical token)", async () => {
    const user = userEvent.setup()
    renderBuilder()
    const slot = screen.getByTestId("slot-trigger")
    expect(slot.getAttribute("data-active")).toBe("false")
    await user.click(slot)
    await user.click(await screen.findByText("chega na etapa"))
    await waitFor(() => {
      expect(screen.getByTestId("slot-trigger").getAttribute("data-active")).toBe("true")
      expect(screen.getByTestId("slot-trigger").className).toMatch(/lia-cyan/)
    })
  })
})

// ── Callbacks ─────────────────────────────────────────────────────────────

describe("SentenceBuilder — callbacks canonical", () => {
  it("cancela sem salvar", async () => {
    const user = userEvent.setup()
    const { onCancel, onSave } = renderBuilder()
    await user.click(screen.getByTestId("cancel"))
    expect(onCancel).toHaveBeenCalledTimes(1)
    expect(onSave).not.toHaveBeenCalled()
  })

  it("onSave recebe state canonical com name suggestion auto-aplicado", async () => {
    const user = userEvent.setup()
    const { onSave } = renderBuilder()
    await user.click(screen.getByTestId("slot-trigger"))
    await user.click(await screen.findByText("completa WSI"))
    await user.click(screen.getByTestId("add-action"))
    await user.click(screen.getByTestId("slot-action-0"))
    await user.click(await screen.findByText("mova para etapa"))
    await waitFor(() => {
      expect(screen.getByTestId("save")).not.toBeDisabled()
    })
    await user.click(screen.getByTestId("save"))
    await waitFor(() => {
      expect(onSave).toHaveBeenCalledTimes(1)
    })
    const payload = onSave.mock.calls[0][0] as SentenceBuilderState
    expect(payload.trigger?.type).toBe("wsi_completed")
    expect(payload.actions[0].type).toBe("move_stage")
    expect(payload.name).toBe("Quando completa WSI → mova para etapa")
  })
})

// ── Initial state ─────────────────────────────────────────────────────────

describe("SentenceBuilder — initial state hydration", () => {
  it("hidrata a partir de initial state (edit mode)", () => {
    const initial: SentenceBuilderState = {
      trigger: { type: "stage_changed", params: { stage: "interview" } },
      conditions: [{ field: "wsi_score", operator: "gt", value: 70 }],
      actions: [{ type: "send_whatsapp", params: { template: "convite" } }],
      name: "Minha automação",
    }
    renderBuilder({ initial })
    expect(screen.getByTestId("slot-trigger")).toHaveTextContent("chega na etapa")
    expect(screen.getByTestId("slot-condition-field-0")).toHaveTextContent("score WSI")
    expect(screen.getByTestId("slot-action-0")).toHaveTextContent("envie WhatsApp")
    expect((screen.getByTestId("automation-name") as HTMLInputElement).value).toBe(
      "Minha automação",
    )
    expect(screen.getByTestId("save")).not.toBeDisabled()
  })
})
