import { describe, it, expect, vi, beforeEach } from "vitest"
import { renderHook, act } from "@testing-library/react"
import { useSettingsEditMode } from "@/hooks/settings/useSettingsEditMode"

vi.mock("@/contexts/auth-context", () => ({
  useAuth: vi.fn(),
}))

import { useAuth } from "@/contexts/auth-context"
const mockUseAuth = vi.mocked(useAuth)

describe("useSettingsEditMode — P2-2 B.4", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    if (typeof window !== "undefined") {
      window.localStorage.clear()
    }
  })

  it("admin tem canToggle=true em qualquer hub", () => {
    mockUseAuth.mockReturnValue({ user: { role: "admin" } } as any)
    const { result } = renderHook(() => useSettingsEditMode("minha-empresa"))
    expect(result.current.canToggle).toBe(true)
  })

  it("viewer tem canToggle=false (read-only forçado)", () => {
    mockUseAuth.mockReturnValue({ user: { role: "viewer" } } as any)
    const { result } = renderHook(() => useSettingsEditMode("minha-empresa"))
    expect(result.current.canToggle).toBe(false)
    expect(result.current.isEditing).toBe(false)
  })

  it("recruiter tem canToggle=true em recrutamento-lia", () => {
    mockUseAuth.mockReturnValue({ user: { role: "recruiter" } } as any)
    const { result } = renderHook(() => useSettingsEditMode("recrutamento-lia"))
    expect(result.current.canToggle).toBe(true)
  })

  it("recruiter tem canToggle=false em integrations", () => {
    mockUseAuth.mockReturnValue({ user: { role: "recruiter" } } as any)
    const { result } = renderHook(() => useSettingsEditMode("integrations"))
    expect(result.current.canToggle).toBe(false)
  })

  it("user null tem canToggle=false (fail-secure)", () => {
    mockUseAuth.mockReturnValue({ user: null } as any)
    const { result } = renderHook(() => useSettingsEditMode("minha-empresa"))
    expect(result.current.canToggle).toBe(false)
  })

  it("default state isEditing=true (legacy preservado)", () => {
    mockUseAuth.mockReturnValue({ user: { role: "admin" } } as any)
    const { result } = renderHook(() => useSettingsEditMode("minha-empresa"))
    expect(result.current.isEditing).toBe(true)
  })

  it("toggleEditMode flipa isEditing", () => {
    mockUseAuth.mockReturnValue({ user: { role: "admin" } } as any)
    const { result } = renderHook(() => useSettingsEditMode("minha-empresa"))
    expect(result.current.isEditing).toBe(true)
    act(() => result.current.toggleEditMode())
    expect(result.current.isEditing).toBe(false)
    act(() => result.current.toggleEditMode())
    expect(result.current.isEditing).toBe(true)
  })

  it("toggleEditMode no-op quando canToggle=false", () => {
    mockUseAuth.mockReturnValue({ user: { role: "viewer" } } as any)
    const { result } = renderHook(() => useSettingsEditMode("minha-empresa"))
    expect(result.current.isEditing).toBe(false)
    act(() => result.current.toggleEditMode())
    expect(result.current.isEditing).toBe(false)
  })

  it("setEditMode(false) força read-only", () => {
    mockUseAuth.mockReturnValue({ user: { role: "admin" } } as any)
    const { result } = renderHook(() => useSettingsEditMode("minha-empresa"))
    act(() => result.current.setEditMode(false))
    expect(result.current.isEditing).toBe(false)
  })

  it("persiste em localStorage", () => {
    mockUseAuth.mockReturnValue({ user: { role: "admin" } } as any)
    const { result } = renderHook(() => useSettingsEditMode("minha-empresa"))
    act(() => result.current.setEditMode(false))
    expect(window.localStorage.getItem("lia-settings-edit-mode")).toBe("false")
  })

  it("lê localStorage no init", () => {
    window.localStorage.setItem("lia-settings-edit-mode", "false")
    mockUseAuth.mockReturnValue({ user: { role: "admin" } } as any)
    const { result } = renderHook(() => useSettingsEditMode("minha-empresa"))
    expect(result.current.isEditing).toBe(false)
  })
})
