"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Mail,
  Users,
  Calendar,
  CheckCircle,
  AlertCircle,
  FileText,
  Phone,
  MessageSquare,
  TrendingUp,
  Clock,
  Filter,
  RefreshCw,
  Eye,
  MoreHorizontal,
  Zap,
  UserCheck,
  Briefcase,
  BarChart3
} from "lucide-react"

interface LIAActivity {
  id: string
  type: 'email' | 'candidate' | 'interview' | 'assessment' | 'report' | 'automation' | 'notification'
  title: string
  description: string
  timestamp: Date
  status: 'success' | 'pending' | 'error' | 'info'
  metadata?: {
    candidateName?: string
    jobTitle?: string
    count?: number
    duration?: string
    platform?: string
  }
  actions?: Array<{
    label: string
    action: () => void
    variant?: 'primary' | 'secondary'
  }>
}

export function LIAActivityFeed() {
  const [activities, setActivities] = useState<LIAActivity[]>([])
  const [filter, setFilter] = useState<string>("all")
  const [isLoading, setIsLoading] = useState(false)

  // Carregar atividades do localStorage
  useEffect(() => {
    const savedActivities = localStorage.getItem('lia-activities')
    if (savedActivities) {
      try {
        const parsed = JSON.parse(savedActivities).map((activity: any) => ({
          ...activity,
          timestamp: new Date(activity.timestamp)
        }))
        setActivities(parsed)
      } catch (error) {
        console.error('Erro ao carregar atividades:', error)
        loadMockActivities()
      }
    } else {
      loadMockActivities()
    }
  }, [])

  // Mock de atividades iniciais
  const loadMockActivities = () => {
    const mockActivities: LIAActivity[] = [
      {
        id: '1',
        type: 'email',
        title: 'Email automático enviado',
        description: 'Confirmação de entrevista enviada para João Silva (Frontend Developer)',
        timestamp: new Date('2024-01-01T10:00:00'), // timestamp fixo
        status: 'success',
        metadata: {
          candidateName: 'João Silva',
          jobTitle: 'Frontend Developer',
          platform: 'Gmail'
        }
      },
      {
        id: '2',
        type: 'candidate',
        title: 'Novo candidato avaliado',
        description: 'Maria Santos recebeu score 9.2 da LIA para vaga de UX Designer',
        timestamp: new Date('2024-01-01T09:45:00'), // timestamp fixo
        status: 'success',
        metadata: {
          candidateName: 'Maria Santos',
          jobTitle: 'UX Designer'
        }
      },
      {
        id: '3',
        type: 'automation',
        title: 'Triagem automática realizada',
        description: '8 candidatos processados automaticamente para vaga de Backend Developer',
        timestamp: new Date('2024-01-01T09:30:00'), // timestamp fixo
        status: 'success',
        metadata: {
          count: 8,
          jobTitle: 'Backend Developer'
        }
      },
      {
        id: '4',
        type: 'interview',
        title: 'Entrevista agendada',
        description: 'Reunião marcada com Pedro Costa para amanhã às 14h',
        timestamp: new Date('2024-01-01T09:15:00'), // timestamp fixo
        status: 'info',
        metadata: {
          candidateName: 'Pedro Costa',
          duration: '60min'
        }
      },
      {
        id: '5',
        type: 'report',
        title: 'Relatório gerado',
        description: 'Relatório semanal de performance de recrutamento disponível',
        timestamp: new Date('2024-01-01T08:00:00'), // timestamp fixo
        status: 'success'
      }
    ]

    setActivities(mockActivities)
    saveActivities(mockActivities)
  }

  // Salvar atividades no localStorage
  const saveActivities = (activitiesToSave: LIAActivity[]) => {
    localStorage.setItem('lia-activities', JSON.stringify(activitiesToSave))
  }

  // Adicionar nova atividade (será chamado pelo sistema de notificações)
  const addActivity = (activity: Omit<LIAActivity, 'id' | 'timestamp'>) => {
    const newActivity: LIAActivity = {
      ...activity,
      id: `activity-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date()
    }

    const updatedActivities = [newActivity, ...activities.slice(0, 49)] // Manter apenas 50 atividades
    setActivities(updatedActivities)
    saveActivities(updatedActivities)
  }

  // Integração com sistema de notificações - escutar eventos
  useEffect(() => {
    const handleNotification = (event: CustomEvent) => {
      const notification = event.detail

      // Converter notificação em atividade da LIA
      let activityType: LIAActivity['type'] = 'notification'
      const metadata: LIAActivity['metadata'] = {}

      if (notification.title.toLowerCase().includes('candidato') || notification.title.toLowerCase().includes('candidatura')) {
        activityType = 'candidate'
        // Extrair nome do candidato da mensagem
        const nameMatch = notification.message.match(/(\w+\s+\w+)\s+(se candidatou|foi avaliado|foi aprovado)/i)
        if (nameMatch) {
          metadata.candidateName = nameMatch[1]
        }
      } else if (notification.title.toLowerCase().includes('entrevista')) {
        activityType = 'interview'
        const nameMatch = notification.message.match(/com\s+(\w+\s+\w+)/i)
        if (nameMatch) {
          metadata.candidateName = nameMatch[1]
        }
      } else if (notification.title.toLowerCase().includes('email') || notification.title.toLowerCase().includes('enviado')) {
        activityType = 'email'
      } else if (notification.title.toLowerCase().includes('processou') || notification.title.toLowerCase().includes('análise')) {
        activityType = 'automation'
        const countMatch = notification.message.match(/(\d+)\s+(candidatos|currículos)/i)
        if (countMatch) {
          metadata.count = parseInt(countMatch[1])
        }
      }

      addActivity({
        type: activityType,
        title: notification.title,
        description: notification.message,
        status: notification.type === 'error' ? 'error' :
                notification.type === 'warning' ? 'pending' :
                notification.type === 'success' ? 'success' : 'info',
        metadata
      })
    }

    // Escutar eventos customizados de notificação
    window.addEventListener('lia-notification' as any, handleNotification)

    return () => {
      window.removeEventListener('lia-notification' as any, handleNotification)
    }
  }, [])

  // Filtrar atividades
  const filteredActivities = activities.filter(activity => {
    if (filter === "all") return true
    return activity.type === filter
  })

  // Agrupar atividades por período
  const groupedActivities = () => {
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000)

    const groups = {
      today: [] as LIAActivity[],
      yesterday: [] as LIAActivity[],
      older: [] as LIAActivity[]
    }

    filteredActivities.forEach(activity => {
      if (activity.timestamp >= today) {
        groups.today.push(activity)
      } else if (activity.timestamp >= yesterday) {
        groups.yesterday.push(activity)
      } else {
        groups.older.push(activity)
      }
    })

    return groups
  }

  // Ícones por tipo de atividade
  const getActivityIcon = (type: LIAActivity['type']) => {
    switch (type) {
      case 'email': return <Mail className="w-4 h-4 text-gray-600 dark:text-gray-400" />
      case 'candidate': return <Users className="w-4 h-4 text-green-500" />
      case 'interview': return <Calendar className="w-4 h-4 text-purple-500" />
      case 'assessment': return <BarChart3 className="w-4 h-4 text-orange-500" />
      case 'report': return <FileText className="w-4 h-4 text-teal-500" />
      case 'automation': return <Zap className="w-4 h-4 text-yellow-500" />
      default: return <CheckCircle className="w-4 h-4 text-gray-600" />
    }
  }

  // Status color
  const getStatusColor = (status: LIAActivity['status']) => {
    switch (status) {
      case 'success': return 'text-green-600'
      case 'error': return 'text-red-600'
      case 'pending': return 'text-yellow-600'
      default: return 'text-gray-600 dark:text-gray-400'
    }
  }

  // Formatar tempo relativo
  const formatTime = (timestamp: Date) => {
    const now = new Date()
    const diff = now.getTime() - timestamp.getTime()
    const minutes = Math.floor(diff / 60000)

    if (minutes < 1) return 'Agora'
    if (minutes < 60) return `${minutes}m atrás`
    if (minutes < 1440) return `${Math.floor(minutes / 60)}h atrás`
    return timestamp.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
  }

  const refreshActivities = () => {
    setIsLoading(true)
    // Simular carregamento
    setTimeout(() => {
      setIsLoading(false)
    }, 1000)
  }

  const groups = groupedActivities()

  return (
    <Card className="bg-white dark:bg-gray-800">
      <CardHeader className="flex flex-row items-center justify-between pb-4">
        <CardTitle className="text-lg font-semibold font-sans text-gray-950 dark:text-gray-50 flex items-center gap-3">
          <div className="w-8 h-8 bg-gray-100 dark:bg-gray-700 rounded-md flex items-center justify-center">
            <span className="text-sm">📝</span>
          </div>
          Feed de Atividades da LIA
        </CardTitle>

        <div className="flex items-center gap-2">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-950 dark:text-gray-50"
          >
            <option value="all">Todas</option>
            <option value="email">Emails</option>
            <option value="candidate">Candidatos</option>
            <option value="interview">Entrevistas</option>
            <option value="automation">Automações</option>
            <option value="report">Relatórios</option>
          </select>

          <Button
            variant="ghost"
            size="sm"
            onClick={refreshActivities}
            disabled={isLoading}
            className="h-8 w-8 p-0"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </CardHeader>

      <CardContent className="max-h-96 overflow-y-auto">
        {Object.entries(groups).map(([period, periodActivities]) => (
          periodActivities.length > 0 && (
            <div key={period} className="mb-6">
              <h4 className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 sticky top-0 bg-white dark:bg-gray-800 py-1">
                {period === 'today' ? 'Hoje' : period === 'yesterday' ? 'Ontem' : 'Mais antigas'}
              </h4>

              <div className="space-y-4">
                {periodActivities.map((activity, index) => (
                  <div key={activity.id} className="flex items-start gap-4">
                    <div className="flex flex-col items-center">
                      <div className="mt-1">
                        {getActivityIcon(activity.type)}
                      </div>
                      {index < periodActivities.length - 1 && (
                        <div className="w-0.5 h-8 bg-gray-200 dark:bg-gray-700 mt-2"></div>
                      )}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className={`font-medium text-sm ${getStatusColor(activity.status)} mb-1`}>
                            {activity.title}
                          </h4>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2 leading-relaxed">
                            {activity.description}
                          </p>

                          {/* Metadata */}
                          {activity.metadata && (
                            <div className="flex flex-wrap gap-2 mb-2">
                              {activity.metadata.candidateName && (
                                <Badge variant="outline" className="text-xs">
                                  <UserCheck className="w-3 h-3 mr-1" />
                                  {activity.metadata.candidateName}
                                </Badge>
                              )}
                              {activity.metadata.jobTitle && (
                                <Badge variant="outline" className="text-xs">
                                  <Briefcase className="w-3 h-3 mr-1" />
                                  {activity.metadata.jobTitle}
                                </Badge>
                              )}
                              {activity.metadata.count && (
                                <Badge variant="outline" className="text-xs">
                                  {activity.metadata.count} itens
                                </Badge>
                              )}
                              {activity.metadata.platform && (
                                <Badge variant="outline" className="text-xs">
                                  {activity.metadata.platform}
                                </Badge>
                              )}
                            </div>
                          )}
                        </div>

                        <div className="flex items-center gap-2 ml-4">
                          <span className="text-xs text-gray-600 dark:text-gray-400">
                            {formatTime(activity.timestamp)}
                          </span>
                          <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                            <MoreHorizontal className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>

                      {/* Actions */}
                      {activity.actions && activity.actions.length > 0 && (
                        <div className="flex gap-2 mt-2">
                          {activity.actions.map((action, actionIndex) => (
                            <Button
                              key={actionIndex}
                              variant={action.variant === 'primary' ? 'default' : 'outline'}
                              size="sm"
                              onClick={action.action}
                              className="h-7 text-xs"
                            >
                              {action.label}
                            </Button>
                          ))}
                        </div>
                      )}

                      {/* Status indicator */}
                      <div className={`inline-block px-2 py-1 rounded text-xs mt-2 ${
                        activity.status === 'success' ? 'bg-green-100 text-green-700' :
                        activity.status === 'error' ? 'bg-red-100 text-red-700' :
                        activity.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-gray-100 dark:bg-gray-800 text-wedo-cyan-dark'
                      }`}>
                        {activity.status === 'success' ? 'Concluído com sucesso' :
                         activity.status === 'error' ? 'Erro na execução' :
                         activity.status === 'pending' ? 'Em andamento' :
                         'Informação'}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )
        ))}

        {filteredActivities.length === 0 && (
          <div className="text-center py-8 text-gray-600 dark:text-gray-400">
            <CheckCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">
              {filter === 'all' ? 'Nenhuma atividade registrada ainda' : `Nenhuma atividade do tipo "${filter}" encontrada`}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// Hook para adicionar atividades externamente
export const useLIAActivityFeed = () => {
  const addActivity = (activity: Omit<LIAActivity, 'id' | 'timestamp'>) => {
    // Disparar evento customizado que será capturado pelo componente
    const event = new CustomEvent('lia-activity', { detail: activity })
    window.dispatchEvent(event)
  }

  return { addActivity }
}
