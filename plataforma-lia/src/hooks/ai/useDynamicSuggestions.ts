"use client"

import { useMemo } from "react"
import { Plus, Search, UserCheck, FileText, Calendar, RefreshCcw, AlertTriangle, Clock, Users } from "lucide-react"
import type { LucideIcon } from "lucide-react"
import { useUIPreferencesStore } from "@/stores/ui-preferences-store"

export interface DynamicSuggestion {
  id: string
  icon: LucideIcon
  title: string
  description: string
  command: string
  category: "vagas" | "candidatos" | "entrevistas" | "relatorios"
  priority: number
  actionType: "inline" | "redirect"
  redirectPath?: string
}

const FALLBACK_SUGGESTIONS: DynamicSuggestion[] = [
  {
    id: "create-job",
    icon: Plus,
    title: "Crie uma nova vaga",
    description: "Configure requisitos do sistema com descrição detalhada",
    command: "Criar uma nova vaga",
    category: "vagas",
    priority: 50,
    actionType: "redirect",
    redirectPath: "/vagas/nova"
  },
  {
    id: "search-candidates",
    icon: Search,
    title: "Buscar candidatos",
    description: "Encontre candidatos no banco de dados por perfil, skills ou experiência",
    command: "Buscar candidatos",
    category: "candidatos",
    priority: 50,
    actionType: "inline"
  },
  {
    id: "share-candidates",
    icon: UserCheck,
    title: "Compartilhe candidatos com gestor",
    description: "Crie relatório com perfis aprovados e recomendações",
    command: "Compartilhe candidatos com gestor",
    category: "candidatos",
    priority: 40,
    actionType: "inline"
  },
  {
    id: "approve-job",
    icon: FileText,
    title: "Solicite aprovação de nova vaga",
    description: "Encaminhe documentação para aprovação gerencial",
    command: "Solicite aprovação de nova vaga",
    category: "vagas",
    priority: 40,
    actionType: "inline"
  },
  {
    id: "candidate-info",
    icon: Search,
    title: "Consulte sobre candidato",
    description: "Obtenha histórico específico e histórico completo",
    command: "Consulte informações sobre candidato",
    category: "candidatos",
    priority: 35,
    actionType: "inline"
  },
  {
    id: "add-candidate",
    icon: UserCheck,
    title: "Adicione novo candidato",
    description: "Cadastre perfil com talentos",
    command: "Adicione novo candidato",
    category: "candidatos",
    priority: 30,
    actionType: "inline"
  },
  {
    id: "reschedule-interview",
    icon: Calendar,
    title: "Reagende uma entrevista",
    description: "Cancele horário e notifique automaticamente participantes",
    command: "Reagende uma entrevista",
    category: "entrevistas",
    priority: 30,
    actionType: "inline"
  },
  {
    id: "update-status",
    icon: RefreshCcw,
    title: "Atualize status do candidato",
    description: "Modifique situação no processo e envie notificações",
    command: "Atualize status do candidato",
    category: "candidatos",
    priority: 25,
    actionType: "inline"
  }
]

export interface ContextualData {
  openJobsWithoutCandidates?: number
  stalledCandidates?: number
  upcomingInterviews?: number
  pendingApprovals?: number
}

function generateContextualSuggestions(data: ContextualData): DynamicSuggestion[] {
  const contextual: DynamicSuggestion[] = []

  if (data.openJobsWithoutCandidates && data.openJobsWithoutCandidates > 0) {
    contextual.push({
      id: "ctx-jobs-no-candidates",
      icon: AlertTriangle,
      title: `${data.openJobsWithoutCandidates} vaga(s) sem candidatos`,
      description: "Busque candidatos para vagas abertas que ainda não têm aplicações",
      command: "Mostre minhas vagas abertas sem candidatos e sugira como encontrar talentos",
      category: "vagas",
      priority: 95,
      actionType: "inline"
    })
  }

  if (data.stalledCandidates && data.stalledCandidates > 0) {
    contextual.push({
      id: "ctx-stalled-candidates",
      icon: Users,
      title: `${data.stalledCandidates} candidato(s) parado(s) no funil`,
      description: "Candidatos aguardando ação há mais de 7 dias",
      command: "Mostre candidatos parados no funil e sugira próximos passos",
      category: "candidatos",
      priority: 90,
      actionType: "inline"
    })
  }

  if (data.upcomingInterviews && data.upcomingInterviews > 0) {
    contextual.push({
      id: "ctx-upcoming-interviews",
      icon: Clock,
      title: `${data.upcomingInterviews} entrevista(s) próxima(s)`,
      description: "Entrevistas agendadas para os próximos 3 dias",
      command: "Mostre minhas entrevistas dos próximos 3 dias com detalhes dos candidatos",
      category: "entrevistas",
      priority: 85,
      actionType: "inline"
    })
  }

  if (data.pendingApprovals && data.pendingApprovals > 0) {
    contextual.push({
      id: "ctx-pending-approvals",
      icon: FileText,
      title: `${data.pendingApprovals} aprovação(ões) pendente(s)`,
      description: "Vagas aguardando aprovação gerencial",
      command: "Mostre vagas pendentes de aprovação e seus status",
      category: "vagas",
      priority: 80,
      actionType: "inline"
    })
  }

  return contextual
}

export function useDynamicSuggestions(refreshKey?: unknown): {
  suggestions: DynamicSuggestion[]
  hasContextualData: boolean
} {
  const recruiterContext = useUIPreferencesStore((state) => state.recruiterContext)

  const contextualData: ContextualData = useMemo(() => {
    if (!recruiterContext) return {}
    return {
      openJobsWithoutCandidates: recruiterContext.openJobsWithoutCandidates ?? 0,
      stalledCandidates: recruiterContext.stalledCandidates ?? 0,
      upcomingInterviews: recruiterContext.upcomingInterviews ?? 0,
      pendingApprovals: recruiterContext.pendingApprovals ?? 0,
    }
  }, [recruiterContext, refreshKey]) // eslint-disable-line react-hooks/exhaustive-deps

  const hasContextualData = useMemo(() => {
    return Object.values(contextualData).some(v => typeof v === "number" && v > 0)
  }, [contextualData])

  const suggestions = useMemo(() => {
    if (!hasContextualData) {
      return [...FALLBACK_SUGGESTIONS].sort((a, b) => b.priority - a.priority)
    }

    const contextual = generateContextualSuggestions(contextualData)
    const combined = [...contextual, ...FALLBACK_SUGGESTIONS]
    return combined.sort((a, b) => b.priority - a.priority).slice(0, 8)
  }, [hasContextualData, contextualData])

  return { suggestions, hasContextualData }
}
