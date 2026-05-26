/**
 * Sprint 2.4 CR-3 sensor (2026-05-26) — notifyChatOfSettingsUpdate
 * deve debouncer events per (actionId+section+field) key pra evitar
 * dispatches prematuros durante typing/drag/slider input.
 *
 * Bug histórico (transcript Paulo 2026-05-26): user digitou "3" em campo
 * default_duration_minutes (numeric input min=15 max=240), onChange
 * disparou notify imediatamente com value=3, system note "[contexto]
 * = 3" apareceu no chat antes de qualquer save real. Schema Pydantic
 * backend Field(ge=15) rejeitaria persist, mas evento UI já vazara.
 *
 * Fix: debounce 1500ms per (actionId, section, field) — events sucessivos
 * com mesma key cancelam timer anterior, só último dispara.
 */
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest"
import { notifyChatOfSettingsUpdate } from "./settings-notify"

describe("settings-notify — Sprint 2.4 CR-3 debounce", () => {
  let dispatchSpy: ReturnType<typeof vi.fn>

  beforeEach(() => {
    vi.useFakeTimers()
    dispatchSpy = vi.fn()
    // Replace window.dispatchEvent
    if (typeof window === "undefined") {
      // @ts-expect-error — vitest env
      global.window = { dispatchEvent: dispatchSpy } as any
    } else {
      vi.spyOn(window, "dispatchEvent").mockImplementation(dispatchSpy)
    }
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it("does NOT dispatch immediately (debounced 1500ms)", () => {
    notifyChatOfSettingsUpdate({
      actionId: "configure_hiring_policy",
      section: "hiring_policies",
      field: "default_duration_minutes",
      value: 3,
    })
    expect(dispatchSpy).not.toHaveBeenCalled()
    vi.advanceTimersByTime(1499)
    expect(dispatchSpy).not.toHaveBeenCalled()
    vi.advanceTimersByTime(2)
    expect(dispatchSpy).toHaveBeenCalledTimes(1)
  })

  it("cancela call anterior com mesma key (debounce per-key)", () => {
    // Simula user typing "3" then "30" rapidly
    notifyChatOfSettingsUpdate({
      actionId: "configure_hiring_policy",
      section: "hiring_policies",
      field: "default_duration_minutes",
      value: 3,
    })
    vi.advanceTimersByTime(500)
    notifyChatOfSettingsUpdate({
      actionId: "configure_hiring_policy",
      section: "hiring_policies",
      field: "default_duration_minutes",
      value: 30,
    })
    vi.advanceTimersByTime(1499)
    expect(dispatchSpy).not.toHaveBeenCalled()
    vi.advanceTimersByTime(2)
    expect(dispatchSpy).toHaveBeenCalledTimes(1)
    // Last value (30) won
    const call = dispatchSpy.mock.calls[0][0] as CustomEvent
    expect((call.detail as { value: unknown }).value).toBe(30)
  })

  it("NÃO cancela calls com keys DIFERENTES (campos independentes)", () => {
    notifyChatOfSettingsUpdate({
      actionId: "configure_hiring_policy",
      section: "hiring_policies",
      field: "default_duration_minutes",
      value: 30,
    })
    notifyChatOfSettingsUpdate({
      actionId: "configure_benefits",
      section: "benefits",
      field: "vale_refeicao",
      value: 40,
    })
    vi.advanceTimersByTime(1501)
    expect(dispatchSpy).toHaveBeenCalledTimes(2)
  })

  it("preserva detail original + adds source/ts", () => {
    notifyChatOfSettingsUpdate({
      actionId: "configure_workforce",
      section: "workforce",
      field: "headcount",
      value: 42,
    })
    vi.advanceTimersByTime(1501)
    const call = dispatchSpy.mock.calls[0][0] as CustomEvent
    expect(call.type).toBe("lia:settings-updated")
    expect(call.detail).toMatchObject({
      actionId: "configure_workforce",
      section: "workforce",
      field: "headcount",
      value: 42,
      source: "ui",
    })
    expect((call.detail as { ts: number }).ts).toBeGreaterThan(0)
  })
})
