"use client"


import { CURRENCY_SYMBOL } from"@/lib/pricing"
import React, { useState, useEffect } from"react"
import { cn } from"@/lib/utils"
import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Input } from"@/components/ui/input"
import { Chip } from "@/components/ui/chip"
import { Progress } from"@/components/ui/progress"
import { ScrollArea } from"@/components/ui/scroll-area"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from"@/components/ui/collapsible"
import { ConfidenceIndicator } from"./confidence-indicator"
import type { CompanyBenefit } from"@/types/benefits"
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Info,
  ChevronDown,
  ChevronRight,
  Brain,
  Building,
  TrendingUp,
  Loader2,
  Send,
} from"lucide-react"

export interface FieldSuggestion {
  value: unknown
  source:"company_history" |"company_defaults" |"market_benchmark"
  confidence: number
  explanation: string
}

export interface FieldDetail {
  category: string
  label: string
  status:"filled" |"missing" |"toggled_off"
  value: unknown
}

export interface CompletenessResult {
  filled_fields: string[]
  missing_critical: string[]
  missing_important: string[]
  toggled_off: string[]
  can_publish: boolean
  completeness_score: number
  field_details: Record<string, FieldDetail>
  suggestions: Record<string, FieldSuggestion>
}

export interface JobData {
  title?: string
  seniority_level?: string
  department?: string
  salary_range?: { min: number; max: number; currency: string }
  benefits?: (string | CompanyBenefit)[]
  technical_requirements?: Record<string, unknown>[]
  behavioral_competencies?: Record<string, unknown>[]
  work_model?: string
  location?: string
  employment_type?: string
  description?: string
  requirements?: string[]
  languages?: Record<string, unknown>[]
  manager?: string
  deadline?: string
  [key: string]: unknown
}

interface FinalReviewPanelProps {
  jobData: JobData
  completenessResult: CompletenessResult
  onFieldEdit: (field: string, value: unknown) => void
  onPublish: () => void
  isPublishing?: boolean
  companyId?: string
}

const FIELD_LABELS: Record<string, string> = {
  job_title:"Título da Vaga",
  seniority:"Senioridade",
  department:"Departamento",
  salary_range:"Faixa Salarial",
  benefits:"Benefícios",
  tech_stack:"Tech Stack",
  behavioral_competencies:"Competências Comportamentais",
  work_model:"Modelo de Trabalho",
  location:"Localização",
  employment_type:"Tipo de Contratação",
  description:"Descrição da Vaga",
  requirements:"Requisitos",
  languages:"Idiomas",
  manager:"Gestor",
  deadline:"Prazo",
}

const SOURCE_LABELS: Record<string, { label: string; icon: typeof Building; color: string }> = {
  company_history: {
    label:"Histórico da empresa",
    icon: TrendingUp,
    color:"text-wedo-cyan-text",
  },
  company_defaults: {
    label:"Configuração padrão",
    icon: Building,
    color:"text-wedo-purple-text",
  },
  market_benchmark: {
    label:"Referência de mercado",
    icon: Brain,
    color:"text-status-warning",
  },
}

function getFieldLabel(fieldKey: string, fieldDetails?: Record<string, FieldDetail>): string {
  if (fieldDetails?.[fieldKey]?.label) {
    return fieldDetails[fieldKey].label
  }
  return FIELD_LABELS[fieldKey] || fieldKey
}

function formatFieldValue(fieldKey: string, value: unknown): string {
  if (value === null || value === undefined) return"-"
  
  if (fieldKey ==="salary_range" && typeof value ==="object") {
    const { min, max, currency } = value as { min?: number; max?: number; currency?: string }
    return `${currency || CURRENCY_SYMBOL} ${min?.toLocaleString()} - ${max?.toLocaleString()}`
  }
  
  if (fieldKey ==="benefits" && Array.isArray(value)) {
    if (value.length === 0) return"-"
    return value.map((b: unknown) => typeof b === 'string' ? b : (b as Record<string, unknown>).name).join(",")
  }
  
  if (Array.isArray(value)) {
    if (value.length === 0) return"-"
    if (typeof value[0] ==="object" && value[0]?.competency) {
      return value.map((v) => v.competency).join(",")
    }
    return value.slice(0, 5).join(",") + (value.length > 5 ? ` +${value.length - 5}` :"")
  }
  
  if (typeof value ==="object") {
    return JSON.stringify(value)
  }
  
  return String(value)
}

function MissingFieldCard({
  fieldKey,
  label,
  suggestion,
  onUseSuggestion,
  onManualEdit,
}: {
  fieldKey: string
  label: string
  suggestion?: FieldSuggestion
  onUseSuggestion: (value: unknown) => void
  onManualEdit: (value: unknown) => void
}) {
  const [manualValue, setManualValue] = useState("")
  const [showInput, setShowInput] = useState(false)

  const sourceInfo = suggestion ? SOURCE_LABELS[suggestion.source] : null
  const SourceIcon = sourceInfo?.icon || Brain

  return (
    <div className="border rounded-xl p-3 bg-lia-bg-primary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <div className="font-medium text-sm text-lia-text-primary">{label}</div>
          
          {suggestion && (
            <div className="mt-2">
              <div className="flex items-center gap-2 text-xs text-lia-text-tertiary mb-1">
                <SourceIcon className={cn("h-3 w-3", sourceInfo?.color)} />
                <span className={sourceInfo?.color}>{sourceInfo?.label}</span>
                <ConfidenceIndicator confidence={suggestion.confidence} size="sm" showPercentage />
              </div>
              
              <div className="bg-lia-bg-secondary rounded-xl p-2 text-sm text-lia-text-secondary">
                <div className="font-medium">{formatFieldValue(fieldKey, suggestion.value)}</div>
                <div className="text-xs text-lia-text-tertiary mt-1">{suggestion.explanation}</div>
              </div>
              
              <Button
                size="sm"
                variant="outline"
                className="mt-2 text-xs h-7 hover:bg-lia-interactive-hover"
                onClick={() => onUseSuggestion(suggestion.value)}
              >
                <Brain className="h-3 w-3 mr-1 text-wedo-cyan" />
                Usar Sugestão
              </Button>
            </div>
          )}
          
          {!suggestion && !showInput && (
            <Button
              size="sm"
              variant="ghost"
              className="mt-2 text-xs h-7 hover:bg-lia-interactive-hover"
              onClick={() => setShowInput(true)}
            >
              Preencher manualmente
            </Button>
          )}
          
          {showInput && (
            <div className="mt-2 flex gap-2">
              <Input
                value={manualValue}
                onChange={(e) => setManualValue(e.target.value)}
                placeholder={`Informe ${label.toLowerCase()}`}
                className="text-sm h-8"
              />
              <Button
                size="sm"
                className="h-8 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
                onClick={() => {
                  onManualEdit(manualValue)
                  setShowInput(false)
                  setManualValue("")
                }}
              >
                Salvar
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function FilledFieldCard({
  fieldKey,
  label,
  value,
}: {
  fieldKey: string
  label: string
  value: unknown
}) {
  return (
    <div className="flex items-center justify-between py-2 last:border-0">
      <span className="text-sm text-lia-text-secondary">{label}</span>
      <span className="text-sm font-medium text-lia-text-primary max-w-[60%] truncate text-right">
        {formatFieldValue(fieldKey, value)}
      </span>
    </div>
  )
}

export function FinalReviewPanel({
  jobData,
  completenessResult,
  onFieldEdit,
  onPublish,
  isPublishing = false,
  companyId,
}: FinalReviewPanelProps) {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    critical: true,
    important: true,
    filled: false,
    toggled_off: false,
  })

  const {
    filled_fields,
    missing_critical,
    missing_important,
    toggled_off,
    can_publish,
    completeness_score,
    field_details,
    suggestions,
  } = completenessResult

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }))
  }

  const handleUseSuggestion = (fieldKey: string, value: unknown) => {
    onFieldEdit(fieldKey, value)
  }

  const handleManualEdit = (fieldKey: string, value: unknown) => {
    onFieldEdit(fieldKey, value)
  }

  const getScoreColor = () => {
    if (completeness_score >= 80) return"bg-status-success"
    if (completeness_score >= 60) return"bg-status-warning"
    return"bg-status-error"
  }

  return (
    <Card className="border-0 rounded-md">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold font-sans">Revisão Final</CardTitle>
          <Chip
            density="relaxed"
            variant="neutral"
            className={cn(
              can_publish ?"border-status-success/30 text-status-success" :"border-status-error/30 text-status-error"
            )}
          >
            {can_publish ?"Pronto para publicar" :"Campos obrigatórios pendentes"}
          </Chip>
        </div>
        
        <div className="mt-3">
          <div className="flex items-center justify-between text-sm mb-1.5">
            <span className="text-lia-text-secondary">Completude</span>
            <span className="font-semibold">{completeness_score}%</span>
          </div>
          <Progress value={completeness_score} className={cn("h-2", getScoreColor())} />
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <ScrollArea className="max-h-content-lg pr-2">
          {missing_critical.length > 0 && (
            <Collapsible
              open={expandedSections.critical}
              onOpenChange={() => toggleSection("critical")}
              className="mb-4"
            >
              <CollapsibleTrigger className="flex items-center justify-between w-full p-2 rounded-md bg-status-error/10 dark:bg-status-error/30 hover:bg-status-error/15 dark:hover:bg-status-error/50 transition-colors motion-reduce:transition-none">
                <div className="flex items-center gap-2">
                  <XCircle className="h-4 w-4 text-status-error dark:text-status-error" />
                  <span className="font-medium text-status-error dark:text-status-error">
                    Campos Críticos Faltantes ({missing_critical.length})
                  </span>
                </div>
                {expandedSections.critical ? (
                  <ChevronDown className="h-4 w-4 text-status-error" />
                ) : (
                  <ChevronRight className="h-4 w-4 text-status-error" />
                )}
              </CollapsibleTrigger>
              <CollapsibleContent className="mt-2 space-y-2">
                {missing_critical.map((fieldKey) => (
                  <MissingFieldCard
                    key={fieldKey}
                    fieldKey={fieldKey}
                    label={getFieldLabel(fieldKey, field_details)}
                    suggestion={suggestions[fieldKey]}
                    onUseSuggestion={(value) => handleUseSuggestion(fieldKey, value)}
                    onManualEdit={(value) => handleManualEdit(fieldKey, value)}
                  />
                ))}
              </CollapsibleContent>
            </Collapsible>
          )}

          {missing_important.length > 0 && (
            <Collapsible
              open={expandedSections.important}
              onOpenChange={() => toggleSection("important")}
              className="mb-4"
            >
              <CollapsibleTrigger className="flex items-center justify-between w-full p-2 rounded-md bg-status-warning/10 dark:bg-status-warning/30 hover:bg-status-warning/15 dark:hover:bg-status-warning/50 transition-colors motion-reduce:transition-none">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-status-warning" />
                  <span className="font-medium text-status-warning">
                    Campos Importantes Faltantes ({missing_important.length})
                  </span>
                </div>
                {expandedSections.important ? (
                  <ChevronDown className="h-4 w-4 text-status-warning" />
                ) : (
                  <ChevronRight className="h-4 w-4 text-status-warning" />
                )}
              </CollapsibleTrigger>
              <CollapsibleContent className="mt-2 space-y-2">
                {missing_important.map((fieldKey) => (
                  <MissingFieldCard
                    key={fieldKey}
                    fieldKey={fieldKey}
                    label={getFieldLabel(fieldKey, field_details)}
                    suggestion={suggestions[fieldKey]}
                    onUseSuggestion={(value) => handleUseSuggestion(fieldKey, value)}
                    onManualEdit={(value) => handleManualEdit(fieldKey, value)}
                  />
                ))}
              </CollapsibleContent>
            </Collapsible>
          )}

          {filled_fields.length > 0 && (
            <Collapsible
              open={expandedSections.filled}
              onOpenChange={() => toggleSection("filled")}
              className="mb-4"
            >
              <CollapsibleTrigger className="flex items-center justify-between w-full p-2 rounded-md bg-status-success/10 dark:bg-status-success/30 hover:bg-status-success/15 dark:hover:bg-status-success/50 transition-colors motion-reduce:transition-none">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-status-success" />
                  <span className="font-medium text-status-success">
                    Campos Preenchidos ({filled_fields.length})
                  </span>
                </div>
                {expandedSections.filled ? (
                  <ChevronDown className="h-4 w-4 text-status-success" />
                ) : (
                  <ChevronRight className="h-4 w-4 text-status-success" />
                )}
              </CollapsibleTrigger>
              <CollapsibleContent className="mt-2">
                <div className="bg-lia-bg-primary rounded-xl border p-3">
                  {filled_fields.map((fieldKey) => (
                    <FilledFieldCard
                      key={fieldKey}
                      fieldKey={fieldKey}
                      label={getFieldLabel(fieldKey, field_details)}
                      value={field_details[fieldKey]?.value || jobData[fieldKey]}
                    />
                  ))}
                </div>
              </CollapsibleContent>
            </Collapsible>
          )}

          {toggled_off.length > 0 && (
            <Collapsible
              open={expandedSections.toggled_off}
              onOpenChange={() => toggleSection("toggled_off")}
              className="mb-4"
            >
              <CollapsibleTrigger className="flex items-center justify-between w-full p-2 rounded-xl bg-lia-bg-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none">
                <div className="flex items-center gap-2">
                  <Info className="h-4 w-4 text-lia-text-tertiary" />
                  <span className="font-medium text-lia-text-secondary">
                    Campos Desativados ({toggled_off.length})
                  </span>
                </div>
                {expandedSections.toggled_off ? (
                  <ChevronDown className="h-4 w-4 text-lia-text-secondary" />
                ) : (
                  <ChevronRight className="h-4 w-4 text-lia-text-secondary" />
                )}
              </CollapsibleTrigger>
              <CollapsibleContent className="mt-2">
                <div className="bg-lia-bg-primary rounded-xl border p-3 text-sm text-lia-text-tertiary">
                  <p className="mb-2">
                    Estes campos foram desativados nas configurações da empresa:
                  </p>
                  <ul className="list-disc list-inside space-y-1">
                    {toggled_off.map((fieldKey) => (
                      <li key={fieldKey}>{getFieldLabel(fieldKey, field_details)}</li>
                    ))}
                  </ul>
                </div>
              </CollapsibleContent>
            </Collapsible>
          )}
        </ScrollArea>

        <div className="pt-3 border-t border-lia-border-subtle">
          <Button
            className="w-full bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
            size="lg"
            disabled={!can_publish || isPublishing}
            onClick={onPublish}
          >
            {isPublishing ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin motion-reduce:animate-none" />
                Publicando...
              </>
            ) : (
              <>
                <Send className="mr-2 h-4 w-4" />
                Publicar Vaga
              </>
            )}
          </Button>
          
          {!can_publish && (
            <p className="text-xs text-center text-status-error dark:text-status-error mt-2" aria-live="polite" aria-atomic="true">
              Preencha todos os campos críticos para publicar a vaga
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export default FinalReviewPanel
