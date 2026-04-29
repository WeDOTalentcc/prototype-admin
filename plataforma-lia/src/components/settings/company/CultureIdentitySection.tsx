'use client'

import React from 'react'
import { useTranslations } from 'next-intl'
import { Chip } from '@/components/ui/chip'
import { CompanyDataCard } from '../CompanyDataCard'
import { inputClass, textareaClass } from '../useCompanyDataForm'
import type { CompanyData } from '../useCompanyDataForm'

interface CultureIdentitySectionProps {
  companyData: CompanyData
  setCompanyData: (fn: (prev: CompanyData) => CompanyData) => void
  isEditing: boolean
  updateLiaToggle: (fieldKey: string, isActive: boolean) => void
  updateLiaInstruction: (fieldKey: string, instruction: string) => void
}

export function CultureIdentitySection({
  companyData,
  setCompanyData,
  isEditing,
  updateLiaToggle,
  updateLiaInstruction,
}: CultureIdentitySectionProps) {
  const t = useTranslations('settings.minhaEmpresa.culture')
  return (
    <div className="space-y-3">
      <h3 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wider px-1">
        {t('sectionTitle')}
      </h3>
      
      <div className="grid grid-cols-1 gap-3">
        <CompanyDataCard
          fieldKey="mission"
          label={t('mission')}
          category={t('category')}
          isActive={companyData.lia_field_toggles?.mission ?? true}
          currentInstruction={companyData.lia_instructions?.mission || ''}
          isEditing={isEditing}
          onToggleChange={updateLiaToggle}
          onInstructionSave={updateLiaInstruction}
        >
          <textarea
            id="field-mission"
            value={companyData.mission || ''}
            onChange={(e) => setCompanyData((prev) => ({ ...prev, mission: e.target.value }))}
            disabled={!isEditing}
            className={textareaClass(!isEditing)}
            rows={2}
            placeholder={t('missionPlaceholder')}
          />
        </CompanyDataCard>

        <CompanyDataCard
          fieldKey="vision"
          label={t('vision')}
          category={t('category')}
          isActive={companyData.lia_field_toggles?.vision ?? true}
          currentInstruction={companyData.lia_instructions?.vision || ''}
          isEditing={isEditing}
          onToggleChange={updateLiaToggle}
          onInstructionSave={updateLiaInstruction}
        >
          <textarea
            id="field-vision"
            value={companyData.vision || ''}
            onChange={(e) => setCompanyData((prev) => ({ ...prev, vision: e.target.value }))}
            disabled={!isEditing}
            className={textareaClass(!isEditing)}
            rows={2}
            placeholder={t('visionPlaceholder')}
          />
        </CompanyDataCard>

        <CompanyDataCard
          fieldKey="values"
          label={t('valuesLabel')}
          category={t('category')}
          isActive={companyData.lia_field_toggles?.values ?? true}
          currentInstruction={companyData.lia_instructions?.values || ''}
          isEditing={isEditing}
          onToggleChange={updateLiaToggle}
          onInstructionSave={updateLiaInstruction}
        >
          <div className="space-y-2">
            <div className="flex flex-wrap gap-2">
              {(companyData.values || []).map((value: string, idx: number) => (
                <Chip variant="neutral" muted key={value} className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-primary text-micro px-2 py-0.5 rounded-full">
                  {value}
                  {isEditing && (
                    <button
                      onClick={() => setCompanyData((prev) => ({
                        ...prev,
                        values: prev.values?.filter((_: string, i: number) => i !== idx),
                      }))}
                      className="ml-1 hover:text-status-error"
                    >×</button>
                  )}
                </Chip>
              ))}
            </div>
            <input
              id="field-values"
              type="text"
              placeholder={t('valuesPlaceholder')}
              disabled={!isEditing}
              className={inputClass(!isEditing)}
              onKeyDown={(e) => {
                if (e.key ==="Enter" && e.currentTarget.value.trim()) {
                  e.preventDefault()
                  setCompanyData((prev) => ({
                    ...prev,
                    values: [...(prev.values || []), e.currentTarget.value.trim()],
                  }))
                  e.currentTarget.value =""
                }
              }}
            />
          </div>
        </CompanyDataCard>

        <CompanyDataCard
          fieldKey="core_competencies"
          label={t('behavioralCompetencies')}
          category={t('category')}
          isActive={companyData.lia_field_toggles?.core_competencies ?? true}
          currentInstruction={companyData.lia_instructions?.core_competencies || ''}
          isEditing={isEditing}
          onToggleChange={updateLiaToggle}
          onInstructionSave={updateLiaInstruction}
        >
          <div className="space-y-2">
            <div className="flex flex-wrap gap-2">
              {(companyData.coreCompetencies || []).map((comp: string, idx: number) => (
                <Chip variant="neutral" muted key={comp} className="bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-primary text-micro px-2 py-0.5 rounded-full">
                  {comp}
                  {isEditing && (
                    <button
                      onClick={() => setCompanyData((prev) => ({
                        ...prev,
                        coreCompetencies: prev.coreCompetencies?.filter((_: string, i: number) => i !== idx),
                      }))}
                      className="ml-1 hover:text-status-error"
                      aria-label={t('removeCompetency', { name: comp })}
                    >×</button>
                  )}
                </Chip>
              ))}
            </div>
            <input
              id="field-core_competencies"
              type="text"
              placeholder={t('addCompetencyPlaceholder')}
              disabled={!isEditing}
              className={inputClass(!isEditing)}
              onKeyDown={(e) => {
                if (e.key ==="Enter" && e.currentTarget.value.trim()) {
                  e.preventDefault()
                  setCompanyData((prev) => ({
                    ...prev,
                    coreCompetencies: [...(prev.coreCompetencies || []), e.currentTarget.value.trim()],
                  }))
                  e.currentTarget.value =""
                }
              }}
            />
          </div>
        </CompanyDataCard>
      </div>
    </div>
  )
}
