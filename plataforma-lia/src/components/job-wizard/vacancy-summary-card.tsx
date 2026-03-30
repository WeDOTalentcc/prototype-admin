'use client'

import React from 'react'
import { cardStyles, badgeStyles, buttonStyles, textStyles } from '@/lib/design-tokens'

interface VacancySummaryCardProps {
  jobData: {
    title?: string
    department?: string
    location?: string
    workModel?: string
    seniority?: string
    contractType?: string
    salaryRange?: { min?: number; max?: number; currency?: string }
    description?: string
    requirements?: string[]
    technicalSkills?: Array<{ name: string; level?: string }>
    behavioralCompetencies?: Array<{ name: string }>
    benefits?: string[]
    wsiQuestions?: Array<{ question: string; block?: string }>
    completionPercentage?: number
  }
  onConfirmPublish?: () => void
  onEdit?: (field: string) => void
  className?: string
}

function SectionHeader({
  label,
  filled,
  onEdit,
  fieldName,
}: {
  label: string
  filled: boolean
  onEdit?: (field: string) => void
  fieldName: string
}) {
  return (
    <div className="flex items-center justify-between mb-2">
      <div className="flex items-center gap-2">
        {filled ? (
          <span className="w-4 h-4 rounded-full bg-status-success/15 dark:bg-status-success/30 flex items-center justify-center">
            <svg className="w-2.5 h-2.5 text-status-success dark:text-status-success" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </span>
        ) : (
          <span className="w-4 h-4 rounded-full bg-status-warning/15 dark:bg-status-warning/30 flex items-center justify-center">
            <svg className="w-2.5 h-2.5 text-status-warning dark:text-status-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01" />
            </svg>
          </span>
        )}
        <span className={textStyles.h4}>{label}</span>
      </div>
      {onEdit && (
        <button
          onClick={() => onEdit(fieldName)}
          className="p-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          aria-label={`Editar ${label}`}
        >
          <svg className="w-3.5 h-3.5 lia-text-secondary hover:lia-text-base dark:hover:lia-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
          </svg>
        </button>
      )}
    </div>
  )
}

function formatCurrency(value: number, currency?: string): string {
  const cur = currency || 'BRL'
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: cur, maximumFractionDigits: 0 }).format(value)
}

export function VacancySummaryCard({ jobData, onConfirmPublish, onEdit, className }: VacancySummaryCardProps) {
  const percentage = jobData.completionPercentage ?? 0

  const hasHeader = !!(jobData.title || jobData.seniority || jobData.department)
  const hasDetails = !!(jobData.location || jobData.workModel || jobData.contractType)
  const hasSalary = !!(jobData.salaryRange?.min || jobData.salaryRange?.max)
  const hasDescription = !!jobData.description
  const hasRequirements = !!(jobData.requirements && jobData.requirements.length > 0)
  const hasTechnicalSkills = !!(jobData.technicalSkills && jobData.technicalSkills.length > 0)
  const hasBehavioral = !!(jobData.behavioralCompetencies && jobData.behavioralCompetencies.length > 0)
  const hasBenefits = !!(jobData.benefits && jobData.benefits.length > 0)
  const hasWSI = !!(jobData.wsiQuestions && jobData.wsiQuestions.length > 0)

  const questionsByBlock: Record<string, number> = {}
  if (jobData.wsiQuestions) {
    for (const q of jobData.wsiQuestions) {
      const block = q.block || 'Geral'
      questionsByBlock[block] = (questionsByBlock[block] || 0) + 1
    }
  }

  return (
    <div className={`${cardStyles.elevated} p-5 font-['Open_Sans',sans-serif] ${className || ''}`}>
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className={textStyles.h3}>Resumo da Vaga</span>
          <span className={`${textStyles.metricSmall} ${percentage >= 80 ? 'text-status-success dark:text-status-success' : percentage >= 50 ? 'text-status-warning dark:text-status-warning' : 'text-status-error dark:text-status-error'}`}>
            {percentage}%
          </span>
        </div>
        <div className="w-full h-1.5 bg-gray-100 dark:bg-lia-bg-elevated rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-[width,height] duration-500 ${percentage >= 80 ? 'bg-status-success' : percentage >= 50 ? 'bg-status-warning' : 'bg-status-error'}`}
            style={{width: `${Math.min(percentage, 100)}%`}}
          />
        </div>
      </div>

      <div className="space-y-4 divide-y divide-gray-100 dark:divide-gray-700">
        <div>
          <SectionHeader label="Cargo" filled={hasHeader} onEdit={onEdit} fieldName="header" />
          {hasHeader ? (
            <div className="space-y-1">
              {jobData.title && <p className={textStyles.bodyLarge}>{jobData.title}</p>}
              <div className="flex flex-wrap gap-1.5">
                {jobData.seniority && <span className={badgeStyles.cyan}>{jobData.seniority}</span>}
                {jobData.department && <span className={badgeStyles.default}>{jobData.department}</span>}
              </div>
            </div>
          ) : (
            <p className={textStyles.description}>Nenhum cargo definido</p>
          )}
        </div>

        <div className="pt-4">
          <SectionHeader label="Detalhes" filled={hasDetails} onEdit={onEdit} fieldName="details" />
          {hasDetails ? (
            <div className="flex flex-wrap gap-1.5">
              {jobData.location && <span className={badgeStyles.default}>{jobData.location}</span>}
              {jobData.workModel && <span className={badgeStyles.default}>{jobData.workModel}</span>}
              {jobData.contractType && <span className={badgeStyles.default}>{jobData.contractType}</span>}
            </div>
          ) : (
            <p className={textStyles.description}>Nenhum detalhe preenchido</p>
          )}
        </div>

        <div className="pt-4">
          <SectionHeader label="Remuneração" filled={hasSalary} onEdit={onEdit} fieldName="salary" />
          {hasSalary ? (
            <p className={textStyles.metric}>
              {jobData.salaryRange?.min != null && formatCurrency(jobData.salaryRange.min, jobData.salaryRange?.currency)}
              {jobData.salaryRange?.min != null && jobData.salaryRange?.max != null && ' – '}
              {jobData.salaryRange?.max != null && formatCurrency(jobData.salaryRange.max, jobData.salaryRange?.currency)}
            </p>
          ) : (
            <p className={textStyles.description}>Faixa salarial não informada</p>
          )}
        </div>

        <div className="pt-4">
          <SectionHeader label="Descrição" filled={hasDescription} onEdit={onEdit} fieldName="description" />
          {hasDescription ? (
            <p className={textStyles.body}>
              {jobData.description!.length > 200 ? `${jobData.description!.slice(0, 200)}…` : jobData.description}
            </p>
          ) : (
            <p className={textStyles.description}>Descrição não preenchida</p>
          )}
        </div>

        <div className="pt-4">
          <SectionHeader label="Requisitos" filled={hasRequirements} onEdit={onEdit} fieldName="requirements" />
          {hasRequirements ? (
            <ul className="space-y-1">
              {jobData.requirements!.map((req, i) => (
                <li key={i} className={`${textStyles.bodySmall} flex items-start gap-1.5`}>
                  <span className="lia-text-secondary mt-0.5">•</span>
                  <span>{req}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className={textStyles.description}>Nenhum requisito adicionado</p>
          )}
        </div>

        <div className="pt-4">
          <SectionHeader label="Skills Técnicas" filled={hasTechnicalSkills} onEdit={onEdit} fieldName="technicalSkills" />
          {hasTechnicalSkills ? (
            <div className="flex flex-wrap gap-1.5">
              {jobData.technicalSkills!.map((skill, i) => (
                <span key={i} className={badgeStyles.cyan}>
                  {skill.name}
                  {skill.level && <span className="ml-1 opacity-70">· {skill.level}</span>}
                </span>
              ))}
            </div>
          ) : (
            <p className={textStyles.description}>Nenhuma skill técnica definida</p>
          )}
        </div>

        <div className="pt-4">
          <SectionHeader label="Competências Comportamentais" filled={hasBehavioral} onEdit={onEdit} fieldName="behavioralCompetencies" />
          {hasBehavioral ? (
            <div className="flex flex-wrap gap-1.5">
              {jobData.behavioralCompetencies!.map((comp, i) => (
                <span key={i} className={badgeStyles.purple}>{comp.name}</span>
              ))}
            </div>
          ) : (
            <p className={textStyles.description}>Nenhuma competência comportamental</p>
          )}
        </div>

        <div className="pt-4">
          <SectionHeader label="Benefícios" filled={hasBenefits} onEdit={onEdit} fieldName="benefits" />
          {hasBenefits ? (
            <ul className="space-y-1">
              {jobData.benefits!.map((benefit, i) => (
                <li key={i} className={`${textStyles.bodySmall} flex items-start gap-1.5`}>
                  <span className="lia-text-secondary mt-0.5">•</span>
                  <span>{benefit}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className={textStyles.description}>Nenhum benefício adicionado</p>
          )}
        </div>

        <div className="pt-4">
          <SectionHeader label="Perguntas WSI" filled={hasWSI} onEdit={onEdit} fieldName="wsiQuestions" />
          {hasWSI ? (
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(questionsByBlock).map(([block, count]) => (
                <span key={block} className={badgeStyles.green}>
                  {block}: {count} {count === 1 ? 'pergunta' : 'perguntas'}
                </span>
              ))}
            </div>
          ) : (
            <p className={textStyles.description}>Nenhuma pergunta de triagem</p>
          )}
        </div>
      </div>

      {onConfirmPublish && (
        <div className="mt-6 pt-4 border-t border-lia-border-subtle dark:border-lia-border-subtle">
          <button
            onClick={onConfirmPublish}
            className={`${buttonStyles.primary} w-full justify-center flex items-center gap-2`}
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
            Publicar Vaga
          </button>
        </div>
      )}
    </div>
  )
}

export default VacancySummaryCard
