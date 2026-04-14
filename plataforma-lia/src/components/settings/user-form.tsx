"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { X, Save, User, Briefcase, Shield } from "lucide-react"
import { textStyles } from '@/lib/design-tokens'
import type { UserData } from './user-management-types'
import { useTranslations } from "next-intl"

interface UserFormProps {
  isCreating: boolean
  formData: Partial<UserData>
  setFormData: React.Dispatch<React.SetStateAction<Partial<UserData>>>
  onSave: () => void
  onCancel: () => void
}

export function UserForm({ isCreating, formData, setFormData, onSave, onCancel }: UserFormProps) {
  const t = useTranslations('settings.users')
  const inputClass = "w-full py-1.5 px-2 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md bg-lia-bg-primary dark:bg-lia-bg-elevated text-lia-text-primary focus:ring-1 focus:ring-lia-btn-primary-bg/10 focus:border-lia-btn-primary-bg"

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className={textStyles.title}>
            {isCreating ? t('formTitleNew') : t('formTitleEdit')}
          </h3>
          <p className={textStyles.description}>
            {isCreating ? t('formDescriptionNew') : t('formDescriptionEdit')}
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={onCancel}>
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
                <input
                  type="text"
                  value={formData.role || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, role: e.target.value }))}
                  className={inputClass}
                  placeholder={t('rolePlaceholder')}
                />
              </div>

              <div>
                <label className={textStyles.label + " block mb-1.5"}>{t('department')}</label>
                <select
                  value={formData.department || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, department: e.target.value }))}
                  className={inputClass}
                >
                  <option value="">{t('departmentSelect')}</option>
                  <option value="Talent Acquisition">{t('departmentTA')}</option>
                  <option value="RH">{t('departmentHR')}</option>
                  <option value="Operações">{t('departmentOps')}</option>
                  <option value="Tecnologia">{t('departmentTech')}</option>
                </select>
              </div>

              <div>
                <label className={textStyles.label + " block mb-1.5"}>{t('position')}</label>
                <input
                  type="text"
                  value={formData.position || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, position: e.target.value }))}
                  className={inputClass}
                  placeholder={t('positionPlaceholder')}
                />
              </div>

              <div>
                <label className={textStyles.label + " block mb-1.5"}>{t('status')}</label>
                <select
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
                    checked={formData.isManager || false}
                    onChange={(e) => setFormData(prev => ({ ...prev, isManager: e.target.checked }))}
                    className="w-3.5 h-3.5 rounded-xl border-lia-border-default"
                  />
                  <span className={textStyles.label}>{t('isManager')}</span>
                </label>
              </div>
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
            <Button variant="outline" size="sm" onClick={onCancel}>
              {t('cancel')}
            </Button>
            <Button onClick={onSave} size="sm" className="gap-1.5 hover:bg-lia-interactive-hover transition-colors cursor-pointer">
              <Save className="w-3.5 h-3.5" />
              {isCreating ? t('createUser') : t('saveChanges')}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
