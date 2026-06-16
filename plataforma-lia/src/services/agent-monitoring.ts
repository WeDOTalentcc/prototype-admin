/**
 * Agent Monitoring Service
 * 
 * Service layer for agent metrics, activity feed, and health monitoring
 * Connects to backend /agent-monitoring endpoints
 */

const BACKEND_URL = '/api/backend-proxy'

export interface GlobalMetrics {
  actions_today: number
  actions_delta: number
  active_agents: number
  total_agents: number
  success_rate: number
  avg_response_time: number
  proactive_alerts: number
}

export interface AgentSummary {
  id: string
  name: string
  icon: string
  status: 'online' | 'idle' | 'warning'
  actions_today: number
  daily_goal: number
  progress: number
  delta: number
  sparkline: number[]
  last_action: string | null
  last_action_time: string | null
}

export interface ActivityEvent {
  id: string
  agent_id: string
  agent_name: string
  agent_icon: string
  type: string
  title: string
  description: string | null
  status: 'success' | 'pending' | 'error' | 'in_progress'
  started_at: string
  completed_at?: string
  duration_seconds?: number
  sla_breach?: boolean
  related_job_id?: string
  related_candidate_id?: string
  metadata?: Record<string, unknown>
}

export interface HealthDriver {
  name: string
  value: number
  weight: number
  impact: 'positive' | 'negative' | 'neutral'
}

export interface AgentHealth {
  agent_id: string
  score: number
  tier: 'excellent' | 'good' | 'watch' | 'critical'
  drivers: HealthDriver[]
  recommendations: string[]
}

export interface ProactiveAlert {
  id: string
  type: string
  agent_id: string
  agent_name: string
  title: string
  description: string
  created_at: string | null
  severity: 'low' | 'medium' | 'high'
}

export interface ActivityFeedFilters {
  agentId?: string
  status?: string
  limit?: number
  offset?: number
}

class AgentMonitoringService {
  private baseUrl: string

  constructor(baseUrl: string = BACKEND_URL) {
    this.baseUrl = baseUrl
  }

  async getGlobalMetrics(): Promise<GlobalMetrics> {
    try {
      const response = await fetch(`${this.baseUrl}/agent-monitoring/metrics`)
      if (!response.ok) {
        throw new Error(`Failed to fetch global metrics: ${response.statusText}`)
      }
      return response.json()
    } catch (error) {
      return this.getMockGlobalMetrics()
    }
  }

  async getAllAgentsSummary(): Promise<AgentSummary[]> {
    try {
      const response = await fetch(`${this.baseUrl}/agent-monitoring/agents`)
      if (!response.ok) {
        throw new Error(`Failed to fetch agents summary: ${response.statusText}`)
      }
      return response.json()
    } catch (error) {
      return this.getMockAgentsSummary()
    }
  }

  async getAgentSummary(agentId: string): Promise<AgentSummary | null> {
    try {
      const response = await fetch(`${this.baseUrl}/agent-monitoring/agents/${agentId}`)
      if (!response.ok) {
        throw new Error(`Failed to fetch agent summary: ${response.statusText}`)
      }
      return response.json()
    } catch (error) {
      return null
    }
  }

  async getAgentActivities(agentId: string, limit: number = 20): Promise<ActivityEvent[]> {
    try {
      const response = await fetch(
        `${this.baseUrl}/agent-monitoring/agents/${agentId}/activities?limit=${limit}`
      )
      if (!response.ok) {
        throw new Error(`Failed to fetch agent activities: ${response.statusText}`)
      }
      return response.json()
    } catch (error) {
      return this.getMockActivityFeed({ agentId })
    }
  }

  async getActivityFeed(filters: ActivityFeedFilters = {}): Promise<ActivityEvent[]> {
    try {
      const params = new URLSearchParams()
      if (filters.agentId) params.set('agent_id', filters.agentId)
      if (filters.status) params.set('status', filters.status)
      if (filters.limit) params.set('limit', filters.limit.toString())
      if (filters.offset) params.set('offset', filters.offset.toString())

      const response = await fetch(`${this.baseUrl}/agent-monitoring/activity-feed?${params}`)
      if (!response.ok) {
        throw new Error(`Failed to fetch activity feed: ${response.statusText}`)
      }
      return response.json()
    } catch (error) {
      return this.getMockActivityFeed(filters)
    }
  }

  async getAgentHealth(agentId: string): Promise<AgentHealth> {
    try {
      const response = await fetch(`${this.baseUrl}/agent-monitoring/agents/${agentId}/health`)
      if (!response.ok) {
        throw new Error(`Failed to fetch agent health: ${response.statusText}`)
      }
      return response.json()
    } catch (error) {
      return this.getMockAgentHealth(agentId)
    }
  }

  async getProactiveAlerts(): Promise<ProactiveAlert[]> {
    try {
      const response = await fetch(`${this.baseUrl}/agent-monitoring/alerts`)
      if (!response.ok) {
        throw new Error(`Failed to fetch proactive alerts: ${response.statusText}`)
      }
      return response.json()
    } catch (error) {
      return this.getMockProactiveAlerts()
    }
  }

  async seedDemoData(): Promise<{ success: boolean; activities_created: number }> {
    try {
      const response = await fetch(`${this.baseUrl}/agent-monitoring/seed-demo`, {
        method: 'POST',
      })
      if (!response.ok) {
        throw new Error(`Failed to seed demo data: ${response.statusText}`)
      }
      return response.json()
    } catch (error) {
      return { success: false, activities_created: 0 }
    }
  }

  private getMockGlobalMetrics(): GlobalMetrics {
    return {
      actions_today: 144,
      actions_delta: 8,
      active_agents: 5,
      total_agents: 7,
      success_rate: 96.7,
      avg_response_time: 1.2,
      proactive_alerts: 2
    }
  }

  private getMockAgentsSummary(): AgentSummary[] {
    const generateSparkline = () => Array.from({ length: 24 }, () => Math.floor(Math.random() * 10) + 1)

    return [
      {
        id: 'job_intake',
        name: 'Job Intake',
        icon: '📋',
        status: 'online',
        actions_today: 12,
        daily_goal: 15,
        progress: 80,
        delta: 3,
        sparkline: generateSparkline(),
        last_action: 'Criou JD para Gerente de Projetos',
        last_action_time: new Date(Date.now() - 2 * 60 * 1000).toISOString()
      },
      {
        id: 'sourcing',
        name: 'Sourcing',
        icon: '🔍',
        status: 'online',
        actions_today: 47,
        daily_goal: 50,
        progress: 94,
        delta: 12,
        sparkline: generateSparkline(),
        last_action: 'Encontrou 12 candidatos para Diretor de TI',
        last_action_time: new Date(Date.now() - 3 * 60 * 1000).toISOString()
      },
      {
        id: 'screening',
        name: 'Screening',
        icon: '🎯',
        status: 'warning',
        actions_today: 23,
        daily_goal: 30,
        progress: 77,
        delta: -2,
        sparkline: generateSparkline(),
        last_action: 'Analisou CV de Carlos Mendonça',
        last_action_time: new Date(Date.now() - 5 * 60 * 1000).toISOString()
      },
      {
        id: 'scheduling',
        name: 'Scheduling',
        icon: '📅',
        status: 'idle',
        actions_today: 8,
        daily_goal: 20,
        progress: 40,
        delta: 0,
        sparkline: generateSparkline(),
        last_action: 'Agendou entrevista para amanhã 14h',
        last_action_time: new Date(Date.now() - 15 * 60 * 1000).toISOString()
      },
      {
        id: 'communication',
        name: 'Communication',
        icon: '✉️',
        status: 'online',
        actions_today: 34,
        daily_goal: 40,
        progress: 85,
        delta: 8,
        sparkline: generateSparkline(),
        last_action: 'Enviou convite de entrevista',
        last_action_time: new Date(Date.now() - 8 * 60 * 1000).toISOString()
      },
      {
        id: 'analytics',
        name: 'Analytics',
        icon: '📊',
        status: 'idle',
        actions_today: 5,
        daily_goal: 10,
        progress: 50,
        delta: 25,
        sparkline: generateSparkline(),
        last_action: 'Gerou relatório semanal',
        last_action_time: new Date(Date.now() - 60 * 60 * 1000).toISOString()
      },
      {
        id: 'recruiter_assistant',
        name: 'Assistente',
        icon: '🤖',
        status: 'online',
        actions_today: 15,
        daily_goal: 25,
        progress: 60,
        delta: 5,
        sparkline: generateSparkline(),
        last_action: 'Preparou briefing para vaga',
        last_action_time: new Date(Date.now() - 12 * 60 * 1000).toISOString()
      }
    ]
  }

  private getMockActivityFeed(filters: ActivityFeedFilters): ActivityEvent[] {
    const activities: ActivityEvent[] = [
      {
        id: '1',
        agent_id: 'job_intake',
        agent_name: 'Job Intake',
        agent_icon: '📋',
        type: 'job_created',
        title: 'Criou nova vaga',
        description: 'Vaga de Gerente de Projetos com JD completo',
        status: 'success',
        started_at: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
        completed_at: new Date().toISOString()
      },
      {
        id: '2',
        agent_id: 'sourcing',
        agent_name: 'Sourcing',
        agent_icon: '🔍',
        type: 'candidates_found',
        title: 'Encontrou candidatos',
        description: '12 novos candidatos para Diretor de TI',
        status: 'success',
        started_at: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
        completed_at: new Date(Date.now() - 3 * 60 * 1000).toISOString()
      },
      {
        id: '3',
        agent_id: 'screening',
        agent_name: 'Screening',
        agent_icon: '🎯',
        type: 'cv_analyzed',
        title: 'Análise de CV',
        description: '5 CVs analisados - 3 aprovados',
        status: 'success',
        started_at: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
        completed_at: new Date(Date.now() - 8 * 60 * 1000).toISOString()
      },
      {
        id: '4',
        agent_id: 'communication',
        agent_name: 'Communication',
        agent_icon: '✉️',
        type: 'email_sent',
        title: 'Email enviado',
        description: 'Follow-up para Patricia Santos',
        status: 'success',
        started_at: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
        completed_at: new Date(Date.now() - 14 * 60 * 1000).toISOString()
      },
      {
        id: '5',
        agent_id: 'scheduling',
        agent_name: 'Scheduling',
        agent_icon: '📅',
        type: 'interview_scheduled',
        title: 'Entrevista agendada',
        description: 'Carlos Mendonça - amanhã 14h',
        status: 'success',
        started_at: new Date(Date.now() - 20 * 60 * 1000).toISOString(),
        completed_at: new Date(Date.now() - 18 * 60 * 1000).toISOString()
      },
      {
        id: '6',
        agent_id: 'recruiter_assistant',
        agent_name: 'Assistente',
        agent_icon: '🤖',
        type: 'briefing_created',
        title: 'Briefing criado',
        description: 'Job description para Dev Senior React',
        status: 'success',
        started_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
        completed_at: new Date(Date.now() - 25 * 60 * 1000).toISOString()
      },
      {
        id: '7',
        agent_id: 'analytics',
        agent_name: 'Analytics',
        agent_icon: '📊',
        type: 'report_generated',
        title: 'Relatório gerado',
        description: 'Métricas do funil - Time-to-hire: 23 dias',
        status: 'success',
        started_at: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
        completed_at: new Date(Date.now() - 55 * 60 * 1000).toISOString()
      },
      {
        id: '8',
        agent_id: 'sourcing',
        agent_name: 'Sourcing',
        agent_icon: '🔍',
        type: 'search_started',
        title: 'Busca iniciada',
        description: 'Busca ativa para 3 vagas',
        status: 'in_progress',
        started_at: new Date(Date.now() - 90 * 60 * 1000).toISOString()
      }
    ]

    let filtered = activities
    if (filters.agentId) {
      filtered = filtered.filter(a => a.agent_id === filters.agentId)
    }
    if (filters.status) {
      filtered = filtered.filter(a => a.status === filters.status)
    }

    return filtered.slice(0, filters.limit || 20)
  }

  private getMockAgentHealth(agentId: string): AgentHealth {
    return {
      agent_id: agentId,
      score: 87,
      tier: 'good',
      drivers: [
        { name: 'Taxa de Sucesso', value: 96, weight: 40, impact: 'positive' },
        { name: 'SLA Compliance', value: 92, weight: 30, impact: 'positive' },
        { name: 'Tempo Médio', value: 25, weight: 20, impact: 'positive' },
        { name: 'Taxa de Erro', value: 4, weight: 10, impact: 'positive' }
      ],
      recommendations: [
        'Agente operando dentro dos parâmetros ideais',
        'Considere aumentar a capacidade em horário de pico'
      ]
    }
  }

  private getMockProactiveAlerts(): ProactiveAlert[] {
    return [
      {
        id: '1',
        agent_id: 'screening',
        agent_name: 'Screening',
        severity: 'medium',
        type: 'performance_warning',
        title: 'Taxa de conversão abaixo da meta',
        description: 'A taxa de conversão caiu 2.1% nas últimas 24h',
        created_at: new Date(Date.now() - 30 * 60 * 1000).toISOString()
      }
    ]
  }
}

export const agentMonitoringService = new AgentMonitoringService()
