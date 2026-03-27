"use client"

import React from "react"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { 
  Loader2,
  Tag,
  DollarSign,
  Wrench,
  Brain,
  MessageSquare,
  FileText,
  Lock,
  Pencil,
  Star,
  Building2,
  MapPin,
  Briefcase,
  User,
  Gift
} from "lucide-react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { BenefitBadgeList } from "@/components/benefits/BenefitBadgeList"
import { toCompanyBenefit, type CompanyBenefit } from "@/types/benefits"

export interface VacancyFullDetails {
  id: string
  title: string
  department: string
  location: string
  work_model: string
  employment_type: string
  salary_range: { min: number; max: number; bonus_min?: number; bonus_max?: number }
  benefits: (string | CompanyBenefit)[]
  technical_skills: Array<{ name: string; level: string; weight: number; required: boolean }>
  behavioral_competencies: Array<{ name: string; weight: number }>
  screening_questions: Array<{ question: string; type: string; expected_answer: any }>
  job_description: string
  manager: string
  manager_email: string
}

export interface VacancyFullSummaryProps {
  vacancy: VacancyFullDetails | null
  editableFields: string[]
  lockedFields: string[]
  isLoading?: boolean
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value)
}

function SectionHeader({ 
  icon: Icon, 
  title, 
  isLocked = false,
  iconColor = "text-gray-600 dark:text-gray-400"
}: { 
  icon: React.ElementType
  title: string
  isLocked?: boolean
  iconColor?: string
}) {
  return (
    <div className="flex items-center justify-between gap-2 mb-2">
      <div className="flex items-center gap-2">
        <Icon className={cn("h-4 w-4", iconColor)} />
        <span className="text-xs font-semibold text-gray-800 dark:text-white">{title}</span>
      </div>
      <Badge 
        variant="outline" 
        className={cn(
          "text-micro h-4 px-1.5 border",
          isLocked 
            ? "bg-gray-100 text-gray-600 border-gray-300 dark:bg-gray-800 dark:text-gray-400 dark:border-gray-600"
            : "bg-blue-50 text-blue-600 border-blue-200 dark:bg-blue-950/30 dark:text-blue-400 dark:border-blue-800"
        )}
      >
        {isLocked ? (
          <><Lock className="h-2.5 w-2.5 mr-0.5" /> Fixo</>
        ) : (
          <><Pencil className="h-2.5 w-2.5 mr-0.5" /> Editável</>
        )}
      </Badge>
    </div>
  )
}

function WeightStars({ weight }: { weight: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <Star
          key={i}
          className={cn(
            "h-2.5 w-2.5",
            i <= weight 
              ? "fill-amber-400 text-amber-400" 
              : "text-gray-300 dark:text-gray-600"
          )}
        />
      ))}
    </div>
  )
}

const LEVEL_CONFIG: Record<string, { label: string; className: string }> = {
  'Básico': { label: 'Básico', className: 'bg-green-50 text-green-700 border-green-200 dark:bg-green-950/30 dark:text-green-400 dark:border-green-800' },
  'Intermediário': { label: 'Intermediário', className: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/30 dark:text-amber-400 dark:border-amber-800' },
  'Avançado': { label: 'Avançado', className: 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/30 dark:text-red-400 dark:border-red-800' },
  'básico': { label: 'Básico', className: 'bg-green-50 text-green-700 border-green-200 dark:bg-green-950/30 dark:text-green-400 dark:border-green-800' },
  'intermediário': { label: 'Intermediário', className: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/30 dark:text-amber-400 dark:border-amber-800' },
  'avançado': { label: 'Avançado', className: 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/30 dark:text-red-400 dark:border-red-800' },
}

const WORK_MODEL_LABELS: Record<string, string> = {
  'remote': 'Remoto',
  'hybrid': 'Híbrido', 
  'onsite': 'Presencial',
  'remoto': 'Remoto',
  'híbrido': 'Híbrido',
  'presencial': 'Presencial',
}

const EMPLOYMENT_TYPE_LABELS: Record<string, string> = {
  'full_time': 'CLT - Tempo Integral',
  'part_time': 'CLT - Meio Período',
  'contract': 'PJ',
  'intern': 'Estágio',
  'clt': 'CLT',
  'pj': 'PJ',
  'estagio': 'Estágio',
}

export function VacancyFullSummary({
  vacancy,
  editableFields,
  lockedFields,
  isLoading = false
}: VacancyFullSummaryProps) {
  if (isLoading) {
    return (
      <div className="flex items-start gap-3 max-w-[85%]">
        <Avatar className="h-8 w-8 flex-shrink-0 border-2 border-gray-300 dark:border-gray-600">
          <AvatarImage src="/images/lia-avatar.png" alt="LIA" />
          <AvatarFallback className="bg-gradient-to-br from-gray-100 dark:from-gray-800 to-[#4FA3B4] text-white text-xs font-medium">
            LIA
          </AvatarFallback>
        </Avatar>
        <div className="rounded-2xl rounded-tl-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin text-gray-600 dark:text-gray-400" />
            <span className="text-sm text-muted-foreground">Carregando detalhes da vaga...</span>
          </div>
        </div>
      </div>
    )
  }

  if (!vacancy) return null

  const isFieldEditable = (field: string) => editableFields.includes(field)
  const isFieldLocked = (field: string) => lockedFields.includes(field)

  return (
    <div className="flex items-start gap-3 max-w-[95%]">
      <Avatar className="h-8 w-8 flex-shrink-0 border-2 border-gray-300 dark:border-gray-600">
        <AvatarImage src="/images/lia-avatar.png" alt="LIA" />
        <AvatarFallback className="bg-gradient-to-br from-gray-100 dark:from-gray-800 to-[#4FA3B4] text-white text-xs font-medium">
          LIA
        </AvatarFallback>
      </Avatar>

      <div className="flex-1 space-y-3">
        <div className="rounded-2xl rounded-tl-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-4 space-y-4">
          <div className="pb-2 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-sm font-bold text-gray-800 dark:text-white">{vacancy.title}</h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              Resumo completo da vaga baseada em processo anterior
            </p>
          </div>

          <div className="space-y-4">
            <div>
              <SectionHeader icon={Tag} title="🏷️ Informações Básicas" isLocked={isFieldLocked('basic_info')} />
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="flex items-center gap-1.5 p-2 rounded bg-gray-50 dark:bg-gray-900">
                  <Building2 className="h-3 w-3 text-muted-foreground" />
                  <span className="text-muted-foreground">Área:</span>
                  <span className="font-medium">{vacancy.department}</span>
                </div>
                <div className="flex items-center gap-1.5 p-2 rounded bg-gray-50 dark:bg-gray-900">
                  <MapPin className="h-3 w-3 text-muted-foreground" />
                  <span className="text-muted-foreground">Local:</span>
                  <span className="font-medium">{vacancy.location}</span>
                </div>
                <div className="flex items-center gap-1.5 p-2 rounded bg-gray-50 dark:bg-gray-900">
                  <Briefcase className="h-3 w-3 text-muted-foreground" />
                  <span className="text-muted-foreground">Modelo:</span>
                  <span className="font-medium">{WORK_MODEL_LABELS[vacancy.work_model.toLowerCase()] || vacancy.work_model}</span>
                </div>
                <div className="flex items-center gap-1.5 p-2 rounded bg-gray-50 dark:bg-gray-900">
                  <Briefcase className="h-3 w-3 text-muted-foreground" />
                  <span className="text-muted-foreground">Contrato:</span>
                  <span className="font-medium">{EMPLOYMENT_TYPE_LABELS[vacancy.employment_type.toLowerCase()] || vacancy.employment_type}</span>
                </div>
                <div className="flex items-center gap-1.5 p-2 rounded bg-gray-50 dark:bg-gray-900 col-span-2">
                  <User className="h-3 w-3 text-muted-foreground" />
                  <span className="text-muted-foreground">Gestor:</span>
                  <span className="font-medium">{vacancy.manager}</span>
                  <span className="text-muted-foreground">({vacancy.manager_email})</span>
                </div>
              </div>
            </div>

            <div>
              <SectionHeader icon={DollarSign} title="💵 Remuneração" isLocked={isFieldLocked('compensation')} />
              <div className="space-y-2">
                <div className="flex items-center gap-2 p-2 rounded bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800">
                  <DollarSign className="h-4 w-4 text-green-600 dark:text-green-400" />
                  <div className="flex-1">
                    <p className="text-micro text-muted-foreground">Faixa Salarial</p>
                    <p className="text-xs font-semibold text-green-700 dark:text-green-400">
                      {formatCurrency(vacancy.salary_range.min)} - {formatCurrency(vacancy.salary_range.max)}
                    </p>
                  </div>
                </div>
                {(vacancy.salary_range.bonus_min || vacancy.salary_range.bonus_max) && (
                  <div className="flex items-center gap-2 p-2 rounded bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800">
                    <DollarSign className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                    <div className="flex-1">
                      <p className="text-micro text-muted-foreground">Bônus</p>
                      <p className="text-xs font-semibold text-blue-700 dark:text-blue-400">
                        {vacancy.salary_range.bonus_min ? formatCurrency(vacancy.salary_range.bonus_min) : 'N/A'} - {vacancy.salary_range.bonus_max ? formatCurrency(vacancy.salary_range.bonus_max) : 'N/A'}
                      </p>
                    </div>
                  </div>
                )}
                {vacancy.benefits.length > 0 && (
                  <div>
                    <SectionHeader icon={Gift} title="🎁 Benefícios" isLocked={isFieldLocked('benefits')} />
                    <BenefitBadgeList
                      benefits={vacancy.benefits.map(b => typeof b === 'string' ? toCompanyBenefit(b) : b as CompanyBenefit)}
                      maxVisible={8}
                      size="sm"
                      showCategory={true}
                    />
                  </div>
                )}
              </div>
            </div>

            <div>
              <SectionHeader icon={Wrench} title="🔧 Competências Técnicas" isLocked={true} iconColor="text-gray-600 dark:text-gray-400" />
              <div className="space-y-1.5 max-h-[150px] overflow-y-auto pr-1">
                {vacancy.technical_skills.map((skill, idx) => {
                  const levelConfig = LEVEL_CONFIG[skill.level] || LEVEL_CONFIG['Intermediário']
                  return (
                    <div key={idx} className="flex items-center justify-between gap-2 p-2 rounded bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700">
                      <div className="flex items-center gap-2 min-w-0">
                        <Wrench className="h-3 w-3 text-gray-600 dark:text-gray-400 flex-shrink-0" />
                        <span className="text-xs font-medium truncate">{skill.name}</span>
                        {skill.required && (
                          <Badge variant="outline" className="text-micro h-3.5 px-1 border-red-300 bg-red-50 text-red-700 dark:border-red-700 dark:bg-red-950/30 dark:text-red-400">
                            Req
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <Badge variant="outline" className={cn("text-micro h-3.5 px-1 border", levelConfig.className)}>
                          {levelConfig.label}
                        </Badge>
                        <WeightStars weight={skill.weight} />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            <div>
              <SectionHeader icon={Brain} title="🧠 Competências Comportamentais" isLocked={true} iconColor="text-purple-500" />
              <div className="space-y-1.5 max-h-[120px] overflow-y-auto pr-1">
                {vacancy.behavioral_competencies.map((comp, idx) => (
                  <div key={idx} className="flex items-center justify-between gap-2 p-2 rounded bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-2 min-w-0">
                      <Brain className="h-3 w-3 text-purple-500 flex-shrink-0" />
                      <span className="text-xs font-medium truncate">{comp.name}</span>
                    </div>
                    <WeightStars weight={comp.weight} />
                  </div>
                ))}
              </div>
            </div>

            <div>
              <SectionHeader icon={MessageSquare} title="📱 Perguntas de Triagem WSI" isLocked={true} iconColor="text-orange-500" />
              <div className="space-y-1.5 max-h-[120px] overflow-y-auto pr-1">
                {vacancy.screening_questions.map((q, idx) => (
                  <div key={idx} className="p-2 rounded bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700">
                    <p className="text-xs text-gray-800 dark:text-white">{idx + 1}. {q.question}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant="secondary" className="text-micro h-3.5 px-1">
                        {q.type === 'yes-no' ? 'Sim/Não' : q.type === 'multiple-choice' ? 'Múltipla escolha' : q.type === 'numeric' ? 'Numérico' : 'Aberta'}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <SectionHeader icon={FileText} title="📝 Job Description" isLocked={isFieldLocked('job_description')} iconColor="text-gray-500" />
              <div className="p-2 rounded bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 max-h-[100px] overflow-y-auto">
                <p className="text-xs text-muted-foreground whitespace-pre-wrap">
                  {vacancy.job_description}
                </p>
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
            <div className="p-3 rounded-md bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600">
              <p className="text-xs text-gray-800 dark:text-white leading-relaxed">
                <span className="font-semibold">📌 O que você pode fazer:</span>
              </p>
              <ul className="text-xs text-muted-foreground mt-1.5 space-y-1">
                <li>• Se quiser <span className="font-medium text-gray-600 dark:text-gray-400">confirmar e publicar</span>, digite <span className="font-mono bg-gray-200 dark:bg-gray-700 px-1 rounded">'confirmar'</span></li>
                <li>• Se quiser <span className="font-medium text-gray-600 dark:text-gray-400">fazer ajustes</span>, me diga o que quer mudar</li>
              </ul>
              <p className="text-micro text-muted-foreground mt-2 italic">
                Exemplos: "salário para 18 a 23k", "modelo híbrido", "adicionar benefício vale alimentação"
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default VacancyFullSummary
