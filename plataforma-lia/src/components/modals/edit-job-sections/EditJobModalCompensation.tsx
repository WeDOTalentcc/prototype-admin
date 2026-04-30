"use client"

import React, { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Chip } from "@/components/ui/chip"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  DollarSign,
  Heart,
  CheckCircle,
  Plus,
  TrendingUp,
  Briefcase,
} from "lucide-react"
import { inputStyle } from '../edit-job-modal.constants'
import type { Job } from '../edit-job/edit-job.types'
import type { CompanyBenefit } from '@/types/benefits'
import { BenefitFormModal } from '@/components/settings/benefits/BenefitFormModal'

type BenefitItem = string | { id?: string; name: string }

function benefitName(b: BenefitItem): string {
  return typeof b === 'string' ? b : b.name
}

function isBenefitAdded(benefits: BenefitItem[], candidate: CompanyBenefit): boolean {
  return benefits.some(b =>
    typeof b === 'string' ? b === candidate.name : (b as { id?: string }).id === candidate.id
  )
}

interface EditJobModalCompensationProps {
  formData: Partial<Job>
  setFormData: React.Dispatch<React.SetStateAction<Partial<Job>>>
  newBenefit: string
  setNewBenefit: (v: string) => void
  companyBenefits: CompanyBenefit[]
  addBenefit: () => void
  removeBenefit: (idx: number) => void
  activeCompensationPolicies: { id: string; name: string; policy_type?: string }[]
  /** INT:005 — triggers LIA chat with apply_compensation_policy intent */
  onSuggestWithLIA?: () => void
}

export function EditJobModalCompensation({
  formData,
  setFormData,
  newBenefit,
  setNewBenefit,
  companyBenefits,
  addBenefit,
  removeBenefit,
  activeCompensationPolicies,
  onSuggestWithLIA,
}: EditJobModalCompensationProps) {
  const benefits = (formData.benefits || []) as BenefitItem[]
  const [showBenefitModal, setShowBenefitModal] = useState(false)
  const [editingBenefit, setEditingBenefit] = useState<Parameters<typeof BenefitFormModal>[0]['editingBenefit']>(null)
  const [isSavingBenefit, setIsSavingBenefit] = useState(false)

  const handleBenefitSaveToCompany = async (benefit: NonNullable<typeof editingBenefit>) => {
    setIsSavingBenefit(true)
    try {
      const res = await fetch('/api/backend-proxy/company/benefits/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(benefit),
      })
      if (res.ok) {
        const data = await res.json()
        setFormData(prev => ({
          ...prev,
          benefits: [...((prev.benefits || []) as BenefitItem[]), { id: data.id, name: data.name }],
        }))
        setShowBenefitModal(false)
        setEditingBenefit(null)
      }
    } finally {
      setIsSavingBenefit(false)
    }
  }

  return (
    <section data-testid="edit-job-compensation-section">
      <div className="flex items-center gap-2 mb-4">
        <DollarSign className="w-4 h-4 text-lia-text-secondary" />
        <h3 className="text-base-ui font-semibold text-lia-text-primary">Remuneração</h3>
      </div>

      <div className="space-y-4">
        <div>
          <Label className="text-xs font-medium text-lia-text-primary mb-1 block">Faixa Salarial</Label>
          <div className="flex gap-3">
            <div className="flex-1">
              <span className="text-micro text-lia-text-tertiary mb-1 block">De</span>
              <Input
                type="number"
                value={formData.salaryMin || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, salaryMin: Number(e.target.value) }))}
                className={inputStyle}
                placeholder="12.000"
              />
            </div>
            <div className="flex-1">
              <span className="text-micro text-lia-text-tertiary mb-1 block">Até</span>
              <Input
                type="number"
                value={formData.salaryMax || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, salaryMax: Number(e.target.value) }))}
                className={inputStyle}
                placeholder="18.000"
              />
            </div>
          </div>
        </div>

        <div>
          <Label className="text-xs font-medium text-lia-text-primary mb-1 block">
            {formData.compensation_policy_id
              ? 'Bônus Anual (override sobre PRV vinculada)'
              : 'Bônus Anual (opcional)'}
          </Label>
          <div className="flex gap-3">
            <div className="flex-1">
              <span className="text-micro text-lia-text-tertiary mb-1 block">De</span>
              <Input
                type="number"
                value={formData.bonusMin || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, bonusMin: Number(e.target.value) }))}
                className={inputStyle}
                placeholder="2.000"
              />
            </div>
            <div className="flex-1">
              <span className="text-micro text-lia-text-tertiary mb-1 block">Até</span>
              <Input
                type="number"
                value={formData.bonusMax || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, bonusMax: Number(e.target.value) }))}
                className={inputStyle}
                placeholder="6.000"
              />
            </div>
          </div>
        </div>

        {activeCompensationPolicies.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 mb-1">
              <TrendingUp className="w-3.5 h-3.5 text-lia-text-secondary" />
              <Label className="text-xs font-medium text-lia-text-primary">
                Política de Remuneração Variável (opcional)
              </Label>
            </div>
            <Select
              value={formData.compensation_policy_id || 'none'}
              onValueChange={(v) =>
                setFormData(prev => ({ ...prev, compensation_policy_id: v === 'none' ? undefined : v }))
              }
            >
              <SelectTrigger className="h-10 w-full text-sm bg-lia-bg-secondary border-lia-border-subtle">
                <SelectValue placeholder="Nenhuma política vinculada" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none" className="text-xs text-lia-text-disabled">Nenhuma</SelectItem>
                {activeCompensationPolicies.map(p => (
                  <SelectItem key={p.id} value={p.id} className="text-xs">
                    {p.name}
                    {p.policy_type && (
                      <span className="ml-2 text-lia-text-tertiary">({p.policy_type})</span>
                    )}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {formData.compensation_policy_id && (
              <div className="mt-1 flex items-center justify-between gap-2">
                <p className="text-micro text-lia-text-tertiary">
                  PRV desta política é a referência; bônus acima substitui pontualmente.
                </p>
                {onSuggestWithLIA && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="h-6 px-2 text-micro text-lia-text-link hover:text-lia-text-primary whitespace-nowrap flex items-center gap-1"
                    onClick={onSuggestWithLIA}
                  >
                    <Briefcase className="w-3 h-3" />
                    Sugerir pacote com LIA
                  </Button>
                )}
              </div>
            )}
          </div>
        )}

        <div>
          <Label className="text-xs text-lia-text-secondary mb-2 block">Benefícios</Label>
          <div className="flex flex-wrap gap-2 mb-3">
            {benefits.map((benefit, idx) => (
              <Chip
                key={idx}
                variant="neutral"
                className="flex items-center gap-1 py-0.5 px-2 text-xs bg-lia-bg-primary"
              >
                <button
                  onClick={() => removeBenefit(idx)}
                  className="text-lia-text-secondary hover:text-status-error mr-0.5"
                  type="button"
                >
                  ×
                </button>
                {benefitName(benefit)}
                {companyBenefits.find(cb => cb.name === benefitName(benefit))?.is_highlighted && (
                  <Heart className="w-3 h-3 text-wedo-magenta fill-pink-500" />
                )}
              </Chip>
            ))}
          </div>
          {companyBenefits.length > 0 && (
            <div className="mb-3">
              <Label className="text-xs text-lia-text-tertiary mb-1.5 block">Sugestões da empresa</Label>
              <div className="flex flex-wrap gap-1.5">
                {companyBenefits.map((benefit) => {
                  const isAdded = isBenefitAdded(benefits, benefit)
                  return (
                    <Chip
                      key={benefit.id}
                      variant="neutral"
                      className={`text-xs px-2 py-0.5 cursor-pointer transition-colors motion-reduce:transition-none ${
                        isAdded
                          ? 'bg-lia-bg-tertiary border-lia-btn-primary-bg text-lia-text-primary'
                          : 'bg-lia-bg-secondary border-lia-border-subtle text-lia-text-secondary hover:bg-lia-interactive-hover hover:border-lia-border-medium hover:text-lia-text-primary'
                      }`}
                      onClick={() => {
                        if (!isAdded) {
                          setFormData(prev => ({
                            ...prev,
                            benefits: [
                              ...((prev.benefits || []) as BenefitItem[]),
                              { id: benefit.id, name: benefit.name },
                            ],
                          }))
                        }
                      }}
                    >
                      {isAdded && <CheckCircle className="w-3 h-3 mr-1" />}
                      {benefit.is_highlighted && <Heart className="w-3 h-3 mr-1 text-wedo-magenta" />}
                      {benefit.name}
                      {!isAdded && <Plus className="w-3 h-3 ml-1" />}
                    </Chip>
                  )
                })}
              </div>
            </div>
          )}
          <div className="flex gap-2">
            <Input
              value={newBenefit}
              onChange={(e) => setNewBenefit(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addBenefit())}
              className={`${inputStyle} flex-1`}
              placeholder="Ex: Vale Refeição, Plano de Saúde..."
            />
            <Button
              variant="outline"
              className="h-10 px-3 text-sm border-lia-btn-primary-bg text-lia-text-primary hover:bg-lia-interactive-hover"
              onClick={addBenefit}
            >
              <Plus className="w-4 h-4 mr-1" />
              Adicionar
            </Button>
            <Button
              variant="outline"
              className="h-10 px-3 text-sm border-lia-border-subtle text-lia-text-secondary hover:bg-lia-interactive-hover"
              title="Cadastrar benefício detalhado e promover para a empresa"
              onClick={() => {
                setEditingBenefit({
                  name: '', description: '', category: 'health', value_type: 'monetary',
                  applicable_to: [], seniority_levels: [], contract_types: [],
                  departments: {}, waiting_period_days: 0,
                  is_mandatory: false, is_active: true, is_highlighted: false,
                  is_discount: false, order: 0,
                })
                setShowBenefitModal(true)
              }}
            >
              <Briefcase className="w-4 h-4 mr-1" />
              Detalhado
            </Button>
          </div>
          <p className="text-micro text-lia-text-tertiary mt-1">
            "Detalhado" salva também no cadastro da empresa para reutilizar em outras vagas.
          </p>
        </div>
      </div>

      {/* 3.5: BenefitFormModal em contexto de vaga */}
      <BenefitFormModal
        open={showBenefitModal}
        onOpenChange={(o) => { if (!o) { setShowBenefitModal(false); setEditingBenefit(null) } }}
        editingBenefit={editingBenefit}
        setEditingBenefit={setEditingBenefit}
        isSaving={isSavingBenefit}
        onSave={handleBenefitSaveToCompany}
        context="job"
      />
    </section>
  )
}
