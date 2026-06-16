/**
 * Sprint 7C Part 3 — CronScheduleBuilder tests
 */
import { describe, expect, it, vi } from "vitest"
import { fireEvent, render, screen } from "@testing-library/react"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

import { CronScheduleBuilder } from "../CronScheduleBuilder"

describe("CronScheduleBuilder — Sprint 7C Part 3", () => {
  it("preset daily emite cron canonical '<m> <h> * * *'", () => {
    const onChange = vi.fn()
    render(<CronScheduleBuilder value="0 9 * * *" onChange={onChange} />)
    // Initial detect -> daily; emits on mount via effect
    expect(onChange).toHaveBeenCalled()
    const lastCall = onChange.mock.calls[onChange.mock.calls.length - 1]
    expect(lastCall[0]).toMatch(/^\d+ \d+ \* \* \*$/)
  })

  it("preset weekly emite cron com dia-da-semana", () => {
    const onChange = vi.fn()
    render(<CronScheduleBuilder value="0 9 * * 1" onChange={onChange} />)
    const lastCall = onChange.mock.calls[onChange.mock.calls.length - 1]
    expect(lastCall[0]).toMatch(/^\d+ \d+ \* \* \d$/)
  })

  it("preset monthly emite cron com dia-do-mes", () => {
    const onChange = vi.fn()
    render(<CronScheduleBuilder value="0 9 1 * *" onChange={onChange} />)
    const lastCall = onChange.mock.calls[onChange.mock.calls.length - 1]
    expect(lastCall[0]).toMatch(/^\d+ \d+ \d+ \* \*$/)
  })

  it("preset custom permite expression livre quando valida", () => {
    const onChange = vi.fn()
    render(<CronScheduleBuilder value="*/15 * * * *" onChange={onChange} />)
    // Detected as custom; valid expression emitted
    expect(screen.queryByTestId("cron-custom-input")).toBeInTheDocument()
    const lastCall = onChange.mock.calls[onChange.mock.calls.length - 1]
    expect(lastCall[0]).toBe("*/15 * * * *")
  })

  it("custom expression invalida mostra mensagem de erro e nao emite onChange", () => {
    const onChange = vi.fn()
    render(<CronScheduleBuilder value="*/15 * * * *" onChange={onChange} />)
    onChange.mockClear()
    const input = screen.getByTestId("cron-custom-input") as HTMLInputElement
    fireEvent.change(input, { target: { value: "not a cron" } })
    expect(screen.getByTestId("cron-custom-invalid")).toBeInTheDocument()
    // Should not emit canonical onChange while invalid
    expect(onChange).not.toHaveBeenCalled()
  })
})
