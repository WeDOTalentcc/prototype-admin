"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Users,
  Network,
  Plus,
  Edit,
  Trash2,
  Save,
  CheckCircle,
  AlertCircle,
  Crown,
  Building2,
  Loader2,
  X,
  Maximize2,
  Linkedin,
} from "lucide-react";
import { LiaFieldToggle, defaultLiaFieldExamples } from './LiaFieldToggle';
import { SmartImportZone } from "./SmartImportZone";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  type Department,
  type DepartmentMember,
  type Approver,
  type CompanyData,
  type NewDepartmentForm,
  type NewMemberForm,
  type NewApproverForm,
  COLOR_OPTIONS,
  DEFAULT_NEW_MEMBER,
  getLevelOrder,
  getLevelLabel,
  getLevelColor,
} from './companyTeamHub.types';
import { textStyles, actionButtonStyles } from "@/lib/design-tokens";

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
}: DepartmentsTabProps) {
  return (
    <>
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="flex items-center gap-2 text-base-ui font-semibold lia-text-950 dark:lia-text-50">
              Departamentos
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
            <p className="text-xs lia-text-600">
              Gerencie a estrutura organizacional da empresa
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
              >
                <Edit className={actionButtonStyles.icon} />
                Editar
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
                >
                  Cancelar
                </button>
                <button
                  onClick={async () => {
                    setIsEditingDepartments(false);
                    setDepartmentsBackup([]);
                  }}
                  disabled={saving}
                  className={actionButtonStyles.smPrimary}
                >
                  {saving ? (
                    <>
                      <Loader2 className={`${actionButtonStyles.icon} animate-spin motion-reduce:animate-none`} />
                      Salvando...
                    </>
                  ) : (
                    <>
                      <Save className={actionButtonStyles.icon} />
                      Salvar Alterações
                    </>
                  )}
                </button>
                <Button
                  onClick={() => setShowDepartmentForm(true)}
                  size="sm"
                  className="gap-1.5 py-1.5 px-2 text-xs rounded-full bg-gray-900 hover:bg-gray-800 text-white dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200"
                >
                  <Plus className="w-3.5 h-3.5" />
                  Novo Departamento
                </Button>
              </>
            )}
          </div>
        </div>

        <SmartImportZone
          title="Importar Departamentos"
          description="Arraste uma planilha Excel ou CSV com o organograma da empresa. A LIA vai identificar automaticamente os departamentos, gestores e hierarquias."
          importEndpoint="/api/backend-proxy/company/departments/import"
          templateDownloadEndpoint="/api/backend-proxy/company/departments/import/template"
          expectedFields={[
            "name",
            "description",
            "manager",
            "manager_email",
            "parent_department",
            "headcount",
            "cost_center",
            "order",
          ]}
          onImportSuccess={() => {
            loadDepartments();
          }}
          disabled={!isEditingDepartments}
        />

        {showDepartmentForm && isEditingDepartments && (
          <Card className="border border-lia-border-subtle dark:border-lia-border-subtle bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md">
            <CardContent className="p-3 space-y-2">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-xs font-semibold lia-text-950 dark:lia-text-50">
                  {editingDepartment ? "Editar Departamento" : "Novo Departamento"}
                </h4>
                <Button
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
                  <label className="block text-micro font-medium lia-text-600 dark:text-lia-text-tertiary mb-1">
                    Nome
                  </label>
                  <input
                    type="text"
                    value={newDepartment.name}
                    onChange={(e) =>
                      setNewDepartment((prev) => ({ ...prev, name: e.target.value }))
                    }
                    className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors motion-reduce:transition-none"
                    placeholder="Ex: Engenharia"
                  />
                </div>
                <div>
                  <label className="block text-micro font-medium lia-text-600 dark:text-lia-text-tertiary mb-1">
                    Gestor
                  </label>
                  <input
                    type="text"
                    value={newDepartment.manager}
                    onChange={(e) =>
                      setNewDepartment((prev) => ({ ...prev, manager: e.target.value }))
                    }
                    className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors motion-reduce:transition-none"
                    placeholder="Nome do gestor"
                  />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="block text-micro font-medium lia-text-600 dark:text-lia-text-tertiary mb-1">
                    Cargo do Gestor
                  </label>
                  <input
                    type="text"
                    value={newDepartment.manager_title}
                    onChange={(e) =>
                      setNewDepartment((prev) => ({ ...prev, manager_title: e.target.value }))
                    }
                    className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors motion-reduce:transition-none"
                    placeholder="Ex: Diretor de Engenharia"
                  />
                </div>
                <div>
                  <label className="block text-micro font-medium lia-text-600 dark:text-lia-text-tertiary mb-1">
                    Email do Gestor
                  </label>
                  <input
                    type="email"
                    value={newDepartment.manager_email}
                    onChange={(e) =>
                      setNewDepartment((prev) => ({ ...prev, manager_email: e.target.value }))
                    }
                    className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors motion-reduce:transition-none"
                    placeholder="gestor@empresa.com"
                  />
                </div>
                <div>
                  <label className="block text-micro font-medium lia-text-600 dark:text-lia-text-tertiary mb-1">
                    Telefone/WhatsApp
                  </label>
                  <input
                    type="text"
                    value={newDepartment.manager_phone}
                    onChange={(e) =>
                      setNewDepartment((prev) => ({ ...prev, manager_phone: e.target.value }))
                    }
                    className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors motion-reduce:transition-none"
                    placeholder="+55 11 99999-0000"
                  />
                </div>
              </div>
              <div>
                <label className="block text-micro font-medium lia-text-600 dark:text-lia-text-tertiary mb-1">
                  Descrição
                </label>
                <textarea
                  value={newDepartment.description}
                  onChange={(e) =>
                    setNewDepartment((prev) => ({ ...prev, description: e.target.value }))
                  }
                  className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors motion-reduce:transition-none"
                  rows={2}
                  placeholder="Descrição do departamento"
                />
              </div>
              <div>
                <label className="block text-micro font-medium lia-text-600 dark:text-lia-text-tertiary mb-1">
                  Cor
                </label>
                <div className="flex gap-2">
                  {COLOR_OPTIONS.map((color) => (
                    <button
                      key={color}
                      type="button"
                      onClick={() =>
                        setNewDepartment((prev) => ({ ...prev, color }))
                      }
                      className={`w-4 h-4 rounded-full ${color.split(" ")[0]} ${newDepartment.color === color ? "ring-2 ring-offset-2 ring-gray-900 dark:lia-ring-50" : ""}`}
                    />
                  ))}
                </div>
              </div>

              {editingDepartment && (
                <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-3 mt-3">
                  <div className="flex items-center justify-between mb-2">
                    <h5 className="text-xs font-semibold lia-text-800 dark:text-lia-text-primary">
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
                      className={`py-1 px-2 text-micro rounded-full border-lia-border-subtle dark:border-lia-border-subtle lia-text-700 dark:text-lia-text-secondary hover:bg-gray-100 dark:hover:bg-gray-700 ${!isEditingDepartments ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      <Plus className="w-3 h-3 mr-1" />
                      Adicionar
                    </Button>
                  </div>

                  <div className="space-y-2 max-h-[200px] overflow-y-auto">
                    {departmentMembers.length === 0 ? (
                      <p className="text-micro lia-text-500 text-center py-3">
                        Nenhum colaborador cadastrado
                      </p>
                    ) : (
                      departmentMembers.map((member) => (
                        <div
                          key={member.id}
                          className="flex items-center justify-between p-2 bg-gray-50 rounded-md"
                        >
                          <div className="flex items-center gap-2">
                            <Avatar className="w-7 h-7">
                              <AvatarFallback className="text-micro bg-gray-100 dark:bg-lia-bg-elevated lia-text-700 dark:text-lia-text-secondary">
                                {member.name.charAt(0).toUpperCase()}
                              </AvatarFallback>
                            </Avatar>
                            <div>
                              <p className="text-xs font-medium lia-text-950 dark:lia-text-50">
                                {member.name}
                              </p>
                              <p className="text-micro lia-text-500">
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
                                className="h-6 w-6 p-0 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
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
                    <div className="mt-2 p-2 border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-white dark:bg-lia-bg-secondary">
                      <h6 className="text-micro font-medium lia-text-600 mb-2">
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
                          className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors motion-reduce:transition-none"
                        />
                        <input
                          type="text"
                          placeholder="Cargo"
                          value={newMember.title}
                          onChange={(e) =>
                            setNewMember((prev) => ({ ...prev, title: e.target.value }))
                          }
                          className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors motion-reduce:transition-none"
                        />
                        <input
                          type="email"
                          placeholder="Email"
                          value={newMember.email}
                          onChange={(e) =>
                            setNewMember((prev) => ({ ...prev, email: e.target.value }))
                          }
                          className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors motion-reduce:transition-none"
                        />
                        <input
                          type="text"
                          placeholder="Telefone"
                          value={newMember.phone}
                          onChange={(e) =>
                            setNewMember((prev) => ({ ...prev, phone: e.target.value }))
                          }
                          className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors motion-reduce:transition-none"
                        />
                        <input
                          type="url"
                          placeholder="LinkedIn URL"
                          value={newMember.linkedin_url}
                          onChange={(e) =>
                            setNewMember((prev) => ({ ...prev, linkedin_url: e.target.value }))
                          }
                          className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors motion-reduce:transition-none col-span-2"
                        />
                        <select
                          value={newMember.level}
                          onChange={(e) =>
                            setNewMember((prev) => ({ ...prev, level: e.target.value }))
                          }
                          className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors motion-reduce:transition-none col-span-2"
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
                          className="py-1 px-2 text-micro rounded-full bg-gray-900 text-white hover:bg-gray-800 dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200"
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
              )}

              <div className="flex justify-end gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCancelDepartmentForm}
                  className="py-1.5 px-2 text-xs rounded-full"
                >
                  Cancelar
                </Button>
                <Button
                  size="sm"
                  onClick={handleSaveDepartment}
                  className="py-1.5 px-2 text-xs rounded-full bg-gray-900 hover:bg-gray-800 text-white dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200"
                >
                  <Save className="w-3.5 h-3.5 mr-1" />
                  {editingDepartment ? "Atualizar" : "Salvar"}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {successMessage && (
          <div className="bg-status-success/10 border border-status-success/30 rounded-md p-2 flex items-center gap-2 text-status-success text-xs">
            <CheckCircle className="w-3.5 h-3.5" />
            {successMessage}
          </div>
        )}
        {error && (
          <div className="bg-status-error/10 border border-status-error/30 rounded-md p-2 flex items-center gap-2 text-status-error text-xs">
            <AlertCircle className="w-3.5 h-3.5" />
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {departments.length === 0 && !showDepartmentForm ? (
            <div className="col-span-2 text-center py-8 lia-text-600">
              <Network className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p className="text-xs font-medium lia-text-700 dark:text-lia-text-secondary">
                Nenhum departamento cadastrado
              </p>
              <p className="text-xs mt-1 lia-text-500 dark:lia-text-500">
                Clique em "Novo Departamento" ou importe uma planilha para começar
              </p>
            </div>
          ) : (
            departments.map((dept) => (
              <Card
                key={dept.id}
                className="border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-white/80 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-md hover:transition-shadow"
              >
                <CardContent className="p-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <div
                        className={`w-9 h-9 rounded-md ${dept.color} flex items-center justify-center`}
                      >
                        <Building2 className="w-4 h-4" />
                      </div>
                      <div>
                        <h4 className="text-xs font-semibold lia-text-950 dark:lia-text-50">
                          {dept.name}
                        </h4>
                        <p className="text-micro lia-text-600">
                          {dept.description}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
                        onClick={() => handleOpenOrgChart(dept)}
                        title="Ver organograma"
                      >
                        <Maximize2 className="w-3.5 h-3.5 lia-text-600 dark:text-lia-text-tertiary" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
                        onClick={() => handleStartEditDepartment(dept)}
                        disabled={!isEditingDepartments}
                      >
                        <Edit className="w-3.5 h-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0 rounded-md text-status-error hover:text-status-error hover:bg-status-error/10"
                        onClick={() => setDepartmentToDelete(dept)}
                        disabled={!isEditingDepartments}
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  </div>
                  <div className="mt-2 pt-2 border-t border-lia-border-subtle dark:lia-border-800 flex items-center justify-between">
                    <div className="flex items-center gap-2 text-micro lia-text-600">
                      <Users className="w-3 h-3" />
                      <span>{dept.headcount} colaboradores</span>
                    </div>
                    {dept.manager && (
                      <Badge
                        variant="outline"
                        className="text-micro rounded-md border-lia-border-subtle dark:border-lia-border-subtle lia-text-700 dark:text-lia-text-secondary"
                      >
                        {dept.manager}
                      </Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>

        <AlertDialog
          open={!!departmentToDelete}
          onOpenChange={() => setDepartmentToDelete(null)}
        >
          <AlertDialogContent className="rounded-md">
            <AlertDialogHeader>
              <AlertDialogTitle className="text-sm font-semibold lia-text-900 dark:lia-text-50">
                Excluir Departamento
              </AlertDialogTitle>
              <AlertDialogDescription>
                Tem certeza que deseja excluir o departamento "
                {departmentToDelete?.name}"? Esta ação não pode ser desfeita.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel className="rounded-md text-xs">
                Cancelar
              </AlertDialogCancel>
              <AlertDialogAction
                className="rounded-md text-xs bg-status-error hover:bg-status-error"
                onClick={() =>
                  departmentToDelete &&
                  handleDeleteDepartment(departmentToDelete.id)
                }
              >
                Excluir
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        <Dialog
          open={!!orgChartDepartment}
          onOpenChange={() => setOrgChartDepartment(null)}
        >
          <DialogContent className="rounded-md max-w-4xl max-h-[85vh] overflow-hidden">
            <DialogHeader>
              <div className="flex items-center gap-3">
                <div
                  className={`w-10 h-10 rounded-md ${orgChartDepartment?.color || "bg-gray-900 text-white"} flex items-center justify-center`}
                >
                  <Network className="w-5 h-5" />
                </div>
                <div>
                  <DialogTitle className="text-sm">
                    Organograma - {orgChartDepartment?.name}
                  </DialogTitle>
                  <p className={`${textStyles.description} mt-0.5`}>
                    {orgChartMembers.length} colaboradores cadastrados
                  </p>
                </div>
              </div>
            </DialogHeader>

            <div className="overflow-y-auto max-h-[60vh] mt-4" role="status" aria-live="polite" aria-label="Carregando...">
              {loadingOrgChart ? (
                <div className="flex items-center justify-center py-12" role="status" aria-live="polite" aria-label="Carregando...">
                  <Loader2 className="w-6 h-6 animate-spin motion-reduce:animate-none lia-text-500 dark:text-lia-text-tertiary" />
                </div>
              ) : orgChartMembers.length === 0 ? (
                <div className="text-center py-12">
                  <Users className="w-12 h-12 mx-auto mb-3 lia-text-300" />
                  <p className="text-xs font-medium lia-text-600">
                    Nenhum colaborador cadastrado
                  </p>
                  <p className={`${textStyles.description} mt-1`}>
                    Adicione colaboradores através da edição do departamento
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {Object.entries(
                    orgChartMembers
                      .sort(
                        (a, b) => getLevelOrder(a.level) - getLevelOrder(b.level),
                      )
                      .reduce(
                        (acc, member) => {
                          const level = member.level || "outros";
                          if (!acc[level]) acc[level] = [];
                          acc[level].push(member);
                          return acc;
                        },
                        {} as Record<string, DepartmentMember[]>,
                      ),
                  )
                    .sort(([a], [b]) => getLevelOrder(a) - getLevelOrder(b))
                    .map(([level, members]) => (
                      <div key={level} className="space-y-2">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge
                            className={`text-micro px-2 py-0.5 rounded-full border ${getLevelColor(level)}`}
                          >
                            {getLevelLabel(level)}
                          </Badge>
                          <div className="flex-1 h-px bg-gray-200"></div>
                          <span className="text-micro lia-text-400">
                            {members.length}{" "}
                            {members.length === 1 ? "pessoa" : "pessoas"}
                          </span>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                          {members.map((member) => (
                            <div
                              key={member.id}
                              className="flex items-center gap-3 p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md hover:transition-shadow"
                            >
                              <Avatar className="w-10 h-10">
                                {member.avatar_url ? (
                                  <img
                                    src={member.avatar_url}
                                    alt={member.name}
                                    className="w-full h-full object-cover rounded-full"
                                  />
                                ) : (
                                  <AvatarFallback className="text-xs bg-gray-100 dark:bg-lia-bg-elevated lia-text-700 dark:text-lia-text-secondary">
                                    {member.name
                                      .split(" ")
                                      .map((n) => n[0])
                                      .slice(0, 2)
                                      .join("")
                                      .toUpperCase()}
                                  </AvatarFallback>
                                )}
                              </Avatar>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-1.5">
                                  <p className="text-xs font-medium lia-text-950 dark:lia-text-50 truncate">
                                    {member.name}
                                  </p>
                                  {member.linkedin_url && (
                                    <a
                                      href={member.linkedin_url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-brand-linkedin hover:opacity-80 flex-shrink-0"
                                    >
                                      <Linkedin className="w-3 h-3" />
                                    </a>
                                  )}
                                </div>
                                <p className="text-micro lia-text-500 truncate">
                                  {member.title || "Sem cargo"}
                                </p>
                                {member.email && (
                                  <p className="text-micro lia-text-400 truncate">
                                    {member.email}
                                  </p>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>
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

interface ApproverSectionProps {
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
}

function ApproverSection({
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
}: ApproverSectionProps) {
  return (
    <div className="space-y-3">
      {successMessage && (
        <div className="bg-status-success/10 border border-status-success/30 rounded-md p-2 flex items-center gap-2 text-status-success text-xs">
          <CheckCircle className="w-3.5 h-3.5" />
          {successMessage}
        </div>
      )}
      {error && (
        <div className="bg-status-error/10 border border-status-error/30 rounded-md p-2 flex items-center gap-2 text-status-error text-xs">
          <AlertCircle className="w-3.5 h-3.5" />
          {error}
        </div>
      )}

      <Card className="border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-white/80 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-md">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base-ui font-semibold flex items-center gap-2">
                <Crown className="w-3.5 h-3.5 lia-text-500" />
                Fluxo de Aprovação de Vagas
              </CardTitle>
              <p className="text-xs lia-text-600 mt-1" aria-live="polite" aria-atomic="true">
                Configure os níveis de aprovação para abertura de vagas
              </p>
            </div>
            <Button
              size="sm"
              variant="outline"
              className="gap-1.5 py-1.5 px-2 text-xs rounded-full border-lia-border-subtle dark:border-lia-border-subtle lia-text-700 dark:text-lia-text-secondary hover:bg-gray-100 dark:hover:bg-gray-700"
              onClick={() => {
                setNewApprover({
                  userName: "",
                  email: "",
                  role: "",
                  level: approvers.length + 1,
                });
                setShowApproverForm(true);
              }}
            >
              <Plus className="w-3.5 h-3.5" />
              Adicionar Nível
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-3 space-y-3">
          {(showApproverForm || editingApprover) && (
            <Card className="border border-lia-border-subtle dark:border-lia-border-subtle bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md mb-3">
              <CardContent className="p-3 space-y-2">
                <h4 className="text-xs font-semibold">
                  {editingApprover ? "Editar Aprovador" : "Novo Aprovador"}
                </h4>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-micro font-medium lia-text-600 dark:text-lia-text-tertiary mb-1">
                      Nome
                    </label>
                    <input
                      type="text"
                      className="w-full px-2 py-1.5 rounded-full border border-lia-border-subtle dark:border-lia-border-subtle bg-white dark:bg-lia-bg-secondary text-xs dark:text-lia-text-primary"
                      placeholder="Nome do aprovador"
                      value={editingApprover ? editingApprover.userName : newApprover.userName}
                      onChange={(e) =>
                        editingApprover
                          ? setEditingApprover({ ...editingApprover, userName: e.target.value })
                          : setNewApprover((prev) => ({ ...prev, userName: e.target.value }))
                      }
                    />
                  </div>
                  <div>
                    <label className="block text-micro font-medium lia-text-600 dark:text-lia-text-tertiary mb-1">
                      Email
                    </label>
                    <input
                      type="email"
                      className="w-full px-2 py-1.5 rounded-full border border-lia-border-subtle dark:border-lia-border-subtle bg-white dark:bg-lia-bg-secondary text-xs dark:text-lia-text-primary"
                      placeholder="email@empresa.com"
                      value={editingApprover ? editingApprover.email : newApprover.email}
                      onChange={(e) =>
                        editingApprover
                          ? setEditingApprover({ ...editingApprover, email: e.target.value })
                          : setNewApprover((prev) => ({ ...prev, email: e.target.value }))
                      }
                    />
                  </div>
                  <div>
                    <label className="block text-micro font-medium lia-text-600 dark:text-lia-text-tertiary mb-1">
                      Cargo
                    </label>
                    <input
                      type="text"
                      className="w-full px-2 py-1.5 rounded-full border border-lia-border-subtle dark:border-lia-border-subtle bg-white dark:bg-lia-bg-secondary text-xs dark:text-lia-text-primary"
                      placeholder="Ex: Gerente de RH"
                      value={editingApprover ? editingApprover.role : newApprover.role}
                      onChange={(e) =>
                        editingApprover
                          ? setEditingApprover({ ...editingApprover, role: e.target.value })
                          : setNewApprover((prev) => ({ ...prev, role: e.target.value }))
                      }
                    />
                  </div>
                  <div>
                    <label className="block text-micro font-medium lia-text-600 dark:text-lia-text-tertiary mb-1">
                      Nível de Aprovação
                    </label>
                    <input
                      type="number"
                      min="1"
                      className="w-full px-2 py-1.5 rounded-full border border-lia-border-subtle dark:border-lia-border-subtle bg-white dark:bg-lia-bg-secondary text-xs dark:text-lia-text-primary"
                      value={editingApprover ? editingApprover.level : newApprover.level}
                      onChange={(e) =>
                        editingApprover
                          ? setEditingApprover({ ...editingApprover, level: parseInt(e.target.value) || 1 })
                          : setNewApprover((prev) => ({ ...prev, level: parseInt(e.target.value) || 1 }))
                      }
                    />
                  </div>
                </div>
                <div className="flex justify-end gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setShowApproverForm(false);
                      setEditingApprover(null);
                    }}
                    className="py-1.5 px-2 text-xs rounded-full"
                  >
                    Cancelar
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleSaveApprover}
                    className="py-1.5 px-2 text-xs rounded-full bg-gray-900 hover:bg-gray-800 text-white dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200"
                  >
                    <Save className="w-3.5 h-3.5 mr-1" />
                    Salvar
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {approvers.length === 0 && !showApproverForm ? (
            <div className="text-center py-6 lia-text-600">
              <Crown className="w-10 h-10 mx-auto mb-2 opacity-30" />
              <p className="text-xs">
                Nenhum aprovador configurado
              </p>
              <p className="text-micro mt-1">
                Clique em "Adicionar Nível" para criar um fluxo de aprovação
              </p>
            </div>
          ) : (
            <div className="relative">
              <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-gray-200 dark:bg-lia-bg-elevated" />
              {approvers
                .sort((a, b) => a.level - b.level)
                .map((approver) => (
                  <div
                    key={approver.id}
                    className="relative flex items-center gap-3 pb-4 last:pb-0"
                  >
                    <div
                      className={`relative z-10 w-10 h-10 rounded-full flex items-center justify-center text-xs font-semibold ${approver.isActive ? "text-white" : "bg-gray-100 lia-text-600 dark:bg-lia-bg-secondary dark:text-lia-text-tertiary"}`}
                    >
                      {approver.level}
                    </div>
                    <Card className="flex-1 border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-white/80 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-md">
                      <CardContent className="p-2 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Avatar className="h-8 w-8">
                            <AvatarFallback className="bg-gray-100 dark:bg-lia-bg-elevated lia-text-700 dark:text-lia-text-secondary text-micro">
                              {approver.userName
                                .split(" ")
                                .map((n) => n[0])
                                .join("")}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <p className="text-xs font-semibold lia-text-950 dark:lia-text-50">
                              {approver.userName}
                            </p>
                            <p className="text-micro lia-text-600">
                              {approver.role} • {approver.email}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-1">
                          <Badge
                            variant={approver.isActive ? "default" : "outline"}
                            className={`text-micro rounded-md ${
                              approver.isActive
                                ? "bg-status-success/15 text-status-success dark:bg-status-success/30 dark:text-status-success"
                                : "border-lia-border-subtle dark:border-lia-border-subtle"
                            }`}
                          >
                            {approver.isActive ? "Ativo" : "Inativo"}
                          </Badge>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 w-7 p-0 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
                            onClick={() => setEditingApprover(approver)}
                          >
                            <Edit className="w-3.5 h-3.5" />
                          </Button>
                          <Button
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

          <div className="bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md p-2 border border-lia-border-subtle dark:border-lia-border-subtle">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5 lia-text-500" />
              <div>
                <p className="text-xs font-semibold lia-text-700 dark:text-lia-text-secondary">
                  Fluxo de Aprovação
                </p>
                <p className="text-micro mt-0.5 lia-text-600 dark:text-lia-text-tertiary" aria-live="polite" aria-atomic="true">
                  Vagas serão enviadas para aprovação sequencial, do nível 1 ao
                  nível final. Cada aprovador receberá notificação por email e
                  pode aprovar diretamente na plataforma.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
