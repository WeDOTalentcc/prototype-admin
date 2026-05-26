/**
 * Sprint 7C Part 3 — EventTriggerPicker tests
 */
import { describe, expect, it, vi } from "vitest"
import { fireEvent, render, screen } from "@testing-library/react"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

import { EventTriggerPicker, CANONICAL_EVENT_TYPES } from "../EventTriggerPicker"

describe("EventTriggerPicker — Sprint 7C Part 3", () => {
  it("renderiza 4 checkboxes canonical", () => {
    render(<EventTriggerPicker value={[]} onChange={() => {}} />)
    for (const evt of CANONICAL_EVENT_TYPES) {
      expect(screen.getByTestId(`event-checkbox-${evt}`)).toBeInTheDocument()
    }
  })

  it("multi-select adiciona evento ao array", () => {
    const onChange = vi.fn()
    render(<EventTriggerPicker value={[]} onChange={onChange} />)
    fireEvent.click(screen.getByTestId("event-checkbox-candidate_added_to_pool"))
    expect(onChange).toHaveBeenCalledWith(["candidate_added_to_pool"])
  })

  it("clicar em evento ja-selecionado remove do array", () => {
    const onChange = vi.fn()
    render(
      <EventTriggerPicker
        value={["candidate_added_to_pool", "weekly_summary"]}
        onChange={onChange}
      />,
    )
    fireEvent.click(screen.getByTestId("event-checkbox-candidate_added_to_pool"))
    expect(onChange).toHaveBeenCalledWith(["weekly_summary"])
  })
})
