/**
 * Task #839 — slot-availability logic for the Scheduling stage panel.
 *
 * The audit `audit-criacao-vaga-2026-04-26.md` (finding L-04) noted that
 * the Scheduling stage has zero coverage across every layer of the test
 * pyramid. This file pins the only piece of recruiter-facing logic that
 * lives inside `SchedulingPanel` itself: which slots are clickable, when
 * the "Confirmar" CTA is enabled, and what happens when the recruiter
 * confirms a window.
 *
 * Multi-interview pagination is also covered because that is the only
 * place where the panel makes a non-trivial state decision (advance vs
 * dispatch the `lia:scheduling-confirmed` event).
 */
import React from "react"
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest"
import { render, screen, cleanup, fireEvent } from "@testing-library/react"

import { SchedulingPanel } from "../SchedulingPanel"

const slotsTwoDays = [
  { date: "2026-05-04", day_label: "Seg 4", time: "09:00", available: true },
  { date: "2026-05-04", day_label: "Seg 4", time: "10:00", available: false },
  { date: "2026-05-05", day_label: "Ter 5", time: "09:00", available: true },
  { date: "2026-05-05", day_label: "Ter 5", time: "10:00", available: true },
]

afterEach(() => {
  cleanup()
})

describe("SchedulingPanel — slot availability logic (Task #839)", () => {
  it("renders one button per available slot and a non-interactive placeholder per unavailable slot", () => {
    render(<SchedulingPanel data={{ available_slots: slotsTwoDays }} />)

    // 3 available slots → 3 buttons with the time/day aria-label.
    expect(screen.getByRole("button", { name: "09:00 em Seg 4" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "09:00 em Ter 5" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "10:00 em Ter 5" })).toBeInTheDocument()

    // The 10:00 cell on Seg 4 is unavailable, so it must NOT be a button.
    expect(screen.queryByRole("button", { name: "10:00 em Seg 4" })).toBeNull()
  })

  it("keeps the confirm CTA disabled until the recruiter selects an available slot, then enables it", () => {
    render(<SchedulingPanel data={{ available_slots: slotsTwoDays }} />)

    const confirm = screen.getByRole("button", { name: /Confirmar agendamento/i })
    expect(confirm).toBeDisabled()
    expect(screen.getByText(/Selecione um horário para continuar/i)).toBeInTheDocument()

    fireEvent.click(screen.getByRole("button", { name: "09:00 em Seg 4" }))
    expect(confirm).toBeEnabled()
    // Helper hint disappears once a slot is chosen.
    expect(screen.queryByText(/Selecione um horário para continuar/i)).toBeNull()
  })

  it("toggles the same slot off when clicked twice (re-disabling confirm)", () => {
    render(<SchedulingPanel data={{ available_slots: slotsTwoDays }} />)

    const slot = screen.getByRole("button", { name: "09:00 em Seg 4" })
    const confirm = screen.getByRole("button", { name: /Confirmar agendamento/i })

    fireEvent.click(slot)
    expect(slot).toHaveAttribute("aria-pressed", "true")
    expect(confirm).toBeEnabled()

    fireEvent.click(slot)
    expect(slot).toHaveAttribute("aria-pressed", "false")
    expect(confirm).toBeDisabled()
  })

  it("dispatches `lia:scheduling-confirmed` and calls onApprove when a single-interview flow is confirmed", () => {
    const onApprove = vi.fn()
    const handler = vi.fn()
    window.addEventListener("lia:scheduling-confirmed", handler as EventListener)

    render(
      <SchedulingPanel
        data={{ available_slots: slotsTwoDays, vacancy_id: "vac-42" }}
        onApprove={onApprove}
      />,
    )

    fireEvent.click(screen.getByRole("button", { name: "09:00 em Ter 5" }))
    fireEvent.click(screen.getByRole("button", { name: /Confirmar agendamento/i }))

    expect(onApprove).toHaveBeenCalledTimes(1)
    expect(handler).toHaveBeenCalledTimes(1)
    const evt = handler.mock.calls[0][0] as CustomEvent
    expect(evt.detail.vacancyId).toBe("vac-42")
    expect(evt.detail.slots).toEqual({ 0: "2026-05-05|09:00" })

    // After the only interview is confirmed the panel flips to the
    // success state ("Entrevista agendada!") instead of the grid.
    expect(screen.getByText(/Entrevista agendada/i)).toBeInTheDocument()

    window.removeEventListener("lia:scheduling-confirmed", handler as EventListener)
  })

  it("multi-interview flow advances to the next interview without dispatching the event yet", () => {
    const handler = vi.fn()
    window.addEventListener("lia:scheduling-confirmed", handler as EventListener)

    render(
      <SchedulingPanel
        data={{
          available_slots: slotsTwoDays,
          interviews: [
            { id: "1", title: "Triagem", candidate_name: "Ana" },
            { id: "2", title: "Painel técnico", candidate_name: "Ana" },
          ],
        }}
      />,
    )

    expect(screen.getByText("Triagem")).toBeInTheDocument()
    expect(screen.queryByText("Painel técnico")).toBeNull()

    fireEvent.click(screen.getByRole("button", { name: "09:00 em Seg 4" }))
    // First interview → CTA reads "Confirmar e avançar", not the final label.
    fireEvent.click(screen.getByRole("button", { name: /Confirmar e avançar/i }))

    // No event yet — only fires on the LAST interview.
    expect(handler).not.toHaveBeenCalled()

    // Second interview is now the active one.
    expect(screen.getByText("Painel técnico")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /Confirmar agendamento/i })).toBeInTheDocument()

    window.removeEventListener("lia:scheduling-confirmed", handler as EventListener)
  })
})
