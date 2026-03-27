"use client"

import React, { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Loader2, Stethoscope, Car, GraduationCap, Wallet, Home, Baby,
  Shield as ShieldIcon, Utensils, Heart, Clock, DollarSign
} from "lucide-react"
import { useCompanyBenefits } from '@/hooks/useCompanyBenefits'
import type { JobBenefit, BenefitCategory } from '@/types/benefits'
import { BENEFIT_CATEGORY_META } from '@/types/benefits'
import { BENEFITS_CATALOG, CompensationData } from "../types"

const CATEGORY_ICONS: Record<string, any> = {
  health: Stethoscope,
  food: Utensils,
  transport: Car,
  education: GraduationCap,
  financial: Wallet,
  quality_life: Home,
  family: Baby,
  security: ShieldIcon,
}

interface PanelProps {
  initialData?: Record<string, unknown>
  onSubmit: (data: unknown) => Promise<void>
  isLoading?: boolean
}

function formatCurrency(value: string): string {
  const numericValue = value.replace(/\D/g, "")
  if (!numericValue) return ""
  const number = parseInt(numericValue, 10) / 100
  return number.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL"
  })
}

function parseCurrency(value: string): number {
  const numericValue = value.replace(/\D/g, "")
  if (!numericValue) return 0
  return parseInt(numericValue, 10) / 100
}

function CurrencyInput({
  value,
  onChange,
  placeholder,
  id
}: {
  value: number
  onChange: (value: number) => void
  placeholder?: string
  id?: string
}) {
  const [displayValue, setDisplayValue] = useState(
    value > 0 ? formatCurrency((value * 100).toString()) : ""
  )

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const rawValue = e.target.value
    const formatted = formatCurrency(rawValue)
    setDisplayValue(formatted)
    onChange(parseCurrency(rawValue))
  }

  useEffect(() => {
    if (value > 0) {
      setDisplayValue(formatCurrency((value * 100).toString()))
    }
  }, [value])

  return (
    <Input
      id={id}
      value={displayValue}
      onChange={handleChange}
      placeholder={placeholder || "R$ 0,00"}
      className="text-right dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100"
    />
  )
}

export function CompensationBenefitsPanel({
  initialData = {},
  onSubmit,
  isLoading = false
}: PanelProps) {
  const [salaryMin, setSalaryMin] = useState<number>(
    (initialData.salary_min as number) || 0
  )
  const [salaryMax, setSalaryMax] = useState<number>(
    (initialData.salary_max as number) || 0
  )
  const [bonusMin, setBonusMin] = useState<number>(
    (initialData.bonus_min as number) || 0
  )
  const [bonusMax, setBonusMax] = useState<number>(
    (initialData.bonus_max as number) || 0
  )
  const [bonusCriteria, setBonusCriteria] = useState<string>(
    (initialData.bonus_criteria as string) || ""
  )
  const { benefits: companyBenefits, isLoading: isLoadingBenefits } = useCompanyBenefits()
  const [benefits, setBenefits] = useState<JobBenefit[]>(() => {
    const initialBenefits = initialData.benefits as JobBenefit[] | undefined
    if (initialBenefits && Array.isArray(initialBenefits)) {
      return initialBenefits.map(b => ({ ...b, enabled: b.enabled !== undefined ? b.enabled : true }))
    }
    return BENEFITS_CATALOG.map((b) => ({ ...b }))
  })
  const [observations, setObservations] = useState<string>(
    (initialData.observations as string) || ""
  )

  useEffect(() => {
    if (companyBenefits.length > 0) {
      setBenefits(prev => {
        const isUsingCatalog = prev.every(b => BENEFITS_CATALOG.some(cb => cb.id === b.id))
        if (!isUsingCatalog) return prev

        return companyBenefits.map(cb => ({
          ...cb,
          enabled: prev.find(p => p.name === cb.name)?.enabled || false
        }))
      })
    }
  }, [companyBenefits])

  const handleBenefitToggle = (benefitIdOrName: string) => {
    setBenefits((prev) =>
      prev.map((b) =>
        (b.id === benefitIdOrName || b.name === benefitIdOrName) ? { ...b, enabled: !b.enabled } : b
      )
    )
  }

  const handleBenefitValueChange = (benefitIdOrName: string, value: string) => {
    setBenefits((prev) =>
      prev.map((b) => (b.id === benefitIdOrName || b.name === benefitIdOrName) ? { ...b, value_details: value } : b)
    )
  }

  const handleSubmit = async () => {
    const data: CompensationData = {
      salary_min: salaryMin,
      salary_max: salaryMax,
      bonus_min: bonusMin || undefined,
      bonus_max: bonusMax || undefined,
      bonus_criteria: bonusCriteria || undefined,
      benefits: benefits.filter((b) => b.enabled),
      observations: observations || undefined
    }
    await onSubmit(data)
  }

  const categorizedBenefits = React.useMemo(() => {
    const groups: Record<string, JobBenefit[]> = {}
    for (const b of benefits) {
      const cat = b.category || 'quality_life'
      if (!groups[cat]) groups[cat] = []
      groups[cat].push(b)
    }
    return groups
  }, [benefits])

  return (
    <div className="space-y-6">
      <Card className="rounded-md dark:bg-gray-800 dark:border-gray-700">
        <CardHeader className="pb-3 border-b border-gray-200 dark:border-gray-700">
          <CardTitle className="text-sm flex items-center gap-2 font-sans dark:text-gray-100">
            💵 Salário Base (CLT)
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="salary_min" className="dark:text-gray-300">Mínimo</Label>
              <CurrencyInput
                id="salary_min"
                value={salaryMin}
                onChange={setSalaryMin}
                placeholder="R$ 0,00"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="salary_max" className="dark:text-gray-300">Máximo</Label>
              <CurrencyInput
                id="salary_max"
                value={salaryMax}
                onChange={setSalaryMax}
                placeholder="R$ 0,00"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="rounded-md dark:bg-gray-800 dark:border-gray-700">
        <CardHeader className="pb-3 border-b border-gray-200 dark:border-gray-700">
          <CardTitle className="text-sm flex items-center gap-2 font-sans dark:text-gray-100">
            🎯 Bônus / Variável
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="bonus_min" className="dark:text-gray-300">Mínimo</Label>
              <CurrencyInput
                id="bonus_min"
                value={bonusMin}
                onChange={setBonusMin}
                placeholder="R$ 0,00"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="bonus_max" className="dark:text-gray-300">Máximo</Label>
              <CurrencyInput
                id="bonus_max"
                value={bonusMax}
                onChange={setBonusMax}
                placeholder="R$ 0,00"
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="bonus_criteria" className="dark:text-gray-300">Critérios de Elegibilidade</Label>
            <Textarea
              id="bonus_criteria"
              value={bonusCriteria}
              onChange={(e) => setBonusCriteria(e.target.value)}
              placeholder="Ex: Atingimento de metas individuais e coletivas, tempo mínimo de 6 meses na empresa..."
              rows={3}
              className="dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100"
            />
          </div>
        </CardContent>
      </Card>

      <Card className="rounded-md dark:bg-gray-800 dark:border-gray-700">
        <CardHeader className="pb-3 border-b border-gray-200 dark:border-gray-700">
          <CardTitle className="text-sm flex items-center gap-2 font-sans dark:text-gray-100">
            🎁 Benefícios
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {isLoadingBenefits && benefits.length === 0 ? (
            <div className="flex items-center gap-2 py-4">
              <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
              <span className="text-sm text-muted-foreground">Carregando benefícios...</span>
            </div>
          ) : (
            Object.entries(categorizedBenefits).map(([categoryId, categoryBenefits]) => {
              const meta = BENEFIT_CATEGORY_META[categoryId as BenefitCategory]
              const CategoryIcon = CATEGORY_ICONS[categoryId] || Home
              if (!meta || categoryBenefits.length === 0) return null

              return (
                <div key={categoryId} className="space-y-3">
                  <Label className="text-xs font-semibold text-muted-foreground dark:text-gray-400 uppercase tracking-wide flex items-center gap-1.5">
                    <CategoryIcon className="w-3.5 h-3.5" />
                    {meta.name}
                  </Label>
                  <div className="space-y-2">
                    {categoryBenefits.map((benefit) => (
                      <BenefitRow
                        key={benefit.id || benefit.name}
                        benefit={benefit}
                        onToggle={() => handleBenefitToggle(benefit.id || benefit.name)}
                        onValueChange={(value) =>
                          handleBenefitValueChange(benefit.id || benefit.name, value)
                        }
                      />
                    ))}
                  </div>
                </div>
              )
            })
          )}
        </CardContent>
      </Card>

      <Card className="rounded-md dark:bg-gray-800 dark:border-gray-700">
        <CardHeader className="pb-3 border-b border-gray-200 dark:border-gray-700">
          <CardTitle className="text-sm flex items-center gap-2 font-sans dark:text-gray-100">
            📝 Observações
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Textarea
            value={observations}
            onChange={(e) => setObservations(e.target.value)}
            placeholder="Informações adicionais sobre a remuneração ou benefícios..."
            rows={4}
            className="dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100"
          />
        </CardContent>
      </Card>

      <Button
        onClick={handleSubmit}
        disabled={isLoading}
        className="w-full bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
        size="lg"
      >
        {isLoading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin mr-2" />
            Salvando...
          </>
        ) : (
          "Concluído"
        )}
      </Button>
    </div>
  )
}

function BenefitRow({
  benefit,
  onToggle,
  onValueChange
}: {
  benefit: JobBenefit
  onToggle: () => void
  onValueChange: (value: string) => void
}) {
  const valueDisplay = benefit.value_type === 'monetary' && benefit.value
    ? `R$ ${benefit.value.toLocaleString('pt-BR')}`
    : benefit.value_type === 'percentage' && benefit.percentage_value
    ? `${benefit.percentage_value}%`
    : ''

  return (
    <div className="flex items-center gap-3 py-1">
      <Checkbox
        id={benefit.id || benefit.name}
        checked={benefit.enabled}
        onCheckedChange={onToggle}
      />
      <Label
        htmlFor={benefit.id || benefit.name}
        className="flex-1 cursor-pointer text-sm font-normal dark:text-gray-300"
      >
        <span>{benefit.name}</span>
        {benefit.is_mandatory && (
          <span className="ml-1 text-micro px-1 py-0 rounded-full bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400">obrig.</span>
        )}
        {benefit.is_highlighted && (
          <Heart className="inline w-3 h-3 ml-1 text-pink-500 fill-pink-500" />
        )}
      </Label>
      {benefit.enabled && (
        <div className="flex items-center gap-2">
          {valueDisplay ? (
            <span className="text-xs text-muted-foreground dark:text-gray-400 whitespace-nowrap">
              {valueDisplay}
            </span>
          ) : (
            <Input
              value={benefit.value_details || ""}
              onChange={(e) => onValueChange(e.target.value)}
              placeholder="Valor"
              className="w-24 h-8 text-xs dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100"
            />
          )}
          {benefit.provider && (
            <span className="text-micro text-muted-foreground dark:text-gray-400 whitespace-nowrap">
              {benefit.provider}
            </span>
          )}
        </div>
      )}
    </div>
  )
}
