"use client"

import React from"react"
import { Chip } from "@/components/ui/chip"
import { cn } from"@/lib/utils"
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
} from"lucide-react"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import { BenefitBadgeList } from"@/components/benefits/BenefitBadgeList"
import { toCompanyBenefit, type CompanyBenefit } from"@/types/benefits"

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
  screening_questions: Array<{ question: string; type: string; expected_answer: unknown }>
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
  iconColor ="text-lia-text-secondary"
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
        <span className="text-xs font-semibold text-lia-text-primary dark:text-white">{title}</span>
      </div>
      <Chip 
        variant="neutral" 
        className={cn("text-micro h-4 px-1.5 border",
          isLocked 
            ?"bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-default"
            :"-dark border-wedo-cyan/30 dark:border-wedo-cyan/30"
        )}
      >
        {isLocked ? (
          <><Lock className="h-2.5 w-2.5 mr-0.5" /> Fixo</>
        ) : (
          <><Pencil className="h-2.5 w-2.5 mr-0.5" /> Editável</>
        )}
      </Chip>
    </div>
  )
}

function WeightStars({ weight }: { weight: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <Star
          key={i}
          className={cn("h-2.5 w-2.5",
            i <= weight 
              ?"fill-amber-400 text-status-warning" 
              :"text-lia-text-disabled"
          )}
        />
      ))}
    </div>
  )
}

const LEVEL_CONFIG: Record<string, { label: string; className: string }> = {
  'Básico': { label: 'Básico', className: ' border-status-success/30 dark:bg-status-success/30 dark:border-status-success/30' },
  'Intermediário': { label: 'Intermediário', className: ' border-status-warning/30 dark:bg-status-warning/30 dark:border-status-warning/30' },
  'Avançado': { label: 'Avançado', className: ' border-status-error/30 dark:bg-status-error/30 dark:text-status-error dark:border-status-error/30' },
  'básico': { label: 'Básico', className: ' border-status-success/30 dark:bg-status-success/30 dark:border-status-success/30' },
  'intermediário': { label: 'Intermediário', className: ' border-status-warning/30 dark:bg-status-warning/30 dark:border-status-warning/30' },
  'avançado': { label: 'Avançado', className: ' border-status-error/30 dark:bg-status-error/30 dark:text-status-error dark:border-status-error/30' },
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
        <Avatar className="h-8 w-8 flex-shrink-0 border-2 border-lia-border-default">
          <AvatarImage src="/images/lia-avatar.png" alt="LIA" />
          <AvatarFallback className="bg-gradient-to-br from-lia-bg-tertiary dark:from-lia-bg-tertiary to-wedo-cyan-dark text-white text-xs font-medium">
            LIA
          </AvatarFallback>
        </Avatar>
        <div className="rounded-xl rounded-tl-sm bg-lia-bg-primary border border-lia-border-subtle p-4" role="status" aria-live="polite" aria-label="Carregando...">
          <div className="flex items-center gap-2" role="status" aria-live="polite" aria-label="Carregando...">
            <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
            <span className="text-sm text-lia-text-tertiary" aria-live="polite" aria-atomic="true">Carregando detalhes da vaga...</span>
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
      <Avatar className="h-8 w-8 flex-shrink-0 border-2 border-lia-border-default">
        <AvatarImage src="/images/lia-avatar.png" alt="LIA" />
        <AvatarFallback className="bg-gradient-to-br from-lia-bg-tertiary dark:from-lia-bg-tertiary to-wedo-cyan-dark text-white text-xs font-medium">
          LIA
        </AvatarFallback>
      </Avatar>

      <div className="flex-1 space-y-3">
        <div className="rounded-xl rounded-tl-sm bg-lia-bg-primary border border-lia-border-subtle p-4 space-y-4">
          <div className="pb-2">
            <h3 className="text-sm font-semibold text-lia-text-primary dark:text-white">{vacancy.title}</h3>
            <p className="text-xs text-lia-text-tertiary mt-0.5" aria-live="polite" aria-atomic="true">
              Resumo completo da vaga baseada em processo anterior
            </p>
          </div>

          <div className="space-y-4">
            <div>
              <SectionHeader icon={Tag} title="🏷️ Informações Básicas" isLocked={isFieldLocked('basic_info')} />
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="flex items-center gap-1.5 p-2 rounded-xl bg-lia-bg-secondary">
                  <Building2 className="h-3 w-3 text-lia-text-tertiary" />
                  <span className="text-lia-text-tertiary">Área:</span>
                  <span className="font-medium">{vacancy.department}</span>
                </div>
                <div className="flex items-center gap-1.5 p-2 rounded-xl bg-lia-bg-secondary">
                  <MapPin className="h-3 w-3 text-lia-text-tertiary" />
                  <span className="text-lia-text-tertiary">Local:</span>
                  <span className="font-medium">{vacancy.location}</span>
                </div>
                <div className="flex items-center gap-1.5 p-2 rounded-xl bg-lia-bg-secondary">
                  <Briefcase className="h-3 w-3 text-lia-text-tertiary" />
                  <span className="text-lia-text-tertiary">Modelo:</span>
                  <span className="font-medium">{WORK_MODEL_LABELS[vacancy.work_model.toLowerCase()] || vacancy.work_model}</span>
                </div>
                <div className="flex items-center gap-1.5 p-2 rounded-xl bg-lia-bg-secondary">
                  <Briefcase className="h-3 w-3 text-lia-text-tertiary" />
                  <span className="text-lia-text-tertiary">Contrato:</span>
                  <span className="font-medium">{EMPLOYMENT_TYPE_LABELS[vacancy.employment_type.toLowerCase()] || vacancy.employment_type}</span>
                </div>
                <div className="flex items-center gap-1.5 p-2 rounded-xl bg-lia-bg-secondary col-span-2">
                  <User className="h-3 w-3 text-lia-text-tertiary" />
                  <span className="text-lia-text-tertiary">Gestor:</span>
                  <span className="font-medium">{vacancy.manager}</span>
                  <span className="text-lia-text-tertiary">({vacancy.manager_email})</span>
                </div>
              </div>
            </div>

            <div>
              <SectionHeader icon={DollarSign} title="💵 Remuneração" isLocked={isFieldLocked('compensation')} />
              <div className="space-y-2">
                <div className="flex items-center gap-2 p-2 rounded-xl bg-status-success/10 dark:bg-status-success/30 border border-status-success/30 dark:border-status-success/30">
                  <DollarSign className="h-4 w-4 text-status-success" />
                  <div className="flex-1">
                    <p className="text-micro text-lia-text-tertiary">Faixa Salarial</p>
                    <p className="text-xs font-semibold text-status-success">
                      {formatCurrency(vacancy.salary_range.min)} - {formatCurrency(vacancy.salary_range.max)}
                    </p>
                  </div>
                </div>
                {(vacancy.salary_range.bonus_min || vacancy.salary_range.bonus_max) && (
                  <div className="flex items-center gap-2 p-2 rounded-xl bg-wedo-cyan/10 border border-wedo-cyan/30 dark:border-wedo-cyan/30">
                    <DollarSign className="h-4 w-4 text-wedo-cyan-dark" />
                    <div className="flex-1">
                      <p className="text-micro text-lia-text-tertiary">Bônus</p>
                      <p className="text-xs font-semibold text-wedo-cyan-text">
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
              <SectionHeader icon={Wrench} title="🔧 Competências Técnicas" isLocked={true} iconColor="text-lia-text-secondary" />
              <div className="space-y-1.5 max-h-[150px] overflow-y-auto pr-1">
                {vacancy.technical_skills.map((skill, idx) => {
                  const levelConfig = LEVEL_CONFIG[skill.level] || LEVEL_CONFIG['Intermediário']
                  return (
                    <div key={idx} className="flex items-center justify-between gap-2 p-2 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle">
                      <div className="flex items-center gap-2 min-w-0">
                        <Wrench className="h-3 w-3 text-lia-text-secondary flex-shrink-0" />
                        <span className="text-xs font-medium truncate">{skill.name}</span>
                        {skill.required && (
                          <Chip variant="danger" className="text-micro h-3.5 px-1 dark:bg-status-error/30">
                            Req
                          </Chip>
                        )}
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <Chip variant="neutral" className={cn("text-micro h-3.5 px-1 border", levelConfig.className)}>
                          {levelConfig.label}
                        </Chip>
                        <WeightStars weight={skill.weight} />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            <div>
              <SectionHeader icon={Brain} title="🧠 Competências Comportamentais" isLocked={true} iconColor="text-wedo-purple" />
              <div className="space-y-1.5 max-h-[120px] overflow-y-auto pr-1">
                {vacancy.behavioral_competencies.map((comp, idx) => (
                  <div key={idx} className="flex items-center justify-between gap-2 p-2 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle">
                    <div className="flex items-center gap-2 min-w-0">
                      <Brain className="h-3 w-3 text-wedo-purple flex-shrink-0" />
                      <span className="text-xs font-medium truncate">{comp.name}</span>
                    </div>
                    <WeightStars weight={comp.weight} />
                  </div>
                ))}
              </div>
            </div>

            <div>
              <SectionHeader icon={MessageSquare} title="📱 Perguntas de Triagem WSI" isLocked={true} iconColor="text-wedo-orange" />
              <div className="space-y-1.5 max-h-[120px] overflow-y-auto pr-1">
                {vacancy.screening_questions.map((q, idx) => (
                  <div key={idx} className="p-2 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle">
                    <p className="text-xs text-lia-text-primary dark:text-white">{idx + 1}. {q.question}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <Chip variant="neutral" muted className="text-micro h-3.5 px-1">
                        {q.type === 'yes-no' ? 'Sim/Não' : q.type === 'multiple-choice' ? 'Múltipla escolha' : q.type === 'numeric' ? 'Numérico' : 'Aberta'}
                      </Chip>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <SectionHeader icon={FileText} title="📝 Job Description" isLocked={isFieldLocked('job_description')} iconColor="lia-text-secondary" />
              <div className="p-2 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle max-h-[100px] overflow-y-auto">
                <p className="text-xs text-lia-text-tertiary whitespace-pre-wrap">
                  {vacancy.job_description}
                </p>
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-lia-border-subtle">
            <div className="p-3 rounded-xl bg-lia-bg-tertiary border border-lia-border-default">
              <p className="text-xs text-lia-text-primary dark:text-white leading-relaxed">
                <span className="font-semibold">📌 O que você pode fazer:</span>
              </p>
              <ul className="text-xs text-lia-text-tertiary mt-1.5 space-y-1">
                <li>• Se quiser <span className="font-medium text-lia-text-secondary">confirmar e publicar</span>, digite <span className="font-mono bg-lia-interactive-active px-1 rounded-md">'confirmar'</span></li>
                <li>• Se quiser <span className="font-medium text-lia-text-secondary">fazer ajustes</span>, me diga o que quer mudar</li>
              </ul>
              <p className="text-micro text-lia-text-tertiary mt-2 italic">
                Exemplos:"salário para 18 a 23k","modelo híbrido","adicionar benefício vale alimentação"
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default VacancyFullSummary
