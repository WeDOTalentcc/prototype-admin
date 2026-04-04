"use client";

import React, { useState, useEffect } from "react";
import { Building, Users, Network, Code } from "lucide-react";
import { CompanyDataSection } from './CompanyDataSection';
import { UserManagement } from "./user-management";
import { BenefitsTab } from "./BenefitsTab";
import { Gift } from "lucide-react";
import { DepartmentsTab } from "./DepartmentsTab";
import { TechStackTab } from "./TechStackTab";
import { TECH_STACK_CATEGORIES } from './companyTeamHub.types';
import type { CompanyTeamHubProps } from './companyTeamHub.types';
import { useCompanyData } from "@/hooks/settings/useCompanyData";
import { useDepartmentManagement } from "@/hooks/settings/useDepartmentManagement";
import { tabStyles } from "@/lib/design-tokens";

export function CompanyTeamHub({
  activeSubsection,
  onUserUpdate,
  onGoalUpdate,
}: CompanyTeamHubProps) {
  const [activeTab, setActiveTab] = useState(
    activeSubsection || "company-data",
  );

  const { state: companyState, actions: companyActions, initialDepartments, initialApprovers } = useCompanyData();

  const { state: deptState, actions: deptActions } = useDepartmentManagement({
    initialDepartments,
    initialApprovers,
    setError: companyActions.setError,
    setSuccessMessage: companyActions.setSuccessMessage,
  });

  const tabs = [
    { id: "company-data", label: "Dados da Empresa", icon: Building },
    { id: "departments", label: "Departamentos", icon: Network },
    { id: "tech-stack", label: "Tech Stack", icon: Code },
    { id: "benefits", label: "Benefícios", icon: Gift },
    { id: "users", label: "Usuários", icon: Users },
  ];

  const renderCompanyData = () => {
    return (
      <CompanyDataSection
        companyData={companyState.companyData as any}
        setCompanyData={companyActions.setCompanyData as any}
        isEditingCompanyData={companyState.isEditingCompanyData}
        setIsEditingCompanyData={companyActions.setIsEditingCompanyData}
        companyDataBackup={companyState.companyDataBackup as any}
        setCompanyDataBackup={companyActions.setCompanyDataBackup as any}
        saveCompanyData={companyActions.saveCompanyData}
        saving={companyState.saving}
        loading={companyState.loading}
        successMessage={companyState.successMessage}
        error={companyState.error}
        updateLiaToggle={companyActions.updateLiaToggle}
        updateLiaInstruction={companyActions.updateLiaInstruction}
        isLiaAnalyzing={companyState.isLiaAnalyzing}
        liaAnalysisProgress={companyState.liaAnalysisProgress}
        liaAnalysisStep={companyState.liaAnalysisStep}
        handleLiaAnalysis={companyActions.handleLiaAnalysis}
        handleSaveCultureFields={companyActions.handleSaveCultureFields}
        techStackByCategory={companyState.techStackByCategory}
        expandedCategories={companyState.expandedCategories}
        setExpandedCategories={companyActions.setExpandedCategories}
        addTechToCategory={companyActions.addTechToCategory}
        removeTechFromCategory={companyActions.removeTechFromCategory}
        TECH_STACK_CATEGORIES={TECH_STACK_CATEGORIES as any}
      />
    );
  };

  const renderDepartments = () => (
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
  );

  const renderTechStack = () => (
    <TechStackTab
      companyData={companyState.companyData}
      isEditingCompanyData={companyState.isEditingCompanyData}
      techStackByCategory={companyState.techStackByCategory}
      expandedCategories={companyState.expandedCategories}
      setExpandedCategories={companyActions.setExpandedCategories}
      setCompanyData={companyActions.setCompanyData}
      addTechToCategory={companyActions.addTechToCategory}
      removeTechFromCategory={companyActions.removeTechFromCategory}
      updateLiaToggle={companyActions.updateLiaToggle}
      updateLiaInstruction={companyActions.updateLiaInstruction}
    />
  );

  const renderUsers = () => <UserManagement onUserUpdate={onUserUpdate as any} />;

  const renderContent = () => {
    switch (activeTab) {
      case "company-data":
        return renderCompanyData();
      case "departments":
        return renderDepartments();
      case "tech-stack":
        return renderTechStack();
      case "benefits":
        return <BenefitsTab />;
      case "users":
        return renderUsers();
      default:
        return renderCompanyData();
    }
  };

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
  );
}
