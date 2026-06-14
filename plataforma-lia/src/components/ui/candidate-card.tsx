import React, { useState, useEffect } from"react"
import { Card, CardContent } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { MapPin, Building, Mail, Linkedin, ExternalLink, Award, Calendar, ChevronDown, ChevronUp, MessageSquare, Check, AlertCircle, Clock, Send } from"lucide-react"
import { textStyles, buttonStyles, cardStyles, badgeStyles } from"@/lib/design-tokens"
import { CandidateTouchIndicator } from "@/components/candidates/CandidateTouchIndicator"

interface CommunicationHistoryItem {
  id: string
  channel: string
  subject: string | null
  message_preview: string | null
  status: string
  created_at: string
  sent_at: string | null
}

interface CandidateCardProps {
  name: string
  title: string | null
  company: string | null
  location: string
  skills: string[]
  source_badge?: string
  match_score?: number | null
  email?: string | null
  linkedin?: string | null
  candidateId?: string | null
  companyId?: string
  onViewProfile?: () => void
  onContact?: () => void
  onScheduleInterview?: () => void
  onViewMoreCommunications?: () => void
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'delivered':
    case 'read':
      return <Check className="w-3 h-3 text-status-success" />
    case 'sent':
      return <Send className="w-3 h-3 text-lia-text-secondary" />
    case 'failed':
      return <AlertCircle className="w-3 h-3 text-status-error" />
    case 'pending':
    default:
      return <Clock className="w-3 h-3 text-status-warning" />
  }
}

const getStatusLabel = (status: string) => {
  switch (status) {
    case 'delivered':
      return 'Entregue'
    case 'read':
      return 'Lida'
    case 'sent':
      return 'Enviada'
    case 'failed':
      return 'Falhou'
    case 'pending':
    default:
      return 'Pendente'
  }
}

const getChannelIcon = (channel: string) => {
  switch (channel) {
    case 'whatsapp':
      return <MessageSquare className="w-3.5 h-3.5 text-status-success" />
    case 'email':
    default:
      return <Mail className="w-3.5 h-3.5 text-lia-text-secondary" />
  }
}

const formatDate = (dateString: string | null) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('pt-BR', { 
    day: '2-digit', 
    month: '2-digit',
    year: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

export function CandidateCard({
  name,
  title,
  company,
  location,
  skills,
  source_badge ="🏢 Banco Proprietário",
  match_score,
  email,
  linkedin,
  candidateId,
  companyId = '',
  onViewProfile,
  onContact,
  onScheduleInterview,
  onViewMoreCommunications
}: CandidateCardProps) {
  const [isHistoryExpanded, setIsHistoryExpanded] = useState(false)
  const [communications, setCommunications] = useState<CommunicationHistoryItem[]>([])
  const [totalCommunications, setTotalCommunications] = useState(0)
  const [isLoading, setIsLoading] = useState(false)
  const [hasLoaded, setHasLoaded] = useState(false)

  const fetchCommunicationHistory = async () => {
    if (!candidateId || hasLoaded) return
    
    setIsLoading(true)
    try {
      const response = await fetch(
        `/api/backend-proxy/communication/history?candidate_id=${candidateId}&company_id=${companyId}&limit=5`,
        {
          headers: {
            'Content-Type': 'application/json',
            'X-Company-ID': companyId,
          },
        }
      )
      
      if (response.ok) {
        const data = await response.json()
        setCommunications(data.communications || [])
        setTotalCommunications(data.total || 0)
        setHasLoaded(true)
      }
    } catch (error) {
    } finally {
      setIsLoading(false)
    }
  }

  const handleToggleHistory = () => {
    if (!isHistoryExpanded && !hasLoaded) {
      fetchCommunicationHistory()
    }
    setIsHistoryExpanded(!isHistoryExpanded)
  }

  return (
    <Card className="border border-lia-border-subtle hover:transition-shadow rounded-xl bg-lia-bg-primary dark:bg-lia-bg-primary">
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <h4 className="font-semibold text-base truncate text-lia-text-primary">
                {name}
              </h4>
              {/* Onda 2 F8 — icone "tocado por agente nas ultimas 24h". */}
              <CandidateTouchIndicator candidateId={candidateId} />
              <Chip variant="neutral" muted className={`text-xs shrink-0 border-0 text-lia-text-secondary ${source_badge.includes("Banco Proprietário") ? 'bg-stone-50' : 'bg-wedo-cyan/10'}`}>
                {source_badge}
              </Chip>
            </div>
            
            {title && (
              <div className="flex items-center gap-1.5 text-sm mb-1 text-lia-text-tertiary">
                <Building className="w-3.5 h-3.5 shrink-0" />
                <span className="truncate">{title} {company && `• ${company}`}</span>
              </div>
            )}
            
            {location && (
              <div className="flex items-center gap-1.5 text-sm mb-3 text-lia-text-disabled">
                <MapPin className="w-3.5 h-3.5 shrink-0" />
                <span className="truncate">{location}</span>
              </div>
            )}
            
            {skills && skills.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mb-3">
                {skills.slice(0, 6).map((skill) => (
                  <Chip
                    key={`${name}-${skill}`}
                    variant="neutral"
                    className="text-xs px-2 py-0.5 border-lia-border-subtle text-lia-text-secondary"
                  >
                    {skill}
                  </Chip>
                ))}
                {skills.length > 6 && (
                  <Chip density="relaxed" variant="neutral" className="px-2 py-0.5 border-lia-border-subtle text-lia-text-secondary">
                    +{skills.length - 6}
                  </Chip>
                )}
              </div>
            )}
            
            {match_score !== null && match_score !== undefined && (
              <div className="flex items-center gap-1.5 mb-3">
                <Award className="w-3.5 h-3.5 text-lia-text-secondary" />
                <span className="text-sm font-medium text-lia-text-secondary">
                  {match_score}% match
                </span>
              </div>
            )}
            
            <div className="flex items-center gap-2 flex-wrap">
              {email && (
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="h-7 text-xs px-2"
                  onClick={onContact}
                >
                  <Mail className="w-3 h-3 mr-1" />
                  Contatar
                </Button>
              )}
              {onScheduleInterview && (
                <Button 
                  variant="ghost" 
                  size="sm" 
 className="h-7 text-xs px-2 text-lia-text-secondary hover:text-lia-text-secondary"
                  onClick={onScheduleInterview}
                >
                  <Calendar className="w-3 h-3 mr-1" />
                  Agendar
                </Button>
              )}
              {linkedin && (
                <Button variant="ghost" size="sm" className="h-7 text-xs px-2" asChild>
                  <a href={linkedin} target="_blank" rel="noopener noreferrer">
                    <Linkedin className="w-3 h-3 mr-1" />
                    LinkedIn
                  </a>
                </Button>
              )}
              <Button 
                variant="ghost" 
                size="sm" 
                className="h-7 text-xs px-2"
                onClick={onViewProfile}
              >
                <ExternalLink className="w-3 h-3 mr-1" />
                Ver Perfil
              </Button>
            </div>

            {candidateId && (
              <div className="mt-3 pt-3 border-t border-lia-border-subtle">
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full h-8 text-xs justify-between px-2 text-lia-text-tertiary"
                  onClick={handleToggleHistory}
                >
                  <span className="flex items-center gap-1.5">
                    <MessageSquare className="w-3.5 h-3.5" />
                    Histórico de Comunicações
                    {totalCommunications > 0 && (
                      <Chip variant="neutral" muted className="text-micro px-1.5 py-0 ml-1">
                        {totalCommunications}
                      </Chip>
                    )}
                  </span>
                  {isHistoryExpanded ? (
                    <ChevronUp className="w-4 h-4" />
                  ) : (
                    <ChevronDown className="w-4 h-4" />
                  )}
                </Button>

                {isHistoryExpanded && (
                  <div className="mt-2 space-y-2">
                    {isLoading ? (
                      <div className="flex items-center justify-center py-4">
                        <div className="animate-spin motion-reduce:animate-none rounded-full h-5 w-5 border-b-2 border-lia-border-medium"></div>
                      </div>
                    ) : communications.length === 0 ? (
                      <div className="text-center py-3 text-xs text-lia-text-disabled">
                        Nenhuma comunicação registrada
                      </div>
                    ) : (
                      <>
                        {communications.map((comm) => (
                          <div
                            key={comm.id}
                            className="flex items-start gap-2 p-2 rounded-xl bg-lia-bg-secondary"
                          >
                            <div className="shrink-0 mt-0.5">
                              {getChannelIcon(comm.channel)}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-1.5 mb-0.5">
                                <span className="text-xs font-medium truncate text-lia-text-primary">
                                  {comm.subject || comm.message_preview?.slice(0, 50) || 'Mensagem'}
                                </span>
                              </div>
                              <div className="flex items-center gap-2 text-micro text-lia-text-disabled">
                                <span>{formatDate(comm.sent_at || comm.created_at)}</span>
                                <span className="flex items-center gap-0.5">
                                  {getStatusIcon(comm.status)}
                                  {getStatusLabel(comm.status)}
                                </span>
                              </div>
                            </div>
                          </div>
                        ))}
                        
                        {totalCommunications > 5 && (
                          <Button
                            variant="link"
                            size="sm"
                            className="w-full h-6 text-xs text-wedo-cyan-text"
                            onClick={onViewMoreCommunications}
                          >
                            Ver mais ({totalCommunications - 5} comunicações)
                          </Button>
                        )}
                      </>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
