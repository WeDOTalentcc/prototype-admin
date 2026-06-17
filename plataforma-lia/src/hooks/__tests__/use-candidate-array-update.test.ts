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

  it("updateItem sends replaced array to canonical endpoint (fallback field)", async () => {
    const arr = [{ title: "A" }, { title: "B" }, { title: "C" }]
    const { result } = renderHook(() => useCandidateArrayUpdate("cand-1", "tags", arr))
    await act(async () => {
      await result.current.updateItem(1, { title: "B-edit" })
    })
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/backend-proxy/chat/actions/candidate-field-update",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          candidate_id: "cand-1",
          fields: { tags: [{ title: "A" }, { title: "B-edit" }, { title: "C" }] },
        }),
      })
    )
  })

  it("addItem appends to array (fallback field)", async () => {
    const arr = [{ title: "A" }]
    const { result } = renderHook(() => useCandidateArrayUpdate("c", "tags", arr))
    await act(async () => {
      await result.current.addItem({ title: "B" })
    })
    const body = JSON.parse((fetchMock.mock.calls[0][1] as { body: string }).body)
    expect(body.fields.tags).toEqual([{ title: "A" }, { title: "B" }])
  })

  it("removeItem deletes by index (fallback field)", async () => {
    const arr = [{ id: 1 }, { id: 2 }, { id: 3 }]
    const { result } = renderHook(() => useCandidateArrayUpdate("c", "tags", arr))
    await act(async () => {
      await result.current.removeItem(1)
    })
    const body = JSON.parse((fetchMock.mock.calls[0][1] as { body: string }).body)
    expect(body.fields.tags).toEqual([{ id: 1 }, { id: 3 }])
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

  it("routes work_history to dedicated PUT /experiences endpoint (F6 Item 3)", async () => {
    const arr = [{ title: "A" }]
    const { result } = renderHook(() => useCandidateArrayUpdate("cand-99", "work_history", arr))
    await act(async () => {
      await result.current.addItem({ title: "B" })
    })
    const [url, opts] = fetchMock.mock.calls[0]
    expect(url).toBe("/api/backend-proxy/candidates/cand-99/experiences")
    expect((opts as { method: string }).method).toBe("PUT")
    // Body is the raw array (not wrapped in fields object)
    const body = JSON.parse((opts as { body: string }).body)
    expect(Array.isArray(body)).toBe(true)
    expect(body).toEqual([{ title: "A" }, { title: "B" }])
  })

  it("routes education to dedicated PUT /education endpoint (F6 Item 3)", async () => {
    const { result } = renderHook(() => useCandidateArrayUpdate("cand-99", "education", []))
    await act(async () => {
      await result.current.addItem({ degree: "MBA" })
    })
    const [url, opts] = fetchMock.mock.calls[0]
    expect(url).toBe("/api/backend-proxy/candidates/cand-99/education")
    expect((opts as { method: string }).method).toBe("PUT")
  })

  it("falls back to candidate-field-update for non-canonical array fields", async () => {
    const { result } = renderHook(() => useCandidateArrayUpdate("cand-99", "tags", []))
    await act(async () => {
      await result.current.addItem("new-tag")
    })
    const [url] = fetchMock.mock.calls[0]
    expect(url).toBe("/api/backend-proxy/chat/actions/candidate-field-update")
  })
})
