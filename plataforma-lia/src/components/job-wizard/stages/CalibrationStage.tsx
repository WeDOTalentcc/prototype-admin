'use client'

import React, { useState } from 'react'
import { 
  User, Briefcase, MapPin, GraduationCap, CheckCircle2, XCircle,
  ChevronLeft, ChevronRight, Linkedin, Star, Clock, Building,
  Loader2, Trophy, Target
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useWizardContext } from '../WizardContext'
import type { CalibrationCandidate } from '../types'

export function CalibrationStage() {
  const {
    calibrationCandidates,
    currentCalibrationIndex,
    setCurrentCalibrationIndex,
    approvedCandidates,
    setApprovedCandidates,
    rejectedCandidates,
    setRejectedCandidates
  } = useWizardContext()

  const [isLoading, setIsLoading] = useState(false)

  const currentCandidate = calibrationCandidates[currentCalibrationIndex]
  const totalCandidates = calibrationCandidates.length
  const processedCount = approvedCandidates.length + rejectedCandidates.length
  const calibrationComplete = processedCount >= Math.min(5, totalCandidates) && totalCandidates > 0

  const handleApprove = (candidateId: string) => {
    if (!approvedCandidates.includes(candidateId)) {
      setApprovedCandidates(prev => [...prev, candidateId])
      setRejectedCandidates(prev => prev.filter(id => id !== candidateId))
    }
    goToNext()
  }

  const handleReject = (candidateId: string) => {
    if (!rejectedCandidates.includes(candidateId)) {
      setRejectedCandidates(prev => [...prev, candidateId])
      setApprovedCandidates(prev => prev.filter(id => id !== candidateId))
    }
    goToNext()
  }

  const goToNext = () => {
    if (currentCalibrationIndex < totalCandidates - 1) {
      setCurrentCalibrationIndex(currentCalibrationIndex + 1)
    }
  }

  const goToPrevious = () => {
    if (currentCalibrationIndex > 0) {
      setCurrentCalibrationIndex(currentCalibrationIndex - 1)
    }
  }

  const getCandidateStatus = (candidateId: string) => {
    if (approvedCandidates.includes(candidateId)) return 'approved'
    if (rejectedCandidates.includes(candidateId)) return 'rejected'
    return 'pending'
  }

  // Loading state
  if (isLoading || (totalCandidates === 0 && !calibrationComplete)) {
    return (
      <div className="flex flex-col items-center justify-center py-12 gap-4" role="status" aria-live="polite" aria-label="Carregando...">
        <Loader2 className="w-8 h-8 text-lia-text-secondary dark:text-lia-text-tertiary animate-spin motion-reduce:animate-none" />
        <div className="text-center">
          <p className="text-sm lia-text-strong font-medium" aria-live="polite" aria-atomic="true">
            Buscando candidatos compatíveis...
          </p>
          <p className="text-xs lia-text-secondary mt-1">
            Analisando perfis no mercado
          </p>
        </div>
      </div>
    )
  }

  // Calibration complete
  if (calibrationComplete) {
    return (
      <div className="flex flex-col items-center justify-center py-12 gap-4">
        <div className="w-16 h-16 rounded-full bg-status-success/10 flex items-center justify-center">
          <Trophy className="w-8 h-8 text-status-success" />
        </div>
        <div className="text-center">
          <p className="text-sm lia-text-strong font-semibold">
            Calibração Concluída!
          </p>
          <p className="text-xs lia-text-secondary mt-1">
            {approvedCandidates.length} aprovado(s) • {rejectedCandidates.length} rejeitado(s)
          </p>
        </div>
        <div className="flex gap-3 mt-2">
          <div className="flex items-center gap-1 px-3 py-1.5 bg-status-success/10 rounded-md">
            <CheckCircle2 className="w-4 h-4 text-status-success" />
            <span className="text-xs font-medium text-status-success">{approvedCandidates.length}</span>
          </div>
          <div className="flex items-center gap-1 px-3 py-1.5 bg-status-error/10 rounded-md">
            <XCircle className="w-4 h-4 text-status-error" />
            <span className="text-xs font-medium text-status-error">{rejectedCandidates.length}</span>
          </div>
        </div>
        <p className="text-micro lia-text-secondary text-center max-w-xs" aria-live="polite" aria-atomic="true">
          O algoritmo de busca foi calibrado com suas preferências. 
          Os candidatos no kanban serão priorizados de acordo.
        </p>
      </div>
    )
  }

  if (!currentCandidate) {
    return (
      <div className="text-center py-8 lia-text-secondary">
        <User className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p className="text-sm" aria-live="polite" aria-atomic="true">Nenhum candidato disponível</p>
      </div>
    )
  }

  const status = getCandidateStatus(currentCandidate.id)

  return (
    <div className="space-y-3">
      {/* Progress bar */}
      <div className="flex items-center gap-2 mb-3">
        <span className="text-micro lia-text-secondary">
          Calibração: {processedCount}/{Math.min(5, totalCandidates)}
        </span>
        <div className="flex-1 h-1 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gray-900 transition-[width,height] duration-300"
            style={{width: `${(processedCount / Math.min(5, totalCandidates)) * 100}%`}}
          />
        </div>
      </div>

      {/* Navigation dots */}
      <div className="flex items-center justify-center gap-1">
        {calibrationCandidates.slice(0, 5).map((c, i) => {
          const cStatus = getCandidateStatus(c.id)
          return (
            <button
              key={c.id}
              onClick={() => setCurrentCalibrationIndex(i)}
              className={cn(
 "w-2 h-2 rounded-full transition-[width,height]",
                i === currentCalibrationIndex && "w-4",
                cStatus === 'approved' ? "bg-status-success" :
                cStatus === 'rejected' ? "bg-status-error" :
                i === currentCalibrationIndex ? "bg-gray-900" : "bg-gray-300"
              )}
            />
          )
        })}
      </div>

      {/* Candidate Card */}
      <div className={cn(
 "rounded-md border overflow-hidden transition-colors",
        status === 'approved' ? "border-status-success bg-status-success/5" :
        status === 'rejected' ? "border-status-error/30 bg-status-error/10" :
        "border-lia-border-subtle"
      )}>
        {/* Header */}
        <div className="p-3 bg-lia-bg-primary border-b border-lia-border-subtle flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-gray-100 dark:from-gray-800 to-wedo-cyan-dark flex items-center justify-center text-white font-semibold text-lg">
            {currentCandidate.name?.charAt(0) || 'C'}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold lia-text-strong truncate">
                {currentCandidate.name}
              </h3>
              {currentCandidate.linkedinUrl && (
                <a href={currentCandidate.linkedinUrl} target="_blank" rel="noopener noreferrer" className="lia-text-base">
                  <Linkedin className="w-4 h-4" />
                </a>
              )}
            </div>
            <p className="text-xs lia-text-secondary truncate">{currentCandidate.currentRole}</p>
            <p className="text-micro lia-text-secondary truncate">{currentCandidate.currentCompany}</p>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-1 justify-end">
              <Star className="w-4 h-4 fill-amber-400 text-status-warning" />
              <span className="text-sm font-semibold lia-text-strong">{currentCandidate.overallScore || 85}%</span>
            </div>
            <span className="text-micro lia-text-secondary">Match Score</span>
          </div>
        </div>

        {/* Content */}
        <div className="p-3 bg-lia-bg-primary space-y-3">
          {/* Highlights */}
          {currentCandidate.highlights && currentCandidate.highlights.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {currentCandidate.highlights.map((h, i) => (
                <div key={i} className="flex items-center gap-1 px-2 py-1 bg-gray-50 rounded-md">
                  <span className="text-micro">{h.icon}</span>
                  <span className="text-micro lia-text-secondary">{h.label}:</span>
                  <span className="text-micro font-medium lia-text-strong">{h.value}</span>
                </div>
              ))}
            </div>
          )}

          {/* Location & Experience */}
          <div className="flex items-center gap-3 text-xs">
            <div className="flex items-center gap-1 lia-text-secondary">
              <MapPin className="w-3 h-3" />
              {currentCandidate.location}
            </div>
            <div className="flex items-center gap-1 lia-text-secondary">
              <Clock className="w-3 h-3" />
              {currentCandidate.totalExperience || '5+ anos'}
            </div>
            <div className="flex items-center gap-1 lia-text-secondary">
              <GraduationCap className="w-3 h-3" />
              {currentCandidate.education}
            </div>
          </div>

          {/* Skills */}
          {currentCandidate.skillMap && currentCandidate.skillMap.length > 0 && (
            <div>
              <span className="text-micro font-semibold lia-text-secondary uppercase">Skills</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {currentCandidate.skillMap.flatMap(sm => sm.skills).slice(0, 8).map((skill, i) => (
                  <span key={i} className="px-1.5 py-0.5 bg-wedo-cyan/10 text-wedo-cyan-dark text-micro rounded-full">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Match Criteria */}
          {currentCandidate.matchCriteria && currentCandidate.matchCriteria.length > 0 && (
            <div>
              <span className="text-micro font-semibold lia-text-secondary uppercase flex items-center gap-1">
                <Target className="w-3 h-3" />
                Critérios de Match
              </span>
              <div className="mt-1 space-y-1">
                {currentCandidate.matchCriteria.slice(0, 4).map((mc) => (
                  <div key={mc.id} className="flex items-center gap-2 text-micro">
                    {mc.isMatch ? (
                      <CheckCircle2 className="w-3 h-3 text-status-success" />
                    ) : (
                      <XCircle className="w-3 h-3 text-status-error" />
                    )}
                    <span className={mc.isMatch ? "lia-text-strong" : "lia-text-secondary"}>
                      {mc.criteria}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="p-3 bg-gray-50 border-t border-lia-border-subtle flex items-center gap-2">
          <button
            onClick={goToPrevious}
            disabled={currentCalibrationIndex === 0}
            className="p-2 lia-text-secondary hover:lia-text-base disabled:opacity-50"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          
          <button
            onClick={() => handleReject(currentCandidate.id)}
            className={cn(
 "flex-1 py-2 px-4 rounded-md text-xs font-medium transition-colors flex items-center justify-center gap-1.5",
              status === 'rejected'
                ? "bg-status-error text-white"
                : "border border-status-error/30 text-status-error hover:bg-status-error/10"
            )}
          >
            <XCircle className="w-4 h-4" />
            Rejeitar
          </button>
          
          <button
            onClick={() => handleApprove(currentCandidate.id)}
            className={cn(
 "flex-1 py-2 px-4 rounded-md text-xs font-medium transition-colors flex items-center justify-center gap-1.5",
              status === 'approved'
                ? "bg-status-success text-white"
                : "bg-gray-900 text-white hover:bg-gray-800 dark:hover:bg-gray-200"
            )}
          >
            <CheckCircle2 className="w-4 h-4" />
            Aprovar
          </button>
          
          <button
            onClick={goToNext}
            disabled={currentCalibrationIndex === totalCandidates - 1}
            className="p-2 lia-text-secondary hover:lia-text-base disabled:opacity-50"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Feedback note */}
      <p className="text-micro lia-text-secondary text-center" aria-live="polite" aria-atomic="true">
        Suas avaliações ajudam a LIA a entender melhor o perfil ideal para esta vaga
      </p>
    </div>
  )
}

export default CalibrationStage
