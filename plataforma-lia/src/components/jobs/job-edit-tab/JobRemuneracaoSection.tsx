"use client"

import React from "react"
import { CURRENCY_SYMBOL } from "@/lib/pricing"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  inputClass,
  selectClass,
  labelClass,
  groupHeaderClass,
} from "./job-edit-tab.constants"
import { ScreeningBadge } from "./ScreeningBadge"
import { VacancyBenefitsManager } from "@/components/benefits/VacancyBenefitsManager"
import { VacancyVariableCompManager } from "@/components/compensation/VacancyVariableCompManager"

interface JobRemuneracaoSectionProps {
  jobEditForm: Record<string, unknown>
  companyDefaults?: Record<string, unknown>
  isEditing: boolean
  updateField: (key: string, value: unknown) => void
}

export function JobRemuneracaoSection({
  jobEditForm,
  companyDefaults,
  isEditing,
  updateField,
}: JobRemuneracaoSectionProps) {
  return (
    <div className="space-y-5">
      <div>
        <h3 className={groupHeaderClass}>Faixa Salarial<ScreeningBadge /></h3>
        <Card className="border border-lia-border-subtle">
          <CardContent className="p-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelClass}>Mínimo</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-lia-text-tertiary">{CURRENCY_SYMBOL}</span>
                  <input type="number" className={`${inputClass(!isEditing)} pl-9`} value={(jobEditForm.salaryMin as string) || ""} onChange={(e) => updateField("salaryMin", e.target.value)} disabled={!isEditing} placeholder="0,00" />
                </div>
              </div>
              <div>
                <label className={labelClass}>Máximo</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-lia-text-tertiary">{CURRENCY_SYMBOL}</span>
                  <input type="number" className={`${inputClass(!isEditing)} pl-9`} value={(jobEditForm.salaryMax as string) || ""} onChange={(e) => updateField("salaryMax", e.target.value)} disabled={!isEditing} placeholder="0,00" />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      <div>
        <h3 className={groupHeaderClass}>Bônus / Variável</h3>
        <Card className="border border-lia-border-subtle">
          <CardContent className="p-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelClass}>Mínimo</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-lia-text-tertiary">{CURRENCY_SYMBOL}</span>
                  <input type="number" className={`${inputClass(!isEditing)} pl-9`} value={(jobEditForm.bonusMin as string) || ""} onChange={(e) => updateField("bonusMin", e.target.value)} disabled={!isEditing} placeholder="0,00" />
                </div>
              </div>
              <div>
                <label className={labelClass}>Máximo</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-lia-text-tertiary">{CURRENCY_SYMBOL}</span>
                  <input type="number" className={`${inputClass(!isEditing)} pl-9`} value={(jobEditForm.bonusMax as string) || ""} onChange={(e) => updateField("bonusMax", e.target.value)} disabled={!isEditing} placeholder="0,00" />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      <div>
        <VacancyVariableCompManager
          value={(jobEditForm.variable_compensation as unknown[]) || []}
          onChange={(next) => updateField("variable_compensation", next)}
          editable={isEditing}
          seniorityLevel={jobEditForm.level as string | undefined}
          department={jobEditForm.department as string | undefined}
          contractType={jobEditForm.type as string | undefined}
        />
      </div>
      <div>
        <VacancyBenefitsManager
          benefits={(jobEditForm.benefits as unknown[]) || []}
          onChange={(next) => updateField("benefits", next)}
          editable={isEditing}
          seniorityLevel={jobEditForm.level as string | undefined}
          department={jobEditForm.department as string | undefined}
          contractType={jobEditForm.type as string | undefined}
        />
      </div>
    </div>
  )
}
