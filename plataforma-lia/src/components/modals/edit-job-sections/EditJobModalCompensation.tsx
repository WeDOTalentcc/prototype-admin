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
import { VacancyBenefitsManager } from '@/components/benefits/VacancyBenefitsManager'

interface EditJobModalCompensationProps {
  formData: Partial<Job>
  setFormData: React.Dispatch<React.SetStateAction<Partial<Job>>>
  activeCompensationPolicies: { id: string; name: string; policy_type?: string }[]
  /** INT:005 — triggers LIA chat with apply_compensation_policy intent */
  onSuggestWithLIA?: () => void
}

export function EditJobModalCompensation({
  formData,
  setFormData,
  activeCompensationPolicies,
  onSuggestWithLIA,
}: EditJobModalCompensationProps) {
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
          <VacancyBenefitsManager
            benefits={(formData.benefits || []) as unknown[]}
            onChange={(next) => setFormData(prev => ({ ...prev, benefits: next as unknown as typeof prev.benefits }))}
            seniorityLevel={formData.seniority as string | undefined}
            department={formData.department as string | undefined}
            contractType={(formData as { type?: string }).type}
          />
        </div>
      </div>

    </section>
  )
}
