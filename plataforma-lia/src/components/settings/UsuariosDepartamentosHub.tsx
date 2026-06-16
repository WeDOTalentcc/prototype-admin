"use client"

import React, { useEffect, useState } from "react"
import { Users, Network } from "lucide-react"
import { useTranslations } from "next-intl"
import { tabStyles } from "@/lib/design-tokens"
import { UserManagement } from "./user-management"
import { DepartmentsTab } from "./DepartmentsTab"
import { DepartmentScopeBanner } from "./DepartmentScopeBanner"  // Sprint 2 RBAC Phase 3 (2026-05-25): nudge banner para popular dept_id
import { useCompanyId } from "@/hooks/company/useCompanyId"
import { useCompanyData } from "@/hooks/settings/useCompanyData"
import { useDepartmentManagement } from "@/hooks/settings/useDepartmentManagement"
import { useUserManagement } from "./use-user-management"

export function UsuariosDepartamentosHub() {
  const t = useTranslations("settings")
  const [activeTab, setActiveTab] = useState<string>(() => {
    if (typeof window === "undefined") return "users"
    try {
      const raw = sessionStorage.getItem("settings-pending-subtab")
      if (raw) {
        const parsed = JSON.parse(raw) as { section?: string; tab?: string }
        if (
          parsed?.section === "usuarios-departamentos" &&
          (parsed.tab === "users" || parsed.tab === "departments")
        ) {
          return parsed.tab
        }
      }
    } catch { /* ignore */ }
    return "users"
  })

  useEffect(() => {
    if (typeof window === "undefined") return
    try {
      sessionStorage.removeItem("settings-pending-subtab")
    } catch { /* ignore */ }
  }, [])

  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail
      if (!detail || typeof detail !== "object") return
      const wantedSection = (detail as { section?: string }).section
      const wantedTab = (detail as { tab?: string }).tab
      if (wantedSection && wantedSection !== "usuarios-departamentos") return
      if (wantedTab === "users" || wantedTab === "departments") {
        setActiveTab(wantedTab)
      }
    }
    window.addEventListener("settings-open-subtab", handler)
    return () => window.removeEventListener("settings-open-subtab", handler)
  }, [])

  const { state: companyState, actions: companyActions, initialDepartments, initialApprovers } = useCompanyData()
  const { companyId } = useCompanyId()  // Sprint 2 RBAC Phase 3 — companyId pro banner localStorage key isolation

  const { state: deptState, actions: deptActions } = useDepartmentManagement({
    initialDepartments,
    initialApprovers,
    setError: companyActions.setError,
    setSuccessMessage: companyActions.setSuccessMessage,
  })


  // B1 (2026-05-25): existing platform users for member linkage UX.
  // Lift state pattern: users canonical via useUserManagement.users, mapped to
  // ExistingUserOption shape, passed down to MemberSection through tab.
  const { users: hubUsers } = useUserManagement()
  const hubExistingUsers = (hubUsers ?? []).map((u: { id: string; name: string; email: string; position?: string }) => ({
    id: String(u.id),
    name: String(u.name),
    email: String(u.email),
    title: u.position ? String(u.position) : undefined,
  }))

  // Bug 2 fix (lift state, 2026-05-25): single source of truth for departments
  // shared between UserManagement and DepartmentManagement tabs. Eliminates
  // stale dropdown after create-in-other-tab race. Canonical-fix #2 (single SoT).
  const hubDeptList = (deptState.departments ?? []).map((d: { id: string; name: string; description?: string }) => ({
    id: String(d.id),
    name: String(d.name),
    code: null as string | null,
    is_active: true,
  }))

  const tabs = [
    { id: "users", label: t("companyTabs.users"), icon: Users },
    { id: "departments", label: t("companyTabs.departments"), icon: Network },
  ]

  const renderContent = () => {
    switch (activeTab) {
      case "users":
        return (
          <UserManagement
            departments={hubDeptList}
            onDepartmentChanged={deptActions.loadDepartments}
          />
        )
      case "departments":
        return (
          <DepartmentsTab
            companyData={companyState.companyData}
            saving={companyState.saving}
            successMessage={companyState.successMessage}
            error={companyState.error}
            updateLiaToggle={companyActions.updateLiaToggle}
            updateLiaInstruction={companyActions.updateLiaInstruction}
            departments={deptState.departments}
            editingDepartment={deptState.editingDepartment}
            showDepartmentForm={deptState.showDepartmentForm}
            departmentToDelete={deptState.departmentToDelete}
            newDepartment={deptState.newDepartment}
            isEditingDepartments={deptState.isEditingDepartments}
            departmentsBackup={deptState.departmentsBackup}
            existingUsers={hubExistingUsers}
            departmentMembers={deptState.departmentMembers}
            showMemberForm={deptState.showMemberForm}
            editingMember={deptState.editingMember}
            savingMember={deptState.savingMember}
            memberError={deptState.memberError}
            memberSuccess={deptState.memberSuccess}
            newMember={deptState.newMember}
            orgChartDepartment={deptState.orgChartDepartment}
            orgChartMembers={deptState.orgChartMembers}
            loadingOrgChart={deptState.loadingOrgChart}
            approvers={deptState.approvers}
            showApproverForm={deptState.showApproverForm}
            editingApprover={deptState.editingApprover}
            newApprover={deptState.newApprover}
            setDepartments={deptActions.setDepartments}
            setShowDepartmentForm={deptActions.setShowDepartmentForm}
            setDepartmentToDelete={deptActions.setDepartmentToDelete}
            setNewDepartment={deptActions.setNewDepartment}
            setIsEditingDepartments={deptActions.setIsEditingDepartments}
            setDepartmentsBackup={deptActions.setDepartmentsBackup}
            setShowMemberForm={deptActions.setShowMemberForm}
            setEditingMember={deptActions.setEditingMember}
            setNewMember={deptActions.setNewMember}
            setMemberError={deptActions.setMemberError}
            setOrgChartDepartment={deptActions.setOrgChartDepartment}
            setShowApproverForm={deptActions.setShowApproverForm}
            setEditingApprover={deptActions.setEditingApprover}
            setNewApprover={deptActions.setNewApprover}
            loadDepartments={deptActions.loadDepartments}
            handleSaveDepartment={deptActions.handleSaveDepartment}
            handleDeleteDepartment={deptActions.handleDeleteDepartment}
            handleStartEditDepartment={deptActions.handleStartEditDepartment}
            handleCancelDepartmentForm={deptActions.handleCancelDepartmentForm}
            handleSaveMember={deptActions.handleSaveMember}
            handleEditMember={deptActions.handleEditMember}
            handleDeleteMember={deptActions.handleDeleteMember}
            handleOpenOrgChart={deptActions.handleOpenOrgChart}
            handleSaveApprover={deptActions.handleSaveApprover}
            handleDeleteApprover={deptActions.handleDeleteApprover}
          />
        )
      default:
        return (
          <UserManagement
            departments={hubDeptList}
            onDepartmentChanged={deptActions.loadDepartments}
          />
        )
    }
  }

  return (
    <div className="space-y-3" data-testid="usuarios-departamentos-hub">
      {/* Sprint 2 RBAC Phase 3 (2026-05-25): banner educacional sobre dept scope soft launch.
          Plan canonical: ~/.claude/plans/jolly-roaming-moler.md */}
      <DepartmentScopeBanner
        departmentsCount={deptState.departments?.length ?? 0}
        companyId={typeof companyId === "string" ? companyId : null}
        onSwitchToDepartmentsTab={() => setActiveTab("departments")}
      />

      <div className={tabStyles.pillContainer}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            data-testid={`usuarios-departamentos-tab-${tab.id}`}
            onClick={() => setActiveTab(tab.id)}
            className={activeTab === tab.id ? tabStyles.pillActive : tabStyles.pill}
          >
            <tab.icon className={tabStyles.pillIcon} />
            {tab.label}
          </button>
        ))}
      </div>

      {renderContent()}
    </div>
  )
}

export default UsuariosDepartamentosHub
