import React, { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { MapPin, Building, Mail, Linkedin, ExternalLink, Award, Calendar, ChevronDown, ChevronUp, MessageSquare, Check, AlertCircle, Clock, Send } from "lucide-react"
import { textStyles, buttonStyles, cardStyles, badgeStyles } from "@/lib/design-tokens"

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
      return <Check className="w-3 h-3 text-green-500" />
    case 'sent':
      return <Send className="w-3 h-3 text-gray-600 dark:text-gray-400" />
    case 'failed':
      return <AlertCircle className="w-3 h-3 text-red-500" />
    case 'pending':
    default:
      return <Clock className="w-3 h-3 text-yellow-500" />
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
      return <MessageSquare className="w-3.5 h-3.5 text-green-600" />
    case 'email':
    default:
      return <Mail className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
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
  source_badge = "🏢 Banco Proprietário",
  match_score,
  email,
  linkedin,
  candidateId,
  companyId = 'default',
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
      console.error('Error fetching communication history:', error)
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
    <Card className="border border-gray-200 dark:border-gray-700 hover:transition-shadow rounded-md bg-white dark:bg-gray-900">
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <h4 className="font-semibold text-base truncate" style={{ color: 'var(--eleven-text-primary)' }}>
                {name}
              </h4>
              <Badge variant="secondary" className="text-xs shrink-0 border-0" style={{
                backgroundColor: source_badge.includes("Banco Proprietário") ? 'var(--eleven-sepia-light)' : 'var(--eleven-bg-accent)',
                color: 'var(--eleven-text-secondary)'
              }}>
                {source_badge}
              </Badge>
            </div>
            
            {title && (
              <div className="flex items-center gap-1.5 text-sm mb-1" style={{ color: 'var(--eleven-text-secondary)' }}>
                <Building className="w-3.5 h-3.5 shrink-0" />
                <span className="truncate">{title} {company && `• ${company}`}</span>
              </div>
            )}
            
            {location && (
              <div className="flex items-center gap-1.5 text-sm mb-3" style={{ color: 'var(--eleven-text-tertiary)' }}>
                <MapPin className="w-3.5 h-3.5 shrink-0" />
                <span className="truncate">{location}</span>
              </div>
            )}
            
            {skills && skills.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mb-3">
                {skills.slice(0, 6).map((skill) => (
                  <Badge
                    key={`${name}-${skill}`}
                    variant="outline"
                    className="text-xs px-2 py-0.5"
                    style={{
                      borderColor: 'var(--eleven-border-subtle)',
                      color: 'var(--eleven-text-secondary)'
                    }}
                  >
                    {skill}
                  </Badge>
                ))}
                {skills.length > 6 && (
                  <Badge variant="outline" className="text-xs px-2 py-0.5" style={{
                    borderColor: 'var(--eleven-border-subtle)',
                    color: 'var(--eleven-text-tertiary)'
                  }}>
                    +{skills.length - 6}
                  </Badge>
                )}
              </div>
            )}
            
            {match_score !== null && match_score !== undefined && (
              <div className="flex items-center gap-1.5 mb-3">
                <Award className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
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
 className="h-7 text-xs px-2 text-gray-600 hover:text-gray-600"
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
              <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full h-8 text-xs justify-between px-2"
                  onClick={handleToggleHistory}
                  style={{ color: 'var(--eleven-text-secondary)' }}
                >
                  <span className="flex items-center gap-1.5">
                    <MessageSquare className="w-3.5 h-3.5" />
                    Histórico de Comunicações
                    {totalCommunications > 0 && (
                      <Badge variant="secondary" className="text-micro px-1.5 py-0 ml-1">
                        {totalCommunications}
                      </Badge>
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
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-400"></div>
                      </div>
                    ) : communications.length === 0 ? (
                      <div className="text-center py-3 text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                        Nenhuma comunicação registrada
                      </div>
                    ) : (
                      <>
                        {communications.map((comm) => (
                          <div
                            key={comm.id}
                            className="flex items-start gap-2 p-2 rounded-md bg-gray-50 dark:bg-gray-800/50"
                          >
                            <div className="shrink-0 mt-0.5">
                              {getChannelIcon(comm.channel)}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-1.5 mb-0.5">
                                <span className="text-xs font-medium truncate" style={{ color: 'var(--eleven-text-primary)' }}>
                                  {comm.subject || comm.message_preview?.slice(0, 50) || 'Mensagem'}
                                </span>
                              </div>
                              <div className="flex items-center gap-2 text-micro" style={{ color: 'var(--eleven-text-tertiary)' }}>
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
                            className="w-full h-6 text-xs"
                            onClick={onViewMoreCommunications}
                            style={{ color: 'var(--eleven-accent)' }}
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
