/**
 * AutomationFromChatBridge tests — Sprint D.3 canonical
 *
 * Verifica que o bridge:
 *  1. Renderiza null (headless)
 *  2. Escuta CustomEvent `lia:create-automation`
 *  3. Persiste detail em sessionStorage com key canonical
 *  4. Navega para path canonical do builder
 *  5. Cleanup listener no unmount
 *  6. Gracefully handles sessionStorage indisponível
 *  7. Handles detail vazio (CustomEvent sem detail)
 */

import { render } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

const mockPush = vi.fn()
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: vi.fn(), prefetch: vi.fn() }),
}))

import {
  AutomationFromChatBridge,
  LIA_CREATE_AUTOMATION_EVENT,
  LIA_PENDING_AUTOMATION_STORAGE_KEY,
  AUTOMATION_BUILDER_PATH,
  type CreateAutomationDetail,
} from "../AutomationFromChatBridge"

describe("AutomationFromChatBridge", () => {
  beforeEach(() => {
    mockPush.mockClear()
    window.sessionStorage.clear()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("renderiza null (componente headless)", () => {
    const { container } = render(<AutomationFromChatBridge />)
    expect(container.firstChild).toBeNull()
  })

  it("escuta CustomEvent lia:create-automation e persiste detail em sessionStorage", () => {
    render(<AutomationFromChatBridge />)

    const detail: CreateAutomationDetail = {
      trigger: { type: "candidate_applied", params: {} },
      conditions: [{ field: "candidate.wsi_score", operator: "gt", value: 70 }],
      actions: [{ type: "send_whatsapp", params: { template_id: "interview_invite" } }],
      name: "WSI alto → convite",
      source: "chat",
    }

    window.dispatchEvent(
      new CustomEvent(LIA_CREATE_AUTOMATION_EVENT, { detail }),
    )

    const stored = window.sessionStorage.getItem(LIA_PENDING_AUTOMATION_STORAGE_KEY)
    expect(stored).not.toBeNull()
    expect(JSON.parse(stored!)).toEqual(detail)
  })

  it("navega para path canonical do builder após receber evento", () => {
    render(<AutomationFromChatBridge />)

    window.dispatchEvent(
      new CustomEvent(LIA_CREATE_AUTOMATION_EVENT, { detail: {} }),
    )

    expect(mockPush).toHaveBeenCalledTimes(1)
    expect(mockPush).toHaveBeenCalledWith(AUTOMATION_BUILDER_PATH)
  })

  it("handles CustomEvent sem detail (fallback para {})", () => {
    render(<AutomationFromChatBridge />)

    window.dispatchEvent(new Event(LIA_CREATE_AUTOMATION_EVENT))

    const stored = window.sessionStorage.getItem(LIA_PENDING_AUTOMATION_STORAGE_KEY)
    expect(stored).toBe("{}")
    expect(mockPush).toHaveBeenCalledWith(AUTOMATION_BUILDER_PATH)
  })

  it("remove listener no unmount (não responde após cleanup)", () => {
    const { unmount } = render(<AutomationFromChatBridge />)
    unmount()

    window.dispatchEvent(
      new CustomEvent(LIA_CREATE_AUTOMATION_EVENT, {
        detail: { name: "post-unmount" },
      }),
    )

    expect(mockPush).not.toHaveBeenCalled()
    expect(
      window.sessionStorage.getItem(LIA_PENDING_AUTOMATION_STORAGE_KEY),
    ).toBeNull()
  })

  it("navega mesmo se sessionStorage indisponível (REGRA 4 anti-silent)", () => {
    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {})
    const setItemSpy = vi
      .spyOn(Storage.prototype, "setItem")
      .mockImplementation(() => {
        throw new Error("QuotaExceeded")
      })

    render(<AutomationFromChatBridge />)

    window.dispatchEvent(
      new CustomEvent(LIA_CREATE_AUTOMATION_EVENT, {
        detail: { name: "test" },
      }),
    )

    expect(warnSpy).toHaveBeenCalledWith(
      expect.stringContaining("[AutomationFromChatBridge]"),
    )
    // Navegação ainda acontece — UX degraded mas não broken
    expect(mockPush).toHaveBeenCalledWith(AUTOMATION_BUILDER_PATH)

    setItemSpy.mockRestore()
    warnSpy.mockRestore()
  })

  it("aceita múltiplos eventos consecutivos (idempotente)", () => {
    render(<AutomationFromChatBridge />)

    window.dispatchEvent(
      new CustomEvent(LIA_CREATE_AUTOMATION_EVENT, {
        detail: { name: "first" },
      }),
    )
    window.dispatchEvent(
      new CustomEvent(LIA_CREATE_AUTOMATION_EVENT, {
        detail: { name: "second" },
      }),
    )

    expect(mockPush).toHaveBeenCalledTimes(2)
    const stored = window.sessionStorage.getItem(LIA_PENDING_AUTOMATION_STORAGE_KEY)
    expect(JSON.parse(stored!)).toEqual({ name: "second" })
  })
})
