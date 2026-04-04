"use client"

import React from "react"
import { CURRENCY_SYMBOL } from "@/lib/pricing"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Plus, X } from "lucide-react"
import {
  inputClass,
  selectClass,
  labelClass,
  groupHeaderClass,
} from "./job-edit-tab.constants"
import { ScreeningBadge } from "./ScreeningBadge"

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
        <h3 className={groupHeaderClass}>Benefícios</h3>
        <Card className="border border-lia-border-subtle">
          <CardContent className="p-4">
            {(() => {
              const selectedBenefits: string[] = Array.isArray(jobEditForm.benefits)
                ? jobEditForm.benefits
                : typeof jobEditForm.benefits === "string" && jobEditForm.benefits
                ? (jobEditForm.benefits as string).split(",").map((b: string) => b.trim()).filter(Boolean)
                : []
              const companyBenefitNames = (((companyDefaults as Record<string, unknown>)?.benefits as Array<{ name: string }>) || []).map((b) => b.name)
              const allAvailable = [...new Set([...companyBenefitNames, ...selectedBenefits])]
              const toggleBenefit = (name: string) => {
                const updated = selectedBenefits.includes(name)
                  ? selectedBenefits.filter((b) => b !== name)
                  : [...selectedBenefits, name]
                updateField("benefits", updated)
              }
              return (
                <div className="space-y-3">
                  <label className={labelClass}>
                    Benefícios da Vaga
                    {companyBenefitNames.length > 0 && (
                      <span className="ml-1.5 text-micro text-wedo-cyan-dark font-normal">({companyBenefitNames.length} cadastrados na empresa)</span>
                    )}
                  </label>
                  {companyBenefitNames.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {allAvailable.map((name) => {
                        const isSelected = selectedBenefits.includes(name)
                        const isFromCompany = companyBenefitNames.includes(name)
                        return (
                          <button key={name} type="button" onClick={() => isEditing && toggleBenefit(name)} disabled={!isEditing} className={`px-3 py-1.5 rounded-md text-xs font-['Open_Sans',sans-serif] font-medium border transition-colors ${isSelected ? "bg-lia-btn-primary-bg text-lia-btn-primary-text border-lia-btn-primary-bg" : "bg-lia-bg-primary text-lia-text-secondary border-lia-border-subtle hover:border-lia-border-medium"} ${!isEditing ? "cursor-default opacity-75" : "cursor-pointer"}`}>
                            {isSelected ? "✓ " : ""}{name}
                            {!isFromCompany && <span className="ml-1 text-micro opacity-60">(custom)</span>}
                          </button>
                        )
                      })}
                    </div>
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      {selectedBenefits.map((name) => (
                        <span key={name} className="px-3 py-1.5 rounded-full text-xs font-['Open_Sans',sans-serif] font-medium bg-lia-btn-primary-bg text-lia-btn-primary-text flex items-center gap-1.5">
                          {name}
                          {isEditing && <button onClick={() => toggleBenefit(name)} className="hover:text-status-error"><X className="w-3 h-3" /></button>}
                        </span>
                      ))}
                    </div>
                  )}
                  {isEditing && (
                    <div className="flex gap-2">
                      <input type="text" className={`${inputClass(false)} flex-1`} placeholder="Adicionar benefício personalizado..." onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault()
                          const val = (e.target as HTMLInputElement).value.trim()
                          if (val && !selectedBenefits.includes(val)) {
                            updateField("benefits", [...selectedBenefits, val]);
                            (e.target as HTMLInputElement).value = ""
                          }
                        }
                      }} />
                    </div>
                  )}
                  {selectedBenefits.length === 0 && !isEditing && (
                    <p className="text-xs text-lia-text-tertiary font-['Open_Sans',sans-serif] italic">Nenhum benefício selecionado</p>
                  )}
                </div>
              )
            })()}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
