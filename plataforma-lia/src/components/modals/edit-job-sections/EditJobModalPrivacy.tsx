"use client"

import React from "react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import {
  Shield,
  Building,
  DollarSign,
  Heart,
} from "lucide-react"
import type { Job } from '../edit-job/edit-job.types'

interface EditJobModalPrivacyProps {
  formData: Partial<Job>
  updateField: (field: keyof Job, value: unknown) => void
}

export function EditJobModalPrivacy({
  formData,
  updateField,
}: EditJobModalPrivacyProps) {
  return (
    <section data-testid="edit-job-privacy-section">
      <div className="flex items-center gap-2 mb-4">
        <Shield className="w-4 h-4 text-lia-text-secondary" />
        <h3 className="text-base-ui font-semibold text-lia-text-primary">Configuração de Confidencialidade para LIA</h3>
      </div>
      
      <p className="text-xs text-lia-text-tertiary mb-3" aria-live="polite" aria-atomic="true">
        Configure o que a IA pode ou não revelar durante conversas com candidatos.
      </p>

      <div className="space-y-3">
        <div className="flex items-center justify-between p-2 bg-lia-bg-secondary rounded-xl">
          <div className="flex items-center gap-2">
            <Building className="w-3.5 h-3.5 text-lia-text-tertiary" />
            <span className="text-xs text-lia-text-secondary">LIA pode revelar o nome da empresa?</span>
          </div>
          <Switch
            checked={(formData.confidentialityConfig as Job['confidentialityConfig'])?.can_reveal_company_name ?? true}
            onCheckedChange={(checked: boolean) => {
              updateField('confidentialityConfig', {
                ...((formData.confidentialityConfig || {}) as Job['confidentialityConfig']),
                can_reveal_company_name: checked
              } as Job['confidentialityConfig'])
            }}
          />
        </div>

        {!(formData.confidentialityConfig as Job['confidentialityConfig'])?.can_reveal_company_name && (
          <div className="ml-4 p-2 bg-status-warning/10 rounded-xl border border-status-warning/30">
            <Label className="text-xs text-status-warning mb-1.5 block">
              Apresentação mascarada para candidatos:
            </Label>
            <Input
              value={(formData.confidentialityConfig as Job['confidentialityConfig'])?.masked_intro || ''}
              onChange={(e) => {
                updateField('confidentialityConfig', {
                  ...((formData.confidentialityConfig || {}) as Job['confidentialityConfig']),
                  masked_intro: e.target.value
                } as Job['confidentialityConfig'])
              }}
              className="h-8 text-xs bg-lia-bg-primary border-status-warning/30"
              placeholder="Uma empresa líder no segmento de pagamentos"
            />
          </div>
        )}

        <div className="flex items-center justify-between p-2 bg-lia-bg-secondary rounded-xl">
          <div className="flex items-center gap-2">
            <DollarSign className="w-3.5 h-3.5 text-lia-text-tertiary" />
            <span className="text-xs text-lia-text-secondary">LIA pode discutir faixa salarial?</span>
          </div>
          <Switch
            checked={(formData.confidentialityConfig as Job['confidentialityConfig'])?.can_discuss_salary ?? true}
            onCheckedChange={(checked: boolean) => {
              updateField('confidentialityConfig', {
                ...((formData.confidentialityConfig || {}) as Job['confidentialityConfig']),
                can_discuss_salary: checked
              } as Job['confidentialityConfig'])
            }}
          />
        </div>

        <div className="flex items-center justify-between p-2 bg-lia-bg-secondary rounded-xl">
          <div className="flex items-center gap-2">
            <Heart className="w-3.5 h-3.5 text-lia-text-tertiary" />
            <span className="text-xs text-lia-text-secondary">LIA pode discutir benefícios?</span>
          </div>
          <Switch
            checked={(formData.confidentialityConfig as Job['confidentialityConfig'])?.can_discuss_benefits ?? true}
            onCheckedChange={(checked: boolean) => {
              updateField('confidentialityConfig', {
                ...((formData.confidentialityConfig || {}) as Job['confidentialityConfig']),
                can_discuss_benefits: checked
              } as Job['confidentialityConfig'])
            }}
          />
        </div>
      </div>
    </section>
  )
}
