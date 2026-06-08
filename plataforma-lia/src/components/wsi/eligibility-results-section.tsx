"use client"

import { useState } from "react"
import { CheckCircle2, XCircle, ChevronDown, ShieldCheck, ShieldX } from "lucide-react"

export interface EligibilityResultItem {
  id: string
  question: string
  answer?: string
  passed: boolean
  is_eliminatory?: boolean
  reconsideration?: string
}

interface EligibilityResultsSectionProps {
  results: EligibilityResultItem[]
}

export function EligibilityResultsSection({ results }: EligibilityResultsSectionProps) {
  if (!results || results.length === 0) return null

  const allPassed = results.every((r) => r.passed)
  const eliminatingQuestion = results.find((r) => !r.passed && r.is_eliminatory !== false)
  const [expanded, setExpanded] = useState(!allPassed)

  return (
    <div
      className="rounded-xl overflow-hidden"
      style={{
        border: `1px solid ${allPassed ? "var(--status-success-border)" : "var(--status-error-border)"}`,
        background: allPassed ? "var(--status-success-bg)" : "var(--status-error-bg)",
      }}
    >
      <button
        type="button"
        className="w-full flex items-center justify-between px-4 py-3 text-left transition-colors"
        style={{ background: "transparent" }}
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
      >
        <div className="flex items-center gap-2.5">
          <div
            className="w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0"
            style={{
              background: allPassed ? "var(--status-success-bg-15, rgba(22,163,74,0.12))" : "var(--status-error-bg-15, rgba(220,38,38,0.12))",
            }}
          >
            {allPassed ? (
              <ShieldCheck className="w-4 h-4" style={{ color: "var(--status-success)" }} />
            ) : (
              <ShieldX className="w-4 h-4" style={{ color: "var(--status-error)" }} />
            )}
          </div>
          <div>
            <p className="text-xs font-semibold" style={{ color: "var(--lia-text-primary)" }}>
              Pré-triagem — Elegibilidade
            </p>
            <p
              className="text-xs mt-0.5 font-medium"
              style={{ color: allPassed ? "var(--status-success)" : "var(--status-error)" }}
            >
              {allPassed
                ? `✅ Todas as ${results.length} perguntas atendidas`
                : eliminatingQuestion
                  ? `❌ Eliminado(a) — ${eliminatingQuestion.question.length > 60 ? eliminatingQuestion.question.slice(0, 60) + "…" : eliminatingQuestion.question}`
                  : "❌ Candidato(a) eliminado(a) nesta fase"}
            </p>
          </div>
        </div>
        <ChevronDown
          className="w-4 h-4 flex-shrink-0 transition-transform motion-reduce:transition-none"
          style={{
            color: "var(--lia-text-disabled)",
            transform: expanded ? "rotate(180deg)" : "rotate(0deg)",
          }}
        />
      </button>

      {expanded && (
        <div
          className="divide-y"
          style={{
            borderTop: `1px solid ${allPassed ? "var(--status-success-border)" : "var(--status-error-border)"}`,
          }}
        >
          {results.map((item, i) => (
            <div
              key={item.id || i}
              className="px-4 py-3"
              style={{
                background: !item.passed ? "var(--status-error-bg-15, rgba(220,38,38,0.06))" : "transparent",
                borderColor: allPassed ? "var(--status-success-border)" : "var(--status-error-border)",
              }}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0 space-y-1">
                  <p className="text-xs leading-relaxed" style={{ color: "var(--lia-text-tertiary)" }}>
                    <span className="font-medium" style={{ color: "var(--lia-text-secondary)" }}>
                      Pergunta:{" "}
                    </span>
                    {item.question}
                  </p>
                  {item.answer && (
                    <p className="text-xs leading-relaxed" style={{ color: "var(--lia-text-secondary)" }}>
                      <span className="font-medium">Resposta: </span>
                      {item.answer}
                    </p>
                  )}
                  {item.reconsideration && (
                    <p
                      className="text-xs italic mt-1.5 pl-2"
                      style={{
                        color: "var(--lia-text-disabled)",
                        borderLeft: "2px solid var(--status-error-border)",
                      }}
                    >
                      {item.reconsideration}
                    </p>
                  )}
                </div>
                <div className="flex-shrink-0 mt-0.5">
                  {item.passed ? (
                    <span
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium whitespace-nowrap"
                      style={{
                        background: "var(--status-success-bg)",
                        color: "var(--status-success)",
                        border: "1px solid var(--status-success-border)",
                      }}
                    >
                      <CheckCircle2 className="w-3 h-3" />
                      Atendido
                    </span>
                  ) : (
                    <span
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium whitespace-nowrap"
                      style={{
                        background: "var(--status-error-bg)",
                        color: "var(--status-error)",
                        border: "1px solid var(--status-error-border)",
                      }}
                    >
                      <XCircle className="w-3 h-3" />
                      Não atendido
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
