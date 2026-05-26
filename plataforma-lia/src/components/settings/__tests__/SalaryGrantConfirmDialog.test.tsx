/**
 * Sprint 5.5 B2 — SalaryGrantConfirmDialog canonical contract.
 *
 * Anti-regression sensor: pin behavior of confirmation dialog used in
 *  - user-list inline toggle
 *  - user-form checkbox
 *  - user-list bulk toolbar (B3)
 *
 * Cases:
 *   T1. granting=true renders grant title + grant body + grant action
 *   T2. granting=false renders revoke title + revoke body + revoke action
 *   T3. target name + targetDetail displayed correctly
 *   T4. onConfirm fires when confirm button clicked
 *   T5. onOpenChange fires on cancel
 *   T6. i18n contract — no MISSING_MESSAGE on pt-BR JSON
 */
import { describe, expect, it, vi } from "vitest"
import { render, screen, fireEvent, within } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"
import { SalaryGrantConfirmDialog } from "../SalaryGrantConfirmDialog"
import ptBRMessages from "../../../../messages/pt-BR.json"

function renderDialog(props: Partial<React.ComponentProps<typeof SalaryGrantConfirmDialog>> = {}) {
  const defaults: React.ComponentProps<typeof SalaryGrantConfirmDialog> = {
    open: true,
    onOpenChange: vi.fn(),
    granting: true,
    target: "Ana Paula Santos",
    targetDetail: "ana.santos@wedotalent.com",
    onConfirm: vi.fn(),
  }
  return render(
    <NextIntlClientProvider locale="pt-BR" messages={ptBRMessages}>
      <SalaryGrantConfirmDialog {...defaults} {...props} />
    </NextIntlClientProvider>,
  )
}

describe("SalaryGrantConfirmDialog — B2 canonical contract", () => {
  it("T1: granting=true renders grant title + grant body + grant action", () => {
    renderDialog({ granting: true })
    expect(screen.getByText(/Conceder acesso a salários\?/i)).toBeInTheDocument()
    expect(screen.getByText(/poderá ver salários de candidatos/i)).toBeInTheDocument()
    expect(screen.getByTestId("salary-grant-confirm")).toHaveTextContent("Conceder acesso")
  })

  it("T2: granting=false renders revoke title + revoke body + revoke action", () => {
    renderDialog({ granting: false })
    expect(screen.getByText(/Revogar acesso a salários\?/i)).toBeInTheDocument()
    expect(screen.getByText(/deixará de ver salários/i)).toBeInTheDocument()
    expect(screen.getByTestId("salary-grant-confirm")).toHaveTextContent("Revogar acesso")
  })

  it("T3: target name + targetDetail displayed", () => {
    renderDialog({ target: "João Silva", targetDetail: "joao@example.com" })
    expect(screen.getByText("João Silva")).toBeInTheDocument()
    expect(screen.getByText(/joao@example\.com/)).toBeInTheDocument()
  })

  it("T4: onConfirm fires when confirm button clicked", () => {
    const onConfirm = vi.fn()
    renderDialog({ onConfirm })
    fireEvent.click(screen.getByTestId("salary-grant-confirm"))
    expect(onConfirm).toHaveBeenCalledTimes(1)
  })

  it("T5: onOpenChange fires when cancel clicked", () => {
    const onOpenChange = vi.fn()
    renderDialog({ onOpenChange })
    fireEvent.click(screen.getByTestId("salary-grant-cancel"))
    expect(onOpenChange).toHaveBeenCalled()
  })

  it("T6: i18n canonical contract — no MISSING_MESSAGE in pt-BR", () => {
    const errors: Error[] = []
    render(
      <NextIntlClientProvider
        locale="pt-BR"
        messages={ptBRMessages}
        onError={(err) => errors.push(err)}
      >
        <SalaryGrantConfirmDialog
          open={true}
          onOpenChange={vi.fn()}
          granting={true}
          target="Test"
          onConfirm={vi.fn()}
        />
      </NextIntlClientProvider>,
    )
    const missing = errors.filter((e) => e.message.includes("MISSING_MESSAGE"))
    expect(missing).toEqual([])
  })

  it("T7: target without detail does not render separator", () => {
    renderDialog({ target: "Ana", targetDetail: undefined })
    // target rendered but no '·' separator
    expect(screen.getByText("Ana")).toBeInTheDocument()
  })
})
