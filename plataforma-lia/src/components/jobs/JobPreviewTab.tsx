"use client"

import React, { useState } from "react"
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
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { BenefitBadgeList } from "@/components/benefits/BenefitBadgeList"
import { toCompanyBenefit, type CompanyBenefit } from "@/types/benefits"

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
    screeningQuestions?: any[]
    screeningConfig?: any
    funnel?: {total: number; screening: number; interview: number; final: number; hired: number}
    nps?: number
    isAffirmative?: boolean
    affirmativeCriteriaPrimary?: string
    affirmativeType?: string
    [key: string]: any
  }
  pipelineStages?: Array<{id: string; name: string; count: number; color?: string}>
}

function formatCurrency(value: number | string | undefined): string {
  if (value === undefined || value === null || value === "") return ""
  const num = typeof value === "string" ? parseFloat(value) : value
  if (isNaN(num)) return ""
  return `R$ ${num.toLocaleString("pt-BR", { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
}

function getCompetencyName(item: {competency?: string; name?: string; weight?: number} | string): string {
  if (typeof item === "string") return item
  return item.competency || item.name || ""
}

export function JobPreviewTab({ job, pipelineStages }: JobPreviewTabProps) {
  const [showFullDescription, setShowFullDescription] = useState(false)

  const description = job.description || ""
  const truncatedDescription = description.length > 300 && !showFullDescription
    ? description.slice(0, 300) + "..."
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

  const benefits = job.benefits || []

  const normalizedBenefits: CompanyBenefit[] = React.useMemo(() => {
    return benefits.map((b: any) => {
      if (typeof b === 'string') return toCompanyBenefit(b)
      if (b.category && b.value_type) return b as CompanyBenefit
      return toCompanyBenefit(b)
    })
  }, [benefits])

  const questions = job.screeningQuestions || []
  const screeningConfig = job.screeningConfig || {}
  const screeningEnabled = screeningConfig?.status?.enabled ?? true
  const totalTime = questions.reduce((acc: number, q: any) => acc + (q.time_limit || 120), 0)
  const estimatedMinutes = Math.ceil(totalTime / 60)

  const channels: string[] = []
  if (screeningConfig?.channels?.whatsapp?.enabled) channels.push("WhatsApp")
  if (screeningConfig?.channels?.chat_web?.enabled) channels.push("Chat Web")
  if (screeningConfig?.channels?.phone?.enabled) channels.push("Telefone")

  const schedulingEnabled = screeningConfig?.scheduling?.enabled ?? false

  return (
    <div className="space-y-4">
      <div className="p-3 bg-white border border-gray-100 rounded-md">
        <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5 mb-2">
          <FileText className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
          Descricao da Vaga
        </h5>
        {description ? (
          <div>
            <p className="text-micro text-gray-600 dark:text-gray-400 leading-relaxed whitespace-pre-line">
              {truncatedDescription}
            </p>
            {description.length > 300 && (
              <button
                onClick={() => setShowFullDescription(!showFullDescription)}
                className="text-micro text-gray-950 dark:text-gray-50 font-medium mt-1 hover:underline"
              >
                {showFullDescription ? "Ver menos" : "Ver mais"}
              </button>
            )}
          </div>
        ) : (
          <p className="text-micro text-gray-600 dark:text-gray-400 italic">
            Nenhuma descricao adicionada
          </p>
        )}
      </div>

      <div className="p-3 bg-white border border-gray-100 rounded-md">
        <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5 mb-2">
          <Zap className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
          Competencias Tecnicas
        </h5>
        {technicalItems.length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            {technicalItems.map((item: any, idx: number) => (
              <Badge key={idx} className="bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 text-micro px-2 py-0.5 h-5 font-medium">
                {getCompetencyName(item)}
              </Badge>
            ))}
          </div>
        ) : (
          <p className="text-micro text-gray-600 dark:text-gray-400 italic">
            Nenhuma competencia tecnica configurada
          </p>
        )}
      </div>

      <div className="p-3 bg-white border border-gray-100 rounded-md">
        <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5 mb-2">
          <Heart className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
          Competencias Comportamentais
        </h5>
        {behavioralItems.length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            {behavioralItems.map((item: any, idx: number) => (
              <Badge key={idx} className="bg-purple-50 text-purple-700 border border-purple-200 text-micro px-2 py-0.5 h-5 font-medium">
                {getCompetencyName(item)}
              </Badge>
            ))}
          </div>
        ) : (
          <p className="text-micro text-gray-600 dark:text-gray-400 italic">
            Nenhuma competencia comportamental configurada
          </p>
        )}
      </div>

      <div className="p-3 bg-white border border-gray-100 rounded-md">
        <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5 mb-2">
          <Globe className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
          Idiomas
        </h5>
        {job.languages && job.languages.length > 0 ? (
          <div className="space-y-1.5">
            {job.languages.map((lang, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <span className="text-micro text-gray-600 dark:text-gray-400 font-medium">
                  {lang.language}
                </span>
                {lang.level && (
                  <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 text-gray-800 dark:text-gray-200">
                    {lang.level}
                  </Badge>
                )}
                {lang.required && (
                  <Badge className="text-micro px-1.5 py-0 h-4 bg-red-50 text-red-600 border border-red-200">
                    Obrigatorio
                  </Badge>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-micro text-gray-600 dark:text-gray-400 italic">
            Nenhum idioma configurado
          </p>
        )}
      </div>

      <div className="p-3 bg-white border border-gray-100 rounded-md">
        <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5 mb-2">
          <DollarSign className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
          Remuneracao e Beneficios
        </h5>
        <div className="space-y-2">
          {hasSalary ? (
            <div className="flex items-center gap-1.5">
              <span className="text-micro text-gray-600 dark:text-gray-400">Salario:</span>
              <span className="text-micro font-medium text-gray-950 dark:text-gray-50">
                {formatCurrency(salaryMin)}{salaryMax ? ` - ${formatCurrency(salaryMax)}` : ""}
              </span>
            </div>
          ) : (
            <p className="text-micro text-gray-600 dark:text-gray-400 italic">
              Faixa salarial nao informada
            </p>
          )}
          {hasBonus && (
            <div className="flex items-center gap-1.5">
              <span className="text-micro text-gray-600 dark:text-gray-400">Bonus:</span>
              <span className="text-micro font-medium text-gray-950 dark:text-gray-50">
                {formatCurrency(bonusMin)}{bonusMax ? ` - ${formatCurrency(bonusMax)}` : ""}
              </span>
            </div>
          )}
          {normalizedBenefits.length > 0 && (
            <div>
              <span className="text-micro text-gray-600 dark:text-gray-400 block mb-1">Beneficios:</span>
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

      <div className="p-3 bg-white border border-gray-100 rounded-md">
        <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5 mb-2">
          <Layers3 className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
          Etapas do Processo
        </h5>
        {pipelineStages && pipelineStages.length > 0 ? (
          <div className="flex items-center gap-1 overflow-x-auto pb-1">
            {pipelineStages.map((stage, idx) => (
              <React.Fragment key={stage.id}>
                {idx > 0 && (
                  <ChevronRight className="w-3 h-3 text-gray-300 flex-shrink-0" />
                )}
                <div className="flex items-center gap-1 px-2 py-1 bg-gray-50 border border-gray-200 rounded-lg flex-shrink-0">
                  {(stage as any).liaAssisted && (
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 flex-shrink-0" />
                  )}
                  <span className="text-micro font-medium text-gray-700">{stage.name}</span>
                  <Badge className="text-micro px-1 py-0 h-3.5 bg-gray-100 text-gray-600">
                    {stage.count}
                  </Badge>
                </div>
              </React.Fragment>
            ))}
          </div>
        ) : job.interviewStages && job.interviewStages.length > 0 ? (
          <div className="flex items-center gap-1 overflow-x-auto pb-1">
            {job.interviewStages
              .sort((a, b) => (a.order || 0) - (b.order || 0))
              .map((stage, idx) => (
                <React.Fragment key={idx}>
                  {idx > 0 && (
                    <ChevronRight className="w-3 h-3 text-gray-300 flex-shrink-0" />
                  )}
                  <div className="flex items-center gap-1 px-2 py-1 bg-gray-50 border border-gray-200 rounded-lg flex-shrink-0">
                    {stage.liaAssisted && (
                      <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 flex-shrink-0" />
                    )}
                    <span className="text-micro font-medium text-gray-700">{stage.stageName}</span>
                  </div>
                </React.Fragment>
              ))}
          </div>
        ) : (
          <p className="text-micro text-gray-600 dark:text-gray-400 italic">
            Nenhuma etapa configurada
          </p>
        )}
      </div>

      {job.isAffirmative && (
        <div className="p-3 bg-white border border-gray-100 rounded-md">
          <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5 mb-2">
            <Heart className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
            Acoes Afirmativas
          </h5>
          <div className="p-2 bg-purple-50 border border-purple-100 rounded-lg">
            {job.affirmativeType && (
              <div className="flex items-center gap-1.5 mb-1">
                <span className="text-micro text-gray-600 dark:text-gray-400">Tipo:</span>
                <Badge className="text-micro px-1.5 py-0 h-4 bg-purple-100 text-purple-700 border border-purple-200">
                  {job.affirmativeType}
                </Badge>
              </div>
            )}
            {job.affirmativeCriteriaPrimary && (
              <div className="flex items-center gap-1.5">
                <span className="text-micro text-gray-600 dark:text-gray-400">Criterio:</span>
                <span className="text-micro font-medium text-gray-950 dark:text-gray-50">
                  {job.affirmativeCriteriaPrimary}
                </span>
              </div>
            )}
            {!job.affirmativeType && !job.affirmativeCriteriaPrimary && (
              <p className="text-micro text-gray-600 dark:text-gray-400">
                Vaga afirmativa habilitada
              </p>
            )}
          </div>
        </div>
      )}

      <div className="border-t border-gray-200 dark:border-gray-700" />

      <div className="p-3 bg-white border border-gray-100 rounded-md">
        <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5 mb-2">
          <ClipboardList className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
          Fluxo de Triagem WSI
          <Badge
            className={`text-micro px-1.5 py-0 h-4 text-gray-800 ${screeningEnabled ? "bg-wedo-green-pastel" : "bg-gray-200"}`}
          >
            {screeningEnabled ? "Ativo" : "Pausado"}
          </Badge>
        </h5>
        <div className="grid grid-cols-2 gap-2">
          <div className="text-center p-2 bg-gray-50 rounded-lg">
            <div className="text-base-ui font-semibold text-gray-800">{questions.length}</div>
            <p className="text-micro text-gray-500">Perguntas</p>
          </div>
          <div className="text-center p-2 bg-gray-50 rounded-lg">
            <div className="text-base-ui font-semibold text-gray-800">{estimatedMinutes}min</div>
            <p className="text-micro text-gray-500">Tempo Est.</p>
          </div>
        </div>
        <p className="text-micro text-gray-400 mt-2">
          Gerencie o roteiro na aba Detalhes da Vaga
        </p>
      </div>

      <div className="p-3 bg-white border border-gray-100 rounded-md">
        <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5 mb-2">
          <CalendarCheck className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
          Agendamento
          <Badge
            className={`text-micro px-1.5 py-0 h-4 text-gray-800 ${schedulingEnabled ? "bg-wedo-green-pastel" : "bg-gray-200"}`}
          >
            {schedulingEnabled ? "Ativo" : "Inativo"}
          </Badge>
        </h5>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <span className="text-micro text-gray-500">Score Minimo</span>
            <p className="text-micro font-medium text-gray-800">{screeningConfig?.scheduling?.minScore || 'Recomendado'}</p>
          </div>
          <div>
            <span className="text-micro text-gray-500">Calendario</span>
            <p className="text-micro font-medium text-gray-800">{screeningConfig?.scheduling?.calendar || 'Outlook'}</p>
          </div>
          <div>
            <span className="text-micro text-gray-500">Horarios</span>
            <p className="text-micro font-medium text-gray-800">{screeningConfig?.scheduling?.hours || '9h-18h'}</p>
          </div>
          <div>
            <span className="text-micro text-gray-500">Duracao</span>
            <p className="text-micro font-medium text-gray-800">{screeningConfig?.scheduling?.duration || '45min'}</p>
          </div>
        </div>
      </div>

      <div className="p-3 bg-white border border-gray-100 rounded-md">
        <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5 mb-2">
          <MessageSquare className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
          Canais de Comunicacao
        </h5>
        {channels.length > 0 ? (
          <div className="flex flex-wrap gap-1.5 mb-2">
            {channels.map((ch, idx) => (
              <Badge key={idx} className="text-micro px-1.5 py-0 h-4 bg-gray-100 text-gray-800 dark:text-gray-200">
                {ch}
              </Badge>
            ))}
          </div>
        ) : (
          <p className="text-micro text-gray-600 dark:text-gray-400 italic mb-2">
            Nenhum canal configurado
          </p>
        )}
        <div className="grid grid-cols-2 gap-2">
          <div>
            <span className="text-micro text-gray-500">Score Minimo Aprovacao</span>
            <p className="text-micro font-medium text-gray-800">{screeningConfig?.minApprovalScore || 'Recomendado'}</p>
          </div>
          <div>
            <span className="text-micro text-gray-500">Timeout Resposta</span>
            <p className="text-micro font-medium text-gray-800">{screeningConfig?.timeout || '24h'}</p>
          </div>
          <div>
            <span className="text-micro text-gray-500">Re-tentativas</span>
            <p className="text-micro font-medium text-gray-800">{screeningConfig?.retries || '2x'}</p>
          </div>
          <div>
            <span className="text-micro text-gray-500">Fallback</span>
            <p className="text-micro font-medium text-gray-800">{screeningConfig?.fallback || 'Revisao Manual'}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
