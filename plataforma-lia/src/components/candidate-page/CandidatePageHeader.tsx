"use client"

import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from"@/components/ui/tooltip"
import {
  X, MapPin, Phone, Mail, Linkedin, Calendar as CalendarIcon,
  ClipboardCheck, Briefcase, Users, MessageSquare, Brain, Globe,
} from"lucide-react"
import { Github } from"lucide-react"
import { CandidateAvatar } from"@/components/candidate-profile/CandidateAvatar"
import { CandidateScoreBadge } from"@/components/candidate-profile/CandidateScoreBadge"
import { EditableField } from "@/components/candidate-profile/EditableField"
import { useCandidateEdit } from "@/components/candidate-profile/CandidateEditContext"

type CandidateRecord = {
  name: string
  id?: string
  candidateId?: string
  headline?: string
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
  const { editable, updateField, isSaving } = useCandidateEdit()
  const handleSave = (fieldName: string) => async (value: string) => {
    if (!updateField) return { success: false, error: "Edit indisponivel" }
    return await updateField(fieldName, value)
  }
  return (
    <TooltipProvider delayDuration={200}>
      <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary dark:border-lia-border-subtle px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CandidateAvatar
              name={_candidate.name as string}
              avatarUrl={(_candidate.avatar_url as string | undefined) || (_candidate.avatar as string | undefined)}
              size="md"
            />
            <div>
              <div className="flex items-center gap-2">
                {editable ? (
                  <EditableField
                    value={_candidate.name as string}
                    onSave={handleSave("name")}
                    label="nome"
                    placeholder="Nome do candidato"
                    saving={isSaving?.("name") ?? false}
                    className="text-base font-semibold"
                  />
                ) : (
                  <h1 className="text-base font-semibold text-lia-text-primary">{_candidate.name as string}</h1>
                )}
                <Chip density="relaxed" variant="neutral" className="px-1.5 py-0">
                  {_candidate.candidateId || _candidate.id}
                </Chip>
                <CandidateScoreBadge score={liaScore} format="percent" />
              </div>
              {editable && (
                <div className="text-xs text-lia-text-secondary mt-0.5">
                  <EditableField
                    value={(_candidate.headline as string | undefined) ?? ""}
                    onSave={handleSave("headline")}
                    label="headline"
                    placeholder="Headline profissional"
                    saving={isSaving?.("headline") ?? false}
                    emptyDisplay="Adicionar headline"
                  />
                </div>
              )}
              <div className="flex items-center gap-2 text-xs text-lia-text-secondary">
                {editable ? (
                  <EditableField
                    value={_candidate.position as string | undefined}
                    onSave={handleSave("current_title")}
                    label="cargo atual"
                    placeholder="Cargo / posição"
                    saving={isSaving?.("current_title") ?? false}
                    emptyDisplay="Adicionar cargo"
                  />
                ) : (
                  <span>{_candidate.position as string | undefined}</span>
                )}
                <span className="lia-text-secondary">•</span>
                <MapPin className="w-3 h-3" aria-hidden="true" />
                {editable ? (
                  <EditableField
                    value={_candidate.location as string | undefined}
                    onSave={handleSave("location_city")}
                    label="localização"
                    placeholder="Cidade, Estado"
                    saving={isSaving?.("location_city") ?? false}
                    emptyDisplay="Adicionar localização"
                  />
                ) : (
                  <span>{_candidate.location as string | undefined}</span>
                )}
              </div>
              {editable && (
                <div
                  className="flex items-center gap-3 text-xs text-lia-text-secondary mt-1 flex-wrap"
                  data-testid="header-editable-details-row"
                >
                  <span className="flex items-center gap-1">
                    <span className="text-micro text-lia-text-tertiary">Anos exp:</span>
                    <EditableField
                      value={_candidate.years_of_experience as number | undefined}
                      onSave={handleSave("years_of_experience")}
                      type="number"
                      label="anos de experiência"
                      placeholder="0"
                      saving={isSaving?.("years_of_experience") ?? false}
                      emptyDisplay="—"
                      showPencilWhenEmpty
                    />
                  </span>
                  <span className="lia-text-secondary">•</span>
                  <span className="flex items-center gap-1">
                    <Github className="w-3 h-3" aria-hidden="true" />
                    <EditableField
                      value={(_candidate.github_url as string | undefined) ?? ""}
                      onSave={handleSave("github_url")}
                      type="url"
                      label="GitHub"
                      placeholder="https://github.com/usuario"
                      saving={isSaving?.("github_url") ?? false}
                      emptyDisplay="Adicionar GitHub"
                      showPencilWhenEmpty
                    />
                  </span>
                  <span className="lia-text-secondary">•</span>
                  <span className="flex items-center gap-1">
                    <Globe className="w-3 h-3" aria-hidden="true" />
                    <EditableField
                      value={(_candidate.portfolio_url as string | undefined) ?? ""}
                      onSave={handleSave("portfolio_url")}
                      type="url"
                      label="Portfolio"
                      placeholder="https://exemplo.com"
                      saving={isSaving?.("portfolio_url") ?? false}
                      emptyDisplay="Adicionar Portfolio"
                      showPencilWhenEmpty
                    />
                  </span>
                </div>
              )}
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
                      className="p-1.5 hover:bg-lia-bg-tertiary rounded-xl transition-colors motion-reduce:transition-none"
                    >
                      <Linkedin className="w-4 h-4 text-lia-text-secondary" />
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
                      className="p-1.5 hover:bg-lia-bg-tertiary rounded-xl transition-colors motion-reduce:transition-none"
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
                      className="p-1.5 hover:bg-lia-bg-tertiary rounded-xl transition-colors motion-reduce:transition-none"
                    >
                      <Globe className="w-4 h-4 text-lia-text-secondary" />
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
                    className="h-7 w-7 p-0 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
                    onClick={() => onSendEmail ? onSendEmail(candidate) : (_candidate.email && window.open(`mailto:${_candidate.email}`, '_self'))}
                    disabled={!_candidate.email && !onSendEmail}
                  >
                    <Mail className="w-4 h-4 text-lia-text-secondary" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Email</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
                    onClick={() => {
                      if (onSendWhatsApp) {
                        onSendWhatsApp(candidate)
                      } else if (_candidate.phone) {
                        window.open(`https://wa.me/${_candidate.phone.replace(/\D/g, '')}`, '_blank')
                      }
                    }}
                    disabled={!_candidate.phone && !onSendWhatsApp}
                  >
                    <Phone className="w-4 h-4 text-lia-text-secondary" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">WhatsApp</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
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
                    className="h-7 w-7 p-0 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
                    onClick={() => onWSIScreening?.(candidate)}
                  >
                    <ClipboardCheck className="w-4 h-4 text-lia-text-secondary" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Triagem WSI</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
                    onClick={() => onAddToVacancy?.(candidate)}
                  >
                    <Briefcase className="w-4 h-4 text-lia-text-secondary" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Adicionar à Vaga</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
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
                    className="h-7 w-7 p-0 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
                    onClick={() => onSendFeedback?.(candidate)}
                  >
                    <MessageSquare className="w-4 h-4 text-wedo-purple" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Enviar Feedback</TooltipContent>
              </Tooltip>
            </div>

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
