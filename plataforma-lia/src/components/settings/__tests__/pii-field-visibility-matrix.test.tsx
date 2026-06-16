/**
 * A6-FE-2 — PiiFieldVisibilityMatrix canonical contract.
 *
 * Cases:
 *   T1. value={} -> field shows Herdado selected (aria-pressed=true)
 *   T2. Clicking Ver on cpf calls onChange with {cpf: true}
 *   T3. Clicking Ocultar on cpf (from {cpf:true}) calls onChange with {cpf: false}
 *   T4. Clicking Herdado on cpf (from {cpf:false}) calls onChange with {} (key deleted)
 *   T5. disabled -> controls are disabled
 *   T6. D-FE: vacancy group renders the vacancy_salary field label
 *   T7. D-FE: clicking Ver on vacancy_salary calls onChange with {vacancy_salary: true}
 */
import { describe, expect, it, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"
import { PiiFieldVisibilityMatrix } from "../PiiFieldVisibilityMatrix"
import ptBRMessages from "../../../../messages/pt-BR.json"
import type { PiiFieldVisibility } from "../user-management-types"

function renderMatrix(
  value: PiiFieldVisibility = {},
  onChange = vi.fn(),
  disabled = false,
) {
  return render(
    <NextIntlClientProvider locale="pt-BR" messages={ptBRMessages}>
      <PiiFieldVisibilityMatrix value={value} onChange={onChange} disabled={disabled} />
    </NextIntlClientProvider>,
  )
}

describe("PiiFieldVisibilityMatrix — A6-FE-2 canonical contract", () => {
  it("T1: value={} shows Herdado selected for a salary field (aria-pressed=true)", () => {
    renderMatrix({})
    // current_salary inherited button should be aria-pressed=true
    const btn = screen.getByTestId("pii-field-current_salary-inherited")
    expect(btn).toHaveAttribute("aria-pressed", "true")
    // show and hide should be aria-pressed=false
    expect(screen.getByTestId("pii-field-current_salary-show")).toHaveAttribute("aria-pressed", "false")
    expect(screen.getByTestId("pii-field-current_salary-hide")).toHaveAttribute("aria-pressed", "false")
  })

  it("T2: clicking Ver on cpf calls onChange with {cpf: true}", () => {
    const onChange = vi.fn()
    renderMatrix({}, onChange)
    const showBtn = screen.getByTestId("pii-field-cpf-show")
    fireEvent.click(showBtn)
    expect(onChange).toHaveBeenCalledTimes(1)
    expect(onChange).toHaveBeenCalledWith({ cpf: true })
  })

  it("T3: clicking Ocultar on cpf (from {cpf:true}) calls onChange with {cpf: false}", () => {
    const onChange = vi.fn()
    renderMatrix({ cpf: true }, onChange)
    const hideBtn = screen.getByTestId("pii-field-cpf-hide")
    fireEvent.click(hideBtn)
    expect(onChange).toHaveBeenCalledTimes(1)
    expect(onChange).toHaveBeenCalledWith({ cpf: false })
  })

  it("T4: clicking Herdado on cpf (from {cpf:false}) calls onChange with {} (key deleted)", () => {
    const onChange = vi.fn()
    renderMatrix({ cpf: false }, onChange)
    const inheritBtn = screen.getByTestId("pii-field-cpf-inherited")
    fireEvent.click(inheritBtn)
    expect(onChange).toHaveBeenCalledTimes(1)
    const result = onChange.mock.calls[0][0] as PiiFieldVisibility
    expect(result).not.toHaveProperty("cpf")
    expect(Object.keys(result)).toHaveLength(0)
  })

  it("T5: disabled -> all buttons are disabled", () => {
    renderMatrix({}, vi.fn(), true)
    const showBtn = screen.getByTestId("pii-field-cpf-show")
    expect(showBtn).toBeDisabled()
    const hideBtn = screen.getByTestId("pii-field-cpf-hide")
    expect(hideBtn).toBeDisabled()
    const inheritBtn = screen.getByTestId("pii-field-cpf-inherited")
    expect(inheritBtn).toBeDisabled()
  })

  it("T6: D-FE — vacancy group renders vacancy_salary label and Herdado is selected by default", () => {
    renderMatrix({})
    // The i18n label for vacancy_salary should be visible
    expect(screen.getByText("Salário da vaga")).toBeDefined()
    // Inherited button should be aria-pressed=true (no value set)
    const inheritedBtn = screen.getByTestId("pii-field-vacancy_salary-inherited")
    expect(inheritedBtn).toHaveAttribute("aria-pressed", "true")
    expect(screen.getByTestId("pii-field-vacancy_salary-show")).toHaveAttribute("aria-pressed", "false")
    expect(screen.getByTestId("pii-field-vacancy_salary-hide")).toHaveAttribute("aria-pressed", "false")
  })

  it("T7: D-FE — clicking Ver on vacancy_salary calls onChange with {vacancy_salary: true}", () => {
    const onChange = vi.fn()
    renderMatrix({}, onChange)
    const showBtn = screen.getByTestId("pii-field-vacancy_salary-show")
    fireEvent.click(showBtn)
    expect(onChange).toHaveBeenCalledTimes(1)
    expect(onChange).toHaveBeenCalledWith({ vacancy_salary: true })
  })
})
