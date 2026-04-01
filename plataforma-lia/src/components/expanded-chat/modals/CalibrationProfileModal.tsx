"use client"

/**
 * CalibrationProfileModal — modal de revisão de perfis de calibração (duplo painel).
 * Painel esquerdo: perfil do candidato (abas experience/education/skillmap).
 * Painel direito: análise LIA, critérios de match, aprovar/reprovar.
 * Extraído de expanded-chat-modal.tsx (Sprint 4.5 — 2026-03-27).
 * Portabilidade Vue: props → defineProps; callbacks → emit.
 */

import {
  ChevronLeft,
  ChevronRight,
  X,
  Star,
  Clock,
  Building2,
  Rocket,
  MapPin,
  CheckCircle2,
  GraduationCap,
} from "lucide-react"
import { cn } from "@/lib/utils"
import type { CalibrationCandidate } from "@/components/expanded-chat/types"

export interface CalibrationProfileModalProps {
  show: boolean
  candidates: CalibrationCandidate[]
  currentIndex: number
  profileTab: 'experience' | 'education' | 'skillmap'
  comment: string
  approvedCount: number
  onSetCurrentIndex: (updater: (prev: number) => number) => void
  onSetProfileTab: (tab: 'experience' | 'education' | 'skillmap') => void
  onSetComment: (comment: string) => void
  onApprove: () => void
  onReject: () => void
  onClose: () => void
  onOpenEditCriteria: () => void
}

export function CalibrationProfileModal({
  show,
  candidates,
  currentIndex,
  profileTab,
  comment,
  approvedCount,
  onSetCurrentIndex,
  onSetProfileTab,
  onSetComment,
  onApprove,
  onReject,
  onClose,
  onOpenEditCriteria,
}: CalibrationProfileModalProps) {
  if (!show || candidates.length === 0) return null

  const candidate = candidates[currentIndex]
  if (!candidate) return null

  return (
    <div className="fixed inset-0 z-overlay flex items-center justify-center bg-black/50">
      <div className="bg-lia-bg-primary rounded-xl w-[95vw] max-w-[1200px] h-[90vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-lia-border-subtle">
          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="flex items-center gap-2 lia-text-secondary hover:lia-text-strong transition-colors motion-reduce:transition-none"
            >
              <ChevronLeft className="w-5 h-5" />
              <span className="text-sm font-medium">
                Review Profiles
              </span>
            </button>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-md hover:bg-gray-50 transition-colors motion-reduce:transition-none"
          >
            <X className="w-5 h-5 lia-text-secondary" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left Panel - Candidate Profile */}
          <div className="flex-1 overflow-y-auto p-6 border-r border-lia-border-subtle">
            <div className="space-y-6">
              {/* Candidate Header */}
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-full bg-gray-900 flex items-center justify-center text-white font-semibold text-sm">
                  {candidate.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h2
                      className="text-base font-semibold lia-text-strong"
                     
                    >
                      {candidate.name}
                    </h2>
                    {candidate.linkedinUrl && (
                      <a
                        href={candidate.linkedinUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="lia-text-secondary hover:lia-text-strong dark:hover:lia-text-muted transition-colors motion-reduce:transition-none"
                      >
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
                        </svg>
                      </a>
                    )}
                    <button className="px-3 py-1 text-xs font-medium bg-white border border-lia-border-default hover:bg-gray-50 dark:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:bg-gray-700 text-lia-text-primary dark:text-lia-text-primary rounded-md transition-colors motion-reduce:transition-none">
                      Full Profile ↗
                    </button>
                  </div>
                  <p className="text-xs lia-text-secondary mt-1">
                    {candidate.location}
                  </p>
                  <p className="text-xs lia-text-strong mt-1">
                    ↻ {candidate.currentRole} at {candidate.currentCompany}
                  </p>
                  <p className="text-xs lia-text-secondary mt-1">
                    ★ {candidate.education}
                  </p>
                </div>
              </div>

              {/* Tabs */}
              <div className="flex gap-1 border-b border-lia-border-subtle">
                {(['experience', 'education', 'skillmap'] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => onSetProfileTab(tab)}
                    className={cn(
 "px-3 py-1.5 text-sm font-medium transition-colors border-b-2",
                      profileTab === tab
                        ? "lia-text-strong border-gray-800"
                        : "lia-text-secondary border-transparent hover:lia-text-strong"
                    )}
                   
                  >
                    {tab === 'experience' ? 'Experience' : tab === 'education' ? 'Education' : 'Skill Map'}
                  </button>
                ))}
              </div>

              {/* Tab Content */}
              {profileTab === 'experience' && (
                <div className="space-y-4">
                  {/* Highlights */}
                  <div className="p-3 bg-gray-50 rounded-md border border-lia-border-subtle">
                    <h4 className="text-sm font-semibold lia-text-strong mb-3">
                      Highlights{' '}
                      <span className="lia-text-secondary font-normal">Show more ({candidate.highlights.length})</span>
                    </h4>
                    <div className="flex flex-wrap gap-3">
                      {candidate.highlights.map((highlight, idx) => (
                        <div key={`hl-${idx}`} className="flex items-center gap-2 px-2 py-1.5 bg-lia-bg-primary rounded-md border border-lia-border-subtle">
                          <div className="w-6 h-6 rounded-md bg-gray-50 flex items-center justify-center">
                            {highlight.icon === 'trophy' && <Star className="w-3.5 h-3.5 text-status-warning" />}
                            {highlight.icon === 'clock' && <Clock className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />}
                            {highlight.icon === 'building' && <Building2 className="w-3.5 h-3.5 text-wedo-purple" />}
                            {highlight.icon === 'rocket' && <Rocket className="w-3.5 h-3.5 text-wedo-green" />}
                            {highlight.icon === 'globe' && <MapPin className="w-3.5 h-3.5 text-wedo-magenta" />}
                          </div>
                          <div>
                            <p className="text-xs font-semibold lia-text-strong">{highlight.label}</p>
                            <p className="text-xs lia-text-secondary">{highlight.value}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Experience Stats */}
                  <div className="flex gap-6 py-3 border-b border-lia-border-subtle">
                    <div>
                      <p className="text-xs lia-text-secondary uppercase tracking-wide">Average Tenure</p>
                      <p className="text-sm font-semibold lia-text-strong">{candidate.averageTenure}</p>
                    </div>
                    <div>
                      <p className="text-xs lia-text-secondary uppercase tracking-wide">Current Tenure</p>
                      <p className="text-sm font-semibold lia-text-strong">{candidate.currentTenure}</p>
                    </div>
                    <div>
                      <p className="text-xs lia-text-secondary uppercase tracking-wide">Total Experience</p>
                      <p className="text-sm font-semibold lia-text-strong">{candidate.totalExperience}</p>
                    </div>
                  </div>

                  {/* Experiences */}
                  <div className="space-y-4">
                    <h4 className="text-sm font-semibold lia-text-strong">
                      Experiences
                    </h4>
                    {candidate.experiences.map((exp) => (
                      <div key={exp.id} className="flex gap-3">
                        <div className="w-8 h-8 rounded-md bg-gray-50 flex items-center justify-center flex-shrink-0">
                          <Building2 className="w-4 h-4 lia-text-secondary" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <p className="text-sm font-semibold lia-text-strong">{exp.company}</p>
                            <span className="text-xs lia-text-secondary">{exp.duration}</span>
                          </div>
                          <div className="flex items-center gap-2 mt-1">
                            <p className="text-sm lia-text-strong">{exp.role}</p>
                            {exp.isPromotion && (
                              <span className="px-2 py-0.5 text-xs font-medium text-wedo-purple bg-wedo-purple/10 rounded-full">
                                Promotion
                              </span>
                            )}
                          </div>
                          <p className="text-xs lia-text-secondary mt-1">{exp.period}</p>
                          {exp.skills.length > 0 && (
                            <p className="text-xs lia-text-secondary mt-2">
                              Skills: {exp.skills.slice(0, 6).join(' · ')}
                              {exp.skills.length > 6 && (
                                <button className="text-lia-text-secondary dark:text-lia-text-tertiary ml-1">Read More</button>
                              )}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {profileTab === 'education' && (
                <div className="space-y-4">
                  {candidate.educationHistory.map((edu) => (
                    <div key={edu.id} className="flex gap-4 p-3 bg-gray-50 rounded-md">
                      <div className="w-8 h-8 rounded-md bg-lia-bg-primary flex items-center justify-center flex-shrink-0">
                        <GraduationCap className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold lia-text-strong">{edu.institution}</p>
                        <p className="text-sm lia-text-secondary">{edu.degree} in {edu.field}</p>
                        <p className="text-xs lia-text-secondary mt-1">{edu.period}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {profileTab === 'skillmap' && (
                <div className="space-y-6">
                  {candidate.skillMap.map((category, idx) => (
                    <div key={`cat-${idx}`}>
                      <h5 className="text-sm font-semibold lia-text-strong mb-2">{category.category}</h5>
                      <div className="flex flex-wrap gap-2">
                        {category.skills.map((skill, sidx) => (
                          <span key={sidx} className="px-2 py-1 text-micro font-medium lia-text-strong bg-gray-50 rounded-full border border-lia-border-subtle">
                            ★ {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}

                  <div>
                    <h5 className="text-sm font-semibold lia-text-strong mb-2">Additional Skills</h5>
                    <div className="flex flex-wrap gap-2">
                      {candidate.additionalSkills.slice(0, 10).map((skill) => (
                        <span key={skill} className="px-3 py-1.5 text-xs lia-text-secondary bg-gray-50 rounded-md">
                          {skill}
                        </span>
                      ))}
                      {candidate.additionalSkills.length > 10 && (
                        <span className="px-3 py-1.5 text-xs text-lia-text-secondary dark:text-lia-text-tertiary font-medium">
                          +{candidate.additionalSkills.length - 10} more skills
                        </span>
                      )}
                    </div>
                  </div>

                  <div>
                    <h5 className="text-sm font-semibold lia-text-strong mb-2">Languages</h5>
                    <div className="flex flex-wrap gap-2">
                      {candidate.languages.map((lang, idx) => (
                        <span key={`lang-${idx}`} className="px-2 py-1 text-xs font-medium lia-text-strong bg-wedo-cyan/10 rounded-md">
                          {lang}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Panel - LIA Analysis & Actions */}
          <div className="w-[380px] flex flex-col bg-gray-50">
            {/* Header */}
            <div className="shrink-0 px-4 pt-4 pb-2">
              <div className="flex items-center justify-between">
                <h3
                  className="text-sm font-semibold lia-text-strong"
                 
                >
                  Por que encontramos este perfil
                </h3>
                <button
                  onClick={onOpenEditCriteria}
                  className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary hover:text-wedo-cyan-dark font-medium transition-colors motion-reduce:transition-none"
                >
                  Editar Critérios
                </button>
              </div>
            </div>

            {/* LIA Insights Box */}
            <div className="shrink-0 px-4 max-h-card-lg overflow-y-auto">
              <div className="p-3 bg-lia-bg-primary rounded-md border border-lia-border-subtle space-y-3">
                {candidate.matchCriteria.map((match) => (
                  <div key={match.id} className="space-y-1">
                    <div className="flex items-start gap-2">
                      <div className={cn(
 "px-1.5 py-0.5 rounded-full text-micro font-medium",
                        match.isMatch ? "bg-wedo-green/10 text-wedo-green" : "bg-status-error/10 text-status-error"
                      )}>
                        {match.isMatch ? '✓ Match' : '✗ No Match'}
                      </div>
                    </div>
                    <p className="text-xs font-semibold lia-text-strong">
                      {match.criteria}
                      <span className="ml-1.5 text-micro lia-text-secondary font-normal">
                        {match.importance === 1 ? '①②' : '①'}
                      </span>
                    </p>
                    <p className="text-micro lia-text-secondary leading-relaxed">
                      {match.explanation}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Comment field */}
            <div className="shrink-0 px-4 py-3">
              <label className="text-xs font-medium lia-text-strong mb-1.5 block">
                Comentário para a LIA (opcional)
              </label>
              <textarea
                value={comment}
                onChange={(e) => onSetComment(e.target.value)}
                placeholder="Ex: Gostei do perfil mas prefiro candidatos com mais experiência em startups..."
                className="w-full px-3 py-2 border border-lia-border-subtle rounded-md text-xs focus:outline-none focus:border-gray-400 resize-none bg-lia-bg-primary"
               
                rows={2}
              />
            </div>

            {/* Edit criteria note */}
            <div className="shrink-0 px-4 pb-3">
              <div className="p-2 bg-gray-50 rounded-md border border-lia-border-subtle">
                <p className="text-micro lia-text-secondary">
                  Você pode{' '}
                  <button onClick={onOpenEditCriteria} className="font-medium">fixar critérios</button>
                  {' '}obrigatórios ou{' '}
                  <button onClick={onOpenEditCriteria} className="lia-text-base font-medium">reordenar</button>
                  {' '}por importância.
                </p>
              </div>
            </div>

            {/* Actions Footer */}
            <div className="shrink-0 px-4 py-3 border-t border-lia-border-subtle bg-lia-bg-primary mt-auto">
              {/* Navigation */}
              <div className="flex items-center justify-between mb-3">
                <button
                  onClick={() => onSetCurrentIndex(prev => Math.max(0, prev - 1))}
                  disabled={currentIndex === 0}
                  className={cn(
 "p-1.5 rounded-md transition-colors",
                    currentIndex === 0 ? "lia-text-muted cursor-not-allowed" : "lia-text-secondary hover:bg-gray-50"
                  )}
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="text-xs lia-text-secondary">
                  Profile {currentIndex + 1}/{candidates.length}
                </span>
                <button
                  onClick={() => onSetCurrentIndex(prev => Math.min(candidates.length - 1, prev + 1))}
                  disabled={currentIndex === candidates.length - 1}
                  className={cn(
 "p-1.5 rounded-md transition-colors",
                    currentIndex === candidates.length - 1 ? "lia-text-muted cursor-not-allowed" : "lia-text-secondary hover:bg-gray-50"
                  )}
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>

              {/* Approve/Reject Buttons */}
              <div className="flex gap-2">
                <button
                  onClick={onApprove}
                  className="flex-1 py-2.5 px-3 bg-gray-900 text-white rounded-md font-medium text-xs hover:bg-gray-800 dark:hover:bg-gray-200 transition-colors motion-reduce:transition-none flex items-center justify-center gap-1.5"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Aprovar
                  <span className="text-micro opacity-80">A</span>
                </button>
                <button
                  onClick={onReject}
                  className="flex-1 py-2.5 px-3 bg-lia-bg-primary text-status-error border border-status-error rounded-md font-medium text-xs hover:bg-status-error/5 transition-colors motion-reduce:transition-none flex items-center justify-center gap-1.5"
                >
                  <X className="w-3.5 h-3.5" />
                  Reprovar
                  <span className="text-micro opacity-80">R</span>
                </button>
              </div>

              <p className="text-micro lia-text-secondary text-center mt-2">
                Isso apenas calibra o agente e não envia emails.
              </p>

              {/* Progress Dots */}
              <div className="mt-2 flex items-center justify-center gap-1.5">
                <span className="text-micro lia-text-secondary">Aprovados:</span>
                <div className="flex gap-1">
                  {[0, 1, 2].map((i) => (
                    <div
                      key={i}
                      className={cn(
 "w-5 h-5 rounded-full flex items-center justify-center text-micro font-medium",
                        approvedCount > i ? "bg-wedo-green text-white" : "bg-gray-200 lia-text-secondary"
                      )}
                    >
                      {approvedCount > i ? '✓' : i + 1}
                    </div>
                  ))}
                </div>
                <span className="text-micro lia-text-secondary">de 3</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
