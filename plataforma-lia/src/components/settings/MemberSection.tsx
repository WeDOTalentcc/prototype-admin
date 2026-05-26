"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Plus,
  Edit,
  Trash2,
  CheckCircle,
  AlertCircle,
  Loader2,
} from "lucide-react";
import {
  type DepartmentMember,
  type NewMemberForm,
  DEFAULT_NEW_MEMBER,
} from '@/hooks/settings/department-types';
import { useTranslations } from "next-intl";

/**
 * B1 (2026-05-25): platform user option for "Vincular usuário existente" selector.
 * Lifted from useUserManagement.users at UsuariosDepartamentosHub level.
 */
export interface ExistingUserOption {
  id: string;
  name: string;
  email: string;
  title?: string;
}

export interface MemberSectionProps {
  departmentMembers: DepartmentMember[];
  showMemberForm: boolean;
  editingMember: DepartmentMember | null;
  savingMember: boolean;
  memberError: string | null;
  memberSuccess: string | null;
  newMember: NewMemberForm;
  isEditingDepartments: boolean;
  setShowMemberForm: (show: boolean) => void;
  setEditingMember: (member: DepartmentMember | null) => void;
  setNewMember: React.Dispatch<React.SetStateAction<NewMemberForm>>;
  setMemberError: (error: string | null) => void;
  handleSaveMember: () => Promise<void>;
  handleEditMember: (member: DepartmentMember) => void;
  handleDeleteMember: (memberId: string) => Promise<void>;
  // B1 (2026-05-25): existing platform users for explicit linkage
  existingUsers?: ExistingUserOption[];
}

export function MemberSection({
  departmentMembers,
  showMemberForm,
  editingMember,
  savingMember,
  memberError,
  memberSuccess,
  newMember,
  isEditingDepartments,
  setShowMemberForm,
  setEditingMember,
  setNewMember,
  existingUsers = [],
  setMemberError,
  handleSaveMember,
  handleEditMember,
  handleDeleteMember,
}: MemberSectionProps) {
  const t = useTranslations('settings.members');
  const td = useTranslations('settings.departments');

  return (
    <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-3 mt-3" data-testid="member-section-root">
      <div className="flex items-center justify-between mb-2">
        <h5 className="text-xs font-semibold text-lia-text-primary">
          {t('title')}
        </h5>
        <Button
          data-testid="member-add-button"
          variant="outline"
          size="sm"
          onClick={() => {
            setShowMemberForm(true);
            setEditingMember(null);
            setNewMember({ ...DEFAULT_NEW_MEMBER });
          }}
          disabled={!isEditingDepartments}
          className={`py-1 px-2 text-micro rounded-full border-lia-border-subtle dark:border-lia-border-subtle text-lia-text-primary hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse ${!isEditingDepartments ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          <Plus className="w-3 h-3 mr-1" />
          {t('add')}
        </Button>
      </div>

      <div className="space-y-2 max-h-chart-sm overflow-y-auto">
        {departmentMembers.length === 0 ? (
          <p className="text-micro text-lia-text-secondary text-center py-3">
            {t('noMembers')}
          </p>
        ) : (
          departmentMembers.map((member) => (
            <div
              key={member.id}
              data-testid={`member-row-${member.id}`}
              className="flex items-center justify-between p-2 bg-lia-bg-secondary rounded-xl"
            >
              <div className="flex items-center gap-2">
                <Avatar className="w-7 h-7">
                  <AvatarFallback className="text-micro bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-primary">
                    {member.name.charAt(0).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <p className="text-xs font-medium text-lia-text-primary">
                    {member.name}
                  </p>
                  <p className="text-micro text-lia-text-secondary">
                    {member.title || td("noTitle")} • {member.level}
                  </p>
                </div>
              </div>
              {isEditingDepartments && (
                <div className="flex gap-1">
                  <Button
                    data-testid={`member-edit-${member.id}`}
                    variant="ghost"
                    size="sm"
                    onClick={() => handleEditMember(member)}
                    className="h-6 w-6 p-0 rounded-md hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
                  >
                    <Edit className="w-3 h-3" />
                  </Button>
                  <Button
                    data-testid={`member-delete-${member.id}`}
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeleteMember(member.id)}
                    className="h-6 w-6 p-0 rounded-md text-status-error hover:text-status-error hover:bg-status-error/10"
                  >
                    <Trash2 className="w-3 h-3" />
                  </Button>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {showMemberForm && (
        <div data-testid={editingMember ? 'member-edit-form' : 'member-create-form'} className="mt-2 p-2 border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary">
          <h6 className="text-micro font-medium text-lia-text-secondary mb-2">
            {editingMember ? t("editMember") : t("newMember")}
          </h6>

          {/* B1 (2026-05-25): "Vincular usuário existente" selector.
              When admin picks a platform user → auto-fill name/email/title + set user_id.
              When left as "Contato externo" → user_id stays null. */}
          {!editingMember && existingUsers.length > 0 && (
            <div className="mb-2 p-2 rounded-xl bg-lia-bg-secondary dark:bg-lia-bg-inverse border border-lia-border-subtle">
              <label className="block text-micro font-medium text-lia-text-secondary mb-1">
                Vincular a usuário existente da plataforma (opcional)
              </label>
              <select
                data-testid="member-field-user-link"
                value={newMember.user_id ?? ""}
                onChange={(e) => {
                  const uid = e.target.value || null;
                  if (uid) {
                    const u = existingUsers.find((x) => x.id === uid);
                    if (u) {
                      setNewMember((prev) => ({
                        ...prev,
                        user_id: u.id,
                        name: u.name,
                        email: u.email,
                        title: u.title || prev.title,
                      }));
                      return;
                    }
                  }
                  setNewMember((prev) => ({ ...prev, user_id: null }));
                }}
                className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-primary"
              >
                <option value="">— Contato externo (sem login) —</option>
                {existingUsers.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.name} ({u.email})
                  </option>
                ))}
              </select>
              {newMember.user_id && (
                <p className="text-micro text-status-success mt-1">
                  Vinculado a usuário da plataforma. Editar dados abaixo refletirá no cadastro do colaborador, não no usuário canônico.
                </p>
              )}
            </div>
          )}

          <div className="grid grid-cols-2 gap-2 mb-2">
            <input
              type="text"
              data-field="name"
              data-testid="member-field-name"
              placeholder={t('namePlaceholder')}
              value={newMember.name}
              onChange={(e) =>
                setNewMember((prev) => ({ ...prev, name: e.target.value }))
              }
              className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-primary focus:ring-2 focus:ring-lia-border-subtle focus:border-lia-border-medium dark:focus:ring-lia-border-strong dark:focus:border-lia-border-medium transition-colors motion-reduce:transition-none"
            />
            <input
              type="text"
              data-field="title"
              data-testid="member-field-title"
              placeholder={t('titlePlaceholder')}
              value={newMember.title}
              onChange={(e) =>
                setNewMember((prev) => ({ ...prev, title: e.target.value }))
              }
              className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-primary focus:ring-2 focus:ring-lia-border-subtle focus:border-lia-border-medium dark:focus:ring-lia-border-strong dark:focus:border-lia-border-medium transition-colors motion-reduce:transition-none"
            />
            <input
              type="email"
              data-field="email"
              data-testid="member-field-email"
              placeholder={t('emailPlaceholder')}
              value={newMember.email}
              onChange={(e) =>
                setNewMember((prev) => ({ ...prev, email: e.target.value }))
              }
              className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-primary focus:ring-2 focus:ring-lia-border-subtle focus:border-lia-border-medium dark:focus:ring-lia-border-strong dark:focus:border-lia-border-medium transition-colors motion-reduce:transition-none"
            />
            <input
              type="text"
              data-field="phone"
              data-testid="member-field-phone"
              placeholder={t('phonePlaceholder')}
              value={newMember.phone}
              onChange={(e) =>
                setNewMember((prev) => ({ ...prev, phone: e.target.value }))
              }
              className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-primary focus:ring-2 focus:ring-lia-border-subtle focus:border-lia-border-medium dark:focus:ring-lia-border-strong dark:focus:border-lia-border-medium transition-colors motion-reduce:transition-none"
            />
            <input
              type="url"
              data-field="linkedin_url"
              data-testid="member-field-linkedin"
              placeholder={t('linkedinPlaceholder')}
              value={newMember.linkedin_url}
              onChange={(e) =>
                setNewMember((prev) => ({ ...prev, linkedin_url: e.target.value }))
              }
              className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-primary focus:ring-2 focus:ring-lia-border-subtle focus:border-lia-border-medium dark:focus:ring-lia-border-strong dark:focus:border-lia-border-medium col-span-2"
            />
            <select
              data-field="level"
              data-testid="member-field-level"
              value={newMember.level}
              onChange={(e) =>
                setNewMember((prev) => ({ ...prev, level: e.target.value }))
              }
              className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-primary focus:ring-2 focus:ring-lia-border-subtle focus:border-lia-border-medium dark:focus:ring-lia-border-strong dark:focus:border-lia-border-medium transition-colors motion-reduce:transition-none col-span-2"
            >
              <option value="ceo">{t('levelCeo')}</option>
              <option value="vp">{t('levelVp')}</option>
              <option value="diretor">{t('levelDirector')}</option>
              <option value="gerente_senior">{t('levelSeniorManager')}</option>
              <option value="gerente">{t('levelManager')}</option>
              <option value="lider">{t('levelLead')}</option>
              <option value="supervisor">{t('levelSupervisor')}</option>
              <option value="especialista">{t('levelSpecialist')}</option>
              <option value="analista">{t('levelAnalyst')}</option>
              <option value="estagiario">{t('levelIntern')}</option>
              <option value="outros">{t('levelOther')}</option>
            </select>
          </div>
          {memberError && (
            <div className="bg-status-error/10 border border-status-error/30 rounded-xl p-2 flex items-center gap-2 text-status-error text-micro">
              <AlertCircle className="w-3 h-3" />
              {memberError}
            </div>
          )}
          {memberSuccess && (
            <div className="bg-status-success/10 border border-status-success/30 rounded-xl p-2 flex items-center gap-2 text-status-success text-micro">
              <CheckCircle className="w-3 h-3" />
              {memberSuccess}
            </div>
          )}
          <div className="flex justify-end gap-2">
            <Button
              data-testid="member-form-cancel"
              variant="ghost"
              size="sm"
              onClick={() => {
                setShowMemberForm(false);
                setEditingMember(null);
                setNewMember({ ...DEFAULT_NEW_MEMBER });
                setMemberError(null);
              }}
              className="py-1 px-2 text-micro rounded-full"
              disabled={savingMember}
            >
              {t('cancel')}
            </Button>
            <Button
              data-testid="member-form-save"
              size="sm"
              onClick={handleSaveMember}
              className="py-1 px-2 text-micro rounded-full bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active"
              disabled={savingMember}
            >
              {savingMember ? (
                <>
                  <Loader2 className="w-3 h-3 mr-1 animate-spin motion-reduce:animate-none" />
                  {t('saving')}
                </>
              ) : (
                t('save')
              )}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
