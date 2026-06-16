"use client"

import React from "react"
import { CheckCircle, FileText, Globe, User } from "lucide-react"

interface TestStatusIndicatorsProps {
  candidate: Record<string, unknown>
}

export function TestStatusIndicators({ candidate }: TestStatusIndicatorsProps) {
  return (
    <div className="flex items-center gap-2">
      {/* Teste Técnico */}
      <div
        className="relative group"
        title={candidate.technicalTestScore ? `Teste Técnico: ${candidate.technicalTestScore}%` : 'Teste Técnico: Pendente'}
      >
        <div className={`w-8 h-8 rounded-md flex items-center justify-center transition-colors motion-reduce:transition-none ${
 candidate.technicalTestScore
            ? 'bg-wedo-purple/15 dark:bg-wedo-purple/30 text-wedo-purple-text dark:text-wedo-purple'
            : 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary'
        }`}>
          <FileText className="w-4 h-4" />
        </div>
        {!!candidate.technicalTestScore && (
          <div className="absolute -top-1 -right-1">
            <div className="w-4 h-4 bg-status-success rounded-full flex items-center justify-center">
              <CheckCircle className="w-3 h-3 text-white" fill="currentColor" />
            </div>
          </div>
        )}
      </div>

      {/* Teste de Inglês */}
      <div
        className="relative group"
        title={candidate.englishTestScore ? `Teste de Inglês: ${candidate.englishTestScore}% (${candidate.englishLevel || 'N/A'})` : 'Teste de Inglês: Pendente'}
      >
        <div className={`w-8 h-8 rounded-md flex items-center justify-center transition-colors motion-reduce:transition-none ${
 candidate.englishTestScore
            ? 'bg-wedo-purple/15 dark:bg-wedo-purple/30 text-wedo-purple-text dark:text-wedo-purple'
            : 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary'
        }`}>
          <Globe className="w-4 h-4" />
        </div>
        {!!candidate.englishTestScore && (
          <div className="absolute -top-1 -right-1">
            <div className="w-4 h-4 bg-status-success rounded-full flex items-center justify-center">
              <CheckCircle className="w-3 h-3 text-white" fill="currentColor" />
            </div>
          </div>
        )}
      </div>

      {/* Big Five */}
      <div
        className="relative group"
        title={candidate.bigFiveScores ? 'Assessment Big Five: Completo' : 'Assessment Big Five: Pendente'}
      >
        <div className={`w-8 h-8 rounded-md flex items-center justify-center transition-colors motion-reduce:transition-none ${
 candidate.bigFiveScores
            ? 'bg-wedo-magenta/15 dark:bg-wedo-magenta/30 text-wedo-magenta-text dark:text-wedo-magenta'
            : 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary'
        }`}>
          <User className="w-4 h-4" />
        </div>
        {!!candidate.bigFiveScores && (
          <div className="absolute -top-1 -right-1">
            <div className="w-4 h-4 bg-status-success rounded-full flex items-center justify-center">
              <CheckCircle className="w-3 h-3 text-white" fill="currentColor" />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
