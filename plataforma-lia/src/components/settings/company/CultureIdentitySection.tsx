'use client'

import React from 'react'
import { Badge } from '@/components/ui/badge'
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
  return (
    <div className="space-y-3">
      <h3 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wider px-1 font-['Open_Sans',sans-serif]">
        Cultura e Identidade
      </h3>
      
      <div className="grid grid-cols-1 gap-3">
        <CompanyDataCard
          fieldKey="mission"
          label="Missão"
          category="Cultura"
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
            placeholder="Missão da empresa..."
          />
        </CompanyDataCard>

        <CompanyDataCard
          fieldKey="vision"
          label="Visão"
          category="Cultura"
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
            placeholder="Visão da empresa..."
          />
        </CompanyDataCard>

        <CompanyDataCard
          fieldKey="values"
          label="Valores"
          category="Cultura"
          isActive={companyData.lia_field_toggles?.values ?? true}
          currentInstruction={companyData.lia_instructions?.values || ''}
          isEditing={isEditing}
          onToggleChange={updateLiaToggle}
          onInstructionSave={updateLiaInstruction}
        >
          <div className="space-y-2">
            <div className="flex flex-wrap gap-2">
              {(companyData.values || []).map((value: string, idx: number) => (
                <Badge key={value} className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-primary text-micro px-2 py-0.5 rounded-full">
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
                </Badge>
              ))}
            </div>
            <input
              id="field-values"
              type="text"
              placeholder="Adicionar valor e pressionar Enter..."
              disabled={!isEditing}
              className={inputClass(!isEditing)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && e.currentTarget.value.trim()) {
                  e.preventDefault()
                  setCompanyData((prev) => ({
                    ...prev,
                    values: [...(prev.values || []), e.currentTarget.value.trim()],
                  }))
                  e.currentTarget.value = ""
                }
              }}
            />
          </div>
        </CompanyDataCard>

        <CompanyDataCard
          fieldKey="core_competencies"
          label="Competências Comportamentais"
          category="Cultura"
          isActive={companyData.lia_field_toggles?.core_competencies ?? true}
          currentInstruction={companyData.lia_instructions?.core_competencies || ''}
          isEditing={isEditing}
          onToggleChange={updateLiaToggle}
          onInstructionSave={updateLiaInstruction}
        >
          <div className="space-y-2">
            <div className="flex flex-wrap gap-2">
              {(companyData.coreCompetencies || []).map((comp: string, idx: number) => (
                <Badge key={comp} className="bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-primary text-micro px-2 py-0.5 rounded-full">
                  {comp}
                  {isEditing && (
                    <button
                      onClick={() => setCompanyData((prev) => ({
                        ...prev,
                        coreCompetencies: prev.coreCompetencies?.filter((_: string, i: number) => i !== idx),
                      }))}
                      className="ml-1 hover:text-status-error"
                      aria-label={`Remover ${comp}`}
                    >×</button>
                  )}
                </Badge>
              ))}
            </div>
            <input
              id="field-core_competencies"
              type="text"
              placeholder="Adicionar competência e pressionar Enter..."
              disabled={!isEditing}
              className={inputClass(!isEditing)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && e.currentTarget.value.trim()) {
                  e.preventDefault()
                  setCompanyData((prev) => ({
                    ...prev,
                    coreCompetencies: [...(prev.coreCompetencies || []), e.currentTarget.value.trim()],
                  }))
                  e.currentTarget.value = ""
                }
              }}
            />
          </div>
        </CompanyDataCard>
      </div>
    </div>
  )
}
