'use client'

import React from 'react'
import { Briefcase, CheckCircle } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { CompanyDataCard } from '../CompanyDataCard'
import { selectClass } from '../useCompanyDataForm'
import type { CompanyData } from '../useCompanyDataForm'

interface WorkModelSectionProps {
  companyData: CompanyData
  setCompanyData: (fn: (prev: CompanyData) => CompanyData) => void
  isEditing: boolean
  updateLiaToggle: (fieldKey: string, isActive: boolean) => void
  updateLiaInstruction: (fieldKey: string, instruction: string) => void
}

export function WorkModelSection({
  companyData,
  setCompanyData,
  isEditing,
  updateLiaToggle,
  updateLiaInstruction,
}: WorkModelSectionProps) {
  return (
    <div className="space-y-3">
      <h3 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wider px-1 font-['Open_Sans',sans-serif]">
        Modelo de Trabalho e Contratação
      </h3>
      
      <div className="grid grid-cols-1 gap-3">
        <CompanyDataCard
          fieldKey="work_model"
          label="Modelo de Trabalho"
          category="Trabalho & Contratação"
          isActive={companyData.lia_field_toggles?.work_model ?? true}
          currentInstruction={companyData.lia_instructions?.work_model || ''}
          isEditing={isEditing}
          onToggleChange={updateLiaToggle}
          onInstructionSave={updateLiaInstruction}
        >
          <div className="flex items-center gap-2">
            <Briefcase className="w-4 h-4 text-lia-text-tertiary" aria-hidden="true" />
            <select
              id="field-work_model"
              value={companyData.work_model || ''}
              onChange={(e) => setCompanyData((prev) => ({ ...prev, work_model: e.target.value }))}
              disabled={!isEditing}
              className={selectClass(!isEditing)}
            >
              <option value="">Selecione...</option>
              <option value="remote">100% Remoto</option>
              <option value="hybrid">Híbrido</option>
              <option value="onsite">Presencial</option>
              <option value="flexible">Flexível</option>
            </select>
          </div>
        </CompanyDataCard>

        <CompanyDataCard
          fieldKey="employment_types"
          label="Modelos de Contratação"
          category="Trabalho & Contratação"
          grouped
          isActive={companyData.lia_field_toggles?.employment_types ?? true}
          currentInstruction={companyData.lia_instructions?.employment_types || ''}
          isEditing={isEditing}
          onToggleChange={updateLiaToggle}
          onInstructionSave={updateLiaInstruction}
        >
          <div className="flex flex-wrap gap-1.5">
            {['CLT', 'PJ', 'Freelancer', 'Estágio', 'Temporário', 'Aprendiz'].map((type) => {
              const isSelected = (companyData.employment_types || []).includes(type)
              return (
                <button
                  key={type}
                  type="button"
                  disabled={!isEditing}
                  onClick={() => {
                    if (!isEditing) return
                    const current = companyData.employment_types || []
                    const updated = isSelected
                      ? current.filter((t: string) => t !== type)
                      : [...current, type]
                    setCompanyData((prev) => ({ ...prev, employment_types: updated }))
                  }}
                  className={`px-2.5 py-1.5 text-micro rounded-full border transition-colors motion-reduce:transition-none ${
                    isSelected
                      ? 'bg-lia-btn-primary-bg border-lia-btn-primary-bg text-white dark:border-lia-border-subtle'
                      : 'bg-lia-bg-primary border-lia-border-subtle text-lia-text-secondary hover:border-lia-border-default dark:bg-lia-bg-secondary dark:border-lia-border-default'
                  } ${!isEditing ? 'opacity-60 cursor-not-allowed' : ''}`}
                >
                  {isSelected && <CheckCircle className="w-2.5 h-2.5 inline mr-0.5" />}
                  {type}
                </button>
              )
            })}
          </div>
        </CompanyDataCard>

        <CompanyDataCard
          fieldKey="seniority_levels"
          label="Níveis de Senioridade"
          category="Trabalho & Contratação"
          grouped
          isActive={companyData.lia_field_toggles?.seniority_levels ?? true}
          currentInstruction={companyData.lia_instructions?.seniority_levels || ''}
          isEditing={isEditing}
          onToggleChange={updateLiaToggle}
          onInstructionSave={updateLiaInstruction}
          className="md:col-span-2"
        >
          <div className="space-y-2">
            <div className="flex flex-wrap gap-2">
              {(companyData.seniority_levels || []).map((level: string, idx: number) => (
                <Badge key={level} className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-primary text-micro px-2 py-0.5 rounded-full">
                  {level}
                  {isEditing && (
                    <button
                      onClick={() => setCompanyData((prev) => ({
                        ...prev,
                        seniority_levels: (prev.seniority_levels || []).filter((_: string, i: number) => i !== idx),
                      }))}
                      className="ml-1 hover:text-status-error"
                    >×</button>
                  )}
                </Badge>
              ))}
            </div>
            <div className="flex flex-wrap gap-1">
              {["Estágio", "Júnior", "Pleno", "Sênior", "Especialista", "Coordenador", "Gerente", "Diretor", "C-Level"]
                .filter((level) => !(companyData.seniority_levels || []).includes(level))
                .map((level) => (
                  <button
                    key={level}
                    type="button"
                    disabled={!isEditing}
                    onClick={() => {
                      if (!isEditing) return
                      setCompanyData((prev) => ({
                        ...prev,
                        seniority_levels: [...(prev.seniority_levels || []), level],
                      }))
                    }}
                    className={`text-micro px-2 py-0.5 border border-dashed border-lia-border-default dark:border-lia-border-default rounded-full text-lia-text-secondary hover:border-wedo-purple/30 hover:text-wedo-purple transition-colors motion-reduce:transition-none ${!isEditing ? 'opacity-60 cursor-not-allowed' : ''}`}
                  >
                    + {level}
                  </button>
                ))}
            </div>
          </div>
        </CompanyDataCard>
      </div>
    </div>
  )
}
