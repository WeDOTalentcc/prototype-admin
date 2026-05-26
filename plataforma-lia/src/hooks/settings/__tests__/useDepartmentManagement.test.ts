import { describe, it, expect, vi, beforeEach } from "vitest"
import { renderHook, act, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import React from "react"
import { useDepartmentManagement } from "../useDepartmentManagement"
import type { Department, Approver } from "../department-types"

// ── Mocks ──────────────────────────────────────────────────────────────────

vi.mock("@/hooks/company/useCompanyId", () => ({
  useCompanyId: () => ({ companyId: "company-test-id" }),
}))

vi.mock("@/lib/api/settings-notify", () => ({
  notifyChatOfSettingsUpdate: vi.fn(),
}))

vi.mock("@/lib/toast", () => ({
  toast: { error: vi.fn() },
}))

// Minimal fetch mock
global.fetch = vi.fn().mockResolvedValue({
  ok: true,
  json: async () => [],
})

const DEPTS: Department[] = [
  {
    id: "dept-1",
    name: "Engenharia",
    description: "Times de engenharia",
    headcount: 10,
    color: "bg-lia-btn-primary-bg text-lia-btn-primary-text",
  },
]

const APPROVERS: Approver[] = [
  {
    id: "appr-1",
    userId: "user-1",
    userName: "Ana Lima",
    email: "ana@example.com",
    role: "Manager",
    level: 1,
    isActive: true,
    departmentId: null,
    canApproveAboveAmount: null,
  },
]

function makeWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  const Wrapper = ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: qc }, children)
  Wrapper.displayName = "QueryWrapper"
  return Wrapper
}

// ── Tests ──────────────────────────────────────────────────────────────────

describe("useDepartmentManagement — smoke tests", () => {
  const setError = vi.fn()
  const setSuccessMessage = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: async () => [],
    })
  })

  it("mounts without throwing", () => {
    const { result } = renderHook(
      () =>
        useDepartmentManagement({
          initialDepartments: [],
          initialApprovers: [],
          setError,
          setSuccessMessage,
        }),
      { wrapper: makeWrapper() },
    )
    expect(result.current).toBeDefined()
    expect(result.current.state).toBeDefined()
    expect(result.current.actions).toBeDefined()
  })

  it("initial state has correct empty/false defaults", () => {
    const { result } = renderHook(
      () =>
        useDepartmentManagement({
          initialDepartments: [],
          initialApprovers: [],
          setError,
          setSuccessMessage,
        }),
      { wrapper: makeWrapper() },
    )
    const s = result.current.state
    expect(Array.isArray(s.departments)).toBe(true)
    expect(s.editingDepartment).toBeNull()
    expect(s.showDepartmentForm).toBe(false)
    expect(s.departmentToDelete).toBeNull()
    expect(s.isEditingDepartments).toBe(false)
    expect(Array.isArray(s.departmentsBackup)).toBe(true)
    expect(Array.isArray(s.departmentMembers)).toBe(true)
    expect(s.showMemberForm).toBe(false)
    expect(s.editingMember).toBeNull()
    expect(s.savingMember).toBe(false)
    expect(s.memberError).toBeNull()
    expect(s.memberSuccess).toBeNull()
    expect(s.orgChartDepartment).toBeNull()
    expect(Array.isArray(s.orgChartMembers)).toBe(true)
    expect(s.loadingOrgChart).toBe(false)
    expect(s.showApproverForm).toBe(false)
    expect(s.editingApprover).toBeNull()
  })

  it("initialDepartments prop seeds the departments list", async () => {
    const { result } = renderHook(
      () =>
        useDepartmentManagement({
          initialDepartments: DEPTS,
          initialApprovers: [],
          setError,
          setSuccessMessage,
        }),
      { wrapper: makeWrapper() },
    )
    await waitFor(() => {
      expect(result.current.state.departments).toEqual(DEPTS)
    })
  })

  it("initialApprovers prop seeds the approvers list", async () => {
    const { result } = renderHook(
      () =>
        useDepartmentManagement({
          initialDepartments: [],
          initialApprovers: APPROVERS,
          setError,
          setSuccessMessage,
        }),
      { wrapper: makeWrapper() },
    )
    await waitFor(() => {
      expect(result.current.state.approvers).toEqual(APPROVERS)
    })
  })

  it("useReducer: setShowDepartmentForm transitions to true", () => {
    const { result } = renderHook(
      () =>
        useDepartmentManagement({
          initialDepartments: [],
          initialApprovers: [],
          setError,
          setSuccessMessage,
        }),
      { wrapper: makeWrapper() },
    )
    act(() => {
      result.current.actions.setShowDepartmentForm(true)
    })
    expect(result.current.state.showDepartmentForm).toBe(true)
  })

  it("useReducer: setEditingDepartment sets and clears", () => {
    const { result } = renderHook(
      () =>
        useDepartmentManagement({
          initialDepartments: DEPTS,
          initialApprovers: [],
          setError,
          setSuccessMessage,
        }),
      { wrapper: makeWrapper() },
    )
    act(() => {
      result.current.actions.setEditingDepartment(DEPTS[0])
    })
    expect(result.current.state.editingDepartment).toEqual(DEPTS[0])
    act(() => {
      result.current.actions.setEditingDepartment(null)
    })
    expect(result.current.state.editingDepartment).toBeNull()
  })

  it("handleCancelDepartmentForm resets form state", () => {
    const { result } = renderHook(
      () =>
        useDepartmentManagement({
          initialDepartments: [],
          initialApprovers: [],
          setError,
          setSuccessMessage,
        }),
      { wrapper: makeWrapper() },
    )
    act(() => {
      result.current.actions.setShowDepartmentForm(true)
      result.current.actions.setShowMemberForm(true)
    })
    act(() => {
      result.current.actions.handleCancelDepartmentForm()
    })
    expect(result.current.state.showDepartmentForm).toBe(false)
    expect(result.current.state.showMemberForm).toBe(false)
    expect(result.current.state.editingDepartment).toBeNull()
  })

  it("public API exposes all 23 action methods", () => {
    const { result } = renderHook(
      () =>
        useDepartmentManagement({
          initialDepartments: [],
          initialApprovers: [],
          setError,
          setSuccessMessage,
        }),
      { wrapper: makeWrapper() },
    )
    const expected = [
      "setDepartments",
      "setEditingDepartment",
      "setShowDepartmentForm",
      "setDepartmentToDelete",
      "setNewDepartment",
      "setIsEditingDepartments",
      "setDepartmentsBackup",
      "setShowMemberForm",
      "setEditingMember",
      "setNewMember",
      "setMemberError",
      "setOrgChartDepartment",
      "setApprovers",
      "setShowApproverForm",
      "setEditingApprover",
      "setNewApprover",
      "loadDepartments",
      "handleSaveDepartment",
      "handleDeleteDepartment",
      "handleStartEditDepartment",
      "handleCancelDepartmentForm",
      "handleSaveMember",
      "handleEditMember",
      "handleDeleteMember",
      "handleOpenOrgChart",
      "handleSaveApprover",
      "handleDeleteApprover",
    ]
    expected.forEach((method) => {
      expect(typeof (result.current.actions as Record<string, unknown>)[method]).toBe("function")
    })
  })
})
