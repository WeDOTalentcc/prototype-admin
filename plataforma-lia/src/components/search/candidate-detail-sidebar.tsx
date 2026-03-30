"use client"

import React from "react"
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
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
  Save
} from "lucide-react"
import { CandidateResult } from "./search-results-card"
import { textStyles, buttonStyles, cardStyles, badgeStyles } from "@/lib/design-tokens"

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
  onContact?: (candidateId: string, method: "email" | "phone" | "linkedin") => void
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
  if (!candidate) return null

  const getInitials = (name: string) => {
    const parts = name.split(" ")
    return parts.length > 1 
      ? `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
      : name.slice(0, 2).toUpperCase()
  }

  const getScoreColor = (score?: number) => {
    if (!score) return "bg-gray-100 dark:bg-lia-bg-secondary lia-text-600 dark:text-lia-text-tertiary"
    if (score >= 80) return "bg-status-success/15 text-status-success"
    if (score >= 60) return "bg-status-warning/15 text-status-warning"
    return "bg-wedo-orange/15 text-wedo-orange"
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  return (
    <Sheet open={open} onOpenChange={() => onClose()}>
      <SheetContent className="w-[450px] sm:w-panel-xl p-0 bg-white dark:bg-lia-bg-primary border-lia-border-subtle dark:border-lia-border-subtle">
        <SheetHeader className="p-6 pb-4 border-b border-lia-border-subtle dark:border-lia-border-subtle">
          <div className="flex items-start gap-4">
            <Avatar className="h-16 w-16">
              {candidate.picture_url ? (
                <AvatarImage src={candidate.picture_url} alt={candidate.name} />
              ) : null}
              <AvatarFallback className="bg-gray-100 dark:bg-lia-bg-secondary lia-text-600 dark:text-lia-text-tertiary text-lg">
                {getInitials(candidate.name)}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <SheetTitle className="text-xl font-semibold lia-text-800 dark:text-lia-text-primary">
                  {candidate.name}
                </SheetTitle>
                {candidate.is_open_to_work && (
                  <Badge className="bg-status-success/15 dark:bg-status-success/30 text-status-success dark:text-status-success border-status-success/30 dark:border-status-success/30">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Aberto
                  </Badge>
                )}
              </div>
              {candidate.current_title && (
                <p className="lia-text-600 dark:text-lia-text-tertiary mt-1">
                  {candidate.current_title}
                  {candidate.current_company && ` @ ${candidate.current_company}`}
                </p>
              )}
              {candidate.location && (
                <p className="text-sm lia-text-800 dark:text-lia-text-primary flex items-center gap-1 mt-1">
                  <MapPin className="h-3 w-3" />
                  {candidate.location}
                </p>
              )}
              <div className="flex flex-col gap-1 mt-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <Badge 
                    variant="outline" 
                    className={`${
                      candidate.source === "local" 
                        ? "border-lia-border-default dark:border-lia-border-default bg-gray-50 dark:bg-lia-bg-secondary lia-text-600 dark:text-lia-text-tertiary" 
                        : "border-lia-border-default dark:border-lia-border-default bg-gray-100 dark:bg-lia-bg-secondary lia-text-600 dark:text-lia-text-tertiary"
                    }`}
                  >
                    {candidate.source === "local" ? (
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
                  </Badge>
                  {candidate.is_discovered && (
                    <Badge 
                      variant="outline" 
                      className="border-status-warning/30 dark:border-status-warning/30 bg-status-warning/10 dark:bg-status-warning/30 text-status-warning dark:text-status-warning"
                    >
                      <Eye className="h-3 w-3 mr-1" />
                      Descoberto
                    </Badge>
                  )}
                  {candidate.score && (
                    <Badge className={getScoreColor(candidate.score)}>
                      <Star className="h-3 w-3 mr-1" />
                      {Math.round(candidate.score)}% match
                    </Badge>
                  )}
                </div>
                {candidate.is_discovered && (
                  <p className="text-xs text-status-warning">
                    Candidato descoberto - ainda não salvo na sua base local
                  </p>
                )}
                {!candidate.is_discovered && candidate.source === "pearch" && (
                  <p className="text-xs lia-text-500 dark:text-lia-text-tertiary">
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
                <h4 className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-2 flex items-center gap-2">
                  <Star className="h-4 w-4 lia-text-600 dark:text-lia-text-tertiary" />
                  Resumo do Match
                </h4>
                <p className="text-sm lia-text-600 dark:text-lia-text-tertiary bg-gray-50 dark:bg-lia-bg-secondary p-3 rounded-md border border-lia-border-subtle dark:border-lia-border-subtle">
                  {candidate.insights.overall_summary}
                </p>
              </div>
            )}

            {candidate.summary && (
              <div>
                <h4 className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-2">Sobre</h4>
                <p className="text-sm lia-text-600 dark:text-lia-text-tertiary">{candidate.summary}</p>
              </div>
            )}

            {candidate.skills.length > 0 && (
              <div>
                <h4 className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-2">Habilidades</h4>
                <div className="flex flex-wrap gap-1.5">
                  {candidate.skills.map((skill, idx) => (
                    <Badge 
                      key={idx} 
                      variant="secondary" 
                      className="bg-gray-100 dark:bg-lia-bg-secondary lia-text-800 dark:text-lia-text-primary font-normal"
                    >
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {candidate.experiences && candidate.experiences.length > 0 && (
              <div>
                <h4 className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 flex items-center gap-2">
                  <Briefcase className="h-4 w-4" />
                  Experiência
                </h4>
                <div className="space-y-4">
                  {candidate.experiences.slice(0, 3).map((exp, idx) => (
                    <div key={idx} className="relative pl-4 border-l-2 border-lia-border-subtle dark:border-lia-border-subtle">
                      <div className="absolute -left-[5px] top-0 w-2 h-2 rounded-full bg-gray-300 dark:lia-bg-600" />
                      <p className="font-medium lia-text-800 dark:text-lia-text-primary">{exp.title}</p>
                      <p className="text-sm lia-text-600 dark:text-lia-text-tertiary">{exp.company}</p>
                      {(exp.start_date || exp.end_date) && (
                        <p className="text-xs lia-text-800 dark:text-lia-text-primary flex items-center gap-1 mt-1">
                          <Calendar className="h-3 w-3" />
                          {exp.start_date} - {exp.is_current ? "Atual" : exp.end_date}
                        </p>
                      )}
                      {exp.description && (
                        <p className="text-sm lia-text-800 dark:text-lia-text-primary mt-1 line-clamp-2">{exp.description}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {candidate.education && candidate.education.length > 0 && (
              <div>
                <h4 className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3 flex items-center gap-2">
                  <GraduationCap className="h-4 w-4" />
                  Formação
                </h4>
                <div className="space-y-3">
                  {candidate.education.slice(0, 2).map((edu, idx) => (
                    <div key={idx}>
                      <p className="font-medium lia-text-800 dark:text-lia-text-primary">{edu.school}</p>
                      {(edu.degree || edu.field_of_study) && (
                        <p className="text-sm lia-text-600 dark:text-lia-text-tertiary">
                          {edu.degree}{edu.field_of_study && ` em ${edu.field_of_study}`}
                        </p>
                      )}
                      {(edu.start_date || edu.end_date) && (
                        <p className="text-xs lia-text-800 dark:text-lia-text-primary">
                          {edu.start_date} - {edu.end_date || "Atual"}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {candidate.languages && candidate.languages.length > 0 && (
              <div>
                <h4 className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-2 flex items-center gap-2">
                  <Languages className="h-4 w-4" />
                  Idiomas
                </h4>
                <div className="flex flex-wrap gap-2">
                  {candidate.languages.map((lang, idx) => (
                    <Badge key={idx} variant="outline" className="border-lia-border-default dark:border-lia-border-default">
                      {lang.language}
                      {lang.proficiency && ` (${lang.proficiency})`}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {candidate.insights?.strengths && candidate.insights.strengths.length > 0 && (
              <div>
                <h4 className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-2">Pontos Fortes</h4>
                <ul className="space-y-1">
                  {candidate.insights.strengths.map((strength, idx) => (
                    <li key={idx} className="text-sm lia-text-600 dark:text-lia-text-tertiary flex items-start gap-2">
                      <CheckCircle className="h-4 w-4 text-status-success mt-0.5 flex-shrink-0" />
                      {strength}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {candidate.insights?.outreach_message && (
              <div>
                <h4 className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-2 flex items-center gap-2">
                  <MessageSquare className="h-4 w-4" />
                  Sugestão de Mensagem
                </h4>
                <div className="relative">
                  <p className="text-sm lia-text-600 dark:text-lia-text-tertiary bg-gray-50 dark:bg-lia-bg-secondary p-3 rounded-md border border-lia-border-subtle dark:border-lia-border-subtle pr-10">
                    {candidate.insights.outreach_message}
                  </p>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute top-2 right-2 h-6 w-6"
                    onClick={() => copyToClipboard(candidate.insights?.outreach_message || "")}
                  >
                    <Copy className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            )}

            <Separator />

            <div>
              <h4 className="text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-3">Contato</h4>
              <div className="space-y-2">
                {candidate.email && (
                  <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-lia-bg-secondary rounded-md">
                    <div className="flex items-center gap-2">
                      <Mail className="h-4 w-4 lia-text-800 dark:text-lia-text-primary" />
                      <span className="text-sm lia-text-800 dark:text-lia-text-primary">{candidate.email}</span>
                    </div>
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        onClick={() => copyToClipboard(candidate.email || "")}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        onClick={() => onContact?.(candidate.id, "email")}
                      >
                        <Send className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                )}
                {candidate.phone && (
                  <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-lia-bg-secondary rounded-md">
                    <div className="flex items-center gap-2">
                      <Phone className="h-4 w-4 lia-text-800 dark:text-lia-text-primary" />
                      <span className="text-sm lia-text-800 dark:text-lia-text-primary">{candidate.phone}</span>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7"
                      onClick={() => copyToClipboard(candidate.phone || "")}
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
                    className="flex items-center justify-between p-2 bg-gray-50 dark:bg-lia-bg-secondary rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <Linkedin className="h-4 w-4 lia-text-600" />
                      <span className="text-sm lia-text-800 dark:text-lia-text-primary">Ver perfil no LinkedIn</span>
                    </div>
                    <ExternalLink className="h-4 w-4 lia-text-600 dark:text-lia-text-tertiary" />
                  </a>
                )}
                {!candidate.email && !candidate.phone && candidate.has_email && (
                  <p className="text-sm lia-text-800 dark:text-lia-text-primary italic">
                    Email disponível via Busca Global (custo: 2 créditos)
                  </p>
                )}
                {!candidate.phone && candidate.has_phone && (
                  <p className="text-sm lia-text-800 dark:text-lia-text-primary italic">
                    Telefone disponível via Busca Global (custo: 14 créditos)
                  </p>
                )}
              </div>
            </div>
          </div>
        </ScrollArea>

        <div className="p-4 border-t border-lia-border-subtle dark:border-lia-border-subtle bg-gray-50 dark:bg-lia-bg-secondary">
          <div className="flex flex-col gap-2">
            {candidate.is_discovered && onSaveToBase && (
              <Button 
                variant="outline"
                className="w-full border-gray-900 dark:lia-border-50 lia-text-600 dark:text-lia-text-tertiary hover:bg-gray-100 dark:bg-lia-bg-secondary"
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
                  className="flex-1 bg-gray-900 hover:bg-gray-800 dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200 text-white"
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
