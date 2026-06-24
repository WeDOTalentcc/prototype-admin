"use client"

import React, { useState } from"react"
import { Button } from"@/components/ui/button"
import { Label } from"@/components/ui/label"
import { Chip } from "@/components/ui/chip"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Loader2, ChevronDown, ChevronRight, MessageCircle, Target } from"lucide-react"
import { COMPETENCIES_CATALOG, Competency, BehavioralCompetenciesData } from"../types"
import { toast } from "sonner"

interface PanelProps {
  initialData?: Record<string, unknown>
  onSubmit: (data: unknown) => Promise<void>
  isLoading?: boolean
}

const LEVEL_STYLES: Record<number, { label: string; style: React.CSSProperties }> = {
  1: { label:"Iniciante", style: { backgroundColor: 'var(--lia-bg-tertiary)', color: 'var(--lia-text-secondary)' } },
  2: { label:"Básico", style: { backgroundColor: 'var(--lia-bg-tertiary)', color: 'var(--lia-text-secondary)' } },
  3: { label:"Intermediário", style: { backgroundColor: 'var(--lia-bg-secondary)', color: 'var(--lia-text-primary)' } },
  4: { label:"Avançado", style: { backgroundColor: 'var(--lia-btn-primary-bg)', color: 'var(--lia-btn-primary-text)' } },
  5: { label:"Expert", style: { backgroundColor: 'var(--lia-btn-primary-bg)', color: 'var(--lia-btn-primary-text)' } }
}

export function BehavioralCompetenciesPanel({
  initialData = {},
  onSubmit,
  isLoading = false
}: PanelProps) {
  const [competencies, setCompetencies] = useState<Competency[]>(() => {
    const initial = initialData.competencies as Competency[] | undefined
    if (initial && Array.isArray(initial)) {
      return COMPETENCIES_CATALOG.map((catalogComp) => {
        const existing = initial.find((c) => c.id === catalogComp.id)
        return existing || { ...catalogComp }
      })
    }
    return COMPETENCIES_CATALOG.map((c) => ({ ...c }))
  })

  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())

  const handleLevelChange = (competencyId: string, level: number) => {
    setCompetencies((prev) =>
      prev.map((c) => (c.id === competencyId ? { ...c, level } : c))
    )
  }

  const toggleExpanded = (competencyId: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(competencyId)) {
        next.delete(competencyId)
      } else {
        next.add(competencyId)
      }
      return next
    })
  }

  const handleSubmit = async () => {
    const data: BehavioralCompetenciesData = {
      competencies: competencies.map((c) => ({
        id: c.id,
        name: c.name,
        description: c.description,
        level: c.level,
        behaviors: c.behaviors,
        questions: c.questions
      }))
    }
    try {
      await onSubmit(data)
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Erro ao salvar competências. Tente novamente."
      )
    }
  }

  const getAverageLevel = () => {
    const sum = competencies.reduce((acc, c) => acc + c.level, 0)
    return (sum / competencies.length).toFixed(1)
  }

  return (
    <div className="space-y-6">
      <Card className="rounded-xl dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
        <CardHeader className="pb-3 dark:border-lia-border-subtle">
          <CardTitle className="text-sm flex items-center justify-between font-sans">
            <span className="flex items-center gap-2">
              🧠 Competências Comportamentais
            </span>
            <Chip density="relaxed" variant="neutral" muted >
              Média: {getAverageLevel()}
            </Chip>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-1">
          {competencies.map((competency) => (
            <CompetencyCard
              key={competency.id}
              competency={competency}
              isExpanded={expandedIds.has(competency.id)}
              onToggleExpand={() => toggleExpanded(competency.id)}
              onLevelChange={(level) => handleLevelChange(competency.id, level)}
            />
          ))}
        </CardContent>
      </Card>

      <Card className="rounded-xl dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
        <CardHeader className="pb-3 dark:border-lia-border-subtle">
          <CardTitle className="text-sm font-sans">📊 Perfil de Competências</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-2">
            {competencies.map((c) => (
              <div key={c.id} className="flex items-center justify-between text-xs">
                <span className="truncate flex-1">{c.name}</span>
                <div className="flex gap-0.5 ml-2">
                  {[1, 2, 3, 4, 5].map((level) => (
                    <div
                      key={level}
                      className="w-2 h-2 rounded-full"
                      style={{backgroundColor: level <= c.level
                          ? 'var(--lia-btn-primary-bg)'
                          : 'var(--lia-bg-tertiary)'}} /* dynamic */
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Button
        onClick={handleSubmit}
        disabled={isLoading}
        className="w-full bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
        size="lg"
      >
        {isLoading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none mr-2" />
            Salvando...
          </>
        ) : ("Concluído"
        )}
      </Button>
    </div>
  )
}

function CompetencyCard({
  competency,
  isExpanded,
  onToggleExpand,
  onLevelChange
}: {
  competency: Competency
  isExpanded: boolean
  onToggleExpand: () => void
  onLevelChange: (level: number) => void
}) {
  return (
    <div className="border rounded-xl overflow-hidden dark:border-lia-border-subtle dark:bg-lia-bg-secondary">
      <button
        type="button"
        className="w-full text-left p-3 hover:bg-lia-bg-tertiary/50 dark:hover:bg-lia-bg-inverse/50 transition-colors motion-reduce:transition-none"
        onClick={onToggleExpand}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-2 flex-1 min-w-0">
            {isExpanded ? (
              <ChevronDown className="h-4 w-4 mt-0.5 text-lia-text-tertiary shrink-0" />
            ) : (
              <ChevronRight className="h-4 w-4 mt-0.5 text-lia-text-tertiary shrink-0" />
            )}
            <div className="min-w-0">
              <div className="font-medium text-sm">{competency.name}</div>
              <div className="text-xs text-lia-text-tertiary line-clamp-1">
                {competency.description}
              </div>
            </div>
          </div>
          <Chip variant="neutral" muted
            className="shrink-0 text-xs"
            style={LEVEL_STYLES[competency.level].style}
          >
            {LEVEL_STYLES[competency.level].label}
          </Chip>
        </div>
      </button>

      <div className="px-3 pb-3">
        <div className="flex items-center gap-2">
          <Label className="text-xs text-lia-text-tertiary shrink-0">Nível:</Label>
          <div className="flex gap-1 flex-1">
            {[1, 2, 3, 4, 5].map((level) => (
              <button
                key={level}
                type="button"
                onClick={(e) => {
                  e.stopPropagation()
                  onLevelChange(level)
                }}
                className="flex-1 h-8 rounded-md text-xs font-medium transition-colors motion-reduce:transition-none"
                style={
                  level === competency.level
                    ? { backgroundColor: 'var(--lia-btn-primary-bg)', color: 'var(--lia-btn-primary-text)', boxShadow: 'var(--lia-shadow-sm)' }
                    : level <= competency.level
                    ? { backgroundColor: 'var(--lia-bg-tertiary)', color: 'var(--lia-text-primary)' }
                    : { backgroundColor: 'var(--lia-bg-secondary)', color: 'var(--lia-text-tertiary)' }
                }
              >
                {level}
              </button>
            ))}
          </div>
        </div>
      </div>

      {isExpanded && (
        <div className="px-3 pb-3 pt-2 border-t border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-tertiary/30 dark:bg-lia-bg-primary/30 space-y-3">
          {competency.behaviors && competency.behaviors.length > 0 && (
            <div>
              <div className="flex items-center gap-1 text-xs font-medium text-lia-text-tertiary mb-2">
                <Target className="h-3 w-3" />
                Comportamentos Esperados
              </div>
              <ul className="space-y-1">
                {competency.behaviors.map((behavior, index) => (
                  <li key={`behavior-${index}`} className="text-xs flex items-start gap-2">
                    <span className="mt-1 text-lia-text-secondary">•</span>
                    <span>{behavior}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {competency.questions && competency.questions.length > 0 && (
            <div>
              <div className="flex items-center gap-1 text-xs font-medium text-lia-text-tertiary mb-2">
                <MessageCircle className="h-3 w-3" />
                Perguntas de Exemplo
              </div>
              <ul className="space-y-2">
                {competency.questions.map((question, index) => (
                  <li
                    key={`question-${index}`}
                    className="text-xs p-2 rounded-xl border italic dark:border-lia-border-subtle dark:bg-lia-bg-secondary bg-lia-bg-primary border-lia-border-subtle"
                  >"{question}"
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
