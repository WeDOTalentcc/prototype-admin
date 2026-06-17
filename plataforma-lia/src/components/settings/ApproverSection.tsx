"use client";

import React from "react";
import { Chip } from "@/components/ui/chip";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Plus,
  Edit,
  Trash2,
  Save,
  CheckCircle,
  AlertCircle,
  Crown,
} from "lucide-react";
import {
  type Approver,
  type NewApproverForm,
} from "@/hooks/settings/department-types";
import { useTranslations } from "next-intl";

export interface ApproverSectionProps {
  approvers: Approver[];
  showApproverForm: boolean;
  editingApprover: Approver | null;
  newApprover: NewApproverForm;
  successMessage: string | null;
  error: string | null;
  setShowApproverForm: (show: boolean) => void;
  setEditingApprover: (approver: Approver | null) => void;
  setNewApprover: React.Dispatch<React.SetStateAction<NewApproverForm>>;
  handleSaveApprover: () => Promise<void>;
  handleDeleteApprover: (id: string) => Promise<void>;
  // P0.D2 (audit Wave 2 2026-05-22): optional list of departments for the
  // per-department routing dropdown. When empty/undefined the field falls
  // back to a text input (UUID string), keeping the component standalone-usable.
  departments?: Array<{ id: string; name: string }>;
}

export const ApproverSection = React.memo(function ApproverSection({
  approvers,
  showApproverForm,
  editingApprover,
  newApprover,
  successMessage,
  error,
  setShowApproverForm,
  setEditingApprover,
  setNewApprover,
  handleSaveApprover,
  handleDeleteApprover,
  departments,
}: ApproverSectionProps) {
  const t = useTranslations('settings.approvers');

  return (
    <div className="space-y-3" data-testid="approver-section-root">
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

      <Card className="border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-lia-bg-primary/80 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-xl">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base-ui font-semibold flex items-center gap-2">
                <Crown className="w-3.5 h-3.5 text-lia-text-secondary" />
                {t('title')}
              </CardTitle>
              <p className="text-xs text-lia-text-secondary mt-1" aria-live="polite" aria-atomic="true">
                {t('description')}
              </p>
            </div>
            <Button
              data-testid="approver-add-button"
              size="sm"
              variant="outline"
              className="gap-1.5 py-1.5 px-2 text-xs rounded-full border-lia-border-subtle dark:border-lia-border-subtle text-lia-text-primary hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
              onClick={() => {
                setNewApprover({
                  userName: "",
                  email: "",
                  role: "",
                  level: approvers.length + 1,
                  departmentId: null,
                  canApproveAboveAmount: null,
                });
                setShowApproverForm(true);
              }}
            >
              <Plus className="w-3.5 h-3.5" />
              {t('addLevel')}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-3 space-y-3">
          {(showApproverForm || editingApprover) && (
            <Card data-testid={editingApprover ? 'approver-edit-form' : 'approver-create-form'} className="border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 rounded-xl mb-3">
              <CardContent className="p-3 space-y-2">
                <h4 className="text-xs font-semibold">
                  {editingApprover ? t("editApprover") : t("newApprover")}
                </h4>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-micro font-medium text-lia-text-secondary mb-1">
                      {t('name')}
                    </label>
                    <input
                      type="text"
                      data-field="userName"
                      data-testid="approver-field-username"
                      className="w-full px-2 py-1.5 rounded-full border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-xs"
                      placeholder={t('namePlaceholder')}
                      value={editingApprover ? editingApprover.userName : newApprover.userName}
                      onChange={(e) =>
                        editingApprover
                          ? setEditingApprover({ ...editingApprover, userName: e.target.value })
                          : setNewApprover((prev) => ({ ...prev, userName: e.target.value }))
                      }
                    />
                  </div>
                  <div>
                    <label className="block text-micro font-medium text-lia-text-secondary mb-1">
                      {t('email')}
                    </label>
                    <input
                      type="email"
                      data-field="email"
                      data-testid="approver-field-email"
                      className="w-full px-2 py-1.5 rounded-full border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-xs"
                      placeholder={t('emailPlaceholder')}
                      value={editingApprover ? editingApprover.email : newApprover.email}
                      onChange={(e) =>
                        editingApprover
                          ? setEditingApprover({ ...editingApprover, email: e.target.value })
                          : setNewApprover((prev) => ({ ...prev, email: e.target.value }))
                      }
                    />
                  </div>
                  <div>
                    <label className="block text-micro font-medium text-lia-text-secondary mb-1">
                      {t('role')}
                    </label>
                    <input
                      type="text"
                      data-field="role"
                      data-testid="approver-field-role"
                      className="w-full px-2 py-1.5 rounded-full border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-xs"
                      placeholder={t('rolePlaceholder')}
                      value={editingApprover ? editingApprover.role : newApprover.role}
                      onChange={(e) =>
                        editingApprover
                          ? setEditingApprover({ ...editingApprover, role: e.target.value })
                          : setNewApprover((prev) => ({ ...prev, role: e.target.value }))
                      }
                    />
                  </div>
                  <div>
                    <label className="block text-micro font-medium text-lia-text-secondary mb-1">
                      {t('approvalLevel')}
                    </label>
                    <input
                      type="number"
                      min="1"
                      data-field="level"
                      data-testid="approver-field-level"
                      className="w-full px-2 py-1.5 rounded-full border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-xs"
                      value={editingApprover ? editingApprover.level : newApprover.level}
                      onChange={(e) =>
                        editingApprover
                          ? setEditingApprover({ ...editingApprover, level: parseInt(e.target.value) || 1 })
                          : setNewApprover((prev) => ({ ...prev, level: parseInt(e.target.value) || 1 }))
                      }
                    />
                  </div>
                  {/* P0.D2 (audit Wave 2 2026-05-22): per-department routing */}
                  <div>
                    <label className="block text-micro font-medium text-lia-text-secondary mb-1">
                      Departamento (opcional)
                    </label>
                    {departments && departments.length > 0 ? (
                      <select
                        data-field="approver-department-id"
                        data-testid="approver-field-department-id"
                        className="w-full px-2 py-1.5 rounded-full border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-xs"
                        value={
                          (editingApprover
                            ? editingApprover.departmentId
                            : newApprover.departmentId) || ""
                        }
                        onChange={(e) => {
                          const val = e.target.value || null;
                          if (editingApprover) {
                            setEditingApprover({ ...editingApprover, departmentId: val })
                          } else {
                            setNewApprover((prev) => ({ ...prev, departmentId: val }))
                          }
                        }}
                      >
                        <option value="">Empresa toda</option>
                        {departments.map((d) => (
                          <option key={d.id} value={d.id}>{d.name}</option>
                        ))}
                      </select>
                    ) : (
                      <input
                        type="text"
                        data-field="approver-department-id"
                        data-testid="approver-field-department-id"
                        className="w-full px-2 py-1.5 rounded-full border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-xs"
                        placeholder="Empresa toda (deixe em branco)"
                        value={
                          (editingApprover
                            ? editingApprover.departmentId
                            : newApprover.departmentId) || ""
                        }
                        onChange={(e) => {
                          const val = e.target.value || null;
                          if (editingApprover) {
                            setEditingApprover({ ...editingApprover, departmentId: val })
                          } else {
                            setNewApprover((prev) => ({ ...prev, departmentId: val }))
                          }
                        }}
                      />
                    )}
                  </div>
                  {/* P0.D2: amount-threshold routing */}
                  <div>
                    <label className="block text-micro font-medium text-lia-text-secondary mb-1">
                      Limite de aprovacao (R$, opcional)
                    </label>
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      data-field="approver-can-approve-above-amount"
                      data-testid="approver-field-can-approve-above-amount"
                      className="w-full px-2 py-1.5 rounded-full border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-xs"
                      placeholder="Qualquer valor"
                      value={
                        (editingApprover
                          ? editingApprover.canApproveAboveAmount
                          : newApprover.canApproveAboveAmount) ?? ""
                      }
                      onChange={(e) => {
                        const raw = e.target.value;
                        const val = raw === "" ? null : parseFloat(raw);
                        if (editingApprover) {
                          setEditingApprover({ ...editingApprover, canApproveAboveAmount: val })
                        } else {
                          setNewApprover((prev) => ({ ...prev, canApproveAboveAmount: val }))
                        }
                      }}
                    />
                  </div>
                </div>
                <div className="flex justify-end gap-2">
                  <Button
                    data-testid="approver-form-cancel"
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setShowApproverForm(false);
                      setEditingApprover(null);
                    }}
                    className="py-1.5 px-2 text-xs rounded-full"
                  >
                    {t('cancel')}
                  </Button>
                  <Button
                    data-testid="approver-form-save"
                    size="sm"
                    onClick={handleSaveApprover}
                    className="py-1.5 px-2 text-xs rounded-full bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
                  >
                    <Save className="w-3.5 h-3.5 mr-1" />
                    {t('save')}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {approvers.length === 0 && !showApproverForm ? (
            <div className="text-center py-6 text-lia-text-secondary">
              <Crown className="w-10 h-10 mx-auto mb-2 opacity-30" />
              <p className="text-xs">
                {t('noApprovers')}
              </p>
              <p className="text-micro mt-1">
                {t('noApproversHint')}
              </p>
            </div>
          ) : (
            <div className="relative">
              <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-lia-interactive-active dark:bg-lia-bg-elevated" />
              {approvers
                .sort((a, b) => a.level - b.level)
                .map((approver) => (
                  <div
                    key={approver.id}
                    data-testid={`approver-row-${approver.id}`}
                    className="relative flex items-center gap-3 pb-4 last:pb-0"
                  >
                    <div
                      
                    >
                      {approver.level}
                    </div>
                    <Card className="flex-1 border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-lia-bg-primary/80 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-xl">
                      <CardContent className="p-2 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Avatar className="h-8 w-8">
                            <AvatarFallback className="bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-primary text-micro">
                              {approver.userName
                                .split("")
                                .map((n) => n[0])
                                .join("")}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <p className="text-xs font-semibold text-lia-text-primary">
                              {approver.userName}
                            </p>
                            <p className="text-micro text-lia-text-secondary">
                              {approver.role} • {approver.email}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-1">
                          <Chip
                            variant="neutral"
                            muted={!approver.isActive}
                          >
                            {approver.isActive ? t("active") : t("inactive")}
                          </Chip>
                          <Button
                            data-testid={`approver-edit-${approver.id}`}
                            variant="ghost"
                            size="sm"
                            className="h-7 w-7 p-0 rounded-xl hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
                            onClick={() => setEditingApprover(approver)}
                          >
                            <Edit className="w-3.5 h-3.5" />
                          </Button>
                          <Button
                            data-testid={`approver-delete-${approver.id}`}
                            variant="ghost"
                            size="sm"
                            className="h-7 w-7 p-0 rounded-md text-status-error hover:text-status-error hover:bg-status-error/10"
                            onClick={() => handleDeleteApprover(approver.id)}
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                ))}
            </div>
          )}

          <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 rounded-xl p-2 border border-lia-border-subtle dark:border-lia-border-subtle">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-lia-text-secondary" />
              <div>
                <p className="text-xs font-semibold text-lia-text-primary">
                  {t('flowTitle')}
                </p>
                <p className="text-micro mt-0.5 text-lia-text-secondary" aria-live="polite" aria-atomic="true">
                  {t('flowDescription')}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
});
