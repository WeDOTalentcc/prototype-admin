/**
 * Tests — useCandidateArrayUpdate replace-all hook.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { renderHook, act } from "@testing-library/react"
import { useCandidateArrayUpdate } from "../candidates/use-candidate-array-update"

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}))

vi.mock("swr", () => ({
  mutate: vi.fn().mockResolvedValue(undefined),
}))

vi.mock("@/hooks/company/use-current-company", () => ({
  useCurrentCompany: () => ({ companyId: "c-1", loading: false }),
}))

describe("useCandidateArrayUpdate", () => {
  let fetchMock: ReturnType<typeof vi.fn>
  beforeEach(() => {
    fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, updated_count: 1 }),
    })
    global.fetch = fetchMock as unknown as typeof fetch
  })
  afterEach(() => vi.restoreAllMocks())

  it("updateItem sends replaced array to canonical endpoint", async () => {
    const arr = [{ title: "A" }, { title: "B" }, { title: "C" }]
    const { result } = renderHook(() => useCandidateArrayUpdate("cand-1", "work_history", arr))
    await act(async () => {
      await result.current.updateItem(1, { title: "B-edit" })
    })
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/backend-proxy/chat/actions/candidate-field-update",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          candidate_id: "cand-1",
          fields: { work_history: [{ title: "A" }, { title: "B-edit" }, { title: "C" }] },
        }),
      })
    )
  })

  it("addItem appends to array", async () => {
    const arr = [{ title: "A" }]
    const { result } = renderHook(() => useCandidateArrayUpdate("c", "work_history", arr))
    await act(async () => {
      await result.current.addItem({ title: "B" })
    })
    const body = JSON.parse((fetchMock.mock.calls[0][1] as { body: string }).body)
    expect(body.fields.work_history).toEqual([{ title: "A" }, { title: "B" }])
  })

  it("removeItem deletes by index", async () => {
    const arr = [{ id: 1 }, { id: 2 }, { id: 3 }]
    const { result } = renderHook(() => useCandidateArrayUpdate("c", "work_history", arr))
    await act(async () => {
      await result.current.removeItem(1)
    })
    const body = JSON.parse((fetchMock.mock.calls[0][1] as { body: string }).body)
    expect(body.fields.work_history).toEqual([{ id: 1 }, { id: 3 }])
  })

  it("refuses LGPD-blocked field name", async () => {
    const { result } = renderHook(() => useCandidateArrayUpdate("c", "race", []))
    let res
    await act(async () => {
      res = await result.current.addItem({ x: 1 })
    })
    expect(res?.success).toBe(false)
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it("does NOT include company_id in body (JWT)", async () => {
    const { result } = renderHook(() => useCandidateArrayUpdate("c", "work_history", []))
    await act(async () => {
      await result.current.addItem({ title: "X" })
    })
    const body = JSON.parse((fetchMock.mock.calls[0][1] as { body: string }).body)
    expect(body).not.toHaveProperty("company_id")
  })

  it("returns success: false when candidateId is undefined", async () => {
    const { result } = renderHook(() => useCandidateArrayUpdate(undefined, "work_history", []))
    let res
    await act(async () => {
      res = await result.current.addItem({ x: 1 })
    })
    expect(res?.success).toBe(false)
    expect(fetchMock).not.toHaveBeenCalled()
  })
})
