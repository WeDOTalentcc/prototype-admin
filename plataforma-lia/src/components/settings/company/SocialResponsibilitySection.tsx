'use client'

import React from 'react'
import { useTranslations } from 'next-intl'
import { Users, Leaf, Heart } from 'lucide-react'
import { CompanyDataCard } from '../CompanyDataCard'
import { textareaClass } from '../useCompanyDataForm'
import type { CompanyData } from '../useCompanyDataForm'

interface SocialResponsibilitySectionProps {
  companyData: CompanyData
  setCompanyData: (fn: (prev: CompanyData) => CompanyData) => void
  isEditing: boolean
  updateLiaToggle: (fieldKey: string, isActive: boolean) => void
  updateLiaInstruction: (fieldKey: string, instruction: string) => void
}

export function SocialResponsibilitySection({
  companyData,
  setCompanyData,
  isEditing,
  updateLiaToggle,
  updateLiaInstruction,
}: SocialResponsibilitySectionProps) {
  const t = useTranslations('settings.minhaEmpresa.social')
  return (
    <div className="space-y-3">
      <h3 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wider px-1">
        {t('sectionTitle')}
      </h3>
      
      <div className="grid grid-cols-1 gap-3">
        <CompanyDataCard
          fieldKey="dei_initiatives"
          label={t('dei')}
          category={t('category')}
          isActive={companyData.lia_field_toggles?.dei_initiatives ?? true}
          currentInstruction={companyData.lia_instructions?.dei_initiatives || ''}
          isEditing={isEditing}
          onToggleChange={updateLiaToggle}
          onInstructionSave={updateLiaInstruction}
        >
          <div className="flex items-start gap-2">
            <Users className="w-4 h-4 text-lia-text-tertiary mt-2" aria-hidden="true" />
            <textarea
              id="field-dei_initiatives"
              value={companyData.dei_initiatives || ''}
              onChange={(e) => setCompanyData((prev) => ({ ...prev, dei_initiatives: e.target.value }))}
              disabled={!isEditing}
              className={textareaClass(!isEditing)}
              rows={2}
              placeholder={t('deiPlaceholder')}
            />
          </div>
        </CompanyDataCard>

        <CompanyDataCard
          fieldKey="sustainability"
          label={t('sustainability')}
          category={t('category')}
          isActive={companyData.lia_field_toggles?.sustainability ?? true}
          currentInstruction={companyData.lia_instructions?.sustainability || ''}
          isEditing={isEditing}
          onToggleChange={updateLiaToggle}
          onInstructionSave={updateLiaInstruction}
        >
          <div className="flex items-start gap-2">
            <Leaf className="w-4 h-4 text-lia-text-tertiary mt-2" aria-hidden="true" />
            <textarea
              id="field-sustainability"
              value={companyData.sustainability || ''}
              onChange={(e) => setCompanyData((prev) => ({ ...prev, sustainability: e.target.value }))}
              disabled={!isEditing}
              className={textareaClass(!isEditing)}
              rows={2}
              placeholder={t('sustainabilityPlaceholder')}
            />
          </div>
        </CompanyDataCard>

        <CompanyDataCard
          fieldKey="social_impact"
          label={t('socialImpact')}
          category={t('category')}
          isActive={companyData.lia_field_toggles?.social_impact ?? true}
          currentInstruction={companyData.lia_instructions?.social_impact || ''}
          isEditing={isEditing}
          onToggleChange={updateLiaToggle}
          onInstructionSave={updateLiaInstruction}
        >
          <div className="flex items-start gap-2">
            <Heart className="w-4 h-4 text-lia-text-tertiary mt-2" aria-hidden="true" />
            <textarea
              id="field-social_impact"
              value={companyData.social_impact || ''}
              onChange={(e) => setCompanyData((prev) => ({ ...prev, social_impact: e.target.value }))}
              disabled={!isEditing}
              className={textareaClass(!isEditing)}
              rows={2}
              placeholder={t('socialImpactPlaceholder')}
            />
          </div>
        </CompanyDataCard>
      </div>
    </div>
  )
}
