"use client"

import { Button } from "@/components/ui/button"
import {
  Star, Phone, Mail, Linkedin, ExternalLink, Calendar,
  Briefcase, ClipboardCheck, MessageSquareText
} from "lucide-react"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { toast } from "sonner"
import type { CandidateData } from "./ProfileTabTypes"

interface CandidatePreviewActionBarProps {
  c: CandidateData
  candidate: Record<string, unknown>
  onSendEmail?: (candidate: Record<string, unknown>) => void
  onSendWhatsApp?: (candidate: Record<string, unknown>) => void
  onSendAgendamento?: (candidate: Record<string, unknown>) => void
  onScheduleInterview?: (candidate: Record<string, unknown>) => void
  onWSIScreening?: (candidate: Record<string, unknown>) => void
  onSendTriagem?: (candidate: Record<string, unknown>) => void
  onAddToVacancy?: (candidate: Record<string, unknown>) => void
  onToggleFavorite?: (candidateId: string) => void
  onSendFeedback?: (candidate: Record<string, unknown>) => void
  isFavorite: boolean
}

export function CandidatePreviewActionBar({
  c,
  candidate,
  onSendEmail,
  onSendWhatsApp,
  onSendAgendamento,
  onScheduleInterview,
  onWSIScreening,
  onSendTriagem,
  onAddToVacancy,
  onToggleFavorite,
  onSendFeedback,
  isFavorite,
}: CandidatePreviewActionBarProps) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-1.5 flex-wrap">
        
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
              onClick={() => onSendEmail ? onSendEmail(candidate) : (c.email && window.open(`mailto:${c.email}`, '_self'))}
              disabled={!c.email && !onSendEmail}
            >
              <Mail className="w-3.5 h-3.5 text-lia-text-secondary" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="text-xs">Email</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
              onClick={() => {
                if (onSendWhatsApp) {
                  onSendWhatsApp(candidate)
                } else if (c.phone) {
                  window.open(`https://wa.me/${(c.phone as string).replace(/\D/g, '')}`, '_blank')
                }
              }}
              disabled={!c.phone && !onSendWhatsApp}
            >
              <Phone className="w-3.5 h-3.5 text-lia-text-secondary" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="text-xs">WhatsApp</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
              onClick={() => onSendAgendamento ? onSendAgendamento(candidate) : onScheduleInterview?.(candidate)}
            >
              <Calendar className="w-3.5 h-3.5 text-wedo-orange" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="text-xs">Agendar Entrevista</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
              onClick={() => onWSIScreening ? onWSIScreening(candidate) : onSendTriagem?.(candidate)}
            >
              <ClipboardCheck className="w-3.5 h-3.5 text-lia-text-secondary" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="text-xs">Triagem WSI</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
              onClick={() => onAddToVacancy?.(candidate)}
            >
              <Briefcase className="w-3.5 h-3.5 text-lia-text-secondary" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="text-xs">Atribuir à Vaga</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className={`h-6 w-6 p-0 ${isFavorite ? 'bg-status-warning/15' : 'hover:bg-status-warning/10'}`}
              onClick={() => {
                onToggleFavorite?.(c.id as string)
                toast.success(isFavorite ? "Removido dos favoritos" : "Adicionado aos favoritos", { description: isFavorite ? "Candidato removido da lista de favoritos" : "Candidato adicionado à lista de favoritos" })
              }}
            >
              <Star className={`w-3.5 h-3.5 ${isFavorite ? 'text-status-warning fill-amber-500' : 'text-status-warning'}`} />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="text-xs">{isFavorite ? 'Remover dos Favoritos' : 'Adicionar aos Favoritos'}</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
              onClick={() => onSendFeedback?.(candidate)}
            >
              <MessageSquareText className="w-3.5 h-3.5 text-wedo-purple" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="text-xs">Enviar Feedback</TooltipContent>
        </Tooltip>

        <span className="lia-text-muted mx-0.5">|</span>

        <Tooltip>
          <TooltipTrigger asChild>
            <a 
              href={((c.linkedin as string | undefined) || (c.linkedin_url as string | undefined) || '#')} 
              target="_blank" 
              rel="noopener noreferrer" 
              className={`p-1 rounded-md transition-colors motion-reduce:transition-none ${(c.linkedin || c.linkedin_url) ? 'hover:bg-wedo-cyan/10' : 'opacity-30 cursor-default'}`}
              onClick={(e) => !(c.linkedin || c.linkedin_url) && e.preventDefault()}
            >
              <Linkedin className={`w-3.5 h-3.5 ${(c.linkedin || c.linkedin_url) ? 'text-lia-text-secondary' : 'text-lia-text-tertiary'}`} />
            </a>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="text-xs">LinkedIn</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <a 
              href={((c.github as string | undefined) || (c.github_url as string | undefined) || '#')} 
              target="_blank" 
              rel="noopener noreferrer" 
              className={`p-1 rounded-md transition-colors motion-reduce:transition-none ${(c.github || c.github_url) ? 'hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse' : 'opacity-30 cursor-default'}`}
              onClick={(e) => !(c.github || c.github_url) && e.preventDefault()}
            >
              <svg className="w-3.5 h-3.5" fill={(c.github || c.github_url) ? 'var(--lia-btn-primary-bg)' : 'var(--lia-text-tertiary)'} viewBox="0 0 24 24">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
            </a>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="text-xs">GitHub</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <a 
              href={((c.stackoverflow as string | undefined) || (c.stackoverflow_url as string | undefined) || '#')} 
              target="_blank" 
              rel="noopener noreferrer" 
              className={`p-1 rounded-md transition-colors motion-reduce:transition-none ${(c.stackoverflow || c.stackoverflow_url) ? 'hover:bg-wedo-orange/10' : 'opacity-30 cursor-default'}`}
              onClick={(e) => !(c.stackoverflow || c.stackoverflow_url) && e.preventDefault()}
            >
              <svg className="w-3.5 h-3.5" fill={(c.stackoverflow || c.stackoverflow_url) ? 'var(--lia-text-secondary)' : 'var(--lia-text-tertiary)'} viewBox="0 0 24 24">
                <path d="M15 21h-10v-2h10v2zm6-11.665l-1.621-9.335-1.993.346 1.62 9.335 1.994-.346zm-5.964 6.937l-9.746-.975-.186 2.016 9.755.879.177-1.92zm.538-2.587l-9.276-2.608-.526 1.954 9.306 2.5.496-1.846zm1.204-2.413l-8.297-4.864-1.029 1.743 8.298 4.865 1.028-1.744zm1.866-1.467l-5.339-7.829-1.672 1.14 5.339 7.829 1.672-1.14zm-2.644 4.195v8h-12v-8h-2v10h16v-10h-2z"/>
              </svg>
            </a>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="text-xs">Stack Overflow</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <a 
              href={((c.twitter as string | undefined) || (c.twitter_url as string | undefined) || (c.x_url as string | undefined) || '#')} 
              target="_blank" 
              rel="noopener noreferrer" 
              className={`p-1 rounded-md transition-colors motion-reduce:transition-none ${(c.twitter || c.twitter_url || c.x_url) ? 'hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse' : 'opacity-30 cursor-default'}`}
              onClick={(e) => !(c.twitter || c.twitter_url || c.x_url) && e.preventDefault()}
            >
              <svg className="w-3.5 h-3.5" fill={(c.twitter || c.twitter_url || c.x_url) ? 'var(--lia-btn-primary-bg)' : 'var(--lia-text-tertiary)'} viewBox="0 0 24 24">
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
              </svg>
            </a>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="text-xs">X (Twitter)</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <a 
              href={((c.behance as string | undefined) || (c.behance_url as string | undefined) || '#')}
              target="_blank" 
              rel="noopener noreferrer" 
              className={`p-1 rounded-md transition-colors motion-reduce:transition-none ${(c.behance || c.behance_url) ? 'hover:bg-wedo-cyan/10' : 'opacity-30 cursor-default'}`}
              onClick={(e) => !(c.behance || c.behance_url) && e.preventDefault()}
            >
              <svg className="w-3.5 h-3.5" fill={(c.behance || c.behance_url) ? 'var(--lia-text-secondary)' : 'var(--lia-text-tertiary)'} viewBox="0 0 24 24">
                <path d="M22 7h-7v-2h7v2zm1.726 10c-.442 1.297-2.029 3-5.101 3-3.074 0-5.564-1.729-5.564-5.675 0-3.91 2.325-5.92 5.466-5.92 3.082 0 4.964 1.782 5.375 4.426.078.506.109 1.188.095 2.14h-8.027c.13 3.211 3.483 3.312 4.588 2.029h3.168zm-7.686-4h4.965c-.105-1.547-1.136-2.219-2.477-2.219-1.466 0-2.277.768-2.488 2.219zm-9.574 6.988h-6.466v-14.967h6.953c5.476.081 5.58 5.444 2.72 6.906 3.461 1.26 3.577 8.061-3.207 8.061zm-3.466-8.988h3.584c2.508 0 2.906-3-.312-3h-3.272v3zm3.391 3h-3.391v3.016h3.341c3.055 0 2.868-3.016.05-3.016z"/>
              </svg>
            </a>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="text-xs">Behance</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <a 
              href={((c.portfolio as string | undefined) || (c.portfolio_url as string | undefined) || '#')} 
              target="_blank" 
              rel="noopener noreferrer" 
              className={`p-1 rounded-md transition-colors motion-reduce:transition-none ${(c.portfolio || c.portfolio_url) ? 'hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse' : 'opacity-30 cursor-default'}`}
              onClick={(e) => !(c.portfolio || c.portfolio_url) && e.preventDefault()}
            >
              <ExternalLink className={`w-3.5 h-3.5 ${(c.portfolio || c.portfolio_url) ? 'text-lia-text-secondary' : 'text-lia-text-muted'}`} />
            </a>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="text-xs">Portfolio</TooltipContent>
        </Tooltip>
      </div>
    </div>
  )
}
