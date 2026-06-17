import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { QuickReplies } from "@/components/onboarding/QuickReplies"

describe("QuickReplies — P2-2 B.2", () => {
  it("renderiza preset boolean com 2 botões", () => {
    render(<QuickReplies preset="boolean" onSelect={() => {}} />)
    expect(screen.getByTestId("quick-reply-sim")).toBeInTheDocument()
    expect(screen.getByTestId("quick-reply-não")).toBeInTheDocument()
  })

  it("renderiza preset work_model com 3 botões", () => {
    render(<QuickReplies preset="work_model" onSelect={() => {}} />)
    expect(screen.getByTestId("quick-reply-presencial")).toBeInTheDocument()
    expect(screen.getByTestId("quick-reply-hibrido")).toBeInTheDocument()
    expect(screen.getByTestId("quick-reply-remoto")).toBeInTheDocument()
  })

  it("renderiza preset autonomy com 3 botões + labels descritivas", () => {
    render(<QuickReplies preset="autonomy" onSelect={() => {}} />)
    expect(screen.getByText(/Low — sempre pede/)).toBeInTheDocument()
    expect(screen.getByText(/Medium — age em decisões/)).toBeInTheDocument()
    expect(screen.getByText(/High — age na maioria/)).toBeInTheDocument()
  })

  it("renderiza preset channel com 3 opções", () => {
    render(<QuickReplies preset="channel" onSelect={() => {}} />)
    expect(screen.getByTestId("quick-reply-whatsapp")).toBeInTheDocument()
    expect(screen.getByTestId("quick-reply-email")).toBeInTheDocument()
    expect(screen.getByTestId("quick-reply-sms")).toBeInTheDocument()
  })

  it("renderiza preset ai_tone com 6 opções", () => {
    render(<QuickReplies preset="ai_tone" onSelect={() => {}} />)
    expect(screen.getByTestId("quick-reply-formal")).toBeInTheDocument()
    expect(screen.getByTestId("quick-reply-direto")).toBeInTheDocument()
  })

  it("renderiza preset experience_policy com 2 opções", () => {
    render(<QuickReplies preset="experience_policy" onSelect={() => {}} />)
    expect(screen.getByTestId("quick-reply-per_job")).toBeInTheDocument()
    expect(screen.getByTestId("quick-reply-company_wide")).toBeInTheDocument()
  })

  it("custom options funcionam (override preset)", () => {
    const custom = [
      { label: "X", value: "x" },
      { label: "Y", value: "y" },
    ]
    render(<QuickReplies options={custom} onSelect={() => {}} />)
    expect(screen.getByTestId("quick-reply-x")).toBeInTheDocument()
    expect(screen.getByTestId("quick-reply-y")).toBeInTheDocument()
  })

  it("não renderiza nada se sem preset E sem options", () => {
    const { container } = render(<QuickReplies onSelect={() => {}} />)
    expect(container.firstChild).toBeNull()
  })

  it("onSelect callback recebe value + label", () => {
    const onSelect = vi.fn()
    render(<QuickReplies preset="boolean" onSelect={onSelect} />)
    fireEvent.click(screen.getByTestId("quick-reply-sim"))
    expect(onSelect).toHaveBeenCalledWith("sim", "Sim")
  })

  it("após click, todos os botões ficam disabled (single-select)", () => {
    render(<QuickReplies preset="boolean" onSelect={() => {}} />)
    const simBtn = screen.getByTestId("quick-reply-sim")
    const naoBtn = screen.getByTestId("quick-reply-não")
    fireEvent.click(simBtn)
    expect(naoBtn).toBeDisabled()
  })

  it("disabled prop bloqueia todos os botões", () => {
    render(<QuickReplies preset="boolean" onSelect={() => {}} disabled />)
    const simBtn = screen.getByTestId("quick-reply-sim")
    expect(simBtn).toBeDisabled()
  })

  it("a11y: role=group + aria-label", () => {
    render(<QuickReplies preset="boolean" onSelect={() => {}} />)
    const group = screen.getByRole("group", { name: /respostas rápidas/i })
    expect(group).toBeInTheDocument()
  })

  it("a11y: aria-pressed reflete selecionado", () => {
    render(<QuickReplies preset="boolean" onSelect={() => {}} />)
    const simBtn = screen.getByTestId("quick-reply-sim")
    expect(simBtn).toHaveAttribute("aria-pressed", "false")
    fireEvent.click(simBtn)
    expect(simBtn).toHaveAttribute("aria-pressed", "true")
  })
})
