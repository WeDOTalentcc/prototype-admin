"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import {
  Plus,
  Edit,
  Save,
  CheckCircle,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { LiaFieldToggle, defaultLiaFieldExamples } from './LiaFieldToggle';
import {
  type Department,
  type DepartmentMember,
  type Approver,
  type CompanyData,
  type NewDepartmentForm,
  type NewMemberForm,
  type NewApproverForm,
} from '@/hooks/settings/department-types';
import { actionButtonStyles } from "@/lib/design-tokens";
import { ApproverSection } from "./ApproverSection";
import { DepartmentFormCard } from "./DepartmentFormCard";
import type { ExistingUserOption } from "./MemberSection";
import { DepartmentGrid } from "./DepartmentGrid";
import { OrgChartDialog } from "./OrgChartDialog";
import { useTranslations } from "next-intl";

export interface DepartmentsTabProps {
  companyData: CompanyData;
  saving: boolean;
  successMessage: string | null;
  error: string | null;
  updateLiaToggle: (fieldKey: string, isActive: boolean) => void;
  updateLiaInstruction: (fieldKey: string, instruction: string) => void;
  departments: Department[];
  editingDepartment: Department | null;
  showDepartmentForm: boolean;
  departmentToDelete: Department | null;
  newDepartment: NewDepartmentForm;
  isEditingDepartments: boolean;
  departmentsBackup: Department[];
  departmentMembers: DepartmentMember[];
  showMemberForm: boolean;
  editingMember: DepartmentMember | null;
  savingMember: boolean;
  memberError: string | null;
  memberSuccess: string | null;
  newMember: NewMemberForm;
  orgChartDepartment: Department | null;
  orgChartMembers: DepartmentMember[];
  loadingOrgChart: boolean;
  approvers: Approver[];
  showApproverForm: boolean;
  editingApprover: Approver | null;
  newApprover: NewApproverForm;
  setDepartments: React.Dispatch<React.SetStateAction<Department[]>>;
  setShowDepartmentForm: (show: boolean) => void;
  setDepartmentToDelete: (dept: Department | null) => void;
  setNewDepartment: React.Dispatch<React.SetStateAction<NewDepartmentForm>>;
  setIsEditingDepartments: (editing: boolean) => void;
  setDepartmentsBackup: (backup: Department[]) => void;
  setShowMemberForm: (show: boolean) => void;
  setEditingMember: (member: DepartmentMember | null) => void;
  setNewMember: React.Dispatch<React.SetStateAction<NewMemberForm>>;
  setMemberError: (error: string | null) => void;
  setOrgChartDepartment: (dept: Department | null) => void;
  setShowApproverForm: (show: boolean) => void;
  setEditingApprover: (approver: Approver | null) => void;
  setNewApprover: React.Dispatch<React.SetStateAction<NewApproverForm>>;
  loadDepartments: () => Promise<void>;
  handleSaveDepartment: () => Promise<void>;
  handleDeleteDepartment: (id: string) => Promise<void>;
  handleStartEditDepartment: (dept: Department) => void;
  handleCancelDepartmentForm: () => void;
  handleSaveMember: () => Promise<void>;
  handleEditMember: (member: DepartmentMember) => void;
  handleDeleteMember: (memberId: string) => Promise<void>;
  handleOpenOrgChart: (dept: Department) => Promise<void>;
  handleSaveApprover: () => Promise<void>;
  handleDeleteApprover: (id: string) => Promise<void>;
  // B1 (2026-05-25): platform users for linkage UX
  existingUsers?: ExistingUserOption[];
}

export function DepartmentsTab({
  companyData,
  saving,
  successMessage,
  error,
  updateLiaToggle,
  updateLiaInstruction,
  departments,
  editingDepartment,
  showDepartmentForm,
  departmentToDelete,
  newDepartment,
  isEditingDepartments,
  departmentsBackup,
  departmentMembers,
  showMemberForm,
  editingMember,
  savingMember,
  memberError,
  memberSuccess,
  newMember,
  orgChartDepartment,
  orgChartMembers,
  loadingOrgChart,
  approvers,
  showApproverForm,
  editingApprover,
  newApprover,
  setDepartments,
  setShowDepartmentForm,
  setDepartmentToDelete,
  setNewDepartment,
  setIsEditingDepartments,
  setDepartmentsBackup,
  setShowMemberForm,
  setEditingMember,
  setNewMember,
  setMemberError,
  setOrgChartDepartment,
  setShowApproverForm,
  setEditingApprover,
  setNewApprover,
  loadDepartments,
  handleSaveDepartment,
  handleDeleteDepartment,
  handleStartEditDepartment,
  handleCancelDepartmentForm,
  handleSaveMember,
  handleEditMember,
  handleDeleteMember,
  handleOpenOrgChart,
  handleSaveApprover,
  handleDeleteApprover,
  existingUsers,
}: DepartmentsTabProps) {
  const t = useTranslations('settings.departments');

  return (
    <>
      <div className="space-y-3" data-testid="departments-tab-root">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="flex items-center gap-2 text-base-ui font-semibold text-lia-text-primary">
              {t('title')}
              <LiaFieldToggle
                fieldKey="departments"
                isActive={companyData.lia_field_toggles?.departments ?? true}
                currentInstruction={companyData.lia_instructions?.departments || ''}
                examples={defaultLiaFieldExamples.departments}
                onToggleChange={updateLiaToggle}
                onInstructionSave={updateLiaInstruction}
                compact
              />
            </h3>
            <p className="text-xs text-lia-text-secondary">
              {t('description')}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {!isEditingDepartments ? (
              <button
                onClick={() => {
                  setDepartmentsBackup([...departments]);
                  setIsEditingDepartments(true);
                }}
                className={actionButtonStyles.smOutline}
                data-action="edit"
                data-testid="departments-edit-button"
                aria-label="Editar departamentos"
              >
                <Edit className={actionButtonStyles.icon} />
                {t('edit')}
              </button>
            ) : (
              <>
                <button
                  onClick={() => {
                    setDepartments(departmentsBackup);
                    setIsEditingDepartments(false);
                    setDepartmentsBackup([]);
                    setShowDepartmentForm(false);
                  }}
                  disabled={saving}
                  className={actionButtonStyles.smSecondary}
                  data-action="cancel"
                  data-testid="departments-cancel-button"
                  aria-label="Cancelar edição de departamentos"
                >
                  {t('cancel')}
                </button>
                <button
                  onClick={async () => {
                    setIsEditingDepartments(false);
                    setDepartmentsBackup([]);
                  }}
                  disabled={saving}
                  className={actionButtonStyles.smPrimary}
                  data-action="save"
                  data-testid="departments-save-button"
                  aria-label="Salvar departamentos"
                >
                  {saving ? (
                    <>
                      <Loader2 className={`${actionButtonStyles.icon} animate-spin motion-reduce:animate-none`} />
                      {t('saving')}
                    </>
                  ) : (
                    <>
                      <Save className={actionButtonStyles.icon} />
                      {t('saveChanges')}
                    </>
                  )}
                </button>
                <Button
                  onClick={() => setShowDepartmentForm(true)}
                  size="sm"
                  data-action="new-department"
                  data-testid="departments-new-button"
                  aria-label="Adicionar novo departamento"
                  className="gap-1.5 py-1.5 px-2 text-xs rounded-full bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
                >
                  <Plus className="w-3.5 h-3.5" />
                  {t('newDepartment')}
                </Button>
              </>
            )}
          </div>
        </div>

        {showDepartmentForm && isEditingDepartments && (
          <DepartmentFormCard
            editingDepartment={editingDepartment}
            newDepartment={newDepartment}
            isEditingDepartments={isEditingDepartments}
            departmentMembers={departmentMembers}
            showMemberForm={showMemberForm}
            editingMember={editingMember}
            savingMember={savingMember}
            memberError={memberError}
            memberSuccess={memberSuccess}
            newMember={newMember}
            setNewDepartment={setNewDepartment}
            setShowMemberForm={setShowMemberForm}
            setEditingMember={setEditingMember}
            setNewMember={setNewMember}
            setMemberError={setMemberError}
            handleCancelDepartmentForm={handleCancelDepartmentForm}
            handleSaveDepartment={handleSaveDepartment}
            handleSaveMember={handleSaveMember}
            handleEditMember={handleEditMember}
            handleDeleteMember={handleDeleteMember}
            existingUsers={existingUsers}
          />
        )}

        {successMessage && (
          <div className="bg-status-success/10 border border-status-success/30 rounded-xl p-2 flex items-center gap-2 text-status-success text-xs">
            <CheckCircle className="w-3.5 h-3.5" />
            {successMessage}
          </div>
        )}
        {error && (
          <div className="bg-status-error/10 border border-status-error/30 rounded-xl p-2 flex items-center gap-2 text-status-error text-xs">
            <AlertCircle className="w-3.5 h-3.5" />
            {error}
          </div>
        )}

        <DepartmentGrid
          departments={departments}
          showDepartmentForm={showDepartmentForm}
          departmentToDelete={departmentToDelete}
          isEditingDepartments={isEditingDepartments}
          setDepartmentToDelete={setDepartmentToDelete}
          handleStartEditDepartment={handleStartEditDepartment}
          handleDeleteDepartment={handleDeleteDepartment}
          handleOpenOrgChart={handleOpenOrgChart}
        />

        <OrgChartDialog
          orgChartDepartment={orgChartDepartment}
          orgChartMembers={orgChartMembers}
          loadingOrgChart={loadingOrgChart}
          setOrgChartDepartment={setOrgChartDepartment}
        />
      </div>

      <ApproverSection
        approvers={approvers}
        showApproverForm={showApproverForm}
        editingApprover={editingApprover}
        newApprover={newApprover}
        successMessage={successMessage}
        error={error}
        setShowApproverForm={setShowApproverForm}
        setEditingApprover={setEditingApprover}
        setNewApprover={setNewApprover}
        handleSaveApprover={handleSaveApprover}
        handleDeleteApprover={handleDeleteApprover}
      />
    </>
  );
}
