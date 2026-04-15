"use client"

import React, { useState } from "react"
import { Users, Network } from "lucide-react"
import { useTranslations } from "next-intl"
import { tabStyles } from "@/lib/design-tokens"
import { UserManagement } from "./user-management"
import { DepartmentsTab } from "./DepartmentsTab"
import { useCompanyData } from "@/hooks/settings/useCompanyData"
import { useDepartmentManagement } from "@/hooks/settings/useDepartmentManagement"

export function UsuariosDepartamentosHub() {
  const t = useTranslations("settings")
  const [activeTab, setActiveTab] = useState("users")

  const { state: companyState, actions: companyActions, initialDepartments, initialApprovers } = useCompanyData()

  const { state: deptState, actions: deptActions } = useDepartmentManagement({
    initialDepartments,
    initialApprovers,
    setError: companyActions.setError,
    setSuccessMessage: companyActions.setSuccessMessage,
  })

  const tabs = [
    { id: "users", label: t("companyTabs.users"), icon: Users },
    { id: "departments", label: t("companyTabs.departments"), icon: Network },
  ]

  const renderContent = () => {
    switch (activeTab) {
      case "users":
        return <UserManagement />
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
        return <UserManagement />
    }
  }

  return (
    <div className="space-y-3">
      <div className={tabStyles.pillContainer}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
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
