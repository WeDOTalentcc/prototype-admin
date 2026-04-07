'use client'

import React from 'react'
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
  return (
    <div className="space-y-3">
      <h3 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wider px-1 font-['Open_Sans',sans-serif]">
        Informações Corporativas
      </h3>
      
      <div className="grid grid-cols-1 gap-3">
        <SimpleDataCard
          label="Nº de Funcionários"
          fieldId="field-employee-count"
          category="Estrutura"
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
              placeholder="Ex: 500"
            />
          </div>
        </SimpleDataCard>

        <SimpleDataCard
          label="Porte da Empresa"
          fieldId="field-company-size"
          category="Estrutura"
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
              <option value="">Selecione...</option>
              <option value="startup">Startup (1-50)</option>
              <option value="small">Pequena (51-200)</option>
              <option value="medium">Média (201-1000)</option>
              <option value="large">Grande (1001-5000)</option>
              <option value="enterprise">Enterprise (5000+)</option>
            </select>
          </div>
        </SimpleDataCard>

        <SimpleDataCard
          label="Ano de Fundação"
          fieldId="field-founded-year"
          category="História"
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
              placeholder="Ex: 2020"
            />
          </div>
        </SimpleDataCard>
      </div>
    </div>
  )
}
