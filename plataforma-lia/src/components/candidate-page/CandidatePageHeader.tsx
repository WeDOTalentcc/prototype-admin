// @ts-nocheck
"use client"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { LiaAnalysisModal } from "@/components/modals/lia-analysis-modal"
import {
  X, MapPin, Phone, Mail, Linkedin, Calendar as CalendarIcon,
  ClipboardCheck, Briefcase, Users, MessageSquare, Brain, Globe,
} from "lucide-react"
import { Github } from "lucide-react"

type CandidateRecord = {
  name: string
  id?: string
  candidateId?: string
  avatar_url?: string
  avatar?: string
  phone?: string
  position?: string
  location?: string
  linkedin_url?: string
  linkedinUrl?: string
  github_url?: string
  portfolio_url?: string
  website?: string
  email?: string
  liaAnalysis?: { score?: number; fitScore?: number }
  [key: string]: unknown
}

interface CandidatePageHeaderProps {
  _candidate: CandidateRecord
  liaScore: number
  showLiaAnalysisModal: boolean
  setShowLiaAnalysisModal: (value: boolean) => void
  handleAnalysisTransport: () => void
  getScoreColor: (score: number) => string
  onClose: () => void
  onSendEmail?: (candidate: Record<string, unknown>) => void
  onSendWhatsApp?: (candidate: Record<string, unknown>) => void
  onSendAgendamento?: (candidate: Record<string, unknown>) => void
  onWSIScreening?: (candidate: Record<string, unknown>) => void
  onAddToVacancy?: (candidate: Record<string, unknown>) => void
  onAddToList?: (candidate: Record<string, unknown>) => void
  onSendFeedback?: (candidate: Record<string, unknown>) => void
  candidate: Record<string, unknown>
}

export function CandidatePageHeader({
  _candidate,
  liaScore,
  showLiaAnalysisModal,
  setShowLiaAnalysisModal,
  handleAnalysisTransport,
  getScoreColor,
  onClose,
  onSendEmail,
  onSendWhatsApp,
  onSendAgendamento,
  onWSIScreening,
  onAddToVacancy,
  onAddToList,
  onSendFeedback,
  candidate,
}: CandidatePageHeaderProps) {
  return (
    <TooltipProvider delayDuration={200}>
      <div className="bg-white dark:bg-lia-bg-secondary border-b border-lia-border-subtle dark:border-lia-border-subtle px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Avatar className="w-10 h-10">
              <AvatarImage src={(_candidate.avatar_url as string | undefined) || (_candidate.avatar as string | undefined)} alt={_candidate.name as string} />
              <AvatarFallback className="text-sm font-medium bg-gray-200 lia-text-base">
                {(_candidate.name as string).split( ).map((n: string) => n[0]).join().slice(0, 2).toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-semibold text-lia-text-primary">{_candidate.name as string}</h1>
                <Badge variant="outline" className="text-xs px-1.5 py-0">
                  {_candidate.candidateId || _candidate.id}
                </Badge>
                <Badge className={}>
                  {liaScore}% Match
                </Badge>
              </div>
              <div className="flex items-center gap-2 text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                <span>{_candidate.position as string | undefined}</span>
                <span className="lia-text-secondary">•</span>
                <MapPin className="w-3 h-3" />
                <span>{_candidate.location as string | undefined}</span>
              </div>
            </div>
          </div>

          {/* Right Side: Social Icons + LIA + Close */}
          <div className="flex items-center gap-2">
            {/* Social Icons */}
            <div className="flex items-center gap-1 mr-2">
              {(_candidate.linkedin_url || _candidate.linkedinUrl) && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <a
                      href={_candidate.linkedin_url || _candidate.linkedinUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-1.5 hover:bg-gray-100 rounded-md transition-colors motion-reduce:transition-none"
                    >
                      <Linkedin className="w-4 h-4 lia-text-base" />
                    </a>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="text-xs">LinkedIn</TooltipContent>
                </Tooltip>
              )}
              {((_candidate.github_url as string | undefined) || (_candidate.githubUrl as string | undefined)) && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <a
                      href={(_candidate.github_url as string | undefined) || (_candidate.githubUrl as string | undefined)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-1.5 hover:bg-gray-100 rounded-md transition-colors motion-reduce:transition-none"
                    >
                      <Github className="w-4 h-4 text-lia-text-primary" />
                    </a>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="text-xs">GitHub</TooltipContent>
                </Tooltip>
              )}
              {((_candidate.portfolio_url as string | undefined) || (_candidate.portfolioUrl as string | undefined) || (_candidate.website as string | undefined)) && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <a
                      href={(_candidate.portfolio_url as string | undefined) || (_candidate.portfolioUrl as string | undefined) || (_candidate.website as string | undefined)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-1.5 hover:bg-gray-100 rounded-md transition-colors motion-reduce:transition-none"
                    >
                      <Globe className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                    </a>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="text-xs">Portfolio</TooltipContent>
                </Tooltip>
              )}
            </div>

            {/* Quick Action Buttons */}
            <div className="flex items-center gap-1 border-l border-lia-border-subtle dark:border-lia-border-default pl-3 ml-1">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                    onClick={() => onSendEmail ? onSendEmail(candidate) : (_candidate.email && window.open(, _self))}
                    disabled={!_candidate.email && !onSendEmail}
                  >
                    <Mail className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Email</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                    onClick={() => {
                      if (onSendWhatsApp) {
                        onSendWhatsApp(candidate)
                      } else if (_candidate.phone) {
                        window.open(, _blank)
                      }
                    }}
                    disabled={!_candidate.phone && !onSendWhatsApp}
                  >
                    <Phone className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">WhatsApp</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                    onClick={() => onSendAgendamento?.(candidate)}
                  >
                    <CalendarIcon className="w-4 h-4 text-wedo-orange" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Agendar Entrevista</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                    onClick={() => onWSIScreening?.(candidate)}
                  >
                    <ClipboardCheck className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Triagem WSI</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                    onClick={() => onAddToVacancy?.(candidate)}
                  >
                    <Briefcase className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Adicionar à Vaga</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                    onClick={() => onAddToList?.(candidate)}
                  >
                    <Users className="w-4 h-4 text-wedo-green" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Adicionar à Lista</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                    onClick={() => onSendFeedback?.(candidate)}
                  >
                    <MessageSquare className="w-4 h-4 text-wedo-purple" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Enviar Feedback</TooltipContent>
              </Tooltip>
            </div>

            {/* LIA Analysis Button */}
            <LiaAnalysisModal
              isOpen={showLiaAnalysisModal}
              onOpen={() => setShowLiaAnalysisModal(true)}
              onClose={() => setShowLiaAnalysisModal(false)}
              candidate={_candidate}
              onTransportToOpinions={handleAnalysisTransport}
            >
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0 hover:bg-gray-100 border border-lia-border-default rounded-md"
                  >
                    <Brain className="w-5 h-5 text-wedo-cyan" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Análises LIA</TooltipContent>
              </Tooltip>
            </LiaAnalysisModal>

            {/* Close Button */}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="sm" onClick={onClose} className="h-7 w-7 p-0">
                  <X className="w-3.5 h-3.5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="text-xs">Fechar</TooltipContent>
            </Tooltip>
          </div>
        </div>
      </div>
    </TooltipProvider>
  )
}
