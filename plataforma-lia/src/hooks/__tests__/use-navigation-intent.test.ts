/**
 * Testes unitários — useNavigationIntent (Phase 4b)
 *
 * Camada 2 — Unitária (jsdom)
 * Cobre: detect(), threshold 0.65, clear(), isDetecting state, erros de rede.
 */

import { renderHook, act, waitFor } from "@testing-library/react"
import { useNavigationIntent, resolveNavigationIntentMode } from "../shared/use-navigation-intent"

// ─── Helpers ──────────────────────────────────────────────────────────────────

function mockFetch(response: object, ok = true, status = 200) {
  global.fetch = vi.fn().mockResolvedValueOnce({
    ok,
    status,
    json: () => Promise.resolve(response),
  } as unknown as Response)
}

function mockFetchError() {
  global.fetch = vi.fn().mockRejectedValueOnce(new Error("Network error"))
}

// ─── Testes ──────────────────────────────────────────────────────────────────

describe("useNavigationIntent", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("estado inicial é null", () => {
    const { result } = renderHook(() => useNavigationIntent())
    expect(result.current.result).toBeNull()
    expect(result.current.isDetecting).toBe(false)
  })

  it("detect() retorna null para mensagem vazia sem chamar fetch", async () => {
    const spy = vi.fn()
    global.fetch = spy
    const { result } = renderHook(() => useNavigationIntent())
    let ret: unknown
    await act(async () => {
      ret = await result.current.detect("")
    })
    expect(ret).toBeNull()
    expect(spy).not.toBeCalled()
  })

  it("detect() retorna null para mensagem só de espaços", async () => {
    const spy = vi.fn()
    global.fetch = spy
    const { result } = renderHook(() => useNavigationIntent())
    let ret: unknown
    await act(async () => {
      ret = await result.current.detect("   ")
    })
    expect(ret).toBeNull()
    expect(spy).not.toBeCalled()
  })

  it("detect() chama POST /api/backend-proxy/navigation-intent", async () => {
    mockFetch({ page: "Vagas", confidence: 0.85, hint: "Ver vagas abertas", matched_pattern: "vagas" })
    const { result } = renderHook(() => useNavigationIntent())
    await act(async () => {
      await result.current.detect("quero ver as vagas abertas")
    })
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/backend-proxy/navigation-intent",
      expect.objectContaining({ method: "POST" })
    )
  })

  it("detect() retorna resultado quando confidence >= 0.65", async () => {
    mockFetch({ page: "Vagas", confidence: 0.85, hint: "Ver vagas abertas", matched_pattern: "vagas" })
    const { result } = renderHook(() => useNavigationIntent())
    let ret: unknown
    await act(async () => {
      ret = await result.current.detect("ver vagas")
    })
    expect((ret as { page: string }).page).toBe("Vagas")
    expect(result.current.result?.page).toBe("Vagas")
  })

  it("detect() zera page/hint quando confidence < 0.65", async () => {
    mockFetch({ page: "Vagas", confidence: 0.5, hint: "Ver vagas", matched_pattern: "vagas" })
    const { result } = renderHook(() => useNavigationIntent())
    let ret: unknown
    await act(async () => {
      ret = await result.current.detect("algo genérico")
    })
    expect((ret as { page: null }).page).toBeNull()
    expect(result.current.result?.page).toBeNull()
    expect(result.current.result?.hint).toBeNull()
  })

  it("detect() retorna null quando backend retorna erro HTTP", async () => {
    mockFetch({}, false, 500)
    const { result } = renderHook(() => useNavigationIntent())
    let ret: unknown
    await act(async () => {
      ret = await result.current.detect("ver candidatos")
    })
    expect(ret).toBeNull()
  })

  it("detect() retorna null em erro de rede (sem lançar)", async () => {
    mockFetchError()
    const { result } = renderHook(() => useNavigationIntent())
    let ret: unknown
    await act(async () => {
      ret = await result.current.detect("ver candidatos")
    })
    expect(ret).toBeNull()
    expect(result.current.isDetecting).toBe(false)
  })

  it("isDetecting é true durante a requisição", async () => {
    let resolveJson!: (v: object) => void
    const jsonPromise = new Promise<object>(r => { resolveJson = r })
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: () => jsonPromise,
    } as unknown as Response)

    const { result } = renderHook(() => useNavigationIntent())
    act(() => { result.current.detect("vagas abertas") })

    await waitFor(() => expect(result.current.isDetecting).toBe(true))

    resolveJson({ page: "Vagas", confidence: 0.9, hint: null, matched_pattern: "vagas" })
    await waitFor(() => expect(result.current.isDetecting).toBe(false))
  })

  it("clear() limpa o resultado", async () => {
    mockFetch({ page: "Vagas", confidence: 0.9, hint: "Ver vagas", matched_pattern: "vagas" })
    const { result } = renderHook(() => useNavigationIntent())
    await act(async () => {
      await result.current.detect("ver vagas")
    })
    expect(result.current.result?.page).toBe("Vagas")

    act(() => { result.current.clear() })
    expect(result.current.result).toBeNull()
  })

  it("detect() envia mensagem no body JSON", async () => {
    mockFetch({ page: "Funil de Talentos", confidence: 0.8, hint: null, matched_pattern: "candidatos" })
    const { result } = renderHook(() => useNavigationIntent())
    await act(async () => {
      await result.current.detect("listar candidatos")
    })
    const callArgs = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0]
    const body = JSON.parse(callArgs[1].body)
    expect(body.message).toBe("listar candidatos")
  })

  it("confidence exatamente 0.65 deve retornar resultado (boundary)", async () => {
    mockFetch({ page: "Tarefas", confidence: 0.65, hint: "Ver tarefas", matched_pattern: "tarefas" })
    const { result } = renderHook(() => useNavigationIntent())
    let ret: unknown
    await act(async () => {
      ret = await result.current.detect("abrir tarefas")
    })
    expect((ret as { page: string }).page).toBe("Tarefas")
  })
})

describe("resolveNavigationIntentMode - imperativo vs interrogativo", () => {
  const BASE = {
    page: "Vagas",
    confidence: 0.8,
    hint: "Ver vagas",
  }

  it("me leve para vagas - navigate", () => {
    const result = resolveNavigationIntentMode(BASE, "/pt/dashboard", "me leve para vagas")
    expect(result.mode).toBe("navigate")
    expect(result.page).toBe("Vagas")
  })

  it("me leva pro pipeline - navigate", () => {
    const result = resolveNavigationIntentMode(BASE, "/pt/dashboard", "me leva pro pipeline")
    expect(result.mode).toBe("navigate")
  })

  it("vai para vagas - navigate", () => {
    const result = resolveNavigationIntentMode(BASE, "/pt/dashboard", "vai para vagas")
    expect(result.mode).toBe("navigate")
  })

  it("abre o kanban - navigate", () => {
    const result = resolveNavigationIntentMode(BASE, "/pt/dashboard", "abre o kanban")
    expect(result.mode).toBe("navigate")
  })

  it("quais vagas estao ativas - ask", () => {
    const result = resolveNavigationIntentMode(BASE, "/pt/dashboard", "quais vagas estao ativas?")
    expect(result.mode).toBe("ask")
  })

  it("ver candidatos - ask", () => {
    const result = resolveNavigationIntentMode(BASE, "/pt/dashboard", "ver candidatos")
    expect(result.mode).toBe("ask")
  })

  it("sem originalMessage - ask", () => {
    const result = resolveNavigationIntentMode(BASE, "/pt/dashboard")
    expect(result.mode).toBe("ask")
  })

  it("imperativo com confidence baixa - page null (threshold vence)", () => {
    const lowConf = { ...BASE, confidence: 0.5 }
    const result = resolveNavigationIntentMode(lowConf, "/pt/dashboard", "me leve para vagas")
    expect(result.page).toBeNull()
  })
})
