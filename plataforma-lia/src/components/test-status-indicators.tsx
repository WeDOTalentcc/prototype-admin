"use client"

import React from "react"
import { CheckCircle, FileText, Globe, User } from "lucide-react"

interface TestStatusIndicatorsProps {
  candidate: any
}

export function TestStatusIndicators({ candidate }: TestStatusIndicatorsProps) {
  return (
    <div className="flex items-center gap-2">
      {/* Teste Técnico */}
      <div
        className="relative group"
        title={candidate.technicalTestScore ? `Teste Técnico: ${candidate.technicalTestScore}%` : 'Teste Técnico: Pendente'}
      >
        <div className={`w-8 h-8 rounded-md flex items-center justify-center transition-colors ${
 candidate.technicalTestScore
            ? 'bg-wedo-purple/15 dark:bg-wedo-purple/30 text-wedo-purple dark:text-wedo-purple'
            : 'bg-gray-100 dark:bg-lia-bg-secondary text-gray-600'
        }`}>
          <FileText className="w-4 h-4" />
        </div>
        {candidate.technicalTestScore && (
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
        <div className={`w-8 h-8 rounded-md flex items-center justify-center transition-colors ${
 candidate.englishTestScore
            ? 'bg-wedo-purple/15 dark:bg-wedo-purple/30 text-wedo-purple dark:text-wedo-purple'
            : 'bg-gray-100 dark:bg-lia-bg-secondary text-gray-600'
        }`}>
          <Globe className="w-4 h-4" />
        </div>
        {candidate.englishTestScore && (
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
        <div className={`w-8 h-8 rounded-md flex items-center justify-center transition-colors ${
 candidate.bigFiveScores
            ? 'bg-wedo-magenta/15 dark:bg-wedo-magenta/30 text-wedo-magenta dark:text-wedo-magenta'
            : 'bg-gray-100 dark:bg-lia-bg-secondary text-gray-600'
        }`}>
          <User className="w-4 h-4" />
        </div>
        {candidate.bigFiveScores && (
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
