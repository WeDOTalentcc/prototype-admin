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
        <div className={`w-8 h-8 rounded-md flex items-center justify-center transition-all ${
          candidate.technicalTestScore
            ? 'bg-wedo-purple/15 dark:bg-wedo-purple/30 text-wedo-purple dark:text-wedo-purple'
            : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-600'
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
        <div className={`w-8 h-8 rounded-md flex items-center justify-center transition-all ${
          candidate.englishTestScore
            ? 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400'
            : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-600'
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
        <div className={`w-8 h-8 rounded-md flex items-center justify-center transition-all ${
          candidate.bigFiveScores
            ? 'bg-pink-100 dark:bg-pink-900/30 text-pink-700 dark:text-pink-400'
            : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-600'
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
