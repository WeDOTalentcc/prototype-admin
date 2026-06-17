"use client"

import React from"react"
import { Chip } from "@/components/ui/chip"
import {
  CheckCircle, Clock, Gauge, GraduationCap, Scale, ShieldAlert, Target
} from"lucide-react"
import type { ScreeningQuestionItem } from './SCMScreeningTypes'

interface QuestionBadgeHelpers {
  getBloomComplexity: (level: number) => { label: string; color: string }
  getBloomLabelPTBR: (level: number) => string
  getDreyfusLabelPTBR: (level: number | string) => string
  getBigFiveLabelPTBR: (trait: string) => string
  getEstimatedTime: (type: string) => string
}

interface SCMQuestionDetailProps {
  item: ScreeningQuestionItem
  isDetailsExpanded: boolean
  onToggleDetails: (id: string) => void
  helpers: QuestionBadgeHelpers
}

type CategoryKind = 'behavioral' | 'technical' | 'cultural' | 'general'

function getCategoryKind(raw?: string): CategoryKind {
  switch (raw) {
    case 'behavioral':
    case 'Comportamental':
    case 'comportamental':
      return 'behavioral'
    case 'technical':
    case 'Técnica':
    case 'técnica':
      return 'technical'
    case 'cultural':
    case 'fit_cultural':
      return 'cultural'
    default:
      return 'general'
  }
}

const CATEGORY_CHIP_CLASSES: Record<CategoryKind, string> = {
  behavioral: 'border border-wedo-purple/30 dark:bg-wedo-purple/20 dark:text-wedo-purple dark:border-wedo-purple/30',
  technical: '-dark border border-wedo-cyan/30 dark:border-wedo-cyan/30',
  cultural: 'border border-wedo-cyan/30 dark:bg-wedo-cyan/20 dark:border-wedo-cyan/30',
  general: 'dark:bg-status-success/20',
}

const CATEGORY_CHIP_LABELS: Record<CategoryKind, string> = {
  behavioral: 'Comportamental',
  technical: 'Técnica',
  cultural: 'Fit Cultural',
  general: 'Geral',
}

export function SCMQuestionDetailView({ item, isDetailsExpanded, onToggleDetails, helpers }: SCMQuestionDetailProps) {
  const { getBloomComplexity, getBloomLabelPTBR, getDreyfusLabelPTBR, getBigFiveLabelPTBR, getEstimatedTime } = helpers
  const complexity = getBloomComplexity(item.bloom_level || 3)
  const estTime = getEstimatedTime(item.question_type || 'open')
  const categoryKind = getCategoryKind(item.category)
  const categoryVariant = categoryKind === 'general' ? 'success' : 'neutral'
  const categoryLabel = categoryKind === 'general' ? (item.category || CATEGORY_CHIP_LABELS.general) : CATEGORY_CHIP_LABELS[categoryKind]

  return (
    <div className="flex-1 min-w-0">
      <div className="flex items-center gap-1.5 mb-2 flex-wrap">
        <Chip variant={categoryVariant} muted className={`text-micro px-2 py-0.5 h-5 rounded-full ${CATEGORY_CHIP_CLASSES[categoryKind]}`}>
          {categoryLabel}
        </Chip>
        {(item.type === 'eliminatory' || item.required || item.is_eliminatory) && (
          <Chip variant="danger" muted className="text-micro px-2 py-0.5 h-5 rounded-full dark:bg-status-error/20">Eliminatória</Chip>
        )}
        <Chip variant="neutral" muted className={`text-micro px-2 py-0.5 h-5 rounded-full border ${complexity.color}`}>
          <Gauge className="w-3 h-3 mr-0.5" />{complexity.label}
        </Chip>
        {item.bloom_level && (
          <Chip variant="neutral" muted className="text-micro px-2 py-0.5 h-5 rounded-full border  border-wedo-cyan/30 dark:bg-wedo-cyan/20 dark:border-wedo-cyan/30">
            <GraduationCap className="w-3 h-3 mr-0.5" />{getBloomLabelPTBR(item.bloom_level) || item.bloom_label}
          </Chip>
        )}
        {item.dreyfus_level && item.block_id !== 2 && (
          <Chip variant="neutral" muted className="text-micro px-2 py-0.5 h-5 rounded-full border  border-wedo-purple/30 dark:bg-wedo-purple/20 dark:text-wedo-purple dark:border-wedo-purple/30">
            {getDreyfusLabelPTBR(item.dreyfus_level) || item.dreyfus_label}
          </Chip>
        )}
        {item.big_five_trait && (
          <Chip variant="neutral" muted className="text-micro px-2 py-0.5 h-5 rounded-full border bg-wedo-magenta/10 text-wedo-magenta-text border-wedo-magenta/30 dark:bg-wedo-magenta/20 dark:text-wedo-magenta dark:border-wedo-magenta/30">
            {getBigFiveLabelPTBR(item.big_five_trait)}
          </Chip>
        )}
        {(item.weight || 0) >= 1.5 && (
          <Chip variant="danger" muted className="text-micro px-2 py-0.5 h-5 rounded-full dark:bg-status-error/20">
            <ShieldAlert className="w-3 h-3 mr-0.5" />Crítica
          </Chip>
        )}
      </div>
      <p className="text-xs text-lia-text-primary leading-relaxed">{item.question || item.text}</p>
      <div className="flex items-center gap-3 mt-2 text-micro text-lia-text-tertiary">
        <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{estTime}</span>
        {item.bloom_label && !item.bloom_level && <span className="flex items-center gap-1"><GraduationCap className="w-3 h-3" />Bloom: {item.bloom_label}</span>}
        {(item.trait || item.skill) && <span className="flex items-center gap-1"><Target className="w-3 h-3" />Avalia: {item.trait || item.skill}</span>}
        <span className="flex items-center gap-1"><Scale className="w-3 h-3" />Peso: {((item.weight || 1) * 100).toFixed(0)}%</span>
      </div>
      <button className="mt-1.5 text-micro text-lia-text-secondary hover:text-lia-text-secondary dark:hover:text-lia-text-tertiary transition-colors motion-reduce:transition-none" onClick={() => onToggleDetails(item.id)}>
        {isDetailsExpanded ? '▲ Ocultar detalhes' : '▼ Ver detalhes'}
      </button>
      {isDetailsExpanded && (
        <div className="mt-2 p-2.5 bg-lia-bg-secondary/50 border border-lia-border-subtle rounded-lg space-y-1.5 text-micro">
          <div className="flex gap-4 flex-wrap">
            <div><span className="text-lia-text-tertiary">Framework:</span><span className="ml-1 text-lia-text-secondary font-medium">{item.framework === 'Company' ? 'Empresa' : (item.block_id === 2 ? 'Empresa' : (item.framework || 'CBI'))}</span></div>
            <div><span className="text-lia-text-tertiary">Dreyfus:</span><span className="ml-1 text-lia-text-secondary font-medium">{item.block_id === 2 ? 'Padrão' : (item.dreyfus_label || '—')}</span></div>
            <div><span className="text-lia-text-tertiary">Tipo:</span><span className="ml-1 text-lia-text-secondary font-medium">{item.question_type === 'yes_no' ? 'Sim/Não' : item.question_type === 'open' ? 'Aberta' : item.question_type || 'Aberta'}</span></div>
          </div>
          {(item.expected_answer || (item.expected_signals && item.expected_signals.length > 0)) && (
            <div><span className="text-lia-text-disabled">Resposta esperada:</span><p className="text-lia-text-secondary mt-0.5">{item.expected_answer || item.expected_signals?.join(', ')}</p></div>
          )}
          {(item.scoring_criteria || item.scoring_rubric) && Object.keys(item.scoring_criteria || item.scoring_rubric || {}).length > 0 && (
            <div><span className="lia-text-secondary">Critérios de pontuação:</span><div className="mt-0.5 space-y-0.5">{Object.entries(item.scoring_criteria || item.scoring_rubric || {}).map(([level, desc]: [string, unknown]) => (<div key={level} className="flex gap-1"><span className="text-lia-text-tertiary font-medium shrink-0">{level}:</span><span className="text-lia-text-secondary">{String(desc)}</span></div>))}</div></div>
          )}
        </div>
      )}
    </div>
  )
}
