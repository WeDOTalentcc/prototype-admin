'use client'

import React from 'react'
import { useTranslations } from 'next-intl'
import { Users, Building2, Calendar } from 'lucide-react'
import { SimpleDataCard } from '../CompanyDataCard'
import { inputClass, selectClass } from '../useCompanyDataForm'
import type { CompanyData } from '../useCompanyDataForm'

interface CorporateInfoSectionProps {
  companyData: CompanyData
  setCompanyData: (fn: (prev: CompanyData) => CompanyData) => void
  isEditing: boolean
}

export function CorporateInfoSection({
  companyData,
  setCompanyData,
  isEditing,
}: CorporateInfoSectionProps) {
  const t = useTranslations('settings.minhaEmpresa.corporate')
  return (
    <div className="space-y-3">
      <h3 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wider px-1">
        {t('sectionTitle')}
      </h3>
      
      <div className="grid grid-cols-1 gap-3">
        <SimpleDataCard
          label={t('employees')}
          fieldId="field-employee-count"
          category={t('structureCategory')}
          isEditing={isEditing}
        >
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-lia-text-tertiary" aria-hidden="true" />
            <input
              id="field-employee-count"
              type="number"
              value={companyData.employee_count || ''}
              onChange={(e) => setCompanyData((prev) => ({
                ...prev,
                employee_count: e.target.value ? parseInt(e.target.value) : undefined,
              }))}
              disabled={!isEditing}
              className={inputClass(!isEditing)}
              placeholder={t('employeeCountPlaceholder')}
            />
          </div>
        </SimpleDataCard>

        <SimpleDataCard
          label={t('companySize')}
          fieldId="field-company-size"
          category={t('structureCategory')}
          isEditing={isEditing}
        >
          <div className="flex items-center gap-2">
            <Building2 className="w-4 h-4 text-lia-text-tertiary" aria-hidden="true" />
            <select
              id="field-company-size"
              value={companyData.company_size || ''}
              onChange={(e) => setCompanyData((prev) => ({ ...prev, company_size: e.target.value }))}
              disabled={!isEditing}
              className={selectClass(!isEditing)}
            >
              <option value="">{t('companySizePlaceholder')}</option>
              <option value="startup">{t('companySizeStartup')}</option>
              <option value="small">{t('companySizeSmall')}</option>
              <option value="medium">{t('employeesMedium')}</option>
              <option value="large">{t('companySizeLarge')}</option>
              <option value="enterprise">{t('companySizeEnterprise')}</option>
            </select>
          </div>
        </SimpleDataCard>

        <SimpleDataCard
          label={t('foundedYear')}
          fieldId="field-founded-year"
          category={t('history')}
          isEditing={isEditing}
        >
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-lia-text-tertiary" aria-hidden="true" />
            <input
              id="field-founded-year"
              type="number"
              value={companyData.founded_year || ''}
              onChange={(e) => setCompanyData((prev) => ({
                ...prev,
                founded_year: e.target.value ? parseInt(e.target.value) : undefined,
              }))}
              disabled={!isEditing}
              className={inputClass(!isEditing)}
              placeholder={t('foundedYearPlaceholder')}
            />
          </div>
        </SimpleDataCard>
      </div>
    </div>
  )
}
