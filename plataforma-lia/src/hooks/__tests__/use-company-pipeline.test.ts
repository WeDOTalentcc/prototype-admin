/**
 * Testes — useCompanyPipeline (Ciclo H post-audit)
 *
 * Camada 2 (Unitário FE — Vitest + @testing-library/react)
 *
 * Cobre:
 * - Estado inicial: loading=true, pipeline=null
 * - Fetch bem-sucedido: pipeline populado, loading=false
 * - Mapeamento correto de campos do backend para o formato interno
 * - Fallback silencioso quando backend falha: loading=false, pipeline=null
 * - Filtro de etapas inativas (is_active=false)
 * - LIA assisted marcado para etapas conhecidas
 */
import { renderHook, waitFor } from "@testing-library/react"
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest"
import { useCompanyPipeline } from "../company/use-company-pipeline"

// Mock dos módulos de constantes
vi.mock("@/lib/recruitment-stages", () => ({
  LIA_ASSISTED_STAGES: ["screening", "technical_interview"],
  LIA_ASSISTED_STAGE_NAMES: ["Triagem", "Entrevista Técnica"],
}))

const MOCK_PIPELINE_RESPONSE = {
  pipeline: [
    {
      name: "screening",
      display_name: "Triagem",
      stage_category: "system",
      is_active: true,
      sla_hours: 48,
    },
    {
      name: "technical_interview",
      display_name: "Entrevista Técnica",
      stage_category: "catalog",
      is_active: true,
      sla_hours: 72,
    },
    {
      name: "custom_etapa",
      display_name: "Etapa Customizada",
      stage_category: "custom",
      is_active: true,
      sla_hours: null,
    },
    {
      name: "desativada",
      display_name: "Etapa Desativada",
      stage_category: "custom",
      is_active: false,
      sla_hours: 24,
    },
  ],
}

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn())
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.clearAllMocks()
})

describe("useCompanyPipeline", () => {
  it("inicia com loading=true e pipeline=null", () => {
    ;(vi.mocked(fetch)).mockReturnValueOnce(new Promise(() => {})) // nunca resolve

    const { result } = renderHook(() => useCompanyPipeline())

    expect(result.current.loading).toBe(true)
    expect(result.current.pipeline).toBeNull()
  })

  it("popula pipeline e define loading=false após fetch bem-sucedido", async () => {
    ;(vi.mocked(fetch)).mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_PIPELINE_RESPONSE,
    })

    const { result } = renderHook(() => useCompanyPipeline())

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.pipeline).not.toBeNull()
    expect(result.current.pipeline).toHaveLength(3) // 4 - 1 inativa
  })

  it("filtra etapas com is_active=false", async () => {
    ;(vi.mocked(fetch)).mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_PIPELINE_RESPONSE,
    })

    const { result } = renderHook(() => useCompanyPipeline())

    await waitFor(() => expect(result.current.loading).toBe(false))

    const names = result.current.pipeline!.map((s) => s.name)
    expect(names).not.toContain("desativada")
    expect(names).toContain("screening")
  })

  it("mapeia corretamente: stageName, order, type, slaDays", async () => {
    ;(vi.mocked(fetch)).mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_PIPELINE_RESPONSE,
    })

    const { result } = renderHook(() => useCompanyPipeline())

    await waitFor(() => expect(result.current.loading).toBe(false))

    const first = result.current.pipeline![0]
    expect(first.stageName).toBe("Triagem")
    expect(first.order).toBe(1)
    expect(first.type).toBe("interview")
    expect(first.slaDays).toBe(2) // 48h / 24
    expect(first.defaultSlaDays).toBe(2)
  })

  it("mapeia stage_category 'catalog' como 'default'", async () => {
    ;(vi.mocked(fetch)).mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_PIPELINE_RESPONSE,
    })

    const { result } = renderHook(() => useCompanyPipeline())

    await waitFor(() => expect(result.current.loading).toBe(false))

    const catalogStage = result.current.pipeline!.find((s) => s.name === "technical_interview")
    expect(catalogStage?.stageCategory).toBe("default")
  })

  it("marca liaAssisted=true para etapas conhecidas", async () => {
    ;(vi.mocked(fetch)).mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_PIPELINE_RESPONSE,
    })

    const { result } = renderHook(() => useCompanyPipeline())

    await waitFor(() => expect(result.current.loading).toBe(false))

    const screeningStage = result.current.pipeline!.find((s) => s.name === "screening")
    expect(screeningStage?.liaAssisted).toBe(true)

    const customStage = result.current.pipeline!.find((s) => s.name === "custom_etapa")
    expect(customStage?.liaAssisted).toBe(false)
  })

  it("define slaDays=3 (padrão) quando sla_hours é null", async () => {
    ;(vi.mocked(fetch)).mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_PIPELINE_RESPONSE,
    })

    const { result } = renderHook(() => useCompanyPipeline())

    await waitFor(() => expect(result.current.loading).toBe(false))

    const customStage = result.current.pipeline!.find((s) => s.name === "custom_etapa")
    expect(customStage?.slaDays).toBe(3)
  })

  it("fallback silencioso: pipeline=null, loading=false quando backend falha (500)", async () => {
    ;(vi.mocked(fetch)).mockResolvedValueOnce({
      ok: false,
      status: 500,
    })

    const { result } = renderHook(() => useCompanyPipeline())

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.pipeline).toBeNull()
  })

  it("fallback silencioso: pipeline=null, loading=false quando fetch lança exceção", async () => {
    ;(vi.mocked(fetch)).mockRejectedValueOnce(new Error("Network error"))

    const { result } = renderHook(() => useCompanyPipeline())

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.pipeline).toBeNull()
  })

  it("propriedades de edição: system=não removível, custom=removível", async () => {
    ;(vi.mocked(fetch)).mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_PIPELINE_RESPONSE,
    })

    const { result } = renderHook(() => useCompanyPipeline())

    await waitFor(() => expect(result.current.loading).toBe(false))

    const systemStage = result.current.pipeline!.find((s) => s.name === "screening")
    expect(systemStage?.isEditable).toBe(false)
    expect(systemStage?.isRemovable).toBe(false)
    expect(systemStage?.isReorderable).toBe(false)

    const customStage = result.current.pipeline!.find((s) => s.name === "custom_etapa")
    expect(customStage?.isEditable).toBe(true)
    expect(customStage?.isRemovable).toBe(true)
    expect(customStage?.isReorderable).toBe(true)
  })
})
