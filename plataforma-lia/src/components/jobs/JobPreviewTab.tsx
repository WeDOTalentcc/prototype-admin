"use client"

import { formatBRL } from"@/lib/pricing"

import React, { useState } from"react"
import {
  FileText,
  Zap,
  Heart,
  Globe,
  DollarSign,
  Layers3,
  ClipboardList,
  CalendarCheck,
  MessageSquare,
  ChevronRight,
} from"lucide-react"
import { Chip } from "@/components/ui/chip"
import { BenefitBadgeList } from"@/components/benefits/BenefitBadgeList"
import { kindLabel } from "@/components/compensation/variable-comp-types"
import { toCompanyBenefit, type CompanyBenefit } from"@/types/benefits"

interface JobPreviewTabProps {
  job: {
    title?: string
    department?: string
    location?: string
    workModel?: string
    type?: string
    level?: string
    description?: string
    requirements?: string[]
    benefits?: Array<{name: string; category?: string}> | string[]
    languages?: Array<{language: string; level?: string; required?: boolean}>
    salaryRange?: {min?: number; max?: number}
    salaryMin?: number | string
    salaryMax?: number | string
    bonusRange?: {min?: number; max?: number}
    bonus_range?: {min?: number; max?: number}
    bonusMin?: number | string
    bonusMax?: number | string
    interviewStages?: Array<{stageName: string; stageCategory?: string; order?: number; liaAssisted?: boolean; color?: string; slaDays?: number}>
    behavioralCompetencies?: Array<{competency?: string; name?: string; weight?: number}> | string[]
    technicalCompetencies?: Array<{competency?: string; name?: string; weight?: number}> | string[]
    screeningQuestions?: Array<{ time_limit?: number; [key: string]: unknown }>
    screeningConfig?: {
      status?: { enabled?: boolean }
      channels?: { whatsapp?: { enabled?: boolean }; chat_web?: { enabled?: boolean }; phone?: { enabled?: boolean } }
      scheduling?: { enabled?: boolean; minScore?: number; calendar?: string; hours?: string; duration?: string }
      minApprovalScore?: number
      timeout?: string
      retries?: string
      fallback?: string
    }
    funnel?: {total: number; screening: number; interview: number; final: number; hired: number}
    nps?: number
    isAffirmative?: boolean
    affirmativeCriteriaPrimary?: string
    affirmativeType?: string
    [key: string]: unknown
  }
  pipelineStages?: Array<{id: string; name: string; count: number; color?: string; liaAssisted?: boolean}>
}

function formatCurrency(value: number | string | undefined): string {
  if (value === undefined || value === null || value ==="") return""
  const num = typeof value ==="string" ? parseFloat(value) : value
  if (isNaN(num)) return""
  return `${formatBRL(num)}`
}

function getCompetencyName(item: {competency?: string; name?: string; weight?: number} | string): string {
  if (typeof item ==="string") return item
  return item.competency || item.name ||""
}

export function JobPreviewTab({ job, pipelineStages }: JobPreviewTabProps) {
  const [showFullDescription, setShowFullDescription] = useState(false)

  const description = job.description ||""
  const truncatedDescription = description.length > 300 && !showFullDescription
    ? description.slice(0, 300) +"..."
    : description

  const technicalItems = job.requirements && job.requirements.length > 0
    ? job.requirements
    : (job.technicalCompetencies || [])

  const behavioralItems = job.behavioralCompetencies || []

  const salaryMin = job.salaryRange?.min ?? job.salaryMin
  const salaryMax = job.salaryRange?.max ?? job.salaryMax
  const hasSalary = salaryMin || salaryMax

  const bonusMin = job.bonusRange?.min ?? job.bonus_range?.min ?? job.bonusMin
  const bonusMax = job.bonusRange?.max ?? job.bonus_range?.max ?? job.bonusMax
  const hasBonus = bonusMin || bonusMax

  const benefits = job.benefits

  const normalizedBenefits: CompanyBenefit[] = React.useMemo(() => {
    const benefitsList = benefits || []
    return benefitsList.map((b: string | { name?: string; category?: string; value_type?: string }) => {
      if (typeof b === 'string') return toCompanyBenefit(b)
      if (b.category && b.value_type) return b as CompanyBenefit
      return toCompanyBenefit(String(b.name || ''))
    })
  }, [benefits])

  const questions = job.screeningQuestions || []
  const screeningConfig = job.screeningConfig || {}
  const screeningEnabled = screeningConfig?.status?.enabled ?? true
  const totalTime = questions.reduce((acc: number, q: { time_limit?: number }) => acc + (q.time_limit || 120), 0)
  const estimatedMinutes = Math.ceil(totalTime / 60)

  const channels: string[] = []
  if (screeningConfig?.channels?.whatsapp?.enabled) channels.push("WhatsApp")
  if (screeningConfig?.channels?.chat_web?.enabled) channels.push("Chat Web")
  if (screeningConfig?.channels?.phone?.enabled) channels.push("Telefone")

  const schedulingEnabled = screeningConfig?.scheduling?.enabled ?? false

  return (
    <div className="space-y-4">
      <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-xl">
        <h5 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5 mb-2">
          <FileText className="w-3.5 h-3.5 text-lia-text-secondary" />
          Descricao da Vaga
        </h5>
        {description ? (
          <div>
            <p className="text-micro text-lia-text-secondary leading-relaxed whitespace-pre-line">
              {truncatedDescription}
            </p>
            {description.length > 300 && (
              <button
                onClick={() => setShowFullDescription(!showFullDescription)}
                className="text-micro text-lia-text-primary font-medium mt-1 hover:underline"
              >
                {showFullDescription ?"Ver menos" :"Ver mais"}
              </button>
            )}
          </div>
        ) : (
          <p className="text-micro text-lia-text-secondary italic">
            Nenhuma descricao adicionada
          </p>
        )}
      </div>

      <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-xl">
        <h5 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5 mb-2">
          <Zap className="w-3.5 h-3.5 text-lia-text-secondary" />
          Competencias Tecnicas
        </h5>
        {technicalItems.length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            {technicalItems.map((item: {competency?: string; name?: string; weight?: number} | string, idx: number) => (
              <Chip variant="neutral" muted key={`tech-${idx}`} className="bg-lia-bg-tertiary text-lia-text-secondary text-micro px-2 py-0.5 h-5 font-medium">
                {getCompetencyName(item)}
              </Chip>
            ))}
          </div>
        ) : (
          <p className="text-micro text-lia-text-secondary italic">
            Nenhuma competencia tecnica configurada
          </p>
        )}
      </div>

      <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-xl">
        <h5 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5 mb-2">
          <Heart className="w-3.5 h-3.5 text-lia-text-secondary" />
          Competencias Comportamentais
        </h5>
        {behavioralItems.length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            {behavioralItems.map((item: {competency?: string; name?: string; weight?: number} | string, idx: number) => (
              <Chip variant="neutral" muted key={`behav-${idx}`} className="border border-wedo-purple/30 text-micro px-2 py-0.5 h-5 font-medium">
                {getCompetencyName(item)}
              </Chip>
            ))}
          </div>
        ) : (
          <p className="text-micro text-lia-text-secondary italic">
            Nenhuma competencia comportamental configurada
          </p>
        )}
      </div>

      <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-xl">
        <h5 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5 mb-2">
          <Globe className="w-3.5 h-3.5 text-lia-text-secondary" />
          Idiomas
        </h5>
        {job.languages && job.languages.length > 0 ? (
          <div className="space-y-1.5">
            {job.languages.map((lang, idx) => (
              <div key={`lang-${idx}`} className="flex items-center gap-2">
                <span className="text-micro text-lia-text-secondary font-medium">
                  {lang.language}
                </span>
                {lang.level && (
                  <Chip variant="neutral" muted className="text-micro px-1.5 py-0 h-4 flex items-center bg-lia-bg-tertiary text-lia-text-primary">
                    {lang.level}
                  </Chip>
                )}
                {lang.required && (
                  <Chip variant="danger" muted className="text-micro px-1.5 py-0 h-4 flex items-center">
                    Obrigatorio
                  </Chip>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-micro text-lia-text-secondary italic">
            Nenhum idioma configurado
          </p>
        )}
      </div>

      <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-xl">
        <h5 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5 mb-2">
          <DollarSign className="w-3.5 h-3.5 text-lia-text-secondary" />
          Remuneracao e Beneficios
        </h5>
        <div className="space-y-2">
          {hasSalary ? (
            <div className="flex items-center gap-1.5">
              <span className="text-micro text-lia-text-secondary">Salario:</span>
              <span className="text-micro font-medium text-lia-text-primary">
                {formatCurrency(salaryMin)}{salaryMax ? ` - ${formatCurrency(salaryMax)}` :""}
              </span>
            </div>
          ) : (
            <p className="text-micro text-lia-text-secondary italic">
              Faixa salarial nao informada
            </p>
          )}
          {hasBonus && (
            <div className="flex items-center gap-1.5">
              <span className="text-micro text-lia-text-secondary">Bonus:</span>
              <span className="text-micro font-medium text-lia-text-primary">
                {formatCurrency(bonusMin)}{bonusMax ? ` - ${formatCurrency(bonusMax)}` :""}
              </span>
            </div>
          )}
          {Array.isArray((job as { variable_compensation?: unknown[] }).variable_compensation) &&
            ((job as { variable_compensation?: unknown[] }).variable_compensation as unknown[]).length > 0 && (
            <div>
              <span className="text-micro text-lia-text-secondary block mb-1">Remuneração variável:</span>
              <div className="flex flex-wrap gap-1.5">
                {((job as { variable_compensation?: Array<Record<string, unknown>> }).variable_compensation || []).map((vc, i) => (
                  <span key={i} className="inline-flex items-center gap-1 rounded-full bg-lia-bg-secondary border border-lia-border-subtle px-2 py-0.5 text-micro text-lia-text-primary">
                    <span className="text-lia-text-tertiary">{kindLabel(String(vc.kind || "bonus"))}:</span> {String(vc.name || "")}
                  </span>
                ))}
              </div>
            </div>
          )}
          {normalizedBenefits.length > 0 && (
            <div>
              <span className="text-micro text-lia-text-secondary block mb-1">Beneficios:</span>
              <BenefitBadgeList
                benefits={normalizedBenefits}
                maxVisible={6}
                size="sm"
                showCategory={true}
              />
            </div>
          )}
        </div>
      </div>

      <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-xl">
        <h5 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5 mb-2">
          <Layers3 className="w-3.5 h-3.5 text-lia-text-secondary" />
          Etapas do Processo
        </h5>
        {pipelineStages && pipelineStages.length > 0 ? (
          <div className="flex items-center gap-1 overflow-x-auto pb-1">
            {pipelineStages.map((stage, idx) => (
              <React.Fragment key={stage.id}>
                {idx > 0 && (
                  <ChevronRight className="w-3 h-3 text-lia-text-disabled flex-shrink-0" />
                )}
                <div className="flex items-center gap-1 px-2 py-1 bg-lia-bg-secondary border border-lia-border-subtle rounded-lg flex-shrink-0">
                  {stage.liaAssisted && (
                    <span className="w-1.5 h-1.5 rounded-full bg-wedo-cyan flex-shrink-0" />
                  )}
                  <span className="text-micro font-medium text-lia-text-primary">{stage.name}</span>
                  <Chip variant="neutral" muted className="text-micro px-1 py-0 h-3.5 bg-lia-bg-tertiary text-lia-text-secondary">
                    {stage.count}
                  </Chip>
                </div>
              </React.Fragment>
            ))}
          </div>
        ) : job.interviewStages && job.interviewStages.length > 0 ? (
          <div className="flex items-center gap-1 overflow-x-auto pb-1">
            {job.interviewStages
              .sort((a, b) => (a.order || 0) - (b.order || 0))
              .map((stage, idx) => (
                <React.Fragment key={`stage-${idx}`}>
                  {idx > 0 && (
                    <ChevronRight className="w-3 h-3 text-lia-text-disabled flex-shrink-0" />
                  )}
                  <div className="flex items-center gap-1 px-2 py-1 bg-lia-bg-secondary border border-lia-border-subtle rounded-lg flex-shrink-0">
                    {stage.liaAssisted && (
                      <span className="w-1.5 h-1.5 rounded-full bg-wedo-cyan flex-shrink-0" />
                    )}
                    <span className="text-micro font-medium text-lia-text-primary">{stage.stageName}</span>
                  </div>
                </React.Fragment>
              ))}
          </div>
        ) : (
          <p className="text-micro text-lia-text-secondary italic">
            Nenhuma etapa configurada
          </p>
        )}
      </div>

      {job.isAffirmative && (
        <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-xl">
          <h5 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5 mb-2">
            <Heart className="w-3.5 h-3.5 text-lia-text-secondary" />
            Acoes Afirmativas
          </h5>
          <div className="p-2 bg-wedo-purple/10 border border-wedo-purple/30 rounded-lg">
            {job.affirmativeType && (
              <div className="flex items-center gap-1.5 mb-1">
                <span className="text-micro text-lia-text-secondary">Tipo:</span>
                <Chip variant="neutral" muted className="text-micro px-1.5 py-0 h-4 flex items-center  border border-wedo-purple/30">
                  {job.affirmativeType}
                </Chip>
              </div>
            )}
            {job.affirmativeCriteriaPrimary && (
              <div className="flex items-center gap-1.5">
                <span className="text-micro text-lia-text-secondary">Criterio:</span>
                <span className="text-micro font-medium text-lia-text-primary">
                  {job.affirmativeCriteriaPrimary}
                </span>
              </div>
            )}
            {!job.affirmativeType && !job.affirmativeCriteriaPrimary && (
              <p className="text-micro text-lia-text-secondary">
                Vaga afirmativa habilitada
              </p>
            )}
          </div>
        </div>
      )}

      <div className="border-t border-lia-border-subtle" />

      <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-xl">
        <h5 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5 mb-2">
          <ClipboardList className="w-3.5 h-3.5 text-lia-text-secondary" />
          Fluxo de Triagem WSI
          <Chip variant="neutral" muted
            className={`text-micro px-1.5 py-0 h-4 flex items-center text-lia-text-primary ${screeningEnabled ?"bg-wedo-green-pastel" :"bg-lia-interactive-active"}`}
          >
            {screeningEnabled ?"Ativo" :"Pausado"}
          </Chip>
        </h5>
        <div className="grid grid-cols-2 gap-2">
          <div className="text-center p-2 bg-lia-bg-secondary rounded-lg">
            <div className="text-base-ui font-semibold text-lia-text-primary">{questions.length}</div>
            <p className="text-micro text-lia-text-secondary">Perguntas</p>
          </div>
          <div className="text-center p-2 bg-lia-bg-secondary rounded-lg">
            <div className="text-base-ui font-semibold text-lia-text-primary">{estimatedMinutes}min</div>
            <p className="text-micro text-lia-text-secondary">Tempo Est.</p>
          </div>
        </div>
        <p className="text-micro text-lia-text-tertiary mt-2">
          Gerencie o roteiro na aba Detalhes da Vaga
        </p>
      </div>

      <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-xl">
        <h5 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5 mb-2">
          <CalendarCheck className="w-3.5 h-3.5 text-lia-text-secondary" />
          Agendamento
          <Chip variant="neutral" muted
            className={`text-micro px-1.5 py-0 h-4 flex items-center text-lia-text-primary ${schedulingEnabled ?"bg-wedo-green-pastel" :"bg-lia-interactive-active"}`}
          >
            {schedulingEnabled ?"Ativo" :"Inativo"}
          </Chip>
        </h5>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <span className="text-micro text-lia-text-secondary">Score Minimo</span>
            <p className="text-micro font-medium text-lia-text-primary">{screeningConfig?.scheduling?.minScore || 'Recomendado'}</p>
          </div>
          <div>
            <span className="text-micro text-lia-text-secondary">Calendario</span>
            <p className="text-micro font-medium text-lia-text-primary">{screeningConfig?.scheduling?.calendar || 'Outlook'}</p>
          </div>
          <div>
            <span className="text-micro text-lia-text-secondary">Horarios</span>
            <p className="text-micro font-medium text-lia-text-primary">{screeningConfig?.scheduling?.hours || '9h-18h'}</p>
          </div>
          <div>
            <span className="text-micro text-lia-text-secondary">Duracao</span>
            <p className="text-micro font-medium text-lia-text-primary">{screeningConfig?.scheduling?.duration || '45min'}</p>
          </div>
        </div>
      </div>

      <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-xl">
        <h5 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1.5 mb-2">
          <MessageSquare className="w-3.5 h-3.5 text-lia-text-secondary" />
          Canais de Comunicacao
        </h5>
        {channels.length > 0 ? (
          <div className="flex flex-wrap gap-1.5 mb-2">
            {channels.map((ch, idx) => (
              <Chip variant="neutral" muted key={`ch-${idx}`} className="text-micro px-1.5 py-0 h-4 flex items-center bg-lia-bg-tertiary text-lia-text-primary">
                {ch}
              </Chip>
            ))}
          </div>
        ) : (
          <p className="text-micro text-lia-text-secondary italic mb-2">
            Nenhum canal configurado
          </p>
        )}
        <div className="grid grid-cols-2 gap-2">
          <div>
            <span className="text-micro text-lia-text-secondary">Score Minimo Aprovacao</span>
            <p className="text-micro font-medium text-lia-text-primary">{screeningConfig?.minApprovalScore || 'Recomendado'}</p>
          </div>
          <div>
            <span className="text-micro text-lia-text-secondary">Timeout Resposta</span>
            <p className="text-micro font-medium text-lia-text-primary">{screeningConfig?.timeout || '24h'}</p>
          </div>
          <div>
            <span className="text-micro text-lia-text-secondary">Re-tentativas</span>
            <p className="text-micro font-medium text-lia-text-primary">{screeningConfig?.retries || '2x'}</p>
          </div>
          <div>
            <span className="text-micro text-lia-text-secondary">Fallback</span>
            <p className="text-micro font-medium text-lia-text-primary">{screeningConfig?.fallback || 'Revisao Manual'}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
