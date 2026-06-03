"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { X, Save, User, Briefcase, Shield } from "lucide-react"
import { textStyles } from '@/lib/design-tokens'
import type { UserData } from './user-management-types'
import { useTranslations } from "next-intl"
import { mapRoleToApi } from "./use-user-management"
import { useAuth } from "@/contexts/auth-context"
import { SalaryGrantConfirmDialog } from "./SalaryGrantConfirmDialog"
import { SensitivePiiGrantConfirmDialog } from "./SensitivePiiGrantConfirmDialog"
import { InlineDepartmentCreateModal, type CreatedDepartment, type InlineDepartmentSaveFn } from "./InlineDepartmentCreateModal"
import { useCompanyId } from "@/hooks/company/useCompanyId"
import { apiFetch } from "@/lib/api/api-fetch"

interface UserFormProps {
  departments?: Array<{ id?: string; name: string }>
  /** Sprint 2 RBAC Phase 2.5: callback para parent refresh departments após inline create. */
  onDepartmentCreated?: () => void
  isCreating: boolean
  formData: Partial<UserData>
  setFormData: React.Dispatch<React.SetStateAction<Partial<UserData>>>
  onSave: () => void
  onCancel: () => void
}

export function UserForm({ isCreating, formData, setFormData, onSave, onCancel, departments, onDepartmentCreated }: UserFormProps) {
  // Sprint 5.5 RBAC (2026-05-25): can_view_salary checkbox gated by tenant admin role.
  // LGPD Art. 6 III minimização — only admin can grant PII access.
  const { user: authUser } = useAuth()
  const isAdmin = authUser?.role === 'admin' || authUser?.role === 'wedotalent_admin'
  // B2 (2026-05-25): confirm dialog antes do grant via checkbox
  const [salaryConfirm, setSalaryConfirm] = useState<{ open: boolean; next: boolean }>({
    open: false,
    next: false,
  })
  const [sensitivePiiConfirm, setSensitivePiiConfirm] = useState<{ open: boolean; next: boolean }>({
    open: false,
    next: false,
  })

  const t = useTranslations('settings.users')
  const inputClass = "w-full py-1.5 px-2 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md bg-lia-bg-primary dark:bg-lia-bg-elevated text-lia-text-primary focus:ring-1 focus:ring-lia-btn-primary-bg/10 focus:border-lia-btn-primary-bg"

  // Sprint 2 RBAC Phase 2.5 (2026-05-25): inline modal para criar departamento sem trocar de tab.
  // Plan canonical: ~/.claude/plans/jolly-roaming-moler.md
  const { companyId } = useCompanyId()
  const [isCreateDeptOpen, setIsCreateDeptOpen] = useState(false)
  const [prevDeptIdBeforeCreate, setPrevDeptIdBeforeCreate] = useState<string | null>(null)

  // Fix P1 (2026-05-26): produtor canônico de save para InlineDepartmentCreateModal.
  // Remove fetch duplicado do modal — modal fica thin, lógica de persistência fica aqui.
  const handleCreateDepartmentSave: InlineDepartmentSaveFn = async (name, { code, managerEmail } = {}) => {
    const payload: Record<string, unknown> = {
      name,
      description: "",
      manager_name: "",
      manager_title: "",
      manager_email: managerEmail ?? "",
      manager_phone: "",
      headcount: 0,
      color: "",
    }
    if (code) payload.code = code
    const cid = companyId ?? ""
    const res = await apiFetch(
      "/api/backend-proxy/company/departments?company_id=" + encodeURIComponent(cid),
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }
    )
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      const detail =
        (typeof body.detail === "string" ? body.detail : null) ||
        (typeof body.message === "string" ? body.message : null) ||
        "HTTP " + res.status
      throw new Error("Falha ao criar departamento: " + detail)
    }
    const result = await res.json().catch(() => ({}))
    return {
      id: result?.id || result?.data?.id || result?.department?.id || "",
      name: result?.name || result?.data?.name || name,
    }
  }

  return (
    <>
      <div className="space-y-4" data-testid={isCreating ? 'user-create-form' : 'user-edit-form'}>
      <div className="flex items-center justify-between">
        <div>
          <h3 className={textStyles.title}>
            {isCreating ? t('formTitleNew') : t('formTitleEdit')}
          </h3>
          <p className={textStyles.description}>
            {isCreating ? t('formDescriptionNew') : t('formDescriptionEdit')}
          </p>
        </div>
        <Button data-testid="user-form-cancel-top" variant="outline" size="sm" onClick={onCancel}>
          <X className="w-3.5 h-3.5 mr-1.5" />
          {t('cancel')}
        </Button>
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <h4 className={`${textStyles.title} flex items-center gap-2`}>
                <User className="w-3.5 h-3.5" />
                {t('personalData')}
              </h4>

              <div>
                <label className={textStyles.label + " block mb-1.5"}>{t('fullName')}</label>
                <input
                  type="text"
                  data-field="name"
                  data-testid="user-field-name"
                  value={formData.name || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  className={inputClass}
                  placeholder={t('fullNamePlaceholder')}
                />
              </div>

              <div>
                <label className={textStyles.label + " block mb-1.5"}>{t('email')}</label>
                <input
                  type="email"
                  data-field="email"
                  data-testid="user-field-email"
                  value={formData.email || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                  className={inputClass}
                  placeholder={t('emailPlaceholder')}
                />
              </div>

              <div>
                <label className={textStyles.label + " block mb-1.5"}>{t('phone')}</label>
                <input
                  type="tel"
                  data-field="phone"
                  data-testid="user-field-phone"
                  value={formData.phone || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
                  className={inputClass}
                  placeholder={t('phonePlaceholder')}
                />
              </div>

              <div>
                <label className={textStyles.label + " block mb-1.5"}>{t('whatsapp')}</label>
                <input
                  type="tel"
                  data-field="whatsapp"
                  data-testid="user-field-whatsapp"
                  value={formData.whatsapp || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, whatsapp: e.target.value }))}
                  className={inputClass}
                  placeholder={t('whatsappPlaceholder')}
                />
              </div>

              <div>
                <label className={textStyles.label + " block mb-1.5"}>{t('location')}</label>
                <input
                  type="text"
                  data-field="location"
                  data-testid="user-field-location"
                  value={formData.location || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, location: e.target.value }))}
                  className={inputClass}
                  placeholder={t('locationPlaceholder')}
                />
              </div>
            </div>

            <div className="space-y-3">
              <h4 className={`${textStyles.title} flex items-center gap-2`}>
                <Briefcase className="w-3.5 h-3.5" />
                {t('professionalData')}
              </h4>

              <div>
                <label className={textStyles.label + " block mb-1.5"}>{t('roleFunction')}</label>
                {/* P1-5 (auditoria Configuracoes): select canonical em vez de input texto
                    com fuzzy match silencioso. value normalizado via mapRoleToApi p/ casar
                    no modo edicao (canonical/label/vazio->viewer). */}
                <select
                  data-field="role"
                  data-testid="user-field-role"
                  value={mapRoleToApi(formData.role)}
                  onChange={(e) => setFormData(prev => ({ ...prev, role: e.target.value }))}
                  className={inputClass}
                >
                  <option value="admin">{t('roleAdmin')}</option>
                  <option value="manager">{t('roleManager')}</option>
                  <option value="recruiter">{t('roleRecruiter')}</option>
                  <option value="viewer">{t('roleViewer')}</option>
                </select>
              </div>

              <div>
                <label className={textStyles.label + " block mb-1.5"}>{t('department')}</label>
                {/* Sprint 2 RBAC (2026-05-25): select agora salva department_id (UUID FK) + department (name display).
                    Plan canonical: ~/.claude/plans/jolly-roaming-moler.md
                    Backend filter (crud.py:list_job_vacancies) usa users.department_id para soft-launch dept scope.
                    Backward compat: department (string) preservado para legacy consumers.

                    Histórico (WT-2022 P0.RBAC3): dropdown puxa dinamicamente de /company/departments.
                    Antes era hardcoded (Talent Acquisition/RH/Operacoes/Tecnologia).
                */}
                <select
                  data-field="department"
                  data-testid="user-field-department"
                  value={(formData.department_id as string) || ''}
                  onChange={(e) => {
                    const deptId = e.target.value
                    // Sprint 2 RBAC Phase 2.5: sentinel "__CREATE_NEW__" abre modal inline
                    if (deptId === "__CREATE_NEW__") {
                      setPrevDeptIdBeforeCreate((formData.department_id as string) || null)
                      setIsCreateDeptOpen(true)
                      return  // não muda formData; modal cancelar reseta select; modal sucesso popula novo dept
                    }
                    // Selected dept object para extrair nome canonical (display label)
                    const dept = departments?.find((d) => d.id === deptId)
                    setFormData(prev => ({
                      ...prev,
                      department_id: deptId || null,
                      department: dept?.name || '',  // sync legacy field display
                    }))
                  }}
                  className={inputClass}
                >
                  <option value="">{t('departmentSelect')}</option>
                  {(departments && departments.length > 0) ? (
                    departments.map((dept) => (
                      <option key={dept.id} value={dept.id}>
                        {dept.name}
                      </option>
                    ))
                  ) : (
                    /* Fallback transitional — sem departments cadastrados ainda */
                    <option value="" disabled>{t('departmentSelect')}</option>
                  )}
                  {/* Sprint 2 RBAC Phase 2.5 (2026-05-25): inline create option canonical */}
                  <option value="__CREATE_NEW__" data-testid="user-field-department-create-new">
                    + Criar novo departamento
                  </option>
                </select>
                {(!departments || departments.length === 0) && (
                  <p className="text-xs text-lia-text-tertiary mt-1.5">
                    Configure departamentos em "Departamentos" para granularidade de acesso (Sprint 2 RBAC).
                  </p>
                )}
              </div>

              <div>
                <label className={textStyles.label + " block mb-1.5"}>{t('position')}</label>
                <input
                  type="text"
                  data-field="position"
                  data-testid="user-field-position"
                  value={formData.position || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, position: e.target.value }))}
                  className={inputClass}
                  placeholder={t('positionPlaceholder')}
                />
              </div>

              <div>
                <label className={textStyles.label + " block mb-1.5"}>{t('status')}</label>
                <select
                  data-field="status"
                  data-testid="user-field-status"
                  value={formData.status || 'active'}
                  onChange={(e) => setFormData(prev => ({ ...prev, status: e.target.value as typeof prev.status }))}
                  className={inputClass}
                >
                  <option value="active">{t('statusActive')}</option>
                  <option value="inactive">{t('statusInactive')}</option>
                  <option value="pending">{t('statusPending')}</option>
                </select>
              </div>

              <div>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    data-toggle="isManager"
                    data-testid="user-toggle-is-manager"
                    checked={formData.isManager || false}
                    onChange={(e) => setFormData(prev => ({ ...prev, isManager: e.target.checked }))}
                    className="w-3.5 h-3.5 rounded-xl border-lia-border-default"
                  />
                  <span className={textStyles.label}>{t('isManager')}</span>
                </label>
              </div>

              {/* Sprint 5.5 RBAC (2026-05-25): can_view_salary grant — tenant admin only.
                  LGPD Art. 6 III minimização. Plan canonical: jolly-roaming-moler.md */}
              {isAdmin && (
                <div>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      data-toggle="canViewSalary"
                      data-testid="user-toggle-can-view-salary"
                      checked={(formData as Record<string, unknown>).can_view_salary as boolean || false}
                      onChange={(e) => setSalaryConfirm({ open: true, next: e.target.checked })}
                      className="w-3.5 h-3.5 rounded-xl border-lia-border-default"
                    />
                    <span className={textStyles.label}>{t('canViewSalaryCheckboxLabel')}</span>
                  </label>
                </div>
              )}

              {isAdmin && (
                <div>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      data-toggle="canViewSensitivePii"
                      data-testid="user-toggle-can-view-sensitive-pii"
                      checked={((formData as Record<string, unknown>).can_view_sensitive_pii as boolean | undefined) ?? true}
                      onChange={(e) => setSensitivePiiConfirm({ open: true, next: e.target.checked })}
                      className="w-3.5 h-3.5 rounded-xl border-lia-border-default"
                    />
                    <span className={textStyles.label}>Pode ver dados pessoais sensíveis (CPF, endereço)</span>
                  </label>
                </div>
              )}
            </div>
          </div>

          <div className="mt-4">
            <h4 className={`${textStyles.title} flex items-center gap-2 mb-3`}>
              <Shield className="w-3.5 h-3.5" />
              {t('permissions')}
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {[
                { id: 'recruitment', label: t('permRecruitment') },
                { id: 'candidates', label: t('permCandidates') },
                { id: 'interviews', label: t('permInterviews') },
                { id: 'reports', label: t('permReports') },
                { id: 'settings', label: t('permSettings') },
                { id: 'users', label: t('permUsers') },
                { id: 'admin', label: t('permAdmin') },
                { id: 'analytics', label: t('permAnalytics') }
              ].map((permission) => (
                <label key={permission.id} className="flex items-center gap-1.5">
                  <input
                    type="checkbox"
                    data-toggle={`permission_${permission.id}`}
                    data-testid={`user-permission-${permission.id}`}
                    checked={(formData.permissions || []).includes(permission.id)}
                    onChange={(e) => {
                      const permissions = formData.permissions || []
                      if (e.target.checked) {
                        setFormData(prev => ({ ...prev, permissions: [...permissions, permission.id] }))
                      } else {
                        setFormData(prev => ({ ...prev, permissions: permissions.filter(p => p !== permission.id) }))
                      }
                    }}
                    className="w-3.5 h-3.5 rounded-xl border-lia-border-default"
                  />
                  <span className={textStyles.label}>{permission.label}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-2 mt-6 pt-4 border-t">
            <Button data-testid="user-form-cancel" variant="outline" size="sm" onClick={onCancel}>
              {t('cancel')}
            </Button>
            <Button data-testid="user-form-save" onClick={onSave} size="sm" className="gap-1.5 hover:bg-lia-interactive-hover transition-colors cursor-pointer">
              <Save className="w-3.5 h-3.5" />
              {isCreating ? t('createUser') : t('saveChanges')}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>

      {/* Sprint 2 RBAC Phase 2.5 (2026-05-25): inline modal canonical */}
      <InlineDepartmentCreateModal
        open={isCreateDeptOpen}
        onOpenChange={(open) => {
          setIsCreateDeptOpen(open)
          // Cancel sem create: select fica no valor prev (estava antes do "__CREATE_NEW__")
          // formData.department_id não mudou, então select já volta natural
          if (!open) {
            void prevDeptIdBeforeCreate  // explicit no-op para preservar intenção
          }
        }}
        companyId={companyId}
        existingDepartments={departments}
        onSave={handleCreateDepartmentSave}
        onCreated={(newDept: CreatedDepartment) => {
          // Auto-select new dept no form
          setFormData(prev => ({
            ...prev,
            department_id: newDept.id,
            department: newDept.name,
          }))
          // Notify parent para refresh canonical list
          onDepartmentCreated?.()
        }}
      />
    <SalaryGrantConfirmDialog
        open={salaryConfirm.open}
        onOpenChange={(open) => setSalaryConfirm((s) => ({ ...s, open }))}
        granting={salaryConfirm.next}
        target={formData.name || ""}
        targetDetail={formData.email}
        onConfirm={() => {
          setFormData(prev => ({ ...prev, can_view_salary: salaryConfirm.next } as typeof prev))
          setSalaryConfirm({ open: false, next: false })
        }}
      />
      <SensitivePiiGrantConfirmDialog
        open={sensitivePiiConfirm.open}
        onOpenChange={(open) => setSensitivePiiConfirm((s) => ({ ...s, open }))}
        granting={sensitivePiiConfirm.next}
        target={formData.name || ""}
        targetDetail={formData.email}
        onConfirm={() => {
          setFormData(prev => ({ ...prev, can_view_sensitive_pii: sensitivePiiConfirm.next } as typeof prev))
          setSensitivePiiConfirm({ open: false, next: false })
        }}
      />
    </>
  )
}
