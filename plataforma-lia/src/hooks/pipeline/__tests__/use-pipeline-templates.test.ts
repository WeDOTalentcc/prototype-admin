/**
 * use-pipeline-templates.test.ts — Fase 4.2 (Sprint Pipeline Templates).
 *
 * Cobre:
 *  - fetches list via SWR (mocked).
 *  - createTemplate POST com body correto + mutate.
 *  - archiveTemplate POST /{id}/archive.
 *  - cloneTemplate POST /{id}/clone.
 */
import { describe, test, expect, vi, beforeEach, afterEach } from "vitest"
import { renderHook, act, waitFor } from "@testing-library/react"

// Mock SWR antes do import do hook.
const mutateSpy = vi.fn()
const swrState: { data: unknown; error: unknown; isLoading: boolean } = {
  data: undefined,
  error: undefined,
  isLoading: false,
}
vi.mock("swr", () => ({
  default: () => ({
    data: swrState.data,
    error: swrState.error,
    isLoading: swrState.isLoading,
    mutate: mutateSpy,
  }),
}))

import { usePipelineTemplates } from "../use-pipeline-templates"

const SAMPLE = {
  id: "tpl-1",
  company_id: "co-1",
  name: "Pipeline Demo",
  description: null,
  stages: [{ name: "Triagem", order: 1, type: "manual", sla_days: 2 }],
  is_default: false,
  is_active: true,
  usage_count: 0,
}

function setSwrData(data: unknown) {
  swrState.data = data
  swrState.error = undefined
  swrState.isLoading = false
}

describe("usePipelineTemplates — fetches list", () => {
  beforeEach(() => {
    mutateSpy.mockReset()
  })

  test("exposes templates + total + isLoading", () => {
    setSwrData({ templates: [SAMPLE], total: 1 })
    const { result } = renderHook(() => usePipelineTemplates())
    expect(result.current.templates).toEqual([SAMPLE])
    expect(result.current.total).toBe(1)
    expect(result.current.isLoading).toBe(false)
  })

  test("handles array shape (no envelope)", () => {
    setSwrData([SAMPLE])
    const { result } = renderHook(() => usePipelineTemplates())
    expect(result.current.templates).toEqual([SAMPLE])
    expect(result.current.total).toBe(1)
  })
})

describe("usePipelineTemplates — mutations", () => {
  let fetchMock: ReturnType<typeof vi.fn>
  beforeEach(() => {
    setSwrData({ templates: [], total: 0 })
    mutateSpy.mockReset()
    fetchMock = vi.fn()
    // @ts-expect-error global override
    global.fetch = fetchMock
  })
  afterEach(() => {
    // @ts-expect-error
    delete global.fetch
  })

  test("createTemplate POSTs payload + calls mutate", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => SAMPLE,
      text: async () => "",
    })
    const { result } = renderHook(() => usePipelineTemplates())

    await act(async () => {
      const created = await result.current.createTemplate({
        name: "Pipeline Demo",
        stages: [{ name: "Triagem", order: 1, type: "manual", sla_days: 2 }],
      })
      expect(created).toEqual(SAMPLE)
    })

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe("/api/backend-proxy/company/pipeline-templates/")
    expect(init?.method).toBe("POST")
    const body = JSON.parse(init?.body as string)
    expect(body.name).toBe("Pipeline Demo")
    expect(body.stages).toHaveLength(1)
    await waitFor(() => expect(mutateSpy).toHaveBeenCalled())
  })

  test("archiveTemplate POSTs /{id}/archive", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      status: 204,
      json: async () => ({}),
      text: async () => "",
    })
    const { result } = renderHook(() => usePipelineTemplates())

    await act(async () => {
      const ok = await result.current.archiveTemplate("tpl-1")
      expect(ok).toBe(true)
    })

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe("/api/backend-proxy/company/pipeline-templates/tpl-1/archive")
    expect(init?.method).toBe("POST")
    await waitFor(() => expect(mutateSpy).toHaveBeenCalled())
  })

  test("cloneTemplate POSTs /{id}/clone", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => ({ ...SAMPLE, id: "tpl-clone" }),
      text: async () => "",
    })
    const { result } = renderHook(() => usePipelineTemplates())

    await act(async () => {
      const cloned = await result.current.cloneTemplate("tpl-1")
      expect(cloned?.id).toBe("tpl-clone")
    })

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe("/api/backend-proxy/company/pipeline-templates/tpl-1/clone")
    expect(init?.method).toBe("POST")
    await waitFor(() => expect(mutateSpy).toHaveBeenCalled())
  })
})
