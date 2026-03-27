"use client"

import React from "react"
import { Brain, ChevronRight } from "lucide-react"

interface ScreeningNotificationCardProps {
  candidateName: string
  jobTitle: string
  wsiScore?: number
  wsiBlocks?: Array<{ name: string; score: number }>
  recommendation: "aprovado" | "reprovado" | "avaliação_manual"
  source: string
  timestamp: string
  onViewDetails?: () => void
  className?: string
}

export function ScreeningNotificationCard({
  candidateName,
  jobTitle,
  wsiScore,
  wsiBlocks = [],
  recommendation,
  source,
  timestamp,
  onViewDetails,
  className = "",
}: ScreeningNotificationCardProps) {
  const recommendationConfig = {
    aprovado: {
      borderColor: "border-l-emerald-500",
      badgeBg: "bg-emerald-50 dark:bg-emerald-900/20",
      badgeText: "text-emerald-700 dark:text-emerald-300",
      label: "Aprovado",
    },
    reprovado: {
      borderColor: "border-l-red-500",
      badgeBg: "bg-red-50 dark:bg-red-900/20",
      badgeText: "text-red-700 dark:text-red-300",
      label: "Reprovado",
    },
    avaliação_manual: {
      borderColor: "border-l-amber-500",
      badgeBg: "bg-amber-50 dark:bg-amber-900/20",
      badgeText: "text-amber-700 dark:text-amber-300",
      label: "Avaliação Manual",
    },
  }

  const config = recommendationConfig[recommendation]

  return (
    <div
      className={`rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 border-l-4 ${config.borderColor} ${className}`}
    >
      <div className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <div className="p-1.5 rounded bg-wedo-cyan/10 dark:bg-wedo-cyan-dark/20">
            <Brain className="w-4 h-4 text-wedo-cyan" />
          </div>
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-50">
            Triagem Automática Concluída
          </h3>
        </div>

        <div className="space-y-3">
          <div>
            <p className="text-xs text-gray-500 dark:text-gray-400">Candidato</p>
            <p className="text-sm font-medium text-gray-900 dark:text-gray-50">
              {candidateName}
            </p>
          </div>

          <div>
            <p className="text-xs text-gray-500 dark:text-gray-400">Vaga</p>
            <p className="text-sm font-medium text-gray-900 dark:text-gray-50">
              {jobTitle}
            </p>
          </div>

          {wsiScore !== undefined && (
            <div>
              <div className="flex items-center justify-between mb-1">
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Pontuação WSI
                </p>
                <p className="font-['Inter',sans-serif] text-sm font-semibold text-gray-900 dark:text-gray-50">
                  {wsiScore}/100
                </p>
              </div>
              <div className="h-2 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${
                    wsiScore >= 75
                      ? "bg-emerald-500"
                      : wsiScore >= 50
                        ? "bg-amber-500"
                        : "bg-red-500"
                  }`}
                  style={{ width: `${wsiScore}%` }}
                />
              </div>
            </div>
          )}

          {wsiBlocks && wsiBlocks.length > 0 && (
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                Dimensões
              </p>
              <div className="grid grid-cols-2 gap-2">
                {wsiBlocks.map((block, index) => (
                  <div
                    key={index}
                    className="p-2 rounded bg-gray-50 dark:bg-gray-700/50"
                  >
                    <p className="text-micro text-gray-600 dark:text-gray-400">
                      {block.name}
                    </p>
                    <p className="font-['Inter',sans-serif] text-xs font-semibold text-gray-900 dark:text-gray-50">
                      {block.score}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="pt-2">
            <span
              className={`inline-flex items-center px-2 py-1 rounded-full text-micro font-medium ${config.badgeBg} ${config.badgeText}`}
            >
              {config.label}
            </span>
          </div>

          <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
            <p className="text-micro text-gray-500 dark:text-gray-400">
              Triagem automática via inscrição pelo website
            </p>
          </div>
        </div>
      </div>

      {onViewDetails && (
        <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/30 rounded-b-md">
          <button
            onClick={onViewDetails}
            className="flex items-center gap-1.5 text-sm font-medium text-wedo-cyan-dark dark:text-wedo-cyan hover:text-wedo-cyan-dark dark:hover:text-wedo-cyan transition-colors"
          >
            Ver Detalhes
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </div>
  )
}
