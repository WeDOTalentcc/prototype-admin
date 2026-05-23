/**
 * Tests — CandidateContactActions canonical building block.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { TooltipProvider } from "@/components/ui/tooltip"
import { CandidateContactActions } from "../CandidateContactActions"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

function renderWithProvider(ui: React.ReactElement) {
  return render(<TooltipProvider>{ui}</TooltipProvider>)
}

describe("CandidateContactActions", () => {
  let originalOpen: typeof window.open
  beforeEach(() => {
    originalOpen = window.open
    window.open = vi.fn() as unknown as typeof window.open
  })
  afterEach(() => {
    window.open = originalOpen
  })

  it("renders email button enabled when email exists", () => {
    renderWithProvider(<CandidateContactActions email="foo@bar.com" />)
    const buttons = screen.getAllByRole("button")
    expect(buttons.length).toBeGreaterThanOrEqual(2)
    expect(buttons[0]).not.toBeDisabled()
  })

  it("disables email button when no email and no callback", () => {
    renderWithProvider(<CandidateContactActions />)
    const buttons = screen.getAllByRole("button")
    expect(buttons[0]).toBeDisabled()
  })

  it("calls onSendEmail callback when provided", () => {
    const onSendEmail = vi.fn()
    renderWithProvider(<CandidateContactActions email="foo@bar.com" onSendEmail={onSendEmail} />)
    const buttons = screen.getAllByRole("button")
    fireEvent.click(buttons[0])
    expect(onSendEmail).toHaveBeenCalled()
  })

  it("falls back to mailto when no callback", () => {
    renderWithProvider(<CandidateContactActions email="foo@bar.com" />)
    const buttons = screen.getAllByRole("button")
    fireEvent.click(buttons[0])
    expect(window.open).toHaveBeenCalledWith("mailto:foo@bar.com", "_self")
  })

  it("hides LinkedIn button when no linkedinUrl and no callback", () => {
    renderWithProvider(<CandidateContactActions email="x@y.com" />)
    const buttons = screen.getAllByRole("button")
    expect(buttons.length).toBe(2)
  })

  it("renders LinkedIn button when linkedinUrl provided", () => {
    const onOpenLinkedIn = vi.fn()
    renderWithProvider(<CandidateContactActions linkedinUrl="https://linkedin.com/in/x" onOpenLinkedIn={onOpenLinkedIn} />)
    const buttons = screen.getAllByRole("button")
    expect(buttons.length).toBe(3)
    fireEvent.click(buttons[2])
    expect(onOpenLinkedIn).toHaveBeenCalled()
  })

  it("calls onSendWhatsApp callback when provided", () => {
    const onSendWhatsApp = vi.fn()
    renderWithProvider(<CandidateContactActions phone="+55 11 99999-9999" onSendWhatsApp={onSendWhatsApp} />)
    const buttons = screen.getAllByRole("button")
    fireEvent.click(buttons[1])
    expect(onSendWhatsApp).toHaveBeenCalled()
  })
})
