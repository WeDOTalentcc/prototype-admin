/**
 * Testes do hook useAuthenticatedUserId + helper resolveUserId.
 *
 * Introduzido no BUG-08 do QA 2026-04-15 para evitar fallback 'default_user'
 * em requests pré-auth (que causavam duplo fetch: default_user + email real).
 */
import { renderHook } from "@testing-library/react"
import { describe, it, expect, vi, beforeEach } from "vitest"

import {
  useAuthenticatedUserId,
  resolveUserId,
} from "../shared/use-authenticated-user-id"

// Mock do contexto de auth
vi.mock("@/contexts/auth-context", () => ({
  useAuth: vi.fn(),
}))

import { useAuth } from "@/contexts/auth-context"

describe("resolveUserId", () => {
  it("retorna null quando user é null/undefined", () => {
    expect(resolveUserId(null)).toBeNull()
    expect(resolveUserId(undefined)).toBeNull()
  })

  it("prefere id sobre email", () => {
    expect(resolveUserId({ id: "uuid-123", email: "x@y.com" } as any)).toBe("uuid-123")
  })

  it("usa email quando id é ausente", () => {
    expect(resolveUserId({ email: "x@y.com" } as any)).toBe("x@y.com")
  })

  it("retorna null quando nem id nem email presentes", () => {
    expect(resolveUserId({} as any)).toBeNull()
  })
})

describe("useAuthenticatedUserId", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("isReady = false enquanto auth está carregando", () => {
    ;(useAuth as any).mockReturnValue({
      user: null,
      isLoading: true,
      isAuthenticated: false,
    })
    const { result } = renderHook(() => useAuthenticatedUserId())
    expect(result.current.userId).toBeNull()
    expect(result.current.isReady).toBe(false)
  })

  it("isReady = false quando auth terminou de carregar mas sem usuário", () => {
    ;(useAuth as any).mockReturnValue({
      user: null,
      isLoading: false,
      isAuthenticated: false,
    })
    const { result } = renderHook(() => useAuthenticatedUserId())
    expect(result.current.userId).toBeNull()
    expect(result.current.isReady).toBe(false)
  })

  it("isReady = true e userId preenchido quando auth carregou com usuário", () => {
    ;(useAuth as any).mockReturnValue({
      user: { id: "user-uuid-42", email: "p@wedotalent.cc" },
      isLoading: false,
      isAuthenticated: true,
    })
    const { result } = renderHook(() => useAuthenticatedUserId())
    expect(result.current.userId).toBe("user-uuid-42")
    expect(result.current.isReady).toBe(true)
  })

  it("nunca retorna 'default_user' — contrato explícito do hook", () => {
    ;(useAuth as any).mockReturnValue({
      user: null,
      isLoading: true,
      isAuthenticated: false,
    })
    const { result } = renderHook(() => useAuthenticatedUserId())
    expect(result.current.userId).not.toBe("default_user")
    expect(result.current.userId).toBeNull()
  })
})
