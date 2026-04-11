"use client"
import React from "react"
import NextImage from "next/image"
import { Image, Building2, Calendar, Users } from "lucide-react"
import { CompanyDataCard, SimpleDataCard } from "../CompanyDataCard"
import {
  INDUSTRIES,
  INDUSTRY_CATEGORIES,
  type IndustryCategory,
} from "@/lib/industry-constants"

const inputClass = (disabled: boolean) =>
  `w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:ring-lia-btn-primary-bg/10 focus:border-lia-btn-primary-bg dark:focus:ring-lia-border-subtle/10 dark:focus:border-lia-border-subtle transition-colors ${disabled ? "opacity-60 cursor-not-allowed bg-lia-bg-secondary dark:bg-lia-bg-primary" : ""}`

const selectClass = (disabled: boolean) =>
  `w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:ring-lia-btn-primary-bg/10 focus:border-lia-btn-primary-bg dark:focus:ring-lia-border-subtle/10 dark:focus:border-lia-border-subtle transition-colors ${disabled ? "opacity-60 cursor-not-allowed bg-lia-bg-secondary dark:bg-lia-bg-primary" : ""}`

interface GeneralInfoSectionProps {
  companyData: Record<string, any>
  setCompanyData: React.Dispatch<React.SetStateAction<Record<string, any>>>
  isEditing: boolean
  updateLiaToggle: (key: string, value: boolean) => void
  updateLiaInstruction: (key: string, value: string) => void
}

export function GeneralInfoSection({
  companyData,
  setCompanyData,
  isEditing,
  updateLiaToggle,
  updateLiaInstruction,
}: GeneralInfoSectionProps) {
  return (
    <div className="space-y-3">
      <h3 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wider px-1 font-['Open_Sans',sans-serif]">
        Informações Gerais
      </h3>
      <div className="grid grid-cols-1 gap-3">
        {/* Logo */}
        <div className="inline-flex items-center gap-3 bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-md px-4 py-3 w-fit">
          <div className="relative w-14 h-14 rounded-xl bg-lia-bg-tertiary dark:bg-lia-bg-secondary border-2 border-dashed border-lia-border-default flex items-center justify-center cursor-pointer hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none hover:border-lia-btn-primary-bg dark:hover:border-lia-border-subtle flex-shrink-0 overflow-hidden">
            {companyData.logo ? (
              <NextImage src={companyData.logo} alt="Logo" fill className="object-cover rounded-md" />
            ) : (
              <div className="text-center">
                <Image className="w-5 h-5 mx-auto text-lia-text-tertiary mb-0.5" />
                <span className="text-micro text-lia-text-secondary font-['Open_Sans',sans-serif]">Upload</span>
              </div>
            )}
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-medium text-lia-text-primary font-['Open_Sans',sans-serif]">Logo da Empresa</span>
            <span className="text-micro text-lia-text-secondary bg-lia-bg-tertiary dark:bg-lia-bg-elevated px-1.5 py-0.5 rounded-full font-['Open_Sans',sans-serif]">Identidade Visual</span>
          </div>
        </div>

        <SimpleDataCard label="Razão Social" category="Registro" isEditing={isEditing}>
          <input type="text" value={companyData.name} onChange={(e) => setCompanyData((prev) => ({ ...prev, name: e.target.value }))} disabled={!isEditing} className={inputClass(!isEditing)} placeholder="Nome legal da empresa" />
        </SimpleDataCard>

        <CompanyDataCard fieldKey="trade_name" label="Nome Fantasia" category="Informações da Empresa" isActive={companyData.lia_field_toggles?.trade_name ?? true} currentInstruction={companyData.lia_instructions?.trade_name || ""} isEditing={isEditing} onToggleChange={updateLiaToggle} onInstructionSave={updateLiaInstruction}>
          <input type="text" value={companyData.tradeName || ""} onChange={(e) => setCompanyData((prev) => ({ ...prev, tradeName: e.target.value }))} disabled={!isEditing} className={inputClass(!isEditing)} placeholder="Nome comercial da empresa" />
        </CompanyDataCard>

        <SimpleDataCard label="CNPJ" category="Registro" isEditing={isEditing}>
          <input type="text" value={companyData.cnpj || ""} onChange={(e) => setCompanyData((prev) => ({ ...prev, cnpj: e.target.value }))} disabled={!isEditing} className={inputClass(!isEditing)} placeholder="00.000.000/0000-00" />
        </SimpleDataCard>

        <CompanyDataCard fieldKey="industry" label="Setor/Indústria" category="Informações da Empresa" isActive={companyData.lia_field_toggles?.industry ?? true} currentInstruction={companyData.lia_instructions?.industry || ""} isEditing={isEditing} onToggleChange={updateLiaToggle} onInstructionSave={updateLiaInstruction}>
          <select value={companyData.industry || ""} onChange={(e) => setCompanyData((prev) => ({ ...prev, industry: e.target.value }))} disabled={!isEditing} className={selectClass(!isEditing)}>
            <option value="">Selecione o setor...</option>
            {(Object.keys(INDUSTRY_CATEGORIES) as IndustryCategory[]).map((category) => (
              <optgroup key={category} label={INDUSTRY_CATEGORIES[category].labelPt}>
                {INDUSTRIES.filter((ind) => ind.category === category).map((ind) => (
                  <option key={ind.key} value={ind.labelPt}>{ind.labelPt}</option>
                ))}
              </optgroup>
            ))}
          </select>
        </CompanyDataCard>
      </div>
    </div>
  )
}
