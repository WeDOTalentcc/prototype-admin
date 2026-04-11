/**
 * P1-E — Testes unitários: useSearchAutocomplete
 *
 * Camada 2 — Unitária (jsdom)
 * Cobre:
 * 1. Estado inicial correto
 * 2. fetchAutocomplete: query curta → limpa sugestões
 * 3. fetchAutocomplete: resultado da API → seta sugestões
 * 4. fetchAutocomplete: cache em memória (segunda chamada não re-fetcha)
 * 5. fetchAutocomplete: resposta vazia → showAutocomplete=false
 * 6. handleAutocompleteKeyDown: ArrowDown incrementa índice
 * 7. handleAutocompleteKeyDown: ArrowUp decrementa / wraps
 * 8. handleAutocompleteKeyDown: Enter chama onSelect e fecha
 * 9. handleAutocompleteKeyDown: Tab chama onSelect e fecha
 * 10. handleAutocompleteKeyDown: Escape fecha sem chamar onSelect
 * 11. autocompleteEnabled toggle
 */

import { renderHook, act } from "@testing-library/react"
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest"
import { useSearchAutocomplete } from "../search/use-search-autocomplete"

const mockSuggestions = [
  { text: "React Developer", category: "job_title", insert_text: "React Developer" },
  { text: "Node.js", category: "skills", insert_text: "Node.js" },
  { text: "São Paulo", category: "location", insert_text: "São Paulo" },
]

const mockFetch = vi.fn()

beforeEach(() => {
  global.fetch = mockFetch
  mockFetch.mockReset()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe("P1-E — useSearchAutocomplete", () => {
  it("1. estado inicial correto", () => {
    const { result } = renderHook(() => useSearchAutocomplete())
    expect(result.current.autocompleteSuggestions).toEqual([])
    expect(result.current.showAutocomplete).toBe(false)
    expect(result.current.selectedAutocompleteIndex).toBe(0)
    expect(result.current.autocompleteEnabled).toBe(true)
  })

  it("2. fetchAutocomplete: query curta limpa sugestões", async () => {
    const { result } = renderHook(() => useSearchAutocomplete())
    await act(async () => {
      await result.current.fetchAutocomplete("a")
    })
    expect(result.current.autocompleteSuggestions).toEqual([])
    expect(result.current.showAutocomplete).toBe(false)
    expect(mockFetch).not.toHaveBeenCalled()
  })

  it("3. fetchAutocomplete: resultado da API seta sugestões", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ items: mockSuggestions }),
    })
    const { result } = renderHook(() => useSearchAutocomplete())
    await act(async () => {
      await result.current.fetchAutocomplete("React")
    })
    expect(result.current.autocompleteSuggestions).toHaveLength(3)
    expect(result.current.showAutocomplete).toBe(true)
  })

  it("4. fetchAutocomplete: cache em memória — segunda chamada idêntica não re-fetcha", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ items: mockSuggestions }),
    })
    const { result } = renderHook(() => useSearchAutocomplete())
    await act(async () => { await result.current.fetchAutocomplete("React") })
    await act(async () => { await result.current.fetchAutocomplete("React") })
    expect(mockFetch).toHaveBeenCalledTimes(1)
  })

  it("5. fetchAutocomplete: resposta vazia → showAutocomplete=false", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ items: [] }),
    })
    const { result } = renderHook(() => useSearchAutocomplete())
    await act(async () => {
      await result.current.fetchAutocomplete("xyzzy")
    })
    expect(result.current.showAutocomplete).toBe(false)
  })

  it("6. handleAutocompleteKeyDown: ArrowDown incrementa índice", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ items: mockSuggestions }),
    })
    const { result } = renderHook(() => useSearchAutocomplete())
    await act(async () => { await result.current.fetchAutocomplete("React") })

    const onSelect = vi.fn()
    act(() => {
      result.current.handleAutocompleteKeyDown({ key: "ArrowDown", preventDefault: vi.fn() } as unknown as React.KeyboardEvent, onSelect)
    })
    expect(result.current.selectedAutocompleteIndex).toBe(1)
  })

  it("7. handleAutocompleteKeyDown: ArrowUp no índice 0 wraps para último", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ items: mockSuggestions }),
    })
    const { result } = renderHook(() => useSearchAutocomplete())
    await act(async () => { await result.current.fetchAutocomplete("React") })

    const onSelect = vi.fn()
    act(() => {
      result.current.handleAutocompleteKeyDown({ key: "ArrowUp", preventDefault: vi.fn() } as unknown as React.KeyboardEvent, onSelect)
    })
    expect(result.current.selectedAutocompleteIndex).toBe(2)
  })

  it("8. handleAutocompleteKeyDown: Enter chama onSelect com insert_text e fecha autocomplete", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ items: mockSuggestions }),
    })
    const { result } = renderHook(() => useSearchAutocomplete())
    await act(async () => { await result.current.fetchAutocomplete("React") })

    const onSelect = vi.fn()
    act(() => {
      result.current.handleAutocompleteKeyDown({ key: "Enter", preventDefault: vi.fn() } as unknown as React.KeyboardEvent, onSelect)
    })
    expect(onSelect).toHaveBeenCalledWith("React Developer")
    expect(result.current.showAutocomplete).toBe(false)
  })

  it("9. handleAutocompleteKeyDown: Tab também chama onSelect", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ items: mockSuggestions }),
    })
    const { result } = renderHook(() => useSearchAutocomplete())
    await act(async () => { await result.current.fetchAutocomplete("React") })

    const onSelect = vi.fn()
    act(() => {
      result.current.handleAutocompleteKeyDown({ key: "Tab", preventDefault: vi.fn() } as unknown as React.KeyboardEvent, onSelect)
    })
    expect(onSelect).toHaveBeenCalledTimes(1)
  })

  it("10. handleAutocompleteKeyDown: Escape fecha sem chamar onSelect", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ items: mockSuggestions }),
    })
    const { result } = renderHook(() => useSearchAutocomplete())
    await act(async () => { await result.current.fetchAutocomplete("React") })

    const onSelect = vi.fn()
    act(() => {
      result.current.handleAutocompleteKeyDown({ key: "Escape", preventDefault: vi.fn() } as unknown as React.KeyboardEvent, onSelect)
    })
    expect(onSelect).not.toHaveBeenCalled()
    expect(result.current.showAutocomplete).toBe(false)
  })

  it("11. autocompleteEnabled toggle", () => {
    const { result } = renderHook(() => useSearchAutocomplete())
    act(() => { result.current.setAutocompleteEnabled(false) })
    expect(result.current.autocompleteEnabled).toBe(false)
    act(() => { result.current.setAutocompleteEnabled(true) })
    expect(result.current.autocompleteEnabled).toBe(true)
  })
})
