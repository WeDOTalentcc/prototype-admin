"use client"

import { useState } from "react"
import { Shield, ChevronUp, ChevronDown } from "lucide-react"

export function CompanyDefaultQuestions({
  questions,
  disabledIds,
  isEditing,
  onToggle,
}: {
  questions: Array<{ id: string; question: string; is_eliminatory: boolean; expected_answer?: string }>
  disabledIds: Set<string>
  isEditing: boolean
  onToggle: (id: string, enabled: boolean) => void
}) {
  const [isExpanded, setIsExpanded] = useState(true)
  const activeCount = questions.filter(q => !disabledIds.has(q.id)).length

  return (
    <div className="border border-lia-border-subtle rounded-xl bg-lia-bg-primary overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-lia-interactive-hover dark:hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none"
      >
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-lia-text-tertiary" />
          <span className="text-xs uppercase tracking-wider font-semibold text-lia-text-tertiary">
            Padrão da Empresa
          </span>
          {questions.length > 0 && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-lia-bg-tertiary text-lia-text-secondary">
              {activeCount}/{questions.length} ativas
            </span>
          )}
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-lia-text-muted" />
        ) : (
          <ChevronDown className="w-4 h-4 text-lia-text-muted" />
        )}
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 space-y-2">
          {questions.length === 0 ? (
            <p className="text-xs text-lia-text-muted text-center py-4 italic">
              Nenhuma pergunta padrão configurada. Acesse <strong>Configurações → Perguntas Padrão</strong>.
            </p>
          ) : (
            questions.map(q => {
              const enabled = !disabledIds.has(q.id)
              return (
                <div
                  key={q.id}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors motion-reduce:transition-none ${
 enabled
                      ? 'bg-lia-bg-primary'
                      : 'bg-lia-bg-secondary/50 opacity-50'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={enabled}
                    disabled={!isEditing}
                    onChange={e => onToggle(q.id, e.target.checked)}
                    className="w-3.5 h-3.5 rounded-xl border-lia-border-default accent-lia-btn-primary-bg cursor-pointer disabled:cursor-default"
                  />
                  <span className="text-xs text-lia-text-secondary flex-1">
                    {q.question}
                  </span>
                  {q.is_eliminatory && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-status-error/10 text-status-error dark:bg-status-error/30 dark:text-status-error">
                      eliminatória
                    </span>
                  )}
                </div>
              )
            })
          )}
        </div>
      )}
    </div>
  )
}

