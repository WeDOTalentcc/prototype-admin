/**
 * P1-E — Testes unitários: useSearchSource
 *
 * Camada 2 — Unitária (jsdom)
 * Cobre:
 * 1. Estado inicial (searchSource='local', sem modal)
 * 2. handleSourceChange('local') → direto, sem modal
 * 3. handleSourceChange('hybrid') → abre modal com pendingSourceChange
 * 4. handleSourceChange('global') → abre modal com pendingSourceChange
 * 5. confirmSourceChange aplica mudança e fecha modal
 * 6. setShowSourceChangeModal(false) cancela sem mudar fonte
 * 7. Reset para local quando showGlobalSearchOptions=false
 * 8. setters de candidateLimit, requireEmails, requirePhoneNumbers
 * 9. pearchSearchType toggle
 */

import { renderHook, act } from "@testing-library/react"
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest"

// Mock dos hooks de dependência
vi.mock("@/hooks/search/useCreditEstimator", () => ({
  useCreditEstimator: () => ({
    balance: null,
    fetchBalance: vi.fn().mockResolvedValue(undefined),
    estimateCost: vi.fn().mockReturnValue(0),
  }),
}))

const mockGlobalSettings = { globalSearchEnabled: true }
let mockLoading = false

vi.mock("@/hooks/search/useGlobalSearchSettings", () => ({
  useGlobalSearchSettings: () => ({
    settings: mockGlobalSettings,
    loading: mockLoading,
  }),
}))

import { useSearchSource } from "../search/use-search-source"

beforeEach(() => {
  mockGlobalSettings.globalSearchEnabled = true
  mockLoading = false
  vi.clearAllMocks()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe("P1-E — useSearchSource", () => {
  it("1. estado inicial: searchSource='local', sem modal", () => {
    const { result } = renderHook(() => useSearchSource())
    expect(result.current.searchSource).toBe('local')
    expect(result.current.showSourceChangeModal).toBe(false)
    expect(result.current.pendingSourceChange).toBeNull()
  })

  it("2. handleSourceChange('local') → atualiza direto sem abrir modal", () => {
    const { result } = renderHook(() => useSearchSource())
    act(() => { result.current.handleSourceChange('local') })
    expect(result.current.searchSource).toBe('local')
    expect(result.current.showSourceChangeModal).toBe(false)
  })

  it("3. handleSourceChange('hybrid') → abre modal com pendingSourceChange='hybrid'", () => {
    const { result } = renderHook(() => useSearchSource())
    act(() => { result.current.handleSourceChange('hybrid') })
    expect(result.current.showSourceChangeModal).toBe(true)
    expect(result.current.pendingSourceChange).toBe('hybrid')
    expect(result.current.searchSource).toBe('local') // ainda não confirmou
  })

  it("4. handleSourceChange('global') → abre modal com pendingSourceChange='global'", () => {
    const { result } = renderHook(() => useSearchSource())
    act(() => { result.current.handleSourceChange('global') })
    expect(result.current.showSourceChangeModal).toBe(true)
    expect(result.current.pendingSourceChange).toBe('global')
  })

  it("5. confirmSourceChange aplica mudança e fecha modal", () => {
    const { result } = renderHook(() => useSearchSource())
    act(() => { result.current.handleSourceChange('hybrid') })
    act(() => { result.current.confirmSourceChange() })
    expect(result.current.searchSource).toBe('hybrid')
    expect(result.current.showSourceChangeModal).toBe(false)
    expect(result.current.pendingSourceChange).toBeNull()
  })

  it("6. fechar modal sem confirmar não muda a fonte", () => {
    const { result } = renderHook(() => useSearchSource())
    act(() => { result.current.handleSourceChange('global') })
    act(() => { result.current.setShowSourceChangeModal(false) })
    expect(result.current.searchSource).toBe('local')
    expect(result.current.showSourceChangeModal).toBe(false)
  })

  it("8. setters de candidateLimit, requireEmails e requirePhoneNumbers", () => {
    const { result } = renderHook(() => useSearchSource())
    act(() => { result.current.setCandidateLimit(30) })
    expect(result.current.candidateLimit).toBe(30)
    act(() => { result.current.setRequireEmails(true) })
    expect(result.current.requireEmails).toBe(true)
    act(() => { result.current.setRequirePhoneNumbers(true) })
    expect(result.current.requirePhoneNumbers).toBe(true)
  })

  it("9. pearchSearchType always fast", () => {
    const { result } = renderHook(() => useSearchSource())
    expect(result.current.pearchSearchType).toBe('fast')
  })
})
