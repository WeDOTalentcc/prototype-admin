/**
 * Q4.3 Studio internal tour — StudioTour contract tests.
 *
 * Garante (AUDIT 7 gap C1):
 *  - dispara na PRIMEIRA visita (sem flag studio_tour_seen no localStorage)
 *  - NÃO dispara em visitas subsequentes (flag presente)
 *  - dismissível: "Pular tour" grava a flag e fecha o tour
 *  - reusa TourSpotlight canonical (mockado)
 */
import { describe, expect, it, vi, beforeEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"

vi.mock("next-intl", () => ({
  useTranslations: () => {
    const t = (key: string) => key
    t.has = () => true
    return t
  },
}))

// Mock canonical TourSpotlight — apenas expõe selector + botão de avançar.
vi.mock("@/components/onboarding/tour/TourSpotlight", () => ({
  TourSpotlight: ({ selector, onDismiss }: { selector: string; onDismiss?: () => void }) => (
    <div data-testid="mock-spotlight" data-selector={selector}>
      <button data-testid="spotlight-advance" onClick={() => onDismiss?.()}>
        advance
      </button>
    </div>
  ),
}))

import { StudioTour } from "../StudioTour"

function mockStorage(initial: Record<string, string> = {}) {
  const store: Record<string, string> = { ...initial }
  Object.defineProperty(window, "localStorage", {
    value: {
      getItem: (k: string) => store[k] ?? null,
      setItem: (k: string, v: string) => {
        store[k] = v
      },
      removeItem: (k: string) => {
        delete store[k]
      },
    },
    writable: true,
  })
  return store
}

beforeEach(() => {
  vi.restoreAllMocks()
})

describe("StudioTour", () => {
  it("starts on first visit (no studio_tour_seen flag)", () => {
    mockStorage()
    render(<StudioTour />)
    expect(screen.getByTestId("studio-tour")).toBeTruthy()
    // First step anchors the create-agent CTA.
    expect(screen.getByTestId("mock-spotlight").getAttribute("data-selector")).toContain(
      "studio-create-agent",
    )
  })

  it("does NOT start when studio_tour_seen is already set", () => {
    mockStorage({ studio_tour_seen: "2026-05-29T00:00:00Z" })
    render(<StudioTour />)
    expect(screen.queryByTestId("studio-tour")).toBeNull()
  })

  it("marks seen and closes when 'Pular tour' is clicked", () => {
    const store = mockStorage()
    render(<StudioTour />)
    expect(screen.getByTestId("studio-tour")).toBeTruthy()

    fireEvent.click(screen.getByTestId("studio-tour-skip"))
    expect(screen.queryByTestId("studio-tour")).toBeNull()
    expect(store.studio_tour_seen).toBeTruthy()
  })

  it("advances through steps and finishes (marks seen) on last advance", () => {
    const store = mockStorage()
    render(<StudioTour />)
    // 5 steps — advance 5x to finish.
    for (let i = 0; i < 5; i++) {
      const adv = screen.queryByTestId("spotlight-advance")
      if (adv) fireEvent.click(adv)
    }
    expect(screen.queryByTestId("studio-tour")).toBeNull()
    expect(store.studio_tour_seen).toBeTruthy()
  })

  it("forceStart starts even when flag is set", () => {
    mockStorage({ studio_tour_seen: "x" })
    render(<StudioTour forceStart />)
    expect(screen.getByTestId("studio-tour")).toBeTruthy()
  })
})
