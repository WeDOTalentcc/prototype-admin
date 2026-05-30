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
    // F1: only email provided -> only email button visible (phone hidden)
    renderWithProvider(<CandidateContactActions email="foo@bar.com" />)
    const buttons = screen.getAllByRole("button")
    expect(buttons.length).toBe(1)
    expect(buttons[0]).not.toBeDisabled()
  })

  it("hides email button when no email and no callback (F1: no placeholder)", () => {
    // F1: absent field -> button hidden, not disabled
    const { container } = renderWithProvider(<CandidateContactActions />)
    const buttons = container.querySelectorAll("button")
    expect(buttons.length).toBe(0)
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
    // email present, no linkedin -> only 1 button (email)
    renderWithProvider(<CandidateContactActions email="x@y.com" />)
    const buttons = screen.getAllByRole("button")
    expect(buttons.length).toBe(1)
  })

  it("renders LinkedIn button when linkedinUrl provided", () => {
    const onOpenLinkedIn = vi.fn()
    // linkedinUrl only (no email, no phone) -> 1 button
    renderWithProvider(<CandidateContactActions linkedinUrl="https://linkedin.com/in/x" onOpenLinkedIn={onOpenLinkedIn} />)
    const buttons = screen.getAllByRole("button")
    expect(buttons.length).toBe(1)
    fireEvent.click(buttons[0])
    expect(onOpenLinkedIn).toHaveBeenCalled()
  })

  it("calls onSendWhatsApp callback when provided", () => {
    const onSendWhatsApp = vi.fn()
    // phone only -> 1 button at index 0
    renderWithProvider(<CandidateContactActions phone="+55 11 99999-9999" onSendWhatsApp={onSendWhatsApp} />)
    const buttons = screen.getAllByRole("button")
    expect(buttons.length).toBe(1)
    fireEvent.click(buttons[0])
    expect(onSendWhatsApp).toHaveBeenCalled()
  })
})

describe("CandidateContactActions -- F1 mandatory: absent fields hidden (no placeholder)", () => {
  it("no email and no callback → email button NOT rendered", () => {
    renderWithProvider(<CandidateContactActions phone="+55 11 99999-9999" />)
    // only phone button should be present; email button hidden when absent
    const buttons = screen.getAllByRole("button")
    expect(buttons.length).toBe(1)
  })

  it("no phone and no callback → phone button NOT rendered", () => {
    renderWithProvider(<CandidateContactActions email="x@y.com" />)
    const buttons = screen.getAllByRole("button")
    expect(buttons.length).toBe(1)
  })

  it("all absent → no buttons rendered", () => {
    const { container } = renderWithProvider(<CandidateContactActions />)
    const buttons = container.querySelectorAll("button")
    expect(buttons.length).toBe(0)
  })

  it("email only → exactly 1 button", () => {
    renderWithProvider(<CandidateContactActions email="foo@bar.com" />)
    expect(screen.getAllByRole("button").length).toBe(1)
  })
})
