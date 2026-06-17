/**
 * Testes — useLiaFloat + LiaFloatProvider (Phase 4a)
 *
 * Camada 2 (Unitário FE — Vitest + jsdom)
 *
 * Cobre:
 * - Estado inicial: isOpen=false, conversationId=null
 * - open() abre o painel
 * - open(id) abre com conversationId específico
 * - close() fecha o painel
 * - toggle() alterna estado
 * - Lança erro se usado fora do provider
 */
import React from "react"
import { renderHook, act } from "@testing-library/react"
import { vi, describe, it, expect } from "vitest"
import { LiaFloatProvider, useLiaFloat } from "../../contexts/lia-float-context"

// Wrapper com provider para os testes que precisam dele
function wrapper({ children }: { children: React.ReactNode }) {
  return React.createElement(LiaFloatProvider, null, children)
}

describe("useLiaFloat", () => {
  // ── Estado inicial ──────────────────────────────────────────────────────

  it("inicia com isOpen=false e conversationId=null", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })
    expect(result.current.isOpen).toBe(false)
    expect(result.current.conversationId).toBeNull()
  })

  // ── open() ──────────────────────────────────────────────────────────────

  it("open() define isOpen=true sem conversationId", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    act(() => { result.current.open() })

    expect(result.current.isOpen).toBe(true)
    expect(result.current.conversationId).toBeNull()
  })

  it("open(id) define isOpen=true com conversationId", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    act(() => { result.current.open("conv-123") })

    expect(result.current.isOpen).toBe(true)
    expect(result.current.conversationId).toBe("conv-123")
  })

  it("open(id) substituindo id anterior", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    act(() => { result.current.open("conv-A") })
    act(() => { result.current.open("conv-B") })

    expect(result.current.conversationId).toBe("conv-B")
    expect(result.current.isOpen).toBe(true)
  })

  // ── close() ─────────────────────────────────────────────────────────────

  it("close() define isOpen=false", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    act(() => { result.current.open() })
    expect(result.current.isOpen).toBe(true)

    act(() => { result.current.close() })
    expect(result.current.isOpen).toBe(false)
  })

  it("close() mantém conversationId inalterado", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    act(() => { result.current.open("conv-keep") })
    act(() => { result.current.close() })

    // conversationId preservado para reabrir depois
    expect(result.current.conversationId).toBe("conv-keep")
  })

  // ── toggle() ────────────────────────────────────────────────────────────

  it("toggle() abre quando fechado", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    act(() => { result.current.toggle() })
    expect(result.current.isOpen).toBe(true)
  })

  it("toggle() fecha quando aberto", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    act(() => { result.current.open() })
    act(() => { result.current.toggle() })
    expect(result.current.isOpen).toBe(false)
  })

  it("toggle() duplo retorna ao estado original", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    act(() => { result.current.toggle() })
    act(() => { result.current.toggle() })
    expect(result.current.isOpen).toBe(false)
  })

  // ── Erro sem provider ────────────────────────────────────────────────────

  it("lança erro se usado fora do LiaFloatProvider", () => {
    // Silencia o console.error do React durante o teste
    const spy = vi.spyOn(console, "error").mockImplementation(() => {})
    expect(() => renderHook(() => useLiaFloat())).toThrow(
      "useLiaFloat deve ser usado dentro de LiaFloatProvider"
    )
    spy.mockRestore()
  })
})
