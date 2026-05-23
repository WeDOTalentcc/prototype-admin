/**
 * Tests — useCandidateFieldUpdate canonical edit hook.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { renderHook, act } from "@testing-library/react"
import { useCandidateFieldUpdate, LGPD_BLOCKED_FIELDS } from "../candidates/use-candidate-field-update"

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}))

vi.mock("swr", () => ({
  mutate: vi.fn().mockResolvedValue(undefined),
}))

vi.mock("@/hooks/company/use-current-company", () => ({
  useCurrentCompany: () => ({ companyId: "company-test-123", loading: false }),
}))

describe("useCandidateFieldUpdate", () => {
  let fetchMock: ReturnType<typeof vi.fn>
  beforeEach(() => {
    fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, updated_count: 1, total: 1 }),
    })
    global.fetch = fetchMock as unknown as typeof fetch
  })
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("LGPD_BLOCKED_FIELDS contains the canonical 14+ sensitive fields", () => {
    expect(LGPD_BLOCKED_FIELDS.has("race")).toBe(true)
    expect(LGPD_BLOCKED_FIELDS.has("gender")).toBe(true)
    expect(LGPD_BLOCKED_FIELDS.has("marital_status")).toBe(true)
    expect(LGPD_BLOCKED_FIELDS.has("religion")).toBe(true)
    expect(LGPD_BLOCKED_FIELDS.has("date_of_birth")).toBe(true)
    expect(LGPD_BLOCKED_FIELDS.has("cpf")).toBe(true)
    expect(LGPD_BLOCKED_FIELDS.has("company_id")).toBe(true)
  })

  it("refuses LGPD-blocked field updates without calling fetch", async () => {
    const { result } = renderHook(() => useCandidateFieldUpdate("cand-1"))
    let res: { success: boolean; error?: string } = { success: true }
    await act(async () => {
      res = await result.current.updateField("race", "any-value")
    })
    expect(res.success).toBe(false)
    expect(res.error).toMatch(/LGPD/)
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it("sends POST to canonical endpoint with correct body", async () => {
    const { result } = renderHook(() => useCandidateFieldUpdate("cand-1"))
    await act(async () => {
      await result.current.updateField("email", "new@test.com")
    })
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/backend-proxy/chat/actions/candidate-field-update",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_id: "cand-1",
          fields: { email: "new@test.com" },
        }),
      })
    )
  })

  it("does NOT include company_id in body (flows via JWT)", async () => {
    const { result } = renderHook(() => useCandidateFieldUpdate("cand-1"))
    await act(async () => {
      await result.current.updateField("phone", "+55 11 99999")
    })
    const body = JSON.parse((fetchMock.mock.calls[0][1] as { body: string }).body)
    expect(body).not.toHaveProperty("company_id")
  })

  it("returns success: false on HTTP error", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 403,
      json: async () => ({ detail: "Forbidden" }),
    })
    const { result } = renderHook(() => useCandidateFieldUpdate("cand-1"))
    let res: { success: boolean; error?: string } = { success: true }
    await act(async () => {
      res = await result.current.updateField("email", "x@y.com")
    })
    expect(res.success).toBe(false)
    expect(res.error).toBe("Forbidden")
  })

  it("returns success: false when no candidateId", async () => {
    const { result } = renderHook(() => useCandidateFieldUpdate(undefined))
    let res: { success: boolean; error?: string } = { success: true }
    await act(async () => {
      res = await result.current.updateField("email", "x@y.com")
    })
    expect(res.success).toBe(false)
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it("isSaving toggles during fetch lifecycle", async () => {
    let resolveFetch: (v: unknown) => void = () => {}
    fetchMock.mockReturnValue(
      new Promise((resolve) => {
        resolveFetch = resolve
      })
    )
    const { result } = renderHook(() => useCandidateFieldUpdate("cand-1"))
    expect(result.current.isSaving("email")).toBe(false)
    let updatePromise: Promise<unknown>
    await act(async () => {
      updatePromise = result.current.updateField("email", "x@y.com")
    })
    expect(result.current.isSaving("email")).toBe(true)
    await act(async () => {
      resolveFetch({ ok: true, json: async () => ({ success: true }) })
      await updatePromise!
    })
    expect(result.current.isSaving("email")).toBe(false)
  })
})
