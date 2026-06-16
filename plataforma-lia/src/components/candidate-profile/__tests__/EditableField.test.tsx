/**
 * Tests — EditableField canonical inline-edit primitive.
 */
import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { EditableField } from "../EditableField"

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}))

describe("EditableField", () => {
  it("renders value as read-only with pencil hidden by default (until hover)", () => {
    render(<EditableField value="foo@bar.com" onSave={vi.fn().mockResolvedValue({ success: true })} label="email" />)
    expect(screen.getByText("foo@bar.com")).toBeInTheDocument()
    const pencilBtn = screen.getByRole("button", { name: /editar email/i })
    expect(pencilBtn).toBeInTheDocument()
  })

  it("does not render pencil when editable=false", () => {
    render(<EditableField value="x" onSave={vi.fn().mockResolvedValue({ success: true })} editable={false} label="x" />)
    expect(screen.queryByRole("button", { name: /editar/i })).toBeNull()
  })

  it("shows emptyDisplay when value is null", () => {
    render(<EditableField value={null} onSave={vi.fn().mockResolvedValue({ success: true })} label="x" emptyDisplay="—" />)
    expect(screen.getByText("—")).toBeInTheDocument()
  })

  it("enters edit mode when pencil clicked", () => {
    render(<EditableField value="foo" onSave={vi.fn().mockResolvedValue({ success: true })} label="campo" />)
    fireEvent.click(screen.getByRole("button", { name: /editar campo/i }))
    const input = screen.getByRole("textbox") as HTMLInputElement
    expect(input.value).toBe("foo")
  })

  it("saves on Enter and exits edit mode", async () => {
    const onSave = vi.fn().mockResolvedValue({ success: true })
    render(<EditableField value="foo" onSave={onSave} label="campo" />)
    fireEvent.click(screen.getByRole("button", { name: /editar campo/i }))
    const input = screen.getByRole("textbox")
    fireEvent.change(input, { target: { value: "bar" } })
    fireEvent.keyDown(input, { key: "Enter" })
    await waitFor(() => expect(onSave).toHaveBeenCalledWith("bar"))
  })

  it("cancels on Esc and reverts draft", () => {
    render(<EditableField value="foo" onSave={vi.fn()} label="campo" />)
    fireEvent.click(screen.getByRole("button", { name: /editar campo/i }))
    const input = screen.getByRole("textbox")
    fireEvent.change(input, { target: { value: "bar" } })
    fireEvent.keyDown(input, { key: "Escape" })
    expect(screen.getByText("foo")).toBeInTheDocument()
  })

  it("shows validation error inline when validate returns string", async () => {
    const validate = vi.fn((v: string) => (v.length < 3 ? "muito curto" : null))
    const onSave = vi.fn()
    render(<EditableField value="foo" onSave={onSave} validate={validate} label="campo" />)
    fireEvent.click(screen.getByRole("button", { name: /editar campo/i }))
    const input = screen.getByRole("textbox")
    fireEvent.change(input, { target: { value: "ab" } })
    fireEvent.click(screen.getByRole("button", { name: /salvar campo/i }))
    await waitFor(() => expect(screen.getByText("muito curto")).toBeInTheDocument())
    expect(onSave).not.toHaveBeenCalled()
  })

  it("shows onSave error inline when result.success=false", async () => {
    const onSave = vi.fn().mockResolvedValue({ success: false, error: "Backend rejeitou" })
    render(<EditableField value="foo" onSave={onSave} label="campo" />)
    fireEvent.click(screen.getByRole("button", { name: /editar campo/i }))
    fireEvent.click(screen.getByRole("button", { name: /salvar campo/i }))
    await waitFor(() => expect(screen.getByText("Backend rejeitou")).toBeInTheDocument())
  })

  it("renders textarea when type=textarea", () => {
    render(<EditableField value="foo" onSave={vi.fn()} label="x" type="textarea" />)
    fireEvent.click(screen.getByRole("button", { name: /editar/i }))
    const ta = screen.getByRole("textbox")
    expect(ta.tagName.toLowerCase()).toBe("textarea")
  })

  it("disables buttons during saving prop=true", () => {
    render(<EditableField value="foo" onSave={vi.fn()} label="x" saving={true} />)
    fireEvent.click(screen.getByRole("button", { name: /editar/i }))
    const saveBtn = screen.getByRole("button", { name: /salvar/i })
    expect(saveBtn).toBeDisabled()
  })
})
