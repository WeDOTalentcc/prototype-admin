"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import React from"react"
import { getScoreBadgeClasses } from"@/lib/score-utils"
import { Sheet, SheetContent, SheetHeader, SheetTitle } from"@/components/ui/sheet"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import { ScrollArea } from"@/components/ui/scroll-area"
import { Separator } from"@/components/ui/separator"
import { 
  MapPin, 
  Briefcase, 
  Mail, 
  Phone, 
  Linkedin, 
  ExternalLink,
  Calendar,
  GraduationCap,
  Languages,
  Star,
  UserPlus,
  MessageSquare,
  FileText,
  Send,
  CheckCircle,
  Copy,
  X,
  Database,
  Globe,
  Eye,
  Save,
  Loader2,
  Zap
} from"lucide-react"
import { CandidateResult } from"./search-results-card"
import { textStyles, buttonStyles, cardStyles, badgeStyles } from"@/lib/design-tokens"

interface CandidateExperience {
  title: string
  company: string
  location?: string
  start_date?: string
  end_date?: string
  is_current?: boolean
  description?: string
}

interface CandidateEducation {
  degree?: string
  field_of_study?: string
  school: string
  start_date?: string
  end_date?: string
}

interface ExtendedCandidateProfile extends CandidateResult {
  summary?: string
  experiences?: CandidateExperience[]
  education?: CandidateEducation[]
  languages?: { language: string; proficiency?: string }[]
  match_summary?: string
  insights?: {
    overall_summary?: string
    strengths?: string[]
    concerns?: string[]
    outreach_message?: string
  }
}

interface CandidateDetailSidebarProps {
  open: boolean
  onClose: () => void
  candidate: ExtendedCandidateProfile | null
  onAddToJob?: (candidateId: string) => void
  onContact?: (candidateId: string, method:"email" |"phone" |"linkedin") => void
  onSendMessage?: (candidateId: string) => void
  onSaveToBase?: (candidateId: string) => void
}

export function CandidateDetailSidebar({
  open,
  onClose,
  candidate,
  onAddToJob,
  onContact,
  onSendMessage,
  onSaveToBase
}: CandidateDetailSidebarProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('candidate-detail-sidebar', open)

  if (!candidate) return null

  const getInitials = (name: string) => {
    const parts = name.split("")
    return parts.length > 1 
      ? `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
      : name.slice(0, 2).toUpperCase()
  }

  const getScoreColor = (score?: number) => {
    if (!score) return"bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary"
    return getScoreBadgeClasses(score)
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  return (
    <Sheet open={open} onOpenChange={() => onClose()}>
      <SheetContent className="w-[450px] sm:w-panel-xl p-0 bg-lia-bg-primary dark:bg-lia-bg-primary border-lia-border-subtle dark:border-lia-border-subtle">
        <SheetHeader className="p-6 pb-4 dark:border-lia-border-subtle">
          <div className="flex items-start gap-4">
            <Avatar className="h-16 w-16">
              {candidate.picture_url ? (
                <AvatarImage src={candidate.picture_url} alt={candidate.name} />
              ) : null}
              <AvatarFallback className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary text-lg">
                {getInitials(candidate.name)}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <SheetTitle className="text-xl font-semibold text-lia-text-primary">
                  {candidate.name}
                </SheetTitle>
                {candidate.is_open_to_work && (
                  <Chip variant="success" muted className="bg-status-success/15 dark:bg-status-success/30">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Aberto
                  </Chip>
                )}
              </div>
              {candidate.current_title && (
                <p className="text-lia-text-secondary mt-1">
                  {candidate.current_title}
                  {candidate.current_company && ` @ ${candidate.current_company}`}
                </p>
              )}
              {candidate.location && (
                <p className="text-sm text-lia-text-primary flex items-center gap-1 mt-1">
                  <MapPin className="h-3 w-3" />
                  {candidate.location}
                </p>
              )}
              <div className="flex flex-col gap-1 mt-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <Chip 
                    variant="neutral" 
                    className={`${
                      candidate.source ==="local" 
                        ?"border-lia-border-default dark:border-lia-border-default bg-lia-bg-secondary dark:bg-lia-bg-secondary text-lia-text-secondary" 
                        :"border-lia-border-default dark:border-lia-border-default bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary"
                    }`}
                  >
                    {candidate.source ==="local" ? (
                      <>
                        <Database className="h-3 w-3 mr-1" />
                        Base local
                      </>
                    ) : (
                      <>
                        <Globe className="h-3 w-3 mr-1" />
                        Base Global
                      </>
                    )}
                  </Chip>
                  {candidate.enrichment_source && (
                    <Chip 
                      variant="neutral" 
                      className={`${
                        candidate.enrichment_source === "apify"
                          ? "border-status-info/30 bg-status-info/10 text-status-info"
                          : candidate.enrichment_source === "pearch"
                          ? "border-wedo-cyan/30 bg-wedo-cyan/10 text-wedo-cyan-text"
                          : "border-lia-border-default bg-lia-bg-secondary text-lia-text-secondary"
                      }`}
                    >
                      <Zap className="h-3 w-3 mr-1" />
                      {candidate.enrichment_source === "apify" ? "Apify" : candidate.enrichment_source === "pearch" ? "Pearch" : "Local"}
                    </Chip>
                  )}
                  {candidate.is_enriching && (
                    <Chip variant="info" className="bg-status-info/10">
                      <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                      Enriquecendo...
                    </Chip>
                  )}
                  {candidate.is_discovered && (
                    <Chip 
                      variant="warning" 
                      className="bg-status-warning/10 dark:bg-status-warning/30"
                    >
                      <Eye className="h-3 w-3 mr-1" />
                      Descoberto
                    </Chip>
                  )}
                  {candidate.score && (
                    <Chip variant="neutral" muted className={getScoreColor(candidate.score)}>
                      <Star className="h-3 w-3 mr-1" />
                      {Math.round(candidate.score)}% match
                    </Chip>
                  )}
                </div>
                {candidate.is_discovered && (
                  <p className="text-xs text-status-warning">
                    Candidato descoberto - ainda não salvo na sua base local
                  </p>
                )}
                {!candidate.is_discovered && candidate.source ==="pearch" && (
                  <p className="text-xs text-lia-text-secondary">
                    Candidato encontrado na busca global (Pearch)
                  </p>
                )}
              </div>
            </div>
          </div>
        </SheetHeader>

        <ScrollArea className="h-[calc(100vh-280px)]">
          <div className="p-6 space-y-6">
            {candidate.insights?.overall_summary && (
              <div>
                <h4 className="text-sm font-medium text-lia-text-primary mb-2 flex items-center gap-2">
                  <Star className="h-4 w-4 text-lia-text-secondary" />
                  Resumo do Match
                </h4>
                <p className="text-sm text-lia-text-secondary bg-lia-bg-secondary dark:bg-lia-bg-secondary p-3 rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle">
                  {candidate.insights.overall_summary}
                </p>
              </div>
            )}

            {candidate.summary && (
              <div>
                <h4 className="text-sm font-medium text-lia-text-primary mb-2">Sobre</h4>
                <p className="text-sm text-lia-text-secondary">{candidate.summary}</p>
              </div>
            )}

            {candidate.skills.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-lia-text-primary mb-2">Habilidades</h4>
                <div className="flex flex-wrap gap-1.5">
                  {candidate.skills.map((skill) => (
                    <Chip 
                      key={skill} 
                      variant="neutral" muted 
                      className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-primary font-normal"
                    >
                      {skill}
                    </Chip>
                  ))}
                </div>
              </div>
            )}

            {candidate.experiences && candidate.experiences.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-lia-text-primary mb-3 flex items-center gap-2">
                  <Briefcase className="h-4 w-4" />
                  Experiência
                </h4>
                <div className="space-y-4">
                  {candidate.experiences.slice(0, 3).map((exp, idx) => (
                    <div key={`exp-${idx}`} className="relative pl-4 border-l-2 border-lia-border-subtle dark:border-lia-border-subtle">
                      <div className="absolute -left-[5px] top-0 w-2 h-2 rounded-full bg-lia-border-default" />
                      <p className="font-medium text-lia-text-primary">{exp.title}</p>
                      <p className="text-sm text-lia-text-secondary">{exp.company}</p>
                      {(exp.start_date || exp.end_date) && (
                        <p className="text-xs text-lia-text-primary flex items-center gap-1 mt-1">
                          <Calendar className="h-3 w-3" />
                          {exp.start_date} - {exp.is_current ?"Atual" : exp.end_date}
                        </p>
                      )}
                      {exp.description && (
                        <p className="text-sm text-lia-text-primary mt-1 line-clamp-2">{exp.description}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {candidate.education && candidate.education.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-lia-text-primary mb-3 flex items-center gap-2">
                  <GraduationCap className="h-4 w-4" />
                  Formação
                </h4>
                <div className="space-y-3">
                  {candidate.education.slice(0, 2).map((edu, idx) => (
                    <div key={`edu-${idx}`}>
                      <p className="font-medium text-lia-text-primary">{edu.school}</p>
                      {(edu.degree || edu.field_of_study) && (
                        <p className="text-sm text-lia-text-secondary">
                          {edu.degree}{edu.field_of_study && ` em ${edu.field_of_study}`}
                        </p>
                      )}
                      {(edu.start_date || edu.end_date) && (
                        <p className="text-xs text-lia-text-primary">
                          {edu.start_date} - {edu.end_date ||"Atual"}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {candidate.languages && candidate.languages.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-lia-text-primary mb-2 flex items-center gap-2">
                  <Languages className="h-4 w-4" />
                  Idiomas
                </h4>
                <div className="flex flex-wrap gap-2">
                  {candidate.languages.map((lang, idx) => (
                    <Chip key={`lang-${idx}`} variant="neutral" className="border-lia-border-default dark:border-lia-border-default">
                      {lang.language}
                      {lang.proficiency && ` (${lang.proficiency})`}
                    </Chip>
                  ))}
                </div>
              </div>
            )}

            {candidate.insights?.strengths && candidate.insights.strengths.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-lia-text-primary mb-2">Pontos Fortes</h4>
                <ul className="space-y-1">
                  {candidate.insights.strengths.map((strength, idx) => (
                    <li key={`str-${idx}`} className="text-sm text-lia-text-secondary flex items-start gap-2">
                      <CheckCircle className="h-4 w-4 text-status-success mt-0.5 flex-shrink-0" />
                      {strength}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {candidate.insights?.outreach_message && (
              <div>
                <h4 className="text-sm font-medium text-lia-text-primary mb-2 flex items-center gap-2">
                  <MessageSquare className="h-4 w-4" />
                  Sugestão de Mensagem
                </h4>
                <div className="relative">
                  <p className="text-sm text-lia-text-secondary bg-lia-bg-secondary dark:bg-lia-bg-secondary p-3 rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle pr-10">
                    {candidate.insights.outreach_message}
                  </p>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute top-2 right-2 h-6 w-6"
                    onClick={() => copyToClipboard(candidate.insights?.outreach_message ||"")}
                  >
                    <Copy className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            )}


            <div>
              <h4 className="text-sm font-medium text-lia-text-primary mb-3">Contato</h4>
              <div className="space-y-2">
                {candidate.email && (
                  <div className="flex items-center justify-between p-2 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
                    <div className="flex items-center gap-2">
                      <Mail className={`h-4 w-4 ${candidate.contact_source === "apify" ? "text-status-info" : "text-lia-text-primary"}`} />
                      <span className="text-sm text-lia-text-primary">{candidate.email}</span>
                      {candidate.contact_source === "apify" && <span className="text-xs text-status-info">(Apify)</span>}
                      {candidate.contact_source === "pearch" && <span className="text-xs text-lia-text-tertiary">(Pearch)</span>}
                    </div>
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        onClick={() => copyToClipboard(candidate.email ||"")}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        onClick={() => onContact?.(candidate.id,"email")}
                      >
                        <Send className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                )}
                {candidate.phone && (
                  <div className="flex items-center justify-between p-2 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
                    <div className="flex items-center gap-2">
                      <Phone className={`h-4 w-4 ${candidate.contact_source === "apify" ? "text-status-info" : "text-lia-text-primary"}`} />
                      <span className="text-sm text-lia-text-primary">{candidate.phone}</span>
                      {candidate.contact_source === "apify" && <span className="text-xs text-status-info">(Apify)</span>}
                      {candidate.contact_source === "pearch" && <span className="text-xs text-lia-text-tertiary">(Pearch)</span>}
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7"
                      onClick={() => copyToClipboard(candidate.phone ||"")}
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                )}
                {candidate.linkedin_url && (
                  <a 
                    href={candidate.linkedin_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="flex items-center justify-between p-2 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none"
                  >
                    <div className="flex items-center gap-2">
                      <Linkedin className="h-4 w-4 text-lia-text-secondary" />
                      <span className="text-sm text-lia-text-primary">Ver perfil no LinkedIn</span>
                    </div>
                    <ExternalLink className="h-4 w-4 text-lia-text-secondary" />
                  </a>
                )}
                {!candidate.email && !candidate.phone && candidate.has_email && (
                  <p className="text-sm text-lia-text-primary italic">
                    Email disponível via Apify ($0.01)
                  </p>
                )}
                {!candidate.phone && candidate.has_phone && (
                  <p className="text-sm text-lia-text-primary italic">
                    Telefone disponível via Apify ($0.01)
                  </p>
                )}
              </div>
            </div>
          </div>
        </ScrollArea>

        <div className="p-4 border-t border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-secondary">
          <div className="flex flex-col gap-2">
            {candidate.is_discovered && onSaveToBase && (
              <Button 
                variant="outline"
                className="w-full border-lia-btn-primary-bg dark:border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-tertiary dark:bg-lia-bg-secondary"
                onClick={() => onSaveToBase(candidate.id)}
              >
                <Save className="h-4 w-4 mr-2" />
                Salvar na Base Local
              </Button>
            )}
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                className="flex-1 border-lia-border-default dark:border-lia-border-default"
                onClick={onClose}
              >
                <X className="h-4 w-4 mr-2" />
                Fechar
              </Button>
              {onAddToJob && (
                <Button 
                  className="flex-1 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active text-white"
                  onClick={() => onAddToJob(candidate.id)}
                >
                  <UserPlus className="h-4 w-4 mr-2" />
                  Adicionar à vaga
                </Button>
              )}
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  )
}

export default CandidateDetailSidebar
