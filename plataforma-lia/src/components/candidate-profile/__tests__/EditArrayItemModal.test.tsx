/**
 * Tests — EditArrayItemModal generic modal.
 */
import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { EditArrayItemModal, type FieldDef } from "../EditArrayItemModal"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

const FIELDS: FieldDef[] = [
  { name: "title", label: "Título", required: true },
  { name: "description", label: "Descrição", type: "textarea" },
]

describe("EditArrayItemModal", () => {
  it("renders fields with initial values when editing", () => {
    render(
      <EditArrayItemModal
        open={true}
        onClose={vi.fn()}
        initialItem={{ title: "Tech Lead", description: "Lidera time" }}
        fields={FIELDS}
        title="Editar"
        onSave={vi.fn().mockResolvedValue({ success: true })}
      />
    )
    expect(screen.getByDisplayValue("Tech Lead")).toBeInTheDocument()
    expect(screen.getByDisplayValue("Lidera time")).toBeInTheDocument()
  })

  it("renders empty fields when adding new item (initialItem=null)", () => {
    render(
      <EditArrayItemModal
        open={true}
        onClose={vi.fn()}
        initialItem={null}
        fields={FIELDS}
        title="Adicionar"
        onSave={vi.fn().mockResolvedValue({ success: true })}
      />
    )
    const titleInput = screen.getByLabelText(/Título/) as HTMLInputElement
    expect(titleInput.value).toBe("")
  })

  it("blocks save when required field is empty", async () => {
    const onSave = vi.fn()
    render(
      <EditArrayItemModal
        open={true}
        onClose={vi.fn()}
        initialItem={null}
        fields={FIELDS}
        title="X"
        onSave={onSave}
      />
    )
    fireEvent.click(screen.getByText("Salvar"))
    await waitFor(() => expect(screen.getByRole("alert").textContent).toMatch(/obrigatório/i))
    expect(onSave).not.toHaveBeenCalled()
  })

  it("calls onSave with current values when valid", async () => {
    const onSave = vi.fn().mockResolvedValue({ success: true })
    const onClose = vi.fn()
    render(
      <EditArrayItemModal
        open={true}
        onClose={onClose}
        initialItem={null}
        fields={FIELDS}
        title="X"
        onSave={onSave}
      />
    )
    const titleInput = screen.getByLabelText(/Título/)
    fireEvent.change(titleInput, { target: { value: "Novo Cargo" } })
    fireEvent.click(screen.getByText("Salvar"))
    await waitFor(() => expect(onSave).toHaveBeenCalledWith({ title: "Novo Cargo", description: "" }))
    await waitFor(() => expect(onClose).toHaveBeenCalled())
  })

  it("shows onSave error and does NOT close", async () => {
    const onSave = vi.fn().mockResolvedValue({ success: false, error: "Backend disse não" })
    const onClose = vi.fn()
    render(
      <EditArrayItemModal
        open={true}
        onClose={onClose}
        initialItem={null}
        fields={FIELDS}
        title="X"
        onSave={onSave}
      />
    )
    fireEvent.change(screen.getByLabelText(/Título/), { target: { value: "X" } })
    fireEvent.click(screen.getByText("Salvar"))
    await waitFor(() => expect(screen.getByRole("alert").textContent).toBe("Backend disse não"))
    expect(onClose).not.toHaveBeenCalled()
  })

  it("cancel button calls onClose", () => {
    const onClose = vi.fn()
    render(
      <EditArrayItemModal
        open={true}
        onClose={onClose}
        initialItem={null}
        fields={FIELDS}
        title="X"
        onSave={vi.fn()}
      />
    )
    fireEvent.click(screen.getByText("Cancelar"))
    expect(onClose).toHaveBeenCalled()
  })

  it("renders textarea for type=textarea field", () => {
    render(
      <EditArrayItemModal
        open={true}
        onClose={vi.fn()}
        initialItem={null}
        fields={FIELDS}
        title="X"
        onSave={vi.fn()}
      />
    )
    const desc = screen.getByLabelText(/Descrição/)
    expect(desc.tagName.toLowerCase()).toBe("textarea")
  })
})
