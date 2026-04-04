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
} from './companyTeamHub.types';

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
  setMemberError,
  handleSaveMember,
  handleEditMember,
  handleDeleteMember,
}: MemberSectionProps) {
  return (
    <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-3 mt-3">
      <div className="flex items-center justify-between mb-2">
        <h5 className="text-xs font-semibold text-lia-text-primary">
          Colaboradores do Departamento
        </h5>
        <Button
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
          Adicionar
        </Button>
      </div>

      <div className="space-y-2 max-h-chart-sm overflow-y-auto">
        {departmentMembers.length === 0 ? (
          <p className="text-micro text-lia-text-secondary text-center py-3">
            Nenhum colaborador cadastrado
          </p>
        ) : (
          departmentMembers.map((member) => (
            <div
              key={member.id}
              className="flex items-center justify-between p-2 bg-lia-bg-secondary rounded-md"
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
                    {member.title || "Sem cargo"} • {member.level}
                  </p>
                </div>
              </div>
              {isEditingDepartments && (
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleEditMember(member)}
                    className="h-6 w-6 p-0 rounded-md hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
                  >
                    <Edit className="w-3 h-3" />
                  </Button>
                  <Button
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
        <div className="mt-2 p-2 border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-lia-bg-primary dark:bg-lia-bg-secondary">
          <h6 className="text-micro font-medium text-lia-text-secondary mb-2">
            {editingMember ? "Editar Colaborador" : "Novo Colaborador"}
          </h6>
          <div className="grid grid-cols-2 gap-2 mb-2">
            <input
              type="text"
              placeholder="Nome"
              value={newMember.name}
              onChange={(e) =>
                setNewMember((prev) => ({ ...prev, name: e.target.value }))
              }
              className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:ring-lia-border-subtle focus:border-lia-border-medium dark:focus:ring-lia-border-strong dark:focus:border-lia-border-medium transition-colors motion-reduce:transition-none"
            />
            <input
              type="text"
              placeholder="Cargo"
              value={newMember.title}
              onChange={(e) =>
                setNewMember((prev) => ({ ...prev, title: e.target.value }))
              }
              className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:ring-lia-border-subtle focus:border-lia-border-medium dark:focus:ring-lia-border-strong dark:focus:border-lia-border-medium transition-colors motion-reduce:transition-none"
            />
            <input
              type="email"
              placeholder="Email"
              value={newMember.email}
              onChange={(e) =>
                setNewMember((prev) => ({ ...prev, email: e.target.value }))
              }
              className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:ring-lia-border-subtle focus:border-lia-border-medium dark:focus:ring-lia-border-strong dark:focus:border-lia-border-medium transition-colors motion-reduce:transition-none"
            />
            <input
              type="text"
              placeholder="Telefone"
              value={newMember.phone}
              onChange={(e) =>
                setNewMember((prev) => ({ ...prev, phone: e.target.value }))
              }
              className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:ring-lia-border-subtle focus:border-lia-border-medium dark:focus:ring-lia-border-strong dark:focus:border-lia-border-medium transition-colors motion-reduce:transition-none"
            />
            <input
              type="url"
              placeholder="LinkedIn URL"
              value={newMember.linkedin_url}
              onChange={(e) =>
                setNewMember((prev) => ({ ...prev, linkedin_url: e.target.value }))
              }
              className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:ring-lia-border-subtle focus:border-lia-border-medium dark:focus:ring-lia-border-strong dark:focus:border-lia-border-medium col-span-2"
            />
            <select
              value={newMember.level}
              onChange={(e) =>
                setNewMember((prev) => ({ ...prev, level: e.target.value }))
              }
              className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:ring-lia-border-subtle focus:border-lia-border-medium dark:focus:ring-lia-border-strong dark:focus:border-lia-border-medium transition-colors motion-reduce:transition-none col-span-2"
            >
              <option value="ceo">CEO</option>
              <option value="vp">VP</option>
              <option value="diretor">Diretor</option>
              <option value="gerente_senior">Gerente Sênior</option>
              <option value="gerente">Gerente</option>
              <option value="lider">Líder</option>
              <option value="supervisor">Supervisor</option>
              <option value="especialista">Especialista</option>
              <option value="analista">Analista</option>
              <option value="estagiario">Estagiário</option>
              <option value="outros">Outros</option>
            </select>
          </div>
          {memberError && (
            <div className="bg-status-error/10 border border-status-error/30 rounded-md p-2 flex items-center gap-2 text-status-error text-micro">
              <AlertCircle className="w-3 h-3" />
              {memberError}
            </div>
          )}
          {memberSuccess && (
            <div className="bg-status-success/10 border border-status-success/30 rounded-md p-2 flex items-center gap-2 text-status-success text-micro">
              <CheckCircle className="w-3 h-3" />
              {memberSuccess}
            </div>
          )}
          <div className="flex justify-end gap-2">
            <Button
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
              Cancelar
            </Button>
            <Button
              size="sm"
              onClick={handleSaveMember}
              className="py-1 px-2 text-micro rounded-full bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active"
              disabled={savingMember}
            >
              {savingMember ? (
                <>
                  <Loader2 className="w-3 h-3 mr-1 animate-spin motion-reduce:animate-none" />
                  Salvando...
                </>
              ) : (
                "Salvar"
              )}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
