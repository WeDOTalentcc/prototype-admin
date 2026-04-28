'use client'

import React from 'react'
import { useTranslations } from 'next-intl'
import { Save, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { CompanyDataCard } from '../CompanyDataCard'
import { BigFiveRadar } from '../BigFiveRadar'
import type { CompanyData } from '../useCompanyDataForm'

interface BigFiveSectionProps {
  companyData: CompanyData
  setCompanyData: (fn: (prev: CompanyData) => CompanyData) => void
  isEditing: boolean
  saving: boolean
  updateLiaToggle: (fieldKey: string, isActive: boolean) => void
  updateLiaInstruction: (fieldKey: string, instruction: string) => void
  handleSaveCultureFields: () => Promise<void>
}

export function BigFiveSection({
  companyData,
  setCompanyData,
  isEditing,
  saving,
  updateLiaToggle,
  updateLiaInstruction,
  handleSaveCultureFields,
}: BigFiveSectionProps) {
  const t = useTranslations('settings.bigFive')
  const tBenefits = useTranslations('settings.benefits')
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wider px-1">
          {t('title')}
        </h3>
        <Button
          variant="outline"
          size="sm"
          onClick={handleSaveCultureFields}
          disabled={saving}
          className="text-micro rounded-xl border-lia-border-default hover:bg-lia-bg-tertiary dark:border-lia-border-default dark:hover:bg-lia-bg-inverse"
        >
          {saving ? (
            <>
              <Loader2 className="w-3 h-3 mr-1.5 animate-spin motion-reduce:animate-none" />
              {tBenefits('savingBtn')}
            </>
          ) : (
            <>
              <Save className="w-3 h-3 mr-1.5 text-lia-text-primary" />
              {t('saveProfile')}
            </>
          )}
        </Button>
      </div>
      
      <CompanyDataCard
        fieldKey="company_big_five"
        label={t('culturalProfile')}
        category={t('organizationalCulture')}
        grouped
        isActive={companyData.lia_field_toggles?.company_big_five ?? true}
        currentInstruction={companyData.lia_instructions?.company_big_five || ''}
        isEditing={isEditing}
        onToggleChange={updateLiaToggle}
        onInstructionSave={updateLiaInstruction}
      >
        <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 rounded-xl p-4">
          <BigFiveRadar
            scores={{
              openness: companyData.openness_score ?? 50,
              conscientiousness: companyData.conscientiousness_score ?? 50,
              extraversion: companyData.extraversion_score ?? 50,
              agreeableness: companyData.agreeableness_score ?? 50,
              stability: companyData.stability_score ?? 50,
            }}
            onScoresChange={(scores) => {
              if (!isEditing) return
              setCompanyData((prev) => ({
                ...prev,
                openness_score: scores.openness,
                conscientiousness_score: scores.conscientiousness,
                extraversion_score: scores.extraversion,
                agreeableness_score: scores.agreeableness,
                stability_score: scores.stability,
              }))
            }}
            isEditable={isEditing}
            size={200}
          />
        </div>
      </CompanyDataCard>
    </div>
  )
}
