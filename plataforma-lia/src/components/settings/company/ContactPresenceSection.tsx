'use client'

import React from 'react'
import { useTranslations } from 'next-intl'
import { MapPin } from 'lucide-react'
import { CompanyDataCard, SimpleDataCard } from '../CompanyDataCard'
import { inputClass } from '../useCompanyDataForm'
import type { CompanyData } from '../useCompanyDataForm'

interface ContactPresenceSectionProps {
  companyData: CompanyData
  setCompanyData: (fn: (prev: CompanyData) => CompanyData) => void
  isEditing: boolean
  updateLiaToggle: (fieldKey: string, isActive: boolean) => void
  updateLiaInstruction: (fieldKey: string, instruction: string) => void
}

export function ContactPresenceSection({
  companyData,
  setCompanyData,
  isEditing,
  updateLiaToggle,
  updateLiaInstruction,
}: ContactPresenceSectionProps) {
  const t = useTranslations('settings.minhaEmpresa.contact')
  return (
    <div className="space-y-3" data-testid="contact-presence-section">
      <h3 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wider px-1">
        {t('sectionTitle')}
      </h3>
      
      <div className="grid grid-cols-1 gap-3">
        <CompanyDataCard
          fieldKey="website"
          label={t('website')}
          category={t('onlinePresence')}
          isActive={companyData.lia_field_toggles?.website ?? true}
          currentInstruction={companyData.lia_instructions?.website || ''}
          isEditing={isEditing}
          onToggleChange={updateLiaToggle}
          onInstructionSave={updateLiaInstruction}
        >
          <div className="flex items-center gap-2">
            <input
              id="field-website"
              type="url"
              value={companyData.website || ''}
              onChange={(e) => setCompanyData((prev) => ({ ...prev, website: e.target.value }))}
              disabled={!isEditing}
              className={inputClass(!isEditing)}
              placeholder={t('websitePlaceholder')}
            />
          </div>
        </CompanyDataCard>

        <CompanyDataCard
          fieldKey="linkedin_url"
          label={t('linkedin')}
          category={t('onlinePresence')}
          isActive={companyData.lia_field_toggles?.linkedin_url ?? true}
          currentInstruction={companyData.lia_instructions?.linkedin_url || ''}
          isEditing={isEditing}
          onToggleChange={updateLiaToggle}
          onInstructionSave={updateLiaInstruction}
        >
          <div className="flex items-center gap-2">
            <input
              id="field-linkedin_url"
              type="url"
              value={companyData.linkedin_url || ''}
              onChange={(e) => setCompanyData((prev) => ({ ...prev, linkedin_url: e.target.value }))}
              disabled={!isEditing}
              className={inputClass(!isEditing)}
              placeholder={t('linkedinPlaceholder')}
            />
          </div>
        </CompanyDataCard>

        <SimpleDataCard
          label={t('email')}
          fieldId="field-email"
          category={t('contactCategory')}
          isEditing={isEditing}
        >
          <div className="flex items-center gap-2">
            <input
              id="field-email"
              type="email"
              value={companyData.email || ''}
              onChange={(e) => setCompanyData((prev) => ({ ...prev, email: e.target.value }))}
              disabled={!isEditing}
              className={inputClass(!isEditing)}
              placeholder={t('emailPlaceholder')}
            />
          </div>
        </SimpleDataCard>

        <SimpleDataCard
          label={t('phone')}
          fieldId="field-telefone"
          category={t('contactCategory')}
          isEditing={isEditing}
        >
          <div className="flex items-center gap-2">
            <input
              id="field-telefone"
              type="tel"
              value={companyData.phone || ''}
              onChange={(e) => setCompanyData((prev) => ({ ...prev, phone: e.target.value }))}
              disabled={!isEditing}
              className={inputClass(!isEditing)}
              placeholder={t('phonePlaceholder')}
            />
          </div>
        </SimpleDataCard>

        <CompanyDataCard
          fieldKey="locations"
          label={t('address')}
          category={t('location')}
          isActive={companyData.lia_field_toggles?.locations ?? true}
          currentInstruction={companyData.lia_instructions?.locations || ''}
          isEditing={isEditing}
          onToggleChange={updateLiaToggle}
          onInstructionSave={updateLiaInstruction}
          className="md:col-span-2"
        >
          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4 text-lia-text-tertiary" aria-hidden="true" />
            <input
              id="field-locations"
              type="text"
              value={companyData.address || ''}
              onChange={(e) => setCompanyData((prev) => ({ ...prev, address: e.target.value }))}
              disabled={!isEditing}
              className={inputClass(!isEditing)}
              placeholder={t('addressPlaceholder')}
            />
          </div>
        </CompanyDataCard>
      </div>
    </div>
  )
}
