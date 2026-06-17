"use client"

import React from"react"
import { Chip } from "@/components/ui/chip"
import { Checkbox } from"@/components/ui/checkbox"
import { Button } from"@/components/ui/button"
import { ChevronDown, ChevronUp, Lock, Plus, Trash2 } from"lucide-react"
import type { UnifiedScreeningQuestion } from"@/hooks/recruitment/use-screening-questions"
import { cn } from"@/lib/utils"
import { WSI_AUTOMATIC_MESSAGES, WSI_BLOCKS, formatMessageWithVariables } from"./ScreeningPanelConstants"

interface ScreeningBlockSectionProps {
  block: typeof WSI_BLOCKS[0]
  questions: UnifiedScreeningQuestion[]
  isExpanded: boolean
  isAffirmative?: boolean
  onToggleBlock: (blockId: number) => void
  onToggleQuestion: (id: string) => void
  onSelectBlockForSuggestion: (blockId: number) => void
}

function getCategoryBadge(question: UnifiedScreeningQuestion) {
  const isAffirmativeQuestion = question.id?.includes('affirmative') || false
  if (isAffirmativeQuestion) return { label: 'Inclusão', color: ' border-wedo-purple/30' }
  const cat = (question.category || '').toLowerCase()
  if (cat.includes('tech')) return { label: 'Técnica', color: '-dark border-wedo-cyan/30 dark:border-wedo-cyan/30' }
  if (cat.includes('behav') || cat.includes('situa')) return { label: 'Experiência', color: ' border-wedo-purple/30' }
  if (cat.includes('elig') && question.is_eliminatory === false) return { label: 'Informativa', color: 'bg-lia-bg-secondary text-lia-text-secondary border-lia-border-subtle' }
  if (cat.includes('elig')) return { label: 'Eliminatória', color: ' border-status-error/30' }
  if (cat.includes('cult')) return { label: 'Cultural', color: ' border-status-success/30' }
  if (cat.includes('company')) return { label: 'Empresa', color: ' border-wedo-orange/30' }
  return { label: 'Informativa', color: 'bg-lia-bg-secondary text-lia-text-secondary border-lia-border-subtle' }
}

function QuestionCard({ question, showDelete, onToggle }: { question: UnifiedScreeningQuestion; showDelete: boolean; onToggle: (id: string) => void }) {
  const isAffirmativeQuestion = question.id?.includes('affirmative') || false
  const badge = getCategoryBadge(question)

  return (
    <div
      key={question.id}
      className={cn("p-3 rounded-md border transition-colors duration-200 group",
        question.is_selected
          ?"bg-lia-bg-primary border-lia-border-subtle"
          :"bg-lia-bg-secondary/50 border-lia-border-subtle opacity-70"
      )}
    >
      <div className="flex items-start gap-3">
        <Checkbox
          checked={question.is_selected}
          onCheckedChange={() => onToggle(question.id)}
          className="mt-0.5"
        />
        <div className="flex-1 space-y-2">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-1">
              <Chip variant="neutral" className={cn("text-micro px-1.5 py-0 h-4 flex items-center border", badge.color)}>
                {badge.label}
              </Chip>
              {isAffirmativeQuestion && (
                <Chip variant="success" className="text-micro px-1.5 py-0 h-4 flex items-center">
                  Não eliminatória
                </Chip>
              )}
            </div>
            {showDelete && (
              <Button
                variant="ghost"
                size="sm"
                className="h-5 w-5 p-0 opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none"
                onClick={() => onToggle(question.id)}
              >
                <Trash2 className="h-3 w-3 text-lia-text-secondary hover:text-status-error" />
              </Button>
            )}
          </div>
          <p className="text-xs text-lia-text-primary leading-relaxed">
            {question.text}
          </p>
          <div className="flex items-center gap-3 text-micro text-lia-text-secondary">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-status-success"></span>
              {question.weight ? `${Math.round(question.weight * 100)}%` : '75%'}
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-status-error"></span>
              0%
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-lia-border-default"></span>
              {question.dreyfus_stage ? `${(question.dreyfus_stage / 5 * 100).toFixed(0)}%` : '55%'}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

export function ScreeningBlockSection({
  block,
  questions,
  isExpanded,
  isAffirmative,
  onToggleBlock,
  onToggleQuestion,
  onSelectBlockForSuggestion,
}: ScreeningBlockSectionProps) {
  const Icon = block.icon
  const selectedInBlock = questions.filter(q => q.is_selected).length

  return (
    <div key={block.id} className="space-y-2">
      <div
        className={cn("flex items-center justify-between p-2.5 rounded-md cursor-pointer transition-colors border",
          block.editable
            ?"bg-lia-bg-primary border-lia-border-subtle hover:bg-lia-interactive-hover"
            :"bg-lia-bg-tertiary/80 border-lia-border-subtle"
        )}
        onClick={() => onToggleBlock(block.id)}
      >
        <div className="flex items-center gap-2.5">
          <div className={cn("w-6 h-6 rounded-full flex items-center justify-center text-micro font-medium",
            block.editable ?"bg-lia-interactive-active text-lia-text-secondary" :"bg-lia-bg-tertiary text-lia-text-secondary"
          )}>
            {block.id}
          </div>
          <Icon className={cn("h-4 w-4", block.editable ?"text-lia-text-secondary" :"lia-text-secondary")} />
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-medium text-lia-text-primary">{block.name}</span>
              {block.id === 2 && isAffirmative && (
                <Chip variant="neutral" className="text-micro px-1.5 py-0 h-4 flex items-center border  border-wedo-purple/30">
                  Vaga Afirmativa
                </Chip>
              )}
            </div>
            <span className="text-micro text-lia-text-secondary">{block.duration}</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {!block.editable && (
            <Chip
              variant="neutral"
              className="text-micro px-1.5 py-0 bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-subtle"
            >
              <Lock className="h-2.5 w-2.5 mr-0.5" />
              Automático
            </Chip>
          )}
          {block.editable && questions.length > 0 && (
            <Chip
              variant="neutral"
              className={`text-micro px-1.5 py-0 ${selectedInBlock > 0 ? 'bg-wedo-green-pastel text-status-success border-wedo-green-pastel' : 'bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-default'}`}
            >
              {selectedInBlock} {selectedInBlock === 1 ? 'Info.' : 'Infos.'}
            </Chip>
          )}
          {isExpanded ? (
            <ChevronUp className="h-4 w-4 text-lia-text-secondary" />
          ) : (
            <ChevronDown className="h-4 w-4 text-lia-text-secondary" />
          )}
        </div>
      </div>

      {isExpanded && (
        <div className="space-y-2 pl-3 pr-1">
          {!block.editable ? (
            WSI_AUTOMATIC_MESSAGES[block.id] ? (
              <div className="rounded-xl border border-lia-border-subtle bg-lia-bg-secondary overflow-hidden">
                <div className="px-3 py-2 bg-lia-bg-tertiary">
                  <p className="text-xs font-medium text-lia-text-primary">
                    {WSI_AUTOMATIC_MESSAGES[block.id].title}
                  </p>
                </div>
                <div className="p-3">
                  <div className="text-xs text-lia-text-primary leading-relaxed whitespace-pre-line">
                    {formatMessageWithVariables(WSI_AUTOMATIC_MESSAGES[block.id].message)}
                  </div>
                </div>
                <div className="px-3 py-2 border-t border-lia-border-subtle bg-lia-bg-secondary">
                  <p className="text-micro text-lia-text-secondary italic">
                    {WSI_AUTOMATIC_MESSAGES[block.id].note}
                  </p>
                </div>
              </div>
            ) : (
              <div className="p-3 rounded-xl bg-lia-bg-secondary/50 border border-lia-border-subtle">
                <p className="text-xs text-lia-text-secondary italic">
                  {block.description}
                </p>
              </div>
            )
          ) : questions.length === 0 ? (
            <div className="p-3 rounded-xl bg-lia-bg-secondary/50 border border-lia-border-subtle border-dashed">
              <p className="text-xs text-lia-text-secondary italic text-center">
                Nenhuma pergunta neste bloco
              </p>
              <div className="flex justify-center mt-2">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 text-micro text-lia-text-secondary"
                  onClick={(e) => {
                    e.stopPropagation()
                    onSelectBlockForSuggestion(block.id)
                  }}
                >
                  <Plus className="h-3 w-3 mr-1" />
                  Adicionar
                </Button>
              </div>
            </div>
          ) : (
            questions.map(q => <QuestionCard key={q.id} question={q} showDelete={false} onToggle={onToggleQuestion} />)
          )}
        </div>
      )}
    </div>
  )
}

export function SuggestionCard({ question, onAdd }: { question: UnifiedScreeningQuestion; onAdd: (q: UnifiedScreeningQuestion) => void }) {
  const getCategoryBadges = () => {
    const badges: { label: string; color: string }[] = []
    const isAffirmativeSuggestion = question.id?.includes('affirmative') || false
    const cat = (question.category || '').toLowerCase()
    if (isAffirmativeSuggestion) {
      badges.push({ label: 'Inclusão', color: ' border-wedo-purple/30' })
    } else if (cat.includes('elig') && question.is_eliminatory !== false) {
      badges.push({ label: 'Eliminatória', color: ' border-status-error/30' })
    } else if (cat.includes('elig')) {
      badges.push({ label: 'Informativa', color: 'bg-lia-bg-secondary text-lia-text-secondary border-lia-border-subtle' })
    }
    if (cat.includes('tech')) badges.push({ label: 'Skills', color: '-dark border-wedo-cyan/30 dark:border-wedo-cyan/30' })
    if (cat.includes('behav') || cat.includes('situa')) badges.push({ label: 'Experiência', color: ' border-wedo-purple/30' })
    if (cat.includes('cult')) badges.push({ label: 'Cultural', color: ' border-status-success/30' })
    if (badges.length === 0) badges.push({ label: 'Geral', color: ' border-wedo-orange/30' })
    return badges
  }

  const badges = getCategoryBadges()

  return (
    <div
      key={question.id}
      className="p-3 rounded-xl border border-lia-border-subtle bg-lia-bg-primary transition-colors motion-reduce:transition-none cursor-pointer group"
      onClick={() => onAdd(question)}
    >
      <div className="flex items-start gap-3">
        <Checkbox
          checked={question.is_selected}
          onCheckedChange={() => onAdd(question)}
          className="mt-0.5"
        />
        <div className="flex-1 space-y-2">
          <p className="text-xs text-lia-text-primary leading-relaxed">
            {question.text}
          </p>
          <div className="flex flex-wrap gap-1">
            {badges.map((badge, idx) => (
              <Chip key={idx} variant="neutral" className={cn("text-micro px-1.5 py-0 h-4 flex items-center border", badge.color)}>
                {badge.label as React.ReactNode}
              </Chip>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
