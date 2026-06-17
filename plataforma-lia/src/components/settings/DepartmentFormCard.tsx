"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { X, Save } from "lucide-react";
import {
  type Department,
  type DepartmentMember,
  type NewDepartmentForm,
  type NewMemberForm,
  COLOR_OPTIONS,
} from '@/hooks/settings/department-types';
import { MemberSection, type ExistingUserOption } from './MemberSection';
import { useTranslations } from "next-intl";

export interface DepartmentFormCardProps {
  editingDepartment: Department | null;
  newDepartment: NewDepartmentForm;
  isEditingDepartments: boolean;
  departmentMembers: DepartmentMember[];
  showMemberForm: boolean;
  editingMember: DepartmentMember | null;
  savingMember: boolean;
  memberError: string | null;
  memberSuccess: string | null;
  newMember: NewMemberForm;
  setNewDepartment: React.Dispatch<React.SetStateAction<NewDepartmentForm>>;
  setShowMemberForm: (show: boolean) => void;
  setEditingMember: (member: DepartmentMember | null) => void;
  setNewMember: React.Dispatch<React.SetStateAction<NewMemberForm>>;
  setMemberError: (error: string | null) => void;
  handleCancelDepartmentForm: () => void;
  handleSaveDepartment: () => Promise<void>;
  handleSaveMember: () => Promise<void>;
  handleEditMember: (member: DepartmentMember) => void;
  handleDeleteMember: (memberId: string) => Promise<void>;
  // B1 (2026-05-25): pass platform users for explicit linkage
  existingUsers?: ExistingUserOption[];
}

export function DepartmentFormCard({
  editingDepartment,
  newDepartment,
  isEditingDepartments,
  departmentMembers,
  showMemberForm,
  editingMember,
  savingMember,
  memberError,
  memberSuccess,
  newMember,
  setNewDepartment,
  setShowMemberForm,
  setEditingMember,
  setNewMember,
  setMemberError,
  handleCancelDepartmentForm,
  handleSaveDepartment,
  handleSaveMember,
  handleEditMember,
  handleDeleteMember,
  existingUsers,
}: DepartmentFormCardProps) {
  const t = useTranslations('settings.departments');

  return (
    <Card data-testid={editingDepartment ? 'department-edit-form' : 'department-create-form'} className="border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 rounded-xl">
      <CardContent className="p-3 space-y-2">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-xs font-semibold text-lia-text-primary">
            {editingDepartment ? t("editDepartment") : t("newDepartment")}
          </h4>
          <Button
            data-testid="department-form-close"
            variant="ghost"
            size="sm"
            className="h-6 w-6 p-0 rounded-md"
            onClick={handleCancelDepartmentForm}
          >
            <X className="w-3.5 h-3.5" />
          </Button>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="block text-micro font-medium text-lia-text-secondary mb-1">
              {t('formName')}
            </label>
            <input
              type="text"
              data-field="name"
              data-testid="department-field-name"
              value={newDepartment.name}
              onChange={(e) =>
                setNewDepartment((prev) => ({ ...prev, name: e.target.value }))
              }
              className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-primary focus:ring-2 focus:ring-lia-border-subtle focus:border-lia-border-medium dark:focus:ring-lia-border-strong dark:focus:border-lia-border-medium transition-colors motion-reduce:transition-none"
              placeholder={t('formNamePlaceholder')}
            />
          </div>
          <div>
            <label className="block text-micro font-medium text-lia-text-secondary mb-1">
              {t('formManager')}
            </label>
            <input
              type="text"
              data-field="manager"
              data-testid="department-field-manager"
              value={newDepartment.manager}
              onChange={(e) =>
                setNewDepartment((prev) => ({ ...prev, manager: e.target.value }))
              }
              className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-primary focus:ring-2 focus:ring-lia-border-subtle focus:border-lia-border-medium dark:focus:ring-lia-border-strong dark:focus:border-lia-border-medium transition-colors motion-reduce:transition-none"
              placeholder={t('formManagerPlaceholder')}
            />
          </div>
        </div>
        <div className="grid grid-cols-3 gap-2">
          <div>
            <label className="block text-micro font-medium text-lia-text-secondary mb-1">
              {t('formManagerTitle')}
            </label>
            <input
              type="text"
              data-field="manager_title"
              data-testid="department-field-manager-title"
              value={newDepartment.manager_title}
              onChange={(e) =>
                setNewDepartment((prev) => ({ ...prev, manager_title: e.target.value }))
              }
              className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-primary focus:ring-2 focus:ring-lia-border-subtle focus:border-lia-border-medium dark:focus:ring-lia-border-strong dark:focus:border-lia-border-medium transition-colors motion-reduce:transition-none"
              placeholder={t('formManagerTitlePlaceholder')}
            />
          </div>
          <div>
            <label className="block text-micro font-medium text-lia-text-secondary mb-1">
              {t('formManagerEmail')}
            </label>
            <input
              type="email"
              data-field="manager_email"
              data-testid="department-field-manager-email"
              value={newDepartment.manager_email}
              onChange={(e) =>
                setNewDepartment((prev) => ({ ...prev, manager_email: e.target.value }))
              }
              className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-primary focus:ring-2 focus:ring-lia-border-subtle focus:border-lia-border-medium dark:focus:ring-lia-border-strong dark:focus:border-lia-border-medium transition-colors motion-reduce:transition-none"
              placeholder={t('formManagerEmailPlaceholder')}
            />
          </div>
          <div>
            <label className="block text-micro font-medium text-lia-text-secondary mb-1">
              {t('formManagerPhone')}
            </label>
            <input
              type="text"
              data-field="manager_phone"
              data-testid="department-field-manager-phone"
              value={newDepartment.manager_phone}
              onChange={(e) =>
                setNewDepartment((prev) => ({ ...prev, manager_phone: e.target.value }))
              }
              className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-primary focus:ring-2 focus:ring-lia-border-subtle focus:border-lia-border-medium dark:focus:ring-lia-border-strong dark:focus:border-lia-border-medium transition-colors motion-reduce:transition-none"
              placeholder={t('formManagerPhonePlaceholder')}
            />
          </div>
        </div>
        <div>
          <label className="block text-micro font-medium text-lia-text-secondary mb-1">
            {t('formDescription')}
          </label>
          <textarea
            data-field="description"
            data-testid="department-field-description"
            value={newDepartment.description}
            onChange={(e) =>
              setNewDepartment((prev) => ({ ...prev, description: e.target.value }))
            }
            className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-primary focus:ring-2 focus:ring-lia-border-subtle focus:border-lia-border-medium dark:focus:ring-lia-border-strong dark:focus:border-lia-border-medium transition-colors motion-reduce:transition-none"
            rows={2}
            placeholder={t('formDescriptionPlaceholder')}
          />
        </div>
        <div>
          <label className="block text-micro font-medium text-lia-text-secondary mb-1">
            {t('formColor')}
          </label>
          <div className="flex gap-2" data-field="color" data-testid="department-field-color">
            {COLOR_OPTIONS.map((color) => (
              <button
                key={color}
                type="button"
                data-testid={`department-color-${color.split(' ')[0]}`}
                onClick={() =>
                  setNewDepartment((prev) => ({ ...prev, color }))
                }
                className={`w-4 h-4 rounded-full ${color.split(" ")[0]} ${newDepartment.color === color ? "ring-2 ring-offset-2 ring-lia-btn-primary-bg dark:ring-lia-border-subtle" : ""}`}
              />
            ))}
          </div>
        </div>

        {editingDepartment && (
          <MemberSection
            departmentMembers={departmentMembers}
            showMemberForm={showMemberForm}
            editingMember={editingMember}
            savingMember={savingMember}
            memberError={memberError}
            memberSuccess={memberSuccess}
            newMember={newMember}
            isEditingDepartments={isEditingDepartments}
            setShowMemberForm={setShowMemberForm}
            setEditingMember={setEditingMember}
            setNewMember={setNewMember}
            setMemberError={setMemberError}
            handleSaveMember={handleSaveMember}
            handleEditMember={handleEditMember}
            handleDeleteMember={handleDeleteMember}
            existingUsers={existingUsers}
          />
        )}

        <div className="flex justify-end gap-2">
          <Button
            data-testid="department-form-cancel"
            variant="ghost"
            size="sm"
            onClick={handleCancelDepartmentForm}
            className="py-1.5 px-2 text-xs rounded-full"
          >
            {t('cancel')}
          </Button>
          <Button
            data-testid="department-form-save"
            size="sm"
            onClick={handleSaveDepartment}
            className="py-1.5 px-2 text-xs rounded-full bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
          >
            <Save className="w-3.5 h-3.5 mr-1" />
            {editingDepartment ? t("formUpdate") : t("formSave")}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
