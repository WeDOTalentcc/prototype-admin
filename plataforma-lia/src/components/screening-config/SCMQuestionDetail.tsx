"use client"

import React from "react"
import { Badge } from "@/components/ui/badge"
import {
  CheckCircle, Clock, Gauge, GraduationCap, Scale, ShieldAlert, Target
} from "lucide-react"
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

export function SCMQuestionDetailView({ item, isDetailsExpanded, onToggleDetails, helpers }: SCMQuestionDetailProps) {
  const { getBloomComplexity, getBloomLabelPTBR, getDreyfusLabelPTBR, getBigFiveLabelPTBR, getEstimatedTime } = helpers
  const complexity = getBloomComplexity(item.bloom_level || 3)
  const estTime = getEstimatedTime(item.question_type || 'open')

  return (
    <div className="flex-1 min-w-0">
      <div className="flex items-center gap-1.5 mb-2 flex-wrap">
        <Badge className={`text-micro px-2 py-0.5 h-5 rounded-full ${item.category === 'behavioral' || item.category === 'Comportamental' || item.category === 'comportamental' ? 'bg-wedo-purple/15 text-wedo-purple border border-wedo-purple/30 dark:bg-wedo-purple/20 dark:text-wedo-purple dark:border-wedo-purple/30' : item.category === 'technical' || item.category === 'Técnica' || item.category === 'técnica' ? 'bg-wedo-cyan/10 text-wedo-cyan-dark border border-wedo-cyan/30 dark:border-wedo-cyan/30' : item.category === 'cultural' || item.category === 'fit_cultural' ? 'bg-wedo-cyan/10 text-wedo-cyan border border-wedo-cyan/30 dark:bg-wedo-cyan/20 dark:border-wedo-cyan/30' : 'bg-status-success/15 text-status-success border border-status-success/30 dark:bg-status-success/20 dark:border-status-success/30'}`}>
          {item.category === 'behavioral' || item.category === 'comportamental' ? 'Comportamental' : item.category === 'technical' || item.category === 'técnica' ? 'Técnica' : item.category === 'cultural' || item.category === 'fit_cultural' ? 'Fit Cultural' : item.category || 'Geral'}
        </Badge>
        {(item.type === 'eliminatory' || item.required || item.is_eliminatory) && (
          <Badge className="text-micro px-2 py-0.5 h-5 rounded-full bg-status-error/10 text-status-error border border-status-error/30 dark:bg-status-error/20 dark:text-status-error dark:border-status-error/30">Eliminatória</Badge>
        )}
        <Badge className={`text-micro px-2 py-0.5 h-5 rounded-full border ${complexity.color}`}>
          <Gauge className="w-3 h-3 mr-0.5" />{complexity.label}
        </Badge>
        {item.bloom_level && (
          <Badge className="text-micro px-2 py-0.5 h-5 rounded-full border bg-wedo-cyan/10 text-wedo-cyan border-wedo-cyan/30 dark:bg-wedo-cyan/20 dark:border-wedo-cyan/30">
            <GraduationCap className="w-3 h-3 mr-0.5" />{getBloomLabelPTBR(item.bloom_level) || item.bloom_label}
          </Badge>
        )}
        {item.dreyfus_level && item.block_id !== 2 && (
          <Badge className="text-micro px-2 py-0.5 h-5 rounded-full border bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30 dark:bg-wedo-purple/20 dark:text-wedo-purple dark:border-wedo-purple/30">
            {getDreyfusLabelPTBR(item.dreyfus_level) || item.dreyfus_label}
          </Badge>
        )}
        {item.big_five_trait && (
          <Badge className="text-micro px-2 py-0.5 h-5 rounded-full border bg-wedo-magenta/10 text-wedo-magenta border-wedo-magenta/30 dark:bg-wedo-magenta/20 dark:text-wedo-magenta dark:border-wedo-magenta/30">
            {getBigFiveLabelPTBR(item.big_five_trait)}
          </Badge>
        )}
        {(item.weight || 0) >= 1.5 && (
          <Badge className="text-micro px-2 py-0.5 h-5 rounded-full border bg-status-error/10 text-status-error border-status-error/30 dark:bg-status-error/20 dark:text-status-error dark:border-status-error/30">
            <ShieldAlert className="w-3 h-3 mr-0.5" />Crítica
          </Badge>
        )}
      </div>
      <p className="text-xs text-lia-text-primary leading-relaxed">{item.question || item.text}</p>
      <div className="flex items-center gap-3 mt-2 text-micro text-lia-text-tertiary">
        <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{estTime}</span>
        {item.bloom_label && !item.bloom_level && <span className="flex items-center gap-1"><GraduationCap className="w-3 h-3" />Bloom: {item.bloom_label}</span>}
        {(item.trait || item.skill) && <span className="flex items-center gap-1"><Target className="w-3 h-3" />Avalia: {item.trait || item.skill}</span>}
        <span className="flex items-center gap-1"><Scale className="w-3 h-3" />Peso: {((item.weight || 1) * 100).toFixed(0)}%</span>
      </div>
      <button className="mt-1.5 text-micro lia-text-secondary hover:text-lia-text-secondary dark:hover:lia-text-muted transition-colors motion-reduce:transition-none" onClick={() => onToggleDetails(item.id)}>
        {isDetailsExpanded ? '▲ Ocultar detalhes' : '▼ Ver detalhes'}
      </button>
      {isDetailsExpanded && (
        <div className="mt-2 p-2.5 bg-lia-bg-secondary/50 border border-lia-border-subtle rounded-lg space-y-1.5 text-micro">
          <div className="flex gap-4 flex-wrap">
            <div><span className="text-lia-text-disabled">Framework:</span><span className="ml-1 text-lia-text-secondary font-medium">{item.framework === 'Company' ? 'Empresa' : (item.block_id === 2 ? 'Empresa' : (item.framework || 'CBI'))}</span></div>
            <div><span className="text-lia-text-disabled">Dreyfus:</span><span className="ml-1 text-lia-text-secondary font-medium">{item.block_id === 2 ? 'Padrão' : (item.dreyfus_label || '—')}</span></div>
            <div><span className="text-lia-text-disabled">Tipo:</span><span className="ml-1 text-lia-text-secondary font-medium">{item.question_type === 'yes_no' ? 'Sim/Não' : item.question_type === 'open' ? 'Aberta' : item.question_type || 'Aberta'}</span></div>
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
