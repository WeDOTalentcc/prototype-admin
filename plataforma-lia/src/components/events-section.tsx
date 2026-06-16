"use client"


import { CURRENCY_SYMBOL } from"@/lib/pricing"
import { useState } from"react"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import {
  Clock,
  Calendar,
  MessageSquare,
  User,
  CheckCircle,
  FileText,
  Video,
  Send,
  Edit,
  Bell,
  ChevronRight,
  Expand,
  Shrink,
  Mail,
  Phone,
  BrainCircuit,
} from"lucide-react"

// Dados das atividades organizados por período
const morningEvents = [
  {
    id: 1,
    title:"Entrevista Técnica - João Silva",
    subtitle:"Frontend Developer • React + TypeScript",
    time:"09:00",
    type:"interview",
    priority:"high",
    details:"Entrevista técnica • 60min • Google Meet",
    hasReminder: true,
    isSuggested: false,
    candidateInfo: {
      name:"João Silva",
      experience:"5 anos em React, 3 anos em TypeScript"
    },
    actions: [
      { icon: Video, label:"Iniciar" },
      { icon: FileText, label:"Ver CV" }
    ]
  },
  {
    id: 2,
    title:"Enviar Lembrete",
    subtitle:"Entrevista João Silva - 09:00",
    time:"08:45",
    type:"reminder",
    priority:"medium",
    details:"Sugerido pela IA • Lembrete automático",
    hasReminder: false,
    isSuggested: true,
    actions: [
      { icon: Send, label:"Enviar" },
      { icon: Edit, label:"Editar" }
    ]
  },
  {
    id: 3,
    title:"Revisar CVs - Backend Dev",
    subtitle:"15 candidatos pendentes",
    time:"10:30",
    type:"review",
    priority:"medium",
    details:"Análise de perfis • Triagem inicial",
    hasReminder: false,
    isSuggested: false,
    actions: [
      { icon: FileText, label:"Revisar" },
      { icon: CheckCircle, label:"Aprovar" }
    ]
  },
  {
    id: 4,
    title:"Revisar Perfis",
    subtitle:"15 candidatos pendentes • Sugestão IA",
    time:"11:00",
    type:"review",
    priority:"medium",
    details:"Sugerido pela IA • Triagem rápida",
    hasReminder: false,
    isSuggested: true,
    actions: [
      { icon: FileText, label:"Revisar" },
      { icon: CheckCircle, label:"Aprovar" }
    ]
  }
]

const afternoonEvents = [
  {
    id: 5,
    title:"Autorizar Feedback - Ana Costa",
    subtitle:"UX Designer • Processo finalizado",
    time:"14:00",
    type:"feedback",
    priority:"high",
    details:"Feedback da equipe • Aprovação necessária",
    hasReminder: true,
    isSuggested: false,
    candidateInfo: {
      name:"Ana Costa",
      experience:"7 anos em UX Design, especialista em mobile"
    },
    actions: [
      { icon: CheckCircle, label:"Aprovar" },
      { icon: Send, label:"Enviar" }
    ]
  },
  {
    id: 6,
    title:"Publicar Vaga - UX Designer",
    subtitle:"Área de Produto • Revisão final",
    time:"15:30",
    type:"publication",
    priority:"medium",
    details:"Vaga aprovada • Publicação em 3 canais",
    hasReminder: true,
    isSuggested: false,
    actions: [
      { icon: Send, label:"Publicar" },
      { icon: Edit, label:"Editar" }
    ]
  },
  {
    id: 7,
    title:"Aprovar Oferta",
    subtitle:"Lucas Mendes - Backend • Sugestão IA",
    time:"16:00",
    type:"offer",
    priority:"high",
    details: `Sugerido pela IA • Oferta ${CURRENCY_SYMBOL} 12.000`,
    hasReminder: false,
    isSuggested: true,
    actions: [
      { icon: CheckCircle, label:"Aprovar" },
      { icon: Edit, label:"Ajustar" }
    ]
  },
  {
    id: 8,
    title:"Enviar Oferta - Lucas Mendes",
    subtitle:"Backend Developer • Aprovado",
    time:"16:30",
    type:"offer",
    priority:"high",
    details: `Oferta salarial • ${CURRENCY_SYMBOL} 12.000 • CLT`,
    hasReminder: true,
    isSuggested: false,
    candidateInfo: {
      name:"Lucas Mendes",
      experience:"8 anos em Node.js e Python"
    },
    actions: [
      { icon: Send, label:"Enviar" },
      { icon: Edit, label:"Ajustar" }
    ]
  }
]

export function EventsSection() {
  const [isExpanded, setIsExpanded] = useState(false)
  const [selectedEvent, setSelectedEvent] = useState<number | null>(null)

  const totalTasks = morningEvents.length + afternoonEvents.length
  const urgentTasks = [...morningEvents, ...afternoonEvents].filter(e => e.priority === 'high').length
  const suggestedTasks = [...morningEvents, ...afternoonEvents].filter(e => e.isSuggested).length

  // Funções utilitárias
  const getTypeIcon = (type: string) => {
    const icons = {
      interview: <Video className="w-4 h-4 text-lia-text-secondary" />,
      feedback: <MessageSquare className="w-4 h-4 text-lia-text-secondary" />,
      publication: <FileText className="w-4 h-4 text-lia-text-secondary" />,
      offer: <Send className="w-4 h-4 text-lia-text-secondary" />,
      review: <FileText className="w-4 h-4 text-lia-text-secondary" />,
      reminder: <Bell className="w-4 h-4 text-lia-text-secondary" />
    }
    return icons[type as keyof typeof icons] || <Calendar className="w-4 h-4 text-lia-text-secondary" />
  }

  const getPriorityBadge = (priority: string) => {
    const badges = {
      high: <Chip density="relaxed" variant="danger" >Urgente</Chip>,
      medium: <Chip density="relaxed" variant="warning" >Média</Chip>,
      low: <Chip density="relaxed" variant="neutral" className="border-lia-border-subtle text-lia-text-primary dark:border-lia-border-subtle">Baixa</Chip>
    }
    return badges[priority as keyof typeof badges]
  }

  const renderEventCard = (event: typeof morningEvents[number], index: number) => (
    <div
      key={event.id}
      className={`flex items-start gap-3 p-4 rounded-md transition-colors motion-reduce:transition-none duration-200 cursor-pointer border ${
 event.isSuggested
 ? 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary border-lia-border-default'
          : 'bg-lia-bg-secondary dark:bg-lia-bg-elevated border-lia-border-subtle dark:border-lia-border-default'
      }`}
      onClick={() => setSelectedEvent(selectedEvent === event.id ? null : event.id)}
    >
      <div className={`w-10 h-10 rounded-md flex items-center justify-center border ${
 event.isSuggested
 ? 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary border-lia-border-default'
          : 'bg-lia-bg-primary border-lia-border-subtle dark:border-lia-border-medium'
      }`}>
        {event.isSuggested ? (
          <BrainCircuit className="w-4 h-4 text-lia-text-secondary" />
        ) : (
          getTypeIcon(event.type)
        )}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between mb-1">
          <div className="flex items-center gap-2">
            <h4 className="font-medium text-lia-text-primary text-sm leading-tight">
              {event.title}
            </h4>
            {event.isSuggested && (
 <Chip density="relaxed" variant="neutral" className="border-lia-border-default text-lia-text-secondary">
                IA
              </Chip>
            )}
            {getPriorityBadge(event.priority)}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-lia-text-tertiary flex-shrink-0 font-mono">
              {event.time}
            </span>
            {isExpanded && (
              <ChevronRight className={`w-3 h-3 text-lia-text-secondary transition-transform motion-reduce:transition-none ${selectedEvent === event.id ? 'rotate-90' : ''}`} />
            )}
          </div>
        </div>

        <p className="text-xs text-lia-text-secondary mb-2 leading-relaxed">
          {event.subtitle}
        </p>

        <div className="flex items-center justify-between mb-2">
          <div className="text-xs text-lia-text-tertiary">
            {event.details.split('•')[1]?.trim()}
          </div>

          {event.hasReminder && (
 <div className="flex items-center gap-1 text-lia-text-secondary text-xs">
              <Bell className="w-3 h-3" />
              <span>Lembrete</span>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          {event.actions.map((action: { icon: React.ComponentType<{ className?: string }>; label: string }, actionIndex: number) => (
            <Button
              key={actionIndex}
              size="sm"
              variant="outline"
              className="h-7 px-2 text-xs border-lia-border-default dark:border-lia-border-medium hover:border-lia-border-medium dark:hover:border-lia-border-medium text-lia-text-primary hover:bg-lia-bg-tertiary dark:hover:bg-lia-border-medium transition-colors motion-reduce:transition-none duration-200"
            >
              <action.icon className="w-3 h-3 mr-1" />
              {action.label}
            </Button>
          ))}
        </div>
      </div>
    </div>
  )

  return (
    <div className="w-full transition-colors motion-reduce:transition-none duration-300">
      <Card className="border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-xl font-semibold text-lia-text-primary">
                Próximas Atividades e Tarefas
              </CardTitle>
              <p className="text-sm text-lia-text-tertiary mt-1">
                {totalTasks} tarefas • {urgentTasks} urgentes • {suggestedTasks} sugeridas pela IA
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Chip density="relaxed" variant="neutral" className="border-lia-border-subtle dark:border-lia-border-default px-2 py-1">
                <Clock className="w-3 h-3 mr-1" />
                Hoje
              </Chip>

              <Button
                variant="ghost"
                size="sm"
                className="h-7 w-7 p-0 text-lia-text-tertiary hover:text-lia-text-secondary dark:hover:text-lia-text-inverse"
                onClick={() => setIsExpanded(!isExpanded)}
              >
                {isExpanded ? (
                  <Shrink className="w-3 h-3" />
                ) : (
                  <Expand className="w-3 h-3" />
                )}
              </Button>

              <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-lia-text-tertiary hover:text-lia-text-secondary dark:hover:text-lia-text-inverse">
                <Calendar className="w-3 h-3" />
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-6 pt-0">
          {/* Sessão Manhã */}
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-8 bg-lia-bg-tertiary dark:bg-lia-bg-elevated rounded-xl flex items-center justify-center">
                <span className="text-sm">🌅</span>
              </div>
              <div>
                <h3 className="font-medium text-lia-text-primary text-sm">Sessão Manhã</h3>
                <p className="text-xs text-lia-text-tertiary">
                  Organizado pela IA • {morningEvents.length} atividades • {morningEvents.filter(e => e.isSuggested).length} sugeridas
                </p>
              </div>
            </div>
            <div className="space-y-3">
              {morningEvents.map((event, index) => renderEventCard(event, index))}
            </div>
          </div>

          {/* Sessão Tarde */}
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-8 bg-lia-bg-tertiary dark:bg-lia-bg-elevated rounded-xl flex items-center justify-center">
                <span className="text-sm">☀️</span>
              </div>
              <div>
                <h3 className="font-medium text-lia-text-primary text-sm">Sessão Tarde</h3>
                <p className="text-xs text-lia-text-tertiary">
                  Organizado pela IA • {afternoonEvents.length} atividades • {afternoonEvents.filter(e => e.isSuggested).length} sugeridas
                </p>
              </div>
            </div>
            <div className="space-y-3">
              {afternoonEvents.map((event, index) => renderEventCard(event, index + morningEvents.length))}
            </div>
          </div>

          {/* Detalhes do evento selecionado */}
          {selectedEvent && isExpanded && (
            <div
              className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-4 overflow-hidden"
             
            >
                {(() => {
                  const event = [...morningEvents, ...afternoonEvents].find(e => e.id === selectedEvent)
                  if (!event) return null

                  return (
                    <div className="bg-lia-bg-secondary dark:bg-lia-bg-elevated rounded-xl p-4 border border-lia-border-subtle dark:border-lia-border-default">
                      <div className="flex items-start gap-3 mb-3">
                        <div className={`w-10 h-10 rounded-md flex items-center justify-center border ${
 event.isSuggested
 ? 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary border-lia-border-default'
                            : 'bg-lia-bg-primary border-lia-border-subtle dark:border-lia-border-medium'
                        }`}>
                          {event.isSuggested ? (
 <BrainCircuit className="w-4 h-4 text-lia-text-secondary" />
                          ) : (
                            getTypeIcon(event.type)
                          )}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-semibold text-lia-text-primary">
                              {event.title}
                            </h3>
                            {event.isSuggested && (
 <Chip density="relaxed" variant="neutral" className="border-lia-border-default text-lia-text-secondary">
                                Sugerido pela IA
                              </Chip>
                            )}
                            {getPriorityBadge(event.priority)}
                          </div>
                          <p className="text-sm text-lia-text-secondary">
                            {event.subtitle}
                          </p>
                          <p className="text-xs text-lia-text-tertiary mt-1">
                            {event.details}
                          </p>
                        </div>
                      </div>

                      {event.candidateInfo && (
                        <div className="bg-lia-bg-primary rounded-xl p-3 mb-3 border border-lia-border-subtle dark:border-lia-border-medium">
                          <h4 className="font-medium text-lia-text-primary mb-2 flex items-center gap-2">
                            <User className="w-4 h-4" />
                            Candidato
                          </h4>
                          <div className="text-sm space-y-1">
                            <div>
                              <span className="text-lia-text-tertiary">Nome:</span>
                              <p className="font-medium text-lia-text-primary">
                                {event.candidateInfo.name}
                              </p>
                            </div>
                            <div>
                              <span className="text-lia-text-tertiary">Experiência:</span>
                              <p className="font-medium text-lia-text-primary">
                                {event.candidateInfo.experience}
                              </p>
                            </div>
                          </div>
                        </div>
                      )}

                      <div className="flex flex-wrap gap-2">
                        {event.actions.map((action: { icon: React.ComponentType<{ className?: string }>; label: string }, actionIndex: number) => (
                          <Button
                            key={actionIndex}
                            size="sm"
                            className="gap-2 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text border-0 dark:hover:bg-lia-interactive-active"
                          >
                            <action.icon className="w-4 h-4" />
                            {action.label}
                          </Button>
                        ))}
                      </div>
                    </div>
                  )
                })()}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
