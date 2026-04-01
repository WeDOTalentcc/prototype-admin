import {
  Plus, Users, TrendingUp, Network, Settings, Target, Workflow, Database, BarChart3, Shield,
  DollarSign, Heart, Building, Clock, Laptop, Globe, FileText, Edit, CheckCircle, X,
  Search, Calendar, Filter, Phone, Download, ClipboardList, Copy, Brain, Zap, Lightbulb
} from "lucide-react"
import type { AgentData, AgentActivity } from "../types"

const mockAgents: AgentData[] = [
  {
    id: "job-intake",
    name: "Job Intake Agent",
    icon: "📋",
    description: "Criação de vagas e JD",
    status: "active",
    actionsToday: 12,
    lastActivity: "Criou JD para Gerente de Projetos",
    lastActivityTime: "há 2 min"
  },
  {
    id: "sourcing",
    name: "Sourcing Agent",
    icon: "🔍",
    description: "Busca de candidatos",
    status: "active",
    actionsToday: 47,
    lastActivity: "Encontrou 12 candidatos para Diretor de TI",
    lastActivityTime: "há 3 min"
  },
  {
    id: "screening",
    name: "Screening Agent",
    icon: "📝",
    description: "Triagem e análise",
    status: "active",
    actionsToday: 23,
    lastActivity: "Analisou CV de Carlos Mendonça - Score 94",
    lastActivityTime: "há 5 min"
  },
  {
    id: "scheduling",
    name: "Scheduling Agent",
    icon: "📅",
    description: "Agendamento",
    status: "idle",
    actionsToday: 8,
    lastActivity: "Agendou entrevista para amanhã 14h",
    lastActivityTime: "há 15 min"
  },
  {
    id: "communication",
    name: "Communication Agent",
    icon: "📧",
    description: "Emails e mensagens",
    status: "active",
    actionsToday: 34,
    lastActivity: "Enviou convite de entrevista para 3 candidatos",
    lastActivityTime: "há 8 min"
  },
  {
    id: "analytics",
    name: "Analytics Agent",
    icon: "📊",
    description: "Métricas e KPIs",
    status: "idle",
    actionsToday: 5,
    lastActivity: "Gerou relatório semanal de pipeline",
    lastActivityTime: "há 1h"
  },
  {
    id: "assistant",
    name: "Recruiter Assistant",
    icon: "🤖",
    description: "Briefing e tarefas",
    status: "active",
    actionsToday: 15,
    lastActivity: "Preparou briefing para vaga de Dev Senior",
    lastActivityTime: "há 12 min"
  }
]

const mockActivities: AgentActivity[] = [
  {
    id: "0",
    agentId: "job-intake",
    agentIcon: "📋",
    agentName: "Job Intake",
    action: "Criou nova vaga de Gerente de Projetos com JD completo",
    timestamp: "10:35",
    status: "success"
  },
  {
    id: "1",
    agentId: "sourcing",
    agentIcon: "🔍",
    agentName: "Sourcing",
    action: "Encontrou 12 novos candidatos matching para Diretor de TI",
    timestamp: "10:32",
    status: "success"
  },
  {
    id: "2",
    agentId: "screening",
    agentIcon: "📝",
    agentName: "Screening",
    action: "Finalizou análise de 5 CVs - 3 aprovados para entrevista",
    timestamp: "10:28",
    status: "success"
  },
  {
    id: "3",
    agentId: "communication",
    agentIcon: "📧",
    agentName: "Communication",
    action: "Enviou email de follow-up para Patricia Santos",
    timestamp: "10:25",
    status: "success"
  },
  {
    id: "4",
    agentId: "scheduling",
    agentIcon: "📅",
    agentName: "Scheduling",
    action: "Confirmou entrevista com Carlos Mendonça - 23/02 às 14h",
    timestamp: "10:18",
    status: "success"
  },
  {
    id: "5",
    agentId: "assistant",
    agentIcon: "🤖",
    agentName: "Assistant",
    action: "Criou job description para Dev Senior React",
    timestamp: "10:05",
    status: "success"
  },
  {
    id: "6",
    agentId: "analytics",
    agentIcon: "📊",
    agentName: "Analytics",
    action: "Atualizou métricas do funil - Time-to-hire: 23 dias",
    timestamp: "09:45",
    status: "success"
  },
  {
    id: "7",
    agentId: "sourcing",
    agentIcon: "🔍",
    agentName: "Sourcing",
    action: "Iniciou busca ativa no LinkedIn para 3 vagas",
    timestamp: "09:30",
    status: "pending"
  },
  {
    id: "8",
    agentId: "screening",
    agentIcon: "📝",
    agentName: "Screening",
    action: "Pré-qualificou 8 candidatos da base interna",
    timestamp: "09:15",
    status: "success"
  }
]

export { mockAgents, mockActivities }
